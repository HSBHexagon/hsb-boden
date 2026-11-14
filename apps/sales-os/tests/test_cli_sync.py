from pathlib import Path
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_cli_help_includes_sync():
    cli_path = REPO_ROOT / "apps" / "sales-os" / "engine" / "hsb_cli.py"
    res = subprocess.run(
        [sys.executable, str(cli_path), "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "sync" in res.stdout
    assert "Dual-Domain" in res.stdout

def test_cli_sync_dry_run():
    cli_path = REPO_ROOT / "apps" / "sales-os" / "engine" / "hsb_cli.py"
    res = subprocess.run(
        [sys.executable, str(cli_path), "sync", "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "--apply" in res.stdout


def test_cli_rescue_bounces_help():
    cli_path = REPO_ROOT / "apps" / "sales-os" / "engine" / "hsb_cli.py"
    res = subprocess.run(
        [sys.executable, str(cli_path), "rescue-bounces", "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "--limit" in res.stdout
    assert "--apply" in res.stdout


def test_cli_approve_verified_drafts_help():
    cli_path = REPO_ROOT / "apps" / "sales-os" / "engine" / "hsb_cli.py"
    res = subprocess.run(
        [sys.executable, str(cli_path), "approve-verified-drafts", "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "--owner" in res.stdout
    assert "--audit-dir" in res.stdout
    assert "--apply" in res.stdout

