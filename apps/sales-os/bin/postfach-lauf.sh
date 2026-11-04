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
# Zugang entweder als GitHub-Secrets (HSB_MAILBOX_CONFIG_JSON, HSB_GOOGLE_AUTHORIZED_USER_JSON) oder lokal.
if [[ -z "${HSB_MAILBOX_CONFIG_JSON:-}" ]]; then
  for v in HSB_COM_JOEL_USER HSB_COM_JOEL_PASS HSB_COM_JORDI_USER HSB_COM_JORDI_PASS; do
    [[ -n "${!v:-}" ]] || { echo "FEHLT: $v (Postfach-Zugang)"; exit 2; }
  done
fi
[[ -n "${HSB_GOOGLE_AUTHORIZED_USER_JSON:-}" || -f "$HOME/.config/google-workspace-mcp/credentials.json" ]] \
  || { echo "FEHLT: Google-Zugang"; exit 2; }
export HSB_CRM_BINDINGS_VERIFIED=yes HSB_CUSTOMER_SEND_ENABLED=no
STAMP="$(date +%Y%m%d-%H%M%S)"; BASE="${HSB_RUN_DIR:-$HOME/KI-System/07_Logs}/hsb-sales-os-$STAMP"
mkdir -p "$BASE"; chmod 700 "$BASE"; LOG="$BASE/lauf.log"
cd "$ENGINE"
# Volle Ausgabe nur ins private Protokoll; auf dem Bildschirm (und im CI-Log) nur Zahlen.
counts() { python3 -c 'import json,sys
for line in sys.stdin:
    line=line.strip()
    try: d=json.loads(line)
    except ValueError: continue
    if isinstance(d,dict):
        d.pop("selected_lead_ids",None); print(json.dumps(d,ensure_ascii=False,default=str))'; }
run() { echo "== $*" | tee -a "$LOG"; python3 -u "$@" >>"$LOG" 2>&1 || { echo "FEHLER in: $* (Details: $LOG)"; tail -5 "$LOG" | grep -iv "@" ; exit 1; }; tail -1 "$LOG" | counts; }
audit() { run sales_reconciliation.py --output "$1"; python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1])),ensure_ascii=False,default=str))' "$1/summary.json"; }

audit "$BASE/audit-1"
run hsb_cli.py dedupe-drafts --audit-dir "$BASE/audit-1" $APPLY
audit "$BASE/audit-2"
for OWNER in JOEL JORDI; do
  if [[ -z "$APPLY" ]]; then
    run hsb_cli.py upgrade-drafts --owner "$OWNER" --variant reparatur --cohort all --limit 10000 --audit-dir "$BASE/audit-2"
    continue
  fi
  # Tranchen à 100, bis nichts mehr ausgewählt wird; jede Tranche schreibt Journal und CRM-Readback.
  for i in $(seq 1 100); do
    run hsb_cli.py upgrade-drafts --owner "$OWNER" --variant reparatur --cohort all --limit 100 \
           --audit-dir "$BASE/audit-2" --apply
    SEL="$(tail -1 "$LOG" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("selected",0))')"
    echo "[$OWNER] Tranche $i: $SEL erneuert" | tee -a "$LOG"
    [[ "$SEL" == "0" ]] && break
  done
done
audit "$BASE/audit-3"
echo "Fertig. Protokoll und Audits: $BASE  (Kundenversand: 0)" | tee -a "$LOG"
