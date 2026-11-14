import type { SpanishService } from "../../../lib/spanishTypes";
import { bodenReparaturInstandsetzung as source } from "../../services/boden-reparatur-instandsetzung";

export const bodenReparaturInstandsetzung: SpanishService = {
  ...source,
    "localizedSlug": "reparacion-pavimentos-industriales",
    "title": "Reparación y rehabilitación puntual",
    "seoTitle": "Reparación de pavimentos industriales | HSB",
    "description": "Reparación de juntas, huecos, fisuras y cantos en pavimentos industriales: resolver daños concretos, a menudo sin detener toda la producción.",
    "h1": "Reparación y rehabilitación puntual de pavimentos industriales",
    "primaryKeyword": "reparación de pavimentos industriales",
    "secondaryKeywords": [
      "rehabilitación de juntas",
      "daños en pavimentos industriales",
      "reparación de pavimentos de producción",
      "rehabilitación por zonas"
    ],
    "problem": "No todos los daños requieren una nueva colocación completa. Las juntas desprendidas, las picaduras, las baldosas sueltas, los encuentros dañados de canaletas y los deterioros de zócalos comprometen la higiene y la estabilidad. Sin embargo, suelen ignorarse demasiado tiempo, hasta que una reparación se convierte en una urgencia.",
    "applications": [
      "Juntas desprendidas y no estancas",
      "Picaduras y daños por ácidos en zonas concretas",
      "Baldosas cerámicas sueltas o rotas",
      "Encuentros dañados con canaletas y paredes",
      "Daños en zócalos y cantos"
    ],
    "technicalRequirements": [
      "Conexión al sistema existente con materiales compatibles",
      "Morteros y materiales de junta de reparación resistentes a ácidos y productos químicos",
      "Comprobación de la resistencia a tracción y del soporte antes de reparar",
      "Restablecimiento de pendientes y estanqueidad"
    ],
    "systemSolution": "Antes de cada reparación aclaramos la causa y el alcance: daño puntual o problema del sistema. Reparamos las zonas afectadas con sistemas resistentes y compatibles con lo existente; se restablecen la junta, el encuentro, la impermeabilización y la pendiente, en lugar de cubrir el daño de forma meramente estética.",
    "benefits": [
      "Menores costes y periodos de cierre que una rehabilitación integral",
      "Rápido restablecimiento de la higiene y de las condiciones para auditorías",
      "Prevención de daños posteriores por entrada de humedad",
      "Prolongación de la vida útil del pavimento existente"
    ],
    "decisionCriteria": [
      "Tipo de daño: puntual o extendido",
      "Estado restante y antigüedad del sistema existente",
      "Urgencia de higiene y auditoría",
      "Relación entre costes de reparación y rehabilitación"
    ],
    "faqs": [
      {
        "question": "¿Conviene reparar el pavimento o es preferible rehabilitarlo?",
        "answer": "Depende del tipo de daño. Cuando los daños son puntuales y el resto del pavimento está en buen estado, una reparación profesional resulta más económica y requiere menos tiempo de cierre. Si el fallo afecta a una superficie extensa, evaluamos sobre el terreno a partir de qué punto conviene una rehabilitación."
      },
      {
        "question": "¿Pueden realizarse reparaciones mientras continúa la producción?",
        "answer": "En muchos casos sí. Las zonas parciales, los periodos de cierre y los sistemas de curado rápido permiten reparar sin detener completamente la producción."
      }
    ],
    "ctaLabel": "Solicitar una evaluación del daño",
    "ctaTarget": "/es/#contact"
};
