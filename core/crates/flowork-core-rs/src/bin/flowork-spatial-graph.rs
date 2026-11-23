// =============================================================================
// 🚀 Flowork Sovereign OS — Spatial UI Graph CLI (flowork-spatial-graph)
// Command-line driver for Unified AT-SPI + DRM Screen Graph & Fast Interaction
// Sprint 1 Milestone Deliverable
// =============================================================================

use clap::Parser;
use reqwest::Client;
use serde_json::{json, Value};
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(name = "flowork-spatial-graph")]
#[command(about = "Flowork Sovereign Spatial UI Graph Engine CLI (Sprint 1)")]
struct Cli {
    /// Target specific application by name or window title
    #[arg(short, long)]
    app: Option<String>,

    /// Include non-interactive widgets (containers, fillers, panels)
    #[arg(long, default_value_t = false)]
    all: bool,

    /// Force refresh DRM framebuffer capture in /dev/shm
    #[arg(long, default_value_t = false)]
    refresh_drm: bool,

    /// Output raw JSON format
    #[arg(long, default_value_t = false)]
    json: bool,

    /// Find widgets matching label, text, or query
    #[arg(long)]
    find: Option<String>,

    /// Filter widgets by role (button, text, entry, combo-box, tab)
    #[arg(long)]
    role: Option<String>,

    /// Click target widget by label, ref, or ID
    #[arg(long)]
    click: Option<String>,

    /// Target widget to type text into
    #[arg(long)]
    type_into: Option<String>,

    /// Text content to inject when using --type-into
    #[arg(long)]
    text: Option<String>,

    /// Force hardware synthetic input via uinput/XTest
    #[arg(long, default_value_t = false)]
    hardware: bool,

    /// Flowork sysd port (default 18090 or FLOWORK_SYSD_PORT)
    #[arg(long)]
    port: Option<u16>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    let port = cli.port.unwrap_or_else(|| {
        std::env::var("FLOWORK_SYSD_PORT")
            .ok()
            .and_then(|p| p.parse().ok())
            .unwrap_or(18090)
    });

    let client = Client::builder()
        .timeout(Duration::from_millis(15000))
        .build()?;

    let base_url = format!("http://127.0.0.1:{}", port);

    // 1. Handle Click Action
    if let Some(target) = cli.click {
        let req_body = json!({
            "action": "click",
            "label": target,
            "ref": target,
            "widget_id": target,
            "app": cli.app,
            "role": cli.role,
            "use_hardware_hid": cli.hardware
        });

        let res = client
            .post(format!("{}/api/agent/input/interact-widget", base_url))
            .json(&req_body)
            .send()
            .await?;

        let res_json: Value = res.json().await?;
        if cli.json {
            println!("{}", serde_json::to_string_pretty(&res_json)?);
        } else {
            if res_json.get("status").and_then(|s| s.as_str()) == Some("ok") {
                let tgt = res_json.get("target").cloned().unwrap_or(json!({}));
                let name = tgt.get("name").and_then(|v| v.as_str()).unwrap_or("");
                let role = tgt.get("role").and_then(|v| v.as_str()).unwrap_or("widget");
                let coords = tgt.get("center").cloned().unwrap_or(json!([]));
                let ms = res_json.get("latency_ms").and_then(|v| v.as_u64()).unwrap_or(0);
                println!(
                    "\x1b[1;32m✓ Click executed deterministically:\x1b[0m [{}] '{}' at center {} ({}ms)",
                    role, name, coords, ms
                );
            } else {
                let err = res_json.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
                eprintln!("\x1b[1;31m✗ Interaction failed:\x1b[0m {}", err);
                std::process::exit(1);
            }
        }
        return Ok(());
    }

    // 2. Handle Type Action
    if let Some(target) = cli.type_into {
        let text_to_type = cli.text.unwrap_or_default();
        let req_body = json!({
            "action": "type",
            "label": target,
            "ref": target,
            "widget_id": target,
            "text": text_to_type,
            "app": cli.app,
            "role": cli.role,
            "use_hardware_hid": cli.hardware
        });

        let res = client
            .post(format!("{}/api/agent/input/interact-widget", base_url))
            .json(&req_body)
            .send()
            .await?;

        let res_json: Value = res.json().await?;
        if cli.json {
            println!("{}", serde_json::to_string_pretty(&res_json)?);
        } else {
            if res_json.get("status").and_then(|s| s.as_str()) == Some("ok") {
                let tgt = res_json.get("target").cloned().unwrap_or(json!({}));
                let name = tgt.get("name").and_then(|v| v.as_str()).unwrap_or("");
                let ms = res_json.get("latency_ms").and_then(|v| v.as_u64()).unwrap_or(0);
                println!(
                    "\x1b[1;32m✓ Text injected:\x1b[0m target '{}' ({}ms)",
                    name, ms
                );
            } else {
                let err = res_json.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
                eprintln!("\x1b[1;31m✗ Type action failed:\x1b[0m {}", err);
                std::process::exit(1);
            }
        }
        return Ok(());
    }

