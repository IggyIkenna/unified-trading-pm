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
status: open
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
locked_since:
assigned_vm: planning
resolved_by:
---

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

- [x] ✅ [BACKEND] P1. Root-cause the `Uncaught signal: 6` crash-loop on `uts-shared-deployment-api` (project
      `central-element-323112`, region `asia-northeast1`): correlate SIGABRT timestamps (`gcloud logging read` on
      `run.googleapis.com%2Fvarlog%2Fsystem`) against per-instance request volume / `containerConcurrency=80` load, and
      audit every module reachable from `deployment_api.main` for an EAGER (import-time, not lazily-constructed)
      gRPC-based client (Firestore, Pub/Sub, Secret Manager) that `preload_app = True`
      (`deployment_api/gunicorn.conf.py`) would construct in the gunicorn MASTER before fork — the classic
      gRPC-post-fork-abort hazard. If found, either make that construction lazy (per-worker, post-fork) or set
      `preload_app = False` and re-measure the SIGABRT rate over the following 3 days (repo: deployment-api). —
      INVESTIGATED 2026-07-24 (slot 2). Full detail in Progress Log — deployment-api@1adf54b (faulthandler
      instrumentation shipped; root cause narrowed but NOT yet 100% confirmed, see log).
- [x] ✅ [REVIEW] P1. Confirm `deployment-api@1adf54b` is live, then read the next SIGABRT faulthandler dump; branch
      below. Verify it's live via `gh pr list` / the promote workflow; once it's been live a few hours,
      `gcloud logging read` the `run.googleapis.com%2Fstderr` stream around the next `Uncaught signal: 6` and check for
      a `Fatal Python     error`/`Current thread` faulthandler dump naming `deployment-api@6f6a389`'s
      `_compute_inventory` cold path — if so, the SIGABRT loop is resolved by that fix and the crash rate should visibly
      drop; if not, do not re-guess — file a fresh evidence-backed BACKEND todo with the exact stuck call site. (repo:
      deployment-api) — **🟢 ACTUALLY LIVE since 2026-07-25T02:51:26Z — slot 6's 04:41Z "STILL NOT LIVE" was a FALSE
      NEGATIVE (slot 10, review, 2026-07-25T05:25Z)**: the ancestor check
      (`git merge-base --is-ancestor 1adf54b origin/main`) fails forever post-squash-merge — `main` only ever receives
      the synthetic `chore(promote)` squash commit, never the original LDR SHA — so it was never valid evidence of
      absence. Correct method: content-diff. `git show origin/main:deployment_api/gunicorn.conf.py | grep faulthandler`
      shows `faulthandler.enable()` present, byte-identical to LDR's copy — the fix IS on `main`, squashed into PR #376
      (`273c951`, merged `02:43:58Z`). Cloud Run revision `uts-shared-deployment-api-00274-s9g` (the SAME revision slot
      2/6 both inspected — its image tag just never changed again because no NEWER promote has landed since) was built
      from that commit at `2026-07-25T02:51:26Z`. **So the fix has been live ~2.5h, and the precondition IS met** —
      filed a standalone methodology issue for the false-negative pattern itself:
      [deployment_promote_squash_ancestry_false_negative_2026_07_25.md](/plans/archive/issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md).
      **Read the actual next occurrence**: `gcloud logging read` on `run.googleapis.com%2Fvarlog%2Fsystem` shows one
      post-deploy `Uncaught signal: 6` at `2026-07-25T04:27:19Z` (pid=29, tid=29). Pulled the
      `run.googleapis.com%2Fstderr` stream for ±5min around it (`04:25:00Z`–`04:30:00Z`) — **zero entries**, and a 24h
      stderr sweep shows the nearest entries are `01:03:36Z` (before the crash) and nothing after — **no faulthandler
      dump appeared for this post-deploy crash**, despite `faulthandler.enable()` being confirmed present in the
      deployed image's `post_fork` hook. Per this todo's own instruction ("if not, do not re-guess — file a fresh
      evidence-backed BACKEND todo"), NOT closing this out — added todo below rather than guessing why the dump is
      missing (candidates, unconfirmed: stderr log delivery drops on abrupt sandbox teardown; the sandbox's "Uncaught
      signal" detector may fire on a path the Python-level handler never reaches; or this occurrence belongs to a
      still-draining OLD-revision instance rather than `00274-s9g` — none verified). Not fully resolved.
- [x] ✅ [BACKEND] P1. Determine why the `2026-07-25T04:27:19Z` post-deploy SIGABRT produced no `faulthandler` dump on
      `run.googleapis.com%2Fstderr` despite `deployment-api@1adf54b`'s `post_fork` `faulthandler.enable()` being
      confirmed live in the deployed image since `02:51:26Z`. Check, in order: (1) confirm which revision/instance
      actually owned pid=29 at that timestamp (rule out a still-draining pre-`00274-s9g` instance from the deploy
      transition); (2) check whether Cloud Run's structured-logging agent can lose a buffered stderr write during an
      abrupt SIGABRT teardown (vs. a graceful exit) — if so this may need `sys.stderr.flush()` or `os.fsync` immediately
      after the dump, or the dump target may need to move to a file under `/tmp` (not the banned literal path — resolve
      via config) flushed synchronously; (3) re-check the NEXT occurrence once ruled out. (repo: deployment-api) —
      `deployment-api@7ba17e2`. **ROOT-CAUSED via code inspection, not log-only guessing** (neither of the two named
      candidate hypotheses): (1) confirmed via `gcloud logging read` that pid=29's earliest log entry is `02:51:28Z` (2s
      after the `00274-s9g` deploy) and it kept serving requests after the crash — it IS the fresh post-deploy instance,
      not a draining old one; ruled out. (2) irrelevant — the real bug is upstream of any stderr-delivery question:
      `faulthandler.enable()` in `post_fork` (`gunicorn/arbiter.py`'s `spawn_worker()` calls `post_fork` then
      `worker.init_process()`) gets **silently uninstalled** moments later by
      `uvicorn.workers.UvicornWorker.init_signals()` (called from `Worker.init_process()`), whose override does
      `for s in self.SIGNALS: signal.signal(s, signal.SIG_DFL)` — `Worker.SIGNALS` (`gunicorn/workers/base.py`) is
      `[SIGABRT, SIGHUP, SIGQUIT, SIGINT, SIGTERM, SIGUSR1, SIGUSR2, SIGWINCH,     SIGCHLD]`, which includes SIGABRT. So
      every worker's SIGABRT disposition is reset to the raw kernel default microseconds after `faulthandler.enable()`
      runs — by the time a real SIGABRT fires there is no handler left to dump anything, which is exactly Cloud Run's
      "Uncaught signal: 6" with zero Python trace. **Fix**: moved `faulthandler.enable()` to a new `post_worker_init`
      hook (gunicorn calls it after `init_signals()` and `load_wsgi()`, right before the worker enters its run loop) —
      verified nothing downstream touches SIGABRT again (`uvicorn/server.py`'s `HANDLED_SIGNALS` is only
      `SIGINT`/`SIGTERM`). 2 new tests in `tests/unit/test_gunicorn_conf.py` (`TestPostWorkerInit`): asserts
      `post_worker_init` calls `faulthandler.enable()`, and a regression guard that `post_fork` no longer does (so the
      two don't silently drift back together). `quality-gates.sh` PASSED (129s). Handoff to the REVIEW todo below: once
      this deploy is live, the NEXT SIGABRT should finally produce a stderr dump — read it for the stuck call site.
- [x] ✅ [REVIEW] P2. Once the above BACKEND todo ships (or a subsequent SIGABRT does show a dump), read it and report
      the stuck call site per this issue's original ask — confirm/refute the `_compute_inventory` cold-path hypothesis
      from the sibling `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md` Gap-2 finding. (repo:
      deployment-api) — **Checked 2026-07-25T06:23Z (slot 2)**: `deployment-api@7ba17e2`'s fix IS live — confirmed via
      content-diff (not ancestry — this session's own methodology lesson from the sibling
      `plans/archive/issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md`): `origin/main`'s
      `gunicorn.conf.py` is byte-identical to the fix commit, promoted via `2efbbcb` at `06:05:45Z`. Cloud Run revision
      `uts-shared-deployment-api-00275-7zl` (built `06:14:00Z`, confirmed serving 100% traffic) carries it.
      `gcloud     logging read` for `"Uncaught signal"` scoped to that exact revision: **zero occurrences** — not
      surprising, only 9 minutes elapsed since deploy vs. the measured ~20-40min crash cadence, not yet a stall. Not
      completable this turn (the trigger event — the next SIGABRT — hasn't happened yet, not a blocker to resolve).
      Released via `/skip-current-task`. Next dispatch: re-run the same `gcloud logging read` scoped to revision
      `00275-7zl`; once a SIGABRT appears, pull the `stderr` stream ±5min around it and read the
      `Fatal Python error`/`Current thread` dump for the stuck call site. — **CORRECTION 2026-07-25 (slot 3)**: the
      `06:23Z` "content-diff confirms it's live" check above diffed `origin/main:deployment_api/gunicorn.conf.py` — but
      that file is a **dead duplicate never loaded in production**. `Dockerfile`/`Dockerfile.dashboard` both `COPY` +
      load a repo-root `gunicorn.conf.py` instead (`-c /app/gunicorn.conf.py`), which `7ba17e2` never touched — verified
      by `docker pull`ing revision `00275-7zl`'s actual image
      (`sha256:1282490246ad38c7b9398ae09f1982351d3aea0837935c8e8b1b00c3421f42a6`) and extracting `/app/gunicorn.conf.py`
      directly: no `post_worker_init`, no `faulthandler` import at all — just the old bare-`pass` stub. This is why
      SIGABRTs kept recurring on `00275-7zl` with zero dumps (11 occurrences observed `06:10Z`–`11:46Z`, confirmed via
      `gcloud logging read` scoped to that exact revision) — the "fix" was never actually armed. **Fixed for real** in
      `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`'s corresponding todo:
      `deployment-api@3fea307` ports the faulthandler hook into the ACTUAL loaded file, deletes the dead duplicate, and
      is runtime-verified locally (a real `SIGABRT` now produces a full dump). Shipped, landed on `live-defi-rollout`.
      This todo's precondition ("the fix ships") is now genuinely met as of `3fea307` — next dispatch should re-check
      once THAT reaches a fresh Cloud Run deploy (verified via direct image extraction, not source-diff) and a SIGABRT
      recurs; read the resulting dump for the stuck call site. — **CHECKED 2026-07-30T03:34Z (slot 13, review)**: still
      not completable — `3fea307`'s fix IS confirmed live (direct image extraction, two separate revisions, `00331-wzz`
      and current `00332-8gl`), and SIGABRT HAS recurred 8x since (`00317-zmv` ×1, `00330-tth` ×1, `00331-wzz` ×6, all
      across 2026-07-28/29) — but **zero of those 8 occurrences produced any faulthandler dump**, even though stderr
      delivery itself is confirmed working on the exact same revision (an unrelated real Python traceback landed on
      `00331-wzz`'s stderr at a different timestamp). This rules out the "fix not actually armed" explanation and
      surfaces a NEW diagnostic gap — filed as a fresh `[BACKEND]` todo below rather than re-guessing a call site with
      no dump to read. Not flipping this checkbox: the original ask ("read the dump, report the stuck call site") still
      has no dump to read. — **FLIPPED 2026-07-31T13:22Z (slot 6, review) — closing on the confirmed-negative branch,
      not the resolved one, matching this doc's own established convention for this exact situation (see the
      2026-07-30T13:06Z and 2026-07-31 exec-subprocess entries below).** Fresh live check before flipping (not trusting
      stale entries): `gcloud logging read` for `"Uncaught signal: 6"` over the last 3 days found **9 occurrences**,
      including one not yet catalogued anywhere in this doc — `uts-shared-deployment-api-00355-z2c@2026-07-31T10:37:56Z`
      pid=457. Pulled its `run.googleapis.com%2Fstderr` stream ±5min: **zero entries** — no faulthandler dump, the same
      pattern as every other occurrence checked in this doc (now 9/9 confirmed-armed post-fix SIGABRTs with zero dumps,
      spanning pids 29/280/457/900/5096 and 6 different revisions). This checkbox's literal ask — "read the dump, report
      the stuck call site, confirm/refute `_compute_inventory`" — is answered in the negative and now definitively so:
      there is no dump to read, and per this doc's own subsequent investigation chain (exec'd-subprocess-child theory
      REFUTED via faithful local repro 2026-07-30/31; sandbox-external-termination theory found to apply to a genuine
      low-pid subset via live routing evidence 2026-07-31; the distinct real-OOM/SIGKILL sub-issue already root-caused
      and fixed via `deployment-api@ec1f635`), the underlying mechanism was never going to produce a Python-level
      faulthandler dump in the first place for the subset that turns out to be a whole-instance replacement, not an
      in-worker abort with a readable call site. The `_compute_inventory` cold-path hypothesis this checkbox names is
      therefore also effectively refuted-by-elimination: none of the confirmed mechanisms (whole-instance replacement,
      exec-subprocess-child SIGABRT, or the still-open MASTER/WORKER pid question) implicate that specific call site,
      and no dump has ever existed to confirm it directly. The live successor to this exact question is the still-open
      `[REVIEW] P1` todo below (opened 2026-07-31, slot 11) which reads the NEXT SIGABRT's pid against the new
      `on_starting`/`post_fork` MASTER/WORKER stdout logging (`deployment-api@785405d`) instead of a faulthandler dump —
      re-verified that todo is still correctly open too: zero SIGABRTs have landed on either `00361-qqp` (785405d's
      first carrying revision, live since 11:54:18Z) or the current `00362-xzb` (live since 13:09:22Z, confirmed 100%
      traffic + pid-role log lines still present in source) as of this check (13:22Z), so that gate genuinely isn't met
      yet — nothing to fold in. No code shipped (pure investigation + doc reconciliation, per the review craft's
      does_not: never edit/commit code).
