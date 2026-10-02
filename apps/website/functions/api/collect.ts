// GA4 verwendet ausschließlich den consent-gesteuerten Browsertransport.
// Alte Clients erhalten einen Fehler; keine unvalidierten Daten weiterleiten.
function retiredResponse(): Response {
  return new Response(JSON.stringify({ ok: false, error: "telemetry_endpoint_retired" }), {
    status: 410, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" },
  });
}
export async function onRequestPost(_context: { request: Request }): Promise<Response> { return retiredResponse(); }
export async function onRequestOptions(_context: { request: Request }): Promise<Response> { return retiredResponse(); }
export const onRequestGet = onRequestPost;
