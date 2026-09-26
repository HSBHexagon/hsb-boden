# HSB .COM Rapid Draft Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ultraschnelle und fehlertolerante Erstellung von Akquise-Entwürfen direkt im .com-Postfach (KASServer IMAP) mit kanonischem Flyer, §35a-Signatur und atomarem Google Sheet Writeback.

**Architecture:** Modulare Python-CLI (`run_com_batch.py`), die autoritative Leads aus `ALL_LEADS` filtert, über die verifizierte IMAP-Engine (`ComMailboxClient`) direkt in den KASServer-Ordner `Entw&APw-rfe` injiziert und das Sheet per 2D-Matrix Bulk aktualisiert.

**Tech Stack:** Python 3.14, `imaplib`, `email`, `google-api-python-client`, `pytest`.

## Global Constraints

- REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Ausschließlich Entwürfe, kein externer SMTP-Versand an Prospekte).
- Absender ist zwingend `j-cherino@hsb-boden.com` (Joel) oder `j-post@hsb-boden.com` (Jordie).
- Geschäftsführername in Signatur und Impressum ist strikt `Jordie Post` (mit "-ie").
- Flyer-Dateien müssen bytegenau den kanonischen Hashes entsprechen (`08e1149e4fed...` für Jordie, `2bccadacc77b...` für Joel).
- Dry-Run als Standard: Reale IMAP-Injektion und Sheet-Writeback erfolgen nur bei explizitem Flag `--apply`.

---

### Task 1: Lead Selector & Filter-Gate (`select_com_eligible_leads`)

**Files:**
- Create: `apps/sales-os/engine/com_batch_selector.py`
- Test: `apps/sales-os/tests/test_com_batch_selector.py`

**Interfaces:**
- Consumes: `list[dict]` (Rohdaten aus `ALL_LEADS`)
- Produces: `select_com_eligible_leads(leads: list[dict], owner: str, limit: int) -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from com_batch_selector import select_com_eligible_leads


def test_select_com_eligible_leads_filters_correctly():
    sample_leads = [
        {"Lead_ID": "L-1", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "a@test.de", "Drafted_At": ""},
        {"Lead_ID": "L-2", "Owner": "Joel Cherino", "Versandfreigabe": "no", "Email": "b@test.de", "Drafted_At": ""},
        {"Lead_ID": "L-3", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "c@test.de", "Drafted_At": "2026-09-20"},
        {"Lead_ID": "L-4", "Owner": "Jordie Post", "Versandfreigabe": "yes", "Email": "d@test.de", "Drafted_At": ""},
        {"Lead_ID": "L-5", "Owner": "Joel Cherino", "Versandfreigabe": "yes", "Email": "e@test.de", "Drafted_At": "", "Opt_Out": "yes"},
    ]
    selected = select_com_eligible_leads(sample_leads, owner="JOEL", limit=10)
    assert len(selected) == 1
    assert selected[0]["Lead_ID"] == "L-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_com_batch_selector.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'com_batch_selector')

- [ ] **Step 3: Implement minimal code**

Write `apps/sales-os/engine/com_batch_selector.py`:
```python
from typing import Any, Dict, List
import re

