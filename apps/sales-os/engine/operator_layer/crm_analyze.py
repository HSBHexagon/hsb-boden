import json, collections, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from crm_common import col
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SID = "1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"
PROFILE = sys.argv[1] if len(sys.argv) > 1 else "cherinojoel"
tok = json.load(open(f"/Users/joelcherinodiaz/.config/google-workspace-mcp/profiles/{PROFILE}/tokens.json"))
cred = json.load(open("/Users/joelcherinodiaz/.config/google-workspace-mcp/credentials.json"))
c = cred.get("installed") or cred.get("web") or cred
creds = Credentials(token=tok.get("access_token"), refresh_token=tok.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token", client_id=c["client_id"],
                    client_secret=c["client_secret"], scopes=tok.get("scope","").split())
svc = build("sheets","v4",credentials=creds, cache_discovery=False)

meta = svc.spreadsheets().get(spreadsheetId=SID, fields=
  "properties(title,locale,timeZone),namedRanges,sheets(properties(title,index,hidden,gridProperties(rowCount,columnCount,frozenRowCount,frozenColumnCount)),protectedRanges,conditionalFormats,basicFilter,filterViews,bandedRanges,charts,developerMetadata)").execute()
print("== SPREADSHEET ==", meta["properties"])
print("named ranges:", len(meta.get("namedRanges",[])), [n["name"] for n in meta.get("namedRanges",[])][:20])
print()
print("== TABS ==")
for s in meta["sheets"]:
    p = s["properties"]; g = p["gridProperties"]
    print(f"{p['index']:>2} {p['title']:<38} hidden={p.get('hidden',False)!s:<5} grid={g['rowCount']}x{g['columnCount']} frozen={g.get('frozenRowCount',0)}/{g.get('frozenColumnCount',0)} protected={len(s.get('protectedRanges',[]))} condFmt={len(s.get('conditionalFormats',[]))} filterViews={len(s.get('filterViews',[]))} basicFilter={'basicFilter' in s} charts={len(s.get('charts',[]))}")

# data row counts per tab (column A non-empty)
print("\n== DATA ROWS (Spalte A nicht leer) ==")
titles = [s["properties"]["title"] for s in meta["sheets"]]
ranges = [f"'{t}'!A1:A" for t in titles]
resp = svc.spreadsheets().values().batchGet(spreadsheetId=SID, ranges=ranges).execute()
for t, vr in zip(titles, resp["valueRanges"]):
    vals = vr.get("values", [])
    n = sum(1 for r in vals if r and str(r[0]).strip())
    print(f"{t:<38} {n:>6}")

# ALL_LEADS: header + formulas check + distributions
hdr = svc.spreadsheets().values().get(spreadsheetId=SID, range="ALL_LEADS!1:1").execute()["values"][0]
print("\n== ALL_LEADS Header (", len(hdr), ") ==")
want = ["Tier","Status","Nächste Aktion","Follow-up-Datum","Opt-in-Status","Opt-out-Status","Versandfreigabe","Verantwortlicher","Segment","Batch_ID","Send_Status","Send_Datum","Bounce_Status","Reply_Status","Legal_Basis","Suppressed","Batch_Status","Draft_ID","Drafted_At","Approved_At","Outlook_Message_ID","Last_Reply_At","Last_Error","Kampagne","Branche","Region","Quelle","Score","Interesse","Projektart","Sanierungsfenster"]
idx = {h:i for i,h in enumerate(hdr)}
rng = [f"ALL_LEADS!{col(idx[w])}2:{col(idx[w])}" for w in want if w in idx]
resp = svc.spreadsheets().values().batchGet(spreadsheetId=SID, ranges=rng).execute()
dist = {}
for w, vr in zip([w for w in want if w in idx], resp["valueRanges"]):
    vals = [ (r[0] if r else "") for r in vr.get("values", []) ]
    vals += [""]*(6424-len(vals))
    cnt = collections.Counter(("<leer>" if v.strip()=="" else v.strip()) for v in vals)
    dist[w]=cnt
    top = cnt.most_common(8)
    filled = 6424-cnt.get("<leer>",0)
    if w in ("Draft_ID","Outlook_Message_ID","Send_Datum","Drafted_At","Approved_At","Last_Reply_At","Follow-up-Datum","Last_Error","Nächste Aktion","Batch_ID","Kampagne"):
        print(f"{w:<20} befüllt={filled:>5}  distinct={len(cnt)-(1 if '<leer>' in cnt else 0)}  top={[(k[:24],n) for k,n in top[:4]]}")
    else:
        print(f"{w:<20} befüllt={filled:>5}  {top}")

