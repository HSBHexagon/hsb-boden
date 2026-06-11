import { useEffect, useMemo, useState } from "react";
import { resolveSuggestedLanguages, supportedLanguages } from "../../data/localization";

const storageKey = "hsb_language_offer_v1";

export function LanguageOffer() {
  const [visible, setVisible] = useState(false);
  const [locale, setLocale] = useState<string | undefined>();
  const suggestions = useMemo(() => resolveSuggestedLanguages(locale), [locale]);

  useEffect(() => {
    const browserLocale = navigator.languages?.[0] ?? navigator.language;
    setLocale(browserLocale);
    if (!window.localStorage.getItem(storageKey) && !browserLocale?.toLowerCase().startsWith("de")) {
      setVisible(true);
    }
  }, []);

  function choose(code: string) {
    window.localStorage.setItem(storageKey, code);
    window.dispatchEvent(new CustomEvent("hsb:language-choice", { detail: { code } }));
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <aside className="fixed right-3 top-20 z-40 w-[min(360px,calc(100vw-24px))] rounded-[4px] border border-hsb-line bg-white p-4 shadow-2xl" aria-label="Sprachangebot">
      <p className="eyebrow">Sprache</p>
      <h2 className="mt-2 text-lg font-black text-hsb-black">Diese Seite ist auf Deutsch. Sprache anbieten?</h2>
      <p className="mt-2 text-sm leading-6 text-hsb-steel">
        Die Fachinhalte bleiben verbindlich auf Deutsch. Für internationale Anfragen können wir die wichtigsten Einstiege mehrsprachig führen.
      </p>
      <div className="mt-4 grid gap-2">
        {suggestions.slice(0, 4).map((language) => (
          <button key={language.code} className="flex items-center justify-between rounded-[4px] border border-hsb-line px-3 py-2 text-left text-sm hover:border-hsb-red" type="button" onClick={() => choose(language.code)}>
            <span className="font-black">{language.nativeLabel}</span>
            <span className="text-xs text-hsb-steel">{language.shortHint}</span>
          </button>
        ))}
      </div>
      <button className="mt-3 text-sm font-black text-hsb-red" type="button" onClick={() => choose("de")}>
        Deutsch beibehalten
      </button>
      <p className="mt-3 text-xs leading-5 text-hsb-steel">
        Geplant: {supportedLanguages.map((language) => language.nativeLabel).join(" · ")}
      </p>
    </aside>
  );
}
