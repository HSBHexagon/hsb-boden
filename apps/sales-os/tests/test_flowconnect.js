/**
 * Testet Jordis Knopfweg: Flow-Aufruf ueber den Logic-Flows-Connector.
 *
 * Hintergrund: Jordis Flow hat einen Button-Trigger. Dessen Aufruf-URL ist
 * von Microsoft gesperrt (ListCallbackUrlOperationBlocked), erreichbar ist
 * er nur ueber den Connector-Endpunkt mit einem Azure-Token. Genau so liefen
 * am 2026-09-07 seine 50 Entwuerfe - damals kam das Token von `az login`,
 * jetzt von der einmaligen Anmeldung im Sheet-Menue.
 *
 * Geprueft wird die AUSGELIEFERTE Datei, nicht die Quelle.
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

let AUFRUFE = [];
let USER_PROPS = {};

/** Baut ein JWT, wie Microsoft es ausstellt - nur der Nutzdatenteil zaehlt. */
function jwtFuer(konto) {
  const teil = Buffer.from(JSON.stringify({ upn: konto, aud: 'https://apihub.azure.com' }))
    .toString('base64').replace(/=+$/, '');
  return 'kopf.' + teil + '.signatur';
}

function makeFetch(opt) {
  opt = opt || {};
  const konto = opt.konto || 'j-post@hsb-boden.de';
  return function (url, params) {
    params = params || {};
    AUFRUFE.push({ url: url, method: (params.method || 'get').toLowerCase() });
    if (/\/send\b/.test(url)) {
      throw new Error('VERSAND VERSUCHT - darf nicht vorkommen: ' + url);
    }
    function antwort(code, obj, kopf) {
      return {
        getResponseCode: function () { return code; },
        getContentText: function () {
          return obj === null ? '' : JSON.stringify(obj);
        },
        getAllHeaders: function () { return kopf || {}; }
      };
    }
    if (/oauth2\/v2\.0\/devicecode/.test(url)) {
      return antwort(200, {
        device_code: 'DC-1', user_code: 'L56BXXHCY',
        verification_uri: 'https://login.microsoft.com/device',
        expires_in: 900, interval: 5
      });
    }
    if (/oauth2\/v2\.0\/token/.test(url)) {
      if (opt.tokenFehler) return antwort(400, { error: 'invalid_grant' });
      return antwort(200, {
        access_token: jwtFuer(konto), refresh_token: 'RT-neu', expires_in: 3600
      });
    }
    if (/\/triggers\/manual\/run/.test(url)) {
      if (opt.flowFehler) {
        return antwort(opt.flowFehler, { error: { code: 'Irgendwas' } });
      }
      if (opt.synchron) {
        // Verhalten eines Flows MIT Response-Aktion. Jordis Flow hat keine
        // mehr - dieser Zweig deckt nur ab, dass der Code den synchronen
        // Rumpf weiterhin korrekt durchreicht.
        return antwort(200, {
          status: 'DRAFTED', leadId: 'HSB-TEST-0001', batchId: 'BATCH-TEST',
          draftId: 'AAMk-JORDI-ENTWURF', internetMessageId: '<t@hsb-boden.de>',
          conversationId: 'CONV-1', attachmentSize: 1534405
        });
      }
      // Gemessene Wirklichkeit am 2026-09-11: ohne Response-Aktion antwortet
      // der Connector mit 202 und leerem Rumpf, die Laufkennung steht in der
      // Kopfzeile.
      return antwort(202, null,
        { 'x-ms-workflow-run-id': '08584124600456631756898045853CU27' });
    }
    throw new Error('Unerwarteter Aufruf: ' + url);
  };
}

