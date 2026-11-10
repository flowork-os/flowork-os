// [FL_INDEX: keywords="git, contribution, commit, author, co-authored" | purpose="Detector for mandatory git contribution attribution trigger"]
use std::env;
use std::process::exit;

fn main() {
    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    let keywords = [
        "git", "commit", "push", "pr", "pull request",
        "repository", "repo", "github", "gitlab"
    ];

    for kw in &keywords {
        if msg.contains(kw) {
            exit(0);
        }
    }

    exit(1);
}
