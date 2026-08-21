/**
 * Testet die AUSGELIEFERTE Apps-Script-Logik in Node.
 *
 * Die Python-Engine und das Apps Script sind zwei Implementierungen derselben
 * Regeln. Getestet werden muss die, die Jordi tatsaechlich benutzt - das ist
 * diese hier. Google-APIs werden gestubbt; geprueft wird die reine Logik:
 * Compliance-Gate, Batch-Auswahl, Dublettenschutz, EML-Aufbau, Locking,
 * Idempotenz, Inbound-Events.
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

let CURRENT_LOCK = null;

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

  LockService: {
    _forceTimeout: false,
    getDocumentLock: function () {
      return {
        tryLock: function (timeout) {
          if (sandbox.LockService._forceTimeout) return false;
          if (CURRENT_LOCK && CURRENT_LOCK !== this) return false;
          CURRENT_LOCK = this;
          return true;
        },
        waitLock: function (timeout) {
          if (!this.tryLock(timeout)) throw new Error('Lock timeout');
        },
        releaseLock: function () {
          if (CURRENT_LOCK === this) CURRENT_LOCK = null;
        },
        hasLock: function () {
          return CURRENT_LOCK === this;
        }
      };
    },
    getScriptLock: function () { return this.getDocumentLock(); },
    getUserLock: function () { return this.getDocumentLock(); }
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
  data.push(row(99, 'JORDI', { 'E-Mail': 'kontakt1@firma1.de' }));
  SHEETS = {
    ALL_LEADS: makeSheet('ALL_LEADS', data), BATCHES: makeSheet('BATCHES', []),
    ACTIVITIES: makeSheet('ACTIVITIES', []), INBOUND_EVENTS: makeSheet('INBOUND_EVENTS', [])
  };
  ctx.invalidateLeadsCache_();

  const b = ctx.prepareBatch({ owner: 'JORDI', count: 10 });
  const mails = b.leads.map(function (l) { return String(l.Email).toLowerCase(); });
  check('Apps Script: doppelte Adresse nicht doppelt ausgewaehlt',
        mails.length === new Set(mails).size,
        mails.length + ' Adressen, ' + new Set(mails).size + ' eindeutig');
  check('Apps Script: genau 5 von 6 ausgewaehlt', b.stats.selected_count === 5,
        'selected=' + b.stats.selected_count);
}

function testNoCrossSender() {
  loadRealFlyers();
  setupSheet(10, 'JORDI');
  const bj = ctx.prepareBatch({ owner: 'JORDI', count: 5 });
  check('JORDI-Batch traegt Jordis Hash', bj.asset_sha256 === FLYERS_.JORDI.sha256);
  check('JORDI-Batch traegt NICHT Joels Hash', bj.asset_sha256 !== FLYERS_.JOEL.sha256);
  check('JORDI-Batch nutzt Jordis Mailbox', bj.mailbox === FLYERS_.JORDI.mailbox);

  setupSheet(10, 'JOEL');
  const bl = ctx.prepareBatch({ owner: 'JOEL', count: 5 });
  check('JOEL-Batch traegt Joels Hash', bl.asset_sha256 === FLYERS_.JOEL.sha256);
  check('JOEL-Batch nutzt Joels Mailbox', bl.mailbox === FLYERS_.JOEL.mailbox);
}

function testEmlStructure() {
  loadRealFlyers();
  const lead = { Lead_ID: 'TEST-001', Company: 'Müller GmbH & Co. KG',
                 Contact: 'Herr Dr. Schmidt', Email: 'schmidt@muster.de' };
  const flyer = FLYERS_.JORDI;
  const dummyPdfChunked = 'AAAA\r\nBBBB';
  const eml = ctx.buildEml_(lead, 'HSB-20260821-JORDI-0001', flyer, dummyPdfChunked);

  check('EML: X-Unsent: 1 gesetzt', /X-Unsent: 1/.test(eml));
  check('EML: X-HSB-Lead-ID gesetzt', /X-HSB-Lead-ID: TEST-001/.test(eml));
  check('EML: X-HSB-Batch-ID gesetzt', /X-HSB-Batch-ID: HSB-20260821-JORDI-0001/.test(eml));
  check('EML: From ist Jordis Mailbox', new RegExp('From: Jordi Post <' + flyer.mailbox + '>').test(eml));
  check('EML: Reply-To gesetzt', new RegExp('Reply-To: ' + flyer.mailbox).test(eml));
  check('EML: To gesetzt', /To: schmidt@muster\.de/.test(eml));
  check('EML: kein fremder Absender', !/j-cherino/.test(eml));
  check('EML: Anhangsname korrekt', new RegExp('filename="' + flyer.fileName + '"').test(eml));
  check('EML: genau ein Anhang', (eml.match(/Content-Type: application\/pdf/g) || []).length === 1);
  check('EML: CRLF-Zeilenenden', eml.indexOf('\r\n') >= 0 && eml.indexOf('\r\n\r\n') >= 0);
  check('EML: Asset-Hash im Header', new RegExp('X-HSB-Asset-SHA256: ' + flyer.sha256).test(eml));
  check('EML: Umlaute im Betreff kodiert', /Subject: =\?UTF-8\?B\?/.test(eml));
}

function testQualifyAndDedupWrite() {
  setupSheet(20, 'JORDI', { 'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN' });
  check('vor Qualifizierung: 0 auswaehlbar',
        ctx.prepareBatch({ owner: 'JORDI', count: 10 }).stats.selected_count === 0);

  const r = ctx.qualifyLeads({ owner: 'JORDI', count: 20, legalBasis: 'OPT_IN' });
  check('Qualifizierung setzt 20 Leads', r.updated === 20, 'updated=' + r.updated);
  check('nach Qualifizierung: 20 auswaehlbar',
        ctx.prepareBatch({ owner: 'JORDI', count: 20 }).stats.selected_count === 20,
        'selected=20');

  // Opt-out darf nicht ueberschrieben werden.
  setupSheet(5, 'JORDI', { 'Opt_Out': 'yes', 'Suppressed': 'yes', 'Legal_Basis': 'UNKNOWN' });
  const r2 = ctx.qualifyLeads({ owner: 'JORDI', count: 5, legalBasis: 'OPT_IN' });
  check('Opt-out wird bei Qualifizierung nicht angetastet', r2.updated === 0, 'updated=' + r2.updated);
}

function testSuppression() {
  loadRealFlyers();
  setupSheet(10, 'JORDI');
  ctx.setLeadStatus('TEST-JORDI-1', 'OPT_OUT', 0, 'Wunsch nach Abmeldung');
  check('Opt-out-Lead faellt aus kuenftigen Batches',
        ctx.prepareBatch({ owner: 'JORDI', count: 10 }).leads.every(function (l) {
          return l.Lead_ID !== 'TEST-JORDI-1';
        }));

  setupSheet(10, 'JORDI');
  ctx.setLeadStatus('TEST-JORDI-2', 'HARD_BOUNCE', 0, 'Mailbox not found 550');
  check('Hard-Bounce-Lead faellt aus kuenftigen Batches',
        ctx.prepareBatch({ owner: 'JORDI', count: 10 }).leads.every(function (l) {
          return l.Lead_ID !== 'TEST-JORDI-2';
        }));
}

function testDuplicateBatchProtection() {
  loadRealFlyers();
  setupSheet(40, 'JORDI');
  const b1 = ctx.prepareBatch({ owner: 'JORDI', count: 20 });
  const b2 = ctx.prepareBatch({ owner: 'JORDI', count: 20 });
  const ids1 = new Set(b1.leads.map(function (l) { return l.Lead_ID; }));
  const overlap = b2.leads.filter(function (l) { return ids1.has(l.Lead_ID); });
  check('kein Lead in zwei aktiven Batches', overlap.length === 0,
        overlap.length + ' Ueberschneidungen');
  check('zweiter Batch liefert weitere 20', b2.stats.selected_count === 20,
        'selected=' + b2.stats.selected_count);
  check('unterschiedliche Batch-IDs', b1.batch_id !== b2.batch_id);
}

function testDashboard() {
  setupSheet(30, 'JORDI');
  const d = ctx.getDashboard();
  check('Dashboard zaehlt alle Leads', d.total === 30, 'total=' + d.total);
  check('Dashboard kennt JORDI', !!d.owners.JORDI);
  check('Dashboard zaehlt sendefaehige', d.owners.JORDI.eligible === 30,
        'eligible=' + d.owners.JORDI.eligible);
}

function testEmlExportChunking() {
  loadRealFlyers();
  setupSheet(45, 'JORDI');
  const b = ctx.prepareBatch({ owner: 'JORDI', count: 45 });
  check('Batch fuer Export vorbereitet', b.stats.selected_count === 45);

  const exp = ctx.exportBatchAsEmlZip(b.batch_id, 0);
  check('Export liefert Teilpakete', exp.parts.length === 3,
        exp.parts.length + ' Pakete');
  check('Export deckt alle Entwuerfe ab', exp.written === 45,
        'written=' + exp.written + ' von ' + exp.total);
  check('Export als vollstaendig markiert', exp.complete === true);
  check('kein Fortsetzungsindex noetig', exp.next_index === null);

  const sumCount = exp.parts.reduce(function (s, p) { return s + p.count; }, 0);
  check('Summe der Teilpakete = Gesamtzahl', sumCount === 45, 'sum=' + sumCount);
  check('kein Teilpaket groesser als das Limit',
        exp.parts.every(function (p) { return p.count <= 20; }));
  check('Export nennt den Asset-Hash', exp.asset_sha256 === FLYERS_.JORDI.sha256);

  const exp2 = ctx.exportBatchAsEmlZip(b.batch_id, 40);
  check('Fortsetzung ab Index 40 liefert nur den Rest', exp2.written === 5,
        'written=' + exp2.written);
}

function testFollowUps() {
  setupSheet(5, 'JORDI');
  ctx.setLeadStatus('TEST-JORDI-1', 'SENT', 0);
  ctx.setLeadStatus('TEST-JORDI-1', 'SENT', 30);
  const due = ctx.getDueFollowUps('JORDI');
  check('Wiedervorlage in 30 Tagen ist NICHT faellig',
        due.every(function (d) { return d.Lead_ID !== 'TEST-JORDI-1'; }));

  ctx.setLeadStatus('TEST-JORDI-2', 'SENT', -1);
  const due2 = ctx.getDueFollowUps('JORDI');
  check('Wiedervorlage liefert eine Liste', Array.isArray(due2));

  ctx.setLeadStatus('TEST-JORDI-2', 'OPT_OUT', 0);
  const due3 = ctx.getDueFollowUps('JORDI');
  check('abgemeldeter Lead erscheint nicht in der Wiedervorlage',
        due3.every(function (d) { return d.Lead_ID !== 'TEST-JORDI-2'; }));
}

function testEnsureColumns() {
  const kurz = [HEADER.slice(0, 19)];
  for (let i = 1; i <= 3; i++) kurz.push(row(i, 'JORDI').slice(0, 19));
  SHEETS = { ALL_LEADS: makeSheet('ALL_LEADS', kurz) };
  ctx.invalidateLeadsCache_();

  const r = ctx.ensureColumns();
  check('ensureColumns ergaenzt zwoelf Spalten', r.added.length === 12,
        r.added.length + ' ergaenzt');

  const sh = SHEETS.ALL_LEADS;
  const hNeu = sh._data[0];
  check('Legal_Basis angelegt', hNeu.indexOf('Legal_Basis') >= 0);
  check('Suppressed angelegt', hNeu.indexOf('Suppressed') >= 0);

  const pos = hNeu.indexOf('Legal_Basis');
  check('Legal_Basis fail-closed auf UNKNOWN vorbelegt',
        sh._data[1][pos] === 'UNKNOWN', sh._data[1][pos]);

  const r2 = ctx.ensureColumns();
  check('ensureColumns ist idempotent', r2.added.length === 0, r2.message);
}

function testSetupState() {
  loadRealFlyers();
  setupSheet(5, 'JORDI');
  var st = ctx.getSetupState();
  check('Setup: vollstaendige Spalten werden erkannt', st.columns_ok === true,
        'fehlend: ' + st.missing_columns.length);
  check('Setup: Flyer als OK gemeldet', st.flyers_ok === true,
        JSON.stringify(st.flyers));

  var kurz = [HEADER.slice(0, 19)];
  for (var i = 1; i <= 3; i++) kurz.push(row(i, 'JORDI').slice(0, 19));
  SHEETS = { ALL_LEADS: makeSheet('ALL_LEADS', kurz), BATCHES: makeSheet('BATCHES', []),
             ACTIVITIES: makeSheet('ACTIVITIES', []), INBOUND_EVENTS: makeSheet('INBOUND_EVENTS', []) };
  ctx.invalidateLeadsCache_();
  var st2 = ctx.getSetupState();
  check('Setup: fehlende Spalten werden gemeldet', st2.columns_ok === false
        && st2.missing_columns.length === 12,
        st2.missing_columns.length + ' fehlend');
}

function testBatchListe() {
  loadRealFlyers();
  setupSheet(80, 'JORDI');
  ctx.prepareBatch({ owner: 'JORDI', count: 10, campaign: 'test-a' });
  ctx.invalidateLeadsCache_();
  ctx.prepareBatch({ owner: 'JORDI', count: 5, campaign: 'test-b' });

  var liste = ctx.getBatches('JORDI', 10);
  check('Batchliste liefert beide Batches', liste.length === 2, liste.length + '');
  check('Batchliste neueste zuerst', liste[0].campaign === 'test-b',
        String(liste[0].campaign));
  check('Batchliste kennt die Anzahl', liste[0].selected === 5,
        String(liste[0].selected));

  var leer = ctx.getBatches('JOEL', 10);
  check('Batchliste filtert nach Absender', leer.length === 0, leer.length + '');
}

function testSuche() {
  loadRealFlyers();
  setupSheet(30, 'JORDI');

  var t = ctx.searchLeads('Beispiel 7 GmbH', 'JORDI', 25);
  check('Suche findet nach Firma', t.length >= 1, t.length + ' Treffer');

  var m = ctx.searchLeads('kontakt3@firma3.de', 'JORDI', 25);
  check('Suche findet nach E-Mail', m.length === 1, m.length + ' Treffer');
  check('Suchtreffer meldet Sendefaehigkeit', m.length && m[0].eligible === true);

  check('Suche unter 2 Zeichen liefert nichts',
        ctx.searchLeads('x', 'JORDI', 25).length === 0);
  check('Suche ohne Treffer liefert leere Liste',
        ctx.searchLeads('gibtesnicht-zzz', 'JORDI', 25).length === 0);
  check('Suche begrenzt die Trefferzahl',
        ctx.searchLeads('Beispiel', 'JORDI', 5).length === 5);

  setupSheet(5, 'JORDI', { 'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN' });
  var g = ctx.searchLeads('Beispiel 1 GmbH', 'JORDI', 5);
  check('Suche nennt den Sperrgrund',
        g.length >= 1 && g[0].eligible === false && g[0].reasons.length > 0,
        g.length ? g[0].reasons.join(', ') : 'kein Treffer');

  setupSheet(10, 'JOEL');
  check('Suche filtert nach Absender',
        ctx.searchLeads('Beispiel', 'JORDI', 10).length === 0);
}

function testLockServiceAndConcurrency() {
  loadRealFlyers();
  setupSheet(40, 'JORDI');

  // 1. LockService timeout fail-closed
  sandbox.LockService._forceTimeout = true;
  let lockFailed = false;
  try {
    ctx.prepareBatch({ owner: 'JORDI', count: 10 });
  } catch (e) {
    lockFailed = /LOCK_TIMEOUT/.test(e.message);
  }
  check('LockService: Timeout wird fail-closed abgewiesen', lockFailed);
  sandbox.LockService._forceTimeout = false;

  // 2. Concurrency Simulation: zwei aufeinanderfolgende Zuteilungen aus demselben Pool
  // duerfen 0 Ueberschneidungen haben.
  setupSheet(50, 'JORDI');
  const op1 = ctx.prepareBatch({ owner: 'JORDI', count: 20 });
  ctx.invalidateLeadsCache_();
  const op2 = ctx.prepareBatch({ owner: 'JORDI', count: 20 });

  const set1 = new Set(op1.leads.map(function (l) { return l.Lead_ID; }));
  const set2 = new Set(op2.leads.map(function (l) { return l.Lead_ID; }));
  const overlapping = Array.from(set1).filter(function (id) { return set2.has(id); });

  check('Concurrency: OVERLAPPING_LEAD_IDS = 0', overlapping.length === 0,
        'overlap=' + overlapping.length);
  check('Concurrency: beide Batches vollstaendig befuellt',
        op1.stats.selected_count === 20 && op2.stats.selected_count === 20,
        'b1=' + op1.stats.selected_count + ' b2=' + op2.stats.selected_count);
}

function testIdempotency() {
  loadRealFlyers();
  setupSheet(30, 'JORDI');

  // Erstes Ausfuehren
  const firstRun = ctx.prepareBatch({ owner: 'JORDI', count: 10, batch_id: 'HSB-20260821-JORDI-IDEMP1' });
  check('Idempotenz: Erstausfuehrung erfolgreich', firstRun.stats.selected_count === 10,
        'selected=' + firstRun.stats.selected_count);

  const initialBatchCount = SHEETS.BATCHES._data.length;
  const initialActCount = SHEETS.ACTIVITIES._data.length;

  // Replay desselben Batch_ID
  const replayRun = ctx.prepareBatch({ owner: 'JORDI', count: 10, batch_id: 'HSB-20260821-JORDI-IDEMP1' });
  check('Idempotenz: Replay liefert already_processed', replayRun.already_processed === true);
  check('Idempotenz: Replay liefert identische Leads',
        replayRun.leads.length === 10 && replayRun.leads[0].Lead_ID === firstRun.leads[0].Lead_ID,
        'first=' + firstRun.leads[0].Lead_ID + ' replay=' + (replayRun.leads[0] || {}).Lead_ID);
  check('Idempotenz: Keine doppelten BATCHES-Zeilen (SECOND_RUN_DUPLICATE_OUTPUTS=0)',
        SHEETS.BATCHES._data.length === initialBatchCount);
  check('Idempotenz: Keine doppelten ACTIVITIES-Zeilen (SECOND_RUN_DUPLICATE_ACTIVITIES=0)',
        SHEETS.ACTIVITIES._data.length === initialActCount);
}

function testInboundEvents() {
  loadRealFlyers();
  setupSheet(20, 'JORDI');

  // Lead vorbereiten und mit Message-ID versehen
  const b = ctx.prepareBatch({ owner: 'JORDI', count: 5 });
  const lead1 = b.leads[0];
  const sh = SHEETS.ALL_LEADS;
  const read = ctx.readLeads_();
  const targetLead1 = read.leads.filter(function (l) { return l.Lead_ID === lead1.Lead_ID; })[0];
  const cMsgId = read.index['Internet_Message_ID'] + 1;
  sh.getRange(targetLead1._row, cMsgId).setValue('<msg-12345@hsb-boden.de>');
  ctx.invalidateLeadsCache_();

  // 1. Gueltige Antwort ueber Message-ID
  const res1 = ctx.processInboundEvent({
    event_id: 'EVT-001',
    event_type: 'REPLY',
    in_reply_to: '<msg-12345@hsb-boden.de>',
    email: lead1.Email,
    subject: 'Re: Industrieboeden'
  });
  check('Inbound: gueltige Antwort erfolgreich zugeordnet',
        res1.matched === true && res1.lead_id === lead1.Lead_ID,
        'lead=' + res1.lead_id);

  const updatedLead1 = ctx.readLeads_().leads.filter(function (l) {
    return l.Lead_ID === lead1.Lead_ID;
  })[0];
  check('Inbound: Reply_Status auf reply/replied gesetzt',
        updatedLead1.Reply_Status === 'reply' || updatedLead1.Reply_Status === 'replied',
        updatedLead1.Reply_Status);

  // 2. Doppeltes Inbound-Event (Deduplizierung)
  const resDup = ctx.processInboundEvent({
    event_id: 'EVT-001',
    event_type: 'REPLY',
    in_reply_to: '<msg-12345@hsb-boden.de>',
    email: lead1.Email
  });
  check('Inbound: doppeltes Event wird ignoriert (DUPLICATE_IGNORED)',
        resDup.duplicate === true && resDup.status === 'DUPLICATE_IGNORED');

  // 3. Hard Bounce ueber E-Mail-Adresse
  const lead2 = b.leads[1];
  const resBounce = ctx.processInboundEvent({
    event_id: 'EVT-002',
    event_type: 'HARD_BOUNCE',
    email: lead2.Email,
    details: '550 User unknown'
  });
  check('Inbound: Hard Bounce zugeordnet',
        resBounce.matched === true && resBounce.lead_id === lead2.Lead_ID);
  const updatedLead2 = ctx.readLeads_().leads.filter(function (l) {
    return l.Lead_ID === lead2.Lead_ID;
  })[0];
  check('Inbound: Hard Bounce setzt Suppressed=yes und Versandfreigabe=no',
        updatedLead2.Suppressed === 'yes' && updatedLead2.Versandfreigabe === 'no',
        'Suppressed=' + updatedLead2.Suppressed + ' Versandfreigabe=' + updatedLead2.Versandfreigabe);

  // 4. Opt-Out
  const lead3 = b.leads[2];
  const resOptOut = ctx.processInboundEvent({
    event_id: 'EVT-003',
    event_type: 'OPT_OUT',
    email: lead3.Email
  });
  check('Inbound: Opt-Out zugeordnet', resOptOut.matched === true);
  const updatedLead3 = ctx.readLeads_().leads.filter(function (l) {
    return l.Lead_ID === lead3.Lead_ID;
  })[0];
  check('Inbound: Opt-Out setzt Opt_Out=yes und Suppressed=yes',
        updatedLead3.Opt_Out === 'yes' && updatedLead3.Suppressed === 'yes');

  // 5. Nicht zuordenbare Antwort -> NEEDS_REVIEW (kein Raten!)
  const resUnmatched = ctx.processInboundEvent({
    event_id: 'EVT-999',
    event_type: 'REPLY',
    email: 'unbekannt-gibtesnicht@nirgendwo.de',
    subject: 'Hallo'
  });
  check('Inbound: unmatchbares Event erhaelt Status NEEDS_REVIEW',
        resUnmatched.matched === false && resUnmatched.status === 'NEEDS_REVIEW');
  const evtData = SHEETS.INBOUND_EVENTS._data;
  const lastEvt = evtData[evtData.length - 1];
  check('Inbound: unmatchbares Event traegt LEERE Lead-ID (kein Raten)',
        lastEvt[3] === '', 'lead_id=' + lastEvt[3]);
}

function testDryRunsAndArbitraryN() {
  loadRealFlyers();

  // Jordi Dry Runs N=1, N=17, N=100
  [1, 17, 100].forEach(function (n) {
    setupSheet(150, 'JORDI');
    const b = ctx.prepareBatch({ owner: 'JORDI', count: n, campaign: 'dryrun-jordi-' + n });
    const ids = b.leads.map(function (l) { return l.Lead_ID; });
    check('JORDI Dry Run N=' + n + ': REQUESTED_N = ACTUAL_N',
          b.stats.selected_count === n, 'actual=' + b.stats.selected_count);
    check('JORDI Dry Run N=' + n + ': UNIQUE_LEAD_IDS',
          ids.length === new Set(ids).size);
    check('JORDI Dry Run N=' + n + ': OWNER_MATCH & NO_CROSSOVER',
          b.leads.every(function (l) { return l.Lead_ID.indexOf('JORDI') >= 0; }));
    check('JORDI Dry Run N=' + n + ': CORRECT_FLYER_SHA',
          b.asset_sha256 === FLYERS_.JORDI.sha256);
  });

  // Joel Dry Runs N=1, N=17, N=100
  [1, 17, 100].forEach(function (n) {
    setupSheet(150, 'JOEL');
    const b = ctx.prepareBatch({ owner: 'JOEL', count: n, campaign: 'dryrun-joel-' + n });
    const ids = b.leads.map(function (l) { return l.Lead_ID; });
    check('JOEL Dry Run N=' + n + ': REQUESTED_N = ACTUAL_N',
          b.stats.selected_count === n, 'actual=' + b.stats.selected_count);
    check('JOEL Dry Run N=' + n + ': UNIQUE_LEAD_IDS',
          ids.length === new Set(ids).size);
    check('JOEL Dry Run N=' + n + ': OWNER_MATCH & NO_CROSSOVER',
          b.leads.every(function (l) { return l.Lead_ID.indexOf('JOEL') >= 0; }));
    check('JOEL Dry Run N=' + n + ': CORRECT_FLYER_SHA',
          b.asset_sha256 === FLYERS_.JOEL.sha256);
  });
}

/* ---------------------------------------------------------------- main */

console.log('='.repeat(70));
console.log('HSB SALES OS - APPS-SCRIPT-TESTS (ausgelieferter Code, Node + Stubs)');
console.log('='.repeat(70));

[testAssetGate, testEligibility, testDynamicCounts, testGateNotBypassable,
 testEmptyBatchExplained, testEmailDedup, testNoCrossSender, testEmlStructure,
 testQualifyAndDedupWrite, testSuppression, testDuplicateBatchProtection,
 testDashboard, testEmlExportChunking, testFollowUps, testEnsureColumns,
 testSetupState, testBatchListe, testSuche,
 testLockServiceAndConcurrency, testIdempotency, testInboundEvents,
 testDryRunsAndArbitraryN].forEach(function (fn) {
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
