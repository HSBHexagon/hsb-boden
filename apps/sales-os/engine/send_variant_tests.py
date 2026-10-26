#!/usr/bin/env python3
"""
HSB Sales OS - 3-Varianten-Test-Runner fuer optische & Zustellbarkeits-Entscheidung.
Versendet 3 gezielte Varianten an cherinodiaz@outlook.com:
- V1: B2B-Kaufmanns-Standard (Reines Outlook-Design, ohne Bilder, mit 241 KB Flyer)
- V2: Corporate-Design mit echtem Inline-CID-Logo (ohne externen Web-Request) + 241 KB Flyer
- V3: Dialog-Fokus (Text-only, ohne Anhang, bietet Flyer auf Wunsch an)
"""
import sys
import os
from pathlib import Path
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.utils import formatdate, make_msgid
import smtplib
import imaplib
import time

ENGINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ENGINE_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

from com_mailbox_manager import ComMailboxClient
from hsb_core import assert_asset_gate

FLYER_PATH = REPO_ROOT / "assets" / "canonical" / "HSB-Flyer-Jordie-Post_FINAL.pdf"
LOGO_PATH = REPO_ROOT / "assets" / "canonical" / "hsb-boden-logo.png"

FIRMA_DATEN = {
    "name": "HSB Hexagon Säurebau GmbH",
    "strasse": "Benzstraße 6",
    "plzOrt": "48599 Gronau",
    "telefon": "+49 2562 9463030",
    "web": "www.hsb-boden.de",
    "sitz": "Gronau",
    "registergericht": "Amtsgericht Coesfeld",
    "hrb": "HRB 21481",
    "geschaeftsfuehrer": "Jordie Post",
}

def get_footer_single_line(optout_url="https://www.hsb-boden.de/abmelden"):
    return (
        f'<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#64748b;line-height:1.45;">'
        f'{FIRMA_DATEN["name"]} &middot; Sitz: {FIRMA_DATEN["sitz"]}<br>'
        f'Registergericht: {FIRMA_DATEN["registergericht"]}, {FIRMA_DATEN["hrb"]} &middot; Geschäftsführer: {FIRMA_DATEN["geschaeftsfuehrer"]}<br>'
        f'<a href="https://www.hsb-boden.de/impressum/" style="color:#64748b;text-decoration:underline;">Impressum</a> &middot; '
        f'<a href="https://www.hsb-boden.de/datenschutz/" style="color:#64748b;text-decoration:underline;">Datenschutz</a> &middot; '
        f'<a href="{optout_url}" style="color:#64748b;text-decoration:underline;">Hier abmelden</a>'
        f'</p>'
    )

def send_raw_mime(client, to_addr, msg, bcc="j-post@hsb-boden.com"):
    from outbound_safety import require_internal_test
    require_internal_test(to_addr, bcc)
    raw_bytes = msg.as_bytes()
    to_addrs = [to_addr]
    if bcc and "@" in bcc:
        to_addrs.append(bcc)

    with smtplib.SMTP_SSL(client.cfg["smtp_server"], client.cfg["smtp_port"], context=client.ssl_context, timeout=client.timeout) as smtp:
        smtp.login(client.cfg["username"], client.cfg["password"])
        smtp.send_message(msg, to_addrs=to_addrs)

    # In Sent-Ordner via IMAP ablegen
    try:
        with client._get_imap() as imap:
            imap.append(
                client.cfg["sent_folder"],
                r"(\Seen)",
                imaplib.Time2Internaldate(time.time()),
                raw_bytes
            )
    except Exception as e:
        print(f"Warning: Sent append failed: {e}")

    return msg["Message-ID"]

