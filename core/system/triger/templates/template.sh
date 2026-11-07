#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Active Shell Trigger Daemon Template
# =============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/.pid"
LAST_ALERT="$DIR/.last_alert"
SIGNAL_FILE="/tmp/flowork_active_trigger.json"

echo $$ > "$PID_FILE"

INTERVAL_SECONDS=10
COOLDOWN_SECONDS=180

while true; do
  # --- 1. Probe Telemetry ---
  CONDITION_BREACHED=0 # Set to 1 if metric exceeds threshold

  # --- 2. Check Debounce & Dispatch ---
  if [ "$CONDITION_BREACHED" -eq 1 ]; then
    NOW=$(date +%s)
    LAST=0
    [ -f "$LAST_ALERT" ] && LAST=$(cat "$LAST_ALERT" 2>/dev/null || echo 0)
    DIFF=$((NOW - LAST))

    if [ "$DIFF" -ge "$COOLDOWN_SECONDS" ]; then
      echo "$NOW" > "$LAST_ALERT"
      cat << JSON > "$SIGNAL_FILE"
{
  "active": true,
  "source": "custom_shell_trigger",
  "timestamp": $NOW,
  "telemetry": {},
  "instruction": "Threshold condition breached."
}
JSON
      echo "[ACTIVE_TRIGGER] Alert dispatched to Flowork Agent"
    fi
  fi

  sleep "$INTERVAL_SECONDS"
done
