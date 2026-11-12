#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Active Shell Trigger: System Telemetry Watchdog
# =============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/.pid"
LAST_ALERT="$DIR/.last_alert"
SIGNAL_FILE="/tmp/flowork_active_trigger.json"

cleanup_pid() {
  rm -f "$PID_FILE"
  exit 0
}
trap cleanup_pid INT TERM

echo $$ > "$PID_FILE"

while true; do
  RAM_USAGE=$(free | awk '/Mem:/ {if ($2 > 0) printf("%.0f", $3/$2 * 100); else print 0}')
  DISK_USAGE=$(df -P / | awk 'NR==2 {print $5}' | tr -d '%')
  case "$RAM_USAGE" in ''|*[!0-9]*) RAM_USAGE=0 ;; esac
  case "$DISK_USAGE" in ''|*[!0-9]*) DISK_USAGE=0 ;; esac

  NOW=$(date +%s)
  LAST=0
  if [ -f "$LAST_ALERT" ]; then
    LAST=$(cat "$LAST_ALERT" 2>/dev/null || echo 0)
    case "$LAST" in ''|*[!0-9]*) LAST=0 ;; esac
  fi
  DIFF=$((NOW - LAST))

  if [ "$RAM_USAGE" -ge 90 ] || [ "$DISK_USAGE" -ge 92 ]; then
    if [ "$DIFF" -ge 300 ]; then
      TMP_ALERT=$(mktemp "$DIR/.last_alert.XXXXXX")
      echo "$NOW" > "$TMP_ALERT" && mv -f "$TMP_ALERT" "$LAST_ALERT"
      TMP_SIG=$(mktemp "$(dirname "$SIGNAL_FILE")/.sig_systel.XXXXXX")
      cat << JSON > "$TMP_SIG"
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
      chmod 644 "$TMP_SIG" 2>/dev/null || true
      mv -f "$TMP_SIG" "$SIGNAL_FILE"
      echo "[ACTIVE_TRIGGER:system_telemetry] Alert dispatched: RAM ${RAM_USAGE}%, Disk ${DISK_USAGE}%"
    fi
  fi

  sleep 15
done