function lade(opt) {
  AUFRUFE = [];
  USER_PROPS = Object.assign({
    HSB_FC_REFRESH_TOKEN: 'RT-vorhanden',
    HSB_FC_KONTO: (opt && opt.konto) || 'j-post@hsb-boden.de'
  }, (opt && opt.props) || {});

  const kontext = {
    console: console, Date: Date, Math: Math, JSON: JSON, Object: Object,
    String: String, Number: Number,
    UrlFetchApp: { fetch: makeFetch(opt) },
    Utilities: {
      base64DecodeWebSafe: function (s) {
        return Array.from(Buffer.from(s, 'base64'));
      },
      newBlob: function (bytes) {
        return { getDataAsString: function () { return Buffer.from(bytes).toString('utf8'); } };
      }
    },
    PropertiesService: {
      getUserProperties: function () {
        return {
          getProperty: function (k) {
            return USER_PROPS[k] === undefined ? null : USER_PROPS[k];
          },
          setProperty: function (k, v) { USER_PROPS[k] = String(v); },
          deleteProperty: function (k) { delete USER_PROPS[k]; }
        };
      },
      getScriptProperties: function () {
        return { getProperty: function () { return null; } };
      }
    },
    SpreadsheetApp: { getUi: function () { throw new Error('keine UI im Test'); } },
    HTTP_TIMEOUT_SECONDS: 60
  };
  vm.createContext(kontext);
  vm.runInContext(
    fs.readFileSync(path.join(DEPLOY, 'HSB_FlowConnect.js'), 'utf8'), kontext);
  return kontext;
}

const NUTZLAST = {
  leadId: 'HSB-TEST-0001', batchId: 'BATCH-TEST', to: 'kunde@example.com',
  subject: 'Betreff', bodyHtml: '<p>Text</p>',
  attachmentName: 'flyer.pdf', attachmentContentBytes: 'AAAA'
};

console.log('\n=== 1. Jordi erzeugt in seinem Postfach (202, asynchron) ===');
{
  const k = lade({ konto: 'j-post@hsb-boden.de' });
  const body = k.fcEntwurfErzeugen_(NUTZLAST, 'JORDI');
  pruefe('Als asynchron gekennzeichnet', body.async === true);
  pruefe('Status ACCEPTED_ASYNC', body.status === 'ACCEPTED_ASYNC');
  pruefe('Laufkennung aus der Kopfzeile',
         body.runId === '08584124600456631756898045853CU27', body.runId);
  pruefe('Draft-ID traegt die Laufkennung',
         body.draftId === 'LAUF:08584124600456631756898045853CU27');
  pruefe('Keine erfundene Anhanggroesse', body.attachmentSize === undefined);
  const lauf = AUFRUFE.filter(function (a) { return /triggers\/manual\/run/.test(a.url); });
  pruefe('Genau ein Flow-Aufruf', lauf.length === 1, lauf.length + ' Aufrufe');
  pruefe('Jordis Flow-ID im Aufruf',
         /47ee3d7a-626c-4fff-9e16-6d938949e4bd/.test(lauf[0].url));
  pruefe('Connector-Endpunkt, keine Aufruf-URL',
         /azure-apihub\.net\/apim\/logicflows/.test(lauf[0].url));
}

console.log('\n=== 1b. Synchroner Rumpf wird weiterhin durchgereicht ===');
{
  const k = lade({ konto: 'j-post@hsb-boden.de', synchron: true });
  const body = k.fcEntwurfErzeugen_(NUTZLAST, 'JORDI');
  pruefe('Status DRAFTED', body.status === 'DRAFTED');
  pruefe('Draft-ID da', body.draftId === 'AAMk-JORDI-ENTWURF');
  pruefe('Anhanggroesse durchgereicht', body.attachmentSize === 1534405);
  pruefe('Nicht als asynchron markiert', !body.async);
}

console.log('\n=== 2. Falsches Konto wird abgewiesen ===');
{
  // Joel ist verbunden, der Lead gehoert Jordi.
  const k = lade({ konto: 'j-cherino@hsb-boden.de' });
  let fehler = '';
  try { k.fcEntwurfErzeugen_(NUTZLAST, 'JORDI'); } catch (e) { fehler = String(e); }
  pruefe('Abbruch mit FALSCHES_KONTO', fehler.indexOf('FALSCHES_KONTO') >= 0,
         fehler.slice(0, 90));
  pruefe('KEIN Flow-Aufruf erfolgt',
         !AUFRUFE.some(function (a) { return /triggers\/manual\/run/.test(a.url); }));
}

console.log('\n=== 3. Wegwahl je Trigger-Art ===');
{
  const k = lade({});
  pruefe('Jordi braucht den Connector', k.fcBrauchtConnector_('JORDI') === true);
  pruefe('Joel braucht ihn nicht (Http-Trigger)',
         k.fcBrauchtConnector_('JOEL') === false);
  pruefe('Unbekannter Owner: kein Connector',
         k.fcBrauchtConnector_('NIEMAND') === false);
}

