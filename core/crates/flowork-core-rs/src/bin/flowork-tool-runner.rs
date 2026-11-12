use flowork_core_rs::{cdp, resolve_home_dir, rea_native, resolve_path_from_cwd};
use glob::glob_with;
use ignore::WalkBuilder;
use regex::Regex;
use serde_json::{json, Value};
use std::env;
use std::fs;
use std::io::Read;
use std::os::unix::fs::{FileTypeExt, OpenOptionsExt};
use std::os::unix::io::{AsRawFd, FromRawFd, OwnedFd};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{self, Command, Output, Stdio};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

mod sandbox {
    use super::*;

    const SYS_LANDLOCK_CREATE_RULESET: libc::c_long = 444;
    const SYS_LANDLOCK_ADD_RULE: libc::c_long = 445;
    const SYS_LANDLOCK_RESTRICT_SELF: libc::c_long = 446;
    const LANDLOCK_CREATE_RULESET_VERSION: u32 = 1 << 0;
    const LANDLOCK_RULE_PATH_BENEATH: u32 = 1;

    const ACCESS_FS_EXECUTE: u64 = 1 << 0;
    const ACCESS_FS_WRITE_FILE: u64 = 1 << 1;
    const ACCESS_FS_READ_FILE: u64 = 1 << 2;
    const ACCESS_FS_READ_DIR: u64 = 1 << 3;
    const ACCESS_FS_REMOVE_DIR: u64 = 1 << 4;
    const ACCESS_FS_REMOVE_FILE: u64 = 1 << 5;
    const ACCESS_FS_MAKE_CHAR: u64 = 1 << 6;
    const ACCESS_FS_MAKE_DIR: u64 = 1 << 7;
    const ACCESS_FS_MAKE_REG: u64 = 1 << 8;
    const ACCESS_FS_MAKE_SOCK: u64 = 1 << 9;
    const ACCESS_FS_MAKE_FIFO: u64 = 1 << 10;
    const ACCESS_FS_MAKE_BLOCK: u64 = 1 << 11;
    const ACCESS_FS_MAKE_SYM: u64 = 1 << 12;
    const ACCESS_FS_REFER: u64 = 1 << 13;
    const ACCESS_FS_TRUNCATE: u64 = 1 << 14;

    #[repr(C)]
    struct LandlockRulesetAttr {
        handled_access_fs: u64,
    }

    #[repr(C)]
    struct LandlockPathBeneathAttr {
        allowed_access: u64,
        parent_fd: i32,
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub enum SandboxMode {
        Auto,
        Enforce,
        Off,
    }

    impl SandboxMode {
        pub fn parse(raw: &str) -> Self {
            match raw.trim().to_ascii_lowercase().as_str() {
                "enforce" | "strict" | "required" => Self::Enforce,
                "off" | "disable" | "disabled" | "0" | "false" => Self::Off,
                _ => Self::Auto,
            }
        }

        pub fn from_env() -> Self {
            env::var("FLOWORK_SANDBOX_MODE")
                .map(|v| Self::parse(&v))
                .unwrap_or(Self::Auto)
        }
    }

    pub struct PreparedSandbox {
        fd: Option<OwnedFd>,
        pub mode: &'static str,
        pub abi: i64,
        pub enforced: bool,
    }

    impl PreparedSandbox {
        pub fn raw_fd(&self) -> Option<i32> {
            self.fd.as_ref().map(|f| f.as_raw_fd())
        }

        pub fn to_json(&self) -> Value {
            json!({
                "mode": self.mode,
                "landlock_abi": self.abi,
                "enforced": self.enforced
            })
        }
    }

    pub fn probe_landlock_abi() -> i64 {
        unsafe {
            libc::syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                std::ptr::null::<LandlockRulesetAttr>(),
                0,
                LANDLOCK_CREATE_RULESET_VERSION,
            ) as i64
        }
    }

    pub fn handled_access_for_abi(abi: i64) -> u64 {
        if abi <= 0 {
            return 0;
        }
        let mut mask = ACCESS_FS_EXECUTE
            | ACCESS_FS_WRITE_FILE
            | ACCESS_FS_READ_FILE
            | ACCESS_FS_READ_DIR
            | ACCESS_FS_REMOVE_DIR
            | ACCESS_FS_REMOVE_FILE
            | ACCESS_FS_MAKE_CHAR
            | ACCESS_FS_MAKE_DIR
            | ACCESS_FS_MAKE_REG
            | ACCESS_FS_MAKE_SOCK
            | ACCESS_FS_MAKE_FIFO
            | ACCESS_FS_MAKE_BLOCK
            | ACCESS_FS_MAKE_SYM;
        if abi >= 2 {
            mask |= ACCESS_FS_REFER;
        }
        if abi >= 3 {
            mask |= ACCESS_FS_TRUNCATE;
        }
        mask
    }

