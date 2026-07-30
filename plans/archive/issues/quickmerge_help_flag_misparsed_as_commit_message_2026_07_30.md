---
doc_type: issue
title:
  quickmerge.sh had no --help and silently ran the full pipeline on any unknown flag — which also reintroduced a known,
  proven-buggy prettier version
summary:
  quickmerge.sh's argument parser had no `--help`/`-h` case; the catch-all treated ANY unrecognized token (including
  `--help` itself) as the commit message and let the REAL pipeline run. In non-agent mode this hit STAGE 3's unscoped
  `quality-gates.sh --lint --fix`, which pinned `prettier@3.6.2` — the exact version
  `prettier_emphasis_mangling_corpus_corruption_2026_07_14` proved corrupts markdown — reintroducing that "resolved"
  corruption on every unscoped `--fix` run, tree-wide (~1,300 files). Root-caused, reproduced in isolation (no side
  effects), and fixed same-session — real `--help` + hard-error-on-unknown-flag added to quickmerge.sh / base-service.sh
  / base-library.sh / base-codex.sh / admin-force-sync-all-to-main.sh, and every stale `prettier@3.6.2` pin in those
  files + the two codex reference copies bumped to `3.9.5`.
status: resolved
resolved_by:
  "2026-07-30 — fixed + shipped same session: unified-trading-pm@bbcd29615 (scripts/quickmerge.sh,
  scripts/quality-gates-base/{base-service,base-library,base-codex}.sh,
  scripts/repo-management/admin-force-sync-all-to-main.sh, codex/06-coding-standards/quality-gates-template.sh,
  codex/scripts/quickmerge.sh). Verified: isolated arg-parser repro (no pipeline side effects) proved the mis-parse;
  `--help`/`-h` and unknown-flag rejection tested end-to-end through the real per-repo quality-gates.sh wrappers
  (unified-trading-pm, unified-trading-library) and quickmerge.sh itself, all exiting correctly with zero working-tree
  side effects before shipping; committed content diffed clean against what was tested (`git diff HEAD -- <7 files>`
  empty post-push); Pass-1 QG green (67s)."
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cicd, quickmerge, quality-gates, tooling, prettier, argument-parsing]
related:
  [
    /plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md,
    /plans/active/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md,
  ]
created: 2026-07-30
source:
  - An agent working on an unrelated UI-tracking plan ran `scripts/quickmerge.sh --help` out of idle curiosity (not part
    of its task), which hung and had to be killed via timeout. It reported git status showing ~1,300 unstaged
    working-tree modifications repo-wide plus 2 of its own in-flight files further corrupted with mangled markdown
    escaping. Investigated on request in a separate session.
assigned_vm: NA
priority: P1
parent_epic: infrastructure_master
locked_by:
---

# quickmerge.sh had no --help and silently ran the full pipeline on any unknown flag

## What happened

`scripts/quickmerge.sh --help` did not print usage. It hung, and the agent that ran it had to kill it via `timeout`,
leaving ~1,300 files with unstaged working-tree modifications (codex docs, GitHub workflow files, unrelated plans) and 2
of the agent's own in-flight files further corrupted with mangled markdown escaping (a stray backslash inserted
mid-word, e.g. `asset_group` → `asset\_group`).

## Root cause (three compounding bugs, all in the same request)

1. **No `--help`/`-h` case anywhere in `quickmerge.sh`'s arg parser.** The catch-all branch
   (`*) COMMIT_MSG="$1"; shift ;;`) treats ANY unrecognized token as the commit message — so `--help` was silently
   swallowed as `COMMIT_MSG="--help"` and the script proceeded to run the real pipeline instead of printing usage and
   exiting. Reproduced in isolation by extracting just the arg-parsing block and running it with `--help`:
   `COMMIT_MSG=[--help]`, `AGENT_MODE=false`, `FILES_ARG=[]` — no side effects, no pipeline execution, definitively
   proving the mis-parse.
2. **`--agent` wasn't also passed**, so `AGENT_MODE=false` routed into the non-agent STAGE 3 branch
   (`quickmerge.sh:1400-1417`), which unconditionally runs `bash scripts/quality-gates.sh --lint --fix` — tree-wide,
   with no `--files` scoping in that branch at all.
