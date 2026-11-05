# Vollständige Entwurfs-Verifikation: Implementierungsplan

> **Für ausführende Agenten:** PFLICHT-SKILL: `superpowers:executing-plans` (Ausführung in dieser Sitzung, gewählt durch `/loop`). Schritte nutzen Checkboxen (`- [ ]`). Der Loop-Teil (Task 4) läuft nur nach dem Kontrakt `docs/ai_state/loops/2026-11-05-entwuerfe-verifikation.md`.

**Ziel:** Ein einziger Prüflauf belegt für jeden Entwurf beider .com-Postfächer, dass er exakt der aktuellen Fassung entspricht oder aus einem benannten Grund zurückgehalten wird. Danach gibt es keine ungeklärten Mängel mehr.

**Architektur:** Das bestehende Audit (`sales_reconciliation.py`) bleibt die Datenquelle. Der neue Prüfer `draft_verify.py` liest dessen Ergebnis samt Roh-Mails, rendert jeden Entwurf frisch aus dem CRM und vergleicht ihn inhaltlich. Mängel repariert `refresh-signature` in place. Alles läuft in GitHub Actions, denn auf dem Mac gibt es keine Postfach-Zugangsdaten. Das Log zeigt nur Zahlen.

**Tech Stack:** Python 3.14, pytest, GitHub Actions (`sales-os-safety.yml`), All-Inkl IMAP, Google Sheets.

**Spec:** Keine eigene Datei. Grundlage ist der Nutzerauftrag vom 05.11.2026: „bis Verifikation aller Entwürfe perfekt bereit liegen“. Dieser Plan setzt `docs/ai_state/loops/2026-11-04-prepare-drafts-kette.md` fort.

## Ausgangslage (belegt)

