---
doc_type: codex-runbook
title: agent-orchestrator FailoverLoop re-enable checklist
summary:
  What must be true before flipping ORCHESTRATOR_FAILOVER_ENABLED=true — registry populated, ≥2 hosts, the
  offline-reroute/rollback gate tests green, the paused-slot-selection fix deployed — and how to verify the first real
  re-route without guessing. FailoverLoop is dormant-but-kept (operator ruling 2026-07-20) and has never fired in
  production, so re-enabling it without this checklist means discovering whether it works during a real incident.
status: current
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [runbook, agent-orchestrator, failover, resilience, multi-vm, dormant-infra]
related:
  [
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    ../../plans/active/ao_failover_multi_vm_readiness_2026_07_20.md,
  ]
created: 2026-07-20
owner: operator (ad-hoc — only when multi-VM genuinely returns)
cadence: on-demand (pre-re-enable gate — not periodic)
verifier:
  "/api/ops/failover/status fleet_registry_entries > 0 + a real offline/return cycle produces failover_rerouted then
  failover_rolled_back activity rows"
last_executed:
code_refs:
  [
    agent-orchestrator/server/failover.py,
    agent-orchestrator/server/routes/vms.py,
    agent-orchestrator/server/routes/ops.py,
  ]
audience: operator / dev
last_updated: 2026-07-20
execution:
  {
    owner: "operator (ad-hoc — only when multi-VM genuinely returns)",
    cadence: "on-demand (pre-re-enable gate — not periodic)",
    verifier:
      "/api/ops/failover/status fleet_registry_entries > 0 + a real offline/return cycle produces failover_rerouted then
      failover_rolled_back activity rows",
    last_executed: NEVER,
  }
---

# agent-orchestrator FailoverLoop re-enable checklist

## What this is

`FailoverLoop` (`agent-orchestrator/server/failover.py`) re-routes soft-pinned tasks off a host that stops heartbeating.
It is **kept but dormant** — multi-VM is not running today, but the operator ruled 2026-07-20 it is likely to return for
resilience/backup, so the code stays and gets hardened instead of deleted
([`ao_failover_multi_vm_readiness_2026_07_20.md`](../../plans/active/ao_failover_multi_vm_readiness_2026_07_20.md)).

**Do not flip `ORCHESTRATOR_FAILOVER_ENABLED=true` (or call `POST /api/ops/failover/enable`) without going through this
checklist first.** The loop has zero `failover_rerouted` events for all of production history — untested resilience
machinery is worse than none, because its first real execution then happens during the incident it was supposed to
soften.

## Pre-enable checklist

All of the following must be true:

1. **The paused-slot-selection fix is deployed.** `_pick_least_loaded_slot` must be the eligibility-filtered version
   (excludes `paused` / `killed` / review / unconfigured slots, not just the offline host's own slots) —
   `agent-orchestrator@03d48e8` or later. Check:
   `git log --oneline -- server/failover.py | grep -i "exclude unusable slots"` should show a commit reachable from your
   deployed SHA. Without this, re-routing can land a task on a slot guaranteed never to run it.
2. **The gate tests are green.** `tests/test_failover.py` + `tests/test_failover_integration.py` pass under
   `bash scripts/quality-gates.sh`. The integration file exercises the offline-reroute and rollback paths against a real
   DB session (not mocks) — it is the only test coverage that has ever actually executed those code paths.
3. **`fleet_registry.json` is populated with every intended host.** Check `GET /api/ops/failover/status` →
   `fleet_registry_entries`. Zero means the loop can enable and run forever without ever detecting an offline host —
   `FailoverLoop.start()` now logs a loud `logger.warning` in this case specifically so this can't happen silently, but
   check the number directly rather than relying on log-scraping.
   - A registry entry only appears after a worker VM calls `POST /api/vms/register` — done automatically by
     `scripts/bootstrap_vm.sh` STEP 10 **on AWS only**. There is currently no GCP self-registration branch (tracked as a
     P3 todo on the readiness plan above) — a GCP-provisioned host will NOT appear here until that gap is closed.
     Confirm every intended host's cloud provider before trusting the count.
4. **At least 2 distinct hosts are in the registry**, and you can identify which `SlotRow.git_status_host` values map to
   which registry `id`/`label` (`_slots_for_host` matches case-insensitively on either). One host can't fail over to
   itself.
5. **You know the heartbeat threshold you're accepting.** Default `ORCHESTRATOR_FAILOVER_HEARTBEAT_THRESHOLD_SECONDS` =
   600s (10 min). A host that's merely slow (not actually down) for >10 min gets its tasks re-routed — confirm this
   matches the actual restart/recovery SLA of the hosts involved before enabling.

## Enabling

Two equivalent paths — pick one:

```bash
# A. Systemd drop-in (persists across restarts) — set on the CENTRAL orchestrator VM only
#    (single decision source; see failover.py module docstring)
ORCHESTRATOR_FAILOVER_ENABLED=true

# B. Hot-enable at runtime, no restart (idempotent)
curl -X POST https://<central-api>/api/ops/failover/enable -H "Authorization: Bearer <token>"
```

Both routes converge on `FailoverLoop.start()` — the empty-registry warning fires either way.

## Verifying the first real re-route

Do not assume it works because the loop is "running". Verify an actual cycle:

1. **Confirm the loop is running and sees the fleet you expect:**
   ```bash
   curl -s https://<central-api>/api/ops/failover/status -H "Authorization: Bearer <token>" | python3 -m json.tool
   # Expect: "running": true, "fleet_registry_entries" >= 2, "previously_offline_hosts": []
   ```
2. **Force (or wait for) a real offline transition** on a non-critical host — stop its heartbeat cron / take it offline
   for longer than the threshold — with at least one `failover_allowed=True`, queued, undispatched task pinned to one of
   its slots.
3. **Watch for the re-route**, within one `ORCHESTRATOR_FAILOVER_INTERVAL_SECONDS` tick (default 60s) of the threshold
   being crossed:
   - `previously_offline_hosts` in `/api/ops/failover/status` includes the host.
   - An activity-feed row with `event_type=failover_rerouted` exists for the task, `details.from_slot`/`to_slot` show a
     real target — not the same paused/dead slot.
   - The task's `target_slot` actually changed in the DB.
4. **Bring the host back and watch for rollback:**
   - `previously_offline_hosts` drops the host.
   - An activity-feed row with `event_type=failover_rolled_back` exists for the task (only if it's still
     queued+unclaimed — a task a worker already picked up on the failover target must NOT roll back).
5. Only after a real cycle has been observed end-to-end is failover something you can rely on during an actual incident,
   not just something that's turned on.

## Troubleshooting

| Symptom                                                 | Likely cause                                                                                                         | Fix                                                                                                               |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `fleet_registry_entries: 0` after enabling              | No worker VM has called `POST /api/vms/register` (single-VM topology, or a GCP host — no self-register branch there) | Confirm `bootstrap_vm.sh` ran STEP 10 on each worker; for GCP hosts, register manually or close the P3 todo first |
| Loop running, host genuinely offline, nothing re-routes | No `failover_allowed=True` queued+undispatched task was pinned to that host's slots                                  | Check `TaskRow.failover_allowed` / `target_slot` for the tasks you expected to move                               |
| Re-route picks a slot that never runs the task          | Paused-slot-selection fix not deployed (pre-`03d48e8`)                                                               | Deploy the fix; re-verify via the gate tests before re-enabling                                                   |
| Rollback never fires when host returns                  | Task was already dispatched before the host came back (correct — by design, live work isn't yanked)                  | Not a bug; only queued+unclaimed tasks roll back                                                                  |
| `/api/ops/failover/status` 404s or `not_initialized`    | Server hasn't wired the loop yet (lifespan hasn't run, or you're hitting the wrong backend)                          | Check you're hitting the CENTRAL orchestrator's API, not a worker VM's local one                                  |

## Cross-references

- [`agent-orchestrator/server/failover.py`](../../../agent-orchestrator/server/failover.py) — the loop itself; module
  docstring has the full trigger contract.
- [Recovery defence-in-depth layers](/codex/04-architecture/recovery-defence-in-depth-layers.md) — where (and where not)
  failover sits among the workspace's recovery mechanisms.
- [Autonomous recovery matrix](/codex/04-architecture/autonomous-recovery-matrix.md) — kill-switch / auto-recovery scope
  this loop does NOT participate in.
- [`ao_failover_multi_vm_readiness_2026_07_20.md`](../../plans/active/ao_failover_multi_vm_readiness_2026_07_20.md) —
  the plan that produced this checklist + the paused-slot fix + the gate tests.

## Reviewer enforcement

Per the workspace Runbook Execution-Owner SSOT, every real execution of this checklist (i.e. every time failover is
actually re-enabled) updates `last_executed:` above with evidence — the `/api/ops/failover/status` output at enable time
and the activity-feed rows from the first verified re-route/rollback cycle. A PR that flips `last_executed:` without
that evidence is review-blocked.
