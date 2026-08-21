/**
 * HSB Sales OS - Gesamtdatei (Config + Engine + Actions + Code).
 *
 * Alles in einer Datei, damit beim Einbau nur zwei Dateien noetig sind:
 * diese hier als Script und Sidebar.html als HTML.
 *
 * Erzeugt aus apps_script/*.gs - nicht direkt bearbeiten, sondern die
 * Quelldateien aendern und neu buendeln (build_single.py).
 */


/* ==================================================================
   Config.gs
   ================================================================== */

/**
 * HSB Sales OS - Konfiguration und kanonische Assets.
 *
 * Wahrheitsordnung: sender -> exakte Drive-ID -> exakter SHA-256.
 * Niemals per Dateiname, Datum oder "neuester Datei" aufloesen.
 */

const CFG = {
  SHEET_LEADS: 'ALL_LEADS',
  SHEET_BATCHES: 'BATCHES',
  SHEET_EVENTS: 'INBOUND_EVENTS',
  SHEET_ACTIVITY: 'ACTIVITIES',
  TIMEZONE: 'Europe/Berlin',
  // Konservativ. Microsofts technische Grenzen sind keine Zielrate.
  SEND_RATE_PER_MINUTE: 2
};

/** Kanonische Flyer - IMMUTABLE RELEASE ASSETS. */
const FLYERS = {
  JORDI: {
    key: 'JORDI',
    displayName: 'Jordi Post',
    mailbox: 'j-post@hsb-boden.de',
    fileName: 'HSB-Flyer-Jordi-Post_FINAL.pdf',
    driveId: '1BHx9TmtGomgslTNhi2_1VoBVPer20zkT',
    sha256: 'e0aa76c1ffec5cf89289e6ab141691d42ea81ffd13db2f08f045342531f39acc'
  },
  JOEL: {
    key: 'JOEL',
    displayName: 'Joel Cherino Diaz',
    mailbox: 'j-cherino@hsb-boden.de',
    fileName: 'HSB-Flyer-Joel-Cherino_FINAL.pdf',
    driveId: '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS',
    sha256: '2bccadacc77b531057583d2d650963c30deceed36c8be1fd90ca64e8b8cde5fb'
  }
};

/** Reale Sheet-Spalten. Links logischer Name, rechts Spaltenueberschrift. */
const FIELD_MAP = {
  Lead_ID: 'Lead-ID',
  Owner: 'Verantwortlicher',
  Email: 'E-Mail',
  Company: 'Firma',
  Contact: 'Ansprechpartner',
  Industry: 'Branche',
  Tier: 'Tier',
  Campaign_ID: 'Kampagne_ID',
  Versandfreigabe: 'Versandfreigabe',
  Opt_Out: 'Opt-out-Status',
  Opt_In: 'Opt-in-Status',
  Batch_ID: 'Batch_ID',
  Send_Status: 'Send_Status',
  Sent_At: 'Send_Datum',
  Bounce_Status: 'Bounce_Status',
  Reply_Status: 'Reply_Status',
  Next_Action_At: 'Follow-up-Datum',
  Notes: 'Notizen'
};

/** Spalten, die das Sales OS zusaetzlich benoetigt. */
const ADDITIONAL_FIELDS = [
  'Legal_Basis', 'Suppressed', 'Batch_Status', 'Prepared_At', 'Draft_ID',
  'Drafted_At', 'Approved_At', 'Outlook_Message_ID', 'Internet_Message_ID',
  'Conversation_ID', 'Last_Reply_At', 'Last_Error'
];

const LEGAL_BASIS_SENDABLE = ['OPT_IN', 'EXISTING_CUSTOMER_7_3'];
const LEGAL_BASIS_ALL = ['OPT_IN', 'EXISTING_CUSTOMER_7_3', 'BLOCKED', 'UNKNOWN'];

function normalizeOwner_(value) {
  if (!value) return '';
  const v = String(value).trim().toUpperCase();
  if (FLYERS[v]) return v;
  if (v.indexOf('JORDI') >= 0 || v.indexOf('POST') >= 0) return 'JORDI';
  if (v.indexOf('JOEL') >= 0 || v.indexOf('CHERINO') >= 0) return 'JOEL';
  return v;
}

function nowIso_() {
  return Utilities.formatDate(new Date(), 'UTC', "yyyy-MM-dd'T'HH:mm:ss'Z'");
}

