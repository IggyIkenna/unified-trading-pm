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

---

## Reason taxonomy (codified 2026-05-07 — operator direction)

Earlier sections describe **3 causes** with binary `error_reason` (None vs typed-error string). Operator direction
2026-05-07: the manifest IS the single source of truth for "what's there + why it's not." Downstream consumers
should not have to consult `venue_trading_calendar` separately to interpret a missing row. Every `(shard_key, day)`
tuple in the expected universe gets a manifest row, and the row's `error_reason` carries one of these structured
codes:

### Manifest `capture_status` × `error_reason` matrix

| `capture_status`     | `error_reason`                                                       | What it means                                                                                                                       | Parquet on disk?                                                |
| -------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `captured`           | (empty)                                                              | Full good data; row count matches expected; OHLC/required cols populated; cluster-coverage met for bundled shards                    | YES — full parquet                                              |
| `empty_confirmed`    | `EXPECTED_HOLIDAY`                                                   | TradFi non-trading day per `venue_trading_calendar`; CME closed for Christmas, etc.                                                | NO — no parquet                                                 |
| `empty_confirmed`    | `EXPECTED_WEEKEND`                                                   | TradFi/CME weekend; expected closed                                                                                                | NO                                                              |
| `empty_confirmed`    | `EXPECTED_PAUSED_LEAGUE`                                             | Sports league not in season; UAC `KNOWN_COVERAGE_GAPS` payload                                                                      | NO                                                              |
| `empty_confirmed`    | `EXPECTED_PRE_SOURCE_COVERAGE_START`                                 | Date is before `SOURCE_COVERAGE_START` for this `(source, data_type)`; data didn't exist back then                                 | NO                                                              |
| `empty_confirmed`    | `EXPECTED_PRE_GENESIS_CHAIN`                                         | DeFi `chain` didn't exist on this date (e.g. Solana pre-2020-03)                                                                   | NO                                                              |
| `empty_confirmed`    | `EXPECTED_INSTRUMENT_NOT_LISTED`                                     | Instrument's `market_created_at` > date (predictions, dated futures pre-listing, etc.)                                             | NO                                                              |
| `empty_confirmed`    | `EXPECTED_INSTRUMENT_DELISTED`                                       | Instrument's `delisted_at` ≤ date (CeFi delisted pairs, dated futures post-expiry, prediction post-settlement)                     | NO                                                              |
| `empty_confirmed`    | `EXPECTED_PARTIAL_HALF_DAY`                                          | TradFi half-day session (Black Friday CME, etc.); fewer rows than full day but the rows present are good                            | OPTIONAL — partial parquet OR no parquet; manifest tells truth |
| `empty_confirmed`    | `SOURCE_RETURNED_ZERO`                                               | Source called, returned legitimately empty (path A from old 3-category model); data was expected but the upstream had nothing       | NO                                                              |
| `attempted_failed`   | `UpstreamTimestampBiasError(...)`                                    | Path B — source returned ticks ALL outside requested day after interval filter; upstream partition mislabeled                       | NO                                                              |
| `attempted_failed`   | `MalformedTickFieldError(...)`                                       | Path C — rows in window but downstream calc dropped all due to NaN/malformed source field                                          | NO                                                              |
| `attempted_failed`   | `ClusterCoverageError(missing=..., observed=...)`                    | Bundled shard partial: observed clusters < expected per UAC registry                                                                | NO                                                              |
| `attempted_failed`   | `MissingAvailableAt`                                                 | Parquet was written but lacks `available_at` column or has nulls — would corrupt LookaheadBiasError downstream gates                | (legacy parquet may exist; reconciler reflips manifest)        |
| `attempted_failed`   | `EmptyPlaceholderBugBackfill`                                        | Reconciler-flipped historical row — pre-fix MDPS wrote 1440-NaN placeholder; reconciler caught it                                  | (legacy parquet exists; reconciler doesn't delete it)          |
| `attempted_failed`   | `RAW_TICK_PARTITION_MISMATCH`                                        | MTDS-side partition validator detected upstream-bug at write time                                                                   | NO                                                              |

### Two principles this codifies

1. **Manifest is the SSOT for absence + reason.** Downstream consumers do NOT re-derive "is this day expected to have
   data?" from `venue_trading_calendar` separately — they read the manifest row and trust the `error_reason`. The
   orchestrator's pre-flight gate populates the manifest with the expected-absence reason at queue time so the row
   exists for every `(shard_key, day)` in the expected universe.
2. **No parquet for bad/partial-expected days.** Even when the data is "good but partial" (half-day trading session),
   the cleanest write is NO parquet + manifest row with `EXPECTED_PARTIAL_HALF_DAY` reason. The downstream consumer
   sees the manifest, decides what to do. (Optional exception: writers MAY persist a partial parquet with the actual
   short row count IF the downstream consumer needs the rows directly — but the manifest reason is still the gate
   and the parquet schema is honest about its short row count, no NaN-fill to "complete" the day.)

---

## Per-service consumer-class audit (2026-05-07 — operator direction)

Different services have different right-answers when they read a manifest row that says `empty_confirmed[reason=...]`
or `attempted_failed[reason=...]`. The audit below is the workspace SSOT for per-service handling. Service code MUST
match this contract.

| Consumer class                                      | Service examples                                          | `empty_confirmed[EXPECTED_*]` action                                                            | `empty_confirmed[SOURCE_RETURNED_ZERO]` action                                | `attempted_failed[reason]` action                                                                                |
| --------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Execution (live trade emission)**                 | execution-service, signal-broadcast                        | **Skip the trade.** Don't trade on an absence we expected. Log + emit `EXECUTION_SKIPPED` event. | Skip the trade. Same reasoning.                                               | **Skip the trade + alert.** `attempted_failed` is a real upstream issue; don't trade through it.                  |
| **ML training (continuous-series)**                 | ml-training-service                                        | **NaN-fill the row** to keep the training-window contiguous. Tree-based ML handles NaN natively. | NaN-fill same as above.                                                       | NaN-fill BUT add a `data_quality_flag=ATTEMPTED_FAILED` column so the model can learn to discount attempted-failed regions if it wants. |
| **ML inference (live feature compute)**             | ml-inference-service                                       | NaN-fill the row before model `predict()` if the feature is in the model's feature list.        | NaN-fill same as above.                                                       | **Block the inference** for that timestamp; emit `INFERENCE_SKIPPED` event. Live model cannot infer through gaps. |
| **Features — rolling window (≥2 sample window)**    | features-volatility (rolling vol), features-cross-instrument (rolling spread), features-onchain (lending APY MA) | **Keep window size, adjust denominator.** 20-day MA over a window with 2 expected-missing days = mean of 18 valid samples; window stays 20. Surface `n_valid` as a sibling column. | Same as expected: keep window, adjust denominator.                            | Skip the calc for that target timestamp; emit `record_empty(...)` for the calc's own output row.                  |
| **Features — same-day single-sample**               | features-cross-instrument (today's basis), features-onchain (today's lending rate snapshot) | **NaN-fill the calc output row** OR emit `record_empty(...)` for the calc's own output. Per-calc choice; document in calc docstring. | Same.                                                                          | Emit `record_empty(...)` for the calc's own output. Don't fabricate.                                              |
| **Features — cross-instrument (require both legs)** | features-cross-instrument (paired-price-dispersion, cross-venue arb) | If EITHER leg is `empty_confirmed`, emit `record_empty(reason=LEG_ABSENT_<which_leg>)` for the calc's own output. | Same as expected.                                                              | If EITHER leg is `attempted_failed`, propagate the failure: emit `record_failed(reason=UPSTREAM_LEG_FAILED)`.       |
| **Strategy (backtest replay)**                      | strategy-service                                           | Treat as "no signal that day"; allocator skips the asset for that allocation cycle.              | Same.                                                                          | Same as expected absence; backtest mode is forgiving (it's reconstructing history).                                |
| **Strategy (live)**                                 | strategy-service (live mode)                               | Allocator skips the asset; rebalance proceeds across the remaining universe.                     | Same.                                                                          | **Block trade emission** for assets affected; alert. Live mode is unforgiving.                                    |
| **Reconciliation (batch-vs-live)**                  | batch-live-reconciliation-service                          | Both sides should agree on the absence; if one side has data and the other doesn't with the same reason, flag the discrepancy. | Same — both sides should agree.                                                | Both sides should also agree; if only one side flags `attempted_failed`, the bug is on that side.                  |
| **Position / Risk monitor**                         | position-balance-monitor-service, risk-and-exposure-service | No-op (these services consume position events, not feature parquets).                              | No-op.                                                                          | Alert if it would block a downstream calc the position depends on.                                                  |

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

Operator-given example: "If you have a one-day moving average for one day and the one day is missing, expected
missing, then you can't do much more than fill in that in." 

For same-day single-sample calcs: there's no rolling-window denominator adjustment available. The right shape:
the calc emits `record_empty(reason=NO_INPUT_AVAILABLE)` for its own output row that day. Downstream consumers see
the absence in the calc's manifest and apply their own consumer-class rule (NaN-fill for ML, skip for execution,
etc.). Don't fabricate a value.

---

## Reader-side fallback for legacy rows (codified 2026-05-07 — operator gap finding)

Phase 2.E.1 ships UTL `record_empty(reason=...)` for NEW writes. Existing manifest rows have `error_reason=None`
for honest empty (or no row at all if calendar-pre-skipped). Without retrospective backfill (writegate Phase 3.D),
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
2. **`SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START`** — date < source coverage → `EXPECTED_PRE_SOURCE_COVERAGE_START`.
3. **`KNOWN_COVERAGE_GAPS`** — sports paused leagues → `EXPECTED_PAUSED_LEAGUE`.
4. **DeFi chain-genesis lookup** — date < chain genesis → `EXPECTED_PRE_GENESIS_CHAIN`.
5. **Instrument lifecycle** (instruments-service `MARKET_LIFECYCLE` for predictions, `delisted_at` for CeFi/TradFi):
   - day < `market_created_at` → `EXPECTED_INSTRUMENT_NOT_LISTED`
   - day ≥ `delisted_at` (or `settlement_time` for predictions) → `EXPECTED_INSTRUMENT_DELISTED`
6. **Default**: `SOURCE_RETURNED_ZERO` — the writer attempted, source had nothing, no calendar/coverage exception
   applied.

This makes the consumer code uniform across legacy AND new manifest rows. Writers populate the manifest reason
upfront so the fast path is just a row read; the fallback exists for in-migration coverage and as a defensive
guarantee that consumers always have an answer.

### What this changes vs. the original codex § "Three causes of no data" matrix

The original matrix said "no manifest row written; `venue_trading_calendar` says closed → skip silently." Per
operator direction 2026-05-07 we now want the manifest to BE the SSOT, so:

- **Going forward**: writers emit `record_expected_empty(reason=EXPECTED_HOLIDAY)` for calendar-closed days
  instead of pre-skipping.
- **For legacy data** (until Phase 3.D backfill runs): consumer-side `classify_legacy_empty_row(...)` derives the
  reason on the fly from the same SSOTs.
- **Either way**, the consumer's downstream behaviour is the same — the lookup is just slightly slower for legacy
  rows. The audit rule per consumer class (NaN-fill / skip / adjust denominator) doesn't care whether the reason
  came from manifest or fallback.

Cross-reference: writegate Phase 3.D `reconcile_expected_absence_reasons.py` per asset_group performs the
retrospective backfill so the slow path eventually empties out per asset_group.

---
