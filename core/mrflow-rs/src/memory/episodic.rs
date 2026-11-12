use crate::config::AppConfig;
use chrono::Utc;
use regex::Regex;
use rusqlite::{params, Connection, OpenFlags};
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

const EPISODIC_STOP_WORDS: &[&str] = &[
    "the", "and", "for", "with", "from", "check", "status", "test", "that", "this",
    "what", "when", "where", "which", "have", "been", "were", "will", "your", "into",
    "file", "path", "code", "make", "help", "task", "error", "fix", "issue", "yang",
    "untuk", "dari", "dengan", "pada", "ini", "itu", "bisa", "cara", "tolong", "coba",
    "buat", "bikin", "cek", "gimana", "bagaimana", "tolongin", "please", "show", "run",
];

#[derive(Debug, Clone)]
pub struct EpisodicMatch {
    #[allow(dead_code)]
    pub id: i64,
    pub category: String,
    pub source: String,
    pub problem: String,
    pub solution: String,
    #[allow(dead_code)]
    pub keywords: String,
    pub score: f64,
}

#[derive(Debug, Clone)]
pub struct NewEpisode<'a> {
    pub session_id: &'a str,
    pub category: &'a str,
    pub problem: &'a str,
    pub solution: &'a str,
    pub keywords: &'a str,
    pub source: &'a str,
    pub exit_code: i32,
}

pub fn episodic_db_path(config: &AppConfig) -> PathBuf {
    if let Ok(explicit) = std::env::var("FLOWORK_EPISODIC_DB") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    config.paths.flowork_root.join("history/episodic_memory.db")
}

pub fn flowfs_db_path(config: &AppConfig) -> PathBuf {
    if let Ok(explicit) = std::env::var("FLOWORK_FLOWFS_DB") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    config
        .paths
        .home_dir
        .join(".local")
        .join("share")
        .join("flowork")
        .join("flowfs.vec.db")
}

pub fn scrub_sensitive(home_dir: Option<&Path>, raw: &str) -> String {
    let mut cleaned = raw.to_string();
    if let Some(h) = home_dir {
        let hs = h.to_string_lossy();
        if !hs.is_empty() && hs != "/" {
            cleaned = cleaned.replace(hs.as_ref(), "$HOME");
        }
    }
    if let Some(h) = dirs::home_dir() {
        let hs = h.to_string_lossy();
        if !hs.is_empty() && hs != "/" {
            cleaned = cleaned.replace(hs.as_ref(), "$HOME");
        }
    }

    let patterns: &[(&str, &str)] = &[
        (r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_API_KEY]"),
        (r"\bsk-[A-Za-z0-9_-]{16,}", "[REDACTED_API_KEY]"),
        (r"\bgh[pous]_[A-Za-z0-9_]{16,}", "[REDACTED_GH_TOKEN]"),
        (r"\bgithub_pat_[A-Za-z0-9_]{20,}", "[REDACTED_GH_TOKEN]"),
        (r"(?i)\bBearer\s+[A-Za-z0-9._-]{16,}", "Bearer [REDACTED_TOKEN]"),
        (
            r#"(?i)(token|password|secret|api_key|apikey)\s*([:=])\s*['"]?([^\s'";,]{8,})['"]?"#,
            "$1$2[REDACTED]",
        ),
    ];
    for (pat, repl) in patterns {
        if let Ok(re) = Regex::new(pat) {
            cleaned = re.replace_all(&cleaned, *repl).into_owned();
        }
    }
    cleaned.trim().to_string()
}

pub fn compute_fingerprint(category: &str, problem: &str) -> String {
    let norm_cat = category
        .to_ascii_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ");
    let norm_prob: String = problem
        .to_ascii_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .chars()
        .take(240)
        .collect();
    let mut hasher = Sha256::new();
    hasher.update(format!("{}|{}", norm_cat, norm_prob).as_bytes());
    let digest = hasher.finalize();
    digest.iter().map(|b| format!("{:02x}", b)).collect()
}

