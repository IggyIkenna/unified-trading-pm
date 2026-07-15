---
doc_type: plan
title: Fix Kraken-Futures dated-future symbol collision — 5 real instruments write to one identical instrument_id
summary: >-
  market-tick-data-service's Kraken-Futures underlying-extraction regex assumes a TICKER-QUOTE symbol shape but Kraken's
  real dated-future format is {TYPE_PREFIX}_{PAIR}_{DATE} (FI_XBTUSD_220325 — FI/FF/PI/PF are contract-type codes, not
  tickers). The regex falls through to grabbing the 2-letter type-prefix, so BCH/ETH/LTC/XBT/XRP quarterly futures (same
  expiry) all collapse onto the byte-identical instrument_id KRAKEN-FUTURES:FUTURE:FI-USD-inverse-20220325 — confirmed
  via 5 real GCS parquet files. Real data corruption risk, not a naming/format issue.
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
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
- [x] [DATA] P1. **Scope real historical damage** — full-corpus walk (all 2,649 real `day=` partitions under
      `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`, not a sample) for
      `venue=KRAKEN-FUTURES` found dated-future (`instrument_type=future`) captures on exactly **5 real days**:
      `2022-03-01`, `2022-03-04`, `2024-02-01`, `2025-01-10`, `2026-01-10` (across `data_type=trades` +
      `data_type=book_snapshot_5`, 10 (day, data_type) combos total) — **125 real parquet files**, **37,559,524 total
      rows**, **6 distinct real tickers** confirmed corrupted (`BCH`, `ETH`, `LTC`, `SOL`, `XBT`, `XRP`) across 15
      distinct real expiry codes. The legacy pre-migration bucket (`market-data-tick-cefi-central-element-323112`, 2,613
      days) was also checked directly — 0 Kraken-Futures dated futures there (only perpetuals; this data was captured
      2026-07-03 → 2026-07-08, after the 2026-06-01 legacy migration cutoff). Important structural finding: **0 of the
      125 files were physically merged/bundled** — every file already isolates exactly one real (ticker, expiry) by its
      raw-symbol filename (e.g. `FI_XBTUSD_220325.parquet`, `instrument_type=future` singular, not the multi-symbol
      `futures_chain` bundle shape) because none of these captures ever went through the production multi-symbol fan-out
      path that would merge same-day siblings into one `underlying=FI/...` v6 shard — confirmed 0 such bundle files/v6
      `underlying=` shards exist anywhere in the corpus for this venue. So the bug corrupted the **derived
      `underlying` + `instrument_id` COLUMN VALUES inside** each file, not the physical file/partition layout.
