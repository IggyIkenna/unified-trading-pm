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
status: open
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

- [ ] [SCRIPT] P1. Root-cause prek's stash/restore patch-replay bug (see recommended next step above) and fix the
      underlying patch-selection/cleanup logic so a stale patch can never be reapplied onto a clean working tree.
- [ ] [SCRIPT] P2. Once root-caused, determine whether `~/.cache/prek/patches/` needs to move to a per-slot or
      per-repo-scoped path to eliminate the cross-contamination risk, and make that change if so.

## Progress Log

- 2026-07-29 (cicd/general-worker, slot 2): filed after reproducing twice in one session while shipping an unrelated
  workflow-comment fix. Both corruption occurrences safely caught + reverted via `git restore` before commit; nothing
  corrupted landed on `origin/live-defi-rollout`. Not investigated further this session — root cause is a prek-internal
  mechanism, out of scope for a docs/workflow-comment task.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — reproduced twice in one session with the offending
  patch file read directly; root-causing the patch-selection/cleanup logic and scoping the cache path are both
  determinable by a worker. Phase-2 conflict-check: ZERO citations anywhere in the active planning corpus.
- 2026-07-30 (satellite corpus-hygiene pass, slot-4): reproduced 2 MORE times, same exact file + same exact garbled
  `last_updated:` signature (`plans/active/defi_consolidated_closeout_2026_07_18.md`), same host, ~15 min apart in this
  session — brings the confirmed total to 4 occurrences across 2 separate sessions, always the same target file so far
  (not yet confirmed whether that's because this file is disproportionately likely to be mid-edit by a concurrent
  session at corruption time, or a deeper pattern in prek's patch-selection). Both caught + reverted via `git restore`
  before commit; nothing corrupted landed. `~/.cache/prek/patches/` inspected this session: dozens of `.patch` files
  with mtimes spanning this exact session's runtime, confirming the mechanism is actively firing on this host right now,
  not a one-off. Still not root-caused (third-party Rust binary, `prek 0.4.5` — reading its internal source is outside a
  bounded doc-hygiene task's scope); this entry exists purely to strengthen the evidence base for whoever picks up the
  actual root-cause investigation next.

- **2026-07-30 (slot-1, harsh_pc)**: first confirmed occurrence where the corruption actually **landed on
  `origin/live-defi-rollout`** rather than being caught pre-commit — a materially worse instance than the 4 above. While
  repairing this exact same target file's already-garbled `last_updated:` field (a separate task, unrelated to this
  issue), the intended clean single-line fix was verified correct locally (schema check passed, no conflict markers) and
  staged, but the SHIPPED commit (`unified-trading-pm@33fcd528d`) contains a different, still-garbled value
  (`last_updated: '2026-06-27 "2026-07-30"'` — parses as valid YAML, so `check_frontmatter_schema.py` did not catch it;
  caught instead by directly diffing `git show origin/<branch>:<path>` against the intended content). Confirms the
  replay can happen **during the quickmerge/prek run itself** (between `git add` and the final commit), not only as a
  leftover unstaged diff a careless `git add -A` might sweep in — post-ship verification for any file this bug might
  touch needs a real content diff against origin, not just "no conflict markers" / schema-pass. A second quickmerge run
  moments later (unrelated file) re-corrupted the same field a THIRD time locally (reverted to a stale pre-fix value,
  `last_updated: 2026-06-27`, caught before staging). Re-fixed properly this time; re-verified byte-for-byte against
  `git show origin/<branch>:<path>` after shipping, not just schema/conflict-marker checks.
