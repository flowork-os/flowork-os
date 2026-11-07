#!/usr/bin/env bash
# ==============================================================================
# Flowork OS Sovereign Browser MCP Server
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "$SCRIPT_DIR/chrome-devtools-mcp.mjs" "$@"
