#!/usr/bin/env python3
"""
Buendelt die vier .gs-Quelldateien zu apps_script/HSB_SALES_OS.gs.

Apps Script teilt sich einen gemeinsamen Namensraum ueber alle Dateien,
deshalb ist das Buendeln rein mechanisch. Vorteil: beim manuellen Einbau
sind nur zwei Einfuegevorgaenge noetig statt fuenf.

Die Quelldateien bleiben massgeblich - diese Datei wird erzeugt, nicht
bearbeitet.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "apps_script"
ORDER = ["Config.gs", "Engine.gs", "Actions.gs", "Code.gs"]
TARGET = SRC / "HSB_SALES_OS.gs"

HEADER = """/**
 * HSB Sales OS - Gesamtdatei (Config + Engine + Actions + Code).
 *
 * ERZEUGT von engine/build_single.py - nicht direkt bearbeiten.
 * Aenderungen gehoeren in die Quelldateien unter apps_script/.
 *
 * Apps Script teilt sich einen gemeinsamen Namensraum ueber alle Dateien
 * eines Projekts; das Buendeln aendert daher nichts am Verhalten.
 */
"""


def build() -> Path:
    parts = [HEADER]
    for name in ORDER:
        path = SRC / name
        if not path.exists():
            raise FileNotFoundError(f"Quelldatei fehlt: {path}")
        parts.append(f"\n/* {'=' * 66}\n   {name}\n   {'=' * 66} */\n")
        parts.append(path.read_text(encoding="utf-8"))
    combined = "\n".join(parts)
    TARGET.write_text(combined, encoding="utf-8")
    return TARGET


if __name__ == "__main__":
    out = build()
    text = out.read_text(encoding="utf-8")
    print(f"{out.relative_to(REPO_ROOT)}: {len(text.splitlines())} Zeilen, "
          f"{len(text)} Zeichen")
