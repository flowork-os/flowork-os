#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign Linux OS — Integrated Desktop Session Runner
# Architecture: Pure Standalone Flowork Shell (Xfwm4 + Xfce4-Panel + Plank)
# Ultra-Lightweight, Modern & Blazingly Fast (<50MB RAM Footprint)
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

if [ -z "$FLOWORK_OS_ROOT" ]; then
  if [ -d "/opt/floworkos" ]; then
    FLOWORK_OS_ROOT="/opt/floworkos"
  elif [ -d "$HOME/floworkos" ]; then
    FLOWORK_OS_ROOT="$HOME/floworkos"
  else
    SESSION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    FLOWORK_OS_ROOT="$(cd "$SESSION_DIR/.." && pwd)"
  fi
fi

if [ -d "$HOME/.cargo/bin" ]; then
  export PATH="$FLOWORK_OS_ROOT/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin:$PATH"
else
  export PATH="$FLOWORK_OS_ROOT/bin:$HOME/.local/bin:/usr/local/bin:$PATH"
fi
export FLOWORK_OS_SESSION=1
export FLOWORK_SOVEREIGN=1
export FLOWORK_VERSION="1.0.0"
export XDG_CURRENT_DESKTOP="Flowork"
export XDG_SESSION_DESKTOP="flowork"
export DESKTOP_SESSION="flowork"

# Propagate environment to systemd user session so all services inherit PATH & display vars
systemctl --user import-environment PATH DISPLAY XDG_CURRENT_DESKTOP FLOWORK_OS_ROOT 2>/dev/null || true

# Load Mr. Flow Sovereign Engine Configuration
if [ -f "$FLOWORK_OS_ROOT/system/mrflow.env" ]; then
  # shellcheck disable=SC1090
  source "$FLOWORK_OS_ROOT/system/mrflow.env"
fi

TARGET_DISPLAY="${DISPLAY:-:0}"
echo "=========================================================="
echo "⚡ FLOWORK SOVEREIGN LINUX DESKTOP INITIALIZING"
echo "🖥️  Target Display: $TARGET_DISPLAY"
echo "🔒 Architecture:   Flowork Sovereign Standalone Shell"
echo "=========================================================="

# 2. Configure GTK Theme, Icons, and CSD Decoration Layout
mkdir -p "$HOME/.config/gtk-3.0" "$HOME/.config/xsettingsd"
if [ ! -f "$HOME/.config/gtk-3.0/gtk.css" ] || ! grep -q "scale trough" "$HOME/.config/gtk-3.0/gtk.css" 2>/dev/null; then
  cp -f /usr/share/themes/Flowork-Quantum-Glass/gtk-3.0/gtk.css "$HOME/.config/gtk-3.0/gtk.css" 2>/dev/null || true
fi
cat << 'EOF_GTK3' > "$HOME/.config/gtk-3.0/settings.ini"
[Settings]
gtk-theme-name=Flowork-Quantum-Glass
gtk-icon-theme-name=Flowork-Quantum-Glass
gtk-cursor-theme-name=breeze_cursors
gtk-font-name=Inter 10
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
EOF_GTK3

cat << 'EOF_GTK2' > "$HOME/.gtkrc-2.0"
gtk-theme-name="Flowork-Quantum-Glass"
gtk-icon-theme-name="Flowork-Quantum-Glass"
gtk-font-name="Inter 10"
gtk-cursor-theme-name="breeze_cursors"
EOF_GTK2

cat << 'EOF_XSETTINGS' > "$HOME/.config/xsettingsd/xsettingsd.conf"
Net/ThemeName "Flowork-Quantum-Glass"
Net/IconThemeName "Flowork-Quantum-Glass"
Gtk/CursorThemeName "breeze_cursors"
Gtk/FontName "Inter 10"
Net/EnableEventSounds 0
Net/EnableInputFeedbackSounds 0
Xft/Antialias 1
Xft/Hinting 1
Xft/HintStyle "hintslight"
Xft/RGBA "rgb"
Gtk/DecorationLayout ":minimize,maximize,close"
EOF_XSETTINGS

