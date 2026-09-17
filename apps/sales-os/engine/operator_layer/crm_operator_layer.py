import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from crm_common import services, SID
DRY = "--apply" not in sys.argv
sheets, _ = services("cherinodiaz" if "--apply" in sys.argv else "cherinojoel")
SH = 767806010  # ALL_LEADS
hdr = sheets.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!1:1").execute()["values"][0]
assert len(hdr) in (56, 57), len(hdr)
ix = {h:i for i,h in enumerate(hdr)}
N = 6425
def rng(c0, c1=None, r0=1, r1=N): return {"sheetId":SH,"startRowIndex":r0,"endRowIndex":r1,"startColumnIndex":c0,"endColumnIndex":(c1 if c1 is not None else c0+1)}
def dim(c0,c1): return {"sheetId":SH,"dimension":"COLUMNS","startIndex":c0,"endIndex":c1}
def rgb(h): return {"red":int(h[0:2],16)/255,"green":int(h[2:4],16)/255,"blue":int(h[4:6],16)/255}
req = []
# 0) Spalte BE anhängen (nur wenn noch 56 Spalten)
grid = sheets.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,gridProperties(columnCount)),filterViews(title))").execute()
sh_obj = next(s for s in grid["sheets"] if s["properties"]["sheetId"]==SH)
cols = sh_obj["properties"]["gridProperties"]["columnCount"]
existing_fvs = set(fv.get("title") for fv in sh_obj.get("filterViews", []))

