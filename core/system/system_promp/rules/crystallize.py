#!/usr/bin/env python3
"""
⚡ FLOWORK OS — AUTONOMOUS KNOWLEDGE CRYSTALLIZATION & STAGING GATE
Pure Sovereign Closed-Loop Learning Engine (Idea #1 Implementation)
Compiles, tests, and promotes incident-specific passive Rust rules with zero-trust safety.
"""

import os
import sys
import json
import time
import subprocess

RULES_DIR = "/opt/floworkos/system/system_promp/rules"
BIN_DIR = os.path.join(RULES_DIR, ".bin")
STAGED_DIR = os.path.join(RULES_DIR, "staged")
PROMPTS_DIR = "/opt/floworkos/system/system_promp/promps/triggers"
TRIGGERS_JSON = "/opt/floworkos/system/system_promp/triggers.json"

RUST_TEMPLATE = """use std::env;
use std::process::exit;

fn main() {{
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();
    let target = env::var("FLOWORK_TARGET_FILE").unwrap_or_default().to_lowercase();

    // Event matches
    if events.contains("{rule_id}") {{
        exit(0);
    }}

    // Target file matches
    if target.contains("{rule_id}") {{
        exit(0);
    }}

    // Dynamic keyword triggers
    let keywords = {keywords_rust_array};
    for kw in &keywords {{
        if msg.contains(kw) {{
            exit(0);
        }}
    }}

    // Quiescent: 0 token cost, inactive
    exit(1);
}}
"""

