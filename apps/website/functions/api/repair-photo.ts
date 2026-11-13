// POST /api/repair-photo — Foto der Schadstelle direkt an HSB senden.
// Die Logik liegt in functions/lib/repair-photo-handler.ts; hier wird nur der echte TCP-Socket angebunden.
import { connect } from "cloudflare:sockets";
import { handleRepairPhoto, type RepairPhotoEnv } from "../lib/repair-photo-handler";

interface Context {
  request: Request;
  env: RepairPhotoEnv;
  waitUntil?: (promise: Promise<unknown>) => void;
}

export async function onRequestPost(context: Context): Promise<Response> {
  return handleRepairPhoto(
    context.request,
    context.env,
    (hostname, port) => connect({ hostname, port }, { secureTransport: "on", allowHalfOpen: false }),
    new Date(),
    // Die Eingangsbestätigung läuft nach der Antwort weiter, damit der Besucher nicht auf zwei SMTP-Sitzungen wartet.
    context.waitUntil?.bind(context),
  );
}
