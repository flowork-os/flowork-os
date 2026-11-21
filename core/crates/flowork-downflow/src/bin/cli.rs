// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - CLI UTILITY
// Clean-room CLI interface under Apache-2.0

#[path = "../ipc.rs"]
mod ipc;
#[path = "../models.rs"]
mod models;

use ipc::{IpcClient, IpcRequest};
use models::DownloadItem;
use std::env;

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 || args[1] == "--help" || args[1] == "-h" || args[1] == "help" {
        print_help();
        return;
    }

    match args[1].as_str() {
        "add" | "--add" => {
            if args.len() < 3 {
                eprintln!("Error: URL required. Usage: downflow-cli add <url> [filename]");
                std::process::exit(1);
            }
            let url = args[2].clone();
            let file_name = args.get(3).cloned();
            match IpcClient::send_request(IpcRequest::Add {
                url,
                file_name,
                category: None,
                later: None,
            }).await {
                Ok(res) => {
                    if res.success {
                        println!("Download added successfully.");
                    } else {
                        eprintln!("Failed to add download: {:?}", res.message);
                    }
                }
                Err(e) => {
                    eprintln!("DownFlow error: {}", e);
                    std::process::exit(1);
                }
            }
        }
        "list" | "--list" | "ls" => {
            match IpcClient::send_request(IpcRequest::List {
                status: None,
                search: None,
                limit: None,
            }).await {
                Ok(res) => {
                    if let Some(data) = res.data {
                        if let Ok(items) = serde_json::from_value::<Vec<DownloadItem>>(data) {
                            println!("{:<5} {:<30} {:<12} {:<15} {:<10}", "ID", "FILE", "STATUS", "SIZE", "SPEED");
                            println!("{}", "-".repeat(78));
                            for it in items {
                                println!("{:<5} {:<30} {:<12} {:<15} {:<10}",
                                    it.id,
                                    truncate(&it.file_name, 28),
                                    it.status.to_string(),
                                    format!("{}/{}", format_size(it.downloaded), format_size(it.size)),
                                    if it.speed_bytes_per_sec > 0 { format!("{}/s", format_size(it.speed_bytes_per_sec)) } else { "-".to_string() }
                                );
                            }
                            return;
                        }
                    }
                    println!("No downloads found.");
                }
                Err(e) => {
                    eprintln!("DownFlow error: {}", e);
                    std::process::exit(1);
                }
            }
        }
        "pause" => {
            let ids: Vec<u64> = args[2..].iter().filter_map(|s| s.parse().ok()).collect();
            let _ = IpcClient::send_request(IpcRequest::Pause { ids }).await;
            println!("Pause command sent.");
        }
        "resume" => {
            let ids: Vec<u64> = args[2..].iter().filter_map(|s| s.parse().ok()).collect();
            let _ = IpcClient::send_request(IpcRequest::Resume { ids }).await;
            println!("Resume command sent.");
        }
        "remove" | "rm" => {
            let ids: Vec<u64> = args[2..].iter().filter_map(|s| s.parse().ok()).collect();
            let _ = IpcClient::send_request(IpcRequest::Remove { ids, delete_files: Some(false) }).await;
            println!("Remove command sent.");
        }
        _ => {
            print_help();
        }
    }
}

fn print_help() {
    println!("👑 Flowork DownFlow Sovereign CLI");
    println!("Usage: downflow-cli <command> [args]");
    println!("\nCommands:");
    println!("  add <url> [name]    Add a new download URL");
    println!("  list                List all active/recent downloads");
    println!("  pause <id...>       Pause specified download IDs");
    println!("  resume <id...>      Resume specified download IDs");
    println!("  remove <id...>      Remove specified download IDs");
    println!("  help, -h, --help    Show this help message");
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() > max {
        format!("{}...", &s[..max.saturating_sub(3)])
    } else {
        s.to_string()
    }
}

fn format_size(bytes: u64) -> String {
    const KB: u64 = 1024;
    const MB: u64 = KB * 1024;
    const GB: u64 = MB * 1024;

    if bytes >= GB {
        format!("{:.2} GB", bytes as f64 / GB as f64)
    } else if bytes >= MB {
        format!("{:.1} MB", bytes as f64 / MB as f64)
    } else if bytes >= KB {
        format!("{:.0} KB", bytes as f64 / KB as f64)
    } else {
        format!("{} B", bytes)
    }
}
