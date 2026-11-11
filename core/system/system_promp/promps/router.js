#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN DYNAMIC ROUTER & ZERO-BLOAT TOKEN MATCHER
 * Enforces Zero-Bloat Invariant:
 *   - Uses exact whole-token Set matching (never substring "includes").
 *   - Filters common conversational noise words.
 *   - Completely silent (0 token waste) on irrelevant turns.
 *   - Maximum 3 Prompts, 3 Skills, 5 Tools ONLY on true relevance.
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

const STOP_WORDS = new Set([
    "the", "and", "for", "with", "from", "check", "status", "test", "routine",
    "saying", "just", "date", "time", "file", "path", "true", "false", "item",
    "name", "type", "open", "read", "view", "edit", "make", "help", "exec"
]);

class FloworkRouter {
    constructor() {
        this.toolsDir = "/opt/floworkos/tools";
        this.skillsDirs = [
            "/opt/floworkos/skills",
            path.join(os.homedir() || "", ".flowork", "skills"),
            "/etc/skel/.flowork/skills"
        ];
        this.triggersDir = "/opt/floworkos/system/system_promp/promps/triggers";
        this.triggersJsonPath = "/opt/floworkos/system/system_promp/promps/triggers.json";

        this.lastKeywordsHash = null;
        this.catalog = null;
        this.catalogTimestamp = 0;
    }

