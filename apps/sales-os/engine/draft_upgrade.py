"""Wiederaufnehmbarer Entwurfsaustausch. Ohne --apply ausschließlich lesend.

Ein dauerhaftes Journal hält Message-ID und Ersatz-MIME vor APPEND fest.
Unklarer APPEND-Ausgang wird niemals automatisch wiederholt. Originale
werden lokal gesichert und per UID MOVE archiviert; es gibt keinen EXPUNGE.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import make_msgid, parseaddr
import base64
import hashlib
import imaplib
import json
import os
from pathlib import Path
import sqlite3
import time

from sales_reconciliation import OUTDATED_PLANNER_COPY, OUTDATED_REPAIR_COPY

IMAP_RETRIES = 3
ARCHIVE = 'Entwürfe-Archiv-v1'
DEEP_DEFECT_CAP = 50
REPAIRABLE = {'BODY_NOT_COMPANY_OR_CONTACT_SPECIFIC', 'SUBJECT_NOT_COMPANY_SPECIFIC',
              'UNRESOLVED_PLACEHOLDER', 'FLYER_LINK_MISSING', 'PERSONAL_OPTOUT_LINK_MISSING',
              'HISTORICAL_VARIANT_REQUIRES_REVIEW', 'PLAIN_TEXT_MISSING', 'LEAD_ID_INFERRED_ONLY',
              OUTDATED_PLANNER_COPY, OUTDATED_REPAIR_COPY}


def modified_utf7(value):
    result = []; pending = []
    def flush():
        if pending:
            raw = ''.join(pending).encode('utf-16-be')
            result.append('&' + base64.b64encode(raw).decode().rstrip('=').replace('/', ',') + '-')
            pending.clear()
    for char in value:
        if ' ' <= char <= '~':
            flush(); result.append('&-' if char == '&' else char)
        else:
            pending.append(char)
    flush()
    return ''.join(result)


def mailbox_arg(value):
    return '"' + modified_utf7(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def _select(imap, folder, validity=None, readonly=True):
    typ, _ = imap.select(folder, readonly=readonly)
    got = imap.response('UIDVALIDITY')[1]
    if typ != 'OK' or not got or not got[0]:
        raise RuntimeError('MAILBOX_UIDVALIDITY_MISSING')
    current = got[0].decode() if isinstance(got[0], bytes) else str(got[0])
    if validity is not None and str(validity) != current:
        raise RuntimeError('DRAFT_UIDVALIDITY_CHANGED')
    return current


def _raw(imap, uid):
    typ, data = imap.uid('fetch', str(uid), '(BODY.PEEK[])')
    parts = [x[1] for x in data or [] if isinstance(x, tuple)] if typ == 'OK' else []
    if len(parts) != 1:
        raise RuntimeError('DRAFT_READBACK_FAILED')
    return parts[0]


def _find(imap, mid):
    typ, data = imap.uid('search', None, 'HEADER', 'Message-ID', '"' + mid + '"')
    if typ != 'OK':
        raise RuntimeError('MESSAGE_SEARCH_FAILED')
    return data[0].split() if data and data[0] else []


def _existing_replacement(imap, rec, lead, owner, template, assess_message):
    """(Message-ID, Rohdaten) eines gültigen Ersatzentwurfs dieses Leads im Entwurfsordner, sonst None.

    Nur der exakte Erstkontakt (template) an genau diesen Empfänger zählt; Folgekontakte nie, mehrdeutige Treffer halten an.
    """
    typ, data = imap.uid('search', None, 'HEADER', 'X-HSB-Lead-ID', '"' + str(lead['Lead-ID']) + '"')
    if typ != 'OK':
        raise RuntimeError('MESSAGE_SEARCH_FAILED')
    found = []
    for uid in (data[0].split() if data and data[0] else []):
        uid = uid.decode()
        if uid == str(rec['uid']):
            continue
        raw = _raw(imap, uid)
        msg = BytesParser(policy=policy.default).parsebytes(raw)
        current = (str(msg.get('X-HSB-Template-ID') or '').strip() == template
                   and parseaddr(str(msg.get('To') or ''))[1].strip().lower() == str(lead.get('E-Mail') or '').strip().lower()
                   and str(msg.get('X-HSB-Lead-ID') or '').strip() == str(lead['Lead-ID'])
                   and not assess_message(raw, owner, [lead])['issues'])
        if current:
            found.append((str(msg['Message-ID']), raw))
    if len(found) > 1:
        raise RuntimeError('REPLACEMENT_NOT_UNIQUE')
    return found[0] if found else None


def upgrade_drafts(owner, limit=5, cohort='pilot', apply=False, journal_path=None, variant='standard', *,
                   records=None, leads=None, client=None, svc=None, mx_check=None, signals=None, lock_client=None,
                   deep_defects=frozenset(), allow_mass_refresh=False):
    """Nur erste v2-Nachricht; Folgekontakte brauchen später das verifizierte Sequenzjournal."""
    from canonical_template_factory import render_email_v2
    from click_sync import click_url
    from hsb_core import check_eligibility, normalize_owner
    from lead_quality import deliverability_flags, fit_score, planner_outreach_allowed, segment_for
    from outbound_safety import crm_write_lead_readback, require_stable_crm_binding
    from sales_reconciliation import assess_message
    from hsb_config import CANONICAL_SPREADSHEET_ID

    owner = normalize_owner(owner)
    if owner not in ('JOEL', 'JORDI') or type(limit) is not int or not 1 <= limit <= 100 or cohort not in ('pilot', 'all') or variant not in ('standard', 'reparatur'):
        raise ValueError('INVALID_UPGRADE_SELECTION')
    if records is None or leads is None:
        raise ValueError('FRESH_AUDIT_AND_CRM_REQUIRED')
    deep_defects = frozenset(deep_defects or ())
    owner_deep = {k for k in deep_defects if k.startswith(f'{owner}|')}
    if len(owner_deep) > DEEP_DEFECT_CAP and not allow_mass_refresh:
        raise RuntimeError('DEEP_DEFECT_CAP_EXCEEDED')
    result = {'selected': 0, 'appended': 0, 'archived': 0, 'crm_updated': 0,
              'skipped_reasons': Counter(), 'customer_emails_sent': 0, 'dry_run': not apply}
    byid = {}
    for lead in leads:
        byid.setdefault(str(lead.get('Lead-ID') or ''), []).append(lead)
    counts = Counter((r.get('owner'), r.get('lead_id')) for r in records)
    done=set()
    if journal_path and Path(journal_path).is_file():
        prior=sqlite3.connect(Path(journal_path).resolve().as_uri()+'?mode=ro',uri=True)
        try:
            done={r[0] for r in prior.execute("SELECT key FROM upgrades WHERE state='DONE'")}
        finally:
            prior.close()
    cache = {}; selected = []
    outdated = {OUTDATED_PLANNER_COPY, OUTDATED_REPAIR_COPY}

    def target_template(segment):
        return f'v2-{segment}-reparatur-s1' if variant == 'reparatur' else f'v2-{segment}-s1'
    # Erst Fit, dann Netzwerkprüfungen: knappe Pilotplätze nicht nach IMAP-Reihenfolge vergeben.
    def rank(record):
        matches = byid.get(str(record.get('lead_id')), [])
        if len(matches) != 1:
            return -1
        return fit_score(matches[0], (signals or {}).get(record.get('lead_id')))[0]
    quotas = {'produktion': limit - round(limit * .2), 'architekten': round(limit * .2)}
    chosen = Counter()
    for record in sorted(records, key=rank, reverse=True):
        if record.get('owner') != owner or record.get('internal_test'):
            continue
        record_key='|'.join(str(record.get(k,'')) for k in ('owner','uidvalidity','uid','sha256'))
        if record_key in done:
            result['skipped_reasons']['ALREADY_DONE']+=1
            continue
        matches = byid.get(str(record.get('lead_id')), [])
        reason = None
        if len(matches) != 1 or counts[(owner, record.get('lead_id'))] != 1:
            reason = 'AMBIGUOUS_LEAD_OR_DRAFT'
        elif set(record.get('issues', [])) - REPAIRABLE:
            reason = 'IDENTITY_OR_HISTORY_ISSUE'
        else:
            lead = dict(matches[0])
            tmpl = str(lead.get('Email_Template_ID') or '')
            segment = segment_for(lead)
            if segment == 'architekten' and not planner_outreach_allowed(lead):
                result['skipped_reasons']['PLANNING_PROJECT_UNVERIFIED'] += 1
                continue
            # Veraltete Fassung, Tiefenmangel oder unverändert neu gespeicherter Entwurf (1:1 Lead/Entwurf ist oben geprüft).
            is_resaved = 'LEAD_ID_INFERRED_ONLY' in record.get('issues', [])
            if is_resaved and record.get('path') and Path(record['path']).is_file():
                from draft_verify import _text_unchanged
                if not _text_unchanged(Path(record['path']).read_bytes(), lead, owner):
                    result['skipped_reasons']['HUMAN_EDITED'] += 1
                    continue
            needs_repair = (bool(outdated & set(record.get('issues', [])))
                            or record_key in deep_defects
                            or is_resaved)
            already_v2 = '-reparatur-' in tmpl if variant == 'reparatur' else tmpl.startswith('v2-')
            if already_v2 and not needs_repair:
                result['skipped_reasons']['ALREADY_V2'] += 1
                continue
            if str(lead.get('Tier') or '').strip().upper()=='Z':
                result['skipped_reasons']['TIER_Z']+=1
                continue
            if cohort == 'pilot' and chosen[segment] >= quotas[segment]:
                result['skipped_reasons']['PILOT_SEGMENT_QUOTA'] += 1
                continue
            lead['Deliverability_Flags'] = deliverability_flags(lead, cache, set(), mx_check=mx_check)
            _, tier, _ = fit_score(lead, (signals or {}).get(lead.get('Lead-ID')))
            if (cohort == 'pilot' and tier == 'Z') or not check_eligibility(lead).eligible:
                reason = 'INELIGIBLE_OR_TIER_Z'
        if reason:
            result['skipped_reasons'][reason] += 1
            continue
        selected.append((record, lead))
        chosen[segment_for(lead)] += 1
        if len(selected) >= limit:
            break
    result['selected'] = len(selected)
    result['selected_lead_ids'] = [str(lead.get('Lead-ID') or '') for _, lead in selected]
    if not apply or not selected:
        return result
    if client is None or svc is None or journal_path is None:
        raise ValueError('APPLY_REQUIRES_CLIENT_CRM_AND_JOURNAL')
    if os.environ.get('HSB_CRM_BINDINGS_VERIFIED') != 'yes':
        raise RuntimeError('CRM_STABLE_BINDING_CANARY_REQUIRED')
    # Prüfung vor dem ersten externen Schreibzugriff.
    if any(not l.get('_row') for _, l in selected):
        raise ValueError('CRM_ROW_MISSING')
    from outbound_safety import mailbox_dispatch_lock
    if lock_client is None:
        from com_mailbox_manager import ComMailboxClient
        lock_client = ComMailboxClient('JOEL')
    # Derselbe JOEL-Lock wie im Versand; schützt beide Postfächer und alle Geräte.
    with mailbox_dispatch_lock(lock_client, release_on_error=True):
        journal_path = Path(journal_path)
        journal_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(journal_path, isolation_level=None)
        journal_path.chmod(0o600)
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS upgrades(key TEXT PRIMARY KEY, mid TEXT, raw BLOB, state TEXT, old_raw BLOB)')
        try:
            # Stabile Zeilenbindungen für genau diese Tranche anlegen und danach wieder entfernen
            # (Google begrenzt Developer-Metadaten auf ~30.000 Zeichen je Tabelle).
            import crm_bindings
            tranche_ids = {str(l.get('Lead-ID') or '') for _, l in selected}
            prebound = set(crm_bindings.existing_bindings(svc, CANONICAL_SPREADSHEET_ID)) & tranche_ids
            created_bindings = tranche_ids - prebound
            try:
                # Auch ein Fehler mitten im Anlegen/Verifizieren räumt die angeforderten Bindungen wieder ab.
                crm_bindings.ensure_bindings(svc, CANONICAL_SPREADSHEET_ID, apply=True, only=created_bindings)
                imap = client._get_imap()
                try:
                    # Ein frischer CRM-Stand je Tranche (höchstens 100 Entwürfe) statt je Entwurf: Google erlaubt nur
                    # 60 Lesezugriffe pro Minute. Die Umstellung sendet nichts; der Versand prüft jede Sperre erneut live.
                    current_rows = svc.spreadsheets().values().get(spreadsheetId=CANONICAL_SPREADSHEET_ID,
                        range='ALL_LEADS!A1:BU6425').execute().get('values', [])
                    def handle(rec, lead, imap):
                        current_matches = [(idx, dict(zip(current_rows[0], r))) for idx, r in enumerate(current_rows[1:], 2)
                            if r and r[0] == lead['Lead-ID']]
                        if len(current_matches) != 1:
                            raise RuntimeError('LIVE_LEAD_NOT_UNIQUE')
                        current_row, current = current_matches[0]
                        current['Deliverability_Flags'] = deliverability_flags(current, {}, set(), mx_check=mx_check)
                        if str(current.get('Tier') or '').strip().upper() == 'Z' or not check_eligibility(current).eligible or normalize_owner(current.get('Verantwortlicher')) != owner:
                            raise RuntimeError('LIVE_LEAD_GATE_BLOCKED')
                        if current.get('E-Mail') != lead.get('E-Mail'):
                            raise RuntimeError('LIVE_RECIPIENT_CHANGED')
                        segment = segment_for(current)
                        if (segment != segment_for(lead)
                                or (segment == 'architekten' and not planner_outreach_allowed(current))):
                            raise RuntimeError('LIVE_PROJECT_FIT_CHANGED')
                        # Vor APPEND/MOVE die stabile CRM-Bindung prüfen, nicht erst nach dem Archivieren.
                        try:
                            binding = require_stable_crm_binding(svc,CANONICAL_SPREADSHEET_ID,lead['Lead-ID'])
                        except RuntimeError as exc:
                            # Ohne eindeutige Bindung nichts anfassen; dieser eine Entwurf bleibt wie er ist.
                            if 'CRM_STABLE_LEAD_BINDING_REQUIRED' not in str(exc) and 'CRM_BINDING_WRONG_SHEET' not in str(exc):
                                raise
                            result['skipped_reasons']['CRM_BINDING_UNAVAILABLE'] += 1
                            return
                        key = '|'.join(str(rec[k]) for k in ('owner', 'uidvalidity', 'uid', 'sha256'))
                        row = db.execute('SELECT mid,raw,state,old_raw FROM upgrades WHERE key=?', (key,)).fetchone()
                        if row and row[2] == 'DONE':
                            return
                        if (outdated & set(rec.get('issues', []))) or key in deep_defects or 'LEAD_ID_INFERRED_ONLY' in rec.get('issues', []):
                            live_binding = (current.get('Draft_ID'), current.get('Email_Template_ID'))
                            original_binding = (lead.get('Draft_ID'), lead.get('Email_Template_ID'))
                            resumed = (row and row[2] == 'ARCHIVED'
                                       and live_binding == (row[0], rendered_id(row[1])))
                            if live_binding != original_binding and not resumed:
                                raise RuntimeError('LIVE_DRAFT_BINDING_CHANGED')
                        lead = dict(current, _row=current_row)
                        _select(imap, rec['folder'], rec['uidvalidity'])
                        old = row[3] if row and row[2] in ('MOVE_UNKNOWN', 'ARCHIVED') else _raw(imap, rec['uid'])
                        if hashlib.sha256(old).hexdigest() != rec['sha256']:
                            result['skipped_reasons']['CHANGED_V1_HASH'] += 1
                            return
                        if 'LEAD_ID_INFERRED_ONLY' in rec.get('issues', []) and row is None:
                            from draft_verify import _text_unchanged
                            if not _text_unchanged(old, lead, owner):
                                result['skipped_reasons']['HUMAN_EDITED'] += 1
                                return
                        adopted = None
                        if row is None:
                            # Das Journal liegt je Lauf auf dem Runner und ist beim Neustart leer: Ein schon angenommener
                            # Ersatzentwurf wird live erkannt und übernommen, statt einen zweiten anzulegen.
                            adopted = _existing_replacement(imap, rec, lead, owner, target_template(segment_for(lead)), assess_message)
                        if adopted:
                            mid, raw = adopted
                            result['replacements_adopted'] = result.get('replacements_adopted', 0) + 1
                            db.execute('INSERT INTO upgrades VALUES(?,?,?,?,?)', (key, mid, raw, 'PREPARED', old))
                            row = (mid, raw, 'PREPARED', old)
                        if row is None:
                            rendered = render_email_v2(lead, owner, click_url=click_url(lead['Lead-ID'], segment_for(lead), os.environ.get('HSB_CLICK_SECRET')), variant=variant)
                            mid = make_msgid(domain='hsb-boden.com')
                            raw, _ = client.build_draft_message(rendered['to_email'], rendered['subject'], body_text=rendered['body_text'],
                                    body_html=rendered.get('body_html', ''),
                                    template_id=rendered['template_id'], lead_id=lead['Lead-ID'], custom_message_id=mid,
                                    copy_rev=rendered.get('copy_rev'))
                            # imaplib.append normalisiert CRLF; Readback und Journal speichern dieselben Bytes.
                            raw = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n').replace(b'\n', b'\r\n')
                            if assess_message(raw, owner, [lead])['issues']:
                                raise RuntimeError('V2_REVALIDATION_FAILED')
                            db.execute('INSERT INTO upgrades VALUES(?,?,?,?,?)', (key, mid, raw, 'PREPARED', old))
                            row = (mid, raw, 'PREPARED', old)
                        mid, raw, state, saved_old = row
                        if saved_old != old:
                            raise RuntimeError('ORIGINAL_BACKUP_MISMATCH')
                        if state == 'DONE':
                            return
                        matches = _find(imap, mid)
                        if len(matches) > 1:
                            raise RuntimeError('REPLACEMENT_NOT_UNIQUE')
                        if not matches:
                            if state != 'PREPARED':
                                raise RuntimeError('UNCERTAIN_APPEND_REQUIRES_RECONCILIATION')
                            db.execute("UPDATE upgrades SET state='APPEND_UNKNOWN' WHERE key=?", (key,))
                            typ, _ = imap.append(rec['folder'], r'(\Draft)', imaplib.Time2Internaldate(time.time()), raw)
                            if typ != 'OK':
                                raise RuntimeError('REPLACEMENT_APPEND_FAILED')
                            result['appended'] += 1
                            matches = _find(imap, mid)
                        if len(matches) != 1 or _raw(imap, matches[0].decode()) != raw:
                            raise RuntimeError('REPLACEMENT_READBACK_MISMATCH')
                        archive = mailbox_arg(ARCHIVE)
                        typ, _ = imap.select(archive, readonly=True)
                        if typ != 'OK':
                            typ, _ = imap.create(archive)
                            if typ != 'OK':
                                raise RuntimeError('ARCHIVE_CREATE_FAILED')
                            _select(imap, archive)
                        original_mid = str(BytesParser(policy=policy.default).parsebytes(old).get('Message-ID') or '')
                        if not original_mid:
                            raise RuntimeError('ORIGINAL_MESSAGE_ID_MISSING')
                        archived = _find(imap, original_mid)
                        if not archived:
                            capabilities = {x.decode().upper() if isinstance(x, bytes) else str(x).upper() for x in imap.capabilities}
                            if 'MOVE' not in capabilities:
                                raise RuntimeError('UID_MOVE_REQUIRED_ORIGINAL_RETAINED')
                            if state in ('MOVE_UNKNOWN', 'ARCHIVED'):
                                raise RuntimeError('UNCERTAIN_MOVE_REQUIRES_RECONCILIATION')
                            _select(imap, rec['folder'], rec['uidvalidity'], readonly=False)
                            # Vor MOVE noch einmal gegen das gesicherte Original vergleichen.
                            if _raw(imap, rec['uid']) != old:
                                raise RuntimeError('ORIGINAL_CHANGED_BEFORE_MOVE')
                            db.execute("UPDATE upgrades SET state='MOVE_UNKNOWN' WHERE key=?", (key,))
                            typ, _ = imap.uid('MOVE', rec['uid'], archive)
                            if typ != 'OK':
                                raise RuntimeError('ARCHIVE_MOVE_FAILED')
                            _select(imap, archive)
                            archived = _find(imap, original_mid)
                        if len(archived) != 1 or _raw(imap, archived[0].decode()) != old:
                            raise RuntimeError('ARCHIVE_READBACK_MISMATCH')
                        result['archived'] += 1
                        db.execute("UPDATE upgrades SET state='ARCHIVED' WHERE key=?", (key,))
                        _select(imap, rec['folder'], rec['uidvalidity'])
                        if _find(imap, original_mid):
                            raise RuntimeError('ORIGINAL_STILL_IN_DRAFTS')
                        # Spaltenreihenfolge vom CRM-Header dieser Tranche; Bindung aus der Prüfung vor APPEND.
                        crm_write_lead_readback(svc, CANONICAL_SPREADSHEET_ID, lead['Lead-ID'],
                            {'Draft_ID': mid, 'Email_Template_ID': rendered_id(raw), 'Drafted_At': datetime.now(timezone.utc).isoformat()},
                            binding=binding, headers=current_rows[0])
                        result['crm_updated'] += 1
                        db.execute("UPDATE upgrades SET state='DONE' WHERE key=?", (key,))
                    # Reißt die IMAP-Verbindung ab, neu anmelden und denselben Entwurf ab dem letzten Journal-Zustand
                    # fortsetzen: PREPARED/APPEND/MOVE werden über Message-ID live nachgeprüft, nie doppelt ausgeführt.
                    for rec, lead in selected:
                        for attempt in range(1, IMAP_RETRIES + 1):
                            try:
                                handle(rec, lead, imap)
                                break
                            except (imaplib.IMAP4.abort, OSError):
                                if attempt == IMAP_RETRIES:
                                    raise
                                result['imap_reconnects'] = result.get('imap_reconnects', 0) + 1
                                try:
                                    imap.logout()
                                except Exception:  # noqa: BLE001
                                    pass
                                time.sleep(5 * attempt)
                                imap = client._get_imap()
                finally:
                    try:
                        imap.logout()
                    except Exception:  # noqa: BLE001 - Server trennt nach langer Tranche; Daten sind geschrieben
                        pass
            finally:
                # Nur selbst angelegte Bindungen entfernen; vorher vorhandene bleiben.
                crm_bindings.remove_bindings(svc, CANONICAL_SPREADSHEET_ID, created_bindings)
        finally:
            db.close()
        result['originals_retained'] = True
        return result


def rendered_id(raw):
    return str(BytesParser(policy=policy.default).parsebytes(raw)['X-HSB-Template-ID'])
