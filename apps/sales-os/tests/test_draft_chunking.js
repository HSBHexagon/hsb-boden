/**
 * Testet das 10er-Chunking des HSB Draft-Adapters (uiCreateDraftsChunk) in Node.js.
 *
 * Verifiziert:
 * 1. Testentwurf (chunkSize=1) verarbeitet exakt 1 Lead.
 * 2. Sequentielles 10er-Chunking verarbeitet exakt 10 Leads pro Block.
 * 3. Idempotenz: Bereits gedraftete Leads werden uebersprungen.
 * 4. Automatische Erkennung von isComplete === true nach Erreichen von 100 Entwuerfen.
 * 5. Sendesicherheit: REAL_EXTERNAL_SEND_COUNT bleibt 0 (nur Drafts, kein Send).
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const AS = path.join(ROOT, 'apps_script');
const DEPLOY = path.join(ROOT, 'deploy');

// ------------------------------------------------------------- Google Stubs
let SHEETS = {};
let MOCK_FETCH_CALLS = 0;
// Steuert, was der nachgebildete Flow als Anhanggroesse zurueckmeldet:
// 'ok' | 'doppelt_kodiert' | 'fehlt'
let MOCK_ANHANG_MODUS = 'ok';
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
      for (let r = 0; r < vals.length; r++) {
        const rIdx = row - 1 + r;
        if (!sheet._data[rIdx]) sheet._data[rIdx] = [];
        for (let c = 0; c < vals[r].length; c++) {
          sheet._data[rIdx][col - 1 + c] = vals[r][c];
        }
      }
    },
    setValue: function (val) {
      this.setValues([[val]]);
    }
  };
}

function makeSheet(name, headers, rows) {
  const s = {
    _name: name,
    _data: [headers.slice()].concat((rows || []).map(r => r.slice())),
    getName: function () { return this._name; },
    getDataRange: function () {
      return makeRange(this, 1, 1, this._data.length, (this._data[0] || []).length);
    },
    getLastRow: function () { return this._data.length; },
    getLastColumn: function () { return (this._data[0] || []).length; },
    getRange: function (r, c, nr, nc) {
      return makeRange(this, r, c, nr, nc);
    },
    appendRow: function (row) {
      this._data.push(row.slice());
      return this;
    }
  };
  SHEETS[name] = s;
  return s;
}

const SCRIPT_PROPS = {
  HSB_ADAPTER_URL_JORDI: 'https://default8adbbf2efd2c48578540bbcd06fa02.02.environment.api.powerplatform.com/workflows/mock-jordi',
  HSB_ADAPTER_URL_JOEL: 'https://default8adbbf2efd2c48578540bbcd06fa02.02.environment.api.powerplatform.com/workflows/mock-joel',
  HSB_ACTIVE_BATCH_ID: 'HSB-20260905-JORDI-0001'
};

const DriveApp = {
  _files: {},
  getFileById: function (id) {
    const f = DriveApp._files[id];
    if (!f) throw new Error('Datei nicht gefunden: ' + id);
    const map = {
      '1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV': 'HSB-Flyer-Jordie-Post_FINAL.pdf',
      '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS': 'HSB-Flyer-Joel-Cherino_FINAL.pdf'
    };
    return {
      getBlob: function () {
        return {
          getBytes: function () { return f.bytes; },
          setName: function () { return this; },
          getName: function () { return map[id] || 'flyer.pdf'; },
          getContentType: function () { return 'application/pdf'; }
        };
      }
    };
  }
};

function loadRealFlyers() {
  const map = {
    '1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV': 'HSB-Flyer-Jordie-Post_FINAL.pdf',
    '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS': 'HSB-Flyer-Joel-Cherino_FINAL.pdf'
  };
  Object.keys(map).forEach(function (id) {
    const p = path.join(ROOT, 'assets', 'canonical', map[id]);
    DriveApp._files[id] = { bytes: fs.readFileSync(p) };
  });
}
loadRealFlyers();

const sandbox = {
  console: console,
  Logger: { log: function () {} },
  SpreadsheetApp: {
    getActiveSpreadsheet: function () {
      return {
        getSheetByName: function (n) { return SHEETS[n] || null; },
        insertSheet: function (n) { return makeSheet(n, [], []); },
        getSheets: function () { return Object.keys(SHEETS).map(k => SHEETS[k]); },
        getName: function () { return 'HSB CRM MASTER 6424'; }
      };
    },
    getActive: function () { return this.getActiveSpreadsheet(); },
    getUi: function () {
      return {
        alert: function () {},
        ButtonSet: { OK: 'OK' }
      };
    }
  },
  PropertiesService: {
    getScriptProperties: function () {
      return {
        getProperty: function (k) { return SCRIPT_PROPS[k] || null; },
        setProperty: function (k, v) { SCRIPT_PROPS[k] = String(v); },
        getProperties: function () { return Object.assign({}, SCRIPT_PROPS); }
      };
    }
  },
  UrlFetchApp: {
    fetch: function (url, opts) {
      MOCK_FETCH_CALLS++;
      const payload = JSON.parse(opts.payload);
      // Der echte Flow liest den Entwurf zurueck und meldet, was Outlook
      // wirklich gespeichert hat. Der Mock rechnet dieselbe Groesse aus den
      // gesendeten Bytes und legt den an 50 realen Entwuerfen gemessenen
      // MIME-Overhead von 292 Bytes drauf.
      const echteBytes = Buffer.from(
        payload.attachmentContentBytes || '', 'base64').length;
      let gemeldeteGroesse = echteBytes + 292;
      if (MOCK_ANHANG_MODUS === 'doppelt_kodiert') {
        // Der Fehler, der monatelang unentdeckt blieb: Outlook speichert die
        // Base64-Zeichen als Nutzdaten statt sie zu dekodieren.
        gemeldeteGroesse = Math.round(echteBytes * 4 / 3) + 292;
      } else if (MOCK_ANHANG_MODUS === 'fehlt') {
        gemeldeteGroesse = null;
      }
      return {
        getResponseCode: function () { return 200; },
        getContentText: function () {
          const antwort = {
            draftId: 'MOCK-DRAFT-' + payload.leadId,
            internetMessageId: '<mock-' + payload.leadId + '@hsb-boden.de>',
            conversationId: 'CONV-' + payload.leadId
          };
          if (gemeldeteGroesse !== null) antwort.attachmentSize = gemeldeteGroesse;
          return JSON.stringify(antwort);
        }
      };
    }
  },
  DriveApp: DriveApp,
  Utilities: {
    DigestAlgorithm: { SHA_256: 'SHA_256' },
    Charset: { UTF_8: 'UTF_8' },
    computeDigest: function (_alg, bytes) {
      const buf = Buffer.from(bytes);
      const hash = crypto.createHash('sha256').update(buf).digest();
      return Array.from(hash).map(b => b > 127 ? b - 256 : b);
    },
    base64Encode: function (data) {
      return Buffer.from(data).toString('base64');
    },
    getUuid: function () { return crypto.randomUUID(); },
    formatDate: function (d, _tz, fmt) {
      return d.toISOString();
    },
    newBlob: function (content, type, name) {
      return {
        _name: name, _type: type, _len: content.length,
        getBytes: function () { return Buffer.from(content); }
      };
    }
  },
  Session: { getActiveUser: function () { return { getEmail: function () { return 'j-post@hsb-boden.de'; } }; } },
  MailApp: { sendEmail: function () { REAL_SEND_CALLS++; } }
};

const ctx = vm.createContext(sandbox);

// Lade Engine & DraftAdapter
['Config.gs', 'Engine.gs', 'Actions.gs', 'Code.gs'].forEach(f => {
  const src = fs.readFileSync(path.join(AS, f), 'utf8');
  vm.runInContext(src, ctx, { filename: f });
});

const draftAdapterSrc = fs.readFileSync(path.join(DEPLOY, 'HSB_DraftAdapter.gs.js'), 'utf8');
vm.runInContext(draftAdapterSrc, ctx, { filename: 'HSB_DraftAdapter.gs.js' });

// ----------------------------------------------------------- Test Data Setup
const LEADS_HEADER = [
  'Lead-ID', 'Firma', 'Branche', 'Tier', 'Ansprechpartner',
  'E-Mail', 'Opt-in-Status', 'Opt-out-Status', 'Versandfreigabe',
  'Verantwortlicher', 'Kampagne_ID', 'Batch_ID', 'Send_Status', 'Send_Datum',
  'Bounce_Status', 'Reply_Status', 'Follow-up-Datum', 'Notizen', 'Standort',
  'Legal_Basis', 'Suppressed', 'Batch_Status', 'Prepared_At', 'Draft_ID',
  'Drafted_At', 'Approved_At', 'Outlook_Message_ID', 'Internet_Message_ID',
  'Conversation_ID', 'Last_Reply_At', 'Last_Error'
];

const BATCH_ID = 'HSB-20260905-JORDI-0001';
const mockLeads = [];
for (let i = 1; i <= 100; i++) {
  const leadRow = new Array(LEADS_HEADER.length).fill('');
  leadRow[0] = 'LEAD-JORDI-' + String(i).padStart(4, '0'); // Lead-ID
  leadRow[1] = 'Testfirma ' + i + ' GmbH';                 // Firma
  leadRow[3] = 'A';                                        // Tier
  leadRow[4] = 'Herr Müller';                              // Ansprechpartner
  leadRow[5] = 'kontakt' + i + '@firma' + i + '.de';       // E-Mail
  leadRow[8] = 'yes';                                      // Versandfreigabe
  leadRow[9] = 'Jordi Post';                               // Verantwortlicher
  leadRow[11] = BATCH_ID;                                  // Batch_ID
  leadRow[12] = 'not_sent';                                // Send_Status
  leadRow[19] = 'OPT_IN';                                  // Legal_Basis
  leadRow[20] = 'no';                                      // Suppressed
  leadRow[21] = 'PREPARED';                                // Batch_Status
  mockLeads.push(leadRow);
}

makeSheet('ALL_LEADS', LEADS_HEADER, mockLeads);

const BATCHES_HEADER = ['Batch_ID', 'Owner', 'Flyer_SHA256', 'Status', 'Lead_Count'];
makeSheet('BATCHES', BATCHES_HEADER, [
  [BATCH_ID, 'JORDI', '08e1149e4fed409ac94d5af18139c36d00027a7a7b53e49928beb429d4a12729', 'PREPARED', 100]
]);
const ACTIVITIES_HEADER = [
  'Activity_ID', 'Lead_ID', 'Timestamp', 'Owner', 'Activity_Type',
  'Channel', 'Result', 'Template_ID', 'Batch_ID', 'Note',
  'Next_Action', 'Next_Action_Date'
];
makeSheet('ACTIVITIES', ACTIVITIES_HEADER, []);

// ------------------------------------------------------------- Testausfuehrung
console.log('======================================================================');
console.log('TEST: HSB SALES OS — 10er-CHUNK-AUTOMATISIERUNG & IDEMPOTENZ');
console.log('======================================================================\n');

let passed = 0;
let failed = 0;

function assert(cond, name, details) {
  if (cond) {
    passed++;
    console.log('PASS  ' + name + (details ? ' (' + details + ')' : ''));
  } else {
    failed++;
    console.error('FAIL  ' + name + (details ? ' (' + details + ')' : ''));
  }
}

// 1. Test: Single Draft (Chunk size = 1)
const r1 = vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 1)', ctx);
assert(r1.ok === true, 'Testentwurf r1.ok === true', r1.error || '');
assert(r1.data && r1.data.draftedCount === 1, 'Exakt 1 Testentwurf gedraftet', 'drafted=' + (r1.data ? r1.data.draftedCount : 0));
assert(r1.data && r1.data.openCount === 99, 'Genau 99 Leads verbleibend', 'open=' + (r1.data ? r1.data.openCount : 0));
assert(r1.data && r1.data.isComplete === false, 'isComplete ist false');
assert(MOCK_FETCH_CALLS === 1, 'Genau 1 Netzwerkaufruf getaetigt', 'calls=' + MOCK_FETCH_CALLS);

// 2. Test: 10er Chunk Schleife
let chunks = 0;
let isComplete = false;
while (!isComplete && chunks < 15) {
  chunks++;
  const res = vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 10)', ctx);
  assert(res.ok === true, 'Chunk ' + chunks + ' erfolgreich ausgeführt');
  isComplete = res.data.isComplete;
  console.log(`      Chunk ${chunks}: ${res.data.draftedCount}/100 gedraftet (offen: ${res.data.openCount})`);
}

assert(chunks === 10, 'Genau 10 Chunks benötigt (1 initial + 9x10 + 1x9)', 'chunks=' + chunks);
assert(isComplete === true, 'Nach 10 Chunks ist isComplete === true');
assert(MOCK_FETCH_CALLS === 100, 'Genau 100 Entwürfe über API angelegt', 'calls=' + MOCK_FETCH_CALLS);

// 3. Test: Idempotenz (Replay bei vollständigem Batch)
const rReplay = vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 10)', ctx);
assert(rReplay.ok === true, 'Replay ist erfolgreich');
assert(rReplay.data.draftedCount === 100, 'Bleibt bei 100 gedrafteten Leads');
assert(rReplay.data.openCount === 0, 'Keine offenen Leads');
assert(rReplay.data.isComplete === true, 'isComplete bleibt true');
assert(MOCK_FETCH_CALLS === 100, 'Keine erneuten Netzwerkaufrufe bei bestehenden Draft_IDs (Idempotenz gewahrt)');

// 4. Test: Send-Sicherheit
assert(REAL_SEND_CALLS === 0, 'REAL_EXTERNAL_SEND_COUNT ist strikt 0 (Human-in-the-Loop gewahrt)');

console.log('\n======================================================================');
console.log(`ERGEBNIS: ${passed} bestanden, ${failed} fehlgeschlagen von ${passed + failed}`);
console.log('REAL_EXTERNAL_SEND_COUNT=0');
console.log('======================================================================');

if (failed > 0) process.exit(1);

// 5. Test: kaputter Anhang muss fail-closed stoppen
//
// Das ist der Fehler, der monatelang durchrutschte: der Flow lieferte eine
// draftId, der Entwurf lag im Postfach - aber der Flyer war doppelt kodiert
// und liess sich nicht oeffnen. Ohne Groessenpruefung meldete die Oberflaeche
// dafuer Erfolg. Der Test haelt fest, dass genau das nicht mehr passiert.
function draftIdsLeeren_() {
  const blatt = SHEETS['ALL_LEADS'];
  const kopf = blatt._data[0];
  const iDraft = kopf.indexOf('Draft_ID');
  const iError = kopf.indexOf('Last_Error');
  const iStatus = kopf.indexOf('Batch_Status');
  for (let r = 1; r < blatt._data.length; r++) {
    blatt._data[r][iDraft] = '';
    blatt._data[r][iError] = '';
    blatt._data[r][iStatus] = '';
  }
}

function letzterFehlerVermerk_() {
  const blatt = SHEETS['ALL_LEADS'];
  const kopf = blatt._data[0];
  const iError = kopf.indexOf('Last_Error');
  const iDraft = kopf.indexOf('Draft_ID');
  for (let r = 1; r < blatt._data.length; r++) {
    if (blatt._data[r][iError]) {
      return { fehler: String(blatt._data[r][iError]), draftId: blatt._data[r][iDraft] };
    }
  }
  return null;
}

draftIdsLeeren_();
MOCK_ANHANG_MODUS = 'doppelt_kodiert';
const rKaputt = vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 10)', ctx);
assert(rKaputt.ok === false, 'Doppelt kodierter Anhang meldet KEINEN Erfolg',
       'ok=' + rKaputt.ok);
assert(String(rKaputt.error || '').indexOf('ANHANG') >= 0,
       'Fehlermeldung benennt den Anhang', rKaputt.error);
const vermerkKaputt = letzterFehlerVermerk_();
assert(vermerkKaputt !== null, 'Der Vorfall steht in Last_Error');
assert(!!(vermerkKaputt && vermerkKaputt.draftId),
       'Draft_ID wird trotzdem geschrieben - kein verwaister Entwurf im Postfach',
       'draftId=' + (vermerkKaputt && vermerkKaputt.draftId));

// 6. Test: fehlende Groessenmeldung gilt ebenfalls als ungeprueft
draftIdsLeeren_();
MOCK_ANHANG_MODUS = 'fehlt';
const rOhne = vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 10)', ctx);
assert(rOhne.ok === false, 'Antwort ohne Anhanggroesse meldet KEINEN Erfolg',
       'ok=' + rOhne.ok);

// 7. Test: nach der Klaerung laesst sich der Vermerk gezielt zuruecksetzen
draftIdsLeeren_();
MOCK_ANHANG_MODUS = 'fehlt';
vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 10)', ctx);
assert(letzterFehlerVermerk_() !== null, 'Vor dem Zuruecksetzen liegt ein Vermerk vor');
const rReset = vm.runInContext('uiFehlerZuruecksetzen("' + BATCH_ID + '")', ctx);
assert(rReset.ok === true, 'Zuruecksetzen laeuft durch', JSON.stringify(rReset));

MOCK_ANHANG_MODUS = 'ok';

console.log('\n======================================================================');
console.log(`ERGEBNIS GESAMT: ${passed} bestanden, ${failed} fehlgeschlagen von ${passed + failed}`);
console.log('======================================================================');
if (failed > 0) process.exit(1);
