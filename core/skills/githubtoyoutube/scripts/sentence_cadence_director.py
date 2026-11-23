#!/usr/bin/env python3
"""
🎬 SENTENCE-BEAT STORYTELLING REGISTRY FOR 'BILLION-CONTEXT'
Maps all 111 sentence cues across 6 chapters to distinct narrative visuals,
emotional stickman poses, dynamic kinetic diagrams, and authentic GitHub proof.
Replaces mechanical static timers with voice-over cadence (Vox / Lemmino style).
"""

import math
import cairo

# ==============================================================================
# CHAPTER BEAT DATA REGISTRY (111 DISTINCT STORY BEATS)
# ==============================================================================

CHAPTER_BEATS = {
    # --------------------------------------------------------------------------
    # CHAPTER 1: THE MILLION-TOKEN ILLUSION (23 BEATS)
    # --------------------------------------------------------------------------
    1: [
        {
            "cat": "CRISIS", "title": "THE HEARTBREAKING MOMENT", "type": "metric",
            "stat": "HOUR 3: AMNESIA", "sub": "Every developer has watched their agent collapse mid-refactor",
            "col": (1.0, 0.25, 0.35), "action": "typing", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "SESSION", "title": "DEEP REFACTORING SESSION", "type": "code",
            "file": "agent_session.ts", "lines": [
                "// Turn 48: 3 hours into multi-file architectural refactor",
                "const sessionElapsed = '03:14:22';",
                "const filesExamined = ['engine.rs', 'context.rs', 'types.rs', 'storage.rs'];",
                "await agent.resolveDependencyGraph();"
            ],
            "action": "typing", "mood": "calm", "pos": (1580, 740)
        },
        {
            "cat": "AST", "title": "INTRICATE DEPENDENCY GRAPH", "type": "diagram", "kind": "ast_graph",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "FATAL", "title": "SUDDEN HALLUCINATION", "type": "incident", "kind": "glitch_amnesia",
            "action": "shocked", "mood": "shocked", "pos": (960, 740)
        },
        {
            "cat": "DATABASE", "title": "DATABASE SCHEMA FORGOTTEN", "type": "code",
            "file": "sqlite_invariants.sql", "lines": [
                "[FATAL] table_not_found: 'user_session_invariants'",
                "-- Model forgot schema negotiated 40 minutes earlier!",
                "-- Attempting to invent non-existent column 'cached_hash'...",
                "SELECT * FROM undefined_table; -- CRASH: EXIT CODE 1"
            ],
            "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "COLLISION", "title": "CRITICAL MODULE OVERWRITE", "type": "comparison",
            "left": "Original Invariant: Safe Rust Memory AST", "right": "Hallucinated Overwrite: Generic Stub",
            "action": "shocked", "mood": "angry", "pos": (1580, 740)
        },
        {
            "cat": "BILLING", "title": "THE $1,450 API BILL SHOCK", "type": "metric",
            "stat": "$1,450.00", "sub": "Single afternoon API bill for looping agent session",
            "col": (1.0, 0.25, 0.35), "action": "pacing", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "PROMISE", "title": "THE BIG TECH PROMISE", "type": "quote",
            "quote": "The era of context limits is officially over.\nBuild with millions of tokens without constraint.",
            "author": "Frontier AI Lab Marketing (2024)",
            "action": "standing", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "SPEC", "title": "THE 2,000,000 TOKEN ILLUSION", "type": "metric",
            "stat": "2,000,000 TOKENS", "sub": "Advertised window size vs catastrophic attention dilution",
            "col": (0.0, 0.95, 1.0), "action": "hanging", "mood": "cheeky", "pos": (1480, 95)
        },
        {
            "cat": "REALITY", "title": "BRUTAL MATHEMATICAL REALITY", "type": "comparison",
            "left": "Bigger Windows: Diluted Attention & Quadratic Costs", "right": "High-Density Memory: Sharp Reasoning & Steady Cost",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "ALGORITHM", "title": "QUADRATIC ATTENTION O(N²)", "type": "diagram", "kind": "attention_quadratic",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "COGNITIVE", "title": "LOST-IN-THE-MIDDLE SYNDROME", "type": "diagram", "kind": "lost_middle",
            "action": "presenting", "mood": "calm", "pos": (1580, 740)
        },
        {
            "cat": "DEGRADATION", "title": "REASONING FIDELITY PLUMMET", "type": "metric",
            "stat": "-64% ACCURACY", "sub": "Cognitive performance drops when saturated with 500k raw logs",
            "col": (1.0, 0.3, 0.4), "action": "presenting", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "DILUTION", "title": "DILUTED IN A SEA OF TOKENS", "type": "diagram", "kind": "token_sea",
            "action": "presenting", "mood": "calm", "pos": (340, 740)
        },
        {
            "cat": "FINANCIAL", "title": "THE FINANCIAL DRAIN", "type": "metric",
            "stat": "BURNING CAPITAL", "sub": "Rapid dollar velocity on uncurated multi-turn agent runs",
            "col": (1.0, 0.75, 0.2), "action": "walking", "mood": "shocked", "pos": (960, 740)
        },
        {
            "cat": "PROTOCOL", "title": "THE CUMULATIVE RE-SEND LOOP", "type": "diagram", "kind": "resend_loop",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "MATH", "title": "80K × 20 = 1,600,000 TOKENS", "type": "metric",
            "stat": "1.6M TOKENS", "sub": "Billed across 20 simple tool invocations re-sending history",
            "col": (1.0, 0.25, 0.35), "action": "presenting", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "ECONOMIC", "title": "THE ECONOMIC BRICK WALL", "type": "diagram", "kind": "economic_wall",
            "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "TRUNCATION", "title": "NAIVE SLIDING WINDOW TRUNCATION", "type": "diagram", "kind": "naive_truncation",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "LOSS", "title": "CHOPPING OFF THE PAST", "type": "code",
            "file": "sliding_window.ts", "lines": [
                "// Context buffer limit reached (128,000 tokens):",
                "messages.splice(0, 40); // VIOLENT CHOPPING",
                "// Lost initial prompt rules & database constraints!",
                "console.warn('System invariants discarded from context');"
            ],
            "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "IDENTITY", "title": "LOST AGENT IDENTITY", "type": "comparison",
            "left": "Naive Truncation: Amnesic Agent with Fragmented Memory", "right": "Dynamic Folding: Continuous Identity across Weeks",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "VERDICT", "title": "THE WRONG ROAD", "type": "quote",
            "quote": "We did not need bigger context windows.\nWe needed an entirely new memory paradigm.",
            "author": "Dr. Flow (Flowork OS)",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "PARADIGM", "title": "THE NEW MEMORY PARADIGM", "type": "metric",
            "stat": "A NEW PARADIGM", "sub": "Model-driven, self-regulating, prefix-friendly cognition",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 2: THE BREAKOUT DISCOVERY (19 BEATS)
    # --------------------------------------------------------------------------
    2: [
        {
            "cat": "DISCOVERY", "title": "ENTER BILLION-CONTEXT", "type": "github",
            "sub": "Trending open-source project by Ran Xiang-lei on GitHub",
            "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "PARADIGM", "title": "SMALL WINDOWS ARE ENOUGH", "type": "metric",
            "stat": "100K TOKENS", "sub": "Why throw raw billions when 100k curated tokens suffice?",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "COMPARE", "title": "RETHINKING THE PIPELINE", "type": "comparison",
            "left": "Bloated Multi-Million Context: High Latency & Cost", "right": "Curated 100K Window: Blazing Fast & Sustained Cache",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "CURATOR", "title": "MODEL AS CONSCIOUS CURATOR", "type": "diagram", "kind": "model_curator",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "SEAM", "title": "TRANSPARENT PROXY ARCHITECTURE", "type": "diagram", "kind": "proxy_seam",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "TOOLS", "title": "THE 4-METHOD ACP TOOL SUITE", "type": "code",
            "file": "acp-kernel/methods.d.ts", "lines": [
                "interface ACPKernel {",
                "  compress(start: number, end: number): Promise<FoldResult>;",
                "  decompress(rangeId: string): Promise<RawTurns>;",
                "  search_context(query: string): Promise<FactMatches>;",
                "  acp_status(): Promise<MemoryBudgetReport>;",
                "}"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "INSTALL", "title": "ZERO-CONFIG NPM INSTALL", "type": "code",
            "file": "terminal.sh", "lines": [
                "npm install -g billion-context --prefix=~/.local",
                "# Zero sudo required, binaries land in ~/.local/bin",
                "bili claude   # Injects transparently into Claude Code",
                "bili pi       # Works natively with Pi Coding Agent"
            ],
            "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "MATRIX", "title": "MULTI-HOST COMPATIBILITY", "type": "diagram", "kind": "host_matrix",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "MARATHON", "title": "FROM 45 MIN TO MONTHS", "type": "metric",
            "stat": "MONTH-LONG RUNS", "sub": "Agents code continuously without hitting context ceilings",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "INVERSION", "title": "INVERTING THE CONTROL FLOW", "type": "comparison",
            "left": "External Blind Truncation: Chopping Past Messages", "right": "Internal Cognitive Folding: Model Decides What to Fold",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "LICENSE", "title": "PERMISSIVE OPEN SOURCE", "type": "quote",
            "quote": "Living research paper and battle-tested code,\nopen-sourced under the MIT license.",
            "author": "ranxianglei/billion-context",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "ECOSYSTEM", "title": "DROP-IN FOR DEVELOPERS", "type": "diagram", "kind": "proxy_seam",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "EMPOWER", "title": "EMPOWERING THE INTELLIGENCE", "type": "metric",
            "stat": "AUTONOMOUS MEMORY", "sub": "Hands memory governance directly to the LLM agent",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "INTERFACE", "title": "CONSCIOUS EDITOR OF HISTORY", "type": "diagram", "kind": "acp_core",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "DENSITY", "title": "HIERARCHICAL SUMMARIZATION", "type": "code",
            "file": "acp-kernel/summarizer.ts", "lines": [
                "// Turn range 12..35 marked for folding:",
                "const foldedSummary = await acpKernel.foldRange(12, 35);",
                "contextWindow.replaceRangeWithSummary(foldedSummary);",
                "console.log('Replaced 45,000 raw tokens with 420-token folded node');"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "HOOK", "title": "AND THE BEST PART?", "type": "metric",
            "stat": "ZERO REWRITE", "sub": "Works seamlessly with existing developer setups",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "SEAMLESS", "title": "UNTOUCHED APPLICATION CODE", "type": "code",
            "file": "bashrc_alias.sh", "lines": [
                "# Add one simple alias to your shell environment:",
                "alias claude='bili claude'",
                "# Zero changes to your codebase, API keys, or workflows",
                "claude --project ./my-deep-repo"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "DEPLOY", "title": "VERSATILE DEPLOYMENT MODES", "type": "diagram", "kind": "host_matrix",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "TRIUMPH", "title": "UNBROKEN CODING HORIZONS", "type": "metric",
            "stat": "100% RELIABILITY", "sub": "Agents run for weeks without amnesia or rate-limit blowouts",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (960, 740)
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 3: REVERSIBLE DYNAMIC FOLDING (22 BEATS)
    # --------------------------------------------------------------------------
    3: [
        {
            "cat": "DEEP DIVE", "title": "THE ANATOMY OF FOLDING", "type": "diagram", "kind": "acp_core",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "FLAW", "title": "TRADITIONAL SUMMARIZATION IS A ONE-WAY STREET", "type": "comparison",
            "left": "Destructive Summarizer: Information Irretrievably Lost", "right": "Reversible Folding: Lossless SQL Storage",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "DESTRUCTION", "title": "50,000 TOKENS CRUSHED TO 500", "type": "metric",
            "stat": "99% DATA LOSS", "sub": "Standard summarizers permanently discard critical facts",
            "col": (1.0, 0.3, 0.4), "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "LOST", "title": "THE FORGOTTEN VARIABLE NAMES", "type": "code",
            "file": "regressed_module.rs", "lines": [
                "// ERROR: Agent forgot exact mutex guard variable name!",
                "// Original: let _lock = state.acquire_write_lock();",
                "// Hallucinated: let state = state.get(); // DEADLOCK",
                "[PANIC] Thread pool deadlock in worker thread 4"
            ],
            "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "CANNOT", "title": "CANNOT DEBUG THE UNSEEN", "type": "comparison",
            "left": "Traditional Summary: 'They discussed state locking.'", "right": "Billion-Context: Full 42-turn verbatim stack trace stored",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "SOLUTION", "title": "REVERSIBLE DYNAMIC FOLDING", "type": "metric",
            "stat": "100% REVERSIBLE", "sub": "Eradicates information loss through dual-layer storage",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "FOUR PILLARS", "title": "THE 4 ACP CAPABILITIES", "type": "diagram", "kind": "acp_core",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "TOOL 1", "title": "SUPERPOWER #1: COMPRESS", "type": "code",
            "file": "acp/compress.ts", "lines": [
                "// 1. Model invokes compress() on saturated turn range:",
                "const res = await acp.compress({ startTurn: 10, endTurn: 35 });",
                "// ACP-Kernel stores raw turns in SQLite vault",
                "// Generates high-density summary node for active prompt"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "THRESHOLD", "title": "HEALTHY THRESHOLD INVOKED", "type": "metric",
            "stat": "ACTIVE COMPRESS", "sub": "Folds when token saturation approaches safe limit",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "calm", "pos": (1580, 740)
        },
        {
            "cat": "HIERARCHY", "title": "MULTI-GENERATIONAL NODES", "type": "diagram", "kind": "memory_iceberg",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "NO DELETE", "title": "NOTHING IS EVER DELETED", "type": "metric",
            "stat": "ZERO DATA LOSS", "sub": "Folded messages are preserved with byte-for-byte fidelity",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "SQLITE", "title": "SQLITE STORAGE VAULT", "type": "code",
            "file": "storage/sqlite.ts", "lines": [
                "import { Database } from 'bun:sqlite';",
                "const db = new Database('session_memory.db');",
                "db.query('INSERT INTO folded_blocks VALUES (?, ?, ?)').run(",
                "  blockId, summaryNode, JSON.stringify(rawTurns));"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "TOOL 2", "title": "SUPERPOWER #2: DECOMPRESS", "type": "code",
            "file": "acp/decompress.ts", "lines": [
                "// 2. Model encounters regression from 3 days ago:",
                "const raw = await acp.decompress('range_turn_10_35');",
                "contextWindow.unfoldVerbatim(raw);",
                "console.log('Restored exact tokens, variables and stack traces!');"
            ],
            "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "EXACT", "title": "RESTORING EXACT PROMPT BLOCKS", "type": "comparison",
            "left": "Standard AI: Vague Guesswork & Hallucinated Code", "right": "Billion-Context: Verbatim Retrieval of Day 1 Turns",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "SEAMLESS", "title": "TRANSPARENT RE-INJECTION", "type": "diagram", "kind": "acp_core",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "TOOL 3", "title": "SUPERPOWER #3: SEARCH_CONTEXT", "type": "code",
            "file": "acp/search.ts", "lines": [
                "// 3. Fast grep across historical conversation iceberg:",
                "const hits = await acp.search_context('Postgres pool timeout');",
                "// Returns sub-millisecond snippets without bloating prompt!",
                "return hits.map(h => ({ turn: h.turn, fact: h.summary }));"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "GREP", "title": "GREP ACROSS HISTORICAL ICEBERG", "type": "diagram", "kind": "memory_iceberg",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "TARGETED", "title": "FACTS RETRIEVED ON DEMAND", "type": "metric",
            "stat": "< 1 MILLISECOND", "sub": "Targeted retrieval of verified decisions and error traces",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "TOOL 4", "title": "SUPERPOWER #4: ACP_STATUS", "type": "code",
            "file": "acp/status.ts", "lines": [
                "// 4. Cognitive introspection report:",
                "return {",
                "  activeTokens: 38400, maxSafeTokens: 100000,",
                "  foldedRanges: 14, prefixCacheRatio: 0.988",
                "};"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "BUDGET", "title": "COGNITIVE INTROSPECTION", "type": "metric",
            "stat": "INTROSPECTION", "sub": "Reports exact token budget, folded ranges, and hit ratios",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "calm", "pos": (1580, 740)
        },
        {
            "cat": "ORGANISM", "title": "SELF-REGULATING COGNITIVE ORGANISM", "type": "quote",
            "quote": "The agent becomes a self-regulating organism,\ncurating its working memory with surgical precision.",
            "author": "ranxianglei/billion-context Architecture",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "SWEET SPOT", "title": "THE 30K - 80K TOKEN SWEET SPOT", "type": "metric",
            "stat": "30K - 80K TOKENS", "sub": "Feather-light working memory preserving maximum reasoning IQ",
            "col": (0.0, 0.95, 1.0), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 4: CACHE PRESERVATION ARCHITECTURE (18 BEATS)
    # --------------------------------------------------------------------------
    4: [
        {
            "cat": "SYSTEMS", "title": "LOW-LEVEL SYSTEMS ENGINEERING", "type": "diagram", "kind": "cache_invariant",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "PRICING", "title": "THE CLOUD PROVIDER PRICING SHIFT", "type": "metric",
            "stat": "PROMPT CACHING", "sub": "Anthropic, OpenAI, and DeepSeek price around prefix hits",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "DISCOUNT", "title": "UP TO 90% DISCOUNT ON CACHED TOKENS", "type": "metric",
            "stat": "-90% DISCOUNT", "sub": "Cached prefix tokens billed at a tenth of base input rate",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "DESTROY", "title": "TRADITIONAL SUMMARIZERS DESTROY CACHING", "type": "comparison",
            "left": "Standard Summarizer: Modifies Middle of Prompt", "right": "Billion-Context: Invariant Cryptographic Prefix",
            "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "MUTATION", "title": "INLINE HISTORY MUTATION", "type": "code",
            "file": "cache_breaker.ts", "lines": [
                "// Traditional summarizer replaces turns 5..10 in-place:",
                "messages[5] = { role: 'system', content: 'Summary...' };",
                "// FATAL: Mutated byte at offset 4,200!",
                "[WARN] Provider Cache Busted: 0% hit rate on next turn"
            ],
            "action": "shocked", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "BUSTED", "title": "THE CACHE IS BUSTED", "type": "metric",
            "stat": "CACHE MISS: 100%", "sub": "Single byte change invalidates subsequent KV-cache",
            "col": (1.0, 0.25, 0.35), "action": "shocked", "mood": "angry", "pos": (1580, 740)
        },
        {
            "cat": "PENALTY", "title": "FULL BILLING PENALTY", "type": "diagram", "kind": "attention_quadratic",
            "action": "pacing", "mood": "shocked", "pos": (1580, 740)
        },
        {
            "cat": "PRECISION", "title": "SURGICAL CACHE INVARIANT DESIGN", "type": "metric",
            "stat": "SURGICAL DESIGN", "sub": "Engineered strictly to satisfy cloud KV-cache invariants",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "INVARIANT", "title": "STRICTLY PREFIX-CACHE FRIENDLY", "type": "diagram", "kind": "cache_invariant",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "APPEND", "title": "APPENDING TO TAIL ONLY", "type": "code",
            "file": "acp-kernel/prompt_builder.ts", "lines": [
                "// Prefix: System prompt + Tool schemas (SHA256 locked)",
                "const prefixBlock = getImmutablePrefixHash(); // NEVER MODIFIED",
                "// Dynamic folded summaries appended strictly to TAIL:",
                "const finalPrompt = [...prefixBlock, ...tailSummaries];",
                "// Result: 98.6% sustained provider cache hits!"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "HIT RATE", "title": "98.6% SUSTAINED CACHE HIT RATE", "type": "metric",
            "stat": "98.6% HIT RATE", "sub": "Sustained across entire multi-day continuous coding runs",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "OVERHEAD", "title": "COMPRESSION COSTS LESS THAN 2%", "type": "metric",
            "stat": "< 2% OVERHEAD", "sub": "Total session overhead of running ACP compression tools",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "ENGINE", "title": "BUN SQLITE EMBEDDED ENGINE", "type": "code",
            "file": "bun_sqlite.ts", "lines": [
                "import { Database } from 'bun:sqlite';",
                "const db = new Database(':memory:');",
                "db.exec('PRAGMA synchronous = OFF; PRAGMA journal_mode = WAL;');",
                "// Executes reads & writes in sub-millisecond async batches"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "ASYNC", "title": "SUB-MS ASYNC DISK FLUSH", "type": "metric",
            "stat": "0.12 MS", "sub": "Asynchronous disk flush without blocking LLM streaming",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "FOOTPRINT", "title": "NEGLIGIBLE LOCAL FOOTPRINT", "type": "metric",
            "stat": "< 50 MB RAM", "sub": "Lightweight memory consumption on developer machines",
            "col": (0.2, 1.0, 0.6), "action": "presenting", "mood": "calm", "pos": (1580, 740)
        },
        {
            "cat": "PROTOCOL", "title": "WIRE PROTOCOL REWRITES", "type": "diagram", "kind": "proxy_seam",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "STREAM", "title": "SSE STREAMING INTERCEPT", "type": "code",
            "file": "proxy/stream_handler.ts", "lines": [
                "// Intercepting Server-Sent Events (SSE) on the fly:",
                "export async function handleStream(req: Request) {",
                "  const rawStream = await fetchUpstream(req);",
                "  return transformAndInjectACP(rawStream);",
                "}"
            ],
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "SYNTHESIS", "title": "LOCAL SPEED + CLOUD ECONOMY", "type": "comparison",
            "left": "Unoptimized Cloud Calls: Expensive & Fragile", "right": "Billion-Context: Unthrottled Local Speed + 90% Bill Savings",
            "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 5: 18.7 BILLION TOKEN BENCHMARK (16 BEATS)
    # --------------------------------------------------------------------------
    5: [
        {
            "cat": "PROOF", "title": "EXTRAORDINARY EMPIRICAL PROOF", "type": "quote",
            "quote": "Extraordinary claims require extraordinary evidence.\nHere is the empirical proof.",
            "author": "ranxianglei/billion-context Study",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "RESEARCH", "title": "LIVING RESEARCH PAPER", "type": "github",
            "sub": "Complete dataset and benchmarks published openly on GitHub",
            "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "STUDY", "title": "4.5 MONTH CONTINUOUS EVALUATION", "type": "metric",
            "stat": "4.5 MONTHS", "sub": "Longitudinal evaluation across production coding environments",
            "col": (0.85, 0.35, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "DATA", "title": "THE NUMBERS SPEAK FOR THEMSELVES", "type": "metric",
            "stat": "HARD DATA", "sub": "Rigorous cross-evaluation on leading open benchmarks",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "CALLS", "title": "174,327 MODEL INVOCATIONS", "type": "metric",
            "stat": "174,327 CALLS", "sub": "Total model calls processed across the evaluation marathon",
            "col": (0.0, 0.95, 1.0), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "VOLUME", "title": "18.76 BILLION INPUT TOKENS", "type": "metric",
            "stat": "18.76 BILLION", "sub": "Cumulative tokens processed with zero context window overflows",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "MARATHON", "title": "12,049 CONSECUTIVE INVOCATIONS", "type": "metric",
            "stat": "12,049 IN A ROW", "sub": "Longest single unbroken coding marathon session",
            "col": (1.0, 0.8, 0.2), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "BOUNDS", "title": "CONFINED TO 200K WINDOW LIMITS", "type": "diagram", "kind": "survival_chart",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "CRASHES", "title": "ZERO CRASHES", "type": "metric",
            "stat": "0 CRASHES", "sub": "Not a single window violation across 174k invocations",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (960, 740)
        },
        {
            "cat": "EXHAUSTION", "title": "ZERO TOKEN EXHAUSTION ABORTS", "type": "metric",
            "stat": "0 ABORTS", "sub": "Sessions code autonomously without manual engineer intervention",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (960, 740)
        },
        {
            "cat": "BENCHMARKS", "title": "THIRD-PARTY EVALUATIONS", "type": "diagram", "kind": "contextbench_chart",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "RANK 1", "title": "CONTEXTBENCH #1 RANKING", "type": "diagram", "kind": "contextbench_chart",
            "action": "presenting", "mood": "excited", "pos": (340, 740)
        },
        {
            "cat": "ACCURACY", "title": "+16.6% OVER LEADING VECTOR RAG", "type": "metric",
            "stat": "+16.6% ACCURACY", "sub": "Outperforms embedding + reranking RAG on LongMemEval-S",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "TTL", "title": "MEMORYAGENTBENCH 1.48M TTL SURVIVAL", "type": "diagram", "kind": "survival_chart",
            "action": "celebrating", "mood": "celebrating", "pos": (340, 740)
        },
        {
            "cat": "REAL", "title": "NOT A THEORETICAL TOY", "type": "quote",
            "quote": "This is not a toy. It is battle-tested,\nproduction-grade cognitive systems engineering.",
            "author": "Empirical Verification Benchmark",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "HORIZON", "title": "PROVEN IN REAL-WORLD COMBAT", "type": "metric",
            "stat": "BATTLE-TESTED", "sub": "Proven across 4.5 months and 18.7 billion tokens",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (960, 740)
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 6: THE SOVEREIGN VERDICT & MASTER FINALE (13 BEATS)
    # --------------------------------------------------------------------------
    6: [
        {
            "cat": "MANIFESTO", "title": "THROWAWAY SESSIONS ARE OVER", "type": "quote",
            "quote": "The era of treat-and-throwaway AI sessions is officially over.\nLong-term resilient memory is here.",
            "author": "Dr. Flow & Flowork Architecture Board",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "WORKFLOW", "title": "DEVELOPMENT DOES NOT RESET HOURLY", "type": "comparison",
            "left": "Fragile 1-Hour Ephemeral Sessions", "right": "Sovereign Multi-Week Iteration Horizon",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "ENGINEERING", "title": "REAL ENGINEERING TAKES WEEKS", "type": "metric",
            "stat": "MULTI-WEEK PEERS", "sub": "Continuous bug reproduction, refactors, and architectural debate",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "calm", "pos": (1580, 740)
        },
        {
            "cat": "PEERS", "title": "AGENTS AS AUTONOMOUS PEERS", "type": "quote",
            "quote": "For coding agents to become true peers,\nthey must possess memory that survives the night.",
            "author": "Sovereign AI Philosophy",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "NOT WAITING", "title": "DO NOT WAIT FOR 5M WINDOWS", "type": "comparison",
            "left": "Waiting for 5M Windows: High Costs & Slow Latency", "right": "billion-context Today: Fast, Cheap & Infinite",
            "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "GOVERNANCE", "title": "MODEL-DRIVEN CONTEXT GOVERNANCE", "type": "diagram", "kind": "acp_core",
            "action": "presenting", "mood": "cool", "pos": (340, 740)
        },
        {
            "cat": "QUICKSTART", "title": "GET STARTED IN UNDER 60 SECONDS", "type": "metric",
            "stat": "< 60 SECONDS", "sub": "Quick global installation with zero root privileges required",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (1580, 740)
        },
        {
            "cat": "SETUP", "title": "60-SECOND INSTALLATION", "type": "code",
            "file": "terminal_quickstart.sh", "lines": [
                "npm install -g billion-context --prefix=~/.local",
                "# Pair directly with your favorite coding agent:",
                "bili claude",
                "# Enjoy 30-day continuous sessions with zero amnesia"
            ],
            "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "OPEN", "title": "ALL CODE & DATA OPEN SOURCED", "type": "github",
            "sub": "Full codebase and longitudinal evaluation on GitHub under MIT",
            "action": "presenting", "mood": "excited", "pos": (1580, 740)
        },
        {
            "cat": "LINK", "title": "GITHUB.COM/RANXIANGLEI/BILLION-CONTEXT", "type": "metric",
            "stat": "STAR THE REPO", "sub": "Official URL pinned on screen & in video description",
            "col": (0.0, 0.95, 1.0), "action": "presenting", "mood": "cool", "pos": (1580, 740)
        },
        {
            "cat": "LIBERATE", "title": "LIBERATE YOUR AI AGENTS", "type": "quote",
            "quote": "Go star the repository, audit the code,\nand liberate your agents from the amnesia tax.",
            "author": "ranxianglei/billion-context (MIT)",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        },
        {
            "cat": "SUBSCRIBE", "title": "SUBSCRIBE FOR REPO BREAKDOWNS", "type": "metric",
            "stat": "🔔 SUBSCRIBE", "sub": "Weekly deep dives into breakthrough open-source repositories",
            "col": (0.2, 1.0, 0.6), "action": "celebrating", "mood": "celebrating", "pos": (960, 740)
        },
        {
            "cat": "SOVEREIGN", "title": "BUILD, SHIP, STAY SOVEREIGN", "type": "quote",
            "quote": "Until next time: keep building, keep shipping,\nand stay sovereign.",
            "author": "Dr. Flow & Flowork OS Studio",
            "action": "standing", "mood": "cool", "pos": (960, 740)
        }
    ]
}


# ==============================================================================
# 2. AUDIO-SYNCHRONIZED SENTENCE BEAT HELPER
# ==============================================================================

def get_sentence_beat(t, cues):
    """
    Finds the active sentence cue from the SRT cues list.
    Returns:
      beat_idx: 0-indexed position of sentence in the chapter
      beat_t: elapsed time in this sentence (t - start)
      beat_dur: total duration of this sentence (end - start)
      beat_prog: progress ratio in this sentence (0.0 to 1.0)
      beat_text: the spoken sentence
      is_cut: True if beat_t < 0.20 (snap cut transition window)
    """
    for idx, (s, e, txt) in enumerate(cues):
        if s <= t <= e:
            dur = max(0.1, e - s)
            elapsed = t - s
            return idx, elapsed, dur, min(1.0, elapsed / dur), txt, (elapsed < 0.20)
    # If before first cue:
    if cues and t < cues[0][0]:
        first_dur = max(0.1, cues[0][1] - cues[0][0])
        return 0, t, first_dur, min(1.0, t / first_dur), cues[0][2], False
    # If after last cue:
    if cues:
        last_idx = len(cues) - 1
        last_dur = max(0.1, cues[-1][1] - cues[-1][0])
        elapsed = t - cues[-1][0]
        return last_idx, elapsed, last_dur, 1.0, cues[-1][2], False
    return 0, 0.0, 5.0, 0.0, "", False


# ==============================================================================
# 3. PROCEDURAL SENTENCE BEAT CARD RENDERER
# ==============================================================================

def resolve_shot_mode(beat, beat_idx):
    btype = beat.get("type", "metric")
    stat = str(beat.get("stat", ""))
    quote = str(beat.get("quote", ""))
    if btype == "incident" or ",450" in stat or "We did not need" in quote or "Extraordinary claims" in quote or "era of treat-and-throwaway" in quote or "0 CRASHES" in stat:
        return "closeup"
    if btype in ["code", "github"]:
        return "fullscreen"
    if btype == "diagram":
        return "diagram_full"
    return "card"

def draw_sentence_beat_card(ctx, ch_num, t, cues, x=220, y=95, w=1480, h=590, img_surf=None):
    """
    Renders an audio-synchronized sentence beat card with 4 dynamic cinematic shot modes:
    1. 'closeup': Dramatic character zoom (2.15x) with floating stat & glowing visor.
    2. 'fullscreen': Immersive full-screen code/GitHub takeover (1760x710).
    3. 'diagram_full': Canvas-spanning kinetic vector architecture (no card borders).
    4. 'card': High-contrast optical glass split card.
    Returns (action, mood, (pos_x, pos_y), stick_scale) for complete cinematic synchrony.
    """
    beat_idx, beat_t, beat_dur, beat_prog, beat_text, is_cut = get_sentence_beat(t, cues)
    beats = CHAPTER_BEATS.get(ch_num, CHAPTER_BEATS[1])
    active_beat = beats[beat_idx % len(beats)]
    shot_mode = resolve_shot_mode(active_beat, beat_idx)

    # Determine Character Scale & Position based on shot mode
    stick_scale = 1.35
    pos = active_beat.get("pos", (1580, 740))
    action = active_beat.get("action", "presenting")
    mood = active_beat.get("mood", "cool")

    if shot_mode == "closeup":
        stick_scale = 2.15
        pos = (960, 740)
    elif shot_mode == "fullscreen":
        stick_scale = 1.25
        pos = (1710, 760) if pos[0] > 960 else (210, 760)
    elif shot_mode == "diagram_full":
        stick_scale = 1.35
        pos = (320, 740) if pos[0] < 960 else (1600, 740)

    # Adjust card geometry for shot mode
    if shot_mode == "fullscreen":
        x, y, w, h = 80, 70, 1760, 710
    elif shot_mode == "diagram_full":
        x, y, w, h = 100, 80, 1720, 700

    ctx.save()

    # Subtle slow push-in animation
    anim_factor = min(1.0, beat_t / 0.25)
    scale_factor = 0.98 + 0.02 * anim_factor + 0.01 * beat_prog
    drift_y = (1.0 - anim_factor) * 12.0

    cx = x + w / 2.0
    cy = y + h / 2.0
    ctx.translate(cx, cy + drift_y)
    ctx.scale(scale_factor, scale_factor)
    ctx.translate(-cx, -cy)

    if shot_mode == "closeup":
        # Heavy cinematic dark vignette focus
        ctx.save()
        v_pat = cairo.RadialGradient(960, 540, 200, 960, 540, 900)
        v_pat.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.3)
        v_pat.add_color_stop_rgba(1.0, 0.01, 0.02, 0.05, 0.85)
        ctx.set_source(v_pat); ctx.rectangle(0, 0, 1920, 1080); ctx.fill()
        if active_beat.get("type") == "incident":
            ctx.translate(math.sin(t * 35.0) * 4.0, math.cos(t * 30.0) * 2.0)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        stat_text = active_beat.get("stat", active_beat.get("title", ""))
        col = active_beat.get("col", (1.0, 0.25, 0.35))
        ctx.set_source_rgba(col[0], col[1], col[2], 0.9)
        ctx.set_font_size(64)
        t_ext = ctx.text_extents(stat_text)
        ctx.move_to((1920 - t_ext.width) / 2.0, 220)
        ctx.show_text(stat_text)
        ctx.set_font_size(24); ctx.set_source_rgb(0.9, 0.95, 1.0)
        sub_text = active_beat.get("sub", active_beat.get("title", ""))
        s_ext = ctx.text_extents(sub_text)
        ctx.move_to((1920 - s_ext.width) / 2.0, 275)
        ctx.show_text(sub_text)
        ctx.set_source_rgba(0.12, 0.16, 0.24, 0.8)
        ctx.rectangle(760, 310, 400, 16); ctx.fill()
        ctx.set_source_rgb(0.0, 0.95, 1.0)
        ctx.rectangle(760, 310, 400 * (1.0 - beat_prog), 16); ctx.fill()
        ctx.set_font_size(10); ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(890, 322); ctx.show_text(f"CADENCE: {max(0.0, beat_dur - beat_t):.1f}s")
        ctx.restore()
    else:
        if shot_mode != "diagram_full":
            ctx.set_source_rgba(0.015, 0.03, 0.06, 0.93 * anim_factor)
            ctx.rectangle(x, y, w, h); ctx.fill()
            ctx.set_source_rgba(0.0, 1.0, 0.7, 0.80 * anim_factor)
            ctx.set_line_width(2.0); ctx.rectangle(x, y, w, h); ctx.stroke()

        bar_h = 44
        ctx.set_source_rgba(0.06, 0.10, 0.16, 0.98)
        ctx.rectangle(x, y, w, bar_h); ctx.fill()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(14); ctx.set_source_rgb(0.0, 1.0, 0.7)
        ctx.move_to(x + 20, y + 28)
        ctx.show_text(f"BEAT {beat_idx + 1:02d}/{len(cues):02d} // [{active_beat['cat']}]")
        ctx.set_font_size(15); ctx.set_source_rgb(0.96, 0.96, 0.98)
        ctx.move_to(x + 240, y + 28); ctx.show_text(active_beat["title"])

        ctx.set_source_rgba(0.15, 0.20, 0.28, 0.85)
        ctx.rectangle(x + w - 260, y + 14, 230, 16); ctx.fill()
        ctx.set_source_rgb(0.0, 0.95, 1.0)
        ctx.rectangle(x + w - 260, y + 14, 230 * (1.0 - beat_prog), 16); ctx.fill()
        ctx.set_font_size(10); ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(x + w - 250, y + 26); ctx.show_text(f"VOICE CADENCE: {max(0.0, beat_dur - beat_t):.1f}s")

        content_y = y + bar_h + 20
        content_h = h - bar_h - 40
        btype = active_beat.get("type", "metric")

        if btype == "metric":
            ctx.set_font_size(68)
            col = active_beat.get("col", (0.0, 0.95, 1.0))
            ctx.set_source_rgb(*col)
            stat_ext = ctx.text_extents(active_beat["stat"])
            ctx.move_to(x + (w - stat_ext.width) / 2.0, content_y + 170); ctx.show_text(active_beat["stat"])
            bx = x + 180; bw = w - 360
            ctx.set_source_rgba(0.12, 0.16, 0.22, 0.9); ctx.rectangle(bx, content_y + 220, bw, 22); ctx.fill()
            fill_ratio = 0.85 + 0.1 * math.sin(t * 3.0)
            ctx.set_source_rgb(*col); ctx.rectangle(bx, content_y + 220, bw * fill_ratio, 22); ctx.fill()
            ctx.set_font_size(21); ctx.set_source_rgb(0.9, 0.94, 0.98)
            sub_ext = ctx.text_extents(active_beat["sub"])
            ctx.move_to(x + (w - sub_ext.width) / 2.0, content_y + 310); ctx.show_text(active_beat["sub"])

        elif btype == "code":
            ctx.set_source_rgba(0.03, 0.05, 0.08, 0.95)
            ctx.rectangle(x + 40, content_y + 10, w - 80, content_h - 20); ctx.fill()
            ctx.set_source_rgba(0.0, 0.8, 1.0, 0.4); ctx.set_line_width(1.5)
            ctx.rectangle(x + 40, content_y + 10, w - 80, content_h - 20); ctx.stroke()
            ctx.set_font_size(14); ctx.set_source_rgb(0.0, 0.95, 1.0)
            ctx.move_to(x + 60, content_y + 40); ctx.show_text(f"📄 {active_beat.get('file', 'main.ts')}")
            ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(17)
            lines = active_beat.get("lines", [])
            for idx, l in enumerate(lines):
                ly = content_y + 90 + idx * 46
                ctx.set_source_rgba(0.4, 0.5, 0.6, 0.7); ctx.move_to(x + 65, ly); ctx.show_text(f"{idx+1:02d}")
                if l.startswith("//") or l.startswith("--") or l.startswith("#"):
                    ctx.set_source_rgb(0.45, 0.55, 0.65)
                elif "FATAL" in l or "CRASH" in l or "PANIC" in l or "ERROR" in l:
                    ctx.set_source_rgb(1.0, 0.3, 0.4)
                elif "await" in l or "const" in l or "let" in l or "import" in l or "alias" in l or "npm" in l:
                    ctx.set_source_rgb(0.0, 0.95, 1.0)
                else:
                    ctx.set_source_rgb(0.2, 1.0, 0.6)
                ctx.move_to(x + 115, ly); ctx.show_text(l)

        elif btype == "comparison":
            half_w = (w - 100) / 2.0
            ctx.set_source_rgba(0.08, 0.03, 0.04, 0.95); ctx.rectangle(x + 30, content_y + 20, half_w, content_h - 40); ctx.fill()
            ctx.set_source_rgba(1.0, 0.25, 0.35, 0.8); ctx.set_line_width(2.0); ctx.rectangle(x + 30, content_y + 20, half_w, content_h - 40); ctx.stroke()
            ctx.set_source_rgb(1.0, 0.3, 0.4); ctx.set_font_size(18); ctx.move_to(x + 55, content_y + 65); ctx.show_text("❌ TRADITIONAL / FLAWED APPROACH")
            ctx.set_source_rgb(0.9, 0.9, 0.95); ctx.set_font_size(18); ctx.move_to(x + 55, content_y + 140); ctx.show_text(active_beat.get("left", ""))

            ctx.set_source_rgba(0.02, 0.07, 0.05, 0.95); ctx.rectangle(x + 50 + half_w, content_y + 20, half_w, content_h - 40); ctx.fill()
            ctx.set_source_rgba(0.2, 1.0, 0.6, 0.85); ctx.set_line_width(2.0); ctx.rectangle(x + 50 + half_w, content_y + 20, half_w, content_h - 40); ctx.stroke()
            ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.set_font_size(18); ctx.move_to(x + 75 + half_w, content_y + 65); ctx.show_text("✅ BILLION-CONTEXT ARCHITECTURE")
            ctx.set_source_rgb(0.9, 0.98, 0.95); ctx.set_font_size(18); ctx.move_to(x + 75 + half_w, content_y + 140); ctx.show_text(active_beat.get("right", ""))

            vs_x, vs_y = x + 40 + half_w, content_y + (content_h / 2.0)
            ctx.set_source_rgba(0.04, 0.08, 0.14, 0.98); ctx.arc(vs_x, vs_y, 35, 0, 2*math.pi); ctx.fill()
            ctx.set_source_rgb(0.0, 0.95, 1.0); ctx.set_line_width(2.5); ctx.arc(vs_x, vs_y, 35, 0, 2*math.pi); ctx.stroke()
            ctx.set_font_size(18); ctx.set_source_rgb(1.0, 1.0, 1.0); ctx.move_to(vs_x - 14, vs_y + 6); ctx.show_text("VS")

        elif btype == "github":
            if img_surf:
                ctx.save()
                ctx.rectangle(x + 30, content_y, w - 60, content_h); ctx.clip()
                img_w = img_surf.get_width(); img_h = img_surf.get_height()
                sc = max((w - 60) / float(img_w), content_h / float(img_h))
                ctx.translate(x + 30, content_y + math.sin(t * 0.5) * 15.0); ctx.scale(sc, sc)
                ctx.set_source_surface(img_surf, 0, 0); ctx.paint()
                ctx.restore()
            ctx.set_source_rgba(0.0, 1.0, 0.7, 0.6); ctx.set_line_width(2.0); ctx.rectangle(x + 30, content_y, w - 60, content_h); ctx.stroke()

        elif btype == "quote":
            q_lines = active_beat.get("quote", "").split("\n")
            for q_idx, ql in enumerate(q_lines):
                q_ext = ctx.text_extents(ql)
                ctx.move_to(x + (w - q_ext.width) / 2.0, content_y + 160 + q_idx * 45); ctx.show_text(ql)
            ctx.set_font_size(18); ctx.set_source_rgb(0.0, 0.95, 1.0)
            auth = f"— {active_beat.get('author', 'Flowork OS')}"
            a_ext = ctx.text_extents(auth); ctx.move_to(x + (w - a_ext.width) / 2.0, content_y + 290); ctx.show_text(auth)

        elif btype == "diagram":
            kind = active_beat.get("kind", "acp_core")
            dcx = x + w / 2.0
            dcy = content_y + content_h / 2.0

            if kind == "acp_core":
                ctx.set_source_rgba(0.0, 0.8, 1.0, 0.25); ctx.arc(dcx, dcy, 120, 0, 2*math.pi); ctx.fill()
                ctx.set_source_rgb(0.0, 1.0, 0.7); ctx.set_line_width(2.5); ctx.arc(dcx, dcy, 120, 0, 2*math.pi); ctx.stroke()
                ctx.set_font_size(24); ctx.set_source_rgb(1.0, 1.0, 1.0); ctx.move_to(dcx - 70, dcy); ctx.show_text("ACP-KERNEL")
                satellites = ["compress()", "decompress()", "search_context()", "acp_status()"]
                for s_idx, s_name in enumerate(satellites):
                    ang = s_idx * (math.pi / 2.0) + math.sin(t * 2.0) * 0.1
                    sx = dcx + math.cos(ang) * 260; sy = dcy + math.sin(ang) * 160
                    ctx.set_source_rgba(0.0, 0.95, 1.0, 0.5); ctx.move_to(dcx, dcy); ctx.line_to(sx, sy); ctx.stroke()
                    ctx.set_source_rgb(0.05, 0.08, 0.14); ctx.rectangle(sx - 75, sy - 22, 150, 44); ctx.fill()
                    ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.rectangle(sx - 75, sy - 22, 150, 44); ctx.stroke()
                    ctx.set_font_size(14); ctx.move_to(sx - 55, sy + 6); ctx.show_text(s_name)

            elif kind == "ast_graph":
                ctx.set_font_size(15)
                nodes = [
                    ("Root AST", dcx, dcy - 120, (0.0, 0.95, 1.0)),
                    ("Lexer / TokenStream", dcx - 280, dcy - 20, (0.2, 1.0, 0.6)),
                    ("Parser / TypeCheck", dcx + 280, dcy - 20, (0.2, 1.0, 0.6)),
                    ("Symbol Table", dcx - 180, dcy + 100, (0.9, 0.4, 1.0)),
                    ("Codegen / Target", dcx + 180, dcy + 100, (1.0, 0.8, 0.2))
                ]
                for n_idx, (lbl, nx, ny, ncol) in enumerate(nodes):
                    if n_idx > 0:
                        ctx.set_source_rgba(ncol[0], ncol[1], ncol[2], 0.4); ctx.set_line_width(2.0)
                        ctx.move_to(nodes[0][1], nodes[0][2]); ctx.line_to(nx, ny); ctx.stroke()
                    ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95); ctx.rectangle(nx - 85, ny - 25, 170, 50); ctx.fill()
                    ctx.set_source_rgb(*ncol); ctx.set_line_width(2.0); ctx.rectangle(nx - 85, ny - 25, 170, 50); ctx.stroke()
                    ctx.set_source_rgb(1.0, 1.0, 1.0); ctx.move_to(nx - 70, ny + 6); ctx.show_text(lbl)

            elif kind == "attention_quadratic":
                ctx.set_source_rgba(0.3, 0.4, 0.5, 0.4); ctx.set_line_width(2.0)
                ctx.move_to(x + 120, content_y + 360); ctx.line_to(x + w - 120, content_y + 360); ctx.stroke()
                ctx.move_to(x + 120, content_y + 360); ctx.line_to(x + 120, content_y + 40); ctx.stroke()
                ctx.set_source_rgb(1.0, 0.25, 0.35); ctx.set_line_width(4.0)
                ctx.move_to(x + 120, content_y + 355)
                for step in range(1, 21):
                    px = x + 120 + step * ((w - 240) / 20.0)
                    py = content_y + 355 - (step / 20.0)**2.2 * 280
                    ctx.line_to(px, py)
                ctx.stroke()
                ctx.set_font_size(18); ctx.move_to(x + w - 420, content_y + 80); ctx.show_text("Standard Transformer: O(N²) Exploding")
                ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.move_to(x + 120, content_y + 320); ctx.line_to(x + w - 120, content_y + 320); ctx.stroke()
                ctx.move_to(x + w - 420, content_y + 300); ctx.show_text("billion-context: O(1) Constant Steady-State")

            elif kind == "lost_middle":
                ctx.set_font_size(17); ctx.set_source_rgb(0.9, 0.95, 1.0)
                ctx.move_to(x + 80, content_y + 40); ctx.show_text("Attention Retention: High at Head & Tail, Lost in the Middle")
                ctx.set_source_rgb(1.0, 0.25, 0.35); ctx.set_line_width(4.0)
                ctx.move_to(x + 100, content_y + 100)
                for step in range(21):
                    prog = step / 20.0; px = x + 100 + prog * (w - 200)
                    u = 4.0 * (prog - 0.5)**2; py = content_y + 340 - u * 200
                    ctx.line_to(px, py)
                ctx.stroke()
                ctx.set_font_size(15); ctx.set_source_rgb(1.0, 0.4, 0.4)
                ctx.move_to(dcx - 110, content_y + 360); ctx.show_text("⚠️ 500k Tokens: Critical Instructions Lost")

            elif kind == "token_sea":
                ctx.set_font_size(16); ctx.set_source_rgba(0.4, 0.5, 0.6, 0.7)
                for r in range(6):
                    ry = content_y + 60 + r * 50
                    ctx.move_to(x + 60, ry); ctx.show_text("0x4F92 [RAW_LOG] " * 7)
                ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95); ctx.rectangle(dcx - 220, dcy - 30, 440, 60); ctx.fill()
                ctx.set_source_rgb(1.0, 0.3, 0.4); ctx.set_line_width(2.0); ctx.rectangle(dcx - 220, dcy - 30, 440, 60); ctx.stroke()
                ctx.set_font_size(18); ctx.move_to(dcx - 200, dcy + 6); ctx.show_text("DILUTED: 'Never drop invariants'")

            elif kind == "resend_loop":
                ctx.set_font_size(18)
                ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95); ctx.rectangle(x + 100, dcy - 50, 240, 100); ctx.fill()
                ctx.set_source_rgb(0.0, 0.95, 1.0); ctx.rectangle(x + 100, dcy - 50, 240, 100); ctx.stroke()
                ctx.move_to(x + 120, dcy + 5); ctx.show_text("Developer Agent")
                ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95); ctx.rectangle(x + w - 340, dcy - 50, 240, 100); ctx.fill()
                ctx.set_source_rgb(1.0, 0.8, 0.2); ctx.rectangle(x + w - 340, dcy - 50, 240, 100); ctx.stroke()
                ctx.move_to(x + w - 310, dcy + 5); ctx.show_text("Cloud LLM API")
                ctx.set_source_rgb(1.0, 0.25, 0.35); ctx.set_line_width(3.0)
                ctx.move_to(x + 340, dcy - 20); ctx.line_to(x + w - 340, dcy - 20); ctx.stroke()
                ctx.move_to(x + w - 340, dcy + 20); ctx.line_to(x + 340, dcy + 20); ctx.stroke()
                ctx.set_font_size(15); ctx.set_source_rgb(1.0, 0.3, 0.4)
                ctx.move_to(dcx - 140, dcy - 30); ctx.show_text("RE-SENDING 80,000 TOKENS CUMULATIVE ➡️")
                ctx.move_to(dcx - 120, dcy + 45); ctx.show_text("⬅️ RESPONSE + INLINE PROMPT COST")

            elif kind == "naive_truncation":
                for blk in range(5):
                    bx = x + 100 + blk * 260; by = content_y + 140
                    if blk < 3:
                        ctx.set_source_rgba(0.2, 0.05, 0.08, 0.9); ctx.rectangle(bx, by, 220, 100); ctx.fill()
                        ctx.set_source_rgb(1.0, 0.3, 0.4); ctx.rectangle(bx, by, 220, 100); ctx.stroke()
                        ctx.set_font_size(16); ctx.move_to(bx + 20, by + 45); ctx.show_text(f"Turn {blk*5+1}-{blk*5+5}")
                        ctx.set_source_rgb(1.0, 0.4, 0.4); ctx.move_to(bx + 20, by + 80); ctx.show_text("[LOST/TRUNCATED]")
                    else:
                        ctx.set_source_rgba(0.04, 0.10, 0.18, 0.9); ctx.rectangle(bx, by, 220, 100); ctx.fill()
                        ctx.set_source_rgb(0.0, 0.9, 1.0); ctx.rectangle(bx, by, 220, 100); ctx.stroke()
                        ctx.set_font_size(16); ctx.move_to(bx + 20, by + 45); ctx.show_text(f"Turn {blk*5+1}-{blk*5+5}")
                        ctx.move_to(bx + 20, by + 80); ctx.show_text("[Active Window]")

            elif kind == "proxy_seam":
                stages = [
                    ("1. AGENT CLI", "Claude Code / Pi / Custom Agent", (0.0, 0.9, 1.0)),
                    ("2. PROXY LAYER", "billion-context (127.0.0.1:8080)", (0.2, 1.0, 0.6)),
                    ("3. TARGET LLM", "Anthropic / DeepSeek / OpenAI", (0.85, 0.4, 1.0))
                ]
                for s_idx, (s_title, s_sub, s_col) in enumerate(stages):
                    sx = x + 80 + s_idx * 460; sy = content_y + 100
                    ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95); ctx.rectangle(sx, sy, 380, 140); ctx.fill()
                    ctx.set_source_rgb(*s_col); ctx.set_line_width(2.0); ctx.rectangle(sx, sy, 380, 140); ctx.stroke()
                    ctx.set_font_size(20); ctx.move_to(sx + 30, sy + 50); ctx.show_text(s_title)
                    ctx.set_font_size(14); ctx.set_source_rgb(0.9, 0.95, 1.0); ctx.move_to(sx + 30, sy + 95); ctx.show_text(s_sub)
                    if s_idx < 2:
                        ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.move_to(sx + 380, sy + 70); ctx.line_to(sx + 460, sy + 70); ctx.stroke()

            elif kind == "host_matrix":
                hosts = [
                    ("Claude Code", "Supported natively via claude prefix alias", "✅ FULL PASS"),
                    ("Pi Coding Agent", "Direct CLI injection with zero modifications", "✅ FULL PASS"),
                    ("OpenCodeInterpreter", "Standard OpenAI wire proxy compatible", "✅ FULL PASS"),
                    ("Custom Python/Rust Swarms", "Direct ACP tool function calling API", "✅ FULL PASS")
                ]
                for h_idx, (h_name, h_desc, h_stat) in enumerate(hosts):
                    hy = content_y + 50 + h_idx * 80
                    ctx.set_source_rgba(0.04, 0.08, 0.14, 0.9); ctx.rectangle(x + 60, hy, w - 120, 60); ctx.fill()
                    ctx.set_source_rgb(0.0, 0.95, 1.0); ctx.rectangle(x + 60, hy, w - 120, 60); ctx.stroke()
                    ctx.set_font_size(18); ctx.set_source_rgb(1.0, 1.0, 1.0); ctx.move_to(x + 90, hy + 38); ctx.show_text(h_name)
                    ctx.set_font_size(14); ctx.set_source_rgb(0.7, 0.8, 0.9); ctx.move_to(x + 400, hy + 38); ctx.show_text(h_desc)
                    ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.move_to(x + w - 240, hy + 38); ctx.show_text(h_stat)

            elif kind == "memory_iceberg":
                ctx.set_font_size(20)
                ctx.set_source_rgba(0.0, 0.8, 1.0, 0.15); ctx.rectangle(x + 60, content_y + 20, w - 120, 130); ctx.fill()
                ctx.set_source_rgb(0.0, 0.95, 1.0); ctx.move_to(x + 90, content_y + 70); ctx.show_text("ACTIVE CONTEXT WINDOW (10% Tip: 100k Tokens)")
                ctx.set_font_size(14); ctx.set_source_rgb(0.9, 0.95, 1.0); ctx.move_to(x + 90, content_y + 110); ctx.show_text("Working reasoning frames, immediate scratchpads, active AST targets")
                ctx.set_source_rgba(0.2, 1.0, 0.6, 0.8); ctx.set_line_width(3.0)
                ctx.move_to(x + 60, content_y + 160); ctx.line_to(x + w - 60, content_y + 160); ctx.stroke()
                ctx.set_source_rgba(0.02, 0.05, 0.12, 0.85); ctx.rectangle(x + 60, content_y + 165, w - 120, 200); ctx.fill()
                ctx.set_font_size(20); ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.move_to(x + 90, content_y + 230); ctx.show_text("SQLITE STORAGE VAULT (90% Submerged: Billions of Tokens)")
                ctx.set_font_size(14); ctx.set_source_rgb(0.8, 0.9, 0.95); ctx.move_to(x + 90, content_y + 270); ctx.show_text("Folded blocks, exact variable names, verified decisions, stack traces")

            elif kind == "cache_invariant":
                ctx.set_font_size(16)
                ctx.set_source_rgba(0.03, 0.06, 0.12, 0.95); ctx.rectangle(x + 60, content_y + 40, w - 120, 100); ctx.fill()
                ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.rectangle(x + 60, content_y + 40, w - 120, 100); ctx.stroke()
                ctx.move_to(x + 90, content_y + 80); ctx.show_text("CRYPTOGRAPHIC PREFIX HASH: SHA256[System + Invariants + Tools]")
                ctx.set_source_rgb(0.0, 0.95, 1.0); ctx.move_to(x + 90, content_y + 115); ctx.show_text("✅ ZERO INLINE MUTATIONS -> 98.6% Sustained Provider Cache Hit")
                ctx.set_source_rgba(0.08, 0.12, 0.20, 0.95); ctx.rectangle(x + 60, content_y + 170, w - 120, 100); ctx.fill()
                ctx.set_source_rgb(0.0, 0.8, 1.0); ctx.rectangle(x + 60, content_y + 170, w - 120, 100); ctx.stroke()
                ctx.set_source_rgb(0.95, 0.95, 1.0); ctx.move_to(x + 90, content_y + 210); ctx.show_text("DYNAMIC FOLDED SUMMARY TAIL: Appended strictly to end of prompt")
                ctx.set_source_rgb(0.8, 0.85, 0.9); ctx.move_to(x + 90, content_y + 245); ctx.show_text("Eliminates prefix hash bust, saving 90% of token billing on Anthropic & DeepSeek")

            elif kind == "contextbench_chart":
                bars = [
                    ("billion-context", 0.98, "Rank #1: -58.3% Cost Reduction (100% Survival)", (0.2, 1.0, 0.6)),
                    ("DeepSeek V4.1 Flash RAG", 0.65, "65.0% Context Retention (-71% Leak)", (0.0, 0.8, 1.0)),
                    ("Full Context Baseline", 0.42, "High Cost & Fatal Degradation", (1.0, 0.3, 0.4))
                ]
                for b_idx, (b_name, b_val, b_desc, b_col) in enumerate(bars):
                    by = content_y + 60 + b_idx * 110
                    ctx.set_font_size(18); ctx.set_source_rgb(0.96, 0.96, 0.98); ctx.move_to(x + 80, by); ctx.show_text(b_name)
                    ctx.set_source_rgba(0.15, 0.20, 0.28, 0.9); ctx.rectangle(x + 80, by + 15, w - 160, 32); ctx.fill()
                    ctx.set_source_rgb(*b_col); ctx.rectangle(x + 80, by + 15, (w - 160) * b_val, 32); ctx.fill()
                    ctx.set_font_size(14); ctx.set_source_rgb(1.0, 1.0, 1.0); ctx.move_to(x + 95, by + 37); ctx.show_text(b_desc)

            elif kind == "survival_chart":
                ctx.set_font_size(20)
                ctx.set_source_rgba(0.04, 0.12, 0.08, 0.95); ctx.rectangle(x + 60, content_y + 40, w - 120, 120); ctx.fill()
                ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.rectangle(x + 60, content_y + 40, w - 120, 120); ctx.stroke()
                ctx.move_to(x + 90, content_y + 90); ctx.show_text("billion-context: 100% SURVIVAL (0 Crashes across 174,327 Calls)")
                ctx.set_font_size(15); ctx.set_source_rgb(0.9, 0.95, 1.0); ctx.move_to(x + 90, content_y + 130); ctx.show_text("Completed 4.5-month evaluation marathon with zero amnesia or TTL aborts")

                ctx.set_source_rgba(0.15, 0.04, 0.06, 0.95); ctx.rectangle(x + 60, content_y + 190, w - 120, 120); ctx.fill()
                ctx.set_source_rgb(1.0, 0.3, 0.4); ctx.rectangle(x + 60, content_y + 190, w - 120, 120); ctx.stroke()
                ctx.set_font_size(20); ctx.move_to(x + 90, content_y + 240); ctx.show_text("Standard Full Context: FAILED 199 OUT OF 199 RUNS")
                ctx.set_font_size(15); ctx.set_source_rgb(0.9, 0.9, 0.95); ctx.move_to(x + 90, content_y + 280); ctx.show_text("Crashed due to TTL expiration, rate-limit explosions, and context amnesia")

            else:
                nodes = ["RAW TURNS", "PROXY INTERCEPT", "DYNAMIC FOLD", "SQLITE BACKING", "PREFIX CACHE"]
                nw = 220
                for n_idx, n_text in enumerate(nodes):
                    nx = x + 80 + n_idx * (nw + 50); ny = dcy - 30
                    ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95); ctx.rectangle(nx, ny, nw, 60); ctx.fill()
                    ctx.set_source_rgb(0.0, 0.95, 1.0); ctx.set_line_width(2.0); ctx.rectangle(nx, ny, nw, 60); ctx.stroke()
                    ctx.set_font_size(14); ctx.set_source_rgb(1.0, 1.0, 1.0); ctx.move_to(nx + 18, ny + 36); ctx.show_text(n_text)
                    if n_idx < len(nodes) - 1:
                        ctx.set_source_rgb(0.2, 1.0, 0.6); ctx.move_to(nx + nw, ny + 30); ctx.line_to(nx + nw + 50, ny + 30); ctx.stroke()

    ctx.restore()

    if is_cut:
        alpha = (1.0 - beat_t / 0.18) * 0.22
        ctx.save()
        ctx.set_source_rgba(0.0, 0.95, 1.0, alpha)
        ctx.rectangle(0, 0, 1920, 1080)
        ctx.fill()
        ctx.restore()

    return action, mood, pos, stick_scale
