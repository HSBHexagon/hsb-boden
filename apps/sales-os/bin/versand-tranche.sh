#!/usr/bin/env bash
# Versand einer Tranche geprüfter Entwürfe über die .com-Postfächer. Nur auf ausdrückliches Kommando.
#
#   bash apps/sales-os/bin/versand-tranche.sh 10           # Probelauf: zeigt, welche 10 je Postfach gingen
#   bash apps/sales-os/bin/versand-tranche.sh 10 --apply   # sendet bis zu 10 je Postfach, 45–90 s Abstand
#
# Obergrenze 35 je Postfach und Tag (outbound_safety.DAILY_CAP). Opt-outs, Bounces, bereits Kontaktierte
# und Antworten werden vor jedem Versand frisch geprüft; jeder Versand wird im Journal und CRM zurückgelesen.
set -euo pipefail
COUNT="${1:?Anzahl je Postfach angeben, z. B. 10}"; APPLY=""; [[ "${2:-}" == "--apply" ]] && APPLY="--apply"
(( COUNT >= 1 && COUNT <= 35 )) || { echo "Anzahl muss zwischen 1 und 35 liegen"; exit 2; }
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
[[ -f "$HOME/.config/hsb-sales-os/env" ]] && set -a && . "$HOME/.config/hsb-sales-os/env" && set +a
export HSB_CRM_BINDINGS_VERIFIED=yes
if [[ -n "$APPLY" ]]; then export HSB_CUSTOMER_SEND_ENABLED=yes; else export HSB_CUSTOMER_SEND_ENABLED=no; fi
cd "$REPO/apps/sales-os/engine"
# Ohne Azure-Zugang (GitHub Actions) nur .com-Antworten abgleichen; .de-Antwortende sind bereits gesperrt.
INBOUND=""; [[ "${HSB_COM_ONLY_INBOUND:-}" == "yes" ]] && INBOUND="--com-only-inbound"
for OWNER in JOEL JORDI; do
  python3 -u hsb_cli.py send-batch --owner "$OWNER" --count "$COUNT" --variant reparatur $INBOUND $APPLY
done