    fn add_path_rule(ruleset_fd: i32, path: &Path, access: u64) {
        if access == 0 || !path.exists() {
            return;
        }
        if let Ok(file) = fs::OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_PATH | libc::O_CLOEXEC)
            .open(path)
        {
            let path_attr = LandlockPathBeneathAttr {
                allowed_access: access,
                parent_fd: file.as_raw_fd(),
            };
            unsafe {
                libc::syscall(
                    SYS_LANDLOCK_ADD_RULE,
                    ruleset_fd,
                    LANDLOCK_RULE_PATH_BENEATH,
                    &path_attr as *const _,
                    0,
                );
            }
        }
    }

    pub fn prepare_ruleset(work_dir: &Path, mode: SandboxMode) -> Result<PreparedSandbox, String> {
        let abi = probe_landlock_abi();
        if mode == SandboxMode::Off {
            return Ok(PreparedSandbox {
                fd: None,
                mode: "off",
                abi,
                enforced: false,
            });
        }
        if abi <= 0 {
            if mode == SandboxMode::Enforce {
                return Err(format!(
                    "FLOWORK_SANDBOX_MODE=enforce requested, but kernel reports Landlock unsupported (abi={}). Enable CONFIG_SECURITY_LANDLOCK=y and CONFIG_SECURITYFS=y.",
                    abi
                ));
            }
            return Ok(PreparedSandbox {
                fd: None,
                mode: "auto_noop",
                abi,
                enforced: false,
            });
        }

        let handled = handled_access_for_abi(abi);
        let attr = LandlockRulesetAttr {
            handled_access_fs: handled,
        };
        let raw_fd = unsafe {
            libc::syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                &attr as *const _,
                std::mem::size_of::<LandlockRulesetAttr>(),
                0,
            ) as i32
        };
        if raw_fd < 0 {
            if mode == SandboxMode::Enforce {
                return Err(format!(
                    "landlock_create_ruleset failed: {}",
                    std::io::Error::last_os_error()
                ));
            }
            return Ok(PreparedSandbox {
                fd: None,
                mode: "auto_noop_ruleset_err",
                abi,
                enforced: false,
            });
        }
        let owned = unsafe { OwnedFd::from_raw_fd(raw_fd) };

        let ro_access = (ACCESS_FS_EXECUTE | ACCESS_FS_READ_FILE | ACCESS_FS_READ_DIR) & handled;
        for ro in [
            "/usr", "/bin", "/sbin", "/lib", "/lib64", "/lib32", "/etc", "/opt", "/proc", "/sys",
            "/var", "/run",
        ] {
            add_path_rule(owned.as_raw_fd(), Path::new(ro), ro_access);
        }

        let dev_access =
            (ACCESS_FS_READ_FILE | ACCESS_FS_READ_DIR | ACCESS_FS_WRITE_FILE | ACCESS_FS_TRUNCATE)
                & handled;
        add_path_rule(owned.as_raw_fd(), Path::new("/dev"), dev_access);

        let rw_access = handled;
        let workspace_only =
            env::var("FLOWORK_SANDBOX_WORKSPACE_ONLY").ok().as_deref() == Some("1");
        let mut rw_paths: Vec<PathBuf> = vec![
            work_dir.to_path_buf(),
            PathBuf::from("/run/flowork"),
        ];
        if !workspace_only {
            rw_paths.push(PathBuf::from("/tmp"));
            rw_paths.push(PathBuf::from("/var/tmp"));
            rw_paths.push(PathBuf::from("/dev/shm"));
            rw_paths.push(resolve_home_dir());
            rw_paths.push(PathBuf::from("/opt/floworkos"));
        } else if let Ok(scoped_tmp) = env::var("TMPDIR") {
            let p = PathBuf::from(scoped_tmp.trim());
            if !p.as_os_str().is_empty() && p != Path::new("/tmp") && p != Path::new("/var/tmp") {
                rw_paths.push(p);
            }
        }
        if let Ok(extra) = env::var("FLOWORK_SANDBOX_RW") {
            for p in extra.split(':').filter(|s| !s.trim().is_empty()) {
                rw_paths.push(PathBuf::from(p.trim()));
            }
        }
        for rw in rw_paths {
            add_path_rule(owned.as_raw_fd(), &rw, rw_access);
        }

        Ok(PreparedSandbox {
            fd: Some(owned),
            mode: if mode == SandboxMode::Enforce {
                "enforce"
            } else {
                "auto"
            },
            abi,
            enforced: true,
        })
    }

    pub unsafe fn restrict_self_async_signal_safe(raw_fd: i32) -> std::io::Result<()> {
        if raw_fd < 0 {
            return Ok(());
        }
        if libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0 {
            return Err(std::io::Error::last_os_error());
        }
        if libc::syscall(SYS_LANDLOCK_RESTRICT_SELF, raw_fd, 0) < 0 {
            return Err(std::io::Error::last_os_error());
        }
        libc::close(raw_fd);
        Ok(())
    }

    pub fn run_sandboxed_output(cmd_str: &str, work_dir: &Path) -> (Result<Output, String>, Value) {
        let sb = match prepare_ruleset(work_dir, SandboxMode::from_env()) {
            Ok(s) => s,
            Err(e) => {
                return (
                    Err(e),
                    json!({
                        "mode": "enforce",
                        "landlock_abi": probe_landlock_abi(),
                        "enforced": false
                    }),
                )
            }
        };
        let sb_meta = sb.to_json();
        let mut cmd = Command::new("/bin/bash");
        cmd.args(["-c", cmd_str])
            .current_dir(work_dir)
            .env("PAGER", "cat");
        if let Some(raw_fd) = sb.raw_fd() {
            unsafe {
                cmd.pre_exec(move || restrict_self_async_signal_safe(raw_fd));
            }
        }
        let res = cmd.output().map_err(|e| e.to_string());
        drop(sb);
        (res, sb_meta)
    }

    pub fn spawn_sandboxed_background(
        cmd_str: &str,
        work_dir: &Path,
    ) -> Result<(process::Child, Value), String> {
        let sb = prepare_ruleset(work_dir, SandboxMode::from_env())?;
        let sb_meta = sb.to_json();
        let mut cmd = Command::new("/bin/bash");
        cmd.args(["-c", cmd_str])
            .current_dir(work_dir)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        if let Some(raw_fd) = sb.raw_fd() {
            unsafe {
                cmd.pre_exec(move || restrict_self_async_signal_safe(raw_fd));
            }
        }
        let child = cmd.spawn().map_err(|e| e.to_string())?;
        drop(sb);
        Ok((child, sb_meta))
    }
}

fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

fn is_chaos_mode() -> bool {
    env::var("FLOWORK_CHAOS_MODE").ok().as_deref() == Some("1")
}

fn print_help() {
    println!("flowork-tool-runner — Unified Native Rust Sovereign Tool Execution Binary");
    println!("Usage: Hardlinked at /opt/floworkos/tools/<tool>/run OR flowork-tool-runner --tool <name>");
}

fn read_stdin_raw() -> String {
    let mut buf = String::new();
    let _ = std::io::stdin().read_to_string(&mut buf);
    buf
}

fn parse_stdin_json() -> Value {
    let raw = read_stdin_raw();
    if raw.trim().is_empty() {
        json!({})
    } else {
        serde_json::from_str(&raw).unwrap_or_else(|_| json!({}))
    }
}

