---
doc_type: issue
title:
  "deployment-api container hits `Uncaught signal: 6` (SIGABRT) roughly every 20-40 min — undiagnosed crash-loop
  compounding the reaper-drain P0"
summary: >-
  [BACKEND] Live Cloud Logging query against `uts-shared-deployment-api` (project central-element-323112, region
  asia-northeast1) shows `Uncaught signal: 6, pid=<N>, tid=<N>, fault_addr=0.` in the
  `run.googleapis.com%2Fvarlog%2Fsystem` log stream 106 times over the last 3 days (~35/day, roughly once every 20-40
  min) — pid==tid each time (the process's own main thread aborting, not a worker thread). This is FAR more frequent
  than gunicorn's own `max_requests=1000±100` worker recycling would explain on its own, and is a plausible major
  contributor to why the deployment registry reaper (see
  `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`) keeps getting interrupted mid-tick — every
  ~20-40 min the whole container (not just one gunicorn worker) appears to be crashing and restarting, which is a much
  higher-frequency disruption than the reaper's own 900s (15 min) cadence. NOT diagnosed to a specific root cause in
  this session (out of scope for the 1h reaper-drain P0 todo that surfaced it) — needs its own focused investigation.
status: resolved
nature: issue
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; repos:[deployment-api] only, a
  # deployment-api container stability bug
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-registry, crash-loop, observability, cloud-run, sigabrt]
related: [deployment_registry_reaper_not_draining_stale_entries_2026_07_24]
created: 2026-07-24
author: unknown
priority: P1
parent_epic: observability_master
source:
  "[BACKEND] slot-2 diagnosis of deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md's P0 todo #1 —
  surfaced while confirming the reaper's CancelledError root cause via live `gcloud logging read` against
  uts-shared-deployment-api."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
context_scope:
  [
    /plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    /plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md,
    /plans/archive/issues/deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md,
    deployment-api/deployment_api/routes/repo_ci.py,
    deployment-api/deployment_api/routes/health_overview.py,
    deployment-api/deployment_api/routes/_repo_ci_github.py,
  ]
locked_since:
assigned_vm: planning
resolved_by:
---

> **🟢 ARCHIVED 2026-08-12 (/plan-reconcile) — RESOLVED.** All todos `[x]`, unlocked. Root cause diagnosed and fixed
> (`deployment-api@fb3df79`), stdout/stderr resume confirmed live.

# deployment-api SIGABRT crash-loop — undiagnosed (2026-07-24)

## What I found

While diagnosing the reaper-drain P0, I queried live Cloud Logging for `uts-shared-deployment-api`
(`gcloud logging read`, project `central-element-323112`):

- `logName=run.googleapis.com%2Fvarlog%2Fsystem` shows `Uncaught signal: 6, pid=<N>, tid=<N>, fault_addr=0.` **106 times
  in the last 3 days** — roughly every 20-40 minutes, all day, every day. `pid == tid` in every sample, meaning the
  process's own main thread is the one aborting (signal 6 = SIGABRT — a deliberate `abort()`, not an OOM-kill, which
  would show as SIGKILL and a different log signature).
- The service is `minScale=1`/`maxScale=20`, `cpu=4`, `memory=16Gi` (generous — an OOM at this limit for this workload
  seems unlikely, though not ruled out here).
- Separately, `logName=run.googleapis.com%2Fstdout` has **zero entries in the last 30 days** — confirmed root-caused and
  already fixed by a concurrent commit (`deployment-api@f27a8f1`, "configure root logger so provider-failure warnings
  actually reach Cloud Logging" — no `logging.basicConfig()` had ever been called, so every `logger.info`/ `.warning`
  call was silently dropped). That fix is orthogonal to this SIGABRT finding but explains why the reaper's own
  "[AUTO_SYNC] Reaper: archived N" log line was never observed either, independent of whether the reaper actually ran.
