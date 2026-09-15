#!/usr/bin/env python3
"""
HSB Sales OS - Entwuerfe erzeugen und jede einzelne Datei nachpruefen.

Erzeugt fuer einen bereits im Sheet reservierten Batch genau eine EML pro
Kontakt: richtiger Empfaenger, richtiger Ansprechpartner im Text, richtiger
Flyer als Anhang. Danach wird jede Datei wieder eingelesen und gegen die
Quelldaten geprueft - eine unbemerkt falsche Anrede oder ein vertauschter
Flyer ist damit ausgeschlossen.

Dieses Werkzeug sendet nichts. Es schreibt Dateien.

    python3 engine/make_drafts.py --batch HSB-20260826-JORDI-0002
    python3 engine/make_drafts.py --batch ... --out ~/Desktop/HSB-Entwuerfe
"""
from __future__ import annotations

import argparse
import csv
import json
import email
import email.policy
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_engine import (Batch, BatchStats, anrede, build_eml,
                          render_email)
from hsb_core import (REPO_ROOT, assert_asset_gate, normalize_owner,
                      sha256_bytes, utc_now_iso)
from sheet_loader import load_from_xlsx

STANDARD_ZIEL = Path.home() / "Desktop" / "HSB-Entwuerfe"


def _dateiname(index: int, lead: dict) -> str:
    """Sortierbarer, im Finder lesbarer Name ohne Sonderzeichen."""
    firma = str(lead.get("Company") or "Unbekannt")
    sicher = "".join(c if (c.isalnum() or c in " -_") else "-" for c in firma)
    return f"{index:03d}_{sicher.strip()[:60]}.eml"


def _batch_aus_leads(batch_id: str, leads: list[dict]) -> Batch:
    owner_key = normalize_owner(leads[0].get("Owner"))
    fremde = {normalize_owner(l.get("Owner")) for l in leads} - {owner_key}
    if fremde:
        raise SystemExit(
            f"ABBRUCH: Batch {batch_id} enthaelt mehrere Absender {fremde}. "
            "Ein Batch gehoert genau einem Absender - sonst wuerde der "
            "falsche Flyer verschickt."
        )
    flyer = assert_asset_gate(owner_key)
    return Batch(
        batch_id=batch_id, owner_key=owner_key,
        owner_display=flyer.display_name, mailbox=flyer.mailbox,
        campaign="", created_at=utc_now_iso(),
        asset_filename=flyer.path.name, asset_drive_id=flyer.drive_id,
        asset_sha256=flyer.sha256, status="PREPARED",
        stats=BatchStats(selected_count=len(leads)), leads=leads,
    )


def _pruefe(pfad: Path, lead: dict, batch: Batch, pdf_sha: str) -> list[str]:
    """Liest die geschriebene Datei zurueck. Gibt gefundene Maengel zurueck."""
    maengel: list[str] = []
    msg = email.message_from_bytes(pfad.read_bytes(), policy=email.policy.default)

    soll_email = str(lead.get("Email") or "").strip()
    if msg["To"] != soll_email:
        maengel.append(f"Empfaenger {msg['To']!r} statt {soll_email!r}")
    if batch.mailbox not in str(msg["From"]):
        maengel.append(f"Absender {msg['From']!r} enthaelt nicht {batch.mailbox}")
    if msg["X-Unsent"] != "1":
        maengel.append("X-Unsent fehlt - Outlook wuerde die Datei nicht als "
                       "Entwurf oeffnen")
    if msg["X-HSB-Batch-ID"] != batch.batch_id:
        maengel.append("Batch-Kennung im Kopf weicht ab")

    koerper = msg.get_body(preferencelist=("plain",))
    text = koerper.get_content() if koerper else ""
    kontakt = anrede(lead.get("Contact"))
    if kontakt and f"Guten Tag {kontakt}," not in text:
        maengel.append(f"Anrede fuer {kontakt!r} fehlt im Text")
    if not kontakt and "Guten Tag," not in text:
        maengel.append("Neutrale Anrede fehlt im Text")
    if batch.owner_display not in text:
        maengel.append("Absendername fehlt im Text")
    firma = str(lead.get("Company") or "").strip()
    if firma and firma not in str(msg["Subject"]):
        maengel.append(f"Firma {firma!r} fehlt im Betreff")

    anhaenge = [t for t in msg.iter_attachments()]
    if len(anhaenge) != 1:
        maengel.append(f"{len(anhaenge)} Anhaenge statt genau einem")
    else:
        roh = anhaenge[0].get_payload(decode=True)
        if sha256_bytes(roh) != pdf_sha:
            maengel.append("Anhang ist nicht der kanonische Flyer")
        if anhaenge[0].get_filename() != batch.asset_filename:
            maengel.append(f"Anhang heisst {anhaenge[0].get_filename()!r}")
    return maengel


