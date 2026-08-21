#!/usr/bin/env python3
"""
HSB Sales OS - Kommandozeile.

Beispiele:
    python3 hsb.py status
    python3 hsb.py gate
    python3 hsb.py prepare --owner JORDI --count 100
    python3 hsb.py prepare --owner JOEL --count 25 --tier A --write
    python3 hsb.py inventory

Diese CLI sendet niemals extern. PREPARE != SEND.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_engine import BATCH_ROOT, explain_batch, prepare_batch, write_batch
from flyer_gate import run_all
from hsb_core import FLYERS, AssetGateError, utc_now_iso
from sheet_loader import SPREADSHEET_ID, load_from_xlsx, summarize


def _load() -> list[dict]:
    return load_from_xlsx()


def cmd_status(args) -> int:
    leads = _load()
    s = summarize(leads)
    print(f"Sheet (System of Record): {SPREADSHEET_ID}")
    print(f"Leads gesamt: {s['total']}")
    for owner, c in sorted(s["per_owner"].items()):
        print(f"  {owner:10s} gesamt={c.get('total',0):5d} "
              f"sendefaehig={c.get('eligible',0):5d} "
              f"gesperrt={c.get('blocked',0):5d}")
    if s["top_block_reasons"]:
        print("\nHaeufigste Sperrgruende:")
        for reason, n in s["top_block_reasons"].items():
            print(f"  {n:5d}x {reason}")
    print("\nHinweis: 'gesperrt' ist kein Fehler. Ohne rechtliche Grundlage")
    print("(Legal_Basis) und Versandfreigabe darf nicht gesendet werden (§7 UWG).")
    return 0


def cmd_gate(args) -> int:
    out = run_all(update_golden=args.update_golden)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["VISUAL_PDF_GATE"] == "PASS" else 1


def _next_seq(owner: str) -> int:
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    existing = [p.name for p in BATCH_ROOT.iterdir()
                if p.is_dir() and f"-{owner}-" in p.name]
    return len(existing) + 1


def _active_lead_ids() -> set:
    ids: set = set()
    if not BATCH_ROOT.exists():
        return ids
    for man in BATCH_ROOT.glob("*/manifest.json"):
        try:
            data = json.loads(man.read_text())
        except Exception:
            continue
        if data.get("status") in {"SENT", "CANCELLED"}:
            continue
        ids.update(l.get("Lead_ID") for l in data.get("leads", []))
    return {i for i in ids if i}


def cmd_prepare(args) -> int:
    leads = _load()
    try:
        batch = prepare_batch(
            leads, owner=args.owner, count=args.count,
            campaign=args.campaign or "", industry=args.industry,
            tier=args.tier, seq=_next_seq(args.owner.upper()),
            active_batch_lead_ids=_active_lead_ids(),
        )
    except AssetGateError as exc:
        print(f"ASSET_GATE=FAIL\n{exc}", file=sys.stderr)
        return 2

    print(explain_batch(batch))
    if args.write and batch.leads:
        out = write_batch(batch)
        size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
        print(f"\nGeschrieben: {out}")
        print(f"Entwuerfe: {len(batch.leads)} | Groesse: {size/1_048_576:.1f} MB")
        print("Import: Outlook > Einstellungen > Dateien > Import > Ordner 'drafts'")
    elif args.write:
        print("\nNichts geschrieben - der Batch ist leer.")
    return 0


def cmd_inventory(args) -> int:
    from asset_inventory import run_inventory
    report = run_inventory(write=args.write)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="HSB Sales OS")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Datenlage und Sendefaehigkeit").set_defaults(
        func=cmd_status)

    g = sub.add_parser("gate", help="Visuelles PDF-Release-Gate")
    g.add_argument("--update-golden", action="store_true")
    g.set_defaults(func=cmd_gate)

    pr = sub.add_parser("prepare", help="Batch mit beliebigem N vorbereiten")
    pr.add_argument("--owner", required=True, choices=list(FLYERS) + ["jordi", "joel"])
    pr.add_argument("--count", required=True, type=int)
    pr.add_argument("--campaign", default="")
    pr.add_argument("--industry")
    pr.add_argument("--tier")
    pr.add_argument("--write", action="store_true", help="EML-Dateien erzeugen")
    pr.set_defaults(func=cmd_prepare)

    inv = sub.add_parser("inventory", help="Flyer-Inventur per Hash")
    inv.add_argument("--write", action="store_true", help="Bericht speichern")
    inv.set_defaults(func=cmd_inventory)

    args = p.parse_args()
    args.owner = args.owner.upper() if hasattr(args, "owner") else None
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