# 3. Configure Standalone Window Manager (xfwm4 - Flowork Quantum Glass)
FLOWORK_SW_COMPOSITOR=0
FLOWORK_WM_COMP_FLAG="--compositor=off"
XFWM4_USE_COMP="false"
XFWM4_SHADOW="true"
if [ -x "$FLOWORK_OS_ROOT/bin/flowork-compositor" ] && "$FLOWORK_OS_ROOT/bin/flowork-compositor" --is-software >/dev/null 2>&1; then
  FLOWORK_SW_COMPOSITOR=1
  FLOWORK_WM_COMP_FLAG="--compositor=on"
  XFWM4_USE_COMP="true"
  XFWM4_SHADOW="false"
fi

mkdir -p "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml"
cat << EOF_XFWM4 > "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml"
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="Flowork-Quantum-Glass"/>
    <property name="button_layout" type="string" value="|HMC"/>
    <property name="title_alignment" type="string" value="center"/>
    <property name="use_compositing" type="bool" value="${XFWM4_USE_COMP}"/>
    <property name="show_frame_shadow" type="bool" value="${XFWM4_SHADOW}"/>
    <property name="show_popup_shadow" type="bool" value="${XFWM4_SHADOW}"/>
    <property name="box_move" type="bool" value="false"/>
    <property name="box_resize" type="bool" value="false"/>
  </property>
</channel>
EOF_XFWM4

# 4. Configure Modern Top Bar (xfce4-panel - 28px Cupertino style)
cat << 'EOF_PANEL' > "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
    <value type="int" value="1"/>
    <property name="dark-mode" type="bool" value="true"/>
    <property name="panel-1" type="empty">
      <property name="position" type="string" value="p=6;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="icon-size" type="uint" value="18"/>
      <property name="size" type="uint" value="28"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/>
        <value type="int" value="3"/>
        <value type="int" value="4"/>
        <value type="int" value="5"/>
        <value type="int" value="8"/>
        <value type="int" value="9"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="whiskermenu">
      <property name="button-title" type="string" value=""/>
      <property name="button-icon" type="string" value="/usr/share/icons/flowork/flowork-emblem.svg"/>
      <property name="button-single-row" type="bool" value="true"/>
      <property name="launcher-icon-size" type="int" value="3"/>
      <property name="favorites-in-recent" type="bool" value="true"/>
      <property name="position-search-alternate" type="bool" value="true"/>
      <property name="position-commands-alternate" type="bool" value="true"/>
      <property name="position-categories-alternate" type="bool" value="true"/>
      <property name="show-command-shutdown" type="bool" value="true"/>
      <property name="command-shutdown" type="string" value="systemctl poweroff"/>
      <property name="show-command-restart" type="bool" value="true"/>
      <property name="command-restart" type="string" value="systemctl reboot"/>
      <property name="show-command-logout" type="bool" value="true"/>
      <property name="command-logout" type="string" value="flowork-power-menu"/>
      <property name="show-command-suspend" type="bool" value="true"/>
      <property name="command-suspend" type="string" value="systemctl suspend"/>
      <property name="show-command-lockscreen" type="bool" value="true"/>
      <property name="command-lockscreen" type="string" value="xflock4"/>
      <property name="show-command-profile" type="bool" value="true"/>
      <property name="command-profile" type="string" value="/opt/floworkos/bin/flowork-profile"/>
    </property>
    <property name="plugin-2" type="string" value="tasklist">
      <property name="grouping" type="uint" value="1"/>
      <property name="flat-buttons" type="bool" value="true"/>
      <property name="show-labels" type="bool" value="true"/>
      <property name="sort-order" type="uint" value="0"/>
    </property>
    <property name="plugin-3" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-4" type="string" value="clock">
      <property name="digital-layout" type="uint" value="3"/>
      <property name="digital-time-format" type="string" value="%a %b %-d  %-I:%M %p"/>
      <property name="digital-format" type="string" value="%a %b %-d  %-I:%M %p"/>
      <property name="mode" type="uint" value="2"/>
    </property>
    <property name="plugin-5" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-6" type="string" value="launcher">
      <property name="items" type="array">
      </property>
    </property>
    <property name="plugin-8" type="string" value="systray">
      <property name="square-icons" type="bool" value="true"/>
    </property>
    <property name="plugin-9" type="string" value="pulseaudio">
      <property name="enable-keyboard-shortcuts" type="bool" value="true"/>
      <property name="show-notifications" type="bool" value="true"/>
    </property>
    <property name="plugin-10" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="flowork-power-menu.desktop"/>
      </property>
    </property>
  </property>
</channel>
EOF_PANEL

