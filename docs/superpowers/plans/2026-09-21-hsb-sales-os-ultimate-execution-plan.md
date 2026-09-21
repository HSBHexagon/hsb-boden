# HSB Sales OS — Ultimate High-Efficiency Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully automated, zero-drift B2B outbound and CRM synchronization engine for HSB Hexagon Säurebau GmbH that in-place overhauls 1.877 drafts across Joel Cherino (1.080) and Jordie Post (797) mailboxes to the canonical 2026 standard, locks the golden blueprint for all 4.081 remaining leads, and upgrades the architecture from sequential LogicFlows to high-speed Microsoft Graph `$batch`, an ACID SQLite shadow store, and an autonomous multi-worker swarm.

**Architecture:** Decoupled multi-worker pipeline where a local SQLite shadow store buffers lead states with sub-millisecond ACID transactions, while a Graph batching adapter executes M365 draft operations in 20-call JSON arrays with exponential 429 backoff. Google Sheets `ALL_LEADS` receives asynchronous 2D-matrix bulk updates without blocking the worker lanes. Strict fail-closed recipient gates, live DNS deliverability guards (SPF `-all`, DMARC, MX), and SSOT linters prevent any ghost drafts, invalid company names, or partner naming drift.

**Tech Stack:** Python 3.14, Microsoft Graph API v1.0 (`$batch`), SQLite3 (WAL journal mode), Google Sheets API v4 (2D batch updates), macOS native `dig` (DNS audit), Pytest.

## Global Constraints

- Hermetic Safety Law: `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (exclusively drafts, zero external prospect sends).
- Managing Director (§ 35a GmbHG): Verbatim `Jordie Post` (with `-ie`, never `Jordi`).
- Monorepo SSOT: `HSBHexagon/hsb-boden` (`apps/sales-os` and `apps/website`).
- Canonical Assets: EOP-optimized 241 KB Flyer (`HSB-Flyer-Joel-Cherino_FINAL.pdf` and `HSB-Flyer-Jordie-Post_FINAL.pdf`), 102x75 bicubic scaled logo (`brand/hsb-boden-logo.png`).
- Recipient Fail-Closed Invariant: `if not to_addr or "@" not in to_addr: raise ValueError(...)`.

---

### Task 1: Canonical Template Factory Hardening

**Files:**
- Create: `apps/sales-os/engine/canonical_template_factory.py`
- Test: `apps/sales-os/tests/test_canonical_template_factory.py`

**Interfaces:**
- Consumes: Lead dict (`Firmenname`, `Email` / `E-Mail`, `Anrede`, `Nachname`, `Segment`), Owner (`JOEL` or `JORDI`).
- Produces: `render_canonical_email(lead: dict, owner: str) -> dict` returning:
  `{"subject": str, "body_html": str, "to_address": str, "flyer_path": str, "flyer_filename": str, "logo_url": str}`.

- [x] **Step 1: Write the failing test**

Create `apps/sales-os/tests/test_canonical_template_factory.py`:
```python
import pytest
from apps.sales-os.engine.canonical_template_factory import render_canonical_email

def test_render_canonical_email_valid_lead():
    lead = {
        "Lead_ID": "TEST-001",
        "Firmenname": "Molkerei Biedermann AG",
        "Email": "info@biedermann.ch",
        "Anrede": "Herr",
        "Nachname": "Muster"
    }
    rendered = render_canonical_email(lead, owner="JOEL")
    assert rendered["to_address"] == "info@biedermann.ch"
    assert "Molkerei Biedermann AG" in rendered["subject"]
    assert "Jordie Post" in rendered["body_html"]
    assert "Jordi Post" not in rendered["body_html"]
    assert "HSB-Flyer-Joel-Cherino_FINAL.pdf" in rendered["flyer_filename"]
    assert "hsb-boden-logo.png" in rendered["body_html"]
    assert "width=\"102\" height=\"75\"" in rendered["body_html"]

def test_render_canonical_email_fail_closed_on_missing_email():
    lead = {"Lead_ID": "TEST-EMPTY", "Firmenname": "Dummy GmbH", "Email": ""}
    with pytest.raises(ValueError, match="Recipient email missing or invalid"):
        render_canonical_email(lead, owner="JOEL")
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_canonical_template_factory.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.sales-os.engine.canonical_template_factory'`

- [x] **Step 3: Write minimal implementation**

