import { useEffect, useState } from "react";
import { consentCategories, getRequiredConsentCategories } from "../../data/consent";

const storageKey = "hsb_cookie_consent_v1";
const initialEnabled = () => Object.fromEntries(consentCategories.map((category) => [category.id, category.required]));

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [enabled, setEnabled] = useState<Record<string, boolean>>(initialEnabled);

  useEffect(() => {
    if (!window.localStorage.getItem(storageKey)) setVisible(true);
  }, []);

  useEffect(() => {
    const openSettings = (event: MouseEvent) => {
      if (!(event.target instanceof Element)) return;
      const trigger = event.target.closest("[data-cookie-reset]");
      if (!trigger) return;

      event.preventDefault();
      window.localStorage.removeItem(storageKey);
      setEnabled(initialEnabled());
      setVisible(true);
    };

    document.addEventListener("click", openSettings);
    return () => document.removeEventListener("click", openSettings);
  }, []);

  function save(choice: Record<string, boolean>) {
    const required = getRequiredConsentCategories();
    const next = {
      ...choice,
      ...Object.fromEntries(required.map((id) => [id, true])),
      savedAt: new Date().toISOString(),
    };
    window.localStorage.setItem(storageKey, JSON.stringify(next));
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: next }));
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <aside className="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-4xl rounded-[4px] border border-hsb-line bg-white p-4 shadow-2xl sm:p-5" aria-label="Cookie-Einstellungen">
      <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-start">
        <div>
          <p className="eyebrow">Privatsphäre</p>
          <h2 className="mt-2 text-xl font-black text-hsb-black">Cookie-Auswahl für HSB</h2>
          <p className="mt-2 text-sm leading-6 text-hsb-steel">
            Essenzielle Cookies sind notwendig. Analyse und Marketing werden erst nach Einwilligung genutzt und können später in den Cookie-Einstellungen geändert werden.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {consentCategories.map((category) => (
              <label key={category.id} className="rounded-[4px] border border-hsb-line p-3 text-sm">
                <span className="flex items-start gap-2 font-black text-hsb-black">
                  <input
                    type="checkbox"
                    checked={enabled[category.id]}
                    disabled={category.required}
                    onChange={(event) => setEnabled((current) => ({ ...current, [category.id]: event.target.checked }))}
                    className="mt-1"
                  />
                  {category.label}
                </span>
                <span className="mt-2 block text-xs leading-5 text-hsb-steel">{category.description}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-3 lg:w-56 lg:grid-cols-1">
          <button className="button-primary" type="button" onClick={() => save(Object.fromEntries(consentCategories.map((category) => [category.id, true])))}>
            Alle akzeptieren
          </button>
          <button className="button-secondary-dark" type="button" onClick={() => save(enabled)}>
            Auswahl speichern
          </button>
          <button className="button-secondary-dark" type="button" onClick={() => save(Object.fromEntries(consentCategories.map((category) => [category.id, category.required])))}>
            Nur essenziell
          </button>
        </div>
      </div>
    </aside>
  );
}