# Configure Top Header Launchers & Whisker Menu
mkdir -p "$HOME/.config/xfce4/panel/launcher-6" "$HOME/.config/xfce4/panel/launcher-10"
rm -rf "$HOME/.config/xfce4/panel/launcher-7" 2>/dev/null || true
cat << 'EOF_LAUNCHER' > "$HOME/.config/xfce4/panel/launcher-10/flowork-power-menu.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Power & Session
GenericName=Session Controls
Comment=Lock, Suspend, Restart or Shut Down Flowork OS
Exec=/usr/local/bin/flowork-power-menu
Icon=system-shutdown-symbolic
Terminal=false
Categories=System;
EOF_LAUNCHER

# Ensure profile manager fallbacks exist for whisker menu
mkdir -p "$HOME/.local/bin"
if [ ! -e "$HOME/.local/bin/mugshot" ]; then
  ln -sf /opt/floworkos/bin/flowork-profile "$HOME/.local/bin/mugshot" 2>/dev/null || true
fi
if [ ! -e "$HOME/.local/bin/flowork-profile" ]; then
  ln -sf /opt/floworkos/bin/flowork-profile "$HOME/.local/bin/flowork-profile" 2>/dev/null || true
fi

cat << 'EOF_WHISKER' > "$HOME/.config/xfce4/panel/whiskermenu-1.rc"
favorites=flowork-cyber-hub.desktop,flowork-stealth.desktop,flowork-connector.desktop,openscreen.desktop,gputaskman.desktop,nemo.desktop,google-chrome.desktop,flowork-settings.desktop,flowork-wallpaper-settings.desktop,code.desktop,flowork-screenshot.desktop
recent=flowork-cyber-hub.desktop,flowork-connector.desktop,nemo.desktop,google-chrome.desktop,flowork-settings.desktop
button-title=
button-icon=/usr/share/icons/flowork/flowork-emblem.svg
button-single-row=true
show-button-title=false
show-button-icon=true
launcher-show-name=true
launcher-show-description=true
launcher-show-tooltip=true
item-icon-size=2
category-icon-size=1
view-as-icons=false
recent-items-max=12
favorites-in-recent=true
position-search-alternate=true
position-commands-alternate=true
position-categories-alternate=true
stay-on-focus-out=false
confirm-session-command=false
menu-width=560
menu-height=620
menu-opacity=92
command-profile=/opt/floworkos/bin/flowork-profile
show-command-profile=true
command-shutdown=systemctl poweroff
show-command-shutdown=true
command-restart=systemctl reboot
show-command-restart=true
command-suspend=systemctl suspend
show-command-suspend=true
command-lockscreen=xflock4
show-command-lockscreen=true
command-logout=flowork-power-menu
show-command-logout=true
EOF_WHISKER

# 5. Configure Flowork Keyboard Shortcuts
mkdir -p "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml"
cat << 'EOF_KB' > "$HOME/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-keyboard-shortcuts" version="1.0">
  <property name="commands" type="empty">
    <property name="custom" type="empty">
      <property name="Print" type="string" value="/opt/floworkos/bin/flowork-screenshot"/>
      <property name="&lt;Shift&gt;Print" type="string" value="/opt/floworkos/bin/flowork-screenshot -a"/>
      <property name="&lt;Super&gt;space" type="string" value="/usr/local/bin/flowork-spotlight"/>
      <property name="&lt;Super&gt;a" type="string" value="/usr/local/bin/flowork-launchpad"/>
      <property name="F4" type="string" value="/usr/local/bin/flowork-launchpad"/>
      <property name="&lt;Alt&gt;F1" type="string" value="xfce4-popup-whiskermenu"/>
      <property name="&lt;Primary&gt;&lt;Alt&gt;Delete" type="string" value="flowork-power-menu"/>
    </property>
  </property>
  <property name="xfwm4" type="empty">
    <property name="default" type="empty">
      <property name="&lt;Alt&gt;Tab" type="string" value="cycle_windows_key"/>
      <property name="&lt;Alt&gt;F4" type="string" value="close_window_key"/>
      <property name="&lt;Alt&gt;F10" type="string" value="maximize_window_key"/>
      <property name="&lt;Alt&gt;F9" type="string" value="hide_window_key"/>
    </property>
  </property>
</channel>
EOF_KB

# 6. Pre-configure Alacritty Terminal (Glass HUD 0.60, JetBrains Mono Bold, Pure Obsidian)
mkdir -p "$HOME/.config/alacritty"
if [ ! -f "$HOME/.config/alacritty/alacritty.toml" ]; then
  cat << 'EOF_ALACRITTY' > "$HOME/.config/alacritty/alacritty.toml"
