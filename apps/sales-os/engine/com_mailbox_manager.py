#!/usr/bin/env python3
"""
HSB Sales OS - .com Mailbox Manager (All-Inkl / KASServer IMAP & SMTP Engine).
Ermoeglicht universellen Zugriff fuer Claude Code (CC), Antigravity (AG) und CLI.

Funktionen:
1. Native IMAP-SSL (Port 993) & SMTP-SSL (Port 465) Integration
2. Atomare Entwurfserstellung in 'Entw&APw-rfe' mit kanonischem Flyer
3. Universell ausfuehrbar ohne Azure/OAuth-Token-Verfall
4. Reconciliation (SentItems & Replies) fuer das ALL_LEADS Google Sheet
"""
from __future__ import annotations

import argparse
import email
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
import html
import hashlib
import imaplib
import os
from pathlib import Path
import re
import smtplib
import ssl
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from hsb_config import get_com_mailbox_config


def html_to_plaintext(source):
    from html.parser import HTMLParser
    class TextParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts=[];self.hidden=0
        def handle_starttag(self,tag,attrs):
            if tag in {'script','style'}:self.hidden+=1
            elif not self.hidden and tag in {'br','p','div','li'}:self.parts.append('\n')
        def handle_endtag(self,tag):
            if tag in {'script','style'}:self.hidden=max(0,self.hidden-1)
            elif not self.hidden and tag in {'p','div','li'}:self.parts.append('\n')
        def handle_data(self,data):
            if not self.hidden:self.parts.append(data)
    parser=TextParser();parser.feed(source);parser.close()
    return ''.join(parser.parts).strip()


def stable_inbound_id(raw, owner, rfc_message_id=''):
    return str(rfc_message_id).strip() or f'COM_IMAP:{owner}:SHA256:{hashlib.sha256(raw).hexdigest()}'


