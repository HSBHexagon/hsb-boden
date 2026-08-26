"""
HSB Sales OS - Testmatrix.

Alle Tests laufen ohne echten externen Versand: REAL_EXTERNAL_SEND_COUNT=0.
Jeder Fall muss deterministisch und fail-closed reagieren.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from email import policy
from email.parser import BytesParser
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

from hsb_core import (  # noqa: E402
    FLYERS, AssetGateError, check_eligibility, make_batch_id, normalize_owner,
    sha256_bytes,
)
from batch_engine import prepare_batch, write_batch, explain_batch  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []
REAL_EXTERNAL_SEND_COUNT = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(condition), detail))
    print(f"{'PASS' if condition else 'FAIL'}  {name}"
          + (f"  ({detail})" if detail else ""))


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

def make_lead(i: int, owner: str = "JORDI", **over) -> dict:
    lead = {
        "Lead_ID": f"TEST-{owner}-{i:05d}",
        "Owner": "Jordi Post" if owner == "JORDI" else "Joel Cherino Diaz",
        "Email": f"kontakt{i}@beispiel-firma-{i}.de",
        "Company": f"Beispiel Firma {i} GmbH",
        "Contact": f"Herr Muster {i}",
        "Industry": "Lebensmittelindustrie",
        "Tier": "A" if i % 3 == 0 else "B",
        "Legal_Basis": "OPT_IN",
        "Versandfreigabe": "yes",
        "Suppressed": "no",
        "Opt_Out": "no",
        "Bounce_Status": "",
        "Send_Status": "not_sent",
    }
    lead.update(over)
    return lead


def pool(n: int, owner: str = "JORDI", **over) -> list[dict]:
    return [make_lead(i, owner, **over) for i in range(1, n + 1)]


# --------------------------------------------------------------------------
# 1. Dynamische Batchgroessen - der Kern der Anforderung
# --------------------------------------------------------------------------

def test_dynamic_counts() -> None:
    leads = pool(400, "JORDI") + pool(400, "JOEL")
    for owner, n in [("JORDI", 1), ("JORDI", 17), ("JORDI", 100),
                     ("JOEL", 1), ("JOEL", 25), ("JOEL", 100), ("JOEL", 250)]:
        b = prepare_batch(leads, owner, n)
        check(f"dynamisch {owner} count={n}",
              b.stats.selected_count == n,
              f"ausgewaehlt {b.stats.selected_count}")
        check(f"nur eigener Absender {owner} count={n}",
              all(normalize_owner(l["Owner"]) == owner for l in b.leads))


def test_count_zero_and_oversized() -> None:
    leads = pool(10, "JORDI")
    b0 = prepare_batch(leads, "JORDI", 0)
    check("count=0 liefert leeren Batch", b0.stats.selected_count == 0)

    b_over = prepare_batch(leads, "JORDI", 500)
    check("zu wenige eligible Leads -> Fehlbetrag ausgewiesen",
          b_over.stats.selected_count == 10 and b_over.stats.shortfall == 490,
          f"selected={b_over.stats.selected_count} shortfall={b_over.stats.shortfall}")


# --------------------------------------------------------------------------
# 2. Compliance-Gate - fail closed
# --------------------------------------------------------------------------

def test_compliance_gate() -> None:
    cases = [
        ("Legal_Basis=UNKNOWN blockiert", {"Legal_Basis": "UNKNOWN"}),
        ("Legal_Basis=BLOCKED blockiert", {"Legal_Basis": "BLOCKED"}),
        ("Versandfreigabe=no blockiert", {"Versandfreigabe": "no"}),
        ("Opt_Out=yes blockiert", {"Opt_Out": "yes"}),
        ("Suppressed=yes blockiert", {"Suppressed": "yes"}),
        ("Hard Bounce blockiert", {"Bounce_Status": "hard_bounce"}),
        ("bereits gesendet blockiert", {"Send_Status": "sent"}),
        ("ungueltige Adresse blockiert", {"Email": "kaputt-ohne-at"}),
        ("leere Adresse blockiert", {"Email": ""}),
    ]
    for name, over in cases:
        leads = pool(5, "JORDI", **over)
        b = prepare_batch(leads, "JORDI", 5)
        check(name, b.stats.selected_count == 0,
              f"selected={b.stats.selected_count}")

    ok = prepare_batch(pool(5, "JORDI"), "JORDI", 5)
    check("gueltige Leads passieren das Gate", ok.stats.selected_count == 5)

    check("EXISTING_CUSTOMER_7_3 ist sendefaehig",
          check_eligibility(make_lead(1, Legal_Basis="EXISTING_CUSTOMER_7_3")).eligible)
    check("OWNER_APPROVED ist neutral protokolliert und sendefaehig",
          check_eligibility(make_lead(1, Legal_Basis="OWNER_APPROVED")).eligible)

    check("leeres Legal_Basis faellt auf UNKNOWN zurueck",
          not check_eligibility(make_lead(1, Legal_Basis="", Opt_In="unknown")).eligible)


def test_gate_not_bypassable_by_count() -> None:
    """Das Gate darf nicht durch grosse Batchgroesse umgangen werden."""
    leads = pool(50, "JORDI", Versandfreigabe="no")
    for n in (1, 10, 999):
        b = prepare_batch(leads, "JORDI", n)
        check(f"Gate nicht umgehbar bei count={n}", b.stats.selected_count == 0)


# --------------------------------------------------------------------------
# 3. Dubletten- und Batchschutz
# --------------------------------------------------------------------------

def test_duplicate_protection() -> None:
    leads = pool(20, "JORDI")
    b1 = prepare_batch(leads, "JORDI", 10, seq=1)
    active = {l["Lead_ID"] for l in b1.leads}
    b2 = prepare_batch(leads, "JORDI", 10, seq=2, active_batch_lead_ids=active)
    overlap = active & {l["Lead_ID"] for l in b2.leads}
    check("kein Lead in zwei aktiven Batches", not overlap,
          f"Ueberschneidung: {len(overlap)}")
    check("zweiter Batch nimmt die naechsten Leads",
          b2.stats.selected_count == 10)

    ids = [l["Lead_ID"] for l in b1.leads]
    check("keine Dubletten innerhalb eines Batches", len(ids) == len(set(ids)))


def test_idempotenz() -> None:
    leads = pool(30, "JORDI")
    a = prepare_batch(leads, "JORDI", 10, seq=1)
    b = prepare_batch(leads, "JORDI", 10, seq=1)
    check("gleiche Eingabe -> gleiche Auswahl (deterministisch)",
          [l["Lead_ID"] for l in a.leads] == [l["Lead_ID"] for l in b.leads])


def test_duplicate_email_in_source() -> None:
    # Gleiche Adresse, UNTERSCHIEDLICHE Lead-IDs - der Fall, den ein reiner
    # Lead-ID-Abgleich nicht faengt.
    leads = pool(5, "JORDI")
    twin = make_lead(99, "JORDI")
    twin["Email"] = leads[0]["Email"]
    leads.append(twin)
    check("Testaufbau: 6 Leads, 5 eindeutige Adressen",
          len(leads) == 6 and len({l["Email"] for l in leads}) == 5)

    b = prepare_batch(leads, "JORDI", 10)
    emails = [l["Email"] for l in b.leads]
    check("doppelte E-Mail wird nicht doppelt versendet",
          len(emails) == len(set(emails)),
          f"{len(emails)} Adressen, {len(set(emails))} eindeutig")
    check("genau ein Datensatz je Adresse ausgewaehlt",
          b.stats.selected_count == 5, f"selected={b.stats.selected_count}")

    ids = [l["Lead_ID"] for l in b.leads]
    check("Lead-ID-Dubletten ebenfalls ausgeschlossen",
          len(ids) == len(set(ids)))


# --------------------------------------------------------------------------
# 4. Asset-Gate und Cross-Sender
# --------------------------------------------------------------------------

def test_asset_gate() -> None:
    for key, flyer in FLYERS.items():
        try:
            b = prepare_batch(pool(3, key), key, 3)
            check(f"Asset-Gate {key} bestanden",
                  b.asset_sha256 == flyer.sha256)
            check(f"Drive-ID {key} korrekt hinterlegt",
                  b.asset_drive_id == flyer.drive_id)
        except AssetGateError as exc:
            check(f"Asset-Gate {key} bestanden", False, str(exc))

    try:
        prepare_batch(pool(3), "UNBEKANNT", 3)
        check("unbekannter Absender wird abgewiesen", False)
    except AssetGateError:
        check("unbekannter Absender wird abgewiesen", True)


def test_zero_cross_sender_attachments() -> None:
    """Jordi darf niemals Joels PDF bekommen und umgekehrt."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ok = True
        detail = ""
        for key, flyer in FLYERS.items():
            other = FLYERS["JOEL" if key == "JORDI" else "JORDI"]
            b = prepare_batch(pool(4, key), key, 4)
            out = write_batch(b, root=root)
            for eml in (out / "drafts").glob("*.eml"):
                msg = BytesParser(policy=policy.default).parsebytes(eml.read_bytes())
                atts = [p for p in msg.walk()
                        if p.get_content_maintype() == "application"
                        and p.get_filename()]
                if len(atts) != 1:
                    ok, detail = False, f"{eml.name}: {len(atts)} Anhaenge"
                    break
                data = atts[0].get_payload(decode=True)
                h = sha256_bytes(data)
                if h != flyer.sha256:
                    ok, detail = False, f"{eml.name}: Hash {h[:12]}"
                    break
                if h == other.sha256:
                    ok, detail = False, f"{eml.name}: FREMDER FLYER"
                    break
                if atts[0].get_filename() != flyer.filename:
                    ok, detail = False, f"{eml.name}: falscher Dateiname"
                    break
        check("ZERO_CROSS_SENDER_ATTACHMENTS", ok, detail)