[window]
startup_mode = "Windowed"
opacity = 0.60
blur = true
padding = { x = 20, y = 16 }
decorations = "full"

[font]
size = 12.0

[font.normal]
family = "JetBrains Mono"
style = "Bold"

[font.bold]
family = "JetBrains Mono"
style = "Bold"

[font.italic]
family = "JetBrains Mono"
style = "Italic"

[selection]
save_to_clipboard = true

[mouse]
hide_when_typing = false
bindings = [
  { mouse = "Right", action = "Paste" },
  { mouse = "Middle", action = "PasteSelection" }
]

[keyboard]
bindings = [
  { key = "C", mods = "Control|Shift", action = "Copy" },
  { key = "V", mods = "Control|Shift", action = "Paste" },
  { key = "V", mods = "Control", action = "Paste" },
  { key = "Insert", mods = "Shift", action = "Paste" },
  { key = "Copy", action = "Copy" },
  { key = "Paste", action = "Paste" }
]

[colors]
transparent_background_colors = true

[colors.primary]
background = "#000000"
foreground = "#ffffff"

[colors.cursor]
text = "#000000"
cursor = "#ffffff"

[colors.selection]
text = "#000000"
background = "#00ffff"

[colors.normal]
black = "#000000"
red = "#ff5555"
green = "#00ff66"
yellow = "#ffff00"
blue = "#00d4ff"
magenta = "#ff00ff"
cyan = "#00ffff"
white = "#ffffff"

[colors.bright]
black = "#475569"
red = "#ff6666"
green = "#33ff88"
yellow = "#ffff33"
blue = "#33ddff"
magenta = "#ff33ff"
cyan = "#33ffff"
white = "#ffffff"
EOF_ALACRITTY
fi

# 7. Configure Plank Floating Bottom Dock (Seed defaults on first launch, preserve user pins)
mkdir -p "$HOME/.config/plank/dock1/launchers"
rm -f "$HOME/.config/plank/dock1/launchers/recordly.dockitem" 2>/dev/null || true
if ! ls "$HOME/.config/plank/dock1/launchers/"*.dockitem >/dev/null 2>&1; then
  cat << 'EOF_TRASH' > "$HOME/.config/plank/dock1/launchers/trash.dockitem"
[PlankDockItemPreferences]
Launcher=docklet://trash
EOF_TRASH
  for dock_app in flowork-launchpad Alacritty code nemo flowork-screenshot mrflow-agent; do
    if [ -f "/usr/share/applications/${dock_app}.desktop" ]; then
      cat << EOF_DOCK > "$HOME/.config/plank/dock1/launchers/${dock_app}.dockitem"
[PlankDockItemPreferences]
Launcher=file:///usr/share/applications/${dock_app}.desktop
EOF_DOCK
    fi
  done
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ dock-items "['trash.dockitem', 'flowork-launchpad.dockitem', 'Alacritty.dockitem', 'code.dockitem', 'nemo.dockitem', 'flowork-screenshot.dockitem', 'mrflow-agent.dockitem']" 2>/dev/null || true
fi
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ auto-pinning false 2>/dev/null || true
if [ -x "$FLOWORK_OS_ROOT/theme/flowork-dock-responsive.py" ]; then
  "$FLOWORK_OS_ROOT/theme/flowork-dock-responsive.py" --sync 2>/dev/null || true
else
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ theme 'Flowork-Modern' 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ position 'bottom' 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ alignment 'center' 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ items-alignment 'center' 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ offset 0 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ hide-mode 'intelligent' 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ icon-size 48 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ zoom-enabled true 2>/dev/null || true
  gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ zoom-percent 140 2>/dev/null || true
fi

# 8. Clean Desktop & User Directories
mkdir -p "$HOME/.config/gtk-3.0" "$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Music" "$HOME/Pictures" "$HOME/Pictures/Screenshots" "$HOME/Videos"
cat << 'EOF_DIRS' > "$HOME/.config/user-dirs.dirs"
XDG_DESKTOP_DIR="$HOME/Desktop"
XDG_DOWNLOAD_DIR="$HOME/Downloads"
XDG_TEMPLATES_DIR="$HOME/Templates"
XDG_PUBLICSHARE_DIR="$HOME/Public"
XDG_DOCUMENTS_DIR="$HOME/Documents"
XDG_MUSIC_DIR="$HOME/Music"
XDG_PICTURES_DIR="$HOME/Pictures"
XDG_VIDEOS_DIR="$HOME/Videos"
EOF_DIRS

