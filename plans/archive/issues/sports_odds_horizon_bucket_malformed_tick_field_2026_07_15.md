---
doc_type: issue
title:
  sports/odds_horizon_bucket_15m MalformedTickFieldError — 100%-causality-filtered odds ticks were misclassified as a
  malformed field instead of honest absence
summary:
  "DP_RUN_MOSTLY_EMPTY alert for sports/odds_horizon_bucket_15m (66/66 attempted_failed,
  error_reason=MalformedTickFieldError, max attempted_at 2026-07-13T23:56:48Z). RECONCILED 2026-07-15 (see 'RECONCILED'
  section): the original investigation's AND the close-out's 'live re-query found ZERO attempted_failed rows' claim was
  WRONG — a WRONG-PREDICATE artifact (reconciliation verdict = (b), different predicate). The original query filtered
  data_type=='odds_horizon_bucket' (base name, NO _15m suffix), which genuinely has 0 attempted_failed; the alert + the
  66 rows live under data_type=='odds_horizon_bucket_15m' in market-data-tick-sports-prd (the canonical
  instruments-store-sports manifest carries NO timeframe-suffixed variant at all, so it could never have found them
  either way). The 66 rows are real and still live. The same bug spans all 4 timeframe variants: _15m=66, _1h=63,
  _4h=89, _1d=87 (305 rows). Provenance: 36 rows are genuine pre-fix MDPS process_to_candles() MalformedTickFieldError
  classifications (written 2026-05-24, service_name=mdps, league_id=''); 30 are rebuild_sports_manifest_v9.py E4 RE-EMIT
  duplicates (written 2026-07-13T23:56:41-48Z, service_name=mtds) — the exact same bulk-re-emit the sibling
  sports/trades finding identified (the rebuild stamps its own runtime as attempted_at, making the rows look freshest in
  the alert batch; fixed forward-only in market-tick-data-service@6fad6565). The code fix
  market-data-processing-service@7ff43d7 (empty_confirmed for the 100%-causality-drop case; genuine schema drift still
  raises) is correct + on LDR but FORWARD-ONLY — it did not touch the 66 existing rows. Historical-row cleanup DEFERRED
  as a tracked follow-up because a naive fix would revert: 36 of the rows sit permanently in
  _index/per_vm/_legacy_seed.parquet as attempted_failed, so a DELETE would RESURRECT on the next consolidator cycle
  (the identical vector that reverted the cefi orphan delete in this same remediation); a durable fix must re-process
  the 17 shards with 7ff43d7 deployed and verify the reclass holds across >=2 consolidator cycles, not a blind manifest
  edit. status stays open; resolved_by cleared."
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, odds, mdps, data-correctness, honest-absence, malformed-tick-field, dp-run-mostly-empty]
related:
  [
    plans/active/data_pipeline_alerts_batch_remediation_2026_07_15.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-15
last_updated:
  2026-07-15 (CLEANED UP — 305 rows reclassified to empty_confirmed; classification proven honest-absence; HELD across 2
  --force full rebuilds + 5 natural cron cycles; status -> resolved)
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: [operator-dispatched sub-agent, data_pipeline_alerts_batch_remediation_2026_07_15.md "New todos" section]
resolved_by: |
  market-data-processing-service@7ff43d7 (forward fix — prevents recurrence) + market-tick-data-service@545ce50b
  (reclass_sports_odds_horizon_malformed_tick_field_2026_07_15.py --apply: 305 attempted_failed/MalformedTickFieldError
  -> empty_confirmed/SOURCE_RETURNED_ZERO in the live market-data-tick-sports canonical; classification proven
  honest-absence via the fixed adapter on real raw ticks; HELD across 2 --force full rebuilds + 5 natural cron cycles;
  legacy seed excluded by unified-trading-library@8e783d70 Part 2). See "CLEANED UP (2026-07-15)" section for the full
  evidence chain.
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

## Follow-ups

- ~~No historical manifest cleanup needed — live re-query confirmed zero current `MalformedTickFieldError` rows~~
  **RETRACTED 2026-07-15 — this bullet was the WRONG-PREDICATE error.** Historical manifest cleanup IS needed: 66
  (`_15m`) — really 305 across all 4 timeframe variants — `MalformedTickFieldError` `attempted_failed` rows are live
  under `data_type=='odds_horizon_bucket_15m/_1h/_4h/_1d'` in `market-data-tick-sports`. See the "RECONCILED" section
  for the disposition (deferred, resurrection-gated) and the safe cleanup recipe. Tracked in
  `data_pipeline_alerts_batch_remediation_2026_07_15.md`.
- The sibling `sports/trades` investigation DID file its doc:
  `plans/active/issues/sports_trades_venue_fetch_failed_2026_07_15.md`. Cross-linked: the 30-row 2026-07-13T23:56:41-48Z
  cohort here is the SAME `rebuild_sports_manifest_v9.py` E4 re-emit (`attempted_at` re-stamp) that doc identified —
  same 8-second window, same fingerprint, different `data_type`. Both the `sports/trades` rows and these
  `odds_horizon_bucket_*` rows were swept up in the one v9 rebuild pass. The MTDS forward-fix
  `market-tick-data-service@6fad6565` covers the re-stamp for future rebuilds; the historical rows in both docs remain a
  deferred cleanup.

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

## RECONCILED (2026-07-15) — the discrepancy is a WRONG-PREDICATE query; the 66 rows are real (verdict (b))

Re-queried both manifests live with the venv pandas reader (parquets downloaded fresh from GCS this session). The two
numbers differ because the ORIGINAL investigation dropped the `_15m` suffix and queried the BASE `odds_horizon_bucket`
data_type, which genuinely has 0 `attempted_failed`. The alert (and the 66 rows) key on `odds_horizon_bucket_15m` — a
**distinct data_type string**, present ONLY in the `market-data-tick-sports` bucket.

### The two query outputs, side by side (same live parquets, same session)

**A — ORIGINAL predicate** `data_type == "odds_horizon_bucket"` (base, NO `_15m`) — reproduces the doc's original
numbers:

```
market-data-tick-sports-prd  data_type=="odds_horizon_bucket": 124,294 rows
    capture_status = {captured: 123642, empty_confirmed: 652}   attempted_failed = 0
instruments-store-sports-prd data_type=="odds_horizon_bucket": 350,713 rows
    capture_status = {expected_unattempted: 199720, captured: 143594, empty_confirmed: 7395, attempted_failed: 4}
    the 4 attempted_failed = RAW_ODDS_SHAPE_UNRECOGNIZED   (Malformed* = 0)
```

**B — ALERT predicate** `data_type == "odds_horizon_bucket_15m"` (WITH `_15m`) — finds the 66:

```
market-data-tick-sports-prd  data_type=="odds_horizon_bucket_15m": 357 rows
    capture_status = {empty_confirmed: 291, attempted_failed: 66}
    all 66 attempted_failed error_reason = MalformedTickFieldError   (max attempted_at 2026-07-13T23:56:48.467702Z)
instruments-store-sports-prd data_type=="odds_horizon_bucket_15m": 0 rows   (this data_type does NOT exist there)
```

### Reconciliation verdict: **(b) — different predicate (different `data_type` string)**

Not (a) wrong bucket and not (c) rows-rewritten-between-checks. Proof:

- The original query's EXACT numbers (124,294 / {captured 123642, empty_confirmed 652, attempted_failed 0} for the tick
  bucket; 350,713 / {…, attempted_failed 4 = RAW_ODDS_SHAPE_UNRECOGNIZED} for the store bucket) **still reproduce
  byte-for-byte today** under `data_type == "odds_horizon_bucket"`. So the original numbers were correct FOR THE
  PREDICATE THEY USED — they were just answering a different question (the base data_type, not the `_15m` variant).
