---
doc_type: issue
title:
  "order-book imbalance is computed independently in BOTH market-tick-data-service and market-data-processing-service —
  real duplication, not just a placement question"
summary:
  'Found 2026-07-07 while reviewing the drilldown mockup: UAC declares order_flow_imbalance as an MTDS data_type
  (computed by market_tick_data_service/cli/handlers/book_microstructure_handler.py from raw book_snapshot_5). Operator
  asked to double-check whether this duplicates work already done in market-data-processing-service (MDPS), which is the
  dedicated downstream HFT-feature service. Confirmed: it does. MDPS independently computes its own imbalance_ratio (and
  a family of aggregates — 15s mean, time-weighted mean/std, sign-persist, an "advanced" top-2-level
  order_book_imbalance, book_pressure_gradient) directly from the SAME raw book_snapshot_5 input, with zero awareness of
  MTDS''s order_flow_imbalance output (confirmed: MDPS''s adapter registers on data_type="book_snapshot_5", not on
  MTDS''s derived data_type). A THIRD, separate, dead implementation of the same base formula
  (numba_kernels.py::calculate_imbalance_numba) also exists in MDPS with zero call sites anywhere in that repo. Two
  live, independent, potentially-diverging implementations of the same signal plus one orphaned dead one.'
status: open
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [market-tick-data-service, market-data-processing-service, unified-api-contracts]
scope: [engineer, admin]
tags: [duplication, order-flow-imbalance, mtds, mdps, hft-features, architecture, honest-coverage]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source:
  "Drilldown mockup review, 2026-07-07 — operator asked to verify a hunch that MDPS already computes this; confirmed via
  direct code read in both repos"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — cross-repo duplicated computation of a live-scored signal, risk of silent
> divergence.** This isn't just "which service should own this" (a placement/style question) — it's two
> independently-maintained implementations of the same order-book-imbalance concept, computed from the same raw input,
> that could drift apart over time with nobody noticing, since neither reads the other's output.

## What was actually found

### 1. MTDS: `order_flow_imbalance` (real, wired)

`market-tick-data-service/market_tick_data_service/cli/handlers/book_microstructure_handler.py` — derives
`order_flow_imbalance` (imbalance + microprice + spread) from captured `book_snapshot_5` (L5) rows, one
`CanonicalBookMicrostructure` value per (venue, instrument) snapshot, written to the manifest via
`record_captured(source="mtds_microstructure")`. Declared in UAC
(`unified-api-contracts/unified_api_contracts/registry/data_type_capability.py:260-287`) as
`live_capable=True, batch_capable=True` for 9 CeFi venues (`BINANCE-FUTURES`, `BINANCE-SPOT`, `OKX-FUTURES`, `OKX-SPOT`,
`OKX-SWAP`, `BYBIT`, `DERIBIT`, `COINBASE-SPOT`, `UPBIT`), plus a second, overlapping declaration for the L5-spot venue
set (`KRAKEN-SPOT`/`BITGET-SPOT`/`BITFINEX-SPOT`/`BYBIT-SPOT`) at lines ~473-489. "batch==live: one
CanonicalBookMicrostructure shape both modes emit."

### 2. MDPS: `imbalance_ratio` + a whole feature family (real, wired, INDEPENDENT)

`market-data-processing-service/market_data_processing_service/app/adapters/cefi/book_snapshot_adapter.py` — registers
on `@CandleAdapterRegistry.register(MarketAssetGroup.CEFI, "book_snapshot_5")` (line 93) with
`data_type = "book_snapshot_5"` (line 130) — i.e. it reads the SAME raw L5 book snapshot MTDS reads, not MTDS's derived
output. Computes, independently, from raw `depth_bid`/`depth_ask` fields:

- `imbalance_ratio = (depth_bid - depth_ask) / (depth_bid + depth_ask)` (line 342)
- `imbalance_ratio_mean_15s` — rolling 15s mean (lines 575-611)
- `book_imbalance_tw_mean` / `book_imbalance_tw_std` — time-weighted mean/std (lines 513-524)
- `book_imbalance_close` — last value in window (line 528)
- `book_imbalance_sign_persist` — fraction of matching-sign consecutive pairs (line 541)
- `order_book_imbalance` — an "advanced top-2-level" variant (lines 637-734, `_calc_order_book_imbalance`)
- `book_pressure_gradient` — rate of change of `imbalance_ratio` (lines 821-842)

