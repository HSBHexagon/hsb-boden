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
  health|reconcile|preflight|send-gated)
    log "Starte n8n_orchestrator.py (Mode=$MODE, Count=$COUNT, JobKey=$JOB_KEY)..."
    python3 "$SALES_DIR/engine/n8n_orchestrator.py" \
      --mode "$MODE" \
      --count "$COUNT" \
      --job-key "$JOB_KEY" | tee -a "$AUDIT_LOG"
    log "n8n_orchestrator.py erfolgreich beendet (Mode=$MODE, JobKey=$JOB_KEY)."
    ;;

  *)
    echo "Unbekannter Modus: $MODE (erlaubt: health, reconcile, preflight, send-gated)" >&2
    exit 1
    ;;
esac
