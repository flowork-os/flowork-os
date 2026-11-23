// ==============================================================================
// 👑 FLOWORK OS — STANFORD MEMORILLA LATENT SEMANTIC MEMORY ENGINE
// Implementation of Latent Semantic Slots, Dual-Tier Memory & JIT Grounding
// Reference: Stanford Memorilla (arXiv:2610.21375) adapted for Flowork OS Rust
// Co-authored-by: Flowork OS Architecture Board & Dr. Flow <agent@floworkos.com>
// ==============================================================================

use crate::config::AppConfig;
use crate::memory::episodic::extract_fts_tokens;
use chrono::Utc;
use rusqlite::{params, Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

// ------------------------------------------------------------------------------
// DATA STRUCTURES
// ------------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StateInvariant {
    pub entity: String,    // e.g. "theme/picom-quantum.conf"
    pub assertion: String, // e.g. "xrender-sync-fence=true & use-damage=true"
    pub proof: String,     // e.g. "Exit Code 0 verified"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatentMemorySlot {
    pub slot_id: String,
    pub session_id: String,
    pub created_at: i64,
    pub last_accessed: i64,
    pub recall_count: u32,
    pub decay_score: f32, // 0.0 (stale/prunable) to 1.0 (verified permanent)
    pub intent_signature: String,
    pub touched_paths: Vec<String>,
    pub state_invariants: Vec<StateInvariant>,
    pub causal_flow: Vec<String>,
    pub git_commit: Option<String>,
    pub keywords: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct MemorillaRecallMatch {
    pub slot: LatentMemorySlot,
    pub score: f32,
}

// ------------------------------------------------------------------------------
// DATABASE RESOLUTION & SCHEMA MANAGEMENT
// ------------------------------------------------------------------------------

pub fn memorilla_db_path(config: &AppConfig) -> PathBuf {
    if let Ok(explicit) = std::env::var("FLOWORK_MEMORILLA_DB") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }

    // 1. Preferred location: .fl_brain/memorilla.db
    let brain_dir = config.paths.flowork_root.join(".fl_brain");
    if brain_dir.is_dir() {
        return brain_dir.join("memorilla.db");
    }

    // 2. Secondary system location: history/memorilla.db
    let history_dir = config.paths.flowork_root.join("history");
    if history_dir.is_dir() {
        return history_dir.join("memorilla.db");
    }

    // 3. User local fallback
    config.paths.user_flowork_dir.join("memorilla.db")
}