def select_com_eligible_leads(leads: List[Dict[str, Any]], owner: str = "JOEL", limit: int = 50) -> List[Dict[str, Any]]:
    norm_owner = owner.strip().upper()
    owner_match = "JOEL" if norm_owner in ("JOEL", "J-CHERINO") else "JORDI"
    
    eligible = []
    seen_emails = set()

    for lead in leads:
        lead_owner = str(lead.get("Owner") or lead.get("Verantwortlicher") or "").upper()
        if owner_match == "JOEL" and "JOEL" not in lead_owner:
            continue
        if owner_match == "JORDI" and "JORD" not in lead_owner:
            continue

        freigabe = str(lead.get("Versandfreigabe") or "").lower().strip()
        if freigabe not in ("yes", "ja", "1", "true"):
            continue

        drafted = str(lead.get("Drafted_At") or "").strip()
        sent = str(lead.get("Send_Status") or "").lower().strip()
        if drafted or sent in ("sent", "gesendet"):
            continue

        optout = str(lead.get("Opt_Out") or lead.get("Opt-out-Status") or "").lower().strip()
        suppressed = str(lead.get("Suppressed") or "").lower().strip()
        if optout in ("yes", "ja") or suppressed in ("yes", "ja"):
            continue

        email = str(lead.get("Email") or lead.get("E-Mail") or "").strip().lower()
        if not email or "@" not in email or email in seen_emails:
            continue

        seen_emails.add(email)
        eligible.append(lead)
        if len(eligible) >= limit:
            break

    return eligible
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_com_batch_selector.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sales-os/engine/com_batch_selector.py apps/sales-os/tests/test_com_batch_selector.py
git commit -m "feat(sales-os): Lead-Selector Gate fuer .com Batch Engine"
```

---

### Task 2: .COM Rapid Batch Runner CLI (`run_com_batch.py`)

**Files:**
- Create: `apps/sales-os/engine/run_com_batch.py`
- Test: `apps/sales-os/tests/test_run_com_batch.py`

**Interfaces:**
- Consumes: `select_com_eligible_leads`, `ComMailboxClient`, `render_canonical_email`, `write_2d_matrix_bulk`
- Produces: CLI execution `run_com_batch(owner: str, count: int, dry_run: bool) -> dict`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import sys
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from run_com_batch import run_com_batch_in_memory


def test_run_com_batch_dry_run_produces_draft_manifest():
    mock_leads = [
        {
            "row_idx": 10,
            "Lead_ID": "HSB-TEST-001",
            "Owner": "Joel Cherino",
            "Versandfreigabe": "yes",
            "Email": "info@test-bau.de",
            "Firmenname": "Test Bau GmbH",
            "Anrede": "Herr",
            "Nachname": "Mustermann"
        }
    ]
    res = run_com_batch_in_memory(mock_leads, owner="JOEL", limit=5, dry_run=True)
    assert res["status"] == "SUCCESS_DRY_RUN"
    assert res["selected_count"] == 1
    assert "HSB-HEXAGON-Industrieboeden-Flyer.pdf" in res["manifest"][0]["flyer_filename"]
    assert "j-cherino@hsb-boden.com" in res["manifest"][0]["sender"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_run_com_batch.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'run_com_batch')

- [ ] **Step 3: Implement minimal code in `run_com_batch.py`**

```python
import argparse
import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List

ENGINE = Path(__file__).resolve().parent
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from com_batch_selector import select_com_eligible_leads
from com_mailbox_manager import ComMailboxClient
from canonical_template_factory import render_canonical_email


def run_com_batch_in_memory(leads: List[Dict[str, Any]], owner: str = "JOEL", limit: int = 50, dry_run: bool = True) -> Dict[str, Any]:
    selected = select_com_eligible_leads(leads, owner=owner, limit=limit)
    if not selected:
        return {"status": "NO_ELIGIBLE_LEADS", "selected_count": 0, "manifest": []}

    client = None if dry_run else ComMailboxClient(owner)
    manifest = []
    sender_email = "j-cherino@hsb-boden.com" if owner.upper() in ("JOEL", "J-CHERINO") else "j-post@hsb-boden.com"

    for lead in selected:
        email_data = render_canonical_email(lead, owner=owner, domain="com")
        item = {
            "lead_id": lead.get("Lead_ID"),
            "to": email_data["to_address"],
            "subject": email_data["subject"],
            "sender": sender_email,
            "flyer_filename": email_data["flyer_filename"]
        }
        if not dry_run and client:
            ok, mid = client.create_draft(
                to_email=email_data["to_address"],
                subject=email_data["subject"],
                body_html=email_data["body_html"],
                flyer_path=email_data["flyer_path"],
                flyer_filename=email_data["flyer_filename"]
            )
            item["message_id"] = mid
            item["status"] = "DRAFTED"
        else:
            item["status"] = "DRY_RUN"

        manifest.append(item)

    status_str = "SUCCESS_DRY_RUN" if dry_run else "SUCCESS_LIVE"
    return {"status": status_str, "selected_count": len(manifest), "manifest": manifest}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_run_com_batch.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sales-os/engine/run_com_batch.py apps/sales-os/tests/test_run_com_batch.py
git commit -m "feat(sales-os): Rapid .COM Batch Runner CLI Engine"
```

---

### Task 3: Live Verification & Self-Review

- [ ] **Step 1: Run full testsuite**

Run: `pytest apps/sales-os/tests/ -q`
Expected: 92 passed, 0 failed.

- [ ] **Step 2: Dry-run execution on Sheet data**

Run: `python3 apps/sales-os/engine/run_com_batch.py --owner JOEL --count 5`
Expected: Lists 5 eligible leads and outputs dry-run manifest.
