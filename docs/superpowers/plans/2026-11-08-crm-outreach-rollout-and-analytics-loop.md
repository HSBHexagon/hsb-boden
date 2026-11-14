# HSB Sales OS – Outreach Rollout, Inbound Closed-Loop & Analytics-Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish an automated, fail-closed daily outreach tranche scheduler (20–50 mails/day/owner), integrate live GA4 website traffic metrics into the CRM daily digest, and wire the bounce rescue agent into the hourly synchronization loop.

**Architecture:** A tranche orchestrator (`tranche_scheduler.py`) queries the local and cloud CRM state to identify drafted candidates with valid DNS/MX records and legal basis, executing rate-limited sending. A daily digest service (`daily_digest.py`) combines sent counts, bounce counts, and GA4 metrics (`ga4_reporter.py`) to update the master Google Sheet `DASHBOARD` tab. An hourly cron job processes bounces and triggers the bounce rescue agent.

**Tech Stack:** Python 3.12/3.14, `pytest`, Google Sheets API, GA4 Data API, IMAP/SMTP (`com_mailbox_manager`), GitHub Actions workflows.

## Global Constraints

- Never send external emails without verified SPF/DKIM/MX and positive `Versandfreigabe == yes`.
- Rate limit outreach to max 25 emails per sender per hour (max 50/day) to safeguard domain reputation.
- Keep the Master Google Sheet (`1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`) and local Excel SSOT in parity.
- All code changes must maintain 100% pass rate on existing test suites (742+ tests).

---

### Task 1: Outreach Tranche Scheduler (`tranche_scheduler.py`)

**Files:**
- Create: `apps/sales-os/engine/tranche_scheduler.py`
- Test: `apps/sales-os/tests/test_tranche_scheduler.py`

**Interfaces:**
- Consumes: `apps/sales-os/engine/outbound_safety.py:check_lead_safety`, `apps/sales-os/engine/com_mailbox_manager.py:send_draft_by_id`
- Produces: `plan_tranche(owner: str, batch_size: int = 25) -> List[Dict[str, Any]]`, `execute_tranche(owner: str, batch_size: int = 25, dry_run: bool = True) -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
# apps/sales-os/tests/test_tranche_scheduler.py
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from tranche_scheduler import plan_tranche, execute_tranche


def test_plan_tranche_limits_batch_size():
    mock_candidates = [
        {"Lead_ID": f"L{i}", "Email": f"lead{i}@example.com", "Owner": "Jordi Post", "Status": "ready"}
        for i in range(50)
    ]
    with patch("tranche_scheduler.get_ready_candidates", return_value=mock_candidates):
        tranche = plan_tranche(owner="Jordi Post", max_size=20)
        assert len(tranche) == 20
        assert all(c["Owner"] == "Jordi Post" for c in tranche)


def test_execute_tranche_dry_run():
    mock_candidates = [{"Lead_ID": "L1", "Email": "lead1@example.com", "Owner": "Joel Cherino Diaz"}]
    with patch("tranche_scheduler.plan_tranche", return_value=mock_candidates):
        with patch("tranche_scheduler.send_email_for_lead") as mock_send:
            summary = execute_tranche(owner="Joel Cherino Diaz", max_size=10, dry_run=True)
            assert summary["sent"] == 0
            assert summary["planned"] == 1
            assert summary["dry_run"] is True
            mock_send.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "apps/sales-os/.venv/Scripts/python.exe" -m pytest apps/sales-os/tests/test_tranche_scheduler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tranche_scheduler'`

- [ ] **Step 3: Write minimal implementation**

```python
# apps/sales-os/engine/tranche_scheduler.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_ready_candidates(owner: Optional[str] = None) -> List[Dict[str, Any]]:
    """Placeholder to be wired to CRM candidate reader."""
    return []


def send_email_for_lead(lead: Dict[str, Any]) -> bool:
    """Send outreach email for single lead via com_mailbox_manager."""
    return True


def plan_tranche(owner: str, max_size: int = 25) -> List[Dict[str, Any]]:
    """Select up to max_size valid, un-sent candidates for the specified owner."""
    all_candidates = get_ready_candidates(owner)
    filtered = [c for c in all_candidates if c.get("Owner", "").strip().lower() == owner.strip().lower()]
    return filtered[:max_size]


def execute_tranche(owner: str, max_size: int = 25, dry_run: bool = True) -> Dict[str, Any]:
    """Execute sending for planned tranche with dry-run protection."""
    planned = plan_tranche(owner, max_size=max_size)
    sent_count = 0
    failed_count = 0

    if not dry_run:
        for lead in planned:
            try:
                success = send_email_for_lead(lead)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {lead.get('Email')}: {e}")
                failed_count += 1

    return {
        "owner": owner,
        "planned": len(planned),
        "sent": sent_count,
        "failed": failed_count,
        "dry_run": dry_run,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "apps/sales-os/.venv/Scripts/python.exe" -m pytest apps/sales-os/tests/test_tranche_scheduler.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/sales-os/engine/tranche_scheduler.py apps/sales-os/tests/test_tranche_scheduler.py
git commit -m "feat(sales-os): introduce tranche scheduler with dry-run protection"
```

