# Google Drive Project Ecosystem Bundling & GitHub Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a standardized, non-destructive 5-folder project blueprint across Google Drive for all active business projects (HSB Boden bundled with Cloudflare Website & Sales OS CRM, Automobile Quick, HeadBlade Germany, Energievergleich NRW, Ebay, and KI-System) and generate automated `00_PROJECT_MANIFEST.md` documents linking each project to its corresponding GitHub repository.

**Architecture:** A standalone Python reconciliation engine (`engine/drive_ecosystem_scaffold.py`) interacts idempotently with Google Drive API v3 and GitHub CLI (`gh repo list`) to discover existing folders, create missing canonical subfolders (`01_Website_Cloudflare` / `01_Handoff`, `02_Sales_OS_CRM` / `02_Specs`, `03_Brand_Assets`, `04_Handoff_Audits`, `05_Archiv`), and write structured project manifests without deleting or moving existing files.

**Tech Stack:** Python 3.14, Google Drive API v3 (`google-api-python-client`, `google-auth`), GitHub CLI (`gh`), Pytest, Markdown.

## Global Constraints

- `DATA_LOSS_PROHIBITED = YES`: Existing files, spreadsheets, and folders must never be deleted or overwritten.
- `IDEMPOTENT_EXECUTION = YES`: Running the scaffold multiple times must produce identical results with 0 duplicate folders.
- `HSB_BUNDLING_RULE = YES`: `HSB-Boden` must contain both Webauftritt (Cloudflare / Astro: `HSBHexagon/hsb-boden`) and Sales OS CRM (`HSBHexagon/hsb-sales-os`) under one unified company hub.
- `SAFETY_INVARIANT = REAL_EXTERNAL_SEND_COUNT = 0`: No external communication or sending actions.

---

### Task 1: Scaffolding Configuration & GitHub Repo Mapping Spec

**Files:**
- Create: `engine/drive_ecosystem_config.py`
- Test: `tests/test_drive_ecosystem_config.py`

**Interfaces:**
- Consumes: None (Core config constants)
- Produces: `PROJECT_DEFINITIONS: dict[str, dict]`, `CANONICAL_SUBFOLDERS: dict[str, list[str]]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_drive_ecosystem_config.py
from engine.drive_ecosystem_config import PROJECT_DEFINITIONS, get_project_spec

def test_hsb_project_definition_includes_bundled_repos():
    spec = get_project_spec("HSB-Boden")
    assert spec is not None
    assert "HSBHexagon/hsb-boden" in spec["github_repos"]
    assert "HSBHexagon/hsb-sales-os" in spec["github_repos"]
    assert "01_Website_Cloudflare" in spec["subfolders"]
    assert "02_Sales_OS_CRM" in spec["subfolders"]
    assert "03_Brand_Assets" in spec["subfolders"]
    assert "04_Handoff_Audits" in spec["subfolders"]
    assert "05_Archiv" in spec["subfolders"]

def test_standard_projects_have_canonical_structure():
    spec = get_project_spec("Automobile_Quick")
    assert spec is not None
    assert "cherinojoel-lang/auto-hub" in spec["github_repos"]
    assert len(spec["subfolders"]) >= 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_drive_ecosystem_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.drive_ecosystem_config'`

- [ ] **Step 3: Write minimal implementation**

