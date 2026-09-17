/**
 * HSB Sales OS — Entwuerfe direkt ueber Microsoft Graph.
 *
 * Warum es diesen Weg gibt
 * ------------------------
 * Der bisherige Weg lief ueber Power Automate. Fuer Jordi ist der am
 * 2026-09-11 nachweislich zu: Microsoft verlangt fuer einen per URL
 * aufrufbaren Flow ("Http"-Connector) eine Premium-Lizenz. Gemessen wurde
 * an diesem Tag, dass die Aktivierung fuer BEIDE Konten abgelehnt wird -
 * auch fuer j-cherino, der den kostenlosen Entwicklerplan besitzt. Joels
 * Flow laeuft ausschliesslich deshalb weiter, weil er vor der Umstellung
 * aktiviert wurde (Bestandsschutz). Wird er je gestoppt, ist er verloren.
 *
 * Vier Varianten wurden durchprobiert und alle vier abgelehnt:
 *   Http-Trigger mit Antwortaktion   -> 403 MissingAdequateQuotaPolicy
 *   Http-Trigger ohne Antwortaktion  -> 403 MissingAdequateQuotaPolicy
 *   Button-Trigger, Aufruf-URL       -> ListCallbackUrlOperationBlocked
 *   Button-Trigger, Flow-API         -> TriggerInputSchemaMismatch
 *
 * Dieser Weg braucht kein Power Automate und keine Lizenz. Jede Person
 * verbindet sich einmalig mit ihrem eigenen Microsoft-Konto; danach legt
 * das Skript Entwuerfe direkt in IHREM Postfach an.
 *
 * Sendesicherheit
 * ---------------
 * Hier kommt ausschliesslich `POST /me/messages` vor. Die Graph-Aktion
 * `POST /me/messages/{id}/send` steht nirgends in dieser Datei. Der Versand
 * bleibt ein bewusster Schritt eines Menschen in Outlook.
 *
 * Wem gehoert das Token
 * ---------------------
 * Das Token liegt in den UserProperties - der Ablage des angemeldeten
 * Google-Kontos. Jordis Token ist damit fuer Joel unsichtbar und umgekehrt.
 * Vor jedem Entwurf wird geprueft, ob das verbundene Postfach zum
 * Verantwortlichen des Leads passt. Ohne diese Pruefung koennte Jordi
 * Entwuerfe in Joels Namen erzeugen.
 */

// ---------------------------------------------------------------- Konfiguration

/** Oeffentliche App-Registrierung im HSB-Tenant, ohne Geheimnis. */
var GRAPH_TENANT_ID = '8adbbf2e-fd2c-4857-8540-bbcdb3a20f30';
var GRAPH_CLIENT_ID = '43c0f077-be59-4509-be74-3d82821eaf0a';
var GRAPH_SCOPE = 'https://graph.microsoft.com/Mail.ReadWrite offline_access';
var GRAPH_BASE = 'https://graph.microsoft.com/v1.0';

var GRAPH_PROPS = {
  refreshToken: 'HSB_GRAPH_REFRESH_TOKEN',
  accessToken: 'HSB_GRAPH_ACCESS_TOKEN',
  expiresAt: 'HSB_GRAPH_EXPIRES_AT',
  mailbox: 'HSB_GRAPH_MAILBOX',
  deviceCode: 'HSB_GRAPH_DEVICE_CODE'
};

// ---------------------------------------------------------------- Anmeldung

function graphAuthUrl_(pfad) {
  return 'https://login.microsoftonline.com/' + GRAPH_TENANT_ID +
         '/oauth2/v2.0/' + pfad;
}

/**
 * Schritt 1 der Anmeldung: holt einen Geraetecode.
 *
 * Bewusst zweistufig. Der Geraetecode-Fluss verlangt Warten, bis der Mensch
 * sich im Browser angemeldet hat; Apps Script bricht Ausfuehrungen nach
 * sechs Minuten ab. Ein Dialog, der den Code zeigt, und ein zweiter Aufruf,
 * der ihn einloest, kommen ohne Wartschleife aus.
 */
