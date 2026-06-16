---
scope: [engineer, admin]
title: Honest-Coverage Baseline (2026-05)
status: draft
created: 2026-05-07
authoritative_for:
  The May-2026 honest-coverage baseline — per-(asset_group, data_type) target coverage % + ratchet schedule. Feeds the
  workspace QG gate that prevents coverage-regression PRs from landing on `live-defi-rollout`.
referenced_by:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
related:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/02-data/expected-absence-backfill-runbook.md
last_reviewed: 2026-05-17
---

# Honest-Coverage Baseline (2026-05)

> **Status:** DRAFT — methodology + ratchet design + table schema landed 2026-05-07 (writegate Phase 5 partial).
> Per-(asset_group, data_type) numbers TBD — populated by the operator-run measurement script; see § "How baseline
> numbers are produced" below.

## Purpose

A single, dated table of per-(asset_group, data_type) coverage % that any future change must not regress. This is the
input to the QG ratchet — a CI step compares the latest manifest's honest coverage against this baseline + raises a
hard-fail if the new value is lower (within tolerance).

"Honest coverage" here = `(captured + empty_confirmed_with_reason) / expected_universe`. Pure `captured/expected`
ignores the legitimate-absence cells; that's the dishonest version we are explicitly retiring.

## Scope

- All 5 asset_groups (cefi / defi / tradfi / sports / prediction).
- All canonical data_types per asset_group as of 2026-05-07.
- Ratchet schedule: when does the baseline tighten next? (e.g. monthly +1pp until 99%).
- Excluded: data_types that don't yet exist as of baseline date (added in subsequent baselines).

## Methodology — exact formulas

For every `(asset_group, data_type)` cell in the baseline table:

- **`expected_universe_count`** = `count(unique (shard_key, day) tuples)` across the full `[earliest_valid_date, today]`
  window per the per-asset-group shard-key matrix in
  [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md). Clipping rules:
  - `SOURCE_COVERAGE_START` per `(source, data_type)` (UAC SSOT) — pre-coverage dates excluded.
  - `*_LAUNCH_DATES` per venue — pre-launch dates excluded.
  - `*_GENESIS_DATES` per chain (DeFi only) — pre-genesis dates excluded.
  - `KNOWN_COVERAGE_GAPS` per `(source, data_type, [date_range])` — known-empty gaps excluded.
  - `venue_trading_calendar` (TradFi only) — non-trading days are KEPT in the denominator (they show as
    `empty_confirmed[reason=EXPECTED_HOLIDAY|EXPECTED_WEEKEND]` per writegate Tier 3D.1).

- **`captured_count`** = `count(manifest_rows WHERE capture_status == "captured")`. Real data on disk passing the
  4-pillar write-gate (row-count > 0, NaN-ratio under threshold, schema match, cluster coverage met).

- **`empty_confirmed_with_reason_count`** =
  `count(manifest_rows WHERE capture_status == "empty_confirmed" AND error_reason IN EMPTY_CONFIRMED_REASONS - {empty_unclassified})`.
  Honest absences with a typed reason from the closed UAC `EMPTY_CONFIRMED_REASONS` set (`EXPECTED_HOLIDAY` /
  `EXPECTED_WEEKEND` / `EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PRE_GENESIS_CHAIN` /
  `EXPECTED_PRE_VENUE_LAUNCH` / `EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED` /
  `EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_REFDATA_CADENCE_CHANGE` / `EXPECTED_DEPRECATED_DATA_TYPE` /
  `SOURCE_RETURNED_ZERO`).

- **`empty_unclassified_count`** =
  `count(manifest_rows WHERE capture_status == "empty_confirmed" AND error_reason IS NULL OR error_reason == "empty_unclassified")`.
  Legacy null-reason rows pre-Tier 3D.1 reconciler back-fill. Excluded from the numerator — these are NOT honest
  absences yet, just absences pending classification. Tracked separately so the ratchet exposes back-fill progress.

- **`attempted_failed_count`** = `count(manifest_rows WHERE capture_status == "attempted_failed")`. Typed-error failures
  bucketed by `_FAILURE_PILLAR_KEYS` (timestamp_bias / malformed / cluster / lookahead_bias / nan_ratio / schema /
  empty_placeholder_backfill / missing_available_at / other) per writegate Phase 4.A.

