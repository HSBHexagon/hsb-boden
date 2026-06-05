import { useState } from "react";
import { loadOptions } from "../../lib/validation";

export function LeadForm() {
  const [started, setStarted] = useState(false);

  function onFocus() {
    if (!started) {
      setStarted(true);
      window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event: "lead_form_start" } }));
    }
  }

  return (
    <form className="surface grid gap-4 p-5" action="/danke-projektanfrage/" method="get" onFocus={onFocus}>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-bold">
          Vorname
          <input required name="firstName" className="rounded border border-hsb-line px-3 py-3 font-normal" />
        </label>
        <label className="grid gap-2 text-sm font-bold">
          Nachname
          <input required name="lastName" className="rounded border border-hsb-line px-3 py-3 font-normal" />
        </label>
      </div>
      <label className="grid gap-2 text-sm font-bold">
        Firma
        <input required name="company" className="rounded border border-hsb-line px-3 py-3 font-normal" />
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-bold">
          E-Mail
          <input required type="email" name="email" className="rounded border border-hsb-line px-3 py-3 font-normal" />
        </label>
        <label className="grid gap-2 text-sm font-bold">
          Telefon
          <input required type="tel" name="phone" className="rounded border border-hsb-line px-3 py-3 font-normal" />
        </label>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-bold">
          Branche
          <select required name="industry" className="rounded border border-hsb-line px-3 py-3 font-normal">
            <option value="">Bitte wählen</option>
            <option value="lebensmittelindustrie">Lebensmittelindustrie</option>
            <option value="molkerei">Molkerei</option>
            <option value="brauerei-getraenkeindustrie">Brauerei/Getränke</option>
            <option value="chemieindustrie">Chemie</option>
            <option value="pharmaindustrie">Pharma</option>
          </select>
        </label>
        <label className="grid gap-2 text-sm font-bold">
          Projektart
          <select required name="projectType" className="rounded border border-hsb-line px-3 py-3 font-normal">
            <option value="">Bitte wählen</option>
            <option value="neubau">Neubau</option>
            <option value="sanierung">Sanierung</option>
            <option value="bewertung">Technische Bewertung</option>
          </select>
        </label>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-bold">
          Fläche in m²
          <input name="areaSize" className="rounded border border-hsb-line px-3 py-3 font-normal" />
        </label>
        <label className="grid gap-2 text-sm font-bold">
          Laufender Betrieb
          <select required name="liveOperation" className="rounded border border-hsb-line px-3 py-3 font-normal">
            <option value="">Bitte wählen</option>
            <option value="ja">Ja</option>
            <option value="nein">Nein</option>
            <option value="unklar">Unklar</option>
          </select>
        </label>
      </div>
      <fieldset className="grid gap-3">
        <legend className="text-sm font-black">Belastungen</legend>
        <div className="grid gap-2 sm:grid-cols-2">
          {loadOptions.map((option) => (
            <label className="flex items-center gap-2 text-sm text-hsb-steel" key={option}>
              <input type="checkbox" name="loads" value={option} />
              {option}
            </label>
          ))}
        </div>
      </fieldset>
      <label className="grid gap-2 text-sm font-bold">
        Nachricht
        <textarea required name="message" rows={5} className="rounded border border-hsb-line px-3 py-3 font-normal" />
      </label>
      <label className="flex items-start gap-3 text-sm leading-6 text-hsb-steel">
        <input required type="checkbox" name="privacyConsent" className="mt-1" />
        Ich stimme zu, dass meine Angaben zur Bearbeitung der Anfrage verarbeitet werden.
      </label>
      <button className="button-primary" type="submit">Projektanfrage senden</button>
    </form>
  );
}
