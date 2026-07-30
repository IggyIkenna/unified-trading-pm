# prek keeper rollback-baseline fix

Fix + verification oracle for the recurring corruption where a `quickmerge`/`git commit` run silently mangles or deletes
content in files the commit never intended to change.

**Issue SSOT:** `/plans/active/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md`

## What actually causes it

Two **different** upstream bugs produced two different symptoms — which is why several earlier fixes were each real but
none of them stopped it.

| Symptom seen in production                                                 | Cause                                                                                                                                                                                       | Status                                                     |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `last_updated: 2026-06-27 2026-06-27 2026-06-27 …` runaway duplication     | **prek ≤ 0.3.x double-restore**: the ctrl-C cleanup handler _borrows_ the keeper and calls `restore()`, then `Drop` _takes_ it and calls `restore()` again → `git apply <patch>` runs twice | **Fixed upstream in v0.4.4** ([#2143]) — upgrade closes it |
| A frontmatter line silently **deleted** (`author: slot-4 …`); file emptied | **Wrong rollback baseline** (this patch)                                                                                                                                                    | **Still open upstream** as of 0.4.11                       |

### The wrong-baseline bug, precisely

prek writes unstaged changes to a patch file, cleans the worktree, runs hooks, then re-applies the patch. If that
re-apply conflicts, it rolls back with:

```
git checkout -- <root>      # restores from the CURRENT index
```

Our `../prettier-autostage.sh` calls `git add` **during** the hook run. So by rollback time the index no longer holds
the pre-hook state — it holds the hook's rewritten content. prek makes that the baseline, then applies a patch computed
against the **original** content on top of it. Unstaged work is silently lost or duplicated, and **`git status` comes
back clean afterwards**, so nothing downstream ever notices.

The fix stores the tree `git write-tree` already computes (prek currently discards it) and rolls back to that instead:

```
git checkout <pre-hook-tree> -- <root>
```

which resets index _and_ worktree to the true pre-hook state, so the patch applies onto the baseline it was computed
against.

## Trigger conditions (measured, not assumed)

Both are required. Breaking either one avoids the corruption:

1. Unstaged changes present anywhere at commit time (this is what engages prek's keeper at all), **and**
2. a hook that rewrites **and `git add`s** a file that _itself_ has unstaged changes.

An unrelated dirty file is **not** sufficient — see scenario S1, which is clean.

## Files

- `keeper-rollback-baseline.patch.b64` — the fix (34 lines, one file: `crates/prek/src/cli/run/keeper.rs`), against the
  `v0.4.11` tag. Decoded sha256: `2152ca85d51eea8240549a7f9aee0bb34bb7143be0d8b4e788577e0920c510d0`.
- `prek-corruption-harness.sh` — 5-scenario oracle. Answers "is this prek build safe for our hook chain?" in ~10s.

### Why the patch is base64 and not a plain `.patch`

**A raw `.patch` file cannot survive this repo's own commit hooks.** Storing it as `.patch` was tried first: the
`trailing-whitespace` and `end-of-file-fixer` hooks rewrote it on the way into the commit, stripping the single-space
blank **context** lines (` `) to empty and dropping the final one. `git apply` then rejected it outright —
`error: corrupt patch at line 101`. In a diff, that leading space is data, not formatting.

So committing the obvious way would have stored a **silently broken fix** — the same class of false-progress this whole
directory exists to prevent, one layer up. Base64 has no trailing whitespace and no significant blank lines, so it round
-trips byte-exactly through any whitespace fixer. Verify with the sha256 above.

(`git apply --recount` does happen to rescue the mangled form, but that papers over a corrupted stored artifact and
would not necessarily save the next patch. The real underlying bug — that these hooks whitespace-normalise `.patch`
files at all, in every repo, not just this one — is tracked as a todo on the issue SSOT.)

## Verify any prek build

```bash
bash prek-corruption-harness.sh                            # whatever `prek` is on PATH
PATH=/path/to/other/build:$PATH bash prek-corruption-harness.sh
```

Safe build → `clean=5 corrupt=0`. Stock prek ≤ 0.4.11 → S3 and S4 report `CORRUPT`.

Run this against each new prek release before rolling it out. That is the whole point of the file: the last two times we
relied on reading upstream changelogs instead, we were wrong.

## Build a patched prek

Needs a Rust toolchain (~90s on 24 cores; no network beyond the initial clone/crates fetch):

```bash
HERE=$(pwd)                      # this directory
git clone --depth 1 --branch v0.4.11 https://github.com/j178/prek.git /tmp/prek-build
cd /tmp/prek-build

# decode + integrity-check before applying
base64 -d "$HERE/keeper-rollback-baseline.patch.b64" > /tmp/keeper.patch
sha256sum -c <<<"2152ca85d51eea8240549a7f9aee0bb34bb7143be0d8b4e788577e0920c510d0  /tmp/keeper.patch"

git apply /tmp/keeper.patch
cargo build --release -p prek    # ~90s on 24 cores
bash "$HERE/prek-corruption-harness.sh"   # MUST report clean=5 corrupt=0 before installing
```

Install by replacing the binary the hooks actually invoke — check `which prek` first; on hosts bootstrapped by
`agent-orchestrator/scripts/bootstrap_vm.sh` it is a `uv tool` shim, not a plain file.

## Regression evidence for the patch

- Harness: 2 corrupt → **0 corrupt**.
- `prettier-autostage`'s normal auto-stage path is **byte-identical** patched vs unpatched (the reformat still lands in
  the commit). The patch only changes the conflict/rollback path.
- Upstream's own keeper tests pass, including `intent_to_add_file_survives_conflicted_stash_restore` (the [#2143]
  regression test), `staged_files_only`, `restore_on_interrupt`, and
  `all_files_with_existing_unstaged_changes_uses_snapshot_baseline`.
- Full upstream suite vs a pristine-`v0.4.11` control: 94/41 control, 93/42 patched. The single delta is
  `perl::additional_dependencies`, which passes deterministically in isolation on the patched build — it is cpan
  flakiness under 24-way test parallelism. Every one of the 42 failures is a language-toolchain test (conda, dart,
  haskell, julia, lua, perl, php, r, ruby) failing for lack of an installed toolchain; none touch `keeper.rs`.
- Performance: **zero cost on the happy path** — it stores a `String` that was already being computed and thrown away.
  The rollback path gains one argv element on a command that only runs when a conflict already occurred.

## Upstreaming

[#1890] proposed essentially this fix and was closed unmerged because the maintainer could not reproduce the general
case from the report. `prek-corruption-harness.sh` is exactly the minimal deterministic reproduction that was asked for
and never supplied. If a PR carrying it is merged, this directory can be deleted and every host simply upgrades.

[#2143]: https://github.com/j178/prek/pull/2143
[#1890]: https://github.com/j178/prek/pull/1890
