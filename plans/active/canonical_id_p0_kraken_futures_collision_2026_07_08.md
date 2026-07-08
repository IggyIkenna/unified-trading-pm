---
doc_type: plan
title: Fix Kraken-Futures dated-future symbol collision — 5 real instruments write to one identical instrument_id
summary: >-
  market-tick-data-service's Kraken-Futures underlying-extraction regex assumes a TICKER-QUOTE symbol shape but Kraken's
  real dated-future format is {TYPE_PREFIX}_{PAIR}_{DATE} (FI_XBTUSD_220325 — FI/FF/PI/PF are contract-type codes, not
  tickers). The regex falls through to grabbing the 2-letter type-prefix, so BCH/ETH/LTC/XBT/XRP quarterly futures (same
  expiry) all collapse onto the byte-identical instrument_id KRAKEN-FUTURES:FUTURE:FI-USD-inverse-20220325 — confirmed
  via 5 real GCS parquet files. Real data corruption risk, not a naming/format issue.
status: active
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [instrument-id, data-integrity, kraken, bug-fix, p0]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  'Canonical instrument-id audit, 2026-07-08 (canonical_instrument_id_audit_2026_07_08.md, finding #1) — direct read of
  5 real GCS parquet files confirmed the collision. Operator: "I dont care that its gonna break live because were not
  trading anything live yet anyway."'
---

> **Real data-corruption bug, not a format preference.** 5 genuinely distinct real financial instruments are currently
> indistinguishable in storage. Fix the extraction, then determine (todo below) whether historical data needs
> re-backfilling or can be left as a known-bad historical range with go-forward correctness only.

## Root cause

`market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py:341-352`
(`_extract_underlying_for_chain`) uses regex `^([A-Z]{2,10})(?:-|USDT_|USD_|USDC_)` expecting a ticker-then-quote shape.
Kraken/cryptofacilities' real dated-future symbols are `{TYPE_PREFIX}_{PAIR}_{DATE}` — confirmed real examples:
`FI_BCHUSD_220325`, `FI_ETHUSD_220325`, `FI_LTCUSD_220325`, `FI_XBTUSD_220325`, `FI_XRPUSD_220325` (all real 2022-03-25
quarterly futures). The regex doesn't recognize this shape and falls through to `re.match(r'^([A-Z]+)', s)`, which
greedily grabs `FI` (the 2-letter contract-type prefix) instead of the real ticker one token over — consumed by
`tardis_cefi_shards.py:104,420` and `tardis_bulk_download.py:59`, then stamped into `instrument_id` by
`market_interface/adapters/cefi/tardis_shared.py:455-459` (`derive_row_instrument_id`).

## Todos

- [x] [DATA] P0. **Fix `_extract_underlying_for_chain` to recognize Kraken's real `{TYPE_PREFIX}_{PAIR}_{DATE}` shape**
      — add an explicit case for the `FI_`/`FF_`/`PI_`/`PF_` prefix family that extracts the real ticker (the segment
      between the prefix and the quote currency), rather than falling through to the greedy generic regex. —
      market-tick-data-service@3d7491b1bcbebc17af0aa31219e90f38478d57cd. Added `_KRAKEN_DATED_PREFIX_RE` (class attr on
      `TardisAdapter`, `tardis_adapter.py`) matched BEFORE the generic fallback regex; also added a permanent
      regression-test class (`TestExtractUnderlyingForChainKrakenFutures`) in
      `tests/unit/test_tardis_symbol_normalization.py` (no prior unit coverage existed for this function).
- [x] [VERIFY] P0. **Confirm the fix against all 5 real colliding files** (`FI_BCHUSD_220325`, `FI_ETHUSD_220325`,
      `FI_LTCUSD_220325`, `FI_XBTUSD_220325`, `FI_XRPUSD_220325`) plus at least 2 more real Kraken dated-future symbols
      not in the original 5, to confirm the fix generalizes and doesn't just special-case the known examples. — Verified
      via direct GCS read (`unified_trading_library.get_storage_client()`, `GCP_PROJECT_ID=central-element-323112`) of
      the real bucket/prefix cited in Root cause, confirming the `symbol` column of each parquet matches its filename.
      Before the fix all 5 same-expiry files derived the SAME `instrument_id`
      (`KRAKEN-FUTURES:FUTURE:FI-USD-inverse-20220325`); after the fix all 5 are distinct
      (`KRAKEN-FUTURES:FUTURE:{BCH,ETH,LTC,XBT,XRP}-USD-inverse-20220325`). Generalization confirmed with 2 more real
      symbols from the same bucket/prefix, different expiries: `FI_XBTUSD_220624` →
      `KRAKEN-FUTURES:FUTURE:XBT-USD-inverse-20220624`, `FI_XBTUSD_220930` →
      `KRAKEN-FUTURES:FUTURE:XBT-USD-inverse-20220930` (both previously distinct from the 220325 group only by
      expiry-date collision-avoidance, now also correctly ticker-distinct from siblings at their own expiry).
- [ ] [DATA] P1. **Scope real historical damage** — query the real GCS bucket for how many days/symbol-pairs this
      collision has silently affected (not just the one 2022-03-25 expiry sample), to size the blast radius before
      deciding on remediation. (Left unchecked — operator-decision-gated per task scope, not attempted.)
- [ ] [DECISION] P1. **Decide remediation for already-collided historical data** — the colliding rows are already
      captured under one wrong shared key; deciding whether to re-backfill the correct per-instrument data (if
      recoverable from Tardis) or accept the historical gap and only fix go-forward captures is an operator call once
      the blast-radius scoping above lands. (Left unchecked — operator decision, not attempted.)
- [x] [SCRIPT] P1. **Ship the fix via quickmerge**, quality-gates green, following this workspace's standard
      commit-push-flip discipline. — market-tick-data-service@3d7491b1bcbebc17af0aa31219e90f38478d57cd via
      `bash scripts/quickmerge.sh ... --agent --files 'market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py tests/unit/test_tardis_symbol_normalization.py'`.
      `bash scripts/quality-gates.sh --no-fix` fully green beforehand (exit 0, "ALL QUALITY GATES PASSED", full
      5469-test suite + basedpyright ran — confirmed via a `QG_SENTINEL_DISABLE=true` forced full re-run, not just a
      content-sentinel cache hit). Landed on `live-defi-rollout`; Tier-C drain promotes to staging/main next.

## Progress Log

- **2026-07-08** — Filed from the canonical instrument-id audit's P0 finding #1. Root cause identified and cited with
  file:line precision by the audit agent via direct GCS reads; no code fix attempted yet.
- **2026-07-08** — Fix shipped: `market-tick-data-service@3d7491b1bcbebc17af0aa31219e90f38478d57cd`. Added
  `_KRAKEN_DATED_PREFIX_RE` to `tardis_adapter.py`'s `_extract_underlying_for_chain` (matched before the generic
  fallback) plus a regression-test class in `tests/unit/test_tardis_symbol_normalization.py`. Verified against the 5
  originally-colliding real files + 2 more real symbols via direct GCS read — all 7 now derive distinct `instrument_id`s
  (previously the 5 same-expiry files all collapsed to one). `quality-gates.sh --no-fix` fully green (full test suite +
  basedpyright confirmed via forced non-cached re-run). Historical-damage scoping + remediation decision left unchecked
  per task scope — operator-decision-gated, not attempted.
