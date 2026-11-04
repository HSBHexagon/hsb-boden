from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from overhaul_drafts import build_canonical_body_2026
from hsb_core import assert_asset_gate, normalize_owner, sanitize_company_name
from run_100_batch import anrede_fuer
from com_mailbox_manager import ComMailboxClient

logger = logging.getLogger("mass_draft_generator")

def build_draft_payload(owner: str, lead: Dict[str, Any]) -> Dict[str, Any]:
    owner = normalize_owner(owner)
    flyer = assert_asset_gate(owner)
    email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
    raw_comp = str(lead.get("Firma") or lead.get("Company") or "").strip()
    company = sanitize_company_name(raw_comp, email)

    lead_copy = dict(lead)
    lead_copy["Firma"] = company
    lead_copy["Company"] = company
    anrede = anrede_fuer(lead_copy)

    lead_id = str(lead.get("Lead_ID") or lead.get("Lead-ID") or "")
    subject = f"Industrieböden für {company} – Beratung von {flyer.display_name}"
    body_html = build_canonical_body_2026(owner, anrede, target="com", lead_id=lead_id, to_email=email)

    return {
        "owner": owner,
        "lead_id": lead_id,
        "row_idx": lead.get("_row"),
        "to_email": email,
        "subject": subject,
        "body_html": body_html,
        "flyer_path": None,  # 0 KB Anhang
        "flyer_filename": None
    }

def generate_drafts_chunked(owner: str, leads: List[Dict[str, Any]], chunk_size: int = 50) -> List[Dict[str, Any]]:
    client = ComMailboxClient(owner)
    results = []
    for i in range(0, len(leads), chunk_size):
        chunk = leads[i:i + chunk_size]
        items = [build_draft_payload(owner, l) for l in chunk]
        chunk_res = client.create_drafts_batch(items)
        results.extend(chunk_res)
        logger.info(f"[{owner}] Chunk {i // chunk_size + 1}: {len(chunk_res)} Entwürfe erfolgreich angelegt.")
    return results
