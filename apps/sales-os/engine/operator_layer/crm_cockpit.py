#!/usr/bin/env python3
"""Baut die Cockpit-Tabs HEUTE JOEL / HEUTE JORDI: fuenf QUERY-Bloecke, Farben, Zaehler, Sync-Anker."""
import sys
from crm_common import services, SID
from crm_operator_layer import PIPELINE_COLORS, rgb

BLOCK_COLS = "B, G, I, BE, AP, AR, AC"   # Firma, Ansprechpartner, E-Mail, Pipeline, Send_Datum, Reply_Status, Notizen
HEADER_LABELS = ["Firma", "Ansprechpartner", "E-Mail", "Pipeline", "Versendet am", "Antwort", "Notizen"]

# Zeilen, die jeder HEUTE-Block reserviert (Titel + Kopf + Formel + Leerzeilen). Der QUERY-`limit`
# jedes Blocks MUSS <= BLOCK_ROWS bleiben, sonst kollidiert die Array-Erweiterung mit der Titelzeile
# des naechsten Blocks (#REF!, Critical 3).
BLOCK_ROWS = 40

def q(where, order="", limit=None):
    return f"=IFERROR(QUERY(ALL_LEADS!A2:BE; \"select {BLOCK_COLS} where {where}{(' order by ' + order) if order else ''}{(' limit ' + str(limit)) if limit else ''}\"; 0); \"— keine —\")"

def cockpit_blocks(owner_match):
    own = f"AA contains '{owner_match}'"
    return [
        {"title": "🔴 Abgemeldet",  "color": PIPELINE_COLORS["Abgemeldet"],  "formula": q(f"{own} and BE = 'Abgemeldet'", "BC desc", limit=BLOCK_ROWS)},
        {"title": "🟡 Antworten offen", "color": PIPELINE_COLORS["Antwort"], "formula": q(f"{own} and BE = 'Antwort' and R is null", "BC desc", limit=BLOCK_ROWS)},
        {"title": "🟠 Bounce", "color": PIPELINE_COLORS["Bounce"], "formula": q(f"{own} and BE = 'Bounce'", "AP desc", limit=BLOCK_ROWS)},
        # AP (Send_Datum) mischt Text- und Datumswerte im Live-Sheet (162 Text / 201 Datum) — ein Datumsvergleich
        # wuerde die Text-Zeilen still ausblenden. Daher kein `AP >= date '…'`, sondern reiner Status-Filter mit
        # den juengsten BLOCK_ROWS nach AP sortiert; der Zaehler unten (count_formula) prueft dieselbe Bedingung.
        {"title": f"🟢 Versendet (zuletzt {BLOCK_ROWS})", "color": PIPELINE_COLORS["Versendet"], "formula": q(f"{own} and BE = 'Versendet'", "AP desc", limit=BLOCK_ROWS)},
        {"title": "🔵 Heute dran (freigegeben / Entwurf)", "color": PIPELINE_COLORS["Freigegeben"], "formula": q(f"{own} and (BE = 'Freigegeben' or BE = 'Entwurf')", "F, B", limit=BLOCK_ROWS)},
    ]

def count_formula(owner_match, state):
    return f'=COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "{state}")'

def cockpit_values(owner_match, mailbox):
    """Zellinhalte des Tabs (Zeilenlisten). Jeder Block: Titelzeile (mit Zaehler), Kopfzeile, QUERY, BLOCK_ROWS Zeilen Platz."""
    rows = [[f"HEUTE — {owner_match.upper()}", "", "", "", "", "", ""],
            [f'=IFERROR("Postfach " & VLOOKUP("{mailbox}"; SYNC_STATUS!A:H; 1; FALSE) & " · zuletzt abgeglichen " & TEXT(VLOOKUP("{mailbox}"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm"); "Abgleich noch nicht gelaufen")'],
            []]
    # Zaehler = exakt dieselbe Bedingung wie die Liste darunter (sonst widersprechen sich Kopf und Inhalt).
    counts = [
        count_formula(owner_match, "Abgemeldet"),
        f'=COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")',
        count_formula(owner_match, "Bounce"),
        count_formula(owner_match, "Versendet"),
        f'=COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "Entwurf")',
    ]
    for blk, cnt in zip(cockpit_blocks(owner_match), counts):
        rows.append([blk["title"], cnt]); rows.append(HEADER_LABELS); rows.append([blk["formula"]])
        rows.extend([[]] * BLOCK_ROWS)
    return rows

