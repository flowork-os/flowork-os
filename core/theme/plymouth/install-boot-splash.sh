#!/bin/bash
set -e

# ==============================================================================
# FLOWORK OS - SOVEREIGN BOOT SPLASH INSTALLER
# Territory: /opt/floworkos
# Installs and locks the Cyber Flowork OS Plymouth boot splash animation.
# ==============================================================================

SRC_DIR="/opt/floworkos/theme/plymouth/flowork-cyber"
TARGET_DIR="/usr/share/plymouth/themes/flowork-cyber"

echo "[FLOWORK OS] 🚀 Installing Sovereign Boot Splash Theme..."

if [ ! -d "$SRC_DIR" ]; then
    echo "[FLOWORK OS] ❌ Error: Source theme directory $SRC_DIR does not exist!"
    exit 1
fi

sudo mkdir -p "$TARGET_DIR"
sudo cp -r "$SRC_DIR"/* "$TARGET_DIR"/
sudo chmod -R 755 "$TARGET_DIR"

echo "[FLOWORK OS] 🔗 Registering theme in update-alternatives..."
sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth "$TARGET_DIR/flowork-cyber.plymouth" 500
sudo update-alternatives --set default.plymouth "$TARGET_DIR/flowork-cyber.plymouth"

echo "[FLOWORK OS] 📦 Rebuilding initramfs image..."
sudo update-initramfs -u

echo "[FLOWORK OS] ✅ Sovereign Boot Splash Theme successfully installed and active!"
update-alternatives --display default.plymouth
