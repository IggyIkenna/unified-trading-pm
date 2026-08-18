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
last_updated: "2026-08-18"
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

- [ ] [REVIEW] P2. **Confirm whether the MEV engines actually call `TenderlyExecutionProvider.simulate-bundle` before
      submission.** A real `TenderlyExecutionProvider` exists (`execution-service/execution_service/providers/tenderly.py`
      — Tenderly Virtual TestNet fork + `simulate-bundle` support, `TenderlyTx`/`BundleSimResult`) and is wired into the
      core `matching_engine.py` (not governance-only — `governance/proposal_simulator.py` is a separate consumer of the
      same generic provider), but no MEV-engine (`liquidation_bundle.py`/`jit_liquidity.py`/`sandwich_theoretical.py`)
      call site was confirmed in the source doc's own pass. If unused, this is a real pre-submission safety gap for
      `LIQUIDATION_BUNDLE`'s atomic flash-loan bundle specifically (a revert there costs gas only, but an unsimulated
      bundle is still a worse bet than a simulated one). Repo: strategy-service, execution-service. Source:
      `plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` todo 1 (line ~126). Done
      when: each of the 3 MEV engines' call (or non-call) to `simulate-bundle` is confirmed with cited file:line
      evidence, and any genuine gap found is filed as its own follow-up rather than fixed inline if it needs a design
      call.
- [ ] [REVIEW] P1. **Confirm the exact default behavior at `liquidation_bundle.py:265-267`.**
      `liq_candidate_debt_amount_<id>`, `liq_candidate_health_factor_<id>`, `liq_candidate_liq_bonus_pct_<id>` are read
      via `.get(id_key)` with no explicit default shown in the source doc's own pass — could be `None` (raising
      downstream), a bare `KeyError`, or silently coerced to something else. Read the exact call sites and trace what
      actually happens on a miss before any fix to the candidate-identification producer is scoped. Repo:
      strategy-service. Source: `plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`
      todo 2 (line ~131). Done when: the exact default/failure behavior is confirmed with cited code evidence and
      reported back into the source doc (and, if it's a silent-default masking a real gap, flagged the same way the
      sibling `backrun`/`jit_liquidity` trigger-defaults-to-0.0 pattern already is in that doc).

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
