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
    instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py,
    deployment-service/scripts/vm/launch-api-football-backfill-vm.sh,
    instruments-service/scripts/census_other_vendors_gap_2026_08_06.py,
    /codex/02-data/mvp-scope-canonical.md,
    /plans/archive/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /plans/archive/issues/manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md,
  ]
---

> **🟡 CROSS-PLAN BANNER (added 2026-08-08) — an IS data_type vocabulary migration is inbound and is GATED ON THIS
> DOC.** The sports venue/data-type canonicalisation chain (authored 2026-08-08 from the live distinct-values audit)
> carries an operator ruling to **merge the sports data_type vocabulary to a single lowercase form** — which renames
> every UPPERCASE API-Football entity token this campaign writes and measures (`FIXTURES`, `FIXTURE_EVENTS`,
> `FIXTURE_STATS`, `FIXTURE_LINEUPS`, `PLAYER_STATS`, `INJURIES`, `STANDINGS`, `TEAMS`) to `fixtures`, `fixture_events`,
> … .
>
> **Ordering is settled: this doc runs FIRST, the rename waits.** The rename phase declares
> `depends_on: sports_af_full_entity_completion_2026_08_03` + `gate_on_depends: true`. Rationale: renaming the registry
> while the two remaining all-leagues backfills (`FIXTURE_LINEUPS` 58,523 · `INJURIES` 62,709) are in flight would make
> the fetch loop write a token the registry no longer expects — minting phantom `expected_unattempted` rows — and would
> leave this doc's P0 re-census measuring the pre-rename axis. Letting this campaign converge first means the migration
> makes ONE pass over the finished corpus.
>
> **Action required of THIS doc: none.** Do NOT "fix" the uppercase tokens here, do not pre-emptively lowercase
> anything, and do not treat the casing as drift — it is the correct vocabulary until the gated rename phase lands. Keep
> launching the backfills and closing the re-census exactly as written.

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

| Entity           | Scope                        | Status (2026-08-05)                                                                                                                                                                                                                             |
| ---------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FIXTURES         | all-383                      | **DONE** — confirmed complete `sports_fixture_events_refetch_progress_2026_07_25.md`                                                                                                                                                            |
| FIXTURE_EVENTS   | MVP-96                       | **DONE 2026-08-03** — pass-3 complete, 1,973 "degenerate" residual corrected as legacy dupes, same doc                                                                                                                                          |
| FIXTURE_STATS    | all-383 (widened 2026-07-28) | 66,325 expected (non-MVP), ~416,042 already resolved, **24,462 needed** — **QUEUED**: quota has reset (confirmed), resumable from `PROGRESS.json` checkpoint `2023-11-19`; queued behind PLAYER_STATS (af-backfill-* singleton lock), see below |
| FIXTURE_LINEUPS  | all-383 (widened 2026-07-28) | 66,325 expected (non-MVP), 52,947 already resolved, **58,523 needed** (small background drift, no dedicated backfill)                                                                                                                           |
| **PLAYER_STATS** | **MVP-96**                   | 42,376 expected, 41,863 already resolved, **513 needed** — **ACTIVE**, chunk 13/26, via `af-backfill-20260807-013716`, see below                                                                                                                |
| **INJURIES**     | **all-383**                  | 108,701 expected, 45,992 already resolved, **62,709 needed** (unchanged — queued behind PLAYER_STATS/FIXTURE_STATS)                                                                                                                             |
| **STANDINGS**    | **all-383**                  | 108,701 expected, 108,430 already resolved, **271 needed (99.75%)** — quota-tail residual; **QUEUED** for a small completion pass once af-backfill-* frees up, see below                                                                        |
| **TEAMS**        | **all-383**                  | 108,701 expected, 108,605 already resolved, **96 needed (99.9%)** — quota-tail residual; **QUEUED** for a small completion pass once af-backfill-* frees up, see below                                                                          |
| **LEAGUES**      | ~~all-383~~ **RETIRED**      | **RESOLVED 2026-08-03** — writer path killed 2026-05-07, **0 genuinely needed**. See below.                                                                                                                                                     |

Denominator = distinct `(date, league_id)` pairs with a captured `FIXTURES`/`FIXTURES_SCHEDULE` row (a genuine fixture
existed that day), intersected with each entity's own `get_entity_league_coverage()` scope — mirrors
`emit_empty_gaps_for_entity`'s own expected-set logic (`sports_reference_core.py:338-341`); a shard is resolved (not
needed) if `capture_status` is `captured` OR `empty_confirmed`. Full census:
`instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py` +
`census_fixture_stats_lineups_widening_volume_2026_07_31.py` (both UTL-client-backed, both fixed 2026-08-04).

**Grand total needed, 2026-08-07T09:03Z: 63,589 across PLAYER_STATS+INJURIES+STANDINGS+TEAMS** (was 192,877 on 08-04, a
further ~67% drop — TEAMS/STANDINGS both essentially converged, see Progress Log) **+ 83,051 across
FIXTURE_STATS+FIXTURE_LINEUPS** (24,495 + 58,556). **The API-Football daily quota exhaustion has RESET** — PLAYER_STATS
is ACTIVE via `af-backfill-20260807-013716`, genuinely progressing through its chunk sweep; FIXTURE_STATS + the small
TEAMS/STANDINGS residual + FIXTURE_LINEUPS/INJURIES are queued behind it (the launcher's own singleton lock blocks
concurrent `af-backfill-*` VMs against the shared API key — documented anti-pattern, avoided). LEAGUES excluded per the
resolved verdict below.

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
- [x] ✅ [SCRIPT] P1. **Launch FIXTURE_LINEUPS all-leagues backfill** — FIXTURE_STATS CONVERGED 2026-08-08T14:40Z (chunk
      26/26, needed=116 from 24,462). Launched `af-backfill-*` (`RESUME_ENTITY=FIXTURE_LINEUPS`). Detail:
      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.
- [x] ✅ [SCRIPT] P0. ~~Recompute PLAYER_STATS/INJURIES/STANDINGS/TEAMS needed counts~~ — **CORRECTED 2026-08-04**: both
      census scripts had an empty_confirmed blind spot, fixed (`instruments-service@579421bf`). See the corrected table
      above. **PLAYER_STATS reprioritized to P0** — only 1,006 needed (was 17,440), genuinely near-complete.
- [x] ✅ [SCRIPT] **P0** (reprioritized, near-complete). **Launch PLAYER_STATS MVP-96 backfill** — **DONE
      2026-08-07T15:15Z**: `af-backfill-20260807-013716` ran its full 26-chunk sweep to `exit_code=0`; re-census
      confirms `needed=18` (was 998), 99.96% resolved.
- [x] ✅ [SCRIPT] P1. **Launch TEAMS all-leagues backfill** — **CONFIRMED DONE 2026-08-07T15:15Z** via the same
      re-census: `needed=96` (was 46,786) — `af-backfill-20260805-201310` (launched 2026-08-05, before this session) had
      already closed nearly all of this gap; only just discovered/confirmed now.
- [x] ✅ [SCRIPT] P1. **Launch STANDINGS all-leagues backfill** — **CONFIRMED DONE 2026-08-07T15:15Z**, same re-census:
      `needed=271` (was 51,114) — same earlier-VM explanation as TEAMS above.
