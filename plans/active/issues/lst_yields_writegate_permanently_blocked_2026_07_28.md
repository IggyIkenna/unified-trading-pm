---
doc_type: issue
title:
  "lst_yields (and sibling lst_native_rates) feature writes were 100% blocked, every day, by two independent bugs —
  found + fixed while executing the coverage-extension backfill"
summary: >-
  While executing the backfill scoped in `defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md`, every
  historical day attempted (including 2026-04-10, a day inside the ALREADY-SUCCESSFUL original 15-day window) failed to
  write any output. Root-caused to two independent, unrelated bugs in `features-service/features_service/onchain/
  engine/lst_features.py` that together made `lst_yields` (and the sibling `lst_native_rates` feature group, same code
  path) permanently unwritable as of current `live-defi-rollout` HEAD — not a historical-data-specific issue, a live P0
  gap feeding `carry_staked_basis`'s STAKING leg. Both fixed in this same session; fix verified via real GCS writes.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [defi, lst_yields, lst_native_rates, writegate, emission-policy, data-correctness, carry_staked_basis, bugfix]
related:
  [
    /plans/active/issues/defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
source:
  [data_engineering slot-6, 2026-07-28, discovered while executing defi_lst_yields_coverage_extension_gcs_verified-001]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# `lst_yields` WriteGate/emission-policy permanently blocked — found + fixed 2026-07-28

## What I found

Attempting the coverage-extension backfill (`--start-date 2024-01-01 --end-date 2024-01-03`), every day failed to write,
and a control test on **2026-04-10** — a day already present in the existing 15-day GCS window — also failed identically
when re-run with `--force` under current code. This proved the blocker was a **code regression affecting every date**,
not a historical-data gap.

**Bug 1 — `lst_native_rate_ts` computed from a String column via `.dt.epoch()`.** `_annualise_and_stamp()` (and the
identical pattern in `compute_lst_native_rates_for_day()`) called `pl.col("timestamp").dt.epoch("s")` to derive
`lst_native_rate_ts` ("epoch float consumed by carry_staked_basis Phase 6B" per the code's own comment). The raw MTDS
`lst_rates` `timestamp` column is written as a bare `YYYY-MM-DD` string (dtype `Utf8`), not a `Datetime` — `.dt.epoch()`
on a String column silently produces `null` for every row. That single all-null column alone tripped
`FeatureWriteGate`'s >95%-NaN-per-column threshold (`features_service/onchain/app/core/feature_writer.py`,
`WRITE_GATE_CONFIG.nan_threshold=0.95`), rejecting the shard outright:
`WARNING FeatureWriteGate REJECTED shard: 1 columns exceed 95% NaN: ['lst_native_rate_ts']`.

**Bug 2 — unmapped tokens (null `protocol`/`asset`) permanently trip `STRICT_FAIL`.** After fixing Bug 1, every day
still failed with `Emission policy suppressed write ... (policy=strict_fail event=STALE_DATA)` — despite the misleading
"STALE_DATA" name, this has **nothing to do with wall-clock date staleness**; `emission_publisher.py`'s
`publish_with_policy()` computes `completeness_fraction` from the NaN ratio of the WHOLE features DataFrame
(`_check_emission_policy()` in `feature_writer.py`) and, under `ServiceEmissionPolicy.STRICT_FAIL`, treats **any**
`completeness_fraction < 1.0` — even a single null cell anywhere — as a full gap: no partial credit, no row written.
`_annualise_and_stamp()`'s own code comment already documented the mechanism ("Tokens not in the [UAC]
`LST_TOKEN_TO_PROTOCOL_ASSET`] SSOT ... get null protocol/asset — caller treats as unmapped") but **no caller ever
actually filtered them** — so every day that included even one unmapped token (which, per the sample below, is every
day) had `completeness_fraction < 1.0` and was rejected wholesale, INCLUDING for the tokens that WERE fully mapped.

Verified on 2024-01-01: 6 of 20 tokens had null protocol/asset — `sanctumSOL`, `wBETH` (both genuine LSTs simply missing
from the UAC registry) and `IDLEDAI-BEST` / `IDLEUSDC-BEST` / `IDLEUSDT-BEST` / `PENDLE-SY-wstETH` (Idle Finance /
Pendle yield-tranche tokens — not LSTs at all, apparent scope creep in the upstream `oracle_prices`/ `lst_rates` MTDS
feed).

