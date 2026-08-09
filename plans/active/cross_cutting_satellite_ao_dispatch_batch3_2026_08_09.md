---
doc_type: plan
title:
  Cross-cutting satellite AO batch 3 — mtds_mdps_master bounded residuals extracted from the 2026-08-09
  satellite-batch-extraction sweep
summary: >-
  Third AO-dispatch batch for the cross-cutting tranche, produced by the same 2026-08-09 satellite-batch-extraction pass
  as batch 2 — this one pulls the bounded, worker-determinable items out of the `mtds_mdps_master` source docs:
  `data_source_provenance_enforcement_2026_07_24.md` (5 items — the highest-yield doc in this pass, 5 of its 19 open
  items clear the eligibility bar) and `legacy_bucket_dual_write_decommission_2026_07_24.md` (2 items). Every genuinely
  gated item — the per-AG whole-corpus backfill single-walks, the manifest dedup-key sequencing decision, whole-bucket
  destroys, items sequenced behind an unresolved dependency — stays in its source doc untouched. One stale checkbox (an
  obsolete Massive-TradFi backfill item, superseded by the 2026-07-19 vendor removal) was flagged by the classifying
  agent but is NOT actioned here — left for a maintainer pass on the source doc since it needs deletion/correction, not
  dispatch.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-3, satellite-docs, mtds-mdps-master]
related:
  [
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch3_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Satellite-batch-extraction sweep 2026-08-09 (8 parallel classification agents over the cross-cutting tranche's 27
  RECLASSIFY-non-qualifying NA docs), mirroring `/ag-closeout-audit`'s satellite-batch pattern.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 3 (mtds_mdps_master) — bounded-item extraction

> **Status: active.** All 7 todos below are same-priority-independent and touch distinct files/repos — no
> `sequential`/`gate_on_depends` needed. Each todo cites its source doc; this batch's finalize twin
> (`cross_cutting_satellite_ao_dispatch_batch3_2026_08_09_finalize.md`) reconciles both source docs once this batch is
> done.

## Todos

- [ ] [SCRIPT] P1. Write `backfill_defi_source_column.py` (copy the existing TradFi template script) to stamp the known
      historical `source` per `data_type`: most DeFi data_types → `onchain_subgraph`; `oracle_prices` → resolve `pyth`
      vs. `chainlink` from the existing `pipeline_mode`/path; `native_staking_rates` → `solana_rpc` vs. `helius_rpc`.
      Idempotent (safe re-run, no duplicate writes). Repo: market-tick-data-service (or wherever the cited TradFi
      template script lives). Source: `data_source_provenance_enforcement_2026_07_24.md` (backfill-script item). Done
      when: the script exists, implements the 3 stated per-`data_type` mapping rules, and is verified idempotent on a
      re-run.
- [ ] [MTDS] P1. Confirm `record_empty_for_shard`/`record_failed_for_shard` in market-data-processing-service's
      `canonical_writer.py` forward a `source` parameter the same way the already-shipped captured-write-path does —
      thread it through if either function currently drops it. Repo: market-data-processing-service. Source:
      `data_source_provenance_enforcement_2026_07_24.md` (empty/failed-path source-forwarding item). Done when: both
      functions accept and forward `source`, verified against the already-shipped captured-path pattern in the same
      file, with a regression test.
- [ ] [TEST] P1. Add a CeFi unit test asserting: (a) a cefi manifest cell without `source=` raises; (b)
      `source='tardis'` persists correctly; (c) a future `['<alt>', 'tardis']` `SOURCE_PRIORITY` registry expansion
      resolves two sources by priority order. Repo: market-tick-data-service. Source:
      `data_source_provenance_enforcement_2026_07_24.md` (CeFi source-stamping test item). Done when: the unit test
      covers all 3 named assertions and is green in CI. If the "raises on blank" gate isn't actually live for cefi yet,
      report that as a finding rather than fabricating a passing test.
- [ ] [TEST] P1. Add an `available_at`-parity fixture test: a 2-source fixture (TradFi is the one live 2-source pair
      today) asserts identical `available_at` derivation per cell regardless of which registered source wrote it, so
      adding/swapping a source never shifts the lookahead window. Repo: market-tick-data-service or
      market-data-processing-service. Source: `data_source_provenance_enforcement_2026_07_24.md` (`available_at`-parity
      item). Done when: the fixture test asserts identical `available_at` derivation from the `SOURCE_PRIORITY` top
      entry across both sources for the same cell.
- [ ] [MTDS] P1. A12a — wire the `assert_defi_catalog_fresh(...)` preflight into the 8 still-unwired DeFi collect
      handlers: `lending_indices_handler`, `liquidations_handler`, `liquidation_events_handler`,
      `bridge_events_handler`, `token_transfers_handler`, `aggregator_route_handler`, `flash_loan_events_handler`,
      `solana_defi_handler` — mirror the already-shipped pattern in the 15 sibling handlers wired via
      `market-tick-data-service@f7d6f5fd` (call at the `process()`/per-shard chokepoint; existing tests patch the call
      to `True`). Also add the DeFi row to `/codex/04-architecture/instruments-preflight-chain.md`. Repo:
      market-tick-data-service, unified-trading-pm. Source: `data_source_provenance_enforcement_2026_07_24.md` (A12a
      remaining-handlers item). Done when: each of the 8 named handlers calls `assert_defi_catalog_fresh(...)` at its
      `process()` chokepoint; their existing tests patch the call to `True`; the codex row is added.
- [ ] [INFRA] P0. Migration data-copy fan-out — the operator-decision gate that previously blocked this (tarball
      pin-retention) is resolved per the source doc's own 2026-08-08 note: confirm the launcher correctly uses
      `tarball_pins.collect_in_use_pins()`/the SHA-pin path, then re-attempt the 20-VM fan-out to completion. Retag the
      source doc's `BLOCKED-INFRA` marker on this item once confirmed resolved — it is stale relative to the cited
      2026-08-08 resolution. Repo: deployment-service. Source: `legacy_bucket_dual_write_decommission_2026_07_24.md`
      (migration data-copy fan-out item). Done when: the launcher's pin usage is verified correct; the 20-VM fan-out is
      re-launched and completes without exit-2.
- [ ] [INFRA] P0. Remove the 8 already-paused (not-yet-removed) legacy manifest-consolidator cron Terraform blocks for
      cefi/defi/tradfi/sports (prediction's is already removed) from `manifest_consolidator_scheduler.tf` — the
      underlying Cloud Scheduler jobs are already inert ("PAUSED-not-removed"), so this is a reversible config cleanup,
      not a new pause action; coordinate with the liveness-watchdog plan if it references these same resources. Repo:
      deployment-service. Source: `legacy_bucket_dual_write_decommission_2026_07_24.md` (pause-crons item). Done when:
      `tofu plan` shows the 8 named scheduler-resource blocks removed with no unintended drift; the corresponding Cloud
      Scheduler jobs stay paused/absent.

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility",
`/codex/04-architecture/instruments-preflight-chain.md`.

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep. 7 items extracted from 2 `mtds_mdps_master`
  source docs (5 from `data_source_provenance_enforcement_2026_07_24.md`, 2 from
  `legacy_bucket_dual_write_decommission_2026_07_24.md`). No conflicts found against active `assigned_vm: planning`
  plans in this parent_epic.
