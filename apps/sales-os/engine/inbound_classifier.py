# apps/sales-os/engine/inbound_classifier.py
from __future__ import annotations
import datetime
import html
import re
from dataclasses import dataclass
from email.header import decode_header, make_header
from typing import Optional

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
BOUNCE_SUBJ_RE = re.compile(r"(unzustellbar|undeliverable|failure|failed|delivery status notification|returned mail)", re.IGNORECASE)
BOUNCE_BODY_RE = re.compile(r"(550\s+5\.\d\.\d|554\s+5\.\d\.\d|user unknown|mailbox unavailable|recipient address rejected)", re.IGNORECASE)

OOO_SUBJ_RE = re.compile(r"(automatische antwort|abwesenheit|out of office|auto[-_ ]?reply|abwesend|urlaub)", re.IGNORECASE)
OOO_BODY_RE = re.compile(r"(nicht im büro|nicht erreichbar|im urlaub|abwesend|out of office|wieder im büro|ab dem|bis zum|bis einschließlich)", re.IGNORECASE)

# Präzise Opt-out Muster (echter Kundenwiderspruch)
OPTOUT_RE = re.compile(
    r"(kein interesse|keinen bedarf|kein bedarf|aus dem verteiler|aus ihrem verteiler|daten löschen|löschen sie|bitte abmelden|melden sie uns ab|melden sie mich ab|nicht mehr kontaktieren|widerspruch|keine weiteren e-?mails|bitte unterlassen)",
    re.IGNORECASE
)
# Echte Kaufsignale & Termine (kein 'interesse' isoliert, um 'kein interesse' nicht fälschlich zu erfassen)
HOT_LEAD_RE = re.compile(
    r"(vorbeikommen|angebot|termin|telefonieren|rufen sie mich|passt (gerade )?gut|wann können sie|muster|beratungstermin|haben interesse|sind interessiert|anfrage zu|bodenbeschichtung)",
    re.IGNORECASE
)

DATE_PATTERNS = [
    re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})"),
    re.compile(r"(\d{1,2})\.(\d{1,2})\."),
]
DAYS_OFFSET_RE = re.compile(r"(\d{1,2})\s*tagen?", re.IGNORECASE)
WEEKS_OFFSET_RE = re.compile(r"(\d{1,2})\s*wochen?", re.IGNORECASE)

FOOTER_CLEAN_RE = re.compile(r"impressum\s*·\s*datenschutz\s*·\s*hier abmelden", re.IGNORECASE)

@dataclass
class InboundClassificationResult:
    category: str  # BOUNCE, OOO_URLAUB, OPTOUT, HOT_LEAD, NEUTRAL
    confidence: float
    recontact_date: Optional[str] = None
    reason: str = ""
    extracted_email: Optional[str] = None


def strip_quoted_reply(body: str) -> str:
    """
    Trennt den neuen Antworttext vom zitierten E-Mail-Verlauf der Originalnachricht,
    damit Absender-Footer (wie 'Hier abmelden') nicht fälschlich ausgewertet werden.
    """
    clean_body = FOOTER_CLEAN_RE.sub("", body)
    lines = []
    quote_starters = [
        "-----original message-----",
        "-----ursprüngliche nachricht-----",
        "von: ",
        "from: ",
        "am ",
        "on "
    ]
    for line in clean_body.splitlines():
        l_low = line.strip().lower()
        if any(l_low.startswith(q) for q in quote_starters) and ("gesendet:" in l_low or "sent:" in l_low or "schrieb:" in l_low or "wrote:" in l_low or "@" in l_low):
            break
        if line.startswith(">"):
            continue
        lines.append(line)
    res = "\n".join(lines).strip()
    return res if res else clean_body


def extract_return_date(text: str, reference_date: Optional[datetime.date] = None) -> Optional[str]:
    ref = reference_date or datetime.date.today()
    days_m = DAYS_OFFSET_RE.search(text)
    if days_m:
        days = int(days_m.group(1))
        return (ref + datetime.timedelta(days=days)).isoformat()

    weeks_m = WEEKS_OFFSET_RE.search(text)
    if weeks_m:
        weeks = int(weeks_m.group(1))
        return (ref + datetime.timedelta(weeks=weeks)).isoformat()

    for p in DATE_PATTERNS:
        m = p.search(text)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3)) if len(m.groups()) >= 3 and m.group(3) else ref.year
            try:
                target = datetime.date(year, month, day)
                if target < ref:
                    target = datetime.date(year + 1, month, day)
                # Nächster Werktag nach Rückkehr
                target = target + datetime.timedelta(days=1)
                return target.isoformat()
            except ValueError:
                continue
    return None


