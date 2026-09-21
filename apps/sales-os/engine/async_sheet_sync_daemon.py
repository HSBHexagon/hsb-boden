import json
from typing import Any


def flush_pending_to_sheets(
    shadow_store: Any, sheets_client: Any, batch_size: int = 50
) -> int:
    pending_events = shadow_store.get_pending_sync_events()
    if not pending_events:
        return 0

    chunk = pending_events[:batch_size]
    updates = []
    processed_ids = []

    for event in chunk:
        lead_id = event.get("lead_id")
        lead = shadow_store.get_lead(lead_id)
        if not lead or not lead.get("row_number"):
            processed_ids.append(event["id"])
            continue

        row_num = lead["row_number"]
        payload = json.loads(event.get("payload") or "{}")

        # Range AO{row}:AR{row} = [Status, Draft_ID, Drafted_At, Batch_ID]
        updates.append(
            {
                "range": f"ALL_LEADS!AO{row_num}:AR{row_num}",
                "values": [
                    [
                        "drafted",
                        payload.get("draft_id", ""),
                        payload.get("drafted_at", ""),
                        payload.get("batch_id", ""),
                    ]
                ],
            }
        )
        processed_ids.append(event["id"])

    if updates:
        sheets_client.batch_update_cells(updates)

    shadow_store.mark_synced(processed_ids)
    return len(processed_ids)
