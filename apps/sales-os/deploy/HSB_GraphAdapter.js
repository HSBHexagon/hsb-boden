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
    ergebnis.mailbox + '\n\nverbunden. Jetzt "Automatischen Abgleich einrichten (alle 15 min)" ausfuehren.',
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
  return reconcileSentMessages_(messages, 'GRAPH');
}

// ---------------------------------------------------------------- Vorfilter fuer den wiederkehrenden Abgleich
//
// processInboundEvent() behandelt NEEDS_REVIEW bewusst als offenen Klaerfall
// (nicht terminal) und haengt bei erneuter Lieferung eine neue Zeile an. Der
// 15-Minuten-Trigger liefert aber jedes Mal dieselben 100 Nachrichten je Ordner.
// Ohne Vorfilter entstuende pro Lauf fuer jede fremde Nachricht (Newsletter,
// interne Post) eine weitere NEEDS_REVIEW-Zeile. Deshalb hier, VOR der Uebergabe:
//   1. Nachrichten ohne jeden Lead-Bezug werden gar nicht protokolliert -
//      ausser Bounce, Abmeldung, Abwesenheit und Kontaktwechsel (sicherheits-
//      relevant, gehen bei Nichtzuordnung als NEEDS_REVIEW in die Warteschlange).
//   2. Bereits protokollierte Ereignisse werden uebersprungen; ein Klaerfall
//      (NEEDS_REVIEW) wird nur dann erneut eingereicht, wenn er inzwischen
//      exakt zuordenbar ist (E-Mail eindeutig, Internet_Message_ID bekannt).


var SICHERHEITSRELEVANT_ = ['HARD_BOUNCE', 'SOFT_BOUNCE', 'OPT_OUT', 'AUTO_REPLY_OOO', 'CONTACT_CHURN', 'NEGATIVE_REPLY'];

/** { Event_ID: Status } aller vorhandenen INBOUND_EVENTS-Zeilen - eine Leseoperation je Lauf. */
function eventIndexLesen_() {
  var idx = {};
  if (typeof sheet_ !== 'function' || typeof CFG === 'undefined') return idx;
  var sh = sheet_(CFG.SHEET_EVENTS);
  var last = sh.getLastRow();
  if (last < 2) return idx;
  sh.getRange(2, 1, last - 1, 10).getValues().forEach(function (r) {
    var id = String(r[0] || '');
    var st = String(r[9] || '');
    // Eine DUPLICATE-Zeile (Migration/Dedupe) darf einen noch offenen
    // Klaerfall (NEEDS_REVIEW) derselben Event_ID nicht ueberschreiben -
    // sonst wird abgleichEntscheidung_ nie mehr auf 'erneut' entscheiden.
    if (id && !(st === 'DUPLICATE' && idx[id] === 'NEEDS_REVIEW')) idx[id] = st;
  });
  return idx;
}

/** Lead-Verzeichnis: E-Mail -> Leads, Domain -> Anzahl, Internet_Message_ID -> Lead. */
function leadIndexLesen_() {
  var leads = (typeof readLeadsCached_ === 'function') ? ((readLeadsCached_() || {}).leads || []) : [];
  var byEmail = {}, byDomain = {}, byMsgId = {};
  leads.forEach(function (l) {
    var e = String(l.Email || '').trim().toLowerCase();
    if (e) {
      (byEmail[e] = byEmail[e] || []).push(l);
      var d = e.split('@')[1] || '';
      if (d) byDomain[d] = (byDomain[d] || 0) + 1;
    }
    if (l.Internet_Message_ID) byMsgId[String(l.Internet_Message_ID)] = l;
  });
  return { byEmail: byEmail, byDomain: byDomain, byMsgId: byMsgId };
}

/** Hat die Adresse irgendeinen Lead-Bezug (exakt oder Firmendomain)? Freemail-Domains zaehlen nicht. */
function adresseMitLeadBezug_(addr, li) {
  addr = String(addr || '').trim().toLowerCase();
  if (!addr) return false;
  if (li.byEmail[addr]) return true;
  var d = addr.split('@')[1] || '';
  if (!d || (typeof istFreemailDomain_ === 'function' && istFreemailDomain_(d))) return false;
  return !!li.byDomain[d];
}

