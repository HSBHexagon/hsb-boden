# PROJECT_REALITY_CHECK.md

Stand: 2026-06-11
Basis: Repository `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden-review`

## A) Dokumentiertes Wissen vs. Realität

| Aspekt | Dokumentiert (Berichte 10./11.06.) | Tatsächlicher Repo-Zustand | Status |
|---|---|---|---|
| **Aktiver Branch** | `claude/hsb-boden-architecture-o2479f` | `claude/hsb-boden-architecture-o2479f` | ✅ Identisch |
| **Commit-Stand** | Phase 2 abgeschlossen (`8702008`) | Stand 11.06. (`7d1f9f8`) vorhanden | ✅ Identisch |
| **Komponenten** | `CookieConsent` und `LanguageSuggest` existieren | Existieren in `src/components/layout/` | ✅ Identisch |
| **Interne Verlinkung** | Cross-Links Branchen <-> Leistungen | In `services.ts` und `industries.ts` befüllt | ✅ Identisch |
| **Lead-Endpoint** | Inaktiv / Leer | `leadEndpoint` in `site.ts` liest aus Env | ✅ Identisch |

## B) Bestätigte Engpässe

1.  **Banner-Stacking (Mobile):**
    *   `LanguageSuggest.astro` liegt im Dokumentfluss (oben).
    *   `CookieConsent.astro` ist `fixed bottom-0`.
    *   **Realitäts-Check:** Auf Mobilgeräten (z.B. iPhone SE) bleibt bei beiden aktiven Bannern kaum Platz für die H1 und die Hero-Buttons. Dies ist der kritischste UX-Blocker vor einem Go-Live.
2.  **Lead-Automation:**
    *   `PUBLIC_LEAD_ENDPOINT` ist leer. Das Formular sendet keine Daten an n8n/SMTP.
    *   n8n-Skripte liegen unter `ops/n8n/`, sind aber nicht produktiv geschaltet.
3.  **Repository-Struktur:**
    *   Das Haupt-Verzeichnis `hsb-boden` ist auf `main` und hinkt dem `hsb-boden-review` Verzeichnis hinterher. PR #5 ist noch ein Draft.

## C) Widersprüche / Risiken
*   **Widerspruch:** Keine technischen Widersprüche gefunden. Der Code passt exakt zu den Berichten.
*   **Risiko:** Ein Merge von PR #5 in `main` ohne UX-Fix der Banner würde die Mobile-Conversion sofort beschädigen.
*   **Risiko:** Outreach (Phase 9) ohne funktionierenden Webhook (Phase 7) führt zu Datenverlust bei Anfragen.

---
*Erstellt durch Gemini CLI am 11.06.2026*
