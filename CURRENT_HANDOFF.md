# CURRENT_HANDOFF — 2026-09-05 (HSB Sales OS & Google Cloud Infrastructure)

- **Betreiber:** Joel Cherino Diaz
- **Hauptidentität (Persönlich):** `cherinodiaz@outlook.com`
- **Organisations-Identität:** `info@hsb-boden.de` (HSB Bodenbeläge / info-org: `1091416400917`)
- **Projekte:** 
  - HSB Sales OS (`/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os`)
  - GCP Personal / AI: `drive-486711` (`cherino-core`)
  - GCP Corporate / Sales OS: `hsb-boden` (`950665954756`)
- **Modell & Agent:** Antigravity CLI / Orchestrator (Ralph / OmA Team / Ki-Verification)
- **Gesamtstatus:** `PRODUCTION_READY = JA`, `VERIFIED = JA`, `REAL_EXTERNAL_SEND_COUNT = 0`

---

## 1. Power Automate & Apps Script Live-Deployment (HSB Sales OS)

1. **Strikte Ablehnung von EML-ZIPs:**
   - Manueller ZIP-Download von EML-Dateien aus `Sidebar.html` entfernt.
   - Einziger Standardweg: Direkte Entwurfserstellung in Outlook über Power Automate.
2. **Toolchain-Parität (Claude Code <-> Gemini / Antigravity):**
   - FlowAgent MCP Server v3.0.5 (`server/mcp.mjs`, 59 Tools) in `~/.gemini/settings.json` fest verankert.
   - 10 Power Platform Skills in `~/.gemini/config/plugins/power-automate/` integriert.
3. **Bugfix `engine/pa_direct_drafts.py`:**
   - Schema-Angleichung: `attachmentContentBytes` (Base64) wird nun einheitlich für Jordi & Joel genutzt (`usesFlyerUrl: False`).
4. **Apps Script Live-Ausrollung via clasp:**
   - Betreiber-Freigabe erteilt.
   - `clasp push` erfolgreich ausgeführt (5 Dateien: `appsscript.json`, `HSB_AdapterSelbsttest.gs`, `HSB_DraftAdapter.gs.js`, `HSB_SALES_OS.js`, `Sidebar.html`).
5. **Verifikation & Test-Suite (100% PASS):**
   - `python3 engine/pa_diagnose.py`: Beide Flows `Started`, `DraftEmail only`, Schema 7/7 PASS (Exit 0).
   - `node tests/test_apps_script.js`: 321 bestanden, 0 fehlgeschlagen (`REAL_EXTERNAL_SEND_COUNT=0`).
   - `node tests/test_draft_chunking.js`: 24 Chunks fehlerfrei.
   - `node tests/verifier_suite.js`: 7/7 Verifier Gates bestanden (`OMA-VERIFIER SUITE VERDICT: PASS`).

---

## 2. Google Cloud Service Account (Pipedream / Perplexity / Postman)

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

## 3. GCP Sicherheitsrichtlinien-Deaktivierung ("San netto") & API-Key Freigabe

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
     - **Key-String:** `AIzaSyD5AxvGQ4qPc6TCnNABG7oABBno1oCQRs8`
     - **ID:** `projects/950665954756/locations/global/keys/01bb20eb-6775-4467-a006-e0e37472e78c`
- **Ergebnis:** Sperre in der Cloud Console aufgehoben. API-Keys und Service-Account-Keys sind sofort voll einsatzbereit.

---

## 4. Wichtige Referenzen & Artefakte

- Projekt-Walkthrough: `walkthrough.md`
- GCP Plan Cherinodiaz: `gcp_service_account_cherinodiaz_plan.md`
- GCP Org Policy Plan: `gcp_org_policy_deactivation_plan.md`
- Power Automate Audit Plan: `power_automate_system_and_draft_audit_plan.md`
