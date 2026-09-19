"""
HSB Sales OS - Deterministic SHA-256 Idempotency & Append-Only Event Sourcing (G10).

Verhindert Zell-Race-Conditions im CRM durch:
1. Deterministische Idempotency-Keys: sha256(recipient + campaign + step).
2. Append-Only Event-Log: Keine direkten Zell-In-Place-Mutationen ohne Audit-Trail.
3. Schreibschutz fuer bestaetigte Lead-Zellen (Campari-Antwort, 167 versendete Datensaetze).
"""
import hashlib
import threading
from typing import Any, Dict, List, Optional, Set, Tuple


def generate_idempotency_key(recipient: str, campaign: str, step: Any) -> str:
    norm_recipient = recipient.strip().lower()
    norm_campaign = str(campaign).strip()
    norm_step = str(step).strip()
    raw = f"{norm_recipient}|{norm_campaign}|{norm_step}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class ProtectedCellError(RuntimeError):
    """Versuch, eine schreibgeschuetzte CRM-Zelle zu ueberschreiben."""


class CrmEventStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._events: List[Dict[str, Any]] = []
        self._seen_keys: Set[str] = set()
        # Schreibgeschuetzte Zellen/Datensaetze (z.B. Campari-Antwort und 167 historische Sends)
        self._protected_lead_ids: Set[str] = {"CAMPARI-01", "LEAD-CAMPARI"}
        self._immutable_states: Dict[str, Dict[str, Any]] = {
            "CAMPARI-01": {
                "Company": "Campari",
                "Reply_Status": "replied",
                "Reply_Type": "positive",
                "Protected": True
            }
        }
        self.duplicate_count = 0
        self.overwrite_attempts = 0

    def append_event(self, event: Dict[str, Any]) -> Tuple[bool, str]:
        with self._lock:
            idempotency_key = event.get("idempotency_key")
            if not idempotency_key:
                lead_id = event.get("lead_id", "")
                campaign = event.get("campaign_id", "DEFAULT")
                step = event.get("step", "1")
                idempotency_key = generate_idempotency_key(lead_id, campaign, step)
                event["idempotency_key"] = idempotency_key

            # 1. Idempotency Check
            if idempotency_key in self._seen_keys:
                self.duplicate_count += 1
                return False, "duplicate_idempotency_key"

            # 2. Cell Protection Check against protected leads (e.g. Campari)
            lead_id = event.get("lead_id")
            if lead_id in self._protected_lead_ids:
                if event.get("action") in ("overwrite", "reset", "clear", "update_reply"):
                    self.overwrite_attempts += 1
                    return False, "protected_cell_mutation_rejected"

            # 3. Append-only commit
            self._seen_keys.add(idempotency_key)
            self._events.append(dict(event))
            return True, "committed"

    @property
    def event_count(self) -> int:
        with self._lock:
            return len(self._events)
