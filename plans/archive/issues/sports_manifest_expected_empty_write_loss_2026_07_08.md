---
doc_type: issue
title: Sports manifest guards silently discarded record_expected_empty() writes (4 fetchers, 10 call sites) — FIXED
summary: |
  Four per-date sports fetchers' early-return guards (coverage-start/known-gap and off-season season-window) called
  record_expected_empty() to stage manifest rows but returned before calling .write(), silently discarding the
  classification. Discovered while driving the understat backfill-completion plan to done. Fixed in this session.
status: resolved
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags:
  [
    manifest,
    capture-status,
    honest-absence,
    sports,
    data-correctness,
    silent-write-loss,
    understat,
    footystats,
    weather,
  ]
related:
  [
    plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md,
    plans/active/issues/understat_bulk_download_backfill_2026_06_29.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-08
parent_epic: infrastructure_master
priority: P1
source: understat_local_backfill_completion_2026_07_06.md task -001, slot-7 data_engineering
assigned_vm: planning
resolved_by: slot-7 (this session) — instruments-service@<pending-commit>
locked_by: live-defi-rollout
audited_scope: data-correctness
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
locked_since: 2026-05-21
---

# Sports manifest guards silently discarded record_expected_empty() writes — FIXED 2026-07-08

## What I found

While running the understat XG/XG_SHOTS backfill driver
(`instruments-service/scripts/backfill/understat_bulk_backfill.py`) to completion for task -001 of
`plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md`, the driver's self-healing retry loop
converged from 20 → 4 remaining `attempted_failed` big-5 XG_SHOTS dates and then got permanently stuck at 4
(`2020-06-24`, `2020-07-02`, `2020-07-03`, `2020-07-24`), hitting `MAX ROUNDS reached` on every run.

The log showed the SAME 4 dates being correctly re-classified as "all expected leagues off-season" on **every** retry
round (6 rounds observed), yet the manifest never updated — `attempted_at` stayed pinned at the stale `2026-06-23`
timestamp from a prior era.

Root cause, confirmed by reading `instruments_service/engine/orchestrator/understat.py`: both early-return guards
(coverage-start/known-gap at the top of each fetcher, and the season-window off-season guard right after it) call
`manifest.record_expected_empty(...)` in a loop — which only **stages** rows in the `ManifestWriter` instance — and then
`return counts` **without ever calling `.write()`**. The `ManifestWriter` object is local to the function call, so on
return the staged rows are silently discarded and never reach GCS. Every other code path in the same functions (the
success path, the no-fixtures path, the exception path) DOES call `.write()` before returning — only these two
early-return guards were missing it.

**This is NOT limited to understat.** The identical guard pattern (`"all expected leagues off-season"` +
`record_expected_empty` loop + early `return`) is copy-pasted across 4 sports fetchers in the same directory. Grep
confirmed the guard text exists in `understat.py`, `footystats.py`, `weather.py`, and `sfi.py`; reading each function
showed:

- `understat.py` — `_fetch_understat_xg` (both guards) + `_run_understat_shots_date` (both guards): **bug present**, 4
  call sites.
- `footystats.py` — `_fetch_footystats_predictions` (both guards) + `_fetch_footystats_matches` (both guards): **bug
  present**, 4 call sites.
- `weather.py` — `_fetch_weather_data` (both guards): **bug present**, 2 call sites.
- `sfi.py` — the off-season guard does NOT early-return; it flips a local flag and falls through to a later
  unconditional `manifest.write()` shared with the rest of the function. **Not affected** (correct pattern already).

Total: **10 call sites across 3 files** silently dropped their computed off-season / pre-coverage-start / known-gap
classification every time they fired against a date that already carried a stale `attempted_failed` or
`attempted_failed`-adjacent row — meaning any date that ever transiently failed and later fell into one of these guard
branches could **never self-heal**, regardless of how many backfill/retry passes ran against it.

## Why it matters

Per `codex/02-data/availability-manifest-and-data-status.md`, `capture_status` is a 4-state ledger and the
honest-coverage denominator (`captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`) is
read directly by downstream consumers (data-status UI, strategy/features pre-flight) — they never re-derive it. A cell
stuck at `attempted_failed` forever (when the correct state is a typed `empty_confirmed`/`expected_unattempted`
off-season/pre-coverage marker) permanently corrupts that denominator for the affected date/league/data_type, and blocks
any self-healing retry loop (like the understat bulk driver, or any future backfill) from ever converging to "0
attempted_failed" for genuinely-resolved dates — the loop keeps re-attempting forever since nothing ever gets written to
break out of the stale state.

This directly blocked `understat_local_backfill_completion_2026_07_06.md` task -001's own completion signal
(`ALL DATES CAPTURED (0 attempted_failed)`) — the 4 stuck understat dates could never converge without this fix, since
the correct classification was being computed and thrown away every single retry round.

## Fix applied (this session, instruments-service)

Added the missing `.write()` call (matching the existing pattern used elsewhere in each same function) immediately after
each `record_expected_empty()` loop, before the early `return`:

- `instruments_service/engine/orchestrator/understat.py`: `_fetch_understat_xg` (2 sites), `_run_understat_shots_date`
  (2 sites).
- `instruments_service/engine/orchestrator/footystats.py`: `_fetch_footystats_predictions` (2 sites),
  `_fetch_footystats_matches` (2 sites).
- `instruments_service/engine/orchestrator/weather.py`: `_fetch_weather_data` (2 sites).

Added regression coverage: `mock_mw.write.assert_called_once()` added to the existing pre-cutoff/known-gap and
off-season unit tests for all 5 affected functions in `tests/unit/test_orchestrator_data_fetchers.py` (10 assertions
total) — the existing tests only asserted `record_expected_empty.assert_called()`, which is exactly why the missing
`.write()` shipped unnoticed. `sfi.py`'s equivalent test was left unchanged since that fetcher's guard does not
early-return.

**No fix needed elsewhere** — `sfi.py`'s off-season guard already falls through to a shared unconditional
`manifest.write()` later in the function.

## Recommended decision

No further action needed on the code fix — already shipped this session (see commit SHA in the understat plan's Progress
Log). The fix only affects **future** invocations; pre-existing stale `attempted_failed` rows for OTHER sports data
types (footystats PREDICTIONS/MATCHES, weather) that hit this exact same bug in the past will only self-correct the next
time a capture process re-attempts those specific (date, league, data_type) cells with `force=True` or via a fresh
non-skip pass — no backfill audit for footystats/weather was in scope for this session and none is proposed here;
flagging so a future footystats/weather data-freshness audit knows this historical write-loss class exists and isn't
itself a NEW regression if found.
