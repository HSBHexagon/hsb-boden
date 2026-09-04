/**
 * HSB Sales OS — Draft-Adapter (Apps Script -> Power Automate -> Outlook-Entwurf)
 *
 * Vertrag (aus CURRENT HANDOFF 2026-08-28, Architektur eingefroren):
 *   - Google Sheet = SSOT. Apps Script entscheidet Eligibility, Owner,
 *     Legal_Basis, Template und Flyer. Power Automate entscheidet NICHTS.
 *   - Power Automate erzeugt ausschliesslich ENTWUERFE. Kein Auto-Send.
 *   - PREPARED != DRAFTED != SENT. Dieses Skript setzt NIEMALS SENT.
 *
 * Dieses Modul ruft keine Engine-Funktion blind auf: preflight() prueft zuerst,
 * ob die erwartete Engine-Oberflaeche wirklich existiert, und bricht sonst mit
 * einer klaren Meldung ab, statt eine zweite Parallelimplementierung zu bauen.
 */

// ---------------------------------------------------------------- Konfiguration

var ADAPTER_PROPS = {
  JORDI: 'HSB_ADAPTER_URL_JORDI',
  JOEL: 'HSB_ADAPTER_URL_JOEL'
};

// Muss vor jedem Lauf bewusst auf den freigegebenen Batch gesetzt werden.
// Kein automatisches "juengsten PREPARED-Batch nehmen": das waere nicht fail-closed.
var ACTIVE_BATCH_PROP = 'HSB_ACTIVE_BATCH_ID';
var EXPECTED_FLYER_SHA256 = {
  JORDI: 'e0aa76c1ffec5cf89289e6ab141691d42ea81ffd13db2f08f045342531f39acc'
};

// Spalten im Sheet, in die zurueckgeschrieben wird.
var WRITEBACK = {
  draftId: 'Draft_ID',
  internetMessageId: 'Internet_Message_ID',
  conversationId: 'Conversation_ID',
  draftedAt: 'Drafted_At',
  batchStatus: 'Batch_Status',
  sendStatus: 'Send_Status',
  lastError: 'Last_Error'
};

// Engine-Funktionen, auf die dieser Adapter angewiesen ist.
var REQUIRED_ENGINE_FUNCTIONS = ['readLeads_', 'getVerifiedFlyer_', 'renderEmail_', 'logActivity_'];

var HTTP_TIMEOUT_SECONDS = 60;

// ---------------------------------------------------------------- Preflight

/**
 * Prueft die Voraussetzungen, ohne irgendetwas zu veraendern.
 * Vor dem ersten echten Lauf ausfuehren und die Ausgabe lesen.
 */
function preflight() {
  var report = [];
  var ok = true;

  REQUIRED_ENGINE_FUNCTIONS.forEach(function (name) {
    var exists = (typeof this[name] === 'function') ||
                 (typeof globalThis[name] === 'function');
    report.push((exists ? 'OK   ' : 'FEHLT') + '  Engine-Funktion ' + name);
    if (!exists) ok = false;
  }, this);

  var props = PropertiesService.getScriptProperties();
  Object.keys(ADAPTER_PROPS).forEach(function (owner) {
    var key = ADAPTER_PROPS[owner];
    var url = props.getProperty(key);
    var good = !!url && url.indexOf('https://') === 0;
    report.push((good ? 'OK   ' : 'FEHLT') + '  Skripteigenschaft ' + key);
    if (!good) ok = false;
  });

  var activeBatch = props.getProperty(ACTIVE_BATCH_PROP);
  var activeBatchGood = !!activeBatch && /^HSB-[A-Z0-9-]+$/.test(activeBatch);
  report.push(
    (activeBatchGood ? 'OK   ' : 'FEHLT') + '  Skripteigenschaft ' +
    ACTIVE_BATCH_PROP + (activeBatchGood ? ' = ' + activeBatch : '')
  );
  if (!activeBatchGood) ok = false;

  report.push('');
  report.push(ok ? 'PREFLIGHT=PASS' : 'PREFLIGHT=FAIL — nichts ausfuehren, bis alle Zeilen OK sind.');
  var text = report.join('\n');
  Logger.log(text);
  return text;
}

// ---------------------------------------------------------------- Hilfen

