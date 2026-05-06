---
scope: [engineer, admin]
---

# Honest Absence — Downstream Handling SSOT

**Companion doc to [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md).** That doc is
the SSOT for the **write side** of honest absence (when a service emits `record_empty(empty_confirmed)`). This doc is
the SSOT for the **read / consume side** — what every downstream service (feature calculators, ML training, strategy
backtest, execution, reconciliation) does when it reads parquet for a `(shard_key, day)` whose manifest row is
`empty_confirmed`.

Codified 2026-05-06 per user direction during master-plan-audit Stage 6 conflict closeout: _"empty upstream means no
expectation of data downstream."_

---

## The principle

> Empty upstream means **no expectation of data downstream.** A `record_empty(empty_confirmed)` row is the canonical "we
> tried, source had nothing" signal. Downstream services NaN-handle the absence using whatever modeling tolerance they
> already have for missing data — they do NOT expect, demand, or fabricate placeholder rows to fill the gap.

Three rules follow:

1. **`record_empty(empty_confirmed)` is the SSOT** for "no data here." There is no second canonical signal. Writers do
   NOT also emit zero-row placeholder parquets, NaN-fill rows, or sentinel values to make the absence "easier" for
   downstream — placeholder rows are double-SSOT and banned (per
   [manifest doc § Three-category empty-output decision tree](availability-manifest-and-data-status.md#6-three-category-empty-output-decision-tree-post-2026-05-06)).
2. **Downstream services NaN-handle.** Tree-based ML, rank-based allocators, and most feature calcs natively tolerate
   1–10% missing data. Forward-fill, masking, dropna-with-min-rows-threshold, and `Optional` typing in calc inputs are
   all acceptable. Each downstream service picks the tolerance shape that fits its modeling approach — there is no
   workspace-wide "fill missing with X" rule because the right answer depends on the consumer.
3. **Holidays + market hours come from `venue_trading_calendar`, not from upstream data.** A TradFi adapter does not
   emit `record_empty` for every Saturday — `venue_trading_calendar` already says CME is closed Saturday. The pipeline
   skips the shard at orchestration time. `record_empty(empty_confirmed)` is reserved for **dates the calendar said
   should have data** but the source legitimately had none.

---

## Three causes of "no data" — different actions

When a downstream service reads parquet and gets zero rows back, the manifest tells it which case it is:

| Cause                                                                                                                                              | Manifest state                                                          | Downstream action                                                                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Calendar said no expectation** (holiday, off-hours, paused league, pre-genesis chain, pre-source-coverage date)                                  | No manifest row written; `venue_trading_calendar` says closed.          | Skip silently. Don't read, don't NaN-fill, don't fail. Pre-flight validation in the downstream service consults `venue_trading_calendar` first and never queues the shard.                                                                                                |
| **Honest empty** (source genuinely returned 0 rows for an expected-data day)                                                                       | `capture_status=empty_confirmed`; `error_reason=None`.                  | NaN-handle per the consumer's modeling tolerance. Fine for tree-based ML (XGBoost / LightGBM handle NaN natively), rank-based allocators (skip the asset for that day), forward-fill (volatility surfaces, lending rates that change slowly). NOT fine to fabricate rows. |
| **Unexpected upstream-pipeline gap** (raw said captured but a downstream layer can't read it; or no manifest row at all on a calendar-trading day) | `capture_status=captured` but reader returns 0 rows; OR no manifest row | STOP. `DependencyError(fail_fast=True)` at the pre-flight boundary. Resolve by running the upstream backfill for the missing window, NOT by `--skip-dependency-check`. Reference: [manifest doc § Honest-absence categories](availability-manifest-and-data-status.md).   |

The first two are honest absence — downstream proceeds with NaN. The third is a bug — downstream fails loud.

---

## What downstream services MUST NOT do

- **Do not write placeholder rows that look populated.** A 1440-row OHLC parquet with `open=high=low=close=NaN` is worse
  than no parquet — manifest says `captured`, downstream computes garbage features, models train on garbage, signals are
  confidently wrong. Reference incident **2026-05-05**: MDPS produced 1440-bar empty placeholder parquets per
  `(venue, data_type, day)` for years; banned in writegate Phase 2.A
  ([manifest doc § Three-category decision tree](availability-manifest-and-data-status.md#6-three-category-empty-output-decision-tree-post-2026-05-06)).
- **Do not bypass `DependencyError`** with `--skip-dependency-check` to "work around" missing upstream data. The check
  exists because the missing data is a real bug — fix upstream, do not mask.
- **Do not invent sentinel values** (`-1`, `0`, `9999`) to mark missing data. NaN is the canonical sentinel. Sentinel
  values that look like real data corrupt downstream calcs the same way placeholder rows do.
- **Do not couple two downstream calcs by writing a "missing-data filler"** somewhere in the middle of the DAG. If calc
  B needs calc A's output and A is empty for a day, B's pre-flight gate fails for that day, full stop. Don't add a
  "fallback" calc whose only job is to manufacture rows when A is empty — that's a placeholder by another name.

---

## What downstream services MAY do (tolerance patterns)

Each consumer picks the shape that matches its modeling. Common patterns:

- **Tree-based ML (XGBoost, LightGBM, CatBoost)** — NaN passes through natively. Empty-day input rows just propagate
  NaN; the model treats it as a missing-feature signal. No special handling needed.
- **Rank-based allocators** — skip the asset for that day's allocation cycle. The asset has no signal so it gets weight
  0; the allocator re-normalises across the remaining universe.
- **Forward-fill for slow-moving signals** (volatility surfaces, lending rates, staking yields) — within a bounded
  window (`max_ffill_days` per signal) so we don't carry stale values indefinitely. Bound is per-feature_group in UAC.
- **Drop-with-min-rows-threshold** — pre-flight gate at the calc level: "I need ≥N input rows to produce a meaningful
  output; below that, emit `record_empty` for my own output." Pushes the empty-confirmed up the chain honestly.
- **Per-row availability_at gating** — feature calcs respect `available_at` per input row; if too few rows are
  available_at the target horizon, the calc emits `record_empty(empty_confirmed)` for that target bar. Lookahead-bias
  guard (`LookaheadBiasError`) enforces this.

---

## Pre-flight validation (per-service responsibility)

Every downstream service has a pre-flight gate that runs BEFORE the expensive compute. The gate consults:

1. `venue_trading_calendar` — skip closed days.
2. The upstream service's manifest — confirm every `(shard_key, day)` in the input window is `captured` or
   `empty_confirmed`. If any required input is `attempted_failed` or missing on a calendar-trading day,
   `DependencyError(fail_fast=True)`.
3. The service's own min-rows / min-coverage threshold — if too few inputs are present even for honest reasons (e.g. 4
   of 5 required venues are paused-league days), emit `record_empty(empty_confirmed)` for the service's own output and
   skip the compute.

The gate is per-service because the right tolerance depends on the modeling. UTL provides the building blocks
(`check_shard_freshness`, `assert_available_at_present`); each service composes them into the gate it needs. There is no
workspace-wide gate that "handles" missing data — by design.

---

## Cross-references

- Write-side rules + the three-category decision tree:
  [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md).
- Per-source `available_at` stamping (so downstream gating works): same doc, § _per-row, write-time `available_at`_.
- Banned `_create_empty_output` placeholder method (writegate Phase 2.A workspace deletion):
  [`unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md).
- Feature calculator NaN tolerance + per-feature_group thresholds: UAC `feature_group → required_inputs` DAG SSOT.
- TradFi calendar / market-hours SSOT: `unified_api_contracts.canonical.crosscutting.venue_trading_calendar`.

---

## Anti-pattern catalogue (search for these in code review)

| Anti-pattern                                                 | Why it's wrong                                                                                             | Right shape                                                                              |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `_create_empty_output()` / `_create_full_day_empty_output()` | Emits NaN-filled placeholder rows that pass manifest cluster validation but corrupt downstream consumers.  | `record_empty(row_key, attempted_at)` — manifest learns absence; no parquet written.     |
| `df.fillna(0)` at calc input boundary                        | Conflates "value was zero" with "value was missing." Trees / rank allocators lose the missing-data signal. | Leave NaN; let the downstream model handle it natively, or drop-with-min-rows.           |
| `if df.empty: df = make_synthetic_default()`                 | Same as placeholder rows but at calc time instead of write time — same corruption, harder to grep.         | `record_empty(...)` and skip; let the consumer's NaN-handling absorb the absence.        |
| `--skip-dependency-check` to bypass missing upstream data    | Masks a real upstream bug. Manifest now lies about coverage.                                               | Run the upstream backfill for the missing window. Fix upstream, don't bypass downstream. |
| Sentinel values (`-1`, `9999`, `""`) to mark missing rows    | Indistinguishable from real values for many calcs.                                                         | NaN. Always NaN.                                                                         |

---

## Reference incidents

- **2026-05-05 MDPS empty-placeholder OHLC** — 1440 NaN-filled rows per `(venue, data_type, day)` for years; manifest
  said `captured`; downstream features computed garbage. Banned in writegate Phase 2.A.
- **2026-04-29 PLAYER_VALUES denorm** — phantom-row script `write_player_values_placeholders.py` wrote 906 zero-row
  placeholders to mask path-prefix drift. Deleted 2026-05-05.
- **2026-05-06 (this doc)** — sports `data_available_at` rename + `_create_full_day_empty_output` consumer audit
  surfaced the need for a workspace-wide downstream-consumption SSOT separate from the write-side manifest doc.
