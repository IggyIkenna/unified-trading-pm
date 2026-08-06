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
    /plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /codex/02-data/mvp-scope-canonical.md,
    /plans/active/issues/manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md,
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
    /plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /codex/02-data/mvp-scope-canonical.md,
    /plans/active/issues/manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md,
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
| FIXTURE_STATS    | all-383 (widened 2026-07-28) | 66,291 expected (non-MVP), 174,674 already resolved, **48,432 needed** (flat 5 ticks, consolidator lag confirmed, trusted) — ACTIVE via `af-backfill-20260806-022033`         |
| FIXTURE_LINEUPS  | all-383 (widened 2026-07-28) | 66,291 expected (non-MVP), 52,372 already resolved, **58,531 needed** (denominator drift only — no backfill run yet)                                                          |
| **PLAYER_STATS** | **MVP-96**                   | 42,371 expected, 41,372 already resolved, **only 999 needed** — nearly done                                                                                                   |
| **INJURIES**     | **all-383**                  | 108,662 expected, 45,953 already resolved, **62,709 needed** (unchanged — no backfill run yet)                                                                                |
| **STANDINGS**    | **all-383**                  | 108,662 expected, 73,748 already resolved, **34,914 needed** (was 64,439 on 08-04, **-29,525**) — **ACTIVE** via a separately-discovered dedicated VM, see below              |
| **TEAMS**        | **all-383**                  | 108,662 expected, 77,624 already resolved, **31,038 needed** (was 64,723 on 08-04, **-33,685**) — **ACTIVE** via `instr-backfill-sports-teams-20260805-055622` (chunk ~31/76) |
| **LEAGUES**      | ~~all-383~~ **RETIRED**      | **RESOLVED 2026-08-03** — writer path killed 2026-05-07, **0 genuinely needed**. See below.                                                                                   |

Denominator = distinct `(date, league_id)` pairs with a captured `FIXTURES`/`FIXTURES_SCHEDULE` row (a genuine fixture
existed that day), intersected with each entity's own `get_entity_league_coverage()` scope — mirrors
`emit_empty_gaps_for_entity`'s own expected-set logic (`sports_reference_core.py:338-341`); a shard is resolved (not
needed) if `capture_status` is `captured` OR `empty_confirmed`. Full census:
`instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py` +
`census_fixture_stats_lineups_widening_volume_2026_07_31.py` (both UTL-client-backed, both fixed 2026-08-04).

**Grand total needed, 2026-08-06T05:29Z: 129,660 across PLAYER_STATS+INJURIES+STANDINGS+TEAMS** (was 192,877 on 08-04, a
further ~33% drop — mostly STANDINGS/TEAMS backlog draining via a separately-discovered dedicated VM, see Progress Log)
**+ 106,963 across FIXTURE_STATS+FIXTURE_LINEUPS** (48,432 + 58,531). TEAMS/STANDINGS and FIXTURE_STATS are BOTH
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
   `codex/02-data/sports-gcs-path-ssot.md:115` states outright that LEAGUES is "cross-league reference data where
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
- **2026-08-04T05:38Z** — Working the sports campaign monitoring loop (independent of the AO park, per the standing
  directive). `asia_northeast1_c_spot_preemption_storm_2026_08_04.md`'s slot-5 entry (04:44Z-05:16Z) found the real
  signal: the original cross-cutting storm (3 asset groups) genuinely subsided; what continues is a narrower pattern
  confined to `expected-universe-v2-sports-*` VMs specifically — **af-backfill itself has been preemption-free since
  01:21:48Z**. Independently re-verified via
  `gcloud logging read 'protoPayload.methodName="compute.instances.preempted" ... AND (protoPayload.resourceName:"af-backfill" OR protoPayload.resourceName:"af-audit")' --freshness=6h`:
  confirmed zero af-backfill/af-audit events since 01:21:48Z — over 4h clean at check time (05:38Z). Singleton lock
  free. Relaunched FIXTURE_STATS as `af-backfill-20260804-063845` (`--entity FIXTURE_STATS 2020-06-06 2026-08-04`, no
  `--force`) — confirmed RUNNING at launch. This is the 9th launch attempt today; unlike the prior 8, this one is backed
  by a genuine multi-hour clean window specific to this VM family, not just a lull in the aggregate zone rate. Note:
  launcher warned of 2 stale code tarballs (instruments-service, deployment-service) — not republished before this
  launch (time-sensitive to catch the clean window; the FIXTURE_STATS fetch path itself hasn't changed since the
  tarballs were built, so this is a low-risk gap, not blocking). Monitoring for a clean, non-preempted run.
