#!/usr/bin/env python3
"""
HSB Sales OS - Rollout Runner für 1.000 Entwürfe (500 Joel / 500 Jordie).
Arbeitet sequentiell in sicheren Tranchen:
- Jordi Post: 40er Tranchen (Ziel: Zeilen 4534 bis 5033)
- Joel Cherino Diaz: 20er Tranchen (Ziel: Zeilen 1152 bis 1651)
Schreibt nach jeder Tranche und via flush_progress die 2D-Matrix ins Google Sheet zurück
und pausiert 400ms zwischen Entwürfen.
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


def rollout_jordie(start_from: int = 4534, target_end: int = 5033, chunk_size: int = 40):
    print(f"\n>>> STARTE ROLLOUT JORDIE (Ziel: Zeilen {start_from} bis {target_end}, {target_end - start_from + 1} Leads)...")
    for start in range(start_from, target_end + 1, chunk_size):
        count = min(chunk_size, target_end + 1 - start)
        print(f"\n[JORDIE] Tranche Zeilen {start} bis {start + count - 1} ({count} Leads)...")
        run_batch("JORDI", count=count, start_row=start)
        time.sleep(1)


def rollout_joel(start_from: int = 1652, target_end: int = 2151, chunk_size: int = 20):
    print(f"\n>>> STARTE ROLLOUT JOEL (Ziel: Zeilen {start_from} bis {target_end}, {target_end - start_from + 1} Leads)...")
    for start in range(start_from, target_end + 1, chunk_size):
        count = min(chunk_size, target_end + 1 - start)
        print(f"\n[JOEL] Tranche Zeilen {start} bis {start + count - 1} ({count} Leads)...")
        run_batch("JOEL", count=count, start_row=start)
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS 1.000er Rollout Runner")
    parser.add_argument("owner", choices=["JOEL", "JORDI", "BOTH"], default="BOTH", nargs="?")
    parser.add_argument("--jordie-start", type=int, default=4534)
    parser.add_argument("--joel-start", type=int, default=1652)
    args = parser.parse_args()

    print("================================================================================")
    print(" STARTE 1.000ER ROLLOUT (500 JOEL / 500 JORDIE)")
    print("================================================================================")

    if args.owner in ["JORDI", "BOTH"]:
        rollout_jordie(start_from=args.jordie_start, target_end=5033, chunk_size=40)

    if args.owner in ["JOEL", "BOTH"]:
        rollout_joel(start_from=args.joel_start, target_end=1651, chunk_size=20)

    print("\n================================================================================")
    print(" 1.000ER ROLLOUT ABGESCHLOSSEN!")
    print("================================================================================")


if __name__ == "__main__":
    main()
