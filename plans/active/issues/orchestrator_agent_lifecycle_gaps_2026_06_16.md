---
title: "Orchestrator agent-lifecycle gaps — reaper skips stale records + central-VM VM_ID config drift"
created: 2026-06-16
status: active
priority: P1
locked_by: live-defi-rollout
source:
  - 2026-06-16 review-agent reliability work (restore-on-ping / stale-extension / tmux_session / hung-respawn chain)
  - 2026-06-17 LIVE INCIDENT — account-pool headroom exhaustion starved all escalation spawns + froze the main agent (Gap 6)
parent_epic: orchestrator_master
---

# Orchestrator agent-lifecycle gaps (2026-06-16)

Two follow-up gaps surfaced while shipping the **review-agent reliability chain** on the central orchestrator VM
(`agent-orchestrator`). The chain itself is shipped + deployed: restore-on-ping (`4bcd3f4`), stale-extension
(`807e927`), `tmux_session` on the self-register path (`01ec482`), and hung-review-agent auto-respawn (`c42b007`). These
two gaps are the remaining loose ends found during that work.

## What I found

### Gap 1 — the reaper never reaps a `stale` sessionless agent record (agent-orchestrator)

`reap_orphan_agents` (`server/state_store/agents.py`) only scans `AgentRow.status == "active"`. But `health.py` marks a
silent agent `stale` after 20 min (`server/health.py` ~L265). A `stale` agent whose `tmux_session` is NULL (or whose
session is dead) is therefore **never re-examined** — it lingers in the DB / dashboard indefinitely. This session I had
to archive `agt-bf6061` + `agt-4ff41f` (dead review records, `status=stale`, `sess=None`) **by hand** because nothing
reaps them.

**Why it matters**: dead `stale` records accumulate forever, cluttering the dashboard's agents list; the reaper's whole
job (keep records honest vs tmux reality) has a blind spot for exactly the records `health.py` dims.

- [ ] [ORCHESTRATOR] P2. Extend `reap_orphan_agents` to also consider `status == "stale"` agents: archive a `stale`
      agent whose tmux session is dead (`dead-tmux-session`) or which is sessionless + silent past `stale_grace`
      (`stale-no-session`) — mirroring the existing active-agent reap branches. Add a unit test (in-memory SQLite, the
      `test_reap_orphan_agents.py` pattern). Composes with restore-on-ping (a `stale` agent that RESUMES pinging is
      already reactivated by `update_agent_ping`; this covers the dead-and-staying-dead case). Repo: agent-orchestrator.

### Gap 2 — central VM declares `ORCHESTRATOR_VM_ID` inconsistently (`planning` vs `vm-0`)

On the central VM, two config sources declare a different `ORCHESTRATOR_VM_ID` — one `planning`, one `vm-0` (seen in
`/etc/systemd/system/orchestrator*` + the repo `.env*`). The VM_ID feeds the host operator →
`expected_branch = tab/{operator}/{slot}` in the FM7 branch-state gate (`worktree_clean_check`). An ambiguous VM_ID
makes the gate's expected branch ill-defined and compounds AutoSpawn branch-state quarantine noise on the central VM.

**Why it matters**: the FM7 gate compares each slot worktree's HEAD to `tab/{operator}/{N}`. Under Path-B the central
VM's slot worktrees sit on `live-defi-rollout`, so the gate already mismatches; an inconsistent VM_ID compounds the
ambiguity. Clean VM_ID config is a prerequisite for reasoning about the central VM's branch-state gate.

- [ ] [CONFIG] P2. Reconcile `ORCHESTRATOR_VM_ID` to ONE canonical value across every config source on the central VM
      (the registry id `planning` per `orchestrator_human_central_vm_split_2026_06_12.md`); verify the FM7
      `expected_branch` derivation is consistent with the actual Path-B worktree branch (`live-defi-rollout`) so
      AutoSpawn does not quarantine clean slots. Repo: agent-orchestrator (config) + deployment-service (VM
      provisioning).

### Gap 3 — `_prune_stale` ignores `execution_scope: local-only` + strict-mode, so stale tasks zombie

