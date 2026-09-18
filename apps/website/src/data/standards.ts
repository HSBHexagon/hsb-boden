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
    scope:
      "Planung und Ausführung säurefester keramischer Beläge im Rüttelverfahren mit Kunstharzfuge.",
    serviceSlugs: ["keramische-industrieboeden", "industrieboden-saeureschutz"],
  },
  {
    id: "DIN EN 14411",
    name: "DIN EN 14411 – Keramische Fliesen und Platten",
    scope:
      "Produktnorm für die eingesetzten Feinsteinzeug- und Spaltplatten (Wasseraufnahme, Biegefestigkeit, Beständigkeit).",
    serviceSlugs: ["keramische-industrieboeden"],
  },
  {
    id: "WHG § 62",
    name: "§ 62 WHG / AwSV – Anlagen zum Umgang mit wassergefährdenden Stoffen",
    scope:
      "Dichtheits- und Beständigkeitsanforderungen an Flächen und Auffangwannen; Ausführung durch Fachbetrieb nach AwSV.",
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
