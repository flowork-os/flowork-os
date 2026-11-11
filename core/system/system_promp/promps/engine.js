/**
 * ⚡ FLOWORK SOVEREIGN PROMPT & TRIGGER ENGINE
 * Decoupled living doctrine loader for MrFlow CLI (Flowork OS).
 * Zero hardcoded prompt logic inside CLI binary.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

class FloworkPromptEngine {
    constructor() {
        this.systemPromptsDir = '/opt/floworkos/system/system_promp/promps';
        this.systemPassiveDir = '/opt/floworkos/system/system_promp';
        this.userPromptsDir = path.join(os.homedir() || process.env.HOME || '/tmp', '.flowork', 'prompts');

        this.assembleSystemPrompt = this.assembleSystemPrompt.bind(this);
        this.getCompressionPrompt = this.getCompressionPrompt.bind(this);
        this.evaluatePassiveTriggers = this.evaluatePassiveTriggers.bind(this);
        this.getSearchDirs = this.getSearchDirs.bind(this);
    }

    getSearchDirs() {
        const dirs = [];
        if (process.env.FLOWORK_PROMPTS_DIR && fs.existsSync(process.env.FLOWORK_PROMPTS_DIR)) {
            dirs.push(process.env.FLOWORK_PROMPTS_DIR);
        }
        if (fs.existsSync(this.systemPromptsDir)) {
            dirs.push(this.systemPromptsDir);
        }
        if (fs.existsSync(this.userPromptsDir) && this.userPromptsDir !== this.systemPromptsDir) {
            dirs.push(this.userPromptsDir);
        }
        return dirs;
    }

    isGitRepository(directory) {
        try {
            let currentDir = path.resolve(directory);
            while (true) {
                const gitDir = path.join(currentDir, '.git');
                if (fs.existsSync(gitDir)) {
                    return true;
                }
                const parentDir = path.dirname(currentDir);
                if (parentDir === currentDir) {
                    break;
                }
                currentDir = parentDir;
            }
        } catch (_) {}
        return false;
    }

    evaluatePassiveTriggers(context, cwd) {
        const triggers = [];
        const config = context?.config;
        const toolRegistry = context?.toolRegistry;

        // Context state extraction
        let interactive = true;
        let approvalMode = 'default';
        let enabledToolNames = new Set();
        let skillsCount = 0;
        let trackerDir = undefined;
        let sandboxMode = 'outside';

        if (config) {
            try {
                if (typeof config.isInteractive === 'function') {
                    interactive = config.isInteractive();
                }
            } catch (_) {}
            try {
                if (typeof config.getApprovalMode === 'function') {
                    approvalMode = (config.getApprovalMode() || 'default').toLowerCase();
                }
            } catch (_) {}
            try {
                if (typeof config.getSkillManager === 'function') {
                    const sm = config.getSkillManager();
                    if (sm && typeof sm.getSkills === 'function') {
                        skillsCount = (sm.getSkills() || []).length;
                    }
                }
            } catch (_) {}
            try {
                if (typeof config.isTrackerEnabled === 'function' && config.isTrackerEnabled()) {
                    if (config.storage && typeof config.storage.getProjectTempTrackerDir === 'function') {
                        trackerDir = config.storage.getProjectTempTrackerDir();
                    }
                }
            } catch (_) {}
        }

        if (toolRegistry && typeof toolRegistry.getAllToolNames === 'function') {
            try {
                enabledToolNames = new Set(toolRegistry.getAllToolNames());
            } catch (_) {}
        }

        // Sandbox detection
        if (process.env.SANDBOX === 'sandbox-exec') sandboxMode = 'macos-seatbelt';
        else if (process.env.SANDBOX) sandboxMode = 'generic';

        // Check search dirs for trigger files
        const searchDirs = this.getSearchDirs();
        const findTriggerFile = (relFile) => {
            for (const d of searchDirs) {
                const full = path.join(d, relFile);
                if (fs.existsSync(full)) return full;
            }
            return null;
        };

        const loadTrigger = (relFile) => {
            const f = findTriggerFile(relFile);
            if (f) {
                try {
                    const c = fs.readFileSync(f, 'utf8').trim();
                    if (c) return c;
                } catch (_) {}
            }
            return null;
        };

        // 1. Workflow Triggers: Primary vs Planning
        if (approvalMode === 'plan') {
            const t = loadTrigger('triggers/planning_workflow.md');
            if (t) triggers.push(t);
        } else {
            const t = loadTrigger('triggers/primary_workflows.md');
            if (t) triggers.push(t);
        }

        // 2. Sovereign / Autonomous Mode
        const isSovereignMode = approvalMode === 'sovereign';
        if (isSovereignMode && interactive) {
            const t = loadTrigger('triggers/interactive_sovereign.md');
            if (t) triggers.push(t);
        }

        // 3. Git Repository Trigger
        if (this.isGitRepository(cwd)) {
            const t = loadTrigger('triggers/git_repo.md');
            if (t) triggers.push(t);
        }

        // 4. Sub-Agents Orchestration
        if (enabledToolNames.has('agent') || enabledToolNames.has('subagent')) {
            const t = loadTrigger('triggers/subagents.md');
            if (t) triggers.push(t);
        }

        // 5. Skills Trigger (Dynamic discovery fallback)
        const hasLocalSkills = fs.existsSync(path.join(cwd, '.flowork', 'skills')) ||
                               fs.existsSync(path.join(os.homedir() || '', '.flowork', 'skills')) ||
                               fs.existsSync(path.join(cwd, '.gemini', 'skills')) ||
                               fs.existsSync(path.join(os.homedir() || '', '.gemini', 'skills'));
        if (skillsCount > 0 || hasLocalSkills) {
            const t = loadTrigger('triggers/skills.md');
            if (t) triggers.push(t);
        }

        // 6. Task Tracker Trigger (Dynamic directory discovery)
        const hasLocalTracker = fs.existsSync(path.join(cwd, '.flowork', 'tracker')) ||
                                fs.existsSync(path.join(cwd, '.gemini', 'tracker'));
        if (trackerDir || hasLocalTracker) {
            const t = loadTrigger('triggers/task_tracker.md');
            if (t) triggers.push(t);
        }

        // 7. Sandbox Mode Trigger
        if (sandboxMode !== 'outside') {
            const t = loadTrigger('triggers/sandbox.md');
            if (t) triggers.push(t);
        }

        // 8. Hook Context Trigger
        if (process.env.FLOWORK_HOOK_CONTEXT || process.env.HOOK_CONTEXT) {
            const t = loadTrigger('triggers/hook_context.md');
            if (t) triggers.push(t);
        }

        // 9. Workspace File Context Triggers - DELEGATED TO JIT DYNAMIC ROUTER
        // To preserve Zero-Bloat Invariant, specialized doctrines (Rust, ISO, PHP)
        // are routed Just-In-Time via router.js and keywords, eliminating base prompt bloat.

        // 10. Modular Engineering & Operational Triggers (JIT)
        const isEditingTools = enabledToolNames.has('write_file') || enabledToolNames.has('replace') || enabledToolNames.has('replace_file_content');
        if (isEditingTools) {
            const t = loadTrigger('triggers/code_engineering.md');
            if (t) triggers.push(t);
        }

        const isSearchingTools = enabledToolNames.has('grep_search') || enabledToolNames.has('glob') || enabledToolNames.has('read_many_files');
        if (isSearchingTools) {
            const t = loadTrigger('triggers/search_efficiency.md');
            if (t) triggers.push(t);
        }

        const hasMemoryFiles = fs.existsSync(path.join(cwd, 'FLOWORK.md')) || fs.existsSync(path.join(cwd, '.flowork', 'MEMORY.md'));
        if (hasMemoryFiles) {
            const t = loadTrigger('triggers/memory_routing.md');
            if (t) triggers.push(t);
        }

        if (process.env.FLOWORK_MCP_ACTIVE || enabledToolNames.has('list_mcp_resources') || enabledToolNames.has('read_mcp_resource')) {
            const t = loadTrigger('triggers/untrusted_context.md');
            if (t) triggers.push(t);
        }

        if (process.env.FLOWORK_REFACTOR_ACTIVE) {
            const t = loadTrigger('triggers/anti_zombie.md');
            if (t) triggers.push(t);
        }

        // 11. External System Passive Triggers (/opt/floworkos/system/system_promp/)
        const registryFile = path.join(this.systemPassiveDir, 'triggers.json');
        if (fs.existsSync(registryFile)) {
            try {
                const reg = JSON.parse(fs.readFileSync(registryFile, 'utf8'));
                if (Array.isArray(reg)) {
                    for (const item of reg) {
                        if (!item.enabled) continue;
                        const ruleRel = item.rule;
                        if (!ruleRel) continue;

                        let execPath = null;
                        if (ruleRel.endsWith('.rs')) {
                            const baseName = path.basename(ruleRel, '.rs');
                            const binPath = path.join(this.systemPassiveDir, 'rules', '.bin', baseName);
                            if (fs.existsSync(binPath)) execPath = binPath;
                        } else if (ruleRel.endsWith('.sh')) {
                            const shPath = path.join(this.systemPassiveDir, ruleRel);
                            if (fs.existsSync(shPath)) execPath = shPath;
                        }

                        if (execPath) {
                            try {
                                const evalRes = spawnSync(execPath, [], {
                                    env: { ...process.env, FLOWORK_CWD: cwd },
                                    timeout: 25
                                });
                                if (evalRes.status === 0 && item.prompt) {
                                    const promptPath = path.join(this.systemPassiveDir, item.prompt);
                                    if (fs.existsSync(promptPath)) {
                                        const pContent = fs.readFileSync(promptPath, 'utf8').trim();
                                        if (pContent) {
                                            triggers.push(`<PASSIVE_ENVIRONMENTAL_INSTINCT id="${item.id}">\n${pContent}\n</PASSIVE_ENVIRONMENTAL_INSTINCT>`);
                                        }
                                    }
                                }
                            } catch (_) {}
                        }
                    }
                }
            } catch (_) {}
        }

        // 11. Active Watchdog Signals (/tmp/flowork_active_trigger.json)
        const signalFile = '/tmp/flowork_active_trigger.json';
        if (fs.existsSync(signalFile)) {
            try {
                const signal = JSON.parse(fs.readFileSync(signalFile, 'utf8'));
                if (signal && signal.active && signal.instruction) {
                    triggers.push(`\n# 🚨 ACTIVE WATCHDOG SIGNAL [${signal.source || 'SYSTEM'}]\n${signal.instruction}\n`);
                }
            } catch (_) {}
        }

        return triggers;
    }

    assembleSystemPrompt(context, userMemory, interactiveOverride, topicUpdateNarrationOverride) {
        const parts = [];
        const baseFiles = ['00_preamble.md', '01_core_mandates.md', '02_operational_guidelines.md'];

        const searchDirs = this.getSearchDirs();
        for (const bf of baseFiles) {
            for (const dir of searchDirs) {
                const filePath = path.join(dir, bf);
                if (fs.existsSync(filePath)) {
                    try {
                        const content = fs.readFileSync(filePath, 'utf8').trim();
                        if (content) {
                            parts.push(content);
                            break;
                        }
                    } catch (err) {
                        console.warn(`[PromptEngine] Warning reading ${filePath}:`, err.message);
                    }
                }
            }
        }

        // Dynamic passive triggers
        const cwd = context?.config?.getProjectRoot?.() || process.cwd();
        const triggers = this.evaluatePassiveTriggers(context, cwd);
        if (triggers.length > 0) {
            parts.push('\n---\n# ⚡ CONTEXTUAL PASSIVE & ACTIVE TRIGGERS INJECTED:\n\n' + triggers.join('\n\n'));
        }

        if (parts.length === 0) {
            parts.push('# 👑 Flowork OS Sovereign AI Agent\nYou are MrFlow, the sovereign autonomous agent for Flowork OS.');
        }

        return parts.join('\n\n---\n\n');
    }

    getCompressionPrompt(context) {
        for (const dir of this.getSearchDirs()) {
            const p = path.join(dir, 'triggers', 'compression.md');
            if (fs.existsSync(p)) {
                try {
                    return fs.readFileSync(p, 'utf8').trim();
                } catch (_) {}
            }
        }
        return 'Compress the conversation history while preserving key decisions, file modifications, and pending tasks.';
    }
}

module.exports = new FloworkPromptEngine();
