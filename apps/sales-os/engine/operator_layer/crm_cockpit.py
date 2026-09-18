#!/usr/bin/env python3
"""Baut die Cockpit-Tabs HEUTE JOEL / HEUTE JORDI: fuenf QUERY-Bloecke, Farben, Zaehler, Sync-Anker."""
import sys, datetime
from crm_common import services, SID, col
from crm_operator_layer import PIPELINE_COLORS, rgb

BLOCK_COLS = "B, G, I, BE, AP, AR, AC"   # Firma, Ansprechpartner, E-Mail, Pipeline, Send_Datum, Reply_Status, Notizen
HEADER_LABELS = ["Firma", "Ansprechpartner", "E-Mail", "Pipeline", "Versendet am", "Antwort", "Notizen"]

def q(where, order="", limit=None):
    return f"=IFERROR(QUERY(ALL_LEADS!A2:BE; \"select {BLOCK_COLS} where {where}{(' order by ' + order) if order else ''}{(' limit ' + str(limit)) if limit else ''}\"; 0); \"— keine —\")"

def cockpit_blocks(owner_match):
    own = f"AA contains '{owner_match}'"
    return [
        {"title": "🔴 Abgemeldet",  "color": PIPELINE_COLORS["Abgemeldet"],  "formula": q(f"{own} and BE = 'Abgemeldet'", "BC desc")},
        {"title": "🟡 Antworten offen", "color": PIPELINE_COLORS["Antwort"], "formula": q(f"{own} and BE = 'Antwort' and R is null", "BC desc")},
        {"title": "🟠 Bounce", "color": PIPELINE_COLORS["Bounce"], "formula": q(f"{own} and BE = 'Bounce'", "AP desc")},
        # AP (Send_Datum) mischt Text- und Datumswerte im Live-Sheet (162 Text / 201 Datum) — ein Datumsvergleich
        # wuerde die Text-Zeilen still ausblenden. Daher kein `AP >= date '…'`, sondern reiner Status-Filter mit
        # den juengsten 60 nach AP sortiert; der Zaehler unten (count_formula) prueft dieselbe Bedingung.
        {"title": "🟢 Versendet (zuletzt 60)", "color": PIPELINE_COLORS["Versendet"], "formula": q(f"{own} and BE = 'Versendet'", "AP desc", limit=60)},
        {"title": "🔵 Heute dran (freigegeben / Entwurf)", "color": PIPELINE_COLORS["Freigegeben"], "formula": q(f"{own} and (BE = 'Freigegeben' or BE = 'Entwurf')", "F, B")},
    ]

def count_formula(owner_match, state):
    return f'=COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "{state}")'

def cockpit_values(owner_match, mailbox):
    """Zellinhalte des Tabs (Zeilenlisten). Jeder Block: Titelzeile (mit Zaehler), Kopfzeile, QUERY, 40 Zeilen Platz."""
    rows = [[f"HEUTE — {owner_match.upper()}", "", "", "", "", "", ""],
            [f'=IFERROR("Postfach " & VLOOKUP("{mailbox}"; SYNC_STATUS!A:H; 1; FALSE) & " · zuletzt abgeglichen " & TEXT(VLOOKUP("{mailbox}"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm") & " UTC"; "Abgleich noch nicht gelaufen")'],
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
        rows.extend([[]] * 40)
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
        r += 43
    return reqs

TABS = {"HEUTE JOEL": ("Joel", "j-cherino@hsb-boden.de"), "HEUTE JORDI": ("Jordi", "j-post@hsb-boden.de")}

# Feste Tab-Reihenfolge und Sichtbarkeit (Controller-Ruling Step 5). Alles nicht Gelistete wird versteckt,
# einschliesslich SYNC_STATUS, das rein als Datenquelle fuer den Sync-Anker dient.
TAB_ORDER = ["README", "HEUTE JOEL", "HEUTE JORDI", "POSTEINGANG", "ALL_LEADS", "DASHBOARD", "VERSAND", "BATCHES"]

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

def ensure_tab(sh, title, index):
    meta = sh.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,title))").execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == title: return s["properties"]["sheetId"]
    res = sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [{"addSheet": {"properties": {"title": title, "index": index, "gridProperties": {"rowCount": 260, "columnCount": 8}}}}]}).execute()
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
    order_tabs(sh, apply=apply)
    return 0

if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
