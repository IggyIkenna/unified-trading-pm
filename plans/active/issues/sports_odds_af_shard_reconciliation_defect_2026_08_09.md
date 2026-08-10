---
doc_type: issue
title: >-
  Sports odds_api attempted_failed vendor-verify (RULED option C) — vendor HAS data; real root cause is a
  shard-granularity write-reconciliation defect, not a genuine vendor coverage gap
summary: >-
  Ran the RULED 2026-08-06 "vendor-verify first" (option C) todo from
  `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` — live-verified 10 (league_id, gap-date) attempted_failed
  groups directly against the Odds-API historical endpoint. Result: 100% of sampled groups show the vendor HAS real
  fixture + bookmaker odds data (contrary to the recommendation's expectation that verification would mostly confirm
  genuine emptiness). Traced why the pipeline still records `attempted_failed`: the sports odds_api manifest shard key
  is `(venue=bookmaker, league_id, date)` — coarser than per-fixture reality (fixture_id is a documented DISPLAY axis,
  not a shard atom, `unified_trading_library/manifest_writer/_rows.py:230-234`). A single run/backfill can capture real
  data for SOME fixtures in a league/day (writes `captured`) while genuinely getting a zero-row response for OTHER
  fixtures in the SAME league/day for the SAME bookmaker (writes `attempted_failed` via the
  `EmptyFromLiveInstrumentError` guard) — both land as separate, uncollapsed rows on the identical shard key with no
  reconciliation. Quantified for 2026-08-02: 735/1082 (67.9%) of that day's odds_api `attempted_failed` rows share a
  shard key that ALSO has a `captured` row from the SAME run (confirmed via `attempted_at`/`written_at`, all within a
  ~3s window on 2026-08-06T18:49Z, the `mtds-backfill-odds-catchup-20260806` VM). The manifest consolidator
  (`uts-prod-manifest-consolidator-market-data-sports`) is running successfully every ~1min (not stale), so this is not
  a "consolidator hasn't run" staleness issue — the per-fixture verdicts are never reconciled into one coherent
  shard-level status in the first place. This inflates every `reachable_coverage`/attempted_failed percentage reported
  in the parent issue doc's 07-27..08-06 table — those are raw row counts over an unreconciled index, not genuine
  current-gap counts. Filed as its own doc because the parent
  (`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`, 1018L) is over its 1000L hard cap and its own
  pre-commit line-cap gate blocks any checkbox-touching edit to it.
status: open
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    sports,
    data-pipeline-correctness,
    odds-api,
    manifest,
    shard-reconciliation,
    capture-status,
    honest-coverage,
    big-finding,
  ]
related:
  [
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
  ]
created: 2026-08-09
author: unknown
last_updated: 2026-08-09
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["/plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md RULED vendor-verify todo"]
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_writer/_rows.py,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_logic.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
  ]
---

# Sports odds_api attempted_failed: vendor-verify confirms vendor HAS data — real defect is shard-level reconciliation

## What I found

Picked up the RULED 2026-08-06 "vendor-verify first" (option C) todo in
`/plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`: the OOM-gap residual
`attempted_failed` (af) population was ~99% classified as an in-coverage expected-but-empty
`record_zero_rows(was_expected=True)` → `EmptyFromLiveInstrumentError` rejection, and the recommendation was "(C)
vendor-verify a sample, then (A) accept residual af as the honest terminal state."

**Vendor-verify sample (10 groups, live `historical/sports/{sport_key}/odds` calls, same shape as
`_run_league_fetch_loop` including re-checking one fixture at its actual TIER_1_OFFSETS timestamps, not just noon):**

| league_id           | date       | vendor fixtures | vendor bookmakers w/ data |
| ------------------- | ---------- | --------------- | ------------------------- |
| ARGENTINA_PRIMERA   | 2026-08-02 | 27              | 17                        |
| MLS                 | 2026-08-02 | 31              | 13                        |
| CHILE_PRIMERA       | 2026-08-02 | 3               | 21                        |
| ELITESERIEN         | 2026-08-02 | 8               | 22                        |
| LIGA_MX             | 2026-08-02 | 11              | 21                        |
| EKSTRAKLASA         | 2026-08-01 | 6               | 22                        |
| ARGENTINA_PRIMERA   | 2026-07-30 | 30              | 16                        |
| BRASILEIRAO         | 2026-07-30 | 12              | 22                        |
| AUSTRIAN_BUNDESLIGA | 2026-08-02 | 9               | 21                        |
| SWISS_SUPER_LEAGUE  | 2026-08-01 | 6               | 23                        |

