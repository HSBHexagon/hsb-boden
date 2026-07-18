# 3D-Scan-Medienintegration

## Zweck

Die Startseite erhält einen eigenständigen Trust-/Prozessabschnitt zur digitalen Bestandsaufnahme vor der Industriebodenausführung. Die Darstellung bleibt bewusst neutral und vermeidet unbelegte Aussagen zu Eigentum, Partnerstatus, Messgenauigkeit oder Normkonformität.

## In diesem Branch veröffentlicht

| Repo-Pfad | Quelle | Verwendung |
|---|---|---|
| `public/media/hsb/projekte/3d-scan/3d-scan-halle-uebersicht.webp` | Foto `297597.jpg` | Kompakte Hallenübersicht mit Messaufbau und Referenzpunkten |

Der neue Startseitenabschnitt kombiniert dieses Scanmotiv mit einem bereits vorhandenen Baustellenbild. Dadurch bleibt die Änderung klein, performant und ohne fehlende Medienreferenzen.

## Lokal vorbereitet, noch nicht veröffentlicht

- optimiertes Detailbild aus `297598.jpg`
- Posterbild aus `297599.mp4`
- weboptimierte H.264-Fassung des rund 17 Sekunden langen Hochkantvideos

Diese Dateien bleiben zunächst außerhalb des Repositories, bis Medienfreigabe, sichtbarer KAGETEC-Schriftzug, erkennbare Personen und mögliche Projektdetails geprüft wurden.

## Technische Entscheidungen

- Kein Autoplay und keine zusätzliche JavaScript-Logik.
- Kein Cloudflare Stream oder R2 für ein einzelnes kurzes Video. Ein Wechsel ist erst bei einer wachsenden Videobibliothek sinnvoll.
- Das veröffentlichte WebP liegt deutlich unter dem Cloudflare-Pages-Limit von 25 MiB je Asset.
- Keine neue Dependency und keine Cloudflare-Konfigurationsänderung.
- Production bleibt unverändert; die Änderung läuft ausschließlich über Branch, Pull Request und Pages-Preview.

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
- Verwendung des sichtbaren KAGETEC-Schriftzugs
- keine vertraulichen Anlagen-, Standort- oder Produktionsdetails
- keine identifizierbaren Personen in veröffentlichten Sequenzen
- Darstellung auf Desktop und Mobilgerät
- Entscheidung, ob Detailbild und Video später im selben Abschnitt ergänzt werden
