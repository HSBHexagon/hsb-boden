"""
engine/drive_ecosystem_scaffold.py
Idempotent Google Drive Ecosystem Scaffolding and Manifest Generator.
"""

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
        "",
    ]
    if spec.get("github_repos"):
        for r in spec.get("github_repos", []):
            lines.append(f"- 🔗 [{r.split('/')[-1]}]({r}) (`{r}`)")
    else:
        lines.append("- *Keine direkten GitHub Repositories zugeordnet (Operations-Projekt).*")

    lines.extend([
        "",
        "## 2. Lokale Entwicklungs-Pfade (Mac)",
        "",
    ])
    if spec.get("local_paths"):
        for lp in spec.get("local_paths", []):
            lines.append(f"- 💻 `{lp}`")
    else:
        lines.append("- *Kein lokales Git-Repository (Reine Cloud/Ops Steuerung).*")

    lines.extend([
        "",
        "## 3. Kanonische 5-Ordner Struktur (v2.5 Standard)",
        "",
    ])
    for sub in spec.get("subfolders", []):
        lines.append(f"- 📁 `{sub}`")

    lines.extend([
        "",
        "---",
        "> **Sicherheit:** Automatisch generiert durch `engine/drive_ecosystem_scaffold.py`. Nicht destruktiv.",
        "",
    ])
    return "\n".join(lines)


def plan_missing_subfolders(spec: Dict[str, Any], existing_names: List[str]) -> List[str]:
    existing_set = set(existing_names)
    return [s for s in spec.get("subfolders", []) if s not in existing_set]
