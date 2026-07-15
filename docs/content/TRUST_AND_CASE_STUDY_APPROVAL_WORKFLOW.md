# Trust- und Case-Study-Freigabeprozess

## Zweck

Dieses Dokument ist das verbindliche Veröffentlichungs-Gate für Teamprofile, Qualifikationen, Zertifikate, Kundenreferenzen, Projektkennzahlen, Zitate und Projektbilder. Ohne dokumentierten Nachweis und die erforderliche Freigabe bleibt der Datensatz im Status `draft` oder `verified` und wird nicht veröffentlicht.

## Statusmodell

- `draft`: Inhalt ist unvollständig oder noch nicht geprüft.
- `verified`: Fakten und Quellen wurden intern geprüft; eine Veröffentlichungsfreigabe fehlt noch.
- `approved`: Fakten sind belegt und die notwendige Veröffentlichungsfreigabe ist dokumentiert.

Nur `approved` kann durch die Filter in `src/lib/trust.ts` ausgegeben werden.

## Teamprofile

Pflichtfelder vor Veröffentlichung:

1. realer Name und tatsächliche Funktion,
2. freigegebener Kurztext,
3. mindestens ein interner Nachweis in `evidenceRefs`,
4. dokumentierte Einwilligung in `publicationConsentRef`,
5. für jede genannte Qualifikation ein eigener `evidenceRef`,
6. bei einem Foto zusätzlich dokumentierte Bildrechte in `imageRightsRef`.

Nicht zulässig:

- erfundene oder beispielhafte Personen,
- geschätzte Beschäftigungsdauer,
- nicht belegte Berufsbezeichnungen,
- pauschale WHG-, ISO-, VCA-/SCC- oder sonstige Zertifikatsaussagen,
- Bilder ohne Nutzungsrecht.

## Case Studies

Pflichtfelder vor Veröffentlichung:

1. belegte Ausgangssituation,
2. belegte technische Lösung,
3. belegtes Ergebnis,
4. Projektquellen in `evidenceRefs`,
5. dokumentierte Owner-/Projektfreigabe in `publicationApprovalRef`.

Zusätzliche Einzel-Freigaben sind erforderlich für:

- `customerName`: öffentlicher Kundenname,
- `logo`: Kundenlogo,
- `exactLocation`: Werk, Stadt oder genauer Standort,
- `metrics`: Flächen, Sperrzeiten, Kosten, Lebensdauer oder Auditergebnisse,
- `quote`: Kundenstimme und namentliche/funktionale Quellenangabe,
- `images`: Projektbilder und deren Bildrechte.

Ohne die jeweilige Freigabe entfernt die Veröffentlichungsfunktion diese Angaben automatisch.

## Quellenreferenzen

`evidenceRefs`, `publicationConsentRef`, `publicationApprovalRef` und Rechteverweise enthalten keine Secrets oder personenbezogenen Dokumentinhalte. Sie sind interne Pointer auf den freigegebenen Ablageort, zum Beispiel:

- interne Dokument-ID,
- freigegebene Drive-Datei,
- schriftliche Kundenfreigabe,
- Projektdokumentation,
- Bildrechte-/Fotografenfreigabe.

Keine Zugangsdaten, privaten URLs mit Tokens oder Dokumentinhalte in Git committen.

## Veröffentlichungscheck

Vor jedem Eintrag:

- [ ] Fakten mit Originalquelle abgeglichen
- [ ] Status auf `approved` gesetzt
- [ ] Owner-/Personenfreigabe dokumentiert
- [ ] Kundenname, Logo, Standort, Kennzahlen, Zitat und Bilder einzeln bewertet
- [ ] Bildrechte und Alt-Text geprüft
- [ ] keine Betriebsgeheimnisse oder personenbezogenen Daten sichtbar
- [ ] Preview kontrolliert
- [ ] PR-Review abgeschlossen
- [ ] Production-Freigabe separat erteilt

## Initialzustand

`src/data/trustContent.ts` bleibt leer, bis reale freigegebene Inhalte vorliegen. Es werden keine Demo-Datensätze veröffentlicht. Die bestehende Referenzlogik in `src/data/references.ts` bleibt davon unabhängig und weiterhin maßgeblich für bereits freigegebene oder anonymisierte Referenzen.
