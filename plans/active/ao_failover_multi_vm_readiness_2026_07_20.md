---
doc_type: plan
title: AO failover — keep it, fix the paused-slot bug, and prove the dormant path actually works
summary:
  Multi-VM is dormant but intended to return for resilience, so FailoverLoop is KEPT (operator 2026-07-20, reversing the
  earlier delete ruling). It has never fired once, has zero fleet-registry entries, and prefers paused slots as re-route
  targets — untested resilience machinery is worse than none. Fix the slot-selection bug and prove the offline-reroute
  and rollback paths before anyone relies on them.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, failover, resilience, multi-vm, dormant-infra]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md, ao_dispatch_liveness_p0_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
model_tier: sonnet-doable # test-writing against one existing module + a docs/runbook deliverable
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# AO failover — keep it, fix it, and prove it works

> **Operator ruling 2026-07-20 (REVERSES the earlier A5 "delete")**: multi-VM is not running today, but it is likely to
> return for resilience/backup, so the failover infrastructure is **KEPT**. The retirement plan drafted earlier was
> removed before any worker saw it (verified: 0 ingested tasks).

## Why this is a real plan and not just a one-line guard fix

The earlier reasoning — "it never fires, so delete it" — inverts once you intend to **rely** on it. Everything measured
on 2026-07-20 now reads as a warning rather than an obituary:

- `ORCHESTRATOR_FAILOVER_ENABLED` unset (default `False`), `/api/ops/failover/status` → `{"running": false}`.
- **0 `failover_rerouted` events for all time** — the re-route path has never executed in production, ever.
- `fleet_registry_entries: 0` — even if enabled today it has no registry data to act on.
- `_pick_least_loaded_slot` **prefers paused slots** (see below).

That is the profile of resilience machinery nobody has ever exercised. **Untested failover is worse than no failover**:
it invites reliance during exactly the incident where its first-ever execution will be discovered to be broken. The work
below makes it dormant-but-trustworthy.

## Execution environment — LOCAL (read this first)

Executed by **operator-assigned agents on this host**, not AO dispatch (`assigned_vm: NA`,
`execution_scope: local-only`). Tick checkboxes by hand.

**This plan is almost entirely local** — todos 1-3 and 5-7 are code, tests and docs in the `agent-orchestrator`
checkout, verified with `bash scripts/quality-gates.sh`. Todo 4 (the `fleet_registry_entries: 0` trace) starts as a
local code read; only confirming the live registry state needs read-only SSM (pattern in
`scripts/orchestrator/check-ao-backlog-status.sh`).

**Do not enable failover anywhere** — see Safeguards. Everything here is provable with tests against the loop directly.

## The slot-selection bug (the concrete defect)

`failover._pick_least_loaded_slot` selects over `select(SlotRow)` filtered ONLY by `exclude_slots` (= the offline host's
slots). It does **not** filter `paused`, `killed`, or review slots. Worse, its load metric is "fewest
queued-and-undispatched tasks pinned to it", and a paused slot has **zero by definition** — nothing dispatches to it —
so `min()` picks a paused slot **preferentially**. Re-routing a task onto the one slot guaranteed never to run it
strands it invisibly, re-creating the exact class the R5 dead-target spill was written to fix. **Slot 0 is paused right
now** and would be today's preferred target.

## Todos

- [ ] [BACKEND] P2. **Exclude unusable slots from failover target selection.** In `failover._pick_least_loaded_slot`,
      filter out `paused` / `killed` and review slots in addition to `exclude_slots`. **Also fix the metric bias, not
      just the guard** — "fewest pinned tasks" will keep nominating any slot that structurally cannot receive work, so
      the selection must be over ELIGIBLE slots, not all slots minus a blocklist. **Gate**: a test with a paused slot
      carrying 0 pinned tasks alongside a busy eligible slot asserts the eligible slot wins; a second test asserts
      `None` (→ the existing "no available slot" skip) when every candidate is ineligible.
- [ ] [BACKEND] P2. **Prove the offline-reroute path end-to-end — it has NEVER executed.** Write an integration test
      that simulates a host going offline past `failover_heartbeat_threshold_seconds`, and asserts eligible tasks
      (`failover_allowed=True`, queued, undispatched, `failover_origin` NULL) are re-pointed to an eligible slot with a
      `failover_rerouted` activity row. **Gate**: the test fails if the loop is a no-op — verify by bug-injection (break
      the re-route, confirm the test goes red).
- [ ] [BACKEND] P2. **Prove the ROLLBACK path too.** When the offline host returns, tasks still queued and unclaimed
      must have `target_slot` + `failover_origin` cleared. An un-exercised rollback is how a recovered host stays
      starved after the incident. **Gate**: a test covering return-from-offline; assert already-dispatched tasks are NOT
      rolled back (only queued+unclaimed), so a live worker is never yanked.
- [ ] [BACKEND] P2. **Explain `fleet_registry_entries: 0` — the gap that makes failover inert even when enabled.** Trace
      what populates `fleet_registry.json` and why it is empty under the single-VM topology. Failover keys "offline
      host" off that registry, so an empty registry means the loop can never fire regardless of the enable flag.
      **Gate**: a written answer covering (a) what writes the registry, (b) whether it would populate when multi-VM
      returns, (c) whether an empty registry should be a loud warning at startup when `failover_enabled=True` — silence
      here is what would make a resilience feature fail closed without telling anyone.
- [ ] [BACKEND] P3. **Write the re-enable checklist — the deliverable that makes dormancy safe.** A short runbook
      section: what must be true before `ORCHESTRATOR_FAILOVER_ENABLED=true` (registry populated, ≥2 hosts, the tests
      above green, the paused-slot fix deployed), and how to verify the first real re-route. Declare `owner` / `cadence`
      / `verifier` / `last_executed` per the runbook rule. **Gate**: an operator can re-enable failover from the
      checklist alone without re-deriving any of this.
- [ ] [BACKEND] P3. **Keep the dormant module from rotting.** Confirm `failover.py` and its tests are inside the
      `quality-gates.sh` scope so dormant code cannot silently drift out of type/lint compliance, and add a one-line
      note at the top of the module stating it is DORMANT-BUT-MAINTAINED for multi-VM's return — so the next person
      auditing dead code (as I did) finds the intent instead of re-proposing deletion. **Gate**: the module carries the
      note; QG covers it.
- [ ] [DOC] P3. **Record the dormant-infra position in codex.** Note in the recovery-layers docs that failover is kept
      deliberately, is not currently a live recovery layer, and must not be cited as one until the re-enable checklist
      passes. **Gate**: no codex doc describes FailoverLoop as an active recovery layer, and none describes it as dead.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Do NOT enable failover in production as part of this plan.** Default stays `False`; the enable is an operator action
  gated on the checklist. Tests exercise the loop directly, not by flipping the live flag.

## Codex SSOTs

- `codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — where failover
  does/does not belong as a recovery layer.
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — the current topology this is dormant under.
- `codex/06-coding-standards/quality-gates.md` — the gate keeping dormant code honest.

## Progress Log

- **2026-07-20 — plan created**, replacing a drafted retirement plan after the operator ruled multi-VM is likely to
  return. **Lesson worth keeping**: "it has never fired" was read as evidence the code is dead, when it was equally
  evidence the code is UNTESTED. Which reading is right depends entirely on whether the capability is still wanted — a
  question about intent, not about the code. Ask it before proposing any deletion of dormant infrastructure.