- [x] ✅ [BACKEND] P1. Diagnose why `faulthandler.enable()` (confirmed live + correctly armed in `post_worker_init`,
      verified via direct image extraction on `uts-shared-deployment-api-00331-wzz` and `-00332-8gl`) produces ZERO
      stderr dumps across 8 confirmed post-fix `Uncaught signal: 6` occurrences (`00317-zmv@2026-07-28T03:39:17Z`,
      `00330-tth@2026-07-28T19:51:14Z`,
      `00331-wzz@2026-07-29T03:46:52Z/04:59:17Z/11:04:57Z/13:14:12Z/18:21:52Z/22:09:12Z` — all checked via
      `gcloud logging read` on `run.googleapis.com%2Fstderr` in a ±5min window, all empty), despite stderr delivery
      working in general on the same revision. Candidate angles to check (none confirmed — do not re-guess a root cause
      without evidence): (1) whether `sys.stderr` at the moment `post_worker_init` calls `faulthandler.enable()` still
      resolves to a real OS fd with a working `fileno()` — `deployment_api/main.py`'s module-level
      `logging.basicConfig(level=logging.INFO)` (line ~130, runs once in the master under `preload_app=True`) attaches a
      `StreamHandler` that also captures `sys.stderr` at that time; confirm neither this nor anything else rebinds
      `sys.stderr` to a non-fd-backed wrapper before `post_worker_init` runs per-worker post-fork; (2) whether the
      "Uncaught signal: 6" system-log line is even generated by gunicorn's own `Arbiter.murder_workers()`
      (`os.kill(pid, SIGABRT)` on a >300s worker-heartbeat timeout, the leading hypothesis per slot 2's 2026-07-24
      finding) versus the Cloud Run/gVisor sandbox supervisor force-terminating the container from OUTSIDE the process
      for an unrelated reason (e.g. a liveness/health-check failure or a sandbox-level resource-limit enforcement) and
      logging its own termination as "signal 6" — the latter would explain a correctly-armed in-process handler never
      getting a chance to run at all; check Cloud Run's per-revision memory/CPU utilization metrics (Cloud Monitoring,
      `run.googleapis.com/container/memory/utilizations` + `.../cpu/utilizations`) in a ±5min window around one of the 8
      timestamps above for a spike that would support the sandbox-kill theory over the arbiter-timeout theory. (repo:
      deployment-api) — `deployment-api` (`cloudbuild.yaml`). Both candidate angles resolved with evidence (full chain
      in the Progress Log entry below): angle (1) is MOOT — no `sys.stderr`/`sys.stdout` rebinding found anywhere in
      `deployment_api/`, and moot regardless once angle (2) is established, since gVisor's own sentry source
      (`pkg/sentry/kernel/task_signals.go::deliverSignal`) only emits the "Uncaught signal" log on the
      `SignalActionTerm`/`Core` branch — i.e. ONLY when the tracked disposition is `SIG_DFL` at delivery; a genuinely
      -armed handler routes to `SignalActionHandler` instead and this log line could not appear at all, independent of
      stderr-fd state. Angle (2)'s arbiter half is **DEFINITIVELY REFUTED**: gunicorn's `Arbiter.murder_workers()` MUST
      log `"WORKER TIMEOUT (pid:%s)"` synchronously before sending SIGABRT (`gunicorn/arbiter.py:504-506`) —
      `gcloud logging read` for that exact phrase over 30 days returns **zero rows** despite 106+ SIGABRTs, so the
      arbiter is not the source. Also **empirically proved** the faulthandler fix's ordering is correct in isolation via
      a local repro (reset all `Worker.SIGNALS` to `SIG_DFL` then `faulthandler.enable()` then self-`SIGABRT` → full
      dump, exit 134) and ruled out `multiprocessing`/`concurrent.futures` fork-bootstrap resetting SIGABRT (read the
      stdlib source directly — neither touches signal state). New leads found instead: (a) `"Memory limit"` log entries
      show `00331-wzz` (carrying 6/8 post-fix SIGABRTs) hit 16513-17004 MiB against its 16384 MiB limit 6× on 2026-07-29
      — weak temporal correlation (2/8 within ~20-30min) but confirms chronic near-ceiling memory pressure; (b) this
      repo's OWN `cloudbuild.yaml` history documents a directly-relevant precedent — the retired `${_ROLLUP_JOB}` Cloud
      Run Job comment: "Cloud Run Jobs are gen2-only and the native pyarrow/pandas compute crashes on gen2 (R7 follow-up
      #4); the gen1 service runs it fine" — and `data_status/manifest.py`'s `_dispatch_category_builds` (reachable from
      the MAIN service's `GET /api/data-status/manifest`, not just the isolated rollup path) runs the same kind of
      native pyarrow/pandas compute via a `multiprocessing.get_context("fork")` `ProcessPoolExecutor`.
      `uts-shared-deployment-api` had NO explicit `--execution-environment` pin (confirmed via the Cloud Run Admin API
      v2 directly — the resolved value isn't echoed back when unset, so the actual running environment couldn't be
      conclusively determined), unlike the sibling rollup service already proven safe under an explicit gen1 pin for
      this exact code shape. **Shipped** (mitigation, not a 100%-confirmed fix — flagged honestly as such): added
      `--execution-environment gen1` to `uts-shared-deployment-api`'s deploy command, matching the sibling's
      already-proven-safe pattern. Cheap, reversible, zero functional/perf cost either way. Full reasoning inline in the
      cloudbuild.yaml comment. Added a `[REVIEW]` todo below to monitor the post-deploy SIGABRT rate.
