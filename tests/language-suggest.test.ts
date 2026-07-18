// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  initLanguageSuggest,
  STORAGE_KEY,
  variants,
} from "../src/lib/languageSuggest";

describe("LanguageSuggest", () => {
  let doc: Document;
  let mockNavigator: any;
  let mockStorage: any;
  let banner: HTMLElement;
  let textSpan: HTMLElement;
  let linkA: HTMLAnchorElement;
  let dismissButton: HTMLButtonElement;
  let store: Record<string, string>;

  beforeEach(() => {
    store = {};
    mockStorage = {
      getItem: vi.fn((key: string) => store[key] || null),
      setItem: vi.fn((key: string, value: string) => {
        store[key] = value;
      }),
    };

    mockNavigator = {
      languages: ["en-US", "en"],
      language: "en-US",
    };

    doc = document.implementation.createHTMLDocument();

    banner = doc.createElement("div");
    banner.id = "lang-suggest";
    banner.classList.add("hidden");

    textSpan = doc.createElement("span");
    textSpan.id = "lang-suggest-text";

    linkA = doc.createElement("a");
    linkA.id = "lang-suggest-link";

    dismissButton = doc.createElement("button");
    dismissButton.id = "lang-suggest-dismiss";

    banner.appendChild(textSpan);
    banner.appendChild(linkA);
    banner.appendChild(dismissButton);
    doc.body.appendChild(banner);
  });

  it("should not show banner if already dismissed", () => {
    store[STORAGE_KEY] = "dismissed";

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(true);
  });

  it("should handle storage exceptions gracefully when checking if dismissed", () => {
    mockStorage.getItem.mockImplementation(() => {
      throw new Error("SecurityError");
    });

    // Default language is en, banner should show
    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
  });

  it("should not show banner if browser language is German", () => {
    mockNavigator.languages = ["de-DE", "de"];
    mockNavigator.language = "de-DE";

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(true);
  });

  it("should fall back to navigator.language if navigator.languages is unavailable", () => {
    mockNavigator.languages = undefined;
    mockNavigator.language = "de-DE";

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(true);
  });

  it("should show correct English variant", () => {
    mockNavigator.languages = ["en-US"];

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
    expect(textSpan.textContent).toBe(variants.en.text);
    expect(linkA.textContent).toBe(variants.en.cta);
    expect(linkA.href).toContain(variants.en.href);
    expect(dismissButton.textContent).toBe(variants.en.dismiss);
  });

  it("should show correct Turkish variant", () => {
    mockNavigator.languages = ["tr-TR"];

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
    expect(textSpan.textContent).toBe(variants.tr.text);
  });

  it("should show correct Dutch variant", () => {
    mockNavigator.languages = ["nl-NL"];

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
    expect(textSpan.textContent).toBe(variants.nl.text);
  });

  it("should show correct Polish variant", () => {
    mockNavigator.languages = ["pl-PL"];

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
    expect(textSpan.textContent).toBe(variants.pl.text);
  });

  it("should show correct French variant", () => {
    mockNavigator.languages = ["fr-FR"];

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
    expect(textSpan.textContent).toBe(variants.fr.text);
  });

  it("should default to English for unmapped languages", () => {
    mockNavigator.languages = ["es-ES"];

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    expect(banner.classList.contains("hidden")).toBe(false);
    expect(textSpan.textContent).toBe(variants.en.text);
  });

  it("should dismiss the banner and save to storage when dismiss is clicked", () => {
    initLanguageSuggest(doc, mockNavigator, mockStorage);
    expect(banner.classList.contains("hidden")).toBe(false);

    dismissButton.click();

    expect(store[STORAGE_KEY]).toBe("dismissed");
    expect(banner.classList.contains("hidden")).toBe(true);
  });

  it("should dismiss the banner even if storage throws an error on setItem", () => {
    mockStorage.setItem.mockImplementation(() => {
      throw new Error("SecurityError");
    });

    initLanguageSuggest(doc, mockNavigator, mockStorage);
    expect(banner.classList.contains("hidden")).toBe(false);

    dismissButton.click();

    expect(banner.classList.contains("hidden")).toBe(true);
  });

  it("should exit early if required DOM elements are missing", () => {
    // Remove link
    banner.removeChild(linkA);

    initLanguageSuggest(doc, mockNavigator, mockStorage);

    // Banner should remain hidden because initialization aborts
    expect(banner.classList.contains("hidden")).toBe(true);
  });

  it("should exit early if banner is missing", () => {
    // Banner is missing entirely
    doc.body.removeChild(banner);

    // Verify it doesn't throw
    expect(() =>
      initLanguageSuggest(doc, mockNavigator, mockStorage),
    ).not.toThrow();
  });
});