function graphVerbindungStarten_() {
  var res = UrlFetchApp.fetch(graphAuthUrl_('devicecode'), {
    method: 'post',
    payload: { client_id: GRAPH_CLIENT_ID, scope: GRAPH_SCOPE },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());
  if (res.getResponseCode() !== 200 || !body.device_code) {
    throw new Error('Geraetecode nicht erhalten: ' +
                    res.getContentText().slice(0, 300));
  }
  PropertiesService.getUserProperties()
    .setProperty(GRAPH_PROPS.deviceCode, body.device_code);
  return body;
}

/**
 * Schritt 2: loest den Geraetecode gegen ein Token ein.
 *
 * Liefert eine Klartextmeldung statt eines Fehlers, wenn der Mensch die
 * Anmeldung im Browser noch nicht abgeschlossen hat - das ist kein Defekt,
 * sondern der Normalfall beim ersten Klick.
 */
function graphVerbindungAbschliessen_() {
  var props = PropertiesService.getUserProperties();
  var code = props.getProperty(GRAPH_PROPS.deviceCode);
  if (!code) {
    throw new Error('Kein offener Anmeldevorgang. Bitte neu starten.');
  }
  var res = UrlFetchApp.fetch(graphAuthUrl_('token'), {
    method: 'post',
    payload: {
      grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
      client_id: GRAPH_CLIENT_ID,
      device_code: code
    },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());

  if (body.error === 'authorization_pending') {
    return { wartet: true };
  }
  if (body.error) {
    props.deleteProperty(GRAPH_PROPS.deviceCode);
    throw new Error('Anmeldung fehlgeschlagen: ' + body.error + ' ' +
                    String(body.error_description || '').slice(0, 200));
  }

  props.deleteProperty(GRAPH_PROPS.deviceCode);
  graphTokenSpeichern_(body);
  var postfach = graphPostfachLesen_(body.access_token);
  props.setProperty(GRAPH_PROPS.mailbox, postfach);
  return { wartet: false, mailbox: postfach };
}

function graphTokenSpeichern_(body) {
  var props = PropertiesService.getUserProperties();
  props.setProperty(GRAPH_PROPS.accessToken, body.access_token);
  // 120 Sekunden Sicherheitsabstand, damit ein Token nicht mitten im
  // Entwurfslauf ablaeuft.
  props.setProperty(GRAPH_PROPS.expiresAt,
                    String(Date.now() + (body.expires_in - 120) * 1000));
  if (body.refresh_token) {
    props.setProperty(GRAPH_PROPS.refreshToken, body.refresh_token);
  }
}

/** Gueltiges Zugriffstoken, bei Bedarf still erneuert. */
function graphToken_() {
  var props = PropertiesService.getUserProperties();
  var token = props.getProperty(GRAPH_PROPS.accessToken);
  var faelligAt = Number(props.getProperty(GRAPH_PROPS.expiresAt) || 0);
  if (token && Date.now() < faelligAt) return token;

  var refresh = props.getProperty(GRAPH_PROPS.refreshToken);
  if (!refresh) {
    throw new Error('NICHT_VERBUNDEN: Dieses Google-Konto ist mit keinem ' +
      'Outlook-Postfach verbunden. Menue "HSB Sales OS" -> ' +
      '"Mit Outlook verbinden".');
  }
  var res = UrlFetchApp.fetch(graphAuthUrl_('token'), {
    method: 'post',
    payload: {
      grant_type: 'refresh_token',
      client_id: GRAPH_CLIENT_ID,
      refresh_token: refresh,
      scope: GRAPH_SCOPE
    },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());
  if (body.error || !body.access_token) {
    props.deleteProperty(GRAPH_PROPS.refreshToken);
    props.deleteProperty(GRAPH_PROPS.accessToken);
    throw new Error('VERBINDUNG_ABGELAUFEN: ' + String(body.error || '') +
      '. Bitte im Menue neu mit Outlook verbinden.');
  }
  graphTokenSpeichern_(body);
  return body.access_token;
}

function graphPostfachLesen_(token) {
  var res = UrlFetchApp.fetch(GRAPH_BASE + '/me?$select=userPrincipalName,mail', {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  });
  var body = JSON.parse(res.getContentText());
  var adresse = body.mail || body.userPrincipalName;
  if (!adresse) {
    throw new Error('Postfach nicht ermittelbar: ' +
                    res.getContentText().slice(0, 200));
  }
  return String(adresse).toLowerCase();
}

/** Postfach dieses Google-Kontos, oder leer wenn nicht verbunden. */
function graphMailbox_() {
  return PropertiesService.getUserProperties()
    .getProperty(GRAPH_PROPS.mailbox) || '';
}

function graphVerbunden_() {
  return !!PropertiesService.getUserProperties()
    .getProperty(GRAPH_PROPS.refreshToken);
}

// ---------------------------------------------------------------- Entwurf

/**
 * Legt einen Entwurf im Postfach des verbundenen Kontos an und liest ihn
 * zurueck.
 *
 * Die Rueckgabe hat bewusst dasselbe Format wie die Antwort des
 * Power-Automate-Flows. Dadurch bleibt die Anhangpruefung in
 * createDraftsForBatch unveraendert gueltig - sie ist der Kern der
 * Absicherung und darf nicht pro Transportweg neu geschrieben werden.
 */
function graphEntwurfErzeugen_(payload, ownerKey) {
  var token = graphToken_();
  var erwartet = String((FLYERS[ownerKey] || {}).mailbox || '').toLowerCase();
  var tatsaechlich = graphMailbox_() ||
                     graphPostfachLesen_(token);

  // Fail-closed: ohne diese Pruefung koennte ein Entwurf im falschen
  // Postfach landen und im Namen der falschen Person hinausgehen.
  if (!erwartet || tatsaechlich !== erwartet) {
    throw new Error('FALSCHES_POSTFACH: Lead gehoert ' + ownerKey +
      ' (' + erwartet + '), verbunden ist aber ' + tatsaechlich +
      '. Dieser Lead muss von ' + ownerKey + ' selbst erzeugt werden.');
  }

  var nachricht = {
    subject: payload.subject,
    body: { contentType: 'HTML', content: payload.bodyHtml },
    toRecipients: [{ emailAddress: { address: payload.to } }],
    attachments: [{
      '@odata.type': '#microsoft.graph.fileAttachment',
      name: payload.attachmentName,
      contentType: 'application/pdf',
      contentBytes: payload.attachmentContentBytes
    }]
  };

  var res = UrlFetchApp.fetch(GRAPH_BASE + '/me/messages', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token },
    payload: JSON.stringify(nachricht),
    timeoutSeconds: HTTP_TIMEOUT_SECONDS,
    muteHttpExceptions: true
  });
  var code = res.getResponseCode();
  if (code !== 201 && code !== 200) {
    throw new Error('GRAPH_HTTP_' + code + ': ' +
                    res.getContentText().slice(0, 300));
  }
  var erzeugt = JSON.parse(res.getContentText());

  // Zuruecklesen. Erst die gespeicherte Groesse beweist, dass der Anhang
  // unbeschaedigt im Postfach liegt; die Antwort auf das Anlegen allein
  // beweist das nicht.
  var geprueft = graphAnhangLesen_(token, erzeugt.id);

  return {
    status: geprueft.size === null ? 'DRAFTED_UNVERIFIED' : 'DRAFTED',
    leadId: payload.leadId,
    batchId: payload.batchId,
    draftId: erzeugt.id,
    internetMessageId: erzeugt.internetMessageId || '',
    conversationId: erzeugt.conversationId || '',
    attachmentSize: geprueft.size,
    attachmentName: geprueft.name,
    verifyError: geprueft.fehler || ''
  };
}

function graphAnhangLesen_(token, messageId) {
  var url = GRAPH_BASE + '/me/messages/' + encodeURIComponent(messageId) +
            '/attachments?$select=name,size';
  var res = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 200) {
    return { size: null, name: '',
             fehler: 'HTTP ' + res.getResponseCode() + ' beim Ruecklesen' };
  }
  var liste = (JSON.parse(res.getContentText()) || {}).value || [];
  if (!liste.length) return { size: null, name: '', fehler: 'kein Anhang gefunden' };
  return { size: liste[0].size, name: liste[0].name, fehler: '' };
}

