import { describe, it, expect } from 'vitest';
import { buildUnsubscribeMailto } from '../src/lib/unsubscribe';

const DEFAULT_HREF = 'mailto:j-cherino@hsb-boden.com?subject=Abmelden';

describe('buildUnsubscribeMailto', () => {
  it('builds_token_mailto_for_owner', () => {
    const r = buildUnsubscribeMailto('?lid=HSB-20260708-01170&o=JORDI');
    expect(r.href).toBe('mailto:j-post@hsb-boden.com?subject=Abmelden&body=HSB-ABMELDUNG%3A%20HSB-20260708-01170');
    expect(r.display).toBeNull();
  });
  it('maps JOEL, JORDIE and unknown or missing owners', () => {
    const body = '?subject=Abmelden&body=HSB-ABMELDUNG%3A%20HSB-20260708-01170';
    expect(buildUnsubscribeMailto('?lid=HSB-20260708-01170&o=JOEL').href).toBe('mailto:j-cherino@hsb-boden.com' + body);
    expect(buildUnsubscribeMailto('?lid=HSB-20260708-01170&o=JORDIE').href).toBe('mailto:j-post@hsb-boden.com' + body);
    expect(buildUnsubscribeMailto('?lid=HSB-20260708-01170&o=X').href).toBe('mailto:j-cherino@hsb-boden.com' + body);
    expect(buildUnsubscribeMailto('?lid=HSB-20260708-01170').href).toBe('mailto:j-cherino@hsb-boden.com' + body);
  });
  it('keeps the static default for an invalid lid', () => {
    for (const q of ['?lid=bogus', '?lid=HSB-2026-1', '?lid=HSB-20260708-01170%0Ax', '?lid=', '']) {
      expect(buildUnsubscribeMailto(q)).toEqual({ href: DEFAULT_HREF, display: null });
    }
  });
  it('legacy_email_param_still_works', () => {
    const r = buildUnsubscribeMailto('?email=buyer%40example.org');
    expect(r.href).toMatch(/^mailto:j-cherino@hsb-boden.com\?subject=Abmelden&body=/);
    expect(decodeURIComponent(r.href)).toContain('buyer@example.org');
    expect(r.display).toBe('Angeschriebene Adresse: buyer@example.org');
  });
  it('prefers the lid form and never shows an address for it', () => {
    const r = buildUnsubscribeMailto('?lid=HSB-20260708-01170&email=buyer%40example.org');
    expect(r.href).toContain('HSB-ABMELDUNG');
    expect(r.href).not.toContain('buyer');
    expect(r.display).toBeNull();
  });
});
