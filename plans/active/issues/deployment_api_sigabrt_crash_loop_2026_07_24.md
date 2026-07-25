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
asset_group: [meta]
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
- [ ] [REVIEW] P1. Confirm `deployment-api@1adf54b` is live, then read the next SIGABRT faulthandler dump; branch below.
      Verify it's live via `gh pr list` / the promote workflow; once it's been live a few hours, `gcloud logging read`
      the `run.googleapis.com%2Fstderr` stream around the next `Uncaught signal: 6` and check for a
      `Fatal Python     error`/`Current thread` faulthandler dump naming `deployment-api@6f6a389`'s `_compute_inventory`
      cold path — if so, the SIGABRT loop is resolved by that fix and the crash rate should visibly drop; if not, do not
      re-guess — file a fresh evidence-backed BACKEND todo with the exact stuck call site. (repo: deployment-api) — **🟢
      ACTUALLY LIVE since 2026-07-25T02:51:26Z — slot 6's 04:41Z "STILL NOT LIVE" was a FALSE NEGATIVE (slot 10, review,
      2026-07-25T05:25Z)**: the ancestor check (`git merge-base --is-ancestor 1adf54b origin/main`) fails forever
      post-squash-merge — `main` only ever receives the synthetic `chore(promote)` squash commit, never the original LDR
      SHA — so it was never valid evidence of absence. Correct method: content-diff.
      `git show origin/main:deployment_api/gunicorn.conf.py | grep faulthandler` shows `faulthandler.enable()` present,
      byte-identical to LDR's copy — the fix IS on `main`, squashed into PR #376 (`273c951`, merged `02:43:58Z`). Cloud
      Run revision `uts-shared-deployment-api-00274-s9g` (the SAME revision slot 2/6 both inspected — its image tag just
      never changed again because no NEWER promote has landed since) was built from that commit at
      `2026-07-25T02:51:26Z`. **So the fix has been live ~2.5h, and the precondition IS met** — filed a standalone
      methodology issue for the false-negative pattern itself:
      [deployment_promote_squash_ancestry_false_negative_2026_07_25.md](deployment_promote_squash_ancestry_false_negative_2026_07_25.md).
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
      `deployment_promote_squash_ancestry_false_negative_2026_07_25.md`): `origin/main`'s `gunicorn.conf.py` is
      byte-identical to the fix commit, promoted via `2efbbcb` at `06:05:45Z`. Cloud Run revision
      `uts-shared-deployment-api-00275-7zl` (built `06:14:00Z`, confirmed serving 100% traffic) carries it.
      `gcloud     logging read` for `"Uncaught signal"` scoped to that exact revision: **zero occurrences** — not
      surprising, only 9 minutes elapsed since deploy vs. the measured ~20-40min crash cadence, not yet a stall. Not
      completable this turn (the trigger event — the next SIGABRT — hasn't happened yet, not a blocker to resolve).
      Released via `/skip-current-task`. Next dispatch: re-run the same `gcloud logging read` scoped to revision
      `00275-7zl`; once a SIGABRT appears, pull the `stderr` stream ±5min around it and read the
      `Fatal Python error`/`Current thread` dump for the stuck call site.

## Progress Log

- **2026-07-25T07:08Z (slot 5, review)** — Re-checked the `[REVIEW] P2` precondition against the actual live revision.
  Confirmed `uts-shared-deployment-api-00275-7zl` (built `06:14:00Z`, carries `deployment-api@7ba17e2`'s
  `post_worker_init` faulthandler fix) is still the live revision (`gcloud run revisions list`, no newer revision
  deployed since slot 2's `06:23Z` check). `gcloud logging read` scoped to that exact revision for `"Uncaught signal"`
  since deploy: **zero occurrences** as of `07:08:40Z` — i.e. **~54.5 minutes elapsed with no crash**, now past the
  measured ~20-40min cadence with margin. Still not conclusive on its own: pulled the full 24h "Uncaught signal" history
  (41 rows) and found natural gaps of **50-71 minutes occur even within confirmed-still-broken periods** (e.g.
  `16:21:04Z`→`17:32:30Z` = 71min gap and `19:09:34Z`→`20:08:58Z` = 59min gap, both on revision `00268-d2l` while the
  loop was unambiguously still active) — so a ~54min quiet window doesn't yet distinguish "fixed" from "just hasn't
  happened yet." No faulthandler dump exists to read; the diagnostic question remains genuinely open.
  - **New substantive evidence** (not previously on this doc): the sibling `_compute_inventory` cold-path hypothesis
    named in this todo already had a partial mitigation live BEFORE the faulthandler fix — `deployment-api@6f6a389`
    (committed `2026-07-24T23:03:07Z`, bounds `_load_inventory`'s cold-cache path to `_PROVIDER_CENSUS_TIMEOUT_SEC`=45s
    via `future.result(timeout=...)`, see
    [deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md](deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md))
    was already part of the SAME deploy wave as `1adf54b` and therefore already live on
    `uts-shared-deployment-api-00274-s9g` since `02:51:26Z`. Yet `00274-s9g` **continued crashing with
    `Uncaught signal: 6` as recently as `06:10:50Z`** — over 3 hours after the 45s bound went live. If the cold-path's
    _unbounded_ synchronous block were the sole mechanism starving gunicorn's 300s worker-heartbeat timeout, bounding it
    to 45s should have materially suppressed further SIGABRTs from that specific path; it did not. This **weakens (does
    not fully refute)** the `_compute_inventory` cold-path hypothesis as the primary/sole cause — plausible remaining
    explanations not yet checked: concurrent cold-path hits across DIFFERENT `(cloud, region_scope)` cache keys stacking
    past 300s in aggregate even with each individually bounded at 45s, or `future.result(timeout=...)` still blocking
    the event loop thread synchronously (not `run_in_executor`-wrapped) so repeated near-back-to-back cold hits could
    still starve the heartbeat, or a genuinely different stuck call site. None of these confirmed — flagging as the next
    investigation angle for whoever reads the actual dump, not asserting a new root cause without evidence.
  - Not closing the checkbox — the precondition (a faulthandler dump to read) still doesn't exist. Releasing via
    `skip-current-task` with `reason_code: GATED` (fleet-scoped cooldown, matching slot 4's prior precedent) rather than
    continuing to poll a stochastic external event in-session — 5 dispatches (slot4→slot6→slot10×2→slot2→slot5) have now
    checked this same precondition; the fleet-scoped GATED cooldown is exactly the mechanism designed to bound that
    waste (per main's `05:16Z` note above). Next dispatch: re-run the same `gcloud logging read` scoped to whatever is
    the CURRENT live revision at that time (re-verify it's still `00275-7zl` or a later one first); once a SIGABRT
    appears, pull the `stderr` stream ±5min around it for the `Fatal Python error`/`Current thread` dump, and weigh it
    against the cold-path-weakening evidence above before concluding a call site.

- **2026-07-25T05:55Z (slot 2, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-002` (the
  `[BACKEND] P1` todo). Root-caused via code inspection rather than another log-only pass: pulled the installed
  `gunicorn`/`uvicorn` package source directly and traced the exact call order inside a forked worker — `post_fork`
  (where `1adf54b` calls `faulthandler.enable()`) runs, then `Worker.init_process()` calls `self.init_signals()`, and
  this service's `worker_class = "uvicorn.workers.UvicornWorker"` OVERRIDES that method with one that does
  `for s in self.SIGNALS: signal.signal(s, signal.SIG_DFL)` — `Worker.SIGNALS` includes `SIGABRT`. So
  `faulthandler.enable()`'s SIGABRT handler is silently reset to the kernel default microseconds after being installed,
  on every single worker, every time — there was never a real handler in place by the time any actual SIGABRT fired,
  which is exactly what "Uncaught signal: 6" with zero Python trace means. This also fully answers this session's
  earlier open question (checked which revision/instance owned pid=29 at `04:27:19Z` via `gcloud logging read` — same
  fresh `00274-s9g` instance, first log at `02:51:28Z`, kept serving requests after the crash — ruling out the
  stale-instance hypothesis) and makes the stderr-buffering hypothesis moot (the handler was never armed, so there was
  nothing to flush). Shipped `deployment-api@7ba17e2`: moved `faulthandler.enable()` to a new `post_worker_init` hook,
  which gunicorn calls AFTER `init_signals()` — verified nothing later in the worker lifecycle (uvicorn's own `Server`
  only ever installs SIGINT/SIGTERM handlers) touches SIGABRT's disposition again. 2 new tests, `quality-gates.sh`
  PASSED. Checkbox flipped — the diagnostic question is answered; whether this actually stops the crash-loop (vs. just
  making it produce a dump) is for the `[REVIEW]` todo below once this deploy is live and the next SIGABRT is read.

- **2026-07-25T05:40Z (slot 4, review)** — Dispatched task `deployment_api_sigabrt_crash_loop-003` (the `[REVIEW] P2`
  todo gated on "once the above BACKEND todo ships (or a subsequent SIGABRT does show a dump)"). Checked both branches
  of that precondition — neither is met: (1) `git log` on `deployment_api/gunicorn.conf.py` / `deployment_api/main.py`
  in this slot's fresh-pulled clone shows `1adf54b` (faulthandler.enable()) is still the newest observability commit —
  no follow-up commit exists yet addressing why the `04:27:19Z` dump was missing; (2) `gcloud logging read` on
  `run.googleapis.com%2Fvarlog%2Fsystem` for `"Uncaught signal"` since `2026-07-25T04:27:00Z` (now `05:40Z`, a ~73min
  window vs. the measured ~20-40min crash cadence) returns exactly ONE row — the same `04:27:19.520761498Z pid=29` entry
  already on record, no NEW occurrence to check for a dump. Live revision is still `uts-shared-deployment-api-00274-s9g`
  (created `02:51:26Z`, confirmed via `gcloud run revisions list` — no newer revision has deployed). Not closing the
  checkbox — genuinely not ready, not a judgment call. Releasing via `skip-current-task` (`reason_code: GATED`, ~30min
  cooldown) rather than idling this slot on an unmet precondition, per main's 05:16Z note that repeat-redispatch of an
  unchanged precondition is the known wasteful-not-harmful pattern this mechanism exists to bound.

- **2026-07-25T05:25Z (slot 10, review)** — Corrected the false "STILL NOT LIVE" verdict from slots 2/6/10's own earlier
  check this session: `deployment-api@1adf54b` HAS been live since `2026-07-25T02:51:26Z` (revision
  `uts-shared-deployment-api-00274-s9g`, built from squash-merged PR #376 / `273c951`) — the repeated
  `git merge-base --is-ancestor 1adf54b origin/main` check is structurally incapable of returning true after a
  squash-merge promote (verified via content-diff instead: `faulthandler.enable()` is present in `origin/main`'s
  `gunicorn.conf.py`, byte-identical to LDR). Filed the systemic verification-methodology bug as its own issue:
  [deployment_promote_squash_ancestry_false_negative_2026_07_25.md](deployment_promote_squash_ancestry_false_negative_2026_07_25.md).
  With the precondition now confirmed met, read the actual next SIGABRT occurrence (`04:27:19Z`, post-deploy) — no
  faulthandler dump appeared on stderr for it (24h stderr sweep shows nothing between `01:03:36Z` and now). Per the
  todo's own instruction, did NOT re-guess a root cause — filed a fresh evidence-backed `[BACKEND]` todo above for why
  the dump is missing, plus a follow-on `[REVIEW]` todo to read the dump once it does appear. Checkbox left unchecked —
  the diagnostic question ("what's the stuck call site") remains genuinely open, just for a new reason (missing
  evidence, not an undeployed fix). No code shipped this entry (pure investigation + doc correction).

- **2026-07-25T05:11Z (slot 10, review)** — Third consecutive dispatch (slot2→slot6→slot10) to re-check the same
  precondition. Zero change since slot 6's 04:41Z check (~30 min prior): live revision still
  `uts-shared-deployment-api-00274-s9g` / image tag `273c951`; `git merge-base --is-ancestor 1adf54b origin/main` still
  fails; `1adf54b` still 13 commits behind `origin/live-defi-rollout` tip;
  `gh pr list --repo IggyIkenna/deployment-api --state open` shows zero open PRs (no promote in flight). Since
  prose-only flags in this log clearly aren't being actioned fast enough to stop the redispatch (slot 6's identical
  recommendation went unaddressed for one full tick), escalated directly via `POST /api/agents/by-role/main/message`
  (msg id 1939) requesting main add a `deployment-api-1adf54b-live` prerequisite gate to this backlog task —
  workers/review slots don't have filesystem access to `backlog.yaml` (it isn't checked out in any slot worktree) so
  this needs main's action. No code shipped (nothing to ship — the fix already shipped as `1adf54b`; still purely
  wait-and-verify).
- **2026-07-25T05:16Z (main, agt-52bb99)** — Replied to review msg 1939 (ack 1948). Correction to "needs main's action":
  main is **also** barred from hand-editing `backlog.yaml` (the same HARD RULE — author plans, backend derives the
  YAML), so main cannot attach the prereq directly. Verified the mechanism in code: the named-gate path exists
  (`POST /api/prerequisites/{name}` sets values; `task.prereqs.prerequisites` gates dispatch) but 0 tasks currently use
  it, and attaching THIS task is a `backlog.yaml` `prereqs.prerequisites` hand-tune that regen _preserves_
  (`server/backlog.py`, the 2026-07-12 `backlog_regen_drops_handtuned_prereqs` durability fix) — an **operator** edit,
  NOT a plan-authorable field (no per-todo prereq syntax; `gate_on_depends` gates plan/task completion, not a
  deployment-state fact like "1adf54b is the live revision"). **Two actions, both surfaced to operator:** (1) [OPERATOR]
  hand-tune `deployment_api_sigabrt_crash_loop-002` → `prereqs.prerequisites: [deployment-api-1adf54b-live]`, seed the
  gate false, flip true once `git merge-base --is-ancestor 1adf54b origin/main` succeeds AND the live Cloud Run revision
  image tag moves off `273c951`. (2) [BACKEND] P2 — make `PlanRegenLoop`/dispatch skip re-offering a task whose worker
  returned "external-precondition-unchanged" (a cooldown or a worker-reported not-ready signal), so this waste-class
  self-limits without a per-task hand-tune. Until then the re-dispatch is wasteful-not-harmful (worker fast-returns on
  the unchanged precondition; no corruption).
- **2026-07-24 (slot 2, backend_engineer)** — Correlated + audited per the todo, then went further once the named
  hypothesis was refuted.
  - **Correlation (live `gcloud logging read` against `uts-shared-deployment-api`, project `central-element-323112`)**:
    pulled every `Uncaught signal: 6` entry from `run.googleapis.com%2Fvarlog%2Fsystem` over the last 3 days, then
    cross-referenced the `run.googleapis.com%2Frequests` stream in ±2min and ±6min windows around several crashes (e.g.
    `2026-07-24T22:31:25Z`, revision `uts-shared-deployment-api-00269-t66`, pid=188). Found **zero correlated heavy/slow
    traffic** — the only requests nearby are trivial `/health` and `/api/health` probes at 3-7ms latency. `pid`s within
    one revision climb monotonically over many hours (e.g. `00268-d2l`: 28 → 2874 across ~8h), meaning the crash hits
    individual gunicorn **workers** repeatedly within the SAME long-lived container, not the master and not a full
    container restart.
  - **Eager-gRPC-client audit (the named hypothesis)**: grepped every route module reachable from `deployment_api.main`
    for module-level (import-time) `firestore.Client(`/`pubsub_v1.*Client(`/ `SecretManagerServiceClient(` construction.
    **None found** — every gRPC-based client construction in the repo (`health_routes.py`'s
    `_check_pubsub`/`_check_secret_manager`/`_check_deployment_events`; `_ci_status_firestore_store.py`'s
    `firestore_module_factory`) is inside a function, called lazily at request time, several with an explicit "lazy
    cloud-SDK boundary" comment for exactly this reason. `_cfg = DeploymentApiConfig()` at `main.py:30` (module level)
    is a pydantic-settings object with no client construction in `__init__`. **This hypothesis is REFUTED** —
    `preload_app = True` is not planting a poisoned gRPC channel across the fork in this codebase today.
  - **New evidence, mechanistic match**: read the installed `gunicorn/arbiter.py` directly
    (`.venv/lib/python3.13/site-packages/gunicorn/arbiter.py:489-508`, `murder_workers()`) — confirmed gunicorn's own
    Arbiter sends **exactly `signal.SIGABRT`** (`self.kill_worker(pid, signal.SIGABRT)`) to any worker whose heartbeat
    file (`worker.tmp.last_update()`) is older than `timeout` (300s here, `deployment_api/gunicorn.conf.py:41`, "5
    minutes for turbo data-status"). This is a 1:1 mechanistic match for the observed "signal 6" — it explains why
    individual WORKER pids die (not the master), and it's consistent with per-worker heartbeat starvation rather than a
    fork-time poisoned resource. **NOT fully confirmed**: the `WORKER TIMEOUT (pid:%s)` critical-level log line
    gunicorn's arbiter emits immediately before the kill (`self.log.critical(...)`, same function) does **not** appear
    anywhere in 7 days of Cloud Run logs (checked all log streams, not just stderr) — so this remains the leading,
    evidence-backed hypothesis, not a closed case. (Confirmed separately: gunicorn's own logging pipeline DOES reach
    Cloud Run stderr in general — e.g. an unrelated `asyncio.CancelledError` traceback from `_cancel_background_tasks`
    inside `lifespan.py` shows up cleanly at `2026-07-24T13:30:43Z` — so the absence isn't a blanket "gunicorn logs
    never reach Cloud Run" explanation; it's specifically the arbiter's own critical-log call that's unaccounted for.)
  - **Most likely trigger for the >300s heartbeat gap**: cross-referencing the SIBLING issue doc
    ([`deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`](deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md))
    Gap 2 — `_load_inventory`'s COLD path (`deployment_api/routes/deployments_inventory.py:2040-2073`) computes
    `_compute_inventory` **synchronously under a lock, with no timeout and no `run_in_executor` wrap**, unlike the
    reaper tick and the main sync loop (both already offloaded to a `ThreadPoolExecutor`). A synchronous call NOT
    wrapped in an executor blocks the single asyncio event loop thread directly — which is exactly what would prevent
    `UvicornWorker`'s heartbeat-notify callback (itself scheduled on that same event loop) from firing, starving the
    gunicorn arbiter's heartbeat file past the 300s cutoff. That gap already has its own tracked `[BACKEND] P1` todo in
    the sibling issue doc (todo 2, not yet shipped) — not duplicated here; flagging the connection is the useful
    addition from this session's evidence.
  - **Shipped**: `deployment-api@1adf54b` — `faulthandler.enable()` added to gunicorn's `post_fork` hook
    (`deployment_api/gunicorn.conf.py`), so every worker now dumps a full all-threads Python stack trace to stderr on
    ANY fatal signal (SIGABRT included) before dying. This is additive-only (no behavior change to request handling),
    directly targets the exact diagnostic gap found above (today's crash leaves zero Python-level trace), and will
    either confirm the arbiter-timeout hypothesis or reveal the true cause definitively on the next occurrence (expected
    within ~20-40 min of deploy, per the measured cadence). `bash scripts/quality-gates.sh --no-fix` green (130s),
    shipped via `quickmerge --agent --files`.
  - **Handoff**: once the deploy carrying `1adf54b` reaches prod (LDR→staging promote per this repo's `staging` toggle —
    NOT direct-to-main; verify via `gh pr list` / the promote workflow) and the next SIGABRT fires,
    `gcloud logging read` the stderr stream for the `Fatal Python error` / `Current thread` faulthandler dump and update
    this doc with the confirmed stuck call site. If it names `_compute_inventory`'s cold path, that directly validates
    (and raises confidence on) the sibling issue doc's Gap-2 todo as the fix. If it names something else entirely, file
    a fresh, evidence-backed BACKEND todo here with the exact stuck frame.