def crystallize_rule(incident_id, title, keywords, prompt_content):
    clean_id = incident_id.strip().lower().replace(" ", "_").replace("-", "_")
    if not clean_id.startswith("auto_"):
        clean_id = f"auto_{clean_id}"

    rule_rs_filename = f"{clean_id}.rs"
    staged_rs_path = os.path.join(STAGED_DIR, rule_rs_filename)
    final_rs_path = os.path.join(RULES_DIR, rule_rs_filename)
    temp_bin = f"/tmp/{clean_id}.test_bin"
    final_bin = os.path.join(BIN_DIR, clean_id)
    prompt_filename = f"{clean_id}.md"
    prompt_path = os.path.join(PROMPTS_DIR, prompt_filename)

    print(f"🏛️ [CRYSTALLIZATION] INITIATING STAGED RULE GATE: {clean_id}")
    print(f"  Title   : {title}")
    print(f"  Keywords: {keywords}")

    # 1. Format keywords into Rust array
    keywords_clean = [k.strip().lower() for k in keywords if k.strip()]
    rust_kw_str = "[" + ", ".join([f'"{k}"' for k in keywords_clean]) + "]"
    
    # 2. Write staged Rust source
    rs_source = RUST_TEMPLATE.format(
        rule_id=clean_id,
        keywords_rust_array=rust_kw_str
    )
    with open(staged_rs_path, "w") as f:
        f.write(rs_source)

    # 3. Write staged Prompt markdown
    with open(prompt_path, "w") as f:
        f.write(prompt_content.strip() + "\n")

    # 4. Zero-Trust Compilation Gate via rustc
    print("  Step 1: Compiling Rust rule in sandbox...")
    compile_res = subprocess.run(
        ["rustc", "-O", staged_rs_path, "-o", temp_bin],
        capture_output=True,
        text=True
    )
    if compile_res.returncode != 0:
        print(f"  [ERROR] rustc compilation failed: {compile_res.stderr}")
        return False, f"rustc compilation failed: {compile_res.stderr}"

    # 5. Staged Mock Simulation Gate
    print("  Step 2: Executing positive & negative regression tests...")
    # Positive Test: message contains first keyword -> MUST exit 0
    test_kw = keywords_clean[0] if keywords_clean else clean_id
    pos_env = dict(os.environ, FLOWORK_USER_MSG=f"Please help fix {test_kw} issue")
    pos_res = subprocess.run([temp_bin], env=pos_env)
    if pos_res.returncode != 0:
        print(f"  [ERROR] Positive test failed: expected exit 0, got {pos_res.returncode}")
        return False, "Positive trigger test failed"

    # Negative Test: message does NOT contain keyword -> MUST exit 1 (quiescent)
    neg_env = dict(os.environ, FLOWORK_USER_MSG="Everything is completely normal and idle")
    neg_res = subprocess.run([temp_bin], env=neg_env)
    if neg_res.returncode != 1:
        print(f"  [ERROR] Negative test failed: expected quiescent exit 1, got {neg_res.returncode}")
        return False, "Negative quiescent test failed"

    # 6. Check for duplicate ID in triggers.json
    print("  Step 3: Checking triggers registry integrity...")
    try:
        with open(TRIGGERS_JSON, "r") as f:
            triggers_data = json.load(f)
    except Exception:
        triggers_data = []

    for item in triggers_data:
        if item.get("id") == clean_id:
            print(f"  [WARN] Trigger ID {clean_id} already exists. Updating in-place.")
            triggers_data.remove(item)
            break

    # 7. Promote binary and update registry
    print("  Step 4: Promoting verified binary to .bin/ production...")
    import shutil
    shutil.move(temp_bin, final_bin)
    os.chmod(final_bin, 0o755)
    
    # Save permanent source in rules/
    with open(final_rs_path, "w") as f:
        f.write(rs_source)

    new_trigger = {
        "id": clean_id,
        "name": title,
        "enabled": True,
        "scope": "universal_all",
        "rule": f"rules/{rule_rs_filename}",
        "prompt": f"promps/triggers/{prompt_filename}"
    }
    triggers_data.append(new_trigger)

    with open(TRIGGERS_JSON, "w") as f:
        json.dump(triggers_data, f, indent=2)

    # 8. Synchronize with DSL triggers matrix (promps/triggers.json)
    dsl_triggers_path = "/opt/floworkos/system/system_promp/promps/triggers.json"
    try:
        if os.path.exists(dsl_triggers_path):
            with open(dsl_triggers_path, "r") as f:
                dsl_data = json.load(f)
            passive_list = dsl_data.get("passive_triggers", [])
            for item in list(passive_list):
                if item.get("id") == clean_id:
                    passive_list.remove(item)
                    break
            kw_quoted = ", ".join([f"'{k}'" for k in keywords_clean])
            dsl_entry = {
                "id": clean_id,
                "file": f"triggers/{prompt_filename}",
                "rule": title,
                "condition": f"hasKeywords([{kw_quoted}])"
            }
            passive_list.append(dsl_entry)
            dsl_data["passive_triggers"] = passive_list
            with open(dsl_triggers_path, "w") as f:
                json.dump(dsl_data, f, indent=2)
            print(f"  ✓ DSL MATRIX SYNCED: {clean_id} registered into promps/triggers.json")
    except Exception as e:
        print(f"  [WARN] Failed to sync DSL matrix: {e}")

    print(f"  ✓ STATE LOCKED: {clean_id} promoted to production (.bin/{clean_id}) with Exit Code 0.")
    return True, "Success"

if __name__ == "__main__":
    if len(sys.argv) < 5:
        # Self-test invocation
        print("Usage: crystallize.py <id> <title> <comma_separated_keywords> <prompt_text>")
        print("Running self-test crystallization...")
        test_id = "ebpf_psi_stall"
        test_title = "eBPF Kernel Memory Pressure Stall Sentinel"
        test_kws = ["psi_stall", "kernel_pressure", "memory_choke", "psi_alert"]
        test_prompt = """# eBPF Kernel Memory Pressure Stall Sentinel
When PSI memory stalls or page-fault spikes exceed critical threshold:
1. Identify high memory consumers without killing PIDs.
2. Recommend cgroup quota throttling or cache dropping.
3. Keep system quiescent if memory pressure normalizes."""
        ok, msg = crystallize_rule(test_id, test_title, test_kws, test_prompt)
        sys.exit(0 if ok else 1)
    else:
        i_id = sys.argv[1]
        i_title = sys.argv[2]
        i_kws = [k.strip() for k in sys.argv[3].split(",")]
        i_prompt = sys.argv[4]
        ok, msg = crystallize_rule(i_id, i_title, i_kws, i_prompt)
        sys.exit(0 if ok else 1)
