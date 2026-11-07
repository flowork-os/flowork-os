use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("github") || events.contains("git_push") {
        exit(0);
    }

    let keywords = [
        "github", "clone repo", "repo remote", "pull request", "gh ", "pr ", "git clone",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
