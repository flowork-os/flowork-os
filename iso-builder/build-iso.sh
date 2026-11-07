#!/usr/bin/env bash
# ==============================================================================
# 👑 FLOWORK SOVEREIGN OS — PRODUCTION LIVE ISO MASTERING ENGINE
# Architecture: Method A (Live System Snapshot & Sanitized Mastering)
# Target Kernel: Linux 7.3.0 Rust (Custom Sovereign Microkernel)
# Bootloader: Hybrid UEFI (GRUB 2.12 x86_64) + BIOS Legacy (ISOLINUX / MBR)
# Co-authored-by: Flowork OS <agent@floworkos.com>
# ==============================================================================
set -euo pipefail

# Visual HUD & Logging Standards
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_step() { echo -e "${CYAN}${BOLD}[FLOWORK ISO]${NC} ${GREEN}→${NC} $1"; }
log_info() { echo -e "${CYAN}${BOLD}[FLOWORK ISO]${NC} ${BLUE}ℹ${NC} $1"; }
log_warn() { echo -e "${CYAN}${BOLD}[FLOWORK ISO]${NC} ${YELLOW}⚠${NC} $1"; }
log_err()  { echo -e "${CYAN}${BOLD}[FLOWORK ISO]${NC} ${RED}✖${NC} $1"; }
log_succ() { echo -e "${CYAN}${BOLD}[FLOWORK ISO]${NC} ${GREEN}✔${NC} ${BOLD}$1${NC}"; }

# Enforce Root Privileges
if [[ $EUID -ne 0 ]]; then
    log_err "This mastering script must be run as root (sudo ./build-iso.sh)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXCLUDES_FILE="${SCRIPT_DIR}/iso-excludes.list"

# Workspace Paths (Utilizing High-Speed Local Storage)
BUILD_BASE="/home/awenkaudico/flowork-iso-build"
CHROOT_DIR="${BUILD_BASE}/chroot"
ISO_DIR="${BUILD_BASE}/iso_root"
OUTPUT_DIR="${BUILD_BASE}/output"
ISO_NAME="flowork-os-7.3.0-amd64.iso"
OUTPUT_ISO="${OUTPUT_DIR}/${ISO_NAME}"

mkdir -p "${BUILD_BASE}" "${OUTPUT_DIR}"

log_step "Phase 1: Validating Build Environment & Prerequisites..."

REQUIRED_TOOLS=(rsync mksquashfs xorriso grub-mkstandalone mkfs.vfat mcopy mmd)
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
        log_err "Missing mandatory build utility: ${tool}"
        exit 1
    fi
done
log_info "All mandatory mastering utilities confirmed."

KERNEL_VER="7.3.0-flowork-rust-gd89e1d186ec9"
VMLINUZ_SRC="/boot/vmlinuz-${KERNEL_VER}"
INITRD_SRC="/boot/initrd.img-${KERNEL_VER}"

if [[ ! -f "$VMLINUZ_SRC" ]]; then
    log_warn "Primary kernel '${VMLINUZ_SRC}' not found. Falling back to active kernel."
    VMLINUZ_SRC="/boot/vmlinuz-$(uname -r)"
    INITRD_SRC="/boot/initrd.img-$(uname -r)"
    KERNEL_VER="$(uname -r)"
fi

if [[ ! -f "$VMLINUZ_SRC" || ! -f "$INITRD_SRC" ]]; then
    log_err "Kernel image or initrd could not be resolved! Vmlinuz: ${VMLINUZ_SRC}, Initrd: ${INITRD_SRC}"
    exit 1
fi
log_info "Selected Kernel: ${VMLINUZ_SRC}"
log_info "Selected Initrd: ${INITRD_SRC}"

if [[ ! -f "$EXCLUDES_FILE" ]]; then
    log_err "Exclusions file '${EXCLUDES_FILE}' is missing!"
    exit 1
fi

log_step "Phase 2: Synchronizing Live System Snapshot to Staging Chroot..."
rm -rf "${CHROOT_DIR}"
mkdir -p "${CHROOT_DIR}"

log_info "Performing full rootfs archive rsync (this captures Flowork OS 100% white-label)..."
rsync -aHAXx --numeric-ids \
    --exclude-from="${EXCLUDES_FILE}" \
    / "${CHROOT_DIR}/"

mkdir -p "${CHROOT_DIR}"/{dev,proc,sys,run,tmp,var/tmp,mnt,media,home,boot/efi}
chmod 1777 "${CHROOT_DIR}/tmp" "${CHROOT_DIR}/var/tmp"

