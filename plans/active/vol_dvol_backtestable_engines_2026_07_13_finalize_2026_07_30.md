---
doc_type: plan
title: VOL/DVOL backtestable engines — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for vol_dvol_backtestable_engines_2026_07_13.md, reclassified `assigned_vm: NA -> planning` by the
  na-eligibility-audit cefi-tranche run 2026-07-30 (retroactive-reclassification shape, codex
  ao-dispatch-batch-naming-and-conflict-check.md §1(b) — name unchanged, bolt-on finalize twin). Once the source doc's 5
  todos (full DVOL history pull, VOL_CARRY backtest, conditional VOL_CARRY registration, VOL_ARB_RV_IV
  backtest-then-register, capability-verdict-matrix regen) are done, independently verifies the manifest actually spans
  the full 2021-03-24→now window, re-checks each registration against the HARD CONTRACT bar rather than trusting the
  source doc's own evidence lines, and checks whether the source doc is now itself an archival candidate.
status: active
nature: process
asset_group: [cefi]
stage: [strategy]
repos: [strategy-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/vol_dvol_backtestable_engines_2026_07_13.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
depends_on: [vol_dvol_backtestable_engines_2026_07_13]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit cefi tranche, 2026-07-30 (autonomous) — retroactive reclassification of an already-owned
  assigned_vm:NA doc per the skill's Phase 2/3. Conflict-check cleared: cross_cutting_satellite_ao_dispatch_batch2_
  2026_07_26.md and cefi_consolidated_closeout_aggregated_sources_2026_07_24.md both name THIS doc as the live owner of
  VOL_CARRY / VOL_ARB_RV_IV rather than claiming the work themselves, and the operator gate the plan was parked behind
  was RULED 2026-07-28 ("no longer operator-gated, now AO-dispatchable").
context_scope:
  [
    /plans/active/vol_dvol_backtestable_engines_2026_07_13.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# VOL/DVOL backtestable engines — finalize

> **Machine-gated on `vol_dvol_backtestable_engines_2026_07_13.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue this plan's todo until the parent's 5 todos are done.

## Why this twin exists

The parent was `assigned_vm: NA` purely because it was authored behind a `BLOCKED-OPERATOR-DECISION` gate on how much
DVOL history to pull. That gate was RULED 2026-07-28 (full history, 2021-03-24 → now) and the parent's own text now says
the remaining work is "a REAL data dependency, not an operator gate". Nothing re-assessed the `assigned_vm` after the
ruling — the classic mis-defaulted-NA shape this skill exists to catch. Per
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §1(b) the parent flips in place (name
unchanged) and gets this bolt-on finalize twin.

The parent's own Progress Log records that **3 slots already burned a dispatch on the stale operator-gate confusion** —
so the single most valuable thing this twin does is force a measured re-check of the data dependency instead of another
verify-from-scratch cycle.

## Todos

- [ ] [SCRIPT] P2. **Verify the parent's 5 todos against their own stated criteria, then check archival eligibility.**
      Once `vol_dvol_backtestable_engines_2026_07_13.md`'s todos are all `[x]`: (1) **Measure, do not trust** — read the
      manifest for `data_type=volatility_index` and confirm captured rows genuinely span the FULL `2021-03-24 → today`
      window for BOTH BTC and ETH (the parent's own `[SCRIPT]` todo warns the range must be checked before the backtest
      is picked up; re-check it here too rather than trusting the parent's evidence line). Report the measured first and
      last captured date per underlying. (2) For whichever of `VOL_CARRY` / `VOL_ARB_RV_IV` were flipped to `available`
      in `ARCHETYPE_ENGINE_REGISTRY`, re-run the `GroupBRunner` backtest and confirm it still clears the parent's HARD
      CONTRACT bar — a registration that only passes on the original run's cached artefacts is not a pass. (3) Confirm
      the regenerated `capability-verdict-matrix.json` commit actually reflects the engines that flipped (0, 1, or 2 —
      the parent explicitly forbids forcing both). (4) Grep the parent for remaining `- [ ]` items; if zero remain and
      `locked_by:` is empty, it is an archival candidate — run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), not just a checkbox flip, and fix every
      corpus referrer that points at `plans/active/`. **Done when**: the measured DVOL date range is recorded here, each
      registered engine has a fresh passing backtest cited by commit sha, and the parent is either archived or its
      remaining open items are named here. Repos: strategy-service, market-tick-data-service, unified-api-contracts,
      unified-trading-pm.

## Progress Log

- **2026-07-30** — Created by `/na-eligibility-audit` (tranche=cefi, autonomous) as the paired finalize twin for the
  parent's `NA → planning` reclassification, per `plans/active/task_template.md`'s finalize-plan-coverage rule
  (`check_finalize_plan_coverage.py` globs `plans/active/*.md`, so a `doc_type: plan` reclassification needs the twin;
  issue docs are structurally exempt). No parent content duplicated here — this twin only verifies.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
