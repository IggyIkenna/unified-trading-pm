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
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27.md,
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
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
---

# DeFi satellite AO batch 6 — 2026-07-30

**status: active — operator-approved and dispatching.** This batch was drafted autonomously by the scheduled
`ag_closeout_auditor`; frontmatter `status` has since been flipped to `active` (2026-07-30, confirmed by real backlog
dispatch of the todos below to worker slots) — this banner was stale (still read "draft — NOT dispatched") after that
flip and is corrected here (slot-14).

## Todos

- [ ] [DIAG] P3. Audit the 12 named DeFi adapters (lst_puffer, lst_lido, lst_renzo, lst_rocket_pool, lst_solblaze,
      restaking_jito, restaking_karak, vault_pendle, lst_coinbase, lst_etherfi, lst_kelpdao, aave_positions) for how
      often they actually hit their `success: False` path in production — grep logs/manifest for the affected venues
      over a real window — to gauge whether the now-fixed failure-accounting gap (market-tick-data-service@df3d55dd) has
      been silently dropping real rows, and anticipate the blast radius now that those results route to `failed` instead
      of `succeeded`. Repo: market-tick-data-service. Done when: a per-adapter hit-rate table is recorded with a stated
      verdict (material drop found / negligible) for each of the 12 adapters. Source:
      `issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md`

- [ ] [SCRIPT] P2. Grep every DeFi-touching repo (instruments-service, market-tick-data-service, features-service,
      market-data-processing-service) for local dict/constant declarations shadowing UAC Category-A data
      (`TOKEN_DECIMALS`, `CHAIN_GENESIS_DATES`, factory-address registries for Uniswap/SushiSwap/PancakeSwap/
      Curve/Aave/Compound etc.); per candidate determine whether UAC is consulted first (cascade) or the local value
      wins outright (override), and whether it currently matches UAC or has drifted. Mirror the
      `LENDING_PROTOCOL_DEPLOY_DATES` fix pattern (remove dead entries, keep+comment-justify genuine ones, add a
      shape-lock regression test) for anything found drifted. Repos: instruments-service, market-tick-data-service,
      features-service, market-data-processing-service. Done when: a written inventory of every shadow-copy site exists
      with a fixed/justified verdict for each, and any drifted site is corrected + regression-tested. Source:
      `issues/defi_broader_local_fallback_vs_uac_sweep_2026_07_27.md`

- [x] ✅ [CODE] P1. Fix `governance_adapter.py`'s swallowed-exception bug: `_fetch_subgraph_proposals`/
      `_fetch_snapshot_proposals` currently swallow real HTTP/network errors into an empty list instead of raising to
      `record_failed`. Repo: market-tick-data-service. Done when: both methods raise on a genuine transport error (only
      a real "no proposals" response short-circuits to empty), covered by a new unit test asserting the distinction,
      shipped via scoped `quickmerge.sh --agent --files`. Source:
      `issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` — market-tick-data-service@d74984b0 (fix
      d040d457 + a stale test fixed to match d74984b0). Both fetch functions now let a genuine transport error propagate
      (removed the `except (aiohttp.ClientError, OSError, ValueError): return []` swallow); a real 200+empty response
      still short-circuits to `[]` unchanged. `_fetch_both_sources` now uses
      `asyncio.gather(..., return_exceptions=True)` so a raise from one source doesn't leave the other task's exception
      unretrieved. New tests: unit coverage on `_fetch_subgraph_proposals`/`_fetch_snapshot_proposals` (genuine-empty vs
      HTTP-error vs connection-error), plus a `_process_protocol`-level test proving the error reaches
      `recorder.record_failed` (not `record_zero_rows`) and that genuine-zero-proposals is unchanged.

