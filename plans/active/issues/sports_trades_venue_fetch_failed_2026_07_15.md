---
doc_type: issue
title:
  sports/trades DP_RUN_MOSTLY_EMPTY (112,277 attempted_failed rows, 21.5%) — NOT a live/recurring venue outage; a v9
  schema-upgrade rebuild silently re-stamped years-old dead rows' attempted_at to its own runtime, making 2020-2022 data
  look like the freshest failure in the whole alert batch — code fix shipped, historical-row restore still open
summary:
  "Investigated the sports/trades DP_RUN_MOSTLY_EMPTY alert cell (112277/522276 attempted_failed,
  error_reason=VENUE_FETCH_FAILED dominant at 94,127 rows, plus an 18,150-row EmptyFromLiveInstrumentError-guard slice)
  flagged as the freshest (attempted_at up to 2026-07-13T23:56Z) of the whole alert batch. Root cause: NOT a
  live/recurring fetch failure. ALL 112,277 rows share one 8-second attempted_at window (2026-07-13T23:56:41-48Z) with a
  blank fixture_id and pipeline_mode=batch_api_football/source=api_football — fingerprints of a bulk RE-EMIT, not
  independent live fetch attempts. Confirmed via git-log pickaxe that the literal error_reason=VENUE_FETCH_FAILED string
  was REMOVED from live sentinel-classification code on 2026-06-28 (market-tick-data-service@b989284c decomposed the
  opaque fallback into UNCLASSIFIED:{code} so real codes stop being masked) — meaning these rows cannot have been
  written by the CURRENT live code path; they are OLD attempted_failed rows (originals span 2020-08-24..2026-05-31)
  carrying the dead pre-2026-06-28 classification vocabulary, re-emitted by `rebuild_sports_manifest_v9.py`'s 2026-07-13
  E4 apply-pass (confirmed live: a code comment in `_rebuild_sports_write.py` cites this exact date/pass; the live GCS
  object-generation history for `_index/availability_index.parquet` shows an ~26min write gap + a 41.0MB→47.3MB size
  jump spanning exactly 2026-07-13T23:53:42Z..2026-07-14T00:19:26Z, bracketing the observed attempted_at). The bug:
  `_write_attempted_failed_rows()` / the CF-11 empty→attempted_failed upgrade branch in `_write_empty_rows()` re-emit
  PRE-EXISTING rows via `record_failed()`/`record_empty()` WITHOUT an explicit attempted_at=, so UTL's
  ManifestWriter._record_status defaults it to datetime.now(UTC) — the rebuild's OWN runtime — silently overwriting the
  real last-attempt timestamp on rows that were never actually re-attempted. This directly explains why a genuinely
  years-old, already-investigated failure population looked like the FRESHEST cell in the entire alert batch. The
  18,150-row EmptyFromLiveInstrumentError-guard slice (record_empty(SOURCE_RETURNED_ZERO) rejected because
  instruments-service confirms the fixture was alive) is confirmed WORKING AS DESIGNED, not a residual gap in the
  2026-06-21 BOOKMAKER_NO_LEAGUE_COVERAGE fix: is_bookmaker_league_covered() returns True for 100% of the 112,277
  attempted_failed rows (verified by direct re-derivation against the live oracle) — every one is a genuinely-covered
  (bookmaker, league) pair whose specific historical fixture needs a real re-fetch to resolve, not a coverage-scope gap
  the June-21 fix should have caught. Code fix shipped: market-tick-data-service@6fad6565 adds
  `_attempted_at_from_row()` (mirrors the existing `_available_at_from_row()` honest-proxy convention) and wires it into
  all 3 record_failed()/record_empty() re-emit call sites in `_rebuild_sports_write.py`, so any FUTURE re-run of this
  (or a similar) rebuild preserves the row's real attempted_at instead of stamping 'now'. 6 new regression tests, QG
  green. Data-side: the 112,277 already-corrupted rows in the LIVE manifest are NOT yet restored to their true
  attempted_at (GCS object versioning is off; the pre-rebuild generation IS recoverable via soft-delete — exact
  generation number + recipe below — but doing the swap safely on a live, actively-written production bucket needs a
  controlled window, not a blind in-place restore under time pressure) — documented as an open follow-up rather than
  forced."
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    sports,
    manifest,
    honest-coverage,
    capture-status,
    attempted-failed,
    attempted-at,
    v9-rebuild,
    data-pipeline-alerts,
    venue-fetch-failed,
    bookmaker-coverage,
  ]