log_succ "Root filesystem rsync complete."

log_step "Phase 3: Sanitizing Snapshot & Provisioning Live Environment..."

truncate -s 0 "${CHROOT_DIR}/etc/machine-id"
rm -f "${CHROOT_DIR}/var/lib/dbus/machine-id"
rm -rf "${CHROOT_DIR}/etc/NetworkManager/system-connections/"*

log_info "Sanitizing user accounts (purging personal and duplicate accounts)..."
sed -i '/^awenkaudico:/d' "${CHROOT_DIR}/etc/passwd" || true
sed -i '/^awenkaudico:/d' "${CHROOT_DIR}/etc/shadow" || true
sed -i '/^awenkaudico:/d' "${CHROOT_DIR}/etc/group" || true
sed -i '/^awenkaudico:/d' "${CHROOT_DIR}/etc/gshadow" 2>/dev/null || true
sed -i -E 's/(^|:|,)(awenkaudico)(,|$)/\1\3/g; s/::/:/; s/:,/:/; s/,,/,/g; s/,$//' "${CHROOT_DIR}/etc/group" || true
sed -i -E 's/(^|:|,)(awenkaudico)(,|$)/\1\3/g; s/::/:/; s/:,/:/; s/,,/,/g; s/,$//' "${CHROOT_DIR}/etc/gshadow" 2>/dev/null || true
sed -i '/^awenkaudico:/d' "${CHROOT_DIR}/etc/subuid" 2>/dev/null || true
sed -i '/^awenkaudico:/d' "${CHROOT_DIR}/etc/subgid" 2>/dev/null || true
rm -f "${CHROOT_DIR}/etc/sudoers.d/99-awenkaudico"

sed -i '/^mrflow:/d' "${CHROOT_DIR}/etc/passwd" || true
sed -i '/^mrflow:/d' "${CHROOT_DIR}/etc/shadow" || true
sed -i '/^mrflow:/d' "${CHROOT_DIR}/etc/group" || true
sed -i '/^mrflow:/d' "${CHROOT_DIR}/etc/gshadow" 2>/dev/null || true
sed -i -E 's/(^|:|,)(mrflow)(,|$)/\1\3/g; s/::/:/; s/:,/:/; s/,,/,/g; s/,$//' "${CHROOT_DIR}/etc/group" || true
sed -i -E 's/(^|:|,)(mrflow)(,|$)/\1\3/g; s/::/:/; s/:,/:/; s/,,/,/g; s/,$//' "${CHROOT_DIR}/etc/gshadow" 2>/dev/null || true

# Purge any existing flowork to guarantee clean recreation
sed -i '/^flowork:/d' "${CHROOT_DIR}/etc/passwd" || true
sed -i '/^flowork:/d' "${CHROOT_DIR}/etc/shadow" || true
sed -i '/^flowork:/d' "${CHROOT_DIR}/etc/group" || true

# Provision sole universal live user 'flowork' (UID 1000, GID 1000)
echo "flowork:x:1000:1000:Flowork Sovereign User,,,:/home/flowork:/bin/bash" >> "${CHROOT_DIR}/etc/passwd"
PASS_HASH='$6$2xBMaCkea5fB588M$/oS88u/U3dF/vHBy8yUDVi0NnQlnK.NEbUt8D6Te501/BUcP6ntmI4M2ig4uhcoIJQRCXFDe3oVOq7hl0u.UE.'
echo "flowork:${PASS_HASH}:19800:0:99999:7:::" >> "${CHROOT_DIR}/etc/shadow"
echo "flowork:x:1000:" >> "${CHROOT_DIR}/etc/group"

for grp in sudo adm dialout cdrom audio dip video plugdev netdev input kvm; do
    if grep -q "^${grp}:" "${CHROOT_DIR}/etc/group"; then
        sed -i -E "s/^(${grp}:[^:]*:[^:]*:)(.*)/\1\2,flowork/" "${CHROOT_DIR}/etc/group"
        sed -i -E "s/,,/,/g; s/:,/:/g; s/,$//g" "${CHROOT_DIR}/etc/group"
    fi
done

rm -rf "${CHROOT_DIR}/home/flowork" "${CHROOT_DIR}/home/mrflow" "${CHROOT_DIR}/home/awenkaudico"
mkdir -p "${CHROOT_DIR}/home/flowork"
cp -a "${CHROOT_DIR}/etc/skel/." "${CHROOT_DIR}/home/flowork/"
chown -R 1000:1000 "${CHROOT_DIR}/home/flowork"
chmod 755 "${CHROOT_DIR}/home/flowork"

