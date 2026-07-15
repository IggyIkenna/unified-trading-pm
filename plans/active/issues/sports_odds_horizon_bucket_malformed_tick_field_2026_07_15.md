---
doc_type: issue
title:
  sports/odds_horizon_bucket_15m MalformedTickFieldError — 100%-causality-filtered odds ticks were misclassified as a
  malformed field instead of honest absence
summary:
  "Investigated the DP_RUN_MOSTLY_EMPTY alert for sports/odds_horizon_bucket_15m (66/66 attempted_failed,
  error_reason=MalformedTickFieldError, attempted_at=2026-07-13T23:56Z, flagged as a small-count-but-100%-ratio cell not
  yet covered by data_pipeline_alerts_batch_remediation_2026_07_15.md). Live re-query of BOTH plausible sports manifests
  found ZERO current attempted_failed rows with a Malformed* error_reason for this data_type — the 66-row figure has
  already drifted to 0 by the time of this investigation (see Investigation section for exact counts/paths checked).
  Traced the code path anyway and found a REAL, standing classification bug (not a transient regression):
  SportsBucketAssignmentAdapter.process_to_candles() raised MalformedTickFieldError whenever its helper
  _prepare_tick_data() returned an empty DataFrame, conflating two structurally different conditions — genuinely
  missing/broken schema columns vs. a well-formed tick frame where every row failed the bm_time <= fetch_utc causality
  check (bm_time is the ODDS_API vendor's own reported update time, which can genuinely skew relative to our fetch_utc
  for late-arriving/stale bookmaker snapshots — a real, reachable upstream-shaped condition, not a local bug). The
  100%-causality-drop case is honest absence, structurally identical to the adapter's own existing 'no h2h rows' Path A½
  precedent two code blocks above — it should never have raised MalformedTickFieldError. Fixed in
  market-data-processing-service@7ff43d7 with 3 new regression tests (coverage.xml-verified both branches hit)."
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, odds, mdps, data-correctness, honest-absence, malformed-tick-field, dp-run-mostly-empty]
related:
  [
    plans/active/data_pipeline_alerts_batch_remediation_2026_07_15.md,
    codex/02-data/honest-absence-downstream-handling.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: [operator-dispatched sub-agent, data_pipeline_alerts_batch_remediation_2026_07_15.md "New todos" section]
resolved_by: market-data-processing-service@7ff43d7197a50cfe52d9ad8fe514cd6a2ca09558
locked_by:
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# sports/odds_horizon_bucket_15m MalformedTickFieldError — misclassified honest absence

## Investigation

### Current live count (re-queried 2026-07-15, ~4h after the alert's attempted_at)

The plan doc's 66-row figure was sourced from the alert payload at `attempted_at=2026-07-13T23:56Z`. Re-querying live:

1. **`market-data-tick-sports-prd-central-element-323112`** `_index/availability_index.parquet` (the bucket named in the
   original task brief): `data_type == "odds_horizon_bucket"` → 124,294 rows, `capture_status` distribution
   `{captured: 123642, empty_confirmed: 652}` — **zero `attempted_failed` rows of any kind currently present** for this
   data_type in this bucket.
2. **`instruments-store-sports-prd-central-element-323112`** `_index/availability_index.parquet` (the CANONICAL sports
   availability manifest per the 2026-06-07 sports-manifest-canonicalisation decision documented inline in
   `market-data-processing-service/scripts/reprocess_sports_odds.py`'s `_resolve_manifest_bucket()` docstring — sports
   manifest numerator/denominator both route here, NOT to `market-data-tick-sports-*`):
   `data_type == "odds_horizon_bucket"` → 350,713 rows, `capture_status` distribution
   `{expected_unattempted: 199720, captured: 143594, empty_confirmed: 7395, attempted_failed: 4}`. The 4
   `attempted_failed` rows all carry `error_reason=RAW_ODDS_SHAPE_UNRECOGNIZED` — **zero `MalformedTickFieldError`
   rows**.

So the 66-row figure has genuinely drifted to 0 in both plausible manifest locations — not a live, currently-recurring
problem. This is consistent with either (a) the affected row_keys being naturally overwritten by a later successful
capture (the daily `reprocess_sports_odds.py` recon window re-attempts previously-`attempted_failed` dates automatically
— only `captured`/`empty_confirmed` prior statuses are skipped, see its `_process_one_date` pre-flight), or (b) the
original 66 rows coming from a one-off manual/ad-hoc run whose manifest writes were never part of ongoing scheduled
traffic to begin with (see below). Investigated the code anyway per the task brief, since a 100%-ratio alert on a real
(if now-stale) error class is worth root-causing regardless of current count.

### Which driver produces this error_reason

Two DIFFERENT drivers can produce `sports`/`odds_horizon_bucket` manifest rows, and only one of them can raise
`MalformedTickFieldError`:

- **`market-data-processing-service/scripts/reprocess_sports_odds.py`** — the dedicated, scheduled (2026-07-14 fix,
  `mdps_odds_horizon_scheduler.tf`, 01:15 UTC daily) batch reprocessor. It calls
  `SportsBucketAssignmentAdapter.process_to_bucketed_df()`, which does **not** raise on an empty result — it silently
  returns an empty DataFrame, and the caller classifies that as `MISSING_REQUIRED_COLUMN` or
  `ADAPTER_RETURNED_EMPTY_OUTPUT` instead. This script can never produce `error_reason=MalformedTickFieldError`.
- **The generic MDPS candle-adapter registry dispatch path** (`CandleAdapterRegistry` → `orchestration_service.py`'s
  `LiveOrchestrationMixin._process_instrument_file` → `live_workers_chain.py`, entry point
  `cli/handlers/process_handler.py --operation process --mode batch`) calls
  `SportsBucketAssignmentAdapter.process_to_candles()` directly, which **does** raise `MalformedTickFieldError`.
  `live_workers_chain.py` (~line 429) catches `(UpstreamTimestampBiasError, MalformedTickFieldError)` together and
  writes `record_failed_for_shard(error=type(e).__name__, ...)` — i.e. the manifest `error_reason` is literally just the
  class name `"MalformedTickFieldError"` (by design — `record_failed_for_shard`'s docstring: "pass the classified error
  string ... NOT the raw exception message"). **The full detail (`field=...`, `n_dropped=...`, `sample_values=...`) is
  never persisted to the manifest — only to application/Cloud Logging** — so there is no fuller manifest-stored text to
  retrieve beyond the class name; this matches what the plan doc already reported.

  The general MDPS batch Cloud Run Job that would drive this path on a schedule
  (`uts-prod-market-data-processing-service-t1-recon`, `0 1 * * *` per `t1_batch_scheduler.tf`) **did not exist** until
  a 2026-07-14 fix (documented separately in the `sports_data_sources_canonical_completion_2026_07_13` audit —
  `gcloud run jobs describe` returned NOT_FOUND for ≥3 days beforehand). Neither this job's 01:00 UTC schedule nor the
  dedicated odds-horizon reprocessor's 01:15 UTC schedule matches the incident's `23:56Z` timestamp. Most plausible
  explanation: a manual/ad-hoc CLI invocation (`--operation process --mode batch --asset-group SPORTS`) during the
  same-day audit — consistent with a one-off event that would not recur on its own even without a code fix, which is
  itself part of why the live count has already returned to 0.

### Root cause — genuine code bug, not (only) upstream data

`_prepare_tick_data()` (`market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py`) pivots raw
MTDS long-format odds to wide-format, validates `bm_minutes_to_kickoff` + the h2h wide columns are present, then
enforces `bm_time <= fetch_utc` (causality) and drops any row that fails it. Before this fix, the function returned a
bare (possibly-empty) DataFrame with no signal for WHY it was empty. `process_to_candles()` treated every empty result
identically:

```python
df = self._prepare_tick_data(tick_data)
if df.empty:
    raise MalformedTickFieldError(
        field="bm_minutes_to_kickoff_or_h2h_columns", ...
    )
```

This conflated two structurally different conditions under one label:

1. **Genuinely malformed data** — `bm_minutes_to_kickoff` missing entirely, or the h2h pivot failed to produce the
   required wide columns. A real schema-drift signal, correctly worth raising loud.
2. **100%-causality-filtered rows** — `bm_minutes_to_kickoff` and the h2h columns are both genuinely present (the tick
   frame is well-formed), but every row's `bm_time` postdates `fetch_utc`. `bm_time` is the ODDS_API vendor's own
   reported last-update timestamp (confirmed in `market-tick-data-service`'s odds adapter — documented explicitly as
   "ground truth, not fetch_time", not locally derived from `fetch_utc`), so vendor clock-skew or a late-arriving stale
   snapshot CAN genuinely produce `bm_time > fetch_utc` for real bookmaker data — this is not necessarily a local bug.
   But treating a 100%-causality-drop as a "malformed field" mislabels an honest-absence outcome as a schema defect —
   exactly the same class of false-failure the adapter's own **existing** "Path A½" fix (2026-05-28, `bb7c829`) already
   corrected two code blocks above, for bookmakers publishing only spreads/totals (no h2h markets). That precedent fix's
   own comment states the rationale verbatim: "This is genuine data absence, not a schema error — record as
   empty_confirmed rather than raising MalformedTickFieldError (which wrongly marks the shard attempted_failed and
   floods the manifest with false failures)." The causality-drop case is the same shape and was simply never covered by
   that fix.

`git log` on `bucket_assignment_adapter.py` shows no commits near 2026-07-13 — this is a **standing** bug (present since
at least 2026-06-01), not a transient regression that "fixed itself"; the zero-current-failures state is explained by
the incident being a one-off manual-run artifact hitting stale/late bookmaker data for that specific run, not by the
underlying code having changed.

## Correlation with the sibling sports/trades VENUE_FETCH_FAILED investigation

Per the dispatch brief, another concurrent session was investigating `sports/trades` `VENUE_FETCH_FAILED` (112277/522276
attempted_failed) from the SAME `attempted_at≈2026-07-13T23:56Z` batch window. Checked `plans/active/issues/` for that
investigation's output at the time of this writing — **no issue doc has been filed for it yet** (that investigation
appears still in flight), so a direct cross-reference to its findings isn't possible yet. Based on this investigation's
own evidence, however, these are **NOT the same root cause**:

- Different services: `sports/trades` `VENUE_FETCH_FAILED` is an MTDS-level raw-fetch failure (raw odds-api/bookmaker
  ingestion); `sports/odds_horizon_bucket` `MalformedTickFieldError` is an MDPS-level derived-aggregation classification
  bug (a downstream consumer of MTDS's already-fetched raw ticks).
- Different manifest buckets: `trades` writes to the MTDS tick manifest directly; `odds_horizon_bucket` writes to the
  canonical `instruments-store-sports-*` manifest (per the 2026-06-07 canonicalisation) or, via the live-path,
  `market-data-tick-sports-*`.
- Different code paths and different failure shapes (a network/API fetch failure vs. a local classification decision on
  already-successfully-fetched data).

The shared `attempted_at` timestamp is most consistent with both cells being swept up in the same ad-hoc/manual batch
run or the same nightly window, rather than one shared upstream outage causing both. Noting the overlap here for the
next investigator rather than asserting a shared cause that the evidence doesn't support.

## Fix shipped

`market-data-processing-service@7ff43d7197a50cfe52d9ad8fe514cd6a2ca09558`:

- `_prepare_tick_data()` now returns `tuple[pd.DataFrame, bool]` — `(df, causality_filtered_to_empty)`. The second
  element is `True` only when `bm_minutes_to_kickoff` and the h2h columns both validated successfully AND the causality
  filter dropped every remaining row (i.e. `df` was non-empty going into the filter and empty coming out).
- `process_to_candles()` now branches on that flag: `causality_filtered_to_empty=True` → logs and returns
  `_make_empty_candle_output()` (records `empty_confirmed`, honest absence), mirroring the existing Path A½ precedent.
  Any other empty-result cause still raises `MalformedTickFieldError` exactly as before — genuine schema drift is not
  papered over.
- `process_to_bucketed_df()`'s call site updated for the new return signature (behavior unchanged there — it already
  treated any empty result the same way regardless of cause).

**Regression tests** (`tests/unit/test_bucket_assignment_adapter.py`, new `TestCausalityFilterHonestAbsence` class):

1. `test_all_rows_future_bm_time_returns_empty_not_malformed` — a well-formed h2h tick frame with `bm_time` strictly
   after `fetch_utc` for every row → asserts `process_to_candles()` does NOT raise, returns a true-empty (0-row)
   `CandleOutput`.
2. `test_partial_causality_drop_still_processes_remaining_rows` — a mix of causally-valid and causally-invalid rows →
   asserts the valid row still produces output (the fix doesn't over-broadly suppress legitimate data).
3. `test_missing_bm_minutes_to_kickoff_still_raises_malformed` — control test: genuine schema drift (no causality
   involved) still raises `MalformedTickFieldError` — confirms the fix is scoped correctly and doesn't over-correct.

Verified via `coverage.xml` (not just "tests pass") that both the new `if causality_filtered_to_empty:` branch and the
still-raising `else` branch were actually exercised (lines hit, not just present). Full `quality-gates.sh --no-fix`
green (basedpyright clean on the touched file; 0 new violations).

## Follow-ups (not blocking, none required to close this issue)

- No historical manifest cleanup needed — live re-query confirmed zero current `MalformedTickFieldError` rows for this
  data_type in either candidate manifest bucket, so there is nothing stale to reclassify.
- If the sibling `sports/trades` `VENUE_FETCH_FAILED` investigation files its own issue doc and finds a genuinely shared
  upstream cause with this one, cross-link the two docs at that point — not asserted here without evidence.

## REOPENED — the "0 rows" claim above does not hold on a fresh re-query (2026-07-15 ~15:30Z)

Adversarial verification (dispatched by the operator explicitly asking to "check" a later close-out that cited this doc
as "fully resolved, count=0") re-queried the live manifest and found the count is **66**, not 0 — timestamps unchanged
from the original pre-fix figure (max `attempted_at` 2026-07-13T23:56:48Z, the same batch this doc's own original
investigation examined). This directly contradicts BOTH this doc's own "Live re-query... found ZERO current
attempted_failed rows" claim (in the frontmatter summary, from the ORIGINAL investigation) AND the later close-out's
repetition of that claim.

**Not yet determined which side is wrong, or why** — possibilities, none confirmed: (a) the original investigation's
"both plausible sports manifests" check missed the actual bucket/path these 66 rows live in; (b) the two checks used
different predicates (e.g. one filtered by `error_reason` starting with `Malformed` specifically, the other used a
broader `data_type=odds_horizon_bucket_15m AND capture_status=attempted_failed` match that would also catch rows with a
DIFFERENT error_reason that happen to share the data_type); (c) something regenerated/rewrote these 66 rows between the
original check and the later one. The code fix (`market-data-processing-service@7ff43d7`) may well be correct for its
own narrow claim (new causality-filtered ticks no longer misclassify going forward) — that part was not disputed — but
it clearly did not make the specific 66 rows the alert keys on disappear, contrary to what both this doc and the
downstream close-out asserted.

**Needs for whoever picks this up**: re-run the EXACT live-manifest query this doc's original investigation used (check
the "Investigation" section above for the precise buckets/paths/predicate), and separately re-run whatever broader
predicate finds the 66 rows, to identify exactly where the discrepancy comes from before concluding anything further. Do
not re-mark this `resolved` without reconciling the two numbers with a real query, not another inference.

Status reverted `resolved` → `open`.
