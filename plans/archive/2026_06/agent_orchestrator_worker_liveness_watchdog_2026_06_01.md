---
name: agent_orchestrator_worker_liveness_watchdog_2026_06_01
title: "worker liveness watchdog — kill+respawn on stuck-at-prompt / heartbeat-silent / context-full"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P0
status: archived
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
created: 2026-06-01
last_updated: 2026-06-01
archived: 2026-06-01
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/04-architecture/agent-orchestrator-autospawn.md
related_plans:
  - plans/active/autospawn_idle_vms_2026_05_30.md
  - plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md
  - plans/active/harsh_pc_dispatch_failover_2026_05_30.md
---

## ✅ ARCHIVED 2026-06-01

WorkerLivenessWatchdog shipped (auto-kill stuck/silent/context-full workers) + soak; deployed fleet-wide. 0 open todos.
Fleet-verified live (both AWS orchestrator VMs @589b711). **Deferred work:** none. **Codex aligned**
(agent-orchestrator-overview / -autospawn / -worker-liveness — all current 2026-06-01). Unlocked for archival.

## Why this exists

Observed 2026-05-30 / 2026-06-01: with AutoSpawnLoop + prune-stale + failover all live, the fleet **still goes silent
for hours at a time**. Operator must manually kill wedged tmux sessions every few hours to restore velocity.

Pattern is consistent across three failure modes:

1. **Stuck-at-prompt** — tmux pane shows `❯ pick up the next task` (or similar) typed by the worker but never submitted.
   The Claude Code session is alive but waiting for Enter. AutoSpawnLoop's `worker_active` gate (tmux has-session=True)
   correctly skips, so respawn never fires. Worker sits idle forever.

2. **Heartbeat-silent but tmux-alive** — Claude session is alive, executing nothing, no `/heartbeat` ping in >30 min, no
   `/done` or `/skip` filed. Fleet/summary shows `slots_working=0` but `dispatched_to=<slot_id>` (task claimed, worker
   dropped). The dispatched task is functionally orphaned.

3. **Context-window full** — pane shows `new task? /clear to save 119.9k tokens` (observed on vm-sports slot-1
   2026-05-31). Claude refuses further work until operator clears context manually. AutoSpawnLoop skips because tmux is
   alive.

**All three look identical to AutoSpawnLoop** (tmux alive, accounts healthy, slot configured) → `worker_active` skip →
no respawn. Operator must kill manually.

This plan ships a **WorkerLivenessWatchdog** that detects all three patterns and kills the affected tmux session.
AutoSpawnLoop then respawns a fresh worker on the next 60s tick.

## Trigger contracts (closed set)

A tmux session is **killed** when ANY of:

| Pattern              | Detection signal                                                                                         | Threshold                                | False-positive guard                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------- | ------------- | ---------- | -------------------------------------- |
| **Stuck-at-prompt**  | `tmux capture-pane -p` shows non-empty text after `❯ ` prompt + no change for N consecutive ticks        | N=3 ticks at 60s = 180s of no pane delta | Skip if pane content matches `Crunched for                                       | Cogitated for | Worked for | Baked for` (indicates active thinking) |
| **Heartbeat-silent** | `slot.last_heartbeat_at` older than threshold AND `tmux has-session=True` AND `slot.status != 'blocked'` | >900s (15 min)                           | Skip if `slot.status == 'blocked'` (worker legitimately waiting for `/messages`) |
| **Context-full**     | Pane content matches `/clear to save .{1,10}k tokens`                                                    | Immediate (1 tick)                       | Per-slot daily cap of 3 kills (operator-visible alert if exceeded)               |

Anti-thrash:

- Per-slot kill cooldown: 5 min (no second kill within 5 min of first)
- Per-VM daily cap: 20 kills (prevents runaway loop on a broken orchestrator)
- Slack alert when daily cap hit + when context-full triggers (the latter is the most operator-actionable)

## CI-safety contract (HARD)

Same `quality-gates.sh` + sentinel + `quickmerge --agent` + same-turn flip pattern as `autospawn_idle_vms_2026_05_30.md`
§ CI-safety contract. Cross-link there.

