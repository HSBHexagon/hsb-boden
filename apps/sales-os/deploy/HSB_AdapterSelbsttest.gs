/**
 * HSB SALES OS — ADAPTER-SELBSTTEST
 * =================================
 * Einmalig nach dem Flow-Import ausführen.
 *
 * Prüft die Kette Apps Script -> Flow -> Outlook isoliert, OHNE die Engine
 * und OHNE einen echten Lead anzufassen. Es wird genau ein Entwurf an dich
 * selbst erzeugt, mit dem echten Flyer im Anhang.
 *
 * Damit ist getrennt nachweisbar:
 *   - die URL in den Skripteigenschaften stimmt
 *   - der Flow nimmt den Payload an
 *   - der Anhang kommt an
 *   - die Antwort enthält die Draft-IDs
 *
 * Erst wenn das grün ist, lohnt es sich, HSB_ADAPTER_renderMail_ zu
 * verdrahten und einen echten Batch zu fahren.
 */

function hsbAdapterSelbsttest() {
  var OWNER = 'JOEL';                       // ggf. auf 'JORDI' ändern
  var AN    = 'j-cherino@hsb-boden.de';     // Empfänger = du selbst

  var url = PropertiesService.getScriptProperties()
              .getProperty('HSB_ADAPTER_URL_' + OWNER);
  if (!url) {
    throw new Error('Skripteigenschaft HSB_ADAPTER_URL_' + OWNER + ' fehlt. ' +
                    'Projekteinstellungen -> Skripteigenschaften.');
  }
  if (url.indexOf('http') !== 0) {
    throw new Error('HSB_ADAPTER_URL_' + OWNER + ' sieht nicht wie eine URL aus.');
  }

  // Flyer über dieselbe Drive-ID wie das Asset-Gate
  var flyerId = {
    JOEL:  '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS',
    JORDI: '1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV'
  }[OWNER];
  var datei  = DriveApp.getFileById(flyerId);
  var bytes  = datei.getBlob().getBytes();
  var base64 = Utilities.base64Encode(bytes);

  Logger.log('Flyer: %s (%s Bytes, base64 %s Zeichen)',
             datei.getName(), bytes.length, base64.length);

  var payload = {
    leadId:  'SELBSTTEST',
    batchId: 'SELBSTTEST',
    owner:   OWNER,
    to:      AN,
    subject: 'HSB Adapter-Selbsttest — nur Entwurf',
    bodyHtml: '<p>Selbsttest des Draft Adapters.</p>' +
              '<p>Wenn diese Nachricht als <b>Entwurf</b> im Postfach liegt ' +
              'und der Flyer im Anhang hängt, funktioniert die Kette ' +
              'Apps&nbsp;Script → Power&nbsp;Automate → Outlook.</p>' +
              '<p>Diese Nachricht nicht senden — einfach löschen.</p>',
    attachmentName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
    attachmentContentBytes: base64
  };

  var res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  var text = res.getContentText();
  Logger.log('HTTP %s', code);
  Logger.log(text);

  if (code < 200 || code >= 300) {
    throw new Error(
      'Adapter antwortet mit HTTP ' + code + '.\n' + text.substring(0, 500) +
      '\n\nHäufige Ursachen:\n' +
      ' 402/403  Premium-Lizenz für den HTTP-Trigger fehlt\n' +
      ' 401      URL unvollständig kopiert (Signatur fehlt)\n' +
      ' 404      Flow ausgeschaltet oder gelöscht\n' +
      ' 502      Flow lief, aber DraftEmail schlug fehl — Flow-Verlauf ansehen'
    );
  }

  var body = {};
  try { body = JSON.parse(text); } catch (e) {}

  if (!body.draftId) {
    throw new Error('Antwort ohne draftId. Rohantwort:\n' + text.substring(0, 500));
  }

  var meldung =
    'SELBSTTEST BESTANDEN\n\n' +
    'draftId:           ' + body.draftId + '\n' +
    'internetMessageId: ' + (body.internetMessageId || '(leer)') + '\n' +
    'conversationId:    ' + (body.conversationId || '(leer)') + '\n\n' +
    'Jetzt in Outlook den Ordner "Entwürfe" öffnen und prüfen:\n' +
    ' - Betreff "HSB Adapter-Selbsttest"\n' +
    ' - Flyer als Anhang vorhanden\n' +
    ' - Nachricht ist ein bearbeitbarer Entwurf, nicht gesendet\n\n' +
    'Danach den Testentwurf löschen.';

  Logger.log(meldung);
  try { SpreadsheetApp.getUi().alert(meldung); } catch (e) {}
  return body;
}
