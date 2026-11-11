use crate::config::AppConfig;
use futures_util::StreamExt;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::time::Duration;
use tokio::sync::mpsc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionCallData {
    pub id: String,
    pub name: String,
    pub args: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentPart {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub thought: Option<bool>,
    #[serde(rename = "thoughtSignature", skip_serializing_if = "Option::is_none")]
    pub thought_signature: Option<String>,
    #[serde(rename = "functionCall", skip_serializing_if = "Option::is_none")]
    pub function_call: Option<FunctionCallData>,
    #[serde(rename = "functionResponse", skip_serializing_if = "Option::is_none")]
    pub function_response: Option<Value>,
    #[serde(rename = "inlineData", skip_serializing_if = "Option::is_none")]
    pub inline_data: Option<InlineBlob>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InlineBlob {
    #[serde(rename = "mimeType")]
    pub mime_type: String,
    pub data: String,
}

impl ContentPart {
    pub fn text(t: impl Into<String>) -> Self {
        Self {
            text: Some(t.into()),
            thought: None,
            thought_signature: None,
            function_call: None,
            function_response: None,
            inline_data: None,
        }
    }

    pub fn function_response(id: &str, name: &str, response_val: Value) -> Self {
        Self {
            text: None,
            thought: None,
            thought_signature: None,
            function_call: None,
            function_response: Some(json!({
                "id": id,
                "name": name,
                "response": response_val
            })),
            inline_data: None,
        }
    }

    pub fn inline_data(mime_type: impl Into<String>, b64: impl Into<String>) -> Self {
        Self {
            text: None,
            thought: None,
            thought_signature: None,
            function_call: None,
            function_response: None,
            inline_data: Some(InlineBlob {
                mime_type: mime_type.into(),
                data: b64.into(),
            }),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String, // "user" | "model"
    pub parts: Vec<ContentPart>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TokenUsage {
    pub input: u64,
    pub output: u64,
    pub cached: u64,
    pub thoughts: u64,
    pub total: u64,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum StreamEvent {
    TextDelta(String),
    ThoughtDelta(String),
    ModelPart(ContentPart),
    ToolCall(FunctionCallData),
    Usage(TokenUsage),
    Finish(String),
    Error(String),
}

#[derive(Debug, Clone)]
pub struct ToolDeclaration {
    pub name: String,
    pub description: String,
    pub parameters_json_schema: Value,
}

pub struct ConnectorClient {
    http: Client,
    base_url: String,
    api_key: String,
    debug: bool,
}

impl ConnectorClient {
    pub fn new(config: &AppConfig) -> Self {
        let http = Client::builder()
            .pool_max_idle_per_host(0)
            .connect_timeout(Duration::from_secs(10))
            .timeout(Duration::from_secs(600))
            .build()
            .unwrap_or_else(|_| Client::new());
        Self {
            http,
            base_url: config.connector_url.trim_end_matches('/').to_string(),
            api_key: config.api_key.clone(),
            debug: config.debug,
        }
    }

    pub fn is_client_schema_error(e: &str) -> bool {
        e.contains("HTTP 400")
            || e.contains("INVALID_ARGUMENT")
            || e.contains("Unknown name")
            || e.contains("Proto field")
    }

    pub fn is_retryable_connector_error(e: &str) -> bool {
        if Self::is_client_schema_error(e) {
            return false;
        }
        let lower = e.to_ascii_lowercase();
        e.contains("429")
            || e.contains("503")
            || e.contains("502")
            || e.contains("500")
            || e.contains("504")
            || e.contains("UNAVAILABLE")
            || e.contains("Empty stream output")
            || e.contains("Connector HTTP error")
            || e.contains("OpenAI connector HTTP error")
            || e.contains("SSE stream read error")
            || e.contains("SSE read error")
            || lower.contains("error sending request")
            || lower.contains("connection")
            || lower.contains("reset")
            || lower.contains("refused")
            || lower.contains("broken pipe")
            || lower.contains("timed out")
    }

    fn is_openai_local_model(model: &str) -> bool {
        let m = model.to_ascii_lowercase();
        m.contains("deepseek") || m.contains("qwen") || m.contains("ollama") || m.contains("llama") || m.contains(":")
    }

    pub fn base_url(&self) -> &str {
        &self.base_url
    }

    /// Collects a full non-interactive completion (used by 2-pass chat compression & session summary).
    pub async fn generate_once(
        &self,
        model: &str,
        system_instruction: &str,
        contents: &[ChatMessage],
        tools: &[ToolDeclaration],
    ) -> Result<(String, Vec<ContentPart>, TokenUsage), String> {
        let (tx, mut rx) = mpsc::unbounded_channel();
        self.stream_generate(model, system_instruction, contents, tools, tx)
            .await?;

        let mut text_out = String::new();
        let mut raw_parts = Vec::new();
        let mut usage = TokenUsage::default();

        while let Some(ev) = rx.recv().await {
            match ev {
                StreamEvent::TextDelta(t) => text_out.push_str(&t),
                StreamEvent::ModelPart(p) => raw_parts.push(p),
                StreamEvent::Usage(u) => usage = u,
                StreamEvent::Error(e) => return Err(e),
                StreamEvent::ThoughtDelta(_) | StreamEvent::ToolCall(_) | StreamEvent::Finish(_) => {}
            }
        }
        let coalesced = crate::context::coalesce_parts(raw_parts);
        Ok((text_out, coalesced, usage))
    }

    fn resolve_offline_fallback_model(&self) -> String {
        let root = std::env::var("FLOWORK_OS_ROOT")
            .map(std::path::PathBuf::from)
            .unwrap_or_else(|_| std::path::PathBuf::from("/opt/floworkos"));
        let models_file = root.join("connector/config/models.json");
        if let Ok(raw) = std::fs::read_to_string(models_file) {
            if let Ok(v) = serde_json::from_str::<Value>(&raw) {
                if let Some(m) = v.get("offline_fallback_model").and_then(|s| s.as_str()) {
                    if !m.trim().is_empty() {
                        return m.trim().to_string();
                    }
                }
            }
        }
        "deepseek-v4-9b-uncensored".to_string()
    }

    /// Streams model response via Connector Gateway (:9099).
    /// Supports both Gemini CloudCode (/v1beta/models/...:streamGenerateContent?alt=sse)
    /// and OpenAI-compatible Ollama/9Router/offline endpoints (/v1/chat/completions).
    pub async fn stream_generate(
        &self,
        model: &str,
        system_instruction: &str,
        contents: &[ChatMessage],
        tools: &[ToolDeclaration],
        tx: mpsc::UnboundedSender<StreamEvent>,
    ) -> Result<(), String> {
        let use_openai = Self::is_openai_local_model(model);
        let mut last_err = String::new();

        for attempt in 0..4 {
            let res = if use_openai {
                self.stream_openai(model, system_instruction, contents, tools, &tx).await
            } else {
                self.stream_gemini(model, system_instruction, contents, tools, &tx).await
            };
            match res {
                Ok(()) => return Ok(()),
                Err(e) => {
                    if self.debug {
                        eprintln!("[mrflow:debug] inference attempt {} failed: {}", attempt + 1, e);
                    }
                    last_err = e.clone();
                    if Self::is_retryable_connector_error(&e) && attempt < 3 {
                        tokio::time::sleep(Duration::from_millis(700 * (attempt as u64 + 1))).await;
                        continue;
                    }
                    break;
                }
            }
        }

        // Offline SLM / Ollama fallback only on network/5xx pool outage, never masking 4xx client schema bugs silently
        if !use_openai && !Self::is_client_schema_error(&last_err) {
            let offline_model = self.resolve_offline_fallback_model();
            if self.debug {
                eprintln!(
                    "[mrflow:debug] failing over to offline SLM ({}) after error: {}",
                    offline_model, last_err
                );
            }
            if let Ok(()) = self
                .stream_openai(
                    &offline_model,
                    system_instruction,
                    contents,
                    tools,
                    &tx,
                )
                .await
            {
                return Ok(());
            }
        }

        Err(last_err)
    }

    async fn stream_gemini(
        &self,
        model: &str,
        system_instruction: &str,
        contents: &[ChatMessage],
        tools: &[ToolDeclaration],
        tx: &mpsc::UnboundedSender<StreamEvent>,
    ) -> Result<(), String> {
        let url = format!(
            "{}/v1beta/models/{}:streamGenerateContent?alt=sse",
            self.base_url,
            urlencoding::encode(model)
        );

        let mut payload = json!({
            "contents": contents,
        });

        if !system_instruction.trim().is_empty() {
            payload["systemInstruction"] = json!({
                "role": "user",
                "parts": [{ "text": system_instruction }]
            });
        }

        if !tools.is_empty() {
            let decls: Vec<Value> = tools
                .iter()
                .map(|t| {
                    let mut schema = t.parameters_json_schema.clone();
                    sanitize_gemini_schema(&mut schema);
                    if !schema.is_object() {
                        schema = json!({ "type": "object", "properties": {} });
                    }
                    json!({
                        "name": t.name,
                        "description": t.description,
                        "parametersJsonSchema": schema
                    })
                })
                .collect();
            payload["tools"] = json!([{ "functionDeclarations": decls }]);
        }

        if self.debug {
            eprintln!(
                "[mrflow:debug] POST {} | model={} sys_len={} tools={} contents={}",
                url,
                model,
                system_instruction.len(),
                tools.len(),
                contents.len()
            );
        }

        let resp = self
            .http
            .post(&url)
            .header("Content-Type", "application/json")
            .header("x-goog-api-key", &self.api_key)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&payload)
            .send()
            .await
            .map_err(|e| format!("Connector HTTP error: {}", e))?;

        let status = resp.status();
        if self.debug {
            eprintln!("[mrflow:debug] HTTP status: {}", status);
        }
        if !status.is_success() {
            let body = resp.text().await.unwrap_or_default();
            return Err(format!("Connector HTTP {} {}: {}", status.as_u16(), status, body));
        }

        let mut stream = resp.bytes_stream();
        let mut buf = String::new();
        let mut tool_idx = 0usize;
        let mut got_any_output = false;
        let mut got_finish = false;

        while let Some(chunk_res) = stream.next().await {
            let chunk = chunk_res.map_err(|e| format!("SSE stream read error: {}", e))?;
            let text_chunk = String::from_utf8_lossy(&chunk);
            buf.push_str(&text_chunk);

            while let Some(pos) = buf.find('\n') {
                let line = buf[..pos].trim_end_matches('\r').to_string();
                buf.drain(..=pos);

                if line.is_empty() {
                    continue;
                }
                let data_str = if let Some(rest) = line.strip_prefix("data:") {
                    rest.trim()
                } else {
                    continue;
                };
                if data_str == "[DONE]" {
                    continue;
                }

                let Ok(v) = serde_json::from_str::<Value>(data_str) else {
                    continue;
                };

                if let Some(err_obj) = v.get("error") {
                    let msg = err_obj
                        .get("message")
                        .and_then(|m| m.as_str())
                        .unwrap_or("Upstream error");
                    let _ = tx.send(StreamEvent::Error(msg.to_string()));
                    return Err(msg.to_string());
                }

                if let Some(usage) = v.get("usageMetadata") {
                    let u = TokenUsage {
                        input: usage.get("promptTokenCount").and_then(|x| x.as_u64()).unwrap_or(0),
                        output: usage.get("candidatesTokenCount").and_then(|x| x.as_u64()).unwrap_or(0),
                        cached: usage.get("cachedContentTokenCount").and_then(|x| x.as_u64()).unwrap_or(0),
                        thoughts: usage.get("thoughtsTokenCount").and_then(|x| x.as_u64()).unwrap_or(0),
                        total: usage.get("totalTokenCount").and_then(|x| x.as_u64()).unwrap_or(0),
                    };
                    let _ = tx.send(StreamEvent::Usage(u));
                }

                if let Some(candidates) = v.get("candidates").and_then(|c| c.as_array()) {
                    for cand in candidates {
                        if let Some(parts) = cand
                            .get("content")
                            .and_then(|c| c.get("parts"))
                            .and_then(|p| p.as_array())
                        {
                            for raw_part in parts {
                                let thought_sig = raw_part
                                    .get("thoughtSignature")
                                    .and_then(|s| s.as_str())
                                    .map(|s| s.to_string());
                                let is_thought = raw_part
                                    .get("thought")
                                    .and_then(|b| b.as_bool())
                                    .unwrap_or(false);

                                if let Some(fc) = raw_part.get("functionCall") {
                                    got_any_output = true;
                                    tool_idx += 1;
                                    let name = fc
                                        .get("name")
                                        .and_then(|n| n.as_str())
                                        .unwrap_or("")
                                        .to_string();
                                    let args = fc.get("args").cloned().unwrap_or_else(|| json!({}));
                                    let id = fc
                                        .get("id")
                                        .and_then(|i| i.as_str())
                                        .map(|s| s.to_string())
                                        .unwrap_or_else(|| {
                                            format!("{}_{}_{}", name, chrono::Utc::now().timestamp_millis(), tool_idx)
                                        });
                                    let fc_data = FunctionCallData { id, name, args };
                                    let part = ContentPart {
                                        text: None,
                                        thought: if is_thought { Some(true) } else { None },
                                        thought_signature: thought_sig.clone(),
                                        function_call: Some(fc_data.clone()),
                                        function_response: None,
                                        inline_data: None,
                                    };
                                    let _ = tx.send(StreamEvent::ModelPart(part));
                                    let _ = tx.send(StreamEvent::ToolCall(fc_data));
                                } else if let Some(txt) = raw_part.get("text").and_then(|t| t.as_str()) {
                                    if !txt.is_empty() {
                                        got_any_output = true;
                                    }
                                    let part = ContentPart {
                                        text: if txt.is_empty() { None } else { Some(txt.to_string()) },
                                        thought: if is_thought { Some(true) } else { None },
                                        thought_signature: thought_sig.clone(),
                                        function_call: None,
                                        function_response: None,
                                        inline_data: None,
                                    };
                                    if part.text.is_some() || part.thought_signature.is_some() {
                                        let _ = tx.send(StreamEvent::ModelPart(part));
                                    }
                                    if !txt.is_empty() {
                                        if is_thought {
                                            let _ = tx.send(StreamEvent::ThoughtDelta(txt.to_string()));
                                        } else {
                                            let _ = tx.send(StreamEvent::TextDelta(txt.to_string()));
                                        }
                                    }
                                } else if thought_sig.is_some() {
                                    let _ = tx.send(StreamEvent::ModelPart(ContentPart {
                                        text: None,
                                        thought: if is_thought { Some(true) } else { None },
                                        thought_signature: thought_sig,
                                        function_call: None,
                                        function_response: None,
                                        inline_data: None,
                                    }));
                                }
                            }
                        }

                        if let Some(reason) = cand.get("finishReason").and_then(|r| r.as_str()) {
                            got_finish = true;
                            let _ = tx.send(StreamEvent::Finish(reason.to_string()));
                        }
                    }
                }
            }
        }

        if !got_any_output && !got_finish {
            return Err("Empty stream output received from upstream provider".to_string());
        }

        Ok(())
    }

    async fn stream_openai(
        &self,
        model: &str,
        system_instruction: &str,
        contents: &[ChatMessage],
        tools: &[ToolDeclaration],
        tx: &mpsc::UnboundedSender<StreamEvent>,
    ) -> Result<(), String> {
        let url = format!("{}/v1/chat/completions", self.base_url);
        let mut messages = Vec::new();
        if !system_instruction.trim().is_empty() {
            messages.push(json!({
                "role": "system",
                "content": system_instruction
            }));
        }

        for msg in contents {
            let role = if msg.role == "model" { "assistant" } else { "user" };
            let mut texts = Vec::new();
            let mut images = Vec::new();
            let mut tool_calls = Vec::new();
            for p in &msg.parts {
                if let Some(ref t) = p.text {
                    if !p.thought.unwrap_or(false) && !t.is_empty() {
                        texts.push(t.clone());
                    }
                }
                if let Some(ref blob) = p.inline_data {
                    if blob.mime_type.starts_with("image/") {
                        images.push(json!({
                            "type": "image_url",
                            "image_url": {
                                "url": format!("data:{};base64,{}", blob.mime_type, blob.data)
                            }
                        }));
                    } else {
                        texts.push(format!("[Attached binary file ({})]", blob.mime_type));
                    }
                }
                if let Some(ref fc) = p.function_call {
                    tool_calls.push(json!({
                        "id": fc.id,
                        "type": "function",
                        "function": {
                            "name": fc.name,
                            "arguments": fc.args.to_string()
                        }
                    }));
                }
                if let Some(ref fr) = p.function_response {
                    let call_id = fr.get("id").and_then(|x| x.as_str()).unwrap_or("call_0");
                    let content_str = fr
                        .get("response")
                        .map(|r| r.to_string())
                        .unwrap_or_else(|| "{}".to_string());
                    messages.push(json!({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": content_str
                    }));
                }
            }
            if !texts.is_empty() || !images.is_empty() || !tool_calls.is_empty() {
                let mut m = json!({ "role": role });
                if !images.is_empty() && role == "user" {
                    let mut arr = Vec::new();
                    if !texts.is_empty() {
                        arr.push(json!({ "type": "text", "text": texts.join("\n") }));
                    }
                    arr.extend(images);
                    m["content"] = json!(arr);
                } else if !texts.is_empty() {
                    m["content"] = json!(texts.join("\n"));
                }
                if !tool_calls.is_empty() {
                    m["tool_calls"] = json!(tool_calls);
                }
                messages.push(m);
            }
        }

        let mut payload = json!({
            "model": model,
            "messages": messages,
            "stream": true
        });

        if !tools.is_empty() {
            let oai_tools: Vec<Value> = tools
                .iter()
                .map(|t| {
                    let mut schema = t.parameters_json_schema.clone();
                    sanitize_gemini_schema(&mut schema);
                    if !schema.is_object() {
                        schema = json!({ "type": "object", "properties": {} });
                    }
                    json!({
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": schema
                        }
                    })
                })
                .collect();
            payload["tools"] = json!(oai_tools);
        }

        let resp = self
            .http
            .post(&url)
            .header("Content-Type", "application/json")
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&payload)
            .send()
            .await
            .map_err(|e| format!("OpenAI connector HTTP error: {}", e))?;

        let status = resp.status();
        if !status.is_success() {
            let body = resp.text().await.unwrap_or_default();
            return Err(format!("OpenAI connector HTTP {} {}: {}", status.as_u16(), status, body));
        }

        let mut stream = resp.bytes_stream();
        let mut buf = String::new();
        let mut tc_acc: std::collections::HashMap<usize, (String, String, String)> =
            std::collections::HashMap::new();
        let mut got_any_output = false;
        let mut emitted_finish = false;

        while let Some(chunk_res) = stream.next().await {
            let chunk = chunk_res.map_err(|e| format!("SSE read error: {}", e))?;
            buf.push_str(&String::from_utf8_lossy(&chunk));

            while let Some(pos) = buf.find('\n') {
                let line = buf[..pos].trim_end_matches('\r').to_string();
                buf.drain(..=pos);
                let Some(data_str) = line.strip_prefix("data:").map(str::trim) else {
                    continue;
                };
                if data_str == "[DONE]" {
                    for (_, (id, name, args_str)) in tc_acc.drain() {
                        if !name.is_empty() {
                            got_any_output = true;
                            let args = serde_json::from_str::<Value>(&args_str).unwrap_or_else(|_| json!({}));
                            let fc = FunctionCallData { id, name, args };
                            let _ = tx.send(StreamEvent::ModelPart(ContentPart {
                                text: None,
                                thought: None,
                                thought_signature: None,
                                function_call: Some(fc.clone()),
                                function_response: None,
                                inline_data: None,
                            }));
                            let _ = tx.send(StreamEvent::ToolCall(fc));
                        }
                    }
                    if !emitted_finish {
                        let _ = tx.send(StreamEvent::Finish("STOP".to_string()));
                        emitted_finish = true;
                    }
                    continue;
                }
                let Ok(v) = serde_json::from_str::<Value>(data_str) else {
                    continue;
                };
                if let Some(err_obj) = v.get("error") {
                    let msg = err_obj
                        .get("message")
                        .and_then(|m| m.as_str())
                        .map(str::to_string)
                        .unwrap_or_else(|| err_obj.to_string());
                    let _ = tx.send(StreamEvent::Error(msg.clone()));
                    return Err(msg);
                }
                if let Some(usage) = v.get("usage") {
                    let inp = usage.get("prompt_tokens").and_then(|x| x.as_u64()).unwrap_or(0);
                    let out = usage.get("completion_tokens").and_then(|x| x.as_u64()).unwrap_or(0);
                    let tot = usage.get("total_tokens").and_then(|x| x.as_u64()).unwrap_or(inp + out);
                    let _ = tx.send(StreamEvent::Usage(TokenUsage {
                        input: inp,
                        output: out,
                        cached: 0,
                        thoughts: 0,
                        total: tot,
                    }));
                }
                if let Some(choices) = v.get("choices").and_then(|c| c.as_array()) {
                    for ch in choices {
                        if let Some(delta) = ch.get("delta") {
                            if let Some(txt) = delta.get("content").and_then(|s| s.as_str()) {
                                if !txt.is_empty() {
                                    got_any_output = true;
                                    let _ = tx.send(StreamEvent::ModelPart(ContentPart::text(txt)));
                                    let _ = tx.send(StreamEvent::TextDelta(txt.to_string()));
                                }
                            }
                            if let Some(tcs) = delta.get("tool_calls").and_then(|t| t.as_array()) {
                                for tc in tcs {
                                    got_any_output = true;
                                    let idx = tc.get("index").and_then(|i| i.as_u64()).unwrap_or(0) as usize;
                                    let entry = tc_acc.entry(idx).or_insert_with(|| {
                                        (
                                            format!("call_oai_{}", idx),
                                            String::new(),
                                            String::new(),
                                        )
                                    });
                                    if let Some(id) = tc.get("id").and_then(|s| s.as_str()) {
                                        if !id.is_empty() {
                                            entry.0 = id.to_string();
                                        }
                                    }
                                    if let Some(func) = tc.get("function") {
                                        if let Some(n) = func.get("name").and_then(|s| s.as_str()) {
                                            entry.1.push_str(n);
                                        }
                                        if let Some(a) = func.get("arguments").and_then(|s| s.as_str()) {
                                            entry.2.push_str(a);
                                        }
                                    }
                                }
                            }
                        } else if let Some(msg) = ch.get("message") {
                            if let Some(txt) = msg.get("content").and_then(|s| s.as_str()) {
                                if !txt.is_empty() {
                                    got_any_output = true;
                                    let _ = tx.send(StreamEvent::ModelPart(ContentPart::text(txt)));
                                    let _ = tx.send(StreamEvent::TextDelta(txt.to_string()));
                                }
                            }
                        }
                    }
                }
            }
        }

        // Flush any buffered tool calls on EOF if upstream closed without explicit [DONE]
        for (_, (id, name, args_str)) in tc_acc.drain() {
            if !name.is_empty() {
                got_any_output = true;
                let args = serde_json::from_str::<Value>(&args_str).unwrap_or_else(|_| json!({}));
                let fc = FunctionCallData { id, name, args };
                let _ = tx.send(StreamEvent::ModelPart(ContentPart {
                    text: None,
                    thought: None,
                    thought_signature: None,
                    function_call: Some(fc.clone()),
                    function_response: None,
                    inline_data: None,
                }));
                let _ = tx.send(StreamEvent::ToolCall(fc));
            }
        }

        // Handle non-SSE JSON response/error fallback in trailing buffer
        let tail = buf.trim();
        if !got_any_output && !tail.is_empty() {
            if let Ok(v) = serde_json::from_str::<Value>(tail) {
                if let Some(err_obj) = v.get("error") {
                    let msg = err_obj
                        .get("message")
                        .and_then(|m| m.as_str())
                        .map(str::to_string)
                        .unwrap_or_else(|| err_obj.to_string());
                    let _ = tx.send(StreamEvent::Error(msg.clone()));
                    return Err(msg);
                }
                if let Some(txt) = v
                    .get("choices")
                    .and_then(|c| c.as_array())
                    .and_then(|a| a.first())
                    .and_then(|c| c.get("message"))
                    .and_then(|m| m.get("content"))
                    .and_then(|s| s.as_str())
                {
                    if !txt.is_empty() {
                        got_any_output = true;
                        let _ = tx.send(StreamEvent::ModelPart(ContentPart::text(txt)));
                        let _ = tx.send(StreamEvent::TextDelta(txt.to_string()));
                    }
                }
            }
        }

        if !got_any_output {
            return Err("OpenAI/local inference stream returned empty output.".to_string());
        }
        if !emitted_finish {
            let _ = tx.send(StreamEvent::Finish("STOP".to_string()));
        }
        Ok(())
    }
}

/// Recursively sanitizes JSON Schema (Draft 2020-12 / MCP schemas) into Gemini OpenAPI Protobuf Schema.
/// Specifically resolves array types like `["string", "null"]`, flattens `anyOf`/`oneOf`,
/// strips unsupported draft-2020-12 keywords, and normalizes formats & required keys.
pub fn sanitize_gemini_schema(val: &mut Value) {
    let Some(obj) = val.as_object_mut() else {
        return;
    };

    // Flatten anyOf / oneOf union branches cleanly
    for union_key in ["anyOf", "oneOf"] {
        if let Some(Value::Array(variants)) = obj.remove(union_key) {
            let mut has_null = false;
            let mut chosen: Option<Value> = None;
            for item in variants {
                let is_null = item
                    .get("type")
                    .and_then(|t| t.as_str())
                    .map(|s| s.eq_ignore_ascii_case("null"))
                    .unwrap_or(false);
                if is_null {
                    has_null = true;
                } else if chosen.is_none() && item.is_object() {
                    chosen = Some(item);
                }
            }
            if has_null {
                obj.insert("nullable".to_string(), json!(true));
            }
            if let Some(mut first) = chosen {
                sanitize_gemini_schema(&mut first);
                if let Some(first_map) = first.as_object() {
                    for (k, v) in first_map {
                        if !obj.contains_key(k) {
                            obj.insert(k.clone(), v.clone());
                        }
                    }
                }
            }
        }
    }

    // Strip JSON Schema keywords rejected by Gemini/CloudCode protobuf Schema
    for unsupported in [
        "$schema",
        "$id",
        "$defs",
        "definitions",
        "$ref",
        "additionalProperties",
        "title",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "default",
        "patternProperties",
        "unevaluatedProperties",
        "const",
        "examples",
        "annotations",
        "readOnly",
        "writeOnly",
        "deprecated",
        "contentEncoding",
        "contentMediaType",
    ] {
        obj.remove(unsupported);
    }

    // Convert array `"type": ["string", "null"]` -> `"type": "string", "nullable": true`
    if let Some(t_val) = obj.get("type").cloned() {
        match t_val {
            Value::Array(arr) => {
                let mut picked: Option<String> = None;
                let mut has_null = false;
                for item in arr {
                    if let Some(s) = item.as_str() {
                        if s.eq_ignore_ascii_case("null") {
                            has_null = true;
                        } else if picked.is_none() {
                            picked = Some(s.to_ascii_lowercase());
                        }
                    }
                }
                obj.insert(
                    "type".to_string(),
                    json!(picked.unwrap_or_else(|| "string".to_string())),
                );
                if has_null {
                    obj.insert("nullable".to_string(), json!(true));
                }
            }
            Value::String(s) => {
                let lower = s.to_ascii_lowercase();
                if lower == "null" {
                    obj.insert("type".to_string(), json!("string"));
                    obj.insert("nullable".to_string(), json!(true));
                } else {
                    obj.insert("type".to_string(), json!(lower));
                }
            }
            _ => {
                obj.insert("type".to_string(), json!("string"));
            }
        }
    }

    // Normalize format strings accepted by Gemini OpenAPI schema
    if let Some(fmt) = obj.get("format").and_then(|v| v.as_str()).map(|s| s.to_string()) {
        match fmt.as_str() {
            "uint" | "uint64" => {
                obj.insert("format".to_string(), json!("int64"));
            }
            "uint32" => {
                obj.insert("format".to_string(), json!("int32"));
            }
            "int32" | "int64" | "float" | "double" | "date-time" | "enum" => {}
            _ => {
                obj.remove("format");
            }
        }
    }

    // Ensure enum elements are strings
    if let Some(Value::Array(enum_arr)) = obj.get_mut("enum") {
        for item in enum_arr.iter_mut() {
            if !item.is_string() {
                *item = json!(item.to_string());
            }
        }
    }

    // Recurse into properties and ensure required keys match existing properties
    let mut prop_keys = std::collections::HashSet::new();
    if let Some(Value::Object(props)) = obj.get_mut("properties") {
        for (k, v) in props.iter_mut() {
            prop_keys.insert(k.clone());
            sanitize_gemini_schema(v);
        }
    }
    if obj.get("type").and_then(|v| v.as_str()) == Some("object") && !obj.contains_key("properties") {
        obj.insert("properties".to_string(), json!({}));
    }
    if let Some(Value::Array(req)) = obj.get_mut("required") {
        req.retain(|v| v.as_str().map(|s| prop_keys.contains(s)).unwrap_or(false));
        if req.is_empty() {
            obj.remove("required");
        }
    }

    // Recurse into array items
    if let Some(items) = obj.get_mut("items") {
        sanitize_gemini_schema(items);
    } else if obj.get("type").and_then(|v| v.as_str()) == Some("array") {
        obj.insert("items".to_string(), json!({ "type": "string" }));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sanitizes_downflow_mcp_array_types_and_draft2020_keywords() {
        let mut schema = json!({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "file_name": {
                    "description": "File name",
                    "type": ["string", "null"]
                },
                "limit": {
                    "description": "Limit",
                    "format": "uint",
                    "minimum": 0,
                    "type": ["integer", "null"]
                },
                "later": {
                    "default": false,
                    "type": "boolean"
                },
                "url": {
                    "type": "string"
                }
            },
            "required": ["url", "nonexistent"]
        });

        sanitize_gemini_schema(&mut schema);

        assert!(schema.get("$schema").is_none());
        let props = schema.get("properties").and_then(|p| p.as_object()).unwrap();
        assert_eq!(props["file_name"]["type"], json!("string"));
        assert_eq!(props["file_name"]["nullable"], json!(true));
        assert_eq!(props["limit"]["type"], json!("integer"));
        assert_eq!(props["limit"]["format"], json!("int64"));
        assert_eq!(props["limit"]["nullable"], json!(true));
        assert!(props["later"].get("default").is_none());
        assert_eq!(schema["required"], json!(["url"]));
    }

    #[test]
    fn flattens_anyof_nullable_schema() {
        let mut schema = json!({
            "anyOf": [
                { "type": "integer", "minimum": 1 },
                { "type": "null" }
            ],
            "description": "Optional integer"
        });
        sanitize_gemini_schema(&mut schema);
        assert!(schema.get("anyOf").is_none());
        assert_eq!(schema["type"], json!("integer"));
        assert_eq!(schema["nullable"], json!(true));
        assert_eq!(schema["minimum"], json!(1));
    }

    #[test]
    fn classifies_retryable_connector_transport_errors() {
        assert!(ConnectorClient::is_retryable_connector_error(
            "Connector HTTP error: error sending request for url (http://127.0.0.1:9099/v1beta/models/gemini-3.8-flash-high:streamGenerateContent?alt=sse)"
        ));
        assert!(ConnectorClient::is_retryable_connector_error("SSE stream read error: unexpected EOF"));
        assert!(ConnectorClient::is_retryable_connector_error("OpenAI connector HTTP error: connection reset by peer"));
        assert!(ConnectorClient::is_retryable_connector_error("Connector HTTP 503 Service Unavailable"));
        assert!(!ConnectorClient::is_retryable_connector_error("Connector HTTP 400 Bad Request: INVALID_ARGUMENT"));
        assert!(!ConnectorClient::is_retryable_connector_error("Proto field unknown: Unknown name 'foo'"));
    }
}

