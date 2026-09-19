# B2B Event-Tracking, dynamische LogoCloud, Beanspruchungs-Check & Schema-Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** hsb-boden.de erhält ein typensicheres GA4-B2B-Event-Layer, eine branchenabhängig sortierte LogoCloud mit datenbasierten Proof-Tags, einen deterministischen technischen Beanspruchungs-Check mit Übergabe an das bestehende Audit-Anfrageformular und ein normenbasiertes Schema.org-/Meta-Upgrade — verifiziert durch `astro check`, Build und Tests.

**Architecture:** Alle neuen Client-Interaktionen laufen über die bestehende consent-gated Schicht `src/lib/tracking.ts` (Allowlist-Sanitizer); `src/lib/analytics.ts` exponiert darüber die vier typisierten B2B-Funktionen. Der Beanspruchungs-Check ist eine reine, unit-getestete Entscheidungsmatrix (`src/data/stressMatrix.ts`) plus eine Astro-Komponente, die nur DOM verdrahtet und das Ergebnis an das vorhandene `LeadForm` übergibt (kein zweiter Submit-Pfad). Normen werden zentral in `src/data/standards.ts` gepflegt und von Schema.org-Buildern konsumiert.

**Tech Stack:** Astro 7 (statisch, kein UI-Framework), TypeScript strict, Tailwind 4, Vitest 4 (jsdom), Zod.

**Spec:** Der Nutzerauftrag (5 Schritte) in dieser Session; Projektregeln `AGENTS.md`, `CLAUDE.md`, `PROJECT_TRUTH.md`.

## Global Constraints

- Freigabe-Annahme: Der 5-Schritte-Auftrag ist die Freigabe für Änderungen unter `apps/website/src/`. **Kein Push, kein Deploy.** Arbeit auf Feature-Branch `feat/b2b-tracking-stresscheck-schema`.
- Kein `any`, keine `TODO`-Kommentare, keine Mock-Daten, keine Platzhalter.
- Keine unbelegten Zertifizierungs-/Referenz-/Herstellerclaims (`AGENTS.md` Non-Negotiables). AGI S 40 und DIN EN 14411 sind Ausführungsnormen → `knowsAbout`/`additionalProperty`, **nicht** `hasCredential`. Nur „Fachbetrieb nach § 62 WHG / AwSV" ist owner-bestätigt (`PROJECT_TRUTH.md §3a`) → `hasCredential`.
- Kein Herstellervergleich im öffentlichen Text („Kagetec-R-Äquivalent" wird nicht gerendert; siehe `manufacturers.ts:14`).
- Krombacher hat kein Logo-Asset und keine Referenzfreigabe → wird nicht erfunden, wird im Report als blockiert gemeldet.
- Proof-Tags werden ausschließlich aus `reference.systems` bzw. `location.branche` abgeleitet.
- `npm run check` ist `astro check --js-only`; Gate verlangt volles `npx astro check` (Baseline: 0/0/0 bei 139 Dateien). Test-Baseline: 223/223.
- Alle Industry-`seoTitle` ≤ 60 Zeichen (`tests/content-meta.test.ts`); neue statische Titles ebenfalls ≤ 60, Descriptions ≤ 160.
- `git add` nur mit exakten Pfaden. `.astro/data-store.json` nie committen.
- Alle Befehle in `apps/website/` ausführen, sofern nicht anders angegeben.

---

### Task 0: Feature-Branch anlegen

**Files:** keine

- [ ] **Step 1: Branch anlegen**

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git checkout -b feat/b2b-tracking-stresscheck-schema
git status --short
```

Expected: Branch gewechselt; nur die drei `__pycache__`-Modifikationen aus `apps/sales-os` (werden nicht angefasst).

---

### Task 1: Normen-Datenquelle (`standards.ts`)

**Files:**
- Create: `apps/website/src/data/standards.ts`
- Test: `apps/website/tests/b2b-schema.test.ts` (Teil 1)

**Interfaces:**
- Produces: `NORM_IDS`, `type NormId = "AGI S 40" | "DIN EN 14411" | "WHG § 62"`, `executionStandards`, `organizationCredential`, `getStandardsForService(slug): NormId[]`.

- [ ] **Step 1: Test schreiben**

```ts
// tests/b2b-schema.test.ts
import { describe, expect, it } from "vitest";
import {
  NORM_IDS,
  executionStandards,
  getStandardsForService,
  organizationCredential,
} from "../src/data/standards";

describe("Normen-Datenquelle", () => {
  it("kennt genau die drei B2B-Normen", () => {
    expect([...NORM_IDS]).toEqual(["AGI S 40", "DIN EN 14411", "WHG § 62"]);
    expect(executionStandards.map((s) => s.id)).toEqual([...NORM_IDS]);
  });

  it("ordnet Leistungen belegbare Ausführungsnormen zu", () => {
    expect(getStandardsForService("keramische-industrieboeden")).toEqual(["AGI S 40", "DIN EN 14411"]);
    expect(getStandardsForService("whg-abdichtung-industrieboden")).toEqual(["WHG § 62"]);
    expect(getStandardsForService("boden-reparatur-instandsetzung")).toEqual([]);
  });

  it("führt nur den owner-bestätigten WHG-Fachbetrieb als Credential", () => {
    expect(organizationCredential.name).toContain("§ 62 WHG");
    expect(organizationCredential.evidenceRef).toContain("PROJECT_TRUTH.md");
  });
});
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `npx vitest run tests/b2b-schema.test.ts`
Expected: FAIL — `Cannot find module '../src/data/standards'`.

- [ ] **Step 3: Implementieren**

```ts
// src/data/standards.ts
export const NORM_IDS = ["AGI S 40", "DIN EN 14411", "WHG § 62"] as const;
export type NormId = (typeof NORM_IDS)[number];

export interface ExecutionStandard {
  id: NormId;
  name: string;
  scope: string;
  serviceSlugs: string[];
}

// Ausführungsnormen: Grundlage der Planung und Ausführung, keine Zertifikate.
// Sie werden in Schema.org als knowsAbout/additionalProperty geführt, nie als
// hasCredential (AGENTS.md: keine unbelegten Zertifizierungsclaims).
export const executionStandards: ExecutionStandard[] = [
  {
    id: "AGI S 40",
    name: "AGI Arbeitsblatt S 40 – Säureschutzbau: Keramische Beläge",
    scope: "Planung und Ausführung säurefester keramischer Beläge im Rüttelverfahren mit Kunstharzfuge.",
    serviceSlugs: ["keramische-industrieboeden", "industrieboden-saeureschutz"],
  },
  {
    id: "DIN EN 14411",
    name: "DIN EN 14411 – Keramische Fliesen und Platten",
    scope: "Produktnorm für die eingesetzten Feinsteinzeug- und Spaltplatten (Wasseraufnahme, Biegefestigkeit, Beständigkeit).",
    serviceSlugs: ["keramische-industrieboeden"],
  },
  {
    id: "WHG § 62",
    name: "§ 62 WHG / AwSV – Anlagen zum Umgang mit wassergefährdenden Stoffen",
    scope: "Dichtheits- und Beständigkeitsanforderungen an Flächen und Auffangwannen; Ausführung durch Fachbetrieb nach AwSV.",
    serviceSlugs: ["whg-abdichtung-industrieboden", "industrieboden-saeureschutz"],
  },
];

// Einziges Credential: Owner-Bestätigung 2026-08-03, Urkunde bewusst nicht im
// Repo (PROJECT_TRUTH.md, Abschnitt 3a).
export const organizationCredential = {
  name: "Fachbetrieb nach § 62 WHG / AwSV",
  credentialCategory: "certification",
  evidenceRef: "PROJECT_TRUTH.md §3a (Owner-Bestätigung 2026-08-03)",
} as const;

export function getStandardsForService(serviceSlug: string): NormId[] {
  return executionStandards
    .filter((standard) => standard.serviceSlugs.includes(serviceSlug))
    .map((standard) => standard.id);
}
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `npx vitest run tests/b2b-schema.test.ts`
Expected: PASS (3 Tests).

- [ ] **Step 5: Commit**

```bash
git add apps/website/src/data/standards.ts apps/website/tests/b2b-schema.test.ts
git commit -m "feat(website): zentrale Normen-Datenquelle für Schema.org und Beanspruchungs-Check"
```

---

### Task 2: GA4 B2B-Event-Layer (`analytics.ts` + `tracking.ts`)

**Files:**
- Create: `apps/website/src/lib/analyticsConfig.ts`
- Modify: `apps/website/src/lib/analytics.ts` (Konstanten re-exportieren, B2B-API anhängen)
- Modify: `apps/website/src/lib/tracking.ts` (Import umstellen, Events, Validatoren, dataLayer-Fallback)
- Test: `apps/website/tests/b2b-analytics.test.ts`

**Interfaces:**
- Consumes: `NORM_IDS`, `NormId` aus Task 1.
- Produces (aus `analytics.ts`):
  - `trackStressCheck(step: number, data: StressCheckStepData): void`
  - `trackReferenceInteraction(clientName: string, industry: string, action: "click" | "view"): void`
  - `trackNormInteraction(norm: NormId, action: "expand" | "download"): void`
  - `trackB2BConversion(type: "audit_request" | "technical_inquiry", payload: Record<string, unknown>): void`
  - `interface B2BDataLayer` mit genau diesen vier Methoden; `export const b2bDataLayer: B2BDataLayer`.
- Produces (aus `tracking.ts`): neue `TrackingEvent`-Werte `StressCheckStep = "stress_check_step"`, `ReferenceInteraction = "reference_interaction"`, `NormInteraction = "norm_interaction"`, `B2BConversion = "b2b_conversion"`.

- [ ] **Step 1: Test schreiben**

```ts
// tests/b2b-analytics.test.ts
// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  b2bDataLayer,
  trackB2BConversion,
  trackNormInteraction,
  trackReferenceInteraction,
  trackStressCheck,
} from "../src/lib/analytics";

type TrackingWindow = Window & {
  dataLayer?: unknown[];
  gtag?: (...args: unknown[]) => void;
};

const win = window as TrackingWindow;

beforeEach(() => {
  delete win.dataLayer;
  delete win.gtag;
  localStorage.setItem("hsb-consent-v1", JSON.stringify({ necessary: true, analytics: true }));
  window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
});