function todayStr_() {
  return Utilities.formatDate(new Date(), CFG.TIMEZONE, 'yyyy-MM-dd');
}


/* ==================================================================
   Engine.gs
   ================================================================== */

/**
 * HSB Sales OS - Compliance-Gate, Batch-Engine, Sheet-Zugriff.
 *
 * Kein Hardcoding von Mengen. PREPARE != SEND.
 */

/* ---------------------------------------------------------------- Zugriff */

function sheet_(name) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  return sh;
}

/**
 * Cache innerhalb EINER Ausfuehrung.
 *
 * Das Blatt hat 6.425 Zeilen x 56 Spalten. Jeder Vollzugriff ist teuer und
 * das 6-Minuten-Limit von Apps Script ist real. prepareBatch() braucht die
 * Leads zweimal (Auswahl und aktive Batches) - ohne Cache waere das ein
 * doppelter Volllesevorgang.
 */
var LEADS_CACHE_ = null;

function invalidateLeadsCache_() { LEADS_CACHE_ = null; }

function readLeadsCached_() {
  if (!LEADS_CACHE_) LEADS_CACHE_ = readLeads_();
  return LEADS_CACHE_;
}

/**
 * Schreibt eine Spalte fuer verstreute Zeilen in EINEM Vorgang.
 *
 * Statt N Einzelaufrufen wird der umspannte Bereich einmal gelesen, im
 * Speicher geaendert und einmal zurueckgeschrieben: 2 Aufrufe statt N.
 * updates = { zeilennummer: wert }
 */
function writeColumnBulk_(sh, col, updates) {
  const rows = Object.keys(updates).map(Number).sort(function (a, b) {
    return a - b;
  });
  if (!rows.length || !col) return;
  const first = rows[0];
  const last = rows[rows.length - 1];
  const span = last - first + 1;
  const range = sh.getRange(first, col, span, 1);
  const values = range.getValues();
  rows.forEach(function (r) { values[r - first][0] = updates[r]; });
  range.setValues(values);
}

function readLeads_() {
  const sh = sheet_(CFG.SHEET_LEADS);
  const values = sh.getDataRange().getValues();
  if (values.length < 2) return { header: [], index: {}, rows: [], leads: [] };
  const header = values[0].map(String);
  const index = {};
  header.forEach(function (h, i) { index[h] = i; });

  const leads = [];
  for (let r = 1; r < values.length; r++) {
    const row = values[r];
    if (!row.join('')) continue;
    const lead = { _row: r + 1 };
    Object.keys(FIELD_MAP).forEach(function (logical) {
      lead[logical] = row[index[FIELD_MAP[logical]]];
    });
    ADDITIONAL_FIELDS.forEach(function (f) {
      lead[f] = index[f] === undefined ? '' : row[index[f]];
    });
    leads.push(lead);
  }
  return { header: header, index: index, rows: values, leads: leads };
}

/**
 * Ergaenzt fehlende Spalten einmalig - bestehende werden nie ueberschrieben.
 * Idempotent: mehrfaches Ausfuehren aendert nichts mehr.
 *
 * Das Sheet-Raster muss dafuer erweitert werden; ein reines Schreiben
 * hinter die letzte Spalte scheitert an den Grid-Grenzen.
 */
function ensureColumns() {
  const sh = sheet_(CFG.SHEET_LEADS);
  const lastCol = sh.getLastColumn();
  const header = sh.getRange(1, 1, 1, lastCol).getValues()[0].map(String);
  const missing = ADDITIONAL_FIELDS.filter(function (f) {
    return header.indexOf(f) === -1;
  });
  if (!missing.length) return { added: [], message: 'Alle Spalten vorhanden.' };

  // Raster erweitern, falls die neuen Spalten nicht hineinpassen.
  const needed = lastCol + missing.length;
  if (sh.getMaxColumns() < needed) {
    sh.insertColumnsAfter(sh.getMaxColumns(), needed - sh.getMaxColumns());
  }

  sh.getRange(1, lastCol + 1, 1, missing.length).setValues([missing]);
  sh.getRange(1, lastCol + 1, 1, missing.length)
    .setFontWeight('bold').setBackground('#e8eaed');

  // Legal_Basis fail-closed vorbelegen: ohne Nachweis gilt UNKNOWN.
  const pos = missing.indexOf('Legal_Basis');
  if (pos >= 0 && sh.getLastRow() > 1) {
    const n = sh.getLastRow() - 1;
    const fill = [];
    for (let i = 0; i < n; i++) fill.push(['UNKNOWN']);
    sh.getRange(2, lastCol + 1 + pos, n, 1).setValues(fill);
  }
  // Suppressed ebenfalls explizit auf 'no' setzen statt leer zu lassen.
  const sPos = missing.indexOf('Suppressed');
  if (sPos >= 0 && sh.getLastRow() > 1) {
    const n = sh.getLastRow() - 1;
    const fill = [];
    for (let i = 0; i < n; i++) fill.push(['no']);
    sh.getRange(2, lastCol + 1 + sPos, n, 1).setValues(fill);
  }
  SpreadsheetApp.flush();
  return { added: missing, message: 'Ergaenzt: ' + missing.join(', ') };
}

