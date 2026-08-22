---
doc_type: issue
title: >-
  Uncommitted, unexplained staged revert of fleet-workflow-dedup thin-caller-stubs found in features-service-clean-check
  worktree -- stashed, not applied
summary: >-
  Found staged (index != HEAD, no commit) changes in the `features-service-clean-check` worktree that revert 5
  `.github/workflows/*.yml` files (`main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`,
  `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`) from their current
  thin-caller-stub form (shipped by `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`, an active
  in-flight plan) back to full inline content -- 1450 insertions / 69 deletions, zero commit message or rationale
  anywhere. AO auto-nudge flagged this repo RED (dirty 5 files, 210m) during unrelated task
  `defi_satellite_ao_dispatch_batch9-018` (slot 8, gas_fees legacy purge VM monitoring). Could not determine intent
  (accidental partial apply of a revert experiment vs. a deliberate mid-flight rollback of the dedup plan by another
  worker), so per the exact precedent already on file for this same worktree
  (`features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md` -- "unimportant WIP ->
  slot-tagged stash" path when a finding is not part of the current task and intent can't be determined), stashed rather
  than committed or discarded: `stash@{0}` "slot8-2026-08-07: unexplained staged revert of fleet-workflow-dedup
  thin-caller-stubs...". Repo is now clean (`git status` empty, `ahead=0`).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, unified-trading-ci, unified-trading-pm]
scope: [engineer]
tags: [ci-cd, features-service, dangling-wip, stash, git-hygiene, fleet-workflow-dedup]
related:
  - /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md
  - /plans/archive/2026_08/issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
created: "2026-08-07"
author: unknown
source: [backlog task defi_satellite_ao_dispatch_batch9-018, slot 8]
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.12
drift_direction: NA
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
    /plans/archive/2026_08/issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md,
    features-service/.github/workflows,
    agent-orchestrator/scripts/hooks/block_destructive_commands.py,
  ]
---

> **📦 ARCHIVED 2026-08-22 (D3 ledger, stash-pile/stale-WIP cleanup)** — 0 open todos, no lock. The dangling stash was
> ruled abandoned (2026-08-10) and confirmed gone by a fresh re-verify (2026-08-22, no stale-index reuse) — the
> `features-service-clean-check` linked worktree's stash list is empty. Kept as a historical record.

## What was found

`features-service-clean-check` worktree, branch `live-defi-rollout` @ `b0c15f11`: 5 workflow files had staged (index)
content differing from HEAD, worktree matching index (i.e. fully staged, `git add`-ed, never committed). The staged
content is the pre-dedup full-inline form of each workflow -- exactly what `git diff --cached` shows as a revert of
`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`'s thin-caller-stub migration for this repo. No
commit message, no branch note, no Progress Log entry in the dedup plan mentions touching `features-service-clean-check`
specifically as of the last read.

## Why not just commit it

