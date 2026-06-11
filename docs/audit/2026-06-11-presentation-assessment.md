# Beurteilung der Darstellung — Stand nach Phase 2

Stand: 2026-06-11. Branch `claude/hsb-boden-architecture-o2479f`, Commit `8b19c48`.
Grundlage: visuelles Re-Audit (Playwright, Desktop 1440px / Mobile 390px) gegen
die Branch-Preview-URL für Start, `/branchen/molkerei/`,
`/leistungen/keramische-industrieboeden/`,
`/wissen/warum-industrieboeden-in-molkereien-versagen/`, `/referenzen/`, `/kontakt/`.

Bewertung je Aspekt: ✅ erfolgreich umgesetzt · ⚠️ teilweise/Beobachtung · ❌ offen/Risiko.

## 1. Startseite — Hero & Erstkontakt

✅ Headline, Subline und Bildbeweis (Baustellenfoto) wirken hochwertig und
klar positioniert. `srcset`/`sizes` für das Hero-Bild ist implementiert
(640w/1024w), `fetchpriority="high"` korrekt gesetzt.
✅ Die 4 Themenkacheln rechts ("Lebensmittelproduktion", "Molkerei & Brauerei",
"Chemie & Pharma", "Sanierung im Betrieb") geben sofort Branchenüberblick.
❌ **Banner-Stacking überlagert den Hero auf Mobile fast vollständig** (siehe
Abschnitt 12) — größter offener Punkt.

## 2. Positionierung „aus einer Hand" (P1)

✅ Neue Sektion direkt unter dem Hero ("Planung und Ausführung aus einer Hand")
ist sauber von der Hero-Botschaft abgegrenzt (Single-Point-of-Contact-Framing
vs. technisches System-Framing im Hero). Die 3-Spalten-Struktur
(Analyse vor Ort / System, nicht Produkt / Sanierung planbar) ist auf Desktop
und Mobile gut lesbar, keine Layoutbrüche.

## 3. Schmerzpunkte-Sektion ("Vier Ursachen, die … auftreten")

✅ Rendert korrekt auf Dunkel-Hintergrund, nummerierte Karten (01–04) mit
„Folge"-Hervorhebung in Rot — guter Kontrast, gute Lesbarkeit auf Mobile.

## 4. Branchen-Übersicht & Branchenseiten

