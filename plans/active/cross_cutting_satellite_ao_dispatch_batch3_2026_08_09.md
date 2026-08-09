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
- [x] ✅ [INFRA] P0. Migration data-copy fan-out — **RESOLVED-MOOT, not re-launched: nothing to re-attempt.**
      Investigated the launcher before verifying pins per the todo's own instructions and found
      `deployment-service/scripts/vm/launch-legacy-bucket-migration-sharded.sh` was already deleted 2026-08-03
      (`deployment-service@d407b8b9`, "chore(vm): delete 2 confirmed-dead migration launchers") — its target script
      `market-tick-data-service/scripts/migrate_legacy_tick_buckets_to_canonical.py` was independently deleted
      2026-07-25 (`market-tick-data-service@4d235caf`/`@f8276e22`) once its own `Delete-when` clause was satisfied. This
      was already investigated and closed 2026-08-03 in `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2f/g/i
      (six days before this 2026-08-09 batch re-surfaced it as a still-actionable fan-out) — that investigation confirms
      the underlying migration completed via a path independent of this launcher, not that it was abandoned.
      Live-reverified 2026-08-09: all 5 legacy flat tick buckets the deleted script's `PAIRS` covered
      (`market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112`) return
      `BucketNotFoundException: 404` via `gsutil ls -b` — none exist, so there is no source data left to copy; all 5
      canonical `-prd-`/`pred-prd-` counterparts exist and are live. There is no launcher to verify pins on and no
      fan-out to re-launch — the drain→migrate→decommission sequence is already complete. Retagged the source doc's
      stale marker accordingly (see `legacy_bucket_dual_write_decommission_2026_07_24.md`'s RESOLVED-MOOT entry). Repo:
      deployment-service (nothing shipped — the launcher is correctly absent, not restored). Evidence:
      `deployment-service@d407b8b9`, `market-tick-data-service@4d235caf`/`@f8276e22`,
      `unified-trading-pm/plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2f/g/i, live
      `gsutil ls -b` 404s on all 5 legacy buckets (2026-08-09).
- [x] ✅ [INFRA] P0. Remove the 8 already-paused (not-yet-removed) legacy manifest-consolidator cron Terraform blocks
      for cefi/defi/tradfi/sports (prediction's is already removed) from `manifest_consolidator_scheduler.tf` —
      **VERIFIED ALREADY DONE, no code change needed.**
      `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` at live-defi-rollout HEAD (2c92c03d) carries
      no `-legacy` keys in `manifest_consolidator_buckets` / `manifest_consolidator_buckets_extended` — its own inline
      comments (L60-69, L99-101, L125-141) document the local-map entries + the live Cloud Run Jobs/crons themselves
      were removed via direct `gcloud` on 2026-07-12 (prediction), 2026-07-13 (cefi/defi/sports) and 2026-07-16 (tradfi)
      — all PREDATING this item's 2026-07-24 source doc, so the premise was already stale at extraction time.
      Live-reverified 2026-08-09:
      `gcloud scheduler jobs list --location=asia-northeast1 --project=central-element-323112` returns zero
      `-legacy`-named or orphaned manifest-consolidator jobs (only the 12 current per-category jobs, all `ENABLED`); a
      broader scan for any other cefi/defi/tradfi/sports-named scheduler job under a different naming scheme also found
      none. `tofu state list` (terraform/gcp, freshly `tofu init`'d) shows this state file never tracked the
      manifest-consolidator resources at all (12 unrelated resources total, none consolidator-related) — a `tofu plan`
      drift-check is inapplicable to these resources, consistent with the file's own repeated "a real tofu apply is not
      runnable here" precedent for this resource family. Done-when re-scoped to reality: confirmed no legacy blocks in
      source + no legacy live jobs — stronger than the stated "paused/absent" bar (they're fully deleted, not paused).
      Repo: deployment-service — no commit, nothing to change.

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility",
`/codex/04-architecture/instruments-preflight-chain.md`.

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep. 7 items extracted from 2 `mtds_mdps_master`
  source docs (5 from `data_source_provenance_enforcement_2026_07_24.md`, 2 from
  `legacy_bucket_dual_write_decommission_2026_07_24.md`). No conflicts found against active `assigned_vm: planning`
  plans in this parent_epic.
- **2026-08-09 (slot-17)**: Migration data-copy fan-out todo closed as RESOLVED-MOOT, not re-launched — the launcher +
  its target migration script were already deleted 2026-08-03/2026-07-25 as confirmed-dead, and live GCS checks confirm
  all 5 legacy flat tick buckets are already gone. See the todo's own entry for full evidence.
- **2026-08-09 (infra worker, slot 16)**: Worked the "Remove the 8 legacy manifest-consolidator cron Terraform blocks"
  todo — found it already resolved (see the flipped checkbox above for full evidence). The removal (both the HCL
  local-map entries and the live GCP Cloud Scheduler jobs, via direct `gcloud`) happened 2026-07-12/13/16, before the
  2026-07-24 source doc this item was extracted from even existed — the source doc's "pause-crons" item text was already
  describing stale state when written. No code change required; verified live against both the terraform source (git
  log) and actual GCP state (`gcloud scheduler jobs list` + a fresh `tofu init` + `tofu state list`).
