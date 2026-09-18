/**
 * Testet den Graph-Adapter: Entwuerfe direkt im Microsoft-365-Postfach.
 *
 * Der Weg ueber Power Automate ist fuer Jordi lizenzbedingt zu. Dieser
 * Adapter ersetzt ihn. Geprueft wird, was schiefgehen koennte, wenn zwei
 * Menschen dieselbe Tabelle benutzen:
 *
 *   1. Ein Entwurf darf NIEMALS im Postfach der falschen Person landen.
 *   2. Es darf nichts versendet werden - nur Entwuerfe.
 *   3. Die Anhanggroesse muss aus dem gespeicherten Entwurf kommen,
 *      nicht aus dem, was beim Anlegen mitgeschickt wurde.
 *   4. Ohne Verbindung muss die Meldung sagen, was zu tun ist.
 *
 * Getestet wird die AUSGELIEFERTE Datei (deploy/), nicht die Quelle -
 * sonst prueft der Test etwas anderes als im Sheet laeuft.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const DEPLOY = path.join(ROOT, 'deploy');

let bestanden = 0;
let fehlgeschlagen = 0;

function pruefe(name, bedingung, detail) {
  if (bedingung) {
    bestanden++;
    console.log('PASS  ' + name + (detail ? '  (' + detail + ')' : ''));
  } else {
    fehlgeschlagen++;
    console.log('FAIL  ' + name + (detail ? '  (' + detail + ')' : ''));
  }
}

// ------------------------------------------------------------- Nachbauten

/** Zaehlt jeden Aufruf, damit ein Versand nicht unbemerkt durchginge. */
let AUFRUFE = [];
let USER_PROPS = {};

