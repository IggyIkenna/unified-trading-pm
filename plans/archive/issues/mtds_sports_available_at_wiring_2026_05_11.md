---
title: "MTDS-slice sports `available_at` wiring — audit + wiring point + open design Qs"
created: 2026-05-11
author: harsh-bucket-and-adapter-tab (slot 4)
source:
  - plans/active/available_at_lookahead_bias_completion_2026_05_08.md (Phase 1 — "TRACK — sports adapter stamping")
  - plans/active/work_split_2026_05_11_harsh.md § "Slot 4" (sports adapter stamping half)
  - market-tick-data-service/market_tick_data_service/engine/orchestrator.py:2102 (_process_sports_venue_with_leagues)
  - unified-trading-library/unified_trading_library/availability_stamping.py
locked_by: live-defi-rollout
locked_since: 2026-05-11
execution:
  owner:
    harsh slot 4 (the MTDS-slice wiring) ← coordinate with Ikenna slot 3 (available_at umbrella owner) + slot 3 (wave3x
    Track E helpers)
  cadence: one-shot (the wiring); then QG-wired (basedpyright + the eventual STEP-5.67 record_captured-stamping check)
  verifier:
    "sports odds parquets carry a non-null `available_at` col == bm_time; LookaheadBiasError strict-mode green for
    sports features-* compute"
  last_executed:
    2026-05-11 (code wired — market-tick-data-service@c186ecb; full-pipeline verifier still pending a sports backfill
    run)
---

> **STATUS 2026-05-11: code SHIPPED.** market-tick-data-service@`c186ecb` wires
> `stamp_available_at_odds_snapshot(shard_df, snapshot_time_col="bm_time")` (UTL wave3x Track E @UTL`2ab3685`) into
> `_process_sports_venue_with_leagues` before `StreamingParquetWriter.write_chunk`, with shard-level failure isolation
> (a per-shard stamping failure → `failed_shards` dict → manifest sentinel `record_failed` + `ADAPTER_FETCH_FAILED`,
> shard skipped — NOT raised). `bm_time` confirmed universal for the only adapter on this path (ODDS_API). 5 new tests
> in `market-tick-data-service/tests/unit/test_sports_odds_available_at.py` pass. **REMAINING** (not slot-4 scope —
> route to Ikenna slot 3, the available_at umbrella owner): (1) flip the
> `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 "TRACK — sports adapter stamping" todo; (2) decide the
> 2 open design Qs below (Q-B all-NaT routing — slot 4 chose `record_failed`; Q new — the sports path uses
> `record_captured_from_counts` so the writegate `assert_available_at_present` guard doesn't fire on it, a
> column-presence assertion at the `StreamingParquetWriter.write_chunk` boundary would be a small follow-up). The
> full-pipeline verifier (sports odds parquets on disk carry non-null `available_at`; LookaheadBiasError strict-mode
> green for sports features-\* compute) needs a sports backfill run — operationally-pending.

# MTDS-slice sports `available_at` wiring — audit (slot 4, 2026-05-11)

> **What this is**: the gated-prep audit for slot 4's "wire Track E's UTL helpers into MTDS sports adapters" task
> (`work_split_2026_05_11_harsh.md` § "Slot 4"). Captured as an issue doc rather than annotated onto
> `available_at_lookahead_bias_completion_2026_05_08.md` because Ikenna slot 3 owns that plan body this cycle (Phase 0
> bar-boundary contract + Phase 4-5 audits) — see cross-side handshake in the work-splits. Triage target: fold into
> `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 (the "TRACK — sports adapter stamping" todo) once the
> gates clear, OR keep here if Ikenna slot 3 wants to own the full sports slice. Slot 1: route a cross-side ping to
> Ikenna slot 3 if a hand-off decision is needed.

> **Severity**: P1 — sports `available_at` is on the lookahead-bias critical path (per
> `available_at_lookahead_bias_completion_2026_05_08.md` — blocks Group F batch-vs-live reconciliation). Not a same-day
> blocker (gated). **Blast radius**: MTDS sports odds write path + downstream features-sports-service lookahead gate.
> **Suggested owner**: harsh slot 4 (wiring) under Ikenna slot 3's umbrella.