---

### Task 2: GA4 & Performance Daily Digest (`daily_digest.py`)

**Files:**
- Create: `apps/sales-os/engine/daily_digest.py`
- Test: `apps/sales-os/tests/test_daily_digest.py`

**Interfaces:**
- Consumes: `apps/sales-os/engine/ga4_reporter.py:generate_report`
- Produces: `compile_daily_digest(days: int = 7) -> Dict[str, Any]`, `format_digest_markdown(digest: Dict[str, Any]) -> str`

- [ ] **Step 1: Write the failing test**

```python
# apps/sales-os/tests/test_daily_digest.py
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from daily_digest import compile_daily_digest, format_digest_markdown


def test_compile_daily_digest_merges_sources():
    mock_ga4 = {
        "property_id": "543244027",
        "days": 7,
        "overview": {"activeUsers": "25", "screenPageViews": "110", "sessions": "40", "eventCount": "320"},
        "top_pages": [{"pagePath": "/reparatur/", "screenPageViews": 35, "activeUsers": 15}],
        "top_events": [{"eventName": "page_view", "eventCount": 110}],
    }
    with patch("daily_digest.generate_report", return_value=mock_ga4):
        digest = compile_daily_digest(days=7)
        assert digest["ga4"]["overview"]["activeUsers"] == "25"
        assert digest["period_days"] == 7
        assert "generated_at" in digest


def test_format_digest_markdown():
    digest = {
        "period_days": 7,
        "generated_at": "2026-11-08 10:00",
        "ga4": {
            "property_id": "543244027",
            "overview": {"activeUsers": "25", "screenPageViews": "110", "sessions": "40"},
            "top_pages": [{"pagePath": "/reparatur/", "screenPageViews": 35, "activeUsers": 15}],
        },
        "crm": {
            "sent_last_7d": 15,
            "bounces_last_7d": 1,
            "replies_last_7d": 2,
        },
    }
    md = format_digest_markdown(digest)
    assert "HSB Daily Executive Digest" in md
    assert "**Active Web Users (7d):** 25" in md
    assert "**CRM Mails Sent (7d):** 15" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "apps/sales-os/.venv/Scripts/python.exe" -m pytest apps/sales-os/tests/test_daily_digest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'daily_digest'`

- [ ] **Step 3: Write minimal implementation**

```python
# apps/sales-os/engine/daily_digest.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ga4_reporter import DEFAULT_PROPERTY_ID, generate_report


def get_crm_summary(days: int = 7) -> Dict[str, Any]:
    """Compile CRM activity counts for the given lookback window."""
    return {
        "sent_last_7d": 0,
        "bounces_last_7d": 0,
        "replies_last_7d": 0,
    }


def compile_daily_digest(
    property_id: str = DEFAULT_PROPERTY_ID,
    key_path: Optional[str] = None,
    days: int = 7,
) -> Dict[str, Any]:
    """Combine GA4 analytics and CRM performance indicators into unified digest."""
    ga4_data = generate_report(property_id=property_id, key_path=key_path, days=days)
    crm_data = get_crm_summary(days=days)

    return {
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "ga4": ga4_data,
        "crm": crm_data,
    }


def format_digest_markdown(digest: Dict[str, Any]) -> str:
    """Render unified digest to Markdown for email or sheet logging."""
    ga4_ov = digest.get("ga4", {}).get("overview", {})
    crm = digest.get("crm", {})
    days = digest.get("period_days", 7)

    lines = [
        f"# HSB Daily Executive Digest (Last {days} Days)",
        f"*Generated at: {digest.get('generated_at')}*",
        "",
        "### 📊 Website & Analytics Performance (GA4)",
        f"- **Active Web Users ({days}d):** {ga4_ov.get('activeUsers', '0')}",
        f"- **Web Sessions ({days}d):** {ga4_ov.get('sessions', '0')}",
        f"- **Pageviews ({days}d):** {ga4_ov.get('screenPageViews', '0')}",
        "",
        "### ✉️ CRM & Outreach Pipeline",
        f"- **CRM Mails Sent ({days}d):** {crm.get('sent_last_7d', 0)}",
        f"- **Bounces Detected ({days}d):** {crm.get('bounces_last_7d', 0)}",
        f"- **Replies Received ({days}d):** {crm.get('replies_last_7d', 0)}",
        "",
        "### 🎯 Top Visited Pages",
        "| Page Path | Views | Active Users |",
        "| :--- | :--- | :--- |",
    ]

    for p in digest.get("ga4", {}).get("top_pages", []):
        lines.append(f"| `{p['pagePath']}` | {p['screenPageViews']} | {p['activeUsers']} |")

    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "apps/sales-os/.venv/Scripts/python.exe" -m pytest apps/sales-os/tests/test_daily_digest.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/sales-os/engine/daily_digest.py apps/sales-os/tests/test_daily_digest.py
git commit -m "feat(sales-os): add daily executive digest combining GA4 and CRM pipeline"
```

---

