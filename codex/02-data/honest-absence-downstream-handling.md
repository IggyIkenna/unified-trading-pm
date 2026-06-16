---
scope: [engineer, admin]
last_reviewed: 2026-05-22
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

## §6A honest-absence violation classes (CeFi/DeFi backfill audit 2026-05-27)

> Codified 2026-05-30 per `cefi_venue_backfill_coverage_remediation_2026_05_27.md` § 6A. These three classes were
> discovered during the CeFi/DeFi venue backfill audit and generalise the operator's 401≠honest-absence concern into a
> taxonomy of silent-drop bugs. All three result in phantom cells — positions in the expected universe that look absent
> when they should be `empty_confirmed` or `attempted_failed` in the manifest.

### Class 1 — In-flight shard failure with no manifest marker ("phantom gap")

**What it looks like**: The adapter logs `WARNING in-flight key=<venue>/<sym>/<date>/<dt>  failed: <error>` (or
equivalent) but exits without calling `record_empty()` or `record_failed()`. The manifest has **no row** for that
`(venue, data_type, day)` cell — the failure is invisible to downstream consumers and honest-coverage metrics.

**Example** (OKX Tardis, fixed MTDS@774db33): `ConnectionTimeoutError` on `book_snapshot_5` and
`ArrowInvalid: Empty CSV file` on `trades` produced ~27+ sampled phantom cells per run.

**Why it's wrong**: A missing manifest row on a calendar-trading day is indistinguishable from "pipeline never ran." The
pre-flight gate at downstream consumers raises `DependencyError` instead of NaN-filling or alerting correctly.
Honest-coverage denominator can't count what it doesn't see.

**Required fix**: In every in-flight failure handler, classify the exception and write a manifest row:

```python
try:
    ...  # fetch / write parquet
except EmptyCsvError:
    writer.record_empty(row_key=..., reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)
except (ConnectionTimeoutError, aiohttp.ClientError):
    writer.record_failed(row_key=..., error=classify_venue_error(exc))
```

The manifest row may be `empty_confirmed` (for genuinely empty sources) or `attempted_failed` (for network/timeout
failures). What's never acceptable is silence.

---

### Class 2 — Silent-zero ("adapter produces no rows, records nothing")

**What it looks like**: The adapter's fetch loop returns zero rows (due to a schema error, empty subgraph result, or
exhausted cascade) but the calling code silently continues without recording any manifest row. The parquet is either
absent or written as a 0-row file with `capture_status=captured` — both are honest-absence violations.

**Example A** (DeFi dex-swaps, fixed MTDS@ed5fdcf): `_PANCAKESWAP_BSC_SWAPS_QUERY` included an unrecognised field
(`sqrtPriceX96`) causing a schema parse error → all cascade queries returned `None` → handler emitted
`SOURCE_RETURNED_ZERO` on a live subgraph (misleading). Fix: raise `_SubgraphNotFoundError` on HTTP 404; raise
`RuntimeError` when ALL cascade queries fail on schema errors → caller calls `record_failed(ADAPTER_FETCH_FAILED)`.

**Example B** (Understat 2019, fixed instruments-service@c654ccf): 100% `404` responses on `getMatch/*` and
`getLeagueData/*/2019` → adapter logged 0 rows but called `record_empty(EXPECTED_NO_FIXTURE)` — using the wrong reason
for a fetch failure. Fix: track `_fetch_error_count`; emit `record_failed(HTTP_NOT_FOUND)` when errors occurred instead
of `record_empty(EXPECTED_NO_FIXTURE)`.

**Why it's wrong**: A `captured` row with 0 rows in the parquet (or no row at all) is worse than `empty_confirmed`.
Downstream features compute on 0 meaningful rows and may produce garbage statistics. Honest-coverage numerator counts
the cell as captured when it should count it as failed.

**Required fix**: Zero-row fetch result must always produce a manifest row, never silence:

```python
rows = adapter.fetch(...)
if not rows:
    # Check WHY we got 0 rows
    if fetch_had_errors:
        writer.record_failed(row_key=..., error=classify_venue_error(last_exc))
    else:
        writer.record_empty(row_key=..., reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)
    return
# normal path
writer.record_captured(row_key=..., df=rows_df)
```

The key diagnostic: **was the fetch attempted and failed** (`attempted_failed`) or **did the fetch succeed but the
source had no data** (`empty_confirmed[SOURCE_RETURNED_ZERO]`)?

---

### Class 3 — Captured-0-row ("manifest says captured, parquet is empty")

**What it looks like**: `record_captured` is called with a 0-row DataFrame (or `row_count=0`), writing
`capture_status=captured` to the manifest despite the parquet having no meaningful rows. Downstream consumers trust the
`captured` status and attempt to compute features — on empty input.

**Historical example** (MDPS 2026-05-05): MDPS wrote 1440-bar NaN-filled placeholder parquets with
`capture_status=captured` for years. Banned in writegate Phase 2.A. The reconciler
`reconcile_legacy_nan_placeholder_bars.py` reclassifies these rows to `attempted_failed[LEGACY_NAN_PLACEHOLDER]`.

**New form** (CEFi/DeFi adapters): A 0-row parquet at `record_captured(df=pd.DataFrame(), ...)` is structurally
identical — manifest says captured, downstream gets empty. `ManifestWriter` now raises `MissingRowCountError` (or
`EmptyDataFrameError` depending on schema enforcement phase) when `df` is empty and `record_captured` is called.

**Why it's wrong**: `capture_status=captured` is a contract: "the data was here, fetch it." If the parquet is empty,
that contract is broken. Features compute on empty input; ML trains on ghost rows; execution prices assets with no real
ticks behind them.

**Required fix**: Never call `record_captured` with an empty DataFrame. The pre-write validation in the `ManifestWriter`
enforces this — but the adapter must also classify correctly:

```python
if df.is_empty():  # polars; .empty for pandas
    # EITHER the source had nothing:
    writer.record_empty(row_key=..., reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)
    # OR the fetch itself failed:
    # writer.record_failed(row_key=..., error=...)
    return
writer.record_captured(row_key=..., df=df)
```

---

### Summary anti-pattern table (§6A additions)

| Violation class              | Symptom                                                                                                  | Root cause pattern                                                                 | Required call site                                                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **In-flight drop** (Class 1) | Exception logged in adapter, no manifest row written; cell absent from expected universe                 | Exception handler exits without calling `record_empty` or `record_failed`          | `record_failed(classify_venue_error(exc))` for network/5xx; `record_empty(SOURCE_RETURNED_ZERO)` for empty-CSV / expected-empty parse results |
| **Silent-zero** (Class 2)    | Zero rows returned; no manifest row, OR wrong reason (`EXPECTED_NO_FIXTURE` instead of `HTTP_NOT_FOUND`) | `if not rows: return` (no manifest write); wrong reason selection on fetch failure | Inspect `fetch_had_errors`; route to `record_failed` vs `record_empty` explicitly                                                             |
| **Captured-0-row** (Class 3) | `capture_status=captured` in manifest; 0-row parquet on disk; downstream computes on empty input         | `record_captured(df=empty_df)` called without checking `df.is_empty()` first       | Check `df.is_empty()` before `record_captured`; route to `record_empty` or `record_failed` on empty                                           |

### Detection

Run `scripts/check_zero_row_captures.py --asset-group cefi` (instruments-service) to scan for `capture_status=captured`
rows whose associated parquet has 0 rows. This is the Class 3 detector.

For Class 1 + Class 2, grep adapter logs for `in-flight.*failed` and `WARNING.*0 rows` patterns that lack a companion
manifest entry in the scan window. The `ADAPTER_FETCH_FAILED` event emitted by correctly-wired adapters provides the
audit trail.

---

## Reference incidents

- **2026-05-05 MDPS empty-placeholder OHLC** — 1440 NaN-filled rows per `(venue, data_type, day)` for years; manifest
  said `captured`; downstream features computed garbage. Banned in writegate Phase 2.A.
- **2026-04-29 PLAYER_VALUES denorm** — phantom-row script `write_player_values_placeholders.py` wrote 906 zero-row
  placeholders to mask path-prefix drift. Deleted 2026-05-05.
- **2026-05-06 (this doc)** — sports `data_available_at` rename + `_create_full_day_empty_output` consumer audit
  surfaced the need for a workspace-wide downstream-consumption SSOT separate from the write-side manifest doc.
- **2026-05-27 (cefi remediation §1 + §2)** — OKX Tardis `code 140` (request outside expiry window) misclassified as
  download error; ~1,250 spurious 400s per VM per window. Operator directive: "if the issue is of 401, we should not
  mark that one as honest-absence — that will make the data look corrupt."

---

## Expiry-window filtering contract (CeFi dated futures — codified 2026-05-27)

### Rule

For dated futures and options, every (instrument, date) pair MUST be filtered against the instrument's availability
window **before** the request is issued to Tardis (or any other historical data source). Never request a shard that is
outside the contract's active life.

### Correct absence classification

| Condition                                                                                    | Manifest status    | Reason                                         |
| -------------------------------------------------------------------------------------------- | ------------------ | ---------------------------------------------- |
| `date < InstrumentRecord.available_from` — instrument not yet listed on the requested date   | `empty_confirmed`  | `EXPECTED_INSTRUMENT_NOT_LISTED`               |
| `date > InstrumentRecord.available_to_datetime` — contract expired before the requested date | `empty_confirmed`  | `EXPECTED_INSTRUMENT_DELISTED`                 |
| In-window date, paid Tardis key expired (HTTP 401)                                           | `attempted_failed` | `CLASSIFIED_VENUE_ERROR` — see §401 rule below |
| In-window date, Tardis `code 140` returned at request time (should not happen post-fix)      | `empty_confirmed`  | `EXPECTED_INSTRUMENT_DELISTED`                 |

### Source of window bounds

`InstrumentRecord.available_from` / `InstrumentRecord.available_to_datetime` — populated from Tardis `availableSince` /
`availableTo` at universe-build time by `instruments-service`. Do NOT re-fetch Tardis per tick request; load once per
run. Venues covered: OKX (dash-parser `YYMMDD`), Deribit (DDMMMYY + Tardis expiry), Kraken futures (underscore
`FI_XBTUSD_YYMMDD` fallback added `instruments-service@ffb8192`).

### Anti-pattern