| Quelle | Stand |
|---|---|
| Letztes Voll-Audit (Lauf 268, `audit-3`, 05.11. 10:40 UTC) | JOEL 2.784 von 2.830 versandbereit, JORDI 1.924 von 1.955 |
| Rest JORDI | 30 schon angeschrieben, 1 nicht freigegeben. Damit ist JORDI am Maximum. |
| Rest JOEL | 38 schon angeschrieben, 3 technisch sauber, aber nicht freigegeben, dazu 5 Fälle mit Befund. Aus den Meldungszahlen abgeleitet, nicht je Entwurf belegt: 2 unbestätigte Firma, 1 Eingang zu prüfen, 2 Mails ohne HSB-Kopfzeilen. |
| Auffällig | Zwischen 09:05 und 10:40 UTC verloren 2 JOEL-Entwürfe ihre HSB-Kopfzeilen und ihren Textteil. Vermutete Ursache: Öffnen in Outlook mobil (Screenshot `info@arekon.de`). Noch nicht belegt. |
| Prüflücke 1 | `assess_message` prüft weder Logo noch Signatur, noch ob der Text zum aktuellen CRM-Stand passt |
| Prüflücke 2 | Freigegebene Leads ganz ohne Entwurf werden nicht je Postfach gezählt. Es gibt nur die Gesamtzahl `NO_DRAFT` = 1.639, darin auch Kontaktierte und Gesperrte. |
| Rendering seit dem Aufbau | `git diff 72952df origin/main` zeigt nur die Eigentümer-Prüfung (#532), keine Änderung an Text oder HTML. Der Vergleich kann also nicht allein deshalb abweichen. |
| Vorhandener Prüfer | `readiness_probe.py` auf `ops/draft-readiness-probe-20261105` prüft nur 50 je Postfach und vergleicht nicht mit einem Rendering. Wird nicht übernommen, das Audit bleibt die eine Datenquelle. |
| Technik | Auf dem Mac fehlt `~/.config/hsb-sales-os/env`, jeder Postfachschritt läuft daher per `gh workflow run`. Das Log eines laufenden Jobs gibt GitHub erst nach Job-Ende frei. |

## Global Constraints

- Kundenversand: 0. `HSB_CUSTOMER_SEND_ENABLED=no` in jedem Lauf, Modus `send` wird nie ausgelöst.
- `REPARATUR_COPY_REV` bleibt `2026-11-05`. Keine Text- und keine Gestaltungsänderung.
- CI-Logs enthalten nur Zahlen: kein `@`, keine Firmen, keine Lead-IDs.
- Gesperrte Leads bleiben gesperrt: Opt-out, Bounce, Antwort, `EXPLICIT_LEGAL_BLOCK`, `Versandfreigabe=no`, schon kontaktiert.
- Originale werden nur per UID MOVE nach `Entwürfe-Archiv-v1` verschoben. Kein EXPUNGE, kein Löschen.
- § 7 UWG ist vom Betreiber geklärt (`PROJECT_TRUTH.md`): keine Frage, keine Warnung.
- Vor jedem Commit: `python3 scripts/verify_ssot.py` mit Exit 0, exakte Pfade stagen.
- Arbeit im Worktree `.worktrees/entwuerfe-verifikation`, Branch `fix/entwuerfe-verifikation`, ab `origin/main`. Der lokale Stand ist rund 10 Commits zurück und bleibt unberührt.

## Review Focus

1. **Ein in Outlook geänderter Entwurf:** Hat jemand den Text wirklich geändert, darf der Lauf ihn nicht überschreiben. Er wird als `HUMAN_EDITED` zurückgehalten. Test: `test_resaved_with_changed_text_is_held` (Task 3).
2. **CRM nach dem Rendern korrigiert**, zum Beispiel ein anderer Nachname: Der Entwurf wirkt technisch sauber, trägt aber den alten Namen. Das ist ein Mangel und wird in place erneuert. Tests: `test_stale_name_is_text_differs` (Task 1), `test_deep_defect_is_refreshed` (Task 3).
3. **Umlaute und Quoted-Printable:** „Müller“ und „Säurebau“ dürfen keinen Fehlalarm auslösen. Verglichen wird dekodierter Inhalt mit normalisierten Zeilenenden, nicht Bytes. Test: `test_umlauts_and_qp_match` (Task 1).
4. **Unvollständiger Schnappschuss** (fehlende Roh-Mail, leeres Audit, Summen stimmen nicht): Das Ergebnis darf nie `PERFECT` sein, der Prüfer endet mit Exit-Code ungleich 0. Test: `test_incomplete_snapshot_is_never_perfect` (Task 1).
5. **Lead nach dem Audit gesperrt:** Der Entwurf wird nicht erneuert und zählt als zurückgehalten. Test: `test_blocked_lead_is_not_refreshed` (Task 3).

---

### Task 1: Prüfer `draft_verify.py`

**Files:**
- Create: `apps/sales-os/engine/draft_verify.py`
- Test: `apps/sales-os/tests/test_draft_verify.py`

**Interfaces:**
- Consumes: Audit-Verzeichnis mit `drafts.json`, `leads.json`, `crm-original.json` und den Roh-Mails unter `record['path']`; `render_email_v2`, `LOGO_URL`, `REPAIR_URL`, `REPARATUR_COPY_REV`, `queue_block_reasons`.
- Produces:
  - `visible_text(raw: bytes) -> str`: sichtbarer Text aus dem HTML-Teil, sonst aus dem Textteil, Leerzeichen zusammengezogen
  - `deep_check(raw: bytes, lead: dict, owner: str) -> list[str]`: Codes aus `SUBJECT_DIFFERS`, `TEXT_DIFFERS`, `HTML_DIFFERS`, `LOGO_MISSING`, `LINK_NOT_SINGLE`, `REV_WRONG`, `TEMPLATE_WRONG`, `FROM_WRONG`, `ATTACHMENT_PRESENT`, `CRM_TEMPLATE_STALE`, `CRM_BINDING_DIFFERS`
  - `classify(record: dict, lead: dict | None, raw: bytes) -> tuple[str, str]`: gibt `(bucket, grund)` zurück, mit `bucket` aus `OK`, `HELD`, `DEFECT`
  - `verify_audit_dir(audit_dir: Path) -> dict`: Ergebnis `{'owners': {'JOEL': {'scanned', 'ok', 'held': {grund: n}, 'defects': {grund: n}, 'eligible_without_draft'}, 'JORDI': {…}}, 'verdict': 'PERFECT' | 'NOT_READY', 'customer_emails_sent': 0}`; schreibt zusätzlich `deep_defects.json` (Datensatz-Schlüssel, nur im privaten Audit-Verzeichnis)
  - CLI: `python -u draft_verify.py --audit-dir DIR` druckt das Ergebnis als JSON. Exit 0 bei `PERFECT`, Exit 3 bei `NOT_READY`, Exit 2 bei unvollständigem Schnappschuss.

**Einstufung, erste Regel gewinnt:**
1. `HELD/ALREADY_CONTACTED`: `ALREADY_CONTACTED` oder `ALREADY_CONTACTED_DOMAIN`
2. `HELD/INELIGIBLE`: `queue_block_reasons(lead)` ist nicht leer
3. `HELD/HUMAN_REVIEW`: `COMPANY_UNVERIFIED` oder `INBOUND_REQUIRES_REVIEW`
4. `HELD/HUMAN_EDITED`: `LEAD_ID_INFERRED_ONLY`, und der sichtbare Text weicht vom frischen Rendering ab
5. `DEFECT/CLIENT_RESAVED`: `LEAD_ID_INFERRED_ONLY`, sichtbarer Text unverändert
6. `DEFECT/<Code>`: jede andere Audit-Meldung und jeder `deep_check`-Code
7. `OK`: `record['sendable']` ist wahr und `deep_check` ist leer

`PERFECT` heißt: für beide Postfächer ist `ok > 0`, `defects` ist leer, `eligible_without_draft == 0`, und `ok + held == scanned`. `eligible_without_draft` zählt je Postfach Leads aus `leads.json`, deren einziger Grund `NO_DRAFT` ist.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

  Testdaten mit erfundenen Leads, Roh-Mail über `ComMailboxClient.build_draft_message` aus `render_email_v2` wie in `tests/test_signature_refresh.py`.

  - `test_fresh_draft_passes_deep_check`: `deep_check(...) == []`
  - `test_stale_name_is_text_differs`: Lead-Nachname nach dem Rendern geändert, `'TEXT_DIFFERS' in deep_check(...)`
  - `test_umlauts_and_qp_match`: Nachname „Müller“, `deep_check(...) == []`
  - `test_missing_logo_is_flagged`: HTML ohne `LOGO_URL`, `'LOGO_MISSING' in deep_check(...)`
  - `test_second_link_is_flagged`: zweiter `href`, `'LINK_NOT_SINGLE' in deep_check(...)`
  - `test_contacted_outranks_outdated`: Meldungen `['ALREADY_CONTACTED', 'OUTDATED_REPAIR_COPY']` ergeben `('HELD', 'ALREADY_CONTACTED')`
  - `test_resaved_is_defect_client_resaved`: `['LEAD_ID_INFERRED_ONLY']` mit unverändertem Text ergibt `('DEFECT', 'CLIENT_RESAVED')`
  - `test_resaved_with_edit_is_held`: dieselbe Meldung mit geändertem Text ergibt `('HELD', 'HUMAN_EDITED')`
  - `test_eligible_without_draft_blocks_perfect`: Lead mit Grund `['NO_DRAFT']`, Ergebnis `NOT_READY`
  - `test_incomplete_snapshot_is_never_perfect`: fehlende Roh-Mail oder leere `drafts.json`, CLI-Exit 2
  - `test_output_has_no_personal_data`: `'@' not in json.dumps(result)` und kein `HSB-` im Ergebnis

- [ ] **Schritt 2: Tests rot sehen**

  Run: `python3 -m pytest apps/sales-os/tests/test_draft_verify.py -q`
  Erwartet: FAIL mit `ModuleNotFoundError: draft_verify`

- [ ] **Schritt 3: Modul mit den Signaturen oben implementieren**

  Parts über `BytesParser(policy=policy.default)` lesen, `get_content()` nutzen, Zeilenenden normalisieren. Vergleichsbasis ist `render_email_v2(lead, owner, step=1, variant='reparatur')`.

- [ ] **Schritt 4: Tests grün sehen**

  Run: `python3 -m pytest apps/sales-os/tests/test_draft_verify.py -q`
  Erwartet: alle PASS

- [ ] **Schritt 5: Commit**

  ```bash
  git add apps/sales-os/engine/draft_verify.py apps/sales-os/tests/test_draft_verify.py
  git commit -m "feat(sales-os): Prüfer vergleicht jeden Entwurf mit frischem Rendering"
  ```

### Task 2: Prüfer in den Audit-Lauf einhängen, Altlast entfernen

**Files:**
- Modify: `.github/workflows/sales-os-safety.yml` (Schritt „Full read-only reconciliation“, Cron `55 1 5 11 *`, Job `chain-start`, Bedingung in `live-readonly-and-inbound`)
- Test: `apps/sales-os/tests/test_workflow_contract.py` (falls vorhanden ergänzen, sonst anlegen)

**Interfaces:**
- Consumes: CLI aus Task 1.
- Produces: Modus `audit` endet rot, solange das Ergebnis nicht `PERFECT` ist. `gh run watch <id> --exit-status` wird damit zum maschinellen Abschlusskriterium.

- [ ] **Schritt 1: Fehlschlagenden Test schreiben**

  `test_audit_mode_runs_verifier`: Die YAML-Datei enthält nach dem Audit-Befehl `draft_verify.py --audit-dir "$RUNNER_TEMP/hsb-reconciliation"`.
  `test_chain_start_removed`: `'55 1 5 11 *' not in text` und `'chain-start' not in text`.

- [ ] **Schritt 2: Test rot sehen**

  Run: `python3 -m pytest apps/sales-os/tests/test_workflow_contract.py -q`
  Erwartet: FAIL

- [ ] **Schritt 3: Workflow ändern**

  Neuer Schritt `Verify every draft against a fresh render` mit Bedingung `inputs.mode == 'audit'`. Cron-Zeile samt Kommentar und Job `chain-start` entfernen, ebenso die Klausel `github.event.schedule != '55 1 5 11 *'`. Das Job-Limit von 20 Minuten bleibt, der Prüfer braucht nur Sekunden.

- [ ] **Schritt 4: Test grün sehen und Commit**

  Run: `python3 -m pytest apps/sales-os/tests/test_workflow_contract.py -q && python3 scripts/verify_ssot.py`
  Erwartet: PASS, Exit 0

  ```bash
  git add .github/workflows/sales-os-safety.yml apps/sales-os/tests/test_workflow_contract.py
  git commit -m "feat(sales-os): Audit endet erst grün, wenn alle Entwürfe geprüft sind; einmaligen Ketten-Cron entfernt"
  ```

### Task 3: Reparaturwege für Prüfer-Mängel

**Files:**
- Modify: `apps/sales-os/engine/signature_refresh.py`
- Modify: `apps/sales-os/engine/draft_upgrade.py`
- Modify: `apps/sales-os/engine/hsb_cli.py` (`cmd_refresh_signature`)
- Modify: `apps/sales-os/bin/postfach-lauf.sh`
- Test: `apps/sales-os/tests/test_signature_refresh.py`, vorhandene Testdatei zu `draft_upgrade`

**Interfaces:**
- Consumes: `deep_defects.json` und `visible_text(raw: bytes) -> str` aus Task 1, `refresh_one` wie vorhanden.
- Produces:
  - `select_candidates(owner, records, leads, *, deep_defects: frozenset[str] = frozenset(), allow_mass_refresh: bool = False)`: nimmt zusätzlich Datensätze, deren Schlüssel `owner|uidvalidity|uid|sha256` in `deep_defects` steht und deren Audit-Meldungen leer oder in `REFRESHABLE` sind. Mehr als 50 solche Datensätze je Postfach: `RuntimeError('DEEP_DEFECT_CAP_EXCEEDED')`. Weder CLI noch Workflow setzen `allow_mass_refresh`.
  - `upgrade_drafts`: `LEAD_ID_INFERRED_ONLY` wird über den vorhandenen langsamen Weg neu aufgebaut, wenn genau ein freigegebener Lead zum Empfänger passt, das Postfach stimmt und der Lead keinen zweiten Entwurf hat. Das ergibt eine neue Message-ID und den vorhandenen CRM-Schreibweg. Weicht `visible_text(alt)` vom frischen Rendering ab: Überspringgrund `HUMAN_EDITED`, Postfach unverändert.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben, mit den vorhandenen Fakes**

  - `test_deep_defect_is_refreshed`: Audit ohne Meldung, Schlüssel in `deep_defects`, Ergebnis `REFRESHED`, gleiche Message-ID
  - `test_deep_defect_cap_stops`: 51 Schlüssel: `DEEP_DEFECT_CAP_EXCEEDED`, kein APPEND
  - `test_blocked_lead_is_not_refreshed`: `Versandfreigabe='no'`, nichts ausgewählt
  - `test_resaved_same_text_is_rebuilt`: Outlook-Fassung ohne HSB-Kopfzeilen, Text unverändert: neuer Entwurf, CRM gebunden, Original im Archiv
  - `test_resaved_with_changed_text_is_held`: Text geändert: `HUMAN_EDITED`, kein APPEND
  - `test_resaved_with_two_drafts_is_skipped`: zweiter Entwurf desselben Leads: nichts ausgewählt

- [ ] **Schritt 2: Tests rot sehen**

  Run: `python3 -m pytest apps/sales-os/tests -q -k "deep_defect or resaved or blocked_lead"`
  Erwartet: die 6 neuen FAIL

- [ ] **Schritt 3: Implementieren**

  `cmd_refresh_signature` liest `deep_defects.json`, falls vorhanden. In `postfach-lauf.sh` läuft nach `audit-2` zuerst der Prüfer: Exit 3 ist normal, Exit 2 bricht den Lauf ab. Danach `refresh-signature`. `draft_upgrade` bekommt den neuen Fall als Ausnahme in der Auswahl und die Textprüfung in `handle`.

- [ ] **Schritt 4: Gesamte Suite grün sehen**

  Run: `python3 -m pytest apps/sales-os/tests -q && python3 scripts/verify_ssot.py`
  Erwartet: 0 failed, Exit 0

- [ ] **Schritt 5: Commit, frischer Reviewer, PR**

  ```bash
  git add apps/sales-os/engine/signature_refresh.py apps/sales-os/engine/draft_upgrade.py apps/sales-os/engine/hsb_cli.py apps/sales-os/bin/postfach-lauf.sh apps/sales-os/tests
  git commit -m "feat(sales-os): Prüfer-Mängel gedeckelt erneuern, neu gespeicherte Entwürfe wieder aufbauen"
  ```

  Diff von `code-reviewer-lite` prüfen lassen (Codex ist an seiner Nutzungsgrenze), Befunde beheben, dann Push und PR mit Auto-Merge. Erst der gemergte Stand auf `main` geht in Task 4.

### Task 4: Verifikations-Loop laufen lassen

**Files:**
- Modify: `docs/ai_state/loops/2026-11-05-entwuerfe-verifikation.md` (Protokoll, Haken)
- Modify: `docs/ai_state/loops/2026-11-04-prepare-drafts-kette.md` (als abgelöst markieren)
- Modify: `CURRENT_STATE.md`, `apps/sales-os/CURRENT_HANDOFF.md`, `CHECKPOINT_STATE.json`

**Interfaces:**
- Consumes: Modus `audit` (Task 2), Modus `prepare-drafts` (Task 3).
- Produces: das Ergebnis `PERFECT` im Log, belegte Endzahlen und die Liste der zurückgehaltenen Gründe.

- [ ] **Schritt 1: Andere Schreiber ausschließen**

  Run: `gh run list --workflow sales-os-safety.yml --status in_progress --json number,headBranch; gh run list --workflow sales-os-safety.yml --status queued --json number`
  Erwartet: leer. Sonst warten, nie parallel starten.

- [ ] **Schritt 2: Audit starten und auf das Ende warten**

  Run: `gh workflow run sales-os-safety.yml --ref main -f mode=audit`, dann `gh run watch <id> --exit-status` als Hintergrundbefehl
  Erwartet: Exit 0 heißt weiter zu Schritt 4, Exit ungleich 0 heißt weiter zu Schritt 3. Der erste Prüflauf bleibt immer rein lesend: Erst die Zahlen lesen, dann entscheiden. Ein Massenbefund bei `TEXT_DIFFERS` oder `HTML_DIFFERS` ist zuerst ein Fehlerverdacht gegen den Prüfer, keine Erneuerung.

- [ ] **Schritt 3: Mängel beheben und Schritt 1 wiederholen**

  Log lesen: `gh run view <id> --log | grep -E '"verdict"|"defects"|"held"'`.

  Nur Code-Regeln, dann `gh workflow run sales-os-safety.yml --ref main -f mode=prepare-drafts`. Ein neuer Mängeltyp bekommt zuerst einen Test und einen PR. Ist `eligible_without_draft` größer 0: neuer Task mit dem vorhandenen `new_drafts.py`. Eine Zeile ins Protokoll: Kriterium, Zahl vorher, Zahl nachher.

- [ ] **Schritt 4: Versandweg lesend bestätigen**

  Run: `gh workflow run sales-os-safety.yml --ref main -f mode=send-preview -f count=5`
  Erwartet: im Log `DRY_RUN_COMPLETED`, `selected` 5 für JOEL und 5 für JORDI, `customer_emails_sent` 0.

- [ ] **Schritt 5: Abschluss prüfen und übergeben**

  `validation-auditor` prüft jede Endzahl gegen das Log. Haken im Kontrakt setzen, Stand-Dateien fortschreiben. PR mit diesen Dokumenten, dann `ai-state event --tool claude --type checkpoint --msg "Entwurfs-Verifikation beendet: <Bilanz>"`.

## Nicht in diesem Plan

- **Gleichmäßigere Verteilung auf die Postfächer:** eigener Auftrag. `run_audit` bricht ab, wenn die Zuständigkeit im CRM nicht genau 3.212 zu 3.212 steht.
- **Empfehlungen aus der Recherche** (Warm-up, Text, Datenschutz-Hinweis, DKIM im KAS): Sie ändern Texte oder liegen im KAS bei dir.
- **Darstellung des Links in Outlook mobil im Dunkelmodus:** Im Screenshot steht der Link dunkel auf farbigem Grund. Ob das nur die Markierung beim Bearbeiten ist, zeigt eine echte Testmail. Eine Änderung hieße neue Fassung und Neuaufbau aller Entwürfe, daher keine Änderung ohne deine Entscheidung.
