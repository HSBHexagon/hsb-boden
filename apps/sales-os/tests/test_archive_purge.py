"""Archiv leeren: nur 'Entwürfe-Archiv-v1', nur in den Papierkorb, nie STORE oder EXPUNGE."""
from email.message import EmailMessage
import re

import pytest

from archive_purge import find_trash, purge_archive
from draft_upgrade import ARCHIVE, mailbox_arg

ARCH = mailbox_arg(ARCHIVE)


def _raw(mid, to='x@firma.de', sender='j-post@hsb-boden.com', lead='L1'):
    msg = EmailMessage()
    msg['From'], msg['To'], msg['Message-ID'] = sender, to, mid
    if lead:
        msg['X-HSB-Lead-ID'] = lead
    msg.set_content('t')
    return msg.as_bytes()


class FakeImap:
    capabilities = (b'MOVE',)

    def __init__(self, boxes, listing=None, move_drops=False):
        self.boxes, self.folder, self.calls, self.writable = boxes, None, [], None
        self.listing = listing if listing is not None else [b'(\\HasNoChildren \\Trash) "." "Papierkorb"',
                                                             b'(\\HasNoChildren) "." "Drafts"']
        self.move_drops = move_drops

    def __enter__(self): return self
    def __exit__(self, *a): pass

    def list(self):
        return 'OK', self.listing

    def select(self, folder, readonly=False):
        self.folder, self.writable = folder.strip('"') if folder.strip('"') in self.boxes else folder, not readonly
        return ('OK', [b'1']) if self.folder in self.boxes else ('NO', [])

    def response(self, key):
        return key, [b'7']

    def uid(self, verb, *args):
        verb = verb.upper()
        self.calls.append(verb)
        box = self.boxes[self.folder]
        if verb == 'SEARCH':
            return 'OK', [' '.join(box).encode()]
        if verb == 'FETCH':
            out = []
            for uid in str(args[0]).split(','):
                out += [(b'1 (UID ' + uid.encode() + b' BODY[HEADER] {1}', box[uid]), b')']
            return 'OK', out
        if verb == 'MOVE':
            assert self.writable
            for uid in str(args[0]).split(','):
                raw = box.pop(uid)
                if not self.move_drops:
                    dest = self.boxes[args[1].strip('"')]
                    dest[str(1000 + len(dest))] = raw
            return 'OK', []
        pytest.fail('unexpected ' + verb)

    def store(self, *a): pytest.fail('STORE')
    def expunge(self): pytest.fail('EXPUNGE')
    def delete(self, *a): pytest.fail('DELETE')
    def append(self, *a): pytest.fail('APPEND')


class Client:
    def __init__(self, imap):
        self.imap = imap
        self.cfg = {'drafts_folder': 'Drafts', 'sent_folder': 'Sent', 'inbox_folder': 'INBOX'}

    def _get_imap(self):
        return self.imap


def _boxes(archive=None):
    return {'Drafts': {'1': _raw('<d1@h>', 'x@firma.de', lead='L1')}, 'Sent': {'5': _raw('<s@h>')},
            'INBOX': {'6': _raw('<i@h>')}, 'Papierkorb': {},
            **({ARCH: archive} if archive is not None else {})}


def test_dry_run_only_counts_and_never_moves():
    imap = FakeImap(_boxes({'1': _raw('<a@h>'), '2': _raw('<a@h>'), '3': _raw('<b@h>', 'y@firma.de', lead='L2')}))
    res = purge_archive(['JORDI'], {'JORDI': Client(imap)}, apply=False)['per_owner']['JORDI']
    assert res['archive_total'] == 3 and res['unique_message_ids'] == 2
    assert res['only_copy'] == 1 and res['moved'] == 0 and res['trash_folder'] == 'Papierkorb'
    assert 'MOVE' not in imap.calls and len(imap.boxes[ARCH]) == 3


def test_apply_moves_everything_to_trash_and_leaves_other_folders():
    imap = FakeImap(_boxes({'1': _raw('<a@h>'), '2': _raw('<b@h>')}))
    before = {k: dict(imap.boxes[k]) for k in ('Drafts', 'Sent', 'INBOX')}
    result = purge_archive(['JOEL'], {'JOEL': Client(imap)}, apply=True)
    res = result['per_owner']['JOEL']
    assert res['moved'] == 2 and res['archive_after'] == 0 and res['trash_after'] - res['trash_before'] == 2
    assert result['customer_emails_sent'] == 0 and imap.boxes[ARCH] == {} and len(imap.boxes['Papierkorb']) == 2
    assert {k: imap.boxes[k] for k in before} == before


