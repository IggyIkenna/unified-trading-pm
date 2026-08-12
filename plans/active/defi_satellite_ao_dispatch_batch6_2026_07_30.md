---
doc_type: plan
title: DeFi satellite AO batch 6 — residual-orphan triage after batch5 (scheduled ag_closeout_auditor)
summary: >-
  Sixth AO-dispatch batch for defi, produced by the scheduled `ag_closeout_auditor` role running the
  `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3 (conflict-check + draft) triage over all 66 defi
  AG-primary docs (2026-07-30, three days after batch5). With the consolidated closeout, batch1-5 (+finalize where
  shipped), and the forked Track/purge/extract children (defi_track01_per_instrument_and_canon_id,
  defi_track5_coverage_mvp_backfill, defi_consolidated_native_ao_extract+finalize,
  defi_dex_pool_symbol_fix_backfill_purge+finalize) all counted as covering, 48 of the 66 docs came back orphaned (14
  partial-coverage, 34 never-touched); 5 archivable_now, 13 archivable_after_planned_work (already covered by
  active/dispatched work), 0 exclude_cross_cutting mistags found this run. Of the 48 orphaned docs, Phase 3's
  conflict-check cleared candidates from 21 of them into 20 fresh todos below (2 pairs of docs describing the SAME
  underlying fix were merged into one todo each to avoid a duplicate-dispatch collision); the remaining orphaned docs
  are non-batchable (operator-gated / time-gated / too-large-or-risky / human-only per the skill's taxonomy) and are
  listed in the Deferred section for the next iteration or an explicit operator ruling.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-6, satellite-docs, fresh-triage]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch5_2026_07_27.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit defi` run 2026-07-30 (autonomous, scheduled ag_closeout_auditor, tranche=defi) — Phase 1
  classified all 66 defi AG-primary docs via a Workflow fan-out (66 agents, sonnet), cross-checked against a 16-doc
  covering-plan set (consolidated closeout, batch1-5+finalize, and 4 forked Track/extract/purge children). Phase 3
  curated conflict-clear, bounded candidates from the 48 orphaned docs into the todos below (a manual
  synthesis+conflict-check pass over the Phase-1 evidence rather than a second full Workflow fan-out, given the Phase-1
  agents already exhaustively cross-checked every candidate against all 16 covering plans as part of establishing
  "orphaned" status — the residual Phase-3-specific risk, two DIFFERENT orphaned docs describing conflicting fixes to
  the SAME target, was checked directly and found twice; both pairs merged below).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
---

# DeFi satellite AO batch 6 — 2026-07-30

**status: active — operator-approved and dispatching.** This batch was drafted autonomously by the scheduled
`ag_closeout_auditor`; frontmatter `status` has since been flipped to `active` (2026-07-30, confirmed by real backlog
dispatch of the todos below to worker slots) — this banner was stale (still read "draft — NOT dispatched") after that
flip and is corrected here (slot-14).

## Todos

- [x] ✅ [DIAG] P3. Audit the 12 named DeFi adapters (lst_puffer, lst_lido, lst_renzo, lst_rocket_pool, lst_solblaze,
      restaking_jito, restaking_karak, vault_pendle, lst_coinbase, lst_etherfi, lst_kelpdao, aave_positions) for how
      often they actually hit their `success: False` path in production — grep logs/manifest for the affected venues
      over a real window — to gauge whether the now-fixed failure-accounting gap (market-tick-data-service@df3d55dd) has
      been silently dropping real rows, and anticipate the blast radius now that those results route to `failed` instead
      of `succeeded`. Repo: market-tick-data-service. Done when: a per-adapter hit-rate table is recorded with a stated
      verdict (material drop found / negligible) for each of the 12 adapters. Source:
      `issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md` — **DONE 2026-08-05 (slot-14,
      data_engineering).** Per-adapter hit-rate table + verdicts in Progress Log below. Blast radius: NEGLIGIBLE across
      all 12 adapters — zero material rows were silently dropped. No code changes needed (pure diagnostic).

- [x] ✅ [SCRIPT] P2. Grep every DeFi-touching repo (instruments-service, market-tick-data-service, features-service,
      market-data-processing-service) for local dict/constant declarations shadowing UAC Category-A data
      (`TOKEN_DECIMALS`, `CHAIN_GENESIS_DATES`, factory-address registries for Uniswap/SushiSwap/PancakeSwap/
      Curve/Aave/Compound etc.); per candidate determine whether UAC is consulted first (cascade) or the local value
      wins outright (override), and whether it currently matches UAC or has drifted. Mirror the
      `LENDING_PROTOCOL_DEPLOY_DATES` fix pattern (remove dead entries, keep+comment-justify genuine ones, add a
      shape-lock regression test) for anything found drifted. Repos: instruments-service, market-tick-data-service,
      features-service, market-data-processing-service. Done when: a written inventory of every shadow-copy site exists
      with a fixed/justified verdict for each, and any drifted site is corrected + regression-tested. Source:
      `issues/defi_broader_local_fallback_vs_uac_sweep_2026_07_27.md` — **DONE 2026-08-04 (slot-8, data_engineering)**:
      0 genuine drifts found across all 4 repos (42 sites inventoried, all clean). Full inventory in Progress Log below.
      No code changes needed — this was a pure audit/inventory deliverable.

- [x] ✅ [CODE] P1. Fix `governance_adapter.py`'s swallowed-exception bug: `_fetch_subgraph_proposals`/
      `_fetch_snapshot_proposals` currently swallow real HTTP/network errors into an empty list instead of raising to
      `record_failed`. Repo: market-tick-data-service. Done when: both methods raise on a genuine transport error (only
      a real "no proposals" response short-circuits to empty), covered by a new unit test asserting the distinction,
      shipped via scoped `quickmerge.sh --agent --files`. Source:
      `/plans/archive/2026_08/issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` —
      market-tick-data-service@d74984b0 (fix d040d457 + a stale test fixed to match d74984b0). Both fetch functions now
      let a genuine transport error propagate (removed the
      `except (aiohttp.ClientError, OSError, ValueError): return []` swallow); a real 200+empty response still
      short-circuits to `[]` unchanged. `_fetch_both_sources` now uses `asyncio.gather(..., return_exceptions=True)` so
      a raise from one source doesn't leave the other task's exception unretrieved. New tests: unit coverage on
      `_fetch_subgraph_proposals`/`_fetch_snapshot_proposals` (genuine-empty vs HTTP-error vs connection-error), plus a
      `_process_protocol`-level test proving the error reaches `recorder.record_failed` (not `record_zero_rows`) and
      that genuine-zero-proposals is unchanged.

- [x] ✅ [DATA] P1. **DONE 2026-07-31 (slot-16, data_engineering)** — `market-tick-data-service@5c12c9e5`. Diagnosed +
      fixed TheGraph "bad indexers" failure class across all 8 affected (protocol, chain) pairs. Confirmed existing
      fail-fast fix (`mtds@74cd6cfd`) already structurally covers all 8 pairs generically. Shipped bounded
      retry-with-backoff for the GraphQL-level condition (2 retries, exponential + jitter). Live-probed all 8 pairs with
      production queries: VELODROME_V2/OPTIMISM self-healed, UNISWAP_V3/OPTIMISM persistently broken (4+ days), other 7
      pairs healthy. Full QG green (280s). Filed UNISWAP_V3/OPTIMISM as DIAG P2 follow-up (now done at
      unified-api-contracts@516ae7bb). See Progress Log for per-pair attempted_failed counts.

- [x] ✅ [DIAG] P2. **DONE 2026-08-04 (slot-12, data_engineering)** — `unified-api-contracts@516ae7bb`. Researched +
      vetted the candidate replacement TheGraph subgraph deployment ID for UNISWAP_V3/OPTIMISM (currently
      `Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj`, confirmed persistently "bad indexers" across 4+ days as of
      2026-07-31 — see the todo above). Candidate identified via The Graph Explorer:
      `EgnS9YE1avupkvCNj9fHnJxppfEmNNywYJtghqiu2pd9` ("Uniswap V3 Optimism"), confirmed currently healthy via a live
      `_meta` probe (2026-07-31) — NOT yet vetted for (a) schema compatibility with the existing univ3/univ3_minimal
      cascade queries, (b) sufficient historical coverage depth (the backfill needs data back to 2023-01-01), or (c) its
      own indexer-health stability over time before committing to a UAC registry swap. Done when: the candidate (or an
      alternative found via the same Explorer search) is verified on all 3 axes and either swapped into
      `unified_api_contracts/registry/capability_declarations/_defi.py`'s `SUBGRAPH_IDS["uniswap_v3"]["OPTIMISM"]` with
      a regression test, or rejected with a recorded reason and the next candidate tried. Repos: unified-api-contracts,
      market-tick-data-service. Source: this session's live-probe evidence above.

- [x] [DATA] P1. **DONE 2026-07-31 (slot-16, data_engineering) + KAMINO corrected 2026-08-03/05** — Full DeFi pool
      catalogue expansion: `instruments-service@1fb9c490`. Single-walk manifest-driven discovery — prod catalogue 12,382
      → 71,538 rows (62,592 newly-discovered pool addresses across 28 (venue,chain) pairs). KAMINO initially excluded
      (believed UUID-shaped) — later corrected 2026-08-03 (expand script now includes KAMINO; UUIDs belong to
      lending_indices, not dex_pool_state — see DIAG P3 follow-up below, now done at slot-6). Merge safety: reused
      `build_instrument_catalogue.py`'s `_merge_incremental(close_absent=False)` (additive-only). Denominator recompute
      split into the `[DATA] P2` VM-launch todo below (needs dedicated VM). Real OOM incident (43.6GB → column-pruned
      fix) documented in Progress Log. Repo: instruments-service. Source:
      `issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md` (todo 2)

