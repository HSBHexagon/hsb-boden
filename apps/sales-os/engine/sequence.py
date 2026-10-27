"""Sequenzplanung und dauerhaftes Journal. Erzeugt keine SMTP-Aufrufe."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import re
import sqlite3


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def workday_after(start, days=1):
    result = as_date(start)
    for _ in range(days):
        result += timedelta(days=1)
        while result.weekday() > 4:
            result += timedelta(days=1)
    return result


def next_step_due(lead, journal_rows, today):
    """Nur explizit journalisierte v2-Kontakte, niemals historische Erstkontakte nachfassen."""
    today = as_date(today)
    if today.weekday() > 4:
        return None
    if str(lead.get('Suppressed') or '').lower() in {'yes', 'ja', 'true'}:
        return None
    if str(lead.get('Opt-out-Status') or '').lower() in {'yes', 'ja', 'true'}:
        return None
    if lead.get('Bounce_Status') or lead.get('Suppression_Reason'):
        return None
    reply = str(lead.get('Reply_Status') or '').lower()
    if reply not in {'', 'no', 'none', 'not_received', 'auto_reply_ooo', 'abwesend'}:
        return None
    if lead.get('Follow-up-Datum'):
        try:
            if as_date(lead['Follow-up-Datum']) > today:
                return None
        except (TypeError, ValueError):
            return None
    if reply in {'auto_reply_ooo', 'abwesend'} and not lead.get('Follow-up-Datum'):
        return None
    rows = [r for r in journal_rows if str(r.get('lead_id')) == str(lead.get('Lead-ID') or lead.get('Lead_ID'))]
    if not rows or any(r.get('state', 'VERIFIED') != 'VERIFIED' for r in rows):
        return None
    bystep = {int(r['step']): r for r in rows}
    if len(bystep) != len(rows) or 1 not in bystep or 3 in bystep:
        return None
    try:
        start = as_date(bystep[1]['sent_at'])
        if 2 not in bystep:
            return 2 if today >= workday_after(start, 4) else None
        # Mindestens vier Werktage nach Schritt 2, auch wenn dieser verspätet war.
        due = max(workday_after(start, 10), workday_after(bystep[2]['sent_at'], 4))
        return 3 if today >= due else None
    except (TypeError, ValueError, KeyError):
        return None


def reply_actions(category, body='', today=None, return_date=None):
    today = as_date(today or date.today())
    if category in {'BOUNCE', 'OPTOUT'}:
        return {}
    if category == 'OOO_URLAUB':
        result = {'Reply_Status': 'abwesend', 'Pipeline': 'Abwesend – Wiedervorlage', 'Follow-up-Datum': ''}
        if return_date:
            try:
                result['Follow-up-Datum'] = workday_after(return_date).isoformat()
            except (TypeError, ValueError):
                pass
        return result
    if category == 'HOT_LEAD':
        status = 'positiv'
    elif re.search(r'kein(?:en)? (?:bedarf|interesse)|nicht interessant', body, re.I):
        status = 'negativ'
    elif re.search(r'zuständig|zustaendig|weitergeleitet|wenden sie sich', body, re.I):
        status = 'weiterleitung'
    else:
        status = 'replied'
    return {'Reply_Status': status, 'Pipeline': 'Antwort – Sichtung',
            'Nächste Aktion': 'Antwort bearbeiten',
            'Follow-up-Datum': workday_after(today).isoformat()}


SEQUENCE_SCHEMA = 'CREATE TABLE IF NOT EXISTS sequence(lead_id TEXT, step INTEGER, owner TEXT, message_id TEXT UNIQUE, sent_at TEXT, state TEXT, PRIMARY KEY(lead_id,step))'


class SequenceJournal:
    """Ein Schritt ist genau einmal reservierbar; unklare Versuche bleiben gesperrt."""
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(path, isolation_level=None)
        path.chmod(0o600)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute(SEQUENCE_SCHEMA)

    def reserve(self, lead_id, step, owner, message_id, day, used_today, budget):
        if step not in (1, 2, 3) or owner not in ('JOEL', 'JORDI'):
            raise ValueError('INVALID_SEQUENCE_STEP_OR_OWNER')
        if not 0 <= used_today < budget <= 35:
            raise RuntimeError('SHARED_DAILY_BUDGET_EXHAUSTED')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if self.db.execute("SELECT 1 FROM sequence WHERE state!='VERIFIED'").fetchone():
                raise RuntimeError('UNRESOLVED_SEQUENCE_ATTEMPT')
            n = self.db.execute('SELECT count(*) FROM sequence WHERE owner=? AND substr(sent_at,1,10)=?', (owner, as_date(day).isoformat())).fetchone()[0]
            if max(n, used_today) >= budget:
                raise RuntimeError('SHARED_DAILY_BUDGET_EXHAUSTED')
            self.db.execute('INSERT INTO sequence VALUES(?,?,?,?,?,?)', (lead_id, step, owner, message_id, as_date(day).isoformat(), 'RESERVED'))
            self.db.execute('COMMIT')
        except Exception:
            self.db.execute('ROLLBACK')
            raise

    def close(self):
        self.db.close()

    def record_verified(self, lead_id, step, owner, message_id, sent_at):
        """Nur nach SMTP-, Sent- und CRM-Readback aufrufen; vorhandene Belege nie ersetzen."""
        if step not in (1, 2, 3) or owner not in ('JOEL', 'JORDI'):
            raise ValueError('INVALID_SEQUENCE_STEP_OR_OWNER')
        as_date(sent_at)
        existing = self.db.execute('SELECT message_id,state FROM sequence WHERE lead_id=? AND step=?', (lead_id,step)).fetchone()
        if existing and existing[0] != message_id:
            raise RuntimeError('SEQUENCE_MESSAGE_ID_CONFLICT')
        if existing:
            self.db.execute("UPDATE sequence SET state='VERIFIED',sent_at=? WHERE lead_id=? AND step=?", (sent_at,lead_id,step))
        elif step == 1:
            self.db.execute('INSERT INTO sequence VALUES(?,?,?,?,?,?)', (lead_id,step,owner,message_id,sent_at,'VERIFIED'))
        else:
            raise RuntimeError('SEQUENCE_RESERVATION_REQUIRED')

    def rows(self):
        cursor=self.db.execute('SELECT lead_id,step,owner,message_id,sent_at,state FROM sequence ORDER BY sent_at')
        names=[c[0] for c in cursor.description]
        return [dict(zip(names,row)) for row in cursor]
