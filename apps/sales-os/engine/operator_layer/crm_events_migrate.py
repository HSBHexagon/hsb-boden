#!/usr/bin/env python3
"""Bringt INBOUND_EVENTS-Altzeilen in-place auf das 12-Spalten-Layout und markiert Wiederholungszeilen.

Erkennung Alt-Layout: Spalte C enthaelt einen Ereignistyp (SENT, REPLY, ...), nicht ein Postfach.
Python-Altzeilen (engine/reconcile_cloud_mailbox.py vor der Umstellung): 12 Zellen, aber Internet_Message_ID
leer in F und die ID in L (Raw_Link) -> L nach F verschieben, L leeren.
Wiederholung: gleiche Event_ID wie eine fruehere Zeile und Status NEEDS_REVIEW -> Processed=DUPLICATE.
Es wird keine Zeile geloescht oder verschoben (Trigger schreibt parallel). Ohne --apply wird nichts geschrieben.
"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
from crm_common import services, SID
TYPES = {"SENT","REPLY","POSITIVE_REPLY","NEGATIVE_REPLY","HARD_BOUNCE","SOFT_BOUNCE","OPT_OUT","AUTO_REPLY_OOO","CONTACT_CHURN"}
STOP = {"OPT_OUT","HARD_BOUNCE","CONTACT_CHURN","NEGATIVE_REPLY"}
MSGID_RE = re.compile(r"^<[^<>\s]+>$")   # RFC-5322 Message-ID in spitzen Klammern, so liegen die Live-Zeilen vor

def alt_zu_neu(r):
    """Alt: Event_ID·Timestamp·Type·Lead_ID·Owner·Email·Message_ID·In_Reply_To·Status·Details -> 12 Zellen.
    Owner (E) faellt weg (steht am Lead); Mailbox und Subject sind im Altbestand nicht vorhanden."""
    g = lambda i: str(r[i]) if len(r) > i else ""
    typ = g(2)
    return [g(0), g(1), "", g(5), "", g(6), g(3), typ, "yes" if typ in STOP else "no", g(8), g(9),
            ("In-Reply-To: " + g(7)) if g(7) else ""]

def plan(rows):
    """rows ohne Header -> Liste (zeilenindex_0basiert, neue_12_zellen, tags) nur fuer Zeilen, die sich aendern.
    tags: Tupel aus 'alt' (Apps-Script-Altlayout), 'msgid' (Message-ID von L nach F), 'dup' (als DUPLICATE markiert)."""
    changes, seen = [], collections.Counter()
    for i, r in enumerate(rows):
        g = lambda k: str(r[k]) if len(r) > k else ""
        tags = []
        alt = g(2) in TYPES
        neu = alt_zu_neu(r) if alt else (list(map(str, r)) + [""] * (12 - len(r)))[:12]
        if alt:
            tags.append("alt")
        elif not neu[5].strip() and MSGID_RE.match(neu[11].strip()):
            neu[5], neu[11] = neu[11].strip(), ""
            tags.append("msgid")
        seen[g(0)] += 1
        if seen[g(0)] > 1 and neu[9] == "NEEDS_REVIEW":
            neu[9] = "DUPLICATE"; tags.append("dup")
        if tags: changes.append((i, neu, tuple(tags)))
    return changes

def main(apply=False):
    sh, _ = services("cherinodiaz" if apply else "cherinojoel")
    vals = sh.spreadsheets().values().get(spreadsheetId=SID, range="INBOUND_EVENTS!A2:L").execute().get("values", [])
    changes = plan(vals)
    zaehl = collections.Counter(t for _, _, tags in changes for t in tags)
    print(f"Zeilen: {len(vals)} | Alt-Layout umgeschrieben: {zaehl['alt']} | Message-ID L->F: {zaehl['msgid']} | "
          f"als DUPLICATE markiert: {zaehl['dup']} | geaenderte Zeilen: {len(changes)}")
    if not apply:
        print("DRY-RUN - nichts geschrieben."); return 0
    data = [{"range": f"INBOUND_EVENTS!A{i + 2}:L{i + 2}", "values": [n]} for i, n, _ in changes]
    for k in range(0, len(data), 400):
        sh.spreadsheets().values().batchUpdate(spreadsheetId=SID, body={"valueInputOption": "RAW", "data": data[k:k + 400]}).execute()
    print("GESCHRIEBEN (in-place)."); return 0

if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
