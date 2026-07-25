---
doc_type: issue
title:
  "api_football per-fixture adapters (FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS) swallow hard fetch
  failures internally, so the orchestrator's entity_failures shard-failure-isolation tracking never fires — a hard
  failure (e.g. API-Football daily-quota exhaustion) gets silently recorded as empty_confirmed/EXPECTED_NO_FIXTURE
  instead of attempted_failed, live-confirmed corrupting the currently-running fixture_events re-fetch VM"
summary: >-
  While health-checking af-backfill-20260725-032253 (the OR-1 fixture_events canonical re-fetch VM,
  sports_satellite_ao_dispatch_batch2-011 / issues/sports_fixture_events_refetch_progress_2026_07_25.md), its
  API-Football key hit the DAILY request-limit at 2026-07-25T08:12:00Z (`{'requests': 'You have reached the request
  limit for the day...'}`, HTTP 200 JSON-envelope, error_code classified UNKNOWN since it isn't
  "rateLimit"/429/401/403). Traced the code path: all 4 per-fixture adapter methods in `api_football.py`
  (get_fixture_statistics/get_fixture_events/get_fixture_lineups/get_fixture_player_stats) wrap their fetch in their OWN
  `try/except Exception: self._emit_fetch_failed(...); return []` — so a hard (non-rate-limit) failure NEVER propagates
  as an exception to `_gather_per_fixture_rows._fetch_one`'s own try/except in `sports_reference_fixtures.py`, which is
  the ONLY place that increments `entity_failures`. Because `entity_failures` stays `(0, "")`,
  `_handle_empty_fixture_entity` takes the "all calls succeeded but returned zero rows — legitimate empty" branch and
  calls `hooks.emit_empty_gaps_for_entity(...)`, which stamps every affected league
  `EXPECTED_NO_FIXTURE`/`EXPECTED_NO_PROVIDER_COVERAGE` (empty_confirmed) — a state that reads as "nothing to capture,
  done" rather than "fetch failed, needs retry". This is the exact honest-absence violation CLAUDE.md's
  data-pipeline-correctness rule prohibits ("a genuine 200+empty and a 401/403/429/5xx/timeout are DIFFERENT states —
  never stamp a failure as zero"), and it directly undermines this task's own OR-1 fixture_events canonical-schema
  re-fetch campaign: dates processed by the VM from 08:12Z onward risk being marked done/empty when they were never
  actually fetched.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags:
  [
    sports,
    api-football,
    fixture-events,
    honest-absence,
    silent-placeholder,
    shard-level-failure-isolation,
    data-correctness,
    live-incident,
  ]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md,
  ]
created: 2026-07-25
priority: P0
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["sports_satellite_ao_dispatch_batch2-011 health-check, slot 7, data_engineering, 2026-07-25T08:34Z"]
drift_direction: advance-code
---

# api_football per-fixture hard failures silently recorded as empty — live incident + root cause

## What I found

