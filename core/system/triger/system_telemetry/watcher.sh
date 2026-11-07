#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Active Shell Trigger: System Telemetry Watchdog
# =============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/.pid"
LAST_ALERT="$DIR/.last_alert"
SIGNAL_FILE="/tmp/flowork_active_trigger.json"

echo $$ > "$PID_FILE"

while true; do
  RAM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')
  DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

  NOW=$(date +%s)
  LAST=0
  [ -f "$LAST_ALERT" ] && LAST=$(cat "$LAST_ALERT" 2>/dev/null || echo 0)
  DIFF=$((NOW - LAST))

  if [ "$RAM_USAGE" -ge 90 ] || [ "$DISK_USAGE" -ge 92 ]; then
    if [ "$DIFF" -ge 300 ]; then
      echo "$NOW" > "$LAST_ALERT"
      cat << JSON > "$SIGNAL_FILE"
{
  "active": true,
  "source": "system_telemetry",
  "timestamp": $NOW,
  "telemetry": {
    "ram_percent": $RAM_USAGE,
    "disk_percent": $DISK_USAGE
  },
  "instruction": "System telemetry breach: RAM ${RAM_USAGE}% or Disk ${DISK_USAGE}% threshold exceeded. Investigate high memory consumers."
}
JSON
      echo "[ACTIVE_TRIGGER:system_telemetry] Alert dispatched: RAM ${RAM_USAGE}%, Disk ${DISK_USAGE}%"
    fi
  fi

  sleep 15
done
