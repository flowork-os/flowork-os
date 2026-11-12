use bytes::Bytes;
use regex::Regex;
use serde_json::{json, Map, Value};
use std::collections::HashSet;
use uuid::Uuid;

use crate::vault::now_ms;

pub fn normalize_model(_model: &str) -> String {
    "gemini-3.8-flash-high".to_string()
}

pub fn sanitize_schema(val: &Value) -> Value {
    match val {
        Value::Array(arr) => Value::Array(arr.iter().map(sanitize_schema).collect()),
        Value::Object(map) => {
            let allowed: HashSet<&str> = [
                "type",
                "format",
                "description",
                "nullable",
                "enum",
                "properties",
                "required",
                "items",
                "minItems",
                "maxItems",
                "minimum",
                "maximum",
                "default",
            ]
            .into_iter()
            .collect();
            let mut out = Map::new();
            for (k, v) in map {
                if !allowed.contains(k.as_str()) {
                    continue;
                }
                if k == "type" {
                    if let Some(s) = v.as_str() {
                        out.insert(k.clone(), Value::String(s.to_uppercase()));
                        continue;
                    }
                } else if k == "properties" {
                    if let Some(prop_obj) = v.as_object() {
                        let mut new_props = Map::new();
                        for (pk, pv) in prop_obj {
                            new_props.insert(pk.clone(), sanitize_schema(pv));
                        }
                        out.insert(k.clone(), Value::Object(new_props));
                        continue;
                    }
                } else if k == "items" && v.is_object() {
                    out.insert(k.clone(), sanitize_schema(v));
                    continue;
                }
                out.insert(k.clone(), v.clone());
            }
            Value::Object(out)
        }
        other => other.clone(),
    }
}

pub fn merge_adjacent_same_role(contents: &[Value]) -> Vec<Value> {
    let mut merged: Vec<Value> = Vec::new();
    for item in contents {
        let Some(role) = item.get("role").and_then(|v| v.as_str()) else {
            continue;
        };
        let parts = item
            .get("parts")
            .and_then(|v| v.as_array())
            .cloned()
            .unwrap_or_default();
        if let Some(last) = merged.last_mut() {
            if last.get("role").and_then(|v| v.as_str()) == Some(role) {
                if let Some(last_parts) = last.get_mut("parts").and_then(|v| v.as_array_mut()) {
                    last_parts.extend(parts);
                }
                continue;
            }
        }
        merged.push(json!({ "role": role, "parts": parts }));
    }
    merged
}

pub fn openai_to_gemini(req: &Value, default_model: &str) -> Value {
    let messages = req
        .get("messages")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    let model = normalize_model(
        req.get("model")
            .and_then(|v| v.as_str())
            .unwrap_or(default_model),
    );
    let mut contents: Vec<Value> = Vec::new();
    let mut sys_text = String::new();
    let mut has_sys = false;

    for m in messages {
        let role = m
            .get("role")
            .and_then(|v| v.as_str())
            .unwrap_or("user")
            .to_lowercase();
        let text = match m.get("content") {
            Some(Value::String(s)) => s.clone(),
            Some(Value::Array(arr)) => arr
                .iter()
                .filter_map(|p| p.get("text").and_then(|t| t.as_str()))
                .collect::<Vec<_>>()
                .join("\n"),
            _ => String::new(),
        };
        if role == "system" {
            if !has_sys {
                sys_text = text;
                has_sys = true;
            } else {
                sys_text.push_str("\n\n");
                sys_text.push_str(&text);
            }
            continue;
        }
        let g_role = if role == "assistant" { "model" } else { "user" };
        contents.push(json!({ "role": g_role, "parts": [{ "text": text }] }));
    }

    if contents.is_empty() {
        contents.push(json!({ "role": "user", "parts": [{ "text": "" }] }));
    }

    let max_out = req
        .get("max_tokens")
        .or_else(|| req.get("max_completion_tokens"))
        .and_then(|v| v.as_i64())
        .unwrap_or(65536);

    let mut gen_cfg = Map::new();
    gen_cfg.insert("maxOutputTokens".to_string(), json!(max_out));
    if let Some(temp) = req.get("temperature") {
        if !temp.is_null() {
            gen_cfg.insert("temperature".to_string(), temp.clone());
        }
    }
    if let Some(top_p) = req.get("top_p") {
        if !top_p.is_null() {
            gen_cfg.insert("topP".to_string(), top_p.clone());
        }
    }

    let sys_instruction = if has_sys {
        json!({ "parts": [{ "text": sys_text }] })
    } else {
        Value::Null
    };

    json!({
        "project": "aicode-consumers",
        "model": model,
        "request": {
            "contents": contents,
            "systemInstruction": sys_instruction,
            "generationConfig": Value::Object(gen_cfg)
        }
    })
}