def build_cockpit_requests(sheet_id, owner_match, mailbox):
    """Formatierung: Titelzeilen farbig, Kopfzeilen fett, Spaltenbreiten, Zeile 1 fixiert, CLIP."""
    reqs = [{"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            {"repeatCell": {"range": {"sheetId": sheet_id}, "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat.wrapStrategy"}}]
    widths = [220, 180, 220, 110, 110, 110, 300]
    for i, w in enumerate(widths):
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})
    r = 3
    for blk in cockpit_blocks(owner_match):
        bg, fg = blk["color"]
        reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                     "cell": {"userEnteredFormat": {"backgroundColor": rgb(bg), "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": rgb(fg)}}},
                     "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
        reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": r + 1, "endRowIndex": r + 2, "startColumnIndex": 0, "endColumnIndex": 7},
                     "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": rgb("F8F9FA")}}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}})
        r += BLOCK_ROWS + 3
    return reqs

EV_COLS = "B, H, G, D, E, J, K"   # Zeit, Typ, Lead-ID, Absender, Betreff, Status, Notiz
EV_LABELS = ["Zeit (UTC)", "Typ", "Lead-ID", "Absender", "Betreff", "Status", "Notiz"]

# Reservierte Zeilen fuer den Klaerfall-Block (149 Klaerfaelle live nach Migration, Critical 3).
KLAER_ROWS = 200
# Gesamtgroesse des POSTEINGANG-Tabs: Klaerfall-Block + Ereignisliste (limit 200) muessen
# hineinpassen, sonst laeuft die Ereignisliste ihrerseits in die letzte Zeile.
POSTEINGANG_ROW_COUNT = 450

# Zeilenindizes (0-basiert, wie in posteingang_values()) — von build_posteingang_requests()
# zum Positionieren der Formatierung wiederverwendet, damit Werte und Formate nicht auseinanderlaufen.
_EV_ROW_TITLE = 0
_EV_ROW_KLAER_TITLE = 3
_EV_ROW_KLAER_LABELS = 4
_EV_ROW_KLAER_DATA = 5
_EV_ROW_EVENTS_TITLE = _EV_ROW_KLAER_DATA + 1 + KLAER_ROWS  # KLAER_ROWS Leerzeilen fuer Klaerfaelle-Ergebnisse
_EV_ROW_EVENTS_LABELS = _EV_ROW_EVENTS_TITLE + 1
_EV_ROW_EVENTS_DATA = _EV_ROW_EVENTS_TITLE + 2

def posteingang_values():
    """Zellinhalte des Tabs POSTEINGANG: Klaerfaelle (NEEDS_REVIEW) oben, Ereignisliste darunter."""
    rows = [["POSTEINGANG — beide Postfächer", "", "", "", "", "", ""],
            ['=IFERROR("Joel zuletzt " & TEXT(VLOOKUP("j-cherino@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm") & " · Jordi zuletzt " & TEXT(VLOOKUP("j-post@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm"); "Abgleich noch nicht gelaufen")'],
            [],
            ["⚠️ Klärfälle — bitte in INBOUND_EVENTS Spalte M eine Lead-ID oder „ignorieren“ eintragen", "=COUNTIF(INBOUND_EVENTS!J2:J; \"NEEDS_REVIEW\")"],
            EV_LABELS,
            [f"=IFERROR(QUERY(INBOUND_EVENTS!A2:M; \"select {EV_COLS} where J = 'NEEDS_REVIEW' order by B desc limit {KLAER_ROWS}\"; 0); \"— keine —\")"]]
    rows.extend([[]] * KLAER_ROWS)
    rows += [["📥 Letzte 200 Ereignisse", ""], EV_LABELS,
             [f"=IFERROR(QUERY(INBOUND_EVENTS!A2:M; \"select {EV_COLS} where A is not null and J <> 'DUPLICATE' order by B desc limit 200\"; 0); \"— keine —\")"]]
    return rows