class ComMailboxClient:
    """IMAP/SMTP Client fuer ein HSB .com Postfach."""

    def __init__(self, owner: str = 'JOEL', timeout: int = 15):
        self.owner = owner.strip().upper()
        self.cfg = get_com_mailbox_config(self.owner)
        self.timeout = timeout
        self.ssl_context = ssl.create_default_context()

    def _get_imap(self) -> imaplib.IMAP4_SSL:
        imap = imaplib.IMAP4_SSL(
            self.cfg['imap_server'],
            self.cfg['imap_port'],
            ssl_context=self.ssl_context
        )
        if hasattr(imap, 'sock') and imap.sock:
            imap.sock.settimeout(25.0)
        imap.login(self.cfg['username'], self.cfg['password'])
        return imap

    def test_connection(self) -> Dict[str, Any]:
        """Testet IMAP- und SMTP-Verbindung."""
        result = {'owner': self.owner, 'email': self.cfg['email'], 'imap': False, 'smtp': False, 'folders': []}
        try:
            with self._get_imap() as imap:
                result['imap'] = True
                typ, folders = imap.list()
                result['folders'] = [f.decode(errors='ignore').split(' "/" ')[-1].strip(' "') for f in folders]
        except Exception as e:
            result['imap_error'] = str(e)

        try:
            with smtplib.SMTP_SSL(self.cfg['smtp_server'], self.cfg['smtp_port'], context=self.ssl_context, timeout=self.timeout) as smtp:
                smtp.login(self.cfg['username'], self.cfg['password'])
                result['smtp'] = True
        except Exception as e:
            result['smtp_error'] = str(e)

        return result

    def get_counts(self) -> Dict[str, int]:
        """Gibt die Anzahl der Mails in Entwuerfe, Gesendet und INBOX zurueck."""
        counts = {'drafts': 0, 'sent': 0, 'inbox': 0}
        with self._get_imap() as imap:
            for folder, key in [(self.cfg['drafts_folder'], 'drafts'), (self.cfg['sent_folder'], 'sent'), (self.cfg['inbox_folder'], 'inbox')]:
                try:
                    res, _ = imap.select(folder, readonly=True)
                    if res == 'OK':
                        typ, data = imap.search(None, 'ALL')
                        counts[key] = len(data[0].split()) if data and data[0] else 0
                except Exception:
                    pass
        return counts

    def _assert_draft_capacity(self, imap, recipients):
        """Existing target met or ambiguous retry: preserve all originals."""
        from email.utils import getaddresses
        typ,_=imap.select(self.cfg['drafts_folder'],readonly=True)
        if typ!='OK':raise RuntimeError('DRAFT_FOLDER_UNAVAILABLE')
        typ,data=imap.uid('search',None,'ALL')
        if typ!='OK':raise RuntimeError('DRAFT_SEARCH_FAILED')
        if data and data[0] and len(data[0].split())>=50:
            raise RuntimeError('DRAFT_TARGET_ALREADY_MET: reconcile existing drafts')
        normalized=[r.strip().lower() for r in recipients]
        if len(normalized)!=len(set(normalized)):raise RuntimeError('DUPLICATE_DRAFT_INPUT')
        for recipient in normalized:
            typ,data=imap.uid('search',None,'HEADER','To',f'"{recipient}"')
            if typ!='OK':raise RuntimeError('DRAFT_RECIPIENT_SEARCH_FAILED')
            if data and data[0]:raise RuntimeError('EXISTING_DRAFT_REQUIRES_RECONCILIATION')

    def create_draft(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        flyer_path: Optional[str] = None,
        flyer_filename: Optional[str] = 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
        custom_message_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Erstellt einen echten Outlook-/IMAP-Entwurf direkt im Ordner 'Entw&APw-rfe'.
        """
        if not to_email or '@' not in to_email:
            raise ValueError(f'Ungueltige Empfaengeradresse: {to_email}')

        fbytes = Path(flyer_path).read_bytes() if flyer_path else None
        raw_bytes, msg_id = self.build_draft_message(to_email,subject,body_html,
            flyer_bytes=fbytes,flyer_filename=flyer_filename,custom_message_id=custom_message_id)

        with self._get_imap() as imap:
            self._assert_draft_capacity(imap,[to_email])
            folder = self.cfg['drafts_folder']
            res, data = imap.append(
                folder,
                r'(\Draft)',
                imaplib.Time2Internaldate(time.time()),
                raw_bytes
            )
            if res != 'OK':
                raise RuntimeError(f'Fehler beim Speichern des Entwurfs: {data}')

        return True, msg_id

    def build_draft_message(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        flyer_bytes: Optional[bytes] = None,
        flyer_filename: Optional[str] = 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
        custom_message_id: Optional[str] = None
    ) -> Tuple[bytes, str]:
        if not to_email or '@' not in to_email:
            raise ValueError(f'Ungueltige Empfaengeradresse: {to_email}')

        from email.message import EmailMessage
        from urllib.parse import unquote
        msg = EmailMessage()
        msg['From'] = f'{self.cfg["display_name"]} <{self.cfg["email"]}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg_id = custom_message_id or make_msgid(domain='hsb-boden.com')
        msg['Message-ID'] = msg_id
        msg['X-Unsent'] = '1'
        ids = set(re.findall(r'HSB-\d{8}-\d+',unquote(body_html)))
        if len(ids)==1:
            msg['X-HSB-Lead-ID']=next(iter(ids))
        plain = html_to_plaintext(body_html)
        # Keep actionable URLs in the plain-text alternative.
        urls = re.findall(r'https?://[^\s<>"\x27]+',html.unescape(body_html))
        msg.set_content(html.unescape(plain) + "\n\n" + "\n".join(dict.fromkeys(urls)))
        msg.add_alternative(body_html,subtype='html')

        if flyer_bytes:
            msg.add_attachment(flyer_bytes,maintype='application',subtype='pdf',
                filename=flyer_filename or 'HSB-HEXAGON-Industrieboeden-Flyer.pdf')

        return msg.as_bytes(), msg_id

    def create_drafts_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Erstellt eine Liste von Entwuerfen in einer einzigen persistenten IMAP-Verbindung."""
        results = []
        flyer_cache: Dict[str, bytes] = {}

        for it in items:
            fpath = it.get('flyer_path')
            if fpath and fpath not in flyer_cache and os.path.exists(fpath):
                with open(fpath, 'rb') as f:
                    flyer_cache[fpath] = f.read()

        with self._get_imap() as imap:
            self._assert_draft_capacity(imap,[it['to_email'] for it in items])
            folder = self.cfg['drafts_folder']
            for it in items:
                fpath = it.get('flyer_path')
                fbytes = flyer_cache.get(fpath) if fpath else None
                try:
                    raw_bytes, mid = self.build_draft_message(
                        to_email=it['to_email'],
                        subject=it['subject'],
                        body_html=it['body_html'],
                        flyer_bytes=fbytes,
                        flyer_filename=it.get('flyer_filename'),
                        custom_message_id=it.get('custom_message_id')
                    )
                    res, data = imap.append(
                        folder,
                        r'(\Draft)',
                        imaplib.Time2Internaldate(time.time()),
                        raw_bytes
                    )
                    if res == 'OK':
                        results.append({'lead_id': it.get('lead_id'), 'row_idx': it.get('row_idx'), 'to': it['to_email'], 'subject': it['subject'], 'message_id': mid, 'status': 'DRAFTED', 'ok': True})
                    else:
                        results.append({'lead_id': it.get('lead_id'), 'row_idx': it.get('row_idx'), 'to': it['to_email'], 'subject': it['subject'], 'message_id': mid, 'status': f'ERROR_{data}', 'ok': False})
                except Exception as ex:
                    results.append({'lead_id': it.get('lead_id'), 'row_idx': it.get('row_idx'), 'to': it['to_email'], 'subject': it.get('subject'), 'status': f'EXCEPTION_{ex}', 'ok': False})
        return results

    def send_message(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        flyer_path: Optional[str] = None,
        flyer_filename: Optional[str] = "HSB-HEXAGON-Industrieboeden-Flyer.pdf",
        custom_message_id: Optional[str] = None,
        bcc_email: Optional[str] = None,
        body_plain: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Versendet eine E-Mail ueber SMTP-SSL und legt eine Kopie im Ordner Gesendet ab.
        Erzeugt zwingend RFC-konformes multipart/alternative (Plain-Text + HTML)
        sowie multipart/mixed falls ein Dateianhang vorhanden ist.
        """
        if not to_email or "@" not in to_email:
            raise ValueError(f"Ungueltige Empfaengeradresse: {to_email}")

        from outbound_safety import require_internal_test
        require_internal_test(to_email, bcc_email)

        # Vollstaendiges HTML-Dokument sicherstellen (verhindert HTML_MIME_NO_HTML_TAG)
        html_content = body_html.strip()
        if not html_content.lower().startswith("<!doctype") and not html_content.lower().startswith("<html"):
            html_content = (
                "<!DOCTYPE html>\n"
                "<html lang=\"de\">\n"
                "<head><meta charset=\"utf-8\"><title>" + html.escape(subject) + "</title></head>\n"
                "<body style=\"margin:0;padding:0;\">\n" + html_content + "\n</body>\n</html>"
            )

        # Plain-Text Version automatisch erzeugen falls nicht uebergeben
        if not body_plain:
            body_plain = html_to_plaintext(body_html)

        # 1. Text-Zweig: multipart/alternative (Plain-Text zuerst, HTML als bevorzugte Alternative)
        alt_part = MIMEMultipart("alternative")
        part_text = MIMEText(body_plain, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        alt_part.attach(part_text)
        alt_part.attach(part_html)

        # 2. Haupt-Container
        if flyer_path and os.path.exists(flyer_path):
            msg = MIMEMultipart("mixed")
            msg.attach(alt_part)
            with open(flyer_path, "rb") as f:
                part_pdf = MIMEApplication(f.read(), _subtype="pdf")
            fname = flyer_filename or os.path.basename(flyer_path)
            part_pdf.add_header("Content-Disposition", "attachment", filename=fname)
            msg.attach(part_pdf)
        else:
            msg = alt_part

        msg["From"] = f"{self.cfg['display_name']} <{self.cfg['email']}>"
        if self.cfg.get("reply_to"):
            msg["Reply-To"] = self.cfg["reply_to"]
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg["Date"] = formatdate(localtime=True)
        msg_id = custom_message_id or make_msgid(domain="hsb-boden.com")
        msg["Message-ID"] = msg_id

        raw_bytes = msg.as_bytes()

        # 1. SMTP Send (Envelope recipients: to_email + optional bcc)
        to_addrs = [to_email]
        if bcc_email and "@" in bcc_email:
            match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", bcc_email)
            if match:
                to_addrs.append(match.group(0))
            else:
                to_addrs.append(bcc_email.strip())

        with smtplib.SMTP_SSL(self.cfg["smtp_server"], self.cfg["smtp_port"], context=self.ssl_context, timeout=self.timeout) as smtp:
            smtp.login(self.cfg["username"], self.cfg["password"])
            if len(to_addrs) > 1:
                smtp.send_message(msg, to_addrs=to_addrs)
            else:
                smtp.send_message(msg)

        # 2. Nach SMTP-Akzeptanz gesonderten IMAP-Nachweis vermerken.
        # IMAP-Fehler duerfen niemals einen automatischen SMTP-Retry ausloesen.
        self.last_sent_copy_ok = False
        self.last_sent_copy_error = None
        try:
            with self._get_imap() as imap:
                result, _ = imap.append(
                    self.cfg["sent_folder"],
                    r"(\Seen)",
                    imaplib.Time2Internaldate(time.time()),
                    raw_bytes,
                )
                self.last_sent_copy_ok = result == "OK"
                if not self.last_sent_copy_ok:
                    self.last_sent_copy_error = "IMAP_APPEND_NOT_OK"
        except Exception as exc:
            self.last_sent_copy_error = type(exc).__name__

        return True, msg_id

    def deliver_verified_bytes(self, raw_bytes, recipient, *, journal):
        from outbound_safety import SendJournal
        if os.environ.get('HSB_CUSTOMER_SEND_ENABLED') != 'yes' or not isinstance(journal, SendJournal):
            raise PermissionError('Verified customer dispatch is disabled')
        parsed = email.message_from_bytes(raw_bytes)
        mid = str(parsed.get('Message-ID') or '')
        row = journal.db.execute(
            "SELECT owner,message_id,state FROM attempts WHERE email=?", (recipient.lower(),)
        ).fetchone()
        if row != (self.owner, mid, 'SMTP_UNKNOWN'):
            raise PermissionError('No durable matching SMTP reservation')
        with smtplib.SMTP_SSL(self.cfg['smtp_server'], self.cfg['smtp_port'],
                context=self.ssl_context, timeout=self.timeout) as smtp:
            smtp.login(self.cfg['username'], self.cfg['password'])
            refused = smtp.sendmail(self.cfg['email'], [recipient], raw_bytes)
            if refused:
                raise RuntimeError('SMTP_RECIPIENT_REFUSED')

    def list_drafts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Liest die neuesten Entwuerfe aus dem Entwurfsordner."""
        drafts = []
        with self._get_imap() as imap:
            res, _ = imap.select(self.cfg['drafts_folder'], readonly=True)
            if res != 'OK':
                return drafts
            typ, data = imap.search(None, 'ALL')
            if not data or not data[0]:
                return drafts
            msg_nums = data[0].split()
            for num in (msg_nums[-limit:] if limit else msg_nums):
                typ, msg_data = imap.fetch(num, '(RFC822.HEADER)')
                for part in msg_data:
                    if isinstance(part, tuple):
                        parsed = email.message_from_bytes(part[1])
                        drafts.append({
                            'num': num.decode(),
                            'to': str(parsed.get('To') or ''),
                            'subject': str(parsed.get('Subject') or ''),
                            'date': str(parsed.get('Date') or ''),
                            'message_id': str(parsed.get('Message-ID') or ''),
                        })
        return drafts

    def fetch_sent_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Liest gesendete Nachrichten aus dem Sent-Ordner."""
        items = []
        with self._get_imap() as imap:
            res, _ = imap.select(self.cfg['sent_folder'], readonly=True)
            if res != 'OK':
                return items
            typ, data = imap.search(None, 'ALL')
            if not data or not data[0]:
                return items
            msg_nums = data[0].split()
            for num in (msg_nums[-limit:] if limit else msg_nums):
                typ, msg_data = imap.fetch(num, '(BODY.PEEK[])')
                for part in msg_data:
                    if isinstance(part, tuple):
                        parsed = email.message_from_bytes(part[1])
                        recips_raw = str(parsed.get('To') or '')
                        recips = [r.strip().lower() for r in re.split(r'[,;]', recips_raw) if r.strip()]
                        items.append({
                            'id': str(parsed.get('Message-ID') or num.decode()),
                            'date_str': str(parsed.get('Date') or ''),
                            'recipients': recips,
                            'subject': str(parsed.get('Subject') or ''),
                            'internet_message_id': str(parsed.get('Message-ID') or ''),
                        })
        return items

    def fetch_inbound_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Liest eingehende Nachrichten aus dem Posteingang (INBOX)."""
        items = []
        with self._get_imap() as imap:
            res, _ = imap.select(self.cfg['inbox_folder'], readonly=True)
            if res != 'OK':
                return items
            typ, data = imap.search(None, 'ALL')
            if not data or not data[0]:
                return items
            msg_nums = data[0].split()
            for num in (msg_nums[-limit:] if limit else msg_nums):
                typ, msg_data = imap.fetch(num, '(BODY.PEEK[])')
                for part in msg_data:
                    if isinstance(part, tuple):
                        parsed = email.message_from_bytes(part[1])
                        body = ""
                        if parsed.is_multipart():
                            for p in parsed.walk():
                                if p.get_content_type() == "message/delivery-status":
                                    body += p.as_string() + "\n"
                                if p.get_content_type() in ("text/plain", "text/html"):
                                    payload = p.get_payload(decode=True)
                                    if payload:
                                        body += payload.decode(errors='replace') + "\n"
                        else:
                            payload = parsed.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors='replace')
                        items.append({
                            'id': stable_inbound_id(part[1],self.owner,parsed.get('Message-ID') or ''),
                            'date_str': str(parsed.get('Date') or ''),
                            'from': str(parsed.get('From') or ''),
                            'to': str(parsed.get('To') or ''),
                            'subject': str(parsed.get('Subject') or ''),
                            'body': body,
                            'internet_message_id': str(parsed.get('Message-ID') or ''),
                        })
        return items

    def clean_test_drafts(self, marker: str = 'TEST') -> int:
        """Loescht Entwuerfe, die mit dem Test-Marker markiert sind."""
        deleted = 0
        with self._get_imap() as imap:
            res, _ = imap.select(self.cfg['drafts_folder'])
            if res != 'OK':
                return 0
            typ, data = imap.search(None, 'ALL')
            if not data or not data[0]:
                return 0
            for num in data[0].split():
                typ, msg_data = imap.fetch(num, '(RFC822.HEADER)')
                for part in msg_data:
                    if isinstance(part, tuple):
                        parsed = email.message_from_bytes(part[1])
                        subj = str(parsed.get('Subject', ''))
                        to_addr = str(parsed.get('To', '')).lower()
                        if marker in subj or to_addr.endswith('@example.com') or to_addr.endswith('.example.com') or to_addr.startswith('test@'):
                            imap.store(num, '+FLAGS', r'\Deleted')
                            deleted += 1
            imap.expunge()
        return deleted

    def purge_all_drafts(self) -> int:
        """Loescht alle vorhandenen Entwuerfe im Entwurfsordner."""
        deleted = 0
        with self._get_imap() as imap:
            res, _ = imap.select(self.cfg['drafts_folder'])
            if res != 'OK':
                return 0
            typ, data = imap.search(None, 'ALL')
            if not data or not data[0]:
                return 0
            for num in data[0].split():
                imap.store(num, '+FLAGS', r'\Deleted')
                deleted += 1
            imap.expunge()
        return deleted

    def purge_drafts_for_recipient(self, to_email: str) -> int:
        """Loescht alle Entwuerfe fuer eine bestimmte Empfaengeradresse (Opt-Out Schutz)."""
        target = str(to_email or "").strip().lower()
        if not target or "@" not in target:
            return 0
        deleted = 0
        with self._get_imap() as imap:
            res, _ = imap.select(self.cfg['drafts_folder'])
            if res != 'OK':
                return 0
            typ, data = imap.search(None, 'HEADER', 'TO', target)
            if not data or not data[0]:
                return 0
            for num in data[0].split():
                imap.store(num, '+FLAGS', r'\Deleted')
                deleted += 1
            imap.expunge()
        return deleted


def print_status():
    print('=' * 80)
    print(' HSB SALES OS — .COM MAILBOX MONITOR (KASServer IMAP / SMTP)')
    print('=' * 80)
    print(f'{"Owner":<10} | {"E-Mail":<26} | {"IMAP":<6} | {"SMTP":<6} | {"Drafts":<8} | {"Sent":<6} | {"Inbox":<6}')
    print('-' * 80)
    for owner in ['JOEL', 'JORDI']:
        client = ComMailboxClient(owner)
        conn = client.test_connection()
        counts = client.get_counts()
        imap_status = 'OK' if conn['imap'] else 'FAIL'
        smtp_status = 'OK' if conn['smtp'] else 'FAIL'
        print(f'{owner:<10} | {conn["email"]:26} | {imap_status:<6} | {smtp_status:<6} | {counts["drafts"]:>8} | {counts["sent"]:>6} | {counts["inbox"]:>6}')
    print('=' * 80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HSB .com Mailbox Manager')
    parser.add_argument('--status', action='store_true', help='Status und Ordner-Zaehler beider Postfaecher anzeigen')
    parser.add_argument('--owner', choices=['JOEL', 'JORDI'], default='JOEL', help='Mailbox Owner')
    parser.add_argument('--test-draft', action='store_true', help='Test-Entwurf anlegen')
    parser.add_argument('--clean-tests', action='store_true', help='Test-Entwuerfe bereinigen')
    parser.add_argument('--purge-drafts', action='store_true', help='Alle vorhandenen Entwuerfe im Ordner Entwuerfe loeschen')
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.test_draft:
        client = ComMailboxClient(args.owner)
        ok, mid = client.create_draft(
            to_email='test@example.com',
            subject='TEST: HSB Sales OS .com Migration Check',
            body_html='<p>Dies ist ein automatisierter Test-Entwurf via IMAP.</p>'
        )
        print(f'Test-Entwurf fuer {args.owner} erfolgreich erstellt! Message-ID: {mid}')
    elif args.clean_tests:
        for owner in ['JOEL', 'JORDI']:
            c = ComMailboxClient(owner)
            n = c.clean_test_drafts()
            print(f'{owner}: {n} Test-Entwuerfe bereinigt.')
    elif args.purge_drafts:
        owners = [args.owner] if args.owner else ['JOEL', 'JORDI']
        for o in owners:
            c = ComMailboxClient(o)
            n = c.purge_all_drafts()
            print(f'{o}: {n} Entwuerfe vollstaendig geloescht.')
    else:
        print_status()
