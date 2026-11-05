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

START_TS=$(date +%s); BUDGET_MIN="${HSB_RUN_BUDGET_MIN:-0}"; MORE=no; RENEWED=0
over_budget() { [[ "$BUDGET_MIN" -gt 0 ]] && (( $(date +%s) - START_TS > BUDGET_MIN * 60 )); }
# Nach einem hart abgebrochenen Lauf bleibt die Versandsperre stehen; ohne unklaren Versand (SENDING) lösen.
if [[ -n "$APPLY" && "${HSB_RELEASE_STALE_LOCK:-}" == "yes" ]]; then
  run hsb_cli.py release-stale-lock --apply
fi
audit "$BASE/audit-1"
run hsb_cli.py dedupe-drafts --audit-dir "$BASE/audit-1" $APPLY
audit "$BASE/audit-2"
# Nur die Gestaltung veraltet: in place mit gleicher Message-ID, ohne CRM-Schreiben, beide Postfächer parallel.
run hsb_cli.py refresh-signature --audit-dir "$BASE/audit-2" $APPLY
[[ -n "$APPLY" ]] && audit "$BASE/audit-2"
for OWNER in JOEL JORDI; do
  if [[ -z "$APPLY" ]]; then
    run hsb_cli.py upgrade-drafts --owner "$OWNER" --variant reparatur --cohort all --limit 100 --audit-dir "$BASE/audit-2"
    continue
  fi
  # Tranchen à 100, bis nichts mehr ausgewählt wird; jede Tranche schreibt Journal und CRM-Readback.
  for i in $(seq 1 100); do
    if over_budget; then echo "[$OWNER] Zeitbudget erreicht, Rest im nächsten Lauf" | tee -a "$LOG"; MORE=yes; break; fi
    run hsb_cli.py upgrade-drafts --owner "$OWNER" --variant reparatur --cohort all --limit 100 \
           --audit-dir "$BASE/audit-2" --apply
    read -r SEL DONE < <(tail -1 "$LOG" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d.get("selected",0), d.get("crm_updated",0))')
    [[ "$SEL" == "0" ]] && { echo "[$OWNER] Tranche $i: 0 erneuert" | tee -a "$LOG"; break; }
    # Stop-on-drift: Dieselben Leads kämen sonst bis zum Budgetende wieder; das andere Postfach ginge leer aus.
    [[ "$DONE" == "0" ]] && { echo "[$OWNER] Tranche $i: kein Fortschritt bei $SEL Auswahl, Postfach endet hier" | tee -a "$LOG"; break; }
    RENEWED=$((RENEWED + DONE))
    echo "[$OWNER] Tranche $i: $DONE erneuert" | tee -a "$LOG"
  done
done
audit "$BASE/audit-3"
echo "Fertig. Erneuert: $RENEWED. Protokoll und Audits: $BASE  (Kundenversand: 0)" | tee -a "$LOG"
# Für die Lauf-Kette: nur bei erschöpftem Zeitbudget und echtem Fortschritt folgt ein weiterer Lauf.
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  [[ "$MORE" == "yes" && "$RENEWED" -gt 0 ]] && echo "more=yes" >> "$GITHUB_OUTPUT" || echo "more=no" >> "$GITHUB_OUTPUT"
fi
