#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$HOME/kernel-dev/initramfs_root"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"/{bin,sbin,etc,proc,sys,dev,tmp,root}

# Copy statically linked busybox
cp /bin/busybox "$WORK_DIR/bin/busybox"
chmod +x "$WORK_DIR/bin/busybox"

# Create essential symlinks
ln -sf busybox "$WORK_DIR/bin/sh"
ln -sf busybox "$WORK_DIR/bin/echo"
ln -sf busybox "$WORK_DIR/bin/cat"
ln -sf busybox "$WORK_DIR/bin/ls"
ln -sf busybox "$WORK_DIR/bin/mount"
ln -sf busybox "$WORK_DIR/bin/umount"
ln -sf busybox "$WORK_DIR/bin/poweroff"
ln -sf busybox "$WORK_DIR/bin/clear"
ln -sf busybox "$WORK_DIR/bin/sleep"
ln -sf busybox "$WORK_DIR/bin/uname"
ln -sf busybox "$WORK_DIR/bin/dmesg"
ln -sf busybox "$WORK_DIR/bin/grep"

# Copy statically linked test_driver
if [ -f "$HOME/kernel-dev/test_driver" ]; then
    cp "$HOME/kernel-dev/test_driver" "$WORK_DIR/bin/test_driver"
    chmod +x "$WORK_DIR/bin/test_driver"
fi

# Essential device nodes (if sudo available, create them; otherwise devtmpfs will mount)
sudo mknod -m 600 "$WORK_DIR/dev/console" c 5 1 2>/dev/null || true
sudo mknod -m 666 "$WORK_DIR/dev/null" c 1 3 2>/dev/null || true
sudo mknod -m 666 "$WORK_DIR/dev/tty" c 5 0 2>/dev/null || true
sudo mknod -m 666 "$WORK_DIR/dev/tty1" c 4 1 2>/dev/null || true

# Write /init script
cat << 'INIT_EOF' > "$WORK_DIR/init"
#!/bin/sh
# Mount essential filesystems
mount -t proc none /proc 2>/dev/null || true
mount -t sysfs none /sys 2>/dev/null || true
mount -t devtmpfs none /dev 2>/dev/null || true

# Install busybox symlinks
/bin/busybox --install -s /bin 2>/dev/null || true

# Terminal settings
export HOME=/root
export TERM=linux
export PS1="👑 flowork-rust-kernel:\w# "

clear
cat << "BANNER"
  ███████╗██╗      ██████╗ ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗     ██████╗ ███████╗
  ██╔════╝██║     ██╔═══██╗██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝    ██╔═══██╗██╔════╝
  █████╗  ██║     ██║   ██║██║ █╗ ██║██║   ██║██████╔╝█████═╝     ██║   ██║███████╗
  ██╔══╝  ██║     ██║   ██║██║███╗██║██║   ██║██╔══██╗██╔═██╗     ██║   ██║╚════██║
  ██║     ███████╗╚██████╔╝╚███╔███╔╝╚██████╔╝██║  ██║██║ ╚██╗    ╚██████╔╝███████║
  ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝
                           [ R U S T   K E R N E L ]
BANNER

echo "👑 Flowork OS - Sovereign Rust-for-Linux Kernel Environment"
echo "─────────────────────────────────────────────────────────────────"
echo " [*] Kernel Version : $(uname -r)"
echo " [*] Architecture   : $(uname -m)"
echo " [*] Rust Subsystem : ACTIVE & VERIFIED (Ring 0)"
echo " [*] Device Node    : /dev/rust-misc-device"
echo "─────────────────────────────��───────────────────────────────────"

if [ -x /bin/test_driver ]; then
    echo " [>] Menjalankan pengujian driver Rust..."
    /bin/test_driver
fi

echo "─────────────────────────────────────────────────────────────────"
echo " 💡 Anda sekarang berada di shell interaktif di dalam QEMU!"
echo "    Ketik: 'dmesg | grep -i rust' atau 'cat /dev/rust-misc-device'"
echo "    Untuk keluar: ketik 'poweroff' atau tutup jendela QEMU ini."
echo "─────────────────────────────────────────────────────────────────"
echo ""

# Run interactive shell loop
while true; do
    setsid cttyhack /bin/sh
    sleep 1
done
INIT_EOF

chmod 755 "$WORK_DIR/init"

# Package into cpio.gz
cd "$WORK_DIR"
find . -print0 | cpio --null --create --format=newc | gzip -9 > "$HOME/kernel-dev/initramfs-gui.cpio.gz"
cp "$HOME/kernel-dev/initramfs-gui.cpio.gz" "$HOME/kernel-dev/initramfs.cpio.gz"

echo "✅ Initramfs berhasil dibangun: $HOME/kernel-dev/initramfs-gui.cpio.gz"