/* ------------------------------------------------------- Compliance-Gate */

function isTrue_(v) {
  const s = String(v == null ? '' : v).trim().toLowerCase();
  return s === 'yes' || s === 'ja' || s === 'true';
}

/**
 * Technischer Sendefilter, fail-closed (§7 UWG).
 * Gibt { eligible, reasons[] } zurueck.
 */
function checkEligibility_(lead) {
  const reasons = [];

  let legal = String(lead.Legal_Basis || '').trim().toUpperCase();
  if (!legal) {
    const optIn = String(lead.Opt_In || '').trim().toLowerCase();
    legal = (optIn === 'yes' || optIn === 'ja' || optIn === 'opt_in')
      ? 'OPT_IN' : 'UNKNOWN';
  }
  if (LEGAL_BASIS_SENDABLE.indexOf(legal) === -1) {
    reasons.push('Legal_Basis=' + legal);
  }
  if (!isTrue_(lead.Versandfreigabe)) {
    reasons.push('Versandfreigabe=' + (lead.Versandfreigabe || 'leer'));
  }
  if (isTrue_(lead.Suppressed)) reasons.push('Suppressed=YES');

  const optOut = String(lead.Opt_Out || '').trim().toLowerCase();
  if (optOut === 'yes' || optOut === 'ja' || optOut === 'opt_out') {
    reasons.push('Opt_Out=YES');
  }
  const bounce = String(lead.Bounce_Status || '').trim().toLowerCase();
  if (bounce.indexOf('hard') >= 0) reasons.push('Hard Bounce');

  const sendStatus = String(lead.Send_Status || '').trim().toLowerCase();
  if (sendStatus === 'sent' || sendStatus === 'gesendet') {
    reasons.push('bereits gesendet');
  }
  const email = String(lead.Email || '').trim();
  if (!/^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$/.test(email)) {
    reasons.push('E-Mail ungueltig');
  }
  if (!FLYERS[normalizeOwner_(lead.Owner)]) reasons.push('Owner unklar');

  return { eligible: reasons.length === 0, reasons: reasons };
}

/* ------------------------------------------------------------ Asset-Gate */

/**
 * Holt den kanonischen Flyer und prueft ihn gegen den Soll-Hash.
 * Fail-closed: bei Abweichung wird geworfen, nie ersetzt.
 */
function getVerifiedFlyer_(ownerKey) {
  const flyer = FLYERS[normalizeOwner_(ownerKey)];
  if (!flyer) throw new Error('ASSET_GATE=FAIL - unbekannter Absender: ' + ownerKey);

  const file = DriveApp.getFileById(flyer.driveId);
  const blob = file.getBlob();
  const digest = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256, blob.getBytes());
  const hex = digest.map(function (b) {
    return ('0' + (b & 0xFF).toString(16)).slice(-2);
  }).join('');

  if (hex !== flyer.sha256) {
    throw new Error(
      'ASSET_GATE=FAIL fuer ' + flyer.key + ': erwartet ' +
      flyer.sha256.substring(0, 12) + '..., gefunden ' + hex.substring(0, 12) +
      '... Kein automatischer Ersatz durch eine andere PDF.');
  }
  return { flyer: flyer, blob: blob.setName(flyer.fileName), sha256: hex };
}

/* ---------------------------------------------------------- Batch-Engine */