# --------------------------------------------------------------------------
# 5. EML-Struktur
# --------------------------------------------------------------------------

def test_eml_structure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        b = prepare_batch(pool(3, "JORDI"), "JORDI", 3, campaign="test-kampagne")
        out = write_batch(b, root=Path(tmp))
        emls = sorted((out / "drafts").glob("*.eml"))
        check("eine EML pro Lead", len(emls) == 3, f"{len(emls)} Dateien")

        msg = BytesParser(policy=policy.default).parsebytes(emls[0].read_bytes())
        check("X-Unsent: 1 gesetzt", msg["X-Unsent"] == "1", str(msg["X-Unsent"]))
        check("X-HSB-Lead-ID gesetzt", bool(msg["X-HSB-Lead-ID"]))
        check("X-HSB-Batch-ID gesetzt", msg["X-HSB-Batch-ID"] == b.batch_id)
        check("From ist die Absender-Mailbox",
              FLYERS["JORDI"].mailbox in str(msg["From"]))
        check("Reply-To gesetzt", FLYERS["JORDI"].mailbox in str(msg["Reply-To"]))
        check("To ist befuellt", "@" in str(msg["To"]))
        check("Betreff enthaelt Firma", "Beispiel Firma" in str(msg["Subject"]))
        body = msg.get_body(preferencelist=("plain",)).get_content()
        check("Abmeldehinweis im Text", "Abmelden" in body)
        # Geschaeftsuebliche Anrede: Vorname/Zaehler entfaellt.
        check("Ansprechpartner personalisiert",
              "Guten Tag Herr Muster," in body)

        check("manifest.json vorhanden", (out / "manifest.json").exists())
        check("status.csv vorhanden", (out / "status.csv").exists())
        man = json.loads((out / "manifest.json").read_text())
        check("Manifest kennt den Asset-Hash",
              man["asset_sha256"] == FLYERS["JORDI"].sha256)


