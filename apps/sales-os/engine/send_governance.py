"""
HSB Sales OS - Send Governance & EOP Anti-Spam Queue Guardrails (G11).

Erzwingt:
1. Natuerlichen stochastischen Jitter: 45 bis 180 Sekunden zwischen E-Mails.
2. Physikalisches Tageslimit: Maximal 35 Mails/Tag pro Postfach.
3. Fail-closed Schutz: Blockiert strikt bei Cap-Erreichung.
"""
from __future__ import annotations

import datetime
import random
from typing import Dict, Optional, Tuple

MIN_JITTER_SECONDS: int = 45
MAX_JITTER_SECONDS: int = 180
DAILY_CAP_PER_MAILBOX: int = 35

REAL_EXTERNAL_PROSPECT_SEND_COUNT: int = 0


class DailyCapReachedError(RuntimeError):
    """Physikalisches Tageslimit pro Postfach erreicht (max. 35 Mails/Tag)."""


class SendGovernanceQueue:
    def __init__(
        self,
        min_jitter: int = MIN_JITTER_SECONDS,
        max_jitter: int = MAX_JITTER_SECONDS,
        daily_cap: int = DAILY_CAP_PER_MAILBOX
    ):
        self.min_jitter = min_jitter
        self.max_jitter = max_jitter
        self.daily_cap = daily_cap
        # mailbox -> { "YYYY-MM-DD": sent_count }
        self._sent_ledger: Dict[str, Dict[str, int]] = {}

    def get_jitter_delay(self) -> float:
        """Erzeugt eine gleichverteilte Pseudozufalls-Verzoegerung im Korridor [45s, 180s]."""
        return random.uniform(self.min_jitter, self.max_jitter)

    def can_send(self, mailbox: str, target_date: Optional[datetime.date] = None) -> Tuple[bool, int, int]:
        """Prueft, ob das Postfach am gegebenen Tag noch Sende-Quota besitzt."""
        if target_date is None:
            target_date = datetime.date.today()
        date_str = target_date.isoformat()
        current_count = self._sent_ledger.get(mailbox, {}).get(date_str, 0)
        remaining = max(0, self.daily_cap - current_count)
        return (current_count < self.daily_cap), current_count, remaining

    def queue_send(
        self,
        mailbox: str,
        prospect_email: str,
        target_date: Optional[datetime.date] = None
    ) -> dict:
        """
        Enqueuet eine E-Mail mit berechneter Jitter-Verzoegerung und aktualisiert den Tageszaehler.
        Wirft DailyCapReachedError, wenn das Tageslimit erreicht ist.
        """
        if target_date is None:
            target_date = datetime.date.today()
        date_str = target_date.isoformat()

        allowed, current_count, remaining = self.can_send(mailbox, target_date)
        if not allowed:
            raise DailyCapReachedError(
                f"Tageslimit fuer {mailbox} am {date_str} erschoepft: "
                f"{current_count}/{self.daily_cap} versendet. Abbruch."
            )

        jitter = self.get_jitter_delay()

        # Buchung im Tages-Ledger
        if mailbox not in self._sent_ledger:
            self._sent_ledger[mailbox] = {}
        self._sent_ledger[mailbox][date_str] = current_count + 1

        return {
            "status": "QUEUED",
            "mailbox": mailbox,
            "prospect_email": prospect_email,
            "date": date_str,
            "jitter_delay_seconds": jitter,
            "day_sequence_number": current_count + 1,
            "remaining_today": remaining - 1,
        }
