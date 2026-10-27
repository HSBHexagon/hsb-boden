// Abmeldelink: URL-Parameter -> mailto. Die Seite sperrt nichts; sie bereitet nur die E-Mail vor.
// Token-Form (?lid=<Lead-ID>&o=<JOEL|JORDI>) enthaelt keine Adresse; das Token entspricht
// engine/outbound_safety.py:add_list_unsubscribe.
const DEFAULT_MAILBOX = 'j-cherino@hsb-boden.com';
const MAILBOX_BY_OWNER: Record<string, string> = {
  JOEL: 'j-cherino@hsb-boden.com',
  JORDI: 'j-post@hsb-boden.com',
  JORDIE: 'j-post@hsb-boden.com',
};
const LEAD_ID = /^HSB-\d{8}-\d+$/;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export interface UnsubscribeMailto {
  href: string;
  display: string | null;
}

export function buildUnsubscribeMailto(search: string): UnsubscribeMailto {
  const fallback: UnsubscribeMailto = { href: `mailto:${DEFAULT_MAILBOX}?subject=Abmelden`, display: null };
  const params = new URLSearchParams(search);

  const lid = (params.get('lid') || '').trim();
  if (LEAD_ID.test(lid)) {
    const mailbox = MAILBOX_BY_OWNER[(params.get('o') || '').trim().toUpperCase()] || DEFAULT_MAILBOX;
    return {
      href: `mailto:${mailbox}?subject=Abmelden&body=${encodeURIComponent(`HSB-ABMELDUNG: ${lid}`)}`,
      display: null,
    };
  }

  const email = (params.get('email') || '').trim();
  if (email.length <= 254 && EMAIL.test(email)) {
    const body = `Bitte melden Sie die E-Mail-Adresse ${email} von weiteren E-Mails ab.\nVielen Dank.`;
    return {
      href: `mailto:${DEFAULT_MAILBOX}?subject=Abmelden&body=${encodeURIComponent(body)}`,
      display: `Angeschriebene Adresse: ${email}`,
    };
  }
  return fallback;
}
