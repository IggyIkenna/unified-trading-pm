---
doc_type: issue
title:
  SportsTriggerScheduler's fixture-lookback window (~2h post-kickoff) structurally prevents any post-match trigger with
  an offset beyond ~2h from ever firing — `stats_delayed` (XG/Understat) and `features_post_match` (derived post-match
  features) have never fired live
summary: >-
  While working the `source_data_latency.py` re-pin todo (sports batch3), the empirical latency-observation data showed
  0 observations ever recorded for Understat/XG despite the live `stats_delayed` trigger (offset_hours=24) existing in
  `configs/sports-trigger-tiers.yaml` since 2026-06-22 and 13 days of continuous scheduler uptime. Root-caused to
  `deployment_service/sports_trigger_state.py::get_upcoming_fixtures()` (`sports_trigger_state.py:44-176`): its
  fixture-inclusion filter is `-2 <= hours_until <= horizon_hours` (a fixture is only visible from 2h before kickoff to
  `horizon_hours` — default 48h — after kickoff). A post-match trigger with `total_offset_minutes` (from `match_end =
  kickoff + 105min`) large enough to push its fire window past `kickoff + 2h` can therefore NEVER see its own target
  fixture in the `fixtures` list by the time it's due to fire — the fixture has already aged out of the lookback.
  `stats_immediate` (offset_minutes=30 → fire window ≈ kickoff+1.75h..+2.75h) barely survives because part of its ±30min
  tolerance window overlaps the `<=2h` cutoff (confirmed empirically: 2504 real `stats_immediate` observations exist).
  `stats_delayed` (offset_hours=24 → fire window ≈ kickoff+25.25h..+26.25h) and `features_post_match` (offset_hours=25,
  `depends_on: stats_delayed`) have ZERO overlap with the `<=2h` cutoff — they are unconditionally dead code paths under
  the current fixture-lookback design, for every fixture, always. This is NOT specific to the latency-observation
  instrumentation: `stats_delayed` is the trigger that dispatches the REAL Understat/FootyStats XG capture and
  `features_post_match` computes REAL derived post-match features (`features-service-sports-job --tables
  derived_features`) — if this bug is confirmed to be live-impacting (see Open questions), sports XG/advanced-stats and
  derived post-match features may never be computed via the live scheduler path at all, only via manual/batch backfill.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [deployment-service]
scope: [engineer]
tags: [sports, scheduler, post-match-trigger, data-completeness, bug, live-pipeline]
related:
  [
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
  ]
created: 2026-07-27
priority: P0
parent_epic: sports_master
source:
  "worker, slot 15, hit while running instruments-service/scripts/aggregate_source_latency_observations.py against prod
  for the source_data_latency.py re-pin todo (sports_satellite_ao_dispatch_batch3_2026_07_25.md item 3) — 0/2504
  observations were understat/sfi, all 2504 were api_football/stats_immediate; traced to the fixture-lookback code, not
  a latency-recorder bug"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# SportsTriggerScheduler post-match fixture-lookback bug

## What I found

Running `instruments-service/scripts/aggregate_source_latency_observations.py --emit-constants` (and
`--first-success-only`) against
`gs://instruments-store-sports-prd-central-element-323112/_index/latency_observations/day=*/*.parquet` (552 parquet
files, 2026-07-14..2026-07-27, ~13 days of live accrual since the 2026-06-24 scheduler-tarball rebuild):

| source       | trigger_name                          | n     | first_success=True | verdict                       |
| ------------ | ------------------------------------- | ----- | ------------------ | ----------------------------- |
| api_football | stats_immediate                       | 2504  | 0                  | has samples (ceiling-only)    |
| understat    | stats_delayed                         | **0** | —                  | **never fires**               |
| sfi          | (none configured)                     | 0     | —                  | no live trigger wiring at all |
| footystats   | (not in ENTITY_TO_OBSERVATION_TARGET) | 0     | —                  | never instrumented            |
| open_meteo   | (not in ENTITY_TO_OBSERVATION_TARGET) | 0     | —                  | never instrumented            |

The sfi/footystats/open_meteo zeros have their own, separate, lower-severity causes (no trigger config entry for
SFI_PROGRESSIVE_STATS; footystats/open_meteo simply absent from `ENTITY_TO_OBSERVATION_TARGET`). This doc is about the
**understat/`stats_delayed` zero**, because that trigger genuinely IS configured and SHOULD be firing — and because
tracing it surfaced a scheduler-wide structural bug, not a latency-recorder-specific one.

### Root cause

`deployment_service/sports_trigger_state.py::get_upcoming_fixtures()` (`sports_trigger_state.py:44-176`) scans
`_fixture_path_patterns` for `day_offset in range(4)` — i.e. **today through today+3** — and then filters each fixture
row by:

```python
hours_until = (kickoff - now).total_seconds() / 3600
if -2 <= hours_until <= horizon_hours:   # horizon_hours defaults to 48
    ...include fixture...
```

A fixture is visible to the scheduler only from 2 hours before its kickoff to `horizon_hours` after kickoff — i.e. the
window CLOSES at `kickoff + 2h`. It never re-opens (no day-in-the-past scan, no separate "recently completed" query).

