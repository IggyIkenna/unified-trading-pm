---
title: "Non-API-Football Sports Provider Backfill Launchers (Transfermarkt / FootyStats / OpenMeteo / Understat)"
priority: P1
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: deployment-service
    code: C0
depends_on: []
isProject: false
---

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

| File                                              | Reference                                                                           |
| ------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `launch-api-football-backfill-vm.sh`              | Template — copy the argparse + singleton-lock + metadata wiring shape.              |
| `launch-sfi-forward-poll.sh`                      | Sibling example — simpler shape, same metadata.                                     |
| `launch-footystats-forward-poll.sh`               | Existing FootyStats launcher — check what it takes + what's missing for historical. |
| `setup-data-pipeline-vm.sh` §line 451+            | Generic VM_TASK fallback consumes VM_SPORTS_PROVIDER — works for every provider.    |
| `codex/02-data/sports-scheduling-and-sharding.md` | §2 provider-by-provider cadence + data-publication rules.                           |

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

- [ ] [AGENT] P0. Copy `launch-api-football-backfill-vm.sh` → `launch-transfermarkt-backfill-vm.sh`. Rename prefix
      `af-backfill-` → `tm-backfill-` throughout. Swap `VM_SPORTS_PROVIDER=API_FOOTBALL` → `TRANSFERMARKT`. Entity list:
      `PLAYER_VALUES | TRANSFERS | TEAM_SQUAD | TRANSFERMARKT_LEAGUES`. Header comment cites codex §2.2 for cadence +
      publication rules.

### Phase 2: FootyStats launcher [PARALLEL]

- [ ] [AGENT] P0. Sibling to `launch-footystats-forward-poll.sh` but for explicit historical ranges + rolling windows.
      Prefix `fs-backfill-`. Entity list: `FIXTURES | MATCH_STATS | ODDS_SNAPSHOTS | PREDICTIONS | PLAYER_PERFORMANCE`.
      Header: codex §2.3 re 6-24h publication lag for MATCH_STATS.

### Phase 3: OpenMeteo launcher [PARALLEL]

- [ ] [AGENT] P0. `launch-openmeteo-backfill-vm.sh`. Prefix `weather-backfill-`. VM_SPORTS_PROVIDER=OPEN_METEO. Entity
      is singular: `WEATHER`. **Remove singleton-lock** — no API key, concurrent VMs safe. Header: codex §2.5 re
      forecast vs ERA5 archive branching.

### Phase 4: Understat launcher [PARALLEL]

- [ ] [AGENT] P0. `launch-understat-backfill-vm.sh`. Prefix `us-backfill-`. VM_SPORTS_PROVIDER=UNDERSTAT. Entity: `XG`.
      Smaller window (6 leagues only — codex §2.6). Understat fetches per `(league, season)` so the adapter iterates
      season keys, not dates; date range selects which seasons overlap. Document this in the header comment.

### Phase 5: Smoke + QG [SEQUENTIAL]

- [ ] [AGENT] P0. For each launcher, launch one VM on a known-good date: - Transfermarkt:
      `--entity PLAYER_VALUES 2024-09-01 2024-09-01` - FootyStats: `--entity ODDS_SNAPSHOTS 2024-09-01 2024-09-01` -
      OpenMeteo: `--entity WEATHER 2024-09-01 2024-09-01` - Understat: `--entity XG 2024-09-01 2024-09-01` Each VM must
      land its parquet + self-delete (vm-exec-with-gcs-tee.sh fix from deployment-service beaa2e5).

- [ ] [AGENT] P0. `bash deployment-service/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. Commit + quickmerge (`--agent`).

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
