"""Versandsperre: Inhaber-Kennung statt offener Verbindung; fremde oder laufende Sperren bleiben unangetastet."""
from types import SimpleNamespace

import pytest

from outbound_safety import LOCK_FOLDER, STALE_LOCK_MIN_AGE_MIN, _lock_marker, mailbox_dispatch_lock, release_stale_lock

NOW = 1_800_000_000


class Server:
    """Gemeinsamer Postfachzustand; jede Anmeldung ist eine eigene Sitzung, die der Server trennen kann."""

    def __init__(self, validity=NOW - 6 * 3600, logout_fails=False):
        self.folders, self.validity, self.logout_fails, self.sessions = {}, validity, logout_fails, []

    def session(self):
        s = Session(self)
        self.sessions.append(s)
        return s


class Session:
    def __init__(self, server):
        self.server, self.dead, self.selected = server, False, None

    def _alive(self):
        if self.dead:
            raise ConnectionResetError(104, 'Connection reset by peer')

    def create(self, folder):
        self._alive()
        if folder in self.server.folders:
            return 'NO', []
        self.server.folders[folder] = []
        return 'OK', []

    def append(self, folder, flags, date, raw):
        self._alive()
        self.server.folders[folder].append(raw)
        return 'OK', []

    def select(self, folder, readonly=True):
        self._alive()
        if folder not in self.server.folders:
            return 'NO', []
        self.selected = folder
        return 'OK', [b'1']

    def response(self, key):
        return key, [str(self.server.validity).encode()]

    def uid(self, verb, *args):
        self._alive()
        box = self.server.folders[self.selected]
        if verb == 'search':
            return 'OK', [' '.join(str(i + 1) for i in range(len(box))).encode()]
        return 'OK', [(b'h', box[int(args[0]) - 1])]

    def close(self):
        self._alive()
        self.selected = None

    def delete(self, folder):
        self._alive()
        self.server.folders.pop(folder, None)
        return 'OK', []

    def logout(self):
        if self.server.logout_fails:
            raise ConnectionResetError(104, 'Connection reset by peer')


def client(server):
    return SimpleNamespace(_get_imap=server.session)


def crm(statuses=('',)):
    rows = [['Lead-ID', 'Send_Status']] + [[f'L{i}', s] for i, s in enumerate(statuses)]
    values = SimpleNamespace(get=lambda **kw: SimpleNamespace(execute=lambda: {'values': rows}))
    return SimpleNamespace(spreadsheets=lambda: SimpleNamespace(values=lambda: values))


def test_release_survives_idle_connection_killed_by_server():
    # Läufe 04.11.2026: 100 Entwürfe fertig, dann 'Connection reset by peer' beim Lösen, Sperre blieb stehen.
    server = Server()
    with mailbox_dispatch_lock(client(server)):
        for s in server.sessions:
            s.dead = True
    assert LOCK_FOLDER not in server.folders


def test_release_retries_on_reset_and_reports_if_it_stays_broken():
    server = Server()
    broken = []

    def connect():
        if broken:
            raise ConnectionResetError(104, 'reset')
        return server.session()
    with pytest.raises(RuntimeError, match='RELEASE_UNVERIFIED'):
        with mailbox_dispatch_lock(SimpleNamespace(_get_imap=connect)):
            broken.append(1)


@pytest.mark.parametrize('release_on_error,kept', [(False, True), (True, False)])
def test_lock_kept_only_for_send_errors(release_on_error, kept):
    server = Server(logout_fails=True)
    with pytest.raises(RuntimeError, match='boom'):
        with mailbox_dispatch_lock(client(server), release_on_error=release_on_error):
            raise RuntimeError('boom')
    assert (LOCK_FOLDER in server.folders) is kept


def test_lock_released_even_if_logout_resets():
    server = Server(logout_fails=True)
    with mailbox_dispatch_lock(client(server)):
        pass
    assert LOCK_FOLDER not in server.folders


def test_second_holder_is_blocked_while_lock_is_held():
    server = Server()
    with mailbox_dispatch_lock(client(server)):
        with pytest.raises(RuntimeError, match='DISPATCH_LOCK_EXISTS'):
            with mailbox_dispatch_lock(client(server)):
                pass


def test_old_holder_never_deletes_a_foreign_lock():
    # Codex-Review #524: Nach fremder Freigabe darf der alte Inhaber die neue Sperre nicht löschen.
    server = Server()
    with pytest.raises(RuntimeError, match='OWNERSHIP_LOST'):
        with mailbox_dispatch_lock(client(server)):
            server.folders[LOCK_FOLDER] = [_lock_marker('fremd')]
    assert LOCK_FOLDER in server.folders


def test_sender_notices_lost_lock_before_next_send():
    server = Server()
    with pytest.raises(RuntimeError, match='OWNERSHIP_LOST'):
        with mailbox_dispatch_lock(client(server), release_on_error=True) as lock:
            lock.assert_held()
            server.folders.pop(LOCK_FOLDER)
            lock.assert_held()


