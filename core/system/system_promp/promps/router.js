#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN DYNAMIC ROUTER & KEYWORD MATCHER
 * Formula 5 - 3 - 3:
 *   - Maximal 5 Tools
 *   - Maximal 3 Skills (List & Path ONLY, mandatory manual read)
 *   - Maximal 3 Passive Trigger Prompts
 * 
 * Enforces Zero-Hallucination Banners & Token Conservation.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

class FloworkRouter {
    constructor() {
        this.toolsDir = '/opt/floworkos/tools';
        this.mcpDir = '/opt/floworkos/mcp';
        this.skillsDirs = [
            '/opt/floworkos/skills',
            path.join(os.homedir() || '', '.flowork', 'skills'),
            '/etc/skel/.flowork/skills'
        ];
        this.triggersDir = '/opt/floworkos/system/system_promp/promps/triggers';
        this.triggersJsonPath = '/opt/floworkos/system/system_promp/promps/triggers.json';

        this.lastKeywordsHash = null;
        this.catalog = null;
        this.catalogTimestamp = 0;
    }

    /**
     * Build or return cached catalog
     */
    getCatalog() {
        const now = Date.now();
        // Refresh catalog every 30 seconds
        if (this.catalog && (now - this.catalogTimestamp < 30000)) {
            return this.catalog;
        }

        const tools = this.loadTools();
        const skills = this.loadSkills();
        const prompts = this.loadPrompts();

        this.catalog = { tools, skills, prompts };
        this.catalogTimestamp = now;
        return this.catalog;
    }

    loadTools() {
        const list = [];
        // 1. Scan /opt/floworkos/tools/
        if (fs.existsSync(this.toolsDir)) {
            try {
                const entries = fs.readdirSync(this.toolsDir, { withFileTypes: true });
                for (const e of entries) {
                    if (!e.isDirectory()) continue;
                    const manifestPath = path.join(this.toolsDir, e.name, 'manifest.json');
                    if (fs.existsSync(manifestPath)) {
                        try {
                            const m = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
                            const triggers = m.triggers || {};
                            const kwList = Array.isArray(triggers.keywords) ? triggers.keywords.join(' ') : '';
                            const text = `${m.name} ${m.description} ${kwList}`.toLowerCase();
                            list.push({
                                name: m.name,
                                description: m.description,
                                activation: m.activation || 'always',
                                triggers: triggers,
                                text
                            });
                        } catch (_) {}
                    }
                }
            } catch (_) {}
        }

        // 2. Add MCP Browser Tools
        const browserTools = [
            { name: "mcp_browser_click", description: "Click DOM element in active browser page" },
            { name: "mcp_browser_navigate_page", description: "Navigate browser URL or reload page" },
            { name: "mcp_browser_take_screenshot", description: "Capture viewport or element screenshot" },
            { name: "mcp_browser_evaluate_script", description: "Execute JavaScript in browser page console" },
            { name: "mcp_browser_fill", description: "Fill form input fields in browser" }
        ];
        for (const bt of browserTools) {
            list.push({
                name: bt.name,
                description: bt.description,
                text: `${bt.name} ${bt.description} browser dom web chrome cdp`.toLowerCase()
            });
        }

        return list;
    }

    loadSkills() {
        const list = [];
        for (const sDir of this.skillsDirs) {
            if (!fs.existsSync(sDir)) continue;
            try {
                const entries = fs.readdirSync(sDir, { withFileTypes: true });
                for (const e of entries) {
                    if (!e.isDirectory()) continue;
                    const skillFile = path.join(sDir, e.name, 'SKILL.md');
                    if (fs.existsSync(skillFile)) {
                        try {
                            const raw = fs.readFileSync(skillFile, 'utf8');
                            // Extract description / frontmatter
                            list.push({
                                name: e.name,
                                path: skillFile,
                                text: `${e.name} ${raw.slice(0, 500)}`.toLowerCase()
                            });
                        } catch (_) {}
                    }
                }
            } catch (_) {}
        }
        return list;
    }

