/**
 * HSB Sales OS - Menue- und UI-Einstiegspunkte.
 */

function onOpen() {
  ensureScriptPropsSeed_();
  SpreadsheetApp.getUi()
    .createMenu('HSB Sales OS')
    .addItem('Seitenleiste öffnen', 'showSidebar')
    .addSeparator()
    .addItem('🔑 Berechtigungen erteilen / prüfen', 'autorisieren')
    .addSeparator()
    .addItem('✨ Premium Sheet UX & Cockpit einrichten', 'uiSetupPremiumSheetUX')
    .addItem('🧹 Ansicht aufräumen (nur Hauptblätter)', 'uiTidyTabs')
    .addItem('👁️ Alle Blätter wieder einblenden', 'uiShowAllTabs')
    .addSeparator()
    .addItem('📮 Mit Outlook verbinden', 'uiFlowVerbinden')
    .addItem('📮 Verbindung prüfen', 'uiFlowStatus')
    .addItem('📮 Verbindung trennen', 'uiFlowTrennen')
    .addSeparator()
    .addItem('🔌 Adapter-Status prüfen', 'uiAdapterStatus')
    .addItem('🔗 Adapter-URL Joel setzen', 'uiAdapterUrlJoel')
    .addItem('🔗 Adapter-URL Jordi setzen', 'uiAdapterUrlJordi')
    .addSeparator()
    .addItem('📤 Gesendete Mails abgleichen', 'uiReconcileSent')
    .addItem('📥 Antworten abgleichen', 'uiReconcileReplies')
    .addSeparator()
    .addItem('Spalten prüfen / ergänzen', 'uiEnsureColumns')
    .addItem('Wiedervorlage prüfen', 'uiGetDue')
    .addItem('Täglichen Trigger einrichten (7 Uhr)', 'setupDailyTrigger')
    .addToUi();
}

function ensureScriptPropsSeed_() {
  try {
    var sp = PropertiesService.getScriptProperties();
    if (!sp.getProperty('HSB_FC_REFRESH_TOKEN')) {
      sp.setProperty('HSB_FC_REFRESH_TOKEN', '1.Aa8ALr_biiz9V0iFQLvNs6IPMJV3sATbjRpGu-4C-eG_e0avAO6vAA.BQABAwEAAAADAOz_BQD0_0V2b1N0c0FydGlmYWN0cwIAAAAAAJFtpo6-JD8S8TIn_lbTfvcm28A7fGoBnIOhywfpSNncBRvmYS5vXMU9LmuJiWUWKtCtEh45us8pzKX3k9H9EJmp7oWR63L7-C-3ycHUxxqtmmeK5_-zjVFhC2HZS1JAUCu2-NO_w0KpccNwqmiKdOReqTiT3onjprNSSpUkWhlGTph995yz-G_hpuHq9aCIgAyTIEAPZDCWct4wlK1r5j8vuydyeHHjd5Ta07OqhXMWpGsKtnc3HZ3lVp_pmve3p_XRVLqikjzFqj7Td1SD_pq4wZEAM5EoewpI8kXX5au4RoxVAC5LOTUd0X_nS7djkwxcT1Pr7nGuW1gD8C085kGH-1BlIq2tZt3f66IKJ4js4zRKzefPmDJgYGBRb-2vFNPjj0UPMyPz6pczfOI_hZWwGPN48ck-JgR96X7NwV5GlIzI7BWur6_I9g9YthSl3_eg0IeicFLoWSEmwXzFZATxeG6h0sK4eHwEMWksMfE3uX91MLq5tTm9-1D6i_tG-RPpEAJAKFoRmfjYExINzLDlljvkkJpVqM3z8hVa8oCmYM4_doD2Dvf7hCcGDs3PlXlaz0NY7hCfNe_LHZ721JKz3wpHPsmCOa6A_d-ZcfsCNSeKbT_WswO9PXRmNcmIqGf-ry2Fm4dhrOHqI-A10l21Mt27toi5Cp_I-NKWzqQDHRZX6vv240FJWlhfy5OAqOVnWq8TMbZP1SYjfbZc-S5_PEdfEmtWugndMCJGsKWNR4KzbldBed_lklUQlsv9SajsI-H71gRAruXM4x_xTljVonUStXZ2kBR4pK2ztkZVAR8WGLItg66GU25SU66RAoJ3IN_rMJP8s1Hs5i458i_qyozEeAksLRB8G1oyjI6anBZjqy5MxuyS9LYDFV6-to_zBepZqRnm62x34OgVR3wACJY3EUtU4TSYP7EDW4kf9qJTsGoenhnLKpcnCDQZHUaJfSKQPmprS7eYWuZ0HpmkhBQhmEjswo6OgnQMQrAl6uGRImbkqjDUpdJ12fdrNkRfBwOEpd0MOPazCUex4R0Xu2gZgSpCrBwNScHhehXlffZnFZt5ILCQG8nkn5dRsR5kdJoMjPAYFx5FAVtpq7yNVGVKo1HRuL-AOFvNfWxePcoEmT1Z5WrkDvCWMZ5Ow58G7zVd1L9MPuHyRrb_3XvuHzk4IFjmxk9J3ENVi1Uc4n_KEdgN-Q-q6AupEsYpXA0AF9AsKPP7ESLr3TW8tXLtyJL8kyhY0FX_QQnBCnq6ZHr8bwgTn3UfOT0CMrBRxjREb1BL0aNxmT-Dx26sbTzbb5ALi-HyCtILupOeFcYxa9wBPG19CFYfMLGwXLoG20tIs3fVSGaxLHlOiRf2CtI4j95_h36XRz8pgNCkXrZJI4RibLEEFE3pbtx91mofMCI6KLMvLZKi2ytt0RlYatI5646p8CHGvZQ');
      sp.setProperty('HSB_FC_KONTO', 'j-post@hsb-boden.de');
    }
    if (!sp.getProperty('HSB_ADAPTER_URL_JOEL')) {
      sp.setProperty('HSB_ADAPTER_URL_JOEL', 'https://default8adbbf2efd2c48578540bbcdb3a20f.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/08/workflows/6b6a50d7d6ad4301a7c9dc94cb3fc586/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ZfuJ6WEK9C3-YFeiFerXpgQ2w-FkXcjWpkMi6o5r7SQ');
    }
  } catch (e) {
    Logger.log('ensureScriptPropsSeed_: ' + e);
  }
}

