import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from closed_loop_crm import rescue_crm_bounces
from bounce_rescue_agent import RescueResult

class TestBounceRescueIntegration(unittest.TestCase):
    def test_rescue_crm_bounces_dry_run(self):
        mock_svc = MagicMock()
        mock_svc.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Lead-ID", "Firma", "E-Mail", "Website", "Bounce_Status", "Reply_Status", "Notizen"],
                ["HSB-001", "Musterbau GmbH", "dead@musterbau.de", "https://musterbau.de", "hard_bounce", "", ""]
            ]
        }
        mock_rescue_res = RescueResult(
            status="SUCCESS",
            failed_email="dead@musterbau.de",
            rescued_email="info@musterbau.de",
            company_name="Musterbau GmbH",
            domain="musterbau.de",
            source_url="https://musterbau.de/impressum",
            confidence=0.95,
            notes="Alternative E-Mail im Impressum gefunden und MX verifiziert."
        )

        with patch("bounce_rescue_agent.BounceRescueAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.rescue_lead.return_value = mock_rescue_res
            mock_agent_cls.return_value = mock_agent

            res = rescue_crm_bounces(apply=False, limit=5, svc=mock_svc)
            self.assertEqual(res["rescued_count"], 1)
            self.assertEqual(res["rescued"][0]["to"], "info@musterbau.de")
            mock_svc.spreadsheets().values().batchUpdate.assert_not_called()

    def test_rescue_crm_bounces_apply(self):
        mock_svc = MagicMock()
        headers = ["Lead-ID", "Firma", "E-Mail", "Website", "Bounce_Status", "Suppressed", "Versandfreigabe", "Reply_Status", "Notizen"]
        row2 = ["HSB-001", "Musterbau GmbH", "dead@musterbau.de", "https://musterbau.de", "hard_bounce", "yes", "no", "", ""]
        readback_row2 = ["HSB-001", "Musterbau GmbH", "info@musterbau.de", "https://musterbau.de", "rescued", "no", "yes", "bounce_rescued", "Bounce gerettet (dead@musterbau.de -> info@musterbau.de)"]
        
        mock_svc.spreadsheets().values().get().execute.side_effect = [
            {"values": [headers, row2]},            # first read
            {"values": [headers, readback_row2]}   # readback
        ]
        mock_rescue_res = RescueResult(
            status="SUCCESS",
            failed_email="dead@musterbau.de",
            rescued_email="info@musterbau.de",
            company_name="Musterbau GmbH",
            domain="musterbau.de",
            source_url="https://musterbau.de/impressum",
            confidence=0.95,
            notes="Alternative E-Mail im Impressum gefunden und MX verifiziert."
        )

        with patch("bounce_rescue_agent.BounceRescueAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.rescue_lead.return_value = mock_rescue_res
            mock_agent_cls.return_value = mock_agent

            res = rescue_crm_bounces(apply=True, limit=5, svc=mock_svc)
            self.assertEqual(res["rescued_count"], 1)
            self.assertTrue(res["applied"])
            mock_svc.spreadsheets().values().batchUpdate.assert_called_once()

if __name__ == "__main__":
    unittest.main()
