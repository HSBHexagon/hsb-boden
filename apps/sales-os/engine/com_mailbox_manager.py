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

        msg = MIMEMultipart('mixed')
        msg['From'] = f'{self.cfg["display_name"]} <{self.cfg["email"]}>'
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8').encode()
        msg['Date'] = formatdate(localtime=True)
        msg_id = custom_message_id or make_msgid(domain='hsb-boden.com')
        msg['Message-ID'] = msg_id
        msg['X-Unsent'] = '1'

        part_html = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(part_html)

        if flyer_path and os.path.exists(flyer_path):
            with open(flyer_path, 'rb') as f:
                part_pdf = MIMEApplication(f.read(), _subtype='pdf')
            fname = flyer_filename or os.path.basename(flyer_path)
            part_pdf.add_header('Content-Disposition', 'attachment', filename=fname)
            msg.attach(part_pdf)

        raw_bytes = msg.as_bytes()

        with self._get_imap() as imap:
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
            for num in msg_nums[-limit:]:
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
            for num in msg_nums[-limit:]:
                typ, msg_data = imap.fetch(num, '(RFC822)')
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
            for num in msg_nums[-limit:]:
                typ, msg_data = imap.fetch(num, '(RFC822)')
                for part in msg_data:
                    if isinstance(part, tuple):
                        parsed = email.message_from_bytes(part[1])
                        body = ""
                        if parsed.is_multipart():
                            for p in parsed.walk():
                                if p.get_content_type() in ("text/plain", "text/html"):
                                    payload = p.get_payload(decode=True)
                                    if payload:
                                        body += payload.decode(errors='replace') + "\n"
                        else:
                            payload = parsed.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors='replace')
                        items.append({
                            'id': str(parsed.get('Message-ID') or num.decode()),
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
                        to_addr = str(parsed.get('To', ''))
                        if marker in subj or 'example.com' in to_addr or 'test@' in to_addr:
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
    else:
        print_status()
