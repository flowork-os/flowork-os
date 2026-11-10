# TOOL STAGE ISOLATION & COMPACT TERMINAL LOG ARCHITECTURE

## 1. Context & Activation Scope
Applies when maintaining or modifying Mr. Flow sidebar UI, execution focus stage, tool lifecycle display, chat history visibility during execution, or post-turn tool summaries.

## 2. Mandatory Behavioral Invariants
- ZERO CHAT IN STAGE: While any tool or thought is active, `#executionFocusStage` has 100% viewport focus. `document.body` MUST have `in-stage-mode` class.
- CSS ENFORCEMENT: Enforce `body.in-stage-mode #chatContainer { display: none !important; }` and `.sovereign-task-hud { display: none !important; }`. Never set `chat.style.display = "block"` in `showSovereignTaskHud`.
- DYNAMIC REPLACEMENT: When consecutive tools run in a loop, `openExecutionStage` dynamically updates the viewport body, replacing the previous tool immediately.
- COMPACT CHAT LOGS: Tool history in chat MUST use native `<details class="tool-exec-log">` (collapsed by default).
- ZERO HEAVY CARDS IN CHAT: Post-turn history rows MUST be minimal monospace CLI logs (`✓ toolName target (time)`). Never inject canvas visualizers or heavy GUI cards into chat bubbles.
- RETURN TO STAGE: If the user toggles history during execution, provide `#stageReturnBanner` and `btnScrollToActiveTask` to return to the active stage instantly.

## 3. Strict Prohibitions
- Never allow `#chatContainer` and `#executionFocusStage` to be visible simultaneously (split layout).
- Never render uncollapsed or heavy GUI components inside chat history bubbles.
- Never write inline styles that override `body.in-stage-mode` isolation.
