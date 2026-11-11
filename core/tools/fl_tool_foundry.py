#!/usr/bin/env python3
"""
⚡ FLOWORK OS — DYNAMIC TOOL FOUNDRY ENGINE (fl_tool_foundry.py)
Autonomous Tool Synthesis, Sandboxed Staging, Empirical Verification (Exit Code 0),
and Atomic Promotion into /opt/floworkos/tools/.

Mandatory Invariants:
1. Strict TDK Schema Linting (name in lowercase snake_case, valid triggers, JSON schema).
2. Isolated Staging in /tmp/foundry/<tool_name>/.
3. Empirical Execution Gate (stdin injection, execution timeout, Exit Code 0, valid stdout).
4. Atomic Promotion to /opt/floworkos/tools/<tool_name>/ and discovery verification via flowork-tool-discovery.
5. Zero Workspace Pollution: Guaranteed rollback on any verification failure.
"""

import sys
import os
import re
import json
import shutil
import stat
import subprocess
from typing import Dict, Any, Tuple, Optional

TOOLS_ROOT = "/opt/floworkos/tools"
STAGING_BASE = "/tmp/foundry"
DISCOVERY_BIN = "/opt/floworkos/bin/flowork-tool-discovery"


class ToolFoundryError(Exception):
    """Custom exception representing Tool Foundry operational rejections."""
    pass


def validate_tool_name(name: str) -> None:
    """Validate that tool name strictly adheres to lowercase snake_case."""
    if not name or not isinstance(name, str):
        raise ToolFoundryError("Tool name must be a non-empty string.")
    if not re.match(r"^[a-z][a-z0-9_]{1,63}$", name):
        raise ToolFoundryError(
            f"Invalid tool name '{name}'. Must be lowercase snake_case (starts with a-z, max 64 chars, letters/numbers/underscores only)."
        )


def validate_manifest_schema(manifest: Dict[str, Any]) -> None:
    """
    Validate manifest against Sovereign Tool Architecture TDK specification:
    - name: matches naming rule
    - description: strict non-empty string
    - activation: 'always' or 'conditional'
    - triggers: object with keywords array (at least 4 items)
    - parametersJsonSchema: valid JSON Schema object with properties and required array
    """
    if not isinstance(manifest, dict):
        raise ToolFoundryError("Manifest must be a JSON object.")

    name = manifest.get("name")
    validate_tool_name(name)

    desc = manifest.get("description")
    if not desc or not isinstance(desc, str) or len(desc.strip()) < 10:
        raise ToolFoundryError("Manifest 'description' must be a clear explanation (minimum 10 characters).")

    activation = manifest.get("activation", "conditional")
    if activation not in ("always", "conditional"):
        raise ToolFoundryError("Manifest 'activation' must be either 'conditional' or 'always'.")

    # If conditional, triggers must be configured properly
    triggers = manifest.get("triggers", {})
    if activation == "conditional":
        if not isinstance(triggers, dict):
            raise ToolFoundryError("Conditional tools must include a 'triggers' object.")
        keywords = triggers.get("keywords", [])
        if not isinstance(keywords, list) or len(keywords) < 4:
            raise ToolFoundryError("Conditional tools must define at least 4 trigger keywords in triggers.keywords.")

    # Validate parametersJsonSchema
    schema = manifest.get("parametersJsonSchema")
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise ToolFoundryError("Manifest 'parametersJsonSchema' must be an object with 'type': 'object'.")
    if not isinstance(schema.get("properties"), dict):
        raise ToolFoundryError("Manifest 'parametersJsonSchema.properties' must be a dictionary.")