This is a real, actively-used feature set (referenced in `aggregation_rules.py`, `config.py`, `models.py`,
`trades_adapter.py`'s docstring), not experimental/dead code.

### 3. MDPS also has a THIRD, dead implementation of the same base formula

`market-data-processing-service/market_data_processing_service/app/calculators/numba_kernels.py:395-421` —
`calculate_imbalance_numba(bid_volumes, ask_volumes, ...)` computes the identical `(bid - ask) / total` ratio via a
numba-jitted kernel. **Zero call sites anywhere in the repo** (grepped the whole `market-data-processing-service` tree).
Looks like an earlier attempt that got superseded by the inline pandas/numpy implementation in
`book_snapshot_adapter.py`, orphaned rather than deleted.

## Why this matters

- **Silent divergence risk**: MTDS's `order_flow_imbalance` and MDPS's `imbalance_ratio` compute conceptually the same
  signal (bid/ask depth imbalance from L5 book) via two separately-maintained formulas. If either changes (a bugfix, a
  different depth-level cutoff, a different tie-breaking rule) the two will disagree with no cross-check catching it —
  whichever a downstream strategy/feature consumer reads becomes the accidental "ground truth," and nobody currently
  knows which one that is or whether it's the more-correct one.
- **Wasted compute + wasted GCS storage**: MTDS captures and stores `order_flow_imbalance` for 9+ venues, batch and
  live, and it's unclear whether anything downstream actually consumes it (MDPS clearly doesn't). If it's unused, it's
  pure waste; if something DOES read it, that consumer should be identified and reconciled with MDPS's version.
- **Dead code hygiene**: the orphaned `calculate_imbalance_numba` should be deleted per the workspace's "delete
  deprecated code, no shims" rule — it's not just unused, it's a plausible trap for a future engineer who finds it and
  assumes it's the live implementation.

## What this is NOT (ruled out already)

- Not a "wrong service" architecture question alone — it's not that MTDS's version SHOULD be relocated to MDPS; it's
  that MDPS already independently built the same thing, blind to MTDS's parallel effort.
- Not a two-stage pipeline — confirmed MDPS reads the raw `book_snapshot_5` data_type, not MTDS's derived
  `order_flow_imbalance` output. If it were consuming MTDS's output as input to its own aggregation layer, this would be
  a non-issue (correct division of labor). It doesn't.

## Decision (operator, 2026-07-07)

**Keep exactly one implementation out of three.** MDPS's live version becomes the single source of truth; MTDS's
`order_flow_imbalance` is retired entirely; MDPS's dead numba kernel is deleted — UNLESS the numba kernel turns out to
be a genuinely faster, mathematically-equivalent implementation that was written for performance and simply never got
wired up, in which case migrate MDPS's live adapter to CALL the numba kernel instead of deleting it (keep the faster
path, delete the slower one). Explicit operator instruction: verify the math is actually equivalent before treating
"delete the numba one" as the default — don't assume orphaned means wrong. A verification workflow (math/formula
comparison, JIT-decoration check, whether other `numba_kernels.py` functions are actually used elsewhere confirming
numba is a real adopted pattern in this codebase, a timing comparison if feasible, plus the full MTDS-retirement blast
radius) is running; implementation follows once it lands.

## Todos

