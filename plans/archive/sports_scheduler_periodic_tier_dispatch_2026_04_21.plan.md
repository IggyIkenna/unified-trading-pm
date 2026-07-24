---
doc_type: plan
title: Sports Scheduler — Periodic Tier Dispatch (Tier-1 Discovery + Tier-2 Reference)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: deployment-service, code: C0, deployment: none, business: none }
depends_on: []
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

`deployment-service/deployment_service/sports_trigger_scheduler.py` currently dispatches **per-fixture triggers only**
(Tier-3 pre-match and Tier-4 post-match). The Tier-1 discovery and Tier-2 reference sections of
`configs/sports-trigger-tiers.yaml` declare `frequency_hours` but **nothing in code reads those keys or fires the
corresponding CLI** — they're read-only intent.

The 2026-04-21 codex SSOT at `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` locks the
rolling-window contract (`[today - lookback_days, today + lookahead_days]` with `force_overwrite: true`). This plan
wires that contract into the scheduler so the cron that already runs `python -m deployment_service sports-trigger` every
few minutes will actually fire Tier-1 + Tier-2 at their declared cadences.

### Blast radius

- **deployment-service**:
  - `deployment_service/sports_trigger_scheduler.py` — add periodic-tier loop (currently only has per-fixture dispatch
    at line 385+). State file / Firestore doc for `last_run[tier_name]` tracking. Reuse existing `_dispatch_local` /
    cloud dispatch paths.
  - `deployment_service/cli/commands/sports_trigger.py` — ensure the CLI entrypoint's main loop invokes periodic-tier
    check every poll.
  - `configs/sports-trigger-tiers.yaml` — already enriched (2026-04-21 commit `8b98449`) with `rolling_window` block
    under `discovery`. No changes needed here but Phase 3 reads the new keys.
  - `deployment_service/cloud_run/` — verify the Tier-1/2 dispatch can target a Cloud Run job (see
    `/codex/02-data/sports-scheduling-and-sharding.md` §8 — default for short periodic jobs is Cloud Run, not VM).
- **instruments-service**: consumer of dispatched CLI invocations. No changes — the existing CLI accepts
  `--start-date` + `--end-date`. (CLI ergonomics flags like `--lookahead-days` are a SEPARATE plan:
  `instruments_service_rolling_window_cli_flags_2026_04_21`. Do not couple.)
- **unified-cloud-interface / unified-trading-library**: none. No new shared types.

### Pre-audit manifest (embedded)

| File                                                | Lines   | Current state                                                                                                  | Action                                                                                                  |
| --------------------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `deployment_service/sports_trigger_scheduler.py`    | 100-135 | `__init__` loads YAML config. No periodic-tier state init.                                                     | Add `_last_run: dict[tier_name, datetime]` state map + persistence.                                     |
| `deployment_service/sports_trigger_scheduler.py`    | 360-430 | `_dispatch_trigger()` handles per-fixture event; hardcodes `--start-date today --end-date today` (line 398-9). | Extract shared CLI-build helper; per-fixture path keeps today/today; periodic path uses rolling window. |
| `deployment_service/sports_trigger_scheduler.py`    | —       | No `_check_periodic_tiers()` method.                                                                           | Add: iterate `discovery` + `reference` sections, check if frequency elapsed, fire.                      |
| `deployment_service/cli/commands/sports_trigger.py` | 15-60   | CLI runs a main poll loop. Polls fixture calendar, fires per-fixture triggers.                                 | Extend loop to call `_check_periodic_tiers()` each iteration.                                           |
| `configs/sports-trigger-tiers.yaml`                 | 12-39   | Tier-1 `discovery` has `frequency_hours: 6` + new `rolling_window` block.                                      | Read-only. Phase 3 consumes these keys.                                                                 |
| `configs/sports-trigger-tiers.yaml`                 | 29-50   | Tier-2 `reference` has `frequency_hours: 24` + `run_always` / `window_condition`.                              | Read-only. Phase 3 honours `window_condition: transfer_window_open` via UAC.                            |

### State persistence

The scheduler must persist `last_run[tier_name]` across restarts. Current scheduler has an in-memory `TriggerState()`
for per-fixture firing (line 113). Extend that with a periodic-tier map OR add a sibling `PeriodicTierState` class.