Issuing the request anyway and letting Tardis return an error is **not acceptable** — it burns quota, floods logs with
vendor 400s, and makes the backfill log look like a failure when it's a calendar truth. Pre-filter in the expansion step
(caller of `tick_data_handler`) before any HTTP call. Shipped: `market-tick-data-service@91e3df03`.

---

## 401 ≠ honest absence (operator directive 2026-05-27)

> "if the issue is of 401, we should not mark that one as honest-absence — that will make the data look corrupt."

### Rule

**HTTP 401 (expired or missing API key) MUST NOT be recorded as `empty_confirmed` or `expected_unattempted`.** The data
exists and is downloadable; it is blocked on a credential. Recording it as honest absence makes the manifest lie about
coverage and causes downstream consumers (reconcilers, feature builders, strategy engines) to treat a credential failure
as a real data gap.

### Correct action for 401

Record as `attempted_failed[CLASSIFIED_VENUE_ERROR]`. The `error_detail` field SHOULD carry the HTTP status code (401)
so dashboards and alerting can distinguish credential failures from other transient errors.

### Downstream treatment

Consumers encountering `attempted_failed` for a CeFi shard on a date that should have paid data MUST treat it as a
pending-download situation, not as an honest absence:

- **Reconcilers**: flag the cell as `PENDING_DOWNLOAD` in their report; do not propagate as `empty_confirmed`.
- **Feature builders**: exclude from window (same as any `attempted_failed`) — do not forward-fill.
- **Alerting**: fire a `CREDENTIAL_FAILURE` alert if the count exceeds a daily threshold.

### The three-way distinction for "no data" in CeFi backfill

| Situation                             | Manifest status    | Reason                           | Consumer reads as                                 |
| ------------------------------------- | ------------------ | -------------------------------- | ------------------------------------------------- |
| Date outside contract expiry window   | `empty_confirmed`  | `EXPECTED_INSTRUMENT_DELISTED`   | Calendar truth — skip in all consumers            |
| Date before instrument listing        | `empty_confirmed`  | `EXPECTED_INSTRUMENT_NOT_LISTED` | Calendar truth — skip                             |
| Paid-key expired / missing (HTTP 401) | `attempted_failed` | `CLASSIFIED_VENUE_ERROR`         | Credential-blocked — re-attempt when key rotated  |
| Transient vendor error (5xx, timeout) | `attempted_failed` | `CLASSIFIED_VENUE_ERROR`         | Retry-eligible                                    |
| Source returned zero rows (no error)  | `empty_confirmed`  | `SOURCE_RETURNED_ZERO`           | Source truth — data does not exist for this shard |

---

## §6A honest-absence-violation classes (anti-patterns — codified 2026-05-27)

These three anti-patterns were named in the CeFi remediation audit and apply workspace-wide.

### Class 1 — In-flight shard failure with no manifest marker

**Description**: an adapter failure (connection timeout, Arrow schema error, stream truncation) produces a `WARNING` log
line but the shard exits without calling `record_empty()` or `record_failed()`. The manifest row is never written (or is
written as `captured` with 0 rows from a prior run).

**Harm**: the shard is invisible to reconcilers; coverage reports under-count the asset_group; orchestrators re-attempt
on the next VM run, but manifest state is inconsistent.

**Correct fix**: every in-flight failure handler MUST call `record_failed()` with a typed reason before propagating or
swallowing the exception. Shard-level failure isolation (no `raise` in per-venue loops) means the handler is always
reachable. Classification:

- Connection timeout / network error → `CLASSIFIED_VENUE_ERROR` (via `classify_venue_error()`)
- Empty CSV / zero-byte stream → `SOURCE_RETURNED_ZERO` or `expected_unattempted[EXPECTED_INSTRUMENT_DELISTED]`
  depending on whether the instrument was alive on the date

**Shipped fix**: `market-tick-data-service@774db33` (Tardis stream adapter).

### Class 2 — Silent zero (source returns 0 rows, no `record_empty`)

**Description**: the source adapter returns an empty DataFrame (no rows, no error) and the writer calls
`record_captured(...)` with 0 rows — or silently skips the manifest call. The manifest shows `captured` but the parquet
is empty or missing.

**Harm**: downstream features compute on empty data (NaN or divide-by-zero); coverage metrics show 100% when the data is
absent; reconcilers miss the gap.

**Correct fix**: after calling the source:

1. If `len(df) == 0` AND the instrument is expected to be alive (IS catalog says alive): call
   `record_failed(UPSTREAM_SUBGRAPH_ZERO)` (DeFi subgraphs) or emit `ADAPTER_FETCH_FAILED` +
   `record_failed(CLASSIFIED_VENUE_ERROR)`.
2. If `len(df) == 0` AND the instrument is known absent (expired, delisted, pre-listing): call
   `record_empty(reason=EXPECTED_INSTRUMENT_DELISTED / EXPECTED_INSTRUMENT_NOT_LISTED)`.
3. If `len(df) == 0` AND the source legitimately returned nothing (deprecated subgraph, source gap): call
   `record_empty(reason=SOURCE_RETURNED_ZERO)`.
4. NEVER call `record_captured(...)` with 0 rows for an instrument that is expected to be alive.

### Class 3 — Captured-0-row (manifest `captured`, 0-row parquet exists)

**Description**: manifest row has `capture_status="captured"` but the parquet file written has 0 data rows (or
`row_count=0` in the manifest). This is distinct from Class 2 — the write call was made, just with empty data.

**Harm**: consumers read the parquet, get 0 rows, and may fail silently (features output NaN, rolling windows
under-count, ML training excludes the date as if the market was closed).

**Correct fix**: `record_captured()` in UTL raises `CapturedZeroRowsError` when `row_count == 0` and the shard is not an
explicit "zero-activity confirmed" type. Writers MUST pass `row_count=len(df)` to trigger this guard. If the instrument
is live and data was expected, treat as Class 2 and call `record_failed` instead.

---

## Reason taxonomy (codified 2026-05-07 — operator direction)

> **Coverage formula SSOT (2026-05-19)**: consumers computing coverage MUST check the `EXPECTED_*` vs non-`EXPECTED_*`
> split on `error_reason` — NOT just `capture_status` alone. The canonical function is
> `compute_honest_coverage(CaptureStatusCounts(...))` from `unified_api_contracts` (`unified-api-contracts@a9891f9`).
> Two `expected_unattempted` sub-buckets: `expected_unattempted_known_empty` (reason startswith `"EXPECTED_"` — counts
> toward numerator) and `expected_unattempted_pending_fetch` (non-`EXPECTED_` reason — counts against coverage, will be
> retried on next backfill). Do **NOT** roll your own formula. SSOT plan:
> `plans/active/honest_coverage_formula_consolidation_2026_05_19.md`.

Earlier sections describe **3 causes** with binary `error_reason` (None vs typed-error string). Operator direction
2026-05-07: the manifest IS the single source of truth for "what's there + why it's not." Downstream consumers should
not have to consult `venue_trading_calendar` separately to interpret a missing row. Every `(shard_key, day)` tuple in
the expected universe gets a manifest row, and the row's `error_reason` carries one of these structured codes:

### Manifest `capture_status` × `error_reason` matrix

