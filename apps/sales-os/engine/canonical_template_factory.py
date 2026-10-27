import os
import re
from pathlib import Path
from typing import Dict, Any, Literal, Optional

from hsb_core import sanitize_company_name
from lead_quality import segment_for
from optout_helper import build_optout_url, build_tracked_website_url

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "canonical"

CANONICAL_FLYERS = {
    "JOEL": {
        "filename": "HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "attachment_name": "HSB-HEXAGON-Industrieboeden-Flyer.pdf",
        "path": str(ASSETS_DIR / "HSB-Flyer-Joel-Cherino_FINAL.pdf"),
        "sender_name": "Joel Cherino Diaz",
        "sender_role": "Vertrieb & Kundenbetreuung",
        "sender_phone": "+49 2562 9463030",
        "sender_email": "j-cherino@hsb-boden.de",
        "reply_to": "Joel Cherino Diaz <j-cherino@hsb-boden.de>",
    },
    "JORDI": {
        "filename": "HSB-Flyer-Jordie-Post_FINAL.pdf",
        "attachment_name": "HSB-HEXAGON-Industrieboeden-Flyer.pdf",
        "path": str(ASSETS_DIR / "HSB-Flyer-Jordie-Post_FINAL.pdf"),
        "sender_name": "Jordie Post",
        "sender_role": "Geschäftsführer",
        "sender_phone": "0170 2340904",
        "sender_email": "j.post@hsb-boden.de",
        "reply_to": "Jordie Post <j-post@hsb-boden.de>",
    },
}
CANONICAL_FLYERS["JORDIE"] = CANONICAL_FLYERS["JORDI"]

LOGO_URL = "https://www.hsb-boden.de/brand/hsb-boden-logo.png"


def anrede_fuer_lead(lead: Dict[str, Any]) -> str:
    ap = str(lead.get("Ansprechpartner") or "").strip()
    if not ap or ap.lower() in ["none", "nan", "null"]:
        return "Guten Tag,"
    teile = ap.split()
    if len(teile) >= 2:
        anr = teile[0].lower()
        nachname = " ".join(teile[1:])
        if "herr" in anr:
            return f"Sehr geehrter Herr {nachname},"
        if "frau" in anr:
            return f"Sehr geehrte Frau {nachname},"
    return f"Guten Tag {ap},"


