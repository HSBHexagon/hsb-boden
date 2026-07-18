export const STORAGE_KEY = "hsb-lang-suggest-v1";

export const variants: Record<
  string,
  { text: string; cta: string; href: string; dismiss: string }
> = {
  en: {
    text: "This page is in German. Would you like to view it in English?",
    cta: "View in English",
    href: "/en/",
    dismiss: "Continue in German",
  },
  tr: {
    text: "Bu sayfa Almanca. İçeriği Türkçe görüntülemek ister misiniz?",
    cta: "Türkçe görüntüle",
    href: "/tr/",
    dismiss: "Almanca devam et",
  },
  nl: {
    text: "Deze pagina is in het Duits. Wilt u de inhoud in het Nederlands bekijken?",
    cta: "Bekijk in het Nederlands",
    href: "/nl/",
    dismiss: "Doorgaan in het Duits",
  },
  pl: {
    text: "Ta strona jest po niemiecku. Czy chcesz zobaczyć treść po polsku?",
    cta: "Zobacz po polsku",
    href: "/pl/",
    dismiss: "Kontynuuj po niemiecku",
  },
  fr: {
    text: "Cette page est en allemand. Souhaitez-vous l'afficher en français ?",
    cta: "Afficher en français",
    href: "/fr/",
    dismiss: "Continuer en allemand",
  },
};

export function initLanguageSuggest(
  document: Document,
  navigator: Navigator,
  localStorage: Storage,
) {
  const banner = document.getElementById("lang-suggest");
  if (!banner) return;

  let dismissed = false;
  try {
    dismissed = localStorage.getItem(STORAGE_KEY) === "dismissed";
  } catch {
    dismissed = false;
  }
  if (dismissed) return;

  const browserLang = (navigator.languages?.[0] ?? navigator.language ?? "de")
    .slice(0, 2)
    .toLowerCase();
  if (browserLang === "de") return;

  const variant = variants[browserLang] ?? variants.en;
  const text = document.getElementById("lang-suggest-text");
  const link = document.getElementById(
    "lang-suggest-link",
  ) as HTMLAnchorElement | null;
  const dismiss = document.getElementById("lang-suggest-dismiss");
  if (!text || !link || !dismiss) return;

  text.textContent = variant.text;
  link.textContent = variant.cta;
  link.href = variant.href;
  dismiss.textContent = variant.dismiss;

  dismiss.addEventListener("click", () => {
    try {
      localStorage.setItem(STORAGE_KEY, "dismissed");
    } catch {
      /* ohne Storage nur für diese Seite ausblenden */
    }
    banner.classList.add("hidden");
  });

  banner.classList.remove("hidden");
}
