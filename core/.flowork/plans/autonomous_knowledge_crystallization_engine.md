# Implementation Plan: Autonomous Knowledge Crystallization Engine (Option A)

## Objective
Implement an autonomous, deterministic Knowledge Crystallization Engine for Mr. Flow (`mrflow-crystallize`) that converts newly resolved incidents and operational doctrines into compiled native Rust sensors (`rules/.bin/<name>`), compact conditional triggers (`promps/triggers/<name>.md`, <250 words), and registry entries in `triggers.json`, ensuring 100% just-in-time injection with zero token bloat on quiescent turns.

## Key Files & Context
- `/opt/floworkos/bin/mrflow-crystallize`: Master CLI executable utility for Mr. Flow to invoke upon resolving any new incident.
- `/opt/floworkos/tools/crystallize/manifest.json`: Tool manifest for dynamic agent discovery and routing via `router.js`.
- `/opt/floworkos/tools/crystallize/crystallize.js`: Core implementation script executed by the CLI and tool interface.
- `/opt/floworkos/system/system_promp/promps/triggers/`: Target storage for conditional prompt files (<250 words, 3-section format).
- `/opt/floworkos/system/system_promp/rules/`: Target storage for native Rust sensor sources (`<name>.rs`).
- `/opt/floworkos/system/system_promp/rules/.bin/`: Target storage for compiled sensor binaries (<1ms evaluation, Exit Code 0/1).
- `/opt/floworkos/system/system_promp/triggers.json` & `/opt/floworkos/system/system_promp/promps/triggers.json`: Central prompt matrix registries.

## Implementation Steps
1. **Author the Crystallization Engine Core (`/opt/floworkos/tools/crystallize/crystallize.js`):**
   - Implement argument parser supporting `--name`, `--title`, `--description`, `--prompt`, `--keywords`, `--events`, `--targets`, `--dry-run`, and `--test`.
   - Enforce the 250-word hard limit and 3-section structure (`Context & Activation Scope`, `Mandatory Behavioral Invariants`, `Strict Prohibitions`).
   - Implement native Rust sensor code generator emitting memory-efficient string matching against `FLOWORK_USER_MSG`, `FLOWORK_ACTIVE_EVENTS`, and `FLOWORK_TARGET_FILE`.
   - Invoke `rustc -O` to compile the sensor into `rules/.bin/<name>` and verify file execution permissions (`chmod 755`).
   - Implement atomic JSON modification for `/opt/floworkos/system/system_promp/triggers.json` and `/opt/floworkos/system/system_promp/promps/triggers.json` with automatic backup and rollback on compilation/validation failure.
   - Run verification probe: execute the compiled binary under matching environment variables (expect Exit Code 0) and non-matching variables (expect Exit Code 1).
2. **Deploy Sovereign CLI Executable (`/opt/floworkos/bin/mrflow-crystallize`):**
   - Create executable wrapper in `/opt/floworkos/bin/mrflow-crystallize` and ensure executable permissions (`chmod +x`).
3. **Register Tool Descriptor (`/opt/floworkos/tools/crystallize/manifest.json`):**
   - Register tool manifest with explicit triggers, keywords, parameter validation, and Landlock/sandbox permissions.
4. **Author End-to-End Verification Test (`/opt/floworkos/system/system_promp/test_crystallize.sh`):**
   - Author empirical test script verifying prompt generation, word count check, Rust compilation, sensor exit code verification (0 on match, 1 on mismatch), and router discovery.
   - Execute the test and assert Exit Code 0.

## Verification & Testing
- Run empirical end-to-end test with a sample crystallization directive.
- Verify that the generated Rust binary compiles cleanly with `rustc 1.99.1`.
- Verify the sensor binary returns `Exit Code 0` when target keywords/events match.
- Verify the sensor binary returns `Exit Code 1` when quiescent (unrelated input).
- Verify `router.js` successfully scores and matches the new trigger.
- Clean up test artifacts and confirm system integrity.