def _held_by(server, run, started, monkeypatch):
    if run == 'local':
        monkeypatch.delenv('GITHUB_RUN_ID', raising=False)
    else:
        workflow, rest = run.split('#')
        monkeypatch.setenv('GITHUB_WORKFLOW', workflow)
        monkeypatch.setenv('GITHUB_RUN_ID', rest.split('/')[0])
        monkeypatch.setenv('GITHUB_RUN_ATTEMPT', rest.split('/')[1])
    server.folders[LOCK_FOLDER] = [_lock_marker('t', now=lambda: started)]


def test_active_mac_sender_keeps_lock_although_nothing_is_sending(monkeypatch):
    # Codex-Review #524 [high]: Zwischen zwei Empfängern steht kein Lead auf SENDING; das beweist kein Ende.
    server = Server()
    _held_by(server, 'local', NOW - 30 * 60, monkeypatch)
    monkeypatch.setenv('GITHUB_WORKFLOW', 'Sales OS')
    monkeypatch.setenv('GITHUB_RUN_ID', '200')
    with pytest.raises(RuntimeError, match='STALE_LOCK_TOO_YOUNG'):
        release_stale_lock(crm(), client(server), 's', apply=True, now=lambda: NOW)
    assert LOCK_FOLDER in server.folders


def test_stale_lock_age_cannot_be_overridden_from_environment():
    import inspect
    import outbound_safety
    assert STALE_LOCK_MIN_AGE_MIN >= 240 and 'HSB_STALE_LOCK' not in inspect.getsource(outbound_safety)


def test_finished_github_run_releases_immediately_because_workflow_runs_are_serialized(monkeypatch):
    server = Server()
    _held_by(server, 'Sales OS#100/1', NOW - 5 * 60, monkeypatch)
    monkeypatch.setenv('GITHUB_RUN_ID', '200')
    assert release_stale_lock(crm(), client(server), 's', apply=True, now=lambda: NOW)['reason'] == 'OWNER_RUN_FINISHED'
    assert LOCK_FOLDER not in server.folders


def test_other_workflow_is_no_proof_of_end(monkeypatch):
    server = Server()
    _held_by(server, 'Anderer Workflow#100/1', NOW - 5 * 60, monkeypatch)
    monkeypatch.setenv('GITHUB_WORKFLOW', 'Sales OS')
    monkeypatch.setenv('GITHUB_RUN_ID', '200')
    with pytest.raises(RuntimeError, match='STALE_LOCK_TOO_YOUNG'):
        release_stale_lock(crm(), client(server), 's', apply=True, now=lambda: NOW)
    assert LOCK_FOLDER in server.folders


def test_old_lock_without_owner_marker_needs_full_age(monkeypatch):
    monkeypatch.delenv('GITHUB_RUN_ID', raising=False)
    young = Server(validity=NOW - 60 * 60)
    young.folders[LOCK_FOLDER] = []
    with pytest.raises(RuntimeError, match='STALE_LOCK_TOO_YOUNG'):
        release_stale_lock(crm(), client(young), 's', apply=True, now=lambda: NOW)
    old = Server(validity=NOW - (STALE_LOCK_MIN_AGE_MIN + 5) * 60)
    old.folders[LOCK_FOLDER] = []
    assert release_stale_lock(crm(), client(old), 's', apply=True, now=lambda: NOW)['reason'] == 'OLDER_THAN_ANY_RUN'


@pytest.mark.parametrize('validity', [0, NOW + 600])
def test_undatable_lock_is_never_released(validity, monkeypatch):
    monkeypatch.delenv('GITHUB_RUN_ID', raising=False)
    server = Server(validity=validity)
    server.folders[LOCK_FOLDER] = []
    with pytest.raises(RuntimeError, match='STALE_LOCK_AGE_UNKNOWN'):
        release_stale_lock(crm(), client(server), 's', apply=True, now=lambda: NOW)
    assert LOCK_FOLDER in server.folders


def test_uncertain_send_keeps_lock_even_for_finished_run(monkeypatch):
    server = Server()
    _held_by(server, 'Sales OS#100/1', NOW - 5 * 60, monkeypatch)
    monkeypatch.setenv('GITHUB_RUN_ID', '200')
    with pytest.raises(RuntimeError, match='STALE_LOCK_KEPT_SEND_UNCERTAIN:1'):
        release_stale_lock(crm(['SENDING', 'sent']), client(server), 's', apply=True, now=lambda: NOW)
    assert LOCK_FOLDER in server.folders


def test_no_lock_is_a_clean_noop():
    assert release_stale_lock(crm(), client(Server()), 's', apply=True, now=lambda: NOW) == {'lock': 'NONE', 'released': False}
