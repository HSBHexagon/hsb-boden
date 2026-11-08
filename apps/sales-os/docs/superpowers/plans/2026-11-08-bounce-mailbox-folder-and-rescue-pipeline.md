# Bounce Mailbox Folder & Autonomous Impressum Rescue Pipeline Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the operator mailboxes by moving bounced emails into an `Unzustellbar` IMAP subfolder and automatically resolve replacement email addresses from company websites/impressum using the existing SSRF-hardened `BounceRescueAgent`.

**Architecture:** Extend `ComMailboxClient` with idempotent IMAP folder creation and UID message movement. Integrate `BounceRescueAgent` into `ingest_bounces.py` and `hsb_cli.py` to inspect bounced leads, scrape `/impressum` and `/kontakt` for alternative emails (e.g. `info@`), verify their DNS MX records, and register the candidates into the CRM Google Sheet (`ALL_LEADS`).

**Tech Stack:** Python 3.12/3.14 (`imaplib`, `urllib`, `socket`, `google-api-python-client`), Google Sheets API, Pytest.

## Global Constraints
- `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` strictly enforced during ingestion and rescue (pure read/search/CRM update).
- No new external dependencies; reuse existing standard library and `bounce_rescue_agent.py`.
- SSRF prevention: All website calls must strictly route through `is_public_hostname` and `_PublicHTTPSHandler`.
- Idempotency: Mail moves and sheet updates must be replay-safe and non-destructive.

---

### Task 1: Add IMAP Folder Management and Message Movement to `ComMailboxClient`

**Files:**
- Modify: `apps/sales-os/engine/com_mailbox_manager.py`
- Test: `apps/sales-os/tests/test_bounce_mailbox_folder.py`

**Interfaces:**
- Consumes: `ComMailboxClient.connect_imap()`
- Produces: 
  - `ComMailboxClient.ensure_folder(folder_name: str) -> bool`
  - `ComMailboxClient.move_message_by_uid(uid: str, source_folder: str, target_folder: str) -> bool`

- [ ] **Step 1: Write the failing unit test**

```python
# apps/sales-os/tests/test_bounce_mailbox_folder.py
import pytest
from unittest.mock import MagicMock, patch
from com_mailbox_manager import ComMailboxClient

def test_ensure_folder_creates_when_missing():
    client = ComMailboxClient("JOEL")
    mock_imap = MagicMock()
    mock_imap.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "INBOX"'])
    mock_imap.create.return_value = ("OK", [b'Success'])
    
    with patch.object(client, "connect_imap", return_value=mock_imap):
        res = client.ensure_folder("Unzustellbar")
        assert res is True
        mock_imap.create.assert_called_once_with('"Unzustellbar"')

def test_move_message_by_uid():
    client = ComMailboxClient("JORDI")
    mock_imap = MagicMock()
    mock_imap.select.return_value = ("OK", [b'1'])
    mock_imap.uid.side_effect = [
        ("OK", [b'Copy OK']),   # COPY
        ("OK", [b'Flags OK']),  # STORE +FLAGS (\Deleted)
        ("OK", [b'Expunge OK']) # EXPUNGE
    ]
    with patch.object(client, "connect_imap", return_value=mock_imap), \
         patch.object(client, "ensure_folder", return_value=True):
        res = client.move_message_by_uid("12345", source_folder="INBOX", target_folder="Unzustellbar")
        assert res is True
        mock_imap.uid.assert_any_call("COPY", "12345", '"Unzustellbar"')
        mock_imap.uid.assert_any_call("STORE", "12345", "+FLAGS", "(\\Deleted)")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_bounce_mailbox_folder.py -v`
Expected: FAIL (`AttributeError: 'ComMailboxClient' object has no attribute 'ensure_folder'`)

- [ ] **Step 3: Implement `ensure_folder` and `move_message_by_uid` in `com_mailbox_manager.py`**

```python
    def ensure_folder(self, folder_name: str) -> bool:
        """Stellt sicher, dass ein IMAP-Ordner existiert (z. B. 'Unzustellbar')."""
        folder_clean = folder_name.strip('"')
        imap = self.connect_imap()
        typ, folders = imap.list()
        existing = [f.decode(errors='ignore').split(' "/" ')[-1].strip(' "') for f in (folders or [])]
        if folder_clean in existing:
            return True
        typ, res = imap.create(f'"{folder_clean}"')
        return typ == "OK"

    def move_message_by_uid(self, uid: str, source_folder: str = "INBOX", target_folder: str = "Unzustellbar") -> bool:
        """Verschiebt eine Nachricht per UID atomar in einen Zielordner."""
        if not self.ensure_folder(target_folder):
            return False
        imap = self.connect_imap()
        imap.select(source_folder, readonly=False)
        typ, res = imap.uid("COPY", str(uid), f'"{target_folder.strip(\'"\')}"')
        if typ != "OK":
            return False
        imap.uid("STORE", str(uid), "+FLAGS", "(\\Deleted)")
        imap.expunge()
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_bounce_mailbox_folder.py -v`
Expected: PASS