**Live trigger (2026-07-25T08:12:00Z):** `af-backfill-20260725-032253`'s API-Football key hit its DAILY request quota
mid-run (`date=2020-03-18`+, 447+ of ~2500 dates in). `run.log`
(gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260725-032253/run.log`) shows the JSON-envelope error `{'errors':
{'requests': 'You have reached the request limit for the day, Go to https://dashboard.api-football.com to upgrade your
plan.'}}`repeating **8,534 times** between 08:12:00Z and 08:34Z (22 min), one per failed per-fixture call, zero successful`Fetched
N events for fixture=X`lines in that window (confirmed via`grep
-c`on the tail of the log after the first occurrence). The`date=`boundary is stuck (still`2020-03-22`as of the last read) — **not a slow-progress case, a hard zero-forward-progress stall**, but the VM stays`RUNNING`
and heartbeats fresh, so a naive activity-only health-check (log growing, heartbeat fresh) would misreport it as
healthy.

**Root cause (code-traced, not speculative):** `error_code` for this error classifies to `UNKNOWN` (`_classify_error`
only matches `401`/`429`/`rate`/`timeout`/`403`/`404` substrings; `"requests"` and `"the day"` match none of them). In
`_extract_response` (`api_football.py:1010-1024`), `is_rate_limit = "rateLimit" in errors` — the daily-quota error's key
is `"requests"`, not `"rateLimit"`, so `is_rate_limit=False`. Per `_fetch_and_extract`'s own docstring this is meant to
be a **hard error that bubbles up immediately** (as opposed to the per-minute `rateLimit` JSON envelope, which retries
with a minute-boundary sleep). It does bubble up — but only as far as each of the 4 per-fixture methods' OWN try/except:

```python
# api_football.py:901-905 (get_fixture_events; get_fixture_statistics/get_fixture_lineups/
# get_fixture_player_stats share the identical shape at lines ~874-876 / ~918-937(lineups) / ~947-962)
try:
    raw_rows = await self._fetch_and_extract(url, params)
except Exception as exc:
    self._emit_fetch_failed(self._classify_error(exc), exc)
    return []
```

This swallows EVERY exception — including genuine hard failures — and returns `[]`. The caller,
`sports_reference_fixtures.py::_gather_per_fixture_rows._fetch_one` (line ~470-495), only increments
`entity_failures[entity_name]` inside ITS OWN `except Exception` block wrapping `await fetch_fn(fid)` — but since the
adapter method never lets the exception reach `_fetch_one`, `rows = []` looks like a completely normal, successful
zero-row response. `entity_failures` for `fixture_stats`/`fixture_events`/`fixture_lineups`/`player_stats` therefore
**never reflects a real failure**, no matter how many fixtures actually failed.

Downstream, `_write_per_fixture_entities` → `_handle_empty_fixture_entity` (`sports_reference_fixtures.py:788-856`)
branches on `entity_failures.get(entity_name, (0, ""))`. Because that's always `(0, "")` for this failure class, it
takes the **`else` branch** ("All calls succeeded but returned zero rows... — legitimate empty") and calls
`hooks.emit_empty_gaps_for_entity(...)` → `sports_reference_core.py::_emit_empty_gap_for_league` → stamps
`EXPECTED_NO_FIXTURE`/`EXPECTED_NO_PROVIDER_COVERAGE` (`empty_confirmed`) for every affected league on that date. This
is a **terminal-looking honest state** — it reads as "checked, genuinely nothing there," not "fetch failed, needs retry"
— so a future re-fetch pass (including THIS todo's own re-census-and-verify step) will not know to retry these cells.

**Blast radius, live and historical:**

- **Live**: every date the VM processes from 08:12Z onward (currently ~2053 of ~2500 dates remaining, unknown how long
  until the API-Football daily quota resets) risks having its `fixture_stats`/`fixture_events`/`fixture_lineups`/
  `player_stats` entities silently recorded `empty_confirmed` instead of genuinely re-fetched — directly defeating this
  campaign's own goal (0 non-canonical objects, honestly).
- **Historical**: this is a code-path bug, not a one-off — any PAST api_football per-fixture run that hit a hard failure
  (daily quota, `INVALID_API_KEY`, `FORBIDDEN`, a malformed-params error, etc., i.e. anything that isn't the `rateLimit`
  JSON envelope or an HTTP 429) on these 4 entities is equally exposed. The
  `api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` doc already found ~3,116 undocumented
  `attempted_failed` rows across INJURIES/FIXTURES/PLAYER_STATS/TEAMS from a DIFFERENT angle (rows that DID get
  correctly marked failed) — this bug describes the complementary, worse failure mode: rows that should have been
  `attempted_failed` but got silently marked `empty_confirmed` instead, so they wouldn't even show up in that reverify's
  `attempted_failed` count. Scale unknown — needs its own audit (todo 2 below), separate from this fix.

## Why it matters

This is the honest-absence hard rule (`/codex/02-data/honest-absence-downstream-handling.md`): a genuine 200+empty and a
fetch failure are different states, and conflating them here means real data silently becomes permanently-unretriable
"confirmed empty" gaps. It is currently active and live — not a historical residue — on the exact VM this plan's own
todo (`sports_satellite_ao_dispatch_batch2-011`) is tracking to completion.

## Recommended decision

1. **[OPS] P0 — VM disposition (operator/main call, not mine to make unilaterally):** `af-backfill-20260725-032253` has
   been in the zero-progress daily-quota-exhausted state since 08:12Z with no sign of self-resolving (unlike the
   per-minute `rateLimit` case, there's no in-adapter retry/backoff for this error class — it will keep silently
   `empty_confirmed`-ing every remaining date until either the daily quota resets or someone stops it). Recommend:
   **stop the VM now** (SPOT, idempotent — safe to stop/relaunch) to cap further silent corruption, rather than letting
   it grind through the remaining ~2053 dates in this broken state. Relaunch once todo 3 (adapter fix) ships AND the
   API-Football daily quota has reset (unknown reset time — check `https://dashboard.api-football.com` account status or
   retry a lightweight `/status` call).
2. **[CODE] P0. Fix the 4 per-fixture adapter methods** (`get_fixture_statistics`, `get_fixture_events`,
   `get_fixture_lineups`, `get_fixture_player_stats` in
   `instruments_service/reference_data/adapters/sports/adapters/api_football.py`) so a HARD failure (anything that
   reaches their `except Exception` after `_fetch_and_extract` — i.e. `is_rate_limit=False` cases, already re-raised
   immediately by `_fetch_and_extract`) re-raises to the caller instead of swallowing to `[]`, restoring the shard-level
   failure-isolation contract `_gather_per_fixture_rows._fetch_one` / `entity_failures` / `_handle_empty_fixture_entity`
   already assumes exists. Keep `_emit_fetch_failed` (observability) but do not `return []` after it for this class —
   either re-raise or return a distinguishable sentinel `_fetch_one` treats as a forced entity_failures increment. Add
   regression tests: one hard-failure-class error (e.g. mock the "requests" daily quota JSON envelope) must result in
   `entity_failures[entity]` incrementing and `_handle_empty_fixture_entity` taking the `record_failed` branch, not the
   empty-gap branch. (repo: instruments-service)
3. **[DATA] P1. Historical audit** — once the fix ships, scope a census (manifest, not a new GCS walk) for
   `capture_status=empty_confirmed` / `EXPECTED_NO_FIXTURE` / `EXPECTED_NO_PROVIDER_COVERAGE` rows on
   `FIXTURE_STATS`/`FIXTURE_EVENTS`/`FIXTURE_LINEUPS`/`PLAYER_STATS` whose `attempted_at` falls inside a window
   correlatable to a known api_football hard-failure event (cross-reference `ADAPTER_FETCH_FAILED` log/event history if
   retained, or re-probe a sample against the live API to see if data actually exists there now) — re-flag genuine false
   positives to `attempted_failed` for re-fetch. Likely overlaps/extends
   `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`'s scope; coordinate rather than
   duplicate. (repo: instruments-service)
4. **[DATA] P1. Re-verify `af-backfill-20260725-032253`'s own output** once it's stopped/resumed/completed: any date
   processed in the 08:12Z-onward window before the stop must be excluded from "done" until re-fetched under the fixed
   adapter — do not let the OR-1 re-census (this plan's own "Done when" step) trust `empty_confirmed` cells from that
   window at face value.

## Codex SSOTs

`/codex/02-data/honest-absence-downstream-handling.md` (the rule this violates),
`/codex/04-architecture/shard-level-failure-isolation.md` (the contract `entity_failures` is supposed to implement).
