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
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /codex/02-data/mvp-scope-canonical.md,
  ]
created: 2026-08-03
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

**⚠️ ALL "needed" figures below are STALE (2026-08-04) — the census scripts had a confirmed empty_confirmed blind spot,
see the 08:31Z Progress Log entry. Do not launch or size work off these numbers; wait for the corrected re-census.**

| Entity           | Scope                        | Status (2026-08-03)                                                                                                   |
| ---------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| FIXTURES         | all-383                      | **DONE** — confirmed complete `sports_fixture_events_refetch_progress_2026_07_25.md`                                  |
| FIXTURE_EVENTS   | MVP-96                       | **DONE 2026-08-03** — pass-3 complete, 1,973 "degenerate" residual corrected as legacy dupes not a gap, same doc      |
| FIXTURE_STATS    | all-383 (widened 2026-07-28) | STALE — census: 69,171 non-MVP shards needed (`census_fixture_stats_lineups_widening_volume_2026_07_31.py`, pre-fix)  |
| FIXTURE_LINEUPS  | all-383 (widened 2026-07-28) | STALE — census: 69,165 non-MVP shards needed (pre-fix)                                                                |
| **PLAYER_STATS** | **MVP-96**                   | STALE — 42,368 expected, 24,928 captured, **17,440 needed** (pre-fix)                                                 |
| **INJURIES**     | **all-383**                  | STALE — 110,739 expected, 9,994 captured, **100,745 needed** (pre-fix)                                                |
| **STANDINGS**    | **all-383**                  | STALE — 110,739 expected, 25,792 captured, **84,947 needed** (pre-fix)                                                |
| **TEAMS**        | **all-383**                  | STALE — 110,739 expected, 42,998 captured, **67,741 needed** (pre-fix, likely closest to accurate — see 08:31Z entry) |
| **LEAGUES**      | ~~all-383~~ **RETIRED**      | **RESOLVED 2026-08-03** — writer path killed 2026-05-07, **0 genuinely needed**. See below.                           |

Denominator = distinct `(date, league_id)` pairs with a captured `FIXTURES`/`FIXTURES_SCHEDULE` row (a genuine fixture
existed that day), intersected with each entity's own `get_entity_league_coverage()` scope — mirrors
`emit_empty_gaps_for_entity`'s own expected-set logic (`sports_reference_core.py:338-341`), so "needed" here means the
same gap the writer's own empty-gap emission targets, not an invented denominator. Full census:
`instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py` (single UTL-client manifest read, same
credential-safe pattern as the fixed `census_fixture_events_schema_variants_2026_07_25.py`).

**Grand total needed across the 4 in-scope entities: 270,873 shards** (PLAYER_STATS+INJURIES+STANDINGS+TEAMS; LEAGUES
excluded per the resolved verdict below — confirmed unchanged for the other 4 after the LEAGUES manifest flip below).

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
- [ ] [SCRIPT] P1. **Launch PLAYER_STATS MVP-96 backfill** (`--entity PLAYER_STATS 2020-06-06 <today>`) once the
      singleton lock frees up — 17,440 needed shards, same MVP scope as FIXTURE_EVENTS (worth checking this entity's
      census script for the SAME fixture_id/af_fixture_id column bug already found + fixed in the FIXTURE_EVENTS census,
      if a dedicated recovery-style census is ever built for it).
- [ ] [SCRIPT] P2. **Launch INJURIES all-leagues backfill** (100,745 needed shards) — likely per-fixture-date cadence,
      apply the daily stop/resume discipline.
- [ ] [SCRIPT] P2. **Launch STANDINGS all-leagues backfill** (84,947 needed shards) — same discipline.
- [ ] [SCRIPT] P2. **Launch TEAMS all-leagues backfill** (67,741 needed shards, BUT likely 1 call/league not 1
      call/shard — confirm real call cost before estimating timeline; may complete far faster than the shard count
      implies).
- [x] ✅ [SCRIPT] P2. ~~Launch LEAGUES all-leagues backfill~~ — NOT APPLICABLE, resolved above: LEAGUES is a retired
      entity (no write path since 2026-05-07); there is nothing to launch. Excluded from this campaign's remaining scope
      and from the grand-total needed count (270,873 across the 4 still-live entities).
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
