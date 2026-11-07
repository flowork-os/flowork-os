#!/usr/bin/env bash
# ==============================================================================
# Flowork Sovereign Stealth - Camoufox Engine Setup & Provisioning
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

echo "[*] Initializing Camoufox Virtualenv at: ${VENV_DIR}"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

echo "[*] Installing dependencies from requirements.txt..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"

echo "[*] Ensuring active Camoufox C++ engine binary is fetched..."
"${VENV_DIR}/bin/camoufox" fetch

echo "[✓] Camoufox engine provisioning completed with Exit Code 0."
