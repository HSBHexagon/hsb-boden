import html as _html
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


_TITLES = {'dr.', 'prof.', 'dipl.-ing.', 'dr.-ing.'}
_SUFFIXES = {'jun.', 'sen.', 'jr.', 'sr.', 'jun', 'sen'}
_PARTICLES = {'von', 'van', 'de', 'der', 'den', 'zu', 'zur', 'ten', 'ter', 'vom', 'di', 'da', 'le', 'la'}


def _nachname_mit_titel(teile):
    """'Dr. Anna von der Heide' → 'Dr. von der Heide'; Vornamen entfallen."""
    titel = [t for t in teile if t.lower() in _TITLES]
    rest = [t for t in teile if t.lower() not in _TITLES]
    zusatz = []
    while len(rest) > 1 and rest[-1].lower() in _SUFFIXES:
        zusatz.insert(0, rest.pop())
    if not rest:
        return ' '.join(titel)
    start = len(rest) - 1
    for i, t in enumerate(rest[:-1]):
        if t.lower() in _PARTICLES:
            start = i
            break
    return ' '.join(titel + rest[start:] + zusatz)


def anrede_fuer_lead(lead: Dict[str, Any]) -> str:
    ap = str(lead.get("Ansprechpartner") or "").strip()
    ap = re.sub(r'(?i)^(guten tag|sehr geehrte[rs]?|hallo|liebe[rs]?)\s+', '', ap).strip(' ,')
    if not ap or ap.lower() in ["none", "nan", "null"]:
        return "Guten Tag,"
    teile = ap.split()
    if len(teile) >= 2:
        # "Herrn"/"Herr."/"Frau." waren mit dem früheren Teilstring-Abgleich gültig und bleiben es.
        anr = teile[0].lower().rstrip(".")
        if anr in ("herr", "herrn", "hr"):
            return f"Sehr geehrter Herr {_nachname_mit_titel(teile[1:])},"
        if anr in ("frau", "fr"):
            return f"Sehr geehrte Frau {_nachname_mit_titel(teile[1:])},"
    return f"Guten Tag {ap},"


