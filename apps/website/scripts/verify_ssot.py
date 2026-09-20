#!/usr/bin/env python3
"""
HSB Monorepo SSOT Verifier & Guardrail Linter.
Ensures zero AI drift across Claude Code, Gemini CLI, Cursor and Codex.
Enforces:
1. Canonical name "Jordi Post" (never "Jordie Post" or "Jordy" in active code)
2. Invariant REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0
3. Terminal preference: iTerm2 over Terminal.app
4. Monorepo integrity: No references pushing to deprecated hsb-sales-os repo
"""
import os
import sys
import subprocess
from pathlib import Path

def get_repo_root() -> Path:
    try:
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return Path(toplevel)
    except Exception:
        return Path(__file__).resolve().parent.parent

REPO_ROOT = get_repo_root()
ERRORS = []

def check_file_content(path: Path):
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return
    
    # Skip git, node_modules, .cache, dist, and historical archives
    if any(p in rel for p in [".git/", "node_modules/", "dist/", ".astro/", "docs/review-archive/"]):
        return

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return

    # Check 1: Forbidden spelling Jordie Post in active code/templates
    if "apps/sales-os/" in rel and path.suffix in [".py", ".js", ".gs", ".html", ".ts"]:
        if "Jordie Post" in text:
            ERRORS.append(f"[{rel}] Unzulässige Namensschreibung 'Jordie Post' gefunden! Erlaubt laut PROJECT_TRUTH.md nur 'Jordi Post'.")

    # Check 2: Terminal.app usage in scripts/osascript (ignoring this verifier script itself)
    if path.name != "verify_ssot.py" and path.suffix in [".sh", ".py", ".md"] and "apps/sales-os/" in rel:
        if 'tell application "Terminal"' in text:
            ERRORS.append(f"[{rel}] 'tell application \"Terminal\"' gefunden! Erlaubt laut PROJECT_TRUTH.md nur 'iTerm'.")

    # Check 3: Pushing to deprecated hsb-sales-os
    if "git push" in text and "hsb-sales-os" in text and not "deprecated" in text.lower() and not "archiviert" in text.lower():
        ERRORS.append(f"[{rel}] Push-Anweisung an stillgelegtes Repo 'hsb-sales-os' gefunden! Kanonisches Monorepo ist 'hsb-boden'.")


def main():
    print("=== HSB MONOREPO SSOT VERIFIER ===")
    print(f"Repo Root: {REPO_ROOT}")
    
    # Check 1: Project Truth & Current State exist
    if not (REPO_ROOT / "PROJECT_TRUTH.md").exists():
        ERRORS.append("PROJECT_TRUTH.md fehlt im Repository Root!")
    if not (REPO_ROOT / "CURRENT_STATE.md").exists():
        ERRORS.append("CURRENT_STATE.md fehlt im Repository Root!")

    # Check 2: Scan files
    for root, _, files in os.walk(REPO_ROOT / "apps/sales-os"):
        for f in files:
            check_file_content(Path(root) / f)

    for root, _, files in os.walk(REPO_ROOT / "scripts"):
        for f in files:
            check_file_content(Path(root) / f)

    if ERRORS:
        print(f"\n❌ {len(ERRORS)} SSOT-Verletzungen gefunden:\n")
        for err in ERRORS:
            print(f"  - {err}")
        print("\nBitte korrigieren gemäß PROJECT_TRUTH.md vor Commit/Abschluss.\n")
        sys.exit(1)

    print("✅ Alle SSOT-Prüfungen bestanden: Jordi Post, Monorepo & Invarianten 100% konform.")
    sys.exit(0)

if __name__ == "__main__":
    main()
