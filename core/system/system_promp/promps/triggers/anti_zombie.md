# 🧟 Anti-Zombie Code, Zero-Backup & Orphan Cleanup Mandate
- **Dead Code Audit:** Following any refactoring or architectural update, inspect and purge all unused functions, imports, variables, and deprecated shims.
- **Strict Zero-Backup Mandate:** NEVER create `.bak`, `.orig`, `.old`, `*.backup`, or duplicate config files anywhere in `/opt/floworkos`, `/home`, or repository roots. Backup files cause critical context contamination, prompting AI agents and tools to revert active implementations back to stale legacy states. Version control belongs exclusively to Git.
- **Orphan & Zombie Eradication:** Clean up temporary test files, old scratch buffers, orphaned configs, and zombie processes immediately upon discovery.
- **Zero Drift:** Maintain zero ghost code and clean git diffs passing Exit Code 0.