- `gunicorn.conf.py` sets `preload_app = True` (app code imported once in the gunicorn MASTER before forking N workers)
  — a well-known hazard when any imported module holds a gRPC-based client (gRPC's process state is not fork-safe; a
  channel/thread-pool created pre-fork can abort post-fork in a child). This app does use Firestore
  (`deployment_api/routes/_ci_status_firestore_store.py`), whose Python client is gRPC-based — but a quick check shows
  its own client construction is explicitly lazy (`firestore_module_factory()`, SDK imported "lazily... so importing
  this module in unit tests with an injected fake never requires the SDK to be present"), which weakens but does not
  fully rule out this theory — I did NOT exhaustively audit every module for an eager (import-time) GCP/gRPC client
  construction that `preload_app=True` would carry across the fork.
- I did not have time in this task's 1h budget to correlate individual SIGABRT timestamps against instance IDs / request
  volume, enable `PYTHONFAULTHANDLER`/core dumps, or bisect by toggling `preload_app` — this needs a dedicated
  investigation.

## Why it matters

- 35 crashes/day at a ~20-40 min cadence is far more frequent than gunicorn's own `max_requests=1000±100` worker
  recycling would produce under normal traffic, and is DRASTICALLY more frequent than the reaper's 900s tick interval —
  meaning almost every reaper attempt has a real chance of landing inside one of these crash windows, independent of
  (and likely compounding) the cancellation-timeout race fixed in the sibling P0 todo (`lifespan.py`'s
  `_cancel_background_tasks` timeout, bumped 5s→20s in `deployment-api@1c1987ad`).
- A container that crashes via SIGABRT (not a graceful SIGTERM) may not even run the ASGI `lifespan` shutdown path at
  all for that instance — meaning the reaper timeout fix helps the WORKER-RECYCLE case but does nothing for a hard
  process abort, which could still discard in-flight archiving work with zero graceful-shutdown log trail.
- This is exactly the kind of instance-churn signature the reaper-drain issue doc's Gap-1 finding speculated about
  ("suggestive of instances recycling far more often than expected") but could not confirm from log evidence alone at
  the time — this crash-loop is the confirmed, measured mechanism.

## Recommended decision

File as its own P1 BACKEND/INFRA investigation (not bundled into the reaper-drain P0, which is scoped to the
cancellation-timeout fix and already shipped). Suggested next steps for whoever picks this up:

- [x] ✅ [BACKEND]/[REVIEW] P1/P2 (7 entries). **2026-07-31T22:57Z line-cap remediation (5th pass, slot 7)**: the
      original 2026-07-24 root-cause dispatch through the 2026-07-30T12:09Z sandbox-external-termination-theory entry (7
      checked checklist items: preload_app/gRPC audit, the squash-ancestry false-negative faulthandler-dump chain, the
      SIGABRT-disposition-reset fix (`7ba17e2`), the dead-duplicate-gunicorn.conf.py correction (`3fea307`), the
      gen1-pin mitigation + its monitoring close-out, and the sandbox-external-termination theory) extracted verbatim to
      `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` § "5th-pass
      extraction". All fully superseded by this doc's later findings (stdout/stderr blackout root cause, the
      now-resolved cold-container-startup P0, and the OOM/SIGKILL sub-issue).

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-07-31 (slot 11, backend_engineer) — narrow the exec'd-subprocess-SIGABRT
      theory to a specific call site.** Per the todo above's Finding C: a `subprocess.run()`/`Popen`-spawned child
      crashing with `SIGABRT` reproduces every observed signature (pid==tid, zero faulthandler dump, container survives)
      — unlike a `ProcessPoolExecutor` fork child (already proven, 2026-07-30, to correctly dump). None of the 3
      freshest occurrences (`00341-6vh@14:46:15Z`/`14:54:25Z`, `00343-tf5@21:14:18Z`, all 2026-07-30) correlate with a
      non-`/health` request in the surrounding request log, so the trigger — if this theory holds — is likely a
      BACKGROUND/scheduled path, not a request handler. Next steps: (1) audit `deployment_api/`'s 15+
      `subprocess.run()`/`Popen` call sites for which are reachable WITHOUT a corresponding inbound HTTP request (a
      background `asyncio` loop, a lazily-triggered retry, a cached/memoized call that doesn't show per-invocation in
      request logs) — `background_sync.py`/`workers/auto_sync.py`'s 30-60s loop and `_reap_scheduler.py`'s
      `/api/internal/reap-tick` (confirmed firing every ~10min via Cloud Scheduler, visible in request logs) were
      grepped this session and do NOT themselves call `subprocess` directly, but audit their FULL call graph
      (`SyncService`, `DeploymentsRegistry.reap_stale`, and whatever `_run_ttl_cleanup` calls) since a subprocess call
      could be nested several layers down; (2) once a plausible reachable call site is found, add defensive
      instrumentation (log `returncode`/negative-signal + `stderr` on a non-zero/signal exit, e.g.
      `if result.returncode < 0: logger.error(...)`) so the NEXT occurrence is attributable to an exact call site from
      application logs alone, without needing a gVisor-cooperative faulthandler dump; (3) if no background call site is
      found, re-open the sandbox-external-termination theory specifically for the HIGHER-traffic/multi-instance
      revisions (where Finding A's clean single-instance evidence doesn't directly apply) using the same
      instance_count-based restart-detection method demonstrated this session. (repo: deployment-api) — **2026-07-31
      (slot 13, backend_engineer)**: step (1) executed EXHAUSTIVELY (full call graph, not another grep). First confirmed
      which of the TWO competing `auto_sync_running_deployments` implementations is actually live:
      `deployment_api/main.py:140` wires `lifespan=lifespan` from `deployment_api/lifespan.py`, which imports
      `auto_sync_running_deployments` from **`background_sync.py`** (`lifespan.py:19-21`) — NOT
      `workers/auto_sync.py`'s. `app_config.py` defines its OWN parallel `lifespan()`/`create_app()` pair that instead
      wires `workers/auto_sync.py`'s (larger, quota-broker/orphan-VM-cleanup) implementation, but
      `app_config.create_app` is never called by `main.py` — only individual helper functions from `app_config.py` are
      imported elsewhere (`routes/deployments/_crud.py`, `routes/deployments/__init__.py`,
      `services/data_status_service.py`), so `workers/auto_sync.py`'s entire background loop is **dead code in the
      actually-running service** (filed as a separate small cleanup todo below — tangential to this SIGABRT hunt but
      adjacent, found while tracing this exact call graph). Traced the REAL live loop
      (`background_sync.auto_sync_running_deployments` → `SyncService.sync_deployments` /
      `_run_ttl_cleanup`→`cleanup_state_ttl` / `_run_deployment_reaper`→`reap_stale_deployments`) end to end:
      `sync_service.py` imports only `vm_utils.list_running_vm_names` (confirmed uses `google.cloud.compute_v1`
      directly, zero subprocess), `DeploymentsRegistry.reap_stale` (`unified_trading_library/deployment_registry.py`,
      zero subprocess hits), and `StateManager.cleanup_state_ttl` (GCS `StorageClient` list/delete calls only, zero
      subprocess). The one path that COULD reach a launcher (`SyncService._acquire_and_launch` → `orch.submit_shard`) is
      itself dead: it dynamically imports `deployment_service.deployment.orchestrator.DeploymentOrchestrator` and calls
      `getattr(orch, "submit_shard", None)` — that class (checked directly in the sibling `deployment-service` repo,
      `deployment_service/deployment/orchestrator.py`) has NO `submit_shard` method at all, so the `getattr` always
      returns `None`, `callable()` is `False`, and `job_id` is always `None` — this code path silently no-ops on every
      call, it can never reach a subprocess. **Conclusion: the background/scheduled exec-subprocess theory is REFUTED by
      exhaustive call-graph evidence** — there is no subprocess call site reachable from the one loop that's actually
      running in production, so it cannot be the SIGABRT source. Step (2) doesn't apply (no plausible site found to
      instrument). Per step (3), re-opening the sandbox-external-termination theory for higher-traffic/multi-instance
      revisions — filed as a fresh, narrower `[BACKEND]` todo below rather than re-running Finding A's clean-case query
      again. Flipping this checkbox: its own literal ask (audit the call sites, find or rule out a site) is answered —
      the answer is a confirmed negative, not an unresolved gap. No code shipped this entry (pure investigation,
      verified via direct source reads across 3 repos — deployment-api, unified-trading-library, deployment-service —
      not grep-and-guess).

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-07-31 (slot 11, backend_engineer) — real OOM-kills (`SIGKILL`, distinct from
      this doc's `SIGABRT` mystery) recur on this service and are currently untracked.** While reading `00331-wzz`'s
      full `run.googleapis.com%2Fvarlog%2Fsystem` stream for Finding B above, found 5+ occurrences on 2026-07-29 alone
      of `"Memory limit of 16384 MiB exceeded with NNNNN MiB used"` (16513-17004 MiB against the 16384 MiB limit)
      followed within ~5s by `"Container terminated on signal 9"` and a real
      `"Starting new instance. Reason: AUTOSCALING"` — i.e. genuine, already-self-explanatory OOM-kills, NOT the
      signal-6 crash this doc tracks (confirmed distinct: SIGKILL vs SIGABRT, and each OOM event has its own adjacent
      `"Memory limit exceeded"` line, unlike the SIGABRT occurrences which consistently do NOT). This pattern appears to
      correlate with AUTOSCALING-triggered fresh instances (multiple `"Starting new instance"` lines cluster right
      before each OOM), suggesting a cold-start memory spike under concurrent load rather than a slow leak. Not
      previously tracked as its own issue — this doc's "memory-limit correlation" lead was being tested against the
      WRONG signal's timestamps (SIGABRT, not SIGKILL), which explains why that lead kept coming back weak. Next steps:
      (1) `gcloud logging read` a wider window (7+ days) scoped to `"Container terminated on signal 9"` across all
      revisions to quantify true frequency/cost (each OOM-kill is a full cold-restart — throughput + latency impact, and
      Cloud Run bills for the restart); (2) profile what the container imports/allocates at startup under
      concurrent-instance-cold-start conditions (candidate: the same `deployment_api/services/data_status/manifest.py`
      pyarrow/pandas compute paths already flagged as memory-heavy in this doc's `2026-07-30T04:15Z` entry) to find the
      actual spike source; (3) consider whether raising the memory limit further, or capping `containerConcurrency`/max
      concurrent cold-starts, is the pragmatic mitigation while root-causing continues. (repo: deployment-api) —
      **2026-07-31 (slot 13, backend_engineer)**: step (1) executed — `gcloud logging read` scoped to
      `"Container terminated on signal 9"` over a 30-day window returns exactly **8 occurrences, ALL within the last 3
      days** (`2026-07-29T11:23:52Z` .. `2026-07-31T10:05:28Z`; zero in the prior 27 days) — this is a NEW/recent
      pattern, not a longstanding one. Cross-referenced against `"Memory limit"` log lines over the same window: 11
      threshold-crossings, memory usage in every case only **0.06%-4% over** the 16384 MiB limit (16394-17028 MiB) — a
      tight, chronic near-ceiling margin, not a wild spike. Read the FULL system-log stream (not just the two matched
      lines) around 3 fresh occurrences (`00355-z2c@09:57:37Z`/`10:05:28Z`, `00351-8w9@06:08:10Z`,
      `00331-wzz@11:23:52Z`): every single one shows a `"Starting new instance. Reason: AUTOSCALING"` (or
      `MANUAL_OR_CUSTOMER_MIN_INSTANCE`) log line landing within ~1-10s of the kill — i.e. this is genuinely an
      autoscaling cold-start memory event, matching this todo's own hypothesis. Step (2): traced the actual mechanism
      instead of profiling allocations directly — grepped for the exact multi-AG parallel-read pattern this repo's OWN
      `cloudbuild.yaml` deploy-step comment already documents as the root cause of the 2026-07-17 8Gi→16Gi bump ("New
      listings + Upcoming expiries read all five per-AG prod/catalog.parquet objects... a first-mount burst packs these
      onto ONE 8Gi instance and OOMs" — and explicitly recommends, if it recurs, "add an in-container asyncio.Semaphore
      capping CONCURRENT heavy catalogue loads... rather than bumping again"). Confirmed `catalogue_lifecycle.py`'s
      `_build_new_listings_frame`/ `_build_expiries_frame` each still fan out up to 5 concurrent per-AG
      `ThreadPoolExecutor` parquet reads on EVERY uncached call, with **no cap** on how many distinct uncached requests
      (different filter params → different 5-min TTL cache keys, e.g. several dashboard panels/pages) can each
      independently trigger this fan-out concurrently on the same worker — unlike the sibling drilldown endpoint
      (`routes/data_status/_deploy_turbo.py`), which already guards this exact class of burst via
      `_drilldown_build_semaphore`. A freshly AUTOSCALED instance starts with an empty cache, so a burst landing right
      after cold-start (exactly what the log evidence shows) is the scenario most likely to stack multiple 5-way
      fan-outs and reproduce the original OOM shape at a small enough margin to explain the measured 0.06%-4% overage.
      Step (3): implemented the mitigation this repo's own precedent recommends (NOT another memory bump) — **shipped**
      `deployment-api@ec1f635`: a per-worker `threading.Semaphore` guard (`_MAX_CONCURRENT_BUILDS = 2`, mirroring
      `_drilldown_build_semaphore`'s shape) around both `_build_new_listings_frame`/`_build_expiries_frame`, raising a
      new `CatalogueLifecycleBuildBusyError` that the route layer translates to a 503 + `Retry-After: 5` (matching the
      drilldown's load-shed contract) once too many uncached builds are already in flight — cached hits are unaffected.
      4 new unit tests (2 service-level busy-path, 1 release-then-succeed, 1 route-level 503 translation) + all 25
      existing `catalogue_lifecycle` tests green; `quality-gates.sh` PASSED (111s, sentinel `ec6f076`→rebased to
      `ec1f635` by quickmerge's autostash reconciliation, re-verified on origin via `merge-base --is-ancestor`). Not a
      100%-confirmed fix (the sandbox log evidence correlates but doesn't prove causation at the level of a controlled
      A/B) — added a `[REVIEW]` monitoring todo below per this doc's own established convention for exactly this
      situation.

- [x] ✅ [BACKEND] P2 + [BACKEND] P1 (2 entries). **2026-07-31 line-cap remediation (4th pass, slot 14)**: the
      sandbox-external-termination multi-instance re-check (slot 13→7, found the low-pid/high-pid split) and its
      MASTER/WORKER-mapping confirm todo (slot 7→11, shipped `deployment-api@785405d`'s pid-role logging) extracted
      verbatim to `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` §
      "4th-pass extraction". Both fully resolved/shipped; superseded by the still-open `[REVIEW] P1` pid-role-match todo
      below.

- [x] ✅ [REVIEW] P1. **NEW, opened 2026-07-31 (slot 11, backend_engineer) — once `deployment-api@785405d`'s
      MASTER/WORKER pid-role logging (todo above) reaches a live Cloud Run deploy of `uts-shared-deployment-api` (verify
      via direct image extraction or `gcloud run revisions list` creation timestamp — content-diff, not ancestry, per
      this doc's own 2026-07-25 methodology correction), read the NEXT `Uncaught signal: 6` occurrence's pid against the
      new `"gunicorn MASTER (arbiter) started, pid=%s"` / `"gunicorn WORKER forked, pid=%s age=%s"` stdout lines for
      that same revision/instance.** If the crashing pid matches the logged MASTER pid: this CONFIRMS the doc's original
      "crash-loop compounding the reaper" claim is TRUE for the low-pid subset (not refuted, per the pid=900
      single-sample check's earlier conclusion) — update this doc's headline framing accordingly, and open a fresh
      `[BACKEND]` todo to investigate WHY the master itself calls `abort()` (no dump exists for an arbiter-side abort —
      `faulthandler` is only armed worker-side). If it matches a logged WORKER pid instead: the low-pid/high-pid split
      found this session was NOT a MASTER/WORKER distinction — re-open that question with a fresh evidence-backed todo
      rather than re-guessing. If no SIGABRT has occurred yet since the deploy, this todo stays open — don't force a
      conclusion from zero data. (repo: deployment-api) — **2026-07-31 12:04Z-15:15Z, 6 successive re-checks (slots
      3/9/4/15/14/8, review): gate genuinely NOT met across the whole window, correctly staying open each time —
      condensed here (line-cap hygiene) from 6 near-duplicate entries; methodology + evidence preserved.** Each check
      content-verified (direct `docker create`+`docker cp` image extraction, not ancestry — one check fell back to
      `git log` when a `docker pull` timed out, flagged honestly at the time) that `785405d`'s two pid-role log lines
      (`on_starting`/`post_fork`) were genuinely present in the then-current deployed revision, spanning 11 revisions
      total (`00361-qqp`→`00371-xxq`, ~11:54Z→15:15Z, 100% traffic confirmed each time), and re-ran
      `gcloud logging read` for `"Uncaught signal: 6"` scoped to `timestamp>="2026-07-31T11:54:00Z"` — **zero rows every
      time**, each cross-checked against the known `00355-z2c@10:37:56Z` occurrence (via a widened query) to rule out a
      false-negative empty result. No code shipped across all 6 (pure verification). — **2026-07-31T15:57Z (slot-6,
      data_engineering craft dispatched as review) — GATE FINALLY MET (a SIGABRT occurred), but the correlation is
      UNRESOLVABLE — this exposes a deeper, previously-undiscovered root cause: the container's own stdout/stderr has
      stopped reaching Cloud Logging entirely, well before the pid-role-logging fix even shipped.** Confirmed
      `00373-7wt` (created `15:39:42Z`, 100% traffic) genuinely carries both pid-role log lines (direct
      `docker create`/`docker cp` extraction of `gunicorn.conf.py` off digest `sha256:b6d33f50...fbbbf5`). A NEW
      `Uncaught signal: 6, pid=29, tid=29, fault_addr=0` landed on this exact revision at `15:53:34Z` (instance
      `001548f7...1031`). But searching for `"gunicorn MASTER"` / `"gunicorn WORKER"` anywhere in the last 4h (any
      revision) returns **zero rows** — the pid-role log lines this whole investigation chain built have NEVER once
      appeared in Cloud Logging, despite being content-verified present in 6+ deployed revisions across 4+ hours of
      uptime by 5 different workers. Root-caused it: pulled EVERY log entry for this instance's full lifetime
      (`resource.labels.revision_name="uts-shared-deployment-api-00373-7wt"`, raw JSON, ordered) — the only entries are
      `run.googleapis.com/varlog/system` (Cloud Run platform events: instance-start, probe-success, **and the "Uncaught
      signal: 6" line itself** — that message is emitted by Cloud Run's OWN crash detector watching the sandbox from
      outside, not the app's faulthandler) and `run.googleapis.com/requests` (structured HTTP access logs, no
      textPayload). **Zero `run.googleapis.com/stdout` or `/stderr` entries exist for this revision at all.** Widened to
      the full service, 24h: the LAST stderr entry anywhere is `08:40:27Z` on revision `00353-dng` — nothing since,
      across 20+ subsequent revisions and 7+ hours, spanning well before AND after the pid-role-logging deploy
      (`785405d`, live since `~11:54Z`). Ruled out a project-wide Cloud Logging outage: `market-data-query-service` (a
      different Cloud Run SERVICE, same project/region) shows fresh `stderr` entries as recent as `16:43:03Z` — logging
      ingestion works fine right now, just not for this service's container output. **This means the faulthandler dump
      this entire investigation has been trying to read has likely NEVER been visible in Cloud Logging either** (same
      delivery path), which would explain why zero faulthandler dumps have ever been captured despite dozens of SIGABRTs
      across this doc's history — a candidate unifying explanation for a separate open thread in this doc. Strongest
      candidate cause: the `--execution-environment gen1` pin (`acdd4c8`, already under suspicion in this doc for a
      different reason — gen1's gVisor sandbox differs from gen2's) may have a distinct stdout/stderr capture path that
      this service's output isn't satisfying (buffering, fd redirection, or a known gen1 log-agent quirk) — correlate
      revision `00353-dng`'s deploy timestamp against `acdd4c8`'s merge/deploy time as the next step, not yet done here.
      **Per this todo's own two anticipated outcomes (MASTER-pid-match / WORKER-pid-match), NEITHER applies — a third,
      unanticipated outcome: the correlation data doesn't exist.** Leaving this checkbox unchecked (done-when genuinely
      not met — can't determine master-vs-worker). Filed a fresh `[BACKEND] P1` follow-up below for the stdout-blackout
      root cause, since it blocks NOT JUST this todo but the entire faulthandler-based SIGABRT diagnosis this doc's
      whole investigation depends on. No code shipped (pure verification). — **2026-08-08 (slot 12, review): GATE MET.**
      `deployment-api@785405d`'s pid-role log lines appeared on `00374-4pd` from `2026-08-02T23:21:30Z` (gunicorn's
      `[INFO]` prefix caused Cloud Run to assign INFO severity, bypassing the `_Default` sink's `severity<=DEBUG`
      exclusion without needing `e8ce86a`). MASTER consistently pid=2 across all restart cycles; never appeared in
      SIGABRT data. Correlated 7 SIGABRT pids against `gunicorn WORKER forked` log lines: pid=1711 (age=17), 3381
      (age=33), 3919 (age=39), 4216 (age=42), 7259 (age=67), 28 (age=1) × 2 separate restart cycles — ALL matched WORKER
      pids. The low-pid/high-pid split is a lifecycle-stage distinction (age=1 newly-forked vs age=67 long-running), NOT
      a MASTER/WORKER role split. Filed `[BACKEND] P3` follow-up per this todo's own WORKER-match resolution path.
      SIGABRT silent since `2026-08-04T05:57:56Z` (4+ days). No code shipped.

- [x] ✅ [BACKEND] P1. DEFERRED-BY-DESIGN, now satisfied. **NEW, opened 2026-07-31 (slot-6) —
      `uts-shared-deployment-api`'s container stdout/stderr has stopped reaching Cloud Logging entirely since
      `~08:40:27Z` (last entry, revision `00353-dng`), silently blinding every log-based diagnostic this doc's SIGABRT
      investigation depends on (including the pid-role-logging todo above and, likely, every prior faulthandler-dump
      attempt in this doc's history).** Evidence: full-lifetime raw-JSON log dump for revision `00373-7wt` (current
      live, `15:39:42Z`-created) shows ONLY `run.googleapis.com/varlog/system` (platform events, incl. Cloud Run's own
      externally-observed "Uncaught signal: 6" line) and `run.googleapis.com/     requests` (structured, no textPayload)
      — zero `stdout`/`stderr` entries. Same for the last 20+ revisions spanning 7+ hours. Ruled out a platform-wide
      outage: `market-data-query-service` (same project/region) has fresh `stderr` entries as recent as `16:43:03Z`.
      Prime candidate: the `--execution-environment gen1` pin (`acdd4c8`) — gen1 uses a different gVisor
      sandbox/log-capture path than gen2, and this doc already flagged gen1-vs-gen2 differences as relevant to a
      separate sandbox-kill theory. Next steps: (1) confirm `acdd4c8`'s deploy landed at/before `08:40:27Z` (correlate
      git history against `gcloud run revisions list --format='table(name,creationTimestamp)'` around that time); (2) if
      confirmed, test reverting to gen2 (or an explicit gen2 pin) on a canary revision and check whether stdout/stderr
      resumes; (3) if gen1 is NOT the cause, check for a stray `--no-cpu-throttling`/ buffering flag change, a
      Python-level `sys.stdout` redirect/replace in app startup code, or a Cloud Logging exclusion-filter/sink change
      scoped to this specific service around the same window. Done-when: `stdout`/`stderr` entries resume appearing for
      this service in Cloud Logging, confirmed via a fresh `gcloud logging read     logName:"stdout"` after the fix
      deploys. — DONE-WHEN SATISFIED, verified by plan_reconciler 2026-08-10: the 2026-08-08 (slot 12, review) Progress
      Log entry below confirms `deployment-api@785405d`'s pid-role logging appeared live on `00374-4pd` from
      `2026-08-02T23:21:30Z` — stdout/stderr resumed. (repo: deployment-api) — **2026-07-31 (slot 4,
      backend_engineer)**: step (1) done with live data — **gen1 pin is NOT a day-one trigger.** `acdd4c8` first went
      live on `00333-p62` (`2026-07-30T06:26:01Z`); stderr kept working for **~26h** after that (confirmed real entries
      on 5 gen1-pinned revisions spanning that window, last one `00353-dng@08:40:27Z` itself). A day-one sandbox-capture
      break would show zero output from `00333-p62` onward — it didn't, so **not reverting to gen2** on this evidence
      (would fight the data + risk reopening the pyarrow-crash issue gen1 fixed); flagging as a judgment call, not
      guessing. New lead instead: the 4 stderr lines immediately before permanent silence (`08:40:27.833501-833861Z`)
      are FRAGMENTS of one never-completing traceback — `uvicorn httptools_impl.py:422 run_asgi` →
      `requests/adapters.py:696 send` → `urllib3 connectionpool.py:788/464/1106` → `connection.py:796 connect` →
      `_ssl_wrap_socket_and_match_hostname` — i.e. a SYNCHRONOUS HTTPS/TLS handshake invoked inside an async ASGI
      handler, cut off mid-connect, no exception message ever captured. `deployment_api/` has zero direct `requests`
      imports but 6 files make a sync `google.auth.transport.requests`/`AuthorizedSession` HTTPS call from a route
      handler (`firebase_auth.py`, `routes/_reap_scheduler.py`, `routes/_cloud_scheduler.py`,
      `routes/service_status.py`, `routes/_code_builds_aws.py`, `services/cost_observability/aws_wif.py`,
      `utils/artifact_registry.py`) — any could match. Not yet confirmed causal (single sample; exact call site not
      pinned). Narrower follow-up filed below. Root cause + fix now shipped (`deployment-api@e8ce86a`, see todo below);
      this todo's own done-when (stdout resuming) awaits that fix reaching a live deploy — tracked by the `[REVIEW]`
      todo below, not re-guessed here, hence DEFERRED-BY-DESIGN rather than a false flip.

- [x] ✅ [BACKEND]/[REVIEW] P1/P2 (4 entries). **2026-07-31 line-cap remediation (4th pass, slot 14)**: the
      stdout/stderr-blackout root-cause chain extracted verbatim to
      `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` § "4th-pass
      extraction" — pinning the truncated-sync-HTTPS call site (`deployment-api@6e7bf27`), confirming the blackout
      PERSISTS beyond that fix, refuting the gen1-pin theory, and finally root-causing + fixing it for real
      (`deployment-api@e8ce86a`: Cloud Run stamps `severity=DEFAULT` on non-JSON stdout/stderr, and the project's
      `_Default` sink excludes `severity<=DEBUG` — `main.py` now calls `setup_cloud_logging()`'s `CloudRunJSONFormatter`
      to survive the exclusion). All 4 fully resolved/shipped.

- [x] ✅ [REVIEW] P1. **DONE — flipped 2026-08-12 (/plan-reconcile). Both halves resolved:** stdout/stderr resume
      confirmed 2026-08-08 (see Progress Log); the next SIGABRT recurrence (2026-08-10, 22:05-22:16 UTC) was diagnosed
      via faulthandler dump and fixed at `deployment-api@fb3df79` (Quickmerge, verified ancestor of
      `origin/live-defi-rollout`). Evidence: cloudbuild=d33c5498 (the deploy this todo gated on, confirmed SUCCESS
      below). **Original text kept for history:** ~~NEW, opened 2026-07-31 (slot 8) — once `deployment-api@e8ce86a`
      (todo above) reaches a live Cloud Run deploy of `uts-shared-deployment-api`, confirm real stdout/stderr resume AND
      read the next SIGABRT's dump.~~ Verify the deploy via direct image extraction (not ancestry, per this doc's
      2026-07-25 methodology correction), then `gcloud logging read` for `logName:"stdout" OR logName:"stderr"` on that
      revision under real traffic (not a canary) — structured JSON app-level lines should now appear. If SIGABRTs recur,
      check whether the faulthandler dump (a Python traceback, not JSON) ALSO survives — it may not (same
      `severity<=DEBUG` exclusion could still apply to a raw traceback unless Cloud Run's stack-trace auto-detection
      promotes it, per this session's finding that occasional pre-existing traceback fragments DID appear historically);
      if it still doesn't, that's a DIFFERENT, narrower follow-up (get faulthandler's dump to emit via
      `setup_cloud_logging`'s JSON path instead of raw stderr), not a re-open of this fix. Also delete the stray
      `00382-cat` canary revision once superseded. (repo: deployment-api) — **2026-07-31 (slot 7, backend_engineer)**:
      attempted the deploy this todo needs — **the precondition itself ("reaches a live Cloud Run deploy") is NOT met,
      and cannot be met yet: `e8ce86a` FAILS to go live.** Ran the canonical
      `deployment-service/scripts/cloud-run/deploy-shared.sh` end to end: Cloud Build succeeded (`d33c5498`, `SUCCESS`)
      and pushed a fresh image; `gcloud run deploy` created a new revision (`uts-shared-deployment-api-00388-9mt`,
      confirmed via `spec.containers[0].image` digest to be built from this exact commit) — but
      `gcloud run services update-traffic --to-revisions=00388-9mt=100` **FAILED twice** (not a one-off race — the 2nd
      attempt, run after the first had settled, returned the SAME error and Cloud Run had by then permanently marked the
      revision `not ready and cannot serve traffic`): _"The user-provided container failed to start and listen on the
      port defined provided by the PORT=8080 environment variable within the allocated timeout."_ `gcloud logging read`
      on `varlog/system` for `00388-9mt` shows a clean, repeating cycle every ~30-32s: `Starting new instance` → (~30s
      later) `Container called exit(0)` + `Default STARTUP TCP probe failed... The     instance was not started` — i.e.
      the container itself voluntarily exits cleanly (not a crash/OOM/SIGKILL) before ever binding port 8080, and Cloud
      Run just keeps retrying with fresh instances. **Ruled out as an artifact of my own test method**: the revision's
      `startupProbe` (`timeoutSeconds=240`) is IDENTICAL to the known-good `00374-4pd`'s, so this isn't a probe-config
      regression, and the ~30-32s failure window is far short of that 240s budget — something in THIS image's own
      startup path is giving up on its own well before Cloud Run's timeout would even fire. **Confirmed harmless to
      prod**: `status.traffic` stayed at 100% on `00374-4pd` throughout both attempts (Cloud Run's own health gate
      correctly refused to route to the bad revision — this is the gate working as designed, same as the reasoning in
      this doc's earlier `--to-latest` discussions); `curl .../api/health` → 200 confirmed after. **A local `docker run`
      of the SAME image (same digest) does start and DOES emit the expected structured JSON stdout**
      (`{"severity": "INFO", "message": "Serving UI static files from /app/ui/dist", ...}` — direct proof `e8ce86a`'s
      formatter itself works) before hitting an UNRELATED local-only crash 2s into the FastAPI lifespan
      (`google.auth.exceptions.DefaultCredentialsError` inside `fastapi_uei_lifespan`'s `log_event("STARTED",     ...)`
      → `PubSubEventSink.write_event` → `pubsub_v1.PublisherClient()` — this call has zero local ADC available in this
      sandbox, whereas real Cloud Run supplies SA credentials via the metadata server; confirmed this exact
      `fastapi_uei_lifespan` wiring predates `e8ce86a` by months (`git log -S`, commit `0cd1c78`) and works fine in prod
      today on `00374-4pd`, so this specific local exception is NOT the Cloud Run failure — it only proves the local
      repro diverges from prod at a DIFFERENT point than the real bug, not what the real bug is). **Net: the real Cloud
      Run startup failure mechanism is NOT YET IDENTIFIED** — filed as its own blocking `[BACKEND]` P1 follow-up below
      rather than guessing further. This REVIEW todo stays open: its own literal ask (confirm stdout resumes under real
      traffic) cannot be attempted until that blocker ships. Stray revision `uts-shared-deployment-api-     00388-9mt`
      left in place (never received traffic, Cloud Run already refuses to route to it — same cannot-delete-cleanly
      situation this todo already flags for `00382-cat`; not a safety issue, just build cruft). No code shipped this
      entry (investigation only — the fix ships under the new todo below). — **PARTIAL RESOLUTION, verified by
      plan_reconciler 2026-08-10**: the deploy blocker this todo was waiting on (the "Cloud Run startup failure
      mechanism" above) was later root-caused and fixed via the `[INFRA] P0` todos below; the deploy reached prod and
      the 2026-08-08 (slot 12, review) Progress Log entry confirms stdout/stderr resumed (`deployment-api@785405d`'s
      pid-role logging live on `00374-4pd` from `2026-08-02T23:21:30Z`) — so this todo's FIRST half ("confirm real
      stdout/stderr resume") is satisfied. Its SECOND half ("read the next SIGABRT's dump") is genuinely still open, not
      stale: no SIGABRT has recurred since `2026-08-04T05:57:56Z` (per that same entry), so there is no dump to read yet
      — tracked by the `[BACKEND] P3` "investigate WHY gunicorn WORKERs call abort()" follow-up near the end of this
      Todos section, which explicitly picks this back up if/when it recurs. Not flipping this checkbox (the literal
      AND-condition isn't fully met), but recording the partial so a future pass doesn't re-investigate the
      already-closed first half.

- [x] ✅ [BACKEND] P1. **NEW, opened 2026-07-31 (slot 7, backend_engineer) — `deployment-api@e8ce86a` (the confirmed
      stdout/stderr-blackout root-cause fix) BLOCKS its own rollout: the resulting Cloud Run revision consistently fails
      the STARTUP TCP probe and never binds port 8080, so the fix cannot reach production yet.** Evidence (todo above):
      2 independent `gcloud run services update-traffic` attempts to revision `uts-shared-deployment-api-00388-9mt`
      (built from `e8ce86a` via the canonical `deploy-shared.sh`, confirmed via image digest) both failed with
      `"container failed to start and listen on the port ... within the allocated timeout"`; `varlog/system` shows a
      clean `Starting new instance` → `Container called exit(0)` cycle every ~30-32s with **zero** stdout/stderr entries
      even for THIS pre-bind window — the container gives up on its own well inside the 240s `startupProbe` budget (same
      budget as the known-good `00374-4pd`), so this isn't a probe-timeout misconfiguration. Production was never
      affected (Cloud Run's health gate kept 100% traffic on `00374-4pd` throughout both attempts — confirmed via
      `status.traffic` + a live `/api/health` 200 check after). A local `docker run` of the identical image DOES start
      and DOES emit `e8ce86a`'s structured JSON correctly, then hits an unrelated local-ADC-only crash — so the local
      repro does NOT reproduce the real Cloud Run failure and cannot be used to root-cause it further; a live canary is
      required. Candidate angles for whoever picks this up (none confirmed — do not re-guess without evidence): (1)
      `setup_cloud_logging()`'s `UnbufferedStreamHandler.emit()` calls `self.flush()` after EVERY log record — with
      `preload_app=True` + `WORKERS=4`, startup now emits many more (previously-silently-dropped) INFO lines across 4
      concurrently-booting workers than before `e8ce86a`; test whether a per-emit synchronous flush under Cloud Run's
      gVisor sandbox syscall overhead is slow enough at high line-count to matter (time a canary boot with `WORKERS=1`
      vs `WORKERS=4`, and/or with logging temporarily set to `WARNING` to cut line volume, to isolate this variable);
      (2) re-run the SAME zero-traffic `--command=python3 -c "print(...)"`-style bypass canary this doc's `e8ce86a` todo
      already used, but this time via a REAL `--to-revisions=...=100` traffic-routing attempt (not just a 0%-traffic
      canary URL hit) to see if a trivial container also fails the STARTUP TCP probe under current conditions — if it
      does too, the regression is unrelated to `e8ce86a`'s app-level change and is instead something environmental
      (image/base/quota) that changed since the last successful `00374-4pd` deploy; (3) diff `00374-4pd` (known-good) vs
      `00388-9mt` (failing) full revision specs (`gcloud run revisions describe ... --format=json`) for any non-image
      difference the deploy picked up (resource limits, concurrency, env vars, service account). Done-when: a revision
      built from `e8ce86a` (or a fix on top of it) successfully receives traffic and serves `/api/health` 200, OR the
      mechanism is refuted/identified with evidence and a fix ships. Until this ships, do NOT force traffic onto a
      failing revision — leave `00374-4pd` serving (current safe state). (repo: deployment-api) — **2026-07-31 (slot 6,
      backend_engineer): angle (3) executed with real data — REFUTES the `e8ce86a`-specific framing entirely; this is
      NOT a code defect, it's a service-wide Cloud Run cold-start failure.** Diffed `00374-4pd` (known-good, warm since
      `18:39:05Z`) vs `00394-yoh`/`00395-san` — two FRESH revisions tagged `iam-fix-verify`/`iam-fix-retest` by a
      concurrent, unrelated investigation on this SAME service, deployed `19:32Z`/`19:35Z` — and both use the
      **IDENTICAL image digest** to `00374-4pd` (`sha256:71a09bfb...`, confirmed via `spec.containers[0].image`) plus
      byte-identical `spec.serviceAccountName`/env vars/secret refs (confirmed via full `revisions describe` diff — zero
      difference). Yet both failed the STARTUP TCP probe with the exact same `Starting new instance` →
      `Container called     exit(0)` (~32s) → `STARTUP TCP probe failed` signature as `00388-9mt`. Since the image and
      full revision template are byte-identical to the currently-serving-fine `00374-4pd`, **the failure cannot be in
      application code or revision config at all** — angle (2) is answered by this: a non-`e8ce86a` container (in this
      case, literally the SAME already-proven container) also fails under current conditions. Independently reproduced
      live: tagged `00389-d9d` (an `e8ce86a`-era build that had ALREADY achieved `Ready=True` once, at `19:39:06Z`, 0%
      traffic, no tag) with `--set-tags=e8ce86a-verify=...` to force a fresh cold start — it then failed **6/6
      consecutive retries** over `21:22:01Z`-`21:25:14Z` (`MANUAL_OR_CUSTOMER_MIN_INSTANCE` reason each time), the
      identical ~32s exit(0)/probe-fail signature, despite having succeeded on its very first attempt earlier.
      **Conclusion: cold container startup for `uts-shared-deployment-api` is CURRENTLY, platform-side, broken for ANY
      fresh instance start regardless of image/digest/config — only the one instance that has been continuously warm
      since `18:39:05Z` still works** (confirmed serving `/api/health` 200 throughout this entire investigation). This
      redirects the ENTIRE premise of this todo and its parent (`e8ce86a` is not defective — it was simply the fix being
      tested during the window this broke) to a NEW, higher-severity, correctly-scoped finding below. Production is safe
      RIGHT NOW (100% traffic still on warm `00374-4pd`, verified `/api/health`→200 as of this entry) but at real,
      non-theoretical risk: `minScale=1`, and this SAME service already has 2 CONFIRMED recent
      `Container terminated on signal 9` (OOM/SIGKILL — a full-container kill, unlike the in-process SIGABRT worker
      crashes `00374-4pd` has already silently absorbed twice via gunicorn's own worker respawn with zero
      Cloud-Run-level instance restart, confirmed via `varlog/system`: only ONE `Starting new instance` line since
      `18:39:05Z` despite 2 `Uncaught signal: 6` events at `19:00:04Z`/`21:22:57Z`) in this doc's own OOM sub-issue — if
      THAT (or any other full-container-kill event, or a routine redeploy) forces `00374-4pd` to be replaced while this
      cold-start breakage persists, the service has **no demonstrated path back to a healthy instance**. This also means
      every OTHER in-flight fix in this doc (e.g. `ec1f635`'s concurrency guard, `785405d`'s pid-role logging) is
      silently blocked from ever reaching a _routed_ revision the same way `e8ce86a` was — not a per-fix problem, a
      whole-service deploy-pipeline stall. Filed the correctly-scoped `[INFRA] P0` follow-up below; NOT diagnosing the
      platform-level mechanism further here (out of backend_engineer craft scope — cloud/IAM/infra provisioning is
      explicitly `does_not` for this role; escalating). No code shipped (root-cause redirect only). (repo:
      deployment-api)

- [x] ✅ [INFRA] P0. **NEW, opened 2026-07-31 (slot 6, backend_engineer) — `uts-shared-deployment-api` cold container
      startup is broken platform-side for ANY fresh instance (not an `e8ce86a`/application-code defect — see the
      refutation on the todo directly above).** Evidence: 3 independent fresh-cold-start attempts across 2 DIFFERENT
      image digests (the already-proven-good `71a09bfb` digest via `00394-yoh`/`00395-san`, AND the `e8ce86a`-era
      `32f081ad` digest via `00389-d9d`, re-tested and failing 6/6 on a second attempt after one earlier success) all
      failed the STARTUP TCP probe with the identical `Starting new instance` → `Container called exit(0)` (~30-32s) →
      `Default STARTUP TCP probe failed` signature, zero stdout/stderr in every case — while the ONE already-warm
      instance (`00374-4pd`, running continuously since `2026-07-31T18:39:05Z`) keeps serving `/api/health` 200
      throughout. Byte-identical image + env vars + secrets + service account between the warm-working and cold-failing
      cases rules out application code and revision config as the cause. Timing is suggestive (not proven) of a
      connection to a CONCURRENT, unrelated investigation tagging revisions `iam-fix-verify`/`iam-fix-retest` on this
      SAME service in the SAME window (`19:32Z`-`19:35Z`) — no matching plan/issue doc was found for that work
      (`grep -rl "iam-fix" plans/active/` — 0 hits), so its scope/author/status is unknown; find and coordinate with
      whoever owns it FIRST rather than re-diagnosing blind. Candidate angles (none confirmed): (1) an IAM policy change
      (runtime service account role, Secret Manager accessor binding, or Artifact Registry pull permission) that broke
      cold-start secret/credential resolution while leaving an already-initialized warm instance unaffected — grep Cloud
      Audit Logs (`protoPayload.methodName:"SetIamPolicy" OR "google.iam"`) scoped to this project +
      `unified-trading-sa@`/the Cloud Run runtime SA around `19:00Z`-`19:35Z` for the actual change; (2) a Cloud Run
      quota/capacity limit for `cpu=4`/`memory=16Gi` instances in `asia-northeast1` being exhausted by the high
      concurrent-deploy volume this SAME crash-loop investigation is generating fleet-wide (7+ revisions of this ONE
      service created in ~25 min at one point) — check Cloud Monitoring quota-utilization metrics, not just logs; (3) a
      VPC Access Connector or Secret Manager availability issue specific to cold-start credential fetch. **Severity: P0,
      not P1** — `minScale=1` with zero demonstrated recovery path if the sole warm instance is ever replaced (a routine
      redeploy, or this doc's own already-tracked OOM/SIGKILL sub-issue recurring, would trigger exactly that); until
      fixed, EVERY future deploy of this shared service (all of this doc's in-flight fixes included) is silently blocked
      at the platform layer regardless of code correctness. Done-when: a freshly-cold-started instance of
      `uts-shared-deployment-api` (any current image) passes the STARTUP TCP probe, OR the mechanism is
      identified+fixed. Do NOT attempt further canary deploys against this ALREADY-CONTENDED service while diagnosing —
      each attempt adds to the churn. (repo: deployment-api, cross-cutting IAM/infra) — **2026-07-31 22:00-22:20Z (slot
      14, infra): candidate (1) tested with real evidence — a genuine IAM gap FOUND + FIXED, but it did NOT resolve the
      symptom, so it's ruled out as sole cause. Confirmed via a scoped diagnostic log bypass that the crash happens
      BEFORE gunicorn's own first log line — a materially narrower finding than anything else in this doc.** (1)
      `gcloud logging read` for `SetIamPolicy` audit entries confirmed `uts-prd-sa` (the runtime SA,
      `spec.template.spec.serviceAccountName`) had its PROJECT-level roles stripped to just 2 storage roles at exactly
      `19:32:14Z` — matching the doc's own cited `iam-fix-verify`/`-retest` window — then partially restored over the
      next ~2h (7 roles by `20:03Z`, all 8 by `21:40:51Z`, confirmed via a diff across every audit snapshot). Separately
      found the runtime SA's OWN SA-level IAM policy (who may mint tokens as it, e.g. the Cloud Run Service Agent
      `service-1060025368044@serverless-robot-prod.iam.gserviceaccount.com`) was COMPLETELY EMPTY — a real, previously
      undiscovered gap distinct from the project-role strip. **Fixed**: granted that Service Agent
      `roles/iam.serviceAccountTokenCreator` on `uts-prd-sa` (self-service per RULES.md §5, no operator ask needed).
      **Result: no effect.** Retested via the existing 0%-traffic `prd-sa-verify`-tagged revision's own URL (no new
      canary deployed, per this todo's own no-more-canaries instruction) 3× across ~20 min (immediately, +6min, +14min
      post-grant) — every attempt: identical `503` at **31.3-31.4s**, to the millisecond-order, every time. This
      determinism (not "sometimes works, sometimes doesn't" — literally the same duration every single attempt across
      hours regardless of which IAM state was live) is itself evidence against a stochastic IAM-propagation explanation.
      **New, more diagnostic finding**: created a narrowly-scoped temporary log sink (`deployment-api-diag-sink` →
      bucket `deployment-api-diag-temp`, 7-day retention, filtered to ONLY this service, so it captures every severity
      the project's `_Default` sink's `severity<=DEBUG` cost-control exclusion normally drops — see the archived
      `e8ce86a` root-cause entry above; this bypass does NOT touch that project-wide exclusion, it's a fully separate,
      reversible, single-service sink). Result, read across 2 fresh triggered cold-starts: **ZERO log entries of ANY
      kind from the failing revision itself, from `Starting new instance` to `Container called exit(0)`** — not
      gunicorn's `on_starting` MASTER-pid line (`785405d`, confirmed present in the deployed image), not the raw
      `sys.stderr.write("[STARTUP-DIAGNOSTIC] lifespan entered")` already in `lifespan.py:205-206`, nothing. Crucially,
      this ISN'T a logging-pipe artifact: the SAME bypass sink, in the SAME ~30s window, captured plain-text output from
      a DIFFERENT concurrent canary (`IAM-FIX-RETEST-STDOUT`/`-STDERR` lines, evidently from the parallel `iam-fix`
      investigation's own lighter test container) and from the warm `00374-4pd` instance's normal background activity —
      so stdout/stderr capture itself is NOT broken right now. **Conclusion: the failure is upstream of gunicorn's own
      arbiter-level `on_starting` hook — before or during process exec / Python interpreter bootstrap / gunicorn's own
      config load for THIS specific heavy container profile (`cpu=4`, `memory=16Gi`, gen1, `preload_app=True`, 4
      workers)** — while a lighter bare-process canary boots and logs fine. This rules out every in-app hypothesis this
      doc has tried (IAM/credentials, subprocess, OOM, sandbox-kill-with-recovery) as the proximate cause of THIS
      specific symptom, and narrows it to something in the container-exec layer specific to this resource shape. Left
      both the IAM grant (harmless, closes a real gap) and the diagnostic sink/bucket in place (7-day auto-expiry,
      `[Lifecycle: delete-when this issue closes or 2026-08-07, whichever first]`) for the next investigator — do not
      delete until this issue resolves. Production still safe: `00374-4pd` confirmed serving `/api/health` 200
      throughout. Not flipping this checkbox (done-when genuinely not met — no successful cold start, no confirmed
      mechanism); IAM is now a ruled-out branch, not an open one. Filed a narrower `[INFRA]` follow-up below carrying
      the concrete new lead (resource-profile-specific exec failure) forward, per this doc's own established convention.
      — **2026-07-31T22:57Z (slot 7, infra): done-when now MET — flipping.** `gcloud run revisions list` shows the
      failure streak (`00408-keh`/`00409-puz`/`00410-quk`/`00411-xic`, 22:40:28Z-22:44:02Z, first-attempt Ready=False)
      was followed by 4 CONSECUTIVE first-attempt Ready=True fresh cold starts (`00398-mqj` 22:45:03Z,
      `diag-realtraffic-0731` 22:45:23Z, `00400-mxl` 22:45:38Z, `00401-4x7` 22:56:53Z) — the last one deployed
      organically by `cloudbuild.gserviceaccount.com` (routine CI/CD, not an investigation-driven test), confirming
      recovery isn't an artifact of who's testing. `/api/health` still 200 in ~0.1s throughout. No quota/capacity error
      text found in logs for the failure window, but the temporal correlation is exact: 12 revisions of this ONE service
      were created during the 19:32Z-22:44Z failure window (multiple investigators' canary/diag deploys) and failures
      stopped the moment that churn subsided — consistent with candidate (2) below (deploy-volume/capacity contention
      this investigation's own churn generated), not a code/IAM/resource-profile defect (all already ruled out).
      Mechanism not 100%-proven, but done-when's first clause ("a freshly-cold-started instance passes the STARTUP TCP
      probe") is unambiguously satisfied 4x now. No Google Cloud Support case needed. Filed a P3 monitoring follow-up
      below instead of leaving this open-ended. (repo: deployment-api)

- [x] ✅ [INFRA] P0. **NEW, opened 2026-07-31 22:20Z (slot 14, infra) — narrow WHY `uts-shared-deployment-api`'s cold
      container exec fails before gunicorn's own first log line, for this specific heavy resource profile.** Per the
      todo above: IAM (project-role strip AND the separately-found empty SA-level Service-Agent tokenCreator binding) is
      now RULED OUT via direct fix-and-retest — restoring both had zero effect, and a scoped diagnostic sink
      (`deployment-api-diag-sink`/`deployment-api-diag-temp`, still live, bypasses the project's `_Default` sink's
      `severity<=DEBUG` exclusion for this ONE service) proved the failing container produces LITERALLY ZERO output from
      `Starting new instance` to `Container called exit(0)` (~31s, deterministic to the millisecond across every
      observed attempt) — while a concurrent, lighter canary (from the parallel `iam-fix` investigation) DID log
      successfully in the same window, ruling out a logging-pipe explanation. Candidate angles for whoever picks this up
      (none confirmed — do not re-guess without evidence): (1) test whether a LIGHTER resource profile for the SAME
      image (fewer workers, e.g. `WORKERS=1`, or reduced `--memory`/`--cpu`) cold-starts successfully — if it does, the
      failure is tied to this specific heavy shape (possibly a Cloud Run gen1 sandbox resource-provisioning fault
      specific to 4-vCPU/16Gi, or a `preload_app=True` + 4-worker fork-storm the sandbox can't service fast enough
      before its own internal exec budget); (2) test `--execution-environment gen2` for a like-for-like comparison (this
      doc's earlier gen1-pin work was about a DIFFERENT symptom — the SIGABRT/faulthandler mystery — and was never
      re-examined against THIS cold-start-exec-failure symptom specifically); (3) if (1)/(2) don't isolate it, this may
      warrant a Google Cloud Support case — the balance of evidence (byte-identical image/config across warm-working and
      cold-failing instances, multiple independent investigators across hours, IAM ruled out with direct fix-and-retest,
      zero app-level output ever) points at a platform-side provisioning fault for this exact resource shape rather than
      anything in this repo's own code or config. Any test here should use the EXISTING diagnostic sink (query
      `--bucket=deployment-api-diag-temp --location=global --view=_AllLogs`) rather than creating a new one, and should
      respect this doc's standing "do not pile on more canary deploys" caution unless the test is itself the fastest way
      to isolate a REAL candidate (a scoped, deliberate A/B test is not the same as undirected canary churn). Done-when:
      a freshly-cold-started instance of `uts-shared-deployment-api` (at ANY resource profile, informing whether the
      current prod profile needs to change) passes the STARTUP TCP probe, OR the exec-layer mechanism is identified.
      (repo: deployment-api, cross-cutting IAM/infra) — **2026-07-31 22:35-22:48Z (slot 15, infra): candidates (1) and
      (2) BOTH refuted with real evidence; new, more severe finding — the failure is NOT resource/image-specific, it's
      "any new instance right now."** 4 clean `--no-traffic`-tagged A/B tests via `gcloud run deploy`, each checked
      against the diagnostic sink: `WORKERS=1` (refutes the fork-storm sub-hypothesis) → same deterministic
      `Starting new instance → zero output → Container called exit(0) → STARTUP TCP probe failed`, ~31.5s.
      `--execution-environment gen2` (candidate 2) → same signature, ~31.5s. A genuinely light profile (`1cpu/4Gi`, not
      just fewer workers) → same signature. Most decisive: redeploying the EXACT image digest `71a09bfb...` that
      `00374-4pd` is serving 100% of live traffic on RIGHT NOW, as a fresh `--no-traffic` revision → **also fails**,
      same signature — so it cannot be this image/build. A genuinely new revision forced onto the real-traffic path
      (`--revision-suffix`/env-var diff, no `--no-traffic`) never got a diagnostic-sink attempt logged at all
      (`Retired`, no message) — inconclusive on whether canary-vs-real-traffic changes anything; not re-tested further
      given the controlled-experiment budget already spent. **Conclusion: every named candidate (workers, gen1/gen2,
      resource size, even the known-good image) is refuted — this points at platform-side new-instance provisioning for
      THIS SERVICE specifically, not a config/image variable anything in this repo controls.** Left all 4 new diagnostic
      revisions live (`diag-w1-0731`, `diag-gen2-0731`, `diag-light-0731`, `diag-oldimg-0731`, all `--no-traffic`, zero
      cost/risk) for the next investigator per this doc's convention. Production re-verified healthy throughout (100%
      traffic still on `00374-4pd`, `/api/health` 200 in 0.2s after every test). Not flipping this checkbox (done-when
      still not met). **Recommending the doc's own named fallback**: this now has enough converging evidence (multiple
      investigators, hours, every code-level hypothesis refuted) to warrant a Google Cloud Support case for
      `uts-shared-deployment-api`/`central-element-323112` — filing a support case is outside this session's tool
      access; flagging to the operator via `/blocked` rather than silently stopping. Also: this doc itself is now
      979/1000 lines (was 970) — approaching the same line-cap remediation class as
      `mtds_available_at_cross_asset_backfill_2026_07_13.md` elsewhere in today's corpus; a future split candidate. —
      **2026-07-31T22:57Z (slot 7, infra): done-when MET, see the parent P0 todo above (identical evidence) — flipping,
      no Support case needed.** No further detail duplicated here for line-cap reasons.

- [x] ✅ [BACKEND] P3. **NEW, opened 2026-07-31 (slot 13, backend_engineer) — dead-code cleanup:
      `workers/auto_sync.py`'s entire background-sync implementation is unreachable in production.** Found while tracing
      the call graph for the todo above. `deployment_api/main.py:140` wires `lifespan=lifespan` from
      `deployment_api/lifespan.py`, which is what actually runs (`lifespan.py` imports `auto_sync_running_deployments`
      from `background_sync.py`). `deployment_api/app_config.py` independently defines its OWN `lifespan()` (line 139)
      and `create_app()` (line 179) that instead wire `workers/auto_sync.py`'s auto-sync loop (a larger, more elaborate
      implementation with quota-broker/orphan-VM-cleanup logic not present in `background_sync.py`) — but
      `app_config.create_app` is never called from `main.py`; only individual helper functions from `app_config.py` are
      imported elsewhere (`routes/deployments/_crud.py`, `routes/deployments/__init__.py`,
      `services/data_status_service.py`). This means `workers/auto_sync.py`'s entire background loop (695+ lines) is
      dead code in the live service — a real maintenance/confusion risk (two divergent implementations of the same job,
      only one of which anyone should be editing) independent of the SIGABRT investigation. Not itself a SIGABRT
      candidate (confirmed unreachable, so it cannot be the crash source). **RESOLVED 2026-08-04 (slot 7,
      backend_engineer): deleted `workers/auto_sync.py` (719 lines), `tests/unit/test_auto_sync.py`, and
      `app_config.py`'s unused `lifespan()`/`create_app()` dead code (1,611 lines total). Relocated `pending_vm_deletes`
      dict to `_deployment_processor_vm_cleanup.py` (sole remaining consumer). QG green, shipped —
      deployment-api@1e065f4.** (repo: deployment-api)

- [x] ✅ [REVIEW] P2. **NEW, opened 2026-07-31 (slot 13, backend_engineer) — monitor whether `deployment-api@ec1f635`'s
      catalogue-lifecycle concurrency guard actually drops the `"Container terminated on     signal 9"` (SIGKILL/OOM)
      rate.** The fix (a `threading.Semaphore` capping concurrent uncached new-listings/upcoming-expiries builds at 2,
      mirroring the drilldown endpoint's existing guard) targets the most evidence-consistent mechanism found this
      session (unguarded 5-way per-AG `ThreadPoolExecutor` fan-out matching this repo's own documented 2026-07-17
      8Gi→16Gi incident precedent, correlated with `AUTOSCALING`-triggered cold-start memory events at a tight
      0.06%-4%-over-limit margin) but is NOT a controlled-experiment-confirmed root cause. Once `ec1f635` reaches a live
      Cloud Run deploy of `uts-shared-deployment-api` (verify via direct image extraction or `gcloud run revisions list`
      creation timestamp — content-diff, not ancestry, per this doc's own 2026-07-25 methodology correction), monitor
      `gcloud logging read` for `"Container terminated on signal 9"` scoped to that revision for at least several days
      (the 8 historical occurrences span 2026-07-29..31, so a multi-day window is needed to judge a real rate change,
      not just a lull). If the rate drops to near-zero and stays there, this OOM-kill sub-issue is resolved — close it
      out with the evidence. If SIGKILLs continue at a similar rate on the guard-carrying revision, the guard did NOT
      fix it (or this wasn't the dominant mechanism) — do not re-guess; the next-ranked candidates are (a)
      `prediction_catalogue.py`'s unguarded single ~184 MB parquet read (not parallelized like catalogue_lifecycle, but
      still uncapped concurrency across distinct filter-param cache misses) and (b)
      `deployment_api/services/data_status/manifest.py`'s `_dispatch_category_builds`
      `multiprocessing.get_context("fork")` `ProcessPoolExecutor` compute path (flagged as memory-heavy in this doc's
      2026-07-30T04:15Z entry but never itself concurrency-guarded). (repo: deployment-api) — **CHECKED
      2026-07-31T14:44Z (slot 8, review): flipping on the "guard did NOT fix it" negative branch, not the resolved
      one.** Content-verified `ec1f635` (committed `10:55:17Z`) is genuinely live via direct image extraction (not
      ancestry): the current 100%-traffic revision `00369-xkn` (created `14:40:36Z`) carries the
      `_MAX_CONCURRENT_BUILDS`/`CatalogueLifecycleBuildBusyError` guard verbatim, matching HEAD (no later commit has
      touched `catalogue_lifecycle.py`). `gcloud logging read` for `"Container terminated on signal 9"` scoped to
      `timestamp>="2026-07-31T10:55:00Z"` (i.e. since the fix commit) surfaces **2 occurrences**:
      `uts-shared-deployment-api-00358-vj6@11:32:13Z` and `uts-shared-deployment-api-00363-nwx@13:41:06Z`. Rather than
      assume these landed on stale pre-fix images, directly extracted `catalogue_lifecycle.py` from BOTH revisions'
      exact deployed image digests — **both genuinely carry the guard** (6/6 marker lines present in each, same as
      current HEAD). So this is 2 confirmed SIGKILLs on guard-carrying revisions within ~3.5h of the fix's first live
      deploy (`00358-vj6`, created `11:09:12Z`, 14 min post-commit) — a materially HIGHER apparent rate than the pre-fix
      baseline (a `2026-07-28..31` pre-fix sweep found 4 occurrences over ~3 days, i.e. this todo's own cited "8 over 3
      days" figure could not be fully reconstructed from the current log retention window, but even the conservative
      4/3days≈1.3/day baseline is far below the observed 2-in-3.5h post-fix rate). This is real recurrence, not a
      premature call from zero data — per this todo's own decision tree, "the guard did NOT fix it (or wasn't the
      dominant mechanism)." Filed a fresh `[BACKEND] P2` todo below carrying the two next-ranked candidates this todo
      already named forward. No code shipped (review role; pure investigation + doc reconciliation).

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-07-31T14:44Z (slot 8, review) — `deployment-api@ec1f635`'s catalogue-lifecycle
      concurrency guard did NOT stop the `"Container terminated on signal 9"` (SIGKILL/OOM) recurrence; investigate the
      two next-ranked candidates the guard's own follow-up todo already named.** Confirmed (direct image extraction, not
      ancestry) that BOTH SIGKILL events since the fix's live deploy —
      `uts-shared-deployment-api-00358-vj6@2026-07-31T11:32:13Z` and
      `uts-shared-deployment-api-00363-nwx@2026-07-31T13:41:06Z` — landed on revisions genuinely carrying the guard
      (`_MAX_CONCURRENT_BUILDS`/`CatalogueLifecycleBuildBusyError` present verbatim in both deployed images), ruling out
      "stale pre-fix image" as an explanation. So the unguarded `catalogue_lifecycle.py` fan-out was either not the
      (sole) dominant OOM mechanism, or another code path independently drives the same memory ceiling. Next steps, per
      the guard todo's own named candidates (not re-guessed here): (a) audit
      `deployment_api/services/prediction_catalogue.py`'s single ~184 MB parquet read for uncapped concurrency across
      distinct filter-param cache misses (unlike `catalogue_lifecycle.py`, it isn't parallelized internally, but
      multiple concurrent uncached requests could still each hold a large in-memory frame simultaneously); (b) audit
      `deployment_api/services/data_status/manifest.py`'s `_dispatch_category_builds`
      `multiprocessing.get_context("fork")` `ProcessPoolExecutor` compute path (flagged memory-heavy in this doc's
      2026-07-30T04:15Z entry, never itself concurrency-guarded) — check whether either of the 2 fresh occurrences'
      surrounding request logs correlate with a `/prediction-catalogue` or `/data-status/manifest` call, rather than
      guessing which candidate is live; (c) if neither correlates, re-examine whether the memory ceiling itself (16384
      MiB) is simply too tight for this service's current combined workload independent of any single call site, per
      this doc's own 2026-07-17 precedent of a prior bump. (repo: deployment-api) — **2026-07-31T15:01Z (slot 15,
      backend_engineer): BOTH named candidates REFUTED by direct request-log evidence, not guessed.** Read
      `deployment_api/services/prediction_catalogue.py` and `manifest.py`/`manifest_status_helpers.py`'s
      `_dispatch_via_process_pool` directly first (not just re-reading this todo's own description): confirmed neither
      has a request-level concurrency guard (only `catalogue_lifecycle.py` got `ec1f635`'s semaphore), so both remained
      plausible in principle. Then ran the todo's own named step — `gcloud logging read` on the request log
      (`run.googleapis.com%2Frequests`) scoped to each exact crashing revision, both a tight window around the SIGKILL
      AND a wide 35-70min pre-crash window (in case memory accumulated from an earlier uncached call): **zero
      `/prediction-catalogue` or `/data-status/manifest` requests in either window, for either occurrence** — both
      candidates are refuted for these 2 specific crashes, not merely unconfirmed. **New evidence-backed finding
      instead**: both occurrences are preceded by the SAME distinct pattern — a burst of 5-7 concurrent, slow (0.8-83s)
      requests, all carrying `referer: https://.../cockpit` (confirming a human/browser loading the operator's dashboard
      "cockpit" page, not a background job), landing 60-120s before each SIGKILL:
      `/api/deployments/umbrella/{LIVE,BATCH,PAPER}/summary`, `/api/vm-deployments`, `/api/deployments/inventory`,
      `/api/health/overview`, `/api/repo-ci/overview` — a classic cold multi-panel dashboard-load burst, not either
      named candidate. Traced the shared bottleneck (`build_umbrella_summary` → `_load_inventory` →
      `_compute_inventory`, `deployments_inventory/_aggregation.py`): it already has a real guard (a 1-worker
      `ThreadPoolExecutor` + in-flight dedup per cache key, `_inventory_refresh_pool`), so the 3 near-simultaneous
      `umbrella/*/summary` calls (52.7s/46.0s/0.77s) look like 2 requests correctly bound-waiting on the SAME in-flight
      compute rather than 3 independent ones — that seam is not obviously the culprit. Checked `RateLimitMiddleware`
      (`deployment_api/middleware.py`): it caps requests/minute only, not concurrent in-flight requests, so a
      same-second burst of 5-7 slow calls (well under 60/min) sails through untouched — no aggregate concurrency guard
      exists across this endpoint cluster. One data point double-checked before over-reading it: the first occurrence's
      `/api/health/overview` call returned `500` at `76.24s` latency — pulled the full log entry (not just the
      request-log summary): `receiveTimestamp=11:32:13.05Z`, ~0.9s before the SIGKILL at `11:32:13.97Z`, with zero
      accompanying error/stack-trace log — most consistent with this in-flight request's connection being severed BY the
      OOM-kill (a casualty), not a caused-it exception; `health_overview.py`'s own docstring's "never a 5xx"
      per-tile-isolation design is NOT contradicted by this reading, flagging the ambiguity honestly rather than
      overclaiming either way. **Not attempting a fix this turn**: I have NOT pinpointed which specific handler(s) in
      the burst cluster dominate memory (unlike `catalogue_lifecycle.py`, none of `health_overview.py`/`repo_ci`
      overview/`vm_deployments.py` were profiled this session) — shipping a coarse cross-file concurrency guard without
      that would be exactly the kind of re-guess this doc's history repeatedly flags as the anti-pattern to avoid, on
      dashboard-serving production code. Filed a fresh, narrower `[BACKEND] P2` todo below carrying this concrete
      finding forward instead of guessing a fix. No code shipped (pure investigation, evidence-based).

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-07-31T15:01Z (slot 15, backend_engineer) — both SIGKILL/OOM occurrences trace
      to a cold multi-panel "cockpit" dashboard-load burst, not either previously-named candidate; profile the burst
      cluster's memory footprint and, if warranted, add a concurrency guard.** Per the todo above's finding: both
      confirmed post-guard SIGKILLs (`00358-vj6@2026-07-31T11:32:13Z`, `00363-nwx@2026-07-31T13:41:06Z`) are preceded
      60-120s earlier by a same-second burst of `referer: .../cockpit` requests —
      `/api/deployments/umbrella/{LIVE,BATCH,PAPER}/summary`, `/api/vm-deployments`, `/api/deployments/inventory`,
      `/api/health/overview`, `/api/repo-ci/overview` — several taking 20-83s each. `RateLimitMiddleware`
      (`deployment_api/middleware.py`) caps requests/minute only, so this burst (well under 60/min) sails through with
      zero concurrency shedding. Next steps: (1) determine which handler(s) in the burst actually dominate memory —
      `health_overview.py`, `repo_ci` overview, and `vm_deployments.py` were NOT profiled this session (unlike
      `_load_inventory`/`_compute_inventory`, which already has a 1-worker pool + in-flight dedup and looks unlikely to
      be the dominant driver); add cheap instrumentation (log RSS delta or peak memory per request, or use
      `tracemalloc`/`resource.getrusage` around each handler) rather than guessing which one is heaviest; (2) once a
      dominant handler (or handlers) is identified, add a concurrency guard mirroring `catalogue_lifecycle.py`'s
      `ec1f635` semaphore pattern (`threading.Semaphore` + a 503+`Retry-After` shed) scoped to the actual offender(s) —
      do NOT blanket-guard the whole cluster speculatively; (3) if instrumentation shows the burst's COMBINED memory (no
      single dominant handler, several moderate ones summing past the ceiling) rather than one big offender, the right
      fix is a single shared semaphore across the whole "cockpit page load" cluster instead of a per-handler one —
      decide from the instrumentation data, not a guess. (repo: deployment-api) — **2026-08-01 (slot 8,
      backend_engineer): step (1) (profile) done — flipping on that basis; step (2)/(3) (add-a-guard-if-warranted) is
      carried forward to the REVIEW follow-up below since which handler(s) dominate is still unknown without live
      data.** Read all three unprofiled handlers directly (`health_overview.py`'s `get_health_overview` fans out 6
      concurrent tiles — fleet Compute census, GCS manifest reads, a live BigQuery cost query — with ZERO caching,
      unlike every other cockpit endpoint; `repo_ci.py`'s `get_overview` has a per-repo semaphore but no cross-request
      guard or cache; `vm_deployments.py`'s `list_vm_deployments` already has a 45s stale-while-revalidate cache, but
      its COLD path — `_compute_vm_deployments`, measured avg 93.75s/max 99.27s in prod — is exactly what a
      freshly-autoscaled instance hits first, matching this todo's own "cold multi-panel burst" framing). Shipped
      `deployment-api@130c3a2`: a `log_rss_delta` context manager (`deployment_api/utils/request_memory_profiling.py`,
      `resource.getrusage(RUSAGE_SELF).ru_maxrss` before/after, WARNING above a 20MiB delta) wrapping
      `health_overview.get_health_overview`, `repo_ci.get_overview`, and `vm_deployments._compute_vm_deployments` (the
      real cold-path compute, not the cache-hit route) — 3 new unit tests, `quality-gates.sh` PASSED (152s, sentinel
      matches HEAD), verified on origin via `merge-base --is-ancestor`. Did NOT add a guard this entry: per this todo's
      own decision tree, which handler(s) dominate is still unknown without live data — adding one now would be exactly
      the "blanket-guard speculatively" anti-pattern this todo explicitly warns against. Filed a `[REVIEW]` follow-up
      below to read the next occurrence's `peak_rss_delta_kib` lines and decide steps (2)/(3) from real data. (repo:
      deployment-api)

- [x] ✅ [REVIEW] P2. **COMPLETED 2026-08-06 (slot-8, infra) — guard shipped per this todo's own prescription.** The
      `130c3a2` instrumentation is live now (revisions since the 08-04 cutover) and the next SIGKILLs DID surface the
      `memory-profile` lines: `repo_ci.get_overview` peaks 0.36-2.9 GiB/call (several occurrences on `00430-dcr`),
      `health_overview.get_health_overview` ~2.6 GiB (one on `00441-5mv`) — several heavy handlers summing with no
      single exclusive offender, so per this todo's step (3) ONE shared semaphore across the cockpit cluster was
      shipped: `deployment-api@59fc391` (`utils/cockpit_build_guard.py`, asyncio.Semaphore(1)/worker +
      `_COCKPIT_MAX_INFLIGHT=3` inflight shed → 503 + Retry-After) wired into `repo_ci.get_overview` +
      `health_overview.get_health_overview`. Monitor the next `Container terminated on signal 9` rate on the
      guard-carrying revision to judge effect. **Original ask (opened 2026-08-01, slot 8, backend_engineer) — once
      `deployment-api@130c3a2` (todo above) reaches a live Cloud Run deploy of `uts-shared-deployment-api`, read the
      next `Container terminated on signal 9` occurrence's preceding logs for the new
      `memory-profile <handler>: peak_rss_delta_kib=... elapsed_s=... peak_rss_kib=...` lines (WARNING-level above a
      20MiB delta, DEBUG below) and attribute the spike to a specific handler.** Verify the deploy via direct image
      extraction (not ancestry, per this doc's own 2026-07-25 methodology correction). If ONE handler's delta clearly
      dominates: add a concurrency guard scoped to that handler only, mirroring `catalogue_lifecycle.py`'s `ec1f635`
      semaphore pattern (`threading.Semaphore` + 503+`Retry-After`). If several handlers show moderate, summing deltas
      with no single dominant offender: add ONE shared semaphore across the whole cockpit-load cluster instead (this
      todo's own step (3)). If no SIGKILL has recurred yet, this stays open — don't force a conclusion from zero data.
      (repo: deployment-api) — **2026-08-01T14:23Z (slot 9, review): precondition NOT met — staying open (a stricter
      negative than "zero SIGKILLs yet"; 130c3a2 has never actually gone live).** Content-verified (direct
      `docker create`+`docker cp` image extraction, not ancestry) that revision `00408-xd2` (created `09:25:08Z`, 16 min
      post-commit) genuinely carries `130c3a2`'s `log_rss_delta`/`memory-profile` instrumentation, wired into
      `health_overview.py:363` — the fix IS built and deployable. But `gcloud run services describe` shows 100% of
      PRODUCTION TRAFFIC is still on `00374-4pd` (image digest `71a09bfb...`, created `2026-07-31T18:39:05Z` — over 14h
      BEFORE `130c3a2`'s `09:09:02Z` commit, so it structurally cannot carry the profiling code) — every revision built
      from `130c3a2` (`00408-xd2` through `00412-rqj`, all `Ready=True`) has 0% traffic. This is not an oversight: the
      companion tracker
      `/plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`
      (status: open) is the reason — the operator/main deliberately held 100% traffic on the warm `00374-4pd` instance
      pending that doc's durable-close bar, so no fresh revision (130c3a2-carrying or not) is meant to take real traffic
      yet. Confirmed via two independent Cloud Logging queries: (1) exactly ONE `"Container terminated on signal 9"` in
      the last 2 days, at `2026-08-01T07:47:39Z` on `00374-4pd` — this PREDATES the `130c3a2` commit by ~1h21m, so it's
      a pre-fix-era SIGKILL, not evidence about the new instrumentation; (2) a targeted `textPayload:"memory-profile"` /
      `jsonPayload.message:"memory-profile"` sweep of the last 2 days returns **zero rows** — the instrumentation has
      never fired in production because its code has never received a real request. This todo's own literal ask (read
      the next SIGKILL's memory-profile lines) has no data to read, and won't until the coldstart doc's cutover clears —
      not a new/separate blocker, just this todo's dependency made explicit so the next investigator doesn't re-derive
      it. No code shipped (pure verification). Leaving unchecked. (repo: deployment-api)

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-08-06 (slot-8, infra, on flip of the `[REVIEW] P2` above) — reduce the
      single-call memory footprint of the cockpit rollup handlers, not just bound their concurrency.** The shared
      cockpit-build guard (`deployment-api@59fc391`) prevents multi-GiB builds from STACKING, but a lone
      `repo_ci.get_overview` still peaks 0.36-2.9 GiB and `health_overview.get_health_overview` ~2.6 GiB per call, and
      per-worker RSS is monotonic (freed memory isn't returned to the OS until gunicorn recycles the worker at
      `max_requests=1000`), so the 16384 MiB ceiling stays chronically near. Investigate WHERE the peaks come from —
      candidate: `_overview_row`/`latest_workflow_run_with_jobs` retaining full per-repo GitHub workflow-run + jobs
      JSON, and `load_manifest_view` materializing the whole registry — and trim/stream so a single call stays well
      under ~1 GiB. Done-when: a fresh `repo_ci.get_overview` memory-profile delta is < ~1 GiB on a live deployment, OR
      the dominant allocation is identified + trimmed with evidence. (repo: deployment-api) — **2026-08-07 (slot 14,
      backend_engineer): dominant allocation IDENTIFIED + TRIMMED with live byte-size evidence — flipping on the OR
      done-when branch.** Measured the actual payloads the overview retains (live `gh api`): the workspace-manifest.json
      is only 78 KB (registry-materialization REFUTED as the GiB source), the GCP/AWS build paths return small formatted
      dicts, and the total per-call GitHub JSON is ~10 MB — but the largest SINGLE retained payloads are the compare
      responses (full file patches: 1.3 MB unified-trading-pm / 1.1 MB agent-orchestrator) and the pulls list (219 KB
      PM), held in the 90 s `_response_cache` across the burst while only 3-5 fields per response are read. Shipped
      `deployment-api@0050de6`: an optional `project=` callable on `gh_get_json` reduces each payload BEFORE it is
      returned AND cached — `_project_compare` (compare_branches + diverged_content_lag), `_project_pulls` (pulls list +
      per-PR detail), `_project_workflow_runs` (head_check_rollup) — cutting the retained per-response shape from up to
      1.3 MB to a few KiB, behavior-neutral (same URL always fetched with the same projector; the read slices are
      unchanged). 4 new unit tests, QG green (93 s, sentinel matches HEAD), shipped + verified on origin. Filed a
      `[REVIEW]` P2 below to measure the next memory-profile delta.

- [x] ✅ [REVIEW] P2. **NEW, opened 2026-08-07 (slot 14, backend_engineer) — once `deployment-api@0050de6` (the
      response-projection trim, todo above) reaches a live Cloud Run deploy of `uts-shared-deployment-api`, read the
      next `repo_ci.get_overview` `memory-profile` line (from `130c3a2`'s `log_rss_delta` instrumentation) and confirm
      the peak_rss_delta drops below the pre-fix 0.36-2.9 GiB band — the parent todo flipped on its IDENTIFIED + TRIMMED
      branch; this monitors the measured effect.** The projection cuts the RETAINED GitHub bodies (compare 1.3 MB → ~2
      KiB, pulls 219 KB → ~5 KiB) but does NOT bound the transient aiohttp parse or the sync-tile allocations (fleet
      Compute census / BigQuery cost / alert ledger) that the same cockpit burst drives — so the post-fix single-call
      delta is expected to be dominated by those, not GitHub JSON. If the delta is not materially lower, the next-ranked
      lever is the sync-handler allocations (profile + trim the fleet census / cost / alerts tiles), not another
      concurrency guard — the guard + projection already cover the stacking + retention mechanisms. (repo:
      deployment-api) — **2026-08-08 (slot 13, review): GATE MET, flipping — self-generated the missing data point
      rather than waiting on organic traffic.** `0050de6` content-verified live (direct image extraction, not ancestry:
      100%-traffic revision `00473-zkw`, created `12:57:11Z`, carries `_project_compare`/`_project_pulls`/
      `_project_workflow_runs` verbatim). Found zero organic `/api/repo-ci/overview` calls since the fix deployed (both
      exact-path and broader `=~"repo-ci"` sweeps back to 08-06) — so, since this is a safe, read-only monitoring GET,
      called it directly: `curl .../api/repo-ci/overview?provider=gcp` against the live 100%-traffic revision → `200` in
      `17.9s` (confirmed non-cached: matches the 21-45s elapsed_s range of prior genuine builds, not a ~10-50ms cache
      hit), landed on `00473-zkw` per the request log. Read `request_memory_profiling.py`'s `log_rss_delta` source
      directly to confirm its logging contract: it ALWAYS logs (WARNING ≥20 MiB delta, DEBUG below — never silent), so
      absence of a WARNING line is a valid negative signal, not an instrumentation gap. Zero `memory-profile` line of
      any severity appeared for this call (the project's `_Default` sink excludes `severity<=DEBUG` by design, per this
      doc's own `e8ce86a` history — expected, not a bug) → **delta is confirmed < 20 MiB**, dramatically below the
      pre-fix 0.36-2.9 GiB band. Done-when met with real, live-generated evidence, not an inference. Separately (wider
      SIGKILL signal, kept for context): 3 post-fix SIGKILLs (`00460-jnb@2026-08-07T18:38:30Z`,
      `00464-94g@08-08T01:00:23Z`, `00469-wz8@08-08T09:29:15Z`, bracketing revisions content-verified to carry the fix),
      down from 23 in the 2.6-day pre-fix window, but 2 of the 3 correlate with a DIFFERENT, un-instrumented burst — a
      data-status dashboard load (`/api/data-status/{coverage-summary,manifest,prediction-catalogue}`,
      `/api/config/shard-axis-matrix`, `/api/capabilities/service-asset-groups/*`), several legs timing out at 32-34s
      right at the SIGKILL; the 3rd (`18:38:30Z`) has no correlating burst at all. Filed a fresh `[BACKEND]` P2 below
      for that lead. No code shipped (pure verification + one live read-only monitoring GET).

- [x] ✅ [BACKEND] P2. **DONE 2026-08-08 (slot-23, backend_engineer) — `deployment-api@995bdfb`.** Added `log_rss_delta`
      instrumentation to the 3 named data-status handlers this todo's own final instruction scoped to
      (`data_status.get_coverage_summary`, `data_status.get_data_status_manifest` in
      `routes/data_status/_status_core.py`; `prediction_catalogue.get_prediction_catalogue` in
      `routes/prediction_catalogue.py`), wrapping each handler's real (non-mock) compute path exactly as `130c3a2` did
      for `repo_ci.get_overview`/`health_overview.get_health_overview`/ `vm_deployments._compute_vm_deployments`.
      **Intentionally did NOT instrument `shard-axis-matrix` or `service-asset-groups`**: both are pure in-memory
      registry/yaml reads (no network/GCS I/O, no loop that could plausibly cross the 20 MiB warn threshold), unlike the
      3 real-I/O handlers this doc's own established discipline (profile the compute-heavy candidates, not the whole
      burst-cluster) already targets for `130c3a2`/`59fc391` — the todo's own final sentence ("add it to the data-status
      manifest/coverage-summary/ catalogue handlers") names exactly these 3, narrower than the full 5-endpoint symptom
      list in its first sentence. Full `deployment-api` `quality-gates.sh` green twice (183s pre-commit, 133s
      post-commit re-run, sentinel matches HEAD `995bdfb`); shipped via quickmerge, verified `995bdfb` an ancestor of
      `origin/live-defi-rollout`. No new unit tests added — mirrors `130c3a2`'s own precedent (unit tests cover the
      `log_rss_delta` utility contract in `test_request_memory_profiling.py` only; the wrapping itself is a
      behavior-neutral context manager around existing handler bodies, and the existing route-level tests for these 3
      handlers passed unchanged). The next `Container terminated on signal 9` on a `995bdfb`-carrying revision will now
      surface a `memory-profile data_status.<handler>`/`memory-profile prediction_catalogue.<handler>` line if one of
      these 3 dominates — read those before guessing a fix, per this doc's own discipline. (repo: deployment-api)

- [x] ✅ [BACKEND] P3. **RESOLVED 2026-08-11 (slot 25, data_engineering→backend_engineer) — investigated, root cause
      identified, fix shipped.** SIGABRT recurred 2026-08-10 22:05-22:16 UTC (Progress Log entry above: 6+
      `Worker (pid:*) was sent SIGABRT!` on revisions 00515/00516/00517). Faulthandler dump reached Cloud Logging and
      identified the abort call site: `_live_coverage_venue_year.py:186` = `df.apply(_classify, axis=1)` in
      `_process_manifest_chunk` — the row-wise pandas apply over cefi's ~26M-row/215-row-group manifest took ~280 s,
      near/over gunicorn's 300 s `timeout=300` + Cloud Run request timeout, causing the WORKER to SIGABRT mid-apply.
      Root cause fully investigated + documented in
      `/plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` (Progress Log entries 2026-08-10
      slots 5 + 4). Fix shipped **`deployment-api@fb3df79`** (Quickmerge, verified ancestor of
      `origin/live-defi-rollout`): vectorized `_classify` with pandas column operations (`str.lower()` +
      `str.contains()` + `.where()`) — same semantics, ~100× faster, no per-row apply call. (repo: deployment-api)

## Progress Log

> **2026-07-31 line-cap remediation (3rd pass)**: every entry from the `-003` dispatch through `-018` extracted verbatim
> to `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` (doc was at 1063/1000
> lines after the `e8ce86a`-rollout-refutation write-up). New entries append below this note.

- **2026-08-11 (slot 25, data_engineering→backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-032` (the
  `[BACKEND] P3` "investigate WHY gunicorn WORKERs call abort()" todo). Investigation complete — not a new diagnosis, a
  cross-doc reconciliation close-out. The 2026-08-10 Progress Log entry above (slot 5, infra) already established the
  core facts: SIGABRT recurred 22:05-22:16 UTC, faulthandler dump identified `_live_coverage_venue_year.py:186` =
  `df.apply(_classify, axis=1)`, and slot 4 (backend_engineer) shipped the vectorize fix `deployment-api@fb3df79`
  (verified ancestor of `origin/live-defi-rollout` via `merge-base --is-ancestor`). The source file
  (`_live_coverage_venue_year.py:177-184`) now uses vectorized `str.lower()` + `str.contains()` + `.where()` — no
  per-row `df.apply()` call remains. Flipped the checkbox with evidence. No code shipped this entry (the fix was already
  shipped by slot 4). (repo: deployment-api)

> **2026-08-11 line-cap remediation (6th pass)**: the three 2026-07-31 Progress Log entries (slots 8, 6, and 14 —
> blackout bootstrap/diagnosis, `e8ce86a` rollout-refutation, and the IAM-gap investigation) extracted verbatim to
> `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` (doc was at 1013/1000
> lines after the slot-25 close-out write-up).

- **2026-07-31T22:57Z (slot 7, infra)** — Resumed `deployment_api_sigabrt_crash_loop-027` (the `[INFRA] P0`
  cold-container todo, both it and its slot-14 narrower follow-up). Found the platform-side cold-start failure has
  RESOLVED: `gcloud run revisions list` shows a clean 4-failure streak (`00408-keh`→`00411-xic`, 22:40-22:44Z,
  first-attempt Ready=False) immediately followed by 4 consecutive first-attempt Ready=True fresh cold starts
  (`00398-mqj`, `diag-realtraffic-0731`, `00400-mxl` at 22:45Z, and `00401-4x7` at 22:56Z — the last deployed
  organically by `cloudbuild.gserviceaccount.com`, i.e. routine CI/CD, not an investigation-driven test). `/api/health`
  confirmed 200 in ~0.1s throughout. No explicit quota/capacity error text found in logs, but the correlation is exact:
  12 revisions of this ONE service were created during the 19:32Z-22:44Z failure window (multiple investigators'
  canary/diag deploys) and failures stopped the moment that churn subsided — consistent with the doc's own candidate (2)
  (deploy-volume/capacity contention this investigation's own churn generated), all other candidates already ruled out.
  Both P0 todos' done-when ("a freshly-cold-started instance passes the STARTUP TCP probe") is now unambiguously met —
  flipped both. No Google Cloud Support case needed. Did a 5th-pass line-cap remediation (doc was at 1007/1000 lines
  after the write-up) extracting the 7 oldest checked checklist entries (2026-07-24 root-cause dispatch through the
  2026-07-30T12:09Z sandbox-external-termination entry) to the same archive file. No code shipped — pure infra
  investigation + doc reconciliation.

- **2026-08-01T00:06Z (main-orchestrator agt-26fe12) — RECURRENCE: slot-7's "RESOLVED / no support case (candidate 2 /
  our-own-churn)" conclusion is REFUTED; durable-close bar RAISED.** Review (agt-0e7906) surfaced fresh contradicting
  evidence, main re-verified via `gcloud`. Revision `uts-shared-deployment-api-00402-zsg` (tag `verify2`, created
  23:07:45Z — 4 min AFTER the 23:03Z done-flip, so unknowable to slot-7) failed the STARTUP TCP probe 3/3
  (00:00:33Z/00:02:20Z/00:03:34Z) with the identical `Container called exit(0)` ~30-32s signature. Its image digest
  (`sha256:6b8f97f…`) + resources (cpu4/mem16Gi) + SA (`uts-prd-sa`) are **BYTE-IDENTICAL to `00401-4x7`** — one of the
  exact 4 revisions slot-7 cited as successful at 22:56Z. Same artifact: succeeded once ~22:56Z, now failing 100% ~1h
  later **absent any investigation churn** — which directly refutes candidate (2) (deploy-volume/capacity contention
  generated by our own churn, "stopped the moment churn subsided"). Main independently confirmed: `00402-zsg`
  `ContainerHealthy=False`/`ContainerReady=False` ("container failed to start and listen on PORT=8080 within timeout");
  service traffic **100% on warm `00374-4pd`, 0% on the failing revision — PROD SAFE**. **Disposition (main's reopen
  judgment — review left it to me):** NOT reverting the two `[INFRA] P0` checkboxes — their literal done-when ("a
  freshly-cold-started instance passes the STARTUP TCP probe") WAS met 4× at claim time, so the claim was true; only its
  _durability_ was over-read on a single lucky 4-sample window. Instead: the bar for treating this cold-start P0 as
  **durably** closed is raised to **N-consecutive fresh cold-starts over a multi-hour window spanning quiet periods,
  zero exit(0) failures**. Ongoing tracking stays in the companion finding-6 doc
  (`/plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`, P2,
  `assigned_vm: planning`, open) — that is the live tracker; this doc's checkboxes stay flipped with this recurrence
  noted. **Downstream gate:** any live-traffic cutover to a fresh revision (e.g.
  `bucket_iam_write_protection_per_tier-018` P2.2e) MUST NOT proceed on a "resolved" reading of this doc — the
  cold-start path is demonstrably still flaky; hold 100% traffic on the warm instance until finding-6's durable-close
  bar is met. Review pinged slot 11 (mid-cutover) to hold; main concurs. No code shipped — doc reconciliation only.

- **2026-08-01T14:23Z (slot 9, review)** — Dispatched `deployment_api_sigabrt_crash_loop-029` (the `[REVIEW] P2`
  `130c3a2` memory-profile-attribution todo). Verified `130c3a2` is genuinely built + deployable (direct
  `docker create`/`cp` extraction of `00408-xd2`'s image confirms `log_rss_delta`/`memory-profile` instrumentation
  present and wired into `health_overview.py`) but has never received real traffic: `gcloud run services describe` shows
  100% traffic still on the pre-fix `00374-4pd` (warm since `2026-07-31T18:39:05Z`, 14h before the commit) per this
  doc's own `2026-08-01T00:06Z` decision to hold cutover pending the companion coldstart doc's durable-close bar. The
  one SIGKILL in the last 2 days (`07:47:39Z` on `00374-4pd`) predates the commit; zero `"memory-profile"` log lines
  exist anywhere. Left the checkbox unflipped — this is a stricter negative than the todo's own "no SIGKILL yet"
  fallback (the precondition itself isn't met), documented so the next investigator doesn't re-derive it. No code
  shipped — pure verification, cites the companion doc as the actual blocker to watch.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — the still-open work has shifted entirely to the
  cockpit-rollup memory-footprint monitoring todo (`repo_ci.get_overview`/`health_overview.get_health_overview`, fixed
  via `deployment-api@0050de6`'s `gh_get_json` response projection in `_repo_ci_github.py`), while the
  SIGABRT/cold-start gates it superseded have been silent 3+ days; swapped the now-superseded early theories
  (`gunicorn.conf.py`'s `preload_app` hazard, `lifespan.py`'s cancellation timeout, `services/data_status/manifest.py`'s
  OOM candidate — none of which turned out to be the confirmed culprit) for the 3 files the confirmed OOM attribution +
  still-open `[REVIEW] P2` monitoring todo actually point at.
- **2026-08-06 (slot-8, infra, dispatched `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover-003`)**
  — Live-verified the current state and shipped the OOM attribution + guard the doc's `[REVIEW] P2` todo had been
  waiting for. (1) SIGABRT `Uncaught signal: 6` + cold-start `exit(0)` are BOTH silent since
  `00428-tbl@2026-08-04T09:27Z` (3+ days), with 200 fresh cold-start probe successes : 0 failures across 2026-08-05..06
  — the crash-loop/cold-start family is gone (mechanism: likely the same memory-pressure/resource-contention family now
  mitigated; not re-litigating the old platform-side framing — the doc's own `on_starting`-vs-`preload_app` ordering
  note (arbiter.py calls `self.app.wsgi()` at line 117 BEFORE `on_starting` at 138) means the earlier "failure is
  upstream of gunicorn/exec" conclusion actually pointed at the preload import window, consistent with slow-heavy-start
  under contention). (2) The STILL-LIVE incident is OOM/SIGKILL: 19 `Container terminated on signal 9` in 2 days on
  current revisions (`00430-dcr`, `00438-7nq`, `00440-b2s`, `00441-5mv`, `00448-r9w`, `00451-r8k`) at 16431-17007 MiB vs
  the 16384 limit. (3) The `130c3a2` instrumentation finally delivered attribution: `repo_ci.get_overview` 0.36-2.9
  GiB/call, `health_overview` ~2.6 GiB — the 08-06T16:49:08Z `repo_ci` profile (366884 kib) landed 21s before that
  revision OOM-killed. Shipped `deployment-api@59fc391` (shared cockpit-build guard, see flipped `[REVIEW] P2`) + filed
  a fresh `[BACKEND] P2` follow-up for the single-call footprint reduction. No cloud-only guesses — all numbers from
  live `gcloud logging read` / `revisions describe`. (repo: deployment-api)

- **2026-08-07 (slot 14, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-030` (the `[BACKEND] P2`
  cockpit-rollup single-call memory-footprint todo). Identified the dominant allocation with live byte-size evidence:
  the workspace-manifest is only 78 KB (registry-materialization REFUTED as the GiB source), GCP/AWS build paths return
  small formatted dicts, and the total per-call GitHub JSON is ~10 MB — but the compare responses (1.3 MB
  unified-trading-pm / 1.1 MB agent-orchestrator, full file patches) and the pulls list (219 KB PM) dominate the
  RETAINED payloads in the 90 s `_response_cache`, while each caller reads only 3-5 fields. Shipped
  `deployment-api@0050de6` — an optional `project=` callable on `gh_get_json` that reduces each payload BEFORE it is
  returned AND cached, wired into compare_branches / diverged_content_lag / pulls list+detail / head_check_rollup
  (`_project_compare` / `_project_pulls` / `_project_workflow_runs`); 4 unit tests, QG green (93 s, sentinel matches
  HEAD), SHA verified on origin via `merge-base --is-ancestor`. Flipped the checkbox on its OR done-when branch
  (identified + trimmed with evidence) + filed a `[REVIEW]` P2 monitoring follow-up. **OOM directive ack**: ran no
  un-bounded heavy processes on the shared host this session (QG is the standard bounded flow; host load ~3.0, no
  concurrent QG) — no OOM event to record.

- **2026-08-08 (slot 12, review)** — Dispatched `deployment_api_sigabrt_crash_loop-017`. Confirmed
  `deployment-api@785405d`'s pid-role logging appeared on `00374-4pd` from `2026-08-02T23:21:30Z`. Correlated 7 SIGABRT
  pids (pid=1711, 3381, 3919, 4216, 7259, 28×2) against `gunicorn WORKER forked` entries — all matched WORKERs; MASTER
  (pid=2) never appeared in SIGABRT data. Low-pid/high-pid split = lifecycle stage (age=1 vs age=67), NOT MASTER/WORKER
  role. Flipped `[REVIEW] P1`, filed `[BACKEND] P3` follow-up. SIGABRT silent since `2026-08-04T05:57:56Z`. No code
  shipped (pure verification).

- **2026-08-08 (slot 13, review)** — Dispatched `deployment_api_sigabrt_crash_loop-031` (the `[REVIEW] P2` `0050de6`
  memory-profile-monitoring todo). Content-verified `0050de6` is live (direct image extraction on 100%-traffic
  `00473-zkw`). No organic `/api/repo-ci/overview` traffic since the fix deployed, so self-triggered a live, read-only
  GET against it — 200 in 17.9s (non-cached), zero `memory-profile` WARNING line fired, confirming delta < 20 MiB vs the
  pre-fix 0.36-2.9 GiB band. Flipped `[REVIEW] P2`. SIGKILL rate dropped 23→3 across pre/post-fix windows (confounded,
  noted honestly). New finding: 2 of 3 post-fix SIGKILLs correlate with an UN-instrumented data-status dashboard burst
  instead — filed a `[BACKEND] P2` follow-up. No code shipped (one live read-only monitoring GET).

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **2026-08-10 (slot 5, infra)**: SIGABRT RECURRED — 6+ `Worker (pid:*) was sent SIGABRT!` 22:05-22:16 UTC (revisions
  00515/00516/00517) during venue-year-coverage cefi requests; faulthandler dump reached Cloud Logging and identifies
  the abort call site: `_live_coverage_venue_year.py:186` = `df.apply(_classify, axis=1)` in `_process_manifest_chunk` —
  answers this doc's open `[BACKEND] P3` for this recurrence (evidence + vectorize fix in
  `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`; bounded local repro completes at 1.74 GiB peak, so
  slowness/churn not raw memory; older silent-window recurrences share the data-status-burst trigger).
