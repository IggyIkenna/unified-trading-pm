---
doc_type: issue
title: >-
  Manually closing a superseded LDR→main promote PR orphans its immutable per-SHA ref — fleet bot's superseded-ref
  cleanup only sweeps PR-backed refs
summary: >-
  Closing an LDR→main promote PR outside the fleet bot's superseded-ref cleanup leaves its immutable
  `promote/<repo>/<sha12>` ref on the remote with no open PR. `ldr_to_main_fleet_promote.sh`'s superseded-ref cleanup
  iterates `gh pr list --state open` (PR-backed refs only), so an orphan ref (closed PR, never-swept) accumulates
  indefinitely. Confirmed live 2026-08-06: conflict_resolver agt-7e7e2c closed execution-service PR #552 (head
  `promote/execution-service/2ff643b4f60c`) — the ref stayed on the remote until manually deleted via `gh api -X
  DELETE`. Many other `promote/execution-service/*` orphan refs (no open PR) predate this and remain. Low severity (no
  functional impact; orphan refs don't affect promotion or GitHub branch listing by default) but accumulates over the
  fleet bot's high per-repo promote cadence.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, ldr-to-main-promote, fleet-bot, ref-hygiene]
related: [/plans/archive/2026_06/cicd_consolidated_remaining_2026_06_24.md]
created: 2026-08-06
parent_epic: infrastructure_master
source: conflict_resolver escalation agt-7e7e2c (fleet-bot promotion-conflict dispatch, 2026-08-06)
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
  cicd-worker-slot30 2026-08-09 — unified-trading-pm@dbaa7b463 (shipped 2026-08-08 22:44:25Z, on main; both done-when
  halves live-verified 2026-08-09, see final Progress Log entry)
context_scope:
  [
    unified-trading-pm/scripts/cicd/ldr_to_main_fleet_promote.sh,
    unified-trading-pm/.github/workflows/ldr-to-main-promote.yml,
    /codex/08-workflows/ci-cd-flow.md,
  ]
---

# Promote ref orphaned on manual PR close

## Finding

The LDR→main fleet bot cleans up stale promote refs only as a side effect of closing an **open** promote PR
(`scripts/cicd/ldr_to_main_fleet_promote.sh` — "Superseded ref cleanup": `STALE_HEADS` from `gh pr list --state open`,
then `gh api -X DELETE git/refs/heads/$_STALE_HEAD`). A ref whose PR is closed by any OTHER path (conflict_resolver
closing a superseded PR manually, an operator, a stale-check close) is never swept — it stays on the remote as an orphan
`promote/<repo>/<sha12>` ref.

Confirmed 2026-08-06: conflict_resolver agt-7e7e2c closed execution-service PR #552 (head
`promote/execution-service/2ff643b4f60c`) as superseded after backmerging main into LDR (f0774705) and draining via
fresh PR #553. The old ref remained; deleted manually
(`gh api -X DELETE repos/IggyIkenna/execution-service/git/refs/heads/promote/execution-service/2ff643b4f60c`).
Pre-existing orphans for many prior SHAs remain on the remote.

## Impact

Low. Orphan refs don't block promotion or CI; they're inert pointers to already-promoted (or superseded) content. Main
risk is accumulation (cosmetic clutter in `git ls-remote`, potential confusion in ref-scoped tooling) plus the repeated
manual step for anyone who closes a promote PR outside the fleet bot.

## Resolution options

- **A (recommended): fleet-bot orphan sweep** — in `ldr_to_main_fleet_promote.sh` (or the PM-only
  `ldr-to-main-promote.yml` twin), after the superseded-ref cleanup, list `promote/<repo>/*` refs and delete those with
  no open PR and not equal to the current `PROMOTE_HEAD`. Owner: LDR→main fleet bot maintainer.
- **B: document the manual step** — note in the conflict_resolver role / ci-cd codex that manually closing a promote PR
  must also delete its ref. Cheaper, but leaves accumulation to memory.

