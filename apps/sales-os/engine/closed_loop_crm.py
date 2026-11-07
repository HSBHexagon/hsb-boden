# apps/sales-os/engine/closed_loop_crm.py
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from inbound_classifier import InboundClassificationResult

logger = logging.getLogger("closed_loop_crm")

def compute_lead_update(row_idx: int, lead_id: str, cls_res: InboundClassificationResult) -> Dict[str, Any]:
    cat = cls_res.category
    optout_val = None
    reply_status = "received"
    pipeline_val = "In Bearbeitung"

    if cat == "BOUNCE":
        reply_status = "bounced"
        pipeline_val = "Zustellmeldung / Prüfung"
    elif cat == "OPTOUT":
        optout_val = "YES"
        reply_status = "opt_out"
        pipeline_val = "Abgemeldet / Widerspruch"
    elif cat == "OOO_URLAUB":
        reply_status = "auto_reply_ooo"
        if cls_res.recontact_date:
            pipeline_val = f"Wiedervorlage {cls_res.recontact_date} (Urlaub)"
        else:
            pipeline_val = "Wiedervorlage (Urlaub/Abwesend)"
    elif cat == "HOT_LEAD":
        reply_status = "replied_interested"
        pipeline_val = "HOT LEAD / Terminprüfung"
    else:
        reply_status = "replied"
        pipeline_val = "Antwort erhalten (Manuelle Sichtung)"

    return {
        "row": row_idx,
        "lead_id": lead_id,
        "optout_val": optout_val,
        "reply_status": reply_status,
        "pipeline_val": pipeline_val,
        "notes": cls_res.reason
    }


def company_domain(lead):
    """Domain der Firmen-Website laut CRM (ohne Schema, www und Pfad); leer, wenn unbekannt."""
    import re
    site=str(lead.get('Website') or lead.get('Web') or '').strip().lower()
    site=re.sub(r'^[a-z]+://','',site).split('/')[0].split('?')[0].split(':')[0]
    return site[4:] if site.startswith('www.') else site