- [x] ✅ [DATA] P1. **DONE 2026-07-31 (slot-16, data_engineering)** — `market-tick-data-service@5c12c9e5`. Diagnose +
      ship a real fix for the TheGraph subgraph-cascade / "bad indexers" failure class across all 8 affected (protocol,
      chain) pairs: VELODROME_V2/OPTIMISM, UNISWAP_V3/OPTIMISM, PANCAKESWAP_V3/BSC, PANCAKESWAP_V3/ETHEREUM,
      UNISWAP_V4/ETHEREUM, UNISWAP_V2/ETHEREUM, AERODROME_V3/BASE, UNISWAP_V3/POLYGON.

      **Confirmed via code read**: the fail-fast classification fix (`_is_bad_indexers_error`/
                  `_SubgraphIndexerUnavailableError`, `market-tick-data-service@74cd6cfd`, verified ancestor of current HEAD) is
                  generic (operates on the raw GraphQL error message, not per-protocol) and already structurally covers all 8
                  pairs via the shared `_run_cascade`/`_execute_subgraph_query` code path — every pair correctly routes to
                  `record_failed` (attempted_failed, retriable), never a misleading schema-drift reason.

                  **Shipped NEW this session**: a bounded retry-with-backoff (2 retries, exponential backoff + jitter, rotating
                  API key) for the "bad indexers" GraphQL-level fingerprint specifically — extends the existing HTTP-status retry
                  in `async_post_to_subgraph` to this GraphQL-level (HTTP-200) condition, per this todo's "retry-with-backoff"
                  ask. Extracted into `_retry_or_raise_bad_indexers()` in `_dex_swaps_queries.py` (kept `dex_swaps_handler.py`
                  under the 900-line file cap and the method under the 50-line cap). 2 new unit tests: retries-then-succeeds
                  (transient blip) and raises-after-retries-exhausted (persistent condition) — both patch `asyncio.sleep` to
                  stay fast/deterministic, mirroring the existing `test_execute_subgraph_query_retry_on_429_then_success` pattern.
                  Full `market-tick-data-service` `quality-gates.sh` green (280s, sentinel matches `d3956d8c`, rebased to
                  `5c12c9e5` on push — verified `git merge-base --is-ancestor` on origin).

                  **Live-probed all 8 pairs today (2026-07-31)** with the real production cascade queries (not just `_meta` —
                  the VELODROME_V2/OPTIMISM trap from 2026-07-28's investigation: `_meta` can read healthy while the actual
                  cascade query still fails):

                  - **VELODROME_V2/OPTIMISM**: SELF-HEALED — 3/3 identical successes on the production `messari_from` query,
                    1000 real swap rows each (page cap hit). Retry-fixable, no code fix needed; next backfill re-run converts.
                  - **UNISWAP_V3/OPTIMISM**: STILL persistently broken — reproduced the IDENTICAL "bad indexers" fingerprint
                    (same 3 indexer addresses `0xeccdf823.../0xf92f430d.../0xfeff9093...`) across 2026-07-27, 07-28, 07-30, and
                    now 07-31 (4+ days) — conclusively NOT transient, now clearly past the "multi-day window" bar the sibling
                    issue doc's P2 todo asked for. A bounded (seconds-scale) retry cannot resolve this class (deterministic
                    indexer-set enumeration, not random routing). Researched The Graph Explorer for a replacement deployment:
                    found candidate `EgnS9YE1avupkvCNj9fHnJxppfEmNNywYJtghqiu2pd9` ("Uniswap V3 Optimism"), confirmed currently
                    healthy via a live `_meta` probe — **NOT vetted** for schema compatibility with the existing univ3 cascade or
                    historical coverage depth, so NOT swapped into the UAC registry this session (a mis-vetted swap risks
                    breaking existing coverage). Filed as a follow-up todo below.
                  - **PANCAKESWAP_V3/BSC**: HEALTHY — 3/3 successful production-query attempts (genuine 0-swaps-that-day
                    answer, not an error). Matches the earlier-established self-heal verdict.
                  - **PANCAKESWAP_V3/ETHEREUM, UNISWAP_V4/ETHEREUM, UNISWAP_V2/ETHEREUM, AERODROME_V3/BASE, UNISWAP_V3/POLYGON**:
                    all HEALTHY via live `_meta` probe (fresh block, `hasIndexingErrors=false`).

                  **Before/after `attempted_failed` counts** (fresh prod manifest pull, `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`,
                  29,520,693 total rows, 2026-07-31, vs the 2026-07-28 snapshot in the sibling issue doc):

                  | pair                       | 2026-07-28 | 2026-07-31 | verdict                                          |
                  | -------------------------- | ---------- | ---------- | ------------------------------------------------- |
                  | VELODROME_V2/OPTIMISM      | 666        | 697        | +31 historical residue while broken; now healed    |
                  | UNISWAP_V3/OPTIMISM        | 360        | 445        | +85, still actively failing every attempt          |
                  | PANCAKESWAP_V3/BSC         | 15         | 24         | +9 residue; confirmed healthy now                  |
                  | PANCAKESWAP_V3/ETHEREUM    | 2          | 2          | unchanged, healthy                                 |
                  | UNISWAP_V4/ETHEREUM        | 12         | 15         | +3, healthy (unrelated to the tracked build_instrument_id sub-issue) |
                  | UNISWAP_V2/ETHEREUM        | 5          | 5          | unchanged, healthy                                 |
                  | AERODROME_V3/BASE          | 1          | 2          | +1, healthy                                        |
                  | UNISWAP_V3/POLYGON         | 2          | 2          | unchanged, healthy                                 |

                  Historical `attempted_failed` rows don't retroactively shrink (they're permanent unless explicitly
                  reclassified/re-backfilled) — the fix's real effect is forward-looking: future backfill attempts against the
                  7 now-healthy pairs should succeed instead of adding fresh rows; UNISWAP_V3/OPTIMISM will keep accumulating
                  until either it genuinely self-heals (evidence says unlikely) or the deployment-ID-swap follow-up lands.

                  Repo: market-tick-data-service. Sources: `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`
                  (todo 6), `issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md` (P2 re-probe item,
                  superseded by this broader fix).

