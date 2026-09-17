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
  JORDI: '08e1149e4fed409ac94d5af18139c36d00027a7a7b53e49928beb429d4a12729',
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

/**
 * Vollstaendiger Lagebericht fuer Menschen. Prueft alles, blockiert nichts.
 *
 * Bewusst getrennt von preflightHart_(): frueher hat diese Funktion den
 * gesamten Entwurfslauf abgebrochen, sobald IRGENDEINE der drei
 * Skripteigenschaften fehlte. Damit sperrte eine fehlende Jordi-URL auch
 * Joels Weg, obwohl dessen Adapter vollstaendig eingerichtet war. Eine
 * Voraussetzung darf nur den blockieren, der sie tatsaechlich braucht.
 */
function preflight() {
  var report = [];

  REQUIRED_ENGINE_FUNCTIONS.forEach(function (name) {
    var exists = (typeof this[name] === 'function') ||
                 (typeof globalThis[name] === 'function');
    report.push((exists ? 'OK   ' : 'FEHLT') + '  Engine-Funktion ' + name);
  }, this);

  var props = PropertiesService.getScriptProperties();
  Object.keys(ADAPTER_PROPS).forEach(function (owner) {
    var key = ADAPTER_PROPS[owner];
    var raw = props.getProperty(key);
    var url = raw ? String(raw).trim() : '';
    var good = !!url && url.indexOf('https://') === 0;
    report.push(
      (good ? 'OK   ' : 'FEHLT') + '  Skripteigenschaft ' + key +
      (good ? '  (' + url.slice(0, 60) + '…)' : '  — ' + owner +
        ' kann ohne diese URL keine Entwuerfe erzeugen')
    );
  });

  var activeBatch = props.getProperty(ACTIVE_BATCH_PROP);
  var activeBatchGood = !!activeBatch && /^HSB-[A-Z0-9-]+$/.test(activeBatch);
  report.push(
    (activeBatchGood ? 'OK   ' : 'OFFEN') + '  Skripteigenschaft ' +
    ACTIVE_BATCH_PROP +
    (activeBatchGood ? ' = ' + activeBatch
                     : ' — nur fuer die Menuepunkte noetig, nicht fuer die Seitenleiste')
  );

  report.push('');
  report.push('Die Seitenleiste braucht je Kontakt nur die Adapter-URL '
    + 'seines Verantwortlichen. Fehlt eine, scheitert genau dieser Kontakt.');
  var text = report.join('\n');
  Logger.log(text);
  return text;
}

/**
 * Harte Voraussetzung fuer jeden Entwurfslauf: die Engine-Funktionen selbst.
 * Ohne sie gibt es weder Leads noch Flyer noch Text - das ist ein Deploy-
 * Fehler und kein Konfigurationsthema.
 */
function preflightHart_() {
  var fehlend = REQUIRED_ENGINE_FUNCTIONS.filter(function (name) {
    return typeof this[name] !== 'function' &&
           typeof globalThis[name] !== 'function';
  }, this);
  if (fehlend.length) {
    throw new Error(
      'DEPLOY_UNVOLLSTAENDIG: Engine-Funktionen fehlen: ' + fehlend.join(', ') +
      '. Das Skript wurde nicht vollstaendig hochgeladen.'
    );
  }
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
  geschaeftsfuehrer: 'Jordie Post'
};

