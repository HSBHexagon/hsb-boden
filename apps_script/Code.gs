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
  const read = readLeads_();
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

function uiExportEml(batchId) {
  try {
    return { ok: true, data: exportBatchAsEmlZip(batchId) };
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