/** Ist die Adresse exakt einem Lead zuordenbar (genau ein Treffer)? */
function adresseExaktZuordenbar_(addr, li) {
  addr = String(addr || '').trim().toLowerCase();
  return !!(addr && li.byEmail[addr] && li.byEmail[addr].length === 1);
}

/** Entscheidet, ob ein Ereignis (erneut) an processInboundEvent geht: 'neu' | 'erneut' | 'uebersprungen'. */
function abgleichEntscheidung_(eventId, evIdx, exaktZuordenbar) {
  var vorhanden = evIdx[eventId];
  if (vorhanden === undefined) return 'neu';
  if ((vorhanden === 'NEEDS_REVIEW' || vorhanden === 'DUPLICATE') && exaktZuordenbar) return 'erneut';
  return 'uebersprungen';
}

/** Verarbeitet Nachrichten im Graph-Format aus "Gesendete Elemente" (Quelle: Graph oder APIHub). */
function reconcileSentMessages_(messages, quelle) {
  var out = { ok: true, matched: 0, checked: messages.length, submitted: 0, skipped: 0, foreign: 0 };
  var evIdx = eventIndexLesen_();
  var li = leadIndexLesen_();
  messages.forEach(function (m) {
    var toAddr = (m.toRecipients && m.toRecipients[0] && m.toRecipients[0].emailAddress) ? String(m.toRecipients[0].emailAddress.address || '').trim().toLowerCase() : '';
    var eventId = quelle + '-SENT-' + (m.internetMessageId || m.id);
    var explicitLeadId = '';
    var hits = (toAddr && li.byEmail[toAddr]) || [];
    if (hits.length === 1) {
      explicitLeadId = hits[0].Lead_ID;
    } else if (hits.length > 1) {
      var draftedHits = hits.filter(function (l) { return l.Send_Status === 'drafted'; });
      if (draftedHits.length === 1) explicitLeadId = draftedHits[0].Lead_ID;
    }
    var msgIdBekannt = !!(m.internetMessageId && li.byMsgId[m.internetMessageId]);
    if (!adresseMitLeadBezug_(toAddr, li) && !msgIdBekannt) { out.foreign++; return; }
    var entscheidung = abgleichEntscheidung_(eventId, evIdx, !!explicitLeadId || msgIdBekannt);
    if (entscheidung === 'uebersprungen') { out.skipped++; return; }
    if (typeof processInboundEvent !== 'function') return;
    out.submitted++;
    var r = processInboundEvent({
      event_id: eventId,
      event_type: 'SENT',
      mailbox: typeof mailboxKonto_ === 'function' ? mailboxKonto_() : '',
      lead_id: explicitLeadId,
      message_id: m.internetMessageId || '',
      email: toAddr,
      subject: m.subject || '',
      details: 'Outlook SentItems Abgleich'
    });
    if (r && r.matched) out.matched++;
  });
  return out;
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
  return reconcileInboxMessages_(messages, 'GRAPH');
}

/** Verarbeitet Nachrichten im Graph-Format aus dem Posteingang (Quelle: Graph oder APIHub). */
function reconcileInboxMessages_(messages, quelle) {
  var out = { ok: true, matched: 0, checked: messages.length, submitted: 0, skipped: 0, foreign: 0 };
  var evIdx = eventIndexLesen_();
  var li = leadIndexLesen_();
  messages.forEach(function (m) {
    var cls = classifyInboundMessage_(m);
    var eventId = quelle + '-INBOX-' + (m.internetMessageId || m.id);
    var sicherheitsrelevant = SICHERHEITSRELEVANT_.indexOf(cls.event_type) >= 0;
    var msgIdBekannt = !!(m.internetMessageId && li.byMsgId[m.internetMessageId]);
    var leadBezug = adresseMitLeadBezug_(cls.email, li) || adresseMitLeadBezug_(cls.failed_recipient, li) || msgIdBekannt;
    if (!leadBezug && !sicherheitsrelevant) { out.foreign++; return; }
    // Eine Abmeldung ist auch ueber die Firmendomain zuordenbar (processInboundEvent
    // sperrt dann alle Leads der Domain) - ein offener Opt-out-Klaerfall wird
    // deshalb erneut eingereicht, sobald die Domain einen Lead trifft.
    var exakt = adresseExaktZuordenbar_(cls.email, li) || adresseExaktZuordenbar_(cls.failed_recipient, li) || msgIdBekannt ||
                (cls.event_type === 'OPT_OUT' && adresseMitLeadBezug_(cls.email, li));
    var entscheidung = abgleichEntscheidung_(eventId, evIdx, exakt);
    if (entscheidung === 'uebersprungen') { out.skipped++; return; }
    if (typeof processInboundEvent !== 'function') return;
    out.submitted++;
    var r = processInboundEvent({
      event_id: eventId,
      event_type: cls.event_type,
      mailbox: typeof mailboxKonto_ === 'function' ? mailboxKonto_() : '',
      message_id: m.internetMessageId || '',
      email: cls.email,
      failed_recipient: cls.failed_recipient,
      subject: m.subject || '',
      details: cls.details,
      follow_up_days: cls.follow_up_days
    });
    if (r && r.matched) out.matched++;
  });
  return out;
}

