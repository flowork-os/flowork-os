// Flowork Sovereign Web-Conduit - Background Service Worker (Manifest V3)
// Canonical Bridge connecting Gemini Web, Claude & ChatGPT to Flowork OS sysd (:18090)

const DEFAULT_SYSD_URL = "http://127.0.0.1:18090";

const DEFAULT_SETTINGS = {
  sysdUrl: DEFAULT_SYSD_URL,
  autoExec: true,
  autoSend: true,
  autoScroll: true,
  allowRawBash: false,
  notificationOnExec: true
};

// Initialize settings on install
chrome.runtime.onInstalled.addListener(async () => {
  const current = await chrome.storage.local.get("settings");
  if (!current.settings) {
    await chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
  }
  updateBadgeStatus();
  console.log("[Flowork Web-Conduit] Service worker initialized.");
});

// Periodic badge health check (every 20s)
async function updateBadgeStatus() {
  try {
    const data = await chrome.storage.local.get("settings");
    const sysdUrl = data.settings?.sysdUrl || DEFAULT_SYSD_URL;
    const res = await fetch(`${sysdUrl}/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      chrome.action.setBadgeText({ text: "ON" });
      chrome.action.setBadgeBackgroundColor({ color: "#00cc66" });
    } else {
      chrome.action.setBadgeText({ text: "ERR" });
      chrome.action.setBadgeBackgroundColor({ color: "#ffaa00" });
    }
  } catch (err) {
    chrome.action.setBadgeText({ text: "OFF" });
    chrome.action.setBadgeBackgroundColor({ color: "#ff3366" });
  }
}

setInterval(updateBadgeStatus, 20000);
updateBadgeStatus();

// Message Router for Content Script and Popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handleMessage = async () => {
    const data = await chrome.storage.local.get("settings");
    const settings = { ...DEFAULT_SETTINGS, ...(data.settings || {}) };
    const sysdUrl = settings.sysdUrl || DEFAULT_SYSD_URL;

    switch (message.action) {
      case "GET_SETTINGS":
        return { ok: true, settings };

      case "SET_SETTINGS":
        await chrome.storage.local.set({ settings: { ...settings, ...message.settings } });
        updateBadgeStatus();
        return { ok: true };

      case "CHECK_HEALTH": {
        try {
          const res = await fetch(`${sysdUrl}/health`, { signal: AbortSignal.timeout(3000) });
          const json = await res.json();
          return { ok: res.ok, data: json };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      case "GET_SYS_INFO": {
        try {
          const res = await fetch(`${sysdUrl}/api/system/info`, { signal: AbortSignal.timeout(4000) });
          const json = await res.json();
          return { ok: res.ok, data: json };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      case "EXEC_COMMAND": {
        const cmd = message.command || message.cmd;
        const cwd = message.cwd || undefined;
        if (!cmd) {
          return { ok: false, error: "Empty command payload" };
        }

        try {
          const startTime = Date.now();
          const res = await fetch(`${sysdUrl}/api/agent/terminal/exec`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              cmd: cmd,
              cwd: cwd
            }),
            signal: AbortSignal.timeout(120000) // 120s max execution
          });

          const result = await res.json();
          const elapsed = Date.now() - startTime;

          if (settings.notificationOnExec) {
            chrome.notifications.create({
              type: "basic",
              iconUrl: "icons/icon48.png",
              title: `Flowork OS Execution (Exit ${result.exit_code})`,
              message: `Cmd: ${cmd.slice(0, 40)}${cmd.length > 40 ? "..." : ""} (${elapsed}ms)`,
              priority: 1
            });
          }

          return {
            ok: res.ok,
            exit_code: result.exit_code,
            stdout: result.stdout || "",
            stderr: result.stderr || "",
            duration_ms: result.duration_ms || elapsed,
            status: result.status || (res.ok ? "ok" : "error")
          };
        } catch (e) {
          return {
            ok: false,
            exit_code: 1,
            stdout: "",
            stderr: `Conduit bridge error: ${e.message}`,
            duration_ms: 0,
            status: "bridge_error"
          };
        }
      }

      case "SPATIAL_GRAPH": {
        try {
          const res = await fetch(`${sysdUrl}/api/system/display/spatial-graph`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(message.payload || {})
          });
          const json = await res.json();
          return { ok: res.ok, data: json };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      case "CAPTURE_SCREEN": {
        try {
          const res = await fetch(`${sysdUrl}/api/system/display/capture`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(message.payload || {})
          });
          const json = await res.json();
          return { ok: res.ok, data: json };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      case "FLOWFS_ROLLBACK": {
        try {
          const res = await fetch(`${sysdUrl}/api/flowfs/temporal/rollback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(message.payload || {})
          });
          const json = await res.json();
          return { ok: res.ok, data: json };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      case "FLOWFS_CHECKPOINT": {
        try {
          const res = await fetch(`${sysdUrl}/api/flowfs/temporal/checkpoint`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(message.payload || { label: "Web Conduit Manual Checkpoint" })
          });
          const json = await res.json();
          return { ok: res.ok, data: json };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      case "NOTIFY_SYSTEM": {
        try {
          const res = await fetch(`${sysdUrl}/api/system/notify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: message.title || "Flowork Web Conduit",
              message: message.message || ""
            })
          });
          return { ok: res.ok };
        } catch (e) {
          return { ok: false, error: e.message };
        }
      }

      default:
        return { ok: false, error: `Unknown action: ${message.action}` };
    }
  };

  handleMessage().then(sendResponse);
  return true; // Keep channel open for async response
});
