/**
 * Testet die AUSGELIEFERTE Apps-Script-Logik in Node.
 *
 * Die Python-Engine und das Apps Script sind zwei Implementierungen derselben
 * Regeln. Getestet werden muss die, die Jordi tatsaechlich benutzt - das ist
 * diese hier. Google-APIs werden gestubbt; geprueft wird die reine Logik:
 * Compliance-Gate, Batch-Auswahl, Dublettenschutz, EML-Aufbau.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const AS = path.join(ROOT, 'apps_script');

/* ------------------------------------------------------- Google-Stubs */

let SHEETS = {};

function makeRange(sheet, row, col, numRows, numCols) {
  numRows = numRows || 1; numCols = numCols || 1;
  return {
    getValues: function () {
      const out = [];
      for (let r = 0; r < numRows; r++) {
        const line = [];
        for (let c = 0; c < numCols; c++) {
          const rr = sheet._data[row - 1 + r] || [];
          line.push(rr[col - 1 + c] === undefined ? '' : rr[col - 1 + c]);
        }
        out.push(line);
      }
      return out;
    },
    setValues: function (vals) {
      vals.forEach(function (line, r) {
        while (sheet._data.length < row + r) sheet._data.push([]);
        line.forEach(function (v, c) {
          sheet._data[row - 1 + r][col - 1 + c] = v;
        });
      });
      return this;
    },
    setValue: function (v) { return this.setValues([[v]]); },
    setFontWeight: function () { return this; },
    setBackground: function () { return this; }
  };
}

function makeSheet(name, data) {
  const sh = { _name: name, _data: data || [] };
  sh.getName = function () { return name; };
  sh.getLastRow = function () { return sh._data.length; };
  sh.getLastColumn = function () {
    return sh._data.reduce(function (m, r) { return Math.max(m, r.length); }, 0);
  };
  sh.getMaxColumns = function () { return Math.max(60, sh.getLastColumn()); };
  sh.getMaxRows = function () { return Math.max(7000, sh._data.length); };
  sh.insertColumnsAfter = function () { return sh; };
  sh.setFrozenRows = function () { return sh; };
  sh.getRange = function (r, c, nr, nc) { return makeRange(sh, r, c, nr, nc); };
  sh.getDataRange = function () {
    return makeRange(sh, 1, 1, Math.max(1, sh._data.length),
                     Math.max(1, sh.getLastColumn()));
  };
  sh.appendRow = function (row) { sh._data.push(row.slice()); return sh; };
  return sh;
}

