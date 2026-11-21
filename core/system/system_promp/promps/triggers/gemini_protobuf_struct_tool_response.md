# GEMINI PROTOBUF STRUCT TOOL RESPONSE INVARIANT

## 1. Context & Activation Scope
Triggered when developing, modifying, or auditing `mrflow-rs` (engine, tools, context, inference) or `flowork-connector` (proxy, translator), specifically when handling tool outputs, chat history serialization, or Gemini REST/Protobuf payloads.

## 2. Mandatory Architectural Invariants
- **Protobuf Struct Object Enforcement:** Under Google Gemini API, `functionResponse.response` strictly requires a `google.protobuf.Struct` (JSON Object `{ ... }`). Primitive values (`String`, `Array`, `Number`, `Boolean`, `Null`) at the root level of `response` trigger fatal `HTTP 400 Bad Request: Invalid value at request.contents[N].parts[0].function_response.response`.
- **Pre-Serialization Normalization:** In `mrflow-rs` (`ContentPart::function_response`, `ToolExecOutcome::ok_json`, and `exec_disk_tool`), always ensure tool outputs are normalized to `Value::Object`. If a tool emits a JSON-stringified object, unescape and parse it into an object; otherwise, wrap raw primitives into `{ "output": ... }`.
- **Dual-Layer Gateway Sanitization:** In `flowork-connector` (`proxy.rs` and `translator.rs`), unconditionally sanitize outgoing `contents` turns via `merge_adjacent_same_role` before forwarding to Google CloudCode. Any non-object `response` must be parsed or wrapped on the fly to heal historical disk sessions.

## 3. Strict Prohibitions
- Never allow raw strings or primitive scalars into `function_response.response`.
- Never bypass `sanitize_function_responses` during context preparation (`prepare_history_for_api`).
