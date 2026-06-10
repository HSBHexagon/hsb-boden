# HEXAFLOOR Arbeitszustand & Abarbeitungsplan — Abgleich mit Repo-Stand (2026-06-10)

> Quelle: hochgeladenes Dokument „HEXAFLOOR / HSB-Boden — Konkreter Arbeitszustand und Abarbeitungsplan" (DOCX).
> Dieses Dokument gleicht den operativen Plan mit dem tatsächlichen Stand dieses Repos ab und markiert, was korrekt/anwendbar ist, was bereits erledigt wurde und was außerhalb des Repos liegt.
> Verbindlicher Rahmen: Preview-/Entwurfsmodus, kein Go-Live (siehe `2026-06-07-hsb-masterplan-golive.md`, Abschnitt „Arbeitszustand 2026-06-10"). Non-Negotiables aus `AGENTS.md` gelten unverändert.

## 1. Bewertung des Dokuments

Das Dokument ist als operativer Akquise-Plan **inhaltlich korrekt und anwendbar**, in zwei Punkten aber gegenüber dem Repo-Stand veraltet:

1. **Website-Status ist überholt.** Die „externe Sichtprüfung" bezog sich auf die alte WordPress-Seite bzw. den frühen Stand. Tatsächlich existiert im Repo eine vollständige Astro-Site (Preview live), inkl. Branchenseiten, kuratierter Referenzen mit Freigabestatus, Leadformular mit Validierung, 301-Redirect-Map und JSON-LD.
2. **Domainstrategie ist zwischenzeitlich entschieden:** hsb-boden.de bleibt vorerst unangetastet; Arbeit nur auf der Preview-Umgebung; PR #2 (Worker-Umbenennung) wird nicht gemerged. Die Empfehlung des Dokuments („hsb-boden.de als Vertrauensanker, hexafloor.de nur kontrolliert weiterführen/weiterleiten") bleibt als Zielbild für den späteren Go-Live gültig.

Die Compliance-Linie des Dokuments (P0: keine Kaltmail an 5.000 Leads, Opt-in-Blocker, Opt-in-Protokoll, Suppression überschreibt alles) deckt sich mit den Non-Negotiables in `AGENTS.md` und ist **vollumfänglich zu übernehmen**. Finale rechtliche Bewertung (UWG § 7, DSGVO Art. 6 / EG 47) bleibt einer juristischen Stelle vorbehalten.

## 2. Phasenabgleich

| Phase (Dokument) | Inhalt | Repo-relevant? | Stand 2026-06-10 |
|---|---|---|---|
| Phase 0 | Inventar, Lead-Datei lokalisieren, Domain-/Website-Status klären | teilweise | Website-Status geklärt: Preview live, Go-Live gesperrt. Lead-Datei + Zugänge: **außerhalb Repo, offen (User)** |
| Phase 1 | Website als Conversion-Basis (Referenzen, Branchen, Kontakt) | ja | **Weitgehend erledigt** (PR #1 + #3): Branchenseiten (`src/pages/branchen/`), Referenzen mit `approvalStatus`, Leadformular inkl. Branchen-Dropdown, SEO-Härtung. Offen: SMTP-Anbindung des Formulars (Masterplan Phase 1) |
| Phase 2 | Flyer als Phone-to-Email-Türöffner, Follow-up-Mail, Call-Script | nein (Vertriebsassets) | **Offen.** QR-/UTM-Ziel kann auf Branchen-Landingpages der Preview zeigen, sobald Domain final ist — vorher keine QR-Drucke mit Preview-URL |
| Phase 3 | CRM-Light in Google Sheets (Tabs, Pflichtfelder, Statusmodell, Testimport) | nein (extern) | **Offen.** Statusmodell + Pflichtspalten des Dokuments sind als Vorgabe übernehmbar; deckt sich mit `2026-06-07-hsb-lead-pipeline.md` |
| Phase 4 | n8n-Workflows A–E (Enrichment, Upsert, Opt-in-Follow-up, IMAP, Reporting) | teilweise (n8n-Instanz existiert lokal) | **Offen.** Opt-in-Blocker (Workflow C) ist P0; ohne ihn kein Mailversand. Hosting-Entscheidung offen (User) |
| Phase 5 | Pilot 25–50 Leads, Vertriebsschulung, Auswertung | nein | **Offen**, erst nach Phase 3+4 und Compliance-Freigabe |
| Phase 6 | Skalierung auf 5.000 Leads in Tranchen | nein | **Offen**, Gate: Pilot ohne Fehlsendung |

## 3. P0-Backlog des Dokuments — Status

| P0-Punkt | Status |
|---|---|
| Keine Kaltmail an 5.000 Leads (Opt-in-Blocker in allen Versandworkflows) | Regel aktiv (AGENTS.md); technische Umsetzung in n8n offen |
| CRM-Sheet mit Opt-in-Protokoll | Offen (extern, User/Vertrieb) |
| Referenzen freigeben/anonymisieren | ✅ **Erledigt im Repo**: nur Südzucker AG namentlich (freigegeben), alle übrigen anonymisiert mit Regionsangabe |
| n8n-Testmodus vor Produktivmodus | Offen; n8n läuft bisher nur lokal mit Testdaten |

P1 „Branchensegmente auf Website abbilden" ist im Repo **erledigt** (jede Zielbranche hat eine eigene Seite unter `/branchen/[slug]/`). P2 „Legacy-/Markenarchitektur bereinigen" (hexafloor.de) ist **dokumentiert, aber bewusst zurückgestellt** bis zur Go-Live-Entscheidung.

## 4. Was dieses Repo NICHT tut (bewusste Abgrenzung)

- Kein Versand von E-Mails, keine Kontaktaufnahme, keine Verarbeitung gekaufter Leads — das Repo liefert nur Website + Formular-Endpunkt.
- Keine Übernahme von hsb-boden.de (DNS, Worker-Name, Production-Deploy) ohne explizite Freigabe.
- Keine rechtliche Bewertung — Impressum/Datenschutz sind Entwürfe bis zur juristischen Prüfung.

## 5. Nächste Schritte (Reihenfolge gemäß User-Entscheidung)

1. **Entwurf finalisieren** (laufend): Inhalte, Referenzen, Kontaktformular, Mobile/Desktop-Prüfung, SEO-Feinschliff — auf der Preview.
2. **Voraussetzungen erfüllen** (User-Inputs): GA4-ID · SMTP-Zugang · n8n-Hosting-Entscheidung + Opt-in-Blocker · juristische Prüfung · finale Freigabe.
3. **Erst danach:** Worker-Umstellung Preview→Produktion (dann PR #2 oder äquivalent), DNS-/Domain-Go-Live.

> Arbeitsregel aus dem Quelldokument, hier übernommen: Dieses Abgleichsdokument nach jeder erledigten Phase aktualisieren (Datum, Ergebnis, offene Blocker).
