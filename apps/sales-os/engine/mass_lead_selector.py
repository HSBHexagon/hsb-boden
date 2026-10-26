from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def filter_and_partition_leads(leads: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filtert Leads auf Versandtauglichkeit:
    - Schließt bereits versendete (sent, gesendet, bounced, invalid) Leads strikt aus
    - Schließt Opt-outs und Abmeldungen aus
    - Validiert E-Mail-Format
    - Partitioniert den berechtigten Pool 50/50 auf Joel und Jordi
    """
    eligible = []
    for l in leads:
        email = (l.get("E-Mail") or l.get("Email") or "").strip().lower()
        if not email or not EMAIL_RE.match(email):
            continue

        send_status = str(l.get("Send_Status") or l.get("Send-Status") or l.get("Status") or "").strip().lower()
        if send_status in ("sent", "gesendet", "bounced", "invalid"):
            continue

        optout = str(l.get("Opt_Out") or l.get("Opt-Out") or "").strip().lower()
        pipeline = str(l.get("Pipeline") or l.get("Pipeline_Status") or "").strip().lower()
        if optout == "yes" or "abgemeldet" in pipeline or "widerspruch" in pipeline:
            continue

        eligible.append(l)

    # 50/50 Split auf Joel und Jordie
    joel_leads = eligible[0::2]
    jordi_leads = eligible[1::2]
    return joel_leads, jordi_leads