- **`expected_unattempted_count`** = `count(manifest_rows WHERE capture_status == "expected_unattempted")`. The 4th
  capture state added 2026-05-07 evening (Phase 3.D.5) for catalog-says-this-should-exist-but-not-fetched-yet rows
  pre-populated by the v2 expected-universe enumerator. NOT in numerator — tracked for completion-of-attempt visibility
  (when this drops to 0, every expected cell has been at least attempted).

- **`honest_coverage_pct`** = `100 × (captured_count + empty_confirmed_with_reason_count) / expected_universe_count`.

- **`attempt_coverage_pct`** =
  `100 × (captured_count + empty_confirmed_with_reason_count + attempted_failed_count) / expected_universe_count`. How
  much of the expected universe has been at least attempted; complement is `expected_unattempted_count`.

- **`unclassified_drag_pct`** = `100 × empty_unclassified_count / expected_universe_count`. Tracks Tier 3D.1 back-fill
  progress; should drop to ~0% per asset_group after the reconciler completes.

**Sanity invariant**: for every `(asset_group, data_type)` cell:
`captured + empty_confirmed_with_reason + empty_unclassified + attempted_failed + expected_unattempted == expected_universe_count`.

## How baseline numbers are produced

Numbers in the baseline table below are NOT auto-generated — they are filled in once per ratchet cadence by an operator
running the measurement script on a same-region GCE VM (cross-region listing is 18× slower per the
[manifest phantom-audit recipe](./availability-manifest-and-data-status.md)).

Reference implementation: TBD `unified-trading-pm/scripts/qg/measure-honest-coverage.py` (writegate Phase 5 follow-up).
Until that script lands, the baseline table is populated manually from a same-region read of
`gs://market-data-tick-{asset_group}-${PID}/_index/availability_index.parquet` per asset_group plus the
instruments-service catalog cross-product for `expected_universe_count`.

The ratchet check (CI step) reads the latest manifest at PR-time and recomputes the cells; the baseline table is the
operator-frozen reference.

## Baseline table — schema (numbers TBD)

The table schema below names the columns the QG ratchet reads. Cells are populated as `<num>` once the operator runs the
measurement script per asset_group.

| asset_group | data_type | expected_universe_count | captured_count | empty_confirmed_with_reason_count | empty_unclassified_count | attempted_failed_count | expected_unattempted_count | honest_coverage_pct | attempt_coverage_pct | unclassified_drag_pct | baseline_date |
| ----------- | --------- | ----------------------: | -------------: | --------------------------------: | -----------------------: | ---------------------: | -------------------------: | ------------------: | -------------------: | --------------------: | ------------- |
| cefi        | TBD       |                     TBD |            TBD |                               TBD |                      TBD |                    TBD |                        TBD |                 TBD |                  TBD |                   TBD | 2026-05-07    |
| defi        | TBD       |                     TBD |            TBD |                               TBD |                      TBD |                    TBD |                        TBD |                 TBD |                  TBD |                   TBD | 2026-05-07    |
| tradfi      | TBD       |                     TBD |            TBD |                               TBD |                      TBD |                    TBD |                        TBD |                 TBD |                  TBD |                   TBD | 2026-05-07    |
| sports      | TBD       |                     TBD |            TBD |                               TBD |                      TBD |                    TBD |                        TBD |                 TBD |                  TBD |                   TBD | 2026-05-07    |
| prediction  | TBD       |                     TBD |            TBD |                               TBD |                      TBD |                    TBD |                        TBD |                 TBD |                  TBD |                   TBD | 2026-05-07    |

> **Per-data_type rows are added by the measurement script.** The seed table above carries one row per asset_group as a
> placeholder; the real table will be ~80-150 rows total covering every canonical `(asset_group, data_type)` pair as of
> 2026-05-07. The full set of canonical data_types per asset_group is enumerated in
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) § "Per-asset-group shard-key
> matrix".

## Ratchet schedule

**Tolerance band for regression noise:** ±0.5pp default.

A PR's manifest must satisfy, for every `(asset_group, data_type)` cell:

- `new.honest_coverage_pct >= baseline.honest_coverage_pct - 0.5pp` — hard-fail QG on regression beyond tolerance.
- `new.unclassified_drag_pct <= baseline.unclassified_drag_pct + 1.0pp` — softer band; back-fill regressions are caught
  but a small uptick during a Tier 3D.1 reconciler re-run is tolerable.
