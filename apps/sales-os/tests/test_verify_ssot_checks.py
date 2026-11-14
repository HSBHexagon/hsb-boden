"""Die SSOT-Prüfungen müssen bei echten Abweichungen anschlagen, nicht nur grün melden."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
_script_path = REPO / 'scripts' / 'verify_ssot.py'
if not _script_path.exists():
    _script_path = REPO / 'apps' / 'website' / 'scripts' / 'verify_ssot.py'
_spec = importlib.util.spec_from_file_location('verify_ssot', _script_path)
verify_ssot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_ssot)


@pytest.mark.parametrize('path', ['/', '/reparatur/', '/reparatur', '/leistungen/boden-reparatur-instandsetzung/',
                                  '/abmelden', '/impressum/', '/datenschutz/', '/brand/hsb-boden-logo.png',
                                  '/flyer', '/r/abc123'])
def test_served_paths_resolve(path):
    assert verify_ssot.site_path_exists(REPO, path), path


@pytest.mark.parametrize('path', ['/flyer/HSB-Flyer-Joel-Cherino_FINAL.pdf', '/gibt-es-nicht/',
                                  '/leistungen/erfundene-leistung/'])
def test_unserved_paths_fail(path):
    assert not verify_ssot.site_path_exists(REPO, path), path


def _fake_repo(tmp_path, truth_hash=None, code=''):
    asset = tmp_path / 'apps/sales-os/assets/canonical/M.pdf'
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b'%PDF-master')
    digest = truth_hash or hashlib.sha256(b'%PDF-master').hexdigest()
    (tmp_path / 'PROJECT_TRUTH.md').write_text(
        f'| `apps/sales-os/assets/canonical/M.pdf` | `{digest}` |\n', encoding='utf-8')
    engine = tmp_path / 'apps/sales-os/engine'
    engine.mkdir(parents=True)
    (engine / 'mail.py').write_text(code, encoding='utf-8')
    (tmp_path / 'apps/sales-os/apps_script').mkdir(parents=True)
    pub = tmp_path / 'apps/website/public'
    pub.mkdir(parents=True)
    (pub / '_redirects').write_text('/reparatur/ /leistungen/x/ 302\n', encoding='utf-8')
    (tmp_path / 'apps/website/src/pages').mkdir(parents=True)
    (tmp_path / 'apps/website/src/data').mkdir(parents=True)
    (tmp_path / 'apps/website/functions').mkdir(parents=True)
    return tmp_path


def test_hash_check_passes_and_detects_mismatch(tmp_path):
    assert verify_ssot.check_asset_hashes(_fake_repo(tmp_path / 'ok')) == []
    errors = verify_ssot.check_asset_hashes(_fake_repo(tmp_path / 'bad', truth_hash='0' * 64))
    assert len(errors) == 1 and 'weicht' in errors[0]


def test_hash_check_requires_asset_section(tmp_path):
    repo = _fake_repo(tmp_path)
    (repo / 'PROJECT_TRUTH.md').write_text('keine Tabelle', encoding='utf-8')
    assert verify_ssot.check_asset_hashes(repo)


def test_personal_attachment_name_is_rejected(tmp_path):
    repo = _fake_repo(tmp_path, code='attachment_name = "HSB-Flyer-Joel-Cherino_FINAL.pdf"\n'
                                      'ok_name = {"attachment_name": "HSB-HEXAGON-Industrieboeden-Flyer.pdf"}\n')
    errors = verify_ssot.check_attachment_names(repo)
    assert len(errors) == 1 and 'HSB-Flyer-Joel-Cherino_FINAL.pdf' in errors[0]


def test_dead_url_in_mail_code_is_rejected(tmp_path):
    repo = _fake_repo(tmp_path, code='A = "https://www.hsb-boden.de/flyer/HSB-Flyer-Joel-Cherino_FINAL.pdf"\n'
                                      'B = "https://www.hsb-boden.de/reparatur/"\n')
    errors = verify_ssot.check_mail_urls(repo)
    assert len(errors) == 1 and '/flyer/HSB-Flyer-Joel-Cherino_FINAL.pdf' in errors[0]


def test_real_repository_passes_all_static_checks():
    assert verify_ssot.check_asset_hashes(REPO) == []
    assert verify_ssot.check_attachment_names(REPO) == []
    assert verify_ssot.check_mail_urls(REPO) == []
