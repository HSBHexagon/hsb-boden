import sys
import pathlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine" / "operator_layer"))
from crm_dashboard import dashboard_rows, formatting_requests


def test_bounce_formula_reads_bounce_status_column():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert "Bounces" in rows
    f_all = rows["Bounces"][1]
    f_jordi = rows["Bounces"][2]
    f_joel = rows["Bounces"][3]
    assert "ALL_LEADS!AQ2:AQ" in f_all
    assert "hard_bounce" in f_all
    assert "bounce_review" in f_all
    assert "BE2:BE" not in f_all
    assert "ALL_LEADS!AQ2:AQ" in f_jordi and "Jordi" in f_jordi
    assert "ALL_LEADS!AQ2:AQ" in f_joel and "Joel" in f_joel


def test_v2_rows_count_template_ids():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert "v2 versendet Produktion" in rows
    assert "v2 versendet Architekten" in rows
    assert 'ALL_LEADS!AF2:AF; "v2-produktion*"' in rows["v2 versendet Produktion"][1]
    assert 'ALL_LEADS!AO2:AO; "sent"' in rows["v2 versendet Produktion"][1]
    assert 'ALL_LEADS!AF2:AF; "v2-architekten*"' in rows["v2 versendet Architekten"][1]
    assert 'ALL_LEADS!AO2:AO; "sent"' in rows["v2 versendet Architekten"][1]


def test_v2_reply_rows_use_reply_status():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert "v2 Antworten Produktion" in rows
    assert "v2 Antworten Architekten" in rows
    assert "Antworten gesamt" in rows
    assert 'ALL_LEADS!AR2:AR; "<>"' in rows["v2 Antworten Produktion"][1]
    assert 'ALL_LEADS!AF2:AF; "v2-produktion*"' in rows["v2 Antworten Produktion"][1]
    assert 'ALL_LEADS!AR2:AR; "<>"' in rows["v2 Antworten Architekten"][1]
    assert 'ALL_LEADS!AF2:AF; "v2-architekten*"' in rows["v2 Antworten Architekten"][1]
    assert 'ALL_LEADS!AR2:AR; "<>"' in rows["Antworten gesamt"][1]


def test_click_row_is_error_safe():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert "Klicks (echt)" in rows
    assert rows["Klicks (echt)"][1].startswith("=IFERROR(")
    assert 'CLICK_EVENTS!D2:D; "human"' in rows["Klicks (echt)"][1]


def test_com_blindspots_resolved():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert "*j-post@hsb-boden.*" in rows["Klärfälle offen"][2] or "j-post@hsb-boden.com" in rows["Klärfälle offen"][2]
    assert "*j-cherino@hsb-boden.*" in rows["Klärfälle offen"][3] or "j-cherino@hsb-boden.com" in rows["Klärfälle offen"][3]
    assert "j-cherino@hsb-boden.com" in rows["Letzter Abgleich Joel"][1]
    assert "j-post@hsb-boden.com" in rows["Letzter Abgleich Jordi"][1]


def test_existing_rows_unchanged():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert rows["Kontakte gesamt"][1] == '=COUNTA(ALL_LEADS!A2:A)'
    assert rows["Versendet"][1] == '=COUNTIF(ALL_LEADS!AO2:AO; "sent")'
    assert rows["Abgemeldet (Opt-out)"][1] == '=COUNTIF(ALL_LEADS!Y2:Y; "yes")'
    assert rows["Freigegeben, noch nicht versendet"][1] == '=COUNTIF(ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIF(ALL_LEADS!BE2:BE; "Entwurf")'
