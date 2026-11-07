# UNIVERSAL CPU COMPATIBILITY & CONNECTOR RUNTIME DOCTRINE

## 1. Context & Activation Scope
Applies whenever configuring AI gateway services, packaging the connector subsystem, or debugging CPU instruction crashes (`SIGILL`, exit code 132).

## 2. Mandatory Behavioral Invariants
- Enforce universal Node.js runtime execution (`/opt/floworkos/connector/server/index.js`) rather than target-specific binary compilation requiring AVX2/BMI2.
- Support legacy instruction baselines (Intel Ivy Bridge, Core 2 Duo, AMD K10) through universal x86-64 bytecode execution without illegal opcode traps.
- Ensure all default system vault configurations (`/opt/floworkos/connector/data/vault.json`) remain unauthenticated blank templates to prevent credential leakage into ISO distributions.
- Implement kernel atomic mutex locks (`fcntl.flock`) on singleton GUI components to eliminate duplicate process spawns across concurrent session services.
- Auto-generate all canonical bookmark directories on session startup with open write permissions (`777`).

## 3. Strict Prohibitions
- Never bundle pre-authenticated tokens or personal account lists into `/opt/floworkos/` system paths.
- Never package binaries compiled with host-specific SIMD instruction assumptions without universal fallback paths.
- Never spawn concurrent duplicate systemd services binding identical network ports (:9099).
