---
doc_type: plan
title: Retire the AO FailoverLoop — cross-host machinery under a single-VM architecture
summary:
  FailoverLoop re-routes tasks when a HOST goes offline, but multi-VM dispatch was deprecated 2026-06-27 in favour of
  one central VM. It is stopped, has never fired, and has zero fleet-registry entries to act on. Delete the loop, its
  routes, its knobs and its wiring — which also removes the paused-slot preference bug it harbours — then rule on the
  vestigial per-task failover fields it leaves behind.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, deprecation, cleanup, single-vm, dispatch]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# Retire the AO FailoverLoop

> **Operator ruling A5, 2026-07-20**: DELETE. Provenance: the B3 audit in
> `ao_open_issues_consolidated_close_out_2026_07_17.md`, where both the failover P3 and the paused-slot P2 are now
> marked SUPERSEDED and moved here.

## Why retire rather than fix

`server/failover.py` exists to re-route soft-pinned tasks when a **host** (e.g. `harsh-pc`) goes offline. Multi-VM
dispatch was **deprecated 2026-06-27** in favour of the single central VM with role-based dispatch (`assigned_vm` ∈
`{planning, NA}`). Measured on the live VM 2026-07-20: `ORCHESTRATOR_FAILOVER_ENABLED` unset (default `False`),
`/api/ops/failover/status` → `{"running": false, "status": "stopped"}`, **0 `failover_rerouted` events for all time**,
and `fleet_registry_entries: 0` — it has no registry data to act on even if enabled.

It also harbours a real bug: `_pick_least_loaded_slot` filters only the offline host's slots — not `paused`, `killed` or
review slots — and its load metric is pinned-task count, which is **0 for a paused slot by definition**, so it picks
paused slots _preferentially_. **Deleting the module removes that bug without writing the guard**, which is why the
paused-slot fix was superseded rather than scheduled.

## Scope correction — read before estimating

The initial framing ("delete the module + 3 knobs") **understated this**. There are two distinct scopes:

| Scope                      | What                                                                                                                                                     | Risk                                              |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| **The LOOP** (todos 1-4)   | `server/failover.py`, `tests/test_failover.py`, 2 routes in `routes/ops.py`, wiring in `server.py` (~L235-245), 3 config knobs                           | Low — self-contained, nothing consumes it         |
| **The FIELDS** (todos 5-6) | `TaskRow.failover_allowed` / `failover_origin` in `orm.py`, `bootstrap.py`, `backlog.py`, `models/backlog.py`, `routes/backlog.py`, `regen_backlog_*.py` | Higher — DB columns + a plan-authoring convention |

Do **not** conflate them. The loop delete is clean; the fields carry a documented plan-authoring convention
(`failover_allowed: false` as a task-line annotation) that becomes a no-op the moment the loop is gone, and dropping
SQLite columns is migration risk for no functional gain.

## Todos

- [ ] [BACKEND] P3. **Delete the loop and its tests.** Remove `server/failover.py` and `tests/test_failover.py`. Per
      CLAUDE.md, DELETE — no deprecation shim, no re-export stub. **Gate**: files gone; no import of `failover` or
      `FailoverLoop` remains anywhere (`rg 'FailoverLoop|import failover'` returns only historical comments you also
      clean up).
- [ ] [BACKEND] P3. **Remove the runtime wiring and routes.** Drop the FailoverLoop construction + fleet-getter in
      `server/server.py` (~L235-245) and the `POST /api/ops/failover/enable` + `GET /api/ops/failover/status` endpoints
      in `server/routes/ops.py`, including the `_state["failover"]` slot. **Gate**: the server boots clean; both routes
      return 404; no `KeyError`/`None`-deref path remains where `_state.get("failover")` was read.
- [ ] [BACKEND] P3. **Remove the three config knobs.** `failover_interval_seconds`,
      `failover_heartbeat_threshold_seconds` (tuning) and `failover_enabled` (env-read, `ORCHESTRATOR_FAILOVER_ENABLED`)
      in `server/config.py`. Purge the env var from `scripts/bootstrap_vm.sh` with a `_remove_env` line so an existing
      VM's `.env.local` is cleaned on next bootstrap — **setting an unknown env var is silent, so leaving it behind is a
      trap, not a leftover**. Update `docs/ENV_VARS.md`. **Gate**: `rg -i failover` over `server/config.py`,
      `scripts/bootstrap_vm.sh` and `docs/ENV_VARS.md` is clean; the removal is listed in ENV_VARS' retired-vars
      section.
- [ ] [BACKEND] P3. **Check the dispatch comment that cites failover's threshold.** `server/dispatch.py`'s
      `_target_slot_is_dead` documents `high_affinity_spill_after_seconds` as "matching `failover.py`'s offline
      threshold". That cross-reference dies with the module — restate the rationale on its own terms rather than leaving
      a pointer to a deleted file. **Gate**: no comment in the tree references `failover.py` as a live authority.
- [ ] [BACKEND] P3. **Rule on the vestigial task fields — recommendation: keep the columns, retire the convention.**
      `failover_allowed` / `failover_origin` become inert once the loop is gone. Dropping columns from SQLite is
      migration risk for zero functional gain, so **leave the columns in place** but stop advertising them: remove the
      `failover_allowed: false` task-line annotation from the plan-authoring docs and from
      `regen_backlog_from_plan.py`'s hard-pin parsing, so nobody writes it expecting an effect. Record the decision
      either way. **Gate**: a written ruling; if the convention is retired, no doc or parser still accepts it silently.
- [ ] [BACKEND] P3. **Leave `tests/test_failover_allowed.py` and the regen tests coherent.** Whatever todo 5 decides,
      these tests must assert the NEW truth rather than being deleted to make the suite green. If the annotation is
      retired, they should assert it is no longer honoured. **Gate**: `bash scripts/quality-gates.sh` green in
      `agent-orchestrator` with no test deleted purely to avoid a failure.
- [ ] [BACKEND] P3. **Ship it and confirm the live orchestrator picked it up.** Commit via
      `bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'` from a green tree, then confirm `ao-self-pull.sh`
      FF-pulled and restarted (it runs every ~15 min; the change is NOT live at merge time). **Gate**: the sha is
      present in the orchestrator's own checkout and the service restarted after it landed — cite both.
- [ ] [DOC] P3. **Close the loop in the codex + the consolidated plan.** Note the retirement wherever failover is
      described as live machinery, and tick the superseded entries in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` (the failover P3 and the paused-slot P2) with this plan's
      shas. **Gate**: no doc still describes FailoverLoop as an active recovery layer.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Deleting is the goal, but a green suite is not proof of a safe delete** — if a test fails after removal, understand
  WHY before changing it. A test that breaks may be telling you something still depends on this.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — the single-VM ruling this retirement follows.
- `codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — confirm failover is
  not cited as a live recovery layer; if it is, that doc needs the same edit.
- `codex/06-coding-standards/quality-gates.md` — the gate every todo above commits behind.

## Progress Log

- **2026-07-20 — plan created** on operator ruling A5. Blast radius mapped BEFORE filing: the loop is self-contained (6
  sites), but the per-task `failover_allowed`/`failover_origin` fields reach 8 more files including a plan-authoring
  convention — which is why todos 5-6 exist instead of one glib "delete it" line.
