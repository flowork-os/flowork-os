#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Live Xephyr Nested Desktop Session Tester
# Runs the full Flowork OS Desktop Environment inside an isolated sandbox window
# =============================================================================
set -e

SESSION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPLAY_NUM=":2"
RESOLUTION="${1:-1280x700}"

if ! command -v Xephyr >/dev/null 2>&1; then
  echo "❌ [Error] Xephyr not found. Please install xserver-xephyr."
  exit 1
fi

echo "=========================================================="
echo "⚡ FLOWORK OS — NESTED DESKTOP SESSION TEST RUNNER"
echo "🖥️  Target Display: $DISPLAY_NUM"
echo "📐 Resolution:     $RESOLUTION (Compact Notebook Screen)"
echo "🔒 Safety Mode:    100% Isolated inside host sandbox window"
echo "=========================================================="

# Clean up stale locks for this display if any
LOCK_FILE="/tmp/.X${DISPLAY_NUM#:}-lock"
if [ -f "$LOCK_FILE" ]; then
  LOCK_PID="$(cat "$LOCK_FILE" 2>/dev/null | tr -d ' ')"
  if ! kill -0 "$LOCK_PID" 2>/dev/null; then
    rm -f "$LOCK_FILE" "/tmp/.X11-unix/X${DISPLAY_NUM#:}" 2>/dev/null || true
  fi
fi

# 1. Launch Nested X-Server (Xephyr)
export HOST_DISPLAY="${DISPLAY:-:0}"
DISPLAY="$HOST_DISPLAY" Xephyr $DISPLAY_NUM -screen $RESOLUTION -ac -br -reset 2>/dev/null &
XEPHYR_PID=$!

# Wait for nested X-server to be ready
echo "⏳ Waiting for display $DISPLAY_NUM to initialize..."
for i in {1..25}; do
  if xset q -display "$DISPLAY_NUM" >/dev/null 2>&1; then
    echo "✅ Display $DISPLAY_NUM is ready."
    break
  fi
  sleep 0.2
done

# 2. Trap signals to guarantee clean teardown
cleanup() {
  echo ""
  echo "🛑 Terminating nested test session..."
  kill "$SESSION_PID" 2>/dev/null || true
  kill "$XEPHYR_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# 3. Launch the Sovereign Flowork Desktop Session inside Xephyr
echo "🚀 Spawning Flowork Desktop Environment on $DISPLAY_NUM..."
DISPLAY=$DISPLAY_NUM "$SESSION_DIR/flowork-session.sh" &
SESSION_PID=$!

# Ensure resolution stays locked to target notebook resolution
(
  sleep 2
  DISPLAY=$DISPLAY_NUM xrandr -s "$RESOLUTION" 2>/dev/null || true
) &

# 4. Auto-launch welcome terminal window after compositor settles
(
  sleep 3
  if command -v gnome-terminal >/dev/null 2>&1; then
    DISPLAY=$DISPLAY_NUM gnome-terminal --title="Flowork OS Sovereign Terminal" -- bash -c "echo '⚡ FLOWORK OS 1.0 (SOVEREIGN LINUX)'; echo '------------------------------------'; neofetch; exec bash" 2>/dev/null || true
  fi
) &

# Wait for user to close Xephyr window
wait $XEPHYR_PID 2>/dev/null || true
kill $SESSION_PID 2>/dev/null || true
echo "✅ Flowork OS nested session exited cleanly."
