# NETWORK STREAM STALL & DEADLOCK RECOVERY GUARD

## 1. Context & Activation Scope
Triggered when network streaming, socket connections, API stalls, or agent freezes are discussed, investigated, or handled.

## 2. Mandatory Behavioral Invariants
- Enforce strict kernel TCP keepalive (`net.ipv4.tcp_keepalive_time=60`, `intvl=10`, `probes=3`) in `/etc/sysctl.d/99-flowork-network.conf` to detect severed sockets within 90 seconds.
- Enforce HTTP client TCP keepalive (30s) in `flowork-connector` (`connector-rs`) to terminate half-open sockets when upstream servers drop.
- In `mrflow-sidebar.py`, maintain a background inactivity watchdog (90s ceiling) that intercepts stalled streams and aborts hung processes cleanly without freezing the UI.
- When aborting agent turns, ensure process groups (`os.killpg`) and all child MCP servers are terminated to eliminate zombie processes.
- Always inspect `/proc/<pid>/wchan`, socket states via `ss -tapn`, and process trees before making remediation claims.

## 3. Strict Prohibitions
- Never allow unmonitored blocking `readline()` calls without watchdog protection.
- Never rely on default Linux 7200s TCP keepalive for real-time AI streaming agents.
- Never claim deadlock resolution without verifying process termination and service recovery with Exit Code 0.