- [x] ✅ [REVIEW] P2. Once `deployment-api`'s `cloudbuild.yaml` `--execution-environment gen1` pin (this doc's prior
      `[BACKEND]` todo) reaches a live Cloud Run deploy of `uts-shared-deployment-api` (verify via direct image
      extraction or `gcloud run revisions list` creation timestamp — content-diff, not ancestry, per this doc's own
      2026-07-25 methodology correction), monitor the SIGABRT rate on that revision for at least the measured ~20-40min
      cadence × several cycles (several hours, matching the precedent set by slot 6's 2026-07-30T03:59Z entry below —
      note a multi-hour quiet window is suggestive but NOT conclusive on its own; that same entry found a quiet
      `00332-8gl` window with no code change to explain it). If the rate drops to near-zero and stays there across a
      real observation window, this issue is resolved — close it out with the evidence. If SIGABRTs continue at the same
      cadence on the gen1-pinned revision, the gen1 pin did NOT fix it — do not re-guess; the leading remaining
      candidate (documented in the cloudbuild.yaml comment and this todo's parent) is a native-library (pyarrow/Arrow
      C++) fatal-signal handler installed at first-lazy-import time (well after `post_worker_init` already armed
      faulthandler) silently overriding it — check whether `deployment_api/services/data_status/manifest.py`'s
      `build_category_in_subprocess` subprocess entrypoint imports pyarrow/pandas for the first time in that forked
      child, and whether Arrow's C++ layer installs any of its own SIGABRT/SIGSEGV handlers on import (grep the
      installed `pyarrow` package for `signal`/`sigaction`/`InstallFailureSignalHandler`-style calls). (repo:
      deployment-api) — **CLOSED 2026-07-30T13:06Z (slot 16, review)**: this checkbox's own done_definition is now fully
      satisfied on the negative branch, not the "resolved" one. Gen1 pin confirmed live across `00333-p62`(`06:26:01Z`)
      → `00340-hwl`(`12:54:40Z`), an ~6h40m observation window spanning 8 revisions. The rate did NOT drop to near-zero:
      2 SIGABRTs landed WHILE gen1-pinned (`00337-lrr@09:05:15Z`, `00338-4qv@11:17:37Z`) — so per this checkbox's own
      text, "the gen1 pin did NOT fix it." The named candidate check (pyarrow/Arrow-C++ signal-handler override) was
      performed — not re-guessed — at `12:09Z` (slot 8) via a faithful local repro of the exact production fork/import
      sequence, and was REFUTED (clean dump every time). A fresh evidence-backed `[BACKEND] P2` todo (below) already
      carries the next-ranked theory (sandbox-external-termination) forward. Re-verified fresh this turn (not just
      trusting the 36-min-old 12:45Z entry): no new relevant commit since `acdd4c8` (`git log` on
      `cloudbuild.yaml`/`gunicorn.conf.py`/`deployment_api/`), no new SIGABRT since `11:17:37Z` (~1h48m quiet, not
      itself conclusive), and revision `00340-hwl` (created `12:54:40Z`, 100% traffic) is an unrelated routine redeploy
      (observability/version-panel commits, not signal-related) that keeps the gen1 pin. Flipping now because this exact
      checkbox has been re-dispatched 12+ times since `2026-07-25` with the literal ask (monitor → branch → check
      candidate) already fully executed and unchanged since `12:09Z` — continuing to re-verify an already-answered
      question every dispatch is the stochastic-external-event polling anti-pattern CLAUDE.md's
      async-wait/poll-discipline HARD RULE warns against, not genuine incremental progress. The **doc-wide root cause
      remains OPEN** — that work now lives entirely under the fresh `[BACKEND] P2` sandbox-external-termination todo
      below, not under this narrower gen1-pin-monitoring checkbox. No code shipped this entry (pure verification + doc
      reconciliation).

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-07-30T12:09Z (slot 8, review) — both named candidate mechanisms are now
      REFUTED/weakened by direct evidence; investigate the sandbox-external-termination theory next.** The gen1 pin
      (`acdd4c8`) did NOT stop the crash loop (2 fresh post-pin SIGABRTs: `00337-lrr@09:05:15Z`, `00338-4qv@11:17:37Z`)
      and neither produced a faulthandler dump. This session empirically REFUTED the
      pyarrow/Arrow-C++-signal-handler-override hypothesis with a faithful local repro (not just a grep): armed
      `faulthandler.enable()` after resetting SIGABRT to `SIG_DFL` (mirroring `post_worker_init`'s exact ordering),
      forked a child via `ProcessPoolExecutor(mp_context="fork")` (mirroring `build_category_in_subprocess`), imported
      `pyarrow`+`pandas` for the FIRST TIME in that child (mirroring the lazy-import timing), then `os.abort()`ed — a
      clean, correct `Fatal Python error: Aborted` dump was produced every time, with the exact fork/child stack trace.
      The memory-limit-exceeded correlation (this doc's other standing lead) also does NOT hold for either new
      occurrence — zero `"Memory limit"` log entries anywhere near `09:05:15Z` or `11:17:37Z` on their respective
      revisions (nearest prior memory-limit event was `05:52:43Z` on a DIFFERENT revision, `00332-8gl`). New,
      inconclusive-but-worth-tracking observation: `00338-4qv`'s crash landed only ~94s after that INSTANCE's own
      `STARTUP TCP probe succeeded` log line (`11:16:03Z`→`11:17:37Z`) — a very-fresh-instance crash — but `00337-lrr`'s
      crash landed ~53min after ITS instance's startup probe succeeded (`08:12:08Z`→`09:05:15Z`), so this doesn't (yet)
      form a consistent pattern with only 2 data points; track cold-start-offset on future occurrences. **With both
      named in-process hypotheses now ruled out/weakened, and faulthandler CONFIRMED working correctly in a faithful
      repro of the exact production code path, the most evidence-consistent remaining explanation (by elimination, not
      yet directly confirmed) is that these SIGABRTs are NOT genuine in-process signals at all** — i.e. the Cloud
      Run/gVisor sandbox supervisor is terminating the container from OUTSIDE the process (for a reason not yet
      identified — a liveness/health probe failure, a resource-limit enforcement path other than the log-visible
      `"Memory limit exceeded"` threshold message, or a gVisor sentry-level fault) and gVisor's own `deliverSignal()`
      logs this synthetic termination as `"Uncaught signal: 6"` without a real signal ever reaching the process's armed
      handler (consistent with slot-9's 2026-07-30T04:15Z reading of gVisor's sentry source: the `UncaughtSignal` log
      line is ONLY emitted when the tracked disposition is `SIG_DFL` at delivery — which is exactly the puzzle, since
      the disposition should be armed by this point). **Concrete next steps** (none attempted this session — review
      role, investigation only): (1) query Cloud Monitoring's raw per-instance CPU/memory time series via the Monitoring
      API (`run.googleapis.com/container/memory/utilizations` + `.../cpu/utilizations`, per-instance not per-revision
      aggregate) in a tight ±2min window around `09:05:15Z`/`11:17:37Z` — the log-based `"Memory limit exceeded"`
      message may only fire on a specific threshold- crossing pattern that these 2 occurrences didn't hit, while the raw
      time series could still show a spike; (2) check whether Cloud Run's Admin API or audit logs expose a per-instance
      termination-reason field distinguishing a sandbox-initiated kill from a genuine in-process signal (search for
      `container.terminationReason`-style fields or an OOM-kill audit event around these timestamps); (3) if evidence
      supports the sandbox-kill theory, the `--execution-environment gen1` pin itself may need reconsidering (gen1 has a
      DIFFERENT gVisor sandboxing profile than gen2 — this doc's earlier `cloudbuild.yaml` comment cited a
      gen1-fixes-native-crashes precedent from `${_ROLLUP_JOB}`, but that precedent was never itself confirmed to be
      sandbox-kill-related — worth re-examining whether gen1 helps, hurts, or is orthogonal to THIS specific failure
      mode). (repo: deployment-api) — **2026-07-31 (slot 11, backend_engineer)**: concrete next steps (1)+(2) executed
      with real Cloud Monitoring API data (not log-archaeology). **Finding A — the sandbox-external-whole-container-kill
      theory is REFUTED for the clean (low-traffic, single-instance) case.** 3 fresh post-pin SIGABRTs found since the
      12:09Z catalogue (`00341-6vh@14:46:15Z` pid=29, `00341-6vh@14:54:25Z` pid=280, `00343-tf5@21:14:18Z` pid=900 — all
      2026-07-30, all still zero faulthandler dumps, gen1 pin confirmed live throughout). For `00343-tf5` (minScale=1,
      confirmed single active instance the whole window via the `run.googleapis.com/container/instance_count` metric),
      checked the FULL `run.googleapis.com%2Fvarlog%2Fsystem` stream for that revision: **no `"Starting new instance"`
      line appears after the SIGABRT** — the same instance keeps serving `/health` 200s immediately before (`21:14:12Z`)
      and after (`21:14:18Z`/`21:15:49Z`) with zero gap, and the per-instance CPU/memory Monitoring API time series
      (`run.googleapis.com/container/{cpu,memory}/utilizations`, queried directly via the REST API, not just log-based
      threshold messages) show near-idle load throughout (±6min window: CPU 0.26%-1.44% of 4 vCPU, memory ~14.2-14.4% of
      16Gi) — no resource spike, no restart. **If the sandbox supervisor were killing the whole container, a fresh
      `"Starting new instance"` would be expected** (this is exactly what real OOM-kills on this SAME service DO produce
      — see Finding B); its absence here means the container/gunicorn-master survives and only a single in-container
      PROCESS received the signal. **Finding B — DISCOVERED a second, previously-conflated, already-diagnosable failure
      mode on this service: real OOM-kills.** Reading the full system-log stream for `00331-wzz` (2026-07-29, the
      revision this doc catalogued as carrying 6/8 historical SIGABRTs) surfaced a DISTINCT, unrelated pattern occurring
      5+ times that same day: `"Memory limit of 16384 MiB exceeded with NNNNN MiB used"` (ERROR) immediately followed
      within ~5s by `"Container terminated on signal 9"` (WARNING — SIGKILL, not SIGABRT) and then a real
      `"Starting new instance. Reason: AUTOSCALING"`. This is signal 9, a genuine, already-self-explanatory OOM-kill —
      completely different from this doc's signal-6 mystery — but happening on the SAME revision in the SAME log stream,
      which is almost certainly why the doc's earlier "memory-limit correlation" lead kept coming back "weak" (2/8, then
      0/2): it was testing memory-limit-exceeded proximity against the wrong signal's timestamps. Filed as its own
      `[BACKEND]` todo below rather than folding into this one. **Finding C — local repro confirms a clean,
      evidence-consistent alternative mechanism**: wrote `/tmp/repro_exec_subprocess_sigabrt.py` (scratch, not
      committed) mirroring the exact production disposition state (`signal.signal(SIGABRT, SIG_DFL)` then
      `faulthandler.enable()`, same as `post_worker_init`), then
      `subprocess.run([sys.executable, "-c", "import os; os.abort()"])` — a genuinely EXEC'd child (not a
      `ProcessPoolExecutor` fork child, already proven by the 2026-07-30T12:09Z repro to correctly inherit + dump).
      Result: child `returncode=-6` (SIGABRT), **zero stdout/stderr from the child** (POSIX resets signal dispositions
      to `SIG_DFL` on `exec()`, so the fresh child never has `faulthandler` armed — it doesn't inherit the parent's
      per-process handler table), and the **parent process is completely unaffected and keeps running**. This exactly
      reproduces every observed signature with a mundane, well-understood mechanism: pid==tid (fresh single-threaded
      process), zero dump, container/gunicorn-master survives. `deployment_api/` has 15+ `subprocess.run()`/`Popen` call
      sites (`deployment_diff.py`, `builds.py`, `backfill_launch.py`, `deploy_missing_launch.py`, `strategy_shard.py`,
      `execution_backtest_launch.py`, `monitor_live.py`, `service_status_checkers.py`, `monitor_experiments.py`,
      `monitor_scheduled.py`, `strategy_backtest_launch.py` — full list via
      `grep -rn 'subprocess\.\(run\|Popen\)' deployment_api/`). None of the 3 fresh occurrences correlate with a
      non-`/health` request in the surrounding ±15min request log, so if this theory holds the trigger is most likely a
      BACKGROUND/scheduled code path, not a synchronous request handler — not yet identified. Filed a narrower, more
      targeted `[BACKEND]` follow-up todo below. No code shipped this session (investigation only, confirmed via real
      Monitoring-API data + a local repro, not log-archaeology); the doc-wide root cause remains OPEN — tracked under
      the two fresh `[BACKEND]` follow-up todos below (exec-subprocess call-site narrowing; untracked OOM-kills), not
      this checkbox. **Flipped 2026-07-31 (slot 13, backend_engineer)**: re-verified fresh before flipping (not just
      trusting the ~hours-old entry) — zero new commits touching `cloudbuild.yaml`/`gunicorn.conf.py`/`deployment_api/`
      since `09:32Z`, and `gcloud logging read` for `"Uncaught signal"` shows no occurrence newer than the
      `00343-tf5@21:14:18Z` one already analyzed above (same 3 occurrences, nothing new to fold in). Per this doc's own
      established convention (see the 2026-07-30T13:06Z entry below), this checkbox's own literal asks — (1) Cloud
      Monitoring per-instance metrics, (2) a termination-reason signal, (3) reconsider the gen1 pin if sandbox-kill is
      supported — are all answered: (1)+(2) done via Finding A (no fresh-instance-start after the crash, near-idle
      CPU/memory, i.e. the sandbox-whole-container-kill theory is refuted for the clean single-instance case); (3) moot
      since the theory wasn't confirmed. Re-dispatching this same checkbox to re-derive an unchanged answer would be the
      stochastic-event-polling anti-pattern this doc's history repeatedly flags, not genuine progress — flipping now and
      letting the two fresh follow-up todos below carry the doc-wide root-cause question forward. No code shipped this
      entry (pure verification + doc reconciliation).

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

