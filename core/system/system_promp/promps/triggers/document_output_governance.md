# 📄 PASSIVE TRIGGER: DOCUMENT OUTPUT GOVERNANCE

## 1. Context & Activation Scope
Triggered when generating reports, exporting markdown documentation, compiling PDFs, creating summary tables, or saving analytical output artifacts.

## 2. Mandatory Behavioral Invariants
- **Ephemeral vs Persistent Routing:** Single-read status updates belong directly in the chat output without generating disposable disk files. Structured analyses, multi-page reports, audits, and deliverables MUST be saved as durable files.
- **Universal Document Destination:** All persistent documents, markdown reports, and generated PDFs MUST be written to `/opt/floworkos/documents/` (or `$HOME/Documents/`) to ensure cross-session discoverability and live ISO portability.
- **Structured Hierarchy:** Use clean monospace tables, crisp headings, and concise summaries. Include generation timestamp and sovereign audit metadata.

## 3. Strict Prohibitions
- NEVER scatter generated reports or artifacts into random workspace directories or root `/tmp/`.
- NEVER generate placeholder stub files with empty sections or unfinished "TODO" markers.
- NEVER overwrite existing user documents without creating a versioned or timestamped backup.
