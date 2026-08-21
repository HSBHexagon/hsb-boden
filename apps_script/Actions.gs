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
  lines.push('Content-Type: application/pdf; name="' + flyer.fileName + '"');
  lines.push('Content-Transfer-Encoding: base64');
  lines.push('Content-Disposition: attachment; filename="' + flyer.fileName + '"');
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
var EML_CHUNK_SIZE = 20;

function exportBatchAsEmlZip(batchId, startIndex) {
  const read = readLeadsCached_();
  const leads = read.leads.filter(function (l) {
    return String(l.Batch_ID) === String(batchId);
  });
  if (!leads.length) throw new Error('Keine Leads fuer Batch ' + batchId);

  const ownerKey = normalizeOwner_(leads[0].Owner);
  const verified = getVerifiedFlyer_(ownerKey);
  // Genau einmal erzeugen - identisch fuer jede EML.
  const pdfChunked = chunk76_(Utilities.base64Encode(verified.blob.getBytes()));

  const folder = getOrCreateFolder_('HSB Sales OS Batches');
  const started = new Date().getTime();
  const parts = [];
  let i = Math.max(0, parseInt(startIndex, 10) || 0);
  let written = 0;

  while (i < leads.length) {
    // Vor jedem Teilpaket pruefen, ob noch Laufzeit bleibt (Limit 6 Minuten).
    if (new Date().getTime() - started > 4 * 60 * 1000) break;

    const slice = leads.slice(i, i + EML_CHUNK_SIZE);
    const files = slice.map(function (l) {
      const safe = String(l.Lead_ID).replace(/[^A-Za-z0-9._-]+/g, '-');
      return Utilities.newBlob(
        buildEml_(l, batchId, verified.flyer, pdfChunked),
        'message/rfc822', ownerKey.toLowerCase() + '_' + safe + '.eml');
    });

    const part = Math.floor(i / EML_CHUNK_SIZE) + 1;
    const name = batchId + '_teil' + ('0' + part).slice(-2) + '.zip';
    const file = folder.createFile(Utilities.zip(files, name));
    parts.push({
      name: name, url: file.getUrl(), count: slice.length,
      size_mb: Math.round(file.getSize() / 1048576 * 10) / 10
    });
    written += slice.length;
    i += EML_CHUNK_SIZE;
  }

  const done = i >= leads.length;
  logActivity_(batchId, 'EML_EXPORT',
    written + ' von ' + leads.length + ' Entwuerfen in ' + parts.length
    + ' Teilpaket(en)' + (done ? '' : ' - Fortsetzung noetig ab ' + i));

  return {
    batch_id: batchId,
    total: leads.length,
    written: written,
    complete: done,
    next_index: done ? null : i,
    parts: parts,
    folder_url: folder.getUrl(),
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
      eventsSh.appendRow(['Event_ID', 'Timestamp', 'Type', 'Lead_ID', 'Owner',
                          'Email', 'Message_ID', 'In_Reply_To', 'Status', 'Details']);
      eventsSh.getRange(1, 1, 1, 10).setFontWeight('bold').setBackground('#e8eaed');
      eventsSh.setFrozenRows(1);
    } else if (eventsSh.getLastRow() >= 2) {
      // Deduplizierungspruefung
      const existingEvents = eventsSh.getRange(2, 1, eventsSh.getLastRow() - 1, 7).getValues();
      for (let ei = 0; ei < existingEvents.length; ei++) {
        const rowEvtId = String(existingEvents[ei][0]);
        const rowMsgId = String(existingEvents[ei][6]);
        if (rowEvtId === eventId || (messageId && rowMsgId === messageId)) {
          return {
            ok: true,
            duplicate: true,
            event_id: rowEvtId,
            status: 'DUPLICATE_IGNORED',
            lead_id: existingEvents[ei][3] || ''
          };
        }
      }
    }

    // Lead-Zuordnung
    const read = readLeadsCached_();
    let matchedLead = null;

    if (explicitLeadId) {
      matchedLead = read.leads.filter(function (l) {
        return String(l.Lead_ID) === explicitLeadId;
      })[0];
    }

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

    const ts = nowIso_();
    if (!matchedLead) {
      // UNMATCHED: Niemals raten, in Review-Warteschlange legen
      eventsSh.appendRow([
        eventId, ts, eventType, '', event.owner || '',
        email, messageId, inReplyTo, 'NEEDS_REVIEW',
        event.subject || event.details || 'Nicht eindeutig zuordenbar'
      ]);
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
      setLeadStatus(leadId, 'OPT_OUT', 0, 'Opt-out: Abmeldung vermerkt');
    }

    eventsSh.appendRow([
      eventId, ts, eventType, leadId, owner,
      email, messageId, inReplyTo, 'PROCESSED',
      event.subject || event.details || 'Erfolgreich zugeordnet'
    ]);

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
