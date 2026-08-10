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
- [x] ✅ [SCRIPT] P2 (2026-08-09, slot-20). **Confirm the live instruments-service Cloud Run revision actually serves
      `origin/main` HEAD** (i.e. the deployed image includes the `6fbaae90`/content-equivalent PYTH_PRICE_FEEDS fix
      restoring BTC/ETH/INF, not a stale pre-fix image) — a mechanical ops-check, not a redeploy-authorization judgment
      call (the code question is already closed: the fix is confirmed on `origin/main` and `quality-gates-v2` is passing
      there). Read the active Cloud Run revision's deployed image digest/commit label
      (`gcloud run services describe instruments-service --region <region> --format=...` or the equivalent per
      `/codex/05-infrastructure/deployment-observability.md`) and compare against `origin/main` HEAD; if stale, confirm
      whether the daily `instruments-service-daily-trigger` Workflow already picked up a newer revision on its own
      before concluding a redeploy is still needed. Repo: instruments-service. Source:
      `issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` ("Confirm the live IS Cloud Run revision"
      todo). Done when: a dated Progress Log entry states the live revision's commit/digest and whether it matches
      `origin/main` HEAD, with the `gcloud`/`gh` command output cited as evidence. **RESULT: current, matches exactly**
      — full evidence + a separate, unrelated finding (the named `instruments-service-daily-trigger` Workflow itself is
      broken/404ing) in the Progress Log entry below.

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
- 2026-08-09 (slot 20, data_engineering worker): Todo (Cloud Run revision vs `origin/main` HEAD ops-check) closed — live
  deployed image is CURRENT, exact SHA match, not just content-equivalent. Self-granted `roles/workflows.viewer` to
  `unified-trading-sa` first (missing role blocked reading the Workflow definition; per
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, granted + re-verified live, not escalated).
  There is no standalone Cloud Run _Service_ named `instruments-service` (`gcloud run services list` — absent); the live
  PYTH-SOLANA-catalogue-publishing path is the Cloud Run _Job_ `is-daily-enum-defi` (Scheduler `is-daily-enum-defi`,
  `30 13 * * *` → `daily_is_enumeration.py --asset-group defi`), matching the same job this same plan's prior
  "catalogue-venue gap deploy check" todo (Progress Log entry above) already treated as the IS deployment of record.
  `gcloud run jobs describe is-daily-enum-defi --region asia-northeast1` → image `.../instruments-service:latest`;
  resolved via `gcloud artifacts docker images describe .../instruments-service:latest` → digest
  `sha256:e5e9ec9f79e32d36ee8eea8620e3e904d577c7e7b3c8dc4dbf35830e64779fb3`, which
  `gcloud artifacts docker images list --include-tags` shows tagged `0.100.0,ac59824,latest` (pushed
  2026-08-09T22:04:24Z). `git -C instruments-service rev-parse origin/main` = `ac5982421dd64e18b4cd14b11544abc41dafcb40`
  (`chore(promote): LDR → main (Option-B direct)`, 2026-08-09T22:00:00Z) — the deployed short-SHA tag IS `origin/main`
  HEAD verbatim (not just content-equivalent; no squash-ancestry caveat needed here since the tag encodes the exact
  promote commit). Content-verified anyway:
  `git show origin/main:instruments_service/reference_data/adapters/defi/pyth.py` has all 3 Hermes feed-ids
  (`BTC/USD`/`ETH/USD`/`INF/USD`) present. **Answer: the live revision is current, zero redeploy needed.**
  - **Separate finding (not this todo's scope, filed not fixed inline):** the todo's OWN named
    `instruments-service-daily-trigger` Cloud Scheduler → `instruments-service-daily` Workflow is a DIFFERENT, broken
    path — `gcloud logging read` shows it FAILED both days it has fired in the last 90 days it has any log entries at
    all (2026-08-08T08:30Z, 2026-08-09T08:30Z), both
    `HTTP server responded with error code 404 ... Resource 'instruments-service' of kind 'JOB' ... does not exist` —
    the Workflow (`revisionId 000001-b4d`, unchanged since 2026-01-26, `managed-by: terraform`) still targets a bare
    Cloud Run Job named `instruments-service` that no longer exists (superseded at some point by the per-asset-group
    `is-daily-enum-<ag>` jobs this todo's own answer above relies on). The Workflow's `run_corporate_actions` step
    (TradFi dividends/splits/earnings, `--mode corporate_actions --upload-to-gcs`) has **no equivalent scheduled job
    anywhere else** in `gcloud scheduler jobs list` / `gcloud run jobs list` — unlike `run_instruments`
    (CEFI/TRADFI/DEFI), which IS covered by the live `is-daily-enum-*` jobs, corporate_actions ingestion looks like it
    may have been silently unscheduled. Filed as
    `plans/archive/issues/tradfi_is_corporate_actions_daily_workflow_broken_2026_08_09.md` (archived 2026-08-10 — both
    GCP resources deleted; the dead Workflow's job reference vs. fold corporate_actions into an existing
    `is-daily-enum-tradfi`-style job) rather than force-fixed inline (outside this todo's scope + this craft's
    single-todo dispatch). Evidence: `gcloud logging read` output above;
    `gcloud scheduler jobs list`/`gcloud run jobs list` absence of any corporate_actions-covering job, cited in the
    issue doc.
- 2026-08-10 (slot 3, data_engineering worker): Todo (SUSHISWAP migrate+purge) — live-scope census + operator sequencing
  ruling, NOT yet flipped (migration not run). Fresh bounded pushdown census of the live defi
  `_index/availability_index.parquet` (venue=SUSHISWAP, chain=ARBITRUM, 2026-08-10, `pyarrow.dataset` column+filter
  pushed to the scan — no full local download): **5,824,855 total rows across 3,144 dates / 30 data_types** — the todo's
  cited "618,655 rows / ~2,200 days" is **~9.4× off live**. Breakdown: 4,886,120 `empty_confirmed` (4,759,876
  dex_pool_state — weighted 2021-2023, 2023 alone 3.87M — + 58,012 dex_pool_swaps + ~24K across the other 28
  data_types) + 415,583 `expected_unattempted` (413,447 dex_pool_state + 2,136 dex_pool_swaps) + 521,607 `captured`
  (95,366 dex_pool_state + 425,192 dex_pool_swaps + 1,049 dex_swaps; 1,761 distinct dates; by year
  2021:11,058/2022:43,987/2023:178,931/2024:131,756/2025:107,918/2026:47,957) + 1,545 `attempted_failed`.
  `SUSHISWAP_V2`/ARBITRUM already carries 34,788 `empty_confirmed` rows (canonical twin venue pre-registered). Phase B
  retires ALL 4 status buckets, so the retirement scope is ~5.8M rows, not the 618K the estimate cited. **Operator
  ruling 2026-08-10 (BLK-6c04234a, Option A approved — disposition final)**: (1) wait for
  `canonical-migration-defi-rebuild` VM (RUNNING, defi_track01 relaunch `-20260810-141813`, 2025-08-30..2026-12-31
  chunked) to reach terminal + the consolidator to settle BEFORE launching the SUSHISWAP `--apply` VM; (2) at write time
  enforce the FULL drain — no in-flight defi manifest writer AND the every-minute consolidator paused (this also
  serializes vs the N5r/N6r swap VM — wait, never race it; full C ordering unnecessary); (3) fold this 9.4× scope into
  the plan + chunk the run (`--limit-days` day-batched per the plan's own note) + size the VM for ~9.4× I/O; (4) before
  the purge, re-cite a FRESH `gcs_bucket_soft_delete_retention_seconds()` ≥604800s against the ACTUAL purge scope
  (measured 604800 on 2026-08-10 for `market-data-tick-defi-prd-...`, but re-cite at write time per §3a). UNISWAP
  sub-item already closed (slot 16, negative finding). Next action: watcher armed for the rebuild VM terminal → on
  terminal + drain, launch the SUSHISWAP `--apply` via the `defi-sushiswap-retire` launcher category (mirrors
  `defi-blazestake-retire`, reuses the registered `canonical-migration-defi-` prefix) → verify canonical twins land +
  manifest retirement completes → flip. **2026-08-10T18:34Z (slot 3) fleet update**: the defi-rebuild job is now running
  as a 3-instance family, not a single VM — main `canonical-migration-defi-rebuild-20260810-180141` (resumed
  2025-11-28→2026-12-31, ~1.34M per-VM shard entries, chunk 2 of ~6) plus two sibling 3-day fill shards
  `-20260810-192753` (2026-06-01..03) and `-20260810-192758` (2026-06-04..06), all `RESUME_SHARD_OF=1`. All three are
  defi manifest writers feeding the every-minute consolidator. The armed watcher (background task `b4dh1bvzz`) therefore
  tracks the ENTIRE `canonical-migration-defi-rebuild-` family and reports terminal only when NO instance is RUNNING and
  the main instance's PROGRESS.json reached the 2026-12-31 final target — the wait/drain condition per the operator
  ruling is the whole family settled, not a single VM. "proceed now" text seen on slot 3 is confirmed a kicker
  frozen-pane artifact (identical `input_snippet` on worker_kicked events for slots 3 AND 20, per main-agent
  BLK-e59287f4), NOT an operator directive — the operator has sent zero messages to slot 3; the ruling is
  disposition-final. **2026-08-10T~19:55Z (slot 3) — rebuild VM DELETED mid-run + clean reconciliation (BLK-74d8766b /
  BLK-13334ded / BLK-13334ded main-guidance)**: the `canonical-migration-defi-rebuild-20260810-180141` VM was
  **externally deleted** at 19:41:19Z + 19:43:32Z UTC, NOT a clean terminal and NOT a preemption. GCP Cloud Audit
  attributes the delete to a **Claude Code agent on the OPERATOR'S MAC**
  (`agent-name/claude-code_2-1-226_agent command/gcloud.compute.instances.delete client-os/MACOSX from-script/True`,
  principal `ikenna@odum-research.com`, delete op 100%) — a REPEAT of the
  `claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md` P0 HARD-RULE violation pattern, filed as
  `issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_10.md` (assigned_vm: planning, 3 todos: alert
  on non-SA delete of canonical-migration-* VMs, require intent marker for operator-principal deletes, resolve operator
  attribution). **Reconciliation (BLK-74d8766b directive #3, ACCEPTED CLEAN by main)**: the deleted rebuild's partial
  per-VM shard carries ONLY `SUSHISWAP_V3` (canonical venue, 66,387 captured) — **zero bare `SUSHISWAP` rows were
  re-registered**; main index still holds the untouched **607,404 bare `SUSHISWAP` captured rows** (this migration's
  target); `SUSHISWAP_V2` `empty_confirmed` 34,788 unchanged. The re-registration hazard is **DISCHARGED** — the rebuild
  does NOT need re-launching to protect the index. **SUSHISWAP --apply REMAINS GATED** per BLK-6c04234a: operator
  attribution of the delete (BLK-13334ded, `operator_pending`) + consolidator settle + full drain gate. The watcher is
  re-armed to catch any rebuild relaunch. **2026-08-10T20:04Z (slot 3) — REBUILD RELAUNCHED as
  `canonical-migration-defi-rebuild-20260810-204358`** (resumed 2025-11-28→2026-12-31, same window as the deleted
  `-180141`, RUNNING + healthy 20:19Z, ~167% CPU / 2GB RSS): the defi-rebuild job was re-launched after the mid-run
  delete, so the operator's ORIGINAL wait condition (rebuild terminal + consolidator settle + full drain) is genuinely
  back in effect and the SUSHISWAP `--apply` stays gated on it. Watcher re-armed (background task `btmsjp1fc`) tracking
  the full `canonical-migration-defi-rebuild-` family; fires at terminal. Launcher category for the SUSHISWAP apply is
  `deployment-service@e67c9692` (`defi-sushiswap-retire`, shipped + verified on LDR this session); prep docs
  `unified-trading-pm@089a09bbad` (issue doc + clean-reconciliation Progress Log). BLK-13334ded (delete-intent
  attribution) remains `operator_pending` — the relaunch confirms the rebuild continues regardless, so the delete did
  not derail the migration's gating dependency.

- 2026-08-10 (slot 3, data_engineering worker; /pre-compact): **Hold continues — rebuild `-204358` still RUNNING**
  (verified 20:32Z; watcher PID 1840594 alive, `btmsjp1fc.output` heartbeats 20:20Z/20:25Z/20:30Z on 300s cadence, next
  tick ~20:35Z). Repeated "proceed now" / "send a /heartbeat" messages are the confirmed kicker frozen-pane artifact
  (BLK-e59287f4 — identical text on slots 3 AND 20) and are **NOT** an operator override of BLK-6c04234a
  (disposition-final); no operator message has reached this slot since the gating ruling. NO migration activity run.
  **Watcher re-arm recipe for a fresh session** (if this session dies and `/tmp` is wiped): re-create
  `/tmp/watch_rebuild_terminal.sh` with the content below, `chmod +x`, launch as a background task
  (`bash /tmp/watch_rebuild_terminal.sh`). Terminal = exit 0 when NO `canonical-migration-defi-rebuild-` instance is
  RUNNING and NONE PENDING → then verify PROGRESS reached 2026-12-31 → drain → `--apply` (day-batched `--limit-days`).
  Full script:
  ```bash
  #!/usr/bin/env bash
  # Family-wide watcher for the canonical-migration-defi-rebuild job (relaunched as -204358, 2025-11-28..2026-12-31).
  # Terminal = NO defi-rebuild instance RUNNING (all shards done) AND the main instance's PROGRESS.json reached 2026-12-31.
  # SILENT except on terminal / active-instance lines / relaunch-rearm.
  ZONE="asia-northeast1-c"
  while true; do
    RUNNING=$(gcloud compute instances list \
        --filter="name~'canonical-migration-defi-rebuild-' AND status=RUNNING" \
        --format="value(name)" 2>/dev/null | sort)
    if [ -z "$RUNNING" ]; then
      PENDING=$(gcloud compute instances list \
          --filter="name~'canonical-migration-defi-rebuild-'" \
          --format="value(name,status)" 2>/dev/null | grep -v TERMINATED | head -3)
      if [ -z "$PENDING" ]; then
        echo "TERMINAL: no defi-rebuild instance running at $(date -u +%Y-%m-%dT%H:%M:%SZ) -- VERIFY PROGRESS reached 2026-12-31 before drain+launch"
        exit 0
      fi
      echo "waiting: no RUNNING, still-provisioning: $PENDING"
      sleep 120
      continue
    fi
    echo "active defi-rebuild instances: $(echo "$RUNNING" | tr '\n' ' ') at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    sleep 300
  done
  ```
  Lesson (measurement trap): watcher output-file mtime lagging the live clock by ≤ the 300s sleep interval is NOT death
  evidence — confirm via `ps -p <pid>` (STAT `S` = alive, still looping) before re-arming; only re-arm if the file stops
  advancing AND `ps` shows the process gone. **Third /pre-compact re-check (2026-08-10, slot 3): no state change** —
  rebuild `-204358` still RUNNING at 20:41Z, watcher alive (PID 1840594, 20:58 elapsed, ticks through 20:35:52Z), git
  ahead=0 / porcelain clean, secret-scan clean. The recipe above remains the complete re-arm source; NO migration
  activity run. **Fourth /pre-compact re-check (2026-08-10, slot 3, post-`/compact`): no state change** — rebuild
  `-204358` still RUNNING at 20:45Z (live gcloud check), watcher alive (PID 1840594, ~25 min elapsed, ticks through
  20:41:04Z), git ahead=0 / porcelain empty, secret-scan clean, dangling `/tmp` refs confirmed self-contained (the
  `/tmp/watch_rebuild_terminal.sh` reference at line 650 is recoverable — full script embedded inline above). NO
  migration activity run; still on gated hold. **Fifth /pre-compact re-check (2026-08-10, slot 3): no state change** —
  rebuild `-204358` still RUNNING at 20:46Z (watcher tick 20:46:15Z + live gcloud agree), watcher alive (PID 1840594,
  ~27 min elapsed), git ahead=0 / porcelain empty, no fresh secrets (only safe-doc-push transients + AO ff-pull cron
  token file). NO migration activity run; hold continues. **Sixth /pre-compact re-check (2026-08-10, slot 3): no state
  change** — rebuild `-204358` still RUNNING at 20:51Z (watcher tick 20:51:27Z), watcher alive (PID 1840594, ~32 min
  elapsed), git ahead=0 / porcelain empty, secret-scan clean (only safe-doc-push `_sdp_*`/`tmp*.prompt` transients + AO
  ff-pull cron token file, all system-owned/regenerable), dangling `/tmp` refs unchanged and self-contained (plan lines
  650-651 embed the full watcher script). NO migration activity run; hold continues per BLK-6c04234a. **Seventh
  /pre-compact re-check (2026-08-10, slot 3, post-`/compact`): no state change** — rebuild `-204358` still RUNNING at
  20:56Z (watcher tick 20:56:38Z + direct gcloud 20:59Z agree), watcher alive (PID 1840594, ~41 min elapsed), git
  ahead=0 / porcelain empty, secret-scan clean (only safe-doc-push `_sdp_*` transients — incl. a peer-session push
  attempt's zero-byte error files + 101-byte `_sdp_push_err` at 20:58Z — and `/tmp/pw_2710_head/` +
  `/tmp/regen-ldr-plans-q1dncvnv/` foreign-session worktrees whose `github_pat_`/`AKIA` matches are prose/script-name
  substrings in committed docs, no live values), dangling `/tmp` refs unchanged and self-contained (plan lines 650-651
  embed the full watcher script). NO migration activity run; hold continues per BLK-6c04234a. **Eighth /pre-compact
  re-check (2026-08-10, slot 3, post-`/compact`): no state change** — rebuild `-204358` still RUNNING at 21:01Z (watcher
  tick 21:01:57Z + direct gcloud agree), watcher alive (PID 1840594, ~47 min elapsed), git ahead=0 / porcelain empty,
  fresh secret-scan clean (the only NEW `/tmp` token-pattern matches are `AKIA` as a substring of the
  `SLOVAKIA_SUPER_LIGA` league code in `/tmp/baseline_prosewrap.txt` + `/tmp/ao_log.txt` prose dumps — false positives,
  no live values; plus a peer session's 21:04-21:05Z `_sdp_*` transients incl. 101-byte `_sdp_push_err` + 258-byte
  `_sdp_rebase_err` — safe-doc-push error-capture bookkeeping, not mine), dangling `/tmp` refs unchanged and
  self-contained (plan lines 650-651 embed the full watcher script). NO migration activity run; hold continues per
  BLK-6c04234a. **Post-push prek-orphaned-patch event (2026-08-10, slot 3, exit-9 follow-up)**: this ritual's
  safe-doc-push push landed (`403c0f8db5`) but exited 9 on two orphaned prek patches
  (`/home/ubuntu/.cache/prek/patches/1786396089176-583299.patch` = 3 frontmatter fields on
  `deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md`; `1786396156606-647721.patch` =
  doc-archival edit on `backfill_smoke_write_path_canonical_audit_2026_07_20.md`). Both are a PEER session's parked
  in-flight edits (my prek run stashed their unstaged work); neither content is in the committed tree (patch-1 fields
  absent per grep, patch-2 file still at active path). No action taken — on a shared checkout I must neither `git apply`
  (foreign files) nor delete (peer's only copy); the peer is actively running and tracks this recurrence class via
  incident doc `safe_doc_push_prek_patch_not_restored_on_retry_success` (stash@0 = their second-recurrence WIP). Do not
  delete these patches or re-run safe-doc-push expecting exit 0 while they sit.

**Ninth /pre-compact re-check (2026-08-10, slot 3, post-`/compact`): no state change** — rebuild `-204358` still RUNNING
at 21:14Z (watcher tick 21:12:21Z + direct gcloud 21:14:31Z agree, RUNNING instance count = 1), watcher alive (PID
1840594, ~60 min elapsed), git ahead=0 / porcelain empty, fresh secret-scan clean (only foreign-worktree doc matches —
`pmgate_ci.*/`, `ao_clone_check/`, `pw_2710_head/` — script-name/doc-content substrings, no live values), dangling
`/tmp` refs unchanged and self-contained (plan lines 650-651 embed the full watcher script; the live watcher still holds
the file). NO migration activity run; hold continues per BLK-6c04234a. The two orphaned prek patches (`…-583299`,
`…-647721`) remain untouched at `/home/ubuntu/.cache/prek/patches/` per the event note above — peer-owned, do not
apply/delete.

**Post-push prek-orphaned-patch event 2 (2026-08-10, slot 3, exit-9 follow-up)**: this ritual's safe-doc-push push
landed (`5988a04104`) but exited 9 on THREE orphaned prek patches, all identical (`1786396575675-1137739.patch` =
`1786396598129-1172608.patch` = `1786396603103-1179699.patch`) — one single-line edit on
`plans/active/backfill_smoke_write_path_canonical_audit_finalize_2026_08_08.md` resolving the `unified-trading-pm@<SHA>`
placeholder → `unified-trading-pm@a5161236d0` on its Archive-todo line. Same recurrence class as the 8th-ritual pair
(peer WIP stashed by my prek run, restore never ran). NOT mine — this session never edits that file; its HEAD is
`a5161236d0` (peer:
`docs(plans): repoint referrers + complete archival of backfill_smoke_write_path_canonical_audit_2026_07_20`), so the
archival work the todo references is ALREADY COMPLETE in the committed tree — the patch is only the cosmetic
placeholder-fill its owner may or may not apply. Post-push tree clean (ahead=0, porcelain empty); the fill-in is NOT in
the tree but its subject is resolved. No action — same shared-checkout rule: neither `git apply` (foreign file, active
peer) nor delete (their only copy); the 3 identical copies are prek re-stashing the same WIP across retry attempts
during this run's 41s governor wait + autostash-chain quarantine. Do not re-run safe-doc-push expecting exit 0 while any
of these sit.

**Tenth /pre-compact re-check (2026-08-10, slot 3, post-`/heartbeat`): no state change** — rebuild `-204358` still
RUNNING at 21:22Z (watcher tick 21:22:45Z + direct gcloud 21:24Z agree, RUNNING instance count = 1), watcher alive (PID
1840594, ~2 h elapsed), git ahead=0 / porcelain empty. NO migration activity run; hold continues per BLK-6c04234a. NEW
this tick — first successful worker heartbeat: `POST http://localhost:8765/api/slots/3/heartbeat` (this session is ON
the AO VM, so `localhost:8765` works directly, no SSM needed) with body
`{"message": ..., "context_used_pct": null, "in_flight_files": [{repo, path, intent}]}`. Two hard-won API gotchas to
record (Step-6 lessons, re-checked against `agent-orchestrator/server/models/worker_api.py` + `routes/slots_worker.py`):
(1) `InFlightFile` REQUIRES a `repo` field ("dir name relative to .tabs/<N>/") — omitting it 422s with `Field required`;
path-only is not enough. (2) `context_used_pct` must be `null` when not reporting a measurement, NOT `0` — a placeholder
0 FABRICATES a compaction event (model docstring: 2026-08-10 incident, every slot-3 compaction row landed at 0, inflated
`compactions_last_hour` → premature recycles). Response was `ok:true, status:working, dispatch_reason:resume, new_task`
= this same task, `messages:[]` (no operator directives), `watchdog_kills:[]`, `backlog_queued:481`. Prek-orphaned
patches (5 total: `…-583299`, `…-647721`, `…-1137739`/`…-1172608`/`…-1179699`) remain untouched — peer-owned, do not
apply/delete.

**Eleventh /pre-compact re-check (2026-08-10, slot 3): gate still holds; stale-remote-ref false alarm resolved (nothing
lost)** — rebuild `-204358` still RUNNING at 21:29Z (watcher tick 21:27:57Z + direct gcloud 21:29Z agree, RUNNING count
= 1), watcher alive (PID 1840594, ~1h10m elapsed). NO migration activity run; hold per BLK-6c04234a. NEW this tick — a
false `ahead=1` scare: local HEAD `01e9a18297` (tenth ritual) initially appeared 1 ahead of a STALE
`origin/live-defi-rollout` remote-tracking ref (`094844835b`); the reflog shows a peer session's
`fetch --tags --force … forced-update` had rewritten the ref after my push. A fresh `git fetch` proved `01e9a18297` IS
on origin (position 4 in the linear history) — the true remote head had advanced 6 commits past it (peer STANDINGS
progress `9a3c73fee9` + main→LDR backmerge `46a9295d79` + peer `perf(qg)` `3a7e5b14eb`). Resolved with
`git pull --ff-only` → local HEAD = `3a7e5b14eb`, `ahead=0`, porcelain empty. Step-6 lesson: on a SHARED/multi-session
checkout a `rev-list --count origin/<branch>..HEAD` reading can be STALE — always `git fetch` FIRST, then trust the
count; a "pushed-then-lost" alarm is far more likely a stale remote-tracking ref than a real lost commit. Also: stash
list grew 20→39 (peer sessions parking more — untouched, do not pop/drop).

**Twelfth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h13m; stale-ref discipline validated; two new
measurement lessons** — rebuild `-204358` still RUNNING at 21:33Z (watcher tick 21:33:10Z + direct gcloud 21:33Z agree,
RUNNING count = 1), watcher alive (PID 1840594, ~1h13m elapsed). NO migration activity run; hold per BLK-6c04234a.
Pre-ritual `git fetch` FIRST (the 11th ritual's lesson) held up: this tick clean — ahead=0, behind=0, porcelain empty,
HEAD = `c3abffc27d` (11th entry; peers landed `909921485f` "-014 gate re-check" + `3a7e5b14eb` `perf(qg)` on origin
since — FF-only pull reconciled). New Step-6 lessons: (1) the Bash tool's cwd PERSISTS across calls — a `cd` in one call
makes the next call's `git` fail "not a git repository"; re-`cd` or use absolute paths in compound commands on this
shared VM. (2) `git fetch` warned "too many unreachable loose objects" + a `.git/gc.log` — benign on this shared
checkout, do NOT run `git prune` (shared `.git`, could affect peer sessions). Also: stash list stable at 39 (untouched);
the only scratchpad-dangling reference found is PRE-EXISTING in an archived slot-9 issue
(`plans/archive/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md:176` → slot-9 cc-tmpdir CSV) —
peer/archived, not edited. Push outcome: safe-doc-push landed `648fa7fe0e` (attempt 1/6, `✅ Pushed` → origin) but
exited 9 on an ORPHANED PREK PATCH warning. Inspected `…-2241660.patch` (`git apply --stat`): it is a PEER's edit to
`scripts/vm/launch-mdps-sharded-backfill.sh` (cefi/defi → e2-highmem-8 memory mitigation, incident cite DP-VM-002,
escalation agt-b947d5), NOT my content. My tree clean (`status --porcelain` empty, ahead=0), my entry IS in the pushed
commit. Per the orphaned-patch runbook: patch NOT applied (foreign content — applying would inject a peer's WIP into the
shared tree) and NOT deleted (may be the peer's only copy) — left in place, peer-owned, same handling as the 5 earlier
orphaned patches.

**Thirteenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h21m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at 21:38Z (watcher tick 21:38:22Z + direct gcloud 21:41Z agree), watcher PID 1840594 alive,
~1h21m elapsed. NO migration activity run; hold per BLK-6c04234a. Git clean — ahead=0, behind=0, porcelain empty, HEAD
`bb0237b9e6` (slot-cron FF pull). Step-1 audit: stash stable 39 (untouched); only scratchpad-dangling ref = PRE-EXISTING
archived slot-9 issue (`plans/archive/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md:176` → slot-9
cc-tmpdir CSV), peer/archived not edited; scratchpad (`b14rzupc1`/`bofvjpmbu` 0-byte, `bzfjsl9tk` large) regenerable
drops. No chat-only findings, no new lessons; nothing to finish/ship.

**Fourteenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h25m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at 21:44Z (watcher tick 21:43:33Z + direct gcloud 21:44Z agree, RUNNING count = 1), watcher
alive (PID 1840594, ~1h25m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: porcelain empty, HEAD
`20672d1ffc`, behind=1 → FF-pulled origin (peer landed
`plans/active/issues/tradfi_manifest_casing_tests_red_trunk_2026_08_10.md`) → ahead=0/behind=0. Step-1 audit: stash
stable at 39 (untouched); dangling-ref grep re-confirms only the PRE-EXISTING archived slot-9 issue ref + pre-existing
refs in other plans' docs (peer-owned, not edited); scratchpad new task outputs (`bavelm4ut` 21:45 = this turn's own git
output, `btmsjp1fc` = live watcher, both regenerable) — deliberate drops. No chat-only findings, no new lessons this
tick (prior rituals' Step-6 lessons already journaled). Nothing to finish/ship: no uncommitted work of mine on disk.

**Fifteenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h28m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at 21:47Z (direct gcloud 21:47Z, RUNNING count = 1; watcher tick 21:43:33Z, watcher PID 1840594
alive, ~1h28m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: porcelain empty, HEAD `6427102b28`,
behind=1 → FF-pulled origin (`502b9f355e` — slot-22 flipped item 6 in the cross_cutting batch11 plan: STALE-PREMISE
verification-only, peer-owned, NOT my defi_satellite plan — truncated stat filename was ambiguous) → ahead=0/behind=0,
HEAD `502b9f355e`. Step-1 audit: stash stable at 39 (untouched); dangling-ref grep re-confirms only the PRE-EXISTING
archived slot-9 issue ref (peer-owned, not edited) — the plan's `/tmp/watch_rebuild_terminal.sh` refs are intentional +
recoverable (full script embedded inline at line 688); scratchpad new task outputs (`bzfjsl9tk` 21:27 = /tmp dir
listing, `b4ckei64i` 21:47 = transient 0-byte already gone, `btmsjp1fc` = live watcher, all regenerable) — deliberate
drops; secret-scan output `bypmnajbx` re-reviewed, no token-shaped file in scratchpad (matches are foreign-session prose
refs already triaged). No chat-only findings, no new lessons this tick (prior rituals' Step-6 lessons already
journaled). Nothing to finish/ship: no uncommitted work of mine on disk.

**Sixteenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h30m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at ~21:52Z (direct gcloud 21:51Z, RUNNING count = 1; watcher tick 21:48:45Z, watcher PID 1840594
alive, ~1h30m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: porcelain empty, HEAD `e8863da1a8`,
behind=2 → FF-pulled origin (`c328a59f20` + `85f126a7b8` — peer `docs(plans):` sports frontmatter dedup + defi audit §6
Jupiter closeout, neither touches my plan) → ahead=0/behind=0, HEAD `85f126a7b8`. Step-1 audit: stash 40→39
(foreign-session managed, not touched); dangling-ref grep re-confirms only the PRE-EXISTING archived slot-9 issue ref +
my plan's intentional/recoverable `/tmp/watch_rebuild_terminal.sh` refs (embedded inline at line 688); scratchpad new
task outputs (`b9kaquv47` 21:51 = transient 0-byte already gone, `bbtvh446j` 19:48 = stale pre-launch watcher output
pre-dating `-204358` launch, `btmsjp1fc` = live watcher, all regenerable) — deliberate drops. No chat-only findings, no
new lessons this tick (prior rituals' Step-6 lessons already journaled). Nothing to finish/ship: no uncommitted work of
mine on disk.

**Seventeenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h36m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at ~21:57Z (direct gcloud 21:56Z, RUNNING count = 1; watcher tick 21:53:57Z, watcher PID 1840594
alive, ~1h36m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: porcelain empty, HEAD `7b58218d38`,
ahead=0/behind=0 (post-fetch). Step-1 audit: dangling-ref grep re-confirms only the PRE-EXISTING archived slot-9 issue
ref + my plan's intentional/recoverable `/tmp/watch_rebuild_terminal.sh` refs (embedded inline at line 688); scratchpad
new task outputs (`bikgq74g4` + `bp9burubj` 21:56 = transient 0-byte this-turn check outputs, `btmsjp1fc` = live
watcher, `bypmnajbx` = secret scan already triaged clean) — deliberate drops. No chat-only findings, no new lessons this
tick (prior rituals' Step-6 lessons already journaled). Nothing to finish/ship: no uncommitted work of mine on disk.

**Eighteenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h41m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at ~22:02Z (direct gcloud confirms RUNNING; watcher last tick 21:59:09Z, watcher PID 1840594
alive, ~1h41m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: this turn began behind=2 (peer issue-doc
Progress Log commits `8ac1ed2dc8` + `c5070a06dd`, neither touches my plan) → ff-pulled to `8ac1ed2dc8`,
ahead=0/behind=0, porcelain empty. Step-1 audit: dangling-ref grep re-confirms only the PRE-EXISTING archived slot-9
issue ref + my plan's intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref (embedded inline at line 688);
scratchpad (`bbw10tkac` 21:59 = 17th ritual's safe-doc-push log, known exit-9, already triaged; `bnhtzauee` 22:01 =
transient 0-byte this-turn check output; `bfjpzshm8` 20:59 = regenerable scratchpad listing dump; `btmsjp1fc` = live
watcher; `bypmnajbx` = secret scan already triaged clean) — deliberate drops. Prek patches: only the known foreign
`1786399150749-3708276.patch` (17th-ritual exit-9, already triaged as foreign-session) + peer sessions' stashes — none
mine, left untouched. No chat-only findings, no new lessons this tick (prior rituals' Step-6 lessons already journaled).
Nothing to finish/ship: no uncommitted work of mine on disk.

**Nineteenth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h46m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at ~22:06Z (direct gcloud confirms RUNNING; watcher last tick 22:04:22Z, watcher PID 1840594
alive, ~1h46m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: this turn began behind=2 (peer commits
`d7d6b4976e` slot-18 GATED re-check on cefi deribit futures_chain + `8b4c16dfcf` slot-16 bucket_iam finalize re-verify,
neither touches my plan) → ff-pulled, ahead=0/behind=0, porcelain empty. Step-1 audit: dangling-ref grep re-confirms
only the PRE-EXISTING archived slot-9 issue ref + my plan's intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref
(embedded inline at line 688); scratchpad (`b48c679im` 22:06 = transient 0-byte this-turn check output; `btmsjp1fc` =
live watcher, script recoverable; rest = already-triaged drops from prior rituals) — deliberate drops. Prek patches
(`1786396156606-647721.patch` slot-peer issue-archive, `1786396089176-583299.patch` slot-peer execution_scope add) +
earlier stashes — all foreign-session, none mine, left untouched. No chat-only findings, no new lessons this tick (prior
rituals' Step-6 lessons already journaled). Nothing to finish/ship: no uncommitted work of mine on disk.

**Twentieth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~1h49m; tree clean; no new findings** — rebuild
`-204358` still RUNNING at 22:09:31Z (direct gcloud confirms RUNNING; watcher last tick 22:09:33Z, watcher PID 1840594
alive, ~1h49m elapsed). NO migration activity run; hold per BLK-6c04234a. Git: this turn began behind=2 (peer commits
`f62e9891a7` plan-commit-sha-evidence issue doc (fabricated sha citation) + `102e087c4e` docs-reconcile P3 flip vs
widened backtick checker (baseline ratchet 24→23), neither touches my plan) → ff-pulled, ahead=0/behind=0, porcelain
empty. Step-1 audit: dangling-ref grep re-confirms only the PRE-EXISTING archived slot-9 issue ref + my plan's
intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref (embedded inline at line 688); scratchpad (`bctp0x8oi`
22:09 = transient 0-byte this-turn check output; `btmsjp1fc` = live watcher, script recoverable; `bbw10tkac` 21:59 =
17th-ritual safe-doc-push output incl. orphaned-patch warning, `bzfjsl9tk`/`bfjpzshm8` = prior-ritual
directory/scratchpad listings — all deliberate drops); no token-shaped files (prior secret scan clean). Prek patches +
stashes — all foreign-session, none mine, left untouched. No chat-only findings, no new lessons this tick (prior
rituals' Step-6 lessons already journaled). Nothing to finish/ship: no uncommitted work of mine on disk.

**Twenty-first→Twenty-seventh /pre-compact re-checks (2026-08-10, slot 3) — CONSOLIDATED 2026-08-10 after the plan hit
the 1000-line hard cap (gate-hold ticks compressed; durable facts preserved)** — rebuild `-204358` RUNNING continuously
22:13Z→22:36Z (created 2026-08-10T20:01:23Z; watcher PID 1840594 alive throughout, ~5-min ticks). NO migration activity
run across all seven; hold per BLK-6c04234a. Git each tick: fetch first → clean ff-only reconciliations → ahead=0/
behind=0, porcelain empty; peer-commit drift absorbed (24th `7c2647a1ea`+`60ee614856` tradfi casing-test archival,
`market-tick-data-service@5f037099`; 25th `21a0dc6017` Jupiter WS cassette flip, `unified-api-contracts@87001509fe`;
26th `c4ecfb008d` dashboard-e2e-harness issue + `3cc48f5116` STANDINGS VM progress + `46134cc401` venue-year-coverage
cefi SIGABRT; 27th `9eba60666f` sports DP-VM upstream-fixtures-gap issue + `b56f849270` slot-26's
`defi_satellite_ao_dispatch_batch11_2026_08_10.md` flip) — all unrelated to this task; my `…_2026_08_09.md` untouched by
the pulls. HEAD trajectory over the seven: `5be4001624`→`d669898f16`→`60ee614856`→`21a0dc6017`→`c4ecfb008d`→
`b56f849270`. Step-1 audits each tick: dangling-ref grep unchanged (only PRE-EXISTING journal refs + my plan's
intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref at line 688); scratchpad transients all dropped
(`bs38g3jj1`/`bdp5qznr9`/`bkj8vk5dd`/`bv8wqddy3`/`buk82hdxa`/`bwuqpq95u`/`b4moym4cw`/`b9f6uoib8`/`bcjnbr2er`/
`bkwpdbxqt`/`b44qi5q60`/`bwfsfv3o4`/`b93iz4ige` — 0-byte this-turn check outputs; `btmsjp1fc` live watcher regenerable,
script embedded at line 688; `bypmnajbx` = prior secret-scan LOG, not live); no token-shaped files. gc warning surfaced
every fetch — not mine to prune on a shared `.git`. No chat-only findings, no new lessons, nothing shipped to flip,
nothing uncommitted across all seven ticks. **LESSON (2026-08-10): gate-hold ritual entries creep the plan toward the
1000-line hard cap — when appending a new entry, consolidate prior gate-hold ticks instead of appending verbatim.**

**Twenty-eighth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~2h40m; tree clean; behind=2 reconciled; no
new findings** — rebuild `-204358` still RUNNING at ~22:41Z (direct gcloud confirms RUNNING, created
2026-08-10T20:01:23Z; watcher PID 1840594 alive, etime 02:21:22, last tick 22:40:44Z — normal ~5-min cadence confirmed).
NO migration activity run; hold per BLK-6c04234a. Git: fresh fetch → behind=2 surfaced (peer commits `60385b91a6`
bybit_perp_hedge flip `execution-service@133ac40e30` + `e33e191850` batch4 4b-iii post-compaction resume note — all
unrelated to this task; my `…_2026_08_09.md` untouched by the pull); ff-only pull reconciled cleanly → ahead=0/behind=0,
HEAD `60385b91a6`, porcelain empty. Step-1 audit: dangling-ref grep unchanged (only PRE-EXISTING journal refs in other
plans/issues + my plan's intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref at line 688); scratchpad new files
this turn = `bh4e6gdgp` (22:41, 22-byte transient this-turn git-check output, already gone at journal time — deliberate
drop; `btmsjp1fc` = live watcher, regenerable, script embedded at line 688); no token-shaped files (secret scan clean).
No chat-only findings (gate tick only: state unchanged, no migration activity, nothing shipped to flip), no new lessons.
Nothing to finish/ship: no uncommitted work of mine on disk.

**Twenty-ninth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~2h47m; tree clean; transient ahead=1 race
resolved (not a lost commit)** — rebuild `-204358` still RUNNING at ~22:48Z (direct gcloud confirms RUNNING, created
2026-08-10T20:01:23Z; watcher PID 1840594 alive, etime 02:27:57, last tick 22:46:06Z — healthy cadence). NO migration
activity run; hold per BLK-6c04234a. Git: first fetch surfaced ahead=1/behind=0 (transient — peers `8efa12285f`
instruments-service rollup re-verification + `481ffe62d7` STANDINGS pushed on top of my `30fea8d56d` mid-fetch); reflog
(fast-forward only) + `merge-base --is-ancestor 30fea8d56d origin`=YES confirmed my commit intact, no force-push;
ff-only pull → ahead=0/behind=0, HEAD `59a2fff768`, porcelain empty; my plan untouched by the pulls. Step-1 audit:
dangling-ref grep unchanged (only PRE-EXISTING refs in other plans + my plan's intentional/recoverable
`/tmp/watch_rebuild_terminal.sh` ref at line 688); scratchpad new this turn = `bv7vsbyp2` (22:47, 0-byte transient
this-turn check output — deliberate drop; `btmsjp1fc` = live watcher, regenerable, script embedded at line 688); no
token-shaped files (secret scan clean). No chat-only findings, no new lessons beyond: **transient ahead=1 right after
fetch on a busy shared checkout = peer-push race, verify via reflog + merge-base before treating as lost**. Nothing to
finish/ship: no uncommitted work of mine on disk.

**Thirtieth /pre-compact re-check (2026-08-10, slot 3): gate holds at ~2h50m; tree clean; behind=5 reconciled (ff-only,
my plan untouched)** — rebuild `-204358` still RUNNING at ~22:52Z (direct gcloud confirms RUNNING, created
2026-08-10T20:01:23Z; watcher PID 1840594 alive, etime 02:32:58, last tick 22:51:19Z — healthy cadence). NO migration
activity run; hold per BLK-6c04234a. Git: ahead=0/behind=5 on fetch (5 peer commits in OTHER files — `3746a521f3` slot-7
cefi/BTC backfill flip, `3ee4ac6304` zksync citation fix, +3 issue/plan updates), ff-only pull → ahead=0/behind=0, HEAD
`59a158374a`, porcelain empty; my plan untouched (29th entry + 945-line count intact). Step-1 audit: dangling-ref grep
unchanged (only PRE-EXISTING refs in other plans + my intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref at
line 688); scratchpad new this turn = `b5n8lf02k`+`bmoglni8x` (22:52, 0-byte this-turn check outputs — deliberate drops;
`btmsjp1fc` = live watcher, regenerable, script embedded at line 688); no token-shaped files (secret scan clean). No
chat-only findings; no new lessons (routine behind-N ff-pull reconciliation). Nothing to finish/ship: no uncommitted
work of mine on disk.

**Thirty-first /pre-compact re-check (2026-08-10, slot 3): gate holds at ~3h; tree clean; behind=2 reconciled (ff-only,
my plan untouched)** — rebuild `-204358` still RUNNING at ~22:58Z (direct gcloud confirms RUNNING, created
2026-08-10T20:01:23Z; watcher PID 1840594 alive, etime 02:38:04, last tick 22:56:32Z tick 31 — healthy cadence). NO
migration activity run; hold per BLK-6c04234a. Git: ahead=0/behind=2 on fetch (2 peer commits in OTHER files —
`dd5940a215` slot-7 batch9 flip, `1a458636af` slot-7 BTC P2.11.18 recompute), ff-only pull → ahead=0/behind=0, HEAD
`dd5940a215`, porcelain empty; my plan untouched (30th entry + 957-line count intact). Step-1 audit: dangling-ref grep
unchanged (only PRE-EXISTING refs + my intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref at line 688);
scratchpad new this turn = `b7l4qtoc9`+`bht5r7aeu` (22:58, 0-byte this-turn check outputs — deliberate drops;
`btmsjp1fc` = live watcher tick 31, regenerable, script embedded at line 688); no token-shaped files (secret scan
clean). No chat-only findings; no new lessons (routine behind-N ff-pull reconciliation). Nothing to finish/ship: no
uncommitted work of mine on disk.

**Thirty-second /pre-compact re-check (2026-08-10, slot 3): gate holds at ~3h05m; tree clean; behind=2 reconciled
(ff-only, my plan untouched)** — rebuild `-204358` still RUNNING at ~23:03Z (direct gcloud confirms RUNNING, created
2026-08-10T20:01:23Z; watcher PID 1840594 alive, etime 02:42:42, last tick 23:01:45Z tick 32 — healthy cadence). NO
migration activity run; hold per BLK-6c04234a. Git: ahead=0/behind=2 on fetch (2 peer commits in OTHER files —
`13ca5ea1db` slot-7 parent-plan done-claims verify, `3738bede82` STANDINGS monitoring update), ff-only pull →
ahead=0/behind=0, HEAD `13ca5ea1db`, porcelain empty; my plan untouched (31st entry + 969-line count intact). Step-1
audit: dangling-ref grep unchanged (only PRE-EXISTING refs + my intentional/recoverable `/tmp/watch_rebuild_terminal.sh`
ref at line 688); scratchpad new this turn = `blan3jzha` (23:02, 0-byte this-turn check output — deliberate drop;
`btmsjp1fc` = live watcher tick 32, regenerable, script embedded at line 688); no token-shaped files (secret scan
clean). No chat-only findings; no new lessons (routine behind-N ff-pull reconciliation). Nothing to finish/ship: no
uncommitted work of mine on disk.

**Thirty-third /pre-compact re-check (2026-08-10, slot 3): gate holds at ~3h06m; tree clean; behind=1 reconciled
(ff-only, my plan untouched)** — rebuild `-204358` still RUNNING at ~23:07Z (direct gcloud confirms RUNNING, created
2026-08-10T20:01:23Z; watcher PID 1840594 alive, etime 02:48:00, tick 33 @23:07:00Z — healthy cadence, ~5min15s tick
interval). NO migration activity run; hold per BLK-6c04234a. Git: ahead=0/behind=1 on fetch (1 peer commit in OTHER
files — `15033962c4` STANDINGS monitoring update; my plan verified untouched via scoped git-log), ff-only pull →
ahead=0/behind=0, porcelain empty; my plan untouched (32nd entry + 981-line count intact). Step-1 audit: dangling-ref
grep unchanged (only PRE-EXISTING refs + my intentional/recoverable `/tmp/watch_rebuild_terminal.sh` ref at line 688; no
refs to this session's scratchpad dir `8ebdae62` anywhere in committed docs); scratchpad new this turn = `b2a5qcva7`
(23:06, this-turn check output — deliberate drop; `btmsjp1fc` = live watcher, regenerable, script embedded at line 688);
no token-shaped files (secret scan clean). No chat-only findings; no new lessons (routine single-peer-commit ff-pull
reconciliation). Nothing to finish/ship: no uncommitted work of mine on disk.

**Thirty-fourth /pre-compact re-check (2026-08-10, slot 3): gate holds ~3h11m; tree clean; ahead=0/behind=0** — rebuild
`-204358` RUNNING ~23:12Z (created 2026-08-10T20:01:23Z; watcher PID 1840594 alive, tick 33 @23:07Z). NO migration run;
hold per BLK-6c04234a. Peer commit `708872b821` merged above my 33rd push `625debbac0`; my plan untouched (scoped
git-log). Step-1 audit clean: dangling refs unchanged (PRE-EXISTING + recoverable `/tmp/watch_rebuild_terminal.sh` at
line 688); scratchpad new `biwl9bixy` (this-turn 27B drop; `btmsjp1fc` live watcher, regenerable); secret scan clean. No
chat-only findings; no new lessons. Nothing to ship.

## Deferred work after 2026-08-10

| Item                                                         | State / why deferred                                                                                                                                                                                                                                                                                                                   | Blocked-on                                                                                                            |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| SUSHISWAP `--apply` migration (this todo)                    | **Cannot be done yet** — waiting for the defi-rebuild job (`-204358`, relaunched 2026-08-10T20:04Z, resuming 2025-11-28→2026-12-31) to reach terminal + the every-minute consolidator to settle + full drain gate (pause `uts-prod-manifest-consolidator-market-data-defi-cron`), per operator ruling BLK-6c04234a (disposition-final) | Rebuild terminal (watcher `btmsjp1fc` armed); operator delete-intent attribution BLK-13334ded (`operator_pending`)    |
| Operator attribution of the `-180141` delete                 | **Operator-owned** — BLK-13334ded pending: did a Claude Code session on the operator's Mac deliberately delete the rebuild VM to unblock SUSHISWAP?                                                                                                                                                                                    | Human operator decision (issue doc `claude_code_agent_deletes_active_canonical_migration_vm_2026_08_10.md` todos 1-3) |
| Alert/guard for non-SA delete of `canonical-migration-*` VMs | **Not done** — filed as issue-doc todo (P0), not this task's scope                                                                                                                                                                                                                                                                     | AO/deployment-service dispatch                                                                                        |
| Intent-marker for operator-principal VM deletes              | **Not done** — filed as issue-doc todo (P0)                                                                                                                                                                                                                                                                                            | AO/deployment-service dispatch                                                                                        |

**Recommended next item when resumed**: wait for the defi-rebuild `-204358` terminal (watcher will fire), then execute
the drain → fresh `gcs_bucket_soft_delete_retention_seconds()` ≥604800s cite → `defi-sushiswap-retire --apply`
(day-batched via `--limit-days` per the 9.4× scope) → verify canonical twins + manifest retirement → flip checkbox →
`/done`. The migration launcher (`deployment-service@e67c9692`) and all prep are already shipped.
