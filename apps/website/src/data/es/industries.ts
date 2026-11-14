import type { SpanishIndustry } from "../../lib/spanishTypes";
import { industryLebensmittelindustrie } from "./industries/lebensmittelindustrie";
import { industryMolkerei } from "./industries/molkerei";
import { industryBrauereiGetraenkeindustrie } from "./industries/brauerei-getraenkeindustrie";
import { industryChemieindustrie } from "./industries/chemieindustrie";
import { industryPharmaindustrie } from "./industries/pharmaindustrie";
import { industryBackwarenproduktionGrosskueche } from "./industries/backwarenproduktion-grosskueche";

export const spanishIndustries: SpanishIndustry[] = [
  industryLebensmittelindustrie,
  industryMolkerei,
  industryBrauereiGetraenkeindustrie,
  industryChemieindustrie,
  industryPharmaindustrie,
  industryBackwarenproduktionGrosskueche,
];
