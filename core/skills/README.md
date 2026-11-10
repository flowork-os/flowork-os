# ⚡ FLOWORK OS — SOVEREIGN SKILL SPECIFICATION & AUTHORING STANDARD

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/skills/` (mirrored at `/home/mrflow/floworkos/skills/`)  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

## 1. Executive Philosophy: Tools vs Skills vs Prompts vs Brain

To maintain absolute non-dualism and prevent architectural degeneration, Flowork OS establishes a rigid separation of concerns across runtime capabilities:

| Component | Physical Path | Primary Role | Analogy | Token Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **TOOL** | `/opt/floworkos/tools/<tool_name>/` | Atomic technical execution instrument. Performs one specific task without procedural bias. | Hands & Scalpels | Minimal (Schema only) |
| **SKILL** | `/opt/floworkos/skills/<skill_name>/` | Standard Operating Procedure (SOP), multi-step domain workflows, best practices, and recovery playbooks. | Technical Playbook | Zero initially (Loaded via Path only) |
| **PROMPT** | `/opt/floworkos/system/system_promp/promps/` | Sovereign doctrines, core moral invariants, and behavioral directives. | Conscience & Persona | Constant (Loaded in preamble/triggers) |

### The Golden Rule of Skills
> **"Skills teach the agent HOW to accomplish complex domain missions using available tools. A skill must NEVER be an executable binary itself; rather, it coordinates tools, scripts, and verification procedures into a deterministic, zero-error outcome."**

---

## 2. Directory Anatomy

Every skill in Flowork OS is an isolated, self-contained directory under `/opt/floworkos/skills/`:

```text
/opt/floworkos/skills/<skill-name>/
├── SKILL.md              [MANDATORY] Primary SOP document with YAML frontmatter
├── scripts/              [OPTIONAL] Supporting automation scripts (.sh, .js, .py)
├── examples/             [OPTIONAL] Concrete reference configurations & inputs
└── resources/            [OPTIONAL] JSON schemas, checklists, and static assets
```

### Constraints:
1. **Directory Naming:** Lowercase alphanumeric with hyphens only (`kebab-case`). No spaces or underscores (e.g., `iso-builder`, `network-hardener`).
2. **Zero Symlinks:** Absolute prohibition of symlinks inside `/opt/floworkos/skills/`. Every skill directory and file must be physical.
3. **No Hidden Logic:** All operational steps must be explicitly documented in `SKILL.md`.

---

## 3. Mandatory YAML Frontmatter Specification

Every `SKILL.md` MUST start with a YAML frontmatter block enclosed between triple dashes (`---`). The parser validates these fields strictly:

```yaml
---
name: flowork-iso-builder
description: Comprehensive procedural playbook for bootstrapping, packaging, and verifying bootable Flowork OS standalone live ISO images with zero Cinnamon remnants.
domain: os_doctrine
keywords:
  - flowork
  - livecd
  - iso
  - squashfs
  - grub
  - chroot
  - initramfs
  - debootstrap
  - kernel
  - bootable
  - sovereign
  - packaging
  - rootfs
  - binary
  - installer
  - calamares
  - xorriso
  - remaster
  - deployment
  - verification
author: Flowork Architecture Board
version: 1.0.0
---
```

### Detailed Field Requirements:

| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | `^[a-z0-9-]+$` | Must exactly match the parent directory name. |
| `description` | String | 100 - 300 characters | Precise trigger condition explaining *when* this skill should be mobilized by the router. |
| `domain` | String | Enum | One of: `os_doctrine`, `browser`, `shell_system`, `code_dev`, `database`, `security`, `network`. |
| `keywords` | Array | **EXACTLY 20 KEYWORDS** | 20 English semantic keywords required for Formula 5-3-3 scoring. |
| `author` | String | Non-empty | Creator authority. |
| `version` | String | SemVer (`X.Y.Z`) | Versioning of the SOP playbook. |

### The 20-Keyword Doctrine
Why **EXACTLY 20 keywords**?
The Flowork Dynamic Tool Router (`/opt/floworkos/prompts/router.js`) uses semantic keyword vectors to rank skills under the Formula 5-3-3 constraint (Max 3 active skills per turn). 
- Fewer than 20 keywords leads to false negatives during domain matching.
- More than 20 keywords causes keyword pollution and false positive skill activations.
- Exact uniformity ensures balanced mathematical scoring across the entire catalog.

---

## 4. Anatomy of `SKILL.md` Content

The body of `SKILL.md` must be written in strict, technical English and must follow the standardized 6-section structure:

```markdown
# [Skill Title in English]

## 1. Executive Summary & Objective
Define the operational mission, boundaries, and expected end state of this capability.

## 2. Prerequisites & Tool Dependencies
List all necessary Flowork OS tools (`run_shell_command`, `read_file`, etc.) and system utilities (`xorriso`, `chroot`, `debootstrap`).

## 3. Standard Operating Procedure (SOP)
Step-by-step procedural workflows. Each step must provide explicit terminal commands, parameters, and rationale.

### Step 1: Environment Preparation
...
### Step 2: Core Execution
...
### Step 3: Artifact Assembly
...

