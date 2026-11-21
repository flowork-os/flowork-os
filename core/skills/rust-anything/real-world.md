# Real-world runs

What happened when rust-anything met real code, and what changed in the tool because of it.

## x18n (the case-study repository)

| Target | What ran | Result |
| --- | --- | --- |
| `packages/core`, 9 units, 29 functions | analyze, bridge, record, diff, bench, shadow, gate | every gate passes; 9,000+ recorded cases match; slower than TS through a bridge ([report](../demo/x18n-core/README.md)) |
| `packages/builtins/src/formats/shared/`, 7 functions | same | 3,672/3,672 cases match, 960 of them built from 40 real files of the repository (YAML locales, JSON, Markdown, TS), in LF and CRLF |
| whole repository | analyze | 142 units; `start_here` now lists only units with bridgeable exports |

Found in the tool, and fixed:

- `analyze` recommended the format parsers first, but their only exports are plugin factories
  (`properties(): Plugin`). `analyze` now counts bridgeable exports with the rules `bridge`
  applies, and leaves units with none out of `start_here`.
- Types imported from workspace packages (`@x18n/core`) were not followed, so `Plugin` looked
  like data. Type lookup now follows workspace packages to their source.
- `record` could not run a module importing `@x18n/core` at runtime: the package has no build
  output. The resolve hook now maps workspace packages to their source.
- Shaped inputs found a real bug in the `text.ts` port (Infinity in a range), then an order
  dependency on V8's sort with NaN comparators; `js::sort` now reproduces V8.

## vercel/ms