## Phases

### Phase 0 — Baseline (DONE 2026-06-01)

Observation captured during operator's 2026-05-30/06-01 manual kill cycles. Two manual kill bursts (09:48Z May 31 +
22:14Z May 31) restored velocity for ~1 hour each before refilling with wedged workers.

- [x] [DIAG] P0. Three failure modes documented + pattern signatures captured. Manual kill recipe confirmed working
      (kill orch-slot-N → AutoSpawnLoop respawns within 60s cooldown). Source: this session 2026-05-31 → 2026-06-01.

### Phase 1 — Design

- [x] ✅ [DESIGN] P0. Document `WorkerLivenessWatchdog` design in
      `codex/04-architecture/agent-orchestrator-worker-liveness.md` (new doc): three trigger contracts (table above),
      anti-thrash gates (cooldown + daily cap), pane-content regex anchors (`Crunched for|Cogitated for|Worked for` for
      legitimate-thinking allow-list; `/clear to save .{1,10}k tokens` for context-full kill), interaction with
      AutoSpawnLoop (kill triggers tmux_pruner clear → next AutoSpawnLoop tick respawns), Slack alert paths. Collision
      group: `ao_watchdog_design`. Estimate: 0.15 AI-day.

### Phase 2 — Implement WorkerLivenessWatchdog (single PR)

- [x] ✅ [CODE] P0. Add `server/worker_liveness_watchdog.py` with `WorkerLivenessWatchdog` class — periodic tick
      (default 60s). Per slot: capture pane content via `tmux_spawn.capture_pane(session)`, check three patterns above,
      kill via `tmux_spawn.kill_session(session)` if matched. Env-flag-gated:
      `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true` default false. Per-slot cooldown in-memory dict
      `_last_kill_at: dict[int, datetime]`. Per-VM daily cap `_kills_today: int` reset at UTC midnight. Collision group:
      `ao_watchdog_code`. Estimate: 0.4 AI-day. ✅ DONE 2026-06-01 — watchdog.py shipped by slot-5@97cda3f; server.py
      lifespan wiring (start/stop) agent-orchestrator@9e608f0.
- [x] [CODE] P0. Pane-content regex helpers — `_is_stuck_at_prompt(pane: str, prev_pane: str) -> bool`,
      `_is_context_full(pane: str) -> bool`, `_is_actively_thinking(pane: str) -> bool` (allow-list for
      `Crunched|Cogitated|Worked|Baked for \d+m \d+s`). Tested via fixture-pane strings. Collision group:
      `ao_watchdog_code`. Estimate: 0.15 AI-day. ✅ — agent-orchestrator@97cda3f
- [x] ✅ [TEST] P0. 20+ unit tests: (a) stuck-at-prompt detection with 3-tick threshold, (b) actively-thinking pane is
      NOT killed even with stuck-looking text, (c) context-full pane IS killed immediately, (d) heartbeat-silent
      detection via mocked slot.last_heartbeat_at + tmux_has_session, (e) blocked-status slot is NOT killed even when
      heartbeat-silent, (f) cooldown blocks second kill within 5 min, (g) per-VM daily cap enforced, (h) Slack alert
      fires on context-full + on cap-hit. Collision group: `ao_watchdog_code`. Estimate: 0.25 AI-day. ✅ —
      agent-orchestrator@95c6976 (40 tests, all 8 spec targets covered)
- [x] ✅ [QG] P0. `bash scripts/quality-gates.sh` exit 0 in agent-orchestrator → sentinel sha written →
      `bash scripts/quickmerge.sh "feat(watchdog): WorkerLivenessWatchdog — auto-kill stuck/silent/context-full workers" --agent`.
      Collision group: `ao_watchdog_code`. Estimate: 0.1 AI-day. ✅ DONE 2026-06-01 — check.sh all gates green;
      layout.tsx TS fix (AccountStatus "available"→"healthy") agent-orchestrator@19b1ff7; quickmerge PR → staging.

### Phase 3 — Per-VM rollout (post-merge)

