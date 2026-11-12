// =============================================================================
// 👁️ FLOWORK OS — UNIFIED FLOWFS PURE RUST ENGINE (Document + Visual OCR Screen Memory)
// Zero Python/NumPy dependency | SQLite WAL + FTS5 BM25 + Sub-word Vector Hybrid
// Local Tesseract/Leptonica OCR (dlopen) + WebP Thumbnailer + DRM SHM Zero-Copy
//
// Universal root: /opt/floworkos
// =============================================================================

use ignore::WalkBuilder;
use rusqlite::{params, Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::ffi::{CStr, CString};
use std::fs;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::os::raw::{c_char, c_float, c_int, c_uchar, c_void};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::sync::{mpsc, OnceLock};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use crate::{resolve_home_dir, FLOWORK_ROOT};

pub const VECTOR_DIM: usize = 128;
pub const DRM_SHM_PIXEL_PATH: &str = "/dev/shm/flowork_drm_latest.bgra";
pub const DRM_SHM_META_PATH: &str = "/dev/shm/flowork_drm_latest.json";
pub const DEFAULT_OCR_TIMEOUT_MS: u64 = 1500;
pub const DEFAULT_RETENTION_DAYS: u64 = 30;
pub const MAX_INDEXABLE_FILE_BYTES: u64 = 5 * 1024 * 1024;
pub const DHASH_UNCHANGED_MAX_HAMMING: u32 = 3; // 3 / 64 bits ~= 4.7% diff (< 5% gate)

const INDEXABLE_EXTENSIONS: &[&str] = &[
    "md", "txt", "py", "json", "toml", "yaml", "yml", "conf", "rs", "js", "html", "css", "sh",
    "c", "h",
];

const IGNORE_DIRS: &[&str] = &[
    ".git",
    "node_modules",
    "target",
    "__pycache__",
    ".cache",
    ".rustup",
    ".npm",
    ".gemini",
    "proc",
    "sys",
    "dev",
    "venv",
    ".venv",
    "site-packages",
    "dist-packages",
    "user_data_chrome",
    "user_data",
];

const PRIVACY_EXCLUSION_PATTERNS: &[&str] = &[
    "keepass",
    "bitwarden",
    "1password",
    "lastpass",
    "proton pass",
    "seahorse",
    "incognito",
    "inprivate",
    "private browsing",
    "tor browser",
    "internet banking",
    "mbanking",
    "password manager",
    "vault.json",
    ".env",
    "id_rsa",
    "id_ed25519",
    "flowork.dev",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentSearchResult {
    pub id: i64,
    pub path: String,
    pub filename: String,
    pub extension: String,
    pub size: i64,
    pub title: String,
    pub snippet: String,
    pub score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenSearchResult {
    pub id: i64,
    pub timestamp: String,
    pub window_title: String,
    pub app_class: String,
    pub screenshot_path: String,
    pub thumbnail_path: String,
    pub text: String,
    pub similarity: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexFilesReport {
    pub new: usize,
    pub updated: usize,
    pub unchanged: usize,
    pub purged: usize,
    pub elapsed_ms: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexScreenReport {
    pub status: String,
    pub id: Option<i64>,
    pub timestamp: String,
    pub screenshot_path: String,
    pub thumbnail_path: String,
    pub window_title: String,
    pub app_class: String,
    pub frame_hash: String,
    pub ocr_chars: usize,
    pub extracted_text: String,
    pub reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowfsStats {
    pub db_path: String,
    pub db_size_bytes: u64,
    pub total_documents: i64,
    pub total_text_bytes: i64,
    pub total_screen_entries: i64,
    pub fts_documents_entries: i64,
    pub fts_screen_entries: i64,
    pub top_extensions: Vec<(String, i64)>,
}

#[derive(Debug, Clone, Default)]
pub struct ScreenCaptureRequest<'a> {
    pub screenshot_path: &'a str,
    pub window_title: Option<&'a str>,
    pub app_class: Option<&'a str>,
    pub explicit_text: Option<&'a str>,
    pub force: bool,
    pub skip_ocr: bool,
    pub publish_bus: bool,
}

#[derive(Debug, Clone, Default)]
pub struct ActiveWindowMeta {
    pub window_title: String,
    pub app_class: String,
}

// -----------------------------------------------------------------------------
// Path Resolution
// -----------------------------------------------------------------------------

pub fn resolve_db_path() -> PathBuf {
    if let Ok(explicit) = std::env::var("FLOWORK_FLOWFS_DB") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    resolve_home_dir()
        .join(".local")
        .join("share")
        .join("flowork")
        .join("flowfs.vec.db")
}

pub fn resolve_thumbs_dir() -> PathBuf {
    if let Ok(explicit) = std::env::var("FLOWORK_THUMBS_DIR") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    let sys_thumbs = PathBuf::from(FLOWORK_ROOT).join("screenshots").join("thumbs");
    if fs::create_dir_all(&sys_thumbs).is_ok() {
        let probe = sys_thumbs.join(".flowfs_write_probe");
        if fs::write(&probe, b"").is_ok() {
            let _ = fs::remove_file(&probe);
            return sys_thumbs;
        }
    }
    let fallback = resolve_home_dir()
        .join(".local")
        .join("share")
        .join("flowork")
        .join("thumbs");
    let _ = fs::create_dir_all(&fallback);
    fallback
}

pub fn resolve_tessdata_dir() -> Option<PathBuf> {
    if let Ok(explicit) = std::env::var("FLOWORK_TESSDATA_DIR") {
        let p = PathBuf::from(explicit.trim());
        if p.join("eng.traineddata").is_file() {
            return Some(p);
        }
    }
    let candidates = [
        PathBuf::from(FLOWORK_ROOT).join("system").join("tessdata"),
        PathBuf::from("/usr/share/tesseract-ocr/5/tessdata"),
        PathBuf::from("/usr/share/tesseract-ocr/4.00/tessdata"),
        PathBuf::from("/usr/share/tesseract-ocr/tessdata"),
    ];
    candidates
        .into_iter()
        .find(|p| p.join("eng.traineddata").is_file())
}

pub fn default_search_roots() -> Vec<PathBuf> {
    let home = resolve_home_dir();
    vec![
        PathBuf::from(FLOWORK_ROOT),
        home.join("Documents"),
        home.join("Desktop"),
        home.join("Downloads"),
        home.join("flowork-os-repo"),
    ]
}

// -----------------------------------------------------------------------------
// Privacy Exclusion & Scrubbing
// -----------------------------------------------------------------------------

pub fn should_exclude_screen_capture(
    window_title: &str,
    app_class: &str,
    screenshot_path: &str,
) -> Option<&'static str> {
    let title_l = window_title.to_ascii_lowercase();
    let class_l = app_class.to_ascii_lowercase();
    let path_l = screenshot_path.to_ascii_lowercase();

    for pat in PRIVACY_EXCLUSION_PATTERNS {
        if *pat == ".env" {
            // Avoid matching ".env" inside unrelated substrings cleanly
            let has_env = title_l.split_whitespace().any(|tok| {
                tok == ".env"
                    || tok.ends_with("/.env")
                    || tok.ends_with("\\.env")
                    || tok.contains(".env.")
            }) || path_l.ends_with("/.env");
            if has_env {
                return Some(".env");
            }
            continue;
        }
        if title_l.contains(pat) || class_l.contains(pat) || path_l.contains(pat) {
            return Some(*pat);
        }
    }

    if class_l.contains("flowork-stealth")
        && (title_l.contains("private") || title_l.contains("incognito") || title_l.contains("login"))
    {
        return Some("flowork-stealth-private");
    }

    None
}

pub fn scrub_ocr_text(raw: &str) -> String {
    let mut out = Vec::new();
    for token in raw.split_whitespace() {
        let lower = token.to_ascii_lowercase();
        if (token.starts_with("AIza") && token.len() >= 20)
            || (token.starts_with("sk-") && token.len() >= 18)
        {
            out.push("[REDACTED_API_KEY]".to_string());
        } else if (token.starts_with("ghp_")
            || token.starts_with("gho_")
            || token.starts_with("github_pat_"))
            && token.len() >= 18
        {
            out.push("[REDACTED_GH_TOKEN]".to_string());
        } else if lower.starts_with("ya29.") && token.len() >= 20 {
            out.push("[REDACTED_OAUTH_TOKEN]".to_string());
        } else if lower.starts_with("password=") || lower.starts_with("passwd=") {
            out.push("password=[REDACTED]".to_string());
        } else {
            out.push(token.to_string());
        }
    }
    let joined = out.join(" ");
    joined.chars().take(12_000).collect()
}

// -----------------------------------------------------------------------------
// Sub-word N-Gram + Hash Vector Embeddings (NumPy-free, f32 LE compatible)
// -----------------------------------------------------------------------------

#[inline]
fn fnv1a_64(bytes: &[u8]) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for &b in bytes {
        hash ^= b as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

pub fn tokenize_words(text: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut cur = String::new();
    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            cur.push(ch.to_ascii_lowercase());
        } else if !cur.is_empty() {
            tokens.push(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        tokens.push(cur);
    }
    tokens
}

pub fn text_to_vector(text: &str) -> [f32; VECTOR_DIM] {
    let words = tokenize_words(text);
    let mut vec = [0.0f32; VECTOR_DIM];
    if words.is_empty() {
        vec[0] = 1.0;
        return vec;
    }

    for w in &words {
        // Whole word feature
        let h = fnv1a_64(w.as_bytes());
        let idx = (h as usize) % VECTOR_DIM;
        let sign = if ((h >> 8) & 1) == 1 { 1.0f32 } else { -1.0f32 };
        let weight = ((1.0 + w.len() as f64).ln()) as f32;
        vec[idx] += sign * weight;

        // Compound split on '_' for camel/snake identifier recall
        if w.contains('_') {
            for part in w.split('_').filter(|p| p.len() >= 2) {
                let ph = fnv1a_64(part.as_bytes());
                let pidx = (ph as usize) % VECTOR_DIM;
                let psign = if ((ph >> 9) & 1) == 1 { 1.0f32 } else { -1.0f32 };
                vec[pidx] += psign * (((1.0 + part.len() as f64).ln()) as f32 * 0.75);
            }
        }

        // Sub-word character trigrams (3-grams) for robust fuzzy/OCR typo matching
        let b = w.as_bytes();
        if b.len() >= 3 {
            for win in b.windows(3) {
                let th = fnv1a_64(win);
                let tidx = (th as usize) % VECTOR_DIM;
                let tsign = if ((th >> 11) & 1) == 1 { 1.0f32 } else { -1.0f32 };
                vec[tidx] += tsign * 0.42;
            }
        }
    }

    let norm_sq: f32 = vec.iter().map(|v| v * v).sum();
    let norm = norm_sq.sqrt();
    if norm > 1e-6 {
        for v in &mut vec {
            *v /= norm;
        }
    }
    vec
}

pub fn vec_to_blob(vec: &[f32; VECTOR_DIM]) -> Vec<u8> {
    let mut out = Vec::with_capacity(VECTOR_DIM * 4);
    for v in vec {
        out.extend_from_slice(&v.to_le_bytes());
    }
    out
}

pub fn blob_cosine_similarity(q: &[f32; VECTOR_DIM], blob: &[u8]) -> f64 {
    if blob.len() < VECTOR_DIM * 4 {
        return 0.0;
    }
    let mut dot = 0.0f64;
    let mut norm_b_sq = 0.0f64;
    for (i, chunk) in blob.as_chunks::<4>().0.iter().take(VECTOR_DIM).enumerate() {
        let val = f32::from_le_bytes(*chunk) as f64;
        dot += (q[i] as f64) * val;
        norm_b_sq += val * val;
    }
    let norm_q_sq: f64 = q.iter().map(|&v| (v as f64) * (v as f64)).sum();
    let denom = (norm_q_sq.sqrt() * norm_b_sq.sqrt()) + 1e-9;
    dot / denom
}

// -----------------------------------------------------------------------------
// SQLite Schema Initialization & Non-Destructive FTS5 Migration
// -----------------------------------------------------------------------------

pub fn init_db(db_path: &Path) -> Result<Connection, String> {
    if let Some(parent) = db_path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("Failed creating DB parent dir: {}", e))?;
    }
    let conn = Connection::open(db_path).map_err(|e| format!("Failed opening FlowFS DB: {}", e))?;
    conn.execute_batch(
        "
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA busy_timeout=3000;

        CREATE TABLE IF NOT EXISTS flow_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime REAL NOT NULL,
            title TEXT,
            snippet TEXT,
            embedding BLOB NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_path ON flow_documents(path);
        CREATE INDEX IF NOT EXISTS idx_filename ON flow_documents(filename);

        CREATE TABLE IF NOT EXISTS flow_screen_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            window_title TEXT,
            app_class TEXT,
            screenshot_path TEXT,
            thumbnail_path TEXT,
            extracted_text TEXT,
            embedding BLOB NOT NULL,
            frame_hash TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_screen_ts ON flow_screen_memory(timestamp);
        ",
    )
    .map_err(|e| format!("Failed creating FlowFS tables: {}", e))?;

    // Non-destructive column upgrades for pre-existing Python flowfs.vec.db
    let mut screen_cols = HashSet::new();
    {
        let mut stmt = conn
            .prepare("PRAGMA table_info(flow_screen_memory)")
            .map_err(|e| e.to_string())?;
        let mut rows = stmt.query([]).map_err(|e| e.to_string())?;
        while let Some(r) = rows.next().map_err(|e| e.to_string())? {
            if let Ok(name) = r.get::<_, String>(1) {
                screen_cols.insert(name);
            }
        }
    }
    if !screen_cols.contains("thumbnail_path") {
        let _ = conn.execute("ALTER TABLE flow_screen_memory ADD COLUMN thumbnail_path TEXT", []);
    }
    if !screen_cols.contains("frame_hash") {
        let _ = conn.execute(
            "ALTER TABLE flow_screen_memory ADD COLUMN frame_hash TEXT DEFAULT ''",
            [],
        );
    }

    conn.execute_batch(
        "
        CREATE INDEX IF NOT EXISTS idx_screen_hash ON flow_screen_memory(frame_hash);

        CREATE VIRTUAL TABLE IF NOT EXISTS flow_documents_fts USING fts5(
            path,
            filename,
            title,
            snippet,
            content='flow_documents',
            content_rowid='id',
            tokenize='porter unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS flow_documents_ai AFTER INSERT ON flow_documents BEGIN
            INSERT INTO flow_documents_fts(rowid, path, filename, title, snippet)
            VALUES (new.id, new.path, new.filename, COALESCE(new.title, ''), COALESCE(new.snippet, ''));
        END;

        CREATE TRIGGER IF NOT EXISTS flow_documents_ad AFTER DELETE ON flow_documents BEGIN
            INSERT INTO flow_documents_fts(flow_documents_fts, rowid, path, filename, title, snippet)
            VALUES ('delete', old.id, old.path, old.filename, COALESCE(old.title, ''), COALESCE(old.snippet, ''));
        END;

        CREATE TRIGGER IF NOT EXISTS flow_documents_au AFTER UPDATE OF path, filename, title, snippet ON flow_documents BEGIN
            INSERT INTO flow_documents_fts(flow_documents_fts, rowid, path, filename, title, snippet)
            VALUES ('delete', old.id, old.path, old.filename, COALESCE(old.title, ''), COALESCE(old.snippet, ''));
            INSERT INTO flow_documents_fts(rowid, path, filename, title, snippet)
            VALUES (new.id, new.path, new.filename, COALESCE(new.title, ''), COALESCE(new.snippet, ''));
        END;

        CREATE VIRTUAL TABLE IF NOT EXISTS flow_screen_fts USING fts5(
            window_title,
            app_class,
            extracted_text,
            screenshot_path,
            content='flow_screen_memory',
            content_rowid='id',
            tokenize='porter unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS flow_screen_ai AFTER INSERT ON flow_screen_memory BEGIN
            INSERT INTO flow_screen_fts(rowid, window_title, app_class, extracted_text, screenshot_path)
            VALUES (new.id, COALESCE(new.window_title, ''), COALESCE(new.app_class, ''), COALESCE(new.extracted_text, ''), COALESCE(new.screenshot_path, ''));
        END;

        CREATE TRIGGER IF NOT EXISTS flow_screen_ad AFTER DELETE ON flow_screen_memory BEGIN
            INSERT INTO flow_screen_fts(flow_screen_fts, rowid, window_title, app_class, extracted_text, screenshot_path)
            VALUES ('delete', old.id, COALESCE(old.window_title, ''), COALESCE(old.app_class, ''), COALESCE(old.extracted_text, ''), COALESCE(old.screenshot_path, ''));
        END;

        CREATE TRIGGER IF NOT EXISTS flow_screen_au AFTER UPDATE OF window_title, app_class, extracted_text, screenshot_path ON flow_screen_memory BEGIN
            INSERT INTO flow_screen_fts(flow_screen_fts, rowid, window_title, app_class, extracted_text, screenshot_path)
            VALUES ('delete', old.id, COALESCE(old.window_title, ''), COALESCE(old.app_class, ''), COALESCE(old.extracted_text, ''), COALESCE(old.screenshot_path, ''));
            INSERT INTO flow_screen_fts(rowid, window_title, app_class, extracted_text, screenshot_path)
            VALUES (new.id, COALESCE(new.window_title, ''), COALESCE(new.app_class, ''), COALESCE(new.extracted_text, ''), COALESCE(new.screenshot_path, ''));
        END;
        ",
    )
    .map_err(|e| format!("Failed creating FlowFS FTS5 triggers: {}", e))?;

    // Backfill FTS5 indexes cleanly if migrating an existing DB populated by Python
    let doc_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_documents", [], |r| r.get(0))
        .unwrap_or(0);
    let doc_fts_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_documents_fts", [], |r| r.get(0))
        .unwrap_or(0);
    if doc_count > 0 && doc_fts_count == 0 {
        let _ = conn.execute("INSERT INTO flow_documents_fts(flow_documents_fts) VALUES('rebuild')", []);
    }

    let scr_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_screen_memory", [], |r| r.get(0))
        .unwrap_or(0);
    let scr_fts_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_screen_fts", [], |r| r.get(0))
        .unwrap_or(0);
    if scr_count > 0 && scr_fts_count == 0 {
        let _ = conn.execute("INSERT INTO flow_screen_fts(flow_screen_fts) VALUES('rebuild')", []);
    }

    Ok(conn)
}

// -----------------------------------------------------------------------------
// Document Indexing & Hybrid Semantic Search
// -----------------------------------------------------------------------------

fn extract_file_content(path: &Path) -> (String, String, String) {
    let fname = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();
    let Ok(mut file) = fs::File::open(path) else {
        return (fname, String::new(), String::new());
    };
    let mut buf = vec![0u8; 32 * 1024];
    let n = match file.read(&mut buf) {
        Ok(n) => n,
        Err(_) => return (fname, String::new(), String::new()),
    };
    buf.truncate(n);
    let content = String::from_utf8_lossy(&buf).into_owned();
    let lines: Vec<&str> = content
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty())
        .collect();

    let mut title = String::new();
    for line in lines.iter().take(5) {
        if line.starts_with('#') {
            title = line.trim_start_matches('#').trim().to_string();
            break;
        }
    }
    if title.is_empty() {
        if let Some(first) = lines.first() {
            title = first.chars().take(80).collect();
        }
    }
    if title.is_empty() {
        title = fname.clone();
    }
    let snippet: String = lines
        .iter()
        .take(5)
        .copied()
        .collect::<Vec<_>>()
        .join(" ")
        .chars()
        .take(360)
        .collect();

    (title, snippet, content)
}

pub fn index_files(db_path: &Path, roots: Option<&[PathBuf]>) -> Result<IndexFilesReport, String> {
    let start = Instant::now();
    let mut conn = init_db(db_path)?;

    let mut existing: HashMap<String, f64> = HashMap::new();
    {
        let mut stmt = conn
            .prepare("SELECT path, mtime FROM flow_documents")
            .map_err(|e| e.to_string())?;
        let mut rows = stmt.query([]).map_err(|e| e.to_string())?;
        while let Some(row) = rows.next().map_err(|e| e.to_string())? {
            if let (Ok(p), Ok(mt)) = (row.get::<_, String>(0), row.get::<_, f64>(1)) {
                existing.insert(p, mt);
            }
        }
    }

    let ignore_set: HashSet<&str> = IGNORE_DIRS.iter().copied().collect();
    let ext_set: HashSet<&str> = INDEXABLE_EXTENSIONS.iter().copied().collect();

    let default_roots = default_search_roots();
    let active_roots = roots.unwrap_or(&default_roots);

    let mut new_count = 0usize;
    let mut updated_count = 0usize;
    let mut unchanged_count = 0usize;
    let mut seen_paths = HashSet::new();
    type DocBatchRow = (String, String, String, i64, f64, String, String, Vec<u8>);
    let mut batch: Vec<DocBatchRow> = Vec::new();

    for root in active_roots {
        if !root.is_dir() {
            continue;
        }
        let root_ignore = ignore_set.clone();
        let walker = WalkBuilder::new(root)
            .hidden(true)
            .git_ignore(false)
            .ignore(false)
            .follow_links(false)
            .filter_entry(move |entry| {
                if entry.depth() == 0 {
                    return true;
                }
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    if let Some(name) = entry.file_name().to_str() {
                        return !root_ignore.contains(name) && !name.starts_with('.');
                    }
                }
                true
            })
            .build();

        for entry in walker.flatten() {
            if !entry.file_type().map(|t| t.is_file()).unwrap_or(false) {
                continue;
            }
            let path = entry.path();
            let Some(ext_raw) = path.extension().and_then(|e| e.to_str()) else {
                continue;
            };
            let ext_low = ext_raw.to_ascii_lowercase();
            if !ext_set.contains(ext_low.as_str()) {
                continue;
            }
            let ext_dot = format!(".{}", ext_low);
            let fname = path
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();
            let fname_low = fname.to_ascii_lowercase();
            if fname_low == "vault.json"
                || fname_low == "flowork.dev"
                || fname_low.ends_with(".key")
                || fname_low.ends_with(".pem")
            {
                continue;
            }

            let Ok(meta) = entry.metadata() else {
                continue;
            };
            let size = meta.len();
            if size > MAX_INDEXABLE_FILE_BYTES {
                continue;
            }
            let mtime = meta
                .modified()
                .ok()
                .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
                .map(|d| d.as_secs_f64())
                .unwrap_or(0.0);

            let full_path_str = path.to_string_lossy().into_owned();
            seen_paths.insert(full_path_str.clone());

            if let Some(&prev_mt) = existing.get(&full_path_str) {
                if (prev_mt - mtime).abs() < 1.0 {
                    unchanged_count += 1;
                    continue;
                }
                updated_count += 1;
            } else {
                new_count += 1;
            }

            let (title, snippet, content) = extract_file_content(path);
            let combined = format!("{} {} {}", fname, title, content);
            let vec = text_to_vector(&combined);
            batch.push((
                full_path_str,
                fname,
                ext_dot,
                size as i64,
                mtime,
                title,
                snippet,
                vec_to_blob(&vec),
            ));
        }
    }

    if !batch.is_empty() {
        let tx = conn.transaction().map_err(|e| e.to_string())?;
        {
            let mut stmt = tx
                .prepare(
                    "INSERT INTO flow_documents (path, filename, extension, size, mtime, title, snippet, embedding)
                     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
                     ON CONFLICT(path) DO UPDATE SET
                       filename = excluded.filename,
                       extension = excluded.extension,
                       size = excluded.size,
                       mtime = excluded.mtime,
                       title = excluded.title,
                       snippet = excluded.snippet,
                       embedding = excluded.embedding",
                )
                .map_err(|e| e.to_string())?;
            for item in batch {
                stmt.execute(params![
                    item.0, item.1, item.2, item.3, item.4, item.5, item.6, item.7
                ])
                .map_err(|e| e.to_string())?;
            }
        }
        tx.commit().map_err(|e| e.to_string())?;
    }

    let mut purged_count = 0usize;
    let stale: Vec<String> = existing
        .keys()
        .filter(|k| !seen_paths.contains(*k))
        .cloned()
        .collect();
    if !stale.is_empty() {
        let tx = conn.transaction().map_err(|e| e.to_string())?;
        {
            let mut del_stmt = tx
                .prepare("DELETE FROM flow_documents WHERE path = ?1")
                .map_err(|e| e.to_string())?;
            for p in &stale {
                purged_count += del_stmt.execute(params![p]).unwrap_or(0);
            }
        }
        tx.commit().map_err(|e| e.to_string())?;
    }

    Ok(IndexFilesReport {
        new: new_count,
        updated: updated_count,
        unchanged: unchanged_count,
        purged: purged_count,
        elapsed_ms: (start.elapsed().as_secs_f64() * 100.0).round() / 100.0,
    })
}

fn build_safe_fts_query(query: &str, prefix_match: bool) -> Option<(String, Vec<String>)> {
    let tokens: Vec<String> = tokenize_words(query)
        .into_iter()
        .filter(|t| t.len() >= 2)
        .take(12)
        .collect();
    if tokens.is_empty() {
        return None;
    }
    let expr = tokens
        .iter()
        .map(|t| {
            if prefix_match && t.len() >= 3 {
                format!("\"{}\"*", t)
            } else {
                format!("\"{}\"", t)
            }
        })
        .collect::<Vec<_>>()
        .join(" OR ");
    Some((expr, tokens))
}

pub fn semantic_search(
    db_path: &Path,
    query: &str,
    limit: usize,
) -> Result<Vec<DocumentSearchResult>, String> {
    if query.trim().is_empty() {
        return Ok(Vec::new());
    }
    if !db_path.is_file() {
        let _ = index_files(db_path, None);
        if !db_path.is_file() {
            return Ok(Vec::new());
        }
    }

    let conn = init_db(db_path)?;
    let query_vec = text_to_vector(query);
    let q_words = tokenize_words(query);
    let q_lower = query.trim().to_ascii_lowercase();
    let max_out = limit.clamp(1, 50);

    // 1. Collect FTS5 BM25 candidate scores
    let mut fts_scores: HashMap<i64, f64> = HashMap::new();
    if let Some((fts_expr, _)) = build_safe_fts_query(query, true) {
        if let Ok(mut stmt) = conn.prepare(
            "SELECT d.id, bm25(flow_documents_fts, 0.5, 4.0, 2.5, 1.5) AS rank
             FROM flow_documents_fts f
             JOIN flow_documents d ON f.rowid = d.id
             WHERE flow_documents_fts MATCH ?1
             ORDER BY rank ASC
             LIMIT 120",
        ) {
            if let Ok(rows) = stmt.query_map(params![fts_expr], |r| {
                Ok((r.get::<_, i64>(0)?, r.get::<_, f64>(1)?))
            }) {
                for row in rows.flatten() {
                    // BM25 rank is negative when strong in FTS5; invert to positive bonus
                    let bonus = (-row.1).clamp(0.1, 12.0) * 0.08;
                    fts_scores.insert(row.0, bonus);
                }
            }
        }
    }

    // 2. Hybrid vector cosine + filename/title/snippet match across documents
    let mut stmt = conn
        .prepare("SELECT id, path, filename, extension, size, COALESCE(title,''), COALESCE(snippet,''), embedding FROM flow_documents")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |r| {
            Ok((
                r.get::<_, i64>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, String>(3)?,
                r.get::<_, i64>(4)?,
                r.get::<_, String>(5)?,
                r.get::<_, String>(6)?,
                r.get::<_, Vec<u8>>(7)?,
            ))
        })
        .map_err(|e| e.to_string())?;

    let mut scored = Vec::new();
    for row in rows.flatten() {
        let (id, path, filename, extension, size, title, snippet, blob) = row;
        let cos = blob_cosine_similarity(&query_vec, &blob);
        let fts_bonus = fts_scores.get(&id).copied().unwrap_or(0.0);

        let fn_low = filename.to_ascii_lowercase();
        let title_low = title.to_ascii_lowercase();
        let snip_low = snippet.to_ascii_lowercase();

        let mut kw_bonus = 0.0f64;
        if fn_low.contains(&q_lower) {
            kw_bonus += 0.45;
        }
        if title_low.contains(&q_lower) {
            kw_bonus += 0.30;
        }
        for w in &q_words {
            if w.len() < 3 {
                continue;
            }
            if fn_low.contains(w.as_str()) {
                kw_bonus += 0.25;
            }
            if title_low.contains(w.as_str()) {
                kw_bonus += 0.15;
            }
            if snip_low.contains(w.as_str()) {
                kw_bonus += 0.06;
            }
        }

        let total = cos + fts_bonus + kw_bonus;
        if total > 0.06 {
            scored.push(DocumentSearchResult {
                id,
                path,
                filename,
                extension,
                size,
                title,
                snippet,
                score: (total * 10_000.0).round() / 10_000.0,
            });
        }
    }

    scored.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    scored.truncate(max_out);
    Ok(scored)
}

// -----------------------------------------------------------------------------
// Native Dynamic Library Bindings: liblept.so.5, libtesseract.so.5, libwebp.so.7
// -----------------------------------------------------------------------------

type PixCreateFromFileFn = unsafe extern "C" fn(*const c_char) -> *mut c_void;
type PixConvertTo32Fn = unsafe extern "C" fn(*mut c_void) -> *mut c_void;
type PixGetDimFn = unsafe extern "C" fn(*mut c_void) -> c_int;
type PixGetPixelFn = unsafe extern "C" fn(*mut c_void, c_int, c_int, *mut u32) -> c_int;
type PixDestroyFn = unsafe extern "C" fn(*mut *mut c_void);

type TessCreateFn = unsafe extern "C" fn() -> *mut c_void;
type TessInit3Fn = unsafe extern "C" fn(*mut c_void, *const c_char, *const c_char) -> c_int;
type TessSetPageSegModeFn = unsafe extern "C" fn(*mut c_void, c_int);
type TessSetImageFn =
    unsafe extern "C" fn(*mut c_void, *const c_uchar, c_int, c_int, c_int, c_int);
type TessGetUtf8TextFn = unsafe extern "C" fn(*mut c_void) -> *mut c_char;
type TessDeleteTextFn = unsafe extern "C" fn(*mut c_char);
type TessEndFn = unsafe extern "C" fn(*mut c_void);
type TessDeleteFn = unsafe extern "C" fn(*mut c_void);

type WebPEncodeRgbaFn =
    unsafe extern "C" fn(*const u8, c_int, c_int, c_int, c_float, *mut *mut u8) -> usize;
type WebPFreeFn = unsafe extern "C" fn(*mut c_void);

struct LeptonicaFfi {
    pix_read: PixCreateFromFileFn,
    pix_convert_to_32: PixConvertTo32Fn,
    pix_get_width: PixGetDimFn,
    pix_get_height: PixGetDimFn,
    pix_get_pixel: PixGetPixelFn,
    pix_destroy: PixDestroyFn,
}

struct TesseractFfi {
    create: TessCreateFn,
    init3: TessInit3Fn,
    set_psm: TessSetPageSegModeFn,
    set_image: TessSetImageFn,
    get_utf8_text: TessGetUtf8TextFn,
    delete_text: TessDeleteTextFn,
    end: TessEndFn,
    delete: TessDeleteFn,
}

struct WebpFfi {
    encode_rgba: WebPEncodeRgbaFn,
    encode_bgra: WebPEncodeRgbaFn,
    free: WebPFreeFn,
}

unsafe fn dlopen_any(candidates: &[&str]) -> *mut c_void {
    for name in candidates {
        if let Ok(c_name) = CString::new(*name) {
            let handle = libc::dlopen(c_name.as_ptr(), libc::RTLD_LAZY | libc::RTLD_LOCAL);
            if !handle.is_null() {
                return handle;
            }
        }
    }
    std::ptr::null_mut()
}

unsafe fn dlsym_opt<T>(handle: *mut c_void, sym: &str) -> Option<T> {
    if handle.is_null() {
        return None;
    }
    let c_sym = CString::new(sym).ok()?;
    let ptr = libc::dlsym(handle, c_sym.as_ptr());
    if ptr.is_null() {
        None
    } else {
        Some(std::mem::transmute_copy(&ptr))
    }
}

fn lept_ffi() -> Option<&'static LeptonicaFfi> {
    static CELL: OnceLock<Option<LeptonicaFfi>> = OnceLock::new();
    CELL.get_or_init(|| unsafe {
        let handle = dlopen_any(&[
            "liblept.so.5",
            "/usr/lib/x86_64-linux-gnu/liblept.so.5",
            "/usr/lib/liblept.so.5",
        ]);
        Some(LeptonicaFfi {
            pix_read: dlsym_opt(handle, "pixRead")?,
            pix_convert_to_32: dlsym_opt(handle, "pixConvertTo32")?,
            pix_get_width: dlsym_opt(handle, "pixGetWidth")?,
            pix_get_height: dlsym_opt(handle, "pixGetHeight")?,
            pix_get_pixel: dlsym_opt(handle, "pixGetPixel")?,
            pix_destroy: dlsym_opt(handle, "pixDestroy")?,
        })
    })
    .as_ref()
}

fn tess_ffi() -> Option<&'static TesseractFfi> {
    static CELL: OnceLock<Option<TesseractFfi>> = OnceLock::new();
    CELL.get_or_init(|| unsafe {
        let handle = dlopen_any(&[
            "libtesseract.so.5",
            "/usr/lib/x86_64-linux-gnu/libtesseract.so.5",
            "/usr/lib/libtesseract.so.5",
        ]);
        Some(TesseractFfi {
            create: dlsym_opt(handle, "TessBaseAPICreate")?,
            init3: dlsym_opt(handle, "TessBaseAPIInit3")?,
            set_psm: dlsym_opt(handle, "TessBaseAPISetPageSegMode")?,
            set_image: dlsym_opt(handle, "TessBaseAPISetImage")?,
            get_utf8_text: dlsym_opt(handle, "TessBaseAPIGetUTF8Text")?,
            delete_text: dlsym_opt(handle, "TessDeleteText")?,
            end: dlsym_opt(handle, "TessBaseAPIEnd")?,
            delete: dlsym_opt(handle, "TessBaseAPIDelete")?,
        })
    })
    .as_ref()
}