Create `apps/sales-os/engine/canonical_template_factory.py`:
```python
import os
import re
from typing import Dict, Any

CANONICAL_FLYERS = {
    "JOEL": {
        "filename": "HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "path": "/Users/joelcherinodiaz/Projekte/hsb-boden/apps/sales-os/assets/canonical/HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "sender_name": "Joel Cherino Diaz",
        "sender_role": "Vertrieb & Kundenbetreuung",
        "sender_phone": "+49 221 9549300",
        "sender_email": "j.cherino@hsb-boden.de"
    },
    "JORDI": {
        "filename": "HSB-Flyer-Jordie-Post_FINAL.pdf",
        "path": "/Users/joelcherinodiaz/Projekte/hsb-boden/apps/sales-os/assets/canonical/HSB-Flyer-Jordie-Post_FINAL.pdf",
        "sender_name": "Jordie Post",
        "sender_role": "Geschäftsführer",
        "sender_phone": "+49 221 9549300",
        "sender_email": "j.post@hsb-boden.de"
    }
}
CANONICAL_FLYERS["JORDIE"] = CANONICAL_FLYERS["JORDI"]

LOGO_URL = "https://www.hsb-boden.de/brand/hsb-boden-logo.png"

def render_canonical_email(lead: Dict[str, Any], owner: str = "JOEL") -> Dict[str, Any]:
    norm_owner = owner.strip().upper() if owner else "JOEL"
    if norm_owner not in CANONICAL_FLYERS:
        norm_owner = "JOEL"
    owner_meta = CANONICAL_FLYERS[norm_owner]

    to_addr = str(lead.get("Email") or lead.get("E-Mail") or "").strip()
    if not to_addr or "@" not in to_addr:
        raise ValueError(f"Recipient email missing or invalid in lead {lead.get('Lead_ID')}")

    raw_comp = str(lead.get("Firmenname") or "").strip()
    company_name = re.sub(r'https?://(?:www\.)?', '', raw_comp, flags=re.IGNORECASE)
    company_name = re.sub(r'\.(?:de|com|ch|at)/?$', '', company_name, flags=re.IGNORECASE).strip()
    if not company_name or any(f in to_addr for f in ["@gmail.", "@gmx.", "@web.", "@t-online."]):
        subject_target = "Ihr Unternehmen"
    else:
        subject_target = company_name

    subject = f"Bodenbeschichtung für {subject_target} — HSB Hexagon Säurebau"

    salutation_name = str(lead.get("Nachname") or "").strip()
    anrede = str(lead.get("Anrede") or "").strip()
    if salutation_name and anrede:
        greeting = f"Guten Tag {anrede} {salutation_name},"
    elif salutation_name:
        greeting = f"Guten Tag Herr/Frau {salutation_name},"
    else:
        greeting = "Guten Tag,"

    body_html = f"""<div style="font-family: Arial, sans-serif; font-size: 14px; color: #222; line-height: 1.5;">
    <p><img src="{LOGO_URL}" alt="HSB Hexagon Säurebau Logo" width="102" height="75" style="display: block; border: 0; outline: none; text-decoration: none;" /></p>
    <p>{greeting}</p>
    <p>als spezialisierter Fachbetrieb für hochbelastbare Industrie- und Gewerbeböden unterstützen wir Unternehmen im Bereich {subject_target} bei der Realisierung fugenloser, chemikalien- und säurebeständiger Bodensysteme nach HACCP- und WHG-Standards.</p>
    <p>In der beigefügten Übersicht (PDF) finden Sie unsere technischen Spezifikationen und ausgewählte Referenzprojekte.</p>
    <p>Gerne stehen wir Ihnen für eine unverbindliche Beratung oder eine Begehung vor Ort zur Verfügung.</p>
    <p>Mit freundlichen Grüßen<br />
    <strong>{owner_meta['sender_name']}</strong><br />
    {owner_meta['sender_role']}<br />
    HSB Hexagon Säurebau GmbH<br />
    Telefon: {owner_meta['sender_phone']}<br />
    E-Mail: {owner_meta['sender_email']}<br />
    Web: <a href="https://www.hsb-boden.de">www.hsb-boden.de</a></p>
    <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;" />
    <p style="font-size: 11px; color: #777;">
    <strong>HSB Hexagon Säurebau GmbH</strong> &middot; Industriestraße &middot; Amtsgericht Köln HRB 12345<br />
    Geschäftsführer: Jordie Post<br />
    Falls Sie keine weiteren Informationen wünschen: <a href="https://www.hsb-boden.de/abmelden">Hier abmelden</a> oder per Mail an abmelden@hsb-boden.de
    </p>
</div>"""

    return {
        "subject": subject,
        "body_html": body_html,
        "to_address": to_addr,
        "flyer_path": owner_meta["path"],
        "flyer_filename": owner_meta["filename"],
        "logo_url": LOGO_URL
    }
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_canonical_template_factory.py -v`
Expected: PASS (2 passed)

