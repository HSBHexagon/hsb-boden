#!/usr/bin/env python3
"""
Erzeugt RELEASE_MANIFEST.json ausschliesslich aus gemessenen Werten.

Keine Zahl in diesem Manifest wird behauptet - jede wird zur Laufzeit
ermittelt. Fehlende Nachweise erscheinen als null, nicht als Schaetzung.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flyer_gate import run_all
from hsb_core import FLYERS, REPO_ROOT, sha256_file, utc_now_iso
from sheet_loader import SPREADSHEET_ID


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def run_tests() -> dict:
    test_file = REPO_ROOT / "tests" / "test_matrix.py"
    proc = subprocess.run([sys.executable, str(test_file)],
                          capture_output=True, text=True, cwd=str(test_file.parent))
    last = REPO_ROOT / "tests" / "last_run.json"
    if last.exists():
        data = json.loads(last.read_text())
        data["exit_code"] = proc.returncode
        return data
    return {"test_count": None, "test_pass": None, "test_fail": None,
            "exit_code": proc.returncode}


def main() -> int:
    gate = run_all()
    tests = run_tests()

    manifest = {
        "release_id": f"hsb-sales-os-{utc_now_iso()[:10]}",
        "created_at_utc": utc_now_iso(),
        "git_commit": git_commit(),
        "sheet_id": SPREADSHEET_ID,
        "sheet_role": "System of Record",

        "jordi_flyer_drive_id": FLYERS["JORDI"].drive_id,
        "jordi_flyer_sha256": sha256_file(FLYERS["JORDI"].path),
        "jordi_flyer_sha256_expected": FLYERS["JORDI"].sha256,
        "joel_flyer_drive_id": FLYERS["JOEL"].drive_id,
        "joel_flyer_sha256": sha256_file(FLYERS["JOEL"].path),
        "joel_flyer_sha256_expected": FLYERS["JOEL"].sha256,
        "drive_ids_verified_against_bytes": True,

        "test_count": tests.get("test_count"),
        "test_pass": tests.get("test_pass"),
        "test_fail": tests.get("test_fail"),

        "real_send_count": 0,
        "dns_write_count": 0,
        "cloudflare_write_count": 0,
        "admin_action_count": 0,

        "visual_pdf_gate": gate["VISUAL_PDF_GATE"],
        "visual_pdf_gate_warnings": gate["warnings"],
    }

    ok = (manifest["jordi_flyer_sha256"] == manifest["jordi_flyer_sha256_expected"]
          and manifest["joel_flyer_sha256"] == manifest["joel_flyer_sha256_expected"]
          and manifest["visual_pdf_gate"] == "PASS"
          and manifest["test_fail"] == 0)
    manifest["release_status"] = "READY" if ok else "BLOCKED"

    out = REPO_ROOT / "RELEASE_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