def create_and_send_v1(client, to_addr):
    """V1: B2B-Kaufmanns-Standard (Reines Outlook-Design, kein Bild, mit Flyer)."""
    subject = "Industrieböden für gewerbliche Bauprojekte – Beratung von Jordie Post [Variante 1: Kaufmanns-Design]"

    body_text = (
        "Guten Tag,\n\n"
        "mein Name ist Jordie Post von der HSB Hexagon Säurebau GmbH. Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.\n\n"
        "Typische Themen bei Produktionsbetrieben:\n"
        "• Risse, Ablösungen und offene Fugen\n"
        "• Keimnester in Nassbereichen\n"
        "• stehendes Wasser durch falsches Gefälle\n"
        "• defekte Rinnen und Abläufe\n\n"
        "Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser Vorgehen von der Analyse bis zur dokumentierten Übergabe.\n\n"
        "Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.\n\n"
        "Mit freundlichen Grüßen\n\n"
        "Jordie Post\n"
        "Geschäftsführer\n"
        "HSB Hexagon Säurebau GmbH\n"
        "Benzstraße 6 · 48599 Gronau\n"
        "Tel. +49 2562 9463030\n"
        "j-post@hsb-boden.com · www.hsb-boden.de\n\n"
        "---\n"
        "Impressum: https://www.hsb-boden.de/impressum/ | Datenschutz: https://www.hsb-boden.de/datenschutz/ | Abmelden: https://www.hsb-boden.de/abmelden"
    )

    body_html = (
        f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;color:#1e293b;line-height:1.55;">'
        f'<p style="margin:0 0 12px 0;">Guten Tag,</p>'
        f'<p style="margin:0 0 12px 0;">mein Name ist Jordie Post von der HSB Hexagon Säurebau GmbH. '
        f'Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – '
        f'ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.</p>'
        f'<p style="margin:0 0 12px 0;">Typische Themen bei Produktionsbetrieben:<br>'
        f'&bull; Risse, Ablösungen und offene Fugen<br>'
        f'&bull; Keimnester in Nassbereichen<br>'
        f'&bull; stehendes Wasser durch falsches Gefälle<br>'
        f'&bull; defekte Rinnen und Abläufe</p>'
        f'<p style="margin:0 0 12px 0;">Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser '
        f'Vorgehen von der Analyse bis zur dokumentierten Übergabe.</p>'
        f'<p style="margin:0 0 16px 0;">Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.</p>'
        f'<p style="margin:0 0 4px 0;">Mit freundlichen Grüßen</p>'
        f'<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#1e293b;line-height:1.5;">'
        f'<strong>Jordie Post</strong><br>'
        f'Geschäftsführer<br>'
        f'{FIRMA_DATEN["name"]}<br>'
        f'{FIRMA_DATEN["strasse"]} &middot; {FIRMA_DATEN["plzOrt"]}<br>'
        f'Tel. {FIRMA_DATEN["telefon"]}<br>'
        f'<a href="mailto:j-post@hsb-boden.com" style="color:#0f172a;text-decoration:none;">j-post@hsb-boden.com</a> &middot; '
        f'<a href="https://www.hsb-boden.de" style="color:#0f172a;text-decoration:none;">www.hsb-boden.de</a>'
        f'</p>'
        f'{get_footer_single_line()}'
        f'</div>'
    )

    msg = MIMEMultipart("mixed")
    msg["From"] = f"Jordie Post <{client.cfg['email']}>"
    msg["Reply-To"] = client.cfg.get("reply_to", client.cfg["email"])
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="hsb-boden.com")

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt_part)

    with open(FLYER_PATH, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename="HSB-HEXAGON-Industrieboeden-Flyer.pdf")
    msg.attach(pdf_part)

    return send_raw_mime(client, to_addr, msg)

