---
doc_type: issue
title:
  Full API-Football entity completion — every AF entity at its correct scope, so the API-Football plan can be downgraded
summary: >-
  Operator directive (2026-08-03): the sports satellite campaign's docs/plans must in aggregate cover EVERY API-Football
  (AF) entity without exception — all-383-league entities fully at 383, MVP-scoped entities fully at 96 — not just the 3
  entities (FIXTURE_EVENTS/FIXTURE_STATS/FIXTURE_LINEUPS) already tracked in
  `sports_fixture_events_refetch_progress_2026_07_25.md`. Explicit business goal: once genuinely complete, the operator
  wants to downgrade the API-Football subscription tier, so full completion here is the actual deliverable, not just
  data-quality hygiene. Censused the 5 previously-untracked AF entities (PLAYER_STATS/INJURIES/STANDINGS/TEAMS/LEAGUES)
  against their own SPORTS_ENTITY_LEAGUE_COVERAGE scope — 4 of the 5 show substantial genuine gaps (270,873 total needed
  shards across PLAYER_STATS/INJURIES/STANDINGS/TEAMS), plausibly explained by the SAME unconditional-MVP-pre-filter bug
  already found + fixed this session (todo #3, `instruments-service` per-fixture task-queueing loop) — these entities
  were already declared `None` (all-383) in the coverage dict from day one, but the actual fetch loop silently capped
  them to MVP-96 until that fix landed. **LEAGUES resolved 2026-08-03**: its initial 110,290-shard "gap" was a
  census-script artifact — the entity's daily write path was retired 2026-05-07 (replaced by code-committed UAC static
  data), confirmed via a live manifest spot-check; zero genuine work remains for LEAGUES.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [sports, api-football, entity-completion, downgrade-planning, mvp-scope]
related:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /codex/02-data/mvp-scope-canonical.md,
    /plans/archive/issues/manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md,
  ]
created: 2026-08-03
author: unknown
priority: P1
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["sports_satellite_ao_dispatch_batch2, autonomous continuation, 2026-08-03 — operator directive"]
drift_direction: advance-code
context_scope:
  [
    /plans/archive/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /codex/02-data/mvp-scope-canonical.md,
    /plans/archive/issues/manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md,
    instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py,
  ]
---

## Why this doc exists (not folded into the parent plan or the FIXTURE_EVENTS issue doc)

`sports_satellite_ao_dispatch_batch2_2026_07_24.md` is at 996/1000 lines (hard cap) — no room to add this scope there.
`sports_fixture_events_refetch_progress_2026_07_25.md` is at 897 lines and scoped specifically to FIXTURE_EVENTS — this
is a genuinely broader initiative (5 more entities, ~381k shards, a different completion criterion: "every AF entity
done" rather than "one entity's non-canonical count converges to 0"). Both existing docs are `related:` linked here.

## The operator's actual ask (verbatim intent, 2026-08-03)

"Ensure the docs/plans/issues you are going through in aggregate will do everything AF related without exception, so
that's finally done for all leagues where relevant and MVP-only leagues where relevant. Means we can then downgrade
API-Football." — i.e., this is not an open-ended data-quality nice-to-have; there is a concrete downstream action
(reducing vendor spend) gated on this campaign's genuine completion. Every AF entity, at its correct scope, or this doc
does not close.

## The full 9-entity picture

Per `unified_api_contracts.canonical.domain.sports.provider_league_ids.SPORTS_ENTITY_LEAGUE_COVERAGE`:

**✅ CORRECTED 2026-08-04T09:00Z, RE-CENSUSED 2026-08-05T16:04Z** — both census scripts fixed to treat `empty_confirmed`
as resolved (see Progress Log). Numbers below are the LATEST re-census, post consolidator-backlog-drain (see Progress
Log 2026-08-05T16:04Z entry — treat these as more current than the 08-04 figures but the consolidator is still not fully
healthy, so even these may understate true progress).

| Entity           | Scope                        | Status (2026-08-05)                                                                                                                                                           |
| ---------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FIXTURES         | all-383                      | **DONE** — confirmed complete `sports_fixture_events_refetch_progress_2026_07_25.md`                                                                                          |
| FIXTURE_EVENTS   | MVP-96                       | **DONE 2026-08-03** — pass-3 complete, 1,973 "degenerate" residual corrected as legacy dupes, same doc                                                                        |
| FIXTURE_STATS    | all-383 (widened 2026-07-28) | 66,292 expected (non-MVP), 329,654 already resolved, **33,671 needed** (continued strong progress, -483) — ACTIVE via `af-backfill-20260806-022033`                           |
| FIXTURE_LINEUPS  | all-383 (widened 2026-07-28) | 66,292 expected (non-MVP), 52,659 already resolved, **58,523 needed** (flat this tick — no dedicated backfill)                                                                |
| **PLAYER_STATS** | **MVP-96**                   | 42,371 expected, 41,373 already resolved, **only 998 needed** — nearly done                                                                                                   |
| **INJURIES**     | **all-383**                  | 108,663 expected, 45,954 already resolved, **62,709 needed** (unchanged — no backfill run yet)                                                                                |
| **STANDINGS**    | **all-383**                  | 108,663 expected, 96,910 already resolved, **11,753 needed** (was 64,439 on 08-04, **-52,686**) — **ACTIVE** via a separately-discovered dedicated VM, see below              |
| **TEAMS**        | **all-383**                  | 108,663 expected, 100,791 already resolved, **7,872 needed** (was 64,723 on 08-04, **-56,851**) — **ACTIVE** via `instr-backfill-sports-teams-20260805-055622` (chunk ~31/76) |
| **LEAGUES**      | ~~all-383~~ **RETIRED**      | **RESOLVED 2026-08-03** — writer path killed 2026-05-07, **0 genuinely needed**. See below.                                                                                   |

Denominator = distinct `(date, league_id)` pairs with a captured `FIXTURES`/`FIXTURES_SCHEDULE` row (a genuine fixture
existed that day), intersected with each entity's own `get_entity_league_coverage()` scope — mirrors
`emit_empty_gaps_for_entity`'s own expected-set logic (`sports_reference_core.py:338-341`); a shard is resolved (not
needed) if `capture_status` is `captured` OR `empty_confirmed`. Full census:
`instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py` +
`census_fixture_stats_lineups_widening_volume_2026_07_31.py` (both UTL-client-backed, both fixed 2026-08-04).

**Grand total needed, 2026-08-06T16:31Z: 83,332 across PLAYER_STATS+INJURIES+STANDINGS+TEAMS** (was 192,877 on 08-04, a
further ~57% drop — mostly STANDINGS/TEAMS backlog draining via a separately-discovered dedicated VM, see Progress Log)
**+ 96,600 across FIXTURE_STATS+FIXTURE_LINEUPS** (38,077 + 58,523). TEAMS/STANDINGS and FIXTURE_STATS are BOTH
confirmed active concurrently (2 lanes, see Progress Log correction). LEAGUES excluded per the resolved verdict below.
**PLAYER_STATS is the standout — genuinely near-complete (97.6%), worth launching soon** since it could converge quickly
once dispatched.

## ✅ RESOLVED 2026-08-03 — LEAGUES verdict: retired entity, 0 real work, do not launch

Two independent investigations converged on the same verdict (a dispatched Explore agent's code/GCS read, and a separate
live-manifest + retirement-commit check) — **measurement artifact, LEAGUES is not in scope at all.**

1. **The writer path was killed 2026-05-07** — `git show 93efebf3`
   (`feat(orchestrator)!: retire api_football LEAGUES daily-dump (C.1)`) confirms the pre-retirement cadence explicitly:
   "was 3046 daily shards of **identical static league refdata**" — so LEAGUES genuinely WAS written per-(date,league)
   historically (not per-season), but every date's shard held redundant, unchanging content, which is why the fix was
   full retirement rather than switching to a coarser cadence. `sports_reference.py:134-146` documents the replacement:
   UAC `LeagueDefinition` + `provider_league_ids` (`FOOTYSTATS_SEASON_IDS`, `FOOTYSTATS_HISTORICAL_SEASON_IDS`, etc.)
   canonicalise league metadata via **code commits at season start**, not a daily GCS dump — the api_football `/leagues`
   endpoint has not been called from the daily orchestrator since. `process_preflight.py:54-61` confirms LEAGUES was
   removed from `_SPORTS_CORE_ENTITIES` the same day. No downstream consumer regressed (features-sports'
   `LEAGUES_COLUMNS` was schema-only, no feature ever read `logo_url` etc. beyond what UAC already provides).
