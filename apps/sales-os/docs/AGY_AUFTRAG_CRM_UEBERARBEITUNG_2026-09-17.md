# AGY-Auftrag: HSB CRM (Google Sheet „HSB CRM MASTER 6424 – Sales OS") funktional und ergonomisch auf Best-Practice-Niveau bringen — PLAN, KEINE AUSFÜHRUNG

Erstellt: 2026-09-17 · Autor: Claude Code (Opus 5) im Auftrag des Owners · Empfänger: Antigravity CLI (`agy`) · Fassung 2 (nach Owner-Entscheidung zur Wahrheitsquelle)

## Startbefehl (vom Owner auszuführen)

```bash
cd ~/KI-System/02_Projects/active/hsb-boden && \
agy --agent oma-director --mode plan --effort high \
  --add-dir ~/KI-System/ObsidianVault/brain \
  --add-dir ~/KI-System/08_System/reports \
  -i "Lies zuerst apps/sales-os/docs/AGY_AUFTRAG_CRM_UEBERARBEITUNG_2026-09-17.md vollständig und arbeite exakt danach. Modus ist PLAN: keine Schreibzugriffe auf Google Sheet, Apps Script, Power Automate, Drive oder Repo-Dateien außer der einen Plandatei, die der Auftrag benennt. Das Team aus oma-researcher, oma-architect, oma-planner, oma-consensus, oma-reviewer und oma-verifier ist einzusetzen; die Zuarbeiten sind im Plan als eigene Abschnitte kenntlich zu machen."
```

- `--mode plan` ist Pflicht: Der Owner lässt den Plan durch Claude Code prüfen und gibt erst dann frei.
- `--effort high` = maximales Reasoning. `--model` bewusst nicht gesetzt: Nimm das stärkste Reasoning-Modell deiner agy-Konfiguration und nenne es im Plan.
- **Kein** `--dangerously-skip-permissions`. Keine Fremdmodelle außerhalb agy.

## Entschiedene Wahrheit (nicht mehr diskutieren)

- **System of Record für HSB-CRM und Outreach ist das Google Sheet** `HSB CRM MASTER 6424 – Sales OS` mit seinem Apps Script (Owner-Entscheidung 2026-09-17, festgehalten in `~/KI-System/ObsidianVault/brain/01_core/STORAGE_ROLES.md`; deckungsgleich mit `apps/sales-os/PROJECT_STATE.md`). Airtable ist keine Wahrheitsquelle und kein Ziel dieses Auftrags.
- Keine zweite Lead-Datenbank, kein zweiter Mail-Writer, kein automatischer Send-Pfad. Jede Erweiterung liest und schreibt **dieses eine Sheet**.
- Sicherheitsinvariante `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` und alle Gates im Apps Script (Reservierung exakt N Kontakte, Opt-out/Suppression/Hard-Bounce/Owner/Flyer-Sperren, retry-sicheres Resume) bleiben **beweisbar** erhalten.

## Auftrag in einem Satz

Das Sheet-basierte CRM so umbauen, dass Jordi und Joel damit **täglich ohne Terminal arbeiten wollen** — nicht Kosmetik, sondern Funktion: Pipeline, Follow-ups, Antworten, Batches, Kennzahlen, Datenqualität — unter Nutzung des vollen Google-Workspace-Werkzeugkastens nach Best Practice, mit dem Sheet als einzigem Backend.

## Ausgangslage (per Google-Workspace-Connector am 2026-09-17 gelesen — belegt, nicht neu erfinden)