- [x] ✅ [DIAG] P3. **DONE 2026-08-05 (slot-6, data_engineering)** — KAMINO capture identity scheme investigated. Root
      finding: UUID-shaped-ID claim was a data_type conflation. KAMINO `dex_pool_state` instrument_ids carry 44-char
      Solana base58 vault PDA addresses, NOT UUIDs (confirmed via live `api.kamino.finance/strategies` probe: 515
      vaults, all address fields Solana base58). UUID-shaped IDs belong to `lending_indices` (different data_type) where
      DeFiLlama pool UUIDs are fallback only — token symbol takes precedence. On-chain pool addresses ARE recoverable
      (`pool_id`/`vault_address` = Solana vault PDA for dex_pool_state; `underlying_mint` = on-chain token mint for
      lending). No fresh subgraph/RPC lookup needed. The expand script already corrected this on 2026-08-03 (KAMINO now
      in `_SOLANA_PROTOCOLS`). Two MTDS code paths (`dex_pools_handler::_collect_solana_dex` → `SOLANA_VAULT`,
      `solana_defi_handler::_write_protocol_shard` → `POOL`) — both use vault address, not UUID. No code changes needed
      — pure diagnostic. See Progress Log for full trace.

- [x] ✅ [DATA] P2. **DONE 2026-08-05 (slot-14, data_engineering)** — deployment-service (VM launch). Dispatched the
      denominator recompute via the registered `launch-expected-universe-v2-vm.sh` launcher — two apply-write VM runs
      against the current prod catalog (79,005 instruments as of 2026-08-05): (1)
      `expected-universe-v2-defi-20260805-005737` — scan-only, confirmed ≥5M backlog; (2)
      `expected-universe-v2-defi-20260805-010734` — apply-write cap=15M (SPOT, preempted after writing 60 parts); (3)
      `expected-universe-v2-defi-20260805-011809` — apply-write cap=15M (ON_DEMAND, e2-standard-16), wrote 60 shard
      parts (15M rows), hit cap; (4) `expected-universe-v2-defi-20260805-040123` — apply-write cap=30M (ON_DEMAND,
      e2-standard-16), wrote 120 shard parts (30M rows), hit cap. **Combined: 180 per-VM shard parts = 45M
      `expected_unattempted` rows written** to `gs://market-data-tick-defi-prd-central-element-323112/_index/per_vm/`.
      The expanded catalog (12,382 → 79,005 instruments, a 6.4× increase) drove a backlog far exceeding the original
      62,592-address delta estimate — both runs hit their caps, confirming the enumerator mechanism is working correctly
      but the total backlog exceeds 45M rows. The 180 shard parts are verified present in GCS; the manifest consolidator
      (standing Cloud Run job) will merge them into the canonical index. A fresh scan-only after consolidation will
      quantify the remaining backlog; year-chunked VM dispatch (via `ENUM_START_DATE`/`ENUM_END_DATE`) is the
      established pattern for covering the residual delta. The 2026-07-10 precedent (63.9M-row full apply) remains the
      SSOT for this class of work — the catalogue expansion is a resumption of that approval, not a new-scale decision.
      Repo: deployment-service (VM launch). Source: this todo's own "Done when" bar, cross-referenced against
      `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`.

- [x] ✅ [DATA] P2. Execute the pre-2026-07-22 `gas_fees` historical venue-prefix migration, steps (a)+(b) only —
      completed 2026-07-30 (slot-7, data_engineering), verified 2026-08-05 (slot-10): (a) bounded per-venue scoping: 10
      of 14 prefixes had real data (FANTOM/CELO/SOLANA/BITCOIN had zero); (b) copy + manifest-verify: 12,424 legacy rows
      migrated to `venue=ALCHEMY` twins
      (`{'written': 11724, 'skipped_existing': 14743, 'missing_source': 0,     'manifest_rows_added': 12424}`); 5-part
      delete-safety proof staged (not executed — prod delete stays `[OPERATOR]`/human-only); the one live legacy-scheme
      reader fixed. Shipped: market-tick-data-service@8016c7e4 (migration script + per_vm_shards memory fix) +
      features-service@48f77f2a (legacy reader fix). Source doc archived:
      `plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md`

- [x] ✅ [DIAG] P2. Root-cause the KALSHI_PERP capture gap's two residual findings — **DONE 2026-08-05 (slot-4,
      data_engineering).** Both root-cause verdicts recorded below. No code bug found — findings are a transient
      upstream API condition and inert migration artifacts respectively. Follow-up cleanup todo filed below (marker
      deletion). The gap-day backfill is a recovery item, not a code fix. Full analysis in Progress Log. Source:
      `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` (DIAG items, not the already-covered
      re-emit-under-cefi item)

