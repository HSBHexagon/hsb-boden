# apps/sales-os/engine/lead_quality.py
"""Listenhygiene: DSN-Klassifikation und Zustellbarkeits-Flags (ohne SMTP-RCPT-Probing)."""
from __future__ import annotations

import re
from collections import Counter
from typing import Callable, Iterable, Literal

from hsb_core import EMAIL_RE

DsnClass = Literal["hard", "soft", "policy", "unknown"]

FLAG_NO_MX = "NO_MX"
FLAG_SYNTAX_INVALID = "SYNTAX_INVALID"
FLAG_ROLE_NOREPLY = "ROLE_NOREPLY"
FLAG_PREVIOUS_HARD_BOUNCE = "PREVIOUS_HARD_BOUNCE"
FLAG_DOMAIN_BOUNCED_BEFORE = "DOMAIN_BOUNCED_BEFORE"

# Warnung: verändert die Zulässigkeit nicht (siehe hsb_core.check_eligibility).
WARNING_FLAGS = frozenset({FLAG_DOMAIN_BOUNCED_BEFORE})

_NOREPLY_RE = re.compile(r"^(no[-_.]?reply|do[-_.]?not[-_.]?reply|mailer-daemon|postmaster|bounce[s]?)$", re.I)

# Statuscode aus dem DSN, nie aus dem gesamten Text (IPs/Hostnamen/Versionen wuerden matchen).
_STATUS_RE = re.compile(r"^Status:\s*([245]\.\d{1,3}\.\d{1,3})\b", re.I | re.M)
_DIAG_RE = re.compile(r"^Diagnostic-Code:[^\n]*(?:\n[ \t]+[^\n]*)*", re.I | re.M)
_SMTP_LINE_RE = re.compile(r"^[ \t>]*([45]\d\d)[ -][ \t]*(?:([245]\.\d{1,3}\.\d{1,3})\b)?[^\n]*", re.M)
_ENH_RE = re.compile(r"(?<![\d.])([245]\.\d{1,3}\.\d{1,3})(?![\d.])")
_SMTP_CODE_RE = re.compile(r"(?<![\d.])([45]\d\d)(?![\d.])")
_POLICY_WORDS_RE = re.compile(r"spam|blocklist|blacklist|policy|blocked|rejected as", re.I)
_SOFT_WORDS_RE = re.compile(r"mailbox full|over quota|try again|temporar", re.I)
_HARD_WORDS_RE = re.compile(r"user unknown|no such user|unknown recipient|does not exist", re.I)


def _extract_dsn_code(text: str) -> tuple[str | None, str | None, str]:
    """Liefert (smtp_code, enhanced_code, diagnosezeile). Reihenfolge: Status, Diagnostic-Code, SMTP-Zeile."""
    smtp = enhanced = None
    diag = ""
    m = _STATUS_RE.search(text)
    if m:
        enhanced = m.group(1)
    m = _DIAG_RE.search(text)
    if m:
        diag = " ".join(m.group(0).split())
        e = _ENH_RE.search(diag)
        c = _SMTP_CODE_RE.search(diag)
        enhanced = enhanced or (e.group(1) if e else None)
        smtp = c.group(1) if c else None
    m = _SMTP_LINE_RE.search(text)
    if m:
        smtp = smtp or m.group(1)
        enhanced = enhanced or m.group(2)
        diag = diag or " ".join(m.group(0).split())
    return smtp, enhanced, diag


def classify_dsn(text: str) -> DsnClass:
    """Klassifiziert ueber den extrahierten DSN-Statuscode; Schluesselwoerter nur ohne Code."""
    if not text:
        return "unknown"
    smtp, enh, diag = _extract_dsn_code(text)
    if enh or smtp:
        if enh and enh.startswith("5.1."):
            return "hard"
        if enh and enh.startswith("5.7."):
            return "policy"
        if smtp == "554" and _POLICY_WORDS_RE.search(diag):
            return "policy"
        if (enh and (enh.startswith("4.") or enh == "5.2.2")) or (smtp and smtp.startswith("4")):
            return "soft"
        return "hard"
    if _POLICY_WORDS_RE.search(text):
        return "policy"
    if _SOFT_WORDS_RE.search(text):
        return "soft"
    if _HARD_WORDS_RE.search(text):
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
    """Berechnet Zustellbarkeits-Flags. MX wird je Domain nur einmal geprüft (mx_cache).

    bounced_domains wird einmal in Kleinschreibung normalisiert; Eintraege duerfen beliebig geschrieben sein.
    """
    email = str(lead.get("Email") or lead.get("E-Mail") or "").strip()
    if not EMAIL_RE.match(email):
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

    if domain in {str(d).strip().lower() for d in bounced_domains}:
        flags.append(FLAG_DOMAIN_BOUNCED_BEFORE)
    return flags


def summarize_bounces(messages: Iterable) -> dict:
    """Zählt Bounces je DSN-Klasse und je Domain. Gibt nie Adressen zurück."""
    from inbound_classifier import classify_inbound_message

    by_class: Counter[str] = Counter()
    by_domain: Counter[str] = Counter()
    hard_by_domain: Counter[str] = Counter()
    for msg in messages:
        cls = classify_inbound_message(msg.sender, msg.subject, msg.body)
        if cls.category != "BOUNCE":
            continue
        dsn = classify_dsn(msg.body)
        by_class[dsn] += 1
        if cls.extracted_email and "@" in cls.extracted_email:
            domain = cls.extracted_email.rsplit("@", 1)[1].lower()
            by_domain[domain] += 1
            if dsn == "hard":
                hard_by_domain[domain] += 1
    return {"total": sum(by_class.values()), "by_class": dict(by_class), "by_domain": dict(by_domain),
            "hard_by_domain": dict(hard_by_domain)}