fn webp_ffi() -> Option<&'static WebpFfi> {
    static CELL: OnceLock<Option<WebpFfi>> = OnceLock::new();
    CELL.get_or_init(|| unsafe {
        let handle = dlopen_any(&[
            "libwebp.so.7",
            "/usr/lib/x86_64-linux-gnu/libwebp.so.7",
            "/usr/lib/libwebp.so.7",
        ]);
        Some(WebpFfi {
            encode_rgba: dlsym_opt(handle, "WebPEncodeRGBA")?,
            encode_bgra: dlsym_opt(handle, "WebPEncodeBGRA")?,
            free: dlsym_opt(handle, "WebPFree")?,
        })
    })
    .as_ref()
}

// -----------------------------------------------------------------------------
// Visual Pixel Utilities: Resize, Perceptual dHash, WebP Thumbnail, Bounded OCR
// -----------------------------------------------------------------------------

pub fn rgba_to_dhash_hex(pixels: &[u8], width: u32, height: u32, is_bgra: bool) -> String {
    if width == 0 || height == 0 || pixels.len() < (width as usize) * (height as usize) * 4 {
        return String::new();
    }
    let mut grid = [0u32; 9 * 8];
    for gy in 0..8usize {
        let sy = ((gy as u64 * height as u64) / 8).min((height - 1) as u64) as usize;
        for gx in 0..9usize {
            let sx = ((gx as u64 * width as u64) / 9).min((width - 1) as u64) as usize;
            let off = (sy * (width as usize) + sx) * 4;
            let (r, g, b) = if is_bgra {
                (pixels[off + 2] as u32, pixels[off + 1] as u32, pixels[off] as u32)
            } else {
                (pixels[off] as u32, pixels[off + 1] as u32, pixels[off + 2] as u32)
            };
            grid[gy * 9 + gx] = (77 * r + 150 * g + 29 * b) >> 8;
        }
    }
    let mut hash: u64 = 0;
    let mut bit = 0u32;
    for gy in 0..8usize {
        for gx in 0..8usize {
            if grid[gy * 9 + gx] > grid[gy * 9 + gx + 1] {
                hash |= 1u64 << bit;
            }
            bit += 1;
        }
    }
    format!("{:016x}", hash)
}

