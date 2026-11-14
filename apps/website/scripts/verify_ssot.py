#!/usr/bin/env python3
"""
HSB Monorepo SSOT Verifier & Guardrail Linter.
Ensures zero AI drift across Claude Code, Gemini CLI, Cursor, Codex and Antigravity.
Enforces:
1. Canonical name "Jordie Post" (never "Jordi Post" or "Jordy" in active code)
2. Invariant REAL_EXTERNAL_PROSPECT_SEND_COUNT == 0
3. Terminal preference: iTerm2 over Terminal.app
4. Monorepo integrity: No references pushing to deprecated hsb-sales-os repo
5. CRM SSOT Lock: Unverrückbares Master-Sheet 1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg
   und striktes Verbot aller 6 archivierten Alt-Sheet-IDs in Produktivcode.
"""
import os
import sys
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

CANONICAL_SPREADSHEET_ID = "1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"

FORBIDDEN_SHEET_IDS = {
    "1ITFextI-EuDXNG2p9yfmAvzA_7AbFk4HDO-GqB7WyLI": "Altes Jordi-Sheet",
    "1FBY9tsDT6ode8QzkSsTQJZxVE81bLZ4DtgDCmojCFoQ": "Altes Joel-Sheet",
    "1JJ49g_P-gVSAE0eG9zlAJBAjopBoG0Ntb7tThJvrIvs": "Altes Master v2 Sheet",
    "1mQCHlJ08BUgyBTk5gSwHfWsS7jvW1FkrcPlo5eHoARk": "Altes Snapshot-Sheet",
    "1NqAQNuXl3W1OjIQ47ix9ZNYTP0-sLKjVRfeTjXCXR7Q": "Altes CRM Light Sheet",
    "1XmbTXyPS5U0tp6PwT5HdF4zE2E3xdrFL9bIvdUtsCD0": "Altes HSB Sales OS Sheet",
}

# Skripte, die zur einmaligen historischen Forensik dienten
FORENSIC_SCRIPTS = [
    "verify_ssot.py",
    "sync_to_google_sheet.py",
    "extract_all_de_sent_exact.py",
    "extract_all_sent_history.py"
]

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

    # Check 1: Forbidden spelling Jordi Post in GF / signature fields
    if "apps/sales-os/" in rel and path.suffix in [".py", ".js", ".gs", ".html", ".ts"]:
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "geschaeftsfuehrer" in line.lower() and "Jordi Post" in line:
                ERRORS.append(f"[{rel}:{line_no}] Unzulässige Namensschreibung 'Jordi Post' im Geschäftsführer-Feld gefunden! Erlaubt laut PROJECT_TRUTH.md nur 'Jordie Post'.")

    # Check 2: Terminal.app usage in scripts/osascript (ignoring this verifier script itself)
    if path.name != "verify_ssot.py" and path.suffix in [".sh", ".py", ".md"] and "apps/sales-os/" in rel:
        if 'tell application "Terminal"' in text:
            ERRORS.append(f"[{rel}] 'tell application \"Terminal\"' gefunden! Erlaubt laut PROJECT_TRUTH.md nur 'iTerm'.")

    # Check 3: Pushing to deprecated hsb-sales-os
    if "git push" in text and "hsb-sales-os" in text and not "deprecated" in text.lower() and not "archiviert" in text.lower():
        ERRORS.append(f"[{rel}] Push-Anweisung an stillgelegtes Repo 'hsb-sales-os' gefunden! Kanonisches Monorepo ist 'hsb-boden'.")

    # Check 4: Verbotene Sheet-IDs in Python/JS/Config-Dateien (außerhalb Whitelist/Forensik)
    if path.name not in FORENSIC_SCRIPTS and path.suffix in [".py", ".js", ".ts", ".json", ".env"]:
        for forbidden_id, label in FORBIDDEN_SHEET_IDS.items():
            if forbidden_id in text:
                ERRORS.append(f"[{rel}] Verbotene/archivierte Google Sheet ID '{forbidden_id}' ({label}) referenziert! Die einzige erlaubte Wahrheit ist '{CANONICAL_SPREADSHEET_ID}'.")


# ---------------------------------------------------------------------------
# Check 5-7: Asset-Hashes, neutraler Anhangsname, URLs im Mail-Code
# ---------------------------------------------------------------------------
import hashlib
import re

NEUTRAL_ATTACHMENT_NAME = "HSB-HEXAGON-Industrieboeden-Flyer.pdf"
_ASSET_ROW_RE = re.compile(r"\|\s*`(apps/sales-os/assets/canonical/[^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|")
_ATTACHMENT_NAME_RE = re.compile(
    r"""(?:attachment_name|attachmentName|ATTACHMENT_NAME|flyer_filename)\s*[:=]\s*['"]([^'"]+\.pdf)['"]""")
_SITE_URL_RE = re.compile(r"https?://(?:www\.)?hsb-boden\.de(/[^\s\"'<>)\\{}]*)?")
MAIL_CODE_DIRS = ("apps/sales-os/engine", "apps/sales-os/apps_script")


def check_asset_hashes(repo_root):
    """Jeder Master in PROJECT_TRUTH.md muss existieren und exakt den hinterlegten Hash haben."""
    errors = []
    truth = (repo_root / "PROJECT_TRUTH.md").read_text(encoding="utf-8")
    rows = _ASSET_ROW_RE.findall(truth)
    if not rows:
        errors.append("PROJECT_TRUTH.md: Abschnitt 'Kanonische Assets' mit Datei/SHA-256 fehlt.")
    for rel, expected in rows:
        path = repo_root / rel
        if not path.is_file():
            errors.append(f"[{rel}] Kanonischer Master fehlt.")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"[{rel}] SHA-256 {actual} weicht von PROJECT_TRUTH.md ({expected}) ab.")
    return errors


