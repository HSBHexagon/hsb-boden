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
 * opts: { owner, count, campaign, industry, tier, batch_id }
 */
function prepareBatch(opts) {
  opts = opts || {};
  const ownerKey = normalizeOwner_(opts.owner);
  const count = Math.max(0, parseInt(opts.count, 10) || 0);

  // Asset-Gate zuerst - vor jeder Auswahl.
  const verified = getVerifiedFlyer_(ownerKey);

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

    // Idempotenzpruefung bei expliziter Batch_ID
    const explicitBatchId = opts.batch_id ? String(opts.batch_id).trim() : null;
    if (explicitBatchId) {
      const batchesSh = sheet_(CFG.SHEET_BATCHES);
      if (batchesSh.getLastRow() >= 2) {
        const bData = batchesSh.getRange(2, 1, batchesSh.getLastRow() - 1, 13).getValues();
        for (let bi = 0; bi < bData.length; bi++) {
          if (String(bData[bi][0]) === explicitBatchId) {
            const existingLeads = read.leads.filter(function (l) {
              return String(l.Batch_ID) === explicitBatchId;
            });
            existingLeads.sort(function (a, b) {
              const ta = String(a.Tier || '').toUpperCase() === 'A' ? 0 : 1;
              const tb = String(b.Tier || '').toUpperCase() === 'A' ? 0 : 1;
              if (ta !== tb) return ta - tb;
              return String(a.Lead_ID).localeCompare(String(b.Lead_ID));
            });
            return {
              batch_id: explicitBatchId,
              owner: bData[bi][1],
              owner_display: (FLYERS[bData[bi][1]] || {}).displayName || bData[bi][1],
              mailbox: (FLYERS[bData[bi][1]] || {}).mailbox || '',
              asset_file: (FLYERS[bData[bi][1]] || {}).fileName || '',
              asset_sha256: bData[bi][9],
              asset_drive_id: (FLYERS[bData[bi][1]] || {}).driveId || '',
              status: bData[bi][3],
              stats: {
                requested_count: bData[bi][4],
                selected_count: bData[bi][5],
                eligible_count: bData[bi][6],
                excluded_count: bData[bi][7],
                shortfall: bData[bi][8]
              },
              already_processed: true,
              leads: existingLeads.map(function (l) {
                return { Lead_ID: l.Lead_ID, Company: l.Company, Email: l.Email,
                         Contact: l.Contact, Tier: l.Tier };
              })
            };
          }
        }
      }
    }

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

    const batchId = explicitBatchId || ('HSB-' + Utilities.formatDate(new Date(), CFG.TIMEZONE, 'yyyyMMdd')
      + '-' + ownerKey + '-'
      + ('000' + nextBatchSeq_(ownerKey)).slice(-4));

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
  } finally {
    if (lock && hasLock) {
      try { lock.releaseLock(); } catch (_) {}
    }
  }
}

/**
 * Jordi-Schnellstart: eine ausdrueckliche Operator-Aktion gibt exakt 100
 * sichere Kontakte frei und reserviert sie im selben DocumentLock.
 *
 * Der neutrale Auditwert OWNER_APPROVED behauptet weder Opt-in noch
 * Bestandskundenstatus. BLOCKED, Opt-out, Suppression, Hard Bounce, bereits
 * gesendete, ungueltige, doppelte oder aktiv reservierte Kontakte werden nie
 * ueberschrieben. Sind nicht exakt 100 sichere Kontakte verfuegbar, bleibt das
 * Sheet unveraendert und es wird kein Batch angelegt.
 */
