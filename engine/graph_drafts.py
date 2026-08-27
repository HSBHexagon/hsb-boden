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
`POST /me/messages` mit `Content-Type: text/plain` und dem Base64-kodierten
MIME der Nachricht. Der Entwurf entsteht dabei serverseitig im Ordner
"Entwuerfe" des Postfachs der angemeldeten Person - unabhaengig davon,
welchen Outlook-Client sie benutzt.

  https://learn.microsoft.com/en-us/graph/outlook-create-send-messages

Sendesicherheit
---------------
Dieses Werkzeug ruft ausschliesslich `POST .../messages` auf. Die Graph-
Aktion `POST .../messages/{id}/send` kommt hier nicht vor - der Versand
bleibt ein bewusster Schritt eines Menschen in Outlook.

Einmalige Einrichtung - OHNE Administrator moeglich
----------------------------------------------------
Fruehere Fassungen dieses Werkzeugs nutzten eine *Anwendungsberechtigung*
(Client-Credentials-Fluss). Application-Permissions wirken unbeaufsichtigt
und tenant-weit - Microsoft laesst sie deshalb grundsaetzlich nur von einer
Person mit einer Entra-Admin-Rolle freischalten (Global Administrator,
Privileged Role Administrator, Application Administrator oder Cloud
Application Administrator). Das ist Sicherheitsdesign, kein Konfigurations-
detail, und laesst sich fuer diesen Berechtigungstyp nicht umgehen.

Dieses Werkzeug braucht aber gar keine tenant-weite Wirkung - jede Person legt
ohnehin nur Entwuerfe im EIGENEN Postfach an. Dafuer reicht eine *delegierte*
Berechtigung, bei der sich die Person einmalig selbst per Geraetecode anmeldet
und selbst zustimmt (Self-Consent) - ohne jede Administratorbeteiligung,
sofern der Tenant Nutzerzustimmung fuer delegierte Berechtigungen nicht
generell gesperrt hat. Ob das der Fall ist, zeigt erst der echte Versuch:
zeigt der Anmeldebildschirm einen normalen Zustimmungsdialog, ist kein Admin
noetig; zeigt er "Genehmigung durch Administrator erforderlich", ist das ein
echter, hier dokumentierter externer Blocker.

Einmalig in Entra ID (jede Person mit gewoehnlichem Nutzerkonto kann eine
App-Registrierung anlegen - auch das braucht standardmaessig keinen Admin):

  1. App-Registrierung anlegen, Typ "Mobile and desktop applications" bzw.
     "Public client flows" = Ja aktivieren (kein Client-Secret noetig).
  2. Unter "API permissions": Microsoft Graph -> Delegated permissions ->
     `Mail.ReadWrite` hinzufuegen.
  3. Client-ID und Tenant-ID aus der Uebersichtsseite der Registrierung
     eintragen:

    export HSB_GRAPH_TENANT_ID=...
    export HSB_GRAPH_CLIENT_ID=...

Beim ersten Lauf zeigt das Werkzeug eine URL und einen kurzen Code; nach der
Anmeldung im Browser laeuft es automatisch weiter und merkt sich ein
Refresh-Token lokal (`~/.hsb_graph_token_cache.json`, nur fuer den
aktuellen Nutzer lesbar), damit spaetere Laeufe ohne erneute Anmeldung
funktionieren, bis das Refresh-Token ablaeuft oder widerrufen wird.

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
import time
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


SCOPE = "https://graph.microsoft.com/Mail.ReadWrite offline_access"
TOKEN_CACHE = Path.home() / ".hsb_graph_token_cache.json"


def _cache_lesen() -> dict:
    if not TOKEN_CACHE.exists():
        return {}
    try:
        return json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cache_schreiben(daten: dict) -> None:
    TOKEN_CACHE.write_text(json.dumps(daten), encoding="utf-8")
    try:
        os.chmod(TOKEN_CACHE, 0o600)
    except OSError:
        pass  # z. B. auf Dateisystemen ohne Unix-Rechte - kein harter Abbruch


def _token_anfrage(tenant: str, felder: dict) -> dict | None:
    """Einzelner Aufruf des Token-Endpunkts. `None` bei HTTP-Fehler statt
    Ausnahme, weil Aufrufer (Refresh-Versuch, Geraetecode-Polling) selbst
    entscheiden, ob ein Fehlschlag ein Abbruch oder nur ein "noch nicht" ist.
    """
    daten = urllib.parse.urlencode(felder).encode()
    req = urllib.request.Request(f"{LOGIN}/{tenant}/oauth2/v2.0/token", data=daten)
    try:
        with urllib.request.urlopen(req, timeout=30) as antwort:
            return json.load(antwort)
    except urllib.error.HTTPError as e:
        try:
            fehler = json.loads(e.read().decode("utf-8", "replace") or "{}")
        except json.JSONDecodeError:
            fehler = {}
        fehler["_http_status"] = e.code
        return fehler


