# WEBHOOK_AUTH_CUTOVER — Pages Function → Google Apps Script

## Ziel

Die bestehende Lead-Pipeline bleibt waehrend der Migration funktionsfaehig und wird anschliessend mit einem separaten Shared Secret abgesichert.

## Implementierter Codepfad

- Ohne `LEAD_WEBHOOK_SECRET` sendet die Pages Function weiterhin den bisherigen Lead-Payload und akzeptiert wie bisher jeden erfolgreichen HTTP-Status des Webhooks.
- Mit `LEAD_WEBHOOK_SECRET` ergaenzt sie das serverseitige Feld `_hsbWebhookToken` und verlangt zusaetzlich die explizite JSON-Antwort `{ "ok": true }`.
- Das Secret wird niemals vom Browser angenommen und niemals an den Browser zurueckgegeben.
- Die URL und der Secret-Wert duerfen nicht in Git, Logs, Screenshots oder Dokumentation eingetragen werden.
- Dadurch bleibt der bestehende Legacy-Pfad bis zur kontrollierten Preview-Umschaltung unveraendert.

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

Nach erfolgreichem CRM-Write muss das Apps Script fuer den spaeteren Secret-Modus diese JSON-Antwort liefern:

```javascript
return jsonResponse({ ok: true });
```

Wichtig:

- Apps-Script-`TextOutput` stellt keinen frei waehlbaren HTTP-Status bereit. Der Cutover darf sich deshalb nicht auf einen erwarteten `401`-Status verlassen.
- Im Legacy-Modus ohne Cloudflare-Secret bleibt der bisherige HTTP-Erfolgsvertrag erhalten.
- Erst im Secret-Modus wertet die Pages Function zusaetzlich das JSON-Feld `ok` aus. `{ ok: false }`, ungueltiges JSON und nicht erfolgreiche HTTP-Statuscodes werden dann als Webhook-Fehler behandelt.
- Das Script Property und das Cloudflare Pages Secret muessen denselben zufaelligen Wert erhalten.
- Das Auth-Feld muss vor dem Mapping ins CRM entfernt werden.
- Bestehende Lead-Felder und die Attributionsspalten duerfen nicht veraendert werden.
- Keine echten Leads fuer den Test verwenden.

## Freigabepflichtige Reihenfolge

1. Apps Script dual-kompatibel deployen; noch kein Script Property und kein Cloudflare-Secret setzen.
2. Mit einem klar markierten Testlead den unveraenderten Legacy-Pfad pruefen und die Testzeile loeschen.
3. Apps Script so verifizieren, dass ein erfolgreicher Test `{ ok: true }` liefert und ein falsches Token `{ ok: false, error: 'unauthorized' }` ohne CRM-Write zurueckgibt.
4. `LEAD_WEBHOOK_SECRET` als Script Property setzen.
5. Dasselbe Secret ausschliesslich in Cloudflare Pages Preview setzen.
6. Preview-End-to-End-Test sowie die Negativtests ausfuehren und Testzeilen loeschen.
7. Erst nach Owner-Freigabe dasselbe Secret in Production setzen und approval-gated deployen.
8. Production-End-to-End-Test ausfuehren und Testzeile loeschen.
9. Alte Apps-Script-Deployments und exponierte Endpoint-Werte erst danach invalidieren beziehungsweise rotieren.

## Negative Tests

- Legacy ohne Secret, bestehende erfolgreiche HTTP-Antwort ohne JSON → Pages Function 200; Payload bleibt unveraendert.
- Fehlendes Token bei aktivem Apps-Script-Secret → Apps Script `{ ok: false, error: 'unauthorized' }`, Pages Function 502, keine CRM-Zeile.
- Falsches Token → Apps Script `{ ok: false, error: 'unauthorized' }`, Pages Function 502, keine CRM-Zeile.
- Gueltiges Token → Apps Script `{ ok: true }`, Pages Function 200, genau eine CRM-Zeile.
- Nicht-JSON-Antwort oder `{ ok: false }` im Secret-Modus → Pages Function 502, kein Erfolgssignal an den Browser.
- Browser-Payload mit eigenem `_hsbWebhookToken` → wird durch die Zod-Validierung nicht als vertrauenswuerdiges Auth-Signal verwendet; die Pages Function setzt ausschliesslich ihren serverseitigen Wert.

## Rollback

- Cloudflare Secret entfernen oder auf die letzte freigegebene Version zurueckrollen; damit gilt wieder der Legacy-HTTP-Vertrag.
- Apps Script voruebergehend wieder dual-kompatibel ohne gesetztes Script Property betreiben.
- Keine URL oder Secret-Werte in den Rollback-Bericht kopieren.

## Gates

- Kein Production-Secret ohne Owner-Freigabe.
- Kein Production-Deploy ohne Workflow-Approval.
- Kein DNS-, Domain-, Mail- oder Outreach-Eingriff in diesem Cutover.
