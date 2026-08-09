---
doc_type: plan
title:
  DeFi satellite AO batch 11 — bounded-item extraction from the RECLASSIFY sweep's 14 whole-doc-ineligible defi docs
  (2026-08-09)
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern, produced from a targeted read of 14 defi plan/issue
  docs that a same-day RECLASSIFY sweep found did NOT qualify for a whole-doc `assigned_vm` flip (each still carries
  genuine judgment/design/operator-gated items). Rather than leave those docs entirely NA, this batch pulls out the
  SPECIFIC bounded, worker-determinable items each doc also carries — 12 items across 6 source docs, conflict-checked
  against defi_satellite_ao_dispatch_batch9/batch10 (both active) and defi_consolidated_closeout_2026_07_18.md, zero
  collisions found. The other 8 source docs (defi_cf2_cf3_legacy_canonical_backfill, 3 ag-closeout-audit parked-findings
  report docs with 0 own checkboxes, defi_distinct_values_zero_noncanonical_dispatch,
  defi_pipeline_mode_source_desync_yearn_v3, solana_dex_pool_swaps_indexer_scope, and the remaining open items in
  defi_adapter_dead_code_audit/defi_onchain_dep_check/ defi_pyth_oracle_prices beyond what's extracted here) yielded
  zero further extractable items — either genuinely scoping/judgment work, already-claimed by an active sibling batch,
  or literal 0-checkbox audit-report docs.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-11, orphan-extraction]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
    /plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md,
    /plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 4.5
estimate_calibrated_ai_days: 3.6
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
depends_on: []
source: >-
  Targeted satellite-batch extraction (2026-08-09), scoped to the 18-doc list a same-day RECLASSIFY sweep flagged as NOT
  whole-doc-flip-eligible (14 defi + 2 tradfi + 2 prediction). Mirrors /ag-closeout-audit's satellite-batch pattern:
  read every named doc end-to-end, classify every open item as bounded/worker-determinable vs genuinely gated, extract
  only the former after a conflict-check against every active sibling batch/finalize doc + the tranche's own
  consolidated-closeout. Per-item Source: citations below point at the exact originating doc; source-doc checkboxes
  replaced with citation pointers in the same edit.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 11 — 2026-08-09

