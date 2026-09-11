/**
 * HSB Sales OS — Jordis Knopfweg: Flow-Aufruf ueber den Logic-Flows-Connector.
 *
 * Warum es diese Datei gibt
 * -------------------------
 * Die beiden Flows unterscheiden sich in der Trigger-Art, und daraus folgt
 * ein unterschiedlicher Uebertragungsweg. Das ist keine Vorliebe, sondern
 * eine harte Grenze von Microsoft, am 2026-09-07 und erneut am 2026-09-11
 * an beiden Flows nachgemessen:
 *
 *   Joel  (Http-Trigger)   -> nur ueber die eigene Aufruf-URL. Der
 *                             Connector-Endpunkt antwortet hier mit HTTP 500.
 *   Jordi (Button-Trigger) -> nur ueber den Connector-Endpunkt. Die Aufruf-URL
 *                             ist gesperrt (ListCallbackUrlOperationBlocked).
 *
 * Joels Weg braucht kein Token - seine URL traegt eine Signatur. Jordis Weg
 * braucht ein Azure-Token. Genau dieses Token lieferte frueher `az login` auf
 * einem Rechner; hier holt es sich jede Person selbst per Geraetecode.
 *
 * Warum das ohne Administrator geht
 * ---------------------------------
 * Verwendet wird die Client-ID der Azure CLI. Diese Anwendung ist im Tenant
 * vorautorisiert - deshalb konnte sich Jordi frueher mit `az login` ohne
 * jede Adminbeteiligung anmelden. Eine eigene App-Registrierung waere
 * zustimmungspflichtig (gemessen: "Administratorgenehmigung erforderlich"),
 * diese ist es nicht.
 *
 * Sendesicherheit
 * ---------------
 * Aufgerufen wird ein Flow, der ausschliesslich `DraftEmail` enthaelt. Es
 * gibt keine Sendeaktion im Flow-Graphen, unabhaengig davon, was hier
 * uebergeben wird. Der Versand bleibt ein Schritt eines Menschen in Outlook.
 *
 * Wem gehoert das Token
 * ---------------------
 * Es liegt in den UserProperties, also getrennt je angemeldetem
 * Google-Konto. Vor jedem Entwurf wird geprueft, ob die angemeldete Person
 * zum Verantwortlichen des Leads passt - sonst schlaegt der Flow ohnehin mit
 * ConnectionAuthorizationFailed fehl, aber die klare Meldung kommt von hier.
 */

// ---------------------------------------------------------------- Konstanten

/** Azure CLI - im Tenant vorautorisiert, deshalb ohne Adminzustimmung nutzbar. */
var FC_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46';
var FC_TENANT_ID = '8adbbf2e-fd2c-4857-8540-bbcdb3a20f30';
var FC_SCOPE = 'https://apihub.azure.com/.default offline_access';

/**
 * Laufzeit-Endpunkt des Logic-Flows-Connectors dieser Umgebung.
 *
 * Fest hinterlegt, damit der Entwurfslauf nicht von einem zweiten Token fuer
 * eine andere Ressource abhaengt. Verschiebt Microsoft den Endpunkt, laesst
 * er sich ohne Codeaenderung ueber die Skripteigenschaft uebersteuern.
 */
var FC_RUNTIME_FALLBACK =
  'https://default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30.06' +
  '.common.germany.azure-apihub.net/apim/logicflows';
var FC_RUNTIME_PROP = 'HSB_FLOW_RUNTIME_URL';

/** Trigger-Art je Verantwortlichem - bestimmt den Uebertragungsweg. */
var FC_FLOWS = {
  JORDI: {
    flowId: '47ee3d7a-626c-4fff-9e16-6d938949e4bd',
    trigger: 'manual',
    triggerKind: 'Button',
    konto: 'j-post@hsb-boden.de'
  },
  JOEL: {
    flowId: '137601e8-7369-4a74-9564-959f1551e48d',
    trigger: 'manual',
    triggerKind: 'Http',
    konto: 'j-cherino@hsb-boden.de'
  }
};

var FC_PROPS = {
  refreshToken: 'HSB_FC_REFRESH_TOKEN',
  accessToken: 'HSB_FC_ACCESS_TOKEN',
  expiresAt: 'HSB_FC_EXPIRES_AT',
  konto: 'HSB_FC_KONTO',
  deviceCode: 'HSB_FC_DEVICE_CODE'
};

// ---------------------------------------------------------------- Anmeldung

function fcAuthUrl_(pfad) {
  return 'https://login.microsoftonline.com/' + FC_TENANT_ID +
         '/oauth2/v2.0/' + pfad;
}

