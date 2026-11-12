pub mod cdp;
pub mod flowfs;
pub mod lifecycle;
pub mod rea_native;

use serde_json::{json, Map, Value};
use std::path::{Path, PathBuf};

pub const FLOWORK_ROOT: &str = "/opt/floworkos";
pub const DEFAULT_TOOLS_DIR: &str = "/opt/floworkos/tools";
pub const DEFAULT_SKILLS_DIR: &str = "/opt/floworkos/skills";

pub fn resolve_home_dir() -> PathBuf {
    if let Ok(h) = std::env::var("HOME") {
        let trimmed = h.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    dirs::home_dir().unwrap_or_else(|| PathBuf::from("/tmp"))
}

pub fn resolve_path_from_cwd(raw: &str, cwd: &Path) -> PathBuf {
    let p = Path::new(raw);
    if p.is_absolute() {
        p.to_path_buf()
    } else {
        cwd.join(p)
    }
}

pub fn inject_intercept_gate_fields(schema: &mut Value) {
    if !schema.is_object() {
        *schema = json!({
            "type": "object",
            "properties": {},
            "required": []
        });
    }
    let obj = schema.as_object_mut().expect("object checked");
    if !obj.contains_key("type") {
        obj.insert("type".to_string(), Value::String("object".to_string()));
    }

    let props_val = obj
        .entry("properties".to_string())
        .or_insert_with(|| Value::Object(Map::new()));
    if !props_val.is_object() {
        *props_val = Value::Object(Map::new());
    }
    let props = props_val.as_object_mut().expect("props object");
    props.insert(
        "reason".to_string(),
        json!({
            "type": "string",
            "maxLength": 160,
            "description": "[MANDATORY AUDIT REASON] Explain why this tool is being used for this action. Required for auditability and safety. Must be in strict English, maximum 160 characters."
        }),
    );
    props.insert(
        "keywords".to_string(),
        json!({
            "type": "array",
            "items": { "type": "string" },
            "minItems": 5,
            "description": "[MANDATORY DYNAMIC ROUTING KEYWORDS] Provide at least 5 English semantic keywords describing this action. Required for the Dynamic Tool Router to match relevant tools (max 5) and trigger modular prompts without token bloat. Minimum 5 keywords."
        }),
    );
    props.insert(
        "goal".to_string(),
        json!({
            "type": "string",
            "maxLength": 160,
            "description": "[INTERCEPT GATE OBJECTIVE] High-level task objective required on the initial tool call of an operation. Explains the overarching operational mission in concise English (maximum 160 characters)."
        }),
    );

    let req_val = obj
        .entry("required".to_string())
        .or_insert_with(|| Value::Array(Vec::new()));
    if !req_val.is_array() {
        *req_val = Value::Array(Vec::new());
    }
    let req = req_val.as_array_mut().expect("req array");
    if !req.iter().any(|v| v.as_str() == Some("reason")) {
        req.push(Value::String("reason".to_string()));
    }
    if !req.iter().any(|v| v.as_str() == Some("keywords")) {
        req.push(Value::String("keywords".to_string()));
    }
}

pub fn content_type_for_path(path: &Path) -> &'static str {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .map(|s| s.to_ascii_lowercase())
        .unwrap_or_default();
    match ext.as_str() {
        "html" => "text/html; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "js" => "application/javascript; charset=utf-8",
        "json" => "application/json",
        "png" => "image/png",
        "jpg" | "jpeg" => "image/jpeg",
        "svg" => "image/svg+xml",
        "mp4" => "video/mp4",
        "mov" => "video/quicktime",
        "mp3" => "audio/mpeg",
        "webp" => "image/webp",
        _ => "application/octet-stream",
    }
}
