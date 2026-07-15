# WEBHOOK_AUTH_CUTOVER — Pages Function → Google Apps Script

## Ziel

Die bestehende Lead-Pipeline bleibt waehrend der Migration funktionsfaehig und wird anschliessend mit einem separaten Shared Secret abgesichert.

## Implementierter Codepfad

- Ohne `LEAD_WEBHOOK_SECRET` sendet die Pages Function weiterhin den bisherigen Lead-Payload.
- Mit `LEAD_WEBHOOK_SECRET` ergaenzt sie das serverseitige Feld `_hsbWebhookToken`.
- Das Secret wird niemals vom Browser angenommen und niemals an den Browser zurueckgegeben.
- Die URL und der Secret-Wert duerfen nicht in Git, Logs, Screenshots oder Dokumentation eingetragen werden.
- Die Pages Function akzeptiert den Webhook nur, wenn die JSON-Antwort explizit `{ "ok": true }` enthaelt.

## Apps-Script-Zielpruefung

Vor dem Setzen des Cloudflare-Secrets muss das Apps Script dual-kompatibel pruefen:

```javascript
const expected = PropertiesService.getScriptProperties().getProperty('LEAD_WEBHOOK_SECRET');
const received = String(payload._hsbWebhookToken || '');

if (expected && received !== expected) {
  return jsonResponse({ ok: false, error: 'unauthorized' });
}

delete payload._hsbWebhookToken;
```

Nach erfolgreichem CRM-Write muss das Apps Script weiterhin eine JSON-Antwort mit mindestens diesem Vertrag liefern:

```javascript
return jsonResponse({ ok: true });
```

Wichtig:

- Apps-Script-`TextOutput` stellt keinen frei waehlbaren HTTP-Status bereit. Der Cutover darf sich deshalb nicht auf einen erwarteten `401`-Status verlassen.
- Die Pages Function wertet sowohl den HTTP-Status als auch das JSON-Feld `ok` aus. `{ ok: false }`, ungueltiges JSON und nicht erfolgreiche HTTP-Statuscodes werden als Webhook-Fehler behandelt.
- Das Script Property und das Cloudflare Pages Secret muessen denselben zufaelligen Wert erhalten.
- Das Auth-Feld muss vor dem Mapping ins CRM entfernt werden.
- Bestehende Lead-Felder und die Attributionsspalten duerfen nicht veraendert werden.
- Keine echten Leads fuer den Test verwenden.

## Freigabepflichtige Reihenfolge

1. Apps Script dual-kompatibel deployen; noch keinen Pflicht-Secret-Modus erzwingen.
2. Mit einem klar markierten Testlead den Legacy-Pfad pruefen, `{ ok: true }` bestaetigen und die Testzeile loeschen.
3. `LEAD_WEBHOOK_SECRET` als Script Property setzen.
4. Dasselbe Secret in Cloudflare Pages Preview setzen.
5. Preview-End-to-End-Test sowie die Negativtests ausfuehren und Testzeilen loeschen.
6. Erst nach Owner-Freigabe dasselbe Secret in Production setzen und approval-gated deployen.
7. Production-End-to-End-Test ausfuehren und Testzeile loeschen.
8. Alte Apps-Script-Deployments und exponierte Endpoint-Werte erst danach invalidieren beziehungsweise rotieren.

## Negative Tests

- Fehlendes Token bei aktivem Apps-Script-Secret → Apps Script `{ ok: false, error: 'unauthorized' }`, Pages Function 502, keine CRM-Zeile.
- Falsches Token → Apps Script `{ ok: false, error: 'unauthorized' }`, Pages Function 502, keine CRM-Zeile.
- Gueltiges Token → Apps Script `{ ok: true }`, Pages Function 200, genau eine CRM-Zeile.
- Nicht-JSON-Antwort oder `{ ok: false }` vom Webhook → Pages Function 502, kein Erfolgssignal an den Browser.
- Browser-Payload mit eigenem `_hsbWebhookToken` → wird durch die Zod-Validierung nicht als vertrauenswuerdiges Auth-Signal verwendet; die Pages Function setzt ausschliesslich ihren serverseitigen Wert.

## Rollback

- Cloudflare Secret entfernen oder auf die letzte freigegebene Version zurueckrollen.
- Apps Script voruebergehend wieder dual-kompatibel ohne gesetztes Script Property betreiben.
- Keine URL oder Secret-Werte in den Rollback-Bericht kopieren.

## Gates

- Kein Production-Secret ohne Owner-Freigabe.
- Kein Production-Deploy ohne Workflow-Approval.
- Kein DNS-, Domain-, Mail- oder Outreach-Eingriff in diesem Cutover.
