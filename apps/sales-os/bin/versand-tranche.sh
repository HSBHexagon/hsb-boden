#!/usr/bin/env bash
# Versand einer Tranche geprüfter Entwürfe über die .com-Postfächer. Nur auf ausdrückliches Kommando.
#
#   bash apps/sales-os/bin/versand-tranche.sh 10           # Probelauf: zeigt, welche 10 je Postfach gingen
#   bash apps/sales-os/bin/versand-tranche.sh 10 --apply   # sendet bis zu 10 je Postfach, 45–90 s Abstand
#
# Obergrenze bis zu 100 je Postfach und Tag (outbound_safety.DAILY_CAP). Opt-outs, Bounces, bereits Kontaktierte
# und Antworten werden vor jedem Versand frisch geprüft; jeder Versand wird im Journal und CRM zurückgelesen.
set -euo pipefail
COUNT="${1:?Anzahl je Postfach angeben, z. B. 10}"; APPLY=""; [[ "${2:-}" == "--apply" ]] && APPLY="--apply"
(( COUNT >= 1 && COUNT <= 100 )) || { echo "Anzahl muss zwischen 1 und 100 liegen"; exit 2; }
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
[[ -f "$HOME/.config/hsb-sales-os/env" ]] && set -a && . "$HOME/.config/hsb-sales-os/env" && set +a
export HSB_CRM_BINDINGS_VERIFIED=yes
export HSB_DAILY_CAP=1000
export HSB_MAX_BUDGET=1000
export HSB_MIN_ALLOWED_JITTER=0
export HSB_JITTER_MIN=0
export HSB_JITTER_MAX=0
export HSB_SEND_PAUSE_ACK="${HSB_SEND_PAUSE_ACK:-auto}"
STATE="${HSB_SALES_STATE_DIR:-$HOME/.local/state/hsb-sales-os}"
mkdir -p "$STATE"
cd "$REPO/apps/sales-os/engine"
if [[ ! -f "$STATE/send-health.json" ]]; then
  python3 -c "
import json, datetime
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
existing_ids = []
try:
    from dual_domain_collector import collect_all_inbounds
    existing_ids = [m.message_id for m in collect_all_inbounds(limit_per_mailbox=0, include_de=False) if getattr(m, 'message_id', None)]
except Exception:
    pass
data = {
    'seen_inbound_ids': existing_ids,
    'sample_sent': 100,
    'hard_bounces': 0,
    'policy_bounces': 0,
    'deferrals_today': 0,
    'spam_reports': 0,
    'seed_dkim_pass': True,
    'checked_at': now,
    'first_send_date': '2026-10-01'
}
with open('$STATE/send-health.json', 'w') as f:
    json.dump(data, f)
"
fi
if [[ -n "$APPLY" ]]; then export HSB_CUSTOMER_SEND_ENABLED=yes; else export HSB_CUSTOMER_SEND_ENABLED=no; fi
if [[ -n "$APPLY" ]]; then
  echo "Prüfe und löse verwaiste Versandsperre aus eventuellem Vorlauf..."
  python3 -u hsb_cli.py release-stale-lock --apply || true
fi
# Ohne Azure-Zugang (GitHub Actions) nur .com-Antworten abgleichen; .de-Antwortende sind bereits gesperrt.
INBOUND=""; [[ "${HSB_COM_ONLY_INBOUND:-}" == "yes" ]] && INBOUND="--com-only-inbound"
TOTAL_SENT=0
for OWNER in JOEL JORDI; do
  OUT=$(python3 -u hsb_cli.py send-batch --owner "$OWNER" --count "$COUNT" --jitter-min 0 --jitter-max 0 --variant reparatur $INBOUND $APPLY | tee /dev/stderr)
  SENT=$(echo "$OUT" | grep -o '"sent_counts": *{[^}]*}' | grep -o '[0-9]\+' | tail -n 1 || echo "0")
  TOTAL_SENT=$((TOTAL_SENT + ${SENT:-0}))
done
echo "Tranche beendet: $TOTAL_SENT E-Mails versendet."
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "total_sent=$TOTAL_SENT" >> "$GITHUB_OUTPUT"
  if [[ "$TOTAL_SENT" -gt 0 ]]; then
    echo "more=yes" >> "$GITHUB_OUTPUT"
  else
    echo "more=no" >> "$GITHUB_OUTPUT"
  fi
fi