gsettings set org.nemo.desktop home-icon-visible false 2>/dev/null || true
gsettings set org.nemo.desktop trash-icon-visible false 2>/dev/null || true
gsettings set org.nemo.window-state sidebar-bookmark-breakpoint 20 2>/dev/null || true
gsettings set org.nemo.window-state start-with-menu-bar false 2>/dev/null || true

# Enforce Flowork OS Glass Themes & Wallpaper across Cinnamon & GNOME environments
SAVED_BG=$(gsettings get org.cinnamon.desktop.background picture-uri 2>/dev/null | tr -d "'\"")
if [ -z "$SAVED_BG" ] || [ "$SAVED_BG" = "''" ]; then
  gsettings set org.cinnamon.desktop.background picture-uri "file://$FLOWORK_OS_ROOT/theme/flowork-quantum-wallpaper.png" 2>/dev/null || true
  gsettings set org.gnome.desktop.background picture-uri "file://$FLOWORK_OS_ROOT/theme/flowork-quantum-wallpaper.png" 2>/dev/null || true
fi
gsettings set org.cinnamon.desktop.background picture-options 'zoom' 2>/dev/null || true
gsettings set org.cinnamon.desktop.interface gtk-theme 'Flowork-Quantum-Glass' 2>/dev/null || true
gsettings set org.cinnamon.desktop.interface icon-theme 'Papirus-Dark' 2>/dev/null || true
gsettings set org.cinnamon.desktop.interface cursor-theme 'breeze_cursors' 2>/dev/null || true
gsettings set org.cinnamon.theme name 'Flowork-Quantum-Glass' 2>/dev/null || true
gsettings set org.gnome.desktop.background picture-options 'zoom' 2>/dev/null || true
gsettings set org.gnome.desktop.interface gtk-theme 'Flowork-Quantum-Glass' 2>/dev/null || true
gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark' 2>/dev/null || true
gsettings set org.gnome.desktop.interface cursor-theme 'breeze_cursors' 2>/dev/null || true

# Ensure custom GTK 3.0 CSS is initialized
if [ ! -f "$HOME/.config/gtk-3.0/gtk.css" ] && [ -f "/etc/gtk-3.0/gtk.css" ]; then
  cp /etc/gtk-3.0/gtk.css "$HOME/.config/gtk-3.0/gtk.css"
fi

# Clean standard and sovereign bookmarks (Dynamic $HOME + Apps + 11 Canonical Pillars)
mkdir -p "$HOME/.config/gtk-3.0"
mkdir -p "$HOME"/{Documents,Downloads,Music,Pictures,Videos} 2>/dev/null || true
mkdir -p /opt/floworkos/{apps,screenshots,tools,agents,mcp,policies,skills,connector,history/chats,system/triger,system/system_promp/promps} 2>/dev/null || true
if [ -x "$FLOWORK_OS_ROOT/bin/flowork-sync-bookmarks" ]; then
  "$FLOWORK_OS_ROOT/bin/flowork-sync-bookmarks" 2>/dev/null || true
else
  cat << EOF > "$HOME/.config/gtk-3.0/bookmarks"
file://${HOME}/Documents Documents
file://${HOME}/Downloads Downloads
file://${HOME}/Music Music
file://${HOME}/Pictures Pictures
file://${HOME}/Videos Videos
file:///opt/floworkos/apps 🚀 Apps
file:///opt/floworkos/screenshots 📸 Screenshots
file:///opt/floworkos/system/system_promp/promps ⚡ Prompts
file:///opt/floworkos/tools 🛠️ Tools
file:///opt/floworkos/agents 🤖 Subagents
file:///opt/floworkos/mcp 🔌 MCP Servers
file:///opt/floworkos/policies ⚖️ Policies
file:///opt/floworkos/skills 💡 Skills
file:///opt/floworkos/system/triger 🎯 Active Triggers
file:///opt/floworkos/system/system_promp 📜 Rules & Triggers
file:///opt/floworkos/history/chats 💬 Chat History
file:///opt/floworkos/connector ⚡ Connector Gateway
EOF
fi


