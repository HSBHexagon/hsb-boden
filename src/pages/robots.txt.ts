export async function GET() {
  return new Response("User-agent: *\nAllow: /\nSitemap: https://www.hsb-boden.de/sitemap.xml\n", {
    headers: {
      "Content-Type": "text/plain",
    },
  });
}
