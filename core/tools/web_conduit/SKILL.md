---
name: web-conduit-bridge
description: Master operational playbook for configuring, executing, and troubleshooting the Flowork Sovereign Web-Conduit bridging web chatbots directly to local OS terminal and desktop runtime.
domain: os_doctrine
keywords:
  - flowork
  - conduit
  - bridge
  - gemini
  - claude
  - chatgpt
  - extension
  - terminal
  - execution
  - daemon
  - landlock
  - headless
  - handsfree
  - browser
  - sysd
  - telemetry
  - crystal
  - glass
  - autonomous
  - sovereign
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# ⚡ Flowork Sovereign Web-Conduit Operational Playbook

## 1. Objective
Establish an autonomous, hands-free execution bridge connecting web-based generative AI interfaces (Google Gemini Web, Anthropic Claude, OpenAI ChatGPT) to native Flowork OS daemon services (`flowork-sysd` :18090). This enables web chatbots to execute bash commands, query desktop GUI graphs, manipulate files with atomic rollback, and interact with the local operating system without requiring external paid API keys or manual terminal copy-pasting.

## 2. Prerequisites
1. Flowork OS (Linux 7.3.0 Rust) with system daemon `flowork-sysd` running on port 18090.
2. Web Conduit extension located in `/opt/floworkos/apps/flowork-web-conduit`.
3. Native binaries installed:
   - `/opt/floworkos/bin/flowork-web-conduit`
   - `/opt/floworkos/bin/flowork-tool-runner`
4. Chromium-based browser (Google Chrome or Chromium) installed in system PATH.
5. Allowed local origins configured in `flowork-sysd` CORS settings.

## 3. Standard Operating Procedure

### Step 1: Verify Conduit & Daemon Health
Before starting browser sessions, verify local daemon availability and extension directory integrity:
```bash
flowork-web-conduit status
```
Ensure `flowork-sysd` reports `ONLINE` and Manifest V3 is reported as `INSTALLED`.

### Step 2: Launch Web Chatbot with Conduit
Launch Google Chrome loaded with the Sovereign Conduit extension directed to the target web chatbot:
```bash
flowork-web-conduit launch gemini
```
Alternative targets include `claude` and `chatgpt`.

### Step 3: Inject Sovereign Controller Instructions
In the web chatbot UI, click **⚡ Inject Prompt** from the floating Pure Crystal Glass HUD widget, or copy the system prompt via CLI:
```bash
flowork-web-conduit prompt
```
Paste this prompt into the chatbot conversation. The chatbot will format all execution commands inside ` ```flowork-exec ` code blocks or `[FLOWORK_CMD]` tags.

### Step 4: Autonomous Command Execution & Feedback Loop
1. When the assistant completes streaming a response containing command blocks, the in-page content script intercepts the payload.
2. The command is transmitted via background service worker to `http://127.0.0.1:18090/api/agent/terminal/exec`.
3. The result is returned with exit code and timing telemetry, then automatically typed back into the prompt textarea and submitted.
4. The web chatbot inspects the output and proceeds recursively to the next operational step.

## 4. Verification
Execute the following verification steps to ensure Exit Code 0 across the conduit bridge subsystem:

```bash
# 1. Verify CLI status and manifest integrity
flowork-web-conduit status | grep -q "ONLINE"

# 2. Verify deterministic simulation cycle
flowork-web-conduit test-exec "uname -r" | grep -q "7.3.0"

# 3. Verify tool runner dispatch
echo '{"action": "test_exec", "command": "id"}' | /opt/floworkos/tools/web_conduit/run | grep -q "uid="
```

## 5. Failure Modes
1. **System Daemon Offline (`flowork-sysd`):** If sysd is not active on port 18090, start or restart the service via `systemctl --user restart flowork-sysd`.
2. **Untrusted Origin / CORS Block:** If requests from the browser extension are rejected, verify `is_trusted_local_origin` in `routes.rs` contains `chrome-extension://`.
3. **Chat Input Selector Desynchronization:** If web UI changes class names on `gemini.google.com`, inspect DOM attributes and fallback to standard contenteditable or textarea selectors.
4. **Command Execution Timeout:** Long-running compiles or background tasks should be launched asynchronously with nohup or background daemon flags.
