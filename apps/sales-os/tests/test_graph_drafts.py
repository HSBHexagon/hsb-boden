"""
HSB Sales OS - Tests fuer den delegierten Geraetecode-Anmeldefluss in
engine/graph_drafts.py.

Kein echter Netzwerkzugriff: alle Graph-/Login-Aufrufe werden an den in
graph_drafts definierten Nahtstellen (_mit_refresh_token,
_interaktive_geraetecode_anmeldung, _device_code_anfordern, _token_anfrage,
_graph) durch Fakes ersetzt. REAL_EXTERNAL_SEND_COUNT=0 - dieses Werkzeug
legt ohnehin nur Entwuerfe an, nie einen Versand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

import graph_drafts as gd  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(condition), detail))
    print(f"{'PASS' if condition else 'FAIL'}  {name}"
          + (f"  ({detail})" if detail else ""))


def _tmp_cache(tmp_path: Path) -> Path:
    return tmp_path / "cache.json"


def _mit_tmp_cache(fn, tmp_path: Path):
    """Fuehrt fn() mit TOKEN_CACHE auf eine temporaere Datei umgebogen aus
    und stellt den vorherigen Wert danach zuverlaessig wieder her."""
    original = gd.TOKEN_CACHE
    gd.TOKEN_CACHE = _tmp_cache(tmp_path)
    try:
        return fn()
    finally:
        gd.TOKEN_CACHE = original


# --------------------------------------------------------------------------
# token_holen(): Entscheidungsbaum Cache -> Refresh -> Geraetecode
# --------------------------------------------------------------------------

def test_ohne_cache_wird_geraetecode_angemeldung_verwendet(tmp_path):
    aufrufe = {"geraetecode": 0, "refresh": 0}

    def fake_refresh(tenant, client_id, refresh_token):
        aufrufe["refresh"] += 1
        return None  # sollte nie erreicht werden - kein Cache vorhanden

    def fake_geraetecode(tenant, client_id):
        aufrufe["geraetecode"] += 1
        return {"access_token": "AT-1", "refresh_token": "RT-1"}

    orig_refresh = gd._mit_refresh_token
    orig_gc = gd._interaktive_geraetecode_anmeldung
    gd._mit_refresh_token = fake_refresh
    gd._interaktive_geraetecode_anmeldung = fake_geraetecode
    import os
    os.environ["HSB_GRAPH_TENANT_ID"] = "tenant-x"
    os.environ["HSB_GRAPH_CLIENT_ID"] = "client-x"
    try:
        token = _mit_tmp_cache(gd.token_holen, tmp_path)
    finally:
        gd._mit_refresh_token = orig_refresh
        gd._interaktive_geraetecode_anmeldung = orig_gc

    check("Ohne Cache: kein Refresh-Versuch (aufrufe.refresh == 0)",
          aufrufe["refresh"] == 0, str(aufrufe))
    check("Ohne Cache: genau eine Geraetecode-Anmeldung",
          aufrufe["geraetecode"] == 1, str(aufrufe))
    check("Ohne Cache: Zugriffstoken kommt aus der Geraetecode-Antwort",
          token == "AT-1")

    cache_inhalt = json.loads(_tmp_cache(tmp_path).read_text(encoding="utf-8"))
    check("Nach Geraetecode-Anmeldung wird das Refresh-Token gespeichert",
          cache_inhalt.get("refresh_token") == "RT-1", str(cache_inhalt))


def test_gueltiges_refresh_token_umgeht_geraetecode_anmeldung(tmp_path):
    aufrufe = {"geraetecode": 0, "refresh": 0}
    _tmp_cache(tmp_path).write_text(
        json.dumps({"refresh_token": "RT-alt"}), encoding="utf-8")

    def fake_refresh(tenant, client_id, refresh_token):
        aufrufe["refresh"] += 1
        check("Refresh-Versuch nutzt das gecachte Token",
              refresh_token == "RT-alt", refresh_token)
        return {"access_token": "AT-2", "refresh_token": "RT-neu"}

    def fake_geraetecode(tenant, client_id):
        aufrufe["geraetecode"] += 1
        return {"access_token": "AT-FALLBACK"}

    orig_refresh = gd._mit_refresh_token
    orig_gc = gd._interaktive_geraetecode_anmeldung
    gd._mit_refresh_token = fake_refresh
    gd._interaktive_geraetecode_anmeldung = fake_geraetecode
    import os
    os.environ["HSB_GRAPH_TENANT_ID"] = "tenant-x"
    os.environ["HSB_GRAPH_CLIENT_ID"] = "client-x"
    try:
        token = _mit_tmp_cache(gd.token_holen, tmp_path)
    finally:
        gd._mit_refresh_token = orig_refresh
        gd._interaktive_geraetecode_anmeldung = orig_gc

    check("Gueltiges Refresh-Token: KEINE erneute Geraetecode-Anmeldung "
          "(kein Login-Zwang bei jedem Lauf)",
          aufrufe["geraetecode"] == 0, str(aufrufe))
    check("Gueltiges Refresh-Token: genau ein stiller Refresh-Versuch",
          aufrufe["refresh"] == 1, str(aufrufe))
    check("Zugriffstoken stammt aus dem Refresh", token == "AT-2")

    cache_inhalt = json.loads(_tmp_cache(tmp_path).read_text(encoding="utf-8"))
    check("Rotiertes Refresh-Token wird nachgefuehrt",
          cache_inhalt.get("refresh_token") == "RT-neu", str(cache_inhalt))


def test_ungueltiges_refresh_token_faellt_zurueck_auf_geraetecode(tmp_path):
    aufrufe = {"geraetecode": 0}
    _tmp_cache(tmp_path).write_text(
        json.dumps({"refresh_token": "RT-abgelaufen"}), encoding="utf-8")

    def fake_refresh(tenant, client_id, refresh_token):
        return None  # z. B. invalid_grant - Refresh-Token nicht mehr gueltig

    def fake_geraetecode(tenant, client_id):
        aufrufe["geraetecode"] += 1
        return {"access_token": "AT-3", "refresh_token": "RT-frisch"}

    orig_refresh = gd._mit_refresh_token
    orig_gc = gd._interaktive_geraetecode_anmeldung
    gd._mit_refresh_token = fake_refresh
    gd._interaktive_geraetecode_anmeldung = fake_geraetecode
    import os
    os.environ["HSB_GRAPH_TENANT_ID"] = "tenant-x"
    os.environ["HSB_GRAPH_CLIENT_ID"] = "client-x"
    try:
        token = _mit_tmp_cache(gd.token_holen, tmp_path)
    finally:
        gd._mit_refresh_token = orig_refresh
        gd._interaktive_geraetecode_anmeldung = orig_gc

    check("Abgelaufenes/ungueltiges Refresh-Token loest genau einen "
          "Geraetecode-Fallback aus", aufrufe["geraetecode"] == 1, str(aufrufe))
    check("Zugriffstoken stammt aus dem Fallback", token == "AT-3")


def test_kein_client_secret_mehr_noetig(tmp_path):
    import os
    os.environ["HSB_GRAPH_TENANT_ID"] = "tenant-x"
    os.environ["HSB_GRAPH_CLIENT_ID"] = "client-x"
    os.environ.pop("HSB_GRAPH_CLIENT_SECRET", None)

    orig_refresh = gd._mit_refresh_token
    orig_gc = gd._interaktive_geraetecode_anmeldung
    gd._mit_refresh_token = lambda *a: None
    gd._interaktive_geraetecode_anmeldung = lambda *a: {"access_token": "AT-4"}
    try:
        token = _mit_tmp_cache(gd.token_holen, tmp_path)
        ok = True
        fehler = ""
    except SystemExit as e:
        ok = False
        fehler = str(e)
    finally:
        gd._mit_refresh_token = orig_refresh
        gd._interaktive_geraetecode_anmeldung = orig_gc

    check("token_holen() verlangt HSB_GRAPH_CLIENT_SECRET nicht mehr",
          ok, fehler)


# --------------------------------------------------------------------------
# _interaktive_geraetecode_anmeldung(): Polling-Zustandsmaschine
# --------------------------------------------------------------------------

def test_geraetecode_polling_wartet_bei_authorization_pending_und_erfolgt_dann():
    antworten = iter([
        {"error": "authorization_pending"},
        {"error": "authorization_pending"},
        {"access_token": "AT-POLL", "refresh_token": "RT-POLL"},
    ])
    schlaef_aufrufe = []

    orig_device = gd._device_code_anfordern
    orig_token = gd._token_anfrage
    orig_sleep = gd.time.sleep
    gd._device_code_anfordern = lambda tenant, cid: {
        "device_code": "DC-1", "user_code": "ABC-123",
        "verification_uri": "https://microsoft.com/devicelogin",
        "interval": 1, "expires_in": 900,
    }
    gd._token_anfrage = lambda tenant, felder: next(antworten)
    gd.time.sleep = lambda s: schlaef_aufrufe.append(s)
    try:
        ergebnis = gd._interaktive_geraetecode_anmeldung("tenant-x", "client-x")
    finally:
        gd._device_code_anfordern = orig_device
        gd._token_anfrage = orig_token
        gd.time.sleep = orig_sleep

    check("Polling liefert am Ende das Zugriffstoken",
          ergebnis.get("access_token") == "AT-POLL", str(ergebnis))
    check("Polling versucht es mehrfach, bis 'authorization_pending' endet",
          len(schlaef_aufrufe) == 3, str(schlaef_aufrufe))


def test_geraetecode_polling_bricht_bei_ablehnung_fail_closed_ab():
    orig_device = gd._device_code_anfordern
    orig_token = gd._token_anfrage
    orig_sleep = gd.time.sleep
    gd._device_code_anfordern = lambda tenant, cid: {
        "device_code": "DC-2", "user_code": "XYZ-999",
        "verification_uri": "https://microsoft.com/devicelogin",
        "interval": 1, "expires_in": 900,
    }
    gd._token_anfrage = lambda tenant, felder: {
        "error": "authorization_declined",
        "error_description": "Nutzer hat abgelehnt",
    }
    gd.time.sleep = lambda s: None
    fehler = None
    try:
        gd._interaktive_geraetecode_anmeldung("tenant-x", "client-x")
    except gd.GraphFehler as e:
        fehler = str(e)
    finally:
        gd._device_code_anfordern = orig_device
        gd._token_anfrage = orig_token
        gd.time.sleep = orig_sleep

    check("Abgelehnte Geraetecode-Anmeldung bricht fail-closed ab "
          "(keine Endlosschleife, kein stillschweigendes Weiterlaufen)",
          fehler is not None and "abgelehnt" in fehler.lower(), str(fehler))


# --------------------------------------------------------------------------
# identitaet_pruefen() / entwurf_anlegen(): /me statt beliebigem Postfach
# --------------------------------------------------------------------------

def test_identitaet_pruefen_akzeptiert_passendes_postfach():
    orig = gd._graph
    gd._graph = lambda methode, pfad, token, *a, **kw: {"mail": "j-post@hsb-boden.de"}
    try:
        gd.identitaet_pruefen("tok", "j-post@hsb-boden.de")
        ok = True
    except gd.GraphFehler:
        ok = False
    finally:
        gd._graph = orig
    check("identitaet_pruefen: passendes /me-Postfach wird akzeptiert", ok)


def test_identitaet_pruefen_lehnt_falsches_postfach_fail_closed_ab():
    orig = gd._graph
    gd._graph = lambda methode, pfad, token, *a, **kw: {"mail": "j-cherino@hsb-boden.de"}
    fehler = None
    try:
        gd.identitaet_pruefen("tok", "j-post@hsb-boden.de")
    except gd.GraphFehler as e:
        fehler = str(e)
    finally:
        gd._graph = orig
    check("identitaet_pruefen: falsches /me-Postfach wird fail-closed "
          "abgelehnt (keine Entwuerfe im falschen Postfach)",
          fehler is not None, str(fehler))


def test_entwurf_anlegen_ruft_me_slash_messages_auf():
    aufgezeichnet = {}

    def fake_graph(methode, pfad, token, koerper=None, typ="application/json"):
        aufgezeichnet["methode"] = methode
        aufgezeichnet["pfad"] = pfad
        return {"id": "MSG-123"}

    orig = gd._graph
    gd._graph = fake_graph
    try:
        kennung = gd.entwurf_anlegen("tok", b"Test-MIME")
    finally:
        gd._graph = orig

    check("entwurf_anlegen ruft POST /me/messages auf (nie /users/{postfach})",
          aufgezeichnet.get("methode") == "POST"
          and aufgezeichnet.get("pfad") == "/me/messages",
          str(aufgezeichnet))
    check("entwurf_anlegen gibt die Nachrichten-Kennung zurueck",
          kennung == "MSG-123")


# --------------------------------------------------------------------------
# main(): --pruefen soll ein reiner Verbindungstest sein koennen, auch ohne
# bereits vorhandene Entwuerfe.
# --------------------------------------------------------------------------

def test_pruefen_ohne_vorhandene_entwuerfe_aber_mit_postfach_funktioniert(tmp_path):
    orig_argv = sys.argv
    orig_token = gd.token_holen
    orig_ident = gd.identitaet_pruefen
    aufrufe = {"identitaet": 0}
    gd.token_holen = lambda: "TOK-TEST"
    gd.identitaet_pruefen = lambda token, postfach: aufrufe.__setitem__(
        "identitaet", aufrufe["identitaet"] + 1)
    sys.argv = [
        "graph_drafts.py", "--batch", "HSB-LEER-0001",
        "--ordner", str(tmp_path), "--postfach", "j-post@hsb-boden.de",
        "--pruefen",
    ]
    try:
        rc = gd.main()
    finally:
        sys.argv = orig_argv
        gd.token_holen = orig_token
        gd.identitaet_pruefen = orig_ident

    check("--pruefen mit --postfach funktioniert ohne vorhandene "
          "EML-Dateien (reiner Anmelde-Probelauf)", rc == 0, f"rc={rc}")
    check("--pruefen prueft die Identitaet trotzdem wirklich "
          "(kein Blindflug)", aufrufe["identitaet"] == 1, str(aufrufe))


def test_ohne_pruefen_und_ohne_dateien_bricht_weiterhin_fail_closed_ab(tmp_path):
    orig_argv = sys.argv
    sys.argv = [
        "graph_drafts.py", "--batch", "HSB-LEER-0002",
        "--ordner", str(tmp_path), "--postfach", "j-post@hsb-boden.de",
    ]
    fehler = None
    try:
        gd.main()
    except SystemExit as e:
        fehler = str(e)
    finally:
        sys.argv = orig_argv

    check("Ohne --pruefen bricht ein Lauf ohne vorhandene Entwuerfe "
          "weiterhin ab (keine leere Ausfuehrung, kein Missverstaendnis)",
          fehler is not None and "ABBRUCH" in fehler, str(fehler))



def test_direkte_graph_rest_draft_erstellung_unter_350ms_fuer_beide_postfaecher():
    import time
    orig = gd._graph
    for postfach, owner in [("j-post@hsb-boden.de", "JORDI"), ("j-cherino@hsb-boden.de", "JOEL")]:
        def fake_graph(methode, pfad, token, koerper=None, typ="text/plain"):
            return {"id": f"DRAFT-{owner}-123", "internetMessageId": f"<{owner}-123@hsb-boden.de>"}
        gd._graph = fake_graph
        try:
            start = time.perf_counter()
            kennung = gd.entwurf_anlegen("tok", b"From: " + postfach.encode() + b"\r\nTo: test@kunde.de\r\n\r\nTest")
            elapsed_ms = (time.perf_counter() - start) * 1000
            check(f"Graph REST Draft < 350ms ({owner}: {postfach})", elapsed_ms < 350, f"{elapsed_ms:.2f}ms")
            check(f"Draft-ID generiert ({owner})", kennung == f"DRAFT-{owner}-123")
        finally:
            gd._graph = orig

if __name__ == "__main__":
    import tempfile

    for fn in [
        test_ohne_cache_wird_geraetecode_angemeldung_verwendet,
        test_gueltiges_refresh_token_umgeht_geraetecode_anmeldung,
        test_ungueltiges_refresh_token_faellt_zurueck_auf_geraetecode,
        test_kein_client_secret_mehr_noetig,
    ]:
        print(f"\n--- {fn.__name__} ---")
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(Path(td))
            except Exception as exc:  # noqa: BLE001
                check(f"{fn.__name__} ohne Ausnahme", False, repr(exc))

    for fn in [
        test_pruefen_ohne_vorhandene_entwuerfe_aber_mit_postfach_funktioniert,
        test_ohne_pruefen_und_ohne_dateien_bricht_weiterhin_fail_closed_ab,
    ]:
        print(f"\n--- {fn.__name__} ---")
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(Path(td))
            except Exception as exc:  # noqa: BLE001
                check(f"{fn.__name__} ohne Ausnahme", False, repr(exc))

    for fn in [
        test_geraetecode_polling_wartet_bei_authorization_pending_und_erfolgt_dann,
        test_geraetecode_polling_bricht_bei_ablehnung_fail_closed_ab,
        test_identitaet_pruefen_akzeptiert_passendes_postfach,
        test_identitaet_pruefen_lehnt_falsches_postfach_fail_closed_ab,
        test_entwurf_anlegen_ruft_me_slash_messages_auf,
        test_direkte_graph_rest_draft_erstellung_unter_350ms_fuer_beide_postfaecher,
    ]:
        print(f"\n--- {fn.__name__} ---")
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            check(f"{fn.__name__} ohne Ausnahme", False, repr(exc))

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    print("\n" + "=" * 70)
    print(f"ERGEBNIS: {passed} bestanden, {failed} fehlgeschlagen von {len(RESULTS)}")
    print("REAL_EXTERNAL_SEND_COUNT=0")
    print("=" * 70)
    if failed:
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"  FAIL: {name} {detail}")
    sys.exit(1 if failed else 0)