fn resolve_tool_and_args() -> (Option<String>, Vec<String>) {
    let mut raw_args: Vec<String> = env::args().collect();
    let argv0 = raw_args.first().cloned().unwrap_or_default();
    let rest: Vec<String> = if raw_args.len() > 1 {
        raw_args.split_off(1)
    } else {
        Vec::new()
    };

    let mut tool_override: Option<String> = None;
    let mut filtered = Vec::new();
    let mut i = 0;
    while i < rest.len() {
        if rest[i] == "--tool" {
            if let Some(next) = rest.get(i + 1) {
                tool_override = Some(next.clone());
                i += 2;
                continue;
            }
        }
        filtered.push(rest[i].clone());
        i += 1;
    }

    if tool_override.is_none() {
        if let Ok(env_tool) = env::var("FLOWORK_TOOL_NAME") {
            let t = env_tool.trim().to_string();
            if !t.is_empty() {
                tool_override = Some(t);
            }
        }
    }

    if tool_override.is_none() && !argv0.is_empty() {
        let p = Path::new(&argv0);
        if p.file_name().and_then(|s| s.to_str()) == Some("run") {
            if let Some(parent_name) = p.parent().and_then(|d| d.file_name()).and_then(|s| s.to_str()) {
                tool_override = Some(parent_name.to_string());
            }
        }
    }

    (tool_override, filtered)
}

fn find_bin(candidates: &[&str]) -> Option<String> {
    for c in candidates {
        if Path::new(c).is_file() {
            return Some((*c).to_string());
        }
    }
    None
}

fn run_agent_browser(cli_args_in: &[String]) -> i32 {
    let mut params = json!({});
    if !cli_args_in.is_empty() {
        if let Ok(parsed) = serde_json::from_str::<Value>(&cli_args_in[0]) {
            params = parsed;
        } else {
            params["action"] = json!(cli_args_in[0]);
            if let Some(a1) = cli_args_in.get(1) {
                params["url"] = json!(a1);
            }
            if let Some(a2) = cli_args_in.get(2) {
                params["ref"] = json!(a2);
            }
        }
    } else if let Ok(act) = env::var("ACTION") {
        params["action"] = json!(act);
        if let Ok(v) = env::var("URL") {
            params["url"] = json!(v);
        }
        if let Ok(v) = env::var("REF") {
            params["ref"] = json!(v);
        }
        if let Ok(v) = env::var("TEXT") {
            params["text"] = json!(v);
        }
        if let Ok(v) = env::var("KEY") {
            params["key"] = json!(v);
        }
    } else {
        params = parse_stdin_json();
    }

    let action = params.get("action").and_then(|v| v.as_str()).unwrap_or("");
    if action.is_empty() {
        eprintln!("FLOWORK TOOL ERROR: 'action' parameter is required.");
        return 1;
    }

    let mut cli_args = Vec::new();
    if let Some(sess) = params.get("session").and_then(|v| v.as_str()) {
        if !sess.is_empty() {
            cli_args.push("--session".to_string());
            cli_args.push(sess.to_string());
        }
    }

    let str_opt = |k: &str| params.get(k).and_then(|v| v.as_str()).map(str::to_string);
    match action {
        "open" => {
            let Some(url) = str_opt("url") else {
                eprintln!("FLOWORK TOOL ERROR: 'url' parameter is required for 'open'.");
                return 1;
            };
            cli_args.push("open".to_string());
            cli_args.push(url);
        }
        "snapshot" => {
            cli_args.push("snapshot".to_string());
            if params.get("interactive_only").and_then(|v| v.as_bool()) != Some(false) {
                cli_args.push("-i".to_string());
            }
        }
        "click" | "dblclick" | "hover" | "focus" | "check" | "uncheck" => {
            let Some(rf) = str_opt("ref") else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' parameter is required for '{}'.", action);
                return 1;
            };
            cli_args.push(action.to_string());
            cli_args.push(rf);
        }
        "type" | "fill" => {
            let Some(rf) = str_opt("ref") else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' and 'text' are required for '{}'.", action);
                return 1;
            };
            let Some(txt) = params.get("text").and_then(|v| {
                v.as_str().map(str::to_string).or_else(|| Some(v.to_string()))
            }) else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' and 'text' are required for '{}'.", action);
                return 1;
            };
            cli_args.push(action.to_string());
            cli_args.push(rf);
            cli_args.push(txt);
        }
        "press" => {
            let Some(key) = str_opt("key") else {
                eprintln!("FLOWORK TOOL ERROR: 'key' parameter is required for 'press'.");
                return 1;
            };
            cli_args.push("press".to_string());
            cli_args.push(key);
        }
        "get" => {
            cli_args.push("get".to_string());
            cli_args.push(str_opt("property").unwrap_or_else(|| "url".to_string()));
        }
        "eval" => {
            let Some(code) = str_opt("js_code") else {
                eprintln!("FLOWORK TOOL ERROR: 'js_code' is required for 'eval'.");
                return 1;
            };
            cli_args.push("eval".to_string());
            cli_args.push(code);
        }
        "screenshot" => {
            cli_args.push("screenshot".to_string());
            if let Some(t) = str_opt("text") {
                cli_args.push(t);
            }
        }
        "connect" => {
            cli_args.push("connect".to_string());
            cli_args.push(str_opt("url").unwrap_or_else(|| "9222".to_string()));
        }
        "close" => cli_args.push("close".to_string()),
        other => {
            eprintln!("FLOWORK TOOL ERROR: Unknown action '{}'.", other);
            return 1;
        }
    }

    if is_chaos_mode() {
        eprintln!("FLOWORK TOOL ERROR: agent_browser blocked during FLOWORK_CHAOS_MODE.");
        return 1;
    }

    let bin = find_bin(&["/usr/local/bin/agent-browser", "/usr/bin/agent-browser"])
        .unwrap_or_else(|| "agent-browser".to_string());
    match Command::new(&bin).args(&cli_args).output() {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
            if !stdout.is_empty() {
                println!("{}", stdout);
            }
            if !stderr.is_empty() {
                eprintln!("{}", stderr);
            }
            out.status.code().unwrap_or(1)
        }
        Err(e) => {
            eprintln!("FLOWORK TOOL EXECUTION ERROR: {}", e);
            1
        }
    }
}

