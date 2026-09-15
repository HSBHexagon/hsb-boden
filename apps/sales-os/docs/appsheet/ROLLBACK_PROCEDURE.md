# HSB Sales OS — Mobile AppSheet Rollback Procedure

## Übersicht
Dieses Dokument beschreibt die Schritte zur sofortigen und sicheren Deaktivierung oder Rückabwicklung des AppSheet-Zugriffs im Falle von Betriebsstörungen, ohne die kanonische Google Sheets Datenbank oder den Apps Script Kernbetrieb zu beeinträchtigen.

---

## 1. Sofortige Deaktivierung mobiler Schreibzugriffe (Maintenance Mode)
1. AppSheet Editor aufrufen (`appsheet.com`).
2. App **HSB Sales OS Mobile** auswählen.
3. Im Menü **Settings → General** navigieren.
4. Den Schalter **Maintenance Mode** auf `ON` stellen.
   - *Wirkung:* Die mobile App wird für Benutzer sofort gesperrt; es können keine Schreibvorgänge oder Synchronisationen mehr durchgeführt werden.

---

## 2. Vollständige Trennung von AppSheet
1. Im AppSheet Editor: **Manage → Deploy → Pause App** oder **Delete App**.
2. Im Google Sheet: Das Blatt `ALL_LEADS` bleibt zu 100 % unverändert.

---

## 3. Wiederherstellung von Daten (Falls unerwünschte Zell-Änderungen auftraten)
1. Im Google Sheet im Menü **Datei → Versionsverlauf → Versionsverlauf ansehen** aufrufen.
2. Den Prüfpunkt vor Beginn der Störung auswählen und auf **Diese Version wiederherstellen** klicken.
3. Alternativ: Automatisiertes Backup-Sheet aus dem Google Drive Ordner einspielen.

---

## 4. Unabhängiger Weiterbetrieb über die Google Sheets Seitenleiste
- Das bestehende Google Apps Script Sales OS arbeitet vollständig unabhängig von AppSheet.
- Bei Ausfall von AppSheet öffnen Joel oder Jordi einfach das Google Sheet im Browser und bedienen die Akquise- und Versandabläufe wie gewohnt über das Menü **HSB Sales OS → Seitenleiste öffnen**.
