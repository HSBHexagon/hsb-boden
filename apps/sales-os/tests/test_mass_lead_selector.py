from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from mass_lead_selector import filter_and_partition_leads

def test_filter_and_partition_leads_skips_sent_and_optout():
    raw_leads = [
        {"Lead_ID": "L-1", "E-Mail": "a@firma.de", "Send_Status": "sent", "Firma": "Firma A"},
        {"Lead_ID": "L-2", "E-Mail": "b@firma.de", "Opt_Out": "YES", "Firma": "Firma B"},
        {"Lead_ID": "L-3", "E-Mail": "c@firma.de", "Send_Status": "", "Firma": "Firma C"},
        {"Lead_ID": "L-4", "E-Mail": "d@firma.de", "Send_Status": "", "Firma": "Firma D"},
        {"Lead_ID": "L-5", "E-Mail": "", "Send_Status": "", "Firma": "Firma E"},
    ]
    joel_leads, jordi_leads = filter_and_partition_leads(raw_leads)
    assert len(joel_leads) == 1
    assert len(jordi_leads) == 1
    assert joel_leads[0]["Lead_ID"] == "L-3"
    assert jordi_leads[0]["Lead_ID"] == "L-4"