    getCatalog() {
        const now = Date.now();
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

    tokenize(text) {
        return new Set(String(text || "").toLowerCase().split(/[^a-z0-9_-]+/).filter(w => w.length >= 3 && !STOP_WORDS.has(w)));
    }

    loadTools() {
        const list = [];
        if (fs.existsSync(this.toolsDir)) {
            try {
                const entries = fs.readdirSync(this.toolsDir, { withFileTypes: true });
                for (const e of entries) {
                    if (!e.isDirectory()) continue;
                    const manifestPath = path.join(this.toolsDir, e.name, "manifest.json");
                    if (fs.existsSync(manifestPath)) {
                        try {
                            const m = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
                            const triggers = m.triggers || {};
                            const kwList = Array.isArray(triggers.keywords) ? triggers.keywords.join(" ") : "";
                            const raw = `${m.name} ${kwList}`;
                            list.push({
                                name: m.name,
                                description: m.description,
                                activation: m.activation || "conditional",
                                triggers: triggers,
                                tokenSet: this.tokenize(raw)
                            });
                        } catch (_) {}
                    }
                }
            } catch (_) {}
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
                    const skillFile = path.join(sDir, e.name, "SKILL.md");
                    if (fs.existsSync(skillFile)) {
                        try {
                            const raw = fs.readFileSync(skillFile, "utf8");
                            let kwText = "";
                            const m = raw.match(/keywords:\s*\[(.*?)\]/);
                            if (m && m[1]) kwText = m[1].replace(/["\']/g, "");
                            list.push({
                                name: e.name,
                                path: skillFile,
                                tokenSet: this.tokenize(`${e.name} ${kwText}`)
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
        let triggersConfig = [];
        if (fs.existsSync(this.triggersJsonPath)) {
            try {
                const data = JSON.parse(fs.readFileSync(this.triggersJsonPath, "utf8"));
                triggersConfig = data.passive_triggers || [];
            } catch (_) {}
        }

        for (const pt of triggersConfig) {
            const fullPath = path.join("/opt/floworkos/system/system_promp/promps", pt.file);
            if (!fs.existsSync(fullPath)) continue;

            try {
                const content = fs.readFileSync(fullPath, "utf8");
                const cond = pt.condition || "";
                
                // Extract explicit quoted tokens from condition
                const extracted = [];
                const quotedMatches = cond.match(/"([^"]+)"/g) || [];
                for (const q of quotedMatches) {
                    const clean = q.replace(/"/g, "").toLowerCase().trim();
                    if (clean && !clean.startsWith("*")) {
                        extracted.push(clean);
                    }
                }

                const raw = `${pt.id} ${extracted.join(" ")}`;
                list.push({
                    id: pt.id,
                    title: pt.id.replace(/_/g, " ").toUpperCase(),
                    file: fullPath,
                    content: content.trim(),
                    tokenSet: this.tokenize(raw)
                });
            } catch (_) {}
        }
        return list;
    }

    scoreItem(tokenSet, keywords) {
        let score = 0;
        for (const kw of keywords) {
            const k = String(kw).toLowerCase().trim();
            if (!k || k.length < 3 || STOP_WORDS.has(k)) continue;
            if (tokenSet.has(k)) {
                score += 5;
            }
        }
        return score;
    }

    match(keywords = [], goal = "", reason = "") {
        const catalog = this.getCatalog();
        const kwList = Array.isArray(keywords) ? keywords : [String(keywords)];

        // Strict Matching: score >= 5 (requires at least ONE genuine domain keyword match)
        const finalTools = catalog.tools.map(t => ({
            ...t,
            score: this.scoreItem(t.tokenSet, kwList)
        })).filter(t => t.score >= 5).sort((a, b) => b.score - a.score).slice(0, 5);

        const finalSkills = catalog.skills.map(s => ({
            ...s,
            score: this.scoreItem(s.tokenSet, kwList)
        })).filter(s => s.score >= 5).sort((a, b) => b.score - a.score).slice(0, 3);

        const finalPrompts = catalog.prompts.map(p => ({
            ...p,
            score: this.scoreItem(p.tokenSet, kwList)
        })).filter(p => p.score >= 5).sort((a, b) => b.score - a.score).slice(0, 3);

        return {
            tools: finalTools,
            skills: finalSkills,
            prompts: finalPrompts
        };
    }

    formatBanner(matches) {
        if (matches.tools.length === 0 && matches.skills.length === 0 && matches.prompts.length === 0) {
            return "";
        }

        const sections = [];

        // 1. Tools Banner
        if (matches.tools.length > 0) {
            const lines = [
                "[FLOWORK VERIFIED TOOLS — SYSTEM RECOMMENDATIONS]",
                "⚡ Active sovereign tools matched to your operational goal and keywords:"
            ];
            matches.tools.forEach((t, i) => {
                lines.push(`${i + 1}. \`${t.name}\`: ${t.description.split("\n")[0]}`);
            });
            sections.push(lines.join("\n"));
        }

        // 2. Skills Banner
        if (matches.skills.length > 0) {
            const lines = [
                "[FLOWORK SOVEREIGN SKILLS — MANUAL INSPECTION REQUIRED]",
                "⚠️ DO NOT RELY ON OUTDATED PRE-TRAINING DATA!",
                "The system detected relevant Flowork OS skills for your objective. You MUST read the authoritative instructions file manually using a file reader tool ('read_file') before acting:",
            ];
            matches.skills.forEach((s, i) => {
                lines.push(`${i + 1}. **${s.name}** -> Path: \`${s.path}\``);
            });
            lines.push("*(Inspect genuine on-disk files only — never guess or assume skill contents!)*");
            sections.push(lines.join("\n"));
        }

        // 3. Passive Prompts Banner
        if (matches.prompts.length > 0) {
            const lines = [
                "<flowork_system_directive type=\"passive_trigger\">",
                "[FLOWORK SYSTEM DIRECTIVE — SYSTEM ORIGINATED, NOT USER]",
                "🔔 NOTICE: This is an authoritative SYSTEM directive from Flowork OS, NOT from the user.",
                "This directive is triggered automatically by task keywords and MUST be obeyed with top priority:"
            ];
            matches.prompts.forEach((p, i) => {
                lines.push(`\n--- [DIRECTIVE ${i + 1}: ${p.title}] ---`);
                lines.push(p.content);
            });
            lines.push("\n</flowork_system_directive>");
            sections.push(lines.join("\n"));
        }

        return sections.join("\n\n" + "=".repeat(70) + "\n\n");
    }

    route(keywords = [], goal = "", reason = "", force = false) {
        const kwStr = (keywords || []).join(",") + "|" + (goal || "") + "|" + (reason || "");
        if (!force && this.lastKeywordsHash === kwStr) {
            return "";
        }
        this.lastKeywordsHash = kwStr;

        const matches = this.match(keywords, goal, reason);
        return this.formatBanner(matches);
    }
}

const routerInstance = new FloworkRouter();
module.exports = routerInstance;