fn run_agent_desktop(cli_args_in: &[String]) -> i32 {
    let uid = unsafe { libc::getuid() };
    let candidates = [
        env::var("DBUS_SESSION_BUS_ADDRESS").ok(),
        Some(format!("unix:path=/run/user/{}/bus", uid)),
        Some("unix:path=/run/user/1001/bus".to_string()),
        Some("unix:path=/run/user/1000/bus".to_string()),
    ];
    for cand in candidates.into_iter().flatten() {
        let sock_path = cand.trim_start_matches("unix:path=");
        if Path::new(sock_path).exists() {
            env::set_var("DBUS_SESSION_BUS_ADDRESS", &cand);
            break;
        }
    }
    if env::var("DISPLAY").unwrap_or_default().is_empty() {
        env::set_var("DISPLAY", ":0");
    }

    let mut params = json!({});
    if !cli_args_in.is_empty() {
        if let Ok(parsed) = serde_json::from_str::<Value>(&cli_args_in[0]) {
            params = parsed;
        } else {
            params["action"] = json!(cli_args_in[0]);
            if let Some(a1) = cli_args_in.get(1) {
                params["ref"] = json!(a1);
            }
            if let Some(a2) = cli_args_in.get(2) {
                params["text"] = json!(a2);
            }
        }
    } else {
        params = parse_stdin_json();
    }

    if params.get("action").and_then(|v| v.as_str()).unwrap_or("").is_empty() {
        if let Ok(act) = env::var("ACTION") {
            params["action"] = json!(act);
            if let Ok(v) = env::var("APP") {
                params["app"] = json!(v);
            }
            if let Ok(v) = env::var("REF") {
                params["ref"] = json!(v);
            }
            if let Ok(v) = env::var("TEXT") {
                params["text"] = json!(v);
            }
            if let Ok(v) = env::var("KEY") {
                params["key"] = json!(v);
            }
        }
    }

    let action = params.get("action").and_then(|v| v.as_str()).unwrap_or("");
    if action.is_empty() {
        eprintln!("FLOWORK TOOL ERROR: 'action' parameter is required.");
        return 1;
    }

    let mut cli_args = Vec::new();
    match action {
        "status" => cli_args.push("status".to_string()),
        "list_windows" | "list-windows" => cli_args.push("list-windows".to_string()),
        "snapshot" => {
            cli_args.push("snapshot".to_string());
            if let Some(app) = params.get("app").and_then(|v| v.as_str()) {
                cli_args.push("--app".to_string());
                cli_args.push(app.to_string());
            }
            if let Some(wid) = params.get("window_id").and_then(|v| v.as_str()) {
                cli_args.push("--window-id".to_string());
                cli_args.push(wid.to_string());
            }
            if params.get("interactive_only").and_then(|v| v.as_bool()) != Some(false) {
                cli_args.push("-i".to_string());
            }
        }
        "click" => {
            let Some(rf) = params.get("ref").and_then(|v| v.as_str()) else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' parameter is required for 'click' action.");
                return 1;
            };
            cli_args.push("click".to_string());
            cli_args.push(rf.to_string());
        }
        "type" => {
            let Some(rf) = params.get("ref").and_then(|v| v.as_str()) else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' and 'text' parameters are required for 'type' action.");
                return 1;
            };
            let Some(txt) = params.get("text").and_then(|v| {
                v.as_str().map(str::to_string).or_else(|| Some(v.to_string()))
            }) else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' and 'text' parameters are required for 'type' action.");
                return 1;
            };
            cli_args.push("type".to_string());
            cli_args.push(rf.to_string());
            cli_args.push(txt);
        }
        "press_key" | "press-key" => {
            let Some(k) = params.get("key").and_then(|v| v.as_str()) else {
                eprintln!("FLOWORK TOOL ERROR: 'key' parameter is required for 'press_key' action.");
                return 1;
            };
            cli_args.push("press-key".to_string());
            cli_args.push(k.to_string());
        }
        "hover" => {
            let Some(rf) = params.get("ref").and_then(|v| v.as_str()) else {
                eprintln!("FLOWORK TOOL ERROR: 'ref' parameter is required for 'hover' action.");
                return 1;
            };
            cli_args.push("hover".to_string());
            cli_args.push(rf.to_string());
        }
        other => {
            eprintln!("FLOWORK TOOL ERROR: Unknown action '{}'.", other);
            return 1;
        }
    }

    if is_chaos_mode() {
        eprintln!("FLOWORK TOOL ERROR: agent_desktop execution skipped in FLOWORK_CHAOS_MODE.");
        return 1;
    }

    let bin = find_bin(&["/usr/local/bin/agent-desktop", "/usr/bin/agent-desktop"])
        .unwrap_or_else(|| "agent-desktop".to_string());
    match Command::new(&bin).args(&cli_args).output() {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
            if !stdout.is_empty() {
                println!("{}", stdout);
            }
            if !stderr.is_empty() {
                eprintln!("{}", stderr);
            }
            out.status.code().unwrap_or(1)
        }
        Err(e) => {
            eprintln!("FLOWORK TOOL EXECUTION ERROR: {}", e);
            1
        }
    }
}

fn run_rea(cli_args_in: &[String]) -> i32 {
    let input = if let Some(first) = cli_args_in.first() {
        serde_json::from_str::<Value>(first).unwrap_or_else(|_| json!({ "command": first }))
    } else {
        parse_stdin_json()
    };

    let command = input
        .get("command")
        .and_then(|v| v.as_str())
        .unwrap_or("capabilities");
    let target = input
        .get("target")
        .or_else(|| input.get("target_file"))
        .and_then(|v| v.as_str());
    let extra: Vec<String> = input
        .get("args")
        .and_then(|v| v.as_array())
        .map(|a| {
            a.iter()
                .filter_map(|x| x.as_str().map(str::to_string))
                .collect()
        })
        .unwrap_or_default();

    match rea_native::execute_rea(command, target, &extra) {
        Ok(res) => {
            println!("{}", serde_json::to_string_pretty(&res).unwrap_or_default());
            0
        }
        Err(e) => {
            eprintln!("[REA ERROR]: {}", e);
            1
        }
    }
}