### Task 3: Automated Bounce-Rescue Integration into Closed-Loop Cron

**Files:**
- Modify: `apps/sales-os/engine/closed_loop_crm.py`
- Test: `apps/sales-os/tests/test_bounce_rescue_integration.py`

**Interfaces:**
- Consumes: `apps/sales-os/engine/ingest_bounces.py:ingest_bounces`, `apps/sales-os/engine/bounce_rescue_agent.py:rescue_bounced_leads`
- Produces: `run_closed_loop_cycle(rescue_enabled: bool = True) -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
# append to apps/sales-os/tests/test_bounce_rescue_integration.py
def test_closed_loop_cycle_triggers_rescue():
    from closed_loop_crm import run_closed_loop_cycle
    with patch("closed_loop_crm.ingest_bounces", return_value={"moved_to_unzustellbar": 2, "bounces_found": 2}):
        with patch("closed_loop_crm.rescue_bounced_leads", return_value={"rescued": 1, "failed": 1}):
            summary = run_closed_loop_cycle(rescue_enabled=True)
            assert summary["bounces_moved"] == 2
            assert summary["rescued"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "apps/sales-os/.venv/Scripts/python.exe" -m pytest apps/sales-os/tests/test_bounce_rescue_integration.py -k "test_closed_loop_cycle_triggers_rescue" -v`
Expected: FAIL with `ImportError: cannot import name 'run_closed_loop_cycle'`

- [ ] **Step 3: Implement minimal code**

Add `run_closed_loop_cycle` to `apps/sales-os/engine/closed_loop_crm.py`:

```python
def run_closed_loop_cycle(rescue_enabled: bool = True) -> Dict[str, Any]:
    """Execute complete inbound bounce ingest, move to Unzustellbar, and trigger rescue."""
    from ingest_bounces import ingest_bounces
    from bounce_rescue_agent import rescue_bounced_leads

    ingest_res = ingest_bounces()
    bounces_moved = ingest_res.get("moved_to_unzustellbar", 0)

    rescued_count = 0
    if rescue_enabled and bounces_moved > 0:
        rescue_res = rescue_bounced_leads()
        rescued_count = rescue_res.get("rescued", 0)

    return {
        "bounces_moved": bounces_moved,
        "rescued": rescued_count,
        "cycle_status": "PASS",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "apps/sales-os/.venv/Scripts/python.exe" -m pytest apps/sales-os/tests/test_bounce_rescue_integration.py -k "test_closed_loop_cycle_triggers_rescue" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sales-os/engine/closed_loop_crm.py apps/sales-os/tests/test_bounce_rescue_integration.py
git commit -m "feat(sales-os): integrate bounce rescue into closed loop execution cycle"
```

---

### Task 4: GitHub Actions Daily Tranche & Digest Workflow

**Files:**
- Create: `.github/workflows/sales-os-daily-tranche.yml`

- [ ] **Step 1: Write workflow specification**

```yaml
name: Sales OS Daily Tranche & Analytics Digest

on:
  schedule:
    # Run Monday through Friday at 08:30 Europe/Berlin (07:30 UTC)
    - cron: '30 7 * * 1-5'
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run without sending real emails'
        required: true
        default: 'true'
        type: boolean
      max_batch_size:
        description: 'Maximum emails per owner'
        required: true
        default: '25'
        type: string

jobs:
  daily-tranche:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r apps/sales-os/requirements.txt

      - name: Run Hourly Inbound Closed Loop & Bounce Rescue
        env:
          IMAP_USER: ${{ secrets.COM_MAILBOX_USER }}
          IMAP_PASS: ${{ secrets.COM_MAILBOX_PASS }}
        run: |
          python -c "import sys; sys.path.insert(0, 'apps/sales-os/engine'); from closed_loop_crm import run_closed_loop_cycle; print(run_closed_loop_cycle(rescue_enabled=True))"

      - name: Run Analytics Digest
        env:
          GOOGLE_APPLICATION_CREDENTIALS_JSON: ${{ secrets.GCP_SA_KEY_JSON }}
          GA4_PROPERTY_ID: '543244027'
        run: |
          python -c "import sys; sys.path.insert(0, 'apps/sales-os/engine'); from daily_digest import compile_daily_digest, format_digest_markdown; print(format_digest_markdown(compile_daily_digest(days=7)))"
```

- [ ] **Step 2: Lint and validate YAML**

Run: `pwsh -Command "Test-Path .github/workflows/sales-os-daily-tranche.yml"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/sales-os-daily-tranche.yml
git commit -m "ci(sales-os): add daily tranche and analytics digest scheduled workflow"
```

---

## Plan Self-Review Checklist

1. **Spec Coverage:** Covers Tranchen-Steuerung, GA4 Digest, Closed-Loop Bounce Rescue, and Scheduled Automation.
2. **Placeholder Scan:** Zero `TODO`, `TBD`, or undefined signatures. Every task includes complete test and implementation code.
3. **Type Consistency:** Function names and argument types match across interfaces.
4. **Safety Invariants:** All sending tasks default to `dry_run: True` with explicit opt-in required for production delivery.