- Datei: „HSB CRM MASTER 6424 – Sales OS – 2026-08-21", 2,65 MB, zuletzt geändert 2026-09-16 15:00 UTC. **Eigentümer laut Drive-Metadaten: das Privatkonto `cherinodiaz@outlook.com`** — Verstoß gegen die Regel „Privates Konto nie mit HSB-Geschäftsflüssen mischen". Der Plan muss einen Eigentumsübergang auf ein HSB-Workspace-Konto als Owner-Gate enthalten (Risiko: Apps-Script-Bindung, Trigger, Freigaben).
- **34 Tabs** (nicht 5): `README`, `VERSAND`, `ALL_LEADS` (6.425 Zeilen × **56 Spalten**), `JOEL` (7.000 × 56), `JORDI` (7.000 × 56), `JOEL_LEGACY_20260904`, `JORDI_LEGACY_20260904`, `READY_CANDIDATES`, `READY_CANDIDATES_LEGACY_20260904`, `DUPLICATES_REVIEW`, `INVALID_EMAIL_REVIEW`, `OPT_OUT_EXCLUDED`, `ALREADY_CONTACTED`, `OWNER_CONFLICT_REVIEW`, `FLYER_MAPPING`, `CAMPAIGN_MAPPING`, `EMAIL_TEMPLATE_MAPPING`, `BATCH_PLAN`, `DASHBOARD`, `ACTIVITIES`, `CONTROL_CENTER` (statischer Snapshot 23.08.), `BATCHES`, `AKTUELLER_BATCH_JORDI_50`, `LEGACY_JORDI_HEUTE_20`, `INBOUND_EVENTS`, `SYSTEM_EVIDENCE`, `RUNBOOK`, `Diagramm1`, `PROJECT_CHRONOLOGY`, drei `*_BACKUP_20260823`, `GO_LIVE_100_REVIEW`, `AUDIT_20260904`. Mindestens zehn davon sind Legacy/Backup/Snapshot — Kandidaten für Archivierung (nie Löschung ohne Manifest).
- `ALL_LEADS`-Header (56): A–AC deutsche Operator-Felder (`Lead-ID`, `Firma`, `Standort`, `Region`, `Branche`, `Tier`, `Ansprechpartner`, `Rolle`, `E-Mail`, `Telefon`, `Website`, `Quelle`, `Beziehung / Kontaktgrund`, `Kampagne`, `Score`, `Status`, `Nächste Aktion`, `Follow-up-Datum`, `Interesse`, `Projektart`, `Fläche geschätzt`, `Belastungsart`, `Sanierungsfenster`, `Opt-in-Status`, `Opt-out-Status`, `Versandfreigabe`, `Verantwortlicher`, `Flyer-Anhang`, `Notizen`), AD–BD englische Maschinen-/Engine-Felder (`Segment`, `Kampagne_ID`, `Email_Template_ID`, `Flyer_ID`, `Flyer_URL`, `Landing_URL`, `UTM_Source/Medium/Campaign/Content`, `Batch_ID`, `Send_Status`, `Send_Datum`, `Bounce_Status`, `Reply_Status`, `Legal_Basis`, `Suppressed`, `Batch_Status`, `Prepared_At`, `Draft_ID`, `Drafted_At`, `Approved_At`, `Outlook_Message_ID`, `Internet_Message_ID`, `Conversation_ID`, `Last_Reply_At`, `Last_Error`). **Das ist der Kern des Bedienproblems:** zwei Sprachwelten und zwei Nutzergruppen (Mensch/Maschine) in einer Tabelle.
- Zeilenhöhen-Ursache (Stichprobe Zeile 2): mehrzeilige, datierte Anhänge in `Notizen`, lange Freitexte in `Beziehung / Kontaktgrund`, 100+ Zeichen lange `Outlook_Message_ID`/`Internet_Message_ID` — bei aktivem Zeilenumbruch. **Keine** Mailtexte in Zellen (frühere Annahme war falsch).
- `VERSAND` ist bereits eine **dynamische, fail-closed Formelansicht** mit 12 Spalten (`Batch`, `Firma`, `Ansprechpartner`, `E-Mail`, `Verantwortlicher`, `Rechtsgrundlage`, `Versandfreigabe`, `Entwurf-ID`, `Versendet am`, `Antwort`, `Notiz`, `Lead-ID`). `README` zeigt Live-Kennzahlen. Die Operator-Schicht existiert also teilweise — gearbeitet wird trotzdem in `ALL_LEADS`/`JOEL`/`JORDI` (Screenshot). Der Plan muss klären, **warum** (fehlende Aktionen? fehlende Felder? Gewohnheit?), nicht nur formatieren.
- `JOEL`/`JORDI` (je 7.000 × 56) neben `ALL_LEADS`: zu klären, ob Formel-Sichten oder **Kopien** (dann dreifache Wahrheit im selben Sheet — Prio-1-Befund).
- Live-Zahlen `DASHBOARD`/`README` (2026-09-17): 6.424 Kontakte (3.212/3.212), Tier A 1.612, Tier B 4.812, 2.470 in Batches reserviert, **159 manuell versendet** (bestätigt, 119 Jordi / 40 Joel), 0 Antworten erfasst, 41 Opt-outs/Bounces, 37 offene Review-Fälle, 7 Batches. `CONTROL_CENTER` (04.09.): 219 Leads mit `Versandfreigabe=yes` + `Legal_Basis=EXISTING_CUSTOMER_7_3`. Die Aussage „Versandfreigabe 0/6424" in älteren Repo-Dokumenten ist damit **überholt** — der Plan zitiert die Sheet-Zahlen, nicht die Repo-Zahlen.
- `INBOUND_EVENTS` enthält `OPCONFIRM-…`-Ereignisse (Mailbox `SENT`, `Classification`, `Stop_Followup`, `Processed`) — der Rückkanal für manuelle Sendebestätigungen existiert; echte Antworten (`Reply_Status`) werden bisher nicht erfasst (0).
- Sicherheitsinvariante gilt weiterhin: kein automatischer Versand; die 159 Sendungen erfolgten manuell in Outlook (`CONTROL_CENTER`: Power Automate erzeugt nur Entwürfe, keine Send-Action).
- `apps/sales-os/README_OPERATING.md`: Seitenleiste „HSB Sales OS" (Apps Script) ist der operative Weg (Absender → „N freigeben & Entwürfe erzeugen" → Pakete automatisch → „Vorgang sicher erneut versuchen").
- Engine (`sheet_loader.py`, `hsb_core.py`, `batch_engine.py`, `build_versand.py`) und Apps Script lesen Spalten **per Header-Namen**; der Plan weist den vollständigen Spaltenvertrag mit Datei:Zeile aus. Header umbenennen oder Spalten löschen bricht Engine und Script.
- Bestand: `engine/apply_sheet_formatting.py`, `sync_to_google_sheet.py`, `gemini_enricher.py`, `drive_ecosystem_*.py`, `graph_drafts.py`, `pa_direct_drafts.py` — vor Neubau prüfen.
- Grenzen: Apps-Script-Laufzeit 6 min, Sheets-API-Quoten, Anhang 1,5 MB je Entwurf, Exchange 30 Nachrichten/min.

