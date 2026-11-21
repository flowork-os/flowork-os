use crate::inference::TokenUsage;
use chrono::Utc;
use serde_json::{json, Value};
use std::io::{self, Write};
use std::sync::Mutex;

pub fn sanitize_ansi(text: &str, raw_output: bool) -> String {
    if raw_output {
        return text.to_string();
    }
    // Strip potentially hazardous terminal escape sequences while keeping tabs/newlines
    let mut out = String::with_capacity(text.len());
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        if c == '\x1b' {
            if matches!(chars.peek(), Some('[')) {
                chars.next();
                while let Some(&n) = chars.peek() {
                    chars.next();
                    if ('@'..='~').contains(&n) {
                        break;
                    }
                }
            }
            continue;
        }
        out.push(c);
    }
    out
}

pub struct StreamJsonEmitter {
    lock: Mutex<()>,
}

impl Default for StreamJsonEmitter {
    fn default() -> Self {
        Self::new()
    }
}

impl StreamJsonEmitter {
    pub fn new() -> Self {
        Self {
            lock: Mutex::new(()),
        }
    }

    fn write_event(&self, payload: &Value) {
        let _g = self.lock.lock().ok();
        if let Ok(line) = serde_json::to_string(payload) {
            let stdout = io::stdout();
            let mut handle = stdout.lock();
            let _ = writeln!(handle, "{}", line);
            let _ = handle.flush();
        }
    }

    pub fn emit_init(&self, session_id: &str, model: &str) {
        self.write_event(&json!({
            "type": "init",
            "timestamp": now_iso(),
            "session_id": session_id,
            "model": model
        }));
    }

    pub fn emit_message(&self, role: &str, content: &str, delta: bool) {
        if content.is_empty() {
            return;
        }
        self.write_event(&json!({
            "type": "message",
            "timestamp": now_iso(),
            "role": role,
            "content": content,
            "delta": delta
        }));
    }

    pub fn emit_thought(&self, thought: &str) {
        if thought.trim().is_empty() {
            return;
        }
        self.write_event(&json!({
            "type": "thought",
            "timestamp": now_iso(),
            "thought": thought
        }));
    }

    pub fn emit_tool_use(&self, tool_id: &str, tool_name: &str, parameters: &Value) {
        self.write_event(&json!({
            "type": "tool_use",
            "timestamp": now_iso(),
            "tool_name": tool_name,
            "tool_id": tool_id,
            "parameters": parameters
        }));
    }

    pub fn emit_tool_result(
        &self,
        tool_id: &str,
        success: bool,
        output: &str,
        error_msg: Option<&str>,
    ) {
        let mut obj = json!({
            "type": "tool_result",
            "timestamp": now_iso(),
            "tool_id": tool_id,
            "status": if success { "success" } else { "error" },
            "output": output
        });
        if let Some(err) = error_msg {
            obj["error"] = json!({
                "type": "tool_execution_error",
                "message": err
            });
        }
        self.write_event(&obj);
    }

    pub fn emit_error(&self, severity: &str, message: &str) {
        self.write_event(&json!({
            "type": "error",
            "timestamp": now_iso(),
            "severity": severity,
            "message": message
        }));
    }

    pub fn emit_ask_user(&self, id: &str, questions: &Value) {
        self.write_event(&json!({
            "type": "ask_user",
            "timestamp": now_iso(),
            "id": id,
            "questions": questions
        }));
    }

    pub fn emit_stats(
        &self,
        turn: usize,
        max_turns: usize,
        tokens: &TokenUsage,
        mode: &str,
        context_tokens: u64,
        provider: Option<&str>,
    ) {
        self.write_event(&json!({
            "type": "stats",
            "timestamp": now_iso(),
            "turn": turn,
            "max_turns": max_turns,
            "mode": mode,
            "context_tokens": context_tokens,
            "provider": provider.unwrap_or("auto"),
            "tokens": {
                "input": tokens.input,
                "output": tokens.output,
                "cached": tokens.cached,
                "thoughts": tokens.thoughts,
                "total": tokens.total
            }
        }));
    }

    pub fn emit_result(
        &self,
        success: bool,
        tokens: &TokenUsage,
        duration_ms: u128,
        tool_calls: usize,
        error_message: Option<&str>,
    ) {
        let mut ev = json!({
            "type": "result",
            "timestamp": now_iso(),
            "status": if success { "success" } else { "error" },
            "stats": {
                "total_tokens": tokens.total,
                "input_tokens": tokens.input,
                "output_tokens": tokens.output,
                "cached": tokens.cached,
                "thoughts": tokens.thoughts,
                "input": tokens.input,
                "duration_ms": duration_ms as u64,
                "tool_calls": tool_calls
            }
        });
        if let Some(msg) = error_message {
            ev["error"] = json!({
                "type": "error",
                "message": msg
            });
        }
        self.write_event(&ev);
    }
}

pub fn print_json_summary(
    session_id: &str,
    model: &str,
    response: &str,
    tokens: &TokenUsage,
    duration_ms: u128,
    tool_calls: usize,
    error: Option<&str>,
) {
    let mut out = json!({
        "session_id": session_id,
        "model": model,
        "response": response,
        "stats": {
            "total_tokens": tokens.total,
            "input_tokens": tokens.input,
            "output_tokens": tokens.output,
            "cached": tokens.cached,
            "thoughts": tokens.thoughts,
            "duration_ms": duration_ms as u64,
            "tool_calls": tool_calls
        }
    });
    if let Some(e) = error {
        out["error"] = json!({ "message": e });
    }
    println!("{}", serde_json::to_string_pretty(&out).unwrap_or_default());
}

fn now_iso() -> String {
    Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true)
}
