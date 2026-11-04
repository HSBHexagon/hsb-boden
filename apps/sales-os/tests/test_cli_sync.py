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
