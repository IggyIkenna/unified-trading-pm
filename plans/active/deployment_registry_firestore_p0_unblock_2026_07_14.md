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
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
sequential: true
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
> `status: active`, no `depends_on`. **Pulled to LOCAL execution 2026-07-14** (`assigned_vm: NA` /
> `execution_scope: local-only`) — AO's per-task turnaround on this chain was too slow (3 P0 tasks still `queued` after
> 6h); driving the remaining P0 todos + the full downstream chain interactively instead. Do not flip back to
> `assigned_vm: planning` without operator instruction.

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

- [x] ✅ [BACKEND] P0. In `auto_sync_running_deployments()` ([background_sync.py:59]), add a ~15-min reaper tick gated
      by a time-modulo (mirror `_run_ttl_cleanup` at line 36). Reuse THIS cycle's already-fetched running-VM set (do not
      re-call GCE) to build `running_vm_names`, then call
      `DeploymentsRegistry(bucket=DEFAULT_BUCKET).reap_stale(running_vm_names=running)`. Wrap in
      `try/except (OSError, ValueError, RuntimeError)`, log the reaped count, never re-raise into the loop. —
      deployment-api@8660e9e, unified-trading-library@b1cdeb77. See Progress Log for a plan/code discrepancy found + the
      design deviation this required.
- [x] ✅ [BACKEND] P0. Make the first drain non-blocking + bounded: run the reap in `run_in_executor` (do not block the
      event loop on a ~138s `list_active`), and cap archives per tick (e.g. 500) so the ~3k backlog drains over several
      ticks; log `reaped=N remaining≈M` each tick. Steady-state (active/ ≈ live count) then reaps in <1s/tick. —
      deployment-api@8660e9e (`_REAPER_MAX_PER_TICK=500`), unified-trading-library@b1cdeb77
      (`DeploymentsRegistry.reap_stale(max_reap=...)`).
- [ ] [REVIEW] P0. Verify the drain end-to-end against the DEPLOYED in-region API: record `active/` object count before
      and after (expect → ≈ running-VM count), and `GET /api/deployments/inventory?status=all` returning non-empty live
      VMs within the 45s bound. Put the before/after numbers + a 200-with-items sample in the Progress Log.
- [x] ✅ [INFRA] P0. Add a SIGTERM handler to the UTL heartbeat daemon — unified-trading-library@04c72ef5
      ([`lifecycle/daemon.py`](../../unified-trading-library/unified_trading_library/lifecycle/daemon.py),
      `HeartbeatDaemon`) that, on SIGTERM, calls `store.complete(self.entry)` (status=failed + exit_code set) within the
      SPOT ~30s preemption grace, then stops the daemon. Idempotent — safe if `complete()` was already called. This
      archives preempted backfill VMs at the source instead of leaving `active/` ghosts.
- [x] ✅ [REVIEW] P0. Unit tests: (a) the reaper tick calls `reap_stale` with the running set and swallows a raised
      reaper error without breaking the loop; (b) a SIGTERM during a running daemon archives the entry (status=failed)
      rather than leaving it `running`. Run `bash scripts/quality-gates.sh` green in BOTH deployment-api and
      unified-trading-library. — deployment-api@47f9b20 (5 new tests in `test_background_sync.py`: tick-boundary gate,
      OSError/ValueError swallow, end-to-end swallow-does-not-break-loop), unified-trading-library@5f015cb5 (3 new tests
      in `test_daemon.py`: SIGTERM archives status=failed, run()'s post-loop `complete()` is idempotent after a signal,
      a raising `store.complete` inside the handler doesn't propagate). Both repos' `quality-gates.sh --no-fix` run
      fresh (sentinel cleared first, not a cache hit) green: deployment-api 128s, unified-trading-library 151s.
- [ ] [INFRA] P0. Ship: commit + push deployment-api and UTL changes (cite `<repo>@<sha>` each) and flip this plan's
      items (`docs(plans):`). THEN hand off (draft-gated chain): edit
      `deployment_registry_firestore_p1_dualwrite_2026_07_14.md` frontmatter `status: draft`→`active` and commit
      (`docs(plans):`), so the fleet ingests Phase 1. Activate ONLY the immediate next phase, nothing further
      downstream.

## Success criteria

- prod Deployments tab (deployed API) returns the live fleet within 45s; `active/` object count ≈ running-VM count.
- SPOT-preempted backfill VMs archive themselves on SIGTERM (verified by test), so `active/` no longer accumulates
  ghosts between reaper ticks.
- No `os.getenv`; UTC datetimes; reaper never raises into the sync loop; QG green on both repos.

## Progress Log

- **2026-07-14 (slot 1, review)** — Attempted the deployed-API end-to-end verification for the `[REVIEW]` P0 todo above.
  **BLOCKED — the fix has not reached the deployed instance yet**, so the "after" half of the check cannot be done
  honestly. Leaving the checkbox unflipped; details below.
  - **Before (confirmed live in prod, matches the plan's problem statement):**
    - `gs://deployment-scripts-central-element-323112/deployments/active/` object count = **3,304** (measured just now
      via `gcloud storage ls | wc -l`; consistent with the plan's "measured 2026-07-14: 3,270" — it's still growing).
    - `GET https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/api/deployments/inventory?status=all` → **HTTP 503
      after 42.6s** (deployed API, no in-flight fix). Confirms the census-timeout bug is still live in prod right now.
    - Live GCE instance count (this project, `RUNNING` only): 18
      (`gcloud compute instances list --project=central-element-323112`).
  - **Why "after" can't be measured yet**: the deployed Cloud Run service (`uts-shared-deployment-api`, revision
    `uts-shared-deployment-api-00163-44l`) is running image `deployment-api:30c4d46` — that's the LDR→main promote from
    PR #278 (merged 2026-07-14T00:57Z), which predates the reaper-tick work. `deployment-api@8660e9e` (the
    [BACKEND]-shipped reaper tick) is **98 commits ahead of `main`** on `live-defi-rollout`, only reachable via the open
    promote PR **#279** (`promote/deployment-api/8660e9eccb6f`).
  - **PR #279 is failing `quality-gates-v2`** (`gh run 29328006371`, `QG slice (lint-codex)` job):
    `❌ Codex compliance FAILED: 6 violations (max allowed: 5)`. I confirmed this is **pre-existing and unrelated to
    this phase's diff** — none of the flagged long-function violations touch `background_sync.py`, `sync_service.py`, or
    `deployment_registry.py` (the files this phase changed); the violating files are unrelated data-status/breakdown
    modules. Something in the 98-commit LDR/main gap since PR #278 pushed the codex-compliance count from 5→6. This is a
    **shared-pipeline blocker** — it blocks EVERY pending promote for this repo, not just this plan.
  - **Recommendation** (chatted to main): file/assign a fix for the codex-compliance regression (identify which of the
    98 commits added the 6th long-function violation, then either shorten that function or bump the accepted baseline
    per `codex/06-coding-standards/quality-gates.md` if warranted) so PR #279 goes green and `deployment-api@8660e9e`
    actually deploys. Once deployed, re-run this same before/after check (before-count already captured above) to close
    this todo.

