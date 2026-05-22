---
name: d8-perf-upgrade-2026-05-20
title: D8 — Performance upgrade plan (hot-path identification from A1)
created: 2026-05-20
status: active
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
source_audits:
  - plans/audit/results/codified_shape_compliance_2026_05_20.csv # A1 hot-path data
related_plans:
  - defi_catalogue_chain_primitives_2026_05_10.md
  - live_pipeline_mtds_mdps_features_2026_05_08.md
note: >
  P2 priority — not blocking May-23 DeFi cutover. Gates D8 on D6 (strategy+execution) green since performance
  optimisations are meaningless before correctness is established.
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

- [ ] [AGENT] P2. Profile `resolve_bucket_name` call frequency in hot paths (MTDS batch handlers, features
      OnChainDataLoader):
  - If called per-shard (not per-service boot), add `@lru_cache(maxsize=None)` or module-level cache
  - UTL may already implement caching — verify before adding duplicate cache
- [ ] [AGENT] P2. Identify top 10 hot-path files by `resolve_bucket_name` call count; add per-file caching where missing

### Phase 3 — Retry overhead reduction via error classification

- [ ] [AGENT] P2. Verify FAIL-class errors in 302 `classify_venue_error` violating files now stop retrying (after D7
      ships):
  - D7 already fixed the DeFi retry loop and 7 CCXT adapters
  - Check remaining 295 violators (A1: 302 - 7 CCXT adapters fixed) in non-execution-service repos
  - Focus on MTDS adapters (high-frequency data fetchers) — unclassified errors = full retry backoff even on 400s

### Phase 4 — Throughput benchmarking

- [ ] [AGENT] P2. Run MTDS batch throughput benchmark before/after Phase 1-3 changes:
  - Metric: shards/minute for DeFi perp_funding handler (highest frequency)
  - Target: ≥20% improvement over pre-D8 baseline (driven by GCS ops speedup at workers=32)
  - Document results in `plans/audit/results/perf_benchmark_d8_2026_05_20.md`

## Success criteria

- [ ] Phase 1: `rg 'subprocess.*gsutil' --type py` returns 0 hits in migration scripts
- [ ] Phase 2: `resolve_bucket_name` called ≤1× per service boot per bucket name (cached)
- [ ] Phase 3: `rg 'classify_venue_error' market-tick-data-service/ --type py` returns hits in all handler except blocks
- [ ] Phase 4: benchmark report shows ≥20% throughput improvement for DeFi MTDS handler

## Full-execution criterion

> MTDS batch throughput benchmark run end-to-end (real GCS, real data, `workers=32`). Before/after measurements
> documented. GCS migration script `migrate_manifest_v8.py` (from D3) uses REST API object ops (not gsutil) — verified
> by running with `--dry-run` and confirming zero subprocess calls.

## Temporary states

None — this plan is additive (performance improvements don't create transitional states).