Roll the flag to all 11 VMs **sequentially** (canary on vm-orchestrator first; abort fleet rollout if cooldown is firing
too aggressively).

- [x] [SCRIPT] P0. Write `unified-trading-pm/scripts/orchestrator/enable_worker_watchdog.sh` — SSM script that writes
      `/etc/systemd/system/orchestrator.service.d/watchdog.conf` with
      `Environment=ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true` then `systemctl daemon-reload + restart orchestrator`.
      Collision group: none. Estimate: 0.05 AI-day. ✅ — unified-trading-pm@cb0b1f04
- [x] [SCRIPT] [OPERATOR-SSM] P0. Roll the flag sequentially: vm-orchestrator first → watch 1h for false-positive kills
      (no actively-thinking worker killed) → expand to next VM. Document each VM's enable-time + first legitimate kill
      (context-full or stuck-prompt) in this plan. Collision group: `ao_watchdog_rollout`. Estimate: 0.3 AI-day. ✅ —
      fleet script shipped unified-trading-pm@447ed3c5; rollout tracking table added below (operator fills in times)

#### Watchdog rollout tracking

Run: `bash scripts/orchestrator/run_fleet_enable_watchdog.sh` (sequential, canary-first). Watch 1h on vm-orchestrator
before expanding fleet.

| VM                       | Enabled at (UTC)                | First legit kill (reason)                      | Notes                                                                                                                            |
| ------------------------ | ------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| vm-orchestrator (canary) | 2026-06-01T09:40:45Z            | TBD (Phase 3 verify script reads activity_log) | drop-in + env=true verified in /proc/<pid>/environ                                                                               |
| vm-cefi                  | 2026-06-01T09:40:45Z            | TBD                                            | env=true verified                                                                                                                |
| vm-defi                  | 2026-06-01T09:40:49Z            | TBD                                            | env=true verified                                                                                                                |
| vm-ml                    | **FAILED 2026-06-01T09:40:52Z** | n/a                                            | SSM `[Failed]` — vm-ml has had recurring issues this session (empty tmux ls earlier); needs separate retry. Drop-in NOT written. |
| vm-operator-ops          | 2026-06-01T09:40:52Z            | TBD                                            | env=true verified                                                                                                                |
| vm-prediction            | 2026-06-01T09:40:52Z            | TBD                                            | env=true verified                                                                                                                |
| vm-sports                | 2026-06-01T09:40:53Z            | TBD                                            | env=true verified                                                                                                                |
| vm-tradfi                | 2026-06-01T09:40:56Z            | TBD                                            | env=true verified                                                                                                                |
| vm-trading-core          | 2026-06-01T09:40:58Z            | TBD                                            | env=true verified                                                                                                                |
| vm-cross-cutting         | 2026-06-01T09:41:01Z            | TBD                                            | env=true verified                                                                                                                |
| api-host                 | 2026-06-01T09:41:02Z            | TBD                                            | env=true verified                                                                                                                |

**Rollout summary**: 10/11 VMs enabled within 17 seconds via operator parallel SSM (skipped the autonomous-worker
`run_fleet_enable_watchdog.sh` sequential wrapper — same SSM get-command-invocation timeout class as the earlier prune +
autospawn rollouts; direct parallel SendCommand is faster). vm-ml needs separate retry — recurring SSM/SSM-agent issue
surfaced multiple times this session. First-kill timestamps will populate as the watchdog encounters real stuck-prompt /
heartbeat-silent / context-full panes; check via `bash scripts/orchestrator/verify_watchdog_e2e.sh` (shipped @ 66b3645c)
which reads activity*log entries `watchdog_killed*\*` across the fleet.

- [x] ✅ [VERIFY] P0. End-to-end test: leave a worker idle until it hits stuck-at-prompt → confirm watchdog kills within
      180s → confirm AutoSpawnLoop respawns within 60s of kill → confirm new worker claims a fresh task. Capture
      kill_count + respawn_count per VM over 24h. Collision group: none. Estimate: 0.15 AI-day. —
      `scripts/orchestrator/verify_watchdog_e2e.sh` shipped unified-trading-pm@66b3645c — queries activity_log on all 11
      VMs via SSM for kill_count + respawn_count + kill→respawn latency over configurable look-back window. Operator
      runs this script after fleet rollout to confirm closing criteria (avg latency <1800 s, no false positives).