def test_malformed_recipients() -> None:
    bad = ["", "keinatzeichen", "@keindomain.de", "a@b", "zwei@@at.de", None]
    leads = [make_lead(i, "JORDI", Email=v) for i, v in enumerate(bad, 1)]
    b = prepare_batch(leads, "JORDI", 10)
    check("alle fehlerhaften Adressen abgewiesen", b.stats.selected_count == 0,
          f"selected={b.stats.selected_count}")


# --------------------------------------------------------------------------
# 6. Filter, leerer Batch, Erklaerbarkeit
# --------------------------------------------------------------------------

def test_filters() -> None:
    leads = pool(60, "JORDI")
    b = prepare_batch(leads, "JORDI", 100, tier="A")
    check("Tier-Filter greift",
          all(str(l["Tier"]).upper() == "A" for l in b.leads) and b.leads)
    b2 = prepare_batch(leads, "JORDI", 5, industry="Lebensmittelindustrie")
    check("Branchen-Filter greift", b2.stats.selected_count == 5)
    b3 = prepare_batch(leads, "JORDI", 5, industry="Gibt-Es-Nicht")
    check("unbekannte Branche -> leerer Batch", b3.stats.selected_count == 0)


def test_empty_batch_is_explained() -> None:
    leads = pool(50, "JORDI", Versandfreigabe="no", Legal_Basis="UNKNOWN")
    b = prepare_batch(leads, "JORDI", 100)
    text = explain_batch(b)
    check("leerer Batch hat Status EMPTY_NO_ELIGIBLE_LEADS",
          b.status == "EMPTY_NO_ELIGIBLE_LEADS", b.status)
    check("Ausschlussgruende werden gezaehlt",
          b.stats.no_legal_basis_count == 50 and b.stats.no_release_count == 50,
          f"legal={b.stats.no_legal_basis_count} freigabe={b.stats.no_release_count}")
    check("Erklaerung nennt den naechsten Schritt",
          "qualifiziert" in text and "Versandfreigabe=YES" in text)


