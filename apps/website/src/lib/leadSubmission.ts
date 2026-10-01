/** HTTP-Erfolg allein bestätigt keine angenommene Projektanfrage. */
export async function submitLeadInquiry(payload: Record<string, unknown>, request: typeof fetch = fetch): Promise<void> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await request("/api/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload), signal: controller.signal,
    });
    if (!response.ok) throw new Error("lead_rejected");
    const result: unknown = await response.json();
    if (!result || typeof result !== "object" || Array.isArray(result) ||
        (result as Record<string, unknown>).ok !== true) throw new Error("lead_not_acknowledged");
  } finally { clearTimeout(timeout); }
}
