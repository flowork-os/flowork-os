use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();
    let target = env::var("FLOWORK_TARGET_FILE").unwrap_or_default().to_lowercase();

    // Event matches
    if events.contains("mrflow_engine_config") {
        exit(0);
    }

    // Target file matches
    if target.contains("mrflow.env") || target.contains("mrflow") {
        exit(0);
    }

    // Dynamic keyword triggers
    let keywords = [
        "max_turns", "maxturns", "turn_limit", "breaker", "circuit_breaker",
        "loop_threshold", "mrflow.env", "binary", "binari", "subagent_max_turns"
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    // Quiescent: 0 token cost, inactive
    exit(1);
}