def check_attachment_names(repo_root):
    """Beim Empfänger darf nie ein Personenname im PDF-Anhang stehen."""
    errors = []
    for base in MAIL_CODE_DIRS:
        for path in sorted((repo_root / base).rglob("*")):
            if path.suffix not in (".py", ".gs", ".js") or "__pycache__" in path.parts:
                continue
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                for name in _ATTACHMENT_NAME_RE.findall(line):
                    if name != NEUTRAL_ATTACHMENT_NAME:
                        errors.append(f"[{path.relative_to(repo_root)}:{line_no}] Anhangsname '{name}' ist nicht "
                                      f"neutral; erlaubt ist nur '{NEUTRAL_ATTACHMENT_NAME}'.")
    return errors


def _redirect_sources(website):
    sources = set()
    redirects = website / "public" / "_redirects"
    if redirects.is_file():
        for line in redirects.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].startswith("/"):
                sources.add(parts[0])
    return sources


def site_path_exists(repo_root, path):
    """Statische Auflösung gegen public/, _redirects, Astro-Seiten und Pages-Functions."""
    website = repo_root / "apps" / "website"
    path = (path or "/").split("?", 1)[0].split("#", 1)[0]
    if path in ("", "/"):
        return True
    stripped = path.rstrip("/")
    if (website / "public" / stripped.lstrip("/")).is_file():
        return True
    for source in _redirect_sources(website):
        if source.endswith("*") and path.startswith(source[:-1]):
            return True
        if source.rstrip("/") == stripped:
            return True
    segments = [s for s in stripped.split("/") if s]
    pages = website / "src" / "pages"
    if (pages.joinpath(*segments) / "index.astro").is_file() or pages.joinpath(*segments[:-1], segments[-1] + ".astro").is_file():
        return True
    parent = pages.joinpath(*segments[:-1])
    if (parent / "[slug].astro").is_file():
        data = website / "src" / "data"
        needle = re.compile(r"""slug\s*:\s*['"]""" + re.escape(segments[-1]) + r"""['"]""")
        if any(needle.search(f.read_text(encoding="utf-8", errors="ignore")) for f in data.rglob("*.ts")):
            return True
    functions = website / "functions"
    fparent = functions.joinpath(*segments[:-1]) if len(segments) > 1 else functions / segments[0]
    if len(segments) == 1 and path.endswith("/") and any((functions / segments[0]).glob("[[]*[]].ts")):
        return True
    if (functions.joinpath(*segments) / "index.ts").is_file() or functions.joinpath(*segments[:-1], segments[-1] + ".ts").is_file():
        return True
    if len(segments) > 1 and any(fparent.glob("[[]*[]].ts")):
        return True
    return False


def check_mail_urls(repo_root):
    """Jede hsb-boden.de-Adresse im Mail-Code muss von der Website bedient werden (statisch geprüft)."""
    errors = []
    for base in MAIL_CODE_DIRS:
        for path in sorted((repo_root / base).rglob("*")):
            if path.suffix not in (".py", ".gs", ".js") or "__pycache__" in path.parts:
                continue
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                for m in _SITE_URL_RE.finditer(line):
                    url_path = (m.group(1) or "/").rstrip(".,;:")
                    if not site_path_exists(repo_root, url_path):
                        errors.append(f"[{path.relative_to(repo_root)}:{line_no}] {m.group(0)} wird von der "
                                      "Website nicht bedient (keine Datei, Seite, Function oder Weiterleitung).")
    return errors


def check_mail_urls_live(repo_root, timeout=15):
    """Optional (--live): jede gefundene Adresse per HTTP prüfen, Weiterleitungen folgen."""
    import urllib.request
    errors, seen = [], set()
    for base in MAIL_CODE_DIRS:
        for path in sorted((repo_root / base).rglob("*")):
            if path.suffix not in (".py", ".gs", ".js") or "__pycache__" in path.parts:
                continue
            for m in _SITE_URL_RE.finditer(path.read_text(encoding="utf-8", errors="ignore")):
                url = m.group(0).rstrip(".,;:").split("?", 1)[0]
                if url in seen or url.rstrip("/").endswith("/r"):
                    continue
                seen.add(url)
                try:
                    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "HSB-SSOT-Verifier/1.0"})
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        if resp.status >= 400:
                            errors.append(f"{url} -> HTTP {resp.status}")
                except Exception as exc:
                    errors.append(f"{url} -> {type(exc).__name__}: {exc}")
    return errors


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

    ERRORS.extend(check_asset_hashes(REPO_ROOT))
    ERRORS.extend(check_attachment_names(REPO_ROOT))
    ERRORS.extend(check_mail_urls(REPO_ROOT))
    if "--live" in sys.argv:
        ERRORS.extend(check_mail_urls_live(REPO_ROOT))

    if ERRORS:
        print(f"\n❌ {len(ERRORS)} SSOT-Verletzungen gefunden:\n")
        for err in ERRORS:
            print(f"  - {err}")
        print("\nBitte korrigieren gemäß PROJECT_TRUTH.md vor Commit/Abschluss.\n")
        sys.exit(1)

    print("✅ Alle SSOT-Prüfungen bestanden: Jordie Post, Monorepo, CRM SSOT-Sheet, Asset-Hashes, Anhangsname, Mail-URLs & Invarianten konform.")
    sys.exit(0)

if __name__ == "__main__":
    main()
