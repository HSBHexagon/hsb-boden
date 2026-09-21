import argparse
from pathlib import Path
import subprocess
import sys

ENGINE = Path(__file__).resolve().parent
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from sqlite_shadow_store import SQLiteShadowStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_ssot_check() -> bool:
    ssot_script = REPO_ROOT / "apps/website/scripts/verify_ssot.py"
    if not ssot_script.exists():
        return True
    res = subprocess.run(
        ["python3", str(ssot_script)], capture_output=True, text=True
    )
    return res.returncode == 0


def run_dns_audit() -> int:
    try:
        from verify_deliverability import audit_domain

        report = audit_domain("hsb-boden.de")
        return report.get("total_score", 0)
    except Exception:
        return 0


def validate_preflight() -> bool:
    if not run_ssot_check():
        print("❌ SSOT Check failed! Aborting orchestrator.")
        return False
    score = run_dns_audit()
    if score < 70:
        print(f"❌ DNS deliverability score too low ({score}/100). Aborting.")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="HSB Master Mailbox Overhaul Orchestrator"
    )
    parser.add_argument(
        "--owner", choices=["JOEL", "JORDI", "ALL"], default="JOEL"
    )
    parser.add_argument("--apply", action="store_true", help="Apply live changes")
    parser.add_argument(
        "--batches", type=int, default=10, help="Number of 50-item batches"
    )
    args = parser.parse_args()

    print("=== HSB SALES OS — MASTER ORCHESTRATOR ===")
    if not validate_preflight():
        sys.exit(1)

    print("✅ Preflight passed: SSOT & DNS Deliverability verified.")
    print(
        f"Target Owner: {args.owner} | Batches: {args.batches} | Mode: {'LIVE APPLY' if args.apply else 'DRY RUN'}"
    )


if __name__ == "__main__":
    main()