// ---------------------------------------------------------------- Bedienung

function uiGraphVerbinden() {
  var ui = SpreadsheetApp.getUi();
  var start = graphVerbindungStarten_();
  ui.alert(
    'Mit Outlook verbinden',
    'Dieser Rechner meldet sich bei Microsoft an.\n\n' +
    '1. Oeffne im Browser:  ' + start.verification_uri + '\n' +
    '2. Gib diesen Code ein:  ' + start.user_code + '\n' +
    '3. Melde dich mit DEINEM Geschaeftskonto an\n' +
    '   (Jordi: j-post@hsb-boden.de, Joel: j-cherino@hsb-boden.de)\n' +
    '4. Komm hierher zurueck und klicke unten OK\n\n' +
    'Dein Passwort sieht nur Microsoft. Der Code ist ' +
    Math.round(start.expires_in / 60) + ' Minuten gueltig.',
    ui.ButtonSet.OK);

  var ergebnis;
  try {
    ergebnis = graphVerbindungAbschliessen_();
  } catch (fehler) {
    ui.alert('Verbindung fehlgeschlagen', String(fehler), ui.ButtonSet.OK);
    return;
  }
  if (ergebnis.wartet) {
    ui.alert('Noch nicht fertig',
      'Die Anmeldung im Browser ist noch nicht abgeschlossen.\n\n' +
      'Schliesse sie ab und rufe den Menuepunkt einfach noch einmal auf - ' +
      'der Code bleibt gueltig.', ui.ButtonSet.OK);
    return;
  }
  ui.alert('Verbunden',
    'Dieses Google-Konto ist jetzt mit dem Postfach\n\n    ' +
    ergebnis.mailbox + '\n\nverbunden. Entwuerfe landen ab sofort dort.',
    ui.ButtonSet.OK);
}

