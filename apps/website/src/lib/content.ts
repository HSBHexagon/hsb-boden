import { articles } from "../data/articles";
import { clientLocations } from "../data/clientLocations";
import { spanishArticles } from "../data/es/articles";
import { spanishIndustries } from "../data/es/industries";
import { spanishRegionalGuides } from "../data/es/regionalGuides";
import { spanishServices } from "../data/es/services";
import { industries } from "../data/industries";
import { jobs } from "../data/jobs";
import { references } from "../data/references";
import { services } from "../data/services";
import { site } from "../data/site";
import { landing } from "./i18n";
import {
  serviceSchema,
  industrySchema,
  referenceSchema,
  articleSchema,
  type Service,
} from "./types";

export function validateSiteContent() {
  const errors: string[] = [];
  for (const service of services) {
    const result = serviceSchema.safeParse(service);
    if (!result.success)
      errors.push(`service:${service.slug}:${result.error.message}`);
  }
  for (const industry of industries) {
    const result = industrySchema.safeParse(industry);
    if (!result.success)
      errors.push(`industry:${industry.slug}:${result.error.message}`);
  }
  for (const reference of references) {
    const result = referenceSchema.safeParse(reference);
    if (!result.success)
      errors.push(`reference:${reference.id}:${result.error.message}`);
  }
  for (const article of articles) {
    const result = articleSchema.safeParse(article);
    if (!result.success)
      errors.push(`article:${article.slug}:${result.error.message}`);
  }

  return { success: errors.length === 0, errors };
}

export function getServices() {
  return services;
}

export function getIndustries() {
  return industries;
}

export function getArticles() {
  return articles;
}

const servicesMap = new Map<string, Service>(
  services.map((s) => [s.slug, s as unknown as Service]),
);

export function getServiceBySlug(slug: string) {
  return servicesMap.get(slug);
}

export function getPublicReferences() {
  return references
    .filter((reference) => {
      const approvalStatus: string = reference.approvalStatus;
      return approvalStatus !== "internal";
    })
    .map((reference) => {
      const approved = reference.approvalStatus === "approved";
      const canShowLogo = approved && reference.canShowLogo;
      const canShowExactLocation = approved && reference.canShowExactLocation;

      return {
        ...reference,
        displayName: approved ? reference.publicName : reference.anonymousName,
        displayLocation: canShowExactLocation
          ? `${reference.city}, ${reference.region}`
          : reference.region,
        canShowExactLocation,
        logo: canShowLogo ? reference.logo : undefined,
      };
    });
}

// Dieselbe Firma kann freigegebene Referenz UND Kundenstandort sein. Beide
// Quellen zusammenzufuehren erzeugte auf der Startseite Duplikate (LogoCloud,
// Kartenmarker, Standortliste). Zugeordnet wird ueber die kanonische
// referenceId aus clientLocations, nicht ueber Namensvergleich; der Guard in
// tests/reference-deduplication.test.ts erzwingt, dass die ID gesetzt ist.

/**
 * Logos fuer den LogoCloud der Startseite. Die freigegebene Referenz hat
 * Vorrang vor dem Kundenstandort-Eintrag derselben Firma.
 */
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
  const affineSystems = new Set(industry?.recommendedSystems ?? []);
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

/**
 * Kundenstandorte ohne die Firmen, die bereits als oeffentliche Referenz
 * erscheinen — verhindert doppelte Kartenmarker und Doppelnennungen in der
 * Liste "Weitere Kundenstandorte".
 */
export function getSupplementalClientLocations() {
  const publicReferenceIds = new Set(
    getPublicReferences().map((reference) => reference.id),
  );

  return clientLocations.filter(
    (location) =>
      !("referenceId" in location) ||
      !publicReferenceIds.has(location.referenceId),
  );
}

export function getReferencesForSlugs(referenceIds: string[]) {
  const allowed = new Set(referenceIds);
  return getPublicReferences().filter((reference) => allowed.has(reference.id));
}

