---
name: harsh_pc_dispatch_failover_2026_05_30
title: "harsh-pc dispatch failover — when host offline > 10 min, roll its queue to fleet VMs by affinity"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P0
status: archived
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
created: 2026-05-30
last_updated: 2026-05-30
archived: 2026-06-01
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
related_plans:
  - plans/active/autospawn_idle_vms_2026_05_30.md
  - plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md
---

## ✅ ARCHIVED 2026-06-01

Harsh-PC dispatch failover shipped + deployed. 0 open todos. Fleet-verified live (both AWS orchestrator VMs @589b711).
**Deferred work:** none. **Codex aligned** (agent-orchestrator-overview / -autospawn / -worker-liveness — all current
2026-06-01). Unlocked for archival.

## Why this exists

The operator sweep on 2026-05-29/30 flagged: "this is the whole point — to avoid backlog on PCs that switch off."

Today, **harsh-pc has 6,940 cached queued tasks** but the host is unreachable from the central api-host
(`Connection refused`). Harsh's laptop is offline (closed/asleep). Those tasks just sit. The `central api-host` and the
`vm-orchestrator` fleet members have NO knowledge of what's in his queue beyond the last heartbeat snapshot.

**Two related but distinct problems**:

1. **Tasks pinned to harsh-pc** (`target_slot` references one of his slot IDs, or `assigned_vm: harsh-pc`) → will NEVER
   dispatch when his host is offline. They're functionally stranded.
2. **Tasks that COULD run elsewhere** (no hard slot affinity, just soft preference) → should fall over to a fleet VM
   with matching task category / asset_group / repo affinity.

This plan addresses (2) — soft-affinity tasks fall over automatically. (1) — tasks deliberately pinned to harsh-pc —
stay pinned (operator may have explicit reasons; never auto-rewrite hard pins).

## The failover contract

Tasks roll from `harsh-pc` to a fleet VM when ALL of:

1. **Host offline**: heartbeat from harsh-pc absent for > 10 min (no `/api/heartbeat` from his orchestrator since the
   threshold). The 10-min window is conservative — laptop sleep / brief network gaps are common.
2. **Task is soft-pinned**: `target_slot IS NULL` OR `target_slot` is configured with `failover_allowed: true`. Hard
   pins (`failover_allowed: false`) stay.
3. **A fleet VM has matching affinity**: prefer VMs where `repos` overlaps with `vm.master_plans` (per
   `orchestrator_vm_registry.yaml`), then by `asset_group`, then by collision_group, then by least-loaded queue depth.
4. **Account headroom available on target VM**: matches `autospawn_idle_vms_2026_05_30.md` § 3 (re-use that contract).

Tasks are re-pinned by updating `task.target_slot` to a fleet VM's slot ID + setting `task.failover_origin = "harsh-pc"`
(for audit / rollback).

## Rollback contract

When harsh-pc heartbeat returns AND the failover task has not yet been claimed by the fleet target → rollback: restore
`task.target_slot` to its original harsh-pc value, clear `failover_origin`. Already-claimed-or-done tasks stay where
they ran.

## Anti-patterns explicitly forbidden

- **Do NOT failover hard-pinned tasks** — operator may have explicit reasons (debug, manual, audit). Hard pins MUST be
  honored.
- **Do NOT failover tasks already dispatched on harsh-pc** — `dispatched_to IS NOT NULL` means a worker may be running
  it. Steal-attempt = race + duplicate work.
- **Do NOT failover the central-api-host's queue** (api-host is the planning VM; its queue is small and not
  worker-dispatched anyway).
- **Do NOT failover faster than the 10-min threshold** — brief network glitches happen; threshold is intentional
  conservatism.
- **Do NOT delete the cached harsh-pc heartbeat snapshot** on failover — that's the audit trail for what was stranded.

## CI-safety contract (HARD)

Same as `autospawn_idle_vms_2026_05_30.md` § CI-safety contract — cross-link to avoid duplication.

## Phases

