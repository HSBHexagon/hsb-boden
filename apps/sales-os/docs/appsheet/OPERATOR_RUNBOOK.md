# HSB Sales OS — Mobile AppSheet Operator Runbook

## Zielgruppe
Dieses Handbuch richtet sich an **Joel Cherino Diaz** und **Jordi Post** für die tägliche Nutzung des HSB Sales OS auf dem Smartphone (iOS / Android) und im Web-Browser.

---

## 1. Erstmalige Einrichtung & Login
1. **App installieren:**
   - **iOS:** Im Apple App Store die offizielle App **AppSheet** von Google herunterladen.
   - **Android:** Im Google Play Store die offizielle App **AppSheet** herunterladen.
   - **Desktop:** AppSheet im Browser öffnen (Google Chrome empfohlen).
2. **Anmeldung:**
   - Auf **Sign in with Google** tippen.
   - Mit dem verifizierten Google Workspace Account anmelden:
     - Joel: `j-cherino@hsb-boden.de`
     - Jordi: `j-post@hsb-boden.de`
3. **App öffnen:**
   - Die freigegebene App **HSB Sales OS Mobile** auswählen.

---

## 2. Hauptbereiche der mobilen App

### 1. HOME (Leitstand-Dashboard)
- Zeigt in Echtzeit deine persönlichen Kennzahlen:
  - **Sendebereite Leads:** Deine noch unkontaktierten Tier-A/B-Leads.
  - **Vorbereitete Batches:** Zuletzt erstellte EML-Pakete.
  - **Offene Wiedervorlagen:** Kontakte, bei denen heute oder früher ein Follow-up fällig ist.
  - **Eingegangene Antworten:** Neue Inbound-Reaktionen von Interessenten.

### 2. MY LEADS (Kontakte-Deck)
- Durchsuchbare Liste aller dir zugewiesenen Leads.
- Farbige Badges: **Tier A (Grün)** = Höchste Priorität, **Tier B (Blau)** = Mittlere Priorität.
- **1-Tap-Aktionen:**
  - 📞 **Anrufen:** Startet sofort die Telefon-App mit der hinterlegten Rufnummer.
  - 🌐 **Website:** Öffnet den Webauftritt des Unternehmens im mobilen Browser.
  - ✏️ **Notiz bearbeiten:** Öffnet die Schnelleingabe für Gesprächsnotizen.

### 3. LEAD DETAIL (Kompaktansicht)
- Zeigt Firma, Ansprechpartner, Branche, Telefon, E-Mail, Website und bisherige Notizen.
- **Erlaubte Änderungen:**
  - `Notizen` (Gesprächsverlauf protokollieren)
  - `Nächste Aktion` (z.B. "Angebot nachfassen", "Zweiter Anrufversuch")
  - `Follow-up-Datum` (Datum für die Wiedervorlage setzen)
- *Hinweis:* Technische Felder (Lead-ID, Kampagne, Batch-Status, etc.) sind schreibgeschützt und vor versehentlichem Überschreiben geschützt.

### 4. REPLIES (Antworten & Triage)
- Chronologische Übersicht aller eingegangenen Antworten deiner Leads.
- 1-Tap öffnet direkt die Detailansicht des Kontakts zur weiteren Bearbeitung.

### 5. BATCHES (Kampagnen-Historie)
- Reine Leseansicht aller bisher vorbereiteten und versendeten E-Mail-Pakete.

---

## 3. Offline-Betrieb & Synchronisation
- **Automatische Synchronisation:** Die App synchronisiert sich beim Start und bei jeder Speicherung automatisch.
- **Offline-Nutzung:** Wenn du unterwegs im Funkloch bist, kannst du zugewiesene Kontakte weiterhin einsehen und Notizen eintragen. Sobald wieder Empfang besteht, überträgt AppSheet die Notizen nahtlos und konfliktfrei in das Google Sheet.
- **Manuelle Synchronisation:** Über das runde Pfeil-Symbol oben rechts kann jederzeit eine manuelle Aktualisierung ausgelöst werden.

---

## 4. Wichtige Sicherheitsregeln
- **Kein E-Mail-Versand aus AppSheet:** Die Vorbereitung und der Versand von Erstkontakt-E-Mails erfolgt wie gewohnt über die Google Sheets Seitenleiste am Desktop.
- **Datenschutz:** Jeder Vertriebsmitarbeiter sieht strikt nur seine eigenen Kontakte (`OWNER_CROSSOVER_COUNT = 0`).
