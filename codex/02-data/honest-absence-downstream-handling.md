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

## Per-source `available_at` stamping helpers (UTL)

Downstream gating only works if every write-side parquet carries a per-row `available_at` equal to when the live
pipeline would actually have had that row — never midnight UTC, never read-time-derived (per the CLAUDE.md
"`available_at` is per-row, write-time, equal to live-pipeline-arrival" rule). The stamping is centralised in
`unified_trading_library.availability_stamping` so every adapter / calculator uses the same per-source rule:

| Helper                                       | Source / data_type                                              | `available_at` rule                                                                                                                                                                                                                         |
| -------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `stamp_available_at_lineups`                 | sports lineups                                                  | `kickoff − 60 min` (conservative — official lineups publish ~T-60min, sometimes earlier; using T-60 clips earlier-leak rows)                                                                                                                |
| `stamp_available_at_injuries`                | sports injury reports                                           | per-row injury-report / occurrence time (so a feature for fixture F sees only injuries reported before F's kickoff — and only from prior fixtures)                                                                                          |
| `stamp_available_at_odds_snapshot`           | sports pre-match odds                                           | per-row snapshot publication time (`bm_time`) — opening lines days before kickoff, closing lines at kickoff; never derived from the fixture date                                                                                            |
| `stamp_available_at_post_match` / `_cascade` | sports post-match (xG, fixture_stats, sfi_progressive, results) | `match_end_time`; `_cascade` tries candidate match-end columns in source-priority order (api_football native → SFI progressive freeze → footystats/understat) then falls back to `kickoff + 120 min` (conservative — never under-estimates) |
| `stamp_available_at_event_time`              | weather forecasts                                               | forecast-**issue** time (distinct from the forecast-target time) — pass the issue-time column                                                                                                                                               |
| `stamp_available_at_cefi_tick`               | CeFi / DeFi / TradFi tick data                                  | tick timestamp + `emission_latency_ms_for_source(source)` (the source-priority emission latency, NOT the slower batch-archive fetch latency)                                                                                                |
| `stamp_available_at_offset` / `_explicit`    | generic                                                         | `kickoff + offset` (rare; e.g. SFI `kickoff + timer_seconds`) / fixed point-in-time snapshot                                                                                                                                                |

`record_captured` calls `assert_available_at_present` internally — a parquet missing or with null `available_at` →
`LookaheadBiasError`. The sports stamp helpers were lifted to UTL by `wave3x_residual_ssots_2026_05_08.md` Track E; the
features-sports / MTDS-sports-adapter wire-in of these helpers at the calculator emission boundaries is the per-service
half (Harsh slot 4 MTDS sports adapter stamping + Ikenna slot 3 available_at Phase 1 — see `plans/active/issues/` for
the MTDS-slice sports `available_at` wiring issue doc).

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
  [`unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md).
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

---

## Reason taxonomy (codified 2026-05-07 — operator direction)

Earlier sections describe **3 causes** with binary `error_reason` (None vs typed-error string). Operator direction
2026-05-07: the manifest IS the single source of truth for "what's there + why it's not." Downstream consumers should
not have to consult `venue_trading_calendar` separately to interpret a missing row. Every `(shard_key, day)` tuple in
the expected universe gets a manifest row, and the row's `error_reason` carries one of these structured codes:

### Manifest `capture_status` × `error_reason` matrix

| `capture_status`   | `error_reason`                                    | What it means                                                                                                                                                                                                                                                                                                                                                                                  | Parquet on disk?                                               |
| ------------------ | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `captured`         | (empty)                                           | Full good data; row count matches expected; OHLC/required cols populated; cluster-coverage met for bundled shards                                                                                                                                                                                                                                                                              | YES — full parquet                                             |
| `empty_confirmed`  | `EXPECTED_HOLIDAY`                                | TradFi non-trading day per `venue_trading_calendar`; CME closed for Christmas, etc.                                                                                                                                                                                                                                                                                                            | NO — no parquet                                                |
| `empty_confirmed`  | `EXPECTED_WEEKEND`                                | TradFi/CME weekend; expected closed                                                                                                                                                                                                                                                                                                                                                            | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PAUSED_LEAGUE`                          | Sports league not in season; UAC `KNOWN_COVERAGE_GAPS` payload                                                                                                                                                                                                                                                                                                                                 | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PRE_SOURCE_COVERAGE_START`              | Date is before `SOURCE_COVERAGE_START` for this `(source, data_type)`; data didn't exist back then                                                                                                                                                                                                                                                                                             | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PRE_GENESIS_CHAIN`                      | DeFi `chain` didn't exist on this date (e.g. Solana pre-2020-03)                                                                                                                                                                                                                                                                                                                               | NO                                                             |
| `empty_confirmed`  | `EXPECTED_INSTRUMENT_NOT_LISTED`                  | Instrument's `market_created_at` > date (predictions, dated futures pre-listing, etc.)                                                                                                                                                                                                                                                                                                         | NO                                                             |
| `empty_confirmed`  | `EXPECTED_INSTRUMENT_DELISTED`                    | Instrument's `delisted_at` ≤ date (CeFi delisted pairs, dated futures post-expiry, prediction post-settlement)                                                                                                                                                                                                                                                                                 | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PARTIAL_HALF_DAY`                       | TradFi half-day session (Black Friday CME, etc.); fewer rows than full day but the rows present are good                                                                                                                                                                                                                                                                                       | OPTIONAL — partial parquet OR no parquet; manifest tells truth |
| `empty_confirmed`  | `EXPECTED_PRE_VENUE_LAUNCH`                       | Date is before venue's `launch_date` per UAC `venue_launch_dates` registry (20 CeFi + 2 Prediction venues). Shipped UAC@`ac218dc` 2026-05-07. Distinct from `EXPECTED_PRE_GENESIS_CHAIN` (DeFi chain genesis) and `EXPECTED_PRE_SOURCE_COVERAGE_START` (source archive start).                                                                                                                 | NO                                                             |
| `empty_confirmed`  | `EXPECTED_OUTSIDE_TRADING_HOURS`                  | Intra-day timestamp falls OUTSIDE the venue's published trading hours for that day. Distinct from whole-day non-trading (HOLIDAY/WEEKEND) and short-session (PARTIAL_HALF_DAY).                                                                                                                                                                                                                | NO                                                             |
| `empty_confirmed`  | `EXPECTED_OUTSIDE_TRANSFER_WINDOW`                | Transfer-event lookback window outside the operator-configured transfer window (DeFi staking / bridging refdata).                                                                                                                                                                                                                                                                              | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PRE_SEASON`                             | Sports — day is before season `schedule_announced_at` per league registry. Distinct from `EXPECTED_PRE_SOURCE_COVERAGE_START` (per-source archive start). Operator msg 9 audit dim #6.                                                                                                                                                                                                         | NO                                                             |
| `empty_confirmed`  | `EXPECTED_POST_SEASON`                            | Sports — day is after season-end (playoff close + offseason). Mirror of `EXPECTED_PRE_SEASON`. Operator msg 9 audit dim #6.                                                                                                                                                                                                                                                                    | NO                                                             |
| `empty_confirmed`  | `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`           | Sports — operator-documented "this source does not cover this league" (e.g. Odds API has no MLB). Distinct from `EXPECTED_PAUSED_LEAGUE` (league exists but is paused). Wave 3.X dim #7.                                                                                                                                                                                                       | NO                                                             |
| `empty_confirmed`  | `EXPECTED_DEPRECATED_DATA_TYPE`                   | Data_type retired at a known date; rows after that date are expected empty. Plan: `manifest_migration_master_2026_05_07.md` § C.1.                                                                                                                                                                                                                                                             | NO                                                             |
| `empty_confirmed`  | `EXPECTED_REFDATA_CADENCE_CHANGE`                 | Reference-data refresh cadence changed at a known date (e.g. daily → weekly). Distinct from `EXPECTED_DEPRECATED_DATA_TYPE`. Plan: `manifest_migration_master_2026_05_07.md` § C.11.                                                                                                                                                                                                           | NO                                                             |
| `empty_confirmed`  | `EXPECTED_KNOWN_SOURCE_GAP`                       | Documented mid-history source gap that doesn't fit the venue-launch / source-coverage-start / pre-genesis primitives. Reference uses: **VIX 15m gap** (`2025-11-13` → `today − 60d`; Yahoo rolling window can't reach + Barchart preload stopped 2025-11-12) + sports `KNOWN_COVERAGE_GAPS` ranges (operator-documented multi-day outages / paused windows). Shipped UAC@`174f401` 2026-05-11. | NO                                                             |
| `empty_confirmed`  | `SOURCE_RETURNED_ZERO`                            | Source called, returned legitimately empty (path A from old 3-category model); data was expected but the upstream had nothing                                                                                                                                                                                                                                                                  | NO                                                             |
| `attempted_failed` | `UpstreamTimestampBiasError(...)`                 | Path B — source returned ticks ALL outside requested day after interval filter; upstream partition mislabeled                                                                                                                                                                                                                                                                                  | NO                                                             |
| `attempted_failed` | `MalformedTickFieldError(...)`                    | Path C — rows in window but downstream calc dropped all due to NaN/malformed source field                                                                                                                                                                                                                                                                                                      | NO                                                             |
| `attempted_failed` | `ClusterCoverageError(missing=..., observed=...)` | Bundled shard partial: observed clusters < expected per UAC registry                                                                                                                                                                                                                                                                                                                           | NO                                                             |
| `attempted_failed` | `MissingAvailableAt`                              | Parquet was written but lacks `available_at` column or has nulls — would corrupt LookaheadBiasError downstream gates                                                                                                                                                                                                                                                                           | (legacy parquet may exist; reconciler reflips manifest)        |
| `attempted_failed` | `EmptyPlaceholderBugBackfill`                     | Reconciler-flipped historical row — pre-fix MDPS wrote 1440-NaN placeholder; reconciler caught it                                                                                                                                                                                                                                                                                              | (legacy parquet exists; reconciler doesn't delete it)          |
| `attempted_failed` | `RAW_TICK_PARTITION_MISMATCH`                     | MTDS-side partition validator detected upstream-bug at write time                                                                                                                                                                                                                                                                                                                              | NO                                                             |

### Two principles this codifies

1. **Manifest is the SSOT for absence + reason.** Downstream consumers do NOT re-derive "is this day expected to have
   data?" from `venue_trading_calendar` separately — they read the manifest row and trust the `error_reason`. The
   orchestrator's pre-flight gate populates the manifest with the expected-absence reason at queue time so the row
   exists for every `(shard_key, day)` in the expected universe.
2. **No parquet for bad/partial-expected days.** Even when the data is "good but partial" (half-day trading session),
   the cleanest write is NO parquet + manifest row with `EXPECTED_PARTIAL_HALF_DAY` reason. The downstream consumer sees
   the manifest, decides what to do. (Optional exception: writers MAY persist a partial parquet with the actual short
   row count IF the downstream consumer needs the rows directly — but the manifest reason is still the gate and the
   parquet schema is honest about its short row count, no NaN-fill to "complete" the day.)

---

## Per-service consumer-class audit (2026-05-07 — operator direction)

Different services have different right-answers when they read a manifest row that says `empty_confirmed[reason=...]` or
`attempted_failed[reason=...]`. The audit below is the workspace SSOT for per-service handling. Service code MUST match
this contract.

| Consumer class                                      | Service examples                                                                                                 | `empty_confirmed[EXPECTED_*]` action                                                                                                                                               | `empty_confirmed[SOURCE_RETURNED_ZERO]` action     | `attempted_failed[reason]` action                                                                                                       |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Execution (live trade emission)**                 | execution-service, signal-broadcast                                                                              | **Skip the trade.** Don't trade on an absence we expected. Log + emit `EXECUTION_SKIPPED` event.                                                                                   | Skip the trade. Same reasoning.                    | **Skip the trade + alert.** `attempted_failed` is a real upstream issue; don't trade through it.                                        |
| **ML training (continuous-series)**                 | ml-training-service                                                                                              | **NaN-fill the row** to keep the training-window contiguous. Tree-based ML handles NaN natively.                                                                                   | NaN-fill same as above.                            | NaN-fill BUT add a `data_quality_flag=ATTEMPTED_FAILED` column so the model can learn to discount attempted-failed regions if it wants. |
| **ML inference (live feature compute)**             | ml-inference-service                                                                                             | NaN-fill the row before model `predict()` if the feature is in the model's feature list.                                                                                           | NaN-fill same as above.                            | **Block the inference** for that timestamp; emit `INFERENCE_SKIPPED` event. Live model cannot infer through gaps.                       |
| **Features — rolling window (≥2 sample window)**    | features-volatility (rolling vol), features-cross-instrument (rolling spread), features-onchain (lending APY MA) | **Keep window size, adjust denominator.** 20-day MA over a window with 2 expected-missing days = mean of 18 valid samples; window stays 20. Surface `n_valid` as a sibling column. | Same as expected: keep window, adjust denominator. | Skip the calc for that target timestamp; emit `record_empty(...)` for the calc's own output row.                                        |
| **Features — same-day single-sample**               | features-cross-instrument (today's basis), features-onchain (today's lending rate snapshot)                      | **NaN-fill the calc output row** OR emit `record_empty(...)` for the calc's own output. Per-calc choice; document in calc docstring.                                               | Same.                                              | Emit `record_empty(...)` for the calc's own output. Don't fabricate.                                                                    |
| **Features — cross-instrument (require both legs)** | features-cross-instrument (paired-price-dispersion, cross-venue arb)                                             | If EITHER leg is `empty_confirmed`, emit `record_empty(reason=LEG_ABSENT_<which_leg>)` for the calc's own output.                                                                  | Same as expected.                                  | If EITHER leg is `attempted_failed`, propagate the failure: emit `record_failed(reason=UPSTREAM_LEG_FAILED)`.                           |
| **Strategy (backtest replay)**                      | strategy-service                                                                                                 | Treat as "no signal that day"; allocator skips the asset for that allocation cycle.                                                                                                | Same.                                              | Same as expected absence; backtest mode is forgiving (it's reconstructing history).                                                     |
| **Strategy (live)**                                 | strategy-service (live mode)                                                                                     | Allocator skips the asset; rebalance proceeds across the remaining universe.                                                                                                       | Same.                                              | **Block trade emission** for assets affected; alert. Live mode is unforgiving.                                                          |
| **Reconciliation (batch-vs-live)**                  | batch-live-reconciliation-service                                                                                | Both sides should agree on the absence; if one side has data and the other doesn't with the same reason, flag the discrepancy.                                                     | Same — both sides should agree.                    | Both sides should also agree; if only one side flags `attempted_failed`, the bug is on that side.                                       |
| **Position / Risk monitor**                         | position-balance-monitor-service, risk-and-exposure-service                                                      | No-op (these services consume position events, not feature parquets).                                                                                                              | No-op.                                             | Alert if it would block a downstream calc the position depends on.                                                                      |

### Worked example — 20-day moving average with 2 expected-missing days

Operator-given example (2026-05-07): "If you have a 20-day moving average of one-day samples and 2 days are missing,
then you have an average of 18 numbers, because the 2 missing are expected to be missing while keeping the 20-day
window."

Implementation (features-onchain rolling-APY calc, illustrative):

```python
def rolling_apy_20d(daily_apy: pd.Series, manifest: ManifestReader) -> pd.Series:
    """20-day rolling APY MA. Adjusts denominator for expected-missing days."""
    out = []
    for target_day in daily_apy.index:
        window_start = target_day - timedelta(days=20)
        window = daily_apy.loc[window_start:target_day]
        # Reads manifest reasons for each day in window
        reasons = [manifest.get_reason(day, shard_key) for day in window.index]
        valid_mask = [
            (r != "EXPECTED_HOLIDAY"
             and r != "EXPECTED_WEEKEND"
             and r != "EXPECTED_PAUSED_LEAGUE"
             and not r.startswith("attempted_failed"))
            for r in reasons
        ]
        valid_window = window[valid_mask]
        if len(valid_window) < MIN_VALID_DAYS_FOR_MA:
            out.append((target_day, np.nan, len(valid_window)))  # not enough valid samples
        else:
            out.append((target_day, valid_window.mean(), len(valid_window)))
    return pd.DataFrame(out, columns=["day", "ma_20d", "n_valid"]).set_index("day")
```

Key shape: the calc output carries an `n_valid` sibling column so downstream consumers can see the denominator used.
That's how absence flows transparently through the DAG without corrupting downstream model trust in the value.

### Worked example — 1-day MA over a single missing day

Operator-given example: "If you have a one-day moving average for one day and the one day is missing, expected missing,
then you can't do much more than fill in that in."

For same-day single-sample calcs: there's no rolling-window denominator adjustment available. The right shape: the calc
emits `record_empty(reason=NO_INPUT_AVAILABLE)` for its own output row that day. Downstream consumers see the absence in
the calc's manifest and apply their own consumer-class rule (NaN-fill for ML, skip for execution, etc.). Don't fabricate
a value.

---

## Reader-side fallback for legacy rows (codified 2026-05-07 — operator gap finding)

Phase 2.E.1 ships UTL `record_empty(reason=...)` for NEW writes. Existing manifest rows have `error_reason=None` for
honest empty (or no row at all if calendar-pre-skipped). Without retrospective backfill (writegate Phase 3.D),
historical reads land on rows the consumer can't classify.

**The contract every consumer service implements** (defensive, runs even after Phase 3.D backfill — covers race
conditions during migration + future-proofs against new asset_groups whose backfill hasn't run):

```python
def get_reason(row_key: dict, day: date) -> str:
    """Return the canonical EMPTY_CONFIRMED_REASONS code for this row.

    Reads the manifest reason if present; falls back to calendar/coverage SSOT
    classification if the row is legacy (error_reason empty) or missing entirely.
    """
    row = manifest.lookup(row_key)
    if row is not None and row.error_reason:
        return row.error_reason  # new writers populate this — fast path
    # Legacy fallback: classify from calendar / coverage SSOTs
    return classify_legacy_empty_row(row_key, day)
```

`classify_legacy_empty_row(row_key, day)` consults the same SSOTs the writer would have:

1. **`venue_trading_calendar`** — TradFi closed-day → `EXPECTED_HOLIDAY` or `EXPECTED_WEEKEND`.
2. **`SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START`** — date < source coverage →
   `EXPECTED_PRE_SOURCE_COVERAGE_START`.
3. **`KNOWN_COVERAGE_GAPS`** — sports paused leagues → `EXPECTED_PAUSED_LEAGUE`.
4. **DeFi chain-genesis lookup** — date < chain genesis → `EXPECTED_PRE_GENESIS_CHAIN`.
5. **Instrument lifecycle** (instruments-service `MARKET_LIFECYCLE` for predictions, `delisted_at` for CeFi/TradFi):
   - day < `market_created_at` → `EXPECTED_INSTRUMENT_NOT_LISTED`
   - day ≥ `delisted_at` (or `settlement_time` for predictions) → `EXPECTED_INSTRUMENT_DELISTED`
6. **Default**: `SOURCE_RETURNED_ZERO` — the writer attempted, source had nothing, no calendar/coverage exception
   applied.

This makes the consumer code uniform across legacy AND new manifest rows. Writers populate the manifest reason upfront
so the fast path is just a row read; the fallback exists for in-migration coverage and as a defensive guarantee that
consumers always have an answer.

### What this changes vs. the original codex § "Three causes of no data" matrix

The original matrix said "no manifest row written; `venue_trading_calendar` says closed → skip silently." Per operator
direction 2026-05-07 we now want the manifest to BE the SSOT, so:

- **Going forward**: writers emit `record_expected_empty(reason=EXPECTED_HOLIDAY)` for calendar-closed days instead of
  pre-skipping.
- **For legacy data** (until Phase 3.D backfill runs): consumer-side `classify_legacy_empty_row(...)` derives the reason
  on the fly from the same SSOTs.
- **Either way**, the consumer's downstream behaviour is the same — the lookup is just slightly slower for legacy rows.
  The audit rule per consumer class (NaN-fill / skip / adjust denominator) doesn't care whether the reason came from
  manifest or fallback.

Cross-reference: writegate Phase 3.D `reconcile_expected_absence_reasons.py` per asset_group performs the retrospective
backfill so the slow path eventually empties out per asset_group.

### Reconciler chain for legacy `error_reason` (the three passes)

There are now THREE reconciler passes over the manifest's `error_reason` column, run in order, each in
`instruments-service/scripts/`:

1. **`reconcile_blank_error_reason_rows.py`** (writegate Phase 3.D.5 Wave 2.M, 2026-05-07) — stamps the _initial_ reason
   on legacy `empty_confirmed` rows that had a **blank** `error_reason`, via `classify_blank_reason_row`. Most rows land
   on `SOURCE_RETURNED_ZERO` (the honest-absence default) or, for cefi/defi/tradfi at instrument-day grain, flip to
   `attempted_failed`.
2. **`reconcile_expected_absence_reasons.py`** (writegate Phase 3.D, the per-asset-group retrospective backfill above) —
   same SSOT classifier, walks the same null-reason set; the canonical retrospective pass.
3. **`reconcile_legacy_blank_to_typed_reason.py`** (Wave 3.X Track C, 2026-05-11) — the _second-pass upgrader_. Walks
   `empty_confirmed` rows whose `error_reason` is one of the pass-1/2 _defaults_ (`SOURCE_RETURNED_ZERO` /
   `EXPECTED_INSTRUMENT_NOT_LISTED`) and re-runs each through `classify_blank_reason_row` — now that the finer SSOTs
   exist (`HALF_DAY_SESSIONS` / `VENUE_SESSION_HOURS` from UAC@bdc84ed, `UNDERSTAT_COVERED_LEAGUES` / per-country
   transfer windows / FootyStats season bounds from UAC@7c8b5ad) — upgrading rows where the classifier now returns a
   _more-specific_ `EXPECTED_*` (never downgrades, never flips `capture_status`). **This is the canonical mechanism for
   legacy-reason upgrades whenever a new `EXPECTED_*` reason is added to UAC `EmptyConfirmedReason` or a new
   fine-grained SSOT lands** — re-run it (scan-only first, then `--apply-flips` after CSV review). Same shape as the
   others (`--asset-group`, `--apply-flips`, `--max-flips-per-run`, `MANIFEST_PER_VM_SHARDS`+`VM_NAME`, `RECONCILER_*`
   events, CSV audit, per-VM-shard write so the consolidator merges last-writer-wins).

(2026-05-11 dry-run on the 5 production manifests: 0 upgrades surfaced on the current manifest data — the pass-1/2
sweep + the orchestrator's calendar-pre-skip already classified most rows; the new branches need finer per-row columns
that current rows mostly lack. The reconciler is ready for whenever those columns are written / a new reason is added.)

---

## MDPS downstream consumption contract (4-state routing)

> Plan: `expected_unattempted_propagation_chain_2026_05_12.md` Phase 2. Codified 2026-05-12.

When MDPS reads the upstream MTDS manifest for a given (asset_group, date, data_type, timeframe) shard, it routes based
on `capture_status`:

| Upstream MTDS `capture_status` | MDPS behaviour                                       | Why                                                                                               |
| ------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `captured`                     | Process normally                                     | Data exists — proceed to candle aggregation                                                       |
| `empty_confirmed` + any reason | Write **zero-volume / forward-fill-last-price** bars | Confirmed no trades; price continuity preserved; not a data quality issue                         |
| `attempted_failed`             | Write **NaN** (do NOT forward-fill)                  | Bad missing — data may exist but fetch failed; downstream must not treat silence as zero-activity |
| `expected_unattempted`         | Write `expected_unattempted` in MDPS manifest + skip | Upstream said skip — MDPS propagates honest absence downstream                                    |

**Implementation** (MDPS `market_data_processing_service/app/core/`):

- `canonical_writer.record_expected_unattempted_for_shard()` — writes the manifest row directly via
  `ManifestWriter.record_expected_unattempted`. Called with `instrument_id=""`, `venue=""` (per-instrument info
  unavailable at category-level skip time). Shard-level failure isolation: exceptions caught + logged, never propagated.
- `CandleOrchestrationService._record_expected_unattempted_on_skip()` — iterates `data_types × timeframes`, calls
  `record_expected_unattempted_for_shard` for each combo. Called from `process_category` at the `deps_ok==False`
  early-return point.

**Cross-references**: writegate plan Phase 2.A (4-state routing in `_emit_status_for_shard`) ·
`availability-manifest-and-data-status.md` § "4-state capture_status" ·
`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`.

---

## Zero-activity-bar shape (case-D design — implementation deferred post-cutover)

> **Status**: audit complete (2026-05-11, `wave3x_residual_ssots_2026_05_08.md` Track D); **implementation deferred
> post-2026-05-23 cutover** — requires a NEW UTL `zero_activity_bars` primitive + `instrument_catalog` threaded at
> adapter construction (writegate Phase 3.D.5 Wave 2/3, "pending"). This section is the design stub so consumers know
> what shape to expect when case-D ships. Reference audit: `plans/archive/issues/wave3x_track_d_findings_2026_05_11.md`.

Case-D fires when: source returned 0 rows AND `instrument_catalog` says the instrument is alive on that date AND the
date falls within the venue's published trading hours. The adapter writes **carry-forward bars** (not NaN-fill) and
calls `record_captured` so downstream consumers see a fully-populated row. The absence of real ticks is transparent via
a `zero_activity=True` column on each bar.

### Carry-forward rule per data_type

| data_type                                                                                                                       | Zero-activity bar shape                                                                                                                                            | `available_at`                                      |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| `ohlcv_1m` / `ohlcv_15m` / `ohlcv_1h` / `ohlcv_24h`                                                                             | O=H=L=C = prior last-trade-price (LTP carry-forward), `volume=0`, `trade_count=0`, `zero_activity=True`                                                            | Interval close time (`window_close` for the candle) |
| `trades`                                                                                                                        | Zero-row parquet (empty DataFrame, 0 rows); `record_captured(row_count=0)`; no rows on disk is the honest shape — a zero-activity day has no individual trades     | Interval close time                                 |
| `book_snapshot_5` / `book_snapshot_25`                                                                                          | Carry-forward last known bid/ask levels (all N levels); `bid_size_*=0`, `ask_size_*=0`, `zero_activity=True` (quoted spread present but no resting volume)         | Snapshot window close                               |
| `derivative_ticker`                                                                                                             | Carry-forward last known `open_interest`, `mark_price`, `index_price`; `funding_rate=0` (no funding accrual on zero-activity period); `zero_activity=True`         | Interval close time                                 |
| `options_chain` / `futures_chain`                                                                                               | Carry-forward last known bid/ask across ALL active strikes/expiries (see volatility-smile note below); `volume=0`, `open_interest` unchanged, `zero_activity=True` | Interval close time                                 |
| DeFi continuous series (`lst_rates`, `staking_yields`, `lending_indices`, `oracle_prices`, `vault_share_price`, `perp_funding`) | Carry-forward last known rate/price; `zero_activity=True`                                                                                                          | Block-close time                                    |
| Prediction market depth / CLOB (`market_depth`, `order_book`)                                                                   | Carry-forward last known mid/best-bid/best-ask; `zero_activity=True`                                                                                               | Snapshot window close                               |

### The volatility-smile constraint (operator-flagged)

Every active strike must be visible even on zero-volume days for cross-instrument analysis. A zero-volume options bar
that disappears from the grid is worse than a carry-forward row because:

1. `features-service cross_instrument` computes cross-strike spreads (basis, put-call parity, skew) across the full
   smile. A missing strike silently widens the observable grid and corrupts skew estimates.
2. ML training on vol-surface features expects a fixed-width grid per day. A narrower grid on quiet days is a
   model-corruption risk even if the missing entries are genuinely zero-volume.

Therefore: for `options_chain`, a zero-volume day writes a carry-forward bar for **every strike that was in the active
catalog on that date**. The `zero_activity=True` column lets downstream consumers optionally drop or down-weight these
rows.

### What the implementation needs (Wave 3.M)

When the case-D implementation ships (writegate Phase 3.D.5 Wave 2/3, post-2026-05-23), it needs:

1. **UTL primitive
   `zero_activity_bars(last_snapshot: pd.DataFrame, data_type: str, interval_close: datetime) -> pd.DataFrame`** —
   per-data_type carry-forward logic per the table above; raises `ValueError` for unknown data_type.
2. **`instrument_catalog` threaded at adapter construction** — adapter checks `catalog.is_alive(instrument_id, day)`
   before deciding case-A vs case-D.
3. **`record_captured(df=zero_activity_df, ...)` call** — manifest records this as a real capture (not
   `empty_confirmed`); the `zero_activity=True` column distinguishes it from a genuine high-volume day.
4. **Sports historical re-scope**: sports HISTORICAL capture lives in `instruments-service` (not MTDS); the case-D
   implementation for sports per-fixture zero-activity belongs there, not in MTDS (per D3 audit finding).

Successor plan: `wave3x_track_d_implementation_<date>.md` (to be filed when the writegate Phase 3.D.5 Wave 2/3 planning
window opens post-2026-05-23 cutover). Reference: operator decision #4 in
`plans/archive/issues/wave3x_track_d_findings_2026_05_11.md`.

---

## Phase 3A CeFi adapter audit results (2026-05-12)

Full per-CeFi-venue adapter audit across all 18 implemented CeFi venues in `VENUES_BY_ASSET_GROUP["cefi"]`, run by slot
2 background sub-agent 2026-05-12. **Result: all 18 compliant — Category A with typed reasons.**

Key findings:

- No `_create_empty_output()` calls in any CeFi base adapter (banned per writegate Phase 2.A). The QG checker
  `unified-trading-pm/scripts/quality_gates/check_banned_placeholder_methods.py` confirms zero matches in non-test code.
- No NaN-placeholder bars emitted by any CeFi venue. The 2026-05-05 MDPS incident pattern (`capture_status=captured`
  with all-NaN OHLC) is absent from new writes post-writegate Wave 2.M.
- All 18 adapters route on-source-zero-response to `record_empty(reason=EXPECTED_*)` (Category A) correctly.
- GMX/DRIFT cefi-side wiring absent in MTDS routing — these have no tick adapter; not a manifest violation.
- `_handle_empty_tick_data` (MDPS `batch_workers.py` + `live_workers.py`) is the approved post-Wave-2.M method that
  routes through `record_empty_for_shard` — it is NOT in the banned-pattern set (it replaced `_create_empty_output`).

**Historical reconciler**: `instruments-service/scripts/reconcile_legacy_nan_placeholder_bars.py` scans
`capture_status=captured` rows in production manifests for all-NaN OHLC parquet data written before writegate Wave 2.M
and reclassifies them to `attempted_failed` with `error_reason="LEGACY_NAN_PLACEHOLDER"`. Default mode: scan-only (CSV
report); pass `--apply-flips` with `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` to mutate. Scopes: `cefi` only (Phase 3
scope; other asset_groups out of scope per this plan).

Reference: `plans/active/cross_asset_group_catalogue_audit_2026_05_10.md` Phase 3A/3B/3C.

---

## Session-typed availability (writegate Phase 2.E.2)

> Shipped 2026-05-15 — MTDS@038a611, tradfi_master_2026_05_07.md § "Replace zero-volume bars during non-tradeable
> sessions."

### What changed

Prior to Phase 2.E.2 the MTDS orchestrator **silently pre-skipped** TradFi venues whose date was a non-trading day
(`is_non_trading_day()` returned True). No manifest row was written. Downstream feature calculators had to re-consult
`venue_trading_calendar` to know why the parquet was absent — violating the "manifest is the SSOT for absence + reason"
principle codified 2026-05-07.

Phase 2.E.2 closes this gap: the orchestrator now calls `record_expected_empty(reason=...)` for **every (venue,
data_type)** it would have silently skipped. The manifest becomes the single authoritative answer.

### The three session-typed reasons

| Reason                           | When emitted                                                                                                                   | Who emits it                                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `EXPECTED_WEEKEND`               | Saturday or Sunday for any TradFi venue (`is_non_trading_day()` returns True and weekday ∈ {5, 6})                             | MTDS orchestrator via `non_trading_day_reason(venue, date)` → `record_expected_empty`              |
| `EXPECTED_HOLIDAY`               | A US-market-holiday weekday per `venue_trading_calendar` (e.g. New Year's Day, Christmas, MLK Day on CME/NYSE/NASDAQ/ICE/CBOE) | Same as above                                                                                      |
| `EXPECTED_OUTSIDE_TRADING_HOURS` | An intra-day timestamp falls outside the venue's published session window (see `VENUE_SESSION_HOURS` in UAC)                   | Per-bar / per-shard feature calculator that checks `classify_session()` before writing to manifest |

`EXPECTED_WEEKEND` and `EXPECTED_HOLIDAY` are whole-day: the orchestrator pre-empts the fetch entirely. The adapter is
never called. `EXPECTED_OUTSIDE_TRADING_HOURS` is intra-day: the adapter may run, but a bar-level filter at the
calculator or writer decides the bar is outside the venue's published hours.

### Orchestrator implementation pattern (canonical — MTDS@038a611)

Two code paths in the MTDS `process_ticks` function both emit session-typed rows:

**Path 1 — all-non-trading-day batch (early return):**

```python
# all venues non-trading → active_venues=[] → early return
for nt_venue in non_trading_skipped:
    nt_reason = non_trading_day_reason(nt_venue, date)  # "EXPECTED_WEEKEND" | "EXPECTED_HOLIDAY" | None
    if nt_reason is None:
        continue
    nt_expected_dts = get_expected_data_types_for_venue(nt_venue)
    if data_type_filter:
        nt_expected_dts = [dt for dt in nt_expected_dts if dt in data_type_filter]
    for nt_dt in nt_expected_dts:
        _nt_writer.record_expected_empty(
            row_key={"date": date, "venue": nt_venue, "chain": "", "data_type": nt_dt},
            reason=nt_reason,
            pipeline_mode=_resolve_pipeline_mode_for_sentinel(nt_venue, nt_dt),
        )
```

**Path 2 — mixed batch (some venues trading, some not):** Same loop body executed after `ManifestWriter` instantiation
in the finalization block, using the already-open `writer_manifest`.

The guard `if nt_reason is None: continue` ensures crypto venues (which always return `None` from
`non_trading_day_reason`) never get session-typed rows — weekends are normal trading days for crypto.

### Downstream consumer action for session-typed rows

| Reason                           | Rolling-window feature (e.g. 20-bar SMA)                                                                              | Same-day single-sample feature (e.g. daily VWAP)                                    | Execution / live strategy                                   |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `EXPECTED_WEEKEND`               | Skip the day; **do not include in denominator**. 20-bar window over Mon–Fri only.                                     | Emit `record_empty(reason=NO_INPUT_AVAILABLE)` for the calc output.                 | Skip asset allocation for that cycle. Log but do not alert. |
| `EXPECTED_HOLIDAY`               | Same as weekend — skip and adjust denominator.                                                                        | Same as weekend.                                                                    | Same as weekend.                                            |
| `EXPECTED_OUTSIDE_TRADING_HOURS` | Drop the bar from the rolling window and adjust denominator; do NOT count outside-hours bars toward the N-bar target. | Omit the bar from the daily aggregate; the aggregate covers session-open bars only. | Do not trade. Session is closed.                            |

The key rule: **session-closed bars are NOT equivalent to "missing data" for a rolling-window feature**. They are
_expected_ closed and the window size must honour calendar structure. A 20-day SMA over CME futures should span 20
trading days, not 20 calendar days.

### `n_valid` sibling column (session-aware calculators)

Session-aware calculators MUST emit an `n_valid` sibling column alongside any rolling aggregate so consumers know the
denominator actually used. See worked example in the "20-day MA" section above for the shape.

## Expected universe v2 — denominator impact on consumers (2026-05-15)

When the v2 instrument-grain enumerator lands (sequenced under `manifest_evolution_master_2026_05_08` gate G3), the
manifest's `expected_unattempted` denominator grows by ~100× (from ~1.4M venue-grain rows to ~190M instrument-grain
rows). Downstream consumers that compute honest-coverage percentages must handle this volume change:

- **Deployment-api data-status drilldown** — `coverage_pct` queries must use column-projection (e.g. `pyarrow` with
  `columns=['capture_status', 'asset_group', 'venue', 'instrument_id', 'date']`) rather than full table scans.
  Pre-compute 24h-TTL redis cache for UI-facing endpoints. DuckDB-style aggregates preferred for ad-hoc queries.
- **features-\* pre-flight gates** — row-count assertions become 100× larger; assert relative coverage (%) not absolute
  count, or adjust thresholds after v2 lands.
- **ML training row counts** — features-to-manifest join denominators shift; update any hardcoded "expected N rows per
  day" assertions to use dynamic lookups from the manifest.
- **Reporting surfaces** — no action needed if they already read from the drilldown endpoint (gets the cache benefit).

This note is pre-emptive — v2 has not yet launched. Update this section after Phase 4 of
[`expected_universe_v2_design_2026_05_08.md`](../../plans/active/expected_universe_v2_design_2026_05_08.md) completes.

### Cross-references

- MTDS implementation: `market_tick_data_service/engine/orchestrator.py` — `process_ticks` non-trading-day block.
- UAC calendar functions: `unified_api_contracts.registry.venue_trading_calendar.is_non_trading_day` +
  `non_trading_day_reason`.
- Intra-day session classifier: `unified_api_contracts.canonical.crosscutting.market_session.classify_session`.
- Feature calculator pattern for session-aware rolling windows:
  [`../../codex/06-coding-standards/session-aware-feature-calculator-pattern.md`](../../codex/06-coding-standards/session-aware-feature-calculator-pattern.md).
- Writegate Phase 2.E.2 plan item: `plans/epics/tradfi_master_2026_05_07.md` § "Replace zero-volume bars during
  non-tradeable sessions."

## Phase 8 honest-coverage VM cron pattern (B-018 Phase 8.A, 2026-05-15)

Daily measurement of honest-coverage runs on a GCE VM launched by Cloud Scheduler. This is the shipped
continuous-verification path for the manifest's `empty_confirmed` / `expected_unattempted` rows.

### Components

| Component | Path | Notes |
| --------- | ---- | ----- |
| VM launcher | `deployment-service/scripts/vm/launch-honest-coverage-vm.sh` | Primary — all asset groups, Cloud Scheduler target |
| Ad-hoc launcher | `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` | Per-asset-group filter via `--asset-group` |
| Scheduler setup | `deployment-service/scripts/vm/setup-honest-coverage-scheduler.sh` | Creates `honest-coverage-daily` Cloud Scheduler job |
| Measurement script | `instruments-service/scripts/measure_honest_coverage.py --asset-group all` | Runs inside VM, writes to GCS |
| Output bucket | `gs://central-element-323112-honest-coverage/{date}/coverage.json` | Consumed by deployment-api |
| API consumer | `deployment-api GET /api/data-status/honest-coverage` (Phase 2C) | UI-facing honest-coverage endpoint |

### Cron schedule

Cloud Scheduler job `honest-coverage-daily` fires at **00:30 UTC daily** and calls the VM launcher.
The launcher enforces a singleton lock — refuses to start if any `honest-coverage-*` VM is RUNNING — so
overlapping runs do not corrupt the GCS output.

### VM spec

- Machine: `e2-standard-2` in `asia-northeast1-c`
- Boot disk: 50 GB
- Auto-shutdown: VM terminates after `measure_honest_coverage.py` exits (STARTED + STOPPED lifecycle events)
- Cost: ~5–15 min runtime → < $0.01/day

### Watchdog registration

VM name prefix `honest-coverage-` is registered in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`. The watchdog
tracks heartbeats but does NOT kill honest-coverage VMs (they are inherently short-lived; heartbeat-only mode).

### Operational rules (derived from workspace HARD RULES)

1. **No fire-and-forget**: VM must emit STARTED within 60 s and STOPPED/FAILED at exit.
2. **Per-VM shard isolation**: set `VM_NAME=honest-coverage-{date}` + `MANIFEST_PER_VM_SHARDS=true`.
3. **Ad-hoc runs**: use `launch-measure-honest-coverage-vm.sh --asset-group {group}` for partial re-runs;
   do NOT re-run the daily launcher with `--force` unless the scheduler job failed.

### Cross-references

- Plan: `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 2B + B-018 Phase 8.A.
- Deployment codex: `codex/05-infrastructure/vm-tarball-deployment.md` (tarball creation for VM code).
- QG enforcement: STEP 5.66 (`MANIFEST_PER_VM_SHARDS=true`) + STEP 5.61 (STARTED/STOPPED lifecycle).