- The 66 rows have been static since 2026-07-13 (max `attempted_at` 2026-07-13T23:56:48Z, unchanged from the pre-fix
  figure) — they did NOT appear between checks. They were always there, under `odds_horizon_bucket_15m`, which neither
  the original "both plausible sports manifests" pass nor the close-out ever queried.
- The canonical `instruments-store-sports` manifest has NO timeframe-suffixed variant at all (only base
  `odds_horizon_bucket`) — so the original investigation's "check the canonical manifest" leg could never have found
  these rows regardless of the suffix. The timeframe-bucketed variants live ONLY in `market-data-tick-sports`.

**Same bug spans all 4 timeframe variants** (all 100% `MalformedTickFieldError`), not just `_15m`:
`odds_horizon_bucket_15m=66, _1h=63, _4h=89, _1d=87` → **305 rows total**. The base `odds_horizon_bucket`=0.

### Row provenance: 36 genuine pre-fix + 30 rebuild re-emit (NOT re-seeded by any scheduled writer)

The 66 rows are two `written_at`/`attempted_at` cohorts, both hitting the same 17 `(date, venue=FOOTBALL)` atoms (shard
dates span 2025-08-05 … 2025-12-31; `source=api_football`, `pipeline_mode=batch_api_football`):

| cohort (written_at)     | rows | service_name                   | league_id | timeframe | transport | what it is                                                                                                                                                                                                                                                                                        |
| ----------------------- | ---- | ------------------------------ | --------- | --------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-24 22:17–23:58Z | 36   | market-data-processing-service | `''`      | `15m`     | (null)    | **genuine pre-fix** MDPS `process_to_candles()` MalformedTickFieldError classifications — the exact rows `7ff43d7` fixes going forward                                                                                                                                                            |
| 2026-07-13 23:56:41–48Z | 30   | market-tick-data-service       | `None`    | (null)    | `rest`    | **`rebuild_sports_manifest_v9.py` E4 RE-EMIT** duplicates — same 8-second window / blank-fixture_id / batch_api_football fingerprint the sibling `sports_trades_venue_fetch_failed_2026_07_15.md` proved is the v9 rebuild re-emitting pre-existing rows with `attempted_at` defaulted to `now()` |

