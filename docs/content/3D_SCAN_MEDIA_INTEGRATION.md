# 3D-Scan-Medienintegration

## Zweck

Die Startseite erhält einen eigenständigen Trust-/Prozessabschnitt zur digitalen Bestandsaufnahme vor der Industriebodenausführung. Die Darstellung bleibt bewusst neutral und vermeidet unbelegte Aussagen zu Eigentum, Partnerstatus, Messgenauigkeit oder Normkonformität.

## Öffentliche Assets

| Repo-Pfad | Quelle | Verwendung |
|---|---|---|
| `public/media/hsb/projekte/3d-scan/3d-scan-halle-uebersicht.webp` | Foto `297597.jpg` | Hallenübersicht mit Messaufbau und Referenzpunkten |
| `public/media/hsb/projekte/3d-scan/3d-scanner-detail.webp` | zugeschnittener Ausschnitt aus `297598.jpg` | Detailansicht des Messgeräts |
| `public/media/hsb/projekte/3d-scan/3d-scan-halle-poster.webp` | Standbild aus `297599.mp4` | Video-Poster |
| `public/media/hsb/projekte/3d-scan/3d-scan-halle.mp4` | weboptimierte Fassung von `297599.mp4` | 17-Sekunden-Prozessvideo, H.264, 540 × 960, ohne Ton |

## Technische Entscheidungen

- Video wird nicht automatisch abgespielt.
- `controls`, `muted`, `playsinline` und `preload="metadata"` sind gesetzt.
- Die MP4-Datei ist etwa 1,4 MiB groß und liegt deutlich unter dem Cloudflare-Pages-Limit von 25 MiB je Asset.
- Kein Cloudflare Stream oder R2 für ein einzelnes kurzes Video. Ein Wechsel ist erst bei einer wachsenden Videobibliothek sinnvoll.
- Keine neue Dependency und keine Cloudflare-Konfigurationsänderung.

## Claim-Grenzen

Ohne gesonderten Nachweis nicht veröffentlichen:

- konkrete Millimeter- oder Toleranzwerte
- pauschale DIN-18202-Konformität
- „Digital Twin“
- Eigentum am Scanner
- KAGETEC-Partnerschaft oder offizieller Partnerstatus
- vollständige Fehlervermeidung

## Vor Production-Merge prüfen

- Medienfreigabe des Auftraggebers beziehungsweise Rechteinhabers
- Verwendung des sichtbaren KAGETEC-Schriftzugs am Gerät
- keine vertraulichen Anlagen-, Standort- oder Produktionsdetails
- keine identifizierbaren Personen in den veröffentlichten Sequenzen
- Darstellung auf Desktop und Mobilgerät
