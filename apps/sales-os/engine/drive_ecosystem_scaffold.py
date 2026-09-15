"""
engine/drive_ecosystem_scaffold.py
Idempotent Google Drive Ecosystem Scaffolding and Manifest Generator.
Standardized 5-Folder Project Architecture (v2.5) with GitHub Reconciliation.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "engine") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "engine"))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from engine.drive_ecosystem_config import PROJECT_DEFINITIONS, get_project_spec


def render_project_manifest(spec: Dict[str, Any]) -> str:
    """Renders canonical markdown manifest connecting Drive folder to GitHub & local paths."""
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
    """Identifies which canonical subfolders are missing from existing folder names."""
    existing_set = set(existing_names)
    return [s for s in spec.get("subfolders", []) if s not in existing_set]


def scaffold_project_dry_run(spec: Dict[str, Any], existing_subfolders: List[Dict[str, str]]) -> Dict[str, Any]:
    """Computes an idempotent execution plan for a single project without making API modifications."""
    existing_names = [f["name"] for f in existing_subfolders]
    missing = plan_missing_subfolders(spec, existing_names)

    # Determine manifest target folder name
    subfolders = spec.get("subfolders", [])
    manifest_target = None
    for candidate in ["04_Handoff_Audits", "01_Handoff_Audits", "01_Handoff", "Handoff"]:
        if candidate in subfolders or candidate in existing_names:
            manifest_target = candidate
            break
    if not manifest_target and subfolders:
        manifest_target = subfolders[0]

    return {
        "project_key": spec.get("folder_name"),
        "display_name": spec.get("display_name"),
        "folder_name": spec.get("folder_name"),
        "parent_hint": spec.get("parent_hint", "root"),
        "existing_subfolders": existing_names,
        "create_subfolders": missing,
        "manifest_target": manifest_target,
    }


def get_drive_service():
    """Initializes Google Drive API v3 client using stored Workspace MCP credentials."""
    with open("/Users/joelcherinodiaz/.config/google-workspace-mcp/profiles/cherinodiaz/tokens.json") as f:
        token_data = json.load(f)

    with open("/Users/joelcherinodiaz/.config/google-workspace-mcp/credentials.json") as f:
        client_data = json.load(f)

    cinfo = client_data.get("installed") or client_data.get("web")

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cinfo.get("client_id"),
        client_secret=cinfo.get("client_secret"),
        scopes=token_data.get("scope", "").split(),
    )
    return build("drive", "v3", credentials=creds)


def find_folder(service, folder_name: str, parent_id: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Searches for an un-trashed folder by name and optional parent ID."""
    q_parts = [
        "mimeType = 'application/vnd.google-apps.folder'",
        f"name = '{folder_name}'",
        "trashed = false",
    ]
    if parent_id and parent_id != "root":
        q_parts.append(f"'{parent_id}' in parents")
    q = " and ".join(q_parts)

    res = service.files().list(q=q, fields="files(id, name, parents)").execute()
    files = res.get("files", [])
    if files:
        return {"id": files[0]["id"], "name": files[0]["name"]}
    return None


def list_subfolders(service, parent_id: str) -> List[Dict[str, str]]:
    """Lists immediate un-trashed subfolders under parent_id."""
    q = f"mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    res = service.files().list(q=q, fields="files(id, name)", pageSize=100).execute()
    return [{"id": f["id"], "name": f["name"]} for f in res.get("files", [])]


def find_or_create_folder(service, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, str]:
    """Finds or idempotently creates a folder in Google Drive."""
    existing = find_folder(service, folder_name, parent_id)
    if existing:
        return existing

    body: Dict[str, Any] = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id and parent_id != "root":
        body["parents"] = [parent_id]

    created = service.files().create(body=body, fields="id, name").execute()
    return {"id": created["id"], "name": created["name"]}


def upload_manifest_doc(service, parent_id: str, manifest_content: str, display_name: str) -> Dict[str, str]:
    """Uploads or updates 00_PROJECT_MANIFEST.md inside the designated target folder."""
    q = f"name = '00_PROJECT_MANIFEST.md' and '{parent_id}' in parents and trashed = false"
    res = service.files().list(q=q, fields="files(id, name)").execute()
    files = res.get("files", [])

    media = MediaInMemoryUpload(manifest_content.encode("utf-8"), mimetype="text/markdown")
    if files:
        file_id = files[0]["id"]
        updated = service.files().update(fileId=file_id, media_body=media, fields="id, name").execute()
        return {"id": updated["id"], "status": "updated"}
    else:
        body = {
            "name": "00_PROJECT_MANIFEST.md",
            "parents": [parent_id],
            "description": f"Projekt-Manifest & GitHub Verknüpfung für {display_name}",
        }
        created = service.files().create(body=body, media_body=media, fields="id, name").execute()
        return {"id": created["id"], "status": "created"}


