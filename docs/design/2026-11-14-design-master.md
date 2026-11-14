# HSB – erweiterte Design- und UX-Optimierung (umgesetzt)

Stand 14. November 2026. Grundlage ist die Codex-Übersicht vom 13. November (acht Punkte, vier Seiten geprüft).
Diese Fassung erweitert sie auf alle 68 erreichbaren Seiten bei 375 und 1440 Pixeln und hält fest, was umgesetzt ist.

Genutzte Skills: UI UX Pro Max (Muster „Trust & Authority + Conversion", Stil „Accessible & Ethical"), Frontend Design, UI UX Conversion.
Marke bleibt unverändert: HSB-Rot, Schwarz, Outfit. Die Farb- und Schriftempfehlung des Skills wurde nicht übernommen.

## Messwerte vorher und nachher

| Messgröße | Vorher | Nachher |
| --- | --- | --- |
| Überschrift der Unterseiten am Desktop | 83 px | 52 px |
| Überschrift der Unterseiten mobil | 42 px | 31 px |
| Seiten mit Überschrift über drei Zeilen, mobil | 46 | 23 |
| Seiten mit Überschrift über drei Zeilen, Desktop | 11 | 2 |
| Seiten mit Projektfoto im ersten Bildschirm, mobil | 8 | 24 |
| Seiten mit Schrift unter 12 px, mobil | 68 | 1 (Ortsnamen in der Standortkarte) |
| Höhe der Startseite mobil | 14.822 px | 12.957 px |
| Pflichtangaben im Kontaktformular | 10 Felder plus Belastung | 7 Felder plus Belastung |
| Seiten mit horizontalem Überlauf | 0 | 0 |

## Die acht Codex-Punkte

| Rang | Punkt | Stand |
| --- | --- | --- |
| 1 | Mobile Auswahl „Foto / Rückruf / Termin" bricht im Wort | Umgesetzt. Unter 640 px drei vollbreite Zeilen, Titel einzeilig, Hinweis rechts. |
| 2 | Kontaktformular verlangt zu viel | Teilweise umgesetzt. Branche, Fläche und laufender Betrieb sind optional und eingeklappt. Die Belastungsangabe bleibt Pflicht, siehe „Offen". |
| 3 | „Ersteinschätzung" führt zu zwei verschiedenen Zielen | Umgesetzt. „Projekt besprechen" führt immer zur Kontaktseite, „Schadstelle melden" immer zur Reparaturanfrage. |
| 4 | Referenzseite beginnt mit sehr großer Überschrift | Umgesetzt für alle Unterseiten: kleinere Überschrift, Projektfoto im Seitenkopf. |
| 5 | Startseite mobil zu lang | Umgesetzt: Branchen zweispaltig, Nachweiskarten kompakt, Fußzeile zweispaltig. |
| 6 | Referenzen als Fallbeispiele | Struktur bestand bereits (Anforderung, Lösung, Ergebnis, System). Lesbarkeit verbessert. Fotos werden nicht einzelnen Kunden zugeordnet, weil dafür keine Freigabe vorliegt. |
| 7 | Interner Begriff „Freigabelogik" | Umgesetzt: „Ausgeführte Projekte zu dieser Leistung". |
| 8 | Mobiles Hero-Foto erscheint spät | Umgesetzt: Einleitung mobil gekürzt. |

## Zusätzlich gefunden und umgesetzt

- Überschriften der Unterseiten waren größer als die Hauptaussage der Startseite. Jetzt eine gemeinsame Skala mit ausgeglichenem Zeilenumbruch.
- Seitenkopf mit Projektfoto auf Leistungs-, Branchen-, Standort-, Referenz- und Ablaufseiten (24 statt 8 Seiten zeigen im ersten Bildschirm ein Foto).
- Kontaktseite: Formular beginnt mobil rund 600 px früher. Die Hinweise links passen jetzt zu den Formularfeldern.
- Kontaktformular: Belastungen als gut treffbare Auswahlfelder mit sichtbarem Zustand.
- Cookie-Hinweis mobil: Schrift 12 statt 11 px, Schaltflächen 44 px hoch.
- Tippziele: Hauptnavigation, Sprachlinks und einzelne Textlinks auf 44 px, Fußzeilenlinks auf 32 px mit Abstand.
- Referenzgalerie: Leerfläche unter dem großen Foto geschlossen.
- Regressionstests für diese Regeln (`apps/website/tests/design-master.test.ts`).

## Offen

- Die Belastungsangabe ist im Serververtrag Pflicht (`loads` mindestens ein Eintrag). Sie ganz optional zu machen, ändert den Vertrag zum Apps-Script-Empfänger und braucht eine echte Testanfrage.
- Der Sanierungsfenster-Rechner zeigt Besuchern den Vermerk „MOCK_DATA". Das folgt der Projektregel zur Kennzeichnung von Beispieldaten, liest sich aber intern.
- 23 Wissensartikel haben mobil weiterhin vier bis fünf Überschriftenzeilen. Das liegt an der Länge der Titel, nicht an der Schriftgröße.
- Die Wirkung auf die Anfragequote ist nicht gemessen.

## Nachtrag: eigener Gestaltungsschwerpunkt (14.11., zweiter Durchgang)

- **Systemschnitt Rüttelkeramik.** Isometrische Zeichnung der fünf Schichten (Betonuntergrund, Haftbrücke, Rüttelbett, Sechskantkeramik, Reaktionsharzfuge) auf der Startseite und der Leistungsseite „Keramische Industrieböden". Die Schichten setzen sich beim ersten Sichtkontakt einmal von unten nach oben; die Zeile unter dem Mauszeiger oder Tastaturfokus hebt ihre Schicht hervor. Inhalt ist eine echte Liste, die Zeichnung selbst ist Schmuck. Ohne JavaScript und bei reduzierter Bewegung steht sie vollständig da.
- **Sechskant-Raster** als leise Struktur der dunklen Flächen (Startseiten-Kopf, Systemschnitt, Abschluss-Aufruf).
- **Weicher Seitenwechsel** über die CSS-Seitenübergänge des Browsers, ohne JavaScript.
- Preis: Die Startseite wird dadurch länger (Desktop rund 8.670 px, mobil rund 14.170 px).