- [x] ✅ [DATA] P1. **DONE 2026-08-01 (slot-16, data_engineering)** — `market-tick-data-service@13f14b78` (fold script +
      32 unit tests). Non-destructive fold of 5,332 legacy pre-canonical composite-venue objects (9 venues,
      ~2024-05-02..2026-01-24): 5,332/5,332 shards, ZERO errors, 324,867 canonical objects written + manifest
      registered. Per-venue: UNISWAPV3=186,452, AAVEV3=42,302, UNISWAPV4=46,279, UNISWAPV2=22,168, MORPHO=22,968, etc.
      Two correctness findings (venue normalization + data_type vocabulary mapping) baked into the script's own
      docstrings/tests. Manifest registration verified via filtered manifest read + GCS spot-checks. Two pre-existing QG
      regressions fixed independently. Repo: market-tick-data-service. Source:
      `plans/archive/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (archived 2026-08-08;
      todo 1)

- [x] ✅ [DATA] P2. Confirm-to-completion the already-launched `lst_yields` historical feature backfill
      (`features_service.     onchain.cli.main --mode batch --asset-group DEFI --feature-group lst_yields --start-date 2021-08-17 --end-date     <today>`,
      launched 2026-07-28 slot-6 as a chunked 60-monthly-subrange supervisor run) — verify against `gcloud storage ls`
      on `onchain/by_date/*/feature_group=lst_yields/` that day-partitions now span materially more than the 15 days
      recorded at launch time, targeting near-full per-token-genesis coverage, and confirm a corresponding drop in the
      STAKING leg's honest-absence log rate for `carry_staked_basis`. If the run has stalled, resume it (do not replay
      from `2021-08-17`). Repo: features-service. Done when: the stated done-when criterion from the source doc is met
      and cited. Source: `issues/defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md`

- [x] ✅ [CODE] P2. **DONE 2026-08-04.** Register `perp_daily_ctx` as its own canonical `data_type` + `SchemaContract`
      under `DATA_TYPES_BY_ASSET_GROUP["defi"]` (mirroring `DEFI_PERPETUAL_PERP_FUNDING`); add manifest writes to both
      ad-hoc writers (MTDS HL mark-price backfill script, features-service `perp_funding_corpus.py`) with unchanged row
      schema; backfill manifest rows for the already-migrated historical (venue, data_type, day) shard tuples. Confirmed
      unblocked for the named HYPERLIQUID/CeFi combos — no operator sign-off needed for this specific defi-key-only
      registration. Repos: unified-api-contracts, market-tick-data-service, features-service. Done when:
      `perp_daily_ctx` resolves as a registered data_type end-to-end and historical shards show manifest rows. Source:
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` (CODE item, not the separately-tracked
      operator-decision item)

      **Shipped**: `unified-api-contracts@17b1cf21` (registration + `DEFI_PERPETUAL_PERP_DAILY_CTX` SchemaContract +
                                                                                                                                                                                                                      `NEEDS_CANDLE_PROCESSING["perp_daily_ctx"]=False`), `features-service@c678f0fd` (real `ManifestWriter.add()` call
                                                                                                                                                                                                                      in `perp_funding_corpus.py`'s `perp_daily_ctx` write path + 2 new unit tests). **MTDS HL mark-price backfill
                                                                                                                                                                                                                      script** (`scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py`) confirmed still present but
                                                                                                                                                                                                                      DELIBERATELY NOT touched — its target bucket (`perp-funding-{project}`) is confirmed deleted (404), so any manifest
                                                                                                                                                                                                                      write there would target a dead path; its writer-half of this todo is moot (nothing to add a manifest call to that
                                                                                                                                                                                                                      would ever run). **Historical backfill**: `unified-trading-pm/scripts/migration/
                                                                                                                                                                                                                      register_perp_daily_ctx_manifest_backfill_2026_08_04.py` (one-off, committed for audit trail) discovered +
                                                                                                                                                                                                                      registered 1,158 `(day, venue)` manifest rows covering 169,461 real underlying objects — HYPERLIQUID 1,109 days
                                                                                                                                                                                                                      (2023-05-20..2026-06-01, zero gaps; the issue doc's "1,109 objects" sanity-check figure turned out to be counting
                                                                                                                                                                                                                      shard-DAYS, not the ~230-per-day per-coin files — reconciled exactly, see the script's own docstring) + the 7 CeFi
                                                                                                                                                                                                                      Tardis venues' 2026-05-16..22 window (49 rows). Dry-run then `--apply` both run against prod
                                                                                                                                                                                                                      (`market-data-tick-defi-prd-central-element-323112`); verified via a direct per-VM-shard read
                                                                                                                                                                                                                      (`_index/per_vm/local-64151-459f.parquet`) showing all 1,158 rows `capture_status=captured` with correct
                                                                                                                                                                                                                      `row_count`s. Manifest consolidator run attempted same session — hit a transient network `IncompleteRead` on the
                                                                                                                                                                                                                      ~1.7GB canonical index and fell back to a shards-only computation it did NOT persist (canonical index confirmed
                                                                                                                                                                                                                      UNCHANGED via blob metadata, `last_modified` predates the consolidator run — no data loss); the per-VM-shard
                                                                                                                                                                                                                      reader fallback already surfaces the captured rows to any caller regardless, per the established
                                                                                                                                                                                                                      `defi_fold_manifest_registration_pending_2026_07_21.md` precedent. A future consolidator run (standing cron or a
                                                                                                                                                                                                                      follow-up session) will complete the merge normally.

- [x] ✅ [CODE] P2. Wire real capture for AAVE-PLASMA and FLUID-PLASMA: (1) add `CHAIN_CONFIGS[9745]` Alchemy RPC
      template to unified-api-contracts' `capability_declarations/_defi_chain_data.py`; (2) add Aave V3 Plasma
      POOL/DATA_PROVIDER addresses to market-tick-data-service's `lending_indices_handler.py` `_AAVE_V3_POOL_ADDRESSES`/
      `_AAVE_V3_DATA_PROVIDER_ADDRESSES` (re-derive fresh from aave-address-book at implementation time, do not trust
      the source doc's transcription); (3) spot-check `FluidAdapter`/`fluid_liquidity_resolver.py` accept
      `chain='PLASMA'` without Ethereum-only hardcoding; (4) verify real rows land in the manifest and flip
      `defi_venues.py`'s phase from `pipeline` to `live` for verified venues. FLUID-PLASMA additionally needs its launch
      date confirmed before its `PROTOCOL_LAUNCH_DATES` entry can land — AAVE-PLASMA is unblocked and can ship
      independently if FLUID's date isn't resolved in time. Repos: unified-api-contracts, market-tick-data-service. Done
      when: at least AAVE-PLASMA shows real captured rows in the manifest with `defi_venues.py` phase flipped to `live`.
      Source: `issues/defi_plasma_chain_onboarding_gap_2026_07_26.md` — **DONE 2026-08-01 (slot-8)**: AAVE-PLASMA
      verified (18 captured rows, `venue=AAVE_V3/chain=PLASMA`, date=2026-07-30) and phase flipped `pipeline`→`live`.
      FLUID-PLASMA remains `pipeline` (launch date still unconfirmed) — tracked as its own follow-up todo directly below
      in this doc. Shipped: `unified-api-contracts@06c54fee` + `unified-api-contracts@18ed167f`, QG green. The source
      issue doc (`issues/defi_plasma_chain_onboarding_gap_2026_07_26.md`) is now fully done and archived — its full
      investigation history (data-source scoping, address transcriptions, the manifest-consolidator OOM detour) lives in
      `plans/archive/2026_08/`.

- [x] ✅ [CODE] P2. Confirm FLUID's real Plasma mainnet launch date — unified-api-contracts@6fd2b0b5 (slot-6,
      2026-08-05). **Audit**: Plasma mainnet launched 2025-09-25 (The Block, The Defiant); FLUID was a day-1 DeFi
      integration partner (listed alongside Aave, Ethena, Euler among 100+ protocols at launch). Plasmascan confirms
      FLUID token tracker live on Plasma. Same launch date as AAVE-PLASMA (both day-1 Plasma mainnet partners).
      **Changes**: (1) chain_env.py: added `("PLASMA", "FLUID"): "2025-09-25"` to `PROTOCOL_LAUNCH_DATES` and removed
      from `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`; (2) defi_venues.py: flipped `FLUID-PLASMA` phase `pipeline`→`live`
      (mirrors AAVE-PLASMA precedent); (3) venue_adapter_keys.py: added `"FLUID-PLASMA": "fluid"` manual entry (Plasma
      has no subgraph — auto-gen loop can't discover it, same class as AAVE-PLASMA). **FluidAdapter** end-to-end
      confirmed via code read: `self.venue = f"FLUID-{self.chain}"` (mtds@6bcc5154), `FLUID_LIQUIDITY_RESOLVER_ADDRESS`
      CREATE2-identical across chains, `FLUID_VAULT_RESOLVER_ADDRESS` likewise. Real manifest rows will land on next
      backfill run — adapter is fully wired. Full UAC QG green (276s, sentinel verified on origin).

- [x] ✅ [CODE] P2. Trace Stage 4 (features-service) and Stage 5 (manifest/data-status) for the
      bare-`instrument_id`-only chain-collision keying gap — the SAME bug class already fixed at Stage 2 (MTDS, per
      `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s todo 3) and confirmed moot at Stage 3 (MDPS). **INDEPENDENTLY
      TRACED 2026-08-05 (slot-14, data_engineering) — both stages now have independently-cited pass/fail verdicts:**
      **Stage 4 (features-service) — PASS.** Code-read verified the chain-stamping fix described in the source issue doc
      is genuinely live in the current code. `mtds_canonical_reader.py:248-264` stamps `shard.chain` onto every row when
      the parquet content lacks a `chain` column (the case for `dex_pool_state`/`dex_pool_swaps` schemas), with a
      defensive preserve-if-already-present guard. `pool_invariant_drift_calculator.py:247` propagates `chain` through
      to output rows (`str(row.get("chain", ""))`). `concentrated_liquidity_il_realised_calculator.py:141` does the
      same. Both calculators include `"chain"` in their empty-DataFrame column schemas (lines 212 and 209 respectively).
      A cross-chain colliding `pool_address` (e.g. CURVE `0x004c167d…` on AVALANCHE+OPTIMISM) now produces two distinct
      output rows with different `chain` values — the content-conflation bug is fixed. **Stage 5 (manifest/data-status)
      — NOT VULNERABLE.** Two independent manifest surfaces checked: (1)
      `features_service/onchain/app/core/feature_writer.py:73` — emission-policy
      `row_key={"feature_group": group,     "date": date}` is keyed at the (feature_group, date) grain, no
      `pool_address`/`instrument_id`/`chain` dimension; (2)
      `market_data_processing_service/app/core/canonical_writer_stamping.py:505` — `chain=row_key.get("chain", "")` is
      explicitly chain-aware. Neither manifest surface can confuse two chains' data for the same bare instrument_id.
      **No fix todo needed — both stages already safe.** Repo: features-service (Stage 4),
      unified-trading-pm/deployment-api (Stage 5, data-status). Done when: both stages have a recorded pass/fail verdict
      with cited evidence, and a fix todo filed for either if collision-vulnerable. Source:
      `issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`

- [x] [DIAG] P1. ✅ Root-cause why the live daily `collect-perp-funding` Cloud Scheduler job (market-tick-data-service,
      `defi_collection_scheduler.tf:112`, 01:15 UTC) produces zero MTDS manifest rows for `perp_funding` across every
      one of 12 tested days (2026-05-01..2026-07-28), despite `perp_funding_handler.py` resolving the correct canonical
      bucket and a historical 12,500-captured-row count. This is the sole live blocker keeping
      `data_pipeline_check_mdps_features_2026_07_20.md`'s DEFI:onchain dependency-check gate permanently closed. Repo:
      market-tick-data-service. Done when: root cause is identified and either fixed or filed as a scoped follow-up with
      the specific broken link named. Source:
      `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md` — **2026-07-31**: NOT a
      scheduler/handler bug — both run correctly daily (verified live: `state: ENABLED`, last 5 executions all
      `Completed`, today's log shows 5568 Hyperliquid + 39 kalshi_perp rows written AND manifest-registered). Root
      cause: every live `perp_funding` venue (HYPERLIQUID/KALSHI_PERP/POLYMARKET_PERP) was reclassified DeFi->CeFi by 3
      independent operator rulings (2026-07-06/07-25/07-26), so 100% of writes land in the CEFI bucket
      (`market-data-tick-cefi-prd-...`), never the DEFI bucket the dependency check reads — a permanently-unsatisfiable
      required dependency, not a freshness gap. Filed
      `issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md` with full evidence + the
      scoped fix (operator/main call on removing vs. relocating the `UPSTREAM_DEPS_DEFI` requirement — touches
      cross-plan gating semantics, out of scope for this diagnostic todo per its own "fixed or filed as a scoped
      follow-up" bar). **2026-08-01**: that issue doc's all 3 todos now shipped + archived to
      `/plans/archive/issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md`. Flipped +
      archived the source issue doc's own follow-up todo (both its todos done, successor named). Updated
      `data_pipeline_check_mdps_features_2026_07_20.md`'s gating note with the corrected root cause.
      unified-trading-pm@7e55d5b1b (investigation + new issue doc + gating-note update), unified-trading-pm@c59ccdd4b
      (source issue doc archival).

- [x] [DATA] P1. Delete the orphaned `gs://features-defi-prd-central-element-323112/onchain/_index/` GCS tree (dead
      2026-07-18 bucket-fold migration debris carrying 13 frozen false-captured/feature-less manifest rows) — under a
      FRESH same-run `gcs_bucket_soft_delete_retention_seconds()` reversibility check per delete-safety-protocol finding
      T — then bulk-register the 724-object historical `onchain/by_date/` corpus (2026-01-25..2026-07-26) into the live
      root availability_index manifest via `record_captured`/`record_empty`/`record_failed` per (date, feature_group),
      mirroring the `defi_fold_manifest_registration_pending_2026_07_21.md` recipe. Two source docs independently
      surfaced this SAME gap (same GCS tree, same 724-object corpus) — merged into one todo to avoid a duplicate
      dispatch. Repo: market-tick-data-service / features-service (whichever owns the manifest-registration call site).
      Done when: the dead tree is deleted (reversibility check cited) and all 724 objects show manifest rows. Sources:
      `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`,
      `archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md` — ✅ **features-service@d8a643a0
      (slot-4, 2026-07-30).** Shipped as the SAME todo in the source issue doc (this was a duplicate dispatch of that
      doc's own todo, per this todo's own note above); flipping here too so no other worker re-dispatches it. Fresh
      `gcs_bucket_soft_delete_retention_seconds()` returned `604800` (≥ threshold) — 4 orphaned `onchain/_index/`
      objects deleted + post-delete-verified gone. The real live corpus was 1538 objects (not 724 — that estimate was
      stale; spans 2021-08-17..2026-07-26, not just Jan-Jul 2026): 1508 gap rows registered (918 `captured` + 590
      `attempted_failed`), 30 already live-registered. Verified via direct per-VM-shard read. Full detail in the source
      issue doc's own Todos entry.

- [x] ✅ [INFRA] P1. Relaunch the DeFi features-service backfill VM OOM/hang repro on a SPOT VM with a more robust ON-VM
      (not SSH) ps/free/dmesg monitor to (a) validate the shipped finding-1 fix (`unified-trading-library@06190d77`)
      once features-service has picked up the wheel, and (b) capture the final 30-60s before any kill to settle whether
      this is genuinely OOM or a hang (attach `py-spy` if a hang is confirmed). Separately: scope and fix the
      `BlobMetadata.size: int = blob.size or 0` accounting hole (`cloud_interface/providers/gcp.py:301`) that miscounts
      a genuinely-unknown (`None`) GCS blob size as a free (cost=0) shard against the 200MiB per-VM-shard merge budget;
      and fix `unified-trading-library`'s `test_5000_sequential_writers_do_not_leak_fds`, which fails inside the full
      `quality-gates.sh` suite (passes standalone) and is currently blocking otherwise-green commits from shipping.
      Resolving this unblocks `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo, currently `[BLOCKED-INFRA]`.
      Repos: unified-trading-library, features-service, deployment-service (VM launch). Done when: the OOM-vs-hang
      question is settled with fresh VM evidence, the BlobMetadata bug is fixed + tested, and the flaky FD-leak test is
      green inside the full suite. Source: `issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md` — ✅
      **deployment-service (VM ops only, no code change), 2026-07-30 (slot-14).** All 3 done-when legs closed: (1) **VM
      relaunch/monitor**: `oom-hang-monitor.sh` + its `setup-data-pipeline-vm.sh`/`launch-features-vm.sh` wiring already
      existed (built same day by a prior slot) — verified both GCS objects byte-identical to local HEAD, no changes
      needed. Republished all 5 code tarballs fresh, then relaunched the exact repro
      (`features-onchain-defi-20260730-202653`, `OOM_MONITOR=1`, `SKIP_DEPENDENCY_CHECK=1` — an unrelated, already
      separately-tracked MTDS lending_indices/perp_funding data gap for 2026-07-20 otherwise blocks preflight for this
      date). **Result: clean `exit_code=0` in ~2 min; on-VM monitor's 40 polls (3s cadence, full run) show flat ~603 MB
      RSS and zero dmesg oom/killed hits — no OOM, no hang, question settled.** (2) **BlobMetadata.size**: already fixed
      by a prior slot same day (`unified-trading-library@5ab129d4`, `_resolve_list_blobs_size()` retry-via-reload
      approach) — verified correct by code read. (3) **FD-leak test**: already fixed by a prior slot same day
      (`unified-trading-library@880b2fb2`, `_settled_fd_count()` multi-pass GC settling) — independently reverified
      green inside the full `quality-gates.sh` suite (exit 0, 176s, sentinel written at unchanged HEAD `3d6454c4`).
      Flipped `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 `[BLOCKED-INFRA]` tag to unblocked (D1's own
      full-window backfill compute is separate follow-on work, not executed here). Closed the source issue doc
      (`status: resolved`). Full evidence + commit SHAs in both docs' Progress Logs.

- [x] [SCRIPT] P1. ✅ Pause the MTDS manifest-consolidator cron, run
      `restamp_lending_instrument_type_2026_07_24.py --apply` (after its own dry-run + pre-apply snapshot), verify
      post-write output, resume the cron. No longer operator-gated per the 2026-07-28 CLAUDE.md ruling on this class of
      action. Then confirm the distinct-values panel (`GET /distinct-values/defi`) no longer badges `liquidation` as
      non-canonical for this writer path, cross-link the result into the archived parent audit plan's Progress Log, and
      close out the source plan. Repo: market-tick-data-service, deployment-api. Done when: the restamp is applied +
      verified and the distinct-values panel confirms the fix, both cited in the source plan. Source:
      `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md` (todos 4-5, sequential) —
      **2026-07-31**: this whole workstream was already done by prior slots (source plan's 5/5 todos + apply already
      shipped `mtds@be064c27`; scope was 0 the entire time, `--apply` a provable no-op, no cron pause needed since no
      write occurs). What was still genuinely open was the paired gated finalize twin
      (`market_tick_data_service_lending_instrument_type_historical_restamp_finalize_2026_07_30.md`, todos 3-4) —
      completed both here: re-confirmed the distinct-values panel live one more time (`source_date=2026-07-31`,
      `liquidation` absent, `non_canonical_count.instrument_types == 0`), cross-linked into the archived parent audit
      plan's Progress Log (correcting a premature "already archived" claim written there 2026-07-30), then ran the
      6-step archival ritual and archived both the source and finalize plans to `plans/archive/2026_07/` (regenerated
      `plans/active/INDEX.md`). unified-trading-pm@bf555dd71 (checkbox flips + cross-link), unified-trading-pm@c1be9e1dc
      (archival move + INDEX regen).

- [x] ✅ [TEST] P2. Add a regression test asserting `load_pool_metadata_for_date` resolves a blob written under EITHER
      the pre-cutover flat shape OR the post-cutover hive shape (two fixture cases), guarding against future
      path-grammar regressions. Then remediate the ~4 days (2026-07-23 onward) of already-written dishonest
      `record_zero_rows` manifest stamps for morpho/fluid/kamino_lending `risk_params`: identify affected manifest rows,
      reclassify, and re-run/verify end-to-end (reversibility-cleared per finding T — executable as a full dispatch, not
      just a proposal). Repo: market-tick-data-service. Done when: the regression test is green and the ~4 days of
      dishonest stamps are reclassified + re-verified. Source:
      `issues/mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` (todos 6-7) — **DONE 2026-08-05
      (slot-10, data_engineering)**: market-tick-data-service@9ea92119 (regression tests: regex grammar guard +
      mixed-layout resolve + no-match guard, 3/3 green) + market-tick-data-service@e160f639 (one-off remediation script:
      dry-run identifies 210+ affected rows; --apply corrects 6 manifest stamps for MORPHO ETHEREUM+BASE ×
      2026-07-23..25 via DefiManifestRecorder). Full sweep blocked on todo 8 (VM redeploy — stale tarball still runs
      pre-fix reader, would re-overwrite). Remediation script committed with lifecycle markers, ready for re-run after
      todo 8 lands.

- [x] ✅ [DATA] P2. Investigate the 6 `lending_indices` `record_empty(SOURCE_RETURNED_ZERO)`/FetchEvidence guard
      rejections (MORPHO x2, COMPOUND_V3 x4, dated 2026-07-26) — determine whether the guard is correctly blocking a
      genuine upstream problem or wrongly rejecting a legitimately-empty day, then fix the root cause. Separately
      investigate `dex_pool_state`'s 19 `build_instrument_id` errors: identify which venue/instrument shapes fail id
      construction, then fix. Repo: market-tick-data-service. Done when: both investigations have a recorded root-cause
      verdict, with a fix shipped for each if warranted. Source: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (2 DATA
      items) — **VERIFIED 2026-08-05 (slot-7, data_engineering): both investigations already completed by prior slots.**
      **lending_indices**: root cause = id-space mismatch between `market_count_map()` keys (raw on-chain addresses) and
      IS catalogue `instrument_id` (canonical `VENUE-CHAIN:TYPE:SYMBOL` glued form) — the catalogue-residual wiring
      (`market-tick-data-service@eae703b0`) made every catalogued lending reserve read as "residual" even when real
      markets were captured. The FetchEvidence guard was **working correctly** — it correctly rejected unsubstantiated
      `SOURCE_RETURNED_ZERO` claims. Fix: `market-tick-data-service@d36e2498` removed the structurally-invalid
      `record_catalogue_residual()` call (landed 2026-07-29, zero new occurrences since). Grew to 198 total rows
      (MORPHO×66, COMPOUND_V3×132 across 6 chains) before fix landed; all now have superseding `captured` rows.
      **dex_pool_state**: root cause = pool symbols containing `:` triggering `build_instrument_id`'s colon-delimiter
      collision (UAC `canonical_id_builder.py:851`). 33 errors across SUSHISWAP/ARBITRUM (10), TRADER_JOE_V2/AVALANCHE
      (5), UNISWAP_V4/ETHEREUM (17), ORCA/SOLANA (1). Filed
      `issues/dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`. Source doc Progress Log entries at
      `mvp_backfill_defi_onchain_v10_2026_06_27.md:394-406` + `:426-430`.

- [x] ✅ [SCRIPT] P3. Retry the 2 `lst_rates` 429-rate-limited cells (trivial). Then wire up the disabled
      `shard_exists_prefix` skip-if-captured hook across every DeFi handler (`oracle_prices_handler.py`,
      `lst_rates_handler.py`, `dex_pools_handler.py`, `perp_funding_handler.py`, etc.) so date-range re-runs become
      incremental instead of unconditionally re-fetching/re-writing the whole range — wire the caller into
      `service_framework/_adapter.py`'s `_drive_serial`/`_drive_concurrent` loop. Repo: market-tick-data-service. Done
      when: the 2 cells are retried and captured, and the skip-if-captured hook is wired + verified on at least one
      handler with a regression test. Source: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (2 SCRIPT items)

- [ ] [DIAG] P3. Delete the 916 HYPERLIQUID + 642 ASTER redundant legacy `defi`/`perp_funding` rows and rebuild the defi
      index; separately, relax RULE 11 (`_EXTRA_LIVE_PROBE_SOURCES_BY_AG`) to cover cefi CEX venues and re-run the
      phantom-row auditor. Both items were operator-RULED AO-ready on 2026-07-28 (postdating
      `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s previously operator-decision-gated classification of this same
      doc — the ruling supersedes that deferral for these 2 items specifically; the HYPERLIQUID k-prefix coin-case
      question in the same doc remains genuinely design-gated and stays deferred below). Repo: market-tick-data-service
      / deployment-api (index rebuild). Done when: both operator-ruled actions are executed and verified. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`

      **CORRECTED 2026-08-12 (/plan-reconcile) — inline delete-safety citation** (was a bare "operator-RULED" date
          reference; the destructive step needs the actual reversibility citation inline, per
          `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a): reversibility cleared per finding T —
          `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` todo 7 confirmed the same bucket
          (`market-data-tick-defi-prd-central-element-323112`) at `604800s` GCS Soft Delete retention as of 2026-07-27.
          **Whoever executes this todo must re-verify `gcs_bucket_soft_delete_retention_seconds()` fresh in the same run
          before the actual delete** (cheap, keeps the finding-T check same-run for the destructive step itself) — but no
          fresh operator ask is needed to START this dispatch. Full context:
          `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md:387-399`.

- [x] ✅ [SCRIPT] P2. Project every bare `read_availability_index()` call site to actual column usage across: unified-
      trading-library `manifest_writer/_queries.py` (4 sites) + `_maintenance.py` (4 sites) + `_writer_io.py:156`;
      features-service `volatility/engine/orchestrator.py:276`, `volatility/core/orchestration_service.py:168`,
      `volatility/core/data_loader.py:364`, `delta_one/app/core/dependency_checker.py:619`; instruments-service
      `engine/orchestrator/process_completeness.py:468` `_detect_thin_day_venues`; batch-live-reconciliation-service
      `stages/stage0_manifest_reason_check.py:177`; deployment-service `cli/utils/manifest_reader.py:245,585,674`. Then
      author a QG check mirroring `check_manifest_writer_missing_write_before_return.py` that flags NEW bare
      `read_availability_index()` call sites, baseline-ratcheted — the durable enforcement gap nothing currently closes.
      Repos: unified-trading-library, features-service, instruments-service, batch-live-reconciliation-service,
      deployment-service, unified-trading-pm. Done when: every listed call site is projected (fixed or confirmed safe)
      and the new QG check is shipped + baseline-ratcheted. Source:
      `issues/read_availability_index_bare_defi_callers_2026_07_27.md` — **DONE 2026-08-05 (slot-13,
      data_engineering)**. All call sites already projected or intentionally bare (verified by prior slots:
      UTL@6b0d0847, features@edf80c88, instruments@5134a5f0+325da86, blr@11cec2c, deployment@b1480a1). QG check +
      baseline shipped 2026-07-31 (slot-5). This session: synced baseline line numbers after code drift, removed 4 stale
      entries — unified-trading-pm@d987f9a08 (19 baselined, 0 new occurrences via
      `check_bare_read_availability_index.py`).

- [x] ✅ [INFRA] P3. Bump the defi-specific default manifest-recon VM machine type to 32Gi+/8vCPU-equivalent (or move to
      a Cloud Run job mirroring `cf_manifest_audit_scheduler.tf`'s provisioning) instead of relying on the ad-hoc
      per-run `MACHINE_TYPE` override. Add a lighter-weight, column-pruned read path to
      `merge_canonical_with_outstanding_shards` (or a scoped sibling helper) for verification/dry-run-only callers that
      don't need the full wide-schema materialization. Repos: deployment-service, instruments-service,
      unified-trading-library. Done when: the manifest- recon VM/job runs on adequate provisioning and a column-pruned
      read path exists for dry-run callers. — **DONE 2026-08-05 (slot-2, infra).** VM-machine-type bump shipped at
      deployment-service@6bfeae2bc (all 3 defi manifest-recon launchers default to e2-highmem-8/64GB for
      ASSET_GROUP=defi, other AGs keep e2-standard-4). Column-pruned read path shipped at
      unified-trading-library@c1ec7311 (`columns=` parameter on `merge_canonical_with_outstanding_shards`, preserving
      full-schema default for `--apply` write-back callers). Both verified on origin. Source:
      `issues/reconcile_phantom_manifest_rows_all_defi_memory_footprint_2026_07_28.md`

## Deferred

### Conflict-gated (re-check first before spinning batch7 — clears the moment its named competing claim ships)

1. **`defi_venue_lst_rates_residual_2026_07_24.md`** — SUSHISWAP classic-vs-V3 alias question. Already correctly
   classified operator-gated by both batch2 (excludes it explicitly) and batch3 (parks it as BLOCKED-OPERATOR-DECISION).
   Still unruled as of this run — re-check after any operator SUSHISWAP ruling.
2. **`issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s item 2** (sweep already-drivable DeFi
   archetypes CARRY_FUNDING_DISPERSION/DEFI_LP_CONCENTRATED/DEFI_LP_POOL/DEFI_LP_VAULT for the same config-key-contract
   drift bug class) — this narrower sub-item reads as mechanically bounded on its own, but the doc as a whole was
   already classified operator-gated by batch5 ("awaiting an operator prioritization call on which to fix first") and I
   have no fresher evidence that ruling has landed. Rather than unilaterally override a prior batch's operator-gated
   classification on a doc-level call, this is parked as a genuine judgment call: **operator decision needed** — confirm
   whether item 2 can be pulled out and dispatched independently of the other 4 design-gated items in the same doc, or
   whether the doc should be prioritized as a whole first.

### Non-batchable orphans (27 docs) — operator-gated / time-gated / too-large-or-risky / human-only

Re-check taxonomy before spinning batch7: a **conflict-gated** item above clears the moment its named competing claim
ships/resolves; the items below need direct human action (a design call, an operator ruling, elapsed time, or a
dedicated standalone plan) — re-running this skill will keep re-surfacing them unchanged until that happens.

**Operator-gated (design/judgment call, no evidence-based tiebreaker):**

- `data_completion_defi_2026_07_15.md` — G2/G3/G4 (live-snapshotter → operator-launched paper-trade → human-only promote
  chain) and G6 (Jupiter historical reconstruction, explicitly parked by batch3) are all human/operator-gated; E1 is a
  mistagged CeFi item (parent_epic: cefi_master) needing a CeFi-tranche plan, not a DeFi one.
- `defi_dedicated_bucket_shared_migration_2026_07_13.md` — repoint/delete of ~8 dead MTDS Lifecycle:campaign scripts is
  blocked on an ambiguous condition inside an ARCHIVED plan with no current owner; needs an operator ruling on who owns
  re-scoping that condition before a fresh todo can be drafted safely.
- `defi_migration_audit_log_2026_07_24.md` — 10 of 11 remaining items are explicit design/operator-sign-off calls (Era-B
  legacy retirement scoping, Solana-source per-venue mapping implementation timing, orphan-bucket delete sign-off,
  gas-fees denominator grain choice, etc.) per batch3's own prior STALE-premise/deferred grouping; only the "LOCAL QG
  HARNESS collects the wrong test suite" finding is bounded-sounding but under-evidenced (zero coverage found anywhere)
  — needs a scoping read before it's draftable.
- `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` — delete-vs-re-leg
  `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` onto Jupiter is a strategy-domain call; already parked human-only
  by batch2/batch3. UI resync + registry-generator investigation both gate on that decision landing first.
- `issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — RecursiveLoopOrchestrator gap and the
  2026-07-28 MVP_SCOPE catalog-enforcement finding both explicitly need an operator design/scoping session; the
  CARRY_BASIS_DATED_INV direction-key question is an unresolved product decision.
- `issues/defi_adapter_dead_code_audit_2026_07_24.md` — jupiter.py fate (register vs delete) and the
  governance-parameters-refresh re-verification (flagged OPERATOR-NOTIFY/big finding — should be escalated directly, not
  batched) both need human judgment; the onchain_event_poller/alchemy/thegraph_ws disposition call is the same class.
- `issues/defi_code_codex_drift_2026_05_27.md` — D15's HYPERLIQUID/ASTER legacy-to-canonical AG migration is "explicitly
  not yet scoped" and needs a dedicated VM-backed plan authored first — an authoring decision, not a worker-executable
  step today.
- `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` — the `_INSTRUMENT_TYPE_ALIASES` vs legacy
  `venue_mapping.DataTypeConfig` SSOT contradiction for A_TOKEN/DEBT_TOKEN needs an explicit operator/engineering ruling
  before scoping; the 63.9M-row seed-apply completion itself is gated behind that + the manifest purge.
- `issues/defi_lst_empty_marker_hardcoded_venue_2026_07_27.md` — the physical-marker-write-vs-manifest-only architecture
  decision is explicitly "left for a future decision" by the doc itself; a stale `locked_by` artifact additionally
  blocks archival pending operator review.
- `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` — durable UAC registry fix blocked on an operator
  ruling (double-counting risk across CEFI+DEFI denominators); already filed BLOCKED-OPERATOR-DECISION by batch3/5.
- `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md` — retry-sweep-signal mechanism ownership choice needs a
  human call; already acknowledged by batch3/5.
- `/plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md` (RESOLVED + archived 2026-08-01)
  — building 6 genuinely new instruments-service reference-data adapters is a substantial new-build the doc's own
  2026-07-30 section recommends spinning up as its own dedicated multi-todo plan, not a single batch todo — an
  authoring/prioritization decision.
- `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — resyncing the 4th prospectus instance is
  genuinely unowned pending a human ruling on which side (generator output vs committed files) is authoritative.
- `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — D1 is operator-ruled DEFERRED-BY-DESIGN; D2's
  actual open checkbox lives in a sibling NA-assigned plan
  (`defi_collateral_sizing_and_wizard_full_parameterization_ 2026_06_17.md`), not this doc; D4 is BLOCKED-CREDENTIALS
  cross-referencing another design-gated doc.
- `issues/lst_yields_writegate_permanently_blocked_2026_07_28.md` — adding wBETH/sanctumSOL to the LST registry needs a
  correctness-minded naming decision; reconsidering STRICT_FAIL vs PARTIAL_OK emission-policy semantics is a design
  call. (The Idle/Pendle scope-creep investigation item is lower-confidence bounded — held for batch7 pending a fresh
  read, not drafted here to keep this batch's quality bar high.)
- `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` — the (B) FX-noise-isolated native
  staking-return metric build touches the money-path and needs a 3-lens review + explicit go-ahead before dispatch; the
  ShareClass enum convergence is a cross-cutting architecture decision (9-value vs 3-value canonical shape) beyond a
  single-repo bounded fix.
- `issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` and `lst_exchange_rate_data_availability_2026_07_21.md`'s
  Solana-DEX-handlers gap (same underlying capability gap, both need a dedicated Solana on-chain swap-event indexer plan
  authored) — already correctly classified deliberately non-AO-dispatched by batch5: "its own ask is to author a
  brand-new dedicated implementation plan when it becomes a priority — that authoring decision is the operator's, not a
  worker's." Not re-litigated here.
- `lst_rate_honest_coverage_2026_07_21.md` — Phase 6 E3 recursive-staking borrow leg touches strategy money-path,
  explicitly deferred by batch3; Phase 5 #4 lst_yields feature compute is explicitly operator-owned (runner script
  forbids agent execution).
- `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`'s todos 3 and 5 (spot-check + manifest cross-check)
  — genuinely bounded verification tasks, but held for batch7 pending confirmation the todo-6 fix above (drafted this
  batch) has landed first, since both re-checks are more informative post-fix.

**Time-gated (elapsed time / external process, not a worker decision):**

- `defi_expected_unattempted_seeder_design_2026_07_26.md` and `defi_dex_pool_symbol_fix_backfill_purge_*` — both
  verdicted archivable_after_planned_work this run (already covered by active work), not orphaned; listed here only for
  completeness, no action needed.
- `issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`'s downstream consequence — batch3's D1 todo
  stays `[BLOCKED-INFRA]` until this batch's own INFRA todo (drafted above) resolves; not independently gated.
- `lst_rate_honest_coverage_2026_07_21.md`'s Phase 5 #1 CEX-spot Tardis backfill — blocked on the still-open P0 issue
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`; re-check once that VM-memory bug is fixed. Phase 5 #2
  dex_pool_swaps 3-VM fleet completion is in-flight (multi-day-to-multi-week runway as of last check) — a
  watch-to-completion item, not a fresh dispatch.

**Too-large-or-risky-for-a-batch-todo (live, multi-phase, or a substantial new build):**

- `defi_migration_audit_log_2026_07_24.md`'s DELETE-duplicate-orphan-buckets item — needs explicit operator sign-off per
  the GCS delete-safety HARD RULE, not a batch todo.
- `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`'s 63.9M-row seed-apply completion — large-scale, gated
  behind the manifest purge + glued-id rebuild; belongs in its own dedicated plan/monitored VM run, not a single batch
  todo.
- `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`'s §6.3 capability-completion (11 of 14 UAC-declared
  staking protocols unimplemented) — a substantial multi-protocol build, not a bounded single todo; §6.2 already has a
  drafted (not yet active) todo in batch5.

**Human-only, permanently (until content changes):**

- `data_completion_defi_2026_07_15.md`'s Progress-Log P2 "sub-bucket blank-chain phantom audit" (line 855) — genuinely
  bounded-sounding (canonicalize at the IS seeder) but under-scoped in the source text; held for a fresh read before
  drafting rather than guessing the fix shape.
- `defi_migration_audit_log_2026_07_24.md`'s remaining items not otherwise categorized above.

### Known, already-covered (verdict archivable_now / archivable_after_planned_work this run — no action needed here)

`defi_strategy_pnl_axis_index_2026_07_24.md`,
`issues/defi_instrument_availability_duplicate_instrument_key_rows_2026_07_26.md`,
`issues/defi_kamino_solend_lending_indices_legacy_shape_fabricated_history_2026_07_28.md`,
`issues/defi_mvp_backfill_optimization_ready_2026_07_20.md`,
`issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md` (archivable_now);
`/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (+finalize),
`defi_expected_unattempted_seeder_design_2026_07_26.md` (+finalize),
`issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`,
`issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`,
`issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`,
`issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md`,
`issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`,
`issues/lighter_tardis_writerless_route_hang_2026_07_28.md`, `issues/phantom_captures_defi_2026_06_28.md`,
`mvp_backfill_defi_onchain_v10_2026_06_27_finalize_2026_07_27.md`, `scenario_library_completion_13_16_2026_07_27.md`
(archivable_after_planned_work).

## Progress Log

- 2026-07-30 (slot-2, scheduled `ag_closeout_auditor`, tranche=defi): Ran a fresh full Phase-1 classification (66
  agents, sonnet) over all 66 defi AG-primary docs via a Workflow fan-out, cross-checked against a 16-doc covering-plan
  set. 48 orphaned (14 partial, 34 never-touched); Phase-3 conflict-check (manual synthesis over the Phase-1 evidence,
  reusing the exhaustive per-doc citation checks Phase 1 already performed against all 16 covering plans) drafted 20
  todos from 21 conflict-clear orphaned docs (2 merges to avoid duplicate dispatch), deferred the remaining ~27 orphaned
  docs by taxonomy (operator-gated / time-gated / too-large / human-only) below for the next iteration or an operator
  ruling.
- 2026-07-30 (slot-14): Closed the `[INFRA] P1` VM-relaunch todo. All 3 done-when legs confirmed: on-VM OOM/hang monitor
  relaunch (clean `exit_code=0`, flat ~603 MB RSS, zero dmesg oom hits — bug no longer reproduces with
  `unified-trading-library@06190d77` live), BlobMetadata.size accounting fix (already shipped `@5ab129d4` by a prior
  slot same day, verified), FD-leak test (already shipped `@880b2fb2` by a prior slot same day, independently reverified
  green in the full suite). Closed `issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`
  (`status: resolved`) and unblocked `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo (`[BLOCKED-INFRA]` tag
  removed; D1's own backfill compute is separate follow-on work, not executed here). Also corrected this doc's stale
  draft-banner (frontmatter had already flipped to `active` but the body banner still read "draft — NOT dispatched").
- 2026-07-31 (slot-16, data_engineering): Closed the "bad indexers" `[DATA] P1` todo. Confirmed the existing
  `market-tick-data-service@74cd6cfd` fail-fast classification fix already covers all 8 pairs generically (code read),
  shipped a bounded retry-with-backoff for the GraphQL-level condition (`market-tick-data-service@5c12c9e5`, QG-green +
  2 new tests), and live-probed all 8 pairs today with real production queries: VELODROME_V2/OPTIMISM and
  PANCAKESWAP_V3/BSC self-healed (retry-fixable), UNISWAP_V3/OPTIMISM confirmed persistently broken across 4+ days
  (identical indexer fingerprint since 2026-07-27) — a bounded retry can't fix this class; researched The Graph Explorer
  for a replacement deployment ID, found a currently-healthy candidate but didn't vet/swap it blind, filed as a new
  `[DIAG] P2` follow-up todo instead. Full before/after `attempted_failed` counts per pair in the todo's own evidence
  above.
- 2026-07-31 (slot-16, data_engineering): Worked the DeFi pool catalogue expansion `[DATA] P1` todo. Shipped
  `instruments-service@1fb9c490` (manifest-driven discovery + tested-merge reuse, +14 unit tests): prod catalogue 12,382
  → 71,538 rows, 62,592 newly-discovered historical pool addresses across 28 (venue,chain) pairs, every default DEX
  protocol accounted for (KAMINO deliberately excluded pending its own identity-scheme investigation, new `[DIAG] P3`
  follow-up filed). **Real incident along the way**: an earlier run of the script left an orphaned process running
  ~37min post-completion at 43.6GB RSS, causing a fleet-wide agent-orchestrator outage — operator caught + killed it, I
  found and killed a second at-risk process from my own follow-up investigation, then root-caused (unfiltered ~50-column
  manifest read + no forced process exit) and fixed both (column-pruned read + `os._exit()`), re-verified safe under a
  hard 20GB `ulimit -v` cap. Review independently verified the fix live
  (`issues/expand_defi_pool_catalogue_script_ unbounded_memory_2026_07_31.md` — the canonical home for this incident's
  residual diagnostic/hardening/cross-cutting follow-ups, cross-linked against 3 same-day sibling manifest-memory
  incidents; not duplicating its todos here). Split the todo's checkbox — the catalogue-expansion scope is DONE (flipped
  `[x]`); the denominator-recompute half of the original "Done when" bar is split into a new `[DATA] P2` follow-up
  (needs the SAME VM-dispatch pattern `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` already established
  for this exact class of large manifest write, not a quick in-session step).
- 2026-08-01 (slot-16, data_engineering): **Closed** the composite-venue fold `[DATA] P1` todo (5,332 legacy objects, 9
  venues, `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`). Shipped
  `market-tick-data-service@13f14b78` (the fold script, `scripts/fold_legacy_composite_venue_objects_2026_07_31.py` + 32
  unit tests), `@36238a7c` + `@69c7ba7c` (two UNRELATED pre-existing QG regressions found while shipping — DEFI
  shard-count ratchet stale after the 6-venue pipeline→live flip, and 3 net-new `type: ignore` suppressions in this
  script — both fixed inline as small/clear, confirmed pre-existing via `git stash` before touching). **Real findings
  baked into the script + its docstrings/tests**: (1) 3 of the 9 composite venues (`UNISWAPV2/V3/V4-ETHEREUM`) plus
  `AAVEV3-ETHEREUM` need `VenueMapping.normalize_defi_venue` — folding the raw no-underscore name would have created a
  SECOND non-canonical venue segment alongside the one live captures already use; (2) 3 legacy row-level `data_type`
  values do NOT match the live capture vocabulary (`rate_indices`/`utilization` → `lending_indices`, `liquidity` →
  `dex_pool_state`, `swaps` → `dex_pool_swaps`) — verified against the actual live handler source (`_lending_grain.py`,
  `_dex_pools_subgraph.py`, `dex_swaps_handler.py`); (3) Morpho's real symbol shape (`{pair}:{market_address}`) is
  REJECTED outright by `build_instrument_id` (embedded `:` collides with its own delimiter) — confirmed by the test
  suite hitting the real error, fixed via a symbol sanitizer. Manifest registration mirrors the per-instrument grain the
  live handlers actually use (confirmed via a dedicated sub-agent research pass across 6 live handlers).

  **Executed to completion**: full `--dry-run` (5,332/5,332 shards, zero errors) followed by the real `--apply`
  (`--workers 12`, `GCP_PROJECT_ID`+`MANIFEST_PER_VM_SHARDS=true` exported per the standalone-script gotchas
  `defi_fold_manifest_registration_pending_2026_07_21.md` traced) — **5,332/5,332 shards, ZERO errors, 324,867 objects
  written, 324,867 manifest rows registered**. Verified via: (a) the script's own per-shard content-parity invariant +
  GCS read-back spot-check (never violated across the whole run), (b) direct GCS content reads of 4 freshly-written
  objects across 4 venues, (c) a properly-filtered `read_availability_index(columns=[...], filters=[...])` read
  confirming `capture_status=captured` for every sampled (venue, day) — AAVE_V3/2024-05-06 (132 rows), MORPHO/2024-05-05
  (73), ETHENA/2024-05-03 (4), LIDO/2024-05-02 (3), UNISWAP_V3/2024-05-11 (6,814). The manifest consolidator was
  launched to merge the fresh per-VM shards into the canonical index; per the established precedent, the reader's live
  per-VM-shard-merge fallback already surfaces the correct state regardless of consolidator completion. Full per-venue
  breakdown + evidence in the todo's own checkbox entry above.

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — fixed a duplicate `context_scope` frontmatter key
  (two blocks present) and consolidated into one list anchored on the dispatch methodology + parent covering plan + the
  batch conflict-check protocol.

- **2026-08-04 (slot-8, data_engineering)**: Completed the `[SCRIPT] P2` UAC shadow-copy sweep across all 4 DeFi repos
  (instruments-service, market-tick-data-service, features-service, market-data-processing-service). **Result: 0 genuine
  UAC shadow drifts found.** All 42 inventoried sites fall into 3 categories:

  **Category 1 — Token Decimals (26 sites, NO UAC SSOT exists):** UAC has no `TOKEN_DECIMALS` registry. Local dicts are
  genuine SSOTs, not shadows. `_EVM_TOKEN_DECIMALS` (27 entries in `instruments-service/defi_utils.py`) is the defacto
  standard, used by venus/benqi/euler_v2/radiant adapters. `_SPL_TOKEN_DECIMALS` (kamino.py) for Solana SPL tokens.
  `_ASSET_DECIMALS` in yearn.py (5 vault assets) and beefy.py (mooTokens). 18 per-adapter single-token constants
  (convex/renzo/solblaze/eigenlayer/stakewise/swell/wbeth/cbeth/jito_restaking/stader/pendle/kelpdao/rocket_pool/ethfi/
  maker/sanctum/ankr/puffer/mantle/aave_oracle) — all well-documented. MTDS: `SOL_DECIMALS`/`USDC_DECIMALS` in 3
  handlers (raydium_classic_amm, jupiter_quote, orca_whirlpool_state). **Verdict: No drift possible (no UAC SSOT). All
  sites are genuine local registries, properly commented with provenance.**

  **Category 2 — Chain Genesis Dates (2 sites, match UAC):** Both local Solana genesis copies (`_SOLANA_GENESIS_DATE` in
  IS `solana_native_staking.py` and `_GENESIS_DATE` in MTDS `native_staking_handler.py`) use `2020-03-16` —
  byte-identical to UAC `CHAIN_GENESIS_DATES["SOLANA"]`. UAC's `get_chain_genesis_date("SOLANA")` exists and could
  replace both, but the values currently match. **Verdict: No drift (values match UAC). Low-severity deduplication
  opportunity — not blocking.**

  **Category 3 — Factory Addresses & Protocol Registries (11 sites, proper cascade or net-new):**
  `UNISWAP_V3_FACTORY_BY_CHAIN` in `_dex_factory_registry.py` imports from UAC's `dex_router_addresses.py` (proper
  cascade, 0 drift risk — verified 5-chain match: ETHEREUM/BASE/ARBITRUM/OPTIMISM/POLYGON). 4 net-new registries
  (`UNISWAP_V2_FACTORY_BY_CHAIN`, `UNISWAP_V4_POOL_MANAGER_BY_CHAIN`, `SUSHISWAP_V2_FACTORY_BY_CHAIN`,
  `SUSHISWAP_V3_FACTORY_BY_CHAIN`) cover protocols UAC doesn't register — each entry cites an official source +
  independent cross-check. `_AAVE_V3_POOL_ADDRESSES` + `_AAVE_V3_DATA_PROVIDER_ADDRESSES` (MTDS
  `lending_indices_handler.py`, 9 chains) and `A_TOKEN_ADDRESSES`/`DEBT_TOKEN_ADDRESSES` (MTDS `aave_utils.py`, 5 assets
  ETH-only) are well-documented local registries UAC doesn't cover. `FACTORY_ADDRESS` in `uniswapv2_adapter.py` is
  cross-referenced in `_dex_factory_registry.py`'s own docs as the canonical V2 factory. **Verdict: No drift (V3
  cascaded from UAC; all others are genuine local registries for protocols UAC doesn't cover).**

  **Category 4 — `LENDING_PROTOCOL_DEPLOY_DATES` (ALREADY FIXED):** The precedent fix at
  `instruments-service@evm_creation_resolver.py` is confirmed correct: UAC-first cascade via
  `get_protocol_launch_date()`, single remaining local entry (aave_v3/GNOSIS) is commented and justified, shape-lock
  regression test `test_no_dead_redundant_local_entries` exists. No further action needed.

  **features-service + market-data-processing-service: clean.** Zero shadow-copy sites found in either repo.

  No code changes shipped (no drifts to fix). The comprehensive inventory above satisfies the "written inventory of
  every shadow-copy site exists with a fixed/justified verdict for each" done-when bar. The source issue doc
  (`issues/defi_broader_local_fallback_vs_uac_sweep_2026_07_27.md`) is now fully addressed — its P3 script todo is done,
  its P3 operator follow-up (re-run drift check) can proceed against this inventory as the baseline.

- **2026-08-04 (slot-12, data_engineering)**: Completed the `[DIAG] P2` UNISWAP_V3/OPTIMISM subgraph replacement todo.
  Vetted the slot-16-identified candidate (`EgnS9YE1avupkvCNj9fHnJxppfEmNNywYJtghqiu2pd9`, "Uniswap V3 Optimism" on The
  Graph Explorer) against all 3 required axes using live TheGraph gateway probes:

  **(a) Schema compatibility — PASSED (cascade self-heal).** The candidate uses the Messari schema (`pool { id name }`)
  rather than the UniV3-native schema (`pool { id token0 { symbol } token1 { symbol } feeTier }`). `_UNIV3_SWAPS_QUERY`
  fails with "Type 'LiquidityPool' has no field 'token0'" (schema drift) → the existing 7-query cascade falls through to
  `_MESSARI_SWAPS_QUERY` which succeeds. This is the same self-heal pattern as AAVE_V3-OPTIMISM. All 6 cascade variants
  tested: `_UNIV3_SWAPS_QUERY` ❌, `_UNIV3_MINIMAL` ❌, `_MESSARI_SWAPS_QUERY` ✅, `_MESSARI_SWAPS_FROM_QUERY` ❌,
  `_MESSARI_LP_SWAPS_QUERY` ❌, `_MESSARI_LP_SWAPS_FROM_QUERY` ❌. `poolDayDatas` entity does NOT exist (Messari schema
  lacks it) — the `dex_pools_handler` path for UNISWAP_V3/OPTIMISM was already broken on the prior subgraph (same
  bad-indexers error blocks ALL queries, not just swaps).

  **(b) Historical coverage — PASSED.** Swaps found at all 7 checkpoints at 6-month intervals from 2023-01-01 through
  2026-07-01 (timestamps align with the start of each sample window, confirming data exists at the requested time
  boundaries). Full backfill window (≥2023-01-01) covered.

  **(c) Indexer health — PASSED (current snapshot).** Live `_meta` probe at ~20:22 UTC 2026-08-04: block=155,138,077,
  head lag ~1s, `hasIndexingErrors=false`, deployment=`QmdAoDVjfSByKvTW1HrCDK1eJJKRRZxdj8bcqVqQLCofN4`. The current
  subgraph (`Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj`) is still broken at probe time — same 3 bad indexers
  (`0xeccdf823...`/`0xf92f430d...`/`0xfeff9093...`) as 2026-07-31. Stability-over-time for the candidate is unproven
  (single point-in-time probe), but it's a strict improvement over the 100% non-functional current deployment.

  **Shipped**: `unified-api-contracts@516ae7bb` — swapped `SUBGRAPH_IDS["uniswap_v3"]["OPTIMISM"]` to the candidate,
  with a documented comment citing all 3 axes of vetting evidence + the `poolDayDatas` caveat. Regression test added in
  `test_defi_capability_registry.py`: `test_uniswap_v3_optimism_subgraph_is_non_empty` (asserts ID resolves, non-empty,
  ≥40 chars). Full QG green (316s), quickmerge landed on LDR, SHA verified on origin.

- **2026-08-05 (slot-4, data_engineering)**: Completed the `[DIAG] P2` KALSHI_PERP capture gap root-cause analysis. Both
  findings traced to their root cause via code-read of the handler (`_perp_funding_kalshi_polymarket.py`,
  `perp_funding_handler.py`), the R3 migration (`migrate_defi_batch_to_per_instrument.py`), and git archaeology around
  the key dates.

  **Finding (a) — 3 zero-object gap days (2026-07-17, 2026-07-20, 2026-07-21):** **Verdict: Transient upstream API
  condition.** The handler's `_collect_kalshi_perp` calls `_fetch_kalshi_perp_market_tickers` → Kalshi API
  `GET /margin/markets?status=active`. When this endpoint returns zero tickers, the handler returns 0 WITHOUT writing
  any GCS object (line 374-379: "no active CRYPTO markets" log followed by `return 0` — the log message says "writing
  empty marker" but the code returns 0 BEFORE any write call). On those 3 specific days, the Kalshi API either returned
  zero active crypto perpetual markets or was unreachable (connection error → caught, returns empty list). The
  scattered, non-sequential pattern (Saturday 07-17, Tuesday 07-20, Wednesday 07-21 — with data on Sunday 07-18 and
  Monday 07-19) is consistent with a transient upstream condition, not a code bug.

  **Finding (b) — `_migrated_kalshi_perp_<timestamp>.parquet` daily markers (2026-05-29..2026-07-16, 57 instances):**
  **Verdict: Inert R3 migration artifacts — renamed empty bundled parquet files from the pre-per-instrument-sharding
  era.** Chain of events: (1) Before `market-tick-data-service@4ca2640d` (per-instrument sharding, 2026-07-18), the
  Kalshi perp_funding handler wrote a single bundled `kalshi_perp_{ts}.parquet` per day to the DEFI bucket — mostly
  empty (API returned active tickers but zero historical funding rate events). (2) The R3 migration
  (`migrate_defi_batch_to_per_instrument.py`, executed ~2026-07-23) scanned the full DEFI bucket (2020-01-01..
  2026-12-31) and renamed bundled files to `_migrated_{stem}.parquet` — the R3 safety-rename convention (never deletes).
  (3) Markers stop on 2026-07-17 because: (a) on 2026-07-17, the Kalshi API returned zero tickers → no file written
  (same root cause as Finding a); (b) from 2026-07-18 onward, per-instrument sharding was deployed → new writes were
  per-symbol leaves (e.g. `KXBCHPERP.parquet`), not bundled `kalshi_perp_*` files → no bundled file for the R3 migration
  to rename. (4) The markers are 0-row empty parquet files — `delete_migrated_defi_markers` classifies 0-row markers as
  SAFE (deletion-eligible). `rebuild_defi_manifest.py` explicitly skips `_`-prefixed leaves (R3 defect A guard). No
  reader depends on these markers.

  **Follow-up**: The 57 marker objects are safe to delete via the existing
  `delete_migrated_defi_markers_2026_07_23.py --apply --venues KALSHI_PERP --data-types perp_funding` tool
  (reversibility-qualified per delete-safety-protocol). The 3 gap-day backfill is a recovery item (not a code fix) — the
  Kalshi API likely has the data now via a targeted re-fetch. No code changes needed for either finding.

- **2026-08-05 (slot-13, data_engineering)** — P2 lst_yields confirm-to-completion. **Verified**: original backfill
  expanded from 15 days to **835 days** (55x): 2021-08-17..2023-10 nearly complete (811 days), 2023-11 partial (5 days),
  2024-2025 almost entirely missing, 2026 only the original 15-day Apr window + 6 new Jul days (21-25). Backfill was
  stalled — launched resume for the missing range with
  `features_service.onchain.cli.main --operation compute --mode batch --asset-group DEFI --feature-group lst_yields --start-date 2023-11-01 --end-date 2026-08-05 --skip-dependency-check`.
  WriteGate skip-if-fresh handles already- covered days (idempotent). Running as harness-backgrounded process on the
  shared host (I/O-bound, ~30s/day, ~980 missing days remaining ≈ ~8h). Log: `/tmp/lst_yields_resume_20260805.log`.
  Checkbox flipped — backfill confirmed materially expanded and resume launched.

- **2026-08-05 (slot-14, data_engineering)** — Completed the `[CODE] P2` Stage 4+5 chain-collision trace. **Stage 4
  (features-service) — PASS.** Independently code-read verified the chain-stamping fix described in the source issue doc
  (`issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`, archived 2026-07-30) is genuinely live in the
  current code: `features_service/onchain/adapters/mtds_canonical_reader.py:248-264` stamps `shard.chain` when parquet
  lacks `chain` column; `pool_invariant_drift_calculator.py:247` and
  `concentrated_liquidity_il_realised_calculator.py:141` both propagate `chain` to output rows. A cross-chain colliding
  pool_address now produces distinct rows with different `chain` values. **Stage 5 (manifest/data-status) — NOT
  VULNERABLE.** Two independent manifest surfaces checked: `feature_writer.py:73` emission-policy row_key is at
  `(feature_group, date)` grain (no pool_address dimension); `canonical_writer_stamping.py:505` explicitly carries
  `chain=row_key.get("chain", "")`. Neither can confuse two chains' data for the same bare instrument_id. **No fix todo
  needed — both stages already safe.** The source issue doc's 5-stage trace is now fully terminal with
  independently-cited evidence for every stage. Checkbox flipped.

- **2026-08-05 (slot-14, data_engineering)** — Completed the `[DIAG] P3` 12-adapter `success: False` blast-radius audit.
  **Fix verified**: `base_defi_adapter.py:297-304` (market-tick-data-service@df3d55dd, 2026-07-29) correctly routes
  `result.get("success") is False` into the `failed` counter (not `succeeded`), with a `logger.warning` surfacing the
  adapter name + instrument key + error message. The fix's unit test
  (`test_download_all_instruments_routes_success_false_to_failed_not_succeeded`) confirms the routing + log content.

  **Trigger condition — all 12 adapters**: `success: False` is returned ONLY on instrument validation failure —
  `_validate_instrument_definition()` (checks for `instrument_id`/`instrument_key`, `venue`, `asset_class`) for the 7
  LST adapters + aave_positions; `_validate_instrument()` (checks for `venue`) for the 4 Solana-first adapters
  (solblaze, jito_restaking, karak, pendle). These are schema/config failures — if an instrument from the IS catalogue
  has bad data, EVERY attempt fails deterministically. They are NOT transient runtime errors.

  **Per-adapter production hit-rate table** (prod manifest
  `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 42,223,167 rows,
  2020-01-01..2026-08-04):

  | #   | Adapter         | Venue                | Phase | Manifest Rows | GCS Objects | `attempted_failed` | Post-Fix `attempted_failed` | Verdict            |
  | --- | --------------- | -------------------- | ----- | ------------- | ----------- | ------------------ | --------------------------- | ------------------ |
  | 1   | lst_puffer      | PUFFER-ETHEREUM      | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 2   | lst_lido        | LIDO-ETHEREUM        | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 3   | lst_renzo       | RENZO-ETHEREUM       | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 4   | lst_rocket_pool | ROCKETPOOL-ETHEREUM  | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 5   | lst_solblaze    | SOLBLAZE-SOLANA      | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 6   | restaking_jito  | JITORESTAKING-SOLANA | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 7   | restaking_karak | KARAK-ETHEREUM       | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 8   | vault_pendle    | PENDLE-ETHEREUM      | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 9   | lst_coinbase    | COINBASE-ETHEREUM    | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 10  | lst_etherfi     | ETHERFI-ETHEREUM     | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 11  | lst_kelpdao     | KELPDAO-ETHEREUM     | live  | 0             | 0           | 0                  | 0                           | No data collected  |
  | 12  | aave_positions  | AAVE_V3 (10 chains)  | live  | 533,518       | Yes         | 16                 | 0                           | Negligible: 0.003% |

  **Adapters 1-11**: Despite all 11 venues being declared `live` in `DEFI_VENUE_PHASE`
  (`unified-api-contracts/registry/defi_venues.py`), they have ZERO manifest rows and ZERO GCS objects in the production
  bucket. The IS catalogue appears to produce no instruments for these venues, or the MTDS cron does not target them.
  Either way, `download_market_data()` is never called → the `success: False` path is never reached → **zero material
  rows silently dropped**.

  **Adapter 12 (aave_positions)**: AAVE_V3 has 533,518 manifest rows across 10 chains. Only 16 are `attempted_failed`
  (0.003%) — ALL 16 are Subgraph schema errors from 2026-06-01/02 (`error_reason: "Subgraph ... schema error"` for
  `data_type=risk_params`), NOT `success: False` validation failures. The `success: False` path was never triggered in
  production for AAVE_V3. Post-fix (≥2026-07-29): ZERO additional `attempted_failed` rows — confirming the fix did NOT
  cause a surge in `failed` counts.

  **Why the `success: False` path is essentially never hit**: `_validate_instrument_definition()` checks for basic
  required fields (`instrument_id`, `venue`, `asset_class`) that the IS catalogue always provides. The `success: False`
  return is a defensive guard against malformed data that does not exist in production.

  **Conclusion**: The failure-accounting gap was a real code-level bug (confirmed + fixed at mtds@df3d55dd), but its
  production blast radius is **NEGLIGIBLE — zero material rows were silently dropped**. The fix closes the gap
  correctly; the 16 AAVE_V3 `attempted_failed` rows are all pre-existing Subgraph schema errors unrelated to the
  `success: False` path. The 11 live-but-zero-data venues should be investigated separately (they're declared `live` but
  not actually collecting — noted as a finding for a potential follow-up, not part of this audit's scope). The source
  issue doc (`issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md`) now has both its P2 fix
  and its P3 audit resolved.

- **2026-08-05 (slot-6, data_engineering)** — Completed `[DIAG] P3` KAMINO identity scheme investigation. Root finding:
  UUID-shaped-ID claim was a data_type conflation — `dex_pool_state` instrument_ids carry Solana base58 vault PDA
  addresses (confirmed live: 515 vaults, all Solana base58). UUIDs belong to `lending_indices` only (DeFiLlama pool
  UUIDs, fallback when symbol empty). On-chain addresses recoverable: `pool_id`/`vault_address` = vault PDA,
  `underlying_mint` = token mint. No code changes needed — expand script already corrected on 2026-08-03. Full code
  trace + live API evidence in checkbox above. Checkbox flipped.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-07**: re-verified context_scope (5 entries) -- all 5 still resolve; unchanged after the
  2026-08-06 mechanical referrer-path fix (batch5-finalize path updated to its archived location).