def create_and_send_v2(client, to_addr):
    """V2: Corporate-Design mit echtem Inline-CID-Logo (ohne HTTP-Anfrage) + Flyer."""
    subject = "Industrieböden für gewerbliche Bauprojekte – Beratung von Jordie Post [Variante 2: Corporate mit Inline-Logo]"

    body_text = (
        "Guten Tag,\n\n"
        "mein Name ist Jordie Post von der HSB Hexagon Säurebau GmbH. Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.\n\n"
        "Typische Themen bei Produktionsbetrieben:\n"
        "• Risse, Ablösungen und offene Fugen\n"
        "• Keimnester in Nassbereichen\n"
        "• stehendes Wasser durch falsches Gefälle\n"
        "• defekte Rinnen und Abläufe\n\n"
        "Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser Vorgehen von der Analyse bis zur dokumentierten Übergabe.\n\n"
        "Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.\n\n"
        "Mit freundlichen Grüßen\n\n"
        "Jordie Post\n"
        "Geschäftsführer\n"
        "HSB Hexagon Säurebau GmbH\n"
        "Benzstraße 6 · 48599 Gronau\n"
        "Tel. +49 2562 9463030\n"
        "j-post@hsb-boden.com · www.hsb-boden.de\n\n"
        "---\n"
        "Impressum: https://www.hsb-boden.de/impressum/ | Datenschutz: https://www.hsb-boden.de/datenschutz/ | Abmelden: https://www.hsb-boden.de/abmelden"
    )

    body_html = (
        f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;color:#1e293b;line-height:1.55;">'
        f'<p style="margin:0 0 12px 0;">Guten Tag,</p>'
        f'<p style="margin:0 0 12px 0;">mein Name ist Jordie Post von der HSB Hexagon Säurebau GmbH. '
        f'Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – '
        f'ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.</p>'
        f'<p style="margin:0 0 12px 0;">Typische Themen bei Produktionsbetrieben:<br>'
        f'&bull; Risse, Ablösungen und offene Fugen<br>'
        f'&bull; Keimnester in Nassbereichen<br>'
        f'&bull; stehendes Wasser durch falsches Gefälle<br>'
        f'&bull; defekte Rinnen und Abläufe</p>'
        f'<p style="margin:0 0 12px 0;">Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser '
        f'Vorgehen von der Analyse bis zur dokumentierten Übergabe.</p>'
        f'<p style="margin:0 0 16px 0;">Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.</p>'
        f'<p style="margin:0 0 4px 0;">Mit freundlichen Grüßen</p>'
        f'<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#1e293b;line-height:1.5;">'
        f'<strong>Jordie Post</strong><br>'
        f'Geschäftsführer<br>'
        f'{FIRMA_DATEN["name"]}<br>'
        f'{FIRMA_DATEN["strasse"]} &middot; {FIRMA_DATEN["plzOrt"]}<br>'
        f'Tel. {FIRMA_DATEN["telefon"]}<br>'
        f'<a href="mailto:j-post@hsb-boden.com" style="color:#0f172a;text-decoration:none;">j-post@hsb-boden.com</a> &middot; '
        f'<a href="https://www.hsb-boden.de" style="color:#0f172a;text-decoration:none;">www.hsb-boden.de</a>'
        f'</p>'
        f'<p style="margin:14px 0 0 0;">'
        f'<img src="cid:hsblogo" alt="{FIRMA_DATEN["name"]}" width="102" height="75" style="display:block;border:0;width:102px;height:75px;" />'
        f'</p>'
        f'{get_footer_single_line()}'
        f'</div>'
    )

    msg = MIMEMultipart("mixed")
    msg["From"] = f"Jordie Post <{client.cfg['email']}>"
    msg["Reply-To"] = client.cfg.get("reply_to", client.cfg["email"])
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="hsb-boden.com")

    # Related Container fuer Inline-Bild
    related_part = MIMEMultipart("related")
    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(body_html, "html", "utf-8"))
    related_part.attach(alt_part)

    # Logo als CID einbetten
    with open(LOGO_PATH, "rb") as f:
        img_part = MIMEImage(f.read())
    img_part.add_header("Content-ID", "<hsblogo>")
    img_part.add_header("Content-Disposition", "inline", filename="hsb-boden-logo.png")
    related_part.attach(img_part)

    msg.attach(related_part)

    # Flyer als PDF-Anhang
    with open(FLYER_PATH, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename="HSB-HEXAGON-Industrieboeden-Flyer.pdf")
    msg.attach(pdf_part)

    return send_raw_mime(client, to_addr, msg)