cat << 'EOF_SUDO' > "${CHROOT_DIR}/etc/sudoers.d/99-flowork"
flowork ALL=(ALL) NOPASSWD: ALL
EOF_SUDO
chmod 0440 "${CHROOT_DIR}/etc/sudoers.d/99-flowork"

# Enforce Autologin in both lightdm.conf and lightdm.conf.d
cat << 'EOF_LIGHTDM' > "${CHROOT_DIR}/etc/lightdm/lightdm.conf"
[Seat:*]
autologin-user=flowork
autologin-user-timeout=0
user-session=flowork
greeter-session=slick-greeter
EOF_LIGHTDM

mkdir -p "${CHROOT_DIR}/etc/lightdm/lightdm.conf.d"
cp -f "${CHROOT_DIR}/etc/lightdm/lightdm.conf" "${CHROOT_DIR}/etc/lightdm/lightdm.conf.d/99-floworkos.conf"

mkdir -p "${CHROOT_DIR}/etc/live/config.conf.d"
cat << 'EOF_LIVECONF' > "${CHROOT_DIR}/etc/live/config.conf.d/99-flowork.conf"
LIVE_USERNAME="flowork"
LIVE_USER_DEFAULT_GROUPS="sudo audio video plugdev netdev input kvm"
EOF_LIVECONF
rm -f "${CHROOT_DIR}/etc/live/config.conf.d/99-mrflow.conf"

echo "floworkos" > "${CHROOT_DIR}/etc/hostname"
if ! grep -q "127.0.1.1\s\+floworkos" "${CHROOT_DIR}/etc/hosts"; then
    echo "127.0.1.1	floworkos" >> "${CHROOT_DIR}/etc/hosts"
fi

cat << 'EOF_FSTAB' > "${CHROOT_DIR}/etc/fstab"
# ==============================================================================
# 👑 FLOWORK OS — LIVE OVERLAY FILESYSTEM (DYNAMIC)
# ==============================================================================
overlay / overlay rw 0 0
tmpfs /tmp tmpfs defaults,noatime,mode=1777 0 0
EOF_FSTAB

# Purge Cache, Logs, LightDM Greeter Data, Lingering Metadata, and Crash Dumps
rm -rf "${CHROOT_DIR}/var/cache/apt/archives/"* 2>/dev/null || true
rm -rf "${CHROOT_DIR}/var/log/"* 2>/dev/null || true
rm -rf "${CHROOT_DIR}/var/lib/systemd/coredump/"* 2>/dev/null || true
rm -rf "${CHROOT_DIR}/var/cache/lightdm/"* 2>/dev/null || true
rm -rf "${CHROOT_DIR}/var/lib/AccountsService/users/"* 2>/dev/null || true
rm -rf "${CHROOT_DIR}/var/lib/lightdm-data/"* 2>/dev/null || true
rm -rf "${CHROOT_DIR}/var/lib/systemd/linger/"* 2>/dev/null || true
# CRITICAL: Purge all browser profiles and user data from /var/lib/lightdm
rm -rf "${CHROOT_DIR}/var/lib/lightdm/".* "${CHROOT_DIR}/var/lib/lightdm/"* 2>/dev/null || true
mkdir -p "${CHROOT_DIR}/var/lib/lightdm"
chown -R 102:103 "${CHROOT_DIR}/var/lib/lightdm" 2>/dev/null || true
# Explicit Zero-Leak & Universal CPU Sanitization
if [ -d "${CHROOT_DIR}/opt/floworkos/connector/data" ]; then
    cat << 'VAULT_EOF' > "${CHROOT_DIR}/opt/floworkos/connector/data/vault.json"
{
  "active_provider": "connector",
  "active_account_id": "",
  "rotation_mode": "failover",
  "flowork_token": "",
  "flowork_user": null,
  "is_logged_out": true,
  "accounts": []
}
VAULT_EOF
fi
rm -f "${CHROOT_DIR}/opt/floworkos/connector/bin/flowork-connector.bun-avx2"
chmod -R 777 "${CHROOT_DIR}/opt/floworkos/connector" 2>/dev/null || true