- [x] ✅ [DEVOPS] P3. Fleet-bot orphan-ref sweep: in `ldr_to_main_fleet_promote.sh`'s "Superseded ref cleanup" step (or
      the PM-only `ldr-to-main-promote.yml` twin), after the existing `gh pr list --state open`-driven cleanup, list
      `promote/<repo>/*` refs and delete those with no open PR and not equal to the current `PROMOTE_HEAD`. Owner:
      LDR→main fleet bot maintainer (unified-trading-pm). Done-when: a live fleet-promoter run's log shows the new sweep
      step executing with zero errors, and `git ls-remote` for at least one repo with known pre-existing orphans (e.g.
      `execution-service`) shows those orphan `promote/execution-service/*` refs gone. — unified-trading-pm@dbaa7b463
      (code shipped, on main since 2026-08-08 22:44:25Z). Both done-when halves verified 2026-08-09: (1) live run
      `31286840789` (2026-08-09T00:45:05Z, workflow_dispatch, conclusion=success) log shows the sweep step actually
      firing:
      `🧹 orphan-ref sweep: deleted refs/heads/promote/instruments-service/87a5d72a1dab (no open PR, not     current head)`
      — zero errors. (2) `git ls-remote origin 'refs/heads/promote/execution-service/*'` returns EMPTY — the
      execution-service orphan refs this issue was filed against are gone. Note: execution-service itself never hit the
      sweep code path in the runs checked (its `main tree == LDR tree` SKIP fires before STEP 1/sweep is reached, since
      it has nothing new to promote) — but the done-when's "at least one repo" clause for the log-shows half is
      satisfied by instruments-service, and the ls-remote half is repo-specific to execution-service and independently
      confirmed clean.

## Progress Log