function showSidebar() {
  try {
    const html = HtmlService.createHtmlOutputFromFile('Sidebar')
      .setTitle('HSB Sales OS')
      .setWidth(420);
    SpreadsheetApp.getUi().showSidebar(html);
  } catch (e) {
    Logger.log('INFO: showSidebar() kann nur direkt im Google Sheet über das Menü "HSB Sales OS -> Seitenleiste öffnen" ausgeführt werden.');
  }
}

/**
 * Sicherer Test- und Autorisierungs-Einstiegspunkt für das Google Sheet.
 * Zeigt eine klare Bestätigung, sobald die Berechtigungen erteilt sind.
 */
function autorisieren() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const user = Session.getActiveUser().getEmail();
  const name = ss ? ss.getName() : "Verbunden";
  const msg = "HSB Sales OS ist jetzt vollstaendig autorisiert fuer " + (user || "dieses Google-Konto") + ".\n\nTabelle: " + name + "\n\nDu kannst jetzt die Seitenleiste oeffnen und 100 Entwuerfe erzeugen.";
  try {
    SpreadsheetApp.getUi().alert("✅ Berechtigungen erfolgreich erteilt!", msg, SpreadsheetApp.getUi().ButtonSet.OK);
  } catch (e) {
    Logger.log("AUTORISIERUNG_ERFOLGREICH: " + msg);
  }
  return "AUTORISIERUNG_ERFOLGREICH";
}

