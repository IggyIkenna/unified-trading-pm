---
doc_type: issue
title:
  "ldr-to-main-promote-fleet.yml AND ldr-to-main-promote.yml return startup_failure on EVERY tick since
  2026-07-29T18:30:03Z (~10h+, ongoing) — entire ldr_main promote fleet blocked, not just one repo"
summary: >-
  While confirming the narrower [CI] P2 todo in
  `plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md` (did
  deployment-service's promote genuinely no-op, or self-resolve?), found the answer to that question is YES it
  self-resolved (deployment-service merged PRs #594-#603 cleanly through 2026-07-29T16:20:03Z, no further manual
  intervention needed) — but discovered a much bigger, CURRENTLY ACTIVE, separate incident in the process: BOTH
  `ldr-to-main-promote-fleet.yml` and `ldr-to-main-promote.yml` (the two workflows the VM heartbeat script
  `scripts/orchestrator/ldr-to-main-promote-heartbeat.sh` dispatches every ~15 min) have returned `conclusion:
  startup_failure` with `jobs: []` on EVERY SINGLE TICK since **2026-07-29T18:30:03Z** — continuously, through at least
  **2026-07-30T04:38Z** when this doc was filed (~10h, run_number 1470+ and climbing on the fleet workflow alone). This
  blocks LDR→main promotion for the ENTIRE `promotion_model: ldr_main` fleet, not just deployment-service —
  deployment-service's LDR is now 720 commits ahead of `main` with zero promotion since ~16:20 on 2026-07-29.

  Ruled out via direct evidence (not guesses): - **NOT a YAML/schema bug in the workflow file**: the exact same commit
  `df93312bddda...` succeeded at
    2026-07-29T18:15:03Z (run `30479053659`) then failed with `startup_failure` at 18:30:03Z (run `30480196705`) —
    content-identical, so it cannot be a parse/schema error in the file's own content. Confirmed no duplicate YAML
    keys (checked with a custom PyYAML loader that flags dup keys PyYAML's default silently tolerates), both files
    (`ldr-to-main-promote-fleet.yml`, its `notify-slack.yml` reusable callee) parse clean.
  - **NOT a billing/hosted-minutes exhaustion**: `ldr-to-main-promote.yml` is 100% self-hosted
    (`runs-on: [self-hosted, glue]`, no reusable-workflow call to anything hosted) and fails identically — self-hosted
    runner minutes are never billed, so a spending-limit block cannot explain this workflow's failure.
  - **NOT a self-hosted runner pool outage**: `GET /repos/IggyIkenna/unified-trading-pm/actions/runners` shows all 8
    `glue-*`/`writer-*` runners `status: online`, `busy: false` at time of filing.
  - **NOT repo-level Actions being disabled**: `GET /repos/IggyIkenna/unified-trading-pm/actions/permissions` →
    `{"enabled": true, "allowed_actions": "all"}`.
  - **NOT a publicly-declared GitHub-wide incident**: `githubstatus.com/api/v2/incidents.json` shows an "Incident with
    Actions" 2026-07-29T15:26–16:00Z (already resolved, and 2.5h before the 18:30 onset — doesn't match) and nothing
    else touching Actions in the 18:30-onward window.
  - **Reproduced live, not just historical**: manually ran
    `gh workflow run ldr-to-main-promote.yml --repo IggyIkenna/unified-trading-pm --ref live-defi-rollout -f
    dry_run=true` at 2026-07-30T04:35:04Z — immediately got another `startup_failure` (run `30514283566`, `jobs: []`),
    ruling out anything specific to the VM heartbeat script's exact invocation (no `-f` flags) vs a manual one (with
    `-f`).
  - `gh run view <id>` on every failing run prints only the generic
    `"This run likely failed because of a workflow file issue."` banner — GH gives no further detail via CLI/REST for
    a `startup_failure`; the `check-suites`/`check-runs` REST endpoints 403 for this PAT
    (`"Resource not accessible by personal access token"`), so root-causing further requires either the GH App token
    (used inside the job, not available to a CLI session) or operator eyes on the github.com web UI (which sometimes
    shows an account-level banner/notice a REST PAT cannot see).

  A SEPARATE but likely-related symptom in the SAME window: native `schedule:` (cron) triggers went completely silent
  for multiple OTHER workflows in `unified-trading-pm` around the same time — not `startup_failure`, just ZERO new run
  records at all: `ci-status-consolidator.yml` (hourly cadence) last fired 2026-07-29T17:37:28Z, nothing since;
  `ldr-ci-monitor.yml` last fired 2026-07-29T18:21:13Z, nothing since. By contrast, `push`/`pull_request`-triggered
  workflows (e.g. `quality-gates-v2.yml` on PRs) kept succeeding normally through the same window — human/webhook-driven
  triggers are unaffected; only `schedule:` and API-driven `workflow_dispatch` are.

  **Working theory (unconfirmed, needs operator verification)**: a GitHub-side automation-throttle specific to this
  account/repo, targeting `schedule:` + `workflow_dispatch` trigger paths specifically (both are "GitHub decides when to
  run this, not a human clicking a button" paths) while leaving push/PR webhooks alone. The VM heartbeat script has been
  calling `workflow_dispatch` on this repo every ~5–15 min for an extended period (see
  `scripts/orchestrator/ldr-to-main-promote-heartbeat.sh`), and `ldr-to-main-promote-fleet.yml`'s own cron is
  over-declared to `*/5 * * * *` (see its top-of-file comment, 2026-07-18) — high-frequency automated dispatch is
  exactly the pattern GitHub's abuse-rate-limiting targets. This cannot be confirmed via REST API with the available PAT
  (no `checks:read`, no billing-scope access) — it needs a human to check the github.com account/repo Actions UI for a
  rate-limit/abuse banner, and/or check email for a GitHub compliance notice.
status: resolved
nature: issue
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [meta]; content is a GitHub Actions
  # ldr-to-main-promote workflow startup_failure incident, squarely ci-tranche (CI/CD pipeline mechanics).
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, ldr-to-main, promote-fleet, github-actions, startup-failure, automation-throttle, P0]
related:
  - /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md
  - /plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
  - /codex/08-workflows/ci-cd-flow.md
created: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: cicd
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,
    /codex/08-workflows/ci-cd-flow.md,
    scripts/orchestrator/ldr-to-main-promote-heartbeat.sh,
    scripts/cicd/promotion_lag_monitor.py,
  ]