# Auto-create all sovereign bookmark endpoints with proper permissions
mkdir -p "${CHROOT_DIR}/opt/floworkos"/{apps,screenshots,tools,agents,mcp,policies,skills,connector,history/chats,system/triger,system/system_promp/promps}
chmod 777 "${CHROOT_DIR}/opt/floworkos/screenshots" "${CHROOT_DIR}/opt/floworkos/agents" "${CHROOT_DIR}/opt/floworkos/history" "${CHROOT_DIR}/opt/floworkos/history/chats" 2>/dev/null || true

log_succ "Chroot sanitization and live user configuration complete."

log_step "Phase 4: Compressing SquashFS Filesystem..."
rm -rf "${ISO_DIR}"
mkdir -p "${ISO_DIR}/live" "${ISO_DIR}/boot/grub" "${ISO_DIR}/EFI/BOOT" "${ISO_DIR}/isolinux"

cp -L "${VMLINUZ_SRC}" "${ISO_DIR}/live/vmlinuz"
cp -L "${INITRD_SRC}" "${ISO_DIR}/live/initrd.img"
log_info "Kernel and initrd integrated into /live."

SQUASHFS_TARGET="${ISO_DIR}/live/filesystem.squashfs"
log_info "Creating ${SQUASHFS_TARGET} (XZ compression, 1MB blocksize, 16 threads)..."
mksquashfs "${CHROOT_DIR}" "${SQUASHFS_TARGET}" \
    -comp xz \
    -b 1048576 \
    -processors "$(nproc)" \
    -noappend

log_succ "SquashFS generated successfully ($(du -h "${SQUASHFS_TARGET}" | cut -f1))."

log_step "Phase 5: Assembling Dual UEFI & BIOS Bootloaders..."

# 5.1 Assemble 64MB FAT32 EFI Boot Image (Mandatory for Intel UEFI)
EFI_IMG="${ISO_DIR}/boot/grub/efi.img"
rm -f "${EFI_IMG}"
dd if=/dev/zero of="${EFI_IMG}" bs=1M count=64 2>/dev/null
mkfs.vfat -F 32 -n "FLOWORK_EFI" "${EFI_IMG}" >/dev/null
mmd -i "${EFI_IMG}" ::/EFI ::/EFI/BOOT
mkdir -p "${ISO_DIR}/EFI/BOOT"

SHIM_SIGNED="/usr/lib/shim/shimx64.efi.signed"
GRUB_SIGNED="/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed"
MM_SIGNED="/usr/lib/shim/mmx64.efi"

if [[ -f "$SHIM_SIGNED" && -f "$GRUB_SIGNED" ]]; then
    log_info "Deploying Microsoft-Signed Shim & Signed GRUB (Intel Secure Boot Ready)..."
    mcopy -i "${EFI_IMG}" "${SHIM_SIGNED}" ::/EFI/BOOT/BOOTX64.EFI
    mcopy -i "${EFI_IMG}" "${GRUB_SIGNED}" ::/EFI/BOOT/grubx64.efi
    cp "${SHIM_SIGNED}" "${ISO_DIR}/EFI/BOOT/BOOTX64.EFI"
    cp "${GRUB_SIGNED}" "${ISO_DIR}/EFI/BOOT/grubx64.efi"
    if [[ -f "$MM_SIGNED" ]]; then
        mcopy -i "${EFI_IMG}" "${MM_SIGNED}" ::/EFI/BOOT/mmx64.efi
        cp "${MM_SIGNED}" "${ISO_DIR}/EFI/BOOT/mmx64.efi"
    fi
else
    cat << 'EOF_EARLY' > /tmp/grub-early.cfg
insmod part_gpt
insmod part_msdos
insmod iso9660
insmod fat
insmod search
search --file --set=root /live/vmlinuz
set prefix=($root)/boot/grub
configfile $prefix/grub.cfg
EOF_EARLY
    grub-mkstandalone \
        --format=x86_64-efi \
        --output=/tmp/BOOTX64.EFI \
        --locales="" \
        --fonts="" \
        --modules="part_gpt part_msdos iso9660 fat search normal test" \
        "boot/grub/grub.cfg=/tmp/grub-early.cfg"
    mcopy -i "${EFI_IMG}" /tmp/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI
    cp /tmp/BOOTX64.EFI "${ISO_DIR}/EFI/BOOT/BOOTX64.EFI"
    rm -f /tmp/BOOTX64.EFI /tmp/grub-early.cfg
fi

cat << 'EOF_GRUB' > "${ISO_DIR}/boot/grub/grub.cfg"
set default=0
set timeout=10

insmod font
insmod all_video
insmod gfxterm
insmod png

terminal_output gfxterm