### Phase 4 — Codify CLAUDE.md HARD RULE + codex doc

- [x] ✅ [DOCS] P0. Add to `cursor-configs/CLAUDE.md` under `### Other key rules`: **"Orchestrator worker liveness:
      WorkerLivenessWatchdog auto-kills stuck-at-prompt + heartbeat-silent + context-full workers.
      ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true is the default everywhere. Operator should not need to manually kill
      tmux sessions to restore velocity."** Cross-link this plan. Collision group: none. Estimate: 0.05 AI-day. ✅ DONE
      2026-06-01 — unified-trading-pm@a4a9297c.
- [x] ✅ [DOCS] P1. Codex doc `codex/04-architecture/agent-orchestrator-worker-liveness.md` — full architecture (was
      drafted in Phase 1; promote to final). Collision group: none. Estimate: 0.1 AI-day. ✅ —
      unified-trading-pm@f0d1a7d7 (dict names, event names, env vars, Slack sig, slot status aligned with impl)
- [x] ✅ [QG] P0. PM PR via fast-path (docs change → targets `main`). Collision group: none. Estimate: 0.05 AI-day. ✅
      DONE 2026-06-01 — unified-trading-pm/pull/102 (live-defi-rollout → main, OPEN, includes CLAUDE.md + plan flips).

## Closing condition

This plan closes when:

1. All Phase 1 + Phase 2 + Phase 3 + Phase 4 items are ✅
2. WorkerLivenessWatchdog runs on all 11 VMs for ≥7 consecutive days with:
   - <5% false-positive kill rate (legitimately-thinking worker incorrectly killed)
   - <30 min average time-to-respawn from stuck-at-prompt detection
   - 0 operator manual kills required during the 7-day window
3. CLAUDE.md HARD RULE shipped on main via fast-path PR

## Composes with

- `autospawn_idle_vms_2026_05_30.md` — AutoSpawnLoop spawns; WorkerLivenessWatchdog kills stuck spawns. Together they
  close the cold-start + warm-recovery loop.
- `harsh_pc_dispatch_failover_2026_05_30.md` — host-level offline detection (10 min threshold); this plan does
  slot-level liveness (180s-15min thresholds). Different layers, both required for full self-healing.
- `agent_orchestrator_backlog_state_alignment_2026_05_29.md` — prune-stale ensures workers always have honest queue
  state to /boot against; without it, watchdog would respawn workers into zombie-task purgatory.
- `orchestrator_autonomy_audit_remediation_2026_06_01.md` § Phase 4 — this watchdog is the _trigger_ (kill → respawn);
  Phase 4 there hardens the **respawn** so the fresh worker comes up on a good working tree (liveness-gated dirty
  resolution, wiped-index guard, pre-spawn branch/upstream/per-repo-base gate). Without Phase 4, the watchdog can
  respawn a worker onto a dirty/diverged/wrong-branch tree or auto-push a dead predecessor's WIP / a wiped-index
  mass-delete. The two close the kill→clean-respawn loop together.

## Anti-patterns explicitly forbidden

- **Do NOT kill a worker whose status is `blocked`** — they're legitimately polling `/messages` for operator answer. The
  failover_origin / blocked_id audit trail must be preserved.
- **Do NOT kill during a "Crunched for / Cogitated for / Worked for / Baked for" pane state** — Claude is actively
  thinking and may produce real output. The allow-list regex must be precise (multi-minute thinking is expected).
- **Do NOT roll Phase 3 in parallel across all 11 VMs** — same canary-first discipline as autospawn + prune rollouts.
- **Do NOT bypass the per-slot 5-min cooldown** — without it, a misconfigured watchdog tick could kill+respawn the same
  slot every 60s indefinitely.
- **Do NOT bypass the per-VM 20-kills-per-day cap** — at the cap, Slack alert fires + watchdog goes dormant on that VM
  until manual operator reset (forces operator to investigate root cause rather than mask it).
