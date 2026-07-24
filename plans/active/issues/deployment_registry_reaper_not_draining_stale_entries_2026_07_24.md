---
doc_type: issue
title:
  "Deployment registry drain P0 verified PARTIALLY: prod 503-timeout is FIXED, but the reaper isn't draining known-dead
  `active/` entries and the inventory endpoint's cold path can still exceed 45s"
summary: >-
  [REVIEW] end-to-end verification of `deployment_registry_firestore_p0_unblock_2026_07_14.md`'s Phase-0 fix, against
  the DEPLOYED `uts-shared-deployment-api` Cloud Run service (revision `uts-shared-deployment-api-00268-d2l`, image
  `deployment-api:e476c73`, confirmed a descendant of the reaper-tick commit `8660e9e`). The original prod-outage bug
  (census download of ~3.3k `active/` blobs timing out → empty Deployments tab) IS fixed for the realistic query shape:
  `active/` object count dropped from 3,304 (2026-07-14 baseline) to 404→403 (measured 2026-07-24), and `GET
  /api/deployments/inventory` (no `status` filter) returns HTTP 200 with 2,518 items (127 `running`) in well under 1s on
  a warm cache. Two residual gaps found during verification, neither present in the original P0 scope: (1) the reaper is
  NOT actually converging `active/` toward the live-VM count — a sample of 30 `active/` entries were ALL already
  classified `status="stale"` by the inventory endpoint's OWN display logic (heartbeat 3-7 days old, VM long gone) yet
  still sit in `active/` unreaped; Cloud Run logs show the reaper tick's `run_in_executor` call being interrupted by
  `asyncio.CancelledError` during container shutdown repeatedly over the last 3 days, a plausible culprit for why reaps
  aren't landing. (2) `_load_inventory`'s COLD path (no cache entry yet for a given `(cloud, region_scope)` key)
  computes synchronously under a lock with no bound — one such cold request (no `status` filter) exceeded 55s before the
  client gave up, while the identical request on a warm cache returned in <1s. This is the same "block past 45s" shape
  as the original bug, just triggered by an empty per-instance in-memory cache (`_inventory_cache` is process-local;
  Cloud Run's `minScale=1`/`maxScale=20` means a freshly scaled-up instance starts cold) rather than a huge `active/`
  backlog. Separately (not a defect, just a plan-clarity nit): the plan's own verification instruction (`GET
  .../inventory?status=all`) will ALWAYS return zero items by design — unlike the `region` param, `status` has no
  `"all"` bypass in `_filter_items` (`deployments_inventory.py:1418`, exact-match: `if status and item.status != status:
  return False`); the deployment-ui already codes around this deliberately (`Deployments.tsx:1412`,
  `deploymentApi.ts:654` both special-case `status==="all"` to OMIT the query param client-side rather than send it
  literally) — so this is expected/known frontend behavior, not a regression, but a reviewer following the plan's
  literal instruction gets a false "empty" result.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-trading-library]
scope: [engineer]
tags: [deployment-registry, reaper, observability, data-correctness, verification, hotfix]
related: [deployment_registry_firestore_p0_unblock_2026_07_14]
created: 2026-07-24
priority: P0
parent_epic: observability_master
source:
  "[REVIEW] slot-2 verification of the `deployment_registry_firestore_p0_unblock_2026_07_14.md` Phase-0 [REVIEW] P0 todo
  ('Verify the drain end-to-end against the DEPLOYED in-region API'), measured live against
  uts-shared-deployment-api-00268-d2l / deployment-api:e476c73 on 2026-07-24."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: true
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# Deployment registry drain — partial verification result (2026-07-24)

## What I found

**Before (from the plan's 2026-07-14 Progress Log, unchanged citation):**
`gs://deployment-scripts-central-element-323112/deployments/active/` = 3,304 objects;
`GET /api/deployments/inventory?status=all` on the then-deployed revision → HTTP 503 after 42.6s.

**After (measured live, 2026-07-24, this session):**

- `active/` object count: **404** (re-measured minutes later: **403**) — a ~87% reduction from the 3,304 baseline, but
  NOT yet "≈ running-VM count" (measured 9 RUNNING GCE instances in `central-element-323112` + 2 unrelated persistent
  AWS EC2 instances in `ap-northeast-1` that aren't part of this registry's tracked fleet).
- Deployed revision confirmed: `uts-shared-deployment-api-00268-d2l`, image `deployment-api:e476c73` (contains the
  reaper-tick commit `8660e9e` per the plan's own 2026-07-24 Progress Log entry).
- `GET /api/deployments/inventory` (no `status` filter — the query shape a real user/UI actually sends) → **HTTP 200**,
  **0.4–1.0s** on a warm cache, `total=2518`, `vm_count=2228`, `cloud_run_job_count=114`, 127 items with
  `status="running"`. Sample:
  ```json
  {"name": "mtds-dex-pools-backfill", "kind": "VM", "umbrella": "BATCH", "cloud": "GCP", "status": "running", "last_run_at": "2026-07-24T17:50:23Z", "heartbeat_age_seconds": 22}
  {"name": "canonical-migration-defi-marker-cleanup-20260724-182226", "kind": "VM", "umbrella": "BATCH", "cloud": "GCP", "status": "running", "last_run_at": "2026-07-24T18:24:58Z", "heartbeat_age_seconds": 53}
  ```
- **The literal plan instruction** `GET .../inventory?status=all` → HTTP 200 in 4.3s but
  `{"items":[],"total":0,"vm_count":0,...}` — expected/by-design (see summary), not a regression.

**Gap 1 — reaper not draining known-dead entries.** Sampled 30 random `active/` entries: **ALL 30** are
`status="running"` in the raw GCS blob but the inventory endpoint's own derived classification calls them
`status="stale"` (`last_heartbeat_at` 3–7 days old, e.g. `canonical-migration-cefi-wp11-wpf07210835` last heartbeat
2026-07-21, `af-backfill-20260718-124341` last heartbeat 2026-07-18). Per `DeploymentsRegistry._reap_reason()`
(`unified_trading_library/deployment_registry.py:455-482`), every one of these should be reaped (`vm_not_running` or
`heartbeat_stale`, both trigger at >6h) on the very next tick. They are not being reaped. Cloud Run logs
(`uts-shared-deployment-api`, last 3 days, severity≥WARNING) show a repeating traceback: `asyncio.CancelledError` raised
inside `_run_deployment_reaper`'s `loop.run_in_executor(...)` call (`deployment_api/background_sync.py:72`), triggered
from `_cancel_background_tasks` (`lifespan.py:126`, `asyncio.wait_for(_background_task, timeout=5)`) — i.e. the reaper
tick is being interrupted by a container shutdown/restart while still mid-flight, repeatedly, over the sampled window.
Never saw a single `"[SYNC_SERVICE] Reaper: archived"` / `"[AUTO_SYNC] Reaper: archived"` log line in 7 days of
`jsonPayload`+`textPayload` search — nor even the one-time `"Started background sync task"` /
`"Background auto-sync task started (leader worker)"` startup lines in 30 days, despite `minScale=1`. This is suggestive
of instances recycling far more often than expected, or the leader-election / lifespan startup path not completing as
assumed — root cause NOT fully diagnosed in this review session (out of scope for a review-only pass; needs a
BACKEND/INFRA todo).

**Gap 2 — cold-cache path can still exceed 45s.** `_load_inventory` (`deployments_inventory.py:2040-2073`): fresh (<TTL)
and stale (>TTL, existing snapshot) paths both return instantly (stale-while-revalidate). The **cold** path
(`cached is None` — no snapshot yet for this `(cloud, region_scope)` cache key) computes `_compute_inventory`
**synchronously, under a lock, with no timeout**. `_inventory_cache` is an in-process dict — NOT shared across Cloud Run
instances — so any freshly-scaled instance (this service runs `minScale=1`/`maxScale=20`) starts with an empty cache and
must pay this synchronous cost on its first request. Measured: one "no filter" request took **>55s** (client gave up);
the identical request retried immediately after returned in 0.4s (consistent with the slow request having finished
server-side and warmed the cache in the interim, or landing on a now-warm instance). This is the same "block past 45s"
failure shape as the original P0 bug, just triggered by a cold in-process cache instead of a huge `active/` backlog —
did not reproduce a second time in 3 attempts, so treating as a real but lower-confidence/lower-frequency finding, not a
confirmed steady-state regression.

## Why it matters

- The plan's own Success Criteria states `active/` object count should be "≈ running-VM count" — 403-404 vs ~9-11 is not
  that, and the underlying cause (reaper ticks apparently not completing) means the backlog will not self-heal; it may
  keep growing until it re-triggers the original timeout bug once it's big enough to slow `_compute_inventory` past 45s
  again on a cold instance (Gap 1 + Gap 2 compound).
- Downstream P1 todos in the SAME plan ("Enable dual-write on a SUBSET of the live fleet... VALIDATE Firestore mirrors
  GCS") depend on the registry being an accurate reflection of true fleet state — reaping is table stakes for that
  comparison to mean anything.
- Per workspace HARD RULE ("Data pipeline correctness is the heartbeat" / "Runtime verification — never done without
  running the code"), a review that found these gaps should not rubber-stamp the todo as done.

## Recommended decision

Do NOT flip the plan's `[REVIEW] P0. Verify the drain end-to-end...` checkbox — the core prod-outage bug is fixed, but
the plan's own success criteria ("active/ ≈ running-VM count") is not yet met and the root cause (reaper interrupted
mid-tick) is unresolved. Recommend: (1) a BACKEND/INFRA todo to diagnose why the reaper tick keeps getting cancelled
mid-flight (instance-recycling frequency vs an unrelated leader-election issue — note the total ABSENCE of even the
one-time startup log lines is itself worth checking first, cheaply, before chasing the cancellation angle); (2) a
BACKEND todo to bound/async-ify `_load_inventory`'s cold path the same way the stale-refresh path already is; (3) once
both ship, re-run this exact verification (`active/` count + the correct non-`status=all` inventory call) before
flipping the checkbox.

## Progress Log

- **2026-07-24 (slot-2)**: Diagnosed todo 1 via live `gcloud logging read` against `uts-shared-deployment-api` (project
  `central-element-323112`). Confirmed root cause directly from prod stderr: the recurring `asyncio.CancelledError`
  traceback at `background_sync.py:72` (inside `_run_deployment_reaper`'s `run_in_executor` call) IS happening, many
  times/day — caused by `lifespan.py`'s `_cancel_background_tasks()` giving the background task only a 5s grace period
  on shutdown, far shorter than a real reap tick's runtime (list_running_vm_names + a sequential per-blob
  `list_active()` download, documented ~138s at 3k-entry scale). `run_in_executor`'s underlying thread can't be
  interrupted by asyncio cancellation, so every worker recycle/restart that lands mid-tick orphans the reap with zero
  net progress. Fix applied: bumped the timeout 5s→20s in `deployment-api/deployment_api/lifespan.py` (leaves headroom
  under gunicorn's `graceful_timeout=30`). Also found (separate, filed as its own issue): a `Uncaught signal: 6`
  (SIGABRT) crash-loop hitting this same service ~35×/day (every 20-40 min per `varlog/system`) — likely compounding the
  same interruption problem, not root-caused in this session →
  `/plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md`. **Code fix is written + individually verified
  but NOT YET SHIPPED**: a full `quality-gates.sh` run surfaced 5 pre-existing test failures unrelated to this change
  (verified via `git stash` on clean HEAD). 1 was a trivial, well-precedented UAC-parity drift (`EMPTY_REASON_KEYS`
  missing `EXPECTED_SUBGRAPH_DEINDEXED`) — fixed inline. The other 4 are a live data-correctness regression from a
  DIFFERENT, still-in-flight migration (sports `FIXTURES`→`FIXTURES_SCHEDULE` atom rename) — NOT mine to fix (owned by
  `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 1) → filed
  `/plans/active/issues/fixtures_schedule_atom_migration_partial_landing_regression_2026_07_24.md` + declared
  repo-blocker `RB-f19d63e7` for `deployment-api` + posted `/blocked` (`BLK-7b657f46`) for operator visibility. Waiting
  on that repo-blocker to clear before `quickmerge` can ship; diff sits ready (uncommitted) in the slot-2
  `deployment-api` worktree.

## Todos

- [x] ✅ [BACKEND] P0. Diagnose why `deployment-api`'s reaper tick (`_run_deployment_reaper`,
      `deployment_api/background_sync.py:59`) is not archiving GCS `deployments/active/` entries that the service's OWN
      inventory endpoint already classifies `status="stale"` (heartbeat >6h old, VM confirmed gone). Start cheap:
      confirm whether `"[AUTO_SYNC] Started background sync task"` /
      `"Background auto-sync task started (leader     worker)"` (`lifespan.py:223`) ever appears in Cloud Run logs for
      `uts-shared-deployment-api` — if it NEVER fires, the leader-election gate (`is_leader_worker()`,
      `deployment_api/utils/worker_identity.py`) is the root cause, not the reaper logic itself. If it DOES fire, then
      chase the repeating `asyncio.CancelledError` inside `run_in_executor` (`background_sync.py:72`) during
      `_cancel_background_tasks` (`lifespan.py:120-143`) — check actual Cloud Run instance restart frequency/count over
      the same window. Fix at the root cause (repo: deployment-api). — **deployment-api@1c1987ad**: confirmed live via
      `gcloud logging read` against `uts-shared-deployment-api` prod stderr — the leader-election startup line DID fire
      historically (stdout logging was separately silent for an unrelated reason, root-caused by a concurrent
      `deployment-api@f27a8f1`), and the recurring `asyncio.CancelledError` at `background_sync.py:72` IS the live root
      cause: `_cancel_background_tasks()`'s 5s grace period is far shorter than a real reap tick's runtime (tens of
      seconds to minutes at current ~400-entry `active/` backlog scale; `run_in_executor`'s underlying thread can't be
      interrupted by asyncio cancellation), so essentially every worker recycle orphaned the tick with zero progress.
      Fixed by bumping the grace period 5s→20s (within gunicorn's `graceful_timeout=30`). Also filed, separately,
      `/plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` (an independent, undiagnosed SIGABRT
      crash-loop ~35×/day likely compounding the same interruption problem — not root-caused in this session).
- [x] [BACKEND] P1. Bound or async-ify `_load_inventory`'s cold-cache path
      (`deployment_api/routes/deployments_inventory.py:2040-2073`) — today it computes `_compute_inventory`
      synchronously under `_inventory_lock` with NO timeout when `_inventory_cache` has no entry for the
      `(cloud, region_scope)` key. Since `_inventory_cache` is in-process (not shared across Cloud Run instances,
      `minScale=1`/`maxScale=20`), every freshly-scaled instance pays this cold cost on its first request — apply the
      same stale-while-revalidate treatment already used for the TTL-expired path (return a fast placeholder + kick
      `_kick_background_refresh`), or at minimum wrap the synchronous compute in the existing
      `_PROVIDER_CENSUS_TIMEOUT_SEC` bound so a cold hit degrades gracefully instead of blocking indefinitely (repo:
      deployment-api). ✅ — **deployment-api@6f6a389**: cold path now calls the SAME `_kick_background_refresh`
      submission the TTL-expired path uses (in-flight guard collapses concurrent first-polls to ONE census — never
      double-submits) and bound-waits on it via `future.result(timeout=_PROVIDER_CENSUS_TIMEOUT_SEC)`; a census that
      doesn't finish in time degrades to an honest empty placeholder (never fabricated data) while the compute keeps
      running in the background and warms the cache for the next poll. `_refresh_inventory`/`_kick_background_refresh`
      now return the computed items/Future so the cold path can consume the same in-flight compute instead of a separate
      synchronous block. quality-gates.sh green; shipped via quickmerge --agent.
- [x] [REVIEW] P1. Once both todos above ship, re-run this same end-to-end verification: `active/` object count
      before/after (must be ≈ live-VM count this time, not just "much smaller"), plus 3 consecutive
      `GET /api/deployments/inventory` (no `status` filter) calls each <45s including a genuinely cold one (e.g. right
      after a fresh deploy/revision rollout). Only then flip the plan's original `[REVIEW]` P0 checkbox. — **RE-VERIFIED
      2026-07-24 (slot-4, review): STILL NOT MET, plus a new P0 regression found.** Both fixes confirmed deployed
      (content-diffed against `deployment-api:366154d`, revision `uts-shared-deployment-api-00270-2l9`). `active/`
      count: still 403–404, unchanged from the pre-fix baseline, both ~1h45m after the P0 reaper fix went live and
      ~10min after the P1 cold-cache fix went live — vs ~9 actually-running VMs. Do NOT flip the plan's original
      `[REVIEW]` checkbox. Full detail + a NEW P0 finding (the P1 cold-cache fix removed the old global serialization on
      cold census computations — 2 concurrent cache-key computations OOM-killed the whole container, 17,002MiB used vs
      16,384MiB limit, `Container terminated on signal 9`, a MORE SEVERE failure mode than the bug it fixed) in
      [issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md](deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md).

- **2026-07-24 (slot-4, review)**: Re-ran the end-to-end verification per the todo above, against the freshly deployed
  `uts-shared-deployment-api-00270-2l9` (`deployment-api:366154d`) — confirmed via `gcloud builds log` (Cloud Build
  `b9005961`, SUCCESS) and content-diff (`git show 366154d:<path> | grep`, not just ancestry-check — the LDR→main
  promote path squash-commits, so `git merge-base --is-ancestor` alone under-reports) that both shipped fixes AND the
  sibling issue doc's faulthandler instrumentation are present in the deployed image. Result: `active/` object count
  unchanged at 403–404 vs ~9 actually-running VMs (7 GCE + 2 AWS EC2), both long after the P0 fix and shortly after the
  P1 fix went live — the plan's success criterion is NOT met. Additionally reproduced a NEW P0 regression: the P1
  cold-cache fix's `_kick_background_refresh` mechanism dropped the old code's full serialization of cold census
  computations (previously one global lock held for the whole compute; now a 2-worker pool lets different cache keys run
  concurrently), and 2 concurrent census computations (default-region stale-refresh + an `all_regions=true` cold poll)
  OOM-killed the container (17,002MiB vs 16,384MiB limit, `signal 9`) — plausibly the SAME mechanism behind the
  still-unconfirmed SIGABRT crash-loop in the sibling issue doc. Filed
  [issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md](deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md)
  (P0, BACKEND) with a concrete reproduction + 4 candidate fix approaches. Did NOT flip this plan's original `[REVIEW]`
  checkbox — leaving it as-is with its existing partial-pass note, now additionally pointing at the new issue doc. No
  code changes made this session (review-only pass).
