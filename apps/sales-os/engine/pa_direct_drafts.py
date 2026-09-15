#!/usr/bin/env python3
"""
HSB Sales OS - Entwuerfe ueber die Power-Automate-Flow-Adapter anlegen.

Warum dieser Weg existiert
--------------------------
Zwei Flows legen je Owner Outlook-Entwuerfe an (nur `DraftEmail`, kein
Send-Action im Flow):

  - Joel (j-cherino@hsb-boden.de): Flow "HSB Sales OS Draft Adapter"
    (`137601e8-7369-4a74-9564-959f1551e48d`), Trigger-Art Request/Http.
    Erfordert Power-Automate-Premium (der Trigger-Typ selbst ist Premium-
    pflichtig) - bei diesem Konto vorhanden.
  - Jordi (j-post@hsb-boden.de): Flow "HSB Sales OS Draft Adapter (Jordi)"
    (`47ee3d7a-626c-4fff-9e16-6d938949e4bd`), Trigger-Art Button (Free-Tier).
    Jordis Konto hat KEINE Premium-Lizenz - deshalb Button statt Request/Http,
    und deshalb bekommt der Flyer die Bytes direkt im Trigger-Body statt per
    HTTP-Download-Aktion (die waere ebenfalls Premium).

Die Trigger-Art bestimmt den Uebertragungsweg - das ist keine Praeferenz,
sondern eine harte Grenze (2026-09-07 an beiden Flows nachgemessen):

  - Button-Trigger (Jordi): NUR ueber den authentifizierten Logic-Flows-
    Connector-Endpunkt. Die SAS-Callback-URL ist hier von Microsoft
    blockiert (`ListCallbackUrlOperationBlocked`).
  - Http-/Request-Trigger (Joel): NUR ueber die eigene Callback-URL
    (`listCallbackUrl`). Der Connector-Endpunkt quittiert diesen Trigger-Typ
    mit HTTP 500 "Unable to cast object of type Dictionary to JObject" -
    und zwar in der Trigger-Schicht, es entsteht nicht einmal ein Flow-Lauf.

    Eine frueherer Kommentarstand behauptete, der Connector-Endpunkt taeuge
    fuer beide Trigger-Arten. Das ist widerlegt.

    1. GET .../powerautomate/apis/shared_logicflows?api-version=1
       (PPAPI, Token-Ressource https://service.powerapps.com/)
       -> liefert properties.primaryRuntimeUrl
    2. POST {primaryRuntimeUrl}/{flowId}/triggers/{trigger}/run
       ?api-version=2016-11-01
       (Token-Ressource https://apihub.azure.com, OHNE Trailing-Slash -
       mit Trailing-Slash liefert Microsoft AuthenticationFailed/
       "Audience nicht in erlaubter Liste")

Sendesicherheit
---------------
Beide Flows rufen ausschliesslich `DraftEmail` auf. Es gibt keine
Send-Action im Flow-Graphen. Der Versand bleibt ein bewusster,
manueller Schritt eines Menschen in Outlook.

Voraussetzung je Lauf
----------------------
`az login` muss als die Person laufen, der die im gewaehlten Flow
verdrahtete Connection gehoert (Joel-Flow -> j-cherino, Jordi-Flow ->
j-post) - Verbindungen sind nicht personen-uebergreifend nutzbar
(`ConnectionAuthorizationFailed`, siehe PROJECT_STATE.md).

Aufruf
------
    python3 engine/pa_direct_drafts.py --owner JORDI --batch HSB-20260826-JORDI-0002 --pruefen
    python3 engine/pa_direct_drafts.py --owner JORDI --batch HSB-20260826-JORDI-0002 --limit 1
    python3 engine/pa_direct_drafts.py --owner JORDI --batch HSB-20260826-JORDI-0002
    python3 engine/pa_direct_drafts.py --owner JOEL  --batch HSB-20260826-JOEL-0001
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hsb_core import FLYERS

PPAPI_BASE = (
    "https://default8adbbf2efd2c48578540bbcdb3a20f.30.environment.api.powerplatform.com"
)
APIHUB_RESOURCE_TOKEN = "https://apihub.azure.com"       # kein Trailing-Slash!
PPAPI_RESOURCE_TOKEN = "https://service.powerapps.com/"

FLOWS = {
    "JOEL": {
        "flowId": "137601e8-7369-4a74-9564-959f1551e48d",
        "trigger": "manual",
        "triggerKind": "Http",     # Request-Trigger -> Callback-URL noetig
        "expectedAccount": "j-cherino@hsb-boden.de",
        "usesFlyerUrl": False,  # Live-Flow erwartet attachmentContentBytes im Trigger-Body
    },
    "JORDI": {
        "flowId": "47ee3d7a-626c-4fff-9e16-6d938949e4bd",
        "trigger": "manual",
        "triggerKind": "Button",   # Button-Trigger -> Connector-Endpunkt
        "expectedAccount": "j-post@hsb-boden.de",
        "usesFlyerUrl": False,  # kein Premium -> Bytes direkt im Body
    },
}

FLOW_API_BASE = "https://api.flow.microsoft.com"
FLOW_ENV = "Default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30"
FLOW_RESOURCE_TOKEN = "https://service.flow.microsoft.com/"


class PaFehler(RuntimeError):
    """Ein Aufruf gegen die Power-Automate-Flow-Adapter ist fehlgeschlagen."""


def _az_token(resource: str) -> str:
    """Holt ein Access-Token ueber die lokale az-CLI-Session. Wirft PaFehler
    mit Klartext, wenn az nicht angemeldet ist - keine automatische
    Anmeldung hier, das macht die Person selbst (`az login`)."""
    try:
        out = subprocess.run(
            ["az", "account", "get-access-token", "--resource", resource,
             "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, timeout=30, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise PaFehler(
            "az-Token-Abruf fehlgeschlagen. Ist az CLI installiert und als "
            "die richtige Person angemeldet? (`az login --use-device-code "
            "--tenant 8adbbf2e-fd2c-4857-8540-bbcdb3a20f30 "
            "--allow-no-subscriptions`)"
        ) from e
    return out.stdout.strip()


def _current_account() -> str:
    out = subprocess.run(
        ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
        capture_output=True, text=True, timeout=30, check=True,
    )
    return out.stdout.strip()


def identitaet_pruefen(owner: str) -> None:
    """Fail-closed: die az-CLI-Identitaet muss zur Connection des gewaehlten
    Flows passen, sonst schlaegt der Lauf mit `ConnectionAuthorizationFailed`
    fehl - besser vorher klar melden als eine kryptische 403 zeigen."""
    erwartet = FLOWS[owner]["expectedAccount"]
    aktuell = _current_account().lower()
    if erwartet.lower() not in aktuell:
        raise PaFehler(
            f"az ist als {aktuell!r} angemeldet, aber der {owner}-Flow "
            f"gehoert {erwartet}. Verbindungen sind nicht personen-"
            f"uebergreifend nutzbar. Erst anmelden: az login --use-device-code "
            f"--tenant 8adbbf2e-fd2c-4857-8540-bbcdb3a20f30 "
            f"--allow-no-subscriptions"
        )


def _runtime_url() -> str:
    """Ermittelt die primaryRuntimeUrl des Logic-Flows-Connectors fuer diese
    Umgebung. Wird nicht fest verdrahtet, weil sie sich mit Microsoft-
    seitigen Aenderungen verschieben kann (siehe Quellcode des flowagent-
    MCP-Plugins, Methode ppapiConnectorUrl)."""
    token = _az_token(PPAPI_RESOURCE_TOKEN)
    req = urllib.request.Request(
        f"{PPAPI_BASE}/powerautomate/apis/shared_logicflows?api-version=1"
    )
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            daten = json.load(r)
    except urllib.error.HTTPError as e:
        raise PaFehler(
            f"Connector-Metadaten nicht abrufbar ({e.code}): "
            f"{e.read().decode('utf-8', 'replace')[:400]}"
        ) from e
    url = (daten.get("properties") or {}).get("primaryRuntimeUrl")
    if not url:
        raise PaFehler("Keine primaryRuntimeUrl in den Connector-Metadaten.")
    return url


def callback_url(owner: str) -> str:
    """Callback-URL eines Http-/Request-Triggers. Nur fuer diese Trigger-Art
    nutzbar; bei Button-Triggern antwortet Microsoft mit
    `ListCallbackUrlOperationBlocked`."""
    flow = FLOWS[owner]
    token = _az_token(FLOW_RESOURCE_TOKEN)
    url = (f"{FLOW_API_BASE}/providers/Microsoft.ProcessSimple/environments/"
           f"{FLOW_ENV}/flows/{flow['flowId']}/triggers/{flow['trigger']}"
           f"/listCallbackUrl?api-version=2016-11-01")
    req = urllib.request.Request(url, data=b"", method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            daten = json.load(r)
    except urllib.error.HTTPError as e:
        raise PaFehler(
            f"Callback-URL nicht abrufbar ({e.code}): "
            f"{e.read().decode('utf-8', 'replace')[:300]}"
        ) from e
    wert = (daten.get("response") or {}).get("value") or daten.get("value")
    if not wert:
        raise PaFehler("Antwort enthaelt keine Callback-URL.")
    return wert


def entwurf_anlegen(owner: str, runtime_url: str, payload: dict) -> dict:
    """Ruft genau einen Flow-Lauf auf. Der Flow selbst enthaelt nur
    `DraftEmail` - kein Versand moeglich, unabhaengig vom Payload hier.

    Der Weg haengt an der Trigger-Art (siehe Kopf dieser Datei): Http-Trigger
    ueber ihre Callback-URL, Button-Trigger ueber den Connector-Endpunkt."""
    flow = FLOWS[owner]
    daten = json.dumps(payload).encode("utf-8")

    if flow.get("triggerKind") == "Http":
        req = urllib.request.Request(callback_url(owner), data=daten,
                                      method="POST")
        req.add_header("Content-Type", "application/json")
    else:
        token = _az_token(APIHUB_RESOURCE_TOKEN)
        url = (f"{runtime_url.rstrip('/')}/{flow['flowId']}/triggers/"
               f"{flow['trigger']}/run?api-version=2016-11-01")
        req = urllib.request.Request(url, data=daten, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            roh = r.read()
            return json.loads(roh) if roh else {}
    except urllib.error.HTTPError as e:
        raise PaFehler(
            f"Flow-Lauf fehlgeschlagen ({e.code}): "
            f"{e.read().decode('utf-8', 'replace')[:500]}"
        ) from e


def payload_fuer_lead(owner: str, lead: dict, batch_id: str, subject: str,
                       body_html: str) -> dict:
    """Baut den Trigger-Payload. `usesFlyerUrl` unterscheidet die zwei
    Flow-Varianten (siehe Kopf dieser Datei)."""
    flyer = FLYERS[owner]
    basis = {
        "leadId": str(lead.get("Lead_ID") or ""),
        "batchId": batch_id,
        "owner": owner,
        "to": str(lead.get("Email") or "").strip(),
        "subject": subject,
        "bodyHtml": body_html,
        "attachmentName": flyer.attachment_name or flyer.filename,
    }
    basis["attachmentContentBytes"] = base64.b64encode(
        flyer.path.read_bytes()
    ).decode("ascii")
    return basis


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", required=True, choices=list(FLOWS))
    ap.add_argument("--batch", required=True)
    ap.add_argument("--pruefen", action="store_true",
                     help="Nur Identitaet/Runtime-URL pruefen, nichts anlegen")
    args = ap.parse_args()

    print(f"Owner : {args.owner}")
    print(f"Batch : {args.batch}")
    print(f"Flow  : {FLOWS[args.owner]['flowId']}\n")

    identitaet_pruefen(args.owner)
    print(f"Identitaet OK ({_current_account()}).")
    runtime_url = _runtime_url()
    print(f"Runtime-URL OK ({runtime_url}).")

    if args.pruefen:
        print("Probelauf beendet - es wurde nichts angelegt.")
        return 0

    print(
        "\nDieses Skript legt hier noch KEINE Batch-Schleife gegen das Sheet "
        "an (das ist bewusst offen - siehe PROJECT_STATE.md, Abschnitt "
        "'Power Automate - direkte Entwurfserzeugung'). Es stellt "
        "`entwurf_anlegen()` und `payload_fuer_lead()` als gepruefte "
        "Bausteine bereit, die ein Aufrufer mit den Sheet-Zeilen aus "
        "READY_CANDIDATES fuettert."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
