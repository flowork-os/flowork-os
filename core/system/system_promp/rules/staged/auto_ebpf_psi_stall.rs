use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();
    let target = env::var("FLOWORK_TARGET_FILE").unwrap_or_default().to_lowercase();

    // Event matches
    if events.contains("auto_ebpf_psi_stall") {
        exit(0);
    }

    // Target file matches
    if target.contains("auto_ebpf_psi_stall") {
        exit(0);
    }

    // Dynamic keyword triggers
    let keywords = ["psi_stall", "kernel_pressure", "memory_choke", "psi_alert"];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    // Quiescent: 0 token cost, inactive
    exit(1);
}
