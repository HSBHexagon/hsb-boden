from sales_reconciliation import link_health, link_payload_valid


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


def test_images_with_matching_content_type_are_valid():
    png=b'\x89PNG\r\n\x1a\n'+b'0'*100
    assert link_payload_valid(png,'image/png')
    assert link_payload_valid(b'\xff\xd8\xff\xe0'+b'0'*50,'image/jpeg')
    assert link_payload_valid(b'<?xml version="1.0"?><svg xmlns="x"></svg>','image/svg+xml; charset=utf-8')
    assert link_payload_valid(b'RIFF\x00\x00\x00\x00WEBPVP8 ','image/webp')


def test_error_pages_and_mismatched_payloads_stay_invalid():
    assert not link_payload_valid(b'<h1>Not found</h1>','text/html')
    assert not link_payload_valid(b'not an image','image/png')
    assert not link_payload_valid(b'\x89PNG\r\n\x1a\n','application/octet-stream')
    assert not link_payload_valid(b'','image/png')
