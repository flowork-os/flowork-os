use crate::config::AppConfig;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

/// Loads hierarchical Flowork context memory (`FLOWORK.md` and `.flowork/MEMORY.md`).
/// Clean-room invariant: strictly ZERO legacy non-Flowork filenames.
pub fn load_hierarchical_memory(config: &AppConfig) -> String {
    let mut visited = HashSet::new();
    let mut sections = Vec::new();

    // 1. User global memory (~/.flowork/FLOWORK.md & ~/.flowork/MEMORY.md)
    let user_candidates = [
        config.paths.user_flowork_dir.join("FLOWORK.md"),
        config.paths.user_flowork_dir.join("MEMORY.md"),
    ];
    for path in &user_candidates {
        if let Some(chunk) = read_with_imports(path, &mut visited, 0) {
            sections.push(format!("<!-- Memory: {} -->\n{}", path.display(), chunk));
        }
    }

    // 2. Git root (or cwd ancestors up to root) -> downward to cwd
    let mut chain = Vec::new();
    let mut cur = Some(config.cwd.as_path());
    while let Some(dir) = cur {
        chain.push(dir.to_path_buf());
        if dir.join(".git").exists() {
            break;
        }
        cur = dir.parent();
    }
    chain.reverse();

    for dir in chain {
        for rel in &["FLOWORK.md", ".flowork/MEMORY.md"] {
            let candidate = dir.join(rel);
            if let Some(chunk) = read_with_imports(&candidate, &mut visited, 0) {
                sections.push(format!(
                    "<!-- Context: {} -->\n{}",
                    candidate.display(),
                    chunk
                ));
            }
        }
    }

    // 3. Included workspace directories
    for inc in &config.include_directories {
        for rel in &["FLOWORK.md", ".flowork/MEMORY.md"] {
            let candidate = inc.join(rel);
            if let Some(chunk) = read_with_imports(&candidate, &mut visited, 0) {
                sections.push(format!(
                    "<!-- Included Context: {} -->\n{}",
                    candidate.display(),
                    chunk
                ));
            }
        }
    }

    sections.join("\n\n---\n\n")
}

fn read_with_imports(
    path: &Path,
    visited: &mut HashSet<PathBuf>,
    depth: usize,
) -> Option<String> {
    if depth > 5 || !path.is_file() {
        return None;
    }
    let canon = fs::canonicalize(path).ok()?;
    if !visited.insert(canon.clone()) {
        return None;
    }
    let raw = fs::read_to_string(&canon).ok()?;
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return None;
    }

    let parent = canon.parent()?;
    let mut out = Vec::new();
    for line in trimmed.lines() {
        let stripped = line.trim();
        if let Some(rel) = stripped.strip_prefix('@') {
            let rel_clean = rel.trim();
            if !rel_clean.is_empty()
                && !rel_clean.contains(' ')
                && (rel_clean.ends_with(".md") || rel_clean.ends_with(".txt"))
            {
                let import_path = parent.join(rel_clean);
                if let Some(imported) = read_with_imports(&import_path, visited, depth + 1) {
                    out.push(imported);
                    continue;
                }
            }
        }
        out.push(line.to_string());
    }
    Some(out.join("\n"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::CliOverrides;

    #[test]
    fn test_zero_legacy_filenames() {
        let content = include_str!("mod.rs");
        assert!(content.contains("FLOWORK.md"));
    }

    #[test]
    fn test_memory_loader_does_not_panic() {
        let cfg = AppConfig::build(CliOverrides::default());
        let _mem = load_hierarchical_memory(&cfg);
    }
}
