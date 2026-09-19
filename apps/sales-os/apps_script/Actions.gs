/**
 * HSB Sales OS - Aktionen: Qualifizierung, Entwuerfe, EML-Fallback,
 * Wiedervorlage, Statusrueckschreibung, Inbound-Events.
 */

/* ------------------------------------------------------- Qualifizierung */

/**
 * Setzt Legal_Basis und Versandfreigabe fuer eine gefilterte Auswahl.
 *
 * Das ist bewusst eine explizite Nutzerentscheidung: ohne rechtliche
 * Grundlage darf nicht gesendet werden. Die Software erleichtert die
 * Erfassung, trifft die Entscheidung aber nicht selbst.
 */
function qualifyLeads(opts) {
  opts = opts || {};
  const ownerKey = normalizeOwner_(opts.owner);
  const legalBasis = String(opts.legalBasis || '').toUpperCase();
  const limit = Math.max(0, parseInt(opts.count, 10) || 0);

  if (LEGAL_BASIS_ALL.indexOf(legalBasis) === -1) {
    throw new Error('Ungueltige Legal_Basis: ' + legalBasis);
  }
  const sendable = LEGAL_BASIS_SENDABLE.indexOf(legalBasis) >= 0;

  const lock = (typeof LockService !== 'undefined' && LockService.getDocumentLock)
    ? LockService.getDocumentLock()
    : null;
  const hasLock = lock ? lock.tryLock(30000) : true;
  if (!hasLock) {
    throw new Error('LOCK_TIMEOUT: Ein anderer Vorgang greift gerade auf das Sheet zu. Bitte in Kürze erneut versuchen.');
  }

  try {
    invalidateLeadsCache_();
    const read = readLeadsCached_();
    const sh = sheet_(CFG.SHEET_LEADS);
    const cLegal = read.index['Legal_Basis'] + 1;
    const cFreigabe = read.index[FIELD_MAP.Versandfreigabe] + 1;
    if (!cLegal || !cFreigabe) {
      throw new Error('Spalten fehlen. Bitte zuerst "Spalten pruefen" ausfuehren.');
    }

    const uLegal = {}, uFreigabe = {};
    let touched = 0;
    for (let i = 0; i < read.leads.length && touched < limit; i++) {
      const l = read.leads[i];
      if (normalizeOwner_(l.Owner) !== ownerKey) continue;
      if (opts.industry && String(l.Industry || '').trim() !== opts.industry) continue;
      if (opts.tier && String(l.Tier || '').trim().toUpperCase()
          !== String(opts.tier).trim().toUpperCase()) continue;
      // Bereits Qualifizierte nicht erneut anfassen.
      if (String(l.Legal_Basis || '').toUpperCase() === legalBasis) continue;
      // Opt-out und Suppression sind unantastbar.
      if (isTrue_(l.Suppressed)) continue;
      const optOut = String(l.Opt_Out || '').trim().toLowerCase();
      if (optOut === 'yes' || optOut === 'ja' || optOut === 'opt_out') continue;

      uLegal[l._row] = legalBasis;
      uFreigabe[l._row] = sendable ? 'yes' : 'no';
      touched++;
    }
    // Zwei Bulk-Vorgaenge statt 2xN Einzelaufrufen.
    writeColumnBulk_(sh, cLegal, uLegal);
    writeColumnBulk_(sh, cFreigabe, uFreigabe);
    SpreadsheetApp.flush();
    invalidateLeadsCache_();
    logActivity_('', 'QUALIFY',
      touched + ' Leads auf ' + legalBasis + ' gesetzt (' + ownerKey + ')');
    return { updated: touched, legalBasis: legalBasis, sendable: sendable };
  } finally {
    if (lock && hasLock) {
      try { lock.releaseLock(); } catch (_) {}
    }
  }
}

/* ----------------------------------------------------- E-Mail-Erzeugung */

var NAMENSZUSAETZE = ['van', 'von', 'de', 'der', 'den', 'du', 'di', 'da',
                      'del', 'dos', 'el', 'zu', 'zum', 'ter'];

/**
 * Geschaeftsuebliche Anrede: "Frau Franziska Koch" -> "Frau Koch".
 *
 * Der volle Vorname wirkt maschinell. Gekuerzt wird aber nur dort, wo die
 * Zerlegung eindeutig ist: bei genau zwei Namensteilen, oder wenn direkt nach
 * dem Vornamen ein Namenszusatz wie "van" oder "von" folgt. Sonst bleibt der
 * Name vollstaendig - ein etwas laengerer Gruss ist harmlos, eine falsch
 * abgeschnittene Anrede an einen Kunden nicht.
 */
function anrede_(contact) {
  const roh = String(contact || '').trim().replace(/\s+/g, ' ');
  if (!roh) return '';
  const m = roh.match(/^(Herr|Frau)\s+(.+)$/i);
  if (!m) return roh;
  const form = m[1];
  const teile = m[2].split(' ').filter(function (s) { return s; });
  // Endstuecke ohne Buchstaben (Zaehler, Kuerzel) sind keine Nachnamen.
  while (teile.length > 1 && !/[A-Za-zÀ-ÿ]/.test(teile[teile.length - 1])) {
    teile.pop();
  }
  if (teile.length === 1) return form + ' ' + teile[0];
  if (teile.length === 2) return form + ' ' + teile[1];
  // Namenszusatz direkt nach dem Vornamen: alles ab dort ist der Nachname.
  if (NAMENSZUSAETZE.indexOf(teile[1].toLowerCase()) >= 0) {
    return form + ' ' + teile.slice(1).join(' ');
  }
  // Zusatz weiter hinten - der Nachname laesst sich nicht sicher abgrenzen,
  // also bleibt der Name vollstaendig stehen.
  for (let i = 2; i < teile.length; i++) {
    if (NAMENSZUSAETZE.indexOf(teile[i].toLowerCase()) >= 0) {
      return form + ' ' + teile.join(' ');
    }
  }
  // Mehrere Vornamen ohne Zusatz: das letzte Wort ist der Nachname.
  return form + ' ' + teile[teile.length - 1];
}

function renderEmail_(lead, flyer) {
  const company = String(lead.Company || 'Ihr Unternehmen').trim();
  const contact = anrede_(lead.Contact);
  let greeting;
  if (!contact) {
    greeting = 'Sehr geehrte Damen und Herren,';
  } else if (/^Herr\b/i.test(contact)) {
    greeting = 'Sehr geehrter ' + contact + ',';
  } else if (/^Frau\b/i.test(contact)) {
    greeting = 'Sehr geehrte ' + contact + ',';
  } else {
    greeting = 'Guten Tag ' + contact + ',';
  }
  const subject = 'Industrieböden für ' + company + ' – Beratung von '
    + flyer.displayName;

  const body = greeting + '\n\n'
    + 'mein Name ist ' + flyer.displayName + ' von der HSB Hexagon Säurebau '
    + 'GmbH. Wir planen, bauen und sanieren säurebeständige, hygienische '
    + 'Industrieböden – ausgelegt auf das reale Belastungsprofil statt auf '
    + 'ein Standardprodukt.\n\n'
    + 'Typische Themen bei Produktionsbetrieben:\n'
    + '- Risse, Ablösungen und offene Fugen\n'
    + '- Keimnester in Nassbereichen\n'
    + '- stehendes Wasser durch falsches Gefälle\n'
    + '- defekte Rinnen und Abläufe\n\n'
    + 'Im angehängten Flyer sehen Sie ausgeführte Projektflächen und unser '
    + 'Vorgehen von der Analyse bis zur dokumentierten Übergabe.\n\n'
    + 'Gerne prüfen wir Ihr Belastungsprofil unverbindlich und vor Ort.\n\n'
    + 'Mit freundlichen Grüßen\n'
    + flyer.displayName + '\n'
    + 'HSB Hexagon Säurebau GmbH\n'
    + flyer.mailbox + '\n'
    + 'Tel. +49 (0)2562 9463030\n\n'
    + '---\n'
    + 'Wenn Sie keine weiteren Informationen erhalten möchten, antworten Sie '
    + 'bitte mit dem Betreff "Abmelden" auf diese E-Mail.';

  return { subject: subject, body: body };
}

