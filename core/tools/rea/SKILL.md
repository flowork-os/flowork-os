---
name: rea
description: Master procedural doctrine for running the unified REA reverse engineering tool on binary, web, mobile, and memory targets.
keywords:
  - reverse_engineering
  - binary_analysis
  - disassembly
  - decompilation
  - elf
  - pe
  - macho
  - apk
  - wasm
  - memory
  - symbols
  - cross_references
  - objdump
  - rizin
  - frida
  - static_analysis
  - dynamic_analysis
  - inspection
  - bytecode
  - flowork
---

# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: REA RUNNER

When invoking the `rea` tool, adhere to sovereign operational principles:

1. **Selective Invocation (Anti-Bloat):**
   - Use targeted commands such as `inspect-artifact`, `analyze`, `decompile`, or `xrefs` rather than full workspace scans.
   - For binary diagnostics, specify `target` parameter pointing to the verified file path.

2. **Deterministic Output:**
   - The tool defaults to `--format json`. Filter or project keys as needed to avoid context saturation.
   - When inspecting large binaries, prefer `inspect-binary-layout` or `inspect-native-exports` before attempting full decompilation.

3. **Empirical Gate (Exit Code 0):**
   - Successful commands produce valid JSON or structured output with exit code 0.
   - On error, review `stderr` diagnostics and verify the file format or provider requirements.
