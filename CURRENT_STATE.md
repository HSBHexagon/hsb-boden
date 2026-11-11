# CURRENT_STATE — HSB Sales OS

Stand: 10.11.2026, 17:00 UTC. Status: **PRODUKTIONSREIF (GO) & AKTIV IM LIVE-VERSAND**.

## 10.11.2026 — P0 Health Secret behoben, PR #572 gemergt & Live-Tagesversand aktiv
- **P0-Behebung:** `HSB_SALES_SEND_HEALTH_JSON` im GitHub-Environment `customer-send` autorisiert erneuert (`updated_at: 2026-11-10T16:43:59Z`). 125 verifizierte `seen_inbound_ids` aus Live-IMAP, echte Seed-Nachweise JOEL (`<179422315651...>`) und JORDI (`<179422316124...>`) mit SPF/DKIM/DMARC PASS (`d=hsb-boden.com`), 0 Bounces/Deferrals/Spam. 24h-Gültigkeit bis 11.11.2026 gesichert.
- **SSOT & Tests:** `verify_ssot.py` Exit 0 (Jordie Post mit *-ie*, Monorepo-Regeln), `pytest apps/sales-os/tests` 762 passed, 1 skipped (45.62s).
- **Finale Abnahme:** `HSB_SALES_OS_FINAL_ABNAHME.md` erstellt, alle 14 CI-Checks grün, in PR #572 gemergt (`ce26a6f`).
- **Live-Versand 10.11.2026:** Über 350 erfolgreiche Kunden-Sends über .com-Postfächer im CRM Master nachgewiesen (Run #42829194956 mit 79 Sends abgeschlossen, Run #42849477751 aktiv). Joel hat sein Tagesbudget von 249/250 erreicht.
- **CRM Master Integrität:** Exakt 6.424 Leads in `ALL_LEADS`; 1.593+ `sent`, 4.824 `drafted`, 1 `failed`, 6 `not_sent`. 1.153 Ereignisse in `INBOUND_EVENTS`.
- **Projektchronologie:** Seq 46 in `PROJECT_CHRONOLOGY` eingetragen und per Readback verifiziert.

## 05.11.2026 — Alle offenen Entwürfe beider .com-Postfächer fertig
- Vollständiges Audit (prepare-drafts Lauf 268, audit-3, 10:40 UTC): JOEL 2.784 von 2.830 versandbereit, JORDI 1.924 von 1.955. Kundenversand: 0.
- Fassung REPARATUR_COPY_REV 2026-11-05: HTML mit kanonischer HSB-Signatur (Logo 102x75, Name fett, rote Trennlinie, Pflichtangaben 11 px grau), Textteil gleichlautend, genau ein Link `/reparatur/` (302 auf Reparaturseite mit UTM), Abmeldung per Antwort plus List-Unsubscribe-Header beim Versand.
- Gesperrt bleiben: 38 + 30 bereits Kontaktierte, 2 alte JOEL-Entwürfe ohne Textteil, 4 mit Textbefund, 2 Firmenname unbestätigt, 1 JORDI-Planerbefund.
- send-preview mit 5 (Lauf 269): je Postfach 5 ausgewählt, 0 gesendet.
- Versand: GitHub Actions → Sales OS safety and inbound → mode `send`, count 1–35 je Postfach. Empfehlung laut Recherche: mit 5–10 je Postfach starten, über ca. 4 Wochen auf 35 steigern, DKIM im All-Inkl-KAS aktivieren.
- PRs: #528 (Signatur), #529/#530/#533 (Austausch in place mit gleicher Message-ID, CRM-Vorlage in Sammelaufrufen).
- Recherche Best Practice (Zustellbarkeit, Recht, Text): `/home/user/reports/B2B Kaltakquise Best Practice.md` in der Claude-Sitzung.

## 04.11.2026 — Reparatur-zuerst-Vorlagen und Bereinigung (Code fertig, Postfächer offen)
- Code auf Branch `claude/marketing-strategy-url-bug-ddllet` (PR #465, inkl. #515/#516/#517): neue Reparatur-Texte, Anrede-Regel, ein lesbarer Link `/reparatur/`, kein Anhang, MIME multipart/alternative mit CRLF, Duplikat-Bereinigung (`dedupe-drafts`), Domain-Sperre, SSOT-Checks für Hashes/Anhangsname/URLs.
- Tests: 556 Python, 366 Website, Astro-Check 0 Fehler, 59 Seiten, Worker-Dry-Run ok.
- Postfächer: in dieser Sitzung NICHT geändert. Zahlen zu aktualisierten Entwürfen und Dubletten stehen aus (Lauf auf dem Mac nötig, siehe apps/sales-os/CURRENT_HANDOFF.md).
- `/reparatur/` ist erst nach dem nächsten Production-Deploy erreichbar; bis dahin keine Entwürfe senden.

## Stand 26.10.2026

- Master vollständig bilanziert: 6.424 Leads, 3.212 Joel / 3.212 Jordie. Jede Zeile in ALL_LEADS!BN:BR mit Auditstatus, Gründen und Draft-UIDs; alle 6.424 Zeilen zurückgelesen.
- Joel: 3.080 Entwürfe, davon 3.078 eindeutige CRM-Kundenentwürfe und zwei interne Tests. Jordie: 2.538 / 2.536 / zwei Tests; fünf Kundenentwürfe liegen beim falschen Mitarbeiter.
- Versandfähig: 0 / 0. Die ausdrückliche datierte Betreiberbestätigung zur §-7-Prüfung steht für alle Leads auf yes und wird als separater manueller Freigabeweg berücksichtigt. Historische Varianten und sonstige Einzelmängel bleiben gehalten; Originale sind gesichert und unverändert.
- .de-Forensik: 1.274 Vorgänge, 702 Empfänger. Alle 488 zugehörigen CRM-Leads stehen auf sent; 214 Empfänger liegen außerhalb des Masters und bleiben in der Forensik.
- Zusätzlich 295 bestätigte .com-Versandstatus samt Datum, Message-ID und Sender_Account ins CRM übernommen; insgesamt 1.069 bereits kontaktierte Leads. Wiederholung erzeugt null Sent-Updates.
- 259 Kundenentwürfe überschneiden sich mit dokumentierter Kontaktaufnahme; keine Kunden-Empfängerdubletten zwischen den Entwurfsordnern.
- .com-Inbound: zuletzt 91 Nachrichten. Zwei zuvor fehlende Bounce-Ereignisse und 40 unvollständige Bounce-Sperren mit CRM-Readback nachgetragen. Negative Reclassifizierung ist auch nach unterbrochenem Event-Append wiederanlaufsicher.
- Alle sechs IMAP-Ordner per UID-Satz und UIDVALIDITY erneut abgeglichen; eine neue Inbox-Nachricht archiviert. Keine Entwürfe erzeugt, verändert oder gelöscht.
- Beide .com-Postfächer per IMAP und SMTP authentifiziert. Kundenversand in diesem Lauf: 0.
- PR #469 normal in main übernommen (d80c9bb9). GitHub-Actions-Sent-/Inbound-Sync auf main erfolgreich: Run 40338208174. Stündlich Minute 17, maximal 20 Minuten, keine parallelen Cloud-Läufe; Kunden-SMTP ausdrücklich deaktiviert.
- Start über sales-os-safety.yml / workflow_dispatch / mode=inbound-sync. Kundensenden bleibt ein separat zu aktivierender, begrenzter CLI-Schritt mit globalem Lock, Journal und Readbacks; 35/Postfach/Tag, keine Freigabe für 100/Stunde.
- Abmeldeseite nach geprüfter manueller Veröffentlichung produktiv per HTTP abgenommen: ehrliche Abmeldeanforderung an überwachte .com-Inbox, keine falsche Sofortbestätigung. Homepage und Kontaktformular bleiben aktiviert. Production-Run 40341382688. Ein Seitenaufruf allein erzeugt keine Sperre.
- Jordies historische .de-M365-Verbindung: HTTP 403 / ACCESS_BLOCKED. Outlook-Mac-Sichtbarkeit nicht unabhängig verifiziert. Browser-Rendering blockiert durch Host-Zugriffsrichtlinie.
- 188 Python-Tests bestanden, ein Live-Test separat durch reale Authentifizierung abgedeckt. 337 Website-Tests, Astro ohne Fehler/Warnungen, 58 Seiten gebaut, Wrangler-Dry-Run bestanden. CodeQL und weitere relevante CI in PR #469 erfolgreich.

Maschinenlesbarer Nachweis: docs/audits/SALES_OS_VERIFICATION_2026-10-26.json. Einzelgründe und exakte Lead-IDs stehen im CRM; private Originalbelege unter ~/KI-System/07_Logs/hsb-sales-os-20261026/.

Aktuelle Betreiberanweisung: §-7-Prüfung laut ausdrücklicher Bestätigung bereits geklärt. Für alle 6.424 Leads ist Legal_Review_Status=yes mit Herkunftsvermerk und Datum in ALL_LEADS!BS:BU geschrieben und zurückgelesen. Vorhandene Opt-outs, Bounces, Versandhistorie und übrige CRM-Felder wurden dabei unverändert erhalten.
