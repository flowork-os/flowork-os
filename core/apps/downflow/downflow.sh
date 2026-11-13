#!/usr/bin/env bash
# ==============================================================================
# 👑 FLOWORK OS — Download Manager (DownFlow Sovereign Accelerator)
# ==============================================================================

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

BIN="/opt/floworkos/apps/downflow/misterdownloadmanager"

if [ ! -x "$BIN" ]; then
    echo "Error: Download Manager binary not found at $BIN" >&2
    exit 1
fi

# Background watcher to ensure clean X11 window title without "Mister"
(
    for _ in {1..30}; do
        sleep 0.2
        WIDS=$(xdotool search --class misterdownloadmanager 2>/dev/null || true)
        for WID in $WIDS; do
            NAME=$(xdotool getwindowname "$WID" 2>/dev/null || true)
            if [[ "$NAME" == *"Mister Download Manager"* ]]; then
                NEW_NAME="${NAME//Mister Download Manager 0.5.2/Download Manager}"
                NEW_NAME="${NEW_NAME//Mister Download Manager/Download Manager}"
                xdotool set_window --name "$NEW_NAME" "$WID" 2>/dev/null || true
            fi
        done
    done
) &

exec "$BIN" "$@"