Options for persistence backend (decide in Phase 1):

1. **Firestore doc** `sports_scheduler_state/{env}` — same pattern as other deployment-service state. Favoured.
2. **Local file** `/var/deployment-service/sports_scheduler_state.json` — simpler, but loses state on Cloud Run instance
   recycle.
3. **GCS object** `gs://deployment-scripts-.../sports_scheduler_state.json` — works for Cloud Run but adds GCS
   roundtrip.

Pick Firestore unless an existing state mechanism already uses one of the others.

### Success criteria

- Tier-1 discovery fires every 6h with the computed rolling window `[today-1, today+7]` (per `rolling_window` config),
  hitting every declared service in the tier.
- Tier-2 reference fires every 24h; respects `window_condition: transfer_window_open` by calling UAC
  `is_transfer_window_open(league_id, today)` — fires only when true.
- `force_overwrite: true` propagates to the CLI as `--redo-all` (or equivalent) so manifests inside the rolling window
  are re-fetched.
- Scheduler restart preserves `last_run` state — no double-fire, no skip-one-cycle.
- Dry-run mode (`--dry-run`) logs what would fire without dispatching.
- Cloud Run backend supported (`_backend="cloud"`) — if the existing code has a
  `TODO: integrate with CloudRunBackend.deploy_shard()` stub (observed at line 425 in the current file), this plan does
  NOT need to fully implement it, but must route Tier-1/2 through the same stub path as per-fixture triggers so turning
  on cloud backend later is a one-line change.
- Quality gates: `bash deployment-service/scripts/quality-gates.sh` green.
- Unit tests cover: time-based firing logic, state persistence, window condition gating, rolling-window CLI assembly.

## Phases

### Phase 1: State persistence + shared CLI builder [SEQUENTIAL]

- [x] [AGENT] P0. Decide state-persistence backend (Firestore doc, local file, or GCS). Grep `deployment-service/` for
      any existing state-file pattern (`deployments_registry`, `vm_state`, etc.) and match that. If nothing exists,
      default to Firestore. Document decision in a 3-line comment at the top of the periodic-tier code.

- [x] [AGENT] P0. Extract current per-fixture CLI assembly at `sports_trigger_scheduler.py:392-407` into a helper
      `_build_cli_cmd(service, operation, category, start_date, end_date,     extra_args, force_overwrite=False)`.
      Per-fixture path calls with `start_date == end_date == today`. Periodic path will call with rolling window.

- [x] [AGENT] P0. Add `PeriodicTierState` class with `get_last_run(tier_name) / set_last_run(tier_name, when)` methods.
      Persist via the chosen backend. Load once at scheduler startup; write after each successful dispatch.

- [x] [AGENT] P0. Unit tests for `_build_cli_cmd` (both per-fixture and rolling-window shapes) + `PeriodicTierState`
      (round-trip persistence).

### Phase 2: Tier-1 discovery dispatch [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. Add `_check_discovery()` method: iterate the `discovery` section of the YAML config, for each tier
      entry compute whether `now - last_run[tier_name] >= timedelta(hours=frequency_hours)`, and if so, fire all
      declared services with the rolling window.

- [x] [AGENT] P0. Rolling window computation: read `discovery.rolling_window.lookback_days` (default 0) and
      `discovery.rolling_window.lookahead_days` (default 0). Compute `start_date = today - lookback_days`,
      `end_date = today +     lookahead_days`. If absent, use single-day `today..today`.

- [x] [AGENT] P0. Force-overwrite wiring: if `discovery.rolling_window.force_overwrite: true`, append `--redo-all` (or
      the current instruments-service equivalent — verify by grepping the CLI arg parser) to the dispatched command so
      skip-if-exists doesn't kick in.

- [x] [AGENT] P0. Call `_check_discovery()` from the main poll loop in `cli/commands/sports_trigger.py` each iteration.

- [x] [AGENT] P1. Unit tests for `_check_discovery()` covering: first-ever run (no state), cadence-elapsed firing,
      cadence-not- elapsed skip, rolling-window date math (today = 2026-04-21 → start=2026-04-20 end=2026-04-28),
      force-overwrite flag presence.

