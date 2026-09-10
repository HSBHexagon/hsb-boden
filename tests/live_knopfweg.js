/**
 * Echtlauf: der DEPLOYTE Apps-Script-Code gegen den ECHTEN Power-Automate-Flow.
 *
 * Warum das noetig ist: alle bisherigen Nachweise liefen ueber ein Python-
 * Skript, das den Flow direkt aufrief. Der Weg, den der Knopf im Sheet nimmt
 * - uiCreateDraftsChunk -> createDraftsForBatch -> adapterUrlFor_ ->
 * UrlFetchApp -> Flow - war noch nie am Stueck gelaufen.
 *
 * Nachgebildet wird hier nur die Google-Laufzeit (Sheet, Drive, Utilities).
 * Flow, Outlook und der Anhang sind echt. Es entsteht ein realer Entwurf.
 * Versand findet nicht statt: der Flow kennt keine Send-Aktion.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const os = require('os');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const AS = path.join(ROOT, 'apps_script');
const DEPLOY = path.join(ROOT, 'deploy');
// Nutzdaten und Antwort laufen ueber Dateien im Temp-Verzeichnis, nicht
// ueber die Kommandozeile: der Anhang ist base64-kodiert rund 2 MB gross
// und sprengt jedes Argumentlimit.
const TEMP = fs.mkdtempSync(path.join(os.tmpdir(), 'hsb-knopfweg-'));

const EMPFAENGER = process.argv[2] || 'cherinodiaz@outlook.com';
const BATCH_ID = 'HSB-20260910-JOEL-TEST';

// --- Aufruf-URL live holen, damit nichts Geheimes im Quelltext steht -------
const ADAPTER_URL = execFileSync('python3', ['-c',
  "import sys; sys.path.insert(0,'" + path.join(ROOT, 'engine') + "');" +
  "from pa_direct_drafts import callback_url; print(callback_url('JOEL'))"
], { encoding: 'utf8' }).trim();

let SHEETS = {};
let ECHTE_AUFRUFE = 0;
let REAL_SEND_CALLS = 0;
let LETZTE_ANTWORT = null;

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
    setValue: function (val) { this.setValues([[val]]); }
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
    getRange: function (r, c, nr, nc) { return makeRange(this, r, c, nr, nc); },
    appendRow: function (row) { this._data.push(row.slice()); return this; }
  };
  SHEETS[name] = s;
  return s;
}

const SCRIPT_PROPS = {
  HSB_ADAPTER_URL_JOEL: ADAPTER_URL,
  HSB_ACTIVE_BATCH_ID: BATCH_ID
};

const FLYER_DATEIEN = {
  '1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV': 'HSB-Flyer-Jordi-Post_FINAL.pdf',
  '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS': 'HSB-Flyer-Joel-Cherino_FINAL.pdf'
};
const DriveApp = {
  _files: {},
  getFileById: function (id) {
    const f = DriveApp._files[id];
    if (!f) throw new Error('Datei nicht gefunden: ' + id);
    return {
      getBlob: function () {
        return {
          getBytes: function () { return f.bytes; },
          setName: function () { return this; },
          getName: function () { return FLYER_DATEIEN[id] || 'flyer.pdf'; },
          getContentType: function () { return 'application/pdf'; }
        };
      }
    };
  }
};
Object.keys(FLYER_DATEIEN).forEach(function (id) {
  DriveApp._files[id] = {
    bytes: fs.readFileSync(path.join(ROOT, 'assets', 'canonical', FLYER_DATEIEN[id]))
  };
});

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
    getUi: function () { return { alert: function () {}, ButtonSet: { OK: 'OK' } }; }
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
  // ECHTER Netzaufruf - kein Mock.
  UrlFetchApp: {
    fetch: function (url, opts) {
      ECHTE_AUFRUFE++;
      const payloadDatei = path.join(TEMP, 'live_payload.json');
      const urlDatei = path.join(TEMP, 'live_url.txt');
      fs.writeFileSync(payloadDatei, opts.payload);
      fs.writeFileSync(urlDatei, url);
      const roh = execFileSync('python3', [path.join(__dirname, 'live_post.py'), TEMP], {
        encoding: 'utf8', maxBuffer: 32 * 1024 * 1024
      });
      const antwort = JSON.parse(roh);
      LETZTE_ANTWORT = antwort;
      return {
        getResponseCode: function () { return antwort.code; },
        getContentText: function () { return antwort.text; }
      };
    }
  },
  DriveApp: DriveApp,
  Utilities: {
    DigestAlgorithm: { SHA_256: 'SHA_256' },
    Charset: { UTF_8: 'UTF_8' },
    computeDigest: function (_alg, bytes) {
      const hash = crypto.createHash('sha256').update(Buffer.from(bytes)).digest();
      return Array.from(hash).map(b => b > 127 ? b - 256 : b);
    },
    base64Encode: function (data) { return Buffer.from(data).toString('base64'); },
    getUuid: function () { return crypto.randomUUID(); },
    formatDate: function (d) { return d.toISOString(); },
    newBlob: function (content, type, name) {
      return {
        _name: name, _type: type, _len: content.length,
        getBytes: function () { return Buffer.from(content); }
      };
    }
  },
  Session: {
    getActiveUser: function () {
      return { getEmail: function () { return 'j-cherino@hsb-boden.de'; } };
    }
  },
  MailApp: { sendEmail: function () { REAL_SEND_CALLS++; } }
};

const ctx = vm.createContext(sandbox);
['Config.gs', 'Engine.gs', 'Actions.gs', 'Code.gs'].forEach(f => {
  vm.runInContext(fs.readFileSync(path.join(AS, f), 'utf8'), ctx, { filename: f });
});
vm.runInContext(
  fs.readFileSync(path.join(DEPLOY, 'HSB_DraftAdapter.gs.js'), 'utf8'),
  ctx, { filename: 'HSB_DraftAdapter.gs.js' }
);

const LEADS_HEADER = [
  'Lead-ID', 'Firma', 'Branche', 'Tier', 'Ansprechpartner',
  'E-Mail', 'Opt-in-Status', 'Opt-out-Status', 'Versandfreigabe',
  'Verantwortlicher', 'Kampagne_ID', 'Batch_ID', 'Send_Status', 'Send_Datum',
  'Bounce_Status', 'Reply_Status', 'Follow-up-Datum', 'Notizen', 'Standort',
  'Legal_Basis', 'Suppressed', 'Batch_Status', 'Prepared_At', 'Draft_ID',
  'Drafted_At', 'Approved_At', 'Outlook_Message_ID', 'Internet_Message_ID',
  'Conversation_ID', 'Last_Reply_At', 'Last_Error'
];
const lead = new Array(LEADS_HEADER.length).fill('');
lead[0] = 'HSB-BUTTONTEST-0001';
lead[1] = 'Musterbetrieb Knopftest GmbH';
lead[3] = 'A';
lead[4] = 'Herr Mustermann';
lead[5] = EMPFAENGER;
lead[8] = 'yes';
lead[9] = 'Joel Cherino Diaz';
lead[11] = BATCH_ID;
lead[12] = 'not_sent';
lead[19] = 'EXISTING_CUSTOMER_7_3';
lead[20] = 'no';
lead[21] = 'PREPARED';
makeSheet('ALL_LEADS', LEADS_HEADER, [lead]);
makeSheet('BATCHES', ['Batch_ID', 'Owner', 'Flyer_SHA256', 'Status', 'Lead_Count'], [
  [BATCH_ID, 'JOEL',
   '2bccadacc77b531057583d2d650963c30deceed36c8be1fd90ca64e8b8cde5fb', 'PREPARED', 1]
]);
makeSheet('ACTIVITIES', [
  'Activity_ID', 'Lead_ID', 'Timestamp', 'Owner', 'Activity_Type',
  'Channel', 'Result', 'Template_ID', 'Batch_ID', 'Note',
  'Next_Action', 'Next_Action_Date'
], []);

console.log('='.repeat(70));
console.log('ECHTLAUF: Apps-Script-Knopfweg gegen den Live-Flow');
console.log('='.repeat(70));
console.log('Empfaenger (nur Entwurf) : ' + EMPFAENGER);
console.log('Adapter-URL              : ' + ADAPTER_URL.slice(0, 78) + '…');
console.log('');

let bestanden = 0, durchgefallen = 0;
function pruefe(bedingung, name, details) {
  if (bedingung) { bestanden++; console.log('PASS  ' + name + (details ? '  (' + details + ')' : '')); }
  else { durchgefallen++; console.error('FAIL  ' + name + (details ? '  (' + details + ')' : '')); }
}

const r = vm.runInContext('uiCreateDraftsChunk("' + BATCH_ID + '", 1)', ctx);

pruefe(r.ok === true, 'Knopfweg meldet Erfolg', r.error || '');
pruefe(ECHTE_AUFRUFE === 1, 'Genau ein echter Flow-Aufruf', 'Aufrufe=' + ECHTE_AUFRUFE);
pruefe(r.ok && r.data && r.data.draftedCount === 1, 'Genau 1 Entwurf gezaehlt',
       'drafted=' + (r.data ? r.data.draftedCount : '-'));

if (LETZTE_ANTWORT) {
  let body = {};
  try { body = JSON.parse(LETZTE_ANTWORT.text); } catch (e) { body = {}; }
  console.log('\nAntwort des Flows:');
  console.log('  HTTP-Code        : ' + LETZTE_ANTWORT.code);
  console.log('  Status           : ' + body.status);
  console.log('  Draft-ID         : ' + String(body.draftId || '').slice(0, 40) + '…');
  console.log('  Anhangname       : ' + body.attachmentName);
  console.log('  Anhanggroesse    : ' + body.attachmentSize + ' Bytes');
  console.log('  Base64-Zeichen   : ' + body.attachmentBase64Chars);

  const flyerBytes = DriveApp._files['16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS'].bytes.length;
  console.log('  Flyer-Quelle     : ' + flyerBytes + ' Bytes');
  pruefe(Math.abs(body.attachmentSize - flyerBytes) <= 1000,
         'Anhang hat die Groesse des Originalflyers',
         'Differenz ' + (body.attachmentSize - flyerBytes) + ' Bytes');
  pruefe(body.attachmentName === 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
         'Anhang traegt den Empfaengernamen', body.attachmentName);
  // Einfach kodiert heisst: Base64-Zeichen = 4/3 der Bytes. Doppelt kodiert
  // waere es 16/9 - genau daran erkennt man den alten Fehler.
  const erwarteteZeichen = Math.ceil(flyerBytes / 3) * 4;
  pruefe(Math.abs(body.attachmentBase64Chars - erwarteteZeichen) <= 500,
         'Anhang ist EINFACH kodiert (nicht doppelt)',
         body.attachmentBase64Chars + ' statt ' + erwarteteZeichen + ' bei doppelter Kodierung waeren es ~' +
         Math.ceil(erwarteteZeichen / 3) * 4);
}

// Rueckschrieb ins (nachgebildete) Sheet pruefen
const blatt = SHEETS['ALL_LEADS'];
const kopf = blatt._data[0];
const zeile = blatt._data[1];
pruefe(!!zeile[kopf.indexOf('Draft_ID')], 'Draft_ID im Sheet eingetragen');
pruefe(zeile[kopf.indexOf('Send_Status')] === 'drafted', 'Send_Status = drafted',
       String(zeile[kopf.indexOf('Send_Status')]));
pruefe(zeile[kopf.indexOf('Batch_Status')] === 'DRAFTED', 'Batch_Status = DRAFTED',
       String(zeile[kopf.indexOf('Batch_Status')]));
pruefe(!zeile[kopf.indexOf('Last_Error')], 'Kein Fehlervermerk');
pruefe(REAL_SEND_CALLS === 0, 'REAL_EXTERNAL_SEND_COUNT = 0 (nichts versendet)');

console.log('\n' + '='.repeat(70));
console.log('ERGEBNIS: ' + bestanden + ' bestanden, ' + durchgefallen + ' fehlgeschlagen');
console.log('='.repeat(70));
process.exit(durchgefallen > 0 ? 1 : 0);
