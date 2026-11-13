import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const mimeTypes = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "application/javascript",
  ".json": "application/json", ".webp": "image/webp", ".png": "image/png",
  ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".woff2": "font/woff2",
};

/** Statische Tests verwenden ausschließlich beim Start inventarisierte Build-Dateien. */
export function createStaticPreview(distDir = path.resolve("dist")) {
  const files = new Map();
  function indexDirectory(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) indexDirectory(file);
      if (!entry.isFile()) continue;
      const route = "/" + path.relative(distDir, file).split(path.sep).join("/");
      files.set(route, file);
      if (route.endsWith("/index.html")) files.set(route.slice(0, -10), file);
      else if (route.endsWith(".html")) files.set(route.slice(0, -5), file);
    }
  }
  indexDirectory(distDir);

  return http.createServer((req, res) => {
    let route;
    try {
      route = decodeURIComponent((req.url ?? "/").split("?")[0]);
    } catch {
      res.writeHead(400).end("Bad Request");
      return;
    }
    const file = files.get(route);
    if (!file) {
      res.writeHead(404).end("Not Found");
      return;
    }
    res.writeHead(200, { "Content-Type": mimeTypes[path.extname(file)] ?? "application/octet-stream" });
    fs.createReadStream(file).on("error", () => res.destroy()).pipe(res);
  });
}