# Klassifikation -> Pipeline-Farbe (Task-5-Ruling): dieselben Farben wie ALL_LEADS, damit
# ein Bounce/Opt-Out/Antwort im Posteingang genauso aussieht wie in der Leadliste.
_CLASSIFICATION_COLORS = [
    (("OPT_OUT",), "Abgemeldet"),
    (("HARD_BOUNCE", "SOFT_BOUNCE"), "Bounce"),
    (("REPLY", "POSITIVE_REPLY"), "Antwort"),
    (("SENT",), "Versendet"),
]

def build_posteingang_requests(sheet_id, existing_cf_count=0):
    """Formatierung: Titelzeilen farbig, Kopfzeilen fett, Spaltenbreiten, Zeile 1 fixiert, CLIP,
    bedingte Formatierung auf Spalte B (Typ) nach Klassifikation fuer beide Bloecke.

    `existing_cf_count` bestehende bedingte Formate des Tabs werden zuerst absteigend geloescht
    (wie crm_operator_layer.py), bevor die vier neuen Regeln angefuegt werden — sonst akkumulieren
    sie bei jedem Lauf (Important 7)."""
    reqs = [{"deleteConditionalFormatRule": {"sheetId": sheet_id, "index": i}}
            for i in range(existing_cf_count - 1, -1, -1)]
    reqs += [{"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            {"repeatCell": {"range": {"sheetId": sheet_id}, "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat.wrapStrategy"}}]
    widths = [140, 130, 120, 220, 260, 110, 260]
    for i, w in enumerate(widths):
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    bg, fg = PIPELINE_COLORS["Abgemeldet"]
    reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": _EV_ROW_KLAER_TITLE, "endRowIndex": _EV_ROW_KLAER_TITLE + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                 "cell": {"userEnteredFormat": {"backgroundColor": rgb(bg), "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": rgb(fg)}}},
                 "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
    reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": _EV_ROW_KLAER_LABELS, "endRowIndex": _EV_ROW_KLAER_LABELS + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                 "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": rgb("F8F9FA")}}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}})
    reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": _EV_ROW_EVENTS_TITLE, "endRowIndex": _EV_ROW_EVENTS_TITLE + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                 "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 12}, "backgroundColor": rgb("F8F9FA")}}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}})
    reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": _EV_ROW_EVENTS_LABELS, "endRowIndex": _EV_ROW_EVENTS_LABELS + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                 "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": rgb("F8F9FA")}}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}})

    # Bedingte Formatierung auf Spalte B (Typ) — ueber beide Bloecke (Klaerfaelle- und Ereignisliste-Ergebnisse).
    anchor = _EV_ROW_KLAER_DATA + 1  # 1-basierte Zeile der ersten Datenzeile, fuer relative Formel-Referenz
    idx = 0
    for values, state in _CLASSIFICATION_COLORS:
        cbg, cfg = PIPELINE_COLORS[state]
        conds = [f'$B{anchor}="{v}"' for v in values]
        formula = conds[0] if len(conds) == 1 else "OR(" + ",".join(conds) + ")"
        reqs.append({"addConditionalFormatRule": {"index": idx, "rule": {
            "ranges": [{"sheetId": sheet_id, "startRowIndex": _EV_ROW_KLAER_DATA, "endRowIndex": POSTEINGANG_ROW_COUNT,
                        "startColumnIndex": 0, "endColumnIndex": 7}],
            "booleanRule": {"condition": {"type": "CUSTOM_FORMULA",
                                          "values": [{"userEnteredValue": f"={formula}"}]},
                            "format": {"backgroundColor": rgb(cbg), "textFormat": {"foregroundColor": rgb(cfg)}}}}}})
        idx += 1
    return reqs

