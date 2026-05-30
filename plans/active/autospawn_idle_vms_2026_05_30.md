---
name: autospawn_idle_vms_2026_05_30
title: "autospawn idle VMs — orchestrator wakes a worker when (queue > 0 AND no workers AND account headroom > 50%)"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P0
status: active
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
created: 2026-05-30
last_updated: 2026-05-30
locked_by: live-defi-rollout
locked_since: 2026-05-30
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md
related_plans:
  - plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md
  - plans/active/harsh_pc_dispatch_failover_2026_05_30.md
  - plans/active/api_host_chronic_impairment_2026_05_29.md
---

## Why this exists

Operator sweep on 2026-05-29/30 discovered the agent-orchestrator fleet was operating with **only 1 active worker
fleet-wide** (api-host slot 1) for several hours. 10 epic VMs were running the orchestrator process with healthy
accounts but zero tmux/Claude sessions. Queued tasks just sat. Plan-derived items in `agent_orchestrator_backlog_state_alignment_2026_05_29.md` Phase 2-5 were targeted at `vm-orchestrator` (the only VM
that could service them) but never dispatched, because no worker existed there.

Operator had to **manually spawn workers** via `/api/slots/<id>/spawn` SSM-fanout on 10 VMs:

```
vm-orchestrator slot 1 → SPAWN_OK (sub-b-iggy2london)
vm-defi          slot 1 → SPAWN_OK (sub-b-iggy2london)
vm-cefi          slot 1 → SPAWN_OK (sub-c-ikenna-odum)
vm-tradfi        slot 1 → SPAWN_OK (harsh-primary)
vm-sports        slot 1 → SPAWN_OK (sub-b-iggy2london)
vm-prediction    slot 1 → SPAWN_OK (sub-c-ikenna-odum)
vm-ml            slot 1 → SPAWN_OK (harsh-primary)
vm-trading-core  slot 1 → SPAWN_OK (sub-b-iggy2london)
vm-operator-ops  slot 1 → SPAWN_OK (sub-c-ikenna-odum)
vm-cross-cutting slot 1 → SPAWN_OK (harsh-primary)
```

Within 5 minutes of spawn, vm-orchestrator's worker shipped 7 tasks. **The work was there. The workers weren't.**

This plan makes spawn **automatic** so the fleet self-heals.

## The trigger contract

A worker is **auto-spawned** on a VM when ALL of:

1. **Queue not empty**: at least one task with `status=queued AND dispatched_to IS NULL` in this VM's `state.db`.
2. **No active worker**: `tmux ls` shows no `orch-slot-N` session, AND `/api/slots/N` shows `state != working`.
3. **Account headroom**: at least one account has `five_hour_pct < 50` AND `weekly_pct < 80` AND `status=healthy` AND
   `rate_limited_until IS NULL`.
4. **Slot configured**: row exists in `slots` table with `slot_id`, `worktree`, `branch`, `operator`.
5. **Not in cooldown**: last autospawn attempt on this VM was > 5 min ago (prevents flap on degenerate states).

When ALL match, the orchestrator's `AutoSpawnLoop` calls its own `/api/slots/<id>/spawn` endpoint, using the
canonical prompt from `/api/spawn/preview`. Account pick respects rotation (least-used 5h window first).

## Anti-patterns explicitly forbidden

- **Do NOT spawn while a worker is actively dispatched** — the dispatcher might have just claimed; the spawn race is
  worse than a 5-min wait.
- **Do NOT spawn when accounts at ≥80% capacity** — burning a rate-limit on a fleet-wide rollout is worse than
  leaving a VM idle for the rest of the 5h window.
- **Do NOT spawn more than 1 worker per slot per cooldown window** — operator may have explicit reasons for an idle
  slot (paused, maintenance, debug).
- **Do NOT bypass `/api/spawn/preview`** — the boot prompt template is the source of truth for worker contract; baking
  another version in the autospawner = drift bug.

## CI-safety contract (HARD)

Every code-change phase MUST follow the same `quality-gates.sh` + sentinel + `quickmerge --agent` + same-turn flip
pattern as `agent_orchestrator_backlog_state_alignment_2026_05_29.md` § CI-safety contract. Cross-link there to avoid
duplication.

## Phases

### Phase 0 — Baseline (DONE 2026-05-30)

Operator sweep captured. Worker spawn done manually via SSM on 10 VMs.

- [x] [DIAG] P0. Pre-existing fleet state captured — 1 active worker fleet-wide for several hours; 10 idle VMs with queued tasks; plan tasks stuck. Manual spawn on 10 VMs validated the spawn API works correctly. Source: this session 2026-05-30 02:13-02:20 UTC.
- [x] [SCRIPT] [OPERATOR-SSM] P0. Emergency manual rollout — 10 workers spawned via parallel `/api/slots/1/spawn` calls (each on its local orchestrator). All 10 returned `SPAWN_OK` with `tmux_session: orch-slot-1`. Within 5 minutes vm-orchestrator's worker shipped 7 tasks. **Done 2026-05-30 02:20 UTC.** This is the workaround; Phase 1+2 below make it autonomous.

### Phase 1 — Design the AutoSpawnLoop

- [ ] [DESIGN] P0. Document the `AutoSpawnLoop` design in `codex/04-architecture/agent-orchestrator-overview.md` § "Auto-spawn lifecycle": trigger conditions (the 5-item contract above), cooldown window (5 min default), account-pick rotation logic (least-used five_hour_pct first, weekly_pct tiebreaker), failure modes (preview fetch failed, spawn HTTP 4xx, tmux create failed), what to log on each path. Collision group: `ao_autospawn_design`. Estimate: 0.15 AI-day.
- [ ] [DESIGN] P0. Identify accountable PR scope — confirm that `AutoSpawnLoop` lives ENTIRELY in `agent-orchestrator/server/` (no PM changes needed) and does NOT touch `regen_backlog_from_plan.py` (different surface). Collision group: `ao_autospawn_design`. Estimate: 0.05 AI-day.

