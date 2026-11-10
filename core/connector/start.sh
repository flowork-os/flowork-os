#!/bin/bash
# MrFlow Sovereign Connector & GUI Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${CONNECTOR_PORT:-9099}

echo "=========================================================="
echo "⚡ Starting MrFlow Sovereign Connector & Account Matrix..."
echo "📡 Server Port: http://127.0.0.1:$PORT"
echo "🎨 GUI Address: http://127.0.0.1:$PORT/gui"
echo "=========================================================="

# Check if port 9099 is already listening
PID_OCCUPIED=$(lsof -ti :$PORT 2>/dev/null)
if [ -n "$PID_OCCUPIED" ]; then
    echo "⚠️ Port $PORT is already in use by PID $PID_OCCUPIED."
    echo "Stopping previous connector process..."
    kill -9 $PID_OCCUPIED 2>/dev/null || true
    sleep 1
fi

# Launch browser if DISPLAY is present
if [ -n "$DISPLAY" ]; then
    (
        sleep 1.5
        if which google-chrome >/dev/null 2>&1; then
            google-chrome "http://127.0.0.1:$PORT/gui" >/dev/null 2>&1 &
        elif which xdg-open >/dev/null 2>&1; then
            xdg-open "http://127.0.0.1:$PORT/gui" >/dev/null 2>&1 &
        fi
    ) &
fi

# Run Compiled Binary if present, otherwise node
if [ -x "$SCRIPT_DIR/bin/flowork-connector" ]; then
    exec "$SCRIPT_DIR/bin/flowork-connector"
elif [ -x "$SCRIPT_DIR/bin/flowork-connector.bin" ]; then
    exec "$SCRIPT_DIR/bin/flowork-connector.bin"
else
    exec node "$SCRIPT_DIR/server/index.js"
fi
