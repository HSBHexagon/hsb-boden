# Lead-UTM-Attribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Website-Leads werden kampagnen- und seitenbezogen attribuierbar (UTM + Referrer + Landingpage + Formularpfad), session-persistent, ohne die Zero-JS-Grundarchitektur oder den bestehenden Versand zu verändern.

**Architecture:** Eine kleine, pure Attributions-Bibliothek (`src/lib/attribution.ts`) erfasst und normalisiert UTM-Parameter, Referrer und Einstiegspfad; ein globales Layout-Script persistiert die Erst-Attribution in `sessionStorage`; das Lead-Formular liest sie beim Submit und legt sie in das bestehende Payload. Der Endpoint-Schema wird rückwärtskompatibel um optionale, längen-/zeichenbegrenzte Felder erweitert; der Pages-Function-Webhook leitet das validierte Objekt unverändert weiter.

**Tech Stack:** Astro (static), TypeScript, Zod, Vitest (jsdom). Keine neuen Dependencies.

## Global Constraints

- Keine neue Dependency, kein React, Zero-JS-Grundarchitektur des Formulars bleibt.
- Bestehendes Schema/CRM-Spalten zuerst wiederverwenden; neue Felder nur optional (rückwärtskompatibel).
- Keine PII in Analytics; keine freien Referrer-/URL-Strings ungeprüft übernehmen; Werte in Länge (UTM ≤ 100, Pfade/Referrer ≤ 200) und Zeichensatz begrenzen.
- Blockierter/fehlender `sessionStorage` darf den Versand nie verhindern; Leads ohne UTM bleiben gültig.
- `source: "website"` bleibt unverändert; Priorität: aktuelle UTMs → Session-Attribution → Referrer → `direct`.
- Kein Push auf `main`, kein Production-Deploy, kein CRM-Sheet-Umbau (neue Spalten = Connector-Gate).

## Datenflusskette (Ist)

1. `src/components/forms/LeadForm.astro` (Inline-Script) baut Payload mit statischem `source: "website"` → `POST /api/lead`.
2. `functions/api/lead.ts` validiert mit `leadEndpointSchema` (Zod strippt unbekannte Keys!) → `fetch(LEAD_WEBHOOK_URL, body: JSON.stringify(lead))` → Apps Script → CRM-Sheet „HSB CRM Light".
3. `leadSchema.ts` akzeptiert bereits `utm_source/medium/campaign` (optional, max 100) — das Formular befüllt sie nie.

Konsequenz: Neue Felder MÜSSEN ins Endpoint-Schema, sonst strippt Zod sie vor dem Webhook.

---

### Task 1: Attributions-Bibliothek `src/lib/attribution.ts` (TDD)

**Files:**
- Create: `src/lib/attribution.ts`
- Test: `tests/attribution.test.ts`

**Interfaces (Produces):**
```ts
export interface Attribution {
  utm_source?: string; utm_medium?: string; utm_campaign?: string;
  utm_term?: string; utm_content?: string;
  referrer?: string;      // nur externes Origin (scheme+host), max 200
  landing_page?: string;  // Pfad ohne Query/Hash, max 200
}
export function captureAttribution(input: { search: string; referrer: string; pathname: string; origin: string }): Attribution;
export function updateSessionAttribution(storage: Pick<Storage,"getItem"|"setItem"> | null, current: Attribution): Attribution;
export function loadAttribution(storage: Pick<Storage,"getItem"> | null): Attribution | undefined;
export function resolveChannel(attr: Attribution): "campaign" | "referral" | "direct";
export function buildLeadAttributionFields(attr: Attribution | undefined, formPath: string): Record<string, string>;
export const ATTRIBUTION_STORAGE_KEY = "hsb-attribution-v1";
```