console.log('\n=== 4. Ohne Anmeldung: brauchbare Meldung ===');
{
  const k = lade({});
  delete USER_PROPS.HSB_FC_REFRESH_TOKEN;
  delete USER_PROPS.HSB_FC_ACCESS_TOKEN;
  let fehler = '';
  try { k.fcToken_(); } catch (e) { fehler = String(e); }
  pruefe('NICHT_VERBUNDEN gemeldet', fehler.indexOf('NICHT_VERBUNDEN') >= 0);
  pruefe('Meldung nennt den Menuepunkt', /Mit Outlook verbinden/.test(fehler));
  pruefe('fcVerbunden_() ist falsch', k.fcVerbunden_() === false);
}

console.log('\n=== 5. Abgelaufene Anmeldung ===');
{
  const k = lade({ tokenFehler: true });
  let fehler = '';
  try { k.fcToken_(); } catch (e) { fehler = String(e); }
  pruefe('VERBINDUNG_ABGELAUFEN gemeldet',
         fehler.indexOf('VERBINDUNG_ABGELAUFEN') >= 0, fehler.slice(0, 70));
  pruefe('Unbrauchbares Token entfernt', !USER_PROPS.HSB_FC_REFRESH_TOKEN);
}

console.log('\n=== 6. Flow-Fehler wird nicht als Erfolg verkauft ===');
{
  const k = lade({ konto: 'j-post@hsb-boden.de', flowFehler: 502 });
  let fehler = '';
  try { k.fcEntwurfErzeugen_(NUTZLAST, 'JORDI'); } catch (e) { fehler = String(e); }
  pruefe('FLOW_HTTP_502 gemeldet', fehler.indexOf('FLOW_HTTP_502') >= 0,
         fehler.slice(0, 60));
}

console.log('\n=== 7. Konto wird aus dem Token gelesen ===');
{
  const k = lade({});
  pruefe('upn korrekt entpackt',
         k.fcKontoAusToken_(jwtFuer('j-post@hsb-boden.de')) === 'j-post@hsb-boden.de');
  pruefe('Kaputtes Token wirft nicht', k.fcKontoAusToken_('unsinn') === '');
}

console.log('\n=== 8. Sendesicherheit und Weiche ===');
{
  const k = lade({ konto: 'j-post@hsb-boden.de' });
  k.fcEntwurfErzeugen_(NUTZLAST, 'JORDI');
  pruefe('REAL_EXTERNAL_SEND_COUNT = 0',
         AUFRUFE.filter(function (a) { return /\/send/.test(a.url); }).length === 0,
         AUFRUFE.length + ' Aufrufe');

  const quelle = fs.readFileSync(path.join(DEPLOY, 'HSB_FlowConnect.js'), 'utf8');
  const ohneKommentare = quelle.replace(/\/\*[\s\S]*?\*\//g, '')
                               .replace(/^\s*\/\/.*$/gm, '');
  pruefe('Kein /send im ausgelieferten Code',
         ohneKommentare.indexOf('/send') === -1);

  const adapter = fs.readFileSync(path.join(DEPLOY, 'HSB_DraftAdapter.gs.js'), 'utf8');
  pruefe('Connector hat Vorrang vor allem anderen',
         adapter.indexOf('fcBrauchtConnector_') < adapter.indexOf('graphVerbunden_()') &&
         adapter.indexOf('fcBrauchtConnector_') <
           adapter.indexOf('UrlFetchApp.fetch(adapterUrlFor_'));
  pruefe('Joels Aufruf-URL-Weg bleibt erhalten',
         /adapterUrlFor_\(owner\)/.test(adapter));
  pruefe('Anhangpruefung weiterhin im Aufrufer',
         /ANHANG_UNGEPRUEFT/.test(adapter));
}

console.log('\n' + '='.repeat(70));
console.log('ERGEBNIS: ' + bestanden + ' bestanden, ' + fehlgeschlagen +
            ' fehlgeschlagen von ' + (bestanden + fehlgeschlagen));
console.log('='.repeat(70));
process.exit(fehlgeschlagen ? 1 : 0);
