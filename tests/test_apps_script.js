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
let REAL_SEND_CALLS = 0;

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
    getValue: function () { return this.getValues()[0][0]; },
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
    // Ordner nach Namen persistiert, wie Drive es tut. Vorher gab
    // getFoldersByName() immer "nicht gefunden" zurueck, sodass jeder Aufruf
    // von getOrCreateFolder_() einen NEUEN Ordner mit leerem Dateibestand
    // anlegte - der Wiederholungsschutz (getFilesByName) griff dadurch nie
    // wirklich, der bestehende Test dazu war ein Scheingruen. Echte Drive-
    // Ordner sind pro Name eindeutig; das bildet dieser Stub jetzt ab.
    _folders: {},
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
    getFoldersByName: function (name) {
      const f = DriveApp._folders[name];
      let geliefert = false;
      return {
        hasNext: function () { return !!f && !geliefert; },
        next: function () { geliefert = true; return f; }
      };
    },
    // Der Ordner merkt sich angelegte Dateien, damit getFilesByName wie in
    // Drive antwortet. Nur so laesst sich pruefen, dass ein Wiederholungs-
    // versuch kein zweites gleichnamiges ZIP erzeugt.
    createFolder: function (name) {
      const dateien = {};
      const ordner = {
        _dateien: dateien,
        createFile: function (blob) {
          const n = blob._name || 'x.zip';
          const datei = {
            getUrl: function () { return 'https://example.invalid/f'; },
            getName: function () { return n; },
            getSize: function () { return 1024; }
          };
          dateien[n] = (dateien[n] || 0) + 1;
          ordner._letzte = datei;
          return datei;
        },
        getFilesByName: function (n) {
          const da = Object.prototype.hasOwnProperty.call(dateien, n);
          let geliefert = false;
          return {
            hasNext: function () { return da && !geliefert; },
            next: function () {
              geliefert = true;
              return { getUrl: function () { return 'https://example.invalid/f'; },
                       getName: function () { return n; },
                       getSize: function () { return 1024; } };
            }
          };
        },
        getUrl: function () { return 'https://example.invalid/folder'; }
      };
      DriveApp._folders[name] = ordner;
      DriveApp._letzterOrdner = ordner;
      return ordner;
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
  MailApp: { sendEmail: function () { REAL_SEND_CALLS++; } },
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
  // Persistierte Drive-Ordner gehoeren nicht zum Sheet-Zustand, muessen aber
  // ebenso pro Test isoliert werden - sonst koennten Batch-ZIPs aus einem
  // frueheren Test faelschlich als "bereits vorhanden" erscheinen.
  DriveApp._folders = {};
}