/** Nachgebildeter Graph-Dienst. */
function makeFetch(opt) {
  opt = opt || {};
  const postfach = opt.postfach || 'j-cherino@hsb-boden.de';
  const anhangGroesse = opt.anhangGroesse === undefined ? 1534405 : opt.anhangGroesse;

  return function (url, params) {
    params = params || {};
    AUFRUFE.push({ url: url, method: (params.method || 'get').toLowerCase() });

    // Jeder Sendeversuch ist ein Testfehler, kein gueltiger Pfad.
    if (/\/send\b/.test(url)) {
      throw new Error('VERSAND VERSUCHT - das darf nicht vorkommen: ' + url);
    }

    function antwort(code, obj) {
      return {
        getResponseCode: function () { return code; },
        getContentText: function () { return JSON.stringify(obj); }
      };
    }

    if (/oauth2\/v2\.0\/token/.test(url)) {
      if (opt.tokenFehler) return antwort(400, { error: 'invalid_grant' });
      return antwort(200, {
        access_token: 'AT-' + Date.now(), refresh_token: 'RT-neu',
        expires_in: 3600
      });
    }
    if (/oauth2\/v2\.0\/devicecode/.test(url)) {
      return antwort(200, {
        device_code: 'DC-1', user_code: 'ABC123456',
        verification_uri: 'https://login.microsoft.com/device', expires_in: 900,
        interval: 5
      });
    }
    if (/\/me\?/.test(url)) {
      return antwort(200, { userPrincipalName: postfach, mail: postfach });
    }
    if (/\/me\/messages\/[^/]+\/attachments/.test(url)) {
      if (anhangGroesse === null) return antwort(200, { value: [] });
      return antwort(200, { value: [{
        name: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf', size: anhangGroesse }] });
    }
    if (/\/me\/messages$/.test(url)) {
      return antwort(201, {
        id: 'AAMk-TEST-ENTWURF-1',
        internetMessageId: '<test@hsb-boden.de>',
        conversationId: 'CONV-1'
      });
    }
    throw new Error('Unerwarteter Aufruf: ' + url);
  };
}

function ladeAdapter(opt) {
  AUFRUFE = [];
  USER_PROPS = Object.assign({
    HSB_GRAPH_REFRESH_TOKEN: 'RT-vorhanden',
    HSB_GRAPH_MAILBOX: (opt && opt.postfach) || 'j-cherino@hsb-boden.de'
  }, (opt && opt.props) || {});

  const kontext = {
    console: console,
    Date: Date,
    Math: Math,
    JSON: JSON,
    Object: Object,
    String: String,
    Number: Number,
    encodeURIComponent: encodeURIComponent,
    UrlFetchApp: { fetch: makeFetch(opt) },
    PropertiesService: {
      getUserProperties: function () {
        return {
          getProperty: function (k) {
            return USER_PROPS[k] === undefined ? null : USER_PROPS[k];
          },
          setProperty: function (k, v) { USER_PROPS[k] = String(v); },
          deleteProperty: function (k) { delete USER_PROPS[k]; }
        };
      }
    },
    SpreadsheetApp: { getUi: function () { throw new Error('keine UI im Test'); } },
    // Aus Config.gs - der Adapter braucht nur die Postfachzuordnung.
    FLYERS: {
      JORDI: { mailbox: 'j-post@hsb-boden.de' },
      JOEL: { mailbox: 'j-cherino@hsb-boden.de' }
    },
    HTTP_TIMEOUT_SECONDS: 60
  };
  vm.createContext(kontext);
  vm.runInContext(
    fs.readFileSync(path.join(DEPLOY, 'HSB_GraphAdapter.js'), 'utf8'), kontext);
  return kontext;
}

const NUTZLAST = {
  leadId: 'HSB-TEST-0001',
  batchId: 'BATCH-TEST',
  to: 'kunde@example.com',
  subject: 'Testbetreff',
  bodyHtml: '<p>Text</p>',
  attachmentName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
  attachmentContentBytes: 'AAAA'
};

// ------------------------------------------------------------- Tests

console.log('\n=== 1. Entwurf im eigenen Postfach ===');
{
  const k = ladeAdapter({ postfach: 'j-cherino@hsb-boden.de' });
  const body = k.graphEntwurfErzeugen_(NUTZLAST, 'JOEL');
  pruefe('Draft-ID zurueckgegeben', body.draftId === 'AAMk-TEST-ENTWURF-1',
         body.draftId);
  pruefe('Status DRAFTED', body.status === 'DRAFTED', body.status);
  pruefe('Anhanggroesse aus dem gespeicherten Entwurf',
         body.attachmentSize === 1534405, String(body.attachmentSize));
  pruefe('Internet-Message-ID durchgereicht',
         body.internetMessageId === '<test@hsb-boden.de>');
  pruefe('Antwortformat gleicht dem Flow (leadId/batchId gesetzt)',
         body.leadId === 'HSB-TEST-0001' && body.batchId === 'BATCH-TEST');
}

console.log('\n=== 2. Fremdes Postfach wird abgewiesen ===');
{
  // Jordi ist verbunden, der Lead gehoert aber Joel.
  const k = ladeAdapter({ postfach: 'j-post@hsb-boden.de' });
  let fehler = '';
  try {
    k.graphEntwurfErzeugen_(NUTZLAST, 'JOEL');
  } catch (e) {
    fehler = String(e);
  }
  pruefe('Abbruch mit FALSCHES_POSTFACH', fehler.indexOf('FALSCHES_POSTFACH') >= 0,
         fehler.slice(0, 90));
  pruefe('KEIN Entwurf angelegt',
         !AUFRUFE.some(function (a) { return /\/me\/messages$/.test(a.url); }),
         AUFRUFE.length + ' Aufrufe');
}

console.log('\n=== 3. Jordi in seinem eigenen Postfach ===');
{
  const k = ladeAdapter({ postfach: 'j-post@hsb-boden.de' });
  const body = k.graphEntwurfErzeugen_(NUTZLAST, 'JORDI');
  pruefe('Jordis Entwurf wird erzeugt', body.draftId === 'AAMk-TEST-ENTWURF-1');
  pruefe('Status DRAFTED', body.status === 'DRAFTED');
}

console.log('\n=== 4. Fehlender Anhang faellt auf ===');
{
  const k = ladeAdapter({ postfach: 'j-cherino@hsb-boden.de', anhangGroesse: null });
  const body = k.graphEntwurfErzeugen_(NUTZLAST, 'JOEL');
  pruefe('Status DRAFTED_UNVERIFIED', body.status === 'DRAFTED_UNVERIFIED',
         body.status);
  pruefe('Groesse null statt geraten', body.attachmentSize === null);
  pruefe('Grund benannt', /kein Anhang/.test(body.verifyError), body.verifyError);
  pruefe('Draft-ID trotzdem da (kein verwaister Entwurf)',
         body.draftId === 'AAMk-TEST-ENTWURF-1');
}

console.log('\n=== 5. Ohne Verbindung: brauchbare Meldung ===');
{
  const k = ladeAdapter({ props: { HSB_GRAPH_REFRESH_TOKEN: undefined } });
  delete USER_PROPS.HSB_GRAPH_REFRESH_TOKEN;
  let fehler = '';
  try {
    k.graphToken_();
  } catch (e) {
    fehler = String(e);
  }
  pruefe('NICHT_VERBUNDEN gemeldet', fehler.indexOf('NICHT_VERBUNDEN') >= 0);
  pruefe('Meldung nennt den Menuepunkt', /Mit Outlook verbinden/.test(fehler));
  pruefe('graphVerbunden_() ist falsch', k.graphVerbunden_() === false);
}

console.log('\n=== 6. Abgelaufene Verbindung wird nicht verschleiert ===');
{
  const k = ladeAdapter({ postfach: 'j-cherino@hsb-boden.de', tokenFehler: true });
  let fehler = '';
  try {
    k.graphToken_();
  } catch (e) {
    fehler = String(e);
  }
  pruefe('VERBINDUNG_ABGELAUFEN gemeldet',
         fehler.indexOf('VERBINDUNG_ABGELAUFEN') >= 0, fehler.slice(0, 80));
  pruefe('Unbrauchbares Token wurde entfernt',
         !USER_PROPS.HSB_GRAPH_REFRESH_TOKEN);
}

console.log('\n=== 7. Sendesicherheit ===');
{
  const k = ladeAdapter({ postfach: 'j-cherino@hsb-boden.de' });
  k.graphEntwurfErzeugen_(NUTZLAST, 'JOEL');
  const sendeVersuche = AUFRUFE.filter(function (a) { return /\/send/.test(a.url); });
  pruefe('REAL_EXTERNAL_SEND_COUNT = 0', sendeVersuche.length === 0,
         AUFRUFE.length + ' Aufrufe, 0 davon Versand');

  const quelle = fs.readFileSync(path.join(DEPLOY, 'HSB_GraphAdapter.js'), 'utf8');
  // Der Kommentarblock nennt /send bewusst als das, was NICHT vorkommt.
  const ohneKommentare = quelle.replace(/\/\*[\s\S]*?\*\//g, '')
                               .replace(/^\s*\/\/.*$/gm, '');
  pruefe('Kein /send im ausgelieferten Code',
         ohneKommentare.indexOf('/send') === -1);
}

console.log('\n=== 8. Weiche im Draft-Adapter ===');
{
  const adapter = fs.readFileSync(
    path.join(DEPLOY, 'HSB_DraftAdapter.gs.js'), 'utf8');
  pruefe('entwurfAnlegen_ existiert', /function entwurfAnlegen_/.test(adapter));
  pruefe('Graph hat Vorrang vor Power Automate',
         adapter.indexOf('graphVerbunden_()') <
         adapter.indexOf('UrlFetchApp.fetch(adapterUrlFor_'));
  pruefe('Anhangpruefung weiterhin im Aufrufer',
         /ANHANG_UNGEPRUEFT/.test(adapter) && /ANHANG_TOLERANZ_BYTES/.test(adapter));
  pruefe('Power Automate bleibt als Rueckfallebene',
         /adapterUrlFor_\(owner\)/.test(adapter));
}

console.log('\n=== 9. Wiederkehrender Postfach-Abgleich: Lead-Bezug und Idempotenz ===');
{
  // Der 15-Minuten-Trigger reicht jede Nachricht der letzten 100 erneut an
  // processInboundEvent. Dort ist NEEDS_REVIEW bewusst nicht terminal - ohne
  // Vorfilter entstuende bei jedem Lauf fuer jede fremde Nachricht
  // (Newsletter, interne Post) eine neue NEEDS_REVIEW-Zeile.
  const k = ladeAdapter({ postfach: 'j-cherino@hsb-boden.de' });
  const EVENTS = [];           // Nachbau INBOUND_EVENTS (kanonisches 12-Spalten-Layout, Processed in Spalte J)
  let LEADS = [
    { Lead_ID: 'HSB-L-1', Email: 'einkauf@brauerei-muster.de', Send_Status: 'sent', Internet_Message_ID: '<sent-1@hsb-boden.de>' },
    { Lead_ID: 'HSB-L-2', Email: 'info@architekten-beispiel.de', Send_Status: 'drafted', Internet_Message_ID: '' }
  ];
  let EINGEREICHT = [];
  k.CFG = { SHEET_EVENTS: 'INBOUND_EVENTS' };
  k.istFreemailDomain_ = function (d) { return ['gmail.com', 'web.de', 'gmx.de'].indexOf(d) >= 0; };   // aus Actions.gs
  k.sheet_ = function () {
    return {
      getLastRow: function () { return EVENTS.length + 1; },
      getRange: function () { return { getValues: function () { return EVENTS.map(function (r) { return r.slice(); }); } }; }
    };
  };
  k.readLeadsCached_ = function () { return { leads: LEADS }; };
  k.processInboundEvent = function (ev) {
    EINGEREICHT.push(ev);
    const hit = LEADS.filter(function (l) { return l.Lead_ID === ev.lead_id || l.Email === ev.email; })[0];
    const status = hit ? 'PROCESSED' : 'NEEDS_REVIEW';
    EVENTS.push([ev.event_id, 'ts', ev.mailbox || '', ev.email || '', ev.subject || '', ev.message_id || '', hit ? hit.Lead_ID : '', ev.event_type, 'no', status, ev.details || '', '']);
    return { ok: true, matched: !!hit, status: status };
  };

  function mail(id, from, subject, preview, to) {
    return { id: id, internetMessageId: '<' + id + '@x>', subject: subject, bodyPreview: preview || '',
             from: { emailAddress: { address: from } },
             toRecipients: [{ emailAddress: { address: to || 'j-cherino@hsb-boden.de' } }] };
  }
  const POSTEINGANG = [
    mail('m1', 'einkauf@brauerei-muster.de', 'AW: Industrieboden', 'Danke, bitte Angebot'),
    mail('m2', 'newsletter@cloudflare.com', 'Cloudflare Connect 2026', 'You are invited'),
    mail('m3', 'postmaster@outlook.com', 'Undeliverable: Industrieboden', '550 5.1.1 user unknown: buero@unbekannte-firma.de'),
    mail('m4', 'kollege@architekten-beispiel.de', 'AW: Industrieboden', 'Ich uebernehme das Thema'),
    mail('m5', 'jemand@gmail.com', 'Abmelden', 'bitte abmelden')
  ];

  const r1 = k.reconcileInboxMessages_(POSTEINGANG, 'TEST');
  const ids1 = EINGEREICHT.map(function (e) { return e.event_id; });
  pruefe('Antwort eines Leads wird eingereicht', ids1.indexOf('TEST-INBOX-<m1@x>') >= 0);
  pruefe('Newsletter ohne Lead-Bezug wird NICHT protokolliert', ids1.indexOf('TEST-INBOX-<m2@x>') === -1, ids1.join(','));
  pruefe('Bounce wird immer eingereicht (Sicherheitsrelevant)', ids1.indexOf('TEST-INBOX-<m3@x>') >= 0);
  pruefe('Kollege aus Lead-Domain wird eingereicht (Klaerfall)', ids1.indexOf('TEST-INBOX-<m4@x>') >= 0);
  pruefe('Abmeldung wird immer eingereicht, auch von fremder Adresse', ids1.indexOf('TEST-INBOX-<m5@x>') >= 0);
  pruefe('Lauf 1 meldet geprueft/eingereicht/fremd', r1.checked === 5 && r1.submitted === 4 && r1.foreign === 1, JSON.stringify(r1));

  EINGEREICHT = [];
  const r2 = k.reconcileInboxMessages_(POSTEINGANG, 'TEST');
  pruefe('Lauf 2 reicht nichts erneut ein (Idempotenz)', EINGEREICHT.length === 0, EINGEREICHT.map(function (e) { return e.event_id; }).join(','));
  pruefe('Lauf 2 zaehlt Uebersprungene', r2.skipped === 4 && r2.foreign === 1, JSON.stringify(r2));

  // Klaerfall wird erneut versucht, sobald er exakt zuordenbar ist.
  LEADS = LEADS.concat([{ Lead_ID: 'HSB-L-3', Email: 'kollege@architekten-beispiel.de', Send_Status: 'sent', Internet_Message_ID: '' }]);
  EINGEREICHT = [];
  k.reconcileInboxMessages_(POSTEINGANG, 'TEST');
  pruefe('NEEDS_REVIEW wird erneut eingereicht, wenn jetzt exakt zuordenbar',
         EINGEREICHT.length === 1 && EINGEREICHT[0].event_id === 'TEST-INBOX-<m4@x>',
         EINGEREICHT.map(function (e) { return e.event_id; }).join(','));

  // Offene Abmeldung (NEEDS_REVIEW) aus einer Firmendomain wird erneut eingereicht,
  // sobald die Domain einen Lead trifft - processInboundEvent sperrt dann die Domain.
  EVENTS.push(['TEST-INBOX-<m6@x>', 'ts', 'j-cherino@hsb-boden.de', 'vorname.name@brauerei-muster.de', 'Abmelden', '<m6@x>', '', 'OPT_OUT', 'yes', 'NEEDS_REVIEW', 'Abmeldung', '']);
  EINGEREICHT = [];
  k.reconcileInboxMessages_([mail('m6', 'vorname.name@brauerei-muster.de', 'Abmelden', 'bitte abmelden')], 'TEST');
  pruefe('Offene Abmeldung aus Lead-Domain wird erneut eingereicht',
         EINGEREICHT.length === 1 && EINGEREICHT[0].event_type === 'OPT_OUT', JSON.stringify(EINGEREICHT));

  // Gesendete Elemente: nur Empfaenger mit Lead-Bezug.
  EINGEREICHT = [];
  const GESENDET = [
    mail('s1', 'j-cherino@hsb-boden.de', 'Industrieboden', '', 'info@architekten-beispiel.de'),
    mail('s2', 'j-cherino@hsb-boden.de', 'Mietgeraet', '', 'depot@vermieter-intern.de'),
    mail('s3', 'j-cherino@hsb-boden.de', 'Tagesbericht', '', 'j-post@hsb-boden.de')
  ];
  const s1 = k.reconcileSentMessages_(GESENDET, 'TEST');
  const sids = EINGEREICHT.map(function (e) { return e.event_id; });
  pruefe('Sendung an Lead wird mit Lead-ID eingereicht',
         sids.indexOf('TEST-SENT-<s1@x>') >= 0 && EINGEREICHT[0].lead_id === 'HSB-L-2');
  pruefe('Sendungen ohne Lead-Bezug werden NICHT protokolliert', sids.length === 1 && s1.foreign === 2, JSON.stringify(s1));
  EINGEREICHT = [];
  const s2 = k.reconcileSentMessages_(GESENDET, 'TEST');
  pruefe('Sende-Abgleich Lauf 2 reicht nichts erneut ein', EINGEREICHT.length === 0 && s2.skipped === 1, JSON.stringify(s2));
}

console.log('\n=== 10. Signatur: Abmelde-Link ===');
{
  const sigKontext = { console: console, String: String, Object: Object };
  vm.createContext(sigKontext);
  vm.runInContext(
    fs.readFileSync(path.join(DEPLOY, 'HSB_DraftAdapter.gs.js'), 'utf8'), sigKontext);
  const sigJordi = sigKontext.signaturHtml_('Jordie Post', 'j-post@hsb-boden.de', '0170 2340904');
  pruefe('Signatur: Abmelde-Link auf das eigene Postfach mit Betreff Abmelden',
         sigJordi.indexOf('href="mailto:j-post@hsb-boden.de?subject=Abmelden"') >= 0 && sigJordi.indexOf('Hier abmelden') >= 0);
  pruefe('Signatur: Abmelde-Link steht vor den Pflichtangaben',
         sigJordi.indexOf('Hier abmelden') < sigJordi.indexOf('Sitz der Gesellschaft'));
}

console.log('\n=== 11. SYNC_STATUS wird je Postfach fortgeschrieben ===');
{
  const k = ladeAdapter({ postfach: 'j-post@hsb-boden.de' });
  const SYNC = { _data: [] };
  const sheet = {
    getLastRow: function () { return SYNC._data.length; },
    appendRow: function (r) { SYNC._data.push(r.slice()); },
    getRange: function (r, c, nr, nc) {
      return {
        getValues: function () { return SYNC._data.slice(r - 1, r - 1 + nr).map(function (x) { return x.slice(c - 1, c - 1 + nc); }); },
        setValues: function (v) { for (let i = 0; i < v.length; i++) SYNC._data[r - 1 + i] = v[i].slice(); },
        setFontWeight: function () { return this; }
      };
    },
    setFrozenRows: function () {}
  };
  k.SpreadsheetApp = { getActiveSpreadsheet: function () { return { getSheetByName: function () { return sheet; }, insertSheet: function () { return sheet; } }; } };
  k.syncStatusSchreiben_('j-post@hsb-boden.de', { ok: true, weg: 'APIHUB', sent: { checked: 100, matched: 52 }, inbox: { checked: 100, matched: 3 }, errors: [] });
  k.syncStatusSchreiben_('j-post@hsb-boden.de', { ok: true, weg: 'APIHUB', sent: { checked: 100, matched: 1 }, inbox: { checked: 100, matched: 0 }, errors: [] });
  pruefe('Header + genau eine Zeile je Postfach (Upsert)', SYNC._data.length === 2, SYNC._data.length + ' Zeilen');
  pruefe('Zweiter Lauf ueberschreibt Zaehler', SYNC._data[1][4] === 1, JSON.stringify(SYNC._data[1]));
  pruefe('Fehlerspalte leer bei ok', SYNC._data[1][7] === '');
}

console.log('\n' + '='.repeat(70));
console.log('ERGEBNIS: ' + bestanden + ' bestanden, ' + fehlgeschlagen +
            ' fehlgeschlagen von ' + (bestanden + fehlgeschlagen));
console.log('='.repeat(70));
process.exit(fehlgeschlagen ? 1 : 0);