The 30-row 07-13 cohort is the SAME artifact class as the sibling sports/trades finding — the rebuild's `attempted_at`
re-stamp bug (fixed forward-only in `market-tick-data-service@6fad6565`) is why these year-old rows carry a
2026-07-13T23:56Z timestamp and looked like the freshest failure in the alert batch. Neither cohort is produced by any
current scheduled writer (no writes to this data_type since 2026-07-13; the historical 2025 shard-dates are not in any
recon window) — i.e. the rows are **static, not actively re-seeded**. The original doc's "one-off manual run that
drifted to 0" theory was directionally right about "one-off" but wrong about "drifted to 0": the rows never went away.

### Disposition: `7ff43d7` is correct + forward-only; historical-row cleanup DEFERRED (a naive fix REVERTS)

- **The code fix stands.** `market-data-processing-service@7ff43d7` is an ancestor of `origin/live-defi-rollout` (not
  yet on `main`), is correct for its narrow claim (100%-causality-drop → `empty_confirmed`; genuine schema drift still
  raises `MalformedTickFieldError`), and prevents NEW misclassifications. It is **forward-only** and does not, and was
  never claimed by its own diff to, retroactively clean the 66 pre-existing rows. The doc's error was the RECONCILIATION
  ("0 rows"), not the fix.
- **A DELETE of these rows would RESURRECT** — verified, not inferred. `market-data-tick-sports`'s per-VM shard dir
  contains `_index/per_vm/_legacy_seed.parquet` (a permanent, never-pruned one-time canonical snapshot fed into EVERY
  consolidator merge). It currently holds **36 `attempted_failed` / `MalformedTickFieldError` rows** for
  `odds_horizon_bucket_15m` (the exact 05-24 cohort, `attempted_at` 2026-05-24T22:17:59…23:58:05Z). The consolidator's
  merge (`manifest_consolidator.py`) dedups on
  `(date, venue, data_type, service_name, +present optional dims: timeframe, league_id, …)` and, for an all-non-captured
  group, falls through to `attempted_at DESC, written_at DESC` (recency). The 2026-07-15 legacy-seed fix
  (`unified-trading-library@f14b13ae`/`8e783d70`) only demotes **captured** seed rows out of the captured-outranking
  tie-break — it does NOT exclude a non-captured seed row from re-supplying a DELETED atom. So a delete leaves the
  seed's `attempted_failed` row as the sole survivor in its partition on the next full-rebuild cycle → the rows come
  back. **This is the identical vector that reverted the cefi orphan delete in this same remediation**
  (`legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md`).
- **A RECLASSIFY (attempted_failed → empty_confirmed) COULD hold** (the canonical row, re-stamped with a newer
  `written_at`, would out-recency the frozen seed row in the same partition) — **but two things block doing it now,
  safely, this session**: (1) **correctness** — I cannot PROVE from the manifest alone that all 66 are the
  causality-drop honest-absence case vs. genuine schema drift; the doc inferred it but did not check the raw MTDS ticks
  for these specific 17 shards. Blind-stamping `empty_confirmed` without that proof would risk papering over a genuine
  failure with a wrong status — the exact mislabel class this whole issue is about, inverted. The correct tool is to
  **re-process the 17 shards with `7ff43d7` deployed** and let the writer decide the status. (2) **durability** — even a
  correct reclass is a live-bucket mutation that needs the same dry-run + snapshot + `--apply` + multi-cycle
  before/after verification the cefi/tradfi reclasses used, and must be confirmed to hold across ≥2 consolidator cycles
  given the legacy-seed vector (the cefi delete passed one cycle then reverted on a later one). This is a
  controlled-window production-data pass, not an inline edit — matching how EVERY sibling historical-row cleanup in this
  remediation wave was scoped (sports/trades `attempted_at` restore, tradfi mbp_10, corp-actions all deferred their
  historical-row cleanup for the same reasons).

