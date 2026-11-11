#!/usr/bin/env python3
"""
👑 FLOWORK OS — COMPREHENSIVE EVOLUTION QC SUITE
Validates all implemented subsystems:
1. Auto-Update Dev Mode Invariant
2. Track 1: Cross-App Neural Pipeline (flowork-pipe & flowork-neural-bus)
3. Track 2: Instant App Remix Engine (flowpkg remix)
4. Track 3: FlowFS Multimodal Screen Memory (flowfs_core & flowfs-search --screen)
5. Architectural Knowledge Crystallization (.fl_brain records)
"""

import os
import sys
import json
import time
import subprocess
import urllib.request

VENV_PYTHON = "/opt/floworkos/apps/camoufox/venv/bin/python3"
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

PASSED_COUNT = 0
FAILED_COUNT = 0

def log_test(test_id, name, success, details=""):
    global PASSED_COUNT, FAILED_COUNT
    status_icon = "✓ PASS" if success else "❌ FAIL"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}[{status_icon}]{reset} [{test_id}] {name}")
    if details:
        for line in details.strip().splitlines():
            print(f"       {line}")
    if success:
        PASSED_COUNT += 1
    else:
        FAILED_COUNT += 1

print("\n" + "="*80)
print("👑 FLOWORK OS — SOVEREIGN SUBSYSTEM QUALITY CONTROL (QC) RUNNER")
print("="*80)

# -----------------------------------------------------------------------------
# TEST 1: Auto-Update Dev Mode Safeguard
# -----------------------------------------------------------------------------
try:
    landmark = "/opt/floworkos/flowork.dev"
    exists = os.path.isfile(landmark)
    if not exists:
        log_test("QC-01", "Auto-Update Dev Mode Landmark", False, "Missing /opt/floworkos/flowork.dev")
    else:
        res = subprocess.run(["/opt/floworkos/bin/flowork-update"], capture_output=True, text=True)
        is_inhibited = "DEV MODE ACTIVE" in (res.stdout + res.stderr) and res.returncode == 0
        log_test("QC-01", "Auto-Update Dev Mode Landmark", is_inhibited, f"Exit code: {res.returncode}, Inhibited: {is_inhibited}")
except Exception as e:
    log_test("QC-01", "Auto-Update Dev Mode Landmark", False, str(e))

# -----------------------------------------------------------------------------
# TEST 2: Syntax, ELF & AST Validation
# -----------------------------------------------------------------------------
try:
    bus_res = subprocess.run(["/opt/floworkos/bin/flowork-neural-bus", "--check"], capture_output=True, text=True)
    pipe_res = subprocess.run([VENV_PYTHON, "-c", "import ast; ast.parse(open('/opt/floworkos/bin/flowork-pipe').read())"], capture_output=True, text=True)
    flowpkg_res = subprocess.run([VENV_PYTHON, "-c", "import ast; ast.parse(open('/opt/floworkos/bin/flowpkg').read())"], capture_output=True, text=True)
    flowfs_res = subprocess.run([VENV_PYTHON, "-c", "import ast; ast.parse(open('/opt/floworkos/connector/flowfs_core.py').read())"], capture_output=True, text=True)
    
    all_syntax = (bus_res.returncode == 0 and pipe_res.returncode == 0 and flowpkg_res.returncode == 0 and flowfs_res.returncode == 0)
    details = f"Rust Neural Bus: {bus_res.returncode == 0}, flowork-pipe: {pipe_res.returncode == 0}, flowpkg: {flowpkg_res.returncode == 0}, flowfs_core: {flowfs_res.returncode == 0}"
    log_test("QC-02", "Binary Self-Check and AST Integrity", all_syntax, details)
except Exception as e:
    log_test("QC-02", "Binary Self-Check and AST Integrity", False, str(e))

