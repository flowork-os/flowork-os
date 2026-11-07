#!/usr/bin/env bash
# ==============================================================================
# 👑 FLOWORK OS - SOVEREIGN RUST KERNEL LAUNCHER (QEMU GTK)
# ==============================================================================
set -euo pipefail

KERNEL_DIR="$HOME/kernel-dev"
KERNEL_IMAGE="$KERNEL_DIR/linux-rust/arch/x86/boot/bzImage"
INITRAMFS="$KERNEL_DIR/initramfs-gui.cpio.gz"

if [ ! -f "$KERNEL_IMAGE" ]; then
    echo "❌ Kernel image not found at $KERNEL_IMAGE"
    exit 1
fi

if [ ! -f "$INITRAMFS" ]; then
    echo "❌ Initramfs not found at $INITRAMFS"
    exit 1
fi

echo "🚀 Meluncurkan Flowork OS Sovereign Rust Kernel di QEMU..."
exec qemu-system-x86_64 \
    -kernel "$KERNEL_IMAGE" \
    -initrd "$INITRAMFS" \
    -m 1024M \
    -smp 2 \
    -vga std \
    -display gtk,zoom-to-fit=on \
    -append "console=ttyS0 console=tty0 panic=-1 rdinit=/init" \
    -name "Flowork OS - Rust Linux Kernel v7.3"
