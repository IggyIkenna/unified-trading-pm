---
doc_type: issue
title: >-
  "All 18 MDPS adapters' process_to_candles(df, …) → Polars adapter-protocol seam" (batch13 todo) is NOT a single-task
  AO-dispatch item — confirmed multi-day, judgment-heavy migration via concrete scope survey
summary: >-
  cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md classified this todo (sourced from
  mtds_file_size_refactor_2026_06_08.md's "survivor M-2" P3 item) as bounded/deterministic AO-dispatch-eligible. A
  concrete file-by-file scope survey (18 adapter files under market_data_processing_service/app/adapters/, their
  callers, and base_adapter.py's shared pandas helpers) shows this is false: it is an atomic, single-PR migration
  touching an ABC/Protocol boundary used polymorphically by CandleAdapterRegistry — every one of the 18 adapters must
  convert together (a partial signature change breaks the shared Protocol), and 5 of the 18 (cefi/trades_adapter.py,
  cefi/book_snapshot_adapter.py, cefi/liquidations_adapter.py, sports/bucket_assignment_adapter.py,
  tradfi/ohlcv_passthrough.py) do genuine groupby-based feature-engineering (whale-detection/momentum/percentile stats,
  HFT microstructure spread/depth/imbalance calcs) with no trivial 1:1 polars swap — a correctness-risk rewrite on live
  candle-production code, not a mechanical type-hint change. This exact work was already operator-deferred twice ("LATER
  migration") across two archived predecessor plans (mdps_pure_polars_migration_2026_05_28.md,
  mdps_adapter_protocol_pandas_to_polars_2026_06_21.md) and its own estimate (shared with one other item) was 2.0
  calibrated AI-days — never a 1-hour single-worker task. Per CLAUDE.md's "AO-eligible = outcome DETERMINABLE by the
  worker alone" rule, this should not have been extracted into a bounded AO-dispatch batch as-is.
status: open
nature: issue
scope: [engineer, admin]
asset_group: [cross-cutting]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
tags: [ao-dispatch, mis-scoping, polars-migration, mdps, adapter-protocol, plan-classification]
related:
  [
    /plans/active/mtds_file_size_refactor_2026_06_08.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-15
author: claude-agent
source: cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md todo pickup, slot-31 infra worker
assigned_vm: NA
parent_epic: mtds_mdps_master
priority: P3
resolved_by:
locked_by:
---

# MDPS adapter-protocol polars seam — mis-scoped for AO dispatch

## What I found

Dispatched batch13's todo "All 18 MDPS adapters' `process_to_candles(df, …)` -> Polars adapter-protocol seam" (Source:
`plans/active/mtds_file_size_refactor_2026_06_08.md`). Before touching code, ran a concrete file-by-file scope survey of
`market_data_processing_service/app/adapters/` (18 files implementing `process_to_candles`), every production caller,
and `base_adapter.py`'s shared pandas helpers.

**The boundary is atomic, not parallelizable.** `process_to_candles` is an `@abstractmethod` on `BaseCandleAdapter`,
invoked polymorphically via `CandleAdapterRegistry.get_adapter(category, data_type)` from `live_workers_chain.py` (3
call sites) and `live_workers_streaming.py` (1 call site) — all 4 call sites currently do an explicit
`tick_data.to_pandas()` immediately before the call, commented as "the UAC adapter Protocol boundary." Flipping the
signature to `pl.DataFrame` requires converting **all 18 adapters in the same PR** — a partial conversion leaves the
registry returning adapters with inconsistent `process_to_candles` signatures under one ABC contract, which is not a
safely revertible/bisectable intermediate state.

**5 of the 18 adapters need genuine internal-logic rewrites, not type-hint swaps** (no `.groupby`/`.resample` →
`.iloc`/`.loc` 1:1 polars mapping): `cefi/trades_adapter.py` (760 lines, 8 `.groupby` calls, 5 custom feature-calc
helpers — delay/momentum/percentile/whale/vol-clock stats; a parallel `_compute_grouped_stats_polars` path already
exists as a partial reference), `cefi/book_snapshot_adapter.py` (929 lines, 3 `.groupby`, HFT microstructure
spread/depth/imbalance math), `cefi/liquidations_adapter.py` (511 lines, 6 `.groupby`),
`sports/bucket_assignment_adapter.py` (1112 lines, session/state-grid machinery layered on `base_adapter.py`'s
`_finalize_session_grid`/`_carry_forward_ohlc` helpers), and `tradfi/ohlcv_passthrough.py` (430 lines — also the
delegation target `tradfi/trades_adapter.py` calls into, so it sits on that adapter's critical path despite
`trades_adapter.py` itself being a trivial delegator).

The other 13 are light-to-trivial (3 are pure `super().process_to_candles(...)` delegation, ~10 pass `tick_data`
straight into `base_adapter.py`'s shared helpers plus ≤1 simple single-key `.groupby`) — most of that surface is
centralized in `base_adapter.py`'s ~5 pandas-typed helper methods (`_convert_to_processing_dt`,
`_get_local_timestamp_column`, `_series_to_datetime`, the `df`-arg variant of `_extract_instrument_info`), so converting
those once covers the light adapters almost for free. The genuinely hard, correctness-risk cost is concentrated in the 5
heavy files.

**Not a new discovery that this is large** — the exact same scope was already operator-deferred twice under two archived
predecessor plans (`mdps_pure_polars_migration_2026_05_28.md`, `mdps_adapter_protocol_pandas_to_polars_2026_06_21.md`),
both explicitly marked "LATER migration" / "not started." `mtds_file_size_refactor_2026_06_08.md`'s own combined
estimate for this item + one unrelated item was `estimate_calibrated_ai_days: 2.0`. batch13's 2026-08-13 audit sweep
re-extracted the todo and classified it "bounded/deterministic (worker-determinable outcome, no open design/judgment
call)" — that classification does not hold up against the concrete survey above; the 5 heavy adapters require domain
judgment about correctness of live feature-engineering translations (the sibling already-shipped engine-internal
conversion, `mdps_polars_engine_cost_sharpening_2026_06_28.md`, needed explicit before/after benchmarking against
audited targets — 10.35× wall / 6.11× peak RSS / 8.88× retention — precisely because a naive pandas→polars port of
aggregation logic is a correctness/perf risk, not a mechanical rename).

## Why it matters

CLAUDE.md's plan-authoring HARD RULE: "AO-eligible = outcome DETERMINABLE by the worker alone, never an open-ended
judgment/design call — resolve that first as a LOCAL plan, then dispatch against its outcome." This todo does not meet
that bar as currently scoped, and attempting it inside a single bounded AO task risks either (a) an unsafe rushed
rewrite of live candle-production code across 5 asset groups (cefi/defi/tradfi/sports/prediction) with no room for the
same before/after benchmarking discipline the sibling engine-internal migration required, or (b) an incomplete,
un-shippable partial conversion that leaves the adapter registry in an inconsistent state. Per the "Data pipeline
correctness is the heartbeat" HARD RULE, this is exactly the class of change that should not be rushed.

## Recommended decision

Do NOT re-extract this todo into a future AO satellite-dispatch batch as a single bounded item. Instead:

1. Keep it parked at its designated owner, `mtds_file_size_refactor_2026_06_08.md` (already self-declared "this plan
   itself remains the owner" in its own Progress Log) — annotated with this survey's findings so a future pickup does
   not have to re-derive the scope from scratch.
2. When picked up, it needs a **dedicated design/execution effort** (mirroring
   `mdps_polars_engine_cost_sharpening_2026_06_28.md`'s own pattern for the engine-internal half of this same seam): one
   atomic PR touching `base_adapter.py`'s ~5 shared helpers + all 18 adapters + the 4 caller-side `.to_pandas()` glue
   sites in `live_workers_chain.py`/ `live_workers_streaming.py`, with before/after correctness verification (existing
   adapter test suite green, ideally a numeric-parity check between the old pandas path and new polars path on a real
   historical shard for each of the 5 heavy adapters) before shipping — not a per-file incremental AO todo split, since
   the ABC boundary can't be half-migrated.

## Todos

- [ ] [DESIGN] P3. Scope a dedicated implementation plan for the MDPS adapter-protocol polars seam (one atomic PR:
      `base_adapter.py`'s 5 shared pandas helpers + all 18 `market_data_processing_service/app/adapters/*` files + the 4
      `.to_pandas()` caller-side sites in `live_workers_chain.py`/`live_workers_streaming.py`), including a
      numeric-parity verification step for the 5 groupby-heavy adapters (cefi/trades_adapter.py,
      cefi/book_snapshot_adapter.py, cefi/liquidations_adapter.py, sports/bucket_assignment_adapter.py,
      tradfi/ohlcv_passthrough.py) before ship. Repo: market-data-processing-service.
