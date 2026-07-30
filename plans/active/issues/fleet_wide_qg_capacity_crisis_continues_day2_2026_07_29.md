---
doc_type: issue
title:
  Fleet-wide QG self-hosted-runner capacity crisis (fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md) is
  still active into a second day — that doc hit its 1000-line hard cap so this is a continuation, not a duplicate
summary: >-
  Responding to an operator #ci-failures Slack dump (2026-07-28 22:40-2026-07-29 01:29 BST) asking whether the flood of
  QG FAILED/RECOVERED flapping, sit-unlock failures, and stuck promotion PRs indicates an ongoing unresolved problem:
  **yes, confirmed live via the AO escalation API** (`GET /api/escalations/active`, SSM against `i-0c9b283b31d6b5ca7`),
  not assumed from the Slack dump alone. As of 2026-07-29T01:05-01:08Z: 47 `ldr_qg_failure` escalations active in the
  trailing 6h window across ~30 repos, of which 6 terminated `still_red_past_deadline` (genuine give-ups, not fixed —
  including `market-tick-data-service` at 46 attempts and `trading-agent-service` at 78 attempts before eventually going
  green) and several more actively re-escalating (`still_red_reescalated`) in a live retry loop at query time
  (`instruments-service`, `e2e-testing` twice). This is the exact same root cause
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` has tracked since 2026-07-27 — shared 16-vCPU/32GB
  box `i-0c9b283b31d6b5ca7` oversubscribed by ~13-20 concurrent AO slot-worker sessions plus up to 22 self-hosted CI
  runner pools — but that doc is now at its 1000-line hard cap (`wc -l` = exactly 1000) and cannot take a new Progress
  Log entry, hence this continuation doc rather than appending. Separately, and NOT yet diagnosed in the original doc:
  `unified-trading-pm`'s own `plan_health` escalation queue (a DIFFERENT `wall_type`, not `ldr_qg_failure`) is actively
  GROWING, not draining — 44 active `plan_health` entries at query time (was ~34 per the operator's own dashboard
  screenshot earlier the same session), spanning 12 distinct promote-PR incarnations (#1740-#1751) in roughly 5 hours,
  every one `status=dispatched`/`resolved_at=null`. The specific trio the operator asked to be watched (PR
  #1746/#1747/#1748, escalation ids `agt-6a6ba6`/`agt-4c0ede`/`agt-4de402`) had NOT cleared as of this check: all three
  still `status=dispatched`, `resolved_at=null`, 44-51 minutes elapsed since their own dispatch (past the 30-40min
  window originally asked about) — and 4 newer PM promote PRs (#1748-#1751) had already queued up behind them in the
  same window, consistent with a queue that isn't keeping pace with its own inflow rather than one that's merely slow.
status: open
nature: issue
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [cross-cutting]; continuation of the
  # fleet_wide_qg_self_hosted_runner_capacity_crisis ci-tranche incident, same content class.
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity, incident, cross-repo, escalation-queue, plan-health, github-actions-cost]
related:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md,
    /plans/active/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
priority: P1
parent_epic: infrastructure_master
source:
  "operator #ci-failures Slack dump + operator ask to verify PM#1746/1747/1748 + 2 ldr_qg_failure items over 30-40min,
  2026-07-29 ~01:05Z"
execution_scope: orchestrator-agent
assigned_role: cicd
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# Fleet-wide QG capacity crisis continues into day 2 (2026-07-29) — original doc at line cap

## Why this doc exists instead of an entry in the original

`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` is at exactly 1000 lines (the hard cap enforced by
`check_line_caps.sh`) — confirmed via `wc -l` before attempting to append. That doc's own root-cause analysis, timeline,
and the operator's 2026-07-28 "protected-6 repos stay self-hosted, accept recurring reds, resolve via retrigger" ruling
all still stand; nothing here supersedes them. This is a same-root-cause continuation entry that had nowhere to land.

## Live verification, 2026-07-29 ~01:05-01:08Z (via AO `GET /api/escalations/active`, SSM)

**`ldr_qg_failure` wall_type, 6h trailing window, 47 entries across ~30 repos:**

- 6 terminated `still_red_past_deadline` (genuine unresolved failures, not fixed): `instruments-service`#1007 (3
  attempts), `agent-orchestrator`#0 (3 attempts), `features-service`#893 (8 attempts), `market-tick-data-service`#774 (2
  attempts), `trading-agent-service`#363 (10 attempts), `market-tick-data-service`#0 (**46 attempts**).
- 1 resolved `qg_v2_green` only after **78 attempts** (`trading-agent-service`#364).
- At query time, several still actively re-escalating (`still_red_reescalated`, i.e. genuinely red again, looped back
  into a fresh dispatch cycle rather than terminally given up): `instruments-service` (×2 rows, one immediately
  re-dispatched), `e2e-testing` (×2 rows).
- Remainder either genuinely `qg_v2_green` (real fixes/self-heals) or still `dispatched` mid-flight.

**This matches `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s signature exactly** — the doc's last
logged entry was 2026-07-28 ~23:26Z (`instruments-service`#1007, `uv` cache race + typecheck timeout + duration miss,
confirmed non-code via clean local QG at the same HEAD); this check ~2h later shows the identical pattern continuing,
unabated, into 2026-07-29.

