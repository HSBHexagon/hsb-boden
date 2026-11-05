#!/usr/bin/env python3
"""Tiefenprüfung: jeder Entwurf gegen ein frisches Rendering aus dem CRM-Schnappschuss des Audits.

Liest nur das private Audit-Verzeichnis, spricht weder IMAP noch das CRM an. Stdout enthält nur
Zahlen und Codes, nie Adressen, Lead-IDs oder Firmennamen. Exit 0 PERFECT, 3 NOT_READY, 2 Schnappschuss
unvollständig.
"""
from __future__ import annotations

import argparse
from collections import Counter
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys

from canonical_template_factory import LOGO_URL, REPAIR_URL, REPARATUR_COPY_REV, render_email_v2
from hsb_core import normalize_owner
from sales_reconciliation import SENDERS, queue_block_reasons

CONTACTED = {'ALREADY_CONTACTED', 'ALREADY_CONTACTED_DOMAIN'}
HUMAN_REVIEW = {'COMPANY_UNVERIFIED', 'INBOUND_REQUIRES_REVIEW'}
RESAVED = 'LEAD_ID_INFERRED_ONLY'
EXIT_PERFECT, EXIT_INCOMPLETE, EXIT_NOT_READY = 0, 2, 3


class IncompleteSnapshot(Exception):
    """Der Schnappschuss taugt nicht als Beleg; die Meldung ist ein Code ohne Daten."""


