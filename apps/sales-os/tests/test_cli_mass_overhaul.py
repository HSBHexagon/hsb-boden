from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_cli_help_includes_overhaul_all():
    cli_path = REPO_ROOT / "apps" / "sales-os" / "engine" / "hsb_cli.py"
    res = subprocess.run(
        [sys.executable, str(cli_path), "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "overhaul-all" in res.stdout
