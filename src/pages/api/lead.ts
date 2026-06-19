import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  const endpoint = import.meta.env.PUBLIC_LEAD_ENDPOINT;
  const accessKey = import.meta.env.LEAD_ACCESS_KEY;

  if (!endpoint) {
    return new Response(JSON.stringify({ error: "Lead endpoint not configured" }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }

  try {
    const payload = await request.json();

    // Add access key if configured
    if (accessKey) {
      payload.access_key = accessKey;
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Upstream returned ${response.status}`);
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    console.error("Lead delivery failed:", error);
    return new Response(JSON.stringify({ error: "Delivery failed" }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
};
