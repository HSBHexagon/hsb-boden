/**
 * HSB Sales OS - Aktionen: Qualifizierung, Entwuerfe, EML-Fallback,
 * Wiedervorlage, Statusrueckschreibung.
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
  const ownerKey = normalizeOwner_(opts.owner);
  const legalBasis = String(opts.legalBasis || '').toUpperCase();
  const limit = Math.max(0, parseInt(opts.count, 10) || 0);

  if (LEGAL_BASIS_ALL.indexOf(legalBasis) === -1) {
    throw new Error('Ungueltige Legal_Basis: ' + legalBasis);
  }
  const sendable = LEGAL_BASIS_SENDABLE.indexOf(legalBasis) >= 0;

  const read = readLeads_();
  const sh = sheet_(CFG.SHEET_LEADS);
  const cLegal = read.index['Legal_Basis'] + 1;
  const cFreigabe = read.index[FIELD_MAP.Versandfreigabe] + 1;
  if (!cLegal || !cFreigabe) {
    throw new Error('Spalten fehlen. Bitte zuerst "Spalten pruefen" ausfuehren.');
  }

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

    sh.getRange(l._row, cLegal).setValue(legalBasis);
    sh.getRange(l._row, cFreigabe).setValue(sendable ? 'yes' : 'no');
    touched++;
  }
  SpreadsheetApp.flush();
  logActivity_('', 'QUALIFY',
    touched + ' Leads auf ' + legalBasis + ' gesetzt (' + ownerKey + ')');
  return { updated: touched, legalBasis: legalBasis, sendable: sendable };
}

/* ----------------------------------------------------- E-Mail-Erzeugung */

function renderEmail_(lead, flyer) {
  const company = String(lead.Company || 'Ihr Unternehmen').trim();
  const contact = String(lead.Contact || '').trim();
  const greeting = contact ? 'Guten Tag ' + contact + ',' : 'Guten Tag,';
  const subject = 'Industrieboeden fuer ' + company + ' - Beratung von '
    + flyer.displayName;

  const body = greeting + '\n\n'
    + 'mein Name ist ' + flyer.displayName + ' von der HSB Hexagon Saeurebau '
    + 'GmbH. Wir planen, bauen und sanieren saeurebestaendige, hygienische '
    + 'Industrieboeden - ausgelegt auf das reale Belastungsprofil statt auf '
    + 'ein Standardprodukt.\n\n'
    + 'Typische Themen bei Produktionsbetrieben:\n'
    + '- Risse, Abloesungen und offene Fugen\n'
    + '- Keimnester in Nassbereichen\n'
    + '- stehendes Wasser durch falsches Gefaelle\n'
    + '- defekte Rinnen und Ablaeufe\n\n'
    + 'Im angehaengten Flyer sehen Sie ausgefuehrte Projektflaechen und unser '
    + 'Vorgehen von der Analyse bis zur dokumentierten Uebergabe.\n\n'
    + 'Gerne pruefen wir Ihr Belastungsprofil unverbindlich und vor Ort.\n\n'
    + 'Mit freundlichen Gruessen\n'
    + flyer.displayName + '\n'
    + 'HSB Hexagon Saeurebau GmbH\n'
    + flyer.mailbox + '\n'
    + 'Tel. +49 (0)2562 9463030\n\n'
    + '---\n'
    + 'Wenn Sie keine weiteren Informationen erhalten moechten, antworten Sie '
    + 'bitte mit dem Betreff "Abmelden" auf diese E-Mail.';

  return { subject: subject, body: body };
}

/** Baut eine RFC-822 EML mit genau einem korrekten PDF-Anhang. */
function buildEml_(lead, batchId, flyer, pdfBase64) {
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
  lines.push('Content-Type: application/pdf; name="' + flyer.fileName + '"');
  lines.push('Content-Transfer-Encoding: base64');
  lines.push('Content-Disposition: attachment; filename="' + flyer.fileName + '"');
  lines.push('');
  lines.push(chunk76_(pdfBase64));
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
 * EML-Fallback: erzeugt fuer einen Batch alle Entwuerfe als ZIP in Drive.
 * Funktioniert ohne Outlook-Verbindung, ohne Admin, ohne DNS.
 */
function exportBatchAsEmlZip(batchId) {
  const read = readLeads_();
  const leads = read.leads.filter(function (l) {
    return String(l.Batch_ID) === String(batchId);
  });
  if (!leads.length) throw new Error('Keine Leads fuer Batch ' + batchId);

  const ownerKey = normalizeOwner_(leads[0].Owner);
  const verified = getVerifiedFlyer_(ownerKey);
  const pdfBase64 = Utilities.base64Encode(verified.blob.getBytes());

  const files = [];
  leads.forEach(function (l) {
    const eml = buildEml_(l, batchId, verified.flyer, pdfBase64);
    const safe = String(l.Lead_ID).replace(/[^A-Za-z0-9._-]+/g, '-');
    files.push(Utilities.newBlob(eml, 'message/rfc822',
               ownerKey.toLowerCase() + '_' + safe + '.eml'));
  });

  const zip = Utilities.zip(files, batchId + '_entwuerfe.zip');
  const folder = getOrCreateFolder_('HSB Sales OS Batches');
  const file = folder.createFile(zip);

  logActivity_(batchId, 'EML_EXPORT', leads.length + ' Entwuerfe als ZIP');
  return {
    batch_id: batchId, count: leads.length,
    url: file.getUrl(), name: file.getName(),
    size_mb: Math.round(file.getSize() / 1048576 * 10) / 10,
    asset_sha256: verified.sha256
  };
}

function getOrCreateFolder_(name) {
  const it = DriveApp.getFoldersByName(name);
  return it.hasNext() ? it.next() : DriveApp.createFolder(name);
}

/* --------------------------------------------------- Wiedervorlage / CRM */

/** Setzt Status und Wiedervorlage fuer einen einzelnen Lead. */
function setLeadStatus(leadId, status, followUpDays, note) {
  const read = readLeads_();
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
  if (s === 'REPLIED' || s === 'POSITIVE_REPLY' || s === 'NEGATIVE_REPLY') {
    set(FIELD_MAP.Reply_Status, s.toLowerCase());
    set('Last_Reply_At', todayStr_());
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
  logActivity_(lead.Batch_ID || '', s, leadId + (note ? ' - ' + note : ''));
  return { lead_id: leadId, status: s };
}

/** Alle heute oder frueher faelligen Wiedervorlagen. */
function getDueFollowUps(ownerKey) {
  const read = readLeads_();
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
  const read = readLeads_();
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
