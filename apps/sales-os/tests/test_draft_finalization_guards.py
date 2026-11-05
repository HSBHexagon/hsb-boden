import pytest
import canonical_template_factory as ctf
from test_signature_refresh import setup, FakeImap, LEAD, run

@pytest.mark.parametrize("renderer", [ctf.render_canonical_email, ctf.render_email_v2])
@pytest.mark.parametrize("owner", ["UNKNOWN_OWNER", "", None])
def test_invalid_owner_is_rejected_before_rendering(renderer, owner):
    with pytest.raises(ValueError, match="INVALID_OWNER"):
        renderer(dict(LEAD), owner=owner)

def test_uncertain_append_stops_without_an_automatic_second_write(setup, monkeypatch):
    store, rec = setup
    writes = []
    def uncertain(self, *args):
        writes.append("APPEND")
        raise TimeoutError("acceptance unknown")
    monkeypatch.setattr(FakeImap, "append", uncertain)
    with pytest.raises(RuntimeError, match="UNCERTAIN_APPEND"):
        run(store, rec)
    assert writes == ["APPEND"]
    assert list(store["Drafts"]) == [1]
    assert not store["ARCHIV"]

def test_uncertain_move_stops_without_an_automatic_second_write(setup, monkeypatch):
    store, rec = setup
    moves = []
    original_uid = FakeImap.uid
    def uncertain(self, verb, *args):
        if verb == "move":
            moves.append("MOVE")
            raise TimeoutError("move result unknown")
        return original_uid(self, verb, *args)
    monkeypatch.setattr(FakeImap, "uid", uncertain)
    with pytest.raises(RuntimeError, match="UNCERTAIN_MOVE"):
        run(store, rec)
    assert moves == ["MOVE"]
    assert len(store["Drafts"]) == 2
    assert not store["ARCHIV"]
