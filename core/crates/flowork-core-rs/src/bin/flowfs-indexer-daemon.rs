// =============================================================================
// 👑 FLOWORK OS — PURE RUST FLOWFS BACKGROUND INDEXER DAEMON
// Zero Python/NumPy | Nice +19 & IOPRIO_CLASS_IDLE syscalls | CPU >70% auto-pause
// Optional DRM SHM keyframe OCR capture (dHash diff > 5% + Privacy Filter)
// =============================================================================

use clap::Parser;
use flowork_core_rs::flowfs::{
    index_drm_shm_frame, index_files, purge_expired_screen_memory, resolve_db_path,
    DEFAULT_RETENTION_DAYS, DRM_SHM_PIXEL_PATH,
};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, SystemTime};

const CHECK_INTERVAL_SECS: u64 = 300;
const DRM_POLL_SECS: u64 = 30;
const LOG_FILE: &str = "/tmp/flowfs-indexer.log";

#[derive(Parser, Debug)]
#[command(
    name = "flowfs-indexer-daemon",
    about = "FlowFS Pure Rust Background Semantic & Screen Memory Indexer Daemon"
)]
struct Cli {
    /// Run a single indexer pass and exit
    #[arg(long = "once")]
    once: bool,

    /// Check daemon status and PID
    #[arg(long = "status")]
    status: bool,

    /// Stop running daemon
    #[arg(long = "stop")]
    stop: bool,

    /// Override doc sync interval in seconds (default: 300)
    #[arg(long = "interval", default_value_t = CHECK_INTERVAL_SECS)]
    interval: u64,
}

fn pid_file_path() -> PathBuf {
    let uid = unsafe { libc::geteuid() };
    let run_dir = PathBuf::from(format!("/run/user/{}", uid));
    if run_dir.is_dir() {
        run_dir.join("flowfs-indexer.pid")
    } else {
        std::env::temp_dir().join(format!("flowfs-indexer-{}.pid", uid))
    }
}

fn log_line(msg: &str) {
    let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
    let line = format!("[{}] [FlowFS-Rust-Daemon] {}\n", ts, msg);
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(LOG_FILE) {
        let _ = f.write_all(line.as_bytes());
    }
    eprint!("{}", line);
}

fn read_proc_stat_sample() -> Option<(u64, u64)> {
    let content = fs::read_to_string("/proc/stat").ok()?;
    let first = content.lines().next()?;
    let mut vals = Vec::new();
    for tok in first.split_whitespace().skip(1).take(7) {
        vals.push(tok.parse::<u64>().ok()?);
    }
    if vals.len() < 5 {
        return None;
    }
    let idle = vals[3] + vals[4];
    let total: u64 = vals.iter().sum();
    Some((idle, total))
}

fn get_cpu_usage_percent() -> f64 {
    if let Some((idle1, total1)) = read_proc_stat_sample() {
        thread::sleep(Duration::from_millis(200));
        if let Some((idle2, total2)) = read_proc_stat_sample() {
            let diff_idle = idle2.saturating_sub(idle1) as f64;
            let diff_total = total2.saturating_sub(total1) as f64;
            if diff_total > 0.0 {
                let usage = 100.0 * (1.0 - (diff_idle / diff_total));
                return (usage * 10.0).round() / 10.0;
            }
        }
    }
    0.0
}

fn apply_idle_resource_governor() {
    unsafe {
        libc::setpriority(libc::PRIO_PROCESS, 0, 19);
        // IOPRIO_WHO_PROCESS = 1, pid = 0 (self), IOPRIO_CLASS_IDLE = 3 << 13
        let ioprio_idle: libc::c_long = 3 << 13;
        libc::syscall(libc::SYS_ioprio_set, 1 as libc::c_long, 0 as libc::c_long, ioprio_idle);
    }
}

fn run_doc_pass(db_path: &Path) -> bool {
    let cpu = get_cpu_usage_percent();
    if cpu > 70.0 {
        log_line(&format!(
            "CPU load elevated ({:.1}% > 70%). Pausing FlowFS indexing cycle.",
            cpu
        ));
        return false;
    }

    log_line(&format!(
        "System idle (CPU {:.1}% <= 70%). Starting incremental FlowFS sync pass...",
        cpu
    ));
    match index_files(db_path, None) {
        Ok(rep) => {
            log_line(&format!(
                "Sync completed in {:.2}ms: {} new, {} updated, {} unchanged, {} purged.",
                rep.elapsed_ms, rep.new, rep.updated, rep.unchanged, rep.purged
            ));
            let days = std::env::var("FLOWORK_SCREEN_RETENTION_DAYS")
                .ok()
                .and_then(|s| s.parse::<u64>().ok())
                .unwrap_or(DEFAULT_RETENTION_DAYS);
            if let Ok(pruned) = purge_expired_screen_memory(db_path, days) {
                if pruned > 0 {
                    log_line(&format!("Pruned {} expired screen memory captures.", pruned));
                }
            }
            true
        }
        Err(e) => {
            log_line(&format!("FlowFS sync pass failed: {}", e));
            false
        }
    }
}

