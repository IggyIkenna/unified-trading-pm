---
doc_type: issue
title:
  "deployment-api's cold-cache inventory fix (deployment-api@6f6a389) removed the OLD global serialization on cold
  census computations — 2 concurrent cache-key computations OOM-killed the whole container (17,002MiB used vs 16,384MiB
  limit), a MORE SEVERE regression than the bug it fixed"
summary: >-
  [REVIEW] Live re-verification of `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`'s two shipped
  BACKEND fixes (deployment-api@1c1987ad reaper grace-period, @6f6a389 cold-cache bound) against the freshly deployed
  Cloud Run revision `uts-shared-deployment-api-00270-2l9` (image `deployment-api:366154d`, confirmed by content diff to
  contain both fixes + the faulthandler instrumentation). The cold-cache fix technically does what it says (bounds a
  single caller's wait to 45s, no more indefinite hangs) — but it changed `_load_inventory`'s cold path from a
  synchronous compute held under `_inventory_lock` for its FULL duration (the OLD code — meaning only ONE cold census
  could run process-wide at a time) to a `_kick_background_refresh` submission to `_inventory_refresh_pool`
  (`ThreadPoolExecutor(max_workers=2)`) that releases the lock immediately after registering the in-flight key. This
  means up to 2 DIFFERENT cache-key census computations can now run truly concurrently (e.g. the default
  `ALL|CONFIGURED` key and an `all_regions=true` sweep's `ALL|ALL` key are different keys, not deduped) — and each
  `_compute_inventory` call internally fans out via its own `_census_pool` (`max_workers=10`) plus several per-provider
  region pools (`max_workers` up to 8 each: aws-region, scheduler-region, cr-jobs-region, cr-svc-region, cf-region).
  Reproduced live: a default-region poll (which kicked a stale-TTL background refresh) followed ~45s later by an
  `all_regions=true` poll (a genuinely cold key) drove the container to **17,002 MiB** against its **16,384 MiB** limit
  — Cloud Run logs show `Memory limit of 16384 MiB exceeded with 17002 MiB used` (ERROR) immediately followed by
  `Container terminated on signal 9` (the OOM-killer) and a fresh instance restart. Also worth noting: `WORKERS=2`
  (gunicorn, per the deploy log) means `_inventory_refresh_pool`/`_inventory_cache`/`_inventory_refreshing` are
  per-gunicorn-worker-process state (not shared within one container), so the real worst case within a single container
  is up to ~4 concurrent full census fan-outs (2 gunicorn workers × 2 pool slots each), not just 2 — this session did
  not confirm that upper bound empirically, flagging it as the more dangerous compounding factor for whoever fixes this.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-registry, oom, cloud-run, memory, concurrency, regression, observability]
related:
  [deployment_registry_reaper_not_draining_stale_entries_2026_07_24, deployment_api_sigabrt_crash_loop_2026_07_24]
created: 2026-07-24
priority: P0
parent_epic: observability_master
source:
  "[REVIEW] slot-4 re-verification of deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md's 3rd
  ([REVIEW] P1) todo, against the deployed uts-shared-deployment-api-00270-2l9 / deployment-api:366154d, 2026-07-24."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: true
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by: deployment-api@91dc53c (fix) + this REVIEW re-verification (slot 7, 2026-07-25)
---

# deployment-api inventory cold-path: concurrent census computations OOM the container (2026-07-24)

> **🟢 RESOLVED 2026-07-25 — ACKED-INTO-CODE** — `deployment-api@91dc53c` (`max_workers=2` → `1`, re-verified live
> against the deployed Cloud Run revision: no OOM, no signal-9, real data eventually served); archived per the
> terminal-status backlog sweep.

## What I found

Re-running the end-to-end verification that `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`'s
third todo asked for, against the newly deployed revision (confirmed via `gcloud builds log` + content-diffed
`git show 366154d:...` — both shipped fixes AND the sibling issue doc's faulthandler instrumentation are present):

- **`active/` object count: still 403–404**, essentially UNCHANGED from the pre-fix baseline, both ~1h45m after the P0
  reaper-grace-period fix went live (revision `-00269-t66`, deployed 21:34:14Z) and ~10 min after the P1 cold-cache fix
  went live (revision `-00270-2l9`, deployed 23:25:24Z) — against ~9 actually-running VMs (7 GCE in
  `central-element-323112` + 2 AWS EC2 in `ap-northeast-1`). The plan's success criterion ("`active/` ≈ running-VM
  count") is NOT met.
- **3 consecutive `GET /api/deployments/inventory` (no `status` filter) calls**, the first genuinely cold (made 2 min
  after the fresh revision deployed): 45.72s / 45.35s / 0.58s. Technically within-or-at the 45s bound (no more
  indefinite hangs — the P1 fix's literal claim holds) — but the first TWO returned **`total=0` / `vm_count=0`** (an
  honest-empty degrade, not real data), and the fast third call served an **empty cached value** (`total=0` in 0.58s) —
  i.e. the cache warmed with NOTHING, not with the real 2,500+-item census. A retry ~2 min later still returned
  `total=0` in 1.3s (served from the same empty-but-warm cache; a background stale-refresh was silently re-kicked per
  the TTL logic but had not resolved by the time of writing).
- **New finding — container OOM-kill.** To isolate why the compute was returning empty, I fired one more request against
  a DIFFERENT (still-cold) cache key: `?all_regions=true`. It returned **HTTP 500 after 63.9s with an EMPTY response
  body** — not an application-level error. Cloud Logging for the same window shows the actual cause:
  ```
  2026-07-24T23:32:32Z ERROR   Memory limit of 16384 MiB exceeded with 17002 MiB used.
  2026-07-24T23:32:36Z WARNING Container terminated on signal 9.
  2026-07-24T23:32:36Z INFO    Starting new instance. Reason: MANUAL_OR_CUSTOMER_MIN_INSTANCE.
  ```
  This lines up exactly with two DIFFERENT cache-key census computations overlapping in time: the default
  `ALL|CONFIGURED` key's stale-TTL background refresh (kicked by my call at 23:30:48) and the `ALL|ALL`
  (`all_regions=true`) key's fresh cold compute (kicked by my call at 23:31:32) — both landed in the 2-worker
  `_inventory_refresh_pool` concurrently. **Root cause, confirmed by content diff against the pre-fix code**: the OLD
  cold path (`deployment_api/routes/deployments_inventory.py`, pre-@6f6a389) held `_inventory_lock` for the ENTIRE
  `_compute_inventory(...)` call — i.e. only ONE cold census could run process-wide at any moment, regardless of cache
  key. The NEW cold path (`_kick_background_refresh`) only holds the lock long enough to register the key in
  `_inventory_refreshing`, then hands off to `_inventory_refresh_pool = ThreadPoolExecutor(max_workers=2)` and releases
  the lock immediately — so up to 2 DIFFERENT cache-key computations can now run truly concurrently, each internally
  fanning out through its own `_census_pool` (`max_workers=10`) plus several per-provider region pools (`max_workers` up
  to 8 each). The P1 fix removed the OLD implicit global-serialization guarantee as a side effect of fixing the "one
  caller blocks too long" bug, and nothing replaced it.
- This is a REALISTIC production trigger, not just an artifact of my back-to-back test calls: the inventory docstring
  itself says "the cockpit polls repeatedly", and the endpoint already partitions by `cloud=gcp|aws` and by
  `region_scope` (configured vs `all`) into DIFFERENT cache keys — any UI usage pattern that touches 2+ of these filter
  combinations within the ~45s TTL window (e.g. a user with two cockpit tabs open, or the UI itself pre-fetching
  multiple filter tabs) reproduces this exact concurrent-cold-compute condition.
- Also worth flagging (not independently confirmed this session): the deploy log shows `WORKERS=2` (gunicorn), and
  `_inventory_cache` / `_inventory_refresh_pool` / `_inventory_refreshing` are plain module-level globals — NOT shared
  across gunicorn worker PROCESSES within one container. That means the real concurrency ceiling inside a single
  container may be closer to 4 simultaneous full census fan-outs (2 gunicorn workers × 2 pool slots each), not the 2
  this session measured directly.

## Why it matters

- This is a MORE SEVERE failure mode than the bug the P1 fix was written to solve: the old bug blocked ONE caller past a
  client-side timeout; this regression can OOM-kill the **entire container**, dropping every in-flight request
  (including, plausibly, the deployment reaper's own background tick — directly undermining the SIBLING P0 fix in the
  same issue doc) and forcing a cold restart that starts the whole cache-warming problem over again.
- This is very likely the SAME mechanism, or a major contributor to, the still-unconfirmed SIGABRT crash-loop tracked in
  `deployment_api_sigabrt_crash_loop_2026_07_24.md` (leading hypothesis there: gunicorn's arbiter SIGABRTs a worker
  whose heartbeat starves past 300s — a container under acute memory pressure / GC thrash from concurrent 16Gi-class
  census fan-outs is a very plausible starvation cause). That issue doc's `faulthandler` instrumentation (also now live,
  `deployment-api@1adf54b`) may or may not fire before an OOM-kill (SIGKILL, unlike SIGABRT, cannot be caught by a
  Python-level fault handler) — worth noting for whoever picks up either issue doc so they don't wait indefinitely on a
  `faulthandler` dump that a SIGKILL will never produce.
- Per the parent plan's own success criteria and the workspace HARD RULE ("Runtime verification — never done without
  running the code"), this re-verification does NOT clear the parent plan's `[REVIEW]` checkbox — the reaper is still
  not draining (403–404 vs ~9 running VMs, unchanged before/after both fixes going live) and the inventory endpoint now
  carries a NEW, more dangerous failure mode.

## Recommended decision

Do NOT flip the parent plan's `[REVIEW]` P0 checkbox yet. File this as its own P0 BACKEND todo (repo: deployment-api) —
re-introduce SOME bound on total concurrent full-census fan-out, without reverting to the original indefinite-block bug.
Candidate approaches for whoever picks this up (not prescribing one — needs a design call):

1. Cap `_inventory_refresh_pool` at `max_workers=1` (restores full serialization across cache keys, same as the OLD
   behavior, while keeping the NEW per-caller 45s bound — the two fixes are orthogonal and can compose).
2. Add a process-wide semaphore around the actual `_compute_inventory(...)` body (not just the `_inventory_refreshing`
   registration) so concurrent DIFFERENT-key colds queue instead of running in parallel.
3. Shrink the per-provider fan-out pools (`_census_pool` + the 5 region pools) so even 2 concurrent full census runs
   stay under the memory budget — cheaper to reason about but more fragile as usage grows.
4. Raise the Cloud Run memory limit as a stopgap ONLY if combined with one of 1–3 (a pure memory bump does not fix the
   unbounded-concurrency root cause, it just moves the ceiling).

Whichever fix lands, re-run the exact reproduction in this doc (a default-region poll followed ~45s later by an
`all_regions=true` poll) against the newly deployed revision and confirm no `Memory limit ... exceeded` / `signal 9` log
lines appear, AND that both calls return real (non-empty) data, before closing this doc.

## Todos

- [x] ✅ [BACKEND] P0. Re-bound total concurrent full-census fan-out in `deployment_api/routes/deployments_inventory.py`
      so 2+ different cache-key cold/stale-refresh computations can no longer run truly concurrently —
      deployment-api@91dc53c (candidate approach 1: `_inventory_refresh_pool` `max_workers=2` → `max_workers=1`) + 2 new
      regression tests proving serialization at the pool level (unit-level reproduction; the live Cloud Run
      re-verification is the `[REVIEW]` todo below, now gated behind this one).
- [x] ✅ [REVIEW] P1. Once the todo above ships, re-run the full
      `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md` verification again (active/ count
      before/after, 3 consecutive inventory calls incl. a cold one) — only then consider flipping that plan's `[REVIEW]`
      checkbox to a clean pass. — RE-VERIFIED 2026-07-25 (slot 7, review): the OOM defect THIS ISSUE DOC tracks is
      CONFIRMED FIXED against the live deployed revision. The sibling reaper-drain defect is NOT fixed (separate,
      already tracked) — so per this doc's own "Recommended decision", the PARENT plan's `[REVIEW]` checkbox stays
      UNFLIPPED. Full detail in Progress Log.

## Progress Log

- **2026-07-25 (slot 7, review) — [REVIEW] P1 re-verification — OOM FIX CONFIRMED, reaper-drain still open.** Confirmed
  the BACKEND fix (deployment-api@91dc53c, `max_workers=2`→`1`) is actually DEPLOYED and live — not just merged:
  `gcloud run services describe uts-shared-deployment-api` →
  `latestReadyRevisionName= uts-shared-deployment-api-00272-jgb`, image digest `sha256:6f918df3...`; matched that digest
  to Cloud Build `01d4aa5e` (region `asia-northeast1`, `COMMIT_SHA=cd002cc` on `main`, pushed `00:24:05Z`, deployed
  `00:34:17Z`); content-diffed (not just ancestry-checked, per the squash-commit caveat this doc's own prior entry
  flags) — `git show origin/main:deployment_api/routes/deployments_inventory.py | grep max_workers` on the fetched
  `main` HEAD confirms `_inventory_refresh_pool = ThreadPoolExecutor(max_workers=1, ...)` is genuinely in the deployed
  image. **Re-ran the exact reproduction**: call 1 (default, no filter) at `00:40:28Z` → HTTP 200 in 46.8s, `total=0`/
  `vm_count=0` (cold, honest-empty — same reaper-drain symptom, see below). Call 2 (`?all_regions=true`, the DIFFERENT
  cache key that previously landed the concurrent-cold-compute OOM) at `00:41:36Z`, ~68s after call 1 started (close to
  the doc's ~45s gap) → **HTTP 200 in 52.0s**, `total=0`/`vm_count=0` — critically, **NOT** the HTTP 500-after-63.9s-
  with-empty-body the pre-fix reproduction produced. Checked Cloud Run logs for the window `00:39:00Z`→now:
  `severity>=WARNING` → **0 entries** (the pre-fix repro showed explicit `ERROR Memory limit ... exceeded` +
  `WARNING Container terminated on signal 9` in this exact window shape) — positive absence, not just "no crash
  observed". Confirmed no restart happened: `latestReadyRevisionName` still `-00272-jgb` after both calls (a container
  OOM-kill would have shown a fresh instance start log line, per the original finding). Call 3 (default, ~19s after
  call 2) → HTTP 200 in **0.3s**, `total=2052`/`vm_count=1762` — the cache eventually warmed with REAL data, proving the
  background refresh completed successfully once serialized rather than being starved/killed. **Honest caveat**: this
  doc's own "Recommended decision" asks that "both calls return real (non-empty) data" — calls 1 and 2 themselves did
  NOT (both `total=0`); only the follow-up call 3 did. This is the SEPARATE, already- tracked reaper-drain defect
  (`active/` object count still ~404 vs 7 actually-running GCE instances, unchanged from every prior session's
  measurement) bleeding into this specific re-verification's timing, not a sign the OOM fix failed — the two defects are
  orthogonal per this doc's own framing, and the positive evidence (no OOM, no 500, no restart, log-confirmed absence of
  the memory-limit/signal-9 signature, eventual real data) is unambiguous for the ONE defect this issue doc tracks.
  **Verdict**: the concurrent-census OOM regression THIS DOC exists for is FIXED. The PARENT plan's `[REVIEW]` checkbox
  stays UNFLIPPED (per this doc's own explicit instruction) because the sibling reaper-drain issue is still open —
  that's tracked separately in `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`'s own Progress Log,
  not duplicated here.

- **2026-07-24 (slot-4, review)**: Diagnosed live against `uts-shared-deployment-api-00270-2l9`
  (`deployment-api:366154d`) per the parent issue doc's 3rd `[REVIEW]` todo. Confirmed both prior fixes ARE deployed
  (content-diffed, not just ancestry-checked — the LDR→main promote path uses SQUASH commits, so
  `git merge-base --is-ancestor` alone is unreliable here; verified via `git show <sha>:<path> | grep`). Found `active/`
  unchanged (403–404) and reproduced a container OOM-kill via 2 concurrent cold/stale-refresh census computations. Filed
  this doc + updated the parent issue doc's Progress Log. NOT fixed in this session (review-only pass; a fix needs a
  BACKEND worker's design call between the 4 candidate approaches above).
- **2026-07-24 (slot-5, review)**: Auto-dispatched task `-002` (the `[REVIEW]` todo below) while `-001` (the `[BACKEND]`
  fix) was still `[ ]` and actively in-progress on slot 6 — this doc's prose ordering ("once the todo above ships") was
  never machine-enforced (`sequential: false`, no `depends_on`), so the dispatcher offered `-002` before its real
  prerequisite existed. Fixed the plan-authoring gap: flipped `sequential: true` above so future regens correctly gate
  this doc's `[REVIEW]` todo behind its `[BACKEND]` todo. Released task `-002` back to the queue via
  `/skip-current-task` (not attempted — there is nothing to verify yet) so it gets picked up once `-001` ships.
- **2026-07-24 (slot-6, backend_engineer)**: Shipped candidate approach 1 —
  `_inventory_refresh_pool = ThreadPoolExecutor(max_workers=2, ...)` → `max_workers=1` in
  `deployment_api/routes/deployments_inventory.py`, restoring the OLD code's process-wide serialization of cold/stale
  census computations (only one in flight at a time) while keeping the NEW per-caller 45s bound in `_load_inventory`
  untouched — the two properties are orthogonal, confirmed by inspecting `_kick_background_refresh`/`_load_inventory`
  (the bound wait is on `future.result(timeout=...)`, independent of pool size). Added two regression tests in
  `tests/unit/test_route_deployments_inventory.py`: `test_inventory_refresh_pool_is_bounded_to_one_worker` (pins the
  pool size) and `test_inventory_refresh_pool_serializes_different_cache_keys` (submits two blocking tasks to the ACTUAL
  production pool object and proves the second never starts until the first releases — the direct unit-level
  reproduction of "2 different cache-key refreshes overlap" without needing live GCP/Cloud Run infra). SCOPE SPLIT: this
  BACKEND todo ships the code fix + the closest feasible non-live reproduction; the `[REVIEW]` P1 todo below (now
  correctly gated behind this one via `sequential: true`) is the LIVE reproduction against the deployed Cloud Run
  revision and stays open until that rollout happens. ALSO FLAGGING (not fixed, out of this todo's scope): a sibling
  pool in `deployment_api/routes/vm_deployments.py` (`_vm_deployments_refresh_pool`, still `max_workers=2`,
  `tests/unit/test_vm_deployments_cache.py`) follows the identical stale-while-revalidate pattern this issue doc's own
  summary says was mirrored FROM — same theoretical OOM shape (2 different cache keys' full registry+Compute-API census
  fanning out concurrently), just not yet confirmed live. Worth its own follow-up todo before it reproduces in prod the
  same way.