function htmlEscape_(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Signatur als HTML mit offiziellem HSB Firmenlogo und §35a GmbHG Pflichtangaben.
 * Inline-Styles, weil Outlook Desktop CSS im <head> weitgehend ignoriert.
 */
function signaturHtml_(ownerDisplay, mailbox, mobile) {
  var mobilZeile = mobile ? ('Mobil ' + htmlEscape_(mobile) + '<br>') : '';
  var ownerSlug = encodeURIComponent(String(ownerDisplay || 'team').toLowerCase().replace(/\s+/g, '_'));
  var webUrlMitUtm = 'https://' + FIRMA.web + '/?utm_source=outreach&utm_medium=email&utm_campaign=kaltakquise_2026_q3&utm_term=' + ownerSlug + '&utm_content=signatur';
  return '<p style="margin:16px 0 0 0;font-family:Arial,Helvetica,sans-serif;'
    + 'font-size:10pt;color:#222222;line-height:1.45;">'
    + '<strong>' + htmlEscape_(ownerDisplay) + '</strong><br>'
    + htmlEscape_(FIRMA.name) + '<br>'
    + htmlEscape_(FIRMA.strasse) + ' &middot; ' + htmlEscape_(FIRMA.plzOrt) + '<br>'
    + mobilZeile
    + 'Tel. ' + htmlEscape_(FIRMA.telefon) + '<br>'
    + '<a href="mailto:' + htmlEscape_(mailbox) + '" style="color:#1155cc;">'
    + htmlEscape_(mailbox) + '</a> &middot; '
    + '<a href="' + webUrlMitUtm + '" style="color:#1155cc;">' + FIRMA.web + '</a>'
    + '</p>'
    + '<p style="margin:12px 0 0 0;">'
    + '<a href="' + webUrlMitUtm + '" target="_blank" style="text-decoration:none;">'
    + '<img src="https://' + FIRMA.web + '/brand/hsb-boden-logo.png" '
    + 'alt="' + htmlEscape_(FIRMA.name) + '" '
    + 'width="102" height="75" '
    + 'style="display:block;border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;width:102px;height:75px;max-width:102px;max-height:75px;" />'
    + '</a>'
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
  var bytes = blob.getBytes();

  var felder = {
    // Empfaengersichtbarer Name, nicht der interne Dateiname.
    attachmentName: (FLYERS[key] && FLYERS[key].attachmentName) || blob.getName(),
    attachmentContentBytes: Utilities.base64Encode(bytes)
  };
  felder._flyer = verified.flyer;
  // Sollgroesse fuer den Rueckvergleich mit dem, was Outlook wirklich
  // gespeichert hat. Ohne diese Zahl waere die Anhangpruefung blind.
  felder._byteLength = bytes.length;
  return felder;
}

/**
 * Flyer je Verantwortlichem genau einmal pro Lauf holen und kodieren.
 *
 * Vorher lag das im Lead-Loop: pro Kontakt ein Drive-Download plus eine
 * Base64-Kodierung von 1,5 MB. Bei zehn Kontakten je Block sind das zehn
 * identische Kodierungen gegen das Sechs-Minuten-Limit von Apps Script.
 */
function flyerCacheHolen_(cache, key, owner) {
  if (!cache[key]) cache[key] = flyerFelderFuer_(key, owner);
  return cache[key];
}

// Outlook zaehlt beim gespeicherten Anhang MIME-Overhead mit. Gemessen am
// 2026-09-07 ueber 50 reale Entwuerfe: konstant 292 Bytes ueber der Quelle.
var ANHANG_TOLERANZ_BYTES = 1000;

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
  if (typeof ensureScriptPropsSeed_ === 'function') {
    ensureScriptPropsSeed_();
  }
  var key = ADAPTER_PROPS[String(owner).toUpperCase().indexOf('JORDI') >= 0 ? 'JORDI' : 'JOEL'];
  var raw = PropertiesService.getScriptProperties().getProperty(key);
  if (!raw) {
    throw new Error('Skripteigenschaft ' + key + ' ist nicht gesetzt. Bitte im Menü "HSB Sales OS -> 🔗 Adapter-URL setzen" konfigurieren.');
  }
  var url = String(raw).trim();
  if (url.indexOf('https://') !== 0) {
    throw new Error('Skripteigenschaft ' + key + ' ist keine gueltige HTTPS-URL.');
  }
  return url;
}

/**
 * Legt einen Entwurf an - ueber Graph, wenn dieses Konto verbunden ist,
 * sonst ueber Power Automate.
 *
 * Beide Wege liefern dasselbe Antwortformat. Die Anhangpruefung im Aufrufer
 * kennt den Transportweg deshalb nicht und muss ihn nicht kennen.
 *
 * Reihenfolge bewusst so: Graph ist der Weg, der ohne Lizenz auskommt und
 * jeder Person ihr eigenes Postfach zuordnet. Power Automate bleibt nur als
 * Rueckfallebene fuer Joel, dessen Flow noch aus Bestandsschutz laeuft.
 */
