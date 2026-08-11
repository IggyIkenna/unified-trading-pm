---
doc_type: issue
title: "deployment-api SIGABRT/OOM crash-loop investigation — Progress Log history (through 2026-07-31 slot-13 entry)"
summary:
  Line-cap remediation extraction from plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md's Progress
  Log — every entry from the original 2026-07-24 finding through the 2026-07-31 `-007` (exec-subprocess call-site audit)
  dispatch, moved verbatim so the live doc stays under the 1000-line hard cap. Every closed checkbox on the live doc
  already carries its own inline evidence summary; this file is the full narrative trail behind those summaries — read
  it only if a deeper citation on a specific dispatch's reasoning is needed.
status: archived
nature: notes
asset_group: [ui]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-registry, crash-loop, sigabrt, oom, history, line-cap-remediation]
related: [/plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md]
created: 2026-07-31
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-07-31
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source: [plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md, line-cap remediation 2026-07-31]
assigned_role: project_management
drift_direction: none
---

# deployment-api SIGABRT/OOM crash-loop investigation — Progress Log history

> Extracted verbatim 2026-07-31 (line-cap remediation, doc was at 1060/1000 lines after the `-008` OOM-kill entry) from
> `/plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md`'s `## Progress Log` section, oldest content
> first. The live doc keeps only its two most recent entries (the 2026-07-31 `-009` and `-008` dispatches) inline going
> forward; everything below was here before that. Fully superseded by the live doc's own checkbox-level evidence
> summaries — those were written to stand alone, so this file adds citation depth, not new facts.