- [ ] [DIAG] P2. **NEW, filed 2026-07-31 (slot-16)** — research + vet a replacement TheGraph subgraph deployment ID for
      UNISWAP_V3/OPTIMISM (currently `Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj`, confirmed persistently "bad
      indexers" across 4+ days as of 2026-07-31 — see the todo above). Candidate identified via The Graph Explorer:
      `EgnS9YE1avupkvCNj9fHnJxppfEmNNywYJtghqiu2pd9` ("Uniswap V3 Optimism"), confirmed currently healthy via a live
      `_meta` probe (2026-07-31) — NOT yet vetted for (a) schema compatibility with the existing univ3/univ3_minimal
      cascade queries, (b) sufficient historical coverage depth (the backfill needs data back to 2023-01-01), or (c) its
      own indexer-health stability over time before committing to a UAC registry swap. Done when: the candidate (or an
      alternative found via the same Explorer search) is verified on all 3 axes and either swapped into
      `unified_api_contracts/registry/capability_declarations/_defi.py`'s `SUBGRAPH_IDS["uniswap_v3"]["OPTIMISM"]` with
      a regression test, or rejected with a recorded reason and the next candidate tried. Repos: unified-api-contracts,
      market-tick-data-service. Source: this session's live-probe evidence above.

- [x] ✅ [DATA] P1. **SPLIT 2026-07-31 (slot-16, data_engineering)** — catalogue expansion half is DONE + VERIFIED (this
      todo's own scope, closed here); the denominator-recompute half is split into the new `[DATA] P2` todo below
      (deliberately NOT run inline this session — needs the same VM-dispatch pattern an existing operator- approved
      process already established for this exact class of large manifest write; see that todo for the full rationale +
      done-when). Execute the operator-ruled (2026-07-28) full-completion instruments-service DeFi pool catalogue
      expansion: a full historical-discovery backfill covering every ever-captured pool address for EVERY default DEX
      protocol (not just the 4 already sampled: curve/sushiswap/velodrome_v2/trader_joe_v2), then re-derive Honest
      Coverage's `expected_unattempted` denominator from the expanded catalogue. Cost pre-approved at the <$100 tier per
      the operator ruling — no fresh operator ask needed. Repo: instruments-service. Done when: the catalogue expansion
      is verified complete for all default DEX protocols and the denominator recompute is confirmed landed. Source:
      `issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md` (todo 2)

      **Catalogue expansion — DONE + VERIFIED.** Shipped `instruments-service@1fb9c490`
              (`scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py` + unit tests). **Single-walk discovery**: the
              MTDS availability manifest already stamps every address-keyed (catalogue-uncovered) historical capture's raw
              pool address as its own `instrument_id` — reading the manifest ONCE gets the identical "no catalogue-covered
              replacement" population the source issue's slower per-directory GCS-listing purge tool found, with zero fresh
              GCS walk. **Scope**: all 12 EVM default DEX protocols (UAC `SUBGRAPH_IDS` SSOT, `0x[hex]`-address-filtered,
              matching the reference purge tool's own regex) + ORCA/RAYDIUM/PHOENIX (Solana, base58-pubkey `instrument_id`,
              confirmed address-shaped by direct sampling). **KAMINO deliberately excluded** — its `dex_pool_state`
              `instrument_id` values are UUID-shaped (not a pool address), and its manifest rows also carry
              `lending_indices`/`solana_lending` instrument_types under the same venue — its capture-id semantics need a
              dedicated investigation before any value gets written into `pool_address` (see the new `[DIAG]` follow-up
              below). **Merge safety**: reused `build_instrument_catalogue.py`'s own tested
              `_merge_incremental(close_absent=False)` (the identical frozen-tail merge a `--mode full` rebuild uses) — purely
              additive, can only widen an existing pool's `available_from` or append a genuinely new one, never
              delist/shrink; `promote_catalogue`'s monotonic guard is the second independent safety net. **Result**: prod
              `instruments-store-defi-…/prod/catalog.parquet` went from **12,382 → 71,538 rows** (62,592 newly-discovered pool
              addresses across 28 (venue,chain) pairs — ORCA/SOLANA 14,103, SUSHISWAP/ARBITRUM 12,855, TRADER_JOE_V2/AVALANCHE
              9,611, UNISWAP_V3 (5 chains) 14,295 combined, BALANCER (6 chains) 6,652 combined, + 20 smaller pairs down to
              PHOENIX/SOLANA's 2). **Per-protocol completeness independently verified** (per the operator's explicit request
              to re-verify rather than trust a single earlier checkpoint — see incident note below): re-ran the full
              discovery+merge a SECOND time after the fix below landed — result was byte-identical (71,538 rows, "0 new
              listings", fully idempotent) — AND cross-checked every one of `dex_pools_handler.py`'s actual
              `_DEFAULT_PROTOCOLS` × supported-chains pairs against the discovery output: every pair either produced gap rows
              (genuine historical under-coverage now fixed) or has a documented zero-gap reason — CURVE/OPTIMISM (already the
              separately-fixed deindexed-subgraph case, `EXPECTED_SUBGRAPH_DEINDEXED`) and KAMINO (deliberately excluded,
              above). No default DEX protocol/chain pair was silently skipped.

              **Real incident during this work, root-caused + fixed (2026-07-31)**: an earlier invocation of this script left
              an ORPHANED process (PID 1033055) running for ~37 minutes past its own logical completion, growing to 43.6GB
              RSS (67% of host RAM) and causing a real fleet-wide agent-orchestrator outage (SQLite write-lock wedge, full
              API unresponsive ~15min, all slots blind) — reported directly by the operator, who SIGTERM'd it. I also found
              and killed a SECOND at-risk process from my own follow-up investigation (a scan-only
              `enumerate_expected_universe.py` run already at 19.6GB RSS and climbing on a host with only 12GB free + 14GB
              swap in use) before it could cause a repeat. **Root cause (my script, confirmed by re-test)**: `pd.read_parquet`
              loaded the FULL ~50-column manifest schema for all 29.5M+ rows when only 6 columns are ever used — the dominant
              memory cost, independent of the ~60K-row output the script actually produces (same "cost dominated by the
              unfiltered read, not the worklist size" shape as
              `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`'s `ManifestWriter` legacy-path finding,
              though NOT the same underlying mechanism — that one was an unset `per_vm_shards=True`; this one never touches
              `ManifestWriter` at all, it's a raw `pd.read_parquet` column-pruning miss). Separately, the ORIGINAL orphaned
              37-minute run strongly suggests something (unconfirmed which dependency) kept a background thread/connection
              alive past `main()`'s own return. **Fixed**: (1) `pd.read_parquet(..., columns=[...])` restricted to the 6
              columns actually used, plus explicit `del manifest`/`del manifest_bytes` once each is no longer needed; (2)
              `os._exit(code)` instead of `sys.exit(code)` at the very end — forces immediate process termination, skipping
              interpreter teardown, so no lingering non-daemon thread can hold the process open (safe here since every write
              the script performs has already completed and returned by that point). **Re-verified safe**: re-ran the full
              script under a hard `ulimit -v 20971520` (20GB) cap — completed in <1 minute, confirmed the process fully exits
              (absent from `ps aux` immediately after the wrapping shell reports completion, unlike the original run).

- [ ] [DIAG] P3. **NEW, filed 2026-07-31 (slot-16)** — investigate KAMINO's `dex_pool_state`/`lending_indices` capture
      identity scheme (UUID-shaped `instrument_id`, not a Solana pool address) before it can be included in the DeFi
      pool catalogue expansion above. Determine what the UUID actually references (a vault/reserve id? an internal
      capture-run id?) and whether KAMINO's on-chain pool addresses are recoverable from a different manifest field or
      need a fresh subgraph/RPC lookup. Small blast radius (1,403 manifest rows total for KAMINO's `dex_pool_state` as
      of 2026-07-31). Repo: market-tick-data-service (capture-id scheme), instruments-service (catalogue entry once
      resolved).

- [ ] [DATA] P2. **NEW, filed 2026-07-31 (slot-16)** — the denominator-recompute half of the todo above: re-run
      `enumerate_expected_universe.py --asset-group defi --apply-write` against the now-expanded catalogue (71,538 rows)
      to re-derive Honest Coverage's `expected_unattempted` for the 62,592 newly-catalogued pool addresses.
      **Deliberately NOT run inline this session** — a scan-only measurement (zero writes) already showed the write
      volume exceeds the enumerator's own 1M-row halt-safety cap, and this exact recompute mechanism is ALREADY governed
      by a standing, operator-approved process in `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (Option A,
      full apply approved 2026-07-10, executed as year-chunked SPOT VM launches via the registered
      `launch-expected-universe-v2-vm.sh` — that same doc's own hard-won lesson: a full unbounded run on even
      `e2-standard-16` (64GB) OOM-killed, "this workspace's own established pattern for large data ops is VM-dispatch,
      not foreground/background laptop execution"). Per that doc's own established precedent, organic catalogue growth
      driving a proportional backlog increase is treated as a RESUMPTION of the existing Option-A approval, not a
      new-scale decision requiring fresh operator sign-off — so this does not need a fresh ask, but it DOES need the
      same VM-dispatch, chunked execution this class of write already requires. Done when: the recompute is dispatched
      via the established launcher (year-chunked or scoped to the actual new pool-address delta, whichever the executor
      determines is more efficient), verified landed (fresh scan-only count drops to ~0 new candidates for the
      62,592-address delta), and the data-status defi denominator refreshes. Repo: instruments-service,
      deployment-service (VM launch). Source: this todo's own "Done when" bar (denominator-recompute half),
      cross-referenced against `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`.

- [ ] [DATA] P2. Execute the pre-2026-07-22 `gas_fees` historical venue-prefix migration, steps (a)+(b) only: (a) a
      bounded per-venue scoping measurement (volume/date-range) across the 14 legacy `venue=<CHAINNAME>` prefixes (12
      EVM chains + SOLANA + BITCOIN); (b) copy each legacy-prefixed object to `venue=ALCHEMY` (chain= preserved) and
      manifest-verify each of the 14 prefixes. Do NOT execute the legacy-prefix delete (step c) — stage the 5-part
      delete-safety proof but leave the actual prod-bucket delete for a separate `[OPERATOR]`-gated todo. Repo:
      market-tick-data-service. Done when: all 14 prefixes are copied to `venue=ALCHEMY` and manifest-verified, with the
      delete-safety proof staged (not executed) and cited. Source:
      `issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md`

- [ ] [DIAG] P2. Root-cause the KALSHI_PERP capture gap's two residual findings: (a) the 3 zero-object gap days inside
      the capture window (2026-07-17, 2026-07-20, 2026-07-21); (b) the daily `_migrated_kalshi_perp_<timestamp>.parquet`
      marker object that appears 2026-05-29..2026-07-16 then stops. Repo: market-tick-data-service. Done when: both
      findings have a recorded root-cause verdict (transient outage / code bug / expected behavior change), with a
      follow-up fix todo filed if either is a real bug. Source:
      `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` (DIAG items, not the already-covered
      re-emit-under-cefi item)

- [ ] [DATA] P1. Execute the non-destructive fold for all 5,332 legacy pre-canonical composite-venue objects (9 venues,
      ~20-month window 2024-05-02..2026-01-24): parse each object's own `instrument_key`/`data_type` parquet columns to
      derive the correct canonical hive path
      (`venue={venue}/chain={chain}/instrument_type={type}/data_type={dt}/     {instrument_id}.parquet`), copy to that
      path, verify content parity, then register a `record_captured` manifest row per folded object — following the
      proven 2026-07-21 dex_pools/lending_indices fold recipe. Legacy objects stay un-deleted/unregistered; deletion is
      a separate, later-gated todo. Repo: market-tick-data-service. Done when: all 5,332 objects are folded +
      manifest-registered, verified via a post-fold count check. Source:
      `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (todo 1)

- [ ] [DATA] P2. Confirm-to-completion the already-launched `lst_yields` historical feature backfill
      (`features_service.     onchain.cli.main --mode batch --asset-group DEFI --feature-group lst_yields --start-date 2021-08-17 --end-date     <today>`,
      launched 2026-07-28 slot-6 as a chunked 60-monthly-subrange supervisor run) — verify against `gcloud storage ls`
      on `onchain/by_date/*/feature_group=lst_yields/` that day-partitions now span materially more than the 15 days
      recorded at launch time, targeting near-full per-token-genesis coverage, and confirm a corresponding drop in the
      STAKING leg's honest-absence log rate for `carry_staked_basis`. If the run has stalled, resume it (do not replay
      from `2021-08-17`). Repo: features-service. Done when: the stated done-when criterion from the source doc is met
      and cited. Source: `issues/defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md`

- [ ] [CODE] P2. Register `perp_daily_ctx` as its own canonical `data_type` + `SchemaContract` under
      `DATA_TYPES_BY_ASSET_GROUP["defi"]` (mirroring `DEFI_PERPETUAL_PERP_FUNDING`); add manifest writes to both ad-hoc
      writers (MTDS HL mark-price backfill script, features-service `perp_funding_corpus.py`) with unchanged row schema;
      backfill manifest rows for the already-migrated historical (venue, data_type, day) shard tuples. Confirmed
      unblocked for the named HYPERLIQUID/CeFi combos — no operator sign-off needed for this specific defi-key-only
      registration. Repos: unified-api-contracts, market-tick-data-service, features-service. Done when:
      `perp_daily_ctx` resolves as a registered data_type end-to-end and historical shards show manifest rows. Source:
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` (CODE item, not the separately-tracked
      operator-decision item)

- [ ] [CODE] P2. Wire real capture for AAVE-PLASMA and FLUID-PLASMA: (1) add `CHAIN_CONFIGS[9745]` Alchemy RPC template
      to unified-api-contracts' `capability_declarations/_defi_chain_data.py`; (2) add Aave V3 Plasma POOL/DATA_PROVIDER
      addresses to market-tick-data-service's `lending_indices_handler.py` `_AAVE_V3_POOL_ADDRESSES`/
      `_AAVE_V3_DATA_PROVIDER_ADDRESSES` (re-derive fresh from aave-address-book at implementation time, do not trust
      the source doc's transcription); (3) spot-check `FluidAdapter`/`fluid_liquidity_resolver.py` accept
      `chain='PLASMA'` without Ethereum-only hardcoding; (4) verify real rows land in the manifest and flip
      `defi_venues.py`'s phase from `pipeline` to `live` for verified venues. FLUID-PLASMA additionally needs its launch
      date confirmed before its `PROTOCOL_LAUNCH_DATES` entry can land — AAVE-PLASMA is unblocked and can ship
      independently if FLUID's date isn't resolved in time. Repos: unified-api-contracts, market-tick-data-service. Done
      when: at least AAVE-PLASMA shows real captured rows in the manifest with `defi_venues.py` phase flipped to `live`.
      Source: `issues/defi_plasma_chain_onboarding_gap_2026_07_26.md`

- [ ] [CODE] P2. Trace Stage 4 (features-service) and Stage 5 (manifest/data-status) for the bare-`instrument_id`-only
      chain-collision keying gap — the SAME bug class already fixed at Stage 2 (MTDS, per
      `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s todo 3) and confirmed moot at Stage 3 (MDPS). Neither Stage 4
      nor Stage 5 has been independently traced by any audit pass to date. Repo: features-service (Stage 4),
      unified-trading-pm/deployment-api (Stage 5, data-status). Done when: both stages have a recorded pass/fail verdict
      with cited evidence, and a fix todo filed for either if collision-vulnerable. Source:
      `issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`

- [ ] [DIAG] P1. Root-cause why the live daily `collect-perp-funding` Cloud Scheduler job (market-tick-data-service,
      `defi_collection_scheduler.tf:112`, 01:15 UTC) produces zero MTDS manifest rows for `perp_funding` across every
      one of 12 tested days (2026-05-01..2026-07-28), despite `perp_funding_handler.py` resolving the correct canonical
      bucket and a historical 12,500-captured-row count. This is the sole live blocker keeping
      `data_pipeline_check_mdps_features_2026_07_20.md`'s DEFI:onchain dependency-check gate permanently closed. Repo:
      market-tick-data-service. Done when: root cause is identified and either fixed or filed as a scoped follow-up with
      the specific broken link named. Source:
      `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`

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

- [ ] [SCRIPT] P1. Pause the MTDS manifest-consolidator cron, run
      `restamp_lending_instrument_type_2026_07_24.py --apply` (after its own dry-run + pre-apply snapshot), verify
      post-write output, resume the cron. No longer operator-gated per the 2026-07-28 CLAUDE.md ruling on this class of
      action. Then confirm the distinct-values panel (`GET /distinct-values/defi`) no longer badges `liquidation` as
      non-canonical for this writer path, cross-link the result into the archived parent audit plan's Progress Log, and
      close out the source plan. Repo: market-tick-data-service, deployment-api. Done when: the restamp is applied +
      verified and the distinct-values panel confirms the fix, both cited in the source plan. Source:
      `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md` (todos 4-5, sequential)

- [ ] [TEST] P2. Add a regression test asserting `load_pool_metadata_for_date` resolves a blob written under EITHER the
      pre-cutover flat shape OR the post-cutover hive shape (two fixture cases), guarding against future path-grammar
      regressions. Then remediate the ~4 days (2026-07-23 onward) of already-written dishonest `record_zero_rows`
      manifest stamps for morpho/fluid/kamino_lending `risk_params`: identify affected manifest rows, reclassify, and
      re-run/verify end-to-end (reversibility-cleared per finding T — executable as a full dispatch, not just a
      proposal). Repo: market-tick-data-service. Done when: the regression test is green and the ~4 days of dishonest
      stamps are reclassified + re-verified. Source:
      `issues/mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` (todos 6-7)

- [ ] [DATA] P2. Investigate the 6 `lending_indices` `record_empty(SOURCE_RETURNED_ZERO)`/FetchEvidence guard rejections
      (MORPHO x2, COMPOUND_V3 x4, dated 2026-07-26) — determine whether the guard is correctly blocking a genuine
      upstream problem or wrongly rejecting a legitimately-empty day, then fix the root cause. Separately investigate
      `dex_pool_state`'s 19 `build_instrument_id` errors: identify which venue/instrument shapes fail id construction,
      then fix. Repo: market-tick-data-service. Done when: both investigations have a recorded root-cause verdict, with
      a fix shipped for each if warranted. Source: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (2 DATA items)

- [ ] [SCRIPT] P3. Retry the 2 `lst_rates` 429-rate-limited cells (trivial). Then wire up the disabled
      `shard_exists_prefix` skip-if-captured hook across every DeFi handler (`oracle_prices_handler.py`,
      `lst_rates_handler.py`, `dex_pools_handler.py`, `perp_funding_handler.py`, etc.) so date-range re-runs become
      incremental instead of unconditionally re-fetching/re-writing the whole range — wire the caller into
      `service_framework/_adapter.py`'s `_drive_serial`/`_drive_concurrent` loop. Repo: market-tick-data-service. Done
      when: the 2 cells are retried and captured, and the skip-if-captured hook is wired + verified on at least one
      handler with a regression test. Source: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (2 SCRIPT items)

- [ ] [DIAG] P3. Delete the 916 HYPERLIQUID + 642 ASTER redundant legacy `defi`/`perp_funding` rows and rebuild the defi
      index; separately, relax RULE 11 (`_EXTRA_LIVE_PROBE_SOURCES_BY_AG`) to cover cefi CEX venues and re-run the
      phantom-row auditor. Both items were operator-RULED AO-ready on 2026-07-28 (postdating
      `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s earlier BLOCKED-OPERATOR-DECISION classification of this same
      doc — the ruling supersedes that deferral for these 2 items specifically; the HYPERLIQUID k-prefix coin-case
      question in the same doc remains genuinely design-gated and stays deferred below). Repo: market-tick-data-service
      / deployment-api (index rebuild). Done when: both operator-ruled actions are executed and verified. Source:
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`

- [ ] [SCRIPT] P2. Project every bare `read_availability_index()` call site to actual column usage across: unified-
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
      `issues/read_availability_index_bare_defi_callers_2026_07_27.md`

- [ ] [INFRA] P3. Bump the defi-specific default manifest-recon VM machine type to 32Gi+/8vCPU-equivalent (or move to a
      Cloud Run job mirroring `cf_manifest_audit_scheduler.tf`'s provisioning) instead of relying on the ad-hoc per-run
      `MACHINE_TYPE` override. Add a lighter-weight, column-pruned read path to
      `merge_canonical_with_outstanding_shards` (or a scoped sibling helper) for verification/dry-run-only callers that
      don't need the full wide-schema materialization. Repos: deployment-service, instruments-service,
      unified-trading-library. Done when: the manifest- recon VM/job runs on adequate provisioning and a column-pruned
      read path exists for dry-run callers. Source:
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
- `issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` — building 6 genuinely new instruments-service
  reference-data adapters is a substantial new-build the doc's own 2026-07-30 section recommends spinning up as its own
  dedicated multi-todo plan, not a single batch todo — an authoring/prioritization decision.
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
`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (+finalize),
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
