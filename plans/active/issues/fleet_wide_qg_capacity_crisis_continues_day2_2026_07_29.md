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
asset_group: [cross-cutting]
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
drift_direction: advance-code
depends_on: []
assigned_vm: NA
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

- [ ] [DATA] P1. Quantify actual cost impact: pull attempt-count distribution across all `ldr_qg_failure` escalations
      over the incident's full 2026-07-27→present window (not just the 6h sample here) and estimate GH-Actions-minute
      waste from cancelled/timed-out/retried runs vs. the self-hosted migration's original projected savings — the
      operator asked for this audit's numbers to be real, not assumed.
- [x] ✅ [OPERATOR] P1. **Operator-ruled 2026-07-29 (interactive decision session)**: keep protected-6 on self-hosted,
      relying on the just-applied host fix (instance resize + added swap) to cut retry-storm frequency, re-measured
      before any further change. Revisit the 2026-07-28 "protected-6 stay self-hosted, accept recurring reds, resolve
      via retrigger" posture now that it has run into a second day with a 46-attempt and a 78-attempt case — the
      original doc's own Progress Log flagged this exact question ("worth an urgent re-look... rather than treating each
      new instance as just another routine corroboration") before hitting its line cap; it was never answered.

- [ ] [BACKEND] P2. **Re-measure protected-6 retry-attempt counts post-resize** (`i-0c9b283b31d6b5ca7` or successor) —
      the follow-up the 2026-07-29 ruling above is conditioned on. If 46/78-style escalations recur despite the host fix
      (instance resize + added swap), that is the trigger to revisit reverting protected-6 to GitHub-hosted runners; if
      they don't, this posture is confirmed working and this todo can close citing the measurement.
- [ ] [BACKEND] P2. Diagnose whether PM's `plan_health` escalation queue (44 active, growing, none resolving) shares the
      `ldr_qg_failure` box-contention root cause or has an independent bottleneck — check whether a `plan_health` worker
      type is actually being spawned/claiming slots at all, vs. queuing indefinitely for lack of a matching worker (a
      distinct failure mode from "slow due to contention").
- [ ] [SCRIPT] P2. Once `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s Recommended-fix-path section
      is next revisited, consider splitting that doc (archive the day-1 Progress Log, keep an active continuation) so
      future corroborations have somewhere to land instead of spawning sibling docs like this one.

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
