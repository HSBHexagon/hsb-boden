// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
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
    const start=source.indexOf('<script is:inline>')+'<script is:inline>'.length;
    const end=source.indexOf('</script>',start);
    const code=source.slice(start,end);
    const location={search:'?email=buyer%40example.org'};
    new Function('window','document','URLSearchParams',code)({location},document,URLSearchParams);
    const href=document.getElementById('unsubscribe-mail')?.getAttribute('href')||'';
    expect(href).toMatch(/^mailto:j-cherino@hsb-boden.com\?/);
    expect(decodeURIComponent(href)).toContain('buyer@example.org');
    expect(document.querySelector('h1')?.textContent).toContain('Abmeldung anfordern');
  });
});
