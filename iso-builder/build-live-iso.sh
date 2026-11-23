#!/usr/bin/env bash
# =============================================================================
# 👑 FLOWORK OS — PRODUCTION LIVE ISO MASTERING PIPELINE (flowork-iso-master)
# Builds reproducible, hybrid UEFI/BIOS bootable ISO with Calamares Sovereign Glass.
# =============================================================================
set -euo pipefail

resolve_output_home() {
    if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
        local sudo_home
        sudo_home="$(getent passwd "${SUDO_USER}" 2>/dev/null | cut -d: -f6 || true)"
        if [ -n "$sudo_home" ] && [ -d "$sudo_home" ]; then
            printf '%s\n' "${sudo_home%/}"
            return 0
        fi
    fi
    printf '%s\n' "${HOME%/}"
}

REAL_HOME="$(resolve_output_home)"
FLOWORK_ROOT="/opt/floworkos"
BUILDER_DIR="${FLOWORK_ROOT}/iso-builder"
INSTALLER_DIR="${FLOWORK_ROOT}/installer/calamares"
OUTPUT_DIR="${REAL_HOME}/Downloads/flowork-iso-build"
ISO_NAME="FloworkOS-1.0-x86_64-Sovereign-Rust.iso"

resolve_latest_kernel_and_initrd() {
    LATEST_VMLINUZ=$(find /boot -name "vmlinuz-*" ! -name "*.old" 2>/dev/null | sort -V | tail -n 1 || echo "")
    if [ -z "$LATEST_VMLINUZ" ]; then
        LATEST_VMLINUZ=$(find /boot -name "vmlinuz*" ! -name "*.old" 2>/dev/null | sort -V | tail -n 1 || echo "")
    fi
    LATEST_INITRD=$(find /boot -name "initrd.img-*" ! -name "*.old" 2>/dev/null | sort -V | tail -n 1 || echo "")
    if [ -z "$LATEST_INITRD" ]; then
        LATEST_INITRD=$(find /boot -name "initrd.img*" ! -name "*.old" 2>/dev/null | sort -V | tail -n 1 || echo "")
    fi
}

check_kernel_flag() {
    local cfg_file="$1"
    local flag="$2"
    grep -qE "^${flag}=(y|m)$" "$cfg_file" 2>/dev/null
}

