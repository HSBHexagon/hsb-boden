# HSB Website – technische Abschlussprüfung

Geprüft am 13. November 2026 auf Basis des gemergten PR #593, Commit `626faf9`.

## Gestaltung und Bedienung

- Industrieller Auftritt mit HSB-Farben und realen Projektfotos. Der Einstieg nennt Industrieböden, Säureschutz, Zielbranchen und den Anfrageweg direkt.
- Die kompakte Referenzübersicht zeigt sechs Namen und Logos sowie einen direkten Weg zu allen Referenzen. Technische Detailangaben bleiben in der ausführlichen Referenzdarstellung verfügbar.
- Das Reparatur-Modal zeigt Foto, Rückruf und Vor-Ort-Termin nebeneinander. Die Foto-Auswahl liegt auf kleinen Displays früher im sichtbaren Dialogbereich.
- Sprachauswahl mit Tastaturbedienung, Zustand über `aria-expanded`, Escape und Schließen außerhalb der Auswahl. Die mobile Navigation bleibt im Querformat scrollbar.
- Umbruch bei 200 Prozent Schriftvergrößerung für Navigation, Grids, Formulare und Buttons korrigiert.

## Behobene Fehler

- Axe meldete unpassende zugängliche Namen der Referenzlinks und der Sprachschaltfläche. Die zugänglichen Namen stimmen jetzt mit den sichtbaren Beschriftungen überein.
- Zwei gleichzeitig gestartete Foto-Auswahlen erzeugten vier Vorschaubilder trotz einer Grenze von drei. Die Aufbereitung wird jetzt sequenziell ausgeführt. Währenddessen ist das Absenden gesperrt, und `aria-busy` beschreibt den Zustand.
- Die Bildaufbereitung liegt in `src/lib/repairPhotoImage.ts`. JPEG-Neukodierung, Entfernung eingebetteter Bildmetadaten, maximale Kantenlänge von 1600 Pixeln und die Grenze von 4 MiB bleiben erhalten.
- Die beiden lokalen Browser-Prüfskripte verwenden einen gemeinsamen Dateiserver mit einer beim Start aufgebauten Liste zulässiger Build-Dateien. Ausbruchsversuche erhalten HTTP 404, ungültige URL-Kodierungen HTTP 400. Die Server lauschen auf Loopback.
- Die Browserprüfung des Modals bricht bei fehlgeschlagenen Assertions ab und schließt Browser und Server auch im Fehlerfall. Die parallele Foto-Auswahl ist als Regressionstest enthalten.
- Die Flyer-Seite hatte verschachtelte Hauptbereiche. Zwei Wissensseiten übersprangen eine Überschriftenebene.
- Der defekte Datenschutzverweis öffnet jetzt die Cookie-Einstellungen direkt und setzt den Tastaturfokus auf deren Bedienelement.
- Die technischen Datenschutzabschnitte wurden mit eigener Einwilligungsverwaltung, Google Analytics 4 und Cloudflare Web Analytics abgeglichen. Die bisherigen Angaben zu Real Cookie Banner, einem separaten Tag-Manager und Meta Conversions API passten zur vorhandenen Implementierung nicht.

## Abhängigkeiten

Der erste produktionsbezogene npm-Audit meldete neun betroffene Pakete, darunter vier mit hoher Einstufung. Der überarbeitete Paketstand erreicht sowohl mit `npm audit --omit=dev` als auch mit `npm audit` null gemeldete Schwachstellen.

Aktualisiert wurden Astro auf 7.4.11, Vite auf 8.3.8, serialize-javascript auf 7.1.4, Zod auf 4.6.7 und Vitest mit Coverage auf 5.1.0. Die transitive Auflösung verwendet sharp 0.35.5, fast-uri 3.1.9 und postcss-selector-parser 6.1.6. Wrangler liegt im kompatiblen Bereich bei 4.162.0. Die Zod- und Vitest-Hauptversionswechsel bestehen die unveränderten 411 fachlichen Tests und die Typprüfung. Die CI verwendet Node 22, CircleCI Node 22.23 und erfüllt die Mindestversion der aktualisierten Testwerkzeuge.

Die Abhängigkeiten wurden in diesem Worktree aus dem aktualisierten Lockfile separat installiert. Die manuellen Formularprüfungen wurden gegen den danach gebauten Stand wiederholt.

