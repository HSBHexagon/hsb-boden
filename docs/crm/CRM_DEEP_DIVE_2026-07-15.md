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

## 3. Kategorien: „Architekten“ vs. „Architekten-Ingenieure“

4.760 Zeilen tragen `Architekten`, 52 tragen `Architekten-Ingenieure` — praktisch dieselbe Zielgruppe, uneinheitlich benannt (vermutlich Artefakt zweier separater Quelldateien). Für Auswertungen/Filter in Joel/Jordis Arbeitsansicht sollten beide als eine Branchen-Gruppe behandelt werden (Anzeige-Alias, keine Änderung der Rohdaten).

## 4. Operative Felder sind bewusst leer — kein Fehler

`Interesse`, `Projektart`, `Belastungsart` sind zu 100 % leer (6.424/6.424). Das ist **korrekt für den Vor-Kontakt-Zustand**: Diese Felder werden erst nach dem ersten Gespräch befüllt, nicht beim Import. `Status` ist einheitlich `neu`, `Versandfreigabe` einheitlich `no`, `Opt-in/Opt-out` einheitlich `unknown` — ebenfalls der korrekte, sichere Ausgangszustand vor jeder Freigabe.

## 5. Zielmodell: Master + abgeleitete Joel-/Jordi-Ansichten

Aktuell sind die Joel- und Jordi-Exporte **Vollkopien** (jede Zeile physisch dupliziert), nicht abgeleitete Filter-Ansichten des Masters. Das ist im Google-Sheet-Kontext eine bekannte, dokumentierte Entscheidung (Drift-Risiko akzeptiert, siehe Handoff 2026-07-12). Für den nächsten Ausbauschritt (sobald Sheet-Zugriff wiederhergestellt ist) empfiehlt sich in Google Sheets:

1. **MASTER bleibt einzige Wahrheit** (bereits so).
2. **Joel-Tab / Jordi-Tab werden nach Backup und Owner-Freigabe zu
   QUERY-Formeln** statt Kopien. `Verantwortlicher` liegt im 29-Spalten-Modell
   in Spalte **AA**, nicht Q:
   - Joel: `=QUERY(MASTER!A:AC; "SELECT * WHERE AA = 'Joel Cherino Diaz'"; 1)`
   - Jordi: `=QUERY(MASTER!A:AC; "SELECT * WHERE AA = 'Jordi Post'"; 1)`
3. **Neue Tabs `HEUTE_JOEL` und `HEUTE_JORDI`**. Google-QUERY erwartet ein
   Datumsliteral; `HEUTE()` muss deshalb ausserhalb des Query-Strings formatiert
   werden. `Status` ist Spalte P, `Follow-up-Datum` R:
   - Joel: `=QUERY(MASTER!A:AC; "SELECT * WHERE AA = 'Joel Cherino Diaz' AND R <= date '"&TEXT(HEUTE();"yyyy-MM-dd")&"' AND P <> 'verloren'"; 1)`
   - Jordi: `=QUERY(MASTER!A:AC; "SELECT * WHERE AA = 'Jordi Post' AND R <= date '"&TEXT(HEUTE();"yyyy-MM-dd")&"' AND P <> 'verloren'"; 1)`
4. **Neuer Tab `OPPORTUNITIES`**. QUERY unterstuetzt hier kein SQL-`IN`; die
   Statuswerte werden explizit verknuepft:
   `=QUERY(MASTER!A:AC; "SELECT * WHERE P = 'interessiert' OR P = 'angebot-offen' OR P = 'termin'"; 1)`

Das Zielmodell umfasst damit **drei neue Tabs und fuenf QUERY-Formeln**. Die
drei neuen Tabs sind additiv und leicht entfernbar. Das Ersetzen der bestehenden
Joel-/Jordi-Vollkopien veraendert dagegen bestehende Tabs und darf nur nach
Backup, Live-Header-Pruefung und Owner-Freigabe erfolgen.

## 6. Verbindung zu Flyer/Mail/Attribution (bereits verifiziert)

Die Zuordnungskette Lead → Flyer → Mail-Variante → Landingpage → Follow-up ist bereits geschlossen (siehe `docs/ai_state/TRUTH_MATRIX_2026-07-15.md` Abschnitt 8). Mit der Region-Lücke aus Punkt 2 behoben, ließe sich zusätzlich nach Bundesland gruppieren — etwa für regionale Nachfass-Kampagnen oder Messeplanung.

## 7. Nicht ausgeführt in dieser Session (Owner-Gate)

- Live-Sheet-Struktur konnte nicht geprüft/verändert werden (Google-Account-Gate).
- Kein Schreibzugriff, keine Testzeile, keine Formel wurde live gesetzt.
- Sobald `cherinojoel@gmail.com` erreichbar ist, sind Punkt 5.2–5.4 nach
  Live-Header-Pruefung als fuenf QUERY-Formeln und drei neue Tabs umsetzbar.
  Eine Zeitdauer wird ohne echten Live-Lauf nicht behauptet.