def render_canonical_email(lead: Dict[str, Any], owner: str = "JOEL", domain: str = "de") -> Dict[str, Any]:
    norm_owner = owner.strip().upper() if isinstance(owner, str) else ""
    if norm_owner not in CANONICAL_FLYERS:
        raise ValueError("INVALID_OWNER")
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
        "wenn {planungsteam} für einen Bauherrn einen Produktions- oder Lebensmittelstandort plant, "
        "können wir Sie bei der technischen Vorprüfung des Bodenaufbaus unterstützen.\n\n"
        "Ich bin {sender} von HSB Hexagon Säurebau. Für die Ausschreibung gehen wir mit Ihnen "
        "durch, wie Gefälle, Rinnenanschlüsse und Fugen auf die spätere Nutzung und Reinigung "
        "abgestimmt werden können. So lassen sich Schnittstellen früh in der Ausführungsplanung klären.\n\n"
        "Möchten Sie einen aktuellen Planstand mit uns durchgehen?{link}"
    ),
    ("architekten", 2): (
        "kurz zu meiner Nachricht von vor ein paar Tagen: Falls {bei} eine Ausschreibung für "
        "Industrie- oder Lebensmittelbereiche ansteht, lohnt sich ein Blick auf die Übergänge zwischen "
        "Boden, Rinnen und Wandanschlüssen. Dort treffen verschiedene Bauteile und Belastungen "
        "aufeinander. Wir können diese Punkte anhand Ihres Vorhabens gemeinsam durchgehen, bevor "
        "die Ausführung festgelegt wird. Falls das Thema gerade jemand anderes in Ihrem Büro betreut, "
        "freue ich mich auch über einen kurzen Hinweis.\n\n"
        "Wer ist dafür bei Ihnen der richtige Ansprechpartner?"
    ),
    ("architekten", 3): (
        "ich melde mich ein letztes Mal zu diesem Thema. Wenn Industrieböden, Gefälle und Fugen "
        "{bei} aktuell keine Rolle spielen, ist das völlig in Ordnung. Sollte später ein "
        "Industrie- oder Lebensmittelprojekt anstehen, können Sie auf diese Nachricht antworten. "
        "Wir besprechen dann gern das Belastungsprofil und mögliche Details der Bodenausführung "
        "anhand des konkreten Vorhabens. Bis dahin wünsche ich Ihnen gutes Gelingen bei Ihren Projekten "
        "und werde hierzu keine weitere Nachricht schicken."
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

# Owner-Entscheidung 2026-11-04 ("Reparatur zuerst"): feste Betreffzeilen ohne Firmennamen,
# keine Firmen-/Titelangaben aus dem CRM im Fließtext, genau ein lesbarer Link auf die
# Reparatur-Ersteinschätzung, kein Anhang. COPY_REV markiert diese Fassung im Entwurf,
# damit ältere Reparatur-Entwürfe als veraltet erkannt und ersetzt werden.
REPAIR_URL = "https://www.hsb-boden.de/reparatur/"
REPARATUR_COPY_REV = "2026-11-05b"

_SUBJECTS_REPARATUR = {
    "architekten": "Industrieböden im Bestand – Einschätzung vor der Ausschreibung",
    "produktion": "Schadstelle im Industrieboden? Ersteinschätzung per Foto",
}

_BODIES_REPARATUR = {
    ("architekten", 1): (
        "bei Umbauten und Sanierungen im Bestand lohnt vor der Ausschreibung ein genauer Blick auf den "
        "vorhandenen Industrieboden. Anhand von Fotos oder Bestandsdaten klären wir mit Ihnen vorab, welche "
        "Bodenflächen erhalten bleiben können und wo Fugen, Rinnen- oder Wandanschlüsse gezielt instand "
        "gesetzt werden können.\n\n"
        "Ich bin {sender} von der HSB Hexagon Säurebau GmbH. So lassen sich Reparatur- und "
        "Sanierungsflächen sauber abgrenzen, bevor das Leistungsverzeichnis steht.{link}"
    ),
    ("architekten", 2): (
        "kurz zu meiner Nachricht von vor ein paar Tagen: Beim Bauen im Bestand entscheidet oft das Detail "
        "an Anschlüssen und Übergängen. Vor einer Reparatur und Instandsetzung prüfen wir Untergrund, Haftzug "
        "und Bestandsaufbau; danach stellen wir Gefälle und Dichtigkeit wieder her.\n\n"
        "Wir stimmen diese Punkte gern anhand Ihrer aktuellen Planung ab, bevor Ausschreibungsdetails "
        "festgelegt werden. Falls das Thema in Ihrem Büro jemand anderes betreut, freue ich mich über einen "
        "kurzen Hinweis.\n\n"
        "Wer ist dafür bei Ihnen der richtige Ansprechpartner?"
    ),
    ("architekten", 3): (
        "ich melde mich ein letztes Mal zu diesem Thema. Wenn Industrieböden und Instandsetzungen im Bestand "
        "bei Ihnen aktuell keine Rolle spielen, ist das völlig in Ordnung.\n\n"
        "Sollte später ein Industrie- oder Gewerbeprojekt anstehen, antworten Sie gern auf diese Nachricht. "
        "Bei Bestandsböden bewerten wir dann gemeinsam vor Ort, ob eine gezielte Reparatur reicht "
        "oder ab wann eine Sanierung wirtschaftlicher ist.\n\n"
        "Bis dahin wünsche ich Ihnen viel Erfolg bei Ihren Projekten und werde Sie hierzu nicht weiter "
        "kontaktieren."
    ),
    ("produktion", 1): (
        "wenn in Ihrem Betrieb eine Fliese lose ist, eine Fuge ausbricht, ein Rinnenanschluss undicht wird "
        "oder Gefälle und Abläufe Probleme machen, muss nicht gleich der gesamte Boden neu verlegt werden. "
        "Eine Schadstelle lässt sich in vielen Fällen gezielt instand setzen, ohne kompletten "
        "Produktionsstopp.\n\n"
        "Ich bin {sender} von der HSB Hexagon Säurebau GmbH. Für eine Ersteinschätzung genügt ein Foto der "
        "Stelle oder eine kurze Beschreibung. Wir prüfen innerhalb eines Arbeitstags kostenfrei, ob eine "
        "gezielte Reparatur ausreicht.{link}\n\n"
        "Das Foto können Sie auch direkt als Antwort auf diese E-Mail senden."
    ),
    ("produktion", 2): (
        "kurz zu meiner Nachricht von vor ein paar Tagen: Wenn Feuchte durch offene Fugen oder Schadstellen "
        "eindringt, drohen Folgeschäden. Je früher eine Schadstelle instand gesetzt wird, desto kleiner bleibt "
        "der Eingriff; über Teilflächen und kurze Sperrzeiten ist das in vielen Fällen im laufenden Betrieb "
        "möglich.\n\n"
        "Fällt Ihnen in Ihrem Betrieb eine Stelle ein, die Sie schon länger beobachten? Schicken Sie mir gern "
        "ein Foto für eine erste Einschätzung, ob eine Reparatur wirtschaftlich ist."
    ),
    ("produktion", 3): (
        "ich melde mich ein letztes Mal zu diesem Thema, um Sie nicht weiter zu belasten. Wenn Fugen, Kanten "
        "und Bodenflächen in Ihrem Betrieb derzeit intakt sind, ist das erfreulich.\n\n"
        "Sollten später Schadstellen auffallen oder Sanierungsfragen auftauchen, antworten Sie einfach auf "
        "diese Nachricht. Vor jeder Reparatur klären wir Ursache und Umfang, damit der Boden fachgerecht "
        "instand gesetzt wird, statt nur kosmetisch überdeckt zu werden.\n\n"
        "Bis dahin wünsche ich Ihnen weiterhin einen reibungslosen Betrieb."
    ),
}

_REPAIR_LINK_LABEL = {
    "architekten": "Ersteinschätzung mit Fotos oder Bestandsdaten",
    "produktion": "Schadstelle beschreiben oder Foto senden",
}

# Anrede nur mit verifizierter Anrede + Nachname; sonst neutral (Owner-Entscheidung 2026-11-04).
NEUTRAL_GREETING = "Sehr geehrte Damen und Herren,"
_GREETING_TITLES = {"dr.": "Dr.", "prof.": "Prof.", "dr.-ing.": "Dr.-Ing."}
_NAME_TOKEN_RE = re.compile(r"^[A-ZÄÖÜ][a-zäöüß]+(?:[-'’][A-ZÄÖÜ]?[a-zäöüß]+)*$")
_NOT_A_PERSON_RE = re.compile(
    r"gmbh|mbh|\bag\b|\bkg\b|gbr|\bug\b|architekt|büro|buero|halle|team|planung|ingenieur|verwaltung|"
    r"einkauf|technik|info|kontakt|service|abteilung|zentrale|werk|betrieb|firma|holding|gruppe",
    re.IGNORECASE,
)


def anrede_v2(lead: Dict[str, Any]) -> str:
    """'Sehr geehrter Herr Dr. Müller,' nur bei eindeutig belegter Anrede und Nachname."""
    anrede = str(lead.get("Anrede") or "").strip().lower().rstrip(".")
    nachname = str(lead.get("Nachname") or "").strip()
    if not (anrede and nachname):
        ap = str(lead.get("Ansprechpartner") or "").strip()
        ap = re.sub(r"(?i)^(guten tag|sehr geehrte[rs]?|hallo|liebe[rs]?)\s+", "", ap).strip(" ,")
        teile = ap.split()
        if len(teile) < 2:
            return NEUTRAL_GREETING
        anrede = teile[0].lower().rstrip(".")
        rest = teile[1:]
        titel = [_GREETING_TITLES[t.lower()] for t in rest if t.lower() in _GREETING_TITLES]
        namen = [t for t in rest if t.lower() not in _GREETING_TITLES]
        # Jeder weitere Titel oder jede Abkürzung (Mag., Arch., Dipl.-Ing., B.Sc.) macht den Eintrag unsicher.
        if not namen or any("." in t for t in namen):
            return NEUTRAL_GREETING
        nachname = _nachname_mit_titel(namen)
        if titel:
            nachname = " ".join(titel + [nachname])
    if anrede in ("herr", "herrn", "hr"):
        prefix = "Sehr geehrter Herr"
    elif anrede in ("frau", "fr"):
        prefix = "Sehr geehrte Frau"
    else:
        return NEUTRAL_GREETING
    name_tokens = [t for t in nachname.split() if t not in _GREETING_TITLES.values()]
    if (not name_tokens or _NOT_A_PERSON_RE.search(nachname)
            or not all(_NAME_TOKEN_RE.match(t) or t.lower() in _PARTICLES for t in name_tokens)
            or not _NAME_TOKEN_RE.match(name_tokens[-1])):
        return NEUTRAL_GREETING
    return f"{prefix} {nachname},"


# Absenderadresse in der Signatur = From-Postfach (nur dort wird gelesen).
_SENDER_COM = {"JOEL": "j-cherino@hsb-boden.com", "JORDI": "j-post@hsb-boden.com",
               "JORDIE": "j-post@hsb-boden.com"}

_PFLICHTANGABEN_V2 = (
    "HSB Hexagon Säurebau GmbH · Benzstraße 6 · 48599 Gronau\n"
    "Registergericht: Amtsgericht Coesfeld, HRB 21481 · Sitz: Gronau · Geschäftsführer: Jordie Post\n"
    "Impressum und Datenschutz: www.hsb-boden.de/impressum/ und www.hsb-boden.de/datenschutz/"
)



_HTML_FONT = "font-family:Arial,Helvetica,sans-serif;"
IMPRESSUM_URL = "https://www.hsb-boden.de/impressum/"
DATENSCHUTZ_URL = "https://www.hsb-boden.de/datenschutz/"
LEGAL_LINKS = frozenset({IMPRESSUM_URL, DATENSCHUTZ_URL})


def _html_paragraph(text: str) -> str:
    """Absatz aus dem Textteil; die Reparatur-URL wird zum Link mit dem Linktext davor."""
    lines = text.split("\n")
    if len(lines) == 2 and lines[1].strip() == REPAIR_URL:
        label = _html.escape(lines[0].rstrip(":"))
        return (f'<p style="margin:0 0 14px 0;"><a href="{REPAIR_URL}" '
                f'style="color:#1d4ed8;font-weight:bold;text-decoration:underline;">{label} &rarr;</a></p>')
    out = []
    for line in lines:
        esc = _html.escape(line)
        if line.strip().startswith("http"):
            url = _html.escape(line.strip(), quote=True)
            esc = f'<a href="{url}" style="color:#1d4ed8;">{url}</a>'
        out.append(esc)
    return '<p style="margin:0 0 14px 0;">' + "<br>\n".join(out) + "</p>"


def _html_v2(greeting: str, body: str, meta: Dict[str, str], mailbox: str, phone_label: str) -> str:
    """HTML-Teil mit der kanonischen HSB-Signatur (Logo 102x75, Pflichtangaben klein und grau).

    Der Textteil bleibt die gleichlautende reine Fassung; das Logo ist das einzige Bild, kein Anhang.
    """
    paras = [p for p in re.split(r"\n\s*\n", f"{greeting}\n\n{body}".strip()) if p.strip()]
    content = "\n".join(_html_paragraph(p) for p in paras)
    sig = (
        f'<p style="margin:18px 0 0 0;">Mit freundlichen Grüßen</p>'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="margin:14px 0 0 0;border-collapse:collapse;"><tr>'
        f'<td style="padding:0 14px 0 0;vertical-align:top;">'
        # Logo nur als Bild, ohne Link: der Reparatur-Link bleibt der einzige Klick-Link.
        f'<img src="{LOGO_URL}" alt="HSB Hexagon Säurebau GmbH" width="102" height="75" '
        f'style="display:block;border:0;outline:none;width:102px;height:75px;-ms-interpolation-mode:bicubic;"></td>'
        f'<td style="padding:0 0 0 14px;border-left:2px solid #c8102e;vertical-align:top;{_HTML_FONT}'
        f'font-size:13px;line-height:1.5;color:#1f2937;">'
        f'<strong style="font-size:14px;color:#111827;">{_html.escape(meta["sender_name"])}</strong><br>'
        f'<span style="color:#4b5563;">{_html.escape(meta["sender_role"])}</span><br>'
        f'HSB Hexagon Säurebau GmbH<br>'
        f'{phone_label}: {_html.escape(meta["sender_phone"])}<br>'
        f'<a href="mailto:{mailbox}" style="color:#1d4ed8;text-decoration:none;">{mailbox}</a>'
        f'</td></tr></table>'
    )
    # Abmelden öffnet eine Antwort ans eigene Postfach: kein weiterer Web-Link, sichtbarer Wortlaut wie im Textteil.
    optout = _html.escape(OPTOUT_LINE_V2).replace(
        "‚Abmelden‘", f'<a href="mailto:{mailbox}?subject=Abmelden" style="color:#4b5563;text-decoration:underline;">‚Abmelden‘</a>')
    legal_link = '<a href="{}" style="color:#6b7280;text-decoration:underline;">{}</a>'
    # Die letzte Zeile nennt im Textteil beide Adressen; im HTML sind es zwei echte Links.
    legal_lines = [_html.escape(l) for l in _PFLICHTANGABEN_V2.split("\n")[:-1]]
    legal_lines.append(f'{legal_link.format(IMPRESSUM_URL, "Impressum")} · {legal_link.format(DATENSCHUTZ_URL, "Datenschutz")}')
    footer = (
        f'<p style="margin:22px 0 0 0;{_HTML_FONT}font-size:12px;color:#4b5563;">{optout}</p>'
        f'<p style="margin:10px 0 0 0;padding-top:10px;border-top:1px solid #e5e7eb;{_HTML_FONT}'
        f'font-size:11px;line-height:1.45;color:#6b7280;">'
        + "<br>".join(legal_lines)
        + "</p>"
    )
    return ('<!DOCTYPE html>\n<html><head><meta charset="utf-8"></head>\n'
            f'<body style="margin:0;{_HTML_FONT}font-size:14px;line-height:1.55;color:#1f2937;">\n'
            f'<div style="max-width:640px;">{content}{sig}{footer}</div>\n</body></html>\n')


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


def _subject_v2(segment: str, firma_short: str, variant: str = "standard") -> str:
    if variant == "reparatur":
        return _SUBJECTS_REPARATUR[segment]
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
    variant: Literal["standard", "reparatur"] = "standard",
) -> Dict[str, Any]:
    """Reiner-Text-Mail v2. Schritt 2/3 antworten im Thread von Schritt 1 und enthalten keinen Link."""
    if variant not in ("standard", "reparatur"):
        raise ValueError(f"Unknown variant: {variant!r}")
    if step not in (1, 2, 3):
        raise ValueError(f"step must be 1, 2 or 3, got {step!r}")
    norm_owner = owner.strip().upper() if isinstance(owner, str) else ""
    if norm_owner not in CANONICAL_FLYERS:
        raise ValueError("INVALID_OWNER")
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
    planungsteam = f"Ihr Team bei {firma_kurz}" if firma_kurz else "Ihr Planungsteam"

    segment = segment_for(lead)
    template_id = f"v2-{segment}-reparatur-s{step}" if variant == "reparatur" else f"v2-{segment}-s{step}"

    link = ""
    if step == 1 and variant == "reparatur":
        # Lesbarer Link statt Klick-Token: kein Hash im Sichttext (Owner-Entscheidung 2026-11-04).
        link = f"\n\n{_REPAIR_LINK_LABEL[segment]}:\n{REPAIR_URL}"
    elif step == 1:
        url = click_url or FLYER_LANDING_URL.format(segment=segment)
        link = f"\n\nEine Übersicht finden Sie hier:\n{url}"
    bodies = _BODIES_REPARATUR if variant == "reparatur" else _BODIES_V2
    body = bodies[(segment, step)].format(
        sender=meta["sender_name"], bei=bei, planungsteam=planungsteam, link=link,
    )

    phone = meta["sender_phone"]
    phone_label = "Mobil" if phone.replace(" ", "").startswith("01") else "Telefon"
    signature = (
        "Mit freundlichen Grüßen\n"
        f"{meta['sender_name']}\n"
        f"{meta['sender_role']}\n"
        "HSB Hexagon Säurebau GmbH\n"
        f"{phone_label}: {phone}\n"
        f"E-Mail: {_SENDER_COM[norm_owner]}"
    )
    body_text = (
        f"{anrede_v2(lead)}\n\n{body}\n\n{signature}\n\n{OPTOUT_LINE_V2}\n\n{_PFLICHTANGABEN_V2}\n"
    )

    body_html = _html_v2(anrede_v2(lead), body, meta, _SENDER_COM[norm_owner], phone_label)

    if step == 1:
        subject = _subject_v2(segment, firma_kurz, variant=variant)
        in_reply_to = references = None
    else:
        original = re.sub(r"^(?:re|aw):\s*", "", str(thread["subject"]).strip(), flags=re.IGNORECASE)
        subject = f"Re: {original}"
        in_reply_to = references = thread["message_id"]

    return {
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "to_email": to_addr,
        "lead_id": lead_id,
        "segment": segment,
        "template_id": template_id,
        "copy_rev": REPARATUR_COPY_REV if variant == "reparatur" else "",
        "in_reply_to": in_reply_to,
        "references": references,
    }
