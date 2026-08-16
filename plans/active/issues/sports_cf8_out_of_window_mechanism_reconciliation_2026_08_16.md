---
doc_type: issue
title:
  "CF-8 out-of-window (14,982-row) blank-timeframe `odds_horizon_bucket` population — TWO DIFFERENT root causes
  identified (2026-08-16): 2026-07-13 cluster (14,656 rows) is `_write_captured_rows()`'s pre-fix rebuild being
  timeframe-blind by construction; 2026-05-05 cluster (326 rows) is NOT MTDS — plausibly MDPS's
  `reprocess_sports_odds.py` coarse-summary-row design, possibly not a bug at all"
summary: >-
  Split from `sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md` (at its 999-line hard cap) to continue the
  root-cause chase for the 14,982-row out-of-window blank-`timeframe` `odds_horizon_bucket` population. A dispatched
  Explore agent traced the live-WS-shard path end-to-end and ruled it out with high confidence (ODDS_API's connector is
  BLOCKED-CREDENTIALS — zero ticks structurally possible — and has no `data_type` gating regardless). It also proposed
  `_write_captured_rows()` (fixed at `market-tick-data-service@e0b34e77fd`, 2026-08-15) as the mechanism, matching the
  row-count/service_name/date-cluster signature. But the parent doc's own already-recorded correction pass explicitly
  falsified this exact hypothesis via a 0/200 sibling check. A tighter, ordering-aware scoped check (2026-08-16)
  RE-FALSIFIES it for the population as a whole — but a git-blame follow-up found the 14,982 rows are actually TWO
  unrelated populations with two different causes; see the Result sections below.
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, cf-8, available-at, sports, manifest-writer, timeframe, regression]
related:
  [
    /plans/active/issues/sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md,
  ]
created: 2026-08-16
author: data_engineering (slot-2)
priority: P1
source: "sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md, split at its 999-line hard cap, 2026-08-16"
parent_epic: infrastructure_master
assigned_vm: NA
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_write.py,
    market-tick-data-service/live/connectors/odds_api_ws.py,
    market-tick-data-service/market_tick_data_service/live/manifest_recorder.py,
    market-data-processing-service/scripts/reprocess_sports_odds.py,
  ]
---

# CF-8 out-of-window population — mechanism reconciliation

## Ruled out: live-WS-shard hypothesis (HIGH confidence, no contradicting evidence)

Dispatched Explore agent traced the full chain:

- WS streaming CLI handler actually lives at
  `market_tick_data_service/cli/handlers/websocket_streaming_handler.py` — **the parent doc's own prior citation of
  `market_tick_data_service/live/websocket_streaming_handler.py` is stale/wrong, that path doesn't exist in this
  checkout.** Correcting it here per the "a stale pointer is a finding, fix it" rule.
- `data_type` is set manually per-shard via `--shard-spec asset_group:venue:data_type`
  (`parse_shard_spec()`, handler.py:88-99) — no auto-iteration, no validation against a real-timeframe registry.
- `odds_api_ws.py` (425 lines): `data_type` is stored at `__init__` (line 232) and **never read again anywhere in the
  file**. Critically, `stream()` (line 345) is gated `BLOCKED-CREDENTIALS` — with no API key it logs and `return`s
  immediately (lines 354-360), yielding **zero ticks**. The venue is registered with an explicit
  `# Sports: ODDS_API (BLOCKED-CREDENTIALS)` comment (`connectors/__init__.py:73`).
- `MTDSShardManifestRecorder.record_captured()` (`manifest_recorder.py:136-185`) genuinely has no `timeframe` param —
  confirmed, matches the parent doc's own finding — but this path can only fire from real ticks, and none flow.
- The single-minute write_at clustering (`2026-07-13T23:5x`, `2026-05-05T22:07`) also contradicts the WS runner's
  continuous ~60s-poll shape, which is a second, independent line of evidence against this hypothesis.

**Verdict: this branch is closed.** No further live-WS-path investigation needed for this population.