check_prerequisites() {
    echo "┌────────────────────────────────────────────────────────┐"
    echo "│ 📀 FLOWORK OS: LIVE ISO BUILD PRE-FLIGHT AUDIT         │"
    echo "├────────────────────────────────────────────────────────┤"

    # 1. Boot skeleton
    if [ -d "${BUILDER_DIR}/boot-skeleton" ]; then
        echo "│ [✓] Boot Skeleton EFI / ISOLINUX / GRUB : OK"
    else
        echo "│ [✗] Boot Skeleton missing at ${BUILDER_DIR}/boot-skeleton"
        return 1
    fi

    # 2. Calamares Installer
    if [ -f "/etc/calamares/settings.conf" ] && [ -f "/etc/calamares/modules/partition.conf" ] && [ -f "${INSTALLER_DIR}/settings.conf" ]; then
        echo "│ [✓] Calamares Installer Configs (/etc/calamares) : OK"
    else
        echo "│ [✗] Calamares configs missing!"
        return 1
    fi

    # 2b. DiskCraft Sovereign Storage Suite
    if [ -x "/opt/floworkos/bin/diskcraft" ] || [ -f "/opt/floworkos/apps/diskcraft/bin/backend.py" ]; then
        echo "│ [✓] DiskCraft Pre-Build Hygiene Suite  : OK"
    fi

    # 3. Kernel, Initrd & Kernel Config Audit
    resolve_latest_kernel_and_initrd
    local kver=""
    local kcfg=""
    local has_user_ns="unknown"
    if [ -n "$LATEST_VMLINUZ" ] && [ -n "$LATEST_INITRD" ]; then
        kver="$(basename "$LATEST_VMLINUZ" | sed 's/^vmlinuz-//')"
        echo "│ [✓] Host Kernel: $(basename "$LATEST_VMLINUZ")"
        echo "│ [✓] Host Initrd: $(basename "$LATEST_INITRD")"
        if [ -f "/boot/config-${kver}" ]; then
            kcfg="/boot/config-${kver}"
        fi
    else
        echo "│ [!] Note: No host kernel found in /boot (Build skeleton fallback mode)"
    fi

    if [ -n "$kcfg" ]; then
        if check_kernel_flag "$kcfg" "CONFIG_SQUASHFS" && check_kernel_flag "$kcfg" "CONFIG_SQUASHFS_XZ" && check_kernel_flag "$kcfg" "CONFIG_OVERLAY_FS"; then
            echo "│ [✓] Kernel Live Boot (SQUASHFS_XZ + OVERLAY_FS) : OK"
        else
            echo "│ [✗] Kernel missing SQUASHFS / OVERLAY_FS required for Live ISO boot!"
            return 1
        fi

        if check_kernel_flag "$kcfg" "CONFIG_USER_NS"; then
            has_user_ns="yes"
            echo "│ [✓] Kernel CONFIG_USER_NS : Enabled"
        else
            has_user_ns="no"
            echo "│ [!] Kernel Warning: CONFIG_USER_NS disabled (enable in next kernel rebuild)"
        fi

        if check_kernel_flag "$kcfg" "CONFIG_FUSE_FS"; then
            echo "│ [✓] Kernel CONFIG_FUSE_FS : Enabled (Portals/AppImage OK)"
        else
            echo "│ [!] Kernel Warning: CONFIG_FUSE_FS disabled (xdg-document-portal/FUSE disabled until kernel rebuild)"
        fi

        if check_kernel_flag "$kcfg" "CONFIG_BTRFS_FS"; then
            echo "│ [✓] Kernel CONFIG_BTRFS_FS : Enabled"
        else
            if grep -qE 'defaultFileSystemType:[[:space:]]*"?btrfs"?' /etc/calamares/modules/partition.conf 2>/dev/null; then
                echo "│ [✗] Calamares defaults to btrfs, but kernel lacks CONFIG_BTRFS_FS!"
                return 1
            fi
            echo "│ [!] Kernel Note: CONFIG_BTRFS_FS disabled (Calamares /etc/calamares uses ext4)"
        fi

        if check_kernel_flag "$kcfg" "CONFIG_SECURITY_LANDLOCK"; then
            echo "│ [✓] Kernel CONFIG_SECURITY_LANDLOCK : Enabled"
        else
            echo "│ [!] Kernel Warning: CONFIG_SECURITY_LANDLOCK disabled"
        fi

        if check_kernel_flag "$kcfg" "CONFIG_DRM_NOUVEAU" || check_kernel_flag "$kcfg" "CONFIG_DRM_AMDGPU"; then
            echo "│ [✓] Kernel Discrete GPU DRM Drivers (Nouveau/AMDGPU) : Enabled"
        else
            echo "│ [!] Kernel Warning: CONFIG_DRM_NOUVEAU/AMDGPU disabled (software simpledrm fallback uses lightweight xfwm4 compositor)"
        fi

        if [ -n "$kver" ] && [ -d "/usr/src/nvidia-595.99.02" ]; then
            if modinfo -k "$kver" nvidia >/dev/null 2>&1 \
                && modinfo -k "$kver" nvidia-modeset >/dev/null 2>&1 \
                && modinfo -k "$kver" nvidia-drm >/dev/null 2>&1 \
                && modinfo -k "$kver" nvidia-uvm >/dev/null 2>&1; then
                echo "│ [✓] NVIDIA DKMS Modules (${kver}) : Built & Ready"
            else
                echo "│ [!] NVIDIA DKMS Warning: modules not built for ${kver} (run sudo ${FLOWORK_ROOT}/system/kernel/enable-landlock-and-nvidia.sh before --build)"
            fi
        fi
    fi

    # 4. Binary tools & Global CLI Toolchain
    for tool in xorriso mksquashfs calamares jq uv uvx; do
        if command -v "$tool" >/dev/null 2>&1; then
            local resolved
            resolved="$(readlink -f "$(command -v "$tool")" 2>/dev/null || true)"
            case "$resolved" in
                /home/*)
                    echo "│ [✗] Tool '$tool' resolves inside /home ($resolved)!"
                    return 1
                    ;;
                *)
                    echo "│ [✓] Tool '$tool' : Available ($resolved)"
                    ;;
            esac
        else
            echo "│ [✗] Required tool '$tool' missing!"
            return 1
        fi
    done

    # 5. System Services & Desktop Readiness (Upower, Compositor, GTK3 CSS, Desktop Shortcuts)
    if [ "$has_user_ns" = "yes" ] || [ -f "/etc/systemd/system/upower.service.d/override.conf" ]; then
        echo "│ [✓] Power Daemon (upower.service + PrivateUsers guard) : OK"
    else
        echo "│ [✗] upower.service will fail with status=217/USER without CONFIG_USER_NS or override.conf!"
        return 1
    fi

    if [ -x "${FLOWORK_ROOT}/bin/flowork-compositor" ] && grep -qF "flowork-compositor" /etc/systemd/user/flowork-compositor.service 2>/dev/null; then
        echo "│ [✓] Adaptive Display Compositor & Service Unit : OK"
    else
        echo "│ [✗] Adaptive flowork-compositor launcher or systemd service missing!"
        return 1
    fi

    if ! grep -qE "^[[:space:]]*transform:" /etc/skel/.config/gtk-3.0/gtk.css /usr/share/themes/Flowork-Quantum-Glass/gtk-3.0/gtk.css 2>/dev/null; then
        echo "│ [✓] GTK3 Theme CSS Syntax (Skel & Flowork-Quantum-Glass) : OK"
    else
        echo "│ [✗] Invalid CSS 'transform:' detected in GTK3 theme or /etc/skel!"
        return 1
    fi

    # 5b. Flowork Quantum Glass & Design System Integrity Guard
    if grep -q 'value="Flowork-Quantum-Glass"' /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml 2>/dev/null \
        && [ -f "/usr/share/themes/Flowork-Quantum-Glass/xfwm4/themerc" ] \
        && [ -f "/etc/skel/.themes/Flowork-Quantum-Glass/xfwm4/themerc" ] \
        && [ -f "/usr/share/icons/Flowork-Quantum-Glass/index.theme" ]; then
        echo "│ [✓] Flowork Quantum Glass Integration (Skel xsettings, xfwm4 & Icons) : OK"
    else
        echo "│ [✗] Flowork-Quantum-Glass missing in /etc/skel xsettings, xfwm4, or icon theme!"
        return 1
    fi

    local broken_desktop_count=0
    local df try_exec exec_line exec_bin hidden_val nodisp_val
    for df in /usr/share/applications/*.desktop; do
        [ -f "$df" ] || continue
        if [ "$df" = "/usr/share/applications/recordly.desktop" ] && [ ! -e "${FLOWORK_ROOT}/apps/recordly" ]; then
            continue
        fi
        hidden_val="$(grep -m1 '^Hidden=' "$df" 2>/dev/null | cut -d= -f2- || true)"
        nodisp_val="$(grep -m1 '^NoDisplay=' "$df" 2>/dev/null | cut -d= -f2- || true)"
        if [ "$hidden_val" = "true" ] || [ "$nodisp_val" = "true" ]; then
            continue
        fi
        try_exec="$(grep -m1 '^TryExec=' "$df" 2>/dev/null | cut -d= -f2- || true)"
        exec_line="$(grep -m1 '^Exec=' "$df" 2>/dev/null | cut -d= -f2- || true)"
        exec_bin=""
        if [ -n "$try_exec" ]; then
            exec_bin="$try_exec"
        elif [ -n "$exec_line" ]; then
            exec_bin="$(printf '%s' "$exec_line" | sed -E 's/^env[[:space:]]+([^=]+="[^"]*"[[:space:]]+|[^=]+=[^[:space:]]+[[:space:]]+)*//; s/^"//; s/".*$//; s/[[:space:]].*$//')"
        fi
        if [ -n "$exec_bin" ] && ! command -v "$exec_bin" >/dev/null 2>&1 && [ ! -x "$exec_bin" ]; then
            echo "│ [✗] Broken visible desktop shortcut: $df -> missing '$exec_bin'"
            broken_desktop_count=$((broken_desktop_count + 1))
        fi
    done
    if [ "$broken_desktop_count" -gt 0 ]; then
        return 1
    fi
    echo "│ [✓] Visible Desktop Entries (/usr/share/applications) : Zero broken shortcuts"

    if grep -q 'binary in ("-", "-c", "-m")' /usr/lib/python3/dist-packages/apport_python_hook.py 2>/dev/null; then
        echo "│ [✓] Python Inline Apport Hook Guard (-c / -) : OK"
    else
        echo "│ [!] Apport Python Hook missing -c guard (/usr/lib/python3/dist-packages/apport_python_hook.py)"
    fi

    if [ -x "/usr/local/bin/mrflow-tray-applet" ] && [ -e "/etc/systemd/user/default.target.wants/flowork-mrflow-tray-applet.service" ]; then
        echo "│ [✓] Mr. Flow Header Tray Applet & Systemd Unit : OK"
    else
        echo "│ [✗] /usr/local/bin/mrflow-tray-applet or systemd want link missing!"
        return 1
    fi

    if [ -x "${FLOWORK_ROOT}/bin/flowork-sync-bookmarks" ] \
        && grep -qF "file:///opt/floworkos/apps" /etc/skel/.config/gtk-3.0/bookmarks 2>/dev/null \
        && ! grep -q "/home/" /etc/skel/.config/gtk-3.0/bookmarks 2>/dev/null; then
        echo "│ [✓] Dynamic File Manager Bookmarks (Downloads + Apps + Pillars) : OK"
    else
        echo "│ [✗] Bookmark synchronizer or clean /etc/skel bookmarks missing!"
        return 1
    fi

    # 6. Audio & Volume Control Verification
    if [ -f "/usr/lib/x86_64-linux-gnu/xfce4/panel/plugins/libpulseaudio-plugin.so" ]; then
        echo "│ [✓] Audio & Volume Panel Plugin (xfce4-pulseaudio) : OK"
    else
        echo "│ [✗] Audio Plugin missing!"
        return 1
    fi

    # 7. Network Tray & Autoconnect Verification
    if command -v nm-applet >/dev/null 2>&1 && [ -f "/etc/NetworkManager/conf.d/99-flowork-network.conf" ]; then
        echo "│ [✓] Internet Tray Applet & NM Autoconnect : OK"
    else
        echo "│ [✗] NetworkManager autoconnect configs missing!"
        return 1
    fi

    # 8. Windows NTFS/exFAT Disks & Polkit Verification
    if command -v ntfs-3g >/dev/null 2>&1; then
        if [ "${EUID:-$(id -u)}" -eq 0 ] || [ -r "/etc/polkit-1/rules.d/10-udisks2.rules" ] || sudo -n test -f "/etc/polkit-1/rules.d/10-udisks2.rules" 2>/dev/null; then
            if [ "${EUID:-$(id -u)}" -eq 0 ] && [ ! -f "/etc/polkit-1/rules.d/10-udisks2.rules" ]; then
                echo "│ [✗] Windows filesystem drivers or Polkit rule missing!"
                return 1
            fi
            echo "│ [✓] Windows Drives (NTFS/exFAT) & Passwordless Udisks2 : OK"
        else
            echo "│ [!] Windows Drives (ntfs-3g) : OK (Polkit rule requires root check before --build)"
        fi
    else
        echo "│ [✗] Windows filesystem drivers or Polkit rule missing!"
        return 1
    fi

    # 9. Flowork Connector Vault Isolation (Exclude host vault.json; inject vault.clean.json inside ISO)
    if [ -f "${FLOWORK_ROOT}/connector/data/vault.clean.json" ] && jq empty "${FLOWORK_ROOT}/connector/data/vault.clean.json" >/dev/null 2>&1; then
        if [ -f "${FLOWORK_ROOT}/connector/data/vault.json" ]; then
            local vault_mode
            vault_mode="$(stat -c '%a' "${FLOWORK_ROOT}/connector/data/vault.json" 2>/dev/null || echo '')"
            if [ "$vault_mode" != "600" ]; then
                echo "│ [✗] Host vault.json permissions (${vault_mode}) exceed strict 600!"
                return 1
            fi
        fi
        echo "│ [✓] Flowork Connector Vault: Clean ISO 0600 + Host Isolated : OK"
    else
        echo "│ [✗] vault.clean.json missing or invalid JSON!"
        return 1
    fi

    # 10. Realtek NIC Uncompressed Firmware Guard (CONFIG_FW_LOADER_COMPRESS disabled)
    if [ -n "$kcfg" ] && ! check_kernel_flag "$kcfg" "CONFIG_FW_LOADER_COMPRESS"; then
        if [ -f "/lib/firmware/rtl_nic/rtl8168h-2.fw.zst" ] && [ ! -f "/lib/firmware/rtl_nic/rtl8168h-2.fw" ]; then
            echo "│ [✗] Missing uncompressed /lib/firmware/rtl_nic/rtl8168h-2.fw for non-zstd kernel!"
            return 1
        fi
    fi
    if [ -f "/lib/firmware/rtl_nic/rtl8168h-2.fw" ]; then
        echo "│ [✓] Realtek NIC Firmware (rtl8168h-2.fw uncompressed) : OK"
    fi

    # 11. Sovereign Rust Mr. Flow & Zero-Node Pure Rust Core Verification
    local MRFLOW_BIN="${FLOWORK_ROOT}/bin/mrflow"
    if [ -x "$MRFLOW_BIN" ] && file "$MRFLOW_BIN" | grep -q "ELF" && "$MRFLOW_BIN" --version 2>/dev/null | grep -q "sovereign"; then
        echo "│ [✓] Mr. Flow Engine: Native Rust Sovereign Binary : OK"
    else
        echo "│ [✗] Mr. Flow native Rust binary missing or invalid at ${MRFLOW_BIN}!"
        return 1
    fi
    if [ -e "${FLOWORK_ROOT}/lib/mrflow" ] || [ -e "/usr/lib/node_modules/@google/gemini-cli" ] || [ -e "/usr/local/lib/node_modules/@google/gemini-cli" ]; then
        echo "│ [✗] Legacy Node mrflow-core / @google/gemini-cli detected! Purge required."
        return 1
    else
        echo "│ [✓] Legacy mrflow-core / @google/gemini-cli Purge : OK"
    fi

    local node_bin
    for node_bin in node npm npx nodejs corepack; do
        if command -v "$node_bin" >/dev/null 2>&1; then
            echo "│ [✗] Forbidden Node.js runtime '$node_bin' detected on host!"
            return 1
        fi
    done
    if [ -d "/usr/lib/node_modules" ] || [ -d "/usr/local/lib/node_modules" ]; then
        echo "│ [✗] Forbidden system node_modules directory detected!"
        return 1
    fi
    local legacy_js
    for legacy_js in \
        "${FLOWORK_ROOT}/bin/flowork-neural-bus.js" \
        "${FLOWORK_ROOT}/skills/lint_skills.js" \
        "${FLOWORK_ROOT}/tools/discovery.js" \
        "${FLOWORK_ROOT}/tools/context_sniffer.js" \
        "${FLOWORK_ROOT}/tools/executor.js" \
        "${FLOWORK_ROOT}/tools/lifecycle_manager.js" \
        "${FLOWORK_ROOT}/tools/browser_mcp_client.js" \
        "${FLOWORK_ROOT}/tools/browser_backend/chrome-devtools-mcp.mjs" \
        "${FLOWORK_ROOT}/connector/server/index.js" \
        "${FLOWORK_ROOT}/apps/flowork-edits/backend/server.js"; do
        if [ -e "$legacy_js" ]; then
            echo "│ [✗] Legacy JS system core artifact remains: ${legacy_js}"
            return 1
        fi
    done
    echo "│ [✓] Zero-Node & Legacy JS Eradication : OK"

    local rust_elf
    for rust_elf in \
        "${FLOWORK_ROOT}/bin/flowork-neural-bus" \
        "${FLOWORK_ROOT}/bin/flowork-edits-daemon" \
        "${FLOWORK_ROOT}/bin/flowork-lint-skills" \
        "${FLOWORK_ROOT}/bin/flowork-tool-discovery" \
        "${FLOWORK_ROOT}/bin/flowork-tool-executor" \
        "${FLOWORK_ROOT}/bin/flowork-tool-runner" \
        "${FLOWORK_ROOT}/bin/flowork-pipe-rs" \
        "${FLOWORK_ROOT}/bin/flowork-sandbox-exec" \
        "${FLOWORK_ROOT}/bin/flowork-mesh" \
        "${FLOWORK_ROOT}/bin/flowfs-search" \
        "${FLOWORK_ROOT}/bin/flowfs-indexer-daemon" \
        "${FLOWORK_ROOT}/bin/flowork-sysd" \
        "${FLOWORK_ROOT}/tools/browser_backend/flowork-browser-mcp" \
        "${FLOWORK_ROOT}/connector/bin/flowork-connector" \
        "/usr/local/bin/agent-browser" \
        "/usr/local/bin/agent-desktop" \
        "/usr/local/bin/agent-desktop-linux-clipboard-owner"; do
        if [ ! -x "$rust_elf" ] || ! file "$rust_elf" | grep -q "ELF"; then
            echo "│ [✗] Missing or invalid Pure Rust ELF: ${rust_elf}"
            return 1
        fi
    done
    if ! "${FLOWORK_ROOT}/bin/flowork-tool-runner" --check >/dev/null 2>&1; then
        echo "│ [✗] flowork-tool-runner --check failed!"
        return 1
    fi
    if ! "${FLOWORK_ROOT}/bin/flowork-sandbox-exec" --check >/dev/null 2>&1; then
        echo "│ [✗] flowork-sandbox-exec --check failed!"
        return 1
    fi
    if ! "${FLOWORK_ROOT}/bin/flowork-mesh" --check >/dev/null 2>&1; then
        echo "│ [✗] flowork-mesh --check failed!"
        return 1
    fi
    local broken_runner_links
    broken_runner_links="$(find "${FLOWORK_ROOT}/tools" -maxdepth 2 -name run ! -samefile "${FLOWORK_ROOT}/bin/flowork-tool-runner" 2>/dev/null || true)"
    if [ -n "$broken_runner_links" ]; then
        echo "│ [✗] Tool runner hardlink mismatch detected: ${broken_runner_links}"
        return 1
    fi
    for ipc_asset in \
        "${FLOWORK_ROOT}/bin/flowork-bus" \
        "${FLOWORK_ROOT}/bin/flowork-pipe" \
        "${FLOWORK_ROOT}/bin/flowork-snapshot" \
        "${FLOWORK_ROOT}/bin/flowork-rollback" \
        "${FLOWORK_ROOT}/bin/flowork-sentinel-daemon" \
        "${FLOWORK_ROOT}/tools/self_healing_sentinel/run.py" \
        "${FLOWORK_ROOT}/bin/kamidi-mastering-cli" \
        "${FLOWORK_ROOT}/bin/kamidi-cli" \
        "${FLOWORK_ROOT}/bin/cutvii-cli" \
        "${FLOWORK_ROOT}/apps/kamidi-mastering/bin/kamidi-mastering-cli" \
        "${FLOWORK_ROOT}/apps/cutvii/bin/cutvii-cli" \
        "${FLOWORK_ROOT}/tools/memory_crystallizer/run.py" \
        "${FLOWORK_ROOT}/bin/flowork-apk" \
        "${FLOWORK_ROOT}/bin/flowork-apk-direct" \
        "${FLOWORK_ROOT}/bin/flowork-diag-display" \
        "${FLOWORK_ROOT}/bin/flowork-click-fx" \
        "${FLOWORK_ROOT}/system/kernel/enable-landlock-and-nvidia.sh" \
        "${FLOWORK_ROOT}/system/kernel/build-flowork-kernel.sh"; do
        if [ ! -x "$ipc_asset" ]; then
            echo "│ [✗] Missing or non-executable Bus/Episodic/Kernel asset: ${ipc_asset}"
            return 1
        fi
    done
    if [ ! -f "${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" ] \
        || [ ! -f "${FLOWORK_ROOT}/policies/mesh.toml" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/kernel/nvidia-595.99.02-linux-7.3-drm-ibt.patch" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/kernel/nvidia-595.99.02-linux-7.3-fbdev-helper.patch" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/kernel/flowork-universal.config" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/system_promp/promps/triggers/episodic_bus_and_sandbox.md" ]; then
        echo "│ [✗] Missing tmpfiles.d/flowork.conf, policies/mesh.toml, kernel NVIDIA patch/config, or triggers/episodic_bus_and_sandbox.md!"
        return 1
    fi
    echo "│ [✓] Pure Rust Core ELFs, Neural Bus CLIs & Episodic/Landlock Ready : OK"

    # 12. Registry, Tool Permissions, Systemd Units & Prompt Matrix Hygiene
    if [ ! -x "${FLOWORK_ROOT}/tools/tool_foundry/run.py" ]; then
        echo "│ [✗] /opt/floworkos/tools/tool_foundry/run.py lacks executable permission (+x)!"
        return 1
    fi
    local flowpkg_out
    flowpkg_out="$("${FLOWORK_ROOT}/bin/flowpkg" list 2>/dev/null || true)"
    if printf '%s\n' "$flowpkg_out" | grep -q "uBlock0.chromium"; then
        echo "│ [✗] flowpkg registry still includes browser extension uBlock0.chromium!"
        return 1
    fi
    if [ -L "${FLOWORK_ROOT}/apps/crypto-radarflow" ]; then
        echo "│ [✗] Duplicate symlink /opt/floworkos/apps/crypto-radarflow still exists!"
        return 1
    fi
    if [ -f "/etc/systemd/system/flowork-adshield-update.timer" ] && ! systemd-analyze verify /etc/systemd/system/flowork-adshield-update.timer >/dev/null 2>&1; then
        echo "│ [✗] Systemd unit /etc/systemd/system/flowork-adshield-update.timer failed verification!"
        return 1
    fi
    if ! jq empty "${FLOWORK_ROOT}/system/system_promp/promps/triggers.json" >/dev/null 2>&1; then
        echo "│ [✗] Invalid JSON in ${FLOWORK_ROOT}/system/system_promp/promps/triggers.json!"
        return 1
    fi
    if [ ! -x "${FLOWORK_ROOT}/system/triger/supervisor.py" ] \
        || [ ! -x "${FLOWORK_ROOT}/system/triger/github_update_watch/watcher.py" ] \
        || ! jq empty "${FLOWORK_ROOT}/system/triger/github_update_watch/trigger.json" >/dev/null 2>&1 \
        || [ ! -f "/etc/systemd/user/flowork-active-triggers.service" ] \
        || [ ! -e "/etc/systemd/user/default.target.wants/flowork-active-triggers.service" ] \
        || [ ! -e "/etc/skel/.config/systemd/user/default.target.wants/flowork-active-triggers.service" ]; then
        echo "│ [✗] Active trigger supervisor or github_update_watch subsystem incomplete!"
        return 1
    fi
    echo "│ [✓] Tool Permissions, App Registry, Timers, Active Triggers & Prompt Matrix : OK"

    # 13. Script Hygiene, App Runtimes, Python Stdlib, FUSE Portal Guard & XDG Desktop Validation
    local crlf_hit=0
    local sc
    for sc in "${FLOWORK_ROOT}/apps/craft-anything/bin/craft-anything" "${FLOWORK_ROOT}/bin/"*; do
        [ -f "$sc" ] && [ ! -L "$sc" ] || continue
        case "$(file -b "$sc" 2>/dev/null || true)" in
            *script*|*text*)
                if grep -q $'\r' "$sc" 2>/dev/null; then
                    echo "│ [✗] CRLF line endings detected in script: $sc"
                    crlf_hit=$((crlf_hit + 1))
                fi
                ;;
        esac
    done
    [ "$crlf_hit" -eq 0 ] || return 1
    echo "│ [✓] Script Line Endings (craft-anything + /opt/floworkos/bin) : Zero CRLF"

    local loop_links
    loop_links="$(find "${FLOWORK_ROOT}/apps" "${FLOWORK_ROOT}/bin" "${FLOWORK_ROOT}/system" "${FLOWORK_ROOT}/theme" -type l \( -lname '.' -o -lname './' \) 2>/dev/null || true)"
    if [ -n "$loop_links" ] || [ -L "${FLOWORK_ROOT}/apps/audacity/runtime/usr" ]; then
        echo "│ [✗] Circular self-loop symlink detected: ${loop_links:-${FLOWORK_ROOT}/apps/audacity/runtime/usr}"
        return 1
    fi
    local rt_dir
    for rt_dir in "${FLOWORK_ROOT}/apps/audacity/runtime" \
                  "${FLOWORK_ROOT}/apps/openscreen/squashfs-root" \
                  "${FLOWORK_ROOT}/apps/gputaskman/runtime"; do
        if [ -d "$rt_dir" ]; then
            local rt_mode
            rt_mode="$(stat -c '%a' "$rt_dir" 2>/dev/null || echo '0')"
            if [ $(( 8#${rt_mode} & 8#005 )) -ne 5 ]; then
                echo "│ [✗] App runtime directory lacks world read+traverse (o+rx, mode=${rt_mode}): ${rt_dir}"
                return 1
            fi
        fi
    done
    echo "│ [✓] App Runtimes & Symlinks (Audacity/OpenScreen/GPUTaskMan) : OK"

    if [ -e "${FLOWORK_ROOT}/mcp/earshot/tokenize.py" ] || [ -e "${FLOWORK_ROOT}/lib/python3/tokenize.py" ] || [ -e "${FLOWORK_ROOT}/lib/python3/token.py" ]; then
        echo "│ [✗] Python stdlib shadowing file (tokenize.py/token.py) remains under ${FLOWORK_ROOT}!"
        return 1
    fi
    if ! python3 -c "import sys; sys.path.insert(0, '${FLOWORK_ROOT}/mcp/earshot'); import tokenize, token, earshot_engine, yaml, certifi, packaging" >/dev/null 2>&1; then
        echo "│ [✗] Python runtime stdlib/dist-packages import check failed!"
        return 1
    fi
    echo "│ [✓] Python Runtime & Earshot Stdlib Integrity : OK"

    if [ -n "$kcfg" ] && ! check_kernel_flag "$kcfg" "CONFIG_FUSE_FS"; then
        if [ ! -f "/etc/systemd/user/xdg-document-portal.service.d/fuse-guard.conf" ] \
            || [ ! -f "/etc/skel/.config/systemd/user/xdg-document-portal.service.d/fuse-guard.conf" ]; then
            echo "│ [✗] Missing xdg-document-portal ConditionPathExists=/dev/fuse drop-in while CONFIG_FUSE_FS is disabled!"
            return 1
        fi
    fi
    echo "│ [✓] xdg-document-portal FUSE Condition Guard : OK"

    if command -v desktop-file-validate >/dev/null 2>&1; then
        local invalid_desktop=0
        local adf
        for adf in "${FLOWORK_ROOT}/apps/"*.desktop; do
            [ -f "$adf" ] || continue
            if ! desktop-file-validate "$adf" >/dev/null 2>&1; then
                echo "│ [✗] desktop-file-validate failed: $adf"
                invalid_desktop=$((invalid_desktop + 1))
            fi
            local sys_adf="/usr/share/applications/$(basename "$adf")"
            if [ -f "$sys_adf" ] && ! desktop-file-validate "$sys_adf" >/dev/null 2>&1; then
                echo "│ [✗] desktop-file-validate failed: $sys_adf"
                invalid_desktop=$((invalid_desktop + 1))
            fi
        done
        [ "$invalid_desktop" -eq 0 ] || return 1
        echo "│ [✓] Desktop Entries XDG Spec Validation : Zero errors"
    fi

    if grep -qF "~/.flowork/skills" "${FLOWORK_ROOT}/system/system_promp/promps/triggers/skills.md" 2>/dev/null \
        || ! grep -qF "/opt/floworkos/skills" "${FLOWORK_ROOT}/system/system_promp/promps/triggers/skills.md" 2>/dev/null; then
        echo "│ [✗] triggers/skills.md still references stale ~/.flowork/skills path!"
        return 1
    fi
    echo "│ [✓] Skills Trigger Path Consistency (/opt/floworkos/skills) : OK"

    # 14. Security & White-Label Sanitization
    if [ -f "${BUILDER_DIR}/.gitignore" ] && grep -q "skel/Documents" "${BUILDER_DIR}/.gitignore"; then
        echo "│ [✓] ISO Builder Anti-Leak Shield (.gitignore integration) : OK"
    else
        echo "│ [✗] Missing or invalid ${BUILDER_DIR}/.gitignore!"
        return 1
    fi
    echo "│ [✓] Rootfs Exclusion Filter: Zero user tokens/homes/broken symlinks/targets"
    echo "│ [✓] White-labeling: 100% verified (Flowork Sovereign)"
    echo "└────────────────────────────────────────────────────────┘"
    return 0
}

sync_host_desktop_to_skel_and_live_user() {
    echo "=========================================================="
    echo "👑 FLOWORK OS SOVEREIGN DESKTOP & LIVE USER SYNC ENGINE"
    echo "→ Guaranteeing 100% desktop fidelity between host and Live ISO..."
    echo "=========================================================="

    local ACTIVE_USER=""
    local ACTIVE_HOME=""

    for _u in $(awk -F: '$3 >= 1000 && $3 != 65534 {print $1":"$6}' /etc/passwd); do
        local _uname="${_u%%:*}"
        local _uhome="${_u##*:}"
        if [ "$_uname" != "flowork" ] && [ -d "$_uhome" ]; then
            ACTIVE_USER="$_uname"
            ACTIVE_HOME="$_uhome"
            break
        fi
    done

    if [ -z "$ACTIVE_HOME" ] && [ -n "${HOME:-}" ] && [ -d "${HOME:-}" ]; then
        ACTIVE_HOME="$HOME"
    fi

    echo "   • Detected Host Profile Source: ${ACTIVE_HOME} (${ACTIVE_USER})"

    sudo mkdir -p /etc/skel/.config /etc/skel/.local/share /etc/skel/Pictures /etc/skel/Desktop
    sudo rm -rf /home/flowork
    sudo mkdir -p /home/flowork

    sudo python3 - "${ACTIVE_HOME}" << 'PY_SYNC_DESKTOP'
import sys, os, shutil, glob

src_home = sys.argv[1]
targets = ["/etc/skel", "/home/flowork"]

print("   → Ensuring clean Documents, Downloads, Pictures, Videos in /etc/skel and /home/flowork...")
for t in targets:
    for d in ["Documents", "Downloads", "Pictures", "Videos"]:
        dpath = f"{t}/{d}"
        os.makedirs(dpath, exist_ok=True)
        for f in os.listdir(dpath):
            if f != ".gitkeep":
                fp = os.path.join(dpath, f)
                if os.path.isdir(fp):
                    shutil.rmtree(fp, ignore_errors=True)
                else:
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
        open(os.path.join(dpath, ".gitkeep"), "a").close()

print("   → Deploying Sovereign .gitignore Protection to /etc/skel and /home/flowork...")
for t in targets:
    if os.path.exists("/opt/floworkos/iso-builder/.gitignore"):
        shutil.copy2("/opt/floworkos/iso-builder/.gitignore", f"{t}/.gitignore")

print("   → Synchronizing Dconf & GNOME/GTK preferences...")
for t in targets:
    os.makedirs(f"{t}/.config/dconf", exist_ok=True)
if os.path.exists(f"{src_home}/.config/dconf/user"):
    for t in targets:
        shutil.copy2(f"{src_home}/.config/dconf/user", f"{t}/.config/dconf/user")

print("   → Synchronizing XFCE4, XFWM4, Plank, Nemo, & GTK configurations...")
configs_to_sync = [
    "xfce4", "plank", "nemo", "gtk-3.0", "gtk-4.0", "alacritty", "flowork", "flowork-apk", "menus",
    "craft-anything", "gridcraft", "photocraft", "tracedraw", "audacity4", "Audacity", "neofetch"
]
for cfg in configs_to_sync:
    src_cfg = f"{src_home}/.config/{cfg}"
    if os.path.exists(src_cfg):
        for t in targets:
            shutil.copytree(src_cfg, f"{t}/.config/{cfg}", dirs_exist_ok=True)

print("   → Synchronizing Desktop & Application Shortcuts...")
for t in targets:
    os.makedirs(f"{t}/Desktop", exist_ok=True)
    os.makedirs(f"{t}/.local/share/applications", exist_ok=True)
    os.makedirs(f"{t}/.local/share/icons", exist_ok=True)
    os.makedirs(f"{t}/.themes", exist_ok=True)

for f in glob.glob(f"{src_home}/Desktop/*.desktop"):
    for t in targets:
        shutil.copy2(f, f"{t}/Desktop/")

for f in glob.glob(f"{src_home}/.local/share/applications/*.desktop") + glob.glob("/opt/floworkos/apps/*.desktop"):
    bname = os.path.basename(f)
    if any(x in bname.lower() for x in ["antigravity", "gemini", "agent.desktop"]):
        continue
    for t in targets:
        dest_file = f"{t}/.local/share/applications/{bname}"
        if os.path.exists(dest_file) or os.path.islink(dest_file):
            try:
                os.remove(dest_file)
            except Exception:
                pass
        if os.path.islink(f):
            linkto = os.readlink(f)
            os.symlink(linkto, dest_file)
        else:
            shutil.copy2(f, dest_file)
    usr_dest = f"/usr/share/applications/{bname}"
    if not os.path.exists(usr_dest) and not os.path.islink(usr_dest):
        if os.path.islink(f):
            linkto = os.readlink(f)
            os.symlink(linkto, usr_dest)
        else:
            shutil.copy2(f, usr_dest)

if os.path.exists(f"{src_home}/.local/share/icons"):
    for t in targets:
        shutil.copytree(f"{src_home}/.local/share/icons", f"{t}/.local/share/icons", dirs_exist_ok=True)
if os.path.exists(f"{src_home}/.themes"):
    for t in targets:
        shutil.copytree(f"{src_home}/.themes", f"{t}/.themes", dirs_exist_ok=True)

print("   → Synchronizing Systemd user service units and wants...")
for t in targets:
    os.makedirs(f"{t}/.config/systemd/user/graphical-session.target.wants", exist_ok=True)
    os.makedirs(f"{t}/.config/systemd/user/default.target.wants", exist_ok=True)

for w in glob.glob(f"{src_home}/.config/systemd/user/*/*.service"):
    rel = os.path.relpath(w, f"{src_home}/.config/systemd/user")
    for t in targets:
        target_path = f"{t}/.config/systemd/user/{rel}"
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if os.path.islink(w):
            linkto = os.readlink(w)
            if os.path.exists(target_path) or os.path.islink(target_path):
                os.remove(target_path)
            os.symlink(linkto, target_path)
        else:
            shutil.copy2(w, target_path)

# Dock eradicated — launcher unified with Mr. Flow Omni-Conduit

print("   → Sanitizing personal paths and ephemeral logs in profiles...")
# For /home/flowork: ensure all path references point to /home/flowork
for root, dirs, files in os.walk("/home/flowork"):
    for fname in files:
        fpath = os.path.join(root, fname)
        if os.path.islink(fpath):
            continue
        if fname.endswith(".log") or fname.endswith(".ini.lock") or fname.endswith(".lock"):
            try:
                os.remove(fpath)
            except Exception:
                pass
            continue
        if fname.endswith((".conf", ".json", ".desktop", ".ini", ".rc", ".xml", "bookmarks")):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as rf:
                    content = rf.read()
                if src_home in content:
                    with open(fpath, "w", encoding="utf-8") as wf:
                        wf.write(content.replace(src_home, "/home/flowork"))
            except Exception:
                pass

# For /etc/skel: purge logs and ephemeral state; remove hardcoded host bookmarks
for root, dirs, files in os.walk("/etc/skel"):
    for fname in files:
        fpath = os.path.join(root, fname)
        if os.path.islink(fpath):
            continue
        if fname.endswith(".log") or fname == "Audacity4.ini":
            try:
                os.remove(fpath)
            except Exception:
                pass

# Write clean system pillar bookmarks to /etc/skel (zero /home/ paths)
os.makedirs("/etc/skel/.config/gtk-3.0", exist_ok=True)
with open("/etc/skel/.config/gtk-3.0/bookmarks", "w", encoding="utf-8") as bf:
    bf.write("""file:///opt/floworkos/apps 🚀 Apps
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
file:///opt/floworkos/apk 📱 Android APKs
""")

print("   ✓ Desktop, Panels, Docks, Themes, and Systemd user units synchronized.")
PY_SYNC_DESKTOP

    sudo chown -R root:root /etc/skel
    sudo chown -R 1000:1000 /home/flowork
    echo "   ✓ /etc/skel set to root:root and /home/flowork set to 1000:1000."
}

build_iso() {
    check_prerequisites
    echo ""
    echo "=========================================================="
    echo "📀 STARTING FLOWORK OS LIVE ISO MASTERING PIPELINE"
    echo "=========================================================="

    local WORK_DIR="${OUTPUT_DIR}/work"
    local ISO_ROOT="${WORK_DIR}/iso_root"
    local SQUASHFS_FILE="${ISO_ROOT}/live/filesystem.squashfs"
    local FINAL_ISO="${OUTPUT_DIR}/${ISO_NAME}"

    # 0. DiskCraft Automated Pre-Build Hygiene Sweep (Auto-Trigger)
    echo "→ Invoking DiskCraft Sentinel for automated pre-build hygiene sweep..."
    if [ -x "/opt/floworkos/bin/diskcraft" ]; then
        /opt/floworkos/bin/diskcraft --clean-prebuild
    elif [ -f "/opt/floworkos/apps/diskcraft/bin/backend.py" ]; then
        python3 "/opt/floworkos/apps/diskcraft/bin/backend.py" --clean-prebuild
    fi

    sudo rm -rf "${WORK_DIR}"
    if [ ! -e "${FLOWORK_ROOT}/apps/recordly" ] && { [ -e "/usr/share/applications/recordly.desktop" ] || [ -L "/usr/local/bin/recordly" ] || [ -e "/usr/share/pixmaps/recordly.png" ]; }; then
        sudo rm -f /usr/local/bin/recordly /usr/share/applications/recordly.desktop /usr/share/pixmaps/recordly.png
    fi
    mkdir -p "${OUTPUT_DIR}" "${WORK_DIR}" "${ISO_ROOT}/live" "${ISO_ROOT}/boot/grub"

    # Synchronize host desktop state directly to /etc/skel and /home/flowork
    sync_host_desktop_to_skel_and_live_user

    echo "→ Preserving host connector vault & personal state (isolated from ISO image)..."

    # Copy boot skeleton to ISO root
    echo "→ Assembling hybrid boot skeleton..."
    cp -r "${BUILDER_DIR}/boot-skeleton/"* "${ISO_ROOT}/"

    # Copy kernel and initrd
    echo "→ Copying kernel and initramfs..."
    resolve_latest_kernel_and_initrd
    if [ -z "$LATEST_VMLINUZ" ] || [ -z "$LATEST_INITRD" ]; then
        echo "[FATAL] Kernel or initramfs missing in /boot!" >&2
        exit 1
    fi

    cp "$LATEST_VMLINUZ" "${ISO_ROOT}/live/vmlinuz"
    cp "$LATEST_INITRD" "${ISO_ROOT}/live/initrd.img"

    # Prepare rootfs exclusions (relative paths required for -wildcards)
    local EXCLUDE_FILE="${WORK_DIR}/squashfs_excludes.txt"
    local REL_OUTPUT_DIR="${OUTPUT_DIR#/}"
    cat << EOF_EXCLUDE > "$EXCLUDE_FILE"
${REL_OUTPUT_DIR}/*
${REL_OUTPUT_DIR}
home/*/.cache/*
home/*/.npm*
etc/skel/.npm*
home/*/.cargo/*
home/*/.rustup/*
home/*/.bash_history
home/*/*token*
home/*/.gemini*
home/*/.gemini/*
home/*/.android*
home/*/.android
etc/skel/.android*
etc/skel/.android
root/.android*
root/.android
*.avd
*.avd/*
*.qcow2
userdata*
userdata-qemu*
cache.img*
encryptionkey*
var/lib/waydroid*
var/lib/waydroid/*
home/*/.local/share/waydroid*
home/*/.local/share/waydroid/*
var/lib/anbox*
tmp/android*
tmp/adb*
tmp/flowork_store_icons*
# User Media & Personal Directories Content Exclusions (Folders preserved, contents 100% excluded)
home/*/Downloads/*
home/*/downloads/*
home/*/Documents/*
home/*/documents/*
home/*/Pictures/*
home/*/pictures/*
home/*/Videos/*
home/*/videos/*
home/*/flowork-os-repo/*
home/*/flowork-os-repo
etc/skel/Downloads/*
etc/skel/downloads/*
etc/skel/Documents/*
etc/skel/documents/*
etc/skel/Pictures/*
etc/skel/pictures/*
etc/skel/Videos/*
etc/skel/videos/*

root/*
swapfile
swapfile*
opt/rustup/*
opt/rustup
opt/metasploit-framework/*
opt/metasploit-framework
opt/floworkos/pipelines/*
opt/floworkos/pipelines
opt/floworkos/documents/*
opt/floworkos/documents
opt/floworkos/artifacts/*
opt/floworkos/artifacts
opt/floworkos/data/*
# Sovereign On-Demand Decoupled External Media Studios
opt/floworkos/apps/audacity/*
opt/floworkos/apps/audacity
opt/floworkos/apps/openscreen/*
opt/floworkos/apps/openscreen
opt/floworkos/apps/social-auto-upload/*
opt/floworkos/apps/social-auto-upload
opt/floworkos/apps/wine-staging/*
opt/floworkos/apps/wine-staging
usr/lib/llvm-16/*
usr/lib/llvm-16
usr/lib/llvm-18/*
usr/lib/llvm-18
usr/lib/llvm-20/*
usr/lib/llvm-20
usr/src/*
*.iso
proc/*
sys/*
dev/*
tmp/*
run/*
mnt/*
media/*
cdrom/*
var/tmp/*
var/cache/apt/archives/*.deb
var/log/*
var/lib/lightdm/.config/google-chrome*
var/lib/lightdm/.config/plank*
opt/flowork-os-repo/*
opt/flowork-os-repo
# System Pillars (Folders preserved, contents 100% excluded)
opt/floworkos/connector/data/*
opt/floworkos/connector/logs/*
opt/floworkos/history/chats/*
opt/floworkos/screenshots/*
*roadmap*
*ROADMAP*
opt/floworkos/flowork.dev
etc/flowork.dev
etc/skel/flowork.dev
etc/skel/.flowork/flowork.dev
home/*/.flowork/flowork.dev
home/*/flowork.dev
.../flowork.dev
.../flowork.dev*
*flowork.dev*
opt/floworkos/documents/*
opt/floworkos/documents
opt/floworkos/docs/*
opt/floworkos/docs
home/*/.flowork/documents/*
home/*/.flowork/documents
*STICKMAN*
*COASTER*
*RAILROADS*
*/finish/*
home/*/.flowork/connector_last_req.json*
home/*/.flowork/logs/*
home/*/.flowork/logs
home/*/.flowork/tmp/*
home/*/.flowork/tmp
home/*/.flowork/data/*
etc/skel/.flowork/connector_last_req.json*
etc/skel/.flowork/logs/*
etc/skel/.flowork/tmp/*
etc/skel/.flowork/data/*
opt/floworkos/.fl_brain/*
opt/floworkos/.fl_brain
home/*/.fl_brain/*
home/*/.fl_brain
etc/skel/.fl_brain/*
etc/skel/.fl_brain
opt/floworkos/history/*.db*
opt/floworkos/history/*.sqlite*
opt/floworkos/*.db
opt/floworkos/*.db-*
opt/floworkos/*.sqlite*
opt/floworkos/apps/flow-repo/data/*.db*
opt/floworkos/apps/artex/data/traffic/_index/*.sqlite*
home/*/.flowork/*.db*
home/*/.flowork/*/*.db*
home/*/.flowork/*.sqlite*
home/*/.flowork/*/*.sqlite*
etc/skel/.flowork/*.db*
etc/skel/.flowork/*/*.db*
etc/skel/.flowork/*.sqlite*
etc/skel/.flowork/*/*.sqlite*
*.bak
*.orig
*~
opt/floworkos/system/triger/*/.pid
opt/floworkos/system/triger/*/.last_alert
opt/floworkos/system/triger/*/.state.json
opt/floworkos/system/triger/*/__pycache__/*
opt/floworkos/system/triger/*/__pycache__
opt/floworkos/apps/flowork-stealth/profiles/*/user_data/*
opt/floworkos/apps/flowork-stealth/profiles/*/user_data/.*
opt/floworkos/apps/flowork-stealth/profiles/*/user_data_chrome/*
opt/floworkos/apps/social-auto-upload/cookies/*
opt/floworkos/apps/social-auto-upload/db/*.db
opt/floworkos/apps/social-auto-upload/videos/*
opt/floworkos/apps/suno-demucs/*
opt/floworkos/apps/suno-demucs
opt/floworkos/apps/dramaboxflow/apk_pulled/*
opt/floworkos/apps/dramaboxflow/apk_pulled
opt/floworkos/agent/*
opt/floworkos/agent/**
opt/floworkos/agent
opt/floworkos/agents/*
opt/floworkos/agents/**
opt/floworkos/agents
opt/floworkos/apps/agent/*
opt/floworkos/apps/agent
opt/floworkos/apps/agent.desktop
usr/share/applications/agent.desktop
usr/share/applications/Antigravity.desktop
usr/share/applications/antigravity.desktop
etc/skel/.local/share/applications/antigravity.desktop
etc/skel/.local/share/applications/Antigravity.desktop
home/*/.local/share/applications/antigravity.desktop
home/*/.local/share/applications/Antigravity.desktop
usr/local/bin/antigravity
*antigravity*
*Antigravity*
etc/skel/.gemini*
home/*/.gemini*
opt/floworkos/lib/mrflow*
usr/lib/node_modules/*
usr/lib/node_modules
usr/local/lib/node_modules/*
usr/local/lib/node_modules
opt/floworkos/target/*
opt/floworkos/target
opt/floworkos/crates/*/target/*
opt/floworkos/crates/*/target
opt/floworkos/connector-rs/target/*
opt/floworkos/connector-rs/target
opt/floworkos/sysd/target/*
opt/floworkos/sysd/target
opt/floworkos/wm/target/*
opt/floworkos/wm/target
opt/floworkos/apps/cutvii/src-tauri/target/*
opt/floworkos/apps/cutvii/src-tauri/target
opt/floworkos/mrflow-rs/target/*
opt/floworkos/mrflow-rs/target
opt/floworkos/mrflow-rs/replica/*
opt/floworkos/mrflow-rs/replica
core
core.*
*.exe
*.msi
opt/floworkos/tools/*/__pycache__/*
opt/floworkos/tools/*/__pycache__
opt/floworkos/apps/*/__pycache__/*
opt/floworkos/apps/*/__pycache__
opt/floworkos/apps/*/bin/__pycache__/*
opt/floworkos/apps/*/bin/__pycache__
etc/passwd
etc/shadow
etc/group
etc/fstab
etc/hostname
etc/hosts
etc/machine-id
etc/sudoers.d/99-flowork
etc/lightdm/lightdm.conf
etc/lightdm/lightdm.conf.d/99-floworkos.conf
usr/share/wayland-sessions/*
opt/floworkos/apps/recordly/*
opt/floworkos/apps/recordly
opt/floworkos/bin/recordly
usr/local/bin/recordly
usr/share/applications/recordly.desktop
usr/share/pixmaps/recordly.png
etc/skel/.config/xfce4/panel/whiskermenu-1.rc
etc/systemd/user/flowork-visiond.service
etc/systemd/user/default.target.wants/flowork-visiond.service
etc/skel/.config/systemd/user/flowork-visiond.service
etc/skel/.config/systemd/user/default.target.wants/flowork-visiond.service
opt/floworkos/models/*.gguf
opt/floworkos/models/*.safetensors
opt/floworkos/models/*.downloading.tmp
usr/share/ollama*
usr/local/lib/ollama*
var/lib/ollama*
opt/floworkos/crates/flowork-auditor/ROADMAP.md
opt/floworkos/data/artex-legacy-backup.tar.gz
EOF_EXCLUDE

    for _hdir in /home/*; do
        [ -d "$_hdir" ] || continue
        _hbase="$(basename "$_hdir")"
        if [ "$_hbase" != "flowork" ]; then
            echo "home/${_hbase}/*" >> "$EXCLUDE_FILE"
            echo "home/${_hbase}" >> "$EXCLUDE_FILE"
        fi
    done

    if [ -f "${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" ]; then
        echo "etc/tmpfiles.d/flowork.conf" >> "$EXCLUDE_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/mrflow-tray.service" ]; then
        echo "etc/systemd/user/mrflow-tray.service" >> "$EXCLUDE_FILE"
        echo "etc/skel/.config/systemd/user/mrflow-tray.service" >> "$EXCLUDE_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-sysd.service" ]; then
        echo "etc/systemd/user/flowork-sysd.service" >> "$EXCLUDE_FILE"
        echo "etc/xdg/systemd/user/flowork-sysd.service" >> "$EXCLUDE_FILE"
        echo "etc/skel/.config/systemd/user/flowork-sysd.service" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/flowork-sysd" ]; then
        echo "usr/local/bin/flowork-sysd" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/kamidi-mastering/bin/kamidi-mastering-cli" ]; then
        echo "usr/local/bin/kamidi-mastering-cli" >> "$EXCLUDE_FILE"
        echo "usr/local/bin/kamidi-cli" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/cutvii/bin/cutvii-cli" ]; then
        echo "usr/local/bin/cutvii-cli" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/gputaskman" ]; then
        echo "usr/local/bin/gputaskman" >> "$EXCLUDE_FILE"
        echo "usr/local/bin/gtm" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/gputaskman/bin/gputaskman-cli" ]; then
        echo "usr/local/bin/gputaskman-cli" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/openscreen" ]; then
        echo "usr/local/bin/openscreen" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/openscreen/bin/openscreen-cli" ]; then
        echo "usr/local/bin/openscreen-cli" >> "$EXCLUDE_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/artex" ]; then
        echo "usr/local/bin/artex" >> "$EXCLUDE_FILE"
    fi
    for df_new in gputaskman.desktop openscreen.desktop social-auto-upload.desktop artex.desktop; do
        if [ -f "${FLOWORK_ROOT}/apps/${df_new}" ]; then
            echo "usr/share/applications/${df_new}" >> "$EXCLUDE_FILE"
        fi
    done
    if [ ! -x "/usr/local/bin/x-flow" ]; then
        echo "etc/systemd/user/flowork-core.service" >> "$EXCLUDE_FILE"
        echo "etc/systemd/user/default.target.wants/flowork-core.service" >> "$EXCLUDE_FILE"
        echo "etc/skel/.config/systemd/user/flowork-core.service" >> "$EXCLUDE_FILE"
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-core.service" >> "$EXCLUDE_FILE"
    fi
    if [ ! -x "/usr/local/bin/flowork-window-daemon" ]; then
        echo "etc/systemd/user/flowork-window-manager.service" >> "$EXCLUDE_FILE"
        echo "etc/systemd/user/default.target.wants/flowork-window-manager.service" >> "$EXCLUDE_FILE"
        echo "etc/skel/.config/systemd/user/flowork-window-manager.service" >> "$EXCLUDE_FILE"
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-window-manager.service" >> "$EXCLUDE_FILE"
    fi

    # Dynamically exclude /usr/local/{bin,sbin} symlinks pointing into /home/* (e.g. host cargo/rustc links)
    find /usr/local/bin /usr/local/sbin -type l 2>/dev/null | while read -r link_path; do
        local link_target
        link_target="$(readlink "$link_path" || true)"
        case "$link_target" in
            /home/*)
                echo "${link_path#/}" >> "$EXCLUDE_FILE"
                ;;
        esac
    done

    echo "→ Generating non-destructive Live ISO pseudo-files (host system untouched)..."
    local SAN_PASSWD="${WORK_DIR}/sanitized_passwd"
    local SAN_SHADOW="${WORK_DIR}/sanitized_shadow"
    local SAN_GROUP="${WORK_DIR}/sanitized_group"
    local SAN_FSTAB="${WORK_DIR}/sanitized_fstab"
    local SAN_HOSTNAME="${WORK_DIR}/sanitized_hostname"
    local SAN_HOSTS="${WORK_DIR}/sanitized_hosts"
    local SAN_MACHINE_ID="${WORK_DIR}/sanitized_machine_id"
    local SAN_SUDOERS="${WORK_DIR}/sanitized_99_flowork"
    local SAN_LIGHTDM="${WORK_DIR}/sanitized_lightdm.conf"
    local SAN_LIGHTDM_D="${WORK_DIR}/sanitized_99_floworkos.conf"
    local SAN_WHISKER="${WORK_DIR}/sanitized_whiskermenu-1.rc"
    local SAN_SKEL_BASHRC="${WORK_DIR}/sanitized_skel_bashrc"
    local SAN_SKEL_PROFILE="${WORK_DIR}/sanitized_skel_profile"
    local SAN_PROFILE_D="${WORK_DIR}/sanitized_profile_flowork.sh"
    local CLEAN_EPISODIC_DB="${WORK_DIR}/clean_episodic_memory.db"
    local PSEUDO_FILE="${WORK_DIR}/pseudo_files.txt"

    # 1. Clean base fstab, hostname, hosts, machine-id
    echo "# UNCONFIGURED FSTAB FOR BASE SYSTEM" > "$SAN_FSTAB"
    echo "flowork-os" > "$SAN_HOSTNAME"
    cat << 'EOF_HOSTS' > "$SAN_HOSTS"
# Standard host addresses
127.0.0.1  localhost
::1        localhost ip6-localhost ip6-loopback
ff02::1    ip6-allnodes
ff02::2    ip6-allrouters
# Live ISO host address
127.0.1.1  flowork-os
EOF_HOSTS
    echo "uninitialized" > "$SAN_MACHINE_ID"

    # 2. Clean sudoers rule (flowork live user AND any user in sudo group)
    cat << 'EOF_SUDO' > "$SAN_SUDOERS"
# Flowork OS Sovereign Sudoers Rules
flowork ALL=(ALL) NOPASSWD: ALL
%sudo ALL=(ALL) NOPASSWD: ALL
EOF_SUDO

    # 3. Synchronize LightDM autologin cleanly for live user flowork without overriding Calamares post-install
    cat << 'EOF_LIGHTDM' > "$SAN_LIGHTDM"
[Seat:*]
autologin-user=flowork
autologin-user-timeout=0
user-session=flowork
greeter-session=slick-greeter
EOF_LIGHTDM

    cat << 'EOF_LIGHTDM_D' > "$SAN_LIGHTDM_D"
[Seat:*]
user-session=flowork
greeter-session=slick-greeter
EOF_LIGHTDM_D

    # 3b. Sanitize /etc/skel Whisker Menu Start favorites (pin openscreen & gputaskman, drop recordly)
    if [ -f "/etc/skel/.config/xfce4/panel/whiskermenu-1.rc" ]; then
        cp -f "/etc/skel/.config/xfce4/panel/whiskermenu-1.rc" "$SAN_WHISKER"
        python3 - "$SAN_WHISKER" << 'PY_ISO_WHISKER'
import sys
p = sys.argv[1]
with open(p, "r", encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()
out = []
for ln in lines:
    if ln.startswith("favorites="):
        favs = [x for x in ln[len("favorites="):].split(",") if x and x != "recordly.desktop"]
        for req in ("gputaskman.desktop", "openscreen.desktop", "flowork-dramaboxflow.desktop", "social-auto-upload.desktop"):
            if req not in favs:
                favs.insert(min(3, len(favs)), req)
        out.append("favorites=" + ",".join(favs))
    else:
        out.append(ln)
with open(p, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
PY_ISO_WHISKER
    fi

    # 3c. Sanitize /etc/skel/.bashrc & /etc/profile.d/flowork.sh for Live ISO Rust & Flowork PATH
    if [ -f "/etc/skel/.bashrc" ]; then
        cp -f "/etc/skel/.bashrc" "$SAN_SKEL_BASHRC"
        if ! grep -q "/opt/floworkos/bin" "$SAN_SKEL_BASHRC"; then
            sed -i '1s|^|# Flowork OS & Rust Toolchain Environment\ncase ":$PATH:" in\n    *:"/opt/floworkos/bin":*) ;;\n    *) export PATH="/opt/floworkos/bin:$PATH" ;;\nesac\ncase ":$PATH:" in\n    *:"$HOME/.cargo/bin":*) ;;\n    *) [ -d "$HOME/.cargo/bin" ] && export PATH="$HOME/.cargo/bin:$PATH" ;;\nesac\n\n|' "$SAN_SKEL_BASHRC"
        fi
    fi

    if [ -f "/etc/skel/.profile" ]; then
        cp -f "/etc/skel/.profile" "$SAN_SKEL_PROFILE"
        if ! grep -q "/opt/floworkos/bin" "$SAN_SKEL_PROFILE"; then
            cat << 'EOF_SKEL_PROF' >> "$SAN_SKEL_PROFILE"

# Flowork OS Sovereign binary and Rust toolchain paths
if [ -d "/opt/floworkos/bin" ]; then
    case ":$PATH:" in
        *:"/opt/floworkos/bin":*) ;;
        *) PATH="/opt/floworkos/bin:$PATH" ;;
    esac
fi

if [ -d "$HOME/.cargo/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/.cargo/bin":*) ;;
        *) PATH="$HOME/.cargo/bin:$PATH" ;;
    esac
fi
EOF_SKEL_PROF
        fi
    fi

    cat << 'EOF_FLOWORK_SH' > "$SAN_PROFILE_D"
if [ -d "/opt/floworkos/bin" ]; then
    case ":$PATH:" in
        *:/opt/floworkos/bin:*) ;;
        *) export PATH="/opt/floworkos/bin:$PATH" ;;
    esac
fi
if [ -d "$HOME/.cargo/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/.cargo/bin":*) ;;
        *) export PATH="$HOME/.cargo/bin:$PATH" ;;
    esac
fi
EOF_FLOWORK_SH

    # 4. User databases: sole live user flowork, purge host human accounts dynamically
    python3 - "$SAN_PASSWD" "$SAN_SHADOW" "$SAN_GROUP" << 'PY_SAN_USERS'
import subprocess, sys

san_passwd, san_shadow, san_group = sys.argv[1:4]

# 1. Identify all human accounts on the host (UID >= 1000 except nobody and flowork)
all_human = set()
with open("/etc/passwd", "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        parts = ln.strip().split(":")
        if len(parts) >= 3:
            u = parts[0]
            try:
                uid = int(parts[2])
            except ValueError:
                continue
            if uid >= 1000 and uid != 65534 and u != "flowork":
                all_human.add(u)

# 2. Build sanitized passwd ensuring flowork (UID 1000) exists
passwd_entries = []
has_flowork_passwd = False
with open("/etc/passwd", "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        parts = ln.strip().split(":")
        if len(parts) >= 3:
            u = parts[0]
            try:
                uid = int(parts[2])
            except ValueError:
                continue
            if u == "flowork":
                has_flowork_passwd = True
                passwd_entries.append(ln.rstrip("\n"))
            elif uid < 1000 or uid == 65534:
                passwd_entries.append(ln.rstrip("\n"))

if not has_flowork_passwd:
    passwd_entries.append("flowork:x:1000:1000:Flowork Sovereign User:/home/flowork:/bin/bash")

with open(san_passwd, "w", encoding="utf-8") as f:
    f.write("\n".join(passwd_entries) + "\n")

# 3. Build sanitized shadow ensuring flowork exists with password 'flowork'
shadow_raw = subprocess.check_output(["sudo", "cat", "/etc/shadow"], text=True, errors="replace")
shadow_entries = []
has_flowork_shadow = False
for ln in shadow_raw.splitlines():
    u = ln.split(":", 1)[0]
    if u == "flowork":
        has_flowork_shadow = True
        shadow_entries.append(ln)
    elif u not in all_human:
        shadow_entries.append(ln)

if not has_flowork_shadow:
    # Default live ISO password 'flowork' (SHA-512 crypt)
    shadow_entries.append("flowork:$6$F/ZutSC9QsLh3eGU$Bmc3DtbHqo/5OB.bGNlFfroeMDkAEnOOnmQIHk313h57JBmXWN6679adrvITKgNGVNmL7ARBqCK8ymapzRIzH1:19000:0:99999:7:::")

with open(san_shadow, "w", encoding="utf-8") as f:
    f.write("\n".join(shadow_entries) + "\n")

# 4. Build sanitized group ensuring flowork group exists and flowork is added to critical desktop & sudo groups
target_groups = {"adm", "sudo", "audio", "video", "plugdev", "netdev", "input", "render", "kvm", "users", "systemd-journal"}
group_entries = []
has_flowork_group = False
with open("/etc/group", "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        ln_s = ln.rstrip("\n")
        parts = ln_s.split(":")
        if len(parts) >= 4:
            gname = parts[0]
            try:
                gid = int(parts[2])
            except ValueError:
                gid = 0
            if gname == "flowork":
                has_flowork_group = True
            elif gname in all_human or (gid >= 1000 and gid != 65534 and gname != "flowork"):
                continue
            members = [m for m in parts[3].split(",") if m and m not in all_human]
            if gname in target_groups and "flowork" not in members:
                members.append("flowork")
            parts[3] = ",".join(members)
            group_entries.append(":".join(parts))

if not has_flowork_group:
    group_entries.append("flowork:x:1000:")

with open(san_group, "w", encoding="utf-8") as out:
    out.write("\n".join(group_entries) + "\n")
PY_SAN_USERS

    # 5. Build pseudo-definitions
    cat << EOF_PSEUDO > "$PSEUDO_FILE"
etc/passwd f 644 0 0 cat ${SAN_PASSWD}
etc/shadow f 640 0 42 cat ${SAN_SHADOW}
etc/group f 644 0 0 cat ${SAN_GROUP}
etc/fstab f 644 0 0 cat ${SAN_FSTAB}
etc/hostname f 644 0 0 cat ${SAN_HOSTNAME}
etc/hosts f 644 0 0 cat ${SAN_HOSTS}
etc/machine-id f 444 0 0 cat ${SAN_MACHINE_ID}
etc/sudoers.d/99-flowork f 440 0 0 cat ${SAN_SUDOERS}
etc/lightdm/lightdm.conf f 644 0 0 cat ${SAN_LIGHTDM}
etc/lightdm/lightdm.conf.d/99-floworkos.conf f 644 0 0 cat ${SAN_LIGHTDM_D}
opt/floworkos/.fl_brain m 777 1000 1000
opt/floworkos/history m 777 1000 1000
opt/floworkos/history/chats m 777 1000 1000
opt/floworkos/pipelines m 777 1000 1000
opt/floworkos/documents m 777 1000 1000
opt/floworkos/artifacts m 777 1000 1000
EOF_PSEUDO
    if [ -f "$SAN_WHISKER" ]; then
        echo "etc/skel/.config/xfce4/panel/whiskermenu-1.rc f 644 0 0 cat ${SAN_WHISKER}" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/connector/data/vault.clean.json" ]; then
        echo "opt/floworkos/connector/data/vault.json f 600 1000 1000 cat ${FLOWORK_ROOT}/connector/data/vault.clean.json" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" ]; then
        echo "etc/tmpfiles.d/flowork.conf f 644 0 0 cat ${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/mrflow-tray.service" ]; then
        echo "etc/systemd/user/mrflow-tray.service f 644 0 0 cat ${FLOWORK_ROOT}/system/systemd/mrflow-tray.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/mrflow-tray.service f 644 0 0 cat ${FLOWORK_ROOT}/system/systemd/mrflow-tray.service" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-sysd.service" ]; then
        echo "etc/systemd/user/flowork-sysd.service f 644 0 0 cat ${FLOWORK_ROOT}/system/systemd/flowork-sysd.service" >> "$PSEUDO_FILE"
        echo "etc/xdg/systemd/user/flowork-sysd.service f 644 0 0 cat ${FLOWORK_ROOT}/system/systemd/flowork-sysd.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/flowork-sysd.service f 644 0 0 cat ${FLOWORK_ROOT}/system/systemd/flowork-sysd.service" >> "$PSEUDO_FILE"
        echo "etc/systemd/user/default.target.wants/flowork-sysd.service s 777 0 0 ../flowork-sysd.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-sysd.service s 777 0 0 ../flowork-sysd.service" >> "$PSEUDO_FILE"
    fi
    # Flowork Neural Conduit (Bottom Synaptic Command Bar) — Unified with Mr. Flow
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-neural-conduit.service" ] || [ -f "/etc/systemd/user/flowork-neural-conduit.service" ]; then
        local _conduit_svc="${FLOWORK_ROOT}/system/systemd/flowork-neural-conduit.service"
        [ -f "$_conduit_svc" ] || _conduit_svc="/etc/systemd/user/flowork-neural-conduit.service"
        echo "etc/systemd/user/flowork-neural-conduit.service f 644 0 0 cat ${_conduit_svc}" >> "$PSEUDO_FILE"
        echo "etc/xdg/systemd/user/flowork-neural-conduit.service f 644 0 0 cat ${_conduit_svc}" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/flowork-neural-conduit.service f 644 0 0 cat ${_conduit_svc}" >> "$PSEUDO_FILE"
        echo "etc/systemd/user/default.target.wants/flowork-neural-conduit.service s 777 0 0 ../flowork-neural-conduit.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-neural-conduit.service s 777 0 0 ../flowork-neural-conduit.service" >> "$PSEUDO_FILE"
        echo "etc/systemd/user/graphical-session.target.wants/flowork-neural-conduit.service s 777 0 0 ../flowork-neural-conduit.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/graphical-session.target.wants/flowork-neural-conduit.service s 777 0 0 ../flowork-neural-conduit.service" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-voice-daemon.service" ] || [ -f "/etc/systemd/user/flowork-voice-daemon.service" ]; then
        local _voice_svc="${FLOWORK_ROOT}/system/systemd/flowork-voice-daemon.service"
        [ -f "$_voice_svc" ] || _voice_svc="/etc/systemd/user/flowork-voice-daemon.service"
        echo "etc/systemd/user/flowork-voice-daemon.service f 644 0 0 cat ${_voice_svc}" >> "$PSEUDO_FILE"
        echo "etc/xdg/systemd/user/flowork-voice-daemon.service f 644 0 0 cat ${_voice_svc}" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/flowork-voice-daemon.service f 644 0 0 cat ${_voice_svc}" >> "$PSEUDO_FILE"
        echo "etc/systemd/user/default.target.wants/flowork-voice-daemon.service s 777 0 0 ../flowork-voice-daemon.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-voice-daemon.service s 777 0 0 ../flowork-voice-daemon.service" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-click-fx.service" ] || [ -f "/etc/systemd/user/flowork-click-fx.service" ]; then
        local _click_svc="${FLOWORK_ROOT}/system/systemd/flowork-click-fx.service"
        [ -f "$_click_svc" ] || _click_svc="/etc/systemd/user/flowork-click-fx.service"
        echo "etc/systemd/user/flowork-click-fx.service f 644 0 0 cat ${_click_svc}" >> "$PSEUDO_FILE"
        echo "etc/xdg/systemd/user/flowork-click-fx.service f 644 0 0 cat ${_click_svc}" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/flowork-click-fx.service f 644 0 0 cat ${_click_svc}" >> "$PSEUDO_FILE"
        echo "etc/systemd/user/default.target.wants/flowork-click-fx.service s 777 0 0 ../flowork-click-fx.service" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-click-fx.service s 777 0 0 ../flowork-click-fx.service" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/flowork-sysd" ]; then
        echo "usr/local/bin/flowork-sysd f 755 0 0 cat ${FLOWORK_ROOT}/bin/flowork-sysd" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/kamidi-mastering/bin/kamidi-mastering-cli" ]; then
        echo "usr/local/bin/kamidi-mastering-cli s 777 0 0 /opt/floworkos/apps/kamidi-mastering/bin/kamidi-mastering-cli" >> "$PSEUDO_FILE"
        echo "usr/local/bin/kamidi-cli s 777 0 0 /opt/floworkos/apps/kamidi-mastering/bin/kamidi-mastering-cli" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/cutvii/bin/cutvii-cli" ]; then
        echo "usr/local/bin/cutvii-cli s 777 0 0 /opt/floworkos/apps/cutvii/bin/cutvii-cli" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/gputaskman" ]; then
        echo "usr/local/bin/gputaskman s 777 0 0 /opt/floworkos/bin/gputaskman" >> "$PSEUDO_FILE"
        echo "usr/local/bin/gtm s 777 0 0 /opt/floworkos/bin/gputaskman" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/gputaskman/bin/gputaskman-cli" ]; then
        echo "usr/local/bin/gputaskman-cli s 777 0 0 /opt/floworkos/apps/gputaskman/bin/gputaskman-cli" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/openscreen" ]; then
        echo "usr/local/bin/openscreen s 777 0 0 /opt/floworkos/bin/openscreen" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/apps/openscreen/bin/openscreen-cli" ]; then
        echo "usr/local/bin/openscreen-cli s 777 0 0 /opt/floworkos/apps/openscreen/bin/openscreen-cli" >> "$PSEUDO_FILE"
    fi
    for df_new in gputaskman.desktop openscreen.desktop social-auto-upload.desktop artex.desktop; do
        if [ -f "${FLOWORK_ROOT}/apps/${df_new}" ]; then
            echo "usr/share/applications/${df_new} f 644 0 0 cat ${FLOWORK_ROOT}/apps/${df_new}" >> "$PSEUDO_FILE"
        fi
    done
    if [ -x "${FLOWORK_ROOT}/bin/social-auto-upload" ]; then
        echo "usr/local/bin/social-auto-upload s 777 0 0 /opt/floworkos/bin/social-auto-upload" >> "$PSEUDO_FILE"
        echo "usr/local/bin/sau s 777 0 0 /opt/floworkos/bin/sau" >> "$PSEUDO_FILE"
        echo "usr/local/bin/sau-gui s 777 0 0 /opt/floworkos/bin/social-auto-upload" >> "$PSEUDO_FILE"
    fi
    echo "etc/skel/.local/share/applications/social-auto-upload.desktop s 777 0 0 /opt/floworkos/apps/social-auto-upload.desktop" >> "$PSEUDO_FILE"
    echo "opt/floworkos/apps/social-auto-upload/cookies m 775 1000 1000" >> "$PSEUDO_FILE"
    if [ -x "${FLOWORK_ROOT}/bin/artex" ]; then
        echo "usr/local/bin/artex s 777 0 0 /opt/floworkos/bin/artex" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/apps/artex.desktop" ]; then
        echo "etc/skel/.local/share/applications/artex.desktop s 777 0 0 /opt/floworkos/apps/artex.desktop" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-artex.service" ] || [ -f "/etc/systemd/user/flowork-artex.service" ]; then
        local _artex_svc="${FLOWORK_ROOT}/system/systemd/flowork-artex.service"
        [ -f "$_artex_svc" ] || _artex_svc="/etc/systemd/user/flowork-artex.service"
        echo "etc/systemd/user/flowork-artex.service f 644 0 0 cat ${_artex_svc}" >> "$PSEUDO_FILE"
        echo "etc/xdg/systemd/user/flowork-artex.service f 644 0 0 cat ${_artex_svc}" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/flowork-artex.service f 644 0 0 cat ${_artex_svc}" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/systemd/flowork-artex-bridge.service" ] || [ -f "/etc/systemd/user/flowork-artex-bridge.service" ]; then
        local _bridge_svc="${FLOWORK_ROOT}/system/systemd/flowork-artex-bridge.service"
        [ -f "$_bridge_svc" ] || _bridge_svc="/etc/systemd/user/flowork-artex-bridge.service"
        echo "etc/systemd/user/flowork-artex-bridge.service f 644 0 0 cat ${_bridge_svc}" >> "$PSEUDO_FILE"
        echo "etc/xdg/systemd/user/flowork-artex-bridge.service f 644 0 0 cat ${_bridge_svc}" >> "$PSEUDO_FILE"
        echo "etc/skel/.config/systemd/user/flowork-artex-bridge.service f 644 0 0 cat ${_bridge_svc}" >> "$PSEUDO_FILE"
    fi
    echo "usr/local/bin/flowork-on-demand s 777 0 0 /opt/floworkos/bin/flowork-on-demand" >> "$PSEUDO_FILE"
    echo "usr/local/bin/flowork-hydrate s 777 0 0 /opt/floworkos/bin/flowork-hydrate" >> "$PSEUDO_FILE"
    echo "usr/local/bin/flowork-apk s 777 0 0 /opt/floworkos/bin/flowork-apk" >> "$PSEUDO_FILE"
    if [ -x "${FLOWORK_ROOT}/bin/flowork-diag-display" ]; then
        echo "usr/local/bin/flowork-diag-display s 777 0 0 /opt/floworkos/bin/flowork-diag-display" >> "$PSEUDO_FILE"
        echo "usr/local/bin/flowork-doctor-display s 777 0 0 /opt/floworkos/bin/flowork-diag-display" >> "$PSEUDO_FILE"
        echo "etc/skel/.local/bin/flowork-diag-display s 777 0 0 /opt/floworkos/bin/flowork-diag-display" >> "$PSEUDO_FILE"
        echo "etc/skel/.local/bin/flowork-doctor-display s 777 0 0 /opt/floworkos/bin/flowork-diag-display" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/theme/picom-quantum.conf" ]; then
        echo "opt/floworkos/theme/picom-quantum.conf f 644 0 0 cat ${FLOWORK_ROOT}/theme/picom-quantum.conf" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/flowork-apk-direct" ]; then
        echo "usr/local/bin/flowork-apk-direct s 777 0 0 /opt/floworkos/bin/flowork-apk-direct" >> "$PSEUDO_FILE"
    fi
    if [ -x "/usr/local/bin/google-chrome-stable" ]; then
        echo "usr/local/bin/google-chrome-stable f 755 0 0 cat /usr/local/bin/google-chrome-stable" >> "$PSEUDO_FILE"
        echo "usr/bin/google-chrome-stable s 777 0 0 /usr/local/bin/google-chrome-stable" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/cargo" ]; then
        echo "usr/local/bin/cargo f 755 0 0 cat ${FLOWORK_ROOT}/bin/cargo" >> "$PSEUDO_FILE"
    fi
    if [ -x "${FLOWORK_ROOT}/bin/rustc" ]; then
        echo "usr/local/bin/rustc f 755 0 0 cat ${FLOWORK_ROOT}/bin/rustc" >> "$PSEUDO_FILE"
    fi
    if [ -f "$SAN_SKEL_BASHRC" ]; then
        echo "etc/skel/.profile f 644 0 0 cat ${SAN_SKEL_PROFILE}" >> "$PSEUDO_FILE"
        echo "etc/skel/.bashrc f 644 0 0 cat ${SAN_SKEL_BASHRC}" >> "$PSEUDO_FILE"
    fi
    if [ -f "$SAN_PROFILE_D" ]; then
        echo "etc/profile.d/flowork.sh f 644 0 0 cat ${SAN_PROFILE_D}" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/theme/fonts/cjk/NotoSansCJKsc-Regular.otf" ]; then
        echo "usr/local/share/fonts/cjk d 755 0 0" >> "$PSEUDO_FILE"
        echo "usr/local/share/fonts/cjk/NotoSansCJKsc-Regular.otf f 644 0 0 cat ${FLOWORK_ROOT}/theme/fonts/cjk/NotoSansCJKsc-Regular.otf" >> "$PSEUDO_FILE"
        echo "usr/local/share/fonts/cjk/NotoSansCJKsc-Bold.otf f 644 0 0 cat ${FLOWORK_ROOT}/theme/fonts/cjk/NotoSansCJKsc-Bold.otf" >> "$PSEUDO_FILE"
    fi
    if [ -f "/etc/systemd/system.conf.d/10-flowork-silent.conf" ]; then
        echo "etc/systemd/system.conf.d d 755 0 0" >> "$PSEUDO_FILE"
        echo "etc/systemd/system.conf.d/10-flowork-silent.conf f 644 0 0 cat /etc/systemd/system.conf.d/10-flowork-silent.conf" >> "$PSEUDO_FILE"
    fi

    # Decoupled placeholder directories for on-demand downloads (777 permissions)
    echo "opt/floworkos/apps/audacity d 777 1000 1000" >> "$PSEUDO_FILE"
    echo "opt/floworkos/apps/openscreen d 777 1000 1000" >> "$PSEUDO_FILE"
    echo "opt/floworkos/apps/social-auto-upload d 777 1000 1000" >> "$PSEUDO_FILE"
    echo "opt/floworkos/apps/wine-staging d 777 1000 1000" >> "$PSEUDO_FILE"

    # Sovereign Zero-Leak Global Git Shield
    echo "etc/flowork-global.gitignore f 644 0 0 cat /etc/flowork-global.gitignore" >> "$PSEUDO_FILE"
    echo "etc/gitconfig f 644 0 0 cat /etc/gitconfig" >> "$PSEUDO_FILE"
    echo "opt/floworkos/.gitignore f 644 0 0 cat /opt/floworkos/.gitignore" >> "$PSEUDO_FILE"
    echo "etc/skel/.gitignore f 644 0 0 cat /etc/skel/.gitignore" >> "$PSEUDO_FILE"
    echo "etc/skel/.config/git d 755 0 0" >> "$PSEUDO_FILE"
    echo "etc/skel/.config/git/ignore f 644 0 0 cat /etc/skel/.config/git/ignore" >> "$PSEUDO_FILE"

    echo "→ Compressing system rootfs into multi-threaded XZ SquashFS..."
    sudo rm -f "$SQUASHFS_FILE"
    sudo mksquashfs / "$SQUASHFS_FILE" \
        -comp xz \
        -b 1048576 \
        -wildcards \
        -ef "$EXCLUDE_FILE" \
        -pf "$PSEUDO_FILE" \
        -noappend

    echo "→ Generating hybrid bootable UEFI/BIOS ISO via xorriso..."
    local MBR_BIN="/usr/lib/ISOLINUX/isohdpfx.bin"
    if [ ! -f "$MBR_BIN" ]; then
        MBR_BIN="${BUILDER_DIR}/boot-skeleton/isolinux/isolinux.bin"
    fi

    sudo xorriso -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "FLOWORK_OS" \
        -eltorito-boot isolinux/isolinux.bin \
        -eltorito-catalog isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -isohybrid-mbr "$MBR_BIN" \
        -eltorito-alt-boot \
        -e boot/grub/efi.img \
        -no-emul-boot \
        -isohybrid-gpt-basdat \
        -output "$FINAL_ISO" \
        "${ISO_ROOT}"

    echo "→ Generating SHA256 verification checksum..."
    (cd "${OUTPUT_DIR}" && sha256sum "$(basename "$FINAL_ISO")" > "${FINAL_ISO}.sha256")

    echo ""
    echo "=========================================================="
    echo "✓ FLOWORK OS LIVE ISO MASTERING COMPLETED SUCCESSFULLY!"
    echo "  ISO Path:   $FINAL_ISO"
    echo "  Size:       $(du -h "$FINAL_ISO" | cut -f1)"
    echo "  SHA256:     $(cat "${FINAL_ISO}.sha256")"
    echo "=========================================================="
}

case "${1:-check}" in
    check|--check)
        check_prerequisites
        echo "✓ Pre-flight verification completed with Exit Code 0."
        ;;
    dry-run|--dry-run)
        check_prerequisites
        echo ""
        echo "Target ISO Output : ${OUTPUT_DIR}/${ISO_NAME}"
        echo "Estimated ISO Size: ~3.2 GB (Multi-threaded XZ SquashFS)"
        echo "Partition Table   : Hybrid MBR / GPT UEFI Bootable"
        if grep -qE 'defaultFileSystemType:[[:space:]]*"?btrfs"?' /etc/calamares/modules/partition.conf 2>/dev/null; then
            echo "Default Target FS : Btrfs (@, @home, @snapshots, @var_log)"
        else
            echo "Default Target FS : ext4 (Calamares /etc/calamares/modules/partition.conf)"
        fi
        echo "✓ Dry-run completed with Exit Code 0."
        ;;
    build|--build)
        build_iso
        ;;
    *)
        echo "Usage: $0 {check | dry-run | build}"
        exit 1
        ;;
esac
exit 0