- [x] ✅ [SCRIPT] P2. **Launch INJURIES all-leagues backfill** — DONE 2026-08-10 (slot 25 re-census discovery):
      `af-backfill-20260809-222924` ran `--entity INJURIES` + completed `exit_code=0` on 2026-08-10T04:23Z (fetched 322
      injuries for day 2026-08-09); fresh census needed=334 (was 62,709) — near-converged completion tail.
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

## Off-campaign follow-ups (vendor-completion audit, opened 2026-08-07) — SUPERSEDED, moved out 2026-08-07

**Promoted to its own doc**: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`. The operator widened the
mandate the same day from "every AF entity" to "every sports vendor (incl. odds_api/MTDS) down to captured +
empty_confirmed only" — genuinely broader than this doc's AF-specific scope and this doc was already at 800/1000 lines,
so the new doc is the tracking home for all of it (including the two items below, which finished before the split and
are kept here only as a compact record):

- [x] ✅ FootyStats 50-league subscription widening + China/Russia purge — DONE 2026-08-07
      (`unified-api-contracts@7810dad61`, `instruments-service@bbba584ef`, `instruments-service@8548182b5`).
- [x] ✅ SFI 89-row `attempted_failed` cluster — DONE 2026-08-07, root cause was a mis-scoped retry (see the new doc's
      Progress Log for the full writeup); confirmed 89 → 0.

Everything still open (footystats VM verification, Transfermarkt's 8-row retry, the PLAYER_VALUES data-discard decision,
the cross-vendor generalization scoping ask, baking checks into a daily AO run, plus the much larger
odds_api/api_football/MTDS picture found during the split) now lives in the new doc.

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
- **2026-08-04 (condensed, slots 4-11, 00:12Z-01:34Z)** — 8 repeated dispatches of
  `sports_af_full_entity_completion-003` (Launch FIXTURE_LINEUPS) against an unmet FIXTURE_STATS-convergence gate,
  during an active `asia-northeast1-c` SPOT preemption storm: 7 consecutive FIXTURE_STATS relaunch attempts (`-233053`
  through `-011911`) were ALL preempted within 1.5-17 min, zero clean completions, zero net progress (stuck at
  125/68,284 non-MVP shards, 0.18%, across the entire window). Root-caused + FIXED a genuine infra gap along the way:
  `af-backfill-`/`af-audit-` were missing from `exit_code_fleet_monitor`'s `_DATA_VM_PREFIXES`, making these VMs
  invisible to preemption auto-recovery regardless of timing — shipped
  `deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`. Filed 2 issue docs (both since resolved/archived):
  `af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md` (the auto-recovery gap) and
  `asia_northeast1_c_spot_preemption_storm_2026_08_04.md` (the zone-wide storm itself, 151+ preemption events across
  sports/tradfi/cefi). After the 7th failed relaunch, durably PARKED the redispatching todo via
  `POST /api/backlog/{task_id}/park` (`condition=auto_unpark__sports_af_full_entity_completion-003`) rather than let an
  9th dispatch repeat the same doomed check — this stopped the redispatch churn until FIXTURE_STATS genuinely converged
  (which it since has, many times over, in later ticks below).
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
    `instruments-service@d9a42d2e`; (2) `/codex/02-data/sports-data-source-coverage-matrix.md`'s SFI table was missing
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
- **2026-08-06T16:50Z-19:31Z (condensed, 7 ticks)** — All 3 lanes (af-backfill FIXTURE_STATS, TEAMS/STANDINGS
  chunk-loop, odds_api bigmem) healthy throughout, odds_api sawtooth normal (peak rss=31,798MiB, comfortably clear of
  the 64GB e2-highmem-8 ceiling, confirmed not a repeat crash). TEAMS dropped 7,872→996 (chunk-loop VM 65→71/76, now
  essentially converged at 99.1%), STANDINGS 11,753→4,448 (lockstep as always), FIXTURE_STATS 33,671→27,291. One
  stash-pop conflict at 17:27Z on an unrelated foreign file
  (`cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`) — confirmed the incoming commit was already the
  authoritative reconciled version, restored via `git checkout HEAD -- <file>`, nothing dropped. Also corrected a stale
  FIXTURE_STATS summary-paragraph figure that had drifted from the table row. Grand total 82,636→69,151 (core 4) +
  91,684→85,814 (FIXTURE_STATS+LINEUPS) across this stretch.
- **2026-08-06T21:55Z — Both dedicated VMs finished; API-Football daily quota exhausted campaign-wide; FIXTURE_STATS VM
  deleted as confirmed billing-waste.** TEAMS/STANDINGS chunk-loop VM (`instr-backfill-sports-teams-20260805-055622`)
  completed its full 76/76-chunk sweep (`exit_code=0`, clean self-delete) — TEAMS 996→96 (99.9% resolved), STANDINGS
  4,448→271 (99.75% resolved). odds_api bigmem VM (`mtds-backfill-odds-catchup-bigmem-20260806`) also completed its full
  assigned range 2026-03-28→2026-08-06 (`exit_code=0`, clean self-delete) — genuinely DONE, no crash, ever since the
  code fix + bigmem mitigation. **However, the chunk-loop's very last chunk (date=2026-08-05) hit API-Football's daily
  request-limit wall**
  (`API-Football returned errors: {'requests': 'You have reached the request limit for the day...'}`,
  `recovery=fail_fast` — correctly NOT silently marked empty, so no data-integrity risk, just real residual gaps) — this
  explains TEAMS/STANDINGS' small non-zero residuals. Checked `af-backfill-20260806-022033` (FIXTURE_STATS) and
  confirmed the SAME quota wall was hit shortly after (~22:29Z) — this is an account-wide daily quota exhaustion, not
  isolated to one VM/key. FIXTURE_STATS' VM was actively re-attempting a 100%-doomed API call roughly twice per second
  with zero chance of success until the quota resets — a confirmed billing-waste runaway per the workspace's
  VM-billing-waste hard rule — so it was **deleted** (not just stopped) to halt the waste; its `PROGRESS.json`
  checkpoint (`last_completed_date=2023-11-19, monotonic=true`) confirms clean resumability, so relaunching later
  resumes forward from there, not from scratch. **Correction to an earlier plan note**: I had planned to run
  `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh` once odds_api completed to "materialise
  empty_confirmed rows" — on inspection this launcher is FIXTURES-entity-specific (canonical `af_league_id` →
  `league_id` remapping for the Phase-5 undercount fix), unrelated to odds_api's own manifest, which the backfill's own
  `ManifestWriter` already updates live as it processes each date. No action needed there; odds_api is genuinely done
  as-is. **Decision: did NOT launch PLAYER_STATS/FIXTURE_LINEUPS/INJURIES this tick** — doing so now would immediately
  hit the same exhausted quota. All AF-entity work is PAUSED pending quota reset (likely UTC-midnight reset per typical
  api-sports.io behavior, unconfirmed for this specific plan tier — will re-check log freshness at the next tick rather
  than assume an exact time). **Also this tick: a NEW unrelated file
  (`ao_fleet_health_investigation_followups_2026_08_06.md`) turned up already git-added on this shared checkout before I
  touched anything — unstaged via `git restore --staged`, left untouched on disk, not mine.** Grand total 64,074
  (core 4) + 83,006 (FIXTURE_STATS+LINEUPS) — both entirely from the pre-pause progress; PLAYER_STATS (998) and INJURIES
  (62,709) unchanged, still queued.
- **2026-08-06T23:46Z — Quota-reset probe: still exhausted, but pinned down the likely reset boundary.** Launched a
  fresh `af-backfill-20260807-003828` scoped `--entity PLAYER_STATS 2020-06-06 2026-08-07` as a cheap probe (the
  launcher took several minutes — it auto-republished a stale `instruments-service` code tarball first, picking up the
  SFI_LEAGUES fix). Its log confirmed the SAME `'You have reached the request limit for the day'` error, still
  `recovery=fail_fast`. **Key finding: the log's own timestamps are UTC and read `2026-08-06T23:45-23:46Z`** — i.e. the
  quota was still exhausted only ~15 minutes before UTC midnight, strongly suggesting API-Football resets on a
  UTC-midnight daily cycle (typical for the api-sports.io family, now empirically supported rather than assumed).
  Deleted this second probe VM immediately once the still-exhausted result was confirmed (same billing-waste reasoning
  as the FIXTURE_STATS VM earlier — no point burning compute against a wall that won't move for another ~15+ min).
  Re-census confirms all numbers flat vs the last tick (as expected, nothing changed): PLAYER_STATS 998, INJURIES
  62,709, STANDINGS 271, TEAMS 96, FIXTURE_STATS 24,462, FIXTURE_LINEUPS 58,523. Grand total unchanged at 64,074
  (core 4) + 82,985 (FIXTURE_STATS+LINEUPS). **Decision: wait well past the inferred UTC-midnight reset before the next
  probe** — re-arming for ~45 min out rather than retrying immediately, to avoid a third wasted probe VM right at the
  boundary.
- **2026-08-07T01:45Z — CONFIRMED: the API-Football daily quota has RESET. Campaign resumed.** Third probe VM
  (`af-backfill-20260807-013716`, launched ~00:44Z) shows ZERO `'reached the request limit'` errors across its full
  233-line log (grepped explicitly to confirm) — genuine successful `Fetched N player stat entries`, real
  `ManifestWriter` shard updates, real per-fixture enrichment batches. UTC-midnight daily-reset hypothesis from the
  prior tick is now confirmed, not just inferred. **Left this VM running** rather than treat it as a disposable probe —
  it's doing real PLAYER_STATS work. Re-census: PLAYER_STATS 1,028 (was 998; the small increase is normal
  daily-denominator drift, not regression — the "as of today" boundary advanced one day, adding a handful of new
  expected fixture-day shards), INJURIES 62,709, STANDINGS 271, TEAMS 96, FIXTURE_STATS 24,495, FIXTURE_LINEUPS 58,556
  (all similarly denominator-drifted, not regressed). Grand total 64,104 (core 4) + 83,051 (FIXTURE_STATS+LINEUPS).
  **Decision: did NOT relaunch FIXTURE_STATS or a TEAMS/STANDINGS residual pass concurrently** — the launcher's own
  singleton lock refuses a second `af-backfill-*`/`af-audit-*` VM while one is running, and its own doc cites a
  documented thundering-herd incident (2026-04-19 SFI: 10 concurrent VMs / 6h / ~4 useful writes) from sharing one API
  key across concurrent VMs — respecting that, FIXTURE_STATS (from its `PROGRESS.json` checkpoint `2023-11-19`) and the
  small TEAMS/STANDINGS residual (96+271) queue behind PLAYER_STATS, to be launched once it completes or shows a genuine
  slowdown. Given PLAYER_STATS is only ~1,028 shards from done (97.6%+ resolved) and `--force` is omitted
  (already-captured shards skip fast), expect it to converge quickly — monitoring on the normal ~15-20 min cadence now
  that real work has resumed.
- **2026-08-07T02:11Z-04:25Z (condensed, 8 ticks)** — `af-backfill-20260807-013716` RUNNING+healthy throughout (0
  rate-limit errors every tick), chunk 1/26→12/26. PLAYER_STATS 1,028→553 (steady real per-minute-throttled progress,
  one 227-shard skip-fast burst at chunk 2→9). FIXTURE_STATS/TEAMS/STANDINGS/FIXTURE_LINEUPS/INJURIES all correctly
  queued behind the singleton lock throughout (2 small background drifts on FIXTURE_STATS/LINEUPS, -33 each, not from
  this campaign's own lane). Grand total 64,079→63,629 (core 4) + 83,051→82,985 (FIXTURE_STATS+LINEUPS). Off-loop aside
  (unrelated to this campaign, closed out by 04:25Z): an operator FootyStats-subscription request — reported the
  50-league Prediction+Features checklist, confirmed no vendor API for league subscription (manual UI only), tracked the
  ~30min cache-propagation delay, and confirmed the final state as **47/50 live**, 3 genuinely missing (Norway
  Eliteserien, Norway 1. divisjon, Turkey 1. Lig) — reported to operator, closed. context-scout refreshed
  `context_scope` (6 entries, added the af-backfill launcher + `census_other_vendors_gap_2026_08_06.py`).
- **2026-08-07T09:03Z** — Still RUNNING and healthy (0 rate-limit errors), advanced to chunk 13/26. PLAYER_STATS 553→513
  (-40), steady pace. FIXTURE_STATS/FIXTURE_LINEUPS/TEAMS/STANDINGS/INJURIES unchanged — still queued, no switch needed.
  Grand total 63,589 (core 4) + 82,985 (FIXTURE_STATS+LINEUPS, unchanged). (Aside: a large amount of off-loop work
  landed this tick, unrelated to this campaign — (1) shipped the FootyStats 50-league subscription widening to UAC
  (`unified-api-contracts@7810dad61` + `instruments-service@bbba584ef`, both QG-green): 4 Prediction leagues added
  (Argentina/Chile/Mexico/K League 1), 2 Features leagues removed (China/Russia, no Prediction-tier sibling in-country),
  tests updated + 1 genuinely-broken test fixed; (2) audited weather/SFI/Understat/Transfermarkt completion at the
  operator's request — weather + Understat are 100% clean (0 attempted_failed); SFI had 89 attempted_failed (all
  SFI_PROGRESSIVE_STATS, all JSONDecodeError, clustered 2026-07-20 — a single-day vendor-side outage pattern) and
  Transfermarkt had 8 (all PLAYER_VALUES, ClientResponseError, clustered 2026-08-04, same pattern) — launched targeted
  `--force` retries for both exact windows (`features-sfi-progressive-20260807-085632`, `tm-backfill-20260807-085636`,
  both confirmed RUNNING); (3) investigated PLAYER_VALUES' ~90% empty_confirmed rate at the operator's challenge — found
  the transfer-window explanation only accounts for 2.1% of it (`EXPECTED_OUTSIDE_TRANSFER_WINDOW`), the real driver is
  `EXPECTED_NO_PROVIDER_COVERAGE` at 91.9% — a distinct, already-implemented "outside scope" reason-code, not a generic
  empty; flagged a larger open ask from the operator (generalize this reason-level denominator hardening across all 5
  vendors + a manifest purge + a new codex SSOT doc) as needing proper scoping before starting, not yet begun.)
- **2026-08-07T09:53Z** — PLAYER_STATS checkpoint climbing (last_completed_date 2023-12-26 as of 09:15Z, monotonic),
  still healthy — no dedicated re-census this tick, deferred to let the following off-loop corrections land first.
  (Aside, all unrelated to this campaign: (1) executed the operator-authorized China/Russia footystats manifest purge —
  `instruments-service/scripts/footystats_purge_out_of_scope_leagues_2026_08_07.py`, confirmed 0 captured rows in the
  drop set, 4,458 rows removed, verified 0 remaining canonical + per-VM, backup at
  `_index/availability_index.20260807-085052.footystats_purge.bak.parquet`, shipped `instruments-service@8548182b5`; (2)
  launched the footystats backfill VM scoped to the new 50-league registry — first launch used `--force`, which this
  launcher's `VM_FORCE=true` metadata translates into a `--force` CLI flag on the actual `instruments_service`
  invocation, i.e. a full redo-all across the whole `--start-date 2020-06-06` range (confirmed via serial console);
  caught before meaningful cost (~2 min into execution, no existing `fs-backfill-*` VM was even running so the
  lock-bypass half of `--force` was never needed), deleted `fs-backfill-20260807-095916` and relaunched clean as
  `fs-backfill-20260807-100731` (no `--force`, skip-if-captured default); (3) went to verify the SFI retry VM launched
  last tick (`features-sfi-progressive-20260807-085632`, exit_code=0) actually cleared the 89 attempted_failed rows — it
  hadn't: **root cause was mis-scoping, not a persistent vendor failure**. The 89 rows are
  `service_name=instruments-service, data_type=SFI_PROGRESSIVE_STATS` (raw ingestion, `soccer_football_info` adapter,
  `sfi.py` orchestrator), but the retry ran `features-service`'s `compute_sfi_progressive_only`, which writes a
  _different_ downstream data_type (`SFI_PROGRESSIVE_FEATURES`) — it never touched the failing rows at all (their
  `attempted_at` timestamps are still 07-20/07-27/08-03, none from the retry's run). Relaunched correctly via
  `deployment-service/scripts/vm/launch-sfi-backfill-vm.sh --entity SFI_PROGRESSIVE_STATS 2026-07-20 2026-08-01` (no
  `--force` needed, no existing `sfi-*` VM running; `sfi.py`'s per-league `record_failed` path — already fixed
  2026-07-14 to mirror the footystats/weather per-league pattern per its own inline comment — means `attempted_failed`
  is not in this orchestrator's skip set either, so this run should genuinely retry all 89 shards). Transfermarkt's
  retry (`tm-backfill-20260807-085636`) was checked too and is correctly scoped (`instruments_service`,
  `--sports-provider TRANSFERMARKT --sports-entity PLAYER_VALUES`, single day `2026-08-04`) — its `--force` is low-risk
  since the date range is a single day, left running as-is. Both SFI (corrected) and TM retries pending confirmation
  next tick.)
- **2026-08-07T10:19Z** — PLAYER_STATS checkpoint climbing (2023-12-26 → 2024-04-07, +103 days), still healthy. (Aside,
  all unrelated to this campaign: (1) **SFI retry CONFIRMED RESOLVED** — `sfi-backfill-20260807-101503` (correctly
  re-scoped to `instruments-service --sports-provider SOCCER_FOOTBALL_INFO`) completed exit_code=0, wrote 5,669 real
  progressive-stat rows for 2026-08-01 alone; manifest re-query confirms **89 → 0** `attempted_failed` for
  `source=soccer_football_info` — the mis-scoping diagnosis from last tick was the true root cause, not a persistent
  vendor failure; (2) footystats backfill VM (`fs-backfill-20260807-100731`) healthy, climbing (2021-01-26 as of 09:49Z)
  — working through the 2020-06-06 floor forward, will take a while given the ~6-year, 50-league range but no concerning
  behavior; (3) **Transfermarkt retry is a live, ongoing vendor problem, not the resolved one-off it looked like last
  tick** — `tm-backfill-20260807-085636` is hitting repeated real-time HTTP 502s from
  `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` (10-attempt exponential-backoff cycles,
  restarting the outer cycle after each exhaustion) continuously from at least 09:35Z through 09:49Z on TODAY's date
  (2026-08-07), not just the original 2026-08-04 cluster — this is correct retry behavior (502 is legitimately
  retryable) so left running, but it means the vendor's `standings` endpoint is currently degraded, not transiently
  blipped; will re-check next tick and consider killing/deferring if it's still spinning identically (billing-waste
  judgment call, not yet warranted at ~1h of retries on a SPOT e2-standard-8).)
- **2026-08-07T10:35Z** — PLAYER_STATS checkpoint climbing (2024-04-07 → 2024-08-14, +129 days). footystats backfill
  climbing (2021-01-26 → 2021-10-09, +257 days). Both healthy. (Aside, all unrelated to this campaign — a big off-loop
  tick: (1) killed `tm-backfill-20260807-085636` after confirming 2h17m of an identical HTTP-502 retry cycle against
  `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` with zero forward progress — a
  durably-down vendor endpoint, not a transient blip, so continuing to let it spin was confirmed billing waste; (2)
  operator widened this session's mandate from "every AF entity" to "every sports vendor (incl. odds_api/MTDS) down to
  captured + empty_confirmed only" — ran a full cross-vendor manifest census (10,463,368 rows) and found the real scope
  is much larger than earlier believed: weather has 205,517 `expected_unattempted` shards and SFI 205,363 (both were
  called "100% clean" earlier this session based only on `attempted_failed=0` — an incomplete check, corrected now), and
  odds_api has by far the largest `attempted_failed` cluster (13,916 rows). Given the AF doc was already at 800/1000
  lines and this is genuinely broader in kind, opened `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` as
  the new tracking home (this doc's own off-campaign section trimmed to a pointer); (3) traced
  `mdps_odds_horizon_bucket`'s gap to an ALREADY-FIXED freshness-check bug (shipped 2026-07-30) and found the actual
  backfill is tracked in a pre-existing doc (`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`) whose P1/P2 todos
  were stuck `BLOCKED-CREDENTIALS` from the 2026-08-02 odds-api quota exhaustion — stale, since the operator's
  10M-credit top-up landed 2026-08-03; retagged both after live-reverifying 14.4M credits available today. Deliberately
  did NOT launch that backfill VM this tick — that doc's own history (5+ uncoordinated relaunches, preemptions, silent
  freezes, one contributing to the original quota-exhaustion incident) argued for a dedicated, attentive next tick
  rather than a rushed launch at the tail of an already-dense one.)
- **2026-08-07T11:08Z** — PLAYER_STATS checkpoint climbing (2024-08-14 → 2024-10-06), chunk 18-19/26. footystats
  backfill climbing (2021-10-09 → 2022-05-01). Both healthy. (Aside, all in
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s scope, not this campaign's: this tick delivered on
  last tick's stated priority — launched the odds_api gap-backfill VM (`mtds-backfill-odds-1`, guard-verified
  `0 running + 1 planned <= cap 1`, no `--force`) and the weather full backfill (`weather-backfill-20260807-120241`)
  cleanly; both confirmed RUNNING. Also root-caused the bulk of api_football's 35,058 attempted_failed rows (78% is the
  already-known 2026-08-06 quota exhaustion, self-resolving via this very campaign's active sweep). Full fleet as of
  this tick: 4 VMs RUNNING (this campaign's `af-backfill`, `fs-backfill`, plus `mtds-backfill-odds-1` and
  `weather-backfill` from the sibling doc) — no conflicts, no shared locks contended.)
- **2026-08-07T12:12Z** — PLAYER_STATS climbing (2024-12-04 → 2025-03-08), footystats climbing (2022-10-13 →
  2023-04-23). Both healthy. (Aside, sibling-doc scope: correction to last tick's optimistic odds_api VM read — it
  turned out `mtds-backfill-odds-1` was OOM-crash-looping the whole time (10 leagues, 10 identical chunk-1 OOM kills,
  zero real progress) and got killed; a relaunch attempt was correctly blocked by the concurrency guard because another
  worker's `mtds-backfill-odds-401-retry` (a legitimate, `--allow-parallel`, guard-respecting parallel launch targeting
  the 871-row 401 retry todo) is still running and healthy. Full detail + the pre-existing OOM bug this reproduces in
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` and
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`. SFI backfill also confirmed healthy this tick (real writes,
  21,742 rows for 2020-10-17). Not this campaign's scope, noted for completeness.)
- **2026-08-07T12:40Z** — PLAYER_STATS climbing (2025-03-08 → 2025-05-31, chunk 21/26, ~5 chunks left). footystats
  climbing (2023-04-23 → 2023-10-16). Both healthy — verified this time via actual date-value diffs against last tick
  per the new codex rule 1b, not just log-line presence. (Aside, sibling-doc scope: added codex rule 1b to
  `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` documenting the crash-loop-looks-like-progress lesson;
  relaunched the odds_api full-range backfill with `--chunk-size 5 --allow-parallel` alongside the still-healthy
  `mtds-backfill-odds-401-retry` (confirmed zero OOM signatures across its full log, credits healthy at 14.46M
  remaining) — full detail in `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.)
