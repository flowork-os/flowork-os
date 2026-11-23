use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::{HashMap, HashSet, VecDeque};
use std::fs;
use std::io::{Read as _, Seek, SeekFrom, Write as _};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;

const CRASH_DROPBOX_DIR: &str = "/tmp/flowork_crashes";
const TMP_SCAN_DIR: &str = "/tmp";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrashIncident {
    pub app: String,
    pub pid: Option<u32>,
    #[serde(rename = "type")]
    pub crash_type: String,
    pub file: Option<String>,
    pub line: Option<u32>,
    pub app_dir: Option<String>,
    pub detail: String,
    pub log_path: Option<String>,
    pub timestamp: u64,
    pub source: String,
}

#[derive(Default)]
struct WatcherState {
    log_offsets: HashMap<PathBuf, u64>,
    seen_hashes: HashSet<String>,
    recent: VecDeque<CrashIncident>,
}

static STATE: OnceLock<Mutex<WatcherState>> = OnceLock::new();

fn state_lock() -> &'static Mutex<WatcherState> {
    STATE.get_or_init(|| Mutex::new(WatcherState::default()))
}

fn unix_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn fnv1a_hex(s: &str) -> String {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in s.as_bytes() {
        h ^= *b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    format!("{:016x}", h)
}

pub fn get_recent_crashes(limit: usize) -> Vec<CrashIncident> {
    let guard = state_lock().lock().unwrap();
    guard.recent.iter().rev().take(limit).cloned().collect()
}

fn extract_app_and_dir(file_path: Option<&str>, log_path: &Path) -> (String, Option<String>) {
    if let Some(fp) = file_path {
        for marker in ["/opt/floworkos/apps/", "/tmp/flowork_mock_apps/"] {
            if let Some(idx) = fp.find(marker) {
                let rest = &fp[idx + marker.len()..];
                if let Some(app_seg) = rest.split('/').next() {
                    if !app_seg.is_empty() {
                        return (app_seg.to_string(), Some(format!("{}{}", marker, app_seg)));
                    }
                }
            }
        }
    }
    let stem = log_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .strip_prefix("flowork_launch_")
        .unwrap_or("unknown")
        .strip_suffix(".log")
        .unwrap_or("unknown");
    let default_dir = PathBuf::from("/opt/floworkos/apps").join(stem);
    let app_dir = if default_dir.is_dir() {
        Some(default_dir.to_string_lossy().to_string())
    } else {
        None
    };
    (stem.to_string(), app_dir)
}

fn parse_traceback_or_panic(chunk: &str, log_path: &Path) -> Option<CrashIncident> {
    let lines: Vec<&str> = chunk.lines().collect();
    if lines.is_empty() {
        return None;
    }

    // Detect Python traceback
    let has_tb = chunk.contains("Traceback (most recent call last):");
    let py_err_prefixes = [
        "SyntaxError:",
        "IndentationError:",
        "RuntimeError:",
        "NameError:",
        "TypeError:",
        "ValueError:",
        "AttributeError:",
        "ImportError:",
        "ModuleNotFoundError:",
        "KeyError:",
        "ZeroDivisionError:",
        "FileNotFoundError:",
        "OSError:",
    ];
    let has_rust_panic = chunk.contains("panicked at ");
    let has_segfault = chunk.contains("Segmentation fault") || chunk.contains("SIGSEGV");

    if !has_tb && !has_rust_panic && !has_segfault {
        // Also catch standalone Python syntax/runtime error trace lines
        if !lines
            .iter()
            .any(|l| py_err_prefixes.iter().any(|p| l.trim_start().starts_with(p)))
        {
            return None;
        }
    }

    let mut file_hit: Option<String> = None;
    let mut line_hit: Option<u32> = None;
    let mut err_line: Option<String> = None;

    for raw in &lines {
        let trimmed = raw.trim();
        if let Some(after_file) = trimmed.strip_prefix("File \"") {
            if let Some(end_q) = after_file.find('"') {
                let fpath = &after_file[..end_q];
                file_hit = Some(fpath.to_string());
                if let Some(line_part) = after_file[end_q..].split("line ").nth(1) {
                    let digits: String = line_part
                        .chars()
                        .take_while(|c| c.is_ascii_digit())
                        .collect();
                    if let Ok(num) = digits.parse::<u32>() {
                        line_hit = Some(num);
                    }
                }
            }
        }
        if has_rust_panic {
            if let Some(idx) = trimmed.find("panicked at ") {
                err_line = Some(trimmed[idx..].to_string());
            }
        }
        if py_err_prefixes
            .iter()
            .any(|p| trimmed.starts_with(p))
        {
            err_line = Some(trimmed.to_string());
        }
    }

    if err_line.is_none() {
        err_line = lines
            .iter()
            .rev()
            .find(|l| !l.trim().is_empty())
            .map(|l| l.trim().to_string());
    }

    let crash_type = if has_segfault {
        "SIGSEGV".to_string()
    } else if has_rust_panic {
        "RUST_PANIC".to_string()
    } else if let Some(ref e) = err_line {
        e.split(':')
            .next()
            .unwrap_or("RuntimeException")
            .trim()
            .to_string()
    } else {
        "RuntimeException".to_string()
    };

    let (app, inferred_dir) = extract_app_and_dir(file_hit.as_deref(), log_path);
    let app_dir = inferred_dir.or_else(|| {
        file_hit
            .as_deref()
            .and_then(|fp| Path::new(fp).parent().map(|p| p.to_string_lossy().to_string()))
    });

    let detail = err_line.unwrap_or_else(|| chunk.chars().take(240).collect());

    Some(CrashIncident {
        app,
        pid: None,
        crash_type,
        file: file_hit,
        line: line_hit,
        app_dir,
        detail: detail.chars().take(400).collect(),
        log_path: Some(log_path.to_string_lossy().to_string()),
        timestamp: unix_secs(),
        source: "crash_watcher.rs".to_string(),
    })
}

fn emit_incident(incident: CrashIncident) {
    let key = fnv1a_hex(&format!(
        "{}|{}|{}|{}",
        incident.app,
        incident.crash_type,
        incident.file.as_deref().unwrap_or(""),
        incident.detail
    ));

    {
        let mut guard = state_lock().lock().unwrap();
        if guard.seen_hashes.contains(&key) {
            return;
        }
        if guard.seen_hashes.len() >= 500 {
            guard.seen_hashes.clear();
        }
        guard.seen_hashes.insert(key.clone());
        if guard.recent.len() >= 50 {
            guard.recent.pop_front();
        }
        guard.recent.push_back(incident.clone());
    }

    // 1. Atomically write JSON to /tmp/flowork_crashes/<app>_<pid_or_ts>.json
    let _ = fs::create_dir_all(CRASH_DROPBOX_DIR);
    let safe_app: String = incident
        .app
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '-' || c == '_' {
                c
            } else {
                '_'
            }
        })
        .collect();
    let suffix = incident
        .pid
        .map(|p| p.to_string())
        .unwrap_or_else(|| format!("{}", incident.timestamp));
    let tmp_path = PathBuf::from(CRASH_DROPBOX_DIR).join(format!(".{}_{}_{}.tmp", safe_app, suffix, &key[..6]));
    let final_path = PathBuf::from(CRASH_DROPBOX_DIR).join(format!("{}_{}_{}.json", safe_app, suffix, &key[..6]));

    if let Ok(payload) = serde_json::to_vec_pretty(&incident) {
        if fs::write(&tmp_path, &payload).is_ok() {
            let _ = fs::rename(&tmp_path, &final_path);
        }
    }

    // 2. Publish system.crash.incident over Neural Bus UNIX socket
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let home_sock = PathBuf::from(home).join(".flowork/bus.sock");
    let bus_msg = json!({
        "type": "system.crash.incident",
        "source": "flowork-sysd:crash_watcher",
        "target": incident.app,
        "action": "crash_detected",
        "payload": incident
    });
    let wire = format!("{}\n", bus_msg);
    for sock_cand in [
        Path::new("/run/flowork/bus.sock"),
        Path::new("/tmp/flowork-neural-bus.sock"),
        home_sock.as_path(),
    ] {
        if sock_cand.exists() {
            if let Ok(mut stream) = UnixStream::connect(sock_cand) {
                let _ = stream.write_all(wire.as_bytes());
                break;
            }
        }
    }
}

