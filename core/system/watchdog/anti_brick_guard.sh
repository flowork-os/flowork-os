#!/bin/bash
# =============================================================================
# 👑 FLOWORK OS — ANTI-BRICK WATCHDOG & BOOT RECOVERY GUARD
# Ensures consecutive boot failures trigger automated instant rollback.
# =============================================================================

STATE_FILE="${HOME}/.local/share/flowork/snapshots/boot_guard.env"
MAX_ATTEMPTS=2
ROLLBACK_BIN="/opt/floworkos/bin/flowork-rollback"

mkdir -p "$(dirname "$STATE_FILE")"

load_state() {
    if [ -f "$STATE_FILE" ]; then
        # shellcheck disable=SC1090
        source "$STATE_FILE"
    else
        BOOT_FAIL_COUNT=0
        LAST_SUCCESS_TS="never"
    fi
    case "${BOOT_FAIL_COUNT:-}" in
        ''|*[!0-9]*) BOOT_FAIL_COUNT=0 ;;
    esac
}

save_state() {
    local tmp_state
    tmp_state="$(mktemp "$(dirname "$STATE_FILE")/.boot_guard.XXXXXX")"
    cat <<EOF > "$tmp_state"
BOOT_FAIL_COUNT=${BOOT_FAIL_COUNT:-0}
LAST_SUCCESS_TS="${LAST_SUCCESS_TS:-$(date +%s)}"
EOF
    mv -f "$tmp_state" "$STATE_FILE"
}

case "${1:-}" in
    --check)
        load_state
        BOOT_FAIL_COUNT=$((BOOT_FAIL_COUNT + 1))
        save_state
        if [ "$BOOT_FAIL_COUNT" -gt "$MAX_ATTEMPTS" ]; then
            echo "[GUARD] Consecutive boot failures detected ($BOOT_FAIL_COUNT > $MAX_ATTEMPTS). Triggering auto-rollback..."
            if "$ROLLBACK_BIN" latest; then
                BOOT_FAIL_COUNT=0
                save_state
                exit 2
            else
                echo "[GUARD] Auto-rollback failed; retaining BOOT_FAIL_COUNT=$BOOT_FAIL_COUNT." >&2
                exit 1
            fi
        fi
        echo "[GUARD] Boot attempt $BOOT_FAIL_COUNT/$MAX_ATTEMPTS recorded."
        ;;
    --success)
        BOOT_FAIL_COUNT=0
        LAST_SUCCESS_TS="$(date +%s)"
        save_state
        echo "[GUARD] Desktop session initialized successfully. Boot failure counter reset to 0."
        ;;
    --fail)
        load_state
        BOOT_FAIL_COUNT=$((BOOT_FAIL_COUNT + 1))
        save_state
        echo "[GUARD] Explicit boot failure recorded. Count=$BOOT_FAIL_COUNT."
        ;;
    --status)
        load_state
        echo "Flowork Boot Guard Status:"
        echo " - Current Fail Count : $BOOT_FAIL_COUNT / $MAX_ATTEMPTS"
        echo " - State File         : $STATE_FILE"
        ;;
    *)
        echo "Usage: $0 {--check | --success | --fail | --status}"
        exit 1
        ;;
esac
exit 0
