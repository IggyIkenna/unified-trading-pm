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
  AWS EC2 instances in `ap-northeast-1`, at this point framed as not part of this registry's tracked fleet — **note:**
  the later 2026-07-24 slot-4 re-verification (Progress Log below / Todo 3) instead folds both into the comparator as
  "~9 actually-running VMs (7 GCE + 2 AWS EC2)"; the two measurements are unreconciled — it's unclear whether AWS EC2 is
  actually in scope for this registry's success criterion, and whether the GCE-only count genuinely dropped 9→7 between
  measurements or was miscounted in one of the two passes).
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
      Fixed by bumping the grace period 5s→20s (within gunicorn's `graceful_timeout=30`) — **this fixed only the
      `CancelledError` symptom (ticks no longer get killed mid-flight), NOT the underlying drain/convergence problem**:
      the 2026-07-24 (slot-4) re-verification below found `active/` unchanged at 403–404 post-fix, so Gap 1 (reaper not
      draining) remains open — see Todo 4. Also filed, separately,
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
      [issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md](/plans/archive/issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md).
- [x] ✅ [BACKEND] P1. **Root-cause why `active/` is still not converging toward the live-VM count after the P0
      `CancelledError`/grace-period fix (Todo 1) and P1 cold-cache fix (Todo 2) both shipped and were re-verified live
      (Todo 3, slot-4: still 403–404, unchanged).** This is Gap 1 itself, distinct from the sibling OOM regression
      (`plans/archive/issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md`, which tracks a DIFFERENT,
      newly-discovered crash bug from the P1 fix) — that sibling doc's own fix does not address why reap ticks that DO
      complete aren't archiving the sampled stale entries. Next steps: confirm a reap tick is actually completing
      end-to-end post-fix (look for the `"[SYNC_SERVICE] Reaper: archived"` / `"[AUTO_SYNC] Reaper: archived"` log lines
      that were NEVER observed in 7 days pre-fix — their continued absence post-fix would point at a second,
      still-undiagnosed blocker beyond the `CancelledError` symptom); if ticks ARE completing, re-sample the 30
      previously-`status="stale"` entries to see whether they were archived or the reap logic itself is silently
      no-op'ing on them. Done-when: the root cause of non-convergence is identified and either fixed + re-verified
      (`active/` ≈ live-VM count) or a concrete blocker is documented. — **ROOT-CAUSED + FIXED 2026-07-25 (slot 2)**:
      `unified-trading-library@4773a3fd`. `"[AUTO_SYNC] Reaper: archived"` confirmed STILL absent 3+ hours after the
      P0/P1 fixes deployed (`gcloud logging read` against `uts-shared-deployment-api`, no matches over 3 days) — AND the
      exact same `asyncio.wait_for(_background_task, timeout=20)` → `_run_deployment_reaper`'s `run_in_executor` failure
      from Todo 1 is STILL firing live (traceback captured `2026-07-25T01:03:36Z`, well after the 5s→20s fix shipped).
      Root cause: `DeploymentsRegistry.list_active()` (`unified_trading_library/deployment_registry.py`) downloads every
      `active/*.json` blob **sequentially**, one `download_string` call at a time — the doc's own cited ~138s/~3k-entry
      rate implies ~46ms/blob, so at the current ~400-entry backlog the tick itself takes ~18-20s, landing right at (or
      over) the 20s grace period. The P0 fix bought headroom but the tick's own duration eats it right back — every
      container recycle (deploy, scale-down, or the sibling SIGABRT crash-loop) still interrupts it before completion,
      so `_archive_reaped_entry` never runs and the backlog cannot converge even though the reap LOGIC itself is correct
      (confirmed via existing test `test_reap_stale_archives_stale_entries`, still passing). **Fix**: parallelized the
      per-blob downloads with a bounded `ThreadPoolExecutor(max_workers=32)` (mirrors the existing idiom in
      `manifest_consolidator.py::_prune_stale_consolidated_shards`) — same ordering, same per-blob malformed-entry-skip
      behavior (still logs + skips, never raises), just concurrent I/O instead of one-at-a-time; should cut wall-clock
      roughly by the worker-count factor. All 42 pre-existing `test_deployment_registry.py` tests pass unmodified; full
      `quality-gates.sh` green (254s). **Not re-verified live this session** — needs an automatic LDR→main promote +
      fresh Cloud Run deploy + several minutes of reap-tick cadence (900s interval) before `active/` count convergence
      can be measured; a future dispatch should re-run the same verification as Todo 3 (`active/` count vs live-VM
      count, plus checking for the now-expected `"Reaper: archived"` log lines) once the fix is confirmed live via
      `git merge-base --is-ancestor 4773a3fd origin/main` + the deployed image tag. **UPDATE 2026-07-25T05:55Z (slot 10,
      review) — RE-VERIFIED, fix IS deployed but `active/` STILL has NOT converged.** Correcting this todo's own
      verification instruction: do NOT rely on `git merge-base --is-ancestor` alone — it fails FOREVER post-squash-merge
      regardless of whether the content shipped (full writeup:
      [issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md](/plans/archive/issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md)).
      Content-diffed instead: `git show origin/main:unified_trading_library/deployment_registry.py` shows
      `ThreadPoolExecutor(max_workers=32)` present, byte-identical to LDR's copy — the fix's content genuinely reached
      `main`. Caveat found while checking: deployment-api consumes UTL via a **local editable path**
      (`unified-trading-library = { path = "../unified-trading-library", editable = true}`, `pyproject.toml:67`), not a
      pinned version, so UTL's own `main` having the fix does NOT by itself prove the DEPLOYED CONTAINER's build
      vendored that exact content — flagging as a real verification gap, not glossed over. Checked BEHAVIORALLY instead
      (sidesteps that gap): since revision `uts-shared-deployment-api-00274-s9g` went live (`2026-07-25T02:51:26Z`,
      ~2.5h before this check), `gcloud logging read` shows **zero** `"Reaper: archived"` lines (still absent, as before
      the fix) AND **zero** `_run_deployment_reaper`/`CancelledError` tracebacks either (also absent — the OLD failure
      symptom isn't recurring, but neither is the expected NEW success signal). `active/` object count measured **404**
      right now vs **9** currently-running VMs (`GET .../inventory?status=running` → `vm_count=9`) — unchanged from the
      pre-fix 403-404 baseline. **Not resolved** — either the built container doesn't actually carry the UTL fix (the
      editable-path gap above), or the reap tick still isn't executing/completing for a different reason than diagnosed.
      New todo added below rather than re-asserting the fix worked without evidence.
- [x] ✅ [BACKEND] P0. **Determine why `active/` still hasn't moved (404, unchanged) despite
      `unified-trading-library@4773a3fd`'s parallelization fix being live on `main` for ~2.5h with zero
      `"Reaper: archived"` lines AND zero `_run_deployment_reaper` tracebacks (neither the old failure nor the expected
      new success signal appears in Cloud Logging).** Check, in order: (1) confirm the DEPLOYED CONTAINER's build
      actually vendored the fixed UTL content — deployment-api depends on `unified-trading-library` via a local editable
      path (`pyproject.toml:67`), not a pinned version, so verifying UTL's own `main` has the fix does not prove the
      built image does; inspect the Cloud Build log / image layer for the actual bundled `deployment_registry.py`
      content if possible. (2) If the container IS correct, confirm the reaper tick is being invoked AT ALL post-deploy
      (add a cheap one-time INFO log at tick start if none exists — the total silence of BOTH the old error and the new
      success line is itself suspicious). (3) Re-check `active/` vs live-VM count once resolved. (repo: deployment-api,
      unified-trading-library) — **ROOT-CAUSED 2026-07-25 (slot 3) via DIRECT IMAGE INSPECTION, not source-repo
      content-diff** (the same false-confidence gap slot 10 flagged but nobody had yet directly checked):
      `docker     pull`ed the LIVE revision's actual image (`uts-shared-deployment-api-00275-7zl`,
      `sha256:1282490246ad38c7b9398ae09f1982351d3aea0837935c8e8b1b00c3421f42a6`), extracted
      `unified_trading_library/deployment_registry.py` and both `gunicorn.conf.py` copies from inside it. Confirmed the
      deployed `deployment_registry.py` has **NO `ThreadPoolExecutor`** — the UTL parallelization fix genuinely never
      reached this image, even though `git show origin/main:...` (what every prior verification pass checked) has it.
      Traced further: the triggering Cloud Build (`7b80517d...`, commit `2efbbcb` — which DOES contain the fix per
      content-diff) produced this EXACT image digest, so the gap isn't a stale/skipped build — chasing that is now a
      separate open question (see the new todo below), not needed to close THIS one. **The real, confirmed, and now
      FIXED root cause for the other symptom (zero faulthandler dumps, zero "Reaper: archived" lines, zero "Started
      background sync task" lines) is a wrong-file bug, unrelated to any build/cache mystery**: two `gunicorn.conf.py`
      files existed in `deployment-api` — a repo-root one (`COPY`'d + loaded by BOTH `Dockerfile` and
      `Dockerfile.dashboard` via `-c /app/gunicorn.conf.py`) and `deployment_api/gunicorn.conf.py` (a duplicate). The
      two SIGABRT/leader-election fix commits (`1adf54b`, `7ba17e2`, both cited as "confirmed live" by prior sessions
      via `git show origin/main:deployment_api/gunicorn.conf.py`) both edited the **`deployment_api/` copy — which
      `deployment_api/gunicorn.conf.py`'s own unit test exercised (hence green `quality-gates.sh`), but which production
      NEVER LOADS**. Extracted the root file from the SAME live image: it's the old stub — bare `pass` in `post_fork`,
      no `post_worker_init` hook at all, so `faulthandler.enable()` never runs AND `worker_identity.set_worker_age()`
      never runs, meaning `is_leader_worker()` (which defaults `True` when `_worker_age` is unset) returns `True` for
      **every** worker, not one — every gunicorn worker has been redundantly running its own auto-sync/reaper loop this
      whole time, contending on the same GCS locks. **Fixed**: `deployment-api@3fea307` — ported both hooks
      (leader-election `post_fork` + faulthandler `post_worker_init`) into the ACTUAL root `gunicorn.conf.py` using
      deferred (function-local, not module-level) imports of `deployment_api.settings`/`worker_identity` — a
      module-level import in this file crashes gunicorn at config-load time (reproduced locally:
      `BucketNamingError: GCP_PROJECT_ID is not set`, since config-load happens BEFORE `preload_app`'s own app import) —
      this is exactly why the root file was originally written to read `PORT`/`WORKERS` straight from env instead of
      importing settings. Deleted the dead `deployment_api/gunicorn.conf.py` duplicate + repointed its test at the real
      file. **Runtime-verified end-to-end against a real local gunicorn boot** (not just unit tests): with `WORKERS=2`,
      exactly one worker now logs `"Background auto-sync task started (leader     worker)"` and the other logs
      `"...skipped (non-leader worker)"` (previously ALL workers would claim leadership); sent a real `SIGABRT` to a
      running worker and it produced a full `Fatal Python error`/`Current thread` faulthandler dump before gunicorn
      cleanly respawned a replacement worker (which itself correctly re-elected a new leader).
      `bash scripts/quality-gates.sh` green (pytest + all steps, twice — once pre-commit dirty-tree, once post-commit
      against the exact shipped SHA). Shipped via `quickmerge --agent --files`, landed on `live-defi-rollout` at
      `deployment-api@3fea307c679d8c974dc68594555d4760524a4935`. **NOT yet re-verified against PROD `active/`
      convergence** (needs a fresh Cloud Run deploy of this fix + several reap-tick intervals to observe — see new todo
      below) and the SEPARATE "why did a build from a commit with the UTL fix produce an image without it" question is
      also still open — both spun into a new todo rather than closing this one on an unverified assumption.
- [ ] [BACKEND] P0. **Two follow-ups from the wrong-gunicorn-file root-cause fix (`deployment-api@3fea307`):** (1) Once
      `3fea307` reaches a fresh Cloud Run deploy, re-verify via the SAME direct-image-extraction method used to find
      this bug (NOT source-repo content-diff — grep the actual pulled/extracted image for `post_worker_init` in
      `/app/gunicorn.conf.py`) that it's really live, then watch `gcloud logging read` for
      `"Background auto-sync task     started (leader worker)"` appearing exactly ONCE per instance (not per-worker) and
      `"[AUTO_SYNC] Reaper: archived"` appearing at all for the first time ever; re-measure `active/` object count vs
      live-VM count after ≥2 reap-tick intervals (900s each). (2) SEPARATELY, root-cause why Cloud Build
      `7b80517d-0457-44b7-9e59-b53076b9bbc9` (triggered from commit `2efbbcb`, which DOES contain
      `unified-trading-library@4773a3fd`'s `ThreadPoolExecutor` fix per content-diff) produced image
      `sha256:1282490246...` whose `unified_trading_library/deployment_registry.py` does NOT contain that fix — check
      the Dockerfile's `FROM ...unified-trading-library@${BASE_IMAGE_DIGEST}` base-image pin (line ~45): if
      `BASE_IMAGE_DIGEST` wasn't refreshed to a UTL base image built from `4773a3fd`, deployment-api's OWN fresh commit
      wouldn't matter — the vendored UTL code comes from a SEPARATE, independently-tagged base image, not from
      re-cloning UTL at deployment-api build time. This is a distinct, real gap from the gunicorn-file bug and needs its
      own verification once found. (repo: deployment-api) — **(2) ROOT-CAUSED 2026-07-25 (slot 6, backend_engineer),
      part (1) still open.** Confirmed via the live service's own
      `/api/cloud-builds/library-status/unified-trading-library` endpoint: deployed `package_version` = `0.55.0`,
      nowhere near `main`'s current `0.56.1.dev357+g6afe62c71`. Traced the full publish chain live (gh CLI + gcloud, not
      source-repo content-diff): UTL's `quality-gates-v2.yml` correctly dispatched `qg-passed` for the exact push
      carrying `4773a3fd` (`gh run` `30145177081`, job "Dispatch cloud-build trigger (main release)" succeeded,
      2026-07-25T05:06:23Z); PM's `cloud-build-router.yml` correctly received it (`gh run` `30145190398`, job
      `route-build` reports `success`) — but that job's own log shows the REAL failure:
      `gcloud builds triggers run unified-trading-library-prod --region=asia-northeast1` →
      **`ERROR:     NOT_FOUND: Requested entity was not found`**, silently swallowed as a WARNING (job still reports
      green, no alert fires). `gcloud builds triggers list --project central-element-323112` confirms **no
      `unified-trading-library-prod` trigger exists at all** (sibling `instruments-service-prod` does, confirming the
      naming convention). `gcloud artifacts docker images list ...unified-trading-library --sort-by="~UPDATE_TIME"`
      confirms **zero images have published since 2026-07-23T09:12:10Z** — 51+ hours and 15+ main-branch commits stale
      as of this writing, despite `update-dependency-version.yml`'s digest-refresh mechanism itself working correctly
      (it just has nothing new to propagate). This is why `BASE_IMAGE_DIGEST` was already at its "freshest" refreshed
      value and STILL didn't carry `4773a3fd` — the freshest value available IS the stale one. Full evidence +
      recommended remediation (GCP infra action — recreate the trigger, out of backend_engineer craft scope) filed as
      its own cross-cutting doc since this blocks EVERY service's Docker build, not just deployment-api:
      [issues/utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md](utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md).
      Part (1) of this todo (live re-verification of `active/` convergence) stays open and is now ALSO gated on that
      doc's Todo 1 (recreate the trigger) — re-verification cannot succeed until a fresh UTL base image actually
      publishes with `4773a3fd` in it, deployment-api rebuilds against it, and a new revision deploys. — **RE-DISPATCHED
      2026-07-25 (slot 2, backend_engineer)**: re-checked the gate chain. Trigger recreation (Todo 1 of the sibling doc)
      is DONE (`unified-trading-library-prod` exists + correctly configured). But manually verifying it hit a NEW real
      bug — unescaped `$VERSION`/`$IMAGE_TAG` comment references in `cloudbuild.yaml` trip Cloud Build's substitution
      validator — fixed + shipped (`unified-trading-library@44922ad1`+`71dcf0f4`), full details + the fleet-wide 15-repo
      instance of the same bug class in
      [issues/cloudbuild_yaml_unescaped_substitution_comments_fleet_wide_2026_07_25.md](cloudbuild_yaml_unescaped_substitution_comments_fleet_wide_2026_07_25.md).
      Both fixes are on `live-defi-rollout` only — `git show origin/main:cloudbuild.yaml` still shows the old unescaped
      content; 2 promote PRs open (`unified-trading-library` #644 for `44922ad1`, #645 for `71dcf0f4`), both
      `mergeable_state: blocked` pending required checks. Part (1)'s full chain (promote lands → fresh UTL base image
      publishes → deployment-api rebuilds → new Cloud Run revision → ≥2 reap-tick intervals, 900s each, of log
      observation) is genuinely not completable in one dispatch turn. Not attempted further. Next dispatch: re-check
      `gh pr list --repo IggyIkenna/unified-trading-library --state open` for #644/#645 merged to `main`; once merged,
      confirm a fresh UTL base image publishes
      (`gcloud artifacts docker images list     .../unified-trading-library --sort-by="~UPDATE_TIME"` shows an
      `UPDATE_TIME` after the merge), THEN proceed with the original re-verification steps (direct image extraction +
      log watch) exactly as scoped above.

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
  [issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md](/plans/archive/issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md)
  (P0, BACKEND) with a concrete reproduction + 4 candidate fix approaches. Did NOT flip this plan's original `[REVIEW]`
  checkbox — leaving it as-is with its existing partial-pass note, now additionally pointing at the new issue doc. No
  code changes made this session (review-only pass).
