// =============================================================================
// 🧠 FLOWORK OS — UNIFIED FLOWFS SEARCH & VISUAL MEMORY CLI (Pure Rust)
// Supports document semantic+BM25 search, OCR screen memory search & indexing,
// DRM SHM capture indexing, and live statistics (<25ms query latency).
// =============================================================================

use clap::Parser;
use flowork_core_rs::flowfs::{
    compute_stats, index_drm_shm_frame, index_files, index_screen_capture,
    purge_expired_screen_memory, recent_screen_memory, resolve_db_path, search_screen_memory,
    semantic_search, ScreenCaptureRequest, DEFAULT_RETENTION_DAYS,
};
use serde_json::json;
use std::time::Instant;

#[derive(Parser, Debug)]
#[command(
    name = "flowfs-search",
    about = "FlowFS — Sovereign Pure Rust Semantic File, Code & Visual Screen Memory Engine"
)]
struct Cli {
    /// Natural language or keyword search query
    query: Option<String>,

    /// Max results to return
    #[arg(short = 'l', long = "limit", default_value_t = 8)]
    limit: usize,

    /// Output results in JSON format
    #[arg(short = 'j', long = "json")]
    json: bool,

    /// Force incremental file indexing pass
    #[arg(short = 'i', long = "index")]
    index: bool,

    /// Display index statistics
    #[arg(short = 's', long = "stats")]
    stats: bool,

    /// Search visual screen memory captures
    #[arg(short = 'c', long = "screen")]
    screen: bool,

    /// List recent screen memory captures (use with --screen or standalone)
    #[arg(long = "recent")]
    recent: bool,

    /// Index a screenshot file (runs WebP 320px thumb + local OCR + FTS5/vector insert)
    #[arg(long = "index-screen")]
    index_screen: Option<String>,

    /// Index the latest zero-copy DRM SHM frame (/dev/shm/flowork_drm_latest.bgra)
    #[arg(long = "capture-drm")]
    capture_drm: bool,

    /// Optional active window title override for --index-screen
    #[arg(long = "title")]
    title: Option<String>,

    /// Optional active app class override for --index-screen
    #[arg(long = "app")]
    app: Option<String>,

    /// Optional explicit OCR/text override for --index-screen
    #[arg(long = "text")]
    text: Option<String>,

    /// Force indexing even if perceptual dHash delta <= 5%
    #[arg(long = "force")]
    force: bool,

    /// Disable Neural Bus event publish during screen indexing
    #[arg(long = "no-bus")]
    no_bus: bool,

    /// Purge screen memory captures older than retention days
    #[arg(long = "prune-screen")]
    prune_screen: bool,
}

fn format_size(bytes_val: u64) -> String {
    let units = ["B", "KB", "MB", "GB", "TB"];
    let mut val = bytes_val as f64;
    for u in units {
        if val < 1024.0 || u == "TB" {
            return format!("{:.1} {}", val, u);
        }
        val /= 1024.0;
    }
    format!("{} B", bytes_val)
}