pub fn dhash_hamming_distance(a_hex: &str, b_hex: &str) -> Option<u32> {
    if a_hex.len() != 16 || b_hex.len() != 16 {
        return None;
    }
    let a = u64::from_str_radix(a_hex, 16).ok()?;
    let b = u64::from_str_radix(b_hex, 16).ok()?;
    Some((a ^ b).count_ones())
}

fn downsample_4bpp(
    src: &[u8],
    src_w: u32,
    src_h: u32,
    dst_w: u32,
    dst_h: u32,
) -> Vec<u8> {
    let mut out = vec![0u8; (dst_w as usize) * (dst_h as usize) * 4];
    for dy in 0..dst_h {
        let sy = ((dy as u64 * src_h as u64) / dst_h as u64).min((src_h - 1) as u64) as u32;
        for dx in 0..dst_w {
            let sx = ((dx as u64 * src_w as u64) / dst_w as u64).min((src_w - 1) as u64) as u32;
            let soff = ((sy as usize) * (src_w as usize) + (sx as usize)) * 4;
            let doff = ((dy as usize) * (dst_w as usize) + (dx as usize)) * 4;
            out[doff..doff + 4].copy_from_slice(&src[soff..soff + 4]);
        }
    }
    out
}

fn encode_4bpp_to_webp(
    pixels: &[u8],
    width: u32,
    height: u32,
    is_bgra: bool,
    out_path: &Path,
) -> Result<(), String> {
    let webp = webp_ffi().ok_or_else(|| "libwebp.so.7 unavailable".to_string())?;
    let target_w: u32 = 320;
    let target_h: u32 = ((height as f64 / width.max(1) as f64) * target_w as f64)
        .round()
        .clamp(90.0, 240.0) as u32;

    let (buf, ew, eh) = if width > target_w {
        (downsample_4bpp(pixels, width, height, target_w, target_h), target_w, target_h)
    } else {
        (pixels.to_vec(), width, height)
    };

    unsafe {
        let mut out_ptr: *mut u8 = std::ptr::null_mut();
        let stride = (ew as c_int) * 4;
        let len = if is_bgra {
            (webp.encode_bgra)(buf.as_ptr(), ew as c_int, eh as c_int, stride, 80.0, &mut out_ptr)
        } else {
            (webp.encode_rgba)(buf.as_ptr(), ew as c_int, eh as c_int, stride, 80.0, &mut out_ptr)
        };
        if len == 0 || out_ptr.is_null() {
            return Err("WebPEncode failed".to_string());
        }
        let slice = std::slice::from_raw_parts(out_ptr, len);
        if let Some(parent) = out_path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        let tmp = out_path.with_extension("webp.tmp");
        let write_res = fs::write(&tmp, slice);
        (webp.free)(out_ptr as *mut c_void);
        write_res.map_err(|e| format!("Failed writing WebP temp: {}", e))?;
        fs::rename(&tmp, out_path).map_err(|e| format!("Failed publishing WebP thumb: {}", e))?;
    }
    Ok(())
}

