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

## Investigation: Open Question 1 — RESOLVED (2026-07-27, slot-8, data_engineering)

**Verdict: CONFIRMED — Understat/XG live capture is dead (zero live-tagged captures, ever). `features_post_match`
(derived_features) is also not being served by the live trigger; the data that does exist comes from a lagging batch
path, not the ~25-26h live window.**

Queried the consolidated availability manifests directly (`read_availability_index()`, no whole-corpus GCS walk),
slim/column-pushdown reads with explicit `filters=` (the full-schema path silently ignores `filters` — confirmed via
source read of `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py`, so every query below
passed `columns=` to keep pushdown active).

**IS manifest** (`instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`):

- `data_type=XG`, last 30 days (2026-06-27..2026-07-27): **11,895 / 11,895 rows = `empty_confirmed`; 0 `captured`.**
- `data_type=XG`, all-time (350,482 rows): 7,714 rows ever `captured` — but **100% of those carry
  `pipeline_mode=batch_understat`**, and every single one's `written_at` falls inside a narrow 2026-07-13T23:48Z ..
  2026-07-22T05:23Z window (a one-shot historical backfill run), backfilling old match `date`s (2020, 2023, …) — not
  live/recent fixtures. Zero rows show any live-pipeline provenance. This is the strongest possible confirmation: not
  one XG capture, ever, in this manifest's history, came from anything other than that one batch backfill job.
- `data_type=FIXTURE_STATS` (context/control — the sibling trigger `stats_immediate` DOES have 2,504 real
  `latency_observations` rows per the parent doc): last-30-days = 72 `captured` / 690 `expected_unattempted` / 11,137
  `empty_confirmed`; all-time captured rows (42,735) are also **100% `pipeline_mode=batch_api_football`**. So even the
  trigger empirically known to fire live shows no live-tagged rows in the PRIMARY availability manifest — the live
  success signal for `stats_immediate` lives only in the separate `_index/latency_observations/` instrumentation, never
  in this manifest's `pipeline_mode`/`capture_status`. Noted as a manifest-labeling nuance, not load-bearing for the XG
  verdict above (XG has literally 0 captures in the last 30 days by either signal).

**features-service manifest** (`features-sports-prd-central-element-323112/_index/availability_index.parquet`):

- `feature_group=derived_features`, last 30 days: 583 `captured` / 10 `empty_confirmed` — so NOT literally zero, unlike
  XG. But the captured rows' `date` (match/business date) tops out at **2026-07-19**, while `written_at` (actual write
  timestamp) reaches **2026-07-27T09:08Z — today**. That's an **~8-day lag between match date and write date**, far
  exceeding the ~25.25-26.25h fire window `features_post_match` targets — if the live trigger were producing this, a
  match's derived features would land within ~26h, not 8+ days.
- All-time `derived_features`: `date` max is also 2026-07-19 despite `written_at` reaching today — same lag, not a
  one-off.
- The SAME `date=2026-07-19` ceiling is shared by 9 other feature_groups in the identical manifest sweep (`fixtures`,
  `fixture_stats`, `fixture_events`, `standings`, `teams`, `venues`, `leagues`, `injuries`, `fixture_lineups`,
  `fixture_player_stats`) — while two DIFFERENT feature_groups fed by separate live pipelines (`fixture_features`,
  `odds_features`) are current through **2026-07-27 (today)**. A cluster of 10 feature_groups all frozen at the exact
  same stale date, while 2 unrelated ones stay live-current, is the signature of one shared BATCH/catch-up job that
  hasn't caught up — not the live per-fixture `features_post_match` trigger (which, per the root-cause above, cannot
  structurally fire at all since it `depends_on: stats_delayed`).

