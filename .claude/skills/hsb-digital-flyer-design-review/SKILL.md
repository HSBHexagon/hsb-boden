---
name: hsb-digital-flyer-design-review
description: Use when reviewing or improving the HSB-Boden digital B2B acquisition flyer (PDF email attachment) and its cold-email suite. Enforces 20 quality criteria, a 6-role relevance check, and 2026 cold-email/one-pager best practices before the asset is considered ready.
---

# HSB Digital Flyer & Cold-Email Review

Projektlokaler QA-Gate für das HSB-Akquise-Asset (Flyer-PDF + Mail-Suite). Kein Druckprodukt — Ziel ist ein hochwertiger, zustellbarer **digitaler PDF-Anhang** plus rückmeldeoptimierte Mails. Bei jedem Review jeden Punkt als TodoWrite-Item anlegen und abhaken.

## Wann anwenden
- Nach Erstellung/Änderung von `marketing/flyer/flyer.html|css`, dem gerenderten PDF oder der Mail-Suite.
- Vor jeder „fertig"-Aussage.

## 20 Akzeptanzkriterien (Flyer-PDF)
1. Sieht NICHT aus wie Word/Standard-HTML/generische Vorlage.
2. Wirkt wie hochwertige technische B2B-Vertriebsunterlage.
3. Klare visuelle Hierarchie: Problem → Lösung → Vertrauen → Kontakt.
4. Hero stark, aber seriös (kein Glow/Glassmorphism/zentrierter Default-Hero).
5. Genug Weißraum.
6. Keine überfüllten Textblöcke.
7. Leistungen als hochwertige Kacheln.
8. Referenzlogo-Zone sichtbar, aber nicht marktschreierisch.
9. CTA sofort erkennbar.
10. Auf Desktop UND Smartphone im PDF gut lesbar (Schriftgröße bei 100 % prüfen).
11. Für E-Mail-Anhang optimiert.
12. Keine unnötig großen Bilder (komprimiertes WebP, SVG-Logos).
13. **PDF < 1 MB** (`ls -la` belegen).
14. Exakt 2 Seiten.
15. Kein abgeschnittener Text (Screenshot beider Seiten prüfen).
16. Keine verzerrten Logos (Seitenverhältnis erhalten).
17. QR-Code nur ergänzend, nicht überdimensioniert.
18. Kontakt sofort auffindbar.
19. Keine erfundenen Zahlen, Zertifikate oder Claims; HACCP nur „auf HACCP-Anforderungen ausgelegt".
20. Keine Kundennamen außer **Südzucker, Meggle, Biovegan**.

## 6-Rollen-Relevanzcheck
Jede Rolle muss beim Überfliegen ihren Anker finden — sonst Headline/Zwischentitel/Kacheln/Gewichtung überarbeiten:
- **Architekt/Planer:** Systemkompetenz, Schnittstellen, Planungssicherheit.
- **Bauleiter:** Ausführung, Sanierungsfenster, Koordination, laufender Betrieb.
- **Technischer Leiter:** Belastungsprofil (Chemie, Feuchte, Reinigung, Temperaturwechsel, Stapler, Fugen, Gefälle).
- **Instandhaltung:** Schäden, Rinnen, Fugen, Notreparaturen.
- **QM/Audit:** Hygiene, Nassbereiche, Dokumentation, Audit-Sicherheit.
- **Geschäftsführer:** Stillstand, Kostenrisiko, Verlässlichkeit, Referenzen.

## Cold-Email-Kriterien (2026-Benchmarks)
- Hauptmail ≤ ~90 Wörter; Kurzvariante ≤ ~55; Follow-ups ≤ ~45/40.
- Genau **eine** CTA, **binäre** Abschlussfrage („2–3 Terminvorschläge?").
- **Personalisierungs-Slot** (1 Satz konkreter Anlass) vorhanden, kein generischer Merge-Tag.
- Mobil-scannbar (kurze Absätze), keine Altfloskel („In der Hoffnung…").
- **2 Follow-ups** (Nachfassen Tag ~3–4, Breakup Tag ~10–14).
- Flyer-Anhang erwähnt; Signatur Joel Cherino Diaz (Tel. 02562 9463030, Mobil 0151 21886891, j-cherino@hsb-boden.de).
- Vor echtem Versand: Seed-/Test-Postfach + Spam-Check empfehlen.

## Gate
Asset gilt erst als „ready", wenn alle 20 Kriterien, der 6-Rollen-Check und die Cold-Email-Kriterien erfüllt sind und die Größe (< 1 MB) + Seitenzahl (2) belegt wurden. Befund in `marketing/flyer/validation.md` protokollieren.