    loadPrompts() {
        const list = [];
        if (fs.existsSync(this.triggersDir)) {
            try {
                const files = fs.readdirSync(this.triggersDir);
                for (const file of files) {
                    if (!file.endsWith('.md')) continue;
                    const fullPath = path.join(this.triggersDir, file);
                    try {
                        const content = fs.readFileSync(fullPath, 'utf8');
                        const id = file.replace('.md', '');
                        list.push({
                            id,
                            title: id.replace(/_/g, ' ').toUpperCase(),
                            file: fullPath,
                            content: content.trim(),
                            text: `${id} ${content}`.toLowerCase()
                        });
                    } catch (_) {}
                }
            } catch (_) {}
        }
        return list;
    }

    /**
     * Compute keyword overlap score
     */
    scoreItem(itemText, keywords, goal, reason = '') {
        let score = 0;
        const normalizedGoal = (typeof goal === 'string' ? goal : '').toLowerCase();
        const normalizedReason = (typeof reason === 'string' ? reason : '').toLowerCase();

        for (const kw of keywords) {
            const k = String(kw).toLowerCase().trim();
            if (!k) continue;
            if (itemText.includes(k)) {
                score += 3;
            }
        }

        // Additional boost if goal mentions item keywords
        if (normalizedGoal) {
            const words = normalizedGoal.split(/\s+/).filter(w => w.length > 3);
            for (const w of words) {
                if (itemText.includes(w)) {
                    score += 1;
                }
            }
        }

        // Additional boost if agent's reason mentions item keywords
        if (normalizedReason) {
            const words = normalizedReason.split(/\s+/).filter(w => w.length > 3);
            for (const w of words) {
                if (itemText.includes(w)) {
                    score += 2;
                }
            }
        }

        return score;
    }

    /**
     * Score tool considering activation and exclude_keywords against keywords, goal, and reason
     */
    scoreTool(tool, keywords, goal, reason = '') {
        const triggers = tool.triggers || {};
        const excludeKeywords = triggers.exclude_keywords || [];
        const combinedContext = `${keywords.join(' ')} ${goal || ''} ${reason || ''}`.toLowerCase();

        // 1. Exclude keywords (Veto: never recommend if excluded in reason or keywords)
        for (const ex of excludeKeywords) {
            const exLower = String(ex).toLowerCase().trim();
            if (exLower && combinedContext.includes(exLower)) {
                return -1;
            }
        }

        // 2. Base scoring
        let score = this.scoreItem(tool.text, keywords, goal, reason);
        if (tool.activation === 'always' && score > 0) {
            score += 1;
        }
        return score;
    }

    /**
     * Match top items according to formula 5-3-3
     */
    match(keywords = [], goal = '', reason = '') {
        const catalog = this.getCatalog();
        const kwList = Array.isArray(keywords) ? keywords : [String(keywords)];

        let lifecycle = null;
        try {
            lifecycle = require('/opt/floworkos/tools/lifecycle_manager.js');
        } catch (_) {}
        const state = lifecycle ? lifecycle.getState() : null;
        const isShort = state?.lastTurn?.isShortResponse;

        // 1. Score Tools (Top 5)
        const scoredTools = catalog.tools.map(t => ({
            ...t,
            score: this.scoreTool(t, kwList, goal, reason)
        })).filter(t => t.score > 0).sort((a, b) => b.score - a.score).slice(0, 5);

        // Fallback default tools if no specific keyword match
        let finalTools = scoredTools.length > 0 ? scoredTools : catalog.tools.slice(0, 5);
        if (isShort && state.activeTools && state.activeTools.length > 0) {
            const retainedTools = catalog.tools.filter(t => state.activeTools.includes(t.name));
            if (retainedTools.length > 0) {
                finalTools = retainedTools.slice(0, 5);
            }
        }

        // 2. Score Skills (Top 3)
        let finalSkills = [];
        if (isShort && state.activeSkills && state.activeSkills.length > 0) {
            finalSkills = catalog.skills.filter(s => state.activeSkills.includes(s.name)).slice(0, 3);
        }
        if (finalSkills.length === 0) {
            const scoredSkills = catalog.skills.map(s => ({
                ...s,
                score: this.scoreItem(s.text, kwList, goal, reason)
            })).filter(s => s.score > 0).sort((a, b) => b.score - a.score).slice(0, 3);
            finalSkills = scoredSkills.length > 0 ? scoredSkills : catalog.skills.slice(0, 3);
        }

        // 3. Score Passive Prompts (Top 3)
        let finalPrompts = [];
        if (isShort && state.activePrompts && state.activePrompts.length > 0) {
            finalPrompts = catalog.prompts.filter(p => state.activePrompts.includes(p.id)).slice(0, 3);
        }
        if (finalPrompts.length === 0) {
            const scoredPrompts = catalog.prompts.map(p => ({
                ...p,
                score: this.scoreItem(p.text, kwList, goal, reason)
            })).filter(p => p.score > 0).sort((a, b) => b.score - a.score).slice(0, 3);
            finalPrompts = scoredPrompts.length > 0 ? scoredPrompts : catalog.prompts.slice(0, 3);
        }

        // Persist active skills & prompts in lifecycle manager
        if (lifecycle) {
            try {
                lifecycle.setActiveSkills(finalSkills.map(s => s.name));
                lifecycle.setActivePrompts(finalPrompts.map(p => p.id));
            } catch (_) {}
        }

        return {
            tools: finalTools,
            skills: finalSkills,
            prompts: finalPrompts
        };
    }

