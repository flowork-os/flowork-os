use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("zero_trust") {
        exit(0);
    }

    let keywords = [
        "zero trust", "zero-trust", "pesimis", "pessimist", "pessimistic",
        "audit ulang", "re-audit", "subagent", "spawn agent", "rawan halusinasi",
        "hallucination", "detect_hardcode", "audit_security", "audit_portability",
        "selesai", "tuntas", "sudah beres", "claim done", "tugas selesai",
        "done", "finished", "complete", "siap kirim", "qc pass",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
