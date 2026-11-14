import { spanishArticles } from "../data/es/articles";
import { spanishIndustries } from "../data/es/industries";
import { spanishRegionalGuides } from "../data/es/regionalGuides";
import { spanishServices } from "../data/es/services";
import { homeAlternates } from "./i18n";
import { spanishStaticPaths } from "./spanishStaticPaths";

function normalizePath(path: string): string {
  if (!path) return "/";
  const [pathname] = path.split(/[?#]/);
  if (!pathname || pathname === "/") return "/";
  return pathname.endsWith("/") ? pathname : `${pathname}/`;
}

const STATIC_GERMAN_TO_SPANISH: Record<string, string> = {
  "/": "/es/",
  "/leistungen/": "/es/servicios/",
  "/branchen/": "/es/sectores/",
  "/wissen/": "/es/conocimiento/",
  "/referenzen/": "/es/referencias/",
  "/beanspruchungs-check/": "/es/analisis-cargas/",
  "/rechner/sanierungsfenster/": "/es/calculadora-paradas/",
  "/danke-projektanfrage/": "/es/gracias/",
  ...spanishStaticPaths,
};
for (const service of spanishServices) {
  STATIC_GERMAN_TO_SPANISH[`/leistungen/${service.slug}/`] =
    `/es/servicios/${service.localizedSlug}/`;
}

for (const industry of spanishIndustries) {
  STATIC_GERMAN_TO_SPANISH[`/branchen/${industry.slug}/`] =
    `/es/sectores/${industry.localizedSlug}/`;
}

for (const article of spanishArticles) {
  STATIC_GERMAN_TO_SPANISH[`/wissen/${article.slug}/`] =
    `/es/conocimiento/${article.localizedSlug}/`;
}

for (const regionSlug of Object.keys(spanishRegionalGuides)) {
  STATIC_GERMAN_TO_SPANISH[`/standorte/${regionSlug}/`] =
    `/es/regiones/${regionSlug}/`;
}

const SPANISH_TO_GERMAN: Record<string, string> = Object.fromEntries(
  Object.entries(STATIC_GERMAN_TO_SPANISH).map(([dePath, esPath]) => [
    esPath,
    dePath,
  ]),
);
const NAVIGATION_FALLBACKS: Record<string, string> = {
  "/kontakt/": "/es/#contact",
  "/projektablauf/": "/es/#proceso",
};

export function toSpanishPath(germanPath: string): string {
  const normalized = normalizePath(germanPath);
  if (STATIC_GERMAN_TO_SPANISH[normalized]) {
    return STATIC_GERMAN_TO_SPANISH[normalized];
  }
  if (NAVIGATION_FALLBACKS[normalized]) {
    return NAVIGATION_FALLBACKS[normalized];
  }
  if (SPANISH_TO_GERMAN[normalized]) {
    return normalized;
  }
  return germanPath;
}

export function toGermanPath(spanishPath: string): string {
  const normalized = normalizePath(spanishPath);
  if (SPANISH_TO_GERMAN[normalized]) {
    return SPANISH_TO_GERMAN[normalized];
  }
  if (STATIC_GERMAN_TO_SPANISH[normalized]) {
    return normalized;
  }
  return spanishPath.startsWith("/es/") ? "/" : spanishPath;
}

export function hasSpanishEquivalent(path: string): boolean {
  const normalized = normalizePath(path);
  return Boolean(
    STATIC_GERMAN_TO_SPANISH[normalized] || SPANISH_TO_GERMAN[normalized],
  );
}

export function spanishAlternates(path: string): { lang: string; path: string }[] {
  const normalized = normalizePath(path);
  if (normalized === "/" || normalized === "/es/") {
    return homeAlternates;
  }
  const dePath = SPANISH_TO_GERMAN[normalized] ?? normalized;
  const esPath = STATIC_GERMAN_TO_SPANISH[dePath];
  if (!esPath) {
    return [];
  }
  return [
    { lang: "de", path: dePath },
    { lang: "es", path: esPath },
    { lang: "x-default", path: dePath },
  ];
}