related:
  [
    ../data_pipeline_alerts_batch_remediation_2026_07_15.md,
    ../data_completion_to_100_all_ag_2026_06_21.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-15
parent_epic: sports_master
priority: P2
source:
  [
    "operator-dispatched sub-agent task, sports/trades cell from data_pipeline_alerts_batch_remediation_2026_07_15.md's
    'New todos' section, 2026-07-15",
  ]
assigned_vm: NA
resolved_by:
  [
    "market-tick-data-service@6fad6565fe66ef34ea245172dc1e606c0a2dd183 (code fix: _attempted_at_from_row() + wiring into
    all 3 v9-rebuild re-emit call sites; prevents recurrence, does not retroactively fix the already- corrupted 112,277
    live rows)",
    "market-tick-data-service@e9d9dec0 (2026-07-23, CAS-safe wipe of ALL source=api_football MTDS-sports manifest rows —
    see mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md — removed the entire 112,277-row
    attempted_failed population this doc analyzed as a side effect, since every row was
    pipeline_mode=batch_api_football/ source=api_football; makes the 'restore true attempted_at' open follow-up moot —
    there is nothing left to restore)",
  ]
locked_by:
locked_since:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# sports/trades VENUE_FETCH_FAILED + EmptyFromLiveInstrumentError-guard investigation — 2026-07-15

## Ground truth (live re-query, 2026-07-15)

Live manifest `market-data-tick-sports-prd-central-element-323112` / `_index/availability_index.parquet`
(`data_type == "trades"`, 1,790,372 rows):

```
capture_status
empty_confirmed     1,268,096
captured               409,999
attempted_failed       112,277
```

`attempted_failed` breakdown by `error_reason`:

- `VENUE_FETCH_FAILED` — **94,127 rows** (BETFAIR=31,376, MATCHBOOK=31,376, PINNACLE=31,375). `league_id` spans 17
  leagues (MLS, SEGUNDA_DIVISION, J1_LEAGUE, SERIE_B, LA_LIGA, SUPER_LIG, LIGUE_2, ELITESERIEN, LIGUE_1, ...);
  `fixture_id`/`underlying`/`instrument_id`/`job_id` are ALL blank; `date` (the cell's business date, not
  `attempted_at`) spans **2020-08-24 to 2026-05-31** (1,579 distinct dates); `pipeline_mode=batch_api_football`,
  `source=api_football` on every row.
- The `EmptyFromLiveInstrumentError`-guard message
  (`record_empty(reason=SOURCE_RETURNED_ZERO) rejected: ... catalog says 'trades' was ALIVE on <VENUE>/<DATE> ... Use record_failed(EmptyFromLiveInstrumentError(...)) instead`)
  — ** 18,150 rows** (BETFAIR=6,050, MATCHBOOK=6,050, PINNACLE=6,050). `date` spans 2020-06-06 to 2026-02-13 (350
  distinct dates), many 2022-era as the operator's original citation noted.
- `94,127 + 18,150 = 112,277` — exhaustive; no third bucket.
- **Every one of the 112,277 rows shares `attempted_at` in the exact window `2026-07-13T23:56:41.328635Z` –
  `2026-07-13T23:56:48.805133Z`** (an 8-second burst). This is the single most important fact: it rules out "still
  actively recurring" — there is no fresh accumulation after 2026-07-13, and the burst signature (thousands of rows in 8
  seconds, spanning 1,579/350 distinct historical dates, zero fixture-level granularity for the VENUE_FETCH_FAILED
  slice) is not consistent with live per-date network fetch attempts at all.