/**
 * Baut eine RFC-822 EML mit genau einem korrekten PDF-Anhang.
 *
 * `pdfChunked` ist der bereits auf 76 Zeichen umgebrochene Base64-Block.
 * Er ist fuer jede EML identisch und wird deshalb genau einmal erzeugt -
 * sonst entstuende pro Lead unnoetig eine weitere 2-MB-Zeichenkette.
 */
function buildEml_(lead, batchId, flyer, pdfChunked) {
  const mail = renderEmail_(lead, flyer);
  const boundary = 'HSB-' + Utilities.getUuid();
  const lines = [];

  lines.push('From: ' + flyer.displayName + ' <' + flyer.mailbox + '>');
  lines.push('To: ' + String(lead.Email || '').trim());
  lines.push('Reply-To: ' + flyer.mailbox);
  lines.push('Subject: ' + encodeHeader_(mail.subject));
  lines.push('Date: ' + Utilities.formatDate(new Date(), CFG.TIMEZONE,
             'EEE, dd MMM yyyy HH:mm:ss Z'));
  lines.push('Message-ID: <' + Utilities.getUuid() + '@hsb-boden.de>');
  lines.push('X-Unsent: 1');                    // Outlook: als Entwurf oeffnen
  lines.push('X-HSB-Lead-ID: ' + lead.Lead_ID);
  lines.push('X-HSB-Batch-ID: ' + batchId);
  lines.push('X-HSB-Owner: ' + flyer.key);
  lines.push('X-HSB-Asset-SHA256: ' + flyer.sha256);
  lines.push('MIME-Version: 1.0');
  lines.push('Content-Type: multipart/mixed; boundary="' + boundary + '"');
  lines.push('');
  lines.push('--' + boundary);
  lines.push('Content-Type: text/plain; charset="UTF-8"');
  lines.push('Content-Transfer-Encoding: base64');
  lines.push('');
  lines.push(chunk76_(Utilities.base64Encode(mail.body, Utilities.Charset.UTF_8)));
  lines.push('--' + boundary);
  var attName = flyer.attachmentName || flyer.fileName;
  lines.push('Content-Type: application/pdf; name="' + attName + '"');
  lines.push('Content-Transfer-Encoding: base64');
  lines.push('Content-Disposition: attachment; filename="' + attName + '"');
  lines.push('');
  lines.push(pdfChunked);
  lines.push('--' + boundary + '--');
  lines.push('');
  return lines.join('\r\n');
}

function encodeHeader_(text) {
  if (/^[\x20-\x7E]*$/.test(text)) return text;
  return '=?UTF-8?B?' + Utilities.base64Encode(text, Utilities.Charset.UTF_8) + '?=';
}

function chunk76_(b64) {
  return (b64.match(/.{1,76}/g) || []).join('\r\n');
}

/**
 * EML-Fallback: erzeugt die Entwuerfe eines Batches als ZIP-Pakete in Drive.
 * Funktioniert ohne Outlook-Verbindung, ohne Admin, ohne DNS.
 */
// Zehn statt zwanzig: eine EML traegt den kompletten Flyer als Base64 und ist
// damit rund 2 MB gross. Zehn Stueck sind etwa 20 MB Zeichenketten plus das
// ZIP - das haelt Apps Script aus. Bei zwanzig lag der Spitzenbedarf bereits
// bei rund 70 MB.
var EML_CHUNK_SIZE = 10;

/**
 * Erzeugt GENAU EIN Teilpaket eines Batches und kehrt zurueck.
 *
 * Frueher lief diese Funktion in einer Schleife, bis der Batch fertig war
 * oder vier Minuten um waren. Fuer 100 Kontakte hiess das fuenf Pakete in
 * einem einzigen Lauf, also fuenfmal rund 40 MB Zeichenketten nacheinander -
 * die haeufigste Ursache fuer einen Abbruch ohne verwertbare Meldung.
 *
 * Jetzt macht ein Aufruf ein Paket. Die Oberflaeche ruft so lange nach, bis
 * `complete` wahr ist; der Nutzer sieht dabei den Fortschritt. Jeder Aufruf
 * ist fuer sich kurz genug, und ein Abbruch kostet hoechstens ein Paket.
 */
function exportBatchAsEmlZip(batchId, startIndex) {
  const read = readLeadsCached_();
  const leads = read.leads.filter(function (l) {
    return String(l.Batch_ID) === String(batchId);
  });
  if (!leads.length) throw new Error('Keine Leads fuer Batch ' + batchId);

  const von = Math.max(0, parseInt(startIndex, 10) || 0);

  if (von >= leads.length) {
    const folderFertig = getOrCreateFolder_('HSB Sales OS Batches');
    return {
      batch_id: batchId, total: leads.length, written: 0, complete: true,
      next_index: null, parts: [], folder_url: folderFertig.getUrl(),
      asset_sha256: getVerifiedFlyer_(normalizeOwner_(leads[0].Owner)).sha256
    };
  }

  const ownerKey = normalizeOwner_(leads[0].Owner);
  const verified = getVerifiedFlyer_(ownerKey);
  const teil = Math.floor(von / EML_CHUNK_SIZE) + 1;
  const gesamtTeile = Math.ceil(leads.length / EML_CHUNK_SIZE);
  const name = batchId + '_teil' + ('0' + teil).slice(-2) + '.zip';
  const slice = leads.slice(von, von + EML_CHUNK_SIZE);

  // Denselben Document-Lock nehmen wie jede andere zustandsaendernde
  // Funktion in dieser Datei (qualifyLeads, prepareBatch,
  // processInboundEvent): ohne ihn waeren "Datei vorhanden?" und "Datei
  // anlegen" zwei getrennte Schritte - zwei echte Parallelaufrufe fuer
  // denselben Batch (z. B. zwei geoeffnete Sidebar-Tabs) koennten beide
  // "nicht vorhanden" sehen und zwei gleichnamige ZIPs anlegen. Der
  // clientseitige exportLaufend-Schutz in Sidebar.html verhindert nur
  // Doppelklicks im selben Tab, keine Parallelitaet ueber Tabs/Sitzungen
  // hinweg.
  const lock = (typeof LockService !== 'undefined' && LockService.getDocumentLock)
    ? LockService.getDocumentLock()
    : null;
  const hasLock = lock ? lock.tryLock(30000) : true;
  if (!hasLock) {
    // Anders als bei den drei Sheet-Schreibvorgaengen oben schuetzt dieser
    // Lock die Drive-Ordnerpruefung/-Anlage, nicht Zellen im Sheet - die
    // Meldung nennt deshalb bewusst das Batch-Paket statt "Sheet".
    throw new Error('LOCK_TIMEOUT: Ein anderer Vorgang legt gerade ein Paket fuer diesen Batch an. Bitte in Kürze erneut versuchen.');
  }

  let file, folder;
  try {
    folder = getOrCreateFolder_('HSB Sales OS Batches');
    // Ein Wiederholungsversuch darf kein zweites, gleichnamiges ZIP anlegen.
    const vorhanden = folder.getFilesByName(name);
    if (vorhanden.hasNext()) {
      file = vorhanden.next();
    } else {
      // Genau einmal erzeugen - identisch fuer jede EML dieses Pakets.
      const pdfChunked = chunk76_(Utilities.base64Encode(verified.blob.getBytes()));
      const files = slice.map(function (l) {
        const safe = String(l.Lead_ID).replace(/[^A-Za-z0-9._-]+/g, '-');
        return Utilities.newBlob(
          buildEml_(l, batchId, verified.flyer, pdfChunked),
          'message/rfc822', ownerKey.toLowerCase() + '_' + safe + '.eml');
      });
      file = folder.createFile(Utilities.zip(files, name));
    }
  } finally {
    if (lock && hasLock) {
      try { lock.releaseLock(); } catch (_) {}
    }
  }

  const weiter = von + slice.length;
  const fertig = weiter >= leads.length;
  logActivity_(batchId, 'EML_EXPORT',
    'Teil ' + teil + ' von ' + gesamtTeile + ' mit ' + slice.length
    + ' Entwuerfen' + (fertig ? ' - vollstaendig' : ''));

  return {
    batch_id: batchId,
    total: leads.length,
    written: slice.length,
    part_index: teil,
    part_total: gesamtTeile,
    complete: fertig,
    next_index: fertig ? null : weiter,
    parts: [{
      name: name, url: file.getUrl(), count: slice.length,
      size_mb: Math.round(file.getSize() / 1048576 * 10) / 10
    }],
    folder_url: folder.getUrl(),
    asset_sha256: verified.sha256
  };
}