/** Klartext aus renderEmail_ in HTML wandeln. Der Outlook-Connector erwartet HTML. */
function textToHtml_(text) {
  var escaped = String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return escaped
    .split(/\n{2,}/)
    .map(function (para) { return '<p>' + para.replace(/\n/g, '<br>') + '</p>'; })
    .join('');
}

/** Flyer als base64 fuer den Connector. Nutzt die Engine-Verifikation, kein eigener Pfad. */
function flyerAttachment_(owner) {
  var flyer = getVerifiedFlyer_(owner);
  if (!flyer) throw new Error('ASSET_GATE_FAIL: kein verifizierter Flyer fuer ' + owner);
  var blob = flyer.blob || DriveApp.getFileById(flyer.fileId).getBlob();
  return {
    Name: blob.getName(),
    ContentBytes: Utilities.base64Encode(blob.getBytes())
  };
}

function sha256Hex_(bytes) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes)
    .map(function (value) {
      return ((value + 256) % 256).toString(16).padStart(2, '0');
    })
    .join('');
}

/**
 * Read-only Asset-Gate. Erzeugt keinen Entwurf und schreibt nichts ins Sheet.
 * Vor entwurfTesten() ausfuehren und nur bei ASSET_GATE=PASS fortfahren.
 */
function flyerPruefen(owner) {
  var key = String(owner || 'JORDI').toUpperCase().indexOf('JORDI') >= 0 ? 'JORDI' : 'JOEL';
  var expected = EXPECTED_FLYER_SHA256[key];
  if (!expected) throw new Error('ASSET_GATE_FAIL: kein Soll-Hash fuer ' + key);

  var flyer = getVerifiedFlyer_(key);
  if (!flyer) throw new Error('ASSET_GATE_FAIL: kein Flyer fuer ' + key);
  var blob = flyer.blob || DriveApp.getFileById(flyer.fileId).getBlob();
  var bytes = blob.getBytes();
  var actual = sha256Hex_(bytes);
  var report = [
    'OWNER=' + key,
    'NAME=' + blob.getName(),
    'BYTES=' + bytes.length,
    'SHA256=' + actual,
    actual === expected ? 'ASSET_GATE=PASS' : 'ASSET_GATE=FAIL'
  ].join('\n');
  Logger.log(report);
  if (actual !== expected) {
    throw new Error('ASSET_GATE_FAIL: erwartet ' + expected + ', erhalten ' + actual);
  }
  return report;
}

function adapterUrlFor_(owner) {
  var key = ADAPTER_PROPS[String(owner).toUpperCase().indexOf('JORDI') >= 0 ? 'JORDI' : 'JOEL'];
  var url = PropertiesService.getScriptProperties().getProperty(key);
  if (!url) throw new Error('Skripteigenschaft ' + key + ' ist nicht gesetzt.');
  return url;
}

// ---------------------------------------------------------------- Kern

/**
 * Erzeugt Entwuerfe fuer einen vorbereiteten Batch.
 *
 * @param {string} batchId    Batch aus dem Sheet (PREPARED).
 * @param {Object} options    {limit: number, dryRun: boolean}
 *
 * Idempotenz: Leads mit Draft_ID werden uebersprungen. Ein Transportfehler ist
 * grundsaetzlich mehrdeutig: Er wird in Last_Error geschrieben und blockiert
 * jeden weiteren Versuch, bis ein Mensch den Outlook-Entwurfsordner geprueft
 * und den Fehler bewusst geklaert hat.
 */
