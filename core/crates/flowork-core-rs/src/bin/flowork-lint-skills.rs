use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;

const DEFAULT_SKILLS_DIR: &str = "/opt/floworkos/skills";
const MANDATORY_SECTIONS: &[&str] = &[
    "Objective",
    "Prerequisites",
    "Standard Operating Procedure",
    "Verification",
    "Failure Modes",
];
const VALID_DOMAINS: &[&str] = &[
    "os_doctrine",
    "browser",
    "shell_system",
    "code_dev",
    "database",
    "security",
    "network",
];

struct ParsedSkill {
    fields: HashMap<String, String>,
    keywords: Vec<String>,
    body: String,
}

fn parse_frontmatter(content: &str) -> Option<ParsedSkill> {
    if !content.starts_with("---") {
        return None;
    }
    let end_rel = content[3..].find("\n---")?;
    let end_idx = 3 + end_rel;
    let raw_yaml = content[3..end_idx].trim();
    let body = content[end_idx + 4..].trim().to_string();

    let mut fields = HashMap::new();
    let mut keywords = Vec::new();
    let mut current_array_key: Option<String> = None;

    for line in raw_yaml.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        if let Some(item) = trimmed.strip_prefix("- ") {
            if current_array_key.as_deref() == Some("keywords") {
                keywords.push(item.trim().trim_matches('"').trim_matches('\'').to_string());
            }
            continue;
        }
        if let Some(colon_idx) = trimmed.find(':') {
            let key = trimmed[..colon_idx].trim().to_string();
            let val = trimmed[colon_idx + 1..].trim();
            if val.is_empty() {
                current_array_key = Some(key);
            } else {
                current_array_key = None;
                if key == "keywords" && val.starts_with('[') && val.ends_with(']') {
                    for part in val[1..val.len() - 1].split(',') {
                        let clean = part.trim().trim_matches('"').trim_matches('\'').trim();
                        if !clean.is_empty() {
                            keywords.push(clean.to_string());
                        }
                    }
                } else {
                    let clean_val = val
                        .trim_start_matches('"')
                        .trim_end_matches('"')
                        .trim_start_matches('\'')
                        .trim_end_matches('\'')
                        .to_string();
                    fields.insert(key, clean_val);
                }
            }
        }
    }

    Some(ParsedSkill {
        fields,
        keywords,
        body,
    })
}

fn print_help() {
    println!("flowork-lint-skills — Sovereign Skill Quality Gate & Validator");
    println!("Usage: flowork-lint-skills [--check] [--help] [skills_dir]");
}

fn lint_dir(skills_dir: &Path) -> i32 {
    println!("=================================================================");
    println!("⚡ FLOWORK OS — SKILL QUALITY GATE & LINTER");
    println!("Auditing target directory: {}", skills_dir.display());
    println!("=================================================================\n");

    let mut dir_names = Vec::new();
    if let Ok(entries) = fs::read_dir(skills_dir) {
        for entry in entries.flatten() {
            let p = entry.path();
            let is_dir_or_link = fs::symlink_metadata(&p)
                .map(|m| m.is_dir() || m.file_type().is_symlink() && p.is_dir())
                .unwrap_or(false);
            if is_dir_or_link {
                if let Some(name) = entry.file_name().to_str() {
                    dir_names.push(name.to_string());
                }
            }
        }
    }
    dir_names.sort();

    let total_skills = dir_names.len();
    let mut failed_skills = 0usize;

    for skill_name in dir_names {
        let skill_dir = skills_dir.join(&skill_name);
        println!("🔍 Inspecting skill: [{}]", skill_name);
        let mut errors = Vec::new();

        if let Ok(meta) = fs::symlink_metadata(&skill_dir) {
            if meta.file_type().is_symlink() {
                errors.push(
                    "Skill directory must not be a symbolic link (violates anti-symlink doctrine)."
                        .to_string(),
                );
            }
        }

        let skill_md_path = skill_dir.join("SKILL.md");
        if !skill_md_path.is_file() {
            errors.push("Missing mandatory SKILL.md file.".to_string());
        } else {
            match fs::read_to_string(&skill_md_path) {
                Ok(raw) => match parse_frontmatter(&raw) {
                    None => errors.push(
                        "SKILL.md is missing valid YAML frontmatter between --- markers.".to_string(),
                    ),
                    Some(parsed) => {
                        let name_val = parsed.fields.get("name").map(String::as_str).unwrap_or("");
                        if name_val != skill_name {
                            errors.push(format!(
                                "Frontmatter name \"{}\" does not match directory name \"{}\".",
                                name_val, skill_name
                            ));
                        }
                        let desc_val = parsed
                            .fields
                            .get("description")
                            .map(String::as_str)
                            .unwrap_or("");
                        if desc_val.len() < 20 {
                            errors.push(
                                "Frontmatter description must be descriptive (at least 20 characters)."
                                    .to_string(),
                            );
                        }
                        let domain_val = parsed
                            .fields
                            .get("domain")
                            .map(String::as_str)
                            .unwrap_or("");
                        if !VALID_DOMAINS.contains(&domain_val) {
                            errors.push(format!(
                                "Frontmatter domain \"{}\" is invalid. Must be one of: {}.",
                                domain_val,
                                VALID_DOMAINS.join(", ")
                            ));
                        }
                        if parsed.keywords.len() != 20 {
                            errors.push(format!(
                                "Frontmatter keywords count is {}. EXACTLY 20 keywords are mandatory.",
                                parsed.keywords.len()
                            ));
                        }
                        let body_lower = parsed.body.to_ascii_lowercase();
                        for sec in MANDATORY_SECTIONS {
                            if !body_lower.contains(&sec.to_ascii_lowercase()) {
                                errors.push(format!("Missing mandatory section: \"{}\".", sec));
                            }
                        }
                    }
                },
                Err(e) => errors.push(format!("Failed reading SKILL.md: {}", e)),
            }
        }

        if errors.is_empty() {
            println!("✅ PASSED: All Flowork OS quality gates verified.");
        } else {
            failed_skills += 1;
            println!(
                "❌ FAILED: {} violation(s) found in [{}]:",
                errors.len(),
                skill_name
            );
            for err in &errors {
                println!("   - {}", err);
            }
        }
        println!();
    }

    println!("-----------------------------------------------------------------");
    println!(
        "Audit Summary: Total Skills: {} | Passed: {} | Failed: {}",
        total_skills,
        total_skills.saturating_sub(failed_skills),
        failed_skills
    );

    if failed_skills > 0 {
        eprintln!("\n❌ QUALITY GATE REJECTION: One or more skills failed sovereign validation.");
        1
    } else {
        println!("\n✅ QUALITY GATE ACCEPTED: Skill catalog is 100% compliant with Flowork OS standards.");
        0
    }
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut target_dir: Option<PathBuf> = env::var("FLOWORK_SKILLS_DIR").ok().map(PathBuf::from);

    for arg in &args {
        match arg.as_str() {
            "--help" | "-h" => {
                print_help();
                return;
            }
            "--check" => {
                println!("flowork-lint-skills: OK (native Rust)");
                return;
            }
            other if !other.starts_with('-') => {
                target_dir = Some(PathBuf::from(other));
            }
            _ => {}
        }
    }

    let dir = target_dir.unwrap_or_else(|| PathBuf::from(DEFAULT_SKILLS_DIR));
    process::exit(lint_dir(&dir));
}