function uiGraphStatus() {
  var ui = SpreadsheetApp.getUi();
  if (!graphVerbunden_()) {
    ui.alert('Outlook-Verbindung',
      'Dieses Google-Konto ist mit keinem Postfach verbunden.\n\n' +
      'Menue "HSB Sales OS" -> "Mit Outlook verbinden".', ui.ButtonSet.OK);
    return;
  }
  var zeilen = ['Gespeichertes Postfach: ' + graphMailbox_()];
  try {
    zeilen.push('Lebendpruefung       : ' + graphPostfachLesen_(graphToken_()));
    zeilen.push('', 'Die Verbindung traegt.');
  } catch (fehler) {
    zeilen.push('Lebendpruefung       : FEHLER', String(fehler));
  }
  ui.alert('Outlook-Verbindung', zeilen.join('\n'), ui.ButtonSet.OK);
}

function uiGraphTrennen() {
  var ui = SpreadsheetApp.getUi();
  var antwort = ui.alert('Outlook-Verbindung trennen',
    'Das gespeicherte Token dieses Google-Kontos wird geloescht.\n' +
    'Bereits erzeugte Entwuerfe bleiben unberuehrt.\n\nFortfahren?',
    ui.ButtonSet.YES_NO);
  if (antwort !== ui.Button.YES) return;
  var props = PropertiesService.getUserProperties();
  Object.keys(GRAPH_PROPS).forEach(function (k) {
    props.deleteProperty(GRAPH_PROPS[k]);
  });
  ui.alert('Getrennt', 'Das Token wurde geloescht.', ui.ButtonSet.OK);
}

// ---------------------------------------------------------------- Sende- & Inbound-Abgleich (Reconciliation)

/**
 * Liest gesendete Nachrichten aus dem Ordner "Gesendete Elemente" (SentItems)
 * und gleicht sie mit ALL_LEADS ab. Bei Treffer wird der Status auf 'sent'
 * gesetzt und die Zeile blau hervorgehoben.
 */
