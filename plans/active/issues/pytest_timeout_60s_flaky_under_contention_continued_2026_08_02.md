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
repos:
  [
    unified-trading-api,
    unified-trading-pm,
    features-service,
    market-data-processing-service,
    deployment-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-08-02
last_updated: 2026-08-03T11:30Z
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
- [ ] 3. [OPERATOR] P2. The `features-service` `wall_type=main_ci_red` escalation has now fired **9 times today**
      (agents `agt-4e5bc3`/`agt-637862`/`agt-a7a7b6`/`agt-3bc731`/`agt-0dbb62`/this session, plus 3 more implied by the
      numbering) for the literal same underlying state — LDR fix shipped, waiting on a runner slot, nothing new to do —
      each dispatch independently re-reads the same run IDs and re-confirms the same "no action, pure wait" verdict. Per
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s dedup-by-state-transition principle (standing conditions
      should fire on change/RESOLVED, never every tick), this trigger appears to lack a cooldown/state-transition guard
      — it is spending a full one-shot cicd agent session every ~15-70 min purely to re-derive "still waiting," burning
      shared CI-firefighter capacity that a genuinely actionable wall elsewhere would need. Recommend: gate this
      escalation's re-fire on either (a) a minimum cooldown since the last `main_ci_red` dispatch for the same repo with
      an unchanged LDR HEAD, or (b) suppressing re-dispatch entirely while `ldr-to-main-promote-fleet`'s own GATE BLOCK
      reason is unchanged from the prior escalation's — operator decision, not something a one-shot wall-clearing
      session should self-implement.

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

- **2026-08-03 ~11:04Z (`cicd` escalation `agt-0dbb62`, slot 9, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — 8th escalation for the same wall, no material change since the prior (10:48Z) entry**: read `main`'s
  failing run `30780455914` directly — same already-diagnosed pre-`c092df50` 150s-pytest-timeout shape (fix on LDR,
  pending promotion). Checked LDR: the same run flagged as in-flight at the end of the prior entry (`30804251677`,
  headSha `d387ba7f`, dispatched 10:07:07Z) is STILL the live run, now ~57min elapsed, no newer LDR run exists (current
  LDR HEAD `9fb37033`, one commit ahead of `d387ba7f`, untested by any run yet). Verified on-disk that all three
  sanctioned mitigations are present and unchanged on `live-defi-rollout`
  (`grep PYTEST_TIMEOUT|PYRIGHT_TIMEOUT| FORMULA_DRIFT_TIMEOUT scripts/quality-gates.sh` →
  `PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}`, `PYRIGHT_TIMEOUT=${PYRIGHT_TIMEOUT:-300}`,
  `run_timeout "${FORMULA_DRIFT_TIMEOUT:-240}"` all intact) — no regression, no new code gap. `GET /api/repo-blockers` →
  `open: []`. `ldr-to-main-promote-fleet` still ticking green every ~15min (latest `30807769375` @11:00:10Z, success)
  and will auto-promote the instant any LDR run reports green. Per this doc's own established precedent (6 of the last 7
  entries), did NOT re-dispatch a fresh `quality-gates-v2` run (would cancel the already 57min-elapsed in-progress run
  via the concurrency group, discarding contention-survival progress for zero benefit) and did NOT raise any timeout a
  further increment (root-cause fix for the underlying host contention is
  `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`, already forked and in flight — out of scope
  for a one-shot wall-clearing task). **Disposition: no code or workflow change made or needed** — this is purely a
  runner-queue-depth wait, identical to entries 3, 4 (partial), and 6. Slot left clean (`features-service` on
  `live-defi-rollout`, 0 commits ahead, no local changes). Pinged the authoring slot (`ci-reconcile`) with the outcome.

- **2026-08-03 ~09:30-11:10Z (`cicd` escalation `agt-771546`, slot 4, `deployment-service`, `wall_type=ldr_qg_failure`,
  `pr_number=674`)** — a NEW repo, same bug class, both timeout shapes in one run: run `30790899514` (promotion PR
  `promote/deployment-service/1c19e5e8a8c3`, base `main`) failed via `Type check FAILED/timeout (exit=124)` (checks leg
  — `[4/6] TYPE CHECK` ran ~2m6s against the shared 120s `PYRIGHT_TIMEOUT` ceiling) AND
  `Failed: Timeout (>150.0s) from pytest-timeout` on 6 tests (tests leg — 5 in
  `TestApiFootballLauncherHardenedPreemptionSignal`, all trivial `subprocess.run(["bash","-c",...])` invocations of a
  mocked VM launcher script, plus `test_cloud_query_client.py::TestParallelScanBuckets::test_success_scans_all_paths`;
  suite otherwise 2858 passed / 4670s total wall — 15-77x this doc's typical per-test cost). Reproduced locally FIRST:
  the exact 7 failing tests all passed in 74s (9-10s each); a full `quality-gates.sh --no-fix` run passed in 210s —
  decisive confirmation of no code/test defect. By the time of diagnosis PR #674 had **already self-merged**
  (`mergedAt: 2026-08-03T06:39:17Z`, 3s after the failing check run was even created — the same
  self-merge-before-confirmatory-check-completes pattern this doc documents for instruments-service #1064 and
  market-data-processing-service #569 above), so the promotion itself needed no further action. LDR's OWN
  `quality-gates-v2` was nonetheless genuinely red 4 consecutive times today (`workflow_dispatch` runs at
  03:04Z/03:32Z/05:33Z, plus the 06:39Z promotion-PR run) with no green run recorded — unlike the "still in-flight,
  wait" disposition of several entries above, this repo showed the SAME "sustained non-self-clearing red" pattern that
  warranted `unified-trading-api@71cdda0`'s and `features-service@c092df50`'s repo-local fix, not just a queue-depth
  wait. Applied the identical sanctioned mitigation: `deployment-service@eb131cd` adds
  `PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}` and `PYRIGHT_TIMEOUT=${PYRIGHT_TIMEOUT:-300}` to `scripts/quality-gates.sh`
  (repo-local, before `LOCAL_DEPS`/further config) — verified green locally post-change (210s,
  `✅ ALL QUALITY GATES PASSED`), shipped via `quickmerge --agent --files 'scripts/quality-gates.sh'`, confirmed on
  `origin/live-defi-rollout` via `merge-base --is-ancestor`. A fresh `quality-gates-v2` run (`30808116964`) was
  auto-triggered by the push (concurrency group `quality-gates-v2-${{ github.ref }}`, `cancel-in-progress: true`,
  correctly superseding the pre-fix `workflow_dispatch` run) — did not additionally hand-dispatch, per this doc's
  established precedent against redundant dispatches onto an already-contended runner pool. Fleet-wide snapshot at
  investigation time (~11:05Z): 10+ `quality-gates-v2` runs queued/in-progress simultaneously across
  deployment-service/instruments-service/market-tick-data-service/execution-service/
  features-service/market-data-processing-service — consistent with every prior entry's host-saturation diagnosis, not
  specific to this repo. `GET /api/repo-blockers` → `open: []`. **Outcome of run `30808116964` not yet observed** — left
  for a follow-up occurrence per this doc's established pattern. Also noted (not acted on, out of scope): a second,
  unrelated open promotion PR `deployment-service#675` (`promote/deployment-service/032a8c031b82`) has
  `mergeStateStatus: DIRTY`/`mergeable: CONFLICTING` — a genuine `merge_conflict` wall, distinct from this
  `ldr_qg_failure` escalation; not touched here, flagging for whoever picks up that wall. Slot left clean
  (`deployment-service` on `live-defi-rollout`, 0 commits ahead of `origin`). Pinged the authoring slot (`planning`)
  with the outcome.

- **2026-08-03 ~11:05-11:15Z (`cicd` escalation `agt-b8bcdb`, slot 10, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — 9th escalation for the same wall, no material change since the 11:04Z entry ~10min prior**: `main`
  still red at the same already-diagnosed run `30780455914` (pre-`c092df50` 150s-pytest-timeout shape, fix on LDR,
  pending promotion). LDR: the same run flagged in-flight at the end of the prior two entries (`30804251677`, headSha
  `d387ba7f`, dispatched 10:07:07Z) is STILL the live run, ~68min elapsed, `status=in_progress`, no newer LDR run
  exists; LDR HEAD unchanged at `9fb37033`. Verified all three timeout mitigations still intact on `live-defi-rollout`
  (unchanged from the 11:04Z check). `ldr-to-main-promote-fleet` latest tick (`30807769375`, 11:00:10Z) still
  `success` + still `GATE BLOCK features-service: ci_status=FAILING` (cached from the 09:11Z red run, awaiting the
  in-flight run's verdict) — will auto-promote the instant it reports green. `GET /api/repo-blockers` → `open: []`.
  Root-cause plan `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` confirmed still
  `assigned_vm: NA` / local / Phase 2-3 open — unchanged, still correctly out of scope for a one-shot task.
  **Disposition: no code or workflow change made or needed** — identical to entries 3, 4 (partial), 6, and 8. Did NOT
  re-dispatch a fresh run (would cancel 68min of contention-survival progress via the concurrency group for zero
  benefit). Given this is now the 9th consecutive re-derivation of the exact same "wait" verdict, added todo 3 above
  flagging the escalation trigger's apparent lack of a dedup/cooldown guard as an operator-level finding — this is a
  distinct, actionable gap (unlike the wall itself, which has no action available) and worth fixing so future
  occurrences don't spend a full agent session re-confirming an unchanged state. Slot left clean (`features-service` on
  `live-defi-rollout`, 0 commits ahead, no local changes). Pinging the authoring slot (`ci-reconcile`) with the outcome.

- **2026-08-03 ~11:20-11:30Z (`cicd` escalation `agt-e5e387`, slot 4, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=1064`) — SAME escalation id as the 09:47-10:10Z entry above (this is a re-dispatch, likely the prior
  session's tmux/session lifecycle ending before it reached its own `/done`, not a new occurrence)**: re-verified from
  scratch rather than trusting the cached entry. `gh pr view 1064` → `state=MERGED`, `mergedAt=2026-08-03T06:31:51Z`
  (unchanged). `gh pr list --state open` for `instruments-service` → **0 open PRs** — confirms no promotion is actually
  stuck; the 07:55:38Z run (`promote/instruments-service/06be51ec6e74`) referenced implicitly by the newer `main` push
  run is ALSO already merged. `main-backmerge-to-ldr` and `Semver Agent` both `success` at `07:55:43Z` (one run PAST the
  06:31:54Z ones already noted in the prior entry) — the business outcome (promote → backmerge → semver-tag) has now
  completed successfully TWICE since the original failing run, fully independent of any confirmatory `quality-gates-v2`
  check. Current `quality-gates-v2` state: `main` run `30795433570` (created 07:55:44Z) still `queued`; LDR run
  `30808129517` (created 11:05:31Z) still `queued` — both 3+ hours old with no runner slot, consistent with every other
  entry in this doc-pair (10+ repos, 25-40+ load average, 20-28 concurrent `quality-gates.sh` processes on this shared
  host). `GET /api/repo-blockers` → `open: []`. LDR HEAD in this slot advanced one commit past the prior entry's repro
  point (`dabbb1a3`, `fix(deps): resolve prek from patched fork` — `pyproject.toml`/`uv.lock` only, no test-affecting
  change per `git show --stat`); did not re-run the full local suite since the prior entry's clean 5159-passed/0-failed
  repro at the immediate parent commit (`d7276438`) already stands and this new commit touches nothing test-relevant.
  **Disposition: no code or workflow change made or needed** — confirms the prior entry's verdict still holds 1h10m
  later; root cause remains fleet-wide runner contention, tracked and out of scope for a one-shot wall-clearing task
  (root-cause fix in flight at `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`). Slot left
  clean (`instruments-service` on `live-defi-rollout`, 0 commits ahead of origin, working tree clean). Pinged the
  authoring slot (`ci`) with the outcome.
