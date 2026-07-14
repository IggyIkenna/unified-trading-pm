---
doc_type: plan
title: Deployment registry Firestore migration — Phase 0 — unblock prod (schedule reaper + graceful complete)
summary:
  Restore the prod Deployments tab NOW, before the multi-week Firestore migration. The inventory census times out and
  renders empty because ~3k stale registry entries must be downloaded within a 45s bound. Fix it two ways — schedule the
  existing reaper (reap_stale) as an in-process tick in deployment-api's background-sync loop so active/ drains to ≈
  live-VM count, and add a SIGTERM handler in the UTL heartbeat daemon so SPOT-preempted backfill VMs archive themselves
  instead of becoming ghosts. GCS-only, partly throwaway once Firestore lands, but prod is broken today.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-trading-library]
scope: [engineer]
tags: [firestore, deployment-registry, observability, reaper, hotfix]
related:
  - deployment_registry_firestore_migration_2026_07_14.md
  - codex/05-infrastructure/deployment-observability.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 0)
---

# Phase 0 — Unblock prod (schedule the reaper + graceful complete)

> **Dispatch:** `assigned_role: infra` · **model: Sonnet** (default) · **effort: high**. First phase of the chain —
> `status: active`, no `depends_on`, so it dispatches immediately. Every downstream phase is also `active` but
> machine-held via `gate_on_depends` until its prerequisites finish.

## Context (read first — self-contained)

The deployment registry is one JSON blob per deployment at
`gs://deployment-scripts-<project>/deployments/active/<deployment_id>.json`
([UTL `deployment_registry.py`](../../unified-trading-library/unified_trading_library/deployment_registry.py), class
`DeploymentsRegistry` at line 296; `ACTIVE_PREFIX = "deployments/active/"` at line 145). The inventory census
([`deployment-api/deployment_api/routes/deployments_inventory.py`](../../deployment-api/deployment_api/routes/deployments_inventory.py))
downloads+parses every `active/` blob within `_PROVIDER_CENSUS_TIMEOUT_SEC = 45.0`; on timeout it discards the whole
census (live VMs included). **Measured 2026-07-14: 3,270 active entries for 44 live VMs → timeout → empty prod tab.**

The reaper already exists and is correct — `DeploymentsRegistry.reap_stale(max_age_hours=6, running_vm_names, now)`
([`deployment_registry.py:429`](../../unified-trading-library/unified_trading_library/deployment_registry.py)) archives
any active entry whose VM is not in `running_vm_names` OR whose heartbeat is older than `max_age_hours` (via
`complete()` → status=failed, exit_code=125, `extras["reap_reason"]`). **The bug: nothing schedules it** — it is only
reachable via the manual `POST /vm-deployments/reconcile` endpoint
([`vm_deployments.py:258` `reconcile_vm_deployments`](../../deployment-api/deployment_api/routes/vm_deployments.py)).

The in-process loop to hook into is `async def auto_sync_running_deployments()`
([`deployment-api/deployment_api/background_sync.py:59`](../../deployment-api/deployment_api/background_sync.py)), which
already runs every 30–60s and already fetches the GCE VM list each cycle; the hourly-modulo gating pattern is
`_run_ttl_cleanup` at line 36 (`if (_time.time() % 3600) >= current_interval`).

**Gotchas (must honour):** the reaper's own `list_active()` downloads every blob (~138s for 3k) — so the FIRST drain
must not block the async loop (run it in a bounded thread executor + cap archives per tick, spread over several ticks,
log remaining count — no silent truncation). Best-effort: a reaper error must NEVER raise into the sync loop. No
`os.getenv` (use `UnifiedCloudConfig`). No `raise` in the per-entry archive loop (reap_stale already isolates per
entry). UTC datetimes only. `quality-gates.sh`-green before each commit; commit + push + cite shas.

## Todos

- [ ] [BACKEND] P0. In `auto_sync_running_deployments()` ([background_sync.py:59]), add a ~15-min reaper tick gated by a
      time-modulo (mirror `_run_ttl_cleanup` at line 36). Reuse THIS cycle's already-fetched running-VM set (do not
      re-call GCE) to build `running_vm_names`, then call
      `DeploymentsRegistry(bucket=DEFAULT_BUCKET).reap_stale(running_vm_names=running)`. Wrap in
      `try/except (OSError, ValueError, RuntimeError)`, log the reaped count, never re-raise into the loop.
- [ ] [BACKEND] P0. Make the first drain non-blocking + bounded: run the reap in `run_in_executor` (do not block the
      event loop on a ~138s `list_active`), and cap archives per tick (e.g. 500) so the ~3k backlog drains over several
      ticks; log `reaped=N remaining≈M` each tick. Steady-state (active/ ≈ live count) then reaps in <1s/tick.
- [ ] [REVIEW] P0. Verify the drain end-to-end against the DEPLOYED in-region API: record `active/` object count before
      and after (expect → ≈ running-VM count), and `GET /api/deployments/inventory?status=all` returning non-empty live
      VMs within the 45s bound. Put the before/after numbers + a 200-with-items sample in the Progress Log.
- [ ] [INFRA] P0. Add a SIGTERM handler to the UTL heartbeat daemon
      ([`lifecycle/daemon.py`](../../unified-trading-library/unified_trading_library/lifecycle/daemon.py),
      `HeartbeatDaemon`) that, on SIGTERM, calls `store.complete(self.entry)` (status=failed + exit_code set) within the
      SPOT ~30s preemption grace, then stops the daemon. Idempotent — safe if `complete()` was already called. This
      archives preempted backfill VMs at the source instead of leaving `active/` ghosts.
- [ ] [REVIEW] P0. Unit tests: (a) the reaper tick calls `reap_stale` with the running set and swallows a raised reaper
      error without breaking the loop; (b) a SIGTERM during a running daemon archives the entry (status=failed) rather
      than leaving it `running`. Run `bash scripts/quality-gates.sh` green in BOTH deployment-api and
      unified-trading-library.
- [ ] [INFRA] P0. Ship: commit + push deployment-api and UTL changes (cite `<repo>@<sha>` each) and flip this plan's
      items with the `docs(plans):` prefix. Phase 1 is already `active`, machine-held by its `gate_on_depends` until
      this plan's tasks are all done — do NOT hand-edit any sibling plan's status.

## Success criteria

- prod Deployments tab (deployed API) returns the live fleet within 45s; `active/` object count ≈ running-VM count.
- SPOT-preempted backfill VMs archive themselves on SIGTERM (verified by test), so `active/` no longer accumulates
  ghosts between reaper ticks.
- No `os.getenv`; UTC datetimes; reaper never raises into the sync loop; QG green on both repos.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — registry-classification SSOT (context; no update this phase).
- `codex/05-infrastructure/spot-vms-for-backfill.md` — why backfill VMs are SPOT (the orphaning source).
