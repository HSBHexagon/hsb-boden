/**
 * HSB Sales OS — Draft-Adapter (Apps Script -> Power Automate -> Outlook-Entwurf)
 *
 * Vertrag:
 *   - Google Sheet = SSOT. Apps Script entscheidet Eligibility, Owner,
 *     Legal_Basis, Template und Flyer. Power Automate entscheidet NICHTS.
 *   - Power Automate erzeugt ausschliesslich ENTWUERFE. Kein Auto-Send.
 *   - PREPARED != DRAFTED != SENT. Dieses Skript setzt NIEMALS SENT.
 */

// ---------------------------------------------------------------- Konfiguration

var ADAPTER_PROPS = {
  JORDI: 'HSB_ADAPTER_URL_JORDI',
  JOEL: 'HSB_ADAPTER_URL_JOEL'
};

var ACTIVE_BATCH_PROP = 'HSB_ACTIVE_BATCH_ID';
var EXPECTED_FLYER_SHA256 = {
  JORDI: 'f343ff05d1e7353a3a91a60f5475c054e1af958ea72e466445e60b9f69059a21',
  JOEL:  '2bccadacc77b531057583d2d650963c30deceed36c8be1fd90ca64e8b8cde5fb'
};

var WRITEBACK = {
  draftId: 'Draft_ID',
  internetMessageId: 'Internet_Message_ID',
  conversationId: 'Conversation_ID',
  draftedAt: 'Drafted_At',
  batchStatus: 'Batch_Status',
  sendStatus: 'Send_Status',
  lastError: 'Last_Error'
};

var REQUIRED_ENGINE_FUNCTIONS = ['readLeads_', 'getVerifiedFlyer_', 'renderEmail_', 'logActivity_'];
var HTTP_TIMEOUT_SECONDS = 60;

// ---------------------------------------------------------------- Preflight

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
    var raw = props.getProperty(key);
    var url = raw ? String(raw).trim() : '';
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

/**
 * Pflichtangaben nach §35a GmbHG. Quelle: hsb-boden.de/impressum (2026-09-07).
 * Ohne diese Angaben ist eine Geschaefts-E-Mail formal angreifbar.
 */
var FIRMA = {
  name: 'HSB Hexagon Säurebau GmbH',
  strasse: 'Benzstraße 6',
  plzOrt: '48599 Gronau',
  telefon: '+49 (0)2562 9463030',
  web: 'www.hsb-boden.de',
  sitz: 'Gronau',
  registergericht: 'Amtsgericht Coesfeld',
  hrb: 'HRB 21481',
  geschaeftsfuehrer: 'Jordi Post'
};

function htmlEscape_(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Signatur als HTML. Bewusst ohne externe Bilder: Outlook blockiert extern
 * geladene Logos standardmaessig und sie erhoehen die Spam-Bewertung.
 * Inline-Styles, weil Outlook Desktop CSS im <head> weitgehend ignoriert.
 */
function signaturHtml_(ownerDisplay, mailbox, mobile) {
  var mobilZeile = mobile ? ('Mobil ' + htmlEscape_(mobile) + '<br>') : '';
  return '<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;'
    + 'font-size:10pt;color:#222222;line-height:1.45;">'
    + '<strong>' + htmlEscape_(ownerDisplay) + '</strong><br>'
    + htmlEscape_(FIRMA.name) + '<br>'
    + htmlEscape_(FIRMA.strasse) + ' &middot; ' + htmlEscape_(FIRMA.plzOrt) + '<br>'
    + mobilZeile
    + 'Tel. ' + htmlEscape_(FIRMA.telefon) + '<br>'
    + '<a href="mailto:' + htmlEscape_(mailbox) + '" style="color:#1155cc;">'
    + htmlEscape_(mailbox) + '</a> &middot; '
    + '<a href="https://' + FIRMA.web + '" style="color:#1155cc;">' + FIRMA.web + '</a>'
    + '</p>'
    + '<p style="margin:10px 0 0 0;font-family:Arial,Helvetica,sans-serif;'
    + 'font-size:8pt;color:#777777;line-height:1.4;">'
    + 'Sitz der Gesellschaft: ' + htmlEscape_(FIRMA.sitz) + ' &middot; '
    + htmlEscape_(FIRMA.registergericht) + ' ' + htmlEscape_(FIRMA.hrb) + ' &middot; '
    + 'Geschäftsführer: ' + htmlEscape_(FIRMA.geschaeftsfuehrer)
    + '</p>';
}

/**
 * HTML-Body: derselbe Text wie renderEmail_(), aber der Klartext-Signaturteil
 * wird abgeschnitten und durch signaturHtml_ ersetzt, damit dieselbe
 * Information nicht doppelt erscheint. Der Abmelde-Hinweis bleibt erhalten -
 * er dokumentiert die Widerspruchsmoeglichkeit nach §7 UWG.
 */
function bodyHtmlMitSignatur_(mail, flyer) {
  var marker = 'Mit freundlichen Grüßen';
  var teile = String(mail.body).split(marker);
  var haupttext = teile[0];
  var rest = teile.length > 1 ? teile[1] : '';
  var abmelde = rest.indexOf('---') >= 0 ? rest.split('---')[1].trim() : '';

  var absaetze = haupttext.trim().split(/\n{2,}/).map(function (p) {
    return '<p style="margin:0 0 12px 0;">'
      + htmlEscape_(p).replace(/\n/g, '<br>') + '</p>';
  }).join('');

  return '<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;'
    + 'color:#222222;line-height:1.5;">'
    + absaetze
    + '<p style="margin:0 0 4px 0;">' + marker + '</p>'
    + signaturHtml_(flyer.displayName, flyer.mailbox, flyer.mobile)
    + '<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;'
    + 'font-size:8pt;color:#999999;">' + htmlEscape_(abmelde) + '</p>'
    + '</div>';
}

function flyerFelderFuer_(key, owner) {
  var verified = getVerifiedFlyer_(owner);
  if (!verified) throw new Error('ASSET_GATE_FAIL: kein verifizierter Flyer fuer ' + owner);
  var blob = verified.blob || DriveApp.getFileById(verified.fileId).getBlob();

  var felder = {
    // Empfaengersichtbarer Name, nicht der interne Dateiname.
    attachmentName: (FLYERS[key] && FLYERS[key].attachmentName) || blob.getName(),
    attachmentContentBytes: Utilities.base64Encode(blob.getBytes())
  };
  felder._flyer = verified.flyer;
  return felder;
}

function sha256Hex_(bytes) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes)
    .map(function (value) {
      return ((value + 256) % 256).toString(16).padStart(2, '0');
    })
    .join('');
}

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
  var raw = PropertiesService.getScriptProperties().getProperty(key);
  if (!raw) throw new Error('Skripteigenschaft ' + key + ' ist nicht gesetzt.');
  var url = String(raw).trim();
  if (url.indexOf('https://') !== 0) {
    throw new Error('Skripteigenschaft ' + key + ' ist keine gueltige HTTPS-URL.');
  }
  return url;
}