## 4. Verification & Quality Gates (Exit Code 0)
Mandatory empirical terminal checks to prove the operation succeeded without relying on assumptions. Every claim must have an empirical command returning Exit Code 0.

## 5. Failure Modes, Edge Cases & Recovery
Common pitfalls, known error messages, and immediate mitigation recipes.

## 6. Prohibitions & Anti-Patterns
Explicit rules on what the agent MUST NEVER do during this workflow (e.g., touching `@lock` lines, leaving temporary build files behind).
```

---

## 5. Lifecycle Management & Formula 5-3-3 Integration

Flowork OS enforces the **Option C Contextual Retention & Lifecycle Engine**:

### 1. Zero Token Bloat (Manual Inspection Required)
When the router matches a skill, it **NEVER** dumps the entire content of `SKILL.md` into the model's context. Instead, it emits the authoritative recommendation banner:

```text
[FLOWORK SOVEREIGN SKILLS — MANUAL INSPECTION REQUIRED]
⚠️ DO NOT RELY ON OUTDATED PRE-TRAINING DATA!
The system detected relevant Flowork OS skills for your objective. You MUST read the authoritative instructions file manually using a file reader tool ('read_file') before acting:
1. **flowork-iso-builder** -> Path: `/opt/floworkos/skills/flowork-iso-builder/SKILL.md`
*(Inspect genuine on-disk files only — never guess or assume skill contents!)*
```

The agent is forced to use `read_file` to inspect the SOP JIT (Just-In-Time) before taking action.

### 2. Short-Response Carryover
When the user sends a terse confirmative reply ($\le 4$ words: *"ok"*, *"lanjut"*, *"gas"*, *"yes proceed"*, *"nomor 2"*), active skills from the previous turn are automatically carried over in `/tmp/flowork_lifecycle_state.json`. The agent preserves its operational context without amnesia.

### 3. Domain Shift Decommissioning
When the user transitions to a distinct new domain (e.g. from `browser` $\rightarrow$ `os_doctrine`), the previous domain's skills slide out, and up to 3 new relevant skills slide in.

---

## 6. Step-by-Step Tutorial: Authoring a Sovereign Skill

Follow this verified protocol to author a new skill:

### Step 1: Create the Skill Workspace
```bash
SKILL_NAME="flowork-package-auditor"
mkdir -p /opt/floworkos/skills/${SKILL_NAME}/scripts
mkdir -p /opt/floworkos/skills/${SKILL_NAME}/examples
```

### Step 2: Draft `SKILL.md` with Exactly 20 Keywords
Create `/opt/floworkos/skills/${SKILL_NAME}/SKILL.md`:
```markdown
---
name: flowork-package-auditor
description: Procedural playbook for auditing debian packages and system binaries to detect and eliminate upstream Cinnamon remnants and non-sovereign dependencies.
domain: os_doctrine
keywords:
  - dpkg
  - apt
  - debian
  - package
  - audit
  - inspection
  - dependency
  - sovereign
  - cinnamon
  - remnants
  - cleanup
  - binary
  - verification
  - repository
  - system
  - library
  - security
  - compliance
  - hardening
  - telemetry
author: Flowork Architecture Board
version: 1.0.0
---

# Flowork Package Auditor SOP

## 1. Executive Summary & Objective
Audit all installed system packages to ensure zero Cinnamon desktop components compromise Flowork OS sovereignty.

## 2. Prerequisites & Tool Dependencies
- Tool: `run_shell_command`
- Packages: `dpkg`, `apt`, `grep`

## 3. Standard Operating Procedure (SOP)
### Step 1: Query Installed Desktop Packages
```bash
dpkg -l | grep -iE 'cinnamon|nemo|muffin'
```

### Step 2: Isolate Foreign Packages
...
```

### Step 3: Validate Skill Formatting & Keywords
Run the Flowork Skill Linter:
```bash
node /opt/floworkos/skills/lint_skills.js
```
The linter will verify that:
- Frontmatter is valid YAML.
- `name` matches directory name.
- `keywords` contains **EXACTLY 20** valid non-empty English strings.
- All mandatory markdown sections exist.

---

## 7. Quality Gate & Acceptance Checklist

Before any skill is authorized in `/opt/floworkos/skills/`, it must pass all 6 verification gates:

- [ ] **Gate 1 (Isolation):** Skill resides in its own isolated directory under `/opt/floworkos/skills/<name>/`.
- [ ] **Gate 2 (Frontmatter):** Frontmatter contains valid `name`, `description`, `domain`, and **EXACTLY 20 English keywords**.
- [ ] **Gate 3 (Language):** All content is in strict technical English (zero Indonesian in prompts, docs, or logs).
- [ ] **Gate 4 (Structure):** Contains all 6 mandatory sections (Summary, Prerequisites, SOP, Verification, Failure Modes, Prohibitions).
- [ ] **Gate 5 (Zero Symlinks):** No symlinks anywhere inside the skill directory.
- [ ] **Gate 6 (Empirical Verification):** Every SOP step and verification command is tested and produces **Exit Code 0**.
