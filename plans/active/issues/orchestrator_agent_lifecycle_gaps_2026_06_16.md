---
title: "Orchestrator agent-lifecycle gaps — reaper skips stale records + central-VM VM_ID config drift"
created: 2026-06-16
status: active
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-16 review-agent reliability work (restore-on-ping / stale-extension / tmux_session / hung-respawn chain)
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

## Related (NOT owned here — likely the live VM-state issue under separate investigation)

The central VM's **slot-1 is FM5-quarantined**: its `unified-api-contracts` worktree is diverged (behind 8, ff-only
failed due to uncommitted local changes to `sports/league_data.py`). This is a dirty/diverged dep worktree blocking
slot-1 worker spawns — almost certainly part of the "worker agents flipped plan items" VM issue already under
investigation by another agent (operator note 2026-06-16). Captured here for traceability; the fix belongs to that
investigation, not this doc.

## Recommended decision

Both gaps are P2 self-heal hardening (not blocking — the review-agent chain works today). Fix Gap 1 on the next
`agent-orchestrator` touch (small, mirrors existing reaper branches + a test). Gap 2 is a config reconcile best done
alongside whoever resolves the slot-1 / central-VM branch-state issue.
