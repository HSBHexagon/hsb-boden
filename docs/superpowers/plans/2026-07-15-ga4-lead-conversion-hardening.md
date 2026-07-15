# GA4 Lead Conversion Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Den erfolgreichen Website-Lead als kanonisches GA4-Event `generate_lead` ohne personenbezogene Parameter senden und den Event-Transport vor dem Redirect begrenzt abschließen.

**Architecture:** Das bestehende Consent Mode v2 bleibt unverändert. `tracking.ts` erhält eine zentrale Payload-Bereinigung sowie eine Promise-basierte Conversion-Funktion mit GA4-Callback und Timeout. Das Lead-Formular ruft diese Funktion ausschließlich nach erfolgreicher `/api/lead`-Antwort auf.

**Tech Stack:** TypeScript, Astro, Vitest, bestehende direkte gtag.js-Integration.

## Constraints

- Kein GA4-Dashboard-, GTM-, Cloudflare-, DNS- oder Secret-Zugriff.
- Keine personenbezogenen Daten in Eventparametern.
- Kein Conversion-Event bei Validierungs-, Netzwerk- oder API-Fehler.
- Tracking darf Formularzustellung und Redirect nicht dauerhaft blockieren.
- Kein Merge oder Production-Deploy.

## Tasks

### 1. Test-first Analytics-Vertrag

- Create `tests/analytics-consent-hardening.test.ts`.
- Verifiziere `generate_lead` als kanonischen Eventnamen.
- Verifiziere Entfernung bekannter PII-Schlüssel und offensichtlich personenbezogener Stringwerte.
- Verifiziere Callback plus Timeout für Conversion-Transport.
- Verifiziere `await trackConversion(...)` nur nach erfolgreichem `/api/lead`.
- Verifiziere weiterhin Consent-Default `denied`.

### 2. Tracking-Härtung

- Ergänze `sanitizeTrackingPayload` in `src/lib/tracking.ts`.
- Nutze bereinigte Payloads in allen Tracking-Aufrufen.
- Ergänze `trackConversion` mit `event_callback` und `event_timeout`.
- Benenne den Lead-Erfolg in `GenerateLead = "generate_lead"` um.

### 3. Formularintegration

- Importiere `trackConversion`.
- Rufe `await trackConversion(TrackingEvent.GenerateLead)` nach `res.ok` auf.
- Leite erst danach auf `/danke-projektanfrage/` weiter.

### 4. Verifikation

- CI, Quality Assurance, Security, Lighthouse und Deploy Preview müssen grün sein.
- Externe GA4-Key-Event-Aktivierung und DebugView-Prüfung bleiben Owner-Gates.