const sandbox = {
  console: console,
  Object: Object, Array: Array, String: String, Number: Number,
  Math: Math, Date: Date, JSON: JSON, RegExp: RegExp, Error: Error,
  parseInt: parseInt, parseFloat: parseFloat, isNaN: isNaN,

  SpreadsheetApp: {
    getActiveSpreadsheet: function () {
      return {
        getSheetByName: function (n) { return SHEETS[n] || null; },
        insertSheet: function (n) { SHEETS[n] = makeSheet(n, []); return SHEETS[n]; },
        getUrl: function () { return 'https://example.invalid/sheet'; }
      };
    },
    flush: function () {},
    getUi: function () {
      return {
        createMenu: function () {
          const m = { addItem: function () { return m; },
                      addSeparator: function () { return m; },
                      addToUi: function () {} };
          return m;
        },
        alert: function () {},
        ButtonSet: { OK: 'OK' }
      };
    }
  },

  DriveApp: {
    _files: {},
    getFileById: function (id) {
      const f = DriveApp._files[id];
      if (!f) throw new Error('Datei nicht gefunden: ' + id);
      return {
        getBlob: function () {
          return {
            getBytes: function () { return f.bytes; },
            setName: function () { return this; }
          };
        }
      };
    },
    getFoldersByName: function () { return { hasNext: function () { return false; } }; },
    createFolder: function () {
      return {
        createFile: function (blob) {
          return { getUrl: function () { return 'https://example.invalid/f'; },
                   getName: function () { return blob._name || 'x.zip'; },
                   getSize: function () { return 1024; } };
        },
        getUrl: function () { return 'https://example.invalid/folder'; }
      };
    }
  },

  Utilities: {
    DigestAlgorithm: { SHA_256: 'SHA_256' },
    Charset: { UTF_8: 'UTF_8' },
    computeDigest: function (_alg, bytes) {
      const buf = Buffer.from(bytes);
      const hash = crypto.createHash('sha256').update(buf).digest();
      // Apps Script liefert signed bytes.
      return Array.from(hash).map(function (b) { return b > 127 ? b - 256 : b; });
    },
    base64Encode: function (data) {
      if (typeof data === 'string') return Buffer.from(data, 'utf8').toString('base64');
      return Buffer.from(data).toString('base64');
    },
    getUuid: function () { return crypto.randomUUID(); },
    formatDate: function (d, _tz, fmt) {
      if (fmt === 'yyyyMMdd') {
        return d.toISOString().slice(0, 10).replace(/-/g, '');
      }
      if (fmt === 'yyyy-MM-dd') return d.toISOString().slice(0, 10);
      if (fmt.indexOf("'T'") >= 0) return d.toISOString().replace(/\.\d+Z$/, 'Z');
      return d.toISOString();
    },
    newBlob: function (content, type, name) {
      return { _name: name, _type: type, _len: content.length,
               getBytes: function () { return Buffer.from(content); } };
    },
    zip: function (blobs, name) {
      const total = blobs.reduce(function (s, b) { return s + b._len; }, 0);
      return { _name: name, _len: total };
    }
  },

  Session: { getActiveUser: function () { return { getEmail: function () { return 'test@invalid'; } }; } },
  MailApp: { sendEmail: function () {} },
  ScriptApp: {
    getProjectTriggers: function () { return []; },
    newTrigger: function () {
      const t = { timeBased: function () { return t; }, atHour: function () { return t; },
                  everyDays: function () { return t; }, create: function () {} };
      return t;
    }
  },
  HtmlService: {
    createHtmlOutputFromFile: function () {
      return { setTitle: function () { return this; }, setWidth: function () { return this; } };
    }
  }
};

const ctx = vm.createContext(sandbox);
const DriveApp = sandbox.DriveApp;

['Config.gs', 'Engine.gs', 'Actions.gs', 'Code.gs'].forEach(function (f) {
  const src = fs.readFileSync(path.join(AS, f), 'utf8');
  try {
    vm.runInContext(src, ctx, { filename: f });
  } catch (e) {
    console.error('SYNTAXFEHLER in ' + f + ': ' + e.message);
    process.exit(1);
  }
});


/**
 * `const` auf oberster Ebene wird zur lexikalischen Bindung des Kontexts,
 * nicht zur Eigenschaft des Sandbox-Objekts. Die .gs-Dateien sehen einander
 * dadurch (wie in Apps Script auch), von aussen braucht es eine Auswertung
 * im Kontext.
 */
function G(name) { return vm.runInContext(name, ctx); }
const FLYERS_ = G('FLYERS');

/* ---------------------------------------------------------- Testrahmen */

const RESULTS = [];
function check(name, cond, detail) {
  RESULTS.push({ name: name, ok: !!cond, detail: detail || '' });
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  (' + detail + ')' : ''));
}

/* ------------------------------------------------------------ Fixtures */

const HEADER = ['Lead-ID', 'Firma', 'Branche', 'Tier', 'Ansprechpartner',
  'E-Mail', 'Opt-in-Status', 'Opt-out-Status', 'Versandfreigabe',
  'Verantwortlicher', 'Kampagne_ID', 'Batch_ID', 'Send_Status', 'Send_Datum',
  'Bounce_Status', 'Reply_Status', 'Follow-up-Datum', 'Notizen', 'Standort',
  'Legal_Basis', 'Suppressed', 'Batch_Status', 'Prepared_At', 'Draft_ID',
  'Drafted_At', 'Approved_At', 'Outlook_Message_ID', 'Internet_Message_ID',
  'Conversation_ID', 'Last_Reply_At', 'Last_Error'];

