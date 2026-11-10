#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — CONTEXT SNIFFER & DYNAMIC TOOL MATCHER
 * Evaluates tool activation based on:
 *   - "always" vs "conditional"
 *   - Keyword triggers vs Exclude keyword negation (strict veto)
 *   - Environmental behaviors (file extensions, active URLs/domains, workspace files)
 */

const fs = require('fs');
const path = require('path');

class ContextSniffer {
    constructor() {
        this.toolsDir = '/opt/floworkos/tools';
        this.cache = new Map();
        this.cacheTimestamp = 0;
    }

    /**
     * Gather current operational context from environment and last state
     */
    sniffContext(cwd = process.cwd(), overridePrompt = null) {
        let lastPrompt = overridePrompt || '';
        let activeUrl = '';

        // 1. Read in-memory intercept state if defined (Fast Path)
        try {
            if (typeof globalFloworkInterceptState !== 'undefined' && globalFloworkInterceptState.activeKeywords) {
                const memGoal = globalFloworkInterceptState.activeGoal || '';
                const memReason = globalFloworkInterceptState.activeReason || '';
                const memKw = (globalFloworkInterceptState.activeKeywords || []).join(' ');
                if (memReason || memKw) {
                    lastPrompt = `${memGoal} ${memReason} ${memKw} ${lastPrompt}`.trim();
                }
            }
        } catch (_) {}

        // 2. Read last active trigger state from /tmp if available
        try {
            if (fs.existsSync('/tmp/flowork_active_trigger.json')) {
                const triggerData = JSON.parse(fs.readFileSync('/tmp/flowork_active_trigger.json', 'utf8'));
                if (!lastPrompt && triggerData.reason) {
                    lastPrompt = `${triggerData.goal || ''} ${triggerData.reason || ''} ${(triggerData.keywords || []).join(' ')}`;
                }
            }
        } catch (_) {}

        // 2. Read active prompt / history from active session if possible
        try {
            if (fs.existsSync('/tmp/flowork_current_prompt.txt')) {
                const currentPrompt = fs.readFileSync('/tmp/flowork_current_prompt.txt', 'utf8').trim();
                if (currentPrompt) {
                    lastPrompt = `${currentPrompt} ${lastPrompt}`;
                }
            }
        } catch (_) {}

        // 3. Detect domains / URLs in prompt
        const urlMatches = lastPrompt.match(/https?:\/\/[^\s/$.?#].[^\s]*/gi) || [];
        const rawDomains = [];
        for (const u of urlMatches) {
            try {
                const parsed = new URL(u);
                rawDomains.push(parsed.hostname.toLowerCase());
            } catch (_) {}
        }

        // Also detect plain domains like youtube.com, github.com in text
        const plainDomainMatches = lastPrompt.match(/\b([a-z0-9-]+(?:\.[a-z0-9-]+)+)\b/gi) || [];
        for (const d of plainDomainMatches) {
            if (d.includes('.') && !d.endsWith('.')) {
                rawDomains.push(d.toLowerCase());
            }
        }
        const activeDomains = Array.from(new Set(rawDomains));

        // 4. Sniff workspace extensions and landmark files
        const activeExtensions = new Set();
        const workspaceFiles = new Set();
        const targetCwd = cwd || process.cwd() || process.env.HOME || '/tmp';

        try {
            if (fs.existsSync(targetCwd)) {
                const entries = fs.readdirSync(targetCwd, { withFileTypes: true });
                for (const e of entries) {
                    if (e.isFile()) {
                        workspaceFiles.add(e.name);
                        const ext = path.extname(e.name).toLowerCase();
                        if (ext) activeExtensions.add(ext);
                    }
                }
            }
        } catch (_) {}

        return {
            text: lastPrompt.toLowerCase(),
            domains: activeDomains,
            extensions: Array.from(activeExtensions),
            files: Array.from(workspaceFiles),
            cwd: targetCwd
        };
    }

    /**
     * Load manifest for a tool
     */
    loadManifest(toolName) {
        const manifestPath = path.join(this.toolsDir, toolName, 'manifest.json');
        if (fs.existsSync(manifestPath)) {
            try {
                return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
            } catch (_) {
                return null;
            }
        }
        return null;
    }

    /**
     * Evaluate if a tool should be active given the context
     * Rule:
     *   1. activation === "always" -> TRUE
     *   2. exclude_keywords hit -> FALSE (Absolute Veto)
     *   3. keywords hit OR behavior hit -> TRUE
     *   4. Else -> FALSE
     */
    isToolActive(toolName, manifest = null, context = null) {
        const m = manifest || this.loadManifest(toolName);
        if (!m) {
            // Default to active if no manifest exists to prevent breaking untracked tools
            return true;
        }

        const ctx = context || this.sniffContext();
        try {
            const lifecycle = require('/opt/floworkos/tools/lifecycle_manager.js');
            return lifecycle.isToolActive(toolName, m, ctx);
        } catch (_) {
            // Fallback to always check if lifecycle manager fails
            return m.activation === 'always';
        }
    }

    /**
     * Check if a tool has an associated SKILL.md and read its prompt content
     */
    getToolSkill(toolName) {
        const candidates = [
            path.join(this.toolsDir, toolName, 'SKILL.md'),
            path.join(this.toolsDir, toolName, 'skill.md'),
            path.join(this.toolsDir, toolName, 'SKILL.MD')
        ];

        for (const p of candidates) {
            if (fs.existsSync(p)) {
                try {
                    const content = fs.readFileSync(p, 'utf8').trim();
                    if (content) {
                        return {
                            path: p,
                            content
                        };
                    }
                } catch (_) {}
            }
        }
        return null;
    }
}

const snifferInstance = new ContextSniffer();
module.exports = snifferInstance;

// CLI test if executed directly
if (require.main === module) {
    const testTool = {
        name: "flowork_web_search",
        activation: "conditional",
        triggers: {
            keywords: ["search", "google", "web", "internet"],
            exclude_keywords: ["offline", "localhost", "127.0.0.1"],
            behavior: {
                domains: ["google.com", "bing.com"]
            }
        }
    };

    const ctx1 = { text: "please search documentation online", domains: ["google.com"], extensions: [], files: [] };
    const ctx2 = { text: "run search on localhost server", domains: ["localhost"], extensions: [], files: [] };
    const ctx3 = { text: "edit this python script", domains: [], extensions: [".py"], files: [] };

    console.log("Test 1 (search online):", snifferInstance.isToolActive("flowork_web_search", testTool, ctx1) ? "ACTIVE (Expected)" : "INACTIVE");
    console.log("Test 2 (localhost with exclude):", snifferInstance.isToolActive("flowork_web_search", testTool, ctx2) ? "ACTIVE" : "INACTIVE (Excluded - Expected)");
    console.log("Test 3 (unrelated python):", snifferInstance.isToolActive("flowork_web_search", testTool, ctx3) ? "ACTIVE" : "INACTIVE (Expected)");
}