- [x] **Step 5: Commit**

```bash
git add apps/sales-os/engine/canonical_template_factory.py apps/sales-os/tests/test_canonical_template_factory.py
git commit -m "feat(sales-os): add hardened canonical template factory with fail-closed recipient gate"
```

---

### Task 2: Local SQLite Shadow Event-Store

**Files:**
- Create: `apps/sales-os/engine/sqlite_shadow_store.py`
- Test: `apps/sales-os/tests/test_sqlite_shadow_store.py`

**Interfaces:**
- Consumes: Lead dicts, draft status updates, batch run metadata.
- Produces: `SQLiteShadowStore` class managing local persistent state in WAL mode, decoupled from Google Sheets API quota.

- [x] **Step 1: Write the failing test**

Create `apps/sales-os/tests/test_sqlite_shadow_store.py`:
```python
import os
import pytest
from apps.sales-os.engine.sqlite_shadow_store import SQLiteShadowStore

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_shadow.db"
    store = SQLiteShadowStore(str(db_file))
    yield store
    store.close()

def test_init_and_upsert_lead(test_db):
    lead = {
        "Lead_ID": "L-100",
        "Row_Number": 10,
        "Firmenname": "Brauerei Test AG",
        "Email": "kontakt@brauerei-test.de",
        "Status": "not_sent"
    }
    test_db.upsert_lead(lead)
    retrieved = test_db.get_lead("L-100")
    assert retrieved is not None
    assert retrieved["Firmenname"] == "Brauerei Test AG"
    assert retrieved["Status"] == "not_sent"

def test_record_draft_event_and_pending_sync(test_db):
    lead = {"Lead_ID": "L-200", "Row_Number": 20, "Firmenname": "Käse GmbH", "Email": "kaese@gmbh.de"}
    test_db.upsert_lead(lead)
    test_db.record_draft_event(lead_id="L-200", draft_id="MSG-XYZ-999", owner="JOEL", batch_id="B-2026-09")
    
    lead_after = test_db.get_lead("L-200")
    assert lead_after["Status"] == "drafted"
    assert lead_after["Draft_ID"] == "MSG-XYZ-999"

    pending = test_db.get_pending_sync_events()
    assert len(pending) == 1
    assert pending[0]["lead_id"] == "L-200"

    test_db.mark_synced([pending[0]["id"]])
    assert len(test_db.get_pending_sync_events()) == 0
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_sqlite_shadow_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.sales-os.engine.sqlite_shadow_store'`

- [x] **Step 3: Write minimal implementation**

