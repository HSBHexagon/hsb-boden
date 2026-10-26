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
        pipeline_val = "Bounced / Ungültig"
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


def sync_inbounds(apply=False, include_de=True):
    """Replay-safe event ingestion; negative evidence never clears a suppression."""
    from collections import defaultdict
    from datetime import datetime, timezone
    import hashlib
    import re
    from dual_domain_collector import collect_all_inbounds
    from inbound_classifier import classify_inbound_message
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
        if cls.category=='OPTOUT':
            # Abmelde-Token aus dem List-Unsubscribe-Link: gilt auch, wenn ein Kollege antwortet.
            for token in UNSUBSCRIBE_TOKEN_RE.findall(msg.body or ''):
                matched_rows.extend(bylead.get(token,[]))
        unique_rows={}
        for row,lead in matched_rows: unique_rows.setdefault(row,lead)
        for row,lead in unique_rows.items():
            blocked=cls.category in {'OPTOUT','BOUNCE'}
            # A corrected classifier must repair an old neutral event, without
            # replaying an already complete suppression or sending anything.
            negative_upgrade = blocked and (
                str(lead.get('Suppressed') or '').lower() != 'yes'
                or str(lead.get('Versandfreigabe') or '').lower() != 'no'
                or (cls.category == 'OPTOUT' and str(lead.get('Opt-out-Status') or '').lower() != 'yes')
                or (cls.category == 'BOUNCE' and not lead.get('Bounce_Status')))
            missing_negative_event = blocked and (msg.message_id, cls.category, str(lead.get('Lead-ID') or '')) not in seen_classifications
            if already_seen and not negative_upgrade and not missing_negative_event:
                continue
            event_id = eid if not already_seen else eid + '-RECLASSIFIED-' + cls.category
            matched+=1;categories[cls.category]=categories.get(cls.category,0)+1
            change={'Last_Reply_At':msg.date or datetime.now(timezone.utc).isoformat()}
            # Replies on already suppressed records must not erase their status.
            if str(lead.get('Reply_Status') or '').lower() not in {'opt_out','bounced'}:
                change['Reply_Status']=compute_lead_update(row,lead.get('Lead-ID'),cls)['reply_status']
            if blocked:
                change.update({'Suppressed':'yes','Versandfreigabe':'no',
                    'Suppression_Reason':'INBOUND_'+cls.category})
                if cls.category=='OPTOUT':change['Opt-out-Status']='yes'
                if cls.category=='BOUNCE':change['Bounce_Status']='hard_bounce' if re.search(r'\b5\.\d\.\d|\b55\d\b|user unknown',msg.body,re.I) else 'bounce_review'
            if cls.recontact_date:change['Follow-up-Datum']=cls.recontact_date
            if apply:
                crm_write_readback(svc,SPREADSHEET_ID,headers,row,change)
            pending.append([event_id, msg.date or datetime.now(timezone.utc).isoformat(),
                msg.source+':'+msg.owner,msg.sender,msg.subject,msg.message_id,
                lead.get('Lead-ID',''),cls.category,'yes' if blocked else 'no',
                'PROCESSED' if apply else 'PENDING',cls.reason,'','MATCHED'])
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