## Pflichtlektüre (in dieser Reihenfolge)

1. `MASTER_EXECUTION_RULES.md`, `PROJECT_TRUTH.md`, `AI_EXECUTION_PLAYBOOK.md` (Repo-Root)
2. `~/KI-System/ObsidianVault/brain/CANONICAL_STATE.md`, `active_state.json` (→ `do_not_do`, `blocked_followups` mit `crm`/`sheet`/`sales`), `CURRENT_HANDOFF.md`, `01_core/STORAGE_ROLES.md`
3. `apps/sales-os/PROJECT_STATE.md`, `README_OPERATING.md`, `CURRENT_HANDOFF.md`, `VERIFICATION_REPORT.md`, `RELEASE_MANIFEST.json`
4. `docs/crm/CRM_DATENQUELLE_WAHRHEIT.md`, `CRM_DISPATCH_ENGINE_2026-08-14.md`, `CRM_FINALIZATION_2026-08-11.md`, `CRM_LIGHT_OPERATOR_READINESS.md`, `CRM_LIGHT_MAX_READINESS.md`
5. `apps/sales-os/engine/*.py` (Spaltenvertrag), `apps/sales-os/apps_script/` (Sidebar, Gates, Trigger), `apps/sales-os/flows/` (Power Automate), `apps/sales-os/tests/`

## Werkzeugkasten, der vollständig zu bewerten ist (je Werkzeug: Nutzen, Best Practice, Risiko, Kosten, Datenschutz, Empfehlung ja/nein)

