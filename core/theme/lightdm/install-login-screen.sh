#!/bin/bash
set -e

# ==============================================================================
# FLOWORK OS - SOVEREIGN LOGIN SCREEN (DISPLAY MANAGER) INSTALLER
# Territory: /opt/floworkos
# Customizes LightDM and Slick Greeter for 100% pure Flowork OS branding.
# ==============================================================================

BASE_DIR="/opt/floworkos"
THEME_DIR="$BASE_DIR/theme/lightdm"

echo "[FLOWORK OS] 🚀 Installing Sovereign Login Screen Branding..."

# 1. Install Wallpaper to system directory
sudo mkdir -p /usr/share/backgrounds/flowork
sudo cp "$BASE_DIR/theme/wallpaper-flowork.png" /usr/share/backgrounds/flowork/wallpaper-flowork.png
sudo chmod 644 /usr/share/backgrounds/flowork/wallpaper-flowork.png

# 2. Install Greeter Logos and Badges
sudo mkdir -p /usr/share/slick-greeter/badges
sudo cp "$THEME_DIR/flowork-logo.png" /usr/share/slick-greeter/badges/flowork-logo.png
sudo cp "$THEME_DIR/flowork-badge.svg" /usr/share/slick-greeter/badges/flowork.svg
sudo cp "$THEME_DIR/flowork-badge.svg" /usr/share/slick-greeter/badges/floworkos.svg
sudo chmod 644 /usr/share/slick-greeter/badges/flowork*

# 3. Configure Slick Greeter
sudo cp "$THEME_DIR/slick-greeter.conf" /etc/lightdm/slick-greeter.conf
sudo chmod 644 /etc/lightdm/slick-greeter.conf

# 4. Configure LightDM Seat Configuration (Sovereign Flowork Session)
sudo tee /etc/lightdm/lightdm.conf.d/99-floworkos.conf > /dev/null << 'EOF'
[Seat:*]
autologin-user=mrflow
autologin-user-timeout=0
user-session=flowork
greeter-session=slick-greeter
EOF
sudo chmod 644 /etc/lightdm/lightdm.conf.d/99-floworkos.conf

# 5. Register Native Flowork Session Desktop Entry
sudo mkdir -p /usr/share/xsessions
sudo cp -f "$BASE_DIR/session/flowork.desktop" /usr/share/xsessions/flowork.desktop
sudo chmod 644 /usr/share/xsessions/flowork.desktop

echo "[FLOWORK OS] ✅ Sovereign Login Screen & Flowork Session successfully configured!"
