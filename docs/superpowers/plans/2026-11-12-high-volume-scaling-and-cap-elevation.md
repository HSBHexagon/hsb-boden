# High-Volume Outreach Scaling & Cap Elevation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove artificial hardcoded 100-mail caps, restore dynamic environment-controlled scaling (up to 1,000+ per mailbox/day), and establish the multi-inbox rotation architecture required for 1,000 to 10,000 emails per campaign without deliverability penalties.

**Architecture:** Refactor `send_governance.py`, `versand-tranche.sh`, and `.github/workflows/sales-os-safety.yml` to remove the hardcoded `min(100, ...)` clamp; restore operator sovereignty via `HSB_DAILY_CAP` / `HSB_MAX_DAILY_CAP`; implement multi-inbox pool rotation and high-throughput token bucket pacing; update test suites.

**Tech Stack:** Python 3.12/3.14 (`smtplib`, `imaplib`), Bash, Pytest, GitHub Actions.

## Global Constraints
- Do not mutate or replace live WordPress site.
- `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` during tests and dry runs.
- Deliverability first: SPF, DKIM (`d=hsb-boden.com`), DMARC (`p=none`) and jitter (45–180s default, configurable) must remain enforced.
- Monorepo rules: Jordie Post spelled with `-ie`.
- Verify with `python3 scripts/verify_ssot.py` and `pytest apps/sales-os/tests`.

---

### Task 1: Remove Artificial 100-Cap Clamp from Engine & Shell Scripts

**Files:**
- Modify: `apps/sales-os/engine/send_governance.py:18-30`
- Modify: `apps/sales-os/bin/versand-tranche.sh:8-25`
- Modify: `.github/workflows/sales-os-safety.yml:25-35`
- Test: `apps/sales-os/tests/test_send_governance.py`
- Test: `apps/sales-os/tests/test_ramp.py`

**Interfaces:**
- Consumes: `os.environ.get('HSB_MAX_DAILY_CAP')`, `os.environ.get('HSB_DAILY_CAP')`
- Produces: `MAX_DAILY_CAP_PER_MAILBOX: int`, `DAILY_CAP_PER_MAILBOX: int` without arbitrary upper `min(100, ...)` clamp.

- [x] **Step 1: Write failing test verifying arbitrary caps (> 100) are accepted when configured**

```python
# In apps/sales-os/tests/test_send_governance.py
def test_governance_allows_operator_configured_high_caps(monkeypatch):
    monkeypatch.setenv("HSB_MAX_DAILY_CAP", "1000")
    monkeypatch.setenv("HSB_DAILY_CAP", "500")
    import importlib
    import send_governance
    importlib.reload(send_governance)
    assert send_governance.MAX_DAILY_CAP_PER_MAILBOX >= 1000
    assert send_governance.DAILY_CAP_PER_MAILBOX >= 500
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_send_governance.py -k test_governance_allows_operator_configured_high_caps`
Expected: FAIL (due to `min(100, ...)`)

- [x] **Step 3: Refactor `send_governance.py` to remove `min(100, ...)` clamp**

Restore operator configurability:
```python
DEFAULT_MAX_CAP = int(os.environ.get('HSB_MAX_DAILY_CAP', 250))
MAX_DAILY_CAP_PER_MAILBOX: int = DEFAULT_MAX_CAP
DAILY_CAP_PER_MAILBOX: int = min(MAX_DAILY_CAP_PER_MAILBOX, int(os.environ.get('HSB_DAILY_CAP', DEFAULT_MAX_CAP)))
```

- [x] **Step 4: Update `versand-tranche.sh` validation boundary**

Change validation from `(( COUNT >= 1 && COUNT <= 100 ))` to `(( COUNT >= 1 && COUNT <= HSB_MAX_BUDGET ))` with fallback up to 1000.

- [x] **Step 5: Run tests and ensure all pass**

Run: `pytest apps/sales-os/tests/test_send_governance.py apps/sales-os/tests/test_ramp.py`
Expected: PASS

---

### Task 2: Multi-Inbox Rotation Engine (Architecture for 1.000 to 10.000 Emails)

**Files:**
- Create: `apps/sales-os/engine/inbox_rotation_pool.py`
- Test: `apps/sales-os/tests/test_inbox_rotation_pool.py`

**Interfaces:**
- Consumes: Mailbox registry from `hsb_config.py` / `CONNECTIONS`
- Produces: `InboxRotationPool.get_next_available_mailbox() -> Optional[str]`
- Enforces: Per-mailbox daily cap distribution across $N$ mailboxes (e.g. 10 mailboxes × 100/day = 1,000/day; 20 mailboxes × 50/day = 1,000/day).

- [x] **Step 1: Write unit tests for round-robin and health-weighted rotation**

Verify that sending 1,000 messages across a pool of $N$ accounts never exhausts a single mailbox beyond its individual cap while fulfilling the aggregate volume.

- [x] **Step 2: Implement `InboxRotationPool`**

Implement round-robin dispatch, cap tracking per sender, and failover when one mailbox reaches limit or encounters temporary deferral.

- [x] **Step 3: Run tests and commit**

Run: `pytest apps/sales-os/tests/test_inbox_rotation_pool.py`
Expected: PASS

---

### Task 3: High-Volume Verification & SSOT Integration

**Files:**
- Modify: `docs/MASTER_EXECUTION_PLAN.md`
- Run: `python3 scripts/verify_ssot.py`
- Run: `pytest apps/sales-os/tests`

- [x] **Step 1: Run SSOT verification script**
- [x] **Step 2: Run complete test suite**
- [x] **Step 3: Commit and update checkpoint state**
