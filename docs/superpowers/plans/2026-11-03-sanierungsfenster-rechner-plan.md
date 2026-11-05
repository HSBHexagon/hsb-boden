# Implementierungsplan: Sanierungsfenster-Rechner (Kloodt Asset 4)

Stand: 03.11.2026.
Ziel: Bereitstellung eines interaktiven Sanierungsfenster-Rechners auf der Website unter Berücksichtigung von Stillstandszeiten, Aushärtezeiten und Bauabschnittsberechnung (rein indikativ, ohne unbelegte Fakten).

---

## 1. Spezifikation & Komponenten
- **Komponente:** `apps/website/src/components/calculator/SanierungsRechner.astro`
  - Vanilla JS im `<script>`, barrierefrei, ohne Client-Framework-Ballast.
  - Eingabefelder: Hallenfläche ($m^2$), Zeitfenster / Schichtmodell (Wochenende 60 h, Betriebsurlaub 7–14 Tage, 24/7 Teilabschnitte), Systemtyp (PU-Beton, Rüttelkeramik AGI S 40, Schnellreparatur).
  - Dynamische Ausgabe: Anzahl Bauabschnitte, indikative Einbau- & Aushärtezeit, Übergabe ins Kontaktformular via URL-Parametern (`/kontakt/?area=...&sections=...`).
- **Landingpage:** `apps/website/src/pages/rechner/sanierungsfenster/index.astro`
  - Breadcrumb JSON-LD & WebPage Schema.
  - SEO Title: `Sanierungsfenster-Rechner | HSB Hexagon` (41 Zeichen <= 60).
  - Description: `Sanierungsfenster für Industrieböden berechnen: Hallenfläche, Schichtbetrieb und Aushärtezeiten indikativ auf Bauabschnitte planen.` (138 Zeichen <= 160).
- **Navigation & Verlinkung:**
  - Verlinkung in `src/lib/content.ts` (Sitemap & B2B-Meta-Audit).
  - Verlinkung im Beanspruchungs-Check und auf der Sanierungsseite (`/leistungen/bodensanierung-laufender-betrieb/`).

---

## 2. Aufgaben-Schritte
1. [x] **Plandatei anlegen** (`docs/superpowers/plans/2026-11-03-sanierungsfenster-rechner-plan.md`).
2. [x] **Astro-Komponente erstellen:** `apps/website/src/components/calculator/SanierungsRechner.astro`.
3. [x] **Landingpage erstellen:** `apps/website/src/pages/rechner/sanierungsfenster/index.astro`.
4. [x] **Content & Sitemap registrieren:** `apps/website/src/lib/content.ts` um die neue Route ergänzen.
5. [x] **Verlinkung in bestehenden Seiten:** Querverweis in `/beanspruchungs-check/` und `/leistungen/bodensanierung-laufender-betrieb/`.
6. [x] **Verifikation:** Vitest (`npm run test:run`), Build (`npm run build`), Sitemap-Check (`npm run check:sitemap`), Pytest (`pytest apps/sales-os/tests/ -q`), SSOT-Verifier (`scripts/verify_ssot.py`).
7. [ ] **Commit & Git-Push zum bestehenden PR #513.**
