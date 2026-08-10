---
doc_type: codex-ssot
title: Host-scoped shipping concurrency governance + commit-time Quickmerge provenance
summary: >-
  SSOT for the 2026-08-09 hardening of the shared-checkout shipping path: per-repo + host-wide concurrency caps on
  quality-gates.sh (qg-host-governor.sh's total-instance gate, now repo-aware), a separate host-wide concurrency cap on
  the docs fast path (push-host-governor.sh, safe-doc-push.sh), a true per-repo+branch push mutex for the actual git-
  remote critical section, and a commit-msg hook that catches a raw source commit missing the Quickmerge trailer at
  COMMIT time rather than only at push time. Root-caused a live, multi-hour shipping incident this doc documents in
  full.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quickmerge, safe-doc-push, quality-gates, concurrency, git-discipline, host-governor, provenance]
related:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-08-09
authoritative_for:
  [QG host-concurrency governance, safe-doc-push.sh concurrency, commit-time Quickmerge provenance enforcement]
referenced_by: []
owner:
last_reviewed: 2026-08-09
code_refs:
  [
    scripts/quality-gates-base/qg-host-governor.sh,
    scripts/dev/push-host-governor.sh,
    scripts/quickmerge.sh,
    scripts/dev/safe-doc-push.sh,
    scripts/hooks/check-quickmerge-provenance.sh,
    scripts/cicd/check_strict_quickmerge.py,
    .pre-commit-config.yaml,
    scripts/pre-commit-templates/,
  ]
---

# Host-scoped shipping concurrency governance + commit-time Quickmerge provenance

## The incident this fixes

Live, 2026-08-09: a single 5-file `scripts/**` fix (portable `UV_VERSION` parsing + a new push governor) took dozens of
attempts and several hours to land on a shared dev-host checkout. Root causes, all independently confirmed:

1. **~24+ distinct AO-dispatched slot identities** committing/pulling/pushing on `unified-trading-pm`
   `live-defi-rollout` concurrently, with **zero cross-slot coordination** — each slot is a separate
   `git clone --reference` (see `/codex/05-infrastructure/per-tab-worktrees.md`), so a flock scoped to "this checkout's
   `.git` dir" (the pre-existing `_qm_locked_git_commit` / `locked_git_commit` per-checkout locks) provides zero
   protection against a DIFFERENT clone's concurrent commit/pull.
