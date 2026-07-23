---
doc_type: issue
title:
  "sports T0→T1 adapter dependency gate (check_api_football_dependency) is fully built, tested, and documented, but
  NEVER actually invoked in production — every real T1 call site omits the date= param needed to trigger it"
summary:
  "While investigating whether api-football's this-session fixture backfill should trigger a re-run of dependent T1
  sources (footystats/understat/transfermarkt/soccer_football_info/open_meteo/betfair), found that
  instruments_service/reference_data/sports_dependency.py::check_api_football_dependency() — the documented,
  SSOT-referenced fail-loud DependencyError gate meant to enforce T0-before-T1 ordering — is never actually triggered.
  create_sports_reference_adapter() only calls the check `if date is not None`, and every real production call site
  (footystats.py x3, transfermarkt.py, understat.py, sfi.py) omits the date= argument entirely. Empirically confirmed
  via live data: understat has 4,273 genuinely `captured` rows for 2014-01-01..2017-12-31 — a period where api-football
  has categorically ZERO fixtures (its documented pre-2018 subscription-floor dead zone) — which would be impossible if
  the gate were actually enforced. The dependency IS real in the data sense (T1 adapters do read api-football's
  canonical fixture IDs for joining), but the fail-loud SAFETY NET around it has silently never fired since it was
  built."
status: open
priority: P2
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, dependency-order, dead-code, api-football, fixtures, data-correctness, architecture]
related:
  [
    ../sports_data_sources_canonical_completion_2026_07_13.md,
    /plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md,
  ]
created: 2026-07-15
parent_epic: infrastructure_master
source:
  "Interactive session 2026-07-15, investigating operator question: does api-football's this-session fixture backfill
  require re-running dependent T1 sources?"
locked_by:
resolved_by:
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: NA
depends_on: []
---

## What I found

`instruments_service/reference_data/sports_dependency.py::check_api_football_dependency()` raises a fail-loud
`DependencyError` (from UTL) if none of api-football's canonical fixture markers exist for a date. It's wired into
`create_sports_reference_adapter()` (`factory.py:89-90`):

```python
if date is not None and venue_requires_api_football(venue_lower):
    check_api_football_dependency(date=date, bucket=bucket)
```

**The check only fires when `date` is passed to the factory call.** Grepped every real call site of
`create_sports_reference_adapter()` in the whole repo:

| call site                                             | venue                | passes `date=`?                         |
| ----------------------------------------------------- | -------------------- | --------------------------------------- |
| `footystats.py:66`                                    | footystats           | **NO**                                  |
| `footystats.py:488`                                   | footystats           | **NO**                                  |
| `footystats.py:885`                                   | footystats           | **NO**                                  |
| `transfermarkt.py:369`                                | transfermarkt        | **NO**                                  |
| `understat.py:49`                                     | understat            | **NO**                                  |
| `sfi.py:119`                                          | soccer_football_info | **NO**                                  |
| `sports_reference.py:100`                             | api_football         | N/A (not gated — not a dependent venue) |
| `sports_reference_fixtures.py:140`                    | api_football         | N/A                                     |
| `adapters/sports/__init__.py:15,20`                   | api_football         | N/A                                     |
| `triggers/sports_fixtures_daily_repoll.py:280`        | api_football         | N/A                                     |
| `scripts/backfill_teams_61_leagues_2026_07_13.py:117` | api_football         | N/A                                     |

**Every single T1-venue call site omits `date=`.** The gate has never fired in production, for any of the 5 dependent
adapters, at any point since it was built.

**Independently confirmed via live data** (not just static code reading): `understat` has **4,273 genuinely `captured`
rows for `2014-01-01..2017-12-31`** — a 4-year window where api-football has categorically ZERO fixtures (its documented
`SOURCE_COVERAGE_START["api_football"] = 2018-01-01` subscription-floor dead zone, per
`unified-api-contracts/.../league_data.py:76`). If the gate were actually enforced, EVERY understat fetch attempt in
this window would raise `DependencyError` before ever reaching the adapter. It doesn't — understat has been happily
capturing real data there the whole time.

## Why this happened (a plausible read, not confirmed)

The gate's own docstring describes it as making an already-existing, previously-silent dependency "explicit" — i.e. it
was added as an observability/safety improvement on TOP of adapters that already worked without it (each T1 adapter has
its own internal logic for looking up fixture IDs, which degrades gracefully — e.g. returns empty/partial results —
rather than crashing when fixtures are absent). It's plausible the gate was built and unit-tested in isolation but the
follow-up work of actually threading `date` through every call site into the factory was never done, and nothing since
has caught the gap (the gate fails SAFE — a missing wire-up means adapters just run unguarded, not that they crash
unexpectedly).

## Why it matters (and why it's P2, not P1)

- **Not currently a data-correctness bug**: since each T1 adapter's own internal logic degrades gracefully without
  api-football's fixtures (confirmed by understat's own healthy pre-2018 data), there's no evidence T1 sources are
  silently producing wrong/incomplete data because of this gap.
- **It IS a genuine gap in the safety net**: if a future date-range regression genuinely wipes out api-football's
  fixtures for some window, the T1 adapters would NOT fail loud with an actionable "run api-football first" message —
  they'd just quietly produce whatever degraded output their own internal fixture-lookup logic falls back to, which is
  exactly the "historically silent" failure mode the gate's own docstring says it was built to eliminate.
- **Directly relevant to this session's api-football backfill work**: no, T1 sources do NOT need re-running as a
  consequence of api-football's `attempted_failed` reduction (4,138→766) or the FIXTURES purge (612 rows) — since the
  gate never blocked them in the first place, none of their own captures were EVER contingent on api-football's gaps.
  Their current near-zero `attempted_failed` counts (footystats 4, soccer_football_info 0, transfermarkt 0,
  open_meteo 0) reflect their own independent fetch success/failure, not something waiting on api-football.

## Recommended decision + todo

- [ ] [SCRIPT] P2. **Thread `date` through every T1 call site of `create_sports_reference_adapter()`** (`footystats.py`
      x3, `transfermarkt.py`, `understat.py`, `sfi.py`) so the existing, already-tested `DependencyError` gate actually
      fires as designed. This is a pure wiring fix — no change to `sports_dependency.py` itself. Verify post-fix that it
      does NOT retroactively break understat's pre-2018 captures (expected: it won't, since those captures already
      succeeded and are cached/complete — the gate only affects NEW fetch attempts going forward for genuinely-missing
      dates). (repo: instruments-service)

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE.** Re-grepped every real call site of `create_sports_reference_adapter()` in
`instruments-service` today: `footystats.py:66,483,875`, `transfermarkt.py:369`, `understat.py:49`, `sfi.py:119` all
still call it with only `venue`/`api_key` positional args — none pass `date=`. Confirmed the factory signature
(`instruments_service/reference_data/adapters/sports/factory.py::create_sports_reference_adapter`) still has
`date: str | None = None` as an optional kwarg, and the gate in `factory.py` still only fires `if date is not None`. The
wiring fix described in the one open todo above has not been applied — the fail-loud `DependencyError` safety net still
never triggers for any T1 adapter. No status change.
