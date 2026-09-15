import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT))

from engine.drive_ecosystem_config import PROJECT_DEFINITIONS, get_project_spec

def test_hsb_project_definition_includes_bundled_repos():
    spec = get_project_spec("HSB-Boden")
    assert spec is not None
    assert "https://github.com/HSBHexagon/hsb-boden" in spec["github_repos"]
    assert "https://github.com/HSBHexagon/hsb-sales-os" in spec["github_repos"]
    assert "01_Website_Cloudflare" in spec["subfolders"]
    assert "02_Sales_OS_CRM" in spec["subfolders"]
    assert "03_Brand_Assets" in spec["subfolders"]
    assert "04_Handoff_Audits" in spec["subfolders"]
    assert "05_Archiv" in spec["subfolders"]

def test_standard_projects_have_canonical_structure():
    spec = get_project_spec("Automobile_Quick")
    assert spec is not None
    assert "https://github.com/cherinojoel-lang/auto-hub" in spec["github_repos"]
    assert len(spec["subfolders"]) >= 5

def test_all_defined_projects_have_required_fields():
    required_keys = ["display_name", "folder_name", "parent_hint", "github_repos", "local_paths", "subfolders", "description"]
    for pkey, pval in PROJECT_DEFINITIONS.items():
        for k in required_keys:
            assert k in pval, f"Missing {k} in {pkey}"
        assert len(pval["subfolders"]) >= 5, f"Less than 5 subfolders in {pkey}"
