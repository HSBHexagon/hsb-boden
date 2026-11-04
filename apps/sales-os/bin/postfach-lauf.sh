#!/usr/bin/env bash
# Kompletter Postfach-Lauf auf dem Mac: Audit -> Dubletten archivieren -> Audit -> Entwürfe auf
# Reparatur-Fassung erneuern -> Abschluss-Audit. Sendet NICHTS. Bricht beim ersten Fehler ab.
#
#   bash apps/sales-os/bin/postfach-lauf.sh            # nur Probelauf (Dry-Run), zeigt die Zahlen
#   bash apps/sales-os/bin/postfach-lauf.sh --apply    # Änderungen in den Postfächern durchführen
#
# Voraussetzungen: HSB_COM_JOEL_USER/PASS, HSB_COM_JORDI_USER/PASS und Google-Zugang
# (~/.config/google-workspace-mcp). Optional werden sie aus ~/.config/hsb-sales-os/env geladen.
set -euo pipefail
APPLY=""; [[ "${1:-}" == "--apply" ]] && APPLY="--apply"
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
ENGINE="$REPO/apps/sales-os/engine"
[[ -f "$HOME/.config/hsb-sales-os/env" ]] && set -a && . "$HOME/.config/hsb-sales-os/env" && set +a
for v in HSB_COM_JOEL_USER HSB_COM_JOEL_PASS HSB_COM_JORDI_USER HSB_COM_JORDI_PASS; do
  [[ -n "${!v:-}" ]] || { echo "FEHLT: $v (Postfach-Zugang)"; exit 2; }
done
[[ -f "$HOME/.config/google-workspace-mcp/credentials.json" ]] || { echo "FEHLT: Google-Zugang"; exit 2; }
export HSB_CRM_BINDINGS_VERIFIED=yes HSB_CUSTOMER_SEND_ENABLED=no
STAMP="$(date +%Y%m%d-%H%M%S)"; BASE="$HOME/KI-System/07_Logs/hsb-sales-os-$STAMP"
mkdir -p "$BASE"; chmod 700 "$BASE"; LOG="$BASE/lauf.log"
cd "$ENGINE"
run() { echo "== $*" | tee -a "$LOG"; python3 "$@" 2>&1 | tee -a "$LOG"; }

run sales_reconciliation.py --output "$BASE/audit-1"
run hsb_cli.py dedupe-drafts --audit-dir "$BASE/audit-1" $APPLY
run sales_reconciliation.py --output "$BASE/audit-2"
for OWNER in JOEL JORDI; do
  if [[ -z "$APPLY" ]]; then
    run hsb_cli.py upgrade-drafts --owner "$OWNER" --variant reparatur --cohort all --limit 10000 --audit-dir "$BASE/audit-2"
    continue
  fi
  # Tranchen à 100, bis nichts mehr ausgewählt wird; jede Tranche schreibt Journal und CRM-Readback.
  for i in $(seq 1 100); do
    OUT="$(python3 hsb_cli.py upgrade-drafts --owner "$OWNER" --variant reparatur --cohort all --limit 100 \
           --audit-dir "$BASE/audit-2" --apply 2>&1 | tee -a "$LOG")"
    SEL="$(printf '%s\n' "$OUT" | tail -1 | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("selected",0))')"
    echo "[$OWNER] Tranche $i: $SEL erneuert" | tee -a "$LOG"
    [[ "$SEL" == "0" ]] && break
  done
done
run sales_reconciliation.py --output "$BASE/audit-3"
echo "Fertig. Protokoll und Audits: $BASE  (Kundenversand: 0)" | tee -a "$LOG"