if cols < 57: req.append({"appendDimension":{"sheetId":SH,"dimension":"COLUMNS","length":57-cols}})
PIPE = ix.get("Pipeline", 56)
# 1) CLIP überall
req.append({"repeatCell":{"range":{"sheetId":SH,"startRowIndex":0,"endRowIndex":N,"startColumnIndex":0,"endColumnIndex":57},"cell":{"userEnteredFormat":{"wrapStrategy":"CLIP","verticalAlignment":"MIDDLE"}},"fields":"userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"}})
# 2) Zeilenhöhe Standard 21
req.append({"updateDimensionProperties":{"range":{"sheetId":SH,"dimension":"ROWS","startIndex":1,"endIndex":N},"properties":{"pixelSize":21},"fields":"pixelSize"}})
# 3) Fixieren 1 Zeile / 2 Spalten
req.append({"updateSheetProperties":{"properties":{"sheetId":SH,"gridProperties":{"frozenRowCount":1,"frozenColumnCount":2}},"fields":"gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}})
# 4) Breiten
widths = {"Lead-ID":150,"Firma":220,"Ansprechpartner":180,"E-Mail":220,"Notizen":260,"Versandfreigabe":110,"Opt-out-Status":110,"Opt-in-Status":110,"Verantwortlicher":150,"Legal_Basis":170,"Send_Status":110,"Reply_Status":120,"Bounce_Status":110,"Send_Datum":150,"Follow-up-Datum":130,"Nächste Aktion":130,"Status":90,"Tier":50}
for h,w in widths.items():
    if h in ix:
        req.append({"updateDimensionProperties":{"range":dim(ix[h],ix[h]+1),"properties":{"pixelSize":w},"fields":"pixelSize"}})
req.append({"updateDimensionProperties":{"range":dim(PIPE,PIPE+1),"properties":{"pixelSize":130},"fields":"pixelSize"}})
# 5) Leere Zukunftsfelder S:W ausblenden
if "Interesse" in ix and "Sanierungsfenster" in ix:
    req.append({"updateDimensionProperties":{"range":dim(ix["Interesse"],ix["Sanierungsfenster"]+1),"properties":{"hiddenByUser":True},"fields":"hiddenByUser"}})
# 6) Maschinenspalten AD:BD gruppieren + einklappen
if "Segment" in ix and "Last_Error" in ix:
    g0, g1 = ix["Segment"], ix["Last_Error"]+1
    req.append({"updateDimensionProperties":{"range":dim(g0,g1),"properties":{"hiddenByUser":True},"fields":"hiddenByUser"}})
def ix2(h): return ix[h]
P = PIPE
# 8) Validierungen (nicht strikt, Chips)
def val(h, opts):
    return {"setDataValidation":{"range":{"sheetId":SH,"startRowIndex":1,"endRowIndex":N,"startColumnIndex":ix2(h),"endColumnIndex":ix2(h)+1},"rule":{"condition":{"type":"ONE_OF_LIST","values":[{"userEnteredValue":o} for o in opts]},"showCustomUi":True,"strict":False}}}
req += [val("Versandfreigabe",["yes","no"]), val("Opt-out-Status",["yes","no","unknown"]), val("Opt-in-Status",["yes","no","unknown"]),
        val("Send_Status",["not_sent","prepared","drafted","sent"]), val("Legal_Basis",["UNKNOWN","no","EXISTING_CUSTOMER_7_3","OWNER_APPROVED"]),
        val("Reply_Status",["replied","auto_reply_ooo","bounced","opt_out"])]
# 9) Kopfzeile fett, grau
req.append({"repeatCell":{"range":{"sheetId":SH,"startRowIndex":0,"endRowIndex":1,"startColumnIndex":0,"endColumnIndex":57},"cell":{"userEnteredFormat":{"backgroundColor":rgb("263238"),"textFormat":{"bold":True,"foregroundColor":rgb("ffffff")},"wrapStrategy":"CLIP"}},"fields":"userEnteredFormat(backgroundColor,textFormat,wrapStrategy)"}})
# 10) Filteransichten nur wenn neu
def fv(title, crit):
    return {"addFilterView":{"filter":{"title":title,"range":{"sheetId":SH,"startRowIndex":0,"endRowIndex":N,"startColumnIndex":0,"endColumnIndex":57},"filterSpecs":[{"columnIndex":c,"filterCriteria":fc} for c,fc in crit]}}}
ALL = ["Neu","Freigegeben","Entwurf","Versendet","Antwort","Bounce","Abgemeldet"]
def hide(keep): return {"hiddenValues":[x for x in ALL if x not in keep]}
new_fvs = [
    ("Heute Joel",[(ix2("Verantwortlicher"),{"condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":"Joel Cherino Diaz"}]}}),(P,hide(["Freigegeben","Entwurf","Antwort"]))]),
    ("Heute Jordi",[(ix2("Verantwortlicher"),{"condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":"Jordi Post"}]}}),(P,hide(["Freigegeben","Entwurf","Antwort"]))]),
    ("Antworten offen",[(P,hide(["Antwort"]))]),
    ("Gesperrt",[(P,hide(["Abgemeldet","Bounce"]))])
]
for title, crit in new_fvs:
    if title not in existing_fvs:
        req.append(fv(title, crit))

print("Requests:", len(req), "| DRY-RUN" if DRY else "| APPLY")
if DRY:
    print(json.dumps([list(r.keys())[0] for r in req]))
    sys.exit(0)
sheets.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests":req}).execute()
# 11) Pipeline-Header + Formel
formula = '=ARRAYFORMULA(IF(A2:A="";"";IFS(Y2:Y="yes";"Abgemeldet";AQ2:AQ<>"";"Bounce";(AR2:AR<>"")*(AR2:AR<>"bounced")*(AR2:AR<>"auto_reply_ooo");"Antwort";AO2:AO="sent";"Versendet";AW2:AW<>"";"Entwurf";Z2:Z="yes";"Freigegeben";1=1;"Neu")))'
sheets.spreadsheets().values().batchUpdate(spreadsheetId=SID, body={"valueInputOption":"USER_ENTERED","data":[{"range":"ALL_LEADS!BE1","values":[["Pipeline"]]},{"range":"ALL_LEADS!BE2","values":[[formula]]}]}).execute()
print("applied successfully")