pub fn gemini_to_openai(req: &Value, model: &str, is_local: bool) -> Value {
    let inner = req.get("request").unwrap_or(req);
    let contents = inner
        .get("contents")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    let sys_inst = inner.get("systemInstruction");
    let mut messages: Vec<Value> = Vec::new();

    if let Some(sys) = sys_inst {
        if let Some(parts) = sys.get("parts").and_then(|v| v.as_array()) {
            if !parts.is_empty() {
                if is_local {
                    messages.push(json!({
                        "role": "system",
                        "content": "You are Mr. Flow (mrflow), the sovereign autonomous AI agent of Flowork OS. Always respond concisely, accurately, and directly in the user's language."
                    }));
                } else {
                    let joined = parts
                        .iter()
                        .filter_map(|p| p.get("text").and_then(|t| t.as_str()))
                        .collect::<Vec<_>>()
                        .join("\n\n")
                        .trim()
                        .to_string();
                    if !joined.is_empty() {
                        messages.push(json!({ "role": "system", "content": joined }));
                    }
                }
            }
        }
    }

    let session_ctx_re = Regex::new(r"(?s)<session_context>.*?</session_context>").ok();
    for r in contents {
        let role = if r.get("role").and_then(|v| v.as_str()) == Some("model") {
            "assistant"
        } else {
            "user"
        };
        let parts = r
            .get("parts")
            .and_then(|v| v.as_array())
            .cloned()
            .unwrap_or_default();
        let mut combined = String::new();
        for p in parts {
            if let Some(txt) = p.get("text").and_then(|v| v.as_str()) {
                let processed = if is_local && txt.contains("<session_context>") {
                    if let Some(ref re) = session_ctx_re {
                        re.replace_all(
                            txt,
                            "<session_context>OS: Flowork Linux 7.3.0 Rust. Workspace: /opt/floworkos.</session_context>",
                        )
                        .to_string()
                    } else {
                        txt.to_string()
                    }
                } else {
                    txt.to_string()
                };
                if !combined.is_empty() {
                    combined.push('\n');
                }
                combined.push_str(&processed);
            }
        }
        if !combined.is_empty() {
            messages.push(json!({ "role": role, "content": combined }));
        }
    }

    json!({
        "model": model,
        "messages": messages,
        "stream": true
    })
}

pub fn parse_gemini_sse_to_full_text(raw: &str) -> String {
    let mut out = String::new();
    for line in raw.lines() {
        let o = line.trim();
        if !o.starts_with("data:") {
            continue;
        }
        let payload = o[5..].trim();
        if payload == "[DONE]" || payload.is_empty() {
            continue;
        }
        if let Ok(parsed) = serde_json::from_str::<Value>(payload) {
            let root = parsed.get("response").unwrap_or(&parsed);
            if let Some(parts) = root
                .get("candidates")
                .and_then(|v| v.as_array())
                .and_then(|arr| arr.first())
                .and_then(|c| c.get("content"))
                .and_then(|c| c.get("parts"))
                .and_then(|v| v.as_array())
            {
                for p in parts {
                    if let Some(txt) = p.get("text").and_then(|v| v.as_str()) {
                        out.push_str(txt);
                    }
                }
            }
        }
    }
    out
}