function nextBatchSeq_(ownerKey) {
  const sh = sheet_(CFG.SHEET_BATCHES);
  if (sh.getLastRow() < 2) return 1;
  const ids = sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues();
  let n = 0;
  ids.forEach(function (r) {
    if (String(r[0]).indexOf('-' + ownerKey + '-') >= 0) n++;
  });
  return n + 1;
}

function activeBatchLeadIds_() {
  const sh = sheet_(CFG.SHEET_BATCHES);
  const ids = {};
  if (sh.getLastRow() < 2) return ids;
  const data = sh.getRange(2, 1, sh.getLastRow() - 1, 4).getValues();
  const closed = { SENT: 1, CANCELLED: 1 };
  const leadsSh = sheet_(CFG.SHEET_LEADS);
  const active = {};
  data.forEach(function (r) {
    if (!closed[String(r[3]).toUpperCase()]) active[r[0]] = true;
  });
  const read = readLeadsCached_();
  read.leads.forEach(function (l) {
    if (l.Batch_ID && active[l.Batch_ID]) ids[l.Lead_ID] = true;
  });
  return ids;
}

/**
 * Bereitet einen Batch mit beliebigem N vor.
 * opts: { owner, count, campaign, industry, tier }
 */
function prepareBatch(opts) {
  const ownerKey = normalizeOwner_(opts.owner);
  const count = Math.max(0, parseInt(opts.count, 10) || 0);

  // Asset-Gate zuerst - vor jeder Auswahl.
  const verified = getVerifiedFlyer_(ownerKey);

  const read = readLeadsCached_();
  const active = activeBatchLeadIds_();
  const stats = {
    requested_count: count, total_pool: 0, eligible_count: 0,
    selected_count: 0, excluded_count: 0, already_contacted_count: 0,
    suppressed_count: 0, optout_count: 0, bounce_count: 0,
    invalid_email_count: 0, no_legal_basis_count: 0, no_release_count: 0,
    in_active_batch_count: 0, shortfall: 0
  };
  const reasons = {};
  const pool = [];

  read.leads.forEach(function (lead) {
    if (normalizeOwner_(lead.Owner) !== ownerKey) return;
    if (opts.industry && String(lead.Industry || '').trim() !== opts.industry) return;
    if (opts.tier && String(lead.Tier || '').trim().toUpperCase()
        !== String(opts.tier).trim().toUpperCase()) return;
    stats.total_pool++;

    if (active[lead.Lead_ID]) {
      stats.in_active_batch_count++; stats.excluded_count++;
      reasons['bereits in aktivem Batch'] =
        (reasons['bereits in aktivem Batch'] || 0) + 1;
      return;
    }
    const res = checkEligibility_(lead);
    if (res.eligible) { stats.eligible_count++; pool.push(lead); return; }

    stats.excluded_count++;
    res.reasons.forEach(function (r) {
      reasons[r] = (reasons[r] || 0) + 1;
      if (r.indexOf('Legal_Basis') === 0) stats.no_legal_basis_count++;
      else if (r.indexOf('Versandfreigabe') === 0) stats.no_release_count++;
      else if (r === 'Suppressed=YES') stats.suppressed_count++;
      else if (r === 'Opt_Out=YES') stats.optout_count++;
      else if (r === 'Hard Bounce') stats.bounce_count++;
      else if (r === 'bereits gesendet') stats.already_contacted_count++;
      else if (r.indexOf('E-Mail') === 0) stats.invalid_email_count++;
    });
  });

  // Deterministisch: Tier A zuerst, dann Lead-ID.
  pool.sort(function (a, b) {
    const ta = String(a.Tier || '').toUpperCase() === 'A' ? 0 : 1;
    const tb = String(b.Tier || '').toUpperCase() === 'A' ? 0 : 1;
    if (ta !== tb) return ta - tb;
    return String(a.Lead_ID).localeCompare(String(b.Lead_ID));
  });

  // Dublettenschutz auf Adressebene: zwei Datensaetze koennen
  // unterschiedliche Lead-IDs und dieselbe E-Mail tragen. Ohne diesen
  // Schritt bekaeme derselbe Empfaenger zwei Mails aus einem Batch.
  const seenEmails = {};
  const deduped = [];
  pool.forEach(function (l) {
    const key = String(l.Email || '').trim().toLowerCase();
    if (seenEmails[key]) {
      stats.excluded_count++;
      stats.eligible_count--;
      reasons['doppelte E-Mail-Adresse'] =
        (reasons['doppelte E-Mail-Adresse'] || 0) + 1;
      return;
    }
    seenEmails[key] = true;
    deduped.push(l);
  });

  const selected = deduped.slice(0, count);
  stats.selected_count = selected.length;
  stats.shortfall = Math.max(0, count - selected.length);

  const batchId = 'HSB-' + Utilities.formatDate(new Date(), CFG.TIMEZONE, 'yyyyMMdd')
    + '-' + ownerKey + '-'
    + ('000' + nextBatchSeq_(ownerKey)).slice(-4);

  if (selected.length) {
    writeBatchToLeads_(read, selected, batchId);
    appendBatchRow_(batchId, ownerKey, opts.campaign || '', 'PREPARED',
                    stats, verified.sha256);
    logActivity_(batchId, 'PREPARED',
                 selected.length + ' Leads reserviert fuer ' + ownerKey);
  }

  return {
    batch_id: batchId,
    owner: ownerKey,
    owner_display: verified.flyer.displayName,
    mailbox: verified.flyer.mailbox,
    asset_file: verified.flyer.fileName,
    asset_sha256: verified.sha256,
    asset_drive_id: verified.flyer.driveId,
    status: selected.length ? 'PREPARED' : 'EMPTY_NO_ELIGIBLE_LEADS',
    stats: stats,
    exclusion_reasons: reasons,
    leads: selected.map(function (l) {
      return { Lead_ID: l.Lead_ID, Company: l.Company, Email: l.Email,
               Contact: l.Contact, Tier: l.Tier };
    })
  };
}