---

### Task 2: Move Bounces to `Unzustellbar` Folder in `ingest_bounces.py`

**Files:**
- Modify: `apps/sales-os/engine/ingest_bounces.py:150-185`
- Test: `apps/sales-os/tests/test_ingest_bounces_move.py`

**Interfaces:**
- Consumes: `ComMailboxClient.move_message_by_uid`
- Produces: `scan_com_mailbox_for_bounces(..., move_bounces=True)`

- [ ] **Step 1: Write test for bounce movement during scan**

```python
# apps/sales-os/tests/test_ingest_bounces_move.py
from unittest.mock import MagicMock, patch
from ingest_bounces import scan_com_mailbox_for_bounces

def test_scan_com_mailbox_moves_bounces():
    mock_client = MagicMock()
    mock_client.fetch_inbound_messages.return_value = [{
        "id": "999",
        "subject": "Undelivered Mail Returned to Sender",
        "body": "Diagnostic-Code: smtp; 550 5.1.1 User unknown <alt@firma.de>",
        "from": "mailer-daemon@kasserver.com",
        "date_str": "Sun, 08 Nov 2026 06:00:00 +0100"
    }]
    with patch("ingest_bounces.ComMailboxClient", return_value=mock_client):
        bounces = scan_com_mailbox_for_bounces("JOEL", limit=10, move_bounces=True)
        assert len(bounces) == 1
        mock_client.move_message_by_uid.assert_called_once_with("999", source_folder="INBOX", target_folder="Unzustellbar")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_ingest_bounces_move.py -v`
Expected: FAIL (`unexpected keyword argument 'move_bounces'`)

- [ ] **Step 3: Update `scan_com_mailbox_for_bounces` in `ingest_bounces.py`**

Add parameter `move_bounces: bool = False`. If True and `is_bounce` is True, call `client.move_message_by_uid(m["id"], "INBOX", "Unzustellbar")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_ingest_bounces_move.py -v`
Expected: PASS

---

### Task 3: Integrate Autonomous Impressum Rescue Pipeline in `hsb_cli.py`

**Files:**
- Modify: `apps/sales-os/engine/hsb_cli.py`
- Modify: `apps/sales-os/engine/bounce_rescue_agent.py`
- Test: `apps/sales-os/tests/test_bounce_rescue_integration.py`

**Interfaces:**
- Consumes: `BounceRescueAgent.rescue_lead()`, `get_sheets_service()`
- Produces: `cmd_bounce_rescue(args)` CLI action

- [ ] **Step 1: Write integration test for bounce rescue CLI command**

```python
# apps/sales-os/tests/test_bounce_rescue_integration.py
from unittest.mock import MagicMock, patch
from hsb_cli import cmd_bounce_rescue
from bounce_rescue_agent import RescueResult

def test_cmd_bounce_rescue_updates_sheet():
    mock_svc = MagicMock()
    mock_svc.spreadsheets().values().get().execute.return_value = {
        "values": [
            ["Lead-ID", "Firma", "E-Mail", "Website", "Bounce_Status", "Notizen"],
            ["HSB-001", "Test GmbH", "tot@test.de", "https://test.de", "hard_bounce", ""]
        ]
    }
    mock_agent = MagicMock()
    mock_agent.rescue_lead.return_value = RescueResult(
        status="SUCCESS",
        failed_email="tot@test.de",
        rescued_email="info@test.de",
        company_name="Test GmbH",
        domain="test.de",
        source_url="https://test.de/impressum",
        confidence=0.95,
        notes="Alternative E-Mail im Impressum gefunden und MX verifiziert."
    )
    args = MagicMock(apply=True, limit=5)
    with patch("hsb_cli.get_sheets_service", return_value=mock_svc), \
         patch("hsb_cli.BounceRescueAgent", return_value=mock_agent):
        count = cmd_bounce_rescue(args)
        assert count == 1
        mock_svc.spreadsheets().values().batchUpdate.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/sales-os/tests/test_bounce_rescue_integration.py -v`
Expected: FAIL (`ImportError: cannot import name 'cmd_bounce_rescue' from 'hsb_cli'`)

- [ ] **Step 3: Implement `cmd_bounce_rescue` in `hsb_cli.py` and register parser**

```python
def cmd_bounce_rescue(args):
    """Sucht für gebouncte Leads nach Impressums-Alternativen und schreibt Kandidaten ins Sheet."""
    from bounce_rescue_agent import BounceRescueAgent
    from sync_to_google_sheet import get_sheets_service, SPREADSHEET_ID
    # Lese gebouncte Leads, rufe rescue_lead() auf und schreibe Kandidaten zurück
    # Setzt Bounce_Status='rescued_candidate' und dokumentiert Quelle in Notizen
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/sales-os/tests/test_bounce_rescue_integration.py -v`
Expected: PASS

---

### Task 4: SSOT Verification & End-to-End Suite

- [ ] **Step 1: Run `verify_ssot.py`**
- [ ] **Step 2: Run all unit tests**
- [ ] **Step 3: Commit and push changes to `main`**
