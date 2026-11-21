#!/usr/bin/env bash
# =============================================================================
# 🚀 Flowork Sovereign OS — Interactive Desktop Surface Runner
# Wrapper around flowork-desktop-canvas.py
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/flowork-desktop-canvas.py" "$@"
