# AUTONOMOUS DEV.TO SEO ARTICLE PUBLISHER

## 1. Context & Activation Scope
Triggered when authoring, scheduling, or automating technical articles, Dev.to publications, SEO backlinks, and autonomous developer advocacy for Flowork OS and GitHub repositories.

## 2. Mandatory Behavioral Invariants
- **Dynamic Path Resolution:** Always resolve user downloads dynamically via `$HOME/Downloads/devto.txt` or `$HOME/Downloads/devto`. NEVER hardcode personal usernames (`/home/username`).
- **Deduplication Check:** Before generating or posting an article, MUST inspect `devto.txt` for previously published titles. Never publish duplicate or overlapping topics.
- **Direct Live Publication:** All API posts via `flowork-devto-publisher` MUST specify `"published": true` for immediate publication. Never leave articles in draft status.
- **Authentic Engineering Tone:** Highlight genuine systems architecture (Landlock LSM, POSIX Exit Code 0, Micro-VM direct X11 windowing, Live USB hybrid) with natural backlinks to `https://floworkos.com/` and `https://github.com/flowork-os/flowork-os`. Avoid promotional buzzwords or exaggerated claims.
- **Active Watchdog Coordination:** The active trigger in `/opt/floworkos/system/triger/devto_seo_publisher/` runs once daily between 21:00 and 02:00 at a randomized time, only if `devto.txt` exists. On publication, emit high-priority alert to `/tmp/flowork_active_trigger.json`.

## 3. Strict Prohibitions
- NEVER expose raw Dev.to API tokens in public logs, chat responses, or unmasked telemetry.
- NEVER overwrite existing title history in `devto.txt` when appending new entries.
- NEVER execute publications outside the randomized night window unless explicitly forced via `--publish`.