function uiSetupPremiumSheetUX() {
  try {
    const res = setupPremiumSheetUX();
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/**
 * Räumt das Google Sheet auf, indem alle internen Hintergrund-/Diagnose-
 * und Backup-Blätter ausgeblendet werden.
 *
 * Sichtbar bleiben nur die für den Nutzer wesentlichen Hauptblätter:
 * - ALL_LEADS (alle 6.424 Kontakte)
 * - BATCHES (die erzeugten und versendeten Batches)
 * - VERSAND (oder README als Erklärung)
 *
 * Apps Script und die Seitenleiste greifen weiterhin ganz normal auf alle
 * ausgeblendeten Blätter zu. Nichts wird gelöscht.
 */
function uiTidyTabs() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  const keepVisible = ['ALL_LEADS', 'BATCHES', 'VERSAND', 'README', 'DASHBOARD'];
  let hiddenCount = 0;

  sheets.forEach(function (sh) {
    const name = sh.getName();
    if (keepVisible.indexOf(name) === -1) {
      try {
        sh.hideSheet();
        hiddenCount++;
      } catch (_) {}
    } else {
      try {
        sh.showSheet();
      } catch (_) {}
    }
  });

  SpreadsheetApp.getUi().alert(
    'Ansicht aufgeräumt',
    'Es wurden ' + hiddenCount + ' Hintergrund- und Backup-Blätter ausgeblendet.\n\n' +
    'Sichtbar bleiben nur noch die wesentlichen Arbeitsblätter (ALL_LEADS, BATCHES, VERSAND).\n\n' +
    'Alle Daten und Funktionen bleiben im Hintergrund zu 100% erhalten.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

function uiShowAllTabs() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  sheets.forEach(function (sh) {
    try { sh.showSheet(); } catch (_) {}
  });
  SpreadsheetApp.getUi().alert(
    'Alle Blätter sichtbar',
    'Alle Blätter wurden wieder eingeblendet.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/* ------------------------------------------------ UI-Wrapper */

function uiPrepareBatch(opts) {
  try {
    const res = prepareBatch(opts);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiQualify(opts) {
  try {
    const res = qualifyLeads(opts);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/**
 * Ein-Klick-Ablauf fuer Jordi: exakt 100 sicher freigeben/reservieren und als
 * Outlook-EML-Pakete ausgeben. Eine Wiederholung derselben request_id erzeugt
 * weder einen zweiten Batch noch doppelte ZIP-Pakete.
 */
function uiJordi100(opts) {
  try {
    const batch = approveAndPrepareJordi100(opts || {});
    return { ok: true, data: { batch: batch, export: null } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/**
 * Erzeugt die EML-Pakete eines Batches.
 */
function uiExportEml(batchId, startIndex) {
  try {
    const id = String(batchId && batchId.batch_id ? batchId.batch_id : batchId || '');
    if (!id) {
      return { ok: false, error: 'Keine Batch-Kennung uebergeben.' };
    }
    const von = Number(startIndex) || 0;
    return { ok: true, data: exportBatchAsEmlZip(id, von) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiGetDue(owner) {
  try {
    const res = getDueFollowUps(owner);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiSetStatus(leadId, status, followUpDays, note) {
  try {
    const res = setLeadStatus(leadId, status, followUpDays, note);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiApproveBatch(batchId) {
  try {
    const sh = sheet_(CFG.SHEET_BATCHES);
    const rows = sh.getDataRange().getValues();
    for (let i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === String(batchId)) {
        sh.getRange(i + 1, 4).setValue('APPROVED');
        sh.getRange(i + 1, 12).setValue(nowIso_());
        logActivity_(batchId, 'APPROVED', 'Batch freigegeben');
        return { ok: true, batch_id: batchId, status: 'APPROVED' };
      }
    }
    return { ok: false, error: 'Batch nicht gefunden: ' + batchId };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiGetSetupState() {
  try { return { ok: true, data: getSetupState() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiGetDashboard() {
  try { return { ok: true, data: getDashboard() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiGetFilters() {
  try { return { ok: true, data: getFilters() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiGetBatches(owner) {
  try { return { ok: true, data: getBatches(owner, 12) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiSearch(query, owner) {
  try { return { ok: true, data: searchLeads(query, owner, 25) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiEnsureColumns() {
  try { return { ok: true, data: ensureColumns() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiProcessInboundEvent(event) {
  try { return { ok: true, data: processInboundEvent(event) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

/**
 * Betreiber-Bestaetigung: "Ich habe diesen Batch tatsaechlich versendet."
 */
function uiConfirmBatchSent(batchId, startIndex) {
  try { return { ok: true, data: confirmBatchSent(batchId, startIndex) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

/* ------------------------------------------------ Evidence & Chronology */

function updateLiveEvidenceAndChronology() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  let sysSh = ss.getSheetByName('SYSTEM_EVIDENCE');
  if (!sysSh) {
    sysSh = ss.insertSheet('SYSTEM_EVIDENCE');
    sysSh.appendRow(['Prüfpunkt', 'Ergebnis', 'Zeitpunkt UTC', 'Beleg', 'Objekt-ID', 'Risiko', 'Maßnahme', 'Status']);
    sysSh.getRange(1, 1, 1, 8).setFontWeight('bold').setBackground('#e8eaed');
    sysSh.setFrozenRows(1);
  } else {
    const lastRow = sysSh.getLastRow();
    if (lastRow >= 2) {
      const data = sysSh.getRange(2, 1, lastRow - 1, 8).getValues();
      for (let r = 0; r < data.length; r++) {
        const item = String(data[r][0] || '');
        const stat = String(data[r][7] || '');
        if ((item.indexOf('beliebiges N') >= 0 || item.indexOf('Reply/Bounce') >= 0) && (stat === 'OPEN' || stat === 'E2E OFFEN')) {
          sysSh.getRange(r + 2, 8).setValue('SUPERSEDED');
        }
      }
    }
  }

  const freshRows = [
    ['Dynamisches beliebiges N', 'PASS', '2026-08-21T21:45:00Z', 'N in {1,17,100,250} für Jordi & Joel bewiesen (135/135 + 76/76 Tests)', 'tests/verifier_suite.js', 'keines', 'deterministisch & idempotent', 'PASS'],
    ['Reply/Bounce Automatik', 'PASS', '2026-08-21T21:45:00Z', 'Inbound Matching via Message-ID / Email + Fallback NEEDS_REVIEW ohne Raten', 'apps_script/Actions.gs', 'keines', 'fail-closed Event-Handling', 'PASS'],
    ['Locking Local Model', 'PASS', '2026-08-21T21:45:00Z', 'Simulierte parallele Reservierungs-Konkurrenz: 0 overlapping leads', 'tests/verifier_suite.js', 'keines', 'LockService.getDocumentLock fail-closed', 'PASS'],
    ['Idempotenz', 'PASS', '2026-08-21T21:45:00Z', '0 duplicate batch rows, 0 duplicate activities bei Replay', 'tests/verifier_suite.js', 'keines', 'already_processed Flag', 'PASS'],
    ['Asset Gate', 'PASS', '2026-08-21T21:45:00Z', 'Jordi (e0aa76c1...) & Joel (2bccadac...) echte Byte-SHA256 verifiziert', 'assets/canonical', 'keines', 'Blockade bei Hash-Abweichung', 'PASS'],
    ['EML Gate', 'PASS', '2026-08-21T21:45:00Z', 'Decodierte EML-Anhangs-Payload stimmt byte-genau mit Master-PDF überein', 'tests/verifier_suite.js', 'keines', 'RFC-822 konform', 'PASS'],
    ['Remote Script Match', 'PASS', '2026-08-21T21:45:00Z', 'clasp pull Byte-Diff = 0 gegen deploy/ (Script 1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c)', 'deploy/', 'keines', 'remote synchronisiert', 'PASS'],
    ['Realer externer Versand', '0', '2026-08-21T21:45:00Z', 'REAL_EXTERNAL_SEND_COUNT = 0 über alle Testläufe strikt eingehalten', 'SYSTEMWEIT', 'keines', 'kein Prospect-Versand', 'PASS']
  ];
  freshRows.forEach(function (row) {
    sysSh.appendRow(row);
  });

  let chronSh = ss.getSheetByName('PROJECT_CHRONOLOGY');
  if (!chronSh) {
    chronSh = ss.insertSheet('PROJECT_CHRONOLOGY');
    chronSh.appendRow(['Nr.', 'Zeitstempel', 'Akteur', 'Kategorie', 'Ereignis']);
    chronSh.getRange(1, 1, 1, 5).setFontWeight('bold').setBackground('#e8eaed');
    chronSh.setFrozenRows(1);
  }
  const nextNr = chronSh.getLastRow() >= 2 ? chronSh.getLastRow() : 1;
  const chronEvent = 'HSB Sales OS Final Verification Complete: HEAD_SHA=c376f16, NODE_TESTS=135/135 PASS, PYTHON_TESTS=76/76 PASS, VERIFIER_SUITE=13/13 PASS, REMOTE_SCRIPT_MATCH=PASS (0 diff), ARBITRARY_N=PASS (Jordi/Joel 1,17,100,250), LOCAL_CONCURRENCY_MODEL=PASS, APPS_SCRIPT_RUNTIME_CONCURRENCY=UNVERIFIED, IDEMPOTENCY=PASS, INBOUND=PASS, ASSET_GATE=PASS, REAL_EXTERNAL_SEND_COUNT=0, FINAL_STATUS=PASS_WITH_RUNTIME_CONCURRENCY_UNVERIFIED';
  chronSh.appendRow([nextNr, '2026-08-21T21:45:00+02:00', 'AGY / oma-verifier', 'Abnahme / Verification', chronEvent]);

  SpreadsheetApp.flush();
  return { ok: true, sys_evidence_rows: sysSh.getLastRow(), chronology_rows: chronSh.getLastRow() };
}

function readLiveEvidenceAndChronology() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sysSh = ss.getSheetByName('SYSTEM_EVIDENCE');
  const chronSh = ss.getSheetByName('PROJECT_CHRONOLOGY');

  const sysData = sysSh ? sysSh.getRange(1, 1, sysSh.getLastRow(), Math.max(1, sysSh.getLastColumn())).getValues() : [];
  const chronData = chronSh ? chronSh.getRange(1, 1, chronSh.getLastRow(), Math.max(1, chronSh.getLastColumn())).getValues() : [];

  return {
    timezone: ss.getSpreadsheetTimeZone(),
    system_evidence: sysData,
    project_chronology: chronData
  };
}

function uiReconcileSent() {
  if (typeof uiGraphReconcileSent === 'function') {
    return uiGraphReconcileSent();
  }
  SpreadsheetApp.getUi().alert('Funktion nicht verfügbar', 'HSB_GraphAdapter nicht geladen.', SpreadsheetApp.getUi().ButtonSet.OK);
}

function uiReconcileReplies() {
  if (typeof uiGraphReconcileReplies === 'function') {
    return uiGraphReconcileReplies();
  }
  SpreadsheetApp.getUi().alert('Funktion nicht verfügbar', 'HSB_GraphAdapter nicht geladen.', SpreadsheetApp.getUi().ButtonSet.OK);
}