function createDraftsForBatch(batchId, options) {
  options = options || {};
  var limit = options.limit || 1;              // bewusst 1 als Default
  var dryRun = options.dryRun === true;

  var pre = preflight();
  if (pre.indexOf('PREFLIGHT=PASS') < 0) throw new Error(pre);

  var leads = readLeads_({ batchId: batchId });
  if (!leads || !leads.length) {
    return 'Keine Leads im Batch ' + batchId + '. Das ist bei geschlossenem Gate korrektes Verhalten.';
  }

  var results = { attempted: 0, drafted: 0, skipped: 0, failed: 0, details: [] };

  for (var i = 0; i < leads.length && results.attempted < limit; i++) {
    var lead = leads[i];

    if (lead[WRITEBACK.draftId]) {
      results.skipped++;
      results.details.push(lead.Lead_ID + ' uebersprungen (Draft_ID vorhanden)');
      continue;
    }

    if (lead[WRITEBACK.lastError]) {
      throw new Error(
        'UNGEKLAERTER_VORFEHLER: ' + lead.Lead_ID + ' ' + lead[WRITEBACK.lastError] +
        '. Zuerst Outlook pruefen und den Fehler bewusst klaeren; kein automatischer Retry.'
      );
    }

    // "limit" begrenzt Netzwerkversuche, nicht nur erfolgreiche Antworten.
    // Damit macht entwurfTesten() unter allen Fehlerbedingungen hoechstens
    // einen einzigen Power-Automate-Aufruf.
    results.attempted++;

    var owner = lead.Verantwortlicher || lead.Owner;
    var rendered = renderEmail_(lead);          // Klartext aus der Engine
    var payload = {
      leadId: lead.Lead_ID,
      batchId: batchId,
      to: lead['E-Mail'] || lead.Email,
      subject: rendered.subject,
      bodyHtml: textToHtml_(rendered.body),
      attachments: [flyerAttachment_(owner)]
    };

    if (dryRun) {
      results.details.push(lead.Lead_ID + ' DRY-RUN, kein Aufruf');
      results.drafted++;
      continue;
    }

    var res;
    try {
      res = UrlFetchApp.fetch(adapterUrlFor_(owner), {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify(payload),
        timeoutSeconds: HTTP_TIMEOUT_SECONDS,
        muteHttpExceptions: true
      });
    } catch (transportError) {
      var transportMessage = 'TRANSPORT_UNKLAR: ' + String(transportError);
      writeBackError_(lead, transportMessage);
      logActivity_('DRAFT_FAILED', lead.Lead_ID, transportMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + transportMessage);
    }

    var code = res.getResponseCode();
    if (code !== 200) {
      results.failed++;
      var httpMessage = 'HTTP ' + code + ' ' + res.getContentText().slice(0, 200);
      writeBackError_(lead, httpMessage);
      logActivity_('DRAFT_FAILED', lead.Lead_ID, httpMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + httpMessage);
    }

    var body;
    try {
      body = JSON.parse(res.getContentText());
    } catch (parseError) {
      writeBackError_(lead, 'INVALID_RESPONSE_JSON');
      logActivity_('DRAFT_FAILED', lead.Lead_ID, 'INVALID_RESPONSE_JSON');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' INVALID_RESPONSE_JSON');
    }
    if (!body || !body.draftId) {
      writeBackError_(lead, 'MISSING_DRAFT_ID');
      logActivity_('DRAFT_FAILED', lead.Lead_ID, 'MISSING_DRAFT_ID');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' MISSING_DRAFT_ID');
    }
    writeBackDraft_(lead, body);
    logActivity_('DRAFTED', lead.Lead_ID, body.draftId);
    results.drafted++;
    results.details.push(lead.Lead_ID + ' DRAFTED ' + body.draftId);
  }

  var summary = 'Batch ' + batchId + ': ' + results.drafted + ' Entwuerfe, ' +
                results.skipped + ' uebersprungen, ' + results.failed + ' Fehler\n' +
                results.details.join('\n') +
                '\n\nSENT wird nicht gesetzt. Versand erfolgt manuell in Outlook.';
  Logger.log(summary);
  return summary;
}

/** Schreibt die Korrelations-IDs zurueck. Setzt niemals SENT. */
function writeBackDraft_(lead, body) {
  var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = lead._row;
  if (!row) throw new Error('Lead ohne Zeilenreferenz (_row): ' + lead.Lead_ID);

  var set = {};
  set[WRITEBACK.draftId] = body.draftId;
  set[WRITEBACK.internetMessageId] = body.internetMessageId;
  set[WRITEBACK.conversationId] = body.conversationId;
  set[WRITEBACK.draftedAt] = new Date();
  set[WRITEBACK.batchStatus] = 'DRAFTED';
  set[WRITEBACK.sendStatus] = 'drafted';
  set[WRITEBACK.lastError] = '';

  Object.keys(set).forEach(function (col) {
    if (headers.indexOf(col) < 0) throw new Error('Spalte fehlt im Sheet: ' + col);
  });
  Object.keys(set).forEach(function (col) {
    var idx = headers.indexOf(col);
    sheet.getRange(row, idx + 1).setValue(set[col]);
  });
}