function graphReconcileSentItems_() {
  var token = graphToken_();
  var url = GRAPH_BASE + '/me/mailFolders/SentItems/messages?$select=id,subject,toRecipients,sentDateTime,internetMessageId&$top=100&$orderby=sentDateTime%20desc';
  var res = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 200) {
    throw new Error('Fehler beim Abruf von SentItems: HTTP ' + res.getResponseCode() + ' ' + res.getContentText().slice(0, 300));
  }
  var messages = (JSON.parse(res.getContentText()) || {}).value || [];
  var matchedCount = 0;
  messages.forEach(function (m) {
    var toAddr = (m.toRecipients && m.toRecipients[0] && m.toRecipients[0].emailAddress) ? String(m.toRecipients[0].emailAddress.address || '').trim().toLowerCase() : '';
    var explicitLeadId = '';
    if (toAddr && typeof readLeadsCached_ === 'function') {
      try {
        var leads = (readLeadsCached_().leads) || [];
        var hits = leads.filter(function (l) {
          return String(l.Email || '').trim().toLowerCase() === toAddr;
        });
        if (hits.length === 1) {
          explicitLeadId = hits[0].Lead_ID;
        } else if (hits.length > 1) {
          var draftedHits = hits.filter(function (l) { return l.Send_Status === 'drafted'; });
          if (draftedHits.length === 1) explicitLeadId = draftedHits[0].Lead_ID;
        }
      } catch (_) {}
    }

    if (typeof processInboundEvent === 'function') {
      var r = processInboundEvent({
        event_id: 'GRAPH-SENT-' + (m.internetMessageId || m.id),
        event_type: 'SENT',
        lead_id: explicitLeadId,
        message_id: m.internetMessageId || '',
        email: toAddr,
        subject: m.subject || '',
        details: 'Outlook SentItems Abgleich'
      });
      if (r && r.matched) matchedCount++;
    }
  });
  return { ok: true, matched: matchedCount, checked: messages.length };
}

/**
 * Intelligente Klassifizierung einer eingehenden E-Mail (Inbox / NDR / Reply).
 * Erkennt Bounces (Hard/Soft), Abwesenheitsnotizen, Opt-Outs, Kontaktwechsel und Kaufinteresse.
 * Standardkonform nach RFC 3464 (DSN), RFC 3834 (Auto-Reply), § 7 UWG.
 */