# 9. Set Flowork OS Sovereign Wallpaper (Respect user choice, fallback to Quantum)
TARGET_WP=""
CURRENT_URI=$(gsettings get org.cinnamon.desktop.background picture-uri 2>/dev/null | tr -d "'\"")
if [[ "$CURRENT_URI" == file://* ]]; then
  LOCAL_WP="${CURRENT_URI#file://}"
  if [ -f "$LOCAL_WP" ]; then
    TARGET_WP="$LOCAL_WP"
  fi
fi

if [ -z "$TARGET_WP" ] || [ ! -f "$TARGET_WP" ]; then
  TARGET_WP="$FLOWORK_OS_ROOT/theme/flowork-quantum-wallpaper.png"
fi

export FLOWORK_WALLPAPER="$TARGET_WP"

flowork_paint_wallpaper() {
  local img="$1"
  if [[ "$img" == *.svg ]]; then
    local cache_png="/run/user/$(id -u)/flowork_wallpaper_rendered.png"
    local wp_w=1920
    local wp_h=1080
    if command -v xrandr >/dev/null 2>&1; then
      read -r det_w det_h < <(xrandr --current 2>/dev/null | sed -n 's/.*current \([0-9]*\) x \([0-9]*\).*/\1 \2/p' | head -n 1 || true)
      if [ -n "${det_w:-}" ] && [ -n "${det_h:-}" ]; then
        wp_w="$det_w"
        wp_h="$det_h"
      fi
    fi
    rsvg-convert -w "$wp_w" -h "$wp_h" "$img" -o "$cache_png" 2>/dev/null && img="$cache_png"
  fi
  if command -v feh >/dev/null 2>&1; then
    feh --no-fehbg --bg-fill "$img" 2>/dev/null || true
  fi
}

flowork_paint_wallpaper "$FLOWORK_WALLPAPER"
# Re-apply wallpaper 1 second after compositor initialization to avoid black framebuffer artifacts
(
  sleep 1
  flowork_paint_wallpaper "$FLOWORK_WALLPAPER"
) &

# 10. Start XSettings Daemon (Ultra-Lightweight Theme Engine)
if command -v xsettingsd >/dev/null 2>&1 && ! pgrep -f "xsettingsd" >/dev/null 2>&1; then
  xsettingsd &
fi

# 11. Start Polkit Agent & Network Applet
if [ -x "/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1" ] && ! pgrep -f "polkit-gnome" >/dev/null 2>&1; then
  /usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1 &
fi
if command -v nm-applet >/dev/null 2>&1 && ! pgrep -f "nm-applet" >/dev/null 2>&1; then
  nm-applet &
fi

# 12. Bind Super Key to Flowork Menu via xcape
if command -v xcape >/dev/null 2>&1 && ! pgrep -f "xcape" >/dev/null 2>&1; then
  xcape -e 'Super_L=Alt_L|F1' &
fi

# 13. Launch Flowork System Daemon (Pure Rust on port 18090)
if [ -x "$FLOWORK_OS_ROOT/bin/flowork-sysd" ] && ! pgrep -f "flowork-sysd" >/dev/null 2>&1; then
  echo "[Flowork Session] Starting Flowork System Daemon (flowork-sysd)..."
  "$FLOWORK_OS_ROOT/bin/flowork-sysd" &
elif command -v flowork-sysd >/dev/null 2>&1 && ! pgrep -f "flowork-sysd" >/dev/null 2>&1; then
  flowork-sysd &
fi

# 14. Ensure Live Mount Compatibility for Calamares Installer
if [ -d "/run/live/medium" ] && [ ! -e "/cdrom" ]; then
  sudo ln -s /run/live/medium /cdrom 2>/dev/null || true
fi

# 16. Sync Desktop Applications & Enforce Sovereign Anti-Duplicate Menu Shield
mkdir -p "$HOME/.local/share/applications"

# Purge legacy duplicate or removed desktop files
rm -f "$HOME/.local/share/applications/flowork-diskcraft.desktop" \
      "$HOME/.local/share/applications/flowork-flow-repo.desktop" \
      "$HOME/.local/share/applications/flowork-sherlockcraft.desktop" \
      "$HOME/.local/share/applications/flowork-flowork-profile.desktop" \
      "$HOME/.local/share/applications/recordly.desktop" 2>/dev/null || true

cp -fu "$FLOWORK_OS_ROOT/apps/"*.desktop "$HOME/.local/share/applications/" 2>/dev/null || true

# Purge removed/defunct shortcuts from user Desktop
rm -f "$HOME/Desktop/flowork-drive.desktop" \
      "$HOME/Desktop/cursor.desktop" \
      "$HOME/Desktop/flowork-studio-hub.desktop" \
      "$HOME/Desktop/recordly.desktop" 2>/dev/null || true

# Enforce clean Start Menu: suppress duplicate, legacy, and removed application entries
for hidden_entry in \
    "recordly.desktop" \
    "flowork-drive.desktop" \
    "cursor.desktop" \
    "flowork-studio-hub.desktop" \
    "Antigravity.desktop" \
    "CutVii.desktop" \
    "com.microsoft.VSCode.desktop" \
    "org.gnome.Screenshot.desktop" \
    "mrflow-cli.desktop" \
    "mrflow-connector.desktop" \
    "mrflow-router.desktop" \
    "plank.desktop" \
    "picom.desktop" \
    "xfce4-file-manager.desktop" \
    "cinnamon.desktop" \
    "cinnamon2d.desktop" \
    "cinnamon-wayland.desktop" \
    "cinnamon-menu-editor.desktop" \
    "cinnamon-killer-daemon.desktop"
do
  cat << 'EOF_HIDE_APP' > "$HOME/.local/share/applications/${hidden_entry}"
[Desktop Entry]
Type=Application
Name=Hidden System Component
NoDisplay=true
Hidden=true
EOF_HIDE_APP
done

# 16. Start Flowork UI & Session Services (Direct + systemd resilient)
if [ -f "$FLOWORK_OS_ROOT/tools/memory_crystallizer/run.py" ] && [ ! -s "$FLOWORK_OS_ROOT/history/episodic_memory.db" ]; then
  (python3 "$FLOWORK_OS_ROOT/tools/memory_crystallizer/run.py" --sync-brain >/dev/null 2>&1 || true) &
fi
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user start xfce4-notifyd.service 2>/dev/null || true
  systemctl --user start flowork-panel.service 2>/dev/null || true
  systemctl --user start flowork-wallpaper-sync.service 2>/dev/null || true
  systemctl --user start flowork-compositor.service 2>/dev/null || true
  systemctl --user start flowork-menu-autoclose.service 2>/dev/null || true
  systemctl --user start flowork-neural-bus.service 2>/dev/null || true
  systemctl --user start mrflow-router.service 2>/dev/null || true
  systemctl --user start flowork-mrflow-sidebar.service 2>/dev/null || true
  systemctl --user start flowork-mrflow-tray-applet.service 2>/dev/null || true
  systemctl --user restart mrflow-tray.service 2>/dev/null || true
  systemctl --user start flowork-active-triggers.service 2>/dev/null || true
  systemctl --user start flowork-sentinel.service 2>/dev/null || true
fi

# Panel configuration & Direct Fallback
if command -v xfconf-query >/dev/null 2>&1; then
  xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -s 1 -t int -s 3 -t int -s 4 -t int -s 5 -t int -s 8 -t int -s 9 -t int -a 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-3 -n -t string -s "separator" 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-3/expand -n -t bool -s true 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-4 -n -t string -s "clock" 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-4/digital-layout -n -t uint -s 3 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-4/digital-time-format -n -t string -s "%a %b %-d  %-I:%M %p" 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-4/mode -n -t uint -s 2 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-5 -n -t string -s "separator" 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-5/expand -n -t bool -s true 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-8 -n -t string -s "systray" 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-8/square-icons -n -t bool -s true 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-9 -n -t string -s "pulseaudio" 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-9/enable-keyboard-shortcuts -n -t bool -s true 2>/dev/null || true
  xfconf-query -c xfce4-panel -p /plugins/plugin-9/show-notifications -n -t bool -s true 2>/dev/null || true

  # Audio Keyboard Shortcuts
  xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/XF86AudioRaiseVolume -n -t string -s "pactl set-sink-volume @DEFAULT_SINK@ +5%" 2>/dev/null || true
  xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/XF86AudioLowerVolume -n -t string -s "pactl set-sink-volume @DEFAULT_SINK@ -5%" 2>/dev/null || true
  xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/XF86AudioMute -n -t string -s "pactl set-sink-mute @DEFAULT_SINK@ toggle" 2>/dev/null || true
  xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/XF86AudioMicMute -n -t string -s "pactl set-source-mute @DEFAULT_SOURCE@ toggle" 2>/dev/null || true
fi

# Nemo Desktop & Disk Visibility (Show C:, D:, E:, USB, Network Shares on Desktop)
if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.nemo.desktop volumes-visible true 2>/dev/null || true
  gsettings set org.nemo.desktop computer-icon-visible true 2>/dev/null || true
  gsettings set org.nemo.desktop show-desktop-icons true 2>/dev/null || true
fi

# Connector Clean Vault Enforcement (Prevent user token leakage on Live ISO)
if [ -d "/run/live" ] || [ "$USER" = "flowork" ] || [ "$USER" = "live" ]; then
  if [ -f "$FLOWORK_OS_ROOT/connector/data/vault.clean.json" ]; then
    cp -f "$FLOWORK_OS_ROOT/connector/data/vault.clean.json" "$FLOWORK_OS_ROOT/connector/data/vault.json" 2>/dev/null || true
    chmod 600 "$FLOWORK_OS_ROOT/connector/data/vault.json" 2>/dev/null || true
  fi
fi

if command -v xfce4-panel >/dev/null 2>&1 && ! pgrep -f "xfce4-panel" >/dev/null 2>&1; then
  nohup xfce4-panel --disable-wm-check </dev/null >/dev/null 2>&1 & disown
fi

if [ -x "/usr/local/bin/mrflow-tray-menu" ] && ! pgrep -f "mrflow-tray-menu" >/dev/null 2>&1; then
  (sleep 2 && /usr/local/bin/mrflow-tray-menu &) &
fi

(
  sleep 1
  if [ -x "$FLOWORK_OS_ROOT/theme/flowork-dock-responsive.py" ]; then
    "$FLOWORK_OS_ROOT/theme/flowork-dock-responsive.py" --sync 2>/dev/null || true
  fi
  if command -v plank >/dev/null 2>&1 && ! pgrep -f "plank" >/dev/null 2>&1; then
    plank &
  fi
  if [ -f "$FLOWORK_OS_ROOT/theme/flowork-dock-responsive.py" ] && ! pgrep -f "flowork-dock-responsive.py" >/dev/null 2>&1; then
    python3 -u "$FLOWORK_OS_ROOT/theme/flowork-dock-responsive.py" --daemon >/dev/null 2>&1 &
  fi
) &

# Fallback Live Wallpaper Sync Daemon
if [ -f "$FLOWORK_OS_ROOT/theme/wallpaper-sync-daemon.py" ] && ! pgrep -f "wallpaper-sync-daemon.py" >/dev/null 2>&1; then
  python3 -u "$FLOWORK_OS_ROOT/theme/wallpaper-sync-daemon.py" >/dev/null 2>&1 &
fi

# 19. Start Adaptive Display Compositor (HW Picom vs Software Lightweight XFWM4)
if [ "${FLOWORK_SW_COMPOSITOR:-0}" -eq 0 ]; then
  if command -v picom >/dev/null 2>&1 && ! pgrep -x "picom" >/dev/null 2>&1; then
    picom --config "$FLOWORK_OS_ROOT/theme/picom-quantum.conf" -b 2>/dev/null || true
  fi
fi

if command -v xfconf-query >/dev/null 2>&1; then
  xfconf-query -c xfwm4 -p /general/use_compositing -s "${XFWM4_USE_COMP}" --create -t bool 2>/dev/null || true
  xfconf-query -c xfwm4 -p /general/show_frame_shadow -s "${XFWM4_SHADOW}" --create -t bool 2>/dev/null || true
  xfconf-query -c xfwm4 -p /general/show_popup_shadow -s "${XFWM4_SHADOW}" --create -t bool 2>/dev/null || true
  xfconf-query -c xfwm4 -p /general/theme -s 'Flowork-Quantum-Glass' --create -t string 2>/dev/null || true
  xfconf-query -c xfwm4 -p /general/button_layout -s '|HMC' --create -t string 2>/dev/null || true
fi

# Default Sovereign Media Player for Video Formats
if command -v xdg-mime >/dev/null 2>&1; then
  xdg-mime default flowork-player.desktop video/mp4 video/x-matroska video/webm video/quicktime image/gif 2>/dev/null || true
fi

# 20. Launch Sovereign Window Manager with Crash-Resistant Loop (Never Logout)
echo "[Flowork Session] Launching Sovereign Window Manager on $TARGET_DISPLAY (${FLOWORK_WM_COMP_FLAG})..."
while true; do
  xfwm4 "${FLOWORK_WM_COMP_FLAG}" "$@" || true
  sleep 1
done
