# Tools

Generated from the MCP server's tool list by `tests/tools.rs`; do not edit by hand (`UPDATE_TOOLS_DOC=1 cargo test --test tools` rewrites it). Every tool is also a CLI command with the same options.

## Analyze repository

Tool `analyze` · CLI `rust-anything analyze`

Map a repository (TypeScript/JavaScript, Python, C, Go, Ruby or Java): units, port order (waves), risks with file:line, bridge per unit, dependency-to-crate fit, and `start_here`: the best first ports.

Read-only.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `root` | string | yes | Repository root. |
| `lang` | string |  | Source language; detected from the repository when omitted. |
| `whole_app` | boolean |  | Plan a whole-app port: entry points and shape (cli, server, library), every dependency imported or declared with its crate and fit, pieces in port order (units that import each other together), and numbered decisions with a recommended answer for the grilling round. |

## Scaffold unit crate

Tool `bridge` · CLI `rust-anything bridge`

Scaffold a Rust crate for one unit: napi-rs or wasm-bindgen bindings in src/lib.rs, stubs to port in src/port.rs, UTF-16 helpers when the unit uses string offsets. Never overwrites an existing folder.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `root` | string | yes |  |
| `unit` | string | yes | Unit id from analyze. |
| `kind` | string |  | Defaults to the plan's bridge. |
| `out` | string |  | Crate folder; defaults to <root>/rust/<name>. |
| `name` | string |  | Crate name; defaults to `<unit>-rs`. |
| `force` | boolean |  | Bridge a unit the plan marks blocked or keep. |
| `keep` | string[] |  | Exports to keep in the source language: `name` or `name: reason`. |
| `batch` | string[] |  | Batch classes, `function:param`: the function runs over many `param` values kept in Rust, on all cores, in one call. A `<Function>Index` struct in port.rs replaces the default per-item loop. |

## Regenerate bindings

Tool `refresh` · CLI `rust-anything refresh`

Regenerate a crate's bindings (lib.rs, index.cjs, js.rs) from the signatures in src/port.rs, after changing them, adding any new batch classes. Never touches port.rs.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |
| `batch` | string[] |  | Batch classes to add, `function:param`: the function runs over many `param` values kept in Rust, on all cores, in one call. A `<Function>Index` struct in port.rs replaces the default per-item loop. |

## Record original behavior

Tool `record` · CLI `rust-anything record`

Run the original functions on generated edge-case inputs (non-ASCII, emoji, -0, NaN, ...) plus optional extra inputs, and save the results as cases.jsonl: the behavior the port must match.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |
| `count` | integer |  | Generated cases per function (default 200). |
| `inputs` | string |  | JSONL file of extra cases: {"fn": name, "args": [...]}. |
| `module` | string |  | JS only: import the original from this JS module instead of the TS source. |
| `resolve_from` | string |  | Resolve npm packages from this folder's node_modules. |
| `float_tolerance` | number |  | Numeric code: floats match when they differ by at most this times the larger magnitude (absolute below 1), e.g. 1e-9. Saved with the crate for diff and gate; 0 removes it. |
| `node_args` | string[] |  | Extra arguments for node, e.g. ["--import=tsx"]. |
| `test_command` | string[] |  | TS/JS or Python: also record every call the original's own test suite makes to the unit's functions, e.g. ["npx", "jest"] or ["pytest"]. Runs in the original's folder. |

## Build crate

Tool `build` · CLI `rust-anything build`

Build the crate: the napi-rs .node, wasm-bindgen output, Python extension or shared library.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |

## Diff port against recording

Tool `diff` · CLI `rust-anything diff`

Replay cases.jsonl against the built Rust module and list mismatches.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |
| `ignore_key_order` | boolean |  |  |
| `module` | string |  | Test this JS module instead of the crate's `index.cjs`. |
| `node_args` | string[] |  | Extra arguments for node, e.g. ["--import=tsx"]. |
| `float_tolerance` | number |  | Floats match within this tolerance for this run (the one saved by record otherwise). |

## Profile workload

Tool `profile` · CLI `rust-anything profile`

Run a real workload (a command: node or python3 script, `go test -bench`, java, ruby) under the language's profiler and rank the repository's hot functions by inclusive time, with their callers, call counts and advice: what to port together, and which loops to batch (`bridge` with `batch`). Profile before porting: leaf functions called one at a time are slower in Rust.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `root` | string | yes |  |
| `command` | string[] | yes | The workload, run in root: ["node", "bench.mjs"]. |
| `lang` | string |  | Detected from the repository when omitted. |

## Benchmark port

Tool `bench` · CLI `rust-anything bench`

Time the recorded cases on the original and on the built Rust module, bridge included; speedup below 1 means the port is slower as its callers call it. Returns the rows and a verdict with advice: ship, keep the slower functions, or port a bigger unit.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |
| `resolve_from` | string |  |  |
| `min_ms` | integer |  | Minimum measured time per function and side, in milliseconds (default 200). |
| `node_args` | string[] |  | Extra arguments for node, e.g. ["--import=tsx"]. |

## Generate shadow module

Tool `shadow` · CLI `rust-anything shadow`