    /**
     * Format into mandatory zero-hallucination banners (Strict English)
     */
    formatBanner(matches) {
        const sections = [];

        // 1. Tools Banner (Max 5)
        if (matches.tools.length > 0) {
            const lines = [
                `[FLOWORK VERIFIED TOOLS — SYSTEM RECOMMENDATIONS]`,
                `⚡ Active sovereign tools matched to your operational goal and keywords:`
            ];
            matches.tools.forEach((t, i) => {
                lines.push(`${i + 1}. \`${t.name}\`: ${t.description.split('\n')[0]}`);
            });
            sections.push(lines.join('\n'));
        }

        // 2. Skills Banner (Max 3, Path ONLY)
        if (matches.skills.length > 0) {
            const lines = [
                `[FLOWORK SOVEREIGN SKILLS — MANUAL INSPECTION REQUIRED]`,
                `⚠️ DO NOT RELY ON OUTDATED PRE-TRAINING DATA!`,
                `The system detected relevant Flowork OS skills for your objective. You MUST read the authoritative instructions file manually using a file reader tool ('read_file') before acting:`,
            ];
            matches.skills.forEach((s, i) => {
                lines.push(`${i + 1}. **${s.name}** -> Path: \`${s.path}\``);
            });
            lines.push(`*(Inspect genuine on-disk files only — never guess or assume skill contents!)*`);
            sections.push(lines.join('\n'));
        }

        // 3. Passive Prompts Banner (Max 3)
        if (matches.prompts.length > 0) {
            const lines = [
                `<flowork_system_directive type="passive_trigger">`,
                `[FLOWORK SYSTEM DIRECTIVE — SYSTEM ORIGINATED, NOT USER]`,
                `🔔 NOTICE: This is an authoritative SYSTEM directive from Flowork OS, NOT from the user.`,
                `This directive is triggered automatically by task keywords and MUST be obeyed with top priority:`
            ];
            matches.prompts.forEach((p, i) => {
                lines.push(`\n--- [DIRECTIVE ${i + 1}: ${p.title}] ---`);
                lines.push(p.content);
            });
            lines.push(`\n</flowork_system_directive>`);
            sections.push(lines.join('\n'));
        }

        return sections.join('\n\n' + '='.repeat(70) + '\n\n');
    }

    /**
     * Main entry point
     */
    route(keywords = [], goal = '', reason = '', force = false) {
        let allKeywords = Array.isArray(keywords) ? [...keywords] : [String(keywords)];
        if (reason && typeof reason === 'string') {
            const reasonWords = reason.toLowerCase().replace(/[^a-z0-9_-]/g, ' ').split(/\s+/).filter(w => w.length > 2);
            allKeywords.push(...reasonWords);
        }
        allKeywords = Array.from(new Set(allKeywords));

        const kwStr = allKeywords.join(',') + '|' + (goal || '') + '|' + (reason || '');
        if (!force && this.lastKeywordsHash === kwStr) {
            return ""; // Deduplicated to save tokens in rapid burst calls
        }
        this.lastKeywordsHash = kwStr;

        const matches = this.match(allKeywords, goal, reason);
        return this.formatBanner(matches);
    }
}

const routerInstance = new FloworkRouter();
module.exports = routerInstance;

// CLI self-test if executed directly
if (require.main === module) {
    const testKeywords = ["linux", "bash", "filesystem", "iso", "build"];
    const testGoal = "Build Flowork OS live ISO and rootfs packaging";
    console.log(routerInstance.route(testKeywords, testGoal, 'Testing packaging'));
}
