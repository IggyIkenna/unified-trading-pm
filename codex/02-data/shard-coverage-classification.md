---
doc_type: codex-ssot
title: Shard-Coverage Classification — windowed RUNNABLE / INSUFFICIENT-HISTORY / HONEST-EMPTY
summary: >-
  Windowed shard-coverage classifier SSOT — the total trichotomy RUNNABLE / INSUFFICIENT_HISTORY / HONEST_EMPTY per
  (asset_group, venue, data_type, instrument, required_window) that the honest-coverage smoke harness reads; the per-day
  bucketing (C/WE/OOW/UK/F/U + missing-row M), the decision-table verdict (any hole -> INSUFFICIENT_HISTORY),
  product-shaped required-windows, and single-walk discipline.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, features-service]
scope: [engineer, admin]
tags: [honest-coverage, manifest, smoke-test, single-walk, data-correctness, golden-window]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-06-29
authoritative_for: [windowed shard-coverage RUNNABLE/INSUFFICIENT-HISTORY/HONEST-EMPTY classification]
referenced_by:
owner:
last_reviewed: 2026-06-29
code_refs:
---

# Shard-Coverage Classification — windowed RUNNABLE / INSUFFICIENT-HISTORY / HONEST-EMPTY

> **This is the SSOT for the windowed shard-coverage classifier** that the honest-coverage smoke-test harness uses to
> decide, per `(asset_group, venue, data_type, instrument, required_window)`, whether the downstream consumer (MDPS /
> features / a smoke runner) should run, refuse-to-run, or tolerate-absence. It composes the existing
> `EMPTY_CONFIRMED_REASONS` partition from `honest-coverage-model.md` and the 4-state `capture_status` write contract
> from `availability-manifest-and-data-status.md` into one window-level verdict.
>
> **Why a separate doc:** Honest-Coverage v2 (sibling doc) measures coverage % per CELL, then rolls up by view. THIS doc
> lifts that semantic up to a WINDOW: a 91-day sports golden window, a 200-trading-day TradFi 24h-feature lookback, a
> 1-day max-daily-aggregation slice. The smoke harness reads the matrix this classifier emits.
>
> **Authority:** UAC `unified_api_contracts.canonical.crosscutting.shard_coverage_classification`. The decision-table
> pure-logic core (`classify_from_capture_counts`, `bucket_capture_status_cell`) lives there + is exhaustively tested.
> The manifest-walking wrapper (`classify_shard_coverage`) is implemented in the smoke harness
> (`e2e-testing/scripts/build_smoke/`) per the IMPLEMENT P1 todo of
> `plans/archive/2026_07/honest_coverage_smoke_harness_2026_06_28.md`.

---

## The three classes

| Class                    | Meaning                                                                                                                             | Smoke-test behaviour                                                |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **RUNNABLE**             | Continuous coverage over the required window — every day is either real data OR a legitimate within-/out-of-window absence.         | Run the path; it MUST succeed (right-edge + no-look-ahead).         |
| **INSUFFICIENT_HISTORY** | The required window is only partially covered — at least one day is `attempted_failed`, pending-`expected_unattempted`, or missing. | **REFUSE to run** — a partial window must NEVER pass smoke.         |
| **HONEST_EMPTY**         | The entire window is legitimately empty — every day is `empty_confirmed` (typed) or Tier-3-known-empty `expected_unattempted`.      | Path must tolerate absence without crashing or silent-placeholders. |

The trichotomy is **total** — every `(window, manifest projection)` lands in exactly one class.

---

## The crux — honest-empty vs insufficient-history must not collapse

The plan's hardest constraint:

> "Distinguish HONEST-EMPTY (`empty_confirmed` / `expected_unattempted`) from INSUFFICIENT-HISTORY (window only
> partially captured) — this is the crux and must not collapse."

The collapse failure mode is real and historic: a half-window producing a green smoke test because some days are "empty"
— when in fact those days are `attempted_failed` rows the harness silently treated as "absent → fine". UAC's existing
`EmptyConfirmedReason` taxonomy + `is_out_of_coverage_window` partition already separate honest absence from venue-side
failure at the CELL level. THIS doc's job is to lift that distinction to the WINDOW.