def posteingang_setup_requests(events_sheet_id):
    """Spalte M `Zuordnung` in INBOUND_EVENTS: Datenvalidierung M2:M — nicht strikt (Freitext bleibt
    erlaubt: Lead-ID), mit `ignorieren` als Dropdown-Vorschlag. `endRowIndex` bewusst weggelassen
    (unbounded) statt einer festen Zeilenobergrenze — sonst schlaegt die Validierung fehl, sobald
    das Blatt anders dimensioniert ist als beim Schreiben dieser Zeile (Critical 2c)."""
    reqs = [{"setDataValidation": {"range": {"sheetId": events_sheet_id, "startRowIndex": 1,
                                              "startColumnIndex": 12, "endColumnIndex": 13},
             "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "ignorieren"}]},
                      "strict": False, "showCustomUi": True}}}]
    return reqs

TABS = {"HEUTE JOEL": ("Joel", "j-cherino@hsb-boden.de"), "HEUTE JORDI": ("Jordi", "j-post@hsb-boden.de")}

# Feste Tab-Reihenfolge und Sichtbarkeit (Controller-Ruling Step 5). Alles nicht Gelistete wird versteckt,
# einschliesslich SYNC_STATUS, das rein als Datenquelle fuer den Sync-Anker dient. INBOUND_EVENTS
# bleibt sichtbar (direkt nach POSTEINGANG), weil der Klaerfall-Workflow verlangt, dass der Operator
# dort in Spalte M eine Lead-ID oder "ignorieren" eintraegt (Important 5).
TAB_ORDER = ["README", "HEUTE JOEL", "HEUTE JORDI", "POSTEINGANG", "INBOUND_EVENTS", "ALL_LEADS", "DASHBOARD", "VERSAND", "BATCHES"]

def order_tabs(sh, apply=False):
    """Setzt Index/Sichtbarkeit aller vorhandenen Tabs gemaess TAB_ORDER; alles andere wird hidden.
    Im Dry-Run wird nur gelesen und der Plan gedruckt, es findet kein batchUpdate statt."""
    meta = sh.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,title,hidden))").execute()
    existing = {s["properties"]["title"]: s["properties"] for s in meta["sheets"]}
    reqs = []
    plan = []
    visible_order = [t for t in TAB_ORDER if t in existing]
    for idx, title in enumerate(visible_order):
        props = existing[title]
        reqs.append({"updateSheetProperties": {"properties": {"sheetId": props["sheetId"], "index": idx, "hidden": False}, "fields": "index,hidden"}})
        plan.append(f"  {title}: index={idx}, hidden=False")
    for title, props in existing.items():
        if title in visible_order:
            continue
        reqs.append({"updateSheetProperties": {"properties": {"sheetId": props["sheetId"], "hidden": True}, "fields": "hidden"}})
        plan.append(f"  {title}: hidden=True")
    print(f"[{'APPLY' if apply else 'DRY-RUN'}] order_tabs geplante Aenderungen:")
    for line in plan:
        print(line)
    if apply and reqs:
        sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": reqs}).execute()
    return reqs

# Sechs Zeilen fuer README!A15:B20 — Spalte A Label, Spalte B Erklaerung (Controller-Ruling Task 7a).
README_SCHNELLSTART = [
    ["1. Dein Tab öffnen", "HEUTE JOEL bzw. HEUTE JORDI – alles Wichtige auf einer Seite, oben steht, wann dein Postfach zuletzt abgeglichen wurde."],
    ["2. Rot = Abgemeldet", "Diese Firmen werden nie wieder angeschrieben. Automatisch gesperrt (auch bei \"Abmelden\" von einer Kollegenadresse derselben Firma)."],
    ["3. Gelb = Antwort offen", "Antworten, zu denen noch kein Follow-up-Datum (Spalte R in ALL_LEADS) steht."],
    ["4. Grün = Versendet", "Kommt automatisch aus deinem Ordner \"Gesendete Elemente\" (alle 15 Minuten). Nichts bestätigen."],
    ["5. Unklare Fälle", "Tab POSTEINGANG, Block \"Klärfälle\": in INBOUND_EVENTS Spalte M eine Lead-ID oder \"ignorieren\" eintragen, dann Menü HSB Sales OS → Klärfälle anwenden."],
    ["6. Neue Entwürfe", "Seitenleiste öffnen (Menü HSB Sales OS → Seitenleiste öffnen), wie bisher."],
]