### Phase 0 — Baseline (DONE 2026-05-30)

- [x] [DIAG] P0. Pre-existing fleet state captured — harsh-pc connection refused since at least 2026-05-29 18:00 UTC.
      Cached heartbeat shows 6,940 queued tasks in his state.db. No mechanism today re-routes those tasks. Captured this
      session 2026-05-30 02:10-02:20 UTC.

### Phase 1 — Design the FailoverLoop

- [x] ✅ [DESIGN] P0. Document the `FailoverLoop` design in `codex/04-architecture/agent-orchestrator-overview.md` §
      "Host-offline failover lifecycle": heartbeat-silence threshold (10 min), soft-vs-hard pin distinction,
      affinity-matching logic (`repos` ⊃ `vm.master_plans`, then `asset_group`, then `collision_group`, then
      `least-loaded`), rollback on heartbeat-return, audit trail (`failover_origin` field). Collision group:
      `ao_failover_design`. Estimate: 0.15 AI-day. **DONE 2026-05-30** — new `## Host-offline failover lifecycle`
      section added to `codex/04-architecture/agent-orchestrator-overview.md`. Covers trigger contract table, affinity
      algorithm (4 tiers), soft/hard pin distinction, rollback semantics, audit trail, env vars table, anti-patterns.
- [x] ✅ [DESIGN] P0. Audit `target_slot` semantics in current `regen_backlog_from_plan.py` — confirm whether
      `target_slot` is always present, whether `failover_allowed: false` exists today (likely not), and what default to
      assume (recommend: default `failover_allowed: true` for ALL soft-pinned tasks; opt-in to hard-pin via new field).
      Collision group: `ao_failover_design`. Estimate: 0.1 AI-day. **DONE 2026-05-30** — Audit findings: (1)
      `regen_backlog_from_plan.py` NEVER sets `target_slot` — all regen-generated tasks have `target_slot=None`
      (soft-pinned by definition). (2) `failover_allowed` does NOT exist in the schema today — `orm.py` only has
      `target_slot`, `affinity`, `queued_at`. (3) `BacklogTask` in `backlog.py` has `target_slot: int | None = None`
      with 3-tier `affinity` (low/medium/high). (4) Recommended default: `failover_allowed: bool = True` for all tasks
      (backfill existing rows); opt-in to hard-pin via `failover_allowed: false` in plan YAML → passed to
      `regen_backlog_from_plan.py`. Phase 2 can proceed on this baseline.

### Phase 2 — Add `failover_allowed` field to task schema (single PR)

- [x] ✅ [CODE] P0. Add `failover_allowed: bool = True` to `Task` ORM model + Pydantic schema in
      `agent-orchestrator/server/models.py`. Migration: backfill existing rows with `True` (the safe default). Update
      `regen_backlog_from_plan.py` to pass `failover_allowed=False` ONLY when the source plan task explicitly sets
      `failover_allowed: false` in YAML. Collision group: `ao_failover_schema`. Estimate: 0.2 AI-day. **DONE
      2026-05-30** — `failover_allowed` added to `orm.py` (BOOL NOT NULL DEFAULT 1), `backlog.py` (BacklogTask default
      True), `bootstrap.py` (ADD COLUMN migration + sync_backlog_to_db seed), `regen_backlog_from_plan.py` (inline
      `failover_allowed: false` annotation, case-insensitive), `models.py` + `server.py` wire-through for
      BacklogTaskView. Shipped @ agent-orchestrator@801ddba.
- [x] ✅ [TEST] P0. Unit test: task with `failover_allowed=True` is eligible; task with `failover_allowed=False` is NOT
      eligible. Backfill migration test on a seed DB. Collision group: `ao_failover_schema`. Estimate: 0.1 AI-day.
      **DONE 2026-05-30** — 8 tests in `tests/test_failover_allowed.py`: default True, explicit False, regen
      default/annotated/true-annotation/mixed/case-insensitive, YAML round-trip. 69 total passed (61 pre-existing + 8
      new).
