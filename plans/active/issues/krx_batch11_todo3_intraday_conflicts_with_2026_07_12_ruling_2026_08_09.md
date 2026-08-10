---
doc_type: issue
title:
  cefi_satellite_ao_dispatch_batch11 todo 3 (KRX 1h/15m/1m Yahoo backfill) conflicts with the resolved 2026-07-12
  KRX-intraday-adapter rejection; 1d leg already ~98% complete
summary: >-
  Dispatched todo 3 of cefi_satellite_ao_dispatch_batch11_2026_08_09.md asks to backfill KRX (HYUNDAI/SAMSUNG/SKHYNIX)
  via guardrailed Yahoo across 4 windows (1d/1h/15m/1m). The todo was extracted verbatim from a 2026-06-24 Phase-5 item
  in cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md — but a LATER, RESOLVED operator decision
  (plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md) explicitly rejected building
  Yahoo intraday fetch capability for KRX and narrowed unified-api-contracts' expected_coverage registry to
  ohlcv_24h-only. Live code (2026-08-09) confirms this is still the case: the Yahoo adapter has no intraday fetch path
  for KRX and the router hard-returns an honest-empty frame for any non-ohlcv_24h KRX request by design. batch11's own
  conflict-check only grepped plans/active/, so it missed this archived, governing decision. Separately, live-verified
  the achievable 1d/ohlcv_24h leg is already ~98% complete with real non-NaN data, and found 2 adjacent (non-blocking)
  manifest-integrity defects while verifying it.