// ---------------------------------------------------------------- Kern

function createDraftsForBatch(batchId, options) {
  options = options || {};
  var limit = options.limit || 1;
  var dryRun = options.dryRun === true;

  var pre = preflight();
  if (pre.indexOf('PREFLIGHT=PASS') < 0) throw new Error(pre);

  var allLeads = (readLeads_().leads) || [];
  var leads = allLeads.filter(function (l) { return String(l.Batch_ID) === String(batchId); });
  if (!leads.length) {
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

    results.attempted++;

    var owner = lead.Owner;
    var ownerKey = String(owner).toUpperCase().indexOf('JOEL') >= 0 ? 'JOEL' : 'JORDI';
    var flyerFelder = flyerFelderFuer_(ownerKey, owner);
    var rendered = renderEmail_(lead, flyerFelder._flyer);
    var payload = {
      leadId: lead.Lead_ID,
      batchId: batchId,
      owner: ownerKey,
      to: lead.Email,
      subject: rendered.subject,
      bodyHtml: bodyHtmlMitSignatur_(rendered, flyerFelder._flyer)
    };
    Object.keys(flyerFelder).forEach(function (k) {
      if (k !== '_flyer') payload[k] = flyerFelder[k];
    });

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
      logActivity_(lead.Lead_ID, 'DRAFT_FAILED', transportMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + transportMessage);
    }

    var code = res.getResponseCode();
    if (code !== 200) {
      results.failed++;
      var httpMessage = 'HTTP ' + code + ' ' + res.getContentText().slice(0, 200);
      writeBackError_(lead, httpMessage);
      logActivity_(lead.Lead_ID, 'DRAFT_FAILED', httpMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + httpMessage);
    }

    var body;
    try {
      body = JSON.parse(res.getContentText());
    } catch (parseError) {
      writeBackError_(lead, 'INVALID_RESPONSE_JSON');
      logActivity_(lead.Lead_ID, 'DRAFT_FAILED', 'INVALID_RESPONSE_JSON');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' INVALID_RESPONSE_JSON');
    }
    if (!body || !body.draftId) {
      writeBackError_(lead, 'MISSING_DRAFT_ID');
      logActivity_(lead.Lead_ID, 'DRAFT_FAILED', 'MISSING_DRAFT_ID');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' MISSING_DRAFT_ID');
    }
    writeBackDraft_(lead, body);
    logActivity_(lead.Lead_ID, 'DRAFTED', body.draftId);
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

function entwurfTesten() {
  var batch = aktivenBatchFinden_();
  return createDraftsForBatch(batch, { limit: 1 });
}

function entwuerfeErzeugen() {
  var batch = aktivenBatchFinden_();
  return createDraftsForBatch(batch, { limit: 9999 });
}

function uiCreateDraftsForBatch(batchId, limit) {
  try {
    if (!batchId) throw new Error('Kein Batch angegeben.');
    var n = parseInt(limit, 10);
    if (!n || n < 1) n = 9999;
    var summary = createDraftsForBatch(String(batchId), { limit: n });
    return { ok: true, data: { summary: summary } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function aktivenBatchFinden_() {
  var batchId = PropertiesService.getScriptProperties().getProperty(ACTIVE_BATCH_PROP);
  if (!batchId) {
    throw new Error('Skripteigenschaft ' + ACTIVE_BATCH_PROP + ' fehlt. Kein Batch wird automatisch gewaehlt.');
  }
  var sheet = SpreadsheetApp.getActive().getSheetByName('BATCHES');
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idBatch = headers.indexOf('Batch_ID');
  var idStatus = headers.indexOf('Status');
  if (idBatch < 0 || idStatus < 0) throw new Error('BATCHES: Spalten Batch_ID/Status nicht gefunden.');
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idBatch]) !== String(batchId)) continue;
    if (String(data[i][idStatus]).toUpperCase() !== 'PREPARED') {
      throw new Error('Aktiver Batch ' + batchId + ' ist nicht PREPARED. Abbruch.');
    }
    return batchId;
  }
  throw new Error('Aktiver Batch ' + batchId + ' wurde in BATCHES nicht gefunden. Abbruch.');
}