function uiGraphReconcileSent() {
  var ui = SpreadsheetApp.getUi();
  try {
    var res = (mailboxLeseweg_() === 'APIHUB') ? fcReconcileSentItems_() : graphReconcileSentItems_();
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
    var res = (mailboxLeseweg_() === 'APIHUB') ? fcReconcileInboxReplies_() : graphReconcileInboxReplies_();
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

// ---------------------------------------- Postfach-Abruf ueber Office-365-Connector (APIHub)
//
// Gleicher Weg wie der Entwurfs-Adapter und engine/reconcile_cloud_mailbox.py:
// Token aus HSB_FlowConnect (Azure-CLI-Client, apihub-Scope, je Nutzer per
// Geraetecode), Connector-Verbindung des jeweiligen Postfachs. Braucht keine
// Admin-Zustimmung fuer eine eigene Graph-App.

var FC_OFFICE365_RUNTIME = 'https://default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30.06.common.germany.azure-apihub.net/apim/office365';
var FC_OFFICE365_CONNECTIONS = {
  'j-cherino@hsb-boden.de': 'shared-office365-819bd473',
  'j-post@hsb-boden.de': '3d152ea7ddb24e9286fe006cb9f5069b'
};

var FC_MAILBOX_CONN_PROP = 'HSB_MAILBOX_CONNECTION';
var FC_MAILBOX_KONTO_PROP = 'HSB_MAILBOX_KONTO';

function fcMailboxVerbunden_() {
  if (!(typeof fcVerbunden_ === 'function') || !fcVerbunden_()) return false;
  try { return !!fcMailboxConnection_(); } catch (e) { return false; }
}

/**
 * Ermittelt die Office-365-Connector-Verbindung dieses Nutzers.
 * 1. gemerkte Verbindung (UserProperties), 2. Konto aus FlowConnect bzw. aus
 * dem Token, 3. Verbindungen durchprobieren (die fremde antwortet 403, die
 * eigene 200) und das Ergebnis merken.
 */
function fcMailboxConnection_() {
  var up = PropertiesService.getUserProperties();
  var gemerkt = up.getProperty(FC_MAILBOX_CONN_PROP);
  if (gemerkt) return gemerkt;

  var konto = String((typeof fcKonto_ === 'function') ? fcKonto_() : '').trim().toLowerCase();
  var token = fcToken_();
  if (!konto && typeof fcKontoAusToken_ === 'function') {
    try { konto = String(fcKontoAusToken_(token) || '').trim().toLowerCase(); } catch (e) {}
  }
  var conn = FC_OFFICE365_CONNECTIONS[konto] || '';
  var kandidaten = conn ? [[konto, conn]] : Object.keys(FC_OFFICE365_CONNECTIONS).map(function (k) { return [k, FC_OFFICE365_CONNECTIONS[k]]; });
  for (var i = 0; i < kandidaten.length; i++) {
    var url = FC_OFFICE365_RUNTIME + '/' + kandidaten[i][1] + '/v3/Mail?folderPath=Inbox&fetchOnlyUnread=false&top=1';
    var res = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + token }, muteHttpExceptions: true });
    if (res.getResponseCode() === 200) {
      up.setProperty(FC_MAILBOX_CONN_PROP, kandidaten[i][1]);
      up.setProperty(FC_MAILBOX_KONTO_PROP, kandidaten[i][0]);
      return kandidaten[i][1];
    }
  }
  return '';
}

function fcMailboxKonto_() {
  return PropertiesService.getUserProperties().getProperty(FC_MAILBOX_KONTO_PROP) ||
         ((typeof fcKonto_ === 'function') ? fcKonto_() : '') || '(Konto unbekannt)';
}