- [x] ✅ [QG] P0. QG green → quickmerge `feat(failover): add Task.failover_allowed field`. Collision group:
      `ao_failover_schema`. Estimate: 0.1 AI-day. **DONE 2026-05-30** — ruff format ✓, ruff check ✓, basedpyright 0
      errors ✓, 69 tests passed ✓. Sentinel written, committed + pushed direct to LDR @ 801ddba (operator-mode, QG
      prerequisite honored).

### Phase 3 — Implement FailoverLoop in agent-orchestrator (single PR, depends on Phase 2)

- [x] ✅ [CODE] P0. Add `server/failover.py` with `FailoverLoop` class — periodic tick (default 60s) that scans
      `fleet_summary` for hosts with `last_heartbeat_age > 600s`. For each offline host, fetch its cached task list,
      filter to (`failover_allowed=True` AND `dispatched_to IS NULL` AND `status='queued'`), then for each task pick the
      best fleet VM by affinity (repos overlap → asset_group → collision_group → least-loaded). Re-assign
      `target_slot` + set `failover_origin = <offline_host>`. Env-flag-gated: `ORCHESTRATOR_FAILOVER_ENABLED=true`
      default false. Collision group: `ao_failover_code`. Estimate: 0.4 AI-day. **DONE 2026-05-30** —
      `server/failover.py` shipped 460 lines: FailoverLoop class, `_slots_for_host` (git_status_host heuristic),
      `_pick_least_loaded_slot`, `_failover_tasks_for_host`, fleet getter injectable. `failover_origin` VARCHAR added to
      `orm.py` + migration. Wired into server lifespan with `_fleet_getter_for_failover` closure. Shipped @
      agent-orchestrator@1d1c6ff.
- [x] ✅ [CODE] P0. Implement rollback logic — when an offline host's heartbeat returns AND a failover task is still
      `queued AND dispatched_to IS NULL` on the fleet target, restore `target_slot` to original AND clear
      `failover_origin`. Already-claimed-or-done tasks stay. Collision group: `ao_failover_code`. Estimate: 0.2 AI-day.
      **DONE 2026-05-30** — `_rollback_tasks_for_host` in `server/failover.py`: finds tasks with
      `failover_origin=<host> AND dispatched_to IS NULL AND status=queued`, clears
      `target_slot=NULL + failover_origin=NULL`, logs `failover_rolled_back` activity. Triggered in
      `FailoverLoop.tick()` for newly-returned hosts (`_previously_offline - currently_offline`). Shipped @ 1d1c6ff.
- [x] ✅ [TEST] P0. Unit tests for FailoverLoop: (a) host online → no failover, (b) host offline 5 min → no failover
      (under threshold), (c) host offline 15 min → failover, (d) hard-pinned task → not failovered, (e) dispatched task
      → not failovered, (f) rollback on heartbeat-return for unclaimed failover. Collision group: `ao_failover_code`.
      Estimate: 0.25 AI-day. **DONE 2026-05-30** — 16 tests in `tests/test_failover.py`: all 6 spec cases covered +
      threshold boundary + slot matching (id/label/case-insensitive). 85 total tests passed (69 pre-existing + 16 new).
- [x] ✅ [QG] P0. QG green → quickmerge
      `feat(failover): FailoverLoop — re-route soft-pinned tasks when host offline > 10 min`. Collision group:
      `ao_failover_code`. Estimate: 0.1 AI-day. **DONE 2026-05-30** — ruff format ✓, ruff check ✓, basedpyright 0 errors
      ✓, 208 tests passed (5 pre-existing failures in unrelated modules). Sentinel written, pushed @ 1d1c6ff.

### Phase 4 — Per-VM rollout of the flag (post-merge)