def readme_values():
    """Sechs Zeilen fuer README!A15:B20."""
    return [list(r) for r in README_SCHNELLSTART]

def readme_table_rows():
    """Drei Zeilen fuer die TABELLEN-UEBERSICHT, nach der DASHBOARD-Zeile einzufuegen."""
    return [
        ["HEUTE JOEL", "Deine Tagesansicht: Abgemeldet · Antworten offen · Bounce · Versendet · Heute dran — nur deine Leads."],
        ["HEUTE JORDI", "Dieselbe Tagesansicht für Jordi."],
        ["POSTEINGANG", "Alle Ereignisse beider Postfächer, Klärfälle oben — mit Spalte M in INBOUND_EVENTS lösbar."],
    ]

def write_readme(sh, apply=False):
    """Schreibt README!A15:B20 (Schnellstart) und ergaenzt die TABELLEN-UEBERSICHT um die drei
    Cockpit-Tabs direkt nach der DASHBOARD-Zeile. Idempotent: ueberspringt das Einfuegen, wenn
    HEUTE JOEL in README!A21:A40 bereits steht. Im Dry-Run wird nur gedruckt, nicht geschrieben."""
    rows = readme_values()
    table_rows = readme_table_rows()
    if not apply:
        print("[DRY-RUN] README!A15:B20 (Schnellstart):")
        for r in rows:
            print(f"  {r}")
        print("[DRY-RUN] TABELLEN-UEBERSICHT-Ergaenzung nach DASHBOARD:")
        for r in table_rows:
            print(f"  {r}")
        return

    meta = sh.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,title))").execute()
    readme_sid = next(s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == "README")

    sh.spreadsheets().values().update(spreadsheetId=SID, range="README!A15:B20", valueInputOption="RAW", body={"values": rows}).execute()

    existing = sh.spreadsheets().values().get(spreadsheetId=SID, range="README!A21:A40").execute().get("values", [])
    flat = [v[0] if v else "" for v in existing]
    if "HEUTE JOEL" in flat:
        print("README: TABELLEN-UEBERSICHT enthaelt HEUTE JOEL bereits, ueberspringe Einfuegen.")
        return
    dashboard_idx = next((i for i, v in enumerate(flat) if v == "DASHBOARD"), None)
    if dashboard_idx is None:
        print("README: DASHBOARD-Zeile in A21:A40 nicht gefunden, ueberspringe Einfuegen.")
        return
    dashboard_row0 = 20 + dashboard_idx  # 0-basierter Grid-Index (Zeile 21 = Index 20)
    sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [
        {"insertDimension": {"range": {"sheetId": readme_sid, "dimension": "ROWS",
                                        "startIndex": dashboard_row0 + 1, "endIndex": dashboard_row0 + 4}}}
    ]}).execute()
    insert_row = dashboard_row0 + 2  # 1-basierte erste neue Zeile (direkt nach DASHBOARD)
    sh.spreadsheets().values().update(spreadsheetId=SID, range=f"README!A{insert_row}:B{insert_row + 2}",
                                       valueInputOption="RAW", body={"values": table_rows}).execute()
    print("README: Schnellstart und TABELLEN-UEBERSICHT aktualisiert.")

def ensure_tab(sh, title, index, row_count=260):
    meta = sh.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,title,gridProperties(rowCount)))").execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == title:
            sid = s["properties"]["sheetId"]
            # Bestehender Tab: Zeilenzahl nachziehen, sonst laufen clear/Formate ueber das Grid.
            have = (s["properties"].get("gridProperties") or {}).get("rowCount", 0)
            if have < row_count:
                sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [{"updateSheetProperties": {
                    "properties": {"sheetId": sid, "gridProperties": {"rowCount": row_count}}, "fields": "gridProperties.rowCount"}}]}).execute()
            return sid
    res = sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [{"addSheet": {"properties": {"title": title, "index": index, "gridProperties": {"rowCount": row_count, "columnCount": 8}}}}]}).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]