/** Schreibt einen Fehler fail-closed zurueck. Kein automatischer Retry. */
function writeBackError_(lead, message) {
  var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = lead._row;
  if (!row) throw new Error('Lead ohne Zeilenreferenz (_row): ' + lead.Lead_ID);
  var idx = headers.indexOf(WRITEBACK.lastError);
  if (idx < 0) throw new Error('Spalte fehlt im Sheet: ' + WRITEBACK.lastError);
  sheet.getRange(row, idx + 1).setValue(String(message).slice(0, 500));
}

// ---------------------------------------------------------------- Bedienung

/** Ein einzelner Entwurf zum Pruefen. Immer damit anfangen. */
function entwurfTesten() {
  var batch = aktivenBatchFinden_();
  return createDraftsForBatch(batch, { limit: 1 });
}

/** Alle Entwuerfe des offenen Batches. Erst nach Sichtung des Testentwurfs. */
function entwuerfeErzeugen() {
  var batch = aktivenBatchFinden_();
  return createDraftsForBatch(batch, { limit: 9999 });
}

/** Verifiziert den explizit konfigurierten Batch und nimmt nie automatisch einen anderen. */
function aktivenBatchFinden_() {
  var batchId = PropertiesService.getScriptProperties().getProperty(ACTIVE_BATCH_PROP);
  if (!batchId) {
    throw new Error('Skripteigenschaft ' + ACTIVE_BATCH_PROP + ' fehlt. Kein Batch wird automatisch gewaehlt.');
  }
  var sheet = SpreadsheetApp.getActive().getSheetByName('BATCHES');
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idBatch = headers.indexOf('Batch');
  var idStatus = headers.indexOf('Status');
  if (idBatch < 0 || idStatus < 0) throw new Error('BATCHES: Spalten Batch/Status nicht gefunden.');
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idBatch]) !== String(batchId)) continue;
    if (String(data[i][idStatus]).toUpperCase() !== 'PREPARED') {
      throw new Error('Aktiver Batch ' + batchId + ' ist nicht PREPARED. Abbruch.');
    }
    return batchId;
  }
  throw new Error('Aktiver Batch ' + batchId + ' wurde in BATCHES nicht gefunden. Abbruch.');
}/**
 * HSB Sales OS — Draft-Adapter (Apps Script -> Power Automate -> Outlook-Entwurf)
 *
 * Vertrag (aus CURRENT HANDOFF 2026-08-28, Architektur eingefroren):
 *   - Google Sheet = SSOT. Apps Script entscheidet Eligibility, Owner,
 *     Legal_Basis, Template und Flyer. Power Automate entscheidet NICHTS.
 *   - Power Automate erzeugt ausschliesslich ENTWUERFE. Kein Auto-Send.
 *   - PREPARED != DRAFTED != SENT. Dieses Skript setzt NIEMALS SENT.
 *
 * Dieses Modul ruft keine Engine-Funktion blind auf: preflight() prueft zuerst,
 * ob die erwartete Engine-Oberflaeche wirklich existiert, und bricht sonst mit
 * einer klaren Meldung ab, statt eine zweite Parallelimplementierung zu bauen.
 */

// ---------------------------------------------------------------- Konfiguration

var ADAPTER_PROPS = {
  JORDI: 'HSB_ADAPTER_URL_JORDI',
  JOEL: 'HSB_ADAPTER_URL_JOEL'
};

// Muss vor jedem Lauf bewusst auf den freigegebenen Batch gesetzt werden.
// Kein automatisches "juengsten PREPARED-Batch nehmen": das waere nicht fail-closed.
var ACTIVE_BATCH_PROP = 'HSB_ACTIVE_BATCH_ID';
var EXPECTED_FLYER_SHA256 = {
  JORDI: 'e0aa76c1ffec5cf89289e6ab141691d42ea81ffd13db2f08f045342531f39acc'
};

// Spalten im Sheet, in die zurueckgeschrieben wird.
var WRITEBACK = {
  draftId: 'Draft_ID',
  internetMessageId: 'Internet_Message_ID',
  conversationId: 'Conversation_ID',
  draftedAt: 'Drafted_At',
  batchStatus: 'Batch_Status',
  sendStatus: 'Send_Status',
  lastError: 'Last_Error'
};

