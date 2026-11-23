# Pitfalls

Mistakes already made in this repository, each with the rule that prevents it. Add one in the
same change whenever a mistake is worth not repeating.

## Generated code and bridges

**A helper in `port.rs` became part of the bridged API.** Making `parse_options` `pub` exported it
through the bridge. Keep helpers private; only the unit's exports are `pub`.

**Wiring every napi function broke crates without `serde_json`.** `required_deps` must add each
crate the generated code uses. After changing codegen, bridge a unit with no JSON parameters and
build it.

**Generated helpers unused by a crate failed clippy.** Emit each helper only when the crate needs
it (as `JOINED_IN_RS` and `JOINED_OUT_RS` are), and run `gate` on a crate that uses none.

**Number formatting picked the wrong digit on ties.** A hand-written shortest-digits routine gave
`...813` where V8 gives `...812`. Take digits from `serde_json` (zmij), which rounds to the closest
value as V8 does, and test ties.

## Recording

**Capture code tripped the project's coverage threshold.** Code `record --from-tests` appends to
the original counted against Jest's limit. Wrap anything added to user files in
`/* c8 ignore start */` and `/* istanbul ignore next */`.

**A test command's output corrupted the MCP stream.** The child wrote to the server's stdout.
Send every child's stdout to stderr or a pipe, never to the MCP server's stdout.

**A test runner in watch mode never ends.** Run every outside program through `crate::process`,
which closes stdin and stops it at a time limit; `from_tests` also sets `CI=1`.

**Coverage listed one file three times.** Paths from import walking kept `..` segments. Compare
and print canonical paths.

## Numbers and claims

**Benchmarks taken while other builds ran were off by a wide margin.** Run `bench` on a quiet
machine, run it twice, and name the hardware and core count next to every published number.

**Every number in the docs is measured.** Say what was run, on what, and the result, including the
slow cases (the single-call row is slower than JS on some units). No rounding up for a headline.

## Repository

**A local path reached a committed manifest.** Demo manifests keep a placeholder `root`; check
`git diff --cached` for `/Users/` and `/home/` before committing (`scripts/check-secrets.sh`
does this in the pre-commit hook).

**A new translation was listed right after English.** Language lines list English first, then
the existing languages in their order, then new ones at the end (see CONTRIBUTING.md).

**Two sessions edited one checkout.** When another agent is working in the repository, work in
a separate worktree and bring the change over when its files do not overlap.