- **2026-08-04T06:03Z** — Checked on `af-backfill-20260804-063845`. **Preempted at 05:41:34Z, ~2 min after launch** —
  despite the 4+ hour af-backfill-specific clean window that motivated the relaunch. **Correction to the prior entry's
  framing**: "af-backfill has been clean" was true of its PAST history but is not immunity — cross-referencing the full
  90-min preemption log shows this was the ONLY af-backfill hit in the window; every other event (13 total) is
  `expected-universe-v2-sports-*`, firing steadily every 2-14 min right through 05:52:59Z (just ~10 min before this
  check) — i.e. the narrower residual pattern flagged in the storm doc is still actively live, and while it's mostly
  hitting one VM-name family, the underlying capacity pressure evidently isn't perfectly isolated to that name (it
  caught af-backfill once too, right in the middle of the sports-VM pattern's continued firing). This matches slot-13's
  original caution (`asia_northeast1_c_spot_preemption_storm_2026_08_04.md`): zone-wide OR single-family aggregate
  history isn't sufficient evidence on its own for this `e2-standard-8` entity. **Did not immediately relaunch again** —
  the residual pattern needs to show genuine subsidence (not just af-backfill's own trailing history) before the next
  attempt. FIXTURE_STATS remains at 125/68,284 non-MVP shards (0.18%), unchanged — 9 attempts today, zero net progress.
- **2026-08-04T06:36Z — strategy shift, 10th relaunch.** `asia_northeast1_c_spot_preemption_storm_2026_08_04.md`'s
  slot-6 entry (06:07-06:10Z) extended the residual-pattern scope further: it now spans 3+ VM families
  (`expected-universe-v2-sports`, `tradfi-bf-cme-ohlcv-1m-*`, `instr-backfill-pred-pchk-*`) across 2 machine types
  (`e2-standard-8` AND `e2-standard-4`) and a 4th asset group (prediction) — a genuinely zone-wide, low-intensity (~1
  event/6min), persistent background rate, NOT a single-launcher-specific problem waiting to clear. **This changes the
  calculus**: waiting for "the whole zone quiet across every VM family for 30-60min" may not resolve for a long time if
  this is a standing background rate rather than a transient storm, and 9 attempts of "wait for evidence, then get
  unlucky anyway" hasn't produced net progress either way. Given (a) the af-backfill launcher is idempotent (skip-aware
  re-fetch, confirmed working correctly across every prior attempt today) and (b) the sub-tick auto-recovery fix
  (`deployment-service@7a2b28f92bc6d1f684d6c4d715d21da3a68d3c0a`, confirmed shipped + deployed) should now catch and
  auto-relaunch a fast preemption without requiring a human/agent to notice and manually re-launch every time — the more
  practical posture is to accept the residual background risk and relaunch now, letting auto-recovery absorb further
  preemptions if any land, rather than continuing to gate on an increasingly-unlikely "fully clean zone" signal.
  Relaunched as `af-backfill-20260804-073723`, confirmed RUNNING. Will monitor for either genuine progress or
  auto-recovery actually firing on a future preemption (a live test of the fix, useful either way).
- **2026-08-04T07:01Z — root cause found and fixed; first genuinely healthy run today.** The residual pattern's real
  root cause was found and fixed by slot-5 (`asia_northeast1_c_spot_preemption_storm_2026_08_04.md`, now fully resolved
  and archived): `expected-universe-v2-sports`'s own per-chunk retry loop had ZERO backoff on confirmed preemption,
  immediately re-launching into the same just-reclaimed SPOT slot — and `launch-api-football-backfill-vm.sh`
  (af-backfill) defaults to the SAME `e2-standard-4` machine type when unset, so the two launchers were colliding on one
  constrained SPOT pool, not two independent ones. Backoff fix shipped `deployment-service@1861cbe`. Checked
  `af-backfill-20260804-073723` at 07:01Z (~24 min after launch): **still RUNNING** — already far outlasting every one
  of today's prior 9 attempts (which died in 1.5-17 min) — zero failure signatures, healthily processing date=2020-08-03
  (up from the 2020-06-06 start). Re-census shows 125/68,284 non-MVP shards still (unchanged) — not yet concerning,
  since a fresh restart always re-walks already-captured early dates before reaching genuinely new ground; the
  durability itself is the real signal here. Continuing to monitor.
