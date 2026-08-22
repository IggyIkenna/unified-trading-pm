---
doc_type: plan
title: MDPS adapter-protocol polars migration — dedicated implementation plan
summary: >-
  Scopes the atomic, single-PR migration of all 18 process_to_candles adapters (plus base_adapter.py's shared
  pandas helpers and 4 caller-side .to_pandas() glue sites) from pandas to polars — the design/execution plan
  mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md's own [DESIGN] todo asked for. Human-driven
  by operator ruling 2026-08-22 (not AO-dispatched — 5 of 18 adapters carry genuine groupby-based feature-engineering
  correctness judgment, not a mechanical type-hint swap).
status: draft
nature: design
asset_group: [cross-cutting]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [mdps, polars, adapter-protocol, migration, design]
related:
  [
    /plans/active/mtds_file_size_refactor_2026_06_08.md,
    /plans/archive/2026_06/mdps_pure_polars_migration_2026_05_28.md,
    /plans/archive/2026_06/mdps_adapter_protocol_pandas_to_polars_2026_06_21.md,
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/adapters/base_adapter.py,
    market-data-processing-service/market_data_processing_service/app/engine/live_workers_chain.py,
    market-data-processing-service/market_data_processing_service/app/engine/live_workers_streaming.py,
    /plans/archive/2026_07/mdps_polars_engine_cost_sharpening_2026_06_28.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md's own [DESIGN] P3 todo — "Scope a dedicated
  implementation plan for the MDPS adapter-protocol polars seam." Picked up by T2 2026-08-22 per operator ruling on
  plan dispatch (human-driven, not AO).
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# MDPS adapter-protocol polars migration — dedicated implementation plan

## Why this plan exists, and why it is `status: draft`

`mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md` proved via a concrete file-by-file scope
survey that converting `process_to_candles(df: pd.DataFrame, ...)` to `pl.DataFrame` across
`market_data_processing_service/app/adapters/` cannot be a bounded AO-dispatch task: it is an atomic boundary
(`BaseCandleAdapter.process_to_candles` is an `@abstractmethod` invoked polymorphically via
`CandleAdapterRegistry.get_adapter(...)` from 4 call sites — 3 in `live_workers_chain.py`, 1 in
`live_workers_streaming.py` — so a partial conversion leaves the registry serving adapters with an inconsistent
signature under one ABC contract), and 5 of the 18 adapters need genuine correctness-judgment rewrites of live
feature-engineering logic, not a mechanical rename. This plan is that dedicated scope.

**`status: draft` is deliberate, not an oversight.** This plan is a SCOPING artifact per its own source todo — it
enumerates the exact 18+1+4 file surface, the verification bar, and a proposed phase/sequencing split, but does
**not** itself execute the migration. Flip to `status: active` only when an operator or engineer picks up actual
execution — until then this stays a reference document, not a live dispatch surface. (It is `assigned_vm: NA`
either way, so this distinction only matters for whether a human treats it as "ready to start.")

## Scope — the exact file surface (verified against the source issue doc, not re-derived)

**Shared boundary (must convert together, first):**
- `market_data_processing_service/app/adapters/base_adapter.py` — ~5 pandas-typed helper methods shared by most
  adapters: `_convert_to_processing_dt`, `_get_local_timestamp_column`, `_series_to_datetime`, the `df`-arg variant
  of `_extract_instrument_info`, plus `BaseCandleAdapter`'s own `process_to_candles` abstract signature.
- 4 caller-side `.to_pandas()` glue sites — 3 in `live_workers_chain.py`, 1 in `live_workers_streaming.py` —
  currently converting the polars `tick_data` to pandas immediately before calling into the adapter Protocol
  boundary; these become no-ops (delete the conversion, pass `tick_data` through as-is) once every adapter accepts
  `pl.DataFrame` natively.

**13 light-to-trivial adapters** (pass `tick_data` straight into `base_adapter.py`'s shared helpers, ≤1 simple
single-key `.groupby`, or pure `super().process_to_candles(...)` delegation — converting the 5 shared helpers above
covers most of this surface "almost for free" per the source survey):
- Enumerate the exact 13 file paths under `market_data_processing_service/app/adapters/{cefi,defi,tradfi,sports,
  prediction}/` at execution time by re-running the same file-by-file survey the source issue doc did (the doc
  names the 5 heavy adapters explicitly below; the light set is "the other 13" — re-enumerate rather than trust
  this plan's own memory of the count, since the adapter directory may have changed between 2026-08-15 and
  execution).

**5 heavy adapters — genuine groupby-based feature-engineering, no trivial 1:1 polars swap, correctness-risk on
live candle production:**
- `cefi/trades_adapter.py` (760 lines at last measurement, 8 `.groupby` calls, 5 custom feature-calc helpers —
  delay/momentum/percentile/whale/vol-clock stats; a parallel `_compute_grouped_stats_polars` path already exists
  as a partial reference to build from).
- `cefi/book_snapshot_adapter.py` (929 lines, 3 `.groupby`, HFT microstructure spread/depth/imbalance math).
- `cefi/liquidations_adapter.py` (511 lines, 6 `.groupby`).
- `sports/bucket_assignment_adapter.py` (1112 lines, session/state-grid machinery layered on `base_adapter.py`'s
  `_finalize_session_grid`/`_carry_forward_ohlc` helpers).
- `tradfi/ohlcv_passthrough.py` (430 lines — also the delegation target `tradfi/trades_adapter.py` calls into, so
  it sits on that adapter's critical path despite `trades_adapter.py` itself being a trivial delegator).

## Verification bar — non-negotiable before ship

Per the sibling engine-internal migration's own precedent (`mdps_polars_engine_cost_sharpening_2026_06_28.md`,
which needed explicit before/after benchmarking against audited targets — 10.35× wall / 6.11× peak RSS / 8.88×
retention — specifically because a naive pandas→polars port of aggregation logic is a correctness/perf risk, not a
mechanical rename):

1. **Existing adapter test suite green** for all 18 adapters, unmodified assertions (a test that had to change its
   expected VALUES to pass is a red flag, not a pass — only signature/type-level test changes are expected).
2. **Numeric-parity check** for each of the 5 heavy adapters: run the OLD pandas path and the NEW polars path
   against the same real historical shard (pick one representative day per adapter, sourced from an already-live
   bucket — no new backfill), and diff every output column. Any non-floating-point-epsilon divergence is a real bug,
   not a formatting difference — do not paper over it with a widened tolerance without root-causing it first.
3. **`quality-gates.sh --no-fix` green** on the full diff before commit (this repo's standard bar — no exception
   for "it's just a type migration").

## Proposed sequencing (subject to revision by whoever executes)

1. Convert `base_adapter.py`'s shared helpers first, keeping BOTH a pandas and polars code path behind a feature
   flag or parallel method name during the transition — this lets the 13 light adapters be verified independently
   before the 5 heavy ones are touched, without leaving the registry in an inconsistent state (the flag/dual-path
   is removed in the SAME PR that flips every adapter, not left as permanent debt — this plan's "atomic" framing
   means the finished PR has zero pandas remnants, not that the WORKING TREE can never have one mid-development).
2. Convert the 13 light adapters, verifying each against step 1's dual path.
3. Convert the 5 heavy adapters one at a time, each with its own numeric-parity check before moving to the next —
   this is where the real time and judgment goes.
4. Flip all 18 to polars-only, delete the 4 caller-side `.to_pandas()` conversions, delete the dual-path scaffold
   from step 1.
5. Full regression run + the numeric-parity report for all 5 heavy adapters, cited as this plan's evidence.

## Todos

- [ ] [BACKEND] P1. Re-enumerate the exact 13 "light" adapter file paths (the source issue doc names the 5 heavy
      ones explicitly; re-derive the light set fresh rather than trusting this plan's count, since the adapter
      directory may have drifted since 2026-08-15). Done-when: a literal file list is pasted into this plan's
      Progress Log, cross-checked against `CandleAdapterRegistry`'s full adapter enumeration (every registered
      adapter accounted for, none missed).
