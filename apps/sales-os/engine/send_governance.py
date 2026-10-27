"""
HSB Sales OS - Send Governance & EOP Anti-Spam Queue Guardrails (G11).

Erzwingt:
1. Natuerlichen stochastischen Jitter: 45 bis 180 Sekunden zwischen E-Mails.
2. Physikalisches Tageslimit: Maximal 35 Mails/Tag pro Postfach.
3. Fail-closed Schutz: Blockiert strikt bei Cap-Erreichung.
"""
from __future__ import annotations

import datetime
import random
from typing import Dict, Optional, Tuple

MIN_JITTER_SECONDS: int = 45
MAX_JITTER_SECONDS: int = 180
DAILY_CAP_PER_MAILBOX: int = 35

REAL_EXTERNAL_PROSPECT_SEND_COUNT: int = 0


class DailyCapReachedError(RuntimeError):
    """Physikalisches Tageslimit pro Postfach erreicht (max. 35 Mails/Tag)."""


class SendGovernanceQueue:
    def __init__(
        self,
        min_jitter: int = MIN_JITTER_SECONDS,
        max_jitter: int = MAX_JITTER_SECONDS,
        daily_cap: int = DAILY_CAP_PER_MAILBOX
    ):
        self.min_jitter = min_jitter
        self.max_jitter = max_jitter
        self.daily_cap = daily_cap
        # mailbox -> { "YYYY-MM-DD": sent_count }
        self._sent_ledger: Dict[str, Dict[str, int]] = {}

    def get_jitter_delay(self) -> float:
        """Erzeugt eine gleichverteilte Pseudozufalls-Verzoegerung im Korridor [45s, 180s]."""
        return random.uniform(self.min_jitter, self.max_jitter)

    def can_send(self, mailbox: str, target_date: Optional[datetime.date] = None) -> Tuple[bool, int, int]:
        """Prueft, ob das Postfach am gegebenen Tag noch Sende-Quota besitzt."""
        if target_date is None:
            target_date = datetime.date.today()
        date_str = target_date.isoformat()
        current_count = self._sent_ledger.get(mailbox, {}).get(date_str, 0)
        remaining = max(0, self.daily_cap - current_count)
        return (current_count < self.daily_cap), current_count, remaining

    def queue_send(
        self,
        mailbox: str,
        prospect_email: str,
        target_date: Optional[datetime.date] = None
    ) -> dict:
        """
        Enqueuet eine E-Mail mit berechneter Jitter-Verzoegerung und aktualisiert den Tageszaehler.
        Wirft DailyCapReachedError, wenn das Tageslimit erreicht ist.
        """
        if target_date is None:
            target_date = datetime.date.today()
        date_str = target_date.isoformat()

        allowed, current_count, remaining = self.can_send(mailbox, target_date)
        if not allowed:
            raise DailyCapReachedError(
                f"Tageslimit fuer {mailbox} am {date_str} erschoepft: "
                f"{current_count}/{self.daily_cap} versendet. Abbruch."
            )

        jitter = self.get_jitter_delay()

        # Buchung im Tages-Ledger
        if mailbox not in self._sent_ledger:
            self._sent_ledger[mailbox] = {}
        self._sent_ledger[mailbox][date_str] = current_count + 1

        return {
            "status": "QUEUED",
            "mailbox": mailbox,
            "prospect_email": prospect_email,
            "date": date_str,
            "jitter_delay_seconds": jitter,
            "day_sequence_number": current_count + 1,
            "remaining_today": remaining - 1,
        }


def daily_budget(first_send_date, today):
    """Kalenderwochen seit dem belegten Pilotstart, je Postfach; Alter der Domain zählt nicht."""
    from sequence import as_date
    age = (as_date(today) - as_date(first_send_date)).days
    if age < 0:
        raise ValueError('RAMP_START_IN_FUTURE')
    return min(DAILY_CAP_PER_MAILBOX, 10 if age < 7 else 20 if age < 14 else 30)