2. **The shard atom never had a `league_id` axis to begin with** —
   `unified-api-contracts/.../canonical/domain/sports/gcs_paths.py:186` declares
   `"LEAGUES": SportsPathLayout.PER_DAY_BARE` (no `league=` path segment), and
   `/codex/02-data/sports-gcs-path-ssot.md:115` states outright that LEAGUES is "cross-league reference data where
   `league_id` grouping has no meaning." A per-`(date, league_id)` denominator was categorically invalid for this entity
   — max theoretical shards was ~2,200 days, not 110,739. GCS confirms deletion too: sampled 5 dates across 2021–2026
   under `pipeline_mode=batch_api_football/`, zero `entity=leagues/` objects in any of them.
3. **Root cause of the false 110,290/449 "needed"/"captured" figures — a genuine bug, now fixed and applied**:
   `scripts/migrate_leagues_kill_2026_05_07.py` (the sanctioned, idempotent flip-to-`empty_confirmed` migration for
   exactly this retirement) hardcoded `SPORTS_BUCKET = f"instruments-store-sports-{PROJECT_ID}"` — missing the `-prd-`
   env infix — so it 404'd every single time it was ever run, silently, since 2026-05-07. It had **never once
   succeeded**; all 8,780 `data_type=LEAGUES` manifest rows were still stuck at `capture_status=captured` right up until
   this session. Fixed to use `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`
   - the UTL `get_storage_client()`/`upload_bytes` pattern (was inlining `google.cloud.storage` directly). Re-ran
     scan-only (confirmed 8,780 stale `captured` rows, not 449 — this doc's own census script's 449 figure was itself an
     undercount, since it only counted rows that also matched a captured-fixture date), then `--apply`'d with
     `MANIFEST_PER_VM_SHARDS=true VM_NAME=migrate-leagues-kill-finish-20260803` (CSV-audited — this is a manifest-only
     flip, NOT the separate operator-gated `gcloud storage rm -r .../entity=leagues/` GCS-object deletion, which remains
     untouched and still requires the operator). A follow-up live-manifest read (independently, by the second
     investigation) confirms all 8,780 rows now show `capture_status=empty_confirmed` +
     `error_reason=EXPECTED_DEPRECATED_DATA_TYPE`, zero `captured` remaining — the migration is genuinely applied, not
     just written. Shipped as `instruments-service@5db692db`.
4. Also dropped `"LEAGUES": False` from `census_all_af_entities_completion_2026_08_03.py`'s `ENTITIES` dict (it was
   censusing a retired data_type against an inapplicable denominator, and never checked for
   `empty_confirmed`/`EXPECTED_DEPRECATED_DATA_TYPE` — so it silently treated every fixture-day as still needing a
   LEAGUES capture) — re-ran, confirmed the other 4 entities' numbers are byte-for-byte unchanged (270,873 = 381,163 −
   110,290 exactly, so nothing else was touched by the flip).