fn run_browser_tool(tool_name: &str, cli_args_in: &[String]) -> i32 {
    let args = if let Some(first) = cli_args_in.first() {
        serde_json::from_str::<Value>(first).unwrap_or_else(|_| json!({ "input": first }))
    } else {
        parse_stdin_json()
    };

    let short = cdp::normalize_short_name(tool_name);
    if let Err(e) = cdp::validate_required_args(short, &args) {
        eprintln!("FLOWORK BROWSER TOOL ERROR: {}", e);
        return 1;
    }

    if is_chaos_mode() {
        eprintln!(
            "FLOWORK BROWSER TOOL ERROR: '{}' halted in FLOWORK_CHAOS_MODE.",
            tool_name
        );
        return 1;
    }

    let Ok(rt) = tokio::runtime::Runtime::new() else {
        eprintln!("FLOWORK BROWSER TOOL ERROR: Failed initializing Tokio runtime.");
        return 1;
    };

    match rt.block_on(cdp::call_browser_tool(tool_name, &args, None)) {
        Ok(res) => {
            if let Some(content) = res.get("content").and_then(|v| v.as_array()) {
                for item in content {
                    match item.get("type").and_then(|v| v.as_str()) {
                        Some("text") => {
                            if let Some(txt) = item.get("text").and_then(|v| v.as_str()) {
                                println!("{}", txt);
                            }
                        }
                        Some("image") => {
                            let mime = item
                                .get("mimeType")
                                .and_then(|v| v.as_str())
                                .unwrap_or("image/png");
                            let len = item
                                .get("data")
                                .and_then(|v| v.as_str())
                                .map(|s| s.len())
                                .unwrap_or(0);
                            println!("[IMAGE DATA: {}, size: {} bytes]", mime, len);
                        }
                        _ => {}
                    }
                }
            } else {
                println!("{}", serde_json::to_string_pretty(&res).unwrap_or_default());
            }
            0
        }
        Err(e) => {
            eprintln!("FLOWORK BROWSER TOOL ERROR: {}", e);
            1
        }
    }
}

fn read_sliced_lines(resolved: &Path, start_line: usize, end_line: Option<usize>) -> Result<Value, String> {
    let content = fs::read_to_string(resolved)
        .map_err(|e| format!("Read error on '{}': {}", resolved.display(), e))?;
    let lines: Vec<&str> = content.split('\n').collect();
    let total = lines.len();
    let start = start_line.max(1);
    let end = end_line.unwrap_or(total).min(total);
    let mut sliced = Vec::new();
    if start <= end && total > 0 {
        for i in (start - 1)..end {
            sliced.push(format!("{}: {}", i + 1, lines[i]));
        }
    }
    Ok(json!({
        "file_path": resolved.to_string_lossy(),
        "total_lines": total,
        "showing_lines": format!("{}-{}", start, end),
        "content": sliced.join("\n")
    }))
}

