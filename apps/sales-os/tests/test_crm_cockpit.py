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
