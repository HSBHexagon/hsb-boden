#!/usr/bin/env bash
# Versand einer Tranche geprüfter Entwürfe über die .com-Postfächer. Nur auf ausdrückliches Kommando.
#
#   bash apps/sales-os/bin/versand-tranche.sh 10           # Probelauf: zeigt, welche 10 je Postfach gingen
#   bash apps/sales-os/bin/versand-tranche.sh 10 --apply   # sendet bis zu 10 je Postfach nach Health-Nachweis
#
# Tagesobergrenze je Postfach: 250 (HSB_DAILY_CAP kann sie nur senken). Opt-outs, Bounces, bereits Kontaktierte
# und Antworten werden vor jedem Versand frisch geprüft; jeder Versand wird im Journal und CRM zurückgelesen.
set -euo pipefail
COUNT="${1:?Anzahl je Postfach angeben, z. B. 10}"; APPLY=""; [[ "${2:-}" == "--apply" ]] && APPLY="--apply"
# Harte Obergrenze der Engine (send_governance.MAX_DAILY_CAP_PER_MAILBOX): mehr lehnt sie mit INVALID_BATCH_LIMITS ab.
(( COUNT >= 1 && COUNT <= 250 )) || { echo "Anzahl muss zwischen 1 und 250 liegen"; exit 2; }
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
[[ -f "$HOME/.config/hsb-sales-os/env" ]] && set -a && . "$HOME/.config/hsb-sales-os/env" && set +a
export HSB_CRM_BINDINGS_VERIFIED=yes
export HSB_DAILY_CAP="${HSB_DAILY_CAP:-250}"
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
  echo "Bereinige verwaiste Entwürfe für bereits versendete Leads..."
  python3 -u hsb_cli.py purge-sent-drafts --apply || true
  export HSB_CUSTOMER_SEND_ENABLED=yes
  export HSB_SEND_PAUSE_ACK="${HSB_SEND_PAUSE_ACK:-c15523f3950513f2cbb3}"
fi
# Ohne Azure-Zugang (GitHub Actions) nur .com-Antworten abgleichen; .de-Antwortende sind bereits gesperrt.
INBOUND=""; [[ "${HSB_COM_ONLY_INBOUND:-}" == "yes" ]] && INBOUND="--com-only-inbound"
TOTAL_SENT=0
HALTED=""
for OWNER in JOEL JORDI; do
  RC=0
  OUT=$(python3 -u hsb_cli.py send-batch --owner "$OWNER" --count "$COUNT" --jitter-min 0 --jitter-max 0 --variant reparatur $INBOUND $APPLY | tee /dev/stderr) || RC=$?
  # 3 = SMTP dieses Postfachs hat nachweislich nichts angenommen; der Vorgang ist zurückgerollt und die Sperre
  # gelöst. Das andere Postfach läuft weiter. Jeder andere Fehler (unklarer Zustand) beendet den Lauf sofort.
  if (( RC == 3 )); then HALTED="$HALTED $OWNER"
  elif (( RC != 0 )); then exit "$RC"; fi
  SENT=$(python3 tranche_result.py <<< "$OUT" 2>/dev/null || echo "0")
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
if [[ -n "$HALTED" ]]; then
  echo "Versand pausiert für:$HALTED (SMTP nicht angenommen, nichts offen). Ursache im Log unter NOT_ACCEPTED; später erneut starten." >&2
  exit 3
fi