[vercel/ms](https://github.com/vercel/ms) (5.5k stars, commit `4ff48ce`) turns `"2 days"` into
milliseconds and back; most Node projects pull it in through some dependency. Ported end to end
with rust-anything 1.5.1; the crate is in
[`demo/real-world/vercel-ms-rs`](../demo/real-world/vercel-ms-rs).

| Step | Result |
| --- | --- |
| `analyze` | 1 unit (`src/index.ts`), ready, readiness 96 |
| `bridge --kind napi` | `ms`, `parse`, `parseStrict` and `format` bridged, none kept in TS |
| `record --from-tests -- jest` | 975 cases: generated ones, traps, and 340 calls captured from vercel/ms's 167 Jest tests (the first port used 149 inputs copied from them by hand) |
| port | 200 lines of Rust for 184 of TS, including a `FormatIndex` that reads `options` once per batch |
| `diff` | 784/784 matched on the first build; 975/975 with the captured calls |
| `gate` | passes (fmt, clippy, tests, error paths, size, behavior) |
| `bench`, per call | 0.56x over the recorded cases (0.39x at first): `parse` on a normal string takes 79 ns, level with JS, but edge cases and thrown errors still cost more through the bridge |
| batch, `parse` x100,000 | JS 11.8 ms, Rust 0.65 ms: **18x**; 3.4x counting the one-time handover of the strings (2.1x before strings crossed joined) |
| batch, `format` x100,000 | JS 2.1 ms, Rust 2.5 ms with the handover: **0.8x** (0.2x at first); `format(x, { long: true })` 1.2x |

What the port had to get right, all caught by recorded cases or traps:

- `/.../i` without the `u` flag folds only ASCII letters, while Rust's `regex` folds Unicode, so
  `"1 ſ"` (long s) and the Kelvin sign would have parsed as seconds. The port matches units by
  hand, ASCII only.
- `Math.round` rounds halves up (`-2.5` gives `-2`); Rust's `round` goes away from zero.
- `${n}` prints `1e+21`, `5e-324` and `0` for `-0`; the port reproduces JS number-to-string.
  Its first version also had a tie bug (`25.728225708007812` printed as `...813`) that ms's
  integer outputs never reach.
- `str.length` counts UTF-16 units, so the 100-character limit counts an emoji as two.

Found in the tool, and fixed: a napi batch method with a structured parameter (`format`'s
`options`) did not compile, since the generated binding took a `serde_json::Value` that napi
cannot convert without its `serde-json` feature. Crates with batch classes now enable it.

Taken back into the tool from this port:

- The generated `js.rs` has `js::number_to_string` and `js::math_round`, checked against Node on
  20,000 random doubles; the port uses them instead of its own copies. `number_to_string` takes
  its digits from serde_json's printer: 5x faster than `format!` for integers, 3x for fractions.
- napi batches send string items as one joined string with UTF-16 end offsets, number items as
  one `Float64Array`, and return string results joined (`index.cjs` splits them with `slice`):
  2x faster for strings and 20x for numbers than one JS value per item. `new Batch(items)` and
  `run()` keep their shape.
- `analyze` flags `Math.round`, `toFixed` and `/i` regexes without `u` that mention `s` or `k`,
  with guidance on each.
- Calls cost less: on napi every sync function goes over the binary wire with no napi arguments
  (an argument costs about 55 ns, the whole call 22 ns), one JS wrapper per function instead of
  two, `serde_json::Value` parameters cross as tagged values of any shape, and errors come back
  in the wire buffer. `parse` per call went from 121 to 79 ns.
- `record --from-tests` replaces copying test inputs by hand: it records each call the suite makes
  while the tests run, with the capture code kept out of coverage (ms enforces 100%).

The verdict: `ms` is a good port and a bad speed target. Correct on every recorded case, faster
only when a program parses many durations in one go.

## Fuse.js

[Fuse.js](https://github.com/krisk/Fuse) (20k stars, about 20 million npm downloads a week,
commit `edf2fb6`) is the fuzzy-search library behind countless search boxes. Ported with
rust-anything 1.6 (unreleased); the crate is in [`demo/real-world/fuse-rs`](../demo/real-world/fuse-rs).

`analyze` put every folder of `src/` in one import cycle, so Fuse cannot be ported file by file.
The port takes the path a search spends its time on instead: a 54-line adapter
(`adapter/relevance.ts`) exports Fuse's own score for one string of a string list, built from
Fuse's `BitapSearch`, field norm and `computeScoreSingle`. That function is what a search over
50,000 strings runs 50,000 times. `bridge --batch relevance:text` keeps the strings in Rust and
runs a search over all of them, on all cores.

| Step | Result |
| --- | --- |
| adapter | the adapter's ranking equals `new Fuse(list).search(q)` on 81 queries and option sets before any Rust |
| `record --inputs` | 3,414 cases: titles from Fuse's own fixtures, non-ASCII, emoji, patterns longer than 32 units, every supported option, and wrong-typed options (refused, 149 cases) |
| port | 673 lines of Rust for the 839 lines of Fuse it stands in for |
| `diff` | 3,414/3,414 match on the first build |
| `gate` | passes |
| drop-in | `withRust(Fuse)` answers string-list searches in Rust and passes everything else to Fuse; it returns byte-identical results to Fuse on 360 searches (12 option sets, 15 queries, with and without `limit`) |

Search time per query, Apple M4 (10 cores), Node 24, results checked identical before timing:

| List | Fuse.js | Rust | Speedup |
| ---: | ---: | ---: | ---: |
| 1,000 strings | 1.9 ms | 0.1 ms | 18x |
| 10,000 strings | 19.1 ms | 0.7 ms | 27 to 30x |
| 50,000 strings | 91.2 ms | 2.8 ms | **32x** |
| 50,000 strings, one core | 92.0 ms | 17.5 ms | 5.3x |

What the port had to get right:

- Bitap runs on 32-bit JS integers: `1 << 31` is negative and `(1 << 31) - 1` is a double that
  becomes `2147483647` at the next shift. The port keeps those values as JS has them.
- Text is indexed in UTF-16 code units, so an emoji is two positions, as in Fuse.
- `ignoreDiacritics` is NFD plus a list of combining-mark ranges and a few letters spelled out
  (`ł`, `ß`, `ı`); the port uses the same list.
- `String.prototype.trim` decides which strings Fuse skips: JS whitespace, not Rust's
  `char::is_whitespace` (which includes U+0085 and leaves out U+FEFF).

Found in the tool, and fixed: batch crates whose items were strings but whose results were not
got an unused helper and failed `clippy -D warnings`; and `gate`'s size check counted only the
adapter (54 lines, so 12.5x "too big") instead of the Fuse files it imports.

What it does not cover: object lists with `keys`, extended and token search, logical queries,
`includeMatches`, a custom `sortFn` or `getFn`. The drop-in hands those to Fuse unchanged. The
speedup needs the list to stay in Rust between searches; building it costs about as much as
Fuse's own index (3.4 ms against 2.8 ms for 50,000 strings).

## Fixtures written to stress the tool

| Fixture | Exercises | Result |
| --- | --- | --- |
| `tests/fixtures/async` | async functions on both bridges | 900/900, both gates pass |
| `tests/fixtures/classes` | classes: state, constructor errors, `Map` order, `split('')` on emoji | 600/600 scenarios, both gates pass |
| `tests/fixtures/aliases` | tsconfig `paths` with `extends`, comments, trailing commas | analyze and record follow them |
| `tests/fixtures/monorepo` | a package importing a sibling with no build output | record resolves it to source |

Found in the tool, and fixed: napi turned `None` into `null` (JS gives `undefined`); scenarios
too short and too random to catch a stateful bug (now up to 12 calls, reusing earlier strings);
generated `let out = ()` and immediately-called closures that clippy rejects.

## External libraries (static only)

`unjs/scule`, `unjs/ufo` and `unjs/pathe` were cloned and analyzed and bridged. Running their
code (`record` executes the original) was refused by the session's safety policy for code
downloaded from the internet, so these runs stop before `record`.

| Library | analyze | bridge |
| --- | --- | --- |
| scule (case conversion) | 2 units, ready | all 11 functions bridgeable after the fix below |
| ufo (URL utilities) | 7 units, ready; `punycode.ts` ranked first | `toASCII` bridged (untyped JS: crosses as JSON) |
| pathe (path utilities) | 5 units; `_glob.ts` caution (dynamic regex) | 13 functions bridged; `typeof path.join`-typed exports cross as JSON |

Found in the tool, and fixed: constrained generics (`camelCase<T extends string | readonly
string[]>`) were treated as "any value, functions included", which kept 10 of scule's 11
functions in TS. Type parameters with data constraints are now substituted by the constraint.

A port of scule was written (`demo` not included: it was never recorded against the original).
