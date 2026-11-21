use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("youtube") {
        exit(0);
    }

    let keywords = [
        "youtube.com", "youtu.be", "youtube video", "transkrip youtube",
        "youtube channel", "youtube", "yt ", "spy youtube", "video summary",
        "upload youtube", "upload video", "youtube studio", "publish video", "post video",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