// Engine-Funktionen, auf die dieser Adapter angewiesen ist.
var REQUIRED_ENGINE_FUNCTIONS = ['readLeads_', 'getVerifiedFlyer_', 'renderEmail_', 'logActivity_'];

var HTTP_TIMEOUT_SECONDS = 60;

// ---------------------------------------------------------------- Preflight

/**
 * Prueft die Voraussetzungen, ohne irgendetwas zu veraendern.
 * Vor dem ersten echten Lauf ausfuehren und die Ausgabe lesen.
 */
function preflight() {
  var report = [];
  var ok = true;

  REQUIRED_ENGINE_FUNCTIONS.forEach(function (name) {
    var exists = (typeof this[name] === 'function') ||
                 (typeof globalThis[name] === 'function');
    report.push((exists ? 'OK   ' : 'FEHLT') + '  Engine-Funktion ' + name);
    if (!exists) ok = false;
  }, this);

  var props = PropertiesService.getScriptProperties();
  Object.keys(ADAPTER_PROPS).forEach(function (owner) {
    var key = ADAPTER_PROPS[owner];
    var url = props.getProperty(key);
    var good = !!url && url.indexOf('https://') === 0;
    report.push((good ? 'OK   ' : 'FEHLT') + '  Skripteigenschaft ' + key);
    if (!good) ok = false;
  });

  var activeBatch = props.getProperty(ACTIVE_BATCH_PROP);
  var activeBatchGood = !!activeBatch && /^HSB-[A-Z0-9-]+$/.test(activeBatch);
  report.push(
    (activeBatchGood ? 'OK   ' : 'FEHLT') + '  Skripteigenschaft ' +
    ACTIVE_BATCH_PROP + (activeBatchGood ? ' = ' + activeBatch : '')
  );
  if (!activeBatchGood) ok = false;

  report.push('');
  report.push(ok ? 'PREFLIGHT=PASS' : 'PREFLIGHT=FAIL — nichts ausfuehren, bis alle Zeilen OK sind.');
  var text = report.join('\n');
  Logger.log(text);
  return text;
}

// ---------------------------------------------------------------- Hilfen

/** Klartext aus renderEmail_ in HTML wandeln. Der Outlook-Connector erwartet HTML. */
function textToHtml_(text) {
  var escaped = String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return escaped
    .split(/\n{2,}/)
    .map(function (para) { return '<p>' + para.replace(/\n/g, '<br>') + '</p>'; })
    .join('');
}

/** Flyer als base64 fuer den Connector. Nutzt die Engine-Verifikation, kein eigener Pfad. */
function flyerAttachment_(owner) {
  var flyer = getVerifiedFlyer_(owner);
  if (!flyer) throw new Error('ASSET_GATE_FAIL: kein verifizierter Flyer fuer ' + owner);
  var blob = flyer.blob || DriveApp.getFileById(flyer.fileId).getBlob();
  return {
    Name: blob.getName(),
    ContentBytes: Utilities.base64Encode(blob.getBytes())
  };
}

function sha256Hex_(bytes) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes)
    .map(function (value) {
      return ((value + 256) % 256).toString(16).padStart(2, '0');
    })
    .join('');
}

/**
 * Read-only Asset-Gate. Erzeugt keinen Entwurf und schreibt nichts ins Sheet.
 * Vor entwurfTesten() ausfuehren und nur bei ASSET_GATE=PASS fortfahren.
 */
function flyerPruefen(owner) {
  var key = String(owner || 'JORDI').toUpperCase().indexOf('JORDI') >= 0 ? 'JORDI' : 'JOEL';
  var expected = EXPECTED_FLYER_SHA256[key];
  if (!expected) throw new Error('ASSET_GATE_FAIL: kein Soll-Hash fuer ' + key);

  var flyer = getVerifiedFlyer_(key);
  if (!flyer) throw new Error('ASSET_GATE_FAIL: kein Flyer fuer ' + key);
  var blob = flyer.blob || DriveApp.getFileById(flyer.fileId).getBlob();
  var bytes = blob.getBytes();
  var actual = sha256Hex_(bytes);
  var report = [
    'OWNER=' + key,
    'NAME=' + blob.getName(),
    'BYTES=' + bytes.length,
    'SHA256=' + actual,
    actual === expected ? 'ASSET_GATE=PASS' : 'ASSET_GATE=FAIL'
  ].join('\n');
  Logger.log(report);
  if (actual !== expected) {
    throw new Error('ASSET_GATE_FAIL: erwartet ' + expected + ', erhalten ' + actual);
  }
  return report;
}

