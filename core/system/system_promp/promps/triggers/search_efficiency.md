# 🔍 Search & Context Optimization
- **Scoped Searching:** Use conservative `total_max_matches` and specific `include_pattern` to avoid dumping massive outputs into context.
- **Parallel Read/Search:** Combine search and read operations in parallel turns. Request sufficient surrounding context to avoid extra turns.
- **Selective Reading:** For large files, use `start_line` and `end_line` ranges rather than full-file dumps.
- **Unambiguous Edits:** Ensure search matches provide enough context so file replacement strings match uniquely.