## Part A — VENUE_FETCH_FAILED is dead classification vocabulary, re-stamped by a rebuild pass

`rg -l "VENUE_FETCH_FAILED"` across `market-tick-data-service`/`unified-trading-library`/`unified-api-contracts`
production source returns **zero hits** — the literal string does not exist anywhere in currently-committed code (only
in tests/scripts/plan docs as example text). `git log --oneline -S "VENUE_FETCH_FAILED" --all` on
market-tick-data-service turns up:

```
b989284c fix(mtds): decompose VENUE_FETCH_FAILED into UNCLASSIFIED:{code} fallback; ...
```

Landed **2026-06-28**. The diff:

```diff
- sports_classified_error = classification.error_code if classification is not None else "VENUE_FETCH_FAILED"
+ sports_classified_error = classification.error_code if classification is not None else f"UNCLASSIFIED:{code_token}"
```

Before 2026-06-28, `_emit_sports_tier2_sentinels`/`_emit_tier3_for_dt` (`sentinels.py`) collapsed EVERY unclassified
venue error into the opaque literal `"VENUE_FETCH_FAILED"`, discarding the real underlying error code. This fallback was
removed 2026-06-28. **A row written by the live code AFTER 2026-06-28 cannot carry
`error_reason="VENUE_FETCH_ FAILED"`** — so the 94,127 rows, despite showing `attempted_at=2026-07-13` (after the fix),
must be RE-EMITTED historical data whose classification predates 2026-06-28.

Traced the re-emit mechanism: `market_tick_data_service/scripts/_rebuild_sports_write.py::_write_attempted_failed_rows`
re-emits PRE-EXISTING `attempted_failed` rows during the v8→v9 manifest schema-upgrade rebuild
(`rebuild_sports_manifest_v9.py`), explicitly preserving the row's OLD `error_reason` verbatim:

```python
existing_error = str(row.get("error_reason", row.get(reason_col)) or "")
...
writer.record_failed(row_key=row_key_fail, error=existing_error, pipeline_mode=mode, ...)
```

Confirmed the rebuild's **E4 apply-pass ran on 2026-07-13** — a comment already in `_rebuild_sports_write.py` (added by
a concurrent agent this same day) cites it directly:
`"ITEM (sports_manifest_canonicalisation_2026_06_01.md, 2026-07-13 E4 apply-pass finding): ..."`. This is airtight: the
July-13 rebuild run is what wrote these rows, preserving their pre-2026-06-28 `error_reason="VENUE_FETCH_FAILED"`
classification while stamping a fresh `attempted_at`.

**Verdict: NOT a live, currently-recurring venue outage.** No retry/backoff/circuit-breaker fix applies — there is
nothing live to back off from. This is dead historical data whose freshness signal was corrupted by a schema-upgrade
tool, not an active fetch failure.

## Part B — the EmptyFromLiveInstrumentError-guard slice: verified NOT a residual coverage gap

Read `data_completion_to_100_all_ag_2026_06_21.md:455-489` in full. The 2026-06-21 fix
(`market-tick-data-service@050a091`) scoped itself specifically to **`sentinels.py`'s `elif` branch**: when
`is_bookmaker_league_covered(bookmaker, league)` is `False` (the bookmaker has NEVER observed-priced this league), route
to `record_empty(EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE)` instead of a fetch-failure path. It did NOT touch the sibling
branch — when the bookmaker DOES cover the league but this specific historical fixture returned zero rows, the code
(current, live, unchanged since) calls:

```python
writer_manifest.record_zero_rows(row_key=_rk, reason="SOURCE_RETURNED_ZERO", was_expected=True, ...)
```

