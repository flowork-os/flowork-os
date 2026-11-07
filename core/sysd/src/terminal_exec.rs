// =============================================================================
// 🚀 Flowork Sovereign OS — Autonomous Terminal Execution Daemon
// Enables the AI agent to execute commands, compile code, and inspect outputs
// =============================================================================

use serde_json::{json, Value};
use std::collections::HashMap;
use std::time::Instant;
use tokio::process::Command;

pub struct TerminalExec;

impl TerminalExec {
    pub async fn execute(
        command: &str,
        cwd: Option<&str>,
        env_vars: Option<HashMap<String, String>>,
    ) -> Value {
        let start = Instant::now();
        let mut cmd = Command::new("bash");
        cmd.arg("-c").arg(command);

        if let Some(dir) = cwd {
            cmd.current_dir(dir);
        }

        if let Some(envs) = env_vars {
            for (k, v) in envs {
                cmd.env(k, v);
            }
        }

        match cmd.output().await {
            Ok(output) => {
                let duration = start.elapsed();
                json!({
                    "status": "ok",
                    "exit_code": output.status.code().unwrap_or(-1),
                    "stdout": String::from_utf8_lossy(&output.stdout),
                    "stderr": String::from_utf8_lossy(&output.stderr),
                    "duration_ms": duration.as_millis()
                })
            }
            Err(e) => {
                json!({
                    "status": "error",
                    "error": format!("Failed to spawn shell process: {}", e)
                })
            }
        }
    }
}
