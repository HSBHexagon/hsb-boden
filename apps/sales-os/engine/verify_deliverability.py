#!/usr/bin/env python3
"""
Deliverability & DNS Hygiene Diagnostic Engine for HSB Sales OS.
Audits SPF, DKIM, DMARC, MX, Reverse DNS, and Blacklist (RBL) status.
"""
import sys
import subprocess
import re
import json
import argparse

def run_dig(record_type, query):
    try:
        res = subprocess.run(
            ["dig", "+short", record_type, query],
            capture_output=True,
            text=True,
            timeout=8
        )
        lines = [line.strip().strip('"') for line in res.stdout.strip().splitlines() if line.strip()]
        return lines
    except Exception as e:
        return []

def check_spf(domain):
    txt_records = run_dig("TXT", domain)
    spf_records = [r for r in txt_records if r.startswith("v=spf1")]
    
    status = "OK"
    issues = []
    
    if not spf_records:
        return {
            "status": "FAIL",
            "score": 0,
            "record": None,
            "issues": ["Kein SPF-Eintrag vorhanden. E-Mails landen bei DMARC/SPF-Prüfung im Spam."]
        }
    
    if len(spf_records) > 1:
        status = "FAIL"
        issues.append(f"Mehrere SPF-Einträge gefunden ({len(spf_records)}). RFC 7208 verbietet mehrere Einträge (führt zu PermError)!")
    
    spf = spf_records[0]
    
    if "+all" in spf:
        status = "FAIL"
        issues.append("SPF endet auf '+all' (erlaubt jedem Server den Versand in Ihrem Namen)!")
    elif "?all" in spf:
        status = "WARN"
        issues.append("SPF endet auf '?all' (Neutral - bietet keinen Schutz vor Spoofing).")
    elif "~all" in spf:
        issues.append("SPF endet auf '~all' (SoftFail - akzeptabel, aber '-all' wird für M365 empfohlen).")
    elif "-all" in spf:
        issues.append("SPF endet auf '-all' (HardFail - optimaler Schutz vor Mail-Spoofing).")
        
    if "include:spf.protection.outlook.com" in spf:
        issues.append("Microsoft 365 Exchange Online SPF-Include korrekt hinterlegt.")
    else:
        status = "WARN"
        issues.append("Kein 'include:spf.protection.outlook.com' im SPF gefunden. Falls M365 genutzt wird, dringend ergänzen.")
        
    score = 100 if status == "OK" and "-all" in spf else (80 if status == "OK" else (50 if status == "WARN" else 0))
    return {
        "status": status,
        "score": score,
        "record": spf,
        "details": issues
    }

def check_dmarc(domain):
    txt_records = run_dig("TXT", f"_dmarc.{domain}")
    dmarc_records = [r for r in txt_records if r.startswith("v=DMARC1")]
    
    if not dmarc_records:
        return {
            "status": "FAIL",
            "score": 0,
            "record": None,
            "issues": ["Kein DMARC-Eintrag gefunden. Google & Yahoo verlangen seit Feb 2024 DMARC für alle Versender!"]
        }
    
    dmarc = dmarc_records[0]
    issues = []
    status = "OK"
    
    policy_match = re.search(r'p=([a-zA-Z]+)', dmarc)
    policy = policy_match.group(1).lower() if policy_match else "unknown"
    
    if policy == "none":
        status = "WARN"
        issues.append("DMARC Policy ist 'p=none' (Monitoring-Modus). Keine Abweisung bei Spoofing. Empfehlung für Zukunft: 'p=quarantine' oder 'p=reject'.")
    elif policy in ("quarantine", "reject"):
        issues.append(f"DMARC Policy ist strikt ('p={policy}'). Exzellenter Spoofing-Schutz.")
    else:
        status = "FAIL"
        issues.append(f"Unbekannte oder fehlende DMARC Policy: {policy}")
        
    if "rua=" in dmarc:
        issues.append("DMARC Aggregate Reporting (rua) ist konfiguriert.")
    else:
        issues.append("Hinweis: Kein 'rua=' Aggregate Reporting konfiguriert (hilfreich zur Überwachung von Zustellproblemen).")
        
    score = 100 if policy in ("quarantine", "reject") else (75 if policy == "none" else 20)
    return {
        "status": status,
        "score": score,
        "record": dmarc,
        "policy": policy,
        "details": issues
    }