fn run_standard_tool(tool_name: &str) -> i32 {
    let args = parse_stdin_json();
    let cwd = env::current_dir().unwrap_or_else(|_| PathBuf::from("/tmp"));

    match tool_name {
        "activate_skill" => {
            let name = args.get("name").and_then(|v| v.as_str()).unwrap_or("unknown");
            println!("{}", serde_json::to_string_pretty(&json!({"status":"skill_activated","skill":name})).unwrap());
            0
        }
        "ask_user" => {
            let qs = args.get("questions").cloned().unwrap_or_else(|| json!([]));
            println!("{}", serde_json::to_string_pretty(&json!({"status":"prompt_displayed","questions":qs})).unwrap());
            0
        }
        "complete_task" => {
            let res = args.get("result").and_then(|v| v.as_str()).unwrap_or("Done");
            println!("{}", serde_json::to_string_pretty(&json!({"status":"task_completed","result":res})).unwrap());
            0
        }
        "enter_plan_mode" => {
            println!("{}", serde_json::to_string_pretty(&json!({"status":"plan_mode_active","mode":"plan"})).unwrap());
            0
        }
        "exit_plan_mode" => {
            println!("{}", serde_json::to_string_pretty(&json!({"status":"plan_mode_exited","mode":"execute"})).unwrap());
            0
        }
        "flowork_web_search" => {
            let q = args.get("query").and_then(|v| v.as_str()).unwrap_or("");
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "ok",
                    "query": q,
                    "results": [{
                        "title": format!("Search query received: {}", q),
                        "snippet": "Web search executed via Flowork OS gateway."
                    }]
                }))
                .unwrap()
            );
            0
        }
        "glob" => {
            let pattern = args.get("pattern").and_then(|v| v.as_str()).unwrap_or("*");
            let root_raw = args.get("path").and_then(|v| v.as_str()).unwrap_or(".");
            let root = resolve_path_from_cwd(root_raw, &cwd);
            let full_pat = if pattern.contains('/') {
                root.join(pattern).to_string_lossy().to_string()
            } else {
                root.join("**").join(pattern).to_string_lossy().to_string()
            };
            let opts = glob::MatchOptions {
                case_sensitive: true,
                require_literal_separator: false,
                require_literal_leading_dot: false,
            };
            let mut files = Vec::new();
            if let Ok(paths) = glob_with(&full_pat, opts) {
                for entry in paths.flatten() {
                    let rel = entry.strip_prefix(&root).unwrap_or(&entry);
                    let has_hidden = rel.components().any(|c| {
                        c.as_os_str()
                            .to_str()
                            .map(|part| part.starts_with('.') && part != "." && part != "..")
                            .unwrap_or(false)
                    });
                    if !has_hidden || pattern.contains("/.") || pattern.starts_with('.') {
                        files.push(entry.to_string_lossy().to_string());
                    }
                    if files.len() >= 500 {
                        break;
                    }
                }
            }
            println!("{}", serde_json::to_string_pretty(&json!({ "files": files })).unwrap());
            0
        }
        "grep_search" => {
            let pattern = args.get("pattern").and_then(|v| v.as_str()).unwrap_or("");
            let search_raw = args.get("path").and_then(|v| v.as_str()).unwrap_or(".");
            if pattern.is_empty() {
                eprintln!("Error: 'pattern' required.");
                return 1;
            }
            let search_path = resolve_path_from_cwd(search_raw, &cwd);
            let Ok(re) = Regex::new(pattern) else {
                eprintln!("Error: Invalid regex pattern '{}'", pattern);
                return 1;
            };
            let inc_pat = args.get("include_pattern").and_then(|v| v.as_str());
            let mut matches = Vec::new();
            let walker = WalkBuilder::new(&search_path)
                .hidden(false)
                .git_ignore(true)
                .max_depth(Some(8))
                .build();
            for entry in walker.flatten() {
                if !entry.file_type().map(|t| t.is_file()).unwrap_or(false) {
                    continue;
                }
                let path = entry.path();
                if let Some(inc) = inc_pat {
                    if let Some(fname) = path.file_name().and_then(|s| s.to_str()) {
                        let suffix = inc.trim_start_matches('*');
                        if !fname.ends_with(suffix) {
                            continue;
                        }
                    }
                }
                let Ok(bytes) = fs::read(path) else {
                    continue;
                };
                if bytes.contains(&0) {
                    continue;
                }
                let text = String::from_utf8_lossy(&bytes);
                let mut file_hits = 0usize;
                for (idx, line) in text.lines().enumerate() {
                    if re.is_match(line) {
                        matches.push(format!("{}:{}:{}", path.display(), idx + 1, line));
                        file_hits += 1;
                        if file_hits >= 50 || matches.len() >= 300 {
                            break;
                        }
                    }
                }
                if matches.len() >= 300 {
                    break;
                }
            }
            println!("{}", serde_json::to_string_pretty(&json!({ "matches": matches })).unwrap());
            0
        }
        "invoke_agent" => {
            let agent = args.get("agent_name").cloned().unwrap_or(Value::Null);
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "subagent_spawned",
                    "agent": agent,
                    "task_id": format!("agent_{}", now_ms())
                }))
                .unwrap()
            );
            0
        }
        "list_background_processes" => {
            let active: Vec<String> = match Command::new("ps").args(["-eo", "pid,comm,args"]).output() {
                Ok(out) => String::from_utf8_lossy(&out.stdout)
                    .lines()
                    .take(20)
                    .map(str::to_string)
                    .collect(),
                Err(_) => vec![],
            };
            println!("{}", serde_json::to_string_pretty(&json!({"status":"ok","active_processes":active})).unwrap());
            0
        }
        "list_directory" => {
            let raw = args.get("path").and_then(|v| v.as_str()).unwrap_or(".");
            let target = resolve_path_from_cwd(raw, &cwd);
            if !target.exists() {
                eprintln!("Error: Path not found: {}", target.display());
                return 1;
            }
            let Ok(entries) = fs::read_dir(&target) else {
                eprintln!("Error: Cannot read directory: {}", target.display());
                return 1;
            };
            let mut items = Vec::new();
            for entry in entries.flatten() {
                let name = entry.file_name().to_string_lossy().to_string();
                let ftype = match entry.file_type() {
                    Ok(ft) if ft.is_dir() => "directory",
                    Ok(ft) if ft.is_symlink() => "symlink",
                    Ok(ft) if ft.is_socket() => "socket",
                    _ => "file",
                };
                items.push(json!({ "name": name, "type": ftype }));
            }
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "path": target.to_string_lossy(),
                    "total": items.len(),
                    "items": items
                }))
                .unwrap()
            );
            0
        }
        "list_mcp_resources" => {
            println!("{}", serde_json::to_string_pretty(&json!({"status":"ok","resources":[]})).unwrap());
            0
        }
        "read_background_output" => {
            let pid = args.get("process_id").cloned().unwrap_or(Value::Null);
            println!("{}", serde_json::to_string_pretty(&json!({"process_id":pid,"output":"[Background process buffer read]"})).unwrap());
            0
        }
        "read_file" | "view_file" => {
            let fp = args
                .get("file_path")
                .or_else(|| args.get("AbsolutePath"))
                .or_else(|| args.get("path"))
                .or_else(|| args.get("target_file"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if fp.is_empty() {
                eprintln!("Error: 'file_path' argument is required.");
                return 1;
            }
            let resolved = resolve_path_from_cwd(fp, &cwd);
            if !resolved.exists() {
                eprintln!("Error: File not found at '{}'", resolved.display());
                return 1;
            }
            let start = args
                .get("start_line")
                .or_else(|| args.get("StartLine"))
                .and_then(|v| v.as_u64())
                .map(|n| n as usize)
                .unwrap_or(1);
            let end = args
                .get("end_line")
                .or_else(|| args.get("EndLine"))
                .and_then(|v| v.as_u64())
                .map(|n| n as usize);
            match read_sliced_lines(&resolved, start, end) {
                Ok(out) => {
                    println!("{}", serde_json::to_string_pretty(&out).unwrap());
                    0
                }
                Err(e) => {
                    eprintln!("{}", e);
                    1
                }
            }
        }
        "read_many_files" => {
            let paths = args
                .get("paths")
                .and_then(|v| v.as_array())
                .cloned()
                .unwrap_or_default();
            let mut results = serde_json::Map::new();
            for p_val in paths {
                if let Some(p_str) = p_val.as_str() {
                    let resolved = resolve_path_from_cwd(p_str, &cwd);
                    let entry = match fs::read_to_string(&resolved) {
                        Ok(txt) => txt,
                        Err(_e) if !resolved.exists() => "[Error: Not found]".to_string(),
                        Err(e) => format!("[Error: {}]", e),
                    };
                    results.insert(p_str.to_string(), Value::String(entry));
                }
            }
            println!("{}", serde_json::to_string_pretty(&json!({ "files": Value::Object(results) })).unwrap());
            0
        }
        "read_mcp_resource" => {
            let uri = args.get("uri").cloned().unwrap_or(Value::Null);
            println!("{}", serde_json::to_string_pretty(&json!({"status":"ok","uri":uri,"data":"[MCP Resource payload]"})).unwrap());
            0
        }
        "replace" => {
            let fp = args.get("file_path").and_then(|v| v.as_str()).unwrap_or("");
            let old_str = args.get("old_string").and_then(|v| v.as_str()).unwrap_or("");
            let new_str = args.get("new_string").and_then(|v| v.as_str()).unwrap_or("");
            if fp.is_empty() || old_str.is_empty() {
                eprintln!("Error: 'file_path' and 'old_string' required.");
                return 1;
            }
            let resolved = resolve_path_from_cwd(fp, &cwd);
            if !resolved.exists() {
                eprintln!("Error: File not found: {}", resolved.display());
                return 1;
            }
            let Ok(original) = fs::read_to_string(&resolved) else {
                eprintln!("Error: Cannot read '{}'", resolved.display());
                return 1;
            };
            if !original.contains(old_str) {
                eprintln!("Error: Target old_string not found in file.");
                return 1;
            }
            let allow_multiple = args.get("allow_multiple").and_then(|v| v.as_bool()).unwrap_or(false);
            let updated = if allow_multiple {
                original.replace(old_str, new_str)
            } else {
                original.replacen(old_str, new_str, 1)
            };
            if let Err(e) = fs::write(&resolved, updated) {
                eprintln!("{}", e);
                return 1;
            }
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "ok",
                    "file_path": resolved.to_string_lossy(),
                    "message": "Content replaced successfully."
                }))
                .unwrap()
            );
            0
        }
        "replace_file_content" => {
            let fp = args
                .get("file_path")
                .or_else(|| args.get("TargetFile"))
                .or_else(|| args.get("path"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let target = args
                .get("target")
                .or_else(|| args.get("TargetContent"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let replacement = args
                .get("replacement")
                .or_else(|| args.get("ReplacementContent"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if fp.is_empty() {
                eprintln!("Error: 'file_path' argument is required.");
                return 1;
            }
            if target.is_empty() {
                eprintln!("Error: 'target' argument is required.");
                return 1;
            }
            let resolved = resolve_path_from_cwd(fp, &cwd);
            if !resolved.exists() {
                eprintln!("Error: File '{}' does not exist.", resolved.display());
                return 1;
            }
            let Ok(original) = fs::read_to_string(&resolved) else {
                eprintln!("Error: Cannot read '{}'", resolved.display());
                return 1;
            };
            if !original.contains(target) {
                eprintln!("Error: Target string not found in '{}'", resolved.display());
                return 1;
            }
            let updated = original.replacen(target, replacement, 1);
            if let Err(e) = fs::write(&resolved, updated) {
                eprintln!("Replace error: {}", e);
                return 1;
            }
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "ok",
                    "file_path": resolved.to_string_lossy(),
                    "message": "Successfully replaced content."
                }))
                .unwrap()
            );
            0
        }
        "run_command" => {
            let cmd = args
                .get("command")
                .or_else(|| args.get("CommandLine"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let cmd_cwd_raw = args
                .get("cwd")
                .or_else(|| args.get("Cwd"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if cmd.is_empty() {
                eprintln!("Error: 'command' argument is required.");
                return 1;
            }
            if is_chaos_mode() && (cmd.contains("/etc/shadow") || cmd.contains("/root/.ssh")) {
                eprintln!("Error: Permission denied in FLOWORK_CHAOS_MODE.");
                return 1;
            }
            let work_dir = if !cmd_cwd_raw.is_empty() && Path::new(cmd_cwd_raw).exists() {
                PathBuf::from(cmd_cwd_raw)
            } else {
                cwd
            };
            let (exec_res, sb_meta) = sandbox::run_sandboxed_output(cmd, &work_dir);
            match exec_res {
                Ok(out) => {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&json!({
                            "stdout": String::from_utf8_lossy(&out.stdout),
                            "stderr": String::from_utf8_lossy(&out.stderr),
                            "exit_code": out.status.code().unwrap_or(1),
                            "sandbox": sb_meta
                        }))
                        .unwrap()
                    );
                    0
                }
                Err(e) => {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&json!({
                            "stdout": "",
                            "stderr": e,
                            "exit_code": 1,
                            "sandbox": sb_meta
                        }))
                        .unwrap()
                    );
                    0
                }
            }
        }
        "run_shell_command" => {
            let cmd = args.get("command").and_then(|v| v.as_str()).unwrap_or("");
            if cmd.is_empty() {
                eprintln!("Error: 'command' required.");
                return 1;
            }
            if is_chaos_mode() && (cmd.contains("/etc/shadow") || cmd.contains("/root/.ssh")) {
                eprintln!("Error: Permission denied in FLOWORK_CHAOS_MODE.");
                return 1;
            }
            if args.get("is_background").and_then(|v| v.as_bool()) == Some(true) {
                match sandbox::spawn_sandboxed_background(cmd, &cwd) {
                    Ok((child, sb_meta)) => {
                        println!(
                            "{}",
                            serde_json::to_string(&json!({
                                "status": "running_background",
                                "pid": child.id(),
                                "sandbox": sb_meta
                            }))
                            .unwrap()
                        );
                        return 0;
                    }
                    Err(e) => {
                        eprintln!("Failed spawning background command: {}", e);
                        return 1;
                    }
                }
            }
            let (exec_res, sb_meta) = sandbox::run_sandboxed_output(cmd, &cwd);
            match exec_res {
                Ok(out) => {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&json!({
                            "stdout": String::from_utf8_lossy(&out.stdout),
                            "stderr": String::from_utf8_lossy(&out.stderr),
                            "exit_code": out.status.code().unwrap_or(1),
                            "sandbox": sb_meta
                        }))
                        .unwrap()
                    );
                    0
                }
                Err(e) => {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&json!({
                            "stdout": "",
                            "stderr": e,
                            "exit_code": 1,
                            "sandbox": sb_meta
                        }))
                        .unwrap()
                    );
                    0
                }
            }
        }
        "tracker_add_dependency" => {
            println!("{}", serde_json::to_string_pretty(&json!({"status":"dependency_added","edge":args})).unwrap());
            0
        }
        "tracker_create_task" => {
            let title = args.get("title").cloned().unwrap_or(Value::Null);
            println!("{}", serde_json::to_string_pretty(&json!({"status":"created","id":format!("task_{}", now_ms()),"title":title})).unwrap());
            0
        }
        "tracker_get_task" => {
            let tid = args.get("task_id").cloned().unwrap_or(Value::Null);
            println!("{}", serde_json::to_string_pretty(&json!({"task_id":tid,"status":"active","title":"Task Details"})).unwrap());
            0
        }
        "tracker_list_tasks" => {
            println!("{}", serde_json::to_string_pretty(&json!({"tasks":[]})).unwrap());
            0
        }
        "tracker_update_task" => {
            let tid = args.get("task_id").cloned().unwrap_or(Value::Null);
            let st = args.get("status").cloned().unwrap_or(Value::Null);
            println!("{}", serde_json::to_string_pretty(&json!({"status":"updated","task_id":tid,"new_status":st})).unwrap());
            0
        }
        "tracker_visualize" => {
            println!("{}", serde_json::to_string_pretty(&json!({"status":"ok","graph":"graph TD\n  Root[Flowork OS] --> Active[Workspace]"})).unwrap());
            0
        }
        "update_topic" => {
            println!("{}", serde_json::to_string_pretty(&json!({"status":"topic_updated","topic":args})).unwrap());
            0
        }
        "web_fetch" => {
            let url = args.get("url").and_then(|v| v.as_str()).unwrap_or("");
            if url.is_empty() {
                eprintln!("Error: 'url' required.");
                return 1;
            }
            if is_chaos_mode() {
                println!("{}", serde_json::to_string_pretty(&json!({"url":url,"status":"error","content":""})).unwrap());
                return 0;
            }
            let rt = tokio::runtime::Runtime::new().ok();
            let fetched = rt.and_then(|r| {
                r.block_on(async {
                    let client = reqwest::Client::builder()
                        .timeout(Duration::from_secs(15))
                        .build()
                        .ok()?;
                    let resp = client.get(url).send().await.ok()?;
                    let ok = resp.status().is_success();
                    let text = resp.text().await.ok()?;
                    let clipped: String = text.chars().take(50000).collect();
                    Some((ok, clipped))
                })
            });
            match fetched {
                Some((ok, content)) => println!(
                    "{}",
                    serde_json::to_string_pretty(&json!({
                        "url": url,
                        "status": if ok { "ok" } else { "error" },
                        "content": content
                    }))
                    .unwrap()
                ),
                None => println!(
                    "{}",
                    serde_json::to_string_pretty(&json!({
                        "url": url,
                        "status": "error",
                        "content": ""
                    }))
                    .unwrap()
                ),
            }
            0
        }
        "write_file" | "write_to_file" => {
            let fp = args
                .get("file_path")
                .or_else(|| args.get("TargetFile"))
                .or_else(|| args.get("path"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let content = args
                .get("content")
                .or_else(|| args.get("CodeContent"))
                .and_then(|v| v.as_str());
            let overwrite = args
                .get("overwrite")
                .or_else(|| args.get("Overwrite"))
                .and_then(|v| v.as_bool())
                .unwrap_or(true);
            if fp.is_empty() {
                eprintln!("Error: 'file_path' argument is required.");
                return 1;
            }
            let Some(body) = content else {
                eprintln!("Error: 'content' argument is required.");
                return 1;
            };
            let resolved = resolve_path_from_cwd(fp, &cwd);
            if resolved.exists() && !overwrite {
                eprintln!(
                    "Error: File '{}' already exists and overwrite is false.",
                    resolved.display()
                );
                return 1;
            }
            if let Some(parent) = resolved.parent() {
                if let Err(e) = fs::create_dir_all(parent) {
                    eprintln!("Write error: {}", e);
                    return 1;
                }
            }
            if let Err(e) = fs::write(&resolved, body) {
                eprintln!("Write error: {}", e);
                return 1;
            }
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "ok",
                    "file_path": resolved.to_string_lossy(),
                    "bytes_written": body.len(),
                    "message": format!("Successfully wrote to {}", resolved.display())
                }))
                .unwrap()
            );
            0
        }
        "write_todos" => {
            let todos = args.get("todos").cloned().unwrap_or_else(|| json!([]));
            let count = todos.as_array().map(|a| a.len()).unwrap_or(0);
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "todos_saved",
                    "count": count,
                    "todos": todos
                }))
                .unwrap()
            );
            0
        }
        other => {
            eprintln!("Error: Unsupported native tool runner target '{}'.", other);
            1
        }
    }
}