- [x] [DECISION] P1. **Decide remediation for already-collided historical data** — per the operator's 2026-07-08
      migration-mechanics decision ([[instrument_id_format_canonicalization_2026_07_08]]): rewrite/relabel in place from
      the untouched raw `symbol` column, no re-download. Since 0 files needed physical re-splitting (see scoping above),
      remediation was column-level only, executed for real against all 125 files: (1) server-side backup of every
      original object to `_remediation_backups/kraken_futures_collision_2026_07_08/<original path>` (verified present
      post-run); (2) recompute `underlying` via the shipped-fixed `TardisAdapter._extract_underlying_for_chain` and
      `instrument_id` via `derive_row_instrument_id`, both driven off the real `symbol` column; (3) overwrite each file
      in place, preserving every other column/row untouched; (4) re-download + assert
      row-count/symbol-column/instrument_id match post-write. Result: **125/125 files fixed, 0 errors, 37,559,524 rows
      corrected**. Independent post-hoc re-scan (fresh full-corpus walk + content read of all 125 files) confirms **0
      files remain showing the buggy bare-prefix `KRAKEN-FUTURES:FUTURE:{FI,FF,PI,PF}-USD-inverse-*` instrument_id**,
      and an aggregate distinct-count check confirms 0 remaining collisions between DIFFERENT real tickers
      (BCH/ETH/LTC/SOL/XBT/XRP are all correctly distinct now). **New, separate finding surfaced by this verification**
      (not the ticker-collision bug, and not fixed here — see new todo below): 13 of the 49 distinct corrected
      `instrument_id`s (45 of the 125 files) map to TWO different real raw symbols sharing the same corrected id — an
      `FI_` and an `FF_` prefix variant of the same (ticker, expiry), e.g. `FI_ETHUSD_240329` (129,010 book_snapshot_5
      rows + 447 trades) and `FF_ETHUSD_240329` (107,156 book_snapshot_5 rows + 330 trades) both derive
      `KRAKEN-FUTURES:FUTURE:ETH-USD-inverse-20240329` — real, different row counts on both sides (not duplicates), only
      affecting ETH/XBT (the 2 most liquid pairs) across 13 (ticker, expiry) combos in the 2024-2026 range.
      `derive_row_instrument_id`'s FUTURE branch has no field to encode the `FI`/`FF` contract-subtype distinction at
      all — a schema gap, not an extraction bug — so it also affects any FI/FF pair that could exist beyond the 125-file
      scope of this fix. Manifest secondary finding: `_index/availability_index.parquet` carries exactly 4 stale rows
      (`2022-03-01`/`2022-03-04` × `trades`+`book_snapshot_5`) with the pre-fix bare `instrument_id="FI"` — the other 3
      affected days have NO manifest row at all for `instrument_type=FUTURE` despite real GCS files existing (a
      pre-existing, unrelated manifest-recording gap — these captures bypassed the
      `record_shard_count`/`record_instrument` bookkeeping entirely). Not hand-patched here (a coarse day-level manifest
      row cannot correctly represent a 6-ticker split without re-deriving multiple new rows against a 7.2M-row SSOT
      index outside the consolidator's own rebuild path) — flagged for the manifest consolidator to reconcile on its
      next real-content rebuild.
- [x] [DATA] P2. **NEW (found during this fix's historical-damage verification, 2026-07-08): resolve the `FI_`-vs-`FF_`
      same-(ticker,expiry) instrument_id collision** — 13 real (ticker, expiry) pairs (ETH/XBT only, 2024-2026 range, 45
      of the 125 remediated files) have BOTH an `FI_` and an `FF_` raw Tardis symbol with real, differing row counts
      (not duplicates) that now derive the IDENTICAL corrected `instrument_id` because `derive_row_instrument_id`'s
      FUTURE branch has no field for the `FI`/`FF` contract-subtype. Needs an operator decision on what `FI_` actually
      represents relative to `FF_` for KRAKEN-FUTURES (the existing code comment in `tardis_shared.py` calling `FI_`
      "old index, pre-2020, no longer active" is contradicted by real 2024-2026 data found here) and how to encode the
      distinction in the canonical instrument_id (e.g. a contract-subtype marker) before any further Kraken-Futures
      remediation or backfill. — **FOLDED OUT** to plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md
      (2026-07-15, plan-reconcile §6 operator ruling); tracked there, not here.
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
- **2026-07-08 (later)** — Historical-damage scoping + remediation executed for real (operator's standing decision:
  "always fix history"). Full-corpus GCS walk (2,649 real day-partitions,
  `market-data-tick-cefi-prd-central-element-323112`, plus the 2,613-day legacy pre-migration bucket checked and
  confirmed clean) found real Kraken-Futures dated-future captures on 5 days (`2022-03-01`, `2022-03-04`, `2024-02-01`,
  `2025-01-10`, `2026-01-10`), 125 real parquet files, 37,559,524 rows, 6 real tickers (BCH/ETH/LTC/SOL/XBT/XRP).
  Structural finding: every affected file was already single-real-instrument by filename (the production multi-symbol
  chain-bundling path never actually ran for this venue — 0 merged `futures_chain`/v6 `underlying=` shards exist
  anywhere in the corpus), so the bug only corrupted the derived `underlying`/`instrument_id` COLUMN VALUES, not the
  physical file layout — no repartition/rename needed. Remediated all 125 files in place (server-side backup to
  `_remediation_backups/kraken_futures_collision_2026_07_08/` first, then recomputed `underlying`+`instrument_id` from
  the untouched raw `symbol` column via the already-shipped fix, overwrote, re-verified): 125/125 fixed, 0 errors.
  Independent post-hoc full re-scan confirms 0 files still carry the buggy bare-prefix instrument_id and 0 remaining
  collisions between different real tickers. Discovered (not fixed — new todo filed) a SEPARATE real ambiguity while
  verifying: 13 (ticker,expiry) pairs (ETH/XBT only, 45 of the 125 files) have both a real `FI_` and a real `FF_` raw
  symbol with different row counts that now share one corrected `instrument_id` — a schema gap (no field for `FI`/`FF`
  contract-subtype), not an extraction bug, and not in scope for this fix. Also found (not fixed — flagged, not silently
  patched) a 4-row staleness in `_index/availability_index.parquet` (still shows the pre-fix bare `"FI"` for the 2
  earliest days) plus a 3-day gap where real GCS captures have no manifest row at all — a pre-existing, unrelated
  manifest-recording issue, left for the manifest consolidator's own rebuild rather than hand-patched against the live
  7.2M-row SSOT index.