describe("B2B DataLayer-Interface", () => {
  it("exponiert die vier typisierten Methoden", () => {
    expect(typeof b2bDataLayer.trackStressCheck).toBe("function");
    expect(typeof b2bDataLayer.trackReferenceInteraction).toBe("function");
    expect(typeof b2bDataLayer.trackNormInteraction).toBe("function");
    expect(typeof b2bDataLayer.trackB2BConversion).toBe("function");
  });

  it("trackStressCheck liefert Schritt und Parameter vollständig an gtag", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackStressCheck(2, { medium: "milchsaeure-molke", tempRange: "thermoschock-85" });
    expect(gtag).toHaveBeenCalledWith("event", "stress_check_step", {
      step: 2,
      medium: "milchsaeure-molke",
      temp_range: "thermoschock-85",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("trackStressCheck verwirft ungültige Schritte und Nicht-Slugs", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackStressCheck(0, { medium: "<script>" });
    expect(gtag).toHaveBeenCalledWith("event", "stress_check_step", { send_to: "G-VC4BJBEFTV" });
  });

  it("trackReferenceInteraction überträgt Kundennamen mit Umlauten und Sonderzeichen", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackReferenceInteraction("Molkerei Gropper GmbH & Co. KG", "molkerei", "click");
    expect(gtag).toHaveBeenCalledWith("event", "reference_interaction", {
      client_name: "Molkerei Gropper GmbH & Co. KG",
      industry: "molkerei",
      action: "click",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("trackNormInteraction akzeptiert nur die drei bekannten Normen", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackNormInteraction("WHG § 62", "expand");
    expect(gtag).toHaveBeenCalledWith("event", "norm_interaction", {
      norm: "WHG § 62",
      action: "expand",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("trackB2BConversion lässt keine personenbezogenen Daten nach GA4 durch", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackB2BConversion("audit_request", {
      recommended_system: "agi-s40-ruettelkeramik",
      industry: "molkerei",
      email: "test@example.com",
      phone: "+491234",
      name: "Test Person",
      message: "vertraulich",
    });
    expect(gtag).toHaveBeenCalledWith("event", "b2b_conversion", {
      conversion_type: "audit_request",
      recommended_system: "agi-s40-ruettelkeramik",
      industry: "molkerei",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("legt dataLayer an, wenn gtag fehlt und dataLayer noch undefiniert ist", () => {
    trackB2BConversion("technical_inquiry", { industry: "chemieindustrie" });
    expect(Array.isArray(win.dataLayer)).toBe(true);
    expect(win.dataLayer).toContainEqual({
      event: "b2b_conversion",
      conversion_type: "technical_inquiry",
      industry: "chemieindustrie",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("sendet ohne Analytics-Einwilligung nichts", () => {
    localStorage.clear();
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: false } }));
    trackStressCheck(1, { medium: "fette-oele" });
    expect(win.dataLayer).toBeUndefined();
  });
});
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `npx vitest run tests/b2b-analytics.test.ts`
Expected: FAIL — Exporte `trackStressCheck` etc. fehlen.

- [ ] **Step 3: `analyticsConfig.ts` anlegen (bricht den Import-Zyklus analytics ↔ tracking)**

```ts
// src/lib/analyticsConfig.ts
export const GA4_MEASUREMENT_ID = "G-VC4BJBEFTV";
export const PRODUCTION_ANALYTICS_HOST = "www.hsb-boden.de";
```

- [ ] **Step 4: `tracking.ts` anpassen**

Zeile 1 ersetzen:

```ts
import { GA4_MEASUREMENT_ID } from "./analyticsConfig";
import { NORM_IDS } from "../data/standards";
```

Enum erweitern (nach `FlyerQrVisit = "flyer_qr_visit",`):

```ts
  StressCheckStep = "stress_check_step",
  ReferenceInteraction = "reference_interaction",
  NormInteraction = "norm_interaction",
  B2BConversion = "b2b_conversion",
```

Typen exportieren (bisher lokal): `export type AnalyticsValue = ...` und `export type AnalyticsPayload = ...`.

Nach `LOCAL_PATH_PATTERN` ergänzen:

```ts
// Anzeigename einer Referenz: Buchstaben, Ziffern, Leerzeichen und übliche
// Firmenzeichen. Kein HTML, keine Steuerzeichen.
const SAFE_LABEL_PATTERN = /^[\p{L}\p{N}][\p{L}\p{N} .,&§+()/-]{0,99}$/u;
const CONVERSION_TYPES = new Set(["audit_request", "technical_inquiry"]);
const REFERENCE_ACTIONS = new Set(["click", "view"]);
const NORM_ACTIONS = new Set(["expand", "download"]);
const NORM_SET = new Set<string>(NORM_IDS);
const isToken = (value: AnalyticsValue) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value);
```

`PARAMETER_VALIDATORS` um folgende Einträge erweitern (vorhandene bleiben):

```ts
  step: (value) => typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 10,
  medium: isToken,
  temp_range: isToken,
  mechanical_load: isToken,
  time_window: isToken,
  recommended_system: isToken,
  industry: isToken,
  project_type: isToken,
  client_name: (value) => typeof value === "string" && SAFE_LABEL_PATTERN.test(value),
  action: (value) => typeof value === "string" && (REFERENCE_ACTIONS.has(value) || NORM_ACTIONS.has(value)),
  norm: (value) => typeof value === "string" && NORM_SET.has(value),
  conversion_type: (value) => typeof value === "string" && CONVERSION_TYPES.has(value),
```

dataLayer-Fallback in `emitEvent` ersetzen — aus

```ts
    if (Array.isArray(trackingWindow.dataLayer)) {
      trackingWindow.dataLayer.push({ event: eventName, ...eventPayload });
      completion?.();
      return true;
    }
```

wird

```ts
    // GTM-Fallback: dataLayer bei Bedarf anlegen, damit ein Event vor dem
    // gtag-Loader nicht verloren geht. Consent ist oben bereits geprüft.
    if (!Array.isArray(trackingWindow.dataLayer)) trackingWindow.dataLayer = [];
    trackingWindow.dataLayer.push({ event: eventName, ...eventPayload });
    completion?.();
    return true;
```

Der abschließende `completion?.(); return false;` nach dem `try/catch` bleibt (greift nur bei Exception).

- [ ] **Step 5: `analytics.ts` erweitern**

Zeilen 3–4 ersetzen durch:

```ts
import { GA4_MEASUREMENT_ID, PRODUCTION_ANALYTICS_HOST } from "./analyticsConfig";
import { TrackingEvent, trackEvent, type AnalyticsPayload, type AnalyticsValue } from "./tracking";
import type { NormId } from "../data/standards";

export { GA4_MEASUREMENT_ID, PRODUCTION_ANALYTICS_HOST };
```

Am Dateiende anhängen:

```ts
// ---------------------------------------------------------------------------
// Typensicheres B2B-DataLayer für GA4. Alle Methoden laufen über die
// consent-gated Schicht in tracking.ts; nicht allowlistete Parameter werden
// dort verworfen, PII erreicht GA4 damit nie.
// ---------------------------------------------------------------------------

export interface StressCheckStepData {
  medium?: string;
  tempRange?: string;
  mechanicalLoad?: string;
  timeWindow?: string;
  recommendedSystem?: string;
}

export type ReferenceAction = "click" | "view";
export type NormAction = "expand" | "download";
export type B2BConversionType = "audit_request" | "technical_inquiry";

export interface B2BDataLayer {
  trackStressCheck(step: number, data: StressCheckStepData): void;
  trackReferenceInteraction(clientName: string, industry: string, action: ReferenceAction): void;
  trackNormInteraction(norm: NormId, action: NormAction): void;
  trackB2BConversion(type: B2BConversionType, payload: Record<string, unknown>): void;
}

const B2B_CONVERSION_KEYS = [
  "form_path",
  "placement",
  "industry",
  "project_type",
  "medium",
  "temp_range",
  "mechanical_load",
  "time_window",
  "recommended_system",
] as const;

function definedEntries(payload: Record<string, AnalyticsValue | undefined>): AnalyticsPayload {
  return Object.fromEntries(
    Object.entries(payload).filter((entry): entry is [string, AnalyticsValue] => entry[1] !== undefined),
  );
}

export function trackStressCheck(step: number, data: StressCheckStepData): void {
  trackEvent(
    TrackingEvent.StressCheckStep,
    definedEntries({
      step,
      medium: data.medium,
      temp_range: data.tempRange,
      mechanical_load: data.mechanicalLoad,
      time_window: data.timeWindow,
      recommended_system: data.recommendedSystem,
    }),
  );
}

export function trackReferenceInteraction(
  clientName: string,
  industry: string,
  action: ReferenceAction,
): void {
  trackEvent(TrackingEvent.ReferenceInteraction, { client_name: clientName, industry, action });
}

export function trackNormInteraction(norm: NormId, action: NormAction): void {
  trackEvent(TrackingEvent.NormInteraction, { norm, action });
}

export function trackB2BConversion(type: B2BConversionType, payload: Record<string, unknown>): void {
  const narrowed: Record<string, AnalyticsValue | undefined> = { conversion_type: type };
  for (const key of B2B_CONVERSION_KEYS) {
    const value = payload[key];
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      narrowed[key] = value;
    }
  }
  trackEvent(TrackingEvent.B2BConversion, definedEntries(narrowed));
}

export const b2bDataLayer: B2BDataLayer = {
  trackStressCheck,
  trackReferenceInteraction,
  trackNormInteraction,
  trackB2BConversion,
};
```

- [ ] **Step 6: Tests laufen lassen**

Run: `npx vitest run tests/b2b-analytics.test.ts tests/tracking.test.ts tests/analytics.test.ts`
Expected: PASS. Falls `tracking.test.ts` „wirft nicht, wenn weder gtag noch dataLayer existieren" weiterhin grün (es prüft nur `not.toThrow`).

- [ ] **Step 7: Typprüfung**

Run: `npx astro check`
Expected: 0 errors.

- [ ] **Step 8: Commit**

```bash
git add apps/website/src/lib/analyticsConfig.ts apps/website/src/lib/analytics.ts apps/website/src/lib/tracking.ts apps/website/tests/b2b-analytics.test.ts
git commit -m "feat(website): typensicheres GA4-B2B-DataLayer mit Allowlist und dataLayer-Fallback"
```

---

### Task 3: Dynamische LogoCloud mit Branchenfilter und Proof-Tags

**Files:**
- Modify: `apps/website/src/lib/content.ts` (`getLogoCloudEntries` erweitern, Labels-Map)
- Modify: `apps/website/src/components/sections/LogoCloud.astro`
- Modify: `apps/website/src/pages/branchen/[slug].astro` (Einbindung nach dem Hero-Bild)
- Test: `apps/website/tests/logo-cloud-filter.test.ts`

**Interfaces:**
- Consumes: `trackReferenceInteraction` aus Task 2.
- Produces: `getLogoCloudEntries(industryFilter?: string): LogoCloudEntry[]` mit `LogoCloudEntry = { id: string; name: string; logo: string; meta: string; industry?: string; systems: string[]; proofTag: string }`.

- [ ] **Step 1: Test schreiben**

```ts
// tests/logo-cloud-filter.test.ts
import { describe, expect, it } from "vitest";
import { getLogoCloudEntries } from "../src/lib/content";

describe("LogoCloud Branchenfilter", () => {
  it("stellt bei 'molkerei' Gropper und Meggle an den Anfang", () => {
    const names = getLogoCloudEntries("molkerei").slice(0, 2).map((entry) => entry.name);
    expect(names).toEqual(expect.arrayContaining(["Molkerei Gropper GmbH & Co. KG", "Meggle"]));
  });

  it("stellt bei 'lebensmittelindustrie' Südzucker an den Anfang", () => {
    expect(getLogoCloudEntries("lebensmittelindustrie")[0].name).toBe("Südzucker AG");
  });

  it("zieht bei 'chemieindustrie' Concept Color vor und Südzucker über Systemaffinität nach vorn", () => {
    const names = getLogoCloudEntries("chemieindustrie").map((entry) => entry.name);
    expect(names[0]).toBe("Concept Color GmbH");
    expect(names.indexOf("Südzucker AG")).toBeLessThan(names.indexOf("Peterstaler Mineralquellen GmbH"));
  });

  it("ändert ohne Filter weder Menge noch Reihenfolge", () => {
    const unfiltered = getLogoCloudEntries();
    const filtered = getLogoCloudEntries("molkerei");
    expect(filtered).toHaveLength(unfiltered.length);
    expect(new Set(filtered.map((e) => e.logo))).toEqual(new Set(unfiltered.map((e) => e.logo)));
  });

  it("leitet Proof-Tags ausschließlich aus den dokumentierten Systemen ab", () => {
    const entries = getLogoCloudEntries();
    const suedzucker = entries.find((entry) => entry.name === "Südzucker AG");
    const gropper = entries.find((entry) => entry.name === "Molkerei Gropper GmbH & Co. KG");
    const kyritzer = entries.find((entry) => entry.logo === "/logos/kyritzer-fruchtsaefte.png");
    expect(suedzucker?.proofTag).toBe("Säureschutz & WHG § 62 Abdichtung");
    expect(gropper?.proofTag).toBe("Rüttelkeramik & Entwässerung");
    expect(kyritzer?.proofTag).toBe("Kundenstandort Getränke");
    for (const entry of entries) expect(entry.proofTag.length).toBeGreaterThan(0);
  });

  it("erfindet keinen Eintrag für Kunden ohne Logo-Freigabe", () => {
    const names = getLogoCloudEntries("brauerei-getraenkeindustrie").map((entry) => entry.name);
    expect(names).not.toContain("Krombacher Brauerei GmbH & Co. KG");
  });
});
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `npx vitest run tests/logo-cloud-filter.test.ts`
Expected: FAIL — `proofTag` undefined, Filter ohne Wirkung.

- [ ] **Step 3: `content.ts` erweitern**

Vor `getLogoCloudEntries` einfügen:

```ts
export interface LogoCloudEntry {
  id: string;
  name: string;
  logo: string;
  meta: string;
  industry?: string;
  systems: string[];
  proofTag: string;
}

// Technische Kurzlabels je Leistungs-Slug. Proof-Tags entstehen nur aus den in
// references.ts dokumentierten Systemen — kein Freitext je Kunde.
const SYSTEM_PROOF_LABELS: Record<string, string> = {
  "industrieboden-saeureschutz": "Säureschutz",
  "whg-abdichtung-industrieboden": "WHG § 62 Abdichtung",
  "keramische-industrieboeden": "Rüttelkeramik",
  "entwaesserung-industrieboden": "Entwässerung",
  "pu-beton-industrieboden": "PU-Beton",
  "epoxidharz-bodenbeschichtung": "Epoxidharz-Beschichtung",
  "dehnungsfugen-rammschutz-industrieboden": "Dehnungsfugen & Rammschutz",
  "bodensanierung-laufender-betrieb": "Sanierung im Betrieb",
  "boden-reparatur-instandsetzung": "Reparatur & Instandsetzung",
};

// Freitext-Branche der Kundenstandorte -> kanonischer Branchen-Slug.
const LOCATION_BRANCHE_TO_INDUSTRY: Record<string, string> = {
  Molkerei: "molkerei",
  Brauerei: "brauerei-getraenkeindustrie",
  Getränke: "brauerei-getraenkeindustrie",
  Lebensmittel: "lebensmittelindustrie",
  Chemie: "chemieindustrie",
  Pharma: "pharmaindustrie",
};

function buildProofTag(systems: string[]): string {
  return systems
    .map((slug) => SYSTEM_PROOF_LABELS[slug])
    .filter((label): label is string => Boolean(label))
    .slice(0, 2)
    .join(" & ");
}
```

`getLogoCloudEntries` ersetzen durch:

```ts
export function getLogoCloudEntries(industryFilter?: string): LogoCloudEntry[] {
  // Bewusst nur gegen die Referenzen deduplizieren, die hier tatsaechlich ein
  // Logo rendern: eine Referenz ohne Logo-Freigabe darf ein separat
  // freigegebenes Standort-Logo nicht stillschweigend unterdruecken.
  const referencesWithLogo = getPublicReferences().filter(
    (reference) => reference.logo,
  );
  const renderedReferenceIds = new Set(
    referencesWithLogo.map((reference) => reference.id),
  );

  const referenceEntries: LogoCloudEntry[] = referencesWithLogo.map((reference) => ({
    id: reference.id,
    name: reference.displayName,
    logo: reference.logo as string,
    meta: "Referenzprojekt",
    industry: reference.industry,
    systems: [...reference.systems],
    proofTag: buildProofTag([...reference.systems]),
  }));

  const locationEntries: LogoCloudEntry[] = clientLocations
    .filter((location) => "logo" in location)
    .filter(
      (location) =>
        !("referenceId" in location) ||
        !renderedReferenceIds.has(location.referenceId),
    )
    .map((location) => ({
      id: `standort-${location.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
      name: location.name,
      logo: location.logo,
      meta: location.branche,
      industry: LOCATION_BRANCHE_TO_INDUSTRY[location.branche],
      systems: [],
      proofTag: `Kundenstandort ${location.branche}`,
    }));

  const entries = [...referenceEntries, ...locationEntries];
  if (!industryFilter) return entries;

  // Rang 2: Branche identisch. Rang 1: mindestens ein System gehört zu den
  // empfohlenen Systemen der gefilterten Branche (z. B. Südzucker bei Chemie
  // über Säureschutz/WHG). Rang 0: Rest. Sortierung ist stabil.
  const industry = getIndustries().find((item) => item.slug === industryFilter);
  const affineSystems = new Set([...(industry?.recommendedSystems ?? []), ...(industry?.relatedServices ?? [])]);
  const rank = (entry: LogoCloudEntry) => {
    if (entry.industry === industryFilter) return 2;
    if (entry.systems.some((slug) => affineSystems.has(slug))) return 1;
    return 0;
  };
  return entries
    .map((entry, index) => ({ entry, index, rank: rank(entry) }))
    .sort((a, b) => b.rank - a.rank || a.index - b.index)
    .map((item) => item.entry);
}
```

Prüfen, dass `getIndustries` in `content.ts` oberhalb definiert ist (sonst hoisting über `function`-Deklaration ohnehin gegeben).

- [ ] **Step 4: Tests laufen lassen**

Run: `npx vitest run tests/logo-cloud-filter.test.ts tests/reference-deduplication.test.ts`
Expected: PASS. Falls der Chemie-Test scheitert, weil `Südzucker` bereits Rang 2 hat: nicht der Fall (industry = lebensmittelindustrie). Falls `Peterstaler` durch `keramische-industrieboeden` ebenfalls Rang 1 erhält, ist das erwartbar — dann Testerwartung auf `toBeLessThanOrEqual` der Position von `Dahlhoff Feinkost GmbH` umstellen (Dahlhoff hat nur pu-beton/sanierung, Chemie empfiehlt `industrieboden-saeureschutz`, `whg-abdichtung-industrieboden`, `epoxidharz-bodenbeschichtung`, `keramische-industrieboeden` — vor der Anpassung `industries.ts` Zeilen 170–223 lesen und den Test anhand der realen Daten festzurren).

- [ ] **Step 5: `LogoCloud.astro` umbauen**

```astro
---
import { getLogoCloudEntries } from "../../lib/content";

interface Props {
  industryFilter?: string;
  eyebrow?: string;
  title?: string;
}

const {
  industryFilter,
  eyebrow = "Vertrauen durch reale Umsetzung",
  title = "Referenzkunden (Auszug)",
} = Astro.props;

const logos = getLogoCloudEntries(industryFilter);
---

<section class="section border-b border-hsb-line bg-white" data-logo-cloud data-industry-filter={industryFilter ?? ""}>
  <div class="container">
    <div class="mb-10 text-center lg:mb-12">
      <p class="text-xs font-black uppercase tracking-[0.2em] text-hsb-red">{eyebrow}</p>
      <h2 class="h2 mt-4">{title}</h2>
    </div>

    <div class="mx-auto grid max-w-6xl grid-cols-2 overflow-hidden rounded-[4px] border border-hsb-line bg-hsb-line sm:grid-cols-4">
      {logos.map((reference) => (
        <a
          href="/referenzen/"
          class="group grid min-h-[148px] content-between justify-items-center gap-4 bg-white px-4 py-5 no-underline transition-colors hover:bg-[#fbfcfd] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-hsb-red"
          data-logo-entry
          data-client={reference.name}
          data-industry={reference.industry ?? ""}
          aria-label={`${reference.name} – ${reference.proofTag} – Referenzen ansehen`}
        >
          <div class="grid h-14 w-full max-w-[150px] place-items-center grayscale opacity-75 contrast-125 transition-all group-hover:grayscale-0 group-hover:opacity-100">
            <img
              src={reference.logo}
              alt={`${reference.name} Logo`}
              class="max-h-11 w-full object-contain"
              loading="lazy"
            />
          </div>
          <div class="grid gap-1 text-center">
            <span class="text-[10px] font-black uppercase tracking-widest text-hsb-black transition-colors group-hover:text-hsb-red">
              {reference.name}
            </span>
            <span class="text-[9px] font-bold uppercase tracking-[0.14em] text-hsb-steel">{reference.meta}</span>
            <span class="mt-1 inline-block justify-self-center rounded-[2px] border border-hsb-line bg-hsb-mist px-2 py-1 text-[9px] font-black uppercase tracking-[0.12em] text-hsb-black">
              {reference.proofTag}
            </span>
          </div>
        </a>
      ))}
    </div>
  </div>
</section>

<script>
  import { trackReferenceInteraction } from "../../lib/analytics";

  const entries = document.querySelectorAll<HTMLAnchorElement>("[data-logo-entry]");

  function describe(element: HTMLElement) {
    return {
      client: element.dataset.client ?? "",
      industry: element.dataset.industry || "unbekannt",
    };
  }

  entries.forEach((element) => {
    element.addEventListener("click", () => {
      const { client, industry } = describe(element);
      trackReferenceInteraction(client, industry, "click");
    });
  });

  // 'view' genau einmal je Logo, sobald es zu 60 % sichtbar war.
  if ("IntersectionObserver" in window) {
    const seen = new WeakSet<Element>();
    const observer = new IntersectionObserver(
      (observed) => {
        observed.forEach((item) => {
          if (!item.isIntersecting || seen.has(item.target)) return;
          seen.add(item.target);
          observer.unobserve(item.target);
          const { client, industry } = describe(item.target as HTMLElement);
          trackReferenceInteraction(client, industry, "view");
        });
      },
      { threshold: 0.6 },
    );
    entries.forEach((element) => observer.observe(element));
  }
</script>
```

Hinweis: `industry` „unbekannt" ist ein gültiges Token für den Validator; Kundennamen mit Umlauten passieren `SAFE_LABEL_PATTERN`.

- [ ] **Step 6: Branchenseiten einbinden**

In `src/pages/branchen/[slug].astro` Import ergänzen:

```astro
import LogoCloud from "../../components/sections/LogoCloud.astro";
```

Direkt nach dem `{industryImage && (...)}`-Block (vor `<section class="section">` „Suchintention") einfügen:

```astro
  <LogoCloud industryFilter={industry.slug} eyebrow="Branchennahe Referenzen" title={`Referenzkunden mit Bezug zu ${industry.title}`} />
```

- [ ] **Step 7: Typprüfung + Tests**

Run: `npx astro check && npx vitest run tests/logo-cloud-filter.test.ts tests/reference-deduplication.test.ts`
Expected: 0 errors, PASS.

- [ ] **Step 8: Commit**

```bash
git add apps/website/src/lib/content.ts apps/website/src/components/sections/LogoCloud.astro "apps/website/src/pages/branchen/[slug].astro" apps/website/tests/logo-cloud-filter.test.ts
git commit -m "feat(website): LogoCloud mit Branchenfilter, datenbasierten Proof-Tags und Referenz-Tracking"
```

---

### Task 4: Deterministische Beanspruchungs-Matrix (`stressMatrix.ts`)

**Files:**
- Create: `apps/website/src/data/stressMatrix.ts`
- Test: `apps/website/tests/stress-matrix.test.ts`

**Interfaces:**
- Consumes: `NormId` aus Task 1.
- Produces: `STRESS_MEDIA`, `STRESS_TEMPERATURES`, `STRESS_MECHANICAL`, `STRESS_TIME_WINDOWS` (je `readonly { id, label, hint? }[]`), Typen `StressMediumId`, `StressTemperatureId`, `StressMechanicalId`, `StressTimeWindowId`, `StressSystemId`, `StressCheckInput`, `StressSystem`, `StressCheckResult`, `STRESS_SYSTEMS`, `resolveStressSystem(input): StressCheckResult`, `isStressCheckInput(value: unknown): value is StressCheckInput`.

- [ ] **Step 1: Test schreiben**

```ts
// tests/stress-matrix.test.ts
import { describe, expect, it } from "vitest";
import {
  STRESS_MECHANICAL,
  STRESS_MEDIA,
  STRESS_SYSTEMS,
  STRESS_TEMPERATURES,
  STRESS_TIME_WINDOWS,
  isStressCheckInput,
  resolveStressSystem,
} from "../src/data/stressMatrix";

describe("Beanspruchungs-Matrix", () => {
  it("liefert für jede der 180 Kombinationen deterministisch ein bekanntes System", () => {
    for (const medium of STRESS_MEDIA) {
      for (const temperature of STRESS_TEMPERATURES) {
        for (const mechanical of STRESS_MECHANICAL) {
          for (const timeWindow of STRESS_TIME_WINDOWS) {
            const input = {
              medium: medium.id,
              tempRange: temperature.id,
              mechanicalLoad: mechanical.id,
              timeWindow: timeWindow.id,
            };
            const first = resolveStressSystem(input);
            const second = resolveStressSystem(input);
            expect(first).toEqual(second);
            expect(STRESS_SYSTEMS[first.system.id]).toBe(first.system);
            expect(first.reasons.length).toBeGreaterThan(0);
          }
        }
      }
    }
  });

  it("Heißdampf > 100 °C erzwingt Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "fette-oele", tempRange: "heissdampf-100", mechanicalLoad: "handhubwagen", timeWindow: "wochenende-48h" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
    expect(result.windowNote).toBeDefined();
  });

  it("Schwerlast mit Vulkollanrollen erzwingt Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "cip-laugen", tempRange: "warmwasser-60", mechanicalLoad: "schwerlast-vulkollan", timeWindow: "revision-7-14d" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
  });

  it("anorganische Säuren ohne Thermoschock führen zur WHG § 62 Fachbeschichtung", () => {
    const result = resolveStressSystem({ medium: "anorganische-saeuren", tempRange: "dauernass-kalt", mechanicalLoad: "gabelstapler-3-5t", timeWindow: "revision-7-14d" });
    expect(result.system.id).toBe("whg-fachbeschichtung");
    expect(result.system.norms).toContain("WHG § 62");
  });

  it("anorganische Säuren mit Thermoschock führen zur Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "anorganische-saeuren", tempRange: "thermoschock-85", mechanicalLoad: "handhubwagen", timeWindow: "neubau" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
  });

  it("Wochenendfenster ohne Zwangskriterium führt zu PU-Beton", () => {
    const result = resolveStressSystem({ medium: "milchsaeure-molke", tempRange: "thermoschock-85", mechanicalLoad: "gabelstapler-3-5t", timeWindow: "wochenende-48h" });
    expect(result.system.id).toBe("pu-beton-hochtemperatur");
  });

  it("Fette/Öle ohne Zwangskriterium führen zu PU-Beton", () => {
    const result = resolveStressSystem({ medium: "fette-oele", tempRange: "warmwasser-60", mechanicalLoad: "handhubwagen", timeWindow: "neubau" });
    expect(result.system.id).toBe("pu-beton-hochtemperatur");
  });

  it("organische Säuren und Laugen im Revisionsfenster führen zur Rüttelkeramik", () => {
    const result = resolveStressSystem({ medium: "milchsaeure-molke", tempRange: "thermoschock-85", mechanicalLoad: "gabelstapler-3-5t", timeWindow: "revision-7-14d" });
    expect(result.system.id).toBe("agi-s40-ruettelkeramik");
    expect(result.system.norms).toEqual(["AGI S 40", "DIN EN 14411"]);
  });

  it("Type-Guard akzeptiert nur bekannte IDs", () => {
    expect(isStressCheckInput({ medium: "fette-oele", tempRange: "warmwasser-60", mechanicalLoad: "handhubwagen", timeWindow: "neubau" })).toBe(true);
    expect(isStressCheckInput({ medium: "x", tempRange: "warmwasser-60", mechanicalLoad: "handhubwagen", timeWindow: "neubau" })).toBe(false);
    expect(isStressCheckInput(null)).toBe(false);
  });

  it("rendert keinen Herstellervergleich im öffentlichen Systemnamen", () => {
    for (const system of Object.values(STRESS_SYSTEMS)) {
      expect(system.name.toLowerCase()).not.toContain("kagetec");
      expect(system.description.toLowerCase()).not.toContain("kagetec");
    }
  });
});
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `npx vitest run tests/stress-matrix.test.ts`
Expected: FAIL — Modul fehlt.

- [ ] **Step 3: Implementieren**

```ts
// src/data/stressMatrix.ts
import type { NormId } from "./standards";

export interface StressOption<Id extends string> {
  id: Id;
  label: string;
  hint?: string;
}

export const STRESS_MEDIA = [
  { id: "milchsaeure-molke", label: "Milchsäure / Molke", hint: "Molkerei, Käserei, Milchverarbeitung" },
  { id: "fruchtsaeuren", label: "Fruchtsäuren", hint: "Getränke, Obst- und Gemüseverarbeitung" },
  { id: "cip-laugen", label: "CIP-Laugen (NaOH)", hint: "Reinigungskreisläufe, Abfüllung" },
  { id: "anorganische-saeuren", label: "Anorganische Säuren (pH 0–2)", hint: "Chemie, Beizerei, Auffangwannen" },
  { id: "fette-oele", label: "Fette / Öle", hint: "Feinkost, Backwaren, Großküche" },
] as const satisfies readonly StressOption<string>[];

export const STRESS_TEMPERATURES = [
  { id: "dauernass-kalt", label: "Dauernass kalt (< 20 °C)" },
  { id: "warmwasser-60", label: "Warmwasser bis 60 °C" },
  { id: "thermoschock-85", label: "Thermoschock / CIP-Reinigung bis 85 °C" },
  { id: "heissdampf-100", label: "Heißdampf > 100 °C" },
] as const satisfies readonly StressOption<string>[];

export const STRESS_MECHANICAL = [
  { id: "handhubwagen", label: "Handhubwagen" },
  { id: "gabelstapler-3-5t", label: "Gabelstapler 3–5 t" },
  { id: "schwerlast-vulkollan", label: "Schwerlast-Flurförderzeuge mit Vulkollanrollen (> 30 N/mm²)" },
] as const satisfies readonly StressOption<string>[];

export const STRESS_TIME_WINDOWS = [
  { id: "wochenende-48h", label: "Wochenendstillstand (< 48 h)" },
  { id: "revision-7-14d", label: "Revisionsstillstand (7–14 Tage)" },
  { id: "neubau", label: "Neubau" },
] as const satisfies readonly StressOption<string>[];

export type StressMediumId = (typeof STRESS_MEDIA)[number]["id"];
export type StressTemperatureId = (typeof STRESS_TEMPERATURES)[number]["id"];
export type StressMechanicalId = (typeof STRESS_MECHANICAL)[number]["id"];
export type StressTimeWindowId = (typeof STRESS_TIME_WINDOWS)[number]["id"];

export interface StressCheckInput {
  medium: StressMediumId;
  tempRange: StressTemperatureId;
  mechanicalLoad: StressMechanicalId;
  timeWindow: StressTimeWindowId;
}

export type StressSystemId = "agi-s40-ruettelkeramik" | "pu-beton-hochtemperatur" | "whg-fachbeschichtung";

export interface StressSystem {
  id: StressSystemId;
  name: string;
  short: string;
  description: string;
  serviceSlug: string;
  norms: NormId[];
}

export const STRESS_SYSTEMS: Record<StressSystemId, StressSystem> = {
  "agi-s40-ruettelkeramik": {
    id: "agi-s40-ruettelkeramik",
    name: "AGI S 40 Vibro-Rüttelkeramik mit Kunstharzfuge",
    short: "Rüttelkeramik (AGI S 40)",
    description:
      "Keramische Platten nach DIN EN 14411, im Rüttelverfahren in ein Reaktionsharz-Bett eingebracht und mit Kunstharzfuge geschlossen. Beständig gegen organische und anorganische Säuren, Laugen und Thermoschock; höchste Druck- und Punktlastfestigkeit.",
    serviceSlug: "keramische-industrieboeden",
    norms: ["AGI S 40", "DIN EN 14411"],
  },
  "pu-beton-hochtemperatur": {
    id: "pu-beton-hochtemperatur",
    name: "Hochtemperatur-Polyurethanbeton (PU-Beton bis 120 °C)",
    short: "PU-Beton (bis 120 °C)",
    description:
      "Fugenarmes, thermoschockbeständiges Polyurethan-Zement-System für Fette, Öle und organische Säuren. Schnell härtend und deshalb erste Wahl für kurze Stillstandsfenster.",
    serviceSlug: "pu-beton-industrieboden",
    norms: [],
  },
  "whg-fachbeschichtung": {
    id: "whg-fachbeschichtung",
    name: "WHG § 62 Fachbeschichtung (Chemie / Auffangwannen)",
    short: "WHG § 62 Fachbeschichtung",
    description:
      "Dichte, chemikalienbeständige Flächen- und Auffangwannenbeschichtung für den Umgang mit wassergefährdenden Stoffen, ausgeführt als Fachbetrieb nach § 62 WHG / AwSV mit Dokumentation für Behörden und Sachverständige.",
    serviceSlug: "whg-abdichtung-industrieboden",
    norms: ["WHG § 62"],
  },
};

export interface StressCheckResult {
  system: StressSystem;
  reasons: string[];
  windowNote?: string;
}

const MEDIA_IDS = new Set<string>(STRESS_MEDIA.map((item) => item.id));
const TEMPERATURE_IDS = new Set<string>(STRESS_TEMPERATURES.map((item) => item.id));
const MECHANICAL_IDS = new Set<string>(STRESS_MECHANICAL.map((item) => item.id));
const TIME_WINDOW_IDS = new Set<string>(STRESS_TIME_WINDOWS.map((item) => item.id));

export function isStressCheckInput(value: unknown): value is StressCheckInput {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.medium === "string" && MEDIA_IDS.has(candidate.medium) &&
    typeof candidate.tempRange === "string" && TEMPERATURE_IDS.has(candidate.tempRange) &&
    typeof candidate.mechanicalLoad === "string" && MECHANICAL_IDS.has(candidate.mechanicalLoad) &&
    typeof candidate.timeWindow === "string" && TIME_WINDOW_IDS.has(candidate.timeWindow)
  );
}

const WINDOW_NOTE_KERAMIK =
  "Rüttelkeramik ist in einem Wochenendfenster unter 48 h nur in Bauabschnitten realisierbar – die Taktung wird im Vor-Ort-Audit festgelegt.";
const WINDOW_NOTE_WHG =
  "Eine WHG-Fachbeschichtung benötigt Untergrundvorbereitung, Dichtheitsprüfung und Dokumentation – ein Wochenendfenster reicht nur für Teilflächen.";

/**
 * Deterministische Systemauslegung: geordnete Regeln, erste zutreffende gewinnt.
 * 1. Heißdampf > 100 °C          -> Rüttelkeramik (Reaktionsharzsysteme thermisch begrenzt)
 * 2. Schwerlast > 30 N/mm²       -> Rüttelkeramik (Druck-/Punktlastfestigkeit)
 * 3. Anorganische Säuren pH 0–2  -> mit Thermoschock: Rüttelkeramik, sonst WHG § 62 Fachbeschichtung
 * 4. Wochenendfenster < 48 h     -> PU-Beton (schnell härtend)
 * 5. Fette / Öle                 -> PU-Beton (fugenarm, fettbeständig)
 * 6. Organische Säuren / Laugen  -> Rüttelkeramik (Kunstharzfuge, pH 0–14)
 */
export function resolveStressSystem(input: StressCheckInput): StressCheckResult {
  const reasons: string[] = [];
  const weekend = input.timeWindow === "wochenende-48h";

  if (input.tempRange === "heissdampf-100") {
    reasons.push("Heißdampf über 100 °C liegt über der thermischen Dauerbelastbarkeit von Reaktionsharz-Systemen; Rüttelkeramik mit Kunstharzfuge bleibt formstabil.");
    if (input.mechanicalLoad === "schwerlast-vulkollan") reasons.push("Punktlasten über 30 N/mm² aus Vulkollanrollen werden von der keramischen Rüttelverlegung abgetragen.");
    return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons, windowNote: weekend ? WINDOW_NOTE_KERAMIK : undefined };
  }

  if (input.mechanicalLoad === "schwerlast-vulkollan") {
    reasons.push("Punktlasten über 30 N/mm² aus Vulkollanrollen erfordern die Druckfestigkeit keramischer Rüttelbeläge nach DIN EN 14411.");
    if (input.medium === "anorganische-saeuren") reasons.push("Anorganische Säuren im pH-Bereich 0–2 werden durch die Kunstharzfuge nach AGI S 40 dauerhaft abgetragen.");
    return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons, windowNote: weekend ? WINDOW_NOTE_KERAMIK : undefined };
  }

  if (input.medium === "anorganische-saeuren") {
    if (input.tempRange === "thermoschock-85") {
      reasons.push("Die Kombination aus anorganischen Säuren (pH 0–2) und Thermoschock bis 85 °C überfordert Beschichtungen; Rüttelkeramik mit Kunstharzfuge nach AGI S 40 ist hier Stand der Technik.");
      return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons, windowNote: weekend ? WINDOW_NOTE_KERAMIK : undefined };
    }
    reasons.push("Anorganische Säuren im pH-Bereich 0–2 fallen unter § 62 WHG; die Fachbeschichtung liefert Dichtheit, Beständigkeit und die behördlich geforderte Dokumentation.");
    if (input.mechanicalLoad === "gabelstapler-3-5t") reasons.push("Staplerverkehr bis 5 t wird durch einen verschleißfesten Deckversiegelungsaufbau abgedeckt.");
    return { system: STRESS_SYSTEMS["whg-fachbeschichtung"], reasons, windowNote: weekend ? WINDOW_NOTE_WHG : undefined };
  }

  if (weekend) {
    reasons.push("Ein Wochenendfenster unter 48 h erlaubt nur schnell härtende Systeme; PU-Beton ist nach kurzer Zeit befahrbar und voll belastbar.");
    if (input.tempRange === "thermoschock-85") reasons.push("PU-Beton ist bis 120 °C thermoschockbeständig und übersteht CIP-Reinigung bis 85 °C.");
    if (input.medium !== "fette-oele") reasons.push("Organische Säuren und Laugen werden im Konzentrationsbereich der Lebensmittelproduktion dauerhaft abgetragen.");
    return { system: STRESS_SYSTEMS["pu-beton-hochtemperatur"], reasons };
  }

  if (input.medium === "fette-oele") {
    reasons.push("Fette und Öle verlangen eine fugenarme, porenfreie Oberfläche; PU-Beton verhindert Unterwanderung und Keimnester.");
    if (input.tempRange === "thermoschock-85") reasons.push("PU-Beton ist bis 120 °C thermoschockbeständig und übersteht CIP-Reinigung bis 85 °C.");
    return { system: STRESS_SYSTEMS["pu-beton-hochtemperatur"], reasons };
  }

  reasons.push("Milchsäure, Fruchtsäuren und CIP-Laugen greifen zementöse und viele Reaktionsharz-Fugen an; die Kunstharzfuge nach AGI S 40 deckt pH 0–14 dauerhaft ab.");
  if (input.tempRange === "thermoschock-85") reasons.push("Thermoschock bis 85 °C wird durch die keramische Rüttelverlegung ohne Haftverbund-Verlust aufgenommen.");
  if (input.mechanicalLoad === "gabelstapler-3-5t") reasons.push("Staplerverkehr bis 5 t liegt innerhalb der Druckfestigkeit von Rüttelkeramik nach DIN EN 14411.");
  if (input.timeWindow === "neubau") reasons.push("Im Neubau kann Gefälle- und Rinnenplanung direkt in die keramische Fläche integriert werden.");
  return { system: STRESS_SYSTEMS["agi-s40-ruettelkeramik"], reasons };
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `npx vitest run tests/stress-matrix.test.ts`
Expected: PASS (10 Tests).

- [ ] **Step 5: Commit**

```bash
git add apps/website/src/data/stressMatrix.ts apps/website/tests/stress-matrix.test.ts
git commit -m "feat(website): deterministische Beanspruchungs-Matrix mit 180 geprüften Kombinationen"
```

---

### Task 5: Übergabe an das Audit-Formular (`stressCheckHandoff.ts` + `LeadForm.astro`)

**Files:**
- Create: `apps/website/src/lib/stressCheckHandoff.ts`
- Modify: `apps/website/src/components/forms/LeadForm.astro` (Prefill-Listener, `any` entfernen)
- Test: `apps/website/tests/stress-check-handoff.test.ts`

**Interfaces:**
- Consumes: `StressCheckInput`, `StressCheckResult`, `STRESS_*` aus Task 4; `loadOptions` aus `validation.ts`.
- Produces: `STRESS_CHECK_STORAGE_KEY = "hsb-stresscheck-v1"`, `STRESS_CHECK_EVENT = "hsb:stresscheck"`, `interface LeadPrefill { loads: string[]; projectType: "neubau" | "sanierung"; liveOperation: "ja" | "nein"; message: string; recommendedSystem: StressSystemId; input: StressCheckInput }`, `buildLeadPrefill(input, result): LeadPrefill`, `saveStressCheckHandoff(storage: Storage, prefill: LeadPrefill): void`, `loadStressCheckHandoff(storage: Storage): LeadPrefill | undefined`, `clearStressCheckHandoff(storage: Storage): void`.

- [ ] **Step 1: Test schreiben**

```ts
// tests/stress-check-handoff.test.ts
// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from "vitest";
import { resolveStressSystem } from "../src/data/stressMatrix";
import {
  STRESS_CHECK_STORAGE_KEY,
  buildLeadPrefill,
  clearStressCheckHandoff,
  loadStressCheckHandoff,
  saveStressCheckHandoff,
} from "../src/lib/stressCheckHandoff";
import { loadOptions } from "../src/lib/validation";

const input = {
  medium: "milchsaeure-molke",
  tempRange: "thermoschock-85",
  mechanicalLoad: "gabelstapler-3-5t",
  timeWindow: "revision-7-14d",
} as const;

beforeEach(() => sessionStorage.clear());

describe("Beanspruchungs-Check → Audit-Formular", () => {
  it("bildet nur Belastungen ab, die das Formular kennt", () => {
    const prefill = buildLeadPrefill(input, resolveStressSystem(input));
    for (const load of prefill.loads) expect(loadOptions).toContain(load);
    expect(prefill.loads).toEqual(expect.arrayContaining(["Säuren/Laugen", "Temperaturwechsel", "Staplerverkehr"]));
  });

  it("leitet Projektart und laufenden Betrieb aus dem Sanierungsfenster ab", () => {
    expect(buildLeadPrefill(input, resolveStressSystem(input)).projectType).toBe("sanierung");
    expect(buildLeadPrefill(input, resolveStressSystem(input)).liveOperation).toBe("ja");
    const neubau = { ...input, timeWindow: "neubau" } as const;
    expect(buildLeadPrefill(neubau, resolveStressSystem(neubau)).projectType).toBe("neubau");
    expect(buildLeadPrefill(neubau, resolveStressSystem(neubau)).liveOperation).toBe("nein");
  });

  it("erzeugt eine technische Nachricht mit allen vier Parametern und dem System", () => {
    const prefill = buildLeadPrefill(input, resolveStressSystem(input));
    expect(prefill.message).toContain("Milchsäure / Molke");
    expect(prefill.message).toContain("Thermoschock / CIP-Reinigung bis 85 °C");
    expect(prefill.message).toContain("Gabelstapler 3–5 t");
    expect(prefill.message).toContain("Revisionsstillstand (7–14 Tage)");
    expect(prefill.message).toContain("AGI S 40 Vibro-Rüttelkeramik mit Kunstharzfuge");
    expect(prefill.message.length).toBeLessThanOrEqual(2000);
  });

  it("überlebt den Seitenwechsel per sessionStorage und lehnt manipulierte Daten ab", () => {
    const prefill = buildLeadPrefill(input, resolveStressSystem(input));
    saveStressCheckHandoff(sessionStorage, prefill);
    expect(loadStressCheckHandoff(sessionStorage)).toEqual(prefill);

    sessionStorage.setItem(STRESS_CHECK_STORAGE_KEY, JSON.stringify({ ...prefill, loads: ["<img>"] }));
    expect(loadStressCheckHandoff(sessionStorage)).toBeUndefined();

    clearStressCheckHandoff(sessionStorage);
    expect(sessionStorage.getItem(STRESS_CHECK_STORAGE_KEY)).toBeNull();
  });
});
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `npx vitest run tests/stress-check-handoff.test.ts`
Expected: FAIL — Modul fehlt.

- [ ] **Step 3: Implementieren**

```ts
// src/lib/stressCheckHandoff.ts
import {
  STRESS_MECHANICAL,
  STRESS_MEDIA,
  STRESS_SYSTEMS,
  STRESS_TEMPERATURES,
  STRESS_TIME_WINDOWS,
  isStressCheckInput,
  type StressCheckInput,
  type StressCheckResult,
  type StressSystemId,
} from "../data/stressMatrix";
import { loadOptions } from "./validation";

export const STRESS_CHECK_STORAGE_KEY = "hsb-stresscheck-v1";
export const STRESS_CHECK_EVENT = "hsb:stresscheck";

export interface LeadPrefill {
  loads: string[];
  projectType: "neubau" | "sanierung";
  liveOperation: "ja" | "nein";
  message: string;
  recommendedSystem: StressSystemId;
  input: StressCheckInput;
}

type LoadOption = (typeof loadOptions)[number];
const LOAD_OPTION_SET = new Set<string>(loadOptions);

function labelOf<Id extends string>(options: readonly { id: Id; label: string }[], id: Id): string {
  return options.find((option) => option.id === id)?.label ?? id;
}

// Abbildung der Check-Parameter auf die im Formular vorhandenen Belastungen
// (validation.ts: loadOptions). Es werden keine neuen Optionen erfunden.
function mapLoads(input: StressCheckInput): LoadOption[] {
  const loads = new Set<LoadOption>();
  loads.add(input.medium === "fette-oele" ? "Fette/Öle" : "Säuren/Laugen");
  if (input.medium === "cip-laugen") loads.add("Hochdruckreinigung");
  if (input.tempRange === "dauernass-kalt") loads.add("Nassbereich");
  else loads.add("Temperaturwechsel");
  if (input.mechanicalLoad !== "handhubwagen") loads.add("Staplerverkehr");
  return [...loads];
}

export function buildLeadPrefill(input: StressCheckInput, result: StressCheckResult): LeadPrefill {
  const isNeubau = input.timeWindow === "neubau";
  const message = [
    "Technischer Beanspruchungs-Check (Website):",
    `Chemisches Medium: ${labelOf(STRESS_MEDIA, input.medium)}`,
    `Thermische Belastung: ${labelOf(STRESS_TEMPERATURES, input.tempRange)}`,
    `Mechanische Last: ${labelOf(STRESS_MECHANICAL, input.mechanicalLoad)}`,
    `Sanierungsfenster: ${labelOf(STRESS_TIME_WINDOWS, input.timeWindow)}`,
    `Vorläufige Systemempfehlung: ${result.system.name}`,
    "",
    "Bitte um Terminvorschlag für ein qualifiziertes Vor-Ort-Audit.",
  ].join("\n");

  return {
    loads: mapLoads(input),
    projectType: isNeubau ? "neubau" : "sanierung",
    liveOperation: isNeubau ? "nein" : "ja",
    message,
    recommendedSystem: result.system.id,
    input,
  };
}

function isLeadPrefill(value: unknown): value is LeadPrefill {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    Array.isArray(candidate.loads) &&
    candidate.loads.every((load) => typeof load === "string" && LOAD_OPTION_SET.has(load)) &&
    (candidate.projectType === "neubau" || candidate.projectType === "sanierung") &&
    (candidate.liveOperation === "ja" || candidate.liveOperation === "nein") &&
    typeof candidate.message === "string" && candidate.message.length <= 2000 &&
    typeof candidate.recommendedSystem === "string" && candidate.recommendedSystem in STRESS_SYSTEMS &&
    isStressCheckInput(candidate.input)
  );
}

export function saveStressCheckHandoff(storage: Storage, prefill: LeadPrefill): void {
  try {
    storage.setItem(STRESS_CHECK_STORAGE_KEY, JSON.stringify(prefill));
  } catch {
    // Storage blockiert: Übergabe läuft dann nur über das DOM-Event.
  }
}

export function loadStressCheckHandoff(storage: Storage): LeadPrefill | undefined {
  try {
    const raw = storage.getItem(STRESS_CHECK_STORAGE_KEY);
    if (raw === null) return undefined;
    const parsed: unknown = JSON.parse(raw);
    return isLeadPrefill(parsed) ? parsed : undefined;
  } catch {
    return undefined;
  }
}

export function clearStressCheckHandoff(storage: Storage): void {
  try {
    storage.removeItem(STRESS_CHECK_STORAGE_KEY);
  } catch {
    // Storage blockiert: nichts zu löschen.
  }
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `npx vitest run tests/stress-check-handoff.test.ts`
Expected: PASS (4 Tests).

- [ ] **Step 5: `LeadForm.astro` um Prefill erweitern**

Im `<script>`-Block Importe ergänzen:

```ts
  import {
    STRESS_CHECK_EVENT,
    clearStressCheckHandoff,
    loadStressCheckHandoff,
    type LeadPrefill,
  } from "../../lib/stressCheckHandoff";
```

`const payload: Record<string, any> = {` → `const payload: Record<string, unknown> = {`.

Vor `form?.addEventListener("focusin", ...)` einfügen:

```ts
  // Übergabe aus dem Beanspruchungs-Check: Belastungen, Projektart, Betrieb
  // und technische Nachricht vorbelegen. Personenfelder bleiben leer.
  function applyPrefill(prefill: LeadPrefill) {
    if (!form) return;
    form.querySelectorAll<HTMLInputElement>('input[name="loads"]').forEach((box) => {
      box.checked = prefill.loads.includes(box.value);
    });
    const projectType = form.elements.namedItem("projectType");
    if (projectType instanceof HTMLSelectElement) projectType.value = prefill.projectType;
    const liveOperation = form.elements.namedItem("liveOperation");
    if (liveOperation instanceof HTMLSelectElement) liveOperation.value = prefill.liveOperation;
    const message = form.elements.namedItem("message");
    if (message instanceof HTMLTextAreaElement && message.value.trim() === "") message.value = prefill.message;
    form.dataset.stressCheckSystem = prefill.recommendedSystem;
  }

  window.addEventListener(STRESS_CHECK_EVENT, (event) => {
    const detail = (event as CustomEvent<LeadPrefill>).detail;
    if (detail) applyPrefill(detail);
  });

  try {
    const stored = loadStressCheckHandoff(window.sessionStorage);
    if (stored) {
      applyPrefill(stored);
      clearStressCheckHandoff(window.sessionStorage);
    }
  } catch {
    // sessionStorage blockiert: Formular bleibt unbefüllt nutzbar.
  }
```

- [ ] **Step 6: Typprüfung + Formular-Tests**

Run: `npx astro check && npx vitest run tests/form.test.ts tests/lead-form-autocomplete.test.ts tests/stress-check-handoff.test.ts`
Expected: 0 errors, PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/website/src/lib/stressCheckHandoff.ts apps/website/src/components/forms/LeadForm.astro apps/website/tests/stress-check-handoff.test.ts
git commit -m "feat(website): Beanspruchungs-Check-Übergabe an das Audit-Anfrageformular"
```

---

### Task 6: `StressCheck.astro` und Seite `/beanspruchungs-check/`

**Files:**
- Create: `apps/website/src/components/forms/StressCheck.astro`
- Create: `apps/website/src/pages/beanspruchungs-check/index.astro`
- Modify: `apps/website/src/lib/content.ts` (`getAllPublicPages`: neue Route)
- Modify: `apps/website/src/pages/branchen/[slug].astro` (Link zum Check)
- Modify: `apps/website/src/pages/kontakt/index.astro` (Hinweis auf den Check)

**Interfaces:**
- Consumes: Task 2 (`trackStressCheck`, `trackB2BConversion`, `trackNormInteraction`), Task 4 (`STRESS_*`, `resolveStressSystem`, `isStressCheckInput`), Task 5 (`buildLeadPrefill`, `saveStressCheckHandoff`, `STRESS_CHECK_EVENT`), Task 1 (`executionStandards`).

- [ ] **Step 1: Komponente schreiben**

```astro
---
// src/components/forms/StressCheck.astro
import { executionStandards } from "../../data/standards";
import {
  STRESS_MECHANICAL,
  STRESS_MEDIA,
  STRESS_SYSTEMS,
  STRESS_TEMPERATURES,
  STRESS_TIME_WINDOWS,
} from "../../data/stressMatrix";

interface Props {
  auditAnchor?: string;
}

const { auditAnchor = "#kontaktformular" } = Astro.props;

const steps = [
  { key: "medium", number: 1, title: "Chemisches Medium", question: "Welches Medium wirkt dauerhaft auf die Fläche ein?", options: STRESS_MEDIA },
  { key: "tempRange", number: 2, title: "Thermische Belastung", question: "Welche Temperaturbelastung tritt im Betrieb auf?", options: STRESS_TEMPERATURES },
  { key: "mechanicalLoad", number: 3, title: "Mechanische Last", question: "Welche Flurförderzeuge befahren die Fläche?", options: STRESS_MECHANICAL },
  { key: "timeWindow", number: 4, title: "Sanierungsfenster", question: "Welches Zeitfenster steht für die Ausführung zur Verfügung?", options: STRESS_TIME_WINDOWS },
] as const;

const systems = Object.values(STRESS_SYSTEMS);
---

<section class="section bg-hsb-mist" id="beanspruchungs-check" data-stress-check data-audit-anchor={auditAnchor}>
  <div class="container max-w-5xl">
    <p class="eyebrow">Technischer Beanspruchungs-Check</p>
    <h2 class="h2 mt-3">Vier Parameter, eine deterministische Systemempfehlung</h2>
    <p class="lead mt-4 max-w-3xl">
      Für Werks- und Betriebsleiter: Medium, Temperatur, mechanische Last und Stillstandsfenster bestimmen das Bodensystem. Die Auswertung folgt festen ingenieurtechnischen Regeln und ersetzt kein Vor-Ort-Audit.
    </p>

    <form class="mt-10 grid gap-6" data-stress-form novalidate>
      {steps.map((step) => (
        <fieldset class="surface grid gap-4 p-6" data-step={step.number}>
          <legend class="flex items-center gap-3 text-sm font-black uppercase tracking-[0.14em] text-hsb-red">
            <span class="grid size-7 place-items-center rounded-full bg-hsb-black text-xs text-white" aria-hidden="true">{step.number}</span>
            {step.title}
          </legend>
          <p class="text-base font-bold text-hsb-black">{step.question}</p>
          <div class="grid gap-2 sm:grid-cols-2">
            {step.options.map((option) => (
              <label class="flex cursor-pointer items-start gap-3 rounded border border-hsb-line bg-white px-4 py-3 text-sm leading-6 transition-colors has-[:checked]:border-hsb-red has-[:checked]:bg-hsb-red/5">
                <input type="radio" name={step.key} value={option.id} required class="mt-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red" />
                <span>
                  <span class="block font-bold text-hsb-black">{option.label}</span>
                  {"hint" in option && option.hint ? <span class="block text-xs text-hsb-steel">{option.hint}</span> : null}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}

      <p data-stress-error role="alert" aria-live="assertive" class="hidden rounded border border-hsb-red/40 bg-hsb-red/5 px-3 py-2 text-sm text-hsb-red">
        Bitte beantworten Sie alle vier Parameter, damit die Systemempfehlung berechnet werden kann.
      </p>

      <div class="flex flex-wrap gap-3">
        <button type="submit" class="button-primary">Systemempfehlung berechnen</button>
        <button type="reset" class="button-secondary" data-stress-reset>Zurücksetzen</button>
      </div>
    </form>

    <div class="mt-10 hidden" data-stress-result aria-live="polite">
      {systems.map((system) => (
        <article class="surface hidden gap-5 p-6 lg:p-8" data-system={system.id}>
          <p class="eyebrow">Vorläufige Systemempfehlung</p>
          <h3 class="h2 mt-2">{system.name}</h3>
          <p class="mt-3 text-base leading-8 text-hsb-steel">{system.description}</p>
          <div>
            <p class="text-sm font-black uppercase tracking-[0.14em] text-hsb-black">Technische Begründung</p>
            <ul class="mt-3 grid gap-2 text-sm leading-7 text-hsb-steel" data-reasons></ul>
            <p class="mt-3 hidden rounded border border-hsb-line bg-hsb-mist px-4 py-3 text-sm leading-6 text-hsb-black" data-window-note></p>
          </div>
          {system.norms.length > 0 && (
            <div class="grid gap-2">
              <p class="text-sm font-black uppercase tracking-[0.14em] text-hsb-black">Ausführungsgrundlage</p>
              {system.norms.map((normId) => {
                const standard = executionStandards.find((item) => item.id === normId);
                return standard ? (
                  <details class="rounded border border-hsb-line bg-white px-4 py-3" data-norm={standard.id}>
                    <summary class="cursor-pointer text-sm font-bold text-hsb-black">{standard.name}</summary>
                    <p class="mt-2 text-sm leading-6 text-hsb-steel">{standard.scope}</p>
                  </details>
                ) : null;
              })}
            </div>
          )}
          <div class="flex flex-wrap gap-3">
            <a class="button-primary" href={auditAnchor} data-audit-cta>Qualifiziertes Vor-Ort-Audit anfragen</a>
            <a class="button-secondary" href={`/leistungen/${system.serviceSlug}/`}>Systemdetails ansehen</a>
          </div>
        </article>
      ))}
    </div>
  </div>
</section>

<script>
  import { trackB2BConversion, trackNormInteraction, trackStressCheck } from "../../lib/analytics";
  import { NORM_IDS, type NormId } from "../../data/standards";
  import { isStressCheckInput, resolveStressSystem, type StressCheckInput, type StressCheckResult } from "../../data/stressMatrix";
  import { STRESS_CHECK_EVENT, buildLeadPrefill, saveStressCheckHandoff } from "../../lib/stressCheckHandoff";

  const root = document.querySelector<HTMLElement>("[data-stress-check]");
  const form = root?.querySelector<HTMLFormElement>("[data-stress-form]");
  const error = root?.querySelector<HTMLElement>("[data-stress-error]");
  const resultContainer = root?.querySelector<HTMLElement>("[data-stress-result]");

  const STEP_KEYS = ["medium", "tempRange", "mechanicalLoad", "timeWindow"] as const;
  type StepKey = (typeof STEP_KEYS)[number];

  function readInput(): Partial<Record<StepKey, string>> {
    if (!form) return {};
    const data = new FormData(form);
    const partial: Partial<Record<StepKey, string>> = {};
    for (const key of STEP_KEYS) {
      const value = data.get(key);
      if (typeof value === "string" && value !== "") partial[key] = value;
    }
    return partial;
  }

  function isNormId(value: string): value is NormId {
    return (NORM_IDS as readonly string[]).includes(value);
  }

  // Jeder abgeschlossene Schritt meldet seinen Stand (1–4), das Ergebnis Schritt 5.
  form?.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || target.type !== "radio") return;
    const stepNumber = Number(target.closest<HTMLElement>("[data-step]")?.dataset.step ?? "0");
    if (stepNumber < 1) return;
    const partial = readInput();
    trackStressCheck(stepNumber, {
      medium: partial.medium,
      tempRange: partial.tempRange,
      mechanicalLoad: partial.mechanicalLoad,
      timeWindow: partial.timeWindow,
    });
  });

  function render(input: StressCheckInput, result: StressCheckResult) {
    if (!resultContainer) return;
    resultContainer.querySelectorAll<HTMLElement>("[data-system]").forEach((card) => {
      const active = card.dataset.system === result.system.id;
      card.classList.toggle("hidden", !active);
      card.classList.toggle("grid", active);
      if (!active) return;

      const list = card.querySelector<HTMLElement>("[data-reasons]");
      if (list) {
        list.replaceChildren(
          ...result.reasons.map((reason) => {
            const item = document.createElement("li");
            item.className = "flex items-start gap-3";
            const marker = document.createElement("span");
            marker.className = "mt-2.5 size-1.5 shrink-0 rounded-full bg-hsb-red";
            marker.setAttribute("aria-hidden", "true");
            const text = document.createElement("span");
            text.textContent = reason;
            item.append(marker, text);
            return item;
          }),
        );
      }

      const note = card.querySelector<HTMLElement>("[data-window-note]");
      if (note) {
        note.textContent = result.windowNote ?? "";
        note.classList.toggle("hidden", !result.windowNote);
      }

      const cta = card.querySelector<HTMLAnchorElement>("[data-audit-cta]");
      cta?.addEventListener(
        "click",
        () => {
          const prefill = buildLeadPrefill(input, result);
          trackB2BConversion("audit_request", {
            placement: "stress_check",
            medium: input.medium,
            temp_range: input.tempRange,
            mechanical_load: input.mechanicalLoad,
            time_window: input.timeWindow,
            recommended_system: result.system.id,
          });
          try {
            saveStressCheckHandoff(window.sessionStorage, prefill);
          } catch {
            // Storage blockiert: DOM-Event reicht auf derselben Seite.
          }
          window.dispatchEvent(new CustomEvent(STRESS_CHECK_EVENT, { detail: prefill }));
        },
        { once: true },
      );
    });

    resultContainer.classList.remove("hidden");
    resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const partial = readInput();
    if (!isStressCheckInput(partial)) {
      error?.classList.remove("hidden");
      form.querySelector<HTMLInputElement>("input[type=radio]:not(:checked)")?.focus();
      return;
    }
    error?.classList.add("hidden");
    const result = resolveStressSystem(partial);
    trackStressCheck(5, { ...partial, recommendedSystem: result.system.id });
    render(partial, result);
  });

  form?.addEventListener("reset", () => {
    error?.classList.add("hidden");
    resultContainer?.classList.add("hidden");
  });

  resultContainer?.querySelectorAll<HTMLDetailsElement>("[data-norm]").forEach((details) => {
    details.addEventListener("toggle", () => {
      const norm = details.dataset.norm ?? "";
      if (details.open && isNormId(norm)) trackNormInteraction(norm, "expand");
    });
  });
</script>
```

Hinweis zu `has-[:checked]:` — Tailwind-4-Variante, im Projekt verfügbar (Tailwind ^4.0.0). Falls der Build die Klasse nicht erzeugt: Alternative `peer`/`peer-checked` verwenden.

- [ ] **Step 2: Seite anlegen**

```astro
---
// src/pages/beanspruchungs-check/index.astro
import LeadFormSection from "../../components/forms/LeadFormSection.astro";
import StressCheck from "../../components/forms/StressCheck.astro";
import PageHero from "../../components/sections/PageHero.astro";
import BaseLayout from "../../layouts/BaseLayout.astro";
import { buildBreadcrumbJsonLd } from "../../lib/schema";

export const prerender = true;

const path = "/beanspruchungs-check/";
const title = "Beanspruchungs-Check für Industrieböden | HSB Hexagon";
const description =
  "Medium, Temperatur, mechanische Last und Sanierungsfenster eingeben – deterministische Systemempfehlung nach AGI S 40, PU-Beton oder WHG § 62 mit direktem Vor-Ort-Audit.";
---

<BaseLayout title={title} description={description} path={path} jsonLd={[buildBreadcrumbJsonLd([{ name: "Start", path: "/" }, { name: "Beanspruchungs-Check", path }])]}>
  <PageHero
    eyebrow="Ingenieurbau"
    title="Technischer Beanspruchungs-Check für Produktionsböden"
    text="Vier betriebliche Parameter entscheiden über Rüttelkeramik nach AGI S 40, Hochtemperatur-PU-Beton oder eine WHG § 62 Fachbeschichtung. Das Ergebnis geht direkt in eine qualifizierte Audit-Anfrage über."
    ctaLabel="Check starten"
    ctaHref="#beanspruchungs-check"
  />
  <StressCheck auditAnchor="#kontaktformular" />
  <LeadFormSection />
</BaseLayout>
```

- [ ] **Step 3: Route in `getAllPublicPages` eintragen**

In `src/lib/content.ts` nach dem `/kontakt/`-Eintrag einfügen:

```ts
    {
      h1: "Technischer Beanspruchungs-Check für Produktionsböden",
      seoTitle: "Beanspruchungs-Check für Industrieböden | HSB Hexagon",
      description:
        "Medium, Temperatur, mechanische Last und Sanierungsfenster eingeben – deterministische Systemempfehlung nach AGI S 40, PU-Beton oder WHG § 62 mit direktem Vor-Ort-Audit.",
      canonicalPath: "/beanspruchungs-check/",
    },
```

- [ ] **Step 4: Verlinkung**

`src/pages/branchen/[slug].astro` — im Abschnitt „Empfohlene Leistungsbereiche" nach dem `grid-auto`-Block einfügen:

```astro
      <div class="mt-8 flex flex-wrap items-center justify-between gap-4 rounded-[4px] border border-hsb-line bg-white px-6 py-5">
        <p class="text-sm leading-7 text-hsb-steel"><strong class="text-hsb-black">Welches System passt zu Ihrer Belastung?</strong> Medium, Temperatur, Last und Stillstandsfenster in vier Schritten prüfen.</p>
        <a class="button-primary" href="/beanspruchungs-check/">Beanspruchungs-Check starten</a>
      </div>
```

`src/pages/kontakt/index.astro` — Hero-Text um Hinweis ergänzen (Prop `text`):

```
Je präziser Belastung, Fläche und Produktionsfenster beschrieben werden, desto besser kann HSB den passenden nächsten Schritt einschätzen. Für eine vorstrukturierte Anfrage steht der technische Beanspruchungs-Check unter /beanspruchungs-check/ bereit.
```

(Der Link im Fließtext ist unter `PageHero` nicht als Anchor möglich — daher zusätzlich unterhalb des Hero eine Zeile:)

```astro
  <section class="section-tight">
    <div class="container">
      <a class="button-secondary" href="/beanspruchungs-check/">Vorab: Technischen Beanspruchungs-Check durchführen</a>
    </div>
  </section>
```

- [ ] **Step 5: Typprüfung, Tests, Build**

Run: `npx astro check && npx vitest run && npm run build && npm run check:sitemap`
Expected: 0 errors, alle Tests grün, Build enthält `dist/beanspruchungs-check/index.html`, Sitemap konsistent.

- [ ] **Step 6: Rendering prüfen**

```bash
grep -c "data-stress-check" dist/beanspruchungs-check/index.html
grep -c "data-logo-cloud" dist/branchen/molkerei/index.html
grep -o 'data-client="[^"]*"' dist/branchen/molkerei/index.html | head -3
```

Expected: 1, 1, und Gropper/Meggle unter den ersten Einträgen.

- [ ] **Step 7: Commit**

```bash
git add apps/website/src/components/forms/StressCheck.astro apps/website/src/pages/beanspruchungs-check/index.astro apps/website/src/lib/content.ts "apps/website/src/pages/branchen/[slug].astro" apps/website/src/pages/kontakt/index.astro
git commit -m "feat(website): interaktiver Beanspruchungs-Check mit Audit-Übergabe und Seite /beanspruchungs-check/"
```

---

### Task 7: Schema.org-Upgrade und Meta-Schärfung

**Files:**
- Modify: `apps/website/src/lib/schema.ts` (Organization: `hasCredential`, `knowsAbout`-Normen; Service: `standards`)
- Modify: `apps/website/src/components/seo/SEOHead.astro` (Description-Fallback, Organization bleibt global)
- Modify: `apps/website/src/pages/leistungen/[slug].astro` (Standards an Service-Schema)
- Modify: `apps/website/src/data/site.ts`, `apps/website/src/lib/content.ts` (Titles/Descriptions), `apps/website/src/pages/kontakt/index.astro`
- Modify: `apps/website/src/data/homepageFaqs.ts:16`, `apps/website/src/data/services/boden-reparatur-instandsetzung.ts:58` (Floskeln)
- Test: `apps/website/tests/b2b-schema.test.ts` (Teil 2), `apps/website/tests/b2b-meta.test.ts`

- [ ] **Step 1: Tests schreiben**

An `tests/b2b-schema.test.ts` anhängen:

```ts
import { buildOrganizationJsonLd, buildServiceJsonLd } from "../src/lib/schema";

describe("Schema.org-Normen", () => {
  it("führt Normen als Wissen und nur den WHG-Fachbetrieb als Credential", () => {
    const graph = buildOrganizationJsonLd();
    const blob = JSON.stringify(graph);
    expect(graph.knowsAbout).toEqual(expect.arrayContaining([
      "AGI S 40 Säureschutzbau (keramische Beläge)",
      "DIN EN 14411 Keramische Fliesen und Platten",
      "§ 62 WHG / AwSV Anlagen mit wassergefährdenden Stoffen",
    ]));
    expect(graph.hasCredential).toHaveLength(1);
    expect(graph.hasCredential[0].name).toBe("Fachbetrieb nach § 62 WHG / AwSV");
    expect(blob).not.toMatch(/"hasCredential":\[[^\]]*AGI S 40/);
    expect(blob).not.toMatch(/"hasCredential":\[[^\]]*DIN EN 14411/);
  });

  it("hängt Ausführungsnormen als additionalProperty an das Service-Schema", () => {
    const graph = buildServiceJsonLd({
      name: "Keramische Industrieböden",
      description: "Rüttelkeramik nach AGI S 40 für produktionskritische Bereiche.",
      path: "/leistungen/keramische-industrieboeden/",
      standards: ["AGI S 40", "DIN EN 14411"],
    });
    expect(graph.additionalProperty).toEqual([
      { "@type": "PropertyValue", name: "Ausführungsgrundlage", value: "AGI S 40" },
      { "@type": "PropertyValue", name: "Ausführungsgrundlage", value: "DIN EN 14411" },
    ]);
    expect(graph.provider.hasCredential?.[0].name).toBe("Fachbetrieb nach § 62 WHG / AwSV");
  });

  it("lässt Service-Schema ohne Normen unverändert schlank", () => {
    const graph = buildServiceJsonLd({ name: "Reparatur", description: "Instandsetzung.", path: "/leistungen/boden-reparatur-instandsetzung/" });
    expect(graph.additionalProperty).toBeUndefined();
  });
});
```

```ts
// tests/b2b-meta.test.ts
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { getAllPublicPages, getIndustries, getServices } from "../src/lib/content";
import { site } from "../src/data/site";
import { homepageFaqs } from "../src/data/homepageFaqs";

const HANDWERKER_PATTERNS = [/€\s*\/?\s*m²/i, /pro m²/i, /Quadratmeterpreis/i, /qm-Preis/i, /deutlich günstiger/i, /billig/i, /preiswert/i];

describe("B2B-Positionierung der Metadaten", () => {
  it("nennt in Titles und Descriptions keine Quadratmeterpreise oder Handwerker-Floskeln", () => {
    const blobs = [
      ...getAllPublicPages().flatMap((page) => [page.seoTitle, page.description, page.h1]),
      ...getIndustries().flatMap((industry) => [industry.seoTitle, industry.description]),
      ...getServices().flatMap((service) => [service.seoTitle, service.description]),
      ...homepageFaqs.flatMap((faq) => [faq.question, faq.answer]),
    ];
    for (const blob of blobs) for (const pattern of HANDWERKER_PATTERNS) expect(blob).not.toMatch(pattern);
  });

  it("hält neue statische Titles unter 60 und Descriptions unter 160 Zeichen", () => {
    const targets = ["/", "/leistungen/", "/kontakt/", "/beanspruchungs-check/"];
    for (const page of getAllPublicPages().filter((item) => targets.includes(item.canonicalPath))) {
      expect(page.seoTitle.length, page.canonicalPath).toBeLessThanOrEqual(60);
      expect(page.description.length, page.canonicalPath).toBeLessThanOrEqual(160);
    }
    expect(site.defaultTitle.length).toBeLessThanOrEqual(60);
    expect(site.defaultDescription.length).toBeLessThanOrEqual(160);
  });

  it("positioniert die Startseite auf Ingenieurbau, Rüttelkeramik und Säureschutz", () => {
    expect(site.defaultTitle).toMatch(/Ingenieurbau/);
    expect(site.defaultTitle).toMatch(/Rüttelkeramik/);
    expect(site.defaultTitle).toMatch(/Säureschutz/);
    expect(getAllPublicPages()[0].seoTitle).toBe(site.defaultTitle);
  });

  it("hält Kontaktseite und Content-Registry auf demselben Title", () => {
    const source = readFileSync(join(process.cwd(), "src/pages/kontakt/index.astro"), "utf8");
    const registry = getAllPublicPages().find((page) => page.canonicalPath === "/kontakt/");
    expect(registry).toBeDefined();
    expect(source).toContain(`title="${registry?.seoTitle}"`);
  });
});
```

- [ ] **Step 2: Tests laufen lassen (müssen fehlschlagen)**

Run: `npx vitest run tests/b2b-schema.test.ts tests/b2b-meta.test.ts`
Expected: FAIL (knowsAbout/hasCredential fehlen, Titles enthalten kein „Ingenieurbau", „deutlich günstiger" vorhanden).

- [ ] **Step 3: `schema.ts` anpassen**

Import ergänzen:

```ts
import { executionStandards, organizationCredential, type NormId } from "../data/standards";
```

Hilfsfunktion oberhalb von `buildOrganizationJsonLd`:

```ts
function buildCredentialJsonLd() {
  return [
    {
      "@type": "EducationalOccupationalCredential",
      credentialCategory: organizationCredential.credentialCategory,
      name: organizationCredential.name,
    },
  ];
}

const NORM_KNOWLEDGE = [
  "AGI S 40 Säureschutzbau (keramische Beläge)",
  "DIN EN 14411 Keramische Fliesen und Platten",
  "§ 62 WHG / AwSV Anlagen mit wassergefährdenden Stoffen",
];
```

In `buildOrganizationJsonLd()` `knowsAbout` erweitern (`...NORM_KNOWLEDGE` anhängen) und nach `knowsAbout` einfügen: `hasCredential: buildCredentialJsonLd(),`.

`buildServiceJsonLd` Signatur und Body:

```ts
export function buildServiceJsonLd(service: {
  name: string;
  description: string;
  path: string;
  standards?: NormId[];
}) {
  const additionalProperty = service.standards?.length
    ? service.standards.map((standard) => ({
        "@type": "PropertyValue",
        name: "Ausführungsgrundlage",
        value: standard,
      }))
    : undefined;

  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: service.name,
    description: service.description,
    url: absoluteUrl(service.path),
    serviceType: service.name,
    areaServed: ["Deutschland", "Österreich", "Schweiz", "Europa"],
    ...(additionalProperty ? { additionalProperty } : {}),
    provider: {
      "@type": "Organization",
      name: "HSB Hexagon Säurebau GmbH",
      url: site.domain,
      hasCredential: buildCredentialJsonLd(),
      address: {
        "@type": "PostalAddress",
        streetAddress: "Benzstraße 6",
        postalCode: "48599",
        addressLocality: "Gronau",
        addressCountry: "DE",
      },
    },
  };
}
```

`executionStandards` wird für die `knowsAbout`-Beschreibung nicht zwingend benötigt; wenn ungenutzt, den Import auf `organizationCredential, type NormId` reduzieren (kein toter Import).

- [ ] **Step 4: `leistungen/[slug].astro`**

Import: `import { getStandardsForService } from "../../data/standards";`
Aufruf: `buildServiceJsonLd({ name: service.title, description: service.description, path, standards: getStandardsForService(service.slug) })`.

- [ ] **Step 5: `SEOHead.astro`**

Import `site`: `import { site } from "../../data/site";`
Zeile `const { title, description, ... }` → nach der Destrukturierung: `const resolvedDescription = description ?? site.defaultDescription;` und alle `content={description}` durch `content={resolvedDescription}` ersetzen (4 Stellen: meta description, og:description, twitter:description). Kommentar über dem JSON-LD-Block:

```astro
<!-- Organization-Schema global (mit owner-bestätigtem WHG-Fachbetrieb-Credential
     und Ausführungsnormen als knowsAbout); Service-Schema je Leistungsseite. -->
```

- [ ] **Step 6: Titles/Descriptions schärfen**

`src/data/site.ts`:

```ts
  defaultTitle: "Ingenieurbau, Rüttelkeramik & Säureschutz | HSB Hexagon",
  defaultDescription:
    "Ingenieurbau für Industrieböden: Rüttelkeramik nach AGI S 40, Säureschutz, PU-Beton und WHG § 62 Abdichtung für Lebensmittel-, Pharma- und Chemieproduktion.",
```

`src/lib/content.ts` `getAllPublicPages()`:
- `/`: `seoTitle: site.defaultTitle`, `description: site.defaultDescription` (Import `site` prüfen; falls nicht vorhanden: `import { site } from "../data/site";`).
- `/leistungen/`: `seoTitle: "Leistungen: Rüttelkeramik, Säureschutz & WHG | HSB Hexagon"`, `description: "Ingenieurbau für Industrieböden: keramische Rüttelbeläge nach AGI S 40, Säureschutz, PU-Beton, Epoxidharz, Entwässerung, WHG § 62 Abdichtung und Sanierung im Betrieb."`
- `/kontakt/`: `seoTitle: "Technisches Vor-Ort-Audit anfragen | HSB Hexagon Säurebau"`, `description: "Vor-Ort-Audit für Industrieböden: Belastungsprofil, Untergrund und Sanierungsfenster werden ingenieurseitig bewertet – Rüttelkeramik, Säureschutz, WHG-Abdichtung."`

`src/pages/kontakt/index.astro`: `title="Technisches Vor-Ort-Audit anfragen | HSB Hexagon Säurebau"` und `description` identisch zur Registry.

Zeichenlängen vor dem Commit messen:

```bash
node -e 'for (const s of ["Ingenieurbau, Rüttelkeramik & Säureschutz | HSB Hexagon","Leistungen: Rüttelkeramik, Säureschutz & WHG | HSB Hexagon","Technisches Vor-Ort-Audit anfragen | HSB Hexagon Säurebau","Beanspruchungs-Check für Industrieböden | HSB Hexagon"]) console.log(s.length, s)'
```

Expected: alle ≤ 60. Descriptions analog ≤ 160 (Test deckt es ab).

- [ ] **Step 7: Floskeln schärfen**

`src/data/homepageFaqs.ts:16`: „deutlich günstiger und schneller als eine Vollsanierung" → „wirtschaftlicher und mit kürzerer Sperrzeit als eine Vollsanierung".
`src/data/services/boden-reparatur-instandsetzung.ts:58`: „deutlich günstiger" → „wirtschaftlicher und mit kürzerer Sperrzeit" (Satz vorher vollständig lesen, Grammatik anpassen).

- [ ] **Step 8: Prüfen, ob Tests hart auf alte Titles verweisen**

Run: `grep -rn "Industrieböden & Säureschutz für Produktion\|Kontakt & Projektanfrage\|Leistungen für Industrieböden & Säureschutz" tests src`
Expected: keine Treffer außer ggf. Sprachseiten (`src/pages/en|fr|nl|pl|tr`) — die bleiben unverändert. Treffer in Tests: Erwartung auf neue Werte umstellen.

- [ ] **Step 9: Tests, Typprüfung**

Run: `npx astro check && npx vitest run`
Expected: 0 errors; alle Tests grün (inkl. `schema.test.ts`, `seo-completeness.test.ts`, `content-meta.test.ts`).

- [ ] **Step 10: Commit**

```bash
git add apps/website/src/lib/schema.ts apps/website/src/components/seo/SEOHead.astro "apps/website/src/pages/leistungen/[slug].astro" apps/website/src/data/site.ts apps/website/src/lib/content.ts apps/website/src/pages/kontakt/index.astro apps/website/src/data/homepageFaqs.ts apps/website/src/data/services/boden-reparatur-instandsetzung.ts apps/website/tests/b2b-schema.test.ts apps/website/tests/b2b-meta.test.ts
git commit -m "feat(website): Schema.org mit Ausführungsnormen und WHG-Credential, B2B-Metadaten geschärft"
```

---

### Task 8: Verifikations-Gate, Review, Pflichtabschluss

**Files:**
- Modify (Repo-Root): `CHECKPOINT_STATE.json`, `SESSION_LOG.md`, `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`
- Create: `~/KI-System/08_System/reports/validation/2026-09-17-hsb-b2b-tracking-stresscheck-schema.md`

- [ ] **Step 1: Gate ausführen (in `apps/website/`)**

```bash
npx astro check 2>&1 | tail -5
npm run build 2>&1 | tail -15
npm run test:run 2>&1 | tail -8
npm run check:sitemap
npm run deploy:dry-run 2>&1 | tail -5
```

Expected: 0 errors / 0 warnings; Build mit ≥ 51 Seiten (bisher 50 + `/beanspruchungs-check/`); Tests ≥ 223 + neue; Sitemap OK; Pages-Function-Build erfolgreich.

- [ ] **Step 2: Rendering aller betroffenen Routen**

```bash
npx astro preview --port 4321 > /tmp/preview.log 2>&1 &
sleep 4
for p in / /branchen/molkerei/ /branchen/chemieindustrie/ /branchen/brauerei-getraenkeindustrie/ /beanspruchungs-check/ /kontakt/ /leistungen/keramische-industrieboeden/ /leistungen/whg-abdichtung-industrieboden/; do
  printf "%s -> " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:4321$p"
done
kill %1
```

Expected: alle `200`. Zusätzlich:

```bash
grep -c '"hasCredential"' dist/index.html
grep -o '"additionalProperty":\[[^]]*\]' dist/leistungen/keramische-industrieboeden/index.html
grep -c 'data-stress-check' dist/beanspruchungs-check/index.html
grep -o 'data-client="[^"]*"' dist/branchen/molkerei/index.html | head -2
grep -o '<title>[^<]*</title>' dist/index.html dist/kontakt/index.html dist/beanspruchungs-check/index.html
```

- [ ] **Step 3: `git diff --stat`**

```bash
git -C ../.. diff --stat main...HEAD
```

- [ ] **Step 4: SEO-/Trust-Review (prüfender Agent, read-only)**

`seo-content-reviewer` auf die geänderten `.astro`/`.ts`-Dateien laufen lassen; Befunde beheben, Gate wiederholen.

- [ ] **Step 5: Pflichtabschluss**

- `CHECKPOINT_STATE.json`: Branch, letzter Commit, Gate-Ergebnis, Push `false`, Deploy `false`.
- `SESSION_LOG.md`: Eintrag 2026-09-17 mit Aufgabe, Ergebnis, offenen Punkten (Krombacher-Logo/Freigabe, „Kagetec-R-Äquivalent" bewusst nicht gerendert, Preis-Sweep-Befund).
- `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`: Kopfblock ergänzen.
- `~/KI-System/tools/handoff.sh write "Claude Code" "<getan>" "<nächster Schritt>"`.
- Report unter `08_System/reports/validation/`.
- `ai-state event --tool claude --type checkpoint --msg "..."`.

- [ ] **Step 6: Abschluss-Commit der Doku (nur Repo-Dateien)**

```bash
git add CHECKPOINT_STATE.json SESSION_LOG.md docs/superpowers/plans/2026-09-17-b2b-tracking-stresscheck-schema.md
git commit -m "docs: Checkpoint und Session-Log für B2B-Tracking/Beanspruchungs-Check/Schema-Upgrade"
```

Kein Push.

---

## Self-Review

**Spec-Abdeckung:**
- Schritt 1 (analytics.ts, 4 Funktionen, dataLayer-Fallback) → Task 2. ✔
- Schritt 2 (LogoCloud `industryFilter`, Sortierung, Proof-Tags, Tracking, Branchenseiten) → Task 3. Krombacher: bewusst nicht renderbar (kein Logo/Freigabe), im Report. ✔
- Schritt 3 (StressCheck.astro, stressMatrix.ts, 4 Parameter, 3 Systeme, Audit-Anbindung) → Tasks 4–6. „Kagetec-R-Äquivalent" bewusst nicht im öffentlichen Text. ✔
- Schritt 4 (SEOHead, Organization/Service mit Normen, Titles/Descriptions) → Task 7. Normen ehrlich modelliert. ✔
- Schritt 5 (astro check, build, diff --stat, Routen-Rendering) → Task 8. ✔
- Preis-/Floskel-Tilgung → Task 7 Step 7 + Guard-Test; TCO-Artikel bewusst erhalten (argumentiert gegen m²-Preis-Denken). ✔

**Platzhalter-Scan:** keine TODO/TBD; jeder Code-Schritt enthält Code.

**Typkonsistenz:** `StressCheckStepData` (analytics) ↔ `trackStressCheck`-Aufruf in StressCheck.astro (camelCase-Keys) ✔; `NormId` überall aus `standards.ts` ✔; `LeadPrefill` in Task 5 definiert, in Task 6 und LeadForm konsumiert ✔; `LogoCloudEntry.proofTag`/`industry` in Task 3 definiert und in LogoCloud.astro genutzt ✔; `buildServiceJsonLd.standards?: NormId[]` in Task 7 definiert und in `leistungen/[slug].astro` genutzt ✔.
