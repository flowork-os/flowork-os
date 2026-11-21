#!/usr/bin/env bash
# ==============================================================================
# Flowork OS Sovereign Browser MCP Server (Pure Rust)
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/flowork-browser-mcp" "$@"