function getOrCreateFolder_(name) {
  const it = DriveApp.getFoldersByName(name);
  return it.hasNext() ? it.next() : DriveApp.createFolder(name);
}

/**
 * Stempelt Sent_At (BATCHES-Blatt, Spalte 13) genau einmal je Batch - beim
 * ersten bestaetigten Sendenachweis eines Leads aus diesem Batch. Spaetere
 * Sendenachweise weiterer Leads desselben Batches ueberschreiben den
 * Zeitpunkt nicht mehr.
 *
 * Der Status in Spalte 4 bleibt dabei bewusst unveraendert: activeBatchLeadIds_
 * behandelt nur SENT/CANCELLED als abgeschlossen. Wuerde ein Batch schon beim
 * ersten bestaetigten Lead auf SENT gesetzt, wuerden seine noch nicht
 * bestaetigten Leads faelschlich als "nicht mehr aktiv" gelten und koennten in
 * einen neuen Batch aufgenommen werden.
 */
function stampBatchSentAt_(batchId) {
  if (!batchId) return;
  const sh = sheet_(CFG.SHEET_BATCHES);
  if (sh.getLastRow() < 2) return;
  const ids = sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues();
  for (let i = 0; i < ids.length; i++) {
    if (String(ids[i][0]) === String(batchId)) {
      const cell = sh.getRange(i + 2, 13);
      if (!cell.getValue()) cell.setValue(nowIso_());
      return;
    }
  }
}

/* --------------------------------------------------- Wiedervorlage / CRM */

/** Setzt Status und Wiedervorlage fuer einen einzelnen Lead. */
function setLeadStatus(leadId, status, followUpDays, note) {
  invalidateLeadsCache_();
  const read = readLeadsCached_();
  const sh = sheet_(CFG.SHEET_LEADS);
  const lead = read.leads.filter(function (l) {
    return String(l.Lead_ID) === String(leadId);
  })[0];
  if (!lead) throw new Error('Lead nicht gefunden: ' + leadId);

  const set = function (field, value) {
    const col = read.index[field];
    if (col !== undefined) sh.getRange(lead._row, col + 1).setValue(value);
  };

  const s = String(status).toUpperCase();
  set(FIELD_MAP.Send_Status, s === 'SENT' ? 'sent' : lead.Send_Status);
  if (s === 'SENT') set(FIELD_MAP.Sent_At, todayStr_());
  if (s === 'REPLY' || s === 'REPLIED' || s === 'POSITIVE_REPLY' || s === 'NEGATIVE_REPLY') {
    set(FIELD_MAP.Reply_Status, s.toLowerCase());
    set('Last_Reply_At', todayStr_());
  }
  if (s === 'AUTO_REPLY_OOO') {
    set(FIELD_MAP.Reply_Status, 'auto_reply_ooo');
  }
  if (s === 'CONTACT_CHURN') {
    set(FIELD_MAP.Reply_Status, 'contact_churn');
    set('Suppressed', 'yes');
    set(FIELD_MAP.Versandfreigabe, 'no');
  }
  if (s === 'OPT_OUT') {
    set(FIELD_MAP.Opt_Out, 'yes');
    set('Suppressed', 'yes');
    set(FIELD_MAP.Versandfreigabe, 'no');
  }
  if (s === 'HARD_BOUNCE') {
    set(FIELD_MAP.Bounce_Status, 'hard_bounce');
    set('Suppressed', 'yes');
    set(FIELD_MAP.Versandfreigabe, 'no');
  }
  if (s === 'SOFT_BOUNCE') set(FIELD_MAP.Bounce_Status, 'soft_bounce');
  set('Batch_Status', s);

  const days = parseInt(followUpDays, 10);
  if (days > 0) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    set(FIELD_MAP.Next_Action_At,
        Utilities.formatDate(d, CFG.TIMEZONE, 'yyyy-MM-dd'));
  }
  if (note) {
    set(FIELD_MAP.Notes,
        String(lead.Notes || '') + '\n[' + todayStr_() + '] ' + note);
  }
  SpreadsheetApp.flush();
  invalidateLeadsCache_();
  logActivity_(lead.Batch_ID || '', s, leadId + (note ? ' - ' + note : ''));
  return { lead_id: leadId, status: s };
}

/** Alle heute oder frueher faelligen Wiedervorlagen. */
function getDueFollowUps(ownerKey) {
  const read = readLeadsCached_();
  const today = todayStr_();
  const owner = ownerKey ? normalizeOwner_(ownerKey) : null;
  const due = [];
  read.leads.forEach(function (l) {
    if (owner && normalizeOwner_(l.Owner) !== owner) return;
    if (isTrue_(l.Suppressed)) return;
    const d = l.Next_Action_At;
    if (!d) return;
    const ds = (d instanceof Date)
      ? Utilities.formatDate(d, CFG.TIMEZONE, 'yyyy-MM-dd') : String(d).trim();
    if (ds && ds <= today) {
      due.push({ Lead_ID: l.Lead_ID, Company: l.Company, Email: l.Email,
                 Owner: normalizeOwner_(l.Owner), Due: ds,
                 Reply_Status: l.Reply_Status, Notes: l.Notes });
    }
  });
  due.sort(function (a, b) { return a.Due < b.Due ? -1 : 1; });
  return due;
}

/** Kennzahlen fuer das Cockpit. */
function getDashboard() {
  const read = readLeadsCached_();
  const out = { total: read.leads.length, owners: {}, due_followups: 0 };
  const today = todayStr_();

  read.leads.forEach(function (l) {
    const o = normalizeOwner_(l.Owner) || 'UNBEKANNT';
    if (!out.owners[o]) {
      out.owners[o] = { total: 0, eligible: 0, blocked: 0, sent: 0,
                        replied: 0, positive: 0, bounced: 0, optout: 0,
                        due: 0 };
    }
    const c = out.owners[o];
    c.total++;
    if (checkEligibility_(l).eligible) c.eligible++; else c.blocked++;

    const st = String(l.Send_Status || '').toLowerCase();
    if (st === 'sent' || st === 'gesendet') c.sent++;
    const rs = String(l.Reply_Status || '').toLowerCase();
    if (rs.indexOf('replied') >= 0 || rs.indexOf('reply') >= 0) c.replied++;
    if (rs.indexOf('positive') >= 0) c.positive++;
    if (String(l.Bounce_Status || '').toLowerCase().indexOf('bounce') >= 0) c.bounced++;
    const oo = String(l.Opt_Out || '').toLowerCase();
    if (oo === 'yes' || oo === 'ja') c.optout++;

    const d = l.Next_Action_At;
    if (d) {
      const ds = (d instanceof Date)
        ? Utilities.formatDate(d, CFG.TIMEZONE, 'yyyy-MM-dd') : String(d).trim();
      if (ds && ds <= today && !isTrue_(l.Suppressed)) {
        c.due++; out.due_followups++;
      }
    }
  });
  return out;
}

