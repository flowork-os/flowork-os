use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();
    let target = env::var("FLOWORK_TARGET_FILE").unwrap_or_default().to_lowercase();

    // Check explicit active events
    if events.contains("glass_hud") || events.contains("terminal_theme") {
        exit(0);
    }

    // Check target file explicitly being modified
    if target.contains("alacritty.toml") || target.contains("mrflow-terminal") || target.contains("glass_hud") {
        exit(0);
    }

    // Check relevant keywords in active user message / prompt
    let keywords = [
        "glass", "opacity", "hud", "transparent", "transparency", "alacritty",
        "terminal theme", "transparan", "warna tulisan", "glassmorphism",
        "see-through", "contrast", "alacritty.toml", "mrflow-terminal",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    // By default: QUIESCENT (suppressed, zero token cost)
    exit(1);
}
