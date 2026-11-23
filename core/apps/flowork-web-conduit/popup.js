// Flowork Sovereign Web-Conduit - Popup Controller
// Pure Optical Crystal Glass HUD Controller

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

document.addEventListener("DOMContentLoaded", () => {
  const statusDot = document.getElementById("status-dot");
  const statusLabel = document.getElementById("status-label");
  const valDaemon = document.getElementById("val-daemon");
  const valKernel = document.getElementById("val-kernel");
  const valVulkan = document.getElementById("val-vulkan");

  const cfgAutoExec = document.getElementById("cfg-auto-exec");
  const cfgAutoSend = document.getElementById("cfg-auto-send");
  const cfgRawBash = document.getElementById("cfg-raw-bash");
  const cfgNotifications = document.getElementById("cfg-notifications");

  const btnCopyPrompt = document.getElementById("btn-copy-prompt");
  const btnOpenGemini = document.getElementById("btn-open-gemini");
  const btnOpenClaude = document.getElementById("btn-open-claude");
  const btnOpenChatgpt = document.getElementById("btn-open-chatgpt");
  const btnTestConnection = document.getElementById("btn-test-connection");

  // Load Settings
  chrome.runtime.sendMessage({ action: "GET_SETTINGS" }, (res) => {
    if (res && res.ok && res.settings) {
      const s = res.settings;
      cfgAutoExec.checked = s.autoExec !== false;
      cfgAutoSend.checked = s.autoSend !== false;
      cfgRawBash.checked = !!s.allowRawBash;
      cfgNotifications.checked = s.notificationOnExec !== false;
      if (s.sysdUrl) {
        valDaemon.innerText = s.sysdUrl.replace(/^https?:\/\//, "");
      }
    }
  });

  // Save Settings Handlers
  function saveSettings() {
    chrome.runtime.sendMessage({
      action: "SET_SETTINGS",
      settings: {
        autoExec: cfgAutoExec.checked,
        autoSend: cfgAutoSend.checked,
        allowRawBash: cfgRawBash.checked,
        notificationOnExec: cfgNotifications.checked
      }
    });
  }

  cfgAutoExec.addEventListener("change", saveSettings);
  cfgAutoSend.addEventListener("change", saveSettings);
  cfgRawBash.addEventListener("change", saveSettings);
  cfgNotifications.addEventListener("change", saveSettings);

  // Check Health & Telemetry
  function refreshStatus() {
    statusLabel.innerText = "Checking...";
    statusDot.className = "status-dot";

    chrome.runtime.sendMessage({ action: "CHECK_HEALTH" }, (res) => {
      if (res && res.ok) {
        statusDot.className = "status-dot online";
        statusLabel.innerText = "ONLINE";
        statusLabel.style.color = "#00ff66";
      } else {
        statusDot.className = "status-dot offline";
        statusLabel.innerText = "OFFLINE";
        statusLabel.style.color = "#ff3366";
      }
    });

    chrome.runtime.sendMessage({ action: "GET_SYS_INFO" }, (res) => {
      if (res && res.ok && res.data) {
        const d = res.data;
        if (d.kernel) valKernel.innerText = d.kernel;
        if (d.vulkan_available !== undefined) {
          valVulkan.innerText = d.vulkan_available ? "Active (NVIDIA)" : "Fallback (CPU)";
        }
      }
    });
  }

  refreshStatus();

  // Button Actions
  btnCopyPrompt.addEventListener("click", () => {
    navigator.clipboard.writeText(FLOWORK_SOVEREIGN_PROMPT).then(() => {
      btnCopyPrompt.innerText = "✓ Prompt Copied!";
      setTimeout(() => {
        btnCopyPrompt.innerText = "📋 Copy Sovereign Prompt";
      }, 2000);
    });
  });

  btnOpenGemini.addEventListener("click", () => {
    chrome.tabs.create({ url: "https://gemini.google.com" });
  });

  btnOpenClaude.addEventListener("click", () => {
    chrome.tabs.create({ url: "https://claude.ai" });
  });

  btnOpenChatgpt.addEventListener("click", () => {
    chrome.tabs.create({ url: "https://chatgpt.com" });
  });

  btnTestConnection.addEventListener("click", () => {
    btnTestConnection.innerText = "⚡ Testing...";
    chrome.runtime.sendMessage({ action: "EXEC_COMMAND", command: "uname -a" }, (res) => {
      if (res && res.ok && res.exit_code === 0) {
        btnTestConnection.innerText = `✓ Exit Code 0 (${res.duration_ms}ms)`;
        setTimeout(() => {
          btnTestConnection.innerText = "⚡ Test Local Daemon (Exit 0)";
        }, 3000);
      } else {
        btnTestConnection.innerText = `✕ Failed (Code ${res ? res.exit_code : 1})`;
        setTimeout(() => {
          btnTestConnection.innerText = "⚡ Test Local Daemon (Exit 0)";
        }, 3000);
      }
    });
  });
});
