# apps/sales-os/engine/dual_domain_collector.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Optional
import logging
from pathlib import Path
import sys

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

logger = logging.getLogger("dual_domain_collector")

@dataclass
class UnifiedInboundMessage:
    source: str  # COM_IMAP | DE_M365
    owner: str   # JOEL | JORDI
    message_id: str
    date: str
    sender: str
    subject: str
    body: str

def deduplicate_inbounds(messages: List[UnifiedInboundMessage]) -> List[UnifiedInboundMessage]:
    seen: Set[str] = set()
    result: List[UnifiedInboundMessage] = []
    for msg in messages:
        key = msg.message_id.strip() if msg.message_id else f"{msg.sender.strip().lower()}_{msg.date}_{msg.subject.strip().lower()}"
        if key not in seen:
            seen.add(key)
            result.append(msg)
    return result

def collect_all_inbounds(owners: Optional[List[str]] = None, limit_per_mailbox: int = 0, include_de: bool = True) -> List[UnifiedInboundMessage]:
    from com_mailbox_manager import ComMailboxClient
    target_owners = owners or ["JOEL", "JORDI"]
    all_msgs: List[UnifiedInboundMessage] = []

    # 1. COM IMAP (All-Inkl .com Postfächer: Kasserver)
    for o in target_owners:
        try:
            client = ComMailboxClient(o)
            raw_items = client.fetch_inbound_messages(limit=limit_per_mailbox)
            for it in raw_items:
                all_msgs.append(UnifiedInboundMessage(
                    source="COM_IMAP",
                    owner=o,
                    message_id=it.get("internet_message_id") or it.get("id", ""),
                    date=it.get("date_str", ""),
                    sender=it.get("from", ""),
                    subject=it.get("subject", ""),
                    body=it.get("body", "")
                ))
        except Exception as e:
            raise RuntimeError(f"COM_INBOUND_UNAVAILABLE: {o}") from e

    if not include_de:
        return deduplicate_inbounds(all_msgs)

    # 2. DE M365 (Microsoft 365 Exchange Cloud Posteingang via Azure APIHub)
    try:
        from reconcile_cloud_mailbox import get_az_apihub_token, fetch_cloud_inbound_messages, CONNECTIONS
        az_token = get_az_apihub_token()
        for o in target_owners:
            conn_info = CONNECTIONS.get(o)
            if not conn_info:
                continue
            conn_id = conn_info.get("connection_id")
            try:
                m365_items = fetch_cloud_inbound_messages(az_token, conn_id, limit=(limit_per_mailbox or 1000))
                for it in m365_items:
                    body_text = it.get("body") or it.get("Body") or it.get("bodyPreview") or ""
                    if isinstance(body_text,dict): body_text=body_text.get('content','')
                    import hashlib
                    native_id=it.get('internet_message_id') or ''
                    fallback='DE_M365:'+o+':'+str(it.get('id') or hashlib.sha256(str(it).encode()).hexdigest())
                    all_msgs.append(UnifiedInboundMessage(
                        source="DE_M365",
                        owner=o,
                        message_id=native_id or fallback,
                        date=it.get("date_str", ""),
                        sender=it.get("from") or it.get("sender") or it.get("From") or "",
                        subject=it.get("subject") or it.get("Subject") or "",
                        body=body_text
                    ))
            except Exception as me:
                raise RuntimeError(f"DE_INBOUND_UNAVAILABLE: {o}") from me
    except Exception as e:
        raise RuntimeError("DE_INBOUND_UNAVAILABLE: use --com-only for an explicitly partial sync") from e

    return deduplicate_inbounds(all_msgs)