**Net**: the reconciliation is resolved (verdict (b), evidence above); the code fix is real and correct; the 66 (really
305 across all 4 timeframes) rows are stale pre-fix rows whose cleanup is deferred to a tracked follow-up with a precise
recipe, because doing it now via the obvious path (delete) would revert and via the alternative (blind reclass) would be
unproven-correct. `status` stays `open`; `resolved_by` cleared. Follow-up todo added to
`data_pipeline_alerts_batch_remediation_2026_07_15.md`.

### Safe cleanup recipe (for the deferred follow-up)

1. Confirm `7ff43d7` is deployed to whatever job re-processes sports odds (the
   `uts-prod-market-data-processing-service-t1-recon` Cloud Run job image, or a targeted
   `--operation process --mode batch --asset-group SPORTS` run pinned to the 17 dates). Verify the raw MTDS odds ticks
   for those 2025 dates still exist first.
2. Re-process the 17 `(date, FOOTBALL)` shards for all 4 timeframe variants (`_15m/_1h/_4h/_1d`) so the WRITER records
   the correct status (`empty_confirmed` for causality-drop, `captured` if data now processes) — do NOT hand-edit the
   manifest.
3. Trigger a consolidator cycle; re-query the live index; confirm the 305 `MalformedTickFieldError` `attempted_failed`
   rows are gone. Then wait for ≥1 MORE consolidator cycle and re-query AGAIN to confirm they do NOT resurrect from
   `_legacy_seed.parquet` (the cefi failure mode). Only then flip this issue to `resolved`.
4. If re-processing is infeasible (raw ticks aged out) and a manifest reclass is the only option, it MUST be dry-run +
   snapshot + `--apply` with before/after counts, target ONLY `data_type LIKE 'odds_horizon_bucket_%'`
   `AND capture_status='attempted_failed' AND error_reason='MalformedTickFieldError' AND venue='FOOTBALL'`, bump
   `written_at` to now so the canonical row out-recencies the seed, and be verified to hold across ≥2 cycles.

## ✅ CLEANED UP (2026-07-15) — 305 rows reclassified to empty_confirmed; HELD across a real `--force` full rebuild + natural cycles

The deferred historical-row cleanup is DONE. The 305 `MalformedTickFieldError` `attempted_failed` rows
(`_15m=66, _1h=63, _4h=89, _1d=87`, all `venue=FOOTBALL`, 22 shard-dates 2025-07-31 … 2025-12-31) are now
`empty_confirmed` / `error_reason=SOURCE_RETURNED_ZERO` in the live `market-data-tick-sports` canonical, joining the
1,032 already-correct suffixed empty_confirmed siblings (→ 1,337 total). `status` → `resolved`.

### Classification PROVEN honest-absence (not schema drift) — re-derived from raw ticks with the fixed adapter

The reclass was NOT a blind status flip. For a 66-instrument sample spanning **all 22 shard-dates and all 10
bookmakers** (betmgm/betway/bovada/coral/fanduel/paddypower/pinnacle/skybet/unibet_uk/williamhill), the FIXED MDPS
adapter (`market-data-processing-service@7ff43d7`, run against the actual raw ODDS_API ticks that produced these rows)
returned **EMPTY (honest absence) 66/66 at every grain** (single-instrument, fixture, whole-file) — 0 raised
`MalformedTickFieldError`, 0 produced candles. Every raw tick is well-formed (`bm_minutes_to_kickoff` present, h2h
`market_key`/`price` present) but the odds sit far outside the T-24h..T-0 horizon staleness window (early pre-match
snapshots, `bm_minutes_to_kickoff` thousands of minutes before kickoff), so there is genuinely no horizon-bucket output.
A `MalformedTickFieldError` manifest row is only ever written on Path C (missing `bm_minutes_to_kickoff` / failed h2h
pivot); none of these atoms hit Path C under the fixed code. `empty_confirmed[SOURCE_RETURNED_ZERO]` is exactly what the
fixed writer (`record_empty_for_shard`) would record on re-process, so the reclass == re-processing outcome without
running the heavier general candle path over 22 historical dates.