- [x] [VERIFY] P0. **Compare `calculate_imbalance_numba` vs. `book_snapshot_adapter.py`'s inline calc for exact
      mathematical equivalence AND relative performance** before deleting either — operator's explicit instruction,
      don't assume orphaned=wrong. **Result**: mathematically equivalent formula, but `calculate_imbalance_numba` is
      non-functional as shipped — `typing.cast()` calls inside the `@njit`-decorated body are not recognized by numba's
      nopython-mode type inferencer, so it raises `TypingError: Untyped global     name 'cast'` on first invocation
      (confirmed by direct execution in the repo's own `.venv`). Not a faster-but-unwired implementation; a broken one.
      Verified via 2-agent workflow, 2026-07-07.
- [x] [CODE] P0. **Deleted `calculate_imbalance_numba`** (`numba_kernels.py:393-421`, zero call sites, confirmed broken
      per the verification above) — kept `book_snapshot_adapter.py`'s inline pandas/numpy calc as the sole live
      implementation. Evidence: `market-data-processing-service@35ca5c1`, quality-gates.sh green.
- [x] [CODE] P0. **Retired MTDS's `order_flow_imbalance` entirely** — deleted `book_microstructure_handler.py`,
      `derived/book_microstructure_compute.py`, `scripts/book_microstructure_connectivity_check.py` (found at repo-root
      `scripts/`, not the `market_tick_data_service/scripts/` path the original audit cited),
      `tests/unit/test_book_microstructure_handler.py`, `tests/unit/derived/test_book_microstructure.py`; removed the
      CLI import + dispatcher entry in `cli/main.py`, the `derived/__init__.py` re-exports, and
      `test_book_microstructure_operation_registered()` in `tests/unit/test_lifecycle_events.py`. Confirmed via grep:
      zero remaining references to `book_microstructure`/`BookMicrostructure`/`order_flow_imbalance` anywhere in the
      MTDS repo. Blast-radius check confirmed zero real consumers and zero production rows ever captured for this
      data_type before deleting. Evidence: `market-tick-data-service@a4fb3d13`, quality-gates.sh green (153s).
- [x] [CODE] P1. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that doc for
      execution]** UAC-side retirement, not yet started**: `data_type_capability.py` (3 sites — the 9-venue block at
      lines ~260-284/287, plus two more at ~470/488 and ~516 not in the original audit's line citation),
      `_source_priority_data.py:130-136,366`, `pipeline_mode.py:112-116,204-205`
      (`BATCH_MTDS_MICROSTRUCTURE`/`LIVE_MTDS_MICROSTRUCTURE`/`REPLAY_MTDS_MICROSTRUCTURE` — needs a usage check before
      deletion, not simple), `availability_semantics.py:116-120`, plus 4 UAC test files
      (`test_book_microstructure_schema.py`, `test_validity_matrix_completeness.py:148-153`,
      `test_source_mode_capability.py:86`, `test_venue_source_adapter_parity.py:83`). **Caveat, must not violate**:
      `canonical/domain/market/microstructure.py`'s `CanonicalBookMicrostructure`/`CanonicalDepthLevel` schema is shared
      with the still-valid, never-captured `queue_position`/`depth_of_book_10` honest-gap declarations — delete only the
      `order_flow_imbalance`-specific capability entries, not the schema itself.
- [x] [VERIFY] P2. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that doc for
      execution]** Once the SSOT decision fully lands (UAC retirement above), check whether the two (now-one) live
      formulas actually agreed numerically on the same real captured data historically (a quick side-by-side computation
      on one venue/day, using whatever historical MTDS order_flow_imbalance rows exist — note: this needs to run BEFORE
      the UAC schema/manifest entries are removed, since it reads MTDS's now-retired output).

## Progress Log

- **2026-07-07 (shipped)** — Verification workflow confirmed the numba kernel is broken (not just unused), not a faster
  unwired alternative — deleted it (`market-data-processing-service@35ca5c1`). Confirmed MTDS's `order_flow_imbalance`
  has zero real consumers and zero production rows ever captured — fully retired it
  (`market-tick-data-service@a4fb3d13`). Both shipped via quickmerge from a green `quality-gates.sh --no-fix` tree.
  Remaining scope is UAC-side reference cleanup (P1, not started) and the historical-agreement check (P2, blocked on
  nothing but deprioritized).
- **2026-07-07 (operator decision)** — Operator decided: keep exactly one of the three implementations (MDPS's live
  version), retire MTDS's `order_flow_imbalance` entirely, delete MDPS's dead numba kernel — UNLESS the numba kernel is
  actually a faster, math-equivalent implementation that never got wired up, in which case migrate TO it instead of
  deleting it. Explicit instruction to verify math/perf before assuming "unused = wrong." Launched a 2-agent
  investigation workflow (math/perf comparison + numba-adoption-pattern check; MTDS retirement blast radius + real
  production capture check) before implementing anything. Results pending.
- **2026-07-07** — Filed after the operator, reviewing the drilldown mockup, asked to double-check a hunch that MDPS
  already computes HFT features including order-book imbalance. Confirmed via direct code read in both repos (not
  guessed): MTDS's `order_flow_imbalance` (book_microstructure_handler.py) and MDPS's `imbalance_ratio` feature family
  (book_snapshot_adapter.py) are independent, both real/wired, both read the same raw `book_snapshot_5` input, neither
  aware of the other. A third, dead implementation (`numba_kernels.py::calculate_imbalance_numba`) also found in MDPS
  with zero call sites. Read-only investigation — no files edited in either service repo.