def test_large_archive_is_moved_in_chunks():
    imap = FakeImap(_boxes({str(i): _raw(f'<m{i}@h>') for i in range(1, 1202)}))
    res = purge_archive(['JORDI'], {'JORDI': Client(imap)}, apply=True)['per_owner']['JORDI']
    assert res['moved'] == 1201 and imap.calls.count('MOVE') == 7


def test_second_run_finds_nothing():
    imap = FakeImap(_boxes({'1': _raw('<a@h>')}))
    purge_archive(['JOEL'], {'JOEL': Client(imap)}, apply=True)
    res = purge_archive(['JOEL'], {'JOEL': Client(imap)}, apply=True)['per_owner']['JOEL']
    assert res['archive_total'] == 0 and res['moved'] == 0


def test_missing_archive_is_zero_and_not_created():
    imap = FakeImap(_boxes())
    res = purge_archive(['JOEL'], {'JOEL': Client(imap)}, apply=True)['per_owner']['JOEL']
    assert res['archive_total'] == 0 and ARCH not in imap.boxes


def test_missing_trash_stops_without_fallback():
    imap = FakeImap(_boxes({'1': _raw('<a@h>')}), listing=[b'(\\HasNoChildren) "." "Drafts"'])
    with pytest.raises(RuntimeError, match='TRASH_NOT_FOUND'):
        purge_archive(['JOEL'], {'JOEL': Client(imap)}, apply=True)
    assert len(imap.boxes[ARCH]) == 1


def test_ambiguous_trash_stops():
    listing = [b'(\\Trash) "." "Papierkorb"', b'(\\Trash) "." "Trash"']
    with pytest.raises(RuntimeError, match='TRASH_AMBIGUOUS'):
        find_trash(FakeImap({}, listing=listing), {'drafts_folder': 'Drafts'})


@pytest.mark.parametrize('name', ['Drafts', 'Entw&APw-rfe-Archiv-v1'])
def test_trash_must_not_be_working_folder(name):
    listing = [('(\\Trash) "." "' + name + '"').encode()]
    with pytest.raises(RuntimeError, match='TRASH_NOT_FOUND'):
        find_trash(FakeImap({}, listing=listing), {'drafts_folder': 'Drafts'})


def test_name_fallback_only_when_no_special_use_flag():
    listing = [b'(\\HasNoChildren) "." "Drafts"', b'(\\HasNoChildren) "." "INBOX.Trash"']
    assert find_trash(FakeImap({}, listing=listing), {'drafts_folder': 'Drafts'}) == 'INBOX.Trash'


@pytest.mark.parametrize('name', ['Entw&APw-rfe', 'Gesendet', 'INBOX'])
def test_quoted_config_folders_are_never_trash(name):
    cfg = {'drafts_folder': '"Entw&APw-rfe"', 'sent_folder': '"Gesendet"', 'inbox_folder': '"INBOX"'}
    listing = [('(\\Trash) "." "' + name + '"').encode()]
    with pytest.raises(RuntimeError, match='TRASH_NOT_FOUND'):
        find_trash(FakeImap({}, listing=listing), cfg)


def test_nested_folder_is_no_trash_by_name():
    listing = [b'(\\HasNoChildren) "." "Kunden.Mueller.Trash"']
    with pytest.raises(RuntimeError, match='TRASH_NOT_FOUND'):
        find_trash(FakeImap({}, listing=listing), {'drafts_folder': 'Drafts'})


def test_lost_mail_fails_readback():
    imap = FakeImap(_boxes({'1': _raw('<a@h>')}), move_drops=True)
    with pytest.raises(RuntimeError, match='TRASH_READBACK_MISMATCH'):
        purge_archive(['JOEL'], {'JOEL': Client(imap)}, apply=True)


def test_counts_foreign_senders_and_missing_lead_ids_without_recipient_data(capsys):
    imap = FakeImap(_boxes({'1': _raw('<a@h>', 'geheim@kunde.de', sender='fremd@x.de', lead=None)}))
    result = purge_archive(['JORDI'], {'JORDI': Client(imap)}, apply=False)
    res = result['per_owner']['JORDI']
    assert res['foreign_sender'] == 1 and res['without_lead_id'] == 1
    assert 'geheim@kunde.de' not in str(result) and '<a@h>' not in str(result)


def test_module_contains_no_delete_commands():
    from pathlib import Path
    import archive_purge
    source = Path(archive_purge.__file__).read_text(encoding='utf-8')
    code = re.sub(r'""".*?"""', '', source, flags=re.S)
    assert not re.search(r'expunge|\\\\Deleted|\.store\(|\.delete\(', code, re.I)