source:
  "cicd agent, slot-11, follow-on discovery while diagnosing
  ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md, 2026-07-30"
resolved_by:
  interactive session, 2026-07-31 — GitHub Actions billing wall (root cause) confirmed cleared via live gh run checks
---

> **🟢 RESOLVED 2026-07-31** — root cause (GitHub Actions billing wall) confirmed cleared via live `gh run` checks in an
> interactive session.

## What I found

See summary above for the full evidence chain. In short: the two workflows that drive ALL LDR→main promotion for the
`promotion_model: ldr_main` fleet have been unable to even start a job for ~10h+ and counting, while every other trigger
path (push, pull_request, repository_dispatch) keeps working normally. This is a live, currently-open outage, not a
historical one.

## Why it matters

- Every repo with `promotion_model: ldr_main` (deployment-service confirmed; likely others) is silently accumulating
  unshippable LDR commits with no path to `main` — deployment-service alone is 720 commits ahead as of filing.
- `unified-trading-pm`'s own standing LDR→main PR (`ldr-to-main-promote.yml`) is equally blocked, so PM's own
  `docs(plans):` direct-push carve-out commits (this doc's own commit included) have no drain path to `main` either
  until this clears.
- The CLAUDE.md HARD RULE "Plans run to actual completion... Data pipeline correctness is the heartbeat" doesn't
  directly gate CI infra, but a 10h+ silent fleet-wide promotion stall is exactly the kind of "big finding" (cross-repo,
  SSOT-adjacent automation failure) the findings-triage rule requires escalating rather than quietly reporting.

## Recommended decision (needs operator — [OPERATOR])

- [x] ✅ **RESOLVED/MOOT 2026-07-31** — [OPERATOR] P0. Check the github.com web UI for a rate-limit/abuse-flag banner.
      Superseded by the sibling doc's finding: this was the same account-level GitHub Actions billing/spending-limit
      wall as `github_actions_billing_wall_recurrence_2026_07_29.md` (identical `startup_failure`/`jobs:[]` signature,
      identical timing), not a throttle specific to this workflow's dispatch frequency. Symptom already self-cleared per
      this doc's own 2026-07-30 slot-3 log (5/5 consecutive successes from 21:52Z) and re-confirmed independently
      2026-07-31T08:16Z (real run durations + a clean full LDR→main promote chain on `instruments-service`). No
      throttle-specific action needed.
- [x] ✅ **RESOLVED/MOOT 2026-07-31** — [OPERATOR] P0. Decide whether to reduce heartbeat/cron dispatch frequency. Moot
      — root cause was the account-level billing wall, not dispatch-frequency-triggered throttling; no frequency change
      needed.
  - [x] ✅ **RESOLVED/MOOT 2026-07-31** — [CI] P1. File the concrete fix once root cause confirmed. Moot per above — the
        root cause was the billing wall (now cleared), not a dispatch-frequency issue requiring a fix here.
- [x] ✅ **MIGRATED 2026-08-02** (operator ruling, `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 3) — both
      prevention todos below moved into `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s
      "Migrated prevention todos from resolved incidents" section. Original text preserved there verbatim with a source
      citation back to this doc. **CLOSED 2026-08-09** (`ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 1
      reconciliation), per the 2026-07-31 na-eligibility-audit verdict's own "cite/close lines 128 and 132-144"
      follow-up below: both migrated items shipped — the `[SCRIPT] P2` standing monitor via
      `unified-trading-pm@ccb1d7b10` (verified ancestor of `origin/live-defi-rollout`;
      `scripts/cicd/promote_fleet_startup_failure_monitor.py` + `promote-fleet-startup-failure-monitor.yml`, 2026-08-02)
      and the `[CI] P1` auto-merge-arm fix + `ARM_FAILED`-tally bug via `unified-trading-pm@4bf65b67c` (verified
      ancestor; 2026-08-02) — both landed via batch1 (batch1's own todos citing this doc as Source, not batch4), which
      `ci_satellite_ao_dispatch_batch4_2026_07_31.md` todos 7/8 independently confirmed live and correctly marked
      `DONE-ELSEWHERE` rather than re-shipping. Zero remaining checkbox or prose work in this doc.

- **2026-07-30 (slot-2, data_engineering craft)**: 10th consecutive re-check of the sibling VERIFY-gate todo in
  `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` — identical unmet state, no new information.
  `market-tick-data-service` most-recent-merged PR to `main` still `#773`; current open promote PR is now `#792`
  (`promote/market-tick-data-service/d072b0358b33`, opened `2026-07-30T23:31:17Z`, `5b5caffa` confirmed carried via
  `git merge-base --is-ancestor`), `mergeStateStatus: UNSTABLE`, `autoMergeRequest: null`, `mergedAt: null` — same
  never-requested-auto-merge shape slot-3 first diagnosed (PRs #788→#792, 5 regenerations since). Filed a `/blocked`
  escalation on this session recommending the sibling todo be PARKED (`backlog.yaml` `priority: 999` +
  `priority_override: true`, per `RULES.md` § 4) since slot-9 already made this recommendation one cycle ago and no
  action has been taken — every re-dispatch of that todo re-derives the same already-tracked root cause above and burns
  a worker slot for zero new signal until this `[CI] P1` fix actually ships.

## Evidence

- First failing run (transition point): `30480196705`, created `2026-07-29T18:30:03Z`, headSha `df93312bddda...` (same
  SHA succeeded 15 min earlier in run `30479053659`).
- Reproduced live: manual dispatch → run `30514283566`, created `2026-07-30T04:35:22Z`, `startup_failure`, `jobs: []`.
- Sibling workflow same pattern: `ldr-to-main-promote.yml` runs `30514040213`/`30513369229`/etc, all `startup_failure`
  since ~2026-07-30T01:00Z window checked (same continuous pattern as the fleet workflow).
- Runner pool health: `GET /repos/IggyIkenna/unified-trading-pm/actions/runners` → 8/8 `online`, `busy: false`.
- Repo Actions permissions: `GET /repos/IggyIkenna/unified-trading-pm/actions/permissions` →
  `{"enabled":true,"allowed_actions":"all"}`.
- `ci-status-consolidator.yml` (hourly `schedule:`) — last run `2026-07-29T17:37:28Z`, nothing since.
- `ldr-ci-monitor.yml` (`schedule:`) — last run `2026-07-29T18:21:13Z`, nothing since.
- Public status feed checked: `https://www.githubstatus.com/api/v2/incidents.json` — no matching open/recent Actions
  incident for the 18:30Z-onward window.
- Origin (narrower, now-resolved question): deployment-service promote PRs `#594`–`#603`, all `MERGED`, spanning
  `2026-07-28T22:07:48Z`–`2026-07-29T16:20:03Z` — confirms the original doc's todo 1 (did deployment-service
  self-resolve within a few ticks) is answered YES, no code fix was needed for that narrower question.

## Progress Log

- **2026-07-31 (interactive)**: root cause identified as the same account-level GitHub Actions billing wall tracked in
  `github_actions_billing_wall_recurrence_2026_07_29.md`, confirmed cleared live (real run durations + a clean
  end-to-end LDR→main promote chain on `instruments-service`). Flipped the 2 `[OPERATOR]` P0 todos + their gated `[CI]`
  P1 sub-item to resolved/moot; `status` flipped to `resolved`. The `[SCRIPT] P2` standing monitor and the separate
  `[CI] P1` market-tick-data-service auto-merge bug (unrelated — a `gh pr merge --auto` gap, not caused by the billing
  wall) are already tracked in `ci_satellite_ao_dispatch_batch4_2026_07_31.md` per the na-eligibility-audit verdict
  below — left open, untouched here to avoid duplicating that batch's coverage.
- **2026-07-30 (slot-11)**: filed, evidence-gathered, escalated to main via chat (message id 2649). Awaiting operator
  check of the GH account/repo Actions UI (not REST-accessible with the available PAT).
- **2026-07-30 (slot-6)**: independent blast-radius confirmation from a DIFFERENT task
  (`defi_venue_pipeline_to_live_ao_build_2026_07_30.md` todo 2) — `market-tick-data-service` is ALSO affected: no
  `chore(promote): LDR → main` PR has merged since #773 (2026-07-28T13:56:40Z), and
  `origin/main..origin/live-defi-rollout` is now **823 commits**. This confirms the incident is genuinely fleet-wide
  (not just deployment-service) and still ongoing at time of writing (`ldr-to-main-promote.yml` still showing
  intermittent `startup_failure`, not fully recovered). Re-confirms `assigned_vm: NA` + P0 is the correct routing —
  already on the operator's radar, no new escalation needed, just corroborating evidence for whoever investigates next.
- **2026-07-30 (slot-3, data_engineering craft)**: the fleet-dispatch-level `startup_failure` itself has now recovered
  (5/5 consecutive successes on both `ldr-to-main-promote.yml`/`-fleet.yml` through `21:52Z`, confirmed by 8 straight
  worker re-checks from slot-12 onward) — but a narrower, likely-related symptom persists: `market-tick-data-service`
  promote PRs keep getting regenerated (#788→#789→#790→#791) and superseded before merging, even once fully green.
  Root-caused PR #791 specifically: `autoMergeRequest: null` despite `mergeable: MERGEABLE` and every required check
  passed — GitHub was never asked to auto-merge it. Filed as new todo `[CI] P1` above with the concrete mechanism to
  check (does the PR-creation step actually call `gh pr merge --auto` / `enablePullRequestAutoMerge`). Did not attempt a
  GH-side fix myself (out of a worker's scope per this doc's own instruction) — declined + skipped the VERIFY-gate task
  per the established posture.

- **2026-07-30 (slot-11, data_engineering craft)**: Nth consecutive re-check (≥11 now, slot-12 through slot-11) of the
  sibling VERIFY-gate todo. **Partial progress**: check (a) now PASSES — `ldr-to-main-promote.yml` / `-fleet.yml` show
  5+ consecutive `success` runs each through `2026-07-30T23:53Z`, no `startup_failure` since the slot-3 recovery. Checks
  (b)/(c) still UNMET, same signature slot-3 diagnosed: `market-tick-data-service`'s most-recently-merged-to-`main` PR
  is still `#773` (2026-07-28); open promote PR is now `#792` (`promote/market-tick-data-service/d072b0358b33`),
  `5b5caffa` confirmed carried but NOT yet an ancestor of `main` (`git merge-base --is-ancestor 5b5caffa origin/main`
  fails), `mergeStateStatus: UNSTABLE`, `mergeable: MERGEABLE`, `autoMergeRequest: null`, `mergedAt: null` — identical
  never-requested-auto-merge shape, PR #792 is the 6th regeneration since #788. Did not attempt the GH-side auto-merge
  fix (out of worker scope). Skipping rather than filing a 3rd `/blocked` — slot-2 already recommended PARKing this
  VERIFY-gate todo one cycle ago (`priority: 999` + `priority_override: true` per `RULES.md` § 4) and it is still
  un-actioned two cycles later; every re-dispatch since has re-derived the identical already-tracked root cause for zero
  new signal. Flagging to main via progress message rather than re-escalating in this doc a third time.

- **2026-07-31 (slot-16, data_engineering craft)**: another consecutive re-check of the sibling VERIFY-gate todo, same
  unmet state, updated evidence only. Check (a) still PASSES (5+ consecutive successes on both promote workflows through
  `2026-07-31T03:30Z`). Checks (b)/(c) still UNMET: `market-tick-data-service`'s most-recently-merged-to-`main` PR is
  still `#773`; open promote PR has regenerated again to `#793` (`promote/market-tick-data-service/d74984b03948`, opened
  `2026-07-31T02:00:59Z`), `5b5caffa` confirmed an ancestor of the current LDR head, `mergeStateStatus: UNSTABLE`,
  `mergeable: MERGEABLE`, `autoMergeRequest: null`, `mergedAt: null` — identical never-requested-auto-merge shape as
  every prior check. Not filing another `/blocked` on THIS doc (per slot-11's posture) — did file one on the sibling
  VERIFY-gate todo itself, since that park recommendation is still unactioned after 12+ cycles. Did not attempt the
  GH-side fix (out of worker scope; the concrete fix — verify the PR-creation step actually calls `gh pr merge --auto`/
  `enablePullRequestAutoMerge` — is already fully specified in the `[CI] P1` todo above, unchanged).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **KEEP-NA-STALE (already-duplicated) — mixed doc, 5 open
todos split cleanly.** The two `[OPERATOR] P0` items (web-UI rate-limit check; heartbeat-frequency decision) and their
gated `[CI] P1` follow-up ("once the operator confirms root cause") are genuinely **KEEP-NA valid** — human-only
diagnostics a worker cannot perform (checks/billing API both 403 for the available PAT scope), still unanswered. The
remaining two — `[SCRIPT] P2` (3+-consecutive-`startup_failure` monitor) and `[CI] P1` (root-cause + fix the missing
`gh pr merge --auto` arm on MTDS promote PRs) — are **already verbatim-extracted into**
`/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (same-day sibling `/ag-closeout-audit ci` draft,
each citing this doc as Source, explicitly noting the auto-merge fix is "not gated on this doc's own operator-only
items"). Not reclassifying either — would duplicate batch4's already-drafted fix once it activates. Follow-up once
batch4 ships or archives unshipped: cite/close lines 128 and 132-144 here. Cross-skill population-overlap tracked in
`/plans/active/issues/na_and_ag_closeout_audit_population_overlap_2026_07_31.md`.
