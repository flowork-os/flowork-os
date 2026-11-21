# SOCIAL AUTO UPLOAD STUDIO DIRECTIVE

## 1. Context & Activation Scope
Applies when orchestrating video publishing, managing multi-account social media sessions (YouTube, TikTok, Instagram, Douyin, Bilibili), or interacting with the Social Auto Upload Studio GUI (`sau`, `social-auto-upload`, `social_publisher`).

## 2. Mandatory Behavioral Invariants
- Enforce unified session cookies under `/opt/floworkos/apps/social-auto-upload/cookies/<platform>_<account>.json`. Both GUI and autonomous agent must reuse shared cookie files.
- Validate account session health via `sau <platform> check --account <account>` before publishing.
- Store rendered and transcoded social media video assets exclusively under `/opt/floworkos/documents/`.
- Provide multi-account targeting (`--account <name>`) to prevent cross-account credential leakage.
- For background agent tasks, invoke `headless=True` to preserve user display space.
- Record every automated publication in `/opt/floworkos/apps/social-auto-upload/db/upload_history.json` for bidirectional visibility with the desktop UI.

## 3. Strict Prohibitions
- Never leak, print, or transmit raw storage state cookies or authentication credentials in logs.
- Never write media or application files outside canonical `/opt/floworkos/` root paths.
- Never hardcode personal username paths; resolve dynamically via `$HOME`.
- Never claim upload completion without empirical Exit Code 0 verification.