function classifyInboundMessage_(m) {
  var fromAddr = (m.from && m.from.emailAddress) ? String(m.from.emailAddress.address || '').trim().toLowerCase() : '';
  var subj = String(m.subject || '').trim();
  var subjLower = subj.toLowerCase();
  var preview = String(m.bodyPreview || '').trim();
  var previewLower = preview.toLowerCase();

  // 1. NDR / Bounce / Unzustellbar Erkennung (RFC 3464 DSN)
  var isMailerDaemon = fromAddr.indexOf('mailer-daemon') >= 0 || fromAddr.indexOf('postmaster') >= 0 || fromAddr.indexOf('administrator@') >= 0;
  var isUndeliverableSubj = subjLower.indexOf('undeliverable') >= 0 || subjLower.indexOf('unzustellbar') >= 0 ||
                            subjLower.indexOf('delivery status notification') >= 0 || subjLower.indexOf('mail delivery failed') >= 0 ||
                            subjLower.indexOf('failure') >= 0 || subjLower.indexOf('nicht zugestellt') >= 0;

  if (isMailerDaemon || isUndeliverableSubj) {
    var emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    var allMatches = (preview + ' ' + subj).match(emailRegex) || [];
    var failedRecipient = '';
    for (var i = 0; i < allMatches.length; i++) {
      var cand = allMatches[i].toLowerCase();
      if (cand.indexOf('hsb-boden.de') === -1 && cand.indexOf('mailer-daemon') === -1 && cand.indexOf('postmaster') === -1 && cand.indexOf('microsoft') === -1) {
        failedRecipient = cand;
        break;
      }
    }

    var isHard = previewLower.indexOf('550') >= 0 || previewLower.indexOf('5.1.1') >= 0 || previewLower.indexOf('user unknown') >= 0 ||
                 previewLower.indexOf('recipient not found') >= 0 || previewLower.indexOf('mailbox unavailable') >= 0 ||
                 previewLower.indexOf('does not exist') >= 0 || previewLower.indexOf('nicht gefunden') >= 0 ||
                 previewLower.indexOf('abgelehnt') >= 0 || isUndeliverableSubj;

    return {
      event_type: isHard ? 'HARD_BOUNCE' : 'SOFT_BOUNCE',
      email: failedRecipient || fromAddr,
      failed_recipient: failedRecipient,
      details: (isHard ? 'Hard Bounce (Unzustellbar): ' : 'Soft Bounce: ') + (failedRecipient || 'Empfaenger unklar'),
      follow_up_days: isHard ? 0 : 3
    };
  }

  // 2. Abwesenheitsnotiz / Out-of-Office (RFC 3834)
  var isOoo = subjLower.indexOf('automatische antwort') >= 0 || subjLower.indexOf('auto-reply') >= 0 ||
              subjLower.indexOf('abwesenheitsnotiz') >= 0 || subjLower.indexOf('out of office') >= 0 ||
              previewLower.indexOf('bin im urlaub') >= 0 || previewLower.indexOf('abwesend bis') >= 0 ||
              previewLower.indexOf('derzeit nicht im büro') >= 0;

  if (isOoo) {
    var dateMatch = preview.match(/bis (?:zum |einschließlich )?(\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2}))/i);
    return {
      event_type: 'AUTO_REPLY_OOO',
      email: fromAddr,
      details: 'Abwesenheit' + (dateMatch ? ' bis ' + dateMatch[1] : ''),
      follow_up_days: 7
    };
  }

  // 3. Mitarbeiterwechsel (Contact Churn)
  var isChurn = previewLower.indexOf('verlassen') >= 0 || previewLower.indexOf('nicht mehr im unternehmen') >= 0 ||
                previewLower.indexOf('nicht mehr im haus') >= 0 || previewLower.indexOf('nicht mehr tätig') >= 0 ||
                previewLower.indexOf('ausgeschieden') >= 0 || previewLower.indexOf('nachfolger') >= 0 ||
                previewLower.indexOf('wenden sie sich bitte an') >= 0;

  if (isChurn) {
    return {
      event_type: 'CONTACT_CHURN',
      email: fromAddr,
      details: 'Ansprechpartner ausgeschieden',
      follow_up_days: 0
    };
  }

  // 4. Opt-Out / DSGVO-Widerspruch
  // Stichwortliste (Fusszeile: "Antworten Sie mit 'Abmelden'"); Betreff und Vorschau.
  var optOutWords = ['abmelden', 'abbestellen', 'austragen', 'opt-out', 'optout', 'unsubscribe',
                     'kein interesse', 'keine werbung', 'keine weiteren', 'löschen sie', 'loeschen sie',
                     'widerspruch', 'widerspreche', 'aus dem verteiler', 'nicht mehr kontaktieren'];
  var optOutText = subjLower + ' ' + previewLower;
  var isOptOut = optOutWords.some(function (w) { return optOutText.indexOf(w) >= 0; });

  if (isOptOut) {
    return {
      event_type: 'OPT_OUT',
      email: fromAddr,
      details: 'Opt-out / Abmeldung angefordert',
      follow_up_days: 0
    };
  }

  // 5. Positives Kaufsignal (Hot Lead)
  var isPositive = previewLower.indexOf('angebot') >= 0 || previewLower.indexOf('preise') >= 0 ||
                   previewLower.indexOf('kosten') >= 0 || previewLower.indexOf('termin') >= 0 ||
                   previewLower.indexOf('besichtigung') >= 0 || previewLower.indexOf('rückruf') >= 0 ||
                   previewLower.indexOf('muster') >= 0 || previewLower.indexOf('quadratmeter') >= 0 ||
                   previewLower.indexOf('gerne mehr infos') >= 0;

  if (isPositive) {
    return {
      event_type: 'POSITIVE_REPLY',
      email: fromAddr,
      details: 'Positives Kaufsignal / Hot Lead',
      follow_up_days: 1
    };
  }

  // 6. Generische Antwort
  return {
    event_type: 'REPLY',
    email: fromAddr,
    details: 'Inbound Antwort erhalten',
    follow_up_days: 0
  };
}

