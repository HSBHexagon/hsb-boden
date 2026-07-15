# Lead-Webhook: authentifizierter Zero-Downtime-Cutover

Status: `code-ready, external owner gates open` | Stand: 2026-07-15

## Ziel und Grenze

Die Pages Function unterstützt während der Migration zwei Modi:

- `LEAD_WEBHOOK_CONFIG` vorhanden: ausschließlich der authentifizierte JSON-Umschlag
  wird an eine strikt validierte Google-Apps-Script-URL gesendet.
- `LEAD_WEBHOOK_CONFIG` nicht vorhanden: vorübergehender Legacy-Fallback über
  `LEAD_WEBHOOK_URL` mit dem bisherigen Lead-JSON.
- `LEAD_WEBHOOK_CONFIG` vorhanden, aber ungültig: fail closed (`502`), niemals Fallback.

`LEAD_WEBHOOK_CONFIG` ist genau ein verschlüsseltes Pages-Secret mit diesem Schema:

```json
{
  "url": "https://script.google.com/macros/s/REPLACE_WITH_NEW_DEPLOYMENT_ID/exec",
  "token": "REPLACE_WITH_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS"
}
```

Keine echten Werte in Git, Shell-History, Tickets, Screenshots oder Logs schreiben.
Die URL allein ist keine Authentifizierung.

## Apps-Script-Adapter

1. In den Script Properties einen zufälligen Wert unter
   `HSB_WEBHOOK_AUTH_TOKEN` speichern.
2. Folgende Hilfsfunktionen in die neue Script-Version übernehmen.
3. `readAuthenticatedLead_(e)` muss am Anfang von `doPost(e)` laufen, **bevor**
   irgendein Sheet geöffnet oder beschrieben wird.
4. Der Erfolgsweg muss `{ok:true}` zurückgeben. Ablehnungen geben `{ok:false,...}`
   zurück; Apps Script kann dabei weiterhin HTTP 200 liefern, weshalb die Pages
   Function zusätzlich den JSON-Acknowledge prüft.

```javascript
function jsonResponse_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function constantTimeEquals_(left, right) {
  left = (typeof left === "string") ? left : "";
  right = (typeof right === "string") ? right : "";

  var mismatch = left.length ^ right.length;
  for (var i = 0; i < right.length; i++) {
    var leftCode = (i < left.length) ? left.charCodeAt(i) : 0;
    mismatch |= leftCode ^ right.charCodeAt(i);
  }
  return mismatch === 0;
}

function readAuthenticatedLead_(e) {
  var expected = PropertiesService.getScriptProperties()
    .getProperty("HSB_WEBHOOK_AUTH_TOKEN");
  if (!expected || expected.length < 32 || expected.length > 512) {
    throw new Error("server_misconfigured");
  }

  var raw = e && e.postData && e.postData.contents;
  var envelope = raw ? JSON.parse(raw) : null;
  var supplied = envelope && envelope.authToken;
  var authorized = envelope &&
    envelope.version === 1 &&
    envelope.lead &&
    typeof envelope.lead === "object" &&
    typeof supplied === "string" &&
    supplied.length <= 512 &&
    constantTimeEquals_(supplied, expected);

  if (!authorized) throw new Error("unauthorized");
  return envelope.lead;
}

function doPost(e) {
  var data;
  try {
    data = readAuthenticatedLead_(e);
  } catch (error) {
    var authCode = error && error.message === "server_misconfigured"
      ? "server_misconfigured"
      : "unauthorized";
    return jsonResponse_({ ok: false, error: authCode });
  }

  try {
    // Ab hier: bestehende serverseitige Feldvalidierung, Formula-Injection-Guards
    // und genau ein Sheet-Write. Vor dieser Stelle darf kein Write stattfinden.
    // ... bestehende Intake-Logik mit `data` ...

    return jsonResponse_({ ok: true });
  } catch (processingError) {
    console.error(JSON.stringify({
      ts: new Date().toISOString(),
      code: "processing_failed"
    }));
    return jsonResponse_({ ok: false, error: "processing_failed" });
  }
}
```

