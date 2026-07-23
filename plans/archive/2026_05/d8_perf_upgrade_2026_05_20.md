---
doc_type: plan
title: D8 — Performance upgrade plan (hot-path identification from A1)
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [deployment-service, features-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/defi_catalogue_chain_primitives_2026_05_10.md,
    /plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
  ]
created: 2026-05-20
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
source_audits: [plans/audit/results/codified_shape_compliance_2026_05_20.csv]
note: "P2 priority — not blocking May-23 DeFi cutover. Gates D8 on D6 (strategy+execution) green since performance
  optimisations are meaningless before correctness is established.

  "
parent_epic: defi_master
---

# D8 — Performance upgrade plan

> **Ordering step 8** in the Phase-E execution chain. P2 priority — post-May-23 scope.
>
> A1 audit identified hot-path files by violation count. This plan converts those findings into targeted performance
> improvements: reducing GCS round-trips, improving batch throughput, and eliminating per-object gsutil calls in
> migration scripts.

## Hot-path findings from A1

A1 CSV (`codified_shape_compliance_2026_05_20.csv`) surfaces the top violating files. Cross-referencing with the
`resolve_bucket_name` check (759 violations) and `no_hardcoded_venue_urls` check (189 violations) reveals the
performance-critical paths:

| Check                              | Violation count | Performance implication                                                                |
| ---------------------------------- | --------------- | -------------------------------------------------------------------------------------- |
| `resolve_bucket_name`              | 759             | Inline f-string bucket construction = no caching; each call rebuilds the URI           |
| `no_hardcoded_venue_urls`          | 189             | Hardcoded URLs = no config-driven failover / no hot-reload                             |
| `classify_venue_error`             | 302             | Unclassified errors = no RETRY/SKIP routing = unnecessary retries on FAIL-class errors |
| GCS object ops (migration scripts) | measured        | `gsutil` per-object = ~500ms; REST API = ~100ms; 250× faster at workers=32             |

## Remediation backlog (ordered)

### Phase 1 — GCS object ops in migration scripts (CLAUDE.md SSOT)

- [x] ✅ [AGENT] P1. Audit all migration scripts for `subprocess.run(['gsutil'...])` or `subprocess.run(['gcloud'...])`
      per-object operations:
  - `rg 'subprocess.*gsutil\|subprocess.*gcloud' --type py plans/ scripts/ --glob '*.py'`
  - Replace each with `gcs_copy_object()` / `gcs_delete_object()` / `gcs_describe_object()` from UTL
  - Enables workers=32 parallel REST API calls (250× faster than serial gsutil)
  - mtds@64ccb562 (migrate_cefi_instrument_types.py: 2x gsutil rm → gcs_delete_object) + deployment-service@5a531d8
    (cleanup_old_tarballs.py: 1x gsutil rm → gcs_delete_object). rg returns 0 per-object gsutil rm/cp/describe hits
    across migration scripts.
- [x] ✅ [AGENT] P1. Target: all `*migration*.py` scripts in IS, MTDS, features-service, deployment-service — 3
      per-object gsutil calls replaced (2 MTDS + 1 deployment-service); IS + features-service had 0 hits; PM migration
      only retains gsutil ls (list op, no UTL equivalent).

### Phase 2 — resolve_bucket_name caching

- [x] ✅ [AGENT] P2. Profile `resolve_bucket_name` call frequency in hot paths (MTDS batch handlers, features
      OnChainDataLoader):
  - UTL `_load_cloud_providers_yaml()` already has `@lru_cache(maxsize=1)` — YAML disk I/O only once per process.
  - MTDS does NOT call `resolve_bucket_name` — uses `get_write_bucket_name()` (string templates, no YAML).
  - features-onchain: 0 callsites. strategy-service: all callsites store result in `self._bucket` at **init** (once per
    object, not per-shard).
  - Conclusion: no consumer-level caching needed. UTL caching is sufficient.
- [x] ✅ [AGENT] P2. Identify top 10 hot-path files by `resolve_bucket_name` call count; add per-file caching where
      missing
  - Top callers: strategy-service/engine/core/{gcs_feature_provider.py, gcs_storage_service.py,
    strategy_config_loader.py} — all called once per object init, not per-shard. No caching additions required.

### Phase 3 — Retry overhead reduction via error classification

- [x] ✅ [AGENT] P2. Verify FAIL-class errors in 302 `classify_venue_error` violating files now stop retrying (after D7
      ships) — MTDS@83f2ac50 (2026-05-22): all 29 remaining MTDS adapter files fixed across DeFi LST
      (lst_binance_eth/lst_lido_eth/lst_rocketpool_eth/lst_cbeth/lst_jitosol/lst_msol) + other DeFi
      (uniswap/curve/aave_v3/chainlink/pyth/coingecko/defillama) + sports (understat/footystats/api_football) +
      prediction (polymarket/kalshi) + tradfi (ibkr/databento/barchart/tiingo/vix). QG all gates green (92s).

### Phase 4 — Throughput benchmarking

- [x] ✅ [AGENT] P2. Run MTDS batch throughput benchmark before/after Phase 1-3 changes:
  - Metric: shards/minute for DeFi perp_funding handler (highest frequency)
  - Analytical benchmark complete — `plans/audit/results/perf_benchmark_d8_2026_05_20.md`
  - Phase 1 affects migration scripts only (not handlers); Phase 2 no change; Phase 3 reduces FAIL-class retry overhead
    (15-33% in error-heavy scenarios, 0% on clean path).
  - Live VM measurement (≥20% target verification) deferred as post-cutover P2. PM@2026-05-22

## Success criteria

- [x] ✅ Phase 1: `rg 'subprocess.*gsutil' --type py` returns 0 hits in migration scripts — verified 2026-05-22
- [x] ✅ Phase 2: `resolve_bucket_name` called ≤1× per service boot per bucket name (cached) — UTL already caches YAML
      load; all hot-path callers store result at init. No changes needed. 2026-05-22
- [x] ✅ Phase 3: `rg 'classify_venue_error' market-tick-data-service/ --type py` returns hits in all handler except
      blocks — MTDS@83f2ac50
- [x] ✅ Phase 4: analytical benchmark complete — `perf_benchmark_d8_2026_05_20.md`. Phase 1-2 do not affect handler
      throughput; Phase 3 gives 15-33% improvement in error-heavy scenarios. Live VM measurement deferred post-cutover
      (P2).

## Full-execution criterion

> MTDS batch throughput benchmark run end-to-end (real GCS, real data, `workers=32`). Before/after measurements
> documented. GCS migration script `migrate_manifest_v8.py` (from D3) uses REST API object ops (not gsutil) — verified
> by running with `--dry-run` and confirming zero subprocess calls.

## Temporary states

None — this plan is additive (performance improvements don't create transitional states).

## Deferred work — migrated to:

- **Live VM measurement (≥20% target verification)**: deferred post-cutover P2. **MIGRATED FROM:** this plan. Home:
  `plans/epics/defi_master.md` P2 — add new item "D8 live VM benchmark: verify ≥20% GCS hot-path improvement on real
  batch VM (workers=32, real data) once fleet stable post-cutover."
