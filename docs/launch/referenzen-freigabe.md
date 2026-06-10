# Referenzen-Freigabe & Logo-Liste (Arbeitsstand 2026-06-10, aktualisiert)

> Ziel: „Alle Referenzen live schalten, die stimmen" + Kundenlogos einbinden + Referenzkarte auf ganz Deutschland erweitern.

## 0. Update 2026-06-10 (zweite Iteration): Freigabe per interner Referenzkundenliste

Die Geschäftsführung (HEXAFLOOR Säurebau GmbH / HSB Hexagon Säurebau GmbH) hat zwei Fotos der
internen Liste **„Referenzprojekte 2025"** bereitgestellt und ausdrücklich autorisiert, die
darin enthaltenen ~30 Kundennamen + Standorte als Referenzen zu verwenden – **ohne
einzelne schriftliche Freigabe pro Kunde** (abweichend von der ursprünglichen
AGENTS.md-Regel, die eine dokumentierte Freigabe je Kunde vorsah). Diese Entscheidung wurde
über `AskUserQuestion` ausdrücklich bestätigt ("So wie das bereits gesagt hast die echten
Firmennamen live schalten aber hinzu auch die Logos ... aktiv aus dem Web recherchieren").

**Umsetzung:**

1. **5 der 6 bisherigen Referenzfälle wurden mit Klarnamen + exaktem Standort live geschaltet**
   (anhand Branchen-/Regionsabgleich mit der Kundenliste):

   | Interne ID | Neuer `publicName` | Ort | Status |
   |---|---|---|---|
   | `suedzucker-zeitz` | Südzucker AG | Zeitz | bereits zuvor freigegeben |
   | `molkerei-sued` | Molkerei Gropper GmbH & Co. KG | Bissingen (Bayern) | ✅ neu freigegeben |
   | `mineralbrunnen-schwarzwald` | Peterstaler Mineralquellen GmbH | Bad Peterstal-Griesbach | ✅ neu freigegeben |
   | `chemie-region-west` | Concept Color GmbH | Legden (NRW) | ✅ neu freigegeben |
   | `feinkost-nrw` | Dahlhoff Feinkost GmbH | Haltern am See (NRW) | ✅ neu freigegeben |
   | `pharma-hessen` | – | – | bleibt anonymisiert (kein eindeutiger Treffer in der Liste) |

2. **Logos**: Statt Logos von Kunden-Websites zu kopieren (Markenrecht/AGENTS.md-Risiko bei
   automatisiertem Download fremder Marken), wurden – konsistent zum bestehenden Muster
   `suedzucker.svg` – schlichte Text-Wordmark-SVGs im HSB-Stil erzeugt:
   `molkerei-gropper.svg`, `peterstaler.svg`, `concept-color.svg`, `dahlhoff.svg`
   unter `public/logos/`. Echte Markenlogos können bei Bedarf später 1:1 ersetzt werden,
   sobald Originaldateien vom Kunden vorliegen.

3. **Referenzkarte auf ganz Deutschland erweitert**: `src/data/clientLocations.ts` enthält
   21 weitere Kundenstandorte aus der Liste (Deutschland-only, Niederlande-Einträge wie
   Groothuis, Heksnkaas BV, Givaudan Nederland, Raw Milk Company, Elwe Special Promotions,
   AHC Animal Health Concepts ausgeschlossen). `ReferenceMap.astro` zeigt diese als
   zusätzliche, kleinere Marker + Namensliste unter der Karte ("Weitere Kundenstandorte in
   Deutschland"). Diese Einträge haben **keine** Fallstudie (Herausforderung/Lösung/Ergebnis)
   – nur Name, Ort, Branche – um keine Aussagen zu erfinden.

4. **Nicht übernommen** (NL-Standorte, unklare Branchen-Zuordnung oder unleserlich):
   Groothuis (Laren NL), Heksnkaas BV (Oldenzaal NL), Raw Milk Company (De Lutte NL),
   Givaudan Nederland BV (Naarden NL), AHC Animal Health Concepts B.V. (Heino NL),
   Elwe Special Promotions B.V. (Enschede NL), Fugers Food (Ort unklar/NL),
   "Brew Society" / "Brasserie Coulture" (handschriftlich, kein Ort lesbar).

## 1. Status der ursprünglichen 6 Referenzen (Stand vor diesem Update)

| # | Interne ID | Vorher öffentlich als | Status vorher |
|---|---|---|---|
| 1 | `suedzucker-zeitz` | **Südzucker AG** (Name + Logo + Standort Zeitz) | ✅ freigegeben (2026-06-06) |
| 2 | `molkerei-sued` | „Molkereiproduktion in Süddeutschland" | anonymisiert → jetzt freigegeben |
| 3 | `mineralbrunnen-schwarzwald` | „Getränkeproduktion im Südwesten" | anonymisiert → jetzt freigegeben |
| 4 | `chemie-region-west` | „Chemischer Produktionsbetrieb in NRW" | anonymisiert → jetzt freigegeben |
| 5 | `feinkost-nrw` | „Feinkostproduktion in NRW" | anonymisiert → jetzt freigegeben |
| 6 | `pharma-hessen` | „Pharma- und Hygienezone in Hessen" | anonymisiert (bleibt) |

## 2. Logo-Beschaffung (Regeln, weiterhin gültig)

- Logos sind Marken der jeweiligen Unternehmen — automatisierter Download von
  Kunden-Websites bleibt vermieden. Stattdessen Text-Wordmarks im HSB-Stil (siehe oben).
- `pharma-hessen` bleibt `approvalStatus: "anonymous"` und zeigt entsprechend Test
  `tests/content.test.ts` weder Logo noch exakten Standort.
- Hersteller-/Maschinenlogos Dritter auf Projektfotos (z. B. Anlagenbauer) werden nicht
  beworben; Fotos mit prominentem Fremdlogo wurden bei der Bildauswahl aussortiert.

## 3. Projektfotos (eingebunden 2026-06-10)

Aus den 20 gelieferten Fotos wurden 6 ausgewählt, optimiert (WebP) und eingebunden:

| Datei (`public/media/hsb/projekte/`) | Motiv | Eingesetzt auf |
|---|---|---|
| `keramik-halle-rinnen.webp` | Helle Halle, Sechskant-Keramik, 2 Rinnenläufe | Startseite (Hauptpanel), Branche Lebensmittel |
| `hexagon-rinne-detail.webp` | Edelstahlrinne in Sechskant-Keramik (Detail) | Startseite (Entwässerung), Branche Molkerei |
| `beschichtete-halle.webp` | Frisch beschichtete Industriehalle | Startseite (Beschichtung & Sanierung) |
| `brauerei-tanks-keramik.webp` | Gärtanks auf Keramikboden | Branche Brauerei & Getränke |
| `saeulen-anschluss-keramik.webp` | Säulen-/Sockelanschluss in Keramik | Reserve (Detailseiten) |
| `verlegung-keramik.webp` | Verlegung in Ausführung | Reserve (Projektablauf/Karriere) |

Nicht verwendet: Maschinen-Nahaufnahmen ohne Bodenfokus, unterbelichtete Motive, Foto mit prominentem KLINGER-Fremdlogo.

## 4. Weitere Projektfotos (eingebunden 2026-06-10, dritte Iteration)

Aus der zweiten Foto-Lieferung wurden 6 weitere Motive ausgewählt, optimiert (WebP) und
eingebunden. Alle wurden vorab auf Fremdlogos/Markenkennzeichnungen geprüft – keines zeigt
lesbare Dritthersteller- oder Maschinenlogos:

| Datei (`public/media/hsb/projekte/`) | Motiv | Eingesetzt auf |
|---|---|---|
| `chemie-anlage-keramik.webp` | Anlage/Maschinenwand auf Sechskant-Keramikboden mit Rinne | Branche Chemieindustrie |
| `pharma-halle-keramik.webp` | Helle, leere Halle mit zwei Rinnenläufen, Sechskant-Mosaik | Branche Pharmaindustrie |
| `produktionsanlage-keramik.webp` | Produktionsanlage auf Sechskant-Keramikboden mit Rinne | Branche Backwaren/Großküche |
| `halle-doppelrinne-keramik.webp` | Helle Halle mit zwei parallelen Edelstahlrinnen, Sechskant-Mosaik | Referenzen-Galerie |
| `entwaesserungsrinne-detail.webp` | Detail: Edelstahlrinne mit Rost in Sechskant-Keramikfliesen | Referenzen-Galerie |
| `halle-in-ausfuehrung.webp` | Halle während Verlegung des Sechskant-Keramikbodens | Referenzen-Galerie |

Aus derselben Lieferung nicht verwendet: mehrere Duplikate/ähnliche Motive ohne zusätzlichen
Mehrwert sowie Aufnahmen mit sichtbarem KLINGER-Fremdlogo (`b40e0737-292221.jpg`,
`e9c2a13a-292227.jpg`). Zusätzlich enthielt die Lieferung mehrere Dateien, die keine
Projektfotos sind, sondern Screenshots eines unzusammenhängenden Social-Media-Beitrags
(Instagram, Account "leadgenman", Thema Claude-Code-Konfiguration) – diese wurden ignoriert
und nicht für die Website verwendet.
