// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - DATA MODELS & STATE
// Clean-room implementation under Apache-2.0

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum DownloadStatus {
    Queued,
    Downloading,
    Paused,
    Complete,
    Error,
}

impl std::fmt::Display for DownloadStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DownloadStatus::Queued => write!(f, "Queued"),
            DownloadStatus::Downloading => write!(f, "Downloading"),
            DownloadStatus::Paused => write!(f, "Paused"),
            DownloadStatus::Complete => write!(f, "Complete"),
            DownloadStatus::Error => write!(f, "Error"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadItem {
    pub id: u64,
    pub url: String,
    pub file_name: String,
    pub dest: String,
    pub size: u64,
    pub downloaded: u64,
    pub status: DownloadStatus,
    pub category: String,
    pub description: String,
    pub speed_bytes_per_sec: u64,
    pub error: Option<String>,
    pub resumable: bool,
    pub added: String,
    pub last_try: String,
}

impl DownloadItem {
    pub fn new(id: u64, url: String, file_name: String, dest: String, category: String) -> Self {
        let now = chrono::Local::now().format("%b %d %H:%M:%S %Y").to_string();
        Self {
            id,
            url,
            file_name,
            dest,
            size: 0,
            downloaded: 0,
            status: DownloadStatus::Queued,
            category,
            description: String::new(),
            speed_bytes_per_sec: 0,
            error: None,
            resumable: true,
            added: now.clone(),
            last_try: now,
        }
    }

    pub fn progress_pct(&self) -> f64 {
        if self.size == 0 {
            0.0
        } else {
            (self.downloaded as f64 / self.size as f64) * 100.0
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadsDatabase {
    pub version: u32,
    pub next_id: u64,
    pub items: Vec<DownloadItem>,
}

impl Default for DownloadsDatabase {
    fn default() -> Self {
        Self {
            version: 3,
            next_id: 1,
            items: Vec::new(),
        }
    }
}

#[derive(Clone)]
pub struct StateManager {
    db_path: PathBuf,
    pub db: Arc<Mutex<DownloadsDatabase>>,
}

impl StateManager {
    pub fn init() -> Self {
        let db_path = Self::resolve_db_path();
        if let Some(parent) = db_path.parent() {
            let _ = fs::create_dir_all(parent);
        }

        let db = if db_path.exists() {
            match fs::read_to_string(&db_path) {
                Ok(content) => serde_json::from_str(&content).unwrap_or_default(),
                Err(_) => DownloadsDatabase::default(),
            }
        } else {
            DownloadsDatabase::default()
        };

        Self {
            db_path,
            db: Arc::new(Mutex::new(db)),
        }
    }

    fn resolve_db_path() -> PathBuf {
        if let Ok(home) = std::env::var("HOME") {
            let p1 = PathBuf::from(&home).join(".local/share/flowork/downflow/downloads.json");
            if p1.exists() {
                return p1;
            }
            let p2 = PathBuf::from(&home).join(".local/share/misterdownloadmanager/downloads.json");
            if p2.exists() {
                return p2;
            }
            return p1;
        }
        PathBuf::from("/tmp/flowork_downloads.json")
    }

    pub fn save(&self) -> Result<(), std::io::Error> {
        let db = self.db.lock().unwrap();
        let json = serde_json::to_string_pretty(&*db)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))?;
        fs::write(&self.db_path, json)
    }

    pub fn add(&self, url: String, custom_name: Option<String>, category: Option<String>) -> DownloadItem {
        let mut db = self.db.lock().unwrap();
        let id = db.next_id;
        db.next_id += 1;

        let filename = custom_name.unwrap_or_else(|| {
            url.split('/')
                .last()
                .and_then(|s| s.split('?').next())
                .filter(|s| !s.is_empty())
                .unwrap_or("download.bin")
                .to_string()
        });

        let cat = category.unwrap_or_else(|| "General".to_string());
        let default_dir = dirs_downloads().join(&cat);
        let dest = default_dir.join(&filename).to_string_lossy().to_string();

        let item = DownloadItem::new(id, url, filename, dest, cat);
        db.items.push(item.clone());
        drop(db);

        let _ = self.save();
        item
    }

    pub fn list(&self) -> Vec<DownloadItem> {
        self.db.lock().unwrap().items.clone()
    }

    pub fn get(&self, id: u64) -> Option<DownloadItem> {
        self.db.lock().unwrap().items.iter().find(|i| i.id == id).cloned()
    }

    pub fn update_status(&self, id: u64, status: DownloadStatus, err: Option<String>) {
        let mut db = self.db.lock().unwrap();
        if let Some(item) = db.items.iter_mut().find(|i| i.id == id) {
            item.status = status;
            item.error = err;
            item.last_try = chrono::Local::now().format("%b %d %H:%M:%S %Y").to_string();
        }
        drop(db);
        let _ = self.save();
    }

    pub fn remove(&self, id: u64, delete_file: bool) -> bool {
        let mut db = self.db.lock().unwrap();
        if let Some(pos) = db.items.iter().position(|i| i.id == id) {
            let item = db.items.remove(pos);
            drop(db);
            if delete_file {
                let _ = fs::remove_file(&item.dest);
            }
            let _ = self.save();
            true
        } else {
            false
        }
    }
}

pub fn dirs_downloads() -> PathBuf {
    if let Ok(home) = std::env::var("HOME") {
        PathBuf::from(home).join("Downloads")
    } else {
        PathBuf::from("/tmp")
    }
}