fn seed_existing_logs() {
    let mut guard = state_lock().lock().unwrap();
    if let Ok(entries) = fs::read_dir(TMP_SCAN_DIR) {
        for entry in entries.flatten() {
            let p = entry.path();
            if let Some(name) = p.file_name().and_then(|s| s.to_str()) {
                if name.starts_with("flowork_launch_") && name.ends_with(".log") {
                    if let Ok(meta) = entry.metadata() {
                        guard.log_offsets.insert(p, meta.len());
                    }
                }
            }
        }
    }
}

fn poll_launch_logs() {
    let Ok(entries) = fs::read_dir(TMP_SCAN_DIR) else {
        return;
    };

    for entry in entries.flatten() {
        let p = entry.path();
        let Some(name) = p.file_name().and_then(|s| s.to_str()) else {
            continue;
        };
        if !name.starts_with("flowork_launch_") || !name.ends_with(".log") {
            continue;
        }
        let Ok(meta) = entry.metadata() else {
            continue;
        };
        let len = meta.len();

        let prev_offset = {
            let guard = state_lock().lock().unwrap();
            *guard.log_offsets.get(&p).unwrap_or(&0)
        };

        let start_offset = if len < prev_offset { 0 } else { prev_offset };
        if len == start_offset {
            continue;
        }

        if let Ok(mut file) = fs::File::open(&p) {
            if file.seek(SeekFrom::Start(start_offset)).is_ok() {
                let to_read = (len - start_offset).min(32 * 1024) as usize;
                let mut buf = vec![0u8; to_read];
                if let Ok(n) = file.read(&mut buf) {
                    let chunk = String::from_utf8_lossy(&buf[..n]).to_string();
                    {
                        let mut guard = state_lock().lock().unwrap();
                        guard.log_offsets.insert(p.clone(), start_offset + n as u64);
                    }
                    if let Some(inc) = parse_traceback_or_panic(&chunk, &p) {
                        emit_incident(inc);
                    }
                }
            }
        }
    }
}