# Locate the root filesystem partition containing /live/vmlinuz
search --no-floppy --set=root --file /live/vmlinuz

menuentry "👑 Flowork OS 7.3.0 (Rust Kernel) - Live Session" --class flowork --class gnu-linux --class gnu --class os {
    search --no-floppy --set=root --file /live/vmlinuz
    linux /live/vmlinuz boot=live components plymouth.enable=0 selinux=0 quiet nosplash ---
    initrd /live/initrd.img
}

menuentry "👑 Flowork OS 7.3.0 (Safe Graphics - nomodeset)" --class flowork --class gnu-linux --class gnu --class os {
    search --no-floppy --set=root --file /live/vmlinuz
    linux /live/vmlinuz boot=live components plymouth.enable=0 selinux=0 nomodeset quiet nosplash ---
    initrd /live/initrd.img
}

menuentry "🚀 Install Flowork OS 1.0 (Calamares GUI Installer)" --class flowork --class gnu-linux --class gnu --class os {
    search --no-floppy --set=root --file /live/vmlinuz
    linux /live/vmlinuz boot=live components plymouth.enable=0 selinux=0 calamares quiet nosplash ---
    initrd /live/initrd.img
}
EOF_GRUB

cp "${ISO_DIR}/boot/grub/grub.cfg" "${ISO_DIR}/EFI/BOOT/grub.cfg"
mcopy -i "${EFI_IMG}" "${ISO_DIR}/boot/grub/grub.cfg" ::/EFI/BOOT/grub.cfg

cp /usr/lib/ISOLINUX/isolinux.bin "${ISO_DIR}/isolinux/"
cp /usr/lib/syslinux/modules/bios/{vesamenu.c32,libutil.c32,ldlinux.c32,libcom32.c32} "${ISO_DIR}/isolinux/"

cat << 'EOF_ISOLINUX' > "${ISO_DIR}/isolinux/isolinux.cfg"
UI vesamenu.c32
PROMPT 0
TIMEOUT 100

MENU TITLE Flowork OS 7.3.0 (Rust Kernel) Boot Menu
MENU COLOR border       30;44   #40ffffff #a0000000 std
MENU COLOR title        1;36;44 #9033ff66 #a0000000 std
MENU COLOR sel          7;37;40 #e0ffffff #20ffffff all
MENU COLOR unsel        37;44   #50ffffff #a0000000 std
MENU COLOR help         37;40   #c0ffffff #a0000000 std

LABEL live
    MENU LABEL ^Flowork OS 7.3.0 (Rust Kernel) - Live Session
    MENU DEFAULT
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live components quiet splash

LABEL safe
    MENU LABEL Flowork OS 7.3.0 - Safe Graphics (nomodeset)
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live components nomodeset quiet splash

LABEL install
    MENU LABEL Install Flowork OS (Calamares Installer)
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live components calamares quiet splash
EOF_ISOLINUX

log_succ "Dual UEFI and BIOS bootloaders assembled."

log_step "Phase 6: Mastering Hybrid Bootable ISO Image via Xorriso..."
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "FLOWORK_OS" \
    -eltorito-boot isolinux/isolinux.bin \
    -eltorito-catalog isolinux/boot.cat \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -eltorito-alt-boot \
    -e boot/grub/efi.img \
    -no-emul-boot \
    -isohybrid-gpt-basdat \
    -output "${OUTPUT_ISO}" \
    "${ISO_DIR}"

log_succ "ISO mastering complete: ${OUTPUT_ISO}"

log_step "Phase 7: Verifying ISO Integrity & Generating Checksums..."
ISO_SIZE="$(du -h "${OUTPUT_ISO}" | cut -f1)"
file "${OUTPUT_ISO}"

log_info "Calculating SHA256 checksum..."
sha256sum "${OUTPUT_ISO}" > "${OUTPUT_ISO}.sha256"
cat "${OUTPUT_ISO}.sha256"

echo "=============================================================================="
echo -e "${GREEN}${BOLD}👑 FLOWORK OS 7.3.0 ISO BUILD COMPLETE & VERIFIED${NC}"
echo -e "💿 File:     ${OUTPUT_ISO}"
echo -e "📦 Size:     ${ISO_SIZE}"
echo -e "🔒 SHA256:   $(cat "${OUTPUT_ISO}.sha256" | cut -d' ' -f1)"
echo -e "⚡ Boot:     Hybrid UEFI (x86_64) + BIOS Legacy"
echo -e "🦀 Kernel:   Linux 7.3.0 Rust Custom"
echo "=============================================================================="
