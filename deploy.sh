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
[ -f "$DEPLOY/appsscript.json" ] || fail "deploy/appsscript.json fehlt"

# --- 3. Projekt anlegen oder verwenden ------------------------------------
cd "$DEPLOY"
if [ ! -f ".clasp.json" ]; then
  info "Lege gebundenes Apps-Script-Projekt am Sheet an ..."
  clasp create-script \
    --type sheets \
    --title "HSB Sales OS" \
    --parentId "$SHEET_ID" \
    --rootDir "$DEPLOY" \
    || fail "Anlegen fehlgeschlagen. Ist die Apps Script API eingeschaltet?"
else
  info "Vorhandenes Projekt gefunden."
fi

# --- 4. Hochladen ---------------------------------------------------------
info "Lade hoch ..."
clasp push --force || fail "Hochladen fehlgeschlagen"

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