def _device_code_anfordern(tenant: str, client_id: str) -> dict:
    daten = urllib.parse.urlencode({
        "client_id": client_id, "scope": SCOPE,
    }).encode()
    req = urllib.request.Request(f"{LOGIN}/{tenant}/oauth2/v2.0/devicecode", data=daten)
    try:
        with urllib.request.urlopen(req, timeout=30) as antwort:
            return json.load(antwort)
    except urllib.error.HTTPError as e:
        raise GraphFehler(
            f"Geraetecode konnte nicht angefordert werden ({e.code}): "
            f"{e.read().decode('utf-8', 'replace')[:400]}"
        ) from e


def _mit_refresh_token(tenant: str, client_id: str, refresh_token: str) -> dict | None:
    """Stiller Anmeldeversuch mit dem gespeicherten Refresh-Token. Gibt `None`
    zurueck (statt eine Ausnahme zu werfen), wenn er nicht (mehr) gueltig ist -
    das ist dann kein Fehler, sondern der Auftrag, sich erneut per
    Geraetecode anzumelden.
    """
    antwort = _token_anfrage(tenant, {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": SCOPE,
    })
    if antwort is None or "access_token" not in antwort:
        return None
    return antwort


def _interaktive_geraetecode_anmeldung(tenant: str, client_id: str) -> dict:
    """Einmalige, von einer Person durchgefuehrte Anmeldung. Delegierte
    Berechtigung, Self-Consent der angemeldeten Person - keine
    Administratorbeteiligung noetig, sofern der Tenant das zulaesst (siehe
    Kopf dieser Datei).
    """
    code = _device_code_anfordern(tenant, client_id)
    print("\nEinmalige Anmeldung noetig:")
    print(f"  1. Im Browser oeffnen: {code['verification_uri']}")
    print(f"  2. Diesen Code eingeben: {code['user_code']}\n")
    print("  Warte auf Anmeldung ...")

    intervall = int(code.get("interval", 5))
    ablauf = time.time() + int(code.get("expires_in", 900))
    while time.time() < ablauf:
        time.sleep(intervall)
        antwort = _token_anfrage(tenant, {
            "client_id": client_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": code["device_code"],
        })
        if antwort and "access_token" in antwort:
            return antwort
        fehlercode = (antwort or {}).get("error", "")
        if fehlercode == "authorization_pending":
            continue
        if fehlercode == "slow_down":
            intervall += 5
            continue
        raise GraphFehler(
            "Geraetecode-Anmeldung fehlgeschlagen: "
            + (antwort or {}).get("error_description", fehlercode or "unbekannt")
        )
    raise GraphFehler("Geraetecode-Anmeldung: Zeit abgelaufen. Bitte erneut versuchen.")


def token_holen() -> str:
    """Delegierter Fluss: zuerst stiller Refresh-Versuch mit dem lokal
    gemerkten Token, nur bei Bedarf eine neue interaktive Geraetecode-
    Anmeldung. Kein Geheimnis in dieser Datei oder in Umgebungsvariablen -
    anders als beim frueheren Client-Credentials-Fluss ist hier nichts
    Tenant-weit Wirksames zu schuetzen.
    """
    tenant = _umgebung("HSB_GRAPH_TENANT_ID")
    client_id = _umgebung("HSB_GRAPH_CLIENT_ID")

    cache = _cache_lesen()
    antwort = None
    refresh_token = cache.get("refresh_token")
    if refresh_token:
        antwort = _mit_refresh_token(tenant, client_id, refresh_token)
    if antwort is None:
        antwort = _interaktive_geraetecode_anmeldung(tenant, client_id)

    if antwort.get("refresh_token"):
        _cache_schreiben({"refresh_token": antwort["refresh_token"]})
    if "access_token" not in antwort:
        raise GraphFehler(f"Anmeldung ohne Zugriffstoken abgeschlossen: {antwort}")
    return antwort["access_token"]


def _graph(methode: str, pfad: str, token: str, koerper: bytes | None = None,
           typ: str = "application/json", versuche: int = 5) -> dict:
    """Ein Graph-Aufruf mit der von Microsoft vorgeschriebenen Drosselung.

    Bei HTTP 429 nennt Graph im Kopf `Retry-After` die Wartezeit in Sekunden.
    Microsoft verlangt ausdruecklich, diese Zeit abzuwarten und *keine*
    sofortige Wiederholung zu senden - jeder Versuch zaehlt gegen das
    Kontingent und verlaengert die Drosselung. Fehlt der Kopf, wird
    exponentiell zurueckgestuft. 503 und 504 werden gleich behandelt.

      https://learn.microsoft.com/en-us/graph/throttling
    """
    for versuch in range(1, versuche + 1):
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
            if e.code not in (429, 503, 504) or versuch == versuche:
                raise GraphFehler(f"{methode} {pfad} -> {e.code}: {text}") from e
            warte = e.headers.get("Retry-After")
            sekunden = int(warte) if (warte or "").isdigit() else 2 ** versuch
            print(f"    gedrosselt ({e.code}), warte {sekunden}s "
                  f"[Versuch {versuch}/{versuche - 1}]")
            time.sleep(sekunden)
    raise GraphFehler(f"{methode} {pfad}: nach {versuche} Versuchen aufgegeben.")