def render_canonical_email(lead: Dict[str, Any], owner: str = "JOEL", domain: str = "de") -> Dict[str, Any]:
    norm_owner = owner.strip().upper() if owner else "JOEL"
    if norm_owner not in CANONICAL_FLYERS:
        norm_owner = "JOEL"
    owner_meta = CANONICAL_FLYERS[norm_owner]
    if domain.lower() == "com":
        sender_email = "j-cherino@hsb-boden.com" if norm_owner == "JOEL" else "j-post@hsb-boden.com"
    else:
        sender_email = owner_meta["sender_email"]

    to_addr = str(lead.get("Email") or lead.get("E-Mail") or "").strip()
    if not to_addr or "@" not in to_addr:
        raise ValueError(f"Recipient email missing or invalid in lead {lead.get('Lead_ID') or lead.get('Lead-ID')}")

    lead_id = str(lead.get("Lead_ID") or lead.get("Lead-ID") or "").strip()

    raw_comp = str(lead.get("Firma") or lead.get("Firmenname") or lead.get("Company") or "").strip()
    clean_comp = re.sub(r"https?://(?:www\.)?", "", raw_comp, flags=re.IGNORECASE)
    clean_comp = re.sub(r"\.(?:de|com|ch|at)/?$", "", clean_comp, flags=re.IGNORECASE).strip()

    # Consumer freemail fallback (z.B. gmail, gmx, web.de) oder privater Bauherr
    is_consumer_freemail = any(f in to_addr.lower() for f in ["@gmail.", "@gmx.", "@web."])
    if not clean_comp or is_consumer_freemail or clean_comp.lower() in ["private bauherr", "privat", "keine"]:
        subject_target = "Ihr Unternehmen"
    else:
        subject_target = sanitize_company_name(clean_comp, to_addr)

    subject = f"Industrieböden für {subject_target} – Beratung von {owner_meta['sender_name']}"
    greeting = anrede_fuer_lead(lead)

    tracked_web_url = build_tracked_website_url("signature_website")
    tracked_logo_url = build_tracked_website_url("signature_logo")
    optout_url = build_optout_url(lead_id=lead_id, email=to_addr)

    body_html = f"""<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1f2937; line-height: 1.55;">
    <p>{greeting}</p>
    <p>mein Name ist {owner_meta['sender_name']} von der HSB Hexagon Säurebau GmbH. Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.</p>
    <p>Typische Themen bei Produktionsbetrieben:<br>
    &bull; Risse, Ablösungen und offene Fugen<br>
    &bull; Keimnester in Nassbereichen<br>
    &bull; stehendes Wasser durch falsches Gefälle<br>
    &bull; defekte Rinnen und Abläufe</p>
    <p>Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser Vorgehen von der Analyse bis zur dokumentierten Übergabe.</p>
    <p>Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.</p>
    <p>Mit freundlichen Grüßen<br />
    <strong>{owner_meta['sender_name']}</strong><br />
    {owner_meta['sender_role']}<br />
    HSB Hexagon Säurebau GmbH<br />
    Telefon: {owner_meta['sender_phone']}<br />
    E-Mail: {sender_email}<br />
    Web: <a href="https://www.hsb-boden.de" style="color: #1d4ed8; text-decoration: none;">www.hsb-boden.de</a></p>
    <p style="margin-top: 15px; margin-bottom: 15px;"><a href="https://www.hsb-boden.de"><img src="{LOGO_URL}" alt="HSB Hexagon Säurebau Logo" width="102" height="75" style="display: block; border: 0; outline: none; text-decoration: none;" /></a></p>
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 18px 0 14px 0;" />
    <p style="font-size: 11px; color: #64748b; line-height: 1.45;">
    <strong>HSB Hexagon Säurebau GmbH</strong> &middot; Benzstraße 6 &middot; 48599 Gronau<br />
    Registergericht: Amtsgericht Coesfeld, HRB 21481 &middot; Sitz: Gronau &middot; Geschäftsführer: Jordie Post<br />
    <a href="https://www.hsb-boden.de/impressum/" style="color: #64748b; text-decoration: underline;">Impressum</a> &middot; <a href="https://www.hsb-boden.de/datenschutz/" style="color: #64748b; text-decoration: underline;">Datenschutz</a> &middot; <a href="{optout_url}" style="color: #64748b; text-decoration: underline;">Hier abmelden</a>
    </p>
</div>"""

    if domain.lower() == 'com':
        body_html = body_html.replace('Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser Vorgehen von der Analyse bis zur dokumentierten Übergabe.',
            'Für ' + __import__('html').escape(subject_target) + ' zeigen wir im <a href="https://www.hsb-boden.de/flyer">Online-Projektflyer</a> unser Vorgehen von der Analyse bis zur dokumentierten Übergabe.')

    return {
        "subject": subject,
        "body_html": body_html,
        "to_address": to_addr,
        "flyer_path": None if domain.lower() == "com" else owner_meta["path"],
        "flyer_filename": owner_meta.get("attachment_name", owner_meta["filename"]),
        "logo_url": LOGO_URL,
        "reply_to": "" if domain.lower() == "com" else owner_meta["reply_to"],
    }


# ---------------------------------------------------------------------------
# Vorlage v2: reiner Text, 2 Segmente (architekten/produktion), 3 Schritte.
# ---------------------------------------------------------------------------

# Ohne Click-Token (siehe click_sync.click_url) bleibt der Link ohne Lead-Bezug.
FLYER_LANDING_URL = (
    "https://www.hsb-boden.de/flyer/?utm_source=hsb_outreach&utm_medium=email"
    "&utm_campaign=iboden_v2_{segment}"
)

OPTOUT_LINE_V2 = "Kein Interesse? Antworten Sie kurz mit ‚Abmelden‘, dann melden wir uns nicht wieder."

_LEGAL_FORM_RE = re.compile(
    r"[\s,]*(?:&\s*Co\.?\s*)?(?<![\w.])(?:GmbH|mbH|AG|KG|GbR|PartGmbB|PartG|"
    r"Partnerschaftsgesellschaft|e\.\s?K\.|UG(?:\s*\(haftungsbeschränkt\))?)\.?\s*$",
    re.IGNORECASE,
)

_SUBJECTS_V2 = {
    "architekten": ("Industrieboden-Details für {firma}", "Industrieboden-Details für Ihre Planung"),
    "produktion": ("Hygieneboden bei {firma}", "Hygieneboden vor dem Audit"),
}