def sync_inbounds(apply=False, include_de=True):
    """Replay-safe event ingestion; negative evidence never clears a suppression."""
    from collections import defaultdict
    from datetime import datetime, timezone
    import hashlib
    import re
    from dual_domain_collector import collect_all_inbounds
    from inbound_classifier import classify_inbound_message
    from sequence import reply_actions
    from hsb_core import FREEMAIL_DOMAINS
    from lead_quality import delivery_bounce_status
    from outbound_safety import crm_write_readback, UNSUBSCRIBE_TOKEN_RE
    from sales_reconciliation import addresses
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    svc = get_sheets_service()
    rows = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!A1:BU6425').execute()['values']
    headers=rows[0]; byemail=defaultdict(list); bylead=defaultdict(list)
    for row,r in enumerate(rows[1:],2):
        d=dict(zip(headers,r));byemail[str(d.get('E-Mail') or '').strip().lower()].append((row,d))
        if d.get('Lead-ID'):bylead[str(d['Lead-ID']).strip()].append((row,d))
    events=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='INBOUND_EVENTS!A1:M10000').execute().get('values',[])
    seen_ids={str(r[0]) for r in events[1:] if r}
    seen_mids={str(r[5]) for r in events[1:] if len(r)>5 and r[5]}
    seen_classifications={(str(r[5]), str(r[7]), str(r[6])) for r in events[1:] if len(r)>7}
    messages=collect_all_inbounds(limit_per_mailbox=0,include_de=include_de)
    pending=[]; categories={}; matched=0
    # Process the whole observed set in one call; no newest-N starvation.
    for msg in messages:
        if not msg.message_id: raise RuntimeError('INBOUND_MESSAGE_ID_MISSING')
        cls=classify_inbound_message(msg.sender,msg.subject,msg.body)
        targets=[cls.extracted_email.lower()] if cls.category=='BOUNCE' and cls.extracted_email else addresses(msg.sender)
        eid='INBOUND-'+hashlib.sha256((msg.source+'|'+msg.owner+'|'+msg.message_id).encode()).hexdigest()
        already_seen = eid in seen_ids or msg.message_id in seen_mids
        matched_rows=[m for target in targets for m in byemail.get(target,[])]
        tokens=set(UNSUBSCRIBE_TOKEN_RE.findall(msg.body or '')) if cls.category=='OPTOUT' else set()
        if len(tokens)==1:
            # Abmelde-Token aus dem List-Unsubscribe-Link: gilt auch, wenn ein Kollege antwortet –
            # aber nur aus derselben Firmendomain und nur ein Token je Mail (keine Fremd-Massensperre).
            sender_domains={a.rsplit('@',1)[-1] for a in addresses(msg.sender)}
            for row,lead in bylead.get(next(iter(tokens)),[]):
                lead_email=str(lead.get('E-Mail') or '').strip().lower()
                lead_domain=lead_email.rsplit('@',1)[-1]
                # Kollegen-Zuordnung nur für verifizierte Firmendomains: Mail-Domain = eigene Website-Domain
                # des Leads. Freemail-Nutzer (gmail, gmx, pm.me …) sind nie "dieselbe Firma".
                if lead_domain in FREEMAIL_DOMAINS or lead_domain!=company_domain(lead): continue
                if lead_domain in sender_domains:
                    matched_rows.append((row,lead))
        unique_rows={}
        for row,lead in matched_rows: unique_rows.setdefault(row,lead)
        for row,lead in unique_rows.items():
            blocked=cls.category in {'OPTOUT','BOUNCE'}
            outcome = delivery_bounce_status(msg.body, cls.extracted_email) if cls.category == 'BOUNCE' else None
            permanently_suppressed = cls.category == 'OPTOUT' or outcome == 'hard_bounce'
            # A corrected classifier must repair an old neutral event, without
            # replaying an already complete suppression or sending anything.
            negative_upgrade = blocked and (
                (permanently_suppressed and str(lead.get('Suppressed') or '').lower() != 'yes')
                or str(lead.get('Versandfreigabe') or '').lower() != 'no'
                or (cls.category == 'OPTOUT' and str(lead.get('Opt-out-Status') or '').lower() != 'yes')
                or (cls.category == 'BOUNCE' and not lead.get('Bounce_Status')))
            missing_negative_event = blocked and (msg.message_id, cls.category, str(lead.get('Lead-ID') or '')) not in seen_classifications
            if already_seen and not negative_upgrade and not missing_negative_event:
                continue
            event_id = eid if not already_seen else eid + '-RECLASSIFIED-' + cls.category
            matched+=1;categories[cls.category]=categories.get(cls.category,0)+1
            change={}
            if cls.category != 'BOUNCE':
                change['Last_Reply_At']=msg.date or datetime.now(timezone.utc).isoformat()
            # Replies on already suppressed records must not erase their status.
            if str(lead.get('Reply_Status') or '').lower() not in {'opt_out','bounced'}:
                change['Reply_Status']=compute_lead_update(row,lead.get('Lead-ID'),cls)['reply_status']

            rescued = False
            rescue_target = None
            if cls.category == 'BOUNCE':
                target_email = cls.extracted_email or str(lead.get('E-Mail') or '')
                try:
                    from bounce_rescue_agent import BounceRescueAgent
                    rescuer = BounceRescueAgent(timeout=5)
                    rescue_res = rescuer.rescue_lead(lead, failed_email=target_email)
                    if rescue_res.status == 'SUCCESS' and rescue_res.rescued_email:
                        rescued = True
                        rescue_target = rescue_res.rescued_email
                except Exception as exc:
                    logger.warning("Bounce rescue exception for %s: %s", target_email, exc)

            if rescued:
                change['E-Mail'] = rescue_target
                change['Bounce_Status'] = 'rescued'
                change['Suppressed'] = 'no'
                change['Versandfreigabe'] = 'yes'
                change['Reply_Status'] = 'bounce_rescued'
                if 'Pipeline' in headers:
                    change['Pipeline'] = 'Freigegeben'
                if 'Notizen' in headers:
                    old_notes = str(lead.get('Notizen') or '')
                    note = f"Bounce gerettet ({target_email} -> {rescue_target})"
                    change['Notizen'] = (old_notes + '; ' + note).strip('; ')
            elif blocked:
                change['Versandfreigabe'] = 'no'
                if permanently_suppressed:
                    change['Suppressed'] = 'yes'
                if cls.category == 'OPTOUT' or not lead.get('Suppression_Reason'):
                    change['Suppression_Reason'] = 'INBOUND_' + cls.category
                if cls.category=='OPTOUT':change['Opt-out-Status']='yes'
                if cls.category=='BOUNCE':
                    previous = str(lead.get('Bounce_Status') or '').strip().lower()
                    if previous not in {'hard_bounce', 'hard', 'hardbounce'} or outcome == 'hard_bounce':
                        change['Bounce_Status'] = 'hard_bounce' if outcome == 'hard_bounce' else 'bounce_review'
                        if 'Last_Error' in headers:
                            change['Last_Error'] = outcome
                    if 'Pipeline' in headers:
                        change['Pipeline'] = 'Bounce'
            if str(lead.get('Reply_Status') or '').lower() not in {'opt_out','bounced'}:
                actions=reply_actions(cls.category, msg.body, return_date=cls.recontact_date)
                # Bestehende Sheets können noch das alte Schema haben.
                change.update({k:v for k,v in actions.items() if k in headers})
            if apply:
                crm_write_readback(svc,SPREADSHEET_ID,headers,row,change)
            event_reason = cls.reason + (f" [RESCUED -> {rescue_target}]" if rescued else "")
            pending.append([event_id, msg.date or datetime.now(timezone.utc).isoformat(),
                msg.source+':'+msg.owner,msg.sender,msg.subject,msg.message_id,
                lead.get('Lead-ID',''),cls.category,'no' if rescued else ('yes' if blocked else 'no'),
                'PROCESSED' if apply else 'PENDING',event_reason,'','MATCHED'])
            lead.update(change)
        seen_ids.add(eid);seen_mids.add(msg.message_id)
    if apply and pending:
        # append is never automatically retried after a timeout; message IDs dedupe replay.
        result=svc.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID,
            range='INBOUND_EVENTS!A:M',valueInputOption='RAW',insertDataOption='INSERT_ROWS',body={'values':pending}).execute()
        updated=result.get('updates',{}).get('updatedRange')
        if not updated:raise RuntimeError('INBOUND_APPEND_RANGE_MISSING')
        back=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range=updated).execute().get('values',[])
        if back!=pending:raise RuntimeError('INBOUND_EVENT_READBACK_MISMATCH')
    return {'scanned':len(messages),'matched_new_events':matched,'categories':categories,'applied':apply,'include_de':include_de,'customer_emails_sent':0}