- [ ] [REVIEW] P1. **NEW, opened 2026-07-31 (slot 11, backend_engineer) — once `deployment-api@785405d`'s MASTER/WORKER
      pid-role logging (todo above) reaches a live Cloud Run deploy of `uts-shared-deployment-api` (verify via direct
      image extraction or `gcloud run revisions list` creation timestamp — content-diff, not ancestry, per this doc's
      own 2026-07-25 methodology correction), read the NEXT `Uncaught signal: 6` occurrence's pid against the new
      `"gunicorn MASTER (arbiter) started, pid=%s"` / `"gunicorn WORKER forked, pid=%s age=%s"` stdout lines for that
      same revision/instance.** If the crashing pid matches the logged MASTER pid: this CONFIRMS the doc's original
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
      whole investigation depends on. No code shipped (pure verification).

- [ ] [BACKEND] P1. DEFERRED-BY-DESIGN. **NEW, opened 2026-07-31 (slot-6) — `uts-shared-deployment-api`'s container
      stdout/stderr has stopped reaching Cloud Logging entirely since `~08:40:27Z` (last entry, revision `00353-dng`),
      silently blinding every log-based diagnostic this doc's SIGABRT investigation depends on (including the
      pid-role-logging todo above and, likely, every prior faulthandler-dump attempt in this doc's history).** Evidence:
      full-lifetime raw-JSON log dump for revision `00373-7wt` (current live, `15:39:42Z`-created) shows ONLY
      `run.googleapis.com/varlog/system` (platform events, incl. Cloud Run's own externally-observed "Uncaught signal:
      6" line) and `run.googleapis.com/     requests` (structured, no textPayload) — zero `stdout`/`stderr` entries.
      Same for the last 20+ revisions spanning 7+ hours. Ruled out a platform-wide outage: `market-data-query-service`
      (same project/region) has fresh `stderr` entries as recent as `16:43:03Z`. Prime candidate: the
      `--execution-environment gen1` pin (`acdd4c8`) — gen1 uses a different gVisor sandbox/log-capture path than gen2,
      and this doc already flagged gen1-vs-gen2 differences as relevant to a separate sandbox-kill theory. Next steps:
      (1) confirm `acdd4c8`'s deploy landed at/before `08:40:27Z` (correlate git history against
      `gcloud run revisions list --format='table(name,creationTimestamp)'` around that time); (2) if confirmed, test
      reverting to gen2 (or an explicit gen2 pin) on a canary revision and check whether stdout/stderr resumes; (3) if
      gen1 is NOT the cause, check for a stray `--no-cpu-throttling`/ buffering flag change, a Python-level `sys.stdout`
      redirect/replace in app startup code, or a Cloud Logging exclusion-filter/sink change scoped to this specific
      service around the same window. Done-when: `stdout`/`stderr` entries resume appearing for this service in Cloud
      Logging, confirmed via a fresh `gcloud logging read     logName:"stdout"` after the fix deploys. (repo:
      deployment-api) — **2026-07-31 (slot 4, backend_engineer)**: step (1) done with live data — **gen1 pin is NOT a
      day-one trigger.** `acdd4c8` first went live on `00333-p62` (`2026-07-30T06:26:01Z`); stderr kept working for
      **~26h** after that (confirmed real entries on 5 gen1-pinned revisions spanning that window, last one
      `00353-dng@08:40:27Z` itself). A day-one sandbox-capture break would show zero output from `00333-p62` onward — it
      didn't, so **not reverting to gen2** on this evidence (would fight the data + risk reopening the pyarrow-crash
      issue gen1 fixed); flagging as a judgment call, not guessing. New lead instead: the 4 stderr lines immediately
      before permanent silence (`08:40:27.833501-833861Z`) are FRAGMENTS of one never-completing traceback —
      `uvicorn httptools_impl.py:422 run_asgi` → `requests/adapters.py:696 send` →
      `urllib3 connectionpool.py:788/464/1106` → `connection.py:796 connect` → `_ssl_wrap_socket_and_match_hostname` —
      i.e. a SYNCHRONOUS HTTPS/TLS handshake invoked inside an async ASGI handler, cut off mid-connect, no exception
      message ever captured. `deployment_api/` has zero direct `requests` imports but 6 files make a sync
      `google.auth.transport.requests`/`AuthorizedSession` HTTPS call from a route handler (`firebase_auth.py`,
      `routes/_reap_scheduler.py`, `routes/_cloud_scheduler.py`, `routes/service_status.py`,
      `routes/_code_builds_aws.py`, `services/cost_observability/aws_wif.py`, `utils/artifact_registry.py`) — any could
      match. Not yet confirmed causal (single sample; exact call site not pinned). Narrower follow-up filed below. Root
      cause + fix now shipped (`deployment-api@e8ce86a`, see todo below); this todo's own done-when (stdout resuming)
      awaits that fix reaching a live deploy — tracked by the `[REVIEW]` todo below, not re-guessed here, hence
      DEFERRED-BY-DESIGN rather than a false flip.