function row(i, owner, over) {
  over = over || {};
  const o = {
    'Lead-ID': 'TEST-' + owner + '-' + i,
    'Firma': 'Beispiel ' + i + ' GmbH',
    'Branche': 'Lebensmittelindustrie',
    'Tier': i % 3 === 0 ? 'A' : 'B',
    'Ansprechpartner': 'Herr Muster ' + i,
    'E-Mail': 'kontakt' + i + '@firma' + i + '.de',
    'Opt-in-Status': 'unknown',
    'Opt-out-Status': 'no',
    'Versandfreigabe': 'yes',
    'Verantwortlicher': owner === 'JORDI' ? 'Jordi Post' : 'Joel Cherino Diaz',
    'Kampagne_ID': 'test', 'Batch_ID': '', 'Send_Status': 'not_sent',
    'Send_Datum': '', 'Bounce_Status': '', 'Reply_Status': '',
    'Follow-up-Datum': '', 'Notizen': '', 'Standort': '',
    'Legal_Basis': 'OPT_IN', 'Suppressed': 'no', 'Batch_Status': '',
    'Prepared_At': '', 'Draft_ID': '', 'Drafted_At': '', 'Approved_At': '',
    'Outlook_Message_ID': '', 'Internet_Message_ID': '', 'Conversation_ID': '',
    'Last_Reply_At': '', 'Last_Error': ''
  };
  Object.keys(over).forEach(function (k) { o[k] = over[k]; });
  return HEADER.map(function (h) { return o[h]; });
}

function setupSheet(n, owner, over) {
  const data = [HEADER.slice()];
  for (let i = 1; i <= n; i++) data.push(row(i, owner, over));
  SHEETS = {
    ALL_LEADS: makeSheet('ALL_LEADS', data),
    BATCHES: makeSheet('BATCHES', []),
    ACTIVITIES: makeSheet('ACTIVITIES', []),
    INBOUND_EVENTS: makeSheet('INBOUND_EVENTS', [])
  };
  ctx.invalidateLeadsCache_();
}

/** Echte Flyer-Bytes in den Drive-Stub legen, damit das Asset-Gate real prueft. */
function loadRealFlyers() {
  const map = {
    '1BHx9TmtGomgslTNhi2_1VoBVPer20zkT': 'HSB-Flyer-Jordi-Post_FINAL.pdf',
    '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS': 'HSB-Flyer-Joel-Cherino_FINAL.pdf'
  };
  Object.keys(map).forEach(function (id) {
    const p = path.join(ROOT, 'assets', 'canonical', map[id]);
    DriveApp._files[id] = { bytes: fs.readFileSync(p) };
  });
}

/* --------------------------------------------------------------- Tests */

function testAssetGate() {
  loadRealFlyers();
  ['JORDI', 'JOEL'].forEach(function (k) {
    try {
      const v = ctx.getVerifiedFlyer_(k);
      check('Asset-Gate ' + k + ' bestanden (echte Bytes, echtes SHA-256)',
            v.sha256 === FLYERS_[k].sha256, v.sha256.substring(0, 12));
    } catch (e) {
      check('Asset-Gate ' + k + ' bestanden', false, e.message);
    }
  });

  // Manipulierte Datei muss abgewiesen werden.
  const orig = DriveApp._files['1BHx9TmtGomgslTNhi2_1VoBVPer20zkT'].bytes;
  DriveApp._files['1BHx9TmtGomgslTNhi2_1VoBVPer20zkT'] =
    { bytes: Buffer.concat([orig, Buffer.from('x')]) };
  let threw = false;
  try { ctx.getVerifiedFlyer_('JORDI'); } catch (e) {
    threw = /ASSET_GATE=FAIL/.test(e.message);
  }
  check('veraenderter Flyer wird abgewiesen (ASSET_GATE=FAIL)', threw);
  DriveApp._files['1BHx9TmtGomgslTNhi2_1VoBVPer20zkT'] = { bytes: orig };

  let threw2 = false;
  try { ctx.getVerifiedFlyer_('NIEMAND'); } catch (e) { threw2 = true; }
  check('unbekannter Absender wird abgewiesen', threw2);
}