function adapterUrlFor_(owner) {
  var key = ADAPTER_PROPS[String(owner).toUpperCase().indexOf('JORDI') >= 0 ? 'JORDI' : 'JOEL'];
  var url = PropertiesService.getScriptProperties().getProperty(key);
  if (!url) throw new Error('Skripteigenschaft ' + key + ' ist nicht gesetzt.');
  return url;
}

// ---------------------------------------------------------------- Kern

/**
 * Erzeugt Entwuerfe fuer einen vorbereiteten Batch.
 *
 * @param {string} batchId    Batch aus dem Sheet (PREPARED).
 * @param {Object} options    {limit: number, dryRun: boolean}
 *
 * Idempotenz: Leads mit Draft_ID werden uebersprungen. Ein Transportfehler ist
 * grundsaetzlich mehrdeutig: Er wird in Last_Error geschrieben und blockiert
 * jeden weiteren Versuch, bis ein Mensch den Outlook-Entwurfsordner geprueft
 * und den Fehler bewusst geklaert hat.
 */
function createDraftsForBatch(batchId, options) {
  options = options || {};
  var limit = options.limit || 1;              // bewusst 1 als Default
  var dryRun = options.dryRun === true;

  var pre = preflight();
  if (pre.indexOf('PREFLIGHT=PASS') < 0) throw new Error(pre);

  var leads = readLeads_({ batchId: batchId });
  if (!leads || !leads.length) {
    return 'Keine Leads im Batch ' + batchId + '. Das ist bei geschlossenem Gate korrektes Verhalten.';
  }

  var results = { attempted: 0, drafted: 0, skipped: 0, failed: 0, details: [] };

  for (var i = 0; i < leads.length && results.attempted < limit; i++) {
    var lead = leads[i];

    if (lead[WRITEBACK.draftId]) {
      results.skipped++;
      results.details.push(lead.Lead_ID + ' uebersprungen (Draft_ID vorhanden)');
      continue;
    }

    if (lead[WRITEBACK.lastError]) {
      throw new Error(
        'UNGEKLAERTER_VORFEHLER: ' + lead.Lead_ID + ' ' + lead[WRITEBACK.lastError] +
        '. Zuerst Outlook pruefen und den Fehler bewusst klaeren; kein automatischer Retry.'
      );
    }

    // "limit" begrenzt Netzwerkversuche, nicht nur erfolgreiche Antworten.
    // Damit macht entwurfTesten() unter allen Fehlerbedingungen hoechstens
    // einen einzigen Power-Automate-Aufruf.
    results.attempted++;

    var owner = lead.Verantwortlicher || lead.Owner;
    var rendered = renderEmail_(lead);          // Klartext aus der Engine
    var payload = {
      leadId: lead.Lead_ID,
      batchId: batchId,
      to: lead['E-Mail'] || lead.Email,
      subject: rendered.subject,
      bodyHtml: textToHtml_(rendered.body),
      attachments: [flyerAttachment_(owner)]
    };

    if (dryRun) {
      results.details.push(lead.Lead_ID + ' DRY-RUN, kein Aufruf');
      results.drafted++;
      continue;
    }

    var res;
    try {
      res = UrlFetchApp.fetch(adapterUrlFor_(owner), {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify(payload),
        timeoutSeconds: HTTP_TIMEOUT_SECONDS,
        muteHttpExceptions: true
      });
    } catch (transportError) {
      var transportMessage = 'TRANSPORT_UNKLAR: ' + String(transportError);
      writeBackError_(lead, transportMessage);
      logActivity_('DRAFT_FAILED', lead.Lead_ID, transportMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + transportMessage);
    }

    var code = res.getResponseCode();
    if (code !== 200) {
      results.failed++;
      var httpMessage = 'HTTP ' + code + ' ' + res.getContentText().slice(0, 200);
      writeBackError_(lead, httpMessage);
      logActivity_('DRAFT_FAILED', lead.Lead_ID, httpMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + httpMessage);
    }

    var body;
    try {
      body = JSON.parse(res.getContentText());
    } catch (parseError) {
      writeBackError_(lead, 'INVALID_RESPONSE_JSON');
      logActivity_('DRAFT_FAILED', lead.Lead_ID, 'INVALID_RESPONSE_JSON');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' INVALID_RESPONSE_JSON');
    }
    if (!body || !body.draftId) {
      writeBackError_(lead, 'MISSING_DRAFT_ID');
      logActivity_('DRAFT_FAILED', lead.Lead_ID, 'MISSING_DRAFT_ID');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' MISSING_DRAFT_ID');
    }
    writeBackDraft_(lead, body);
    logActivity_('DRAFTED', lead.Lead_ID, body.draftId);
    results.drafted++;
    results.details.push(lead.Lead_ID + ' DRAFTED ' + body.draftId);
  }

  var summary = 'Batch ' + batchId + ': ' + results.drafted + ' Entwuerfe, ' +
                results.skipped + ' uebersprungen, ' + results.failed + ' Fehler\n' +
                results.details.join('\n') +
                '\n\nSENT wird nicht gesetzt. Versand erfolgt manuell in Outlook.';
  Logger.log(summary);
  return summary;
}