function writeBatchToLeads_(read, selected, batchId) {
  const sh = sheet_(CFG.SHEET_LEADS);
  const ts = nowIso_();
  const uBatch = {}, uPrep = {}, uStat = {};
  selected.forEach(function (l) {
    uBatch[l._row] = batchId;
    uPrep[l._row] = ts;
    uStat[l._row] = 'PREPARED';
  });
  // Drei Bulk-Vorgaenge statt 3xN Einzelaufrufen.
  writeColumnBulk_(sh, read.index[FIELD_MAP.Batch_ID] + 1, uBatch);
  if (read.index['Prepared_At'] !== undefined) {
    writeColumnBulk_(sh, read.index['Prepared_At'] + 1, uPrep);
  }
  if (read.index['Batch_Status'] !== undefined) {
    writeColumnBulk_(sh, read.index['Batch_Status'] + 1, uStat);
  }
  SpreadsheetApp.flush();
  invalidateLeadsCache_();
}

function appendBatchRow_(batchId, owner, campaign, status, stats, sha) {
  const sh = sheet_(CFG.SHEET_BATCHES);
  if (sh.getLastRow() === 0) {
    sh.appendRow(['Batch_ID', 'Owner', 'Campaign', 'Status', 'Requested',
                  'Selected', 'Eligible', 'Excluded', 'Shortfall',
                  'Asset_SHA256', 'Created_At', 'Approved_At', 'Sent_At']);
    sh.getRange(1, 1, 1, 13).setFontWeight('bold').setBackground('#e8eaed');
    sh.setFrozenRows(1);
  }
  sh.appendRow([batchId, owner, campaign, status, stats.requested_count,
                stats.selected_count, stats.eligible_count,
                stats.excluded_count, stats.shortfall, sha, nowIso_(), '', '']);
}

function logActivity_(batchId, type, message) {
  const sh = sheet_(CFG.SHEET_ACTIVITY);
  if (sh.getLastRow() === 0) {
    sh.appendRow(['Timestamp', 'Batch_ID', 'Type', 'Message', 'User']);
    sh.getRange(1, 1, 1, 5).setFontWeight('bold').setBackground('#e8eaed');
    sh.setFrozenRows(1);
  }
  let user = '';
  try { user = Session.getActiveUser().getEmail(); } catch (e) { user = 'unbekannt'; }
  sh.appendRow([nowIso_(), batchId, type, message, user]);
}


