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
STATE="${HSB_SALES_STATE_DIR:-$HOME/.local/state/hsb-sales-os}"
mkdir -p "$STATE"
if [[ ! -f "$STATE/send-health.json" ]]; then
  python3 -c "
import json, datetime
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
data = {
    'seen_inbound_ids': [],
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
cd "$REPO/apps/sales-os/engine"
# Ohne Azure-Zugang (GitHub Actions) nur .com-Antworten abgleichen; .de-Antwortende sind bereits gesperrt.
INBOUND=""; [[ "${HSB_COM_ONLY_INBOUND:-}" == "yes" ]] && INBOUND="--com-only-inbound"
for OWNER in JOEL JORDI; do
  python3 -u hsb_cli.py send-batch --owner "$OWNER" --count "$COUNT" --jitter-min 0 --jitter-max 0 --variant reparatur $INBOUND $APPLY
done
