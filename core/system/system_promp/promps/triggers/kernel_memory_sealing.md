# MRFLOW KERNEL MEMORY SEALING DIRECTIVE

## 1. Context & Activation Scope
Applies when maintaining, inspecting, building, or debugging the `mrflow` binary loader, monolithic JavaScript bundles, anti-decompilation defenses, or runtime execution memory.

## 2. Mandatory Behavioral Invariants
- **Zero Disk Unpacking:** Never unpack plaintext JavaScript source chunks to `/dev/shm`, `/tmp`, or any filesystem directory.
- **Option 2 memfd_create Sealing:** The Rust loader MUST allocate anonymous kernel memory via `libc::SYS_memfd_create` with `MFD_ALLOW_SEALING`.
- **Kernel Immutability Seals:** Apply `F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE` immediately after writing decrypted code to ensure zero in-memory tampering.
- **Preserve Symlinks Main:** Execute Node via `node --preserve-symlinks-main /tmp/.flowork_core_<pid>_<nanos>.mjs`, passing the sealed high descriptor (`42`) across `exec` with `F_SETFD = 0`.
- **Zero-Trace Ephemeral Cleanup:** Wrap the `/tmp` symlink in an RAII Drop guard (`SymlinkGuard`) ensuring instant unlinking and descriptor closure upon process termination.
- **Biometric Invariant Verification:** Always compute and verify the Biometric Invariant Matrix (Chars, Spaces, Vowels a,i,u,e,o) post-decryption before memory allocation.
- **Decoupled GUI Architecture:** Sidebar (`mrflow-sidebar.py`) and CLI terminal launcher scripts MUST remain outside the binary as directly editable source files.

## 3. Strict Prohibitions
- NEVER reintroduce directory-based ramdisk unpacking into `/dev/shm`.
- NEVER disable anti-debug sentinels (`TracerPid` detection and `PR_SET_DUMPABLE = 0`).
- NEVER leave plaintext JS source files exposed in filesystem mounts during execution.
