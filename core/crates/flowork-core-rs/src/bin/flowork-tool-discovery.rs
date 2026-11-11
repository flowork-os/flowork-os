use flowork_core_rs::lifecycle::{is_tool_active, load_state, sniff_context, LifecycleState, SniffedContext};
use flowork_core_rs::{inject_intercept_gate_fields, DEFAULT_TOOLS_DIR};
use serde_json::{json, Value};
use std::env;
use std::fs;
use std::path::PathBuf;

fn print_help() {
    println!("flowork-tool-discovery — Sovereign Dynamic Tool Discovery Engine");
    println!("Usage: flowork-tool-discovery [--check] [--test-sniffer] [--tools-dir <dir>] [--help]");
}

fn run_sniffer_self_test() -> i32 {
    let test_tool = json!({
        "name": "flowork_web_search",
        "activation": "conditional",
        "triggers": {
            "keywords": ["search", "google", "web", "internet"],
            "exclude_keywords": ["offline", "localhost", "127.0.0.1"],
            "behavior": {
                "domains": ["google.com", "bing.com"]
            }
        }
    });
    let st = LifecycleState::default();
    let ctx1 = SniffedContext {
        text: "please search documentation online".to_string(),
        domains: vec!["google.com".to_string()],
        extensions: vec![],
        files: vec![],
        cwd: "/tmp".to_string(),
    };
    let ctx2 = SniffedContext {
        text: "run search on localhost server".to_string(),
        domains: vec!["localhost".to_string()],
        extensions: vec![],
        files: vec![],
        cwd: "/tmp".to_string(),
    };
    let ctx3 = SniffedContext {
        text: "edit this python script".to_string(),
        domains: vec![],
        extensions: vec![".py".to_string()],
        files: vec![],
        cwd: "/tmp".to_string(),
    };

    let t1 = is_tool_active("flowork_web_search", &test_tool, &ctx1, Some(&st));
    let t2 = is_tool_active("flowork_web_search", &test_tool, &ctx2, Some(&st));
    let t3 = is_tool_active("flowork_web_search", &test_tool, &ctx3, Some(&st));

    println!(
        "Test 1 (search online): {}",
        if t1 { "ACTIVE (Expected)" } else { "INACTIVE" }
    );
    println!(
        "Test 2 (localhost with exclude): {}",
        if t2 { "ACTIVE" } else { "INACTIVE (Excluded - Expected)" }
    );
    println!(
        "Test 3 (unrelated python): {}",
        if t3 { "ACTIVE" } else { "INACTIVE (Expected)" }
    );

    if t1 && !t2 && !t3 {
        0
    } else {
        1
    }
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut tools_dir = env::var("FLOWORK_TOOLS_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(DEFAULT_TOOLS_DIR));

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--help" | "-h" => {
                print_help();
                return;
            }
            "--check" => {
                println!("flowork-tool-discovery: OK (native Rust)");
                return;
            }
            "--test-sniffer" => {
                std::process::exit(run_sniffer_self_test());
            }
            "--tools-dir" => {
                if let Some(next) = args.get(i + 1) {
                    tools_dir = PathBuf::from(next);
                    i += 1;
                }
            }
            other if !other.starts_with('-') => {
                tools_dir = PathBuf::from(other);
            }
            _ => {}
        }
        i += 1;
    }

    let cwd = env::current_dir().unwrap_or_else(|_| PathBuf::from("/tmp"));
    let context = sniff_context(&cwd, None);
    let state = load_state();
    let mut discovered = Vec::new();

    if let Ok(entries) = fs::read_dir(&tools_dir) {
        let mut dir_paths: Vec<PathBuf> = entries
            .flatten()
            .filter_map(|e| {
                let p = e.path();
                p.is_dir().then_some(p)
            })
            .collect();
        dir_paths.sort();

        for tool_dir in dir_paths {
            let manifest_path = tool_dir.join("manifest.json");
            if !manifest_path.is_file() {
                continue;
            }
            let Ok(raw) = fs::read_to_string(&manifest_path) else {
                continue;
            };
            let Ok(manifest) = serde_json::from_str::<Value>(&raw) else {
                continue;
            };
            let Some(name) = manifest.get("name").and_then(|v| v.as_str()) else {
                continue;
            };
            let Some(desc) = manifest.get("description").and_then(|v| v.as_str()) else {
                continue;
            };

            if !is_tool_active(name, &manifest, &context, Some(&state)) {
                continue;
            }

            let mut schema = manifest
                .get("parametersJsonSchema")
                .cloned()
                .unwrap_or_else(|| {
                    json!({
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                });
            inject_intercept_gate_fields(&mut schema);

            let activation = manifest
                .get("activation")
                .and_then(|v| v.as_str())
                .unwrap_or("always");

            discovered.push(json!({
                "name": name,
                "description": desc,
                "parametersJsonSchema": schema,
                "activation": activation
            }));
        }
    }

    println!(
        "{}",
        serde_json::to_string_pretty(&discovered).unwrap_or_else(|_| "[]".to_string())
    );
}