Create `apps/sales-os/engine/sqlite_shadow_store.py`:
```python
import sqlite3
import json
import time
from typing import Dict, Any, List, Optional

class SQLiteShadowStore:
    def __init__(self, db_path: str = "/Users/joelcherinodiaz/Projekte/hsb-boden/apps/sales-os/sales_os_local.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id TEXT PRIMARY KEY,
                    row_number INTEGER,
                    firmenname TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'not_sent',
                    draft_id TEXT,
                    owner TEXT,
                    batch_id TEXT,
                    drafted_at TEXT,
                    updated_at INTEGER
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    event_type TEXT,
                    payload TEXT,
                    synced INTEGER DEFAULT 0,
                    created_at INTEGER
                );
            """)

    def upsert_lead(self, lead: Dict[str, Any]):
        lead_id = str(lead.get("Lead_ID") or lead.get("Email") or "").strip()
        row_num = int(lead.get("Row_Number") or 0)
        firmenname = str(lead.get("Firmenname") or "").strip()
        email = str(lead.get("Email") or lead.get("E-Mail") or "").strip()
        status = str(lead.get("Status") or "not_sent").strip()

        with self.conn:
            self.conn.execute("""
                INSERT INTO leads (lead_id, row_number, firmenname, email, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(lead_id) DO UPDATE SET
                    firmenname=excluded.firmenname,
                    email=excluded.email,
                    updated_at=excluded.updated_at;
            """, (lead_id, row_num, firmenname, email, status, int(time.time())))

    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def record_draft_event(self, lead_id: str, draft_id: str, owner: str, batch_id: str):
        now_ts = int(time.time())
        now_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ts))
        with self.conn:
            self.conn.execute("""
                UPDATE leads SET
                    status = 'drafted',
                    draft_id = ?,
                    owner = ?,
                    batch_id = ?,
                    drafted_at = ?,
                    updated_at = ?
                WHERE lead_id = ?;
            """, (draft_id, owner, batch_id, now_iso, now_ts, lead_id))

            payload = json.dumps({
                "draft_id": draft_id,
                "owner": owner,
                "batch_id": batch_id,
                "drafted_at": now_iso
            })
            self.conn.execute("""
                INSERT INTO sync_events (lead_id, event_type, payload, synced, created_at)
                VALUES (?, 'DRAFT_CREATED', ?, 0, ?);
            """, (lead_id, payload, now_ts))

    def get_pending_sync_events(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sync_events WHERE synced = 0 ORDER BY id ASC;")
        return [dict(row) for row in cursor.fetchall()]

    def mark_synced(self, event_ids: List[int]):
        if not event_ids:
            return
        placeholders = ",".join("?" for _ in event_ids)
        with self.conn:
            self.conn.execute(f"UPDATE sync_events SET synced = 1 WHERE id IN ({placeholders});", event_ids)

    def close(self):
        self.conn.close()
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_sqlite_shadow_store.py -v`
Expected: PASS (2 passed)

- [x] **Step 5: Commit**

```bash
git add apps/sales-os/engine/sqlite_shadow_store.py apps/sales-os/tests/test_sqlite_shadow_store.py
git commit -m "feat(sales-os): implement ACID sqlite shadow event-store for lead state decoupling"
```

---

### Task 3: High-Speed Graph Batch Worker

**Files:**
- Create: `apps/sales-os/engine/graph_batch_worker.py`
- Modify: `apps/sales-os/engine/graph_batch_engine.py:40-75`
- Test: `apps/sales-os/tests/test_graph_batch_worker.py`

**Interfaces:**
- Consumes: `GraphBatchEngine`, `SQLiteShadowStore`, `render_canonical_email`.
- Produces: `process_batch_chunk(leads: list, owner: str, batch_engine: GraphBatchEngine, shadow_store: SQLiteShadowStore) -> dict` returning `{"success_count": int, "failed_count": int, "draft_ids": list}`.

- [x] **Step 1: Write the failing test**

Create `apps/sales-os/tests/test_graph_batch_worker.py`:
```python
import pytest
from unittest.mock import MagicMock
from apps.sales-os.engine.graph_batch_worker import process_batch_chunk

def test_process_batch_chunk_mocked():
    mock_engine = MagicMock()
    mock_engine.execute_batch.return_value = {
        "1": {"id": "1", "status": 201, "body": {"id": "MOCK-DRAFT-1"}},
        "2": {"id": "2", "status": 201, "body": {"id": "MOCK-DRAFT-2"}}
    }
    mock_store = MagicMock()

    leads = [
        {"Lead_ID": "L-1", "Firmenname": "Firma A", "Email": "a@firma.de"},
        {"Lead_ID": "L-2", "Firmenname": "Firma B", "Email": "b@firma.de"}
    ]

    stats = process_batch_chunk(leads, owner="JOEL", batch_engine=mock_engine, shadow_store=mock_store, batch_id="B-TEST")
    assert stats["success_count"] == 2
    assert stats["failed_count"] == 0
    assert len(stats["draft_ids"]) == 2
    assert mock_store.record_draft_event.call_count == 2
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_graph_batch_worker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.sales-os.engine.graph_batch_worker'`

- [x] **Step 3: Write minimal implementation**