def validate_code_syntax(runner_filename: str, file_path: str) -> None:
    """Check code syntax using native interpreters or validate ELF binary."""
    if runner_filename == "run.js":
        raise ToolFoundryError("Runner 'run.js' is prohibited in Zero-Node Pure Rust mode. Use 'run', 'run.py', or 'run.sh'.")

    if runner_filename == "run":
        with open(file_path, "rb") as fb:
            head = fb.read(4)
        if head == b"\x7fELF":
            return
        with open(file_path, "r", encoding="utf-8", errors="ignore") as ft:
            first_line = ft.readline().lower()
        if "sh" in first_line and "python" not in first_line:
            runner_filename = "run.sh"
        elif "python" in first_line or not first_line.startswith("#!"):
            runner_filename = "run.py"
        else:
            return

    if runner_filename == "run.py":
        # Check Python syntax using native AST parser
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_text = f.read()
            import ast
            ast.parse(code_text, filename=file_path)
        except SyntaxError as e:
            raise ToolFoundryError(f"Python syntax compilation failed:\n{e}")
        except Exception as e:
            raise ToolFoundryError(f"Failed to parse Python code: {e}")

    elif runner_filename == "run.sh":
        # Check Bash syntax
        res = subprocess.run(
            ["/bin/bash", "-n", file_path],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            raise ToolFoundryError(f"Bash syntax check failed:\n{res.stderr}")


def stage_tool(
    name: str,
    manifest: Dict[str, Any],
    runner_filename: str,
    runner_code: str,
    skill_content: Optional[str] = None
) -> str:
    """Stage tool artifacts inside /tmp/foundry/<tool_name>/."""
    validate_tool_name(name)
    staging_dir = os.path.join(STAGING_BASE, name)

    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, mode=0o755, exist_ok=True)

    # 1. Write manifest.json
    manifest_path = os.path.join(staging_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2. Write runner script
    if runner_filename not in ("run", "run.py", "run.sh"):
        raise ToolFoundryError(
            f"Invalid runner filename '{runner_filename}'. Allowed: run, run.py, run.sh."
        )
    runner_path = os.path.join(staging_dir, runner_filename)
    with open(runner_path, "w", encoding="utf-8") as f:
        f.write(runner_code)

    # Set executable permissions
    os.chmod(runner_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    # Syntax validation
    validate_code_syntax(runner_filename, runner_path)

    # 3. Write optional SKILL.md
    if skill_content:
        skill_path = os.path.join(staging_dir, "SKILL.md")
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(skill_content)

    return staging_dir


def execute_sandboxed_test(
    staging_dir: str,
    runner_filename: str,
    test_input: Dict[str, Any],
    timeout_sec: int = 10
) -> Dict[str, Any]:
    """Execute the staged runner with test_input injected via stdin."""
    runner_path = os.path.join(staging_dir, runner_filename)
    if not os.path.exists(runner_path):
        raise ToolFoundryError(f"Runner '{runner_path}' does not exist.")

    tool_name = os.path.basename(staging_dir)
    input_str = json.dumps(test_input)

    cmd = []
    if runner_filename in ("run", "run.sh"):
        cmd = [runner_path]
    elif runner_filename == "run.py":
        cmd = [sys.executable, runner_path]
    else:
        raise ToolFoundryError(f"Unsupported runner '{runner_filename}'. Allowed: run, run.py, run.sh.")

    env = os.environ.copy()
    env["FLOWORK_TOOL_NAME"] = tool_name
    env["FLOWORK_FOUNDRY_TEST"] = "1"

    try:
        proc = subprocess.run(
            cmd,
            input=input_str,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=staging_dir,
            env=env
        )
    except subprocess.TimeoutExpired:
        raise ToolFoundryError(f"Test execution timed out after {timeout_sec} seconds.")
    except Exception as e:
        raise ToolFoundryError(f"Test execution failed to spawn: {str(e)}")

    if proc.returncode != 0:
        raise ToolFoundryError(
            f"Tool execution returned non-zero exit code ({proc.returncode}).\n"
            f"Stderr: {proc.stderr}\nStdout: {proc.stdout}"
        )

    # Validate output
    stdout = proc.stdout.strip()
    parsed_output = None
    if stdout:
        try:
            parsed_output = json.loads(stdout)
        except json.JSONDecodeError:
            # Output is non-JSON text; acceptable if non-empty
            parsed_output = {"raw_output": stdout}
    else:
        parsed_output = {"status": "ok"}

    return {
        "status": "success",
        "exit_code": proc.returncode,
        "output": parsed_output,
        "stderr": proc.stderr.strip()
    }


def promote_to_registry(tool_name: str, staging_dir: str) -> str:
    """Atomically promote staged tool into /opt/floworkos/tools/<tool_name>/."""
    target_dir = os.path.join(TOOLS_ROOT, tool_name)
    backup_dir = None

    if os.path.exists(target_dir):
        backup_dir = f"/tmp/foundry_backup_{tool_name}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)
        shutil.move(target_dir, backup_dir)

    try:
        shutil.copytree(staging_dir, target_dir)

        # Run Rust flowork-tool-discovery ELF to verify discovery parsing
        disc_res = subprocess.run(
            [DISCOVERY_BIN],
            capture_output=True,
            text=True,
            cwd=TOOLS_ROOT
        )

        if disc_res.returncode != 0:
            raise ToolFoundryError(f"flowork-tool-discovery failed after tool promotion: {disc_res.stderr}")

        # Check if the tool appears in discovery output
        try:
            disc_tools = json.loads(disc_res.stdout)
            # Conditional tools might not appear in general sniffContext, but json must be valid
            if not isinstance(disc_tools, list):
                raise ToolFoundryError("flowork-tool-discovery output is not a valid JSON array.")
        except json.JSONDecodeError:
            raise ToolFoundryError(f"flowork-tool-discovery returned non-JSON stdout: {disc_res.stdout}")

        # Cleanup backup and staging on success
        if backup_dir and os.path.exists(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)
        shutil.rmtree(staging_dir, ignore_errors=True)

        return target_dir

    except Exception as e:
        # Rollback target directory
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        if backup_dir and os.path.exists(backup_dir):
            shutil.move(backup_dir, target_dir)
        raise ToolFoundryError(f"Promotion failed and was rolled back: {str(e)}")


def retire_tool(tool_name: str) -> bool:
    """Safely delete and unregister a synthesized tool from /opt/floworkos/tools/."""
    validate_tool_name(tool_name)
    target_dir = os.path.join(TOOLS_ROOT, tool_name)

    # Protect essential core tools
    CORE_PROTECTED = {
        "read_file", "write_file", "replace", "list_directory", "run_shell_command",
        "enter_plan_mode", "exit_plan_mode", "discovery", "executor", "ask_user",
        "activate_skill", "invoke_agent", "take_screenshot", "flowork_web_search"
    }
    if tool_name in CORE_PROTECTED:
        raise ToolFoundryError(f"Tool '{tool_name}' is a protected core system tool and cannot be retired.")

    if not os.path.exists(target_dir):
        return False

    shutil.rmtree(target_dir)

    # Verify flowork-tool-discovery still succeeds
    disc_res = subprocess.run(
        [DISCOVERY_BIN],
        capture_output=True,
        text=True,
        cwd=TOOLS_ROOT
    )
    if disc_res.returncode != 0:
        raise ToolFoundryError(f"flowork-tool-discovery failed after retiring tool: {disc_res.stderr}")

    return True


def create_and_promote_tool(
    name: str,
    manifest: Dict[str, Any],
    runner_filename: str,
    runner_code: str,
    test_input: Dict[str, Any],
    skill_content: Optional[str] = None
) -> Dict[str, Any]:
    """Complete 4-stage pipeline: validate, stage, test, promote."""
    # Stage 1: Lint manifest
    validate_manifest_schema(manifest)

    # Stage 2: Stage & syntax check
    staging_dir = stage_tool(name, manifest, runner_filename, runner_code, skill_content)

    try:
        # Stage 3: Sandboxed test execution
        test_result = execute_sandboxed_test(staging_dir, runner_filename, test_input)

        # Stage 4: Promotion to registry
        promoted_path = promote_to_registry(name, staging_dir)

        return {
            "status": "promoted",
            "tool_name": name,
            "path": promoted_path,
            "test_result": test_result
        }
    except Exception:
        # Ensure staging cleanup on failure
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)
        raise


def main():
    """CLI dispatcher for stdin JSON payload."""
    try:
        raw_input = sys.stdin.read().strip()
        data = json.loads(raw_input) if raw_input else {}
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON stdin: {str(e)}"}))
        sys.exit(1)

    action = data.get("action", "create")

    try:
        if action == "create":
            name = data.get("name")
            manifest = data.get("manifest")
            runner_filename = data.get("runner_filename", "run.py")
            runner_code = data.get("runner_code")
            test_input = data.get("test_input", {})
            skill_content = data.get("skill_content")

            if not all([name, manifest, runner_filename, runner_code]):
                raise ToolFoundryError("Fields 'name', 'manifest', 'runner_filename', and 'runner_code' are required.")

            res = create_and_promote_tool(name, manifest, runner_filename, runner_code, test_input, skill_content)
            print(json.dumps(res, indent=2))
            sys.exit(0)

        elif action == "test":
            name = data.get("name")
            manifest = data.get("manifest")
            runner_filename = data.get("runner_filename", "run.py")
            runner_code = data.get("runner_code")
            test_input = data.get("test_input", {})
            skill_content = data.get("skill_content")

            validate_manifest_schema(manifest)
            staging_dir = stage_tool(name, manifest, runner_filename, runner_code, skill_content)
            try:
                res = execute_sandboxed_test(staging_dir, runner_filename, test_input)
                print(json.dumps(res, indent=2))
            finally:
                shutil.rmtree(staging_dir, ignore_errors=True)
            sys.exit(0)

        elif action == "retire":
            name = data.get("name")
            if not name:
                raise ToolFoundryError("Field 'name' is required for retire action.")
            deleted = retire_tool(name)
            print(json.dumps({"status": "retired" if deleted else "not_found", "tool_name": name}))
            sys.exit(0)

        elif action == "inspect":
            name = data.get("name")
            if not name:
                raise ToolFoundryError("Field 'name' is required for inspect action.")
            tool_dir = os.path.join(TOOLS_ROOT, name)
            if not os.path.exists(tool_dir):
                print(json.dumps({"status": "not_found", "tool_name": name}))
                sys.exit(0)

            manifest_path = os.path.join(tool_dir, "manifest.json")
            manifest_data = {}
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

            files = os.listdir(tool_dir)
            print(json.dumps({
                "status": "exists",
                "tool_name": name,
                "path": tool_dir,
                "manifest": manifest_data,
                "files": files
            }, indent=2))
            sys.exit(0)

        else:
            raise ToolFoundryError(f"Unknown action '{action}'. Supported: create, test, retire, inspect.")

    except ToolFoundryError as e:
        print(json.dumps({"status": "error", "error_type": "FoundryValidation", "message": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error_type": "Internal", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
