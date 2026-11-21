// [FL_INDEX: keywords="subagent, mandate, supervisor, worker, trigger" | purpose="Detector for subagent worker mandate activation"]
use std::env;
use std::process::exit;

fn main() {
    let role = env::var("FLOWORK_AGENT_ROLE").unwrap_or_default().to_lowercase();
    let persona = env::var("FLOWORK_TARGET_PERSONA").unwrap_or_default().to_lowercase();
    let is_subagent = env::var("FLOWORK_IS_SUBAGENT").unwrap_or_default();

    if is_subagent == "1" || is_subagent == "true" || persona != "leader" && persona != "mr.flow" && !role.is_empty() {
        exit(0);
    }

    exit(1);
}