Der Ausschnitt ersetzt nicht die bestehende Feldvalidierung oder Sheet-Logik. Vor dem
Deployment muss der Operator den Platzhalterblock mit dem live geprüften Bestandscode
zusammenführen. Token, vollständiger Request und personenbezogene Daten dürfen nicht
geloggt werden.

## Verbindliche Reihenfolge

1. Bestehenden Apps-Script-Stand und Deployment-Zuordnung sichern, ohne Secret-Werte
   zu exportieren. Legacy bleibt aktiv.
2. Neue Script-Version mit Auth-Adapter, Attribution-Mapping und `{ok:true}`-Acknowledge
   erstellen. Als **neues** Web-App-Deployment veröffentlichen; Legacy nicht ändern.
3. Den dual-kompatiblen Pages-Code als PR-Preview deployen. Der Preview-Workflow
   aktiviert dazu nur die Formular-UI; der Endpoint akzeptiert ausschließlich
   `https://*.hsb-boden.pages.dev` für dieses Projekt. Der Unit-Test muss belegen,
   dass eine fehlende neue Config den vorhandenen Legacy-Pfad unverändert nutzt. Hat
   Preview keines der beiden Bindings, ist dort `502` das korrekte fail-closed Ergebnis.
4. Im Cloudflare-Dashboard unter **Workers & Pages → hsb-boden → Settings → Variables
   and Secrets** `LEAD_WEBHOOK_CONFIG` zuerst nur für **Preview** als verschlüsseltes
   Secret setzen. Preview nutzt ein isoliertes Testziel und einen eigenen Testtoken;
   Same-Repo-PR-Code kann Preview-Bindings lesen. Danach eine neue PR-Preview aus
   demselben geprüften Commit deployen.
5. Preview negativ prüfen: zuerst absichtlich falschen Preview-Token setzen, neu
   deployen und `502` ohne Sheet-Zeile bestätigen. Dann den korrekten **Preview**-Token
   setzen, erneut deployen und genau einen klar markierten Test-Lead über `/api/lead`
   senden. Testzeile prüfen und entfernen. Keine direkte POST-Anfrage an Apps Script.
6. Erst nach grünem Preview einen **anderen, ausschließlich für Production erzeugten**
   Token als Script Property und im Production-`LEAD_WEBHOOK_CONFIG` setzen. Falls kein
   isoliertes Preview-Script verfügbar ist, den Testtoken jetzt rotieren; danach muss
   das alte Preview-Binding absichtlich ungültig sein. Anschließend denselben geprüften
   Commit ausschließlich über `deploy-production.yml` manuell deployen.
   Pages-Secrets müssen vor dem Deployment gesetzt sein; ein bestehendes Deployment
   übernimmt den neuen Binding-Wert nicht rückwirkend.
7. Binding-Namen ohne Werte prüfen, dann genau einen owner-gated Production-Test über
   das Website-Formular ausführen und die markierte Testzeile entfernen.
8. `LEAD_WEBHOOK_URL` erst nach erfolgreicher Production-Prüfung entfernen. Danach das
   Legacy-Deployment und alle weiteren öffentlich bekannten Alt-Deployments
   invalidieren. Dies ist der letzte Schritt, nicht der erste.

Wrangler 4.106.0 bietet für `pages secret put` keinen eindeutigen Preview-/Production-
Schalter. Für diesen getrennten Cutover ist daher das offizielle Pages-Dashboard der
kanonische Weg. Secret-Werte niemals als CLI-Argument oder über `echo` übergeben.

## Abnahmekriterien

- Ungültige/zusätzliche Config-Felder, unsichere Hosts, Query/Fragment, schwache Tokens
  und fehlende `{ok:true}`-Antworten schlagen geschlossen fehl.
- Preview und Production verwenden nach ihrem jeweiligen Redeploy den neuen
  authentifizierten Umschlag.
- Kein realer Token und keine reale vollständige Ziel-URL erscheint in Git oder Logs.
- Legacy-Secret und Alt-Deployments sind erst nach nachgewiesener Zustellung entfernt.
- Die entfernbare Testzeile ist geprüft und anschließend gelöscht; echte Leads werden
  nicht als Testdaten verwendet.