function testEligibility() {
  const base = { Legal_Basis: 'OPT_IN', Versandfreigabe: 'yes', Suppressed: 'no',
                 Opt_Out: 'no', Bounce_Status: '', Send_Status: 'not_sent',
                 Email: 'a@b.de', Owner: 'Jordi Post' };
  check('gueltiger Lead ist sendefaehig', ctx.checkEligibility_(base).eligible);

  const cases = [
    ['Legal_Basis=UNKNOWN blockiert', { Legal_Basis: 'UNKNOWN' }],
    ['Legal_Basis=BLOCKED blockiert', { Legal_Basis: 'BLOCKED' }],
    ['Versandfreigabe=no blockiert', { Versandfreigabe: 'no' }],
    ['Suppressed blockiert', { Suppressed: 'yes' }],
    ['Opt_Out blockiert', { Opt_Out: 'yes' }],
    ['Hard Bounce blockiert', { Bounce_Status: 'hard_bounce' }],
    ['bereits gesendet blockiert', { Send_Status: 'sent' }],
    ['ungueltige Adresse blockiert', { Email: 'kaputt' }],
    ['leere Adresse blockiert', { Email: '' }],
    ['unklarer Owner blockiert', { Owner: '' }]
  ];
  cases.forEach(function (c) {
    const lead = Object.assign({}, base, c[1]);
    check(c[0], !ctx.checkEligibility_(lead).eligible);
  });

  check('EXISTING_CUSTOMER_7_3 ist sendefaehig',
        ctx.checkEligibility_(Object.assign({}, base,
          { Legal_Basis: 'EXISTING_CUSTOMER_7_3' })).eligible);
  check('leeres Legal_Basis faellt auf UNKNOWN zurueck',
        !ctx.checkEligibility_(Object.assign({}, base,
          { Legal_Basis: '', Opt_In: 'unknown' })).eligible);
}

function testDynamicCounts() {
  loadRealFlyers();
  [1, 17, 25, 100, 250].forEach(function (n) {
    setupSheet(300, 'JORDI');
    const b = ctx.prepareBatch({ owner: 'JORDI', count: n });
    check('Apps Script dynamisch JORDI count=' + n,
          b.stats.selected_count === n, 'selected=' + b.stats.selected_count);
  });

  setupSheet(300, 'JOEL');
  const b = ctx.prepareBatch({ owner: 'JOEL', count: 100 });
  check('Apps Script dynamisch JOEL count=100', b.stats.selected_count === 100);
  check('Batch nutzt Joels Flyer', b.asset_sha256 === FLYERS_.JOEL.sha256);
  check('Batch-ID Format', /^HSB-\d{8}-JOEL-\d{4}$/.test(b.batch_id), b.batch_id);
}

function testGateNotBypassable() {
  loadRealFlyers();
  [1, 10, 999].forEach(function (n) {
    setupSheet(50, 'JORDI', { 'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN' });
    const b = ctx.prepareBatch({ owner: 'JORDI', count: n });
    check('Gate nicht ueber Batchgroesse umgehbar (count=' + n + ')',
          b.stats.selected_count === 0, 'selected=' + b.stats.selected_count);
  });
}

function testEmptyBatchExplained() {
  loadRealFlyers();
  setupSheet(50, 'JORDI', { 'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN' });
  const b = ctx.prepareBatch({ owner: 'JORDI', count: 100 });
  check('leerer Batch hat Status EMPTY_NO_ELIGIBLE_LEADS',
        b.status === 'EMPTY_NO_ELIGIBLE_LEADS', b.status);
  check('Ausschlussgruende werden gezaehlt',
        b.exclusion_reasons['Legal_Basis=UNKNOWN'] === 50,
        JSON.stringify(b.exclusion_reasons));
  check('Fehlbetrag ausgewiesen', b.stats.shortfall === 100);
}

function testEmailDedup() {
  loadRealFlyers();
  const data = [HEADER.slice()];
  for (let i = 1; i <= 5; i++) data.push(row(i, 'JORDI'));
  // Gleiche Adresse, andere Lead-ID.
  data.push(row(99, 'JORDI', { 'E-Mail': 'kontakt1@firma1.de' }));
  SHEETS = {
    ALL_LEADS: makeSheet('ALL_LEADS', data), BATCHES: makeSheet('BATCHES', []),
    ACTIVITIES: makeSheet('ACTIVITIES', []), INBOUND_EVENTS: makeSheet('INBOUND_EVENTS', [])
  };
  ctx.invalidateLeadsCache_();

  const b = ctx.prepareBatch({ owner: 'JORDI', count: 10 });
  const mails = b.leads.map(function (l) { return String(l.Email).toLowerCase(); });
  const uniq = {};
  mails.forEach(function (m) { uniq[m] = 1; });
  check('Apps Script: doppelte Adresse nicht doppelt ausgewaehlt',
        mails.length === Object.keys(uniq).length,
        mails.length + ' Adressen, ' + Object.keys(uniq).length + ' eindeutig');
  check('Apps Script: genau 5 von 6 ausgewaehlt',
        b.stats.selected_count === 5, 'selected=' + b.stats.selected_count);
}