pub fn extract_fts_tokens(text: &str) -> Vec<String> {
    let stop: HashSet<&str> = EPISODIC_STOP_WORDS.iter().copied().collect();
    let mut seen = HashSet::new();
    let mut out = Vec::new();
    for raw in text
        .to_ascii_lowercase()
        .split(|c: char| !(c.is_ascii_alphanumeric() || c == '_'))
    {
        if raw.len() < 3 || stop.contains(raw) || raw.chars().all(|c| c.is_ascii_digit()) {
            continue;
        }
        if seen.insert(raw.to_string()) {
            out.push(raw.to_string());
            if out.len() >= 12 {
                break;
            }
        }
    }
    out
}

fn ensure_schema(conn: &Connection) -> Result<(), String> {
    conn.execute_batch(
        "
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA busy_timeout=2000;
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TEXT,
            category TEXT,
            problem TEXT,
            solution TEXT,
            keywords TEXT,
            exit_code INTEGER DEFAULT 0,
            fingerprint TEXT,
            source TEXT DEFAULT 'manual',
            hit_count INTEGER DEFAULT 0
        );
        ",
    )
    .map_err(|e| e.to_string())?;

    let mut cols = HashSet::new();
    {
        let mut stmt = conn
            .prepare("PRAGMA table_info(episodes)")
            .map_err(|e| e.to_string())?;
        let mut rows = stmt.query([]).map_err(|e| e.to_string())?;
        while let Some(row) = rows.next().map_err(|e| e.to_string())? {
            if let Ok(name) = row.get::<_, String>(1) {
                cols.insert(name);
            }
        }
    }
    if !cols.contains("fingerprint") {
        let _ = conn.execute("ALTER TABLE episodes ADD COLUMN fingerprint TEXT", []);
    }
    if !cols.contains("source") {
        let _ = conn.execute(
            "ALTER TABLE episodes ADD COLUMN source TEXT DEFAULT 'manual'",
            [],
        );
    }
    if !cols.contains("hit_count") {
        let _ = conn.execute(
            "ALTER TABLE episodes ADD COLUMN hit_count INTEGER DEFAULT 0",
            [],
        );
    }

    conn.execute_batch(
        "
        CREATE UNIQUE INDEX IF NOT EXISTS idx_episodes_fingerprint
        ON episodes(fingerprint)
        WHERE fingerprint IS NOT NULL AND fingerprint != '';

        CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
            category,
            problem,
            solution,
            keywords,
            content='episodes',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
            INSERT INTO episodes_fts(rowid, category, problem, solution, keywords)
            VALUES (new.id, new.category, new.problem, new.solution, new.keywords);
        END;

        CREATE TRIGGER IF NOT EXISTS episodes_ad AFTER DELETE ON episodes BEGIN
            INSERT INTO episodes_fts(episodes_fts, rowid, category, problem, solution, keywords)
            VALUES('delete', old.id, old.category, old.problem, old.solution, old.keywords);
        END;

        CREATE TRIGGER IF NOT EXISTS episodes_au AFTER UPDATE OF category, problem, solution, keywords ON episodes BEGIN
            INSERT INTO episodes_fts(episodes_fts, rowid, category, problem, solution, keywords)
            VALUES('delete', old.id, old.category, old.problem, old.solution, old.keywords);
            INSERT INTO episodes_fts(rowid, category, problem, solution, keywords)
            VALUES (new.id, new.category, new.problem, new.solution, new.keywords);
        END;
        ",
    )
    .map_err(|e| e.to_string())?;

    Ok(())
}

/// Inserts or updates a verified experience episode (Exit Code 0 / recovery) with secret scrubbing and SHA-256 dedup.
pub fn crystallize_verified(config: &AppConfig, ep: NewEpisode<'_>) -> Result<(i64, bool), String> {
    let db_path = episodic_db_path(config);
    crystallize_verified_at(&db_path, Some(&config.paths.home_dir), ep)
}