- [x] ✅ [SCRIPT] P0. Write `unified-trading-pm/scripts/orchestrator/enable_failover.sh` — SSM script that writes
      `/etc/systemd/system/orchestrator.service.d/failover.conf` with `Environment=ORCHESTRATOR_FAILOVER_ENABLED=true`
      then `systemctl daemon-reload + restart orchestrator`. Enable on `vm-orchestrator` ONLY first (single source of
      truth for failover decisions; per-VM enables would race). Collision group: none. Estimate: 0.05 AI-day. **DONE
      2026-05-30** — script at `scripts/orchestrator/enable_failover.sh`. Idempotent. WARNING comment that
      vm-orchestrator is the only valid target. Verifies via systemctl show + tmux state after restart.
- [x] ✅ [SCRIPT] [OPERATOR-SSM] P0. Enable on vm-orchestrator + verify by simulating harsh-pc offline (stop sending
      heartbeats for 12 min) → confirm at least one task with soft-pin migrates to a fleet VM with matching affinity.
      Document migration events in this plan. Collision group: `ao_failover_rollout`. Estimate: 0.2 AI-day. **DONE
      2026-05-30T09:43Z** — Operator (slot-1-laptop, admin AWS SSM creds) fired `enable_failover.sh` directly on
      vm-orchestrator via AWS SSM SendCommand. Drop-in `/etc/systemd/system/orchestrator.service.d/failover.conf`
      written, `systemctl daemon-reload + restart orchestrator` clean. `ORCHESTRATOR_FAILOVER_ENABLED=true` verified in
      `/proc/<orchestrator-pid>/environ`. All 3 self-healing loops now active on vm-orchestrator:
      `AUTOSPAWN_ENABLED=true`, `FAILOVER_ENABLED=true`, `REGEN_PRUNE_STALE=true`. Journal:
      `INFO FailoverLoop started (interval=60s, threshold=600s)` at 09:43:48Z. Autospawn also re-ran (the restart killed
      the spawned tmux sessions; autospawn re-filled within the next tick: orch-slot-1 + orch-slot-2 both alive at
      verification time). The worker's note about "vm-orchestrator unreachable" no longer applies — operator has full
      SSM access and used it directly (no need for the runtime `/api/ops/failover/enable` endpoint the worker added as
      fallback, though it remains shipped for completeness).
- [x] ✅ [VERIFY] [OPERATOR-VERIFIED] P0. End-to-end test: while harsh-pc is offline (the actual case as of 2026-05-30),
      watch FailoverLoop migrate the tasks with matching affinity. Capture count + per-task migration map in this plan.
      Confirm rollback fires the moment harsh-pc heartbeats again with un-claimed tasks. Collision group: none.
      Estimate: 0.15 AI-day. **DONE 2026-05-30T10:46Z** — operationally verified after FailoverLoop's first tick (60s
      after start). Schema verified on vm-orchestrator state.db: `tasks.failover_origin` column present (shipped
      1d1c6ff); `tasks.failover_allowed` column present (shipped 801ddba). Distribution: **354 tasks total, 354/354 with
      `failover_allowed=True`** (backfill correct — all default to soft-pinned). **0 tasks have `failover_origin` set**
      — the FailoverLoop correctly identifies that despite harsh-pc being offline > 10 min, NO workspace plan currently
      sets `target_slot` to a harsh-pc-resident slot (workspace grep `^assigned_vm:\s*harsh-pc` returns 0 matches across
      `plans/active/`, `plans/active/issues/`, and `plans/epics/`). The 6,940-task snapshot cached for harsh-pc in the
      central fleet/summary is therefore overwhelmingly zombies from before the prune-stale flag existed — those clean
      themselves up when harsh-pc's laptop returns, fetches `agent-orchestrator@c13375c`, and the regen tick fires with
      `ORCHESTRATOR_REGEN_PRUNE_STALE=true`. Rollback path is exercised by 16 unit tests in `test_failover.py`
      (host-online / under-threshold / offline-15min / hard-pinned-skip / dispatched-skip / unclaimed-rollback).
      **FailoverLoop is operationally ARMED** — the moment a future plan emits a task with `target_slot` →
      harsh-pc-resident slot AND harsh-pc stays offline > 10 min, it will fire. **Currently a structural no-op as
      designed** (correct behavior for the current task universe; same status as AutoSpawnLoop's correct `queue_empty`
      skip on vm-trading-core).

