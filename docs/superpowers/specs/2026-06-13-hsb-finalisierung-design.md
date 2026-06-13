# HSB-Boden – Finalisierung & Konsolidierung (2026-06-13)

## Kontext / Problem
Eine nächtliche Ordner-Umstrukturierung hatte das Repo zerstückelt (mehrere
`KI-System-Backup-*`, `AI-OS`, kaputtes `.git`, leeres `src/`). Parallel existierten
zwei Cloudflare-Worker (`hsb-boden`, `hsb-boden-preview`) → „zwei Wahrheiten".

## Entscheidungen
- **Einzige lokale Wahrheit:** `…/KI-System/01_Wahrheitsquelle/Memory/AI-Memory-Hub/projects/hsb-boden`,
  wiederhergestellt aus `origin/main` (GitHub = vollständige Quelle, nichts verloren).
- **Einzige Live-Wahrheit:** Cloudflare-Worker `hsb-boden-preview` (Default-Env in `wrangler.toml`).
  `hsb-boden` wurde gelöscht. `--env production` (=Name `hsb-boden`) wird NICHT verwendet.
- Mehrsprachseiten (en/fr/nl/pl/tr) sind schlanke `InternationalLanding`-Seiten ohne
  „bundesweit"-Claims → keine Replikation der DE-Texte nötig.

## Umgesetzte Änderungen (Screenshot-Fixes + Master-Prompt)
1. **Peterstaler-Logo** sichtbar: `fill="#fff"` → `#1a1a1a` (war weiß auf weiß).
2. **Referenzbild** „Doppelrinne": `halle-doppelrinne-keramik.webp` → `keramik-halle-rinnen.webp` (hell).
3. **Hero-Box rechts**: Padding `lg:p-10`→`lg:p-12`, H2 `max-w-md` (Text nicht mehr an Kante).
4. **ProofMedia Panel 4**: „Chemische und mechanische Beständigkeit unter Produktionslast" + neuer Text.
5. **Freigabe-Hinweis** („Nicht freigegebene Projekte…") aus ReferenceMap entfernt.
6. **bundesweit → „Deutschland und europaweit"** (Hero, ReferenceMap-H3, Reichweite-Label).
7. **Südzucker AG**: WHG-Abdichtung ergänzt (System `whg-abdichtung-industrieboden` + Lösungstext).
8. **Referenz Kyritzer Fruchtsäfte** (Kyritz, Brandenburg) als Kartenmarker + echtes Logo
   `/logos/kyritzer-fruchtsaefte.png` (erscheint auch in der Logo-Cloud). Ersetzt frühere Wietz-Notiz.
9. **Projektablauf-Phasentexte** branchenspezifischer (Sechskant-Keramik, Gefälle/Rinnen, Verfugung,
   Hygiene/WHG-Nachweise) – kein separater Block.
10. **Leadform-Auswahl**: Schrift 14→18px, „Neubau, Sanierung oder Reparatur?".
11. **Reparaturen** sichtbar (Homepage-Block + Leadform).
12. **Footer**: Gruppe „Unternehmen & Team" + „Über uns"-Link (#ueber-uns) + Team-Text.
13.+14. **Über-uns/Team-Sektion** auf Startseite (Anker `#ueber-uns`, 4 Fakten-Kacheln,
    verbindliche Team-Fakten: eigenes Personal, kein Subunternehmer, ~30 J. Erfahrung,
    40+ J. Sechskantfliesen, SOKA-BAU, VCA/SCC, mehrsprachig).
2(Std). „Planung und Ausführung aus einer Hand"-Satz präziser + Abstände verbessert.

## Verifikation (ADR-003-Gate)
`astro check` 0/0/0 · `astro build` ✓ · `vitest` 31/31 · DOM- + Live-Verifikation auf
`hsb-boden-preview` (Version 19c4c171). Keine Konsolen-Fehler.

## Offen (kein Blocker)
- Task 1 (vollständige fachlich/sprachliche Tiefenprüfung) und globales Spacing-Feintuning
  als optionaler weiterer Review-Pass.
