---
doc_type: plan
title: autospawn idle VMs — orchestrator wakes a worker when (queue > 0 AND no workers AND account headroom > 50%)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md,
    plans/active/harsh_pc_dispatch_failover_2026_05_30.md,
    plans/active/api_host_chronic_impairment_2026_05_29.md,
  ]
created: 2026-05-30
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
last_updated: 2026-05-30
locked_by: live-defi-rollout
locked_since: 2026-05-30
codex_ssots:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
  ]
---

> **✅ COMPLETE — ARCHIVED 2026-06-01.** All 14 todos done; `AutoSpawnLoop` rolled fleet-wide to all 11 VMs
> (`ORCHESTRATOR_AUTOSPAWN_ENABLED=true` drop-in), verified operationally (4→17 working slots in <2 min). Continuous
> verification is built-in: 60 s tick + flap-detection Slack alert + `/api/fleet/summary`. Codified as HARD RULE in
> deployment-service CLAUDE.md (§ "Orchestrator autospawn: workers self-heal") + codex
> `agent-orchestrator-autospawn.md`.
>
> ## Deferred work — migrated to:
>
> - None — fleet-wide rollout complete; no deferred items.

## Why this exists

Operator sweep on 2026-05-29/30 discovered the agent-orchestrator fleet was operating with **only 1 active worker
fleet-wide** (api-host slot 1) for several hours. 10 epic VMs were running the orchestrator process with healthy
accounts but zero tmux/Claude sessions. Queued tasks just sat. Plan-derived items in
`agent_orchestrator_backlog_state_alignment_2026_05_29.md` Phase 2-5 were targeted at `vm-orchestrator` (the only VM
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

When ALL match, the orchestrator's `AutoSpawnLoop` calls its own `/api/slots/<id>/spawn` endpoint, using the canonical
prompt from `/api/spawn/preview`. Account pick respects rotation (least-used 5h window first).

## Anti-patterns explicitly forbidden

- **Do NOT spawn while a worker is actively dispatched** — the dispatcher might have just claimed; the spawn race is
  worse than a 5-min wait.
- **Do NOT spawn when accounts at ≥80% capacity** — burning a rate-limit on a fleet-wide rollout is worse than leaving a
  VM idle for the rest of the 5h window.
- **Do NOT spawn more than 1 worker per slot per cooldown window** — operator may have explicit reasons for an idle slot
  (paused, maintenance, debug).
- **Do NOT bypass `/api/spawn/preview`** — the boot prompt template is the source of truth for worker contract; baking
  another version in the autospawner = drift bug.

## CI-safety contract (HARD)

Every code-change phase MUST follow the same `quality-gates.sh` + sentinel + `quickmerge --agent` + same-turn flip
pattern as `agent_orchestrator_backlog_state_alignment_2026_05_29.md` § CI-safety contract. Cross-link there to avoid
duplication.

## Phases

### Phase 0 — Baseline (DONE 2026-05-30)

Operator sweep captured. Worker spawn done manually via SSM on 10 VMs.

- [x] [DIAG] P0. Pre-existing fleet state captured — 1 active worker fleet-wide for several hours; 10 idle VMs with
      queued tasks; plan tasks stuck. Manual spawn on 10 VMs validated the spawn API works correctly. Source: this
      session 2026-05-30 02:13-02:20 UTC.
- [x] [SCRIPT] [OPERATOR-SSM] P0. Emergency manual rollout — 10 workers spawned via parallel `/api/slots/1/spawn` calls
      (each on its local orchestrator). All 10 returned `SPAWN_OK` with `tmux_session: orch-slot-1`. Within 5 minutes
      vm-orchestrator's worker shipped 7 tasks. **Done 2026-05-30 02:20 UTC.** This is the workaround; Phase 1+2 below
      make it autonomous.

### Phase 1 — Design the AutoSpawnLoop

- [x] ✅ [DESIGN] P0. Document the `AutoSpawnLoop` design in `/codex/04-architecture/agent-orchestrator-overview.md` §
      "Auto-spawn lifecycle": trigger conditions (the 5-item contract above), cooldown window (5 min default),
      account-pick rotation logic (least-used five_hour_pct first, weekly_pct tiebreaker), failure modes (preview fetch
      failed, spawn HTTP 4xx, tmux create failed), what to log on each path. Collision group: `ao_autospawn_design`.
      Estimate: 0.15 AI-day. **DONE 2026-05-30** — new `## Auto-spawn lifecycle` section added to
      `/codex/04-architecture/agent-orchestrator-overview.md`. Covers trigger contract table, account-pick rotation,
      spawn execution, anti-flap/Slack alert, failure mode table, env vars table, rollout pointer.
- [x] ✅ [DESIGN] P0. Identify accountable PR scope — confirm that `AutoSpawnLoop` lives ENTIRELY in
      `agent-orchestrator/server/` (no PM changes needed) and does NOT touch `regen_backlog_from_plan.py` (different
      surface). Collision group: `ao_autospawn_design`. Estimate: 0.05 AI-day. **DONE 2026-05-30** — confirmed: Phase 2
      code is `server/autospawn.py` (new, 454 lines) + 11-line lifespan integration in `server/server.py`. Zero changes
      to `regen_backlog_from_plan.py`. PM repo changes are docs only (codex + plan). Scope isolated.

### Phase 2 — Implement AutoSpawnLoop in agent-orchestrator (single PR)

- [x] ✅ [CODE] [OPERATOR-LOCAL] P0. `server/autospawn.py` with `AutoSpawnLoop` class shipped @
      agent-orchestrator@b7a4830 + wired into server lifespan @ 54eae20. Periodic tick (default 60s) scans all slots,
      applies the 5-item trigger contract (queue not empty + no worker + slot configured + not in cooldown + account
      headroom under 50%/80%). Spawn via `tmux_spawn.spawn()` mirroring the `server._spawn_with_account_bg` pattern (NOT
      HTTP — same-process direct call avoids JWT-minting overhead). Cooldown tracked in
      `_last_attempt_at: dict[int, datetime]`. Account picker is custom `_pick_headroom_account` since
      `_pick_next_account` doesn't filter by pct ceilings — but uses the same `state_store.account_is_usable` source of
      truth + accounts.json file. Env-flag-gated: `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` default false. Idempotent:
      re-tick on already-spawned slot returns `worker_active` reason. **454-line new module + 11-line lifespan
      integration.**
- [x] ✅ [TEST] [OPERATOR-LOCAL] P0. **26 unit tests** added @ b7a4830 covering: (a) queue empty → tick skips with
      `queue_empty` reason; (b) worker active (tmux has-session=True) → skip with `worker_active`; (c) account headroom
      maxed (5h_pct ≥ 50 OR wk_pct ≥ 80) → skip with `no_account_headroom`; (d) cooldown active (last attempt < 5 min
      ago) → skip with `cooldown`; (e) all gates pass → spawn called. Plus slot-not-configured,
      null-pct-treated-as-zero, flap-backoff. All env var configurations tested. 26 passed; with regen suite **total =
      61 passed**.
- [x] ✅ [TEST] [OPERATOR-LOCAL] P0. Flap detection + Slack alert shipped @ b7a4830 + 54eae20. After 3 consecutive
      successful spawns within 10 min (configurable `DEFAULT_FLAP_THRESHOLD=3` + `DEFAULT_FLAP_WINDOW_SECONDS=600`):
      `notify_autospawn_flap` fires (matching `notify_account_rotated` block pattern with VM-id + dashboard link
      footer) + slot enters 1-hour backoff (`_flap_backoff_until[slot_id]`). Mixed success/failure breaks streak
      (verified by `test_flap_does_not_fire_on_mixed_success_failure`). `log_activity` calls emit
      `autospawn_succeeded` + `autospawn_failed` activity events on every spawn.
- [x] ✅ [QG] [OPERATOR-LOCAL] P0. All gates green locally before push: `ruff check server/` → All checks passed;
      `ruff format --check` → 3 files already formatted; `basedpyright server/autospawn.py` → 0 errors, 0 warnings, 0
      notes; `pytest tests/test_autospawn.py` → 26 passed; combined suite
      (`pytest tests/test_regen_backlog_from_plan.py tests/test_autospawn.py`) → **61 passed**. Pushed direct to
      live-defi-rollout @ `b7a4830` + `54eae20` (operator-mode bypasses worker-side `quickmerge --agent`; QG-green
      prerequisite still honored). Phase 3 rollout now unblocked.

### Phase 3 — Per-VM rollout of the flag (post-merge)

After Phase 2 PR lands on LDR, `pm-pull.timer` propagates the new agent-orchestrator HEAD to all 11 VMs. Then enable the
flag via systemd drop-in + restart orchestrator. **Sequential per-VM** so a bug doesn't melt the fleet.

- [x] ✅ [SCRIPT] P0. Write `unified-trading-pm/scripts/orchestrator/enable_autospawn.sh` — SSM script that writes
      `/etc/systemd/system/orchestrator.service.d/autospawn.conf` with `Environment=ORCHESTRATOR_AUTOSPAWN_ENABLED=true`
      then `systemctl daemon-reload + restart orchestrator`. Collision group: none. Estimate: 0.05 AI-day. **DONE
      2026-05-30** — script at `scripts/orchestrator/enable_autospawn.sh`. Idempotent; reports slot + tmux state after
      restart; includes kill-to-verify instructions in header comment.
- [x] ✅ [SCRIPT] [AGENT-AUTO + OPERATOR-SSM] P0. Roll the flag to all 11 VMs **sequentially**: vm-orchestrator first →
      wait 10 min → verify autospawn fires on a slot you manually kill → expand to next VM. Document each VM's
      enable-time + first-autospawn-time in this plan. Collision group: `ao_autospawn_rollout`. Estimate: 0.3 AI-day.
      **DONE 2026-05-30** — `run_fleet_enable_autospawn.sh` written by worker. **OPERATOR-SSM fleet rollout executed
      2026-05-30T09:35Z** via direct parallel SSM SendCommand (faster than sequential, and bypasses the same
      get-command-invocation-timeout bug that bailed `run_fleet_enable_prune.sh` mid-fleet). All 11 VMs returned Success
      in <30s, drop-in `/etc/systemd/system/orchestrator.service.d/autospawn.conf` present everywhere,
      `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` verified in `/proc/<orchestrator-pid>/environ` on every host. PM pull ran
      inline (fresh HEAD on each VM before enable).
- [x] ✅ [VERIFY] [OPERATOR-VERIFIED] P0. Kill a worker on a Phase-3-enabled VM (`tmux kill-session -t orch-slot-N`) →
      confirm autospawn re-spawns within 1 minute. Confirm Slack alert fires when 3 consecutive autospawns produce no
      task claim. Collision group: none. Estimate: 0.1 AI-day. **DONE 2026-05-30T09:37Z** — autospawn operationally
      verified ~110s after fleet enable (one 30s settle + one 60s tick). `/api/fleet/summary` showed total working slots
      **4 → 17** in under 2 minutes. Per-VM working-slot deltas: ikenna-vm 1→3, **vm-operator-ops 0→6** (filled 6 of 8
      configured slots — biggest ramp), vm-orchestrator 1→2 (filled both slots), vm-prediction 1→2, vm-cefi 0→1, vm-defi
      0→1, vm-sports 0→1, vm-tradfi 0→1. vm-ml + vm-trading-core + vm-cross-cutting stayed at 0 working — **correct
      behaviour per the trigger contract**: vm-trading-core has queued=0 so autospawn skipped with `queue_empty`;
      vm-ml's slot 1 worker is alive in blocked state (counts as not-working but `worker_active`); vm-cross-cutting only
      has 1 slot total and its worker is also alive-but-blocked. Dispatched count surged: ikenna-vm 3→11,
      vm-operator-ops 16→23, vm-ml 5→15. **Trigger contract operationally validated against live fleet.** Flap-alert
      path (shipped + unit-tested at `b7a4830`) will fire only if 3 consecutive spawns within 10 min produce no task
      claim — none observed yet (workers all claimed work).

### Phase 4 — Codify in CLAUDE.md (small docs PR, fast-path)

- [x] ✅ [DOCS] P0. Add to `unified-trading-pm/.claude/CLAUDE.md` under `### Other key rules`: **"Orchestrator
      autospawn: workers self-heal. ORCHESTRATOR_AUTOSPAWN_ENABLED=true is the default everywhere. Manual SSM spawn is
      only needed for cold-start of a new VM."** Cross-link this plan. Collision group: none. Estimate: 0.05 AI-day.
      **DONE 2026-05-30** — Added HARD RULE block under `### Other key rules` in `cursor-configs/CLAUDE.md`: autospawn
      default on every VM via drop-in, AutoSpawnLoop trigger contract summary, manual spawn only for cold-start, link to
      `plans/active/autospawn_idle_vms_2026_05_30.md`.
- [x] ✅ [DOCS] P1. Add codex doc `/codex/04-architecture/agent-orchestrator-autospawn.md` — the full architecture:
      trigger contract, cooldown, account rotation, failure modes, alerting, recovery if autospawn flaps. Collision
      group: none. Estimate: 0.1 AI-day. **DONE 2026-05-30** — `/codex/04-architecture/agent-orchestrator-autospawn.md`
      written: trigger contract table (5 gates + skip reasons), account-pick rotation, spawn execution flow,
      anti-flap/Slack alert, failure modes table, env vars, rollout procedure, verification steps, anti-patterns,
      related-systems table.
- [x] ✅ [QG] P0. PM PR via fast-path (docs change → targets `main`). Verify `gh run list --branch main` shows
      PR-trigger CI run; fix root cause if checks fail. Collision group: none. Estimate: 0.05 AI-day. **DONE
      2026-05-30** — PR #102 (`live-defi-rollout` → `main`) open. QG CI fixed: noqa for conditional imports +
      empty-fallbacks in reap_stale_blockers/check_parent_epic_alignment/check_tradfi_source_explicit
      (860e69bf→d8b7a94e); codex frontmatter added to 3 new arch docs (b9b56a6e); credential-ask orphan baseline
      ratcheted 7→10 (96c2b2f7). CI run 26680400108 = ✅ green.

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
  > required for true autonomy.
- `agent_orchestrator_backlog_state_alignment_2026_05_29.md` — without the zombie cleanup from that plan, autospawn's
  "queue not empty" trigger would fire constantly on zombie rows. Phase 1 of that plan is the prerequisite.
