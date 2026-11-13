// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - MULTI-CHUNK DOWNLOAD ENGINE
// Clean-room segmented downloader under Apache-2.0

use crate::models::{DownloadItem, DownloadStatus, StateManager};
use futures_util::StreamExt;
use reqwest::header::{ACCEPT_RANGES, CONTENT_LENGTH, RANGE};
use std::fs::{self, File, OpenOptions};
use std::io::{Seek, SeekFrom, Write};
use std::path::Path;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::mpsc;

pub struct DownloadEngine {
    state: StateManager,
    client: reqwest::Client,
}

impl DownloadEngine {
    pub fn new(state: StateManager) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .user_agent("Mozilla/5.0 (X11; Linux x86_64) FloworkOS/1.0 (DownFlow)")
            .build()
            .unwrap_or_default();

        Self { state, client }
    }

    pub async fn execute_download(&self, id: u64, cancel_flag: Arc<AtomicBool>) -> Result<(), String> {
        let item = self.state.get(id).ok_or_else(|| "Download not found".to_string())?;

        self.state.update_status(id, DownloadStatus::Downloading, None);

        // Ensure target directory exists
        if let Some(parent) = Path::new(&item.dest).parent() {
            let _ = fs::create_dir_all(parent);
        }

        // Head/Get request to probe server capabilities
        let head_resp = self.client.head(&item.url).send().await;
        let (content_length, supports_ranges) = match head_resp {
            Ok(resp) => {
                let len = resp.headers().get(CONTENT_LENGTH)
                    .and_then(|v| v.to_str().ok())
                    .and_then(|s| s.parse::<u64>().ok())
                    .unwrap_or(0);
                let ranges = resp.headers().get(ACCEPT_RANGES)
                    .and_then(|v| v.to_str().ok())
                    .map(|s| s.contains("bytes"))
                    .unwrap_or(false);
                (len, ranges)
            }
            Err(_) => (0, false),
        };

        // Update item size if discovered
        if content_length > 0 {
            let mut db = self.state.db.lock().unwrap();
            if let Some(it) = db.items.iter_mut().find(|i| i.id == id) {
                it.size = content_length;
                it.resumable = supports_ranges;
            }
            drop(db);
            let _ = self.state.save();
        }

        let temp_dest = format!("{}.fldown", item.dest);
        let mut file = OpenOptions::new()
            .create(true)
            .write(true)
            .read(true)
            .open(&temp_dest)
            .map_err(|e| format!("Failed to create file: {}", e))?;

        if content_length > 0 {
            let _ = file.set_len(content_length);
        }

        // If large file and supports ranges, perform 4-part segmented parallel download
        let num_parts = if supports_ranges && content_length > 4 * 1024 * 1024 {
            4
        } else {
            1
        };

        let chunk_size = if num_parts > 1 {
            content_length / num_parts
        } else {
            content_length
        };

        let downloaded_bytes = Arc::new(AtomicU64::new(0));
        let mut tasks = Vec::new();

        for i in 0..num_parts {
            let start = i * chunk_size;
            let end = if i == num_parts - 1 {
                content_length - 1
            } else {
                (i + 1) * chunk_size - 1
            };

            let client = self.client.clone();
            let url = item.url.clone();
            let dest_path = temp_dest.clone();
            let cancel = cancel_flag.clone();
            let dl_counter = downloaded_bytes.clone();

            tasks.push(tokio::spawn(async move {
                let mut req = client.get(&url);
                if supports_ranges && content_length > 0 {
                    req = req.header(RANGE, format!("bytes={}-{}", start, end));
                }

                let resp = req.send().await.map_err(|e| e.to_string())?;
                if !resp.status().is_success() {
                    return Err(format!("HTTP {}", resp.status()));
                }

                let mut stream = resp.bytes_stream();
                let mut current_pos = start;

                let mut part_file = OpenOptions::new()
                    .write(true)
                    .open(&dest_path)
                    .map_err(|e| e.to_string())?;
                part_file.seek(SeekFrom::Start(current_pos)).map_err(|e| e.to_string())?;

                while let Some(chunk_res) = stream.next().await {
                    if cancel.load(Ordering::Relaxed) {
                        return Err("Download paused".to_string());
                    }

                    let chunk = chunk_res.map_err(|e| e.to_string())?;
                    part_file.write_all(&chunk).map_err(|e| e.to_string())?;
                    let len = chunk.len() as u64;
                    current_pos += len;
                    dl_counter.fetch_add(len, Ordering::Relaxed);
                }

                Ok::<(), String>(())
            }));
        }

        // Monitor progress loop
        let monitor_counter = downloaded_bytes.clone();
        let monitor_state = self.state.clone();
        let monitor_cancel = cancel_flag.clone();
        let monitor_cancel_task = cancel_flag.clone();

        let monitor_task = tokio::spawn(async move {
            let mut last_dl = 0u64;
            let mut last_instant = Instant::now();

            while !monitor_cancel_task.load(Ordering::Relaxed) {
                tokio::time::sleep(Duration::from_millis(500)).await;
                let current_dl = monitor_counter.load(Ordering::Relaxed);
                let now = Instant::now();
                let elapsed = now.duration_since(last_instant).as_secs_f64();

                if elapsed > 0.0 {
                    let speed = ((current_dl.saturating_sub(last_dl)) as f64 / elapsed) as u64;
                    let mut db = monitor_state.db.lock().unwrap();
                    if let Some(it) = db.items.iter_mut().find(|i| i.id == id) {
                        it.downloaded = current_dl;
                        it.speed_bytes_per_sec = speed;
                    }
                    drop(db);
                    last_dl = current_dl;
                    last_instant = now;
                }
            }
        });

        // Wait for workers
        let mut overall_err = None;
        for t in tasks {
            match t.await {
                Ok(Ok(())) => {}
                Ok(Err(e)) => overall_err = Some(e),
                Err(e) => overall_err = Some(e.to_string()),
            }
        }

        monitor_cancel.store(true, Ordering::Relaxed);
        let _ = monitor_task.await;

        if let Some(err) = overall_err {
            if err.contains("paused") {
                self.state.update_status(id, DownloadStatus::Paused, None);
            } else {
                self.state.update_status(id, DownloadStatus::Error, Some(err.clone()));
            }
            return Err(err);
        }

        // Rename temp file to final destination
        let _ = fs::rename(&temp_dest, &item.dest);
        let final_size = fs::metadata(&item.dest).map(|m| m.len()).unwrap_or(content_length);

        let mut db = self.state.db.lock().unwrap();
        if let Some(it) = db.items.iter_mut().find(|i| i.id == id) {
            it.status = DownloadStatus::Complete;
            it.downloaded = final_size;
            if it.size == 0 {
                it.size = final_size;
            }
            it.speed_bytes_per_sec = 0;
            it.error = None;
        }
        drop(db);
        let _ = self.state.save();

        Ok(())
    }
}