def test_batch_id_format() -> None:
    bid = make_batch_id("JORDI", 1)
    parts = bid.split("-")
    check("Batch-ID Format HSB-JJJJMMTT-OWNER-NNNN",
          len(parts) == 4 and parts[0] == "HSB" and parts[2] == "JORDI"
          and len(parts[1]) == 8 and len(parts[3]) == 4, bid)


def test_owner_normalisation() -> None:
    for raw, want in [("Jordi Post", "JORDI"), ("jordi", "JORDI"),
                      ("Joel Cherino Diaz", "JOEL"), ("JOEL", "JOEL"),
                      ("j-cherino", "JOEL")]:
        check(f"Owner-Normalisierung {raw!r} -> {want}",
              normalize_owner(raw) == want, normalize_owner(raw))


# --------------------------------------------------------------------------
# 7. Reale Daten
# --------------------------------------------------------------------------

def test_anrede() -> None:
    """Die Anrede darf kuerzen, aber niemals falsch kuerzen."""
    from batch_engine import anrede
    faelle = [
        # (Eingabe, Erwartung, Begruendung)
        ("Frau Franziska Koch", "Frau Koch", "Vor- und Nachname"),
        ("Herr Ulrich Robert Hägele", "Herr Hägele", "zweiter Vorname"),
        ("Herr Jan van den Berg", "Herr van den Berg", "Namenszusatz vorn"),
        ("Frau Birgit Wrocklage-aus der Fünten",
         "Frau Birgit Wrocklage-aus der Fünten", "Zusatz mittig: unklar"),
        ("Herr Muster 1", "Herr Muster", "Zaehler am Ende"),
        ("Frau Koch", "Frau Koch", "bereits kurz"),
        ("Dr. Meier", "Dr. Meier", "keine Anredeform erkennbar"),
        ("Muhtesim Dumlu", "Muhtesim Dumlu", "kein Herr/Frau"),
        ("  Frau   Franziska   Koch  ", "Frau Koch", "Mehrfach-Leerzeichen"),
        ("", "", "leer"),
        (None, "", "None"),
    ]
    for eingabe, erwartet, warum in faelle:
        ist = anrede(eingabe)
        check(f"Anrede ({warum})", ist == erwartet,
              f"{eingabe!r} -> {ist!r}, erwartet {erwartet!r}")

    # Zusicherung ueber die realen Daten: die Anrede ist immer die Anredeform
    # plus ein zusammenhaengendes Ende des Namens. Damit kann nie ein Stueck
    # aus der Mitte stehenbleiben und nie ein fremder Name entstehen.
    from sheet_loader import load_from_xlsx
    verstoesse, leer = [], 0
    for lead in load_from_xlsx():
        roh = " ".join(str(lead.get("Contact") or "").split())
        if not roh:
            continue
        ist = anrede(roh)
        if not ist:
            leer += 1
            continue
        if ist == roh:
            continue
        teile_roh, teile_ist = roh.split(), ist.split()
        passt = (teile_ist[0] == teile_roh[0]
                 and teile_roh[-len(teile_ist) + 1:] == teile_ist[1:])
        if not passt:
            verstoesse.append((roh, ist))
    check("reale Daten: Anrede nie leer bei vorhandenem Kontakt", leer == 0,
          f"{leer} leere Anreden")
    check("reale Daten: Anrede ist immer Anredeform + Namensende",
          not verstoesse,
          f"{len(verstoesse)} Verstoesse, z. B. {verstoesse[:2]}")