function testNoCrossSender() {
  loadRealFlyers();
  setupSheet(200, 'JORDI');
  const bJ = ctx.prepareBatch({ owner: 'JORDI', count: 50 });
  check('JORDI-Batch traegt Jordis Hash', bJ.asset_sha256 === FLYERS_.JORDI.sha256);
  check('JORDI-Batch traegt NICHT Joels Hash', bJ.asset_sha256 !== FLYERS_.JOEL.sha256);
  check('JORDI-Batch nutzt Jordis Mailbox', bJ.mailbox === 'j-post@hsb-boden.de');

  setupSheet(200, 'JOEL');
  const bO = ctx.prepareBatch({ owner: 'JOEL', count: 50 });
  check('JOEL-Batch traegt Joels Hash', bO.asset_sha256 === FLYERS_.JOEL.sha256);
  check('JOEL-Batch nutzt Joels Mailbox', bO.mailbox === 'j-cherino@hsb-boden.de');
}

function testEmlStructure() {
  loadRealFlyers();
  const flyer = FLYERS_.JORDI;
  const lead = { Lead_ID: 'TEST-1', Company: 'Beispiel GmbH',
                 Contact: 'Herr Muster', Email: 'kontakt@beispiel.de' };
  const eml = ctx.buildEml_(lead, 'HSB-20260821-JORDI-0001', flyer, 'QkFTRTY0');

  check('EML: X-Unsent: 1 gesetzt', /^X-Unsent: 1$/m.test(eml));
  check('EML: X-HSB-Lead-ID gesetzt', /^X-HSB-Lead-ID: TEST-1$/m.test(eml));
  check('EML: X-HSB-Batch-ID gesetzt',
        /^X-HSB-Batch-ID: HSB-20260821-JORDI-0001$/m.test(eml));
  check('EML: From ist Jordis Mailbox', eml.indexOf('j-post@hsb-boden.de') > 0);
  check('EML: Reply-To gesetzt', /^Reply-To: j-post@hsb-boden\.de$/m.test(eml));
  check('EML: To gesetzt', /^To: kontakt@beispiel\.de$/m.test(eml));
  check('EML: kein fremder Absender', eml.indexOf('j-cherino@') === -1);
  check('EML: Anhangsname korrekt',
        eml.indexOf('HSB-Flyer-Jordi-Post_FINAL.pdf') > 0);
  check('EML: genau ein Anhang',
        (eml.match(/Content-Disposition: attachment/g) || []).length === 1);
  check('EML: CRLF-Zeilenenden', eml.indexOf('\r\n') > 0);
  check('EML: Asset-Hash im Header',
        eml.indexOf(flyer.sha256) > 0);

  const utf8 = ctx.buildEml_({ Lead_ID: 'X', Company: 'Käse & Co', Contact: 'Frau Grün',
                               Email: 'a@b.de' }, 'B', flyer, 'QQ==');
  check('EML: Umlaute im Betreff kodiert',
        /^Subject: =\?UTF-8\?B\?/m.test(utf8) || /^Subject: [\x20-\x7E]*$/m.test(utf8));
}

function testQualifyAndDedupWrite() {
  loadRealFlyers();
  setupSheet(50, 'JORDI', { 'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN' });

  const before = ctx.prepareBatch({ owner: 'JORDI', count: 20 });
  check('vor Qualifizierung: 0 auswaehlbar', before.stats.selected_count === 0);

  const q = ctx.qualifyLeads({ owner: 'JORDI', count: 20,
                               legalBasis: 'EXISTING_CUSTOMER_7_3' });
  check('Qualifizierung setzt 20 Leads', q.updated === 20, 'updated=' + q.updated);

  const after = ctx.prepareBatch({ owner: 'JORDI', count: 20 });
  check('nach Qualifizierung: 20 auswaehlbar',
        after.stats.selected_count === 20, 'selected=' + after.stats.selected_count);

  // Opt-out darf durch Qualifizierung nicht ueberschrieben werden.
  setupSheet(10, 'JORDI', { 'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN',
                            'Opt-out-Status': 'yes' });
  const q2 = ctx.qualifyLeads({ owner: 'JORDI', count: 10, legalBasis: 'OPT_IN' });
  check('Opt-out wird bei Qualifizierung nicht angetastet', q2.updated === 0,
        'updated=' + q2.updated);
}