_BODIES_V2 = {
    ("architekten", 1): (
        "mein Name ist {sender} von der HSB Hexagon Säurebau GmbH. Wir planen, bauen und sanieren "
        "säurebeständige Industrieböden.\n\n"
        "Falls {bei} gerade Industrie-, Gewerbe- oder Lebensmittelprojekte in Planung sind: In den "
        "Leistungsphasen 5 bis 7 entscheidet sich oft, wie lange ein Boden in Nassbereichen hält, etwa "
        "bei Gefälle zu den Rinnen, Fugenplanung und Belastungsprofil. Wir stellen dafür "
        "herstellerneutrale LV-Bausteine und Detailzeichnungen bereit, die Sie frei in Ihre "
        "Ausschreibung übernehmen können.\n\n"
        "Darf ich Ihnen diese Unterlagen unverbindlich zusenden?{link}"
    ),
    ("architekten", 2): (
        "kurz zu meiner Nachricht von vor ein paar Tagen: Gefälle, Rinnenanschlüsse und Fugen lassen sich "
        "am einfachsten klären, solange die Leistungsphasen 5 bis 7 noch offen sind. Unsere "
        "herstellerneutralen LV-Bausteine und Detailzeichnungen wären dafür eine Arbeitsgrundlage für "
        "Ihre Projekte {bei}, die Sie an Ihre Ausschreibung anpassen und frei weiterverwenden können. "
        "Sie sind so aufgebaut, dass Sie einzelne Bausteine auch getrennt übernehmen können.\n\n"
        "Darf ich Ihnen die Unterlagen als PDF und DWG zusenden?"
    ),
    ("architekten", 3): (
        "ich melde mich ein letztes Mal zu diesem Thema, denn ich möchte Sie nicht weiter mit "
        "Nachrichten belasten. Wenn Gefälle, Rinnen und Fugen {bei} gerade kein Thema sind, ist das völlig "
        "in Ordnung. Sollte bei einem späteren Projekt die Ausschreibung anstehen, antworten Sie "
        "einfach auf diese Nachricht. Dann sende ich Ihnen gern herstellerneutrale LV-Bausteine und "
        "Detailzeichnungen zu. Ich wünsche Ihnen weiterhin gutes Gelingen bei Ihren Projekten."
    ),
    ("produktion", 1): (
        "mein Name ist {sender} von der HSB Hexagon Säurebau GmbH. Wir planen, bauen und sanieren "
        "säurebeständige, hygienische Industrieböden für Produktionsbetriebe.\n\n"
        "Falls {bei} IFS- oder BRC-Audits anstehen, rückt der Boden oft in den Blick: Fugen als "
        "mögliche Keimnester, Rinnen und Abläufe sowie die Rutschhemmung. Bei einer Sanierung "
        "entscheidet meist das Stillstandsfenster. Deshalb planen wir Schichtaufbau und "
        "Aushärtezeiten auf Ihren Produktionsrhythmus.\n\n"
        "Wäre ein kurzes, unverbindliches Gespräch dazu für Sie interessant?{link}"
    ),
    ("produktion", 2): (
        "kurz zu meiner Nachricht von vor ein paar Tagen: Falls ein IFS- oder BRC-Audit {bei} ansteht, lohnt "
        "es sich, Fugen, Rinnen und Rutschhemmung frühzeitig zu betrachten. Dann lässt sich ein "
        "Stillstandsfenster mit passenden Aushärtezeiten in Ruhe planen, statt unter Zeitdruck. "
        "Dabei können auch einzelne Teilflächen getrennt betrachtet werden. Wir stimmen Schichtaufbau "
        "und Ablauf gern auf Ihren Produktionsrhythmus ab.\n\n"
        "Wäre ein kurzes Gespräch dazu für Sie interessant?"
    ),
    ("produktion", 3): (
        "ich melde mich ein letztes Mal zu diesem Thema, denn ich möchte Sie nicht weiter mit "
        "Nachrichten belasten. Wenn Fugen, Rinnen und das Stillstandsfenster {bei} gerade kein Thema sind, "
        "ist das völlig in Ordnung. Sollte vor einem Audit oder einer Sanierung der Boden wieder in "
        "den Fokus rücken, antworten Sie einfach auf diese Nachricht. Ich wünsche Ihnen weiterhin "
        "einen reibungslosen Betrieb."
    ),
}

# Absenderadresse in der Signatur = From-Postfach (nur dort wird gelesen).
_SENDER_COM = {"JOEL": "j-cherino@hsb-boden.com", "JORDI": "j-post@hsb-boden.com"}

_PFLICHTANGABEN_V2 = (
    "HSB Hexagon Säurebau GmbH · Benzstraße 6 · 48599 Gronau\n"
    "Registergericht: Amtsgericht Coesfeld, HRB 21481 · Sitz: Gronau · Geschäftsführer: Jordie Post\n"
    "Impressum und Datenschutz: www.hsb-boden.de/impressum/ und www.hsb-boden.de/datenschutz/"
)


