/** Regional engineering guidance: scenarios, not claims of local offices or executed projects. */
export interface RegionalGuide {
  label: string;
  summary: string;
  focus: string;
  diagnosticQuestions: [string, string, string];
  serviceSlugs: [string, string, string];
  industrySlugs: [string, string];
  articleSlug: string;
}

export const regionalGuides = {
  "nrw": {
    label: "Nordrhein-Westfalen",
    summary: "Für chemisch belastete Flächen und nass gereinigte Produktionsbereiche ist nicht der Standortname, sondern das Belastungsprofil entscheidend. Zur Einordnung gehören Medienliste, Rinnenanschlüsse, Staplerverkehr und ein belastbarer Sanierungsablauf.",
    focus: "Chemische Beanspruchung, Nassbereiche und dicht ausgeführte Übergänge",
    diagnosticQuestions: ["Welche Chemikalien treffen in welcher Konzentration und Einwirkdauer auf Belag und Fugen?", "Welche Anforderungen ergeben sich aus der konkreten Anlage nach WHG und AwSV?", "Welche Reinigungs- und Transportwege müssen während der Sanierung nutzbar bleiben?"],
    serviceSlugs: ["whg-abdichtung-industrieboden", "industrieboden-saeureschutz", "bodensanierung-laufender-betrieb"],
    industrySlugs: ["chemieindustrie", "lebensmittelindustrie"],
    articleSlug: "whg-abdichtung-industrieboden-pflicht",
  },
  "bayern": {
    label: "Bayern",
    summary: "Bei Abfüllung, Brauereiprozessen und Lebensmittelverarbeitung müssen Gefälle, Rinnen, Reinigungstemperatur und fahrende Lasten zusammen betrachtet werden. Ein keramischer Belag oder PU-Beton ist erst nach Prüfung dieser Belastungen sinnvoll zu wählen.",
    focus: "Abfüllbereiche, thermische Reinigung und Entwässerung",
    diagnosticQuestions: ["Wie viel Reinigungswasser fällt pro Zyklus an und wo kann es sicher ablaufen?", "Welche Temperatursprünge und Reinigungsmedien wirken auf Fläche und Fugen?", "Welche Abschnitte können ohne Unterbrechung der gesamten Produktionslinie saniert werden?"],
    serviceSlugs: ["entwaesserung-industrieboden", "keramische-industrieboeden", "pu-beton-industrieboden"],
    industrySlugs: ["brauerei-getraenkeindustrie", "molkerei"],
    articleSlug: "entwaesserung-gefaelle-produktionsbereiche",
  },
  "hamburg": {
    label: "Hamburg und Norddeutschland",
    summary: "Für Umschlag, Lagerung und nass beanspruchte Produktionsflächen lohnt sich die getrennte Bewertung von Transportlast, Eintrag von Feuchtigkeit und eventuellen chemischen Stoffen. Aus dem Einsatzgebiet allein ergibt sich keine bestimmte Abdichtungspflicht.",
    focus: "Umschlagbelastung, Transportwege und mögliche Stoffeinträge",
    diagnosticQuestions: ["Welche Radlasten, Fahrzyklen und Scherkräfte entstehen an den Fugen?", "Sind wassergefährdende Stoffe beteiligt und welche Anforderungen gelten für diese Anlage?", "Wo liegen Übergänge zwischen trockenen Verkehrsflächen und dauerhaft nassen Zonen?"],
    serviceSlugs: ["dehnungsfugen-rammschutz-industrieboden", "whg-abdichtung-industrieboden", "boden-reparatur-instandsetzung"],
    industrySlugs: ["chemieindustrie", "lebensmittelindustrie"],
    articleSlug: "rutschhemmklassen-r9-bis-r13-industrieboden",
  },
  "hessen": {
    label: "Hessen",
    summary: "Bei chemischen und pharmazeutischen Produktionsflächen stehen häufig Reinigbarkeit, Materialbeständigkeit und dokumentierbare Anschlussdetails im Vordergrund. Reinraumanforderungen und der tatsächliche Bodenaufbau müssen jeweils anlagenspezifisch geklärt werden.",
    focus: "Reinigungsprozesse, Medienbeständigkeit und Detaildokumentation",
    diagnosticQuestions: ["Welches Reinigungs- und Desinfektionsverfahren ist für den Bereich tatsächlich vorgesehen?", "Welche Beständigkeits- oder ESD-Nachweise verlangt das Nutzungskonzept?", "Wie werden Anschlüsse an Durchdringungen, Sockel und Entwässerungen bewertet?"],
    serviceSlugs: ["epoxidharz-bodenbeschichtung", "industrieboden-saeureschutz", "whg-abdichtung-industrieboden"],
    industrySlugs: ["pharmaindustrie", "chemieindustrie"],
    articleSlug: "esd-ableitfaehigkeit-explosionsschutz-industrieboden",
  },
  "niedersachsen": {
    label: "Niedersachsen",
    summary: "In der Milch- und Lebensmittelverarbeitung wirken Nässe, organische Säuren und regelmäßige Reinigung oft gemeinsam. Bei einer Sanierung müssen Fugen und Entwässerung ebenso geprüft werden wie die verfügbare Zeit bis zur Wiederinbetriebnahme.",
    focus: "Milchverarbeitung, Hygienezonen und Sanierung in Etappen",
    diagnosticQuestions: ["Wo entstehen an Rinnen oder Hohlkehlen bereits undichte Stellen?", "Welche Reinigungsmedien und Temperaturen sind im Schichtbetrieb üblich?", "Welche Produktions- und Hygienegrenzen gelten für Bauabschnitte?"],
    serviceSlugs: ["keramische-industrieboeden", "entwaesserung-industrieboden", "bodensanierung-laufender-betrieb"],
    industrySlugs: ["molkerei", "lebensmittelindustrie"],
    articleSlug: "warum-industrieboeden-in-molkereien-versagen",
  },
  "baden-wuerttemberg": {
    label: "Baden-Württemberg",
    summary: "Für Getränkeabfüllung und technisch belastete Produktionsflächen sind punktuelle Radlasten, Fugenkanten und planmäßige Reinigung zentrale Planungsgrößen. Die Systementscheidung benötigt Betriebsdaten und die konkreten Herstellerangaben.",
    focus: "Abfülltechnik, Punktlasten und dauerhaft belastete Fugen",
    diagnosticQuestions: ["Welche Lasten und Fahrbewegungen beanspruchen die Fläche und ihre Fugen?", "Welche Fugen sind Bewegungsfugen und welche dürfen nicht überbaut werden?", "Wie greifen Oberbelag und Entwässerungsrinne konstruktiv ineinander?"],
    serviceSlugs: ["keramische-industrieboeden", "dehnungsfugen-rammschutz-industrieboden", "entwaesserung-industrieboden"],
    industrySlugs: ["brauerei-getraenkeindustrie", "lebensmittelindustrie"],
    articleSlug: "hohlkehle-sockelausbildung-industrieboden",
  },
  "rheinland-pfalz": {
    label: "Rheinland-Pfalz",
    summary: "In Getränke- und Lebensmittelbetrieben sollte vor der Auswahl eines Bodensystems die Kombination aus Reinigungsmedien, Gefälle, Entwässerungsdetails und saisonalen Betriebsfenstern betrachtet werden. Eine passende Lösung ist vom Einzelfall abhängig.",
    focus: "Getränkeproduktion, Ablaufplanung und angepasste Sanierungsfenster",
    diagnosticQuestions: ["Welche Medien und Reinigungsmittel treten im Nassbereich auf?", "Führt das vorhandene Gefälle Wasser zu den vorgesehenen Abläufen?", "Wie werden Reparaturabschnitte und Freigaben für die Wiederinbetriebnahme geplant?"],
    serviceSlugs: ["entwaesserung-industrieboden", "boden-reparatur-instandsetzung", "pu-beton-industrieboden"],
    industrySlugs: ["brauerei-getraenkeindustrie", "lebensmittelindustrie"],
    articleSlug: "sanierung-ohne-produktionsstillstand",
  },
  "sachsen-anhalt": {
    label: "Sachsen-Anhalt",
    summary: "In industriellen Bestandsflächen treffen häufig unterschiedliche Beanspruchungen an Anschlüssen und Übergängen aufeinander. Vor der Erneuerung sollten Medien, Untergrundzustand und die geltenden Anforderungen an Auffang- oder Abdichtungsflächen dokumentiert werden.",
    focus: "Bestandsaufnahme, Säureschutz und Abdichtung an Übergängen",
    diagnosticQuestions: ["Welche Schadensbilder zeigen Fugen, Anschlüsse und Betonuntergrund?", "Ist die Fläche Teil einer Anlage mit Anforderungen nach WHG/AwSV?", "Welche Systemschichten und Prüfzeugnisse werden für die konkrete Nutzung benötigt?"],
    serviceSlugs: ["industrieboden-saeureschutz", "whg-abdichtung-industrieboden", "boden-reparatur-instandsetzung"],
    industrySlugs: ["chemieindustrie", "lebensmittelindustrie"],
    articleSlug: "saeurefeste-fliesen-industrieboden",
  },
  "thueringen": {
    label: "Thüringen",
    summary: "Bei lebensmittelverarbeitenden Produktionslinien zählen hygienische Übergänge, mechanische Belastung und kurze, abgestimmte Eingriffe in den Betrieb. Pauschale Aussagen zur Befahrbarkeit sind ohne Systemaufbau und konkrete Aushärtungsbedingungen nicht belastbar.",
    focus: "Hygienische Übergänge, Reparatur und Betriebsfenster",
    diagnosticQuestions: ["Wo treten wiederkehrende Schäden an Hohlkehlen und Rinnenflanschen auf?", "Welche Reinigungsintervalle und Temperaturwechsel sind zu berücksichtigen?", "Wann kann der gewählte Aufbau nach Herstellervorgabe wieder freigegeben werden?"],
    serviceSlugs: ["bodensanierung-laufender-betrieb", "keramische-industrieboeden", "boden-reparatur-instandsetzung"],
    industrySlugs: ["lebensmittelindustrie", "backwarenproduktion-grosskueche"],
    articleSlug: "sanierung-ohne-produktionsstillstand",
  },
} as const satisfies Record<string, RegionalGuide>;