def select_sent_evidence(messages, leads):
    from collections import defaultdict
    from datetime import timezone
    from email.utils import parsedate_to_datetime
    from sales_reconciliation import addresses
    own={'j-cherino@hsb-boden.com','j-post@hsb-boden.com','j-cherino@hsb-boden.de','j-post@hsb-boden.de'}
    index=defaultdict(list);found={}
    for lead in leads:index[str(lead.get('E-Mail') or lead.get('Email') or '').strip().lower()].append(lead)
    for msg in messages:
        sender=addresses(msg.get('from'));mid=str(msg.get('internet_message_id') or '').strip()
        if len(sender)!=1 or sender[0] not in own or not mid.startswith('<') or not mid.endswith('>'):continue
        try:
            stamp=parsedate_to_datetime(msg.get('date_str') or '')
            if stamp.tzinfo is None:continue
            stamp=stamp.astimezone(timezone.utc).isoformat()
        except (ValueError,TypeError):continue
        for email in addresses(msg.get('to')):
            matches=index.get(email,[])
            if len(matches)!=1:continue
            lead=matches[0]
            if str(lead.get('Send_Status') or '').strip().lower() in {'sent','gesendet'}:continue
            updates={'Send_Status':'sent','Send_Datum':stamp,'Internet_Message_ID':mid,
                     'Sender_Account':sender[0],'Batch_Status':'SENT'}
            if 'Reconciliation_Status' in lead:updates['Reconciliation_Status']='HOLD'
            if 'Reconciliation_Reasons' in lead:
                updates['Reconciliation_Reasons']=str(lead.get('Reconciliation_Reasons') or '')+'; CONFIRMED_SENT'
            key=lead.get('Lead-ID') or lead.get('Lead_ID')
            if key not in found or found[key]['updates']['Send_Datum']<stamp:
                found[key]={'lead_id':key,'row':lead['_row'],'updates':updates}
    return list(found.values())


