// =============================================================================
// ⏱️ FLOWORK OS — FLOWFS V2 TEMPORAL TIME-TRAVEL ROLLBACK CLI
// Command-line driver for granular per-file atomic rollback & turn snapshots
// Sprint 2 Milestone Deliverable
// =============================================================================

use clap::Parser;
use flowork_core_rs::flowfs_temporal::TemporalEngine;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "flowfs-rollback")]
#[command(about = "FlowFS v2 Temporal Time-Travel & Granular File Rollback Engine (Sprint 2)")]
struct Cli {
    /// List available turn checkpoints
    #[arg(long, default_value_t = false)]
    list: bool,

    /// Target session ID (defaults to active session)
    #[arg(short, long)]
    session: Option<String>,

    /// Target turn number for rollback or checkpoint
    #[arg(short, long)]
    turn: Option<u32>,

    /// Target file path to roll back or checkpoint
    #[arg(short, long)]
    file: Option<PathBuf>,

    /// Revert all files modified in the specified turn
    #[arg(long)]
    revert_turn: Option<u32>,

    /// Take a new turn checkpoint for the specified file(s)
    #[arg(long, default_value_t = false)]
    checkpoint: bool,

    /// Descriptive checkpoint label (e.g. "Sebelum modifikasi kernel module")
    #[arg(long)]
    label: Option<String>,

    /// Output machine-readable JSON format
    #[arg(long, default_value_t = false)]
    json: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    let session_id = cli
        .session
        .unwrap_or_else(TemporalEngine::get_active_session_id);

    // 1. Handle Checkpoint Creation
    if cli.checkpoint {
        let turn = cli.turn.unwrap_or(1);
        let Some(file_path) = cli.file else {
            eprintln!("\x1b[1;31mError:\x1b[0m --file is required when creating a checkpoint.");
            std::process::exit(1);
        };

        let abs_path = if file_path.is_absolute() {
            file_path
        } else {
            std::env::current_dir()?.join(file_path)
        };

        match TemporalEngine::create_checkpoint(
            &session_id,
            turn,
            cli.label.as_deref(),
            std::slice::from_ref(&abs_path),
        ) {
            Ok(manifest) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&manifest)?);
                } else {
                    println!(
                        "\x1b[1;32m✓ Checkpoint locked:\x1b[0m Session '{}', Turn #{} [{} file(s)]",
                        session_id, turn, manifest.files.len()
                    );
                    for f in manifest.files {
                        println!("  → [{}] {} ({})", f.action, f.path, &f.sha256[..12]);
                    }
                }
                return Ok(());
            }
            Err(e) => {
                eprintln!("\x1b[1;31m✗ Checkpoint creation failed:\x1b[0m {}", e);
                std::process::exit(1);
            }
        }
    }

    // 2. Handle Revert Entire Turn
    if let Some(target_turn) = cli.revert_turn {
        match TemporalEngine::rollback_turn(&session_id, target_turn) {
            Ok(receipts) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&receipts)?);
                } else {
                    println!(
                        "\x1b[1;32m✓ Turn #{} successfully reverted across {} file(s):\x1b[0m",
                        target_turn,
                        receipts.len()
                    );
                    for r in receipts {
                        println!(
                            "  → Restored: '{}' [{} bytes in {}ms]",
                            r.path, r.bytes_restored, r.latency_ms
                        );
                    }
                }
                return Ok(());
            }
            Err(e) => {
                eprintln!("\x1b[1;31m✗ Turn rollback failed:\x1b[0m {}", e);
                std::process::exit(1);
            }
        }
    }

    // 3. Handle Rollback Single Target File
    if let (Some(target_turn), Some(file_path)) = (cli.turn, cli.file) {
        let abs_path = if file_path.is_absolute() {
            file_path
        } else {
            std::env::current_dir()?.join(file_path)
        };

        match TemporalEngine::rollback_single_file(&session_id, target_turn, &abs_path) {
            Ok(receipt) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&receipt)?);
                } else {
                    println!(
                        "\x1b[1;32m✓ Atomic file rollback succeeded:\x1b[0m\n  File: {}\n  Turn: #{}\n  Restored SHA-256: {}\n  Bytes: {} bytes\n  Latency: {}ms",
                        receipt.path, receipt.turn, receipt.sha256, receipt.bytes_restored, receipt.latency_ms
                    );
                }
                return Ok(());
            }
            Err(e) => {
                eprintln!("\x1b[1;31m✗ File rollback failed:\x1b[0m {}", e);
                std::process::exit(1);
            }
        }
    }

    // 4. Default: List Checkpoints
    let checkpoints = TemporalEngine::list_checkpoints(Some(&session_id))?;
    if cli.json {
        println!("{}", serde_json::to_string_pretty(&checkpoints)?);
        return Ok(());
    }

    println!("\x1b[1;36m┌────────────────────────────────────────────────────────────────────────┐\x1b[0m");
    println!(
        "\x1b[1;36m│ ⏱️  FLOWFS V2 TEMPORAL TIME-TRAVEL VAULT — Session: {:<18} │\x1b[0m",
        if session_id.len() > 18 { &session_id[..18] } else { &session_id }
    );
    println!("\x1b[1;36m├──────┬──────────────────────┬─────────┬────────────────────────────────┤\x1b[0m");
    println!("\x1b[1m│ TURN │ TIMESTAMP            │ FILES   │ LABEL                          │\x1b[0m");
    println!("\x1b[1;36m├──────┼──────────────────────┼─────────┼────────────────────────────────┤\x1b[0m");

    let mut count = 0;
    for sess in checkpoints {
        if let Some(turns) = sess.get("turns").and_then(|t| t.as_array()) {
            for t in turns {
                let turn_num = t.get("turn").and_then(|v| v.as_u64()).unwrap_or(0);
                let ts_ms = t.get("timestamp_ms").and_then(|v| v.as_u64()).unwrap_or(0);
                let label = t.get("label").and_then(|v| v.as_str()).unwrap_or("-");
                let files_cnt = t.get("file_count").and_then(|v| v.as_u64()).unwrap_or(0);

                let ts_str = if ts_ms > 0 {
                    chrono::DateTime::from_timestamp_millis(ts_ms as i64)
                        .map(|dt| dt.format("%Y-%m-%d %H:%M:%S").to_string())
                        .unwrap_or_else(|| "-".to_string())
                } else {
                    "-".to_string()
                };

                let label_trunc: String = if label.len() > 30 {
                    format!("{}...", &label[..27])
                } else {
                    label.to_string()
                };

                println!(
                    "│ #{:<3} │ {:<20} │ {:>5}   │ {:<30} │",
                    turn_num, ts_str, files_cnt, label_trunc
                );
                count += 1;
            }
        }
    }

    if count == 0 {
        println!("│ (No turn checkpoints recorded yet in this session)                     │");
    }
    println!("\x1b[1;36m└──────┴──────────────────────┴─────────┴────────────────────────────────┘\x1b[0m");
    println!("Total checkpoints: {}", count);

    Ok(())
}
