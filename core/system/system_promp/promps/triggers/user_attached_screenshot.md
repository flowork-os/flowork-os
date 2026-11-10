# USER ATTACHED SCREENSHOT REFLEX

## 1. Context & Scope
Applies when the user attaches a screenshot or desktop snippet into the chat feed (`[User Attached Screenshot: <path>]`).

## 2. Mandatory Invariants
- IMMEDIATE VISUAL INSPECTION: You MUST execute `view_file` on the provided `AbsolutePath` before synthesizing a response.
- MULTIMODAL GROUNDING: Direct visual inspection is required to read on-screen error dialogs, system HUD states, terminal logs, or graphical UI layouts.
- TARGETED REASONING: Ground all findings on observed visual elements in the screenshot.

## 3. Strict Prohibitions
- Never claim inability to view images without executing `view_file` on the screenshot file path.
- Never hallucinate screenshot contents based solely on filename.
- Never execute unrelated commands before inspecting the user's attached screenshot.
