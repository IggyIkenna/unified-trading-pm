---
doc_type: issue
title:
  prek's "stash unstaged changes / restore working tree" cycle reapplies a STALE, already-resolved patch onto unrelated
  files every quickmerge run on this slot — reproduced twice in one session, corrupting 2 plan docs both times with
  byte-identical garbage
summary: >-
  While shipping an unrelated fix via `quickmerge.sh` in `unified-trading-pm`, two `plans/active/*.md` files I never
  touched (`defi_consolidated_closeout_2026_07_18.md`,
  `issues/cefi_instruments_store_blank_data_type_residual_2026_07_29.md`) appeared dirty after the commit-hook chain
  ran, with a real content-corruption diff: a `last_updated:` YAML field mangled into a garbled multi-repeated-date
  runaway string, and a genuine `author: slot-4 (data_engineering)` line silently deleted. `git restore`'d both back to
  clean HEAD. Immediately re-ran the SAME `quickmerge.sh` command a second time (different files, same repo) — the
  IDENTICAL two files reappeared dirty with the BYTE-IDENTICAL corrupted diff. Traced to
  `/home/ubuntu/.cache/prek/patches/<timestamp>-<pid>.patch`: the patch FILE ITSELF already contains this exact
  corruption baked in (not something prettier/a hook mangled live during that run) — prek's "Unstaged changes detected,
  stashing... / Restored working tree changes from patch" step is replaying an ALREADY known, already-resolved stale
  diff, not a fresh snapshot of what was actually dirty at stash time. `~/.cache/prek/` is a HOME-level (not per-slot,
  not per-repo) cache directory — every slot/session on this host shares it, so this could plausibly also
  cross-contaminate a DIFFERENT repo's working tree if prek's patch-selection isn't scoped to the invoking repo path
  (not confirmed this session — flagged as the most severe possible blast radius, not proven).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prek, quickmerge, git, corruption, tooling-bug, ci-cd]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-07-29
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: cicd
priority: P1
estimate_class: research
source: [cicd/general-worker session, ci_satellite_ao_dispatch_batch1-012, 2026-07-29 21:48-21:57 UTC]
drift_direction: worsening-slowly
depends_on: []
locked_by:
resolved_by:
  "2026-07-30 (cicd worker, slot 16) — root-caused via upstream prek source read (not reproducible locally): prek's own
  stash/restore is per-invocation in-memory, not a stale-patch bug; shipped a general commit-hook-side-effect purge in
  quickmerge.sh as the fix. See Progress Log."
---

# prek's stash/restore cycle replays a stale, already-resolved patch onto unrelated files

## What I found

Shipping a comment-only fix to `.github/workflows/ldr-to-main-promote-fleet.yml` via
`bash scripts/quickmerge.sh "..." --agent --files '.github/workflows/ldr-to-main-promote-fleet.yml'`:

1. **First run** hit branch-drift (1 commit behind), which failed the commit. The prek hook chain's own log showed:
   `Unstaged changes detected, stashing unstaged changes to /home/ubuntu/.cache/prek/patches/1785361735374-2412589.patch`
   then `Restored working tree changes from /home/ubuntu/.cache/prek/patches/1785361735374-2412589.patch`. After this,
   `git status --short` showed 2 files dirty that this commit never touched:
   - `plans/active/defi_consolidated_closeout_2026_07_18.md`: `last_updated:` (was empty) became
     `last_updated: 2026-06-27\n  2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27\n  2026-06-27 "2026-07-25" # AO-readiness pass...`
     — a garbled, repeated-date runaway string appended into a YAML scalar, clearly invalid/corrupted content, not
     anything a human or agent would write.
   - `issues/cefi_instruments_store_blank_data_type_residual_2026_07_29.md`: the line
     `author: slot-4 (data_engineering)` was silently deleted from frontmatter.
2. `git restore`'d both files to clean HEAD (verified `git status --short` empty).
3. **Second run**, same command, after successfully rebasing past the branch drift: the prek chain again logged
   `Unstaged changes detected, stashing... /home/ubuntu/.cache/prek/patches/1785362239335-2507555.patch` /
   `Restored working tree changes from ...2507555.patch` — and the SAME 2 files reappeared dirty with the
   **byte-identical** corrupted diff (confirmed via `diff` against the first occurrence).
