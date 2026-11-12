# EPISODIC MEMORY, NEURAL BUS & LANDLOCK SANDBOX INVARIANTS

## 1. Context & Activation Scope
Activate only when modifying, debugging, or invoking `mrflow-rs` episodic FTS5 memory, `memory_crystallizer`, `flowork-neural-bus` / `flowork-pipe` studio pipelines, `flowork-tool-runner` Landlock gating, or `/dev/shm` DRM capture.

## 2. Mandatory Behavioral Invariants
- Keep JIT episodic recall strictly bounded (`<= 3` matches, `<= 1200` chars) and auto-crystallize only verified recoveries or multi-step workflows with `Exit Code 0`.
- Scrub API keys, Bearer/GitHub tokens, and `$HOME` paths before writing `episodic_memory.db`.
- Pass `RUSTFLAGS="--remap-path-prefix=$HOME=/opt/build"` when compiling release binaries and verify zero `$HOME` hits via `strings`.
- Preserve all `/opt/floworkos/tools/<tool>/run` hardlinks via `ln -f` whenever replacing `/opt/floworkos/bin/flowork-tool-runner`.
- Check live Landlock ABI (`flowork-tool-runner --check` or `:18090/api/agent/sandbox/status`); rely on `FLOWORK_SANDBOX_MODE=auto` unless kernel Landlock ABI `> 0`.

## 3. Strict Prohibitions
- Never inject full `.fl_brain/*.md` dumps or unconditional prompts into the base system prompt.
- Never overwrite `/opt/floworkos/bin/flowork-tool-runner` without re-linking all `/opt/floworkos/tools/*/run` hardlinks.
- Never claim Landlock kernel confinement or NVIDIA GPU acceleration is active while `landlock_abi <= 0` or `nvidia` module is unloaded.