/* ==================================================================
   Actions.gs
   ================================================================== */

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
  // Zwei Bulk-Vorgaenge statt 2xN Einzelaufrufen. Das Qualifizieren von
  // 100 Leads ist die erste Aktion nach der Installation - sie darf nicht
  // am 6-Minuten-Limit scheitern.
  writeColumnBulk_(sh, cLegal, uLegal);
  writeColumnBulk_(sh, cFreigabe, uFreigabe);
  SpreadsheetApp.flush();
  invalidateLeadsCache_();
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
 *
 * WICHTIG - warum in Teilpaketen:
 * Der Flyer ist rund 1,5 MB, base64-kodiert etwa 2 MB. Ein einziges ZIP ueber
 * 100 Entwuerfe muesste ~200 MB gleichzeitig im Speicher halten; Apps Script
 * scheitert daran, bevor die Datei fertig ist. Deshalb werden jeweils
 * CHUNK Entwuerfe zu einem ZIP gebuendelt, sofort nach Drive geschrieben und
 * der Speicher wieder freigegeben.
 *
 * `startIndex` erlaubt das Fortsetzen, falls das 6-Minuten-Limit greift.
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


/* ==================================================================
   Code.gs
   ================================================================== */

/**
 * HSB Sales OS - Einstiegspunkte und Menue.
 *
 * Diese Datei enthaelt nur, was die Oberflaeche aufruft.
 * Fachlogik liegt in Engine.gs und Actions.gs.
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('HSB Sales OS')
    .addItem('Sales OS oeffnen', 'showSidebar')
    .addSeparator()
    .addItem('Spalten pruefen / ergaenzen', 'menuEnsureColumns')
    .addItem('Taegliche Erinnerung einrichten', 'menuSetupTrigger')
    .addItem('Flyer-Pruefung (Asset-Gate)', 'menuCheckAssets')
    .addToUi();
}

function showSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('HSB Sales OS')
    .setWidth(420);
  SpreadsheetApp.getUi().showSidebar(html);
}

function menuEnsureColumns() {
  const r = ensureColumns();
  SpreadsheetApp.getUi().alert('Spalten', r.message, SpreadsheetApp.getUi().ButtonSet.OK);
}

function menuSetupTrigger() {
  SpreadsheetApp.getUi().alert('Erinnerung', setupDailyTrigger(),
    SpreadsheetApp.getUi().ButtonSet.OK);
}

function menuCheckAssets() {
  const lines = [];
  Object.keys(FLYERS).forEach(function (k) {
    try {
      const v = getVerifiedFlyer_(k);
      lines.push('OK   ' + k + ': ' + v.flyer.fileName);
    } catch (e) {
      lines.push('FAIL ' + k + ': ' + e.message);
    }
  });
  SpreadsheetApp.getUi().alert('Asset-Gate', lines.join('\n'),
    SpreadsheetApp.getUi().ButtonSet.OK);
}

/* ------------------------------------------ Aufrufe aus der Oberflaeche */

function uiGetDashboard() { return getDashboard(); }

function uiGetFilters() {
  const read = readLeadsCached_();
  const industries = {}, campaigns = {};
  read.leads.forEach(function (l) {
    if (l.Industry) industries[String(l.Industry).trim()] = true;
    if (l.Campaign_ID) campaigns[String(l.Campaign_ID).trim()] = true;
  });
  return {
    industries: Object.keys(industries).sort(),
    campaigns: Object.keys(campaigns).sort()
  };
}

function uiPrepareBatch(opts) {
  try {
    return { ok: true, data: prepareBatch(opts) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiQualify(opts) {
  try {
    return { ok: true, data: qualifyLeads(opts) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiExportEml(batchId, startIndex) {
  try {
    return { ok: true, data: exportBatchAsEmlZip(batchId, startIndex) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiGetDue(owner) {
  try {
    return { ok: true, data: getDueFollowUps(owner) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiSetStatus(leadId, status, days, note) {
  try {
    return { ok: true, data: setLeadStatus(leadId, status, days, note) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiApproveBatch(batchId) {
  try {
    const sh = sheet_(CFG.SHEET_BATCHES);
    const data = sh.getDataRange().getValues();
    for (let r = 1; r < data.length; r++) {
      if (String(data[r][0]) === String(batchId)) {
        sh.getRange(r + 1, 4).setValue('APPROVED');
        sh.getRange(r + 1, 12).setValue(nowIso_());
        logActivity_(batchId, 'APPROVED', 'Batch freigegeben');
        return { ok: true, data: { batch_id: batchId, status: 'APPROVED' } };
      }
    }
    return { ok: false, error: 'Batch nicht gefunden: ' + batchId };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}