fn read_image_rgba_via_lept(image_path: &Path) -> Result<(Vec<u8>, u32, u32), String> {
    let lept = lept_ffi().ok_or_else(|| "liblept.so.5 unavailable".to_string())?;
    let c_path = CString::new(image_path.to_string_lossy().as_bytes())
        .map_err(|_| "Invalid image path".to_string())?;
    unsafe {
        let mut pix = (lept.pix_read)(c_path.as_ptr());
        if pix.is_null() {
            return Err(format!("liblept could not decode {}", image_path.display()));
        }
        let pix32 = (lept.pix_convert_to_32)(pix);
        (lept.pix_destroy)(&mut pix);
        if pix32.is_null() {
            return Err("pixConvertTo32 returned null".to_string());
        }
        let w = (lept.pix_get_width)(pix32) as u32;
        let h = (lept.pix_get_height)(pix32) as u32;
        if w == 0 || h == 0 || w > 16384 || h > 16384 {
            let mut p = pix32;
            (lept.pix_destroy)(&mut p);
            return Err("Invalid image dimensions".to_string());
        }
        let mut rgba = vec![0u8; (w as usize) * (h as usize) * 4];
        for y in 0..h {
            for x in 0..w {
                let mut px_val: u32 = 0;
                (lept.pix_get_pixel)(pix32, x as c_int, y as c_int, &mut px_val);
                let off = ((y as usize) * (w as usize) + (x as usize)) * 4;
                rgba[off] = ((px_val >> 24) & 0xff) as u8;
                rgba[off + 1] = ((px_val >> 16) & 0xff) as u8;
                rgba[off + 2] = ((px_val >> 8) & 0xff) as u8;
                rgba[off + 3] = (px_val & 0xff) as u8;
            }
        }
        let mut p = pix32;
        (lept.pix_destroy)(&mut p);
        Ok((rgba, w, h))
    }
}