The rule the classifier enforces:

- `attempted_failed`, pending-`expected_unattempted`, **and missing rows** (writer was supposed to emit
  `expected_unattempted` but didn't — see `data-pipeline-correctness-hard-rule.md` "never silent placeholders") all
  count as **holes**. A single hole in the window → `INSUFFICIENT_HISTORY`.
- `empty_confirmed` cells — REGARDLESS of within- vs out-of-coverage-window reason — are **legitimate days**. A window
  of entirely-empty-confirmed cells → `HONEST_EMPTY`. A mix of `captured` + `empty_confirmed` (no holes) → `RUNNABLE`.

So `HONEST_EMPTY` ≠ "no data found" — it specifically means "no data found AND every day in the window has a typed
absence row proving the absence is legitimate". An untyped or absent absence routes to `INSUFFICIENT_HISTORY`.

---

## Per-day bucketing (decision table input)

The classifier projects each per-day manifest row into one of six buckets via
`bucket_capture_status_cell(capture_status, error_reason, data_type)`:

| Bucket | Mapping                                                                                                                                                                                                                                                    |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `C`    | `capture_status == "captured"`                                                                                                                                                                                                                             |
| `WE`   | `capture_status == "empty_confirmed"` AND `is_within_window_absence(error_reason, data_type)` (weekend / holiday / paused-league / postponed / source-returned-zero / …)                                                                                   |
| `OOW`  | `capture_status == "empty_confirmed"` AND `is_out_of_coverage_window(error_reason, data_type)` (pre-genesis / pre-venue-launch / not-listed / delisted / source-doesn't-cover / no-fixture / not-enough-tvl / schedule-defining FIXTURES no-match-day / …) |
| `UK`   | `capture_status == "expected_unattempted"` AND `error_reason.startswith("EXPECTED_")` — Tier-3 sentinel pre-resolved as no-fetch-needed                                                                                                                    |
| `F`    | `capture_status == "attempted_failed"`                                                                                                                                                                                                                     |
| `U`    | `capture_status == "expected_unattempted"` AND NOT `EXPECTED_*` (sentinel says "expected to exist but never tried" — the gap a backfill must close)                                                                                                        |

A seventh bucket — `M` (missing row) — is detected by the wrapper, not the per-cell function: dates inside the required
window with NO manifest row at all. The writer was supposed to materialise an `expected_unattempted` row at pre-flight
time per `availability-manifest-and-data-status.md` § Expected-universe materialisation; its absence is a writer bug we
MUST NOT silently absorb. Treated identically to `F` / `U` at the window level.

---

## Window verdict (decision table output)

Applied in priority order, total over all non-negative count tuples:

1. `F + U + M > 0` → **INSUFFICIENT_HISTORY**. Any hole forbids running. This is the safety property the harness exists
   to enforce; the report carries the first ~5 hole dates in the `rationale` field so the operator can audit-trail the
   failure.

2. `C > 0` → **RUNNABLE**. Continuous coverage — `WE` / `OOW` / `UK` days inside the window are legitimate absences
   (weekend / holiday / paused / postponed / pre-genesis / pre-launch / not-listed / delisted / source-doesn't-cover /
   no-fixture / not-enough-tvl / …). The downstream path runs; sub-path correctness is asserted by the smoke-runner via
   the Plan-4 right-edge / no-look-ahead guard.

3. otherwise → **HONEST_EMPTY**. `C == 0` AND `F == U == M == 0` — every day in the window is `empty_confirmed` (typed)
   or Tier-3-known-empty `expected_unattempted`. The downstream path MUST tolerate absence without crashing or writing
   silent placeholders.

The rule is **symmetric** in `WE` vs `OOW` vs `UK` at the WINDOW level — they all count as "this day is honestly
accounted for". The typed taxonomy is PRESERVED on the report's `WindowCaptureCounts` so consumers can drill into the
WHY without re-reading the manifest.

---

## Required-window is product-shaped

Three kinds; the source is the live registry, not magic numbers.

| Kind                    | Source                                                                                                   | Example                                                                               |
| ----------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `seasonal_continuous`   | Sports league registry season boundaries (UAC `sports.provider_league_ids` + season-start / season-end). | EPL golden window `2025-09-01 .. 2025-11-30` (91d).                                   |
| `max_daily_aggregation` | Data-type contract — paths that aggregate only WITHIN a day need 1 day.                                  | `ohlcv_24h` derived from intraday ticks.                                              |
| `lookback_n`            | `max over feature families of (lookback_periods × coarsest_timeframe)` for what consumes this shard.     | 200-period 24h feature on a 15s base ⇒ ~200 trading days (~290 calendar days TradFi). |

The required-window registry — the **DESIGN P1 todo of the smoke-harness plan** AFTER this DESIGN — encodes the
boundaries per `(asset_group, data_type)` and resolves the `lookback_n` value from the real feature config
(`features-service` configs), never from a guess.

---

## Implementation contract

- **Pure-logic core** (UAC):
  - `classify_from_capture_counts(counts: WindowCaptureCounts) -> ShardCoverageClass` — the decision table.
  - `bucket_capture_status_cell(*, capture_status, error_reason, data_type) -> Literal["C", "WE", "OOW", "UK", "F", "U"]`
    — the per-cell mapping. Both are pure, no IO, exhaustively unit-testable from integer tuples
    (`tests/unit/test_shard_coverage_classification.py`).

- **Manifest-walking wrapper** (signature in UAC, body in `e2e-testing`):
  - `classify_shard_coverage(*, asset_group, venue, data_type, instrument_id, required_window, manifest_cells, bundle_key=())`
    — walks the consolidated availability-index projection
    (`read_availability_index(bucket, columns=["date", "capture_status", "error_reason", "venue", "instrument_type", "data_type", ...])`)
    for one shard and one window, buckets each cell, detects missing-row days, delegates to
    `classify_from_capture_counts`, and returns a `ShardCoverageReport`. The body raises `NotImplementedError` today;
    the IMPLEMENT P1 todo wires the `read_availability_index` + per-shard fan-out.

- **Single-walk discipline** (per workspace CLAUDE.md / honest-coverage-model.md): the harness MUST share ONE
  bounded-column walk of `availability_index.parquet` across all shards in the MVP universe — re-walking per shard is a
  review-blocking violation.

---

## Carve-outs — what the classifier does NOT decide

- **Coverage % per cell / per AG** — that is Honest-Coverage v2 (`honest-coverage-model.md`). This classifier consumes
  the WRITER's `capture_status` + `error_reason` columns; it does NOT re-derive whether a cell SHOULD be empty — that is
  the writer / Tier-3 sentinel job per `availability-manifest-and-data-status.md` § Proof-of-honest- absence.

- **Layer-1 denominator audit** — whether `(venue, instrument_type, data_type)` is in the expected universe is
  Honest-Coverage v2 Layer-1 (`enumerate_expected_universe.py`). Out-of-Layer-1 tuples are out-of-scope for this
  classifier — the smoke harness skips them upstream.

- **Right-edge / no-look-ahead** — once a shard is RUNNABLE, the smoke-runner exercises the path and asserts the Plan-4
  guard. The classifier only decides "should we even try".

---

## Codex SSOTs

| Topic                                                        | SSOT                                                      |
| ------------------------------------------------------------ | --------------------------------------------------------- |
| 4-state `capture_status` write contract + manifest schema    | `/codex/02-data/availability-manifest-and-data-status.md` |
| `EmptyConfirmedReason` taxonomy + within-/out-of-window      | `/codex/02-data/honest-absence-downstream-handling.md`    |
| Honest-Coverage v2 (two-layer / two-view / instrument-gate)  | `/codex/02-data/honest-coverage-model.md`                 |
| Data-pipeline correctness hard rule (no silent placeholders) | `/codex/02-data/data-pipeline-correctness-hard-rule.md`   |

Plan (COMPLETE, archived 2026-07-15): `plans/archive/2026_07/honest_coverage_smoke_harness_2026_06_28.md` — all 6 todos
verified `[x]` with evidence, no open prose work. (Was "in-flight"; corrected 2026-07-15, plan-reconcile §7-residual
operator ruling A — this codex doc asserted a plan was in-flight that had in fact been done, which is live plan↔codex
drift.)
