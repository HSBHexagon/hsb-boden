# RECOVERY_EXECUTION_PLAN.md

Priorisierung nach Geschäftsnutzen und Engpass-Beseitigung.

## P0: KRITISCH - UX & Conversion (Mobile)
**Ziel:** Website auf Mobilgeräten nutzbar machen, trotz rechtlicher Banner.
1.  **Layout-Fix Banner:**
    *   `LanguageSuggest.astro` von Block-Element auf kompaktes Overlay oder priorisierte Anzeige umstellen (z.B. Sprachhinweis erst nach Cookie-Entscheidung oder umgekehrt).
    *   Kompaktere Buttons für `CookieConsent` auf Mobile (nebeneinander statt gestapelt).
    *   **Erfolgskriterium:** H1 und mindestens ein CTA-Button auf einem 390px Viewport sichtbar, wenn Banner aktiv sind.

## P1: HOCH - Lead-Infrastruktur
**Ziel:** Anfragen technisch empfangen können.
1.  **n8n / Endpoint Konfiguration:**
    *   Entscheidung über n8n-Hosting (Cloud vs. lokal/Wrangler-Proxy).
    *   Webhook-URL in `.env` (lokal) hinterlegen und `leadEndpoint` verifizieren.
    *   SMTP-Integration für Bestätigungs-Mails vorbereiten.
2.  **Testlauf:** Test-Lead absenden und Empfang in n8n/E-Mail bestätigen.

## P2: MITTEL - Rechtliche Absicherung
**Ziel:** Haftungsrisiken minimieren.
1.  **Review Rechtstexte:**
    *   Impressum und Datenschutz final prüfen lassen (extern/User).
    *   Opt-in-Logik für Kaltakquise-System (n8n-Filter) implementieren.

## P3: NIEDRIG - Repository-Hygiene
**Ziel:** Sauberer Stand für künftige Wartung.
1.  **Merge PR #5:** Sobald P0-Fixes im Branch sind, PR #5 finalisieren und in `main` mergen.
2.  **Sync `hsb-boden`:** Haupt-Projektordner auf den Stand von `hsb-boden-review` bringen.

---
**Nächster empfohlener Schritt:**
Start mit **P0 (Banner-Stacking Fix)**. Dies ist eine rein lokale Code-Änderung in `src/components/layout/`, die sofort den größten Hebel auf die Conversion-Rate hat, ohne auf externe Zugänge (SMTP/n8n) warten zu müssen.