def test_real_data_snapshot() -> None:
    try:
        from sheet_loader import load_from_xlsx, summarize
        leads = load_from_xlsx()
    except Exception as exc:                       # pragma: no cover
        check("realer Sheet-Snapshot ladbar", False, str(exc))
        return

    check("realer Sheet-Snapshot ladbar", len(leads) == 6424, f"{len(leads)} Zeilen")
    s = summarize(leads)
    jordi = s["per_owner"].get("JORDI", {})
    joel = s["per_owner"].get("JOEL", {})
    check("Aufteilung 3212/3212",
          jordi.get("total") == 3212 and joel.get("total") == 3212,
          f"JORDI={jordi.get('total')} JOEL={joel.get('total')}")

    b = prepare_batch(leads, "JORDI", 100)
    # Frueher stand hier selected_count == 0. Das war keine Regel, sondern der
    # damalige Datenstand: es war noch nichts qualifiziert. Inzwischen sind
    # Kontakte freigegeben, und die Zahl aendert sich weiter. Geprueft wird
    # deshalb die eigentliche Zusicherung: es wird nie mehr ausgewaehlt als
    # tatsaechlich sendefaehig ist, und jeder Ausgewaehlte traegt Rechts-
    # grundlage und Versandfreigabe.
    check("reale Daten: nie mehr ausgewaehlt als sendefaehig",
          b.stats.selected_count <= b.stats.eligible_count,
          f"selected={b.stats.selected_count} eligible={b.stats.eligible_count}")
    unerlaubt = [l for l in b.leads if not check_eligibility(l).eligible]
    check("reale Daten: kein Ausgewaehlter ohne Rechtsgrundlage/Freigabe",
          not unerlaubt, f"{len(unerlaubt)} unerlaubte Treffer")

    # Nach Qualifizierung muss derselbe Aufruf 100 liefern.
    qualified = []
    for lead in leads:
        l = dict(lead)
        if normalize_owner(l.get("Owner")) == "JORDI":
            l["Legal_Basis"] = "OPT_IN"
            l["Versandfreigabe"] = "yes"
        qualified.append(l)
    b2 = prepare_batch(qualified, "JORDI", 100)
    check("reale Daten: nach Qualifizierung liefert JORDI+100 genau 100",
          b2.stats.selected_count == 100, f"selected={b2.stats.selected_count}")
    b3 = prepare_batch(qualified, "JORDI", 250)
    check("reale Daten: JORDI+250 liefert 250",
          b3.stats.selected_count == 250, f"selected={b3.stats.selected_count}")


# --------------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("HSB SALES OS - TESTMATRIX")
    print("=" * 70)
    for fn in [
        test_dynamic_counts, test_count_zero_and_oversized,
        test_compliance_gate, test_gate_not_bypassable_by_count,
        test_duplicate_protection, test_idempotenz, test_duplicate_email_in_source,
        test_asset_gate, test_zero_cross_sender_attachments,
        test_eml_structure, test_malformed_recipients,
        test_filters, test_empty_batch_is_explained,
        test_batch_id_format, test_owner_normalisation,
        test_anrede,
        test_real_data_snapshot,
    ]:
        print(f"\n--- {fn.__name__} ---")
        try:
            fn()
        except Exception as exc:
            check(f"{fn.__name__} ohne Ausnahme", False, repr(exc))

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    print("\n" + "=" * 70)
    print(f"ERGEBNIS: {passed} bestanden, {failed} fehlgeschlagen "
          f"von {len(RESULTS)}")
    print(f"REAL_EXTERNAL_SEND_COUNT={REAL_EXTERNAL_SEND_COUNT}")
    print("=" * 70)
    if failed:
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"  FAIL: {name} {detail}")
    summary = {"test_count": len(RESULTS), "test_pass": passed,
               "test_fail": failed,
               "real_external_send_count": REAL_EXTERNAL_SEND_COUNT}
    Path(__file__).parent.joinpath("last_run.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
