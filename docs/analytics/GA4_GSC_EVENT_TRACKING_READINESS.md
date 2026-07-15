# GA4_GSC_EVENT_TRACKING_READINESS — HSB-Boden / HEXAFLOOR

Status: `ga4-basic-consent-cutover-in-pr; gsc-owner-gates-open`
Stand: 2026-07-15

Diese Datei unterscheidet Quellcode, beobachtete UI-Evidenz und Owner-Schritte.
Sie aktiviert weder GA4 noch Search Console und legt keine Properties, Events oder
Verknüpfungen in Google an.

## Implementierung im Review

Die Basic-Consent-Implementierung liegt auf dem gestapelten Review-Branch und ist
erst nach Merge und dem manuellen Produktions-Deploy wirksam.

| Schutz | Implementierung |
| --- | --- |
| Kein Google-Request vor Einwilligung | `src/lib/analytics.ts` fügt `gtag.js` erst bei `analytics: true` hinzu. |
| Einmalige Initialisierung | Gespeicherte Einwilligung führt zu genau einem `config`-Aufruf mit einem Pageview. |
| Widerruf im aktuellen Tab | Das Consent-Ereignis aktualisiert GA4 auf `denied`; ohne neue Einwilligung werden keine eigenen Events transportiert. |
| Nur nicht-personenbezogene Felder | `src/lib/tracking.ts` erlaubt ausschließlich feste Tokens, lokale Pfade und Booleans. Name, E-Mail, Telefon, Freitext und UTM-Rohwerte sind ausgeschlossen. |
| Sicherer Lead-Redirect | Ein erfolgreicher Submit erzeugt `generate_lead` und wartet höchstens kurz auf den Callback, bevor zur Danke-Seite navigiert wird. |
| Zielbindung | Eigene Events enthalten `send_to` für die konfigurierte GA4-Destination. |

## Implementierte Events

| GA4-Event | Auslöser | Zulässige Daten |
| --- | --- | --- |
| `lead_form_start` | erste Formularinteraktion | nur freigegebene, nicht-personenbezogene Metadaten |
| `generate_lead` | `/api/lead` meldet Erfolg | festes `method: contact_form`; keine Lead-Daten |

Alle weiteren früher beschriebenen Analytics-Events sind **nicht** Teil dieses
Cutovers. Neue Felder oder Events benötigen eine Datenschutz- und Code-Review.

## GSC — belegter und offener Stand

| Bereich | Stand |
| --- | --- |
| Technische Grundlage | `robots.txt`, Sitemap, Canonicals und Hreflang werden aus dem Projekt gebaut. |
| UI-Evidenz | Für die URL-Präfix-Property `https://www.hsb-boden.de/` war interaktiver Zugriff sichtbar; die im Screenshot gezeigten Indexierungszahlen sind zeitabhängig und keine Live-Garantie. |
| API/Automatisierung | Nicht als freigeschaltet belegt; keine GSC-Mutation aus diesem Branch. |
| Property-/GA4-Verknüpfung | Nicht als korrekt belegt und daher offen. |

## Owner-Gates nach Merge und Preview

1. Inkognito prüfen: vor Statistik-Einwilligung darf kein Request an Google Tag
   Manager entstehen; nach Einwilligung darf genau ein GA4-Config/Pageview entstehen.
2. Einen ausschließlich internen, erfolgreichen Preview-Testlead absenden und
   `generate_lead` in GA4 DebugView prüfen. Keine echten Kontaktdaten verwenden.
3. Erst nach dieser Prüfung `generate_lead` in der richtigen GA4-Property als Key
   Event markieren und etwaige zusätzliche Google-Destinations separat prüfen.
4. In Search Console die kanonische Property bestätigen, Sitemap-Status sowie die
   aktuellen Gründe nicht indexierter URLs prüfen und erst danach GA4/GSC verknüpfen.

## Verboten

- Keine Analytics-Events mit personenbezogenen Lead- oder URL-Rohdaten.
- Keine externe Google-Tag-Anfrage vor einer aktiven Statistik-Einwilligung.
- Keine automatische Property-Erstellung, GSC-Validierung oder Verknüpfung ohne
  identifizierte Owner-Property.
