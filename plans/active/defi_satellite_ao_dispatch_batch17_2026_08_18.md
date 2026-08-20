---
doc_type: plan
title: DeFi satellite AO batch 17 — per-todo RECLASSIFY-split extraction from na-eligibility-audit 2026-08-18
summary: >-
  Satellite-batch extraction from the 2026-08-18 /na-eligibility-audit defi run's per-todo RECLASSIFY split path,
  extracting the 2 bounded confirm-and-report items from a brand-new source doc,
  mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md (3 of 4 code-shipped MEV strategy engines have
  no producer for their own opportunity-detection features). The doc's other 4 items (build 3 new feature
  calculators + a downstream UAC registry declaration gated on those) are genuine design/build work, not bounded —
  they stay in the source doc under `assigned_vm: NA`. Both extracted items conflict-checked against every active
  defi covering doc (consolidated closeout, satellite batch2/11/14/16 + finalize pairs, track01/track5,
  defi_gas_net_cost_partial_wiring_gap — the explicitly cross-referenced sibling finding on the COST side of the
  same MEV engines) — zero prior claim found on either.
status: active
nature: process
asset_group: [defi]
stage: [strategy, features]
repos: [strategy-service, execution-service]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-17, na-eligibility-audit, reclassification, mev]
related:
  [
    /plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md,
    /plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md,
    /plans/active/defi_satellite_ao_dispatch_batch17_2026_08_18_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: quant_dev
effort: medium
thinking_tier: high
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md,
    /plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/defi_satellite_ao_dispatch_batch17_2026_08_18_finalize.md,
    /plans/active/issues/mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md,
  ]
source: >-
  `/na-eligibility-audit defi` (2026-08-18, dispatch agt-2c8a26, slot 31). Both items cleared the shared
  conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) against every
  active defi covering doc. Per-item Source: citations below point at the exact originating doc + todo.
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 17 — 2026-08-18

## Todos

- [x] ✅ [REVIEW] P2. **Confirmed: NONE of the 3 MEV engines call `TenderlyExecutionProvider.simulate-bundle` (or its
      `gate_or_advise()` pre-flight wrapper) before submission — and `gate_or_advise()` has zero callers anywhere in
      the repo tree, so nothing is wired to it at all.** Direct code read, not a grep proxy:
      `strategy-service/strategy_service/engine/strategies/v2/mev/{liquidation_bundle,jit_liquidity,sandwich_theoretical}.py`
      import only `unified_api_contracts.internal` + sibling `strategy_service` modules — zero references to
      `execution_service`/Tenderly/`simulate`. `execution_service/providers/tenderly.py:331` defines
      `TenderlyExecutionProvider.simulate_bundle()`; its only production caller is `gate_or_advise()`
      (same file, lines 458-484); `gate_or_advise()` itself has no callers outside its own module family
      (`tenderly.py`/`tenderly_budget.py`/`_tenderly_errors.py`). **Correction to this todo's own premise**:
      `matching_engine.py` does NOT call `TenderlyExecutionProvider` either — it only mentions it in
      docstrings/comments ("Route EVM DeFi legs through TenderlyExecutionProvider",
      `execution_service/providers/matching_engine.py:15,18,261`) and raises `NotImplementedError` for EVM DeFi legs
      instead of actually routing to it. This IS a genuine pre-submission safety gap (worst for `LIQUIDATION_BUNDLE`'s
      atomic flash-loan bundle) but needs a design call (single call site in `matching_engine.py`'s EVM DeFi dispatch
      vs. 3 per-engine call sites) — filed as its own follow-up per this todo's own "Done when" bar rather than fixed
      inline: `plans/active/issues/mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md`. Repo:
      strategy-service, execution-service (docs only, no code shipped this pass). Source:
      `plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` todo 1 (line ~126).
- [x] ✅ [REVIEW] P1. **Confirmed the exact default behavior at `liquidation_bundle.py:265-269`
      (`_candidate_from_features`).** `.get(id_key)` — no default argument at all. On any missing key the function
      returns `None` for the whole candidate (explicit `is None` checks; own docstring: "Returns `None` when any
      required key is missing — the orchestrator should backfill the calculator before this engine emits"), and
      `on_tick()` `continue`s past that candidate. Not a `KeyError`, not a silent coercion, and — the important
      contrast — NOT the same silent-zero pattern as `backrun`/`jit_liquidity`'s `.get(key, 0.0)`: this engine
      declines to act on missing data instead of fabricating a comparison against a fake zero. Net effect on the
      candidate-identification producer todo: purely additive — no engine-side correctness fix needed alongside it.
      Repo: strategy-service. Reported back into the source doc
      (`plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`, §"NOT WIRED" item 3,
      updated same pass).

## Progress Log

- **2026-08-18 (na-eligibility-audit, defi tranche, dispatch agt-2c8a26)**: drafted via the per-todo RECLASSIFY-split
  path. Source doc filed the same day (brand new, never previously audited) with 6 open todos in a clear bounded/
  unbounded mix: todos 1-2 (extracted here) are pure confirm-and-report code reads with a determinable outcome; todos
  3-5 are real feature-calculator design/build work (each explicitly states an unresolved design question — "needs a
  design decision on exact derivation, not a blind guess," "reconcile the doc against the code before building
  anything new," "the exact ID-keyed shape... needs confirming"); todo 6 is explicitly gated on 3/4/5 landing. Both
  extracted items conflict-checked against the full active-defi covering set, including the explicitly
  cross-referenced sibling `defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` (same 2 engines, but the COST side —
  confirmed no overlap: that doc's own todos are gas/fee-netting math, never Tenderly simulation or the
  `liq_candidate_*` trigger-key defaults) and `defi_satellite_ao_dispatch_batch16_2026_08_17.md` (mentions
  `liquidation_bundle.py` but at different line ranges, for the unrelated profit-gating computation, not the
  candidate-identification triggers) — zero prior claims found on either extracted item. Paired with
  `defi_satellite_ao_dispatch_batch17_2026_08_18_finalize.md` (`depends_on` + `gate_on_depends: true`,
  `status: active`) in the same turn.
- **2026-08-18 (interactive, slot-6)**: closed the `[REVIEW] P1` `liquidation_bundle.py` default-behavior todo —
  direct code read of `_candidate_from_features` (lines 255-287), no design call needed. Finding reported back into
  the source doc per the todo's own "Done when" bar. Remaining item in this batch (`[REVIEW] P2` Tenderly
  `simulate-bundle` call-site confirmation) untouched — separate scope, not part of this pass.
- **2026-08-19 (slot-10, review)**: closed the `[REVIEW] P2` Tenderly `simulate-bundle` call-site todo — confirmed
  via direct code read that none of the 3 MEV engines (nor `matching_engine.py`) call `simulate_bundle`/
  `gate_or_advise`; `gate_or_advise` has zero callers anywhere in the repo. Filed the genuine gap as its own
  follow-up (needs a design call on call-site placement, not a mechanical fix) rather than fixing inline:
  `plans/active/issues/mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md`. Every todo in this batch is
  now closed; not archiving this pass since `defi_satellite_ao_dispatch_batch17_2026_08_18_finalize.md` gates on it
  via `depends_on`/`gate_on_depends: true` — leave archival to that finalize plan's own flow.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
