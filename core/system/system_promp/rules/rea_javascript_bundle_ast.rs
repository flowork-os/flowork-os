use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("rea_javascript_bundle_ast") {
        exit(0);
    }

    let triggers = ["vendor.chunk.js", "bundle.js", "javascript bundle", "deminify modules"];
    for t in &triggers {
        if msg.contains(t) {
            exit(0);
        }
    }

    exit(1);
}
