import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine" / "operator_layer"))
from crm_operator_layer import pipeline_row_tints, PIPELINE_COLORS

def test_row_tint_rules():
    reqs = pipeline_row_tints(sheet_id=123, last_row=6425, last_col=57)
    assert len(reqs) == 7
    r0 = reqs[0]["addConditionalFormatRule"]["rule"]
    assert r0["booleanRule"]["condition"]["type"] == "CUSTOM_FORMULA"
    assert r0["booleanRule"]["condition"]["values"][0]["userEnteredValue"] == '=$BE2="Abgemeldet"'
    rng = r0["ranges"][0]
    assert (rng["startColumnIndex"], rng["endColumnIndex"], rng["startRowIndex"]) == (0, 57, 1)
    assert set(PIPELINE_COLORS) == {"Abgemeldet", "Bounce", "Antwort", "Versendet", "Entwurf", "Freigegeben", "Neu"}

from crm_cockpit import cockpit_blocks, BLOCK_COLS

def test_cockpit_blocks_joel():
    b = cockpit_blocks("Joel")
    assert [x["title"] for x in b] == ["🔴 Abgemeldet", "🟡 Antworten offen", "🟠 Bounce", "🟢 Versendet (zuletzt 60)", "🔵 Heute dran (freigegeben / Entwurf)"]
    assert all("AA contains 'Joel'" in x["formula"] for x in b)
    assert "BE = 'Abgemeldet'" in b[0]["formula"]
    assert "BE = 'Versendet'" in b[3]["formula"] and "limit 60" in b[3]["formula"]
    assert BLOCK_COLS == "B, G, I, BE, AP, AR, AC"

from crm_cockpit import posteingang_values

def test_posteingang_blocks():
    v = posteingang_values()
    titles = [r[0] for r in v if r and str(r[0]).startswith(("⚠️", "📥"))]
    assert titles == ["⚠️ Klärfälle — bitte in INBOUND_EVENTS Spalte M eine Lead-ID oder „ignorieren“ eintragen", "📥 Letzte 200 Ereignisse"]
    f = [r[0] for r in v if r and str(r[0]).startswith("=IFERROR(QUERY(INBOUND_EVENTS")]
    assert "J = 'NEEDS_REVIEW'" in f[0] and "order by B desc" in f[0]
    assert "limit 200" in f[1]

from crm_dashboard import dashboard_rows

def test_dashboard_formulas():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert rows["Abgemeldet (Opt-out)"][1] == '=COUNTIF(ALL_LEADS!Y2:Y; "yes")'
    assert rows["Bounces"][1] == '=COUNTIF(ALL_LEADS!BE2:BE; "Bounce")'
    assert rows["Antworten offen"][1] == '=COUNTIFS(ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")'
    assert rows["Klärfälle offen"][1] == '=COUNTIF(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW")'
    assert rows["Versendet letzte 30 Tage"][1].startswith("=SPARKLINE(")
    assert len(dashboard_rows()) == 28
    assert rows["ERZEUGTE BATCHES (Letzte 10)"]