/**
 * Filterwerte fuer die Seitenleiste. Die Oberflaeche liest ausschliesslich
 * `industries`; weitere Felder werden bewusst nicht geliefert.
 */
function getFilters() {
  const read = readLeadsCached_();
  const seen = {};
  read.leads.forEach(function (l) {
    const v = String(l.Industry || '').trim();
    if (v) seen[v] = true;
  });
  const industries = Object.keys(seen).sort(function (a, b) {
    return a.localeCompare(b, 'de');
  });
  return { industries: industries };
}

/* ------------------------------------------------ Taegliche Erinnerung */

/**
 * Zeit-Trigger: schickt morgens eine Uebersicht der faelligen Wiedervorlagen.
 * Einrichten ueber das Menue "HSB Sales OS > Taegliche Erinnerung einrichten".
 */
function dailyDigest() {
  const dash = getDashboard();
  const due = getDueFollowUps(null);
  if (!due.length && !dash.due_followups) return;

  let html = '<h2>HSB Sales OS - Wiedervorlagen</h2>';
  html += '<p>Stand ' + todayStr_() + '</p><ul>';
  Object.keys(dash.owners).forEach(function (o) {
    const c = dash.owners[o];
    html += '<li><b>' + o + '</b>: ' + c.due + ' faellig, ' + c.sent
         + ' gesendet, ' + c.replied + ' Antworten, ' + c.bounced
         + ' Bounces, ' + c.eligible + ' sendefaehig</li>';
  });
  html += '</ul><h3>Heute faellig</h3><ol>';
  due.slice(0, 50).forEach(function (d) {
    html += '<li>' + d.Company + ' (' + d.Email + ') - faellig ' + d.Due + '</li>';
  });
  html += '</ol>';
  html += '<p><a href="' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
       + '">Sales OS oeffnen</a></p>';

  MailApp.sendEmail({
    to: Session.getActiveUser().getEmail(),
    subject: 'HSB Sales OS - ' + due.length + ' Wiedervorlagen faellig',
    htmlBody: html
  });
}

function setupDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'dailyDigest') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('dailyDigest').timeBased().atHour(7).everyDays(1).create();
  return 'Taegliche Erinnerung um 7 Uhr eingerichtet.';
}

/* ------------------------------------------------- Batch-Uebersicht */

/** Liste der Batches, neueste zuerst. */
function getBatches(ownerKey, limit) {
  const sh = sheet_(CFG.SHEET_BATCHES);
  if (sh.getLastRow() < 2) return [];
  const owner = ownerKey ? normalizeOwner_(ownerKey) : null;
  const rows = sh.getRange(2, 1, sh.getLastRow() - 1, 13).getValues();
  const out = [];
  for (let i = rows.length - 1; i >= 0; i--) {
    const r = rows[i];
    if (owner && normalizeOwner_(r[1]) !== owner) continue;
    out.push({
      batch_id: r[0], owner: r[1], campaign: r[2], status: r[3],
      requested: r[4], selected: r[5], eligible: r[6],
      created_at: r[10], approved_at: r[11], sent_at: r[12]
    });
    if (limit && out.length >= limit) break;
  }
  return out;
}

/* --------------------------------------------------------- Suche */

/** Sucht Leads nach Firma oder E-Mail. Liefert hoechstens `limit` Treffer. */
function searchLeads(query, ownerKey, limit) {
  const q = String(query || '').trim().toLowerCase();
  if (q.length < 2) return [];
  const owner = ownerKey ? normalizeOwner_(ownerKey) : null;
  const max = limit || 25;
  const read = readLeadsCached_();
  const hits = [];
  for (let i = 0; i < read.leads.length && hits.length < max; i++) {
    const l = read.leads[i];
    if (owner && normalizeOwner_(l.Owner) !== owner) continue;
    const hay = (String(l.Company || '') + ' ' + String(l.Email || '')
                 + ' ' + String(l.Lead_ID || '')).toLowerCase();
    if (hay.indexOf(q) === -1) continue;
    const el = checkEligibility_(l);
    hits.push({
      Lead_ID: l.Lead_ID, Company: l.Company, Email: l.Email,
      Owner: normalizeOwner_(l.Owner), Tier: l.Tier,
      Send_Status: l.Send_Status, Reply_Status: l.Reply_Status,
      Batch_ID: l.Batch_ID, Next_Action_At: l.Next_Action_At,
      eligible: el.eligible, reasons: el.reasons
    });
  }
  return hits;
}

/* ------------------------------------------------ Setup-Zustand */

/**
 * Sagt der Oberflaeche, ob die Einrichtung abgeschlossen ist.
 * Ohne die Zusatzspalten kann nichts vorbereitet werden.
 */
function getSetupState() {
  const sh = sheet_(CFG.SHEET_LEADS);
  const lastCol = sh.getLastColumn();
  const header = sh.getRange(1, 1, 1, lastCol).getValues()[0].map(String);
  const missing = ADDITIONAL_FIELDS.filter(function (f) {
    return header.indexOf(f) === -1;
  });
  const flyers = {};
  Object.keys(FLYERS).forEach(function (k) {
    try { getVerifiedFlyer_(k); flyers[k] = 'OK'; }
    catch (e) { flyers[k] = String(e.message || e); }
  });
  return {
    columns_ok: missing.length === 0,
    missing_columns: missing,
    flyers: flyers,
    flyers_ok: Object.keys(flyers).every(function (k) { return flyers[k] === 'OK'; })
  };
}

/* --------------------------------------------------- Inbound-Verarbeitung */

/**
 * Verarbeitet ein Inbound-Event (Antwort, Bounce, Opt-out).
 *
 * Regeln:
 * 1. Deduplizierung: Gleiche Event-ID oder Message-ID fuehrt nicht zu
 *    mehrfachen Statusaenderungen (Idempotenz).
 * 2. Deterministische Zuordnung:
 *    a) Explizite Lead_ID
 *    b) In-Reply-To oder Message-ID gegen Internet_Message_ID / Outlook_Message_ID
 *    c) E-Mail-Adresse gegen ALL_LEADS
 * 3. Kein Raten: Nicht zuordenbare Events erhalten Status 'NEEDS_REVIEW' und
 *    werden niemals auf Verdacht einem Lead zugeordnet.
 */
// Freemail-Anbieter tragen keine Firmenzuordnung: eine Adresse dort sagt
// nichts ueber das Unternehmen des Leads aus.
var FREEMAIL_DOMAINS_ = ['gmail.com', 'googlemail.com', 'outlook.com', 'outlook.de', 'hotmail.com', 'hotmail.de',
  'live.com', 'live.de', 'web.de', 'gmx.de', 'gmx.net', 'gmx.at', 'gmx.ch', 't-online.de', 'yahoo.com', 'yahoo.de',
  'icloud.com', 'me.com', 'freenet.de', 'aol.com', 'posteo.de', 'mail.de', 'protonmail.com', 'proton.me'];

function istFreemailDomain_(domain) {
  return FREEMAIL_DOMAINS_.indexOf(String(domain || '').trim().toLowerCase()) >= 0;
}

// Kanonisches Layout von INBOUND_EVENTS (docs/appsheet/inbound_events_schema_spec.json).
// Alle Schreiber (Apps Script, engine/reconcile_cloud_mailbox.py) halten diese Reihenfolge ein.
var INBOUND_EVENT_HEADER_ = ['Event_ID', 'Received_UTC', 'Mailbox', 'From', 'Subject',
  'Internet_Message_ID', 'Lead_ID', 'Classification', 'Stop_Followup', 'Processed', 'Notes', 'Raw_Link'];

function inboundEventRow_(p) {
  var stop = (p.type === 'OPT_OUT' || p.type === 'HARD_BOUNCE' || p.type === 'CONTACT_CHURN' || p.type === 'NEGATIVE_REPLY') ? 'yes' : 'no';
  return [p.eventId, p.ts, p.mailbox || '', p.from || '', p.subject || '', p.messageId || '',
          p.leadId || '', p.type, stop, p.status, p.notes || '', p.inReplyTo ? ('In-Reply-To: ' + p.inReplyTo) : ''];
}

