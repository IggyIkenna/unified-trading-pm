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
status: complete # (was: active) 2026-08-03 -- todo done, parent + this twin archived together
nature: process
asset_group: [cefi]
stage: [strategy]
repos: [strategy-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/archive/2026_08/vol_dvol_backtestable_engines_2026_07_13.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-08-03"
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
    /plans/archive/2026_08/vol_dvol_backtestable_engines_2026_07_13.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# VOL/DVOL backtestable engines — finalize

> **✅ ARCHIVED 2026-08-03 — todo DONE.** Re-verified the parent independently rather than trusting its own evidence
> lines: measured the CONSOLIDATED manifest directly (1955 distinct dates × {BTC, ETH}, 2021-03-24→2026-07-30, 100%
> `captured`); confirmed 0/2 engines flipped to `available` (so no fresh backtest re-run was owed — that step only
> applies to a flipped engine); confirmed `capability-verdict-matrix.json`@`14dbb6d1` genuinely reflects 0/2; ran the
> 6-step archival ritual and archived the parent alongside this twin in the same commit. See Progress Log below.

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

- [x] ✅ [SCRIPT] P2. **Verify the parent's 5 todos against their own stated criteria, then check archival
      eligibility.** — **DONE 2026-08-03 (slot-13, `backend_engineer`).** (1) **Measured, not trusted**: read the
      CONSOLIDATED availability manifest directly via `unified_trading_library.read_availability_index_safe` against
      `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="cefi")`, filtered
      `data_type=volatility_index`/`venue=DERIBIT` — **1955 distinct captured dates for BOTH BTC and ETH, span exactly
      2021-03-24→2026-07-30** (matches the expected inclusive calendar-day count exactly), 100%
      `capture_status=captured`, 0 failed/empty. (A few harmless duplicate rows exist for 3 specific dates —
      2026-07-08/09/13 — from the earlier small connectivity-test overlapping the later full backfill; distinct-date
      count, which is what the window claim rests on, is exact.) This independently confirms the parent's claimed range
      — not a re-quote. (2) **0 of 2 engines flipped to `available`** — re-confirmed live, zero hits for
      `VOL_CARRY`/`VOL_ARB_RV_IV` in `strategy_service/engine/strategies/v2/factory.py`'s `ARCHETYPE_ENGINE_REGISTRY` —
      so the "re-run backtest for any flipped engine" step is vacuously satisfied (it only applies to an engine that WAS
      registered; neither was). (3) Confirmed `capability-verdict-matrix.json`@`14dbb6d1` (unified-api-contracts)
      genuinely reflects 0/2 flipped — both archetypes still `not_registered(no_v2_engine)`, summary totals
      byte-identical to the prior regen. (4) Grepped the parent: zero remaining `- [ ]` items, `locked_by:` empty →
      archival candidate confirmed. Ran the 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): fixed every corpus referrer pointing at
      the parent's `plans/active/` path (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`,
      `v2_engine_venue_buildout_2026_06_15.md` ×5, `plans/epics/strategy_master.md` ×2,
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s stale bare-slug prose claim); no new codex contract
      needed (the memory-bounding + one-off-backfill-VM-launcher patterns the parent used were both pre-existing
      established patterns, not new ones it introduced); archived the parent alongside this twin into
      `plans/archive/2026_08/` in the same commit. **Done when met**: measured DVOL date range recorded above, 0 engines
      needed a fresh backtest (none registered), and the parent is archived (not left with remaining open items). Repos:
      unified-trading-pm only (verification found nothing to change in
      strategy-service/market-tick-data-service/unified-api-contracts — 0 registrations flipped, no code follow-up
      owed).

## Progress Log

- **2026-07-30** — Created by `/na-eligibility-audit` (tranche=cefi, autonomous) as the paired finalize twin for the
  parent's `NA → planning` reclassification, per `plans/active/task_template.md`'s finalize-plan-coverage rule
  (`check_finalize_plan_coverage.py` globs `plans/active/*.md`, so a `doc_type: plan` reclassification needs the twin;
  issue docs are structurally exempt). No parent content duplicated here — this twin only verifies.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-03 (slot-13, `backend_engineer`)**: Closed the todo. Independently re-measured the DVOL manifest
  (consolidated availability index, not the per-VM shard) — 1955 distinct dates × {BTC, ETH}, 2021-03-24→2026-07-30,
  100% captured, confirming the parent's claim rather than trusting it. Confirmed 0/2 engines registered (no re-backtest
  owed) and the matrix regen (`14dbb6d1`) correctly reflects that. Fixed all corpus referrers to the parent's
  `plans/active/` path (5 files). Archived both this twin and the parent into `plans/archive/2026_08/` in the same
  commit as the standard 6-step ritual's final step.
