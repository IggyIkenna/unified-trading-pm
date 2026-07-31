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
- [ ] [REVIEW] P2. Once the above BACKEND todo ships (or a subsequent SIGABRT does show a dump), read it and report the
      stuck call site per this issue's original ask — confirm/refute the `_compute_inventory` cold-path hypothesis from
      the sibling `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md` Gap-2 finding. (repo:
      deployment-api) — **Checked 2026-07-25T06:23Z (slot 2)**: `agent-orchestrator@7ba17e2`'s fix IS live — confirmed
      via content-diff (not ancestry — this session's own methodology lesson from the sibling
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
      has no dump to read.
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

- [x] ✅ [BACKEND] P2. **NEW, opened 2026-07-31 (slot 13, backend_engineer) — re-open the sandbox-external-termination
      theory specifically for HIGHER-traffic/multi-instance revisions.** This session exhaustively ruled out the
      exec'd-subprocess-in-background-loop theory (see the todo above) via a full call-graph audit — the one background
      loop actually wired into production (`background_sync.auto_sync_running_deployments`, confirmed via
      `main.py:140`'s `lifespan=lifespan` import chain) has zero reachable `subprocess`/`Popen` call sites anywhere in
      its call graph (`SyncService`, `vm_utils.list_running_vm_names`, `DeploymentsRegistry.reap_stale`,
      `StateManager.cleanup_state_ttl` — none call subprocess; the one path that could,
      `SyncService._acquire_and_launch` → `orch.submit_shard`, is dead code since `DeploymentOrchestrator` has no
      `submit_shard` method). With the background-exec-subprocess theory now refuted (not just the arbiter and
      pyarrow-signal-handler theories from earlier in this doc) and Finding A (2026-07-31, slot 11) having only checked
      the CLEAN single-instance case for the sandbox-external-termination theory, the natural next step is re-running
      Finding A's exact method (per-instance `container/{cpu,memory}/utilizations` + `instance_count` Cloud Monitoring
      queries, `"Starting new instance"` presence/absence in the system log) against a SIGABRT that landed on a revision
      actively running MULTIPLE concurrent instances — Finding A's own caveat is that its clean evidence doesn't
      directly apply there. Concrete next steps: (1) `gcloud logging read` for
      `run.googleapis.com/container/instance_count` (or the Monitoring API equivalent) around each of the 9 cataloged
      post-fix SIGABRT timestamps in this doc to find one where `instance_count` > 1 at the time of the crash; (2) for
      that occurrence, apply Finding A's exact method — check for a `"Starting new instance"` line immediately after
      (would support sandbox-external-kill) vs. its absence (would support genuinely in-process, still-unexplained); (3)
      if no multi-instance occurrence exists yet in the historical catalogue, this todo stays open until the next
      SIGABRT lands on a multi-instance revision — don't force a conclusion from single-instance data. (repo:
      deployment-api) — **2026-07-31 (slot 7, backend_engineer)**: all 3 steps done with live Cloud Monitoring + Logging
      data. (1) `run.googleapis.com/container/instance_count` (Monitoring API v3 REST, no `gcloud monitoring` CLI
      subcommand exists) at 1-min res around every queryable cataloged timestamp (`00317-zmv`/`00330-tth` have rolled
      off the `varlog/system` retention window — verified via a zero-row bare-timestamp query, not assumed) found
      `00338-4qv@2026-07-30T11:17:37Z` (pid=29) at `instance_count=2`, the needed multi-instance case. (2) Applying
      Finding A's method here surfaces a signal it missed: the request log's per-instance-ID trace, not just system-log
      `"Starting new instance"` presence. Pre-crash instance `001548f72951...` (613 reqs since `09:26:10Z`) served its
      LAST request `11:17:27.722Z` (9.6s pre-crash) and never serves again; a co-existing already-warming instance
      `001548f729a8...` (spun up `11:15:20Z` for an unrelated autoscale event) absorbs all traffic from `11:17:56.505Z`
      (19.2s post-crash) — genuine instance abandonment with no NEW `"Starting new instance"` line needed since spare
      capacity already existed (Finding A's line-absence test is a false negative here: it checks _provisioning_, not
      _routing abandonment_). Cross-checked a genuinely single-instance pid=29 case, `00337-lrr@09:05:15Z`
      (`instance_count=1` throughout): here a REAL `"Starting new instance. Reason: AUTOSCALING"` line DOES fire, 2.58s
      post-crash, paired with a `"Truncated response body ... application exited before the response was finished"`
      WARNING, plus a hard instance-ID swap in the request log (`...e3c2...`→`...df14...`) — i.e. Cloud Run silently
      kill-replaced the whole instance under a generic `AUTOSCALING` tag indistinguishable by text alone from a benign
      scale event. **This directly contradicts Finding A's blanket "refuted for the clean case," which was drawn from
      one pid=900 sample.** (3) Checked pid as the differentiator: Finding A's clean case was pid=900; both disrupted
      cases here are pid=29. A third check, `00341-6vh@14:54:25Z` (pid=280), shows the SAME instance ID serving
      continuously through the crash, zero gap — matching the pid=900 pattern. **4/4 occurrences split cleanly by pid:
      low (28/29, plausibly gunicorn master/earliest worker) → genuine whole-instance replacement; high (280/900/5096,
      plausibly recycled workers) → zero disruption.** Tried to CONFIRM (not just correlate) the master/worker mapping
      via gunicorn's own boot logging on `stdout`/`stderr` — zero such lines emitted (a real logging gap, not
      retention), so the mapping is a strong 4/4 correlation, not yet mechanistically proven. Filed a `[BACKEND] P1`
      follow-up to confirm it directly and reconcile the doc's framing — this reframes the doc's core question as "TRUE
      for the low-pid subset, confirmed via live routing evidence," not the "refuted" verdict the prior single-sample
      check reached. No code shipped (pure investigation, 4 occurrences × 2 log streams each).