function processInboundEvent(event) {
  if (!event || typeof event !== 'object') {
    throw new Error('Ungueltiges Event-Objekt');
  }
  const eventId = String(event.event_id || ('EVT-' + Utilities.getUuid()));
  const eventType = String(event.event_type || 'REPLY').toUpperCase();
  const email = String(event.email || '').trim().toLowerCase();
  const messageId = String(event.message_id || '').trim();
  const inReplyTo = String(event.in_reply_to || '').trim();
  const explicitLeadId = String(event.lead_id || '').trim();

  const lock = (typeof LockService !== 'undefined' && LockService.getDocumentLock)
    ? LockService.getDocumentLock()
    : null;
  const hasLock = lock ? lock.tryLock(30000) : true;
  if (!hasLock) {
    throw new Error('LOCK_TIMEOUT: Ein anderer Vorgang greift gerade auf das Sheet zu.');
  }

  try {
    const eventsSh = sheet_(CFG.SHEET_EVENTS);
    if (eventsSh.getLastRow() === 0) {
      eventsSh.appendRow(INBOUND_EVENT_HEADER_);
      eventsSh.getRange(1, 1, 1, 12).setFontWeight('bold').setBackground('#e8eaed');
      eventsSh.setFrozenRows(1);
    } else if (eventsSh.getLastRow() >= 2) {
      // Deduplizierungspruefung
      //
      // Spalte J (Processed) zaehlt bewusst mit: eine fruehere Zeile mit
      // NEEDS_REVIEW hat NIE einen Lead-Zustand veraendert (Abschnitt 3 oben,
      // "Kein Raten"). Sie ist deshalb kein abgeschlossenes Ereignis, sondern
      // ein offener Klaerfall - wird dieselbe Event-/Message-ID spaeter
      // erneut geliefert (z. B. weil inzwischen Internet_Message_ID am Lead
      // nachgetragen wurde), muss die Zuordnung ERNEUT versucht werden.
      // Ohne diese Ausnahme wuerde ein einmal unklarer Sendenachweis
      // dauerhaft als "DUPLICATE_IGNORED" verschluckt, obwohl er inzwischen
      // zuordenbar waere - das widerspraeche der Exactly-once-Garantie fuer
      // SENT ebenso wie einer spaeteren Korrektur bei REPLY/BOUNCE.
      const existingEvents = eventsSh.getRange(2, 1, eventsSh.getLastRow() - 1, 10).getValues();
      for (let ei = 0; ei < existingEvents.length; ei++) {
        const rowEvtId = String(existingEvents[ei][0]);
        const rowMsgId = String(existingEvents[ei][5]);
        const rowStatus = String(existingEvents[ei][9] || '');
        const isTerminal = rowStatus !== 'NEEDS_REVIEW' && rowStatus !== 'DUPLICATE';
        if (isTerminal && (rowEvtId === eventId || (messageId && rowMsgId === messageId))) {
          return {
            ok: true,
            duplicate: true,
            event_id: rowEvtId,
            status: 'DUPLICATE_IGNORED',
            lead_id: existingEvents[ei][6] || ''
          };
        }
      }
    }

    // Lead-Zuordnung
    const read = readLeadsCached_();
    let matchedLead = null;
    let domainOptOutLeads = [];   // nur bei OPT_OUT ueber die Firmendomain gefuellt

    if (explicitLeadId) {
      matchedLead = read.leads.filter(function (l) {
        return String(l.Lead_ID) === explicitLeadId;
      })[0];
    }

    if (!matchedLead && eventType === 'SENT') {
      // Sendenachweis-Korrelation: Microsoft dokumentiert, dass die normale
      // Element-ID (hier Outlook_Message_ID/Draft_ID) sich aendern kann,
      // wenn ein Element die Ordner wechselt - und genau das passiert beim
      // Versand eines Entwurfs (Drafts -> Sent Items). Nur die
      // Internet_Message_ID (RFC-5322 Message-ID, Teil des MIME-Inhalts)
      // bleibt dabei inhaltsbedingt stabil. Ein SENT-Ereignis darf deshalb
      // NUR ueber eine explizite Lead-ID oder ueber Internet_Message_ID
      // zugeordnet werden - nie ueber Outlook_Message_ID/Draft_ID allein und
      // nie ueber die E-Mail-Adresse (die beweist keinen bestimmten Versand,
      // nur eine Adresse). Alles andere geht fail-closed nach NEEDS_REVIEW.
      const ref = messageId || inReplyTo;
      if (ref) {
        matchedLead = read.leads.filter(function (l) {
          return l.Internet_Message_ID && String(l.Internet_Message_ID) === ref;
        })[0];
      }
    } else {
      if (!matchedLead && (inReplyTo || messageId)) {
        const searchRef = inReplyTo || messageId;
        matchedLead = read.leads.filter(function (l) {
          return (l.Internet_Message_ID && String(l.Internet_Message_ID) === searchRef)
              || (l.Outlook_Message_ID && String(l.Outlook_Message_ID) === searchRef)
              || (l.Draft_ID && String(l.Draft_ID) === searchRef);
        })[0];
      }

      if (!matchedLead && email) {
        const candidates = read.leads.filter(function (l) {
          return String(l.Email || '').trim().toLowerCase() === email;
        });
        if (candidates.length === 1) {
          matchedLead = candidates[0];
        } else if (candidates.length > 1 && event.owner) {
          const oNorm = normalizeOwner_(event.owner);
          const ownerCandidates = candidates.filter(function (l) {
            return normalizeOwner_(l.Owner) === oNorm;
          });
          if (ownerCandidates.length === 1) matchedLead = ownerCandidates[0];
        }
      }

      // Abmeldung aus einer Firmendomain: Der Widerspruch gilt dem Unternehmen
      // (§ 7 UWG). Kommt "Abmelden" von einer anderen Adresse derselben
      // Firmendomain (Lead: info@firma.de, Antwort: vorname.name@firma.de),
      // wird JEDER Lead dieser Domain gesperrt. Eine Abmeldung darf nie als
      // Klaerfall liegen bleiben, waehrend weiter gesendet wird - hier ist
      // Sperren die sichere Richtung, nicht Abwarten. Freemail-Domains
      // tragen keine Firmenzuordnung und bleiben ausgenommen (NEEDS_REVIEW).
      if (!matchedLead && eventType === 'OPT_OUT' && email) {
        const optOutDomain = email.split('@')[1] || '';
        if (optOutDomain && !istFreemailDomain_(optOutDomain)) {
          domainOptOutLeads = read.leads.filter(function (l) {
            return String(l.Email || '').trim().toLowerCase().split('@')[1] === optOutDomain;
          });
          if (domainOptOutLeads.length) matchedLead = domainOptOutLeads[0];
        }
      }

      // Reverse Lookup wenn failed_recipient uebergeben wurde (NDR / Mailer-Daemon)
      if (!matchedLead && event.failed_recipient) {
        const failEmail = String(event.failed_recipient).trim().toLowerCase();
        const candidates = read.leads.filter(function (l) {
          return String(l.Email || '').trim().toLowerCase() === failEmail;
        });
        if (candidates.length === 1) matchedLead = candidates[0];
      }
    }

    const ts = nowIso_();
    if (!matchedLead) {
      // UNMATCHED: Niemals raten, in Review-Warteschlange legen
      eventsSh.appendRow(inboundEventRow_({
        eventId: eventId, ts: ts, mailbox: event.mailbox, from: email, subject: event.subject,
        messageId: messageId, leadId: '', type: eventType, status: 'NEEDS_REVIEW',
        notes: event.details || 'Nicht eindeutig zuordenbar', inReplyTo: inReplyTo
      }));
      logActivity_('', 'INBOUND_UNMATCHED',
        eventType + ' von ' + (email || 'unbekannt') + ' (NEEDS_REVIEW)');
      return {
        ok: true,
        matched: false,
        event_id: eventId,
        status: 'NEEDS_REVIEW'
      };
    }

    // MATCHED: Lead-Status aktualisieren
    const leadId = matchedLead.Lead_ID;
    const owner = normalizeOwner_(matchedLead.Owner);

    if (eventType === 'REPLY' || eventType === 'POSITIVE_REPLY' || eventType === 'NEGATIVE_REPLY') {
      setLeadStatus(leadId, eventType, 0, 'Inbound-Antwort empfangen');
    } else if (eventType === 'HARD_BOUNCE') {
      setLeadStatus(leadId, 'HARD_BOUNCE', 0, 'Hard Bounce: Empfaenger unzustellbar');
    } else if (eventType === 'SOFT_BOUNCE') {
      setLeadStatus(leadId, 'SOFT_BOUNCE', 3, 'Soft Bounce: Wiedervorlage in 3 Tagen');
    } else if (eventType === 'OPT_OUT') {
      if (domainOptOutLeads.length) {
        domainOptOutLeads.forEach(function (l) {
          setLeadStatus(l.Lead_ID, 'OPT_OUT', 0, 'Opt-out: Domain-Abmeldung von ' + email);
        });
      } else {
        setLeadStatus(leadId, 'OPT_OUT', 0, 'Opt-out: Abmeldung vermerkt');
      }
    } else if (eventType === 'AUTO_REPLY_OOO') {
      const followUp = parseInt(event.follow_up_days, 10) || 7;
      setLeadStatus(leadId, 'AUTO_REPLY_OOO', followUp, 'Abwesenheitsnotiz (' + (event.details || 'Urlaub') + ')');
    } else if (eventType === 'CONTACT_CHURN') {
      setLeadStatus(leadId, 'CONTACT_CHURN', 0, 'Kontakt-Wechsel: ' + (event.details || 'Person ausgeschieden'));
    } else if (eventType === 'SENT') {
      // Geschaeftsseitige Idempotenz zusaetzlich zur Event-/Message-ID-
      // Dedup-Pruefung oben: Diese greift nur, wenn Event- ODER Message-ID
      // identisch wiederkehren. Ein zweites, technisch anderes Sendesignal
      // fuer denselben bereits bestaetigten Lead (z. B. ein erneuter
      // Automatisierungslauf mit neuer Event-/Message-ID) darf trotzdem
      // keine zweite Statusaenderung oder Aktivitaet erzeugen - SENT ist ein
      // Einwegzustand.
      if (String(matchedLead.Send_Status || '').toLowerCase() === 'sent') {
        eventsSh.appendRow(inboundEventRow_({
          eventId: eventId, ts: ts, mailbox: event.mailbox, from: email, subject: event.subject,
          messageId: messageId, leadId: leadId, type: eventType, status: 'ALREADY_SENT_IGNORED',
          notes: 'Lead bereits als SENT vermerkt - keine erneute Statusaenderung/Aktivitaet', inReplyTo: inReplyTo
        }));
        return {
          ok: true, matched: true, lead_id: leadId, owner: owner,
          event_type: eventType, status: 'ALREADY_SENT_IGNORED'
        };
      }
      // Zwei Beweisstufen, die im Audit-Trail unterscheidbar bleiben muessen:
      // ein technischer Nachweis (Message-Korrelation) sagt "das System hat
      // es gesehen", eine reine Lead-ID-Bestaetigung ohne Message-Bezug
      // (siehe confirmBatchSent unten) sagt nur "ein Mensch hat es erklaert".
      const beleg = messageId || inReplyTo;
      const hinweis = beleg
        ? 'Sendenachweis abgeglichen (' + beleg + ')'
        : 'Betreiber-Bestaetigung: manueller Versand ohne automatischen Nachweis';
      setLeadStatus(leadId, 'SENT', 0, hinweis);
      stampBatchSentAt_(matchedLead.Batch_ID);
    }

    const eventNotiz = domainOptOutLeads.length
      ? ('Domain-Abmeldung von ' + email + ': gesperrt ' + domainOptOutLeads.map(function (l) { return l.Lead_ID; }).join(', '))
      : (event.subject || event.details || 'Erfolgreich zugeordnet');
    eventsSh.appendRow(inboundEventRow_({
      eventId: eventId, ts: ts, mailbox: event.mailbox, from: email, subject: event.subject,
      messageId: messageId, leadId: leadId, type: eventType, status: 'PROCESSED',
      notes: eventNotiz, inReplyTo: inReplyTo
    }));

    logActivity_(matchedLead.Batch_ID || '', 'INBOUND_' + eventType,
      leadId + ' (' + email + ') verarbeitet');

    return {
      ok: true,
      matched: true,
      lead_id: leadId,
      owner: owner,
      event_type: eventType,
      status: 'PROCESSED'
    };
  } finally {
    if (lock && hasLock) {
      try { lock.releaseLock(); } catch (_) {}
    }
  }
}