function fcMailLesen_(ordnerKandidaten, top) {
  var token = fcToken_();
  var conn = fcMailboxConnection_();
  if (!conn) throw new Error('Kein Office-365-Connector fuer Konto ' + fcKonto_());
  var letzter = '';
  for (var i = 0; i < ordnerKandidaten.length; i++) {
    var url = FC_OFFICE365_RUNTIME + '/' + conn + '/v3/Mail?folderPath=' + encodeURIComponent(ordnerKandidaten[i]) +
              '&fetchOnlyUnread=false&top=' + (top || 100);
    var res = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + token }, muteHttpExceptions: true });
    if (res.getResponseCode() === 200) {
      return (JSON.parse(res.getContentText()) || {}).value || [];
    }
    letzter = 'HTTP ' + res.getResponseCode() + ' ' + res.getContentText().slice(0, 300);
  }
  throw new Error('Postfach-Abruf fehlgeschlagen (' + ordnerKandidaten.join('/') + '): ' + letzter);
}

/** Bringt eine APIHub-Nachricht (from/toRecipients als Strings) in das Graph-Format der Verarbeitungsschleifen. */
function fcNachrichtNormalisieren_(m) {
  var to = String(m.toRecipients || m.To || '').split(/[;,]/).map(function (a) { return a.trim(); }).filter(String);
  var preview = m.bodyPreview || String(m.body || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 2000);
  return {
    id: m.id,
    subject: m.subject || m.Subject || '',
    internetMessageId: m.internetMessageId || '',
    bodyPreview: preview,
    from: { emailAddress: { address: String(m.from || m.From || '').trim() } },
    toRecipients: to.map(function (a) { return { emailAddress: { address: a } }; })
  };
}

function fcReconcileSentItems_() {
  var msgs = fcMailLesen_(['Gesendete Elemente', 'SentItems'], 100).map(fcNachrichtNormalisieren_);
  return reconcileSentMessages_(msgs, 'APIHUB');
}

function fcReconcileInboxReplies_() {
  var msgs = fcMailLesen_(['Posteingang', 'Inbox'], 100).map(fcNachrichtNormalisieren_);
  return reconcileInboxMessages_(msgs, 'APIHUB');
}

/** Welcher Lesezugang ist fuer diesen Nutzer vorhanden? 'APIHUB' (Adapter-Anmeldung) bevorzugt, sonst 'GRAPH'. */
function mailboxLeseweg_() {
  if (fcMailboxVerbunden_()) return 'APIHUB';
  if (graphVerbunden_()) return 'GRAPH';
  return '';
}

function mailboxKonto_() {
  return mailboxLeseweg_() === 'APIHUB' ? fcMailboxKonto_() : graphMailbox_();
}

var SYNC_STATUS_SHEET_ = 'SYNC_STATUS';
var SYNC_STATUS_HEADER_ = ['Mailbox', 'Letzter_Lauf_UTC', 'Weg', 'Gesendet_geprueft', 'Neu_versendet',
  'Posteingang_geprueft', 'Antworten_Abmeldungen_Bounces', 'Fehler'];

/** Eine Zeile je Postfach: wann lief der Abgleich zuletzt, was hat er gefunden. Sichtbar fuer beide Nutzer. */
function syncStatusSchreiben_(mailbox, r) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SYNC_STATUS_SHEET_) || ss.insertSheet(SYNC_STATUS_SHEET_);
  if (sh.getLastRow() === 0) { sh.appendRow(SYNC_STATUS_HEADER_); sh.getRange(1, 1, 1, 8).setFontWeight('bold'); sh.setFrozenRows(1); }
  var row = [mailbox, new Date().toISOString(), r.weg || '', ((r.sent || {}).checked || 0), ((r.sent || {}).matched || 0),
             ((r.inbox || {}).checked || 0), ((r.inbox || {}).matched || 0), (r.errors || []).join(' | ')];
  var n = sh.getLastRow();
  if (n >= 2) {
    var vals = sh.getRange(2, 1, n - 1, 1).getValues();
    for (var i = 0; i < vals.length; i++) {
      if (String(vals[i][0]) === mailbox) { sh.getRange(i + 2, 1, 1, 8).setValues([row]); return; }
    }
  }
  sh.appendRow(row);
}

