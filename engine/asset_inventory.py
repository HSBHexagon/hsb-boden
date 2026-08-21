"""
HSB Sales OS - Flyer-Inventur per Inhalt, nicht per Ordnerliste.

Zweimal in Folge hat eine geratene Verzeichnisliste die entscheidende Datei
uebersehen. Diese Inventur sucht deshalb nach Inhalt: alle PDFs unterhalb
definierter Wurzeln werden gehasht und gegen die bekannten Fassungen
eingeordnet.

Diese Datei loescht nichts. Sie erzeugt ein Manifest und schlaegt
Quarantaene-Verschiebungen vor. Das Verschieben bleibt eine bewusste
Einzelentscheidung des Nutzers.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hsb_core import FLYERS, KNOWN_BAD_HASHES, REPO_ROOT, sha256_file

SEARCH_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "ABLAGE" / "04_PROJEKTE" / "03_HSB_BODEN",
    REPO_ROOT,
]

SKIP_DIR_PARTS = {
    "node_modules", ".git", "Library", ".Trash", "_SOFT_DELETED",
    ".worktrees", "06_Archiv", "__pycache__", ".venv",
}

NAME_HINTS = ("hsb-flyer", "hsb_flyer", "flyer")
CANON_BY_HASH = {f.sha256: f for f in FLYERS.values()}


def _iter_pdfs(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*.pdf"):
        if any(part in SKIP_DIR_PARTS for part in p.parts):
            continue
        if not any(h in p.name.lower() for h in NAME_HINTS):
            continue
        yield p


def run_inventory(write: bool = False) -> dict:
    canonical, outdated, unknown, errors = [], [], [], []

    for root in SEARCH_ROOTS:
        for pdf in _iter_pdfs(root):
            try:
                digest = sha256_file(pdf)
            except OSError as exc:
                errors.append({"path": str(pdf), "error": str(exc)})
                continue

            entry = {"path": str(pdf), "sha256": digest,
                     "bytes": pdf.stat().st_size}

            if digest in CANON_BY_HASH:
                entry["owner"] = CANON_BY_HASH[digest].owner_key
                canonical.append(entry)
            elif digest in KNOWN_BAD_HASHES:
                entry["reason"] = KNOWN_BAD_HASHES[digest]
                outdated.append(entry)
            else:
                unknown.append(entry)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "kanonisch_korrekt": len(canonical),
            "veraltet_bekannt_fehlerhaft": len(outdated),
            "unbekannte_fassung": len(unknown),
            "lesefehler": len(errors),
            "quarantaene_vorschlag": f"_SOFT_DELETED/{ts}/",
        },
        "canonical": canonical,
        "outdated": outdated,
        "unknown": unknown,
        "errors": errors,
        "hinweis": (
            "Diese Inventur loescht nichts. 'outdated' sind nachweislich "
            "veraltete Fassungen; sie gehoeren in die Quarantaene, nicht in "
            "den Papierkorb. Kanonische Master niemals verschieben."
        ),
    }

    if write:
        out = REPO_ROOT / "docs" / "ASSET_INVENTORY.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        report["written_to"] = str(out)
    return report


if __name__ == "__main__":
    print(json.dumps(run_inventory(write=True), indent=2, ensure_ascii=False))
