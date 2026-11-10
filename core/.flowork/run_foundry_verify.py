#!/usr/bin/env python3
"""
⚡ FLOWORK OS — FOUNDRY TEST EXECUTION RUNNER
Directly executes the verification suite and logs results to .flowork/foundry_test_result.json
"""
import sys
import os
import json
import subprocess
import shutil

ENGINE_PATH = "/opt/floworkos/tools/fl_tool_foundry.py"
DISCOVERY_PATH = "/opt/floworkos/tools/discovery.js"
TEST_TOOL_NAME = "fl_autotest_digest"
TOOLS_ROOT = "/opt/floworkos/tools"
RESULT_LOG = "/opt/floworkos/.flowork/foundry_test_result.json"

def run_foundry(payload: dict) -> tuple:
    proc = subprocess.run(
        [sys.executable, ENGINE_PATH],
        input=json.dumps(payload),
        capture_output=True,
        text=True
    )
    data = {}
    try:
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except Exception:
        pass
    return proc.returncode, data, proc.stderr

def run_all_tests():
    report = {"tests": [], "success": False}

    # Test 1: Creation and Promotion
    t1_manifest = {
        "name": TEST_TOOL_NAME,
        "description": "Calculates SHA256 digest of input text payload for verification.",
        "activation": "conditional",
        "triggers": {
            "keywords": ["digest", "hash", "sha256", "checksum"],
            "exclude_keywords": ["unsupported"]
        },
        "parametersJsonSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to hash."}
            },
            "required": ["text"]
        }
    }
    t1_runner = """#!/usr/bin/env python3
import sys, json, hashlib
def main():
    try:
        data = json.loads(sys.stdin.read() or '{}')
        text = data.get('text', '')
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        print(json.dumps({'status': 'ok', 'sha256': digest}))
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
if __name__ == '__main__':
    main()
"""
    code, out, err = run_foundry({
        "action": "create",
        "name": TEST_TOOL_NAME,
        "manifest": t1_manifest,
        "runner_filename": "run.py",
        "runner_code": t1_runner,
        "test_input": {"text": "sovereign_verify"}
    })
    t1_pass = (code == 0 and out.get("status") == "promoted" and os.path.exists(os.path.join(TOOLS_ROOT, TEST_TOOL_NAME)))
    report["tests"].append({"name": "test_1_create_and_promote", "passed": t1_pass, "code": code, "output": out, "err": err})

    # Test 2: discovery.js parse
    node_bin = shutil.which("node") or "/usr/bin/node"
    proc_disc = subprocess.run([node_bin, DISCOVERY_PATH], capture_output=True, text=True, cwd=TOOLS_ROOT)
    t2_pass = (proc_disc.returncode == 0)
    report["tests"].append({"name": "test_2_discovery_js_parse", "passed": t2_pass, "code": proc_disc.returncode, "err": proc_disc.stderr})

    # Test 3: Intentional Failure & Zero Workspace Pollution
    bad_manifest = {
        "name": "fl_bad_tool",
        "description": "Fails intentional syntax check.",
        "activation": "conditional",
        "triggers": {"keywords": ["bad", "fail", "test", "syntax"]},
        "parametersJsonSchema": {"type": "object", "properties": {}}
    }
    code_bad, out_bad, err_bad = run_foundry({
        "action": "create",
        "name": "fl_bad_tool",
        "manifest": bad_manifest,
        "runner_filename": "run.py",
        "runner_code": "def broken(:\n pass\n",
        "test_input": {}
    })
    t3_pass = (code_bad != 0 and not os.path.exists(os.path.join(TOOLS_ROOT, "fl_bad_tool")))
    report["tests"].append({"name": "test_3_failure_rollback", "passed": t3_pass, "code": code_bad, "output": out_bad})

    # Test 4: Retire Tool
    code_ret, out_ret, err_ret = run_foundry({"action": "retire", "name": TEST_TOOL_NAME})
    t4_pass = (code_ret == 0 and not os.path.exists(os.path.join(TOOLS_ROOT, TEST_TOOL_NAME)))
    report["tests"].append({"name": "test_4_retire_tool", "passed": t4_pass, "code": code_ret, "output": out_ret})

    report["success"] = all(t["passed"] for t in report["tests"])

    with open(RESULT_LOG, "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    rep = run_all_tests()
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["success"] else 1)
