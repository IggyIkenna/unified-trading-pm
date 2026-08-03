---
doc_type: issue
title:
  "pytest-timeout-under-contention bug class continues (original doc at 1000-line hard cap) — unified-trading-api's 5th
  occurrence in one day, this time fixed with a repo-local mitigation rather than left as noise"
summary: >-
  Continuation of `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` (996/1000 lines, its
  own last entry already flagged "next occurrence MUST split/archive, not append"). `cicd` escalation `agt-bde7b9`
  (`WALL_TYPE=ldr_qg_failure`, `REPO=unified-trading-api`, slot 4) hit unified-trading-api's 5th same-day recurrence of
  this doc's flake class — 4 prior consecutive `quality-gates-v2` failures on 2026-08-02 (13:32Z/18:41Z/21:12Z/22:36Z
  runs), each via `Failed: Timeout (>150.0s) from pytest-timeout` on a DIFFERENT random subset of route tests (9-10 of
  441), all passing in well under 1s locally in isolation. Confirmed via a full local `quality-gates.sh` run at LDR HEAD
  `990187dd5` — 100% green, 441 passed, 79s — that no code/test defect exists; host corroboration at investigation time:
  `load average 24.83-29.28` on 16 vCPUs, `20Gi/47Gi` swap in active use, 23 concurrent `quality-gates.sh` processes + 7
  sibling self-hosted `glue` CI runners sharing this same physical host — matching every prior entry in the parent doc's
  "fleet-wide QG capacity crisis, not a regression" diagnosis. Unlike every prior entry (which all concluded "no action
  taken, self-clears"), this occurrence had NOT self-cleared after 4 attempts spanning 9+ hours (no green run since
  2026-07-31 10:55Z, 36+ hours prior) — so rather than a 5th blind retry, applied the parent doc's own sanctioned fix
  philosophy ("raising a wall-clock timeout to absorb scheduling variance is not weakening the check") as a repo-local,
  low-blast-radius mitigation.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-api, unified-trading-pm, features-service, market-data-processing-service]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-08-02
last_updated: 2026-08-03T10:48Z
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "cicd-role escalation agt-bde7b9 (WALL_TYPE=ldr_qg_failure, REPO=unified-trading-api, slot 4)"
context_scope:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /codex/06-coding-standards/quality-gates.md,
    unified-trading-api/scripts/quality-gates.sh,
  ]
---

# pytest-timeout-under-contention: unified-trading-api's 5th occurrence, fixed with a repo-local mitigation

Parent doc `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` is at its 1000-line hard cap
(996 lines) with its final entry explicitly noting "next occurrence MUST split/archive, not append" — this doc is that
split, not a duplicate.

## What was found + done

`cicd` escalation `agt-bde7b9` for `unified-trading-api` `ldr_qg_failure` (`PR_NUMBER=0`, no PR — direct LDR push gate).
LDR HEAD `990187dd5bdc0459e4ec3b639cfac035312be98a` (2026-08-02T12:52:43Z). CI runs `30761689446` (18:41Z, 10 tests / 9
files) and `30770482343` (22:36Z, 9 tests / 8 files) both failed via `Failed: Timeout (>150.0s) from pytest-timeout` on
a DIFFERENT random test subset each time (`test_events`, `test_defi_basis`, `test_defi_liquidation`, `test_registry`,
`test_defi_lp`, `test_strategy_performance`, `test_middleware`, `test_routes`, `test_routes_extra`, `test_catalogue`
across the two runs) — no test-content overlap, consistent with scheduler-descheduling under host contention rather than
a real hang or a per-test anti-pattern. Local reproduction at the same HEAD: `quality-gates.sh` backgrounded per the
mandatory pattern, 441/441 passed, 68-79s, zero timeouts, across 2 independent runs. Host snapshot at investigation
time: `load average: 24.83, 26.18, 29.28` (16 vCPUs — 1.5-2x oversubscribed), `20Gi/47Gi` swap in use, 23 concurrent
`quality-gates.sh` processes (`pgrep -af`), 7 concurrent self-hosted `glue` CI runner processes on the SAME physical
host. Zero open `/api/repo-blockers` entries for `unified-trading-api`.

