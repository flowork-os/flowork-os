---
name: skillevaluator
slash_command: skillevaluator
description: Run static, rubric, security, and live agent benchmark evaluations using NVIDIA SkillEvaluator CLI to score skill quality, discoverability, and lift.
domain: code_dev
keywords:
  - nvidia
  - skillevaluator
  - benchmark
  - validation
  - quality
  - security
  - staticanalysis
  - agent
  - evaluation
  - lift
  - rubric
  - testing
  - telemetry
  - grading
  - audit
  - inspection
  - scoring
  - linting
  - devops
  - sandboxing
author: NVIDIA / Flowork Architecture Board
version: 1.0.1
---

# NVIDIA SkillEvaluator SOP

## 1. Executive Summary & Objective
SkillEvaluator provides automated benchmark scoring and validation for agent skills across three hierarchical tiers:
1. **Tier 1 (Static Analysis & Rubric)**: Validates directory structure, AST safety, PII detection, security vulnerabilities, and quality metrics (Correctness, Discoverability, Reliability, Efficiency).
2. **Tier 2 (Deduplication)**: Identifies semantic overlap and redundant instruction sets within and across skill collections using text embeddings.
3. **Tier 3 (Live Agent Evaluation)**: Benchmarks real agent execution (with vs. without skill) under isolated sandboxes to compute Skill Lift, pass@k, and discoverability trajectories.

## 2. Prerequisites & Tool Dependencies
- **CLI Executable**: `/usr/local/bin/skillevaluator` (configured with Python 3.12+ under `/opt/floworkos/apps/skillevaluator/venv`).
- **Core Tools**: `run_shell_command`, `read_file`, `write_file`.
- **Keyless Execution**: Commands like `quality-check`, `security-scan`, and `tier1 --no-llm` run keyless without external model dependencies.
- **LLM Provider (Tier 2/3 & Rubric)**: Requires `SKILL_EVAL_LLM_PROVIDER` and corresponding credentials (e.g., `NVIDIA_API_KEY` from https://build.nvidia.com or local endpoint via `openai-compatible`).

## 3. Standard Operating Procedure (SOP)

### Step 1: Health & Readiness Check
Verify CLI readiness and scanner dependencies:
```bash
skillevaluator health-check --tier 1
```

### Step 2: Keyless Tier 1 Quality Audit
Execute static quality checks on target skill directory:
```bash
skillevaluator quality-check /opt/floworkos/skills/<target-skill>
```
For full static verification without external LLM calls:
```bash
skillevaluator tier1 /opt/floworkos/skills/<target-skill> --no-llm
```

### Step 3: Security & PII Scan
Perform dedicated credential leak and security audits:
```bash
skillevaluator security-scan /opt/floworkos/skills/<target-skill>
skillevaluator pii-scan /opt/floworkos/skills/<target-skill>
```

### Step 4: Collection Deduplication (Tier 2)
Detect overlapping directives across skills:
```bash
skillevaluator similarity-check /opt/floworkos/skills/
```

### Step 5: Test Case Evaluation & Validation
Validate `<skill-dir>/evals/evals.json` against reference schemas:
```bash
skillevaluator tier3 validate /opt/floworkos/skills/<target-skill> --strict
```

### Command Matrix
| User Goal | Command | Dependencies |
| :--- | :--- | :--- |
| Keyless Quality Score | `skillevaluator quality-check <skill-dir>` | Local CLI |
| Static Gate for Single Skill | `skillevaluator tier1 <skill-dir> --no-llm` | Local Scanners |
| Static Gate + LLM Rubric | `skillevaluator tier1 <skill-dir>` | Provider API Key |
| Security / PII Scan Only | `skillevaluator security-scan <skill-dir>` | SkillSpector |
| Internal Redundancy (Tier 2) | `skillevaluator tier2 <skill-dir>` | Embeddings Provider |
| Collection Overlap | `skillevaluator similarity-check <skills-dir>` | Embeddings Provider |
| Live Agent Benchmark (Tier 3) | `skillevaluator tier3 <skill-dir>` | Provider + Agent Sandbox |

## 4. Verification & Quality Gates (Exit Code 0)
1. **Exit Code Conventions**:
   - `0`: Success, all active gate criteria satisfied.
   - `1`: Gate failure, critical security finding, or incomplete evaluation.
   - `2`: CLI usage syntax error or invalid argument flags.
2. **Quality Passing Standard**:
   - Quality score >= 70 (Grade C or above) with zero HIGH or CRITICAL security findings.
3. **Publication Eligibility**:
   - Static passing results indicate `Publication eligibility: Incomplete` until Tier 2 and Tier 3 benchmarks are executed with positive Skill Lift (+0.05).

## 5. Failure Modes, Edge Cases & Recovery
- **Missing CLI**: If `skillevaluator` is unavailable, ensure `/opt/floworkos/apps/skillevaluator/venv/bin` is intact and `/usr/local/bin/skillevaluator` wrapper exists.
- **Scanner Missing**: Run `skillevaluator health-check --tier 1` to identify missing binary scanners.
- **Provider Key Absent**: When LLM calls fail with missing provider, switch to keyless flags (`--no-llm`) or configure `SKILL_EVAL_LLM_PROVIDER`.
- **Inconclusive Activation**: In Tier 3 evaluations, if the agent fails to invoke the skill, refine `description` keywords and explicit trigger prompts in `<skill-dir>/evals/evals.json`.

## 6. Prohibitions & Anti-Patterns
- Never log, print, or expose provider API keys (`NVIDIA_API_KEY`, etc.) in CLI commands, shell history, or outputs.
- Never interpret a high quality grade (A or B) as passing if security findings are present.
- Never invent test cases or benchmark metrics without empirical execution records.
- Never run blanket evaluations on untrusted third-party skills outside isolated sandbox containers.