status: open
nature: notes
asset_group: [cefi, tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [krx, yahoo-finance, tradfi, ssot-contradiction, honest-coverage, manifest-integrity, ao-dispatch]
related:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-08-09
author: slot-32
source: [cefi_satellite_ao_dispatch_batch11_2026_08_09.md todo 3, live code + manifest verification 2026-08-09]
assigned_vm: planning
parent_epic: infrastructure_master
priority: P2
resolved_by: applying-existing-2026-07-12-operator-ruling
locked_by:
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# KRX intraday Yahoo backfill (batch11 todo 3): SSOT conflict + 1d-leg verification

## What I found

**The SSOT conflict.** `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 3 asks: "Backfill the 3 KRX stocks
(HYUNDAI/SAMSUNG/SK-Hynix cash-twins) via guardrailed Yahoo: 1d since 2019-01-01 + 1h trailing 730d + 15m trailing 89d
(range=60d) + 1m 28-day-chunked." It cites `cefi_consolidated_closeout_2026_07_18.md` Track 0 (line 168), which in turn
cites `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 5 (dated 2026-06-24).

`plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` — filed 18 days AFTER that Phase 5
item, and RESOLVED — found the exact same ask genuinely impossible under the shipped adapter and put it to the operator.
**Operator decision (2026-07-12): "Yahoo doesn't reliably serve intraday granularity over long historical backfill
windows, so build-the-adapter (option 1) was rejected."** Shipped `unified-api-contracts@a2751f36`: narrowed
`expected_coverage.py`'s KRX entry from `["ohlcv_1m", "ohlcv_15m", "ohlcv_24h"]` to `["ohlcv_24h"]`, and dropped KRX
`ohlcv_1m` from the tradfi-perp equity-basis MVP carve-out (both registries narrowed in lockstep, same commit).

**Confirmed still true today (2026-08-09), live code read**:

- `unified-api-contracts/unified_api_contracts/registry/expected_coverage.py:200` — `"KRX": ["ohlcv_24h"]`.
- `market-tick-data-service/market_tick_data_service/adapters/_umi_yahoo.py::fetch_yahoo_equities` has NO
  interval/granularity parameter — it only ever calls `YahooFinanceAdapter.download_daily` (hardcoded
  `data_type="ohlcv_24h"` on every row).
- `route_yahoo_tradfi` in the same file hard-gates:
  `if data_types and "ohlcv_24h" not in data_types: return pd.DataFrame()` for FX/KRX/ICE — an explicit, documented,
  by-design empty-return for any non-daily request (citing the 2026-07-09 452-shard-sweep silent-mislabeling bug this
  exact guard was built to prevent — see the same archived issue doc).
- The adapter CLASS does have a general `YahooFinanceAdapter.download_intraday(interval, ...)` method with the guardrail
  wired (`assert_yahoo_intraday_within_limit` — probed ladder 1m=28d/15m=89d(range=60d)/1h=730d), but nothing in the KRX
  code path ever calls it. This is the exact gap the 2026-07-12 issue identified and the operator declined to close.
- Manifest (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, filtered
  `venue=KRX`): there is no `ohlcv_1h` data_type tracked for KRX at all. `ohlcv_15m`/`ohlcv_1m` rows exist under the
  canonical instrument_id form but **zero** are ever `capture_status=captured` (all `attempted_failed`/
  `empty_confirmed`/`expected_unattempted`) — live confirmation of zero real capability, matching the 2026-07-12 finding
  exactly.

**Why batch11 missed it**: batch11's own Progress Log conflict-check (2026-08-09) states it "grepped the full
`plans/active/` corpus" for each todo's target — the governing decision lives in `plans/archive/issues/`, outside that
grep's scope, so a resolved, directly-on-point operator ruling from 4 weeks earlier was never surfaced.

## The achievable leg (1d/ohlcv_24h) — verified ~98% complete

Filtered the same manifest to `venue=KRX, data_type=ohlcv_24h`, canonical instrument_id form (`KRX:EQUITY:{code}-USD` —
see "adjacent finding 2" below for the non-canonical duplicate): **2943 `captured` / ~2997 total rows (~98%) since
2019-01-02**, across all 3 symbols. Remaining gaps: 42 `expected_unattempted` + 12 `attempted_failed`
(`NO_RAW_TICK_DATA_FOR_SHARD`), all within 2026-08-03..2026-08-06 — the most recent trading days, consistent with
ordinary Yahoo adjusted-close publication lag rather than a structural gap.

Spot-verified against the REAL GCS object (not just the manifest label) — the manifest's `row_count` field reads 0 for
most `captured` rows (see adjacent finding 1), so I did not trust the manifest alone:
`gs://market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/day=2020-01-06/pipeline_mode=batch_yahoo/asset_group=tradfi/venue=KRX/instrument_type=equity/data_type=ohlcv_24h/KRX:EQUITY:005930-USD.parquet`
— 1 real row, non-NaN: `open=47801.95 high=48402.70 low=47716.13 close=47887.77 volume=10009778`. The 1d leg's data is
genuinely there and correct.

## Adjacent findings (not blocking this todo — filed as follow-up todos below)

1. **Manifest `row_count` field bug**: 2925 of 2943 canonical-id `ohlcv_24h`/KRX `captured` rows show `row_count=0` in
   the manifest despite the underlying GCS parquet object genuinely holding 1 non-NaN row (confirmed above). The writer
   is marking `capture_status=captured` correctly but not populating `row_count` for this venue+data_type — a
   metadata-integrity defect. Any downstream consumer trusting `row_count` (rather than re-reading the parquet) would
   undercount KRX daily coverage as ~0% when it's actually ~98%.
2. **Duplicate/stale shard-atom instrument_id**: the manifest carries a SECOND, non-canonical instrument_id form for the
   same 3 equities — `KRX:EQUITY:{code}.KS-USD` (retaining the Yahoo `.KS` suffix) — with **zero** real captures (all
   `empty_confirmed`/`expected_unattempted`, ~8261 rows total) alongside the canonical `KRX:EQUITY:{code}-USD` form
   (which the current writer, `derive_tradfi_row_instrument_id`-based, actually uses). Violates the "shard atom
   identical across writer/manifest/status/gate/UI" HARD RULE
   (`/codex/02-data/availability-manifest-and-data-status.md`); looks orphaned from before the current writer path
   shipped. Inflates `expected_unattempted`/gap counts for any KRX coverage dashboard or audit that doesn't also filter
   by instrument_id form (e.g. this is why a naive venue=KRX groupby initially looked like ~0.07% coverage before I
   split by instrument_id).

## Recommended decision (applied — no new operator input required)

The 2026-07-12 ruling is directly on point and unreversed; I'm applying it as governing precedent rather than treating
this as fresh ambiguity. **`cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 3 is narrowed to its 1d/ohlcv_24h leg
(already ~98% complete, verified with real data) and closed; the 1h/15m/1m legs are marked will-not-build per the
resolved 2026-07-12 decision**, with a pointer back to this doc. If a future business need genuinely requires KRX
intraday bars, that's a fresh product-scope question for the operator (Yahoo's short/rolling intraday windows would only
ever cover the trailing 28-730 days, never deep history) — not a re-litigation of this finding.

## Todos

- [x] ✅ [DATA] P2. Root-cause + fix the KRX `ohlcv_24h` manifest `row_count=0`-on-`captured` bug in
      market-tick-data-service's Yahoo write path (the writer correctly marks `capture_status=captured` but doesn't
      populate `row_count` for the row actually written — confirmed via direct GCS parquet read vs. manifest label
      mismatch above). Repo: market-tick-data-service. **Done when**: newly-written KRX ohlcv_24h shards carry a correct
      non-zero `row_count`, `quality-gates.sh` green. — market-tick-data-service@ca93d553. **Root cause was NOT the live
      Yahoo daily writer** (`_umi_yahoo.py` → `partitioned_writer.py` → `manifest_finalize.py` already correctly counts
      `len(group_df)` per shard — confirmed via manifest read: the 18 rows written by the daily scheduled path all carry
      `row_count=1`). The 2925 zero-`row_count` rows all share one `written_at=2026-08-02T17:40:20` timestamp — a single
      bulk run of `market_tick_data_service/scripts/rebuild_tradfi_manifest.py` (the
      `mtds_available_at_cross_asset_backfill` manifest-rebuild script, object-scan reconstruction from live GCS paths).
      Its non-bundled `_emit_shard_row` hardcoded `row_count=0` on every `target.add()` call — a genuine metadata bug,
      not just a display artifact, since the row's own blob existing means ≥1 row was genuinely written. Fixed to
      `row_count=1` (`rebuild_tradfi_manifest.py:551`), mirroring the sibling `_emit_bundled_shard_row`'s pre-existing
      `row_count=1` placeholder convention (same PERF rationale: skip the parquet download, stamp a non-zero value so
      the row doesn't read as a `captured & row_count<=0` phantom). Added regression test
      `test_scan_rebuild_apply_non_bundled_row_count_is_nonzero`
      (`tests/unit/scripts/test_rebuild_tradfi_manifest_coverage.py`). `quality-gates.sh` green (sentinel=ca93d553).
      **Scope note**: this fixes the code path going forward (future rebuild-script runs); it does NOT repair the 2925
      already-written zero-`row_count` manifest rows in place — that would need a fresh `rebuild_tradfi_manifest.py`
      re-run over the affected range, a separate (larger, infra-scale) action out of this todo's 1-hour scope.
- [ ] [DATA] P3. Clean up the orphaned `KRX:EQUITY:{code}.KS-USD` manifest shard-atom duplicate (~8261 rows, 0 real
      captures, predates the current `derive_tradfi_row_instrument_id`-based writer). Confirm it's genuinely dead (no
      writer emits it anymore), then either exclude it from future enumeration or purge the manifest rows per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Repos: market-tick-data-service, instruments-service
      (enumerator). **Done when**: the manifest carries only the canonical instrument_id form for KRX going forward,
      `quality-gates.sh` green.

## Progress Log

- **2026-08-09** — Filed while executing `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 3. Found the SSOT
  conflict via `plans/archive/issues/` grep (batch11's own conflict-check only covered `plans/active/`), confirmed live
  against current `expected_coverage.py` + `_umi_yahoo.py` code and the live manifest + a real GCS parquet read.
  Resolution applied same-day: todo 3 narrowed + closed citing this doc (see batch11's Progress Log entry).
- **2026-08-09** (slot-7) — Flipped todo 1. Read-verified the manifest split by `written_at`: the daily live Yahoo
  writer (`_umi_yahoo.py`) already stamps correct `row_count=1` (18/18 sampled rows); the 2925 zero-`row_count` rows all
  trace to one bulk `rebuild_tradfi_manifest.py` run (2026-08-02T17:40:20Z, the `mtds_available_at_cross_asset_backfill`
  manifest rebuild). Root cause: that script's non-bundled object-scan `.add()` call hardcoded `row_count=0`. Fixed to
  `row_count=1` (matches the sibling bundled-shard code path's existing convention) + regression test. Shipped
  market-tick-data-service@ca93d553, QG green. Todo 2 (P3, duplicate instrument_id cleanup) remains open — doc stays
  active.
