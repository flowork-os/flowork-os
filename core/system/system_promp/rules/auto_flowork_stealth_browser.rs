use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();
    let target = env::var("FLOWORK_TARGET_FILE").unwrap_or_default().to_lowercase();

    // Event matches
    if events.contains("flowork_stealth_browser") {
        exit(0);
    }

    // Target file matches
    if target.contains("flowork-stealth") {
        exit(0);
    }

    // Dynamic keyword triggers
    let keywords = [
        "stealth", "anti-detect", "antidetect", "fingerprint", "spoofing",
        "ixbrowser", "adspower", "dolphin", "canvas_spoof", "webgl_spoof",
        "audio_seed", "multi_account", "webrtc_leak"
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    // Quiescent: 0 token cost, inactive
    exit(1);
}
