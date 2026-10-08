# HEXAFLOOR / HSB — SEO-Umsetzung und technisches Claims-Audit

Stand: 2026-10-08. Branch `feat/seo-regions-claims-quality-20261008`, PR #447 (inkl. noch ungemergtem PR #446). **Keine Produktionsfreigabe und kein Production-Deploy erfolgt.**

## Ausgeführte Änderungen

1. **Neun regionale Seiten**: Technische Entscheidungsfragen nach Einsatzbedingungen statt nahezu identischer geografischer Textblöcke; je drei Links zu existierenden Leistungen, zwei zu Branchen und einer zu einem relevanten Wissensartikel. Zentrale Angabe des Unternehmenssitzes Gronau; keine erfundenen lokalen Niederlassungen oder regionale Kundenprojekte. Die Branchenseiten behalten eigene kanonische URLs, regionale Metadaten wurden mit der `getAllPublicPages` Registry synchronisiert. Vorheriger PR #446 liefert einheitliches `Service`-Schema; die neue Phase ergänzt Breadcrumbs.
2. **Normen und Produktclaims**: Fälschliche DIN-EN-14411-Zuordnung zum Rüttelverfahren korrigiert. Die Norm betrifft keramische Fliesen/Platten als **Produkte**. Temperaturbeständigkeit, Aushärte-/Befahrbarkeit, pH-Bereiche, Nutzungsdauer, Rutschhemmung und chemische Resistenz müssen je nach gewähltem Produkt und Einsatzprofil nachgewiesen werden.
3. **WHG/AwSV**: § 62 WHG betrifft Anlagenanforderungen; die Zertifizierung von Fachbetrieben ist in § 62 AwSV geregelt, Fachbetriebspflichten in § 45 AwSV. Daher keine generische DIBt- oder Dichtheitsgarantie für jede chemisch belastete Fläche. Das aus den Bestandsdaten stammende Fachbetriebs-Credential ist als Eigentümerangabe übernommen, die Urkunde wurde hier **nicht extern geprüft**.
4. **Leistung/Branche**: Sechs gezielte technische Checklisten (Keramik, PU-Beton, WHG, Molkerei, Brauerei/Getränke, Chemie), in vorhandene SEO-Seitentemplates eingebunden. Keine neuen Thin-Content-URLs oder Kundenbehauptungen.
5. **Wissensartikel**: Ursprünglich 558 Zeilen umfassendes Artikelmodul in zwei Module unter jeweils 500 Zeilen aufgeteilt. 18 problematische technische Artikelabschnitte angepasst; drei frühere unbewiesene `Praxisbeispiele` werden ausdrücklich als hypothetische Szenarien dargestellt. Artikel-URLs und Gesamtmenge unverändert.
6. **Tests und CI**: Tests für Regionseinzigartigkeit, interne Links, Breadcrumb/Metadaten, Normen, Artikelintegrität, Sitemap, Lighthouse-Zielseiten und LCP/CLS/TBT-Lab-Warnschwellen. Quality-Workflow prüft SSOT-Skript, Typen, Build, Sitemap, Tests, Pages-Dry-Run. Preview- und manuelles Production-Workflow ergänzen Sitemap-Prüfung; `workflow_dispatch`-Produktion bleibt unverändert.

## Beweislage / Einschränkungen

- Firecrawl hatte am 08.10.2026 unter `www.hsb-boden.de` neun regionale SEO-Seiten in einem URL-Inventar mit 57 gefundenen URLs. URLs im Crawlinventar sind **nicht** automatisch Google-indexiert.
- Das ursprüngliche regional vorhandene LocalBusiness-Markup und eine falsche NRW-Telefonnummer wurden in PR #446 bereits in der Preview beseitigt.
- Cloudflare Preview und GitHub Actions sind autoritative Prüfsysteme für diese Branch-Änderungen. Vor dem Livegang Endstatus sämtlicher Checks und HTTP 200 für reale Preview-Userpfade abgleichen. Eine erfolgreiche CI gibt keine Berechtigung für automatisch produktive Änderungen.
- **Offene Beweismittel:** Zugriff auf Google Search Console für Indexierung, Impressionen, CTR und Ranking; CrUX-Felddaten für LCP/INP/CLS; Freigabedokumente zu Fachbetrieb, technischen Systemen und kundenspezifischen Bildern/Namen. Ohne diese Nachweise keine Steigerung von Suchtraffic oder Rich Results behaupten.
- Weitere Aussagen in nicht überarbeiteten Artikeln, Fotos und internationalen Sprachversionen erfordern eine **separate** Fachprüfung. Das jetzige Audit ist zielgerichtet, nicht rechtsverbindlich oder vollständig über jedes technische Produkt.

## Fachquellen

- Google Search Central: https://developers.google.com/search/docs/essentials/spam-policies
- Google hilfreiche Inhalte: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google strukturierte Daten: https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- DIN EN 14411: https://www.dinmedia.de/de/norm/din-en-14411/256449026
- Wasserhaushaltsgesetz § 62: https://www.gesetze-im-internet.de/whg_2009/__62.html
- AwSV § 62: https://www.gesetze-im-internet.de/awsv/__62.html
- Lighthouse CI assertions: https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md

## Release-Gate

- PR #447 ist Draft und umfasst die vorherigen PR-#446-Änderungen. **Keinen doppelten Merge**, sondern den final genehmigten Gesamtumfang übernehmen.
- Nur nach grünem CI, QA, Security, Lighthouse, erfolgreicher Preview-Validierung, expliziter fachlicher Freigabe und manueller Freigabe über `deploy-production.yml` veröffentlichen. Keine Änderung an CRM/Outreach oder MX/DNS.
