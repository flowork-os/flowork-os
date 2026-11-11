# 💬 FLOWORK OS — EPISODIC CHAT HISTORY & SESSION VAULT SPECIFICATION

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/history/chats/` (System Vault) & `$HOME/.flowork/history/chats/` (User Runtime)  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

## 1. Executive Philosophy

Flowork OS persists every autonomous reasoning trajectory, tool call, multimodal blob metadata, token ledger, and compression checkpoint in an **append-only streaming JSONL ledger** implemented natively in `mrflow-rs/src/session/mod.rs`.

Rather than truncating conversation history destructively when context grows large, **Mr. Flow** appends compact snapshot records (`compression_snapshot`) while keeping every original historical turn intact on disk for forensic inspection, sidebar rendering, and exact checkpoint restoration.

---

## 2. Storage Path Resolution & Portability

Path resolution in `mrflow-rs/src/config/mod.rs` separates shared system templates/vault storage from per-user active runtime persistence:

| Storage Layer | Path / Resolution Rule | Purpose |
| :--- | :--- | :--- |
| **Canonical OS Vault** | `/opt/floworkos/history/chats/` | Shared system chat vault (`chmod 0777` for multi-user / Live ISO portability), containing `.gitignore`, `.gitkeep`, and workspace transcripts such as `floworkos/`. |
| **Explicit Override** | `$FLOWORK_HISTORY_DIR` | Environment override redirecting `AppPaths.history_chats_dir` to a custom vault path (such as `/opt/floworkos/history/chats`). |
| **Default User Vault** | `$HOME/.flowork/history/chats/` | Default runtime ledger directory when `FLOWORK_HISTORY_DIR` is unset. |
| **Checkpoints Store** | `$HOME/.flowork/history/checkpoints/<project_slug>/` | Tagged full-history JSON snapshots saved via `SessionVault::save_checkpoint`. |
| **Latest Session Link** | `$HOME/.flowork/history/latest_session` | Runtime symlink maintained outside `/opt/floworkos/` internal symlinks, pointing to the most recent active `.jsonl` file. |

### Project Slug Partitioning
Conversations are partitioned under `<history_chats_dir>/<project_slug>/`.  
`resolve_project_slug(cwd, user_flowork_dir)` inspects `$HOME/.flowork/projects.json` for an exact or longest-prefix path match (falling back to the sanitized directory basename of `cwd`, e.g. `floworkos`).

```text
/opt/floworkos/history/chats/
├── floworkos/
│   └── session-2026-11-11T23-03-af7dde18.jsonl
├── .gitignore
├── .gitkeep
└── README.md
```

---

## 3. Streaming JSONL Ledger Schema

Each session file (`session-YYYY-MM-DDTHH-MM-<short8>.jsonl`) is strictly newline-delimited JSON (`SessionVault` in `mrflow-rs/src/session/mod.rs`):

| Record Type | Trigger / Method | Key Fields |
| :--- | :--- | :--- |
| **Header Line** | `SessionVault::open_or_create` | `sessionId`, `projectHash`, `startTime`, `lastUpdated`, `kind: "main"` |
| **User Turn / Tool Output** | `append_user_prompt` / `append_tool_responses` | `id`, `timestamp`, `type: "user"`, `content: ContentPart[]` |
| **Model Turn** | `append_model_turn` | `id`, `timestamp`, `type: "gemini"`, `content`, `thoughts`, `tokens`, `model`, `rawParts`, optional `toolCalls` |
| **Compression Snapshot** | `append_compression_snapshot` | `id`, `timestamp`, `type: "compression_snapshot"`, `snapshot`, `preservedTail`, `originalTokenCount`, `newTokenCount` |
| **Incremental Patch** | `touch_updated` / `append_summary` | `{"$set": {"lastUpdated" \| "summary": ...}}` |
| **Rewind Marker** | `append_rewind` | `timestamp`, `{"$rewind": {"keepCount": N}}` |

### Lossless Resume & Replay Semantics (`load_jsonl_session`)
When `mrflow --resume` loads a `.jsonl` transcript:
1. All original `"user"` and `"gemini"` records remain preserved in order on disk.
2. Encountering `"type": "compression_snapshot"` resets active replay history to the synthesized compressed state anchor plus `preservedTail`, minimizing prompt tokens on resume while retaining full raw audit logs above the anchor line.
3. Encountering `"$rewind"` truncates reconstructed replay history to `keepCount`.
4. Internal `<session_context>` wrapper text is skipped during history replay so stale environment dumps are never re-injected into new turns.
5. Note: `/usr/local/bin/flowork-sysd` also maintains a lightweight SQLite REST store (`chat_store.rs`, `/api/agent/chat/history` & `/api/agent/chat/message`) for desktop widget integrations on port `18090`.

---

## 4. CLI Session Management Commands

Defined in `mrflow-rs/src/cli/mod.rs`:

```bash
# List all recorded sessions for the current workspace
mrflow --list-sessions

# Resume the latest session in the current workspace
mrflow --resume latest

# Resume by numeric list index or session UUID
mrflow --resume <index|uuid>

# Open an explicit session JSON/JSONL ledger file directly
mrflow --session-file /opt/floworkos/history/chats/floworkos/session-2026-11-11T23-03-af7dde18.jsonl

# Start a session pinned to a caller-supplied UUID
mrflow --session-id <uuid>

# Delete a recorded session by index or session ID
mrflow --delete-session <index|uuid>
```

---

## 5. Multi-User Portability & Hygiene Invariants

1. **Zero Hardcoded Home Paths:** Never hardcode `/home/<username>` inside configs or session tools; always resolve `$HOME` or `$FLOWORK_HISTORY_DIR`.
2. **Safe JSONL Validation:** All lines inside active `.jsonl` files must remain valid standalone JSON objects; partial manual edits break append integrity.
3. **Directory Permissions:** `/opt/floworkos/history/chats/` retains `0777` permissions and `.gitignore`/`.gitkeep` hygiene markers for clean ISO mastering.
