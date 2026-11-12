#!/usr/bin/env bash
# ==============================================================================
# Flowork Sovereign OS — Kernel Builder (Rust + Landlock + Universal Hardware)
# Builds Debian kernel packages (bindeb-pkg) non-interactively in user-space.
# Usage:
#   KERNEL_SRC_DIR=/path/to/linux-flowork-rust /opt/floworkos/system/kernel/build-flowork-kernel.sh [--config-only]
# ==============================================================================
set -euo pipefail

FLOWORK_ROOT="${FLOWORK_ROOT:-/opt/floworkos}"
BASE_CONFIG="${BASE_CONFIG:-/boot/config-$(uname -r)}"
FRAGMENT="${FRAGMENT:-${FLOWORK_ROOT}/system/kernel/flowork-universal.config}"
KERNEL_SRC_DIR="${KERNEL_SRC_DIR:-${HOME}/kernel-build/linux-flowork-rust}"
JOBS="${JOBS:-$(nproc)}"
CONFIG_ONLY=0

if [[ "${1:-}" == "--config-only" ]]; then
    CONFIG_ONLY=1
fi

export PATH="${HOME}/.cargo/bin:${PATH}"
export KBUILD_BUILD_USER="${KBUILD_BUILD_USER:-flowork}"
export KBUILD_BUILD_HOST="${KBUILD_BUILD_HOST:-sovereign}"
export DEBFULLNAME="${DEBFULLNAME:-Flowork OS Architect}"
export DEBEMAIL="${DEBEMAIL:-architect@flowork.ai}"

if [[ ! -d "${KERNEL_SRC_DIR}" || ! -f "${KERNEL_SRC_DIR}/Makefile" ]]; then
    echo "ERROR: Kernel source directory not found: ${KERNEL_SRC_DIR}" >&2
    exit 1
fi
if [[ ! -f "${BASE_CONFIG}" ]]; then
    echo "ERROR: Base kernel config not found: ${BASE_CONFIG}" >&2
    exit 1
fi
if [[ ! -f "${FRAGMENT}" ]]; then
    echo "ERROR: Config fragment not found: ${FRAGMENT}" >&2
    exit 1
fi

cd "${KERNEL_SRC_DIR}"

echo "[Kernel] Verifying Rust-for-Linux toolchain..."
make rustavailable

echo "[Kernel] Merging base config (${BASE_CONFIG}) + ${FRAGMENT}..."
cp -f "${BASE_CONFIG}" .config
./scripts/kconfig/merge_config.sh -m .config "${FRAGMENT}"
make olddefconfig

echo "[Kernel] Auditing mandatory Sovereign & Intel/AMD flags..."
required_checks=(
    "CONFIG_RUST=y"
    "CONFIG_SECURITYFS=y"
    "CONFIG_SECURITY_LANDLOCK=y"
    "CONFIG_USER_NS=y"
    "CONFIG_FUSE_FS=y"
    "CONFIG_BTRFS_FS=y"
    "CONFIG_INPUT_UINPUT=y"
    "CONFIG_PSI=y"
    "CONFIG_DRM_I915=y"
    "CONFIG_DRM_XE=m"
    "CONFIG_DRM_AMDGPU=m"
    "CONFIG_DRM_NOUVEAU=m"
    "CONFIG_IWLWIFI=m"
    "CONFIG_I2C_HID_ACPI=m"
    "CONFIG_HID_MULTITOUCH=m"
    "CONFIG_VMD=y"
    "CONFIG_SND_SOC_SOF_PCI=m"
    "CONFIG_BT_HCIBTUSB=m"
)
missing=0
for sym in "${required_checks[@]}"; do
    if ! grep -qxF "${sym}" .config; then
        echo "[FAIL] Missing expected config line: ${sym}" >&2
        missing=$((missing + 1))
    fi
done
if [[ "${missing}" -ne 0 ]]; then
    exit 1
fi

KREL="$(make -s kernelrelease)"
echo "[OK] Kernel configuration verified. Target kernelrelease: ${KREL}"

if [[ "${CONFIG_ONLY}" -eq 1 ]]; then
    exit 0
fi

echo "[Build] Compiling Linux Debian packages with -j${JOBS} (output goes to parent of ${KERNEL_SRC_DIR})..."
make -j"${JOBS}" bindeb-pkg KDEB_PKGVERSION="${FLOWORK_KDEB_VER:-7.3.0-gd89e1d186ec9-8}"
echo "[OK] Kernel .deb packages generated in $(dirname "${KERNEL_SRC_DIR}")"
ls -lh "$(dirname "${KERNEL_SRC_DIR}")"/*.deb
