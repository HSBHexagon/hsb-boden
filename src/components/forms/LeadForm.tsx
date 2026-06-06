import { useState } from "react";
import { loadOptions } from "../../lib/validation";
import { site } from "../../data/site";

type Status = "idle" | "submitting" | "error";

// Online-Versand nur aktiv, wenn ein Zustell-Endpoint (Provider/CRM) konfiguriert ist.
const deliveryConfigured = Boolean(site.leadEndpoint);

export function LeadForm() {
  const [started, setStarted] = useState(false);
  const [status, setStatus] = useState<Status>("idle");

  function onFocus() {
    if (!started) {
      setStarted(true);
      window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event: "lead_form_start" } }));
    }
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deliveryConfigured) return;

    const form = event.currentTarget;
    const fd = new FormData(form);
    const payload: Record<string, unknown> = {
      source: "website",
      legalBasis: "inquiry",
      firstName: fd.get("firstName"),
      lastName: fd.get("lastName"),
      company: fd.get("company"),
      email: fd.get("email"),
      phone: fd.get("phone"),
      industry: fd.get("industry"),
      projectType: fd.get("projectType"),
      areaSize: fd.get("areaSize") ?? "",
      liveOperation: fd.get("liveOperation"),
      loads: fd.getAll("loads"),
      message: fd.get("message"),
      privacyConsent: fd.get("privacyConsent") === "on",
    };
    // Manche Provider (z.B. Web3Forms) erwarten den Access-Key im Payload.
    if (site.leadAccessKey) payload.access_key = site.leadAccessKey;

    setStatus("submitting");
    try {
      const res = await fetch(site.leadEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Status ${res.status}`);
      window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event: "lead_form_submit" } }));
      window.location.href = "/danke-projektanfrage/";
    } catch {
      setStatus("error");
    }
  }

  return (
    <form className="surface grid gap-4 p-5" onSubmit={onSubmit} onFocus={onFocus}>
      {!deliveryConfigured ? (
        <div className="rounded border border-hsb-red/30 bg-hsb-red/5 p-4 text-sm leading-6 text-hsb-black">
          <p className="font-black">Direkter Draht ins Projektgeschäft</p>
          <p className="mt-1 text-hsb-steel">
            Für eine schnelle Ersteinschätzung erreichen Sie HSB direkt:
          </p>
          <p className="mt-2 font-bold">
            <a className="text-hsb-red hover:underline" href={`tel:${site.phone.replace(/[^+\d]/g, "")}`}>{site.phone}</a>
            <span className="mx-2 text-hsb-line">·</span>
            <a className="text-hsb-red hover:underline" href={`mailto:${site.email}`}>{site.email}</a>
          </p>
        </div>
      ) : null}

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

      {status === "error" ? (
        <p className="rounded border border-hsb-red/40 bg-hsb-red/5 px-3 py-2 text-sm text-hsb-red">
          Senden fehlgeschlagen. Bitte kontaktieren Sie uns direkt unter {site.phone} oder {site.email}.
        </p>
      ) : null}

      <button
        className="button-primary disabled:cursor-not-allowed disabled:opacity-60"
        type="submit"
        disabled={!deliveryConfigured || status === "submitting"}
      >
        {!deliveryConfigured
          ? "Bitte direkt anrufen oder mailen"
          : status === "submitting"
            ? "Wird gesendet …"
            : "Projektanfrage senden"}
      </button>
    </form>
  );
}
