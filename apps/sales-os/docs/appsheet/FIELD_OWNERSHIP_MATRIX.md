# HSB Sales OS — ALL_LEADS 56-Spalten Field Ownership Matrix

Dieses Dokument definiert verbindlich die Eigentümerschaft, Berechtigungen und Validierungsregeln für alle 56 Spalten des kanonischen `ALL_LEADS` Worksheets.

---

## 1. Übersicht der Kategorien

* **`HUMAN_EDITABLE` (3 Spalten):** Ausschließlich diese Felder dürfen von Vertriebsmitarbeitern (Joel & Jordi) in der mobilen AppSheet-App oder im Google Sheet editiert werden.
* **`SYSTEM_MANAGED` (20 Spalten):** Werden ausschließlich vom Apps Script Kernsystem (Batch-Allokation, EML-Generierung, Graph-Drafts, Inbound-Webhooks) geschrieben. AppSheet-Berechtigung: `Editable_If = FALSE`.
* **`STATIC_CANONICAL` (23 Spalten):** Stammdaten des Leads aus der Master-Liste. AppSheet-Berechtigung: `Editable_If = FALSE`.
* **`AUDIT_ONLY` (10 Spalten):** Technische Nachweise und Zeitstempel. Schreibgeschützt.

---

## 2. Vollständiges 56-Spalten-Verzeichnis