- **2026-08-07T13:09Z** — PLAYER_STATS climbing fast (2025-05-31 → 2025-08-19), now **chunk 22/26 — only 4 chunks
  left**, likely to finish within the next 1-2 ticks. footystats climbing (2023-10-16 → 2024-03-30). Both healthy,
  verified via actual date-value diffs again (rule 1b). Watch closely next tick for chunk 26/26 + clean exit — once that
  lands, the `af-backfill-*` singleton lock frees and FIXTURE_STATS (this doc's next queued P0 todo) should launch
  immediately, resuming from its own `PROGRESS.json` checkpoint per the doc's existing Todos section.
- **2026-08-07T13:39Z** — PLAYER_STATS still chunk 22/26, actively working through it (fixture lookups now at
  2025-10-26, cheap 0-extra-API-call URDI passthrough). Not done yet — no completion signal, still ~4 chunks remaining.
  footystats climbing (2024-03-30 → 2024-09-22). Both healthy. (Aside, sibling-doc scope: the odds_api 401-retry VM's
  EPL chunk finally OOM'd after covering most of its 8-month range — the wrapping loop self-recovered correctly by
  moving to the next league, matching documented "working as designed" behavior, not a repeat of the earlier bad
  crash-loop. The independently-tracked SOURCE_RETURNED_ZERO cluster (13,045 rows) turned out to already be root-caused
  and fixed by another worker this session — one less open item. Full detail in
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.)
- **2026-08-07T14:18Z** — PLAYER_STATS now **chunk 24/26** (was 22/26), only **2 chunks left** — should complete within
  the next tick or two. footystats climbing (2024-09-22 → 2025-04-06). Both healthy, verified via date-value diffs.
  Watching closely for chunk 26/26 + clean exit to launch FIXTURE_STATS immediately once the lock frees.
- **2026-08-07T14:48Z** — PLAYER_STATS now **chunk 25/26 — only 1 chunk left, imminent.** footystats climbing
  (2025-10-17), SFI climbing (2022-08-13). All healthy. (Aside, sibling-doc scope, important correction: the weather
  backfill VM completed with `exit_code=0` but a re-census showed it did NOT actually resolve the honest-coverage gap —
  `expected_unattempted` barely moved and 16,241 new genuine `attempted_failed` rows appeared. Caught this via a proper
  post-completion re-census rather than trusting the clean exit code, per codex rule 4a. Full detail + follow-up todos
  in `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`. Not this campaign's scope.)
- **2026-08-07T15:15Z — MILESTONE: PLAYER_STATS genuinely converged.** `af-backfill-20260807-013716` reached chunk
  26/26, `instruments-backfill loop complete`, `exit_code=0`, self-deleted — and this time VERIFIED via a real re-census
  (`census_all_af_entities_completion_2026_08_03.py`) rather than trusted on the exit code alone (per this session's own
  weather-backfill lesson, applied immediately): **PLAYER_STATS needed=18** (down from 998 at the start of this run, and
  1,006/17,440 before that) — 99.96% resolved, the residual 18 is plausibly a genuine honest-absence floor, not a real
  gap. **Bonus finding from the same census**: TEAMS (needed=96) and STANDINGS (needed=271) are ALSO already near-fully
  resolved — turns out an earlier VM run (`af-backfill-20260805-201310`, before this session's PLAYER_STATS focus began)
  had already closed most of their gaps; this campaign is further along than the standing Progress Log entries
  suggested. The `af-backfill-*` singleton lock freed — immediately launched the next queued P1 entity,
  **FIXTURE_STATS** (`launch-api-football-backfill-vm.sh --entity FIXTURE_STATS 2020-06-06 2026-08-07`, should resume
  from its own `PROGRESS.json` checkpoint at `2023-11-19` per the existing Todos section — confirming next tick). Note:
  this doc's own AO-parked condition (`auto_unpark__sports_af_full_entity_completion-003`) only blocks AO's own
  task-offering, not a direct manual VM launch, so no unpark action was needed to proceed.
- **2026-08-07T16:19Z** — **FIXTURE_STATS confirmed launched and RUNNING**: `af-backfill-20260807-161736` (auto-
  republished 2 stale tarballs — instruments-service, deployment-service — before create, then succeeded). Will confirm
  actual date-progress + resume-from-checkpoint behavior next tick.
- **2026-08-07T16:52Z — correction + a second genuine milestone.** FIXTURE_STATS is doing a full skip-fast sweep from
  `2020-06-06` (chunk 1/26, per-fixture skip-logic already firing: "skipping 3 entities already in manifest", "39 pairs
  already in existing per-league parquets"), NOT literally resuming from the `2023-11-19` checkpoint the doc's own text
  suggested — same pattern PLAYER_STATS used successfully, just means real wall-clock time to skip-fast through ~3.5
  already-covered years before reaching genuinely-new ground; not a bug, correcting my earlier expectation. Separately
  (sibling-doc scope, but a real AF-adjacent win): **footystats' 50-league-widening backfill finished cleanly and was
  VERIFIED via re-census (not just `exit_code=0`)** — 0 `attempted_failed`, 0 `expected_unattempted`, both before and
  after; +2,383 captured / +8,088 empty_confirmed added for the 18 newly-added leagues. Genuinely, cleanly done, unlike
  weather's messy outcome. SFI, `mtds-backfill-odds-smallchunk-20260807` (chunk 18/451, 4 OOM total, still
  self-recovering), and `mtds-backfill-odds-401-retry` (18 OOM total, same ~6-9 min/league cadence) all confirmed
  healthy via value-diffs.
- **2026-08-07T16:38Z** — FIXTURE_STATS chunk 2/26 (2020-10-25/26), a `PROGRESS.json` timestamp momentarily looked stale
  (~an hour old by my initial, WRONG assumption of current time) — checked `date -u` before concluding a stall per the
  async-wait discipline, found actual current time was only ~2 min past the log's last line; false alarm, genuinely
  healthy. Lesson: always verify current wall-clock time directly rather than assuming a scheduled-wakeup delay landed
  exactly on time. SFI (2023-05-11→2023-11-17), `mtds-backfill-odds-smallchunk-20260807` (chunk 18/451, 5 OOM),
  `mtds-backfill-odds-401-retry` (23 OOM, CHILE_PRIMERA/LIGA_MX/K_LEAGUE_1) all confirmed healthy, consistent with
  established patterns — no new incidents.
- **2026-08-07T17:48Z** — FIXTURE_STATS chunk 4/26 (2021-03-09), SFI 2024-09-26. Both healthy, genuine progress
  confirmed via value-diffs. (Aside, sibling-doc scope: confirmed the stale-code fix from last tick is holding —
  `mtds-backfill-odds-smallchunk2-20260807` is 0/5-chunks-clean OOM and, more importantly, odds_api's total
  `attempted_failed` count has generated exactly **0 new rows** since the fixed VM launched at 17:18Z (26,934→26,937,
  the +3 is noise) — the SOURCE_RETURNED_ZERO bug is genuinely not recurring anymore.)
- **2026-08-07T18:17Z** — FIXTURE_STATS chunk 4/26 (2021-04-15), SFI (2025-01-31), `mtds-backfill-odds-smallchunk2`
  (chunk 10/451, still 0 OOM). All healthy, quiet tick — no new incidents.
- **2026-08-07T19:21Z** — FIXTURE_STATS chunk 5/26 (2021-07-28), SFI (2025-11-23, closing in on the full-range end — ~8
  months left), `mtds-backfill-odds-smallchunk2` (chunk 17/451, still 0 OOM). All healthy. Also this tick: shipped the
  long-deferred daily-AO-skill request (sibling-doc scope) — baked the vendor-completion audit checks into
  `cursor-configs/skills/data-pipeline-reconciliation/reference-sports.md` (`722fd6d4cf`), closing the last
  unilaterally-actionable item from the operator's original asks; only the cross-vendor generalization scoping ask
  (needs operator input) remains genuinely open.
- **2026-08-07T19:48Z** — FIXTURE_STATS chunk 5/26 (2021-08-20). SFI made a huge jump — **2025-11-23 → 2026-03-21** (~4
  months of dates in one ~27 min tick) — **now only ~4.5 months from the full-range end, likely to finish within the
  next tick or two.** `mtds-backfill-odds-smallchunk2` chunk 18/451, one new EPL OOM self-recovered correctly (moved to
  LA_LIGA, 1/18 chunks — consistent with the established low, tolerable rate). All healthy.
- **2026-08-07T21:17Z** — FIXTURE_STATS chunk 6/26 (2021-09-14). `mtds-backfill-odds-smallchunk2` chunk 18/451 (3 OOM
  total, still self-recovering, still within tolerable range). Both healthy. (Aside, sibling-doc scope, major milestone:
  SFI backfill genuinely COMPLETED and self-deleted — verified via re-census, not just exit_code=0, per rule 4a — found
  the exact same structural pattern weather hit (`expected_unattempted` completely unmovable by any amount of
  re-running, seeded by a historically-broader-scope writer than the current one). Ran the already-built, sanctioned
  reclassification scripts for both weather and SFI (`type_weather_eu_no_provider_coverage_2026_06_27.py`,
  `type_sfi_eu_no_provider_coverage_2026_06_27.py`), retyping a combined 410,665 rows from misleading
  `expected_unattempted` to honest `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)` — safe, additive per-VM-shard
  writes, pending the next consolidator merge cycle. Full detail in
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.)
- **2026-08-07T20:48Z** — FIXTURE_STATS chunk 6/26 (2021-10-14). `mtds-backfill-odds-smallchunk2` chunk 18/451, 6 OOM
  total but verified as 6 DIFFERENT leagues each self-recovering once (not a stuck repeat) — consistent with the
  established tolerable pattern. Both healthy. (Aside, sibling-doc scope: **CONFIRMED the weather+SFI reclassification
  fully landed** — re-census shows `expected_unattempted` completely gone (0) for both sources, `empty_confirmed` grew
  by exactly the retyped row counts. Both sources now hold only `captured`/`empty_confirmed`/a small already-diagnosed
  `attempted_failed` tail — genuinely at the operator's target state.)
- **2026-08-07T21:17Z** — FIXTURE_STATS chunk 6/26 (2021-11-06). `mtds-backfill-odds-smallchunk2` has now spent ~2 hours
  on chunk 18/451 alone (2020-08-30→2020-09-03), 9 OOM total but verified still 9 DISTINCT leagues (EPL through
  ELITESERIEN) self-recovering each time, not a stuck repeat. Likely explanation: this exact 5-day window covers
  multiple European leagues' season-openers simultaneously (high real fixture density across many leagues at once),
  plausibly why this one chunk is taking disproportionately long among 451 total — not a new bug, self-recovery still
  working correctly, no data loss. Watching; will note if it doesn't eventually move past chunk 18.
- **2026-08-07T21:22Z** — FIXTURE_STATS advanced chunk 6/26 to `2021-11-19` (fresh checkpoint, was `2021-11-06`),
  healthy. `mtds-backfill-odds-smallchunk2` STILL on chunk 18/451 — read the full `run.log` (not just PROGRESS.json,
  which looked 2h-stale) and confirmed 10/18 leagues OOM'd (55%) but each a genuinely distinct league, EKSTRAKLASA fully
  completed, no repeats — genuine progress, not a stall; PROGRESS.json just checkpoints at the whole-chunk boundary.
  Full root-cause writeup: `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`@`b90338bfd9`.
- **2026-08-07T21:53Z** — FIXTURE_STATS jumped 89 days to `last_completed_date=2022-02-16` (fresh checkpoint,
  `21:52:23Z`), accelerating nicely toward its 26-chunk end. `mtds-backfill-odds-smallchunk2` still on chunk 18/451
  (~2h40m now) but confirmed still genuinely progressing — 22 distinct leagues attempted (up from 18), currently
  `J1_LEAGUE`, RSS cycling normally, 12 total OOMs (up from 10, still zero repeats). Watching; would escalate if still
  stuck on chunk 18 at the next tick. Full detail: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.
- **2026-08-07T22:21Z** — FIXTURE_STATS +49 days (`last_completed_date=2022-04-06`, fresh `22:20:25Z`), still
  accelerating. odds smallchunk2 STILL on chunk 18/451 (~3h) — followed up on the flagged outlier: 25 distinct leagues
  now attempted (up from 22, zero repeats, spanning Europe/S.America/Asia/N.America/Oceania), 13 OOMs (+1, LIGA_MX).
  Concluded this is a genuinely large Prediction-tier roster hitting its first true global season-opener week
  simultaneously (2020-08-30→2020-09-03), not malfunction — values keep climbing every tick (rule 1b), no intervention.
  Full detail + league list: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`949f0c59bf`.
- **2026-08-07T22:50Z** — FIXTURE_STATS +45 days (`last_completed_date=2022-05-21`, fresh `22:49:35Z`), steady. odds
  smallchunk2 still chunk 18/451 (~3.5h) — 29 leagues (up from 25), 15 OOM (up from 13), zero repeats — continued
  genuine progress, root cause already established, no further deep-dive needed each tick.
- **2026-08-07T23:17Z — CLOSED: chunk 18 cleared (3h38m total, 30 leagues, 16 OOM, 14 clean first-try).** FIXTURE_STATS
  +72 days (`last_completed_date=2022-08-01`, fresh `23:16:40Z`), accelerating well. odds smallchunk2 now on chunk 19
  (`2020-09-04→2020-09-08`), already moving fast (skip-fast dates), confirming off-season weeks are much cheaper as
  hypothesized. Noted for future ticks: `PROGRESS.json` lagged the true `run.log` checkpoint by 18+ minutes at this
  transition — cross-check `run.log`'s own `PROGRESS: chunk=N` line near a suspected boundary rather than trusting
  `PROGRESS.json` alone. Full detail: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`8c34027029`.
  Reverting to lightweight per-tick checks now that the outlier is resolved.
- **Self-correction**: FIXTURE_STATS's chunk-number label had gone stale in this doc for several ticks (I kept writing
  "chunk 6/26" from an early read without re-verifying against `run.log`) — a live check shows it's actually **chunk
  9/26**. The `last_completed_date` values reported each tick were always accurate; only the chunk-number label was
  stale. Chunks 6-8 each cleared in under an hour once past the early quota-limited chunks. Using chunk 9/26 going
  forward.
- **2026-08-07T23:47Z** — FIXTURE_STATS +30 days (`last_completed_date=2022-08-31`, fresh `23:46:43Z`). odds
  smallchunk2: `PROGRESS.json` appears to have stopped uploading entirely after chunk 17 (unrelated to OOM — VM is
  confirmed healthy) — cross-checked via `run.log`'s own `PROGRESS: chunk=N` lines instead: genuinely on **chunk
  22/451** now (`2020-09-19`), chunks 19-21 each cleared in ~6 min, zero new OOMs since chunk 18 closed. Full detail:
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`7889dffd04`,
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`@`9422004062`.
- **2026-08-08T00:16Z** — FIXTURE_STATS +29 days (`last_completed_date=2022-09-29`, fresh `00:15:42Z`), steady. odds
  smallchunk2 now chunk 25/451 (`2020-10-04`, via `run.log`), zero new OOMs (16 total, unchanged). Both healthy.
- **2026-08-08T00:16Z-02:46Z — MAJOR: odds smallchunk2 found DELETED (external kill, unexplained), recovered with zero
  data loss as `smallchunk3`.** FIXTURE_STATS: confirmed **chunk 12/26** (`last_completed_date=2023-03-05`, actively
  processing `2023-03-06`), healthy. odds: `gcloud compute operations list` showed unexplained `delete` ops at
  `00:55:20Z`/`00:56:15Z` (shared automation SA, not attributable to a specific worker); `run.log` genuinely stopped at
  `00:37:08Z` mid-chunk-26 with **no terminal `exit_code=` line** — not the VM's own graceful self-delete-on-exit per
  codex's "Self-deleting VM/job" rule, looks like an external forced deletion. Real progress preserved through chunk
  25/451 (no data loss). Concurrency guard confirmed 0 running odds VMs, relaunched as
  **`mtds-backfill-odds-smallchunk3-20260808`** (same params, tarballs fresh), verified booted + correctly skip-fasting
  through already-covered dates. Also hit a >1h `gcloud storage cat` flakiness episode (three different error types on
  files `ls -L` proved existed) — worked around via direct HTTPS GET, resolved on its own by ~02:44Z. Full detail:
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`a6dab782b5`.
- **2026-08-08T03:15Z** — FIXTURE_STATS +80 days (`last_completed_date=2023-05-24`, fresh `03:14:21Z`), ~chunk 13/26.
  `smallchunk3` confirmed healthy: chunk 7/451 (`2020-07-06`), steady ~4.5min/chunk skip-fast pace, zero OOM, ETA ~1h20m
  to reach chunk 26 where real new work resumes. Both healthy.
- **2026-08-08T03:43Z** — FIXTURE_STATS +72 days (`last_completed_date=2023-08-04`, fresh `03:41:29Z`). smallchunk3
  chunk 13/451 (`2020-08-05`), pace holding, zero OOMs. Both healthy.
- **2026-08-08T04:10Z** — FIXTURE_STATS +30 days (`last_completed_date=2023-09-03`, fresh `04:09:26Z`). smallchunk3
  chunk 17/451 (`2020-08-25`), zero OOMs — approaching chunk 18 (the known season-opener week); expect some OOMs to
  resume there but a shorter pass than the original 3h38m since ~14/30 leagues are already durably captured. Full
  detail: `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`0428a48f99`.
- **2026-08-08T04:38Z** — FIXTURE_STATS +47 days (`last_completed_date=2023-10-20`, fresh `04:37:30Z`). smallchunk3 now
  in chunk 18, 4 leagues attempted, zero OOMs so far — confirms the skip-fast hypothesis. Full detail:
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`8c7d3249ac`.
- **2026-08-08T05:05Z** — FIXTURE_STATS +49 days (`last_completed_date=2023-12-08`, fresh `05:04:33Z`). smallchunk3
  still chunk 18, 10 leagues attempted, zero OOMs. Both healthy.
- **2026-08-08T05:33Z — MAJOR: smallchunk3 also died (2nd occurrence of a genuine silent-hang-then-watchdog-kill
  pattern, distinct from OOM).** Not OOM, not a graceful self-delete — heartbeat blob itself stopped updating
  (`05:06:23Z`) confirming a real hang, correctly caught by `vm_zombie_watchdog.py` (`delete` at `05:26:25Z`). New
  issue: `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`. No data loss. Relaunched as
  `mtds-backfill-odds-smallchunk4-20260808`. FIXTURE_STATS unaffected. Full detail:
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`@`4d57ad99b8`.
- **2026-08-08T05:57Z** — smallchunk4 confirmed booted + healthy (chunk 4/451, zero OOMs). FIXTURE_STATS jumped 98 days
  (`last_completed_date=2024-03-15`, fresh `05:55:28Z`). Both healthy.
- **2026-08-08T06:24Z** — FIXTURE_STATS +34 days (`last_completed_date=2024-04-18`, fresh `06:23:27Z`). smallchunk4
  chunk 10/451 (`2020-07-21`), zero OOMs, no 3rd hang occurrence yet. Both healthy.
- **2026-08-10 (slot 25, `-011` re-census)**: PLAYER_STATS 3 · INJURIES 334 (was 62,709) · STANDINGS 271 · TEAMS 96 ·
  FIXTURE_STATS 136 · FIXTURE_LINEUPS 136 = ~976 (was 146,640). ~all `expected_unattempted`/absent tail, 19 TEAMS
  `attempted_failed` — completion pass would close it, NOT confirmed floors. LINEUPS+INJURIES backfills done since last
  entry (af-backfill-20260809-* exit_code=0). Checkbox OPEN.
- **2026-08-10T04:58Z corroboration (independent session, `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`
  commit `4a2d0c35bf`)**: for the 4 entities that doc tracked (PLAYER_STATS/INJURIES/STANDINGS/TEAMS), a repeat
  re-census with zero active VM read byte-identical to the prior tick (INJURIES 334 both times) — per rule 4a, a stable
  repeat reading with no writer running confirms a genuine floor, not consolidator lag. Matches this doc's slot-25
  numbers exactly. Does NOT independently confirm FIXTURE_STATS/FIXTURE_LINEUPS (136 each, out of that doc's scope) —
  this doc's own "NOT confirmed floors" caveat for those 2 entities still stands; checkbox correctly stays OPEN until
  they're similarly re-verified stable.
- **2026-08-10 (slot 18, data_engineering, `sports_af_full_entity_completion-9798da269f23` stale re-dispatch of the
  final re-census todo)**: The todo's done-when is explicitly "once every backfill above completes" — and a backfill is
  STILL in-flight: `gcloud compute instances list` shows `af-backfill-20260810-103218` RUNNING (created
  2026-08-10T03:32Z, `instruments_chunk_loop.sh`, heartbeat daemon alive), processing an INJURIES historical chunk
  (`--sports-entity INJURIES --start-date 2022-08-25 --end-date 2022-11-22`). Running the 8-entity re-census now would
  capture a mid-backfill snapshot, not the terminal convergence check the todo exists to perform — the same
  stale-baseline reasoning slot 25's re-census (above) and the sibling paper-gate doc both applied. Declining to run the
  census this turn; skipping with `reason_code: GATED` + `park_now: true` so it stops re-dispatching to fresh workers
  until the INJURIES backfill terminates. No code/report changes; this Progress Log entry is the only change this turn.
- **2026-08-11 (slot 19, `sports_af_full_entity_completion-9798da269f23` re-dispatch of the final re-census todo)**:
  done-when STILL unmet — `af-backfill-20260810-162910` (STANDINGS all-383 completion pass, 2020-06-06→2026-08-10) is
  RUNNING and GENUINELY progressing (PROGRESS.json `last_completed_date=2022-03-13` monotonic, updated 00:01:13Z live;
  run.log tail shows active per-fixture STANDINGS work + fresh PIPELINE_HEARTBEAT — not a stale heartbeat). The two
  other today VMs (`-154220`/`-160958`) are TERMINATED with no EXIT_STATUS blob (preempted/killed, not clean
  completions). Running the 8-entity census now would capture a mid-backfill snapshot of STANDINGS (residual 271 at
  slot-25 census), not the terminal convergence check — same rule-4a/slot-18/25 stale-baseline reasoning. Skipping
  `reason_code: GATED` + `park_now: true`. **Unpark**: when `af-backfill-20260810-162910` terminates (running
  `af-backfill-*` count == 0), re-run both census scripts + confirm all 8 entities stable ~0 / honest-absence floors,
  then close this doc + notify operator. No code changes; Progress Log entry only.
- **2026-08-11 (slot 23, `sports_af_full_entity_completion-9798da269f23` re-dispatch)**: done-when STILL unmet — slot-19
  VM `af-backfill-20260810-162910` TERMINATED, but its STANDINGS all-383 scope was RELAUNCHED as
  `af-backfill-20260811-012845` (2020-06-06→2026-08-10, e2-standard-8 asia-northeast1-c), RUNNING + GENUINELY
  progressing (PROGRESS.json `last_completed_date=2020-11-14` monotonic @2026-08-11T03:30:54Z; WATCHDOG_TRACE size
  688k→754k, iter=115). Only `-012845` running (GCP); AWS none. Census now = mid-backfill STANDINGS snapshot (residual
  271), not terminal convergence — same rule-4a/slot-18/19/25 stale-baseline reasoning. Skipping `reason_code: GATED` +
  `park_now: true`. **Unpark**: when running `af-backfill-*` count == 0, re-run both census scripts + confirm all 8
  entities stable ~0 / honest-absence floors, then close this doc + notify operator. No code changes; Progress Log only.
- **2026-08-11 (slot 17, `sports_af_full_entity_completion-9798da269f23` re-dispatch)**: done-when STILL unmet —
  `af-backfill-20260811-012845` (STANDINGS all-383, 2020-06-06→2026-08-10) is RUNNING (GCP asia-northeast1-c). The two
  other today VMs (`-154220`/`-160958`) are TERMINATED; `-162910` TERMINATED per slot-23. Only `-012845` running (GCP);
  AWS none. Census now = mid-backfill STANDINGS snapshot (residual 271 at slot-25 census), not terminal convergence —
  same rule-4a/slot-18/19/23 stale-baseline reasoning. Skipping `reason_code: GATED` + `park_now: true`. **Unpark**:
  when running `af-backfill-*` count == 0, re-run both census scripts + confirm all 8 entities stable ~0 /
  honest-absence floors, then close this doc + notify operator. No code changes; Progress Log only.
- **2026-08-11 (slot 24, `sports_af_full_entity_completion-9798da269f23` re-dispatch, resumed mid-edit after OOM
  kill)**: done-when STILL unmet — `af-backfill-20260811-012845` (STANDINGS all-383, 2020-06-06→2026-08-10,
  e2-standard-8 asia-northeast1-c) still RUNNING (`gcloud` confirmed, status unchanged since prior tick). Only `-012845`
  running among `af-backfill-*` (GCP); AWS none. Census now = mid-backfill STANDINGS snapshot, not terminal convergence
  — same rule-4a/slot-17/18/19/23 stale-baseline reasoning. Skipping `reason_code: GATED` + `park_now: true`.
  **Unpark**: when running `af-backfill-*` count == 0, re-run both census scripts + confirm all 8 entities stable ~0 /
  honest-absence floors, then close this doc + notify operator. No code changes; Progress Log only.
- **2026-08-11T16:36Z (slot 32, `sports_af_full_entity_completion-9798da269f23` re-dispatch)**: done-when STILL unmet —
  prior `-012845` gone; a fresh `af-backfill-20260811-162726` (STANDINGS all-383, resuming from 2023-06-06) is RUNNING
  (GCP asia-northeast1-c), verified via `run.log`/heartbeat (not just `gcloud list`): real `ManifestWriter` shard
  writes, fresh `PIPELINE_HEARTBEAT`, monotonic checkpoint `2023-06-06→2023-06-08`. Census now = mid-backfill snapshot,
  not terminal convergence — same rule-4a/slot-17/18/19/23/24 stale-baseline reasoning. Skipping `reason_code: GATED` +
  `park_now: true`. **Unpark**: when running `af-backfill-*` count == 0, re-run both census scripts + confirm all 8
  entities stable ~0 / honest-absence floors, then close this doc + notify operator. No code changes; Progress Log only.
- **2026-08-11T16:53Z (slot 21, `sports_af_full_entity_completion-9798da269f23` re-dispatch)**: done-when STILL unmet —
  `gcloud compute instances list` shows only `af-backfill-20260811-162726` RUNNING (`af-backfill-20260810-162910`
  TERMINATED, matches slot-32). Verified genuine live progress directly via `run.log` (UTL `download_bytes`, not
  `gsutil` — blocked by the destructive-command guardrail; not just `gcloud list`/serial-console boot noise, which
  doesn't carry app-level output): monotonic `[[VM_PROGRESS]] last_completed_date=2023-07-05→2023-07-06` at `16:53:33Z`,
  real `ManifestWriter` per-VM shard write (23,010 entries, +767 new) moments before this check — advanced well past
  slot-32's `2023-06-06→2023-06-08` checkpoint 17 min earlier, confirming continuous forward progress, not a stall.
  Census now = mid-backfill STANDINGS snapshot, not terminal convergence — same rule-4a/slot-17/18/19/23/24/32
  stale-baseline reasoning. Skipping `reason_code: GATED` + `park_now: true`. **Unpark**: when running `af-backfill-*`
  count == 0, re-run both census scripts + confirm all 8 entities stable ~0 / honest-absence floors, then close this
  doc + notify operator. No code changes; Progress Log only.
