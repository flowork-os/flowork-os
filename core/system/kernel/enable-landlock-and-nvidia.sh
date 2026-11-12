#!/usr/bin/env bash
# ==============================================================================
# Flowork Sovereign OS — Root Kernel & System Provisioning Helper
# Provisions:
#   1. /etc/tmpfiles.d/flowork.conf -> creates /run/flowork (0777) for /run/flowork/bus.sock
#   2. Staged /opt/floworkos/bin/flowork-sysd -> /usr/local/bin/flowork-sysd (if present)
#   3. NVIDIA 595.99.02 DKMS module for the running kernel (/usr/src/nvidia-595.99.02)
#   4. Kernel Landlock LSM + SecurityFS config check & interactive rebuild guidance
#      (CONFIG_SECURITY_LANDLOCK=y, CONFIG_SECURITYFS=y, CONFIG_LSM="...,landlock")
# Idempotent; requires root (sudo).
# ==============================================================================
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "ERROR: Please run as root (e.g., sudo $0)" >&2
    exit 1
fi

KVER="$(uname -r)"
echo "[Flowork Root Provisioning] Kernel: ${KVER}"

# 1. Install systemd-tmpfiles rule for /run/flowork/bus.sock
install -d -m 0755 /etc/tmpfiles.d
install -m 0644 /opt/floworkos/system/tmpfiles.d/flowork.conf /etc/tmpfiles.d/flowork.conf
systemd-tmpfiles --create /etc/tmpfiles.d/flowork.conf
install -d -m 0777 /run/flowork
echo "[OK] /run/flowork provisioned via /etc/tmpfiles.d/flowork.conf"

# 2. Deploy staged flowork-sysd (/dev/shm zero-copy DRM export) if compiled
if [[ -x /opt/floworkos/bin/flowork-sysd ]]; then
    install -m 0755 /opt/floworkos/bin/flowork-sysd /usr/local/bin/flowork-sysd
    echo "[OK] Installed /usr/local/bin/flowork-sysd"
elif [[ -x /opt/floworkos/sysd/target/release/flowork-sysd ]]; then
    install -m 0755 /opt/floworkos/sysd/target/release/flowork-sysd /usr/local/bin/flowork-sysd
    echo "[OK] Installed /usr/local/bin/flowork-sysd from sysd/target/release/flowork-sysd"
else
    echo "[INFO] No newly built flowork-sysd binary staged; keeping existing /usr/local/bin/flowork-sysd"
fi

# 2b. Expose headless studio CLIs in /usr/local/bin and prune dead legacy skel wants
ln -sf /opt/floworkos/apps/kamidi-mastering/bin/kamidi-mastering-cli /usr/local/bin/kamidi-mastering-cli
ln -sf /opt/floworkos/apps/kamidi-mastering/bin/kamidi-mastering-cli /usr/local/bin/kamidi-cli
ln -sf /opt/floworkos/apps/cutvii/bin/cutvii-cli /usr/local/bin/cutvii-cli
if [[ ! -x /usr/local/bin/x-flow ]]; then
    rm -f /etc/skel/.config/systemd/user/default.target.wants/flowork-core.service 2>/dev/null || true
fi
if [[ ! -x /usr/local/bin/flowork-window-daemon ]]; then
    rm -f /etc/skel/.config/systemd/user/default.target.wants/flowork-window-manager.service 2>/dev/null || true
fi
echo "[OK] Headless CLI symlinks installed in /usr/local/bin"

# 3. Build/install NVIDIA DKMS driver for running kernel if module missing
if modinfo nvidia >/dev/null 2>&1; then
    echo "[OK] NVIDIA kernel module already built for ${KVER}"
elif [[ -d /usr/src/nvidia-595.99.02 ]] && command -v dkms >/dev/null 2>&1; then
    echo "[Build] Installing NVIDIA 595.99.02 DKMS module for ${KVER}..."
    dkms install -m nvidia -v 595.99.02 -k "${KVER}" || dkms autoinstall -k "${KVER}"
    depmod -a "${KVER}"
    modprobe nvidia || true
    echo "[OK] NVIDIA DKMS provisioning attempted (verify with: nvidia-smi)"
else
    echo "[WARN] /usr/src/nvidia-595.99.02 or dkms not found; skipping NVIDIA module build"
fi

# 4. Inspect Landlock kernel support and guide/enable kernel configuration
KCFG="/boot/config-${KVER}"
if [[ -f "${KCFG}" ]]; then
    echo "[Check] Inspecting ${KCFG} for Landlock & SecurityFS..."
    grep -E 'CONFIG_SECURITY_LANDLOCK|CONFIG_SECURITYFS|CONFIG_LSM=' "${KCFG}" || true
fi

if [[ -d /sys/kernel/security/landlock ]] || grep -q "landlock" /sys/kernel/security/lsm 2>/dev/null; then
    echo "[OK] Landlock LSM is ACTIVE in running kernel."
else
    echo "[ACTION REQUIRED] Landlock LSM is NOT enabled in kernel ${KVER}."
    echo "Locate your kernel source tree and enable:"
    echo "  scripts/config --enable CONFIG_SECURITYFS"
    echo "  scripts/config --enable CONFIG_SECURITY_LANDLOCK"
    echo "  scripts/config --set-str CONFIG_LSM \"lockdown,yama,loadpin,safesetid,integrity,selinux,smack,tomoyo,apparmor,ipe,landlock\""
    echo "Then rebuild kernel image, modules, and reinstall GRUB entry, followed by reboot."
    if [[ -n "${KERNEL_SRC_DIR:-}" && -d "${KERNEL_SRC_DIR}" && -x "${KERNEL_SRC_DIR}/scripts/config" ]]; then
        echo "[Auto] Applying Landlock config flags inside KERNEL_SRC_DIR=${KERNEL_SRC_DIR}..."
        (
            cd "${KERNEL_SRC_DIR}"
            ./scripts/config --enable CONFIG_SECURITYFS
            ./scripts/config --enable CONFIG_SECURITY_LANDLOCK
            make olddefconfig
            echo "[OK] Updated ${KERNEL_SRC_DIR}/.config — run 'make -j\$(nproc) bzImage modules && make modules_install && make install' to finalize."
        )
    fi
fi

echo "[Flowork Root Provisioning] Complete. Restart user daemons as user:"
echo "  systemctl --user restart flowork-neural-bus flowork-sysd"
