// [FL_INDEX: keywords="scratch_janitor, log_pruning, storage_hygiene, zero_residue" | purpose="Automated rotation and quota enforcement for .FL_BIN/scratch/ logs in flowork-sysd"]

use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

const MAX_SCRATCH_BYTES: u64 = 50 * 1024 * 1024; // 50 MB
const TARGET_SCRATCH_BYTES: u64 = 25 * 1024 * 1024; // 25 MB
const MAX_AGE_SECONDS: u64 = 48 * 3600; // 48 Hours

/// Spawns the autonomous background janitor loop
pub async fn start_scratch_janitor() {
    tokio::spawn(async {
        // Initial delay to avoid slowing down startup
        tokio::time::sleep(Duration::from_secs(5)).await;
        loop {
            clean_all_scratchpads();
            tokio::time::sleep(Duration::from_secs(3600)).await; // Run hourly
        }
    });
}

/// Identifies candidate scratchpad directories and prunes stale logs
pub fn clean_all_scratchpads() {
    let mut candidate_roots = Vec::new();

    if let Ok(root) = std::env::var("FLOWORK_ROOT") {
        candidate_roots.push(PathBuf::from(root).join(".FL_BIN").join("scratch"));
    }
    candidate_roots.push(PathBuf::from("/opt/floworkos/.FL_BIN/scratch"));

    if let Ok(home) = std::env::var("HOME") {
        candidate_roots.push(PathBuf::from(home).join("floworkos/.FL_BIN/scratch"));
    }

    let mut visited = std::collections::HashSet::new();

    for scratch_dir in candidate_roots {
        if let Ok(canonical) = fs::canonicalize(&scratch_dir) {
            if visited.insert(canonical.clone()) && canonical.exists() {
                prune_scratch_dir(&canonical);
            }
        }
    }
}

struct LogEntry {
    path: PathBuf,
    size: u64,
    modified: SystemTime,
}

fn prune_scratch_dir(scratch_dir: &Path) {
    let logs_dir = scratch_dir.join("logs");
    let target_dirs = if logs_dir.exists() {
        vec![logs_dir, scratch_dir.to_path_buf()]
    } else {
        vec![scratch_dir.to_path_buf()]
    };

    let mut log_entries: Vec<LogEntry> = Vec::new();
    let mut total_bytes: u64 = 0;
    let now = SystemTime::now();

    for dir in target_dirs {
        let entries = match readdir_shallow(&dir) {
            Ok(e) => e,
            Err(_) => continue,
        };

        for path in entries {
            // Absolute Rule: Never touch .flowork or hidden configuration assets!
            let fname = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
            if fname.starts_with('.') || fname.contains(".flowork") {
                continue;
            }

            if let Ok(metadata) = fs::metadata(&path) {
                if !metadata.is_file() {
                    continue;
                }

                let size = metadata.len();
                let modified = metadata.modified().unwrap_or(now);

                // 1. Age-based Pruning (Remove files older than 48 hours)
                if let Ok(age) = now.duration_since(modified) {
                    if age.as_secs() > MAX_AGE_SECONDS {
                        let _ = fs::remove_file(&path);
                        continue;
                    }
                }

                total_bytes += size;
                log_entries.push(LogEntry {
                    path,
                    size,
                    modified,
                });
            }
        }
    }

    // 2. Quota-based Pruning (If total scratch logs > 50MB, prune down to 25MB)
    if total_bytes > MAX_SCRATCH_BYTES {
        // Sort by modified time ascending (oldest first)
        log_entries.sort_by_key(|a| a.modified);

        for entry in log_entries {
            if total_bytes <= TARGET_SCRATCH_BYTES {
                break;
            }
            if fs::remove_file(&entry.path).is_ok() {
                total_bytes = total_bytes.saturating_sub(entry.size);
            }
        }
    }
}


fn readdir_shallow(p: &Path) -> std::io::Result<Vec<PathBuf>> {
    let mut list = Vec::new();
    for e in fs::read_dir(p)?.flatten() {
        list.push(e.path());
    }
    Ok(list)
}
