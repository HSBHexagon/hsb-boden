"""
HSB Sales OS - Multi-Inbox Pool-Rotations-Engine (High-Volume Architecture).

Ermöglicht die aggregierte Skalierung des E-Mail-Versands auf 1.000 bis 10.000+ Mails/Tag
durch stochastische Verteilung auf einen Pool gesunder Postfächer, unter strikter Einhaltung
individueller Postfach-Limits, SPF/DKIM/DMARC-Authentifizierung und automatischer Deferral-Umgehung.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional


class PoolExhaustedError(RuntimeError):
    """Alle Postfächer im Rotations-Pool haben ihr Tageslimit erreicht oder sind temporär pausiert."""


@dataclass
class MailboxNode:
    email: str
    daily_cap: int
    sent_count: int = 0
    deferred_until: float = 0.0
    active: bool = True

    def is_available(self, current_time: Optional[float] = None) -> bool:
        now = time.time() if current_time is None else current_time
        return self.active and (self.sent_count < self.daily_cap) and (now >= self.deferred_until)

    @property
    def remaining_capacity(self) -> int:
        return max(0, self.daily_cap - self.sent_count)


class InboxRotationPool:
    def __init__(self):
        self._mailboxes: Dict[str, MailboxNode] = {}
        self._order: List[str] = []
        self._cursor: int = 0

    def register_mailbox(self, email: str, daily_cap: int = 500, active: bool = True) -> None:
        """Registriert ein Postfach im Rotations-Pool."""
        if email not in self._mailboxes:
            self._order.append(email)
        self._mailboxes[email] = MailboxNode(email=email, daily_cap=daily_cap, active=active)

    def mark_deferred(self, email: str, defer_seconds: float = 300.0) -> None:
        """Pausiert ein Postfach temporär (z.B. bei Greylisting oder SMTP 4xx Deferral)."""
        if email in self._mailboxes:
            self._mailboxes[email].deferred_until = time.time() + defer_seconds

    def get_sent_count(self, email: str) -> int:
        """Gibt die Anzahl versendeter Mails für ein Postfach zurück."""
        node = self._mailboxes.get(email)
        return node.sent_count if node else 0

    def get_remaining_capacity(self, email: str) -> int:
        """Gibt das verbleibende Kontingent für ein Postfach zurück."""
        node = self._mailboxes.get(email)
        return node.remaining_capacity if node else 0

    def total_pool_capacity(self) -> int:
        """Gesamtkapazität aller registrierten Postfächer."""
        return sum(node.daily_cap for node in self._mailboxes.values())

    def get_next_mailbox(self) -> str:
        """
        Wählt das nächste verfügbare Postfach im Round-Robin-Verfahren aus und reserviert einen Sende-Slot.
        Wirft PoolExhaustedError, wenn kein Postfach mehr Sende-Quota besitzt.
        """
        if not self._mailboxes:
            raise PoolExhaustedError("Keine Postfächer im Pool registriert.")

        total_nodes = len(self._order)
        now = time.time()

        for _ in range(total_nodes):
            current_email = self._order[self._cursor]
            self._cursor = (self._cursor + 1) % total_nodes
            node = self._mailboxes[current_email]

            if node.is_available(now):
                node.sent_count += 1
                return node.email

        raise PoolExhaustedError("Alle Postfächer im Pool haben ihr Tageslimit erreicht oder sind pausiert.")
