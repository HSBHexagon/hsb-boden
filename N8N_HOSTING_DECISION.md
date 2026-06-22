# N8N_HOSTING_DECISION — HSB-Boden

> P0A-Entscheidungsvorlage. Stand: 2026-06-14. Keine Live-Aktivierung, kein Webhook-Livebetrieb ohne Freigabe.

## 1. Optionen

| Option | Beschreibung |
|--------|--------------|
| A: n8n Cloud | gehostet, gemanagt |
| B: self-hosted VPS | eigener Server (z. B. Hetzner/DO) |
| C: Docker / Cloudflare-nahes Setup (später) | containerisiert, näher an bestehender Plattform |

## 2. Entscheidungskriterien

| Kriterium | A: Cloud | B: VPS | C: Docker (später) |
|-----------|----------|--------|--------------------|
| Aufwand Setup | niedrig | mittel | hoch |
| Kosten | Abo | VPS-Miete | variabel |
| Wartung | gering (gemanagt) | hoch (selbst) | hoch |
| Sicherheit | Anbieter + Account | selbst verantwortlich | selbst verantwortlich |
| Credentials | n8n-Credential-Store | n8n + Server-Härtung | n8n + Container-Secrets |
| Backups | Anbieter | selbst einrichten | selbst einrichten |
| Verfügbarkeit | hoch (SLA) | abhängig | abhängig |

## 3. Startempfehlung
**Option A (n8n Cloud)** für schnellen, wartungsarmen Start. Migration zu B/C später optional, nur bei belegtem Bedarf. (Empfehlung, keine Festlegung — Entscheidung beim Nutzer.)

## 4. Benötigte Secrets (extern, nicht im Repo)

| Secret | Zweck |
|--------|-------|
| n8n Webhook-URL | Zieladresse für Endpoint-Weiterleitung |
| Google Service-Account / OAuth | Sheets-Zugriff (siehe `GOOGLE_API_SETUP.md`) |
| SMTP-Credentials | Benachrichtigungen/Reports |

## 5. Credential-Speicher
- Ausschließlich n8n-Credential-Store bzw. `~/KI-System/05_Secrets/`.
- Nie im Repo, nie in `.env` committen, nie im Frontend.

## 6. Betriebsgrenzen (P0A)
- Kein produktiver Webhook.
- Kein automatisierter Versand.
- Kein Import echter personenbezogener Leads vor Freigabe.

## 7. Live-Gate
Kein Live-Webhook und keine produktive n8n-Anbindung ohne ausdrückliche Freigabe.

## 8. Nächster Entscheidungspunkt
Nutzer wählt Hosting-Option (A/B/C) + bestätigt Credential-Ablageort → Voraussetzung für P0B.

## 9. Entscheidung (2026-06-22, Claude Code stellvertretend nach Nutzer-Freigabe)
**Option A: n8n Cloud.** Begründung: niedrigster Aufwand, kein Server-Härtungsaufwand, Anbieter-SLA passt zu einem niedrigvolumigen B2B-Lead-Formular. Migration zu B/C bleibt offen, ist aber nicht durch belegten Bedarf gerechtfertigt. Credential-Ablageort: `~/KI-System/05_Secrets/` bzw. n8n-Credential-Store — keine Secrets im Repo. Live-Webhook bleibt trotzdem gesperrt, bis `N8N_WEBHOOK_URL` real vorliegt (siehe `P0B_SECRET_REQUIREMENTS.md`).

## 9b. Revision der Entscheidung (2026-06-22, gleicher Tag, explizite Nutzervorgabe)
**Option A wird verworfen.** Nutzervorgabe: "die nehmen, die gratis ist und bleibt" — n8n Cloud ist laut §2 dieser Tabelle ein Abo (laufende Kosten), das widerspricht der Vorgabe direkt, unabhängig vom geringen Setup-Aufwand. Optionen B/C (VPS/Docker) sind ebenfalls nicht dauerhaft kostenlos (Server-/Hosting-Miete).

**Neue Lösung: kein n8n.** Stattdessen ein **Google Apps Script Web App**, fest an das CRM-Light-Sheet gebunden (`doPost(e)` hängt die Lead-Zeile direkt an, optional `MailApp.sendEmail()` für die Sofort-Benachrichtigung) — innerhalb der Google-Workspace-Gratis-Kontingente, keine Abo-Kosten, kein Server, kein Service-Account-/OAuth-Setup nötig (läuft unter dem Sheet-Eigentümer-Konto). Details: `GOOGLE_SHEETS_CRM_SETUP.md`.

Der bereits implementierte `/api/lead`-Endpoint (Zod-Validierung, Rate-Limit, Honeypot, Origin-Check) bleibt unverändert bestehen — er ist webhook-agnostisch und leitet lediglich an die in `LEAD_WEBHOOK_URL` konfigurierte Ziel-URL weiter. Es ändert sich nur das Ziel: Apps-Script-Web-App-URL statt n8n-Webhook-URL. Live-Gate (§7) bleibt unverändert: kein Versand ohne Freigabe und ohne real konfigurierte `LEAD_WEBHOOK_URL`.