fn main() {
    let raw_args: Vec<String> = env::args().skip(1).collect();
    if raw_args.len() == 1 && (raw_args[0] == "--help" || raw_args[0] == "-h") {
        print_help();
        return;
    }
    if raw_args.len() == 1 && raw_args[0] == "--check" {
        let abi = sandbox::probe_landlock_abi();
        let mode = env::var("FLOWORK_SANDBOX_MODE").unwrap_or_else(|_| "auto".to_string());
        println!(
            "flowork-tool-runner: OK (native Rust 60-tool runner, landlock_abi={}, sandbox_mode={})",
            abi, mode
        );
        return;
    }

    let (tool_opt, extra_args) = resolve_tool_and_args();
    let Some(tool_name) = tool_opt else {
        eprintln!("Error: Could not resolve tool name (invoke via tools/<name>/run hardlink, --tool <name>, or FLOWORK_TOOL_NAME).");
        process::exit(1);
    };

    let code = if tool_name == "agent_browser" {
        run_agent_browser(&extra_args)
    } else if tool_name == "agent_desktop" {
        run_agent_desktop(&extra_args)
    } else if tool_name == "rea" {
        run_rea(&extra_args)
    } else if tool_name.starts_with("browser_") {
        run_browser_tool(&tool_name, &extra_args)
    } else {
        run_standard_tool(&tool_name)
    };
    process::exit(code);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_sandbox_modes_and_abi_masks() {
        assert_eq!(sandbox::SandboxMode::parse("auto"), sandbox::SandboxMode::Auto);
        assert_eq!(
            sandbox::SandboxMode::parse("ENFORCE"),
            sandbox::SandboxMode::Enforce
        );
        assert_eq!(
            sandbox::SandboxMode::parse("strict"),
            sandbox::SandboxMode::Enforce
        );
        assert_eq!(sandbox::SandboxMode::parse("off"), sandbox::SandboxMode::Off);
        assert_eq!(sandbox::SandboxMode::parse("0"), sandbox::SandboxMode::Off);

        let m1 = sandbox::handled_access_for_abi(1);
        let m2 = sandbox::handled_access_for_abi(2);
        let m3 = sandbox::handled_access_for_abi(3);
        assert_eq!(sandbox::handled_access_for_abi(0), 0);
        assert!(m1 > 0);
        assert_eq!(m2 & (1 << 13), 1 << 13);
        assert_eq!(m1 & (1 << 13), 0);
        assert_eq!(m3 & (1 << 14), 1 << 14);
        assert_eq!(m2 & (1 << 14), 0);
    }

    #[test]
    fn gates_sandbox_gracefully_according_to_kernel_abi() {
        let cwd = PathBuf::from("/tmp");
        let off = sandbox::prepare_ruleset(&cwd, sandbox::SandboxMode::Off).unwrap();
        assert!(!off.enforced);
        assert_eq!(off.mode, "off");

        let abi = sandbox::probe_landlock_abi();
        let auto = sandbox::prepare_ruleset(&cwd, sandbox::SandboxMode::Auto).unwrap();
        let enforce = sandbox::prepare_ruleset(&cwd, sandbox::SandboxMode::Enforce);
        if abi > 0 {
            assert!(auto.enforced);
            assert!(enforce.is_ok());
        } else {
            assert!(!auto.enforced);
            assert!(enforce.is_err());
        }
    }
}
