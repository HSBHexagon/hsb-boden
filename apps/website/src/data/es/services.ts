import type { SpanishService } from "../../lib/spanishTypes";
import { industriebodenSaeureschutz } from "./services/industrieboden-saeureschutz";
import { keramischeIndustrieboeden } from "./services/keramische-industrieboeden";
import { puBetonIndustrieboden } from "./services/pu-beton-industrieboden";
import { epoxidharzBodenbeschichtung } from "./services/epoxidharz-bodenbeschichtung";
import { entwaesserungIndustrieboden } from "./services/entwaesserung-industrieboden";
import { whgAbdichtungIndustrieboden } from "./services/whg-abdichtung-industrieboden";
import { bodensanierungLaufenderBetrieb } from "./services/bodensanierung-laufender-betrieb";
import { dehnungsfugenRammschutzIndustrieboden } from "./services/dehnungsfugen-rammschutz-industrieboden";
import { bodenReparaturInstandsetzung } from "./services/boden-reparatur-instandsetzung";

export const spanishServices: SpanishService[] = [
  industriebodenSaeureschutz,
  keramischeIndustrieboeden,
  puBetonIndustrieboden,
  epoxidharzBodenbeschichtung,
  entwaesserungIndustrieboden,
  whgAbdichtungIndustrieboden,
  bodensanierungLaufenderBetrieb,
  dehnungsfugenRammschutzIndustrieboden,
  bodenReparaturInstandsetzung,
];

export const spanishServiceTitleMap: Record<string, string> = Object.fromEntries(
  spanishServices.map((s) => [s.slug, s.title]),
);
