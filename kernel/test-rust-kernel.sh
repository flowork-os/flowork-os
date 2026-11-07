#!/usr/bin/env bash
set -e

KERNEL_IMG="$HOME/kernel-dev/linux-rust/arch/x86/boot/bzImage"
INITRD="$HOME/kernel-dev/initramfs-test.cpio.gz"

if [ ! -f "$KERNEL_IMG" ]; then
    echo "[-] Error: Kernel bzImage tidak ditemukan di $KERNEL_IMG"
    exit 1
fi

echo "=========================================================="
echo "👑 MENJALANKAN UJI OTOMATIS LINUX RUST KERNEL (QEMU) 👑"
echo "=========================================================="
echo "Kernel: $KERNEL_IMG"
echo "Menjalankan boot test..."
echo "----------------------------------------------------------"

qemu-system-x86_64 \
    -kernel "$KERNEL_IMG" \
    -initrd "$INITRD" \
    -nographic \
    -append "console=ttyS0 panic=-1 loglevel=4" \
    -m 512M \
    -no-reboot

echo "----------------------------------------------------------"
echo "✅ Uji Otomatis Berhasil Selesai!"
echo "=========================================================="
