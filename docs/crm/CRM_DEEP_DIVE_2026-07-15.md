# CRM Deep-Dive & Zielmodell — 2026-07-15

Analysebasis: lokale Rohexporte `data/lead-import/output/HSB_CRM_Leads_ALL_{MASTER,Joel,Jordi}_2026-07-08.csv` (bewusst unversioniert, `.gitignore`). Live-Sheet-Zugriff war in dieser Session durch ein Google-Account-Gate blockiert (siehe `docs/ai_state/TRUTH_MATRIX_2026-07-15.md` Abschnitt 5) — diese Analyse ersetzt keinen Live-Sheet-Check, sondern bereitet ihn vor.

## 1. Bestand — bestätigt sauber

- 6.424 Leads, exakt Joel 3.212 + Jordi 3.212, keine Überlappung, keine Dubletten.
- **0 fehlende E-Mail-Adressen, 0 doppelte E-Mail-Adressen** über den gesamten Bestand.
- Scoring ist intern konsistent und nachvollziehbar:

  | Score | Tier | Branche | Anzahl |
  |---|---|---|---|
  | 60 | B | Architekten / Architekten-Ingenieure | 4.812 |
  | 80 | A | Getränkeindustrie | 1.587 |
  | 85 | A | Molkerei / Brauerei (Spezialfälle) | 25 |

  → Score und Tier sind redundant, aber widerspruchsfrei. Getränke-/Molkerei-Branche wird bewusst höher priorisiert als Architekten — nachvollziehbare Geschäftslogik (direkte Bauherren/Betreiber vs. Vermittler).

## 2. Echter Datenqualitäts-Befund: Tier A hat keine Standortdaten

**Alle 1.612 Tier-A-Leads (100 %) haben ein leeres `Region`- UND ein leeres `Standort`-Feld.** Das ist kein Fehler der Import-Pipeline (Standort ist in der Quelle selbst leer), sondern eine Lücke der vier zugrunde liegenden Branchenlisten:

| Quelle | Betroffene Zeilen |
|---|---|
| Getraenke Deutschland Excel 2026-07-08 | 1.519 |
| Getraenke Schweiz Excel 2026-07-08 | 68 |
| Molkerei Schweiz Excel 2026-07-08 | 13 |
| Brauereiliste NRW Excel 2026-07-08 | 12 |

**Praktische Konsequenz für Joel/Jordi:** Die höchstpriorisierten Leads (Tier A, Score 80–85) lassen sich aktuell nicht nach Region filtern oder für Reise-/Vor-Ort-Termine clustern — genau die Leads, bei denen das am meisten zählt (Getränkeindustrie/Molkereien sind oft mit Werksbesichtigung verbunden).

**Empfehlung (keine Automatisierung ohne Freigabe):** Firmenname + vorhandene Website-URL genügen für eine manuelle oder KI-gestützte Nachanreicherung von Ort/Bundesland (z. B. Impressum-Abgleich). Sollte als eigener, kleiner freigegebener Arbeitsblock laufen — nicht spekulativ befüllen.

## 3. Kategorien: „Architekten" vs. „Architekten-Ingenieure"

4.760 Zeilen tragen `Architekten`, 52 tragen `Architekten-Ingenieure` — praktisch dieselbe Zielgruppe, uneinheitlich benannt (vermutlich Artefakt zweier separater Quelldateien). Für Auswertungen/Filter in Joel/Jordis Arbeitsansicht sollten beide als eine Branchen-Gruppe behandelt werden (Anzeige-Alias, keine Änderung der Rohdaten).

## 4. Operative Felder sind bewusst leer — kein Fehler

`Interesse`, `Projektart`, `Belastungsart` sind zu 100 % leer (6.424/6.424). Das ist **korrekt für den Vor-Kontakt-Zustand**: Diese Felder werden erst nach dem ersten Gespräch befüllt, nicht beim Import. `Status` ist einheitlich `neu`, `Versandfreigabe` einheitlich `no`, `Opt-in/Opt-out` einheitlich `unknown` — ebenfalls der korrekte, sichere Ausgangszustand vor jeder Freigabe.

## 5. Zielmodell: Master + abgeleitete Joel-/Jordi-Ansichten

Aktuell sind die Joel- und Jordi-Exporte **Vollkopien** (jede Zeile physisch dupliziert), nicht abgeleitete Filter-Ansichten des Masters. Das ist im Google-Sheet-Kontext eine bekannte, dokumentierte Entscheidung (Drift-Risiko akzeptiert, siehe Handoff 2026-07-12). Für den nächsten Ausbauschritt (sobald Sheet-Zugriff wiederhergestellt ist) empfiehlt sich in Google Sheets:

1. **MASTER bleibt einzige Wahrheit** (bereits so).
2. **Joel-Tab / Jordi-Tab werden zu QUERY-Formeln** statt Kopien:
   `=QUERY(MASTER!A:AC; "SELECT * WHERE Q = 'Joel Cherino Diaz'"; 1)` (Spalte Q = Verantwortlicher) — eliminiert Drift vollständig, ohne Apps Script.
3. **Neuer Tab `HEUTE_JOEL` / `HEUTE_JORDI`** (ebenfalls QUERY-basiert): filtert auf `Follow-up-Datum <= HEUTE()` UND `Status != 'verloren'` — beantwortet direkt „Was muss ich heute tun? Was ist überfällig?" ohne manuelles Sortieren.
4. **Neuer Tab `OPPORTUNITIES`** (nur bei `Status IN ('interessiert','angebot-offen','termin')`) für den Vertriebstrichter oberhalb reiner Kontaktverwaltung.

Keiner dieser Schritte erfordert das Löschen oder Umstrukturieren bestehender Daten — alle sind additiv (neue Tabs/Formeln) und rückgängig machbar.

## 6. Verbindung zu Flyer/Mail/Attribution (bereits verifiziert)

Die Zuordnungskette Lead → Flyer → Mail-Variante → Landingpage → Follow-up ist bereits geschlossen (siehe `docs/ai_state/TRUTH_MATRIX_2026-07-15.md` Abschnitt 8). Mit der Region-Lücke aus Punkt 2 behoben, ließe sich zusätzlich nach Bundesland gruppieren — etwa für regionale Nachfass-Kampagnen oder Messeplanung.

## 7. Nicht ausgeführt in dieser Session (Owner-Gate)

- Live-Sheet-Struktur konnte nicht geprüft/verändert werden (Google-Account-Gate).
- Kein Schreibzugriff, keine Testzeile, keine Formel wurde live gesetzt.
- Sobald `cherinojoel@gmail.com` erreichbar ist, sind Punkt 5.2–5.4 in ca. 15–20 Minuten manuell umsetzbar (drei QUERY-Formeln, ein neuer Tab).
