---
name: social-auto-upload
description: Autonomous multi-platform social media video and content publishing playbook for YouTube, TikTok, Douyin, Bilibili, and Instagram using anti-detect browser automation.
domain: browser
keywords:
  - social_auto_upload
  - sau
  - youtube
  - tiktok
  - douyin
  - bilibili
  - instagram
  - browser_automation
  - patchright
  - playwright
  - video_publisher
  - creator_studio
  - headless_browser
  - cookie_authentication
  - content_distribution
  - stealth_automation
  - anti_detect
  - social_media
  - shorts
  - flowork_publisher
author: Flowork Architecture Board
version: 1.0.0
---

# ⚡ FLOWORK OS SOVEREIGN SKILL: SOCIAL AUTO UPLOAD & CONTENT DISTRIBUTION

## 1. Objective
Equip Mr. Flow with an autonomous, quota-immune Standard Operating Procedure (SOP) to authenticate, schedule, and distribute generated video assets (Stickman, Blender renders, system demonstrations, and vertical shorts) across major global and domestic social media networks (YouTube Shorts, TikTok, Douyin, Bilibili, Instagram, and Tencent Video Channels).
- Bypass restrictive official developer API quotas and mandatory enterprise verification processes.
- Automate Creator Studio interactions directly using anti-detect browser contexts (`patchright`).
- Maintain persistent authentication sessions through storage state cookie isolation.
- Coordinate end-to-end rendering, audio scoring, thumbnail generation, and multi-platform publishing.

## 2. Prerequisites & Tool Dependencies
1. **Flowork Sovereign Execution Instruments**:
   - `run_shell_command`: Execute `sau` CLI operations, session checks, and video distribution.
   - `social_publisher`: Native JSON tool interface (`/opt/floworkos/tools/social_publisher/run.py`).
   - `read_file` / `view_file`: Inspect video parameters, upload logs, and frame previews.
   - `flowork-sound-forge`: Procedural SFX audio scoring for social retention optimization.
2. **System Runtimes & Binaries**:
   - Python 3.12+ virtual environment located at `/opt/floworkos/apps/social-auto-upload/.venv`.
   - Patchright Chromium browser engine (`~/.cache/ms-playwright/chromium_headless_shell-1208`).
   - Global executable wrapper `sau` located at `/opt/floworkos/bin/sau`.
   - FFmpeg and FFprobe for video container inspection and transcode validation.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Authentication & Session Verification
Before triggering an automated upload batch, always verify that the target account session is valid:
```bash
sau <platform> check --account <account_name>
```
1. If output is `valid` with Exit Code 0: Proceed directly to publishing.
2. If output is `invalid` or cookie does not exist:
   - Initiate interactive login workflow on the active X11/Wayland display:
     ```bash
     sau <platform> login --account <account_name>
     ```
   - User signs in or scans QR code. The browser saves `cookies/<platform>_<account_name>.json`.

### Phase 2: Video Asset Preparation & Compliance
1. Ensure the video adheres to platform specifications (e.g. 9:16 vertical ratio `720x1280` or `1080x1920`, H.264 video codec, AAC audio, duration < 60s for Shorts/Reels).
2. Confirm file is stored in `/opt/floworkos/documents/` per the Universal Document Output Law.
3. Generate or locate the custom thumbnail frame (PNG/JPEG format).

### Phase 3: Autonomous Publishing Execution
Execute the upload via the native `social_publisher` tool or the `sau` CLI:
```bash
sau youtube upload-video \
  --account main \
  --file /opt/floworkos/documents/stickman_flowork_demo.mp4 \
  --title "Flowork OS Sovereign Agent Demo #Shorts" \
  --desc "Autonomous OS execution demo with Mr. Flow #Flowork #Linux #AI" \
  --tags "flowork,ai,linux,stickman,shorts" \
  --thumbnail /opt/floworkos/documents/stickman_preview.png \
  --visibility public
```

### Phase 4: Headless Background Operation
For recurring distribution pipelines, set `headless=True` to execute background browser uploads without occupying visible desktop real estate.

## 4. Verification & Validation
1. Verify session validity:
   ```bash
   sau youtube check --account main
   ```
   Must output `valid` with terminal Exit Code 0.
2. Verify tool invocation via JSON interface:
   ```bash
   echo '{"action": "check_status", "platform": "youtube", "account": "main"}' | /opt/floworkos/tools/social_publisher/run.py
   ```
   Must return valid JSON with `"success": true` and `"exit_code": 0`.
3. Verify video publishing completion log:
   - Confirm terminal output contains `[SUCCESS]` or `🥳 发布完成`.
   - Inspect Studio dashboard to ensure video is listed and processing checks are complete.

## 5. Failure Modes & Recovery Playbook
- **Failure Mode 1: Interstitial Browser Warning (Outdated Browser)**
  - *Symptom*: YouTube Studio shows unsupported browser notice or redirects away from studio dashboard.
  - *Recovery*: Ensure `DEFAULT_USER_AGENT` is configured with a modern Chrome build string (`Chrome/133.0.0.0+`) and URL includes `?approve_browser_access=true`.
- **Failure Mode 2: Session Expired / Token Revocation**
  - *Symptom*: `check` returns `invalid` or redirect hits `accounts.google.com` or login portal.
  - *Recovery*: Re-run `sau <platform> login --account <account>` to refresh storage state cookies.
- **Failure Mode 3: Upload Stall Mid-Stream**
  - *Symptom*: Browser closes prematurely while upload progress is below 100%.
  - *Recovery*: Ensure `_wait_upload_complete` is polling both localized ("Upload selesai", "Pemrosesan", "Checks") and standard progress indicators before triggering the publish button.

## 6. Prohibitions & Anti-Patterns
- **No Secret Leaks:** NEVER commit, export, or print raw cookie files containing session tokens (`cookies/*.json`).
- **No Blanket Formatting on Binaries:** Never run text transformation tools (`sed`, `dos2unix`) across `/opt/floworkos/bin/sau` or compiled binaries.
- **No Arbitrary Directories:** Never place media assets outside `/opt/floworkos/documents/` or applications outside `/opt/floworkos/apps/`.