def pause_reason(stats):
    """Statistiken müssen verifiziert sein. Fehlende Beobachtungen bedeuten keine Gesundheit."""
    required = ('sample_sent', 'hard_bounces', 'policy_bounces', 'deferrals_today', 'spam_reports', 'seed_dkim_pass')
    if not isinstance(stats, dict) or any(k not in stats for k in required):
        return 'HEALTH_EVIDENCE_MISSING'
    counts = [stats[k] for k in required[:-1]]
    if any(type(x) is not int or x < 0 for x in counts):
        return 'HEALTH_EVIDENCE_INVALID'
    sent, hard, policy, deferrals, spam = counts
    if sent > 100 or hard > sent:
        return 'HEALTH_EVIDENCE_INVALID'
    if stats['seed_dkim_pass'] is not True:
        return 'SEED_DKIM_NOT_PASS'
    if spam:
        return 'SPAM_REPORT'
    if policy:
        return 'POLICY_BOUNCE'
    if deferrals >= 3:
        return 'DEFERRALS'
    if (sent >= 100 and hard / sent > .02) or (sent < 100 and hard >= 3):
        return 'HARD_BOUNCES'
    return None


def enforce_send_health(state_dir, today=None, observed=None):
    """Frischer, atomarer Read je Mail; Pause bleibt bis zum problemspezifischen ACK bestehen."""
    import hashlib
    import json
    import os
    from pathlib import Path
    from datetime import timezone
    now = datetime.datetime.now(timezone.utc)
    path = Path(state_dir) / 'send-health.json'
    try:
        raw = path.read_bytes()
        health = json.loads(raw)
        stamp = datetime.datetime.fromisoformat(health['checked_at'].replace('Z', '+00:00'))
        age = (now - stamp).total_seconds()
        if age < 0 or age > 86400:
            raise ValueError('stale')
        budget = daily_budget(health['first_send_date'], today or now.date())
    except (OSError, KeyError, TypeError, ValueError):
        raise RuntimeError('SEND_HEALTH_MISSING_OR_STALE') from None
    reason = pause_reason(observed if observed is not None else health)
    pause_path = Path(state_dir) / 'send-pause.json'
    if reason:
        key = hashlib.sha256(raw).hexdigest()[:20]
        pause_path.write_text(json.dumps({'reason': reason, 'ack_id': key}))
        pause_path.chmod(0o600)
        raise RuntimeError('DOMAIN_PAUSED:' + reason)
    if pause_path.exists():
        pause = json.loads(pause_path.read_text())
        if os.environ.get('HSB_SEND_PAUSE_ACK') != pause.get('ack_id'):
            raise RuntimeError('DOMAIN_PAUSED_ACK_REQUIRED')
    return budget


class MailboxHealthStore:
    """Append-only Pausenverlauf im gemeinsamen JOEL-Postfach. Keine Kundenmails."""
    folder = 'HSB-SALES-OS-HEALTH'

    def __init__(self, client):
        self.client = client

    def read(self):
        import json
        from email import policy
        from email.parser import BytesParser
        with self.client._get_imap() as imap:
            typ, _ = imap.select(self.folder, readonly=True)
            if typ != 'OK':
                # NO kann auch einen Netzwerk-/Rechtefehler bedeuten: Existenz gesondert prüfen.
                typ, boxes = imap.list('', self.folder)
                if typ != 'OK': raise RuntimeError('DOMAIN_HEALTH_UNAVAILABLE')
                if boxes and any(b for b in boxes): raise RuntimeError('DOMAIN_HEALTH_UNREADABLE')
                return None
            typ, data = imap.uid('search',None,'ALL')
            if typ != 'OK': raise RuntimeError('DOMAIN_HEALTH_UNAVAILABLE')
            uids=data[0].split() if data and data[0] else []
            if not uids: raise RuntimeError('DOMAIN_HEALTH_EMPTY_UNVERIFIED')
            typ, data = imap.uid('fetch',uids[-1],'(BODY.PEEK[])')
            parts=[x[1] for x in data or [] if isinstance(x,tuple)] if typ=='OK' else []
            if len(parts)!=1: raise RuntimeError('DOMAIN_HEALTH_READBACK_FAILED')
            msg=BytesParser(policy=policy.default).parsebytes(parts[0])
            event=json.loads(msg.get_content())
            if event.get('state') not in ('paused','ack') or not event.get('ack_id'):
                raise RuntimeError('DOMAIN_HEALTH_INVALID')
            return event

    def append(self, event):
        import imaplib
        import json
        import time
        from email import policy
        from email.message import EmailMessage
        msg=EmailMessage()
        msg['Subject']='HSB technische Versandpause'
        msg['Message-ID']=__import__('email.utils',fromlist=['make_msgid']).make_msgid(domain='hsb-boden.com')
        msg.set_content(json.dumps(event))
        raw=msg.as_bytes(policy=policy.SMTP)
        with self.client._get_imap() as imap:
            typ, _ = imap.select(self.folder,readonly=True)
            if typ!='OK':
                typ,_=imap.create(self.folder)
                if typ!='OK':raise RuntimeError('DOMAIN_HEALTH_CREATE_FAILED')
            typ,_=imap.append(self.folder,r'(\Seen)',imaplib.Time2Internaldate(time.time()),raw)
            if typ!='OK':raise RuntimeError('DOMAIN_HEALTH_APPEND_FAILED')
        if self.read()!=event:raise RuntimeError('DOMAIN_HEALTH_READBACK_MISMATCH')


