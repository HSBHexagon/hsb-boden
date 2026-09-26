#!/usr/bin/env python3
"""
Dual-Delivery & Enterprise SEG Anti-Quarantine Helper for HSB Sales OS.
Classifies recipient domain mail gateways (Proofpoint, Mimecast, Defender ATP)
and manages dual-delivery options (241 KB PDF attachment vs. trusted CDN link).
"""
import subprocess
import re
from typing import Dict, Any, Tuple

# Canonical Assets
CANONICAL_FLYERS = {
    "JOEL": {
        "filename": "HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "local_path": "/Users/joelcherinodiaz/Projekte/hsb-boden/apps/sales-os/assets/canonical/HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "cdn_url": "https://www.hsb-boden.de/flyer/HSB-Flyer-Joel-Cherino_FINAL.pdf",
        "size_kb": 241
    },
    "JORDI": {
        "filename": "HSB-Flyer-Jordie-Post_FINAL.pdf",
        "local_path": "/Users/joelcherinodiaz/Projekte/hsb-boden/apps/sales-os/assets/canonical/HSB-Flyer-Jordie-Post_FINAL.pdf",
        "cdn_url": "https://www.hsb-boden.de/flyer/HSB-Flyer-Jordie-Post_FINAL.pdf",
        "size_kb": 241
    }
}

# Alias
CANONICAL_FLYERS["JORDIE"] = CANONICAL_FLYERS["JORDI"]

ENTERPRISE_SEG_PATTERNS = {
    "proofpoint": r"pphosted\.com|proofpoint",
    "mimecast": r"mimecast",
    "barracuda": r"barracudanetworks|barracuda",
    "cisco_ironport": r"iphmx\.com|ironport",
    "sophos": r"sophos",
    "trendmicro": r"trendmicro",
    "defender_atp": r"mail\.protection\.outlook\.com"
}

def get_mx_records(domain: str) -> list:
    try:
        res = subprocess.run(
            ["dig", "+short", "MX", domain],
            capture_output=True,
            text=True,
            timeout=5
        )
        return [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
    except Exception:
        return []

def classify_recipient_seg(email_or_domain: str) -> Dict[str, Any]:
    """
    Analyzes MX records to detect whether the recipient uses an enterprise Secure Email Gateway.
    """
    domain = email_or_domain.split("@")[-1].strip().lower()
    mx_records = get_mx_records(domain)
    mx_joined = " ".join(mx_records).lower()

    detected_seg = "standard"
    high_quarantine_risk = False
    details = []

    for seg_name, pattern in ENTERPRISE_SEG_PATTERNS.items():
        if re.search(pattern, mx_joined):
            detected_seg = seg_name
            if seg_name in ("proofpoint", "mimecast", "barracuda"):
                high_quarantine_risk = True
                details.append(f"Erkanntes Enterprise SEG: {seg_name.upper()}. Aggressive Sandbox-Prüfung bei PDF-Anhängen.")
            elif seg_name == "defender_atp":
                details.append("Microsoft Defender for Office 365 (Safe Attachments aktiv).")
            break

    if detected_seg == "standard":
        details.append("Standard Mail-Infrastruktur oder kein bekanntes Enterprise SEG.")

    return {
        "domain": domain,
        "mx_records": mx_records,
        "seg": detected_seg,
        "high_quarantine_risk": high_quarantine_risk,
        "details": details
    }

def get_flyer_delivery_config(owner: str, recipient_email: str) -> Dict[str, Any]:
    """
    Returns the optimal flyer strategy (Attachment + CDN Link vs Attachment only)
    based on the recipient's email gateway.
    """
    norm_owner = owner.strip().upper()
    if norm_owner not in CANONICAL_FLYERS:
        norm_owner = "JOEL"
        
    flyer_meta = CANONICAL_FLYERS[norm_owner]
    seg_info = classify_recipient_seg(recipient_email)

    # Both: Always provide 241 KB attachment + CDN Fallback in footer for maximum deliverability
    return {
        "owner": norm_owner,
        "flyer_filename": flyer_meta["filename"],
        "flyer_local_path": flyer_meta["local_path"],
        "flyer_cdn_url": flyer_meta["cdn_url"],
        "flyer_size_kb": flyer_meta["size_kb"],
        "attach_physical_pdf": True,
        "include_cdn_link": True,
        "seg_classification": seg_info
    }

if __name__ == "__main__":
    import sys
    test_domain = sys.argv[1] if len(sys.argv) > 1 else "basf.com"
    print(f"Testing SEG classification for {test_domain}...")
    res = classify_recipient_seg(test_domain)
    print(res)
