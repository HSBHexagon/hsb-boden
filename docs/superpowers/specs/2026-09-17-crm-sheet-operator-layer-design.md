# HSB CRM (Google Sheet „Sales OS"): Operator-Schicht, Datenmodell-Reparatur, Postfach-Automatik — Design

Datum: 2026-09-17 · Owner-Entscheidungen dieser Session: Sheet = System of Record (Airtable nicht), kostenfrei, Priorität visuelle/effiziente Bedienung, Abmeldung per Antwort „Abmelden", beide Postfächer (Joel, Jordi).

## Belegte Ausgangslage (Sheets-API-Analyse + Power-Automate-Inventar, 2026-09-17)

- Sheet `HSB CRM MASTER 6424 – Sales OS – 2026-08-21`, Locale de_DE, Europe/Berlin, 34 Tabs, **5 sichtbar** (`README`, `VERSAND`, `ALL_LEADS`, `DASHBOARD`, `BATCHES`). `JOEL`/`JORDI`/`READY_CANDIDATES` sind `QUERY`-Sichten auf `ALL_LEADS` (keine Kopien). Keine benannten Bereiche, keine geschützten Bereiche, keine Filteransichten; `ALL_LEADS`: 14 bedingte Formate, Basisfilter, 1 fixierte Zeile, **alle 56 Spalten `WRAP`**, Breiten 52–183 px → Zeilen wachsen mit Freitext (Ursache des Screenshots).
- `ALL_LEADS` 6.424 Zeilen: Operator-Felder tot (`Status`=neu ×6.424, `Nächste Aktion`=prüfen ×6.424, `Opt-in-`/`Opt-out-Status`=unknown ×6.424, `Follow-up-Datum`/`Interesse`/`Projektart`/`Sanierungsfenster`/`Segment`/`Outlook_Message_ID`/`Last_Reply_At`/`Bounce_Status` leer). Maschinenfelder aktiv: `Send_Status` not_sent 4.054 / drafted 2.125 / prepared 86 / sent 159; `Draft_ID` 2.271; `Batch_ID` 23 distinct; `Reply_Status` bounced 20, auto_reply_ooo 4; `Suppressed=yes` 20; `Versandfreigabe=yes` 694; `Legal_Basis` UNKNOWN 4.052 / no 2.000 / EXISTING_CUSTOMER_7_3 251 / OWNER_APPROVED 101 / yes 20 (gemischtes Vokabular); `Send_Datum` in zwei Formaten. Konsistenzprüfungen (SENT↔Datum, Draft↔Status, Opt-out↔Suppressed↔Freigabe): 0 Widersprüche.
- Power Automate (Tenant HSB-Boden.de): `HSB Sales OS Draft Adapter` (Joel, Started, HTTP→DraftEmail, liefert `draftId`/`internetMessageId`/`conversationId`), `… (Jordi)` **Stopped**, Outlook-Connection nur `j-cherino`; Google-Tabellen-/Drive-Connections auf Privatkonto `cherinodiaz@outlook.com`. **Kein Flow mit Posteingangs-/Gesendet-Trigger** → keine automatische Statusfortschreibung, keine Abmeldeerfassung.
- Apps Script `deploy/HSB_GraphAdapter.js` enthält Klassifikation (Bounce/OOO/Opt-out per Stichwort) und Sheet-Writeback, läuft nur manuell.

## Ziele

1. `ALL_LEADS` ist auf einen Blick lesbar: eine Zeile = eine Zeile, farbige Zustände, Maschinenspalten eingeklappt, Sichten je Person.
2. Ein sichtbarer Pipeline-Zustand je Lead, berechnet aus bestehenden Spalten (kein neuer Speicher).
3. Statuswechsel **Versendet / Antwort / Abmeldung / Bounce** entstehen automatisch aus beiden Postfächern, mit Beleg in `INBOUND_EVENTS`; Abmeldung sperrt dauerhaft.
4. Kein Header wird umbenannt oder gelöscht (Spaltenvertrag Engine/Apps Script). Neue Spalten nur am Ende.
5. Kostenfrei; kein zweiter Datenspeicher; kein automatischer Versand (Zero-Send bleibt).

## Nicht-Ziele

Migration in ein Markt-CRM; Abmelde-Link (Ausbaustufe); AppSheet-App (Ausbaustufe); Änderung der Versandfreigabe-Logik oder der Rechtsgrundlagen-Entscheidung (bleibt menschlich).

## Architektur

```
Outlook (j-cherino, j-post)
  └─ Power Automate: Trigger "Neue E-Mail (V3)" Ordner=Gesendete Elemente  ─┐
  └─ Power Automate: Trigger "Neue E-Mail (V3)" Ordner=Posteingang        ─┤ HTTP POST (JSON, Shared-Secret)
                                                                           ▼
                                     Apps Script Web-App "HSB Sales OS Inbound" (Erweiterung HSB_GraphAdapter.js)
                                       - Zuordnung: conversationId → Conversation_ID, sonst Empfänger/Absender-E-Mail → E-Mail
                                       - Klassifikation: sent | reply | opt_out | bounce | auto_reply
                                       - Gates: nie Versandfreigabe=yes setzen; Opt-out ist idempotent und unumkehrbar per Script
                                       - Writeback ALL_LEADS (nur Zielspalten) + Append INBOUND_EVENTS (dedupliziert über Internet_Message_ID)
                                                                           ▼
                                     Google Sheet ALL_LEADS (System of Record) → QUERY-Sichten, Pipeline-Spalte, Filteransichten, Dashboard
```

