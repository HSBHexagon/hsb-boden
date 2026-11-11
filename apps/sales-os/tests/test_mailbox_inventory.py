from email.message import EmailMessage

import pytest


class HeaderMailbox:
    def __init__(self, drift=False, omit=False):
        self.drift, self.omit, self.searches = drift, omit, 0
        self.folder = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def select(self, folder, readonly=False):
        assert readonly, 'inventory must never select writable'
        self.folder, self.searches = folder, 0
        self.validity_available = True
        return 'OK', [b'1']

    def response(self, name):
        assert name == 'UIDVALIDITY'
        if not self.validity_available:
            return name, [None]
        self.validity_available = False
        return 'UIDVALIDITY', [b'10']

    def uid(self, command, *args):
        if command.upper() == 'SEARCH':
            self.searches += 1
            return 'OK', [b'1 2' if self.drift and self.searches > 1 else b'1']
        assert command.upper() == 'FETCH', 'inventory may only SEARCH or FETCH'
        assert 'BODY.PEEK[HEADER.FIELDS' in args[1]
        if self.omit:
            return 'OK', []
        msg = EmailMessage()
        msg['From'] = 'Joel <j-cherino@hsb-boden.com>'
        msg['To'] = 'Test Person <person@example.org>'
        msg['Message-ID'] = '<one@example.org>'
        msg['X-HSB-Lead-ID'] = 'HSB-20260101-1'
        msg['X-HSB-Template-ID'] = 'v2-produktion-reparatur-s1'
        msg['X-HSB-Copy-Rev'] = '2026-11-05'
        return 'OK', [(b'1 (UID 1 BODY[HEADER.FIELDS] {100}', msg.as_bytes()), b')']


class Client:
    cfg = {'drafts_folder': 'Drafts', 'sent_folder': 'Sent', 'inbox_folder': 'INBOX'}

    def __init__(self, **kwargs):
        self.imap = HeaderMailbox(**kwargs)

    def _get_imap(self):
        return self.imap


def test_inventory_uses_headers_and_preserves_uid_identity():
    from mailbox_inventory import scan_headers
    result = scan_headers('JOEL', Client())
    assert result['drafts'][0] == {
        'owner': 'JOEL', 'folder': 'Drafts', 'uidvalidity': '10', 'uid': '1',
        'message_id': '<one@example.org>', 'recipients': ['person@example.org'],
        'senders': ['j-cherino@hsb-boden.com'], 'lead_id': 'HSB-20260101-1',
        'template_id': 'v2-produktion-reparatur-s1', 'copy_rev': '2026-11-05',
    }
    assert len(result['sent']) == 1


@pytest.mark.parametrize('kwargs,error', [
    ({'drift': True}, 'MAILBOX_CHANGED_DURING_INVENTORY'),
    ({'omit': True}, 'INVENTORY_FETCH_INCOMPLETE'),
])
def test_inventory_never_accepts_incomplete_or_changed_snapshot(kwargs, error):
    from mailbox_inventory import scan_headers
    with pytest.raises(RuntimeError, match=error):
        scan_headers('JOEL', Client(**kwargs))


def test_distribution_detects_wrong_mailbox_without_publishing_customer_addresses():
    from mailbox_inventory import summarize
    leads = [{'Lead-ID': 'HSB-20260101-1', 'E-Mail': 'person@example.org',
              'Verantwortlicher': 'Jordie Post', 'Branche': 'Lebensmittelproduktion'}]
    record = {'lead_id': 'HSB-20260101-1', 'recipients': ['person@example.org'],
              'senders': ['j-cherino@hsb-boden.com'], 'message_id': '<one@example.org>',
              'template_id': 'v2-produktion-reparatur-s1', 'copy_rev': '2026-11-05'}
    mailboxes = {'JOEL': {'drafts': [record], 'sent': [], 'inbox': []},
                 'JORDI': {'drafts': [], 'sent': [], 'inbox': []}}
    result = summarize(leads, mailboxes)
    assert result['owners']['JOEL']['wrong_crm_owner'] == 1
    assert result['owners']['JOEL']['segments'] == {'produktion': 1}
    assert 'person@example.org' not in str(result)
    assert result['customer_emails_sent'] == 0


def test_missing_search_payload_does_not_become_empty_mailbox():
    from mailbox_inventory import scan_headers
    client = Client()
    original = client.imap.uid
    client.imap.uid = lambda command, *args: ('OK', [None]) if command.upper() == 'SEARCH' else original(command, *args)
    with pytest.raises(RuntimeError, match='INVENTORY_SEARCH_INCOMPLETE'):
        scan_headers('JOEL', client)


def test_untrusted_copy_revision_never_appears_in_public_summary():
    from mailbox_inventory import scan_headers, summarize
    leads = [{'Lead-ID': 'HSB-20260101-1', 'E-Mail': 'person@example.org',
              'Verantwortlicher': 'JOEL', 'Branche': 'Lebensmittelproduktion'}]
    boxes = {'JOEL': scan_headers('JOEL', Client()), 'JORDI': {'drafts': [], 'sent': [], 'inbox': []}}
    boxes['JOEL']['drafts'][0]['copy_rev'] = 'private-customer@example.org'
    result = summarize(leads, boxes)
    assert result['owners']['JOEL']['copy_revisions'] == {'(unrecognized)': 1}
    assert 'private-customer@example.org' not in str(result)


def test_inventory_detects_sent_message_left_in_drafts():
    from mailbox_inventory import summarize
    lead = {'Lead-ID': 'L1', 'E-Mail': 'person@example.org', 'Verantwortlicher': 'JOEL'}
    record = {'lead_id': 'L1', 'recipients': ['person@example.org'],
              'senders': ['j-cherino@hsb-boden.com'], 'message_id': '<same@example.org>',
              'template_id': 'v2-produktion-reparatur-s1', 'copy_rev': '2026-11-05'}
    mailboxes = {'JOEL': {'drafts': [record], 'sent': [record], 'inbox': []},
                 'JORDI': {'drafts': [], 'sent': [], 'inbox': []}}
    summary = summarize([lead], mailboxes)
    assert summary['owners']['JOEL']['sent_message_still_in_drafts'] == 1
    assert summary['owners']['JORDI']['sent_message_still_in_drafts'] == 0
    assert 'person@example.org' not in str(summary)