Unlike the parent doc's prior entries (which found LDR already green by investigation time and took no action), this
repo had 4 consecutive failures with no green run in 36+ hours — the "self-clears" assumption did not hold here. Rather
than a 5th unmonitored multi-hour retry against a demonstrably still-saturated host, applied the parent doc's own
established fix philosophy as a scoped, low-risk, repo-local mitigation: `unified-trading-api@71cdda0` adds
`PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}` to the repo's own `scripts/quality-gates.sh` (before sourcing
`base-service.sh`), doubling this repo's effective budget over the shared 150s default. This changes no check's
assertion — only the wall-clock deadline the same passing tests are held to. Verified locally green post-change (68s,
441 passed) and shipped via `quickmerge --agent --files 'scripts/quality-gates.sh'`, confirmed on
`origin/live-defi-rollout` via `merge-base --is-ancestor`. Fresh `quality-gates-v2` run triggered
(`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`) — run id in the Progress Log below once observed.

## Todos

- [ ] 1. [INFRA] P3. Once the fresh post-mitigation `quality-gates-v2` run (triggered this session) completes, record
      the outcome here. If GREEN: confirms a 300s repo-local budget clears this specific severity of contention for
      unified-trading-api; consider this the template for any OTHER repo that similarly fails to self-clear (i.e., a
      per-repo `PYTEST_TIMEOUT` override is preferable to indefinite blind retries once a repo shows sustained,
      non-self-clearing red). If RED again with the same timeout signature even at 300s: this repo's host contention
      severity now exceeds what a 2x budget raise absorbs — escalate to the parent capacity-crisis doc
      (`/plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) rather than raising the
      timeout further in isolation (per that doc's own conclusion: repeatedly raising a deadline "moves the threshold,
      does not close the class").
- [ ] 2. [INFRA] P3. If todo 1 confirms the fix, consider whether other repos in the parent doc's `repos:` list with
      recurring (not just single) unified-trading-api-style sustained-red occurrences would benefit from the same
      repo-local `PYTEST_TIMEOUT` raise, rather than relying solely on retries. Not done proactively here — scope
      bounded to the one escalation this doc was filed under. **na-eligibility-audit 2026-08-03 note**:
      `features-service` already got exactly this treatment (`PYTEST_TIMEOUT=300` + `PYRIGHT_TIMEOUT=300`,
      `features-service@c092df50`, verified green — see Progress Log entries below), so this todo is partially
      addressed, but "other repos" beyond `features-service` is broader than one confirmed repo — staying open, not
      closing.

## Progress Log

- **2026-08-02 23:52Z (`cicd` `agt-bde7b9`, slot 4)** — Diagnosed, applied repo-local `PYTEST_TIMEOUT=300` mitigation
  (`unified-trading-api@71cdda0`), shipped + verified on origin, triggered fresh `quality-gates-v2` run `30773174599`.
  Filed this continuation doc (parent doc at hard cap). Outcome of the fresh run to be added once observed by this or a
  follow-up session.

- **2026-08-03 06:20-07:26Z (`cicd` `agt-4e5bc3`, slot 9, `features-service`, `wall_type=main_ci_red`, `pr_number=0`)**
  — This is todo 2's template-extension actually landing, tracked here retroactively: an earlier same-day session
  (`agt-8e5d24`, slot 2, logged in the parent doc
  `/plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) had already applied this doc's
  exact mitigation pattern to `features-service` — `PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}` AND
  `PYRIGHT_TIMEOUT=${PYRIGHT_TIMEOUT:-300}` (this repo hits both the pytest-timeout AND basedpyright-120s-ceiling
  shapes) — `features-service@c092df50`, verified locally green (338s, zero timeouts). This session picked up the same
  wall re-escalating (`main` ~428 commits behind LDR, fleet-promote gate still
  `GATE BLOCK features-service: ci_status=FAILING` because no run had yet tested `c092df50` itself — the LDR run in
  flight at fix-landing time, `30780475199`, was still testing the OLD pre-fix HEAD and never got a runner slot in
  3.5h+). Per this doc's own posture (observe before re-deriving), triggered the fresh post-mitigation observation run
  (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`, run `30790679266`) — concurrency group
  `quality-gates-v2-refs/heads/live-defi-rollout` (`cancel-in-progress: true`) correctly auto-cancelled the stale
  pre-fix run. Host corroboration: `uptime` load average `39.03, 43.52, 44.74` on 16 vCPUs (worse than every prior entry
  in this doc or the parent). Fleet-wide snapshot at 07:23Z: dozens of queued/in-progress `quality-gates-v2` runs across
  ~20 repos (not features-service-specific), several `in_progress` for 3-4h+ — confirmed via spot-check
  (`unified-api-contracts` run `30780884061`, in-progress since 03:05Z, still churning/cleaning up orphan processes at
  07:10Z) that these are genuinely progressing, not dead/hung, just severely backlogged. As of session end (~07:26Z, 51
  min after dispatch) run `30790679266` was still `queued`, never claimed a runner. **Outcome not yet observed** — left
  for a follow-up occurrence per this doc's established pattern; no further code action needed for `features-service`,
  the fix is already correct and shipped, this is purely a runner-queue-depth wait. `GET /api/repo-blockers` →
  `open: []`. Slot left clean on `live-defi-rollout` (only this doc touched this session; no code change —
  `features-service`'s fix was already shipped by the prior session).

- **2026-08-03 ~08:30Z (`cicd` `agt-637862`, slot 4, `features-service`, `wall_type=main_ci_red`, `pr_number=0`)** —
  Same wall re-escalated a 3rd time; same run `30790679266` (the prior session's dispatch) is STILL the live one — now
  `in_progress`/`queued` for 1h55m+ (started 06:35:05Z). Confirmed via direct process inspection on this shared host
  (this box IS the `glue-ip-172-31-5-118-1` runner, `172.31.5.118`) that the `tests` job's pytest (PID 208125,
  `-n 0 --timeout=300`, `--cov=features_service`) is genuinely alive and accruing CPU time (not deadlocked) but starved
  — `uptime` load `37.25, 37.60, 38.12` on 16 vCPUs, `ps aux` shows 12+ concurrent `claude` agent sessions plus 6+
  distinct per-repo self-hosted `glue` runner processes all on this one box. No `timeout-minutes` set anywhere in
  `quality-gates-v2.yml` (job or step level), so GH Actions' own ceiling is the 360min default — this run could
  legitimately churn for hours yet before GH itself would kill it. Re-confirmed no code/workflow defect: `main`'s 3
  failed `quality-gates-v2` runs today (00:10Z/01:35Z/02:55Z) are the pre-fix 150s-timeout shape exactly as diagnosed;
  LDR HEAD (`b81a6a75`, one commit after the fix) has no red run against it, only this one still-pending run.
  `ldr-to-main-promote-fleet` (ticking every ~15min, latest `30796675435` @08:15Z, success) correctly still shows
  `GATE BLOCK features-service: ci_status=FAILING` — it will auto-promote (create+merge the LDR→main PR) the moment this
  run reports green; no manual promotion action needed or taken. Did NOT re-dispatch a 4th redundant run (would only
  re-trigger the `cancel-in-progress` concurrency group and reset elapsed progress on an already-alive job with zero
  benefit — the bottleneck is host-wide runner-slot scarcity, not a stale/dead run). Took no action beyond this log
  entry; `GET /api/repo-blockers` → `open: []`. Slot left clean on `live-defi-rollout`, no code touched. Escalating to
  the operator via the authoring-slot ping that this is now a 3rd consecutive same-day escalation for the same wall with
  no forward progress in 2h — worth checking whether host-wide agent-fleet concurrency (12+ simultaneous `claude`
  sessions observed) should itself be throttled, per the parent doc's still-open finding that "repeatedly raising a
  timeout moves the threshold, does not close the class."

- **2026-08-03 09:47-10:10Z (`cicd` escalation `agt-e5e387`, slot 6, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=1064`)** — same signature, a specific worker-crash variant not yet in this doc's own entries: run
  `30790501567` (`promote/instruments-service/631fd6fc30d5`, base `main`) `QG slice (tests)` job started `07:43Z`,
  produced clean progress dots through `[85%]` (08:40:55Z) then went silent for ~13min before an xdist
  `worker_internal_error` (`Failed: Timeout (>150.0s) from pytest-timeout` firing INSIDE the SIGALRM handler while it
  tried to flush the execnet channel pipe — the handler itself blocked on I/O, so the worker died mid-signal rather than
  cleanly reporting one slow test) killed one worker at 08:53:44Z; a second, identical crash killed a second worker
  43min later (09:36:45Z); with too few workers left, `xdist/dsession.py` raised
  `RuntimeError: Unexpectedly no active workers available` and the whole slice aborted (09:44:35Z, ~2h1m wall time for a
  suite that normally takes ~60s) — `qg_red_reason=pytest`, `large_file_count=8`. Confirmed no test-content overlap
  possible to check (no individual test names survive in the non-verbose xdist crash output), but the shape — dead time
  at a random completion percentage, not a specific always-failing test — matches this doc's established
  scheduling-induced-timeout signature, not a per-test defect.

  **Reproduced locally FIRST, backgrounded per the mandatory pattern**, at LDR HEAD `d7276438` (fast-forwarded from 2
  commits behind, clean tree): `bash scripts/quality-gates.sh --no-fix` → **`✅ ALL QUALITY GATES PASSED (137s)`** —
  tests slice `5159 passed, 6 skipped, 0 failed in 60.50s`, zero timeouts, zero xdist errors. Decisive confirmation the
  code is 100% clean and the CI wall is pure host contention. Host corroboration at investigation time: `uptime` load
  average `31.90, 33.77, 32.80` on 16 vCPUs (~2x oversubscribed), swap `21Gi/47Gi` in use, 27 concurrent
  `quality-gates.sh` processes live on this shared host — the identical whole-host-thrashing signature every other entry
  in this doc-pair tracks.

  By the time this was diagnosed, PR #1064 had **already self-merged** (`mergedAt: 2026-08-03T06:31:51Z`, ~1h before the
  failing run's own `qg_red_reason` was even recorded) — the same self-merge-before-confirmatory-check-completes pattern
  this doc documents for other repos (deployment-service #672/#673, features-service #902/#919, instruments-service
  #1026/#1027/#1035). `main`'s post-merge push-triggered `quality-gates-v2` (`30795433570`) and LDR's own confirmatory
  dispatch (`30800087100`) were BOTH still `queued` (not stuck/dead, just queue-starved) at investigation time —
  `main-backmerge-to-ldr` and `Semver Agent` had already completed successfully on the promoted commit, so the real
  business outcome (code promoted to `main`, backmerged, semver-tagged) is already done, fully independent of whether
  either confirmatory `quality-gates-v2` check ever goes green.

  **Disposition: no code or workflow change made or needed.** Did not add a redundant retrigger on either branch — both
  already have a dispatch queued at investigation time, and per this doc's established posture a duplicate dispatch onto
  an already-contended runner pool doesn't help. `GET /api/repo-blockers` → `open: []`. A second, unrelated
  `instruments-service` `ldr_qg_failure` escalation (`agt-05a7fe`, `pr_number=0`) was already independently resolved
  (`still_red_past_deadline`, 05:18Z) before this session started — not touched here. Slot left clean on
  `live-defi-rollout` (fast-forwarded 2 commits, no local changes beyond this doc). Thirteenth repo-specific
  corroboration of the fleet-wide contention root cause in this doc-pair, and the first to document the specific
  worker-dies-inside-its-own-SIGALRM-handler crash mechanics rather than a plain timeout-then-clean-report.

- **context-scout 2026-08-03**: populated context_scope (4 entries).

- **2026-08-03 ~09:10-09:24Z (`cicd` escalation `agt-7784b3`, slot 5, `market-data-processing-service`,
  `wall_type=ldr_qg_failure`, `pr_number=569`)** — same bug class, a new repo: `quality-gates-v2` failed on the LDR→main
  promotion PR (`promote/market-data-processing-service/23aad425a868`, headSha `23aad42`), run `30790876831` (created
  06:38:47Z). Both slices failed: `QG slice (checks)` exit=143 after a 79-minute hang inside the repo-local
  `[6.X] PER-SHARD MEMORY REGRESSION GATE` step (runs `tests/perf/test_polars_instrument_day_memory.py` unconditionally
  after `base-service.sh` returns, regardless of LEG) — traced the exit code to `qg-host-governor.sh`'s own RAM-pressure
  watchdog (`QG_HOST_RAM_ABORT_PCT`, SIGTERM to the process tree after sustained ≥80% host RAM), NOT a pytest-timeout
  expiry (the perf test's own `--timeout=120` never even fired — the process was starved of scheduler time, not merely
  slow). `QG slice (tests)` exit=1 after a 41-minute hang ending in `PluggyTeardownRaisedWarning` /
  `OSError: cannot send (already closed?)` (pytest-xdist worker death under the same pressure) — consistent symptom of
  the same class, not a distinct defect. Host corroboration at investigation time: `uptime` load average
  `33.52, 32.00, 32.82`, `22Gi/47Gi` swap in active use, 28 concurrent `quality-gates.sh` processes — matches every
  prior entry. Confirmed no code/test defect: no commit in this repo's recent history touches
  `tests/perf/test_polars_instrument_day_memory.py` or the polars candle engine it exercises; ran the perf test in
  isolation (`.venv/bin/python -m pytest tests/perf/test_polars_instrument_day_memory.py --timeout=120 -q` after
  `uv sync`) — 5 passed in 1.99s, zero regression. Unlike the pytest-timeout-expiry shape this doc otherwise tracks,
  this specific failure mode (governor RAM-abort) is NOT fixed by raising a pytest-level timeout budget — the governor's
  SIGTERM fires independently of any in-process timeout, so no repo-local code change was applied (would be a no-op fix
  for the actual trigger). By the time of this diagnosis the promotion PR had ALREADY MERGED
  (`mergedAt: 2026-08-03T06:38:48Z`, one second after creation — branch protection evidently accepted an earlier green
  status on the same SHA lineage or an admin/automerge path; the still-running/then-failing `quality-gates-v2` check on
  the PR context completed 2h37m AFTER the merge and is now moot) — `main`'s own post-merge `quality-gates-v2` run
  (`30790880111`) was still `in_progress` at 2h45m+, and `main-backmerge-to-ldr` + `Semver Agent` had both already
  completed successfully, so nothing was actually blocked. `GET /api/repo-blockers` → `open: []`. Per this doc's own
  precedent (`agt-637862`'s "did NOT re-dispatch a redundant run — bottleneck is host-wide runner-slot scarcity, not a
  stale/dead run or code gap"), did NOT trigger a fresh `quality-gates-v2` run — the promotion is already complete and a
  new dispatch would only add to the same contention this doc tracks for zero benefit. Slot left clean
  (`market-data-processing-service` on `live-defi-rollout`, 0 commits ahead; discarded a `uv.lock` diff produced by
  local `uv sync` — not an intended change). No code shipped this session.

- **2026-08-03 ~08:35-08:55Z (`cicd` escalation `agt-a7a7b6`, slot 6, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — 4th escalation for the same wall, this time a genuinely NEW (not yet-fixed) gap found**: read
  `main`'s failing run `30780455914` (02:55Z) directly rather than re-deriving the prior entries' diagnosis. Confirmed
  the `tests` slice's failure is the already-diagnosed pre-`c092df50` 150s-pytest-timeout shape (fix already on LDR,
  pending promotion — nothing to do). But the SAME run's `checks` slice failed independently via STEP 5.91 (formula-hash
  drift gate): its output printed a clean `MATCH: 5 DRIFTED: 0 NEW: 29` (proving no real drift — verified by running
  `python -m features_service.delta_one.app.features.status_report --check-drift` locally against both `main` and LDR
  checkouts, byte-identical registry.py/calculator sources on both, both exit 0) then still failed the step ~37s after
  its last output line — this command's OWN `run_timeout 60` wrapper (a bare `python -m` invocation, NOT pytest/pyright)
  was never covered by the `PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT` raise, since it's a third, independent hardcoded timeout
  in the same file. Cross-checked a second failing run (`30777230449`) where this same step took 65s to pass —
  corroborates a step that's genuinely marginal against a 60s budget under this host's contention, not a one-off fluke.
  Applied the identical sanctioned fix philosophy: `features-service@fd84f90a` raises this specific `run_timeout 60` to
  `${FORMULA_DRIFT_TIMEOUT:-240}` (scoped, single-line, no logic change). Verified via the underlying command directly
  (not a full local `quality-gates.sh` re-run — started one, backgrounded, then killed it early: this box hosts the
  actual `glue` CI runners and running a redundant full suite would only add to the exact contention this doc tracks for
  zero new signal beyond what the isolated command already proved) and via quickmerge's own Pass-1 QG, which now shows
  STEP 5.91 passing cleanly. Verified the commit landed:
  `git merge-base --is-ancestor fd84f90a origin/live-defi-rollout` → true. Did NOT re-dispatch a fresh
  `quality-gates-v2` run on LDR — one was already `in_progress` (`30790679266`, testing older SHA `c092df50`, queued
  since 06:35Z, now finally running) and a fresh dispatch would cancel it via the concurrency group, discarding elapsed
  progress, per this doc's own established precedent. The `ldr-to-main-promote-fleet` auto-promotion will pick up
  whichever LDR SHA next reports green (any of `c092df50`/`b81a6a75`/`fd84f90a` should now pass both fixed timeouts) —
  no manual promotion action taken or needed. `GET /api/repo-blockers` → `open: []`. Slot left clean (features-service
  on `live-defi-rollout`, 0 commits ahead of `origin`; scratch worktree removed). Pinged the authoring slot
  (`ci-reconcile`) with the outcome. This is the 4th same-day escalation for this exact wall — unlike entries 2-3, this
  one found and closed an actual code gap rather than re-confirming "wait it out," so it's not pure duplication of the
  standing operator concern about agent-fleet throttling, but that concern (noted in the entry above) remains open and
  unaddressed by this entry.

- **2026-08-03 ~10:07-10:48Z (`cicd` escalation `agt-3bc731`, slot 3, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — 6th escalation for this repo's wall, and the first live confirmation of todo 1's "still red past the
  300s raise" branch (previously only anticipated, for unified-trading-api)**: `main` still red at run `30780455914`
  (02:55Z, pre-`c092df50` 150s-timeout shape, already-diagnosed/fixed on LDR — nothing new there). Checked LDR itself —
  NOT green either: latest completed run `30800328624` (09:11Z, headSha `fd84f90a`, i.e. testing the commit AFTER both
  prior mitigations: `c092df50`'s `PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT=300` and `fd84f90a`'s `FORMULA_DRIFT_TIMEOUT=240`)
  still failed BOTH slices: `tests` hung 18m35s inside `test_cross_timeframe_sanity.py` (last stderr line 09:38:14,
  `Timeout` fired 09:56:49 — pure scheduler starvation, not a slow-but-progressing test) with a DIFFERENT random hang
  site than the earlier `main` run's `test_signal_composer.py` (no content overlap → contention signature, not a
  per-test defect, matching this doc's established pattern); `checks` slice's basedpyright run hit
  `❌ Type check FAILED/timeout (exit=124)` at exactly the 300s `PYRIGHT_TIMEOUT` ceiling (09:15:56→09:20:57) — the
  ALREADY-RAISED budget is now the one timing out, not a pre-raise stale value. (Also inspected the 96 `reportAny`
  errors from the `e2e-testing` peripheral-dir check on the same run — confirmed `log_warn`-only per
  `scripts/quality-gates.sh:145-146`, non-blocking, ruled out as the actual cause before finding the real one at the
  STEP-4 typecheck timeout.) Host corroboration: `uptime` load average `29.85, 27.81, 28.60` (16 vCPUs), 20 concurrent
  `quality-gates.sh` processes — identical signature to every other entry in this doc-pair. This is exactly the scenario
  todo 1 anticipated ("if RED again with the same timeout signature even at 300s... escalate to the parent
  capacity-crisis doc rather than raising the timeout further in isolation") — did NOT raise
  `PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT` a third time; a further raise only moves the threshold and does not close the
  class, and the actual fix for this exact root cause (cross-repo QG-governor ledger coordination on this one shared
  glue-runner host) is already forked, scoped, and mid-flight in
  `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` (Phases 0-1 shipped
  `unified-trading-pm@fada7dc20`; Phase 2 live-validation + Phase 3 rollout still open) — duplicating that effort here
  would be scope creep for a one-shot wall-clearing task. A newer LDR run was already in flight at investigation time
  (`30804251677`, headSha `d387ba7f`, queued→in_progress during this session) — did not trigger a redundant dispatch
  (would only cancel-in-progress via the concurrency group and reset elapsed contention-survival time, per this doc's
  established precedent). `GET /api/repo-blockers` → `open: []`. No code or workflow change made — every candidate fix
  already exists on `live-defi-rollout`; the remaining wall is pure runner-queue-depth/host-CPU-scheduling delay
  (classification (A) from this escalation's own boot context, but the causal chain is infra capacity, not a
  stuck/missing promotion PR — none exists yet because LDR `ci_status` hasn't reported green;
  `ldr-to-main-promote-fleet` ticks every ~15min and will auto-create+merge the promotion PR the moment any LDR run
  does). Slot left clean (`features-service` on `live-defi-rollout`, 0 commits ahead). Pinged the authoring slot
  (`ci-reconcile`) with the outcome. Todo 2 remains open/unaddressed by this entry (scope stayed bounded to this one
  escalation, per prior-entry precedent).