def decode_mime_header(value: str) -> str:
    """RFC-2047-Wörter (z. B. =?UTF-8?B?QWJtZWxkZW4=?=) in Klartext; bei kaputter Kodierung unverändert."""
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:  # z. B. HeaderParseError: ein kaputter Betreff darf den Abgleich nie abbrechen
        return value or ""


def classify_inbound_message(sender: str, subject: str, body: str, reference_date: Optional[datetime.date] = None) -> InboundClassificationResult:
    sender_clean = sender.lower().strip()
    subj_clean = decode_mime_header(subject).strip()

    # 1. Bounces / NDRs (haben immer Vorrang, auch bei Mailer-Daemon)
    if BOUNCE_SUBJ_RE.search(subj_clean) or BOUNCE_BODY_RE.search(body) or "mailer-daemon" in sender_clean or "postmaster" in sender_clean:
        found = [e for e in EMAIL_RE.findall(body) if not any(d in e.lower() for d in ["hsb-boden", "kasserver", "microsoft", "outlook"])]
        dsn = re.search(r"(?:Final|Original)-Recipient:\s*rfc822;\s*([^\s<>]+@[^\s<>]+)", body, re.I)
        extracted = dsn.group(1).strip() if dsn else (found[0] if found else None)
        return InboundClassificationResult(category="BOUNCE", confidence=0.95, reason="Delivery Failure (NDR)", extracted_email=extracted)

    # 2. Interne Absender & Plattform-Benachrichtigungen ausschließen
    internal_domains = ["hsb-boden.de", "hsb-boden.com", "microsoft outlook"]
    if any(d in sender_clean for d in internal_domains):
        return InboundClassificationResult(category="NEUTRAL", confidence=1.0, reason="Interne Absenderadresse / Test-Nachricht")

    system_domains = ["google.com", "cloudflare.com", "maestrolabs.com", "supabase.com", "tailscale.com", "azure.com", "microsoft.com", "apple.com", "github.com", "stripe.com"]
    if any(d in sender_clean for d in system_domains):
        return InboundClassificationResult(category="NEUTRAL", confidence=1.0, reason="Plattform- / System-Benachrichtigung")

    # Bereinigung des Antworttexts (Zitate und Footer ignorieren)
    new_reply_text = strip_quoted_reply(body)
    full_new_text = f"{subj_clean.lower()} {new_reply_text.lower()}"

    # 3. Echter Opt-out / Widerspruch des Kunden (hat Vorrang vor zufälligen Begriffen)
    explicit_subject = re.fullmatch(r"(?:re:\s*|aw:\s*)*(?:abmelden|abmeldung|unsubscribe|stop)\s*[.!]?", subj_clean.strip(), re.I)
    if explicit_subject or OPTOUT_RE.search(full_new_text):
        return InboundClassificationResult(category="OPTOUT", confidence=0.90, reason="Widerspruch / Opt-out Signal")

    # 4. Hot Lead / Termin-Interesse
    if HOT_LEAD_RE.search(full_new_text):
        return InboundClassificationResult(category="HOT_LEAD", confidence=0.88, reason="Positives Interesse / Terminanfrage")

    # 5. Out of Office / Urlaub
    if OOO_SUBJ_RE.search(subj_clean) or OOO_BODY_RE.search(new_reply_text.lower()):
        ret_date = extract_return_date(new_reply_text, reference_date=reference_date)
        return InboundClassificationResult(category="OOO_URLAUB", confidence=0.92, recontact_date=ret_date, reason="Automatische Abwesenheitsnotiz")

    # 6. Neutraler Fallback
    return InboundClassificationResult(category="NEUTRAL", confidence=0.50, reason="Allgemeine Antwort / Manuelle Sichtung")
