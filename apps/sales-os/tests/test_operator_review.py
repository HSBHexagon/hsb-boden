from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
from hsb_core import check_eligibility

def approved(**changes):
    row={'Lead-ID':'L1','E-Mail':'buyer@example.invalid','Firma':'Example GmbH',
         'Verantwortlicher':'Joel Cherino Diaz','Versandfreigabe':'yes','Send_Status':'drafted',
         'Legal_Basis':'CONTRACT_APPROVED','Legal_Review_Status':'yes',
         'Legal_Review_Vermerk':'Ausdrückliche Betreiberbestätigung: Die rechtliche Prüfung nach § 7 wurde bereits geklärt.',
         'Legal_Review_At':'2026-10-26T10:00:00Z'}
    row.update(changes)
    return row

def test_recorded_manual_review_is_not_a_fabricated_optin():
    row=approved()
    assert check_eligibility(row).eligible
    assert 'Opt-in-Status' not in row
    assert 'Legal_Evidence' not in row

@pytest.mark.parametrize('changes',[
    {'Legal_Review_Vermerk':''}, {'Legal_Review_At':''},
    {'Legal_Review_Status':''}, {'Legal_Review_At':'2099-01-01T10:00:00Z'}])
def test_bare_yes_or_incomplete_review_does_not_qualify(changes):
    assert not check_eligibility(approved(**changes)).eligible

@pytest.mark.parametrize('changes',[
    {'Legal_Basis':'BLOCKED'}, {'Legal_Basis':'NO'}, {'Opt-out-Status':'yes'}, {'Suppressed':'yes'}, {'Bounce_Status':'hard_bounce'},
    {'Send_Status':'sent'}, {'Versandfreigabe':'no'}])
def test_manual_review_never_clears_individual_suppression(changes):
    assert not check_eligibility(approved(**changes)).eligible
