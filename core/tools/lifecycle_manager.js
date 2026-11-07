#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — CONTEXTUAL RETENTION & LIFECYCLE MANAGEMENT ENGINE
 * 
 * Enforces Option C Lifecycle Doctrine:
 * 1. Short-Response Carryover:
 *    - Recognizes terse user responses (<= 4 words: "ok", "lanjut", "gas", "yes", "proceed", "nomor 2", etc.)
 *    - Retains conditional tools, active skills, active domain, and passive prompts from previous turn.
 *    - Eliminates conversational amnesia.
 * 
 * 2. Domain Shift Detection & Sliding Window:
 *    - Detects transitions across domains (browser, shell_system, code_dev, os_doctrine).
 *    - Automatically decommissions obsolete conditional tools on domain switch.
 *    - Slides in new domain tools, skills, and prompts (Formula 5-3-3).
 * 
 * 3. State-Bound Retention:
 *    - Tracks physical resources (e.g. open browser pages in Chrome DevTools MCP backend).
 *    - Retains browser tools active while browser tabs/sessions are open, until browser_close_page.
 * 
 * 4. Just-In-Time (JIT) Skill Lifecycle:
 *    - Injects tool SKILL.md ONLY during the turn the tool executes.
 *    - Prevents token pollution in subsequent turns.
 */

const fs = require('fs');
const path = require('path');

const STATE_FILE = '/tmp/flowork_lifecycle_state.json';
const CURRENT_PROMPT_FILE = '/tmp/flowork_current_prompt.txt';
const ACTIVE_TRIGGER_FILE = '/tmp/flowork_active_trigger.json';

