from pathlib import Path
import sys
from typing import Any, Dict, List

ENGINE = Path(__file__).resolve().parent
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from canonical_template_factory import render_canonical_email


def process_batch_chunk(
    leads: List[Dict[str, Any]],
    owner: str,
    batch_engine: Any,
    shadow_store: Any,
    batch_id: str = "BATCH-DEFAULT",
) -> Dict[str, Any]:
    sub_requests = []
    lead_map = {}

    for idx, lead in enumerate(leads, start=1):
        req_id = str(idx)
        try:
            rendered = render_canonical_email(lead, owner=owner)
            sub_req = batch_engine.build_create_draft_request(
                req_id=req_id,
                subject=rendered["subject"],
                to_email=rendered["to_address"],
                body_html=rendered["body_html"],
            )
            sub_requests.append(sub_req)
            lead_map[req_id] = lead
        except Exception:
            # Skip invalid lead immediately
            continue

    if not sub_requests:
        return {"success_count": 0, "failed_count": len(leads), "draft_ids": []}

    responses = batch_engine.execute_batch(sub_requests)
    success_count = 0
    failed_count = 0
    draft_ids = []

    for req_id, lead in lead_map.items():
        resp = responses.get(req_id, {})
        status = resp.get("status")
        if status in (200, 201):
            body = resp.get("body", {})
            draft_id = body.get("id", f"GRAPH-{req_id}")
            draft_ids.append(draft_id)
            shadow_store.record_draft_event(
                lead_id=lead["Lead_ID"],
                draft_id=draft_id,
                owner=owner,
                batch_id=batch_id,
            )
            success_count += 1
        else:
            failed_count += 1

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "draft_ids": draft_ids,
    }
