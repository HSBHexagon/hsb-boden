"""Shared corporate-domain deduplication and opt-out guards."""
from __future__ import annotations

from hsb_core import FREEMAIL_DOMAINS

OWN_DOMAINS = frozenset({"hsb-boden.com", "hsb-boden.de"})
SYNTHETIC_TEST_DOMAINS = frozenset({"example.com", "example.org", "example.net"})
SYNTHETIC_TEST_SUFFIXES = (".invalid", ".example", ".test")
OPT_OUT_TRUE = frozenset({"yes", "ja", "true", "1", "opt_out"})


def corporate_domain_of(email_addr: str) -> str:
    """Return lowercase corporate domain, or '' for freemail, own, or RFC 2606 test domains."""
    addr = str(email_addr or "").strip().lower()
    if "@" not in addr:
        return ""
    dom = addr.rpartition("@")[2].strip("<>").lower()
    if not dom or dom in FREEMAIL_DOMAINS or dom in OWN_DOMAINS:
        return ""
    if dom in SYNTHETIC_TEST_DOMAINS or dom.endswith(SYNTHETIC_TEST_SUFFIXES):
        return ""
    return dom


def is_opted_out(lead: dict) -> bool:
    """Return True when opt-out status or opt-out suppression reason is set on a CRM lead."""
    if any(str(lead.get(k) or "").strip().lower() in OPT_OUT_TRUE for k in ("Opt-out-Status", "Opt_Out")):
        return True
    if str(lead.get("Reply_Status") or "").strip().lower() == "opt_out":
        return True
    reason = str(lead.get("Suppression_Reason") or "").strip().upper()
    return any(tok in reason for tok in ("OPTOUT", "OPT_OUT", "OPT OUT"))
