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


def _img(fmt):
    from io import BytesIO
    from PIL import Image
    buf = BytesIO(); Image.new('RGB', (4, 4), 'red').save(buf, fmt); return buf.getvalue()


def test_decodable_images_in_declared_format_are_valid():
    assert link_payload_valid(_img('PNG'), 'image/png')
    assert link_payload_valid(_img('JPEG'), 'image/jpeg')
    assert link_payload_valid(_img('GIF'), 'image/gif')
    assert link_payload_valid(_img('WEBP'), 'image/webp')
    assert link_payload_valid(b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', 'image/svg+xml; charset=utf-8')


def test_error_pages_truncated_and_mismatched_payloads_stay_invalid():
    png = _img('PNG')
    assert not link_payload_valid(b'<h1>Not found</h1><!-- <svg -->', 'image/svg+xml')
    assert not link_payload_valid(b'<html><body>404</body></html>', 'image/svg+xml')
    assert not link_payload_valid(b'\x89PNG\r\n\x1a\n', 'image/png')
    assert not link_payload_valid(png[:len(png) // 2], 'image/png')
    assert not link_payload_valid(png, 'image/jpeg')
    assert not link_payload_valid(b'RIFF\x00\x00\x00\x00WEBPVP8 ', 'image/webp')
    assert not link_payload_valid(png, 'application/octet-stream')
    assert not link_payload_valid(b'<h1>Not found</h1>', 'text/html')
    assert not link_payload_valid(b'', 'image/png')


def test_utf16_entity_svg_and_truncated_multiframe_gif_rejected():
    from io import BytesIO
    from PIL import Image
    svg16 = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE s [<!ENTITY a "x">]><svg>&a;</svg>'.encode('utf-16')
    assert not link_payload_valid(svg16, 'image/svg+xml')
    frames = [Image.new('RGB', (8, 8), c) for c in ('red', 'green', 'blue')]
    buf = BytesIO(); frames[0].save(buf, 'GIF', save_all=True, append_images=frames[1:]); gif = buf.getvalue()
    assert link_payload_valid(gif, 'image/gif')
    assert not link_payload_valid(gif[:-20], 'image/gif')