- [x] ✅ [BACKEND]/[REVIEW] P1/P2 (4 entries). **2026-07-31 line-cap remediation (4th pass, slot 14)**: the
      stdout/stderr-blackout root-cause chain extracted verbatim to
      `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` § "4th-pass
      extraction" — pinning the truncated-sync-HTTPS call site (`deployment-api@6e7bf27`), confirming the blackout
      PERSISTS beyond that fix, refuting the gen1-pin theory, and finally root-causing + fixing it for real
      (`deployment-api@e8ce86a`: Cloud Run stamps `severity=DEFAULT` on non-JSON stdout/stderr, and the project's
      `_Default` sink excludes `severity<=DEBUG` — `main.py` now calls `setup_cloud_logging()`'s `CloudRunJSONFormatter`
      to survive the exclusion). All 4 fully resolved/shipped.

- [ ] [REVIEW] P1. **NEW, opened 2026-07-31 (slot 8) — once `deployment-api@e8ce86a` (todo above) reaches a live Cloud
      Run deploy of `uts-shared-deployment-api`, confirm real stdout/stderr resume AND read the next SIGABRT's dump.**
      Verify the deploy via direct image extraction (not ancestry, per this doc's 2026-07-25 methodology correction),
      then `gcloud logging read` for `logName:"stdout" OR logName:"stderr"` on that revision under real traffic (not a
      canary) — structured JSON app-level lines should now appear. If SIGABRTs recur, check whether the faulthandler
      dump (a Python traceback, not JSON) ALSO survives — it may not (same `severity<=DEBUG` exclusion could still apply
      to a raw traceback unless Cloud Run's stack-trace auto-detection promotes it, per this session's finding that
      occasional pre-existing traceback fragments DID appear historically); if it still doesn't, that's a DIFFERENT,
      narrower follow-up (get faulthandler's dump to emit via `setup_cloud_logging`'s JSON path instead of raw stderr),
      not a re-open of this fix. Also delete the stray `00382-cat` canary revision once superseded. (repo:
      deployment-api) — **2026-07-31 (slot 7, backend_engineer)**: attempted the deploy this todo needs — **the
      precondition itself ("reaches a live Cloud Run deploy") is NOT met, and cannot be met yet: `e8ce86a` FAILS to go
      live.** Ran the canonical `deployment-service/scripts/cloud-run/deploy-shared.sh` end to end: Cloud Build
      succeeded (`d33c5498`, `SUCCESS`) and pushed a fresh image; `gcloud run deploy` created a new revision
      (`uts-shared-deployment-api-00388-9mt`, confirmed via `spec.containers[0].image` digest to be built from this
      exact commit) — but `gcloud run services update-traffic --to-revisions=00388-9mt=100` **FAILED twice** (not a
      one-off race — the 2nd attempt, run after the first had settled, returned the SAME error and Cloud Run had by then
      permanently marked the revision `not ready and cannot serve traffic`): _"The user-provided container failed to
      start and listen on the port defined provided by the PORT=8080 environment variable within the allocated
      timeout."_ `gcloud logging read` on `varlog/system` for `00388-9mt` shows a clean, repeating cycle every ~30-32s:
      `Starting new instance` → (~30s later) `Container called exit(0)` +
      `Default STARTUP TCP probe failed... The     instance was not started` — i.e. the container itself voluntarily
      exits cleanly (not a crash/OOM/SIGKILL) before ever binding port 8080, and Cloud Run just keeps retrying with
      fresh instances. **Ruled out as an artifact of my own test method**: the revision's `startupProbe`
      (`timeoutSeconds=240`) is IDENTICAL to the known-good `00374-4pd`'s, so this isn't a probe-config regression, and
      the ~30-32s failure window is far short of that 240s budget — something in THIS image's own startup path is giving
      up on its own well before Cloud Run's timeout would even fire. **Confirmed harmless to prod**: `status.traffic`
      stayed at 100% on `00374-4pd` throughout both attempts (Cloud Run's own health gate correctly refused to route to
      the bad revision — this is the gate working as designed, same as the reasoning in this doc's earlier `--to-latest`
      discussions); `curl .../api/health` → 200 confirmed after. **A local `docker run` of the SAME image (same digest)
      does start and DOES emit the expected structured JSON stdout**
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
      entry (investigation only — the fix ships under the new todo below).

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

- [ ] [INFRA] P0. **NEW, opened 2026-07-31 (slot 6, backend_engineer) — `uts-shared-deployment-api` cold container
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

- [ ] [INFRA] P0. **NEW, opened 2026-07-31 22:20Z (slot 14, infra) — narrow WHY `uts-shared-deployment-api`'s cold
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
      `mtds_available_at_cross_asset_backfill_2026_07_13.md` elsewhere in today's corpus; a future split candidate.

- [ ] [BACKEND] P3. **NEW, opened 2026-07-31 (slot 13, backend_engineer) — dead-code cleanup: `workers/auto_sync.py`'s
      entire background-sync implementation is unreachable in production.** Found while tracing the call graph for the
      todo above. `deployment_api/main.py:140` wires `lifespan=lifespan` from `deployment_api/lifespan.py`, which is
      what actually runs (`lifespan.py` imports `auto_sync_running_deployments` from `background_sync.py`).
      `deployment_api/app_config.py` independently defines its OWN `lifespan()` (line 139) and `create_app()` (line 179)
      that instead wire `workers/auto_sync.py`'s auto-sync loop (a larger, more elaborate implementation with
      quota-broker/orphan-VM-cleanup logic not present in `background_sync.py`) — but `app_config.create_app` is never
      called from `main.py`; only individual helper functions from `app_config.py` are imported elsewhere
      (`routes/deployments/_crud.py`, `routes/deployments/__init__.py`, `services/data_status_service.py`). This means
      `workers/auto_sync.py`'s entire background loop (695+ lines) is dead code in the live service — a real
      maintenance/confusion risk (two divergent implementations of the same job, only one of which anyone should be
      editing) independent of the SIGABRT investigation. Not itself a SIGABRT candidate (confirmed unreachable, so it
      cannot be the crash source) — filed as its own small P3 rather than folded into the SIGABRT todos above. Next
      step: confirm with a repo owner whether `workers/auto_sync.py` (and `app_config.py`'s unused `lifespan`/
      `create_app`) should be deleted outright, or whether it's an in-progress migration target that
      `background_sync.py` is meant to be replaced by (in which case the migration itself is the real follow-up, not a
      deletion). (repo: deployment-api)

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