// Known domains and their defining patterns & keywords
const DOMAIN_DEFINITIONS = {
    browser: {
        patterns: [/https?:\/\//i, /www\./i, /\.(com|org|net|io|html|php)\b/i],
        keywords: [
            'browser', 'page', 'tab', 'url', 'website', 'web', 'scrape', 'dom',
            'click', 'screenshot', 'navigate', 'devtools', 'selector', 'input',
            'button', 'href', 'html', 'css', 'form', 'login'
        ]
    },
    shell_system: {
        patterns: [/\b(bash|sh|zsh)\b/i, /\b(sudo|systemctl|service|journalctl)\b/i, /\b(apt|dpkg)\b/i],
        keywords: [
            'bash', 'shell', 'terminal', 'command', 'exec', 'systemctl', 'service',
            'kernel', 'iso', 'rootfs', 'apt', 'dpkg', 'disk', 'memory', 'cpu',
            'process', 'kill', 'chmod', 'chown', 'sudo', 'mount', 'systemd',
            'network', 'ip', 'ping', 'daemon'
        ]
    },
    code_dev: {
        patterns: [/\b(git|github|gitlab)\b/i, /\.(py|rs|js|ts|cpp|c|go|php|json|toml)\b/i],
        keywords: [
            'code', 'function', 'script', 'python', 'rust', 'javascript', 'typescript',
            'node', 'compiler', 'syntax', 'refactor', 'git', 'commit', 'branch',
            'merge', 'push', 'pull', 'test', 'debug', 'lint', 'bug', 'class',
            'cargo', 'npm', 'composer', 'api', 'endpoint'
        ]
    },
    os_doctrine: {
        patterns: [/flowork/i, /sovereign/i, /cinnamon/i],
        keywords: [
            'flowork', 'sovereign', 'doctrine', 'rules', 'goal', 'soul', 'cinnamon',
            'desktop', 'icon', 'wm', 'mcp', 'tools', 'skills', 'prompts', 'readme',
            'banner', 'interceptor', 'lock', 'freeze'
        ]
    }
};

// Patterns representing terse/confirmative user replies (<= 4 words)
const SHORT_RESPONSE_PATTERNS = [
    // English
    /^(ok|okay|oke|yes|yep|y|sure|proceed|continue|next|go|go ahead|do it|apply|execute|run it|ready|fine|done|great|cool|perfect)\b/i,
    /^(option\s*\d+|number\s*\d+|step\s*\d+|choice\s*\d+|\d+)\b/i,
    // Indonesian
    /^(ok|oke|sip|siap|lanjut|lanjutkan|gas|gass|mantap|terapkan|eksekusi|kerjakan|jalan|jalankan|bener|betul|iya|ya)\b/i,
    /^(nomor\s*\d+|pilih\s*\d+|ke-\d+|opsi\s*\d+|\d+)\b/i
];

class LifecycleManager {
    constructor() {
        this.state = this.loadState();
    }

    /**
     * Load persistent state from /tmp
     */
    loadState() {
        try {
            if (fs.existsSync(STATE_FILE)) {
                const raw = fs.readFileSync(STATE_FILE, 'utf8');
                return JSON.parse(raw);
            }
        } catch (_) {}

        return {
            lastTurn: {
                userText: '',
                domain: 'general',
                isShortResponse: false,
                timestamp: 0
            },
            activeGoal: null,
            activeReason: null,
            activeKeywords: [],
            activeTools: [],
            activeSkills: [],
            activePrompts: [],
            resourceState: {
                browserOpenPages: 0,
                lastBrowserActivity: 0
            }
        };
    }

    /**
     * Persist state to disk
     */
    saveState() {
        try {
            fs.writeFileSync(STATE_FILE, JSON.stringify(this.state, null, 2), 'utf8');
        } catch (_) {}
    }

    /**
     * Check if user text qualifies as a short / confirmative response
     */
    isShortResponse(text) {
        if (!text || typeof text !== 'string') return false;
        const trimmed = text.trim();
        if (!trimmed) return false;

        const words = trimmed.split(/\s+/).filter(Boolean);
        if (words.length > 4) return false;

        // Check if words match confirmation patterns or numbers
        for (const pat of SHORT_RESPONSE_PATTERNS) {
            if (pat.test(trimmed)) {
                return true;
            }
        }

        // Single word or digits <= 3 characters are always treated as short responses
        if (words.length === 1 && words[0].length <= 5) {
            return true;
        }

        return false;
    }

    /**
     * Detect domain based on user text and environment
     */
    detectDomain(text, cwd = process.cwd()) {
        const t = (text || '').toLowerCase();
        const scores = {
            browser: 0,
            shell_system: 0,
            code_dev: 0,
            os_doctrine: 0
        };

        for (const [dom, def] of Object.entries(DOMAIN_DEFINITIONS)) {
            for (const pat of def.patterns) {
                if (pat.test(t)) {
                    scores[dom] += 5;
                }
            }
            for (const kw of def.keywords) {
                if (t.includes(kw)) {
                    scores[dom] += 2;
                }
            }
        }

        let bestDomain = null;
        let maxScore = 0;
        for (const [dom, score] of Object.entries(scores)) {
            if (score > maxScore) {
                maxScore = score;
                bestDomain = dom;
            }
        }

        return maxScore >= 2 ? bestDomain : null;
    }

    /**
     * Check if physical browser resources are currently open/active
     */
    isBrowserStateOpen() {
        if (!this.state.resourceState) return false;
        const pages = this.state.resourceState.browserOpenPages || 0;
        const lastActive = this.state.resourceState.lastBrowserActivity || 0;
        const now = Date.now();

        // If tabs are tracked as open and activity within last 30 minutes
        if (pages > 0 && (now - lastActive < 1800000)) {
            return true;
        }

        return false;
    }

    /**
     * Hook called at the start of every chat turn when a user message arrives
     */
    onUserMessage(userMessageContent, cwd = process.cwd()) {
        const text = (userMessageContent || '').trim();
        if (!text) return;

        // Persist raw prompt for external sniffers
        try {
            fs.writeFileSync(CURRENT_PROMPT_FILE, text, 'utf8');
        } catch (_) {}

        const isShort = this.isShortResponse(text);
        const previousDomain = this.state.lastTurn.domain || 'general';

        if (isShort) {
            // SHORT RESPONSE CARRYOVER:
            // Retain active domain, conditional tools, skills, goal, and prompts
            this.state.lastTurn = {
                userText: text,
                domain: previousDomain,
                isShortResponse: true,
                timestamp: Date.now()
            };
            this.saveState();
            return {
                mode: 'carryover',
                domain: previousDomain,
                isShortResponse: true,
                activeTools: this.state.activeTools,
                activeSkills: this.state.activeSkills,
                activePrompts: this.state.activePrompts
            };
        }

        // FULL USER MESSAGE: Detect Domain & Evaluate Domain Shift
        const newDomain = this.detectDomain(text, cwd) || 'general';
        const isShift = (previousDomain !== 'general' && newDomain !== 'general' && previousDomain !== newDomain);

        if (isShift) {
            // Domain Shift detected!
            // Check state-bound retention: Are browser resources still open?
            const browserOpen = this.isBrowserStateOpen();

            // Archive old tools unless state-bound retention applies
            if (previousDomain === 'browser' && browserOpen) {
                // Retain browser tools alongside new domain until closed
                this.state.activeTools = this.state.activeTools.filter(t => t.startsWith('browser_'));
            } else {
                this.state.activeTools = [];
            }

            // Slide out old skills and prompts
            this.state.activeSkills = [];
            this.state.activePrompts = [];
            this.state.activeGoal = null; // Reset goal on major domain shift
        }

        this.state.lastTurn = {
            userText: text,
            domain: newDomain,
            isShortResponse: false,
            timestamp: Date.now()
        };

        this.saveState();
        return {
            mode: isShift ? 'shift' : 'continue',
            domain: newDomain,
            isShortResponse: false,
            activeTools: this.state.activeTools,
            activeSkills: this.state.activeSkills,
            activePrompts: this.state.activePrompts
        };
    }

    /**
     * Hook called whenever a tool is successfully executed
     */
    onToolExecuted(toolName, params = {}) {
        if (!toolName) return;

        // 1. Manage Browser physical resource state
        if (toolName.startsWith('browser_') || toolName.startsWith('mcp_browser_')) {
            if (!this.state.resourceState) {
                this.state.resourceState = { browserOpenPages: 0, lastBrowserActivity: 0 };
            }

            if (toolName.includes('new_page')) {
                this.state.resourceState.browserOpenPages = Math.max(1, (this.state.resourceState.browserOpenPages || 0) + 1);
            } else if (toolName.includes('close_page')) {
                this.state.resourceState.browserOpenPages = Math.max(0, (this.state.resourceState.browserOpenPages || 1) - 1);
            } else {
                this.state.resourceState.browserOpenPages = Math.max(1, this.state.resourceState.browserOpenPages || 1);
            }
            this.state.resourceState.lastBrowserActivity = Date.now();
        }

        // 2. Record tool in activeTools
        if (!this.state.activeTools.includes(toolName)) {
            this.state.activeTools.push(toolName);
        }

        // 3. Update intercept metadata if provided
        if (params.reason) this.state.activeReason = params.reason;
        if (params.goal) this.state.activeGoal = params.goal;
        if (Array.isArray(params.keywords) && params.keywords.length > 0) {
            this.state.activeKeywords = params.keywords;
        }

        this.saveState();

        // Synchronize active trigger file
        try {
            fs.writeFileSync(ACTIVE_TRIGGER_FILE, JSON.stringify({
                goal: this.state.activeGoal,
                reason: this.state.activeReason,
                keywords: this.state.activeKeywords,
                tool: toolName,
                timestamp: new Date().toISOString()
            }, null, 2));
        } catch (_) {}
    }

    /**
     * Check if a tool should be active under current lifecycle rules
     */
    isToolActive(toolName, manifest, context) {
        if (!manifest) return true;

        // 1. Always active tools bypass conditional lifecycle
        if (manifest.activation === 'always') {
            return true;
        }

        const triggers = manifest.triggers || {};
        const excludeKeywords = triggers.exclude_keywords || [];

        // 2. Exclude Keywords Check (Strict Veto)
        const ctxText = (context && context.text) ? context.text : '';
        const ctxDomains = (context && context.domains) ? context.domains : [];
        for (const ex of excludeKeywords) {
            const exLower = String(ex).toLowerCase().trim();
            if (!exLower) continue;
            if (ctxText.includes(exLower)) return false;
            if (ctxDomains.some(d => d === exLower || d.endsWith('.' + exLower))) return false;
        }

        // 3. State-Bound Retention: Browser tools remain active if browser pages are open
        if ((toolName.startsWith('browser_') || toolName.startsWith('mcp_browser_')) && this.isBrowserStateOpen()) {
            return true;
        }

        // 4. Short-Response Carryover: Retain previously active conditional tools
        if (this.state.lastTurn && this.state.lastTurn.isShortResponse) {
            if (this.state.activeTools.includes(toolName)) {
                return true;
            }
            // If previous domain was browser and tool is browser tool, keep active
            if (this.state.lastTurn.domain === 'browser' && toolName.startsWith('browser_')) {
                return true;
            }
        }

        // 5. Environmental & Keyword Inclusions
        const keywords = triggers.keywords || [];
        for (const kw of keywords) {
            const kwLower = String(kw).toLowerCase().trim();
            if (!kwLower) continue;
            if (ctxText.includes(kwLower)) return true;
            if (ctxDomains.some(d => d.includes(kwLower) || kwLower.includes(d))) return true;
        }

        // Behavior matching
        const behavior = triggers.behavior || {};
        if (Array.isArray(behavior.file_extensions) && behavior.file_extensions.length > 0) {
            const exts = context?.extensions || [];
            for (const ext of behavior.file_extensions) {
                const normExt = ext.startsWith('.') ? ext.toLowerCase() : `.${ext.toLowerCase()}`;
                if (exts.includes(normExt) || ctxText.includes(normExt)) return true;
            }
        }

        if (Array.isArray(behavior.domains) && behavior.domains.length > 0) {
            for (const dom of behavior.domains) {
                const domLower = dom.toLowerCase().trim();
                if (domLower === '*') {
                    if (ctxDomains.length > 0 || ctxText.includes('http') || ctxText.includes('www.')) return true;
                    continue;
                }
                if (ctxDomains.some(d => d.includes(domLower)) || ctxText.includes(domLower)) return true;
            }
        }

        if (Array.isArray(behavior.files) && behavior.files.length > 0) {
            const files = context?.files || [];
            for (const f of behavior.files) {
                if (files.includes(f) || ctxText.includes(f.toLowerCase())) return true;
            }
        }

        return false;
    }

    /**
     * Get active state snapshot
     */
    getState() {
        return this.state;
    }

    /**
     * Update active skills list
     */
    setActiveSkills(skills) {
        this.state.activeSkills = Array.isArray(skills) ? skills : [];
        this.saveState();
    }

    /**
     * Update active prompts list
     */
    setActivePrompts(prompts) {
        this.state.activePrompts = Array.isArray(prompts) ? prompts : [];
        this.saveState();
    }
}

const lifecycleInstance = new LifecycleManager();
module.exports = lifecycleInstance;
