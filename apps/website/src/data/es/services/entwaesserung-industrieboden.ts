import type { SpanishService } from "../../../lib/spanishTypes";
import { entwaesserungIndustrieboden as source } from "../../services/entwaesserung-industrieboden";

export const entwaesserungIndustrieboden: SpanishService = {
  ...source,
    "localizedSlug": "drenaje-pavimentos-industriales",
    "title": "Drenaje de pavimentos industriales",
    "seoTitle": "Drenaje industrial, canaletas y pendientes | HSB",
    "description": "Canaletas higiénicas de acero inoxidable y pendientes para pavimentos industriales. Canaletas y pavimento integrados en un sistema estanco.",
    "h1": "Drenaje integrado y planificación de pendientes",
    "primaryKeyword": "drenaje de pavimentos industriales",
    "secondaryKeywords": [
      "canaletas de acero inoxidable",
      "sumideros industriales",
      "recrecido con pendientes",
      "drenaje HACCP"
    ],
    "problem": "El agua estancada favorece la proliferación microbiana, provoca accidentes por resbalones y permite infiltraciones bajo las uniones entre revestimiento y canaleta.",
    "applications": [
      "Plantas lácteas",
      "Cervecerías",
      "Cocinas centrales",
      "Producción química",
      "Limpieza húmeda"
    ],
    "technicalRequirements": [
      "Calidades de acero inoxidable V2A/V4A",
      "Geometría higiénica de canaletas (R > 10 mm)",
      "Conexión mediante bridas adhesivas estancas",
      "Cálculo de la capacidad hidráulica",
      "Planificación de pendientes según caudal, uso de la superficie y disposición de canaletas"
    ],
    "systemSolution": "Hexagon Säurebau planifica el drenaje como elemento central del pavimento, no como un accesorio. Coordinamos el recrecido con pendientes y la colocación de canaletas para asegurar la continuidad de la evacuación del agua.",
    "benefits": [
      "Evitar la formación de charcos tras la limpieza",
      "Planificación y comprobación de encuentros estancos con el pavimento según el proyecto",
      "Limpieza sencilla conforme a HACCP",
      "Cumplimiento de la seguridad laboral"
    ],
    "decisionCriteria": [
      "Volumen de los vertidos de agua",
      "Sólidos presentes en las aguas residuales",
      "Ciclos de limpieza y productos químicos",
      "Profundidad de instalación y conducciones existentes"
    ],
    "faqs": [
      {
        "question": "¿Por qué son tan importantes las pendientes?",
        "answer": "Sin una pendiente correcta, el agua queda estancada. Esto aumenta el trabajo de limpieza, el riesgo de resbalones y las cargas sobre las juntas y la impermeabilización."
      }
    ],
    "ctaLabel": "Planificar el concepto de drenaje",
    "ctaTarget": "/es/#contact"
};