## What MTDS actually writes for `sports`

MTDS is "market data only" — so the **only sports data MTDS writes is ODDS data** (`instrument_type=odds`,
`data_type=trades`). Fixture-level reference data (lineups / injuries / fixture*stats / fixture_events / weather /
reference-tables) is written by the **sports backfill owned by `sports_master_2026_05_07`** (the `af-backfill-` /
`fs-backfill-` / `sfi-backfill-` etc. VMs), NOT by MTDS. So the `stamp_available_at_lineups` / `_injuries` /
`\_post_match*\*` helpers Track E ships are for those OTHER write paths; the MTDS slice is the **odds-snapshot stamping
only**.

## The MTDS sports write path (the wiring point)

`market_tick_data_service/engine/orchestrator.py` →
`_process_sports_venue_with_leagues(venue, process_date, api_key, venue_data_types, asset_group)` (line ~2102):

1. `records_df = await _fetch_one_venue(venue, process_date, ...)` — the sports adapter (odds_api / betfair / matchbook
   / sfi / footystats — under `market_interface/adapters/sports/`) returns a canonical odds DataFrame.
2. Rename `venue`→`bookmaker_key` if needed; ensure `league_id` col exists.
3. `for (bookmaker_key, league_id), shard_df in records_df.groupby(["bookmaker_key", "league_id"]):`
   - build
     `gcs_path = f"{RAW_TICK_DATA_PREFIX}day={process_date}/asset_group=sports/data_source={SRC}/venue={BM}/league_id={L}/instrument_type=odds/data_type=trades/ticks.parquet"`
   - `shard_writer = StreamingParquetWriter(bucket=bucket, gcs_path=gcs_path)` (UTL `StreamingParquetWriter`, plain
     parquet writer — NOT `PartitionedTickWriter`; `PartitionedTickWriter` explicitly raises for `asset_group="sports"`
     per `_build_partition_path_for_asset_group`, orchestrator.py:885-887).
   - `shard_writer.write_chunk(shard_df)` ← **the stamping injection point: stamp `shard_df["available_at"]` before this
     call** (or stamp `records_df["available_at"]` once right after `_fetch_one_venue`, before the groupby — either
     works; per-shard is cheaper to reason about, whole-df is one call).
   - Manifest recording is decoupled: `shard_counts[(bm_str, "trades", league_str, "odds", "")] += rows` accumulates,
     then flushed later via `writer_manifest.record_captured_from_counts(...)` (so the writegate
     `assert_available_at_present` guard does NOT fire on this path today — it fires only on the `record_captured` path
     that writes a df; `record_captured_from_counts` takes counts, not a df. **Open Q (B): does the sports path need a
     separate `assert_available_at_present`-equivalent guard, or is the column-presence assertion enough at the
     parquet-write boundary?**)

## The stamping rule for sports odds

Per CLAUDE.md "available_at is a write-time column" → "Pre-match odds: publication time per snapshot (opening days
before, closing at kickoff)". The odds-API adapter design (odds_api_adapter.py header) says: **`bm_time` (bookmaker
`market.last_update`) is ground truth, not fetch_time** — i.e. `bm_time` is when the bookmaker published that line, so
that's the "publication time per snapshot". So:

```python
# In _process_sports_venue_with_leagues, before shard_writer.write_chunk(shard_df):
from unified_trading_library.availability_stamping import stamp_available_at_event_time
shard_df = stamp_available_at_event_time(shard_df, event_time_col="bm_time")  # available_at = bm_time
# (OR a Track-E `stamp_available_at_odds(shard_df, ..., source=data_source)` that does bm_time + emission_latency_ms_for_source)
```

