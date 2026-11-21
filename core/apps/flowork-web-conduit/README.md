# ⚡ Flowork Sovereign Web-Conduit

> **Zero-API Autonomous OS Bridge for Web Chatbots (Gemini Web, Claude, ChatGPT)**  
> **Aesthetic Standard:** Pure Optical Crystal Glass HUD (28px blur, #00ff66)  
> **Canonical Root:** `/opt/floworkos/apps/flowork-web-conduit`  

---

## 1. Overview
**Flowork Sovereign Web-Conduit** is a high-speed Manifest V3 browser extension and daemon conduit designed natively for **Flowork OS** (Linux 7.3.0 Rust). It allows AI models running in web interfaces (such as Google Gemini at `gemini.google.com`, Anthropic Claude at `claude.ai`, and OpenAI ChatGPT at `chatgpt.com`) to autonomously execute bash commands, query desktop GUI graphs, manipulate files with atomic rollback, and interact with the local operating system without requiring paid API keys, CLI copy-pasting, or external proxies.

---

## 2. Architecture & Execution Loop

```text
┌─────────────────────────┐              ┌─────────────────────────┐
│       Web Browser       │              │    Flowork OS Native    │
│  (gemini.google.com)    │              │         System          │
└────────────┬────────────┘              └────────────┬────────────┘
             │                                        │
    1. Gemini outputs:                                │
       ```flowork-exec                                │
       uname -a                                       │
       ```                                            │
             │                                        │
             ▼                                        │
    2. Content Script                                 │
       (Pure Crystal HUD)                             │
             │                                        │
             ▼ (IPC)                                  │
    3. Background Worker                              │
             │                                        │
             ▼ HTTP POST :18090                       │
             ├───────────────────────────────────────►│ 4. flowork-sysd
             │                                        │    (Landlock LSM)
             │                                        │         │
             │                                        │    5. TerminalExec
             │                                        │         │
             │◄───────────────────────────────────────┤ 6. JSON Result
             ▼                                        │    (Exit Code 0)
    7. In-Page Auto-Feedback                          │
       [FLOWORK_OUTPUT exit_code=0]                   │
       Linux 7.3.0-flowork-rust...                    │
       [/FLOWORK_OUTPUT]                              │
             │                                        │
             ▼                                        │
    8. Automatically types into input                 │
       and clicks 'Send' button                       │
```

---

## 3. Supported Command Formats
The conduit recognizes four standard command syntaxes:

### Format A: Fenced Code Block (Recommended)
````markdown
```flowork-exec
ls -la /opt/floworkos
```
````

### Format B: Tagged Block
```text
[FLOWORK_CMD]cat /etc/os-release[/FLOWORK_CMD]
```

### Format C: Bash Fenced Block with Marker
````markdown
```bash # flowork:exec
flowork-spatial-graph --json
```
````

### Format D: Raw Bash Fenced Block (Optional)
When **Allow Raw Bash** is checked in settings, any markdown bash block is intercepted.

---

## 4. Installation & Quickstart

### Step 1: Load Extension into Chrome
1. Open Google Chrome or Chromium.
2. Navigate to `chrome://extensions`.
3. Enable **Developer mode** (toggle in upper right).
4. Click **Load unpacked**.
5. Select directory: `/opt/floworkos/apps/flowork-web-conduit`.

### Step 2: Launch via CLI Shortcut
You can also launch Google Chrome directly loaded with the extension:
```bash
flowork-web-conduit launch gemini
```

### Step 3: Start Chatting
1. Open [Google Gemini Web](https://gemini.google.com).
2. Click the floating green HUD widget or extension icon.
3. Click **⚡ Inject Prompt** (or **📋 Copy Prompt** and paste it into the chat).
4. Prompt Gemini: *"Check the CPU, kernel version, and list running processes on my Flowork OS."*
5. Watch Gemini autonomously execute terminal commands and receive instant feedback!

---

## 5. Security & Sandbox Invariants
- Execution runs via `flowork-sysd` (:18090) with Landlock LSM confinement.
- Destructive commands can be reversed using `flowfs-rollback`.
- Cgroup v2 protection isolates memory and CPU spikes via `flowork-cgroup-guardian`.