/**
 * Betreiber-Bestaetigung: "Ich habe diesen Batch tatsaechlich in Outlook
 * versendet." Es gibt (noch) keine lebende Power-Automate/Graph-Sent-
 * Trigger-Integration, die einen echten Versand automatisch beobachten und
 * melden koennte (siehe PROJECT_STATE.md) - bis dahin ist das hier die
 * einzige Moeglichkeit, SENT ueberhaupt zu setzen. Bewusst KEIN direktes
 * Schreiben auf Send_Status: jeder Lead laeuft durch dieselbe
 * processInboundEvent()-Logik wie ein technischer Sendenachweis und erbt
 * damit alle dort bereits gebauten und getesteten Garantien - dieselbe
 * Exactly-once-Sperre (ALREADY_SENT_IGNORED bei Wiederholung), denselben
 * INBOUND_EVENTS-Audit-Eintrag, dieselbe Batch-Sent_At-Stempelung. Die
 * explizite Lead-ID ist dabei die staerkste Korrelationsstufe, die
 * processInboundEvent kennt - hier zu Recht, denn ein Mensch bestaetigt
 * direkt, nicht ein System ueber eine Message-ID.
 *
 * In Bloecken statt auf einmal, aus demselben Grund wie beim EML-Export:
 * jeder processInboundEvent()-Aufruf liest ueber readLeadsCached_() das
 * komplette ALL_LEADS-Blatt neu ein, weil der Cache nach jeder erfolgreichen
 * Statusaenderung ungueltig wird. Hundert Wiederholungen in einem einzigen
 * Serveraufruf waeren unnoetig nah an der Sechs-Minuten-Grenze.
 */
var CONFIRM_CHUNK_SIZE = 20;

function confirmBatchSent(batchId, startIndex) {
  const id = String(batchId || '').trim();
  if (!id) throw new Error('Keine Batch-Kennung uebergeben.');
  const alleLeads = readLeadsCached_().leads.filter(function (l) {
    return String(l.Batch_ID) === id;
  });
  if (!alleLeads.length) throw new Error('Keine Leads fuer Batch ' + id);

  const von = Math.max(0, parseInt(startIndex, 10) || 0);
  const slice = alleLeads.slice(von, von + CONFIRM_CHUNK_SIZE);
  let neuBestaetigt = 0;
  let bereitsGesendet = 0;

  slice.forEach(function (lead) {
    const res = processInboundEvent({
      event_id: 'OPCONFIRM-' + id + '-' + lead.Lead_ID,
      event_type: 'SENT',
      lead_id: lead.Lead_ID
    });
    if (res.status === 'ALREADY_SENT_IGNORED' || res.status === 'DUPLICATE_IGNORED' || res.duplicate) {
      bereitsGesendet++;
    } else if (res.matched) {
      neuBestaetigt++;
    }
  });

  const weiter = von + slice.length;
  const fertig = weiter >= alleLeads.length;
  return {
    batch_id: id,
    total: alleLeads.length,
    verarbeitet: slice.length,
    neu_bestaetigt: neuBestaetigt,
    bereits_gesendet: bereitsGesendet,
    complete: fertig,
    next_index: fertig ? null : weiter
  };
}