The UTL `availability_stamping.py` module **already has** `stamp_available_at_event_time` (line 137) — its module
docstring even has the exact example `stamp_available_at_event_time(df, event_time_col="bm_time")` for the odds case. So
the helper Track E nominally ships (`stamp_available_at_odds`) is either already covered by
`stamp_available_at_event_time` OR Track E adds a thin `stamp_available_at_odds` wrapper that also adds
`emission_latency_ms_for_source(source)`. **Open Q (A): which is canonical for odds — `available_at = bm_time`
(event-time, zero polling lag, slightly optimistic) or
`available_at = bm_time + emission_latency_ms_for_source(<sports source>)` (conservative)?** This is a Track E /
sports_master / Ikenna-slot-3 design call, not mine. (And: is there a registered `emission_latency_ms_for_source` entry
for the sports sources `odds_api` / `sfi` / `footystats` / `betfair` / `matchbook` in UAC `SOURCE_PRIORITY`? If not,
that's a UAC pre-req — Track E or wave3x Track B territory.)

## Gates (before this can ship)

1. **Slot 3 (wave3x Track E) ships its UTL helpers.** Mostly already present in `availability_stamping.py`
   (`stamp_available_at_lineups` / `_event_time` / `_post_match` / `_offset` / `_explicit` / `_cefi_tick`); Track E may
   add `stamp_available_at_odds` + reorganise the module into a package (`availability_stamping/`). Need the final
   shape + the odds-rule decision (Open Q A).
2. **Ikenna slot 3 Phase 0 (bar boundary contract)** — actually **NOT a hard gate for the MTDS sports odds slice**:
   Phase 0 blocks "chain link 1 (adapter stamping) for **MDPS-derived** data_types" (OHLCV/aggregate bars). Sports odds
   is raw tick data written directly by MTDS — not MDPS-derived — so it doesn't stand on the bar-boundary contract. The
   work-split lists Phase 0 as a gate for "per-adapter wiring" generally (the bar-data adapters) — for sports odds
   specifically it's only Open Q A that gates. **Recommendation**: I can ship the sports-odds stamping as soon as Open Q
   A is answered + Track E's helper shape is final, without waiting for Phase 0. Confirm with Ikenna slot 3 / slot 1.
3. **The odds-row schema has a `bm_time` column on disk for all sports sources** — verified true for odds_api (adapter
   header). Need to confirm betfair / matchbook / sfi / footystats adapter outputs also carry `bm_time` (or the
   equivalent publication-time col), else the stamping helper's `event_time_col=` differs per source → may need a
   per-source dispatch (like the CeFi `source=` arg).

## Open design questions (route to Ikenna slot 3 / sports_master / slot 1)

- **Q-A**: odds `available_at` rule — `bm_time` (event-time) vs `bm_time + emission_latency_ms_for_source(src)`?
- **Q-B**: does the MTDS sports write path need an `assert_available_at_present`-equivalent guard (it uses
  `record_captured_from_counts`, not `record_captured(df)`, so the writegate guard doesn't fire), or is the
  column-presence assertion at the `StreamingParquetWriter.write_chunk` boundary sufficient?
- **Q-C**: do all sports adapters (betfair / matchbook / sfi / footystats, not just odds_api) emit a `bm_time` (or
  equivalent publication-time) column, or is a per-source `event_time_col` / `source=`-arg dispatch needed?
- **Q-D**: is there a `SOURCE_PRIORITY` / `emission_latency_ms_for_source` entry for the sports sources in UAC? If not
  and Q-A picks the conservative rule, that's a UAC pre-req.

### Answers (slot 3, 2026-05-11 — Re-task c)

> **Q-A — RESOLVED conservative rule**: `available_at = bm_time + emission_latency_ms_for_source(<sports_src>)` is the
> canonical rule. **Reasoning**: per CLAUDE.md "Live = batch — same data, same fields, same timing semantics" rule,
> historical writes MUST stamp with the live-pipeline-arrival latency added, not the raw event time. The bm_time alone
> gives feature compute at `bm_time + 1000ms` a row that the live pipeline (5s polling cadence on odds_api) would not
> actually have observed yet — that's a 4-second look-ahead leak. The conservative rule (`bm_time + 5000ms` for
> odds_api) matches CeFi's `tick_timestamp + emission_latency_ms_for_source(tardis=50ms)` precedent at
> `PartitionedTickWriter.write_chunk`. **Action**: Harsh slot 4's shipped behaviour (event-time only) stays in place as
> a temporary state with a named successor — filed as Phase 1 P1 follow-up todo in
> `available_at_lookahead_bias_completion_2026_05_08.md` ("Sports odds — promote `bm_time` stamping to conservative
> rule"). Sequencing-safe because conservative ≥ optimistic; downstream `<= target_ts - horizon` checks become slightly
> more conservative, no regression.

> **Q-B — RESOLVED column-presence assertion at the `StreamingParquetWriter.write_chunk` boundary**. The writegate
> `assert_available_at_present(df)` inside `ManifestWriter.record_captured` is the right guard, but it only fires on the
> `record_captured(df=...)` code path. MTDS sports uses `record_captured_from_counts(...)` (no df passed), so the guard
> doesn't fire today. Right shape: **call `assert_available_at_present(df)` unconditionally inside
> `StreamingParquetWriter.write_chunk(df)`** — that's the universal parquet-write boundary every MTDS adapter passes
> through, so adding the guard there covers ALL data_types (cefi via `PartitionedTickWriter`, sports + prediction
> streaming via `StreamingParquetWriter`, future adapters too) consistently, regardless of which manifest helper fires
> downstream. Filed as Phase 1 P1 follow-up todo in `available_at_lookahead_bias_completion_2026_05_08.md`
> ("`StreamingParquetWriter.write_chunk` — `assert_available_at_present` boundary guard"). ~30-min UTL edit + 5 unit
> tests.

> **Q-C — DEFERRED (not in current scope; re-audit when other adapters wire into MTDS)**. The issue doc verifies
> `bm_time` is universal for the ODDS_API adapter, which is the only sports adapter currently routed through
> `_process_sports_venue_with_leagues`. Other adapters (betfair / matchbook / sfi / footystats) EXIST under
> `market_interface/adapters/sports/` but are NOT wired into the MTDS sports orchestrator surface today — verified by
> reading the sports SOURCE_PRIORITY (Q-D answer below): ODDS_SNAPSHOT / ODDS_MOVEMENT / ARBITRAGE are all routed to
> `odds_api` only; FIXTURE_LINEUPS / FIXTURE_EVENTS / FIXTURE_STATS / etc. go to `api_football` but via the
> sports-backfill VMs, NOT through MTDS's sports orchestrator. So Q-C is moot for the current shipping state of MTDS
> sports. Re-audit if a future sports_master phase wires additional sports adapters into MTDS (Harsh's MTDS slot's
> next-cycle scope OR sports_master Phase 1-2). If betfair/matchbook get wired, those adapters will likely have their
> own publication-time column name (e.g. `pt` for betfair publish-time), needing a per-source `event_time_col` dispatch
> — handle at wiring time.

> **Q-D — RESOLVED yes, sports sources already have SOURCE_PRIORITY + EMISSION_LATENCY_MS_BY_SOURCE entries** in UAC.
> Verified 2026-05-11 by reading `unified_api_contracts/canonical/crosscutting/source_priority.py`:
> `api_football=1000ms`, `odds_api=5000ms`, `understat=7_200_000ms` (2h post-match xG),
> `soccer_football_info=3_600_000ms` (1h SFI freeze cadence), `open_meteo=3_600_000ms` (1h forecast issue cadence),
> `transfermarkt=86_400_000ms` (24h market values cadence). No UAC pre-req remains — the conservative rule (Q-A) is
> implementable today on the strength of existing UAC registrations. No new UAC entries needed.

### Disposition (Re-task c → "Recommended decision" below)

This issue doc's status flips from `STATUS: code SHIPPED — 2 open Qs` to
`STATUS: code SHIPPED + 4 design Qs RESOLVED + 2 P1 follow-up todos filed`. The actual code change (conservative-rule
promotion + writer-boundary guard) lives in `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 follow-up
todos. This issue doc is ready to **archive** (per CLAUDE.md "Plan Archival" HARD RULE) once the 2 P1 follow-ups land —
slot 3 owns the archival routing decision but does NOT auto-archive (live-defi-rollout lock). Archival deferred to
whoever ships the 2 P1 follow-ups, citing this resolution as the source-of-decision.

## Recommended decision

Fold this into `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 once the gates clear; the actual code
change is small (a few lines in `_process_sports_venue_with_leagues` + the column-presence assertion + ~3-5 unit tests,
mirroring `tests/unit/test_partitioned_writer_cefi_available_at.py`). Until then this issue doc holds the audit so the
wiring doesn't need a re-scan.
