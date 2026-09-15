# HSB Sales OS — Mobile Hardening & Activities Timeline Runbook

## 1. Aktivitäten-Historie im mobilen Lead Detail
1. **Lead öffnen:** Im Tab `MY LEADS` auf einen zugewiesenen Lead tippen.
2. **Timeline einsehen:** Unter den Stammdaten zeigt der Bereich `Related Activities` chronologisch alle vergangenen Interaktionen (Erstansprache, Notizänderungen, eingegangene Antworten).
3. **Details anzeigen:** 1-Tap auf einen Aktivitäts-Eintrag öffnet die vollständige Notiz und das Protokoll.

---

## 2. Gesprächsnotizen und Wiedervorlagen mobil pflegen
1. Im Lead Detail auf **Bearbeiten (Stift-Symbol)** tippen.
2. Folgende 3 Felder stehen zur sicheren Bearbeitung bereit:
   - `Notizen`: Gesprächsinhalt, Kundenfeedback, Sonderwünsche eintragen.
   - `Nächste Aktion`: Aus dem kontrollierten Dropdown wählen (z.B. "Angebot nachfassen", "Zweiter Anruf").
   - `Follow-up-Datum`: Datum für die nächste Wiedervorlage setzen.
3. Auf **Speichern** tippen.
4. **Automatischer Audit-Trail:** AppSheet erzeugt automatisch einen neuen `NOTE_EDITED`-Eintrag in der Aktivitäten-Tabelle mit Zeitstempel und deiner Operator-Kennung (`USEREMAIL()`).

---

## 3. Synchronisation & Offline-Verhalten
- Nach dem Speichern wird die Änderung sofort in die lokale Warteschlange eingereiht und bei bestehender Internetverbindung automatisch ins Google Sheet übertragen.
- Im Offline-Modus (z.B. Funkloch) bleibt der Lead vollständig lesbar und editierbar. Bei Wiederverbindung erfolgt der Upload atomar und ohne Dubletten.