✅ Branchen-Grid auf der Startseite ("Jede Produktion hat ein anderes
Belastungsprofil") zeigt alle 6 Branchen mit klaren CTAs.
✅ Branchenseite (`/branchen/molkerei/`): Hero, Referenzfoto, „Was Entscheider
hier wirklich suchen", „Empfohlene Leistungsbereiche", „Projektbeispiele aus
ähnlichen Bereichen" — alles vorhanden und stimmig.
✅ **Neu: „Fachwissen zu dieser Branche"** rendert zwei thematisch passende
Wissen-Artikel (Molkerei → „Warum Industrieböden in Molkereien versagen" +
„Entwässerung und Gefälle in Produktionsbereichen") — Karten mit Eyebrow,
Titel, Teaser, korrektes Layout.

## 5. Leistungsseiten + neue Cross-Link-Sektionen

✅ `/leistungen/keramische-industrieboeden/`: „Warum diese Leistung relevant
ist", Systemlösung/Anforderungen-Boxen, Vorteile/Entscheidungskriterien —
alles wie zuvor stimmig.
✅ **Neu: „Für welche Branchen relevant"** zeigt 3 passende Branchen
(Lebensmittelindustrie, Molkerei, Brauerei & Getränkeindustrie) mit
`searchIntent`-Text — fügt sich optisch nahtlos zwischen
Hersteller-Block und Projektbeispielen ein.
✅ **Neu: „Vertiefendes Fachwissen"** zeigt 3 passende Artikel
(PU-Beton vs. Keramik, Molkerei-Versagen, Säurefeste Fliesen) in
3-Spalten-Grid — saubere Eyebrow/Titel/Teaser-Struktur, konsistent mit
Branchenseiten-Pattern.
✅ FAQ-Akkordeon und finaler CTA-Block direkt darunter, keine Überschneidung
mit den neuen Sektionen.

## 6. Wissen-Artikel + Cross-Links

✅ `/wissen/warum-industrieboeden-in-molkereien-versagen/`: Artikeltext,
Abschnittsstruktur klar.
✅ **Neu: „Passende Leistungen und Branchen"** (Eyebrow „Weiterführend") zeigt
3 Leistungen + 1 Branche (Molkerei) als Karten — funktioniert, Links zeigen
auf die korrekten Slugs.
✅ PageHero-CTA jetzt konsistent „Werksbegehung anfragen" (vorher
„Ersteinschätzung anfordern" — Inkonsistenz behoben).

## 7. Referenzen / Projektkarte (P2)

✅ `/referenzen/`: Hero „Ausgeführte Industrieböden für produktionskritische
Bereiche", reale Bodenflächenfotos (kein Stock), Eyebrow „Reale Bodenflächen
statt Symbolbilder" — starke Differenzierung.
✅ Projektkarte ("Projektkarte Deutschland") mit 21 Kundenstandorten +
5 namentlichen Referenzkarten + anonymisierte Referenzen sauber getrennt
nach `approvalStatus`. Anonyme Referenzen zeigen korrekt **kein** Logo/Klarname/
Standort.
✅ Formulierung „zeigt … wo Hexagon Säurebau bundesweit Kunden und
Projektstandorte hat" vermeidet Übergeneralisierung gegenüber den reinen
Standort-Pins ohne Case-Study.

## 8. CTA-Sektionen (P5)

✅ Geschärfter Default-CTA „Werksbegehung oder technische Bodenanalyse
anfragen" / „Werksbegehung anfragen" rendert konsistent auf Start-,
Branchen-/Leistungen-/Wissen-Übersicht, Referenzen und Wissen-Detailseiten.
Wirkt konkreter als die vorherige „Kostenlose Ersteinschätzung"-Formulierung,
ohne neue Leistungsversprechen zu erfinden.

## 9. Kontaktformular (`/kontakt/`)

✅ Vollständiges Formular (Name, Firma, E-Mail, Telefon, Projekttyp, Branche,
Fläche, Zeitfenster, Belastungsarten als Checkboxen, Nachricht,
DSGVO-Einverständnis-Checkbox). Direktkontakt (Telefon/E-Mail) prominent über
dem Formular. Layout zweispaltig auf Desktop, sauber gestapelt auf Mobile.
⚠️ Auch hier überlagert das Banner-Stacking (Punkt 12) den Lead-Text direkt
unter der H1 — auf Desktop sichtbar überlappend mit „Je präziser …".

## 10. SEO-Metadaten / OG-Image

✅ `og-image.png` (1200×630, brandkonform aus Logo + Hexagon-Pattern generiert)
korrekt referenziert, `og:image:width`/`height` gesetzt — Social-Previews
zeigen jetzt ein vollformatiges Bild statt des kleinen Logos.

## 11. Footer & Navigation

✅ Footer konsistent auf allen geprüften Seiten: Leistungen-, Branchen-,
Unternehmen- und Rechtliches-Spalten identisch strukturiert, alle Links auf
gültige Routen. Hauptnavigation (inkl. Sprachumschalter DE/EN/FR/NL/PL/TR)
funktional.

## 12. ❌ Banner-Stacking: Cookie-Consent + Sprachhinweis (kritischster Befund)

Auf **jeder geprüften Seite** erscheinen beim ersten Laden zwei Overlays
übereinander:

1. Sprachhinweis-Banner „This page is in German. Would you like to view it in
   English? — View in English / Continue in German"
2. Cookie-Consent-Banner („Wir verwenden technisch notwendige Cookies …" mit
   „Einstellungen / Nur notwendige / Alle akzeptieren")

**Mobile (390px):** Beide Banner zusammen verdecken auf der Startseite ca.
60–70 % des ersten Bildschirms — H1 „Hygienische Industrieböden …" ist nur in
Fragmenten sichtbar, beide CTA-Buttons („Projekt anfragen“ /
„Referenzen ansehen“) sind komplett verdeckt.

**Desktop (1440px):** Geringere, aber sichtbare Überlappung mit dem
Lead-Text/CTA-Bereich direkt unter der H1 (z. B. `/kontakt/`,
`/leistungen/keramische-industrieboeden/`).

Dies ist die bereits in `2026-06-11-phase2-website-excellence.md` als Risiko
dokumentierte Cookie-Banner-Problematik — durch das zusätzlich sichtbare
Sprachhinweis-Banner jedoch **verschärft**: Erstbesucher aus dem
deutschsprachigen Raum sehen zwei Hinweis-Layer gleichzeitig, bevor sie
überhaupt den eigentlichen Seiteninhalt sehen.

Funktional sind beide Banner korrekt (DSGVO-Mechanik bzw. Spracherkennung
arbeiten wie vorgesehen) — es handelt sich um ein reines
Darstellungs-/Stacking-Problem, **nicht** in dieser Bewertung behoben
(berührt Consent-/i18n-Logik, siehe Leitplanken).

## 13. Gesamtfazit

Alle Phase-2-Maßnahmen (interne Verlinkung, OG-Image, Hero-`srcset`,
Positionierung „aus einer Hand", Projektkarte als USP, geschärfte CTAs) sind
**visuell verifiziert erfolgreich umgesetzt** und fügen sich konsistent in das
bestehende Designsystem ein — keine Layoutbrüche, keine Kontrastprobleme,
keine erfundenen Inhalte.

Der mit Abstand größte verbleibende Punkt mit direktem Conversion-Einfluss ist
das **Banner-Stacking (Cookie-Consent + Sprachhinweis)** auf allen Seiten,
besonders mobil. Empfehlung unverändert: als eigener, isolierter Folge-Schritt
mit Fokus auf Layout (z. B. kompaktere/einzeilige Darstellung, ggf.
nacheinander statt gleichzeitig anzeigen) und ohne Eingriff in die
zugrunde liegende Consent-/i18n-Logik — idealerweise mit
Vorher/Nachher-Screenshot-Vergleich.
