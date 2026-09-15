#!/usr/bin/env python3
"""
HSB Sales OS - Rollout Runner für 1.000 Entwürfe (500 Joel / 500 Jordie).
Arbeitet sequentiell in 50er Tranchen, schreibt nach jeder Tranche die 2D-Matrix
ins Google Sheet zurück und pausiert 400ms zwischen Entwürfen.
Sicherheit: Reines DraftEmail, REAL_EXTERNAL_SEND_COUNT = 0.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from run_100_batch import run_batch


def main():
    print("================================================================================")
    print(" STARTE 1.000ER ROLLOUT (500 JOEL / 500 JORDIE)")
    print("================================================================================")

    # 1. Jordie: Zeilen 3534 bis 4033 (500 Leads)
    print("\n>>> ROLLOUT JORDIE (Ziel: Zeilen 3534 bis 4033)...")
    for start in range(3534, 4034, 50):
        count = min(50, 4034 - start)
        print(f"\n[JORDI] Tranche Zeilen {start} bis {start + count - 1} ({count} Leads)...")
        run_batch("JORDI", count=count, start_row=start)
        time.sleep(1)

    # 2. Joel: Zeilen 152 bis 651 (500 Leads)
    print("\n>>> ROLLOUT JOEL (Ziel: Zeilen 152 bis 651)...")
    for start in range(152, 652, 25):
        count = min(25, 652 - start)
        print(f"\n[JOEL] Tranche Zeilen {start} bis {start + count - 1} ({count} Leads)...")
        run_batch("JOEL", count=count, start_row=start)
        time.sleep(1)

    print("\n================================================================================")
    print(" 1.000ER ROLLOUT ABGESCHLOSSEN!")
    print("================================================================================")


if __name__ == "__main__":
    main()