| `capture_status`   | `error_reason`                                    | What it means                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Parquet on disk?                                               |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| `captured`         | (empty)                                           | Full good data; row count matches expected; OHLC/required cols populated; cluster-coverage met for bundled shards                                                                                                                                                                                                                                                                                                                                                                          | YES — full parquet                                             |
| `empty_confirmed`  | `EXPECTED_HOLIDAY`                                | TradFi non-trading day per `venue_trading_calendar`; CME closed for Christmas, etc.                                                                                                                                                                                                                                                                                                                                                                                                        | NO — no parquet                                                |
| `empty_confirmed`  | `EXPECTED_WEEKEND`                                | TradFi/CME weekend; expected closed                                                                                                                                                                                                                                                                                                                                                                                                                                                        | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PAUSED_LEAGUE`                          | Sports league not in season; UAC `KNOWN_COVERAGE_GAPS` payload                                                                                                                                                                                                                                                                                                                                                                                                                             | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PRE_SOURCE_COVERAGE_START`              | Date is before `SOURCE_COVERAGE_START` for this `(source, data_type)`; data didn't exist back then                                                                                                                                                                                                                                                                                                                                                                                         | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PAST_SOURCE_COVERAGE_END`               | Date is after the source archive's documented coverage end date — the archive stopped writing. E.g. Drift V1 S3 archive stopped writing 2025-01-08 (direct S3 probe 2026-05-20). Distinct from `EXPECTED_PRE_SOURCE_COVERAGE_START` (archive start) and `EXPECTED_PRE_VENUE_LAUNCH` (venue launch). Driven by `InstrumentRecord.source_coverage_end` per data_type. Added UAC@5a54bfd 2026-05-20 for Drift S3 backfill.                                                                    | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PRE_GENESIS_CHAIN`                      | DeFi `chain` didn't exist on this date (e.g. Solana pre-2020-03)                                                                                                                                                                                                                                                                                                                                                                                                                           | NO                                                             |
| `empty_confirmed`  | `EXPECTED_INSTRUMENT_NOT_LISTED`                  | Instrument's `market_created_at` > date (predictions, dated futures pre-listing, etc.)                                                                                                                                                                                                                                                                                                                                                                                                     | NO                                                             |
| `empty_confirmed`  | `EXPECTED_INSTRUMENT_DELISTED`                    | Instrument's `delisted_at` ≤ date (CeFi delisted pairs, dated futures post-expiry, prediction post-settlement)                                                                                                                                                                                                                                                                                                                                                                             | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PARTIAL_HALF_DAY`                       | TradFi half-day session (Black Friday CME, etc.); fewer rows than full day but the rows present are good                                                                                                                                                                                                                                                                                                                                                                                   | OPTIONAL — partial parquet OR no parquet; manifest tells truth |
| `empty_confirmed`  | `EXPECTED_PRE_VENUE_LAUNCH`                       | Date is before venue's `launch_date` per UAC `venue_launch_dates` registry (20 CeFi + 2 Prediction venues). Shipped UAC@`ac218dc` 2026-05-07. Distinct from `EXPECTED_PRE_GENESIS_CHAIN` (DeFi chain genesis) and `EXPECTED_PRE_SOURCE_COVERAGE_START` (source archive start).                                                                                                                                                                                                             | NO                                                             |
| `empty_confirmed`  | `EXPECTED_OUTSIDE_TRADING_HOURS`                  | Intra-day timestamp falls OUTSIDE the venue's published trading hours for that day. Distinct from whole-day non-trading (HOLIDAY/WEEKEND) and short-session (PARTIAL_HALF_DAY).                                                                                                                                                                                                                                                                                                            | NO                                                             |
| `empty_confirmed`  | `EXPECTED_OUTSIDE_TRANSFER_WINDOW`                | Day falls outside the transfer window for this league. Two use-cases: (1) **Sports player-transfer window closed** — football leagues have Jan + Jul windows; `transfer_records` shard expected empty outside these windows (see `is_transfer_window_open()` in UAC `canonical/domain/sports/transfer_windows.py`). (2) **DeFi transfer-event lookback** outside the operator-configured bounds (staking / bridging refdata).                                                              | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PRE_SEASON`                             | Sports — day is before season `schedule_announced_at` per league registry. Distinct from `EXPECTED_PRE_SOURCE_COVERAGE_START` (per-source archive start). Operator msg 9 audit dim #6.                                                                                                                                                                                                                                                                                                     | NO                                                             |
| `empty_confirmed`  | `EXPECTED_POST_SEASON`                            | Sports — day is after season-end (playoff close + offseason). Mirror of `EXPECTED_PRE_SEASON`. Operator msg 9 audit dim #6.                                                                                                                                                                                                                                                                                                                                                                | NO                                                             |
| `empty_confirmed`  | `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`           | Sports — operator-documented "this source does not cover this league" (e.g. Odds API has no MLB). Distinct from `EXPECTED_PAUSED_LEAGUE` (league exists but is paused). Wave 3.X dim #7.                                                                                                                                                                                                                                                                                                   | NO                                                             |
| `empty_confirmed`  | `EXPECTED_DEPRECATED_DATA_TYPE`                   | Data_type retired at a known date; rows after that date are expected empty. Plan: `plans/epics/manifest_master.md`                                                                                                                                                                                                                                                                                                                                                                         | NO                                                             |
| `empty_confirmed`  | `EXPECTED_REFDATA_CADENCE_CHANGE`                 | Reference-data refresh cadence changed at a known date (e.g. daily → weekly). Distinct from `EXPECTED_DEPRECATED_DATA_TYPE`. Plan: `plans/epics/manifest_master.md`                                                                                                                                                                                                                                                                                                                        | NO                                                             |
| `empty_confirmed`  | `EXPECTED_KNOWN_SOURCE_GAP`                       | Documented mid-history source gap that doesn't fit the venue-launch / source-coverage-start / pre-genesis primitives. Reference uses: **VIX 15m gap** (`2025-11-13` → `today − 60d`; Yahoo rolling window can't reach + Barchart preload stopped 2025-11-12) + sports `KNOWN_COVERAGE_GAPS` ranges (operator-documented multi-day outages / paused windows). Shipped UAC@`174f401` 2026-05-11.                                                                                             | NO                                                             |
| `empty_confirmed`  | `SOURCE_RETURNED_ZERO`                            | Source called, returned legitimately empty (path A from old 3-category model); data was expected but the upstream had nothing                                                                                                                                                                                                                                                                                                                                                              | NO                                                             |
| `attempted_failed` | `UpstreamTimestampBiasError(...)`                 | Path B — source returned ticks ALL outside requested day after interval filter; upstream partition mislabeled                                                                                                                                                                                                                                                                                                                                                                              | NO                                                             |
| `attempted_failed` | `MalformedTickFieldError(...)`                    | Path C — rows in window but downstream calc dropped all due to NaN/malformed source field                                                                                                                                                                                                                                                                                                                                                                                                  | NO                                                             |
| `attempted_failed` | `ClusterCoverageError(missing=..., observed=...)` | Bundled shard partial: observed clusters < expected per UAC registry                                                                                                                                                                                                                                                                                                                                                                                                                       | NO                                                             |
| `attempted_failed` | `MissingAvailableAt`                              | Parquet was written but lacks `available_at` column or has nulls — would corrupt LookaheadBiasError downstream gates                                                                                                                                                                                                                                                                                                                                                                       | (legacy parquet may exist; reconciler reflips manifest)        |
| `attempted_failed` | `EmptyPlaceholderBugBackfill`                     | Reconciler-flipped historical row — pre-fix MDPS wrote 1440-NaN placeholder; reconciler caught it                                                                                                                                                                                                                                                                                                                                                                                          | (legacy parquet exists; reconciler doesn't delete it)          |
| `attempted_failed` | `RAW_TICK_PARTITION_MISMATCH`                     | MTDS-side partition validator detected upstream-bug at write time                                                                                                                                                                                                                                                                                                                                                                                                                          | NO                                                             |
| `attempted_failed` | `SCHEMA_VALIDATION_FAILED`                        | Pydantic / dataclass validation rejected the row — hard-required field missing or mistyped (e.g. `base_asset` null for SPOT_PAIR, `pool_address` null for DeFi on-chain instrument). Introduced by `hard_schema_enforcement_2026_05_08.md` Phase 2. `error_detail={field, expected_type, observed_value}` carried in the manifest row. — `uac@3157f45`                                                                                                                                     | NO                                                             |
| `attempted_failed` | `UPSTREAM_SUBGRAPH_ZERO`                          | DeFi subgraph returned zero rows on a date the instruments-service catalog reports as alive. Must not be silently `empty_confirmed` — flip to `attempted_failed` so alerting fires. Matched to `UpstreamSubgraphZeroError`.                                                                                                                                                                                                                                                                | NO                                                             |
| `attempted_failed` | `MALFORMED_ROW_KEY`                               | `ManifestWriter.record_captured` rejected the `row_key` shape: per-instrument shard missing `instrument_id`; bundled shard missing `chain` / `options_chain` / `canonical_question_group`. Phase 4 of `hard_schema_enforcement_2026_05_08.md`.                                                                                                                                                                                                                                             | NO                                                             |
| `attempted_failed` | `CLASSIFIED_VENUE_ERROR`                          | Adapter error classified via UAC `classify_venue_error()` (rate-limit / 5xx / timeout / circuit-tripped). Venue-side transient / operational. Typically should retry. Existing `record_failed(error=classify_venue_error(exc))` callsites route here.                                                                                                                                                                                                                                      | NO                                                             |
| `attempted_failed` | `UNCLASSIFIED_ADAPTER_ERROR`                      | Adapter exception that did NOT pass through `classify_venue_error()` before `record_failed`. Transition-period bucket; Phase 2 of `hard_schema_enforcement` forces every callsite to either use `classify_venue_error()` or a structured enum member. Any production occurrence is a bug in the calling adapter.                                                                                                                                                                           | NO                                                             |
| `attempted_failed` | `UPSTREAM_LIVE_GAP`                               | MTDS emitted `CONNECTIVITY_GAP_DETECTED` for this (venue, data_type). MDPS detected the gap in MTDS availability manifest and propagates it. Downstream consumers SHOULD skip or alert; gap fills when MTDS auto-backfills on `CONNECTIVITY_RECOVERED`. — `uac@60c0ee9`                                                                                                                                                                                                                    | NO                                                             |
| `empty_confirmed`  | `EXPECTED_OUT_OF_COVERAGE_WINDOW`                 | Data_type is valid and restorable post-cutover, but currently OUT of the operator-acked MVP coverage scope. Distinct from `EXPECTED_DEPRECATED_DATA_TYPE` (permanent) — this is a scope shrink that may reverse. Canonical case: TradFi `trades`/`tbbo` (L1/L2 tick data) moved to post-cutover per operator direction 2026-05-15. SSOT: `TRADFI_TICK_DATA_WINDOWS` (empty = OHLCV-only mode). Plan: `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`.                                       | NO                                                             |
| `empty_confirmed`  | `EXPECTED_PROTOCOL_PAUSED`                        | DeFi protocol was operational before and after but paused (intentionally or otherwise) during a documented date range. Examples: Aave V2→V3 migration windows, Compound V2 wind-down, chain-level outages. Registry SSOT: `PROTOCOL_PAUSE_WINDOWS` keyed by `(protocol, chain)` → list of `(start, end)` date tuples. Added 2026-05-20 per mega-audit Phase A2.                                                                                                                            | NO                                                             |
| `empty_confirmed`  | `EXPECTED_FIXTURE_POSTPONED`                      | Sports fixture status PST (postponed): fixture postponed before kickoff with no rescheduled date yet (or rescheduled outside the current pipeline window). Source: API Football `status.short == "PST"`. Instruments-service emits this so downstream features don't treat absence as a fetch failure.                                                                                                                                                                                     | NO                                                             |
| `empty_confirmed`  | `EXPECTED_FIXTURE_CANCELLED`                      | Sports fixture status CANC (cancelled): the fixture was cancelled outright. Source: API Football `status.short == "CANC"`. Instruments-service emits this so consumers can distinguish cancelled fixtures from data-fetch failures.                                                                                                                                                                                                                                                        | NO                                                             |
| `empty_confirmed`  | `EXPECTED_LEGACY_MIGRATION_MISSING_EXPIRY`        | TradFi futures/options row from a pre-2026-05-13 historical capture that lacks a populated `expiration`/`expiry_date` field AND cannot be back-filled from Databento metadata at migration time. Distinct from `EXPECTED_INSTRUMENT_NOT_LISTED` (never existed) and `EXPECTED_INSTRUMENT_DELISTED` (removed after date). Plan: `tradfi_canonical_futures_contract_hard_required_fields_2026_05_13.md`.                                                                                     | NO                                                             |
| `empty_confirmed`  | `NO_INPUT_AVAILABLE`                              | Downstream feature or model computation skipped because an upstream input had `attempted_failed` status. Distinct from `EXPECTED_UPSTREAM_EMPTY` (which propagates `empty_confirmed`/`expected_unattempted`) — this fires when upstream was ATTEMPTED but FAILED. Used by: rolling-window calcs, same-day single-sample calcs that cannot proceed with a failed upstream.                                                                                                                  | NO                                                             |
| `empty_confirmed`  | `LEG_ABSENT_LEFT`                                 | Cross-instrument calc: the LEFT leg (first instrument in the pair) had `empty_confirmed` or `attempted_failed` status — the paired calc cannot produce output. Emitted by features-cross-instrument for paired-price-dispersion and cross-venue arb calcs. Consumer: treat as honest empty — NaN-fill for ML; skip for execution.                                                                                                                                                          | NO                                                             |
| `empty_confirmed`  | `LEG_ABSENT_RIGHT`                                | Cross-instrument calc: the RIGHT leg (second instrument in the pair) had `empty_confirmed` or `attempted_failed` status — the paired calc cannot produce output. Mirror of `LEG_ABSENT_LEFT`. Consumer: same as `LEG_ABSENT_LEFT`.                                                                                                                                                                                                                                                         | NO                                                             |
| `empty_confirmed`  | `EXPECTED_NO_FUNDING_RATE_TICKS`                  | features-service `perp_funding_rates` adapter found no funding-rate ticks for the requested `(venue, symbol, date)`. Applies to both CeFi (`features_service/cefi/calculators/perp_funding_rates.py`) and DeFi (`features_service/onchain/calculators/perp_funding_rates_defi.py`) paths. Consumer: strategy-service — skip the trade (no funding signal); ML — NaN-fill. Shipped: features-service@e43f8370 per `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` Phase A. | NO                                                             |
| `empty_confirmed`  | `EXPECTED_NO_PNL_STREAM`                          | features-service `performance_features` passthrough subdomain received no `StrategyPnlStreamEvent` upstream for this day. Off-by-default for May-23 cutover: no upstream PnL stream wired → every day is `empty_confirmed` with this reason until trading-agent-service directive emission is enabled. Shipped: features-service@2a7af305 per `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` Phase H.                                                                    | NO                                                             |

> **[DELTA 2026-05-22]** **Current state:** Two new `empty_confirmed` reasons added above:
> `EXPECTED_NO_FUNDING_RATE_TICKS` (features-service perp_funding_rates adapter) and `EXPECTED_NO_PNL_STREAM`
> (performance_features passthrough, off-by-default May-23). **Planned delta:**
> `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` Phase A shipped these; codex was missing both
> entries. Fixed 2026-05-22 codex audit. **Target architecture:** Both reasons codified in UAC `EmptyConfirmedReason`
> enum and in this table. UAC enum addition tracked in the plan's Codex SSOT updates section.

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

> **[DELTA 2026-06-01 — codex audit status]** **Current state:** 33-reason taxonomy table above + per-source sports
> coverage rules (Wave 3.S, `§ Per-source sports coverage rules`) + 4-state consumer-class table
> (`§ Per-service consumer-class — 4-state`) + per-reason-group consumer policy quick-reference
> (`§ Per-reason-group → consumer policy`) all shipped 2026-05-22. One remaining pending item:
>
> - **`DATA_QUALITY_SUSPECTED_GAP` reason** (writegate plan Phase MDPS liquidity baseline, line ~4191):
>   `record_failed(reason=DATA_QUALITY_SUSPECTED_GAP)` when MDPS tick-rate < 20% of baseline. UAC `RecordFailedReason`
>   enum addition pending. Add a row to the reason taxonomy table when UAC lands this reason.
>
> All other pending items from the 2026-05-22 morning delta note are now ✅ delivered.

---

**Cross-references for the reason taxonomy**:

- §
  [Reader-side fallback for legacy rows](#reader-side-fallback-for-legacy-rows-codified-2026-05-07--operator-gap-finding)
  — how consumers handle `error_reason=None` in rows written before Phase 2.E.1
- § [Reconciler chain for legacy error_reason](#reconciler-chain-for-legacy-error_reason-the-three-passes) — the three
  `instruments-service/scripts/reconcile_*.py` passes that retrospectively backfill typed reasons
- Per-asset-group backfill runbook (shipped 2026-05-07):
  [`codex/02-data/expected-absence-backfill-runbook.md`](./expected-absence-backfill-runbook.md) — volumes per
  asset_group, invocation recipe, reconciler + enumerator scripts
  (`instruments-service/scripts/reconcile_expected_absence_reasons.py` + `enumerate_expected_universe.py`), UTL
  reader-side fallback `classify_legacy_empty_row()`

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

### Per-asset-group × data_type routing quick-reference

The consumer-class rules above apply uniformly. The table below shows the most common reason codes per asset_group ×
data_type combination — the patterns engineers hit most in practice:

| asset_group  | data_type         | Most common `EXPECTED_*` reason(s)                                      | Consumer class (typical)                                   |
| ------------ | ----------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------- |
| `cefi`       | `ohlcv_24h`       | `EXPECTED_INSTRUMENT_DELISTED`; `EXPECTED_INSTRUMENT_NOT_LISTED`        | Feature rolling-window (adjust denominator)                |
| `cefi`       | `funding_rate`    | `EXPECTED_INSTRUMENT_DELISTED`; `SOURCE_RETURNED_ZERO` (no perp on day) | Strategy live — skip trade; ML — NaN-fill                  |
| `defi`       | `lending_indices` | `EXPECTED_PRE_GENESIS_CHAIN`; `EXPECTED_PRE_SOURCE_COVERAGE_START`      | Feature same-day single-sample — emit `record_empty`       |
| `defi`       | `lst_rates`       | `EXPECTED_PRE_SOURCE_COVERAGE_START`; `EXPECTED_INSTRUMENT_NOT_LISTED`  | Feature rolling-window (adjust denominator)                |
| `defi`       | `gas_fees`        | `EXPECTED_PRE_GENESIS_CHAIN`                                            | Feature same-day single-sample — emit `record_empty`       |
| `tradfi`     | `ohlcv_1d`        | `EXPECTED_HOLIDAY`; `EXPECTED_WEEKEND`; `EXPECTED_PARTIAL_HALF_DAY`     | Feature rolling-window (adjust denominator)                |
| `tradfi`     | `ohlcv_15m`       | `EXPECTED_OUTSIDE_TRADING_HOURS`; `EXPECTED_HOLIDAY`                    | Feature rolling-window (adjust denominator); intraday only |
| `sports`     | `match_odds`      | `EXPECTED_PAUSED_LEAGUE`; `EXPECTED_PRE_SEASON`; `EXPECTED_POST_SEASON` | Feature rolling-window (adjust denominator)                |
| `sports`     | `match_results`   | `EXPECTED_PAUSED_LEAGUE`; `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`       | ML training — NaN-fill                                     |
| `prediction` | `market_prices`   | `EXPECTED_INSTRUMENT_NOT_LISTED`; `EXPECTED_INSTRUMENT_DELISTED`        | ML training — NaN-fill; execution — skip                   |

Use the `n_valid` sibling column on all rolling-window calcs so downstream consumers can observe the effective
denominator. For same-day single-sample calcs with `empty_confirmed`, emit `record_empty(reason=NO_INPUT_AVAILABLE)` for
the calc's own output row rather than NaN-filling (the difference: NaN-fill is a value; `record_empty` is honest absence
with a typed reason).

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

## Per-reason-group → consumer policy quick-reference

> Codified 2026-05-22 — fulfils writegate plan P1 `[DOCS]` item line 2922. Companion to the per-service consumer-class
> table above. Groups the 33-member `EmptyConfirmedReason` closed set by semantic meaning; columns give the per-consumer
> policy for each group. All rows assume `capture_status=empty_confirmed` unless noted.

| Reason group                        | `EmptyConfirmedReason` members                                                                                                                                                       | Rolling-window denominator policy                                                                                                                                                                | ML training / inference                                                                                                              | Live execution                                                                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Calendar / schedule — whole day** | `EXPECTED_HOLIDAY` · `EXPECTED_WEEKEND`                                                                                                                                              | Window spans **trading days only** — weekend and holidays are outside the N-day window by construction. Denominator = n_trading_day_samples. Do NOT count these as "missing days within window." | NaN-fill                                                                                                                             | Skip silently — no alert. Calendar says closed; expected behavior.                                                                                 |
| **Intra-day / partial session**     | `EXPECTED_OUTSIDE_TRADING_HOURS` · `EXPECTED_PARTIAL_HALF_DAY`                                                                                                                       | Drop out-of-session bars from the rolling window; denominator = n_session_bars actually within published hours. Partial day: count actual bar count, not expected full-session bar count.        | NaN-fill                                                                                                                             | Skip the bar / time-slot — no alert. Session gate says closed.                                                                                     |
| **Lifecycle — not yet listed**      | `EXPECTED_INSTRUMENT_NOT_LISTED` · `EXPECTED_PRE_VENUE_LAUNCH` · `EXPECTED_PRE_GENESIS_CHAIN` · `EXPECTED_PRE_SOURCE_COVERAGE_START` · `EXPECTED_PRE_SEASON` · `EXPECTED_NO_FIXTURE` | Exclude from window span — data will never exist for these dates; include only dates ≥ instrument/venue/chain/season start. Denominator = n_valid_in_window.                                     | NaN-fill                                                                                                                             | Skip silently — no alert. Instrument or source did not exist on that date.                                                                         |
| **Lifecycle — permanently gone**    | `EXPECTED_INSTRUMENT_DELISTED` · `EXPECTED_PAST_SOURCE_COVERAGE_END` · `EXPECTED_DEPRECATED_DATA_TYPE` · `EXPECTED_POST_SEASON`                                                      | Exclude from window span — data ceased at a known date. Do not extend window to compensate.                                                                                                      | NaN-fill                                                                                                                             | Skip silently — no alert. Instrument or source retired after that date.                                                                            |
| **Temporary gap / pause**           | `EXPECTED_PAUSED_LEAGUE` · `EXPECTED_REFDATA_CADENCE_CHANGE` · `EXPECTED_OUT_OF_COVERAGE_WINDOW` · `EXPECTED_PROTOCOL_PAUSED` · `EXPECTED_OUTSIDE_TRANSFER_WINDOW`                   | Date falls inside the calendar window span; denominator = n_valid (exclude the paused day from the numerator and denominator). Gap is expected to resolve in the future.                         | NaN-fill                                                                                                                             | Skip silently — no alert. Pause is documented and expected.                                                                                        |
| **Source-specific / no coverage**   | `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` · `EXPECTED_KNOWN_SOURCE_GAP` · `SOURCE_RETURNED_ZERO`                                                                                       | Include date in window span; denominator = n_valid. `SOURCE_RETURNED_ZERO` warrants an optional per-service soft monitoring counter for anomaly detection — not a page.                          | NaN-fill                                                                                                                             | Skip. Optional soft alert on `SOURCE_RETURNED_ZERO` (configurable per service; not default).                                                       |
| **Sports event status**             | `EXPECTED_FIXTURE_POSTPONED` · `EXPECTED_FIXTURE_CANCELLED` · `EXPECTED_OUTSIDE_PROCESSING_SCOPE`                                                                                    | Skip day in rolling window; denominator = n_valid.                                                                                                                                               | NaN-fill                                                                                                                             | Skip silently — no alert. Event-level absence (fixture not played).                                                                                |
| **Upstream cascade**                | `EXPECTED_UPSTREAM_EMPTY` · `NO_INPUT_AVAILABLE` · `EXPECTED_NO_FUNDING_RATE_TICKS` · `EXPECTED_NO_PNL_STREAM` · `LEG_ABSENT_LEFT` · `LEG_ABSENT_RIGHT`                              | Skip day; denominator = n_valid. Do NOT attempt compute when upstream is absent.                                                                                                                 | NaN-fill OR emit `record_empty(reason=NO_INPUT_AVAILABLE)` for the calc's own output — per-calc choice; document in calc docstring.  | Skip. Log at INFO level (upstream is known empty; not a pipeline failure).                                                                         |
| **Migration artifact**              | `EXPECTED_LEGACY_MIGRATION_MISSING_EXPIRY`                                                                                                                                           | Skip day; denominator = n_valid. Resolves after migration backfill completes.                                                                                                                    | NaN-fill                                                                                                                             | Skip silently — no alert. Resolves post-migration.                                                                                                 |
| **`attempted_failed` (any reason)** | `ClusterCoverageError` · `SCHEMA_VALIDATION_FAILED` · `CLASSIFIED_VENUE_ERROR` · `UPSTREAM_SUBGRAPH_ZERO` · `UPSTREAM_LIVE_GAP` · others                                             | **Exclude from window.** Do NOT forward-fill with prior day's value — data may exist but was corrupted in transit.                                                                               | NaN-fill AND add `data_quality_flag=ATTEMPTED_FAILED` sibling column so the model can learn to discount these regions if it chooses. | **Block live trade** for affected assets + fire alert. Live mode does not trade through pipeline failures. Backtest mode treats as honest absence. |

### Key distinction: calendar-closed vs temporary gap for rolling windows

**Calendar-closed days (`EXPECTED_HOLIDAY`, `EXPECTED_WEEKEND`)** are OUTSIDE the N-day window by construction — a
20-day trading SMA spans 20 trading days; weekend/holiday dates are never in the window to begin with.

**Temporary gaps** (`SOURCE_RETURNED_ZERO`, `EXPECTED_PAUSED_LEAGUE`) fall INSIDE the calendar span but had no data.
These reduce the effective denominator: a 20-day window with 2 paused-league days computes the mean of 18 valid samples
while the lookback span stays 20 calendar days.

Getting this wrong produces a biased estimator: treating a holiday as a missing-within-window day inflates the true
window size; treating a paused-league day as calendar-closed narrows the lookback span incorrectly.

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

## Per-source sports coverage rules (Wave 3.S)

> Shipped 2026-05-22 — UAC@83c0e789. SSOT: `unified_api_contracts/registry/sports_per_source_rules.py`.

The Wave 3.S dimension tracks which `(source, league_id, day)` combinations are **expected to have data** vs expected to
be absent. Each source has a different coverage shape:

| Source         | Coverage gate                                                      | `EmptyConfirmedReason` emitted                                                        |
| -------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `understat`    | Fixed league whitelist (`UNDERSTAT_COVERED_LEAGUES`)               | `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` if `league_id` ∉ whitelist                    |
| `understat`    | Archive coverage-start date (`SOURCE_COVERAGE_START["understat"]`) | `EXPECTED_PRE_SOURCE_COVERAGE_START` if `day < coverage_start`                        |
| `footystats`   | Archive coverage-start date                                        | `EXPECTED_PRE_SOURCE_COVERAGE_START` if `day < coverage_start`                        |
| `footystats`   | Per-league season bounds (`footystats_season_status_for_day()`)    | `EXPECTED_PRE_SEASON` or `EXPECTED_POST_SEASON`                                       |
| `api_football` | Archive coverage-start date                                        | `EXPECTED_PRE_SOURCE_COVERAGE_START` if `day < coverage_start`                        |
| any source     | Transfer-window gate for `data_type=transfer_records`              | `EXPECTED_OUTSIDE_TRANSFER_WINDOW` if `is_transfer_window_open(league_id, day)=False` |

### Uniform entry point

`sports_per_source_rules.is_expected_for_source(source, league_id, day, *, data_type=None) -> tuple[bool, str | None]`

Returns `(True, None)` if data is expected; `(False, <EmptyConfirmedReason>)` if the shard is expected absent. Call this
at the orchestrator-queue or per-shard pre-flight gate — it replaces ad-hoc source-specific checks.

```python
from unified_api_contracts.registry.sports_per_source_rules import is_expected_for_source

