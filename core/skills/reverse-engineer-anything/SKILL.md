---
name: reverse-engineer-anything
description: Reverse engineer native binaries, mobile APKs, JavaScript/Electron packages, and firmware targets using REA with zero prompt bloat.
domain: security
keywords:
  - reverse_engineering
  - binary_analysis
  - disassembly
  - decompilation
  - elf
  - pe
  - macho
  - apk
  - firmware
  - ghidra
  - rizin
  - objdump
  - static_analysis
  - dynamic_analysis
  - symbol_extraction
  - cross_reference
  - assembly
  - bytecode
  - flowork
  - audit
---

# ⚡ FLOWORK OS SOVEREIGN SKILL: REVERSE ENGINEER ANYTHING (REA)

## 1. Objective
Enable autonomous, safe, and token-efficient reverse engineering workflows on Flowork OS. This skill governs the inspection, decompilation, binary layout reconstruction, and runtime observation of compiled artifacts (ELF, PE, Mach-O, Android APK/DEX, Electron, WebAssembly, and firmware) without creating persistent prompt bloat.

## 2. Prerequisites
1. **Target Existence:** Verify that the artifact under analysis physically exists on disk and is accessible.
2. **Runtime Engine:** Flowork OS Pure Rust `flowork-tool-runner` engine is configured for executing the native REA tool suite.
3. **Execution Tool:** Utilize the native conditional tool `/opt/floworkos/tools/rea/run` via `run_shell_command`.
4. **Safety Isolation:** Analyze targets in read-only mode; do not execute untrusted binaries outside sandboxed environments.

## 3. Standard Operating Procedure (SOP)

### Step 1: Initial Artifact Identification & Entropy Check
Begin with lightweight static inspection before invoking heavy disassemblers:
```bash
/opt/floworkos/tools/rea/run '{"command":"inspect-byte-entropy","target":"/path/to/binary"}'
```
Analyze section entropy to determine whether the binary is packed, compressed, or encrypted.

### Step 2: Binary Metadata & Symbol Triage
Extract architectural layout, exported routines, and imported symbols:
```bash
/opt/floworkos/tools/rea/run '{"command":"inspect-artifact","target":"/path/to/binary"}'
```
For managed runtimes (e.g., .NET, Android APK), identify entry points and manifest declarations before drilling into code.

### Step 3: Targeted Function Analysis & Cross-References
Focus decompilation strictly on candidate functions of interest rather than entire codebases:
```bash
/opt/floworkos/tools/rea/run '{"command":"xrefs","target":"/path/to/binary","args":["--address","0x1000"]}'
```
Query specific routines and call graphs to answer targeted architectural questions.

### Step 4: Managed & Web Application Reconstruction
For Electron or JavaScript bundles, extract packed assets and reconstruct modules:
```bash
/opt/floworkos/tools/rea/run '{"command":"analyze-javascript-application","target":"/path/to/app.asar"}'
```

## 4. Verification & Quality Gates
1. **Empirical Gate (Exit Code 0):** Every analytical query must terminate with status code 0 and emit valid structured JSON.
2. **Schema Integrity:** Verify that output conforms to REA normalized evidence format with confidence ratings and limitation disclosures.
3. **Reproducibility:** Analysis parameters and target digests (SHA-256) must be captured in the operational audit trail.

## 5. Failure Modes & Recovery
1. **Missing Provider Tooling:**
   - *Symptom:* `provider_unavailable` error returned for specialized providers (e.g. Ghidra, Pwntools).
   - *Recovery:* Fall back to built-in self-contained providers (`byte-entropy`, `inspect-artifact`, or standard system utilities like `objdump` and `readelf`).
2. **Unsupported File Architecture:**
   - *Symptom:* `unsupported_format` reported during parsing.
   - *Recovery:* Inspect binary magic bytes with `file` or `hexdump` to determine file encapsulation before re-attempting extraction.
3. **Memory / Token Saturation:**
   - *Symptom:* Output exceeds context capacity.
   - *Recovery:* Apply pagination flags (`--token-limit`, `--token-offset`) or filter JSON fields before rendering.

## 6. Strict Prohibitions
- PROHIBITED to register bulk MCP tools that flood the baseline system prompt.
- PROHIBITED to execute unknown target binaries natively without virtualization or sandboxing.
- PROHIBITED to modify the active target binary during static analysis.