function entwurfAnlegen_(owner, ownerKey, payload) {
  // Jordis Flow hat einen Button-Trigger und ist deshalb NUR ueber den
  // Logic-Flows-Connector erreichbar - seine Aufruf-URL ist von Microsoft
  // gesperrt. Das ist derselbe Weg, der am 2026-09-07 real 50 Entwuerfe
  // erzeugt hat, nur dass das Token nicht mehr von `az login` kommt,
  // sondern von der einmaligen Anmeldung im Sheet-Menue.
  if (typeof fcBrauchtConnector_ === 'function' && fcBrauchtConnector_(ownerKey)) {
    return fcEntwurfErzeugen_(payload, ownerKey);
  }

  // Graph braucht eine Administratorzustimmung, die im HSB-Tenant bisher
  // fehlt. Bleibt als Weg bestehen, falls sie je erteilt wird.
  if (typeof graphVerbunden_ === 'function' && graphVerbunden_()) {
    return graphEntwurfErzeugen_(payload, ownerKey);
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
    throw new Error('TRANSPORT_UNKLAR: ' + String(transportError));
  }

  var code = res.getResponseCode();
  if (code !== 200) {
    throw new Error('HTTP ' + code + ' ' + res.getContentText().slice(0, 200));
  }
  try {
    return JSON.parse(res.getContentText());
  } catch (parseError) {
    throw new Error('INVALID_RESPONSE_JSON');
  }
}

// ---------------------------------------------------------------- Kern

