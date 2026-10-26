from pathlib import Path
from email.message import EmailMessage
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))

@pytest.mark.parametrize('reply,attachment,blocked',[
    (None,False,False),
    ('Joel Cherino Diaz <j-cherino@hsb-boden.com>',False,False),
    ('j-cherino@hsb-boden.de',False,True),
    ('j-post@hsb-boden.com',False,True),
    ('j-cherino@hsb-boden.com',True,True)])
def test_current_and_fully_reconciled_same_from_variants(reply,attachment,blocked):
    from sales_reconciliation import has_unreviewed_legacy_variant
    msg=EmailMessage()
    msg['From']='j-cherino@hsb-boden.com'
    if reply:msg['Reply-To']=reply
    msg.set_content('Example GmbH')
    if attachment:msg.add_attachment(b'old',maintype='application',subtype='pdf',filename='old.pdf')
    assert has_unreviewed_legacy_variant(msg,'JOEL') is blocked
