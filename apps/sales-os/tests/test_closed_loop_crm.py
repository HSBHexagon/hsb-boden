from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from closed_loop_crm import compute_lead_update
from inbound_classifier import InboundClassificationResult

def test_compute_lead_update_bounce():
    cls_res = InboundClassificationResult(category="BOUNCE", confidence=0.95, reason="User unknown")
    upd = compute_lead_update(row_idx=15, lead_id="LEAD-101", cls_res=cls_res)
    assert upd["optout_val"] is None
    assert upd["reply_status"] == "bounced"
    assert upd["pipeline_val"] == "Bounced / Ungültig"

def test_compute_lead_update_ooo_with_date():
    cls_res = InboundClassificationResult(category="OOO_URLAUB", confidence=0.92, recontact_date="2026-11-05")
    upd = compute_lead_update(row_idx=20, lead_id="LEAD-202", cls_res=cls_res)
    assert upd["optout_val"] is None
    assert upd["reply_status"] == "auto_reply_ooo"
    assert "Wiedervorlage 2026-11-05" in upd["pipeline_val"]

def test_compute_lead_update_hot_lead():
    cls_res = InboundClassificationResult(category="HOT_LEAD", confidence=0.88, reason="Besichtigung gewünscht")
    upd = compute_lead_update(row_idx=35, lead_id="LEAD-303", cls_res=cls_res)
    assert upd["reply_status"] == "replied_interested"
    assert "HOT LEAD" in upd["pipeline_val"]

def test_compute_lead_update_optout():
    cls_res = InboundClassificationResult(category="OPTOUT", confidence=0.90, reason="Widerspruch")
    upd = compute_lead_update(row_idx=42, lead_id="LEAD-404", cls_res=cls_res)
    assert upd["optout_val"] == "YES"
    assert upd["reply_status"] == "opt_out"
    assert upd["pipeline_val"] == "Abgemeldet / Widerspruch"
