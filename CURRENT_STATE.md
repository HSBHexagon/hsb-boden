# CURRENT_STATE — Live-Fortschritt & Taskboard (SSOT)

> **Stand:** 2026-10-13, Live-Abgleich der All-Inkl-Postfächer und des Google-CRM  
> **Dokumentationsstand:** PR #458; produktive Dateien liegen auf `main` und im Live-CRM. Merge/Freigabe getrennt.  
> **System-Status:** `.COM`-Postfächer aktiv; **100 externe Nachrichten vom 12.10.2026 im Gesendet-Ordner von Jordie nachgewiesen** (Zustellung nicht einzeln belegt). Historische 798/798 Tests vom 12.10. sind kein neuer Gesamtabnahmetest. Neuversand nicht freigegeben.

---

## 1. Abgeschlossene Meilensteine (DONE)

- [x] **Dev-Dummy Bereinigung:** 4 Entwicklungs-Mails restlos aus Exchange gelöscht.
- [x] **Inbound Automation Workers:** `ingest_bounces.py` + `ingest_optouts.py` implementiert und ausgeführt.
- [x] **Pre-Send DNS/MX-Guard:** `check_domain_mx` fängt ungültige Domains automatisch ab.
- [x] **Kanonisches Namens-Hardening:** `Jordie Post` (mit -ie) in allen Dateien verankert (§ 35a GmbHG).
- [x] **SSOT-Architektur:** `PROJECT_TRUTH.md` und `scripts/verify_ssot.py` etabliert.
- [x] **Kanonische Vektor-Flyer (241 KB):** Joel & Jordie Master-PDFs mit SHA-256 Gates integriert.
- [x] **.COM Outbound Akquise-Shield (All-Inkl):** 
  - `j-cherino@hsb-boden.com`: 102 Entwürfe (IMAP/SMTP OK)
  - `j-post@hsb-boden.com`: 52 Entwürfe (IMAP/SMTP OK)
  - `Reply-To: ...@hsb-boden.de` für M365-Antwort-Routing verifiziert
- [ ] **HTTPS-Weiterleitung `.com`:** 13.10. Live-TLS-Prüfung fehlgeschlagen: Zertifikat `*.kasserver.com` passt nicht zu `hsb-boden.com`. Der 301-Redirect funktioniert nur, wenn die Zertifikatsprüfung deaktiviert wird (kein positiver HTTPS-Nachweis). Autoritative DNS-Server weiterhin All-Inkl; Cloudflare-Zone `pending`. Nameserver/MX nicht ungeprüft ändern.
- [x] **Google Sheet SSOT Sync 12.10.:** Historisch 50 Leads für Jordie als `drafted` synchronisiert. **Korrektur 13.10.:** 100 eindeutige externe Sendungen (Sent-Ordner vom 12.10.) in `ALL_LEADS` über Empfänger UND `Internet_Message_ID` wiedergefunden. Diese 100 von `drafted` auf `sent` und `SENT_COM_2026` gesetzt, UTC-Sendezeit sowie `.com`-Sender ergänzt; 300 API-Operationen, 0 unerwartete Änderungen an anderen Leads.
- [x] **Live-Testversand an Betreiber:** Erfolgreiche Test-Zustellung an `cherinodiaz@outlook.com` ohne Bounces.

---

## 2. Nächste operative Schritte (TODO)

### P1 — Operative Akquise & Vertrieb
- [ ] **Tägliche Outlook-Sichtung:** Joel und Jordie prüfen vorhandene Entwürfe (100 externe Joel + 50 externe Jordie, jeweils 2 interne Tests). Kein weiterer Kundensendebatch ohne belegte Freigaben, deduplizierte CRM-Statusabfrage und Postfachabgleich.
- [ ] **Nächster Entwurfs-Batch:** Nicht automatisch nachladen. Die vorhandenen Postfächer enthalten bereits 150 externe Entwürfe; 100 weitere Jordie-Empfänger wurden gesendet. Rechtliche Einzelnachweise sind in `ALL_LEADS!BL:BM` nicht hinterlegt und dürfen nicht fingiert werden.
- [ ] **Dual-Domain Reconciliation:** Regelmäßiger Abgleich via `python3 apps/sales-os/engine/hsb_cli.py sync`.

### P2 — Wartung & GitHub
- [ ] **Dependabot PR #457:** Bump sharp/wrangler in `apps/website` final abschließen (nach CodeQL-Freigabe).
- [ ] **4.000+ verbleibende Leads:** Sukzessive Vorbereitung im Google Sheet `ALL_LEADS`.

---

## 3. Tool-Start-Anweisung für KIs

Vor jeder Bearbeitung:
1. Lies `PROJECT_TRUTH.md`
2. Lies `CURRENT_STATE.md` (diese Datei)
3. Führe nach Änderungen `python3 scripts/verify_ssot.py` aus (Muss Exit 0 sein!)
4. Teste mit `pytest apps/sales-os/tests/ -q`

### Nachweis 13.10.2026: `.com`-Betriebsprüfung

| Prüfschritt | Joel | Jordie |
| --- | --- | --- |
| IMAP / SMTP | OK / OK | OK / OK |
| Entwürfe gesamt | 102 | 52 |
| Davon externe Entwürfe | 100 | 50 |
| Sent-Ordner | 3 | 104 |
| Externe Sendungen vom 12.10. | 0 gefunden | 100 gefunden und CRM-korrigiert |
| Reply-To bei sämtlichen Entwürfen | `.de` | `.de` |
| PDFs bei sämtlichen Entwürfen | 102/102 | 52/52, ein älterer interner Test mit 1,5 MB |

Alle 154 Drafts haben `X-Unsent=1`, `.com`-From und je einen PDF-Anhang; kein externer Draft-Empfänger überschneidet sich mit dem Sent-Ordner desselben Postfachs. `COM_ROLLOUT_GATE!A90:F98` ist der aktuelle Live-Nachweis; frühere Einträge sind Historie. Der Mac-Entwurfsworker läuft per LaunchAgent alle 120 Sekunden mit Freigabe-/Duplikatsprüfungen; der Cloud Scheduler bleibt **PAUSED**. SPF setzt All-Inkl ein, DMARC ist `p=none`; DKIM-Alignment und TLS-Abnahme fehlen. Die 100 beobachteten Sent-Nachrichten sind keine unabhängige Zustellbestätigung; die erzeugende Aktion/Person ist ungeklärt. Keine neuen Mails oder Drafts während dieser Prüfung.