pub fn create_openai_json_response(content: &str, model: &str) -> Value {
    let hex_id = &Uuid::new_v4().simple().to_string()[..24];
    json!({
        "id": format!("chatcmpl-{}", hex_id),
        "object": "chat.completion",
        "created": now_ms() / 1000,
        "model": model,
        "choices": [{
            "index": 0,
            "message": { "role": "assistant", "content": content },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    })
}

pub struct GeminiToOpenAiState {
    pub model: String,
    pub completion_id: String,
    pub created: i64,
    pub buffer: String,
}

impl GeminiToOpenAiState {
    pub fn new(model: String) -> Self {
        let hex_id = &Uuid::new_v4().simple().to_string()[..24];
        Self {
            model,
            completion_id: format!("chatcmpl-{}", hex_id),
            created: now_ms() / 1000,
            buffer: String::new(),
        }
    }

    pub fn push_chunk(&mut self, bytes: &[u8]) -> Bytes {
        self.buffer.push_str(&String::from_utf8_lossy(bytes));
        let mut out = String::new();
        while let Some(pos) = self.buffer.find('\n') {
            let line = self.buffer[..pos].trim().to_string();
            self.buffer.drain(..=pos);
            if line.is_empty() || line.starts_with(':') {
                continue;
            }
            if let Some(rest) = line.strip_prefix("data:") {
                let raw = rest.trim();
                if raw == "[DONE]" {
                    continue;
                }
                if let Ok(parsed) = serde_json::from_str::<Value>(raw) {
                    let root = parsed.get("response").unwrap_or(&parsed);
                    if let Some(parts) = root
                        .get("candidates")
                        .and_then(|v| v.as_array())
                        .and_then(|arr| arr.first())
                        .and_then(|c| c.get("content"))
                        .and_then(|c| c.get("parts"))
                        .and_then(|v| v.as_array())
                    {
                        for p in parts {
                            if let Some(txt) = p.get("text").and_then(|v| v.as_str()) {
                                let chunk = json!({
                                    "id": self.completion_id,
                                    "object": "chat.completion.chunk",
                                    "created": self.created,
                                    "model": self.model,
                                    "choices": [{
                                        "index": 0,
                                        "delta": { "content": txt },
                                        "finish_reason": Value::Null
                                    }]
                                });
                                out.push_str(&format!("data: {}\n\n", chunk));
                            }
                        }
                    }
                }
            }
        }
        Bytes::from(out)
    }

    pub fn flush(&mut self) -> Bytes {
        let mut out = String::new();
        if !self.buffer.trim().is_empty() {
            let rem = self.buffer.clone();
            self.buffer.clear();
            let extra = self.push_chunk(format!("{}\n", rem).as_bytes());
            out.push_str(&String::from_utf8_lossy(&extra));
        }
        let end_chunk = json!({
            "id": self.completion_id,
            "object": "chat.completion.chunk",
            "created": self.created,
            "model": self.model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        });
        out.push_str(&format!("data: {}\n\ndata: [DONE]\n\n", end_chunk));
        Bytes::from(out)
    }
}

pub struct OpenAiToGeminiState {
    pub buffer: String,
    pub stop_emitted: bool,
}

impl OpenAiToGeminiState {
    pub fn new() -> Self {
        Self {
            buffer: String::new(),
            stop_emitted: false,
        }
    }

    fn emit_stop(&mut self, out: &mut String) {
        if self.stop_emitted {
            return;
        }
        self.stop_emitted = true;
        let stop_ev = json!({
            "response": {
                "candidates": [{
                    "content": { "role": "model", "parts": [] },
                    "finishReason": "STOP"
                }]
            },
            "candidates": [{
                "content": { "role": "model", "parts": [] },
                "finishReason": "STOP"
            }]
        });
        out.push_str(&format!("data: {}\n\n", stop_ev));
    }

    pub fn push_chunk(&mut self, bytes: &[u8]) -> Bytes {
        self.buffer.push_str(&String::from_utf8_lossy(bytes));
        let mut out = String::new();
        while let Some(pos) = self.buffer.find('\n') {
            let line = self.buffer[..pos].trim().to_string();
            self.buffer.drain(..=pos);
            if line.is_empty() || line.starts_with(':') {
                continue;
            }
            if let Some(rest) = line.strip_prefix("data:") {
                let raw = rest.trim();
                if raw == "[DONE]" {
                    self.emit_stop(&mut out);
                    continue;
                }
                if let Ok(parsed) = serde_json::from_str::<Value>(raw) {
                    if let Some(delta) = parsed
                        .get("choices")
                        .and_then(|v| v.as_array())
                        .and_then(|a| a.first())
                        .and_then(|c| c.get("delta"))
                    {
                        let th = delta
                            .get("reasoning")
                            .or_else(|| delta.get("reasoning_content"))
                            .and_then(|v| v.as_str())
                            .unwrap_or("");
                        if !th.is_empty() {
                            let c = json!({
                                "response": {
                                    "candidates": [{
                                        "content": { "role": "model", "parts": [{ "thought": true, "text": th }] },
                                        "finishReason": Value::Null
                                    }]
                                },
                                "candidates": [{
                                    "content": { "role": "model", "parts": [{ "thought": true, "text": th }] },
                                    "finishReason": Value::Null
                                }]
                            });
                            out.push_str(&format!("data: {}\n\n", c));
                        }
                        let txt = delta.get("content").and_then(|v| v.as_str()).unwrap_or("");
                        if !txt.is_empty() {
                            let c = json!({
                                "response": {
                                    "candidates": [{
                                        "content": { "role": "model", "parts": [{ "text": txt }] },
                                        "finishReason": Value::Null
                                    }]
                                },
                                "candidates": [{
                                    "content": { "role": "model", "parts": [{ "text": txt }] },
                                    "finishReason": Value::Null
                                }]
                            });
                            out.push_str(&format!("data: {}\n\n", c));
                        }
                    }
                }
            }
        }
        Bytes::from(out)
    }

    pub fn flush(&mut self) -> Bytes {
        let mut out = String::new();
        if !self.buffer.trim().is_empty() {
            let rem = self.buffer.clone();
            self.buffer.clear();
            let extra = self.push_chunk(format!("{}\n", rem).as_bytes());
            out.push_str(&String::from_utf8_lossy(&extra));
        }
        self.emit_stop(&mut out);
        Bytes::from(out)
    }
}

pub struct UnwrapCloudCodeSseState {
    pub buffer: String,
}

impl UnwrapCloudCodeSseState {
    pub fn new() -> Self {
        Self {
            buffer: String::new(),
        }
    }

    fn process_line(line: &str) -> String {
        let trimmed = line.trim();
        if trimmed.starts_with("data:") {
            let raw = trimmed[5..].trim();
            if raw == "[DONE]" {
                return "data: [DONE]\n\n".to_string();
            }
            if let Ok(parsed) = serde_json::from_str::<Value>(raw) {
                let unwrapped = parsed.get("response").unwrap_or(&parsed);
                return format!("data: {}\n\n", unwrapped);
            }
            return format!("{}\n", line);
        }
        if !trimmed.is_empty() {
            return format!("{}\n", line);
        }
        String::new()
    }

    pub fn push_chunk(&mut self, bytes: &[u8]) -> Bytes {
        self.buffer.push_str(&String::from_utf8_lossy(bytes));
        let mut out = String::new();
        while let Some(pos) = self.buffer.find('\n') {
            let line = self.buffer[..pos].to_string();
            self.buffer.drain(..=pos);
            out.push_str(&Self::process_line(&line));
        }
        Bytes::from(out)
    }

    pub fn flush(&mut self) -> Bytes {
        let mut out = String::new();
        let rem = self.buffer.trim().to_string();
        self.buffer.clear();
        if !rem.is_empty() {
            if let Some(raw) = rem.strip_prefix("data:").map(|s| s.trim()) {
                if let Ok(parsed) = serde_json::from_str::<Value>(raw) {
                    let unwrapped = parsed.get("response").unwrap_or(&parsed);
                    out.push_str(&format!("data: {}\n\n", unwrapped));
                } else {
                    out.push_str(&format!("{}\n\n", rem));
                }
            } else {
                out.push_str(&format!("{}\n\n", rem));
            }
        }
        Bytes::from(out)
    }
}

pub fn build_gemini_buffered_json(raw_sse: &str) -> Value {
    let mut all_parts: Vec<Value> = Vec::new();
    let mut finish_reason = "STOP".to_string();
    let mut usage_meta: Option<Value> = None;

    for line in raw_sse.lines() {
        let trimmed = line.trim();
        let Some(rest) = trimmed.strip_prefix("data:") else {
            continue;
        };
        let payload = rest.trim();
        if payload.is_empty() || payload == "[DONE]" {
            continue;
        }
        if let Ok(parsed) = serde_json::from_str::<Value>(payload) {
            let root = parsed.get("response").unwrap_or(&parsed);
            if let Some(u) = root.get("usageMetadata") {
                usage_meta = Some(u.clone());
            }
            if let Some(cand) = root
                .get("candidates")
                .and_then(|v| v.as_array())
                .and_then(|a| a.first())
            {
                if let Some(fr) = cand.get("finishReason").and_then(|v| v.as_str()) {
                    finish_reason = fr.to_string();
                }
                if let Some(parts) = cand
                    .get("content")
                    .and_then(|c| c.get("parts"))
                    .and_then(|p| p.as_array())
                {
                    all_parts.extend(parts.clone());
                }
            }
        }
    }

    let mut collapsed: Vec<Value> = Vec::new();
    let mut text_acc = String::new();
    for p in all_parts {
        let is_thought = p.get("thought").and_then(|v| v.as_bool()).unwrap_or(false);
        if let Some(txt) = p.get("text").and_then(|v| v.as_str()) {
            if !is_thought {
                text_acc.push_str(txt);
                continue;
            }
        }
        if p.get("functionCall").is_some() {
            if !text_acc.is_empty() {
                collapsed.push(json!({ "text": text_acc }));
                text_acc.clear();
            }
            collapsed.push(p);
        } else if !is_thought {
            collapsed.push(p);
        }
    }
    if !text_acc.is_empty() {
        collapsed.push(json!({ "text": text_acc }));
    }
    if collapsed.is_empty() {
        let full = parse_gemini_sse_to_full_text(raw_sse);
        collapsed.push(json!({ "text": if full.is_empty() { "Done." } else { &full } }));
    }

    let mut out = json!({
        "candidates": [{
            "content": { "role": "model", "parts": collapsed },
            "finishReason": finish_reason
        }]
    });
    if let Some(u) = usage_meta {
        if let Some(obj) = out.as_object_mut() {
            obj.insert("usageMetadata".to_string(), u);
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sanitize_schema_uppercases_and_strips() {
        let input = json!({
            "type": "object",
            "additionalProperties": false,
            "properties": {
                "path": { "type": "string", "description": "file path", "$schema": "draft7" },
                "tags": { "type": "array", "items": { "type": "string" } }
            },
            "required": ["path"]
        });
        let out = sanitize_schema(&input);
        assert_eq!(out["type"], "OBJECT");
        assert!(out.get("additionalProperties").is_none());
        assert_eq!(out["properties"]["path"]["type"], "STRING");
        assert!(out["properties"]["path"].get("$schema").is_none());
        assert_eq!(out["properties"]["tags"]["items"]["type"], "STRING");
    }

    #[test]
    fn test_merge_adjacent_roles() {
        let input = vec![
            json!({ "role": "user", "parts": [{ "text": "a" }] }),
            json!({ "role": "user", "parts": [{ "text": "b" }] }),
            json!({ "role": "model", "parts": [{ "text": "c" }] }),
        ];
        let out = merge_adjacent_same_role(&input);
        assert_eq!(out.len(), 2);
        assert_eq!(out[0]["parts"].as_array().unwrap().len(), 2);
    }

    #[test]
    fn test_gemini_to_openai_local_condenses_context() {
        let input = json!({
            "systemInstruction": { "parts": [{ "text": "Huge instruction" }] },
            "contents": [{
                "role": "user",
                "parts": [{ "text": "Hello\n<session_context>BIG TREE</session_context>\nWorld" }]
            }]
        });
        let out = gemini_to_openai(&input, "deepseek-v4", true);
        let msg = out["messages"][1]["content"].as_str().unwrap();
        assert!(!msg.contains("BIG TREE"));
        assert!(msg.contains("Flowork Linux 7.3.0 Rust"));
    }

    #[test]
    fn test_sse_stream_transformers() {
        let mut g2o = GeminiToOpenAiState::new("gemini-3.8-flash-high".to_string());
        let chunk = br#"data: {"response":{"candidates":[{"content":{"parts":[{"text":"Hi"}]}}]}}
"#;
        let out = g2o.push_chunk(chunk);
        let out_str = String::from_utf8_lossy(&out);
        assert!(out_str.contains(r#""content":"Hi""#));
        let flushed = g2o.flush();
        assert!(String::from_utf8_lossy(&flushed).contains("[DONE]"));

        let mut o2g = OpenAiToGeminiState::new();
        let o_chunk = br#"data: {"choices":[{"delta":{"reasoning":"think","content":"ans"}}]}
data: [DONE]
"#;
        let g_out = String::from_utf8_lossy(&o2g.push_chunk(o_chunk)).to_string();
        assert!(g_out.contains(r#""thought":true"#));
        assert!(g_out.contains(r#""text":"ans""#));
        assert!(g_out.contains(r#""finishReason":"STOP""#));
    }
}