function fcVerbindungStarten_() {
  var res = UrlFetchApp.fetch(fcAuthUrl_('devicecode'), {
    method: 'post',
    payload: { client_id: FC_CLIENT_ID, scope: FC_SCOPE },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());
  if (res.getResponseCode() !== 200 || !body.device_code) {
    throw new Error('Geraetecode nicht erhalten: ' +
                    res.getContentText().slice(0, 300));
  }
  PropertiesService.getUserProperties()
    .setProperty(FC_PROPS.deviceCode, body.device_code);
  return body;
}

function fcVerbindungAbschliessen_() {
  var props = PropertiesService.getUserProperties();
  var code = props.getProperty(FC_PROPS.deviceCode);
  if (!code) throw new Error('Kein offener Anmeldevorgang. Bitte neu starten.');

  var res = UrlFetchApp.fetch(fcAuthUrl_('token'), {
    method: 'post',
    payload: {
      grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
      client_id: FC_CLIENT_ID,
      device_code: code
    },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());

  if (body.error === 'authorization_pending') return { wartet: true };
  if (body.error) {
    props.deleteProperty(FC_PROPS.deviceCode);
    throw new Error('Anmeldung fehlgeschlagen: ' + body.error + ' ' +
                    String(body.error_description || '').slice(0, 200));
  }

  props.deleteProperty(FC_PROPS.deviceCode);
  fcTokenSpeichern_(body);
  var konto = fcKontoAusToken_(body.access_token);
  props.setProperty(FC_PROPS.konto, konto);
  return { wartet: false, konto: konto };
}

function fcTokenSpeichern_(body) {
  var props = PropertiesService.getUserProperties();
  props.setProperty(FC_PROPS.accessToken, body.access_token);
  props.setProperty(FC_PROPS.expiresAt,
                    String(Date.now() + (body.expires_in - 120) * 1000));
  if (body.refresh_token) {
    props.setProperty(FC_PROPS.refreshToken, body.refresh_token);
  }
}

/**
 * Liest den Kontonamen aus dem Token.
 *
 * Bewusst ohne Signaturpruefung: der Wert dient nur dazu, dem Menschen zu
 * zeigen, als wer er verbunden ist, und einen offensichtlich falschen
 * Verantwortlichen frueh abzufangen. Die eigentliche Autorisierung macht
 * Microsoft beim Flow-Aufruf.
 */
function fcKontoAusToken_(token) {
  try {
    var teil = String(token).split('.')[1];
    var roh = Utilities.newBlob(
      Utilities.base64DecodeWebSafe(teil)).getDataAsString();
    var anspruch = JSON.parse(roh);
    return String(anspruch.upn || anspruch.unique_name ||
                  anspruch.preferred_username || '').toLowerCase();
  } catch (fehler) {
    return '';
  }
}

function fcToken_() {
  var props = PropertiesService.getUserProperties();
  var token = props.getProperty(FC_PROPS.accessToken);
  var faellig = Number(props.getProperty(FC_PROPS.expiresAt) || 0);
  if (token && Date.now() < faellig) return token;

  var refresh = props.getProperty(FC_PROPS.refreshToken);
  if (!refresh) {
    throw new Error('NICHT_VERBUNDEN: Dieses Google-Konto ist mit keinem ' +
      'Microsoft-Konto verbunden. Menue "HSB Sales OS" -> ' +
      '"Mit Outlook verbinden".');
  }
  var res = UrlFetchApp.fetch(fcAuthUrl_('token'), {
    method: 'post',
    payload: {
      grant_type: 'refresh_token',
      client_id: FC_CLIENT_ID,
      refresh_token: refresh,
      scope: FC_SCOPE
    },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());
  if (body.error || !body.access_token) {
    props.deleteProperty(FC_PROPS.refreshToken);
    props.deleteProperty(FC_PROPS.accessToken);
    throw new Error('VERBINDUNG_ABGELAUFEN: ' + String(body.error || '') +
      '. Bitte im Menue neu verbinden.');
  }
  fcTokenSpeichern_(body);
  return body.access_token;
}

function fcVerbunden_() {
  return !!PropertiesService.getUserProperties()
    .getProperty(FC_PROPS.refreshToken);
}

function fcKonto_() {
  return PropertiesService.getUserProperties()
    .getProperty(FC_PROPS.konto) || '';
}

function fcRuntimeUrl_() {
  var eigen = PropertiesService.getScriptProperties()
    .getProperty(FC_RUNTIME_PROP);
  return String(eigen || FC_RUNTIME_FALLBACK).replace(/\/+$/, '');
}

// ---------------------------------------------------------------- Entwurf

/**
 * Loest einen Flow-Lauf ueber den Connector-Endpunkt aus.
 *
 * Die Antwort ist der Rueckgabekoerper der Response-Aktion im Flow und hat
 * damit dasselbe Format wie beim Aufruf ueber die Aufruf-URL. Die
 * Anhangpruefung im Aufrufer bleibt dadurch unveraendert gueltig.
 */
function fcEntwurfErzeugen_(payload, ownerKey) {
  var flow = FC_FLOWS[ownerKey];
  if (!flow) throw new Error('Unbekannter Verantwortlicher: ' + ownerKey);

  var token = fcToken_();
  var konto = fcKonto_() || fcKontoAusToken_(token);

  // Fail-closed. Der Flow wuerde ohnehin mit ConnectionAuthorizationFailed
  // abbrechen; diese Meldung sagt dem Menschen, was tatsaechlich los ist.
  if (konto && konto !== String(flow.konto).toLowerCase()) {
    throw new Error('FALSCHES_KONTO: Lead gehoert ' + ownerKey + ' (' +
      flow.konto + '), verbunden ist aber ' + konto +
      '. Dieser Lead muss von ' + ownerKey + ' selbst erzeugt werden.');
  }

  var url = fcRuntimeUrl_() + '/' + flow.flowId + '/triggers/' +
            flow.trigger + '/run?api-version=2016-11-01';
  var res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token },
    payload: JSON.stringify(payload),
    timeoutSeconds: HTTP_TIMEOUT_SECONDS,
    muteHttpExceptions: true
  });
  var code = res.getResponseCode();
  if (code !== 200 && code !== 202) {
    throw new Error('FLOW_HTTP_' + code + ': ' +
                    res.getContentText().slice(0, 300));
  }
  try {
    return JSON.parse(res.getContentText());
  } catch (fehler) {
    throw new Error('INVALID_RESPONSE_JSON vom Connector-Endpunkt');
  }
}