1. **Sheets-nativ:** Tabellen-Feature („In Tabelle konvertieren", Spaltentypen, Tabellenansichten), Filteransichten je Owner, Gruppierung/Ausblenden der Maschinenspalten, fixierte Zeilen/Spalten, Datenvalidierung als Dropdown-Chips (`Versandfreigabe`, `Legal_Basis`, `Reply_Status`, `Send_Status`), Personen-/Datums-Chips, bedingte Formatierung (Ampeln), Zeitachsen-Ansicht für `Next_Action_At`, geschützte Bereiche für Engine-Spalten, benannte Bereiche, bedingte Benachrichtigungen (Antwort/Bounce), Versionsverlauf.
2. **Apps Script (bestehend):** Seitenleiste modernisieren (HTML-Service, klare Zustände, Fortschritt, Fehlerbilder), Menüaktionen für Tagesarbeit (Antwort erfassen, Follow-up setzen, Suppression), zeitgesteuerte Trigger für `VERSAND`/`DASHBOARD`-Aktualisierung, Ausführungsprotokoll; Grenzen (6 min, Quoten) einplanen; Deployment-Versionierung ohne neue IDs.
3. **AppSheet** (Google-nativ, Sheet als Backend, keine zweite Wahrheit): Operator-App je Rolle (Jordi/Joel), mobil, Aktionen mit Gates; prüfen, ob die Send-Sperre und Reservierungslogik im Apps Script bleibt und AppSheet nur Zustände schreibt, die das Script ohnehin erlaubt.
4. **Looker Studio:** Dashboard auf dem Sheet (nur lesend): Pipeline, Batches, Antwortquote, Bounces, Freigabestand je Owner.
5. **Gemini:** Gemini in Sheets/Workspace (Klassifikation von Antworten, Zusammenfassung, Datenbereinigung) und der bestehende `gemini_enricher.py`; ausdrücklich prüfen: Datenschutz (B2B-Kontaktdaten), Kosten, Determinismus, Owner-Freigabe je Nutzung; kein Gemini-Schreibzugriff auf Gate-Spalten.
6. **Power Automate / Outlook-Adapter (bestehend):** Rückkanal für `Sent_At`, `Reply_Status`, `Bounce_Status`, Message-IDs — was ist heute automatisiert, was manuell, was sollte es sein.
7. **Drive-Ökosystem:** Ablage von Anhängen, Konversations-Exporten, Backups; Verweise statt Kopien.
8. **Add-ons / Installationen:** Nur mit Datenschutzbewertung, Berechtigungsumfang und Deinstallationspfad; ohne Nachweis eines konkreten Nutzens: nein.
9. **n8n:** nur, wenn ein Rückkanal ohne Apps-Script-Grenzen zwingend nötig ist; keine Wahrheitsquelle.

Für jedes Werkzeug gilt: Was liest es, was schreibt es, in welche Spalten, wer klickt, was passiert bei Fehler, wie wird es zurückgebaut.

## Erwartetes Ergebnis: genau eine Plandatei

Pfad: `apps/sales-os/docs/CRM_UEBERARBEITUNG_PLAN_2026-09-17.md` (einzige erlaubte Schreiboperation). Struktur:

1. **Ist-Aufnahme (read-only, belegt):** Tabs, Spaltenzahl je Tab, Header-Liste, Spaltenvertrag (welche Header Engine/Apps Script/Power Automate lesen — Datei:Zeile), Formeln, Validierungen, geschützte/benannte Bereiche, Trigger, Sidebar-Funktionen. Zahlen nur, wenn gemessen (Befehl + Ausgabe zitieren) oder aus Repo-Quellen belegt; Screenshot-Befunde des Owners bestätigen oder korrigieren.
2. **Operator-Zielbild** für Jordi und Joel: Tagesablauf in 5–8 Schritten, die 8–12 Spalten des Tagesbetriebs, Aktionen (freigeben, Batch erzeugen, Antwort erfassen, Follow-up datieren, Suppression), Ampeln, Kennzahlen; Rollen/Rechte; mobil oder nur Desktop.
3. **Datenhygiene und Governance:** Eigentumsübergang des Sheets vom Privatkonto auf ein HSB-Konto (Auswirkungen auf Apps-Script-Bindung, Trigger, Freigaben, Power-Automate-Connection), Klärung `JOEL`/`JORDI` vs. `ALL_LEADS` (Sicht oder Kopie), Archivierungsvorschlag für Legacy-/Backup-Tabs mit Manifest, Reply-Erfassung (0 Antworten trotz 159 Sendungen).
4. **Funktionslandkarte:** Was das System heute kann, was fehlt (Pipeline-Stufen, Follow-up-Steuerung, Antwortklassifikation, Bounce-Handling, Batch-Historie, Datenqualität/Dubletten, Kennzahlen), Priorität je Lücke.
5. **Werkzeugbewertung** nach obiger Liste, mit begründeter Auswahl und einem **Zielstack** (welche Werkzeuge, in welcher Rolle, mit welchem Schreibrecht).
6. **Zielarchitektur:** `ALL_LEADS` als Rohdaten-Store (Maschinenspalten gruppiert/versteckt/geschützt), kuratierte Sichten (`VERSAND`, `DASHBOARD`, ggf. `HEUTE_JOEL`/`HEUTE_JORDI`) per QUERY/FILTER ohne Kopien, Sidebar/AppSheet als Aktionsschicht, Looker Studio als Berichtsschicht; Datenfluss-Diagramm (Text), Schreibrechte-Matrix (Mensch / Script / Adapter / Gemini) je Spalte.
7. **Umsetzungsvarianten** (mindestens zwei, z. B. „Sheets-nativ + Apps Script" vs. „+ AppSheet-App"), je mit Aufwand in Tagen, Risiko, Rückbau, Betriebskosten; Empfehlung mit Reihenfolge (Quick Wins zuerst, die den Betrieb sofort verbessern).
8. **Sicherheitsplan:** Vor jedem Schreibzugriff datierte Sheet-Kopie in Drive **und** CSV-Export je Tab mit SHA-256-Manifest unter `~/KI-System/08_System/backups/<datum>-hsb-crm-sheet/`; Rollback-Schritte; Engine-Tests `apps/sales-os/tests` vor/nach; Zero-Send-Nachweis vor/nach; Spaltenvertrag-Test (Header unverändert); Owner-Freigabepunkte.
9. **Task-Liste** in atomaren, einzeln verifizierbaren Schritten (Schritt → Befehl/Aktion → erwartete Ausgabe → Prüfung), skriptbasiert wo möglich (`apply_sheet_formatting.py` erweitern statt Klick-Anleitungen), geeignet zur Übergabe an Claude Code.
10. **Team-Nachweis:** Abschnitte von `oma-researcher` (Ist), `oma-architect` (Zielbild/Varianten), `oma-planner` (Tasks), `oma-consensus` (Variantenentscheid), `oma-reviewer` (Plan-Review, Befunde), `oma-verifier` (Vollständigkeit gegen diese Liste) — mit Modellangabe.
11. **Nicht getan / bewusst offen** (explizit).

## Harte Regeln

- PLAN-Modus: keine Änderung an Sheet, Apps Script, Power Automate, Drive, Add-ons oder Repo außer der Plandatei. Lesen per Sheets-/Drive-API nur, wenn ein Google-Profil ohne Rückfrage verfügbar ist — sonst Ist-Aufnahme aus Repo und Screenshot, Lücken kennzeichnen.
- Keine Ressourcen-IDs, Tokens, Webhook-URLs, keine personenbezogenen Leaddaten in die Plandatei (IDs stehen in `PROJECT_STATE.md`, dort referenzieren).
- Keine erfundenen Zahlen. Jede Zahl mit Messbefehl oder Quelle.
- `do_not_do` aus `active_state.json` ist verbindlich. Privates Konto `cherinodiaz@outlook.com` nie mit HSB-Flüssen mischen.
- Keine Versandfreigabe-Logik ändern; `PHASE_7_COMPLIANCE_GATE` bleibt unberührt.
- Abschluss nur mit `oma-reviewer`-Review und `oma-verifier`-Prüfung gegen diese Liste; beide Ergebnisse im Plan zitieren.

## Nach Abgabe

Der Owner übergibt die Plandatei an Claude Code. Claude Code prüft gegen diesen Auftrag, die Wahrheitsdateien und die Engine-Verträge und gibt ein Gutachten ab; der Owner gibt frei. Erst danach Umsetzung — mit Backup, atomar, mit Verifikation vor jeder Fertigmeldung.