**100% of sampled groups show the vendor HAS real data** — every one of the exact bookmakers our manifest marks
`attempted_failed` for that league/day is present in the vendor's own response with real odds. This is the OPPOSITE of
what the recommendation's "(C) then (A)" framing expected (that verification would mostly confirm genuine emptiness).

**Root-cause trace.** `unified_trading_library/manifest_writer/_rows.py:230-234` documents `fixture_id` as a
DISPLAY-axis column, not part of the shard atom: "the shard atom remains `(league_id, day)` so `(fixture_id, day)`
bundles the fixture set per cell." The real sports-odds shard key is `(venue=bookmaker, league_id, date)` — coarser than
the genuine per-fixture reality, where a specific bookmaker legitimately covers SOME fixtures in a league/day and not
others (normal per-fixture market-coverage variance, not a failure).

Direct manifest read (`instruments-store-sports-prd-central-element-323112`, date-filtered,
`venue=PINNACLE`/`league_id=ARGENTINA_PRIMERA`/`date=2026-08-02`) shows the identical shard key carrying **3 `captured`
rows AND 13 `attempted_failed` rows**, all from the SAME run — `attempted_at`/`written_at` for every one of the 16 rows
falls within a ~3-second window (`2026-08-06T18:49:32.95Z`–`18:49:35.41Z`), matching the
`mtds-backfill-odds-catchup- 20260806` VM's run window. The backfill genuinely captured real odds for some
ARGENTINA_PRIMERA fixtures that day and genuinely got zero rows for PINNACLE on other fixtures that same day — both
verdicts land on the identical coarse-grained manifest cell with no reconciliation between them.

**Quantified blast radius (2026-08-02 sample only):** of 1082 odds_api `attempted_failed` rows that day, **735 (67.9%)
share a shard key that ALSO has a `captured` row.** Confirmed the manifest consolidator
(`uts-prod-manifest-consolidator-market-data-sports`) is not stale — `gcloud run jobs executions list` shows it
completing successfully every ~1 minute, current as of the check (2026-08-09T22:2x). The consolidator's own documented
"last-write-wins by `attempted_at`" dedup rule (`/codex/05-infrastructure/manifest-consolidator-ssot.md` line ~156) is
evidently not reconciling these same-run, same-shard-key, opposite-verdict rows — either the dedup key used doesn't
match what I traced from `_rows.py`, or the per-fixture writes never get folded into ONE shard-level call before
reaching the consolidator at all (i.e. the defect may be upstream, in how the adapter/orchestrator issues its manifest
writes per shard, not in the consolidator's merge itself — NOT root-caused to file:line in this pass, see the follow-up
todo).

## Why it matters

**Data-pipeline-correctness big finding**: this is not a genuine vendor-coverage gap needing a relabel decision (option
B) or an accept-as-terminal call (option A) — it is a measurement/reconciliation defect that makes a REAL majority of
the sports-odds `attempted_failed` population look worse than it is. Every `reachable_coverage`/attempted_failed
percentage reported in the parent issue doc's 07-27..08-06 table (`captured`/`empty_confirmed`/`attempted_failed` counts
per gap day) is a raw row count over this unreconciled index — those numbers likely OVERSTATE the genuine current gap,
potentially significantly (67.9% on the one day quantified here). Any other sports-odds coverage reporting built the
same way (other reconciliation reports, dashboards) carries the same bias and should be treated with the same caveat
until the reconciliation defect is fixed.