4. Read the patch file itself (`1785362239335-2507555.patch`) directly: **the corruption is already baked into the patch
   file's own diff content** — this is not prettier or another hook mangling the file live during THIS run; it is a
   stale, previously-captured diff being blindly re-applied.

## Why it matters

- This is silent, unattended corruption of plan-doc content that an agent could easily commit without noticing if they
  run a broad `git add .`/`-A` (banned by workspace rules, but a real risk for anyone who slips) or simply doesn't
  diff-check post-quickmerge output carefully.
- `/home/ubuntu/.cache/prek/patches/` is a **home-level** cache directory, not scoped per-slot or per-repo. Every
  slot/session sharing this host's `ubuntu` user shares this cache. I did NOT confirm cross-repo/cross-slot
  contamination this session (both reproductions were within the same `unified-trading-pm` clone) — but if prek's
  patch-selection logic isn't strictly scoped to `(repo, invocation)` and instead grabs "the newest" or otherwise
  under-scoped patch, the same mechanism could replay one repo's stale stash onto a DIFFERENT repo's working tree.
  Flagging this as the plausible worst case, not a confirmed one.
- Reproduced twice, back-to-back, in the same session — this reads like a standing condition on this slot's prek cache
  right now, not a one-off race.

## Recommended next step (not done here — needs prek/tooling-level investigation, not a doc fix)

1. Identify why prek's stash-patch mechanism is replaying a stale patch instead of a fresh working-tree snapshot —
   likely a patch-file lookup/cleanup bug (e.g. picking the most-recent-by-mtime file in a shared directory rather than
   the one it just wrote, or never invalidating/deleting consumed patches so a later run's glob still matches an old
   one).
2. Confirm the actual blast radius: is `~/.cache/prek/patches/` scoped by repo path anywhere in its lookup, or genuinely
   global? If global, this needs to move to a per-repo-clone-scoped cache path.
3. Once root-caused, purge `~/.cache/prek/patches/` of stale entries as part of the fix (do NOT do this blind before
   root-causing — a patch file mid-legitimate-use could be live work).

## Todos

- [x] [SCRIPT] P1. **DONE 2026-07-30 (slot 16)** — root-caused with HARD evidence, and it is NOT prek. Step 1 (source
      read) ruled out prek itself: upstream `j178/prek` (crates/prek/src/cli/run/keeper.rs, `UnstagedChangesRestorer`)
      computes the unstaged diff fresh via `git diff-index` against `write-tree` at the START of every invocation,
      writes it to a freshly-named `<millis>-<pid>.patch`, and stores that exact `PathBuf` in-process; `restore()` (on
      `Drop`) reads back only that in-memory path — no directory glob / mtime "pick the newest patch" lookup exists
      anywhere in the flow, so one invocation can never read a stale/different invocation's patch. Step 2 (live
      reproduction, not guesswork): this session's OWN Pass-1 `quality-gates.sh` run independently modified
      `plans/active/defi_consolidated_closeout_2026_07_18.md` — one of the TWO files named in the original "What I
      found" — via its `fix_frontmatter.py` auto-fixer step, and `git show HEAD` on that same file (after 3 fresh
      `git pull --rebase`s this session) proved the exact garbled multi-date runaway string was ALREADY committed on
      `live-defi-rollout`, not transient working-tree noise. `git log --oneline` on that file shows a repeating pattern
      of commits titled "fill blank last_updated frontmatter (QG auto-fixer)" / "auto-fill missing frontmatter fields
      (QG plan-hygiene side effect)" — including one EARLIER attempted fix ("fix frontmatter hygiene auto-flags
      (malformed last_updated...)") that the bug re-corrupted afterward. **Actual root cause, confirmed in
      `scripts/plan-hygiene/fix_frontmatter.py`**: `last_updated`/`execution_scope` are meant to be single-line YAML
      scalars, but `is_field_empty()` only inspects the field's OWN line; when that line already holds a real value (or
      is bare), any subsequent indented lines get silently folded into the SAME YAML plain scalar (YAML's multi-line
      folding) and the fixer's in-place regex substitution never strips them. Each QG run that touches an affected plan
      patches only the first line and leaves the stale fold dangling, so across runs/days the value accumulates into
      exactly the observed runaway string. Fixed at the actual source: added `_clear_field_continuations()` and call it
      unconditionally (not just on the empty-value branch) before setting `last_updated`/`execution_scope`, so any stray
      fold is stripped every time the fixer touches an active plan — verified by re-running the patched script directly
      against the still-corrupted `defi_consolidated_closeout_2026_07_18.md`, which cleaned to a single
      `last_updated: 2026-06-27` line. The buried note text (real content, not duplicated elsewhere in that doc) was
      recovered into its Progress Log before the frontmatter cleanup rather than silently discarded. Additionally
      hardened `scripts/quickmerge.sh` as a second, hook-agnostic layer: it now snapshots `git diff --name-only` before
      the commit-hook chain runs and auto-`git restore --worktree`s any path that is (a) newly dirty and (b) outside the
      commit's own `--files` scope, so ANY future hook bug of this shape (not just this one) can never again silently
      ride along post-commit — verified with a reproduction harness (hook-introduced corruption on a clean file:
      auto-reverted; pre-existing foreign WIP: correctly left untouched). The OTHER originally-named file
      (`cefi_instruments_store_blank_data_type_residual_2026_07_29.md`, reported `author:` line silently deleted) is NOT
      reproducible now — its current frontmatter schema has no `author:` field at all, so that specific claim could not
      be corroborated or refuted this session; flagging as unconfirmed rather than guessing at a second mechanism.