## Reopened, NOT resolved: `_write_captured_rows()` vs. the parent doc's own falsification

The parent doc's Evidence table (lines ~120-128) already proves the general mechanism for THIS SESSION's own in-window
bug: 6 original rows (`T-6h`/`T-4h`/`T-10m`/`T-2h`/`T-12h`/`T-24h`, all `written_at=2026-05-05T22:07:40.697xxx`, real
timeframes) plus one new blank-`timeframe` row (`written_at=2026-08-15T11:39:52`, "mine") — additive, non-superseding,
sibling with the real timeframe still present. That confirms the MECHANISM is real and additive.

The question is whether the SAME mechanism, from two EARLIER, pre-fix invocations, explains the out-of-window
population's two clusters (14,656 rows @ `2026-07-13T23:5x` + 326 rows @ `2026-05-05T22:07`, both
`service_name=market-tick-data-service`, non-blank `league_id`, `capture_status=captured`). The agent's case for this:
`_write_captured_rows()` is called by `rebuild_sports_manifest_v9.py` and by
`sports_captured_available_at_targeted_backfill_2026_07_14.py`, both of which are named in
`sports_cf8_available_at_backfill_regression_2026_07_13.md` — a backfill regression dated **2026-07-13**, matching the
larger cluster exactly. Row-count order of magnitude also matches (`delete_cf8_phantom_timeframe_sibling_confirmed_
2026_08_15.py` documents a 14,330-row population from this exact bug class).

Directly against this: the parent doc's own reopened-P1 entry states a **0/200 sampled sibling check on this exact
14,982-row population found ZERO rows with a non-blank-timeframe sibling** under the coarse
`(date,venue,league_id,data_type,service_name)` key — and reasons that if `_write_captured_rows()`'s bug is additive
(proven above), a real sibling should ALWAYS exist, so its absence falsifies the mechanism for this population.

**Why this isn't yet a real contradiction — it's an unchecked assumption on the falsification side**: the sibling-check
reasoning assumes the `captured_df` input to the 2026-07-13/2026-05-05 invocations of `_write_captured_rows()` itself
carried a REAL per-timeframe value to omit. But `_write_captured_rows()` re-emits from `captured_df` — if, on those
specific earlier runs, the source `captured_df` was ITSELF sourced from something that lacked timeframe granularity for
`odds_horizon_bucket` at that time (e.g., an earlier-schema index, or a differently-shaped intermediate table), then
there never was a "real-timeframe original" for those specific rows to leave a sibling of — same bug class, same
function, different (older) invocation context, no sibling expected. This is a plausible reconciliation, **NOT
confirmed** — it has not been checked against the actual `captured_df` construction path used by
`rebuild_sports_manifest_v9.py`/the 2026-07-14 targeted-backfill script as of those two specific dates (git history of
`_rebuild_sports_write.py` / its callers around 2026-05-05 and 2026-07-13, not yet read).

## Precise next step

A sibling check SCOPED exactly to the two clusters (not a random sample of the full 14,982), with an explicit
older-`written_at` ordering constraint:

1. Query rows with `written_at` in `[2026-07-13T23:50, 2026-07-13T23:59]` and separately
   `[2026-05-05T22:07:00, 2026-05-05T22:07:59]`, `data_type=odds_horizon_bucket`, blank `timeframe`,
   `service_name=market-tick-data-service`.