**`plan_health` wall_type on `unified-trading-pm` specifically — NOT covered by the original doc, distinct symptom:**

44 active entries at query time (`now=2026-07-29T01:05:17Z`), all `status=dispatched`, all `resolved_at=null`, spanning
promote-PR incarnations #1740 through #1751 (12 PRs in ~5h — i.e. a fresh promote PR roughly every 25min, consistent
with `ldr-to-main-promote-fleet.yml`'s `*/15` cadence plus PM being an unusually active repo). The operator-flagged
trio:

| escalation_id | PR   | created (UTC) | dispatched (UTC) | status     | resolved_at | elapsed since dispatch |
| ------------- | ---- | ------------- | ---------------- | ---------- | ----------- | ---------------------- |
| `agt-6a6ba6`  | 1746 | 23:34:02      | 00:17:38         | dispatched | null        | ~51min                 |
| `agt-4c0ede`  | 1747 | 23:41:07      | 00:18:37         | dispatched | null        | ~50min                 |
| `agt-4de402`  | 1748 | 23:51:17      | 00:21:04         | dispatched | null        | ~47min                 |

**Answer to the operator's direct ask: no, this trio had not cleared within 30-40min — nor within the ~50min this check
ran at.** Whether `plan_health` escalations on PM are being starved by the same host-contention root cause (a
`plan_health` worker is presumably itself a slot session competing for the same oversubscribed box) or have a separate,
undiagnosed bottleneck is **not yet determined** — flagging as open rather than assuming either.

## Why this matters for the original CI-cost-reduction thread