async fn watch_coredump_journal() {
    loop {
        let child = Command::new("journalctl")
            .args(["-f", "-n", "0", "-o", "json", "-t", "systemd-coredump"])
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::null())
            .spawn();

        let Ok(mut proc_child) = child else {
            tokio::time::sleep(Duration::from_secs(10)).await;
            continue;
        };

        if let Some(stdout) = proc_child.stdout.take() {
            let mut reader = BufReader::new(stdout).lines();
            while let Ok(Some(line)) = reader.next_line().await {
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&line) {
                    let exe = val
                        .get("COREDUMP_EXE")
                        .and_then(|v| v.as_str())
                        .unwrap_or("");
                    let msg = val.get("MESSAGE").and_then(|v| v.as_str()).unwrap_or("");
                    if exe.contains("/opt/floworkos")
                        || exe.contains("flowork")
                        || msg.contains("/opt/floworkos")
                    {
                        let comm = val
                            .get("COREDUMP_COMM")
                            .and_then(|v| v.as_str())
                            .unwrap_or("flowork-bin");
                        let pid = val
                            .get("COREDUMP_PID")
                            .and_then(|v| v.as_str())
                            .and_then(|s| s.parse::<u32>().ok());
                        let sig = val
                            .get("COREDUMP_SIGNAL_NAME")
                            .and_then(|v| v.as_str())
                            .unwrap_or("SIGSEGV");
                        let (app, app_dir) = extract_app_and_dir(Some(exe), Path::new(exe));
                        let app_name = if app == "unknown" { comm.to_string() } else { app };
                        emit_incident(CrashIncident {
                            app: app_name,
                            pid,
                            crash_type: sig.to_string(),
                            file: (!exe.is_empty()).then(|| exe.to_string()),
                            line: None,
                            app_dir,
                            detail: msg.chars().take(360).collect(),
                            log_path: None,
                            timestamp: unix_secs(),
                            source: "crash_watcher.rs:coredump".to_string(),
                        });
                    }
                }
            }
        }

        let _ = proc_child.wait().await;
        tokio::time::sleep(Duration::from_secs(5)).await;
    }
}

pub async fn start_crash_watcher() {
    seed_existing_logs();
    println!("  [flowork-sysd] 🛡️  Crash Watcher started (journal coredump + /tmp/flowork_launch_*.log)");

    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_millis(500));
        loop {
            interval.tick().await;
            let _ = tokio::task::spawn_blocking(poll_launch_logs).await;
        }
    });

    tokio::spawn(watch_coredump_journal());
}
