use flowork_core_rs::sandbox::{
    build_sandbox_plan, create_ruleset_for_plan, probe_landlock_abi, publish_sandbox_violation,
    restrict_self_raw, CapabilityProfile, STRIP_SENSITIVE_ENVS,
};
use serde_json::json;
use std::env;
use std::fs::OpenOptions;
use std::io::Read as _;
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

fn print_help() {
    println!("flowork-sandbox-exec — Pure Rust Per-App Kernel Landlock Capability Jail");
    println!("Usage:");
    println!("  flowork-sandbox-exec --check");
    println!("  flowork-sandbox-exec --app-id <id> [--manifest <path>] [--profile <strict|standard|network_off|unrestricted_trusted>] [--detach] [--sandbox-trace] -- <cmd> [args...]");
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() || args.iter().any(|a| a == "--help" || a == "-h") {
        print_help();
        return;
    }

    if args.iter().any(|a| a == "--check") {
        let abi = probe_landlock_abi();
        println!(
            "flowork-sandbox-exec: OK (Pure Rust Landlock FS+Net jail, landlock_abi={})",
            abi
        );
        return;
    }

    let mut app_id = String::from("generic_app");
    let mut manifest_path: Option<PathBuf> = None;
    let mut profile_override: Option<CapabilityProfile> = None;
    let mut detach = false;
    let mut trace_only = false;
    let mut cmd_start: Option<usize> = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--" => {
                cmd_start = Some(i + 1);
                break;
            }
            "--app-id" => {
                if let Some(v) = args.get(i + 1) {
                    app_id = v.clone();
                    i += 1;
                }
            }
            "--manifest" => {
                if let Some(v) = args.get(i + 1) {
                    manifest_path = Some(PathBuf::from(v));
                    i += 1;
                }
            }
            "--profile" => {
                if let Some(v) = args.get(i + 1) {
                    profile_override = Some(CapabilityProfile::parse_str(v));
                    i += 1;
                }
            }
            "--detach" => detach = true,
            "--sandbox-trace" => trace_only = true,
            other if !other.starts_with('-') => {
                cmd_start = Some(i);
                break;
            }
            _ => {}
        }
        i += 1;
    }

    let plan = build_sandbox_plan(&app_id, manifest_path.as_deref(), profile_override);

    if trace_only && cmd_start.is_none() {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "app_id": plan.app_id,
                "profile": plan.permissions.profile.as_str(),
                "landlock_abi": plan.abi,
                "allow_network": !plan.block_network,
                "ipc_neural_bus": plan.permissions.ipc_neural_bus,
                "data_dir": plan.data_dir,
                "read_only_count": plan.read_only_paths.len(),
                "read_write_count": plan.read_write_paths.len(),
                "rejected_paths": plan.rejected_paths,
                "hard_deny_paths": plan.hard_deny_paths,
            }))
            .unwrap_or_default()
        );
        return;
    }

    let Some(start_idx) = cmd_start else {
        eprintln!("Error: Missing command after '--'");
        std::process::exit(1);
    };
    if start_idx >= args.len() {
        eprintln!("Error: Empty command after '--'");
        std::process::exit(1);
    }

    let target_cmd = &args[start_idx];
    let target_args = &args[start_idx + 1..];

    let ruleset_fd_opt = match create_ruleset_for_plan(&plan) {
        Ok(fd) => fd,
        Err(e) => {
            eprintln!("Sandbox ruleset error: {}", e);
            std::process::exit(1);
        }
    };

    let mut cmd = Command::new(target_cmd);
    cmd.args(target_args);

    for k in STRIP_SENSITIVE_ENVS {
        cmd.env_remove(k);
    }
    cmd.env("FLOWORK_SANDBOXED", "1");
    cmd.env("FLOWORK_APP_ID", &plan.app_id);
    cmd.env("FLOWORK_DATA_DIR", &plan.data_dir);
    cmd.env("FLOWORK_ROOT", "/opt/floworkos");
    cmd.env("FLOWORK_SANDBOX_PROFILE", plan.permissions.profile.as_str());

    if trace_only {
        eprintln!(
            "[flowork-sandbox-exec] app={} profile={} abi={} net_blocked={} ro={} rw={}",
            plan.app_id,
            plan.permissions.profile.as_str(),
            plan.abi,
            plan.block_network,
            plan.read_only_paths.len(),
            plan.read_write_paths.len()
        );
    }

    if detach {
        let log_path = format!("/tmp/flowork_launch_{}.log", plan.app_id);
        let log_file = OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&log_path);
        cmd.stdin(Stdio::null());
        if let Ok(lf) = log_file {
            if let Ok(lf_err) = lf.try_clone() {
                cmd.stdout(Stdio::from(lf));
                cmd.stderr(Stdio::from(lf_err));
            }
        }
        unsafe {
            cmd.pre_exec(move || {
                libc::setsid();
                if let Some(fd) = ruleset_fd_opt {
                    if let Err(errno) = restrict_self_raw(fd) {
                        return Err(std::io::Error::from_raw_os_error(errno));
                    }
                }
                Ok(())
            });
        }
        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => {
                eprintln!("Failed spawning sandboxed app {}: {}", target_cmd, e);
                std::process::exit(1);
            }
        };
        if let Some(fd) = ruleset_fd_opt {
            unsafe { libc::close(fd) };
        }
        thread::sleep(Duration::from_millis(250));
        match child.try_wait() {
            Ok(Some(status)) => {
                let msg = std::fs::read_to_string(&log_path).unwrap_or_default();
                let preview: String = msg.lines().take(4).collect::<Vec<_>>().join(" | ");
                if preview.contains("PermissionError")
                    || preview.contains("Permission denied")
                    || preview.contains("Operation not permitted")
                {
                    publish_sandbox_violation(
                        &plan.app_id,
                        plan.permissions.profile.as_str(),
                        &preview,
                    );
                }
                eprintln!(
                    "Sandboxed launch failure for {} (exited {:?}): {}",
                    target_cmd,
                    status.code(),
                    preview
                );
                std::process::exit(status.code().unwrap_or(1));
            }
            Ok(None) => {
                println!(
                    "{}",
                    json!({
                        "status": "running",
                        "pid": child.id(),
                        "cmd": target_cmd,
                        "app_id": plan.app_id,
                        "profile": plan.permissions.profile.as_str(),
                        "landlock_abi": plan.abi,
                        "network_blocked": plan.block_network
                    })
                );
                return;
            }
            Err(e) => {
                eprintln!("Probe error: {}", e);
                std::process::exit(1);
            }
        }
    }

    // Foreground supervised execution with EACCES/violation detection
    cmd.stdin(Stdio::inherit());
    cmd.stdout(Stdio::inherit());
    cmd.stderr(Stdio::piped());

    unsafe {
        cmd.pre_exec(move || {
            if let Some(fd) = ruleset_fd_opt {
                if let Err(errno) = restrict_self_raw(fd) {
                    return Err(std::io::Error::from_raw_os_error(errno));
                }
            }
            Ok(())
        });
    }

    let mut child = match cmd.spawn() {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Failed spawning {}: {}", target_cmd, e);
            std::process::exit(1);
        }
    };

    if let Some(fd) = ruleset_fd_opt {
        unsafe { libc::close(fd) };
    }

    let mut err_buf = String::new();
    if let Some(mut stderr_pipe) = child.stderr.take() {
        let mut raw = Vec::new();
        let _ = stderr_pipe.read_to_end(&mut raw);
        err_buf = String::from_utf8_lossy(&raw).to_string();
        if !err_buf.is_empty() {
            eprint!("{}", err_buf);
        }
    }

    let status = child.wait().ok();
    let code = status.and_then(|s| s.code()).unwrap_or(1);

    if code != 0
        && (err_buf.contains("PermissionError")
            || err_buf.contains("Permission denied")
            || err_buf.contains("Operation not permitted")
            || err_buf.contains("Errno 13"))
    {
        publish_sandbox_violation(&plan.app_id, plan.permissions.profile.as_str(), &err_buf);
    }

    std::process::exit(code);
}