**Conclusion**: this is NOT "reaching GCS through a separate LIVE path" (the question's alternative). It's reaching GCS
through a separate BATCH path — for XG, a single historical backfill run and nothing since; for derived_features, a
shared multi-feature-group batch job running days behind the live-window target. The live scheduler's `stats_delayed` /
`features_post_match` triggers are confirmed dead in production exactly as the fixture-lookback root-cause predicts;
whatever coverage exists today is backfill-only and, for derived_features, meaningfully stale (~8 days) versus what a
working live trigger would provide.

## Recommended decision

File a dedicated fix plan (`assigned_vm: planning`, scoped to deployment-service) once Q1/Q2 above are answered — the
fix itself (likely (b): a day-range-aware lookback specifically for `evaluate_post_match_triggers`, since widening the
shared `horizon_hours` window would also inflate pre-match/discovery scan cost) should NOT be done as a rider on the
source-latency re-pin todo that discovered it (different repo focus, different testing surface, scoped fix vs.
mechanical constant re-pin).

## Q1 corroboration (worker slot 10, 2026-07-27) — independent second read, same verdict

Cross-checked slot-8's verdict above with an independent manifest read + code trace before starting the fix todo below —
same conclusion, plus two provenance details worth keeping on record:

- Confirmed the `features_post_match` dead-code path structurally: it shares the exact same
  `evaluate_post_match_triggers()` / `get_upcoming_fixtures()` fixture-list gate as `stats_delayed` in
  `sports_trigger_scheduler.py` (no code path distinguishes the two triggers) — so the fix below must cover both, not
  just `stats_delayed`.
- Traced the source of `derived_features`' apparent recent activity to a specific manual entrypoint:
  `features-service/scripts/vm/launch-features-sports-backfill-vm.sh`
  (`python -m features_service.sports --tables ... --force`), consistent with slot-8's
  `sports_consolidated_native_ao_extract_2026_07_25.md` Track F citation (the 2026-07-19 historical re-run) and Track
  V's still-open "which launcher ran this" todo.
- Confirmed no Tier-1/Tier-2 periodic entry exists for XG or derived_features either — `sports-trigger-tiers.yaml`'s
  `discovery`/`reference` sections only dispatch `instruments-service` FIXTURES/STANDINGS/INJURIES/TRANSFERS/LEAGUES.

## Todos

- [x] ✅ [DATA] P0. Answer Open Question 1 above: query the live sports manifest
      (`market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`) for
      `data_type=XG`/`entity=derived_features` capture_status counts over the last 30 days and compare against
      `FIXTURE_STATS` counts for the same fixture population, to determine whether Understat/derived-features capture is
      ALSO silently dead (not just the latency-observation instrumentation) or is reaching GCS through a separate path.
      Repo: instruments-service / market-tick-data-service (read-only). **Done when**: a clear confirmed/refuted verdict
      is recorded in this doc with the counts cited. — unified-trading-pm (doc-only, no code). See "Investigation: Open
      Question 1 — RESOLVED" above: CONFIRMED dead for XG (0/11,895 captured last 30d; all-time captures 100%
      `batch_understat`, one-shot 2026-07-13..22 backfill); derived_features not literally zero but ~8-day stale and
      tracking a shared batch job, not the live 26h window — consistent with `features_post_match` also never firing
      live. Independently corroborated by slot-10, see "Q1 corroboration" above.
- [x] ✅ [INFRA] P0. If Q1 confirms live capture is dead: design + ship a fix to
      `deployment_service/sports_trigger_state.py::get_upcoming_fixtures()` / `evaluate_post_match_triggers()` so
      post-match triggers with an offset beyond the current ~2h fixture-visibility cutoff can actually fire (see
      "Recommended decision" above for the design options) — with a regression test proving a synthetic 25h-offset
      trigger now fires for a fixture whose kickoff was >24h in the past. Repo: deployment-service. **Done when**: the
      fix ships, the regression test passes, and a live re-verification (next `stats_delayed` cycle after deploy) shows
      a fresh `data_type=XG` capture or a fresh `_index/latency_observations` row with `trigger_name=stats_delayed`. —
      deployment-service@5b5d227. Implemented option (b) — `SportsTriggerScheduler._max_post_match_lookback_hours()`
      derives the widest configured post-match fire-window edge from `configs/sports-trigger-tiers.yaml` (currently
      `features_post_match`: 105+25\*60+60=1665min=27.75h) and `run_once()` fetches a SEPARATE, wider-lookback fixture
      list (`get_upcoming_fixtures(lookback_hours=...)`) for `evaluate_post_match_triggers` only — the shared 2h
      pre-match/discovery cutoff and its GCS scan cost are unchanged. Also fixed `evaluate_post_match_triggers` to
      respect each trigger's own `tolerance_minutes` (was hardcoded to 30, silently ignoring `features_post_match`'s
      configured 60). 5 new regression tests in
      `deployment-service/tests/unit/test_sports_trigger_postmatch_lookback.py` (all pass; full suite 91/91 pass;
      `quality-gates.sh` green, basedpyright error count net DOWN 39→31 on the two touched files) — including an
      end-to-end `run_once()` test proving a synthetic fixture kicked off >24h ago now fires `stats_delayed` (would fail
      pre-fix, since `run_once` fed the single 2h-lookback fixture list to both pre- and post-match evaluation). **Live
      re-verification NOT YET DONE** — requires this fix to reach the deployed scheduler (LDR→staging→main promotion +
      redeploy) and a real fixture's `stats_delayed` window (~kickoff+25.25h..26.25h) to actually elapse post-deploy;
      tracked as a new todo below rather than claimed here.