class _TextExtractor(HTMLParser):
    _BLOCK = {'p', 'div', 'br', 'tr', 'td', 'table', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'blockquote', 'hr'}
    _SKIP = {'head', 'style', 'script', 'title'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self.skip += 1
        elif tag in self._BLOCK:
            self.out.append(' ')

    def handle_endtag(self, tag):
        if tag in self._SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self._BLOCK:
            self.out.append(' ')

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def _collapse(text: str) -> str:
    return ' '.join(str(text).split())


def _html_visible(markup: str) -> str:
    parser = _TextExtractor()
    parser.feed(markup)
    parser.close()
    return _collapse(''.join(parser.out))


def _lines(text: str) -> str:
    """Dekodierten Inhalt vergleichbar machen: Zeilenenden und Zeilenend-Leerraum zählen nicht."""
    unified = str(text).replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join(line.rstrip() for line in unified.split('\n')).strip()


def _parse(raw: bytes):
    return BytesParser(policy=policy.default).parsebytes(raw)


def _part(msg, content_type: str) -> str | None:
    for part in msg.walk():
        if part.get_content_type() == content_type and not part.is_attachment():
            try:
                return part.get_content()
            except (LookupError, UnicodeError):
                return None
    return None


def visible_text(raw: bytes) -> str:
    msg = _parse(raw)
    markup = _part(msg, 'text/html')
    if markup is not None:
        return _html_visible(markup)
    return _collapse(_part(msg, 'text/plain') or '')


def _render(lead: dict, owner: str) -> dict:
    return render_email_v2(lead, owner, step=1, variant='reparatur')


def deep_check(raw: bytes, lead: dict, owner: str) -> list[str]:
    try:
        fresh = _render(lead, owner)
    except ValueError:
        return ['RENDER_FAILED']
    msg = _parse(raw)
    plain, markup = _part(msg, 'text/plain'), _part(msg, 'text/html')
    codes = []
    if _collapse(msg.get('Subject') or '') != _collapse(fresh['subject']):
        codes.append('SUBJECT_DIFFERS')
    if plain is None or _lines(plain) != _lines(fresh['body_text']):
        codes.append('TEXT_DIFFERS')
    if markup is None or _lines(markup) != _lines(fresh['body_html']):
        codes.append('HTML_DIFFERS')
    if markup is None or f'src="{LOGO_URL}"' not in markup:
        codes.append('LOGO_MISSING')
    bodies = html.unescape('\n'.join(p for p in (plain, markup) if p))
    links = {u for u in re.findall(r'https?://[^\s<>"\x27]+', bodies) if u != LOGO_URL}
    if links != {REPAIR_URL}:
        codes.append('LINK_NOT_SINGLE')
    if str(msg.get('X-HSB-Copy-Rev') or '').strip() != REPARATUR_COPY_REV:
        codes.append('REV_WRONG')
    if str(msg.get('X-HSB-Template-ID') or '').strip() != fresh['template_id']:
        codes.append('TEMPLATE_WRONG')
    if [a.lower() for _, a in getaddresses([str(msg.get('From') or '')])] != [SENDERS[owner]]:
        codes.append('FROM_WRONG')
    if any(p.is_attachment() or p.get_content_maintype() not in ('multipart', 'text') for p in msg.walk()):
        codes.append('ATTACHMENT_PRESENT')
    if str(lead.get('Email_Template_ID') or '').strip() != fresh['template_id']:
        codes.append('CRM_TEMPLATE_STALE')
    if str(lead.get('Draft_ID') or '').strip() != str(msg.get('Message-ID') or '').strip():
        codes.append('CRM_BINDING_DIFFERS')
    return codes


def _code(issue) -> str:
    """Nur der Code einer Meldung; Details wie Adressen oder URLs bleiben privat."""
    match = re.match(r'[A-Z][A-Z0-9_]*', str(issue))
    return match.group() if match else 'UNKNOWN_ISSUE'


def _text_unchanged(raw: bytes, lead: dict, owner: str) -> bool:
    try:
        fresh = _render(lead, owner)
    except ValueError:
        return False
    return visible_text(raw) in {_html_visible(fresh['body_html']), _collapse(fresh['body_text'])}


def classify(record: dict, lead: dict | None, raw: bytes) -> tuple[str, str]:
    owner = record['owner']
    issues = [_code(i) for i in record.get('issues', [])]
    if CONTACTED & set(issues):
        return 'HELD', 'ALREADY_CONTACTED'
    if record.get('internal_test'):
        return 'HELD', 'INTERNAL_TEST'
    if not lead:
        return 'DEFECT', issues[0] if issues else 'CRM_RECIPIENT_MISSING'
    if queue_block_reasons(lead):
        return 'HELD', 'INELIGIBLE'
    if HUMAN_REVIEW & set(issues):
        return 'HELD', 'HUMAN_REVIEW'
    if RESAVED in issues:
        return ('DEFECT', 'CLIENT_RESAVED') if _text_unchanged(raw, lead, owner) else ('HELD', 'HUMAN_EDITED')
    if issues:
        return 'DEFECT', issues[0]
    codes = deep_check(raw, lead, owner)
    if codes:
        return 'DEFECT', codes[0]
    return ('OK', '') if record.get('sendable') else ('DEFECT', 'NOT_SENDABLE')


def _load_json(path: Path, code: str):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise IncompleteSnapshot(code) from exc


def _load_leads(audit_dir: Path) -> dict[str, dict]:
    snapshot = _load_json(audit_dir / 'crm-original.json', 'CRM_SNAPSHOT_UNREADABLE')
    try:
        rows = snapshot['valueRanges'][0]['values']
    except (KeyError, IndexError, TypeError) as exc:
        raise IncompleteSnapshot('CRM_SNAPSHOT_INVALID') from exc
    if len(rows) < 2:
        raise IncompleteSnapshot('CRM_SNAPSHOT_EMPTY')
    leads = {}
    for row in rows[1:]:
        lead = dict(zip(rows[0], row))
        leads.setdefault(str(lead.get('Lead-ID') or ''), lead)
    return leads


def _read_raw(record: dict) -> bytes:
    try:
        raw = Path(record['path']).read_bytes()
    except (KeyError, TypeError, OSError) as exc:
        raise IncompleteSnapshot('RAW_MESSAGE_MISSING') from exc
    if hashlib.sha256(raw).hexdigest() != record.get('sha256'):
        raise IncompleteSnapshot('RAW_MESSAGE_HASH_MISMATCH')
    return raw


def verify_audit_dir(audit_dir: Path) -> dict:
    audit_dir = Path(audit_dir)
    drafts = _load_json(audit_dir / 'drafts.json', 'DRAFTS_UNREADABLE')
    balances = _load_json(audit_dir / 'leads.json', 'LEADS_UNREADABLE')
    leads = _load_leads(audit_dir)
    owners = {o: {'scanned': 0, 'ok': 0, 'held': Counter(), 'defects': Counter(), 'eligible_without_draft': 0}
              for o in SENDERS}
    deep_defects = []
    for record in drafts:
        owner = normalize_owner(record.get('owner'))
        if owner not in owners:
            raise IncompleteSnapshot('UNKNOWN_OWNER')
        raw = _read_raw(record)
        bucket, reason = classify(record, leads.get(str(record.get('lead_id') or '')), raw)
        stats = owners[owner]
        stats['scanned'] += 1
        if bucket == 'OK':
            stats['ok'] += 1
        elif bucket == 'HELD':
            stats['held'][reason] += 1
        else:
            stats['defects'][reason] += 1
            if not record.get('issues'):
                deep_defects.append(f"{owner}|{record.get('uidvalidity')}|{record.get('uid')}|{record.get('sha256')}")
    if any(stats['scanned'] == 0 for stats in owners.values()):
        raise IncompleteSnapshot('MAILBOX_WITHOUT_DRAFTS')
    for balance in balances:
        owner = normalize_owner(balance.get('owner'))
        if owner in owners and balance.get('reasons') == ['NO_DRAFT']:
            owners[owner]['eligible_without_draft'] += 1
    target = audit_dir / 'deep_defects.json'
    target.write_text(json.dumps(sorted(deep_defects)), encoding='utf-8')
    os.chmod(target, 0o600)
    perfect = all(s['ok'] > 0 and not s['defects'] and not s['eligible_without_draft']
                  and s['ok'] + sum(s['held'].values()) == s['scanned'] for s in owners.values())
    return {'owners': {o: dict(s, held=dict(s['held']), defects=dict(s['defects'])) for o, s in owners.items()},
            'verdict': 'PERFECT' if perfect else 'NOT_READY', 'customer_emails_sent': 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_audit_dir(args.audit_dir)
    except IncompleteSnapshot as exc:
        print(json.dumps({'verdict': 'INCOMPLETE', 'reason': str(exc), 'customer_emails_sent': 0}))
        return EXIT_INCOMPLETE
    print(json.dumps(result, indent=2, sort_keys=True))
    return EXIT_PERFECT if result['verdict'] == 'PERFECT' else EXIT_NOT_READY


if __name__ == '__main__':
    sys.exit(main())