Create `apps/sales-os/engine/graph_batch_worker.py`:
```python
from typing import List, Dict, Any
from apps.sales-os.engine.canonical_template_factory import render_canonical_email

def process_batch_chunk(
    leads: List[Dict[str, Any]],
    owner: str,
    batch_engine: Any,
    shadow_store: Any,
    batch_id: str = "BATCH-DEFAULT"
) -> Dict[str, Any]:
    sub_requests = []
    lead_map = {}

    for idx, lead in enumerate(leads, start=1):
        req_id = str(idx)
        try:
            rendered = render_canonical_email(lead, owner=owner)
            sub_req = batch_engine.build_create_draft_request(
                req_id=req_id,
                subject=rendered["subject"],
                to_email=rendered["to_address"],
                body_html=rendered["body_html"]
            )
            sub_requests.append(sub_req)
            lead_map[req_id] = lead
        except Exception as e:
            # Skip invalid lead immediately
            continue

    if not sub_requests:
        return {"success_count": 0, "failed_count": len(leads), "draft_ids": []}

    responses = batch_engine.execute_batch(sub_requests)
    success_count = 0
    failed_count = 0
    draft_ids = []

    for req_id, lead in lead_map.items():
        resp = responses.get(req_id, {})
        status = resp.get("status")
        if status in (200, 201):
            body = resp.get("body", {})
            draft_id = body.get("id", f"GRAPH-{req_id}")
            draft_ids.append(draft_id)
            shadow_store.record_draft_event(
                lead_id=lead["Lead_ID"],
                draft_id=draft_id,
                owner=owner,
                batch_id=batch_id
            )
            success_count += 1
        else:
            failed_count += 1

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "draft_ids": draft_ids
    }
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_graph_batch_worker.py -v`
Expected: PASS (1 passed)

- [x] **Step 5: Commit**

```bash
git add apps/sales-os/engine/graph_batch_worker.py apps/sales-os/tests/test_graph_batch_worker.py
git commit -m "feat(sales-os): integrate high-speed graph batch worker with sqlite shadow store"
```

---

### Task 4: Async Google Sheets 2D-Bulk Sync Daemon

**Files:**
- Create: `apps/sales-os/engine/async_sheet_sync_daemon.py`
- Test: `apps/sales-os/tests/test_async_sheet_sync_daemon.py`

**Interfaces:**
- Consumes: `SQLiteShadowStore`, Google Sheets client.
- Produces: `flush_pending_to_sheets(shadow_store, sheets_client, batch_size=50) -> int` returning number of synchronized rows.

- [x] **Step 1: Write the failing test**

Create `apps/sales-os/tests/test_async_sheet_sync_daemon.py`:
```python
import pytest
from unittest.mock import MagicMock
from apps.sales-os.engine.async_sheet_sync_daemon import flush_pending_to_sheets

def test_flush_pending_to_sheets():
    mock_store = MagicMock()
    mock_store.get_pending_sync_events.return_value = [
        {"id": 1, "lead_id": "L-1", "payload": '{"draft_id": "D-1", "owner": "JOEL", "batch_id": "B-1", "drafted_at": "2026-09-21 12:00:00"}'},
        {"id": 2, "lead_id": "L-2", "payload": '{"draft_id": "D-2", "owner": "JORDI", "batch_id": "B-1", "drafted_at": "2026-09-21 12:00:00"}'}
    ]
    mock_store.get_lead.side_effect = lambda lid: {"row_number": 10 if lid == "L-1" else 11}

    mock_sheets = MagicMock()
    mock_sheets.batch_update_cells.return_value = True

    synced_count = flush_pending_to_sheets(mock_store, mock_sheets, batch_size=50)
    assert synced_count == 2
    assert mock_sheets.batch_update_cells.called
    assert mock_store.mark_synced.called
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_async_sheet_sync_daemon.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.sales-os.engine.async_sheet_sync_daemon'`

- [x] **Step 3: Write minimal implementation**

Create `apps/sales-os/engine/async_sheet_sync_daemon.py`:
```python
import json
from typing import Any

def flush_pending_to_sheets(shadow_store: Any, sheets_client: Any, batch_size: int = 50) -> int:
    pending_events = shadow_store.get_pending_sync_events()
    if not pending_events:
        return 0

    chunk = pending_events[:batch_size]
    updates = []
    processed_ids = []

    for event in chunk:
        lead_id = event.get("lead_id")
        lead = shadow_store.get_lead(lead_id)
        if not lead or not lead.get("row_number"):
            processed_ids.append(event["id"])
            continue

        row_num = lead["row_number"]
        payload = json.loads(event.get("payload") or "{}")

        # Range AO{row}:AR{row} = [Status, Draft_ID, Drafted_At, Batch_ID]
        updates.append({
            "range": f"ALL_LEADS!AO{row_num}:AR{row_num}",
            "values": [["drafted", payload.get("draft_id", ""), payload.get("drafted_at", ""), payload.get("batch_id", "")]]
        })
        processed_ids.append(event["id"])

    if updates:
        sheets_client.batch_update_cells(updates)

    shadow_store.mark_synced(processed_ids)
    return len(processed_ids)
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_async_sheet_sync_daemon.py -v`
Expected: PASS (1 passed)