function loadRealFlyers() {
  const map = {
    '1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV': 'HSB-Flyer-Jordi-Post_FINAL.pdf',
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
  const orig = DriveApp._files['1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV'].bytes;
  DriveApp._files['1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV'] =
    { bytes: Buffer.concat([orig, Buffer.from('x')]) };
  let threw = false;
  try { ctx.getVerifiedFlyer_('JORDI'); } catch (e) {
    threw = /ASSET_GATE=FAIL/.test(e.message);
  }
  check('veraenderter Flyer wird abgewiesen (ASSET_GATE=FAIL)', threw);
  DriveApp._files['1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV'] = { bytes: orig };

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

function testJordi100OneClick() {
  loadRealFlyers();
  setupSheet(120, 'JORDI', {
    'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN'
  });

  const r = ctx.uiJordi100({ request_id: 'test-one-click-1' });
  check('Jordi-100: UI-Aufruf erfolgreich', r.ok === true,
        r.error || 'ok');
  check('Jordi-100: exakt 100 reserviert',
        r.ok && r.data.batch.stats.selected_count === 100,
        r.ok ? 'selected=' + r.data.batch.stats.selected_count : 'kein Batch');
  check('Jordi-100: exakt 100 neutral freigegeben',
        r.ok && r.data.batch.approval.newly_approved === 100,
        r.ok ? 'approved=' + r.data.batch.approval.newly_approved : 'kein Batch');
  check('Jordi-100: Status bleibt PREPARED',
        r.ok && r.data.batch.status === 'PREPARED');
  // Die Freigabe erzeugt bewusst noch keine Pakete: 100 Mails mit je 1,5 MB
  // Anhang sind rund 200 MB Base64 und sprengen die Laufzeitgrenze von Apps
  // Script. Die Oberflaeche holt sie anschliessend in Bloecken zu 20 nach.
  check('Jordi-100: Freigabe erzeugt noch keine Pakete',
        r.ok && r.data.export === null,
        r.ok ? 'export=' + JSON.stringify(r.data.export) : 'kein Batch');

  // uiExportEml wird von der Seitenleiste mit zwei Einzelwerten aufgerufen,
  // nicht mit einem Objekt. Genau diese Abweichung liess den Knopf
  // "Entwuerfe erzeugen" frueher immer scheitern.
  const x = ctx.uiExportEml(r.data.batch.batch_id, 0);
  check('Export: Aufruf mit Einzelwerten funktioniert', x.ok === true,
        x.error || 'ok');
  let idx = x.ok ? x.data.next_index : null, ges = x.ok ? x.data.written : 0;
  let pakete = 1, schutz = 0;
  while (idx !== null && schutz++ < 30) {
    const w = ctx.uiExportEml(r.data.batch.batch_id, idx);
    if (!w.ok) break;
    ges += w.data.written; idx = w.data.next_index; pakete++;
  }
  check('Export: 100 Outlook-Entwuerfe ueber die Schleife erzeugt',
        ges === 100, 'written=' + ges + ' in ' + pakete + ' Aufrufen');
  check('Export: zehn Pakete zu je hoechstens zehn Entwuerfen',
        pakete === 10, 'pakete=' + pakete);
  check('Export: ohne Batch-Kennung sauberer Fehler statt Absturz',
        ctx.uiExportEml('', 0).ok === false);

  check('Jordi-100: keine Send-Action aufgerufen', REAL_SEND_CALLS === 0,
        'send calls=' + REAL_SEND_CALLS);

  const legalCol = HEADER.indexOf('Legal_Basis');
  const releaseCol = HEADER.indexOf('Versandfreigabe');
  const batchCol = HEADER.indexOf('Batch_ID');
  const rows = SHEETS.ALL_LEADS._data.slice(1);
  const reserved = rows.filter(function (x) { return x[batchCol]; });
  const untouched = rows.filter(function (x) { return !x[batchCol]; });
  check('Jordi-100: reservierte Leads tragen OWNER_APPROVED',
        reserved.length === 100
          && reserved.every(function (x) { return x[legalCol] === 'OWNER_APPROVED'; }));
  check('Jordi-100: reservierte Leads tragen Versandfreigabe=yes',
        reserved.every(function (x) { return x[releaseCol] === 'yes'; }));
  check('Jordi-100: Rest bleibt unveraendert fail-closed',
        untouched.length === 20
          && untouched.every(function (x) {
            return x[legalCol] === 'UNKNOWN' && x[releaseCol] === 'no';
          }));

  const batchesBefore = SHEETS.BATCHES._data.length;
  const retry = ctx.uiJordi100({ request_id: 'test-one-click-1' });
  check('Jordi-100: Retry ist idempotent',
        retry.ok && retry.data.batch.already_processed === true);
  check('Jordi-100: Retry legt keinen zweiten Batch an',
        SHEETS.BATCHES._data.length === batchesBefore);
  check('Jordi-100: Retry erzeugt keine doppelten ZIPs',
        retry.ok && retry.data.export === null);
}

function testJordi100SafetyGates() {
  loadRealFlyers();
  setupSheet(110, 'JORDI', {
    'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN'
  });
  const idx = function (name) { return HEADER.indexOf(name); };
  const data = SHEETS.ALL_LEADS._data;

  data[1][idx('Opt-out-Status')] = 'yes';
  data[2][idx('Suppressed')] = 'yes';
  data[3][idx('Bounce_Status')] = 'hard_bounce';
  data[4][idx('Send_Status')] = 'sent';
  data[5][idx('E-Mail')] = 'ungueltig';
  data[6][idx('Verantwortlicher')] = 'Joel Cherino Diaz';
  data[7][idx('Legal_Basis')] = 'BLOCKED';
  data[8][idx('E-Mail')] = data[9][idx('E-Mail')];
  data[10][idx('Batch_ID')] = 'ACTIVE-JORDI-1';
  SHEETS.BATCHES._data = [
    ['Batch_ID', 'Owner', 'Campaign', 'Status', 'Requested', 'Selected',
     'Eligible', 'Excluded', 'Shortfall', 'Asset_SHA256', 'Created_At',
     'Approved_At', 'Sent_At'],
    ['ACTIVE-JORDI-1', 'JORDI', '', 'PREPARED', 1, 1, 1, 0, 0, '', '', '', '']
  ];
  ctx.invalidateLeadsCache_();

  const r = ctx.approveAndPrepareJordi100({ request_id: 'safety-gates-1' });
  const ids = new Set(r.leads.map(function (l) { return l.Lead_ID; }));
  check('Jordi-100 Gates: trotz Sperrfaellen exakt 100 sichere Leads',
        r.stats.selected_count === 100, 'selected=' + r.stats.selected_count);
  [1, 2, 3, 4, 5, 6, 7, 8, 10].forEach(function (n) {
    check('Jordi-100 Gates: TEST-JORDI-' + n + ' ausgeschlossen',
          !ids.has('TEST-JORDI-' + n));
  });
  const emails = r.leads.map(function (l) { return l.Email.toLowerCase(); });
  check('Jordi-100 Gates: E-Mail-Dedupe aktiv',
        emails.length === new Set(emails).size);

  setupSheet(99, 'JORDI', {
    'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN'
  });
  const short = ctx.approveAndPrepareJordi100({ request_id: 'shortfall-1' });
  check('Jordi-100 Shortfall: Vorgang blockiert',
        short.status === 'BLOCKED_EXACT_100');
  check('Jordi-100 Shortfall: null Zeilen veraendert',
        SHEETS.ALL_LEADS._data.slice(1).every(function (x) {
          return x[idx('Legal_Basis')] === 'UNKNOWN'
            && x[idx('Versandfreigabe')] === 'no'
            && !x[idx('Batch_ID')];
        }));
  check('Jordi-100 Shortfall: kein Batch angelegt',
        SHEETS.BATCHES._data.length === 0);

  setupSheet(120, 'JORDI', {
    'Versandfreigabe': 'no', 'Legal_Basis': 'UNKNOWN'
  });
  sandbox.LockService._forceTimeout = true;
  let lockBlocked = false;
  try {
    ctx.approveAndPrepareJordi100({ request_id: 'lock-timeout-1' });
  } catch (e) {
    lockBlocked = /LOCK_TIMEOUT/.test(e.message);
  } finally {
    sandbox.LockService._forceTimeout = false;
  }
  check('Jordi-100 Lock: Timeout blockiert fail-closed', lockBlocked);
  check('Jordi-100 Lock: Timeout hinterlaesst null Writes',
        SHEETS.ALL_LEADS._data.slice(1).every(function (x) {
          return x[idx('Legal_Basis')] === 'UNKNOWN'
            && x[idx('Versandfreigabe')] === 'no'
            && !x[idx('Batch_ID')];
        }));
}

function testJordi100UiContract() {
  const sidebar = fs.readFileSync(path.join(AS, 'Sidebar.html'), 'utf8');
  check('Jordi-100 UI: Schnellstart oben vorhanden',
        /Jordi · 100 Outlook-Entwürfe/.test(sidebar));
  check('Jordi-100 UI: eindeutiger Ein-Klick-Button',
        /100 freigeben &amp; Entwürfe erzeugen/.test(sidebar));
  check('Jordi-100 UI: serverseitiger Wrapper verdrahtet',
        /\.uiJordi100\(\{ request_id: jordi100RequestId \}\)/.test(sidebar));
  check('Jordi-100 UI: alter Freigabedialog fuer Jordi initial verborgen',
        /<details class="schritt" id="s1" style="display:none">/.test(sidebar));
  check('Jordi-100 UI: keine Prospect-Send-Action eingebaut',
        !/(sendEmail|SendEmailV2|GmailApp|SendDraftEmail)/.test(sidebar));
}

/**
 * Deckt die zwei Klassen von Oberflaechen-Fehlern ab, die der unabhaengige
 * Review verlangt: den haengenden Spinner (Erfolgshandler ohne Fehlerhandler)
 * und den manuellen Weiterklick fuer etwas, das automatisch weiterlaufen
 * sollte. Beides ist eine reine Textpruefung gegen die ausgelieferte
 * Sidebar.html - es gibt keinen Browser in dieser Testumgebung.
 */
function testSidebarFailureHandling() {
  const sidebar = fs.readFileSync(path.join(AS, 'Sidebar.html'), 'utf8');

  function ketteVor(name) {
    const idx = sidebar.search(new RegExp('\\.' + name + '\\('));
    if (idx < 0) return null;
    const start = sidebar.lastIndexOf('google.script.run', idx);
    return start < 0 ? null : sidebar.slice(start, idx);
  }

  // Jeder dieser Aufrufe setzt vorher eine Ladeanzeige und veraendert
  // Server-Zustand. Ohne withFailureHandler haengt die Anzeige bei einem
  // echten Apps-Script-Fehler (Timeout, Ausnahme ausserhalb try/catch) fuer
  // immer - der reine {ok:false}-Zweig im Erfolgshandler faengt das nicht,
  // weil ein Plattformfehler den Erfolgshandler gar nicht erst aufruft.
  ['uiEnsureColumns', 'uiQualify', 'uiPrepareBatch', 'uiJordi100',
   'uiExportEml', 'uiGetBatches', 'uiGetSetupState', 'uiApproveBatch',
   'uiSetStatus', 'uiGetDue', 'uiSearch', 'uiConfirmBatchSent'
  ].forEach(function (name) {
    const kette = ketteVor(name);
    check('Kritischer Aufruf ' + name + ' hat withFailureHandler',
          !!kette && /withFailureHandler/.test(kette),
          kette ? 'gefunden, aber ohne Fehlerhandler' : 'Aufruf nicht gefunden');
  });

  // Fruehere Fassung verlangte einen manuellen Klick auf "Weiter ab X" fuer
  // jedes einzelne Teilpaket - bei zehn Teilpaketen also neun Klicks. Die
  // Erzeugung muss sich nach einem Erfolg selbst fortsetzen.
  const emlExportBody = (function () {
    const start = sidebar.indexOf('function emlExport(');
    if (start < 0) return '';
    let tiefe = 0, i = start, began = false, out = '';
    for (; i < sidebar.length; i++) {
      const c = sidebar[i];
      if (c === '{') { tiefe++; began = true; }
      if (began) out += c;
      if (c === '}') { tiefe--; if (began && tiefe === 0) break; }
    }
    return out;
  })();
  check('emlExport-Funktion gefunden', emlExportBody.length > 0);
  check('Erfolgsfall ruft bei unvollstaendigem Batch automatisch das naechste '
        + 'Teilpaket ab (kein Klick noetig)',
        /!d\.complete[\s\S]{0,400}emlExport\(/.test(emlExportBody));
  check('Ein Fehlschlag bietet einen Wiederholen-Knopf statt bei Null neu zu '
        + 'starten',
        /withFailureHandler[\s\S]*onclick="emlExport\(/.test(emlExportBody)
        || /onclick="emlExport\([^,]+,\s*von/.test(emlExportBody));
  check('Parallelaufrufe fuer denselben Batch werden clientseitig verhindert '
        + '(Doppelklick-Schutz)',
        /exportLaufend/.test(emlExportBody) || /exportAktiv/.test(emlExportBody));
  check('Keine veraltete feste Paketgroesse "je 20" mehr im Text',
        !/je 20/.test(sidebar));
  check('Keine veraltete feste Paketanzahl "fuenf" mehr im Jordi-100-Text '
        + '(EML_CHUNK_SIZE bestimmt die tatsaechliche Anzahl)',
        !/f[üu]nf Outlook-Pakete/.test(sidebar));
}

function testSidebarServerContract() {
  setupSheet(3, 'JORDI');
  const dashboard = ctx.uiGetDashboard();
  check('Sidebar-Contract: uiGetDashboard vorhanden und erfolgreich',
        dashboard.ok && dashboard.data.owners.JORDI.total === 3);
  const filters = ctx.uiGetFilters();
  check('Sidebar-Contract: uiGetFilters vorhanden und erfolgreich',
        filters.ok && Array.isArray(filters.data.industries)
          && filters.data.industries.indexOf('Lebensmittelindustrie') >= 0);

  // Jeder Serveraufruf der Seitenleiste muss existieren. Fehlt einer, wirft
  // google.script.run synchron und die gesamte Ladekette bricht ab -
  // einschliesslich der Sicherheitswarnungen.
  const sidebar = fs.readFileSync(path.join(AS, 'Sidebar.html'), 'utf8');
  const aufrufe = {};
  const re = /\.\s*(ui[A-Za-z0-9_]*)\s*\(/g;
  let m;
  while ((m = re.exec(sidebar)) !== null) aufrufe[m[1]] = true;
  const namen = Object.keys(aufrufe).sort();
  check('Sidebar-Contract: mindestens zehn Serveraufrufe geprueft',
        namen.length >= 10, 'gefunden=' + namen.length);
  namen.forEach(function (name) {
    check('Sidebar-Contract: ' + name + ' serverseitig definiert',
          typeof ctx[name] === 'function');
  });

  // Nicht nur ob die Funktion existiert, sondern ob sie so aufgerufen wird,
  // wie sie deklariert ist. uiExportEml wurde mit zwei Einzelwerten gerufen,
  // erwartete aber ein Objekt - der Knopf konnte nie funktionieren, und der
  // reine Existenztest oben hat das nicht bemerkt.
  aufrufe.__stellen__ = undefined;
  delete aufrufe.__stellen__;
  const argRe = /\.\s*(ui[A-Za-z0-9_]*)\s*\(/g;
  let a;
  while ((a = argRe.exec(sidebar)) !== null) {
    const name = a[1];
    if (typeof ctx[name] !== 'function') continue;
    // Argumenttext bis zur passenden schliessenden Klammer einsammeln.
    let tiefe = 1, i = argRe.lastIndex, text = '';
    while (i < sidebar.length && tiefe > 0) {
      const c = sidebar[i];
      if (c === '(') tiefe++;
      else if (c === ')') tiefe--;
      if (tiefe > 0) text += c;
      i++;
    }
    // Kommas nur auf oberster Ebene zaehlen.
    let ebene = 0, uebergeben = text.trim() ? 1 : 0;
    for (const c of text) {
      if ('([{'.indexOf(c) >= 0) ebene++;
      else if (')]}'.indexOf(c) >= 0) ebene--;
      else if (c === ',' && ebene === 0) uebergeben++;
    }
    const erwartet = ctx[name].length;
    check('Sidebar-Contract: ' + name + ' Argumentzahl passt',
          uebergeben <= erwartet,
          'uebergeben=' + uebergeben + ' deklariert=' + erwartet);
  }

  // Beide Handler muessen das {ok,data}-Format auspacken.
  check('Sidebar-Contract: cockpitLaden prueft r.ok',
        /function cockpitLaden\(\)[\s\S]{0,220}if \(!r\.ok\)/.test(sidebar));
  check('Sidebar-Contract: filterLaden prueft r.ok',
        /function filterLaden\(\)[\s\S]{0,200}if \(!r \|\| !r\.ok\)/.test(sidebar));
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

  // Ein Aufruf erzeugt genau ein Teilpaket. Das begrenzt den Speicherbedarf
  // eines Laufs und macht den Fortschritt sichtbar. Die Oberflaeche ruft
  // nach, bis complete wahr ist - genau das wird hier nachgefahren.
  const erste = ctx.exportBatchAsEmlZip(b.batch_id, 0);
  check('Export liefert genau ein Teilpaket pro Aufruf',
        erste.parts.length === 1, erste.parts.length + ' Pakete');
  check('erstes Teilpaket hat Paketgroesse', erste.written === 10,
        'written=' + erste.written);
  check('Export noch nicht vollstaendig', erste.complete === false);
  check('Fortsetzungsindex genannt', erste.next_index === 10,
        'next=' + erste.next_index);
  check('Teilnummerierung ausgewiesen',
        erste.part_index === 1 && erste.part_total === 5,
        erste.part_index + '/' + erste.part_total);
  check('Export nennt den Asset-Hash',
        erste.asset_sha256 === FLYERS_.JORDI.sha256);

  let index = erste.next_index, summe = erste.written, runden = 1;
  const namen = { };
  erste.parts.forEach(function (x) { namen[x.name] = true; });
  while (index !== null && runden < 20) {
    const r = ctx.exportBatchAsEmlZip(b.batch_id, index);
    summe += r.written;
    r.parts.forEach(function (x) { namen[x.name] = true; });
    index = r.next_index;
    runden++;
  }
  check('Schleife deckt alle Entwuerfe ab', summe === 45,
        'summe=' + summe + ' in ' + runden + ' Aufrufen');
  check('genau fuenf verschiedene Teilpakete',
        Object.keys(namen).length === 5, Object.keys(namen).join(','));
  check('Schleife endet von selbst', index === null);

  // Ein Wiederholungsversuch darf kein zweites gleichnamiges ZIP anlegen.
  const nochmal = ctx.exportBatchAsEmlZip(b.batch_id, 0);
  check('Wiederholung legt kein zweites ZIP an',
        DriveApp._letzterOrdner._dateien[nochmal.parts[0].name] === 1,
        'Anlagen=' + DriveApp._letzterOrdner._dateien[nochmal.parts[0].name]);

  // Ueber das Ende hinaus darf nichts kaputtgehen.
  const dahinter = ctx.exportBatchAsEmlZip(b.batch_id, 45);
  check('Aufruf hinter dem Ende meldet vollstaendig',
        dahinter.complete === true && dahinter.written === 0);
}

/**
 * Zwei Randfaelle, die reine Existenzpruefung nicht abdeckt:
 *
 * 1. Ein Drive-Fehler mitten in der Paketfolge darf nur das eine betroffene
 *    Paket kosten - bereits fertige Pakete bleiben unberuehrt, und ein
 *    Wiederholungsversuch legt genau das fehlende Paket nach, nicht die
 *    schon vorhandenen erneut.
 * 2. Ein Client, der eine erfolgreiche Antwort "verliert" (Reload,
 *    abgebrochener Callback) und deshalb wieder bei Index 0 anfragt, darf
 *    keine Duplikate erzeugen - er muss die bereits erzeugten Pakete
 *    wiederfinden statt sie neu anzulegen.
 */
function testExportRetryAndRecovery() {
  loadRealFlyers();
  setupSheet(23, 'JORDI');
  const b = ctx.prepareBatch({ owner: 'JORDI', count: 23 });
  check('Batch fuer Retry-Test vorbereitet (3 Teilpakete: 10/10/3)',
        b.stats.selected_count === 23);

  const teil1 = ctx.exportBatchAsEmlZip(b.batch_id, 0);
  check('Teil 1 erzeugt', teil1.written === 10 && teil1.complete === false);

  const ordner = DriveApp._letzterOrdner;
  const teil1Name = b.batch_id + '_teil01.zip';
  const teil2Name = b.batch_id + '_teil02.zip';
  const teil3Name = b.batch_id + '_teil03.zip';
  const echtCreateFile = ordner.createFile;
  ordner.createFile = function (blob) {
    if (blob._name === teil2Name) {
      throw new Error('Simulierter Drive-Fehler beim Anlegen von Teil 2');
    }
    return echtCreateFile.call(ordner, blob);
  };

  let fehlerAusgeloest = false;
  try {
    ctx.exportBatchAsEmlZip(b.batch_id, teil1.next_index);
  } catch (e) {
    fehlerAusgeloest = true;
  }
  check('Mitten in der Folge: Fehler bei Teil 2 wird nicht verschluckt',
        fehlerAusgeloest);
  check('Teil 1 bleibt nach dem Fehlschlag unberuehrt',
        ordner._dateien[teil1Name] === 1);
  check('Teil 2 wurde beim Fehlschlag NICHT angelegt',
        !Object.prototype.hasOwnProperty.call(ordner._dateien, teil2Name));

  ordner.createFile = echtCreateFile;
  const retryTeil2 = ctx.exportBatchAsEmlZip(b.batch_id, teil1.next_index);
  check('Wiederholung erzeugt nur das fehlgeschlagene Teil 2',
        retryTeil2.written === 10 && retryTeil2.parts[0].name === teil2Name);
  check('Teil 1 wurde durch den Retry NICHT doppelt angelegt',
        ordner._dateien[teil1Name] === 1);

  const teil3 = ctx.exportBatchAsEmlZip(b.batch_id, retryTeil2.next_index);
  check('Teil 3 (Rest) schliesst den Batch ab',
        teil3.written === 3 && teil3.complete === true);

  const zaehleTeile = function () {
    return [teil1Name, teil2Name, teil3Name].filter(function (n) {
      return Object.prototype.hasOwnProperty.call(ordner._dateien, n);
    }).length;
  };
  check('Nach Fehler und Retry existieren genau drei Teilpakete, keine Duplikate',
        zaehleTeile() === 3, 'gefunden=' + zaehleTeile());

  // --- Szenario 2: verlorene Erfolgsantwort / Reload --------------------
  // Ein Client, der die Antwort zu Teil 1 nie sah (Netzwerkfehler,
  // Sidebar-Reload), fragt nach einem Neustart wieder bei Index 0 an.
  const nachReload = ctx.exportBatchAsEmlZip(b.batch_id, 0);
  check('Reload-Anfrage bei Index 0 liefert Teil 1 erneut, ohne ihn neu anzulegen',
        nachReload.parts[0].name === teil1Name && ordner._dateien[teil1Name] === 1);
  check('Reload-Anfrage meldet korrekt: noch nicht fertig, weiter bei Teil 2',
        nachReload.complete === false && nachReload.next_index === 10);

  // Die Oberflaeche wuerde jetzt automatisch weiterlaufen, bis complete.
  let weiterIndex = nachReload.next_index, schutz = 0;
  while (weiterIndex !== null && schutz++ < 10) {
    const r = ctx.exportBatchAsEmlZip(b.batch_id, weiterIndex);
    weiterIndex = r.next_index;
  }
  check('Nach dem simulierten Reload bleiben es genau drei Teilpakete',
        zaehleTeile() === 3, 'gefunden=' + zaehleTeile());
  check('Kein Teilpaket wurde durch den Reload mehrfach angelegt',
        ordner._dateien[teil1Name] === 1 && ordner._dateien[teil2Name] === 1
        && ordner._dateien[teil3Name] === 1);
}

/**
 * Belegt die Wiederaufnahme, wenn die Oberflaeche eine erfolgreiche Antwort
 * "verliert" (Netzwerkfehler, Reload, geschlossener Tab): der Server hat den
 * Batch schon committet, bevor er antwortet - ein Reload muss ihn ueber
 * uiGetBatches/getBatches wiederfinden, statt einen zweiten anzulegen.
 */
function testBatchRecoveryAfterLostCallback() {
  setupSheet(30, 'JOEL');
  const erster = ctx.prepareBatch({ owner: 'JOEL', count: 12, campaign: 'lost-callback' });
  check('Batch wurde server-seitig committet', erster.stats.selected_count === 12);

  // "Reload": die Oberflaeche kennt den Batch nicht mehr aus dem Speicher,
  // fragt aber ueber getBatches nach - das liest ausschliesslich das
  // persistierte Blatt BATCHES, nicht Client-Zustand.
  const liste = ctx.getBatches('JOEL', 12);
  const gefunden = liste.filter(function (b) { return b.batch_id === erster.batch_id; });
  check('Reload findet den bereits committeten Batch ueber getBatches',
        gefunden.length === 1, 'Treffer=' + gefunden.length);
  check('Gefundener Batch zeigt die korrekte Anzahl',
        gefunden.length === 1 && gefunden[0].selected === 12);

  // Ein erneuter prepareBatch-Aufruf mit derselben Batch-ID (der
  // Wiederaufnahme-Pfad einer robusten Oberflaeche) darf keinen zweiten
  // Batch anlegen.
  const wiederholt = ctx.prepareBatch({
    owner: 'JOEL', count: 12, campaign: 'lost-callback', batch_id: erster.batch_id
  });
  check('Wiederaufnahme ueber dieselbe Batch-ID meldet already_processed',
        wiederholt.already_processed === true);
  const listeNachher = ctx.getBatches('JOEL', 50);
  const treffer = listeNachher.filter(function (b) { return b.batch_id === erster.batch_id; });
  check('Kein zweiter Batch-Datensatz durch die Wiederaufnahme',
        treffer.length === 1, 'BATCHES-Zeilen=' + treffer.length);
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

  // 3. Derselbe Lock schuetzt auch die Drive-Ordnerpruefung/-Anlage in
  // exportBatchAsEmlZip - ohne ihn koennten zwei echte Parallelaufrufe fuer
  // denselben Batch beide "Datei nicht vorhanden" sehen (siehe
  // testExportRetryAndRecovery fuer den sequentiellen Retry-Nachweis).
  loadRealFlyers();
  const expBatch = ctx.prepareBatch({ owner: 'JORDI', count: 3 });
  sandbox.LockService._forceTimeout = true;
  let exportLockFailed = false;
  try {
    ctx.exportBatchAsEmlZip(expBatch.batch_id, 0);
  } catch (e) {
    exportLockFailed = /LOCK_TIMEOUT/.test(e.message);
  }
  check('exportBatchAsEmlZip: LockService-Timeout wird fail-closed abgewiesen',
        exportLockFailed);
  sandbox.LockService._forceTimeout = false;
  const expDochOk = ctx.exportBatchAsEmlZip(expBatch.batch_id, 0);
  check('exportBatchAsEmlZip: nach Freigabe der Sperre funktioniert der Export',
        expDochOk.written === 3 && expDochOk.complete === true);
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

/**
 * Post-Send-Reconciliation: ein SENT-Event darf nur bei starker,
 * bewegungsstabiler Korrelation (Internet_Message_ID / explizite Lead-ID)
 * den Status aendern - nie ueber E-Mail-Adresse oder ueber eine ID, die sich
 * beim Verschieben Entwurf -> Gesendete Objekte aendern kann
 * (Outlook_Message_ID/Draft_ID allein reicht nicht). Erneutes Einspielen darf
 * niemals eine zweite Statusaenderung, Aktivitaet oder Wiedervorlage
 * erzeugen. ZIP/EML/Entwurf duerfen SENT niemals implizieren.
 */
function testPostSendReconciliation() {
  loadRealFlyers();
  setupSheet(20, 'JORDI');

  const b = ctx.prepareBatch({ owner: 'JORDI', count: 5, batch_id: 'HSB-20260827-JORDI-RECON1' });
  const lead1 = b.leads[0];
  const lead2 = b.leads[1];
  const lead4 = b.leads[3];
  const read0 = ctx.readLeads_();

  const setCol = function (lead, field, value) {
    const l = read0.leads.filter(function (x) { return x.Lead_ID === lead.Lead_ID; })[0];
    SHEETS.ALL_LEADS._data[l._row - 1][read0.index[field]] = value;
  };
  setCol(lead1, 'Internet_Message_ID', '<msg-sent-001@hsb-boden.de>');
  setCol(lead2, 'Internet_Message_ID', '<msg-sent-002@hsb-boden.de>');
  // lead4 hat NUR eine Outlook_Message_ID (Drive-/Graph-Element-ID) - genau
  // der Fall, in dem sich die ID beim Verschieben nach "Gesendete Objekte"
  // aendern kann. Ohne Internet_Message_ID darf daraus kein Treffer werden.
  setCol(lead4, 'Outlook_Message_ID', 'AAMkAGdriftable==');
  ctx.invalidateLeadsCache_();

  // Exporte/Entwuerfe duerfen SENT niemals implizieren.
  ctx.exportBatchAsEmlZip(b.batch_id, 0);
  const afterExport = ctx.readLeads_().leads.filter(function (l) {
    return l.Batch_ID === b.batch_id;
  });
  check('Reconciliation: EML-Export impliziert kein SENT',
        afterExport.every(function (l) { return String(l.Send_Status || '').toLowerCase() !== 'sent'; }));

  // 1. Echter Sendenachweis ueber Internet_Message_ID -> genau einmal SENT
  const actBefore = SHEETS.ACTIVITIES._data.length;
  const res1 = ctx.processInboundEvent({
    event_id: 'EVT-SENT-001',
    event_type: 'SENT',
    message_id: '<msg-sent-001@hsb-boden.de>',
    email: lead1.Email
  });
  check('Reconciliation: SENT-Event ueber Internet_Message_ID zugeordnet',
        res1.matched === true && res1.lead_id === lead1.Lead_ID, JSON.stringify(res1));

  const l1AfterSent = ctx.readLeads_().leads.filter(function (l) { return l.Lead_ID === lead1.Lead_ID; })[0];
  check('Reconciliation: Send_Status = sent', String(l1AfterSent.Send_Status).toLowerCase() === 'sent',
        l1AfterSent.Send_Status);
  check('Reconciliation: Sent_At gesetzt', !!l1AfterSent.Sent_At);
  check('Reconciliation: Batch_Status = SENT', l1AfterSent.Batch_Status === 'SENT', l1AfterSent.Batch_Status);

  const batchRow1 = SHEETS.BATCHES._data.filter(function (r) { return r[0] === b.batch_id; })[0];
  check('Reconciliation: Batch-Sent_At (Spalte 13) gestempelt', !!batchRow1[12]);
  const stampedAt = batchRow1[12];

  // 2. Wiederholung DERSELBEN Message-ID -> generische Dedup, 0 neue Aktivitaeten
  const res1Replay = ctx.processInboundEvent({
    event_id: 'EVT-SENT-001B',
    event_type: 'SENT',
    message_id: '<msg-sent-001@hsb-boden.de>',
    email: lead1.Email
  });
  check('Reconciliation: Replay derselben Message-ID = DUPLICATE_IGNORED',
        res1Replay.duplicate === true && res1Replay.status === 'DUPLICATE_IGNORED');

  // 3. Zweites, technisch anderes SENT-Event fuer DENSELBEN bereits
  //    gesendeten Lead (andere Event-/Message-ID, z.B. erneuter
  //    Power-Automate-Lauf) -> businessseitig idempotent, 0 doppelte
  //    Aktivitaeten/Statusaenderungen (SENT_STATUS geschieht genau einmal).
  const res1SecondTechnical = ctx.processInboundEvent({
    event_id: 'EVT-SENT-001C',
    event_type: 'SENT',
    lead_id: lead1.Lead_ID,
    message_id: '<msg-sent-001-retrigger@hsb-boden.de>'
  });
  check('Reconciliation: zweites Sendesignal fuer bereits gesendeten Lead ohne erneute Statusaenderung',
        res1SecondTechnical.status === 'ALREADY_SENT_IGNORED');
  check('Reconciliation: DUPLICATE_SEND_ACTIVITY_COUNT = 0',
        SHEETS.ACTIVITIES._data.length === actBefore + 2,
        'activities=' + (SHEETS.ACTIVITIES._data.length - actBefore));

  const batchRow1b = SHEETS.BATCHES._data.filter(function (r) { return r[0] === b.batch_id; })[0];
  check('Reconciliation: Batch-Sent_At bleibt nach erneutem Signal unveraendert',
        batchRow1b[12] === stampedAt);

  // 4. Zweiter GENUINE Sendenachweis (anderer Lead, andere Message-ID) im
  //    selben Batch -> ebenfalls genau einmal SENT, Batch-Sent_At bleibt der
  //    Zeitpunkt des ERSTEN Nachweises (nicht ueberschrieben).
  const res2 = ctx.processInboundEvent({
    event_id: 'EVT-SENT-002',
    event_type: 'SENT',
    message_id: '<msg-sent-002@hsb-boden.de>',
    email: lead2.Email
  });
  check('Reconciliation: zweiter echter Sendenachweis zugeordnet',
        res2.matched === true && res2.lead_id === lead2.Lead_ID);
  const batchRow2 = SHEETS.BATCHES._data.filter(function (r) { return r[0] === b.batch_id; })[0];
  check('Reconciliation: Batch-Sent_At bleibt der erste Zeitstempel',
        batchRow2[12] === stampedAt);

  // 5. Nur bewegungsanfaellige ID (Outlook_Message_ID) vorhanden -> fail-closed
  const res4 = ctx.processInboundEvent({
    event_id: 'EVT-SENT-004',
    event_type: 'SENT',
    message_id: 'AAMkAGdriftable=='
  });
  check('Reconciliation: reine Outlook_Message_ID reicht fuer SENT nicht (NEEDS_REVIEW)',
        res4.matched === false && res4.status === 'NEEDS_REVIEW', JSON.stringify(res4));
  const l4AfterAttempt = ctx.readLeads_().leads.filter(function (l) { return l.Lead_ID === lead4.Lead_ID; })[0];
  check('Reconciliation: Lead4 bleibt unveraendert (kein Raten)',
        String(l4AfterAttempt.Send_Status || '').toLowerCase() !== 'sent');

  // 6. Reine E-Mail-Adresse ohne jede Message-Korrelation -> ebenfalls
  //    fail-closed fuer SENT (kein Beweis, welcher Versand gemeint ist).
  const res5 = ctx.processInboundEvent({
    event_id: 'EVT-SENT-005',
    event_type: 'SENT',
    email: b.leads[2].Email
  });
  check('Reconciliation: E-Mail allein reicht fuer SENT nicht (NEEDS_REVIEW)',
        res5.matched === false && res5.status === 'NEEDS_REVIEW', JSON.stringify(res5));

  // 7. Ein zunaechst unklarer Sendenachweis (NEEDS_REVIEW, weil dem Lead noch
  //    keine Internet_Message_ID zugeordnet war) darf NICHT dauerhaft als
  //    Duplikat verschluckt werden, sobald die Zuordnung nachtraeglich moeglich
  //    wird (z. B. Internet_Message_ID wird nachgetragen und dieselbe
  //    Message-ID kommt mit neuer Event-ID erneut herein - realistisches
  //    Retry-Verhalten einer externen Automatisierung).
  const lead5 = b.leads[4];
  const resFirstUnclear = ctx.processInboundEvent({
    event_id: 'EVT-SENT-006',
    event_type: 'SENT',
    message_id: '<msg-sent-late-linked@hsb-boden.de>'
  });
  check('Reconciliation: Sendenachweis ohne bekannte Internet_Message_ID zunaechst NEEDS_REVIEW',
        resFirstUnclear.matched === false && resFirstUnclear.status === 'NEEDS_REVIEW',
        JSON.stringify(resFirstUnclear));

  setCol(lead5, 'Internet_Message_ID', '<msg-sent-late-linked@hsb-boden.de>');
  ctx.invalidateLeadsCache_();

  const resRetryAfterFix = ctx.processInboundEvent({
    event_id: 'EVT-SENT-006B',
    event_type: 'SENT',
    message_id: '<msg-sent-late-linked@hsb-boden.de>'
  });
  check('Reconciliation: nach Nachtrag der Internet_Message_ID wird derselbe Nachweis erneut versucht statt als Duplikat verschluckt',
        resRetryAfterFix.matched === true && resRetryAfterFix.lead_id === lead5.Lead_ID,
        JSON.stringify(resRetryAfterFix));
  const l5AfterRetry = ctx.readLeads_().leads.filter(function (l) { return l.Lead_ID === lead5.Lead_ID; })[0];
  check('Reconciliation: Lead5 nach nachtraeglich moeglicher Zuordnung korrekt SENT',
        String(l5AfterRetry.Send_Status).toLowerCase() === 'sent', l5AfterRetry.Send_Status);
}

/**
 * Betreiber-Bestaetigung ohne jede Microsoft-Integration: confirmBatchSent
 * ist der einzige Weg, SENT ueberhaupt zu setzen, solange kein lebender
 * Sent-Trigger existiert. Muss in Bloecken (CONFIRM_CHUNK_SIZE) laufen,
 * exactly-once sein und den Unterschied zu einem technischen Nachweis im
 * Notiztext erkennbar lassen.
 */
function testOperatorSendConfirmation() {
  loadRealFlyers();
  setupSheet(30, 'JORDI');

  const b = ctx.prepareBatch({ owner: 'JORDI', count: 25, batch_id: 'HSB-20260827-JORDI-CONFIRM1' });
  check('Betreiber-Bestaetigung: Testbatch hat 25 Leads', b.leads.length === 25);

  const actBefore = SHEETS.ACTIVITIES._data.length;

  const teil1 = ctx.confirmBatchSent(b.batch_id, 0);
  check('Betreiber-Bestaetigung: erster Abschnitt bestaetigt genau CONFIRM_CHUNK_SIZE',
        teil1.verarbeitet === 20 && teil1.neu_bestaetigt === 20 && teil1.complete === false,
        JSON.stringify(teil1));
  check('Betreiber-Bestaetigung: next_index zeigt auf den Rest',
        teil1.next_index === 20, teil1.next_index);

  const teil2 = ctx.confirmBatchSent(b.batch_id, teil1.next_index);
  check('Betreiber-Bestaetigung: zweiter Abschnitt schliesst den Batch ab',
        teil2.verarbeitet === 5 && teil2.neu_bestaetigt === 5 && teil2.complete === true
          && teil2.next_index === null, JSON.stringify(teil2));

  const alleNachher = ctx.readLeads_().leads.filter(function (l) {
    return l.Batch_ID === b.batch_id;
  });
  check('Betreiber-Bestaetigung: alle 25 Leads jetzt Send_Status=sent',
        alleNachher.length === 25 && alleNachher.every(function (l) {
          return String(l.Send_Status).toLowerCase() === 'sent';
        }));
  check('Betreiber-Bestaetigung: alle 25 Leads haben Sent_At',
        alleNachher.every(function (l) { return !!l.Sent_At; }));
  check('Betreiber-Bestaetigung: Notiz unterscheidet sich klar von einem '
        + 'technischen Sendenachweis (kein Systembeleg vorgetaeuscht)',
        alleNachher.every(function (l) {
          return String(l.Notes || '').indexOf('Betreiber-Bestaetigung') >= 0;
        }));

  const batchRow = SHEETS.BATCHES._data.filter(function (r) { return r[0] === b.batch_id; })[0];
  check('Betreiber-Bestaetigung: Batch-Sent_At gestempelt', !!batchRow[12]);

  // Replay des ersten Abschnitts (z. B. versehentlicher Doppelklick nach
  // Seitenreload) darf keine einzige zusaetzliche Aktivitaet erzeugen.
  const teil1Replay = ctx.confirmBatchSent(b.batch_id, 0);
  check('Betreiber-Bestaetigung: Replay meldet alle als bereits gesendet',
        teil1Replay.bereits_gesendet === 20 && teil1Replay.neu_bestaetigt === 0,
        JSON.stringify(teil1Replay));
  check('Betreiber-Bestaetigung: Replay erzeugt keine zusaetzlichen ACTIVITIES-Zeilen '
        + 'ueber die urspruenglichen 25 Bestaetigungen hinaus',
        SHEETS.ACTIVITIES._data.length === actBefore + 25 * 2,
        'activities=' + (SHEETS.ACTIVITIES._data.length - actBefore));
}

function testDryRunsAndArbitraryN() {
  loadRealFlyers();

  // Jordi Dry Runs N=1, N=17, N=25, N=100, N=150
  [1, 17, 25, 100, 150].forEach(function (n) {
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

  // Joel Dry Runs N=1, N=17, N=25, N=100, N=150
  [1, 17, 25, 100, 150].forEach(function (n) {
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


function testActivity12ColumnContract() {
  setupSheet(10, 'JORDI');
  SHEETS.ACTIVITIES._data = [];
  
  // Test direct logActivity_ call with PREPARED event and structured batch ID
  ctx.logActivity_('HSB-20260826-JORDI-0001', 'PREPARED', '94 Leads reserviert fuer JORDI');
  
  check('ACTIVITIES: Header wird mit 12 Spalten angelegt',
        SHEETS.ACTIVITIES._data.length >= 2 && SHEETS.ACTIVITIES._data[0].length === 12);
  
  const header = SHEETS.ACTIVITIES._data[0];
  const expectedHeader = [
    'Activity_ID', 'Lead_ID', 'Timestamp', 'Owner', 'Activity_Type',
    'Channel', 'Result', 'Template_ID', 'Batch_ID', 'Note',
    'Next_Action', 'Next_Action_Date'
  ];
  check('ACTIVITIES: Exakte 12-Spalten-Namen',
        expectedHeader.every(function (h, idx) { return header[idx] === h; }));
        
  const firstRow = SHEETS.ACTIVITIES._data[1];
  check('ACTIVITIES: Erste Zeile hat genau 12 Felder', firstRow.length === 12);
  check('ACTIVITIES: Activity_ID beginnt mit ACT-', firstRow[0].startsWith('ACT-'));
  check('ACTIVITIES: Lead_ID ist leer', firstRow[1] === '');
  check('ACTIVITIES: Timestamp ist ISO-String', /^\d{4}-\d{2}-\d{2}T/.test(firstRow[2]));
  check('ACTIVITIES: Owner deterministisch als JORDI abgeleitet', firstRow[3] === 'JORDI');
  check('ACTIVITIES: Activity_Type gesetzt', firstRow[4] === 'PREPARED');
  check('ACTIVITIES: Channel ist SYSTEM', firstRow[5] === 'SYSTEM');
  check('ACTIVITIES: Result ist leer', firstRow[6] === '');
  check('ACTIVITIES: Template_ID ist leer', firstRow[7] === '');
  check('ACTIVITIES: Batch_ID korrekt zugeordnet', firstRow[8] === 'HSB-20260826-JORDI-0001');
  check('ACTIVITIES: Note gesetzt', firstRow[9] === '94 Leads reserviert fuer JORDI');
  check('ACTIVITIES: Next_Action ist leer', firstRow[10] === '');
  check('ACTIVITIES: Next_Action_Date ist leer', firstRow[11] === '');
  
  // Test direct logActivity_ call with QUALIFY event (empty batch ID)
  ctx.logActivity_('', 'QUALIFY', '50 Leads qualifiziert');
  const qualifyRow = SHEETS.ACTIVITIES._data[2];
  check('ACTIVITIES: QUALIFY Zeile hat genau 12 Felder', qualifyRow.length === 12);
  check('ACTIVITIES: QUALIFY Owner ist fail-safe leer (kein Raten)', qualifyRow[3] === '');
  check('ACTIVITIES: QUALIFY Activity_Type ist QUALIFY', qualifyRow[4] === 'QUALIFY');
  check('ACTIVITIES: QUALIFY Result ist leer', qualifyRow[6] === '');
  check('ACTIVITIES: QUALIFY Batch_ID ist leer', qualifyRow[8] === '');
  check('ACTIVITIES: QUALIFY Note ist 50 Leads qualifiziert', qualifyRow[9] === '50 Leads qualifiziert');

  // Test appendActivityRow_ directly with Lead_ID and explicit fields
  ctx.appendActivityRow_({
    leadId: 'HSB-20260708-00001',
    owner: 'JORDI',
    activityType: 'NOTE_EDITED',
    channel: 'MANUAL',
    result: 'SAVED',
    note: 'Kunde angerufen',
    nextAction: 'Wiedervorlage',
    nextActionDate: '2026-09-01'
  });
  
  const thirdRow = SHEETS.ACTIVITIES._data[3];
  check('ACTIVITIES: Dritte Zeile hat genau 12 Felder', thirdRow.length === 12);
  check('ACTIVITIES: Lead_ID gesetzt', thirdRow[1] === 'HSB-20260708-00001');
  check('ACTIVITIES: Owner normalisiert', thirdRow[3] === 'JORDI');
  check('ACTIVITIES: Result ist SAVED', thirdRow[6] === 'SAVED');
  check('ACTIVITIES: Next_Action gesetzt', thirdRow[10] === 'Wiedervorlage');
  check('ACTIVITIES: Next_Action_Date gesetzt', thirdRow[11] === '2026-09-01');

  // Test Schema Mismatch Fail-Closed
  const brokenSheet = {
    _data: [['Timestamp', 'Batch_ID', 'Type', 'Message', 'User']],
    getLastRow: function () { return this._data.length; },
    getLastColumn: function () { return this._data[0].length; },
    getRange: function () {
      const self = this;
      return {
        getValues: function () { return [self._data[0]]; },
        setFontWeight: function () { return this; },
        setBackground: function () { return this; }
      };
    },
    setFrozenRows: function () {},
    appendRow: function (r) { this._data.push(r); }
  };
  const oldActSheet = SHEETS.ACTIVITIES;
  SHEETS.ACTIVITIES = brokenSheet;
  let mismatchCaught = false;
  try {
    ctx.logActivity_('HSB-20260826-JORDI-0001', 'PREPARED', 'Test');
  } catch (err) {
    if (err.message && err.message.indexOf('ACTIVITY_SCHEMA_MISMATCH') !== -1) {
      mismatchCaught = true;
    }
  }
  SHEETS.ACTIVITIES = oldActSheet;
  check('ACTIVITIES: Schema-Mismatch fuehrt zu fail-closed ACTIVITY_SCHEMA_MISMATCH', mismatchCaught);
}

/* ---------------------------------------------------------------- main */

console.log('='.repeat(70));
console.log('HSB SALES OS - APPS-SCRIPT-TESTS (ausgelieferter Code, Node + Stubs)');
console.log('='.repeat(70));

[testAssetGate, testEligibility, testDynamicCounts, testGateNotBypassable,
 testEmptyBatchExplained, testEmailDedup, testNoCrossSender, testEmlStructure,
 testQualifyAndDedupWrite, testJordi100OneClick, testJordi100SafetyGates,
 testJordi100UiContract, testSidebarServerContract, testSidebarFailureHandling,
 testSuppression, testDuplicateBatchProtection,
 testDashboard, testEmlExportChunking, testExportRetryAndRecovery,
 testBatchRecoveryAfterLostCallback,
 testFollowUps, testEnsureColumns,
 testSetupState, testBatchListe, testSuche,
 testLockServiceAndConcurrency, testIdempotency, testInboundEvents,
 testPostSendReconciliation, testOperatorSendConfirmation,
 testDryRunsAndArbitraryN, testActivity12ColumnContract].forEach(function (fn) {
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
try {
  fs.writeFileSync(path.join(__dirname, 'last_run_apps_script.json'),
    JSON.stringify({ test_count: RESULTS.length, test_pass: pass,
                     test_fail: fail }, null, 2) + '\n');
} catch (_) {}
process.exit(fail ? 1 : 0);
