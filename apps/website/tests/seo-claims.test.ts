import { describe, expect, it } from "vitest";
import { keramischeIndustrieboeden } from "../src/data/services/keramische-industrieboeden";
import { whgAbdichtungIndustrieboden } from "../src/data/services/whg-abdichtung-industrieboden";
import { puBetonIndustrieboden } from "../src/data/services/pu-beton-industrieboden";
import { industries } from "../src/data/industries";

describe("Claims und technische Genauigkeit", () => {
  it("ordnet DIN EN 14411 dem Fliesenprodukt, nicht der Rüttelverlegung zu", () => {
    const text = [keramischeIndustrieboeden.systemSolution, ...keramischeIndustrieboeden.technicalRequirements].join(" ");
    expect(text).not.toMatch(/Rüttel(?:verlegung|verlegetechnik) nach DIN EN 14411/);
    expect(text).toMatch(/DIN EN 14411/);
    expect(text).toMatch(/Produkteigenschaften|Fliesen und Platten/);
  });

  it("verzichtet auf pauschale mechanische Lebensdauer-/Freigabe-Garantien", () => {
    const text = JSON.stringify(keramischeIndustrieboeden);
    expect(text).not.toMatch(/oft 25\+ Jahre|nach 48-72 Stunden|> 70 N\/mm²/);
  });

  it("garantiert weder pauschale WHG-Zulassung noch Vollschutz", () => {
    const text = JSON.stringify(whgAbdichtungIndustrieboden);
    expect(text).not.toMatch(/Vollständiger Schutz|Vollständige DIBt-Dokumentation|Höchste Beständigkeit/);
    expect(text).toMatch(/Medienliste|Anlage|AwSV/);
  });

  it("macht aus PU-Beton keine universelle Systemgarantie", () => {
    const text = JSON.stringify(puBetonIndustrieboden);
    expect(text).not.toMatch(/das einzige System|Keine mikrobielle Ansiedlung möglich|immer|dauerhaft beständig gegen Heißwasserreinigung/);
    expect(text).toMatch(/Hersteller|Produkt|System/);
  });

  it("leitet pH, Gefälle und Zertifikate nicht aus der Branche allein ab", () => {
    const dairy = industries.find((item) => item.slug === "molkerei")!;
    const chemical = industries.find((item) => item.slug === "chemieindustrie")!;
    expect(JSON.stringify(dairy)).not.toMatch(/pH-Werte von 0 bis 14|Gefälle \(> 2%\)/);
    expect(JSON.stringify(chemical)).not.toMatch(/gesamte Spektrum von pH 0 bis 14/);
  });
});
