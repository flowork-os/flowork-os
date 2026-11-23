#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Neural State Bridge (RAM Shared Memory)
# Real-Time Bridge connecting Mr. Flow Agents, Voice Daemon & Living Wallpaper
# Zero Disk I/O: Atomic JSON updates in /dev/shm
# Co-authored-by: Flowork OS Architecture Board & Dr. Flow <agent@floworkos.com>
# =============================================================================

import os
import json
import time

STATE_FILE = "/dev/shm/flowork-neural-state.json"

def get_tool_morphology(tool_name: str) -> str:
    """Map tool name to one of the 6 Flowork Sovereign visual morphologies."""
    name = (tool_name or "").lower()
    # 1. Circle / Sonar Radar (Search, Grep, Web, Glob, Schedule, Thinking)
    if any(k in name for k in ("search", "grep", "glob", "find", "schedule", "cron", "think", "reason", "brain", "web", "url")):
        return "morph-circle"
    # 2. Frameless Holographic Laser Sweep (View, Read, Inspect, Cat)
    if any(k in name for k in ("view", "read", "cat", "inspect", "open", "show")):
        return "morph-frameless"
    # 3. Chamfered Crystalline Lattice (Write, Edit, Replace, Patch, Lock)
    if any(k in name for k in ("write", "replace", "patch", "lock", "edit", "perm", "chmod", "update")):
        return "morph-chamfer"
    # 4. Swarm / Tri-Node Gravitational Field (Subagent, Swarm, Concurrency, Task)
    if any(k in name for k in ("subagent", "agent", "swarm", "manage_task", "manage_subagents")):
        return "morph-swarm"
    # 5. Terminal / Phosphor Cyber-Grid (Run Command, Bash, Shell, Terminal Execution)
    return "morph-terminal"

def set_neural_state(state: str, tool_name: str = "", morphology: str = "", action: str = "", amplitude: float = 0.0):
    """
    Atomically updates the neural reactor state in shared memory (/dev/shm).
    state: "idle" | "thinking" | "tool_use" | "speaking"
    morphology: "morph-idle" | "morph-terminal" | "morph-circle" | "morph-frameless" | "morph-chamfer" | "morph-swarm" | "morph-speech"
    """
    try:
        morph = morphology
        if not morph:
            if state == "speaking":
                morph = "morph-speech"
            elif state == "tool_use":
                morph = get_tool_morphology(tool_name)
            elif state == "thinking":
                morph = "morph-thinking"
            else:
                morph = "morph-idle"

        data = {
            "state": state,
            "tool_name": tool_name or "",
            "morphology": morph,
            "action": action or "",
            "amplitude": max(0.0, min(1.0, float(amplitude))),
            "timestamp": time.time()
        }
        tmp_file = f"{STATE_FILE}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_file, STATE_FILE)
    except Exception:
        pass

def get_neural_state():
    """Reads current neural state from shared memory with auto-expiration guard."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Auto expire if state is older than 45 seconds to prevent stale states
                if time.time() - data.get("timestamp", 0) > 45.0:
                    return {"state": "idle", "morphology": "morph-idle", "amplitude": 0.0, "tool_name": "", "action": ""}
                return data
    except Exception:
        pass
    return {"state": "idle", "morphology": "morph-idle", "amplitude": 0.0, "tool_name": "", "action": ""}
