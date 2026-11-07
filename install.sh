#!/usr/bin/env bash
# ==============================================================================
# 👑 FLOWORK OS — SOVEREIGN IN-PLACE SYSTEM CONVERTER & INSTALLER
# Transforms standard Debian/Ubuntu systems into Flowork OS (Linux 7.3.0 Rust).
# Repository: https://github.com/flowork-os/flowork-os.git
# ==============================================================================
set -euo pipefail

# Sovereign HUD Colors
BOLD="\033[1m"
GREEN="\033[38;2;0;255;102m"
CYAN="\033[38;2;0;242;254m"
AMBER="\033[38;2;255;184;0m"
RED="\033[38;2;255;51;102m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}  👑 FLOWORK OS — SOVEREIGN SYSTEM CONVERTER & INSTALLER        ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"

# 1. Privileges & Architecture Verification
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}[ERROR] This installer must be executed with root privileges.${RESET}" >&2
    echo -e "Please run: ${BOLD}sudo ./install.sh${RESET}" >&2
    exit 1
fi

ARCH="$(uname -m)"
if [ "$ARCH" != "x86_64" ]; then
    echo -e "${RED}[ERROR] Flowork OS currently supports x86_64 architecture only (Detected: $ARCH).${RESET}" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo "")}"
TARGET_HOME=""
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
fi

echo -e "${CYAN}→ Target System User:${RESET} ${TARGET_USER:-root} (${TARGET_HOME:-/root})"