/* ------------------------------------------------ Premium Sheet UX */

/**
 * Richtet das gesamte Google Sheet mit Live-Formeln, dynamischem Cockpit
 * und aufgeraeumter Spaltenstruktur ein.
 */
function setupPremiumSheetUX() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 1. Sichtbare Tabs einstellen
  const keepVisible = ['README', 'VERSAND', 'ALL_LEADS', 'DASHBOARD', 'BATCHES'];
  ss.getSheets().forEach(function (sh) {
    const name = sh.getName();
    if (keepVisible.indexOf(name) === -1) {
      try { sh.hideSheet(); } catch (_) {}
    } else {
      try { sh.showSheet(); } catch (_) {}
    }
  });

  // 2. README Startseite dynamisieren
  const readme = ss.getSheetByName('README');
  if (readme) {
    readme.clear();
    readme.setTabColor('#1a73e8');

    const readmeData = [
      ['HSB Sales OS · Leitstand', ''],
      ['Status', 'PRODUKTIV EINSATZBEREIT'],
      ['', ''],
      ['LIVE-KENNZAHLEN (Echtzeit)', ''],
      ['Gesamte Leads im System', '=COUNTA(ALL_LEADS!A2:A)'],
      ['Leads von Jordi Post', '=COUNTIF(ALL_LEADS!AA2:AA; "*Jordi*")'],
      ['Leads von Joel Cherino Diaz', '=COUNTIF(ALL_LEADS!AA2:AA; "*Joel*")'],
      ['Vorbereitete Batches', '=COUNTA(BATCHES!A2:A)'],
      ['In Batches reservierte Kontakte', '=COUNTIF(ALL_LEADS!AN2:AN; "<>")'],
      ['Tatsächlich versendete E-Mails', '=COUNTIF(ALL_LEADS!AO2:AO; "sent")'],
      ['Eingegangene Antworten', '=COUNTIF(ALL_LEADS!AR2:AR; "replied")'],
      ['Offene Klärungsfälle (Review)', '=COUNTIF(ALL_LEADS!BD2:BD; "<>")'],
      ['', ''],
      ['SCHNELLSTART-ANLEITUNG FÜR JORDI & JOEL', ''],
      ['1. Seitenleiste öffnen', 'Klicke oben im Menü auf "HSB Sales OS" -> "Seitenleiste öffnen".'],
      ['2. Absender wählen', 'Wähle in der Seitenleiste oben deinen Reiter ("Jordi" oder "Joel").'],
      ['3. Paketgröße wählen', 'Unterstützt: 1, 25, 100 oder 150 Kontakte (Schnellstart: "100 freigeben & Entwürfe erzeugen").'],
      ['4. Outlook-Entwürfe laden', 'Die Seitenleiste lädt die ZIP-Pakete herunter. Mails in Outlook in "Entwürfe" ziehen.'],
      ['5. Nach manuellem Versand', 'In der Seitenleiste beim Batch auf "Versand bestätigen" klicken.'],
      ['', ''],
      ['TABELLEN-ÜBERSICHT', ''],
      ['ALL_LEADS', 'Die zentrale Kontaktdatenbank (6.424 geprüfte Kontakte).'],
      ['BATCHES', 'Historie aller vorbereiteten und freigegebenen Kampagnen-Pakete.'],
      ['VERSAND', 'Projektionsansicht aller aktuell in Vorbereitung/Versand befindlichen Leads.'],
      ['DASHBOARD', 'Kompakte Chef-Übersicht & Vergleich zwischen Jordi und Joel.']
    ];

    readme.getRange(1, 1, readmeData.length, 2).setValues(readmeData);
    readme.getRange('A1:B1').merge().setFontSize(16).setFontWeight('bold').setBackground('#1a73e8').setFontColor('#ffffff');
    readme.getRange('A4:B4').merge().setFontSize(12).setFontWeight('bold').setBackground('#e8eaed');
    readme.getRange('A14:B14').merge().setFontSize(12).setFontWeight('bold').setBackground('#e8eaed');
    readme.getRange('A21:B21').merge().setFontSize(12).setFontWeight('bold').setBackground('#e8eaed');
    readme.setColumnWidth(1, 300);
    readme.setColumnWidth(2, 550);
  }

  // 3. DASHBOARD formatieren
  const dash = ss.getSheetByName('DASHBOARD');
  if (dash) {
    dash.clear();
    dash.setTabColor('#0d652d');

    const dashData = [
      ['HSB SALES OS · VERTRIEBS-COCKPIT', '', '', '', ''],
      ['', '', '', '', ''],
      ['Metrik / Kennzahl', 'Gesamt', 'Jordi Post', 'Joel Cherino Diaz', 'Status / Ziel'],
      ['Kontakte gesamt', '=COUNTA(ALL_LEADS!A2:A)', '=COUNTIF(ALL_LEADS!AA2:AA; "*Jordi*")', '=COUNTIF(ALL_LEADS!AA2:AA; "*Joel*")', '6.424 verifiziert'],
      ['Tier A Kontakte', '=COUNTIF(ALL_LEADS!F2:F; "A")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Jordi*"; ALL_LEADS!F2:F; "A")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Joel*"; ALL_LEADS!F2:F; "A")', 'Prio 1 Kaltakquise'],
      ['Tier B Kontakte', '=COUNTIF(ALL_LEADS!F2:F; "B")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Jordi*"; ALL_LEADS!F2:F; "B")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Joel*"; ALL_LEADS!F2:F; "B")', 'Prio 2 Kaltakquise'],
      ['In Batches reserviert', '=COUNTIF(ALL_LEADS!AN2:AN; "<>")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Jordi*"; ALL_LEADS!AN2:AN; "<>")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Joel*"; ALL_LEADS!AN2:AN; "<>")', 'Vorbereitet'],
      ['Tatsächlich versendet', '=COUNTIF(ALL_LEADS!AO2:AO; "sent")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Jordi*"; ALL_LEADS!AO2:AO; "sent")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Joel*"; ALL_LEADS!AO2:AO; "sent")', 'Bestaetigt'],
      ['Antworten erhalten', '=COUNTIF(ALL_LEADS!AR2:AR; "replied")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Jordi*"; ALL_LEADS!AR2:AR; "replied")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Joel*"; ALL_LEADS!AR2:AR; "replied")', 'Inbound'],
      ['Opt-Outs / Bounces', '=COUNTIF(ALL_LEADS!AQ2:AQ; "<>") + COUNTIF(ALL_LEADS!AT2:AT; "yes")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Jordi*"; ALL_LEADS!AT2:AT; "yes")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*Joel*"; ALL_LEADS!AT2:AT; "yes")', 'Gesperrt'],
      ['', '', '', '', ''],
      ['ERZEUGTE BATCHES (Letzte 10)', '', '', '', ''],
      ['Batch ID', 'Owner', 'Status', 'Anzahl Leads', 'Erstellt am']
    ];

    dash.getRange(1, 1, dashData.length, 5).setValues(dashData);
    dash.getRange('A1:E1').merge().setFontSize(16).setFontWeight('bold').setBackground('#0d652d').setFontColor('#ffffff');
    dash.getRange('A3:E3').setFontWeight('bold').setBackground('#e8eaed');
    dash.getRange('A12:E12').merge().setFontSize(12).setFontWeight('bold').setBackground('#e8eaed');
    dash.getRange('A13:E13').setFontWeight('bold').setBackground('#f1f3f4');

    for (let b = 1; b <= 10; b++) {
      const rowNum = 13 + b;
      dash.getRange(rowNum, 1).setValue('=IF(ISBLANK(BATCHES!A' + (b + 1) + '); ""; BATCHES!A' + (b + 1) + ')');
      dash.getRange(rowNum, 2).setValue('=IF(ISBLANK(BATCHES!B' + (b + 1) + '); ""; BATCHES!B' + (b + 1) + ')');
      dash.getRange(rowNum, 3).setValue('=IF(ISBLANK(BATCHES!D' + (b + 1) + '); ""; BATCHES!D' + (b + 1) + ')');
      dash.getRange(rowNum, 4).setValue('=IF(ISBLANK(BATCHES!F' + (b + 1) + '); ""; BATCHES!F' + (b + 1) + ')');
      dash.getRange(rowNum, 5).setValue('=IF(ISBLANK(BATCHES!K' + (b + 1) + '); ""; BATCHES!K' + (b + 1) + ')');
    }

    dash.setColumnWidth(1, 240);
    dash.setColumnWidth(2, 130);
    dash.setColumnWidth(3, 150);
    dash.setColumnWidth(4, 150);
    dash.setColumnWidth(5, 180);
  }

  // 4. ALL_LEADS formatieren
  const allLeads = ss.getSheetByName('ALL_LEADS');
  if (allLeads) {
    allLeads.setFrozenRows(1);
    allLeads.setTabColor('#f29900');
    allLeads.getRange(1, 1, 1, 56).setFontWeight('bold').setBackground('#1f2937').setFontColor('#ffffff');

    // Konditionale Formatierung: Visuelles Farb-Leitsystem (Blau, Gruen, Gelb, Rot, Flieder)
    try {
      const rules = allLeads.getConditionalFormatRules() || [];
      const blueRowRule = SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=$AO2="sent"')
        .setBackground('#e8f0fe')
        .setFontColor('#174ea6')
        .setBold(true)
        .setRanges([allLeads.getRange('AN2:BD6500')])
        .build();
      const blueChipRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('sent')
        .setBackground('#c2e7ff')
        .setFontColor('#001b36')
        .setBold(true)
        .setRanges([allLeads.getRange('AO2:AO6500')])
        .build();
      const positiveRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('positive_reply')
        .setBackground('#ceead6')
        .setFontColor('#0d652d')
        .setBold(true)
        .setRanges([allLeads.getRange('AR2:AR6500')])
        .build();
      const greenRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('replied')
        .setBackground('#e6f4ea')
        .setFontColor('#137333')
        .setBold(true)
        .setRanges([allLeads.getRange('AR2:AR6500')])
        .build();
      const oooRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('auto_reply_ooo')
        .setBackground('#fef7e0')
        .setFontColor('#b06000')
        .setBold(true)
        .setRanges([allLeads.getRange('AR2:AR6500')])
        .build();
      const hardBounceRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('hard_bounce')
        .setBackground('#fce8e6')
        .setFontColor('#c5221f')
        .setBold(true)
        .setRanges([allLeads.getRange('AQ2:AQ6500')])
        .build();
      const softBounceRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('soft_bounce')
        .setBackground('#feefe3')
        .setFontColor('#c26401')
        .setBold(true)
        .setRanges([allLeads.getRange('AQ2:AQ6500')])
        .build();
      const optOutRule = SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo('yes')
        .setBackground('#f3e8fd')
        .setFontColor('#7627bb')
        .setBold(true)
        .setRanges([allLeads.getRange('AT2:AT6500')])
        .build();

      rules.unshift(optOutRule);
      rules.unshift(softBounceRule);
      rules.unshift(hardBounceRule);
      rules.unshift(oooRule);
      rules.unshift(greenRule);
      rules.unshift(positiveRule);
      rules.unshift(blueChipRule);
      rules.unshift(blueRowRule);
      allLeads.setConditionalFormatRules(rules);
    } catch (_) {}
  }

  SpreadsheetApp.flush();
  return { ok: true, message: 'Premium Sheet UX erfolgreich eingerichtet.' };
}


