# apps/sales-os/engine/lead_quality.py
"""Listenhygiene: DSN-Klassifikation und Zustellbarkeits-Flags (ohne SMTP-RCPT-Probing)."""
from __future__ import annotations

import re
from collections import Counter
from typing import Callable, Iterable, Literal

DsnClass = Literal["hard", "soft", "policy", "unknown"]

FLAG_NO_MX = "NO_MX"
FLAG_SYNTAX_INVALID = "SYNTAX_INVALID"
FLAG_ROLE_NOREPLY = "ROLE_NOREPLY"
FLAG_PREVIOUS_HARD_BOUNCE = "PREVIOUS_HARD_BOUNCE"
FLAG_DOMAIN_BOUNCED_BEFORE = "DOMAIN_BOUNCED_BEFORE"

# Warnung: verändert die Zulässigkeit nicht (siehe hsb_core.check_eligibility).
WARNING_FLAGS = frozenset({FLAG_DOMAIN_BOUNCED_BEFORE})

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$")
_NOREPLY_RE = re.compile(r"^(no[-_.]?reply|do[-_.]?not[-_.]?reply|mailer-daemon|postmaster|bounce[s]?)$", re.I)
_POLICY_RE = re.compile(r"\b5\.7\.\d+\b|spam|blocklist|blacklist|policy|blocked|rejected as", re.I)
_SOFT_RE = re.compile(r"\b4\.\d+\.\d+\b|\b452\b|\b5\.2\.2\b|mailbox full|over quota|try again|temporar", re.I)
_HARD_RE = re.compile(r"\b5\.1\.\d+\b|\b550\b|\b5\.\d+\.\d+\b|user unknown|no such user|unknown recipient|does not exist", re.I)


def classify_dsn(text: str) -> DsnClass:
    """Ordnet einen Bounce-Text ein: policy (5.7.x/Spam) vor soft (4.x.x/452) vor hard (5.1.x/550)."""
    if not text:
        return "unknown"
    if _POLICY_RE.search(text):
        return "policy"
    if _SOFT_RE.search(text):
        return "soft"
    if _HARD_RE.search(text):
        return "hard"
    return "unknown"


def _split_email(email: str) -> tuple[str, str]:
    local, _, domain = email.strip().lower().rpartition("@")
    return local, domain


def deliverability_flags(
    lead: dict,
    mx_cache: dict[str, bool],
    bounced_domains: set[str],
    mx_check: Callable[[str], bool] | None = None,
) -> list[str]:
    """Berechnet Zustellbarkeits-Flags. MX wird je Domain nur einmal geprüft (mx_cache)."""
    email = str(lead.get("Email") or lead.get("E-Mail") or "").strip()
    if not _EMAIL_RE.match(email):
        return [FLAG_SYNTAX_INVALID]

    flags: list[str] = []
    local, domain = _split_email(email)

    if domain not in mx_cache:
        if mx_check is None:
            from enrich_company_names import check_domain_mx as mx_check
        mx_cache[domain] = bool(mx_check(domain))
    if not mx_cache[domain]:
        flags.append(FLAG_NO_MX)

    if _NOREPLY_RE.match(local):
        flags.append(FLAG_ROLE_NOREPLY)

    if str(lead.get("Bounce_Status") or "").strip().lower() in {"hard_bounce", "hard", "hardbounce"}:
        flags.append(FLAG_PREVIOUS_HARD_BOUNCE)

    if domain in {d.lower() for d in bounced_domains}:
        flags.append(FLAG_DOMAIN_BOUNCED_BEFORE)
    return flags


def summarize_bounces(messages: Iterable) -> dict:
    """Zählt Bounces je DSN-Klasse und je Domain. Gibt nie Adressen zurück."""
    from inbound_classifier import classify_inbound_message

    by_class: Counter[str] = Counter()
    by_domain: Counter[str] = Counter()
    for msg in messages:
        cls = classify_inbound_message(msg.sender, msg.subject, msg.body)
        if cls.category != "BOUNCE":
            continue
        by_class[classify_dsn(msg.body)] += 1
        if cls.extracted_email and "@" in cls.extracted_email:
            by_domain[cls.extracted_email.rsplit("@", 1)[1].lower()] += 1
    return {"total": sum(by_class.values()), "by_class": dict(by_class), "by_domain": dict(by_domain)}