- [x] ✅ [BACKEND] P1. **NEW, opened 2026-07-31 (slot 7, backend_engineer) — confirm whether the low-pid (28/29) vs
      high-pid (280/900/5096) split found this session (see the todo above) actually maps to gunicorn MASTER vs
      recycled-WORKER roles, and reconcile the doc's headline conclusion.** 4/4 checked occurrences split cleanly: low
      pids → genuine whole-instance replacement (request abandonment, instance-ID swap, sometimes a
      generically-`AUTOSCALING`-tagged `"Starting new instance"` line); high pids → zero disruption. Strong correlation,
      not yet a confirmed mechanism — gunicorn's own boot-time PID/role logging doesn't reach Cloud Logging on this
      service (checked `stdout`/`stderr` around `00337-lrr`'s boot, zero matching lines). Next: (1) add explicit
      PID-role logging in `gunicorn.conf.py`'s `on_starting` (arbiter) vs `post_fork` (per-worker) hooks so the next
      SIGABRT's pid maps to a role without guessing; (2) if confirmed, update this doc's framing — the original
      "crash-loop compounding the reaper" claim is TRUE for the low-pid subset (not refuted, as the pid=900
      single-sample check had concluded), just mislabeled by Cloud Run's generic `AUTOSCALING` reason string; (3) then
      investigate WHY the master itself calls `abort()` (never established — this doc only traced supervisory mechanics;
      `faulthandler` is only armed worker-side, so an arbiter-side abort has no dump to read yet). (repo:
      deployment-api) — **2026-07-31 (slot 11, backend_engineer)**: shipped step (1), the only part of this todo
      determinable without waiting for a future SIGABRT. `deployment-api@785405d`: added an `on_starting` hook (fires
      ONCE, in the master/arbiter, before any fork) logging `"gunicorn MASTER (arbiter) started, pid=%s"` via
      `server.log.info` (reaches stdout — `errorlog = "-"`/`accesslog = "-"` are already confirmed-working delivery
      paths per this doc's earlier findings), and extended the existing `post_fork` hook to also log
      `"gunicorn WORKER forked, pid=%s age=%s"` per worker fork (age = gunicorn's own spawn-order counter, already used
      for leader-election — 0..N-1 = initial spawn, N+ = a post-recycle re-fork). Together these give a durable stdout
      record mapping every pid this container ever forks to a role (MASTER vs WORKER) + spawn generation, so the NEXT
      SIGABRT's pid can be looked up against these lines instead of inferred from magnitude. 2 new unit tests
      (`TestOnStarting.test_logs_master_pid`, `TestPostFork.test_logs_worker_pid_and_age`) + all existing
      `test_gunicorn_conf.py` tests green; `quality-gates.sh` PASSED (112s); verified live on origin via
      `merge-base --is-ancestor`. Steps (2)/(3) are NOT actionable yet — they require reading a SIGABRT that occurs
      AFTER this ships and matching its pid against these new log lines; filed as a `[REVIEW]` follow-up below rather
      than guessing ahead of the evidence.

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
      conclusion from zero data. (repo: deployment-api) — **2026-07-31 (slot 3, review): gate genuinely NOT met yet —
      zero SIGABRTs on the new-logging deploy so far, correctly staying open.** Content-verified (not just
      ancestry-inferred) that `deployment-api@785405d` is actually live: pulled the exact image
      (`asia-northeast1-docker.pkg.dev/.../deployment-api@sha256:2d69d3a6...489d7`) backing the current Cloud Run
      revision `uts-shared-deployment-api-00361-qqp` (created 2026-07-31T11:54:18Z, ~26min after the commit's 11:28:37Z
      timestamp — plausible normal CI-deploy SLA) and grepped the extracted `gunicorn.conf.py`: both new log lines
      (`"gunicorn MASTER (arbiter) started, pid=%s"` in `on_starting`, `"gunicorn WORKER forked, pid=%s     age=%s"` in
      `post_fork`) are genuinely present in the deployed bytes. Then searched Cloud Logging
      (`resource.type=cloud_run_revision`, `service_name=uts-shared-deployment-api`,
      `textPayload:"Uncaught signal:     6"`, 2-day window) for any SIGABRT since that deploy: the most recent
      occurrence is on revision `uts-shared-deployment-api-00355-z2c` at `2026-07-31T10:37:56Z` — **before** `00361-qqp`
      (11:54:18Z), i.e. on a pre-logging revision. Zero SIGABRTs have landed on `00361-qqp` (or any later revision) as
      of this check. Per this todo's own done-when clause, correctly leaving it open rather than forcing a conclusion
      from zero data. No code shipped (pure verification). Re-check next time a fresh dispatch of this task fires, or
      whenever a new `Uncaught signal: 6` log line appears for `uts-shared-deployment-api` on a revision at/after
      `00361-qqp`.

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

- [ ] [REVIEW] P2. **NEW, opened 2026-07-31 (slot 13, backend_engineer) — monitor whether `deployment-api@ec1f635`'s
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
      2026-07-30T04:15Z entry but never itself concurrency-guarded). (repo: deployment-api)

## Progress Log

- **2026-07-31 (slot 7, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-009` (the sandbox-
  external-termination-for-multi-instance todo). Executed all 3 named steps with live Cloud Monitoring/Logging data;
  full evidence is inline on that checkbox above, not duplicated here. Headline: found the needed multi-instance
  occurrence (`00338-4qv@11:17:37Z`, pid=29, `instance_count=2`), and applying Finding A's method to it (plus 2 more
  cross-checks) surfaced a pid-based split across 4 occurrences — low pids (28/29) correlate with genuine whole-instance
  replacement (incl. a real `"Starting new instance"`/`AUTOSCALING`-tagged line + a `"Truncated response body"` line on
  the single-instance pid=29 case), high pids (280/900) show zero disruption — which CONTRADICTS Finding A's blanket
  "refuted" conclusion (drawn from one pid=900 sample). Flipped the checkbox; filed a `[BACKEND] P1` follow-up to
  confirm the pid↔gunicorn-role mapping and reconcile the doc's framing. No code shipped (pure investigation).

- **2026-07-31 (slot 13, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-008` (the real-OOM-kill /
  SIGKILL todo). `gcloud logging read` over 30 days found exactly 8 `"Container terminated on signal 9"` events, ALL
  within the last 3 days, each within 0.06%-4% of the 16384 MiB limit and each within seconds of an `AUTOSCALING`
  `"Starting new instance"` line — a genuine, recent, cold-start-correlated OOM pattern. Traced the mechanism (not just
  logs): `catalogue_lifecycle.py`'s new-listings/upcoming-expiries builders each fan out 5 concurrent per-AG
  `ThreadPoolExecutor` parquet reads on every UNCACHED call with no cap on concurrent uncached requests — the exact
  multi-AG "first-mount burst" this repo's own `cloudbuild.yaml` comment already documents as the 2026-07-17 8Gi→16Gi
  incident's cause, which explicitly recommends a concurrency guard "rather than bumping again" instead of the fix ever
  being built. Shipped `deployment-api@ec1f635`: a `threading.Semaphore` guard (mirrors the sibling drilldown endpoint's
  `_drilldown_build_semaphore`) that sheds load as a 503 + `Retry-After` once 2 uncached builds are already in flight. 4
  new tests + all 25 existing `catalogue_lifecycle` tests green; `quality-gates.sh` PASSED (111s); verified on origin
  via `merge-base --is-ancestor`. Flipped the checkbox; filed a `[REVIEW] P2` monitoring todo (does the SIGKILL rate
  actually drop on the fix-carrying revision) plus two named next-candidate mechanisms if it doesn't.

- **2026-07-31 (slot 11, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-014` (confirm/reconcile the
  pid↔gunicorn-role mapping). Shipped the only currently-determinable part (step 1): `deployment-api@785405d` adds an
  `on_starting` hook logging the arbiter's own pid once at master startup, and extends `post_fork` to log each worker's
  pid+age on every fork — together a durable stdout record so the NEXT SIGABRT's pid can be matched to MASTER vs WORKER
  without guessing. 2 new unit tests + all existing `test_gunicorn_conf.py` tests green; `quality-gates.sh` PASSED
  (112s); verified on origin. Steps (2)/(3) need a post-deploy SIGABRT to read against these new lines — filed a
  `[REVIEW] P1` follow-up rather than guessing ahead of the evidence. Flipped the checkbox.

> **2026-07-31 line-cap remediation**: every entry from the original 2026-07-24 finding through the `-007` dispatch
> extracted verbatim to `/plans/archive/2026_07/deployment_api_sigabrt_crash_loop_progress_log_history_2026_07_31.md`
> (doc was at 1060/1000 lines). New entries append below this note going forward.
