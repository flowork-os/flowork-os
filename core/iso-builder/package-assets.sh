#!/usr/bin/env bash
# ==============================================================================
# 👑 FLOWORK OS — SOVEREIGN ASSET PACKAGER FOR ON-DEMAND HYDRATION
# Compresses heavy decoupled subsystems into zstd release assets for GitHub Releases
# Target: Flowork OS (Linux 7.3.0-flowork-rust)
# ==============================================================================
set -e

DEST_DIR="${HOME}/Downloads/flowork-release-assets"
mkdir -p "$DEST_DIR"
cd /opt/floworkos

echo "=========================================================================="
echo "👑 FLOWORK OS: PACKAGING DECOUPLED ON-DEMAND ASSETS"
echo "Target Output Directory: $DEST_DIR"
echo "=========================================================================="

# 1. Android Micro-VM Subsystem (System Images + Emulator)
if [ -d "android-sdk/system-images" ] && [ -d "android-sdk/emulator" ]; then
    echo "→ Packaging Android Micro-VM Subsystem..."
    tar --exclude='*.lock' --exclude='*.qcow2' -I 'zstd -T0 -3' -cf \
        "${DEST_DIR}/flowork-android-subsystem.tar.zst" \
        android-sdk/system-images \
        android-sdk/emulator
    echo "  ✓ flowork-android-subsystem.tar.zst created: $(du -h "${DEST_DIR}/flowork-android-subsystem.tar.zst" | cut -f1)"
fi

# 2. Audacity OpenVINO AI Studio
if [ -d "apps/audacity" ]; then
    echo "→ Packaging Audacity Studio Runtime..."
    tar -I 'zstd -T0 -3' -cf \
        "${DEST_DIR}/flowork-audacity.tar.zst" \
        apps/audacity
    echo "  ✓ flowork-audacity.tar.zst created: $(du -h "${DEST_DIR}/flowork-audacity.tar.zst" | cut -f1)"
fi

# 3. OpenScreen Video Demo Studio
if [ -d "apps/openscreen" ]; then
    echo "→ Packaging OpenScreen Video Studio..."
    tar -I 'zstd -T0 -3' -cf \
        "${DEST_DIR}/flowork-openscreen.tar.zst" \
        apps/openscreen
    echo "  ✓ flowork-openscreen.tar.zst created: $(du -h "${DEST_DIR}/flowork-openscreen.tar.zst" | cut -f1)"
fi

# 4. Wine Staging & Audio Production
if [ -d "apps/wine-staging" ]; then
    echo "→ Packaging Wine Staging & Audio Production Engine..."
    tar -I 'zstd -T0 -3' -cf \
        "${DEST_DIR}/flowork-wine-staging.tar.zst" \
        apps/wine-staging \
        apps/flstudio 2>/dev/null || tar -I 'zstd -T0 -3' -cf "${DEST_DIR}/flowork-wine-staging.tar.zst" apps/wine-staging
    echo "  ✓ flowork-wine-staging.tar.zst created: $(du -h "${DEST_DIR}/flowork-wine-staging.tar.zst" | cut -f1)"
fi

# 5. Social Auto Upload Engine (Clean of cookies & personal data)
if [ -d "apps/social-auto-upload" ]; then
    echo "→ Packaging Social Auto Upload Engine..."
    tar --exclude='apps/social-auto-upload/cookies/*' \
        --exclude='apps/social-auto-upload/videos/*' \
        --exclude='apps/social-auto-upload/db/*.db' \
        --exclude='apps/social-auto-upload/.venv' \
        -I 'zstd -T0 -3' -cf \
        "${DEST_DIR}/flowork-social-auto-upload.tar.zst" \
        apps/social-auto-upload
    echo "  ✓ flowork-social-auto-upload.tar.zst created: $(du -h "${DEST_DIR}/flowork-social-auto-upload.tar.zst" | cut -f1)"
fi

# Generate SHA256 checksums for all packages
echo "→ Generating SHA-256 verification signatures..."
cd "$DEST_DIR"
sha256sum *.tar.zst > SHA256SUMS.txt

echo ""
echo "=========================================================================="
echo "✓ ALL ON-DEMAND ASSETS PACKAGED SUCCESSFULLY!"
ls -lh "$DEST_DIR"
echo "=========================================================================="