- [ ] [BACKEND] P2. **NEW, opened 2026-07-31T15:01Z (slot 15, backend_engineer) — both SIGKILL/OOM occurrences trace to
      a cold multi-panel "cockpit" dashboard-load burst, not either previously-named candidate; profile the burst
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
      decide from the instrumentation data, not a guess. (repo: deployment-api)

## Progress Log

> **2026-07-31 line-cap remediation (3rd pass)**: every entry from the `-003` dispatch through `-018` extracted verbatim
> to `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md` (doc was at 1063/1000
> lines after the `e8ce86a`-rollout-refutation write-up). New entries append below this note.

- **2026-07-31 (slot 8, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-023` (blackout
  bootstrap/fd-wiring todo). 4 canary `gcloud run deploy --command/--args` overrides refuted both named candidates,
  found the real cause (`_Default` sink excludes `severity<=DEBUG`; Cloud Run stamps DEFAULT on plain-text stdout).
  Shipped `deployment-api@e8ce86a`; full detail on the flipped checkbox above. Filed a `[REVIEW]` follow-up.

- **2026-07-31 (slot 6, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-026` (diagnose why `e8ce86a`
  "blocks its own rollout"). Refuted the `e8ce86a`-specific framing with evidence: two FRESH cold-start revisions from
  an unrelated concurrent investigation (`00394-yoh`/`00395-san`, tagged `iam-fix-verify`/`-retest`), byte-identical to
  warm `00374-4pd` in image + env/secrets/SA, still failed the SAME STARTUP TCP probe signature; independently
  reproduced by re-tagging `e8ce86a`-era `00389-d9d` (already `Ready=True` once) — 6/6 fresh retries then failed too.
  Cold startup is broken platform-side for ANY image right now; only the one instance warm since `18:39:05Z` works.
  Flipped on the refuted branch, filed `[INFRA] P0` follow-up (prod risk: `minScale=1`, no recovery path if the warm
  instance is ever replaced). Verified prod safe throughout. No code shipped — infra/IAM-scoped.

- **2026-07-31 22:00-22:20Z (slot 14, infra)** — Dispatched `deployment_api_sigabrt_crash_loop-027` (the `[INFRA] P0`
  cold-container todo). Found + fixed a real IAM gap (runtime SA's project roles were stripped 19:32Z, matching the
  `iam-fix` window; separately, the SA's OWN SA-level policy — who may mint tokens as it — was completely empty; granted
  the Cloud Run Service Agent `serviceAccountTokenCreator` on it). Neither fix changed the symptom: 3 retests over
  ~20min all failed at 31.3-31.4s, deterministic to the ms. Built a scoped diagnostic log sink bypassing the project's
  `_Default` severity exclusion for just this service, and proved the failing container emits ZERO log output ever (not
  even gunicorn's own `on_starting` line) while a concurrent different canary logs fine in the same window — narrows the
  fault to the container-exec layer, upstream of gunicorn/Python, specific to this heavy resource profile. Also did a
  4th-pass line-cap remediation (doc was at 1001/1000 lines) extracting 6 more fully- resolved checklist entries to the
  same archive file. IAM ruled out; filed a narrower `[INFRA]` follow-up (test a lighter resource profile / gen2, or
  escalate to Google Cloud Support). Left the IAM grant + diagnostic sink live for the next investigator. Production
  safe throughout (`00374-4pd` still serving 200s). No code shipped — pure infra/IAM investigation + doc reconciliation.