pub fn crystallize_verified_at(
    db_path: &Path,
    home_dir: Option<&Path>,
    ep: NewEpisode<'_>,
) -> Result<(i64, bool), String> {
    if let Some(parent) = db_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;
    ensure_schema(&conn)?;

    let cat_clean: String = scrub_sensitive(home_dir, ep.category)
        .chars()
        .take(64)
        .collect();
    let cat_final = if cat_clean.is_empty() {
        "general".to_string()
    } else {
        cat_clean
    };
    let prob_clean: String = scrub_sensitive(home_dir, ep.problem)
        .chars()
        .take(600)
        .collect();
    let sol_clean: String = scrub_sensitive(home_dir, ep.solution)
        .chars()
        .take(1600)
        .collect();
    let kw_clean: String = scrub_sensitive(home_dir, ep.keywords)
        .chars()
        .take(400)
        .collect();

    if prob_clean.is_empty() || sol_clean.is_empty() {
        return Err("Episode problem and solution must be non-empty".to_string());
    }

    let fp = compute_fingerprint(&cat_final, &prob_clean);
    let ts = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();

    let existing_id: Option<i64> = conn
        .query_row(
            "SELECT id FROM episodes WHERE fingerprint = ?1 LIMIT 1",
            params![fp],
            |r| r.get(0),
        )
        .ok();

    if let Some(id) = existing_id {
        conn.execute(
            "UPDATE episodes SET session_id = ?1, timestamp = ?2, solution = ?3, keywords = ?4, source = ?5, exit_code = ?6 WHERE id = ?7",
            params![ep.session_id, ts, sol_clean, kw_clean, ep.source, ep.exit_code, id],
        )
        .map_err(|e| e.to_string())?;
        return Ok((id, false));
    }

    conn.execute(
        "INSERT INTO episodes (session_id, timestamp, category, problem, solution, keywords, exit_code, fingerprint, source, hit_count)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, 0)",
        params![
            ep.session_id,
            ts,
            cat_final,
            prob_clean,
            sol_clean,
            kw_clean,
            ep.exit_code,
            fp,
            ep.source
        ],
    )
    .map_err(|e| e.to_string())?;

    Ok((conn.last_insert_rowid(), true))
}

/// Queries SQLite FTS5 read-only for relevant past solutions with strict relevance & size gates.
#[allow(dead_code)]
pub fn query_episodes(
    config: &AppConfig,
    query: &str,
    max_results: usize,
) -> Result<Vec<EpisodicMatch>, String> {
    query_episodes_at(&episodic_db_path(config), query, max_results)
}

pub fn query_episodes_at(
    db_path: &Path,
    query: &str,
    max_results: usize,
) -> Result<Vec<EpisodicMatch>, String> {
    if !db_path.is_file() {
        return Ok(Vec::new());
    }
    let tokens = extract_fts_tokens(query);
    if tokens.is_empty() || (tokens.len() == 1 && tokens[0].len() < 5) {
        return Ok(Vec::new());
    }

    let conn = Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(|e| e.to_string())?;
    let _ = conn.busy_timeout(std::time::Duration::from_millis(500));

    let table_exists: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='episodes_fts'",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if table_exists == 0 {
        return Ok(Vec::new());
    }

    let fts_expr = tokens
        .iter()
        .map(|t| format!("\"{}\"", t))
        .collect::<Vec<_>>()
        .join(" OR ");
    let limit = max_results.clamp(1, 5) as i64;

    let mut stmt = conn
        .prepare(
            "SELECT e.id, e.category, COALESCE(e.source, 'manual'), e.problem, e.solution, e.keywords,
                    bm25(episodes_fts, 1.0, 4.0, 2.5, 3.0) AS score
             FROM episodes_fts f
             JOIN episodes e ON f.rowid = e.id
             WHERE episodes_fts MATCH ?1 AND e.exit_code = 0
             ORDER BY score ASC
             LIMIT ?2",
        )
        .map_err(|e| e.to_string())?;

    let rows = stmt
        .query_map(params![fts_expr, limit], |r| {
            Ok(EpisodicMatch {
                id: r.get(0)?,
                category: r.get(1)?,
                source: r.get(2)?,
                problem: r.get(3)?,
                solution: r.get(4)?,
                keywords: r.get(5)?,
                score: r.get(6)?,
            })
        })
        .map_err(|e| e.to_string())?;

    let mut out = Vec::new();
    for item in rows.flatten() {
        let haystack = format!(
            "{} {} {}",
            item.problem.to_ascii_lowercase(),
            item.keywords.to_ascii_lowercase(),
            item.category.to_ascii_lowercase()
        );
        let overlap = tokens
            .iter()
            .filter(|t| haystack.contains(t.as_str()))
            .count();

        // Zero-bloat precision gate: require real multi-term match or high BM25 confidence
        let confident = if tokens.len() >= 2 {
            overlap >= 2 || item.score <= -2.5
        } else {
            overlap >= 1 && item.score <= -1.2
        };

        if confident {
            out.push(item);
        }
    }
    Ok(out)
}