function testSuppression() {
  loadRealFlyers();
  setupSheet(10, 'JORDI');
  ctx.setLeadStatus('TEST-JORDI-1', 'OPT_OUT', 0, 'Abmeldung per Mail');
  ctx.invalidateLeadsCache_();
  const b = ctx.prepareBatch({ owner: 'JORDI', count: 10 });
  const ids = b.leads.map(function (l) { return l.Lead_ID; });
  check('Opt-out-Lead faellt aus kuenftigen Batches',
        ids.indexOf('TEST-JORDI-1') === -1);

  setupSheet(10, 'JORDI');
  ctx.setLeadStatus('TEST-JORDI-2', 'HARD_BOUNCE', 0, '');
  ctx.invalidateLeadsCache_();
  const b2 = ctx.prepareBatch({ owner: 'JORDI', count: 10 });
  check('Hard-Bounce-Lead faellt aus kuenftigen Batches',
        b2.leads.map(function (l) { return l.Lead_ID; }).indexOf('TEST-JORDI-2') === -1);
}

function testDuplicateBatchProtection() {
  loadRealFlyers();
  setupSheet(60, 'JORDI');
  const b1 = ctx.prepareBatch({ owner: 'JORDI', count: 20 });
  ctx.invalidateLeadsCache_();
  const b2 = ctx.prepareBatch({ owner: 'JORDI', count: 20 });

  const s1 = {};
  b1.leads.forEach(function (l) { s1[l.Lead_ID] = 1; });
  const overlap = b2.leads.filter(function (l) { return s1[l.Lead_ID]; });
  check('kein Lead in zwei aktiven Batches', overlap.length === 0,
        overlap.length + ' Ueberschneidungen');
  check('zweiter Batch liefert weitere 20', b2.stats.selected_count === 20,
        'selected=' + b2.stats.selected_count);
  check('unterschiedliche Batch-IDs', b1.batch_id !== b2.batch_id);
}

function testDashboard() {
  loadRealFlyers();
  setupSheet(30, 'JORDI');
  const d = ctx.getDashboard();
  check('Dashboard zaehlt alle Leads', d.total === 30, 'total=' + d.total);
  check('Dashboard kennt JORDI', !!d.owners.JORDI);
  check('Dashboard zaehlt sendefaehige', d.owners.JORDI.eligible === 30,
        'eligible=' + d.owners.JORDI.eligible);
}


function testEmlExportChunking() {
  loadRealFlyers();
  setupSheet(60, 'JORDI');
  const b = ctx.prepareBatch({ owner: 'JORDI', count: 45 });
  check('Batch fuer Export vorbereitet', b.stats.selected_count === 45);
  ctx.invalidateLeadsCache_();

  const r = ctx.exportBatchAsEmlZip(b.batch_id, 0);
  check('Export liefert Teilpakete', r.parts.length >= 2,
        r.parts.length + ' Pakete');
  check('Export deckt alle Entwuerfe ab', r.written === 45,
        'written=' + r.written + ' von ' + r.total);
  check('Export als vollstaendig markiert', r.complete === true);
  check('kein Fortsetzungsindex noetig', r.next_index === null);
  const sum = r.parts.reduce(function (s, p) { return s + p.count; }, 0);
  check('Summe der Teilpakete = Gesamtzahl', sum === 45, 'sum=' + sum);
  check('kein Teilpaket groesser als das Limit',
        r.parts.every(function (p) { return p.count <= 20; }));
  check('Export nennt den Asset-Hash', r.asset_sha256 === FLYERS_.JORDI.sha256);

  // Fortsetzung ab der Mitte darf nicht von vorn beginnen.
  const r2 = ctx.exportBatchAsEmlZip(b.batch_id, 40);
  check('Fortsetzung ab Index 40 liefert nur den Rest', r2.written === 5,
        'written=' + r2.written);
}