pub fn generate_webp_thumbnail_for_file(image_path: &Path, key_seed: &str) -> Option<String> {
    if !image_path.is_file() {
        return None;
    }
    let thumbs_dir = resolve_thumbs_dir();
    let mut hasher = Sha256::new();
    hasher.update(key_seed.as_bytes());
    let hex_digest: String = hasher
        .finalize()
        .iter()
        .take(12)
        .map(|b| format!("{:02x}", b))
        .collect();
    let thumb_path = thumbs_dir.join(format!("{}.webp", hex_digest));
    if thumb_path.is_file() {
        return Some(thumb_path.to_string_lossy().into_owned());
    }

    if let Ok((rgba, w, h)) = read_image_rgba_via_lept(image_path) {
        if encode_4bpp_to_webp(&rgba, w, h, false, &thumb_path).is_ok() {
            return Some(thumb_path.to_string_lossy().into_owned());
        }
    }

    // Fallback to ImageMagick `convert` if available
    if let Ok(status) = std::process::Command::new("convert")
        .args([
            image_path.to_string_lossy().as_ref(),
            "-resize",
            "320x180^",
            "-gravity",
            "center",
            "-extent",
            "320x180",
            "-quality",
            "80",
            thumb_path.to_string_lossy().as_ref(),
        ])
        .status()
    {
        if status.success() && thumb_path.is_file() {
            return Some(thumb_path.to_string_lossy().into_owned());
        }
    }

    None
}

fn prepare_l8_for_ocr(
    pixels: &[u8],
    width: u32,
    height: u32,
    is_bgra: bool,
) -> (Vec<u8>, u32, u32) {
    let dst_w = width.clamp(1, 1280);
    let dst_h = if width > dst_w {
        ((height as f64 / width as f64) * dst_w as f64)
            .round()
            .max(1.0) as u32
    } else {
        height.max(1)
    };

    let len = (dst_w as usize) * (dst_h as usize);
    let mut gray = vec![0u8; len];
    let mut sum: u64 = 0;

    for dy in 0..dst_h {
        let sy = ((dy as u64 * height as u64) / dst_h as u64).min((height - 1) as u64) as usize;
        for dx in 0..dst_w {
            let sx = ((dx as u64 * width as u64) / dst_w as u64).min((width - 1) as u64) as usize;
            let off = (sy * (width as usize) + sx) * 4;
            let (r, g, b) = if is_bgra {
                (pixels[off + 2] as u32, pixels[off + 1] as u32, pixels[off] as u32)
            } else {
                (pixels[off] as u32, pixels[off + 1] as u32, pixels[off + 2] as u32)
            };
            let lum = ((77 * r + 150 * g + 29 * b) >> 8) as u8;
            gray[(dy as usize) * (dst_w as usize) + (dx as usize)] = lum;
            sum += lum as u64;
        }
    }

    // Dark-mode HUD inversion: Tesseract accuracy & speed improve dramatically on light paper/dark ink
    if !gray.is_empty() && (sum / gray.len() as u64) < 110 {
        for px in &mut gray {
            *px = 255 - *px;
        }
    }

    (gray, dst_w, dst_h)
}

pub fn extract_ocr_from_pixels_bounded(
    pixels: &[u8],
    width: u32,
    height: u32,
    is_bgra: bool,
    timeout_ms: u64,
) -> String {
    if width == 0 || height == 0 || pixels.len() < (width as usize) * (height as usize) * 4 {
        return String::new();
    }
    let Some(tessdata) = resolve_tessdata_dir() else {
        return String::new();
    };
    if tess_ffi().is_none() {
        return String::new();
    }

    let (gray, ow, oh) = prepare_l8_for_ocr(pixels, width, height, is_bgra);
    let (tx, rx) = mpsc::channel();
    std::thread::spawn(move || {
        let text = run_ocr_l8_sync(&gray, ow, oh, &tessdata).unwrap_or_default();
        let _ = tx.send(text);
    });

    rx.recv_timeout(Duration::from_millis(timeout_ms.clamp(200, 5000)))
        .unwrap_or_default()
}

pub fn extract_ocr_from_file_bounded(image_path: &Path, timeout_ms: u64) -> String {
    if !image_path.is_file() {
        return String::new();
    }
    if let Ok((rgba, w, h)) = read_image_rgba_via_lept(image_path) {
        return extract_ocr_from_pixels_bounded(&rgba, w, h, false, timeout_ms);
    }
    String::new()
}

pub fn extract_ocr_from_bgra_bounded(
    bgra: &[u8],
    width: u32,
    height: u32,
    timeout_ms: u64,
) -> String {
    extract_ocr_from_pixels_bounded(bgra, width, height, true, timeout_ms)
}

fn run_ocr_l8_sync(gray: &[u8], width: u32, height: u32, tessdata_dir: &Path) -> Option<String> {
    let tess = tess_ffi()?;
    let c_data = CString::new(tessdata_dir.to_string_lossy().as_bytes()).ok()?;
    let c_lang = CString::new("eng").ok()?;

    unsafe {
        let api = (tess.create)();
        if api.is_null() {
            return None;
        }
        if (tess.init3)(api, c_data.as_ptr(), c_lang.as_ptr()) != 0 {
            (tess.delete)(api);
            return None;
        }
        (tess.set_psm)(api, 3);
        (tess.set_image)(
            api,
            gray.as_ptr(),
            width as c_int,
            height as c_int,
            1,
            width as c_int,
        );
        let txt_ptr = (tess.get_utf8_text)(api);
        let extracted = if !txt_ptr.is_null() {
            let s = CStr::from_ptr(txt_ptr).to_string_lossy().into_owned();
            (tess.delete_text)(txt_ptr);
            s
        } else {
            String::new()
        };
        (tess.end)(api);
        (tess.delete)(api);
        Some(scrub_ocr_text(&extracted))
    }
}

// -----------------------------------------------------------------------------
// Telemetry & IPC Helpers: flowork-sysd Windows API & flowork-neural-bus Publish
// -----------------------------------------------------------------------------