expected, reason = is_expected_for_source(source, league_id, day, data_type=data_type)
if not expected:
    writer.record_expected_empty(row_key=..., reason=reason)
    continue
```

### Data types covered by bundled cluster validation

Sports shards for `odds_snapshot` / `odds_movement` / `arbitrage_opportunity` require cluster validation at
`record_captured()` time (registered in `BUNDLED_DATA_TYPES` + `DATA_TYPE_TO_CLUSTER_REGISTRY`). The cluster extractor
is the **bookmaker set** per fixture; the registry name is `SPORTS_FIXTURE_CLUSTERS`. Pass `cluster_registry_name` and
`observed_clusters` kwargs to `record_captured()` for these data_types — `ManifestWriter` raises
`MissingClusterValidationError` if absent.

### Per-league season bounds (footystats)

`footystats_season_status_for_day(league_id, day)` returns:

- `None` — day is within an active season window; data expected
- `"EXPECTED_PRE_SEASON"` — day is before the season's schedule announcement date
- `"EXPECTED_POST_SEASON"` — day is after season end (post-playoff / offseason)

The season-bounds table lives in `unified_api_contracts.canonical.domain.sports.season_dates`. Add new
`(league_id, season_year)` → `(schedule_announced_at, season_end)` rows there when new leagues or seasons land.

### Adding a new sports source (expansion recipe)

1. Add the source's coverage-start date to `SOURCE_COVERAGE_START` in
   `unified_api_contracts.canonical.domain.sports.league_data`.
2. If the source has a league whitelist, add it to `unified_api_contracts.canonical.domain.sports.provider_league_ids`
   (same pattern as `UNDERSTAT_COVERED_LEAGUES`).
3. Add a `source_key == "<newsource>"` branch to `is_expected_for_source()` in `sports_per_source_rules.py`.
4. Add the corresponding `EmptyConfirmedReason` enum value to UAC `honest_coverage.py` if a new reason is needed.
5. Re-run `reconcile_legacy_blank_to_typed_reason.py` (scan-only first, then `--apply-flips` after CSV review) to
   upgrade historical rows that previously landed on `SOURCE_RETURNED_ZERO` or `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`.
6. Add a row to the per-source table in this section.

---

## Multi-source cell consumer policy (TradFi dual-source, v9)

> Added 2026-05-28 — Phase 6 of `tradfi_massive_dual_source_2026_05_28.md`. **Generalised 2026-06-01 to ALL asset
> groups** (`data_source_provenance_all_asset_groups_2026_06_01.md`): the union semantics +
> `select_primary_available_source()` resolution below are **asset-group-agnostic** and apply to every multi-source
> cell, not just tradfi — defi `oracle_prices` (`pyth_hermes`/`chainlink`) + `native_staking_rates`
> (`solana_rpc`/`helius_rpc`), sports `FIXTURES` (`api_football`/`footystats`), and any cefi/prediction cell once a 2nd
> source lands. Single-source cells now also carry `source` (auto-stamped from the registry — universal stamping for
> swap-resilience); their consumer policy is trivial (one source). Computed/service-emitted cells (`COMPUTED_SOURCES`)
> are exempt (no `source`).
>
> **Read-path status (2026-06-01 finding)**: the resolver primitives are generic + unit-tested (uac@559dc81b) but **not
> yet wired into a non-test consumer**, and `manifest_consolidator.py` dedups multi-source rows by last-write-wins (its
> dedup key omits `source`) — i.e. the manifest collapses to the union row; per-source provenance lives in the parquet
> `source` column. Wiring the resolver into consumers + the consolidator-dedup-key decision are open Phase 5 todos.
>
> Applies to `asset_group=tradfi` (and now all multi-source groups) when a `(shard_key, day)` cell has manifest rows
> from multiple sources (e.g. `source=databento` + `source=massive`). Requires v9 manifest schema with the `source`
> column populated.

### Union semantics for multi-source cells

When a TradFi cell has manifest rows from more than one source, the downstream consumer resolves the cell's effective
`capture_status` by **union**: if at least one source row has `capture_status=captured`, the cell is treated as
`captured` for all downstream purposes.

| Source A `capture_status` | Source B `capture_status` | Resolved cell status | Downstream action                                                                                                                  |
| ------------------------- | ------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `captured`                | `captured`                | `captured`           | Use highest-priority source per `SOURCE_PRIORITY`; log divergence if content differs (`DivergenceKind.DUAL_SOURCE_DUPLICATE`)      |
| `captured`                | `empty_confirmed`         | `captured`           | Use the captured source; source B's empty reason noted but does NOT downgrade the cell                                             |
| `captured`                | `attempted_failed`        | `captured`           | Use the captured source; alert on source B's failure separately (per-source alert, not cell-level `DependencyError`)               |
| `empty_confirmed`         | `empty_confirmed`         | `empty_confirmed`    | Both absent; apply normal per-reason taxonomy (see `## Reason taxonomy`) — the stricter / more informative reason wins for logging |
| `attempted_failed`        | `attempted_failed`        | `attempted_failed`   | Both failed; block live trade, alert                                                                                               |

