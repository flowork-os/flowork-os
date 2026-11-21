// =============================================================================
// ⏱️ FLOWORK OS — FLOWFS V2 TEMPORAL TIME-TRAVEL CHECKPOINT ENGINE
// Pure Rust | Content-Addressable Zstd Deltas per-turn | Atomic Rollback
// Milestone Sprint 2 Deliverable
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Read;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Instant, SystemTime, UNIX_EPOCH};

pub const CHECKPOINTS_ROOT: &str = "/opt/floworkos/history/checkpoints";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckpointFileEntry {
    pub path: String,
    pub sha256: String,
    pub size_bytes: u64,
    pub mode: u32,
    pub blob_name: String,
    pub action: String, // "checkpointed", "created", "deleted"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TurnManifest {
    pub session_id: String,
    pub turn: u32,
    pub timestamp_ms: u64,
    pub label: String,
    pub files: Vec<CheckpointFileEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RollbackReceipt {
    pub status: String,
    pub path: String,
    pub turn: u32,
    pub sha256: String,
    pub bytes_restored: u64,
    pub latency_ms: u64,
}

pub struct TemporalEngine;

impl TemporalEngine {
    /// Resolve checkpoints base root
    pub fn root_dir() -> PathBuf {
        let base = std::env::var("FLOWORK_CHECKPOINTS_DIR")
            .unwrap_or_else(|_| CHECKPOINTS_ROOT.to_string());
        PathBuf::from(base)
    }

    /// Resolve active session ID from environment or recent transcripts
    pub fn get_active_session_id() -> String {
        if let Ok(sid) = std::env::var("FLOWORK_SESSION_ID") {
            if !sid.trim().is_empty() {
                return sid.trim().to_string();
            }
        }

        // Try scanning latest transcript in /opt/floworkos/history/chats
        let chats_dir = Path::new("/opt/floworkos/history/chats");
        if let Ok(entries) = fs::read_dir(chats_dir) {
            let mut latest: Option<(SystemTime, String)> = None;
            for entry in entries.flatten() {
                let p = entry.path();
                if p.extension().and_then(|e| e.to_str()) == Some("jsonl") {
                    if let Ok(meta) = p.metadata() {
                        if let Ok(mtime) = meta.modified() {
                            let stem = p.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();
                            if latest.as_ref().map(|(t, _)| mtime > *t).unwrap_or(true) {
                                latest = Some((mtime, stem));
                            }
                        }
                    }
                }
            }
            if let Some((_, sid)) = latest {
                return sid;
            }
        }

        "sovereign_session".to_string()
    }

    /// Resolve session directory
    pub fn resolve_session_dir(session_id: &str) -> PathBuf {
        Self::root_dir().join(session_id)
    }

    /// Resolve turn directory
    pub fn resolve_turn_dir(session_id: &str, turn: u32) -> PathBuf {
        Self::resolve_session_dir(session_id).join(format!("turn_{}", turn))
    }

    /// Compute SHA-256 hash of a file
    pub fn hash_file(path: &Path) -> Result<String, String> {
        let mut file = File::open(path).map_err(|e| format!("Failed to open '{}': {}", path.display(), e))?;
        let mut hasher = Sha256::new();
        let mut buffer = [0u8; 16384];
        loop {
            let n = file.read(&mut buffer).map_err(|e| format!("Read error on '{}': {}", path.display(), e))?;
            if n == 0 {
                break;
            }
            hasher.update(&buffer[..n]);
        }
        Ok(format!("{:x}", hasher.finalize()))
    }

    /// Compress file into content-addressable zstd blob
    pub fn compress_blob(src: &Path, dst: &Path) -> Result<String, String> {
        let sha256 = Self::hash_file(src)?;
        let zstd_bin = if Path::new("/opt/floworkos/bin/zstd").exists() {
            "/opt/floworkos/bin/zstd"
        } else {
            "zstd"
        };

        let tmp_dst = dst.with_extension("tmp");
        let output = Command::new(zstd_bin)
            .arg("-q")
            .arg("-f")
            .arg("-o")
            .arg(&tmp_dst)
            .arg(src)
            .output()
            .map_err(|e| format!("Failed running zstd compression: {}", e))?;

        if !output.status.success() {
            return Err(format!("zstd failed: {}", String::from_utf8_lossy(&output.stderr)));
        }

        fs::rename(&tmp_dst, dst).map_err(|e| format!("Failed publishing blob: {}", e))?;
        Ok(sha256)
    }

    /// Decompress zstd blob back to target path atomically
    pub fn decompress_blob(blob: &Path, target: &Path) -> Result<(), String> {
        let zstd_bin = if Path::new("/opt/floworkos/bin/zstd").exists() {
            "/opt/floworkos/bin/zstd"
        } else {
            "zstd"
        };

        if let Some(parent) = target.parent() {
            let _ = fs::create_dir_all(parent);
        }

        let tmp_target = target.with_extension("rollback_tmp");
        let output = Command::new(zstd_bin)
            .arg("-d")
            .arg("-q")
            .arg("-f")
            .arg("-o")
            .arg(&tmp_target)
            .arg(blob)
            .output()
            .map_err(|e| format!("Failed running zstd decompression: {}", e))?;

        if !output.status.success() {
            return Err(format!("zstd decompression failed: {}", String::from_utf8_lossy(&output.stderr)));
        }

        fs::rename(&tmp_target, target).map_err(|e| format!("Failed restoring target file: {}", e))?;
        Ok(())
    }

    /// Create turn checkpoint for target files before or after tool actions
    pub fn create_checkpoint(
        session_id: &str,
        turn: u32,
        label: Option<&str>,
        target_files: &[PathBuf],
    ) -> Result<TurnManifest, String> {
        let turn_dir = Self::resolve_turn_dir(session_id, turn);
        fs::create_dir_all(&turn_dir).map_err(|e| format!("Failed creating turn dir '{}': {}", turn_dir.display(), e))?;

        let mut entries = Vec::new();

        for file_path in target_files {
            if !file_path.exists() {
                entries.push(CheckpointFileEntry {
                    path: file_path.to_string_lossy().to_string(),
                    sha256: "EMPTY_PRE_CREATE".to_string(),
                    size_bytes: 0,
                    mode: 0o644,
                    blob_name: "".to_string(),
                    action: "created".to_string(),
                });
                continue;
            }

            let meta = fs::metadata(file_path).map_err(|e| e.to_string())?;
            let mode = meta.permissions().mode();
            let size = meta.len();

            let sha = Self::hash_file(file_path)?;
            let blob_name = format!("blob_{}.zst", &sha[..16]);
            let blob_path = turn_dir.join(&blob_name);

            Self::compress_blob(file_path, &blob_path)?;

            entries.push(CheckpointFileEntry {
                path: file_path.to_string_lossy().to_string(),
                sha256: sha,
                size_bytes: size,
                mode,
                blob_name,
                action: "checkpointed".to_string(),
            });
        }

        let manifest = TurnManifest {
            session_id: session_id.to_string(),
            turn,
            timestamp_ms: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_millis() as u64)
                .unwrap_or(0),
            label: label.unwrap_or("Autonomous checkpoint").to_string(),
            files: entries,
        };

        let manifest_path = turn_dir.join("manifest.json");
        let manifest_bytes = serde_json::to_vec_pretty(&manifest).map_err(|e| e.to_string())?;
        fs::write(&manifest_path, manifest_bytes).map_err(|e| e.to_string())?;

        // Update session index.json
        Self::update_session_index(session_id, &manifest)?;

        Ok(manifest)
    }

    /// Update session index.json with new turn summary
    fn update_session_index(session_id: &str, manifest: &TurnManifest) -> Result<(), String> {
        let session_dir = Self::resolve_session_dir(session_id);
        let index_path = session_dir.join("index.json");

        let mut index_val: Value = if index_path.exists() {
            fs::read_to_string(&index_path)
                .ok()
                .and_then(|s| serde_json::from_str(&s).ok())
                .unwrap_or(json!({ "session_id": session_id, "turns": [] }))
        } else {
            json!({ "session_id": session_id, "turns": [] })
        };

        if let Some(turns_arr) = index_val.get_mut("turns").and_then(|t| t.as_array_mut()) {
            turns_arr.retain(|item| item.get("turn").and_then(|v| v.as_u64()) != Some(manifest.turn as u64));
            turns_arr.push(json!({
                "turn": manifest.turn,
                "timestamp_ms": manifest.timestamp_ms,
                "label": manifest.label,
                "file_count": manifest.files.len()
            }));
            turns_arr.sort_by_key(|item| item.get("turn").and_then(|v| v.as_u64()).unwrap_or(0));
        }

        let index_bytes = serde_json::to_vec_pretty(&index_val).map_err(|e| e.to_string())?;
        fs::write(&index_path, index_bytes).map_err(|e| e.to_string())?;
        Ok(())
    }

    /// Roll back single target file to state recorded in turn N
    pub fn rollback_single_file(
        session_id: &str,
        turn: u32,
        file_path: &Path,
    ) -> Result<RollbackReceipt, String> {
        let start = Instant::now();
        let turn_dir = Self::resolve_turn_dir(session_id, turn);
        let manifest_path = turn_dir.join("manifest.json");

        if !manifest_path.exists() {
            return Err(format!(
                "Checkpoint turn {} not found for session '{}' at '{}'",
                turn,
                session_id,
                manifest_path.display()
            ));
        }

        let raw = fs::read_to_string(&manifest_path).map_err(|e| e.to_string())?;
        let manifest: TurnManifest = serde_json::from_str(&raw).map_err(|e| e.to_string())?;

        let target_canonical = file_path.to_string_lossy().to_string();
        let entry = manifest.files.iter().find(|e| e.path == target_canonical || Path::new(&e.path) == file_path);

        let Some(file_entry) = entry else {
            let available: Vec<String> = manifest.files.iter().map(|f| f.path.clone()).collect();
            return Err(format!(
                "File '{}' not recorded in turn {} manifest. Captured files: {:?}",
                file_path.display(),
                turn,
                available
            ));
        };

        if file_entry.action == "created" {
            // The file did not exist before this turn, delete it to revert
            if file_path.exists() {
                let _ = fs::remove_file(file_path);
            }
            return Ok(RollbackReceipt {
                status: "ok".to_string(),
                path: target_canonical,
                turn,
                sha256: "REVERTED_PRE_CREATE".to_string(),
                bytes_restored: 0,
                latency_ms: start.elapsed().as_millis() as u64,
            });
        }

        let blob_path = turn_dir.join(&file_entry.blob_name);
        if !blob_path.exists() {
            return Err(format!("Blob '{}' missing in turn directory", blob_path.display()));
        }

        Self::decompress_blob(&blob_path, file_path)?;

        // Restore file permissions
        let _ = fs::set_permissions(file_path, fs::Permissions::from_mode(file_entry.mode));

        // Re-index file in FlowFS if applicable
        let db_path = crate::flowfs::resolve_db_path();
        let _ = crate::flowfs::index_single_file(&db_path, file_path);

        Ok(RollbackReceipt {
            status: "ok".to_string(),
            path: target_canonical,
            turn,
            sha256: file_entry.sha256.clone(),
            bytes_restored: file_entry.size_bytes,
            latency_ms: start.elapsed().as_millis() as u64,
        })
    }

    /// Roll back all files captured in turn N
    pub fn rollback_turn(session_id: &str, turn: u32) -> Result<Vec<RollbackReceipt>, String> {
        let turn_dir = Self::resolve_turn_dir(session_id, turn);
        let manifest_path = turn_dir.join("manifest.json");

        if !manifest_path.exists() {
            return Err(format!("Manifest not found for turn {} at '{}'", turn, manifest_path.display()));
        }

        let raw = fs::read_to_string(&manifest_path).map_err(|e| e.to_string())?;
        let manifest: TurnManifest = serde_json::from_str(&raw).map_err(|e| e.to_string())?;

        let mut receipts = Vec::new();
        for file_entry in &manifest.files {
            let path = PathBuf::from(&file_entry.path);
            let receipt = Self::rollback_single_file(session_id, turn, &path)?;
            receipts.push(receipt);
        }

        Ok(receipts)
    }

    /// List all captured checkpoints across sessions
    pub fn list_checkpoints(filter_session: Option<&str>) -> Result<Vec<Value>, String> {
        let root = Self::root_dir();
        if !root.exists() {
            return Ok(Vec::new());
        }

        let mut list = Vec::new();
        let entries = fs::read_dir(&root).map_err(|e| e.to_string())?;

        for entry in entries.flatten() {
            let session_path = entry.path();
            if !session_path.is_dir() {
                continue;
            }
            let sid = session_path.file_name().and_then(|n| n.to_str()).unwrap_or("").to_string();

            if let Some(ref filt) = filter_session {
                if !sid.contains(filt) {
                    continue;
                }
            }

            let index_path = session_path.join("index.json");
            if let Ok(content) = fs::read_to_string(&index_path) {
                if let Ok(v) = serde_json::from_str::<Value>(&content) {
                    list.push(v);
                    continue;
                }
            }

            // Fallback manually inspect turn folders
            let mut turns = Vec::new();
            if let Ok(turn_entries) = fs::read_dir(&session_path) {
                for te in turn_entries.flatten() {
                    let tp = te.path();
                    let tname = tp.file_name().and_then(|n| n.to_str()).unwrap_or("");
                    if tname.starts_with("turn_") {
                        let mpath = tp.join("manifest.json");
                        if let Ok(mraw) = fs::read_to_string(&mpath) {
                            if let Ok(mval) = serde_json::from_str::<Value>(&mraw) {
                                turns.push(mval);
                            }
                        }
                    }
                }
            }
            list.push(json!({ "session_id": sid, "turns": turns }));
        }

        Ok(list)
    }
}
