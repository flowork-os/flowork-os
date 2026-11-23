# Context & Activation Scope
Active when designing, building, debugging, or integrating Model Context Protocol (MCP) servers, clients, tools, resources, and stdio/HTTP transports.

# Mandatory Behavioral Invariants
1. **Stateless Robust Transport:** Support standard stdio and Streamable HTTP/SSE protocols. Keep MCP servers stateless; maintain all runtime session context explicitly within Flowork OS state stores.
2. **Actionable Tool Contracts:** Write unambiguous tool descriptions, strict JSON schemas, and clear error responses. If an invocation fails, return structured, actionable troubleshooting guidance rather than generic stack traces.
3. **Canonical Location:** All persistent MCP servers and configurations must reside strictly under `/opt/floworkos/mcp/` with standardized entry points.
4. **High-Speed Execution:** Minimize serialization latency and avoid external network handshakes on local tool paths. Return native Exit Code 0 and deterministic outputs.

# Strict Prohibitions
- PROHIBITED: Exposing unbounded destructive tools without explicit parameter constraints or confirmation guards.
- PROHIBITED: Writing unversioned MCP server manifests or scattering server binaries outside `/opt/floworkos/mcp/`.
- PROHIBITED: Hardcoding sensitive credentials or API keys directly in MCP configuration files.
