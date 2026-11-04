from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from dual_domain_collector import UnifiedInboundMessage, deduplicate_inbounds

def test_deduplicate_inbounds():
    m1 = UnifiedInboundMessage(source="COM_IMAP", owner="JORDI", message_id="<123@abc>", date="2026-10-22", sender="k@kunde.de", subject="Re: Hallo", body="Ja")
    m2 = UnifiedInboundMessage(source="DE_M365", owner="JORDI", message_id="<123@abc>", date="2026-10-22", sender="k@kunde.de", subject="Re: Hallo", body="Ja")
    m3 = UnifiedInboundMessage(source="COM_IMAP", owner="JOEL", message_id="<456@def>", date="2026-10-22", sender="b@kunde.de", subject="Re: Test", body="Nein")
    deduped = deduplicate_inbounds([m1, m2, m3])
    assert len(deduped) == 2
    assert {m.message_id for m in deduped} == {"<123@abc>", "<456@def>"}

def test_deduplicate_inbounds_fallback_key():
    m1 = UnifiedInboundMessage(source="COM_IMAP", owner="JORDI", message_id="", date="2026-10-22", sender="k@kunde.de", subject="Re: Hallo", body="Ja")
    m2 = UnifiedInboundMessage(source="DE_M365", owner="JORDI", message_id="", date="2026-10-22", sender="k@kunde.de", subject="Re: Hallo", body="Ja")
    deduped = deduplicate_inbounds([m1, m2])
    assert len(deduped) == 1
