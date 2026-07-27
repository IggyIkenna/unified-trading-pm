---
doc_type: issue
title:
  "MDPS candle-manifest coverage is near-zero corpus-wide for cefi/defi/tradfi/prediction — 0.1-2.3% of
  processed_candles/ objects have a manifest row under either vocabulary; sports is the sole outlier at ~100%"
summary: >-
  First-ever full-corpus run of the new candle_orphan_sweep.py tool (todo 1 of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md), executed on real prod GCS + manifest data via 4
  Tier-2 SPOT VMs (cefi/defi/tradfi/prediction). Found near-total absence of `record_captured` manifest coverage for the
  MDPS processed_candles/ corpus: cefi 460/405,956 objects manifested (0.11%), tradfi 4,388/541,322 (0.81%), prediction
  13,281/583,228 (2.28%), defi 0/1,131,367 (0%). Sports (bounded 200-object sample, not yet full-corpus) showed 100%
  coverage, the opposite pattern. This is far larger in scope than todo 7's already-fixed self-referential emission-gate
  lockout (which targeted only the trades-sourced ohlcv_1m/ohlcv_1h/book_snapshot_5 family) — this gap spans EVERY
  data_type/timeframe combination observed, across 4 of 5 asset_groups.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, mdps, candle, manifest-completeness, orphan-real, honest-absence, big-finding]
related:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/active/issues/mdps_candle_orphan_sweep_design_brief_2026_07_27.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-07-27 (slot 9) running the first full-corpus validation of the newly-shipped candle_orphan_sweep.py tool
  (market-data-processing-service@d921823 + deployment-service@d75e8f3/@ff8eebe), via 4 real Tier-2 SPOT VMs, per main's
  ruling on BLK-c8936baa (this VM-launch was read-only/safe-idempotent/AO-eligible without operator gate).
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# MDPS candle-manifest coverage is near-zero corpus-wide (cefi/defi/tradfi/prediction)

## What I found

Ran the new `candle_orphan_sweep.py` (A/D/E/F taxonomy, dual-vocabulary manifest-coverage join — see the design brief)
on real prod data via 4 Tier-2 SPOT VMs (`canonical-migration-{cefi,defi,tradfi,prediction}-candle-orphan-sweep-*`,
`e2-standard-8`, all completed in <2 min each, no preemption). Real, measured results:

| asset_group | A (canonical_manifested)                      | E (orphan, post-cutover) | F (ambiguous, pre-cutover) | coverage % |
| ----------- | --------------------------------------------- | ------------------------ | -------------------------- | ---------- |
| cefi        | 460                                           | 0                        | 405,496                    | 0.11%      |
| defi        | 0                                             | 7,936                    | 1,123,431                  | 0.00%      |
| tradfi      | 4,388                                         | 0                        | 536,934                    | 0.81%      |
| prediction  | 13,281                                        | 0                        | 569,947                    | 2.28%      |
| **sports**  | 200 (bounded 200-obj sample, not full corpus) | 0                        | 0                          | **100%**   |

`--manifest-fix-cutover 2026-07-27` (today) was passed for every run, so the acceptance-bar metric (class E) reads 0 for
cefi/tradfi/prediction — but that is an artifact of the cutover classifying every pre-existing miss as (F) ambiguous
rather than a genuine "no gap" result. DeFi's 7,936 E-count proves the gap is NOT fully historical — objects written
strictly AFTER today's cutover are still landing with zero manifest coverage for DeFi specifically.

**Verified this is a real manifest absence, not a matching-logic bug** in the new sweep tool: spot-checked cefi's live
`_index/availability_index.parquet` directly (8,779,029 total rows) — `service_name == "market-data-processing-service"`
returns only **75 rows total** for the entire cefi bucket, with zero rows for `venue=DERIBIT` at all (the exact object
the sweep flagged). The sweep's `is_covered()` dual-vocabulary check (source `data_type` + `mdps_data_type_key()`
aggregated form) had nothing to match against — there is no row to find under either vocabulary.

