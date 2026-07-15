# SEO-, Accessibility- und Performance-Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bestehende technische Grundlagen ohne breite Content-Umschreibung härten: genau eine Search-Console-Verifikation, vollständige Social-Metadaten, zentrale Telefonnummern und ein abgesicherter LCP-Hero.

**Architecture:** Der PR verändert nur den globalen Head, die globale CTA-Komponente und statische Regressionstests. Bestehende Seitentexte, Bilder und Routing-Strukturen bleiben unverändert. Keine neue Dependency und keine Cloudflare-Konfiguration.

**Tech Stack:** Astro 6, TypeScript, Vitest, bestehende GitHub Actions und Cloudflare Pages Preview.

## Constraints

- Kein Merge oder Production-Deploy.
- Keine Änderungen an DNS, Secrets, Analytics, CRM oder n8n.
- Keine erfundenen Meta-Claims oder Keyword-Massentexte.
- Keine pauschalen Alt-Text-Umschreibungen ohne sichtbaren Bildinhalt.

## Tasks

### 1. Test-first Guardrails

- Create `tests/seo-accessibility-performance.test.ts`.
- Verifiziere genau eine Google-Verifikationsquelle.
- Verifiziere vollständige Open-Graph-/Twitter-Metadaten.
- Verifiziere zentrale Telefonnummer in `CTASection.astro`.
- Verifiziere das bestehende Homepage-LCP-Bild mit Dimensionen, `loading="eager"` und `fetchpriority="high"`.

### 2. Head-Härtung

- Entferne die zweite Verifikations-Meta aus `BaseLayout.astro`.
- Ergänze `og:image:alt`, Twitter-Titel, -Beschreibung und -Bild in `SEOHead.astro`.

### 3. Zentrale Telefonnummer

- Nutze `site.phone` in `CTASection.astro`.
- Leite `tel:` aus den zentralen Daten ab.
- Entferne die fest codierte Telefonnummer.

### 4. Verifikation

- CI, Quality Assurance, Security, Lighthouse und Deploy Preview müssen grün sein.
- PR bleibt ungemergt und Production unverändert.
