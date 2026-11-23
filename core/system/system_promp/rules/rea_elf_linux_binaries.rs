use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let events = env::var("FLOWORK_ACTIVE_EVENTS").unwrap_or_default().to_lowercase();

    if events.contains("rea_elf_linux_binaries") {
        exit(0);
    }

    let triggers = [".elf", "readelf", "elf linux", "linux binary", "elf binary"];
    for t in &triggers {
        if msg.contains(t) {
            exit(0);
        }
    }

    exit(1);
}
