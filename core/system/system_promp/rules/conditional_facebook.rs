// [FL_INDEX: keywords="facebook, trigger, rule, rust, detector" | purpose="Native detector rule for ambient Facebook sensory trigger"]
use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("facebook") || events.contains("fb.com") {
        exit(0);
    }

    let keywords = [
        "facebook.com", "fb.com", "fb.watch", "facebook", "fb status",
        "update status facebook", "posting facebook", "post facebook",
        "fb ", "facebook feed", "facebook post",
    ];
    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