### Phase 2 — Implement AutoSpawnLoop in agent-orchestrator (single PR)

- [ ] [CODE] P0. Add `server/autospawn.py` with `AutoSpawnLoop` class — periodic tick (default 60s) that scans all slots, checks the 5-item trigger contract per slot, calls local `/api/slots/<id>/spawn` when all match. Idempotent (re-tick on already-spawned slot is a no-op). Env-flag-gated: `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` default false. Cooldown tracked in-memory (`Dict[slot_id, last_attempt_ts]`). Account pick uses the existing rotation logic from `_pick_next_account` in `server.py` — same source of truth, no drift. Collision group: `ao_autospawn_code`. Estimate: 0.4 AI-day.
- [ ] [TEST] P0. Unit tests for AutoSpawnLoop trigger logic: (a) queue empty → no spawn, (b) worker active → no spawn, (c) accounts maxed → no spawn, (d) cooldown active → no spawn, (e) all conditions met → spawn called once. Plus integration test that mocks the `/api/slots/<id>/spawn` HTTP call. Collision group: `ao_autospawn_code`. Estimate: 0.2 AI-day.
- [ ] [TEST] P0. Add alert when AutoSpawnLoop fires 3 consecutive times on a VM but the worker never claims a task within 10 min — this is the "spawn succeeds but worker is wedged" failure mode. Alert path: emit `ACTIVITY_LOG_ENTRY` with kind=`autospawn_loop_no_progress` + Slack notification via the existing `notify_account_rotated_to_slack` pattern. Collision group: `ao_autospawn_code`. Estimate: 0.15 AI-day.
- [ ] [QG] P0. `bash scripts/quality-gates.sh` exit 0 in agent-orchestrator → sentinel sha written → `bash scripts/quickmerge.sh "feat(autospawn): AutoSpawnLoop — wake worker on (queue > 0 AND no worker AND headroom > 50%)" --agent`. PR merges through staging to LDR. Collision group: `ao_autospawn_code`. Estimate: 0.1 AI-day.

### Phase 3 — Per-VM rollout of the flag (post-merge)

After Phase 2 PR lands on LDR, `pm-pull.timer` propagates the new agent-orchestrator HEAD to all 11 VMs. Then enable
the flag via systemd drop-in + restart orchestrator. **Sequential per-VM** so a bug doesn't melt the fleet.

- [ ] [SCRIPT] P0. Write `unified-trading-pm/scripts/orchestrator/enable_autospawn.sh` — SSM script that writes `/etc/systemd/system/orchestrator.service.d/autospawn.conf` with `Environment=ORCHESTRATOR_AUTOSPAWN_ENABLED=true` then `systemctl daemon-reload + restart orchestrator`. Collision group: none. Estimate: 0.05 AI-day.
- [ ] [SCRIPT] P0. Roll the flag to all 11 VMs **sequentially**: vm-orchestrator first → wait 10 min → verify autospawn fires on a slot you manually kill → expand to next VM. Document each VM's enable-time + first-autospawn-time in this plan. Collision group: `ao_autospawn_rollout`. Estimate: 0.3 AI-day.
- [ ] [VERIFY] P0. Kill a worker on a Phase-3-enabled VM (`tmux kill-session -t orch-slot-N`) → confirm autospawn re-spawns within 1 minute. Confirm Slack alert fires when 3 consecutive autospawns produce no task claim. Collision group: none. Estimate: 0.1 AI-day.

### Phase 4 — Codify in CLAUDE.md (small docs PR, fast-path)

- [ ] [DOCS] P0. Add to `unified-trading-pm/.claude/CLAUDE.md` under `### Other key rules`: **"Orchestrator autospawn: workers self-heal. ORCHESTRATOR_AUTOSPAWN_ENABLED=true is the default everywhere. Manual SSM spawn is only needed for cold-start of a new VM."** Cross-link this plan. Collision group: none. Estimate: 0.05 AI-day.
- [ ] [DOCS] P1. Add codex doc `codex/04-architecture/agent-orchestrator-autospawn.md` — the full architecture: trigger contract, cooldown, account rotation, failure modes, alerting, recovery if autospawn flaps. Collision group: none. Estimate: 0.1 AI-day.
- [ ] [QG] P0. PM PR via fast-path (docs change → targets `main`). Verify `gh run list --branch main` shows PR-trigger CI run; fix root cause if checks fail. Collision group: none. Estimate: 0.05 AI-day.

## Closing condition

This plan closes when:

1. All Phase 1 + Phase 2 + Phase 3 items are ✅
2. Phase 4 docs land
3. `tmux kill-session -t orch-slot-1` on any VM → re-spawn within 1 minute, with Slack alert on flapping
4. No manual SSM spawn required for 7 consecutive days; if any VM goes silent for > 15 min, the alert chain fires before
   operator notices

## Composes with

- `harsh_pc_dispatch_failover_2026_05_30.md` — that plan handles the case where a HOST goes offline (heartbeat silent
  > 10 min). This plan handles the case where a VM is RUNNING but its slot has no worker. Different triggers, both
  required for true autonomy.
- `agent_orchestrator_backlog_state_alignment_2026_05_29.md` — without the zombie cleanup from that plan, autospawn's
  "queue not empty" trigger would fire constantly on zombie rows. Phase 1 of that plan is the prerequisite.