Extracted from a targeted end-to-end read of 14 defi plan/issue docs a same-day RECLASSIFY sweep found ineligible for a
whole-doc `assigned_vm` flip. Every todo below cleared the shared conflict-check
([`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
§3) against `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (active),
`defi_satellite_ao_dispatch_batch10_2026_08_06.md` (active, draft-pending-approval), and
`defi_consolidated_closeout_2026_07_18.md` — no other active/draft defi doc claims the same target file/mechanism as any
item here.

## Todos

- [x] ✅ [DATA] P1. **Delete the lending-indices legacy bucket (C0f) + resolve the TF-state drift
      (`market_data_defi_lending_indices_prd` still declared) + the bare `features-onchain` vs asset-group bucket.**
      (2026-08-09, live-verify-and-close, no new infra mutation). **Already resolved historically; verified live, not
      re-executed.** All three sub-items were closed in a prior session
      (`bucket_estate_consolidation_to_sub100_2026_07_13.md` Item C, STATUS: COMPLETE 2026-07-15) that never got its
      resolution reflected back into the closeout doc's checkbox — this RECLASSIFY sweep re-surfaced a stale
      `[OPERATOR]` tag pointing at already-finished work. Fresh live verification 2026-08-09T07:58Z: (1)
      `gcloud storage buckets describe gs://lending-indices-central-element-323112` → 404;
      `gs://     lending-indices-prd-central-element-323112` → 404 (both deleted 2026-07-15 per the archived plan's Item
      C). (2) No `resource "google_storage_bucket"` block for `market_data_defi_lending_indices_prd` anywhere in
      `deployment-service/terraform/gcp/` (only a historical removal-comment at `main.tf:319`, "REMOVED 2026-07-14");
      fetched the live GCS-backed terraform state directly
      (`gs://uts-terraform-state-central-element-323112/terraform/     state/{default,prod}/default.tfstate`, 48 + 313
      resources) — zero `lending` hits in either, confirming no orphaned state entry (no `terraform state rm` needed).
      (3) `gs://features-onchain-central-element-323112` (bare) → 404 (deleted 2026-07-15 per
      `features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15.md`'s Option-A resolution, content relocated
      to `gs://onchain-research-central-element-323112`, confirmed live); its would-be asset-group siblings
      `features-onchain-{cefi,defi}` are ALSO 404 — folded further into the canonical `features-{cefi,defi}-prd` buckets
      (both confirmed live) by the Wave-3 fold, a stronger consolidation than this todo's own text anticipated. No code
      change needed — swept live service repos for hardcoded `"lending-indices-{PROJECT_ID}"` string literals; all 5
      hits are dated one-off historical migration scripts (`market-tick-data-service/scripts/defi_*_2026_06_01.py`,
      `instruments-service/scripts/     {canonicalize_lending_indices_data_type_2026_05_16,reconcile_lending_indices_phantom}.py`,
      `deployment-api/scripts/cleanup_ghost_venue_manifest_rows.py`), none a live/scheduled code path — out of this
      todo's named scope (lending-indices bucket / TF drift / bare features-onchain bucket), not touched. Repos:
      deployment-service, market-tick-data-service. Source: `defi_consolidated_closeout_2026_07_18.md`, Track 2
      ("Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)" item). Done when: the bucket delete is executed (or
      explicitly re-gated) with the cited soft-delete value, and the TF-drift + bare-bucket references are resolved —
      satisfied by live-verified prior completion.
- [x] ✅ [DATA] P2. **Wire a real source for `liquidation_events`** (MVP scope, 2026-08-08 operator ruling per
      `defi_migration_audit_log_2026_07_24.md`) — distinct from the already-migrated `liquidations` data_type
      (protocol-level liquidation event SUMMARIES). **Already resolved historically; verified live 2026-08-09, no new
      code needed.** The source-doc premise (`liquidation_events` = "NO GCS data at all today, handler-if-any produces
      nothing") is stale: `LiquidationEventsHandler`
      (`market_tick_data_service/cli/handlers/liquidation_events_handler.py`) is a complete, non-stub implementation —
      Aave V3 `liquidationCalls` + Morpho `liquidationEvents` via The Graph subgraphs (`_fetch_aave_liquidations`/
      `_fetch_morpho_liquidations`, keyed by `get_subgraph_id`/`get_supported_chains_for_protocol`), full
      `record_captured`/`record_zero_rows`/`record_failed`(`record_shard_failure`)/`record_catalog_unavailable`
      honest-absence wiring via `DefiManifestRecorder`, CLI-registered (`market_tick_data_service/cli/main.py:566`,
      `"collect-liquidation-events": LiquidationEventsHandler`), and Cloud-Scheduler-wired
      (`deployment-service/terraform/gcp/defi_collection_scheduler.tf:186`, cron `35 1 * * *` daily). Live GCS
      verification (`gcloud storage ls -l`) confirms it is genuinely producing real rows, not just scaffolded: 4 real
      `AAVE_V3`/`{ARBITRUM,AVALANCHE,BSC,POLYGON}` parquet shards (~9.8KB each) + 1 real `MORPHO`/`ETHEREUM` shard under
      `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-08-08/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue={AAVE_V3,MORPHO}/chain=.../instrument_type=lending/data_type=liquidation_events/`,
      all object-timestamped `2026-08-09T11:33Z` (today, matching the 01:35 UTC cron processing the prior day) —
      `day=2026-08-05..07` show 0 files, so this is the collector's first observed successful production run, not stale
      leftover data. (`pipeline_mode=batch_onchain_rpc`, not the `PipelineMode.BATCH_ONCHAIN_SUBGRAPH` constant the
      handler passes to the manifest recorder, because `write_defi_rows`'s `_resolve_pipeline_mode` independently
      derives the GCS-path pipeline_mode from `derive_pipeline_mode_for_row(venue, "defi", data_type)` — a UTL registry
      lookup — when no explicit `pipeline_mode=` is passed to `write_defi_rows`; the manifest-record pipeline_mode and
      the GCS-path pipeline_mode are two independently-resolved fields, not required to match.)
      `recorder.record_captured()` is called unconditionally per market once `rows` is non-empty (`_shape_and_record`,
      right after the GCS `upload_bytes` loop) — the observed non-empty, real parquet content for AAVE_V3×4-chains +
      MORPHO-ETHEREUM deterministically implies a matching `record_captured` manifest row landed for the same
      venue/chain/day, satisfying this todo's Done-when bar. No code shipped — verifying the premise and live production
      state, not writing a migration. Repo: market-tick-data-service. Source: `defi_migration_audit_log_2026_07_24.md`
      ("Wire a real source for `liquidation_events`" todo). Done when: a real `liquidation_events` manifest row lands
      for at least one live venue/day — **satisfied by live-verified existing production, 2026-08-09.**
- [x] ✅ [DATA] P2. **Wire a real source for `token_transfers`** (MVP scope, 2026-08-08 operator ruling per
      `defi_migration_audit_log_2026_07_24.md`) — currently a no-data scaffold. Determine the real source (EVM
      `Transfer` event logs via existing Alchemy/RPC access, or a subgraph if one of the already-registered
      `SUBGRAPH_IDS` protocols exposes transfer history) and wire a collector writing real rows via the standard
      honest-absence contract. Repo: market-tick-data-service. Source: `defi_migration_audit_log_2026_07_24.md` ("Wire a
      real source for `token_transfers`" todo). Done when: a real `token_transfers` manifest row lands for at least one
      live venue/day. **2026-08-09**: the handler (`token_transfers_handler.py`) already existed as a complete, non-stub
      Alchemy `getAssetTransfers` implementation but had NO Cloud Scheduler entry — wired it into
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf@a791a273` (`uts-prod-mtds-collect-token-transfers`
      Cloud Run Job + `20 2 * * *` cron, applied live via `tofu apply`, matching the other 14 `collect-*` jobs). Two
      live executions (`-zssjz`, `-x2lg2`) each wrote real, honest `capture_status=empty_confirmed`/
      `SOURCE_RETURNED_ZERO` manifest rows for `ALCHEMY`/`{ETHEREUM,ARBITRUM,BASE,OPTIMISM}`/2026-08-08 — satisfies the
      done-when bar (a real, genuinely-attempted manifest row, not a placeholder). A follow-up correctness gap
      (Cloud-Run-vs-direct-call zero-rows discrepancy on ETHEREUM + wrong per-chain token addresses on the 3 L2s) filed
      as an issue doc, now resolved + archived at
      `/plans/archive/issues/token_transfers_cloud_run_zero_rows_vs_local_2026_08_09.md` — both the Cloud-Run silent-
      swallow bug and the wrong per-chain L2 addresses are fixed + live-verified (all 4 chains now record
      `capture_status=captured` with real row counts).
- [x] ✅ [DATA] P2. **Wire a real source for `governance_events`** (MVP scope, 2026-08-08 operator ruling per
      `defi_migration_audit_log_2026_07_24.md`) — currently a no-data scaffold. Determine the real source (on-chain
      governance-contract event logs — proposal created/voted/executed — for the DeFi protocols this asset_group already
      tracks governance for, e.g. via the existing `_defi_chain_data`/`SOLANA_RPC_TEMPLATES`-style RPC registry, or a
      governance subgraph) and wire a collector writing real rows via the standard honest-absence contract. Repo:
      market-tick-data-service. Source: `defi_migration_audit_log_2026_07_24.md` ("Wire a real source for
      `governance_events`" todo). Done when: a real `governance_events` manifest row lands for at least one live
      venue/day. **2026-08-09** — `governance_events_handler.py` (Compound/Aave/Uniswap proposal+vote events via
      TheGraph subgraph) was already a complete, non-stub, CLI-registered implementation with NO Cloud Scheduler entry
      (same gap class as the sibling `token_transfers` todo above) — wired it into
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf@0f00861f`
      (`uts-prod-mtds-collect-governance-events` Cloud Run Job + `25 2 * * *` cron, applied live via `tofu apply`,
      matching the other 15 `collect-*` jobs). Live execution (`uts-prod-mtds-collect-governance-events-7bhzd`) wrote
      real, honest `capture_status=empty_confirmed`/ `SOURCE_RETURNED_ZERO` manifest rows for
      `AAVE`/`COMPOUND`/`UNISWAP` on ETHEREUM/2026-08-08 (TheGraph API key present, genuinely attempted, zero
      proposals/votes that day) — satisfies the done-when bar (a real, genuinely-attempted manifest row, not a
      placeholder). Repo: deployment-service.
- [x] ✅ [DATA] P2. **Skip `migrate_defi_batch_to_per_instrument.py`'s per-year `discover_bundled()` full GCS listing
      for years that already have a recorded `[[VM_PROGRESS]] last_completed_date=` monotonic checkpoint** (or an
      equivalent already-migrated marker), instead of re-walking the whole `raw_tick_data/by_date/day=*` tree for that
      year on every relaunch. Two consecutive `canonical-migration-defi-per-instrument` VMs OOM'd 2026-08-06 on this
      exact waste — per-year listing time climbed 68s→123s→186s (2022→2024) then crossed the OOM threshold on 2025, even
      though every year fast-skips (corpus already migrated). Repo: market-tick-data-service. Source:
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (DP-VM-003 follow-up todo, R3 section). Done when: a
      relaunch of `canonical-migration-defi-per-instrument` against already-migrated years no longer pays the growing
      full-year listing cost (verified via the run's own per-year timing log), `quality-gates.sh` green. **2026-08-09
      (slot 20, data_engineering) — fixed at the launcher, not the migration tool.** The real gap was one level up: the
      Python tool's `discover_bundled()` is a plain per-invocation GCS walk with no checkpoint awareness of its own, and
      `relaunch_backfill_vm.py`'s `RelaunchPreemptedVm` actuator ALREADY computes a resume value from the
      `[[VM_PROGRESS]]` checkpoint and passes it as `RESUME_START_DATE` (its own comment names
      `launch-canonical-migration-vm.sh` as one of the 5 launchers whose positional start-date arg resolves it) — but
      `defi-per-instrument`'s literal `for y in 2020 2021 ... 2026` bash chunk loop never consulted `$START_DATE` at
      all, so the resume value the actuator had already computed landed at the launcher and was silently discarded,
      every relaunch re-walking every year from genesis regardless. Fix: filter the year list to drop any year whose
      full range (`${y}-12-31`) is already `<= $START_DATE` before baking the remaining years into the VM's command —
      unit-tested in isolation (resume checkpoint `2022-12-31` → correctly keeps only 2023-2026; a normal fresh launch
      with `--start-date 2020-01-01` → unchanged, all 7 years kept; fully-done checkpoint `2026-12-31` → empty list,
      loop no-ops cleanly, rebuild step still runs). `quality-gates.sh` green (full pass, 252s). Repo:
      deployment-service (`scripts/vm/launch-canonical-migration-vm.sh`) — **not** market-tick-data-service as
      originally scoped; the migration tool itself needed no change since it's already correctly idempotent, the fix is
      purely in which years the launcher even bothers invoking it for. Commit:
      `deployment-service@66803f0c5500e59c0a3f2904428b60f1c99bd964` — verified `git merge-base --is-ancestor` an
      ancestor of `origin/live-defi-rollout`.
- [x] ✅ [SCRIPT] P1. **Implement the derivative_ticker/InstrumentType ratification** (per the 2026-08-08 operator
      ruling recorded in `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md` Track 1 line 456-458:
      `derivative_ticker` is the single canonical raw-funding home for all DeFi perps, and
      `lst`/`staking`/`yield_bearing` are ratified canonical `InstrumentType` grains) — drop the Drift-only 24h/7d/30d
      window aggregates in favor of `derivative_ticker` as the sole raw-funding capture path for all DeFi perps; confirm
      `lst`/`staking`/`yield_bearing` carry no remaining case-variant/alias drift anywhere they're consumed. Repos:
      market-tick-data-service, unified-api-contracts. Source: `defi_track01_per_instrument_and_canon_id_2026_07_24.md`,
      Track 1 ("Implement the derivative_ticker/InstrumentType ratification" todo). Done when: the Drift-only window
      aggregates are removed, `derivative_ticker` is the sole raw-funding path for every DeFi perp venue, and a fresh
      grep/manifest check confirms zero remaining case/alias drift on the 3 ratified grains. **Already resolved
      historically across two prior sessions; verified live 2026-08-09, no new code needed.** (1) Drift-only
      `funding_rate_24h/7d/30d` aggregates: `market-tick-data-service@5f659c12` (2026-07-15) already replaced them with
      `funding_rate`+`annualized_rate`; DRIFT-SOLANA was then removed from the platform entirely (2026-07-16 operator
      ruling, SSOT `/codex/04-architecture/solana-defi-coverage.md`) — fresh grep confirms zero
      `funding_rate_24h/7d/30d` hits and zero `drift_adapter`/`DRIFT-SOLANA` refs anywhere in MTDS/instruments-service
      (only a denylist entry in `instruments-service/scripts/build_instrument_catalogue.py:1290-1291` guarding against
      phantom re-entry, which is correct-by-design, not a gap). (2) `derivative_ticker` as sole raw-funding path for
      DeFi perps: **there are currently zero live `asset_group="defi"` perp venues at all** — GMX-ARBITRUM/GMX-AVALANCHE
      removed 2026-07-25, DRIFT/PACIFICA-SOLANA removed 2026-07-16, and
      HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC were reclassified from `defi`→`cefi`
      (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:467-473`, "On-chain CLOBs
      (reclassified from DEFI"); live-verified every remaining perp_funding/derivative_ticker handler in
      `market-tick-data-service/market_tick_data_service/cli/handlers/` (`perp_funding_handler.py`,
      `_perp_funding_hyperliquid.py`, `onchain_perp_batch_handler.py`, `_perp_funding_kalshi_polymarket.py`) writes with
      explicit `asset_group="cefi"` — none writes `asset_group="defi"` — so the "sole raw-funding path for all DeFi
      perps" condition holds vacuously (empty venue set, not a violation). (3) `lst`/`staking`/`yield_bearing`
      case/alias drift: the manifest-side check was already run live 2026-07-24 (sibling todo above, same source plan)
      against a fresh 24,123,783-row read of the prod availability index — unanimous single-casing (lowercase) with 0
      exceptions for all 11 `instrument_type` values including these 3. Fresh 2026-08-09 grep sweep across
      market-tick-data-service/unified-api-contracts/features-service/deployment-api/unified-trading-library for
      case-variant literals found no genuine drift: the `InstrumentType` enum's UPPERCASE members
      (`LST`/`STAKING`/`YIELD_BEARING`, `unified-api-contracts/unified_api_contracts/_instrument_enums.py:59-63`) are
      the consistent code-level SSOT; the manifest-write layer's lowercase `"lst"`/`"staking"`/`"yield_bearing"`
      literals (e.g. `_lst_rates_write.py`, `lst_rates_handler.py`, `eigenlayer_rewards_handler.py`,
      `vault_share_price_handler.py`) are a deliberate, separate persisted-partition-value convention (matches the
      unanimous-lowercase manifest reality); the `INSTRUMENT_TYPE_TO_FOLDER`/`BLOB_PATH_INSTRUMENT_TYPE` dicts in
      `deployment-api/deployment_api/utils/path_combinatorics.py` and
      `features-service/features_service/delta_one/app/core/data_loader.py` map both `"LST"` and `"YIELD_BEARING"` enum
      keys to the shared `"lst"` GCS folder (an intentional many-to-one physical-folder choice, keyed consistently by
      the canonical uppercase enum, not a stray alias). No genuine mismatch (a query filtering one case while data is
      stored in the other) found. No code shipped — verifying the premise, not writing a migration.
- [x] ✅ [SCRIPT] P1. **Wire RPC `factory()` lookup for the 206,107 bare SUSHISWAP/UNISWAP rows** (per the 2026-08-08
      operator ruling, option (b) — `defi_track01_per_instrument_and_canon_id_2026_07_24.md`,
      `unified-trading-pm@a55b820b76`) — build the adapter scaffold now regardless of provider-credential status per the
      External-Data-Always-Available rule: (1) enumerate the unique `pool_address` set from the raw MTDS parquet for
      these rows, (2) RPC `factory()` lookup per pool, (3) resolve each pool to its canonical venue via the
      already-shipped factory-address→version map (`_dex_factory_registry.py`), (4) register
      `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` in UAC `ALL_DEFI_VENUES` (currently only bare `SUSHISWAP-ARBITRUM`
      exists), (5) rewrite/migrate the historical GCS objects + manifest rows to the resolved canonical venue+chain
      path, (6) purge the non-canonical originals once canonical twins are verified present — a fresh
      `gcs_bucket_soft_delete_retention_seconds()` check qualifies this for agent-execution per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (cite the returned value before purging). Repos:
      instruments-service, unified-api-contracts, market-tick-data-service. Source:
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, Track 1 ("Wire RPC `factory()` lookup for the 206,107
      bare SUSHISWAP/UNISWAP rows" todo). Done when: the unique pool_address set is resolved via factory address, the
      missing UAC venues are registered, historical objects/manifest rows are migrated, and the non-canonical originals
      are purged with the cited soft-delete value ≥604800s (or explicitly re-gated if below). **Closed 2026-08-09
      (slot 16) — sub-items (1)-(4) shipped in full; (5)-(6) split out to the new follow-up todo below** (the
      GCS-object/ manifest migrate+purge half is heavier, unstarted, VM-scale I/O — a distinct-enough scope to track as
      its own todo rather than leave this one open indefinitely): see Progress Log for full detail; commits
      `instruments-service@fa54f1d8` (RPC factory()-resolver + resolution script/tests) +
      `unified-api-contracts@ed6b4c78` (venue registration).
- [ ] [SCRIPT] P1. **Migrate + purge the historical SUSHISWAP-ARBITRUM GCS objects/manifest rows to their
      factory()-resolved canonical venue, and enumerate + resolve the UNISWAP-ETHEREUM bare-row cohort** — follow-up to
      the todo above, split out because it's the heavier, unstarted half of the original scope. (1) For the 12,910
      SUSHISWAP-ARBITRUM pool addresses already RPC-resolved (100% `SUSHISWAP_V2-ARBITRUM` per the resolution report at
      `gs://<instruments-defi-bucket>/_cache/reports/dex_pool_factory_resolution_SUSHISWAP_ARBITRUM.parquet` — bucket
      via `get_bucket_name("instruments","defi")`), rewrite/migrate the historical GCS objects + manifest rows from the
      bare `SUSHISWAP-ARBITRUM` path to the canonical `SUSHISWAP_V2-ARBITRUM` path (day-partitioned parquet rewrite —
      this is full-corpus-touching heavy I/O, run on a VM in-region per
      `/codex/05-infrastructure/vm-launcher-runbook.md`, never inline in an interactive session). (2) Once canonical
      twins are verified present, purge the non-canonical originals — cite a fresh
      `gcs_bucket_soft_delete_retention_seconds()` value ≥604800s before purging (or re-gate `[OPERATOR]` if below), per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. (3) The UNISWAP- ETHEREUM bare-row cohort (13,420
      rows per the original 206,107-row estimate's residual) was NOT enumerated or RPC-resolved this session — repeat
      the `resolve_dex_pool_factory_addresses_2026_08_09.py --venue UNISWAP --chain     ETHEREUM --write-report` step
      first, then fold its migrate+purge into this same todo's scope once resolved. Repos: instruments-service,
      unified-api-contracts, market-tick-data-service. Source: this plan's todo above (split 2026-08-09). Done when:
      both cohorts' historical objects/manifest rows are migrated to their resolved canonical venue+chain path and
      non-canonical originals are purged with the cited soft-delete value ≥604800s.

      **2026-08-09 (slot 16) — sub-item (3) CLOSED (no real cohort exists); sub-items (1)-(2) script written +
                                          dry-run-validated, NOT applied. Not flipping — scope incomplete.** (3) Ran
                                          `resolve_dex_pool_factory_addresses_2026_08_09.py --venue UNISWAP --chain ETHEREUM` as instructed: the
                                          instruments-service defi lifecycle catalogue has **zero bare `UNISWAP` rows on any chain** — UNISWAP is already
                                          fully version-split (`UNISWAP_V2`/`UNISWAP_V3`/`UNISWAP_V4`, 24,555 rows total across ETHEREUM/ARBITRUM/BASE/
                                          OPTIMISM/POLYGON). Cross-checked directly against the MTDS raw manifest (`market-data-tick-defi-prd-...`
                                          `availability_index.parquet`, bounded pushdown read): `venue=UNISWAP, chain=ETHEREUM` has exactly 7,625 rows, ALL
                                          `capture_status=empty_confirmed` / `error_reason=EXPECTED_INSTRUMENT_NOT_LISTED`, blank `instrument_id`, dated
                                          `2018-01-01..2018-11-01` (pre-Uniswap-V2-mainnet-launch honest-absence scaffolding, not real captured pool data —
                                          the `13,420` figure this todo's text cites is from the 2026-07-21 source doc and is stale/pre-cleanup; the current
                                          live count is 7,625 and none of it is a genuine factory-resolution gap). **Nothing to migrate for UNISWAP** — this
                                          sub-item is closed on a negative finding, not deferred.
                                          (1)-(2) Wrote + dry-run-validated `market-tick-data-service/scripts/one_offs/relabel_retire_sushiswap_v2_arbitrum_venue_2026_08_09.py`
                                          (`market-tick-data-service@107e1f18c`) — mirrors the proven `relabel_retire_blazestake_venue_2026_08_06.py`
                                          two-phase pattern (Phase A: per-object copy+relabel with `venue`/`instrument_id` content-column rewrite,
                                          registered via `ManifestWriter`; Phase B: row-group-at-a-time retirement of the legacy rows in
                                          `_index/availability_index.parquet`), generalized for this corpus's multiple `instrument_type`/`data_type` combos
                                          (read off each object's own GCS path rather than hardcoded, unlike BLAZESTAKE's single `lst_rates`/`lst`
                                          pairing). Dry-run validated against real prod GCS+manifest data: 195 objects correctly identified + path/filename
                                          transforms verified correct across 3 known-captured legacy days (`dex_pool_state` files with the embedded
                                          `SUSHISWAP-ARBITRUM:POOL:...` filename tag correctly swapped to `SUSHISWAP_V2-ARBITRUM:POOL:...`;
                                          `dex_pool_swaps`' pool-address-keyed files and the `_migrated_sushiswap_*` marker correctly left filename-unchanged,
                                          only the `venue=` path segment moves). One real finding from the dry-run pass: the discovery step's first draft
                                          (mirroring BLAZESTAKE's full-local-download pattern) hit `OSError: No space left on device` — the manifest is
                                          2.87GB and this shared host's `/tmp` tmpfs had only 860MB free; fixed by switching discovery to a bounded
                                          pushdown read (`pyarrow.dataset` + `GcsFileSystem`, column+filter pushed to the scan, no full local download) —
                                          worth flagging for whoever revisits `relabel_retire_blazestake_venue_2026_08_06.py`-style scripts in the future,
                                          the same OOM/disk-space class STEP 0.56 warns about applies to `tempfile.mktemp()`-based manifest downloads too,
                                          not just in-memory loads. **NOT applied to prod this session** — the real target is 618,655 manifest rows
                                          (486,290 `captured` + 112,687 `empty_confirmed` + 18,133 `expected_unattempted` + 1,545 `attempted_failed`)
                                          across ~2,200 distinct captured days; per `/codex/05-infrastructure/vm-launcher-runbook.md` this is VM-scale
                                          heavy I/O, not an interactive-session operation. **Next steps for whoever resumes**: launch the script with
                                          `--apply` on a dedicated VM (day-batched via `--limit-days` if chunking is needed, mirroring the odds_api
                                          backfill's chunk-size lessons in `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`), verify canonical
                                          twins land + the manifest retirement completes cleanly, THEN this checkbox is flippable (UNISWAP sub-item is
                                          already closed, no further action needed there).

- [x] ✅ [SERVICE] P1. **Verify current shipped state, then ship the already-coded+tested BALANCER/ORCA/RAYDIUM
      token-symbol-resolution diff** if it hasn't landed since 2026-08-03 — first check via `git log` whether
      instruments-service's `resolve_evm_token_symbol`/`resolve_solana_token_symbol` wiring into
      `balancer.py::_pool_to_record`, `orca.py::_build_pool_record`, `raydium.py::_build_pool_record` has already
      shipped elsewhere (the ship-blocking cross-repo test-drift issue,
      `issues/instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md`, was confirmed resolved
      2026-08-03 — `instruments-service@fd0d12a9` — with no independent evidence found yet that the 3-adapter diff
      itself was re-attempted). If not yet shipped: re-run the quickmerge for the 3 changed adapters + their 2 test
      files (code is untouched and ready from the 2026-07-21 session — no fresh work needed, just ship it). Repo:
      instruments-service. Source: `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, Track 1 ("eliminate the
      address/UUID fallback in `canonical_instrument_id`" todo, sub-items (2)/(4)). Done when: `quality-gates.sh` is
      green and the diff is confirmed an ancestor of `origin/live-defi-rollout`, cited by commit sha. **Verified
      2026-08-09 — already shipped, no re-execution needed.** `resolve_evm_token_symbol`/`resolve_solana_token_symbol`
      wiring is live in all 3 adapters (`balancer.py::_pool_to_record`, `orca.py::_build_pool_record`,
      `raydium.py::_build_pool_record`), shipped by `instruments-service@aeaa7e50` ("fix(defi): resolve blank/malformed
      pool token symbols via the shared UTL resolver", 2026-07-22 — predates the 2026-08-03 threshold this todo checked
      against). `git merge-base --is-ancestor aeaa7e50 origin/live-defi-rollout` confirms it's on the integration trunk;
      `gh run list --branch live-defi-rollout` shows `quality-gates-v2` currently green (run 31307721283,
      2026-08-09T10:11:18Z). Associated tests present at
      `tests/unit/reference_data/adapters/defi/test_dex_metadata_population.py` and
      `tests/unit/test_defi_adapters_comprehensive.py`. No code change made — nothing to ship.
- [x] ✅ [SCRIPT] P2. **Check whether the catalogue-venue gap fix (`unified-api-contracts@f7314dc2`) has reached the
      deployed instruments-service image**, and if so, run the deploy-gated re-enum+re-rollup.** The fix (26 new DeFi
      venues registered in the UAC validation allowlist, e.g. RENZO-ETHEREUM) is shipped on LDR but the re-enum/
      re-rollup was explicitly noted as
      `DEPLOY-GATED: after ship → LDR→main → IS-image rebuild → then     is-daily-enum-defi re-enum + lifecycle-catalogue-full-defi re-rollup + verify`.
      Check the live IS Cloud Run revision's deployed commit/digest against `origin/main`; if it carries the fix,
      trigger `is-daily-enum-defi` + `lifecycle-catalogue-full-defi` and verify the 26 new venues now enumerate; if the
      image is still stale, record that finding and stop (no redeploy authorization needed for a check-only todo, but do
      not force a manual redeploy here — a stale image is a distinct, separately-trackable finding). Repos:
      instruments-service, unified-trading-pm. Source: `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, R2
      ("Catalogue-venue gap" todo). Done when: a dated note states the live revision's commit/digest, whether it matches
      `origin/main`, and (if matching) the re-enum/re-rollup's resulting venue count. **2026-08-09 (slot 16) — deployed
      image confirmed carrying the fix; re-enum + re-rollup triggered and verified, no code shipped.** `f7314dc2`
      (2026-07-19) is not a direct ancestor of `origin/main` (promotion squashes into `chore(promote)` commits) but its
      exact file content IS on main (`git diff origin/main origin/live-defi-rollout -- instrument_validation.py` empty)
      since the promote commit `2399ffd7` (2026-07-25), well inside the released `v0.73.0`+ range (latest `v0.107.0`,
      satisfying instruments-service's `>=0.106.0,<1.0.0` pin). The two Cloud Run Jobs
      (`is-daily-enum-defi`/`lifecycle-catalogue-full-defi`) both run image tag `:latest`, which resolved to digest
      `sha256:b2a00b3e0a34...` at check time — built from `instruments-service@2972f54d`, itself `origin/main` HEAD
      (`git rev-parse origin/main` == `2972f54d`), confirming the deployed image matches main. Triggered both jobs live:
      `is-daily-enum-defi-6n58b` (20:30:01Z→20:42:00Z, `succeededCount=1`, 0 `unknown venue` rejections for any of the
      26 R2 venues — 1 unrelated `AAVE_V3-PLASMA` unknown-chain warning, out of this todo's scope, not investigated) →
      `lifecycle-catalogue-full-defi-4dgnv` (20:44:43Z→21:18:12Z, `CATALOGUE_ROLLUP_COMPLETED rows=78294 exit_code=0`).
      Post-rollup bounded pushdown read of `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`
      (rewritten `2026-08-09T21:18:06Z`, matching the rollup's completion) confirms all 14 spot-checked R2 venue
      prefixes present in the live `venue` column: BEEFY, CONVEX, IDLE, JITORESTAKING, KARAK, KELPDAO, PENDLE, PUFFER,
      RENZO, ROCKETPOOL, SANCTUM, SOLBLAZE, SYMBIOTIC, YEARN_V3 (61 total distinct venues) — identical to the pre-rollup
      snapshot, indicating these venues were already enumerating successfully via the routine daily/weekly cron cadence
      sometime after the 2026-07-25 promote (this dispatch's live-triggered runs re-confirm rather than newly unblock).
      No code change needed — verification + a fresh dated confirmation run, not a migration.
- [x] ✅ [SERVICE] P2. **Consolidate `native_staking_handler.py` onto `HeliusSolanaAdapter`** per the 2026-08-08
      operator ruling (`issues/defi_adapter_dead_code_audit_2026_07_24.md` §6 item 4) — delete the hand-rolled RPC
      plumbing — not a clean 1:1 swap: (a) add `get_vote_accounts()` to `HeliusSolanaAdapter` mirroring
      `_fetch_vote_accounts`'s shape/limit (currently missing from the adapter); (b) either extend the adapter with the
      Helius→Alchemy→public-RPC fallback tier, or have `NativeStakingHandler` construct `HeliusSolanaAdapter` only when
      a Helius key is present and keep its own lightweight fallback path when absent; (c) swap
      `NativeStakingHandler._collect_staking_rows`'s raw RPC calls for
      `HeliusSolanaAdapter.get_inflation_rate()`/`get_epoch_info()`/`get_vote_accounts()`, keeping the schedule-rate +
      Jito-MEV logic unchanged (those are NOT Helius calls and stay in the handler regardless); (d) delete the now-dead
      hand-rolled RPC plumbing (`_rpc_call`/`_fetch_vote_accounts`/`_fetch_live_rates`'s raw-HTTP body,
      `_get_helius_api_key`/`_get_solana_rpc_url`) from `native_staking_handler.py`. The `helius-api-key` credential is
      already approved + provisioned (2026-05-15, confirmed live in `/codex/05-infrastructure/credentials-matrix.md`) —
      not credential-blocked. Repo: market-tick-data-service. Source:
      `issues/defi_adapter_dead_code_audit_2026_07_24.md` §6 item 4 ("RULED 2026-08-08 (operator): consolidate onto
      `HeliusSolanaAdapter`" todo). Done when: `native_staking_handler.py` imports `HeliusSolanaAdapter` for its live
      RPC path with no duplicate hand-rolled JSON-RPC POST/retry code remaining, and the existing staking-rate unit
      tests (mocked) still pass green. **Shipped market-tick-data-service@082f1141**: added
      `HeliusSolanaAdapter.get_vote_accounts()` + `from_environment()` classmethod (Helius→Alchemy→public-RPC fallback
      resolution, mirrors the deleted handler logic); `NativeStakingHandler` now constructs the adapter via
      `from_environment()` and routes `get_inflation_rate()`/`get_epoch_info()`/`get_vote_accounts()` through it;
      deleted `_rpc_call`, `_fetch_vote_accounts`, `_get_helius_api_key`, `_get_solana_rpc_url`, and
      `_fetch_live_rates`'s raw-HTTP body from the handler; schedule-rate + Jito-MEV logic untouched. `quality-gates.sh`
      green (10454 passed, 28 skipped, 1 xpassed, coverage 81.10%); rewrote affected unit tests to mock
      `HeliusSolanaAdapter.from_environment()` instead of the deleted RPC functions; added new adapter-level coverage
      for `get_vote_accounts()`/`from_environment()`.
- [ ] [SCRIPT] P3. **Reclassify the 1,404 BLAZESTAKE retirement markers out of `attempted_failed`** per the 2026-08-08
      operator ruling, option (c) — this is a `capture_status` flip (`attempted_failed`→`empty_confirmed`), NOT a row
      delete, matching the corpus's existing "capture_status-flip retirement" precedent (fully reversible, no row
      removed). Write a targeted reclassification script (same shape as the already-shipped
      `relabel_retire_blazestake_venue_2026_08_06.py`, which flipped these exact rows `captured`→`attempted_failed` with
      reason `superseded_by_content_verified_canonical_solblaze_solana_relabel_2026_08_06`) that finds every
      `(defi, lst_rates, BLAZESTAKE)` row with `capture_status=attempted_failed` AND an `error_reason` starting
      `superseded_by_` (currently ~1,404 rows — live-reverify the count at execution time, do NOT assume it's still
      exactly 1,404), and rewrites each to `capture_status=empty_confirmed` via the standard manifest recorder's
      honest-absence path. Use a bounded pushdown read (`pyarrow.fs.GcsFileSystem` +
      `dataset.scanner(columns=...,     filter=...)`, NOT a full `to_table()` — the 2.6GB defi `_index` OOMs on a full
      read). Repo: deployment-service (or wherever the manifest-mutation script family for this consolidator lives —
      mirror the existing script's repo). Source:
      `issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md` item 4. Done when: (1) a bounded pushdown
      read confirms 0 remaining `attempted_failed` rows for `(BLAZESTAKE, lst_rates)` with a `superseded_by_*` reason
      after the script runs; (2) DP-FETCH-009's `(defi, lst_rates)` `attempted_failed` count drops by the reclassified
      row count.
- [ ] [SCRIPT] P2. **Confirm the live instruments-service Cloud Run revision actually serves `origin/main` HEAD** (i.e.
      the deployed image includes the `6fbaae90`/content-equivalent PYTH_PRICE_FEEDS fix restoring BTC/ETH/INF, not a
      stale pre-fix image) — a mechanical ops-check, not a redeploy-authorization judgment call (the code question is
      already closed: the fix is confirmed on `origin/main` and `quality-gates-v2` is green there). Read the active
      Cloud Run revision's deployed image digest/commit label
      (`gcloud run services describe instruments-service --region <region> --format=...` or the equivalent per
      `/codex/05-infrastructure/deployment-observability.md`) and compare against `origin/main` HEAD; if stale, confirm
      whether the daily `instruments-service-daily-trigger` Workflow already picked up a newer revision on its own
      before concluding a redeploy is still needed. Repo: instruments-service. Source:
      `issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` ("Confirm the live IS Cloud Run revision"
      todo). Done when: a dated Progress Log entry states the live revision's commit/digest and whether it matches
      `origin/main` HEAD, with the `gcloud`/`gh` command output cited as evidence.

## Not extracted this batch — source docs with zero extractable items

- `plans/active/defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md` — all 6 open todos are the scoping pass itself
  (exact date list, cell shapes, sizing, backfill-vs-relabel classification); none is a bounded fact yet, per the doc's
  own dispatch-scope-eligibility self-assessment.
- `plans/active/issues/ag_closeout_audit_defi_parked_2026_08_06.md`,
  `plans/active/issues/ag_closeout_audit_defi_parked_2026_08_07.md`,
  `plans/active/issues/ag_closeout_audit_defi_parked_2026_08_08.md` — audit-report docs, 0 own `- [ ]` checkboxes
  (findings tables only); the batch11 candidates they themselves name (e.g.
  `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`,
  `defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`, since archived 2026-08-09 — all 12 todos closed,
  `/plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`) live in OTHER docs
  outside this run's 18-doc scope, not extracted here.
- `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` — a dispatch-tracking narrative doc
  (status table + prose), 0 real `- [ ]` checkboxes to extract.
- `plans/active/issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` — sole open item (Todo 5, "append F10 to
  the reconciliation register") is already an open citation-anchor todo inside the ACTIVE
  `defi_satellite_ao_dispatch_batch10_2026_08_06.md` — conflict, not re-drafted.
- `plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` — sole open item is "archive this scoping
  doc", explicitly owned by the sibling `solana_dex_pool_swaps_indexer_2026_08_08_finalize.md`'s own reconciliation
  todo, not independently actionable here.
- `plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md` §6 items 1 and 3 (Jupiter venue registration,
  onchain_event_poller wiring) — both explicitly citation-only, real execution already `assigned_vm: planning` in the
  ACTIVE `defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md`; item 2 (governance-params-poller
  cross-repo re-verify) remains an unruled, cross-repo big finding, genuinely operator-notify not worker-bounded.
- `plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md` item 3 (lending_indices stall
  root-cause diagnosis) — held by the ACTIVE `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s own Deferred section
  (conflict-parked pending a park-text reconciliation neither sibling batch has done yet) — dropped per the conflict-
  check protocol rather than opening a second dispatch path.
- `plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`'s `[DATA] P3` instrument_id
  naming-reconciliation item — genuine design/judgment work the doc's own text flags as previously producing a false "77
  gap days" result; stays behind.

## Progress Log

- 2026-08-09 (slot 16, data_engineering worker): Todo "Wire RPC `factory()` lookup for the 206,107 bare
  SUSHISWAP/UNISWAP rows" — sub-items (1)-(4) shipped, (5)-(6) split to a new follow-up todo (not flipped `[x]`, scope
  incomplete). Built `instruments_service/reference_data/utils/evm_factory_resolver.py` (RPC `eth_call` to `factory()`,
  selector `0xc45a0155`, GCS-cached, same shape as sibling `evm_creation_resolver.py`/`block_resolver.py`)
  - `scripts/resolve_dex_pool_factory_addresses_2026_08_09.py` (enumerates unique `pool_address` from the defi lifecycle
    catalogue — single-walk-compliant, no raw corpus walk — resolves via RPC, writes a resolution report parquet). Ran
    it live against SUSHISWAP-ARBITRUM: 12,910/12,910 pool addresses resolved, 100% match the V2 (classic) factory
    (`0xc35DADB65012eC5796536bD9864eD8773aBc74C4`) — corroborated independently by `capability_declarations/_defi.py`
    documenting the `"sushiswap"` subgraph slug MTDS captures Arbitrum from as legacy-V2-only (Messari
    `liquidityPoolDailySnapshots` schema), so this is a deterministic 1:1 remap, not a mixed cohort. Registered
    `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` in UAC `ALL_DEFI_VENUES` (phase="pipeline", not "live" — neither is
    `_build_defi_venues()`-producible today, matches the METEORA-SOLANA declared-but-not-adapter- backed precedent) +
    `PROTOCOL_LAUNCH_DATES`/pending-investigation entries. Commits: `instruments-service@fa54f1d8` (resolver + script +
    tests, landed `origin/live-defi-rollout`), `unified-api-contracts@ed6b4c78` (venue registration + test, landed
    `origin/live-defi-rollout` — recovered via `git reflog` + `cherry-pick` after the first quickmerge attempt hit the
    known `quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md` bug and dropped the original commit
    `69206506`; re-verified `ed6b4c78` an ancestor of origin independently via `git merge-base --is-ancestor` after the
    retry, not just trusting quickmerge's own success message). UNISWAP-ETHEREUM cohort (~13,420 rows) was NOT
    enumerated or resolved this session. The GCS-object/manifest migrate+purge step (5)-(6) is genuinely heavy
    full-corpus I/O — scoped out as VM-launcher work per the workspace rule, not attempted inline; split into the new
    follow-up todo above.
- 2026-08-09 (slot 2, data_engineering worker): Todo 6 (derivative_ticker/InstrumentType ratification) closed on live
  re-verification, not new execution. Drift-only funding window aggregates were already removed
  (`market-tick-data-service@5f659c12`, 2026-07-15) and the whole DRIFT-SOLANA vertical was removed platform-wide the
  next day (2026-07-16 operator ruling) — fresh grep confirms zero `funding_rate_24h/7d/30d` or `drift_adapter` hits.
  `derivative_ticker` as the sole DeFi-perp raw-funding path holds vacuously: zero venues remain in `asset_group="defi"`
  with any perp capability today (GMX/DRIFT/PACIFICA removed; HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC
  reclassified `defi`→`cefi`) — live-verified every current perp_funding/derivative_ticker handler writes explicit
  `asset_group="cefi"`. `lst`/`staking`/`yield_bearing` case/alias drift: the manifest-side unanimous-casing check
  already ran live 2026-07-24 (0 exceptions across 24.1M rows, same source plan); a fresh 2026-08-09 code-level grep
  sweep across MTDS/UAC/features-service/deployment-api/UTL found the UPPERCASE `InstrumentType` enum members are the
  consistent code SSOT and the lowercase manifest-write literals + folder-mapping dicts are a deliberate, consistent
  convention — no genuine case-mismatch bug found. No code shipped; full evidence in the flipped checkbox above.
- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside its finalize twin. 12
  conflict-clear todos extracted from 6 of the 14 defi source docs this run read end-to-end; the other 8 yielded zero
  extractable items (see "Not extracted" above). Conflict-check run against `batch9`/`batch10` (both active) +
  `defi_consolidated_closeout_2026_07_18.md` — zero collisions found.
- 2026-08-09 (slot 33, data_engineering worker): Todo 1 (lending-indices bucket + TF-drift + bare features-onchain
  bucket) closed on live re-verification, not new execution — all 3 sub-items were already resolved 2026-07-15/19 in
  prior sessions whose completion never propagated back into the closeout doc's checkbox, so this RECLASSIFY-derived
  extraction was re-surfacing already-finished work. `gcloud storage buckets describe` confirms 404 for
  `lending-indices-central-element-323112`, `lending-indices-prd-central-element-323112`, and
  `features-onchain-central-element-323112` (bare); direct read of the live GCS-backed terraform state (`prod` + default
  workspaces, 313 + 48 resources) confirms zero orphaned `lending` state entries and no `.tf` resource block declares
  `market_data_defi_lending_indices_prd`. No code shipped — swept live repos for hardcoded legacy-bucket string literals
  and found only dead one-off historical migration scripts (out of scope, not touched). Full evidence in the flipped
  checkbox above.
- 2026-08-09 (slot 29, data_engineering worker): Todo 7 (BALANCER/ORCA/RAYDIUM token-symbol-resolution diff) closed on
  live verification, not new execution — the `resolve_evm_token_symbol`/`resolve_solana_token_symbol` wiring was already
  shipped by `instruments-service@aeaa7e50` (2026-07-22), well before the 2026-08-03 threshold this todo checked
  against. Confirmed `aeaa7e50` is an ancestor of `origin/live-defi-rollout` HEAD (`git merge-base --is-ancestor`), and
  `quality-gates-v2` is currently green on the branch (run 31307721283, 2026-08-09T10:11:18Z). No code change needed.
  Full evidence in the flipped checkbox above.
- 2026-08-09 (slot 24, data_engineering worker): Todo 2 (`liquidation_events` real source) closed on live verification,
  not new execution — the source doc's "no data at all, handler-if-any produces nothing" premise was stale.
  `LiquidationEventsHandler` is a complete Aave V3 + Morpho subgraph collector with full honest-absence wiring,
  CLI-registered, and Cloud-Scheduler-wired (`35 1 * * *` daily). Live `gcloud storage ls -l` against
  `market-data-tick-defi-prd-central-element-323112` confirms real, non-trivial parquet shards for
  AAVE_V3×{ARBITRUM,AVALANCHE,BSC,POLYGON} + MORPHO×ETHEREUM under `day=2026-08-08`, object-timestamped
  `2026-08-09T11:33Z` (today's cron run) — `day=2026-08-05..07` show 0 files, confirming this is the collector's first
  observed successful production, not stale leftover data. `record_captured` is called unconditionally per market once
  fetched rows are non-empty, so the observed real parquet content deterministically implies a matching manifest row. No
  code shipped. Full evidence in the flipped checkbox above.
- 2026-08-09 (slot 16, data_engineering worker): Todo 6 (SUSHISWAP-ARBITRUM migrate+purge / UNISWAP-ETHEREUM enumeration
  follow-up) — partial progress, not flipped. UNISWAP-ETHEREUM sub-item closed on a negative finding (0 bare rows exist
  anywhere — already fully version-split in the catalogue; the 7,625 raw-manifest rows under the bare venue are pre-2020
  honest-absence scaffolding, not real pool data). Wrote + dry-run-validated the SUSHISWAP-ARBITRUM migrate script
  (`market-tick-data-service@107e1f18c`), confirmed correct against real prod data (195 objects, 3 days). Not applied —
  618,655-row/~2,200-day migration is VM-scale heavy I/O per the workspace runbook, launch is the next dispatch's job.
  Full detail in the todo's own inline addendum above.
- 2026-08-09 (slot 20, data_engineering worker): Todo (`discover_bundled()` full-listing waste on already-migrated
  years) closed — shipped at the launcher, not the migration tool. Traced the actual gap: `relaunch_backfill_vm.py`'s
  `RelaunchPreemptedVm` already resumes this launcher via `RESUME_START_DATE` (its own comment names
  `launch-canonical-migration-vm.sh` explicitly), but `defi-per-instrument`'s literal per-year bash loop never read
  `$START_DATE`, so the checkpoint resume value the actuator computed was silently discarded on every relaunch. Fixed by
  filtering the year list against `$START_DATE` before building the remote command — years fully before the checkpoint
  are dropped from the loop entirely (zero GCS calls), not just fast-skipped inside the tool. Unit-tested the filter
  logic in isolation (3 scenarios: mid-range resume, normal fresh launch, fully-done checkpoint) before shipping.
  `quality-gates.sh` green. Commit: `deployment-service@66803f0c5500e59c0a3f2904428b60f1c99bd964`. Full evidence in the
  flipped checkbox above.
- 2026-08-09 (slot 16, data_engineering worker): Todo (catalogue-venue gap deploy check) closed — deployed IS image
  confirmed matching `origin/main` HEAD (content-equivalent to `unified-api-contracts@f7314dc2`, live since promote
  `2399ffd7` 2026-07-25). Triggered `is-daily-enum-defi` (succeeded, 0 unknown-venue rejections for the 26 R2 venues)
  then `lifecycle-catalogue-full-defi` (succeeded, 78,294 rows) live via `gcloud run jobs execute`; post-rollup
  catalogue read confirms all 14 spot-checked R2 venues enumerate. No code shipped — a live ops-check + confirmation
  run. Full evidence in the flipped checkbox above.
