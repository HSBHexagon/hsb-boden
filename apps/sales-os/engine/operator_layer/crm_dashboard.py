#!/usr/bin/env python3
"""Ersetzt den Kennzahlenblock des DASHBOARD (Opt-out/Bounce/Klaerfall-Zahlen, 30-Tage-Trend,
Abgleich-Anker) und haengt den Batch-Block (ERZEUGTE BATCHES) unmittelbar darunter wieder an,
statt ihn zu ueberschreiben. Idempotent."""
import sys
from crm_common import services, SID
from crm_operator_layer import rgb

DASHBOARD_TITLE = "DASHBOARD"


def per_owner(f_all, f_owner):
    return [f_all, f_owner.format(o="Jordi"), f_owner.format(o="Joel")]


def dashboard_rows():
    """A1:E27 des DASHBOARD-Tabs.

    Zeilen 1-14 = KPI-Block exakt in Brief-Reihenfolge, 15 leer, 16-17 Batch-Ueberschrift/-Kopf,
    18-27 = 10 Batch-Zeilen (Formeln auf BATCHES!). Zeile 7 = Abgemeldet, Zeile 8 = Bounces,
    Zeile 10 = Klaerfaelle offen, Zeile 16 = Batch-Ueberschrift, Zeile 17 = Batch-Kopf. Die
    Formatierung in formatting_requests() ermittelt diese Zeilennummern per Label-Lookup aus
    dieser Liste, statt sie erneut hart zu kodieren — damit beide nicht wieder auseinanderlaufen.
    """
    R = lambda label, f_all, f_owner, ziel: [label] + per_owner(f_all, f_owner) + [ziel]
    rows = [
        ["HSB SALES OS · VERTRIEBS-COCKPIT"],  # 1
        [],  # 2
        ["Kennzahl", "Gesamt", "Jordi Post", "Joel Cherino Diaz", "Bedeutung"],  # 3
        R("Kontakte gesamt", '=COUNTA(ALL_LEADS!A2:A)', '=COUNTIF(ALL_LEADS!AA2:AA; "*{o}*")', "Datenbank"),  # 4
        R("Versendet", '=COUNTIF(ALL_LEADS!AO2:AO; "sent")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!AO2:AO; "sent")', "automatisch aus Gesendete Elemente"),  # 5
        R("Antworten offen", '=COUNTIFS(ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")', "ohne Follow-up-Datum"),  # 6
        R("Abgemeldet (Opt-out)", '=COUNTIF(ALL_LEADS!Y2:Y; "yes")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!Y2:Y; "yes")', "dauerhaft gesperrt"),  # 7
        R("Bounces", '=COUNTIF(ALL_LEADS!BE2:BE; "Bounce")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Bounce")', "unzustellbar"),  # 8
        R("Freigegeben, noch nicht versendet", '=COUNTIF(ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIF(ALL_LEADS!BE2:BE; "Entwurf")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Entwurf")', "naechste Sendungen"),  # 9
        ["Klärfälle offen", '=COUNTIF(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW")',
         '=COUNTIFS(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW"; INBOUND_EVENTS!C2:C; "j-post@hsb-boden.de")',
         '=COUNTIFS(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW"; INBOUND_EVENTS!C2:C; "j-cherino@hsb-boden.de")', "im Tab POSTEINGANG loesen"],  # 10
        [],  # 11
        ["Versendet letzte 30 Tage", '=SPARKLINE(MAP(SEQUENCE(30; 1; TODAY()-29; 1); LAMBDA(t; COUNTIF(ALL_LEADS!AP2:AP; TEXT(t; "yyyy-mm-dd") & "*"))); {"charttype"\\"column"})', "", "", "Tage links = älter"],  # 12
        ["Letzter Abgleich Joel", '=IFERROR(TEXT(VLOOKUP("j-cherino@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm.yyyy hh:mm") & " UTC"; "noch nicht")', "", "", "alle 15 Minuten"],  # 13
        ["Letzter Abgleich Jordi", '=IFERROR(TEXT(VLOOKUP("j-post@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm.yyyy hh:mm") & " UTC"; "noch nicht")', "", "", "alle 15 Minuten"],  # 14
        [],  # 15
        ["ERZEUGTE BATCHES (Letzte 10)"],  # 16
        ["Batch ID", "Owner", "Status", "Anzahl Leads", "Erstellt am"],  # 17
    ]
    # 18-27: 10 Batch-Zeilen, Mapping Dashboard-Spalte -> BATCHES-Spalte: A<-A, B<-B, C<-D, D<-F, E<-K.
    for b in range(1, 11):
        r = b + 1
        rows.append([
            f'=IF(ISBLANK(BATCHES!A{r}); ""; BATCHES!A{r})',
            f'=IF(ISBLANK(BATCHES!B{r}); ""; BATCHES!B{r})',
            f'=IF(ISBLANK(BATCHES!D{r}); ""; BATCHES!D{r})',
            f'=IF(ISBLANK(BATCHES!F{r}); ""; BATCHES!F{r})',
            f'=IF(ISBLANK(BATCHES!K{r}); ""; BATCHES!K{r})',
        ])
    return rows


