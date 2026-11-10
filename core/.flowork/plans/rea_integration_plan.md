# Implementation Plan: REA (Reverse Engineer Anything) Sovereign Integration

## Objective
Integrate the morluto/rea reverse engineering capabilities into Flowork OS following sovereign architecture standards:
1. Zero Prompt Bloat Tool (/opt/floworkos/tools/rea/): Packaged as a conditional native tool (activated only on RE/binary keywords, 0 tokens when idle) with Node 22 execution runtime.
2. Standard Sovereign Skill (/opt/floworkos/skills/reverse-engineer-anything/): Authoritative operational playbook strictly adhering to /opt/floworkos/skills/README.md and passing lint_skills.js with Exit Code 0.

## Key Files & Context
- /opt/floworkos/tools/rea/manifest.json: Tool schema, conditional triggers, parameters.
- /opt/floworkos/tools/rea/run.js: Executable runner invoking REA CLI under Node 22 runtime with structured JSON stdout.
- /opt/floworkos/tools/rea/SKILL.md: JIT-injected operational directives for the tool.
- /opt/floworkos/skills/reverse-engineer-anything/SKILL.md: Comprehensive skill playbook with 20 keywords, 5 mandatory sections, and security domain classification.
- /opt/floworkos/skills/reverse-engineer-anything/references/: In-depth runtime and artifact references imported from canonical REA docs.

## Implementation Steps

### Phase 1: Native Sovereign Tool (/opt/floworkos/tools/rea/)
1. Create directory /opt/floworkos/tools/rea/.
2. Configure manifest.json with conditional activation, semantic keyword triggers, file extension behavior triggers (.so, .elf, .exe, .apk, .wasm, .bin), and parameter schema (command, target, args).
3. Implement run.js with executable permissions, Node 22 environment invocation, structured JSON stdout, and clean Exit Code 0.
4. Author SKILL.md inside tool directory for JIT injection with YAML frontmatter and 20 keywords.

### Phase 2: Sovereign Skill (/opt/floworkos/skills/reverse-engineer-anything/)
1. Create directory /opt/floworkos/skills/reverse-engineer-anything/ and references/.
2. Copy technical references from REA repository.
3. Draft SKILL.md complying with all quality gates (name, security domain, exactly 20 keywords, mandatory sections: Objective, Prerequisites, Standard Operating Procedure, Verification, Failure Modes).
4. Verify zero symlinks exist.

### Phase 3: Verification & Quality Gates
1. Run node /opt/floworkos/skills/lint_skills.js to verify skill quality gate passes with Exit Code 0.
2. Run discovery schema check: node /opt/floworkos/tools/discovery.js.
3. Run context sniffer check: node /opt/floworkos/tools/context_sniffer.js.
4. Test tool execution with Exit Code 0.
