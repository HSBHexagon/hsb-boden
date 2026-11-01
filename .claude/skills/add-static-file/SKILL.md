---
name: add-static-file
description: Legt eine statische Datei im Stammverzeichnis der Website ab (z. B. Domain-Verifizierung, robots, Verifikations-HTML) und prüft, dass sie nach dem Deployment wirklich erreichbar ist. Verwenden, wenn eine Datei unter hsb-boden.de/<name> ausgeliefert werden soll.
---

# Statische Datei im Website-Root

Statische Dateien liegen in `apps/website/public/` und werden nach dem Deployment unter `https://www.hsb-boden.de/<name>` ausgeliefert.

## Ablauf
1. Datei **unverändert** nach `apps/website/public/<name>` kopieren (Verifizierungsdateien nicht umformatieren).
2. `apps/website/public/_redirects` und `_headers` lesen: Keine Regel darf die Datei umleiten oder blockieren. Die Domain-Kanonisierung (`hsb-boden.com` nach `www.hsb-boden.de`) ist gewollt; eine einzelne Weiterleitung auf `www` ist für Anbieter wie Atlassian erlaubt.
3. Lokal prüfen: Dev-Server starten (`npm --prefix apps/website run dev`), dann `curl -s -o /dev/null -w "%{http_code}" http://localhost:4321/<name>` — erwartet 200 — und prüfen, dass der erwartete Inhalt/Token enthalten ist.
4. Auf eigenem Branch committen, nur den exakten Pfad stagen (`git add apps/website/public/<name>`, nie `git add .`). `public/` zählt laut `CLAUDE.md` zum Website-Code: nur mit Freigabe.
5. Nach Merge und Production-Deploy (manueller Workflow): Statuscode und Weiterleitungen mit `curl -sIL -o /dev/null -w "%{http_code} %{num_redirects}" https://hsb-boden.de/<name>` prüfen (erwartet 200, höchstens eine Weiterleitung) und **zusätzlich den Inhalt per GET holen** (`curl -sL https://hsb-boden.de/<name> | grep -c "<erwartetes Token>"`, erwartet mindestens 1). `-I` zeigt nur Header, eine veraltete Datei mit Status 200 würde sonst fälschlich bestehen.
6. Die Datei dauerhaft behalten; Anbieter prüfen sie regelmäßig erneut.