/** Braucht dieser Verantwortliche den Connector-Weg? */
function fcBrauchtConnector_(ownerKey) {
  var flow = FC_FLOWS[ownerKey];
  return !!flow && flow.triggerKind === 'Button';
}

// ---------------------------------------------------------------- Bedienung

function uiFlowVerbinden() {
  var ui = SpreadsheetApp.getUi();
  var start = fcVerbindungStarten_();
  ui.alert(
    'Mit Outlook verbinden',
    'Einmalige Anmeldung bei Microsoft - dieselbe wie frueher per az login.\n\n' +
    '1. Oeffne im Browser:  ' + start.verification_uri + '\n' +
    '2. Gib diesen Code ein:  ' + start.user_code + '\n' +
    '3. Melde dich mit DEINEM Geschaeftskonto an\n' +
    '   (Jordi: j-post@hsb-boden.de, Joel: j-cherino@hsb-boden.de)\n' +
    '4. Komm hierher zurueck und klicke OK\n\n' +
    'Dein Passwort sieht nur Microsoft. Der Code ist ' +
    Math.round(start.expires_in / 60) + ' Minuten gueltig.',
    ui.ButtonSet.OK);

  var ergebnis;
  try {
    ergebnis = fcVerbindungAbschliessen_();
  } catch (fehler) {
    ui.alert('Verbindung fehlgeschlagen', String(fehler), ui.ButtonSet.OK);
    return;
  }
  if (ergebnis.wartet) {
    ui.alert('Noch nicht fertig',
      'Die Anmeldung im Browser ist noch nicht abgeschlossen.\n\n' +
      'Schliesse sie ab und rufe den Menuepunkt noch einmal auf - ' +
      'der Code bleibt gueltig.', ui.ButtonSet.OK);
    return;
  }
  ui.alert('Verbunden',
    'Dieses Google-Konto ist jetzt mit\n\n    ' + ergebnis.konto +
    '\n\nverbunden. Entwuerfe entstehen ab sofort in diesem Postfach.',
    ui.ButtonSet.OK);
}

function uiFlowStatus() {
  var ui = SpreadsheetApp.getUi();
  var zeilen = [];
  zeilen.push('Microsoft-Verbindung dieses Google-Kontos:');
  if (!fcVerbunden_()) {
    zeilen.push('  nicht verbunden');
    zeilen.push('', 'Menue -> "Mit Outlook verbinden".');
  } else {
    zeilen.push('  ' + (fcKonto_() || '(Konto unbekannt)'));
    try {
      fcToken_();
      zeilen.push('  Token gueltig.');
    } catch (fehler) {
      zeilen.push('  FEHLER: ' + String(fehler).slice(0, 160));
    }
  }
  zeilen.push('', 'Wege je Verantwortlichem:');
  Object.keys(FC_FLOWS).forEach(function (k) {
    zeilen.push('  ' + k + ': ' + FC_FLOWS[k].triggerKind +
      (FC_FLOWS[k].triggerKind === 'Button'
        ? ' -> Connector (Anmeldung noetig)'
        : ' -> Aufruf-URL (ohne Anmeldung)'));
  });
  ui.alert('Verbindungsstatus', zeilen.join('\n'), ui.ButtonSet.OK);
}

function uiFlowTrennen() {
  var ui = SpreadsheetApp.getUi();
  if (ui.alert('Verbindung trennen',
      'Das gespeicherte Token dieses Google-Kontos wird geloescht.\n' +
      'Bereits erzeugte Entwuerfe bleiben unberuehrt.\n\nFortfahren?',
      ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  var props = PropertiesService.getUserProperties();
  Object.keys(FC_PROPS).forEach(function (k) {
    props.deleteProperty(FC_PROPS[k]);
  });
  ui.alert('Getrennt', 'Das Token wurde geloescht.', ui.ButtonSet.OK);
}
