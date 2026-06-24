---
title: "IS tradfi trades provenance test asserts massive-first but UAC derives databento-first (foreign skew)"
created: 2026-06-24
source:
  - instruments-service/tests/unit/scripts/test_enumerate_provenance_stamping.py::test_tradfi_trades_seed_carries_massive_batch_rest
  - unified-api-contracts SOURCE_PRIORITY (tradfi/trades)
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

`tests/unit/scripts/test_enumerate_provenance_stamping.py::test_tradfi_trades_seed_carries_massive_batch_rest`
FAILS on clean `origin/live-defi-rollout` (instruments-service): it asserts the tradfi/trades seed
derives `pipeline_mode == "batch_massive"` / `source == "massive"`, but
`enumerate_expected_universe._derive_pm_source_transport("tradfi","trades")` now returns
`batch_databento` / `databento`.

The test docstring cites "MASSIVE-FIRST per operator ratification 2026-06-11". But the live UAC
`SOURCE_PRIORITY` for tradfi was changed (the 2026-06-21 CLAUDE.md tradfi-databento lockdown:
"the sole tradfi live WS producer is databento"; `live_source_for_venue` tradfi branch returns
`databento`). The BATCH-path derivation now also resolves databento-first.

This is NOT a DeFi-pipeline change — it is a pre-existing UAC↔IS-test skew, surfaced while running
the IS whole-tree QG for the DeFi dual-form catalogue ship (this plan:
`defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md`). The DeFi ship deselects it.

## Why it matters

It blocks the IS whole-tree `quality-gates.sh` sentinel, so it gates every IS ship until
reconciled. It is one test asserting a stale source-priority.

## Recommended decision

Diagnose which is canonical for tradfi/trades BATCH provenance:
- If databento-first is correct (matches the 2026-06-21 lockdown + live `_derive`), update the test
  + its docstring to `batch_databento`/`databento`.
- If massive-first is still the batch SSOT (massive is `Mode.LIVE`-capable, operator 2026-06-05),
  fix `_derive_pm_source_transport` / the UAC tradfi batch SOURCE_PRIORITY to return massive.

Owner: tradfi epic VM (mtds_mdps_master / tradfi_master). Not in scope for the DeFi catalogue plan.