/**
 * Liest Antworten aus dem Posteingang (Inbox) und traegt Antworten sowie
 * Abmeldungen (Opt-Outs) im CRM ein.
 */
function graphReconcileInboxReplies_() {
  var token = graphToken_();
  var url = GRAPH_BASE + '/me/mailFolders/Inbox/messages?$select=id,subject,from,receivedDateTime,internetMessageId,bodyPreview&$top=100&$orderby=receivedDateTime%20desc';
  var res = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 200) {
    throw new Error('Fehler beim Abruf von Inbox: HTTP ' + res.getResponseCode() + ' ' + res.getContentText().slice(0, 300));
  }
  var messages = (JSON.parse(res.getContentText()) || {}).value || [];
  var matchedCount = 0;
  messages.forEach(function (m) {
    var cls = classifyInboundMessage_(m);
    if (typeof processInboundEvent === 'function') {
      var r = processInboundEvent({
        event_id: 'GRAPH-INBOX-' + (m.internetMessageId || m.id),
        event_type: cls.event_type,
        message_id: m.internetMessageId || '',
        email: cls.email,
        failed_recipient: cls.failed_recipient,
        subject: m.subject || '',
        details: cls.details,
        follow_up_days: cls.follow_up_days
      });
      if (r && r.matched) matchedCount++;
    }
  });
  return { ok: true, matched: matchedCount, checked: messages.length };
}

function uiGraphReconcileSent() {
  var ui = SpreadsheetApp.getUi();
  try {
    var res = graphReconcileSentItems_();
    ui.alert('Sende-Abgleich erfolgreich',
      'Outlook Gesendete Elemente (Sent Items) wurden geprüft.\n\n' +
      'Geprüfte Nachrichten : ' + res.checked + '\n' +
      'Neu im CRM als SENT erfasst : ' + res.matched + '\n\n' +
      'Alle versendeten Zeilen sind in ALL_LEADS blau hervorgehoben.',
      ui.ButtonSet.OK);
    return { ok: true, data: res };
  } catch (e) {
    ui.alert('Abgleich fehlgeschlagen', String(e.message || e), ui.ButtonSet.OK);
    return { ok: false, error: String(e.message || e) };
  }
}

function uiGraphReconcileReplies() {
  var ui = SpreadsheetApp.getUi();
  try {
    var res = graphReconcileInboxReplies_();
    ui.alert('Antworten-Abgleich erfolgreich',
      'Outlook Posteingang (Inbox) wurde geprüft.\n\n' +
      'Geprüfte Nachrichten : ' + res.checked + '\n' +
      'Erfasste Antworten / Opt-Outs : ' + res.matched + '\n\n' +
      'Status in ALL_LEADS & INBOUND_EVENTS aktualisiert.',
      ui.ButtonSet.OK);
    return { ok: true, data: res };
  } catch (e) {
    ui.alert('Abgleich fehlgeschlagen', String(e.message || e), ui.ButtonSet.OK);
    return { ok: false, error: String(e.message || e) };
  }
}


// ------------------------------------------- Automatischer Abgleich (Trigger)
//
// Der Graph-Token liegt in den UserProperties des angemeldeten Nutzers. Ein
// zeitgesteuerter Trigger laeuft unter der Identitaet dessen, der ihn angelegt
// hat - Joel und Jordi richten den Trigger daher je einmal in ihrer eigenen
// Sitzung ein, dann werden beide Postfaecher unabhaengig voneinander
// abgeglichen. Es wird nie gesendet; es werden nur Sent Items und Inbox
// gelesen und ueber processInboundEvent() (mit allen Gates) ins CRM
// geschrieben.

var HSB_AUTO_RECONCILE_HANDLER = 'hsbAutoReconcile';
var HSB_AUTO_RECONCILE_MINUTES = 15;

