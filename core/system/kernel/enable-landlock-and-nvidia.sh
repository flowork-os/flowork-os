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

RUNNING_KVER="$(uname -r)"
KVER="${TARGET_KVER:-${RUNNING_KVER}}"
echo "[Flowork Root Provisioning] Target Kernel: ${KVER} (Running: ${RUNNING_KVER})"

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

# 3. Build/install NVIDIA DKMS driver for target kernel if any module is missing
if modinfo -k "${KVER}" nvidia >/dev/null 2>&1 \
    && modinfo -k "${KVER}" nvidia-modeset >/dev/null 2>&1 \
    && modinfo -k "${KVER}" nvidia-drm >/dev/null 2>&1 \
    && modinfo -k "${KVER}" nvidia-uvm >/dev/null 2>&1; then
    echo "[OK] NVIDIA kernel modules already built for ${KVER}"
    if [[ "${KVER}" == "${RUNNING_KVER}" ]]; then
        for mod in nvidia nvidia-modeset nvidia-drm nvidia-uvm; do
            modprobe "${mod}" >/dev/null 2>&1 || true
        done
        if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
            echo "[OK] NVIDIA GPU driver loaded and verified via nvidia-smi!"
        fi
    fi
elif [[ -d /usr/src/nvidia-595.99.02 ]] && command -v dkms >/dev/null 2>&1; then
    NV_SRC="/usr/src/nvidia-595.99.02"
    NV_PATCH="/opt/floworkos/system/kernel/nvidia-595.99.02-linux-7.3-drm-ibt.patch"
    NV_FBDEV_PATCH="/opt/floworkos/system/kernel/nvidia-595.99.02-linux-7.3-fbdev-helper.patch"
    if [[ -f "${NV_PATCH}" ]]; then
        if ! command -v patch >/dev/null 2>&1; then
            echo "[ERROR] 'patch' utility is required to apply ${NV_PATCH}" >&2
            exit 1
        fi
        if grep -qF 'drm_plane_funcs_has_atomic_create_state' "${NV_SRC}/conftest.sh" \
            && grep -qF 'drm_crtc_funcs_has_atomic_create_state' "${NV_SRC}/nvidia-drm/nvidia-drm-sources.mk" \
            && grep -qF 'nv_drm_atomic_crtc_create_state' "${NV_SRC}/nvidia-drm/nvidia-drm-crtc.c" \
            && ! grep -qF 'CONFIG_X86_KERNEL_IBT=' "${NV_SRC}/dkms.conf"; then
            echo "[OK] NVIDIA Linux 7.3 DRM/IBT compatibility patch already applied to ${NV_SRC}"
        elif patch -d "${NV_SRC}" -p1 -N --batch --dry-run < "${NV_PATCH}" >/dev/null 2>&1; then
            echo "[Patch] Applying Linux 7.3 DRM/IBT compatibility patch to ${NV_SRC}..."
            patch -d "${NV_SRC}" -p1 -N --batch --no-backup-if-mismatch < "${NV_PATCH}"
            echo "[OK] Patched ${NV_SRC} cleanly"
        else
            echo "[ERROR] Compatibility patch ${NV_PATCH} could not be applied cleanly to ${NV_SRC}" >&2
            exit 1
        fi
    fi
    if [[ -f "${NV_FBDEV_PATCH}" ]]; then
        if grep -qF 'drm/clients/drm_fbdev_helper.h' "${NV_SRC}/header-presence-tests.mk" \
            && grep -qF 'NV_DRM_CLIENTS_DRM_FBDEV_HELPER_H_PRESENT' "${NV_SRC}/conftest.sh" \
            && grep -qF 'NV_DRM_CLIENTS_DRM_FBDEV_HELPER_H_PRESENT' "${NV_SRC}/nvidia-drm/nvidia-drm-drv.c"; then
            echo "[OK] NVIDIA Linux 7.3 fbdev-helper compatibility patch already applied to ${NV_SRC}"
        elif patch -d "${NV_SRC}" -p1 -N --batch --dry-run < "${NV_FBDEV_PATCH}" >/dev/null 2>&1; then
            echo "[Patch] Applying Linux 7.3 fbdev-helper compatibility patch to ${NV_SRC}..."
            patch -d "${NV_SRC}" -p1 -N --batch --no-backup-if-mismatch < "${NV_FBDEV_PATCH}"
            echo "[OK] Patched ${NV_SRC} fbdev-helper cleanly"
        else
            echo "[ERROR] Compatibility patch ${NV_FBDEV_PATCH} could not be applied cleanly to ${NV_SRC}" >&2
            exit 1
        fi
    fi

    echo "[Build] Installing NVIDIA 595.99.02 DKMS modules for ${KVER}..."
    rm -rf /var/lib/dkms/nvidia/595.99.02/build
    dkms add -m nvidia -v 595.99.02 >/dev/null 2>&1 || true
    dkms install -m nvidia -v 595.99.02 -k "${KVER}" --force
    depmod -a "${KVER}"
    if [[ "${KVER}" == "${RUNNING_KVER}" ]]; then
        for mod in nvidia nvidia-modeset nvidia-drm nvidia-uvm; do
            modprobe "${mod}" || true
        done
        if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
            echo "[OK] NVIDIA GPU driver loaded and verified via nvidia-smi!"
        else
            echo "[OK] NVIDIA DKMS modules built & installed for ${KVER} (reboot or restart display manager if DRM modeset was already bound to simpledrm)"
        fi
    else
        echo "[OK] NVIDIA DKMS modules built & installed for ${KVER} (reboot into ${KVER} to activate)"
    fi
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
    echo "Clone/locate full Linux 7.3.0-flowork-rust kernel source tree (headers-only /usr/src/linux-headers-* is insufficient) and enable:"
    echo "  scripts/config --enable CONFIG_SECURITYFS"
    echo "  scripts/config --enable CONFIG_SECURITY_LANDLOCK"
    echo "  scripts/config --set-str CONFIG_LSM \"lockdown,yama,loadpin,safesetid,integrity,selinux,smack,tomoyo,apparmor,ipe,landlock\""
    echo "Then rebuild kernel image, modules, and reinstall GRUB entry, followed by reboot."
    if [[ -n "${KERNEL_SRC_DIR:-}" && -d "${KERNEL_SRC_DIR}/security/landlock" && -x "${KERNEL_SRC_DIR}/scripts/config" ]]; then
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
