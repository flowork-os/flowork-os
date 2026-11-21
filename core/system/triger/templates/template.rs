// =============================================================================
// 🚀 Flowork Sovereign OS — Active Rust Trigger Daemon Template
// =============================================================================
use std::fs;
use std::path::Path;
use std::thread::sleep;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

fn get_now_secs() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

fn can_alert(state_file: &Path, cooldown_secs: u64) -> bool {
    if let Ok(content) = fs::read_to_string(state_file) {
        if let Ok(last_ts) = content.trim().parse::<u64>() {
            return (get_now_secs() - last_ts) >= cooldown_secs;
        }
    }
    true
}

fn mark_alerted(state_file: &Path) {
    let now = get_now_secs();
    let _ = fs::write(state_file, now.to_string());
}

fn dispatch_signal(trigger_id: &str, telemetry_json: &str, instruction: &str) {
    let signal_path = "/tmp/flowork_active_trigger.json";
    let now = get_now_secs();
    let payload = format!(
        r#"{{"active": true, "source": "{}", "timestamp": {}, "telemetry": {}, "instruction": "{}"}}"#,
        trigger_id, now, telemetry_json, instruction
    );
    let _ = fs::write(signal_path, payload);
    println!("[TRIGGER:{}] Alert dispatched to Flowork Agent", trigger_id);
}

fn main() {
    let pid = std::process::id();
    let dir = std::env::current_dir().unwrap();
    let pid_file = dir.join(".pid");
    let state_file = dir.join(".last_alert");

    let _ = fs::write(&pid_file, pid.to_string());
    println!("[ACTIVE_TRIGGER] Started PID {}", pid);

    let interval = Duration::from_secs(10);
    let cooldown_secs = 180;

    loop {
        // --- 1. Probe Telemetry ---
        let condition_breached = false; // Replace with actual probe logic

        // --- 2. Check Debounce & Dispatch ---
        if condition_breached && can_alert(&state_file, cooldown_secs) {
            mark_alerted(&state_file);
            dispatch_signal("custom_trigger", r#"{"metric": 95}"#, "Custom threshold breached.");
        }

        sleep(interval);
    }
}