def create_and_send_v3(client, to_addr):
    """V3: Dialog-Fokus (Text-only, ohne Anhang, bietet Flyer auf Wunsch an)."""
    subject = "Industrieböden für gewerbliche Bauprojekte – Beratung von Jordie Post [Variante 3: Dialog-Fokus ohne Anhang]"

    body_text = (
        "Guten Tag,\n\n"
        "mein Name ist Jordie Post von der HSB Hexagon Säurebau GmbH. Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.\n\n"
        "Typische Themen bei Produktionsbetrieben:\n"
        "• Risse, Ablösungen und offene Fugen\n"
        "• Keimnester in Nassbereichen\n"
        "• stehendes Wasser durch falsches Gefälle\n"
        "• defekte Rinnen und Abläufe\n\n"
        "Wir haben eine 4-seitige Projektübersicht mit ausgeführten Flächen und unserem Vorgehen von der Analyse bis zur dokumentierten Übergabe vorbereitet.\n\n"
        "Soll ich Ihnen den Flyer kurz als PDF zusenden oder haben Sie aktuell eine konkrete Produktionsfläche, die geprüft werden soll?\n\n"
        "Mit freundlichen Grüßen\n\n"
        "Jordie Post\n"
        "Geschäftsführer\n"
        "HSB Hexagon Säurebau GmbH\n"
        "Benzstraße 6 · 48599 Gronau\n"
        "Tel. +49 2562 9463030\n"
        "j-post@hsb-boden.com · www.hsb-boden.de\n\n"
        "---\n"
        "Impressum: https://www.hsb-boden.de/impressum/ | Datenschutz: https://www.hsb-boden.de/datenschutz/ | Abmelden: https://www.hsb-boden.de/abmelden"
    )

    body_html = (
        f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;color:#1e293b;line-height:1.55;">'
        f'<p style="margin:0 0 12px 0;">Guten Tag,</p>'
        f'<p style="margin:0 0 12px 0;">mein Name ist Jordie Post von der HSB Hexagon Säurebau GmbH. '
        f'Wir planen, bauen und sanieren säurebeständige, hygienische Industrieböden – '
        f'ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.</p>'
        f'<p style="margin:0 0 12px 0;">Typische Themen bei Produktionsbetrieben:<br>'
        f'&bull; Risse, Ablösungen und offene Fugen<br>'
        f'&bull; Keimnester in Nassbereichen<br>'
        f'&bull; stehendes Wasser durch falsches Gefälle<br>'
        f'&bull; defekte Rinnen und Abläufe</p>'
        f'<p style="margin:0 0 12px 0;">Wir haben eine 4-seitige Projektübersicht mit ausgeführten Flächen und unserem '
        f'Vorgehen von der Analyse bis zur dokumentierten Übergabe vorbereitet.</p>'
        f'<p style="margin:0 0 16px 0;">Soll ich Ihnen den Flyer kurz als PDF zusenden oder haben Sie aktuell eine konkrete Produktionsfläche, die geprüft werden soll?</p>'
        f'<p style="margin:0 0 4px 0;">Mit freundlichen Grüßen</p>'
        f'<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#1e293b;line-height:1.5;">'
        f'<strong>Jordie Post</strong><br>'
        f'Geschäftsführer<br>'
        f'{FIRMA_DATEN["name"]}<br>'
        f'{FIRMA_DATEN["strasse"]} &middot; {FIRMA_DATEN["plzOrt"]}<br>'
        f'Tel. {FIRMA_DATEN["telefon"]}<br>'
        f'<a href="mailto:j-post@hsb-boden.com" style="color:#0f172a;text-decoration:none;">j-post@hsb-boden.com</a> &middot; '
        f'<a href="https://www.hsb-boden.de" style="color:#0f172a;text-decoration:none;">www.hsb-boden.de</a>'
        f'</p>'
        f'{get_footer_single_line()}'
        f'</div>'
    )

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Jordie Post <{client.cfg['email']}>"
    msg["Reply-To"] = client.cfg.get("reply_to", client.cfg["email"])
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="hsb-boden.com")

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    return send_raw_mime(client, to_addr, msg)

def main():
    target_email = "cherinodiaz@outlook.com"
    client = ComMailboxClient("JORDI")
    print(f"=== STARTE 3-VARIANTEN-TEST AN {target_email} ===")

    print("1/3 Sende Variante 1 (Kaufmanns-Design mit Flyer)...")
    id1 = create_and_send_v1(client, target_email)
    print(f"    ✓ V1 versendet! Message-ID: {id1}")
    time.sleep(2)

    print("2/3 Sende Variante 2 (Corporate mit Inline-CID-Logo & Flyer)...")
    id2 = create_and_send_v2(client, target_email)
    print(f"    ✓ V2 versendet! Message-ID: {id2}")
    time.sleep(2)

    print("3/3 Sende Variante 3 (Dialog-Fokus ohne Anhang)...")
    id3 = create_and_send_v3(client, target_email)
    print(f"    ✓ V3 versendet! Message-ID: {id3}")

    print("\n=== ALLE 3 TEST-MAILS ERFOLGREICH VERSENDET! ===")

if __name__ == "__main__":
    main()
