#!/usr/bin/env python3
"""Raeumt die Testentwuerfe aus einem HSB-Postfach.

Beim Aufbau des Entwurfsweges sind ueber Wochen Testentwuerfe im Postfach
liegengeblieben - Anhangproben, Beweisentwuerfe, Knopfweg-Tests. Von Hand
sind sie zwischen echten Kontakten schwer zu finden.

Sicherheitsregeln, bewusst eng:

  - Ohne `--loeschen` wird NICHTS geloescht, nur aufgelistet.
  - Geloescht wird ausschliesslich, was ein Testmerkmal im Betreff traegt
    UND im Ordner "Entwuerfe" liegt. Alles andere wird nicht angefasst,
    auch nicht auf Zuruf.
  - Geloescht heisst hier: in den Papierkorb verschoben (Graph `DELETE` auf
    eine Nachricht landet in "Geloeschte Elemente"). Nichts ist endgueltig
    weg, bis der Papierkorb geleert wird - und das macht dieses Werkzeug
    nicht.

Voraussetzung: dieselbe Anmeldung wie `graph_drafts.py`.

    export HSB_GRAPH_TENANT_ID=...
    export HSB_GRAPH_CLIENT_ID=...

Aufruf
------
    python3 engine/graph_aufraeumen.py --postfach j-cherino@hsb-boden.de
    python3 engine/graph_aufraeumen.py --postfach j-cherino@hsb-boden.de --loeschen
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph_drafts import _graph, identitaet_pruefen, token_holen

# Betreff-Merkmale der Testentwuerfe aus dem Aufbau des Systems.
# Bewusst als Praefix/Teilstring gepflegt statt als Regex: die Liste soll
# man ohne Nachdenken erweitern koennen.
TESTMERKMALE = [
    "[TEST",
    "[PRUEFUNG",
    "[PRÜFUNG",
    "[BEWEIS",
    "[PROBE",
    "Knopftest",          # Musterbetrieb Knopftest GmbH, live_knopfweg.js
    "Musterbetrieb",
]


def ist_testentwurf(betreff: str) -> bool:
    text = str(betreff or "")
    return any(m.lower() in text.lower() for m in TESTMERKMALE)


def entwuerfe_lesen(token: str) -> list[dict]:
    """Holt alle Entwuerfe des angemeldeten Postfachs, seitenweise."""
    felder = "id,subject,createdDateTime,toRecipients,hasAttachments"
    pfad = ("/me/mailFolders/drafts/messages"
            f"?$select={urllib.parse.quote(felder)}&$top=100")
    alle: list[dict] = []
    while pfad:
        antwort = _graph("GET", pfad, token)
        alle.extend(antwort.get("value", []))
        weiter = antwort.get("@odata.nextLink")
        # nextLink ist absolut; _graph erwartet einen Pfad relativ zu /v1.0.
        pfad = weiter.split("/v1.0", 1)[1] if weiter else ""
    return alle


def empfaenger(entwurf: dict) -> str:
    ziele = entwurf.get("toRecipients") or []
    if not ziele:
        return "(kein Empfaenger)"
    return ", ".join(
        (z.get("emailAddress") or {}).get("address", "?") for z in ziele[:3])


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--postfach", required=True,
                    help="Erwartetes Postfach - Schutz vor falscher Anmeldung")
    ap.add_argument("--loeschen", action="store_true",
                    help="Testentwuerfe wirklich in den Papierkorb verschieben")
    args = ap.parse_args()

    token = token_holen()
    identitaet_pruefen(token, args.postfach)
    print(f"Postfach: {args.postfach}\n")

    alle = entwuerfe_lesen(token)
    treffer = [e for e in alle if ist_testentwurf(e.get("subject"))]
    andere = len(alle) - len(treffer)

    print(f"Entwuerfe insgesamt : {len(alle)}")
    print(f"davon Testentwuerfe : {len(treffer)}")
    print(f"unberuehrt          : {andere}\n")

    if not treffer:
        print("Nichts aufzuraeumen.")
        return 0

    for i, e in enumerate(treffer, 1):
        anhang = "mit Anhang" if e.get("hasAttachments") else "ohne Anhang"
        print(f"[{i:2}] {str(e.get('createdDateTime'))[:16]}  "
              f"{str(e.get('subject'))[:58]:58}  -> {empfaenger(e)}  ({anhang})")

    if not args.loeschen:
        print(f"\nProbelauf - nichts geloescht. Zum Ausfuehren dieselbe Zeile "
              f"noch einmal mit --loeschen.")
        return 0

    print(f"\nVerschiebe {len(treffer)} Entwuerfe in den Papierkorb ...")
    fehler = 0
    for i, e in enumerate(treffer, 1):
        try:
            _graph("DELETE", f"/me/messages/{e['id']}", token)
            print(f"[{i:2}/{len(treffer)}] weg: {str(e.get('subject'))[:60]}")
        except Exception as fehlschlag:            # noqa: BLE001
            fehler += 1
            print(f"[{i:2}/{len(treffer)}] FEHLER: {str(fehlschlag)[:120]}")

    uebrig = [e for e in entwuerfe_lesen(token) if ist_testentwurf(e.get("subject"))]
    print(f"\nKontrolle: {len(uebrig)} Testentwuerfe noch im Ordner "
          f"(erwartet 0), {fehler} Fehler.")
    print("Die Entwuerfe liegen jetzt in 'Geloeschte Elemente' und sind von "
          "dort wiederherstellbar.")
    return 1 if (uebrig or fehler) else 0


if __name__ == "__main__":
    raise SystemExit(main())
