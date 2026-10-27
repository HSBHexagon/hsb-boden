from sales_reconciliation import link_health


def test_unique_links_probed_once_and_no_query_sent():
    calls=[]; cache={}
    def probe(u):
        calls.append(u); return {'valid':True}
    assert link_health(['https://www.hsb-boden.de/flyer/?x=1','https://www.hsb-boden.de/flyer/?x=2'],cache,probe)==[]
    assert calls==['https://www.hsb-boden.de/flyer/']


def test_broken_and_untrusted_urls():
    calls=[]
    assert link_health(['https://www.hsb-boden.de/missing'],probe=lambda u:{'valid':False})==['LINK_BROKEN:www.hsb-boden.de/missing']
    assert link_health(['http://127.0.0.1/'],probe=lambda u:calls.append(u))
    assert calls==[]