def sync_sent_messages(apply=False):
    from com_mailbox_manager import ComMailboxClient
    from sync_to_google_sheet import get_sheets_service,SPREADSHEET_ID
    from outbound_safety import col_name
    svc=get_sheets_service();messages=[]
    for owner in ['JOEL','JORDI']:
        messages.extend(ComMailboxClient(owner).fetch_sent_messages(limit=0))
    rows=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!A1:BU6425').execute()['values']
    headers=rows[0];leads=[dict(zip(headers,r),_row=i) for i,r in enumerate(rows[1:],2)]
    evidence=select_sent_evidence(messages,leads)
    if apply and evidence:
        data=[{'range':f"ALL_LEADS!{col_name(headers.index(k)+1)}{e['row']}",'values':[[v]]} for e in evidence for k,v in e['updates'].items()]
        svc.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID,body={'valueInputOption':'RAW','data':data}).execute()
        back=svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,range='ALL_LEADS!A1:BU6425').execute()['values']
        for e in evidence:
            actual=dict(zip(back[0],back[e['row']-1]))
            if actual.get('Lead-ID')!=e['lead_id'] or any(actual.get(k)!=v for k,v in e['updates'].items()):
                raise RuntimeError('SENT_CRM_READBACK_MISMATCH')
    return {'sent_headers_scanned':len(messages),'missing_sent_status':len(evidence),'applied':apply,'verified_rows':len(evidence) if apply else 0,'customer_emails_sent':0}


def rescue_crm_bounces(apply=False, limit=50, svc=None):
    """
    Durchsucht bestehende Bounces im CRM und versucht, alternative Adressen via Impressum zu retten.
    """
    from bounce_rescue_agent import BounceRescueAgent
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    from outbound_safety import col_name
    svc = svc or get_sheets_service()
    res = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()
    rows = res.get("values", [])
    if not rows:
        return {"scanned_bounces": 0, "rescued_count": 0, "failed_count": 0, "rescued": [], "applied": apply}
    headers = rows[0]
    leads = [dict(zip(headers, r), _row=i) for i, r in enumerate(rows[1:], start=2)]

    rescuer = BounceRescueAgent(timeout=5)
    rescued_leads = []
    failed_leads = []

    for lead in leads:
        bounce_st = str(lead.get('Bounce_Status') or '').strip().lower()
        reply_st = str(lead.get('Reply_Status') or '').strip().lower()
        if bounce_st == 'rescued' or reply_st == 'bounce_rescued':
            continue
        if bounce_st not in ('hard_bounce', 'bounce_review', 'soft_bounce', 'hard') and reply_st != 'bounced':
            continue

        target_email = str(lead.get('E-Mail') or lead.get('Email') or '').strip().lower()
        if not target_email or '@' not in target_email:
            continue

        rescue_res = rescuer.rescue_lead(lead, failed_email=target_email)
        if rescue_res.status == 'SUCCESS' and rescue_res.rescued_email:
            change = {
                'E-Mail': rescue_res.rescued_email,
                'Bounce_Status': 'rescued',
                'Suppressed': 'no',
                'Versandfreigabe': 'yes',
                'Reply_Status': 'bounce_rescued',
            }
            if 'Pipeline' in headers:
                change['Pipeline'] = 'Freigegeben'
            if 'Notizen' in headers:
                old_notes = str(lead.get('Notizen') or '')
                note = f"Bounce gerettet ({target_email} -> {rescue_res.rescued_email})"
                change['Notizen'] = (old_notes + '; ' + note).strip('; ')
            rescued_leads.append({
                'lead_id': lead.get('Lead-ID') or lead.get('Lead_ID'),
                'row': lead['_row'],
                'original_email': target_email,
                'rescued_email': rescue_res.rescued_email,
                'source': rescue_res.source_url,
                'updates': {k: v for k, v in change.items() if k in headers}
            })
            if limit and len(rescued_leads) >= limit:
                break
        else:
            failed_leads.append({
                'lead_id': lead.get('Lead-ID') or lead.get('Lead_ID'),
                'email': target_email,
                'reason': rescue_res.notes
            })

    if apply and rescued_leads:
        data = [{'range': f"ALL_LEADS!{col_name(headers.index(k)+1)}{item['row']}", 'values': [[v]]}
                for item in rescued_leads for k, v in item['updates'].items()]
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'valueInputOption': 'RAW', 'data': data}
        ).execute()
        back = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()['values']
        for item in rescued_leads:
            actual = dict(zip(back[0], back[item['row'] - 1]))
            for k, v in item['updates'].items():
                if actual.get(k) != v:
                    raise RuntimeError(f"BOUNCE_RESCUE_READBACK_MISMATCH in row {item['row']} col {k}")

    return {
        "scanned_bounces": len(rescued_leads) + len(failed_leads),
        "rescued_count": len(rescued_leads),
        "failed_count": len(failed_leads),
        "rescued": [{'lead_id': item['lead_id'], 'from': item['original_email'], 'to': item['rescued_email'], 'source': item['source']} for item in rescued_leads],
        "applied": apply
    }