# 2. Installing Custom Linux 7.3.0 Rust Kernel Packages
echo -e "\n${BOLD}${CYAN}[STAGE 1/6] Installing Custom Linux 7.3.0 Rust Kernel...${RESET}"
KERNEL_DIR="${SCRIPT_DIR}/kernel"
if compgen -G "${KERNEL_DIR}/*.deb" > /dev/null; then
    echo -e "Installing kernel images and headers from local packages..."
    dpkg -i "${KERNEL_DIR}"/*.deb || apt-get install -f -y
    echo -e "${GREEN}✓ Linux 7.3.0 Rust Kernel installed successfully.${RESET}"
else
    echo -e "${AMBER}⚠ No local kernel deb packages found in kernel/. Keeping existing kernel.${RESET}"
fi

# 3. Installing Required System Dependencies
echo -e "\n${BOLD}${CYAN}[STAGE 2/6] Verifying & Installing Core Dependencies...${RESET}"
DEPS=(
    "python3" "python3-gi" "gir1.2-webkit2-4.1" "gir1.2-gtk-3.0"
    "xdotool" "x11-utils" "maim" "xclip" "rsync" "curl" "git"
    "lightdm" "xfwm4" "xfce4-panel" "plank" "jq"
)

MISSING=()
for dep in "${DEPS[@]}"; do
    if ! dpkg -s "$dep" &>/dev/null; then
        MISSING+=("$dep")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "Installing missing dependencies: ${MISSING[*]}..."
    apt-get update -qq
    apt-get install -y --no-install-recommends "${MISSING[@]}"
fi
echo -e "${GREEN}✓ All core runtime dependencies satisfied.${RESET}"

# 4. Deploying Flowork OS Core Layer (/opt/floworkos)
echo -e "\n${BOLD}${CYAN}[STAGE 3/6] Deploying Core Layer to /opt/floworkos...${RESET}"
mkdir -p /opt/floworkos
rsync -a --delete \
    --exclude="history/chats" \
    --exclude="*.log" \
    --exclude=".git*" \
    "${SCRIPT_DIR}/core/" /opt/floworkos/

# Set proper permissions
chown -R root:root /opt/floworkos
chmod -R 755 /opt/floworkos
if [ -n "$TARGET_USER" ]; then
    chown -R "${TARGET_USER}:${TARGET_USER}" /opt/floworkos/history 2>/dev/null || true
fi
echo -e "${GREEN}✓ Core system assets deployed to /opt/floworkos.${RESET}"

# 5. Deploying System Daemons, Binaries & Policies
echo -e "\n${BOLD}${CYAN}[STAGE 4/6] Installing System Binaries & Daemons...${RESET}"
if [ -d "${SCRIPT_DIR}/system/bin" ]; then
    cp -a "${SCRIPT_DIR}/system/bin/"* /usr/local/bin/ 2>/dev/null || true
fi

# Symlinks for essential sovereign commands
ln -sf /opt/floworkos/bin/flowork-update /usr/local/bin/flowork-update
ln -sf /opt/floworkos/bin/flowork-update /usr/local/bin/flowork-updater
ln -sf /opt/floworkos/bin/mrflow /usr/local/bin/mrflow
ln -sf /opt/floworkos/bin/mrflow-terminal /usr/local/bin/mrflow-terminal
ln -sf /opt/floworkos/bin/flowork-adshield /usr/local/bin/flowork-adshield

# Systemd services
if [ -d "${SCRIPT_DIR}/system/systemd" ]; then
    cp -f "${SCRIPT_DIR}/system/systemd/"* /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload
fi

# Desktop sessions & LightDM
if [ -d "${SCRIPT_DIR}/system/xsessions" ]; then
    mkdir -p /usr/share/xsessions
    cp -f "${SCRIPT_DIR}/system/xsessions/"* /usr/share/xsessions/ 2>/dev/null || true
fi
if [ -d "${SCRIPT_DIR}/system/lightdm" ]; then
    mkdir -p /etc/lightdm
    cp -f "${SCRIPT_DIR}/system/lightdm/"* /etc/lightdm/ 2>/dev/null || true
fi

# Browser enterprise policies (AdShield)
if [ -d "${SCRIPT_DIR}/system/browser-policies" ]; then
    mkdir -p /etc/opt/chrome/policies /etc/chromium/policies
    cp -rf "${SCRIPT_DIR}/system/browser-policies/chrome-policies" /etc/opt/chrome/policies/ 2>/dev/null || true
    cp -rf "${SCRIPT_DIR}/system/browser-policies/chromium-policies" /etc/chromium/policies/ 2>/dev/null || true
fi
echo -e "${GREEN}✓ System daemons, commands, and security policies installed.${RESET}"

# 6. Deploying User Skeleton & Configuring Active User
echo -e "\n${BOLD}${CYAN}[STAGE 5/6] Applying User Skeleton & Environment...${RESET}"
if [ -d "${SCRIPT_DIR}/skel" ]; then
    mkdir -p /etc/skel
    rsync -a "${SCRIPT_DIR}/skel/" /etc/skel/

    if [ -n "$TARGET_HOME" ] && [ -d "$TARGET_HOME" ]; then
        echo -e "Updating Flowork user configs for: ${TARGET_USER}..."
        # Copy non-destructively: only add missing configs, do not wipe user files
        rsync -a --ignore-existing "${SCRIPT_DIR}/skel/" "${TARGET_HOME}/"
        # Always update Flowork desktop entry and sidebar configs
        mkdir -p "${TARGET_HOME}/.config/systemd/user"
        if [ -f "/opt/floworkos/apps/mrflow-sidebar/systemd/flowork-mrflow-sidebar.service" ]; then
            cp -f "/opt/floworkos/apps/mrflow-sidebar/systemd/flowork-mrflow-sidebar.service" "${TARGET_HOME}/.config/systemd/user/"
        fi
        chown -R "${TARGET_USER}:${TARGET_USER}" "${TARGET_HOME}/.config" "${TARGET_HOME}/.flowork" 2>/dev/null || true
    fi
fi
echo -e "${GREEN}✓ Desktop skeleton and user preferences configured.${RESET}"

# 7. Activating Services & Bootloader Update
echo -e "\n${BOLD}${CYAN}[STAGE 6/6] Activating Auto-Update Timers & GRUB...${RESET}"
systemctl enable flowork-updater.timer --now 2>/dev/null || true

# Update GRUB for Linux 7.3.0 Rust
if command -v update-grub &>/dev/null; then
    echo -e "Updating GRUB bootloader menu..."
    update-grub
fi

echo -e "\n${BOLD}${GREEN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}  👑 CONGRATULATIONS! FLOWORK OS IS SUCCESSFULLY INSTALLED!     ${RESET}"
echo -e "${BOLD}${GREEN}================================================================${RESET}"
echo -e "${GREEN}→ Linux 7.3.0 Rust Kernel configured.${RESET}"
echo -e "${GREEN}→ Sovereign Glass HUD & Mr. Flow Companion active.${RESET}"
echo -e "${GREEN}→ Background OTA Auto-Updater daemon enabled (flowork-updater.timer).${RESET}"
echo -e "${BOLD}${AMBER}→ Please reboot your computer now to boot into Flowork OS:${RESET}"
echo -e "  ${BOLD}sudo reboot${RESET}\n"

exit 0
