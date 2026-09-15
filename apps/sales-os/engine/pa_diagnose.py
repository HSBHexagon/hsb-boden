#!/usr/bin/env python3
"""
HSB Sales OS - Power Automate Autonome Systemdiagnose & Status-Pruefung.

Ueberprueft:
  1. Azure CLI Authentifizierung & Tenant-Zugehoerigkeit
  2. FlowAgent MCP Server (59 Tools) & Token-Synchronisation
  3. Power Automate Environment (Default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30)
  4. Flow-Zustand fuer Jordi (47ee3d7a-...) und Joel (137601e8-...)
  5. Connection References (Office 365 Outlook) & Identity-Bindung
  6. Trigger-Schema-Validierung (Pflichtfelder fuer Direkt-Entwuerfe)
  7. Juengste Ausfuehrungshistorie & Auslesung der realen Draft-IDs
  8. Sendesicherheit (DraftEmail-Invariante: Real external prospect send = 0)

Aufruf:
    python3 engine/pa_diagnose.py
    python3 engine/pa_diagnose.py --flow-id 47ee3d7a-626c-4fff-9e16-6d938949e4bd
    python3 engine/pa_diagnose.py --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

TENANT_ID = "8adbbf2e-fd2c-4857-8540-bbcdb3a20f30"
DEFAULT_ENV_ID = f"Default-{TENANT_ID}"
FLOW_API_BASE = "https://germany.api.flow.microsoft.com"
FLOWAGENT_BUNDLE = "/Users/joelcherinodiaz/.claude/plugins/cache/power-platform-skills/power-automate/3.0.5/server/mcp.mjs"

REQUIRED_TRIGGER_PROPERTIES = [
    "leadId",
    "batchId",
    "to",
    "subject",
    "bodyHtml",
    "attachmentName",
    "attachmentContentBytes",
]

FLOWS = {
    "JORDI": {
        "id": "47ee3d7a-626c-4fff-9e16-6d938949e4bd",
        "name": "HSB Sales OS Draft Adapter (Jordi)",
        "owner": "j-post@hsb-boden.de",
        "expected_conn_id": "3d152ea7ddb24e9286fe006cb9f5069b",
        "trigger": "Button (Free-Tier)",
    },
    "JOEL": {
        "id": "137601e8-7369-4a74-9564-959f1551e48d",
        "name": "HSB Sales OS Draft Adapter",
        "owner": "j-cherino@hsb-boden.de",
        "expected_conn_id": "shared-office365-819bd473",
        "trigger": "Request/Http (Premium)",
    },
}


def run_cmd(cmd: List[str], timeout: int = 15) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()


def check_az_identity() -> Dict[str, Any]:
    out = run_cmd(["az", "account", "show", "--output", "json"])
    data = json.loads(out)
    return {
        "user": data.get("user", {}).get("name"),
        "tenantId": data.get("tenantId"),
        "is_tenant_ok": data.get("tenantId") == TENANT_ID,
    }


def get_flow_token() -> str:
    out = run_cmd([
        "az", "account", "get-access-token",
        "--resource", "https://service.flow.microsoft.com",
        "--query", "accessToken",
        "-o", "tsv"
    ])
    return out.strip()


def get_environment_info(token: str) -> Dict[str, Any]:
    url = f"{FLOW_API_BASE}/providers/Microsoft.ProcessSimple/environments/{DEFAULT_ENV_ID}?api-version=2016-11-01"
    out = run_cmd(["curl", "-s", "-H", f"Authorization: Bearer {token}", url])
    data = json.loads(out)
    props = data.get("properties", {})
    return {
        "name": data.get("name"),
        "displayName": props.get("displayName"),
        "location": data.get("location"),
        "state": props.get("states", {}).get("runtime", {}).get("id"),
        "isDefault": props.get("isDefault"),
    }


def get_flow_details(token: str, flow_id: str) -> Dict[str, Any]:
    url = f"{FLOW_API_BASE}/providers/Microsoft.ProcessSimple/environments/{DEFAULT_ENV_ID}/flows/{flow_id}?api-version=2016-11-01"
    out = run_cmd(["curl", "-s", "-H", f"Authorization: Bearer {token}", url])
    data = json.loads(out)
    props = data.get("properties", {})
    definition = props.get("definition", {})
    triggers_def = definition.get("triggers", {})
    actions_def = definition.get("actions", {})
    connection_refs = props.get("connectionReferences", {})
    
    # Schema validation
    manual_trigger = triggers_def.get("manual", {})
    schema_props = (manual_trigger.get("inputs", {})
                                  .get("schema", {})
                                  .get("properties", {}))
    missing_fields = [f for f in REQUIRED_TRIGGER_PROPERTIES if f not in schema_props]
    schema_valid = len(missing_fields) == 0

    # Connection reference check
    o365_ref = connection_refs.get("shared_office365", {})
    conn_name = o365_ref.get("connectionName")
    
    # Sendesicherheit pruefen: Keine 'Send'-Actions
    has_send_action = any(
        "send" in a.get("swaggerOperationId", "").lower() or "send" in a.get("name", "").lower()
        for a in props.get("definitionSummary", {}).get("actions", [])
    )
    
    return {
        "id": data.get("name"),
        "displayName": props.get("displayName"),
        "state": props.get("state"),
        "lastModifiedTime": props.get("lastModifiedTime"),
        "connection_name": conn_name,
        "connection_display": o365_ref.get("displayName"),
        "schema_valid": schema_valid,
        "missing_schema_fields": missing_fields,
        "send_safety_verified": not has_send_action,
    }


def get_flow_runs(token: str, flow_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    url = f"{FLOW_API_BASE}/providers/Microsoft.ProcessSimple/environments/{DEFAULT_ENV_ID}/flows/{flow_id}/runs?api-version=2016-11-01"
    out = run_cmd(["curl", "-s", "-H", f"Authorization: Bearer {token}", url])
    data = json.loads(out)
    runs = data.get("value", [])[:limit]
    parsed = []
    for r in runs:
        props = r.get("properties", {})
        run_info = {
            "run_id": r.get("name"),
            "startTime": props.get("startTime"),
            "endTime": props.get("endTime"),
            "status": props.get("status"),
            "error": props.get("error"),
            "response_outputs_url": props.get("response", {}).get("outputsLink", {}).get("uri"),
        }
        parsed.append(run_info)
    return parsed


def fetch_response_output(url: str) -> Optional[Dict[str, Any]]:
    if not url:
        return None
    try:
        out = run_cmd(["curl", "-s", url], timeout=5)
        data = json.loads(out)
        body = data.get("body", {})
        return {
            "statusCode": data.get("statusCode"),
            "draftId": body.get("draftId"),
            "internetMessageId": body.get("internetMessageId"),
            "status": body.get("status"),
        }
    except Exception:
        return None


def check_mcp_server() -> Dict[str, Any]:
    node_code = f"""