Regeln:
- `sanitize`: trim, Steuerzeichen und `<>"'\`` entfernen, Länge kappen, leer → `undefined`.
- Referrer: `new URL()`-Parse; same-origin → `undefined`; sonst nur `url.origin`.
- Pfade: `pathname` only (kein Query/Hash → keine PII/Token), muss mit `/` beginnen.
- `updateSessionAttribution`: neue gültige UTM-Kampagne überschreibt gespeicherte; sonst gespeicherte behalten; nichts gespeichert → aktuelle speichern. Storage-Fehler werden geschluckt.
- `buildLeadAttributionFields`: nur definierte Felder + `attribution_channel` + `form_path` + `landing_page`.

- [ ] Schritt 1: `tests/attribution.test.ts` mit den 10 Unit-Szenarien schreiben (volle UTM-URL; partielle UTMs; keine UTMs; externer Referrer; direct ohne Referrer; Landing→Kontakt-Wechsel; Session-Load; neue Kampagne überschreibt; ungültige/überlange Werte; Storage wirft).
- [ ] Schritt 2: `npx vitest run tests/attribution.test.ts` → erwartet FAIL (Modul fehlt).
- [ ] Schritt 3: `src/lib/attribution.ts` minimal implementieren.
- [ ] Schritt 4: `npx vitest run tests/attribution.test.ts` → PASS.
- [ ] Schritt 5: Commit `feat(attribution): add session-scoped lead attribution capture library`.

### Task 2: Endpoint-Schema rückwärtskompatibel erweitern (TDD)

**Files:**
- Modify: `src/lib/leadSchema.ts`
- Test: `tests/lead-endpoint-schema.test.ts` (erweitern)

**Interfaces (Produces):** `leadEndpointSchema` akzeptiert zusätzlich optional:
`utm_term`, `utm_content` (max 100), `referrer`, `landing_page`, `form_path` (max 200),
`attribution_channel` als `z.enum(["campaign","referral","direct"])`.

- [ ] Schritt 1: Tests erweitern — neue Felder akzeptiert und im Output enthalten; überlange Werte abgelehnt; Payload OHNE neue Felder weiterhin gültig (Test 11 + 12 der Spezifikation).
- [ ] Schritt 2: `npx vitest run tests/lead-endpoint-schema.test.ts` → FAIL (Zod strippt neue Felder → nicht im Output).
- [ ] Schritt 3: Felder in `leadSchema.ts` ergänzen.
- [ ] Schritt 4: Testlauf → PASS.
- [ ] Schritt 5: Commit `feat(lead-schema): accept optional attribution fields end-to-end`.

### Task 3: Layout-Capture + Formular-Integration

**Files:**
- Modify: `src/layouts/BaseLayout.astro` (neues gebündeltes `<script>` vor `</body>`: capture + updateSessionAttribution, komplett in try/catch)
- Modify: `src/components/forms/LeadForm.astro` (beim Submit: `loadAttribution(sessionStorage)` mit Fallback auf Frisch-Capture, `buildLeadAttributionFields(...)` ins Payload spreaden — vor den Pflichtfeldern, damit nichts überschrieben wird; try/catch, Versand darf nie scheitern)

- [ ] Schritt 1: `npm run test:run && npm run check && npm run build` → PASS (Integration bricht nichts).
- [ ] Schritt 2: Commit `feat(lead-form): attach session attribution to lead payload`.

### Task 4: Doku + CRM-Gate

**Files:**
- Modify: `docs/crm/CRM_LIGHT_MAX_READINESS.md` (Abschnitt: Attribution-Felder, Prioritätsregeln, Session-/Fehlerverhalten, Datenschutz, benötigte CRM-Spalten als Connector-Gate, Rollback)

- [ ] Schritt 1: Abschnitt schreiben, Commit `docs(crm): document lead attribution mapping and connector gate`.

### Task 5: Verifikation + Draft-PR

- [ ] `npm run test:run`, `npm run check`, `npm run build`, `npm run deploy:dry-run`
- [ ] Preview-/Browser-Nachweis mit `?utm_source=internal_test&utm_medium=qa&utm_campaign=lead_attribution` (Build-Output/lokal, kein Produktions-Lead)
- [ ] Branch pushen, Draft-PR gegen `main`, AI-Reviews beobachten, Findings triagieren.