def approve_verified_drafts(apply=False, limit=0, owner=None, audit_dir=None, svc=None):
    """
    Gleicht vorhandene All-Inkl Entwürfe mit dem CRM ab.
    Für Leads mit passendem kanonischen Entwurf:
    - Spalte BE (Pipeline) = "Freigegeben"
    - Spalte Z (Versandfreigabe) = "yes"
    """
    from pathlib import Path
    import json
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    from outbound_safety import col_name
    from sales_reconciliation import addresses, normalize_owner

    svc = svc or get_sheets_service()
    res = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()
    rows = res.get("values", [])
    if not rows:
        return {"drafts_scanned": 0, "eligible_leads": 0, "applied": apply, "sample": []}
    headers = rows[0]
    leads = [dict(zip(headers, r), _row=i) for i, r in enumerate(rows[1:], start=2)]

    leads_by_email = {}
    for l in leads:
        em = str(l.get('E-Mail') or l.get('Email') or '').strip().lower()
        if em and '@' in em:
            leads_by_email[em] = l

    draft_recipients = set()
    if audit_dir and (Path(audit_dir) / 'drafts.json').exists():
        draft_records = json.loads((Path(audit_dir) / 'drafts.json').read_text())
        for d in draft_records:
            if d.get('technical_ready', False) and not d.get('internal_test', False):
                for r in d.get('recipients', []):
                    draft_recipients.add(r.strip().lower())
    else:
        from com_mailbox_manager import ComMailboxClient
        owners = [normalize_owner(owner)] if owner else ['JOEL', 'JORDI']
        for o in owners:
            client = ComMailboxClient(o)
            drafts = client.list_drafts(limit=0)
            for d in drafts:
                for r in addresses(d.get('to')):
                    draft_recipients.add(r.strip().lower())

    approved_leads = []
    for em in sorted(draft_recipients):
        lead = leads_by_email.get(em)
        if not lead:
            continue
        if owner and normalize_owner(lead.get('Verantwortlicher')) != normalize_owner(owner):
            continue
        optout = str(lead.get('Opt_Out') or lead.get('Opt-out-Status') or '').strip().lower()
        suppressed = str(lead.get('Suppressed') or '').strip().lower()
        bounce_st = str(lead.get('Bounce_Status') or '').strip().lower()
        send_st = str(lead.get('Send_Status') or '').strip().lower()
        if optout in ('yes', 'ja', 'true') or suppressed in ('yes', 'ja', 'true'):
            continue
        if bounce_st in ('hard_bounce', 'hard', 'hardbounce'):
            continue
        if send_st in ('sent', 'gesendet') or lead.get('Send_Datum'):
            continue

        current_freigabe = str(lead.get('Versandfreigabe') or '').strip().lower()
        current_pipe = str(lead.get('Pipeline') or '').strip()

        if current_freigabe in ('yes', 'ja', 'true') and current_pipe == 'Freigegeben':
            continue

        updates = {}
        if 'Versandfreigabe' in headers:
            updates['Versandfreigabe'] = 'yes'
        if 'Pipeline' in headers:
            updates['Pipeline'] = 'Freigegeben'

        approved_leads.append({
            'lead_id': lead.get('Lead-ID') or lead.get('Lead_ID'),
            'row': lead['_row'],
            'email': em,
            'owner': normalize_owner(lead.get('Verantwortlicher')),
            'updates': updates
        })
        if limit and len(approved_leads) >= limit:
            break

    if apply and approved_leads:
        data = [{'range': f"ALL_LEADS!{col_name(headers.index(k)+1)}{item['row']}", 'values': [[v]]}
                for item in approved_leads for k, v in item['updates'].items()]
        chunk_size = 500
        for i in range(0, len(data), chunk_size):
            svc.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'valueInputOption': 'RAW', 'data': data[i:i+chunk_size]}
            ).execute()
        back = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="ALL_LEADS!A1:BU6425").execute()['values']
        for item in approved_leads[:20]:
            actual = dict(zip(back[0], back[item['row'] - 1]))
            for k, v in item['updates'].items():
                if actual.get(k) != v:
                    raise RuntimeError(f"APPROVE_DRAFTS_READBACK_MISMATCH in row {item['row']} col {k}")

    return {
        "drafts_scanned": len(draft_recipients),
        "eligible_leads": len(approved_leads),
        "applied": apply,
        "sample": [{'row': x['row'], 'lead_id': x['lead_id'], 'email': x['email']} for x in approved_leads[:10]]
    }

