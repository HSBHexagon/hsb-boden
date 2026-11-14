import type { Article, Industry, Service } from "./types";
import type { TechnicalDecisionGuide } from "../data/technicalDecisionGuides";
import type { RegionalGuide } from "../data/regionalGuides";

/** Keep source IDs stable for relationships; localize only the public path. */
export interface SpanishService extends Service { localizedSlug: string }
export interface SpanishIndustry extends Industry { localizedSlug: string }
export interface SpanishArticle extends Article {
  localizedSlug: string;
  sections: { title: string; body: string }[];
}
export type SpanishTechnicalDecisionGuide = TechnicalDecisionGuide;
export type SpanishRegionalGuide = RegionalGuide;
