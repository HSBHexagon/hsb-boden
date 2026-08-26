#!/usr/bin/env python3
"""
HSB Sales OS - Entwuerfe direkt im Microsoft-365-Postfach anlegen.

Warum dieser Weg existiert
--------------------------
Der bisherige Weg legte EML-Dateien ab, die von Hand nach Outlook gezogen
werden. Der Kopfzeilen-Trick `X-Unsent: 1`, mit dem Outlook eine solche Datei
als unversendeten Entwurf oeffnen soll, wird von Outlook fuer Mac ignoriert
und im neuen Outlook fuer Windows nicht mehr zuverlaessig ausgewertet.

Der dokumentierte Weg von Microsoft ist stattdessen
`POST /users/{postfach}/messages` mit `Content-Type: text/plain` und dem
Base64-kodierten MIME der Nachricht. Der Entwurf entsteht dabei serverseitig
im Ordner "Entwuerfe" des Postfachs - unabhaengig davon, welchen Outlook-
Client der Bearbeiter benutzt.

  https://learn.microsoft.com/en-us/graph/outlook-create-send-messages

Sendesicherheit
---------------
Dieses Werkzeug ruft ausschliesslich `POST .../messages` auf. Die Graph-
Aktion `POST .../messages/{id}/send` kommt hier nicht vor - der Versand
bleibt ein bewusster Schritt eines Menschen in Outlook.

Einmalige Einrichtung
---------------------
Eine App-Registrierung in Entra ID mit der *Anwendungsberechtigung*
`Mail.ReadWrite` und erteilter Administratorzustimmung. Danach:

    export HSB_GRAPH_TENANT_ID=...
    export HSB_GRAPH_CLIENT_ID=...
    export HSB_GRAPH_CLIENT_SECRET=...

Empfehlenswert ist zusaetzlich eine Anwendungszugriffsrichtlinie
(`New-ApplicationAccessPolicy`), die die App auf genau die beiden HSB-
Postfaecher begrenzt, statt ihr den gesamten Tenant zu oeffnen.

Aufruf
------
    python3 engine/graph_drafts.py --batch HSB-20260826-JORDI-0002 --pruefen
    python3 engine/graph_drafts.py --batch HSB-20260826-JORDI-0002
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_drafts import STANDARD_ZIEL

GRAPH = "https://graph.microsoft.com/v1.0"
LOGIN = "https://login.microsoftonline.com"


class GraphFehler(RuntimeError):
    """Ein Aufruf gegen Microsoft Graph ist fehlgeschlagen."""


def _umgebung(name: str) -> str:
    wert = os.environ.get(name, "").strip()
    if not wert:
        raise SystemExit(
            f"ABBRUCH: {name} ist nicht gesetzt. Siehe 'Einmalige Einrichtung' "
            f"im Kopf dieser Datei ({Path(__file__).name})."
        )
    return wert


def token_holen() -> str:
    """Client-Credentials-Fluss. Das Geheimnis verlaesst diese Funktion nicht."""
    tenant = _umgebung("HSB_GRAPH_TENANT_ID")
    daten = urllib.parse.urlencode({
        "client_id": _umgebung("HSB_GRAPH_CLIENT_ID"),
        "client_secret": _umgebung("HSB_GRAPH_CLIENT_SECRET"),
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }).encode()
    req = urllib.request.Request(f"{LOGIN}/{tenant}/oauth2/v2.0/token", data=daten)
    try:
        with urllib.request.urlopen(req, timeout=30) as antwort:
            return json.load(antwort)["access_token"]
    except urllib.error.HTTPError as e:
        raise GraphFehler(
            f"Anmeldung fehlgeschlagen ({e.code}). Pruefe Tenant, Client-ID "
            f"und Geheimnis: {e.read().decode('utf-8', 'replace')[:400]}"
        ) from e


def _graph(methode: str, pfad: str, token: str, koerper: bytes | None = None,
           typ: str = "application/json") -> dict:
    req = urllib.request.Request(f"{GRAPH}{pfad}", data=koerper, method=methode)
    req.add_header("Authorization", f"Bearer {token}")
    if koerper is not None:
        req.add_header("Content-Type", typ)
    try:
        with urllib.request.urlopen(req, timeout=120) as antwort:
            roh = antwort.read()
            return json.loads(roh) if roh else {}
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")[:500]
        raise GraphFehler(f"{methode} {pfad} -> {e.code}: {text}") from e


def postfach_pruefen(token: str, postfach: str) -> None:
    """Fail-closed: ohne erreichbares Postfach wird nichts angelegt."""
    p = urllib.parse.quote(postfach)
    info = _graph("GET", f"/users/{p}?$select=mail,userPrincipalName", token)
    erreicht = (info.get("mail") or info.get("userPrincipalName") or "").lower()
    if postfach.lower() not in erreicht:
        raise GraphFehler(
            f"Postfach {postfach} aufgeloest auf {erreicht!r} - abgebrochen, "
            "damit keine Entwuerfe im falschen Postfach landen."
        )


def entwurf_anlegen(token: str, postfach: str, mime: bytes) -> str:
    """Legt genau einen Entwurf an und gibt dessen Kennung zurueck."""
    p = urllib.parse.quote(postfach)
    ergebnis = _graph("POST", f"/users/{p}/messages", token,
                      base64.b64encode(mime), typ="text/plain")
    return str(ergebnis.get("id", ""))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--postfach", default=None,
                    help="Standard: Absender laut EML-Kopf")
    ap.add_argument("--ordner", default=str(STANDARD_ZIEL),
                    help="Ordner mit den erzeugten EML-Dateien")
    ap.add_argument("--pruefen", action="store_true",
                    help="Nur Anmeldung und Postfach pruefen, nichts anlegen")
    ap.add_argument("--limit", type=int, default=0,
                    help="Nur die ersten N Entwuerfe anlegen (Probelauf)")
    args = ap.parse_args()

    quelle = Path(args.ordner).expanduser() / args.batch / "Entwuerfe"
    dateien = sorted(quelle.glob("*.eml"))
    if not dateien:
        raise SystemExit(
            f"ABBRUCH: Keine EML-Dateien in {quelle}. Zuerst erzeugen mit:\n"
            f"  python3 engine/make_drafts.py --batch {args.batch}")

    postfach = args.postfach
    if not postfach:
        import email
        import email.policy
        kopf = email.message_from_bytes(dateien[0].read_bytes(),
                                        policy=email.policy.default)
        postfach = str(kopf["From"]).split("<")[-1].strip(" <>")

    print(f"Batch    : {args.batch}")
    print(f"Postfach : {postfach}")
    print(f"Dateien  : {len(dateien)}\n")

    token = token_holen()
    postfach_pruefen(token, postfach)
    print("Anmeldung und Postfach geprueft.")
    if args.pruefen:
        print("Probelauf beendet - es wurde nichts angelegt.")
        return 0

    ziel = dateien[: args.limit] if args.limit else dateien
    kennungen, fehler = [], []
    for i, pfad in enumerate(ziel, 1):
        try:
            kennungen.append(entwurf_anlegen(token, postfach, pfad.read_bytes()))
        except GraphFehler as e:
            fehler.append((pfad.name, str(e)))
        if i % 10 == 0 or i == len(ziel):
            print(f"  {i}/{len(ziel)} angelegt, {len(fehler)} Fehler")

    protokoll = quelle.parent / "graph_entwuerfe.json"
    protokoll.write_text(json.dumps(
        {"batch": args.batch, "postfach": postfach,
         "angelegt": len(kennungen), "fehler": fehler,
         "message_ids": kennungen}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    if fehler:
        print(f"\nERGEBNIS=FAIL - {len(fehler)} von {len(ziel)} fehlgeschlagen.")
        for name, meldung in fehler[:5]:
            print(f"  {name}: {meldung}")
        return 1
    print(f"\nERGEBNIS=PASS - {len(kennungen)} Entwuerfe im Ordner 'Entwuerfe' "
          f"von {postfach}.")
    print(f"Protokoll: {protokoll}")
    print("Es wurde nichts versendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
