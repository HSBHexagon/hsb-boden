"""Regressionsschutz: Mails duerfen keine Flyer-/PDF-Links auf nicht existierende Seiten enthalten.

Hintergrund: dual_delivery_helper.py verwies auf https://www.hsb-boden.de/flyer/*_FINAL.pdf
(live HTTP 404). Der Flyer geht ausschliesslich als Anhang raus.
"""
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

SALES_OS = Path(__file__).resolve().parent.parent
REPO_ROOT = SALES_OS.parent.parent
PUBLIC_DIR = REPO_ROOT / "apps" / "website" / "public"
ENGINE = SALES_OS / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

import dual_delivery_helper  # noqa: E402

PDF_URL_RE = re.compile(r"https?://(?:www\.)?hsb-boden\.(?:de|com)(/[^\s\"'<>)\\]*?\.pdf)", re.IGNORECASE)


@pytest.mark.parametrize("owner", ["JOEL", "JORDI", "JORDIE"])
def test_flyer_delivery_is_attachment_only(owner):
    with mock.patch.object(dual_delivery_helper, "get_mx_records", return_value=[]):
        cfg = dual_delivery_helper.get_flyer_delivery_config(owner, "info@example.de")
    assert cfg["attach_physical_pdf"] is True
    assert cfg["include_cdn_link"] is False
    assert cfg["flyer_cdn_url"] is None
    assert cfg["flyer_filename"] == "HSB-HEXAGON-Industrieboeden-Flyer.pdf"


def _code_files():
    for base, patterns in ((ENGINE, ("*.py",)), (SALES_OS / "apps_script", ("*.gs",)), (SALES_OS / "deploy", ("*.gs", "*.html"))):
        for pattern in patterns:
            yield from base.glob(pattern)


def test_pdf_links_in_mail_code_point_to_published_files():
    broken = []
    for path in _code_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in PDF_URL_RE.finditer(text):
            if not (PUBLIC_DIR / m.group(1).lstrip("/")).is_file():
                broken.append(f"{path.relative_to(REPO_ROOT)}: {m.group(0)}")
    assert not broken, "PDF-Links ohne veroeffentlichte Datei in apps/website/public:\n" + "\n".join(broken)