- **2026-08-04T07:37Z** — `af-backfill-20260804-073723` was preempted at 07:16:29Z after a **38-minute lifetime** —
  dramatically better than any of the 9 prior attempts (best before this was ~17min), strong confirmation the backoff
  fix genuinely helped. No successor VM appeared after ~20 min (auto-recovery did not fire for this normal-tick
  preemption; separate from the sub-tick gap already fixed — not investigated further here, flagged for whoever next
  touches auto-recovery). Manually relaunched as `af-backfill-20260804-084714`, confirmed RUNNING. **Open question
  raised, not yet resolved**: re-census after the 38-min run STILL showed 125/68,284 non-MVP shards — genuinely zero new
  captures despite real fetch activity (run.log showed regular `EXPECTED_NO_PROVIDER_COVERAGE` skips for out-of-coverage
  non-MVP league fixtures). Read `census_fixture_stats_lineups_widening_volume_2026_07_31.py`'s source: it only counts
  `capture_status=="captured"` rows as done, with ZERO accounting for `empty_confirmed` (honest-absence) rows — the same
  blind-spot class as the LEAGUES miscount resolved earlier in this doc. If a meaningful fraction of the 68,284 "needed"
  shards are actually already-resolved `EXPECTED_NO_PROVIDER_COVERAGE` cases, the true remaining volume could be much
  smaller than assumed all day. **Not yet confirmed** — a live `capture_status` value-count query for FIXTURE_STATS has
  been running 10+ min without returning (heavy concurrent manifest-read contention today), so this is flagged as an
  open investigation, not a confirmed finding. Also noted: the launcher's own output says "after completion, rerun the
  rescan to materialise empty_confirmed rows" (`launch-sports-manifest-rescan-vm.sh`) — it's possible these gaps aren't
  even materialized as `empty_confirmed` yet without that separate rescan step, which would mean the census isn't wrong
  per se, just measuring a state that hasn't been finalized. Do not assume either direction until the pending query
  resolves or someone re-checks.
- **2026-08-04T08:31Z — CONFIRMED, campaign-wide census bug, both scripts fixed.** The `capture_status` breakdown is now
  in: **FIXTURE_STATS** `empty_confirmed=266,758 expected_unattempted=127,600 captured=37,024`. Ran the same check for
  the other 5 remaining entities — **every one shows the identical pattern**: FIXTURE_LINEUPS
  `empty_confirmed=228,117 expected_unattempted=153,761 captured=42,539`; PLAYER_STATS
  `empty_confirmed=399,716 captured=26,787 expected_unattempted=1,768`; INJURIES
  `empty_confirmed=295,481 expected_unattempted=202,453 captured=10,337`; STANDINGS
  `expected_unattempted=195,080 empty_confirmed=191,514 captured=117,373`; TEAMS
  `captured=445,266 expected_unattempted=197,025 empty_confirmed=26,864` (TEAMS is the one exception where `captured`
  already dominates, consistent with it being observed as ~1 API call per league rather than per fixture-date). **Both
  census scripts** (`census_fixture_stats_lineups_widening_volume_2026_07_31.py` and my own
  `census_all_af_entities_completion_2026_08_03.py`) only counted `capture_status=="captured"` as resolved, with zero
  accounting for `empty_confirmed` — silently counting hundreds of thousands of already-resolved honest-absence shards
  as still needed, for every entity except LEAGUES (already separately fixed) and possibly TEAMS (where the effect is
  smaller since captured already dominates). **Fixed both scripts** to treat
  `capture_status in {"captured", "empty_confirmed"}` as resolved (also routed the widening script's manifest read
  through the UTL storage client instead of a bare `gs://` reader, matching the reliability fix already applied
  elsewhere this campaign). Re-running both corrected scripts now (background, heavy manifest-read contention today is
  making single reads take 5-10+ min) to get the TRUE remaining volume for all 6 affected entities before launching or
  continuing any further backfills against the old, inflated numbers. **Do not trust the
  68,284/68,290/17,440/100,745/84,947/67,741 figures elsewhere in this doc until the corrected re-census lands** — they
  are very likely substantial overstatements. FIXTURE_STATS VM relaunched again (13th attempt,
  `af-backfill-20260804-093140`) after two more short preemptions (12th attempt `-091624` ~5.4min); this remains a
  separate, already-understood SPOT-variance issue, not blocked on the census fix.
- **2026-08-04T09:00Z-11:42Z (condensed)** — Attempts 14-15 alternated FIXTURE_STATS/PLAYER_STATS, landing in the 3-14
  min range each time (best: attempt 14 survived ~13.5min). PLAYER_STATS's first 2 tries this window (`-102139` ~3min,
  `-105027` ~2.7min) showed zero census movement — established the alternating-on-2-consecutive-shorts strategy used for
  the rest of the session. Full blow-by-blow superseded by the summary table + later entries below.