export function getAllPublicPages() {
  return [
    {
      h1: "Industrieböden und Säureschutzsysteme für produktionskritische Bereiche",
      seoTitle: site.defaultTitle,
      description: site.defaultDescription,
      canonicalPath: "/",
    },
    {
      h1: "Leistungen für Industrieböden und Säureschutz",
      seoTitle: "Leistungen: Rüttelkeramik, Säureschutz & WHG | HSB Hexagon",
      description:
        "Ingenieurbau für Industrieböden: Rüttelkeramik nach AGI S 40, Säureschutz, PU-Beton, Epoxidharz, Entwässerung, WHG § 62 Abdichtung und Sanierung im Betrieb.",
      canonicalPath: "/leistungen/",
    },
    {
      h1: "Branchenspezifische Industrieböden",
      seoTitle: "Industrieböden nach Branche | HSB Hexagon Säurebau",
      description:
        "Industrieböden für Lebensmittelindustrie, Molkereien, Brauereien, Chemie, Pharma, Backwarenproduktion und Großküchen.",
      canonicalPath: "/branchen/",
    },
    {
      h1: "Referenzen aus produktionskritischen Bereichen",
      seoTitle:
        "Referenzen für Industrieböden & Säureschutz | HSB Hexagon Säurebau",
      description:
        "Ausgewählte Referenzen für Industrieböden, Säureschutz, Keramik, Entwässerung und Sanierung.",
      canonicalPath: "/referenzen/",
    },
    {
      h1: "Wissen zu Industrieböden, Säureschutz und Sanierung",
      seoTitle: "Wissen zu Industrieböden & Säureschutz | HSB Hexagon Säurebau",
      description:
        "Praxisnahes Wissen zu PU-Beton, keramischen Industrieböden, Molkereiböden, säurefesten Fliesen, Entwässerung und Sanierung.",
      canonicalPath: "/wissen/",
    },
    {
      h1: "Ein klarer Projektablauf für produktionskritische Bodenflächen",
      seoTitle: "Projektablauf für Industrieböden und Säureschutz | HSB",
      description:
        "Vom Belastungsprofil bis zur Abnahme: So strukturiert HSB Analyse, Systemauslegung, Untergrund, Einbau und Dokumentation von Industriebodenprojekten.",
      canonicalPath: "/projektablauf/",
    },
    {
      h1: "Projektanfrage für Industrieböden",
      seoTitle: "Technisches Vor-Ort-Audit anfragen | HSB Hexagon Säurebau",
      description:
        "Vor-Ort-Audit für Industrieböden: Belastungsprofil, Untergrund und Sanierungsfenster ingenieurseitig bewertet – Rüttelkeramik, Säureschutz, WHG-Abdichtung.",
      canonicalPath: "/kontakt/",
    },
    {
      h1: "Technischer Beanspruchungs-Check für Produktionsböden",
      seoTitle: "Beanspruchungs-Check für Industrieböden | HSB Hexagon",
      description:
        "Medium, Temperatur, Last und Sanierungsfenster eingeben – deterministische Systemempfehlung nach AGI S 40, PU-Beton oder WHG § 62 mit direktem Vor-Ort-Audit.",
      canonicalPath: "/beanspruchungs-check/",
    },
    {
      h1: "Danke für Ihre Projektanfrage",
      seoTitle: "Danke für Ihre Projektanfrage | HSB Hexagon Säurebau",
      description:
        "Ihre Anfrage wurde vorbereitet. HSB meldet sich zur technischen Bewertung von Industrieboden, Säureschutz oder Sanierung.",
      canonicalPath: "/danke-projektanfrage/",
    },
    {
      h1: "Karriere bei HSB Hexagon Säurebau",
      seoTitle: "Karriere bei HSB Hexagon Säurebau | Industrieboden-Projekte",
      description:
        "Karriere bei HSB: Arbeiten an anspruchsvollen Industrieböden, Säureschutzsystemen und Sanierungsprojekten in Produktionsbetrieben.",
      canonicalPath: "/karriere/",
    },
    ...jobs.map((job) => ({
      h1: job.title,
      seoTitle: job.seoTitle,
      description: job.shortDescription,
      canonicalPath: `/karriere/${job.slug}/`,
    })),
    // Rechtsseiten: gebaut, indexierbar und im Footer verlinkt — sie gehören
    // deshalb in die Sitemap. Titel und Beschreibung müssen mit den Werten in
    // src/pages/impressum/ bzw. src/pages/datenschutz/ übereinstimmen.
    {
      h1: "Impressum",
      seoTitle: "Impressum | HSB Hexagon Säurebau GmbH",
      description:
        "Impressum und Anbieterkennzeichnung der HSB Hexagon Säurebau GmbH, Benzstraße 6, 48599 Gronau.",
      canonicalPath: "/impressum/",
    },
    {
      h1: "Datenschutzinformation",
      seoTitle: "Datenschutz | HSB Hexagon Säurebau GmbH",
      description:
        "Datenschutzinformation der HSB Hexagon Säurebau GmbH nach DSGVO: Verarbeitung, Rechtsgrundlagen, Speicherdauer, Löschung und Ihre Betroffenenrechte.",
      canonicalPath: "/datenschutz/",
    },
    {
      h1: "Ausschreibungstexte & technische Spezifikationen für Industrieböden",
      seoTitle: "Planerportal & LV-Texte Industrieboden | HSB",
      description:
        "Ausschreibungstexte (LV) für Architekten und Planer: Rüttelkeramik nach AGI S 40, PU-Beton 9 mm und WHG § 62 Dichtflächen mit 1-Klick-Kopierfunktion.",
      canonicalPath: "/planer/",
    },
    {
      h1: "Fugen-Forensik: Typische Schadensbilder an Industrieböden verstehen",
      seoTitle: "Fugen-Forensik & Schadensanalyse Industrieboden | HSB",
      description:
        "Schadensbilder bei Industrieböden technisch aufklären: Ausgewaschene Fugen, hohle Fliesen, Rinnenabrisse und Thermoschock – Ursachen und Sanierung.",
      canonicalPath: "/wissen/fugen-forensik/",
    },
    {
      h1: "Ausgewaschene Fugen: Wenn Reinigungschemie den Boden zersetzt",
      seoTitle: "Ausgewaschene Fugen im Industrieboden sanieren | HSB",
      description:
        "Ausgewaschene Fugen im Lebensmittelbetrieb: Wie Milchsäure, Fette und CIP-Reiniger zementäre Fugen zerstören und wie Reaktionsharzfugen schützen.",
      canonicalPath: "/wissen/fugen-forensik/fuge-ausgewaschen/",
    },
    {
      h1: "Hohl liegende Fliesen & Plattenbruch unter Flurförderzeugen",
      seoTitle: "Hohle Fliesen & Kantenbrüche sanieren | HSB",
      description:
        "Hohl liegende Fliesen und Plattenbrüche: Ursachen durch fehlende Vollbettung und Schubspannungen, Sanierung im Rüttelverfahren nach AGI S 40.",
      canonicalPath: "/wissen/fugen-forensik/fliesen-hohl/",
    },
    {
      h1: "Gerissene Rinnenkanten: Die kritische Schnittstelle zwischen Stahl und Estrich",
      seoTitle: "Gerissene Rinnenkanten & Anschlüsse sanieren | HSB",
      description:
        "Risse an Entwässerungsrinnen: Warum Edelstahl und Beton ohne elastische Hybridfuge reißen und wie HSB dauerhafte Rinnenanschlüsse baut.",
      canonicalPath: "/wissen/fugen-forensik/rinnenkante-gerissen/",
    },
    {
      h1: "Undichte Hohlkehlen: Die unterschätzte Gefahr am Wandanschluss",
      seoTitle: "Schadensbild: Undichte Hohlkehlen & Wandanschlüsse | HSB",
      description:
        "Undichte Hohlkehlen und Sockelbereiche in der Lebensmittelindustrie: Wie Feuchtigkeit hinter Sockelfliesen kriecht, Keimnester bildet und wie entkoppelte Hohlkehlensysteme dicht halten.",
      canonicalPath: "/wissen/fugen-forensik/hohlkehle-undicht/",
    },
    {
      h1: "Thermoschock: Wenn heißes Reinigungswasser Beschichtungen abplatzen lässt",
      seoTitle: "Thermoschock & Schubspannungsrisse beheben | HSB",
      description:
        "Thermoschock am Industrieboden: Warum Heißwasser (CIP über 80 °C) auf kaltem Untergrund Beschichtungen ablöst und welche Systeme standhalten.",
      canonicalPath: "/wissen/fugen-forensik/thermoschock-schaeden/",
    },
    {
      h1: "Rüttelboden-Aufbau: Schichten, Verlegung und AGI S 40",
      seoTitle: "Rüttelboden-Aufbau: Schichten & AGI S 40 | HSB",
      description:
        "Wie ist ein Rüttelboden aufgebaut? Untergrund, Haftbrücke, Mörtelbett, Rüttelfliesen und Fugen im Überblick – mit Planungshinweisen zu AGI S 40.",
      canonicalPath: "/wissen/ruettelkeramik-agi-s-40/",
    },
    {
      h1: "Muster-Abnahmeprotokoll: Was ein belastbares Gutachten ausmacht",
      seoTitle: "Muster-Abnahmeprotokoll & IFS-Checkliste Boden | HSB",
      description:
        "Muster-Abnahmeprotokoll für Industrieböden: Prüfung nach DIN 18202, Gefälle, Haftzug, Rinnenanschlüsse und IFS/BRC-Audit-Checkliste zum Download.",
      canonicalPath: "/wissen/muster-abnahmeprotokoll/",
    },
    {
      h1: "Sanierungsfenster-Rechner: Bauabschnitte und Stillstandszeiten planen",
      seoTitle: "Sanierungsfenster-Rechner | HSB Hexagon",
      description:
        "Sanierungsfenster für Industrieböden berechnen: Hallenfläche, Schichtbetrieb und Aushärtezeiten indikativ auf Bauabschnitte planen.",
      canonicalPath: "/rechner/sanierungsfenster/",
    },
    ...services.map((service) => ({
      h1: service.h1,
      seoTitle: service.seoTitle,
      description: service.description,
      canonicalPath: `/leistungen/${service.slug}/`,
    })),
    ...industries.map((industry) => ({
      h1: industry.h1,
      seoTitle: industry.seoTitle,
      description: industry.description,
      canonicalPath: `/branchen/${industry.slug}/`,
    })),
    ...articles.map((article) => ({
      h1: article.h1,
      seoTitle: article.seoTitle,
      description: article.description,
      canonicalPath: `/wissen/${article.slug}/`,
    })),
    ...Object.entries(landing).map(([lang, content]) => ({
      h1: content.hero.h1,
      seoTitle: content.meta.seoTitle,
      description: content.meta.description,
      canonicalPath: `/${lang}/`,
    })),
    {
      h1: "Industrieboden-Spezialist in Norddeutschland",
      seoTitle: "Industrieboden Hamburg | Keramische Böden & Säureschutz Nord",
      description:
        "Industrieboden Hamburg: Lasten, Übergänge, Entwässerung und mögliche Anforderungen an Auffangflächen im Betrieb einordnen.",
      canonicalPath: "/standorte/hamburg/",
    },
    {
      h1: "Industrieboden-Spezialist in Bayern",
      seoTitle: "Industrieboden Bayern | Böden & Säureschutz München",
      description:
        "Industrieboden Bayern: Abfüllung, Gefälle, Rinnen, Reinigungstemperaturen und Keramik oder PU-Beton für die technische Planung vergleichen.",
      canonicalPath: "/standorte/bayern/",
    },
    {
      h1: "Industrieboden-Spezialist in Nordrhein-Westfalen",
      seoTitle: "Industrieboden NRW | Böden & Säureschutz",
      description:
        "Industrieboden NRW: Säureschutz, WHG-Flächen und Sanierung anhand von Medienliste, Fugen und Betriebsfenstern technisch bewerten.",
      canonicalPath: "/standorte/nrw/",
    },
    {
      h1: "Industrieboden-Spezialist in Rheinland-Pfalz",
      seoTitle: "Industrieboden Rheinland-Pfalz | Böden & Säureschutz",
      description:
        "Industrieboden Rheinland-Pfalz: Getränkeproduktion, Nasszonen und Reparaturen anhand von Medien, Gefälle und Betriebsfenstern planen.",
      canonicalPath: "/standorte/rheinland-pfalz/",
    },
    {
      h1: "Industrieboden-Spezialist in Baden-Württemberg",
      seoTitle: "Industrieboden Baden-Württemberg | Böden & Säureschutz",
      description:
        "Industrieboden Baden-Württemberg: Keramik, Fugenprofile und Entwässerung nach Radlast, Medien und Betriebsablauf auswählen.",
      canonicalPath: "/standorte/baden-wuerttemberg/",
    },
    {
      h1: "Industrieboden-Spezialist in Niedersachsen",
      seoTitle: "Industrieboden Niedersachsen | Böden & Säureschutz",
      description:
        "Industrieboden Niedersachsen: Feuchte, Milchsäure, Rinnenanschlüsse und Sanierungsfenster in Lebensmittelbetrieben fachlich bewerten.",
      canonicalPath: "/standorte/niedersachsen/",
    },
    {
      h1: "Industrieboden-Spezialist in Hessen",
      seoTitle: "Industrieboden Hessen | Böden & Säureschutz",
      description:
        "Industrieboden Hessen: Reinigungsvalidierung, chemische Beständigkeit und Dokumentation für Produktions- und Hygienebereiche planen.",
      canonicalPath: "/standorte/hessen/",
    },
    {
      h1: "Industrieboden-Spezialist in Thüringen",
      seoTitle: "Industrieboden Thüringen | Böden & Säureschutz",
      description:
        "Industrieboden Thüringen: Hygieneanschlüsse, Reparatur und Wiederinbetriebnahme abhängig von Bodenaufbau und Reinigungsanforderungen prüfen.",
      canonicalPath: "/standorte/thueringen/",
    },
    {
      h1: "Industrieboden-Spezialist in Sachsen-Anhalt",
      seoTitle: "Industrieboden Sachsen-Anhalt | Böden & Säureschutz",
      description:
        "Industrieboden Sachsen-Anhalt: Bestandsaufnahme, chemische Belastung und WHG-/AwSV-relevante Abdichtungen technisch klären.",
      canonicalPath: "/standorte/sachsen-anhalt/",
    },
    {
      h1: "Servicios para pavimentos industriales y protección antiácida",
      seoTitle: "Servicios: cerámica vibrada, antiácidos y WHG | HSB",
      description:
        "Ingeniería de pavimentos industriales: cerámica vibrada según AGI S 40, protección antiácida, PU-cemento, resina epoxi, drenaje, impermeabilización WHG y rehabilitación.",
      canonicalPath: "/es/servicios/",
    },
    {
      h1: "Cada planta de producción presenta un perfil de cargas distinto",
      seoTitle: "Pavimentos industriales por sector | HSB Hexagon",
      description:
        "Pavimentos industriales para industria alimentaria, lácteas, cerveceras, industria química, farmacéutica, panaderías industriales y cocinas centrales.",
      canonicalPath: "/es/sectores/",
    },
    {
      h1: "Pavimentos industriales ejecutados en áreas críticas de producción",
      seoTitle: "Referencias en pavimentos industriales y antiácidos | HSB",
      description:
        "Referencias de pavimentos industriales cerámicos, protección antiácida, drenaje y rehabilitación en producción alimentaria, lácteas, cervecerías e industria química.",
      canonicalPath: "/es/referencias/",
    },
    {
      h1: "Conocimiento sobre pavimentos industriales, protección antiácida y rehabilitación",
      seoTitle: "Conocimiento técnico sobre pavimentos industriales | HSB",
      description:
        "Artículos técnicos y guías prácticas sobre PU-cemento, cerámica vibrada AGI S 40, pavimentos para lácteas, baldosas antiácidas, drenaje y rehabilitación.",
      canonicalPath: "/es/conocimiento/",
    },
    {
      h1: "Análisis técnico de cargas para pavimentos de producción",
      seoTitle: "Análisis de cargas para pavimentos industriales | HSB",
      description:
        "Introduzca medio químico, temperatura, carga mecánica y ventana de intervención para obtener una orientación técnica entre cerámica vibrada AGI S 40, PU-cemento o WHG § 62.",
      canonicalPath: "/es/analisis-cargas/",
    },
    {
      h1: "Calculadora de ventanas de rehabilitación: planificar fases de obra y tiempos de parada",
      seoTitle: "Calculadora de ventanas de rehabilitación | HSB Hexagon",
      description:
        "Calcule de forma orientativa las ventanas de rehabilitación para pavimentos industriales: superficie de nave, régimen de turnos y tiempos de curado por fases.",
      canonicalPath: "/es/calculadora-paradas/",
    },
    {
      h1: "Análisis de juntas: comprender los daños habituales en pavimentos industriales",
      seoTitle: "Análisis de juntas y daños del pavimento industrial | HSB",
      description:
        "Diagnóstico técnico de daños en pavimentos industriales: juntas erosionadas, baldosas huecas, fisuras junto a canaletas y choque térmico. Causas y rehabilitación.",
      canonicalPath: "/es/conocimiento/analisis-juntas/",
    },
    {
      h1: "Juntas erosionadas: cuando los productos de limpieza degradan el pavimento",
      seoTitle: "Rehabilitación de juntas erosionadas en pavimentos | HSB",
      description:
        "Juntas erosionadas en la industria alimentaria: cómo el ácido láctico, las grasas y los limpiadores CIP degradan las juntas cementosas y cómo protegen las resinas de reacción.",
      canonicalPath: "/es/conocimiento/analisis-juntas/junta-erosionada/",
    },
    {
      h1: "Baldosas huecas y rotura de piezas bajo el paso de carretillas",
      seoTitle: "Rehabilitación de baldosas huecas y roturas de bordes | HSB",
      description:
        "Baldosas huecas y roturas de piezas: causas por apoyo incompleto y tensiones de cizallamiento, y rehabilitación mediante colocación por vibración según AGI S 40.",
      canonicalPath: "/es/conocimiento/analisis-juntas/baldosas-huecas/",
    },
    {
      h1: "Bordes de canaleta agrietados: el encuentro crítico entre el acero y el pavimento",
      seoTitle: "Rehabilitar bordes de canaletas y encuentros | HSB",
      description:
        "Fisuras junto a canaletas de drenaje: por qué el acero inoxidable y el hormigón se fisuran sin junta híbrida elástica y cómo HSB ejecuta encuentros duraderos.",
      canonicalPath: "/es/conocimiento/analisis-juntas/fisuras-borde-canaleta/",
    },
    {
      h1: "Medias cañas con filtraciones: un punto crítico en el encuentro con la pared",
      seoTitle: "Daño habitual: medias cañas y encuentros con filtraciones | HSB",
      description:
        "Medias cañas y zócalos con filtraciones en la industria alimentaria: cómo penetra la humedad tras el zócalo, genera focos bacterianos y cómo se mantienen estancos los sistemas desacoplados.",
      canonicalPath: "/es/conocimiento/analisis-juntas/filtraciones-media-cana/",
    },
    {
      h1: "Choque térmico: cuando el agua caliente de limpieza desprende los revestimientos",
      seoTitle: "Corregir daños por choque térmico y fisuras | HSB",
      description:
        "Choque térmico en el pavimento industrial: por qué el agua caliente de limpieza sobre un soporte frío desprende revestimientos y qué sistemas deben estudiarse según las cargas.",
      canonicalPath: "/es/conocimiento/analisis-juntas/danos-choque-termico/",
    },
    {
      h1: "Estructura de un pavimento vibrado: capas, colocación y AGI S 40",
      seoTitle: "Estructura de un pavimento vibrado: capas y AGI S 40 | HSB",
      description:
        "¿Cómo se compone un pavimento vibrado? Soporte, puente de adherencia, lecho de mortero, baldosas para vibrado y juntas en resumen, con criterios de planificación según AGI S 40.",
      canonicalPath: "/es/conocimiento/estructura-pavimento-vibrado-agi-s-40/",
    },
    {
      h1: "Protocolo de recepción de pavimentos industriales: qué aporta una evaluación técnica",
      seoTitle: "Protocolo de recepción y lista IFS de pavimentos | HSB",
      description:
        "Modelo de protocolo de recepción para pavimentos industriales: comprobación según DIN 18202, pendientes, adherencia, encuentros de canaletas y lista de control para auditorías IFS/BRC.",
      canonicalPath: "/es/conocimiento/protocolo-recepcion-pavimentos/",
    },
    ...spanishServices.map((service) => ({
      h1: service.h1,
      seoTitle: service.seoTitle,
      description: service.description,
      canonicalPath: `/es/servicios/${service.localizedSlug}/`,
    })),
    ...spanishIndustries.map((industry) => ({
      h1: industry.h1,
      seoTitle: industry.seoTitle,
      description: industry.description,
      canonicalPath: `/es/sectores/${industry.localizedSlug}/`,
    })),
    ...spanishArticles.map((article) => ({
      h1: article.h1,
      seoTitle: article.seoTitle,
      description: article.description,
      canonicalPath: `/es/conocimiento/${article.localizedSlug}/`,
    })),
    ...Object.entries(spanishRegionalGuides).map(([slug, guide]) => ({
      h1: `Especialista en pavimentos industriales en ${guide.label}`,
      seoTitle: `Pavimento industrial ${guide.label} | HSB Hexagon`,
      description: `Pavimento industrial en ${guide.label}: ${guide.focus.toLowerCase()}. Evaluación técnica según medios químicos, juntas y ventanas operativas.`,
      canonicalPath: `/es/regiones/${slug}/`,
    })),
  ];
}