fn clip_single_line(s: &str, max_chars: usize) -> String {
    let flat = s
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    let count = flat.chars().count();
    if count <= max_chars {
        flat
    } else {
        let cut: String = flat.chars().take(max_chars.saturating_sub(3)).collect();
        format!("{}...", cut.trim_end())
    }
}

fn screen_prompt_tokens(query: &str) -> (Vec<String>, bool) {
    let low = query.to_ascii_lowercase();
    let visual_cue = ["screen", "layar", "screenshot", "tadi", "terminal", "jendela", "window", "muncul"]
        .iter()
        .any(|k| low.contains(k));
    let generic_visual_words: HashSet<&str> = [
        "the", "and", "for", "with", "from", "what", "when", "where", "which", "have", "been",
        "yang", "untuk", "dari", "dengan", "pada", "ini", "itu", "bisa", "apa", "gimana",
        "tadi", "tolong", "coba", "lihat", "screen", "layar", "screenshot",
    ]
    .into_iter()
    .collect();

    let mut seen = HashSet::new();
    let mut out = Vec::new();
    for raw in low.split(|c: char| !(c.is_ascii_alphanumeric() || c == '_')) {
        if raw.len() < 3 || generic_visual_words.contains(raw) || raw.chars().all(|c| c.is_ascii_digit()) {
            continue;
        }
        if seen.insert(raw.to_string()) {
            out.push(raw.to_string());
            if out.len() >= 10 {
                break;
            }
        }
    }
    (out, visual_cue)
}

pub fn recall_screen_jit_at(
    flowfs_db: &Path,
    home_dir: Option<&Path>,
    user_prompt: &str,
    max_results: usize,
    max_total_chars: usize,
) -> Option<String> {
    if !flowfs_db.is_file() || max_total_chars < 140 {
        return None;
    }
    let (tokens, visual_cue) = screen_prompt_tokens(user_prompt);
    if tokens.is_empty() && !visual_cue {
        return None;
    }

    let conn = Connection::open_with_flags(
        flowfs_db,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .ok()?;
    let _ = conn.busy_timeout(std::time::Duration::from_millis(300));

    let fts_exists: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='flow_screen_fts'",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if fts_exists == 0 {
        return None;
    }

    let limit = max_results.clamp(1, 3) as i64;
    let mut hits: Vec<(String, String, String, String)> = Vec::new();

    if !tokens.is_empty() {
        let fts_expr = tokens
            .iter()
            .map(|t| {
                if t.len() >= 4 {
                    format!("\"{}\"*", t)
                } else {
                    format!("\"{}\"", t)
                }
            })
            .collect::<Vec<_>>()
            .join(" OR ");

        if let Ok(mut stmt) = conn.prepare(
            "SELECT m.timestamp, COALESCE(m.window_title,'Desktop'),
                    COALESCE(m.screenshot_path,''), COALESCE(m.extracted_text,''),
                    bm25(flow_screen_fts, 3.0, 1.5, 4.0, 0.5) AS rank
             FROM flow_screen_fts f
             JOIN flow_screen_memory m ON f.rowid = m.id
             WHERE flow_screen_fts MATCH ?1
             ORDER BY rank ASC, m.id DESC
             LIMIT ?2",
        ) {
            if let Ok(rows) = stmt.query_map(params![fts_expr, limit], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, String>(2)?,
                    r.get::<_, String>(3)?,
                    r.get::<_, f64>(4)?,
                ))
            }) {
                for (ts, wt, shot, txt, rank) in rows.flatten() {
                    let hay = format!("{} {}", wt.to_ascii_lowercase(), txt.to_ascii_lowercase());
                    let overlap = tokens.iter().filter(|t| hay.contains(t.as_str())).count();
                    if overlap >= 2 || (overlap >= 1 && (visual_cue || rank <= -1.2)) {
                        hits.push((ts, wt, shot, txt));
                    }
                }
            }
        }
    }

    if hits.is_empty() && visual_cue {
        if let Ok(mut stmt) = conn.prepare(
            "SELECT timestamp, COALESCE(window_title,'Desktop'),
                    COALESCE(screenshot_path,''), COALESCE(extracted_text,'')
             FROM flow_screen_memory
             WHERE LENGTH(COALESCE(extracted_text,'')) > 8
             ORDER BY id DESC
             LIMIT ?1",
        ) {
            if let Ok(rows) = stmt.query_map(params![limit], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, String>(2)?,
                    r.get::<_, String>(3)?,
                ))
            }) {
                for row in rows.flatten() {
                    hits.push(row);
                }
            }
        }
    }

    if hits.is_empty() {
        return None;
    }

    let mut lines = vec![
        "<SCREEN_MEMORY_JIT source=\"flowfs_ocr\">".to_string(),
        "Recent screen OCR captures matching context:".to_string(),
    ];
    let mut used: usize = lines.iter().map(|l| l.len() + 1).sum();

    for (idx, (ts, wt, shot, txt)) in hits.into_iter().take(max_results.clamp(1, 3)).enumerate() {
        let clean_wt = clip_single_line(&scrub_sensitive(home_dir, &wt), 64);
        let clean_txt = clip_single_line(&scrub_sensitive(home_dir, &txt), 240);
        let entry = format!(
            "{}. [{}] {} ({}) => OCR: {}",
            idx + 1,
            ts,
            clean_wt,
            shot,
            clean_txt
        );
        if used + entry.len() + 26 > max_total_chars {
            break;
        }
        used += entry.len() + 1;
        lines.push(entry);
    }

    if lines.len() <= 2 {
        return None;
    }
    lines.push("</SCREEN_MEMORY_JIT>".to_string());
    Some(lines.join("\n"))
}

