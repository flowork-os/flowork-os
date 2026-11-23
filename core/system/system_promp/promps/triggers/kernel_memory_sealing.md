# MRFLOW KERNEL MEMORY SEALING DIRECTIVE

## 1. Context & Activation Scope
Applies when maintaining, inspecting, hardening, or debugging `/opt/floworkos/bin/mrflow` (`mrflow-rs`), runtime memory protections, anti-debug sentinels, or core daemon process integrity.

## 2. Mandatory Behavioral Invariants
- **Pure Rust Native ELF Execution:** Operate `/opt/floworkos/bin/mrflow` exclusively as a stripped release ELF compiled from `/opt/floworkos/mrflow-rs/`, with zero wrapped JavaScript chunks or external runtime VMs.
- **Zero Disk Secret Exposure:** Never unpack, cache, or stage plaintext credentials, tokens, or memory dumps into `/dev/shm`, `/tmp`, or swap-backed directories.
- **Kernel Anti-Debug & Dump Guards:** Enforce process non-dumpability (`PR_SET_DUMPABLE = 0`), `TracerPid` inspection, and kernel `memfd` immutability seals (`F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE`) whenever sealed shared buffers are allocated.
- **Process Hygiene & FD Isolation:** Drain child pipes cleanly with bounded timeouts so detached descendants cannot inherit sensitive descriptors or stall command exits.
- **Decoupled GUI Architecture:** Companion UI scripts (`mrflow-sidebar.py`) and terminal launchers MUST remain decoupled external files communicating solely over NDJSON streams.

## 3. Strict Prohibitions
- NEVER reintroduce legacy Node.js wrappers, monolithic JS bundles, or `/dev/shm` source unpacking.
- NEVER disable `TracerPid` sentinels, `PR_SET_DUMPABLE = 0` hardening, or secret scrubbing.
- NEVER leave core dumps, plaintext credential buffers, or debug symbols in release ELFs.