2. For each, look up `(date, venue, league_id, data_type, service_name)` for ANY sibling row with a **non-blank**
   `timeframe` AND a **strictly OLDER** `written_at` (a "real original this run was supposed to re-emit, not
   supersede" — the ordering constraint the general 0/200 check may not have applied).
3. If siblings are found this way but weren't caught by the general check (e.g. because the general check's 200-row
   sample under-drew from the smaller 326-row cluster, or didn't apply the ordering constraint) — `_write_captured_
   rows()` is CONFIRMED for this population, and the earlier "CORRECTION...FALSIFIED" entry in the parent doc needs its
   own follow-up correction.
4. If genuinely zero siblings exist even under this tighter scoping — the mechanism really is something else, and the
   `captured_df`-construction-history angle (git-blame `_rebuild_sports_write.py`'s callers around those two dates)
   becomes the next lead.

Not yet run this pass (batching/turn budget) — filed as the next actionable todo, not executed speculatively.

## Result (2026-08-16): scoped check REINFORCES the falsification

Ran the scoped check exactly as designed above (`read_availability_index_safe`, blank-timeframe MTDS rows narrowly
windowed to each cluster's `written_at`, groupby-indexed older-sibling lookup — script stayed in scratchpad per this
investigation's established one-off convention for trivial diagnostic queries):

- **2026-07-13 cluster**: 14,656 blank-timeframe MTDS rows confirmed in-window. Sampled the first 200 — **0/200 have
  an OLDER real-timeframe sibling**, even under the ordering constraint the earlier general 0/200 check didn't apply.
  This is step 4 of the "Precise next step" above: **the mechanism is genuinely something else**, not
  `_write_captured_rows()`. The parent doc's original falsification stands, now with a tighter, ordering-aware check
  behind it.
- **2026-05-05 cluster**: 0 blank-timeframe MTDS rows found in the exact `[22:07:00, 22:07:59]` window — at the time
  this was flagged as an unresolved discrepancy against the parent doc's stated 326-row figure; **resolved below**.

**Verdict on this doc's central question: `_write_captured_rows()` is NOT the mechanism for the 14,656-row
2026-07-13 cluster.** Todo #2 (git-blame `captured_df`'s construction history) is now unblocked and is the next lead.

## Result (2026-08-16, part 2): git-blame resolves both clusters — TWO DIFFERENT root causes, not one

Dispatched a read-only Explore agent to git-blame `_write_captured_rows()`'s history and its callers as of both
cluster dates (todo #2). Its claims were cross-checked against the parent doc's own already-recorded numbers before
being accepted — see below.

**2026-07-13 cluster (14,656 rows) — `_write_captured_rows()` IS the mechanism, via hypothesis (b), NOT a
duplicate-collapse bug:**

- The function existed at commit `79db7597` (2026-07-13, same day), sole caller `rebuild_sports_manifest_v9.py`.
- As of that commit the WHOLE v9 rebuild pipeline was timeframe-blind by construction: `_ROW_KEY_COLS`
  (`_rebuild_sports_write.py:93-104`) does not include `timeframe`, and the caller file has zero references to the
  string `"timeframe"` anywhere. `captured_df` is built from `index_df[captured_mask]`
  (`rebuild_sports_manifest_v9.py:596,727`) — a walk over the OLD v8 manifest INDEX, never a per-row data read.
- So `captured_df` never carried a real per-row timeframe value to omit on this run — a **"blank from birth" gap**
  in the old rebuild's row-key design, not the same additive/duplicate-collapse bug proven for the in-session case.
  The fix at `e0b34e77fd` threads `timeframe` through where the source row HAS one — it does not retroactively
  recover a timeframe the v8 index never carried for this historical run.
- Confidence: SUPPORTED, not proven with certainty (git history alone can't inspect the historical parquet's actual
  column values) — but the code's total architectural blindness to timeframe as of that exact commit is strong,
  independent corroborating evidence.

**2026-05-05 cluster (326 rows) — `_write_captured_rows()` RULED OUT with certainty; different repo, plausible
mechanism that may not even be a bug:**

- Neither `_write_captured_rows()` nor its caller existed yet — both added 2026-06-01/06-11, 3+ weeks later
  (`git log --diff-filter=A` add-dates). Closes the reopened question for this sub-cluster outright.
- **Resolves this doc's own P2 "0-row discrepancy" todo without further investigation**: the parent doc's cited
  "service_name=market-tick-data-service, 14,656/14,982, 98%" figure IS EXACTLY the 2026-07-13 sub-cluster's own
  share (14,656/14,982 = 97.8%, rounds to 98%) — the remaining 326 rows were never claimed to be MTDS-attributed.
  My scoped check's `service_name=market-tick-data-service` filter correctly found 0 rows in that window because
  this sub-cluster genuinely isn't MTDS. Not a discrepancy — a wrong assumption in my own check (that both clusters
  shared one service_name), now corrected by re-reading the parent doc's own number.
- Plausible candidate (circumstantial, NOT confirmed): `market-data-processing-service` commit `45ae73c2`
  (2026-05-05 22:03, same calendar day/hour as the cluster), `scripts/reprocess_sports_odds.py:552-566` —
  `_SERVICE_NAME="market-data-processing-service"` (consistent with "not MTDS" above),
  `_MANIFEST_DATA_TYPE="odds_horizon_bucket"`. Per successful day it writes ONE coarse summary row (blank
  `league_id`, blank `timeframe`, explicit code comment *"keeps pre-flight skip working on resume runs"*) plus one
  real fine-grained row per `(league_id, horizon_name)` shard, all flushed in one batched `writer.write()` — which
  independently explains both the near-identical `written_at` clustering and the 0/200 sibling-check null result
  (the coarse row's blank `league_id` can never match the sibling key against any fine row). **If confirmed, this
  coarse row is a DELIBERATE design pattern, not a bug** — a materially different characterization from the rest of
  the CF-8 chain.

**This overturns this doc's own earlier framing**: the 14,982 rows are two unrelated populations in two different
repos with two different causes, not one shared mechanism.

## Todos

- [x] [DATA] P1. Run the scoped sibling check above (2 narrow written_at windows, older-timestamp ordering constraint)
      against the live MTDS canonical via `read_availability_index_safe` — resolves the `_write_captured_rows()`
      reconciliation either way. **DONE 2026-08-16**: 0/200 (2026-07-13 cluster) have an older real-timeframe
      sibling; 2026-05-05 cluster window returned 0 blank-timeframe MTDS rows. `_write_captured_rows()`
      RE-FALSIFIED. See Result section above. (repo: market-tick-data-service)
- [x] [DATA] P1. Git-blame `_rebuild_sports_write.py` and its callers as of 2026-07-13 and 2026-05-05 to confirm/
      refute whether `captured_df` carried real per-timeframe values at those points in history. **DONE 2026-08-16**:
      2026-07-13 cluster confirmed `_write_captured_rows()`-caused via a "blank from birth" v8-index-blind rebuild
      (not duplicate-collapse); 2026-05-05 cluster's mechanism ruled OUT for `_write_captured_rows()` with certainty
      (script didn't exist yet) — see Result part 2 above. (repo: market-tick-data-service)
- [x] [DATA] P2. Reconcile why the scoped check found 0 blank-timeframe MTDS rows in the exact
      `[2026-05-05T22:07:00, 2026-05-05T22:07:59]` window against the parent doc's own stated 326-row figure.
      **DONE 2026-08-16**: not a discrepancy — 14,656/14,982=97.8%≈98%, the parent doc's own cited "98% MTDS" figure
      already IS just the 2026-07-13 sub-cluster; the 326-row 2026-05-05 cluster was never MTDS-attributed. See
      Result part 2 above. (repo: market-tick-data-service)
- [ ] [DATA] P2. Confirm the MDPS `reprocess_sports_odds.py` coarse-summary-row hypothesis for the 326-row
      2026-05-05 cluster with a live scoped query filtered `service_name=market-data-processing-service` (currently
      circumstantial: date/hour/data_type/structural-shape match, not a direct row-level confirmation).
      (repo: market-data-processing-service)
- [ ] [DATA] P1. **SAFETY** — before any delete/cleanup script targets this 14,982-row population, confirm it
      EXCLUDES the 326-row 2026-05-05 MDPS cluster if the coarse-summary-row hypothesis above is confirmed as
      deliberate design (pre-flight-skip marker), not a bug — deleting it would be a regression, not a cleanup.
      Cross-check against `delete_cf8_phantom_timeframe_sibling_confirmed_2026_08_15.py`'s actual row-selection
      filter to see whether it already excludes this sub-cluster or would sweep it up. (repo: market-tick-data-service)
- [ ] [OPERATOR] P2. Decide remediation policy for the 2026-07-13 cluster's "blank from birth" gap (real timeframe
      never captured by the old v8-index rebuild): is this "safe to leave" (same posture as the earlier P2
      `data_type=odds` conclusion), or does it warrant a real backfill recovering true timeframe from underlying
      source data where still available? Affects whether this is closed as understood-and-accepted or becomes new
      remediation work. (repo: market-tick-data-service)
- [x] [DOC] P3. Fix the stale `market_tick_data_service/live/websocket_streaming_handler.py` path reference in
      `sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md` (if present) to the confirmed real location
      `market_tick_data_service/cli/handlers/websocket_streaming_handler.py`. **DONE 2026-08-16 (moot)**: grepped the
      parent doc for this path — zero hits. The "stale reference" was the dispatching agent's own framing, not an
      actual line in the parent doc; nothing to fix. (repo: unified-trading-pm)

## Progress Log

### 2026-08-16 — doc created, split from parent at its line cap

Dispatched Explore agent (`aa9ff9fb0521b6989`, "Trace ODDS_API odds_horizon_bucket WS classification") returned;
findings triaged against the parent doc's own recorded history before writing anything up, per CLAIM ≤ MEASUREMENT —
the agent's "CONFIRMED" verdict on `_write_captured_rows()` was NOT taken at face value, since it directly restates a
hypothesis the parent doc's own correction pass already falsified. Live-WS-shard branch closed with high confidence
(multiple independent, non-contradicting lines of evidence). `_write_captured_rows()` branch reopened but left
genuinely unresolved, with a concrete, scoped next check identified rather than a re-guess in either direction.

### 2026-08-16 — scoped check run, `_write_captured_rows()` RE-FALSIFIED

Ran todo #1's scoped check (background, `read_availability_index_safe` + groupby-indexed older-sibling lookup —
the naive per-row version had timed out at 3 minutes in the foreground earlier, rewritten before this run). Result:
0/200 sampled 2026-07-13-cluster rows have an older real-timeframe sibling even under the stricter ordering
constraint; the 2026-05-05 cluster window returned zero blank-timeframe MTDS rows at all (new discrepancy, filed as
a todo, not yet explained). `_write_captured_rows()` is confirmed NOT the mechanism for this population — the
parent doc's original falsification was correct. Git-blame (todo #2) is now the live next lead.

### 2026-08-16 — git-blame resolves both clusters: TWO different root causes (big finding, operator notified)

Dispatched Explore agent to git-blame `_write_captured_rows()`'s and its caller's history as of both cluster dates.
Result overturns this doc's own single-mechanism framing: the 14,982 rows are two unrelated populations. 2026-07-13
(14,656 rows) IS `_write_captured_rows()`-caused, but via a "blank from birth" v8-index-blind rebuild, not the
duplicate-collapse bug proven for the in-session case. 2026-05-05 (326 rows) is ruled OUT for `_write_captured_
rows()` with certainty (the script didn't exist yet) and is plausibly (not confirmed) MDPS's `reprocess_sports_
odds.py` writing a deliberate coarse pre-flight-skip marker row — which, if confirmed, is not a bug at all. Also
resolved this doc's own P2 discrepancy todo: the parent doc's "98% MTDS" figure was already just the 2026-07-13
sub-cluster's own share (14,656/14,982=97.8%), not a claim about the full population — no real discrepancy, a wrong
assumption in my own scoped-check filter. Filed a SAFETY todo (P1) flagging that any cleanup/delete script scoped
to this population must not sweep up the possibly-legitimate MDPS marker rows. Per the big-finding HARD RULE
(cross-repo, overturns a previously-recorded framing, data-correctness), notified the operator directly in-chat
this session.
