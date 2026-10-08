/** Procurement prompts for real engineers: no generic certification or lifetime guarantees. */
interface TechnicalDecisionGuide {
  heading: string;
  intro: string;
  requiredInputs: readonly [string, string, string];
  decisionRule: string;
  relatedUrl: string;
  relatedLabel: string;
}

export const technicalDecisionGuides = {
  "molkerei": {
    heading: "Vor der Bodenauswahl in der Molkerei klären",
    intro: "CIP-Reinigung, organische Säuren, Transportlast und Nassbereiche wirken häufig gleichzeitig. Die folgenden Angaben helfen bei einer belastbaren technischen Ersteinschätzung.",
    requiredInputs: ["CIP-Ablauf mit Reinigungsmitteln, Konzentration, Temperatur und Häufigkeit", "Plan der Entwässerung mit Gefälle, Rinnen, Sockeln und bekannten Schadstellen", "Betriebs- und Sperrzeiten sowie Belastungen durch Roll- und Hubwagen"],
    decisionRule: "Ob Keramik oder PU-Beton sinnvoll ist, hängt vor allem von Medien, Fugenbeanspruchung, Reinigung und Untergrund ab; kein Werkstoff eignet sich pauschal für jede Molkerei.",
    relatedUrl: "/wissen/pu-beton-oder-keramischer-industrieboden/",
    relatedLabel: "Keramik und PU-Beton technisch vergleichen",
  },
  "brauerei-getraenkeindustrie": {
    heading: "Abfüll- und Reinigungsbereiche planen",
    intro: "Bei Abfülllinien greifen Reinigung, Staplerverkehr und Entwässerung ineinander. Der Ablauf kann nicht unabhängig vom Bodenaufbau geplant werden.",
    requiredInputs: ["Lage von Maschinen, Rinnen und Feststoffeintrag aus dem Reinigungsprozess", "Häufigkeit der Reinigung, Temperaturwechsel sowie eingesetzte Laugen und Säuren", "Radlasten an Fugen, Rampen und Übergängen zwischen Produktionsabschnitten"],
    decisionRule: "Gefälleführung, Rinnenkonstruktion und Belag sind als System zu prüfen. Ein vorgegebener pauschaler Gefällewert ersetzt keine projektbezogene Planung.",
    relatedUrl: "/leistungen/entwaesserung-industrieboden/",
    relatedLabel: "Entwässerung und Gefälle im Industrieboden",
  },
  "chemieindustrie": {
    heading: "Chemisch belastete Fläche vor Ausschreibung prüfen",
    intro: "Nicht die Branche allein entscheidet über die Abdichtungsanforderung: Maßgeblich sind Anlagenart, Medien, Stoffeigenschaften und die anwendbaren technischen Regeln.",
    requiredInputs: ["Medienliste mit Konzentrationen, Temperatur und Einwirkdauer", "Anlagentyp und Einstufung sowie erforderliche Nachweise nach WHG und AwSV", "Anschlussdetails, Prüfkonzept und mechanische Beanspruchung der Schutzschicht"],
    decisionRule: "Chemische Beständigkeit, mögliche ESD-Anforderungen und Abdichtungseignung müssen separat geprüft werden; ein universell zertifiziertes Bodensystem wird nicht vorausgesetzt.",
    relatedUrl: "/wissen/whg-abdichtung-industrieboden-pflicht/",
    relatedLabel: "Wann WHG-Abdichtung notwendig wird",
  },
  "keramische-industrieboeden": {
    heading: "Keramischen Belag und Verlegeverfahren getrennt bewerten",
    intro: "DIN EN 14411 definiert Eigenschaften keramischer Fliesen und Platten. Das ist kein pauschaler Nachweis für die Eignung einer Rüttelverlegung unter jeder Industriebeanspruchung.",
    requiredInputs: ["Produktkennwerte und Prüfzeugnisse der gewählten keramischen Fliesen", "Untergrund, Einbauverfahren, Verbund und konstruktive Bewegungsfugen", "Radlasten, Medienbeständigkeit der Fuge und notwendige Rutschhemmung"],
    decisionRule: "Materialeigenschaften, Einbauqualität und Fugenaufbau bilden ein Gesamtsystem. Wiederbefahrbarkeit erst nach systembezogener Freigabe ansetzen.",
    relatedUrl: "/leistungen/pu-beton-industrieboden/",
    relatedLabel: "Alternative PU-Beton-Systeme vergleichen",
  },
  "pu-beton-industrieboden": {
    heading: "PU-Beton nur mit freigegebenem Systemaufbau spezifizieren",
    intro: "Schichtstärke, Temperaturbeanspruchung und Reinigungschemie sind produktabhängig. Pauschale Aussagen über Dampfreinigung oder Aushärtungszeit sind nicht belastbar.",
    requiredInputs: ["Herstellerfreigaben zu Temperatur, Chemikalien und erforderlicher Schichtstärke", "Substratfeuchte und Zustand des Untergrunds sowie Bewegungsfugen", "Frühester zulässiger Produktionsanlauf nach Einbau und Reinigung"],
    decisionRule: "Thermoschock- und Hygieneeignung aus Systemdaten und Einsatzbedingungen ableiten. Für schwere Punktlasten kann keramischer Belag eine Alternative sein.",
    relatedUrl: "/leistungen/keramische-industrieboeden/",
    relatedLabel: "Keramische Industrieböden als Alternative",
  },
  "whg-abdichtung-industrieboden": {
    heading: "WHG-/AwSV-Anforderungen systematisch eingrenzen",
    intro: "§ 62 WHG betrifft Anforderungen an bestimmte Anlagen mit wassergefährdenden Stoffen. Die Fachbetriebspflicht wird über die AwSV konkretisiert und gilt nicht pauschal für jede chemisch beanspruchte Bodenfläche.",
    requiredInputs: ["Beschreibung der Anlage und Medienliste für den konkreten Nutzungsbereich", "Gegebenenfalls einschlägige Eignungsnachweise von Abdichtungsprodukt und Anschlüssen", "Dokumentations- und Prüfanforderungen des Betreibers und zuständiger Stellen"],
    decisionRule: "Erst Anlagenpflicht und Schutzkonzept ermitteln, dann Material, Prüfzeugnisse und Detailausführung auswählen; eine allgemeine DIBt-Garantie ist nicht sachgerecht.",
    relatedUrl: "/wissen/whg-abdichtung-industrieboden-pflicht/",
    relatedLabel: "Die rechtlichen Grundlagen zum WHG",
  },
} as const satisfies Record<string, TechnicalDecisionGuide>;