`record_zero_rows(was_expected=True)` is a **deliberate, documented, sanctioned path**
(`unified_trading_library/manifest_writer/_writer_record.py:566-580`): it directly constructs an
`EmptyFromLiveInstrumentError` and routes to `record_failed()` — "a source that returns nothing for a shard the
catalog/fixtures confirm SHOULD have had data is a real fetch failure (attempted_failed, retried by default), NOT honest
absence." The guard-rejection message text IS that exception's `str()`. This is **working exactly as designed**, not a
bug.

Re-derived the coverage classification for all 112,277 attempted_failed rows directly against the LIVE
`is_bookmaker_league_covered()` oracle (`unified_api_contracts.registry`):

```
covered vs uncovered split: 112,277 / 112,277 = 100% covered (0 uncovered)
```

**Every single row is a genuinely-covered (bookmaker, league) pair.** None of them are "never covered" cells the
2026-06-21 fix's scope should have caught — the fix's scope was correct and complete; there is no residual gap. These
rows genuinely need a real re-fetch attempt to determine whether the underlying fixture's odds data is recoverable —
that is a data-availability question, not a classification bug.

## Root code fix shipped

`market-tick-data-service@6fad6565fe66ef34ea245172dc1e606c0a2dd183`:

- Added `_attempted_at_from_row(row) -> datetime | None` to `_rebuild_sports_write.py`, mirroring the file's own
  existing `_available_at_from_row()` "honest proxy from the v8 index row" convention (prefer the row's own
  `attempted_at`, fall back to `written_at`, `None` only when neither exists — letting the writer's own
  `datetime.now(UTC)` default apply only for genuinely-missing timestamps).
- Wired it into all 3 `record_failed()`/`record_empty()` re-emit call sites that previously omitted `attempted_at=`
  entirely: `_write_empty_rows`'s CF-11 `mark_attempted_failed` branch, `_write_empty_rows`'s plain `record_empty` call,
  and `_write_attempted_failed_rows`'s re-emit call (the one responsible for this specific 112,277-row incident).
- 6 new regression tests (`test_attempted_at_from_row_*`,
  `test_write_attempted_failed_rows_preserves_original_ attempted_at`,
  `test_write_empty_rows_cf11_preserves_original_attempted_at`,
  `test_write_empty_rows_srz_preserves_original_attempted_at`), full 46-test file green, `quality-gates.sh --no-fix`
  green.
- **Prevents recurrence only** — does not retroactively fix the 112,277 rows already corrupted in the live manifest
  (they still show `attempted_at=2026-07-13` today). See the follow-up below.

## Open follow-up — restoring the true `attempted_at` on the 112,277 already-corrupted live rows

GCS object versioning is OFF on `market-data-tick-sports-prd-central-element-323112`, so the pre-rebuild content is NOT
reachable via a normal generation-scoped read. However, the bucket's **soft-delete policy (7-day retention)** DOES
retain the pre-rebuild object generation:

- **Pre-rebuild generation**: `_index/availability_index.parquet#1783986822147154`, `time_created=2026-07-13T23:53:42Z`,
  size=41,059,409 bytes. This is the LAST generation before the rebuild's write gap (next captured generation:
  `2026-07-14T00:19:26Z`, size=47,322,660 bytes — a ~26min gap + ~6.3MB/15% size jump, consistent with the rebuild's
  bulk re-emit).
- Confirmed via `google-cloud-storage` SDK `bucket.get_blob(..., generation=1783986822147154, soft_deleted=True)` that
  the METADATA is reachable — but GCS explicitly refuses to serve the object's DATA for a soft-deleted object
  (`400 Cannot request object data for soft-deleted object`) via any read path (raw REST, `gsutil`, `gcloud storage cp`
  all hit the same restriction). **The only way to recover the bytes is `gcloud storage restore`, which recreates the
  object as the new LIVE generation AT THE SAME PATH** — there is no "restore to a different path" primitive.
