use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("portability") {
        exit(0);
    }

    let keywords = [
        "refactor", "nano modular", "baca file dan refactor", "cat <<", "type ",
        "copy ", "set-content", "out-file", "view_file", "write_to_file",
        "python", "rust", "golang", "typescript", "script", "skrip",
        "backend", "logic", "portable", "multi-os", "cross-platform",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
