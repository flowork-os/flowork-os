// [FL_INDEX: keywords="guardrail, external, untrusted, boundary, safety" | purpose="Detector for external input boundary guardrail"]
use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("webhook") || events.contains("external_input") || events.contains("untrusted") {
        exit(0);
    }

    let keywords = [
        "http://", "https://", "curl", "wget", "fetch",
        "external url", "untrusted", "payload", "webhook"
    ];

    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
