# Phase 0 — Project Reality Audit: Master Status Matrix

Stand: 2026-06-10 (nach Commit `219b050`, Branch `claude/hsb-boden-architecture-o2479f`, PR #5 draft).
Protokoll: `docs/superpowers/plans/2026-06-10-master-execution-plan-v2.md`.
Keine Änderungen in dieser Phase — nur konsolidierte Bestandsaufnahme.

## Master Status Matrix

| Bereich | Status | Risiko | Potenzial |
|---|---|---|---|
| **Repository/Branches** | Sauber. `main` + Arbeitsbranch `claude/hsb-boden-architecture-o2479f` (PR #5 draft, offen). PR #2 (Worker-Umbenennung → Produktion) bewusst NICHT gemerged. | Niedrig. Einzige Gefahr: versehentlicher Merge von PR #2 → Sperre beachten. | PR #5 ist der vollständige Arbeitsstand; nach Freigabe einfacher Merge. |
| **Build/Tests/Gates** | `npm run check` 0/0/0 (65 Dateien), `test:run` 9/9 grün, Build erfolgreich. Tests erzwingen Referenz-Freigabelogik (anonyme Referenzen nie mit Logo/Klarname/Standort). | Niedrig. | Gate-Disziplin etabliert; CI-fähig. |
| **Seitenstruktur** | Vollständig: Start, 6 Branchen, 8 Leistungen, 5 Wissen-Artikel, Referenzen, Kontakt, Karriere, Impressum, Datenschutz, 5 Sprachvarianten (en/fr/nl/pl/tr), Sitemap/robots dynamisch. | Niedrig. | Solide SEO-Landingpage-Basis (≥22 indexierbare Seiten). |
| **Referenzen** | 5 von 6 mit Klarnamen live (Südzucker, Gropper, Peterstaler, Concept Color, Dahlhoff), Wordmark-Logos; `pharma-hessen` anonym (kein Listen-Treffer). 21 weitere Kundenstandorte auf Deutschlandkarte (Name/Ort/Branche, ohne Fallstudie). Freigabe dokumentiert in `referenzen-freigabe.md` §0. | Mittel: Wordmarks statt echter Markenlogos (bewusst, markenrechtlich sicher); Fallstudientexte branchentypisch formuliert statt firmenspezifisch (SEO-Reviewer-Auflage erfüllt). | Echte Logos nachrüsten sobald Kunde liefert; NL-Standorte später ergänzbar; Fallstudien je Kunde vertiefbar nach Einzelverifikation. |
| **Medienbestand** | 12 von 33 gelieferten Fotos verwendet (6+6, WebP-optimiert), dokumentiert in `referenzen-freigabe.md` §3+§4. Aussortiert: 2× KLINGER-Fremdlogo, 7-9× fremde Instagram-Screenshots, Rest Duplikate/ohne Bodenfokus. Keine Videos vorhanden. | Niedrig. Lücke: Leistungsseiten haben keinen Bildslot. | Bildslot für Leistungen bei neuer Fotolieferung; Videomaterial fehlt komplett (Phase 3). |
| **SEO On-Page** | seoTitles/descriptions einzigartig u. valide (Zod-erzwungen), H1-Struktur sauber, JSON-LD (Organization, LocalBusiness, FAQ, Breadcrumb, Service), Canonicals + hreflang korrekt. | Niedrig–Mittel: OG-Image nur 322×237-Logo (Soll: 1200×630); Hero ohne `srcset`; „5 Kunden, bundesweit"-Stat in ReferenceMapPreview (belegbar durch Freigabeliste, aber zählsensibel). | OG-Asset erstellen; srcset/sizes für Hero+Galerien; interne Verlinkung ausbauen (s. u.). |
| **Interne Verlinkung** | Branchen→Leistungen vollständig (relatedServices). LÜCKEN: Leistungen zeigen `relatedIndustries` nicht an (Datenfeld existiert, Template ignoriert es); Wissen-Artikel sind isoliert (keine related-Felder, nirgends aus Branchen/Leistungen verlinkt). | Mittel (SEO-Authority-Verlust). | Quick Win: relatedIndustries-Widget + Wissen-Cross-Links — größter SEO-Hebel mit kleinstem Aufwand. |
| **Wissen/Authority** | 5 Artikel strukturell gut (Titel, Sections, FAQs), aber Fließtext je Section dünn/skeletthaft. Themenlücken ggü. Phase-4-Soll: CIP, HACCP, Chemikalienbeständigkeitstabellen, Großküche vertieft. | Mittel: Thin Content schwächt Autoritäts-/Rankingziel. | Phase 4: Artikel vertiefen + 3–5 neue Themen; FAQ-System aus Suchintentionen ausbauen. |
| **Design/Mobile** | Tailwind-basiert, konsistente Komponenten; Hero `fetchpriority="high"` korrekt; Galerien mit lazy-loading. Mobile-Audit (360/390/430px) noch NICHT systematisch durchgeführt. | Mittel (unverifiziert ≠ schlecht). | Phase 2: Screenshot-Matrix + Lighthouse; CTA-Hierarchie-Review. |
| **Formular/Lead-Engine** | Formular mit Validierung, Honeypot, Branchen-Dropdown, Danke-Seite. Webhook-Endpunkt vorhanden. SMTP NICHT konfiguriert → kein Mailversand; n8n nur lokal, Workflows nicht publiziert, Opt-in-Blocker (P0) unimplementiert. | HOCH (für Akquise-Ziel): Leads laufen aktuell ins Leere ohne SMTP/n8n. Benötigt User-Input (Zugänge, Hosting-Entscheidung). | Phase 7: Fehlerpfade/Monitoring konzipieren; sofort umsetzbar sobald Zugänge vorliegen. |
| **CRM/E-Mail** | Nur Konzept (`2026-06-07-hsb-lead-pipeline.md`, HEXAFLOOR-Abgleich §Phase 3/4): Google-Sheets-CRM-Light, Statusmodell definiert. Nichts implementiert. Kaltmail an 5.000 Leads bleibt gesperrt bis Opt-in-Blocker + juristische Freigabe. | HOCH (rechtlich, falls vorzeitig versendet) — Sperre aktiv. | Phase 8: Templates/Strukturen risikofrei vorbereitbar. |
| **Flyer/Kampagne** | Vorhandener Projektflyer noch nicht im Repo/auditiert. | Mittel: Flyer könnte veraltete Referenzen/Marken zeigen. | Phase 9: an neue Referenz-/Logo-Lage angleichen. |
| **Analytics** | GA4/Search Console nicht eingerichtet (User-Input: GA4-ID). Kein Event-Tracking. | Mittel: Ohne Messung kein KPI-Nachweis ab Tag 1. | Phase 10: Messkonzept jetzt dokumentierbar, Einbau bei ID-Lieferung trivial. |
| **Cloudflare** | Worker `hsb-boden-preview` + Auto-Deploy des Branches (Branch-Preview-URLs funktionieren, Deploy ✅ für `219b050`). Caching/Security-Header/Monitoring noch nicht auditiert. | Niedrig–Mittel. | Phase 6: Header-Härtung, Cache-Regeln, Image Delivery. |
| **Rechtliches** | Impressum/Datenschutz als Entwurf; juristische Prüfung offen (extern). Cookie-Banner + 6-Sprachen-Consent vorhanden. | HOCH vor Go-Live (Blocker), kein Risiko im Preview. | Nach juristischer Freigabe nur Textabnahme nötig. |
| **Wettbewerb** | Keine Analyse vorhanden. | — | Phase 1: Gap-Report ggü. Steuler, Sika/Ucrete, Remmers, StoCretec, ARDEX, Korodur. |
| **Go-Live-Sperre** | Aktiv und eingehalten: PR #2 unmerged, kein DNS/Produktions-Touch. | — | Phase 11/12 erst nach allen Gates. |

## Konsolidierte Prioritätenliste (für Phase 1 ff., nach Hebel sortiert)

1. **Interne Verlinkung** (Leistungen→Branchen-Widget, Wissen-Cross-Links) — kleinster Aufwand, größter SEO-Hebel.
2. **OG-Image 1200×630 + srcset für Hero/Galerien** — Social-/Performance-Quick-Win.
3. **Mobile-/Design-/Lighthouse-Audit** (Phase 2) — Verifikation vor weiterer Design-Politur.
4. **Wettbewerbsanalyse** (Phase 1) — bestimmt Content-Prioritäten für Phase 4.
5. **Wissen-Vertiefung + FAQ-System** (Phase 4) — Autoritätsaufbau, größter Content-Hebel.
6. **Cloudflare-Härtung** (Phase 6) — produktionsreif ohne Cutover.
7. **Lead-/CRM-/E-Mail-/Analytics-Vorbereitung** (Phasen 7–10) — soweit ohne externe Zugänge möglich; Rest wartet auf User-Inputs (SMTP, GA4-ID, n8n-Hosting, juristische Prüfung).

## Offene User-Inputs (außerhalb Repo, blockieren jeweilige Phasen)

- SMTP-Zugangsdaten (Phase 7) · GA4-ID (Phase 10) · n8n-Hosting-Entscheidung (Phase 7/8)
- Juristische Prüfung Impressum/Datenschutz/Kaltakquise (Phase 8/11)
- Echte Kundenlogos als Dateien (Phase 3, optional) · Projektflyer-Quelldatei (Phase 9)
- Videomaterial, falls vorhanden (Phase 3)
