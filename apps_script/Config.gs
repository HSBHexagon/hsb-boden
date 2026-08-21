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
