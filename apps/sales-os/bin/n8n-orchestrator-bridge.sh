#!/usr/bin/env bash
# HSB Sales OS / n8n Orchestrator Bridge
# Brücke zwischen n8n-Workflows und der bestehenden hsb_cli.py / versand-tranche.sh Engine.
#
# Modi:
#   health          Prüft CRM-Leitstand und Postfach-Zustand (Read-Only)
#   preflight <N>   Dry-Run für N Leads je Postfach (KEIN Versand)
#   send-gated <N>  Versand NUR nach grünem Gate und mit Job-Key
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SALES_DIR="$REPO_ROOT/apps/sales-os"
STATE_DIR="${HSB_SALES_STATE_DIR:-$HOME/.local/state/hsb-sales-os}"
mkdir -p "$STATE_DIR"
AUDIT_LOG="$STATE_DIR/n8n_orchestration_audit.log"

log() {
  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "[$ts] $*" | tee -a "$AUDIT_LOG"
}

MODE="${1:-health}"
COUNT="${2:-10}"
JOB_KEY="${3:-job-$(date +%s)}"

log "n8n-Bridge aufgerufen: Mode=$MODE, Count=$COUNT, JobKey=$JOB_KEY"

case "$MODE" in
  health)
    log "Führe Read-Only Health Check aus..."
    cd "$SALES_DIR/engine"
    # Status über hsb_cli abfragen
    python3 hsb_cli.py status | tee -a "$AUDIT_LOG"
    log "Health Check beendet."
    ;;

  preflight)
    log "Führe Dry-Run Preflight für $COUNT Leads je Postfach aus (KEIN Versand)..."
    bash "$SALES_DIR/bin/versand-tranche.sh" "$COUNT" | tee -a "$AUDIT_LOG"
    log "Preflight erfolgreich beendet. Versandmenge war 0 (Dry-Run)."
    ;;

  send-gated)
    # Strikte Sicherheitsgates prüfen
    log "Prüfe Freigabe-Gates vor potentiellem Live-Versand..."
    
    # Gate 1: Betreiber-Freigabe-Flag zwingend erforderlich
    if [[ "${HSB_ALLOW_LIVE_SEND:-no}" != "yes" ]]; then
      log "GATE REJECTED: HSB_ALLOW_LIVE_SEND steht nicht auf 'yes'. Abbruch (Fail-Closed)!"
      exit 1
    fi

    # Gate 2: Leitstand muss 0 Opt-outs und 0 Bounces ohne Sperre haben
    python3 -c "
import sys, os
sys.path.insert(0, '$SALES_DIR/engine/operator_layer')
from crm_common import services, SID
sheets, _ = services('info')
res = sheets.spreadsheets().values().get(spreadsheetId=SID, range=\"'LEITSTAND VISUELL'!B18:B19\").execute()
vals = res.get('values', [])
optouts_unsuppressed = int(vals[0][0]) if len(vals) > 0 and vals[0] else -1
bounces_unsuppressed = int(vals[1][0]) if len(vals) > 1 and vals[1] else -1
if optouts_unsuppressed != 0 or bounces_unsuppressed != 0:
    print(f'GATE FAILED: Leitstand meldet {optouts_unsuppressed} Opt-outs und {bounces_unsuppressed} Bounces ohne Sperre!')
    sys.exit(2)
print('GATE PASSED: 0 Opt-outs ohne Sperre, 0 Bounces ohne Sperre.')
" | tee -a "$AUDIT_LOG"

    log "Alle Gates grün! Starte bestehende Versand-Engine mit JobKey=$JOB_KEY..."
    bash "$SALES_DIR/bin/versand-tranche.sh" "$COUNT" --apply | tee -a "$AUDIT_LOG"
    log "Gated Send beendet."
    ;;

  *)
    echo "Unbekannter Modus: $MODE (erlaubt: health, preflight, send-gated)" >&2
    exit 1
    ;;
esac
