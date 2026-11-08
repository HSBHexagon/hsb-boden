#!/usr/bin/env bash
# Versand einer Tranche geprüfter Entwürfe über die .com-Postfächer. Nur auf ausdrückliches Kommando.
#
#   bash apps/sales-os/bin/versand-tranche.sh 10           # Probelauf: zeigt, welche 10 je Postfach gingen
#   bash apps/sales-os/bin/versand-tranche.sh 10 --apply   # sendet bis zu 10 je Postfach nach Health-Nachweis
#
# Obergrenze bis zu 100 je Postfach und Tag (outbound_safety.DAILY_CAP). Opt-outs, Bounces, bereits Kontaktierte
# und Antworten werden vor jedem Versand frisch geprüft; jeder Versand wird im Journal und CRM zurückgelesen.
set -euo pipefail
COUNT="${1:?Anzahl je Postfach angeben, z. B. 10}"; APPLY=""; [[ "${2:-}" == "--apply" ]] && APPLY="--apply"
(( COUNT >= 1 && COUNT <= 100 )) || { echo "Anzahl muss zwischen 1 und 100 liegen"; exit 2; }
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
[[ -f "$HOME/.config/hsb-sales-os/env" ]] && set -a && . "$HOME/.config/hsb-sales-os/env" && set +a
export HSB_CRM_BINDINGS_VERIFIED=yes
export HSB_DAILY_CAP="${HSB_DAILY_CAP:-100}"
export HSB_MAX_BUDGET="${HSB_MAX_BUDGET:-$HSB_DAILY_CAP}"
export HSB_MIN_ALLOWED_JITTER=0
export HSB_JITTER_MIN=0
export HSB_JITTER_MAX=0
STATE="${HSB_SALES_STATE_DIR:-$HOME/.local/state/hsb-sales-os}"
mkdir -p "$STATE"
cd "$REPO/apps/sales-os/engine"
export HSB_CUSTOMER_SEND_ENABLED=no
if [[ -n "$APPLY" ]]; then
  python3 -c 'import sys; from send_governance import prepare_send_health; prepare_send_health(sys.argv[1])' "$STATE"
  echo "Prüfe und löse verwaiste Versandsperre aus eventuellem Vorlauf..."
  python3 -u hsb_cli.py release-stale-lock --apply
  export HSB_CUSTOMER_SEND_ENABLED=yes
fi
# Ohne Azure-Zugang (GitHub Actions) nur .com-Antworten abgleichen; .de-Antwortende sind bereits gesperrt.
INBOUND=""; [[ "${HSB_COM_ONLY_INBOUND:-}" == "yes" ]] && INBOUND="--com-only-inbound"
TOTAL_SENT=0
for OWNER in JOEL JORDI; do
  OUT=$(python3 -u hsb_cli.py send-batch --owner "$OWNER" --count "$COUNT" --jitter-min 0 --jitter-max 0 --variant reparatur $INBOUND $APPLY | tee /dev/stderr)
  SENT=$(python3 -c "import json, sys; out = sys.stdin.read(); start, end = out.find('{'), out.rfind('}'); data = json.loads(out[start:end+1]) if start != -1 and end != -1 else {}; print(sum(data.get('sent_counts', {}).values()))" <<< "$OUT" 2>/dev/null || echo "0")
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