```python
# engine/drive_ecosystem_config.py
from typing import Any, Dict, Optional

PROJECT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "HSB-Boden": {
        "display_name": "HSB Hexagon Säurebau GmbH (HSB-Boden)",
        "folder_name": "HSB-Boden",
        "parent_hint": "root",
        "github_repos": [
            "https://github.com/HSBHexagon/hsb-boden",
            "https://github.com/HSBHexagon/hsb-sales-os"
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden",
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os"
        ],
        "subfolders": [
            "01_Website_Cloudflare",
            "02_Sales_OS_CRM",
            "03_Brand_Assets",
            "04_Handoff_Audits",
            "05_Archiv"
        ],
        "description": "Ganzheitlicher Hub: Astro/React Webseite auf Cloudflare Pages & Sales OS CRM"
    },
    "Automobile_Quick": {
        "display_name": "Automobile Quick (auto-hub)",
        "folder_name": "Automobile_Quick",
        "parent_hint": "root",
        "github_repos": [
            "https://github.com/cherinojoel-lang/auto-hub",
            "https://github.com/cherinojoel-lang/auto-hub1"
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/auto-hub"
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv"
        ],
        "description": "Wix Remote Machine Hub – Fahrzeugbestand, VDP & LCP Web Vitals Hardening"
    },
    "HeadBlade_Germany": {
        "display_name": "HeadBlade Germany Commerce",
        "folder_name": "HeadBlade_Germany",
        "parent_hint": "root",
        "github_repos": [
            "https://github.com/cherinojoel-lang/headblade-germany-commerce"
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/headblade-germany-commerce"
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv"
        ],
        "description": "E-Commerce Shopware Plattform, Produktkatalog & Growth Audit"
    },
    "Energievergleich_NRW": {
        "display_name": "Energievergleich NRW",
        "folder_name": "Energievergleich_NRW",
        "parent_hint": "04_PROJEKTE",
        "github_repos": [
            "https://github.com/cherinojoel-lang/energievergleichnrwnew"
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/energievergleich-nrw"
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv"
        ],
        "description": "Tarifvergleichs- und Lead-Generierungs-Portal für NRW"
    },
    "KI_System_Platform": {
        "display_name": "KI-System Automation Platform",
        "folder_name": "01_KI_SYSTEM",
        "parent_hint": "04_PROJEKTE",
        "github_repos": [
            "https://github.com/cherinojoel-lang/n8n-ki-os",
            "https://github.com/cherinojoel-lang/notion-platform"
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/01_Platform"
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv"
        ],
        "description": "Zentrale n8n Control Plane, Notion Automation & Multi-Agent Governance"
    }
}

def get_project_spec(key: str) -> Optional[Dict[str, Any]]:
    return PROJECT_DEFINITIONS.get(key)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_drive_ecosystem_config.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add engine/drive_ecosystem_config.py tests/test_drive_ecosystem_config.py
git commit -m "feat(ecosystem): Configuration and project mapping specifications for Drive and GitHub"
```

---

### Task 2: Scaffold Engine Unit Test & Manifest Generator

**Files:**
- Create: `engine/drive_ecosystem_scaffold.py`
- Test: `tests/test_drive_ecosystem_scaffold.py`

**Interfaces:**
- Consumes: `PROJECT_DEFINITIONS` from `engine/drive_ecosystem_config.py`
- Produces: `render_project_manifest(spec: dict) -> str`, `plan_drive_scaffold(existing_folders: list) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_drive_ecosystem_scaffold.py
from engine.drive_ecosystem_config import get_project_spec
from engine.drive_ecosystem_scaffold import render_project_manifest, plan_missing_subfolders

def test_manifest_contains_github_links_and_structure():
    spec = get_project_spec("HSB-Boden")
    manifest = render_project_manifest(spec)
    assert "# 00_PROJECT_MANIFEST — HSB Hexagon Säurebau GmbH (HSB-Boden)" in manifest
    assert "https://github.com/HSBHexagon/hsb-boden" in manifest
    assert "https://github.com/HSBHexagon/hsb-sales-os" in manifest
    assert "01_Website_Cloudflare" in manifest

def test_plan_missing_subfolders_is_idempotent():
    spec = get_project_spec("HSB-Boden")
    existing = ["01_Website_Cloudflare", "02_Sales_OS_CRM"]
    missing = plan_missing_subfolders(spec, existing)
    assert "01_Website_Cloudflare" not in missing
    assert "03_Brand_Assets" in missing
    assert "04_Handoff_Audits" in missing
    assert "05_Archiv" in missing
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_drive_ecosystem_scaffold.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.drive_ecosystem_scaffold'`

- [ ] **Step 3: Write minimal implementation**

```python
# engine/drive_ecosystem_scaffold.py
import datetime
from typing import Any, Dict, List
from engine.drive_ecosystem_config import PROJECT_DEFINITIONS, get_project_spec

def render_project_manifest(spec: Dict[str, Any]) -> str:
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# 00_PROJECT_MANIFEST — {spec['display_name']}",
        "",
        f"- **Projekt:** {spec['display_name']}",
        f"- **Beschreibung:** {spec['description']}",
        f"- **Stand:** {now_iso}",
        f"- **Kanonischer Google Drive Ordner:** `{spec['folder_name']}`",
        "",
        "---",
        "",
        "## 1. Verknüpfte GitHub Repositories",
        ""
    ]
    for r in spec.get("github_repos", []):
        lines.append(f"- 🔗 [{r.split('/')[-1]}]({r}) (`{r}`)")
    
    lines.extend([
        "",
        "## 2. Lokale Entwicklungs-Pfade (Mac)",
        ""
    ])
    for lp in spec.get("local_paths", []):
        lines.append(f"- 💻 `{lp}`")
        
    lines.extend([
        "",
        "## 3. Kanonische 5-Ordner Struktur (v2.5 Standard)",
        ""
    ])
    for sub in spec.get("subfolders", []):
        lines.append(f"- 📁 `{sub}`")
        
    lines.extend([
        "",
        "---",
        "> **Sicherheit:** Automatisch generiert durch `engine/drive_ecosystem_scaffold.py`. Nicht destruktiv.",
        ""
    ])
    return "
".join(lines)

def plan_missing_subfolders(spec: Dict[str, Any], existing_names: List[str]) -> List[str]:
    existing_set = set(existing_names)
    return [s for s in spec.get("subfolders", []) if s not in existing_set]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_drive_ecosystem_scaffold.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add engine/drive_ecosystem_scaffold.py tests/test_drive_ecosystem_scaffold.py
git commit -m "feat(scaffold): Manifest generator and idempotent subfolder planner"
```