pub fn fetch_active_window_meta() -> ActiveWindowMeta {
    let Ok(mut stream) =
        TcpStream::connect_timeout(&"127.0.0.1:18090".parse().unwrap(), Duration::from_millis(250))
    else {
        return ActiveWindowMeta::default();
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(350)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(250)));

    let req = b"GET /api/system/windows HTTP/1.1\r\nHost: 127.0.0.1:18090\r\nConnection: close\r\n\r\n";
    if stream.write_all(req).is_err() {
        return ActiveWindowMeta::default();
    }
    let mut raw = String::new();
    if stream.read_to_string(&mut raw).is_err() {
        return ActiveWindowMeta::default();
    }
    let body = raw.split("\r\n\r\n").nth(1).unwrap_or("");
    let Ok(json_val) = serde_json::from_str::<serde_json::Value>(body) else {
        return ActiveWindowMeta::default();
    };
    let Some(wins) = json_val.get("windows").and_then(|v| v.as_array()) else {
        return ActiveWindowMeta::default();
    };

    let chosen = wins
        .iter()
        .find(|w| {
            w.get("is_active").and_then(|v| v.as_bool()).unwrap_or(false)
                || w.get("is_focused").and_then(|v| v.as_bool()).unwrap_or(false)
        })
        .or_else(|| wins.last());

    if let Some(w) = chosen {
        let title = w
            .get("title")
            .and_then(|v| v.as_str())
            .unwrap_or("Desktop")
            .to_string();
        let raw_cls = w
            .get("wm_class")
            .or_else(|| w.get("class_name"))
            .and_then(|v| v.as_str())
            .unwrap_or("Desktop");
        let app_class = raw_cls
            .split('\0')
            .rfind(|s| !s.trim().is_empty())
            .unwrap_or("Desktop")
            .to_string();
        return ActiveWindowMeta {
            window_title: title,
            app_class,
        };
    }
    ActiveWindowMeta::default()
}

pub fn publish_screen_indexed_event(report: &IndexScreenReport) {
    let payload = serde_json::json!({
        "type": "event",
        "source": "flowfs",
        "target": "*",
        "action": "flowfs.screen.indexed",
        "payload": {
            "id": report.id,
            "timestamp": report.timestamp,
            "window_title": report.window_title,
            "app_class": report.app_class,
            "screenshot_path": report.screenshot_path,
            "thumbnail_path": report.thumbnail_path,
            "frame_hash": report.frame_hash,
            "ocr_chars": report.ocr_chars
        }
    });
    let Ok(body) = serde_json::to_vec(&payload) else {
        return;
    };

    // Unix socket speaks newline-delimited JSON messages
    let sock_candidates = [
        PathBuf::from("/tmp/flowork-neural-bus.sock"),
        PathBuf::from("/run/flowork/bus.sock"),
        resolve_home_dir().join(".flowork").join("bus.sock"),
    ];
    for sock in &sock_candidates {
        if sock.exists() {
            if let Ok(mut u) = UnixStream::connect(sock) {
                let _ = u.set_write_timeout(Some(Duration::from_millis(200)));
                let _ = u.set_read_timeout(Some(Duration::from_millis(200)));
                let mut line = body.clone();
                line.push(b'\n');
                if u.write_all(&line).is_ok() {
                    let mut ack = [0u8; 256];
                    let _ = u.read(&mut ack);
                    return;
                }
            }
        }
    }

    // Fallback to TCP HTTP /api/bus/publish
    let http_req = format!(
        "POST /api/bus/publish HTTP/1.1\r\nHost: 127.0.0.1:18095\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
        body.len()
    );
    if let Ok(mut tcp) =
        TcpStream::connect_timeout(&"127.0.0.1:18095".parse().unwrap(), Duration::from_millis(200))
    {
        let _ = tcp.set_write_timeout(Some(Duration::from_millis(200)));
        let _ = tcp.write_all(http_req.as_bytes());
        let _ = tcp.write_all(&body);
    }
}

// -----------------------------------------------------------------------------
// Visual OCR Screen Memory Indexing, Retention & Search
// -----------------------------------------------------------------------------

pub fn latest_frame_hash(conn: &Connection) -> Option<String> {
    conn.query_row(
        "SELECT COALESCE(frame_hash, '') FROM flow_screen_memory WHERE frame_hash != '' ORDER BY id DESC LIMIT 1",
        [],
        |r| r.get::<_, String>(0),
    )
    .ok()
    .filter(|s| !s.is_empty())
}

pub fn purge_expired_screen_memory(db_path: &Path, retention_days: u64) -> Result<usize, String> {
    if !db_path.is_file() {
        return Ok(0);
    }
    let conn = init_db(db_path)?;
    let days = retention_days.max(1) as i64;
    let cutoff = (chrono::Utc::now() - chrono::Duration::days(days))
        .format("%Y-%m-%d %H:%M:%S")
        .to_string();

    let mut thumb_paths = Vec::new();
    {
        let mut stmt = conn
            .prepare("SELECT COALESCE(thumbnail_path, '') FROM flow_screen_memory WHERE timestamp < ?1")
            .map_err(|e| e.to_string())?;
        let mut rows = stmt.query(params![cutoff]).map_err(|e| e.to_string())?;
        while let Some(r) = rows.next().map_err(|e| e.to_string())? {
            if let Ok(tp) = r.get::<_, String>(0) {
                if !tp.is_empty() {
                    thumb_paths.push(tp);
                }
            }
        }
    }

    let deleted = conn
        .execute(
            "DELETE FROM flow_screen_memory WHERE timestamp < ?1",
            params![cutoff],
        )
        .map_err(|e| e.to_string())?;

    for tp in thumb_paths {
        let _ = fs::remove_file(tp);
    }

    Ok(deleted)
}

pub fn index_screen_capture(
    db_path: &Path,
    req: ScreenCaptureRequest<'_>,
) -> Result<IndexScreenReport, String> {
    let ts = chrono::Utc::now().format("%Y-%m-%d %H:%M:%S").to_string();
    let sys_win = if req.window_title.map(str::trim).unwrap_or("").is_empty()
        || req.app_class.map(str::trim).unwrap_or("").is_empty()
    {
        fetch_active_window_meta()
    } else {
        ActiveWindowMeta::default()
    };

    let window_title = req
        .window_title
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(str::to_string)
        .or_else(|| {
            if sys_win.window_title.is_empty() {
                None
            } else {
                Some(sys_win.window_title.clone())
            }
        })
        .unwrap_or_else(|| "Desktop".to_string());

    let app_class = req
        .app_class
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(str::to_string)
        .or_else(|| {
            if sys_win.app_class.is_empty() {
                None
            } else {
                Some(sys_win.app_class.clone())
            }
        })
        .unwrap_or_else(|| "Desktop".to_string());

    if let Some(matched_pat) =
        should_exclude_screen_capture(&window_title, &app_class, req.screenshot_path)
    {
        return Ok(IndexScreenReport {
            status: "skipped_privacy".to_string(),
            id: None,
            timestamp: ts,
            screenshot_path: req.screenshot_path.to_string(),
            thumbnail_path: String::new(),
            window_title,
            app_class,
            frame_hash: String::new(),
            ocr_chars: 0,
            extracted_text: String::new(),
            reason: Some(format!("Privacy exclusion matched: {}", matched_pat)),
        });
    }

    let conn = init_db(db_path)?;
    let img_path = Path::new(req.screenshot_path);
    let mut frame_hash = String::new();
    let decoded = if img_path.is_file() {
        read_image_rgba_via_lept(img_path).ok()
    } else {
        None
    };

    if let Some((ref rgba, w, h)) = decoded {
        frame_hash = rgba_to_dhash_hex(rgba, w, h, false);
        if !req.force && req.explicit_text.is_none() {
            if let Some(prev) = latest_frame_hash(&conn) {
                if let Some(dist) = dhash_hamming_distance(&prev, &frame_hash) {
                    if dist <= DHASH_UNCHANGED_MAX_HAMMING {
                        return Ok(IndexScreenReport {
                            status: "skipped_unchanged".to_string(),
                            id: None,
                            timestamp: ts,
                            screenshot_path: req.screenshot_path.to_string(),
                            thumbnail_path: String::new(),
                            window_title,
                            app_class,
                            frame_hash,
                            ocr_chars: 0,
                            extracted_text: String::new(),
                            reason: Some(format!("Keyframe delta {}/64 <= 3 bits (<5%)", dist)),
                        });
                    }
                }
            }
        }
    }

    let thumb_path = if let Some((ref rgba, w, h)) = decoded {
        let thumbs_dir = resolve_thumbs_dir();
        let seed = if frame_hash.is_empty() {
            format!("{}:{}", req.screenshot_path, ts)
        } else {
            format!("{}:{}", frame_hash, req.screenshot_path)
        };
        let mut hasher = Sha256::new();
        hasher.update(seed.as_bytes());
        let hex_digest: String = hasher
            .finalize()
            .iter()
            .take(12)
            .map(|b| format!("{:02x}", b))
            .collect();
        let target = thumbs_dir.join(format!("{}.webp", hex_digest));
        if target.is_file() || encode_4bpp_to_webp(rgba, w, h, false, &target).is_ok() {
            target.to_string_lossy().into_owned()
        } else {
            generate_webp_thumbnail_for_file(img_path, &seed).unwrap_or_default()
        }
    } else if img_path.is_file() {
        let seed = format!("{}:{}", req.screenshot_path, ts);
        generate_webp_thumbnail_for_file(img_path, &seed).unwrap_or_default()
    } else {
        String::new()
    };

    let extracted_text = match req.explicit_text {
        Some(t) if !t.trim().is_empty() => scrub_ocr_text(t),
        _ => {
            if !req.skip_ocr {
                if let Some((ref rgba, w, h)) = decoded {
                    extract_ocr_from_pixels_bounded(rgba, w, h, false, DEFAULT_OCR_TIMEOUT_MS)
                } else if img_path.is_file() {
                    extract_ocr_from_file_bounded(img_path, DEFAULT_OCR_TIMEOUT_MS)
                } else {
                    String::new()
                }
            } else {
                String::new()
            }
        }
    };

    let combined = format!("{} {} {}", window_title, app_class, extracted_text)
        .trim()
        .to_string();
    let vec_input = if combined.is_empty() {
        img_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("screen")
            .to_string()
    } else {
        combined
    };
    let blob = vec_to_blob(&text_to_vector(&vec_input));

    conn.execute(
        "INSERT INTO flow_screen_memory
         (timestamp, window_title, app_class, screenshot_path, thumbnail_path, extracted_text, embedding, frame_hash)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            ts,
            window_title,
            app_class,
            req.screenshot_path,
            thumb_path,
            extracted_text,
            blob,
            frame_hash
        ],
    )
    .map_err(|e| format!("Failed inserting screen capture: {}", e))?;

    let row_id = conn.last_insert_rowid();
    let report = IndexScreenReport {
        status: "indexed".to_string(),
        id: Some(row_id),
        timestamp: ts,
        screenshot_path: req.screenshot_path.to_string(),
        thumbnail_path: thumb_path,
        window_title,
        app_class,
        frame_hash,
        ocr_chars: extracted_text.chars().count(),
        extracted_text,
        reason: None,
    };

    if req.publish_bus {
        publish_screen_indexed_event(&report);
    }

    Ok(report)
}

