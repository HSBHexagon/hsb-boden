"""Seed-Platzierungstest und DNSBL-Pruefung (ohne IMAP-Logins fuer Seed-Anbieter)."""
from __future__ import annotations

import ipaddress
import json
import re
import secrets
import socket
from email import policy
from email.parser import BytesParser
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parent.parent / "config" / "seed_inboxes.json"

BLOCKLIST_ZONES = {
    "Barracuda": "b.barracudacentral.org",
    "SpamCop": "bl.spamcop.net",
    "UCEPROTECT-L1": "dnsbl-1.uceprotect.net",
    "UCEPROTECT-L2": "dnsbl-2.uceprotect.net",
    "UCEPROTECT-L3": "dnsbl-3.uceprotect.net",
    "PSBL": "psbl.surriel.com",
    "Mailspike": "bl.mailspike.net",
}
SPAMHAUS_NOTE = ("Spamhaus: nur manuell pruefen (https://check.spamhaus.org); DNS-Abfragen ueber "
                 "Public-Resolver sind gesperrt, Nutzung ohne Lizenz eingeschraenkt.")

_REFUSAL_NET = ipaddress.ip_network("127.255.255.0/24")


def load_seed_inboxes(path=None):
    p = Path(path) if path else SEED_PATH
    if not p.exists():
        raise FileNotFoundError(f"Seed-Liste fehlt: {p} (Vorlage: seed_inboxes.example.json)")
    data = json.loads(p.read_text(encoding="utf-8"))
    seeds = [d for d in data if d.get("address")]
    for d in seeds:
        dom = d["address"].lower().rsplit("@", 1)[-1]
        if dom == "example.com" or dom.endswith(".example"):
            raise ValueError(f"Platzhalter-Adresse in Seed-Liste: {d['address']}")
    return seeds


def _result(msg, key):
    m = re.search(rf"\b{key}=(\w+)", msg, re.I)
    return m.group(1).lower() if m else None


def parse_auth_results(raw: bytes) -> dict:
    msg = BytesParser(policy=policy.default).parsebytes(raw, headersonly=True)
    out = {"spf": None, "dkim": None, "dmarc": None, "dkim_domain": None, "folder": None}
    for hdr in msg.get_all("Authentication-Results", []):
        text = " ".join(str(hdr).split())
        for k in ("spf", "dkim", "dmarc"):
            if out[k] is None:
                out[k] = _result(text, k)
        if out["dkim_domain"] is None:
            m = re.search(r"dkim=\w+[^;]*?header\.(?:i|d)=@?([\w.-]+)", text, re.I)
            if m:
                out["dkim_domain"] = m.group(1).lower()
    return out


def _lookup_zone(ip, zone, resolver):
    """Gibt die Antwort-IP oder None (NXDOMAIN) zurueck."""
    rev = ".".join(reversed(ip.split(".")))
    try:
        return resolver(f"{rev}.{zone}")
    except socket.gaierror:
        return None


def blocklist_status(ip: str, resolver=None) -> dict:
    ipaddress.IPv4Address(ip)
    resolver = resolver or socket.gethostbyname
    res = {}
    for name, zone in BLOCKLIST_ZONES.items():
        try:
            test = _lookup_zone("127.0.0.2", zone, resolver)
            if test is None or ipaddress.IPv4Address(test) in _REFUSAL_NET:
                res[name] = "check_failed"
                continue
            if _lookup_zone("127.0.0.1", zone, resolver) is not None:
                res[name] = "check_failed"  # Wildcard-Zone
                continue
            ans = _lookup_zone(ip, zone, resolver)
        except OSError:
            res[name] = "check_failed"
            continue
        if ans is None:
            res[name] = "clean"
        elif ipaddress.IPv4Address(ans) in _REFUSAL_NET:
            res[name] = "check_failed"
        else:
            res[name] = "listed"
    return res


def new_token():
    return "HSB-SEED-" + secrets.token_hex(4)


def send_seed(client, seed_path, only_addresses):
    """Sendet eine neutrale Plain-Text-Testmail an Seed-Adressen. Gibt (token, results) zurueck."""
    seeds = load_seed_inboxes(seed_path)
    allowed = {s["address"].lower() for s in seeds}
    targets = [a.lower() for a in only_addresses] if only_addresses else sorted(allowed)
    if not targets:
        raise ValueError("Keine Seed-Empfaenger ausgewaehlt")
    outside = [a for a in targets if a not in allowed]
    if outside:
        raise PermissionError("Empfaenger nicht in der Seed-Liste: " + ", ".join(outside))
    from outbound_safety import require_internal_test
    for a in targets:
        require_internal_test(a, None, extra_allowed=allowed)
    token = new_token()
    subject = f"Testnachricht {token}"
    body = f"Dies ist eine Testnachricht zur Zustellpruefung. Kennung: {token}\n"
    results = []
    for a in targets:
        ok, msg_id = client.send_message(
            to_email=a, subject=subject, body_html=f"<p>{body}</p>", body_plain=body,
            extra_allowed_recipients=allowed)
        results.append({"address": a, "ok": ok, "message_id": msg_id})
    return token, results


def print_checklist(seeds, token):
    print(f"Manuelle Pruefung (Kennung im Betreff: {token})")
    for s in seeds:
        print(f"- {s.get('provider', '?')} ({s['address']}):")
        print("    Ordner notieren: Inbox / Spam / Promotions (Tab) / Updates")
        print("    'Original anzeigen' speichern -> Authentication-Results: spf, dkim, dmarc = pass?")
        print("    DKIM-Domain (header.i / header.d) = hsb-boden.com?")
        print("    Danach: seed-read --raw-file <datei.eml>")
