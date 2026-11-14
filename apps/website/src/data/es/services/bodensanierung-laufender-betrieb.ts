import type { SpanishService } from "../../../lib/spanishTypes";
import { bodensanierungLaufenderBetrieb as source } from "../../services/bodensanierung-laufender-betrieb";

export const bodensanierungLaufenderBetrieb: SpanishService = {
  ...source,
    "localizedSlug": "rehabilitacion-pavimentos-produccion-activa",
    "title": "Rehabilitación de pavimentos durante la producción",
    "seoTitle": "Rehabilitar pavimentos con producción en marcha | HSB",
    "description": "Rehabilitación de pavimentos durante la producción: fases, medidas de protección y puesta en servicio adaptadas al proceso y al sistema elegido.",
    "h1": "Rehabilitar pavimentos industriales con la producción en marcha",
    "primaryKeyword": "rehabilitación de pavimentos durante la producción",
    "secondaryKeywords": [
      "rehabilitación en fin de semana",
      "preparación del soporte con bajas emisiones de polvo",
      "hormigón de fraguado rápido industrial",
      "protección de la producción"
    ],
    "problem": "Una rehabilitación suele detener toda la producción. El polvo pone en peligro alimentos expuestos o electrónica sensible. Los plazos imprecisos provocan retrasos en las entregas.",
    "applications": [
      "Naves existentes",
      "Ampliaciones",
      "Reparaciones por deficiencias detectadas en auditorías",
      "Rehabilitación de juntas"
    ],
    "technicalRequirements": [
      "Preparación del soporte con bajas emisiones de polvo y medidas de protección eficaces",
      "Sistemas de depresión y protección frente al polvo",
      "Materiales de curado rápido (PMMA/PU-cemento)",
      "Planificación coordinada de fases de obra y periodos de cierre"
    ],
    "systemSolution": "Planificamos la rehabilitación en fases de obra coordinadas. El tiempo de curado y la reapertura al tráfico dependen del soporte, las condiciones de aplicación y las autorizaciones del fabricante; los periodos disponibles de producción se acuerdan antes de comenzar.",
    "benefits": [
      "Limitar las interrupciones de producción mediante fases de obra adecuadas",
      "Proteger las zonas próximas frente al polvo y los olores",
      "Reducir los riesgos de parada mediante una planificación anticipada",
      "Menor riesgo de costes globales"
    ],
    "decisionCriteria": [
      "Periodos disponibles de producción",
      "Rutas logísticas (flujo de materiales)",
      "Requisitos de protección frente al polvo",
      "Profundidad de la rehabilitación necesaria"
    ],
    "faqs": [
      {
        "question": "¿Cómo evitan el polvo en la zona de producción contigua?",
        "answer": "Las separaciones adecuadas, la extracción y los procedimientos de trabajo coordinados reducen la entrada de polvo. No debe prometerse una ausencia total de polvo sin comprobar las condiciones del lugar."
      },
      {
        "question": "¿Puedo calcular previamente en línea el periodo necesario para la rehabilitación?",
        "answer": "Sí. Nuestra calculadora de periodos de rehabilitación permite planificar de forma orientativa las fases de obra y los tiempos de curado a partir de la superficie de la nave, el trabajo por turnos y el sistema de pavimentación."
      }
    ],
    "ctaLabel": "Analizar el periodo de rehabilitación",
    "ctaTarget": "/es/#contact"
};