function createDraftsForBatch(batchId, options) {
  options = options || {};
  var limit = options.limit || 1;
  var dryRun = options.dryRun === true;

  if (typeof ensureScriptPropsSeed_ === 'function') {
    ensureScriptPropsSeed_();
  }
  preflightHart_();

  var allLeads = (readLeads_().leads) || [];
  var leads = allLeads.filter(function (l) { return String(l.Batch_ID) === String(batchId); });
  if (!leads.length) {
    return 'Keine Leads im Batch ' + batchId + '. Das ist bei geschlossenem Gate korrektes Verhalten.';
  }

  // "async" wird getrennt gezaehlt: diese Entwuerfe entstehen real, sind aber
  // von Apps Script aus nicht nachgeprueft. Sie unter "drafted" zu fuehren
  // wuerde die Zusammenfassung zu gut aussehen lassen.
  var results = { attempted: 0, drafted: 0, async: 0, skipped: 0, failed: 0,
                  details: [] };
  var flyerCache = {};

  for (var i = 0; i < leads.length && results.attempted < limit; i++) {
    var lead = leads[i];

    if (lead[WRITEBACK.draftId]) {
      results.skipped++;
      results.details.push(lead.Lead_ID + ' uebersprungen (Draft_ID vorhanden)');
      continue;
    }

    if (lead[WRITEBACK.lastError]) {
      Logger.log('Vorfehler bei Lead ' + lead.Lead_ID + ': ' + lead[WRITEBACK.lastError] + ' — erneuter Versuch');
    }

    results.attempted++;

    var owner = lead.Owner;
    var ownerKey = String(owner).toUpperCase().indexOf('JOEL') >= 0 ? 'JOEL' : 'JORDI';
    var flyerFelder = flyerCacheHolen_(flyerCache, ownerKey, owner);
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
      if (k.charAt(0) !== '_') payload[k] = flyerFelder[k];
    });

    if (dryRun) {
      results.details.push(lead.Lead_ID + ' DRY-RUN, kein Aufruf');
      results.drafted++;
      continue;
    }

    var body;
    try {
      body = entwurfAnlegen_(owner, ownerKey, payload);
    } catch (transportError) {
      results.failed++;
      var transportMessage = String(transportError).slice(0, 300);
      writeBackError_(lead, transportMessage);
      logActivity_(lead.Lead_ID, 'DRAFT_FAILED', transportMessage);
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' ' + transportMessage);
    }
    // Asynchroner Weg (Jordi): der Flow bestaetigt nur die Annahme. Der
    // Entwurf entsteht in seinem Postfach, aber Apps Script sieht weder
    // Draft-ID noch Anhanggroesse und darf ihn deshalb nicht als geprueft
    // ausweisen. Der Batch laeuft weiter - ein Abbruch waere hier falsch,
    // weil nichts fehlgeschlagen ist.
    if (body && body.async) {
      var asyncHinweis = 'ASYNCHRON: Flow-Lauf ' + body.runId + ' angenommen. ' +
        'Der Entwurf entsteht im Postfach von ' + ownerKey + ', Apps Script ' +
        'bekommt vom Flow keine Rueckmeldung. Anhang ungeprueft - vor dem ' +
        'Versand in Outlook sichten.';
      writeBackDraft_(lead, body, asyncHinweis);
      logActivity_(lead.Lead_ID, 'DRAFT_ASYNC', asyncHinweis);
      results.async++;
      results.details.push(lead.Lead_ID + ' ANGENOMMEN (Lauf ' + body.runId + ')');
      continue;
    }

    if (!body || !body.draftId) {
      writeBackError_(lead, 'MISSING_DRAFT_ID');
      logActivity_(lead.Lead_ID, 'DRAFT_FAILED', 'MISSING_DRAFT_ID');
      throw new Error('DRAFT_FAILED: ' + lead.Lead_ID + ' MISSING_DRAFT_ID');
    }

    // Anhangpruefung. Der Flow liest den erzeugten Entwurf zurueck und meldet
    // die Groesse, die Outlook wirklich gespeichert hat. Genau hier ist der
    // Fehler jahrelang durchgerutscht: eine Antwort mit draftId galt als
    // Erfolg, obwohl der Flyer doppelt kodiert und damit unlesbar war.
    var soll = flyerFelder._byteLength;
    var ist = body.attachmentSize;
    var anhangOk = (typeof ist === 'number') &&
                   Math.abs(ist - soll) <= ANHANG_TOLERANZ_BYTES;

    if (!anhangOk) {
      // Draft_ID trotzdem schreiben: der Entwurf liegt real im Postfach.
      // Ohne Eintrag waere er verwaist und ein Folgelauf erzeugte ein Duplikat.
      var anhangFehler = 'ANHANG_UNGEPRUEFT: Soll ' + soll + ' Bytes, gemeldet ' +
        (ist === undefined || ist === null ? 'nichts' : ist) +
        (body.verifyError ? ' (' + String(body.verifyError).slice(0, 120) + ')' : '') +
        '. Entwurf ' + body.draftId + ' liegt im Postfach und ist von Hand zu pruefen.';
      writeBackDraft_(lead, body, anhangFehler);
      logActivity_(lead.Lead_ID, 'DRAFT_UNVERIFIED', anhangFehler);
      results.failed++;
      throw new Error('ANHANG_FEHLER: ' + lead.Lead_ID + ' ' + anhangFehler);
    }

    writeBackDraft_(lead, body, '');
    logActivity_(lead.Lead_ID, 'DRAFTED', body.draftId);
    results.drafted++;
    results.details.push(lead.Lead_ID + ' DRAFTED ' + body.draftId +
                          ' (Anhang ' + ist + ' Bytes)');
  }

  var summary = 'Batch ' + batchId + ': ' + results.drafted + ' Entwuerfe, ' +
                results.async + ' angenommen (ungeprueft), ' +
                results.skipped + ' uebersprungen, ' + results.failed + ' Fehler\n' +
                results.details.join('\n') +
                '\n\nSENT wird nicht gesetzt. Versand erfolgt manuell in Outlook.';
  Logger.log(summary);
  return summary;
}