This session's original mandate was auditing/reducing GH Actions spend (~$1,150-1,200/mo baseline measured 2026-07-15).
A `trading-agent-service` PR needing **78 retry attempts** before going green, and a `market-tick-data-service`
escalation racking up **46 attempts** before giving up entirely, represent exactly the kind of CI-minute waste that
audit was meant to catch — except this waste is _retry churn from host contention_, not from slow tests or heavy
libraries. The self-hosted-runner migration (this session's own earlier fix, intended to CUT GH-hosted-minute spend) is
the proximate trigger: it moved CI load onto a box that can't sustain it, and the resulting retry storm may be burning
more wall-clock/compute (on infra you're already paying for) than the GH minutes it saved. This is worth quantifying,
not just noting.

## Todos

- [x] ✅ [DATA] P1. Quantify actual cost impact: pull attempt-count distribution across all `ldr_qg_failure` escalations
      over the incident's full 2026-07-27→present window (not just the 6h sample here) and estimate GH-Actions-minute
      waste from cancelled/timed-out/retried runs vs. the self-hosted migration's original projected savings — the
      operator asked for this audit's numbers to be real, not assumed. **DONE 2026-07-30T10:54-11:05Z (slot 5,
      data_engineering) — real numbers pulled from the AO SQLite state.db directly (bypasses the
      `/api/escalations/active` API's hardcoded `.limit(100)` rows, confirmed too small to cover the full window) + real
      GH Actions run history via `gh api`/`gh run list`. See Progress Log entry below for the full breakdown and
      methodology. Verdict: the retry storm's GH-Actions-DOLLAR waste is real but small
      (~$10 over the sampled 3.5-day window, ≈$90/mo if sustained) — roughly 2-3% of the migration's ~$350-450/mo
      projected fleet savings, not big enough to threaten it. The bigger, genuinely unquantified-here cost is AWS EC2
      wall-clock/compute on the oversubscribed shared host from the 815 real agent-dispatch attempts — a different cost
      bucket than what this todo asked about (GH-Actions-minutes), flagged as a new follow-up rather than
      assumed-covered.**
- [x] ✅ [OPERATOR] P1. **Operator-ruled 2026-07-29 (interactive decision session)**: keep protected-6 on self-hosted,
      relying on the just-applied host fix (instance resize + added swap) to cut retry-storm frequency, re-measured
      before any further change. Revisit the 2026-07-28 "protected-6 stay self-hosted, accept recurring reds, resolve
      via retrigger" posture now that it has run into a second day with a 46-attempt and a 78-attempt case — the
      original doc's own Progress Log flagged this exact question ("worth an urgent re-look... rather than treating each
      new instance as just another routine corroboration") before hitting its line cap; it was never answered.

- [x] ✅ [BACKEND] P2. **Re-measure protected-6 retry-attempt counts post-resize** (`i-0c9b283b31d6b5ca7` or successor)
      — the follow-up the 2026-07-29 ruling above is conditioned on. If 46/78-style escalations recur despite the host
      fix (instance resize + added swap), that is the trigger to revisit reverting protected-6 to GitHub-hosted runners;
      if they don't, this posture is confirmed working and this todo can close citing the measurement. **Re-measured
      2026-07-30, ~06:20-06:27Z (this session's operator-ruling close-out pass) — the AO escalations API itself could
      NOT be queried (see Progress Log entry below for the full host-level measurement); host-level evidence answers the
      todo's underlying question directly: the box remains severely oversubscribed post-resize, closing this todo with a
      NEGATIVE verdict (the host fix has NOT resolved the contention) rather than a positive confirmation.**
- [ ] [BACKEND] P2. Diagnose whether PM's `plan_health` escalation queue (44 active, growing, none resolving) shares the
      `ldr_qg_failure` box-contention root cause or has an independent bottleneck — check whether a `plan_health` worker
      type is actually being spawned/claiming slots at all, vs. queuing indefinitely for lack of a matching worker (a
      distinct failure mode from "slow due to contention").
- [ ] [SCRIPT] P2. Once `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s Recommended-fix-path section
      is next revisited, consider splitting that doc (archive the day-1 Progress Log, keep an active continuation) so
      future corroborations have somewhere to land instead of spawning sibling docs like this one.
- [ ] [DATA] P2. **New, opened by the P1 cost-quantification finding above.** The retry storm's real, expensive cost
      bucket is AWS EC2 wall-clock/compute on the oversubscribed shared host (`i-0c9b283b31d6b5ca7`) from the 815 real
      agent-dispatch attempts recorded against `ldr_qg_failure` escalations since 2026-07-27 (self-hosted GH Actions
      runner minutes are free from GitHub's side, so this is NOT GH-Actions-billed — a genuinely separate cost category
      the P1 todo's "GH-Actions-minute" framing didn't cover). Quantify it: pull the box's real AWS Cost Explorer /
      instance-hours data for the 2026-07-27→present window (the box is `m8i.4xlarge`, on-demand or reserved — check
      which) and estimate
      $ cost attributable to the retry-storm's share of CPU/wall-clock vs. steady-state baseline
      usage. Done when: a real $
      figure (not assumed) is added alongside this doc's existing GH-Actions-dollar figure, so the two cost buckets can
      be compared side-by-side.
- [ ] [OPERATOR] P3. Confirm the OOM-killer mechanism for the 2026-07-30 14:54-15:01Z mass `tmux_session_lost` cluster
      (slots 1, 4, 5, 9, 10, 11 killed across 3 waves in ~7 min, see Progress Log below) via `dmesg`/`journalctl -k` on
      `i-0c9b283b31d6b5ca7` (needs root — no agent session has it). Currently UNCONFIRMED: swap (14-16Gi used) + load
      (peak ~26/16vCPU) are consistent with memory pressure but the kernel OOM-killer log has not been read this session
      or any prior one in this doc.

## Evidence

- Live query: `GET http://localhost:8765/api/escalations/active?include_resolved_within_hours=6` via SSM against
  `i-0c9b283b31d6b5ca7`, 2026-07-29T01:05:17Z and T01:08Z snapshots (raw JSON captured in this session's tool output,
  not reproduced here in full — re-run the same query for a fresh sample).
- Original doc: `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (1000 lines, at
  cap as of this writing).

## Progress Log

- **2026-07-29 (cicd escalation `agt-575a4c`, slot 3)**: corroborating data point for the P2 "re-measure protected-6
  post-resize" todo above. `instruments-service` PR #1012 (LDR→main promote, created 2026-07-29T04:49:40Z) hit
  `ldr_qg_failure` — checks-leg `QG_SLICE=typecheck` timed out (`exit=124`, run
  [30423320298](https://github.com/IggyIkenna/instruments-service/actions/runs/30423320298), ~04:52-04:54Z) while the
  SAME job's `QG_SLICE=lint-codex` selector independently printed "ALL QUALITY GATES PASSED" — confirms the failure was
  isolated to the typecheck selector, not a codex-compliance/lint regression (3 pre-existing tolerated violations —
  `sports_reference_fixtures.py` 914L file-size + a `process.py` function-size violation since fixed — sat within
  `CODEX_MAX_VIOLATIONS=3` in both this and later runs; the file-size violation is still present today and non-blocking,
  a red herring). Tests-leg failed independently in the same run via a pytest-xdist
  `RuntimeError: Unexpectedly no active workers available` AFTER all 1176 tests had already passed — a worker-teardown
  crash, not a test failure. Self-healed with no code change: PR #1012 closed, and 8 subsequent promote-PR incarnations
  (#1013, #1015, #1017-#1020) merged clean over the following ~10h, with the latest direct `live-defi-rollout`
  push-triggered run (`30462644516`, 2026-07-29T14:47:46Z) green — `QG_SLICE=typecheck` PASSED in 9s (vs.
  ~2min-before-timeout in the failing run), consistent with transient host contention, not a code regression. No fix
  applied (none needed — nothing is currently broken); filed as evidence for the re-measurement todo, not as a fresh
  unresolved occurrence.

- **2026-07-29 ~20:45Z (cicd escalation `agt-eda323`, slot 14)**: a DIFFERENT failure signature than every entry above —
  not host-contention-during-real-execution (timeouts, uv cache races, worker-teardown crashes), but the gate never
  starting at all. Dispatched to fix `instruments-service`#1025 (LDR→main promote) `ldr_qg_failure`; found
  `content-gate` ("content sentinel") + the `quality-gates-v2` aggregation job (both still hardcoded
  `runs-on: ubuntu-latest` in `python-quality-gates-v2.yml` — never migrated by either Wave-1 or Wave-2, which only
  touched `qg-slices` and the CALLER template's escalate/notify/dispatch jobs) failing in 2-3s with **zero steps and
  zero log blob**. Confirmed via `GET .../actions/runs/<id>/timing`: `"billable":{"UBUNTU":{"total_ms":0,...}}` for all
  4 ubuntu-latest jobs across two separate attempts (PR-triggered `30477967414` @18:00Z and a `workflow_dispatch` retry
  `30479612102` @18:22Z), while the SAME runs' self-hosted `[self-hosted, glue]` jobs (escalate-ldr-qg-failure,
  notify-ci-watcher) succeeded normally (runner `glue-ip-172-31-5-118-1`, confirmed online + idle both times).
  `QG slice` (the job that runs the actual test/lint/type work) was SKIPPED both times — i.e. **the real gate never ran;
  there is no code defect to fix**. GitHub status page checked live: Actions fully operational (only Copilot degraded) —
  rules out a platform incident. Widened the check fleet-wide: `agent-orchestrator`, `deployment-service`,
  `unified-trading-pm`, `market-data-processing-service`, `features-service` all show the SAME pattern on their most
  recent runs (19:20-20:45Z), and it has escalated over the evening from partial (only the ubuntu-latest jobs within a
  mixed run fail) to full run-level `startup_failure` with `total_count: 0` jobs (e.g. `unified-trading-pm` run
  `30489671842`, `agent-orchestrator` run `30487051711`) — nothing is even being scheduled for these workflows now, not
  just the QG reusable one. Working theory (not yet operator-confirmed): the retry-storm volumes this doc already
  documents (46 + 78 + many more `ldr_qg_failure` attempts fleet-wide) plus PM's own still-not-migrated Tier-B pipeline
  files (`ldr-to-main-promote(-fleet)`, `sit-gate`, etc. — all still `ubuntu-latest` per this doc's sibling
  `gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`) have now burned through the account's GitHub
  Actions spending limit for GH-hosted (ubuntu-latest) runners specifically — self-hosted jobs are unaffected because
  GitHub doesn't bill/gate self-hosted runner minutes at all, which is exactly the asymmetry observed. **If confirmed,
  this blocks EVERY repo's promotion pipeline fleet-wide right now, not just instruments-service#1025** — filed
  `BLK-21d55fb1` (task `agt-eda323`) to the dashboard for operator/main-agent decision (check/raise the GH Actions
  spending limit vs. migrate the remaining ubuntu-latest jobs to the already-oversubscribed self-hosted pool) rather
  than attempting a code "fix" for a gate that was never actually exercised. No code changed on `instruments-service`;
  slot left clean on `live-defi-rollout`.

- **2026-07-29 ~20:56Z (cicd escalation `agt-0cd704`, slot 9) — corroboration, pins down onset + one more affected PR**:
  dispatched to fix `ldr_qg_failure` on `unified-api-contracts` promotion PR #796. The ORIGINAL wall (`QG slice (tests)`
  failing a `uv` build-isolation step, "No such file or directory (os error 2)") was transient host contention, already
  refuted as a code issue by a same-commit `workflow_dispatch` success 8 min later (16:31:50Z, zero commits in between).
  Attempting to re-gate the PR head hit the SAME full run-level `startup_failure` (0 jobs) this doc's prior entry
  describes — 3 separate `workflow_dispatch` attempts on `unified-api-contracts`, plus one on `unified-trading-pm`'s
  `ldr-to-main-promote-fleet.yml`, all `startup_failure`/0 jobs. Swept `unified-trading-pm`'s run history back through
  100+ runs to pin the exact onset: **last success `2026-07-29T18:25:50Z` (`repository_dispatch`) → first failure
  `2026-07-29T18:27:24Z` (`schedule`)** — a hard transition, not a gradual degradation, and every run of every trigger
  type has failed continuously since. Runners confirmed `online`/idle (not busy) on `unified-trading-pm`,
  `agent-orchestrator`, `unified-api-contracts` — rules out runner-side unavailability as the mechanism for the
  full-run-level failures. Not re-filing `BLK-21d55fb1` (same standing condition, already escalated by `agt-eda323`) —
  adding this only as corroboration + the precise onset timestamp, which the prior entry didn't have. `#796` stays
  blocked on this fleet-wide incident clearing; no code fix applies. Pinged the authoring slot with this outcome; slot
  left clean on `live-defi-rollout`, no repo touched beyond this doc.

- **2026-07-29 ~21:00Z (cicd escalation `agt-dfdd5b`, slot 5)**: independent corroboration, escalated for
  `client-reporting-api` `ldr_qg_failure` (`#0`, no PR — a plain LDR-direct wall). Reproduced locally FIRST per the boot
  instructions: `bash scripts/quality-gates.sh` at HEAD `ed6586b8` — 665 passed, 4 skipped, 71.56% coverage,
  `ALL QUALITY GATES PASSED (59s)`, zero failures. The code and tests are clean; the wall is CI-only. Checked the actual
  failing CI run (`30479590370`, 18:22:09Z, the one that fired this escalation): `content-gate` + both `qg-slices` legs
  (`checks`, `tests`) all `success`, but the `quality-gates-v2` aggregation job itself failed in 12s despite its
  `needs.qg-slices.result` being `success` — logs for that job already 404'd (expired) by the time I looked.
  Re-dispatched fresh (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`) three times across a ~10min
  window: all `startup_failure`, 1s, zero jobs. Widened the check myself (independently of `agt-eda323`'s own fleet
  check above, before finding this doc): `market-tick-data-service` and `instruments-service` fresh dispatches both
  `startup_failure` identically — and critically, `unified-trading-library` (NOT on the self-hosted-runner allowlist,
  `self_hosted_runner_labels: ""` i.e. `ubuntu-latest`-only, whose own dispatch succeeded cleanly at 16:31:54Z earlier
  today) now ALSO fails `startup_failure` on a fresh dispatch — ruling out "self-hosted pool contention" as sufficient
  explanation on its own (a pure-`ubuntu-latest` repo is affected too) and confirming this is the account-wide
  GH-hosted-runner spending-limit block `agt-eda323` already diagnosed, not something self-hosted-specific. Checked
  githubstatus.com independently: Actions component "Operational" (only a Copilot model-provider degradation listed) —
  platform-side incident ruled out again. **No code or workflow change made or needed on `client-reporting-api`** —
  filing my own bounded `/blocked` for escalation `agt-dfdd5b` referencing this doc + `BLK-21d55fb1` rather than
  duplicating the operator page; if unanswered within the 2-min bound, stopping per the one-shot contract. Slot left
  clean on `live-defi-rollout` (no branch changes made).

- **2026-07-29 ~21:20Z (cicd escalation `agt-614695`, slot 15) — DIFFERENT from every entry above: a real, separate
  local test regression, not pure infra**. Dispatched for `instruments-service` `ldr_qg_failure` (`#0`). CI showed the
  same fleet-wide `startup_failure` (0 jobs, 0 billable ms, confirmed via `.../actions/runs/<id>/timing`) this doc
  already tracks — but per the boot contract I also reproduced locally FIRST, and unlike `agt-dfdd5b`'s clean repro,
  `bash scripts/quality-gates.sh` at HEAD `4c05f2d3` genuinely failed: 10 failed / 5034 passed. Root-caused as
  cross-repo editable-dependency drift (`unified-api-contracts@0c0f6953` registered `FRED` as a new tradfi venue +
  `ohlcv_1d` as a genuine tradfi data_type) breaking two stale instruments-service test-side assumptions: (1) 9 tradfi
  v2 enumerator tests in `test_enumerate_expected_universe_v2.py` relied on `ohlcv_1d` silently passing through
  `_row_data_types`' unknown-data_type escape hatch to dodge NASDAQ/ETF's validity matrix + the MVP data_type-narrowing
  gate — now a real registered data_type, the passthrough no longer applies and row_dts collapsed to empty; (2)
  `test_pipeline_e2e_prediction.py`'s pinned `_PER_AG_TARGET_COUNTS["TRADFI"]` (7) went stale vs. the real UAC registry
  (now 8 venues). While diagnosing, discovered `slot-14` had independently found + fixed the identical root cause
  moments earlier (`instruments-service@7f272911`, "fix(tests): update tradfi test fixtures for FRED's ohlcv_1d/venue
  registration") — my own from-scratch fix converged on the same data_type swap (`ohlcv_1m`) and the same count bump
  (7→8), confirming the diagnosis independently. Discarded my redundant local changes in favor of the already-landed,
  already-verified commit (`git checkout HEAD --` on both files) rather than force a duplicate/conflicting push.
  Re-verified at current HEAD: `ALL QUALITY GATES PASSED (93s)`, 5044 passed / 0 failed. **This underlying test
  regression is now fully fixed on `live-defi-rollout`** — the residual CI red on this repo is purely the ongoing
  fleet-wide `startup_failure` incident this doc already tracks (`BLK-21d55fb1`), not re-filing it. Pinged
  `AUTHORING_SLOT=ci-reconcile` with the outcome. Slot left clean on `live-defi-rollout`, no branch changes beyond the
  (already-shipped) fix confirmed.

- **2026-07-29 ~23:38Z (cicd escalation `agt-28375c`, slot 1) — 3rd independent confirmation for `instruments-service`:
  the `agt-614695` test-regression fix holds, residual red is pure infra**. Re-dispatched against the same standing
  `instruments-service` `ldr_qg_failure` wall (`#0`, no PR; this escalation alone was already at `attempts: 4` per
  `GET /api/escalations/active` before this run — one of several duplicate concurrent escalations for this repo,
  `agt-4b4ba8`/`agt-614695`/`agt-d04227`/`agt-28375c`, all `still_red_reescalated` from prior rounds). Reproduced
  locally FIRST per the boot contract, backgrounded per the mandatory non-blocking pattern (never foreground — 15-min
  heartbeat-silence kill risk): `bash scripts/quality-gates.sh` at HEAD `7f272911` (the exact fix commit `agt-614695`
  already verified) — `5044 passed, 7 skipped`, coverage `88.77% ≥ 88.0%` floor, `ALL QUALITY GATES PASSED (99s)`,
  sentinel written matching HEAD. Zero failures; nothing left to fix on the code/test side. Fresh CI check: 3 most
  recent `live-defi-rollout` runs (23:35:55Z, 22:14:38Z, 22:01:22Z) all `startup_failure`; confirmed `jobs: []` +
  `timing.billable: {}` + `run_duration_ms: 1000` on the newest (`30500040561`) — identical zero-job signature to every
  other repo this doc and `github_actions_billing_wall_recurrence_2026_07_29.md` track. Also checked the PUSH-triggered
  run for the fix commit itself (`30492395057`, `headSha=7f272911...`, 21:26:43Z, 0s): same `startup_failure`/`jobs:[]`
  signature — the fix commit was never able to prove itself green on CI because the wall was already up by the time it
  landed, not because the fix is incomplete. **No code or workflow change made or needed.** `GET /api/repo-blockers` →
  `open: []` (none registered for this repo, nothing to fast-path). Not re-filing `/blocked` (same standing
  `BLK-21d55fb1` condition; the `[OPERATOR] P0` in `github_actions_billing_wall_recurrence_2026_07_29.md` already covers
  the decision — avoiding the escalation-spam pattern that doc's own P3 todo flags). Not pinging the authoring slot
  (`AUTHORING_SLOT=ci-reconcile`, the confirmed non-numeric literal that 400s per the entries above and the sibling
  doc's evidence log). Slot left clean on `live-defi-rollout`, working tree clean, no branch changes.

- **2026-07-30 ~06:20-06:27Z (operator-ruling close-out pass)**: Attempted the P2 "re-measure protected-6 retry-attempt
  counts post-resize" todo. `curl http://localhost:8765/api/escalations/active?...` via SSM against
  `i-0c9b283b31d6b5ca7` **timed out** (`curl --max-time 20` → exit 28, `HTTP_STATUS:000`) on both the original unbounded
  attempt (never returned in ~10min, abandoned) and a bounded 20s retry — the AO escalations API itself is currently
  unresponsive on this box, so the literal attempt-count metric this todo asks for could not be pulled. Fell back to
  direct host-level measurement (same SSM channel), which answers the todo's underlying question directly without
  needing the API: `cat /proc/loadavg` → **97.38, 93.02, 78.15** (1/5/15-min load) on a confirmed **16-vCPU** box
  (`nproc`) — i.e. ~6x oversubscribed, not a transient spike (5-min and 15-min averages are both severely elevated too).
  Confirmed this IS the post-resize box, not a stale reading: `aws ec2 describe-instances` shows `i-0c9b283b31d6b5ca7`
  is `m8i.4xlarge` (16 vCPU / 64GB), `LaunchTime=2026-07-29T04:47:41Z` — launched the same day as the ruling's
  "just-applied host fix," so this measurement genuinely reflects the resized instance, not the pre-fix box.
  `ps -eo pid,pcpu,pmem,etimes,comm --sort=-pcpu` top-12: a mix of `python3` (the AO server itself, PID 4051394, 68%
  CPU) and **10 separate `claude` processes each at 39-68% CPU** — i.e. roughly a dozen concurrent AO-slot/agent
  sessions actively burning CPU simultaneously on this one box, consistent with (not less than) the original doc's
  "13-20 concurrent AO slot-worker sessions" figure. `pgrep -fc "Runner.Listener"` → **33** self-hosted GitHub Actions
  runner processes — MORE than the original doc's "up to 22 self-hosted CI runner pools" figure, not fewer; `free -h` →
  `Swap: 47Gi total, 21Gi used` — heavy swap usage persists (the "added swap" half of the fix is in place and is
  genuinely being drawn on, which is itself a symptom of memory pressure, not evidence the pressure is resolved).

  **Verdict: NEGATIVE — the post-resize host fix has NOT resolved the contention.** Load average ~6x the box's CPU
  count, 33 live self-hosted runners (up from ~22), a dozen concurrent `claude` sessions, and 21GB of active swap usage
  are a more severe oversubscription signature than the original incident's own numbers, not an improved one. This
  directly satisfies this todo's own stated trigger ("if 46/78-style escalations recur despite the host fix... that is
  the trigger to revisit reverting protected-6 to GitHub-hosted runners") — even without the literal escalation
  attempt-count (blocked by the unresponsive API, itself corroborating evidence of the same overload), the host-level
  picture is unambiguous. Recommend the next session/operator treat "revisit reverting protected-6 to GitHub-hosted
  runners" as the live decision now due, rather than continuing to await a clean post-resize confirmation that this
  measurement shows will not arrive on the current box as configured. Not making that reversion call myself — it is a
  real production-topology decision (which repos' CI moves back to GH-hosted, cost/perf tradeoff), not a mechanical
  follow-up of an already-made ruling, so left for the operator per this session's own scope (execute already-decided
  rulings, don't make new policy calls). No code/infra change made; read-only SSM queries only.

- **na-eligibility-audit 2026-07-30** (tranche=cross-cutting, autonomous): RECLASSIFY NA → planning — the 4 remaining
  todos are bounded measurements/diagnostics (attempt-count distribution over a stated window, post-resize protected-6
  re-measure, plan_health-queue root-cause split, doc split); the one operator call is already `[x]` ruled. **Note
  (integrator, same day)**: the close-out pass recorded immediately above already executed the post-resize protected-6
  re-measure and returned a NEGATIVE verdict, so that particular todo is answered even though its checkbox is untouched
  here.

- **2026-07-30T10:54-11:05Z (slot 5, data_engineering) — P1 cost-quantification todo, real numbers**. Two real,
  independently-sourced datasets, not assumed:

  **(1) Escalation attempt-count distribution — pulled directly from the AO's SQLite `state.db`
  (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`, read-only query), NOT the
  `/api/escalations/active` HTTP endpoint.** Confirmed via code read (`server/escalation.py:list_active_escalations`,
  line ~1804) that the endpoint hard-caps at `.limit(100)` rows ordered by `created_at DESC` REGARDLESS of the
  `include_resolved_within_hours` window passed — verified empirically too (`include_resolved_within_hours=72` and
  `=200` both returned exactly 100 rows, earliest `created_at` unchanged at `2026-07-29T06:27:48Z` either way). This
  means the endpoint structurally CANNOT answer "full 2026-07-27→present window" once total escalation volume (all
  wall_types) exceeds 100 in that window — which it does (100 rows only reached back ~28h, not the ~83h this todo
  needs). Querying `escalation_queue` directly instead: **168 `ldr_qg_failure` escalations created since
  2026-07-27T00:00:00Z** (status: 125 `resolved`/`qg_v2_green`, 28 `unresolved`/`still_red_past_deadline`, 9
  `dispatched`/`still_red_reescalated`, 6 `dispatched` mid-flight). Attempts: **min 1, max 224, mean 4.85, sum 815**
  across the 168 rows. Distribution is heavily right-skewed: 76 rows at exactly 1 attempt, 51 at 2, 22 at 3, tapering to
  a long tail of 12 escalations at ≥5 attempts including the extremes already known from prior entries in this doc
  (`trading-agent-service`#364 = 78, `market-tick-data-service`#0 = 46) PLUS one NEW extreme not previously surfaced:
  **`instruments-service`#1009 (`agt-1b4cc2`) hit 224 attempts** before resolving `qg_v2_green` at 2026-07-29T09:59:49Z
  (created 2026-07-29T01:05:15Z, ~8h54m to resolve).

  **Attempts ≠ CI re-triggers — confirmed by direct cross-check, an important methodology correction.** Sampled the
  224-attempt `instruments-service`#1009 case against real GH Actions history
  (`gh run list --workflow=quality-gates-v2.yml --created "2026-07-29T01:00:00Z..2026-07-29T10:00:00Z"`): only **19
  actual CI runs** occurred in that ~9h window (11 success, 7 failure, 1 cancelled) — nowhere near 224. So
  `escalation.attempts` (incremented once per fix-worker DISPATCH, `escalation.py:647`) measures agent-RESPAWN churn,
  not CI-run churn; a naive "attempts × CI-run-cost" formula would have overstated GH-Actions waste by ~12×. Corrected
  the estimate below to use REAL CI run counts instead of escalation attempt counts.

  **(2) Real fleet-wide `quality-gates-v2` CI run volume since 2026-07-27, via `gh run list`/`gh api`** across the 25
  distinct repos carrying a `ldr_qg_failure` escalation in this window (queried per-repo with
  `--created "2026-07-27T00:00:00Z..2026-07-30T23:59:59Z"`; `unified-trading-pm` hit the 500-row page cap on a single
  query so it was re-split into 5 sub-windows and re-summed to get its true count — every other repo stayed under the
  cap on the first pass). **Grand total: 2,893 `quality-gates-v2` runs fleet-wide** — 2,269 success (78.4%), 322
  cancelled (11.1%), 255 failure (8.8%), 40 `startup_failure` (1.4%, the account-wide GH-hosted-runner spending-limit
  incident this doc's earlier entries already traced — `BLK-21d55fb1`), 7 queued/pending. Non-success (real retry churn)
  = 624 runs (21.6%).

  **GH-Actions-dollar estimate.** Confirmed via `gh api .../actions/runs/<id>/jobs` on a sample run (`30441834008`) that
  the residual, still-not-self-hosted-migrated jobs are 3 short `ubuntu-latest` jobs per run (`content sentinel`,
  `quality-gates-v2` aggregator, `Record QG result` — all ≤10s wall-clock but per the pre-existing migration doc's own
  established finding, `github_actions_self_hosted_runner_migration_2026_07_15.md:1386`, GitHub bills a **1-minute
  minimum PER JOB** regardless of the sub-10s actual duration the `timing` API rounds to `0ms`). Confirmed
  `startup_failure` runs bill
  **$0** (0 jobs ever scheduled, matching this doc's earlier `billable: {}`/`jobs:
  []` findings). At the confirmed **$0.006/min**
  rate (`github_actions_cost_reduction_options_analysis_2026_07_15.md`): real-dispatched non-success runs (cancelled
  322 + failure 255 = 577; excluding the 40 zero-job `startup_failure` runs) × 3 jobs × 1 min × $0.006/min = **~$10.39**
  in GH-Actions-dollar waste from actual retry/cancel churn over this ~3.5-day sampled window — extrapolated (if this
  rate held for a full month, which it may not since this is an active incident, not steady-state): **≈$85-95/mo**.

  **Verdict vs. the migration's original projected savings.** The archived migration plan's own stated target: fleet
  **~$1,000/mo → ~$550-650/mo** (i.e.,
  **~$350-450/mo projected savings**,
  `github_actions_self_hosted_runner_migration_2026_07_15.md` Progress Log). The retry storm's GH-Actions-dollar waste
  (~$85-95/mo
  if sustained) is **real but small — roughly 2-3% of the projected savings, not big enough to threaten or erase the
  migration's net benefit in GH-Actions-billing terms.** This is the mechanical, non-obvious reason: the migration moved
  the expensive, long-running `qg-slices` (test/typecheck) work to self-hosted runners, which GitHub does not bill at
  all — so even a large volume of RETRIED runs only re-bills the tiny residual 3-job hosted overhead, not the real
  compute. The operator's original framing ("retry churn may be burning more wall-clock/compute than the GH minutes it
  saved") is directionally correct, but the expensive resource it's pointing at is **AWS EC2 wall-clock/compute on the
  oversubscribed shared host** (`i-0c9b283b31d6b5ca7`, real cost, NOT GitHub-Actions-billed) from the 815 real
  agent-dispatch attempts — a genuinely different cost bucket than "GH-Actions-minutes," which this todo's literal
  framing didn't cover and which this session did NOT quantify (opened as a new `[DATA] P2` follow-up todo above rather
  than assumed away). No code/infra change made; read-only SQLite + `gh api`/`gh run list` queries only; slot left clean
  on `live-defi-rollout`.

- **2026-07-30 ~08:44Z (cicd escalation `agt-08a769`, slot 9) — corroboration, `client-reporting-api` promotion PR
  #609**: dispatched for `ldr_qg_failure` (`quality-gates-v2` red on the LDR→main promote PR, run
  [30526015130](https://github.com/IggyIkenna/client-reporting-api/actions/runs/30526015130)). Diagnosed the exact
  failure: `QG slice (checks)` job's `QG_SLICE=typecheck` selector hit the hard 120s basedpyright timeout
  (`Type check FAILED/timeout (exit=124)`, `08:20:25Z→08:22:25Z`) — same signature this doc already tracks fleet-wide.
  Reproduced locally FIRST: `QG_SLICE=typecheck bash scripts/quality-gates.sh --no-fix` at the same HEAD completed
  cleanly and fast (133 pre-existing basedpyright warnings, no error ceiling set, `QG_SLICE=typecheck PASSED`) —
  confirms the code is clean and the wall is CI-host-contention only, not a regression. By the time this was diagnosed
  the pipeline had already self-healed with no code change: PR #609 merged at 08:16:02Z (merge commit `d5ebf83a`), a
  fresh `workflow_dispatch` retrigger on `live-defi-rollout` (`30526108370`, 08:17:26Z) went green, the next promote PR
  #610 merged cleanly at 09:16:04Z, and the current `live-defi-rollout` HEAD (`e1b3106`) is green (`30535642575`,
  10:41:33Z). No open PRs, no open repo-blockers for this repo. **No code or workflow change made or needed** — filing
  as another corroborating data point for the box-contention root cause, not a fresh unresolved occurrence. Slot left
  clean on `live-defi-rollout`.

- **2026-07-30 ~15:48Z (review agent `agt-2552a2`, slot 1) — corroboration, mass `tmux_session_lost` cluster
  (2026-07-30T14:54-15:01Z) + a concrete double-requeue**: independently re-verified (not just relayed from a prior
  session's chat) via `GET /api/activity?limit=500` against the live orchestrator API. Three back-to-back kill waves in
  ~7 minutes: **14:54:09Z** — slots 1, 5, 9, 11 all `tmux_session_lost`→`killed` in the same second (slot 5 released
  `sports_odds_api_scattered_multiyear_gaps-002`, slot 9 released `mtds_plan_flip_fabricated_commit_sha_evidence-002`,
  slot 11 released `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero-003`); **14:58:13Z** — slots 1, 4 killed again;
  **15:01:32Z** — slots 1, 10 killed, slot 10 releasing `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero-003` — the SAME
  task id slot 11 had just released 7m23s earlier, i.e. a genuine double-requeue-in-7min of one task (real rework, not
  retry-churn noise). Notably slot 1 itself (this review agent's own slot) was killed in all three waves (14:54:09Z,
  14:58:13Z, 15:01:32Z) — direct first-hand evidence this session's predecessor review agent (`agt-4daef9`) was a
  casualty of the same cluster, which is why this is a fresh review session picking the thread back up. **Current host
  reading** (2026-07-30T15:48:40Z, `uptime`/`free -h` on the box this session runs on): load average 11.94 / 20.27 /
  21.63 (1/5/15-min) on 16 vCPUs — 1-min has eased under the ~26.20/16vCPU peak cited earlier today, but the 15-min
  average is still ~135% of core count, so this reads as fluctuating-but-still-elevated contention, not resolved; swap
  14Gi/47Gi used (same order of magnitude as the ~16Gi cited earlier). **OOM-mechanism stays UNCONFIRMED** — this
  session has no root and did not check `dmesg`/`journalctl -k`, so the swap+load pressure is "consistent with memory
  pressure" only, not an asserted OOM-kill cause (see the new `[OPERATOR]` todo above for the kernel-log follow-up this
  needs). **Recommend** (not actioned — plan-owner's call, not mine): this is the second corroboration entry landed in
  under 12h (after the 08:44Z one above); the L150 `[SCRIPT] P2` doc-split todo is worth pulling forward given entries
  keep accumulating. No code or plan-structure change made; slot 1 left clean on `live-defi-rollout`.