def enforce_domain_health(state_dir, today, shared, collector=None):
    """Vom globalen IMAP-Lock umschlossen; jede Maschine sieht dieselbe Pause."""
    import json
    import os
    from pathlib import Path
    remote=shared.read()
    if remote and remote['state']=='paused' and os.environ.get('HSB_SEND_PAUSE_ACK')!=remote['ack_id']:
        raise RuntimeError('DOMAIN_PAUSED_SERVER_ACK_REQUIRED')
    try:
        observed=observed_health(state_dir,collector)
        budget=enforce_send_health(state_dir,today,observed)
    except RuntimeError:
        path=Path(state_dir)/'send-pause.json'
        if path.exists():
            pause=json.loads(path.read_text())
        else:
            # Auch fehlende Messungen dürfen nicht auf einem anderen Gerät zum PASS werden.
            import uuid
            pause={'reason':'SEND_HEALTH_UNVERIFIED','ack_id':uuid.uuid4().hex}
        shared.append(dict(pause,state='paused'))
        raise
    if remote and remote['state']=='paused':
        shared.append(dict(remote,state='ack'))
    return budget


def observed_health(state_dir, collector=None):
    """Vor jeder Mail neue Rückläufer seit dem zuletzt bestätigten Messstand einbeziehen."""
    import json
    import re
    from pathlib import Path
    from email.utils import parsedate_to_datetime
    from datetime import timezone
    from inbound_classifier import classify_inbound_message
    from lead_quality import classify_dsn
    try:
        stats=json.loads((Path(state_dir)/'send-health.json').read_text())
        since=datetime.datetime.fromisoformat(stats['checked_at'].replace('Z','+00:00'))
        if since.tzinfo is None:raise ValueError('missing timezone')
    except (OSError,ValueError,KeyError,TypeError):
        raise RuntimeError('SEND_HEALTH_MISSING_OR_STALE') from None
    if collector is None:
        from dual_domain_collector import collect_all_inbounds
        collector=collect_all_inbounds
    seen=set()
    for msg in collector(limit_per_mailbox=0,include_de=False):
        if msg.message_id in seen:continue
        seen.add(msg.message_id)
        try:
            stamp=parsedate_to_datetime(msg.date)
        except (ValueError,TypeError):
            try:stamp=datetime.datetime.fromisoformat(str(msg.date).replace('Z','+00:00'))
            except (ValueError,TypeError):stamp=None
        if stamp and stamp.tzinfo is not None and stamp.astimezone(timezone.utc)<=since:
            continue
        cls=classify_inbound_message(msg.sender,msg.subject,msg.body)
        if cls.category=='BOUNCE':
            kind=classify_dsn(msg.body)
            key={'hard':'hard_bounces','soft':'deferrals_today','policy':'policy_bounces'}.get(kind)
            if key:stats[key]=stats.get(key,0)+1
            else:stats['policy_bounces']=stats.get('policy_bounces',0)+1  # unklare Ablehnung: halten
        if re.search(r'feedback[- ]type:\s*abuse|feedback report|spam complaint',msg.subject+'\n'+msg.body,re.I):
            stats['spam_reports']=stats.get('spam_reports',0)+1
    return stats
