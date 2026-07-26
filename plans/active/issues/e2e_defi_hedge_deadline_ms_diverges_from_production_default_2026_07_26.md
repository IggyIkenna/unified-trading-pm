---
doc_type: issue
title:
  e2e DeFi staked-basis smokes hard-code hedge_deadline_ms=2000, production default is 5000 — one of 5 behavioural
  params diverges
summary: >-
  Audit of the 5 e2e-hardcoded behavioural params (entry_bps/exit_bps/min_health_factor/hedge_deadline_ms/
  peg_drift_threshold_bps) vs their production/engine-intended defaults, per the "NEW findings" P2 ask in
  e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md and defi_satellite_ao_dispatch_batch2_2026_07_26.md item 4. 4
  of 5 match exactly; hedge_deadline_ms does not.
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [e2e-testing, strategy-service]
scope: [engineer]
tags: [defi, e2e, strategy, config, param-audit]
related:
  [
    /plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: strategy_master
priority: P3
source:
  [
    e2e-testing/scripts/defi/test_csb_paper_e2e_smoke.py,
    e2e-testing/scripts/defi/test_apd_paper_e2e_smoke.py,
    e2e-testing/scripts/defi/test_concurrent_archetype_e2e_smoke.py,
    e2e-testing/scripts/defi/test_failure_modes_e2e_smoke.py,
    e2e-testing/scripts/defi/test_additional_asset_groups_e2e_smoke.py,
    strategy-service/strategy_service/engine/strategies/v2/param_schema.py,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
  ]
estimate_class: research
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Comparison of the 5 behavioural params the e2e DeFi catalog leaves at engine defaults
(`e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` "NEW findings" P2 ask) against the production/engine-intended
values, sourced from `strategy-service/strategy_service/engine/strategies/v2/param_schema.py`'s `CARRY_STAKED_BASIS`
param-schema block and cross-checked against the literal defaults in `staked_basis.py`:

| param                     | e2e value (all 5 files: `test_csb_paper_e2e_smoke.py`, `test_apd_paper_e2e_smoke.py`, `test_concurrent_archetype_e2e_smoke.py`, `test_failure_modes_e2e_smoke.py`, `test_additional_asset_groups_e2e_smoke.py`) | production default (`param_schema.py` / `staked_basis.py`)                                                                   | verdict           |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| `entry_bps`               | `"200"`                                                                                                                                                                                                         | `200` (`staked_basis.py:387`)                                                                                                | match             |
| `exit_bps`                | `"50"`                                                                                                                                                                                                          | `50` (`staked_basis.py:388`)                                                                                                 | match             |
| `min_health_factor`       | `"1.25"`                                                                                                                                                                                                        | `1.25` (`staked_basis.py:357`)                                                                                               | match             |
| `peg_drift_threshold_bps` | unset (falls through to engine default)                                                                                                                                                                         | `25` (`dynamic_hedge_ratio.py` `DEFAULT_PEG_DRIFT_THRESHOLD_BPS`)                                                            | match by omission |
| `hedge_deadline_ms`       | `"2000"` (all 5 files, no per-test variation)                                                                                                                                                                   | `5000` (`param_schema.py` source-cites `staked_basis.py:598`; confirmed `int_param(self.params, "hedge_deadline_ms", 5000)`) | **MISMATCH**      |

`hedge_deadline_ms` is identically `2000` across every e2e file that sets it — not a per-test tuning choice, and no
comment anywhere in `e2e-testing/scripts/defi/` explains the divergence from the production default.

## Why it matters

Two readings, both plausible, requiring an owner decision rather than a unilateral fix:

1. **Unintentional drift**: nobody has revisited this literal since it was first copy-pasted across the 5 e2e files, and
   the e2e smokes are silently exercising a materially tighter (2.5x faster) leader/hedge atomic-execution deadline than
   production intends — meaning a hedge-leg race/timeout condition that would surface at 5000ms in production could be
   masked or never triggered at the tighter 2000ms in e2e (or vice versa: a spurious e2e timeout that would never occur
   in production).
2. **Deliberate test-speed choice**: e2e smokes may intentionally use a tighter deadline purely to keep CI wall-clock
   down, with no correctness implication (the deadline is a max-wait ceiling, not a target).

This is exactly the kind of "tests prove the engine, not the deployable config" fidelity gap the parent issue doc flags
— D1 in that doc turned out to be operator-confirmed-intentional (isolation phase), so precedent exists for either
verdict here.

## Recommended decision

Ack + route to the strategy-engine e2e owner. Options:

- **A**: If deliberate (test-speed), add a one-line comment at each of the 5 call sites citing this issue doc, so the
  divergence reads as intentional rather than silent drift. No functional change.
- **B**: If unintentional, bump all 5 to `hedge_deadline_ms: "5000"` to match production intent (functional parity with
  the taxonomy audit's goal).

- [ ] [SCRIPT] P3. Resolve the `hedge_deadline_ms` 2000-vs-5000 divergence per the operator's A/B call above — either
      comment the 5 e2e call sites as intentional, or bump them to 5000. Repo: e2e-testing. Files:
      `test_csb_paper_e2e_smoke.py`, `test_apd_paper_e2e_smoke.py`, `test_concurrent_archetype_e2e_smoke.py`,
      `test_failure_modes_e2e_smoke.py`, `test_additional_asset_groups_e2e_smoke.py` (2 call sites in the last file).
