// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - MAIN DAEMON & TUI ENTRY
// Clean-room sovereign downloader under Apache-2.0

mod engine;
mod ipc;
mod models;
mod ui;

use engine::DownloadEngine;
use ipc::IpcServer;
use models::{DownloadStatus, StateManager};
use std::sync::atomic::AtomicBool;
use std::sync::Arc;
use std::time::Duration;
use ui::TuiApp;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let state = StateManager::init();

    // Start background IPC server for extensions & CLI
    let ipc = IpcServer::new(state.clone());
    tokio::spawn(async move {
        let _ = ipc.run().await;
    });

    // Start background download worker queue
    let queue_state = state.clone();
    tokio::spawn(async move {
        let engine = DownloadEngine::new(queue_state.clone());
        loop {
            let next_to_run = {
                let db = queue_state.db.lock().unwrap();
                db.items.iter().find(|i| i.status == DownloadStatus::Queued).map(|i| i.id)
            };

            if let Some(id) = next_to_run {
                let cancel_flag = Arc::new(AtomicBool::new(false));
                let _ = engine.execute_download(id, cancel_flag).await;
            } else {
                tokio::time::sleep(Duration::from_millis(500)).await;
            }
        }
    });

    // If --daemon, run headless in background
    if args.iter().any(|a| a == "--daemon" || a == "-d") {
        loop {
            tokio::time::sleep(Duration::from_secs(3600)).await;
        }
    }

    // Default: run interactive TUI
    let mut app = TuiApp::new(state);
    app.run().await?;

    Ok(())
}
