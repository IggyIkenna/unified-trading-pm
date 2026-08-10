---
doc_type: issue
title: >-
  API-Football sports completion campaign residual: ~976-object tail (fresh 2026-08-10 re-census) has no tracked owner —
  the re-census gate in sports_af_full_entity_completion_2026_08_03.md is parked pending ~0, but no todo runs the
  residual completion pass.
summary: >-
  Slot 25's 2026-08-10 re-census of the 8 in-scope AF entities found a ~976-object residual tail (was 146,640):
  PLAYER_STATS 3 · INJURIES 334 · STANDINGS 271 · TEAMS 96 · FIXTURE_STATS 136 · FIXTURE_LINEUPS 136, ~all
  `expected_unattempted`/absent tail, 19 TEAMS `attempted_failed`. The completion campaign's P0 re-census gate
  (`sports_af_full_entity_completion_2026_08_03.md`) is durably PARKED by slot 25 because its done-when (~0 needed) is
  unmet — but the residual pass that would actually close the tail was only a prose recommendation in that doc's
  Progress Log, never a tracked todo. This issue owns the completion pass so the campaign can genuinely converge and the
  re-census gate can then pass + the AF plan downgrade.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [sports, api-football, backfill, completion, data-correctness]
related: [/plans/active/issues/sports_af_full_entity_completion_2026_08_03.md]
created: "2026-08-10"
author: main agent (agt-fe67fd) — routing the slot-25 re-census residual (2026-08-10)
source: sports_af_full_entity_completion_2026_08_03.md slot-25 re-census progress entry (2026-08-10)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-data
depends_on: []
---

## Todos

- [ ] [SCRIPT] P1. **Residual completion pass — close the ~976-object tail** (fresh 2026-08-10 re-census, slot 25):
      PLAYER_STATS 3 · INJURIES 334 · STANDINGS 271 · TEAMS 96 · FIXTURE_STATS 136 · FIXTURE_LINEUPS 136 = ~976 (was
      146,640); ~all `expected_unattempted`/absent tail, 19 TEAMS `attempted_failed`. Launch the `af-backfill-*`
      residual pass (`--entity` per remaining non-zero entity, respecting the `af-backfill-*`/`af-audit-*` singleton
      lock — one `af-backfill-*` VM at a time against the shared API key, self-check the lock before launching),
      resuming from each entity's `PROGRESS.json` checkpoint where present. Done when: a fresh re-census shows every
      in-scope entity at ~0 needed (only genuine honest-absence floors remain, e.g. FIXTURE_EVENTS' ~1,943-stub
      pattern), i.e. the re-census gate in `/plans/active/issues/sports_af_full_entity_completion_2026_08_03.md` can
      pass. Then unpark/flip the re-census condition (`auto_unpark__sports_af_full_entity_completion-9798da269f23`) so
      it dispatches and closes that doc. (repo: instruments-service / market-tick-data-service)

## Progress Log

- **2026-08-10 (main agent, agt-fe67fd)**: Filed this doc to give the slot-25 re-census residual an owner. The re-census
  task `sports_af_full_entity_completion-9798da269f23` is durably parked (cooldown GATED + prereq
  `auto_unpark__...-9798da269f23`=0, set_by slot-25 2026-08-10 09:51:52) and correctly so — its done-when (~0) is unmet.
  But nothing tracks the ~976-object completion pass itself; this doc owns it. Fleet impact of leaving it unowned: the
  parked re-census is the top idle-blocker-inferred source (17 events) holding ~270 downstream tasks.
