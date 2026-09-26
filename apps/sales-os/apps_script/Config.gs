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
    displayName: 'Jordie Post',
    mailbox: 'j-post@hsb-boden.com',
    fileName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
    // Name im Anhang beim Empfaenger. Getrennt von fileName, weil dieser an
    // Hash-Gate und Drive-Ablage haengt und nicht umbenannt werden darf.
    attachmentName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
    // Persoenliche Mobilnummer fuer die Signatur, Quelle ist der kanonische
    // Flyer. Das Impressum traegt nur die zentrale Durchwahl.
    mobile: '0170 2340904',
    driveId: '1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV',
    sha256: 'a11876f02b54421bcafd9a6b8ec6f62d748e383b26fcadc8bbe834ee7ffbc4ce'
  },
  JOEL: {
    key: 'JOEL',
    displayName: 'Joel Cherino Diaz',
    mailbox: 'j-cherino@hsb-boden.com',
    fileName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
    attachmentName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf',
    mobile: '0151 21886891',
    driveId: '16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS',
    sha256: '6ac5ed1112c88768ac56950faab8802ceaa2817913f35a7b95e73ee79c3431d8'
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

// OWNER_APPROVED ist eine neutrale, protokollierte Operator-Freigabe. Der Wert
// behauptet weder Opt-in noch Bestandskundenstatus und darf nur durch den
// atomaren Jordi-100-Ablauf gesetzt werden.
const LEGAL_BASIS_SENDABLE = ['OPT_IN', 'EXISTING_CUSTOMER_7_3', 'OWNER_APPROVED'];
const LEGAL_BASIS_ALL = [
  'OPT_IN', 'EXISTING_CUSTOMER_7_3', 'OWNER_APPROVED', 'BLOCKED', 'UNKNOWN'
];

const FREEMAIL_DOMAINS = [
  'gmail.com', 'googlemail.com', 'outlook.com', 'outlook.de', 'hotmail.com', 'hotmail.de',
  'live.com', 'live.de', 'web.de', 'gmx.de', 'gmx.net', 'gmx.at', 'gmx.ch', 't-online.de',
  'yahoo.com', 'yahoo.de', 'icloud.com', 'me.com', 'freenet.de', 'aol.com', 'posteo.de',
  'mail.de', 'protonmail.com', 'proton.me'
];

const FREEMAIL_NAMES = [
  't-online', 't online', 'tonline', 'gmail', 'googlemail', 'gmx', 'web.de', 'web de', 'web',
  'yahoo', 'outlook', 'hotmail', 'live', 'aol', 'freenet', 'posteo', 'mail.de', 'protonmail',
  'proton', 'icloud'
];

function sanitizeCompanyName_(rawName, email) {
  if (!rawName) return 'Ihr Unternehmen';
  var name = String(rawName).trim();
  var norm = name.toLowerCase();
  if (!norm || norm === 'none' || norm === 'nan' || norm === 'null' || norm === 'undefined' || norm === '-' || norm === '.' || norm === '/') {
    return 'Ihr Unternehmen';
  }
  var normClean = norm.replace(/-/g, ' ').replace(/\./g, ' ').trim();
  for (var i = 0; i < FREEMAIL_NAMES.length; i++) {
    var fn = FREEMAIL_NAMES[i];
    if (norm === fn || normClean === fn.replace(/-/g, ' ').replace(/\./g, ' ')) {
      return 'Ihr Unternehmen';
    }
  }
  if (email && email.indexOf('@') >= 0) {
    var parts = email.split('@');
    var domain = parts[parts.length - 1].trim().toLowerCase();
    if (FREEMAIL_DOMAINS.indexOf(domain) >= 0) {
      var domainBase = domain.split('.')[0];
      if (normClean.indexOf(domainBase) >= 0) {
        return 'Ihr Unternehmen';
      }
    }
  }
  return name;
}

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
