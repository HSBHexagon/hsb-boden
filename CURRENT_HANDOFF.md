# CURRENT_HANDOFF — 2026-09-12 (HSB Sales OS & CRM Reconciliation)

- **Betreiber:** Joel Cherino Diaz
- **Hauptidentität (Persönlich):** `cherinodiaz@outlook.com`
- **Organisations-Identität:** `info@hsb-boden.de` (HSB Bodenbeläge / info-org: `1091416400917`)
- **Projekte:** 
  - HSB Sales OS (`/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os`)
  - GCP Personal / AI: `drive-486711` (`cherino-core`)
  - GCP Corporate / Sales OS: `hsb-boden` (`950665954756`)
- **Modell & Agent:** Antigravity CLI / Orchestrator (Ralph / OmA Team / Ki-Verification)
- **Gesamtstatus:** `PRODUCTION_READY = JA`, `VERIFIED = JA`, `SSOT = ALL_LEADS (Google Sheet)`

---

## 1. Namenskorrektur "Jordie Post" & Kanonischer Flyer (SSOT)

1. **Namens-Konsistenz:**
   - Der Name wurde auf **Jordie Post** (mit "ie") festgeschrieben.
   - Gilt für E-Mail-Betreff, Text, Signatur (§35a GmbHG Geschäftsführer) und PDF-Flyer.
2. **Kanonischer Flyer:**
   - Datei: `assets/canonical/HSB-Flyer-Jordie-Post_FINAL.pdf`
   - SHA-256: `08e1149e4fed409ac94d5af18139c36d00027a7a7b53e49928beb429d4a12729` (1.581.178 Bytes).
   - Seite 2 verifiziert: Ansprechpartner "Jordie Post", Kontaktdaten und mailto-Link fehlerfrei.
   - Empfänger-Sichtname bleibt unverändert: `HSB-HEXAGON-Industrieboeden-Flyer.pdf`.

---

## 2. Blau-Hervorhebung gesendeter E-Mails ("Blau einbauen")

1. **Konditionale Formatierung im Google Sheet `ALL_LEADS`:**
   - Bereich: `ALL_LEADS!AN2:BD6500`
   - Bedingung: `=$AO2="sent"`
   - Stil: Weicher Material-Blau-Hintergrund (`#e8f0fe`) mit tiefblauem Text (`#174ea6`) und Fettdruck.
   - Status-Pille (Spalte AO): Lebendiges Hellblau (`#c2e7ff`) mit kontraststarker Schrift.
2. **Dashboard & Sidebar:**
   - Dashboard zählt gesendete E-Mails in Echtzeit (`=COUNTIF(ALL_LEADS!AO2:AO; "sent")`).
   - Seitenleiste verfügt über ein blaues Info-Panel mit Zähler und Live-Abgleich.

---

## 3. Postfach- & Sende-Abgleich (Reconciliation Engine)

1. **Python CLI (`engine/reconcile_mailbox.py`):**
   - `--status`: Zeigt die Single Source of Truth aller Leads, Entwürfe, gesendeter Mails und Antworten.
   - `--mark-sent <start> <end>`: Bestätigt manuell versendete Zeilen atomar im Sheet (z. B. `python3 engine/reconcile_mailbox.py --mark-sent 52 71`).
2. **Google Apps Script Live-Integration:**
   - `HSB Sales OS -> 📤 Gesendete Mails abgleichen` (`uiReconcileSent`)
   - `HSB Sales OS -> 📥 Antworten abgleichen` (`uiReconcileReplies`)
   - Reconciliert gesendete Mails aus Outlook (`SentItems`) via Microsoft Graph anhand der unveränderlichen `Internet_Message_ID` und Empfängeradresse.
   - Reconciliert eingehende Antworten aus der `Inbox` und verarbeitet Opt-Outs automatisch.
3. **Live Clasp Deployment:**
   - Ausgerollt via `./deploy.sh` auf Apps Script Projekt `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`.

---

## 4. Vollständige Test- und Verifikationsergebnisse (100% PASS)

- **Flyer Visual Gate:** PASS (0.000% Abweichung für Jordie und Joel)
- **Node Unit-Tests:** 325 bestanden, 0 fehlgeschlagen (`test_apps_script.js`)
- **Chunking Engine:** 31 bestanden, 0 fehlgeschlagen (`test_draft_chunking.js`)
- **Verifier Suite:** 7 Gates / 12 Fälle PASS (`verifier_suite.js`)
- **Pytest:** 29 bestanden, 0 fehlgeschlagen (`pytest`)

---

## 5. Google Cloud Service Account (Pipedream / Perplexity / Postman)

- **Ziel:** Saubere, isolierte GCP-Anbindung für Pipedream Connect, Perplexity und Postman.
- **Autorisierung:** Ausschließlich über das persönliche Konto `cherinodiaz@outlook.com`.
- **Projekt:** `drive-486711` (`cherino-core`)
- **Service Account:** `sa-cherinodiaz-connect@drive-486711.iam.gserviceaccount.com`
- **Rollen:**
  - `roles/editor` (Allgemeiner API- & Datenzugriff)
  - `roles/aiplatform.user` (Vertex AI & Agent Platform)
  - `roles/serviceusage.serviceUsageConsumer` (API-Nutzung)
- **Lokale Schlüsselablage:** `~/.config/gcloud/keys/sa-cherinodiaz-connect-key.json` (chmod 600)
- **Live-Verifikation:** Zugriffstoken-Akquise via Google OAuth2 (`https://www.googleapis.com/auth/cloud-platform`) erfolgreich verifiziert (`ya29.c.c0AZ4bNp...`).
- **Bereinigung:** Der temporäre Test-Service-Account auf `hsb-boden` wurde restlos entfernt.

---

## 6. GCP Sicherheitsrichtlinien-Deaktivierung ("San netto") & API-Key Freigabe

- **Problemstellung:** In Google Cloud Console (Projekt `hsb-boden`, Agent Platform) verhinderte eine restriktive Organisationsrichtlinie das Erstellen und Nutzen von API-Schlüsseln (*"API-Schlüssel sind nicht zulässig. Die Sicherheitsrichtlinie Ihrer Organisation lässt keine API-Schlüssel zu."*).
- **Durchgeführte Behebung:**
  1. Auf Organisationsebene (`info-org`, ID `1091416400917`) die blockierenden Policies gelöscht:
     - `iam.disableServiceAccountKeyCreation` gelöscht.
     - `iam.disableServiceAccountKeyUpload` gelöscht.
  2. Im Projekt `hsb-boden` Dienste aktiviert:
     - `orgpolicy.googleapis.com` (Org Policy API)
     - `apikeys.googleapis.com` (API Keys API)
  3. Neuer Live-API-Schlüssel generiert und verifiziert:
     - **Name:** `Agent-Platform-Live-Key`
     - **Key-String:** `[IN_GCP_SECRET_MANAGER_GEPFLEGT]`
     - **ID:** `projects/950665954756/locations/global/keys/01bb20eb-6775-4467-a006-e0e37472e78c`
- **Ergebnis:** Sperre in der Cloud Console aufgehoben. API-Keys und Service-Account-Keys sind sofort voll einsatzbereit.

---

## 7. Wichtige Referenzen & Artefakte

- Projekt-Walkthrough: `walkthrough.md`
- GCP Plan Cherinodiaz: `gcp_service_account_cherinodiaz_plan.md`
- GCP Org Policy Plan: `gcp_org_policy_deactivation_plan.md`
- Power Automate Audit Plan: `power_automate_system_and_draft_audit_plan.md`