/// Formats bounded Just-In-Time episodic + FlowFS visual screen memory recall (zero bloat).
pub fn recall_jit(
    config: &AppConfig,
    user_prompt: &str,
    max_results: usize,
    max_total_chars: usize,
) -> Option<String> {
    let ep = recall_jit_at(&episodic_db_path(config), user_prompt, max_results, max_total_chars);
    let ep_len = ep.as_ref().map(|s| s.len()).unwrap_or(0);
    let screen_budget = max_total_chars.saturating_sub(ep_len).min(640);
    let scr = if screen_budget >= 180 {
        recall_screen_jit_at(
            &flowfs_db_path(config),
            Some(&config.paths.home_dir),
            user_prompt,
            max_results.min(2),
            screen_budget,
        )
    } else {
        None
    };

    match (ep, scr) {
        (Some(a), Some(b)) => Some(format!("{}\n{}", a, b)),
        (Some(a), None) => Some(a),
        (None, Some(b)) => Some(b),
        (None, None) => None,
    }
}

pub fn recall_jit_at(
    db_path: &Path,
    user_prompt: &str,
    max_results: usize,
    max_total_chars: usize,
) -> Option<String> {
    let matches = query_episodes_at(db_path, user_prompt, max_results.clamp(1, 3)).ok()?;
    if matches.is_empty() {
        return None;
    }

    let mut lines = vec![
        "<EPISODIC_JIT_MEMORY source=\"sqlite_fts5\">".to_string(),
        "Relevant verified solutions recalled from past Flowork OS executions:".to_string(),
    ];
    let mut used_chars: usize = lines.iter().map(|l| l.len() + 1).sum();

    for (idx, m) in matches.into_iter().take(max_results.clamp(1, 3)).enumerate() {
        let prob = clip_single_line(&m.problem, 140);
        let sol = clip_single_line(&m.solution, 280);
        let entry = format!(
            "{}. [{}|{}] Problem: {} => Verified Fix: {}",
            idx + 1,
            m.category,
            m.source,
            prob,
            sol
        );
        if used_chars + entry.len() + 32 > max_total_chars {
            break;
        }
        used_chars += entry.len() + 1;
        lines.push(entry);
    }

    if lines.len() <= 2 {
        return None;
    }
    lines.push("</EPISODIC_JIT_MEMORY>".to_string());
    Some(lines.join("\n"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scrub_and_jit_recall_respect_dedup_and_bounds() {
        let tmp_dir = std::env::temp_dir().join(format!("mrflow_ep_test_{}", std::process::id()));
        let _ = fs::create_dir_all(&tmp_dir);
        let db_file = tmp_dir.join("episodic_memory.db");
        let _ = fs::remove_file(&db_file);

        let (id1, new1) = crystallize_verified_at(
            &db_file,
            None,
            NewEpisode {
                session_id: "sess_1",
                category: "recovery",
                problem: "flowork-neural-bus pipeline failed timeout with token AIzaSyFakeSecretKey1234567890",
                solution: "Fixed stage timeout in /opt/floworkos/bin/flowork-neural-bus and validated JSON output.",
                keywords: "flowork-neural-bus, pipeline, timeout",
                source: "test_suite",
                exit_code: 0,
            },
        )
        .expect("insert 1");
        assert!(new1);

        // Identical problem should deduplicate cleanly
        let (id2, new2) = crystallize_verified_at(
            &db_file,
            None,
            NewEpisode {
                session_id: "sess_2",
                category: "recovery",
                problem: "flowork-neural-bus pipeline failed timeout with token AIzaSyFakeSecretKey1234567890",
                solution: "Updated solution with 300s pipeline stage cap.",
                keywords: "flowork-neural-bus, pipeline, timeout, stages",
                source: "test_suite",
                exit_code: 0,
            },
        )
        .expect("dedup update");
        assert!(!new2);
        assert_eq!(id1, id2);

        // Trivial prompt must NOT bloat context
        assert!(recall_jit_at(&db_file, "hello", 3, 1200).is_none());

        // Matching query recalls redacted entry within char bound
        let recalled = recall_jit_at(&db_file, "fix flowork-neural-bus pipeline timeout", 3, 1200)
            .expect("should recall matching episode");
        assert!(recalled.contains("<EPISODIC_JIT_MEMORY"));
        assert!(recalled.contains("300s pipeline stage cap"));
        assert!(!recalled.contains("AIzaSyFakeSecretKey"));
        assert!(recalled.contains("[REDACTED_API_KEY]"));
        assert!(recalled.len() <= 1200);

        // Screen OCR JIT memory recall via flow_screen_fts
        let scr_db = tmp_dir.join("flowfs.vec.db");
        let _ = fs::remove_file(&scr_db);
        let conn = Connection::open(&scr_db).unwrap();
        conn.execute_batch(
            "
            CREATE TABLE flow_screen_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                window_title TEXT,
                app_class TEXT,
                screenshot_path TEXT,
                thumbnail_path TEXT,
                extracted_text TEXT,
                embedding BLOB NOT NULL
            );
            CREATE VIRTUAL TABLE flow_screen_fts USING fts5(
                window_title, app_class, extracted_text, screenshot_path,
                content='flow_screen_memory', content_rowid='id', tokenize='porter unicode61'
            );
            CREATE TRIGGER flow_screen_ai AFTER INSERT ON flow_screen_memory BEGIN
                INSERT INTO flow_screen_fts(rowid, window_title, app_class, extracted_text, screenshot_path)
                VALUES (new.id, new.window_title, new.app_class, new.extracted_text, new.screenshot_path);
            END;
            ",
        )
        .unwrap();
        conn.execute(
            "INSERT INTO flow_screen_memory (timestamp, window_title, app_class, screenshot_path, thumbnail_path, extracted_text, embedding)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                "2026-11-12 15:20:00",
                "Alacritty Terminal",
                "Alacritty",
                "/opt/floworkos/screenshots/err.png",
                "/opt/floworkos/screenshots/thumbs/err.webp",
                "panic at ERR_FLOWORK_XY99 linker failure",
                vec![0u8; 512]
            ],
        )
        .unwrap();
        drop(conn);

        assert!(recall_screen_jit_at(&scr_db, None, "hello world", 2, 600).is_none());
        let scr_hit = recall_screen_jit_at(&scr_db, None, "tadi error apa di terminal ERR_FLOWORK_XY99", 2, 600)
            .expect("should recall matching screen capture");
        assert!(scr_hit.contains("<SCREEN_MEMORY_JIT"));
        assert!(scr_hit.contains("ERR_FLOWORK_XY99"));
        assert!(scr_hit.len() <= 600);

        let _ = fs::remove_dir_all(&tmp_dir);
    }
}
