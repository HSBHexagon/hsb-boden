import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

describe("RepairModal & Zero-Friction Lead Flow", () => {
  const root = join(process.cwd(), "src");

  it("stellt die RepairModal-Komponente mit nativem Dialog und a11y bereit", () => {
    const modalPath = join(root, "components/forms/RepairModal.astro");
    expect(existsSync(modalPath)).toBe(true);

    const source = readFileSync(modalPath, "utf8");
    expect(source).toContain("<dialog");
    expect(source).toContain('id="repair-modal"');
    expect(source).toContain('aria-labelledby="repair-modal-title"');
    expect(source).toContain('aria-modal="true"');
    expect(source).toContain("showModal()");
    expect(source).toContain("close()");
    expect(source).toContain("data-open-repair-modal");
    expect(source).toContain("#foto-modal");
    expect(source).toContain("#schadstelle-melden");
    expect(source).toContain("openModal=repair");
    expect(source).toContain('idPrefix="modal-repair-photo"');
  });

  it("schließt nicht bei Tastatur-Klicks und respektiert den Upload-Schalter", () => {
    const source = readFileSync(join(root, "components/forms/RepairModal.astro"), "utf8");
    // Backdrop-Schließen nur, wenn der Klick den Dialog selbst trifft
    expect(source).toContain("if (event.target !== modal) return;");
    // Ohne PUBLIC_REPAIR_PHOTO_ENABLED wird kein Modal gerendert und kein Link abgefangen
    expect(source).toContain("const enabled = site.hasRepairPhotoUpload;");
    expect(source).toMatch(/\{enabled && \(\s*<dialog/);
    expect(source).toContain("if (modal && (trigger || linkTrigger))");
  });

  it("verankert RepairModal global im BaseLayout", () => {
    const layoutPath = join(root, "layouts/BaseLayout.astro");
    const source = readFileSync(layoutPath, "utf8");
    expect(source).toContain('import RepairModal from "../components/forms/RepairModal.astro"');
    expect(source).toContain("<RepairModal />");
  });

  it("verhindert in RepairInquirySection irreführende mailto-Buttons und priorisiert die Mobil-Reihenfolge", () => {
    const sectionPath = join(root, "components/forms/RepairInquirySection.astro");
    const source = readFileSync(sectionPath, "utf8");
    // Kein konkurrierender mailto-Link mehr, der Nutzer vom Web-Upload wegleitet
    expect(source).not.toContain("mailto:");
    expect(source).not.toContain("Per E-Mail senden");
    // Auf Mobilgeräten liegt das Formular oben (order-1), der Text stützt darunter (order-2)
    expect(source).toContain("order-1 lg:order-2");
    expect(source).toContain("order-2 lg:order-1");
    expect(source).toContain('id="reparaturanfrage"');
  });

  it("unterstützt in RepairPhotoForm mehrfache Instanzen über idPrefix und Container-Scoping", () => {
    const formPath = join(root, "components/forms/RepairPhotoForm.astro");
    const source = readFileSync(formPath, "utf8");
    expect(source).toContain("idPrefix");
    expect(source).toContain("data-repair-photo-container");
    expect(source).toContain("initRepairPhotoForm(container)");
    expect(source).toContain('canvas.toBlob(resolve, "image/jpeg", 0.82)');
  });
});
