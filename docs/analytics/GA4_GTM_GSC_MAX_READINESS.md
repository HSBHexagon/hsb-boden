# GA4_GTM_GSC_MAX_READINESS — HSB-Boden / HEXAFLOOR

Status: `ga4-basic-consent-cutover-in-pr; external-owner-verification-open`
Stand: 2026-07-15

Kanonische Detaildokumentation: `GA4_GSC_EVENT_TRACKING_READINESS.md`.

## Nachweisbarer Code-Stand

- Die GA4 Measurement ID ist im Quellcode vorhanden, aber die neue Basic-Consent-
  Implementierung ist noch nicht in `main` oder Produktion gemergt.
- `gtag.js` wird nach diesem Cutover ausschließlich nach aktiver Analytics-
  Einwilligung dynamisch geladen; kein externes Google-Skript vor Consent.
- Erfolgreiche Leads werden als `generate_lead` ohne personenbezogene Nutzdaten
  versendet; die Navigation wartet begrenzt auf den Event-Callback.
- Der lokale Gate-Lauf ist dokumentiert, ersetzt aber keine Browser- oder
  DebugView-Prüfung einer bereitgestellten Preview.

## Externe Owner-Gates

- Richtige GA4-Property und allfällige weitere Google-Destinations identifizieren.
- Preview in einem frischen Browserprofil vor/nach Einwilligung prüfen.
- `generate_lead` in DebugView belegen und erst dann als Key Event markieren.
- Die kanonische Search-Console-Property, Sitemap-Status und Indexierungsgründe
  im Owner-Konto prüfen; keine zweite Property erzeugen.
- Erst danach eine GA4/GSC-Verknüpfung setzen.

## Grenzen

Kein GTM-Container, keine Google-Property, keine Key Events und keine Search-
Console-Verknüpfung werden aus diesem Repository automatisiert angelegt. Diese
Dokumentation ist kein Ersatz für eine rechtliche Bewertung des Consent-Texts.