def short_company(name: Any) -> str:
    """Kurzname fuer Betreffzeilen: Zusaetze nach dem Komma und Rechtsform entfernt, hoechstens 40 Zeichen."""
    text = re.sub(r"\s+", " ", str(name or "")).strip()
    text = text.split(",", 1)[0].strip()
    while True:
        stripped = _LEGAL_FORM_RE.sub("", text).strip()
        if stripped == text or not stripped:
            break
        text = stripped
    if len(text) > 40:
        cut = text[:40].rsplit(" ", 1)[0] if " " in text[:40] else text[:40]
        text = cut.strip()
    return text


def _subject_v2(segment: str, firma_short: str) -> str:
    with_firma, topic_only = _SUBJECTS_V2[segment]
    if firma_short:
        candidate = with_firma.format(firma=firma_short)
        if len(candidate) <= 50 and len(candidate.split()) <= 5:
            return candidate
    return topic_only


def render_email_v2(
    lead: Dict[str, Any],
    owner: str = "JOEL",
    step: Literal[1, 2, 3] = 1,
    thread: Optional[Dict[str, str]] = None,
    click_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Reiner-Text-Mail v2. Schritt 2/3 antworten im Thread von Schritt 1 und enthalten keinen Link."""
    if step not in (1, 2, 3):
        raise ValueError(f"step must be 1, 2 or 3, got {step!r}")
    norm_owner = owner.strip().upper() if owner else "JOEL"
    if norm_owner not in CANONICAL_FLYERS:
        norm_owner = "JOEL"
    meta = CANONICAL_FLYERS[norm_owner]

    to_addr = str(lead.get("Email") or lead.get("E-Mail") or "").strip()
    if not to_addr or "@" not in to_addr:
        raise ValueError(f"Recipient email missing or invalid in lead {lead.get('Lead_ID') or lead.get('Lead-ID')}")
    lead_id = str(lead.get("Lead_ID") or lead.get("Lead-ID") or "").strip()
    if step > 1 and not (thread and thread.get("message_id") and thread.get("subject")):
        raise ValueError("thread with message_id and subject is required for step 2 and 3")

    raw_comp = str(lead.get("Firma") or lead.get("Firmenname") or lead.get("Company") or "").strip()
    clean_comp = re.sub(r"https?://(?:www\.)?", "", raw_comp, flags=re.IGNORECASE)
    clean_comp = re.sub(r"\.(?:de|com|ch|at)/?$", "", clean_comp, flags=re.IGNORECASE).strip()
    is_consumer_freemail = any(f in to_addr.lower() for f in ["@gmail.", "@gmx.", "@web."])
    if not clean_comp or is_consumer_freemail or clean_comp.lower() in ["private bauherr", "privat", "keine"]:
        firma = ""
    else:
        firma = sanitize_company_name(clean_comp, to_addr)
        if firma == "Ihr Unternehmen":
            firma = ""
    firma_kurz = short_company(firma) if firma else ""
    bei = f"bei {firma_kurz}" if firma_kurz else "bei Ihnen"

    segment = segment_for(lead)
    template_id = f"v2-{segment}-s{step}"

    link = ""
    if step == 1:
        url = click_url or FLYER_LANDING_URL.format(segment=segment)
        link = f"\n\nEine Übersicht finden Sie hier:\n{url}"
    body = _BODIES_V2[(segment, step)].format(sender=meta["sender_name"], bei=bei, link=link)

    phone = meta["sender_phone"]
    phone_label = "Mobil" if phone.replace(" ", "").startswith("01") else "Telefon"
    signature = (
        "Mit freundlichen Grüßen\n"
        f"{meta['sender_name']}\n"
        f"{meta['sender_role']}\n"
        "HSB Hexagon Säurebau GmbH\n"
        f"{phone_label}: {phone}\n"
        f"E-Mail: {_SENDER_COM['JORDI' if meta is CANONICAL_FLYERS['JORDI'] else 'JOEL']}"
    )
    body_text = (
        f"{anrede_fuer_lead(lead)}\n\n{body}\n\n{signature}\n\n{OPTOUT_LINE_V2}\n\n{_PFLICHTANGABEN_V2}\n"
    )

    if step == 1:
        subject = _subject_v2(segment, firma_kurz)
        in_reply_to = references = None
    else:
        original = re.sub(r"^(?:re|aw):\s*", "", str(thread["subject"]).strip(), flags=re.IGNORECASE)
        subject = f"Re: {original}"
        in_reply_to = references = thread["message_id"]

    return {
        "subject": subject,
        "body_text": body_text,
        "to_email": to_addr,
        "lead_id": lead_id,
        "segment": segment,
        "template_id": template_id,
        "in_reply_to": in_reply_to,
        "references": references,
    }