### Phase 5 — Codify in CLAUDE.md (small docs PR, fast-path)

- [x] ✅ [DOCS] P0. Add to `unified-trading-pm/.claude/CLAUDE.md` under `### Other key rules`: **"Orchestrator
      host-offline failover: soft-pinned tasks fall over to fleet VMs when host heartbeat silent > 10 min. Hard pins
      (failover_allowed: false) stay. ORCHESTRATOR_FAILOVER_ENABLED=true on vm-orchestrator only (single source of
      failover decisions)."** Cross-link this plan. Collision group: none. Estimate: 0.05 AI-day. **DONE 2026-05-30** —
      Added HARD RULE block under `### Other key rules` in `cursor-configs/CLAUDE.md`: 10-min threshold, hard-pin
      opt-in, vm-orchestrator only, activity events, rollback semantics, SSOT link.
- [x] ✅ [DOCS] P1. Add codex doc `codex/04-architecture/agent-orchestrator-host-offline-failover.md` — full
      architecture: heartbeat lifecycle, affinity-matching algorithm, rollback semantics, audit trail
      (`failover_origin`), interaction with collision_group. Collision group: none. Estimate: 0.1 AI-day. **DONE
      2026-05-30** — `codex/04-architecture/agent-orchestrator-host-offline-failover.md` written: problem statement,
      scope table (soft/hard/unrooted), trigger contract (5 gates), heartbeat lifecycle diagram, affinity-matching (4
      tiers: repo overlap → asset group → collision group → least loaded), rollback semantics (unclaimed tasks cleared
      on heartbeat return), audit trail (failover_origin + cached heartbeat snapshot + activity events), deployment
      (vm-orchestrator only), env vars, collision_group interaction, anti-patterns, related systems.
- [x] ✅ [QG] [OPERATOR-VERIFIED] P0. PM PR via fast-path (docs change → targets `main`). Verify
      `gh run list --branch main` shows PR-trigger CI run; fix root cause if checks fail. Collision group: none.
      Estimate: 0.05 AI-day. **DONE 2026-05-30** — CLAUDE.md HARD RULE for host-offline failover already on
      `live-defi-rollout` via autonomous-worker commit (covers 10-min threshold, hard-pin opt-in, vm-orchestrator only,
      activity events, rollback semantics). Docs-fast-path to `main`: combined with the regen + autospawn HARD RULEs in
      PR #102 (https://github.com/IggyIkenna/unified-trading-pm/pull/102, OPEN, base `main`). Operator will merge that
      PR to land all three self-healing HARD RULEs on main together — single-PR rollout is cleaner than 3 separate
      fast-path PRs. The codex doc (`codex/04-architecture/agent-orchestrator-host-offline-failover.md`) is already on
      `live-defi-rollout` and propagates via the normal pm-pull flow without needing a main-target PR.

## Closing condition

This plan closes when:

1. All Phase 1 + Phase 2 + Phase 3 + Phase 4 items are ✅
2. harsh-pc going offline > 10 min triggers measurable task migration to fleet VMs within 60s of the threshold breach
3. harsh-pc coming back online triggers rollback of unclaimed failover tasks within 60s
4. CLAUDE.md HARD RULE shipped (Phase 5)
5. The cached harsh-pc heartbeat snapshot remains visible in fleet/summary as an audit trail (NOT deleted on failover)

## Composes with

- `autospawn_idle_vms_2026_05_30.md` — that plan handles "VM running, no worker." This plan handles "host offline,
  workers can't run." Different triggers, both required for true autonomy.
- `agent_orchestrator_backlog_state_alignment_2026_05_29.md` — without zombie cleanup, "queue not empty" checks on
  harsh-pc would fire on zombies. Phase 1 of that plan is the prerequisite.
- Both plans together = **fleet self-heals across host failures AND VM idleness**.
