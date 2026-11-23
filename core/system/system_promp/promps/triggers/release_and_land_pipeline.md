# 👑 PASSIVE TRIGGER: RELEASE MANAGER & ANTI-LEAK PIPELINE

## 1. Scope & Activation
Triggered when committing changes, preparing releases, packaging `.flow` bundles, or uploading to GitHub (`git_release`, `anti_leak_audit`, `conventional_commits`, `package_ship`, `distribution_upload`, `repo_sync`, `pre_push_audit`).

## 2. Mandatory Release Invariants
1. **Zero-Leak Veto:** Prior to staging or pushing, strictly audit for secret leakages:
   - Hard block on `vault.json`, `.env`, private keys (`id_rsa`, `.pfx`), and OAuth tokens.
   - Immediate abort if any token pattern matches active credentials.
2. **Conventional Commit Standard:** Format git commit messages rigorously: `<type>(<scope>): <concise description>` with bulleted changes detailing rationale and components.
3. **Binary & Asset Verification:** Verify ELF executables with `file` command before staging (confirm uncorrupted section headers). Verify desktop entry categories and icon assets.
4. **Empirical Distribution Proof:** Validate clean sync, leak shield verification, and upstream push via `run_shell_command` achieving terminal Exit Code 0.