# -----------------------------------------------------------------------------
# TEST 3: Track 1 - Neural Bus Chained Execution & Agentic Pipe
# -----------------------------------------------------------------------------
test_bus_proc = None
mock_bin_dir = "/tmp/flowork_qc_bin"
try:
    test_port = 18099
    env = os.environ.copy()
    env["FLOWORK_BUS_PORT"] = str(test_port)
    env["FLOWORK_BUS_URL"] = f"http://127.0.0.1:{test_port}"
    
    test_bus_proc = subprocess.Popen(["/opt/floworkos/bin/flowork-neural-bus"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    
    # Check bus health
    health_req = urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/bus/health", timeout=3)
    health_data = json.loads(health_req.read().decode("utf-8"))
    bus_ok = health_data.get("status") == "ok"
    
    # Run mock pipe chaining test
    os.makedirs(mock_bin_dir, exist_ok=True)
    with open(f"{mock_bin_dir}/qc_step_a", "w") as f:
        f.write("#!/bin/sh\necho '{\"status\": \"ok\", \"file\": \"/tmp/test.wav\", \"text\": \"sample\"}'\n")
    os.chmod(f"{mock_bin_dir}/qc_step_a", 0o755)
    
    with open(f"{mock_bin_dir}/qc_step_b", "w") as f:
        f.write("#!/bin/sh\necho '{\"status\": \"ok\", \"final\": \"done\", \"received_file\": \"'$2'\"}'\n")
    os.chmod(f"{mock_bin_dir}/qc_step_b", 0o755)
    
    env["PATH"] = f"{mock_bin_dir}:" + env.get("PATH", "")
    
    pipe_cmd = ["python3", "/opt/floworkos/bin/flowork-pipe", "--json", "qc_step_a::run | qc_step_b::run --input {file}"]
    pipe_exec = subprocess.run(pipe_cmd, env=env, capture_output=True, text=True)
    pipe_out = json.loads(pipe_exec.stdout) if pipe_exec.returncode == 0 else {}
    
    chain_ok = (bus_ok and pipe_exec.returncode == 0 and pipe_out.get("status") == "ok" and pipe_out.get("stages_completed") == 2)
    log_test("QC-03", "Track 1: Neural Bus Chained Payload Pipeline", chain_ok, f"Stages completed: {pipe_out.get('stages_completed')}, Exit Code: {pipe_exec.returncode}")
except Exception as e:
    log_test("QC-03", "Track 1: Neural Bus Chained Payload Pipeline", False, str(e))
finally:
    if test_bus_proc:
        test_bus_proc.terminate()
        try:
            test_bus_proc.wait(timeout=3)
        except Exception:
            test_bus_proc.kill()
            test_bus_proc.wait()
    import shutil as _shutil
    _shutil.rmtree(mock_bin_dir, ignore_errors=True)

# -----------------------------------------------------------------------------
# TEST 4: Track 2 - App Remix Engine (flowpkg remix)
# -----------------------------------------------------------------------------
try:
    remix_inspect = subprocess.run([VENV_PYTHON, "/opt/floworkos/bin/flowpkg", "remix", "crypto-radar", "--inspect"], capture_output=True, text=True)
    inspect_ok = remix_inspect.returncode == 0 and "REMIX APPLICATION STUDIO" in remix_inspect.stdout and "ui/index.html" in remix_inspect.stdout
    
    remix_prompt = subprocess.run([VENV_PYTHON, "/opt/floworkos/bin/flowpkg", "remix", "crypto-radar", "--prompt", "Automated QC Test Prompt"], capture_output=True, text=True)
    prompt_ok = remix_prompt.returncode == 0 and "Recorded remix directive" in remix_prompt.stdout
    
    remix_ok = inspect_ok and prompt_ok
    log_test("QC-04", "Track 2: App Remix Engine (flowpkg remix)", remix_ok, f"Inspect Exit: {remix_inspect.returncode}, Prompt Exit: {remix_prompt.returncode}")
except Exception as e:
    log_test("QC-04", "Track 2: App Remix Engine (flowpkg remix)", False, str(e))

# -----------------------------------------------------------------------------
# TEST 5: Track 3 - FlowFS Multimodal Screen Memory
# -----------------------------------------------------------------------------
try:
    # 1. Index sample test screen memory
    index_cmd = [VENV_PYTHON, "-c", """
import sys; sys.path.insert(0, '/opt/floworkos/connector'); import flowfs_core
res = flowfs_core.index_screen_capture('/opt/floworkos/screenshots/ambient_20261109_205839.png', window_title='QC Active Window Studio', app_class='Studio', text='Unit test screen context memory sample')
print(res.get('status'))
"""]
    idx_run = subprocess.run(index_cmd, capture_output=True, text=True)
    idx_ok = idx_run.returncode == 0 and "indexed" in idx_run.stdout

    # 2. Search screen memory via flowfs-search
    search_cmd = ["/opt/floworkos/bin/flowfs-search", "--screen", "Window Studio", "--json"]
    search_run = subprocess.run(search_cmd, capture_output=True, text=True)
    search_json = json.loads(search_run.stdout) if search_run.returncode == 0 else {}
    results = search_json.get("results", [])
    
    search_ok = (idx_ok and search_run.returncode == 0 and len(results) > 0 and results[0].get("similarity", 0) > 0.0)
    details = f"Indexed: {idx_ok}, Matches Found: {len(results)}, Top Match: {results[0].get('window_title') if results else 'None'}"
    log_test("QC-05", "Track 3: FlowFS Screen Memory Vector Search", search_ok, details)
except Exception as e:
    log_test("QC-05", "Track 3: FlowFS Screen Memory Vector Search", False, str(e))

# -----------------------------------------------------------------------------
# TEST 6: Knowledge Crystallization (.fl_brain records)
# -----------------------------------------------------------------------------
try:
    f1 = "/opt/floworkos/.fl_brain/cross_app_neural_pipeline.md"
    f2 = "/opt/floworkos/.fl_brain/remix_and_screen_memory.md"
    f1_ok = os.path.isfile(f1) and os.path.getsize(f1) > 200
    f2_ok = os.path.isfile(f2) and os.path.getsize(f2) > 200
    brain_ok = f1_ok and f2_ok
    log_test("QC-06", "Knowledge Crystallization (.fl_brain)", brain_ok, f"Pipeline record: {f1_ok}, Remix & Memory record: {f2_ok}")
except Exception as e:
    log_test("QC-06", "Knowledge Crystallization (.fl_brain)", False, str(e))

# -----------------------------------------------------------------------------
# TEST 7: Pillar 3 - Autonomous Crash Sentinel Loop
# -----------------------------------------------------------------------------
try:
    daemon_bin = "/opt/floworkos/bin/flowork-sentinel-daemon"
    audit_res = subprocess.run([VENV_PYTHON, daemon_bin, "--audit"], capture_output=True, text=True)
    audit_json = json.loads(audit_res.stdout) if audit_res.returncode == 0 else {}
    audit_ok = (audit_res.returncode == 0 and "components" in audit_json and "kernel_traps" in audit_json["components"])

    sim_dir = "/tmp/flowork_crashes"
    os.makedirs(sim_dir, exist_ok=True)
    test_incident = {
        "app": "crypto-radar",
        "pid": "77777",
        "signal": "SIGSEGV",
        "simulated": True,
        "detail": "QC automated test incident"
    }
    tmp_crash_file = f"{sim_dir}/.qc_test_crash.json.tmp"
    final_crash_file = f"{sim_dir}/qc_test_crash.json"
    with open(tmp_crash_file, "w") as f:
        json.dump(test_incident, f)
    os.replace(tmp_crash_file, final_crash_file)

    dry_env = os.environ.copy()
    dry_env["FLOWORK_SENTINEL_DRY_RUN"] = "1"
    heal_res = subprocess.run([VENV_PYTHON, daemon_bin, "--heal", "--dry-run"], env=dry_env, capture_output=True, text=True)
    heal_json = json.loads(heal_res.stdout) if heal_res.returncode == 0 else {}
    heal_ok = (heal_res.returncode == 0 and "actions_taken" in heal_json)

    if os.path.exists(final_crash_file):
        os.remove(final_crash_file)

    sentinel_ok = audit_ok and heal_ok
    log_test("QC-07", "Pillar 3: Autonomous Crash Sentinel Loop", sentinel_ok, f"Audit OK: {audit_ok}, Heal OK: {heal_ok}")
except Exception as e:
    log_test("QC-07", "Pillar 3: Autonomous Crash Sentinel Loop", False, str(e))

# -----------------------------------------------------------------------------
# TEST 8: Pillar 4 - Embedded Offline SLM & Air-Gapped Mode
# -----------------------------------------------------------------------------
try:
    slm_bin = "/opt/floworkos/bin/flowork-slm"
    res_remix = subprocess.run([VENV_PYTHON, slm_bin, "remix crypto-radar", "--json"], capture_output=True, text=True)
    json_remix = json.loads(res_remix.stdout) if res_remix.returncode == 0 else {}
    ok_remix = (res_remix.returncode == 0 and json_remix.get("success") is True and len(json_remix.get("tool_traces", [])) > 0)

    res_screen = subprocess.run([VENV_PYTHON, slm_bin, "cari layar Orbit", "--json"], capture_output=True, text=True)
    json_screen = json.loads(res_screen.stdout) if res_screen.returncode == 0 else {}
    ok_screen = (res_screen.returncode == 0 and json_screen.get("success") is True)

    slm_ok = ok_remix and ok_screen
    log_test("QC-08", "Pillar 4: Embedded Offline SLM & Air-Gapped Mode", slm_ok, f"Remix Intent: {ok_remix}, Screen Intent: {ok_screen}")
except Exception as e:
    log_test("QC-08", "Pillar 4: Embedded Offline SLM & Air-Gapped Mode", False, str(e))

print("="*80)
print(f"📊 QC FINAL SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED (TOTAL: {PASSED_COUNT + FAILED_COUNT})")
print("="*80 + "\n")

if FAILED_COUNT > 0:
    sys.exit(1)
sys.exit(0)
