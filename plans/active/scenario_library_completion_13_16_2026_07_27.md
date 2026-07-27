---
doc_type: plan
title: Scenario library completion — execution_slippage_spike + lst_unstake_queue_blowup
summary:
  Implement the 2 orphaned Day-1 scenario designs (plans/active/scratch_scenarios_day1/13 and 16) into the UAC
  ScenarioOverlay registry + UTL applier, per operator decision (2026-07-27 pre-June-1 stale-plans audit) — the other 16
  of 18 Day-1 scenarios were all consumed one way or another; these 2 were designed 2026-05-12 and never picked up
  anywhere.
status: active
nature: process
asset_group: [defi, cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [scenario-injection, uac, defi, execution, lst, game-day]
related: []
created: 2026-07-27
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source:
  [
    plans/active/scratch_scenarios_day1/13_execution_slippage_spike.md,
    plans/active/scratch_scenarios_day1/16_lst_unstake_queue_blowup.md,
  ]
assigned_role: backend_engineer
drift_direction: none
---

# Scenario library completion — execution_slippage_spike + lst_unstake_queue_blowup

## Context

16 of the 18 `plans/active/scratch_scenarios_day1/*.md` Day-1 scenario designs (2026-05-11/12) were consumed somewhere —
the `unified-api-contracts` `ScenarioOverlay` registry (`registry/scenarios/{cefi,defi,cross_asset}.py`), a smoke test,
a runbook verifier, or an alerting-service subscriber. 2 were not: `13_execution_slippage_spike.md` and
`16_lst_unstake_queue_blowup.md` have zero downstream consumption anywhere. The registry pattern is established (see
e.g. `DEFI_CHAIN_RPC_OUTAGE_SOLANA` in `registry/scenarios/defi.py:44-70` — a `ScenarioOverlay` with `scenario_id`,
`category`, `layer`, `asset_groups`, `applies_to` filter, `mutation_spec`, and `expected_outcomes` assertions).

## Todos

- [ ] [CODE] P2. **Implement `execution_slippage_spike` as a `ScenarioOverlay`.** Read
      `plans/active/scratch_scenarios_day1/13_execution_slippage_spike.md` in full for the exact mutation spec and
      expected outcomes it designed. Add it to `unified-api-contracts/unified_api_contracts/registry/scenarios/` (likely
      `cross_asset.py` or `defi.py` depending on scope — check the source doc), following the
      `DEFI_CHAIN_RPC_OUTAGE_SOLANA` pattern (category, layer, `applies_to` filter, `mutation_spec`, `expected_outcomes`
      with real breaker/kill-switch/alert-code assertions, not placeholders).
- [ ] [CODE] P2. **Implement `lst_unstake_queue_blowup` as a `ScenarioOverlay`.** Read
      `plans/active/scratch_scenarios_day1/16_lst_unstake_queue_blowup.md` in full for the exact mutation spec and
      expected outcomes it designed. Add it to the UAC registry (likely `defi.py`, LST/restaking-adjacent — compare
      against the existing `defi_lst_depeg_steth_5pct` entry for a similar-shape neighbor).
- [ ] [VALIDATE] P3. **Wire both into the UTL applier + confirm consumption.** Verify `unified-trading-library`'s
      scenario applier actually picks up the 2 new `ScenarioOverlay` entries (mirrors how the other 16 scenarios are
      exercised — via UAC registry consumption directly, a smoke test, or a game-day runbook). Once confirmed consumed,
      update `plans/active/scratch_scenarios_day1/13_*.md` and `16_*.md` to note the registry entry they now back (they
      stay as design provenance, per the pattern set by scenarios 01-10).

## Progress Log

- 2026-07-27: Plan created per operator decision (pre-June-1 stale-plans audit) — implement both, don't drop.
