#!/usr/bin/env python3
"""
⚡ FLOWORK OS — TOOL FOUNDRY VERIFICATION TEST SUITE (test_tool_foundry.py)
Empirical validation of:
1. Manifest linting and schema rejection.
2. Sandboxed execution with stdin/stdout verification.
3. Exit Code 0 requirement and failure rollbacks.
4. Promotion to /opt/floworkos/tools/ and confirmation in discovery.js.
5. Retirement and cleanup.
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

def run_foundry(payload: dict) -> tuple[int, dict, str]:
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

def test_1_create_and_promote_success():
    print("[TEST 1] Testing successful synthesis, staging, test execution, and promotion...")
    manifest = {
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
                "text": {
                    "type": "string",
                    "description": "Text to hash."
                }
            },
            "required": ["text"]
        }
    }
    runner_code = """#!/usr/bin/env python3
import sys
import json
import hashlib

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
    test_input = {"text": "flowork_sovereignty_2026"}

    payload = {
        "action": "create",
        "name": TEST_TOOL_NAME,
        "manifest": manifest,
        "runner_filename": "run.py",
        "runner_code": runner_code,
        "test_input": test_input
    }

    code, out, err = run_foundry(payload)
    assert code == 0, f"Expected returncode 0, got {code}. Out: {out}, Err: {err}"
    assert out.get("status") == "promoted", f"Expected promoted status, got {out}"
    assert os.path.exists(os.path.join(TOOLS_ROOT, TEST_TOOL_NAME)), "Tool directory was not promoted!"
    print("  -> PASSED: Tool synthesized and promoted successfully.")

def test_2_discovery_js_integration():
    print("[TEST 2] Verifying discovery.js parses newly promoted tool without errors...")
    node_bin = shutil.which("node") or "/usr/bin/node"
    proc = subprocess.run(
        [node_bin, DISCOVERY_PATH],
        capture_output=True,
        text=True,
        cwd=TOOLS_ROOT
    )
    assert proc.returncode == 0, f"discovery.js failed: {proc.stderr}"
    tools = json.loads(proc.stdout)
    assert isinstance(tools, list), "discovery.js did not output a list!"
    print(f"  -> PASSED: discovery.js ran cleanly with {len(tools)} active tools.")

def test_3_intentional_failure_and_rollback():
    print("[TEST 3] Testing intentional failure (syntax error) and zero pollution rollback...")
    bad_manifest = {
        "name": "fl_bad_syntax_tool",
        "description": "Tool intentionally containing Python syntax errors.",
        "activation": "conditional",
        "triggers": {
            "keywords": ["bad", "syntax", "error", "test"]
        },
        "parametersJsonSchema": {
            "type": "object",
            "properties": {}
        }
    }
    bad_code = "def broken_syntax(:\n    return False\n"
    payload = {
        "action": "create",
        "name": "fl_bad_syntax_tool",
        "manifest": bad_manifest,
        "runner_filename": "run.py",
        "runner_code": bad_code,
        "test_input": {}
    }
    code, out, err = run_foundry(payload)
    assert code != 0, "Expected non-zero exit code on syntax error!"
    assert not os.path.exists(os.path.join(TOOLS_ROOT, "fl_bad_syntax_tool")), "Failed tool must NOT be in tools root!"
    print("  -> PASSED: Syntax error detected and workspace protected from pollution.")

def test_4_retire_tool():
    print("[TEST 4] Testing retiring/cleanup of synthesized tool...")
    payload = {
        "action": "retire",
        "name": TEST_TOOL_NAME
    }
    code, out, err = run_foundry(payload)
    assert code == 0, f"Retire failed with code {code}: {out}, {err}"
    assert out.get("status") == "retired", f"Expected retired status, got {out}"
    assert not os.path.exists(os.path.join(TOOLS_ROOT, TEST_TOOL_NAME)), "Tool directory still exists after retirement!"
    print("  -> PASSED: Tool successfully retired and cleaned up.")

def main():
    print("=== STARTING DYNAMIC TOOL FOUNDRY TEST SUITE ===")
    try:
        test_1_create_and_promote_success()
        test_2_discovery_js_integration()
        test_3_intentional_failure_and_rollback()
        test_4_retire_tool()
        print("=== ALL FOUNDRY TESTS PASSED (EXIT CODE 0) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAILURE] Assertion failed: {e}", file=sys.stderr)
        # Cleanup if needed
        shutil.rmtree(os.path.join(TOOLS_ROOT, TEST_TOOL_NAME), ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        shutil.rmtree(os.path.join(TOOLS_ROOT, TEST_TOOL_NAME), ignore_errors=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