- [ ] [BACKEND] P1. Convert `base_adapter.py`'s 5 shared pandas helpers (`_convert_to_processing_dt`,
      `_get_local_timestamp_column`, `_series_to_datetime`, the `df`-arg `_extract_instrument_info` variant, and
      `BaseCandleAdapter.process_to_candles`'s own abstract signature) to accept `pl.DataFrame`, behind a dual-path
      scaffold per the sequencing note above. Done-when: existing `base_adapter.py` unit tests pass unmodified
      against BOTH the pandas and polars paths.
- [ ] [BACKEND] P1. Convert the 13 light adapters (from the first todo's enumeration) to the polars path. Done-when:
      each adapter's existing test suite passes unmodified.
- [ ] [BACKEND] P0. Convert `cefi/trades_adapter.py`'s 8 `.groupby` calls / 5 feature-calc helpers to polars,
      building from the existing partial `_compute_grouped_stats_polars` reference path. Done-when: existing tests
      pass AND a numeric-parity diff against one real historical shard shows zero non-epsilon divergence across
      every output column.
- [ ] [BACKEND] P0. Convert `cefi/book_snapshot_adapter.py`'s 3 `.groupby` HFT microstructure calcs to polars.
      Done-when: same two-part bar as the trades_adapter todo above.
- [ ] [BACKEND] P0. Convert `cefi/liquidations_adapter.py`'s 6 `.groupby` calls to polars. Done-when: same two-part
      bar.
- [ ] [BACKEND] P0. Convert `sports/bucket_assignment_adapter.py`'s session/state-grid machinery (built on
      `base_adapter.py`'s `_finalize_session_grid`/`_carry_forward_ohlc`) to polars. Done-when: same two-part bar.
- [ ] [BACKEND] P0. Convert `tradfi/ohlcv_passthrough.py` to polars (note: `tradfi/trades_adapter.py` delegates into
      this file, so verify the delegator's own tests too, not just this file's). Done-when: same two-part bar,
      covering both files' test suites.
- [ ] [BACKEND] P1. Flip all 18 adapters to polars-only: delete the dual-path scaffold from the `base_adapter.py`
      todo, delete the 4 caller-side `.to_pandas()` conversions in `live_workers_chain.py` (3 sites) and
      `live_workers_streaming.py` (1 site). Done-when: `grep -rn "to_pandas()" app/engine/live_workers_chain.py
      app/engine/live_workers_streaming.py` returns zero matches on this specific conversion pattern, and
      `CandleAdapterRegistry`-mediated dispatch still resolves every registered adapter (a live/paper smoke run,
      not just unit tests).
- [ ] [BACKEND] P1. Run the full `market-data-processing-service` regression suite + compile the 5 heavy adapters'
      numeric-parity reports into this plan's Progress Log as the final evidence, then `quality-gates.sh --no-fix`
      green, then ship as ONE commit/PR (per the source issue doc's own "not a per-file incremental AO todo split,
      since the ABC boundary can't be half-migrated" finding). Done-when: `market-data-processing-service@<sha>`
      cited, ancestor-verified on `live-defi-rollout`.

## Progress Log

**2026-08-22 — plan authored, `status: draft`.** T2 tranche, per operator ruling on plan dispatch (human-driven,
not AO — `mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md`'s own `[DESIGN] P3` todo is what
this plan satisfies). Scope enumerated from the source issue doc's already-completed file-by-file survey, not
re-derived from scratch. No execution attempted this session — this plan IS the scoping deliverable; flip to
`status: active` when execution begins.