def _pakete(entwuerfe: Path, ziel: Path, groesse: int) -> list[Path]:
    """Buendelt die Entwuerfe in handliche ZIP-Pakete zum Weitergeben.

    Eine einzelne EML traegt den kompletten Flyer als Base64 und ist damit
    rund 2 MB gross. Ein Paket aus allen 100 waere unhandlich; in Bloecken zu
    20 laesst es sich verschicken und einzeln importieren. Vorhandene Pakete
    desselben Batches werden ersetzt, damit kein alter Stand liegenbleibt.
    """
    ordner = ziel / "Pakete"
    ordner.mkdir(exist_ok=True)
    for alt in ordner.glob("*.zip"):
        alt.unlink()
    dateien = sorted(entwuerfe.glob("*.eml"))
    bloecke = [dateien[i:i + groesse] for i in range(0, len(dateien), groesse)]
    raus = []
    for nr, block in enumerate(bloecke, 1):
        pfad = ordner / f"Paket-{nr}-von-{len(bloecke)}.zip"
        with ZipFile(pfad, "w", ZIP_DEFLATED) as z:
            for datei in block:
                z.write(datei, arcname=datei.name)
        raus.append(pfad)
    return raus


def _rueckschreiben(leads: list[dict], ziel: Path, datum: str) -> str:
    """Beschreibt, wo im Sheet das Entwurfsdatum einzutragen ist.

    Dieses Werkzeug hat selbst keinen Schreibzugriff auf das Sheet - es
    arbeitet auf einem Export. Damit die Spalte "Entwurf erstellt" nicht
    stillschweigend leer bleibt und VERSAND faelschlich "kein Entwurf" zeigt,
    wird der genaue Bereich hier ausgegeben und als Datei hinterlegt.
    """
    zeilen = sorted(l.get("_row", 0) for l in leads if l.get("_row"))
    if not zeilen:
        return ""
    lueckenlos = zeilen == list(range(zeilen[0], zeilen[-1] + 1))
    bereich = (f"ALL_LEADS!AX{zeilen[0]}:AX{zeilen[-1]}" if lueckenlos
               else "mehrere Bereiche - siehe " + str(ziel / "sheet_update.json"))
    (ziel / "sheet_update.json").write_text(json.dumps(
        {"spalte": "Drafted_At (AX)", "wert": datum, "zeilen": zeilen,
         "zusammenhaengend": lueckenlos, "bereich": bereich},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return bereich


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True, help="Batch_ID aus dem Sheet")
    ap.add_argument("--out", default=str(STANDARD_ZIEL),
                    help=f"Zielordner (Standard: {STANDARD_ZIEL})")
    ap.add_argument("--xlsx", default=None, help="Sheet-Export, sonst neuester")
    ap.add_argument("--paketgroesse", type=int, default=20,
                    help="Dateien je ZIP-Paket; 0 schaltet das Packen ab")
    args = ap.parse_args()

    leads = [l for l in load_from_xlsx(args.xlsx)
             if str(l.get("Batch_ID") or "").strip() == args.batch]
    if not leads:
        raise SystemExit(f"ABBRUCH: Kein Kontakt mit Batch_ID {args.batch!r} "
                         "im Sheet-Export gefunden.")

    ohne_mail = [l for l in leads if not str(l.get("Email") or "").strip()]
    if ohne_mail:
        raise SystemExit(f"ABBRUCH: {len(ohne_mail)} Kontakte ohne E-Mail-Adresse.")

    batch = _batch_aus_leads(args.batch, leads)
    pdf = Path(batch.asset_filename)
    pdf_pfad = REPO_ROOT / "assets" / "canonical" / pdf.name
    pdf_bytes = pdf_pfad.read_bytes()
    pdf_sha = sha256_bytes(pdf_bytes)

    ziel = Path(args.out).expanduser() / args.batch
    entwuerfe = ziel / "Entwuerfe"
    entwuerfe.mkdir(parents=True, exist_ok=True)
    for alt in entwuerfe.glob("*.eml"):
        alt.unlink()

    print(f"Batch      : {batch.batch_id}")
    print(f"Absender   : {batch.owner_display} <{batch.mailbox}>")
    print(f"Flyer      : {batch.asset_filename}  sha256={pdf_sha[:12]}...")
    print(f"Kontakte   : {len(leads)}")
    print(f"Zielordner : {entwuerfe}\n")

    zeilen, alle_maengel = [], []
    for i, lead in enumerate(sorted(leads, key=lambda l: str(l.get("Lead_ID") or "")), 1):
        pfad = entwuerfe / _dateiname(i, lead)
        pfad.write_bytes(build_eml(lead, batch, pdf_bytes))
        maengel = _pruefe(pfad, lead, batch, pdf_sha)
        if maengel:
            alle_maengel.append((pfad.name, maengel))
        betreff, _ = render_email(lead, batch)
        zeilen.append({
            "Nr": i, "Datei": pfad.name,
            "Firma": lead.get("Company") or "",
            "Ansprechpartner": lead.get("Contact") or "",
            "E-Mail": lead.get("Email") or "",
            "Betreff": betreff,
            "Lead-ID": lead.get("Lead_ID") or "",
            "Geprueft": "OK" if not maengel else "; ".join(maengel),
        })

    with open(ziel / "Uebersicht.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)

    if alle_maengel:
        print(f"PRUEFUNG=FAIL - {len(alle_maengel)} von {len(zeilen)} Dateien "
              "fehlerhaft:")
        for name, m in alle_maengel[:10]:
            print(f"  {name}: {'; '.join(m)}")
        return 1

    print(f"PRUEFUNG=PASS - {len(zeilen)}/{len(zeilen)} Entwuerfe erzeugt und "
          "einzeln nachgeprueft.")
    print(f"Uebersicht : {ziel / 'Uebersicht.csv'}")
    if args.paketgroesse:
        pakete = _pakete(entwuerfe, ziel, args.paketgroesse)
        gesamt = sum(p.stat().st_size for p in pakete) / 1e6
        print(f"Pakete     : {len(pakete)} ZIP-Dateien, zusammen "
              f"{gesamt:.0f} MB, in {ziel / 'Pakete'}")
    heute = utc_now_iso()[:10]
    bereich = _rueckschreiben(leads, ziel, heute)
    if bereich:
        print(f"\nNoch im Sheet einzutragen: Spalte 'Drafted_At' auf {heute}")
        print(f"  Bereich: {bereich}")
        print("  Sonst zeigt das Blatt VERSAND fuer diese Kontakte weiterhin "
              "'kein Entwurf'.")

    print("\nEs wurde nichts versendet.")
    print("Zum Import: die Dateien in Outlook in den Ordner 'Entwuerfe' des "
          "Postfachs ziehen.")
    print("Hinweis: die Kopfzeile X-Unsent wird von Outlook fuer Mac ignoriert "
          "und im neuen\nOutlook nicht mehr zuverlaessig ausgewertet - "
          "Doppelklick oeffnet die Datei dann als\nempfangene Nachricht statt "
          "als Entwurf. Der belastbare Weg ist "
          "engine/graph_drafts.py,\ndas den Entwurf direkt im Postfach anlegt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