## Why it matters

`lst_yields` feeds `CanonicalLstYieldsIndexProvider`, which `strategy-service@e93902d8` reads for the STAKING leg of
`carry_staked_basis` (per `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`). Because this was a
**code-level regression, not a historical-data absence**, it meant `lst_yields` could not be written for ANY date — past
or present — as of current HEAD: the STAKING leg's honest-absence path was silently starved of new data every single
day, not just for the 15-day historical window the coverage-extension doc flagged.

## Fix (shipped this session)

`features-service/features_service/onchain/engine/lst_features.py`:

1. `_timestamp_to_epoch_expr(timestamp_dtype)` — dtype-aware: parses `YYYY-PM-DD` via
   `pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%d", strict=False)` before `.dt.epoch("s")` when the column is
   `Utf8`; passes through unchanged (`.dt.epoch("s")` directly) when already temporal (covers existing unit-test
   fixtures that mock `timestamp` as `datetime` objects).
2. `_drop_unmapped_tokens(out, feature_group, date)` — drops rows with null `protocol`/`asset` (unmapped tokens) BEFORE
   the emission-policy completeness check, logging a `LST_UNMAPPED_TOKENS_DROPPED` event listing the dropped token names
   (not silent). Applied in both `compute_lst_features_for_day` (lst_yields) and `compute_lst_native_rates_for_day`
   (lst_native_rates — same bug, same fix).

Verified: `--start-date 2024-01-01 --end-date 2024-01-03 --skip-dependency-check` now writes 14/16/16 rows/day to
`gs://features-defi-prd-central-element-323112/onchain/by_date/day=<date>/feature_group=lst_yields/features.parquet` —
confirmed via `gcloud storage ls`. Full features-service test suite (17,964 tests) passes with the fix; targeted
`basedpyright` on the changed file is clean (0 errors).

## Recommended follow-up (NOT done in this fix — deliberately out of scope, needs judgment)

- [ ] [DATA] P2. Add `wBETH` and `sanctumSOL` to UAC's
      `unified_api_contracts.internal.domain.defi.LST_TOKEN_TO_PROTOCOL_ASSET` (both are genuine LSTs currently dropped
      by `_drop_unmapped_tokens` purely because they're missing from the registry) — needs a correctness-minded decision
      on the exact canonical protocol/asset name pair, not a mechanical fix. Repo: unified-api-contracts.
- [ ] [DATA] P3. Investigate whether `IDLEDAI-BEST` / `IDLEUSDC-BEST` / `IDLEUSDT-BEST` / `PENDLE-SY-wstETH` belong in
      the MTDS `lst_rates`/`oracle_prices` feed at all — they read as Idle Finance / Pendle yield-tranche tokens, not
      liquid-staking tokens, and may indicate upstream data-scope creep worth tightening at the MTDS handler rather than
      silently filtering downstream forever. Repo: market-tick-data-service.
- [ ] [DATA] P3. Consider whether `ServiceEmissionPolicy.STRICT_FAIL`'s all-or-nothing completeness semantics (no
      partial credit for a mostly-complete row) is the right policy for `lst_yields`/`lst_native_rates`, or whether
      `PARTIAL_OK` degraded-publish semantics (already used elsewhere per `WRITE_GATE_CONFIG`'s own comment re:
      `lending_rates`) would be more appropriate now that unmapped-token filtering exists as a safety net. Repo:
      features-service / unified-trading-library (`emission_publisher.py` policy assignment is UAC-owned).

## Evidence

- `gcloud storage ls "gs://features-defi-prd-central-element-323112/onchain/by_date/*/feature_group=lst_yields/"` —
  day-partitions for 2024-01-01/02/03 now present alongside the original 15 (2026-04-03..19).
- features-service full test suite: 17964 passed, 209 skipped (pre-existing, unrelated skips).
- `features-service@<commit-sha-of-this-fix>` (see companion plan-flip commit).