### Phase 3: Tier-2 reference dispatch with window-condition [SEQUENTIAL, depends on Phase 2]

- [x] [AGENT] P0. Add `_check_reference()` method mirroring `_check_discovery()` but reads the `reference` section.

- [x] [AGENT] P0. Window-condition gating: for services with `run_always:     false` and
      `window_condition: transfer_window_open`, call UAC
      `from unified_api_contracts.sports import is_transfer_window_open` for each league the service scopes to. If the
      helper doesn't exist, add it to UAC as part of this phase (simple lookup against the season calendar — see codex
      §7.1). If it's per-league, loop over `get_expected_leagues_for_source("transfermarkt")` and fire the service with
      `--league L1,L2,...` for the leagues whose windows are open.

- [x] [AGENT] P0. Season-boundary gate: on start-of-season and end-of-season days (computed from UAC
      `sports.season_calendar`), fire a one-off `LEAGUES` + `TEAMS` + `STANDINGS` refresh. Declare this in the YAML as a
      new `season_boundary` tier or inline as a reference-tier `window_condition: season_boundary`. Prefer the YAML-
      declaration route for codex consistency.

- [x] [AGENT] P0. Call `_check_reference()` from the main poll loop.

- [x] [AGENT] P1. Unit tests for `_check_reference()`: window-condition gating (true / false / unknown league),
      per-league loop assembly.

### Phase 4: Cloud Run dispatch parity [PARALLEL with Phase 3]

- [x] [AGENT] P1. Verify the existing `_backend="cloud"` stub at line 418-427 still applies — if it's still a TODO,
      leave it TODO but ensure the new periodic dispatch hits the same code path as per-fixture dispatch does (no
      duplicate stub). If the stub has been filled in, route periodic dispatch through it.

- [x] [AGENT] P2. If Cloud Run dispatch works, wire the Tier-1/2 services to use Cloud Run by default (per codex §8 —
      periodic jobs are cheaper on Cloud Run than long-lived VMs). Leave Tier-3/4 on the existing path.

### Phase 5: Dry-run validation + quality gates [SEQUENTIAL]

- [x] [AGENT] P0. Run the scheduler in `--dry-run` mode for one poll cycle with tier frequencies temporarily reduced
      (e.g. `frequency_hours: 0.01` via test fixture). Verify both Tier-1 and Tier-2 fire with the correct rolling
      window + force-overwrite flags.

- [x] [AGENT] P0. `bash deployment-service/scripts/quality-gates.sh` green (ruff, basedpyright, tests, coverage ≥
      baseline).

- [x] [AGENT] P0. Commit + quickmerge (`--agent`, branch auto-read from workspace-manifest.json).

## Dependency graph

```
Phase 1 (state + CLI builder) ─► Phase 2 (discovery) ─► Phase 3 (reference)
                                      │
                                      └─► Phase 4 (Cloud Run) ─┐
                                                               ▼
                                                        Phase 5 (validate)
```

## SSOT cross-refs

- Contract for rolling window + cadences: `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` (§2
  providers, §4 rolling window, §7 transfer-window triggers, §8 Cloud Run vs VM).
- Current scheduler: `deployment-service/deployment_service/sports_trigger_scheduler.py`.
- Tier config: `deployment-service/configs/sports-trigger-tiers.yaml`.
- UAC helpers: `unified_api_contracts.sports.get_expected_leagues_for_source`, `get_league_fixture_calendar`,
  `is_transfer_window_open` (new, may need authoring in Phase 3).

## Out of scope

- **CLI flag ergonomics** (`--lookahead-days`, `--force-window`) — separate plan
  `instruments_service_rolling_window_cli_flags_2026_04_21`. This plan computes the window server-side in the scheduler;
  operators manually launching runs can wait for that plan.
- **Feature-pipeline denormalisation** — separate plan `features_sports_denormalisation_pipeline_2026_04_21`.
- **Match-state-driven odds polling refinements** — the existing Tier-3 T-24h/T-6h/T-1h triggers already cover
  pre-match. In-play live loop is owned by market-tick-data-service, not this scheduler.
