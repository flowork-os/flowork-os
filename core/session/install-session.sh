#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Session Installer & Registrar
# Registers Flowork OS in display manager and ensures sovereign desktop registration
# Universal Linux FHS Standard | 100% User Agnostic
# =============================================================================
set -e

SESSION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "$SESSION_DIR/.." && pwd)"
TARGET_DESKTOP="/usr/share/xsessions/flowork.desktop"
CURRENT_USER="${SUDO_USER:-$USER}"
TARGET_HOME=$(getent passwd "$CURRENT_USER" | cut -d: -f6 || echo "$HOME")

case "$1" in
  --uninstall|-u)
    echo "🗑️ Removing Flowork OS session entry from /usr/share/xsessions/..."
    sudo rm -f "$TARGET_DESKTOP" /usr/local/bin/flowork-session
    echo "✅ Flowork OS session entry removed cleanly."
    ;;
  *)
    echo "=========================================================="
    echo "📦 REGISTERING FLOWORK OS DESKTOP SESSION"
    echo "🎯 Target File: $TARGET_DESKTOP"
    echo "👤 User Context: $CURRENT_USER ($TARGET_HOME)"
    echo "=========================================================="

    # 1. Clean and suppress non-Flowork sessions
    for s in /usr/share/xsessions/*.desktop; do
      if [ -f "$s" ] && [ "$(basename "$s")" != "flowork.desktop" ]; then
        if ! grep -q "NoDisplay=true" "$s"; then
          echo "NoDisplay=true" | sudo tee -a "$s" > /dev/null
        fi
      fi
    done

    # 2. Install Universal Session Runner
    sudo tee /usr/local/bin/flowork-session > /dev/null << 'EOF'
#!/usr/bin/env bash
if [ -x "/opt/floworkos/session/flowork-session.sh" ]; then
  exec "/opt/floworkos/session/flowork-session.sh" "$@"
elif [ -x "$HOME/floworkos/session/flowork-session.sh" ]; then
  exec "$HOME/floworkos/session/flowork-session.sh" "$@"
else
  SESSION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../session" && pwd)"
  if [ -x "$SESSION_DIR/flowork-session.sh" ]; then
    exec "$SESSION_DIR/flowork-session.sh" "$@"
  else
    echo "Error: Flowork OS session runner not found." >&2
    exit 1
  fi
fi
EOF
    sudo chmod 755 /usr/local/bin/flowork-session

    # 3. Install System Icon
    sudo mkdir -p /usr/share/icons/flowork
    if [ -f "$SOURCE_ROOT/theme/Flowork-OS/flowork/flowork-logo.svg" ]; then
      sudo cp -f "$SOURCE_ROOT/theme/Flowork-OS/flowork/flowork-logo.svg" /usr/share/icons/flowork/flowork-logo.svg
      sudo chmod 644 /usr/share/icons/flowork/flowork-logo.svg
    fi

    # 4. Register Native Flowork OS session
    sudo cp -f "$SESSION_DIR/flowork.desktop" "$TARGET_DESKTOP"
    sudo chmod 644 "$TARGET_DESKTOP"

    # 5. Install Greeter badges
    sudo mkdir -p /usr/share/slick-greeter/badges
    if [ -f "$SOURCE_ROOT/theme/lightdm/flowork-badge.svg" ]; then
      sudo cp -f "$SOURCE_ROOT/theme/lightdm/flowork-badge.svg" /usr/share/slick-greeter/badges/flowork.svg
      sudo cp -f "$SOURCE_ROOT/theme/lightdm/flowork-badge.svg" /usr/share/slick-greeter/badges/floworkos.svg
      sudo chmod 644 /usr/share/slick-greeter/badges/flowork*
    fi

    # 6. Set default session to Flowork in LightDM
    sudo mkdir -p /etc/lightdm/lightdm.conf.d
    sudo tee /etc/lightdm/lightdm.conf.d/99-floworkos.conf > /dev/null << EOF
[Seat:*]
autologin-user=$CURRENT_USER
autologin-user-timeout=0
user-session=flowork
greeter-session=slick-greeter
EOF
    sudo chmod 644 /etc/lightdm/lightdm.conf.d/99-floworkos.conf

    # 7. Set user cached session in AccountsService & ~/.dmrc
    ACT_FILE="/var/lib/AccountsService/users/$CURRENT_USER"
    if [ -f "$ACT_FILE" ]; then
      sudo sed -i 's/^XSession=.*/XSession=flowork/' "$ACT_FILE"
    fi
    if [ -d "$TARGET_HOME" ]; then
      cat << 'EOF_DMRC' > "$TARGET_HOME/.dmrc"
[Desktop]
Session=flowork
EOF_DMRC
      chmod 644 "$TARGET_HOME/.dmrc"
      chown "$CURRENT_USER:$CURRENT_USER" "$TARGET_HOME/.dmrc" 2>/dev/null || true
    fi

    echo "✅ Flowork OS session registered & collision resolved successfully!"
    echo "ℹ️  Default session set to 'flowork' for user $CURRENT_USER."
    ;;
esac