Generate a drop-in shadow (a TS or Python module, Go package, Ruby file, Java classes or C file) that runs the original and the Rust port side by side and reports mismatches; RUST_ANYTHING_MODE=old|shadow|new switches at runtime.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |
| `out` | string |  |  |

## Check definition of done

Tool `gate` · CLI `rust-anything gate`

Definition of done: fmt, clippy -D warnings, cargo test, unsafe with SAFETY comments only, no unimplemented functions, build, API present, recorded behavior matches.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `crate` | string | yes | Folder of the generated crate (holds rust-anything.json). |
| `node_args` | string[] |  | Extra arguments for node, e.g. ["--import=tsx"]. |

## Record whole app

Tool `app_record` · CLI `rust-anything app record`

Record the whole CLI app's behavior: run the original on its own documented examples, an inputs file and semantic traps (non-ASCII and emoji, negative division, overflow, float extremes, map order), twice each. What differs between runs is reported by kind in `noise`: values (now [..] wildcards), order (lines compared in any order) and lines (a ... that matches anything): show every one to the user. Cases are trycmd files in <repo>/rust/app-cases/ (argv, stdin, env, files in; stdout, stderr, exit code, files out).

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `repo` | string | yes | Repository root. |
| `run` | string[] |  | Command that runs the original, paths relative to repo: ["python3", "cli.py"]. Optional after the first record. |
| `inputs` | string |  | JSONL of extra cases: {"name", "args": [...], "stdin", "env": {...}, "files": {path: text}}. |
| `normalize` | string[] |  | Normalizers: timestamps, uuids, key-order, or name=regex. |
| `name` | string |  | Name the app is invoked by in its docs. |
| `timeout` | integer |  | Seconds before a run is killed (default 30). |
| `traps` | boolean |  | Add semantic-trap cases (default true). |
| `http` | boolean |  | The app is a server: `run` starts it (it takes its port from PORT or {port}); cases are requests from curl lines in its docs, `inputs` ({"name", "method", "path", "headers", "body"}) and traps. |
| `port` | integer |  | A port the server always listens on (implies http). |
| `float_tolerance` | number |  | Numeric output: numbers match when they differ by at most this times the larger magnitude (absolute below 1), e.g. 1e-9. Saved with the cases; 0 removes it. |

## Replay app cases

Tool `app_replay` · CLI `rust-anything app replay`

Replay <repo>/rust/app-cases/ against a build (the original, the front door, the final Rust binary): passed/total, fallback rate when the build reports it, and a report with a diff per failing case (rust/app-cases/replay-report.md).

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `repo` | string | yes | Repository root. |
| `build` | string |  | Command line of the build to test; the original when omitted. |
| `port` | integer |  | Servers: the port the build always listens on; otherwise it gets a free one through PORT and {port}. |
| `timeout` | integer |  | Seconds before a run is killed (default 30). |
| `case` | string |  | Replay only this case, by the name the report gives it (a library: only this unit): the fast loop for fixing one mismatch. |

## Scaffold Rust front door

Tool `app_front_door` · CLI `rust-anything app front-door`

Scaffold <repo>/rust/app, the Rust binary that owns the CLI's entry point: a clap parser for the recorded commands and flags, every command running the original with the same argv, stdin and env (each fallback counted). For a server: an axum app that starts the original on a port of its own and proxies every route no unit answers. Builds it and replays the cases: 100% passed at 100% fallback. Needs app_record first; never overwrites rust/app.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `repo` | string | yes | Repository root. |
| `check` | boolean |  | Build and replay (default true). |
| `library` | boolean |  | Treat the repository as a library even if it has a main: the front door is a Rust crate with the public API, re-exporting each wired unit's port. Found by default when there is no main and no server. |

## Wire unit into app

Tool `app_wire` · CLI `rust-anything app wire`

After a unit passes gate, hand its commands to its port.rs: adds the unit crate to rust/app as a library, writes a glue stub (src/units/<unit>.rs, yours to write: parse args, call <crate>::port, print what the original prints), regenerates the routing with a kill switch RUST_ANYTHING_UNIT_<NAME>=original, then builds and replays. Run it again after writing the glue: 100% passed and a lower fallback rate.

Runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `repo` | string | yes | Repository root. |
| `unit` | string | yes | Unit crate folder, its name under rust/, or the unit id it was bridged from. |
| `commands` | string[] |  | Commands the unit answers; kept from the last wire when omitted. |
| `routes` | string[] |  | Servers: routes the unit answers, axum syntax: "GET /users/{id}", "/path" for any method, "*" for everything else; kept from the last wire when omitted. |
| `skip_gate` | boolean |  | Do not run gate on the unit first. |
| `check` | boolean |  | Build and replay (default true). |

## Lift to pure Rust app

Tool `app_lift` · CLI `rust-anything app lift`

Make rust/app a pure Rust app. Refuses (and lists every blocker) unless replay passes with fallback rate 0 and every unit passes gate. Then, on a copy first: removes the fallback and kill switches, turns each unit into a plain library (no cdylib, bindings or generated wrappers), adds a trycmd test running rust/app-cases on cargo test, checks fmt/clippy/tests, DECISIONS.md targets and assets, and replays the pure binary. Never touches the original.

May overwrite files, runs the original's code or commands.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `repo` | string | yes | Repository root. |