3. **That tree-wide `--fix` pass called `npx --yes prettier@3.6.2`** (`base-service.sh` — mirrored in `base-library.sh`,
   `base-codex.sh`, and `admin-force-sync-all-to-main.sh`), which is the _exact_ prettier version
   `prettier_emphasis_mangling_corpus_corruption_2026_07_14` already proved deterministically corrupts markdown (bare
   underscore identifiers rewritten as asterisks/escaped-underscores). That fix's `PRETTIER_MIN_VERSION=3.9.5` guard
   only ever landed in `scripts/hooks/prettier-autostage.sh` (the prek per-commit hook) — this tree-wide `--fix`
   invocation was a second, independent, never-updated pin of the proven-buggy version, silently reintroducing the
   "resolved" corpus corruption on every unscoped `--fix` run. The `**/*.{md,json,yaml,yml}` glob matches "codex docs,
   GitHub workflow files, unrelated plans" exactly as reported. Prettier rewrites whatever's on disk regardless of git
   staging state, so the agent's already-`git add`ed files got their working-tree copies reformatted on top of the
   staged (clean) index — explaining "2 of my own files further corrupted, but the index stayed untouched."

This is a **different** bug from `prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md`
(commit-hook-chain dirt during an actual `git commit`, root-caused there to `fix_frontmatter.py`) — this one fires
entirely inside STAGE 3, before any commit is attempted, so that issue's post-commit purge safety net never gets a
chance to run.

## Fix shipped

- `scripts/quickmerge.sh`: real `--help`/`-h` (full usage — routing model, every flag, examples — not a stub) as the
  first arm in the parser; the catch-all now hard-errors (exit 1) on any flag-like (`-*`-prefixed) unrecognized token
  instead of treating it as the commit message.
- `scripts/quality-gates-base/base-service.sh`: already had `--help` (added 2026-07-20 for the same class of bug); added
  the missing unknown-flag catch-all (was silently ignored — no error, no effect); bumped prettier to `3.9.5`.
- `scripts/quality-gates-base/base-library.sh`: had **no** `--help` at all — added it (mirroring base-service.sh, scoped
  to its actual flag set); added the catch-all; bumped prettier.
- `scripts/quality-gates-base/base-codex.sh`: same treatment. Currently dormant (no live repo sources it —
  `unified-trading-codex` is archived) but fixed for SSOT consistency since it's declared canonical for any future
  docs-only repo.
- `scripts/repo-management/admin-force-sync-all-to-main.sh`: unknown flag now hard-errors (was warn-and-continue);
  bumped both prettier pins — its "matches the pre-commit `additional_dependencies` pin" rationale comment was itself
  stale (that hook is `prettier-autostage.sh`, already on `3.9.5`; the comment described an older `mirrors-prettier`
  setup that no longer exists).
- `codex/06-coding-standards/quality-gates-template.sh` (cited as "the reference implementation... all 13 repos must
  align to") and `codex/scripts/quickmerge.sh` (unreferenced historical snapshot): both updated to match, so neither
  teaches the unknown-flag-swallow anti-pattern or the buggy prettier version to a future copy-paste.

Verified end-to-end through the real per-repo `quality-gates.sh` wrappers (not just `bash -n`) before shipping, with git
status checked clean after every test invocation.

## Follow-ups noticed but out of scope for this fix

- `unified-trading-system-ui/context/codex/06-coding-standards/quality-gates-template.sh` (a mirror copy in a different
  repo) still cites `prettier@3.6.2` — not fixed here since it's a different repo's clone; open as its own small todo if
  it's a live-synced mirror rather than a one-time snapshot.
- While shipping this fix, agent-orchestrator's pre-spawn dirty-state gate (`DirtyStateResolution.COMMIT_AND_PUSH`) was
  observed to auto-commit this session's uncommitted WIP as `chore(orphan-wip)` (slot 4, commit `713999e5e`) but the
  branch was then reset to a newer `origin/live-defi-rollout` tip before the "push" half landed — the commit went
  dangling (recovered here via `git checkout <sha> -- <files>`, nothing lost, but the gate's own stated guarantee —
  "preserves the previous worker's WIP that would otherwise be discarded" — didn't hold). Worth its own issue doc if it
  reproduces again; not investigated further here since this session's own work was fully recoverable.