**Critical rule**: a single `attempted_failed` source does NOT block a consumer when another source is `captured`. The
failure is recorded and alerted per source, but the cell-level status is `captured`. This is the key difference from the
single-source world where any `attempted_failed` immediately triggers `DependencyError`.

### Per-reason taxonomy unchanged

The `error_reason` taxonomy (see `## Reason taxonomy` and `## Per-reason-group → consumer policy`) applies **per source
row** — not to the resolved cell status. A source B row with `capture_status=empty_confirmed[EXPECTED_HOLIDAY]` still
means "source B expected empty on that holiday." The union resolution step runs AFTER per-source reason validation.

Consumers do NOT need to modify their reason-group handling (NaN-fill / skip / adjust denominator). Those rules apply to
the resolved cell status. If the resolved status is `captured` (because source A is captured), the consumer proceeds
normally; it never sees the source B empty row directly.

### Source priority resolution

When the resolved cell status is `captured` and multiple sources contributed captured rows, the consumer selects the
primary source using `select_primary_available_source()` from
`unified_api_contracts.canonical.crosscutting.source_priority`:

```python
from unified_api_contracts.canonical.crosscutting.source_priority import (
    select_primary_available_source,
    detect_dual_source_conflicts,
)

# rows_by_source: dict[str, pd.DataFrame] — keyed by source string
primary_source = select_primary_available_source(
    rows_by_source=rows_by_source,
    asset_group="tradfi",
    data_type=data_type,
)
df = rows_by_source[primary_source]
```