- **2026-08-04T12:12Z** — PLAYER_STATS's 3rd attempt ran ~9 min (10:43:55Z→10:52:56Z) — best PLAYER_STATS run yet, and
  **real confirmed progress**: re-census shows PLAYER_STATS dropped 1,006→998 needed (8 shards resolved). First genuine
  forward movement on PLAYER_STATS today. Given real progress, relaunched PLAYER_STATS again immediately (favoring it
  over the strict alternation) — first attempt hit a genuine **STOCKOUT** (not a preemption):
  `does not have enough resources available... 'NULL:0/NULL:0/NULL:0 (state:STOCKOUT...)'` for `e2-standard-8` in
  `asia-northeast1-c` (error suggested `asia-northeast1-b`/`asia-northeast1-a` as alternatives — the launcher hardcodes
  the zone, no CLI override available, not changed given this is a shared-launcher zone choice outside this task's scope
  to unilaterally alter). Retried once — succeeded (`af-backfill-20260804-121224`, RUNNING), confirming the stockout was
  momentary, not sustained. This STOCKOUT (as distinct from a post-launch preemption) is a genuinely new data point for
  the zone's capacity pressure — worth a mention if anyone picks up the residual `expected-universe-v2-sports`
  investigation again, though not pursued further here.
- **2026-08-04T12:37Z** — Two more short attempts (`-121224` ~51s, `-121839` ~2.3min). Checked the broader zone-wide
  preemption rate to rule out a resurging storm before continuing to just relaunch blindly: only 13 events in the
  trailing 60min, no dense clustering — confirms this is still the same low, sustained background rate already
  documented (not a new crisis). Relaunched PLAYER_STATS again (`af-backfill-20260804-123759`), confirmed RUNNING.
- **2026-08-04T12:46Z** — `-123759` also landed short (~3.6min, 11:39:06Z→11:42:45Z preempted). That's 2 consecutive
  short PLAYER_STATS preemptions since the last confirmed-progress run, so per the alternating strategy switched the
  singleton lock to FIXTURE_STATS rather than a 3rd blind PLAYER_STATS retry — launched `af-backfill-20260804-124609`,
  confirmed RUNNING. Launch emitted a stale-tarball warning for instruments-service (tarball @87682dd98 vs repo
  @579421bf, i.e. the census-fix commit) — not republished: the backfill VM runs the AF fetch/writer path, not the
  standalone census scripts the fix touched, so this is not expected to affect this run's correctness; noting it in case
  a future launch on this VM needs newer instruments-service code for an unrelated reason.
- **2026-08-04T13:09Z** — `-124609` also landed short (~4.6min, 11:47:36Z→11:52:13Z preempted; only 1st FIXTURE_STATS
  attempt this switch, not yet 2-in-a-row). Zone-wide preemption count jumped 13→31 events/60min — checked the actual
  event list rather than just the count: the increase is a dense burst of `tradfi-bf-*` preemptions (16 events across 8
  VM names in a ~4min window, 12:03-12:07Z), a **different machine-type pool** (`e2-highmem-16`, a large concurrent
  tradfi backfill fleet launch) from ours (`e2-standard-8`) — not evidence our own pool is under fresh pressure, just a
  separate fleet's contention sharing the same zone. Not investigated further (out of this campaign's scope; the
  resolved `asia_northeast1_c_spot_preemption_storm_2026_08_04.md` doc is the right home if anyone picks that up).
  Relaunched FIXTURE_STATS once more (`af-backfill-20260804-130914`), confirmed RUNNING.
- **2026-08-04T13:37Z — MAJOR FINDING, separate issue doc filed.** (`-130914` ran ~11min, immediate re-census showed
  zero movement; initial "ordinary consolidator lag" theory superseded by this finding.) After `-133748` ran 22+ min
  with the consolidator STILL showing zero canonical movement, dug into the actual
  `uts-prod-manifest-consolidator-instruments-sports` Cloud Run job execution logs (not just scheduler health). **The
  consolidator's canonical `rows_out` has been frozen at exactly 9,239,513 for 5+ hours (2026-08-04T08:06Z→13:08Z+),
  across ~35+ successful merges**, despite processing 3-15 shards and 187-2,000,000 `dedup_dropped` rows every single
  cycle — the arithmetic (`dedup_dropped = rows_in - rows_out`) holds exactly every time, meaning every row entering the
  merge across the ENTIRE sports-prd bucket (not just AF — enrichment crons, fixtures schedules, other backfills all
  write here) is being classified as a duplicate and dropped, not merged in. This is NOT the previously-resolved
  staleness/loud-fail issue — this consolidator reports `success=True error=-` every cycle, believing it's working
  normally; the existing liveness watchdog only checks heartbeat age, not output growth, so it wouldn't catch this.
  Filed `manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md` with full evidence/repro steps — out of
  this campaign's scope to root-cause (needs someone with context on `manifest_consolidator.py`'s merge/dedup logic).
  **Practical implication for this campaign**: keep launching backfills (real data keeps accumulating durably, confirmed
  independent of this bug), but census-confirmed convergence cannot be truthfully declared for ANY entity in this doc
  while the consolidator stays frozen — treat every "needed" figure in this doc as a stale floor, not current truth,
  until that issue resolves. Relaunched FIXTURE_STATS again regardless.
