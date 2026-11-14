// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { buildUnsubscribeMailto } from '../src/lib/unsubscribe';
import { describe, it, expect } from 'vitest';
const source=readFileSync('src/pages/abmelden/index.astro','utf8');
describe('unsubscribe request',()=>{
  it('never confirms an unrecorded suppression',()=>{
    expect(source).not.toContain('Erfolgreich abgemeldet');
    expect(source).not.toContain('sofort systemweit hinterlegt');
    expect(source).toContain('mailto:j-cherino@hsb-boden.com');
  });
  it('prepares the original address as an email request without claiming success',()=>{
    document.body.innerHTML=source.slice(source.indexOf('<BaseLayout'));
    expect(source).toContain('buildUnsubscribeMailto');
    const {href,display}=buildUnsubscribeMailto('?email=buyer%40example.org');
    expect(href).toMatch(/^mailto:j-cherino@hsb-boden.com\?/);
    expect(decodeURIComponent(href)).toContain('buyer@example.org');
    expect(display).toContain('buyer@example.org');
    expect(document.querySelector('h1')?.textContent).toContain('Abmeldung anfordern');
  });
});
