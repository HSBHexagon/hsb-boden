export type Job = {
  slug: string;
  title: string;
  seoTitle: string;
  shortDescription: string;
  fullDescription: string;
  tasks: string[];
  profile: string[];
  offer: string[];
  employmentType: "FULL_TIME";
  occupationalCategory: string;
  // Reales Datum: Tag, an dem die Stelle erstmals öffentlich auf der Website
  // stand (initialer Commit der Karriere-Seite, 2026-06-05). Kein erfundenes
  // Datum — belegt per `git log --follow -- src/pages/karriere/index.astro`.
  datePosted: string;
};

export const jobs: Job[] = [
  {
    slug: "fliesenleger",
    title: "Fliesenleger (m/w/d) Industrieboden",
    seoTitle: "Fliesenleger (m/w/d) Industrieboden | Karriere bei HSB Hexagon Säurebau",
    shortDescription:
      "Verlegung und Sanierung keramischer Industrieböden, Säureschutzsysteme und technischer Detailpunkte in Lebensmittel-, Getränke- und Industrieproduktion.",
    fullDescription:
      "Sie verlegen und sanieren keramische Industrieböden und Säureschutzsysteme auf wechselnden Baustellen bei Kunden aus Lebensmittel-, Getränke- und Industrieproduktion. Der Schwerpunkt liegt auf technischen Detailpunkten: Säulen- und Sockelanschlüsse, Gefälle, Hohlkehlen und Abdichtungen, die unter laufender Produktion oder in kurzen Stillstandsfenstern dicht und belastbar ausgeführt werden müssen.",
    tasks: [
      "Verlegung keramischer Fliesen und Platten auf Industrieböden",
      "Ausführung von Säureschutzsystemen und Hohlkehlen",
      "Technische Detailpunkte: Säulen-, Sockel- und Wandanschlüsse",
      "Sanierungsarbeiten an bestehenden Industrieböden im laufenden Betrieb",
    ],
    profile: [
      "Erfahrung als Fliesenleger, idealerweise im Industrie- oder Gewerbebau",
      "Sorgfalt bei technischen Detailpunkten und Abdichtungen",
      "Bereitschaft zu wechselnden Einsatzorten auf Kundenbaustellen",
    ],
    offer: [
      "Technisch anspruchsvolle Projekte statt Standard-Bodenverlegung",
      "Arbeiten im eingespielten Team mit klaren Ausführungsstandards",
      "Meldeort und Disposition ab dem HSB-Standort in Gronau",
    ],
    employmentType: "FULL_TIME",
    occupationalCategory: "Bauwesen",
    datePosted: "2026-06-05",
  },
  {
    slug: "bauhelfer",
    title: "Bauhelfer mit Industrieerfahrung (m/w/d)",
    seoTitle: "Bauhelfer mit Industrieerfahrung (m/w/d) | Karriere bei HSB Hexagon Säurebau",
    shortDescription:
      "Unterstützung bei Verlegung und Sanierung keramischer Industrieböden und Säureschutzsystemen in Industriebetrieben.",
    fullDescription:
      "Sie unterstützen das Verlegeteam bei der Ausführung keramischer Industrieböden und Säureschutzsysteme auf Kundenbaustellen in der Industrie- und Lebensmittelproduktion — von der Baustellenvorbereitung über Materiallogistik bis zur Mithilfe bei Verlegung und Sanierung.",
    tasks: [
      "Vorbereitung und Absicherung der Baustelle",
      "Materialtransport und -logistik auf der Baustelle",
      "Mithilfe bei Verlegung und Sanierung keramischer Industrieböden",
      "Unterstützung bei Reinigungs- und Abschlussarbeiten",
    ],
    profile: [
      "Erfahrung auf Industrie- oder Baustellen von Vorteil",
      "Körperlich belastbar, zuverlässig im Team",
      "Bereitschaft zu wechselnden Einsatzorten auf Kundenbaustellen",
    ],
    offer: [
      "Einstieg in ein technisches Handwerk mit Entwicklungsperspektive",
      "Arbeiten im eingespielten Team mit klaren Ausführungsstandards",
      "Meldeort und Disposition ab dem HSB-Standort in Gronau",
    ],
    employmentType: "FULL_TIME",
    occupationalCategory: "Bauwesen",
    datePosted: "2026-06-05",
  },
  {
    slug: "projektleitung-industrieboden",
    title: "Projektleitung Industrieboden (m/w/d)",
    seoTitle: "Projektleitung Industrieboden (m/w/d) | Karriere bei HSB Hexagon Säurebau",
    shortDescription:
      "Planung, Koordination und Leitung von Projekten im Bereich keramische Industrieböden, Säureschutz und Sanierung für Industrie- und Lebensmittelbetriebe.",
    fullDescription:
      "Sie planen, koordinieren und leiten Projekte im Bereich keramische Industrieböden, Säureschutzsysteme und Sanierung für Industrie- und Lebensmittelbetriebe — von der technischen Klärung mit dem Kunden über Terminplanung und Materialdisposition bis zur Bauleitung vor Ort und Abnahme.",
    tasks: [
      "Technische Klärung und Angebotsvorbereitung mit dem Kunden",
      "Termin- und Ressourcenplanung für laufende Projekte",
      "Bauleitung und Qualitätskontrolle vor Ort auf Kundenbaustellen",
      "Koordination von Team, Material und Zeitfenstern im laufenden Betrieb",
    ],
    profile: [
      "Erfahrung in Bauleitung oder Projektleitung im Bau- oder Industriebereich",
      "Sicherer Umgang mit technischen Anforderungen an Industrieböden",
      "Reisebereitschaft zu wechselnden Kundenstandorten",
    ],
    offer: [
      "Verantwortung für technisch anspruchsvolle Industrieprojekte",
      "Direkter Draht zu Kunden aus Lebensmittel-, Getränke-, Pharma- und Chemieproduktion",
      "Meldeort und Disposition ab dem HSB-Standort in Gronau",
    ],
    employmentType: "FULL_TIME",
    occupationalCategory: "Bauwesen",
    datePosted: "2026-06-05",
  },
];

export function getJobs() {
  return jobs;
}

export function getJobBySlug(slug: string) {
  return jobs.find((job) => job.slug === slug);
}
