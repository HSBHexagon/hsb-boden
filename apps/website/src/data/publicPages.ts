import { site } from "./site";

export interface PublicPage {
  h1: string;
  seoTitle: string;
  description: string;
  canonicalPath: string;
}

export const staticPublicPages: PublicPage[] = [
  {
    h1: "Industrieböden und Säureschutzsysteme für produktionskritische Bereiche",
    seoTitle: site.defaultTitle,
    description: site.defaultDescription,
    canonicalPath: "/",
  },
  {
    h1: "Leistungen für Industrieböden und Säureschutz",
    seoTitle: "Leistungen: Rüttelkeramik, Säureschutz & WHG | HSB Hexagon",
    description:
      "Ingenieurbau für Industrieböden: Rüttelkeramik nach AGI S 40, Säureschutz, PU-Beton, Epoxidharz, Entwässerung, WHG § 62 Abdichtung und Sanierung im Betrieb.",
    canonicalPath: "/leistungen/",
  },
  {
    h1: "Branchenspezifische Industrieböden",
    seoTitle: "Industrieböden nach Branche | HSB Hexagon Säurebau",
    description:
      "Industrieböden für Lebensmittelindustrie, Molkereien, Brauereien, Chemie, Pharma, Backwarenproduktion und Großküchen.",
    canonicalPath: "/branchen/",
  },
  {
    h1: "Referenzen aus produktionskritischen Bereichen",
    seoTitle:
      "Referenzen für Industrieböden & Säureschutz | HSB Hexagon Säurebau",
    description:
      "Ausgewählte Referenzen für Industrieböden, Säureschutz, Keramik, Entwässerung und Sanierung.",
    canonicalPath: "/referenzen/",
  },
  {
    h1: "Wissen zu Industrieböden, Säureschutz und Sanierung",
    seoTitle: "Wissen zu Industrieböden & Säureschutz | HSB Hexagon Säurebau",
    description:
      "Praxisnahes Wissen zu PU-Beton, keramischen Industrieböden, Molkereiböden, säurefesten Fliesen, Entwässerung und Sanierung.",
    canonicalPath: "/wissen/",
  },
  {
    h1: "Ein klarer Projektablauf für produktionskritische Bodenflächen",
    seoTitle: "Projektablauf für Industrieböden und Säureschutz | HSB",
    description:
      "Vom Belastungsprofil bis zur Abnahme: So strukturiert HSB Analyse, Systemauslegung, Untergrundvorbereitung, Einbau und Dokumentation von Industriebodenprojekten.",
    canonicalPath: "/projektablauf/",
  },
  {
    h1: "Projektanfrage für Industrieböden",
    seoTitle: "Technisches Vor-Ort-Audit anfragen | HSB Hexagon Säurebau",
    description:
      "Vor-Ort-Audit für Industrieböden: Belastungsprofil, Untergrund und Sanierungsfenster ingenieurseitig bewertet – Rüttelkeramik, Säureschutz, WHG-Abdichtung.",
    canonicalPath: "/kontakt/",
  },
  {
    h1: "Technischer Beanspruchungs-Check für Produktionsböden",
    seoTitle: "Beanspruchungs-Check für Industrieböden | HSB Hexagon",
    description:
      "Medium, Temperatur, Last und Sanierungsfenster eingeben – deterministische Systemempfehlung nach AGI S 40, PU-Beton oder WHG § 62 mit direktem Vor-Ort-Audit.",
    canonicalPath: "/beanspruchungs-check/",
  },
  {
    h1: "Danke für Ihre Projektanfrage",
    seoTitle: "Danke für Ihre Projektanfrage | HSB Hexagon Säurebau",
    description:
      "Ihre Anfrage wurde vorbereitet. HSB meldet sich zur technischen Bewertung von Industrieboden, Säureschutz oder Sanierung.",
    canonicalPath: "/danke-projektanfrage/",
  },
  {
    h1: "Karriere bei HSB Hexagon Säurebau",
    seoTitle: "Karriere bei HSB Hexagon Säurebau | Industrieboden-Projekte",
    description:
      "Karriere bei HSB: Arbeiten an anspruchsvollen Industrieböden, Säureschutzsystemen und Sanierungsprojekten in Produktionsbetrieben.",
    canonicalPath: "/karriere/",
  },
  // Rechtsseiten: gebaut, indexierbar und im Footer verlinkt — sie gehören
  // deshalb in die Sitemap. Titel und Beschreibung müssen mit den Werten in
  // src/pages/impressum/ bzw. src/pages/datenschutz/ übereinstimmen.
  {
    h1: "Impressum",
    seoTitle: "Impressum | HSB Hexagon Säurebau GmbH",
    description:
      "Impressum und Anbieterkennzeichnung der HSB Hexagon Säurebau GmbH, Benzstraße 6, 48599 Gronau.",
    canonicalPath: "/impressum/",
  },
  {
    h1: "Datenschutzinformation",
    seoTitle: "Datenschutz | HSB Hexagon Säurebau GmbH",
    description:
      "Datenschutzinformation der HSB Hexagon Säurebau GmbH nach DSGVO: Verarbeitung personenbezogener Daten, Rechtsgrundlagen, Speicherdauer, Löschung und Ihre Betroffenenrechte.",
    canonicalPath: "/datenschutz/",
  },
  {
    h1: "Industrieboden-Spezialist in Norddeutschland",
    seoTitle: "Industrieboden Hamburg | Keramische Böden & Säureschutz Nord",
    description:
      "Industrieboden Hamburg: Lasten, Übergänge, Entwässerung und mögliche Anforderungen an Auffangflächen im Betrieb einordnen.",
    canonicalPath: "/standorte/hamburg/",
  },
  {
    h1: "Industrieboden-Spezialist in Bayern",
    seoTitle: "Industrieboden Bayern | Böden & Säureschutz München",
    description:
      "Industrieboden Bayern: Abfüllung, Gefälle, Rinnen, Reinigungstemperaturen und Keramik oder PU-Beton für die technische Planung vergleichen.",
    canonicalPath: "/standorte/bayern/",
  },
  {
    h1: "Industrieboden-Spezialist in Nordrhein-Westfalen",
    seoTitle: "Industrieboden NRW | Böden & Säureschutz",
    description:
      "Industrieboden NRW: Säureschutz, WHG-Flächen und Sanierung anhand von Medienliste, Fugen und Betriebsfenstern technisch bewerten.",
    canonicalPath: "/standorte/nrw/",
  },
  {
    h1: "Industrieboden-Spezialist in Rheinland-Pfalz",
    seoTitle: "Industrieboden Rheinland-Pfalz | Böden & Säureschutz",
    description:
      "Industrieboden Rheinland-Pfalz: Getränkeproduktion, Nasszonen und Reparaturen anhand von Medien, Gefälle und Betriebsfenstern planen.",
    canonicalPath: "/standorte/rheinland-pfalz/",
  },
  {
    h1: "Industrieboden-Spezialist in Baden-Württemberg",
    seoTitle: "Industrieboden Baden-Württemberg | Böden & Säureschutz",
    description:
      "Industrieboden Baden-Württemberg: Keramik, Fugenprofile und Entwässerung nach Radlast, Medien und Betriebsablauf auswählen.",
    canonicalPath: "/standorte/baden-wuerttemberg/",
  },
  {
    h1: "Industrieboden-Spezialist in Niedersachsen",
    seoTitle: "Industrieboden Niedersachsen | Böden & Säureschutz",
    description:
      "Industrieboden Niedersachsen: Feuchte, Milchsäure, Rinnenanschlüsse und Sanierungsfenster in Lebensmittelbetrieben fachlich bewerten.",
    canonicalPath: "/standorte/niedersachsen/",
  },
  {
    h1: "Industrieboden-Spezialist in Hessen",
    seoTitle: "Industrieboden Hessen | Böden & Säureschutz",
    description:
      "Industrieboden Hessen: Reinigungsvalidierung, chemische Beständigkeit und Dokumentation für Produktions- und Hygienebereiche planen.",
    canonicalPath: "/standorte/hessen/",
  },
  {
    h1: "Industrieboden-Spezialist in Thüringen",
    seoTitle: "Industrieboden Thüringen | Böden & Säureschutz",
    description:
      "Industrieboden Thüringen: Hygieneanschlüsse, Reparatur und Wiederinbetriebnahme abhängig von Bodenaufbau und Reinigungsanforderungen prüfen.",
    canonicalPath: "/standorte/thueringen/",
  },
  {
    h1: "Industrieboden-Spezialist in Sachsen-Anhalt",
    seoTitle: "Industrieboden Sachsen-Anhalt | Böden & Säureschutz",
    description:
      "Industrieboden Sachsen-Anhalt: Bestandsaufnahme, chemische Belastung und WHG-/AwSV-relevante Abdichtungen technisch klären.",
    canonicalPath: "/standorte/sachsen-anhalt/",
  },
];
