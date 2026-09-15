#!/usr/bin/env python3
"""
HSB Sales OS - Rollout Runner für 2.000 Entwürfe (1.000 Joel / 1.000 Jordie).
Arbeitet sequentiell in sicheren Tranchen:
- Jordie: 40er Tranchen (Ziel: Zeilen 3534 bis 4533)
- Joel  : 20er Tranchen (Ziel: Zeilen 152 bis 1151)
Schreibt dank flush_progress nach jeweils 10 Entwürfen und am Tranchen-Ende
die 2D-Matrix ins Google Sheet zurück.
Sicherheit: Reines DraftEmail, REAL_EXTERNAL_SEND_COUNT = 0.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from run_100_batch import run_batch


def rollout_jordi(start_from: int = 3534, target_end: int = 4533, chunk_size: int = 40):
    print(f"
>>> STARTE ROLLOUT JORDIE (Ziel: Zeilen {start_from} bis {target_end}, {target_end - start_from + 1} Leads)...")
    for start in range(start_from, target_end + 1, chunk_size):
        count = min(chunk_size, target_end + 1 - start)
        print(f"
[JORDI] Tranche Zeilen {start} bis {start + count - 1} ({count} Leads)...
")
        run_batch("JORDI", count=count, start_row=start)
        time.sleep(1)


def rollout_joel(start_from: int = 152, target_end: int = 1151, chunk_size: int = 20):
    print(f"
>>> STARTE ROLLOUT JOEL (Ziel: Zeilen {start_from} bis {target_end}, {target_end - start_from + 1} Leads)...")
    for start in range(start_from, target_end + 1, chunk_size):
        count = min(chunk_size, target_end + 1 - start)
        print(f"
[JOEL] Tranche Zeilen {start} bis {start + count - 1} ({count} Leads)...
")
        run_batch("JOEL", count=count, start_row=start)
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS 2.000er Rollout Runner")
    parser.add_argument("owner", choices=["JOEL", "JORDI", "BOTH"], default="BOTH", nargs="?")
    parser.add_argument("--jordi-start", type=int, default=3534)
    parser.add_argument("--joel-start", type=int, default=152)
    args = parser.parse_args()

    print("================================================================================")
    print(" STARTE 2.000ER ROLLOUT (1.000 JOEL / 1.000 JORDIE)")
    print("================================================================================")

    if args.owner in ["JORDI", "BOTH"]:
        rollout_jordi(start_from=args.jordi_start, target_end=4533, chunk_size=40)

    if args.owner in ["JOEL", "BOTH"]:
        rollout_joel(start_from=args.joel_start, target_end=1151, chunk_size=20)

    print("
================================================================================")
    print(" 2.000ER ROLLOUT ABGESCHLOSSEN!")
    print("================================================================================")


if __name__ == "__main__":
    main()
