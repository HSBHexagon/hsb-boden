import sys
from unittest.mock import MagicMock

# Mock google modules prior to import
sys.modules['google'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.credentials'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

sys.path.insert(0, 'apps/sales-os/engine')
import sync_apple_mail

def test_ignored_email_keywords_constant():
    assert hasattr(sync_apple_mail, 'IGNORED_EMAIL_KEYWORDS')
    assert isinstance(sync_apple_mail.IGNORED_EMAIL_KEYWORDS, (tuple, set))
    expected = ('hsb-boden.de', 'microsoft', 'postmaster', 'mailer-daemon')
    for kw in expected:
        assert kw in sync_apple_mail.IGNORED_EMAIL_KEYWORDS

def test_filtering_logic():
    emails = [
        "valid.lead@example.com",
        "user@hsb-boden.de",
        "admin@microsoft.com",
        "postmaster@domain.com",
        "mailer-daemon@server.net",
        "another.valid@company.de"
    ]
    cand_emails = [e.lower() for e in emails if not any(x in e.lower() for x in sync_apple_mail.IGNORED_EMAIL_KEYWORDS)]
    assert cand_emails == ["valid.lead@example.com", "another.valid@company.de"]