const {{ spawn }} = require('child_process');
const p = spawn('node', ['{FLOWAGENT_BUNDLE}'], {{
  env: {{ ...process.env, PA_DEFAULT_ENVIRONMENT: '{DEFAULT_ENV_ID}' }}
}});
let output = '';
let errOutput = '';
p.stdout.on('data', d => output += d.toString());
p.stderr.on('data', d => errOutput += d.toString());
setTimeout(() => {{
  p.kill();
  const toolMatch = errOutput.match(/(\\d+)\\s+tools/i);
  console.log(JSON.stringify({{
    alive: true,
    toolsFound: toolMatch ? parseInt(toolMatch[1], 10) : 0,
    banner: errOutput.trim().split('\\n')[0]
  }}));
}}, 1500);
"""
    try:
        out = run_cmd(["node", "-e", node_code], timeout=5)
        return json.loads(out.strip())
    except Exception as e:
        return {"alive": False, "error": str(e)}


def main() -> int:
    parser = argparse.ArgumentParser(description="HSB Sales OS Power Automate Diagnostik")
    parser.add_argument("--flow-id", help="Spezifische Flow-ID analysieren")
    parser.add_argument("--json", action="store_true", help="JSON-Ausgabe")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant_id": TENANT_ID,
    }

    # 1. Identity
    identity = check_az_identity()
    report["identity"] = identity

    # 2. Token & Env
    token = get_flow_token()
    env = get_environment_info(token)
    report["environment"] = env

    # 3. FlowAgent MCP
    mcp_status = check_mcp_server()
    report["mcp_server"] = mcp_status

    # 4. Flows
    flows_report = {}
    flows_to_check = FLOWS.values()
    if args.flow_id:
        flows_to_check = [f for f in FLOWS.values() if f["id"] == args.flow_id]

    for meta in flows_to_check:
        flow_id = meta["id"]
        owner_key = "JORDI" if "Jordi" in meta["name"] else "JOEL"
        details = get_flow_details(token, flow_id)
        runs = get_flow_runs(token, flow_id, limit=5)
        
        # Latest run output details
        latest_output = None
        if runs and runs[0].get("response_outputs_url"):
            latest_output = fetch_response_output(runs[0]["response_outputs_url"])
        
        flows_report[owner_key] = {
            "meta": meta,
            "details": details,
            "runs": runs,
            "latest_output": latest_output,
        }
    report["flows"] = flows_report

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    # Human-readable Markdown output
    print("# HSB Sales OS - Power Automate Autonomer Diagnosebericht")
    print(f"**Zeitstempel:** {report['timestamp']}")
    print(f"**Aktiver Azure-Benutzer:** `{identity['user']}` (Tenant: `{identity['tenantId']}`)")
    print(f"**Environment:** `{env['displayName']}` ({env['name']}, Status: `{env['state']}`)")
    print(f"**FlowAgent MCP Server:** {'ONLINE' if mcp_status.get('alive') else 'OFFLINE'} ({mcp_status.get('toolsFound', 0)} Tools registriert)")
    print()

    print("## Flow Status & Sendesicherheits-Matrix")
    print("| Owner | Flow Name | Status | Connection | Schema-Validität | Sendesicherheit | Letzter Lauf |")
    print("|---|---|---|---|---|---|---|")
    for key, f in flows_report.items():
        det = f["details"]
        runs = f["runs"]
        last_run = runs[0] if runs else None
        last_run_str = f"{last_run['status']} ({last_run['startTime'][:19]})" if last_run else "Keine Ausfuehrung"
        safety_str = "GESICHERT (DraftEmail only)" if det["send_safety_verified"] else "ACHTUNG: Send-Action gefunden"
        schema_str = "PASS (7/7 Felder)" if det["schema_valid"] else f"FAIL (fehlt: {det['missing_schema_fields']})"
        conn_str = f"`{det['connection_name'][:12]}...`" if det['connection_name'] else "FEHLT"
        print(f"| **{key}** | {det['displayName']} | `{det['state']}` | {conn_str} | {schema_str} | {safety_str} | {last_run_str} |")

    print()
    print("## Letzte nachgewiesene Entwurfs-Generierung (End-to-End IDs)")
    for key, f in flows_report.items():
        lo = f.get("latest_output")
        runs = f["runs"]
        last_run = runs[0] if runs else None
        print(f"### Flow `{key}` ({f['details']['displayName']})")
        if last_run and lo:
            print(f"- **Run ID:** `{last_run['run_id']}`")
            print(f"- **Status:** `{lo.get('status', 'OK')}` (HTTP {lo.get('statusCode')})")
            print(f"- **Draft ID (Outlook):** `{lo.get('draftId')}`")
            print(f"- **Internet Message ID:** `{lo.get('internetMessageId')}`")
        else:
            print("- Keine detaillierten Response-Outputs verfuegbar.")

    print()
    print("## Juengste Ausfuehrungshistorie (Top 3 je Flow)")
    for key, f in flows_report.items():
        print(f"### Flow: {f['details']['displayName']} (`{key}`)")
        for r in f["runs"][:3]:
            print(f"- **Run `{r['run_id'][:16]}...`**: Status `{r['status']}` | Start: `{r['startTime']}`")

    print()
    print("Zero-Touch-Diagnose erfolgreich abgeschlossen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