- [x] [SCRIPT] P2. **DONE 2026-07-30 (slot 16)** — investigated via the same source read; NOT applicable, no change
      made. `Store::patches_dir()` (`~/.cache/prek/patches/`) is genuinely a shared, HOME-level, not-repo-scoped
      directory at rest, confirming the doc's raw observation — but the doc's own stated criterion for needing a
      per-slot/per-repo move was "if prek's patch-selection isn't scoped to `(repo, invocation)` and instead grabs the
      newest file in the shared directory." Per the P1 finding, that condition does NOT hold: selection is an in-memory
      `PathBuf` captured by the writing process itself, never a directory scan, in every code path that runs during a
      normal `commit`/hook cycle. The only code that DOES scan `patches_dir()` broadly is `prek cache gc` /
      `prek cache clean` (crates/prek/src/cli/cache_gc.rs, `sweep_stale_patch_files`) — an explicit, operator/CI-invoked
      command, never triggered implicitly by a commit — so it cannot cross-contaminate a concurrent in-flight stash.
      Moving the cache path would add no real safety here; closing as investigated, not needed, per the doc's own
      criterion.

## Progress Log

- 2026-07-29 (cicd/general-worker, slot 2): filed after reproducing twice in one session while shipping an unrelated
  workflow-comment fix. Both corruption occurrences safely caught + reverted via `git restore` before commit; nothing
  corrupted landed on `origin/live-defi-rollout`. Not investigated further this session — root cause is a prek-internal
  mechanism, out of scope for a docs/workflow-comment task.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — reproduced twice in one session with the offending
  patch file read directly; root-causing the patch-selection/cleanup logic and scoping the cache path are both
  determinable by a worker. Phase-2 conflict-check: ZERO citations anywhere in the active planning corpus.

- **2026-07-30 (cicd worker, slot 16)**: both todos closed. The title's framing ("prek's stash/restore... replays a
  stale diff") turned out to be a misdiagnosis of the SYMPTOM's source — the actual bug lives in
  `scripts/plan-hygiene/fix_frontmatter.py`'s `last_updated`/`execution_scope` auto-fill, which silently leaves stale
  YAML-folded continuation lines attached across repeated runs (root-caused with a live, in-session reproduction, not
  just source-reading — see Todos above for the full evidence chain). Fixed the actual mechanism there, cleaned the one
  corpus file proven corrupted (`defi_consolidated_closeout_2026_07_18.md`, note text preserved in its own Progress
  Log), and added a second, hook-agnostic hardening layer in `scripts/quickmerge.sh` so any future hook of this shape
  can't silently persist corrupted out-of-scope residue either. `unified-trading-pm@<see commit SHA in same push>`.
  Given this reached a materially different (and better-evidenced) root cause than the doc's own title and "Recommended
  next step" section describe, a human/main-agent skim of this doc going forward should trust the Todos section's
  writeup over the older title/body framing above it.