`deployment_service/sports_trigger_scheduler.py::evaluate_post_match_triggers()` (`sports_trigger_scheduler.py:265-320`)
computes each post-match trigger's fire window from the SAME fixture list:

```python
match_end = kickoff + timedelta(minutes=MATCH_END_OFFSET_MIN)   # MATCH_END_OFFSET_MIN = 105
fire_at = match_end + timedelta(minutes=total_offset_minutes)
delta_minutes = abs((now - fire_at).total_seconds()) / 60
if delta_minutes <= 30:   # fires
```

Per `configs/sports-trigger-tiers.yaml`:

- `stats_immediate`: `offset_minutes: 30` → `fire_at = kickoff + 135min` (2.25h) → fire window
  `[kickoff+1.75h, kickoff+2.75h]`. This OVERLAPS the fixture-visibility cutoff (`kickoff+2h`) in the
  `[kickoff+1.75h, kickoff+2h]` slice (15 min). With a 5-min poll interval that's usually ≥1 tick inside the overlap —
  hence real observations exist (2504 of them), though the design is fragile (a slow/late poll tick could miss the
  15-min window entirely for a given fixture).
- `stats_delayed`: `offset_hours: 24` → `fire_at = kickoff + 105min + 24h ≈ kickoff+25.75h` → fire window
  `[kickoff+25.25h, kickoff+26.25h]`. **Zero overlap** with the `≤kickoff+2h` visibility cutoff — the fixture has
  already aged out of `get_upcoming_fixtures()`'s result by ~23 hours before this trigger could ever become due. This
  trigger can never fire for ANY fixture under the current code.
- `features_post_match`: `offset_hours: 25`, `depends_on: stats_delayed` — same problem, one hour further out.

### Why it matters

`stats_delayed` isn't only the latency-observation trigger — its `services` block is a REAL dispatch of
`instruments-service --sports-entity XG` (Understat/FootyStats advanced-stats capture), and `features_post_match` is a
REAL dispatch of `features-service-sports-job --tables derived_features`. If this bug has been live since these triggers
were added (need to confirm the git-blame date on `sports-trigger-tiers.yaml`'s `post_match` section — NOT investigated
as part of this todo, out of scope for the re-pin task), sports post-match XG/advanced-stats and derived-features data
may have NEVER been captured via the live scheduler path — only via manual/batch backfill runs, if any. This is a
potential live-pipeline data-completeness gap, hence P0.

## Open questions (NOT investigated — out of scope for the re-pin todo that surfaced this)

1. Is `stats_delayed`'s real (non-latency) dispatch — the actual XG/Understat instruments-service fetch — also silently
   never firing, or is there a SEPARATE catch-up path (e.g. a periodic backfill VM, a Tier-2 reference sweep) that
   captures this data through a different mechanism? The manifest would show this directly (compare `capture_status`
   counts for `data_type=XG` against `FIXTURE_STATS` over the same fixture population).
2. When was `stats_delayed`/`features_post_match` added to `sports-trigger-tiers.yaml` relative to when the scheduler VM
   was last relaunched? (Determines how long this has been silently dead, if it's confirmed dead per Q1.)
3. Is the intended fix (a) widen `get_upcoming_fixtures()`'s lookback to cover the largest configured post-match offset
   (currently 25h → need ≥26h lookback), (b) add a SEPARATE "recently-completed fixtures" query path for post-match
   triggers only (keeps the pre-match/discovery horizon tight while giving post-match room), or (c) something else? This
   is a design decision, not mechanical — needs its own scoped todo/plan, not a blind fix.

## Recommended decision

File a dedicated fix plan (`assigned_vm: planning`, scoped to deployment-service) once Q1/Q2 above are answered — the
fix itself (likely (b): a day-range-aware lookback specifically for `evaluate_post_match_triggers`, since widening the
shared `horizon_hours` window would also inflate pre-match/discovery scan cost) should NOT be done as a rider on the
source-latency re-pin todo that discovered it (different repo focus, different testing surface, scoped fix vs.
mechanical constant re-pin).

## Todos

- [ ] [DATA] P0. Answer Open Question 1 above: query the live sports manifest
      (`market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`) for
      `data_type=XG`/`entity=derived_features` capture_status counts over the last 30 days and compare against
      `FIXTURE_STATS` counts for the same fixture population, to determine whether Understat/derived-features capture is
      ALSO silently dead (not just the latency-observation instrumentation) or is reaching GCS through a separate path.
      Repo: instruments-service / market-tick-data-service (read-only). **Done when**: a clear confirmed/refuted verdict
      is recorded in this doc with the counts cited.
- [ ] [INFRA] P0. If Q1 confirms live capture is dead: design + ship a fix to
      `deployment_service/sports_trigger_state.py::get_upcoming_fixtures()` / `evaluate_post_match_triggers()` so
      post-match triggers with an offset beyond the current ~2h fixture-visibility cutoff can actually fire (see
      "Recommended decision" above for the design options) — with a regression test proving a synthetic 25h-offset
      trigger now fires for a fixture whose kickoff was >24h in the past. Repo: deployment-service. **Done when**: the
      fix ships, the regression test passes, and a live re-verification (next `stats_delayed` cycle after deploy) shows
      a fresh `data_type=XG` capture or a fresh `_index/latency_observations` row with `trigger_name=stats_delayed`.