`regen_backlog_from_plan._prune_stale` builds its "current briefs" set (the todos that should remain) WITHOUT the
`execution_scope == local-only` skip or the `require_vm_match` (strict) filter that the scan loop applies. So on a VM
that owns ≥1 plan, a plan later marked `local-only` (or that falls out of this VM's scope) keeps its queued tasks
forever — the prune still treats their briefs as "current" and never GCs them. Separately, the DB-GC safety guard
(`if current_briefs:`) correctly refuses to GC when a VM legitimately owns nothing, so a VM whose entire scope is
local-only (e.g. the central VM) can never auto-clear and needs a manual backlog wipe.

**Why it matters**: observed 2026-06-16 — marking the planning-owned plans `local-only` did NOT clear their
already-queued tasks; they had to be cleared by hand. A worker VM that owns other plans would silently zombie the
local-only plan's tasks (AutoSpawn keeps them dispatchable).

- [ ] [ORCHESTRATOR] P2. Mirror the scan-loop scope filters EXACTLY in `_prune_stale`'s current-briefs walk
      (`execution_scope == local-only` skip + the issues opt-in + the `require_vm_match` strict filter); thread
      `require_vm_match` through from `regen()`. Factor the shared filter into one helper so scan + prune cannot drift
      again. Add a test: a plan flipped to `local-only` → its queued tasks are pruned on the next regen. Repo:
      agent-orchestrator.

### Gap 4 — central VM backend runs under TWO process managers (systemd + main-agent `nohup`) → bind races + stale-state re-persistence

The central VM's backend is managed by `orchestrator.service` (systemd, `enabled`), but the **main orchestrator agent
also self-heals it via `nohup .venv/bin/python3 -m uvicorn …`** (seen in its shell-snapshot restart script). When both
fire they race for `127.0.0.1:8765`: one binds, the other crash-loops on "address already in use", and an orphaned
uvicorn (ppid=1, untracked by systemd) keeps the pre-restart backlog in memory and **re-persists stale tasks over any
disk clear**.

**Why it matters**: observed 2026-06-16 — three competing uvicorns on the central VM; a backlog clear kept getting
undone until the agent-`nohup` instance was killed. Single-management is a prerequisite for any reliable backend-state
operation (clear / restart / reconfigure) on the central VM.

- [ ] [ORCHESTRATOR] P1. Make the central VM backend single-managed: the main-agent self-heal must
      `sudo systemctl restart orchestrator.service` (NOT `nohup uvicorn`), and the launch path must refuse to start a
      second instance when `:8765` is already bound (pre-bind check). Audit + remove the nohup path from the main-agent
      restart snapshot. Repo: agent-orchestrator.

### Gap 5 — `ORCHESTRATOR_BACKLOG` points at the RETIRED `harsh_orchestrator/backlog.yaml`

The central VM's `.env.local` sets `ORCHESTRATOR_BACKLOG=…/unified-trading-pm/harsh_orchestrator/backlog.yaml` — a path
under the `harsh_orchestrator/` tree that was **retired 2026-05-25** (CLAUDE.md: only `_agent_pings.md` stays there). It
is gitignored runtime state so it functions, but routing the live backlog through a retired PM-repo path is confusing.

**Why it matters**: observed 2026-06-16 — it cost real time to discover that clearing the backlog had to target this
file, not the canonical `agent-orchestrator/data/config/backlog.yaml`.

- [ ] [CONFIG] P2. Repoint `ORCHESTRATOR_BACKLOG` to the canonical `agent-orchestrator/data/config/backlog.yaml` (or
      drop the override so it defaults there) on the central VM; migrate any live runtime backlog; verify regen writes
      the canonical path. Repo: agent-orchestrator (config) + deployment-service (VM provisioning).

### Gap 6 — account-pool headroom exhaustion starves ALL escalation spawns + freezes the main agent; abandon path emits a misleading "Auto-respawn FAILED slot 0" alert (LIVE INCIDENT 2026-06-17)

**Trigger**: two Slack pages 2026-06-17 09:04 UTC — `escalation agt-753352 abandoned after 24h queued` (features-service
`ldr_qg_failure`) + `escalation agt-705557 abandoned after 24h queued` (fund-administration-service `ldr_qg_failure`),
both rendered under a `:rotating_light: Auto-respawn FAILED slot 0` header.

**Root cause (verified on the central VM `agent-orchestrator-vm` / `i-0c9b283b…` state.db + tmux 2026-06-17 ~11:00
UTC)**: the Claude **account pool is exhausted**, so `autospawn._pick_headroom_account()` returns `None` for long
stretches. Ceilings are `weekly < 80%` AND `5h < 50%` (`autospawn.DEFAULT_WEEKLY_PCT_CEILING=80` /
`DEFAULT_FIVE_HOUR_PCT_CEILING=50`); live `account_usage`:

| account | weekly% | 5h% | rate_limited_until | status | verdict |
| --- | --- | --- | --- | --- | --- |
| sub-a-ikenna | 14 | 31 | **2026-06-17 14:00** | healthy | headroom, but RATE-LIMITED until 14:00 → excluded |
| sub-b-iggy2london | **98** | 71 | 2026-06-21 | healthy | over weekly ceiling + RL 4 days → excluded |
| sub-c-ikenna-odum | **87** | 1 | (elapsed) | healthy | over weekly ceiling → excluded |
| sub-d-odum1default | **100** | 21 | none | healthy | over weekly ceiling → excluded |
| harsh-primary | — | — | — | **auth_failed since 2026-06-10** | excluded |

→ every account filtered out → `pick_headroom_account → None` → **escalations cannot dispatch**. Live queue: **39
queued, 19 abandoned, 7 resolved**; 20 queued carry `last_error="no headroom setup-token account"`. The FIFO-head row
(`agt-3bd816`) shows **attempts=230** — the AutoSpawnLoop `retry_queued_escalations` IS running and hammering the head
every tick, always failing headroom, then `break` (so newer rows stay `attempts=0`). Abandoned set includes **real,
silently-dropped walls**: `main_ci_red` (SIT / fund-admin), `merge_conflict` (PM ×2), `ldr_qg_failure` (e2e ×6,
fund-admin ×5, features ×2, strategy ×2, …).

**Consequence — the "agent stuck for 24h"**: the main orchestrator agent (`orch-agent-main`, tmux session up since
2026-06-16 12:01) hit its account's usage cap and is **frozen at the interactive Claude CLI modal** "What do you want to
do? → 1. Stop and wait for limit to reset / 2. Upgrade your plan" (last useful output 03:16 UTC). `main_agent_keeper`
rotates the main agent onto a headroom account — but there is none, so it cannot recover and the agent wedges on a modal
that won't auto-dismiss even after the limit resets.

**Why it matters**: the orchestrator's entire CI self-healing loop (escalation dispatch + main-agent plan-health) is
down whenever the account pool has no headroom — and the operator is paged with a **misleading** signal that points at
the wrong fix. `escalation.retry_queued_escalations` calls `slack.notify_agent_stuck_escalation(0, …)` on abandonment,
which renders `:rotating_light: Auto-respawn FAILED slot 0 … SSH to VM, tmux ls, inspect, manually respawn` — there is
no slot 0, and respawning solves nothing; the real fix is account capacity. 19 abandonments → up to 19 misleading
"manually respawn slot 0" pages, while the actual condition (pool exhausted) is never paged as such.

**Immediate operator recovery (NOT a code fix)**:

- [ ] [HUMAN] P0. **Restore account headroom on the central VM.** Highest leverage: re-auth `harsh-primary` (idle
      `auth_failed` since 2026-06-10 = a full fresh weekly budget) via `claude setup-token` → update its
      `oauth_token_env_file`. `sub-a-ikenna` self-frees at 14:00 UTC. Until then the escalation loop + main agent stay
      starved. Repo: operator/credentials (agent-orchestrator `accounts.json`).
- [ ] [HUMAN] P1. **Unwedge the frozen main agent** (`orch-agent-main`): once a headroom account exists, dismiss the
      "Stop and wait for limit to reset" modal (select 1 + Enter) or restart the main agent so `main_agent_keeper`
      re-spawns it on the healthy account. Repo: operator (central VM tmux).

**Durable fixes (agent-orchestrator)** — all SHIPPED `agent-orchestrator@38fde6cc` (LDR), QG-green (680 passed):

- [x] ✅ [ORCHESTRATOR] P0. **Misleading "Auto-respawn FAILED slot 0" alert killed.** Added
      `notify_escalation_abandoned(escalation_id, repo, wall_type, age_hours, reason)` (slack + telegram) naming the
      wall + real cause + "free account capacity" action; `retry_queued_escalations` calls it instead of
      `notify_agent_stuck_escalation(0, …)`. No fake slot id, no "manually respawn". — agent-orchestrator@38fde6cc
- [x] ✅ [ORCHESTRATOR] P0/design (operator 2026-06-17). **Raise spawn-headroom ceilings 5h 50→95 / weekly 80→95** via
      shared env-tunable helpers `autospawn.five_hour_pct_ceiling()`/`weekly_pct_ceiling()` wired into the autospawn
      tick, escalation dispatch, `main_agent_keeper`, and `plan_health` (the latter three previously hardcoded the
      DEFAULT consts, ignoring the env override). 80% needlessly excluded accounts with ~20% real budget left (sub-c at
      87% — the incident). — agent-orchestrator@38fde6cc
- [x] ✅ [ORCHESTRATOR] P1. **Sustained account-pool exhaustion paged** (deduped, re-armed on recovery):
      `_maybe_alert_pool_exhaustion` fires `notify_account_pool_exhausted(queued, account_summary)` once per episode
      when escalations wait with no headroom account — the real signal, not per-escalation spam. — agent-orchestrator@38fde6cc
- [x] ✅ [ORCHESTRATOR] P1. **No silent drop of an UNRESOLVED wall.** `retry_queued_escalations` re-probes
      `_poll_wall_resolution` at the 24h soft TTL: cleared → resolved; still-RED → HELD queued (dispatchable when
      capacity returns); only past a 48h HARD ceiling is it abandoned (honest alert). — agent-orchestrator@38fde6cc
- [x] ✅ [ORCHESTRATOR] P1. **Main-agent rate-limit modal detected + auto-handled.** `main_agent_keeper._handle_rate_limit_modal`
      captures the live main-agent pane (session-alive ≠ healthy), matches the usage-cap modal, KILLS the wedged
      session (→ next tick respawns on a headroom account), and pages once. — agent-orchestrator@38fde6cc

> **Deploy note**: shipped to AO `live-defi-rollout`; takes effect on the central VM after `git pull --ff-only` +
> `systemctl restart orchestrator.service`. With the 95% ceiling, `sub-c` (87% weekly) becomes immediately usable →
> escalations drain + the keeper respawns the main agent.
>
> **DEPLOYED + VERIFIED 2026-06-17 11:36 UTC** (central VM, `orchestrator.service` restarted on `38fde6cc`): log shows
> `AutoSpawnLoop started … 5h_ceiling=95% wk_ceiling=95%`; `MainAgentKeeper: main agent wedged on usage-cap modal —
> killing for account swap` → killed → **respawned on `sub-c-ikenna-odum`** (`spawned main agent agt-2743af`); AutoSpawn
> also spawned `orch-slot-2` on sub-c. Account-pool starvation is broken. (`sub-a` also back in use.)

**Gap 6 residual — escalation drain now head-of-line-blocked by a quarantined slot (surfaced 2026-06-17 once headroom was fixed)**:

With headroom restored, the FIFO-head escalation `agt-3bd816` now fails with `spawn failed: branch-state quarantine
(FM5/FM7)` on **slot 1** (its `unified-api-contracts` worktree is `diverged` — behind 78, ff-only blocked by
uncommitted local edits to `unified_api_contracts/canonical/domain/sports/league_data.py`). Two distinct problems keep
all 39 queued walls stuck behind it:

- [ ] [HUMAN/INVESTIGATION] P1. **Clean the central-VM slot-1 `unified-api-contracts` quarantine** — the worktree holds
      FOREIGN uncommitted WIP (`sports/league_data.py`); do NOT stomp it. Owner of that WIP must commit/inherit or
      discard it, then `git pull --ff-only`, so slot 1 leaves FM5 quarantine. (Same worktree flagged in "Related" below
      — now the active escalation-drain blocker.) Repo: central VM slot-1 worktree.
- [ ] [ORCHESTRATOR] P1. **`_pick_free_slot` must skip branch-quarantined slots.** It returns the lowest free
      configured slot without consulting branch-state, so it deterministically hands every escalation to the quarantined
      slot 1 and never tries clean slots (3/6). Make it skip a slot whose worktree fails the `worktree_clean_check`
      branch-state gate (the same FM5/FM7 check `do_spawn` applies), falling through to the next clean slot. Repo:
      agent-orchestrator (`server/escalation.py`).
- [ ] [ORCHESTRATOR] P1. **`retry_queued_escalations` must not head-of-line-block on a slot-specific spawn failure.**
      The loop `break`s on every `EscalationError` (correct for genuine no-capacity, wrong for a `spawn failed:
      branch-state quarantine` that is specific to one slot) → one un-spawnable head freezes the whole queue. Distinguish
      "no capacity" (break) from "this slot/spawn failed" (skip the slot / try the next), composing with the
      `_pick_free_slot` fix above. Repo: agent-orchestrator (`server/escalation.py`).

## Related (NOT owned here — likely the live VM-state issue under separate investigation)

The central VM's **slot-1 is FM5-quarantined**: its `unified-api-contracts` worktree is diverged (behind 8, ff-only
failed due to uncommitted local changes to `sports/league_data.py`). This is a dirty/diverged dep worktree blocking
slot-1 worker spawns — almost certainly part of the "worker agents flipped plan items" VM issue already under
investigation by another agent (operator note 2026-06-16). Captured here for traceability; the fix belongs to that
investigation, not this doc.

## Recommended decision

Gaps 1-3 + 5 are self-heal / config hardening (P2; not blocking — the review-agent chain works today). **Gap 4 is P1**:
the dual process-manager actively undermined backend state management on the live central VM (2026-06-16 — port-bind
races + stale-backlog re-persistence) and should be fixed first. Fix Gap 1 + Gap 3 on the next `agent-orchestrator`
touch (both small, mirror existing branches + add a test). Gaps 2 + 5 are config reconciles best done alongside whoever
resolves the central-VM branch-state issue.

Gaps 3-5 were surfaced 2026-06-16 while enforcing "central VM ingests nothing"
(`ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true`

- the planning-owned plans marked `execution_scope: local-only`). That end state is live + verified (regen ingests 0;
  backlog 0); these gaps are the residual hardening so it stays that way without manual intervention.
