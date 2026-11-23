# 👑 PASSIVE TRIGGER: REAL-BROWSER QA & LIVE REPRODUCTION

## 1. Scope & Activation
Triggered when verifying web applications, testing browser sessions, auditing DOM elements, or reproducing UI bugs (`browser_qa`, `dom_testing`, `reproduction`, `devtools_audit`, `visual_verification`, `e2e_testing`, `live_probe`, `cdp_inspection`).

## 2. Mandatory QA Invariants
1. **Zero Assumption Protocol:** Never assume a frontend or web application works based on source code alone. Always execute the real browser via `run_shell_command` with `flowork-launch <app>` or use native Flowork browser tools (`browser_navigate_page`, `browser_click`, `browser_take_screenshot`, `take_screenshot`).
2. **Deterministic Step Reproduction:** Reproduce user-reported bugs step-by-step. Document the exact sequence of clicks, inputs, network responses, and console outputs.
3. **Empirical Visual Verification:** Capture desktop or viewport screenshots as indisputable proof of operational success. Inspect rendered geometry, text clipping, and modal responsiveness.
4. **Console & Network Cleanliness:** A verification pass is invalid if unhandled JavaScript console exceptions or broken HTTP 4xx/5xx network requests remain unresolved.
