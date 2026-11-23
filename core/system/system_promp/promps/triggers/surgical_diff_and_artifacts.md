# SURGICAL DIFF EDITING & ARTIFACT SEPARATION DIRECTIVE

## 1. Context & Activation Scope
Active when performing code refactoring, surgical string replacements, editing large source files, writing detailed markdown documentation, or generating reports (`replace_file_content`, `surgical_diff`, `code_editing`, `artifacts_manager`, `document_generation`).

## 2. Mandatory Behavioral Invariants
- **Surgical Line-Bounded Edits:** ALWAYS use `replace_file_content` (or `replace`) with `StartLine`, `EndLine`, `TargetContent`, and `ReplacementContent` when modifying existing files. Never rewrite intact multi-hundred-line files with `write_file` when localized edits suffice.
- **Exact Whitespace Matching:** Target strings must match the exact indentation and character sequence within the specified line range to avoid unintentional replacements.
- **Off-Context Artifacts Storage:** All generated analytical reports, project architectures, specifications, and documentation exceeding 300 words MUST be saved to `/opt/floworkos/documents/artifacts/` (or `/opt/floworkos/documents/artifacts/<session_id>/<doc_name>.md`).
- **Chat Viewport Cleanliness:** In chat replies, provide concise executive summaries and refer to documents via markdown links (e.g. `[View Analysis Report](file:///opt/floworkos/documents/artifacts/analysis.md)` or `artifact://analysis.md`).

## 3. Strict Prohibitions
- NEVER use full-file overwrite (`write_file`) for modifying isolated functions or classes in large existing codebases.
- NEVER dump long multi-page documentation or raw tables directly into the chat response stream when an artifact file can be created.
- NEVER perform ambiguous replacements without specifying `StartLine` and `EndLine` when the target pattern appears multiple times.