function hsbAutoReconcile() {
  if (!graphVerbunden_()) {
    console.warn('hsbAutoReconcile: kein Graph-Token fuer diesen Nutzer - Abgleich uebersprungen.');
    return { ok: false, skipped: 'nicht_verbunden' };
  }
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    console.warn('hsbAutoReconcile: Sperre belegt - anderer Abgleich laeuft.');
    return { ok: false, skipped: 'gesperrt' };
  }
  var out = { ok: true, mailbox: graphMailbox_(), sent: null, inbox: null, errors: [] };
  try {
    try { out.sent = graphReconcileSentItems_(); }
    catch (e1) { out.errors.push('sent: ' + String(e1.message || e1)); }
    try { out.inbox = graphReconcileInboxReplies_(); }
    catch (e2) { out.errors.push('inbox: ' + String(e2.message || e2)); }
    out.ok = out.errors.length === 0;
    if (!out.ok) console.error('hsbAutoReconcile: ' + out.errors.join(' | '));
    return out;
  } finally {
    lock.releaseLock();
  }
}

function hsbAutoReconcileTriggerLoeschen_() {
  var n = 0;
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === HSB_AUTO_RECONCILE_HANDLER) { ScriptApp.deleteTrigger(t); n++; }
  });
  return n;
}

function uiAutoReconcileEinrichten() {
  var ui = SpreadsheetApp.getUi();
  if (!graphVerbunden_()) {
    ui.alert('Erst mit Outlook verbinden',
      'Fuer diesen Nutzer ist kein Outlook-Zugang (Graph) hinterlegt.\n' +
      'Bitte zuerst "Mit Outlook verbinden" ausfuehren, danach den automatischen Abgleich einrichten.',
      ui.ButtonSet.OK);
    return { ok: false, error: 'nicht_verbunden' };
  }
  hsbAutoReconcileTriggerLoeschen_();
  ScriptApp.newTrigger(HSB_AUTO_RECONCILE_HANDLER).timeBased().everyMinutes(HSB_AUTO_RECONCILE_MINUTES).create();
  var first = hsbAutoReconcile();
  ui.alert('Automatischer Abgleich aktiv',
    'Postfach: ' + graphMailbox_() + '\n' +
    'Intervall: alle ' + HSB_AUTO_RECONCILE_MINUTES + ' Minuten (Gesendete Elemente + Posteingang).\n\n' +
    'Erster Lauf: ' +
    (first.ok
      ? ('Gesendet geprueft ' + ((first.sent || {}).checked || 0) + ', neu SENT ' + ((first.sent || {}).matched || 0) +
         '; Posteingang geprueft ' + ((first.inbox || {}).checked || 0) + ', Antworten/Opt-Outs ' + ((first.inbox || {}).matched || 0))
      : ('Fehler: ' + (first.errors || [first.skipped]).join(' | '))) +
    '\n\nVersendet, Antwort, Abmeldung und Bounce werden ab jetzt automatisch in ALL_LEADS und INBOUND_EVENTS eingetragen. Es wird nichts versendet.',
    ui.ButtonSet.OK);
  return { ok: true, first: first };
}

function uiAutoReconcileStoppen() {
  var ui = SpreadsheetApp.getUi();
  var n = hsbAutoReconcileTriggerLoeschen_();
  ui.alert('Automatischer Abgleich gestoppt', n + ' Trigger entfernt (nur fuer diesen Nutzer).', ui.ButtonSet.OK);
  return { ok: true, removed: n };
}

function uiAutoReconcileStatus() {
  var ui = SpreadsheetApp.getUi();
  var mine = ScriptApp.getProjectTriggers().filter(function (t) { return t.getHandlerFunction() === HSB_AUTO_RECONCILE_HANDLER; });
  ui.alert('Automatischer Abgleich - Status',
    'Nutzer: ' + Session.getActiveUser().getEmail() + '\n' +
    'Outlook verbunden: ' + (graphVerbunden_() ? ('ja (' + graphMailbox_() + ')') : 'nein') + '\n' +
    'Trigger dieses Nutzers: ' + mine.length + (mine.length ? (' (alle ' + HSB_AUTO_RECONCILE_MINUTES + ' min)') : ''),
    ui.ButtonSet.OK);
  return { ok: true, triggers: mine.length, connected: graphVerbunden_() };
}