var HSB_AUTO_RECONCILE_HANDLER = 'hsbAutoReconcile';
var HSB_AUTO_RECONCILE_MINUTES = 15;

function hsbAutoReconcile() {
  var weg = mailboxLeseweg_();
  if (!weg) {
    console.warn('hsbAutoReconcile: kein Postfach-Lesezugang fuer diesen Nutzer - Abgleich uebersprungen.');
    return { ok: false, skipped: 'nicht_verbunden' };
  }
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    console.warn('hsbAutoReconcile: Sperre belegt - anderer Abgleich laeuft.');
    return { ok: false, skipped: 'gesperrt' };
  }
  var out = { ok: true, weg: weg, mailbox: mailboxKonto_(), sent: null, inbox: null, errors: [] };
  try {
    try { out.sent = (weg === 'APIHUB') ? fcReconcileSentItems_() : graphReconcileSentItems_(); }
    catch (e1) { out.errors.push('sent: ' + String(e1.message || e1)); }
    try { out.inbox = (weg === 'APIHUB') ? fcReconcileInboxReplies_() : graphReconcileInboxReplies_(); }
    catch (e2) { out.errors.push('inbox: ' + String(e2.message || e2)); }
    out.ok = out.errors.length === 0;
    if (!out.ok) console.error('hsbAutoReconcile: ' + out.errors.join(' | '));
    try { syncStatusSchreiben_(out.mailbox, out); } catch (e3) { console.warn('SYNC_STATUS: ' + e3); }
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
  if (!mailboxLeseweg_()) {
    ui.alert('Erst mit Outlook verbinden',
      'Fuer diesen Nutzer ist kein Postfach-Zugang hinterlegt.\n' +
      'Bitte zuerst Menue "HSB Sales OS" -> "Outlook fuer Entwuerfe verbinden (Adapter)" ausfuehren ' +
      '(Geraetecode, Anmeldung mit dem eigenen @hsb-boden.de-Konto), danach den automatischen Abgleich einrichten.',
      ui.ButtonSet.OK);
    return { ok: false, error: 'nicht_verbunden' };
  }
  hsbAutoReconcileTriggerLoeschen_();
  ScriptApp.newTrigger(HSB_AUTO_RECONCILE_HANDLER).timeBased().everyMinutes(HSB_AUTO_RECONCILE_MINUTES).create();
  var first = hsbAutoReconcile();
  ui.alert('Automatischer Abgleich aktiv',
    'Postfach: ' + mailboxKonto_() + ' (Weg: ' + mailboxLeseweg_() + ')\n' +
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
    'Postfach-Zugang: ' + (mailboxLeseweg_() ? (mailboxLeseweg_() + ' (' + mailboxKonto_() + ')') : 'nein') + '\n' +
    'Trigger dieses Nutzers: ' + mine.length + (mine.length ? (' (alle ' + HSB_AUTO_RECONCILE_MINUTES + ' min)') : ''),
    ui.ButtonSet.OK);
  return { ok: true, triggers: mine.length, connected: !!mailboxLeseweg_() };
}

/** Manueller Sofort-Abgleich beider Ordner ueber den vorhandenen Lesezugang. */
function uiJetztAbgleichen() {
  var ui = SpreadsheetApp.getUi();
  if (!mailboxLeseweg_()) {
    ui.alert('Erst mit Outlook verbinden',
      'Fuer diesen Nutzer ist kein Postfach-Zugang hinterlegt. Bitte zuerst "Mit Outlook verbinden" ausfuehren.',
      ui.ButtonSet.OK);
    return { ok: false, error: 'nicht_verbunden' };
  }
  var r = hsbAutoReconcile();
  ui.alert(r.ok ? 'Abgleich erledigt' : 'Abgleich mit Fehlern',
    'Postfach: ' + (r.mailbox || '?') + ' (Weg: ' + (r.weg || '?') + ')\n' +
    'Gesendet geprueft: ' + ((r.sent || {}).checked || 0) + ', neu als versendet: ' + ((r.sent || {}).matched || 0) + '\n' +
    'Posteingang geprueft: ' + ((r.inbox || {}).checked || 0) + ', Antworten/Abmeldungen/Bounces: ' + ((r.inbox || {}).matched || 0) +
    (r.errors && r.errors.length ? ('\n\nFehler: ' + r.errors.join(' | ')) : ''),
    ui.ButtonSet.OK);
  return r;
}
