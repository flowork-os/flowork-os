# GPU Task Manager (`gputaskman` / `flowork-taskman`)
**Sovereign First-Party Rust GPU & AI Telemetry Engine for Flowork OS**

Part of the Flowork OS native core (`floworkos.com`).

---

## 1. Overview
`gputaskman` is a high-speed, zero-dependency, clean-room native Rust hardware and AI workload telemetry monitor designed specifically for Flowork OS. It provides real-time monitoring of GPU utilization, VRAM allocation, power draw, thermals, CPU cores, host memory, and automatic classification of LLM/AI runtimes (Ollama, vLLM, ComfyUI, PyTorch, llama.cpp, GGUF workers).

### Key Architectural Highlights
- **100% Native Rust Clean-Room:** Built using `ratatui`, `crossterm`, `sysinfo`, and direct DRM / NVML telemetry.
- **Zero Python / PyInstaller Overhead:** Startup time < 10ms, binary footprint < 1 MB (down from 41 MB legacy PyInstaller bundle).
- **Dual-Mode Operation:** Full interactive keyboard-driven TUI, plus headless CLI integration with Flowork Neural Bus (`--json`, `--once`, `--list-gpus`).
- **AI Workload Identification:** Automatically scans running processes, parent chains, and open memory-mapped models to identify active AI agents and inference servers.

---

## 2. Usage

### Interactive TUI Mode
```bash
# Launch interactive terminal TUI
gputaskman

# Launch inside dedicated Sovereign Glass Alacritty window
gputaskman --window

# Custom refresh interval (e.g. 0.5s)
gputaskman -i 0.5
```

#### Keyboard Navigation
- `q` or `Ctrl+C`: Quit
- `j` / `↓`: Move selection down
- `k` / `↑`: Move selection up
- `s` / `Tab`: Cycle sort criteria (`VRAM` -> `CPU%` -> `RAM` -> `PID`)
- `/`: Enter process filter mode (filter by name, PID, or AI tag)
- `x` / `K`: Send SIGTERM to terminate selected process
- `r`: Force instant metrics refresh
- `?`: Toggle help overlay

### Headless & Neural Bus CLI Mode
```bash
# Dump full telemetry snapshot as JSON
gputaskman --json

# Human-readable one-shot terminal snapshot
gputaskman --once

# Enumerate available GPU accelerators
gputaskman --list-gpus

# Neural bus proxy CLI
/opt/floworkos/apps/gputaskman/bin/gputaskman-cli snapshot
/opt/floworkos/apps/gputaskman/bin/gputaskman-cli list-gpus
```

---

## 3. License
Licensed under the **Apache License, Version 2.0**.
See [LICENSE](LICENSE) for details.