def identitaet_pruefen(token: str, erwartetes_postfach: str) -> None:
    """Fail-closed: mit delegierter Berechtigung wirkt jeder Aufruf im
    Postfach der ANGEMELDETEN Person (`/me`), nie in einem beliebigen
    anderen. Diese Pruefung stellt sicher, dass sich die richtige Person
    angemeldet hat, bevor irgendein Entwurf angelegt wird - sonst koennte
    sich z. B. Joel anmelden, waehrend fuer Jordi Entwuerfe gedacht waren.
    """
    info = _graph("GET", "/me?$select=mail,userPrincipalName", token)
    erreicht = (info.get("mail") or info.get("userPrincipalName") or "").lower()
    if erwartetes_postfach.lower() not in erreicht:
        raise GraphFehler(
            f"Angemeldet als {erreicht!r}, erwartet wurde {erwartetes_postfach} "
            "- abgebrochen, damit keine Entwuerfe im falschen Postfach landen."
        )


def entwurf_anlegen(token: str, mime: bytes) -> str:
    """Legt genau einen Entwurf im Postfach der angemeldeten Person an."""
    ergebnis = _graph("POST", "/me/messages", token,
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
    ap.add_argument("--erneut", action="store_true",
                    help="Trotz bereits angelegter Entwuerfe erneut laufen")
    args = ap.parse_args()

    quelle = Path(args.ordner).expanduser() / args.batch / "Entwuerfe"
    dateien = sorted(quelle.glob("*.eml"))
    postfach = args.postfach

    if not dateien:
        # --pruefen soll einen reinen Anmelde-/Verbindungstest ermoeglichen,
        # OHNE dass vorher schon ein Batch erzeugt sein muss - genau dafuer
        # ist der Modus da. Ohne Dateien laesst sich das Postfach nur nicht
        # automatisch aus dem "From"-Kopf ableiten, deshalb dann --postfach
        # explizit verlangen statt zu raten.
        if not (args.pruefen and postfach):
            raise SystemExit(
                f"ABBRUCH: Keine EML-Dateien in {quelle}. Zuerst erzeugen mit:\n"
                f"  python3 engine/make_drafts.py --batch {args.batch}\n"
                "Fuer einen reinen Anmelde-Probelauf ohne vorhandene Entwuerfe:"
                " --pruefen zusammen mit --postfach angeben.")
    elif not postfach:
        import email
        import email.policy
        kopf = email.message_from_bytes(dateien[0].read_bytes(),
                                        policy=email.policy.default)
        postfach = str(kopf["From"]).split("<")[-1].strip(" <>")

    print(f"Batch    : {args.batch}")
    print(f"Postfach : {postfach}")
    print(f"Dateien  : {len(dateien)}\n")

    # Ein zweiter Lauf wuerde stillschweigend 100 weitere Entwuerfe anlegen.
    # Graph kennt kein natuerliches Schluesselfeld dafuer, deshalb dient das
    # Protokoll des letzten Laufs als Sperre.
    protokoll = quelle.parent / "graph_entwuerfe.json"
    if protokoll.exists() and not args.pruefen and not args.erneut:
        vorher = json.loads(protokoll.read_text(encoding="utf-8"))
        raise SystemExit(
            f"ABBRUCH: Fuer {args.batch} wurden bereits "
            f"{vorher.get('angelegt', '?')} Entwuerfe in "
            f"{vorher.get('postfach', '?')} angelegt "
            f"(siehe {protokoll}).\nEin zweiter Lauf wuerde sie verdoppeln. "
            "Bewusst wiederholen mit --erneut.")

    token = token_holen()
    identitaet_pruefen(token, postfach)
    print("Anmeldung und Postfach geprueft.")
    if args.pruefen:
        print("Probelauf beendet - es wurde nichts angelegt.")
        return 0

    ziel = dateien[: args.limit] if args.limit else dateien
    kennungen, fehler = [], []
    for i, pfad in enumerate(ziel, 1):
        try:
            kennungen.append(entwurf_anlegen(token, pfad.read_bytes()))
        except GraphFehler as e:
            fehler.append((pfad.name, str(e)))
        if i % 10 == 0 or i == len(ziel):
            print(f"  {i}/{len(ziel)} angelegt, {len(fehler)} Fehler")

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