**Residual, non-blocking (not this doc's scope, noted for whoever next touches sports config)**:
`SPORTS_ENTITY_LEAGUE_COVERAGE["LEAGUES"] = None` and `SPORTS_ENTITY_START_DATES["LEAGUES"] = "2019-01-01"` in
`provider_league_ids.py` are stale leftovers from before the 2026-05-07 retirement — they actively mislead any future
census/tooling into treating LEAGUES as a live all-383 entity (as they did here). Worth a follow-up cleanup PR in UAC,
not urgent enough to block this campaign.

## ⚠️ Caveat still open for the 4 in-scope entities

1. **The "needed shards → API calls" conversion is UNKNOWN for TEAMS/STANDINGS/INJURIES.** The 4.5875-fixtures-per-shard
   ratio used to estimate FIXTURE_STATS/LINEUPS/EVENTS call volume was derived from FIXTURE_EVENTS specifically (a
   genuinely per-fixture entity — one event-list call per match). TEAMS is observed in logs as one call per **league**
   (`Fetched 20 teams for league=39 season=2025`), not per fixture — so a single API call likely satisfies MANY
   `(date, league)` shard-rows at once (every date that league had a fixture inherits the same team-roster fetch). **Do
   not multiply TEAMS' needed-shard count by 4.5875** — that would badly overstate its real API-call cost.
   INJURIES/STANDINGS are more plausibly per-fixture-date already (injury reports and standings snapshots genuinely
   change match-to-match), closer to the FIXTURE_EVENTS model, but this is also unverified. (This is the same
   LEAGUES-shaped trap the resolved verdict above just caught — worth actually checking before launching, not assuming.)

## Todos

- [x] ✅ [SCRIPT] P1. **Spot-check LEAGUES' real write cadence** — **RESOLVED 2026-08-03**: LEAGUES daily-dump write
      path retired 2026-05-07 (`instruments-service@93efebf3`), replaced by code-committed UAC static data. Root cause
      of the 110,290/449 false figures found + fixed: `migrate_leagues_kill_2026_05_07.py`'s hardcoded bucket name
      (`instruments-service@5db692db`); applied, confirmed via live manifest read (all 8,780 LEAGUES rows =
      `empty_confirmed`/`EXPECTED_DEPRECATED_DATA_TYPE`, zero `captured`). Census script corrected to 4 entities. Not in
      scope, no LEAGUES backfill will be launched. See "RESOLVED" section above.
- [x] ✅ [SCRIPT] P1. **Launch FIXTURE_STATS all-leagues backfill** — CONFIRMED RUNNING 2026-08-03: VM
      `af-backfill-20260803-233053` (launched by `unified-trading-sa`, `purpose=api-football-backfill`,
      `managed-by=deployment-service`), metadata confirms
      `entity=FIXTURE_STATS source=API_FOOTBALL     start_date=2020-06-06`. FIXTURE_EVENTS pass-3 singleton lock had
      cleared (it is the only `af-backfill-*`/ `af-audit-*` VM RUNNING — the prior three are TERMINATED). `run.log`
      shows healthy per-fixture progress (`[[VM_PROGRESS]] last_completed_date=2020-06-13→2020-06-14`, manifest writes,
      correct rate-limit backoff handling). No duplicate VM launched — a second concurrent AF-consuming VM would violate
      the shared singleton lock / quota.
- [ ] [SCRIPT] P1. **Launch FIXTURE_LINEUPS all-leagues backfill** the same way, after FIXTURE_STATS converges.
      Corrected: 58,523 needed (was 69,165 pre-fix).
- [x] ✅ [SCRIPT] P0. ~~Recompute PLAYER_STATS/INJURIES/STANDINGS/TEAMS needed counts~~ — **CORRECTED 2026-08-04**: both
      census scripts had an empty_confirmed blind spot, fixed (`instruments-service@579421bf`). See the corrected table
      above. **PLAYER_STATS reprioritized to P0** — only 1,006 needed (was 17,440), genuinely near-complete.
- [ ] [SCRIPT] **P0** (reprioritized, near-complete). **Launch PLAYER_STATS MVP-96 backfill**
      (`--entity PLAYER_STATS 2020-06-06 <today>`) once the singleton lock frees up — only **998 needed shards**
      (2026-08-05 re-census), should converge fast.
- [ ] [SCRIPT] P1. **Launch TEAMS all-leagues backfill** (46,786 needed as of 2026-08-05T19:11Z — **IN PROGRESS**,
      `af-backfill-20260805-201310` launched 20:13Z after FIXTURE_STATS's rate slowed; likely 1 call/league not 1
      call/shard, confirm real call cost before estimating timeline; may complete far faster than the shard count
      implies).
- [ ] [SCRIPT] P1. **Launch STANDINGS all-leagues backfill** (51,114 needed, 2026-08-05 re-census — dropped from
      64,439). Same discipline. Next up after TEAMS.
- [ ] [SCRIPT] P2. **Launch INJURIES all-leagues backfill** (62,709 needed, unchanged — no backfill run against it yet)
      — likely per-fixture-date cadence, apply the daily stop/resume discipline.
- [x] ✅ [SCRIPT] P2. ~~Launch LEAGUES all-leagues backfill~~ — NOT APPLICABLE, resolved above: LEAGUES is a retired
      entity (no write path since 2026-05-07); there is nothing to launch. Excluded from this campaign's remaining scope
      and from the grand-total needed count.
- [ ] [SCRIPT] P0. **Re-census the 8 in-scope entities once every backfill above completes** (FIXTURES, FIXTURE_EVENTS,
      FIXTURE_STATS, FIXTURE_LINEUPS, PLAYER_STATS, INJURIES, STANDINGS, TEAMS — LEAGUES permanently excluded, resolved
      above), confirm every needed-count converges to ~0 (accounting for genuine honest-absence floors per entity, same
      pattern as FIXTURE_EVENTS' ~1,943-stub floor), and only then close this doc + notify the operator the full AF
      completion is genuinely done and the API-Football plan can be downgraded.
- [x] ✅ [SCRIPT] P1. **Implement the durable convergence-gate fix flagged 4 times in this doc's Progress Log (repo:
      agent-orchestrator).** — **DONE 2026-08-04 (slot 11)**: slots 5/6/8/13 all correctly found no filesystem access to
      the LIVE `data/config/backlog.yaml` from their `.tabs/<slot>/agent-orchestrator` clones and concluded this needed
      main/operator — but a purpose-built API endpoint for exactly this disposition already existed and was missed:
      `POST /api/backlog/{task_id}/park` (`server/routes/backlog.py:709`, shipped
      `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31`, predates none of the prior dispatches' checks
      but wasn't discovered until this one). It applies the identical mutation RULES.md §4 describes
      (`priority=999`+`priority_override=true`+ a false synthetic `prereqs.prerequisites` condition) via a single
      authenticated POST — **no backlog.yaml filesystem access needed at all**, worker-callable. Called it:
      `condition=auto_unpark__sports_af_full_entity_completion-003`, confirmed via `GET /api/backlog/parked`
      (`parked:     true`, `priority_override` implied by presence in that list). This task will not be offered to ANY
      slot again until that condition is flipped true. **Unpark criteria** (for whoever does it — operator via dashboard
      "Dispatch now", or a worker instructed to check): re-run
      `instruments-service/scripts/census_fixture_stats_lineups_widening_volume_2026_07_31.py`, confirm FIXTURE_STATS
      non-MVP captured count is at/near the full ~68k needed (it was 125/68,284 = 0.18% at park time, 2026-08-04T01:40Z)
      — once genuinely converging,
      `POST /api/prerequisites/auto_unpark__sports_af_full_entity_completion-003     {"value": true, "set_by": "operator"}`
      (or `POST /api/backlog/sports_af_full_entity_completion-003/unpark`). **Residual gap, not fixed here**:
      FIXTURE_STATS itself has no dedicated recurring-retry todo of its own — every relaunch to date happened only as a
      side-effect of this task's repeated redispatch. Now that this task is parked, nothing will proactively relaunch
      FIXTURE_STATS past the SPOT storm; it needs an explicit operator check-in (dashboard's parked-tasks view now
      surfaces this task per `get_parked_tasks()`'s design intent) rather than relying on redispatch churn to notice.

## Sequencing note

All of these share the SAME `af-backfill-*`/`af-audit-*` singleton lock (one API-Football-consuming VM at a time, shared
daily quota) as the already-in-flight FIXTURE_EVENTS pass-3 and the queued FIXTURE_STATS/FIXTURE_LINEUPS work — this is
a genuinely sequential, multi-day-to-multi-week campaign, not something to parallelize across VMs. Priority order above
(P1 before P2) reflects: entities already declared as "widened this session" (FIXTURE_STATS/LINEUPS/ PLAYER_STATS)
before the newly-discovered-but-not-yet-widened-in-conversation entities (INJURIES/STANDINGS/TEAMS/ LEAGUES), though all
are genuinely in scope for the operator's "no exceptions" directive.

## Progress Log

- **2026-08-03 (main agt-1756f6)** — Blocked-queue Q **BLK-169e1207** (slot 12, task
  `sports_af_full_entity_completion-003` = "Launch FIXTURE_LINEUPS all-leagues backfill") answered **A: do NOT launch
  now**. The worker correctly caught a **premature-dispatch**: FIXTURE_LINEUPS is gated on "after FIXTURE_STATS
  converges" (todo above), but FIXTURE_STATS (`af-backfill-20260803-233053`) had only started ~10 min earlier (69,171
  shards, multi-day) and was the sole RUNNING AF VM. Launching FIXTURE_LINEUPS then would have run a 2nd concurrent AF
  VM against the **shared singleton lock / one API-Football daily quota** (the Sequencing note above), violating the
  lock. Instructed `skip-current-task` (returns to queue).
- **Recurring risk flagged (durable fix needed, not yet done)**: the launch todos here are serialized only by
  `sequential:true`, which encodes **dispatch order, NOT the real convergence gate**. So each launch todo redispatches
  the instant the prior one _completes_ (i.e. the prior VM _launches_ / its dispatch finishes), not when the prior
  entity's backfill actually _converges_ (census == 0 needed) and frees the singleton lock. Any slot that next claims a
  launch todo will hit the same trap. **Proper fix**: gate each launch todo on a real prerequisite keyed to the prior
  entity's census-0 / lock-free state (a `depends_on` prerequisite the backend actually blocks on, or park the
  downstream launch todos until an operator/worker confirms the prior AF VM finished), rather than relying on dispatch
  ordering. Until then, any worker dispatched a `Launch <ENTITY> backfill` todo here MUST first verify no other
  `af-backfill-*`/`af-audit-*` VM is RUNNING (singleton lock free) and that the immediately-prior entity's census shows
  ~0 needed — if not, `skip-current-task` and it requeues (do NOT launch a 2nd concurrent AF VM).
- **2026-08-04 (slot 4)** — Dispatched the same `sports_af_full_entity_completion-003` (Launch FIXTURE_LINEUPS) todo.
  Re-verified the gate per the risk note above: singleton lock was FREE (no `af-backfill-*`/`af-audit-*` VM RUNNING —
  confirmed via `gcloud compute instances list`), but FIXTURE_STATS had **not converged**: re-ran
  `census_fixture_stats_lineups_widening_volume_2026_07_31.py`, which showed only 125/68,409 non-MVP shards captured
  (0.18%) — essentially unchanged from launch. Root cause: the prior FIXTURE_STATS VM (`af-backfill-20260803-233053`)
  was **SPOT-preempted ~17 min after launch** (audit log: `compute.instances.preempted` at 2026-08-03T23:47-48Z, ~16 min
  after the 23:31 `instances.insert`) and **never auto-resumed** — the VM no longer exists at all (not even TERMINATED
  in the instance list), and no successor `af-backfill-*` VM was ever launched. This is exactly the class the codex HARD
  RULE "preemption recovery must resume from measured PROGRESS, never replay START_DATE" exists for
  (`/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis/backfill preemption); the
  `exit_code_fleet_monitor`/`RelaunchPreemptedVm` auto-recovery apparently did not fire for this VM (worth a follow-up
  look at why, not chased further here — out of this doc's scope). **Action taken**: relaunched FIXTURE_STATS as
  `af-backfill-20260804-001203` (`launch-api-football-backfill-vm.sh --entity FIXTURE_STATS 2020-06-06 2026-08-04`,
  SPOT, idempotent skip-if-captured — no `--force`, so this is a safe resume, not a redo_all). Verified healthy at
  T+~4min: `run.log` shows genuine per-fixture FIXTURE_STATS fetches (`Fetched 2 stat rows for fixture=...`), correct
  skip-already-captured + observed-out-of-coverage handling, and correct 429 rate-limit backoff — not a crash-loop.
  **FIXTURE_LINEUPS remains blocked** — its gate ("after FIXTURE_STATS converges") is still unmet; did NOT launch it.
  `skip-current-task`'d `sports_af_full_entity_completion-003` again so it requeues once FIXTURE_STATS genuinely
  converges. The durable fix flagged above (a real `depends_on` convergence gate instead of dispatch-order
  `sequential:true`) is still not implemented — a future worker will hit this same trap a third time until it is; not
  fixed in this session (outside this task's scope, flagging again for whoever next touches plan authoring for this
  campaign).
- **2026-08-04 (slot 6)** — Dispatched `sports_af_full_entity_completion-003` a third time. Re-verified the gate per the
  standing risk note: singleton lock FREE (no `af-backfill-*`/`af-audit-*` VM RUNNING), but FIXTURE_STATS still NOT
  converged — re-ran `census_fixture_stats_lineups_widening_volume_2026_07_31.py`: 125/68,409 non-MVP shards captured
  (0.18%), essentially unchanged from slot 4's check. Root cause: slot 4's relaunch (`af-backfill-20260804-001203`,
  launched 00:12:03Z) was **SPOT-preempted again ~6 min later** (audit log: `compute.instances.preempted` at
  00:18:20-31Z) — the **second same-day preemption of the same entity's backfill**, and again with **no auto-recovery**:
  `dp_exit_code_monitor_cron` runs `*/5 * * * *`, so 1-2 ticks had already elapsed with no successor VM launched by the
  time I checked (~00:25-00:30Z). Investigated whether this is a config gap (it isn't — `af-backfill-` is correctly
  registered in `launcher_registry.py`, the PREEMPTED relaunch budget is 48/day and nowhere near exhausted, resume-env
  is correctly persisted via `lc_write_launch_params`) and filed the recurring-pattern finding as its own issue doc
  since it's a genuine infra gap outside this campaign's scope:
  `/plans/archive/issues/af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md` (leading hypothesis: a VM whose
  full lifetime is shorter than one 5-min monitor tick may be structurally invisible to the monitor's
  prior-tick/this-tick census diff — both preempted VMs today died in ~6-17 min). **Action taken**: relaunched
  FIXTURE_STATS again as `af-backfill-20260804-002608` (same safe idempotent resume, no `--force`) — verified healthy at
  boot (serial console: dependencies installed, task launched PID 8317, `=== VM setup complete ===` exit 0) and
  confirmed genuine fetch activity in `run.log` shortly after. **FIXTURE_LINEUPS remains blocked** — gate still unmet;
  did NOT launch it. `skip-current-task`'d `sports_af_full_entity_completion-003` again so it requeues once
  FIXTURE_STATS genuinely converges. Given this is now 2 preemptions in <24h with 2 manual relaunches, the durable
  convergence-gate fix (flagged twice above, still not implemented) and the new auto-recovery issue doc are both now
  higher-priority than before — a fourth dispatch of this same todo without either fix landing is a near-certainty.
- **2026-08-04 (slot 6, continued)** — Root-caused + fixed the auto-recovery gap in the same session (see
  `af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md`): `af-backfill-`/`af-audit-` were entirely missing
  from `exit_code_fleet_monitor`'s `_DATA_VM_PREFIXES`, making these VMs structurally invisible to the preemption
  classifier regardless of timing. Shipped `deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`.
- **2026-08-04 (slot 5)** — Dispatched `sports_af_full_entity_completion-003` a fourth time, exactly as slot 6's note
  predicted. Re-verified the gate: singleton lock FREE, FIXTURE_STATS still NOT converged (125/68,409 non-MVP shards,
  unchanged). Relaunched FIXTURE_STATS as `af-backfill-20260804-004955` (same safe idempotent resume) — preempted almost
  immediately (~1.5 min lifetime, 00:49:55Z→00:51:21Z), the **third** preemption of this entity in <24h, each faster
  than the last (17min→6min→1.5min). Investigated further and found this is **not af-backfill-specific**:
  `asia-northeast1-c` is in an active, sustained SPOT preemption storm — 151 `compute.instances.preempted` events over
  the prior 5h, hitting sports/tradfi/cefi concurrently, still firing as of the check. Filed
  `/plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md` (P1, cross-cutting) with the full
  evidence and a recommended decision (confirm the auto-recovery fix above is actually deployed to the live Cloud Run
  job image; re-check preemption volume in a few hours; do not keep blind-relaunching into an active storm). **Did NOT
  attempt a further relaunch** — burning more SPOT minutes into a confirmed active storm is not productive.
  `skip-current-task`'d `sports_af_full_entity_completion-003` again so it requeues once the storm subsides and
  FIXTURE_STATS can make real progress. The durable convergence-gate fix (flagged three times now) remains the standing
  structural recommendation — but the storm, not the gate mechanism, is now the actual blocker for FIXTURE_STATS itself;
  a fifth dispatch should first check `/plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md`
  before relaunching again.
- **2026-08-04 (slot 8)** — Dispatched `sports_af_full_entity_completion-003` a sixth time
  (`already_in_progress: true`/resume — this session had this task before, per an earlier turn). Per the storm doc:
  confirmed via `gcloud artifacts docker images describe ...:latest` that the af-backfill/af-audit prefix fix IS
  deployed (digest `sha256:1ba77ac3...`, matching what slot 5 already verified independently — my own first read of the
  images-list table briefly pointed at the wrong row/timestamp before the digest check corrected it). Re-verified the
  gate: singleton lock was occupied by `af-backfill-20260804-015704` (launched 00:58:21Z) when I first checked, so I
  waited rather than launching a 2nd concurrent AF VM — it was preempted at 01:04:30-41Z (~6.2min lifetime), the **6th
  FIXTURE_STATS launch and 5th-or-6th preemption today** (full today's timeline: `-233053` ~16.5min → `-001203` ~5.8min
  → `-002608` ~12min → `-004955` ~1.5min → `-015704` ~6.2min; zero clean completions). Re-ran
  `census_fixture_stats_lineups_widening_volume_2026_07_31.py`: still 125/68,284 non-MVP shards captured (0.18%,
  byte-identical to every prior check today) — **zero net progress across 5 launch attempts and ~1.5h of wall-clock
  storm exposure.** The `asia-northeast1-c` storm is confirmed STILL ACTIVE (this fresh preemption, ~4 min before this
  check). Consistent with slot 5's judgment, did **NOT** attempt a 6th blind FIXTURE_STATS relaunch — the storm shows no
  sign of subsiding and each attempt is now converting to preemption within single-digit minutes regardless. Did **NOT**
  launch FIXTURE_LINEUPS (both gates still unmet). Filed the durable convergence-gate fix as a proper `- [ ]` todo above
  (P1, repo: agent-orchestrator) instead of a 4th prose-only flag — this worker has no filesystem access to the live
  `data/config/backlog.yaml` to implement it directly. `skip-current-task`'d `sports_af_full_entity_completion-003`
  again. Recommend the next dispatch check both the storm doc's "re-check after several hours" todo (not yet due — only
  ~15-20 min of storm-doc-tracked time has elapsed since it was filed) and this doc's new durable-gate-fix todo before
  repeating the same manual check a 7th time.
- **2026-08-04 (slot 13)** — Dispatched `sports_af_full_entity_completion-003` a seventh time. Singleton lock was FREE.
  Bucketed the storm doc's preemption log into 10-min buckets over the trailing 90 min and found a real peak-then-taper
  shape (32→1-6/10min) plus an 11-min clean gap right before checking — read as genuine subsidence and relaunched
  FIXTURE_STATS as `af-backfill-20260804-011911` (safe idempotent resume). Preempted again at 01:21:36-48Z, ~2.5min
  lifetime — the **7th FIXTURE_STATS preemption today**, zero clean completions across all 7 attempts. Re-ran
  `census_fixture_stats_lineups_widening_volume_2026_07_31.py` beforehand: still 125/68,284 non-MVP shards (0.18%,
  unchanged). Full analysis + revised recommendation in
  `/plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md`'s Progress Log — zone-wide aggregate
  rate alone was NOT sufficient evidence to safely relaunch this `e2-standard-8` entity; a future dispatch should wait
  for a longer confirmed-clean window before trying again. Did NOT attempt an 8th relaunch. **FIXTURE_LINEUPS remains
  blocked** — gate still unmet; did NOT launch it. `skip-current-task`'d again so it requeues. The durable
  convergence-gate fix (now a proper `- [ ]` todo above, P1, repo: agent-orchestrator) is unchanged by this dispatch —
  confirmed (again) this worker has no filesystem access to the live orchestrator `data/config/backlog.yaml` from
  `.tabs/13/agent-orchestrator` (only the `backlog.test.yaml` fixture) to implement it directly; still needs
  main/operator.
- **2026-08-04 (slot 11)** — Dispatched `sports_af_full_entity_completion-003` an eighth time. Re-verified both gates
  fresh: singleton lock FREE (no `af-backfill-*`/`af-audit-*` VM RUNNING or even listed — today's ephemeral VMs are
  fully deleted on preemption, not just terminated), FIXTURE_STATS re-censused at 125/68,284 non-MVP shards (0.18%) —
  byte-identical to slot 13's check ~19 min earlier, zero net progress. Pulled the raw `compute.instances.preempted`
  audit log for `asia-northeast1-c` 01:02Z→01:34Z: events at 01:04 (af-backfill), 01:06×4 (2 tradfi VMs), 01:21×2
  (af-backfill), and **01:33:47Z** — an `expected-universe-v2-sports-*` VM (non-af-backfill), i.e. the zone was still
  actively preempting sports-campaign VMs **~1 minute before this check**. Given that fresher, still-active evidence
  plus the established 7/7 relaunch-failure pattern, did **NOT** attempt a further FIXTURE_STATS relaunch (would only
  repeat slot 13's just-failed judgment call on comparably-thin evidence of a "clean window"). **Root-fixed the
  redispatch waste instead of re-logging it a 5th time**: found `POST /api/backlog/{task_id}/park`
  (`server/routes/backlog.py:709`, live since `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31`) — a
  worker-callable API that applies RULES.md §4's exact park recipe without needing the backlog.yaml filesystem access
  that blocked slots 5/6/8/13. Called it (see todo above, now flipped) — `sports_af_full_entity_completion-003` is now
  durably parked (`condition=auto_unpark__sports_af_full_entity_completion-003`, confirmed via
  `GET /api/backlog/parked`), so this task will NOT be redispatched to any slot again until an operator (or an
  explicitly instructed worker) confirms FIXTURE_STATS convergence and flips the condition true. Did not attempt to also
  fix FIXTURE_STATS's own lack-of-a-retry-mechanism (out of scope for a park action) — flagged as a residual gap in the
  todo above instead. `skip-current-task`'d (reason_code=GATED) to release the slot per the now-parked state.
- **2026-08-04 (condensed, 05:38Z-13:37Z)** — A day of SPOT-preemption churn: 15 relaunch attempts for FIXTURE_STATS/
  PLAYER_STATS against a zone-wide `asia-northeast1-c` low-intensity background preemption rate (documented + resolved
  in `asia_northeast1_c_spot_preemption_storm_2026_08_04.md`); root cause was a missing backoff on
  `expected-universe-v2-sports`'s retry loop colliding with af-backfill on the same SPOT pool, fixed
  `deployment-service@1861cbe` (best run afterward: 38min, up from ~17min). **Campaign-wide census bug found + fixed**:
  both census scripts only counted `capture_status=="captured"`, silently missing hundreds of thousands of already-
  resolved `empty_confirmed` (honest-absence) shards for every entity — fixed to treat `captured OR empty_confirmed` as
  resolved. A "frozen consolidator `rows_out`" finding was filed as a separate issue doc, then (08-05T17:03Z) discovered
  to be a duplicate of an already-resolved prior investigation proving it's expected idempotent-absorption behavior, not
  data loss — downgraded to false-positive/P3, no impact on this doc's figures.
- **2026-08-05 (condensed)** — Two scheduling idle-gaps in the af-backfill-* singleton lock (10hr, then 15hr, root cause
  not pursued — out of this doc's diagnostic scope). instruments-service's `.venv` was found genuinely missing, fixed
  via `uv sync`. A long healthy FIXTURE_STATS run (~7hrs total) drove FIXTURE_STATS from 56,940→49,442 needed before its
  rate dropped below the ~300-400/check threshold, triggering the first deliberate entity-switch to TEAMS
  (`af-backfill-20260805-201310`) — which then ran ~6.8hrs, dropping TEAMS/STANDINGS from ~66k/62k resolved further, and
  established that TEAMS+STANDINGS move in lockstep even when only `--entity TEAMS` is passed (the launcher processes
  both "core" per-date entities together regardless of scoping flag).
- **2026-08-06T01:16Z-02:18Z** — Switched back to FIXTURE_STATS once TEAMS/STANDINGS's rate crossed the switch threshold
  (`af-backfill-20260806-022033` launched). **Correction**: 3 ticks of continued TEAMS/STANDINGS drainage after that
  "pause" were initially misattributed to trailing consolidator lag — investigation found the true cause:
  **`instr-backfill-sports-teams-20260805-055622`**, a separate dedicated chunked TEAMS backfill
  (`instruments_chunk_loop.sh`, 76 chunks, running continuously since 2026-08-05T05:59:14Z, independent of the
  `af-backfill-*` pool/launcher family) had been the real ongoing driver all along. Reclassified TEAMS/STANDINGS ACTIVE
  (not paused) via this VM, added it to the standing VM-health check filter. Grand total 145,166 (core 4) + 106,963
  (FIXTURE_STATS+LINEUPS) at this point.
- **2026-08-06T02:41Z-05:29Z (condensed, 7 ticks)** — Sustained steady-state: both lanes healthy throughout. TEAMS
  dropped 38,792→31,038 (-7,754 total), STANDINGS 42,666→34,914 (-7,752, near-identical to TEAMS the whole stretch,
  minor variance normal) via the dedicated VM. FIXTURE_STATS held flat the entire stretch (48,432 unchanged) —
  re-verified via run.log twice more during this window (02:41Z: confirmed active via VM_PROGRESS markers, 3x total by
  then; 04:51Z after a longer ~93min gap: confirmed active again, VM had advanced ~176 days of real dates
  2020-10-02→2021-03-27 while the manifest count stayed frozen, the longest unabsorbed backlog of the campaign) —
  treated as expected consolidator lag, no longer re-verifying unless the flat stretch reaches ~10+ ticks. Grand total
  dropped from 143,332 to 129,660 (core 4) across this stretch; FIXTURE_STATS+LINEUPS held at 106,963 throughout.
- **2026-08-06T05:48Z** — Both lanes healthy. TEAMS 31,038→30,330 (-708), STANDINGS 34,914→34,206 (-708) — continued
  steady progress. FIXTURE_STATS flat for a 9th tick (48,432, unchanged) — approaching the ~10-tick re-verify milestone;
  will do one more run.log sanity check next tick if it's still flat. Grand total 128,244 (core 4) + 106,963
  (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T06:07Z — final planned FIXTURE_STATS re-verify.** TEAMS 30,330→29,931 (-399), STANDINGS 34,206→33,807
  (-399) — continued progress. FIXTURE_STATS hit the 10th consecutive flat tick, so did the planned final sanity check:
  `[[VM_PROGRESS]]` markers now at 2021-05-23, further advanced from the 2021-03-27 seen at the last re-verify (~57 more
  days of real work processed while the manifest count stayed at 48,432 the whole time). Confirmed healthy — this is the
  last planned re-verification; going forward, flat FIXTURE_STATS readings are fully trusted without further run.log
  checks unless something structurally changes (VM disappears, preemption, etc.). Grand total 127,446 (core 4) + 106,963
  (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T06:26Z** — FIXTURE_STATS moved for the first time after the extended flat stretch: 48,432→48,424 (-8) —
  small, not the large catch-up burst anticipated, just normal incremental progress resuming. FIXTURE_LINEUPS also moved
  by the same -8 (58,531→58,523) despite having no dedicated backfill VM — likely incidental resolution via the
  FIXTURE_STATS VM's per-fixture enrichment loop touching adjacent entities, similar in spirit to the earlier
  TEAMS/STANDINGS pairing discovery; not investigated further, small and not concerning. PLAYER_STATS also ticked -1
  (999→998) with no dedicated VM — likely the same incidental-resolution mechanism. TEAMS 29,931→29,245 (-686),
  STANDINGS 33,807→33,121 (-686) — continued progress via the dedicated VM. Grand total 126,073 (core 4) + 106,947
  (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T06:46Z** — Both lanes healthy. TEAMS 29,245→28,494 (-751), STANDINGS 33,121→32,370 (-751) — continued
  steady progress. FIXTURE_STATS+LINEUPS both flat this tick (48,424/58,523 unchanged), no re-verification per the
  now-established trust. Grand total 124,571 (core 4) + 106,947 (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T07:06Z** — Both lanes healthy. TEAMS 28,494→27,627 (-867), STANDINGS 32,370→31,503 (-867) — continued
  strong progress. FIXTURE_STATS resumed steady movement (48,424→48,354, -70); FIXTURE_LINEUPS flat. Grand total 122,837
  (core 4) + 106,877 (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T07:25Z** — Both lanes healthy. TEAMS 27,627→27,284 (-343), STANDINGS 31,503→31,160 (-343) — smaller delta
  than recent ticks but this is the dedicated chunk-loop VM (not switch-eligible), just noted. FIXTURE_STATS
  accelerating (48,354→48,202, -152). Grand total 122,151 (core 4) + 106,725 (FIXTURE_STATS+LINEUPS). Both VMs left
  running.
- **2026-08-06T07:45Z** — Both lanes healthy. TEAMS rebounded strongly: 27,284→26,110 (-1,174), STANDINGS 31,160→29,986
  (-1,174). FIXTURE_STATS continued its acceleration trend: 48,202→47,815 (-387, its largest single-tick drop yet).
  Grand total 119,803 (core 4) + 106,338 (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T08:04Z** — Both lanes healthy. TEAMS 26,110→25,185 (-925), STANDINGS 29,986→29,061 (-925) — continued
  strong progress. FIXTURE_STATS continued dropping (47,815→47,532, -283). Grand total 117,953 (core 4) + 106,055
  (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T08:24Z** — Both lanes healthy. TEAMS 25,185→24,613 (-572), STANDINGS 29,061→28,489 (-572) — continued
  progress. FIXTURE_STATS hit a new acceleration record: 47,532→47,049 (-483). Grand total 116,809 (core 4) + 105,572
  (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T08:43Z-09:38Z (condensed, 3 ticks)** — Both lanes healthy throughout. TEAMS dropped 24,613→22,267 (-2,346
  total), STANDINGS 28,489→26,143 (-2,346, lockstep as usual) via the dedicated VM; FIXTURE_STATS dropped 47,049→45,711
  (-1,338 total). Grand total fell from 116,465 to 112,117 (core 4) across this stretch. Two notable events during this
  window: (1) **operator side-question (out of this doc's scope)**: asked in live chat about completion status of 5
  OTHER sports vendors (odds_api/footystats/understat/open_meteo-weather/soccer_football_info/ transfermarkt) — agent
  investigation found 4/6 already ≥97-100% done at MVP-96, only WEATHER (~1,105 fixed + ~60-96/day growing) and SFI
  (~1,145 fixed + ~63/day growing) show real active gaps; proposed launching footystats+weather+sfi backfills, operator
  has NOT yet confirmed, not started, not acted on. (2) **git-discipline finding**: hit an unresolved autostash-pop
  conflict (8 accumulated stash entries found on this checkout, pre-existing not caused by this campaign) on an
  unrelated file (`deepseek_flash_ab_routing_test_2026_08_05.md`) — verified its content was byte-identical to
  HEAD/origin (already independently committed by another agent, `28f357806`) before marking resolved via `git add`, so
  nothing was discarded; unstaged (not deleted) an unrelated foreign new-file artifact from the same stash-pop; left the
  8 stash entries and an unrelated modified script untouched (not mine to manage). No impact to the campaign itself.
- **2026-08-06T10:01Z** — Both lanes healthy. TEAMS 22,267→21,103 (-1,164), STANDINGS 26,143→24,979 (-1,164).
  FIXTURE_STATS 45,711→45,127 (-584). Grand total 109,789 (core 4) + 103,650 (FIXTURE_STATS+LINEUPS). Both VMs left
  running.
- **2026-08-06T10:24Z** — Both lanes healthy. TEAMS 21,103→19,910 (-1,193, now under 20k), STANDINGS 24,979→23,786
  (-1,193). FIXTURE_STATS hit a new acceleration record: 45,127→43,883 (-1,244). Grand total 107,403 (core 4) + 102,406
  (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T10:44Z** — Both lanes healthy. TEAMS 19,910→19,253 (-657), STANDINGS 23,786→23,133 (-657). FIXTURE_STATS
  43,883→42,795 (-1,088). Grand total 106,093 (core 4) + 101,318 (FIXTURE_STATS+LINEUPS). Both VMs left running. Also
  pulled in an unrelated corpus-hygiene commit (`b30fb5267`) that updated this doc's `related:`/ `context_scope:`
  frontmatter reference paths after two linked docs got archived elsewhere — content unaffected, no action needed.
- **2026-08-06T11:04Z** — Both lanes healthy. TEAMS 19,253→18,857 (-396), STANDINGS 23,133→22,737 (-396). FIXTURE_STATS
  42,795→41,577 (-1,218). Grand total 105,301 (core 4) + 100,100 (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T11:19Z** — Both lanes healthy. TEAMS 18,857→18,475 (-382), STANDINGS 22,737→22,355 (-382). FIXTURE_STATS
  40,969 (-608, was 41,577). Grand total 104,537 (core 4) + 99,492 (FIXTURE_STATS+LINEUPS). Both VMs confirmed RUNNING
  (af-backfill-20260806-022033, instr-backfill-sports-teams-20260805-055622). Operator's other-6-vendor backfill
  question (weather/sfi/footystats/understat/transfermarkt/odds_api) remains genuinely open — no explicit go-ahead
  received yet, still parked per standing caveat.
- **2026-08-06T11:34Z** — Both lanes healthy. TEAMS 18,475→18,151 (-324), STANDINGS 22,355→22,031 (-324). FIXTURE_STATS
  40,969→40,399 (-570). Grand total 103,889 (core 4) + 98,922 (FIXTURE_STATS+LINEUPS). Both VMs confirmed RUNNING.
  Pulled in unrelated foreign commits cleanly (new issue docs + a workflow-extraction doc update, none touching this
  file).
- **2026-08-06T11:48Z** — Both lanes accelerating. TEAMS 18,151→17,343 (-808), STANDINGS 22,031→21,224 (-807).
  FIXTURE_STATS 40,399→39,396 (-1,003, new-ish record pace). Grand total 102,274 (core 4) + 97,919
  (FIXTURE_STATS+LINEUPS). Both VMs confirmed RUNNING.
- **2026-08-06T12:06Z** — Both lanes healthy, strong pace continues. TEAMS 17,343→16,390 (-953), STANDINGS 21,224→20,271
  (-953). FIXTURE_STATS 39,396→38,727 (-669). Grand total 100,368 (core 4, now under 101k) + 97,250
  (FIXTURE_STATS+LINEUPS). Both VMs confirmed RUNNING.
- **2026-08-06T12:24Z** — TEAMS/STANDINGS still strong: TEAMS 16,390→15,724 (-666), STANDINGS 20,271→19,605 (-666).
  FIXTURE_STATS slowed to 38,727→38,554 (-173, single data point — not yet a sustained decline, no switch action taken
  this tick). Grand total 99,036 (core 4, first time under 100k) + 97,077 (FIXTURE_STATS+LINEUPS). Both VMs confirmed
  RUNNING.
- **2026-08-06T12:43Z** — FIXTURE_STATS back to normal pace: 38,554→38,077 (-477), confirming last tick's -173 was
  one-off noise, not a sustained decline — no entity-switch needed. TEAMS 15,724→14,823 (-901), STANDINGS 19,605→18,704
  (-901). Grand total 97,234 (core 4) + 96,600 (FIXTURE_STATS+LINEUPS). Both VMs confirmed RUNNING.
- **2026-08-06T~13:05-13:20Z — OTHER-VENDOR BACKFILLS launched, operator explicit go-ahead received.** Operator
  clarified live-chat scope twice: (1) "we just need the prediction leagues... thats the mvp for those data sources...
  its api football that has an expanded list" — weather/sfi/footystats/understat's correct "MVP" denominator is each
  vendor's own Prediction-tier league set via `get_expected_leagues_for_source(source, ["Prediction"])`
  (`unified_api_contracts.canonical.domain.sports.league_data`), NOT api_football's wider 96-league
  `get_mvp_football_league_ids()` — those are two genuinely different lists; (2) rationale: "we predict on the
  prediction leagues, thats the odds_api data we have — no point having rich features for others; the extra AF leagues
  help with basic game summary + adjacent-game fatigue/injury context." Wrote
  `instruments-service/scripts/census_other_vendors_gap_2026_08_06.py` (mirrors the AF census script's denominator +
  resolved-status logic) and censused at Prediction-tier scope:
  - **WEATHER** (open_meteo, 34 leagues): needed=1 — essentially DONE, no launch.
  - **SFI_PROGRESSIVE_STATS** (34 leagues): needed=12 — essentially DONE, no launch.
  - **MATCHES/PREDICTIONS** (footystats, 29 leagues): needed=0 — DONE.
  - **ODDS** (footystats, 29 leagues): needed=1 — essentially DONE, no launch.
  - **XG/XG_SHOTS** (understat, 5 leagues): needed=0 — DONE.
  - **SFI_LEAGUES** (34 leagues): needed=20,068 of 22,132 expected (~91% missing!), range 2020-06-06..2026-08-02 — the
    ONE genuine large gap. Launched `sfi-backfill-20260806-140815` via
    `launch-sfi-backfill-vm.sh --entity SFI_LEAGUES 2020-06-06 2026-08-02` (single-stream — the launcher's own guard
    REFUSES `--chunks` for SFI: the RapidAPI key's 4 req/s limit is per-account, so N parallel chunks would 429-storm
    each other, confirmed via the launcher's own error message). No singleton-lock conflict with the AF campaign
    (different launcher family/API key). RUNNING confirmed. Launch logged a tarball-staleness WARNING
    (instruments-service manifest vs repo commit) that raced against this same tick's own census-script quickmerge — the
    only new commit was docs/tooling (the census script itself), zero core `instruments_service` package changes, so
    this is benign; not re-launched.
  - **odds_api** (MTDS, not instruments-service — different bucket, not covered by the census script above): its own
    launcher `launch-mtds-sports-odds-backfill-vm.sh` defaults to a HARDCODED `END_DATE=2026-03-28`, ~4 months stale vs
    today — launched a trailing-gap catchup `mtds-backfill-odds-catchup-20260806`
    (`--start 2026-03-28 --end 2026-08-06`, default unscoped = Prediction-tier only per the launcher's own doc comment,
    `--force` omitted so already-captured shards skip). `odds-api-guard` confirmed 0 running + 1 planned <= cap 1 before
    launch. RUNNING confirmed.
  - Both new VMs are independent lanes — different API keys/quotas from the af-backfill-* pool and the TEAMS/STANDINGS
    chunk-loop VM, genuinely concurrent, no lock contention. Monitor read-only alongside the existing two lanes going
    forward; SFI_LEAGUES is the long pole (single-stream over ~91% of a 6-year range) — expect this to run for a while,
    no need to babysit closely, just fold into the periodic VM-health check.
  - Census script shipped: `instruments-service@0bb2143d`. Campaign now has **4 concurrent VM lanes** (up from 2), all
    independent — af-backfill-20260806-022033 (FIXTURE_STATS), instr-backfill-sports-teams-20260805-055622
    (TEAMS/STANDINGS), sfi-backfill-20260806-140815 (SFI_LEAGUES), mtds-backfill-odds-catchup-20260806 (odds_api). After
    SFI_LEAGUES/odds_api complete, run `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh` to
    materialise empty_confirmed rows before declaring those entities done (per the SFI launcher's own instructions).
- **2026-08-06T14:20Z** — AF campaign resumed after the vendor-backfill detour (all 4 lanes confirmed RUNNING). TEAMS
  14,823→13,521 (-1,302), STANDINGS 18,704→17,402 (-1,302). FIXTURE_STATS 38,077→37,251 (-826). Grand total 94,630
  (core 4) + 95,774 (FIXTURE_STATS+LINEUPS). First background census attempt this tick failed (session cwd had drifted
  to unified-trading-pm from doc commits, `FileNotFoundError` on the relative script path) — fixed by always `cd`-ing
  explicitly into `instruments-service/` before invoking these scripts, never relying on stale cwd; retry succeeded
  cleanly.
- **2026-08-06T14:38Z — odds_api catchup VM OOM-killed, relaunched.** `mtds-backfill-odds-catchup-20260806` had
  disappeared from the VM list at this check — its `run.log` showed
  `CHUNK_FAILED: chunk=1/1 ... exit=137 reason=OOM_KILLED` at 13:29:02Z (rss climbed to ~30GB against the 32GB
  `e2-highmem-4` ceiling, then self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`) — matches the documented failure class
  in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`/the launcher's own header comment (odds_api fan-out has no
  aggregate byte-budget cap). Real progress had already been written before the crash (manifest shard showed 2,757
  entries, skip-if-fresh logging real SKIPs for already-captured dates), so a plain relaunch of the identical range is
  safe and resumes forward — relaunched as `mtds-backfill-odds-catchup-retry1-20260806`, confirmed RUNNING. If this
  recurs, the next lever is splitting the ~130-day range into 2-3 smaller sub-range VMs rather than one chunk covering
  the whole thing (not attempted yet — single retry first). AF campaign: TEAMS 13,521→12,663 (-858), STANDINGS
  17,402→16,544 (-858). FIXTURE_STATS 37,251→36,744 (-507). Grand total 92,914 (core 4) + 95,267
  (FIXTURE_STATS+LINEUPS). Condensed the 2026-08-04/08-05/early-08-06 blow-by-blow (05:38Z-02:18Z) into 3 short summary
  paragraphs above — doc was at 782 lines, now back to ~555.
- **2026-08-06T15:00Z — SFI_LEAGUES DONE; odds_api OOM'd a 2nd time, now splitting the range.** **SFI_LEAGUES completed
  successfully**: `sfi-backfill-20260806-140815`'s run.log shows
  `[[VM_PROGRESS]] last_completed_date=2026-08-02 monotonic=true`, `exit_code=0`, self-deleted cleanly — reached the end
  of its full 2020-06-06..2026-08-02 range in under 2 hours (much faster than the ~68-day single-stream estimate quoted
  in the launcher's own doc comment, which was for a denser per-match-granularity SFI workload; SFI_LEAGUES is
  comparatively lightweight per-date league metadata). Manifest rescan still owed before declaring this genuinely 0
  needed (queued as a todo). **odds_api retry1 also OOM-killed**, identical signature: `exit=137 reason=OOM_KILLED` at
  13:51:21Z, rss climbed to ~27GB before the kill, ~4.5min runtime — same as the first attempt. Two consecutive
  full-range OOMs now confirms this isn't one-off variance, so per the standing plan switched strategy: split the
  ~130-day range (2026-03-28..2026-08-06) into smaller sub-ranges instead of a 3rd blind full-range retry. Launched the
  first split, `mtds-backfill-odds-catchup-split1-20260806` (2026-03-28..2026-05-11, ~44 days) — launch confirmation
  still pending at journal time, will confirm RUNNING next tick; the remaining 2 sub-ranges (~05-12..06-25, ~06-26..
  08-06) queued to launch sequentially once this one completes or fails (the launcher's own `odds-api-guard` caps
  concurrent odds_api VMs at 1, so sequential is the safe default rather than `--allow-parallel`, which risks a
  429-storm on top of the memory issue). AF campaign: TEAMS 12,663→11,983 (-680), STANDINGS 16,544→15,864 (-680).
  FIXTURE_STATS 36,744→36,476 (-268, smaller than the recent ~500-900 range but a single data point — not yet 2
  consecutive sub-threshold ticks, no switch action taken). Grand total 91,554 (core 4) + 94,999
  (FIXTURE_STATS+LINEUPS). Both core AF lanes confirmed RUNNING.
- **2026-08-06T15:25Z — OPERATOR-DIRECTED DATA-INTEGRITY AUDIT: real findings, 2 fixes shipped, 1 correction to the
  SFI_LEAGUES claim above.** Operator asked to verify every campaign VM is genuinely capturing data, not silently
  accumulating `attempted_failed` rows. Checked per-VM manifest shards directly (not just log text) for all active/
  recent VMs:
  - **af-backfill (FIXTURE_STATS) + instr-backfill-sports-teams (TEAMS/STANDINGS): CLEAN.** Zero `attempted_failed` rows
    in either shard — only `captured`/`empty_confirmed`, exactly as expected.
  - **odds_api: real `attempted_failed` rows found (6,333 total across all history)** — every one shares the identical
    `error_reason`:
    `record_empty(reason=SOURCE_RETURNED_ZERO) rejected: ... catalog says 'trades' was ALIVE on <VENUE>/<DATE> ... this is a real fetch failure, not honest absence`,
    spread across all 23 bookmaker venues (WILLIAMHILL dominant at 1,592). Traced to an EXISTING, already-closed
    investigation (`sports_trades_venue_fetch_failed_2026_07_15.md`, `status: resolved`) that analyzed this exact guard
    signature and confirmed **WORKING AS DESIGNED**: `is_bookmaker_league_covered()` returns True for every one of these
    rows — each is a genuinely-covered (bookmaker, league) pair whose specific historical fixture needs a real re-fetch,
    not a coverage-scope bug or silent masking. Population has shrunk since that investigation (was 18,150 for the
    guard-specific slice on 07-15; now 6,333 total). **Correctly classified, not silently swept — no action needed
    beyond continuing to re-fetch, which the backfill campaign is already doing.**
  - **MAJOR CORRECTION to the "SFI_LEAGUES DONE" claim in the prior entry: `SFI_LEAGUES` is a RETIRED data_type**
    (`unified-api-contracts@b5210c2b`, 2026-05-05,
    `"feat(sports)!: retire TRANSFERMARKT_LEAGUES + SFI_LEAGUES as captured data types"` — catalog mapping now lives in
    UAC `SOCCER_FOOTBALL_INFO_IDS`, not captured data). All 12,469 SFI_LEAGUES manifest rows carry
    `error_reason=EXPECTED_DEPRECATED_DATA_TYPE`, dated `written_at=2026-07-13` (a bulk rebuild pass), zero rows written
    by today's backfill run. **My `census_other_vendors_gap_2026_08_06.py` script wrongly treated SFI_LEAGUES as a live
    entity — the earlier "20,068 needed" figure was a false positive, the exact same class of mistake as the AF LEAGUES
    entity earlier this campaign.** The real gap was always 0; the VM I launched (`sfi-backfill-20260806-140815`)
    correctly did nothing new against a defunct entity — not wasteful (SPOT, ran ~1.5hrs, cheap), but based on a flawed
    premise. Fixed: (1) `census_other_vendors_gap_2026_08_06.py` excludes SFI_LEAGUES now, shipped
    `instruments-service@d9a42d2e`; (2) `codex/02-data/sports-data-source-coverage-matrix.md`'s SFI table was missing
    the RETIRED annotation that the TRANSFERMARKT_LEAGUES row (same commit) already had — fixed, committed `87a60d43f8`.
    Sanity-checked `SFI_PROGRESSIVE_STATS` for the same class of bug — genuinely healthy (20,851 real `captured` rows,
    legitimate `empty_confirmed` reasons, only 89 `attempted_failed` — a `JSONDecodeError`, tiny — 384 rows written
    today), not affected.
  - **odds_api OOM investigation deepened: 3 consecutive OOMs, not range-size-dependent.** Confirmed
    `mtds-backfill-odds-catchup-split1-20260806` (the 44-day split from the prior entry) ALSO OOM-killed (`exit=137` at
    14:13:01Z, rss~25GB), crashing on the very FIRST fresh date it processed (2026-03-28) after writing real data for
    that date (14,087 rows, 20 shards — confirms genuine captures happen before the crash, not a silent failure). Since
    all 3 attempts (2 full-range + 1 44-day split) crash on essentially the same first-fresh-date pattern regardless of
    total range, splitting the range further wouldn't help — the bottleneck is per-date memory, not cumulative range
    size. Tried a bigger machine instead: `--machine-type e2-highmem-8` (64GB, up from e2-highmem-4/32GB) on the full
    range, launched as `mtds-backfill-odds-catchup-bigmem-20260806` — confirmed RUNNING. If this also OOMs, the next
    step is filing a proper issue doc (this is a genuine code-level gap — the launcher's own header comment already
    flags "no aggregate byte-budget cap" for odds_api's per-date (bookmaker, league, fixture) fan-out — not something
    further ops-level relaunching can fix).
  - AF campaign continues strong: TEAMS 11,983→9,996 (-1,987, first time under 10k), STANDINGS 15,864→13,877 (-1,987).
    FIXTURE_STATS 36,476→35,411 (-1,065, confirms last tick's -268 was noise, not a slowdown). Grand total 87,580
    (core 4) + 93,934 (FIXTURE_STATS+LINEUPS). Both core AF lanes confirmed RUNNING.
- **2026-08-06T16:13Z — REAL CODE FIX shipped for the odds_api OOM (operator: "dont just file doc fix it too").**
  Root-caused fully via the already-filed `sports_mtds_backfill_vm_unscoped_fetch_oom_2026_08_06.md`: an unscoped sports
  odds_api backfill's `OddsApiAdapter._fetch_all_leagues` (market-tick-data-service) iterates ALL ~30 Prediction-tier
  leagues in ONE Python process, accumulating every league's rows into a single in-memory list before writing — the
  confirmed OOM mechanism. Rather than touch the adapter's accumulation internals (a prior investigation explicitly
  judged that streaming-write refactor too risky for a live P0 — could convert a loud, honest OOM failure into a silent
  zero-row false-success), mirrored the already-proven `--league` scoping fix used on the LIVE dispatch path
  (`deployment-service@4e0e03d`) onto the VM backfill path instead: modified
  `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s `mtds-backfill` chunk-loop generation so that when
  `VM_ASSET_GROUP=sports` AND `VM_VENUE`/`VM_LEAGUE` are both empty (the exact unscoped case), it discovers the live
  Prediction-tier league list at boot and fans the chunk-loop out to one subprocess PER LEAGUE (each bounded to ~1/30th
  the memory of the unscoped call, each a fresh process so nothing carries over) instead of one process for all leagues
  at once. Every other launcher/asset_group/venue/explicitly-scoped sports run is byte-identical to before (verified).
  Preserves shard-level failure isolation (one league OOM-ing doesn't block its siblings) and the PROGRESS.json
  checkpoint's correctness guarantee (suppressed if ANY league in a chunk fails). Verified via hand-built bash test
  harnesses (3 scenarios: unscoped fallback, per-league fan-out, one-league-fails) AND the real pytest suite: fixed 5
  existing tests that broke (`${_SPORTS_LEAGUE_CSV:-}` default-safe pattern + one legitimate assertion-string update),
  added 4 new dedicated regression tests, full `quality-gates.sh` GREEN. Shipped via quickmerge (task bkgd b06mtwnjz,
  landing confirmation pending next tick). Separately, the ALREADY-RUNNING `mtds-backfill-odds-catchup-bigmem-20260806`
  (launched pre-fix on e2-highmem-8 as an ops-level mitigation) has held steady well past 15:12Z (rss cycling 5-31GB
  under the 64GB ceiling, past every point where e2-highmem-4 crashed 3x) — left running to completion independently;
  the code fix benefits every FUTURE unscoped odds_api launch going forward.
- **2026-08-06T16:31Z — code fix CONFIRMED landed.** The first quickmerge attempt for the fix had silently failed
  (`--files 'path1,path2'` comma-separated was misparsed — quickmerge requires SPACE-separated paths inside one quoted
  string, `--files "path1 path2"` — it concluded "already committed" from a false read and the files stayed genuinely
  uncommitted). Caught by directly checking `git status --porcelain`/`git log` rather than trusting the "completed" task
  notification alone. Retried with correct syntax — landed clean as `deployment-service@a0143b51`, verified via
  `git log -1 --oneline -- scripts/vm/setup-data-pipeline-vm.sh`. Marked
  `sports_mtds_backfill_vm_unscoped_fetch_oom_2026_08_06.md` resolved (unified-trading-pm@0ae3d1b334). Lesson carried
  forward for the rest of this campaign: always independently verify a quickmerge's real git effect, never trust the
  notification alone. AF campaign: TEAMS 8,287→7,872 (-415), STANDINGS 12,168→11,753 (-415). FIXTURE_STATS 34,154→33,671
  (-483). Grand total 83,332 (core 4) + 92,194 (FIXTURE_STATS+LINEUPS). All 3 VM lanes confirmed RUNNING.
