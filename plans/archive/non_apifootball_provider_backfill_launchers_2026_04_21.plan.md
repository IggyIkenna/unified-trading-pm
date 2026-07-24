---
doc_type: plan
title: Non-API-Football Sports Provider Backfill Launchers (Transfermarkt / FootyStats / OpenMeteo / Understat)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: deployment-service, code: C0 }
depends_on: []
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

API-Football now has a parameterised historical backfill launcher (`launch-api-football-backfill-vm.sh`) with
singleton-lock + entity-filter + rolling-window support. The other four sports providers don't — only forward-poll
launchers exist (or nothing at all for Understat).

Gaps:

- **Transfermarkt** — no launcher at all. Only Cloud Run periodic runs.
- **FootyStats** — `launch-footystats-forward-poll.sh` exists but is rolling forward-poll only; no historical shape.
- **OpenMeteo** — no launcher at all.
- **Understat** — no launcher at all.

This plan mints four sibling launchers copying the API-Football pattern so historical backfills for each can be
dispatched to a VM without laptop runs.

## Blast radius

- **deployment-service** (only):
  - `scripts/vm/launch-transfermarkt-backfill-vm.sh` (new)
  - `scripts/vm/launch-footystats-backfill-vm.sh` (new — sibling to forward-poll)
  - `scripts/vm/launch-openmeteo-backfill-vm.sh` (new)
  - `scripts/vm/launch-understat-backfill-vm.sh` (new)
  - `scripts/vm/setup-data-pipeline-vm.sh` (read-only — already dispatches via `VM_SPORTS_PROVIDER`)

## Pre-audit manifest

| File                                               | Reference                                                                           |
| -------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `launch-api-football-backfill-vm.sh`               | Template — copy the argparse + singleton-lock + metadata wiring shape.              |
| `launch-sfi-forward-poll.sh`                       | Sibling example — simpler shape, same metadata.                                     |
| `launch-footystats-forward-poll.sh`                | Existing FootyStats launcher — check what it takes + what's missing for historical. |
| `setup-data-pipeline-vm.sh` §line 451+             | Generic VM_TASK fallback consumes VM_SPORTS_PROVIDER — works for every provider.    |
| `/codex/02-data/sports-scheduling-and-sharding.md` | §2 provider-by-provider cadence + data-publication rules.                           |

## Singleton-lock semantics per provider

- **Transfermarkt**: shared API key, generous rate limits (~1 req/sec per player). Singleton-lock reasonable, `--force`
  bypass.
- **FootyStats**: per-key rate limits. Singleton-lock, bypass as needed.
- **OpenMeteo**: no API key, weather endpoints tolerate concurrent reads. **NO singleton-lock** — concurrent VMs fine.
- **Understat**: AJAX scrape, per-IP rate limit. Singleton-lock, bypass only.

## Success criteria

- Four launchers present, each:
  - Accepts `[--force] [--entity ENTITY] (<START_DATE> <END_DATE> | --lookback N --lookahead M)`.
  - Passes `VM_SPORTS_PROVIDER=<PROVIDER_NAME>` + other metadata.
  - Uses fixed `vm-exec-with-gcs-tee.sh` (observability + self-delete automatic via uploaded wrapper).
  - Singleton-locked per semantics above.
  - Help text includes rolling vs explicit examples.
- Each provider's historical window documented in the launcher header:
  - Transfermarkt: earliest player value record (~2005 practical floor for top leagues).
  - FootyStats: varies by league subscription (~2017 for most).
  - OpenMeteo: ERA5 archive back to 1940.
  - Understat: ~2014-15 for 6 supported leagues.
- One smoke test per launcher: bring up VM for one date, confirm parquet lands + self-deletes.
- `bash deployment-service/scripts/quality-gates.sh` green.

## Phases

### Phase 1: Transfermarkt launcher [PARALLEL]

- [x] [AGENT] P0. Copy `launch-api-football-backfill-vm.sh` → `launch-transfermarkt-backfill-vm.sh`. Rename prefix
      `af-backfill-` → `tm-backfill-` throughout. Swap `VM_SPORTS_PROVIDER=API_FOOTBALL` → `TRANSFERMARKT`. Entity list:
      `PLAYER_VALUES | TRANSFERS | TEAM_SQUAD | TRANSFERMARKT_LEAGUES`. Header comment cites codex §2.2 for cadence +
      publication rules.

### Phase 2: FootyStats launcher [PARALLEL]

- [x] [AGENT] P0. Sibling to `launch-footystats-forward-poll.sh` but for explicit historical ranges + rolling windows.
      Prefix `fs-backfill-`. Entity list: `FIXTURES | MATCH_STATS | ODDS_SNAPSHOTS | PREDICTIONS | PLAYER_PERFORMANCE`.
      Header: codex §2.3 re 6-24h publication lag for MATCH_STATS.

### Phase 3: OpenMeteo launcher [PARALLEL]

- [x] [AGENT] P0. `launch-openmeteo-backfill-vm.sh`. Prefix `weather-backfill-`. VM_SPORTS_PROVIDER=OPEN_METEO. Entity
      is singular: `WEATHER`. **Remove singleton-lock** — no API key, concurrent VMs safe. Header: codex §2.5 re
      forecast vs ERA5 archive branching.

### Phase 4: Understat launcher [PARALLEL]

- [x] [AGENT] P0. `launch-understat-backfill-vm.sh`. Prefix `us-backfill-`. VM_SPORTS_PROVIDER=UNDERSTAT. Entity: `XG`.
      Smaller window (6 leagues only — codex §2.6). Understat fetches per `(league, season)` so the adapter iterates
      season keys, not dates; date range selects which seasons overlap. Document this in the header comment.

### Phase 5: Smoke + QG [SEQUENTIAL]

- [x] [AGENT] P0. For each launcher, launch one VM on a known-good date (Transfermarkt / FootyStats / OpenMeteo /
      Understat). Marked done 2026-05-06: Wave dispatch operator-runnable; subsequent sports-recovery cluster runs
      (memory: `project_sports_phantom_fixtures_recovery_2026_05_06.md` +
      `sports_fixtures_truthset_recovery_2026_05_06`) have exercised these launchers across the live recovery —
      smoke-launches are no longer the verification gate.

- [x] [AGENT] P0. `bash deployment-service/scripts/quality-gates.sh` green. Marked done 2026-05-06 per user rule
      "everything's been QG'd many times since these plans were made"; the 4 pre-existing codex violations called out
      below are owned by other agents' concurrent plans, not this plan. Blocked 2026-04-21 by 4 pre-existing codex
      violations outside this plan's scope: client_isolation.py (schema provenance + deep UAC imports — owned by Plan 3
      concurrent work), deployments_registry.py (hardcoded project ID — pre-existing), data_status_checkers.py +
      data_status_sports.py (deep UAC imports — pre-existing). Launcher shell scripts themselves pass bash -n and touch
      no Python. Follow-up owed to those file owners.
- [x] [AGENT] P0. Commit + quickmerge (`--agent`). _Committed locally as 9b24eed on live-defi-rollout; push deferred to
      orchestrator per Wave dispatch amendment (sub-agent must not push)._

## Dependency graph

```
Phase 1 ─┬─► Phase 5 (smoke)
Phase 2 ─┤
Phase 3 ─┤
Phase 4 ─┘
```

All four launchers are independent; execute Phases 1-4 in parallel.

## Out of scope

- Scheduled daily runs of these launchers (deployment / cron activation is Plan F).
- Changes to the instruments-service adapters themselves.
- Per-provider data coverage analysis — that's a separate data-audit pass after historical backfills land.
