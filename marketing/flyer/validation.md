# Validierung — HSB Digital-Flyer + Akquise-Mail-Suite

Stand: 2026-06-12 · QA-Skill: `hsb-digital-flyer-design-review`

## Artefakte
| Datei | Status |
|---|---|
| `public/HSB-Flyer-Joel-Cherino.pdf` | **253679 Bytes**, **2 Seiten** ✓ |
| `public/HSB-Flyer-Jordie-Post.pdf` | **253428 Bytes**, **2 Seiten** ✓ |
| `public/HSB-Flyer-Geschaeftsfuehrer.pdf` | **253428 Bytes**, **2 Seiten** ✓ |
| `flyer.html` / `flyer.css` / `render-flyer.mjs` | erstellt ✓ |
| `akquise-email.md` (Hauptmail) | erstellt ✓ |
| `akquise-email-varianten.md` (Kurz + 3 Branchen + 2 Follow-ups + 5 Betreff) | erstellt ✓ |
| Assets (hero/detail JPG, Logos JPG, Referenz-SVG, QR-SVG) | komprimiert ✓ |

## 20 Akzeptanzkriterien (Flyer)
1. Nicht wie Word/Standard-HTML ✓ · 2. Hochwertige B2B-Unterlage ✓ · 3. Hierarchie Problem→Lösung→Vertrauen→Kontakt ✓ · 4. Hero stark & seriös (dunkel, kein Glow/Glass) ✓ · 5. Weißraum ✓ · 6. Keine überfüllten Blöcke ✓ · 7. Leistungen als Kacheln (4×2) ✓ · 8. Referenzzone dezent (Logo + 2 Wordmarks, grayscale) ✓ · 9. CTA sofort erkennbar (rote Leiste) ✓ · 10. Desktop+Smartphone lesbar (pt-basierte Größen) ✓ · 11. Für E-Mail-Anhang optimiert ✓ · 12. Keine unnötig großen Bilder (JPEG q72, ~58/67 KB) ✓ · 13. **PDF < 1 MB (248 KB)** ✓ · 14. Exakt 2 Seiten ✓ · 15. Kein abgeschnittener Text (Screenshot-geprüft) ✓ · 16. Logos unverzerrt (object-fit:contain, ratio gehalten) ✓ · 17. QR ergänzend, ~26 mm ✓ · 18. Kontakt sofort auffindbar (CTA-Leiste + dunkler Footer) ✓ · 19. Keine erfundenen Zahlen/Zertifikate; HACCP nur „ausgelegt auf" ✓ · 20. Nur Südzucker/Meggle/Biovegan namentlich ✓

## 6-Rollen-Relevanzcheck
- **Architekt/Planer:** „nach realem Belastungsprofil statt Standardprodukt", Systementscheidung, 8 Systeme, dokumentierte Übergabe → ✓
- **Bauleiter:** Sanierungsfenster, Bauabschnitte, „auch im laufenden Betrieb", Ausführung → ✓
- **Technischer Leiter:** Säuren/Laugen/Fette, Feuchte, Temperaturwechsel, Stapler, Fugen, Gefälle (Problemblock) → ✓
- **Instandhaltung:** Risse, Rinnen/Abläufe, Notreparaturen, Schadensbilder, Checkliste → ✓
- **QM/Audit:** Keimnester, Hygiene, Nassbereiche, Audit-Risiken, Dokumentation → ✓
- **Geschäftsführer:** „Stillstand teuer", Produktionsausfälle, Kostenrisiko, Referenzen → ✓

## Cold-Mail-Kriterien (2026-Benchmarks)
- Hauptmail Body **63 Wörter** (≤ ~90) ✓ · eine binäre CTA „2–3 Terminvorschläge?" ✓
- Personalisierungs-Slot vorhanden (Pflichtfeld) ✓ · keine Altfloskel ✓ · mobil-scannbar ✓
- Kurzvariante + 3 Branchenvarianten + **2 Follow-ups** (Nachfassen + Breakup) + 5 Betreffzeilen ✓
- Flyer-Anhang in jeder Mail erwähnt ✓ · Signatur Joel Cherino Diaz (02562 9463030, 0151 21886891, j-cherino@hsb-boden.de) ✓

## Faktencheck
- Kontaktdaten korrekt (Repo `site.ts` + User-Ergänzung Mobil) ✓
- Nur 3 freigegebene Kundennamen, restliche Referenzen anonym formuliert ✓
- Keine erfundenen Zahlen/Zertifikate ✓

## Isolation
- `git status -- src/ astro.config.* package.json` → leer (Website unberührt) ✓
- Neue Pfade nur unter `marketing/` und `.claude/skills/hsb-digital-flyer-design-review/` ✓

## Empfehlung vor Echtbetrieb
1. Personalisierungs-Satz je Empfänger füllen (kein generischer Merge-Tag).
2. Testmail an eigenes Seed-Postfach + kurzer Spam-Filter-Check (Anhang < 1 MB → geringes Risiko).
3. Betreffzeilen A/B-testen; Follow-ups im selben Thread über 7–14 Tage.