pub fn index_drm_shm_frame(db_path: &Path, force: bool, publish_bus: bool) -> Result<IndexScreenReport, String> {
    let meta_path = Path::new(DRM_SHM_META_PATH);
    let pix_path = Path::new(DRM_SHM_PIXEL_PATH);
    if !meta_path.is_file() || !pix_path.is_file() {
        return Err("DRM SHM frame (/dev/shm/flowork_drm_latest.bgra/.json) not present".to_string());
    }

    let meta_raw = fs::read_to_string(meta_path).map_err(|e| e.to_string())?;
    let meta_val: serde_json::Value = serde_json::from_str(&meta_raw).map_err(|e| e.to_string())?;
    let w = meta_val.get("width").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
    let h = meta_val.get("height").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
    let bgra = fs::read(pix_path).map_err(|e| e.to_string())?;
    if w == 0 || h == 0 || bgra.len() < (w as usize) * (h as usize) * 4 {
        return Err("DRM SHM frame dimensions/size invalid".to_string());
    }

    let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    let win = fetch_active_window_meta();
    let window_title = if win.window_title.is_empty() {
        "Desktop".to_string()
    } else {
        win.window_title
    };
    let app_class = if win.app_class.is_empty() {
        "Desktop".to_string()
    } else {
        win.app_class
    };

    if let Some(pat) = should_exclude_screen_capture(&window_title, &app_class, DRM_SHM_PIXEL_PATH) {
        return Ok(IndexScreenReport {
            status: "skipped_privacy".to_string(),
            id: None,
            timestamp: ts,
            screenshot_path: DRM_SHM_PIXEL_PATH.to_string(),
            thumbnail_path: String::new(),
            window_title,
            app_class,
            frame_hash: String::new(),
            ocr_chars: 0,
            extracted_text: String::new(),
            reason: Some(format!("Privacy exclusion matched: {}", pat)),
        });
    }

    let conn = init_db(db_path)?;
    let frame_hash = rgba_to_dhash_hex(&bgra, w, h, true);
    if !force {
        if let Some(prev) = latest_frame_hash(&conn) {
            if let Some(dist) = dhash_hamming_distance(&prev, &frame_hash) {
                if dist <= DHASH_UNCHANGED_MAX_HAMMING {
                    return Ok(IndexScreenReport {
                        status: "skipped_unchanged".to_string(),
                        id: None,
                        timestamp: ts,
                        screenshot_path: DRM_SHM_PIXEL_PATH.to_string(),
                        thumbnail_path: String::new(),
                        window_title,
                        app_class,
                        frame_hash,
                        ocr_chars: 0,
                        extracted_text: String::new(),
                        reason: Some(format!("DRM keyframe delta {}/64 <= 3 bits (<5%)", dist)),
                    });
                }
            }
        }
    }

    let thumbs_dir = resolve_thumbs_dir();
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let thumb_file = thumbs_dir.join(format!("drm_{}_{}.webp", frame_hash, stamp));
    let thumb_path = if encode_4bpp_to_webp(&bgra, w, h, true, &thumb_file).is_ok() {
        thumb_file.to_string_lossy().into_owned()
    } else {
        String::new()
    };

    let extracted_text = extract_ocr_from_bgra_bounded(&bgra, w, h, DEFAULT_OCR_TIMEOUT_MS);
    let combined = format!("{} {} {}", window_title, app_class, extracted_text);
    let blob = vec_to_blob(&text_to_vector(&combined));
    let screenshot_ref = if !thumb_path.is_empty() {
        thumb_path.clone()
    } else {
        DRM_SHM_PIXEL_PATH.to_string()
    };

    conn.execute(
        "INSERT INTO flow_screen_memory
         (timestamp, window_title, app_class, screenshot_path, thumbnail_path, extracted_text, embedding, frame_hash)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            ts,
            window_title,
            app_class,
            screenshot_ref,
            thumb_path,
            extracted_text,
            blob,
            frame_hash
        ],
    )
    .map_err(|e| format!("Failed inserting DRM screen memory: {}", e))?;

    let row_id = conn.last_insert_rowid();
    let report = IndexScreenReport {
        status: "indexed".to_string(),
        id: Some(row_id),
        timestamp: ts,
        screenshot_path: screenshot_ref,
        thumbnail_path: thumb_path,
        window_title,
        app_class,
        frame_hash,
        ocr_chars: extracted_text.chars().count(),
        extracted_text,
        reason: None,
    };

    if publish_bus {
        publish_screen_indexed_event(&report);
    }

    Ok(report)
}