### The legacy-seed resurrection vector is CLOSED by deployed code (Part 2) — the odds-doc's earlier premise was stale

The earlier disposition assumed `unified-trading-library@f14b13ae`/`8e783d70` only demote **captured** seed rows, so a
canonical fix would resurrect from the 164 attempted_failed seed rows. Reading the actual Part-2 code (`8e783d70`)
disproves this: Part 2 excludes `_index/per_vm/_legacy_seed.parquet` **ENTIRELY** from the full-rebuild/canonical merge
whenever a canonical exists (`merge_paths` filter + `exclude_legacy_seed` in `_read_and_merge_per_vm_shards` /
`merge_canonical_with_outstanding_shards` / `rebuild_manifest_from_canonical_paths`) — regardless of `capture_status`.
It is deployed on the sports consolidator (`market-tick-data-service:latest`, verified live below). The routine
per-minute cron runs the incremental path, which structurally never includes the frozen-mtime seed. So the seed rows are
inert; **no code gap remains** and no UTL change was needed.

The seed file was deliberately **NOT** rewritten: any write bumps its frozen mtime, which would re-introduce all ~1.76M
seed rows into the incremental merge (which does NOT apply Part-2's exclusion) — strictly riskier than leaving the inert
seed alone. Belt-and-suspenders instead: the reclass bumps `written_at` to now on the 305 canonical rows, so even in the
hypothetical event Part 2 were reverted, the corrected rows out-recency the seed's 2026-05-24 rows in the consolidator's
`attempted_at DESC, written_at DESC` non-captured tie-break.

### Method + HOLD-across-a-cycle evidence

- **Tool**: `market-tick-data-service/scripts/reclass_sports_odds_horizon_malformed_tick_field_2026_07_15.py --apply`
  (raw canonical read + generation → verified pre-flip snapshot → invariant guards {captured unchanged, attempted_failed
  −305, row_count unchanged} → atomic CAS `conditional_upload_bytes(if_generation_match=...)`). CAS correctly REFUSED
  the first attempt when the per-minute cron bumped the generation mid-snapshot; the sports consolidator cron
  (`uts-prod-manifest-consolidator-market-data-sports-cron`) was paused for a clean CAS window and resumed immediately
  after (22:35→22:41Z).
- **Apply**: matched exactly 305 (66/87/63/89), CAS write generation `1784154944569578 → 1784155070991313`,
  attempted_failed `112582 → 112277`, captured `575671` unchanged. Snapshot:
  `_index/snapshots/pre_odds_horizon_malformed_reclass_20260715-223708.parquet`.
- **Immediate re-read**: 0 attempted_failed/MalformedTickFieldError `odds_horizon_bucket_*`; 1,337 suffixed
  `empty_confirmed[SOURCE_RETURNED_ZERO]`.
- **HELD across a REAL `--force` full rebuild** (exec `uts-prod-manifest-consolidator-market-data-sports-wqsgs`,
  `phase=duckdb_merge_start mode=full`, `legacy_seed_in_cycle=False`, `shards_downloaded shards=0` of
  `shards_listed shards=1` — the seed was listed but EXCLUDED by Part 2; `rows_in=1958499 rows_out=1958498`): post-force
  re-read = **0** resurrected, 1,337 empty_confirmed preserved. This is the exact vector (`--force` full rebuild that
  re-includes the seed) that reverted the sibling cefi delete pre-Part-2 — it held.
- **HELD across 5 natural incremental cron cycles** (22:43–22:47Z, cron resumed): re-read = 0 resurrected, 1,337
  preserved.
- **HELD across a SECOND deliberate `--force`** (exec `...-lvrbd`, `mode=full`, `legacy_seed_in_cycle=False`,
  `shards_downloaded shards=0` of `shards_listed shards=1`, `rows_in=rows_out=1958498`): re-read = 0 resurrected, 1,337
  preserved. Multi-cycle proof: apply→0, force#1→0, 5 incremental→0, force#2→0. Matches the cefi
  "one-cycle-isn't-enough" discipline — the seed vector was exercised twice and both times excluded by Part 2.
  Consolidator cron re-enabled after verification.

Tool committed at `market-tick-data-service@545ce50b` (QG-green, quickmerge). Snapshot restore point:
`_index/snapshots/pre_odds_horizon_malformed_reclass_20260715-223708.parquet`. No `unified-trading-library` change was
needed — Part 2 (`8e783d70`) already closes the legacy-seed resurrection gap for attempted_failed rows (the earlier
"code gap" framing was based on Part 1 alone).