fn main() {
    let cli = Cli::parse();
    let db_path = resolve_db_path();

    if cli.prune_screen {
        let days = std::env::var("FLOWORK_SCREEN_RETENTION_DAYS")
            .ok()
            .and_then(|s| s.parse::<u64>().ok())
            .unwrap_or(DEFAULT_RETENTION_DAYS);
        match purge_expired_screen_memory(&db_path, days) {
            Ok(purged) => {
                if cli.json {
                    println!("{}", json!({"status": "ok", "purged": purged, "retention_days": days}));
                } else {
                    println!("Purged {} expired screen memory entries (> {} days).", purged, days);
                }
            }
            Err(e) => {
                eprintln!("Error pruning screen memory: {}", e);
                std::process::exit(1);
            }
        }
        return;
    }

    if let Some(shot_path) = cli.index_screen.as_deref() {
        let req = ScreenCaptureRequest {
            screenshot_path: shot_path,
            window_title: cli.title.as_deref(),
            app_class: cli.app.as_deref(),
            explicit_text: cli.text.as_deref(),
            force: cli.force,
            skip_ocr: false,
            publish_bus: !cli.no_bus,
        };
        match index_screen_capture(&db_path, req) {
            Ok(rep) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&rep).unwrap_or_default());
                } else {
                    println!(
                        "FlowFS Screen [{}] title='{}' ocr_chars={} thumb='{}'",
                        rep.status, rep.window_title, rep.ocr_chars, rep.thumbnail_path
                    );
                }
            }
            Err(e) => {
                eprintln!("Error indexing screen capture: {}", e);
                std::process::exit(1);
            }
        }
        return;
    }

    if cli.capture_drm {
        match index_drm_shm_frame(&db_path, cli.force, !cli.no_bus) {
            Ok(rep) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&rep).unwrap_or_default());
                } else {
                    println!(
                        "FlowFS DRM Screen [{}] title='{}' ocr_chars={} thumb='{}'",
                        rep.status, rep.window_title, rep.ocr_chars, rep.thumbnail_path
                    );
                }
            }
            Err(e) => {
                eprintln!("Error indexing DRM SHM frame: {}", e);
                std::process::exit(1);
            }
        }
        return;
    }

    if cli.stats {
        match compute_stats(&db_path) {
            Ok(st) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&st).unwrap_or_default());
                    return;
                }
                println!("┌────────────────────────────────────────────────────────┐");
                println!("│ 🧠 FLOWFS PURE RUST INDEX STATISTICS                   │");
                println!("├────────────────────────────────────────────────────────┤");
                println!("│ Total Indexed Documents : {}", st.total_documents);
                println!("│ Documents FTS5 Rows     : {}", st.fts_documents_entries);
                println!("│ Screen Memory Entries   : {}", st.total_screen_entries);
                println!("│ Screen FTS5 Rows        : {}", st.fts_screen_entries);
                println!("│ Total Text Volume       : {}", format_size(st.total_text_bytes.max(0) as u64));
                println!("│ Database File Size      : {}", format_size(st.db_size_bytes));
                println!("│ Vector Database Path    : {}", st.db_path);
                println!("├────────────────────────────────────────────────────────┤");
                println!("│ Top File Extensions Indexed:                           │");
                for (ext, count) in st.top_extensions {
                    println!("│   {:<8} : {:>5} files", ext, count);
                }
                println!("└────────────────────────────────────────────────────────┘");
            }
            Err(e) => {
                eprintln!("Error computing stats: {}", e);
                std::process::exit(1);
            }
        }
        return;
    }

    if cli.index {
        if !cli.json {
            println!("🔍 FlowFS (Rust) — Starting incremental FTS5 + vector indexing...");
        }
        match index_files(&db_path, None) {
            Ok(rep) => {
                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&rep).unwrap_or_default());
                } else {
                    println!(
                        "✓ Indexing complete ({:.2}ms): {} new, {} updated, {} unchanged, {} purged.",
                        rep.elapsed_ms, rep.new, rep.updated, rep.unchanged, rep.purged
                    );
                }
            }
            Err(e) => {
                eprintln!("Indexing failed: {}", e);
                std::process::exit(1);
            }
        }
        return;
    }

    if cli.recent {
        let start = Instant::now();
        let results = recent_screen_memory(&db_path, cli.limit).unwrap_or_default();
        let elapsed_ms = ((start.elapsed().as_secs_f64() * 1000.0) * 100.0).round() / 100.0;
        if cli.json {
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "query": "*",
                    "mode": "screen_memory",
                    "elapsed_ms": elapsed_ms,
                    "results": results
                }))
                .unwrap_or_default()
            );
        } else {
            for (idx, res) in results.iter().enumerate() {
                println!("{}. [{}] {} -> {}", idx + 1, res.timestamp, res.window_title, res.screenshot_path);
            }
        }
        return;
    }

    let query = cli.query.as_deref().unwrap_or("").trim();
    if query.is_empty() {
        let _ = <Cli as clap::CommandFactory>::command().print_help();
        println!();
        return;
    }

    if cli.screen {
        let start = Instant::now();
        let results = match search_screen_memory(&db_path, query, cli.limit) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("Screen search failed: {}", e);
                std::process::exit(1);
            }
        };
        let elapsed_ms = ((start.elapsed().as_secs_f64() * 1000.0) * 100.0).round() / 100.0;

        if cli.json {
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "query": query,
                    "mode": "screen_memory",
                    "elapsed_ms": elapsed_ms,
                    "results": results
                }))
                .unwrap_or_default()
            );
            return;
        }

        if results.is_empty() {
            println!(
                "\n❌ No matching screen memory moments found for: '{}' ({} ms)",
                query, elapsed_ms
            );
            return;
        }

        println!("┌────────────────────────────────────────────────────────────────────────┐");
        println!(
            "│ 👁️  FLOWFS SCREEN MEMORY: \"{}\" ({} ms)",
            query.chars().take(35).collect::<String>(),
            elapsed_ms
        );
        println!("├────────────────────────────────────────────────────────────────────────┤");
        for (i, res) in results.iter().enumerate() {
            let pct = (res.similarity.min(1.0) * 100.0) as i32;
            println!("│ {}. [{}] {} (Match: {}%)", i + 1, res.timestamp, res.window_title, pct);
            println!("│    Screenshot: {}", res.screenshot_path);
            if !res.thumbnail_path.is_empty() {
                println!("│    Thumbnail : {}", res.thumbnail_path);
            }
            if !res.text.is_empty() {
                let preview: String = res.text.replace('\n', " ").chars().take(68).collect();
                println!("│    OCR Text  : \"{}...\"", preview);
            }
            println!("│");
        }
        println!("└────────────────────────────────────────────────────────────────────────┘");
        return;
    }

    let start = Instant::now();
    let results = match semantic_search(&db_path, query, cli.limit) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("Semantic search failed: {}", e);
            std::process::exit(1);
        }
    };
    let elapsed_ms = ((start.elapsed().as_secs_f64() * 1000.0) * 100.0).round() / 100.0;

    if cli.json {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "query": query,
                "elapsed_ms": elapsed_ms,
                "results": results
            }))
            .unwrap_or_default()
        );
        return;
    }

    if results.is_empty() {
        println!(
            "\n❌ No matching documents found for: '{}' ({} ms)",
            query, elapsed_ms
        );
        return;
    }

    println!("┌────────────────────────────────────────────────────────────────────────┐");
    println!(
        "│ 🧠 FLOWFS HYBRID SEARCH: \"{}\" ({} ms)",
        query.chars().take(35).collect::<String>(),
        elapsed_ms
    );
    println!("├────────────────────────────────────────────────────────────────────────┤");
    for (i, res) in results.iter().enumerate() {
        let pct = (res.score.min(1.0) * 100.0) as i32;
        println!("│ {}. {} (Match: {}%)", i + 1, res.filename, pct);
        println!("│    Path: {}", res.path);
        if !res.snippet.is_empty() {
            let preview: String = res.snippet.replace('\n', " ").chars().take(68).collect();
            println!("│    Excerpt: \"{}...\"", preview);
        }
        println!("│");
    }
    println!("└────────────────────────────────────────────────────────────────────────┘");
}
