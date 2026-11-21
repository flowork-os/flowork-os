#!/usr/bin/env python3
"""
🎬 OPENCLAW SENTENCE-BEAT STORYTELLING CADENCE DIRECTOR
Maps all 30 sentence cues across 6 chapters to distinct narrative visuals,
emotional stickman poses, dynamic kinetic diagrams, and authentic OpenClaw GitHub proof.
Strictly adheres to High-Contrast Inversion (Non-white bright background + Dark matte cards & Stickman).
"""

import math
import cairo

OPENCLAW_BEATS = {
    # --------------------------------------------------------------------------
    # CHAPTER 1: THE CLOUD SUBSCRIPTION TRAP (7 BEATS)
    # --------------------------------------------------------------------------
    1: [
        {
            "cue": 1,
            "title": "THE BIG TECH PROMISE (2024)",
            "cat": "PROMISE",
            "type": "quote",
            "quote": "AI agents will liberate every software engineer\nfrom repetitive busywork forever.",
            "author": "Frontier AI Cloud Keynote (2024)",
            "action": "walking",
            "mood": "confident",
            "pos": (380, 720),
            "zoom": 1.0,
            "bg": "kraft"
        },
        {
            "cue": 2,
            "title": "THE BRUTAL REALITY (2026)",
            "cat": "CRISIS",
            "type": "metric",
            "stat": "CONCRETE WALL",
            "sub": "Developers locked into rigid, expensive cloud agent silos",
            "col": (1.0, 0.25, 0.35),
            "action": "confused",
            "mood": "confused",
            "pos": (1550, 720),
            "zoom": 1.15,
            "bg": "cream"
        },
        {
            "cue": 3,
            "title": "PROPRIETARY SAAS PRICING",
            "cat": "PRICING",
            "type": "comparison",
            "left": "Cloud Agent SaaS: $200 / User / Month + Token Markups",
            "right": "Local Open Source: 100% Free on Your Own Hardware",
            "action": "leaning",
            "mood": "confident",
            "pos": (1550, 720),
            "zoom": 1.0,
            "bg": "sage"
        },
        {
            "cue": 4,
            "title": "CREDENTIAL & DATA EXFILTRATION",
            "cat": "LEAK",
            "type": "incident",
            "kind": "data_leak_warning",
            "action": "shocked",
            "mood": "shocked",
            "pos": (960, 720),
            "zoom": 1.4,
            "bg": "amber"
        },
        {
            "cue": 5,
            "title": "INTERNET FLICKER = AGENT DEATH",
            "cat": "FAILURE",
            "type": "code",
            "file": "cloud_agent_crash.log",
            "lines": [
                "[FATAL] 504 Gateway Timeout: cloud-agent-api.corp.com",
                "[WARN] Connection dropped mid-refactor! All 48 turns lost.",
                "-- Cloud vendor state vanished. Local workspace corrupted.",
                "Process terminated with Exit Code 137 (KILLED)"
            ],
            "action": "splat",
            "mood": "shocked",
            "pos": (1550, 720),
            "zoom": 1.0,
            "bg": "slate"
        },
        {
            "cue": 6,
            "title": "VENDOR LOCK-IN & RATE HIKES",
            "cat": "FINANCIAL",
            "type": "metric",
            "stat": "$2,400.00 / YR",
            "sub": "Mandatory annual enterprise seat fee per engineer",
            "col": (1.0, 0.3, 0.35),
            "action": "shocked",
            "mood": "shocked",
            "pos": (1550, 720),
            "zoom": 1.8, # Dynamic camera punch-in
            "bg": "kraft"
        },
        {
            "cue": 7,
            "title": "THE WALLED GARDEN TRAP",
            "cat": "VERDICT",
            "type": "quote",
            "quote": "Developers were paying thousands for the illusion of automation,\nwhile trapped inside someone else's walled garden.",
            "author": "Dr. Flow // Flowork OS Research",
            "action": "standing",
            "mood": "confident",
            "pos": (960, 720),
            "zoom": 1.0,
            "bg": "cream"
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 2: THE LOBSTER RISES // PETER STEINBERGER & MOLTY (6 BEATS)
    # --------------------------------------------------------------------------
    2: [
        {
            "cue": 1,
            "title": "THE REBEL FOUNDER // PETER STEINBERGER",
            "cat": "ORIGIN",
            "type": "code",
            "file": "soul.md",
            "lines": [
                "// OpenClaw Genesis: Built out of pure frustration with cloud agents",
                "const creator = 'Peter Steinberger (@steipete)';",
                "const companion = 'Molty the Space Lobster 🦞';",
                "const mission = 'The AI that really does things. Any OS. The lobster way.';"
            ],
            "action": "bouncing",
            "mood": "celebrating",
            "pos": (1550, 720),
            "zoom": 1.0,
            "bg": "sage"
        },
        {
            "cue": 2,
            "title": "THE MISSION: 100% LOCAL FREEDOM",
            "cat": "MISSION",
            "type": "comparison",
            "left": "Cloud Agents: Closed, Untrusted, Paywalled, Telemetry Tracked",
            "right": "OpenClaw: 100% Local Hardware, Zero Telemetry, Free MIT",
            "action": "salto",
            "mood": "celebrating",
            "pos": (960, 720),
            "zoom": 1.25,
            "bg": "amber"
        },
        {
            "cue": 3,
            "title": "THE SEISMIC REPO LAUNCH",
            "cat": "LAUNCH",
            "type": "metric",
            "stat": "395,000+ STARS",
            "sub": "One of the fastest growing open-source repositories in GitHub history",
            "col": (0.0, 1.0, 0.4),
            "action": "celebrating",
            "mood": "celebrating",
            "pos": (1550, 720),
            "zoom": 1.5,
            "bg": "slate"
        },
        {
            "cue": 4,
            "title": "THE INDEPENDENT FOUNDATION",
            "cat": "GOVERNANCE",
            "type": "quote",
            "quote": "OpenClaw is stewarded by an independent 501(c)(3) foundation.\nNo paid tier, no token, no corporate takeover.",
            "author": "OpenClaw Foundation Charter",
            "action": "leaning",
            "mood": "confident",
            "pos": (380, 720),
            "zoom": 1.0,
            "bg": "kraft"
        },
        {
            "cue": 5,
            "title": "GLOBAL SPONSOR ECOSYSTEM",
            "cat": "SPONSORS",
            "type": "code",
            "file": "sponsors.json",
            "lines": [
                "// Backed by donors who believe in local personal sovereignty:",
                "const donors = ['Amazon', 'OpenAI', 'NVIDIA', 'Red Hat', 'Vercel'];",
                "const governance = '100% Independent Non-Profit Foundation';",
                "console.log('Zero corporate telemetry. Fully community owned.');"
            ],
            "action": "sitting_laptop",
            "mood": "confident",
            "pos": (1550, 720),
            "zoom": 1.0,
            "bg": "cream"
        },
        {
            "cue": 6,
            "title": "THE LOBSTER PHENOMENON",
            "cat": "MOMENTUM",
            "type": "metric",
            "stat": "THE LOBSTER WAY 🦞",
            "sub": "Cross-platform autonomy without corporate cloud surveillance",
            "col": (1.0, 0.4, 0.2),
            "action": "hover",
            "mood": "laser",
            "pos": (960, 680),
            "zoom": 1.2,
            "bg": "sage"
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 3: GATEWAY PORT 18789 // ZERO-LEAK LOCAL ARCHITECTURE (5 BEATS)
    # --------------------------------------------------------------------------
    3: [
        {
            "cue": 1,
            "title": "THE GATEWAY NERVE // PORT 18789",
            "cat": "GATEWAY",
            "type": "diagram",
            "kind": "gateway_architecture",
            "action": "thinking",
            "mood": "thinking",
            "pos": (380, 720),
            "zoom": 1.0,
            "bg": "amber"
        },
        {
            "cue": 2,
            "title": "SOVEREIGN CONTROL PLANE",
            "cat": "ARCHITECTURE",
            "type": "code",
            "file": "gateway_daemon.ts",
            "lines": [
                "// Bound strictly to loopback: 127.0.0.1:18789",
                "const gateway = new OpenClawGateway({ port: 18789, host: '127.0.0.1' });",
                "await gateway.listen();",
                "console.log('Gateway active: Local state stays on local NVMe.');"
            ],
            "action": "presenting",
            "mood": "confident",
            "pos": (1550, 720),
            "zoom": 1.15,
            "bg": "slate"
        },
        {
            "cue": 3,
            "title": "EMBEDDED SQLITE STATE STORE",
            "cat": "DATABASE",
            "type": "metric",
            "stat": "LOCAL SQLITE",
            "sub": "Sessions, nodes, credentials & memory encrypted on your local drive",
            "col": (0.2, 0.85, 1.0),
            "action": "heavy_lifting",
            "mood": "strained",
            "pos": (960, 720),
            "zoom": 1.0,
            "bg": "kraft"
        },
        {
            "cue": 4,
            "title": "LOW-LATENCY WEBSOCKET FABRIC",
            "cat": "IPC",
            "type": "diagram",
            "kind": "websocket_bus",
            "action": "walking",
            "mood": "confident",
            "pos": (380, 720),
            "zoom": 1.0,
            "bg": "cream"
        },
        {
            "cue": 5,
            "title": "PLUGGABLE BRAIN HARNESSES",
            "cat": "MODELS",
            "type": "comparison",
            "left": "Hosted Models: Claude 3.7, GPT-4o, DeepSeek V3",
            "right": "Local Offline: Ollama, Llama 3.3, Qwen 2.5 (Zero API Cost)",
            "action": "camera_zoom", # Dynamic Macro Camera Zoom (2.5x)
            "mood": "confident",
            "pos": (960, 720),
            "zoom": 2.2,
            "bg": "sage"
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 4: THE 20+ CHANNEL OMNI-NERVE // WHATSAPP TO TERMINAL (4 BEATS)
    # --------------------------------------------------------------------------
    4: [
        {
            "cue": 1,
            "title": "ERADICATING DESKTOP FRICTION",
            "cat": "CHANNELS",
            "type": "metric",
            "stat": "20+ CHANNELS",
            "sub": "WhatsApp, Telegram, Slack, Discord, iMessage, Signal, Google Chat",
            "col": (0.0, 1.0, 0.4),
            "action": "hanging", # Hanging playfully from WhatsApp card!
            "mood": "cheeky",
            "pos": (1500, 100),
            "zoom": 1.0,
            "bg": "amber"
        },
        {
            "cue": 2,
            "title": "CROSS-PLATFORM INTEGRATION",
            "cat": "DISPATCH",
            "type": "code",
            "file": "channel_bridge.ts",
            "lines": [
                "// Intercept WhatsApp Voice Note / Telegram Message:",
                "const incoming = await channel.receive('whatsapp:+14155550199');",
                "const task = await agent.plan(incoming.transcription);",
                "await terminal.execute(task.shellCommand); // Run locally!"
            ],
            "action": "sitting_laptop",
            "mood": "confident",
            "pos": (1550, 720),
            "zoom": 1.0,
            "bg": "slate"
        },
        {
            "cue": 3,
            "title": "AUTOMATING FROM YOUR PHONE",
            "cat": "WORKFLOW",
            "type": "diagram",
            "kind": "mobile_to_git",
            "action": "sprint", # Turbo sprint run
            "mood": "laser",
            "pos": (960, 720),
            "zoom": 1.2,
            "bg": "kraft"
        },
        {
            "cue": 4,
            "title": "ZERO EXPOSED PORTS",
            "cat": "SECURITY",
            "type": "quote",
            "quote": "Your entire computing environment becomes accessible from your phone\nwithout opening inbound router ports or paying intermediaries.",
            "author": "OpenClaw Architectural Manual",
            "action": "leaning",
            "mood": "confident",
            "pos": (380, 720),
            "zoom": 1.0,
            "bg": "cream"
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 5: ZERO-TRUST PAIRING // IMMUNITY TO PROMPT INJECTION (4 BEATS)
    # --------------------------------------------------------------------------
    5: [
        {
            "cue": 1,
            "title": "THE CHAT SECURITY DILEMMA",
            "cat": "THREAT",
            "type": "metric",
            "stat": "PROMPT INJECTION",
            "sub": "Untrusted strangers messaging your bot cannot execute arbitrary shell code",
            "col": (1.0, 0.25, 0.35),
            "action": "shocked",
            "mood": "shocked",
            "pos": (1550, 720),
            "zoom": 1.15,
            "bg": "sage"
        },
        {
            "cue": 2,
            "title": "TWO-TIER PAIRING ARCHITECTURE",
            "cat": "DEFENSE",
            "type": "code",
            "file": "pairing_auth.ts",
            "lines": [
                "// Unknown sender detected on WhatsApp:",
                "const pairing = await gateway.requestPairing({ channel: 'whatsapp', senderId });",
                "console.log(`[ALERT] Run: openclaw pairing approve whatsapp ${pairing.code}`);",
                "// Zero execution privileges granted until explicit operator approval"
            ],
            "action": "laser_pointer",
            "mood": "laser",
            "pos": (380, 720),
            "zoom": 1.1,
            "bg": "amber"
        },
        {
            "cue": 3,
            "title": "COMMAND SURFACE QUARANTINE",
            "cat": "POLICY",
            "type": "diagram",
            "kind": "pairing_wall",
            "action": "peeking", # Peeking from bottom border
            "mood": "cheeky",
            "pos": (960, 950),
            "zoom": 1.0,
            "bg": "slate"
        },
        {
            "cue": 4,
            "title": "IRONCLAD EFFECTIVE PERMISSIONS",
            "cat": "ISOLATION",
            "type": "metric",
            "stat": "ZERO EFFECTIVE ACCESS",
            "sub": "Unapproved nodes and capability widenings are permanently sandboxed",
            "col": (0.0, 1.0, 0.4),
            "action": "camera_zoom", # 2.5x closeup
            "mood": "confident",
            "pos": (960, 720),
            "zoom": 2.4,
            "bg": "kraft"
        }
    ],

    # --------------------------------------------------------------------------
    # CHAPTER 6: THE SOVEREIGN AI ERA // THE LOBSTER REVOLUTION (4 BEATS)
    # --------------------------------------------------------------------------
    6: [
        {
            "cue": 1,
            "title": "THE INEVITABLE DESTINATION",
            "cat": "MANIFESTO",
            "type": "quote",
            "quote": "The ultimate destination of artificial intelligence\nis not giant cloud monopolies, but personal hardware sovereignty.",
            "author": "Open-Source Sovereign Movement",
            "action": "standing",
            "mood": "confident",
            "pos": (960, 720),
            "zoom": 1.0,
            "bg": "cream"
        },
        {
            "cue": 2,
            "title": "ZERO TELEMETRY BY DEFAULT",
            "cat": "SOVEREIGNTY",
            "type": "comparison",
            "left": "Big Tech: Continuous Prompt Logging & Model Training",
            "right": "OpenClaw + Flowork OS: 100% Private, Zero Telemetry, Offline Capable",
            "action": "bouncing",
            "mood": "celebrating",
            "pos": (1550, 720),
            "zoom": 1.1,
            "bg": "sage"
        },
        {
            "cue": 3,
            "title": "THE COMMUNITY FORCE",
            "cat": "COMMUNITY",
            "type": "metric",
            "stat": "COMMUNITY POWERED",
            "sub": "Thousands of contributors advancing the global open AI ecosystem",
            "col": (0.0, 1.0, 0.5),
            "action": "hover",
            "mood": "laser",
            "pos": (960, 680),
            "zoom": 1.25,
            "bg": "amber"
        },
        {
            "cue": 4,
            "title": "THE FUTURE IS SOVEREIGN",
            "cat": "FINALE",
            "type": "metric",
            "stat": "FLOWORK OS × OPENCLAW",
            "sub": "Living proof that the future belongs to open, local, and sovereign code",
            "col": (0.0, 1.0, 0.4),
            "action": "celebrating", # Epic Victory Jump with Confetti!
            "mood": "celebrating",
            "pos": (960, 720),
            "zoom": 1.0,
            "bg": "slate"
        }
    ]
}
