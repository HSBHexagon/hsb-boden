# Referenzen-Freigabe & Logo-Liste (Arbeitsstand 2026-06-10)

> Ziel: „Alle Referenzen live schalten, die stimmen" + Kundenlogos einbinden.
> Non-Negotiable (AGENTS.md): Kein Kundenname, kein Logo, kein exakter Standort ohne dokumentierte Freigabe des Kunden. Das Datenmodell ist fertig — pro Referenz muss nur `approvalStatus`, `publicName` und ggf. `logo` in `src/data/references.ts` gesetzt werden.

## 1. Status der 6 Referenzen

| # | Interne ID | Aktuell öffentlich als | Status | Live-Schaltung mit Namen braucht |
|---|---|---|---|---|
| 1 | `suedzucker-zeitz` | **Südzucker AG** (Name + Logo + Standort Zeitz) | ✅ freigegeben (2026-06-06) | – erledigt, Logo liegt unter `/logos/suedzucker.svg` |
| 2 | `molkerei-sued` | „Molkereiproduktion in Süddeutschland" | anonymisiert | Echten Firmennamen + schriftliche Freigabe + Logo-Datei |
| 3 | `mineralbrunnen-schwarzwald` | „Getränkeproduktion im Südwesten" | anonymisiert | Echten Firmennamen + schriftliche Freigabe + Logo-Datei |
| 4 | `chemie-region-west` | „Chemischer Produktionsbetrieb in NRW" | anonymisiert | Echten Firmennamen + schriftliche Freigabe + Logo-Datei |
| 5 | `feinkost-nrw` | „Feinkostproduktion in NRW" | anonymisiert | Echten Firmennamen + schriftliche Freigabe + Logo-Datei |
| 6 | `pharma-hessen` | „Pharma- und Hygienezone in Hessen" | anonymisiert | Echten Firmennamen + schriftliche Freigabe + Logo-Datei |

**Was du pro Referenz liefern musst (dann schalte ich sie namentlich live):**
1. Echter Firmenname (die aktuellen `publicName`-Werte 2–6 sind Platzhalter).
2. Freigabe-Nachweis (E-Mail oder Vertragspassus des Kunden: Namensnennung ja/nein, Logo ja/nein, Standort ja/nein).
3. Logo-Datei (SVG bevorzugt, sonst PNG mit transparentem Hintergrund, min. 300 px Breite) → wird unter `public/logos/<id>.svg` abgelegt.

## 2. Logo-Beschaffung (Regeln)

- Logos sind Marken der jeweiligen Unternehmen — Einbindung **nur** mit Freigabe aus Punkt 1.2 (kein Download von der Kunden-Website ohne Erlaubnis).
- Bereits referenzierte Logo-Pfade in `references.ts` (`molkerei-sued.svg`, `mineralbrunnen.svg`, `chemie-west.svg`, `feinkost.svg`, `pharma.svg`) sind Platzhalter; die Dateien existieren bewusst nicht und werden bei `approvalStatus: "anonymous"` nie gerendert (abgesichert durch Test `tests/content.test.ts`).
- Hersteller-/Maschinenlogos Dritter auf Projektfotos (z. B. Anlagenbauer) werden nicht beworben; Fotos mit prominentem Fremdlogo wurden bei der Bildauswahl aussortiert.

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