/**
 * UI-Bridge fuer Direkt-Entwuerfe im Batch via Draft-Adapter in sicheren 10er-Haeppchen.
 */
function uiCreateDraftsChunk(batchId, chunkSize) {
  try {
    if (typeof createDraftsForBatch === 'function') {
      var size = parseInt(chunkSize, 10) || 10;
      var summary = createDraftsForBatch(String(batchId), { limit: size });
      var allLeads = (readLeads_().leads) || [];
      var batchLeads = allLeads.filter(function (l) { return String(l.Batch_ID) === String(batchId); });
      var draftedLeads = batchLeads.filter(function (l) { return !!l.Draft_ID; });
      var openLeads = batchLeads.filter(function (l) {
        return !l.Draft_ID;
      });
      return {
        ok: true,
        data: {
          summary: summary,
          draftedCount: draftedLeads.length,
          openCount: openLeads.length,
          totalCount: batchLeads.length,
          isComplete: openLeads.length === 0
        }
      };
    }
    return { ok: true, data: { summary: 'DraftAdapter nicht gebunden.', draftedCount: 0, openCount: 0, totalCount: 0, isComplete: true } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/**
 * UI-Bridge fuer Direkt-Entwuerfe mit globalem Limit (Fallback/Kompatibilitaet).
 */
function uiCreateDraftsForBatch(batchId, limit) {
  try {
    if (typeof createDraftsForBatch === 'function') {
      var n = parseInt(limit, 10);
      if (!n || n < 1) n = 9999;
      var summary = createDraftsForBatch(String(batchId), { limit: n });
      return { ok: true, data: { summary: summary } };
    }
    return { ok: true, data: { summary: 'DraftAdapter nicht gebunden.' } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/** Klaerfaelle aus INBOUND_EVENTS anwenden: Spalte M traegt eine Lead-ID oder "ignorieren". */
function hsbKlaerfaelleAnwenden() {
  const sh = sheet_(CFG.SHEET_EVENTS);
  const n = sh.getLastRow();
  const out = { ok: true, applied: 0, ignored: 0, errors: [] };
  if (n < 2) return out;
  if (sh.getMaxColumns() < 13) sh.insertColumnsAfter(sh.getMaxColumns(), 13 - sh.getMaxColumns());
  const vals = sh.getRange(2, 1, n - 1, 13).getValues();
  const knownLeadIds = readLeadsCached_().leads.map(function (l) { return String(l.Lead_ID); });
  for (let i = 0; i < vals.length; i++) {
    const r = vals[i];
    const entscheidung = String(r[12] || '').trim();
    if (String(r[9]) !== 'NEEDS_REVIEW' || !entscheidung) continue;
    if (entscheidung.toLowerCase() === 'ignorieren') {
      sh.getRange(i + 2, 10).setValue('IGNORED'); out.ignored++; continue;
    }
    if (knownLeadIds.indexOf(entscheidung) === -1) {
      out.errors.push(String(r[0]) + ': Lead-ID ' + entscheidung + ' nicht gefunden');
      continue;
    }
    try {
      const res = processInboundEvent({
        event_id: String(r[0]) + '-MANUAL', event_type: String(r[7]), lead_id: entscheidung,
        email: String(r[3] || ''), message_id: String(r[5] || ''), subject: String(r[4] || ''),
        mailbox: String(r[2] || ''), details: 'Manuell zugeordnet (Klaerfall)'
      });
      if (res && res.matched) {
        sh.getRange(i + 2, 10).setValue('RESOLVED');
        sh.getRange(i + 2, 7).setValue(entscheidung);
        out.applied++;
      } else out.errors.push(String(r[0]) + ': Lead-ID ' + entscheidung + ' nicht gefunden');
    } catch (e) { out.errors.push(String(r[0]) + ': ' + String(e.message || e)); }
  }
  out.ok = out.errors.length === 0;
  return out;
}

function uiKlaerfaelleAnwenden() {
  const ui = SpreadsheetApp.getUi();
  const r = hsbKlaerfaelleAnwenden();
  ui.alert('Klaerfaelle angewendet', 'Zugeordnet: ' + r.applied + '\nIgnoriert: ' + r.ignored +
           (r.errors.length ? ('\n\nFehler:\n' + r.errors.join('\n')) : ''), ui.ButtonSet.OK);
  return r;
}
