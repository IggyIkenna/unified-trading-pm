---
title: "Orchestrator agent-lifecycle gaps — reaper skips stale records + central-VM VM_ID config drift"
created: 2026-06-16
status: active
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-16 review-agent reliability work (restore-on-ping / stale-extension / tmux_session / hung-respawn chain)
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