**Why this differs from `candle_feature_canonical_path_divergence_2026_07_20.md` todo 7**: that fix
(`market-data-processing-service@caa995c`) targeted ONLY the trades-sourced, self-referentially-gated
`ohlcv_1m`/`ohlcv_1h`/`book_snapshot_5` family, and only the emission-GATE bug for NEW writes going forward. This gap
spans every `data_type` observed in the sweep (`derivative_ticker`, `trades`, `dex_pool_swaps`, plus whatever else
populates the remaining ~1M+ F-classified objects per AG) and clearly predates and postdates the fix — DeFi's
`dex_pool_swaps` path was explicitly named as OUT of todo 7's scope ("does NOT touch DEFI's dex_pool_swaps candle path —
policy resolver returns None, skips the gate entirely"), yet DeFi shows 0% coverage here, the worst of the four. This
means todo 7's fix, while correct for its narrow target, did not touch the actual root cause of `record_captured` never
being called for the vast majority of candle-writing code paths.

**Sports is the outlier** — its manifest DOES carry rows keyed with `timeframe` populated correctly (confirmed via
direct inspection, 157,527 mdps rows for sports alone vs. 75 for ALL of cefi). Whatever `record_captured` wiring
sports's candle writer has, cefi/defi/tradfi/prediction's candle writers evidently lack (or call it on a
disjoint/incompatible key that never lands as `service_name="market-data-processing-service"`,
`capture_status= "captured"` for these AGs).

## Why it matters

This is squarely the "data-pipeline correctness is the heartbeat" HARD RULE — a near-total absence of manifest coverage
for a major data corpus (processed_candles/) means the manifest can answer none of the standard questions (is this shard
captured? complete? stale?) for candle data across 4 of 5 asset_groups. Any downstream consumer that trusts
`capture_status="captured"` as the completeness signal for candles is silently blind to ~1.1-2.2M objects' worth of
real, on-disk data per asset_group. This is the "silent-write / manifest-completeness bug the operator fears as a v10
trigger" that `migration_orphan_sweep.py`'s own module docstring names as the reason CF-17 exists — just surfaced for
the candle layer instead of raw-tick.

## Recommended decision

- [ ] [DIAG] P0. **Root-cause why `record_captured` is never reached (or never lands under a matching key) for the MDPS
      candle writer across cefi/defi/tradfi/prediction**, contrasted against sports's working wiring. Check
      `market-data-processing-service/market_data_processing_service/app/core/candle_write_mixin.py` +
      `canonical_writer.py`/`canonical_writer_stamping.py` (the same files todo 7's `caa995c` fix touched) for whether
      the emission-gate / manifest-write call is even reached for non-sports asset_groups, or whether it's reached but
      silently swallowed (todo 7 also fixed a swallowed-exception path — check whether that fix's
      `record_failed_for_shard` addition is actually catching anything now, or whether the failure is upstream of that
      try/except entirely).
- [ ] [DATA] P1. **Once root-caused, scope + execute the historical backfill** for cefi/defi/tradfi/prediction's ~2.6M
      total F-classified (+7,936 E-classified for DeFi) unmanifested candle objects via `record_captured`-only backfill
      (never delete — mirrors `backfill_orphan_class_e.py`'s precedent). Given the scale (~1.1M for DeFi alone), this is
      its own VM-launch campaign, not an in-session fix.
- [ ] [DATA] P2. **Complete the sports full-corpus sweep** (only a bounded 200-object sample has been run) to confirm
      the ~100% coverage pattern holds across sports's entire historical corpus, not just a recent-day sample.
- [ ] [REVIEW] P2. Cross-check whether `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s narrower
      CEFI-only scope (3 known venues, one known day, "corpus-wide extent unknown") is now superseded by this
      corpus-wide measurement — likely yes, this doc should probably fold into or supersede that one once the backfill
      scope is finalized.

## Progress Log

- **2026-07-27** (AO dispatch, slot 9) — Filed while running the first full-corpus validation of
  `candle_orphan_sweep.py` (todo 1 of `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`). Real numbers
  captured above from 4 completed Tier-2 SPOT VM runs against live prod data; spot-verified the cefi gap directly
  against the live manifest (not a tool artifact). Did not attempt the backfill (P1) — out of scope for this dispatch
  and a real infra decision (~2.6M-row scale) that deserves its own scoped campaign.
