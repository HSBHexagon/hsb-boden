import csv, hashlib, os, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
from crm_common import services, SID
sheets, drive = services()
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")  # je Lauf ein eigener Ordner, nichts wird ueberschrieben
out = os.path.expanduser(f"~/KI-System/08_System/backups/{stamp}-hsb-crm-sheet"); os.makedirs(out, exist_ok=True)
copy = drive.files().copy(fileId=SID, body={"name":f"HSB CRM MASTER 6424 – Sales OS – BACKUP-{stamp}"}).execute()
print("Drive-Kopie:", copy["id"], copy["name"])
meta = sheets.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(title))").execute()
titles = [s["properties"]["title"] for s in meta["sheets"]]
lines=[]; counts={}
for t in titles:
    vals = sheets.spreadsheets().values().get(spreadsheetId=SID, range=f"'{t}'", valueRenderOption="FORMULA").execute().get("values",[])
    fn = os.path.join(out, t.replace("/","_")+".csv")
    with open(fn,"w",newline="",encoding="utf-8") as f:
        csv.writer(f).writerows(vals)
    h = hashlib.sha256(open(fn,"rb").read()).hexdigest()
    lines.append(f"{h}  {os.path.basename(fn)}"); counts[t]=len(vals)
open(os.path.join(out,"MANIFEST.sha256"),"w").write("\n".join(lines)+"\n")
open(os.path.join(out,"BACKUP_INFO.txt"),"w").write(f"quelle={SID}\nkopie={copy['id']}\nzeit={datetime.datetime.now().isoformat()}\nrender=FORMULA\n"+"\n".join(f"{t}={n}" for t,n in counts.items())+"\n")
print("Tabs:", len(titles), "ALL_LEADS Zeilen:", counts["ALL_LEADS"], "JOEL:", counts["JOEL"])