## Komponenten

### A. Sichtbarkeit (Sheets-API, idempotentes Skript `engine/apply_sheet_formatting.py`)
- `wrapStrategy=CLIP` auf A:BE; Zeilenhöhe Standard.
- Spaltengruppe AD:BD (Maschinenfelder) angelegt und eingeklappt; Spalten S:W (leere Zukunftsfelder) ausgeblendet (nicht gelöscht).
- Fixiert: 1 Zeile, 2 Spalten (`Lead-ID`, `Firma`). Breiten: Firma 220, Ansprechpartner 180, E-Mail 220, Notizen 260, Pipeline 130, Statusspalten 110.
- Datenvalidierung als Dropdown-Chips (nicht strikt, damit Altwerte sichtbar bleiben): `Versandfreigabe` yes/no; `Opt-out-Status` yes/no/unknown; `Opt-in-Status` yes/no/unknown; `Send_Status` not_sent/prepared/drafted/sent; `Legal_Basis` UNKNOWN/no/EXISTING_CUSTOMER_7_3/OWNER_APPROVED; `Reply_Status` (leer)/replied/auto_reply_ooo/bounced/opt_out.
- Neue Spalte **BE `Pipeline`** (ARRAYFORMULA in BE2), Reihenfolge der Auswertung: Abgemeldet (rot) → Bounce (orange) → Antwort (gelb) → Versendet (grün) → Entwurf (hellblau) → Freigegeben (blau) → Neu (grau). Bedingte Formate auf BE.
- Filteransichten: `Heute Joel`, `Heute Jordi` (Verantwortlicher + Pipeline in {Freigegeben, Entwurf, Antwort}), `Antworten offen`, `Gesperrt`.
- Bestehende 14 bedingte Formate bleiben unangetastet.

### B. Datenmodell-Reparatur (nur mit Owner-Freigabe je Regel, Skript mit Dry-Run)
- `Legal_Basis`: `yes` (20) → `OWNER_APPROVED`; `no` bleibt `no`. Vorher Liste der 20 Lead-IDs als Dry-Run-Ausgabe.
- `Bounce_Status`: aus `Reply_Status=bounced` (20) → `hard`; `Reply_Status` bleibt bounced (Kompatibilität Dashboard/Adapter).
- `Send_Datum`: einheitlich ISO-8601 mit Zeitzone; reine Datumswerte (25) bekommen `T00:00:00+02:00`? — **nein**: bleiben Datum, nur neue Werte ISO. Keine Rückdatierung erfinden.
- `DASHBOARD`: Opt-outs/Bounces = `COUNTIF(Y:Y,"yes")+COUNTIF(AQ:AQ,"<>")`-Korrektur.

### C. Automatik
- Apps Script: `doPost(e)` mit Shared-Secret-Header, Payload `{mailbox, folder, internetMessageId, conversationId, from, to[], subject, receivedUtc, bodyPreview(<=2000), ndr:boolean}`. Antwort `{status, leadId, classification}`. Log in `INBOUND_EVENTS` (Event_ID = SHA1(internetMessageId)). Idempotent.
- Flows (je Postfach 2): Trigger V3 mit Ordner; Aktion HTTP POST; bei Fehler Wiederholung 3×; keine Send-Aktion. Stichwörter Opt-out: abmelden, austragen, abbestellen, keine weiteren, unsubscribe, widerspruch, widerspreche. NDR: Betreff „Unzustellbar"/„Undeliverable" oder Absender `postmaster`/`MAILER-DAEMON`.
- Rückabgleich ab 2026-09-04: manueller Flow „E-Mails abrufen (V3)" je Ordner, gleicher POST.
- Jordi: eigene Outlook-Connection, Flows als Co-Owner dupliziert. Bis dahin läuft Joel produktiv.

## Fehlerbehandlung
Web-App antwortet 200 auch bei „kein Lead gefunden" (Event wird mit `Lead_ID` leer protokolliert, `Classification=unmatched`) — nichts geht verloren, nichts wird geraten. 4xx nur bei ungültigem Secret. Flows loggen Fehlläufe; Sheet bleibt unverändert bei Fehler.

## Verifikation
- Vorher/Nachher-Zählungen mit `crm_analyze.py` (Wrap, Breiten, Gruppen, Filteransichten, Verteilungen).
- Testfall 1: Testentwurf an eigene Adresse senden → Zeile `Send_Status=sent`, Pipeline grün, Event `sent`.
- Testfall 2: Antwort „Abmelden" auf die Testmail → `Opt-out-Status=yes`, `Suppressed=yes`, `Versandfreigabe=no`, Pipeline rot, Event `opt_out`; erneute Antwort ändert nichts (idempotent).
- Testfall 3: künstliche NDR → `Bounce_Status=hard`, Pipeline orange.
- `apps/sales-os/tests` grün vor/nach; Header von `ALL_LEADS` A1:BD1 byte-identisch vor/nach.

## Owner-Gates (offen)
Sheet-Eigentum + Google-Connections vom Privatkonto auf HSB-Konto; Freigabe der Regel B (Legal_Basis-Umschlüsselung); Jordis Connection.