- **Not attempted in this session**: doing an in-place restore-then-recopy-then-restore-current-back dance on a live,
  actively-written production bucket (other agents are concurrently touching sports manifest paths this same day — see
  `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s Progress Log) risks a real consumer (the consolidator, a
  dashboard query, another agent's script) observing the WRONG (stale v8) index during the brief swap window. This is
  exactly the kind of "big, non-trivial risk under time pressure" this session's own safety instructions say to document
  rather than force.
- **Urgency**: the soft-delete retention window expires ~2026-07-20 (7 days from 2026-07-13). After that, this specific
  generation is unrecoverable by any means.
- **Recommended safe procedure for a future pass** (during a maintenance window / with the sports consolidator paused):
  1. Download the CURRENT live `_index/availability_index.parquet` as a full backup.
  2. `gcloud storage restore` the soft-deleted generation `#1783986822147154` (this makes it live again, briefly).
  3. Immediately re-upload it to a new snapshot path (`_index/snapshots/pre_v9_rebuild_2026_07_13T235342Z.parquet`) via
     UTL's storage client.
  4. Immediately re-upload step-1's backup back to `_index/availability_index.parquet` to restore current state.
  5. From the snapshot, build a `(row_key) -> original attempted_at` lookup for the 112,277 affected rows (NOTE: the
     snapshot is v8 schema, not v9 — matching requires replicating `_build_row_key`/`canonicalize_fn`'s v8→v9
     normalization, which is itself real complexity, not a trivial join).
  6. Reclassification script (dry-run default, `--apply` + snapshot-before, matching this session's established pattern)
     that restores `attempted_at` (not `capture_status`/`error_reason` — those are genuinely unresolved, see Part A/B
     above) for matched rows only; unmatched rows left untouched and logged.
- Given the code fix already prevents recurrence, and the 112,277 rows are already correctly `attempted_failed` (Part B
  confirmed this is the honest classification — they just need a real re-fetch, which is separate from this
  `attempted_at` staleness bug), this restore is a freshness-accuracy improvement for the alert detector, not a
  data-correctness emergency. Flagging as open, not resolved.

## Findings-triage classification

This is a **data-pipeline-correctness finding** (per `codex/11-project-management/` triage rules): in-repo code bug
fixed in this pass (attempted_at preservation); the historical-row restore is a separate, larger, genuinely-risky
production-data-mutation follow-up appropriately deferred rather than forced. No operator notification triggered — this
is not a cross-repo/SSOT-contradiction/kill-switch class finding, and the underlying data was already correctly
classified as `attempted_failed` (Part B), just mis-timestamped.

## CORRECTION 2026-07-20 — the soft-delete "retention cliff" was a false deadline

The closeout plan escalated this as ⏰ TIME-CRITICAL: recover the true `attempted_at` from soft-deleted generation
`_index/availability_index.parquet#1783986822147154` before it hard-deletes at 2026-07-21T00:19:26Z, via
`gcloud storage restore`. Operator approved the controlled-window restore. **Measuring before executing showed the
premise was wrong on two counts, so it was not run.**

**1. That generation is itself clobbered.** The v9 rebuild ran FOUR times, each pass re-stamping the previous stamp:

| index state                                                                                     | `attempted_at` window (BETFAIR/MATCHBOOK/PINNACLE) | verdict    |
| ----------------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------- |
| `_index/snapshots/pre_migration_v9_2026-07-12_availability_index.parquet` (07-12T22:19Z)        | 2026-06-21 14:23:10 → 22:41:51 (29,922s spread)    | ✅ TRUE    |
| `pre_migration_v9_2026-07-13_availability_index` / `pre_force_consolidate_2026-07-13T06_36_00Z` | 2026-07-12 23:17:54 → 23:18:04 (10s)               | clobber #1 |
| `pre_cf8_backfill_20260713T210725Z`                                                             | 2026-07-13 06:16:02 → 06:16:12 (10s)               | clobber #2 |
| `pre_cf8_backfill_retry_20260713T233900Z`                                                       | 2026-07-13 21:23:42 → 21:23:49 (7s)                | clobber #3 |
| LIVE `availability_index.parquet`                                                               | 2026-07-13 23:56:41 → 23:56:48 (7s)                | clobber #4 |

Generation `#1783986822147154` was created 2026-07-13T23:53:42Z — **between clobber #3 and #4**. Restoring it would have
recovered the 21:23 window: a clobbered value, mistaken for the truth.

**2. No restore is needed.** The true values survive in an ordinary LIVE object with no soft-delete and no retention
deadline: `_index/snapshots/pre_migration_v9_2026-07-12_availability_index.parquet` (112,278 triplet rows, 8.3h spread).
A plain `cp` reads it. **There is no deadline on this work.**

**3. The approved operation would also have paged.** `unified_trading_library/monitors/consolidator_liveness.py` has an
explicit `REASON_SCHEDULER_PAUSED` branch — "deterministically dead, will NOT self-recover" — evaluated by a `*/2`
watchdog wired to PagerDuty/Telegram. Pausing the `*/1` consolidator cron (the documented first step of the controlled
window) fires an ERROR-level page. Suppressing it would have meant disabling the safety net around a live 5.3M-row index
with the operator away.

**Still true / unchanged**: the schema-drift complexity flagged in step 5 above is real — the 07-12 snapshot carries 40
columns vs the live index's 41, so the `(row_key) -> attempted_at` join still needs the normalization work described,
and the restore remains a freshness-accuracy improvement rather than a data-correctness emergency. What changed is only
that it is **no longer time-boxed** and no longer requires a risky in-place soft-delete restore.

Evidence: `scratchpad/verify_preclobber.py`, `scratchpad/ladder.py` (2026-07-20).

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK** (data side; the code-fix half was already resolved). Re-queried the LIVE
`market-data-tick-sports-prd-central-element-323112` / `_index/availability_index.parquet` directly (563,384 total rows
today, down from the pre-wipe 1,830,258):

- `source == "api_football"` rows: **0** (was 1,266,874 before the 2026-07-23 wipe).
- `error_reason == "VENUE_FETCH_FAILED"` rows: **0** (was 94,127 — this doc's Part A population).
- The `SOURCE_RETURNED_ZERO`-guard message rows (this doc's Part B, 18,150-row slice) are also **gone**: the current
  21,920 `SOURCE_RETURNED_ZERO` rows are ALL `capture_status=empty_confirmed` (not `attempted_failed`) and their
  `source` breakdown is `polymarket_clob=20,785 / mdps_odds_horizon_bucket=652 / footystats=449 / odds_api=34` — zero
  `api_football`. `data_type=trades` overall now shows only `captured=374,578` / `empty_confirmed=20,803` /
  `attempted_failed=0`.

This confirms the task brief's expectation precisely: the entire 112,277-row `attempted_failed` population this doc
diagnosed (both the VENUE_FETCH_FAILED slice and the EmptyFromLiveInstrumentError-guard slice) was removed as a side
effect of `market-tick-data-service@e9d9dec0` (2026-07-23 CAS-safe wipe of all `source=api_football` MTDS-sports
manifest rows, filed under `mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`) — every
affected row was `pipeline_mode=batch_api_football`/`source=api_football`, exactly the wipe's scope. The root-cause
analysis in Parts A/B above remains historically accurate (it correctly explained why the population looked artificially
fresh, and the prevention fix `mtds@6fad6565` is still valid/shipped), but the specific "restore true `attempted_at` on
the 112,277 already-corrupted rows" open follow-up is now moot — there is no longer any live row to restore a timestamp
on. Flipped `status: resolved` and added the wipe SHA to `resolved_by`.
