import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT))

from engine.drive_ecosystem_config import get_project_spec
from engine.drive_ecosystem_scaffold import (
    render_project_manifest,
    plan_missing_subfolders,
    scaffold_project_dry_run,
)


def test_manifest_contains_github_links_and_structure():
    spec = get_project_spec("HSB-Boden")
    assert spec is not None
    manifest = render_project_manifest(spec)
    assert "# 00_PROJECT_MANIFEST — HSB Hexagon Säurebau GmbH (HSB-Boden)" in manifest
    assert "https://github.com/HSBHexagon/hsb-boden" in manifest
    assert "https://github.com/HSBHexagon/hsb-sales-os" in manifest
    assert "01_Website_Cloudflare" in manifest
    assert "02_Sales_OS_CRM" in manifest
    assert "03_Brand_Assets" in manifest
    assert "04_Handoff_Audits" in manifest
    assert "05_Archiv" in manifest


def test_plan_missing_subfolders_is_idempotent():
    spec = get_project_spec("HSB-Boden")
    assert spec is not None
    existing = ["01_Website_Cloudflare", "02_Sales_OS_CRM"]
    missing = plan_missing_subfolders(spec, existing)
    assert "01_Website_Cloudflare" not in missing
    assert "02_Sales_OS_CRM" not in missing
    assert "03_Brand_Assets" in missing
    assert "04_Handoff_Audits" in missing
    assert "05_Archiv" in missing


def test_scaffold_project_dry_run_identifies_needed_actions():
    spec = get_project_spec("HSB-Boden")
    assert spec is not None
    existing_subfolders = [{"name": "Handoff", "id": "1LrvCBlWEAcYFjm4rm6a7YLDwfrHrvxJW"}]
    plan = scaffold_project_dry_run(spec, existing_subfolders)
    assert len(plan["create_subfolders"]) > 0
    assert "01_Website_Cloudflare" in plan["create_subfolders"]
    assert "02_Sales_OS_CRM" in plan["create_subfolders"]
    assert "03_Brand_Assets" in plan["create_subfolders"]
    assert "04_Handoff_Audits" in plan["create_subfolders"]
    assert "05_Archiv" in plan["create_subfolders"]
