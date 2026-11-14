# Organische Besucher: geprüfte Inhaltsoptimierung vom 14.11.2026

Status: lokal umgesetzt und geprüft; Veröffentlichung und Ranking-Wirkung stehen aus.

Branch: feat/organic-growth-20261114  
Basis: origin/main, 867e2c4914ee7694c72e5057fa148bb053cd4152  
Arbeitsverzeichnis: .worktrees/organic-growth-20261114

## Ziel und belegte Ausgangslage

Mehr passende organische Besucher auf den bestehenden Leistungs- und Branchenseiten gewinnen. Grundlage sind die direkten Search-Console-Daten vom 15.10.–11.11.2026, alle Länder/Geräte, Search Type Web. Die durchschnittlichen Positionen sind historische Mittelwerte und keine aktuellen lokalen Einzelränge.

| Suchbegriff | Impressionen | Ø Position | Bestehender Ansatzpunkt |
|---|---:|---:|---|
| rüttelboden | 68 | 62,8 | Keramik-Leistungsseite |
| rüttelboden aufbau | 57 | 48,2 | AGI-S-40-Ratgeber |
| rüttelklinker | 66 | 32,5 | Keramik-Leistungsseite |
| pu-beton | 60 | 10,6 | PU-Beton-Leistungsseite |
| whg abdichtung | 64 | 11,5 | WHG-Leistungsseite |
| industrieboden lebensmittelindustrie | 64 | 16,8 | Branchen-/Vergleichsinhalte |
| industrieboden chemieindustrie | 68 | 5,5 | Chemie-Branchenpage |

Die Property hatte 45 Klicks und 6.020 Impressionen im Fenster. GA4 hatte 31 organische Sitzungen. Daraus wird keine prognostizierte Besuchersteigerung abgeleitet.

## Umgesetzt

- Keramik-Leistung: Rüttelboden in Titel und H1; Rüttelfliesen und Rüttelklinker im erklärenden Inhalt; praktische Antworten zu Systemunterschieden, Aufbau und Kostenfaktoren.
- Aufbau-Ratgeber: eigenständige Informationsabsicht in Titel, H1 und Einführung; passende Links zur Keramik-Leistung und zum Systemvergleich.
- Die bestehende Entscheidungshilfe auf der Keramik-Leistung verlinkt den Aufbau-Ratgeber. Footer-Anker benennen Leistung und Aufbau verständlicher.
- PU-Beton und WHG: genauere Titel, H1 und Beschreibungen sowie systembezogene Planungsfragen ohne pauschale Freigabe- oder Zulassungszusagen.
- Lebensmittel-, Molkerei- und Chemiebranche: präzisere Einstiege und zusätzliche Fragen zur konkreten Planung. Die Lebensmittel-Seite behält HACCP im Titel; ihr FAQ ordnet den Boden als Teil des betrieblichen Hygienekonzepts ein.
- Insgesamt 13 zusätzliche FAQ-Antworten auf sechs Leistungs-/Branchenseiten. Vorhandene FAQ-Ausgabe und zugehöriges JSON-LD nutzen dieselben Daten.
- Fachartikel-Headline und Metadaten sind mit dem Inhaltskatalog und dem Article-JSON-LD synchronisiert.

Es entstehen keine neuen Leistungs-URLs oder konkurrierenden Landingpage-Duplikate. Bestehende Canonicals, Sitemap-URLs und Anfragewege bleiben erhalten.

## Korrektur zum vorherigen Audit

Der festgestellte fehlende HTML-Eingang zu /planer/ ist ein tatsächlicher Crawl-Befund, aber kein automatisch zu behebender Fehler. Commit e9da519 hat Planer-/LV-Einstiege ausdrücklich entfernt. Diese Änderung wird respektiert. Die frühere Audit-Empfehlung, das Portal wieder zu verlinken, ist deshalb für diese Umsetzung nicht übernommen.

## Verifikation

- Baseline vor Änderungen: 420 Tests bestanden; Build erfolgreich.
- Nach Änderungen: 420 Tests in 56 Dateien bestanden.
- Astro-Check: 0 Fehler, 0 Warnungen, 1 Hinweis.
- Astro-Build: 69 Seiten.
- Bestehender deploy:dry-run: erfolgreich, Worker kompiliert.
- Browser: sieben betroffene Seiten jeweils bei 375 und 1440 Pixeln plus Startseite bei 375 Pixeln, insgesamt 15 Ansichten. Keine horizontalen Überläufe oder JavaScript-Laufzeitfehler.
- In den geprüften Ansichten jeweils eine H1, passende Canonicals; FAQ-Zahl stimmt mit JSON-LD überein. Article-Headline entspricht der sichtbaren H1.
- Reale lokale Nutzerfolge: Aufbau-Ratgeber → Keramik-Leistung → FAQ öffnen → Kontaktseite. Keine Formularübermittlung an die Produktion.
- Alle 65 Sitemap-URLs identisch mit der vorigen Live-Aufnahme.
- SSOT-Verifier und git diff --check erfolgreich.

Belege: /Users/joelcherinodiaz/KI-System/work/hsb-organic-growth-20261114/  
Datenbasis: /Users/joelcherinodiaz/KI-System/work/hsb-audit-20261114/evidence/google-deeper.json

## Veröffentlichung und Erfolgskontrolle

Push, PR und Production-Deploy sind noch nicht erfolgt. Die Projektregeln verlangen dafür eine ausdrückliche Freigabe. Ein Production-Deploy erfolgt ausschließlich über den bestehenden manuellen Workflow nach grünen Pflichtprüfungen.

Nach Veröffentlichung zuerst die tatsächlichen Titel, H1, Links und Canonicals per HTTP/Browser prüfen. Danach für dieselben Zielseiten und Suchbegriffe zwei abgeschlossene 28-Tage-Fenster vergleichen. Zusätzlich Deutschland separat betrachten. Primäre Kennzahlen: Google-Klicks, organische GA4-Sitzungen und nachvollziehbar gemessene qualifizierte Anfragen. Query-Anonymisierung und Consent-Abdeckung bleiben Messgrenzen.

Der Lead-E2E-Nachweis, Verzeichniskorrekturen, GBP-Inhaberzugriff und Bild-/LCP-Optimierungen bleiben getrennte Aufgaben aus dem Audit. Es wurden keine Google-Konfigurationen, externen Profile, Zugangsdaten oder Versandflüsse verändert.
