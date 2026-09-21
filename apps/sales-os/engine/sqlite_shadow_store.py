import json
import sqlite3
import time
from typing import Any, Dict, List, Optional


class SQLiteShadowStore:
    def __init__(
        self,
        db_path: str = "/Users/joelcherinodiaz/Projekte/hsb-boden/apps/sales-os/sales_os_local.db",
    ):
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
        lead_id = str(
            lead.get("Lead_ID") or lead.get("lead_id") or lead.get("Email") or ""
        ).strip()
        row_num = int(lead.get("Row_Number") or lead.get("row_number") or 0)
        firmenname = str(lead.get("Firmenname") or lead.get("firmenname") or "").strip()
        email = str(
            lead.get("Email") or lead.get("email") or lead.get("E-Mail") or ""
        ).strip()
        status = str(lead.get("Status") or lead.get("status") or "not_sent").strip()

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO leads (lead_id, row_number, firmenname, email, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(lead_id) DO UPDATE SET
                    firmenname=excluded.firmenname,
                    email=excluded.email,
                    status=excluded.status,
                    updated_at=excluded.updated_at;
            """,
                (lead_id, row_num, firmenname, email, status, int(time.time())),
            )

    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["Lead_ID"] = res.get("lead_id")
        res["Row_Number"] = res.get("row_number")
        res["Firmenname"] = res.get("firmenname")
        res["Email"] = res.get("email")
        res["Status"] = res.get("status")
        res["Draft_ID"] = res.get("draft_id")
        res["Owner"] = res.get("owner")
        res["Batch_ID"] = res.get("batch_id")
        res["Drafted_At"] = res.get("drafted_at")
        return res

    def record_draft_event(
        self, lead_id: str, draft_id: str, owner: str, batch_id: str
    ):
        now_ts = int(time.time())
        now_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ts))
        with self.conn:
            self.conn.execute(
                """
                UPDATE leads SET
                    status = 'drafted',
                    draft_id = ?,
                    owner = ?,
                    batch_id = ?,
                    drafted_at = ?,
                    updated_at = ?
                WHERE lead_id = ?;
            """,
                (draft_id, owner, batch_id, now_iso, now_ts, lead_id),
            )

            payload = json.dumps(
                {
                    "draft_id": draft_id,
                    "owner": owner,
                    "batch_id": batch_id,
                    "drafted_at": now_iso,
                }
            )
            self.conn.execute(
                """
                INSERT INTO sync_events (lead_id, event_type, payload, synced, created_at)
                VALUES (?, 'DRAFT_CREATED', ?, 0, ?);
            """,
                (lead_id, payload, now_ts),
            )

    def get_pending_sync_events(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM sync_events WHERE synced = 0 ORDER BY id ASC;"
        )
        return [dict(row) for row in cursor.fetchall()]

    def mark_synced(self, event_ids: List[int]):
        if not event_ids:
            return
        placeholders = ",".join("?" for _ in event_ids)
        with self.conn:
            self.conn.execute(
                f"UPDATE sync_events SET synced = 1 WHERE id IN ({placeholders});",
                event_ids,
            )

    def close(self):
        self.conn.close()