def main(apply=False):
    sh, _ = services("cherinodiaz" if apply else "cherinojoel")
    for idx, (title, (owner, mailbox)) in enumerate(TABS.items(), start=1):
        vals = cockpit_values(owner, mailbox)
        if not apply:
            print(f"[DRY-RUN] {title}: {len(vals)} Zeilen, {len(build_cockpit_requests(0, owner, mailbox))} Format-Requests"); continue
        sid = ensure_tab(sh, title, idx)
        sh.spreadsheets().values().clear(spreadsheetId=SID, range=f"'{title}'!A1:H260").execute()
        sh.spreadsheets().values().update(spreadsheetId=SID, range=f"'{title}'!A1", valueInputOption="USER_ENTERED", body={"values": vals}).execute()
        sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": build_cockpit_requests(sid, owner, mailbox)}).execute()
        print(f"{title}: geschrieben (sheetId {sid})")

    # Ein Lese-Call fuer beide Vorbedingungen: bestehende bedingte Formate von POSTEINGANG (I7) und
    # die aktuelle Spaltenzahl von INBOUND_EVENTS (C2a) — read-only, auch im Dry-Run erlaubt.
    meta = sh.spreadsheets().get(
        spreadsheetId=SID,
        fields="sheets(properties(sheetId,title,gridProperties(columnCount)),conditionalFormats)"
    ).execute()
    by_title = {s["properties"]["title"]: s for s in meta["sheets"]}
    posteingang_sheet = by_title.get("POSTEINGANG")
    existing_cf_count = len(posteingang_sheet.get("conditionalFormats", [])) if posteingang_sheet else 0

    ev_vals = posteingang_values()
    if not apply:
        print(f"[DRY-RUN] POSTEINGANG: {len(ev_vals)} Zeilen, "
              f"{len(build_posteingang_requests(0, existing_cf_count))} Format-Requests "
              f"({existing_cf_count} bestehende bedingte Formate wuerden zuerst geloescht)")
    else:
        pid = ensure_tab(sh, "POSTEINGANG", 3, row_count=POSTEINGANG_ROW_COUNT)
        sh.spreadsheets().values().clear(spreadsheetId=SID, range=f"'POSTEINGANG'!A1:H{POSTEINGANG_ROW_COUNT}").execute()
        sh.spreadsheets().values().update(spreadsheetId=SID, range="'POSTEINGANG'!A1", valueInputOption="USER_ENTERED", body={"values": ev_vals}).execute()
        sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": build_posteingang_requests(pid, existing_cf_count)}).execute()
        print(f"POSTEINGANG: geschrieben (sheetId {pid})")

    # Spalte M (`Zuordnung`) in INBOUND_EVENTS anlegen, falls das Live-Grid noch bei 12 Spalten steht
    # (Critical 2a) — sonst schlaegt der anschliessende M1-Write/die Validierung fehl.
    ev_sheet = by_title.get("INBOUND_EVENTS")
    if ev_sheet:
        ev_sid = ev_sheet["properties"]["sheetId"]
        col_count = ev_sheet["properties"]["gridProperties"]["columnCount"]
        if col_count < 13:
            if apply:
                sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [
                    {"appendDimension": {"sheetId": ev_sid, "dimension": "COLUMNS", "length": 13 - col_count}}
                ]}).execute()
                print(f"INBOUND_EVENTS: Spalte M angelegt ({col_count} -> 13 Spalten).")
            else:
                print(f"[DRY-RUN] INBOUND_EVENTS hat {col_count} Spalten, Spalte M wuerde angelegt (+{13 - col_count}).")
        elif not apply:
            print(f"[DRY-RUN] INBOUND_EVENTS hat bereits {col_count} Spalten, Spalte M vorhanden.")
        if apply:
            m1 = sh.spreadsheets().values().get(spreadsheetId=SID, range="INBOUND_EVENTS!M1").execute().get("values", [[""]])
            if not (m1 and m1[0] and str(m1[0][0]).strip()):
                sh.spreadsheets().values().update(spreadsheetId=SID, range="INBOUND_EVENTS!M1", valueInputOption="USER_ENTERED", body={"values": [["Zuordnung"]]}).execute()
            sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": posteingang_setup_requests(ev_sid)}).execute()

    write_readme(sh, apply=apply)
    order_tabs(sh, apply=apply)
    return 0

if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