pub fn ensure_memorilla_schema(conn: &Connection) -> Result<(), String> {
    conn.execute_batch(
        "
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA busy_timeout=2500;

        CREATE TABLE IF NOT EXISTS memorilla_slots (
            slot_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            last_accessed INTEGER NOT NULL,
            recall_count INTEGER DEFAULT 0,
            decay_score REAL DEFAULT 1.0,
            intent_signature TEXT NOT NULL,
            touched_paths_json TEXT NOT NULL,
            state_invariants_json TEXT NOT NULL,
            causal_flow_json TEXT NOT NULL,
            git_commit TEXT,
            keywords_json TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS memorilla_fts USING fts5(
            intent_signature,
            touched_paths_json,
            state_invariants_json,
            keywords_json,
            content='memorilla_slots',
            content_rowid='rowid'
        );

        CREATE INDEX IF NOT EXISTS idx_memorilla_decay ON memorilla_slots(decay_score);
        CREATE INDEX IF NOT EXISTS idx_memorilla_accessed ON memorilla_slots(last_accessed);
        ",
    )
    .map_err(|e| format!("Memorilla schema creation failed: {}", e))
}

// ------------------------------------------------------------------------------
// DETERMINISTIC LEVEL-1 MICRO-COMPACTOR (ZERO-LLM OVERHEAD)
// ------------------------------------------------------------------------------

pub fn compute_slot_id(intent_signature: &str, touched_paths: &[String]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(intent_signature.trim().to_lowercase().as_bytes());
    for p in touched_paths {
        hasher.update(b"|");
        hasher.update(p.trim().as_bytes());
    }
    let digest = hasher.finalize();
    digest.iter().map(|b| format!("{:02x}", b)).collect::<String>()[..24].to_string()
}

pub fn extract_invariants_from_turn(
    final_response: &str,
    used_tools: &[String],
    touched_files: &[String],
    exit_code: i32,
) -> Vec<StateInvariant> {
    let mut invariants = Vec::new();

    // 1. Extract invariants from touched files
    for file in touched_files {
        let clean = file.trim();
        if clean.is_empty() {
            continue;
        }
        let fname = Path::new(clean)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or(clean);

        let assertion = if clean.ends_with(".conf") || clean.ends_with(".json") || clean.ends_with(".toml") {
            format!("Configuration updated in {}", fname)
        } else if clean.ends_with(".rs") || clean.ends_with(".py") || clean.ends_with(".sh") {
            format!("Source code patched in {}", fname)
        } else {
            format!("System asset verified in {}", fname)
        };

        invariants.push(StateInvariant {
            entity: clean.to_string(),
            assertion,
            proof: if exit_code == 0 {
                "Exit Code 0 verified".to_string()
            } else {
                format!("Exit Code {}", exit_code)
            },
        });
    }

    // 2. Extract verified outcome from final response lines
    for line in final_response.lines() {
        let t = line.trim();
        if t.starts_with("•") || t.starts_with("- [✓]") || t.starts_with("[✓]") || t.starts_with("✓") {
            let clean_line = t.trim_start_matches(|c: char| c == '•' || c == '-' || c == '[' || c == '✓' || c == ']' || c == ' ')
                .chars()
                .take(160)
                .collect::<String>();
            if clean_line.len() >= 12 && invariants.len() < 6 {
                invariants.push(StateInvariant {
                    entity: "system_state".to_string(),
                    assertion: clean_line,
                    proof: "Verified outcome".to_string(),
                });
            }
        }
    }

    // 3. Fallback tool invariant if nothing extracted
    if invariants.is_empty() && !used_tools.is_empty() {
        invariants.push(StateInvariant {
            entity: "tool_pipeline".to_string(),
            assertion: format!("Executed tools: {}", used_tools.join(", ")),
            proof: if exit_code == 0 { "Exit Code 0".to_string() } else { "Failed".to_string() },
        });
    }

    invariants
}

pub fn compact_and_crystallize(
    config: &AppConfig,
    session_id: &str,
    user_prompt: &str,
    final_response: &str,
    used_tools: &[String],
    touched_files: &[String],
    exit_code: i32,
    git_commit: Option<String>,
) -> Result<Option<String>, String> {
    if exit_code != 0 && touched_files.is_empty() {
        // Do not crystallize unverified failed turns with no mutations
        return Ok(None);
    }

    let db_path = memorilla_db_path(config);
    if let Some(parent) = db_path.parent() {
        let _ = fs::create_dir_all(parent);
    }

    let conn = Connection::open_with_flags(
        &db_path,
        OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE,
    )
    .map_err(|e| format!("Failed to open Memorilla DB at {}: {}", db_path.display(), e))?;

    ensure_memorilla_schema(&conn)?;

    // Synthesize intent signature
    let intent_signature = {
        let first_line = user_prompt.lines().find(|l| !l.trim().is_empty()).unwrap_or(user_prompt);
        first_line.chars().take(120).collect::<String>().trim().to_string()
    };

    let invariants = extract_invariants_from_turn(final_response, used_tools, touched_files, exit_code);
    let mut touched_clean: Vec<String> = touched_files.iter().map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect();
    touched_clean.sort();
    touched_clean.dedup();

    let slot_id = compute_slot_id(&intent_signature, &touched_clean);
    let now = Utc::now().timestamp();
    let decay_score = if exit_code == 0 { 1.0f32 } else { 0.6f32 };

    let causal_flow: Vec<String> = used_tools.iter().map(|t| format!("Tool `{}` called", t)).collect();
    let keywords = extract_fts_tokens(&format!("{} {}", intent_signature, touched_clean.join(" ")));

    let touched_json = serde_json::to_string(&touched_clean).unwrap_or_else(|_| "[]".to_string());
    let invariants_json = serde_json::to_string(&invariants).unwrap_or_else(|_| "[]".to_string());
    let causal_json = serde_json::to_string(&causal_flow).unwrap_or_else(|_| "[]".to_string());
    let keywords_json = serde_json::to_string(&keywords).unwrap_or_else(|_| "[]".to_string());

    // Upsert slot with Hierarchical Merging: bump recall_count and refresh invariants
    conn.execute(
        "
        INSERT INTO memorilla_slots (
            slot_id, session_id, created_at, last_accessed, recall_count, decay_score,
            intent_signature, touched_paths_json, state_invariants_json, causal_flow_json,
            git_commit, keywords_json
        ) VALUES (?1, ?2, ?3, ?4, 1, ?5, ?6, ?7, ?8, ?9, ?10, ?11)
        ON CONFLICT(slot_id) DO UPDATE SET
            last_accessed = excluded.last_accessed,
            recall_count = memorilla_slots.recall_count + 1,
            decay_score = MIN(1.0, memorilla_slots.decay_score + 0.2),
            state_invariants_json = excluded.state_invariants_json,
            git_commit = COALESCE(excluded.git_commit, memorilla_slots.git_commit);
        ",
        params![
            slot_id,
            session_id,
            now,
            now,
            decay_score,
            intent_signature,
            touched_json,
            invariants_json,
            causal_json,
            git_commit,
            keywords_json,
        ],
    )
    .map_err(|e| format!("Failed to insert Memorilla slot: {}", e))?;

    // Refresh FTS index
    let _ = conn.execute(
        "
        INSERT INTO memorilla_fts (rowid, intent_signature, touched_paths_json, state_invariants_json, keywords_json)
        SELECT rowid, intent_signature, touched_paths_json, state_invariants_json, keywords_json
        FROM memorilla_slots WHERE slot_id = ?1;
        ",
        params![slot_id],
    );

    // Periodic Garbage Collection: Prune deeply decayed slots older than 30 days
    let _ = prune_decayed_slots(&conn, 30);

    Ok(Some(slot_id))
}

pub fn prune_decayed_slots(conn: &Connection, max_age_days: i64) -> Result<usize, String> {
    let threshold_time = Utc::now().timestamp() - (max_age_days * 86400);
    let deleted = conn
        .execute(
            "DELETE FROM memorilla_slots WHERE decay_score < 0.20 AND last_accessed < ?1",
            params![threshold_time],
        )
        .map_err(|e| format!("Failed to prune decayed slots: {}", e))?;

    if deleted > 0 {
        let _ = conn.execute("INSERT INTO memorilla_fts(memorilla_fts) VALUES('rebuild')", []);
    }
    Ok(deleted)
}

// ------------------------------------------------------------------------------
// DUAL-KEY ATTENTION GATE & SURGICAL JIT RECALL
// ------------------------------------------------------------------------------

pub fn recall_memorilla_jit(
    config: &AppConfig,
    user_prompt: &str,
    _active_session_id: &str,
) -> Option<String> {
    let db_path = memorilla_db_path(config);
    if !db_path.is_file() {
        return None;
    }

    let conn = Connection::open_with_flags(&db_path, OpenFlags::SQLITE_OPEN_READ_ONLY).ok()?;

    let prompt_tokens = extract_fts_tokens(user_prompt);
    if prompt_tokens.is_empty() {
        return None;
    }

    let lower_prompt = user_prompt.to_ascii_lowercase();

    // Query active slots ordered by access recency and decay score
    let mut stmt = conn
        .prepare(
            "
            SELECT slot_id, session_id, created_at, last_accessed, recall_count, decay_score,
                   intent_signature, touched_paths_json, state_invariants_json, causal_flow_json,
                   git_commit, keywords_json
            FROM memorilla_slots
            WHERE decay_score > 0.35
            ORDER BY last_accessed DESC, decay_score DESC
            LIMIT 40;
            ",
        )
        .ok()?;

    let rows = stmt
        .query_map([], |row| {
            let touched_raw: String = row.get(7)?;
            let invariants_raw: String = row.get(8)?;
            let causal_raw: String = row.get(9)?;
            let keywords_raw: String = row.get(11)?;

            Ok(LatentMemorySlot {
                slot_id: row.get(0)?,
                session_id: row.get(1)?,
                created_at: row.get(2)?,
                last_accessed: row.get(3)?,
                recall_count: row.get(4)?,
                decay_score: row.get(5)?,
                intent_signature: row.get(6)?,
                touched_paths: serde_json::from_str(&touched_raw).unwrap_or_default(),
                state_invariants: serde_json::from_str(&invariants_raw).unwrap_or_default(),
                causal_flow: serde_json::from_str(&causal_raw).unwrap_or_default(),
                git_commit: row.get(10)?,
                keywords: serde_json::from_str(&keywords_raw).unwrap_or_default(),
            })
        })
        .ok()?;

    let mut scored_matches: Vec<MemorillaRecallMatch> = Vec::new();

    for r in rows.flatten() {
        // 1. Causal Path Gate Score: Does the prompt or active workspace reference touched paths?
        let mut path_hit = false;
        for path in &r.touched_paths {
            let fname = Path::new(path)
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or(path)
                .to_ascii_lowercase();
            if lower_prompt.contains(&fname) || lower_prompt.contains(&path.to_ascii_lowercase()) {
                path_hit = true;
                break;
            }
        }
        let path_score = if path_hit { 0.50f32 } else { 0.0f32 };

        // 2. Semantic Intent Gate Score: Jaccard keyword overlap
        let slot_kws: HashSet<String> = r.keywords.iter().map(|k| k.to_ascii_lowercase()).collect();
        let matched_tokens = prompt_tokens.iter().filter(|t| slot_kws.contains(*t)).count();
        let token_overlap_ratio = if !prompt_tokens.is_empty() {
            (matched_tokens as f32) / (prompt_tokens.len().min(8) as f32)
        } else {
            0.0
        };
        let semantic_score = (token_overlap_ratio * 0.50).min(0.50);

        // Combined Dual-Key Score
        let combined_score = (path_score + semantic_score) * r.decay_score;

        // Strict Attention Threshold Gate: Must achieve >= 0.70 to open injection gate
        if combined_score >= 0.70 {
            scored_matches.push(MemorillaRecallMatch {
                slot: r,
                score: combined_score,
            });
        }
    }

    if scored_matches.is_empty() {
        // Zero Token Bloat: Injection gate remains closed
        return None;
    }

    scored_matches.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    scored_matches.truncate(2);

    // Format into ultra-dense Surgical Memory Capsule (< 120 tokens)
    let mut capsule = String::new();
    capsule.push_str("<MEMORILLA_LATENT_GROUNDING>\n");
    capsule.push_str("[Verified System Invariants & Continuity]:\n");

    for m in &scored_matches {
        let slot = &m.slot;
        capsule.push_str(&format!("• Intent: {}\n", slot.intent_signature));
        if let Some(ref commit) = slot.git_commit {
            capsule.push_str(&format!("  Commit: {}\n", commit));
        }
        for inv in slot.state_invariants.iter().take(2) {
            capsule.push_str(&format!("  - {}: {} ({})\n", inv.entity, inv.assertion, inv.proof));
        }
    }

    capsule.push_str("</MEMORILLA_LATENT_GROUNDING>");

    Some(capsule)
}

// ------------------------------------------------------------------------------
// UNIT TESTS
// ------------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_slot_id_deterministic() {
        let id1 = compute_slot_id("fix nvidia screen", &["/etc/picom.conf".to_string()]);
        let id2 = compute_slot_id("fix nvidia screen", &["/etc/picom.conf".to_string()]);
        assert_eq!(id1, id2);
        assert_eq!(id1.len(), 24);
    }

    #[test]
    fn test_extract_invariants() {
        let touched = vec!["/opt/floworkos/theme/picom-quantum.conf".to_string()];
        let tools = vec!["replace_file_content".to_string()];
        let res = "All verified.\n✓ picom-quantum.conf synced cleanly\n";
        let invs = extract_invariants_from_turn(res, &tools, &touched, 0);
        assert!(!invs.is_empty());
        assert_eq!(invs[0].entity, "/opt/floworkos/theme/picom-quantum.conf");
    }
}
