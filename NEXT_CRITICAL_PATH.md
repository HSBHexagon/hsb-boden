# NEXT_CRITICAL_PATH.md

Stand: 2026-06-11
Projekt: HSB-Boden / HEXAFLOOR
Status: Fokus auf Finalisierung & Go-Live Readiness

## 1. Verbleibende Aufgaben bis zum Geschäftsziel

| Aufgabe | Typ | Status | Ziel |
|---|---|---|---|
| **Lead-Infrastruktur** | Technik | Offen | Webhook-Empfang & E-Mail-Notifikation sicherstellen. |
| **n8n Hosting** | Infrastruktur | Offen | Dauerhafter Betrieb des Lead-Workflows. |
| **Finale Textabnahme** | Rechtlich | Offen | Rechtssicherheit für Impressum/DSGVO gewährleisten. |
| **Repository Sync** | Ops | Offen | Produktiven Stand im Haupt-Repo (`hsb-boden`) sichern. |
| **Outreach Start** | Sales | Offen | Ansprache der 30 qualifizierten Leads. |

## 2. Kritische Blocker für den Versand (Kundenkontakt)

Diese Punkte **müssen** vor dem ersten Kundenkontakt (Flyer/Lead-Liste) gelöst sein:

1.  **Technischer Blocker: Webhook-Aktivierung**
    *   Das Kontaktformular ist derzeit "blind". Ohne die Variable `PUBLIC_LEAD_ENDPOINT` in der `.env` landen Anfragen im Nichts.
    *   *Aktion:* Webhook-URL generieren (n8n) und eintragen.
2.  **Rechtlicher Blocker: Text-Freigabe**
    *   Für Kaltakquise und Website-Betrieb ist die finale Bestätigung der Rechtstexte durch den Inhaber zwingend.
    *   *Aktion:* Kurzes Review von `src/pages/impressum.astro` und `src/pages/datenschutz.astro`.

## 3. Heute noch abschließbar (Fast-Track)

*   [ ] **Infrastruktur:** Entscheidung über n8n-Hosting (Cloud/Lokal).
*   [ ] **Konfiguration:** Webhook-URL in `.env` eintragen und Test-Lead absenden.
*   [ ] **Validation:** Manueller End-to-End Test (Formular -> n8n -> E-Mail).
*   [ ] **Git-Ops:** Merge von PR #5 in `main` und Synchronisation von `hsb-boden`.

---
**Fokus für den Rest des Tages:** 
Vollständige Aktivierung der **Lead-Pipeline**. Sobald der erste Test-Lead erfolgreich in n8n ankommt, ist die Website "Business-Ready".