`SOURCE_PRIORITY[("tradfi", data_type)]` determines source preference order (e.g. `["databento", "massive"]` for OHLCV
data types). `select_primary_available_source` returns the highest-priority source whose manifest row is `captured`.

### Conflict detection when both sources are captured

If both sources have `captured` status for the same cell (expected state after Phase 5 Massive backfill), call
`detect_dual_source_conflicts()` to surface any divergences before committing to a primary:

- `DivergenceKind.DUAL_SOURCE_DUPLICATE` — both sources present but content is identical; deduplicate silently
- `DivergenceKind.VALUE_DIVERGENCE` — OHLCV values differ between sources beyond tolerance; log + alert (primary source
  wins; do NOT blend or average the two)
- `DivergenceKind.COVERAGE_DIVERGENCE` — one source has more bars than the other; primary source wins

These divergences are soft warnings for the reconciliation audit; the primary source's data is always the authoritative
downstream output.

### Pre-flight gate adaptation

When the pre-flight gate checks a TradFi cell's upstream status (step 2 from `## Pre-flight validation`), it MUST apply
union semantics before deciding whether to proceed or raise `DependencyError`:

```python
def resolve_cell_status(
    manifest_rows: list[AvailabilityRecord],  # one per source for this (shard_key, day)
) -> CaptureStatus:
    """Union: captured beats empty_confirmed beats attempted_failed."""
    statuses = {r.capture_status for r in manifest_rows}
    if CaptureStatus.CAPTURED in statuses:
        return CaptureStatus.CAPTURED
    if CaptureStatus.EMPTY_CONFIRMED in statuses:
        return CaptureStatus.EMPTY_CONFIRMED
    return CaptureStatus.ATTEMPTED_FAILED
```

A cell with `attempted_failed` from source A but `captured` from source B resolves to `captured` — no `DependencyError`.
The source B failure is tracked and alerted via per-source alerting without blocking the consumer.

### Scope

This section applies only when ALL of the following are true:

- `asset_group=tradfi`
- v9 manifest schema — `source` column populated (non-empty) on TradFi rows
- Multiple source rows exist for the same `(shard_key, day)` combination

For `asset_group` ≠ `tradfi`, each cell has exactly one source row (source column is `""`); this section does not apply
and standard single-source rules govern.

### Cross-references

- `SOURCE_PRIORITY` registry + UAC multi-source merge logic:
  `unified_api_contracts.canonical.crosscutting.source_priority`
- v9 `source` column definition + backfill plan:
  [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) § _Schema v9_
- Phase 5 Massive backfill (blocked BLK-b00254d7 pending MASSIVE_API_KEY credential):
  `tradfi_massive_dual_source_2026_05_28.md` Phase 5

---

## Per-service consumer-class — 4-state `capture_status` handling

> **Codified 2026-05-22** — fills the P0 gap from `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 3.D.3.
> Cross-reference: `expected_unattempted` cascade contract in `availability-manifest-and-data-status.md` §
> "`expected_unattempted` cascade contract".

The table below is the quick-reference for the 4 pipeline services most commonly asked about. For the full
consumer-class taxonomy (ML training, rolling-window features, same-day features, execution, reconciliation) see the
`## Per-service consumer-class audit` section above.

| Service              | `empty_confirmed[EXPECTED_*]` handling                                                                                                             | `empty_confirmed[SOURCE_RETURNED_ZERO]` handling                                                | `attempted_failed` handling                                                                                               | `expected_unattempted` handling                                                                      |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **MDPS**             | Write zero-volume / forward-fill-last-price bars (price continuity preserved; not a data quality issue)                                            | Same — write zero-volume / forward-fill bars                                                    | Write **NaN** — do NOT forward-fill (data may exist but fetch failed; downstream must not treat silence as zero-activity) | Record `expected_unattempted` in MDPS manifest + skip this shard entirely                            |
| **features-service** | Skip if reason is `EXPECTED_*` (calendar/lifecycle expectation met); write `record_empty(reason=EXPECTED_UPSTREAM_EMPTY)` for service's own output | Alert if unexpected for the asset_group; otherwise NaN-fill / adjust rolling-window denominator | Alert + write `record_empty(reason=NO_INPUT_AVAILABLE)` for service's own output; do NOT attempt the calc                 | Propagate as `record_expected_unattempted(reason=EXPECTED_UPSTREAM_EMPTY)` — do NOT attempt the calc |
| **strategy-service** | **Batch/backtest**: skip the asset for that allocation cycle (no signal). **Live**: skip asset + rebalance across remaining universe               | Same skip logic as `EXPECTED_*`                                                                 | **Batch**: treat as honest absence; skip. **Live**: BLOCK trade emission for affected assets + alert                      | Skip; schedule retry when upstream shard eventually resolves to `captured` or `empty_confirmed`      |
| **deployment-api**   | Show as grey cell in data-status UI; reason tooltip from `error_reason`                                                                            | Show as grey cell; tooltip says "source returned empty"                                         | Show as orange cell in UI; alert fired; tooltip shows classified error                                                    | Show as pending cell (clock icon); tooltip says "pipeline not yet run for this window"               |

**The key rule for `expected_unattempted`:** Every service in the cascade MUST propagate `expected_unattempted`
downstream rather than silently skipping or raising `DependencyError`. The propagation uses
`record_expected_unattempted(reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY)`. This ensures the full pipeline state
is visible in each service's manifest without masking the scheduling artifact as a failure.

**Why `attempted_failed` is different from `expected_unattempted` at strategy-service:** `attempted_failed` means real
upstream data was attempted but corrupted/lost — live strategy cannot trade through a pipeline failure with unknown
quality. `expected_unattempted` means the pipeline window has not opened yet — strategy retries when the window
resolves, without triggering an alert.

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

> **⚠️ MARKER RECONCILIATION (B2, 2026-06-02 — `fleet_audit_triad_deferred_followups_2026_06_01.md`).** The
> `zero_activity=True` boolean column described throughout this section was the original case-D _design_ marker; it has
> **no code consumers** and was **never implemented as a column**. The carry-forward / no-trade-bar behaviour shipped
> instead via `BaseCandleAdapter._finalize_session_grid(...)` (MDPS leading-NaN workstream, 2026-06-02), and the
> **as-shipped marker is `staleness_seconds > 0` AND `trade_count == 0`** (the forward-filled bar carries the last
> traded price with a non-zero `staleness_seconds`), NOT a `zero_activity` flag. **Model split (operator-ruled):**
> tradfi / cefi / defi session-grid candles are **dense forward-filled, never NaN** → identify a carried bar by
> `staleness_seconds>0 + trade_count==0`; **prediction** Category-D uses the **nullable-OHLCV** variant and emits
> NaN-OHLC bars (a distinct marker — nullable OHLC is allowed only for `prediction`/`sports`). Wherever a row below says
> `zero_activity=True`, read it as "the shipped `staleness_seconds>0 + trade_count==0` carried bar" (cefi/tradfi/defi)
> or the NaN-OHLC bar (prediction). Canonical contract: `codex/06-coding-standards/adapter-finalization-contract.md` + §
> "Per-adapter density contract" below.

> **Status**: audit complete (2026-05-11, `wave3x_residual_ssots_2026_05_08.md` Track D); the **dense forward-fill
> carry-forward shipped 2026-06-02** via `_finalize_session_grid` (see banner above + § "Per-adapter density contract").
> The originally-scoped separate `zero_activity_bars` UTL primitive was **not** built — the finalizer subsumes it.
> Reference audit: `plans/archive/issues/wave3x_track_d_findings_2026_05_11.md`.

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

> Shipped 2026-05-15 — MTDS@038a611, tradfi_master.md § "Replace zero-volume bars during non-tradeable sessions."

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

When the v2 instrument-grain enumerator lands (sequenced under `plans/epics/manifest_master.md` gate G3), the manifest's
`expected_unattempted` denominator grows by ~100× (from ~1.4M venue-grain rows to ~190M instrument-grain rows).
Downstream consumers that compute honest-coverage percentages must handle this volume change:

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
- Writegate Phase 2.E.2 plan item: `plans/epics/tradfi_master.md` § "Replace zero-volume bars during non-tradeable
  sessions."

## Phase 8 honest-coverage VM cron pattern (B-018 Phase 8.A, 2026-05-15)

Daily measurement of honest-coverage runs on a GCE VM launched by Cloud Scheduler. This is the shipped
continuous-verification path for the manifest's `empty_confirmed` / `expected_unattempted` rows.

### Components

| Component          | Path                                                                                                                                 | Notes                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| VM launcher        | `deployment-service/scripts/vm/launch-honest-coverage-vm.sh`                                                                         | Primary — all asset groups, Cloud Scheduler target  |
| Ad-hoc launcher    | `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh`                                                                 | Per-asset-group filter via `--asset-group`          |
| Scheduler setup    | `deployment-service/scripts/vm/setup-honest-coverage-scheduler.sh`                                                                   | Creates `honest-coverage-daily` Cloud Scheduler job |
| Measurement script | `instruments-service/scripts/measure_honest_coverage.py --asset-group all`                                                           | Runs inside VM, writes to GCS                       |
| Output bucket      | resolved via `resolve_bucket_name("honest-coverage")/{date}/coverage.json` (actual bucket: `central-element-323112-honest-coverage`) | Consumed by deployment-api                          |
| API consumer       | `deployment-api GET /api/data-status/honest-coverage` (Phase 2C)                                                                     | UI-facing honest-coverage endpoint                  |

### Cron schedule

Cloud Scheduler job `honest-coverage-daily` fires at **00:30 UTC daily** and calls the VM launcher. The launcher
enforces a singleton lock — refuses to start if any `honest-coverage-*` VM is RUNNING — so overlapping runs do not
corrupt the GCS output.

