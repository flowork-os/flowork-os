// [FL_INDEX: keywords="web, stack, package, discovery, cargo, npm" | purpose="Detector for web application stack discovery trigger"]
use std::env;
use std::path::Path;
use std::process::exit;

fn main() {
    let ws = env::var("FLOWORK_WORKSPACE").unwrap_or_else(|_| ".".to_string());
    let ws_path = Path::new(&ws);

    let markers = [
        "package.json", "Cargo.toml", "requirements.txt", "go.mod",
        "composer.json", "pom.xml", "build.gradle", "tsconfig.json"
    ];

    for marker in &markers {
        if ws_path.join(marker).exists() {
            exit(0);
        }
    }

    let msg = env::var("FLOWORK_USER_MSG").unwrap_or_default().to_lowercase();
    if msg.contains("stack") || msg.contains("dependencies") || msg.contains("package.json") || msg.contains("cargo.toml") {
        exit(0);
    }

    exit(1);
}