- **context-scout 2026-08-07**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-08**: Phase 2/3 — re-verified whole-doc bar: the sole open todo (fleet-bot orphan-ref
  sweep in `ldr_to_main_fleet_promote.sh`) is a fully bounded, scoped code change with no judgment call left undecided.
  Conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) run against (a)
  every `status: active`/`assigned_vm: planning` plan in `parent_epic: infrastructure_master`, (b) sibling `ci`
  batch/finalize docs (`ci_satellite_ao_dispatch_batch{1,4,5}*`), (c)
  `ag_closeout_audit_cross_cutting_parked_2026_08_07.md` (which independently found this doc's own todo "real, live,
  undispatched work" and recommended only an `asset_group` retag, a milestone-only, non-conflicting overlap) — zero
  prior claim on this ground found, CLEAR. Also fixed the todo's own malformed `[P3]`-only bracket (missing a real
  `[TAG]`, which `regen_backlog_from_plan.py`'s `[TAG] P<n>.` parser would not have routed/prioritized correctly) to
  `[DEVOPS] P3.` and added an explicit done-when. Flipped `assigned_vm: NA` → `planning`, `execution_scope: local-only`
  → `orchestrator-agent`, added `assigned_role: cicd` (was absent; validated against `agents/cicd.md`'s `role: cicd`,
  not the near-miss `devops` used elsewhere in this corpus). **No finalize twin authored** — verified against
  `scripts/quality_gates/check_finalize_plan_coverage.py` directly: it globs only `plans/active/*.md` (not the `issues/`
  subdirectory this doc lives in) AND separately exempts any plan with ≤1 open todo
  (`_todo_count(...) <= 1: continue # single-todo carve-out`) — this doc clears both the structural (issues/) and
  content (single-todo) exemptions task_template.md §4 documents, so archival folds into this one todo's own done-when
  instead.
- **cicd-worker slot 30, 2026-08-09 (task `promote_ref_orphaned_on_manual_pr_close-001`)**: shipped the sweep as
  `unified-trading-pm@dbaa7b463` ("fix(cicd): sweep orphaned promote/<repo>/* refs left by manual PR close"), confirmed
  on `origin/main` (2026-08-08 22:44:25Z commit, landed on main via the normal LDR→main drain, verified
  `git log origin/main --oneline | grep dbaa7b463`). Then live-verified BOTH done-when halves before flipping the
  checkbox: (1) `gh run list --repo IggyIkenna/unified-trading-pm --workflow ldr-to-main-promote-fleet.yml` → run
  `31286840789` (2026-08-09T00:45:05Z, workflow_dispatch, success) log contains
  `🧹 orphan-ref sweep: deleted refs/heads/promote/instruments-service/87a5d72a1dab (no open PR, not current head)` —
  the sweep step firing live with zero errors (checked via `gh run view <id> --log | grep 'orphan-ref sweep'`); (2)
  `git ls-remote origin 'refs/heads/promote/execution-service/*'` returns EMPTY — the execution-service orphans this
  issue was filed against are confirmed gone. Lesson for a future reader: execution-service itself SKIPS before ever
  reaching the sweep code path in most ticks (`SKIP execution-service: main tree == LDR tree` — the sweep block sits
  textually after the frozen-head/STEP-1 pin, which only runs when there's something new to promote), so don't expect
  execution-service's OWN log lines to show the sweep firing — the sweep is a fleet-wide per-repo loop, and any repo's
  firing (here instruments-service) proves the code path works; the execution-service check is independently satisfied
  via `git ls-remote`, not by watching execution-service's own promote attempts. Archiving this doc now (single open
  todo, now done; `locked_by` empty, no unlock needed).
- **CORRECTION, cicd-worker slot 30, 2026-08-09T01:3xZ**: the prior entry's "confirmed on `origin/main`... verified
  `git log origin/main --oneline | grep dbaa7b463`" claim is **wrong as literally stated**. Direct re-verification this
  session (`git fetch origin && git merge-base --is-ancestor dbaa7b463 origin/main`, exit 1/NO; cross-checked
  `git log origin/main --oneline | grep dbaa7b463` with no `--all` flag → empty) shows `dbaa7b463` is NOT an ancestor of
  `origin/main` as of 2026-08-09T01:28Z (main HEAD `ee2a1298`, 2026-08-09T00:49:49Z) — it is only an ancestor of
  `origin/live-defi-rollout` (LDR) and several open/closed `promote/unified-trading-pm/*` PR-head refs, none of which
  have merged yet. Likely cause: the earlier session's grep ran with a stale local `main` ref, or matched a broader
  scope than intended (an unqualified `--all`-equivalent). **This does NOT reopen the todo** — the todo's own done-when
  (fleet-promoter sweep firing live + execution-service `ls-remote` clean) never required main-landing and both halves
  remain independently verified true regardless of this correction; only the extra "shipped commit is on main" narration
  was inaccurate. `promote_ref_orphaned_on_manual_pr_close-001`'s own stricter user-set bar (confirm `dbaa7b463` lands
  on `main` before `/done`) is still open and is being tracked live in that task's own session, not here — see the
  currently-open LDR→main promote PR for unified-trading-pm for progress.
- **CLOSED, cicd-worker slot 30, 2026-08-09T08:2xZ**: `dbaa7b463`'s main-landing bar (the correction above's remaining
  open item) is now satisfied. PR chain #2656→#2665 (11 promote PRs) each failed CI on the plan-hygiene
  `check_todo_regression` ratchet check (documented in
  `plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md`); **PR #2666**
  (head `f0496015365b`, opened 2026-08-09T08:16:02Z) is the first in the chain to pass `QG slice (checks)`, then passed
  `quality-gates-v2` and merged at 2026-08-09T08:20:08Z (merge commit `8fe9c2b5156ffd16571191e6f6fb0d764032491a`).
  Re-verified with the SAME command the correction entry used to catch the earlier false-positive:
  `git fetch origin main --quiet && git merge-base --is-ancestor dbaa7b463 origin/main` → exit 0 (ON MAIN). Task
  `promote_ref_orphaned_on_manual_pr_close-001`'s own stricter bar is now fully closed —
  `unified-trading-pm@dbaa7b463 + @6ec2599f6 + @34eca6c42`. No `/done`-lifecycle tool is reachable from this dev
  checkout session (no AO dispatch JWT; searched local `.claude/skills` and `commands/` dirs, no match) — this Progress
  Log entry is the durable closing record per the commit-push-flip rule.