## Prüfergebnisse

| Prüfung | Ergebnis |
| --- | --- |
| `npm run test:run` | 411 Tests bestanden |
| `npm run check` | 0 Fehler, 0 Warnungen |
| Build mit beiden Formular-Schaltern | 69 HTML-Seiten erzeugt |
| `npm run deploy:dry-run` | Worker erfolgreich kompiliert |
| `npm run check:sitemap` | 65 Sitemap-URLs und indexierbare Seiten stimmen überein |
| `python3 scripts/verify_ssot.py` im Repository-Stamm | Exit 0 |
| Playwright mit 375, 768 und 1440 Pixeln | 207 Seitenprüfungen, 0 Überläufe, defekte Bilder, doppelte IDs oder JavaScript-Seitenfehler |
| Interne Verweise | 6.532 Linkvorkommen geprüft, 0 fehlende statische Ziele oder Anker im geprüften Umfang |
| axe-core 4.14.0 | Alle 69 Seiten bei 375 Pixeln ohne gemeldeten Verstoß |
| Zusätzliche Axe-Prüfung | Acht zentrale Seiten bei 375 und 1440 Pixeln sowie geöffnetes Modal, insgesamt 18 Zustände ohne gemeldeten Verstoß |
| Schriftvergrößerung auf 200 Prozent | Startseite, Kontakt und Reparatur bei 375, 720 und 1440 Pixeln ohne horizontalen Überlauf |
| Modal, mobile Navigation und Sprachauswahl | Tastatur, Escape, Fokus-Rückgabe und Querformat geprüft |
| Anfragewege | Foto, Rückruf und Vor-Ort-Termin mit simulierten Serverantworten erfolgreich durchlaufen |
| Fehlerversuche | Fehlendes Foto, HTTP 422, HTTP 429, Erhalt eingegebener Daten und erneutes Absenden geprüft |
| Foto-Aufbereitung | Gleichzeitige Auswahl auf drei Bilder begrenzt, JPEG-Nutzlast und maximale Kantenlänge geprüft |
| Build-Schalter | Alle vier Kombinationen aus Lead- und Foto-Schalter mit korrektem Modal, Kontaktformular und eindeutigem Reparaturanker geprüft |

Die Linkprüfung deckt statische, interne absolute Pfade und deren Anker ab. Serverfunktionen wie `/reparatur/`, `/api/` und bestehende Weiterleitungen wurden dabei separat behandelt.

## Lighthouse

Lighthouse 13.6.0, lokaler Produktionsbuild, mobile Standardsimulation. Drei aufeinanderfolgende Einzelmessungen ergaben die folgenden Werte. Die Zeit- und Layoutmessgrößen zeigen den Median.

| Kategorie oder Messgröße | Ergebnis |
| --- | --- |
| Performance | 100 |
| Accessibility | 100 |
| Best Practices | 100 |
| SEO | 100 |
| LCP | 0,903 Sekunden im Median |
| TBT | 0 Millisekunden |
| CLS | 0,0000225 |

Ein früherer, parallel zu anderen Browserprüfungen ausgeführter Lauf erreichte Performance 80 mit 827 Millisekunden TBT. Die drei seriellen Messungen dokumentieren die Wiederholungsprüfung unter geringerer lokaler Last. Feldmesswerte aus realen Kundenbesuchen stehen aus.

## Abnahmegrenzen

Die Anfrageprüfungen verwenden im Browser abgefangene Serverantworten. Der produktive SMTP-Eingang und die reale Zustellung einer Anfrage bleiben gesonderte Nachweise. Die vorhandenen Handler- und SMTP-Tests sind Bestandteil der 411 Tests.

Das technische Ergebnis ist für die anschließende CI- und Releaseprüfung vorbereitet. Die Produktionsveröffentlichung folgt der ausdrücklichen Betreiberfreigabe gemäß `AGENTS.md`. Eine juristische Abnahme der Datenschutzinformation und ein gemessener Wettbewerbsvergleich bleiben offen. Automatische Accessibility-Prüfungen und Tastaturtests ersetzen eine vollständige manuelle WCAG-Abnahme durch qualifizierte Prüfer.

Lokale Rohdaten und Screenshots liegen unter `/tmp/hsb-final-review-20261113/`.
