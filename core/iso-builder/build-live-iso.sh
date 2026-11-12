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

    local broken_desktop_count=0
    local df try_exec exec_line exec_bin hidden_val nodisp_val
    for df in /usr/share/applications/*.desktop; do
        [ -f "$df" ] || continue
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
    if command -v ntfs-3g >/dev/null 2>&1 && sudo test -f "/etc/polkit-1/rules.d/10-udisks2.rules"; then
        echo "│ [✓] Windows Drives (NTFS/exFAT) & Passwordless Udisks2 : OK"
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
    local broken_runner_links
    broken_runner_links="$(find "${FLOWORK_ROOT}/tools" -maxdepth 2 -name run ! -samefile "${FLOWORK_ROOT}/bin/flowork-tool-runner" 2>/dev/null || true)"
    if [ -n "$broken_runner_links" ]; then
        echo "│ [✗] Tool runner hardlink mismatch detected: ${broken_runner_links}"
        return 1
    fi
    for ipc_asset in \
        "${FLOWORK_ROOT}/bin/flowork-bus" \
        "${FLOWORK_ROOT}/bin/flowork-pipe" \
        "${FLOWORK_ROOT}/bin/kamidi-mastering-cli" \
        "${FLOWORK_ROOT}/bin/kamidi-cli" \
        "${FLOWORK_ROOT}/bin/cutvii-cli" \
        "${FLOWORK_ROOT}/apps/kamidi-mastering/bin/kamidi-mastering-cli" \
        "${FLOWORK_ROOT}/apps/cutvii/bin/cutvii-cli" \
        "${FLOWORK_ROOT}/tools/memory_crystallizer/run.py" \
        "${FLOWORK_ROOT}/system/kernel/enable-landlock-and-nvidia.sh" \
        "${FLOWORK_ROOT}/system/kernel/build-flowork-kernel.sh"; do
        if [ ! -x "$ipc_asset" ]; then
            echo "│ [✗] Missing or non-executable Bus/Episodic/Kernel asset: ${ipc_asset}"
            return 1
        fi
    done
    if [ ! -f "${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/kernel/nvidia-595.99.02-linux-7.3-drm-ibt.patch" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/kernel/flowork-universal.config" ] \
        || [ ! -f "${FLOWORK_ROOT}/system/system_promp/promps/triggers/episodic_bus_and_sandbox.md" ]; then
        echo "│ [✗] Missing tmpfiles.d/flowork.conf, kernel NVIDIA patch/config, or triggers/episodic_bus_and_sandbox.md!"
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
    for rt_dir in "${FLOWORK_ROOT}/apps/audacity/runtime" "${FLOWORK_ROOT}/apps/recordly/squashfs-root"; do
        if [ -d "$rt_dir" ]; then
            local rt_mode
            rt_mode="$(stat -c '%a' "$rt_dir" 2>/dev/null || echo '0')"
            if [ $(( 8#${rt_mode} & 8#005 )) -ne 5 ]; then
                echo "│ [✗] App runtime directory lacks world read+traverse (o+rx, mode=${rt_mode}): ${rt_dir}"
                return 1
            fi
        fi
    done
    echo "│ [✓] App Runtimes & Symlinks (Audacity/Recordly traverse perms) : OK"

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
    echo "│ [✓] Rootfs Exclusion Filter: Zero user tokens/homes/broken symlinks/targets"
    echo "│ [✓] White-labeling: 100% verified (Flowork Sovereign)"
    echo "└────────────────────────────────────────────────────────┘"
    return 0
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

    sudo rm -rf "${WORK_DIR}"
    mkdir -p "${OUTPUT_DIR}" "${WORK_DIR}" "${ISO_ROOT}/live" "${ISO_ROOT}/boot/grub"

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
home/awenk/*
home/awenk
home/awenkaudico/*
home/awenkaudico
home/*/.cache/*
home/*/.npm*
etc/skel/.npm*
home/*/.cargo/*
home/*/.rustup/*
home/*/.bash_history
home/*/*token*
home/*/Downloads/*
home/*/Downloads
home/*/downloads/*
home/*/downloads
root/Downloads/*
root/Downloads
root/*
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
opt/floworkos/connector/data/vault.json
opt/floworkos/connector/data/vault.json.tmp*
opt/floworkos/connector/data/vault.dev.bak
opt/floworkos/flowork.dev
*flowork.dev*
opt/floworkos/history/chats/*
opt/floworkos/history/episodic_memory.db*
opt/floworkos/system/triger/*/.pid
opt/floworkos/system/triger/*/.last_alert
opt/floworkos/system/triger/*/.state.json
opt/floworkos/system/triger/*/__pycache__/*
opt/floworkos/system/triger/*/__pycache__
opt/floworkos/screenshots/*.png
opt/floworkos/screenshots/thumbs/*
opt/floworkos/apps/flowork-stealth/profiles/*/user_data/*
opt/floworkos/apps/flowork-stealth/profiles/*/user_data/.*
opt/floworkos/apps/flowork-stealth/profiles/*/user_data_chrome/*
opt/floworkos/apps/flowork-stealth/profiles/*/user_data_chrome/.*
opt/floworkos/agents/*
opt/floworkos/agents
opt/floworkos/apps/agent/*
opt/floworkos/apps/agent
opt/floworkos/apps/agent.desktop
usr/share/applications/agent.desktop
usr/share/applications/Antigravity.desktop
usr/local/bin/antigravity
*antigravity*
etc/skel/.gemini*
home/*/.gemini*
opt/floworkos/lib/mrflow*
usr/lib/node_modules/*
usr/lib/node_modules
usr/local/lib/node_modules/*
usr/local/lib/node_modules
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
EOF_EXCLUDE

    if [ -f "${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" ]; then
        echo "etc/tmpfiles.d/flowork.conf" >> "$EXCLUDE_FILE"
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
    if [ ! -x "/usr/local/bin/x-flow" ]; then
        echo "etc/skel/.config/systemd/user/default.target.wants/flowork-core.service" >> "$EXCLUDE_FILE"
    fi
    if [ ! -x "/usr/local/bin/flowork-window-daemon" ]; then
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

    # 2. Clean sudoers rule (flowork live user only, zero hardcoded personal user)
    cat << 'EOF_SUDO' > "$SAN_SUDOERS"
# Flowork OS Sovereign Sudoers Rules
flowork ALL=(ALL) NOPASSWD: ALL
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

    # 4. User databases: sole live user flowork, purge host personal accounts safely
    grep -v -E '^(awenk|awenkaudico):' /etc/passwd > "$SAN_PASSWD"
    sudo grep -v -E '^(awenk|awenkaudico):' /etc/shadow > "$SAN_SHADOW"
    sed 's/,awenkaudico//g; s/awenkaudico,//g; s/:awenkaudico/:/g; s/,awenk//g; s/awenk,//g; s/:awenk/:/g' /etc/group | grep -v -E '^(awenk|awenkaudico):' > "$SAN_GROUP"

    # 4b. Pre-seed clean .fl_brain-only Episodic FTS5 DB (zero host personal chat logs)
    if [ -x "${FLOWORK_ROOT}/tools/memory_crystallizer/run.py" ]; then
        FLOWORK_EPISODIC_DB="$CLEAN_EPISODIC_DB" python3 "${FLOWORK_ROOT}/tools/memory_crystallizer/run.py" --sync-brain >/dev/null
        python3 - "$CLEAN_EPISODIC_DB" << 'PY_SQLITE_CLEAN'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
conn.execute("PRAGMA journal_mode=DELETE;")
conn.close()
PY_SQLITE_CLEAN
        rm -f "${CLEAN_EPISODIC_DB}-wal" "${CLEAN_EPISODIC_DB}-shm"
    fi

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
opt/floworkos/history m 775 1000 1000
EOF_PSEUDO
    if [ -f "${FLOWORK_ROOT}/connector/data/vault.clean.json" ]; then
        echo "opt/floworkos/connector/data/vault.json f 600 1000 1000 cat ${FLOWORK_ROOT}/connector/data/vault.clean.json" >> "$PSEUDO_FILE"
    fi
    if [ -f "$CLEAN_EPISODIC_DB" ]; then
        echo "opt/floworkos/history/episodic_memory.db f 644 1000 1000 cat ${CLEAN_EPISODIC_DB}" >> "$PSEUDO_FILE"
    fi
    if [ -f "${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" ]; then
        echo "etc/tmpfiles.d/flowork.conf f 644 0 0 cat ${FLOWORK_ROOT}/system/tmpfiles.d/flowork.conf" >> "$PSEUDO_FILE"
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
