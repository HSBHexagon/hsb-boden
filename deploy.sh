#!/usr/bin/env bash
#
# HSB Sales OS - Einbau ins Google Sheet per clasp.
#
# Voraussetzungen (beides einmalig, beides durch DICH):
#   1) Apps Script API aktivieren:
#      https://script.google.com/home/usersettings  -> "Google Apps Script API" AN
#   2) clasp login
#
# Danach genuegt:  ./deploy.sh
#
# Das Skript legt beim ersten Lauf ein an das Sheet gebundenes
# Apps-Script-Projekt an und schiebt Code + Oberflaeche hinein.
# Bei jedem weiteren Lauf aktualisiert es nur noch.

set -euo pipefail

SHEET_ID="1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY="$ROOT/deploy"
SRC="$ROOT/apps_script"

info()  { printf '\033[1m%s\033[0m\n' "$*"; }
fail()  { printf '\033[31mFEHLER: %s\033[0m\n' "$*" >&2; exit 1; }

command -v clasp >/dev/null || fail "clasp fehlt. npm install -g @google/clasp"

# --- 1. Anmeldung pruefen -------------------------------------------------
if ! clasp show-authorized-user 2>/dev/null | grep -qi '@'; then
  cat <<'EOF'
Nicht angemeldet.

Zwei einmalige Schritte, beide im Browser:

  1) Apps Script API einschalten
     https://script.google.com/home/usersettings
     Schalter "Google Apps Script API" auf AN

  2) Anmelden
     clasp login

Danach dieses Skript erneut starten.
EOF
  exit 1
fi

info "Angemeldet als: $(clasp show-authorized-user 2>/dev/null | head -1)"

# --- 2. Quelldateien buendeln --------------------------------------------
info "Buendle Quelldateien ..."
python3 "$ROOT/engine/build_single.py" || fail "Buendeln fehlgeschlagen"

mkdir -p "$DEPLOY"
cp "$SRC/HSB_SALES_OS.gs" "$DEPLOY/HSB_SALES_OS.js"
cp "$SRC/Sidebar.html"    "$DEPLOY/Sidebar.html"
[ -f "$ROOT/deploy_manifest.json" ] || fail "deploy_manifest.json fehlt"

# --- 3. Projekt verwenden -------------------------------------------------
#
# clasp kann sich NICHT selbst an ein bestehendes Sheet binden: seine
# Anmeldung umfasst nur "drive.file", also Zugriff auf Dateien, die es
# selbst erzeugt hat. Ein "clasp create --parentId <fremdes Sheet>"
# scheitert deshalb mit "The caller does not have permission" - und
# "--type sheets" wuerde stattdessen ein neues, leeres Sheet anlegen.
#
# Das gebundene Projekt wird daher EINMALIG im Browser erzeugt
# (Sheet -> Erweiterungen -> Apps Script). Danach kann clasp per
# Apps-Script-API beliebig oft hochladen - dafuer genuegt "script.projects".
#
# Die Skript-ID steht in der Adresszeile des Apps-Script-Editors:
#   https://script.google.com/.../projects/<SCRIPT_ID>/edit
# und gehoert in die Datei SCRIPT_ID neben diesem Skript.

cd "$DEPLOY"
if [ ! -f ".clasp.json" ]; then
  [ -f "$ROOT/SCRIPT_ID" ] || cat <<EOF && [ -f "$ROOT/SCRIPT_ID" ] || exit 1

Es fehlt die Skript-ID des gebundenen Projekts.

Einmalig im Browser:

  1) Sheet oeffnen
     https://docs.google.com/spreadsheets/d/$SHEET_ID/edit
  2) Menue "Erweiterungen" -> "Apps Script"
     (legt ein leeres, an das Sheet gebundenes Projekt an)
  3) Skript-ID aus der Adresszeile kopieren:
     https://script.google.com/.../projects/<SCRIPT_ID>/edit
  4) Hier ablegen:
     echo "<SCRIPT_ID>" > "$ROOT/SCRIPT_ID"

Danach dieses Skript erneut starten.

EOF

  SCRIPT_ID="$(tr -d '[:space:]' < "$ROOT/SCRIPT_ID")"
  [ -n "$SCRIPT_ID" ] || fail "SCRIPT_ID ist leer."
  info "Verwende bestehendes Projekt: $SCRIPT_ID"
  cat > .clasp.json <<EOF
{
  "scriptId": "$SCRIPT_ID",
  "rootDir": "$DEPLOY",
  "scriptExtensions": [".js", ".gs"],
  "htmlExtensions": [".html"],
  "jsonExtensions": [".json"]
}
EOF
else
  info "Vorhandenes Projekt gefunden: $(python3 -c "import json;print(json.load(open('.clasp.json'))['scriptId'])")"
fi

# --- 3c. Eigenes Manifest durchsetzen -------------------------------------
# clasp klont beim Anlegen das Standardmanifest der Serverseite und
# ueberschreibt dabei ein vorhandenes appsscript.json. Deshalb wird es
# hier NACH dem Anlegen und VOR dem Hochladen wiederhergestellt.
cp "$ROOT/deploy_manifest.json" "$DEPLOY/appsscript.json"

# --- 4. Hochladen ---------------------------------------------------------
info "Lade hoch ..."
clasp push --force || fail "Hochladen fehlgeschlagen"

# --- 5. Ergebnis pruefen --------------------------------------------------
TZ_UP="$(python3 -c "import json;print(json.load(open('appsscript.json'))['timeZone'])")"
[ "$TZ_UP" = "Europe/Berlin" ] || fail "Zeitzone im Manifest ist $TZ_UP"
info "Manifest korrekt: Europe/Berlin, eigene OAuth-Scopes."

info ""
info "Fertig."
cat <<EOF

Naechste Schritte im Browser:

  1) Sheet neu laden
     https://docs.google.com/spreadsheets/d/$SHEET_ID/edit

  2) Menue "HSB Sales OS" -> "Spalten pruefen / ergaenzen"
     (fragt einmalig nach Berechtigungen)

  3) Menue "HSB Sales OS" -> "Flyer-Pruefung (Asset-Gate)"
     Erwartet: OK JORDI / OK JOEL

  4) Menue "HSB Sales OS" -> "Sales OS oeffnen"
     Erster Lauf mit N = 5, nicht mit 100.

EOF
