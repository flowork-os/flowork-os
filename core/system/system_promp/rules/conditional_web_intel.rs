use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("web_intel") {
        exit(0);
    }

    let has_web_url = (msg.contains("http://") || msg.contains("https://") || msg.contains("www."))
        && !msg.contains("youtube.com")
        && !msg.contains("youtu.be")
        && !msg.contains("github.com")
        && !msg.contains("localhost")
        && !msg.contains("127.0.0.1");

    if has_web_url
        || msg.contains("scrape web")
        || msg.contains("web security audit")
        || msg.contains("web intelligence")
    {
        exit(0);
    }

    exit(1);
}