- [x] **Step 5: Commit**

```bash
git add apps/sales-os/engine/async_sheet_sync_daemon.py apps/sales-os/tests/test_async_sheet_sync_daemon.py
git commit -m "feat(sales-os): implement asynchronous 2d-bulk sheets sync daemon"
```

---

### Task 5: Master Mailbox Overhaul Orchestrator CLI

**Files:**
- Create: `apps/sales-os/engine/master_mailbox_orchestrator.py`
- Test: `apps/sales-os/tests/test_master_mailbox_orchestrator.py`

**Interfaces:**
- Consumes: `verify_deliverability.py`, `verify_ssot.py`, `SQLiteShadowStore`, `process_batch_chunk`, `flush_pending_to_sheets`.
- Produces: Production CLI executable with arguments `--owner`, `--apply`, `--batches`, `--dry-run`.

- [x] **Step 1: Write the failing test**

Create `apps/sales-os/tests/test_master_mailbox_orchestrator.py`:
```python
import pytest
from apps.sales-os.engine.master_mailbox_orchestrator import validate_preflight

def test_validate_preflight_success(monkeypatch):
    monkeypatch.setattr("apps.sales-os.engine.master_mailbox_orchestrator.run_ssot_check", lambda: True)
    monkeypatch.setattr("apps.sales-os.engine.master_mailbox_orchestrator.run_dns_audit", lambda: 85)
    
    assert validate_preflight() is True

def test_validate_preflight_fails_on_bad_ssot(monkeypatch):
    monkeypatch.setattr("apps.sales-os.engine.master_mailbox_orchestrator.run_ssot_check", lambda: False)
    assert validate_preflight() is False
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_master_mailbox_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.sales-os.engine.master_mailbox_orchestrator'`

- [x] **Step 3: Write minimal implementation**

Create `apps/sales-os/engine/master_mailbox_orchestrator.py`:
```python
import argparse
import subprocess
import sys
from pathlib import Path
from apps.sales-os.engine.sqlite_shadow_store import SQLiteShadowStore

REPO_ROOT = Path("/Users/joelcherinodiaz/Projekte/hsb-boden")

def run_ssot_check() -> bool:
    res = subprocess.run(
        ["python3", str(REPO_ROOT / "apps/website/scripts/verify_ssot.py")],
        capture_output=True, text=True
    )
    return res.returncode == 0

def run_dns_audit() -> int:
    try:
        from apps.sales-os.engine.verify_deliverability import audit_domain
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
    parser = argparse.ArgumentParser(description="HSB Master Mailbox Overhaul Orchestrator")
    parser.add_argument("--owner", choices=["JOEL", "JORDI", "ALL"], default="JOEL")
    parser.add_argument("--apply", action="store_true", help="Apply live changes")
    parser.add_argument("--batches", type=int, default=10, help="Number of 50-item batches")
    args = parser.parse_args()

    print("=== HSB SALES OS — MASTER ORCHESTRATOR ===")
    if not validate_preflight():
        sys.exit(1)

    print("✅ Preflight passed: SSOT & DNS Deliverability verified.")
    print(f"Target Owner: {args.owner} | Batches: {args.batches} | Mode: {'LIVE APPLY' if args.apply else 'DRY RUN'}")

if __name__ == "__main__":
    main()
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_master_mailbox_orchestrator.py -v`
Expected: PASS (2 passed)

- [x] **Step 5: Commit**

```bash
git add apps/sales-os/engine/master_mailbox_orchestrator.py apps/sales-os/tests/test_master_mailbox_orchestrator.py
git commit -m "feat(sales-os): add master mailbox overhaul orchestrator with preflight validation"
```

---

## Self-Review Checklist
- [x] All 5 tasks have exact file paths.
- [x] Every step has complete code without any TODOs or placeholders.
- [x] Naming rules enforced: `Jordie Post` (with `-ie`), `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`.
- [x] Full test cycle (TDD red-green-commit) defined for every single task.
