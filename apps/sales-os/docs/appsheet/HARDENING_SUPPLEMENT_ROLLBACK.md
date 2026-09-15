# HSB Sales OS — Hardening Supplement Rollback Procedure

## 1. Rollback der ACTIVITIES-Schema-Änderung
Sollte die 12-Spalten-Aktivitäten-Struktur unerwartete Inkompatibilitäten mit externen Prozessen verursachen:
1. In `apps_script/Engine.gs` greift der abwärtskompatible Wrapper `logActivity_` weiterhin transparent.
2. Die historische Migration ist additiv; bestehende Zeilen wurden nicht gelöscht.
3. Im Notfall kann `Engine.gs` auf die vorherige 5-Spalten-Version zurückgestellt werden, ohne dass `ALL_LEADS` oder der EML-Versandprozess beeinträchtigt werden.

---

## 2. Rollback des AppSheet Relational Timeline Views
1. Im AppSheet Editor: Tabelle `Activities` entfernen oder Spalte `[Related Activities]` im Blatt `Leads` deaktivieren.
2. Der Lead Detail View arbeitet sofort wieder als eigenständige Ansicht ohne Aktivitäten-Unterelemente.

---

## 3. Vollständiger System-Schutz
- Das kanonische Lead-System (`ALL_LEADS`) und alle Apps Script Kernfunktionen (`Config.gs`, `Engine.gs`, `Actions.gs`) sind durch getrennte Tabellen und Schutzbereiche 100% isoliert.
- Bei vollständigem AppSheet-Ausfall bleibt der Betrieb über die Google Sheets Desktop-Seitenleiste uneingeschränkt funktionsfähig.
