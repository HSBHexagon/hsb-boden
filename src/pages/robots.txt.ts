export async function GET() {
  return new Response("User-agent: *\nAllow: /\nSitemap: https://hsb-boden.de/sitemap.xml\n", {
    headers: {
      "Content-Type": "text/plain",
    },
  });
}