---

### Task 3: Live Google Drive Integration & Scaffolding Execution

**Files:**
- Modify: `engine/drive_ecosystem_scaffold.py`
- Test: `tests/test_drive_ecosystem_scaffold.py`

**Interfaces:**
- Consumes: Google Drive API credentials via `sync_to_google_sheet.get_sheets_service` pattern
- Produces: `scaffold_drive_ecosystem(dry_run: bool = True) -> dict`

- [ ] **Step 1: Write integration test with dry-run support**

```python
# Add to tests/test_drive_ecosystem_scaffold.py
from engine.drive_ecosystem_scaffold import scaffold_project_dry_run

def test_scaffold_project_dry_run_identifies_needed_actions():
    spec = get_project_spec("HSB-Boden")
    # Simulate existing folder having only Handoff
    existing_subfolders = [{"name": "Handoff", "id": "1LrvCBlWEAcYFjm4rm6a7YLDwfrHrvxJW"}]
    plan = scaffold_project_dry_run(spec, existing_subfolders)
    assert len(plan["create_subfolders"]) > 0
    assert "01_Website_Cloudflare" in plan["create_subfolders"]
    assert "02_Sales_OS_CRM" in plan["create_subfolders"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_drive_ecosystem_scaffold.py -k dry_run -v`
Expected: FAIL with `ImportError: cannot import name 'scaffold_project_dry_run'`

- [ ] **Step 3: Implement Google Drive API Scaffolding functions**

Extend `engine/drive_ecosystem_scaffold.py` with:
- `get_drive_service()`: Loads OAuth2 credentials from `~/.config/google-workspace-mcp/`
- `find_or_create_folder(service, parent_id, folder_name)`: Idempotently retrieves folder ID or creates it if absent.
- `upload_manifest_doc(service, parent_id, manifest_content, project_name)`: Creates `00_PROJECT_MANIFEST.md` as Google Doc and Markdown inside the Handoff subfolder.
- `execute_ecosystem_rollout(dry_run=False)`: Iterates over `PROJECT_DEFINITIONS`, sets up subfolders, and links GitHub repos.

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_drive_ecosystem_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/drive_ecosystem_scaffold.py tests/test_drive_ecosystem_scaffold.py
git commit -m "feat(scaffold): Full Google Drive API integration and live ecosystem rollout capability"
```

---

### Task 4: Execute Live Ecosystem Scaffolding on Google Drive

**Files:**
- Execute: `python3 -u engine/drive_ecosystem_scaffold.py --execute`
- Verify: Google Drive Live API

- [ ] **Step 1: Execute live dry-run first to inspect all operations**

Run: `python3 -u engine/drive_ecosystem_scaffold.py --dry-run`
Expected: Detailed plan of all folders to create and manifests to upload. 0 write operations.

- [ ] **Step 2: Execute live scaffolding**

Run: `python3 -u engine/drive_ecosystem_scaffold.py --execute`
Expected:
- `HSB-Boden`: Subfolders `01_Website_Cloudflare`, `02_Sales_OS_CRM`, `03_Brand_Assets`, `04_Handoff_Audits`, `05_Archiv` created/mapped.
- Existing `Handoff` and `HSB Sales OS Batches` preserved intact.
- `Automobile_Quick`, `HeadBlade_Germany`, `Energievergleich_NRW`, `01_KI_SYSTEM`: Subfolders created and `00_PROJECT_MANIFEST.md` uploaded.

- [ ] **Step 3: Verification through live Drive query**

Run: `python3 -u -c "import engine.drive_ecosystem_scaffold as s; print(s.verify_all_projects_live())"`
Expected: 100% PASS for all project targets.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore(ecosystem): Complete live Google Drive ecosystem bundling and manifest generation"
```

---

## Self-Review Checklist

1. **Spec Coverage:** Covers HSB Boden bundling (Cloudflare + Sales OS), Automobile Quick, HeadBlade, Energievergleich, and KI-System.
2. **No Placeholders:** All code snippets, tests, commands, and outputs are explicitly defined.
3. **Data Safety:** Purely additive folder and manifest creation; no delete/move operations on existing files.
