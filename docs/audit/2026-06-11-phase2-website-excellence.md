# Phase 2 — Website Excellence: Pflicht-Gate-Report

Stand: 2026-06-11. Protokoll: `2026-06-10-master-execution-plan-v2.md`.
Branch `claude/hsb-boden-architecture-o2479f`, Commit `8702008`.

## 1. Analyse

- Visuelles Audit per Playwright (Chromium, lokal über `/opt/pw-browsers/chromium-1194`)
  gegen die Branch-Preview-URL: 7 Seiten (Start, `/branchen/molkerei/`,
  `/leistungen/.../`, `/wissen/.../`, `/referenzen/`, `/kontakt/`, `/en/`) ×
  5 Breakpoints (360/390/430/Tablet/Desktop) = 35 Screenshots.
- Technische Lücken aus Phase 0 verifiziert:
  - `relatedIndustries` in `src/data/services.ts` existierte für alle 8
    Leistungen, wurde aber von `leistungen/[slug].astro` nicht gerendert.
  - Wissen-Artikel (`src/data/articles.ts`) waren isoliert: keine Cross-Links
    zu/von Branchen oder Leistungen.
  - Hero-Bild (`index.astro`) hatte `fetchpriority="high"`, aber kein
    `srcset`/`sizes`.
  - OG-Image (`SEOHead.astro`) zeigte das 322×237-Logo statt eines
    1200×630-Bildes.
- Neuer Befund (mobiles Audit, `home-fold`/`referenzen-fold` bei 390px):
  Das Cookie-Consent-Banner (`CookieConsent.astro`) nimmt auf Mobilgeräten
  beim ersten Laden ca. 45–50 % der Viewport-Höhe ein und verdeckt CTA-Buttons
  und Teile der H1. Funktional korrekt (DSGVO-Banner, schließt nach Auswahl),
  aber Conversion-relevant für Erstbesucher auf Mobilgeräten.
