import os
import re
from pathlib import Path
from typing import Dict, Any

from hsb_core import sanitize_company_name
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
