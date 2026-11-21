// =============================================================================
// 🚀 Flowork Sovereign OS — Autonomous Terminal Execution Daemon
// Enables the AI agent to execute commands, compile code, and inspect outputs
// Hardened with Landlock LSM Kernel Sandboxing & Execution Timeout Guard
// =============================================================================

use crate::landlock_sandbox::LandlockSandbox;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::path::Path;
use std::time::{Duration, Instant};
use tokio::process::Command;

pub struct TerminalExec;

impl TerminalExec {
    pub async fn execute(
        command: &str,
        cwd: Option<&str>,
        env_vars: Option<HashMap<String, String>>,
    ) -> Value {
        let start = Instant::now();
        let timeout_secs: u64 = std::env::var("FLOWORK_EXEC_TIMEOUT_SECS")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(120);

        let mut cmd = Command::new("bash");
        cmd.arg("-c").arg(command);

        let effective_cwd = cwd.unwrap_or(".");
        cmd.current_dir(effective_cwd);

        if let Some(envs) = env_vars {
            for (k, v) in envs {
                cmd.env(k, v);
            }
        }

        // Configure Landlock LSM ruleset if enabled
        let sandbox_mode = std::env::var("FLOWORK_SANDBOX_MODE").unwrap_or_else(|_| "auto".to_string());
        if sandbox_mode != "off" && LandlockSandbox::get_abi_version() > 0 {
            let home_dir = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
            let ro_paths = ["/usr", "/lib", "/lib64", "/bin", "/sbin", "/etc", "/dev", "/proc", "/sys"];
            
            let mut rw_vec: Vec<&str> = vec!["/tmp", "/dev/shm", "/opt/floworkos"];
            if Path::new(&home_dir).exists() {
                rw_vec.push(&home_dir);
            }
            if let Some(d) = cwd {
                if Path::new(d).exists() && !rw_vec.contains(&d) {
                    rw_vec.push(d);
                }
            }

            if let Ok(ruleset_fd) = LandlockSandbox::create_sovereign_ruleset(&ro_paths, &rw_vec) {
                unsafe {
                    cmd.pre_exec(move || {
                        LandlockSandbox::apply_ruleset(ruleset_fd)
                            .map_err(std::io::Error::other)
                    });
                }
            }
        }

        match tokio::time::timeout(Duration::from_secs(timeout_secs), cmd.output()).await {
            Ok(Ok(output)) => {
                let duration = start.elapsed();
                json!({
                    "status": "ok",
                    "exit_code": output.status.code().unwrap_or(-1),
                    "stdout": String::from_utf8_lossy(&output.stdout),
                    "stderr": String::from_utf8_lossy(&output.stderr),
                    "duration_ms": duration.as_millis()
                })
            }
            Ok(Err(e)) => {
                json!({
                    "status": "error",
                    "exit_code": 1,
                    "error": format!("Failed to spawn shell process: {}", e),
                    "duration_ms": start.elapsed().as_millis()
                })
            }
            Err(_) => {
                json!({
                    "status": "timeout",
                    "exit_code": 124,
                    "error": format!("Command execution timed out after {}s", timeout_secs),
                    "duration_ms": start.elapsed().as_millis()
                })
            }
        }
    }
}