fn maybe_index_drm_keyframe(db_path: &Path, last_seen_mtime: &mut Option<SystemTime>) {
    if std::env::var("FLOWORK_SCREEN_DAEMON").as_deref() == Ok("0") {
        return;
    }
    let pix = Path::new(DRM_SHM_PIXEL_PATH);
    let Ok(meta) = fs::metadata(pix) else {
        return;
    };
    let Ok(mtime) = meta.modified() else {
        return;
    };
    if last_seen_mtime.as_ref() == Some(&mtime) {
        return;
    }
    let cpu = get_cpu_usage_percent();
    if cpu > 50.0 {
        return;
    }
    *last_seen_mtime = Some(mtime);
    if let Ok(rep) = index_drm_shm_frame(db_path, false, true) {
        if rep.status == "indexed" {
            log_line(&format!(
                "DRM keyframe indexed (title='{}', ocr_chars={}, thumb='{}').",
                rep.window_title, rep.ocr_chars, rep.thumbnail_path
            ));
        }
    }
}

static STOP_FLAG: AtomicBool = AtomicBool::new(false);

extern "C" fn handle_sig(_sig: libc::c_int) {
    STOP_FLAG.store(true, Ordering::SeqCst);
}

fn main() {
    let cli = Cli::parse();
    let pid_file = pid_file_path();

    if cli.status {
        if let Ok(raw) = fs::read_to_string(&pid_file) {
            if let Ok(pid) = raw.trim().parse::<libc::pid_t>() {
                let alive = unsafe { libc::kill(pid, 0) } == 0;
                if alive {
                    println!("FlowFS Pure Rust Indexer Daemon is running (PID {}).", pid);
                    std::process::exit(0);
                }
                println!("FlowFS Indexer Daemon PID file exists but process is not running.");
                std::process::exit(1);
            }
        }
        println!("FlowFS Indexer Daemon is stopped.");
        std::process::exit(0);
    }

    if cli.stop {
        if let Ok(raw) = fs::read_to_string(&pid_file) {
            if let Ok(pid) = raw.trim().parse::<libc::pid_t>() {
                let rc = unsafe { libc::kill(pid, libc::SIGTERM) };
                let _ = fs::remove_file(&pid_file);
                if rc == 0 {
                    println!("FlowFS Indexer Daemon (PID {}) stopped.", pid);
                    std::process::exit(0);
                }
            }
        }
        println!("No running daemon found.");
        std::process::exit(0);
    }

    apply_idle_resource_governor();
    let db_path = resolve_db_path();

    if cli.once {
        let ok = run_doc_pass(&db_path);
        std::process::exit(if ok { 0 } else { 1 });
    }

    unsafe {
        libc::signal(libc::SIGINT, handle_sig as *const () as libc::sighandler_t);
        libc::signal(libc::SIGTERM, handle_sig as *const () as libc::sighandler_t);
    }

    let my_pid = unsafe { libc::getpid() };
    let _ = fs::write(&pid_file, format!("{}", my_pid));
    log_line(&format!(
        "FlowFS Pure Rust Indexer Daemon started (PID {}, interval={}s).",
        my_pid, cli.interval
    ));

    let running = Arc::new(&STOP_FLAG);
    run_doc_pass(&db_path);

    let interval = cli.interval.max(30);
    let mut elapsed_since_doc: u64 = 0;
    let mut last_drm_mtime: Option<SystemTime> = None;

    while !running.load(Ordering::SeqCst) {
        thread::sleep(Duration::from_secs(DRM_POLL_SECS));
        if running.load(Ordering::SeqCst) {
            break;
        }
        elapsed_since_doc += DRM_POLL_SECS;
        maybe_index_drm_keyframe(&db_path, &mut last_drm_mtime);
        if elapsed_since_doc >= interval {
            elapsed_since_doc = 0;
            run_doc_pass(&db_path);
        }
    }

    let _ = fs::remove_file(&pid_file);
    log_line("FlowFS Pure Rust Indexer Daemon terminated gracefully.");
}