2. **`.git/index.lock` churn** from that same concurrent load — sampled continuously HELD for 60s straight at one point,
   with `lsof` confirming no live holder (a crashed/killed process's abandoned lock, not real contention) at least twice
   during the same incident.
3. **`git commit`/`git pull --rebase --autostash` racing prek's own stash-save/restore cycle** — a well-known,
   previously-documented class (`autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`,
   `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`) that this incident re-confirmed live multiple
   times: staged content silently reverting to match HEAD between one shell command and the next, with no error.
4. **A raw `git commit` retry-loop**, built mid-incident specifically to get UNSTUCK from (1)-(3), was ITSELF an
   instance of the exact problem section 3 below now closes: it bypassed `quickmerge.sh` entirely, so none of the
   governance in this doc applied to it.
5. A separate, pre-existing bug (`grep -oP` — a GNU/PCRE-only flag — silently killing `scripts/setup.sh` under `set -e`
   on macOS's BSD `grep`) made `quickmerge.sh` itself appear to hang/loop on this host for unrelated reasons,
   compounding the diagnosis. Fixed with `sed -E` (POSIX-portable) in `setup.sh` and
   `quality-gates-base/base-library.sh`.

## 1. QG per-repo + host-wide concurrency caps

`qg-host-governor.sh`'s `qg_governor_acquire_total_instance()` (called by every repo's `quality-gates.sh` via
`base-service.sh`/`base-library.sh`, right after sourcing the governor) now composes TWO caps, not one:

- **Per-repo sub-cap**: PM (`unified-trading-pm`) ≤ 4 concurrent QG runs host-wide; every OTHER (service) repo ≤ 1 —
  never two concurrent QG runs on the SAME service repo on one host, since those virtually always collide on the same
  git ref. Override: `QG_REPO_INSTANCE_CAP`.
- **Host-wide flat cap**: ≤ 6 concurrent QG runs total, regardless of repo mix (was 4, floored on physical cores; raised
  to 6 alongside the new per-repo dimension since the two now compose instead of one flat number doing both jobs).
  Override: `QG_TOTAL_INSTANCE_CAP`.

Admission requires BOTH caps to have room, checked together each cycle (never hold one while blocked on the other — that
would let a repo's own slot sit idle mid-wait, starving same-repo peers for no reason). A cycle that acquires the repo
token but not the global one releases the repo token immediately and retries both from scratch next tick.

**Implementation trap already hit and fixed while building this**: the first version's acquire helper captured its
result via `$(...)` command substitution — which forks a subshell, and an `flock` held on an FD opened inside that
subshell is released the INSTANT the subshell exits (closing the FD), before the caller ever gets to use it. A
contention test (two processes on the same repo, cap=1) caught this immediately — the second process sailed through
instead of queueing. Fixed by inlining the `exec`+`flock` pair directly in the caller's own shell (no
command-substitution wrapper around the actual lock acquisition) — see `_qg_try_repo_token` / `_qg_try_global_token` in
`qg-host-governor.sh`. **Any future addition to this file must keep flock acquisition out of a `$()` capture.**

## 2. `safe-doc-push.sh`'s own concurrency budget

`push-host-governor.sh`'s `push_gov_acquire_validate` (K=8 default, `PUSH_GOV_VALIDATE_CONCURRENCY` override) now
brackets `safe-doc-push.sh`'s ENTIRE run (acquired near the top of the script, released after the retry loop) — not just
the commit-hook-chain call the way `quickmerge.sh`'s own (narrower, unchanged) use of this same function still does.
This is a SEPARATE, independent budget from the QG caps in section 1 — the docs fast path is deliberately lighter-weight
(no heavy tests) so it tolerates more real concurrency, and it must never compete with quality-gates' budget for the
same tokens.

## 3. Never commit/push behind remote

Both `quickmerge.sh` (STAGE 0.4, `PRECOMMIT_WORKING_TREE_CONFLICT` / `AUTOSTASH_POP_CONFLICT` / etc. structured codes)
and `safe-doc-push.sh` (its own fetch → reconcile → commit → push retry loop) fetch and reconcile against origin BEFORE
every commit attempt, and hard-fail (`QUICKMERGE_BLOCKED ...` / a non-zero exit with a printed recovery line) rather
than silently proceeding when a genuine unresolvable conflict is hit. **HARD RULE: an agent must never work around one
of these structured failures by dropping to a raw, unscoped `git commit`/ `git push` — that bypasses every governance
mechanism in this doc**, including section 4 below (which now catches exactly that bypass at commit time).

## 4. Commit-time Quickmerge provenance (new — catches what push-time enforcement misses)

`check_strict_quickmerge.py` has long enforced, at PRE-PUSH time, that any commit touching a SOURCE file
(`.py`/`.ts`/`.tsx`, outside `scripts/`/`tests/`/`test/`/`.github/` — see its `SOURCE_EXT`/`NONSOURCE_DIR`) must carry a
`Quickmerge:` trailer (added by `quickmerge.sh`'s own commit call) or be a merge/bot/carve-out-only commit. The gap: a
raw local `git commit` bypassing `quickmerge.sh` was invisible to this until PUSH time — long enough to sit in a shared
checkout racing every other concurrent session's pulls/rebases/autostashes (see the incident above, cause 4).

**`scripts/hooks/check-quickmerge-provenance.sh`** closes this — a NEW `commit-msg`-stage local hook (installed via
`.pre-commit-config.yaml` and all three `scripts/pre-commit-templates/*.yaml` — docs, python-service, python-library)
that runs the identical carve-out logic at commit time: reads the about-to-be-created commit message (git passes its
file path as `$1` for a `commit-msg` hook), checks staged files against the same `SOURCE_EXT`/`NONSOURCE_DIR` shape
(duplicated by hand from `check_strict_quickmerge.py`, kept in sync via cross-reference comment in both files — a bash
hook and a Python CLI can't share an import), and exits 0 with a printed warning (not a failure) if a source file is
staged with no `Quickmerge:` trailer present.

**Rollout is WARN-only by default**, mirroring `check_strict_quickmerge.py`'s own `STRICT_QUICKMERGE_BLOCK` precedent
exactly (land unblocking, observe real fleet traffic for false positives, THEN flip to enforcing — never ship a new
fleet-wide commit-blocking gate pre-armed). Override to enforce: `QUICKMERGE_PROVENANCE_BLOCK=1`.

**Known gap**: husky-managed JS/TS repos (`deployment-ui`, `unified-trading-system-ui`) don't run prek at all — their
pre-push guard is a committed `.husky/pre-push` delegate file, not this hook chain, so this new commit-msg check does
not currently reach them. A husky-side equivalent is tracked as future work, not yet built.

## Operator/agent takeaways

- Don't hand-roll a raw `git commit`/`git push` retry loop to escape contention on a shared checkout — that bypasses
  every gate in this doc. If `quickmerge.sh`/`safe-doc-push.sh` themselves are stuck on host contention, the fix is
  patience (both have their own bounded, backed-off retry logic) or an isolated `git worktree` (shares the same object
  database, so a commit made there is immediately valid from the main checkout too — see this doc's own shipping
  incident for the exact recovery sequence used).
- A stale `.git/index.lock` (confirmed via `lsof <path>` showing NO holder) is safe to remove — it is an abandoned
  marker from a crashed process, not live work; removing it is infrastructure hygiene, not a destructive operation on
  anyone's WIP.
- `QUICKMERGE_PROVENANCE_BLOCK=1` and `QG_REPO_INSTANCE_CAP`/`QG_TOTAL_INSTANCE_CAP`/ `PUSH_GOV_VALIDATE_CONCURRENCY`
  are operator-facing tuning knobs, not agent-facing overrides — an agent hitting a WARN from the new hook should switch
  to the sanctioned ship path, not adjust the env var to silence it.
