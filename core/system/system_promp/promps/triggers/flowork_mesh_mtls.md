# FLOWORK MESH ZERO-TRUST mTLS P2P COMPUTE

## 1. Context & Activation Scope
Activate when configuring, extending, debugging, or auditing `/opt/floworkos/bin/flowork-mesh`, `/opt/floworkos/policies/mesh.toml`, `flowork-pipe-rs --target @peer`, Neural Bus `hardware` telemetry on `:18095/api/bus/apps`, or mTLS P2P inference/media offload.

## 2. Mandatory Behavioral Invariants
- Keep Zero-Trust defaults intact in `/opt/floworkos/policies/mesh.toml`: `enabled_by_default = false`, `require_mtls = true`, `allow_shell = false`, and explicit `allow_media_cli` whitelisting.
- Require mutual Ed25519 Root CA verification (`WebPkiClientVerifier`) on `tokio-rustls` `/mesh/v1/*` endpoints and `0o600` permissions on `ca.key`/`node.key`.
- When running whitelisted CLIs inside `flowork-sandbox-exec` (`api_job`), canonicalize `resolved_cli` and grant only `job_dir`, the CLI parent directory, and `/opt/floworkos/apps/<app>` in `read_paths`—never pass wholesale `/opt/floworkos` because `hard_deny_invariants` blocks ancestors of `connector/data`.
- Keep flag parsing (`--check`, `--help`, `-h`, `--json`) restricted to tokens before `--` in both `flowork-mesh` and `flowork-sandbox-exec` so proxied CLI arguments pass cleanly.
- Use `zstd` (`-q` without `-z` on decompress) and JSON `.pairing_pin` schema consistently across pairing, workspace offload, and artifact return.

## 3. Strict Prohibitions
- Never enable `flowork-mesh serve` automatically at boot on fresh Live ISOs or allow arbitrary remote shell (`bash`/`sh`/`python3`) execution over the mesh.
