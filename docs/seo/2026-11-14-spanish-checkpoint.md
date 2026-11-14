# Checkpoint: Website-Feinschliff und spanische Vollübersetzung

Stand: 2026-11-14T15:05:24.556186+01:00

Joel verlangt mit „5 % abschluss jetzt“ den Abschluss dieser Sitzung. Stand sichern, keine weiteren Hintergrundarbeiten. Kein Push/Deploy erfolgt.

## Auftrag und Eigentümerschaft

Organische Besucher optimieren, Spanisch ergänzen, Website verfeinern. Joel hat anschließend ausdrücklich alle Fach- und Leistungsseiten auf Spanisch gewählt. Isolierter Branch feat/organic-growth-20261114, Arbeitsroot .worktrees/organic-growth-20261114. Gemeinsame Brain-Dateien und ursprünglicher Main-Worktree unverändert.

## Bereits gesicherter SEO-Schritt

Commit48c930ce4722c9ef1d09c6f40eeacb6030b0ba71:7wichtige Inhaltsseiten und interne Links optimiert. Damals420Webtests,15Browseransichten, Build/Check/Dry-run sowie850Sales-Safety-Tests mit1Skip erfolgreich. Nicht veröffentlicht. Details:2026-11-14-organic-growth.md.

## Geprüfter erster Spanisch-/Feinschliff-Stand

Vor Beginn der Vollübersetzung: spanische Einstiegsseite, Navigation/Footer/Cookies, Formular und noindex-Dankeseite, Browser-Sprachvorschlag; Referenzjahre umbrechungsfest, mobiler Kontaktanker korrigiert, echte Projektaufnahme auf Fremdsprachen-Einstiegen, sprachlich markierte Oberflächen. Geprüft:423Tests,77Browseransichten,66mobileAXE-Prüfungen ohne gemeldete WCAG-Regelverstöße, spanische Validierungs-/Fehler-/Erfolgszustände mit ausschließlich lokal simulierten Antworten; no-JS-Telefon/E-Mail-Fallback sichtbar.

Diese Nachweise gelten für den Stand vor der späteren Vollübersetzung, NICHT als Abnahme des aktuellen WIP. Rohbelege: ~/KI-System/work/hsb-polish-spanish-20261114/.

## Vollübersetzung: geschrieben, noch nicht integriert/freigegeben

-9Leistungsdatensätze und19FAQs unter src/data/es/services*.
-6Branchen,6technische Entscheidungshilfen,9regionale Guides.
-12strukturierte Fachartikel mit86vollständigen Abschnitten.
-8statische spanische Wissensseiten:2Leitfäden, Forensik-Hub und5Schadensbilder.
-8Referenz-Textkopien; Namen/Orte/Logos/Freigaben nicht erweitert.
-Spanische Typdefinitionen, Static-Pfadpaare und gemeinsamer Kontaktabschnitt.
-Alle Übersetzer arbeiteten in getrennten Dateibereichen; ihre Syntax-/Datenprüfungen ersetzen keine Gesamt-Abnahme.

## Konkrete offene Integration

1.src/lib/spanishPaths.ts fehlt noch (wird von den8neuen statischen Seiten importiert). Kein aktueller Gesamt-Build-PASS behaupten.
2.buildArticleJsonLd muss optional language fürES unterstützen; statischeES-Seiten übergeben dieses Feld bereits.
3.Spanische Routenvorlagen für9Leistungen,6Branchen,12Datenartikel,9Regionen,3Hubs und Referenzen fehlen. Daten-Slugs stehen jeweils in localizedSlug, logische Original-IDs bleiben gleich.
4.Deutsche Rückverweise/hreflang, sprachabhängige Navigation, selbstbezogene Canonicals und Sitemap-/Seitenregister vollständig integrieren. SEOHead unterstützt x-default bereits aus dem deutschen Alternate-Pfad.
5.Beanspruchungs-Check und Sanierungsfenster-Rechner vollständig lokalisieren. Diese beiden Folgeaufgaben wurden für den Sitzungsabschluss unterbrochen; keine Komponentenumsetzung als erledigt ausgeben. Originalkomponenten: forms/StressCheck.astro und calculator/SanierungsRechner.astro.
6.Mindestens50neue Gegenstücke (48Inhalts-/Übersichtsseiten plus2Tools) per Quell-/Routenmatrix abnehmen. Rechts-/Karriereseiten nicht Kern des Auftrags. Planer/LV-Einstiege wurden in e9da519 bewusst entfernt und bleiben ausgeschlossen.
7.Nach Integration alle Tests, Check, Build, Dry-run, komplette HTTP-/Link-/hreflang-/Schema-Prüfung und mobile/Desktop-/Formular-Abnahme wiederholen.
8.origin/main wurde zuletzt bei062f19a gelesen, zwei Sales-OS-Commits nach867e2c4. Vor Übernahme erneut fetch/diff prüfen und die fremden Sales-Änderungen erhalten; nicht Main zurücksetzen.

## Fachliche Korrekturen vor Veröffentlichung

-ES-Rutschhemmungsartikel enthält korrigierte V4/V6-Einheiten cm³/dm² und differenzierte Normhinweise. DE articles-supplemental.ts hat noch falsche4/6Literpro m² und alte Normzuordnung. Offizielle DGUV-Quelle208-041 Abs2.3 nennt4cm³/dm² fürV4. Direkten Primärdokument-Readback und DE/ES-Synchronisierung abschließen. Quellen:https://publikationen.dguv.de/widgets/pdf/download/article/890 sowie https://www.dguv.de/medien/fb-handelundlogistik/pdf-dokumente/faq-din-en-16165.pdf und https://www.dguv.de/dguv-test/aktuelles/2024/2024_details_634313.jsp . Suchauszüge werden separat gesichert.
-ES-TCO und Tiefkühlartikel sind bereits vorsichtiger formuliert; DE-Pauschalen5–8/25–30Jahre, Amortisation und Kältegarantien müssen synchron geprüft/präzisiert werden.
-ES-Manuelseiten verzichten auf pauschale1,5N/mm²,50–80mm,15–18mm und30cmAnkerabstand. Die4deutschenOriginalstellen sind noch zu synchronisieren: wissen/ruettelkeramik-agi-s-40/index.astro (Untergrund/Bettung/Belagsstärke) und wissen/fugen-forensik/rinnenkante-gerissen.astro (Ankerabstand).
-Weitere ungeprüfte Alt-Claims: Reinraum-/GMP-Aussagen, punktuelle200°C, Radius≥50mm/Gefälle1,5%, Tg50–60°C/fünffacheDehnung/PU9mm, Hohlkehlenhöhe15cm. Keine neue technische Freigabe aus bloßer Übersetzung ableiten.

## Sicherung und Fortsetzung

Aktueller WIP bleibt absichtlich uncommittet und unveröffentlicht. Ein Inventar mitSHA-256, ein Git-Patch und ein Archiv aller geänderten/neuen Quelldateien werden neben den Prüfnachweisen abgelegt. Keine Originale gelöscht oder zurückgesetzt. Vor Fortsetzung aktuellen Status/Hashes prüfen; Sicherung nicht ungeprüft über neuere Nutzeränderungen zurückspielen. Push/PR/Production-Deploy brauchen weiterhin ausdrückliche Freigabe nach vollständiger Abnahme.