def execute_ecosystem_rollout(dry_run: bool = True) -> Dict[str, Any]:
    """Executes or previews the complete Google Drive project ecosystem bundling."""
    service = get_drive_service()
    results: Dict[str, Any] = {}

    for pkey, spec in PROJECT_DEFINITIONS.items():
        parent_hint = spec.get("parent_hint", "root")
        folder_name = spec["folder_name"]

        # Resolve parent ID
        parent_id: Optional[str] = None
        if parent_hint == "04_PROJEKTE":
            p_folder = find_folder(service, "04_PROJEKTE")
            if p_folder:
                parent_id = p_folder["id"]
            else:
                if not dry_run:
                    p_folder = find_or_create_folder(service, "04_PROJEKTE")
                    parent_id = p_folder["id"]

        # Find project folder
        project_folder = find_folder(service, folder_name, parent_id)
        if not project_folder and not dry_run:
            project_folder = find_or_create_folder(service, folder_name, parent_id)

        existing_subfolders: List[Dict[str, str]] = []
        if project_folder:
            existing_subfolders = list_subfolders(service, project_folder["id"])

        plan = scaffold_project_dry_run(spec, existing_subfolders)

        if dry_run:
            results[pkey] = {
                "dry_run": True,
                "project_folder_found": bool(project_folder),
                "project_folder_id": project_folder["id"] if project_folder else None,
                "plan": plan,
            }
        else:
            if not project_folder:
                raise RuntimeError(f"Could neither find nor create project folder {folder_name}")

            created_folders = []
            for missing_sub in plan["create_subfolders"]:
                created = find_or_create_folder(service, missing_sub, project_folder["id"])
                created_folders.append(created)

            # Re-fetch subfolders to get folder ID for manifest target
            refreshed_subfolders = list_subfolders(service, project_folder["id"])
            target_name = plan["manifest_target"]
            target_id = project_folder["id"]
            for sf in refreshed_subfolders:
                if sf["name"] == target_name:
                    target_id = sf["id"]
                    break

            manifest_content = render_project_manifest(spec)
            manifest_res = upload_manifest_doc(service, target_id, manifest_content, spec["display_name"])

            results[pkey] = {
                "dry_run": False,
                "project_folder_id": project_folder["id"],
                "created_subfolders": [c["name"] for c in created_folders],
                "all_subfolders": [sf["name"] for sf in refreshed_subfolders],
                "manifest": manifest_res,
                "manifest_folder_name": target_name,
            }

    return results


def verify_all_projects_live() -> Dict[str, Any]:
    """Verifies live on Google Drive that all projects, canonical subfolders, and manifests exist."""
    service = get_drive_service()
    verification: Dict[str, Any] = {"all_passed": True, "projects": {}}

    for pkey, spec in PROJECT_DEFINITIONS.items():
        parent_hint = spec.get("parent_hint", "root")
        folder_name = spec["folder_name"]

        parent_id = None
        if parent_hint == "04_PROJEKTE":
            p_folder = find_folder(service, "04_PROJEKTE")
            if p_folder:
                parent_id = p_folder["id"]

        project_folder = find_folder(service, folder_name, parent_id)
        if not project_folder:
            verification["all_passed"] = False
            verification["projects"][pkey] = {"status": "FAIL", "reason": "Project folder missing"}
            continue

        existing_subs = list_subfolders(service, project_folder["id"])
        existing_sub_names = {s["name"]: s["id"] for s in existing_subs}

        missing_subs = [s for s in spec["subfolders"] if s not in existing_sub_names]

        # Check manifest in candidate folders
        manifest_found = False
        manifest_file_id = None
        manifest_folder_found = None
        for candidate in ["04_Handoff_Audits", "01_Handoff_Audits", "01_Handoff", "Handoff"]:
            if candidate in existing_sub_names:
                cid = existing_sub_names[candidate]
                q = f"name = '00_PROJECT_MANIFEST.md' and '{cid}' in parents and trashed = false"
                res = service.files().list(q=q, fields="files(id, name)").execute()
                if res.get("files"):
                    manifest_found = True
                    manifest_file_id = res["files"][0]["id"]
                    manifest_folder_found = candidate
                    break

        status = "PASS" if (len(missing_subs) == 0 and manifest_found) else "FAIL"
        if status == "FAIL":
            verification["all_passed"] = False

        verification["projects"][pkey] = {
            "status": status,
            "project_folder_id": project_folder["id"],
            "missing_subfolders": missing_subs,
            "manifest_found": manifest_found,
            "manifest_file_id": manifest_file_id,
            "manifest_folder": manifest_folder_found,
        }

    return verification


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drive Ecosystem Scaffolding")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Preview actions without executing")
    parser.add_argument("--execute", action="store_true", help="Execute live Drive modifications")
    args = parser.parse_args()

    is_dry = not args.execute
    mode_str = "DRY-RUN (Preview)" if is_dry else "LIVE EXECUTION"
    print(f"=== HSB Google Drive Ecosystem Rollout: {mode_str} ===")
    rollout_results = execute_ecosystem_rollout(dry_run=is_dry)
    print(json.dumps(rollout_results, indent=2))