pub fn search_screen_memory(
    db_path: &Path,
    query: &str,
    limit: usize,
) -> Result<Vec<ScreenSearchResult>, String> {
    if query.trim().is_empty() || !db_path.is_file() {
        return Ok(Vec::new());
    }

    let conn = init_db(db_path)?;
    let max_out = limit.clamp(1, 50);
    let q_vec = text_to_vector(query);
    let q_words = tokenize_words(query);
    let q_lower = query.trim().to_ascii_lowercase();

    // 1. Collect FTS5 BM25 hits across all history
    let mut fts_scores: HashMap<i64, f64> = HashMap::new();
    let mut matched_ids = Vec::new();
    if let Some((fts_expr, _)) = build_safe_fts_query(query, true) {
        if let Ok(mut stmt) = conn.prepare(
            "SELECT m.id, bm25(flow_screen_fts, 3.0, 1.5, 4.0, 0.5) AS rank
             FROM flow_screen_fts f
             JOIN flow_screen_memory m ON f.rowid = m.id
             WHERE flow_screen_fts MATCH ?1
             ORDER BY rank ASC
             LIMIT 100",
        ) {
            if let Ok(rows) = stmt.query_map(params![fts_expr], |r| {
                Ok((r.get::<_, i64>(0)?, r.get::<_, f64>(1)?))
            }) {
                for row in rows.flatten() {
                    let bonus = (-row.1).clamp(0.15, 12.0) * 0.12;
                    fts_scores.insert(row.0, bonus);
                    matched_ids.push(row.0);
                }
            }
        }
    }

    // 2. Load recent 500 screen captures + any FTS hits beyond 500
    let mut seen_ids = HashSet::new();
    let mut scored = Vec::new();

    let mut score_row = |id: i64,
                         ts: String,
                         title: String,
                         app_class: String,
                         shot: String,
                         thumb: String,
                         text: String,
                         blob: Vec<u8>| {
        if !seen_ids.insert(id) {
            return;
        }
        let cos = blob_cosine_similarity(&q_vec, &blob);
        let fts_bonus = fts_scores.get(&id).copied().unwrap_or(0.0);

        let title_l = title.to_ascii_lowercase();
        let class_l = app_class.to_ascii_lowercase();
        let text_l = text.to_ascii_lowercase();

        let mut kw_bonus = 0.0f64;
        if text_l.contains(&q_lower) {
            kw_bonus += 0.55;
        }
        if title_l.contains(&q_lower) {
            kw_bonus += 0.40;
        }
        for w in &q_words {
            if w.len() < 3 {
                continue;
            }
            if text_l.contains(w.as_str()) {
                kw_bonus += 0.22;
            }
            if title_l.contains(w.as_str()) {
                kw_bonus += 0.18;
            }
            if class_l.contains(w.as_str()) {
                kw_bonus += 0.10;
            }
        }

        let sim = cos + fts_bonus + kw_bonus;
        if sim > 0.04 {
            scored.push(ScreenSearchResult {
                id,
                timestamp: ts,
                window_title: if title.is_empty() {
                    "Desktop".to_string()
                } else {
                    title
                },
                app_class,
                screenshot_path: shot,
                thumbnail_path: thumb,
                text,
                similarity: (sim * 10_000.0).round() / 10_000.0,
            });
        }
    };

    if !matched_ids.is_empty() {
        let mut stmt = conn
            .prepare(
                "SELECT id, timestamp, COALESCE(window_title,''), COALESCE(app_class,''),
                        COALESCE(screenshot_path,''), COALESCE(thumbnail_path,''),
                        COALESCE(extracted_text,''), embedding
                 FROM flow_screen_memory
                 WHERE id = ?1",
            )
            .map_err(|e| e.to_string())?;
        for mid in matched_ids {
            if let Ok(r) = stmt.query_row(params![mid], |r| {
                Ok((
                    r.get::<_, i64>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, String>(2)?,
                    r.get::<_, String>(3)?,
                    r.get::<_, String>(4)?,
                    r.get::<_, String>(5)?,
                    r.get::<_, String>(6)?,
                    r.get::<_, Vec<u8>>(7)?,
                ))
            }) {
                score_row(r.0, r.1, r.2, r.3, r.4, r.5, r.6, r.7);
            }
        }
    }

    let mut recent_stmt = conn
        .prepare(
            "SELECT id, timestamp, COALESCE(window_title,''), COALESCE(app_class,''),
                    COALESCE(screenshot_path,''), COALESCE(thumbnail_path,''),
                    COALESCE(extracted_text,''), embedding
             FROM flow_screen_memory
             ORDER BY id DESC
             LIMIT 500",
        )
        .map_err(|e| e.to_string())?;
    let rows = recent_stmt
        .query_map([], |r| {
            Ok((
                r.get::<_, i64>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, String>(3)?,
                r.get::<_, String>(4)?,
                r.get::<_, String>(5)?,
                r.get::<_, String>(6)?,
                r.get::<_, Vec<u8>>(7)?,
            ))
        })
        .map_err(|e| e.to_string())?;
    for r in rows.flatten() {
        score_row(r.0, r.1, r.2, r.3, r.4, r.5, r.6, r.7);
    }

    scored.sort_by(|a, b| {
        b.similarity
            .partial_cmp(&a.similarity)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    scored.truncate(max_out);
    Ok(scored)
}

pub fn recent_screen_memory(db_path: &Path, limit: usize) -> Result<Vec<ScreenSearchResult>, String> {
    if !db_path.is_file() {
        return Ok(Vec::new());
    }
    let conn = Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT id, timestamp, COALESCE(window_title,''), COALESCE(app_class,''),
                    COALESCE(screenshot_path,''), COALESCE(thumbnail_path,''),
                    COALESCE(extracted_text,'')
             FROM flow_screen_memory
             ORDER BY id DESC
             LIMIT ?1",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map(params![limit.clamp(1, 50) as i64], |r| {
            let wt: String = r.get(2)?;
            Ok(ScreenSearchResult {
                id: r.get(0)?,
                timestamp: r.get(1)?,
                window_title: if wt.is_empty() {
                    "Desktop".to_string()
                } else {
                    wt
                },
                app_class: r.get(3)?,
                screenshot_path: r.get(4)?,
                thumbnail_path: r.get(5)?,
                text: r.get(6)?,
                similarity: 1.0,
            })
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

pub fn compute_stats(db_path: &Path) -> Result<FlowfsStats, String> {
    let conn = init_db(db_path)?;
    let (total_documents, total_text_bytes): (i64, i64) = conn
        .query_row(
            "SELECT COUNT(*), COALESCE(SUM(size), 0) FROM flow_documents",
            [],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .unwrap_or((0, 0));
    let total_screen_entries: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_screen_memory", [], |r| r.get(0))
        .unwrap_or(0);
    let fts_documents_entries: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_documents_fts", [], |r| r.get(0))
        .unwrap_or(0);
    let fts_screen_entries: i64 = conn
        .query_row("SELECT COUNT(*) FROM flow_screen_fts", [], |r| r.get(0))
        .unwrap_or(0);

    let mut top_extensions = Vec::new();
    if let Ok(mut stmt) = conn.prepare(
        "SELECT extension, COUNT(*) as c FROM flow_documents GROUP BY extension ORDER BY c DESC LIMIT 8",
    ) {
        if let Ok(rows) = stmt.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?))) {
            for r in rows.flatten() {
                top_extensions.push(r);
            }
        }
    }

    let db_size_bytes = fs::metadata(db_path).map(|m| m.len()).unwrap_or(0);

    Ok(FlowfsStats {
        db_path: db_path.to_string_lossy().into_owned(),
        db_size_bytes,
        total_documents,
        total_text_bytes,
        total_screen_entries,
        fts_documents_entries,
        fts_screen_entries,
        top_extensions,
    })
}

// -----------------------------------------------------------------------------
// Unit Tests
// -----------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn temp_test_dir(tag: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(1);
        let dir = std::env::temp_dir().join(format!("flowfs_{}_{}_{}", tag, std::process::id(), stamp));
        let _ = fs::create_dir_all(&dir);
        dir
    }

    #[test]
    fn hybrid_document_indexing_and_fts5_search_sub30ms() {
        let dir = temp_test_dir("docs");
        let docs_root = dir.join("workspace");
        fs::create_dir_all(&docs_root).unwrap();
        fs::write(
            docs_root.join("landlock_guard.rs"),
            "# Flowork Landlock Guard\nEnforces 5-tier syscall capability sandbox across apps.\n",
        )
        .unwrap();
        fs::write(
            docs_root.join("earshot_synth.py"),
            "# Earshot Procedural Synthesizer\nGenerates shutter acoustic feedback for screen capture.\n",
        )
        .unwrap();

        let db_path = dir.join("flowfs.vec.db");
        let rep = index_files(&db_path, Some(&[docs_root.clone()])).expect("index files");
        assert_eq!(rep.new, 2);

        let start = Instant::now();
        let hits = semantic_search(&db_path, "Landlock capability sandbox", 5).expect("search");
        let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
        assert!(!hits.is_empty());
        assert_eq!(hits[0].filename, "landlock_guard.rs");
        assert!(elapsed_ms < 30.0, "search took {}ms", elapsed_ms);

        // Incremental pass detects unchanged & deletes stale
        fs::remove_file(docs_root.join("earshot_synth.py")).unwrap();
        let rep2 = index_files(&db_path, Some(&[docs_root])).expect("reindex");
        assert_eq!(rep2.unchanged, 1);
        assert_eq!(rep2.purged, 1);

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn privacy_exclusion_dhash_delta_and_ocr_screen_memory() {
        let dir = temp_test_dir("screen");
        let db_path = dir.join("flowfs.vec.db");
        std::env::set_var("FLOWORK_THUMBS_DIR", dir.join("thumbs"));

        // 1. Privacy filter blocks password managers & incognito
        assert!(should_exclude_screen_capture("Bitwarden Vault", "bitwarden", "/tmp/a.png").is_some());
        assert!(should_exclude_screen_capture("Secret - Incognito", "chrome", "/tmp/a.png").is_some());
        assert!(should_exclude_screen_capture("Editing .env config", "code", "/tmp/a.png").is_some());

        let priv_res = index_screen_capture(
            &db_path,
            ScreenCaptureRequest {
                screenshot_path: "/tmp/nonexistent.png",
                window_title: Some("KeePassXC - Passwords.kdbx"),
                app_class: Some("keepassxc"),
                explicit_text: Some("master password secret"),
                force: false,
                skip_ocr: true,
                publish_bus: false,
            },
        )
        .unwrap();
        assert_eq!(priv_res.status, "skipped_privacy");

        // 2. Render synthetic PNG containing ERR_FLOWORK_XY99 if ImageMagick `convert` exists
        let synth_png = dir.join("err_capture.png");
        let generated_png = std::process::Command::new("convert")
            .args([
                "-size",
                "640x160",
                "xc:white",
                "-fill",
                "black",
                "-pointsize",
                "36",
                "-gravity",
                "center",
                "-annotate",
                "+0+0",
                "ERR_FLOWORK_XY99",
                synth_png.to_string_lossy().as_ref(),
            ])
            .status()
            .map(|s| s.success())
            .unwrap_or(false);

        if generated_png && synth_png.is_file() {
            let idx = index_screen_capture(
                &db_path,
                ScreenCaptureRequest {
                    screenshot_path: synth_png.to_string_lossy().as_ref(),
                    window_title: Some("Alacritty Terminal"),
                    app_class: Some("Alacritty"),
                    explicit_text: None,
                    force: true,
                    skip_ocr: false,
                    publish_bus: false,
                },
            )
            .expect("ocr capture");
            assert_eq!(idx.status, "indexed");
            assert!(
                idx.thumbnail_path.ends_with(".webp") && Path::new(&idx.thumbnail_path).is_file(),
                "expected valid .webp thumbnail at {:?}",
                idx.thumbnail_path
            );
            assert!(
                idx.extracted_text.contains("ERR_FLOWORK_XY99"),
                "expected OCR to extract ERR_FLOWORK_XY99, got {:?}",
                idx.extracted_text
            );

            // Re-indexing identical image without --force skips due to <5% dHash diff
            let dup = index_screen_capture(
                &db_path,
                ScreenCaptureRequest {
                    screenshot_path: synth_png.to_string_lossy().as_ref(),
                    window_title: Some("Alacritty Terminal"),
                    app_class: Some("Alacritty"),
                    explicit_text: None,
                    force: false,
                    skip_ocr: false,
                    publish_bus: false,
                },
            )
            .expect("dup check");
            assert_eq!(dup.status, "skipped_unchanged");

            let start = Instant::now();
            let hits = search_screen_memory(&db_path, "ERR_FLOWORK_XY99", 5).expect("screen search");
            let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
            assert!(!hits.is_empty());
            assert!(hits[0].thumbnail_path.ends_with(".webp"));
            assert!(elapsed_ms < 30.0, "screen search took {}ms", elapsed_ms);
        }

        std::env::remove_var("FLOWORK_THUMBS_DIR");
        let _ = fs::remove_dir_all(&dir);
    }
}
