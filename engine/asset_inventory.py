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
    # Eigene Verifikations-Artefakte - sonst zaehlt sich die Inventur selbst
    # mit und blaeht die Zahl "kanonisch korrekt" auf.
    "drive_verify",
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
        "reichweite": {
            "geprueft": "lose .pdf-Dateien unterhalb der Suchwurzeln",
            "NICHT_geprueft": [
                "PDFs innerhalb von ZIP-Archiven",
                "PDFs, die als Anhang in .eml-Dateien eingebettet sind",
                "Dateien in Drive (nur die zwei kanonischen IDs werden "
                "beim Asset-Gate geprueft)",
            ],
            "konsequenz": (
                "Ein Ergebnis ohne Treffer beweist nur, dass keine LOSE "
                "veraltete PDF gefunden wurde. Fuer EML-Anhaenge braucht es "
                "eine eigene Pruefung - siehe verify_eml_attachments()."
            ),
        },
    }

    if write:
        out = REPO_ROOT / "docs" / "ASSET_INVENTORY.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        report["written_to"] = str(out)
    return report


def verify_eml_attachments(roots: list[Path] | None = None) -> dict:
    """
    Prueft die PDF-Anhaenge in .eml-Dateien - die Luecke, die eine reine
    Dateisuche nach *.pdf nicht schliesst.

    Genau hier steckte der Fehler vom 2026-08-21: die losen PDFs waren
    korrigiert, die eingebetteten Anhaenge zunaechst nicht.
    """
    import email
    from email import policy
    from email.parser import BytesParser

    roots = roots or [Path.home() / "Desktop", Path.home() / "ABLAGE"]
    canonical, outdated, unknown, missing = [], [], [], []
    checked = 0

    for root in roots:
        if not root.exists():
            continue
        for eml in root.rglob("*.eml"):
            if any(part in SKIP_DIR_PARTS for part in eml.parts):
                continue
            checked += 1
            try:
                with open(eml, "rb") as fh:
                    msg = BytesParser(policy=policy.default).parsebytes(fh.read())
            except Exception as exc:
                unknown.append({"path": str(eml), "error": str(exc)})
                continue

            found = False
            for part in msg.walk():
                if (part.get_content_maintype() == "application"
                        and part.get_filename()):
                    found = True
                    data = part.get_payload(decode=True) or b""
                    digest = hashlib_sha256(data)
                    entry = {"path": str(eml), "attachment": part.get_filename(),
                             "sha256": digest}
                    if digest in CANON_BY_HASH:
                        entry["owner"] = CANON_BY_HASH[digest].owner_key
                        canonical.append(entry)
                    elif digest in KNOWN_BAD_HASHES:
                        entry["reason"] = KNOWN_BAD_HASHES[digest]
                        outdated.append(entry)
                    else:
                        unknown.append(entry)
            if not found:
                missing.append({"path": str(eml), "reason": "kein Anhang"})

    return {
        "eml_geprueft": checked,
        "anhang_kanonisch": len(canonical),
        "anhang_veraltet": len(outdated),
        "anhang_unbekannt": len(unknown),
        "ohne_anhang": len(missing),
        "veraltete_details": outdated[:20],
        "ohne_anhang_details": missing[:20],
    }


def hashlib_sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    import sys
    if "--eml" in sys.argv:
        print(json.dumps(verify_eml_attachments(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(run_inventory(write=True), indent=2, ensure_ascii=False))
