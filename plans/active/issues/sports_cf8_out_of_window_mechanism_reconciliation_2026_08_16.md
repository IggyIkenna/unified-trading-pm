---
doc_type: issue
title:
  "CF-8 out-of-window (14,982-row) blank-timeframe `odds_horizon_bucket` population — live-WS-shard hypothesis RULED
  OUT; `_write_captured_rows()` hypothesis RE-FALSIFIED by a tighter scoped check (2026-08-16) — mechanism still
  genuinely unknown; split from the parent doc at its 999-line cap"
summary: >-
  Split from `sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md` (at its 999-line hard cap) to continue the
  root-cause chase for the 14,982-row out-of-window blank-`timeframe` `odds_horizon_bucket` population. A dispatched
  Explore agent traced the live-WS-shard path end-to-end and ruled it out with high confidence (ODDS_API's connector is
  BLOCKED-CREDENTIALS — zero ticks structurally possible — and has no `data_type` gating regardless). It also proposed
  `_write_captured_rows()` (fixed at `market-tick-data-service@e0b34e77fd`, 2026-08-15) as the mechanism, matching the
  row-count/service_name/date-cluster signature. But the parent doc's own already-recorded correction pass explicitly
  falsified this exact hypothesis via a 0/200 sibling check. A tighter, ordering-aware scoped check (2026-08-16)
  RE-FALSIFIES it — the mechanism for this population remains genuinely unknown; see the Result section below.
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

## Todos

- [x] [DATA] P1. Run the scoped sibling check above (2 narrow written_at windows, older-timestamp ordering constraint)
      against the live MTDS canonical via `read_availability_index_safe` — resolves the `_write_captured_rows()`
      reconciliation either way. **DONE 2026-08-16**: 0/200 (2026-07-13 cluster) have an older real-timeframe
      sibling; 2026-05-05 cluster window returned 0 blank-timeframe MTDS rows. `_write_captured_rows()`
      RE-FALSIFIED. See Result section above. (repo: market-tick-data-service)
- [ ] [DATA] P1. Git-blame `_rebuild_sports_write.py` and its callers (`rebuild_sports_manifest_v9.py`,
      the 2026-07-14 targeted-backfill script) as of 2026-07-13 and 2026-05-05 to confirm/refute whether `captured_df`
      carried real per-timeframe values at those points in history — **now unblocked**, the sibling check above came
      back negative, this is the next lead. (repo: market-tick-data-service)
- [ ] [DATA] P2. Reconcile why the scoped check found 0 blank-timeframe MTDS rows in the exact
      `[2026-05-05T22:07:00, 2026-05-05T22:07:59]` window against the parent doc's own stated 326-row figure for this
      cluster — check `service_name`/`capture_status`/second-level bounds used by the original count.
      (repo: market-tick-data-service)
- [ ] [DOC] P3. Fix the stale `market_tick_data_service/live/websocket_streaming_handler.py` path reference in
      `sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md` (if present) to the confirmed real location
      `market_tick_data_service/cli/handlers/websocket_streaming_handler.py`. (repo: unified-trading-pm)

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
