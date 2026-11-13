---
name: social_publisher
version: 1.0.0
description: Autonomous multi-platform video publishing engine (YouTube, TikTok, Douyin, Bilibili, Instagram, WeChat Channels) via anti-detect patchright browser automation.
activation: conditional
keywords:
  - social_publisher
  - social_auto_upload
  - video_upload
  - youtube_upload
  - tiktok_upload
  - douyin_upload
  - bilibili_upload
  - instagram_upload
  - sau_cli
  - video_distribution
  - faceless_channel
  - content_automation
  - auto_publisher
  - browser_automation
  - patchright
  - storage_state
  - video_marketing
  - automated_publishing
  - multi_platform_distribution
  - flowork_publisher
domain: automation
---

# 🚀 SOCIAL PUBLISHER SOVEREIGN TOOL SOP

## 1. Trigger Scenarios
Invoke `social_publisher` when:
- The user requests uploading, distributing, or publishing video files to YouTube, TikTok, Douyin, Bilibili, Instagram, or other supported social media platforms.
- An autonomous workflow (e.g. `blender-mastering` or `stickman-video-director`) has rendered a finished video in `/opt/floworkos/documents/` and needs to be deployed to public channels.
- Verifying whether an account session or cookie is active (`check_status`).
- Initiating an interactive login session (`login`).

## 2. Input Interface & Execution Pattern
The tool accepts JSON input with the following schema:
```json
{
  "action": "upload_video",
  "platform": "youtube",
  "account": "main",
  "file_path": "/opt/floworkos/documents/output.mp4",
  "title": "Flowork OS Sovereign Agent Demo",
  "description": "Showcasing autonomous video generation and publication.",
  "tags": ["flowork", "linux", "ai"],
  "visibility": "public"
}
```

## 3. Operating Guidelines & Edge Cases
1. **Pre-flight Session Verification:** Always run `check_status` before initiating an automated batch upload to ensure the session cookie has not expired.
2. **Path Integrity:** Ensure `file_path` points to a fully rendered and verified media file (Exit Code 0 on `ffmpeg -v error -i ... -f null -`).
3. **Desktop Interaction on Login:** If `action` is `login`, an interactive browser window will appear on the Flowork OS desktop display `:0` for QR code scanning or password entry.

## 4. Prohibitions & Anti-Patterns
1. NEVER upload corrupted, incomplete, or 0-byte video files.
2. NEVER hardcode API keys or credentials directly into parameters; authentication is managed via `storage_state` session profiles.
3. NEVER pass invalid timestamps in `schedule`. Use strictly `YYYY-MM-DD HH:MM`.

## 5. Recovery Protocols
- If `exit_code` indicates session expiry: notify user to run `login` action to refresh the session token.
- If upload fails due to network timeout: retry once with exponential backoff or verify network connectivity.
