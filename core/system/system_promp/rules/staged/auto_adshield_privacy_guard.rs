use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();
    let target = env::var("FLOWORK_TARGET_FILE").unwrap_or_default().to_lowercase();

    // Event matches
    if events.contains("auto_adshield_privacy_guard") {
        exit(0);
    }

    // Target file matches
    if target.contains("auto_adshield_privacy_guard") {
        exit(0);
    }

    // Dynamic keyword triggers
    let keywords = ["adblock", "block_ads", "adshield", "privacy_protection", "stop_ads", "anti_telemetry", "hosts_blackhole", "ublock_managed"];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    // Quiescent: 0 token cost, inactive
    exit(1);
}