function approveAndPrepareJordi100(opts) {
  opts = opts || {};
  const target = 100;
  const ownerKey = 'JORDI';
  const requestId = String(opts.request_id || '').trim();
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(requestId)) {
    throw new Error('Ungueltige request_id fuer Jordi-100.');
  }
  const campaignKey = 'JORDI100:' + requestId;

  // Owner/Flyer-Gate vor jedem moeglichen Sheet-Write.
  const verified = getVerifiedFlyer_(ownerKey);
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
    if (read.index['Legal_Basis'] === undefined
        || read.index[FIELD_MAP.Versandfreigabe] === undefined) {
      throw new Error('Spalten fehlen. Bitte zuerst "Spalten pruefen" ausfuehren.');
    }

    // Derselbe Browser-Aufruf darf auch nach Timeout/Retry keinen zweiten
    // Batch und keine doppelten ZIP-Pakete erzeugen.
    const batchesSh = sheet_(CFG.SHEET_BATCHES);
    if (batchesSh.getLastRow() >= 2) {
      const existingRows = batchesSh.getRange(
        2, 1, batchesSh.getLastRow() - 1, 13).getValues();
      for (let bi = 0; bi < existingRows.length; bi++) {
        const row = existingRows[bi];
        if (String(row[2]) !== campaignKey) continue;
        const existingBatchId = String(row[0]);
        const existingLeads = read.leads.filter(function (lead) {
          return String(lead.Batch_ID) === existingBatchId;
        });
        return {
          batch_id: existingBatchId,
          owner: ownerKey,
          owner_display: verified.flyer.displayName,
          mailbox: verified.flyer.mailbox,
          asset_file: verified.flyer.fileName,
          asset_sha256: verified.sha256,
          asset_drive_id: verified.flyer.driveId,
          status: String(row[3] || 'PREPARED'),
          stats: {
            requested_count: Number(row[4] || target),
            selected_count: Number(row[5] || existingLeads.length),
            eligible_count: Number(row[6] || existingLeads.length),
            excluded_count: Number(row[7] || 0),
            shortfall: Number(row[8] || 0)
          },
          approval: {
            audit_value: 'OWNER_APPROVED',
            already_eligible: existingLeads.length,
            newly_approved: 0,
            safe_available: existingLeads.length
          },
          already_processed: true,
          leads: existingLeads.map(function (lead) {
            return { Lead_ID: lead.Lead_ID, Company: lead.Company,
                     Email: lead.Email, Contact: lead.Contact, Tier: lead.Tier };
          })
        };
      }
    }

    const active = activeBatchLeadIds_();
    const candidates = [];
    let totalPool = 0;
    let blockedCount = 0;

    read.leads.forEach(function (lead) {
      if (normalizeOwner_(lead.Owner) !== ownerKey) return;
      totalPool++;
      if (active[lead.Lead_ID]) { blockedCount++; return; }

      const rawLegal = String(lead.Legal_Basis || '').trim().toUpperCase();
      if (rawLegal === 'BLOCKED'
          || (rawLegal && LEGAL_BASIS_ALL.indexOf(rawLegal) === -1)) {
        blockedCount++;
        return;
      }

      const eligibility = checkEligibility_(lead);
      const immutableReasons = eligibility.reasons.filter(function (reason) {
        return reason.indexOf('Legal_Basis=') !== 0
          && reason.indexOf('Versandfreigabe=') !== 0;
      });
      if (immutableReasons.length) { blockedCount++; return; }
      candidates.push({ lead: lead, eligible: eligibility.eligible });
    });

    // Gleiche Prioritaet wie die normale Batch-Engine: Tier A, dann Lead-ID.
    candidates.sort(function (a, b) {
      const ta = String(a.lead.Tier || '').toUpperCase() === 'A' ? 0 : 1;
      const tb = String(b.lead.Tier || '').toUpperCase() === 'A' ? 0 : 1;
      if (ta !== tb) return ta - tb;
      return String(a.lead.Lead_ID).localeCompare(String(b.lead.Lead_ID));
    });

    const seenEmails = {};
    const uniqueCandidates = [];
    candidates.forEach(function (candidate) {
      const emailKey = String(candidate.lead.Email || '').trim().toLowerCase();
      if (seenEmails[emailKey]) { blockedCount++; return; }
      seenEmails[emailKey] = true;
      uniqueCandidates.push(candidate);
    });

    if (uniqueCandidates.length < target) {
      return {
        batch_id: '', owner: ownerKey, owner_display: verified.flyer.displayName,
        mailbox: verified.flyer.mailbox, asset_file: verified.flyer.fileName,
        asset_sha256: verified.sha256, asset_drive_id: verified.flyer.driveId,
        status: 'BLOCKED_EXACT_100', already_processed: false,
        stats: {
          requested_count: target, selected_count: 0,
          eligible_count: uniqueCandidates.length,
          excluded_count: Math.max(blockedCount, totalPool - uniqueCandidates.length),
          shortfall: target - uniqueCandidates.length
        },
        approval: {
          audit_value: 'OWNER_APPROVED', already_eligible: 0,
          newly_approved: 0, safe_available: uniqueCandidates.length
        },
        leads: []
      };
    }

    const chosen = uniqueCandidates.slice(0, target);
    const selected = chosen.map(function (candidate) { return candidate.lead; });
    const sh = sheet_(CFG.SHEET_LEADS);
    const legalUpdates = {};
    const releaseUpdates = {};
    const approvedAtUpdates = {};
    const approvedAt = nowIso_();
    let alreadyEligible = 0;
    let newlyApproved = 0;

    chosen.forEach(function (candidate) {
      const lead = candidate.lead;
      if (candidate.eligible) {
        alreadyEligible++;
        return;
      }
      newlyApproved++;
      const rawLegal = String(lead.Legal_Basis || '').trim().toUpperCase();
      if (LEGAL_BASIS_SENDABLE.indexOf(rawLegal) === -1) {
        const optIn = String(lead.Opt_In || '').trim().toLowerCase();
        legalUpdates[lead._row] = (optIn === 'yes' || optIn === 'ja'
          || optIn === 'true' || optIn === 'opt_in') ? 'OPT_IN' : 'OWNER_APPROVED';
      }
      if (!isTrue_(lead.Versandfreigabe)) releaseUpdates[lead._row] = 'yes';
      if (read.index['Approved_At'] !== undefined) {
        approvedAtUpdates[lead._row] = approvedAt;
      }
    });

    if (Object.keys(legalUpdates).length) {
      writeColumnBulk_(sh, read.index['Legal_Basis'] + 1, legalUpdates);
    }
    if (Object.keys(releaseUpdates).length) {
      writeColumnBulk_(sh, read.index[FIELD_MAP.Versandfreigabe] + 1,
                       releaseUpdates);
    }
    if (Object.keys(approvedAtUpdates).length) {
      writeColumnBulk_(sh, read.index['Approved_At'] + 1, approvedAtUpdates);
    }
    SpreadsheetApp.flush();
    invalidateLeadsCache_();

    const batchId = 'HSB-' + Utilities.formatDate(
      new Date(), CFG.TIMEZONE, 'yyyyMMdd') + '-JORDI-'
      + ('000' + nextBatchSeq_(ownerKey)).slice(-4);
    const stats = {
      requested_count: target,
      total_pool: totalPool,
      eligible_count: uniqueCandidates.length,
      selected_count: target,
      excluded_count: Math.max(blockedCount, totalPool - uniqueCandidates.length),
      shortfall: 0
    };

    writeBatchToLeads_(read, selected, batchId);
    appendBatchRow_(batchId, ownerKey, campaignKey, 'PREPARED',
                    stats, verified.sha256);
    logActivity_(batchId, 'OWNER_APPROVED',
      'Jordi-100: ' + newlyApproved + ' neu freigegeben, '
      + alreadyEligible + ' bereits sendefaehig, exakt 100 reserviert');
    logActivity_(batchId, 'PREPARED',
      '100 Leads atomar reserviert fuer JORDI; kein automatischer Versand');

    return {
      batch_id: batchId,
      owner: ownerKey,
      owner_display: verified.flyer.displayName,
      mailbox: verified.flyer.mailbox,
      asset_file: verified.flyer.fileName,
      asset_sha256: verified.sha256,
      asset_drive_id: verified.flyer.driveId,
      status: 'PREPARED',
      stats: stats,
      approval: {
        audit_value: 'OWNER_APPROVED',
        already_eligible: alreadyEligible,
        newly_approved: newlyApproved,
        safe_available: uniqueCandidates.length
      },
      already_processed: false,
      leads: selected.map(function (lead) {
        return { Lead_ID: lead.Lead_ID, Company: lead.Company, Email: lead.Email,
                 Contact: lead.Contact, Tier: lead.Tier };
      })
    };
  } finally {
    if (lock && hasLock) {
      try { lock.releaseLock(); } catch (_) {}
    }
  }
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