- **2026-08-05T00:30Z** — Two findings this check. (1) Consolidator: `rows_out` ticked +1 (9,239,513→9,239,514) around
  18:55Z on 08-04, then re-froze at the new value through at least 00:22Z on 08-05 (5.5+ hrs, ~35+ more merges) — not a
  recovery, reinforces the original finding (full detail in the issue doc's update). (2) `af-backfill-20260804-145154`
  (the singleton lock's last occupant) was preempted at **14:13:36Z on 08-04 after a decent ~20min run** — and the lock
  sat **completely idle for 10+ hours** until this check, no VM running the whole time. Relaunched immediately
  (`af-backfill-20260805-013103`), confirmed RUNNING. Root cause of the idle gap not investigated (outside this doc's
  scope to diagnose the scheduling mechanism itself) — noting it so a future tick doesn't assume continuous coverage
  between Progress Log entries.
- **2026-08-05T16:04Z-16:09Z — genuine re-census movement, second (bigger) idle gap, venv incident, all closed out.**
  Four things this check: (1) **Second idle gap, worse than the first**: `af-backfill-20260805-013103` was preempted at
  00:54:37Z after a ~23min run, and the lock sat idle **15+ hours** (vs. 10+ hours last time) until this check —
  relaunched immediately (`af-backfill-20260805-171010`). This is now a recurring pattern (2 occurrences, growing) worth
  flagging even though its root cause (a scheduling/session-continuity gap, not this doc's mechanism to fix) is out of
  scope here. (2) **Consolidator: genuine bursty recovery, not a fix** — `rows_out` grew 9,241,283→9,270,239 (+28,956)
  over ~14.5h, in bursty stuck-then-active cycles rather than a clean resolution; full detail in the issue doc's
  2026-08-05T16:04Z update. (3) **First real census movement in over a day**: FIXTURE_STATS needed dropped 56,940→56,646
  (-294, genuine, from this campaign's own backfills). STANDINGS (64,439→51,740, -12,699) and TEAMS (64,723→47,020,
  -17,703) dropped dramatically too, despite **zero AF backfill VMs ever launched against either entity this campaign**
  (verified via `gcloud compute operations list` — no such launches) — almost certainly backlogged work from other
  routine sports jobs (enrichment/fixtures-schedule crons) draining through as the consolidator catches up, not a
  parallel dispatch to coordinate with. Summary table above updated to the 2026-08-05 figures. (4)
  **instruments-service's `.venv` was genuinely missing** (confirmed via `ls`, sibling repos had theirs intact) — fixed
  via `uv sync` per the documented troubleshooting step (`per-tab-worktrees.md` § Troubleshooting), not investigated
  further since the fix worked cleanly. **Given STANDINGS/TEAMS are now closer to done than
  FIXTURE_STATS/FIXTURE_LINEUPS (51,740/47,020 vs. 56,646/58,523), worth reprioritizing them once the current entity
  stalls** — updated todos below.
- **2026-08-05T17:03Z** — `af-backfill-20260805-171010` still healthy, ~53min elapsed, no reason to interrupt. Re-census
  confirms continued real FIXTURE_STATS progress (56,646→56,403, -243 further) from this run specifically. Every other
  entity unchanged since the last check — the earlier STANDINGS/TEAMS jump was a one-time backlog drain, not an ongoing
  trend; only actively-backfilled entities move now. No consolidator or idle-gap news this check.
- **2026-08-05T17:03Z (correction)** — Found a pre-existing, already-RESOLVED sister doc
  (`sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`) that investigated the EXACT same "frozen rows_out"
  symptom on this same consolidator 5 days earlier and, via a live pause+snapshot+probe diagnostic, proved it's the
  **expected signature of legitimate idempotent absorption**, not data loss (`dedup_dropped` is _derived_ as
  `rows_in - rows_out`, not independently measured — the two "corroborating" numbers are one statement, not two).
  **Downgraded `manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md` to `likely-false-alarm` / P3**
  accordingly — I made the identical reasoning error the 07-29 doc's own original (later-disproven) report made. **This
  does NOT affect anything in THIS doc** — the census figures above read the canonical directly and their movements
  track real backfill activity regardless of whether the "stuck" periods were a bug or expected no-op re-merges; every
  needed-count and progress claim in this doc stands as-is.
- **2026-08-05T17:34Z-18:32Z (condensed)** — `af-backfill-20260805-171010` kept running healthily through this whole
  window (83.5min→142min elapsed), producing the campaign's most consistent steady progress: FIXTURE_STATS
  56,403→54,810→53,692→52,515→51,438 across 4 checks (~1,000-1,600 shards/check). STANDINGS/TEAMS ticked down a bit
  early in the window (51,740→51,114, 47,020→46,786) then went flat — confirms the earlier "backlog drain" was a
  continuing-but-decaying trickle, not a clean one-time event, and it appears to have settled now. PLAYER_STATS/INJURIES
  unchanged throughout (no backfill run against either).
- **2026-08-05T18:52Z** — `af-backfill-20260805-171010` still healthy, ~161.7min elapsed (still going), left running.
  **FIXTURE_STATS crossed below 50,000 needed for the first time**: 51,438→49,734 (-1,704). Total genuine progress since
  this VM launched: 56,940→49,734, a 12.7% reduction in one continuous run. Everything else flat.
- **2026-08-05T19:11Z-20:13Z — deliberate entity switch.** FIXTURE_STATS's rate at ~180min elapsed clearly slowed:
  49,734→49,442, only -292 (vs. ~1,000-1,700/check earlier in this same run). Rather than let a diminishing-returns run
  keep occupying the singleton lock while TEAMS (46,786 needed) sits completely untouched, deliberately stopped the
  still-healthy VM (`gcloud compute instances delete af-backfill-20260805-171010`) and launched TEAMS
  (`af-backfill-20260805-201310`), confirmed RUNNING. FIXTURE_STATS ends this stretch at 49,442 needed (from 56,940 —
  7,498 shards resolved, ~13.2% of its total, over one ~3-hour run). Will return to FIXTURE_STATS/FIXTURE_LINEUPS after
  TEAMS/STANDINGS.
- **2026-08-05T19:53Z-20:12Z** — TEAMS shows persistent zero census movement (~39min then ~58min, both checks) — unlike
  every other entity's early runs. Verified via the run.log both times rather than assume something's wrong: genuine
  real work confirmed and CONTINUING (per-VM shard grew 41,418→67,496 total entries between the two checks, now
  processing dates into September 2020). This is purely consolidator-absorption lag for this specific VM's shard, not a
  stall or failure — the underlying data is real and growing steadily. Left running; expect the next census check to
  finally show the accumulated progress once a merge cycle picks up this shard.
- **2026-08-05T20:32Z — TEAMS finally shows real movement, plus a useful pairing insight.** ~78min elapsed. TEAMS:
  46,786→46,593 (-193). **STANDINGS also moved (51,114→50,628, -486) despite no dedicated STANDINGS VM ever being
  launched** — the run.log shows this "TEAMS-only" scoped VM also logs `STANDINGS presence-guard` checks and fetches
  standings from cache every date, confirming TEAMS and STANDINGS are processed together as paired "core" per-date
  entities regardless of the `--entity` scoping flag (which appears to only govern the separate per-fixture entities
  like FIXTURE_STATS/PLAYER_STATS/INJURIES). **Practical implication: this TEAMS run is already advancing STANDINGS for
  free** — may not need a separate dedicated STANDINGS launch at all if this run continues; will re-evaluate once TEAMS
  converges or this run ends.
- **2026-08-05T20:51Z-01:03Z (condensed)** — `af-backfill-20260805-201310` ran continuously through this whole stretch
  (97min→409min elapsed, past 6.8hrs by the end). TEAMS/STANDINGS dropped in lockstep throughout (paired-entity
  mechanism confirmed repeatedly): 46,457→46,333→46,013→45,378→44,447→43,569→42,549→41,690→41,206 (TEAMS), STANDINGS
  mirroring exactly. Included one 5-check flat stretch (21:28Z-22:28Z, ~117min→194min elapsed) verified via run.log to
  be genuine consolidator-absorption lag, not a stall (VM kept advancing through real dates, per-VM shard grew
  substantially) — followed by a strong catch-up burst once the consolidator processed the backlog. From 00:26Z onward
  the per-tick delta began a genuine decline (1,020→859→484), tracked closely since it was approaching the established
  ~300-400/check switch threshold. Grand total dropped from 152,680 to 149,994 across this stretch. _(context-scout also
  populated context_scope frontmatter on this doc during this window — harmless, unrelated.)_
- **2026-08-06T01:16Z-01:25Z — SWITCH: TEAMS/STANDINGS paused, FIXTURE_STATS resumed.** 4th consecutive tick confirmed
  the trend below threshold: TEAMS 41,206→40,941 (-265), STANDINGS 45,080→44,815 (-265). Verified via run.log before
  acting (not just assuming): the VM was genuinely still advancing through real dates (~1 date/40s, into Nov 2021,
  `[[VM_PROGRESS]] monotonic=true` markers present), but presence-guard log lines showed most dates in this window are
  cache-hits with per-league data already substantially captured — a real diminishing-returns pattern (same shape as
  FIXTURE_STATS's earlier slowdown), not a stall or bug. Given the exceptional ~7hr run already extracted (TEAMS
  66,113→67,721 resolved, STANDINGS 62,239→63,847 resolved just this window) and the confirmed sub-threshold rate,
  stopped `af-backfill-20260805-201310` (`gcloud compute instances delete`) and launched FIXTURE_STATS
  (`af-backfill-20260806-022033`, confirmed RUNNING) to resume its paused 49,442-needed backlog. Grand total across the
  4 in-scope entities now 149,464 (TEAMS/STANDINGS paused at 40,941/44,815). Noted in passing: the launcher flagged a
  "stale tarball" warning for instruments-service, checked and it was a single CI-config-only commit
  (`fix(ci): revert to GitHub-hosted runners`) unrelated to backfill logic — non-issue, no action needed.
- **2026-08-06T01:41Z** — First check on the new FIXTURE_STATS VM (`af-backfill-20260806-022033`, ~17min elapsed,
  RUNNING): 49,442→48,432 needed (-1,010), a strong resumed start. FIXTURE_LINEUPS denominator drifted +8
  (66,283→66,291, new days rolling into scope, no backfill run against it). TEAMS/STANDINGS also kept draining despite
  the VM being stopped (TEAMS 40,941→40,408 -533, STANDINGS 44,815→44,282 -533) — expected trailing consolidator
  absorption of that VM's final per-VM shard, not new work. Grand total 148,398 (core 4) + 106,963 (FIXTURE_STATS +
  LINEUPS). Left FIXTURE_STATS running.
- **2026-08-06T01:59Z** — FIXTURE_STATS census read completely flat (48,432 needed, unchanged) after ~35min elapsed —
  verified via run.log rather than assume anything: genuinely active, real API calls fetching fixture-stat rows every
  ~0.6s throughout the window, confirmed not a stall, purely consolidator-absorption lag on this VM's per-VM shard.
  TEAMS/STANDINGS continued their trailing drain for a 2nd tick post-stop, and the delta grew rather than shrank (TEAMS
  40,408→39,678 -730, STANDINGS 44,282→43,552 -730, vs -533 last tick) — still consistent with the same
  per-VM-shard-absorption mechanism (the consolidator cron can batch a larger chunk of the leftover shard in one cycle
  than another), not treated as a new concern; will keep an eye out but not investigating further unless it persists
  past another tick or two. Grand total 146,938 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Left FIXTURE_STATS running.
- **2026-08-06T02:18Z — CORRECTION: TEAMS/STANDINGS were never actually paused.** The "trailing consolidator absorption"
  explanation for continued TEAMS/STANDINGS drainage (2 prior ticks, growing delta 533→730→886 on this tick) was wrong —
  investigated because a 3rd consecutive tick of growing post-stop drainage crossed the standing "worth a closer look"
  threshold. Widened the VM search beyond the `af-backfill-*` name filter this doc has used all campaign and found
  **`instr-backfill-sports-teams-20260805-055622`**, RUNNING continuously since **2026-08-05T05:59:14Z** (~20.3hrs by
  this check) — a separate, dedicated, chunked TEAMS backfill (`instruments_chunk_loop.sh`, 76 chunks covering
  2020-06-06→2026-08-06, `Entity-scoped mode: restricting to TEAMS only`, currently at chunk 29/76 ≈ Oct 2022) launched
  via a different script/naming convention than the `launch-api-football-backfill-vm.sh` → `af-backfill-*` pool this doc
  has been actively managing. This VM — not consolidator lag — has been the real, continuous driver of TEAMS/STANDINGS
  progress this entire session (likely concurrently with `af-backfill-20260805-201310` for the portion of this window
  before that VM was stopped). Checked for similar hidden VMs against FIXTURE_LINEUPS/INJURIES/PLAYER_STATS
  (`name~'instr-backfill' OR name~'sports'` across all VMs) — found none; those three are confirmed genuinely untouched
  as documented. **Implication for the "singleton lock" model**: it was incomplete — there can be (and have been) two
  concurrent API-Football-consuming VMs at once (this dedicated TEAMS chunk-loop + whatever's in the `af-backfill-*`
  pool), sharing the same vendor quota rather than being mutually exclusive. This doesn't invalidate the earlier switch
  decision (FIXTURE_STATS redirect was still reasonable given that VM's own declining rate), but it does mean
  TEAMS/STANDINGS should be reclassified ACTIVE, not PAUSED, and this VM should be included in VM-state checks going
  forward (`name~'af-backfill' OR name~'instr-backfill-sports'`). At current pace (29/76 chunks in ~20.3hrs) this TEAMS
  VM has roughly another 30+ hours to run before its full 2020-2026 sweep completes — no action needed, just monitor
  read-only alongside the af-backfill-* pool. Census this tick: TEAMS 39,678→38,792 (-886), STANDINGS 43,552→42,666
  (-886). Grand total 145,166 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Also condensed the 2026-08-05T20:51Z-01:03Z
  block of per-tick entries above into one summary paragraph (doc was at 643 lines).
- **2026-08-06T02:41Z** — Both lanes checked fresh and both healthy. FIXTURE_STATS census read flat for a 3rd
  consecutive tick (48,432, unchanged) — re-verified via run.log one final time: confirmed genuinely active via
  `[[VM_PROGRESS]] last_completed_date=...` markers advancing monotonically (2020-09-16→2020-10-02 within this log
  window), not a loop (the handful of repeated fixture IDs seen in raw log lines were retry/sub-entity noise within the
  same date, not the VM stuck on one date). This is now confirmed 3x — treating flat FIXTURE_STATS readings as expected
  consolidator lag going forward without further run.log re-verification, per the accepted-characteristic rule.
  Dedicated TEAMS VM continued strong: TEAMS 38,792→37,874 (-918), STANDINGS 42,666→41,750 (-916, near-identical to
  TEAMS but not exactly, presumably a minor independent presence-guard skip difference — not concerning). Grand total
  143,332 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T02:59Z** — Both lanes healthy. TEAMS 37,874→36,884 (-990), STANDINGS 41,750→40,760 (-990) — continued
  steady progress via the dedicated VM. FIXTURE_STATS flat for a 4th tick (48,432, unchanged) — not re-verifying per the
  accepted-characteristic rule established last tick (this matches the earlier 5-tick flat stretch seen with the same VM
  type; expect a catch-up burst eventually). Grand total 141,352 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Both VMs
  left running.
- **2026-08-06T03:18Z** — Both lanes healthy. TEAMS 36,884→36,199 (-685), STANDINGS 40,760→40,075 (-685) — continued
  steady progress. FIXTURE_STATS essentially still flat for a 5th tick (48,432 needed, resolved ticked +1 to 174,674 —
  negligible, consistent with expectations). Grand total 139,982 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Both VMs
  left running.
- **2026-08-06T04:51Z** — Longer-than-usual gap since the last tick (~93min, vs. the standard ~15-20min cadence).
  TEAMS/STANDINGS made strong accumulated progress over that window: TEAMS 36,199→33,173 (-3,026), STANDINGS
  40,075→37,049 (-3,026). FIXTURE_STATS now flat for a 6th consecutive tick — the longest flat stretch of the campaign —
  so re-verified via run.log once more given the extended duration: confirmed genuinely active, VM_PROGRESS date markers
  advanced from 2020-10-02 (last verified) all the way to 2021-03-27 (~176 days of real processed dates) while the
  manifest count stayed frozen — a much larger unabsorbed backlog than any prior flat stretch, but the mechanism is
  identical (per-VM-shard-to-canonical consolidator lag) and clearly not a stall. Expect an unusually large catch-up
  burst whenever the consolidator processes this shard. Grand total 133,930 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS).
  Both VMs left running.
- **2026-08-06T05:11Z** — Both lanes healthy. TEAMS 33,173→31,994 (-1,179), STANDINGS 37,049→35,870 (-1,179) — continued
  steady progress. FIXTURE_STATS flat for a 7th tick (48,432, unchanged) — within tolerance of the accepted pattern, not
  re-verifying. Grand total 131,572 (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Both VMs left running.
- **2026-08-06T05:29Z** — Both lanes healthy. TEAMS 31,994→31,038 (-956), STANDINGS 35,870→34,914 (-956) — continued
  steady progress. FIXTURE_STATS flat for an 8th tick (48,432, unchanged) — still within tolerance. Grand total 129,660
  (core 4) + 106,963 (FIXTURE_STATS+LINEUPS). Both VMs left running.
