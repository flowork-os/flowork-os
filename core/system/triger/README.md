# 🎯 FLOWORK OS — ACTIVE TRIGGER SUBSYSTEM & WATCHDOG ARCHITECTURE GUIDE

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/system/triger/`  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

# 🛑 SUPREME LAW: ZERO PERSISTENT PROMPTS — 100% CONDITIONAL TRIGGER MANDATE
## ⚠️ CREATING ALWAYS-ON GLOBAL PROMPTS IS STRICTLY PROHIBITED

> **THE ANTI-BLOAT LAW:**  
> Adding new fixes or intelligence to the always-loaded base prompt is **STRICTLY FORBIDDEN**.  
> Every new prompt **MUST BE 100% CONDITIONAL** (Passive Trigger via `rules/.bin/` or `promps/triggers/`, or an Active Watchdog). A prompt is ONLY injected when its physical condition or active turn keywords match, preventing fatal prompt bloat and context saturation.

---

## 1. Executive Philosophy: What is a Trigger in Flowork OS?

In Flowork OS, a **Trigger** is an environmental sensory receptor and automated reflex mechanism. Triggers continuously observe the physical state of the operating system, workspace filesystem, hardware resources, and active runtime processes to inject high-priority contextual directives into the agent's active consciousness.

### Non-Dualism of Runtime Capabilities:
- **TOOL (`/opt/floworkos/tools/<tool_name>/`):** The atomic instrument of physical action (Hands & Scalpels).
- **SKILL (`/opt/floworkos/skills/<skill_name>/`):** The operational playbook, multi-step SOP, and domain heuristics (Procedural Brain Lobe).
- **PROMPT (`/opt/floworkos/system/system_promp/promps/`):** The living conscience, behavioral constraints, and dynamic environmental instincts (Soul & Reflexes).
- **AGENT (`/opt/floworkos/agents/<agent_name>.md`):** The delegated autonomous worker operating in an isolated sub-turn sandbox.
- **POLICY (`/opt/floworkos/policies/*.toml`):** The system-level legal constitution and security governance gate.
- **TRIGGER (`/opt/floworkos/system/triger/` & `/opt/floworkos/system/system_promp/`):** The nervous system and automated reflex arc that detects environmental conditions and emergency anomalies.

---

## 2. Core Architectural Distinction: Active Triggers vs. Passive Triggers

Flowork OS enforces a rigorous architectural separation between **Active Triggers** and **Passive Triggers**:

| Architectural Dimension | Active Triggers (`/opt/floworkos/system/triger/`) | Passive Triggers (`/opt/floworkos/system/system_promp/`) |
| :--- | :--- | :--- |
| **Execution Mode** | **Continuous Watchdog Daemon (Asynchronous)** | **Event-Driven / JIT Evaluation (Synchronous)** |
| **Runtime Presence** | Runs constantly in the background as an OS daemon/subprocess. | Does NOT run in background; evaluated only when MrFlow starts or executes a turn. |
| **Primary Location** | `/opt/floworkos/system/triger/<watchdog_name>/` | `/opt/floworkos/system/system_promp/rules/` and `promps/triggers/` |
| **Evaluation Method** | Polling loop with fixed intervals (e.g. 10s-15s) and cooldown timers. | Native compiled Rust rules (`rules/.bin/*`) + Formula 5-3-3 Router (`mrflow-rs`). |
| **Delivery Mechanism** | Writes alert payload to IPC buffer file (`/tmp/flowork_active_trigger.json`). | Injected directly into the system prompt envelope or tool response stream. |
| **Typical Use Cases** | Dynamic system breaches: RAM >90%, Disk full, CPU runaway processes, kernel/repo alerts. | Static environmental facts: Landmark file presence (`Cargo.toml`), git status, active tool keywords. |
| **Resource Footprint** | Lightweight daemon sleeping between intervals; near-zero CPU. | Exactly **0% CPU when idle** (zero background processes). |
| **Interrupt Priority** | **Emergency High-Priority Interrupt:** Prepends alert when active & within `300s` TTL. | Standard contextual guidance appended to turn context envelope. |

---

## 3. How the Active Trigger Subsystem Works

The active trigger subsystem operates on an asynchronous supervisor-daemon loop that communicates with MrFlow via an IPC signal file:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DAEMON SUPERVISOR (/opt/floworkos/system/triger/supervisor.py)      │
│ Scans /opt/floworkos/system/triger/* (ignoring templates/__pycache__)  │
│ Auto-discovers watcher (ELF) -> watcher.sh -> watcher.py -> watcher.rs │
│ (compiles .rs via rustc -O); restarts any crashed daemon cleanly.      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Spawns active watcher daemons]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. CONTINUOUS SYSTEM WATCHERS (4 Live Watchdog Modules)                │
│ - process_watchdog    (Monitors runaway PIDs, CPU saturation, leaks)   │
│ - system_telemetry    (Monitors RAM >90%, Swap, Disk thresholds)       │
│ - kernel_telemetry    (Monitors kernel dmesg/oops & thermal telemetry) │
│ - github_update_watch (Monitors remote repository release/sync state)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Threshold breached AND cooldown satisfied]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. IPC SIGNAL DISPATCH (/tmp/flowork_active_trigger.json)              │
│ Watcher writes high-priority JSON alert payload to the IPC buffer.     │
│ Updates .last_alert timestamp to enforce cooldown_seconds.             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [MrFlow executes active turn]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. ORCHESTRATOR INTERCEPT (mrflow-rs/src/cognitive/mod.rs)             │
│ MrFlow checks /tmp/flowork_active_trigger.json (ACTIVE_TRIGGER_TTL_SECS│
│ = 300s): rejects stale timestamps (>5 min old), otherwise injects:     │
│ [# 🚨 ACTIVE WATCHDOG SIGNAL [source] ...]                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Active Trigger Authoring Standards

Every active trigger deployed to `/opt/floworkos/system/triger/` MUST conform to this structure:

### 1. Dedicated Watchdog Directory:
```text
/opt/floworkos/system/triger/<trigger_name>/
├── trigger.json         <-- Mandatory configuration manifest
├── watcher[.sh|.py|.rs] <-- Executable watcher (ELF `watcher`, `watcher.sh`, `watcher.py`, or `watcher.rs`)
├── .pid                 <-- Generated at runtime: active process ID
└── .last_alert          <-- Generated at runtime: UNIX timestamp of last fired alert
```

### 2. Mandatory Schema: `trigger.json`

```json
{
  "name": "system_telemetry",
  "description": "Active shell watchdog monitoring RAM, swap, and disk thresholds",
  "version": "1.0.0",
  "type": "active",
  "enabled": true,
  "interval_seconds": 15,
  "cooldown_seconds": 300,
  "thresholds": {
    "ram_percent": 90,
    "disk_percent": 92
  },
  "keywords": [
    "memory", "telemetry", "ram_limit", "disk_full", "swap", "system_health"
  ]
}
```

#### Field Specifications:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | **YES** | Unique identifier (`^[a-z0-9_-]+$`). Must match the parent directory name. |
| `description` | String | **YES** | Clear explanation of the physical metrics monitored. |
| `type` | String | **YES** | Must be strictly `"active"`. |
| `enabled` | Boolean | **YES** | Master switch. If `false`, the supervisor will skip this daemon. |
| `interval_seconds` | Integer | **YES** | Polling frequency in seconds (`interval_sec` also used in `kernel_telemetry`; recommended `10`-`30`). |
| `cooldown_seconds` | Integer | **YES** | Minimum seconds between fired alerts to prevent notification spam. |
| `thresholds` | Object | Optional | Metric thresholds triggering the emergency alert. |
| `keywords` | Array | Optional | Related semantic keywords for Formula 5-3-3 correlation. |

### 3. The IPC Signal Protocol: `/tmp/flowork_active_trigger.json`
When a watcher triggers an alert, it must write a valid JSON object matching this schema:

```json
{
  "active": true,
  "source": "system_telemetry",
  "timestamp": 1730761200,
  "telemetry": {
    "ram_percent": 93,
    "disk_percent": 81
  },
  "instruction": "🚨 CRITICAL: High memory pressure detected (RAM 93%). Suspend memory-intensive builds and clean cache before proceeding."
}
```

### 4. Non-Negotiable Operational Invariants:
1. **PID Management:** The watcher must write its PID to `.pid` on startup so `supervisor.py` can monitor its liveness and clean stale files.
2. **Cooldown Enforcement:** The watcher MUST read `.last_alert` and ensure `current_time - last_alert >= cooldown_seconds` before emitting a new alert.
3. **Lightweight Execution:** Watchers must sleep between loops (`sleep 15`). Tight unthrottled infinite loops are strictly prohibited.
4. **Strict English Doctrine:** All instructions, alert messages, and logs must be in clear technical English.

---

## 5. Step-by-Step Tutorial: Authoring a New Active Watchdog

Here is how to author an active watchdog that monitors disk space exhaustion:

### Step 1: Create the Directory
```bash
WATCHER_DIR="/opt/floworkos/system/triger/disk_guard"
mkdir -p "$WATCHER_DIR"
```

### Step 2: Author the Manifest (`trigger.json`)
Create `/opt/floworkos/system/triger/disk_guard/trigger.json`:
```json
{
  "name": "disk_guard",
  "description": "Monitors root partition disk space and alerts when storage drops below 5GB",
  "version": "1.0.0",
  "type": "active",
  "enabled": true,
  "interval_seconds": 30,
  "cooldown_seconds": 600,
  "thresholds": {
    "min_free_mb": 5000
  }
}
```

### Step 3: Author the Executable Script (`watcher.sh`)
Create `/opt/floworkos/system/triger/disk_guard/watcher.sh`:
```bash
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/.pid"
LAST_ALERT="$DIR/.last_alert"
SIGNAL_FILE="/tmp/flowork_active_trigger.json"

echo $$ > "$PID_FILE"

while true; do
  FREE_MB=$(df -m / | awk 'NR==2 {print $4}')
  NOW=$(date +%s)
  LAST=0
  [ -f "$LAST_ALERT" ] && LAST=$(cat "$LAST_ALERT" 2>/dev/null || echo 0)
  DIFF=$((NOW - LAST))

  if [ "$FREE_MB" -le 5000 ] && [ "$DIFF" -ge 600 ]; then
    echo "$NOW" > "$LAST_ALERT"
    cat << JSON > "$SIGNAL_FILE"
{
  "active": true,
  "source": "disk_guard",
  "timestamp": $NOW,
  "telemetry": { "free_mb": $FREE_MB },
  "instruction": "🚨 CRITICAL: Root filesystem storage critically low (${FREE_MB} MB free). Delete stale build artifacts in /tmp and cache before compiling."
}
JSON
    echo "[ACTIVE_TRIGGER:disk_guard] Alert fired: ${FREE_MB} MB free"
  fi

  sleep 30
done
```
Make the script executable:
```bash
chmod +x /opt/floworkos/system/triger/disk_guard/watcher.sh
```

### Step 4: Verification
Test execution directly:
```bash
/opt/floworkos/system/triger/disk_guard/watcher.sh &
sleep 2
cat /opt/floworkos/system/triger/disk_guard/.pid
kill $(cat /opt/floworkos/system/triger/disk_guard/.pid)
```
The watcher starts, writes its PID, and monitors health cleanly with Exit Code 0.

---

## 6. Quality Gate & Acceptance Checklist

Before any active trigger is authorized in `/opt/floworkos/system/triger/`:

- [ ] **Gate 1 (Territory):** Resides strictly in `/opt/floworkos/system/triger/<trigger_name>/`.
- [ ] **Gate 2 (Configuration):** `trigger.json` exists, is valid JSON, declares `type: "active"`, and defines `interval_seconds` and `cooldown_seconds`.
- [ ] **Gate 3 (PID Tracking):** Script records its PID into `.pid` on startup.
- [ ] **Gate 4 (Cooldown Protection):** Implements `.last_alert` state tracking to prevent alert storms.
- [ ] **Gate 5 (Signal Conformance):** Signal payload written to `/tmp/flowork_active_trigger.json` conforms to schema.
- [ ] **Gate 6 (Language):** All instructions and logs written in strict technical English.
- [ ] **Gate 7 (Zero Symlinks):** All files are physical files on disk.