| Spalte # | Spaltenname (Header) | Datentyp | Kategorie | Google Sheets Validierung | AppSheet `Editable_If` | Beschreibung / Semantik |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `Lead-ID` | Text | `STATIC_CANONICAL` | Regex `^HSB-\d{8}-\d{5}$` | `FALSE` (Primary Key) | Unveränderlicher Primärschlüssel |
| **2** | `Firma` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Firmenname |
| **3** | `Standort` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Ort / PLZ |
| **4** | `Region` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Bundesland / Region |
| **5** | `Branche` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Branchenklassifikation |
| **6** | `Tier` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Lead-Priorität (Tier A, Tier B) |
| **7** | `Ansprechpartner` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Vollständiger Name |
| **8** | `Rolle` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Funktion im Unternehmen |
| **9** | `E-Mail` | Text | `STATIC_CANONICAL` | E-Mail-Format | `FALSE` | Kontakt-E-Mail |
| **10** | `Telefon` | Text | `STATIC_CANONICAL` | Telefon-Format | `FALSE` | Rufnummer (1-Tap-Call fähig) |
| **11** | `Website` | Text | `STATIC_CANONICAL` | URL-Format | `FALSE` | Firmen-Website |
| **12** | `Quelle` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Herkunft des Leads |
| **13** | `Score` | Zahl | `SYSTEM_MANAGED` | Keine (Gesperrt) | `FALSE` | Berechneter Lead-Score |
| **14** | `Status` | Text | `SYSTEM_MANAGED` | Keine (Gesperrt) | `FALSE` | Aggregierter Bearbeitungsstatus |
| **15** | `Kontakt_Datum` | Datum | `SYSTEM_MANAGED` | Datumsformat | `FALSE` | Datum der Erstansprache |
| **16** | `Kanal` | Text | `SYSTEM_MANAGED` | Keine (Gesperrt) | `FALSE` | Kommunikationskanal |
| **17** | `Nächste Aktion` | Text | `HUMAN_EDITABLE` | Dropdown-Liste | `TRUE` | **Aufgabe / Vertriebsschritt** |
| **18** | `Follow-up-Datum` | Datum | `HUMAN_EDITABLE` | Datumsformat | `TRUE` | **Wiedervorlage-Termin** |
| **19** | `Ergebnis` | Text | `SYSTEM_MANAGED` | Keine (Gesperrt) | `FALSE` | Letztes Aktionsergebnis |
| **20** | `Wiedervorlage` | Text | `SYSTEM_MANAGED` | Keine (Gesperrt) | `FALSE` | Wiedervorlage-Status |
| **21** | `Opt_Out` | Text | `SYSTEM_MANAGED` | Dropdown yes/no | `FALSE` | Abmeldevermerk |
| **22** | `Hard_Bounce` | Text | `SYSTEM_MANAGED` | Dropdown yes/no | `FALSE` | Unzustellbarkeitsvermerk |
| **23** | `Soft_Bounce` | Text | `SYSTEM_MANAGED` | Dropdown yes/no | `FALSE` | Temporärer Bounce |
| **24** | `Reply` | Text | `SYSTEM_MANAGED` | Dropdown yes/no | `FALSE` | Antwort-Kennzeichen |
| **25** | `Manual_Review` | Text | `SYSTEM_MANAGED` | Dropdown yes/no | `FALSE` | Prüf-Kennzeichen |
| **26** | `Versandfreigabe` | Text | `SYSTEM_MANAGED` | Dropdown yes/no | `FALSE` | Compliance-Versandfreigabe |
| **27** | `Verantwortlicher` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Joel Cherino Diaz / Jordi Post |
| **28** | `Flyer-Anhang` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Flyer-Dateiname |
| **29** | `Notizen` | LongText | `HUMAN_EDITABLE` | Freitext | `TRUE` | **Gesprächsnotizen & Verlauf** |
| **30** | `Kampagne_ID` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Kampagnen-ID |
| **31** | `Email_Template_ID`| Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | E-Mail-Vorlagen-ID |
| **32** | `Flyer_ID` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | Flyer-Asset-ID |
| **33** | `Flyer_URL` | Text | `STATIC_CANONICAL` | URL-Format | `FALSE` | Google Drive URL |
| **34** | `Landing_URL` | Text | `STATIC_CANONICAL` | URL-Format | `FALSE` | Zielseite |
| **35** | `UTM_Source` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | UTM Parameter |
| **36** | `UTM_Medium` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | UTM Parameter |
| **37** | `UTM_Campaign` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | UTM Parameter |
| **38** | `UTM_Content` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | UTM Parameter |
| **39** | `UTM_Term` | Text | `STATIC_CANONICAL` | Keine (Gesperrt) | `FALSE` | UTM Parameter |
| **40** | `Batch_ID` | Text | `SYSTEM_MANAGED` | Regex `^HSB-.*` | `FALSE` | Zugewiesener Batch |
| **41** | `Send_Status` | Text | `SYSTEM_MANAGED` | not_sent/sent/blocked| `FALSE` | Sende-Status |
| **42** | `Send_Datum` | Datum | `SYSTEM_MANAGED` | Datumsformat | `FALSE` | Tatsächliches Sendedatum |
| **43** | `Bounce_Status` | Text | `SYSTEM_MANAGED` | none/hard/soft | `FALSE` | Zustellbarkeitsstatus |
| **44** | `Reply_Status` | Text | `SYSTEM_MANAGED` | none/replied | `FALSE` | Inbound-Reaktionsstatus |
| **45** | `Legal_Basis` | Text | `SYSTEM_MANAGED` | Fail-closed UNKNOWN | `FALSE` | DSGVO/UWG Rechtsgrundlage |
| **46** | `Suppressed` | Text | `SYSTEM_MANAGED` | yes/no | `FALSE` | Ausschluss-Kennzeichen |
| **47** | `Batch_Status` | Text | `SYSTEM_MANAGED` | PREPARED/SENT | `FALSE` | Status des Batches |
| **48** | `Prepared_At` | DateTime | `AUDIT_ONLY` | ISO-8601 | `FALSE` | Vorbereitungs-Zeitstempel |
| **49** | `Draft_ID` | Text | `SYSTEM_MANAGED` | Keine (Gesperrt) | `FALSE` | Graph Entwurfs-ID |
| **50** | `Drafted_At` | DateTime | `AUDIT_ONLY` | ISO-8601 | `FALSE` | Entwurf-Zeitstempel |
| **51** | `Approved_At` | DateTime | `AUDIT_ONLY` | ISO-8601 | `FALSE` | Freigabe-Zeitstempel |
| **52** | `Outlook_Message_ID`| Text | `AUDIT_ONLY` | Keine (Gesperrt) | `FALSE` | Graph API Message-ID |
| **53** | `Internet_Message_ID`| Text | `AUDIT_ONLY` | Keine (Gesperrt) | `FALSE` | RFC-5322 Message-ID |
| **54** | `Conversation_ID`| Text | `AUDIT_ONLY` | Keine (Gesperrt) | `FALSE` | Thread Conversation-ID |
| **55** | `Last_Reply_At` | DateTime | `AUDIT_ONLY` | ISO-8601 | `FALSE` | Antwort-Zeitstempel |
| **56** | `Last_Error` | Text | `AUDIT_ONLY` | Keine (Gesperrt) | `FALSE` | Letzte Fehlermeldung |