- **2026-07-31 (slot 13, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-007` (the `[BACKEND] P2`
  "narrow the exec'd-subprocess-SIGABRT theory" todo). Fresh-pulled all slot repos. Executed step (1) exhaustively
  rather than another grep pass: first confirmed which of the two competing `auto_sync_running_deployments`
  implementations is actually live — `main.py:140`'s `lifespan=lifespan` wires `lifespan.py`, which imports the loop
  from `background_sync.py`, NOT `workers/auto_sync.py` (whose loop is wired only by `app_config.py`'s own parallel,
  never-called `create_app()`/`lifespan()` — dead code, filed as its own P3 cleanup todo below). Traced the real live
  loop's full call graph end to end (`SyncService.sync_deployments`/ `_run_ttl_cleanup`/`reap_stale_deployments` →
  `vm_utils.list_running_vm_names` (google.cloud compute_v1, no subprocess) → `DeploymentsRegistry.reap_stale`
  (unified-trading-library, no subprocess) → `StateManager. cleanup_state_ttl` (GCS StorageClient, no subprocess); the
  one path that could reach a launcher, `_acquire_and_launch` → `orch.submit_shard`, is dead — `DeploymentOrchestrator`
  (checked directly in the sibling deployment-service repo) has no `submit_shard` method, so the `getattr` always
  resolves to `None` and the call silently no-ops). **Conclusion: zero subprocess call sites are reachable from the loop
  that's actually running in production — the background-exec-subprocess theory is REFUTED by exhaustive call-graph
  evidence**, not a grep-depth limitation. Flipped the checkbox (its own ask — audit and find-or-rule-out a call site —
  is answered, on the negative branch, same convention as this doc's other closed checkboxes). Filed two fresh todos: a
  `[BACKEND] P2` re-opening the sandbox-external-termination theory specifically for higher-traffic/multi-instance
  revisions (Finding A only checked the clean single-instance case), and a `[BACKEND] P3` for the `workers/auto_sync.py`
  dead-code discovery (tangential to the SIGABRT hunt, adjacent finding, doesn't warrant its own issue doc). No code
  shipped this entry (pure investigation via direct source reads across deployment-api, unified-trading-library, and
  deployment-service — not log-archaeology or re-guessing).

- **2026-07-31 (slot 13, backend_engineer)** — Re-dispatched `deployment_api_sigabrt_crash_loop-006` (this
  `[BACKEND] P2` sandbox-external-termination todo, 18th+ dispatch on this doc, ~hours after slot 11's 09:32Z session
  below). Fresh-pulled all slot repos. Re-verified fresh rather than trusting the recent entry:
  `git log --since="2026-07-31 09:32:00" -- cloudbuild.yaml gunicorn.conf.py deployment_api/` on
  `origin/live-defi-rollout` — zero new commits; `gcloud logging read` for `"Uncaught signal"` scoped to
  `uts-shared-deployment-api` over the last 2 days — the newest row is still `00343-tf5@2026-07-30T21:14:18Z`, the same
  occurrence slot 11 already folded into Finding A/C below, nothing new. This checkbox's own 3 concrete next steps
  (Cloud Monitoring per-instance metrics; a termination-reason signal; reconsider the gen1 pin if sandbox-kill is
  supported) were all already executed with real data in the 09:32Z session and conclusively answered (theory refuted
  for the clean single-instance case; gen1-pin reconsideration moot). Per this doc's own established convention
  (2026-07-30T13:06Z entry: flip once a checkbox's own literal ask is answered, even on the negative/refuted branch, and
  let a fresh follow-up todo carry the doc-wide question forward — don't keep re-dispatching an unchanged answer),
  flipped the checkbox above rather than re-running the same already-answered checks a 18th time. No code shipped (pure
  verification + doc reconciliation); the doc-wide root cause stays open under the two `[BACKEND]` follow-up todos slot
  11 filed (exec-subprocess call-site narrowing; untracked OOM-kills) — whoever picks up
  `deployment_api_sigabrt_crash_loop-007`/`-008` next should work those.

- **2026-07-31T09:32Z (slot 11, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-006` (the
  `[BACKEND] P2` sandbox-external-termination todo, 17th+ dispatch on this doc). Fresh-pulled all slot repos; confirmed
  no new deployment-api commit touching `cloudbuild.yaml`/`gunicorn.conf.py`/`deployment_api/` since the last progress
  entry. Confirmed current live revision is `uts-shared-deployment-api-00353-dng` (100% traffic, `07:10:20Z`), gen1 pin
  still present. Executed the todo's own concrete next steps (1)+(2) with real data instead of re-verifying the
  already-settled precondition checks: `gcloud logging read` found 3 fresh post-catalogue SIGABRTs
  (`00341-6vh@14:46:15Z`/`14:54:25Z`, `00343-tf5@21:14:18Z`, all 2026-07-30) — gen1 pin conclusively still doesn't stop
  it (5 total post-pin now). Queried the Cloud Monitoring REST API directly (`timeSeries.list` on
  `container/{cpu,memory}/utilizations` and `container/instance_count`, not just log-based threshold messages) for
  `00343-tf5`'s clean single-instance window around `21:14:18Z`: CPU/memory both near-idle, and — the key new fact —
  `instance_count` never drops to 0 and the system log shows NO `"Starting new instance"` after the crash, meaning the
  container/gunicorn-master genuinely survives. This is direct evidence AGAINST the sandbox-whole-container-kill theory
  this todo was chasing (a real sandbox-initiated kill should produce a fresh instance-start, exactly as seen for actual
  OOM-kills — see below). While reading `00331-wzz`'s full system-log stream for comparison, discovered a SEPARATE,
  previously-conflated failure mode: real `SIGKILL`/"Container terminated on signal 9" OOM-kills (5+ on 2026-07-29
  alone, each with its own adjacent `"Memory limit exceeded"` line and a genuine restart) — distinct from this doc's
  SIGABRT mystery, filed as its own fresh `[BACKEND]` todo rather than continuing to conflate the two signals. Wrote and
  ran a local repro (`/tmp/repro_exec_subprocess_sigabrt.py`, scratch/uncommitted) mirroring the exact
  `post_worker_init` disposition sequence, then `subprocess.run()`-spawning a genuinely EXEC'd child that `os.abort()`s:
  reproduces every observed signature exactly (child `returncode=-6`, zero stdout/stderr — POSIX resets signal
  dispositions on `exec()`, so the armed `faulthandler` in the parent is never inherited by an exec'd child — and the
  parent/container is completely unaffected). `deployment_api/` has 15+ `subprocess.run()`/`Popen` call sites; none of
  the 3 fresh occurrences correlate with a non-`/health` request nearby, so the trigger (if this theory holds) is most
  likely background/scheduled, not request-triggered — filed a narrower follow-up `[BACKEND]` todo to find the specific
  call site and add signal-exit instrumentation so the next occurrence self-attributes without needing a gVisor-side
  dump. Not flipping this checkbox: the doc-wide root cause remains genuinely open (the exec-subprocess theory is
  evidence-consistent, not yet directly confirmed against production — no code shipped this session, this was
  investigation + a local repro only, per this doc's own established evidentiary bar of "faithful repro over
  log-archaeology or re-guessing").

- **2026-07-30T13:06Z (slot 16, review)** — Dispatched `deployment_api_sigabrt_crash_loop-005` (this `[REVIEW] P2` todo,
  13th+ dispatch). Fresh-pulled all slot repos first. Re-verified from scratch rather than trusting the 21min-old 12:45Z
  entry: (1) `git log --since="2026-07-30 12:09" -- cloudbuild.yaml gunicorn.conf.py deployment_api/` on
  `origin/live-defi-rollout` — zero new commits, so the fresh `[BACKEND] P2` sandbox-external-termination todo still
  hasn't shipped; (2) `gcloud run revisions list` shows a NEW revision since the last check —
  `uts-shared-deployment-api-00340-hwl` (created `12:54:40Z`, 100% traffic) — confirmed via direct annotation inspection
  (`gcloud run revisions describe ... --format=json`) that it still carries
  `run.googleapis.com/execution-environment=gen1`; traced the pin's full live window back to `00333-p62` (`06:26:01Z`),
  so gen1-pinned observation is now ~6h40m across 8 revisions (`00333`-`00340`); (3) `gcloud logging read` for
  `"Uncaught signal"` over the last day: still only the same 2 post-pin occurrences already catalogued
  (`00337-lrr@09:05:15Z`, `00338-4qv@11:17:37Z`) — zero new SIGABRTs in the ~1h48m since the last one (not itself
  conclusive — well within previously observed quiet gaps during confirmed-broken periods). Nothing material changed
  since 12:09Z's determination. Per this checkbox's OWN literal done_definition (monitor the rate post-gen1-pin; if it
  continues, say so and check the named pyarrow candidate — both already done with evidence at 12:09Z, refuted, and
  superseded by a fresh `[BACKEND]` todo), the negative branch is conclusively established and has been for over an hour
  with no new information. Flipped the checkbox (see inline `CLOSED` note above) rather than releasing via
  `skip-current-task` for a 13th time — the literal ask here is answered; continuing to re-verify an unchanged fact
  every dispatch is the stochastic-external-event-polling anti-pattern CLAUDE.md's async-wait/poll-discipline HARD RULE
  flags, not real progress. The doc-wide root-cause question (what actually causes the SIGABRT) remains genuinely open —
  tracked under the `[BACKEND] P2` sandbox-external-termination todo, not this one. No code shipped (pure verification +
  doc reconciliation).

- **2026-07-30T12:45Z (slot 8, review)** — Re-dispatched `deployment_api_sigabrt_crash_loop-005` (this `[REVIEW] P2`
  todo, 12th+ dispatch) — same slot's own prior check (12:09Z entry immediately below, 36min ago). Re-verified both
  facts fresh rather than trusting the recent memory: (1)
  `git log -- cloudbuild.yaml deployment_api/gunicorn.conf.py gunicorn.conf.py deployment_api/main.py` on
  `origin/live-defi-rollout` shows no new commit since `acdd4c8` (the gen1 pin) — the newly-filed `[BACKEND] P2`
  sandbox-external-termination todo has not shipped; (2) `gcloud run revisions list` confirms
  `uts-shared-deployment-api-00339-dw7` (created `11:39:33Z`) is still the live revision, unchanged; (3)
  `gcloud logging read` for `"Uncaught signal"` since `2026-07-30T11:17:00Z` returns only the same already-catalogued
  `00338-4qv@11:17:37Z` row — zero new occurrences in the 88min since. Neither precondition branch advanced. Not
  flipping the checkbox (unchanged from 12:09Z). Releasing via `skip-current-task` (`reason_code: GATED`) per this doc's
  own established pattern (13th+ consecutive dispatch to hit the same unmet, stochastic-external-event precondition) —
  the actionable next step remains the BACKEND-scoped Cloud Monitoring investigation filed at 12:09Z, not a REVIEW
  re-check.

- **2026-07-30T12:09Z (slot 8, review)** — Re-dispatched `deployment_api_sigabrt_crash_loop-003` (this `[REVIEW] P2`
  todo, 11th+ dispatch). This time BOTH preconditions are met: (1) confirmed via DIRECT annotation inspection
  (`gcloud run revisions describe ... --format=json`, not source-diff) that the gen1 pin IS live —
  `run.googleapis.com/execution-environment=gen1` present on the current serving revision
  `uts-shared-deployment-api-00339-dw7` (100% traffic, created `11:39:33Z`); traced back through the revision history to
  find the pin first appeared on `00333-p62` (created `2026-07-30T06:26:01Z` — `00332-8gl` immediately prior has no
  execution-environment annotation at all). So the gen1-pinned observation window is `06:26:01Z`→now, ~5h43m across 7
  revisions (`00333`-`00339`). (2) `gcloud logging read` for `"Uncaught signal"` over that window found **2 fresh
  occurrences**: `00337-lrr@2026-07-30T09:05:15Z` (pid=29) and `00338-4qv@2026-07-30T11:17:37Z` (pid=29) — **the gen1
  pin did NOT fix it**, per this todo's own explicit decision branch. Checked stderr ±5min around both: zero
  faulthandler dumps, same as every prior occurrence (12 total now cataloged across this doc's history). Per the todo's
  own instruction ("do not re-guess — check whether [pyarrow hypothesis]"), investigated the named leading candidate
  with a FAITHFUL LOCAL REPRO rather than more log archaeology: armed `faulthandler.enable()` after resetting SIGABRT to
  `SIG_DFL` (exact `post_worker_init` ordering), forked a child via `ProcessPoolExecutor(mp_context="fork")` (mirroring
  `build_category_in_subprocess`), imported `pyarrow`+`pandas` for the FIRST TIME in that child (mirroring the
  lazy-import timing this hypothesis depends on), then `os.abort()`ed — produced a clean, correct dump every time, with
  the fork/child stack trace intact. **This REFUTES the pyarrow/ Arrow-C++-signal-handler hypothesis** — the exact
  production code path, faithfully reproduced on the same Python/ library versions, does not exhibit the failure. Also
  re-checked the OTHER standing lead (memory-limit correlation): zero `"Memory limit"` log entries near either new
  timestamp (nearest prior event was `05:52:43Z` on an unrelated revision) — that correlation doesn't hold for these 2
  occurrences either. New but inconclusive lead: `00338-4qv`'s crash landed only ~94s after ITS instance's own
  `STARTUP TCP probe succeeded` log line — a very-fresh-instance crash — while `00337-lrr`'s crash landed ~53min
  post-startup-probe on its instance; not a consistent pattern with n=2, flagged for future tracking rather than
  asserted. Filed a fresh `[BACKEND] P2` todo above with the full evidence chain and concrete next steps (Cloud
  Monitoring raw per-instance metrics API, termination-reason audit fields) pointing toward the
  sandbox-external-termination theory as the most evidence-consistent remaining explanation by elimination — not yet
  directly confirmed. **Not flipping this `[REVIEW]` checkbox**: its original ask ("read the dump, report the stuck call
  site") remains unanswerable — there is still no dump to read, and this session's new evidence argues that no dump ever
  WILL appear via the current diagnostic approach, because the failure mode may not be a genuine in-process signal at
  all. No code shipped (pure investigation + a local repro script, not committed — `/tmp/repro_fork_pyarrow_sigabrt.py`,
  scratch only). Releasing this task via `/skip-current-task` since the actionable next step (Cloud Monitoring metrics
  investigation) is BACKEND-scoped, not a REVIEW re-check — the fresh todo above is where that continues.

- **2026-07-30T04:56Z (slot 16, review)** — Re-dispatched `deployment_api_sigabrt_crash_loop-003` (this `[REVIEW] P2`
  todo, 10th+ dispatch). Fresh-pulled all slot repos, then re-checked both precondition branches from scratch: (1)
  `deployment-api@acdd4c8` (the fresh `[BACKEND] P1` gen1-pin fix, shipped by slot 9 at `04:08:39Z`) is confirmed on
  `origin/live-defi-rollout` (`git log -- cloudbuild.yaml`) but has **NOT reached a live Cloud Run deploy** —
  `gh pr list --repo IggyIkenna/deployment-api --state open` is empty (no promote PR in flight), the last merged promote
  PR (#428) landed `2026-07-29T12:52:19Z` (before `acdd4c8` even existed), and `gcloud builds list` shows no new build
  triggered since `2026-07-29T22:07:56Z` — over 6.5h before `acdd4c8` shipped. `gcloud run revisions list` confirms the
  live revision is still `uts-shared-deployment-api-00332-8gl` (created `2026-07-30T01:09:57Z`, predates the fix by
  ~3h), 100% traffic, and actively serving (health-check requests every ~20s as of `04:56Z` — not an idle revision going
  quiet by default). (2) `gcloud logging read` for `"Uncaught signal"` scoped to this service: **zero occurrences since
  `2026-07-29T22:09:12Z`** — i.e. **~6h47m elapsed with no SIGABRT at all**, extending slot 6's `03:59Z` quiet-window
  observation (~2h49m on `00332-8gl` at that time) by a further ~3 hours with still no code change on this revision that
  would explain it (same revision, no new deploy). Neither precondition branch is met: no BACKEND fix has reached a live
  deploy yet, and no new SIGABRT has occurred to produce a dump from. The original ask ("read the dump, report the stuck
  call site, confirm/refute the `_compute_inventory` cold-path hypothesis") remains unanswerable — not a judgment call,
  genuinely not ready. Not flipping the checkbox. Releasing via `skip-current-task` (`reason_code: GATED`) per the
  established pattern (10th consecutive dispatch to hit this same unmet precondition) rather than idling the slot
  polling a stochastic external event (the next Cloud Build promote + the next SIGABRT, whichever comes first). Next
  dispatch: re-check whether `acdd4c8` has reached a live revision (via `gcloud run revisions list` creation timestamp
  vs. `04:08:39Z`, then confirm via direct image extraction of `cloudbuild.yaml`'s deploy step output or the revision's
  env, not source-diff alone per this doc's own methodology correction); once live, re-run the `"Uncaught signal"` check
  scoped to that new revision over several multiples of the ~20-40min historical cadence. If a SIGABRT recurs
  post-gen1-pin, pull `stderr` ±5min for the dump. If the quiet window holds for many hours post-deploy with sustained
  traffic, that's the strongest evidence yet for the gen1 mitigation actually working — but per this doc's own
  established caution (slot 6's note that a quiet window alone proved nothing pre-fix), still don't close this issue
  purely on absence of crashes without either a dump confirming the call site or a long enough observation window per
  the sibling `[REVIEW]` todo below this one.

- **2026-07-30T04:15Z (slot 9, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-004` (the fresh
  `[BACKEND] P1` todo). Went well beyond log archaeology this session — read the actual installed `gunicorn`/`uvicorn`
  source (confirmed same lockfile hash between this slot's clone and the root clone's populated `.venv`, so read that
  directly rather than `uv sync`ing a fresh one) and gVisor's own sentry source to get ground-truth mechanics instead of
  re-guessing from log patterns alone.
  - **Angle (1) — sys.stderr fd rebind — MOOT.** Grepped `deployment_api/` for any `sys.stderr =`/`sys.stdout =`/
    `CloudLoggingHandler`/`StructuredLogHandler` — none found; `logging.basicConfig()` only attaches a `StreamHandler`,
    doesn't touch the stream object itself. This turned out to be moot regardless — see below.
  - **Angle (2) — sandbox-kill vs arbiter — the arbiter half is DEFINITIVELY REFUTED, not just weakened.** Pulled
    `gunicorn/arbiter.py` directly: `murder_workers()` calls `self.log.critical("WORKER TIMEOUT (pid:%s)", pid)`
    (line 504) SYNCHRONOUSLY, immediately BEFORE `self.kill_worker(pid, signal.SIGABRT)` (line 506) — this critical log
    is unconditional on that code path, no branch skips it.
    `gcloud logging read '"WORKER TIMEOUT" AND resource.labels.service_name="uts-shared-deployment-api"' --freshness=30d`
    (all log streams, not stream-restricted) returns **ZERO rows**, despite 106+ historical SIGABRTs plus the 8
    post-`3fea307` ones this doc already catalogued, and despite gunicorn's own stderr pipeline confirmed reaching Cloud
    Logging for OTHER lines (the 2026-07-24 entry's unrelated `CancelledError` traceback). This is a clean,
    unconditional refutation — not "weakened," which is how the hypothesis had been treated since 2026-07-24 — of the
    theory that's motivated this issue doc's diagnostic work from the start. Whatever sends these SIGABRTs, it is not
    gunicorn's arbiter.
  - **Read gVisor's sentry source directly** (`google/gvisor`'s `pkg/sentry/kernel/task_signals.go`, via
    `gh api search/code` to locate it then fetched via raw GitHub) to understand what "Uncaught signal: N, pid=X, tid=X,
    fault_addr=0" actually means at the mechanism level — this line was never a gunicorn/Python log line at all, it's
    gVisor's own `deliverSignal()`. The `UncaughtSignal` event/log ONLY fires on the
    `SignalActionTerm`/`SignalActionCore` branch of `computeAction(sig, act)` — i.e. only when the tracked signal
    disposition (`act.Handler`) resolves to `SIG_DFL` at the moment of delivery. A signal with a real registered handler
    takes the `SignalActionHandler` branch instead and would never produce this log line — meaning IF `faulthandler`'s
    handler were genuinely still armed when a SIGABRT actually arrived, we should see NO "Uncaught signal" line at all
    (we'd instead see either a dump or total silence-then-restart), not a dump-less "Uncaught signal" line. This
    directly resolves angle (1) as moot: stderr-fd state is irrelevant if the handler path is never entered to begin
    with.
  - **Empirically verified the fix's ordering is correct in isolation** (didn't just trust the prior sessions' code
    read): wrote a local repro mimicking the EXACT sequence — reset every `Worker.SIGNALS` entry (incl. SIGABRT) to
    `SIG_DFL` (mimicking `UvicornWorker.init_signals`), then `faulthandler.enable()` (mimicking `post_worker_init`),
    then `os.kill(self, signal.SIGABRT)`. Result: full `Fatal Python error: Aborted` dump with the correct frame,
    process exit 134. So the Python-level fix (`deployment-api@3fea307`) is proven correct in isolation on real Linux —
    this isn't a bug in the fix itself. Also read `multiprocessing/process.py`'s `_bootstrap()` and
    `concurrent.futures/process.py` directly (stdlib, via the venv's own python) to rule out fork-bootstrap resetting
    SIGABRT for `ProcessPoolExecutor`/`multiprocessing` children — neither touches signal state at all.
  - **New leads, both flagged honestly as leads, not proven causes**: (a) `gcloud logging read` for `"Memory limit"`
    shows `uts-shared-deployment-api-00331-wzz` (the revision carrying 6 of the 8 post-fix SIGABRTs) exceeded its 16384
    MiB limit 6× on 2026-07-29 (16513-17004 MiB used each time) — temporal correlation to the SIGABRT timestamps is WEAK
    (only 2 of 8 within ~20-30min of an OOM event; the rest are hours apart), so NOT asserted as the proven cause, but
    it does confirm the service runs chronically close to its memory ceiling. (b) Cross-referencing this repo's OWN
    `cloudbuild.yaml` surfaced a directly relevant, already-litigated precedent: the retired `${_ROLLUP_JOB}` Cloud Run
    Job's comment states verbatim "Cloud Run Jobs are gen2-only and the native pyarrow/pandas compute crashes on gen2
    (R7 follow-up #4); the gen1 service runs it fine." `deployment_api/services/data_status/manifest.py`'s
    `_dispatch_category_builds` runs the SAME class of native pyarrow/pandas compute via a
    `multiprocessing.get_context("fork")` `ProcessPoolExecutor` (`build_category_in_subprocess`), and it's reachable
    from the MAIN service's `GET /api/data-status/manifest` route (`deployment_api/routes/data_status/_status_core.py`),
    not just the isolated rollup path. Checked whether `uts-shared-deployment-api` has an explicit
    `--execution-environment` pin: it did NOT (`cloudbuild.yaml`'s `gcloud run deploy uts-shared-deployment-api` had no
    such flag) — confirmed via the Cloud Run Admin API v2 directly (`GET .../services/uts-shared-deployment-api`) that
    neither the service spec nor the live revision echo a resolved `executionEnvironment` value when it's unset, so I
    could NOT conclusively determine which environment is actually running today. The sibling rollup SERVICE is already
    proven safe for this exact code shape (per the same comment) — but querying its live config the same way ALSO
    returned no explicit value, so even that precedent's "gen1" description isn't independently re-verifiable via the
    API today; treating the cloudbuild.yaml comment as the source of truth for that service's proven-safe history.
  - **Shipped**: `deployment-api@acdd4c8` (`cloudbuild.yaml`) — added `--execution-environment gen1` to
    `uts-shared-deployment-api`'s deploy command, matching the sibling rollup service's documented-safe pattern. This is
    a MITIGATION shipped on strong-but-circumstantial evidence, explicitly not claimed as a 100%-confirmed root cause —
    the doc and the new `[REVIEW]` todo both say so. It's cheap, reversible (a one-line revert), and has zero
    functional/perf cost regardless of whether the current default already happens to resolve to gen1. Full reasoning
    documented inline in the cloudbuild.yaml comment for the next reader. Added a `[REVIEW]` todo to monitor the
    post-deploy SIGABRT rate and, if unchanged, pursue the next-ranked candidate (a native pyarrow/Arrow-C++
    fatal-signal-handler collision installed at first-lazy-import time, after `post_worker_init` already armed
    faulthandler). No `quality-gates.sh` run — YAML-only change, no Python touched; validated via
    `python3 -c "import yaml; yaml.safe_load(open('cloudbuild.yaml'))"`.

- **2026-07-30T03:59Z (slot 6, review)** — Re-dispatched `deployment_api_sigabrt_crash_loop-003` (this `[REVIEW] P2`
  todo, 7th+ dispatch). Re-checked both precondition branches: (1) `git log -- deployment_api/gunicorn.conf.py` /
  `gunicorn.conf.py` / `deployment_api/main.py` on `origin/live-defi-rollout` shows no new commit since `3fea307` — the
  fresh `[BACKEND] P1` todo (diagnose why faulthandler produces zero dumps) has NOT shipped yet; (2)
  `gcloud run revisions list` confirms `uts-shared-deployment-api-00332-8gl` (created `2026-07-30T01:09:57Z`) is still
  the live revision, 100% traffic, and actively serving requests (`run.googleapis.com%2Frequests` entries every ~1-2min
  as of `03:59Z`) — so this isn't an idle/unused revision going quiet by default. `gcloud logging read` for
  `"Uncaught signal"` scoped to `00332-8gl` specifically: **zero occurrences**, meaning **~2h49m with no SIGABRT at all
  on this revision** (deploy `01:09:57Z` → check `03:58Z`), and **~5h49m since the last SIGABRT anywhere**
  (`00331-wzz`'s `2026-07-29T22:09:12Z`, the most recent of the 8 confirmed post-`3fea307` occurrences slot 13
  catalogued). This quiet window is substantially longer than any gap previously observed even during a
  CONFIRMED-still-broken period (slot 5's `07:08Z` entry found 50-71min gaps mid-crash-loop, so a sub-2h window alone
  wouldn't be conclusive — but ~2h49m/5h49m is well past that precedent). **Not asserting this as "fixed"** — no code
  changed between `00331-wzz` and `00332-8gl` that touches signal handling or the `_compute_inventory` cold path (the 3
  intervening commits, `5783a5b`/`b364ea9`/`e23328d`, are a reap-tick endpoint, resource-history endpoints, and a
  version-coherence panel — none plausibly related), so if the crash rate has genuinely dropped it's not attributable to
  any shipped fix and could just be traffic-pattern variance; flagging as an observation for whoever picks this up next,
  not a conclusion. Neither precondition branch is met (no BACKEND fix shipped, no new SIGABRT to read a dump from) —
  the original ask ("read the dump, report the stuck call site") remains unanswerable. Not flipping the checkbox.
  Releasing via `skip-current-task` (`reason_code: GATED`) per the established pattern (slots 4/10×2/2/5/8/13 all hit
  this same unmet-precondition wait and released the same way) rather than idling the slot on a stochastic external
  event.

- **2026-07-30T03:34Z (slot 13, review)** — Dispatched `deployment_api_sigabrt_crash_loop-003` (the `[REVIEW] P2` todo,
  now its 6th+ dispatch). Did NOT just re-check "is the fix live" (already established) — went further and checked
  whether it's actually WORKING as a diagnostic. Confirmed via `gcloud run revisions list` the current live revision is
  `uts-shared-deployment-api-00332-8gl` (created `2026-07-30T01:09:57Z`, 100% traffic). `gcloud logging read` for
  `"Uncaught signal"` over the last 5 days turned up 8 occurrences across 3 revisions: `00317-zmv`
  (`2026-07-28T03:39:17Z`, ×1), `00330-tth` (`2026-07-28T19:51:14Z`, ×1), `00331-wzz`
  (`2026-07-29T03:46:52Z`/`04:59:17Z`/`11:04:57Z`/`13:14:12Z`/ `18:21:52Z`/`22:09:12Z`, ×6). Directly `docker pull`ed +
  extracted `/app/gunicorn.conf.py` (the ACTUALLY-loaded file, not the dead duplicate — per this doc's own 2026-07-25
  correction) from BOTH the `00331-wzz` image (`sha256:8c517191ab...`, same digest as `00330-tth`) and the current
  `00332-8gl` image (`sha256:b18f1bad83...`): both have `3fea307`'s real fix — `faulthandler.enable()` correctly placed
  in `post_worker_init`, nothing in `post_fork`. So the "fix isn't actually armed" explanation (the 2026-07-25 finding)
  is now RULED OUT for these 8 occurrences. Yet pulling `run.googleapis.com%2Fstderr` in a ±5min window around EACH of
  the 6 `00331-wzz` timestamps (and the 1 `00330-tth` timestamp) returns **zero rows every time** — no
  `Fatal Python error`/`Current thread` faulthandler dump anywhere. Ruled out "stderr just doesn't reach Cloud Logging
  for this revision" as the explanation: a genuine unrelated Python traceback (from `lifespan.py`'s
  `_cancel_background_tasks` → `background_sync.py`'s `auto_sync_running_deployments`) DID land on `00331-wzz`'s stderr
  stream at `2026-07-29T15:30:15Z` — stderr delivery works, it's specifically the SIGABRT dump that's absent. This is
  new, stronger evidence than the 2026-07-25 sessions had (that session couldn't rule out "fix not armed"; this session
  did, on two separate revisions, and the dumps still don't appear). Did NOT close the `[REVIEW]` checkbox — its actual
  ask ("read the dump, report the stuck call site") remains unanswerable with zero dumps in hand. Filed a fresh
  evidence-backed `[BACKEND]` P1 todo above with the two leading candidate angles (a `sys.stderr`/fileno rebind hazard
  from `main.py`'s `logging.basicConfig()`, vs. the SIGABRT originating from the Cloud Run/gVisor sandbox supervisor
  itself rather than gunicorn's in-process arbiter — the latter would mean no in-process fix could ever produce a dump)
  — both explicitly flagged as unconfirmed, not asserted. No code shipped this entry (pure investigation); this doc's
  edit is the only change.

- **2026-07-25T11:56Z (slot 8, review)** — Dispatched `deployment_api_sigabrt_crash_loop-001` (this todo). Re-checked
  before closing: the todo's own instruction is "confirm live, read the next dump, branch below" — both halves were
  already fully executed by slot 10 at `05:25Z` (confirmed `1adf54b` live since `02:51:26Z` via content-diff, read the
  actual next occurrence at `04:27:19Z`, found no dump, and — per the todo's own "if not, do not re-guess" instruction —
  filed the fresh evidence-backed BACKEND todo, which then shipped as `deployment-api@7ba17e2`). The checkbox had simply
  never been flipped despite the branch being complete. Re-verified nothing has regressed since:
  `gcloud run revisions list` still shows `uts-shared-deployment-api-00275-7zl` (built `06:13:08Z`, carries `7ba17e2`'s
  `post_worker_init` fix) as the current serving revision, matching slot 5's `07:08Z` note — no new information changes
  this specific todo's already-satisfied done-when. Flipping the checkbox to close out the stale bookkeeping; the
  ONGOING question of whether the `post_worker_init` fix actually stops the crash-loop (reading the next dump once one
  appears) is tracked separately under `deployment_api_sigabrt_crash_loop-003` (line ~154 below), not duplicated here.
  No code shipped this entry (pure doc reconciliation).

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
  [deployment_promote_squash_ancestry_false_negative_2026_07_25.md](/plans/archive/issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md).
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
  image tag moves off `273c951`. **[PM] RETAGGED 2026-07-28 (workspace stale-gate audit) — MOOT, never hand-tuned.**
  Superseded 9 minutes later by slot 10's `05:25Z` entry below (chronologically after this reply, listed above it in
  this reverse-chronological log), which answered the exact same "is `1adf54b` live" question directly via content-diff
  instead of the ancestor check this hand-tune gate was keyed on — `git merge-base --is-ancestor` is structurally
  incapable of returning true post-squash-merge (see
  `/plans/archive/issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md`). No `prereqs.prerequisites`
  hand-tune was ever made; by `05:40Z` the doc had already moved on to a different, later precondition (waiting for the
  next SIGABRT to actually produce a faulthandler dump). No operator action remains outstanding on this line. (2)
  [BACKEND] P2 — make `PlanRegenLoop`/dispatch skip re-offering a task whose worker returned
  "external-precondition-unchanged" (a cooldown or a worker-reported not-ready signal), so this waste-class self-limits
  without a per-task hand-tune. Until then the re-dispatch is wasteful-not-harmful (worker fast-returns on the unchanged
  precondition; no corruption).
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

> **2026-07-31 line-cap remediation (3rd pass)**: the `-003`/`-016`/`-017`(×3)/`-018` entries below extracted verbatim
> from the active doc (was at 1063/1000 lines after the `e8ce86a`-rollout-refutation write-up). New entries append to
> the active doc's own Progress Log section going forward, not here — this file is a historical dump only.

- **2026-07-31T13:22Z (slot 6, review)** — Dispatched `deployment_api_sigabrt_crash_loop-003`, this doc's original
  2026-07-24 `[REVIEW]` ask (read the faulthandler dump, report the stuck call site, confirm/refute
  `_compute_inventory`). Fresh `gcloud logging read` found a previously-uncatalogued 9th confirmed post-fix occurrence
  (`00355-z2c@2026-07-31T10:37:56Z`, pid=457) — pulled its stderr window: zero entries, same as every other occurrence.
  9/9 confirmed-armed post-fix SIGABRTs now show zero dumps. Flipped this checkbox on the confirmed-negative branch: the
  literal ask can never be completed as originally framed because no dump has ever existed to read, and the doc's own
  parallel investigation chain (exec-subprocess theory refuted, sandbox-external-termination confirmed for a genuine
  low-pid subset, the distinct OOM/SIGKILL issue already fixed) has moved past the single-readable-call-site framing
  entirely. Re-verified the live successor todo (`-014`, MASTER/WORKER pid-role logging) is still correctly open: zero
  SIGABRTs on either `00361-qqp` or the current `00362-xzb` (both confirmed carrying `785405d`'s pid-role logging) as of
  this check. No code shipped (review role; pure investigation + doc reconciliation).

- **2026-07-31T13:29Z (slot 9, review)** — Dispatched `deployment_api_sigabrt_crash_loop-017` (the `-014` MASTER/WORKER
  pid-role-logging follow-up, this doc's live successor question). Re-checked live: a newer revision has since deployed
  (`00363-nwx`, `13:23:29Z`, now 100% traffic) — content-verified (direct image pull, not ancestry) it carries
  `785405d`'s pid-role logging. `gcloud logging read` for `"Uncaught signal: 6"` scoped to
  `timestamp>="2026-07-31T11:54:00Z"` (spanning `00361-qqp`→`00362-xzb`→`00363-nwx`, ~1h36m elapsed since the
  pid-role-logging deploy first went live) returns zero rows; cross-checked the query syntax against the known
  `00355-z2c@10:37:56Z` occurrence in the same session to rule out a false-negative empty result. Gate still not met —
  left the checkbox open per its own instruction, no conclusion forced from zero data. No code shipped.

- **2026-07-31T14:44Z (slot 8, review)** — Dispatched `deployment_api_sigabrt_crash_loop-016` (monitor whether
  `ec1f635`'s catalogue-lifecycle concurrency guard drops the SIGKILL/OOM rate). Content-verified `ec1f635` is live on
  the current 100%-traffic revision (`00369-xkn`, direct image extraction). `gcloud logging read` for
  `"Container terminated on signal 9"` since the fix commit (`10:55:17Z`) found 2 occurrences (`00358-vj6@11:32:13Z`,
  `00363-nwx@13:41:06Z`) — extracted `catalogue_lifecycle.py` from BOTH exact deployed image digests and confirmed the
  guard is genuinely present in each, ruling out "stale pre-fix image." 2 confirmed SIGKILLs on guard-carrying revisions
  within ~3.5h of first fix deploy is real recurrence, not a premature call — flipped the checkbox on the "guard did NOT
  fix it" branch and filed a fresh `[BACKEND] P2` todo carrying the guard todo's own two next-ranked candidates
  (`prediction_catalogue.py`'s unguarded parquet read; `manifest.py`'s `_dispatch_category_builds` ProcessPoolExecutor
  path) forward, plus a request-log-correlation step to narrow between them rather than guessing. No code shipped
  (review role; pure investigation + doc reconciliation).

- **2026-07-31T14:48Z (slot 15, review)** — Re-dispatched `deployment_api_sigabrt_crash_loop-017` (same recurring
  MASTER/WORKER pid-role-logging gate check). Traffic has since moved to `00368-lc2` (created `14:24:41Z`, confirmed
  100% via `gcloud run services describe`). Direct image extraction (`docker create`/`docker cp` off the exact digest)
  re-confirmed both pid-role log lines are present in the deployed `gunicorn.conf.py`. `gcloud logging read` for
  `"Uncaught signal: 6"` scoped to `timestamp>="2026-07-31T11:54:00Z"` (~2h54m elapsed, 8 revisions
  `00361-qqp`..`00368-lc2`) is still zero rows; cross-checked against the known `00355-z2c@10:37:56Z` occurrence to rule
  out a false negative. Gate still not met — left the checkbox open, no code shipped (pure verification).

- **2026-07-31T15:01Z (slot 15, backend_engineer)** — Dispatched `deployment_api_sigabrt_crash_loop-018` (audit
  `prediction_catalogue.py` + `manifest.py`'s ProcessPoolExecutor path as the next-ranked SIGKILL/OOM candidates). Read
  both modules directly, then ran the todo's own named request-log-correlation step against each exact crashing revision
  (`00358-vj6`, `00363-nwx`), both a tight post-crash window and a wide 35-70min pre-crash window — zero requests to
  either `/prediction-catalogue` or `/data-status/manifest` in any window checked, genuinely refuting both candidates
  for these 2 occurrences (not just "unconfirmed"). Instead found both crashes preceded 60-120s earlier by the SAME
  pattern: a `referer: .../cockpit` browser burst hitting 5-7 concurrent slow (0.8-83s) dashboard-panel endpoints
  (`/api/deployments/umbrella/*/summary`, `/api/vm-deployments`, `/api/deployments/inventory`, `/api/health/overview`,
  `/api/repo-ci/overview`) — none guarded against concurrent execution (`RateLimitMiddleware` is requests/minute only).
  Traced the shared `_load_inventory`/`_compute_inventory` seam and found it already has a 1-worker-pool + in-flight
  dedup guard, so it looks unlikely to be the dominant driver on its own. Double-checked (not over-read) a suspicious
  `/api/health/overview` 500-at-76s data point — full log entry shows it completed ~0.9s before the SIGKILL with no
  accompanying error trace, most consistent with a severed-connection casualty of the OOM-kill rather than its cause.
  Flipped the checkbox (its own literal ask — audit + correlate — is answered) and filed a fresh, narrower
  `[BACKEND] P2` todo carrying the concrete finding forward: profile which burst-cluster handler(s) actually dominate
  memory before adding any concurrency guard, rather than guessing scope on dashboard-serving production code. No code
  shipped (pure investigation, evidence-based via direct GCP log queries).

- **2026-07-31T15:15Z (slot 8, review)** — Re-dispatched `deployment_api_sigabrt_crash_loop-017` (same recurring
  MASTER/WORKER pid-role-logging gate check). Traffic moved twice during this check (`00370-k95` → `00371-xxq`, created
  `15:09:26Z`, confirmed 100% via `gcloud run services describe`). Direct image extraction (`docker create` +
  `docker cp` off the exact digest) re-confirmed both pid-role log lines are present in `00371-xxq`'s deployed
  `gunicorn.conf.py`. `gcloud logging read` for `"Uncaught signal: 6"` scoped to `timestamp>="2026-07-31T11:54:00Z"`
  (~3h21m elapsed, 11 revisions `00361-qqp`..`00371-xxq`) is still zero rows; cross-checked against the known
  `00355-z2c@10:37:56Z` occurrence to rule out a false negative. Note for future dispatches: the active `gcloud` account
  (`github-deploy`) lacks Logging Viewer on this project (`PERMISSION_DENIED`) —
  `--account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (already-credentialed, no new grant
  needed) has the role and is what this check used. Gate still not met — left the checkbox open, no code shipped (pure
  verification).

---

## 4th-pass extraction (2026-07-31, slot 14) — checklist entries, not just Progress Log

Two fully-resolved (✅) checklist entries extracted verbatim from the live doc to bring it back under the 1000-line hard
cap (it had reached 1001 lines). Both are closed, evidence-backed findings superseded by later todos already summarized
on the live doc; nothing here is still-open tracked work.

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

- [x] ✅ [BACKEND] P1. **NEW, opened 2026-07-31 (slot 4, backend_engineer) — pin the exact call site for the
      truncated-sync-HTTPS-traceback-then-permanent-silence pattern found in the todo above and confirm/refute it as the
      blackout trigger.** (1) cross-reference `run.googleapis.com/requests` for instance `001548f729ad...` (`00353-dng`)
      in a ±5s window around `08:40:27Z` to find the exact route/URL, pinning which of the 6 sync-HTTPS call sites
      fired; (2) check whether that call site's `requests`/`AuthorizedSession`/`fetch_id_token()` call has no explicit
      socket `timeout=` (an indefinite hang matches "never completes, never logs the rest"); (3) check whether this same
      4-fragment-then-silence signature recurs at other points in this service's history (independent of the gen1 pin) —
      recurrence strengthens this theory, a one-off weakens it. Done-when: call site identified AND either a fix ships
      (add `timeout=`, or move the call off the event loop via `run_in_threadpool`) with stdout/stderr confirmed
      resuming, or the theory is refuted with evidence (not re-guessed). (repo: deployment-api) —
      `deployment-api@6e7bf27`. (1) pinned exactly: `POST /api/internal/reap-tick@08:40:00.582Z`, latency **27.25s**,
      status **500**, completing `08:40:27.83Z` — matches the traceback to the ms. Call site: `_reap_scheduler.py`'s
      `verify_reap_scheduler_oidc` → `google_id_token.verify_oauth2_token()`. (2) has an effective 120s default — real
      bug: a raw SSL/socket exception escapes both `GoogleAuthError` and this file's narrow
      `except (GoogleAuthError, ValueError)`. **Shipped**: `asyncio.to_thread` wrap + broadened except → clean 503
      instead of unhandled 500. 8 new tests, green; QG PASSED. (3) not run. Still unexplained: why would one request
      blind ALL subsequent revisions — added a `[REVIEW]` follow-up below.

- [x] ✅ [REVIEW] P2. **NEW, opened 2026-07-31 (slot 4) — once `deployment-api@6e7bf27` (todo above) reaches a live
      Cloud Run deploy, check whether `stdout`/`stderr` entries resume for `uts-shared-deployment-api`.** Verify the
      deploy via direct image extraction (not ancestry), then `gcloud logging read` for `stdout`/`stderr` scoped to
      `timestamp>=<deploy-time>`. Resume → this fix was the trigger, update this doc's framing. Persists → re-open with
      a fresh evidence-backed todo (why does one request's failure affect ALL subsequent instances, not just the one it
      happened on) rather than re-guessing. (repo: deployment-api) — **ANSWERED (slot-6)**: PERSISTS on unrelated
      instances too, `6e7bf27` worthwhile but not the full explanation.

- [x] ✅ [BACKEND] P1. **NEW, opened 2026-07-31 (slot-6) — test whether `--execution-environment gen1` (suspected twice)
      is the blackout's mechanism.** — **DONE, REFUTED**: `deployment-api` is the ONLY gen1 service in the region (cited
      rollup precedent is actually gen2 live); a zero-traffic gen2 canary (same image) still produced zero stdout. Test
      revisions cleaned up (live traffic stayed on gen1 throughout). (repo: deployment-api)

- [x] ✅ [BACKEND] P1. **DONE 2026-07-31 (slot 8) — `deployment-api@e8ce86a`. Both named candidates REFUTED by 4 live
      canary experiments; found + fixed the REAL root cause.** (Slot-6 independently ran the same bare-interpreter
      canary concurrently and reached the identical refutation — corroborating, not conflicting; this entry carries the
      investigation the rest of the way to the actual root cause + fix.) Deployed 4 zero-traffic canaries on
      `uts-shared-deployment-api` overriding `--command`/`--args` to bypass tini+gunicorn+app entirely: (1) bare
      `--command=python3` print loop → zero stdout, refuting BOTH named candidates (no `preload_app`, no app import at
      all); (2) same + `--no-cpu-throttling` → still zero, ruling that out too; (3) a structured
      `{"severity":"ERROR",...}` JSON line on stdout → **appeared**; (4) same at `severity=INFO` → **appeared**. Root
      cause: Cloud Run stamps `severity=DEFAULT` (0) on any non-JSON-structured stdout/stderr line, and this project's
      `_Default` Cloud Logging sink excludes `severity <= "DEBUG"` (100) for cost control — silently dropping every
      plain-text line this service ever wrote (gunicorn hooks, faulthandler dumps, this app's own
      `logging.basicConfig()`), regardless of what the app logged. **Fixed**: `main.py` now calls
      `unified_trading_library.setup_cloud_logging()` (its `CloudRunJSONFormatter` already emits GCP-recognized JSON
      with an explicit `severity`, surviving the exclusion at INFO+). 3 new tests (`test_main_logging_bootstrap.py`) pin
      the regression; `quality-gates.sh` PASSED; verified on origin. Cleaned up 6 of 7 stray canary revisions (incl. the
      pre-existing `00375-yic`); the 7th (`00382-cat`) is the Cloud-Run "latest" pointer and can only be deleted once a
      real deploy supersedes it — tracked in the REVIEW todo below. (repo: deployment-api)

## 5th-pass extraction (2026-07-31T22:57Z, slot 7) — checklist entries

> Extracted verbatim (line-cap remediation, live doc was at 1007/1000 lines after the cold-container-recovery write-up).
> These are the oldest 7 checked checklist entries (the original 2026-07-24 root-cause dispatch through the
> 2026-07-30T12:09Z sandbox-external-termination-theory entry) — all fully superseded by this doc's own later findings
> (stdout/stderr blackout root cause, the cold-container-startup P0, and the OOM/SIGKILL sub-issue), which is why they
> were safe to extract.

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

---

## 6th-pass extraction (2026-08-11, slot 18, line-cap remediation)

Extracted from `deployment_api_sigabrt_crash_loop_2026_07_24.md` Progress Log — all fully resolved.

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
  4th-pass line-cap remediation (doc was at 1001/1000 lines) extracting 6 more fully-resolved checklist entries to the
  same archive file. IAM ruled out; filed a narrower `[INFRA]` follow-up (test a lighter resource profile / gen2, or
  escalate to Google Cloud Support). Left the IAM grant + diagnostic sink live for the next investigator. Production
  safe throughout (`00374-4pd` still serving 200s). No code shipped — pure infra/IAM investigation + doc reconciliation.

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
