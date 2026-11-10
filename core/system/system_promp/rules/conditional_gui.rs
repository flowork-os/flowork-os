use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("gui") {
        exit(0);
    }

    let keywords = [
        ".html", ".css", ".scss", ".vue", ".jsx", ".tsx", ".svelte", ".svg",
        "styling", "glassmorphism", "fl_dashboard.css", "frontend", "ui", "gui",
        "dashboard", "interface", "antarmuka", "tampilan", "landing page",
        "tailwind", "navbar", "modal", "component", "komponen",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