function writeBackDraft_(lead, body, warnung) {
  var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = lead._row;
  if (!row) throw new Error('Lead ohne Zeilenreferenz (_row): ' + lead.Lead_ID);

  var geprueft = !warnung;
  var set = {};
  set[WRITEBACK.draftId] = body.draftId;
  set[WRITEBACK.internetMessageId] = body.internetMessageId;
  set[WRITEBACK.conversationId] = body.conversationId;
  set[WRITEBACK.draftedAt] = new Date();
  // Ein Entwurf mit ungepruefetem Anhang ist kein fertiger Entwurf. Der Status
  // sagt das, damit niemand ihn versehentlich als versandbereit behandelt.
  set[WRITEBACK.batchStatus] = geprueft ? 'DRAFTED' : 'DRAFTED_UNVERIFIED';
  set[WRITEBACK.sendStatus] = geprueft ? 'drafted' : 'needs_check';
  set[WRITEBACK.lastError] = String(warnung || '').slice(0, 500);

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

// ---------------------------------------------------------------- Einrichtung

/**
 * Adapter-URL eines Verantwortlichen setzen.
 *
 * Die URL enthaelt eine Signatur und ist damit ein Geheimnis - sie gehoert
 * deshalb in die Skripteigenschaften und nicht in den Quelltext. Sie wird
 * hier einmalig von Hand eingefuegt statt automatisch geholt, weil Apps
 * Script keine Azure-Anmeldung besitzt.
 */
function uiAdapterUrlSetzen_(ownerKey) {
  var ui = SpreadsheetApp.getUi();
  var propKey = ADAPTER_PROPS[ownerKey];
  var bisher = PropertiesService.getScriptProperties().getProperty(propKey);

  var antwort = ui.prompt(
    'Adapter-URL für ' + FLYERS[ownerKey].displayName,
    'Aufruf-URL des Power-Automate-Flows einfügen.\n\n' +
    'Postfach: ' + FLYERS[ownerKey].mailbox + '\n' +
    'Bisher: ' + (bisher ? bisher.slice(0, 70) + '…' : 'nicht gesetzt'),
    ui.ButtonSet.OK_CANCEL
  );
  if (antwort.getSelectedButton() !== ui.Button.OK) return 'Abgebrochen.';

  var url = String(antwort.getResponseText() || '').trim();
  if (url.indexOf('https://') !== 0) {
    ui.alert('Das ist keine HTTPS-URL. Nichts gespeichert.');
    return 'ABGELEHNT: keine HTTPS-URL.';
  }
  PropertiesService.getScriptProperties().setProperty(propKey, url);
  ui.alert('Gespeichert', propKey + ' ist gesetzt.\n\n' +
    'Nächster Schritt: Menü "Adapter-Status prüfen".', ui.ButtonSet.OK);
  return 'OK: ' + propKey + ' gesetzt.';
}

function uiAdapterUrlJoel() { return uiAdapterUrlSetzen_('JOEL'); }
function uiAdapterUrlJordi() { return uiAdapterUrlSetzen_('JORDI'); }

function uiAdapterStatus() {
  var text = preflight();
  try {
    SpreadsheetApp.getUi().alert('Adapter-Status', text, SpreadsheetApp.getUi().ButtonSet.OK);
  } catch (e) {
    Logger.log(text);
  }
  return text;
}

/**
 * Stehengebliebene Fehlermeldungen eines Batches loeschen.
 *
 * createDraftsForBatch bricht bei einem alten Last_Error bewusst ab, damit
 * niemand blind nachlaeuft. Nur: ohne einen Weg, den Vermerk nach der
 * Klaerung zu entfernen, bleibt der Batch fuer immer gesperrt. Zeilen mit
 * Draft_ID bleiben unberuehrt - dort ist der Vermerk das Pruefprotokoll.
 */
function uiFehlerZuruecksetzen(batchId) {
  try {
    if (!batchId) throw new Error('Kein Batch angegeben.');
    var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
    var werte = sheet.getDataRange().getValues();
    var headers = werte[0];
    var iBatch = headers.indexOf('Batch_ID');
    var iError = headers.indexOf(WRITEBACK.lastError);
    var iDraft = headers.indexOf(WRITEBACK.draftId);
    if (iBatch < 0 || iError < 0 || iDraft < 0) {
      throw new Error('Spalten Batch_ID / Last_Error / Draft_ID fehlen im Sheet.');
    }

    var bereinigt = 0;
    for (var r = 1; r < werte.length; r++) {
      if (String(werte[r][iBatch]) !== String(batchId)) continue;
      if (werte[r][iDraft]) continue;
      if (!werte[r][iError]) continue;
      sheet.getRange(r + 1, iError + 1).setValue('');
      bereinigt++;
    }
    return { ok: true, data: {
      summary: bereinigt + ' Fehlervermerk(e) in Batch ' + batchId + ' zurueckgesetzt.'
    } };
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
