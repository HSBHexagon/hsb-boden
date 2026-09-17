"""Tests fuer engine/operator_layer/crm_events_migrate.py (reine Planungslogik, kein Sheet-Zugriff)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine" / "operator_layer"))
from crm_events_migrate import plan, alt_zu_neu


def test_alt_layout_wird_auf_header_gemappt():
    alt = ["APIHUB-INBOX-<1>", "2026-09-17T12:00:00Z", "OPT_OUT", "HSB-1", "JORDI", "a@b.de", "<1>", "", "PROCESSED", "Abmelden"]
    neu = alt_zu_neu(alt)
    assert neu[:10] == ["APIHUB-INBOX-<1>", "2026-09-17T12:00:00Z", "", "a@b.de", "", "<1>", "HSB-1", "OPT_OUT", "yes", "PROCESSED"]
    assert len(neu) == 12
    assert neu[10] == "Abmelden"          # Details -> Notes
    assert neu[11] == ""                  # kein In_Reply_To -> Raw_Link leer


def test_alt_layout_in_reply_to_wandert_nach_raw_link():
    alt = ["E", "t", "REPLY", "HSB-2", "", "x@y.de", "<2>", "<orig@hsb>", "PROCESSED", "AW"]
    neu = alt_zu_neu(alt)
    assert neu[8] == "no" and neu[11] == "In-Reply-To: <orig@hsb>"


def test_wiederholte_klaerfaelle_werden_markiert_nicht_geloescht():
    a = ["E1", "t1", "REPLY", "", "", "x@y.de", "<1>", "", "NEEDS_REVIEW", "s"]
    b = ["E1", "t2", "REPLY", "", "", "x@y.de", "<1>", "", "NEEDS_REVIEW", "s"]
    c = ["E2", "t3", "j@hsb.de", "x@y.de", "s", "<2>", "HSB-1", "REPLY", "no", "PROCESSED", "n", ""]
    changes = plan([a, b, c])
    idx = [i for i, _ in changes]
    assert idx == [0, 1]                       # c ist schon kanonisch und unveraendert
    assert changes[0][1][9] == "NEEDS_REVIEW"  # erste bleibt
    assert changes[1][1][9] == "DUPLICATE"     # Wiederholung markiert


def test_kanonische_wiederholung_wird_ebenfalls_markiert():
    # Wiederholung bereits im neuen Layout (Trigger nach Umstellung): nur die Markierung aendert sich.
    a = ["E9", "t1", "j@hsb.de", "x@y.de", "s", "<9>", "", "REPLY", "no", "NEEDS_REVIEW", "n", ""]
    b = ["E9", "t2", "j@hsb.de", "x@y.de", "s", "<9>", "", "REPLY", "no", "NEEDS_REVIEW", "n", ""]
    changes = plan([a, b])
    assert [i for i, _ in changes] == [1]
    assert changes[0][1] == b[:9] + ["DUPLICATE", "n", ""]


def test_terminale_wiederholung_bleibt_unangetastet():
    # Gleiche Event_ID, aber PROCESSED: kein Klaerfall, wird nicht als DUPLICATE markiert.
    a = ["E5", "t1", "j@hsb.de", "x@y.de", "s", "<5>", "HSB-1", "REPLY", "no", "PROCESSED", "n", ""]
    b = ["E5", "t2", "j@hsb.de", "x@y.de", "s", "<5>", "HSB-1", "REPLY", "no", "PROCESSED", "n", ""]
    assert plan([a, b]) == []


def test_kurze_zeilen_werden_auf_12_zellen_aufgefuellt():
    kurz = ["E7", "t", "SENT", "HSB-3", "JOEL", "z@z.de"]
    neu = alt_zu_neu(kurz)
    assert len(neu) == 12 and neu[7] == "SENT" and neu[9] == "" and neu[3] == "z@z.de"