Notified operator per the data-pipeline-correctness-hard-rule big-finding trigger (contradicts prior coverage-percentage
reporting across this pipeline's own audit trail).

## Recommended next steps

- [x] ✅ [DATA] P1. Root-cause + fix the sports odds_api manifest shard-reconciliation defect —
      market-tick-data-service@cf855ff0. `(venue=bookmaker, league_id, date)` is coarser than actual per-fixture
      coverage variance, so a single run can write BOTH `captured` and `attempted_failed` for the identical shard key
      with no reconciliation — confirmed live for `PINNACLE/ARGENTINA_PRIMERA/2026-08-02` (3 captured + 13
      attempted_failed, same run, `attempted_at` within ~3s) and quantified at 67.9% (735/1082) of 2026-08-02's odds_api
      attempted_failed rows sharing a shard key with a co-existing captured row. Read
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` (`_resolve_dedup_cols()`/`_dedup_key_sql()`, the
      documented "last-write-wins by attempted_at" behavior that should already prevent this) FIRST — trace whether the
      dedup key it uses actually matches `unified_trading_library/manifest_writer/_rows.py::_ROW_KEY_COLUMNS`, or
      whether the per-fixture verdicts never get folded into one shard-level write before reaching the consolidator
      (upstream defect in the adapter/orchestrator write path instead). Also assess whether
      `EmptyFromLiveInstrumentError`'s per-fixture "was_expected" guard
      (`unified_api_contracts/canonical/crosscutting/_honest_coverage_logic.py`) is too coarse for sports (checks
      fixture-liveness only, not per-bookmaker-per-fixture coverage) — that may be a second, independent contributor.
      Done when: a unit test confirms a shard key that receives BOTH a captured and an attempted_failed write within one
      run resolves to a single, non-contradictory manifest state, and a re-read of the 2026-08-02 sample shows the
      phantom-duplicate rate materially below 67.9%. (repo: unified-trading-library, market-tick-data-service,
      unified-api-contracts) — **root cause confirmed: NOT the consolidator's dedup key or the
      `EmptyFromLiveInstrumentError` guard** (both behave as documented) — it's an UPSTREAM MTDS write-path bug. Both
      `_write_shard_counts_to_manifest` (captured path, `manifest_finalize.py`) and `_emit_sports_v2_sentinels`
      (attempted_failed/empty_confirmed sentinel fan-out, `sentinels.py`) were stamping the per-fixture id into
      `underlying=` — one of the consolidator's `_OPTIONAL_DEDUP_COLS` — instead of the documented DISPLAY-axis
      `fixture_id=` column (`_rows.py:230-234`, excluded from the dedup key). That fragmented the documented
      `(venue=bookmaker, league_id, day)` shard atom into one manifest row PER FIXTURE, so a captured row and an
      attempted_failed row for the SAME (bookmaker, league, day) never shared a dedup key and never reconciled. Fixed
      both call sites to stamp `fixture_id=`/`"fixture_id"` instead of `underlying=`/`"underlying"`; added 2 regression
      unit tests (`test_sports_shard_write_stamps_fixture_id_not_underlying`,
      `test_emit_sports_v2_sentinels_stamps_fixture_id_not_underlying`) asserting the write path no longer fragments the
      shard atom. **Second half of done-when NOT run this pass**: a live re-read showing phantom-duplicate rate <67.9%
      needs the fix deployed (MTDS image rebuild) + a fresh capture/consolidation cycle — the ALREADY-WRITTEN 2026-08-02
      rows keep their old `underlying=fixture_id` values regardless of this code fix (only new writes stop fragmenting),
      so this is the same live verification already scoped as todo 2 below, not a separate check.
- [ ] [DATA] P2. Once the reconciliation fix above ships, re-run the `reachable_coverage` table for the 07-27..08-06 gap
      days (`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`'s own backfill todo) against the CORRECTED
      manifest read and post the delta — confirms whether the true residual af is small enough to accept as terminal
      (original option A) or still needs further work. Done when: a corrected coverage table is posted in the parent
      issue doc (small marker-append only, respecting its line cap) or a fresh dated doc if still over cap. (repo:
      unified-trading-library)

## Verdict

RULED option C run as directed: 10-group live vendor-verify sample against the Odds-API historical endpoint. Result
CONTRADICTS the recommendation's "then (A)" expectation — 100% of sampled groups show the vendor has real, capturable
data, and the root cause is a manifest shard-granularity write-reconciliation defect (not a genuine vendor gap),
quantified at 67.9% phantom-duplicate rate on the one day fully measured. Filed as a P1 follow-up rather than fixed
blind in this pass (the fix touches consolidator dedup-key resolution and/or the honest-coverage guard, both areas this
codebase's own SSOT flags as historically fragile). No code changed this todo — pure vendor-verify + root-cause
identification.

## Progress Log

**2026-08-09 (slot 32, data_engineering)** — Dispatched the RULED "vendor-verify first" todo from
`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`. Fetched the live `odds-api-key` secret
(`central-element-323112`), confirmed vendor quota healthy (10.6M+ credits remaining). Pulled a sample of
`attempted_failed` odds_api shards from the sports manifest (`instruments-store-sports-prd`, date-filtered reads via
`read_availability_index_safe`, no whole-corpus walk) across 2026-07-27/07-30/07-31/08-01/08-02. Resolved canonical
`league_id` → Odds-API `sport_key` via `unified_api_contracts` (`get_league` → `api_football_id` →
`LEAGUE_CLASSIFICATION_DATA[afid]['odds_api_league_name']`). Ran 10 live historical-odds queries — 100% hit. Verified
the finding isn't a snapshot-timing artifact by re-querying one real ARGENTINA_PRIMERA fixture at 4 different
TIER_1_OFFSETS-derived timestamps (T-2h/T-1h/T-10m/T-0) — pinnacle odds present at every one. Traced the manifest schema
(`_rows.py`) to confirm `fixture_id` is display-only, found the same-run captured+attempted_failed contradiction for
`PINNACLE/ARGENTINA_PRIMERA/2026-08-02` via `available_at`/`attempted_at`/`written_at` columns, quantified the 67.9%
(735/1082) phantom-duplicate rate for that day, and confirmed the consolidator is running successfully (not stale) via
`gcloud run jobs executions list uts-prod-manifest-consolidator-market-data-sports`. Attempted to record this directly
in the parent issue doc first; its pre-commit `check_line_caps` hook hard-blocked the edit (1018L, over the 1000L cap,
and my checkbox-flip + evidence diff didn't fit any of the three documented small-edit exceptions) — filed this
standalone doc instead per CLAUDE.md's "split when over cap" guidance, `related:` back to the parent. No code shipped
(pure investigation, per this todo's own done-when).

**2026-08-09 (slot 32, data_engineering)** — Picked up todo 1 (root-cause + fix). Traced the write path from
`odds_api_adapter.py` → `venue_fetch.py::_fetch_sports_venue_and_write` (captured shards grouped by
`(bookmaker_key, league_id, fixture_id)`) → `manifest_finalize.py::_write_shard_counts_to_manifest` (captured rows) and
`sentinels.py::_emit_sports_v2_sentinels` (attempted_failed/empty_confirmed sentinel fan-out, one call per (bookmaker,
league_id, fixture_id) not already captured). Confirmed the consolidator's dedup key (`_BASE_DEDUP_COLS` +
`_OPTIONAL_DEDUP_COLS`, `manifest_consolidator.py`) behaves exactly as documented — `underlying` IS in
`_OPTIONAL_DEDUP_COLS`, `fixture_id` is NOT. Both write call sites were stamping the fixture id via
`underlying=`/`"underlying"` instead of the dedicated `fixture_id=`/`"fixture_id"` display-axis column
(`ManifestWriter.add()` and `_ROW_KEY_COLUMNS` both already support `fixture_id` — it was simply the wrong kwarg name at
both call sites). Root cause is a plain column-naming bug in MTDS, not a consolidator or honest-coverage-guard defect.
Fixed both sites (`manifest_finalize.py`, `sentinels.py`), added 2 regression unit tests, ran full `quality-gates.sh`
(green, sentinel matches shipped SHA), shipped via quickmerge — market-tick-data-service@cf855ff0, verified on
`origin/live-defi-rollout`. Flipped todo 1's checkbox above. Live phantom-duplicate-rate re-verification against the
2026-08-02 sample is deferred to todo 2 (already scoped for exactly this, and requires the fix to reach the deployed
MTDS image + a fresh capture/consolidation cycle before any NEW rows reflect it — old rows keep their pre-fix
`underlying=fixture_id` values).

**2026-08-10 (slot 31, data_engineering)** — Picked up todo 2 (P2, re-run reachable_coverage for 07-27..08-06 gap). Fix
cf855ff0 confirmed on LDR. Found MTDS Cloud Build predated the fix (b5c79987 at 19:56 UTC vs commit at 22:45 UTC) —
triggered new build 20f30012 (SUCCESS). Fixed a blocking cloudbuild.yaml defect (`_PKG_NAME` unused substitution,
introduced by 841cf94f) — shipped market-tick-data-service@21346114 via quickmerge. The launch script auto-detected the
stale MTDS tarball and republished it at SHA 213461147eb7 (includes both cf855ff0 fix AND the cloudbuild fix). Launched
targeted backfill VM `mtds-backfill-odds-gap-20260727-20260806` (SPOT, asia-northeast1-c, 07-27..08-06, 5-day chunks)
with the fixed MTDS code. Armed persistent Monitor on run.log. Awaiting backfill completion before computing corrected
coverage table.