/** Schreibt die Korrelations-IDs zurueck. Setzt niemals SENT. */
function writeBackDraft_(lead, body) {
  var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = lead._row;
  if (!row) throw new Error('Lead ohne Zeilenreferenz (_row): ' + lead.Lead_ID);

  var set = {};
  set[WRITEBACK.draftId] = body.draftId;
  set[WRITEBACK.internetMessageId] = body.internetMessageId;
  set[WRITEBACK.conversationId] = body.conversationId;
  set[WRITEBACK.draftedAt] = new Date();
  set[WRITEBACK.batchStatus] = 'DRAFTED';
  set[WRITEBACK.sendStatus] = 'drafted';
  set[WRITEBACK.lastError] = '';

  Object.keys(set).forEach(function (col) {
    if (headers.indexOf(col) < 0) throw new Error('Spalte fehlt im Sheet: ' + col);
  });
  Object.keys(set).forEach(function (col) {
    var idx = headers.indexOf(col);
    sheet.getRange(row, idx + 1).setValue(set[col]);
  });
}

/** Schreibt einen Fehler fail-closed zurueck. Kein automatischer Retry. */
function writeBackError_(lead, message) {
  var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = lead._row;
  if (!row) throw new Error('Lead ohne Zeilenreferenz (_row): ' + lead.Lead_ID);
  var idx = headers.indexOf(WRITEBACK.lastError);
  if (idx < 0) throw new Error('Spalte fehlt im Sheet: ' + WRITEBACK.lastError);
  sheet.getRange(row, idx + 1).setValue(String(message).slice(0, 500));
}

// ---------------------------------------------------------------- Bedienung

/** Ein einzelner Entwurf zum Pruefen. Immer damit anfangen. */
function entwurfTesten() {
  var batch = aktivenBatchFinden_();
  return createDraftsForBatch(batch, { limit: 1 });
}

/** Alle Entwuerfe des offenen Batches. Erst nach Sichtung des Testentwurfs. */
function entwuerfeErzeugen() {
  var batch = aktivenBatchFinden_();
  return createDraftsForBatch(batch, { limit: 9999 });
}

/** Verifiziert den explizit konfigurierten Batch und nimmt nie automatisch einen anderen. */
function aktivenBatchFinden_() {
  var batchId = PropertiesService.getScriptProperties().getProperty(ACTIVE_BATCH_PROP);
  if (!batchId) {
    throw new Error('Skripteigenschaft ' + ACTIVE_BATCH_PROP + ' fehlt. Kein Batch wird automatisch gewaehlt.');
  }
  var sheet = SpreadsheetApp.getActive().getSheetByName('BATCHES');
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idBatch = headers.indexOf('Batch');
  var idStatus = headers.indexOf('Status');
  if (idBatch < 0 || idStatus < 0) throw new Error('BATCHES: Spalten Batch/Status nicht gefunden.');
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idBatch]) !== String(batchId)) continue;
    if (String(data[i][idStatus]).toUpperCase() !== 'PREPARED') {
      throw new Error('Aktiver Batch ' + batchId + ' ist nicht PREPARED. Abbruch.');
    }
    return batchId;
  }
  throw new Error('Aktiver Batch ' + batchId + ' wurde in BATCHES nicht gefunden. Abbruch.');
}