- **2026-08-10 (slot 15, data_engineering)** — Residual completion pass started:
  - Fresh census (`census_all_af_entities_completion_2026_08_03.py`) confirmed slot 25's numbers byte-for-byte:
    PLAYER_STATS needed=3 · INJURIES needed=334 · STANDINGS needed=271 · TEAMS needed=96 (grand total 704 across 4
    entities). FIXTURE_STATS (136) + FIXTURE_LINEUPS (136) still from slot 25's snapshot = ~976 total.
  - No `af-backfill-*`/`af-audit-*` VMs were running (singleton lock clear). Live API-Football `/status`:
    remaining_daily_quota=135,443 (healthy).
  - **Launched `af-backfill-20260810-102659`** (SPOT, `--entity INJURIES 2020-06-06 2026-08-10`) — vanished during boot,
    likely SPOT preemption before `run.log` was written. **Re-launched `af-backfill-20260810-103218`** (on-demand,
    `e2-standard-8`, same range/entity) — confirmed RUNNING and healthy via SSH at 10:35Z: `instruments_chunk_loop.sh`
    active, chunk 1 processing dates from 2020-06-14, fetching INJURIES, rate-budget 167 req/min, manifest per-VM shard
    writing. Fetched 0 INJURIES for early dates (2020-06-14, 2020-06-15 — expected for COVID-era sparse fixture
    calendar). VM left running; next entities (STANDINGS/TEAMS/FIXTURE_STATS/FIXTURE_LINEUPS/PLAYER_STATS) queued behind
    the singleton lock. Will monitor for completion via run.log → exit_code.
  - **Session compacted 2026-08-10 ~11:00Z** — VM still mid-flight. Deferred work table below.

    - **2026-08-10 (slot 15, data_engineering, post-compact resume ~12:00Z)** — Resumed, VM still RUNNING:
      - Progress: `last_completed_date=2021-11-26` via SSH (GCS tee shows `2021-11-24`, normal lag). Pace ~10 dates/min,
        ~3 more hours to complete the full 2020-06-06 to 2026-08-10 range.
      - Confirmed all-entity invocation: omitting `--entity` from the launcher defaults to "all entities" mode (line
        308: `ENTITY_DESC="all entities"`). Strategy: a single all-entity VM will close the 5 remaining entities
        (STANDINGS/TEAMS/FIXTURE_STATS/FIXTURE_LINEUPS/PLAYER_STATS) in one pass rather than 5 sequential launches.
      - **Session compacted 2026-08-10 ~13:30Z** — VM still mid-flight: (see deferred work table below for latest)

      - **Session compacted 2026-08-10 ~11:45Z** — VM still mid-flight: (see deferred work table below for latest)

      - **Session compacted 2026-08-10 ~11:48Z** — VM still RUNNING:
        - Progress: `last_completed_date=2022-05-01` (local SSH, 11:48Z), `2022-04-23` (GCS tee, normal lag). ~695/2257
          days done (~31%). Pace steady at ~7-10 dates/min. ETA to completion: ~2.6-3.7h → finish ~14:30-15:30Z.
        - VM healthy: `instruments_chunk_loop.sh` + `heartbeat_daemon.py` both running, PIPELINE_HEARTBEAT emitting.

      - **Session compacted 2026-08-10 ~11:53Z** — VM still RUNNING:
        - Progress: `last_completed_date=2022-06-11` (local SSH, 11:52Z), `2022-05-26` (GCS tee, normal ~15-date lag).
          ~735/2257 days done (~33%). Pace steady at ~10 dates/min. ETA to completion: ~2.5h → finish ~14:40Z.
        - VM healthy: `instruments_chunk_loop.sh` + `heartbeat_daemon.py` both running.

      - **Session resumed 2026-08-10 ~12:00Z (post-compact)** — VM still RUNNING:
        - Progress: `last_completed_date=2022-07-18` (GCS tee, ~11:56Z); SSH unavailable (transient). GCS tee lag
          typically ~15 dates behind local → local est. `~2022-08-02`. ~772-787/2256 days done (~34-35%). Pace steady at
          ~10 dates/min. ETA: ~14:25Z.
        - VM confirmed RUNNING via GCS tee progression + `gcloud compute instances list`; `heartbeat_daemon.py`
          emitting. Monitors re-armed: run.log poll + 30-min watchdog.

      - **Session compacting 2026-08-10 ~12:15Z** — VM still RUNNING:
        - Progress: GCS tee `last_completed_date=2022-08-27` (monitor `bwf612ii7`/`bpe60pooj`). ~812/2256 days done
          (~36%). Pace steady at ~10 dates/min. ETA: ~14:40Z.
        - SSH remains unavailable (transient, same as prior session). VM healthy per GCS tee progression + watchdog.

      - **Session compacting 2026-08-10 ~12:04Z** — VM still RUNNING:
        - Progress: GCS tee `last_completed_date=2022-09-28` (direct `gsutil cat`). ~844/2256 days done (~37%). Pace
          steady at ~10 dates/min, ~1412 days remaining → ETA ~14:25Z.
        - VM confirmed RUNNING via `gcloud compute instances list`; no `exit_code=` yet (expected — still mid-flight).

      - **Session compacting 2026-08-10 ~12:09Z** — VM still RUNNING:
        - Progress: GCS tee `last_completed_date=2022-10-23` (~39%), ~1387 days remaining. Pace steady at ~10 dates/min.
          ETA ~14:30Z.
        - VM confirmed RUNNING via `gcloud compute instances list`; no `exit_code=` yet (mid-flight). Monitors re-armed.

## Deferred work after 2026-08-10 ~12:09Z

| Item                                                                                                                | State / why deferred                              | Blocked on                                                                                           |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **INJURIES backfill** (`af-backfill-20260810-103218`)                                                               | RUNNING, GCS tee `2022-10-23` (~39%), ETA ~14:30Z | VM completion (real infra)                                                                           |
| **All-entity backfill** (STANDINGS 271 + TEAMS 96 + FIXTURE_STATS 136 + FIXTURE_LINEUPS 136 + PLAYER_STATS 3 = 642) | Queued — singleton lock held by INJURIES VM       | INJURIES VM exit_code                                                                                |
| **Re-census to confirm ~0**                                                                                         | Gated on all backfills converging                 | All entity backfills complete                                                                        |
| **Unpark `sports_af_full_entity_completion-9798da269f23`**                                                          | Gated on re-census ~0                             | `POST /api/prerequisites/auto_unpark__sports_af_full_entity_completion-9798da269f23 {"value": true}` |

**Recommended NEXT item**: Check `af-backfill-20260810-103218` status:

```bash
gcloud compute instances list --filter='name=af-backfill-20260810-103218' --format='table(name,status)'
# If TERMINATED: check exit_code:
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260810-103218/run.log | grep 'exit_code=' | tail -1
# If exit_code=0: launch ALL-ENTITY VM (no --entity) to close remaining 5 entities in one pass:
cd deployment-service && bash scripts/vm/launch-api-football-backfill-vm.sh --on-demand 2020-06-06 2026-08-10
# If RUNNING: monitor until completion, then launch all-entity VM
```

**Strategy for follow-up**: a single all-entity VM (no `--entity` flag) is now preferred over sequential entity-scoped
launches. Campaign history shows entities resolve in lockstep and the chunk-loop architecture handles all entities
efficiently in one pass. Validated from launcher source (line 308: `ENTITY_DESC="all entities"` when `$ENTITY` is
empty). Always use `--on-demand` — `asia-northeast1-c` SPOT preemption killed the first launch
(`af-backfill-20260810-102659`) before it could write `run.log`.
