import os
import re
from pathlib import Path
from typing import Dict, Any

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "canonical"

CANONICAL_FLYERS = {
    "JOEL": {
        "filename": "HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "path": str(ASSETS_DIR / "HSB-Flyer-Joel-Cherino_FINAL.pdf"),
        "sender_name": "Joel Cherino Diaz",
        "sender_role": "Vertrieb & Kundenbetreuung",
        "sender_phone": "+49 2562 9463030",
        "sender_email": "j-cherino@hsb-boden.de",
        "reply_to": "Joel Cherino Diaz <j-cherino@hsb-boden.de>",
    },
    "JORDI": {
        "filename": "HSB-Flyer-Jordie-Post_FINAL.pdf",
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

    raw_comp = str(lead.get("Firma") or lead.get("Firmenname") or lead.get("Company") or "").strip()
    company_name = re.sub(r"https?://(?:www\.)?", "", raw_comp, flags=re.IGNORECASE)
    company_name = re.sub(r"\.(?:de|com|ch|at)/?$", "", company_name, flags=re.IGNORECASE).strip()
    if not company_name or any(f in to_addr.lower() for f in ["@gmail.", "@gmx.", "@web.", "@t-online."]):
        subject_target = "Ihr Unternehmen"
    else:
        subject_target = company_name

    subject = f"Industrieböden für {subject_target} – Beratung von {owner_meta['sender_name']}"
    greeting = anrede_fuer_lead(lead)

    body_html = f"""<div style="font-family: Arial, sans-serif; font-size: 14px; color: #222; line-height: 1.5;">
    <p><img src="{LOGO_URL}" alt="HSB Hexagon Säurebau Logo" width="102" height="75" style="display: block; border: 0; outline: none; text-decoration: none;" /></p>
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
    Web: <a href="https://www.hsb-boden.de">www.hsb-boden.de</a></p>
    <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;" />
    <p style="font-size: 11px; color: #777;">
    <strong>HSB Hexagon Säurebau GmbH</strong> &middot; Benzstraße 6 &middot; 48599 Gronau<br />
    Registergericht: Amtsgericht Coesfeld, HRB 21481 &middot; Sitz: Gronau<br />
    Geschäftsführer: Jordie Post<br />
    Falls Sie keine weiteren Informationen wünschen: <a href="https://www.hsb-boden.de/abmelden">Hier abmelden</a> oder per Antwort mit dem Betreff &bdquo;Abmelden&ldquo;.
    </p>
</div>"""

    return {
        "subject": subject,
        "body_html": body_html,
        "to_address": to_addr,
        "flyer_path": owner_meta["path"],
        "flyer_filename": owner_meta["filename"],
        "logo_url": LOGO_URL,
        "reply_to": owner_meta["reply_to"],
    }