- **2026-07-14 (slot 3, backend-engineer)** — Shipped both [BACKEND] todos.
  - **Plan/code discrepancy found**: the plan assumed `auto_sync_running_deployments()` "already fetches the GCE VM list
    each cycle" to reuse as `running_vm_names`. Traced `SyncService.sync_deployments()` → `scan_deployment_states()` /
    `EventProcessor` and found NO aggregated GCE VM-list call anywhere in that path — `EventProcessor` only reads
    per-deployment `vm_status.json` from GCS. The only existing aggregated-list helper is
    `deployment_api/vm_utils.py::list_running_vm_names(project_id)`, used today by the manual
    `POST /vm-deployments/reconcile` endpoint ([`vm_deployments.py:285-288`]). Adapted: the reaper tick calls
    `list_running_vm_names` itself, but only on the same ~15-min gate as the reap itself (not every 30-60s sync cycle),
    so the extra GCE aggregated-list RPC stays cheap/bounded rather than being re-fetched every cycle.
  - **Design deviation (test-safety)**: rather than calling `DeploymentsRegistry`/`list_running_vm_names` directly
    inside `background_sync.py` (as the plan's snippet implies), the reap logic is a new
    `SyncService.reap_stale_deployments(max_reap=500)` method, and the background-sync tick calls
    `_sync_service.reap_stale_deployments(...)`. Reason: `tests/unit/test_background_sync.py` runs the REAL
    `auto_sync_running_deployments()` loop with only `SyncService` + `asyncio.sleep` mocked; a bare/direct GCP call
    added straight into the tick body would have a small but real per-test-run chance of firing a genuine GCE/GCS call
    (this worker VM carries real ADC credentials) — including a real `reap_stale` archiving real `deployments/active/`
    entries from a unit test run. Routing through `_sync_service` (the object every existing test already replaces
    wholesale) makes the new tick a guaranteed no-op under those mocks, matching how `_run_ttl_cleanup` already relies
    on `_sync_service.cleanup_state_ttl`. Verified: ran `tests/unit/test_background_sync.py` 6× — 15/15 passed every
    time, ~0.16-0.48s (no real network calls slipping through).
  - **`reap_stale(max_reap=...)` added** to `DeploymentsRegistry` (unified-trading-library) rather than bounding only in
    the caller — bounds the archive burst (GCS upload+delete pairs) directly at the source, logs
    `reaped=N remaining≈M (capped at max_reap=M)` on the same cadence the gotcha asked for. First cut of `reap_stale`
    landed at 58 lines (`MAX_METHOD_LINES=50` in this repo's QG) — extracted the per-entry archive+stamp step into
    `_archive_reaped_entry()` to bring it under the limit; behavior unchanged, confirmed by the existing 33 (+2 new)
    unit tests in `test_deployment_registry.py`.
  - Added `test_reap_stale_max_reap_caps_archives_per_call` (unified-trading-library) covering the new cap: archives
    exactly `max_reap` per call, leaves the remainder in `active/`, and a follow-up call drains the rest — this is the
    only new test added; it covers the `max_reap` code path only, NOT the full reaper-tick / SIGTERM coverage the
    [REVIEW] todo below still needs.
  - QG: both repos ran `bash scripts/quality-gates.sh --no-fix` full-green against their committed HEAD before shipping
    (deployment-api 139s/128s, unified-trading-library 174s). Shipped via `quickmerge --agent --files`, both landed on
    `live-defi-rollout` with zero unpushed commits remaining (`git rev-list --count HEAD ^origin/live-defi-rollout` = 0
    in both repos post-ship).
  - **Handoff for [REVIEW]/[INFRA] todos below**: the reaper tick + `reap_stale(max_reap=...)` are shipped and unit-
    tested at the `max_reap` level; NOT YET done: (a) the reaper-tick-level unit test asserting it swallows a raised
    reaper error without breaking the loop, (b) the SIGTERM daemon handler + its test, (c) the deployed-API before/
    after `active/` count verification, (d) the Phase-1 draft→active handoff.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — registry-classification SSOT (context; no update this phase).
- `codex/05-infrastructure/spot-vms-for-backfill.md` — why backfill VMs are SPOT (the orphaning source).
