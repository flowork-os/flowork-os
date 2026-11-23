# Context & Activation Scope
Active when inspecting, parsing, generating, or converting multi-format documents (`PDF`, `DOCX`, `PPTX`, `Markdown`, `RTF`), presentations, and complex file payloads.

# Mandatory Behavioral Invariants
1. **Pre-Flight Structural Inspection:** Perform content inventory before parsing (page count, vector text layers vs scanned bitmap, font embedding). Inspect headers/metadata first rather than blindly streaming giant binary files into memory.
2. **Spatial Layout & Tabular Preservation:** When extracting or rendering tables and forms, preserve column alignment and hierarchical headers rather than flattening into unreadable raw text strings.
3. **Typographic Hierarchy & Flow:** Enforce consistent document margins, explicit typographic scales, orphan/widow suppression, and universal page numbering (`Page X of Y`).
4. **Universal Output Destination:** All generated documents, reports, presentations, and PDFs MUST target `/opt/floworkos/documents/` (mirrored to `$HOME/Documents/`).

# Strict Prohibitions
- PROHIBITED: Dumping unparsed binary or 50MB+ file contents directly into chat or context buffers.
- PROHIBITED: Hardcoding artificial page breaks that sever paragraphs or leave orphan headers.
- PROHIBITED: Outputting generated documents outside `/opt/floworkos/documents/`.
