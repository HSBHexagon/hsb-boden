import type { SpanishTechnicalDecisionGuide } from "../../lib/spanishTypes";

export const spanishTechnicalDecisionGuides: Record<string, SpanishTechnicalDecisionGuide> = {
  "molkerei": {
    "heading": "Qué aclarar antes de elegir el pavimento de una planta láctea",
    "intro": "La limpieza CIP, los ácidos orgánicos, las cargas de transporte y las zonas húmedas suelen actuar a la vez. Los siguientes datos ayudan a realizar una primera evaluación técnica fundamentada.",
    "requiredInputs": [
      "Proceso CIP con productos de limpieza, concentraciones, temperaturas y frecuencia",
      "Plano del drenaje con pendientes, canaletas, zócalos y daños conocidos",
      "Horarios de producción y parada, y cargas de carros y transpaletas"
    ],
    "decisionRule": "La elección entre cerámica y PU-cemento depende sobre todo de los medios químicos, la exposición de las juntas, la limpieza y el soporte; ningún material es adecuado de forma general para todas las plantas lácteas.",
    "relatedUrl": "/wissen/pu-beton-oder-keramischer-industrieboden/",
    "relatedLabel": "Comparar técnicamente cerámica y PU-cemento"
  },
  "brauerei-getraenkeindustrie": {
    "heading": "Planificar las zonas de llenado y limpieza",
    "intro": "En las líneas de llenado interactúan la limpieza, el tráfico de carretillas y el drenaje. La evacuación no puede planificarse de forma independiente de la composición del pavimento.",
    "requiredInputs": [
      "Ubicación de máquinas y canaletas, y entrada de sólidos procedentes de la limpieza",
      "Frecuencia de limpieza, cambios de temperatura y ácidos y álcalis utilizados",
      "Cargas por rueda en juntas, rampas y transiciones entre áreas de producción"
    ],
    "decisionRule": "Las pendientes, la construcción de las canaletas y el revestimiento deben comprobarse como un sistema. Un valor genérico de pendiente prefijado no sustituye una planificación específica del proyecto.",
    "relatedUrl": "/leistungen/entwaesserung-industrieboden/",
    "relatedLabel": "Drenaje y pendientes del pavimento industrial"
  },
  "chemieindustrie": {
    "heading": "Revisar la superficie expuesta a productos químicos antes de licitar",
    "intro": "El sector por sí solo no determina los requisitos de impermeabilización: lo determinante es el tipo de instalación, los medios químicos, las propiedades de las sustancias y las reglas técnicas aplicables.",
    "requiredInputs": [
      "Lista de medios químicos con concentraciones, temperaturas y tiempos de exposición",
      "Tipo y clasificación de la instalación y justificantes necesarios según WHG y AwSV",
      "Detalles de encuentros, concepto de inspección y solicitación mecánica de la capa de protección"
    ],
    "decisionRule": "La resistencia química, los posibles requisitos ESD y la idoneidad de la impermeabilización deben comprobarse por separado; no se presupone un sistema de pavimentación certificado para todas las situaciones.",
    "relatedUrl": "/wissen/whg-abdichtung-industrieboden-pflicht/",
    "relatedLabel": "Cuándo se requiere impermeabilización WHG"
  },
  "keramische-industrieboeden": {
    "heading": "Evaluar por separado la baldosa cerámica y el método de colocación",
    "intro": "DIN EN 14411 define propiedades de las baldosas cerámicas. No constituye una acreditación general de la idoneidad de la colocación por vibración para cualquier solicitación industrial.",
    "requiredInputs": [
      "Características y certificados de ensayo de las baldosas cerámicas elegidas",
      "Soporte, método de colocación, adherencia y juntas de movimiento constructivas",
      "Cargas por rueda, resistencia química de las juntas y resistencia al deslizamiento necesaria"
    ],
    "decisionRule": "Las propiedades del material, la calidad de colocación y la composición de las juntas forman un sistema completo. La circulación solo debe preverse tras la autorización específica del sistema.",
    "relatedUrl": "/wissen/ruettelkeramik-agi-s-40/",
    "relatedLabel": "Capas del pavimento por vibración y AGI S 40 en detalle"
  },
  "pu-beton-industrieboden": {
    "heading": "Especificar PU-cemento solo con una composición de sistema autorizada",
    "intro": "El espesor de capa, la exposición térmica y los productos de limpieza dependen del producto. Las afirmaciones generales sobre limpieza con vapor o tiempo de curado no son una base técnica fiable.",
    "requiredInputs": [
      "Autorizaciones del fabricante sobre temperaturas, productos químicos y espesor de capa necesario",
      "Humedad y estado del soporte, y juntas de movimiento",
      "Momento más temprano de reanudación de la producción tras la colocación y limpieza"
    ],
    "decisionRule": "La idoneidad frente a choques térmicos y para las condiciones de higiene se deduce de los datos del sistema y de las condiciones de uso. Para cargas puntuales elevadas, el revestimiento cerámico puede ser una alternativa.",
    "relatedUrl": "/leistungen/keramische-industrieboeden/",
    "relatedLabel": "Pavimentos cerámicos industriales como alternativa"
  },
  "whg-abdichtung-industrieboden": {
    "heading": "Delimitar de forma sistemática los requisitos WHG/AwSV",
    "intro": "El § 62 WHG establece requisitos para determinadas instalaciones con sustancias peligrosas para el agua. La AwSV concreta la obligación de recurrir a empresas especializadas, que no se aplica automáticamente a toda superficie sometida a productos químicos.",
    "requiredInputs": [
      "Descripción de la instalación y lista de medios químicos de la zona de uso concreta",
      "Cuando corresponda, justificantes de idoneidad aplicables al producto impermeabilizante y a los encuentros",
      "Requisitos documentales y de inspección del titular y de los organismos competentes"
    ],
    "decisionRule": "Primero se determinan las obligaciones de la instalación y el concepto de protección; después se eligen materiales, certificados de ensayo y detalles de ejecución. Una garantía general de aprobación DIBt no resulta adecuada.",
    "relatedUrl": "/wissen/whg-abdichtung-industrieboden-pflicht/",
    "relatedLabel": "Fundamentos legales de WHG"
  }
};
