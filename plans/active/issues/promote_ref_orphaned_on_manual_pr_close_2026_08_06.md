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
status: open
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

- [ ] [DEVOPS] P3. Fleet-bot orphan-ref sweep: in `ldr_to_main_fleet_promote.sh`'s "Superseded ref cleanup" step (or the
      PM-only `ldr-to-main-promote.yml` twin), after the existing `gh pr list --state open`-driven cleanup, list
      `promote/<repo>/*` refs and delete those with no open PR and not equal to the current `PROMOTE_HEAD`. Owner:
      LDR→main fleet bot maintainer (unified-trading-pm). Done-when: a live fleet-promoter run's log shows the new sweep
      step executing with zero errors, and `git ls-remote` for at least one repo with known pre-existing orphans (e.g.
      `execution-service`) shows those orphan `promote/execution-service/*` refs gone.

## Progress Log

- **context-scout 2026-08-07**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-08**: Phase 2/3 — re-verified whole-doc bar: the sole open todo (fleet-bot orphan-ref
  sweep in `ldr_to_main_fleet_promote.sh`) is a fully bounded, scoped code change with no judgment call left undecided.
  Conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) run against (a) every
  `status: active`/`assigned_vm: planning` plan in `parent_epic: infrastructure_master`, (b) sibling `ci`
  batch/finalize docs (`ci_satellite_ao_dispatch_batch{1,4,5}*`), (c) `ag_closeout_audit_cross_cutting_parked_2026_08_07.md`
  (which independently found this doc's own todo "real, live, undispatched work" and recommended only an `asset_group`
  retag, a milestone-only, non-conflicting overlap) — zero prior claim on this ground found, CLEAR. Also fixed the
  todo's own malformed `[P3]`-only bracket (missing a real `[TAG]`, which `regen_backlog_from_plan.py`'s
  `[TAG] P<n>.` parser would not have routed/prioritized correctly) to `[DEVOPS] P3.` and added an explicit
  done-when. Flipped `assigned_vm: NA` → `planning`, `execution_scope: local-only` → `orchestrator-agent`, added
  `assigned_role: cicd` (was absent; validated against `agents/cicd.md`'s `role: cicd`, not the near-miss `devops`
  used elsewhere in this corpus). **No finalize twin authored** — verified against
  `scripts/quality_gates/check_finalize_plan_coverage.py` directly: it globs only `plans/active/*.md` (not the
  `issues/` subdirectory this doc lives in) AND separately exempts any plan with ≤1 open todo (`_todo_count(...) <= 1:
  continue # single-todo carve-out`) — this doc clears both the structural (issues/) and content (single-todo)
  exemptions task_template.md §4 documents, so archival folds into this one todo's own done-when instead.
