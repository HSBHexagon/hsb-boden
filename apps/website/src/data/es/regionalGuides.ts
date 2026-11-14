import type { SpanishRegionalGuide } from "../../lib/spanishTypes";

export const spanishRegionalGuides: Record<string, SpanishRegionalGuide> = {
  "nrw": {
    "label": "Renania del Norte-Westfalia",
    "summary": "En superficies expuestas a productos químicos y áreas de producción con limpieza húmeda, lo decisivo no es el nombre de la ubicación, sino el perfil de solicitaciones. Para evaluarlo se necesitan la lista de medios químicos, los encuentros con las canaletas, el tráfico de carretillas y un proceso de rehabilitación viable.",
    "focus": "Exposición química, zonas húmedas y transiciones estancas",
    "diagnosticQuestions": [
      "¿Qué productos químicos alcanzan el revestimiento y las juntas, con qué concentración y durante cuánto tiempo?",
      "¿Qué requisitos WHG y AwSV se derivan de la instalación concreta?",
      "¿Qué vías de limpieza y transporte deben seguir utilizándose durante la rehabilitación?"
    ],
    "serviceSlugs": [
      "whg-abdichtung-industrieboden",
      "industrieboden-saeureschutz",
      "bodensanierung-laufender-betrieb"
    ],
    "industrySlugs": [
      "chemieindustrie",
      "lebensmittelindustrie"
    ],
    "articleSlug": "whg-abdichtung-industrieboden-pflicht"
  },
  "bayern": {
    "label": "Baviera",
    "summary": "En el llenado de bebidas, los procesos de cervecería y el procesado de alimentos deben considerarse conjuntamente las pendientes, las canaletas, la temperatura de limpieza y las cargas de tráfico. La elección de cerámica o PU-cemento solo resulta fundamentada tras comprobar estas solicitaciones.",
    "focus": "Zonas de llenado, limpieza térmica y drenaje",
    "diagnosticQuestions": [
      "¿Cuánta agua de limpieza se produce en cada ciclo y dónde puede evacuarse de forma segura?",
      "¿Qué cambios de temperatura y productos de limpieza actúan sobre la superficie y las juntas?",
      "¿Qué tramos pueden rehabilitarse sin interrumpir toda la línea de producción?"
    ],
    "serviceSlugs": [
      "entwaesserung-industrieboden",
      "keramische-industrieboeden",
      "pu-beton-industrieboden"
    ],
    "industrySlugs": [
      "brauerei-getraenkeindustrie",
      "molkerei"
    ],
    "articleSlug": "entwaesserung-gefaelle-produktionsbereiche"
  },
  "hamburg": {
    "label": "Hamburgo y norte de Alemania",
    "summary": "En zonas de carga, almacenamiento y producción expuestas a humedad conviene evaluar por separado las cargas de transporte, la entrada de humedad y la posible presencia de sustancias químicas. La ubicación del trabajo por sí sola no determina una obligación concreta de impermeabilización.",
    "focus": "Cargas de manipulación, vías de transporte y posibles entradas de sustancias",
    "diagnosticQuestions": [
      "¿Qué cargas por rueda, ciclos de circulación y esfuerzos cortantes se producen en las juntas?",
      "¿Intervienen sustancias peligrosas para el agua y qué requisitos se aplican a esta instalación?",
      "¿Dónde se encuentran las transiciones entre vías secas y zonas permanentemente húmedas?"
    ],
    "serviceSlugs": [
      "dehnungsfugen-rammschutz-industrieboden",
      "whg-abdichtung-industrieboden",
      "boden-reparatur-instandsetzung"
    ],
    "industrySlugs": [
      "chemieindustrie",
      "lebensmittelindustrie"
    ],
    "articleSlug": "rutschhemmklassen-r9-bis-r13-industrieboden"
  },
  "hessen": {
    "label": "Hesse",
    "summary": "En las superficies de producción química y farmacéutica suelen ser prioritarias la facilidad de limpieza, la resistencia de los materiales y la documentación de los encuentros. Los requisitos de sala limpia y la composición real del pavimento deben aclararse para cada instalación.",
    "focus": "Procesos de limpieza, resistencia química y documentación de detalles",
    "diagnosticQuestions": [
      "¿Qué procedimiento de limpieza y desinfección está realmente previsto para la zona?",
      "¿Qué justificantes de resistencia o ESD exige el concepto de uso?",
      "¿Cómo se evalúan los encuentros con penetraciones, zócalos y elementos de drenaje?"
    ],
    "serviceSlugs": [
      "epoxidharz-bodenbeschichtung",
      "industrieboden-saeureschutz",
      "whg-abdichtung-industrieboden"
    ],
    "industrySlugs": [
      "pharmaindustrie",
      "chemieindustrie"
    ],
    "articleSlug": "esd-ableitfaehigkeit-explosionsschutz-industrieboden"
  },
  "niedersachsen": {
    "label": "Baja Sajonia",
    "summary": "En el procesado de leche y alimentos, la humedad, los ácidos orgánicos y la limpieza periódica suelen actuar conjuntamente. Durante una rehabilitación deben comprobarse tanto las juntas y el drenaje como el tiempo disponible hasta la puesta en servicio.",
    "focus": "Procesado de leche, zonas higiénicas y rehabilitación por etapas",
    "diagnosticQuestions": [
      "¿Dónde hay ya filtraciones junto a canaletas o medias cañas?",
      "¿Qué productos de limpieza y temperaturas son habituales durante los turnos?",
      "¿Qué límites de producción e higiene se aplican a las fases de obra?"
    ],
    "serviceSlugs": [
      "keramische-industrieboeden",
      "entwaesserung-industrieboden",
      "bodensanierung-laufender-betrieb"
    ],
    "industrySlugs": [
      "molkerei",
      "lebensmittelindustrie"
    ],
    "articleSlug": "warum-industrieboeden-in-molkereien-versagen"
  },
  "baden-wuerttemberg": {
    "label": "Baden-Wurtemberg",
    "summary": "En el llenado de bebidas y las superficies de producción con altas solicitaciones técnicas, las cargas puntuales por rueda, los bordes de juntas y la limpieza programada son variables centrales de la planificación. La elección del sistema requiere datos de funcionamiento e información concreta del fabricante.",
    "focus": "Tecnología de llenado, cargas puntuales y juntas sometidas a solicitaciones continuadas",
    "diagnosticQuestions": [
      "¿Qué cargas y movimientos de circulación solicitan la superficie y sus juntas?",
      "¿Qué juntas son de movimiento y cuáles no deben cubrirse con el revestimiento?",
      "¿Cómo se integran constructivamente el revestimiento y la canaleta de drenaje?"
    ],
    "serviceSlugs": [
      "keramische-industrieboeden",
      "dehnungsfugen-rammschutz-industrieboden",
      "entwaesserung-industrieboden"
    ],
    "industrySlugs": [
      "brauerei-getraenkeindustrie",
      "lebensmittelindustrie"
    ],
    "articleSlug": "hohlkehle-sockelausbildung-industrieboden"
  },
  "rheinland-pfalz": {
    "label": "Renania-Palatinado",
    "summary": "En empresas de bebidas y alimentación, antes de seleccionar el pavimento deben estudiarse conjuntamente los productos de limpieza, las pendientes, los detalles de drenaje y los periodos estacionales de trabajo disponibles. La solución adecuada depende de cada caso.",
    "focus": "Producción de bebidas, planificación de la evacuación y periodos de rehabilitación adaptados",
    "diagnosticQuestions": [
      "¿Qué medios químicos y productos de limpieza aparecen en la zona húmeda?",
      "¿La pendiente existente conduce el agua hasta los puntos de evacuación previstos?",
      "¿Cómo se planifican los tramos de reparación y las autorizaciones de puesta en servicio?"
    ],
    "serviceSlugs": [
      "entwaesserung-industrieboden",
      "boden-reparatur-instandsetzung",
      "pu-beton-industrieboden"
    ],
    "industrySlugs": [
      "brauerei-getraenkeindustrie",
      "lebensmittelindustrie"
    ],
    "articleSlug": "sanierung-ohne-produktionsstillstand"
  },
  "sachsen-anhalt": {
    "label": "Sajonia-Anhalt",
    "summary": "En superficies industriales existentes suelen coincidir distintas solicitaciones en encuentros y transiciones. Antes de renovar deben documentarse los medios químicos, el estado del soporte y los requisitos aplicables a las superficies de retención o impermeabilización.",
    "focus": "Evaluación inicial, protección contra ácidos e impermeabilización de transiciones",
    "diagnosticQuestions": [
      "¿Qué daños presentan las juntas, los encuentros y el soporte de hormigón?",
      "¿La superficie forma parte de una instalación sujeta a requisitos WHG/AwSV?",
      "¿Qué capas del sistema y certificados de ensayo se necesitan para el uso concreto?"
    ],
    "serviceSlugs": [
      "industrieboden-saeureschutz",
      "whg-abdichtung-industrieboden",
      "boden-reparatur-instandsetzung"
    ],
    "industrySlugs": [
      "chemieindustrie",
      "lebensmittelindustrie"
    ],
    "articleSlug": "saeurefeste-fliesen-industrieboden"
  },
  "thueringen": {
    "label": "Turingia",
    "summary": "En líneas de producción alimentaria son decisivos los encuentros higiénicos, la carga mecánica y las intervenciones breves coordinadas con la actividad. Las afirmaciones generales sobre la posibilidad de circular no son fiables sin conocer la composición del sistema y las condiciones concretas de curado.",
    "focus": "Encuentros higiénicos, reparación y periodos de trabajo disponibles",
    "diagnosticQuestions": [
      "¿Dónde aparecen daños recurrentes en medias cañas y bridas de canaletas?",
      "¿Qué intervalos de limpieza y cambios de temperatura deben considerarse?",
      "¿Cuándo puede ponerse de nuevo en servicio el sistema elegido según las indicaciones del fabricante?"
    ],
    "serviceSlugs": [
      "bodensanierung-laufender-betrieb",
      "keramische-industrieboeden",
      "boden-reparatur-instandsetzung"
    ],
    "industrySlugs": [
      "lebensmittelindustrie",
      "backwarenproduktion-grosskueche"
    ],
    "articleSlug": "sanierung-ohne-produktionsstillstand"
  }
};
