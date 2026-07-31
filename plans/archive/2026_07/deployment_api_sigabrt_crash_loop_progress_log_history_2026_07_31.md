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