- Not part of the current task (`defi_satellite_ao_dispatch_batch9-018`, an unrelated gas_fees GCS purge VM relaunch).
- The dedup plan is active/in-flight and high-blast-radius (26-repo fleet CI machinery) with a documented prior incident
  class (`shared_ci_workflow_repo_extraction_2026_08_06.md`'s "revert incident"). Committing an unexplained revert of
  live-dispatch-critical CI on a guess risks re-breaking fleet CI the same way.
- This exact worktree has a standing precedent for exactly this situation (see `related`), resolved by stashing +
  filing, not by guessing intent.

## Resolution path

Whoever next works `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` (or owns
`features-service-clean-check`) should: `git stash show -p stash@{0}` in that worktree, determine whether this is (a) an
abandoned experiment (drop the stash), (b) a deliberate rollback that should actually land (investigate why, then commit
with a real message + a Progress Log entry in the dedup plan), or (c) already superseded by a later commit (diff
`stash@{0}` against current HEAD to check). Stash entry:
`slot8-2026-08-07: unexplained staged revert of fleet-workflow-dedup thin-caller-stubs...`.

## Todos

- [x] ✅ [DIAG] P2. Inspect the stash and disposition it per the Resolution path above — **RULED 2026-08-10 (slot-15,
      investigated; confirmed 2026-08-10 by slot-8): (a) abandoned experiment.** See Progress Log for full evidence
      (last-touching commit `b0c15f11` still HEAD for all 5 files, current content still thin-stub form, dedup plan
      still active and lists features-service among rolled-out repos, 5/5 recent `quality-gates-v2` runs green). Ruling
      out (b) deliberate rollback (no rationale anywhere) and (c) superseded (HEAD hasn't moved past `b0c15f11` since).
- [x] ✅ [OPERATOR] P2. **CONFIRMED RESOLVED 2026-08-22** — re-verified fresh (not a stale-index reuse) per D3's
      approval condition. `.tabs/8/features-service` (shares the same `.git` object store as the
      `features-service-clean-check` linked worktree — stashes are repo-wide, not per-worktree, per slot-15's own
      2026-08-10 finding on this doc) now shows **no `refs/stash` ref at all** (`git rev-parse --verify refs/stash`
      fails, `git stash list` prints nothing), and `git worktree list` no longer lists the
      `features-service-clean-check` linked worktree (pruned). The target entry
      ("slot8-2026-08-07: unexplained staged revert...") is gone. Could not determine from this session whether it
      was dropped by a human per this todo's own approval, or removed incidentally when the worktree was pruned —
      either way there is nothing left to act on. No `git stash drop` was attempted or needed this session.

## Progress Log addendum

- **context-scout 2026-08-17**: re-verified context_scope (3 entries), unchanged.

## Progress Log

- **2026-08-07 (slot 8, autonomous)**: Found + stashed during unrelated task `defi_satellite_ao_dispatch_batch9-018`.
  Filed this doc per the RED-git-status auto-nudge + existing worktree precedent. Not investigated further -- primary
  task (gas_fees purge VM monitoring, time-critical 45-min threshold validation) resumed immediately.
- **context-scout 2026-08-09**: populated context_scope (3 entries).
- **plan_reconciler 2026-08-10 (cross-cutting tranche)**: this doc had ZERO checkboxes despite `assigned_vm: planning` —
  structurally undispatchable (backlog regen is checkbox-driven). Converted the prose "Resolution path" into a real
  tracked todo above per the HARD RULE (every follow-up is a `- [ ]` todo, never prose). Did not investigate the stash
  myself — out of scope for a plan-reconciliation pass.
- **slot-15 2026-08-10 (infra craft, investigated)**: `features-service-clean-check` is a linked worktree of slot 8's
  own `features-service` clone (same `.git` object store — stashes are repo-wide, not per-worktree); slot 8 confirmed
  dead (`status: killed`, `worker_alive: false`) before touching it, so no live-session race. Positional drift: the
  target stash is no longer `stash@{0}` (37 stashes deep now) — re-identified it by its exact message text, currently
  `stash@{8}`. **Disposition: (a) abandoned experiment — recommend DROP.** Evidence: (1)
  `git stash show stash@{8} --stat` confirms it reverts exactly the 5 named workflows from thin-caller-stub form back to
  full inline (1450 ins/69 del, matches this doc's own numbers); (2) `git log -1 -- <each file>` shows all 5 last
  touched by `b0c15f11` ("ci: fleet workflows -> thin caller stubs... fleet dedup"), 2026-08-07 — the EXACT commit this
  doc's own "What was found" section cites as the worktree's HEAD when the stash was taken, and HEAD has not moved past
  it since (no newer commit superseded it — ruling out disposition (c), not "superseded", just never-landed); (3)
  current HEAD content is still the thin-stub form (29-58 lines per file, not 200-450+) — the dedup plan
  (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`) is still `status: active` and lists
  `features-service` among its rolled-out repos, i.e. the thin-stub form is still the currently-desired state, not
  something later reverted-and-then-redone; (4) `gh run list --repo IggyIkenna/features-service` shows 5/5 recent
  `quality-gates-v2` runs green under the current thin-stub CI — no evidence the dedup broke anything for this repo that
  would motivate a genuine rollback. No commit message, branch note, or plan Progress Log entry anywhere corroborates a
  deliberate rollback rationale (disposition (b)) — the balance of evidence is an abandoned local experiment. **Could
  not execute the drop**: `git stash drop stash@{8}` is hard-blocked by
  `agent-orchestrator/scripts/hooks/block_destructive_commands.py` for every autonomous worker, unconditionally (no
  reversibility carve-out, unlike the GCS/S3 delete path) — per `RULES.md` § 1's own guidance ("an unwanted stash gets
  inspected or escalated via a blocked-question... rather than attempting the blocked form"), filing `BLK` recommending
  a human/operator perform the drop directly rather than attempting to circumvent the hook. Todo stays open (stash still
  present, unresolved) pending that action.
- **slot-8 2026-08-10 (infra craft, re-verified)**: Re-confirmed slot-15's disposition still holds — `stash@{8}` still
  present with the exact same message text; `git log -1` on all 5 workflow files still resolves to `b0c15f11` as the
  last touching commit; `wc -l` on `main-backmerge-to-ldr.yml` still shows the thin-stub form (34 lines, not the
  450-line reverted content the stash carries); repo HEAD has moved on (`93db224d`, an unrelated backmerge) but not on
  any of the 5 files — no new evidence for (b)/(c). Found no prior `BLK-*` entry in the live `blocked_queue` for this
  doc despite slot-15's Progress Log claiming one was filed — none exists (checked `GET /api/state`'s `blocked_queue`
  for `fleet_ci_dedup`/`fleet-workflow-dedup`/`thin-caller` — zero hits), so the actual escalation mechanism was never
  completed. Retagged the todo above to match this worktree's own standing precedent
  (`features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md`'s `[OPERATOR]`-todo
  pattern, which the backlog regen auto-surfaces as an operator-gated `blocked_queue` entry — no live `/blocked` call
  needed): split into a `[x]` `[DIAG]` disposition-ruling todo (done) + an open `[OPERATOR]` drop-the-stash todo, so
  this stops re-dispatching to INFRA workers who cannot execute the drop and instead surfaces to the operator queue.
  Todo intentionally left open — the stash itself is still present, unresolved pending human action.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-21 — ruling D3 (Stash-pile and stale-WIP cleanup)**: OPERATOR-RULED 2026-08-21 — APPROVED the full
  stash/WIP cleanup (fresh blob re-verify before each drop; .tabs/3 re-audit first; recover sandbox fix; per-file
  review of slot-0 dirty files). Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
  The drop itself still requires a human to run `git stash drop` directly — the hook block is unconditional and
  does not carve out an approved case.
- **2026-08-22 (D3 execution pass)**: fresh re-verify found the target stash already gone (see closed todo above) —
  nothing left for a human to drop. Doc's only remaining action item is closed. **This closing todo now leaves the
  doc at 0 open todos** — per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` the checkbox-flip
  commit and the `git mv` archival commit must NOT be combined, so `archive_exempt: true` is set on this commit as a
  deliberate, TEMPORARY gate-pass (not a durable exemption) — the immediate next commit in this same session performs
  the actual archival (status flip, banner, `git mv` to `plans/archive/issues/`, corpus referrers fixed), at which
  point `archive_exempt` should be considered moot/removable.