- `new.attempted_failed_count - baseline.attempted_failed_count` is reported but NOT gated — failure spikes need
  alerting (writegate Phase 4 — alerting plan), not a merge gate.

**Cadence:** monthly review (operator-driven, written into `unified-trading-pm/.github/ISSUE_TEMPLATE/` calendar). At
each review:

1. Re-run the measurement script.
2. Compare against the previous baseline.
3. For each `(asset_group, data_type)` whose `honest_coverage_pct` improved by ≥1pp, ratchet the baseline up to
   `floor(observed - 0.5pp)`. Cells stuck at the previous baseline stay frozen.
4. For cells that regressed structurally (retired venue, deprecated data_type, etc.), explicitly relax via the override
   procedure below — never silent rollback.

**Long-term floor:** 99% honest coverage per `(asset_group, data_type)` is the workspace-wide goal. Once a cell reaches
99% it's frozen there until a deliberate scope change (new venue / new data_type / contract change) requires a relax.

## QG ratchet implementation (outline)

CI step `qg/honest-coverage-ratchet.sh` (writegate Phase 5 follow-up):

1. Discover the `live-defi-rollout` HEAD's manifest snapshot per asset_group (read-only, cached).
2. For every cell in this baseline doc's table, compute the same formulas above against the HEAD manifest.
3. Apply the tolerance band per cell. Hard-fail QG if any cell regresses beyond tolerance.
4. Emit a JSON report (`/tmp/honest-coverage-delta.json`) of all per-cell deltas — surfaced in the GHA log so the PR
   author sees exactly which cell tripped the gate.

The ratchet is a passive safety net — its job is to catch unintentional regressions. Intentional regressions (e.g.
retiring a venue, deprecating a data_type) require the override procedure.

## Override procedure

When a legitimate, intentional regression is needed:

1. Open a PR titled `coverage-relax(<asset_group>/<data_type>): <one-line reason>`.
2. Edit the affected cell(s) in this doc, lowering the baseline to the new floor.
3. Add the rationale + dated entry to the "Override log" section below.
4. Tag the operator (Ikenna / Harsh) for review — overrides are NOT auto-approved by CI.
5. After merge, the next PR's QG check runs against the relaxed baseline.

The override log is the durable record of why every baseline tightening or relaxation happened — auditable by future
agents reading the doc cold.

### Override log

_(empty as of 2026-05-07 baseline draft — first entries land when an actual override is needed)_

## Open questions

- ~~What is the tolerance band for "regression noise" — 0.1pp? 0.5pp? Per-asset-group different?~~ **RESOLVED
  2026-05-07**: ±0.5pp uniform default. Per-asset-group variants TBD if any cell proves chronically noisy.
- Do we baseline + ratchet at the (asset_group, data_type) granularity or aggregate per asset_group? — **RECOMMEND
  per-data-type** (current schema). Aggregate would hide regressions in low-volume data_types.
- How is the expected universe sized exactly — current declared instrument count, or instrument count at baseline date
  frozen? **RECOMMEND date-frozen** at baseline_date so a PR adding 100 new instruments doesn't artificially drop
  coverage on next QG run. Override procedure handles deliberate universe expansion.
- Does the ratchet account for venue/source-coverage-start clipping, or is that already baked into `expected_universe`?
  **BAKED IN**: per the methodology section, the denominator is clipped at measurement time using UAC
  `SOURCE_COVERAGE_START` / `*_LAUNCH_DATES` / `*_GENESIS_DATES` / `KNOWN_COVERAGE_GAPS`. The ratchet reads the
  post-clip denominator.

## Cross-references

- **Plan(s) implementing this:**
  [`writegate_honest_coverage_endtoend`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) Phase 5.
- **Related codex SSOTs:** [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md),
  [`honest-absence-downstream-handling`](./honest-absence-downstream-handling.md),
  [`expected-absence-backfill-runbook`](./expected-absence-backfill-runbook.md).
- **Code:** TBD ratchet check — `unified-trading-pm/scripts/qg/measure-honest-coverage.py` (measurement) +
  `unified-trading-pm/scripts/qg/honest-coverage-ratchet.sh` (CI gate).
