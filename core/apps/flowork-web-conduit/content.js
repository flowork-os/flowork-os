// Flowork Sovereign Web-Conduit - In-Page Content Script
// Bridges Gemini Web, Claude, and ChatGPT to Flowork OS sysd (:18090)
// Complete 4-Layer Autonomous Loop: Structured Actions, Vision Paste & Android/Desktop Control

(function () {
  if (window.__flowork_conduit_injected) return;
  window.__flowork_conduit_injected = true;

  console.log("%c⚡ Flowork Sovereign Web-Conduit Active (v2.0 Autonomous Loop)", "color: #00ff66; font-weight: bold; font-size: 14px;");

  // System Prompt for Web AI
  const FLOWORK_SOVEREIGN_PROMPT = `[SYSTEM INSTRUCTION: FLOWORK OS 100% AUTONOMOUS CONTROLLER]
You are connected directly to the operator's Flowork OS (Linux 7.3.0 Rust Sovereign Agent-Native OS) via the Flowork Web Conduit.
You have native execution privileges across:
1. Desktop Linux GUI (X11/Wayland uinput mouse click/type/keyboard shortcuts)
2. Native Terminal Bash (Landlock LSM Sandboxed)
3. Android Micro-VM Subsystem (Live ADB emulator-5554: launch apps, tap, swipe, dump UI)
4. Chrome CDP Browser Automation (open, click, type, eval)
5. Visual Screen Telemetry & Spatial UI Graph (AT-SPI2 + DRM bounding boxes)
6. FlowFS Temporal Safety (atomic rollback & turn checkpoints)

HOW TO ISSUE COMMANDS:
You can format your commands in two standard ways:

Format A: Unified Actuator (Recommended)
\`\`\`flowork-exec
flowork-act <subsystem> [args...]
\`\`\`
Examples:
- Desktop Click: \`flowork-act desktop click 500 300\`
- Desktop Type: \`flowork-act desktop type "Hello Flowork"\`
- Desktop Shortcut: \`flowork-act desktop key "ctrl+alt+t"\`
- Desktop Focus: \`flowork-act desktop focus "Blender"\`
- Screen Vision: \`flowork-act screenshot --base64\` (Automatically pastes screenshot image directly into this chat!)
- Spatial UI Graph: \`flowork-act spatial-graph\`
- Android Launch App: \`flowork-act apk launch capcut\`
- Android Tap: \`flowork-act apk tap 540 1200\`
- Android Swipe: \`flowork-act apk swipe 540 1600 540 400 300\`
- Android UI Dump: \`flowork-act apk dump\`
- Chrome Browser: \`flowork-act browser open "https://github.com"\`
- Safe Checkpoint: \`flowork-act checkpoint "Before building feature"\`

Format B: Structured JSON Action
\`\`\`flowork-action
{
  "action": "screenshot",
  "base64": true
}
\`\`\`

Format C: Tagged Block
[FLOWORK_CMD]uname -a[/FLOWORK_CMD]

The local daemon executes your request with sub-5ms latency and returns:
[FLOWORK_OUTPUT exit_code=0 duration=15ms]
<stdout/stderr>
[/FLOWORK_OUTPUT]

Rules:
1. When inspecting visual desktop states, run 'flowork-act screenshot --base64'; the image will attach directly to your prompt input!
2. Execute multi-step tasks recursively until fully completed.
3. Prioritize precision and sovereign execution.`;

  let conduitSettings = {
    sysdUrl: "http://127.0.0.1:18090",
    autoExec: true,
    autoSend: true,
    allowRawBash: true,
    autoScroll: true
  };

  let executedCommandHashes = new Set();

  // Load Settings from background
  chrome.runtime.sendMessage({ action: "GET_SETTINGS" }, (res) => {
    if (res && res.ok && res.settings) {
      conduitSettings = { ...conduitSettings, ...res.settings };
      updateHudToggles();
    }
  });

  // ---------------- DOM Selectors Adapter ----------------
  function getPlatform() {
    const host = window.location.hostname;
    if (host.includes("gemini.google.com")) return "gemini";
    if (host.includes("claude.ai")) return "claude";
    if (host.includes("chatgpt.com")) return "chatgpt";
    return "generic";
  }

  function getChatInput() {
    const platform = getPlatform();
    if (platform === "gemini") {
      return document.querySelector("rich-textarea .ql-editor") ||
             document.querySelector("rich-textarea textarea") ||
             document.querySelector("div.ql-editor[contenteditable='true']") ||
             document.querySelector("div[contenteditable='true']");
    } else if (platform === "claude") {
      return document.querySelector("fieldset div[contenteditable='true']") ||
             document.querySelector("div[contenteditable='true']") ||
             document.querySelector("textarea");
    } else if (platform === "chatgpt") {
      return document.querySelector("#prompt-textarea") ||
             document.querySelector("textarea[data-id]") ||
             document.querySelector("div[contenteditable='true']");
    }
    return document.querySelector("textarea") || document.querySelector("div[contenteditable='true']");
  }

  function getSendButton() {
    const platform = getPlatform();
    if (platform === "gemini") {
      return document.querySelector("button[aria-label*='Send']") ||
             document.querySelector("button.send-button") ||
             document.querySelector("div[aria-label*='Send']") ||
             document.querySelector("button:has(mat-icon[fonticon='send'])") ||
             document.querySelector("button:has(svg)");
    } else if (platform === "claude") {
      return document.querySelector("button[aria-label*='Send']") ||
             document.querySelector("button[aria-label*='send']") ||
             document.querySelector("button:has(svg)");
    } else if (platform === "chatgpt") {
      return document.querySelector("button[data-testid='send-button']") ||
             document.querySelector("button[aria-label='Send prompt']");
    }
    return document.querySelector("button[type='submit']") || document.querySelector("button[aria-label*='Send']");
  }

  function isAiGenerating() {
    const platform = getPlatform();
    if (platform === "gemini") {
      return !!document.querySelector("button[aria-label*='Stop']") ||
             !!document.querySelector("mat-progress-spinner") ||
             !!document.querySelector(".loading-indicator");
    } else if (platform === "claude") {
      return !!document.querySelector("button[aria-label*='Stop']") ||
             !!document.querySelector("div[data-is-streaming='true']");
    } else if (platform === "chatgpt") {
      return !!document.querySelector("button[data-testid='stop-button']");
    }
    return false;
  }

  // Multiline-Safe Injection into Quill / ProseMirror / Textarea
  function injectTextToChatInput(text) {
    const input = getChatInput();
    if (!input) {
      console.warn("[Flowork Conduit] Chat input not found");
      return false;
    }

    input.focus();

    if (input.tagName === "TEXTAREA" || input.tagName === "INPUT") {
      input.value = text;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    } else if (input.isContentEditable) {
      input.innerHTML = "";

      // Split into discrete lines preserving all formatting
      const lines = text.split("\n");
      const fragment = document.createDocumentFragment();

      for (const line of lines) {
        const p = document.createElement("p");
        if (line.length === 0) {
          p.innerHTML = "<br>";
        } else {
          p.textContent = line;
        }
        fragment.appendChild(p);
      }

      input.appendChild(fragment);

      input.dispatchEvent(new InputEvent("input", {
        bubbles: true,
        cancelable: true,
        inputType: "insertText"
      }));
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));

      // Move cursor to end
      const range = document.createRange();
      const sel = window.getSelection();
      range.selectNodeContents(input);
      range.collapse(false);
      sel.removeAllRanges();
      sel.addRange(range);
    }

    if (conduitSettings.autoScroll) {
      input.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    return true;
  }

  // ---------------- Visual Multimodal Paste ----------------
  function base64ToPngFile(base64Data, filename = "flowork_desktop_capture.png") {
    try {
      const cleanB64 = base64Data.replace(/^data:image\/\w+;base64,/, "");
      const byteCharacters = atob(cleanB64);
      const byteArrays = [];
      for (let offset = 0; offset < byteCharacters.length; offset += 512) {
        const slice = byteCharacters.slice(offset, offset + 512);
        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
          byteNumbers[i] = slice.charCodeAt(i);
        }
        byteArrays.push(new Uint8Array(byteNumbers));
      }
      const blob = new Blob(byteArrays, { type: "image/png" });
      return new File([blob], filename, { type: "image/png" });
    } catch (e) {
      console.error("[Flowork Conduit] Error converting base64 to File:", e);
      return null;
    }
  }

  function pasteImageToChat(file, captionText = "") {
    const input = getChatInput();
    if (!input || !file) return false;

    input.focus();
    const dt = new DataTransfer();
    dt.items.add(file);

    // Dispatch native paste event containing the image file
    const pasteEvent = new ClipboardEvent("paste", {
      bubbles: true,
      cancelable: true,
      clipboardData: dt
    });
    input.dispatchEvent(pasteEvent);
    console.log("[Flowork Conduit] Synthesized image paste event dispatched to Gemini input.");

    if (captionText) {
      setTimeout(() => {
        injectTextToChatInput(captionText);
      }, 500);
    }
    return true;
  }

  function triggerSendMessage() {
    const btn = getSendButton();
    if (btn && !btn.disabled) {
      btn.click();
      console.log("[Flowork Conduit] Auto-send dispatched.");
      return true;
    }
    return false;
  }

  // ---------------- Floating Glass HUD ----------------
  function createHudWidget() {
    if (document.getElementById("flowork-conduit-hud")) return;

    const hud = document.createElement("div");
    hud.id = "flowork-conduit-hud";
    hud.innerHTML = `
      <div class="fl-header" id="fl-hud-drag">
        <div class="fl-title-wrap">
          <div class="fl-pulse-dot" id="fl-hud-dot"></div>
          <span class="fl-title">Flowork OS Autonomous Hub</span>
        </div>
        <div class="fl-controls">
          <button class="fl-icon-btn" id="fl-hud-collapse" title="Collapse HUD">_</button>
        </div>
      </div>
      <div class="fl-body">
        <div class="fl-status-row">
          <span class="fl-label">Daemon</span>
          <span class="fl-val" id="fl-hud-daemon">127.0.0.1:18090</span>
        </div>
        <div class="fl-status-row">
          <span class="fl-label">Android ADB</span>
          <span class="fl-val" style="color: #00e5ff;">emulator-5554</span>
        </div>
        <div class="fl-switch-row">
          <span class="fl-label">Auto-Execute Commands</span>
          <label class="fl-toggle-switch">
            <input type="checkbox" id="fl-toggle-auto-exec" ${conduitSettings.autoExec ? "checked" : ""}>
            <span class="fl-slider"></span>
          </label>
        </div>
        <div class="fl-switch-row">
          <span class="fl-label">Auto-Send Feedback</span>
          <label class="fl-toggle-switch">
            <input type="checkbox" id="fl-toggle-auto-send" ${conduitSettings.autoSend ? "checked" : ""}>
            <span class="fl-slider"></span>
          </label>
        </div>
        <div class="fl-action-grid">
          <button class="fl-btn-primary" id="fl-hud-inject-prompt">
            ⚡ Inject Prompt
          </button>
          <button class="fl-btn-secondary" id="fl-hud-copy-prompt">
            📋 Copy Prompt
          </button>
        </div>
        <div class="fl-action-grid">
          <button class="fl-btn-secondary" id="fl-hud-screenshot">
            📸 Vision Paste
          </button>
          <button class="fl-btn-secondary" id="fl-hud-spatial">
            🎯 UI Graph
          </button>
        </div>
        <div class="fl-action-grid">
          <button class="fl-btn-secondary" id="fl-hud-apk">
            📱 APK Current
          </button>
          <button class="fl-btn-secondary" id="fl-hud-checkpoint">
            ⏪ Checkpoint
          </button>
        </div>
      </div>
      <div class="fl-footer">
        <span id="fl-hud-session">Sovereign 4-Tier Loop</span>
        <span id="fl-hud-status-text">Connected</span>
      </div>
    `;

    document.body.appendChild(hud);

    // Event Listeners
    const collapseBtn = hud.querySelector("#fl-hud-collapse");
    collapseBtn.addEventListener("click", () => {
      hud.classList.toggle("collapsed");
      collapseBtn.innerText = hud.classList.contains("collapsed") ? "□" : "_";
    });

    const autoExecToggle = hud.querySelector("#fl-toggle-auto-exec");
    autoExecToggle.addEventListener("change", (e) => {
      conduitSettings.autoExec = e.target.checked;
      chrome.runtime.sendMessage({ action: "SET_SETTINGS", settings: { autoExec: conduitSettings.autoExec } });
    });

    const autoSendToggle = hud.querySelector("#fl-toggle-auto-send");
    autoSendToggle.addEventListener("change", (e) => {
      conduitSettings.autoSend = e.target.checked;
      chrome.runtime.sendMessage({ action: "SET_SETTINGS", settings: { autoSend: conduitSettings.autoSend } });
    });

    hud.querySelector("#fl-hud-inject-prompt").addEventListener("click", () => {
      injectTextToChatInput(FLOWORK_SOVEREIGN_PROMPT);
    });

    hud.querySelector("#fl-hud-copy-prompt").addEventListener("click", () => {
      navigator.clipboard.writeText(FLOWORK_SOVEREIGN_PROMPT);
      alert("Flowork Autonomous System Prompt copied to clipboard!");
    });

    hud.querySelector("#fl-hud-screenshot").addEventListener("click", () => {
      chrome.runtime.sendMessage({ action: "EXEC_COMMAND", command: "flowork-act screenshot --base64" }, (res) => {
        if (res && res.ok && res.exit_code === 0) {
          try {
            const parsed = JSON.parse(res.stdout);
            if (parsed.base64) {
              const file = base64ToPngFile(parsed.base64);
              if (file) {
                pasteImageToChat(file, `[DESKTOP_SCREENSHOT_ATTACHED] Inspect this screenshot image (${parsed.file_path}).`);
                return;
              }
            }
            injectTextToChatInput(`[FLOWORK_SCREENSHOT_CAPTURED]\nPath: ${parsed.file_path}\nMarkdown: ${parsed.markdown}\n[/FLOWORK_SCREENSHOT_CAPTURED]`);
          } catch (_) {
            injectTextToChatInput(`[FLOWORK_SCREENSHOT_CAPTURED]\n${res.stdout}\n[/FLOWORK_SCREENSHOT_CAPTURED]`);
          }
        } else {
          alert("Screenshot failed: " + (res?.stderr || "Unknown error"));
        }
      });
    });

    hud.querySelector("#fl-hud-spatial").addEventListener("click", () => {
      chrome.runtime.sendMessage({ action: "SPATIAL_GRAPH", payload: { interactive_only: true } }, (res) => {
        if (res && res.ok) {
          const summary = JSON.stringify(res.data, null, 2).slice(0, 3000);
          injectTextToChatInput(`[FLOWORK_SPATIAL_GRAPH]\n${summary}\n[/FLOWORK_SPATIAL_GRAPH]`);
        } else {
          alert("Spatial UI Graph query failed: " + (res?.error || "Unknown"));
        }
      });
    });

    hud.querySelector("#fl-hud-apk").addEventListener("click", () => {
      chrome.runtime.sendMessage({ action: "EXEC_COMMAND", command: "flowork-act apk current" }, (res) => {
        if (res && res.ok) {
          injectTextToChatInput(`[FLOWORK_ANDROID_STATE]\n${res.stdout}\n[/FLOWORK_ANDROID_STATE]`);
        } else {
          alert("APK query failed: " + (res?.stderr || "Unknown"));
        }
      });
    });

    hud.querySelector("#fl-hud-checkpoint").addEventListener("click", () => {
      chrome.runtime.sendMessage({ action: "EXEC_COMMAND", command: "flowork-act checkpoint 'HUD Manual Snapshot'" }, (res) => {
        if (res && res.ok) {
          alert("FlowFS Checkpoint created!");
        } else {
          alert("Checkpoint error: " + (res?.stderr || "Unknown"));
        }
      });
    });

    // Draggable HUD
    const dragHeader = hud.querySelector("#fl-hud-drag");
    let isDragging = false;
    let startX, startY, origLeft, origTop;

    dragHeader.addEventListener("mousedown", (e) => {
      if (e.target.tagName === "BUTTON") return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = hud.getBoundingClientRect();
      origLeft = rect.left;
      origTop = rect.top;
      hud.style.bottom = "auto";
      hud.style.right = "auto";
      hud.style.left = `${origLeft}px`;
      hud.style.top = `${origTop}px`;
    });

    window.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      hud.style.left = `${origLeft + (e.clientX - startX)}px`;
      hud.style.top = `${origTop + (e.clientY - startY)}px`;
    });

    window.addEventListener("mouseup", () => {
      isDragging = false;
    });

    checkHealth();
  }

  function updateHudToggles() {
    const autoExecToggle = document.getElementById("fl-toggle-auto-exec");
    if (autoExecToggle) autoExecToggle.checked = conduitSettings.autoExec;
    const autoSendToggle = document.getElementById("fl-toggle-auto-send");
    if (autoSendToggle) autoSendToggle.checked = conduitSettings.autoSend;
  }

  function checkHealth() {
    chrome.runtime.sendMessage({ action: "CHECK_HEALTH" }, (res) => {
      const dot = document.getElementById("fl-hud-dot");
      const statusText = document.getElementById("fl-hud-status-text");
      if (!dot || !statusText) return;

      if (res && res.ok) {
        dot.className = "fl-pulse-dot";
        statusText.innerText = "Online";
        statusText.style.color = "#00ff66";
      } else {
        dot.className = "fl-pulse-dot offline";
        statusText.innerText = "Offline";
        statusText.style.color = "#ff3366";
      }
    });
  }

  setInterval(checkHealth, 15000);

  // ---------------- Command Parsing & Execution ----------------
  function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return hash.toString();
  }

  // Detects if a <pre> element represents an executable codeblock
  function inspectPreElement(preNode) {
    if (preNode.dataset.floworkBound === "true") return null;

    const codeNode = preNode.querySelector("code") || preNode;
    const rawContent = (codeNode.textContent || "").trim();
    if (!rawContent || rawContent === "<command>" || rawContent.startsWith("[FLOWORK_OUTPUT")) return null;

    // Check language identifiers
    const codeClass = (codeNode.className || "") + " " + (preNode.className || "");
    const parentContainer = preNode.closest(".code-block, code-block, .code-container") || preNode.parentElement;
    const headerText = (parentContainer ? (parentContainer.querySelector(".code-block-header, .header, header, .code-block-decoration")?.textContent || "") : "").toLowerCase();
    const dataLang = (preNode.getAttribute("data-language") || codeNode.getAttribute("data-language") || "").toLowerCase();

    let isMatch = false;
    let matchType = "codeblock";
    let isStructuredAction = false;

    // 1. Structured flowork-action
    if (codeClass.includes("flowork-action") || codeClass.includes("language-flowork-action") || headerText.includes("flowork-action") || dataLang === "flowork-action" || rawContent.startsWith("#FLOWORK_ACTION")) {
      isMatch = true;
      matchType = "flowork-action";
      isStructuredAction = true;
    }
    // 2. Explicit flowork-exec language
    else if (codeClass.includes("flowork-exec") || codeClass.includes("language-flowork-exec") || headerText.includes("flowork-exec") || dataLang === "flowork-exec" || rawContent.startsWith("#FLOWORK_EXEC")) {
      isMatch = true;
      matchType = "flowork-exec";
    }
    // 3. Explicit flowork language
    else if (codeClass.includes("flowork") || codeClass.includes("language-flowork") || headerText.includes("flowork") || dataLang === "flowork") {
      isMatch = true;
      matchType = "flowork";
    }
    // 4. Tagged header inside code
    else if (rawContent.startsWith("# flowork:exec") || rawContent.startsWith("#flowork:exec") || rawContent.startsWith("#!/bin/bash")) {
      isMatch = true;
      matchType = "bash_tagged";
    }
    // 5. flowork-act CLI invocations
    else if (rawContent.startsWith("flowork-act ") || rawContent.startsWith("/opt/floworkos/bin/flowork-act")) {
      isMatch = true;
      matchType = "flowork-act";
    }
    // 6. Raw bash/sh block when allowRawBash is enabled
    else if (conduitSettings.allowRawBash && (codeClass.includes("language-bash") || codeClass.includes("language-sh") || codeClass.includes("language-shell") || headerText.includes("bash") || headerText.includes("shell") || dataLang === "bash" || dataLang === "sh")) {
      isMatch = true;
      matchType = "bash";
    }

    if (isMatch) {
      let finalCmd = rawContent;
      if (finalCmd.startsWith("# flowork:exec") || finalCmd.startsWith("#FLOWORK_EXEC") || finalCmd.startsWith("#FLOWORK_ACTION")) {
        finalCmd = finalCmd.replace(/^#(?:flowork:exec|FLOWORK_EXEC|FLOWORK_ACTION)\s*\n?/, "");
      }

      // If structured JSON action, convert to flowork-act json '<payload>'
      if (isStructuredAction && finalCmd.startsWith("{") && finalCmd.endsWith("}")) {
        const escaped = finalCmd.replace(/'/g, "'\\''");
        finalCmd = `flowork-act json '${escaped}'`;
      }

      return {
        command: finalCmd.trim(),
        raw: rawContent,
        type: matchType,
        anchorNode: parentContainer || preNode
      };
    }

    return null;
  }

  // Detects tagged commands: [FLOWORK_CMD]...[/FLOWORK_CMD] or [FLOWORK_EXEC]...[/FLOWORK_EXEC]
  function inspectTaggedCommands(msgRoot) {
    const commands = [];
    const fullText = msgRoot.textContent || "";
    const tagRegex = /\[FLOWORK_(?:CMD|EXEC)\]([\s\S]*?)\[\/FLOWORK_(?:CMD|EXEC)\]/g;
    let match;

    while ((match = tagRegex.exec(fullText)) !== null) {
      const cmd = match[1].trim();
      if (cmd && cmd !== "<command>" && !cmd.includes("[FLOWORK_OUTPUT")) {
        let targetParagraph = null;
        const paragraphs = msgRoot.querySelectorAll("p, div");
        for (const p of paragraphs) {
          if (p.textContent.includes(match[0]) && !p.dataset.floworkBound) {
            targetParagraph = p;
            break;
          }
        }

        commands.push({
          command: cmd,
          raw: match[0],
          type: "tag",
          anchorNode: targetParagraph || msgRoot
        });
      }
    }

    return commands;
  }

  function attachConduitBar(anchorNode, cmdObj) {
    const hash = hashString(cmdObj.command);
    if (document.querySelector(`[data-conduit-hash="${hash}"]`)) return;

    anchorNode.dataset.floworkBound = "true";

    const bar = document.createElement("div");
    bar.className = "fl-conduit-bar";
    bar.setAttribute("data-conduit-hash", hash);

    bar.innerHTML = `
      <div class="fl-bar-top">
        <div class="fl-bar-badge">
          <span>⚡ Flowork OS</span>
          <span style="opacity: 0.65; font-size: 10px;">[${cmdObj.type}]</span>
        </div>
        <button class="fl-bar-btn" data-action="run">⚡ Run on Flowork OS</button>
      </div>
      <div class="fl-terminal-output" style="display: none;"></div>
    `;

    // Insert right after the codeblock/anchor node
    if (anchorNode.nextSibling) {
      anchorNode.parentNode.insertBefore(bar, anchorNode.nextSibling);
    } else {
      anchorNode.parentNode.appendChild(bar);
    }

    const runBtn = bar.querySelector("button[data-action='run']");
    const outputDiv = bar.querySelector(".fl-terminal-output");

    const executeThis = async () => {
      if (executedCommandHashes.has(hash)) return;
      executedCommandHashes.add(hash);

      bar.className = "fl-conduit-bar executing";
      runBtn.disabled = true;
      runBtn.innerText = "Executing...";
      outputDiv.style.display = "block";
      outputDiv.innerText = "Dispatching to flowork-sysd (127.0.0.1:18090)...";

      chrome.runtime.sendMessage({ action: "EXEC_COMMAND", command: cmdObj.command }, (res) => {
        runBtn.disabled = false;
        if (res && res.ok && res.exit_code === 0) {
          bar.className = "fl-conduit-bar success";
          runBtn.innerText = `✓ Exit Code 0 (${res.duration_ms}ms)`;
          const outText = (res.stdout || "").trim() || "(No stdout, exit code 0)";
          outputDiv.innerText = outText;

          // Check if output contains base64 screenshot
          let hasImagePasted = false;
          try {
            const parsed = JSON.parse(outText);
            if (parsed.base64) {
              const file = base64ToPngFile(parsed.base64);
              if (file) {
                pasteImageToChat(file, `[FLOWORK_OUTPUT exit_code=0 duration=${res.duration_ms}ms]\nScreenshot captured: ${parsed.file_path}\n[/FLOWORK_OUTPUT]`);
                hasImagePasted = true;
              }
            }
          } catch (_) {}

          if (conduitSettings.autoSend && !hasImagePasted) {
            sendOutputBackToChat(cmdObj.command, outText, res.exit_code, res.duration_ms);
          }
        } else {
          bar.className = "fl-conduit-bar error";
          const code = res ? res.exit_code : 1;
          const duration = res ? res.duration_ms : 0;
          runBtn.innerText = `✕ Exit Code ${code} (${duration}ms)`;
          const errText = (res?.stderr || res?.stdout || res?.error || "Execution failed").trim();
          outputDiv.innerText = errText;

          if (conduitSettings.autoSend) {
            sendOutputBackToChat(cmdObj.command, errText, code, duration);
          }
        }
      });
    };

    runBtn.addEventListener("click", executeThis);

    // Auto-execute if enabled and AI is done streaming
    if (conduitSettings.autoExec && !executedCommandHashes.has(hash)) {
      scheduleAutoExecution(executeThis, hash);
    }
  }

  function scheduleAutoExecution(execFn, hash) {
    const checkInterval = setInterval(() => {
      if (!isAiGenerating()) {
        clearInterval(checkInterval);
        setTimeout(() => {
          if (!executedCommandHashes.has(hash)) {
            console.log("[Flowork Conduit] Triggering auto-execution for command:", hash);
            execFn();
          }
        }, 500);
      }
    }, 350);

    // Safety timeout: 45s max wait
    setTimeout(() => clearInterval(checkInterval), 45000);
  }

  function sendOutputBackToChat(command, output, exitCode, durationMs) {
    const formatted = `[FLOWORK_OUTPUT exit_code=${exitCode} duration=${durationMs}ms]
${output}
[/FLOWORK_OUTPUT]`;

    console.log("[Flowork Conduit] Injecting terminal output back to web chat...");
    const injected = injectTextToChatInput(formatted);
    if (injected) {
      setTimeout(() => {
        triggerSendMessage();
      }, 500);
    }
  }

  // ---------------- DOM Scanner with Duplicate Prevention ----------------
  function scanForCommands() {
    const platform = getPlatform();
    let rootSelector = "";

    if (platform === "gemini") {
      rootSelector = "model-response, .model-response-text";
    } else if (platform === "claude") {
      rootSelector = ".font-claude-message";
    } else if (platform === "chatgpt") {
      rootSelector = "div[data-message-author-role='assistant']";
    } else {
      rootSelector = "article, .assistant-message, .message-assistant";
    }

    const messageRoots = document.querySelectorAll(rootSelector);
    messageRoots.forEach((msgRoot) => {
      // 1. Scan for <pre> codeblocks directly
      const pres = msgRoot.querySelectorAll("pre");
      pres.forEach((pre) => {
        const cmdObj = inspectPreElement(pre);
        if (cmdObj) {
          attachConduitBar(cmdObj.anchorNode, cmdObj);
        }
      });

      // 2. Scan for tagged text commands: [FLOWORK_CMD]...[/FLOWORK_CMD]
      const taggedCmds = inspectTaggedCommands(msgRoot);
      taggedCmds.forEach((cmdObj) => {
        attachConduitBar(cmdObj.anchorNode, cmdObj);
      });
    });
  }

  // MutationObserver with Debounce
  let scanDebounce = null;
  const observer = new MutationObserver(() => {
    if (scanDebounce) clearTimeout(scanDebounce);
    scanDebounce = setTimeout(scanForCommands, 250);
  });

  function init() {
    createHudWidget();
    scanForCommands();
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
