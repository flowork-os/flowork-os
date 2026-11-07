#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Quantum Glass Sovereign Theme Manager
# 100% Bespoke Sovereign Architecture — Zero Apple, Zero Windows
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

THEME_NAME="Flowork-Quantum-Glass"
ICON_THEME="Papirus-Dark"
CURSOR_THEME="breeze_cursors"
FONT_NAME="Inter 10"
WALLPAPER="/opt/floworkos/theme/flowork-quantum-wallpaper.png"

apply_theme() {
  echo "=========================================================="
  echo "⚡ APPLYING FLOWORK SOVEREIGN QUANTUM GLASS THEME ($THEME_NAME)"
  echo "=========================================================="

  # 1. Synthesize & Ensure XFWM4 and GTK Themes exist
  if [ ! -d "$HOME/.themes/Flowork-Quantum-Glass/xfwm4" ]; then
    python3 /opt/floworkos/theme/generate-xfwm4-theme.py
  fi

  # 2. Standalone Window Manager (xfwm4)
  if command -v xfconf-query >/dev/null 2>&1; then
    xfconf-query -c xfwm4 -p /general/theme -s "$THEME_NAME" --create -t string 2>/dev/null || true
    xfconf-query -c xfwm4 -p /general/button_layout -s "|HMC" --create -t string 2>/dev/null || true
    xfconf-query -c xfwm4 -p /general/title_font -s "JetBrains Mono Bold 10" --create -t string 2>/dev/null || true
    xfconf-query -c xfwm4 -p /general/use_compositing -s true --create -t bool 2>/dev/null || true
  fi

  # 3. XSettings Daemon & GTK3/GTK4 configs
  mkdir -p "$HOME/.config/gtk-3.0" "$HOME/.config/xsettingsd"
  cat << EOF_GTK > "$HOME/.config/gtk-3.0/settings.ini"
[Settings]
gtk-theme-name=$THEME_NAME
gtk-icon-theme-name=$ICON_THEME
gtk-cursor-theme-name=$CURSOR_THEME
gtk-font-name=$FONT_NAME
gtk-application-prefer-dark-theme=1
gtk-button-images=1
gtk-menu-images=1
gtk-enable-event-sounds=0
gtk-enable-input-feedback-sounds=0
gtk-xft-antialias=1
gtk-xft-hinting=1
gtk-xft-hintstyle=hintslight
gtk-xft-rgba=rgb
gtk-decoration-layout=:minimize,maximize,close
EOF_GTK

  cat << EOF_XSET > "$HOME/.config/xsettingsd/xsettingsd.conf"
Net/ThemeName "$THEME_NAME"
Net/IconThemeName "$ICON_THEME"
Gtk/CursorThemeName "$CURSOR_THEME"
Gtk/FontName "$FONT_NAME"
Net/EnableEventSounds 0
Net/EnableInputFeedbackSounds 0
Xft/Antialias 1
Xft/Hinting 1
Xft/HintStyle "hintslight"
Xft/RGBA "rgb"
Gtk/DecorationLayout ":minimize,maximize,close"
EOF_XSET

  # 4. Reload xsettingsd
  pkill -HUP xsettingsd 2>/dev/null || true

  # 5. Plank Dock Theme
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ theme "Flowork-Modern" 2>/dev/null || true

  # 6. Apply Sovereign Wallpaper
  if [ -f "$WALLPAPER" ]; then
    feh --bg-fill "$WALLPAPER" 2>/dev/null || python3 /opt/floworkos/theme/set-root-wallpaper.py "$WALLPAPER" 2>/dev/null || true
  fi

  echo "✅ Flowork Sovereign Quantum Glass Theme applied successfully."
}

case "$1" in
  --status|-s)
    echo "=========================================================="
    echo "📊 CURRENT FLOWORK THEME STATUS"
    echo "=========================================================="
    echo "🎨 Active Theme: $THEME_NAME"
    echo "🔘 Icons:        $ICON_THEME"
    echo "🖼️ Wallpaper:    $WALLPAPER"
    echo "=========================================================="
    ;;
  *)
    apply_theme
    ;;
esac
