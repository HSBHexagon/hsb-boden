import sys
from pathlib import Path
import pytest

ENGINE = Path(__file__).resolve().parents[1] / 'engine'
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))


def test_strip_x_unsent_preserves_other_headers_and_original_body():
    from sent_header_repair import strip_x_unsent
    raw = (b'From: Jordie <j-post@hsb-boden.com>\r\n'
           b'To: person@example.org\r\n'
           b'Message-ID: <m1@example.org>\r\n'
           b'X-Unsent: 1\r\n'
           b'Subject: Original\r\n\r\nBody\r\n')
    result = strip_x_unsent(raw)
    assert result == raw.replace(b'X-Unsent: 1\r\n', b'')
    assert b'Body\r\n' == result.split(b'\r\n\r\n')[1]


@pytest.mark.parametrize('header', [
    b'X-Unsent: 0\r\n',
    b'X-Unsent: 1\r\nX-Unsent: 1\r\n',
    b'',
])
def test_strip_x_unsent_rejects_ambiguous_or_absent_markers(header):
    from sent_header_repair import strip_x_unsent
    raw = b'From: x@example.org\r\n' + header + b'\r\nContent\r\n'
    with pytest.raises(ValueError):
        strip_x_unsent(raw)


def test_plan_only_accepts_unique_crm_confirmed_sent_messages():
    from sent_header_repair import plan_sent_repairs
    sent = {'message_id': '<m1@example.org>', 'recipients': ['person@example.org'],
            'senders': ['j-post@hsb-boden.com'], 'uid': '3', 'uidvalidity': '11',
            'lead_id': 'L1', 'x_unsent': True, 'draft_flag': False}
    leads = [{'Lead-ID': 'L1', 'E-Mail': 'person@example.org', 'Verantwortlicher': 'Jordie Post',
              'Send_Status': 'sent', 'Send_Datum': '2026-11-10T10:00:00Z',
              'Internet_Message_ID': '<m1@example.org>', 'Sender_Account': 'j-post@hsb-boden.com'}]
    box = {'sent': [sent], 'drafts': [], 'inbox': []}
    plan, counts = plan_sent_repairs(leads, box, 'JORDI')
    assert len(plan) == 1
    assert counts['eligible_to_correct'] == 1
    assert counts['sent_with_unsent_header'] == 1
    assert 'person@example.org' not in str(counts)
    box['drafts'] = [sent]
    plan, counts = plan_sent_repairs(leads, box, 'JORDI')
    assert len(plan) == 0
    assert counts['held'] == 1
    box['drafts'] = []
    leads[0]['Send_Status'] = 'drafted'
    plan, counts = plan_sent_repairs(leads, box, 'JORDI')
    assert len(plan) == 0 and counts['held'] == 1