function testFollowUps() {
  loadRealFlyers();
  setupSheet(10, 'JORDI');
  // Zwei Faellige, einer in der Zukunft.
  ctx.setLeadStatus('TEST-JORDI-1', 'REPLIED', 0, 'Rueckmeldung');
  ctx.setLeadStatus('TEST-JORDI-2', 'FOLLOWUP', -1, '');
  ctx.setLeadStatus('TEST-JORDI-3', 'FOLLOWUP', 30, '');
  ctx.invalidateLeadsCache_();

  const due = ctx.getDueFollowUps('JORDI');
  const ids = due.map(function (d) { return d.Lead_ID; });
  check('Wiedervorlage in 30 Tagen ist NICHT faellig',
        ids.indexOf('TEST-JORDI-3') === -1);
  check('Wiedervorlage liefert eine Liste', Array.isArray(due));

  // Opt-out darf nie in der Wiedervorlage auftauchen.
  ctx.setLeadStatus('TEST-JORDI-4', 'FOLLOWUP', -1, '');
  ctx.setLeadStatus('TEST-JORDI-4', 'OPT_OUT', 0, '');
  ctx.invalidateLeadsCache_();
  const due2 = ctx.getDueFollowUps('JORDI');
  check('abgemeldeter Lead erscheint nicht in der Wiedervorlage',
        due2.map(function (d) { return d.Lead_ID; }).indexOf('TEST-JORDI-4') === -1);
}

function testEnsureColumns() {
  // Blatt ohne die zwoelf Zusatzspalten.
  const shortHeader = HEADER.slice(0, 19);
  const data = [shortHeader];
  for (let i = 1; i <= 5; i++) data.push(row(i, 'JORDI').slice(0, 19));
  SHEETS = { ALL_LEADS: makeSheet('ALL_LEADS', data), BATCHES: makeSheet('BATCHES', []),
             ACTIVITIES: makeSheet('ACTIVITIES', []), INBOUND_EVENTS: makeSheet('INBOUND_EVENTS', []) };
  ctx.invalidateLeadsCache_();

  const r = ctx.ensureColumns();
  check('ensureColumns ergaenzt zwoelf Spalten', r.added.length === 12,
        r.added.length + ' ergaenzt');

  const hdr = SHEETS.ALL_LEADS._data[0];
  check('Legal_Basis angelegt', hdr.indexOf('Legal_Basis') >= 0);
  check('Suppressed angelegt', hdr.indexOf('Suppressed') >= 0);

  const lbCol = hdr.indexOf('Legal_Basis');
  check('Legal_Basis fail-closed auf UNKNOWN vorbelegt',
        SHEETS.ALL_LEADS._data[1][lbCol] === 'UNKNOWN',
        String(SHEETS.ALL_LEADS._data[1][lbCol]));

  ctx.invalidateLeadsCache_();
  const r2 = ctx.ensureColumns();
  check('ensureColumns ist idempotent', r2.added.length === 0, r2.message);
}

/* ---------------------------------------------------------------- main */

console.log('='.repeat(70));
console.log('HSB SALES OS - APPS-SCRIPT-TESTS (ausgelieferter Code, Node + Stubs)');
console.log('='.repeat(70));

[testAssetGate, testEligibility, testDynamicCounts, testGateNotBypassable,
 testEmptyBatchExplained, testEmailDedup, testNoCrossSender, testEmlStructure,
 testQualifyAndDedupWrite, testSuppression, testDuplicateBatchProtection,
 testDashboard, testEmlExportChunking, testFollowUps, testEnsureColumns].forEach(function (fn) {
  console.log('\n--- ' + fn.name + ' ---');
  try { fn(); } catch (e) {
    check(fn.name + ' ohne Ausnahme', false, e.message + '\n' + e.stack);
  }
});

const pass = RESULTS.filter(function (r) { return r.ok; }).length;
const fail = RESULTS.length - pass;
console.log('\n' + '='.repeat(70));
console.log('ERGEBNIS: ' + pass + ' bestanden, ' + fail + ' fehlgeschlagen von '
            + RESULTS.length);
console.log('REAL_EXTERNAL_SEND_COUNT=0');
console.log('='.repeat(70));
if (fail) {
  RESULTS.filter(function (r) { return !r.ok; }).forEach(function (r) {
    console.log('  FAIL: ' + r.name + ' ' + r.detail);
  });
}
fs.writeFileSync(path.join(__dirname, 'last_run_apps_script.json'),
  JSON.stringify({ test_count: RESULTS.length, test_pass: pass,
                   test_fail: fail }, null, 2) + '\n');
process.exit(fail ? 1 : 0);