- Playwright-Setup repariert: `npm install -D playwright@1.60.0` installiert,
  aber `/opt/pw-browsers/` enthält nur Chromium-Build 1194 (nicht das von
  1.60.0 erwartete 1223). Workaround: `executablePath` explizit auf
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` gesetzt + Flags
  `--disable-quic --disable-features=EncryptedClientHello
  --ignore-certificate-errors` (Sandbox-Netzwerk benötigt das für TLS zur
  Cloudflare-Preview-URL). Funktioniert zuverlässig für künftige Audits.

## 2. Änderungen (Commit `8702008`)

1. **Interne Verlinkung (größter SEO-Hebel aus Phase 0/1):**
   - `src/lib/content.ts`: Schema um `relatedArticles` (Services/Industries)
     und `relatedServices`/`relatedIndustries` (Articles) erweitert.
   - `src/data/services.ts`, `src/data/industries.ts`, `src/data/articles.ts`:
     Cross-Reference-Felder mit thematisch passenden Slugs befüllt (alle
     bestehend, keine neuen Inhalte/Claims).
   - `src/pages/leistungen/[slug].astro`: neue Sektion „Für welche Branchen
     relevant" (rendert `relatedIndustries`).
   - `src/pages/branchen/[slug].astro` + `leistungen/[slug].astro`: neue
     Sektion „Fachwissen zu dieser Branche" / „Vertiefendes Fachwissen"
     (rendert `relatedArticles`).
   - `src/pages/wissen/[slug].astro`: neue Sektion „Passende Leistungen und
     Branchen" (rendert `relatedServices`/`relatedIndustries`).
2. **OG-Image (Quick Win, Phase 0 #2):** `public/brand/og-image.png`
   (1200×630, per sharp aus Logo + Brand-Farben/Hexagon-Pattern generiert,
   keine Stock-/Fremdbilder). `SEOHead.astro` referenziert es jetzt + setzt
   `og:image:width`/`og:image:height`.
3. **Hero-srcset (Quick Win, Phase 0 #2):** `public/media/hsb/current/
   industrieboden-baustelle-640.webp` (640px-Variante, 18 KB) erzeugt;
   `index.astro` Hero-`<img>` hat jetzt `srcset`/`sizes`.
4. **P1 — Positionierung „aus einer Hand"** (Competitive Gap Report): neue
   Sektion direkt unter dem Hero auf der Startseite, H2 „Planung und
   Ausführung aus einer Hand" + Lead-Text (Single-Point-of-Contact-Framing,
   differenziert von der Hero-Systembotschaft).
5. **P2 — Referenzkarte als USP**: `ReferenceMapPreview.astro` Eyebrow zu
   „Projektkarte Deutschland" geändert + ergänzender Satz zur
   bundesweiten Kunden-/Projektkarte (Formulierung nach Reviewer-Hinweis
   präzisiert: „Kunden und Projektstandorte" statt pauschal „umgesetzt").
6. **P5 — CTA geschärft**: `CTASection.astro` Default-Title/Label von
   „Kostenlose Ersteinschätzung vor Ort" / „Ersteinschätzung anfordern" zu
   „Werksbegehung oder technische Bodenanalyse anfragen" / „Werksbegehung
   anfragen" (wirkt auf Start-, Branchen-/Leistungs-/Wissen-Übersichten,
   Referenzen, Danke-Seite). `wissen/[slug].astro` PageHero-CTA auf
   „Werksbegehung anfragen" angeglichen (Konsistenz-Hinweis Reviewer).
7. `playwright@1.60.0` als devDependency ergänzt (für künftige
   Mobile-/Visual-Audits).

## 3. Verifikation

- `npm run check`: 0 Fehler / 0 Warnungen / 0 Hinweise (65 Dateien).
- `npm run test:run`: 9/9 Tests grün.
- `npm run build`: erfolgreich, alle Branchen-/Leistungen-/Wissen-Seiten
  inkl. neuer Cross-Link-Sektionen gebaut.
- `seo-content-reviewer`: **PASS** (2 Warnungen behoben — Referenzkarten-Text
  präzisiert, Wissen-CTA-Label vereinheitlicht).
- Lokaler Visual-Check (Playwright, Desktop 1440px) für Startseite,
  `/leistungen/keramische-industrieboeden/`,
  `/wissen/warum-industrieboeden-in-molkereien-versagen/`: neue Sektionen
  rendern korrekt, keine Layoutbrüche.
- Commit `8702008` gepusht auf `claude/hsb-boden-architecture-o2479f`
  (PR #5 aktualisiert sich automatisch über Cloudflare-Webhook).

## 4. Risiken

- **Mobiles Cookie-Banner (neu identifiziert, NICHT behoben):** verdeckt auf
  390px-Breite ca. die Hälfte des ersten Bildschirms inkl. CTA-Buttons.
  Rechtlich korrekt, aber conversion-kritisch. Eine Änderung am
  Consent-Banner berührt DSGVO-Mechanik — bewusst nicht in diesem Schritt
  angefasst (Risiko einer fehlerhaften Consent-Logik > Nutzen einer
  optischen Verkleinerung ohne Rechtsprüfung).
- Lighthouse-Audit (Performance/SEO/Accessibility/Best-Practices) wurde in
  dieser Phase **nicht** durchgeführt (Tool nicht im Projekt vorhanden,
  Playwright-Reparatur hat den Zeitrahmen dieser Phase ausgeschöpft).
- `playwright`-devDependency erhöht `node_modules`-Größe geringfügig; kein
  Einfluss auf Produktion-Build (nur devDependency).
- Neue og-image.png (101 KB) wird nur von Social-Crawlern geladen, nicht von
  normalen Besuchern — keine Performance-Auswirkung auf reguläre Seiten.

## 5. Empfehlungen

1. **Mobiles Cookie-Banner kompakter gestalten** (z. B. einzeiliger Text +
   Buttons nebeneinander statt gestapelt) — als eigener, isolierter
   Folge-Schritt mit Fokus auf DSGVO-Konformität, idealerweise mit
   Vorher/Nachher-Screenshot-Vergleich.
2. **Lighthouse-Audit nachholen** (jetzt, da Playwright/Chromium lauffähig
   ist): `npx lighthouse <preview-url> --chrome-flags="--headless
   --disable-quic --disable-features=EncryptedClientHello
   --ignore-certificate-errors" --output=json` für Start, eine Branchen- und
   `/referenzen/`-Seite.
3. Verbleibende Punkte aus der Konsolidierten Prioritätenliste (Phase 0):
   Wissen-Vertiefung + FAQ-System (Phase 4), Cloudflare-Härtung (Phase 6).
4. Die übrigen Chancen aus dem Competitive Gap Report (P3 Zertifikate, P4
   Ansprechpartner, P9 weitere Logos) bleiben durch fehlende User-Inputs
   blockiert (siehe Master-Status-Matrix).

## 6. Nächster Schritt

Gemäß Pflicht-Gate: **Stopp.** Warten auf Freigabe des Nutzers für Phase 3
(Referenzen/Logos/Medien) oder für einen gezielten Folge-Schritt zum mobilen
Cookie-Banner / Lighthouse-Audit.