# cross checks
def series(w):
    vr = svc.spreadsheets().values().get(spreadsheetId=SID, range=f"ALL_LEADS!{col(idx[w])}2:{col(idx[w])}6425").execute().get("values",[])
    v=[(r[0].strip() if r else "") for r in vr]; return v+[""]*(6424-len(v))
ss, sd, dr, opt, sup, vf, rs, lr, nb = series("Send_Status"), series("Send_Datum"), series("Draft_ID"), series("Opt-out-Status"), series("Suppressed"), series("Versandfreigabe"), series("Reply_Status"), series("Last_Reply_At"), series("Bounce_Status")
print("\n== KONSISTENZ ==")
print("SENT ohne Send_Datum:", sum(1 for a,b in zip(ss,sd) if a.upper()=="SENT" and not b))
print("Send_Datum ohne SENT:", sum(1 for a,b in zip(ss,sd) if b and a.upper()!="SENT"))
print("Draft_ID vorhanden, Send_Status leer:", sum(1 for a,b in zip(dr,ss) if a and not b))
print("Opt-out=yes aber Suppressed!=yes:", sum(1 for a,b in zip(opt,sup) if a.lower()=="yes" and b.lower()!="yes"))
print("Opt-out=yes aber Versandfreigabe=yes:", sum(1 for a,b in zip(opt,vf) if a.lower()=="yes" and b.lower()=="yes"))
print("Bounce gesetzt aber Versandfreigabe=yes:", sum(1 for a,b in zip(nb,vf) if a and a.lower() not in ("","none","no") and b.lower()=="yes"))
print("Reply_Status gesetzt:", sum(1 for a in rs if a), " Last_Reply_At gesetzt:", sum(1 for a in lr if a))

# JOEL/JORDI: formula or copy?
for t in ("JOEL","JORDI","VERSAND","READY_CANDIDATES","DASHBOARD"):
    f = svc.spreadsheets().values().get(spreadsheetId=SID, range=f"'{t}'!A1:C6", valueRenderOption="FORMULA").execute().get("values",[])
    has_formula = any(str(c).startswith("=") for r in f for c in r)
    print(f"\n{t}: Formeln in A1:C6 -> {has_formula}; erste Zellen:", [ [str(c)[:60] for c in r][:2] for r in f[:3]])
# Lead-ID overlap
ids = {}
for t in ("ALL_LEADS","JOEL","JORDI"):
    v = svc.spreadsheets().values().get(spreadsheetId=SID, range=f"'{t}'!A2:A").execute().get("values",[])
    ids[t] = set(r[0].strip() for r in v if r and r[0].strip())
print("\nLead-IDs: ALL", len(ids["ALL_LEADS"]), "JOEL", len(ids["JOEL"]), "JORDI", len(ids["JORDI"]), "JOEL∩JORDI", len(ids["JOEL"]&ids["JORDI"]), "JOEL∪JORDI==ALL:", (ids["JOEL"]|ids["JORDI"])==ids["ALL_LEADS"], "ALL dupl:", 6424-len(ids["ALL_LEADS"]) if len(ids["ALL_LEADS"])<=6424 else 0)

# row heights ALL_LEADS (sample first 50 rows) + wrap strategy
g = svc.spreadsheets().get(spreadsheetId=SID, ranges=["ALL_LEADS!A1:BD30"], fields="sheets(data(rowMetadata(pixelSize),columnMetadata(pixelSize,hiddenByUser),rowData(values(effectiveFormat(wrapStrategy,backgroundColor)))))").execute()
d = g["sheets"][0]["data"][0]
rh = [r.get("pixelSize") for r in d.get("rowMetadata",[])]
print("\nALL_LEADS Zeilenhöhen (px) Zeile 1-30:", rh[:30])
cw = d.get("columnMetadata",[])
print("Spaltenbreiten (px):", [c.get("pixelSize") for c in cw][:56])
print("ausgeblendete Spalten:", [col(i) for i,c in enumerate(cw) if c.get("hiddenByUser")])
wr = collections.Counter(v.get("effectiveFormat",{}).get("wrapStrategy") for r in d.get("rowData",[])[1:] for v in r.get("values",[]))
print("wrapStrategy Zeile 2-30:", wr)