    // 3. Query Spatial Scene Graph
    let query_body = json!({
        "app": cli.app,
        "interactive_only": !cli.all,
        "refresh_drm": cli.refresh_drm
    });

    let res = client
        .post(format!("{}/api/system/display/spatial-graph", base_url))
        .json(&query_body)
        .send()
        .await?;

    let res_json: Value = res.json().await?;

    if cli.json {
        println!("{}", serde_json::to_string_pretty(&res_json)?);
        return Ok(());
    }

    let graph = res_json.get("graph").cloned().unwrap_or(json!({}));
    let nodes = graph.get("nodes").and_then(|n| n.as_array()).cloned().unwrap_or_default();
    let total = graph.get("total_nodes").and_then(|t| t.as_u64()).unwrap_or(nodes.len() as u64);
    let latency_ms = graph.get("latency_ms").and_then(|l| l.as_u64()).unwrap_or(0);
    let disp_w = graph.get("display_width").and_then(|w| w.as_u64()).unwrap_or(0);
    let disp_h = graph.get("display_height").and_then(|h| h.as_u64()).unwrap_or(0);
    let active_app = graph.get("active_app").and_then(|a| a.as_str()).unwrap_or("none");

    println!("\x1b[1;36m┌────────────────────────────────────────────────────────────────────────┐\x1b[0m");
    println!(
        "\x1b[1;36m│ 🌐 FLOWORK SPATIAL UI GRAPH — Display: {}x{} | Active: {:<14} │\x1b[0m",
        disp_w, disp_h, active_app
    );
    println!(
        "\x1b[1;36m│ Nodes: {:<4} | Latency: {}ms | DRM Frame: Synced                   │\x1b[0m",
        total, latency_ms
    );
    println!("\x1b[1;36m├────────────┬─────────────────┬──────────────────────┬──────────┬───────┤\x1b[0m");
    println!("\x1b[1m│ ROLE       │ APP             │ LABEL / NAME         │ CENTER   │ REF   │\x1b[0m");
    println!("\x1b[1;36m├────────────┼─────────────────┼──────────────────────┼──────────┼───────┤\x1b[0m");

    let mut printed = 0;
    for node in nodes {
        let role = node.get("role").and_then(|r| r.as_str()).unwrap_or("");
        let app = node.get("app").and_then(|a| a.as_str()).unwrap_or("");
        let name = node.get("name").and_then(|n| n.as_str()).unwrap_or("");
        let cx = node.get("center_x").and_then(|x| x.as_i64()).unwrap_or(0);
        let cy = node.get("center_y").and_then(|y| y.as_i64()).unwrap_or(0);
        let ref_id = node.get("ref_id").and_then(|r| r.as_str()).unwrap_or("-");
        let is_occluded = node.get("is_occluded").and_then(|o| o.as_bool()).unwrap_or(false);

        // Filter if --find is specified
        if let Some(ref q) = cli.find {
            let q_lower = q.to_lowercase();
            if !name.to_lowercase().contains(&q_lower) && !role.to_lowercase().contains(&q_lower) {
                continue;
            }
        }

        // Filter if --role is specified
        if let Some(ref rf) = cli.role {
            if !role.to_lowercase().contains(&rf.to_lowercase()) {
                continue;
            }
        }

        let name_trunc: String = if name.len() > 20 {
            format!("{}...", &name[..17])
        } else {
            name.to_string()
        };

        let app_trunc: String = if app.len() > 15 {
            format!("{}...", &app[..12])
        } else {
            app.to_string()
        };

        let occ_marker = if is_occluded { "\x1b[33m(occ)\x1b[0m" } else { "" };

        println!(
            "│ {:<10} │ {:<15} │ {:<20} │ {:>4},{:<4} │ {:<5} │ {}",
            role, app_trunc, name_trunc, cx, cy, ref_id, occ_marker
        );
        printed += 1;
    }

    println!("\x1b[1;36m└────────────┴─────────────────┴──────────────────────┴──────────┴───────┘\x1b[0m");
    println!("Total matched widgets: {}", printed);

    Ok(())
}