### VM spec

- Machine: `e2-standard-2` in `asia-northeast1-c`
- Boot disk: 50 GB
- Auto-shutdown: VM terminates after `measure_honest_coverage.py` exits (STARTED + STOPPED lifecycle events)
- Cost: ~5–15 min runtime → < $0.01/day

### Watchdog registration

VM name prefix `honest-coverage-` is registered in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`. The watchdog tracks
heartbeats but does NOT kill honest-coverage VMs (they are inherently short-lived; heartbeat-only mode).

### Operational rules (derived from workspace HARD RULES)

1. **No fire-and-forget**: VM must emit STARTED within 60 s and STOPPED/FAILED at exit.
2. **Per-VM shard isolation**: set `VM_NAME=honest-coverage-{date}` + `MANIFEST_PER_VM_SHARDS=true`.
3. **Ad-hoc runs**: use `launch-measure-honest-coverage-vm.sh --asset-group {group}` for partial re-runs; do NOT re-run
   the daily launcher with `--force` unless the scheduler job failed.

### Cross-references

- Plan: `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 2B + B-018 Phase 8.A.
- Deployment codex: `codex/05-infrastructure/vm-tarball-deployment.md` (tarball creation for VM code).
- QG enforcement: STEP 5.66 (`MANIFEST_PER_VM_SHARDS=true`) + STEP 5.61 (STARTED/STOPPED lifecycle).

## Scenario-driven gap injection

The scenario harness can produce **synthetic gaps** via two `ScenarioMutationSpec` types from
[`../04-architecture/scenario-injection-architecture.md`](../04-architecture/scenario-injection-architecture.md):

- **`DropRows`**: drops one or more data rows mid-sequence at the `MANIFEST` tap layer, causing the manifest writer to
  emit `empty_confirmed[SOURCE_RETURNED_ZERO]` or `attempted_failed` depending on the harness config.
- **`ManifestPhantom`**: injects a phantom manifest row with a configurable `capture_status` (any of the 4-state
  taxonomy: `captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted`) and a specified reason code.

### Per-row `scenario_id` provenance

Every manifest row produced by a scenario injection carries:

- `synthetic=true` on the emitted event (alerting-service suppresses paging on `synthetic=true` rows)
- `scenario_id: str` — the snake_case scenario identifier from the UAC `SCENARIO_REGISTRY`

Downstream consumers receiving a scenario-injected gap row MUST use the `scenario_id` column to distinguish
scenario-fire from real-fire when computing quality metrics or firing alerts. The `ScenarioReport` parquet produced by
`ScenarioMatrixRunner` carries per-row `scenario_id` for attribution.

### Consumer-class behavior under synthetic gaps

The consumer-class rules from the
[Per-service consumer-class audit](#per-service-consumer-class-audit-2026-05-07--operator-direction) table apply
unchanged for synthetic gaps — the consumer does not need to know the gap is synthetic in order to apply the correct
handling (skip / NaN-fill / alert). The two scenario-aware differences are:

1. **Alerting suppression**: alerting-service checks `synthetic=true` before firing a page. Human-facing alerts do NOT
   fire for scenario rows. Internal `SCENARIO_OUTCOME_ASSERTION_FAILED` alerts still fire (they are test-harness
   signals, not production pages).
2. **Attribution audit**: downstream services that write secondary manifests (features-service, strategy-service) must
   propagate `scenario_id` on their own output rows so the full scenario-fire provenance chain is traceable from MTDS
   input → features output → strategy signal.

### Manifest-layer scope

`MANIFEST` tap layer is DEFERRED to post-cutover per Phase 3.G. Pre-cutover scenario-driven gap injection is limited to
the `ORDER` layer (adversarial fill rejection / matching-engine adversarial mode) — these do not produce manifest gaps
directly. Full gap-injection scenarios (DropRows + ManifestPhantom) activate post-cutover per
[`../../plans/active/simulation_scenarios_post_cutover_2026_06_01.md`](../../plans/active/simulation_scenarios_post_cutover_2026_06_01.md).

---

## ODDS NaN-fill semantics (sports)

> Codified 2026-05-23 — fulfils sports_master.md P1 item (§ "EXPECTED_BOOKMAKER_MARKET_SETS NaN-fill enumeration").

### Background

The instruments-service ODDS orchestrator today fetches the day-level ODDS endpoint for each fixture date. When a
(fixture × bookmaker × market_type) triple is expected but the source doesn't return it, zero rows are produced instead
of a NaN-fill row. This violates the zero-volume-bar precedent from category-D MDPS: **missing triples must be
represented as NaN-fill rows** so downstream features can distinguish "source returned no odds for this bookmaker" from
"we never queried this bookmaker."

### NaN-fill vs `record_empty` for ODDS

| Scenario                                                       | Correct mechanism                                            | Why                                                                                                                           |
| -------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Expected (fixture × bookmaker × market) not in source response | `record_captured` with NaN payload values                    | Triple was expected (per `EXPECTED_BOOKMAKER_MARKET_SETS`); source didn't return it — that's data absence, not source absence |
| Source ODDS endpoint returned HTTP error for a date            | `record_failed(reason=CLASSIFIED_VENUE_ERROR)`               | The entire source was unavailable, not just one triple                                                                        |
| Bookmaker genuinely doesn't offer this market type             | `record_empty(reason=EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE)` | Structural gap, not a transient miss                                                                                          |

### Consumer policy for NaN-fill ODDS rows

| Consumer                                                | Policy                                                                                                                                                                        |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Arbitrage calculator** (odds dispersion across books) | **Drop NaN bookmakers** from the pricing comparison. Arbitrage requires ≥2 valid book quotes; NaN book is not valid. Already the correct behavior in the existing calculator. |
| **Odds-movement / CLV calculator**                      | **Treat NaN snapshot as no-update.** Forward-fill with the most recent non-NaN snapshot for the (fixture × bookmaker × market) triple. Already the correct behavior.          |
| **ML training**                                         | NaN-fill the feature value and add `data_quality_flag=ODDS_MISSING_BOOKMAKER` for model discounting.                                                                          |
| **Pre-match execution (arbitrage live)**                | Skip trade if NaN-fill drops below N_MIN_BOOKS (configurable, default 3). Do not enter a trade with only 1 book quote.                                                        |

### Implementation note

When `EXPECTED_BOOKMAKER_MARKET_SETS` is shipped (sports_master.md P0 orchestrator step), the NaN-fill rows are written
at the same `record_captured` call that writes the valid triples for a fixture — same parquet, same date partition. The
NaN payload conforms to the ODDS UAC schema: all price/volume columns are `float = NaN`; `bookmaker_id` and
`market_type` are populated (they ARE the identity of the gap).

**Cluster validation**: `expected_root_clusters = {fixture_id: len(EXPECTED_BOOKMAKER_MARKET_SETS[tier])}` ensures the
validator sees the correct denominator including NaN-fill rows.

---

## Per-source consumer policy — TradFi dual-source cells (v9, 2026-05-30)

**Plan**: `tradfi_massive_dual_source_2026_05_28.md`. **Live**: UTL@`c7bfa427`.

When both Databento and Massive run for the same TradFi `(venue, data_type, day)`, the manifest holds two rows
distinguished by `source`. Each row carries an independent `capture_status`.

### Union semantics — cell-level coverage

> **Rule**: a TradFi cell is treated as `captured` by downstream consumers if **at least one** source row has
> `capture_status=captured`. A cell is `attempted_failed` only when **all** source rows failed.

This matches the honest-coverage denominator policy: the `compute_honest_coverage` numerator counts a cell once
(captured) as long as any source delivered data, not once per source.

### Per-consumer policy table

| Consumer                                       | Policy when ≥1 source captured                                                                                                        | Policy when all sources failed                                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Feature pipeline** (MDPS → features-service) | Read the `SOURCE_PRIORITY`-ranked shard. Prefer `"massive"` over `"databento"` when both are `captured` (SOURCE_PRIORITY rank order). | Propagate `attempted_failed` upstream. Feature service records `EXPECTED_UNATTEMPTED` for downstream ML. |
| **ML training**                                | Use highest-priority captured source. Add `data_quality_flag=TRADFI_SINGLE_SOURCE` when only one of two expected sources is present.  | Mark training window as `DATA_MISSING`; do not impute.                                                   |
| **Execution service**                          | Use highest-priority captured source for reference pricing.                                                                           | Block execution for the affected instrument on that day; log `NO_TRADFI_DATA`.                           |
| **Data-status UI**                             | Show cell as `captured` (green). Tooltip lists per-source status breakdown.                                                           | Show cell as `attempted_failed` (red).                                                                   |
| **Honest-coverage rollup**                     | Cell counts as 1 captured row in numerator.                                                                                           | Cell counts as 1 attempted_failed row; excluded from numerator.                                          |

### Source priority for TradFi

The canonical ranking is defined in `unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY`. For
TradFi cells, `"massive"` ranks above `"databento"` when both are present (Massive has lower scrape latency and broader
options chain coverage). Consumers must not hard-code the order — read it from `SOURCE_PRIORITY` at runtime.

### Empty-confirmed from one source, captured from another

A cell where Massive returned zero rows for a day (legitimate market holiday gap) while Databento captured data is
valid:

```
(source=databento) → capture_status=captured
(source=massive)   → capture_status=empty_confirmed  (reason=SOURCE_RETURNED_ZERO)
```

Downstream consumers treat this cell as `captured` (union semantics). The `empty_confirmed` Massive row is logged and
visible in the data-status UI tooltip but does not degrade coverage percentage.

---

## §7 — CeFi expiry-window contract + 401≠honest-absence (backfill audit 2026-05-27)

> **Source**: operator direction 2026-05-27 + CeFi audit findings §1 + §2 of
> `cefi_venue_backfill_coverage_remediation_2026_05_27.md`. Codified here to prevent re-discovery.

### Expiry-window request-filtering contract

CeFi dated instruments (OKX futures, Deribit options/futures, Kraken futures) have a documented availability window
`[available_from, available_to_datetime]` sourced from `InstrumentRecord` (instruments-service SSOT via Tardis
`availableSince`/`availableTo`).

**Rule**: never request data for dates OUTSIDE `[available_from, available_to_datetime]`. The correct pre-request
filter:

```python
if available_from and date < available_from.date():
    record_empty(reason=EmptyConfirmedReason.EXPECTED_INSTRUMENT_NOT_LISTED)
    continue
if available_to and date > available_to_datetime.date():
    record_empty(reason=EmptyConfirmedReason.EXPECTED_INSTRUMENT_DELISTED)
    continue
```

**Why**: Tardis responds to out-of-window requests with `code 140: "Data … available only up to <date>"` (HTTP 400).
These 400s are not adapter errors — they are predictable consequences of requesting impossible (shard_key, day) pairs.
Attempting the request and recording `attempted_failed` is wrong; the correct manifest state is `expected_unattempted`.

**Shipped**: `market-tick-data-service@91e3df03` (OKX window filter in CeFi Tardis download path).
`instruments-service@ffb8192` (Kraken futures `_parse_underscore_yymmdd_symbol_expiry()` fallback to populate
`available_to_datetime` for `FI_XBTUSD_*` symbols).

| Scenario                                             | `capture_status`       | `error_reason`                           |
| ---------------------------------------------------- | ---------------------- | ---------------------------------------- |
| Date < `available_from` (pre-listing)                | `expected_unattempted` | `EXPECTED_INSTRUMENT_NOT_LISTED`         |
| Date > `available_to_datetime` (post-expiry)         | `expected_unattempted` | `EXPECTED_INSTRUMENT_DELISTED`           |
| Date in window, request succeeds                     | `captured`             | (none)                                   |
| Date in window, Tardis returns 400 for other reasons | `attempted_failed`     | `CLASSIFIED_VENUE_ERROR` or typed reason |

### 401≠honest-absence rule

**Rule**: HTTP 401 (expired API key / missing credentials) MUST be recorded as `attempted_failed`, NOT as
`empty_confirmed` or `expected_unattempted`.

**Operator direction 2026-05-27**: _"If the issue is 401, we should not mark that one as honest-absence — that will make
the data look corrupt."_

A 401 means the data EXISTS but is temporarily inaccessible due to a credential block. It is NOT a confirmed absence.

| Scenario                                | `capture_status`       | `error_reason`                                                     |
| --------------------------------------- | ---------------------- | ------------------------------------------------------------------ |
| HTTP 401 — expired key                  | `attempted_failed`     | `CLASSIFIED_VENUE_ERROR`                                           |
| HTTP 401 — missing key                  | `attempted_failed`     | `CLASSIFIED_VENUE_ERROR`                                           |
| HTTP 400 code 140 — out-of-window date  | `expected_unattempted` | `EXPECTED_INSTRUMENT_DELISTED` or `EXPECTED_INSTRUMENT_NOT_LISTED` |
| HTTP 400 other reason (e.g. bad symbol) | `attempted_failed`     | `CLASSIFIED_VENUE_ERROR`                                           |

**Why the distinction matters**: `empty_confirmed` tells downstream consumers "this data does not exist, skip it." A
401-era manifest stamped `empty_confirmed` looks identical to a correctly absent day — consumers will never retry and
the data gap becomes permanent even after key renewal. `attempted_failed` marks the cell as "retryable once key is
active," which is the correct operational state.

**Recovery path**: after Tardis API key renewal, re-run the backfill for all dates where manifest rows carry
`attempted_failed` due to 401s. The rows' `capture_status` will flip to `captured` once the download succeeds.

### Cross-references

- `cefi_venue_backfill_coverage_remediation_2026_05_27.md` §1 (expiry window), §2 (401 rule)
- `codex/04-architecture/cefi-batch-live.md` §9 (adapter-level expiry-window + 401 contract)
- `market-tick-data-service@91e3df03` — window filter implementation
- `instruments-service@ffb8192` — Kraken underscore-symbol expiry parser

---

## Per-adapter density contract: dense + LOCF + no leading NaN + carry-from-prior-day

> Codified 2026-06-02 from `plans/active/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md` (operator decisions
> 2026-06-01). Full contract + per-adapter table: `codex/06-coding-standards/adapter-finalization-contract.md`.

**Within-series density is a separate axis from shard-level honest absence.** Shard-level honest absence answers "did
this (venue × data*type × day) shard get captured at all?" (`captured` / `empty_confirmed` / `attempted_failed` /
`expected_unattempted`). The **density contract** governs what a \_captured* shard's per-bar series looks like: it must
be dense, LOCF-filled, and free of NaN in the required columns.

