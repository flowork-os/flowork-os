// [FL_INDEX: agent_desktop_bridge, flowork_sysd, accessibility_atspi, cli_bridge | COT: Bridge flowork-sysd directly to agent-desktop CLI for AT-SPI accessibility automation.| AT: 2026-11-11T13:40:00Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Agent Desktop Bridge for flowork-sysd
// Bridges REST endpoints to /usr/bin/agent-desktop (AT-SPI2 accessibility tree)
// =============================================================================

use serde_json::{json, Value};
use std::process::Command;

pub struct FloworkAgentBridge;

impl FloworkAgentBridge {
    pub async fn snapshot(app: Option<&str>, compact: bool) -> Result<Value, String> {
        let mut cmd = Command::new("/usr/bin/agent-desktop");
        cmd.arg("snapshot");
        if let Some(a) = app {
            cmd.arg("--app").arg(a);
        }
        if compact {
            cmd.arg("-i");
        }
        let output = cmd.output().map_err(|e| format!("Failed to execute agent-desktop: {}", e))?;
        if output.status.success() {
            let parsed: Value = serde_json::from_slice(&output.stdout)
                .map_err(|e| format!("Invalid JSON from agent-desktop snapshot: {}", e))?;
            Ok(parsed)
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }

    pub async fn find(payload: &Value) -> Result<Value, String> {
        let mut cmd = Command::new("/usr/bin/agent-desktop");
        cmd.arg("find");
        if let Some(app) = payload.get("app").and_then(|v| v.as_str()) {
            cmd.arg("--app").arg(app);
        }
        if let Some(role) = payload.get("role").and_then(|v| v.as_str()) {
            cmd.arg("--role").arg(role);
        }
        if let Some(name) = payload.get("name").and_then(|v| v.as_str()) {
            cmd.arg("--name").arg(name);
        }
        if let Some(text) = payload.get("text").and_then(|v| v.as_str()) {
            cmd.arg("--text").arg(text);
        }
        let output = cmd.output().map_err(|e| format!("Failed to execute agent-desktop: {}", e))?;
        if output.status.success() {
            let parsed: Value = serde_json::from_slice(&output.stdout)
                .map_err(|e| format!("Invalid JSON from agent-desktop find: {}", e))?;
            Ok(parsed)
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }

    pub async fn act(
        action: &str,
        target_ref: Option<&str>,
        text: Option<&str>,
        key: Option<&str>,
        headed: bool,
    ) -> Result<Value, String> {
        let mut cmd = Command::new("/usr/bin/agent-desktop");
        match action {
            "click" => {
                let r = target_ref.ok_or_else(|| "Target ref is required for click action".to_string())?;
                cmd.arg("click").arg(r);
            }
            "type" => {
                let r = target_ref.ok_or_else(|| "Target ref is required for type action".to_string())?;
                let t = text.unwrap_or("");
                cmd.arg("type").arg(r).arg(t);
            }
            "press" => {
                let k = key.ok_or_else(|| "Key is required for press action".to_string())?;
                cmd.arg("press").arg(k);
            }
            other => return Err(format!("Unsupported desktop action: {}", other)),
        }
        if headed {
            cmd.arg("--headed");
        }
        let output = cmd.output().map_err(|e| format!("Failed to execute agent-desktop: {}", e))?;
        if output.status.success() {
            let parsed: Value = serde_json::from_slice(&output.stdout)
                .unwrap_or_else(|_| json!({ "status": "ok", "output": String::from_utf8_lossy(&output.stdout) }));
            Ok(parsed)
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }
}