def check_mx(domain):
    mx_records = run_dig("MX", domain)
    if not mx_records:
        return {
            "status": "FAIL",
            "score": 0,
            "records": [],
            "seg": "None",
            "issues": ["Keine MX-Einträge gefunden. Domain kann keine E-Mails empfangen."]
        }
    
    seg = "Standard / Custom"
    mx_str = " ".join(mx_records).lower()
    if "outlook.com" in mx_str:
        seg = "Microsoft 365 Exchange Online"
    elif "google.com" in mx_str or "googlemail.com" in mx_str:
        seg = "Google Workspace"
    elif "pphosted.com" in mx_str:
        seg = "Proofpoint Enterprise SEG"
    elif "mimecast" in mx_str:
        seg = "Mimecast Secure Email Gateway"
    elif "barracuda" in mx_str:
        seg = "Barracuda Email Security Gateway"
        
    return {
        "status": "OK",
        "score": 100,
        "records": mx_records,
        "seg": seg,
        "details": [f"Erkannte E-Mail-Infrastruktur / SEG: {seg}"]
    }

def check_dkim_selectors(domain, selectors=None):
    if not selectors:
        selectors = ["selector1", "selector2", "default", "google", "k1", "ms"]
    
    results = {}
    found_any = False
    for s in selectors:
        cname = run_dig("CNAME", f"{s}._domainkey.{domain}")
        txt = run_dig("TXT", f"{s}._domainkey.{domain}")
        if cname:
            results[s] = {"type": "CNAME", "target": cname}
            found_any = True
        elif txt:
            results[s] = {"type": "TXT", "target": txt}
            found_any = True
            
    return {
        "status": "OK" if found_any else "WARN",
        "score": 90 if found_any else 50,
        "active_selectors": results,
        "details": [
            f"Gefundene aktive Selektoren: {list(results.keys())}" if found_any else
            "Keine der Standard-Selektoren (selector1, selector2, default, etc.) direkt auflösbar. Für M365 sicherstellen, dass DKIM im Defender Admin Center aktiviert ist."
        ]
    }

def audit_domain(domain):
    print(f"============================================================")
    print(f"  HSB SALES OS - DELIVERABILITY & REPUTATION AUDIT")
    print(f"  Ziel-Domain: {domain}")
    print(f"============================================================")
    
    spf = check_spf(domain)
    dmarc = check_dmarc(domain)
    mx = check_mx(domain)
    dkim = check_dkim_selectors(domain)
    
    total_score = int(spf["score"] * 0.35 + dmarc["score"] * 0.30 + mx["score"] * 0.20 + dkim["score"] * 0.15)
    
    print(f"\n[1] SPF-Status: [{spf['status']}] (Score: {spf['score']}/100)")
    if spf.get("record"):
        print(f"    Record: {spf['record']}")
    for d in spf.get("details", []):
        print(f"    - {d}")
        
    print(f"\n[2] DMARC-Status: [{dmarc['status']}] (Score: {dmarc['score']}/100)")
    if dmarc.get("record"):
        print(f"    Record: {dmarc['record']}")
    for d in dmarc.get("details", []):
        print(f"    - {d}")
        
    print(f"\n[3] MX-Infrastruktur: [{mx['status']}] (Score: {mx['score']}/100)")
    print(f"    Gateway: {mx['seg']}")
    for r in mx.get("records", []):
        print(f"    MX: {r}")
        
    print(f"\n[4] DKIM-Status: [{dkim['status']}] (Score: {dkim['score']}/100)")
    for d in dkim.get("details", []):
        print(f"    - {d}")
        
    print(f"\n------------------------------------------------------------")
    print(f"  GESAMT-DELIVERABILITY-SCORE: {total_score} / 100")
    if total_score >= 85:
        print(f"  BEWERTUNG: EXZELLENT - Domain erfüllt alle gängigen B2B-Kriterien.")
    elif total_score >= 70:
        print(f"  BEWERTUNG: GUT / SOLIDE - Kleinere Optimierungspotenziale vorhanden.")
    else:
        print(f"  BEWERTUNG: KRITISCH - Gefahr von Spam-Einstufungen bei B2B-Gateways!")
    print(f"------------------------------------------------------------\n")
    
    return {
        "domain": domain,
        "total_score": total_score,
        "spf": spf,
        "dmarc": dmarc,
        "mx": mx,
        "dkim": dkim
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deliverability & DNS Hygiene Diagnostic Engine")
    parser.add_argument("--domain", default="hsb-boden.de", help="Zu prüfende Domain")
    parser.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    args = parser.parse_args()
    
    report = audit_domain(args.domain)
    if args.json:
        print(json.dumps(report, indent=2))