def _row_of(rows, label):
    """1-basierter Zeilenindex der Zeile, deren erste Zelle == label ist."""
    return next(i + 1 for i, r in enumerate(rows) if r and r[0] == label)


def formatting_requests(sheet_id, rows=None):
    """Ein batchUpdate: Titelzeile (merge), Kopfzeilen, Klaerfall-/Abgemeldet-/Bounce-Faerbung.

    Die Zielzeilen werden per Label aus dashboard_rows() ermittelt statt hart kodiert, damit
    Layout-Aenderungen an dashboard_rows() nicht unbemerkt zu falsch gefaerbten Zeilen fuehren.
    unmergeCells muss vor mergeCells laufen, weil Sheets einen zweiten merge auf eine bereits
    gemergte Range ablehnt (A1:E1 kann schon aus einem frueheren Lauf gemergt sein).
    """
    rows = rows if rows is not None else dashboard_rows()
    row_titel = _row_of(rows, "HSB SALES OS · VERTRIEBS-COCKPIT")
    row_header = _row_of(rows, "Kennzahl")
    row_abgemeldet = _row_of(rows, "Abgemeldet (Opt-out)")
    row_bounces = _row_of(rows, "Bounces")
    row_klaerfaelle = _row_of(rows, "Klärfälle offen")
    row_batch_titel = _row_of(rows, "ERZEUGTE BATCHES (Letzte 10)")
    row_batch_header = _row_of(rows, "Batch ID")

    def row_fmt(row_1based, bg=None, bold=False, size=None, fg=None, cols=5):
        fmt = {}
        if bg:
            fmt["backgroundColor"] = rgb(bg)
        tf = {}
        if bold:
            tf["bold"] = True
        if size:
            tf["fontSize"] = size
        if fg:
            tf["foregroundColor"] = rgb(fg)
        if tf:
            fmt["textFormat"] = tf
        fields = ",".join("userEnteredFormat." + k for k in fmt)
        return {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": row_1based - 1, "endRowIndex": row_1based,
                      "startColumnIndex": 0, "endColumnIndex": cols},
            "cell": {"userEnteredFormat": fmt}, "fields": fields}}

    a1e1 = {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 5}
    return [
        {"unmergeCells": {"range": a1e1}},
        row_fmt(row_titel, bg="0d652d", bold=True, size=16, fg="ffffff"),
        {"mergeCells": {"range": a1e1, "mergeType": "MERGE_ALL"}},
        row_fmt(row_header, bg="e8eaed", bold=True),
        row_fmt(row_abgemeldet, bg="F4C7C3"),
        row_fmt(row_bounces, bg="FCE8B2"),
        row_fmt(row_klaerfaelle, bg="FCE8B2"),
        row_fmt(row_batch_titel, bg="e8eaed", bold=True, size=12),
        row_fmt(row_batch_header, bg="e8eaed", bold=True),
    ]


def main(apply=False):
    sh, _ = services("cherinodiaz" if apply else "cherinojoel")
    rows = dashboard_rows()
    if not apply:
        cur = sh.spreadsheets().values().get(spreadsheetId=SID, range="DASHBOARD!A12:A13").execute().get("values", [])
        print(f"[DRY-RUN] aktuell DASHBOARD!A12:A13 = {cur}")
        print(f"[DRY-RUN] DASHBOARD!A1:E{len(rows)} wuerde {len(rows)} Zeilen erhalten")
        return 0
    sh.spreadsheets().values().update(spreadsheetId=SID, range=f"DASHBOARD!A1:E{len(rows)}",
                                       valueInputOption="USER_ENTERED", body={"values": rows}).execute()
    grid = sh.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,title))").execute()
    sheet_id = next(s["properties"]["sheetId"] for s in grid["sheets"] if s["properties"]["title"] == DASHBOARD_TITLE)
    sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": formatting_requests(sheet_id, rows)}).execute()
    print("DASHBOARD geschrieben.")
    return 0


if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