- [x] ✅ [VERIFY] P1. Live re-verification follow-up for the fix above (deployment-service@5b5d227): first check
      `deployment-service`'s CI/CD status (`gh run list`/promotion PR state) to confirm the fix has reached the deployed
      sports-trigger-scheduler (promoted past staging + redeployed) — dispatch normally rather than waiting on an
      operator ask, since promotion status is a checkable fact. — unified-trading-pm (doc-only, no code). **Check 1
      (2026-07-28, slot-10) — CI/CD status check DONE, verdict: NOT YET DEPLOYED.** `5b5d227` is confirmed an ancestor
      of `deployment-service`'s LDR HEAD but NOT of `origin/main` (`git merge-base --is-ancestor 5b5d227 origin/main` →
      NO). It IS included in the currently-open LDR→main promotion PR `IggyIkenna/deployment-service#591` (opened
      2026-07-28T14:44Z, head `promote/deployment-service/f27ada5a4e92`, confirmed via
      `git merge-base --is-ancestor 5b5d227 <PR591-head>` → YES). PR591's required `quality-gates-v2` check **FAILED**
      (run `30369898092`, `QG slice (checks)` job, completed 2026-07-28T15:37Z): every individual gate (lint, typecheck,
      the sports-touched-file checks, etc.) PASSED — the failure is a pure wall-clock budget breach
      (`Resource drift: wall 1438s > 2× baseline 106.0s`; hard cap is 300s), NOT a regression in the sports fix itself.
      This matches the known, already-tracked, mostly-remediated fleet-wide self-hosted-runner capacity issue in
      `plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (oversubscribed shared
      16-vCPU runner host) — an `ldr_qg_failure` auto-escalation for this PR already fired and completed
      (`deployment-service` job "Escalate LDR-QG failure to orchestrator", 2026-07-28T18:03Z), so this is not a new,
      separately-escalation-worthy failure. **This "first check" sub-scope is done**; the manifest-verification
      sub-scope cannot run yet (nothing has redeployed) — split out as its own follow-up todo below rather than left
      unresolved here.
- [ ] [VERIFY] P1. Once `deployment-service@5b5d227` is confirmed on `origin/main` AND the sports-trigger-scheduler is
      confirmed redeployed past that point (re-run `git merge-base --is-ancestor 5b5d227 origin/main`, then check the
      scheduler's deployed-revision timestamp), query the live sports manifest for a FRESH `data_type=XG` `captured` row
      with `pipeline_mode` != `batch_understat` (i.e. NOT the 2026-07-13..22 one-shot backfill) or a fresh
      `_index/latency_observations/` row with `trigger_name=stats_delayed`, dated after the redeploy. Repo:
      instruments-service / market-tick-data-service (read-only). **Done when**: such a row is found (confirms the live
      fix works end-to-end) or, if none appears after a full day-plus of live operation post-redeploy, escalate — that
      would mean a second, still-undiagnosed issue beyond the lookback bug fixed here. **Blocked on**: PR591 (or its
      successor) actually merging to main — see "Check 1" above; do not dispatch the manifest query before confirming
      the ancestor check is YES.