### The rule

Every MDPS candle adapter routes its full-day grid through `BaseCandleAdapter._finalize_session_grid(...)` before
returning. For a _captured_ shard:

- **No leading NaN.** Pre-first-observation bins are either **dropped** (cold-start — no prior observation to carry) or
  **carried from the prior day's last-known value** (`seed_price`/`seed_ts`/`seed_state`, PIT-safe — yesterday's close
  is known at 00:00, so batch==live with zero look-ahead).
- **No NaN OHLC.** State-only streams (derivative ticker, options/futures chains, liquidity/lending snapshots,
  book/quote) drive `o=h=l=c` from their state column (`state_col=mark_price`/`mid_price`/…) or from a populated `close`
  price proxy. OHLCV is non-nullable for every asset group except `prediction`/`sports`.
- **No NaN volume.** Trade-derived flow columns are zero-filled on snapshot bars (`flow_cols`); adapters that repurpose
  `volume` to carry a **real** value (liquidity TVL, market_state total-supply) stay **close-driven** so the value is
  preserved, never zeroed.
- **Open no-trade bars are forward-filled** `o=h=l=c=prev_close`, `volume=0`, with `staleness_seconds` recording how
  stale the carried price is — exactly what a live trader observes. `market_state==CLOSED` bars drop (untradeable).

### Honest-absence interaction

A _captured_ shard whose price driver is entirely absent (e.g. a derivative tick carrying funding but no mark price)
collapses to the **zero-row honest-absence output** rather than fabricating NaN-OHLC bars — i.e. the density contract
**defers to honest absence** when there is no price to anchor a candle. This is the per-bar expression of the same
"never emit silent placeholders" principle: no price → no candle → `record_empty_for_shard`, not a NaN row.

### Downstream consumer policy

- Consumers MAY trust that a _captured_ candle parquet has no NaN in `open`/`high`/`low`/`close`/`volume` (CeFi / DeFi /
  TradFi). A NaN there is an **adapter density bug**, not honest absence — surface it (the `fast_candle_aggregation.py`
  input-NaN WARN is the in-pipeline guard) rather than masking it.
- `staleness_seconds` is the signal for down-weighting/excluding stale carried bars — consumers gate on it instead of
  re-deriving "is this bar real?" from NaN patterns.
- Reprocessing existing parquets to densify them rides the deferred GCS backfill pass — never a standalone whole-corpus
  walk (single-walk discipline).

---

## OOW Denominator Partition — Never-Collectable Cells Excluded From Coverage % (2026-06-14)

### What is OOW?

**Out-of-coverage-window (OOW)** is a sub-partition of `empty_confirmed` rows that describe cells that were
**structurally never collectable** — not actionable gaps. Examples (UAC `is_out_of_coverage_window` classifier):

| UAC reason constant                            | Meaning                                                     |
| ---------------------------------------------- | ----------------------------------------------------------- |
| `EXPECTED_PRE_GENESIS_CHAIN`                   | Chain didn't exist on that date (e.g. pre-Solana-mainnet)   |
| `EXPECTED_PRE_LAUNCH_VENUE`                    | Venue/exchange not yet live                                 |
| `EXPECTED_INSTRUMENT_NOT_LISTED`               | Instrument delisted or not yet listed at that time          |
| `EXPECTED_DEPRECATED_DATA_TYPE`                | Data type retired/sunset, never collectable for that period |
| `EXPECTED_PAST_SOURCE_COVERAGE_END`            | Source's historical coverage ended before this date         |
| `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` | Sports/prediction markets outside the active season         |
| `EXPECTED_OUTSIDE_SCOPE`                       | Asset-group-level scope exclusion                           |
| (+ 8 more)                                     | See `unified_api_contracts.is_out_of_coverage_window`       |

### Denominator formula

```
denominator = captured + within_window_empty + attempted_failed + expected_unattempted
coverage_%  = captured / denominator × 100
```

**`out_of_window` is EXCLUDED from the denominator.** Including OOW cells (which were always empty by design) would make
coverage% look artificially low — the DeFi effect was 22.11% → 97.55% (+75.44pp) once OOW was excluded.

### Column name duality

The live consolidated index (`_index/availability_index.parquet`) uses `error_reason` for the reason column. The CF-20
beta projected parquet (`_index/audit/projected_index_{asset_group}.parquet`) uses `reason`. Downstream consumers
(deployment-api `coverage.py`) MUST accept BOTH:

```python
_reason_col = "error_reason" if "error_reason" in index.columns else (
    "reason" if "reason" in index.columns else None
)
```

### Where is OOW surfaced?

1. **deployment-api** (`deployment_api/services/data_status/coverage.py`, `_build_coverage_for_cat`): partitions
   empty_confirmed rows → `capture_status_counts["out_of_window"]` separate key, denominator excludes it.
2. **deployment-ui** (`src/api/client.ts`): `TurboSubDimension`, `TurboAssetGroupStatus`, `HonestCoverageStatusCounts`
   all carry `out_of_window?: number` (optional; absent = 0).
3. **deployment-ui** (`src/components/HonestCoverageCard.tsx`): `CoverageBar` renders OOW as a distinct slate-grey
   segment with tooltip "outside window — not a gap: N"; legend entry "outside window — not a gap".
4. **Tooltip** on the "reachable" badge notes OOW exclusion from the denominator.

### Ships

- deployment-api commit `149473c` (initial OOW partition) + `90a8ad7` (column-name resilience fix)
- deployment-ui commit `ea1db02` (type defs + mock data + UI rendering + 7 unit tests + 206 Playwright smoke tests)

### Verification (2026-06-14)

Real GCS data check on `gs://market-data-tick-defi-prd-central-element-323112/_index/audit/projected_index_defi.parquet`
(1.58M rows, updated 2026-06-11):

| Bucket                    | Count       |
| ------------------------- | ----------- |
| captured                  | 349,326     |
| empty_confirmed OOW       | 1,221,955   |
| empty_confirmed in-window | 6,016       |
| attempted_failed          | 2,740       |
| expected_unattempted      | 0           |
| **denominator**           | **358,082** |
| **coverage %**            | **97.55%**  |
| naive (OOW included)      | 22.11%      |
