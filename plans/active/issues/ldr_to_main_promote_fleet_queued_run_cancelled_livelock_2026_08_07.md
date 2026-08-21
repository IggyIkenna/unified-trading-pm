---
doc_type: issue
title:
  ldr-to-main-promote-fleet's single concurrency group starves under heavy multi-agent trigger volume — queued runs keep
  getting superseded before ever starting a job
summary: >-
  Since ~2026-08-07T11:23Z (the moment its sibling ldr-to-main-promote.yml's own runs-on flipped self-hosted→
  ubuntu-latest in the same commit, ruled out as cause — see evidence), every ldr-to-main-promote-fleet run shows
  conclusion=cancelled with ZERO jobs ever created (gh api .../jobs → total_count:0, not a mid-run cancellation).
  Account-wide GitHub-hosted concurrent-job saturation was the leading hypothesis but is RULED OUT: (1) operator
  confirmed no account-wide cap is in effect; (2) other workflows in the same repo (ci-status-update, sit-gate-stuck-
  detector, glue-pool-starvation-monitor, promote-fleet-startup-failure-monitor) ran successfully throughout the same
  window; (3) most tellingly, ldr-to-main-promote.yml — the sibling workflow dispatched by the SAME 15-min heartbeat at
  the SAME instant, verified via live SSM inspection of the orchestrator VM's systemd timer (firing exactly on its
  documented */15 schedule, no drift) — succeeded on every single run in the same window, one even mid-flight
  in_progress when checked. The heartbeat itself is fully healthy and not the cause. The asymmetry between the two
  sibling workflows is the real lead: ldr-to-main-promote-fleet is the one every per-repo agent verifying a fleet-wide
  promotion naturally triggers via workflow_dispatch (confirmed: at least 3 different agents in this session alone did
  exactly this for instruments-service, market-data-processing-service, and unified-trading-ci), while
  ldr-to-main-promote.yml (PM-only) is not a natural target for that pattern. Combined with its own native */5 schedule
  AND the 15-min heartbeat AND ad-hoc manual dispatches from potentially multiple concurrent sessions, the trigger rate
  for THIS SPECIFIC concurrency group appears to exceed whatever rate at which GitHub actually promotes a queued run to
  in_progress for it — each new arrival keeps re-winning the single queued-waiter slot before the previous one is ever
  allocated a runner. A genuine GitHub-side incident today (ARC runner pods stuck idle, job assignment failures,
  status.github.com, marked resolved) may have contributed a baseline layer of flakiness on top, but does not explain
  the sustained, isolated-to-one-workflow pattern by itself. Net effect: no repo has promoted from live-defi-rollout to
  main since ~11:23Z, which also blocks live-verifying the
  semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md fix end-to-end (fix is shipped and correct, but no tag
  can mint until a real promotion happens).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promotion-lag, contention, github-actions, monitoring-gap]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /plans/archive/2026_08/issues/ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source: "ci-reconcile sweep, 2026-08-07, waiting on semver-agent fix live verification"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    .github/workflows/ldr-to-main-promote-fleet.yml,
    .github/workflows/promote-fleet-startup-failure-monitor.yml,
    scripts/cicd/glue_pool_starvation_monitor.py,
    scripts/cicd/promotion_lag_monitor.py,
    /codex/08-workflows/ci-cd-flow.md,
    scripts/cicd/promote_fleet_startup_failure_monitor.py,
  ]
---

# ldr-to-main-promote-fleet stuck — queued runs cancelled before ever starting

## What was measured (live, 2026-08-07, ~12:00Z-14:24Z)

- Every run in this window: `status=completed conclusion=cancelled`, `gh run view <id>` shows an EMPTY jobs list (no job
  ever started, not a mid-run cancellation).
- Mix of `event=schedule` (every 5 min, expected) and `event=workflow_dispatch` (multiple, from at least this session's
  own agents AND at least one other concurrent session — `14:00Z` and `14:15Z` workflow_dispatch events fired after this
  session stopped dispatching new agents).
- `concurrency.cancel-in-progress: false` on this workflow — confirmed in source. A queued (not started) run being
  superseded by a newer trigger is normal GitHub Actions concurrency-group behavior regardless of this flag (the flag
  only protects an already-IN-PROGRESS job); what's abnormal is that NOTHING has transitioned queued→in_progress in 2+
  hours despite `runs-on: ubuntu-latest`, which should have ample hosted capacity.
- `promote-fleet-startup-failure-monitor.yml` (5 most recent runs, spanning this exact window) reports `success`
  throughout — it is not catching this failure mode.
- Fleet-wide effect: `batch-live-reconciliation-service` main is 267 commits behind live-defi-rollout with no open
  promote PR; `promotion_lag_monitor.py` did not flag it as lagging yet (likely still inside its own grace window).

## Not fixed autonomously — why

The fix here is a design choice with fleet-wide behavioral consequences, not a mechanical patch: debouncing/rate-
limiting manual dispatches of a shared fleet-critical workflow, or changing its concurrency semantics, changes how every
agent's "did my repo promote yet" verification pattern needs to work going forward. That's worth an operator decision on
the actual mechanism (see options below), not a same-session unilateral change to CI infrastructure this central to the
whole fleet's shipping pipeline.

## Evidence chain (in order investigated, ruled out is marked)

1. ❌ RULED OUT — account-wide GitHub-hosted concurrent-job cap (operator confirmed no cap in effect).
2. ❌ RULED OUT — general GitHub-side outage (other workflows in the same repo ran fine throughout).
3. ❌ RULED OUT — heartbeat misconfiguration (live SSM check: systemd timer firing exactly on its documented `*/15`
   schedule, zero drift, both dispatches per tick succeed at the API-call level).
4. ❌ RULED OUT (as sole cause) — the same-commit self-hosted→ubuntu-latest revert (`c8cd56251e`, landed 11:23:30 UTC,
   suspicious timing match): the sibling workflow changed `runs-on` in the identical commit and works perfectly, so the
   revert itself isn't the mechanism, though its timing coincides with when the pattern was first observed.
5. ✅ LEADING, evidenced — trigger-volume asymmetry: `ldr-to-main-promote-fleet` uniquely absorbs schedule (`*/5`) +
   heartbeat (`*/15`, both workflows) + ad-hoc `workflow_dispatch` from every per-repo agent verifying its own repo's
   promotion (confirmed 3 separate agents did this today) + potentially other concurrent sessions. Its PM-only sibling
   shares the schedule+heartbeat baseline but not the ad-hoc per-repo-verification trigger pattern, and never starved.
6. Contributing, unconfirmed — a same-day GitHub Actions incident (ARC runner pods stuck idle, job assignment failures)
   may add background flakiness but doesn't explain the isolation to one specific workflow.

## ACTUAL root cause found 2026-08-07 ~17:42Z — corrects the trigger-volume theory above

The trigger-volume-asymmetry theory (§ Evidence chain item 5) was **wrong as the primary cause** — the convention-rule

- schedule-trim fix shipped against it (Todo 1) did NOT clear the livelock; re-checked ~3 hours after shipping,
  `batch-live-reconciliation-service` was still 267 commits behind main, unchanged, and a fresh manually-triggered run
  still showed `total_count:0` jobs.

**The real mechanism**: `python3 scripts/cicd/glue_pool_starvation_monitor.py --repo IggyIkenna/unified-trading-pm` (the
actual script behind the `glue-pool-starvation-monitor` Slack alert — read it, don't just trust the alert text) listed
run `31176101874` ("promote-ldr-to-main", queued 344+ minutes) among 10 glue-starved jobs. Traced it directly:

```
gh api repos/IggyIkenna/unified-trading-pm/actions/runs/31176101874 →
  {"name":"ldr-to-main-promote-fleet","path":".github/workflows/ldr-to-main-promote-fleet.yml",
   "event":"schedule","head_branch":"main","created_at":"2026-08-07T11:56:22Z","status":"queued"}
gh api .../31176101874/jobs → {"name":"promote-ldr-to-main","labels":["self-hosted","glue"],"status":"queued"}
```

**This is the chicken-and-egg bug**: a `schedule:`-triggered GitHub Actions run ALWAYS uses whatever version of the
workflow file exists on the repo's DEFAULT branch (`main`) — never `live-defi-rollout`, regardless of what's on LDR
(this is a documented GitHub Actions rule, already noted elsewhere in this repo's own CLAUDE.md: "A scheduled/`push`
workflow fires ONLY from the DEFAULT branch"). The `runs-on: [self-hosted, glue] → ubuntu-latest` fix (`c8cd56251e`,
11:23:30 UTC) landed on LDR, but **had not yet promoted to `main`** — because the very promoter that would carry it
there was the thing broken. So the very next native schedule tick at 11:56:22Z fired against the STILL-OLD version of
the workflow on `main`, declaring `runs-on: [self-hosted, glue]` — a pool with permanently ZERO runners (see
`self_hosted_runner_public_repo_revert_2026_08_05.md`, todo 21 DONE). That job queued forever, waiting for a runner that
will never appear.

Because `concurrency.cancel-in-progress: false`, and GitHub Actions concurrency groups track exactly one "currently
claiming the group" run, this permanently-unstartable zombie run appears to have been occupying that single slot — so
every SUBSEQUENT trigger (even `workflow_dispatch` runs correctly using the FIXED ubuntu-latest spec from LDR) just
queued behind it and got superseded by the next arrival, forever, never getting a turn. Verified: this was the ONLY
currently-queued run of either promote workflow
(`gh api .../actions/runs --jq 'select(.name=="ldr-to-main- promote-fleet" or .name=="ldr-to-main-promote") | select(.status=="queued" or .status=="in_progress")'`
→ exactly this one run, nothing else).

**Fix applied**: `gh run cancel 31176101874` at ~17:42Z. **Live-verified working**: triggered a fresh
`gh workflow run ldr-to-main-promote-fleet.yml` immediately after — run `31203568988` reached `status: in_progress` (job
`promote-ldr-to-main: in_progress`) at 17:44:23Z — **the first non-cancelled run of this workflow all day**.

**Side finding, false-positive, filed separately below**: while investigating, found `glue-runner-crash-loop- watchdog`
paging CRITICAL on 4 repos' (e2e-testing, strategy-service, market-tick-data-service, ml-service) dedicated self-hosted
runners for "continuously active >3h, likely hung." Live SSM check (`systemctl status` + `ps`) on `i-042a6332509482556`
showed **3.3s total CPU time** across 3h+ of "active" runtime for all 4, and GitHub's own runner API confirms
`status:online, busy:false` for each — these are healthy IDLE runners, not hung processes; the watchdog's ">10800s
active" heuristic doesn't check actual CPU/busy state, so it false-positives when overall job throughput craters (as it
did fleet-wide during this incident) rather than when a runner is actually wedged. Did NOT restart these services —
restarting a healthy runner achieves nothing and would just reset the false-positive's timer. Filed as its own
coverage-gap todo below (same class as `ci_failure_watcher.py`'s bugs and `promote-fleet-startup-failure-monitor.yml`'s
blind spot, all found 2026-08-07).

**Still open**: confirm this stays clear — the operator's explicit instruction (2026-08-07) is to keep this
`/ci-reconcile` session running until a full 60 consecutive minutes pass with zero new CI alerts, not to declare victory
on one successful `in_progress` transition. If the SAME class of chicken-and-egg zombie recurs (any future workflow-file
fix that changes `runs-on:` needs to reach `main` via a working promoter before the OLD spec stops being able to
zombie-queue on the next native schedule tick — a structural risk any time this exact workflow's own `runs-on:` changes
again), the mitigation is: after any fix to a `schedule:`-triggered workflow's `runs-on:`, check for and cancel any
pre-existing queued run of that same workflow before/immediately after shipping, don't assume the fix alone is
sufficient.

## Todos

- [x] 1. ✅ [OPERATOR] P1. **Decided 2026-08-07 — ship (b) + (d)-lite now, defer (a).** Operator chose the convention
      fix + schedule trim as the immediate action; the in-workflow self-debounce (option (a) below) is deferred, gated
      on whether the problem recurs after these two land (observe via run history / live recheck, not built
      preemptively). - **(b) rate-limit ad-hoc verification — DONE.** Added a HARD RULE against
      `gh workflow run ldr-to-main-promote-fleet.yml` used just to check promotion status, in TWO places (both needed —
      see `/codex/05-infrastructure/claude-code-settings-symlink.md` for why one alone doesn't cover both AO workers and
      Task-tool sub-agents): `unified-trading-pm/cursor-configs/CLAUDE.md`'s `## CI verification after every push`
      section (auto-loaded by every AO top-level worker + interactive session) and
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`'s `## Async-wait / background work` section (pasted at every
      Task/Agent-tool sub-agent spawn, which is what actually caused 3+ of today's confirmed triggers). Both point to
      `promotion_lag_monitor.py`'s live output / `gh pr list --search "chore(promote)"` as the correct check. -
      **(mechanical, folds into (d)) trim the redundant native schedule — DONE.** `*/5` → `*/15` in
      `ldr-to-main-promote-fleet.yml`, matching `ldr-to-main-promote-heartbeat.timer`'s already-deterministic `*/15`
      cadence — the native schedule was compensating for GHA's own unreliable delivery, a problem the heartbeat already
      solves; cuts baseline trigger volume with no SLA regression (still ≤15 min worst case).
- [x] ✅ [OPERATOR] P1 (deferred, conditional). **CHECKED 2026-08-09 (operator-directed, interactive session) — NOT
      recurred, self-debounce not needed, closing as moot.** Checked live via
      `gh api repos/.../actions/workflows/ldr-to-main-promote-fleet.yml/runs?status=cancelled`: 105 historical cancelled
      runs total, but the most recent is `2026-08-07T17:19:08Z` — BEFORE the 17:42Z zombie-cancel fix (todo 2), not
      after. Zero cancelled runs since. Separately confirmed the 50 most recent runs overall (spanning
      `2026-08-08T23:57:13Z`→`2026-08-09T08:27:18Z`, ~8.5h) are 100% `success`. ~39 hours clean on the specific
      cancelled+zero-jobs signature this todo exists to catch. **(a) in-workflow self-debounce is NOT needed** — do not
      build it absent a fresh recurrence. Note: this closes only THIS narrow "has the livelock signature recurred"
      question — it does NOT itself clear the broader todo below (the 60-min zero-new-alerts bar spans other
      sub-incidents this check didn't verify).
- [x] 2. ✅ [DEVOPS] P1. **Real root cause found + fixed 2026-08-07 ~17:42Z — see section above.** Was a zombie queued
      run (`31176101874`) from a `schedule` trigger that fired against `main` before the `runs-on:` fix had promoted
      there, permanently occupying the workflow's one concurrency slot. Cancelled it; a fresh run immediately reached
      `in_progress` (`31203568988`) for the first time all day. NOT the trigger-volume theory from Todo 1 — that fix was
      still worth keeping (real, if secondary, load reduction) but did not by itself clear this.
- [x] 3. ✅ [DEVOPS] P1. **Partially confirmed 2026-08-07 ~18:12Z.** `ldr-to-main-promote-fleet` runs are clean
      (success, jobs created) since the 17:42:47Z fix — `31203568988`, `31203749677`, `31203965610`, `31204912834`, all
      `success`, zero cancelled/zero-jobs runs in that window. Real `chore(promote)` PRs ARE merging end-to-end
      fleet-wide (16+ repos confirmed via `gh search prs "promote" in:title --owner IggyIkenna`, e.g.
      `instruments-service#1099`, `strategy-service#504`, `execution-service#560`, `unified-trading-api#511`, etc., all
      merged 17:46-18:06Z). `market-tick-data-service` confirms a REAL end-to-end tag mint (`v0.105.0` at 17:49:26Z,
      `v0.106.0` at 18:06:55Z, each immediately following its own promote-merge) — but MTDS was NOT part of the
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` template rollout (excluded, pre-existing test
      blocker), so this proves the FLEET PROMOTER is healthy, not that the squash-promote patch-fallback fix itself
      works. The 60-consecutive-minute clock is still running (started ~17:42Z) — do not mark `resolved` yet.
- [x] 4. ✅ [DEVOPS] P1. **NEW REGRESSION found 2026-08-07 ~18:15Z, agent dispatched to fix.** The
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` template rollout (21 repos) broke GH's Actions
      schema parser on at least `instruments-service` and `unified-trading-api`: every push-triggered `semver-agent.yml`
      run since the rollout landed on `main` (~17:46Z) creates ZERO jobs and fails with GitHub's own "This run likely
      failed because of a workflow file issue" — confirmed via `gh api repos/<repo>/actions/runs/<id>/jobs` returning
      `{"total_count":0}` AND via `gh api repos/<repo>/actions/workflows` showing the registered workflow `name` has
      fallen back to the raw file path (`.github/workflows/semver-agent.yml`) instead of the YAML's own
      `name: Semver Agent` — GitHub's own tell that its schema parser rejected the file, even though
      `python3 -c "import yaml..."` and `actionlint` both report it as clean (ruled out: no duplicate keys, no
      CRLF/hidden-char issues, indentation of the new `run: |` content visually matches). Root cause not yet found
      manually; dispatched a dedicated agent (2026-08-07 ~18:20Z) to bisect the two added hunks (concurrency group +
      patch-fallback bash block), fix `scripts/workflow-templates/semver-agent.yml.tmpl`, re-roll fleet-wide via
      `rollout-workflow-templates.sh`, and re-verify all 21 repos. **This directly blocks Todo 3's remaining proof**
      (the patch-fallback fix minting a real tag) — MTDS's tag mint does NOT count as proof of that fix since MTDS was
      excluded from the rollout. See `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` for the fix's own
      follow-up section once the dispatched agent lands it.
- [x] ✅ [DEVOPS] P2. **RESOLVED — DONE (plan_reconciler Phase -1, 2026-08-16).** `unified-trading-pm@c526128fb0`
      (+`ff435d5b53` refinement), ancestor of HEAD, title cites this doc by filename — adds `fetch_queued_runs()` /
      `stuck_queued_runs()` for the exact "status=queued longer than N min, no newer completed run" signature.
      Independently re-confirmed by `ci_satellite_ao_dispatch_batch13_2026_08_13.md:158-162`. Was: **Agent dispatched
      2026-08-07 ~18:20Z.** Harden `promote-fleet-startup-failure-monitor.yml` to also
  catch "queued, never started for an extended period" as its own failure signature — it currently reports success
  throughout this entire incident (same class of coverage gap as `ci_failure_watcher.py`'s glue-starvation/
  escalation-label bugs found earlier 2026-08-07).
- [x] ✅ [DEVOPS] P2. **RESOLVED — DONE (plan_reconciler Phase -1, 2026-08-16).** `unified-trading-pm@c0003b9e28`
      (dated same day 2026-08-07 20:00, ancestor of HEAD) adds `runner_busy_status()` — a GitHub-API busy-check consumed
      by `is_wedged()` — directly fixing the exact incident (execution-service/glue-1 3.1h/busy:false false page). Was:
      **Agent dispatched 2026-08-07 ~18:20Z.** `glue-runner-crash-loop-watchdog`'s ">10800s active =
  probably hung" heuristic false-positived on 4 healthy, idle, `busy:false` runners (e2e-testing, strategy-service,
  market-tick-data-service, ml-service) during this incident's low-throughput window — add an actual CPU-time or
  GitHub-API `busy` check before paging, not wall-clock active-duration alone. Do not restart these services; they were
  never actually stuck.
- [x] ✅ [DEVOPS] P3. **Resolved 2026-08-07 ~18:26Z.** Cross-checked
      `asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md` against this incident — CONFIRMED unrelated: that
      doc describes 38 GCP Cloud Scheduler jobs (`asia-northeast1`, GCP region naming, project `central-element-323112`)
      pointing at deleted Cloud Run Jobs. No GitHub Actions `schedule:`/`concurrency:`/self-hosted-runner mechanism, no
      AWS `ap-northeast-1`, no shared workflow file. No `related:` link warranted — zero mechanistic overlap.
- [x] ✅ [DEVOPS] P1. **New, found + fixed 2026-08-07 ~18:20-19:48Z.** `ldr_to_main_fleet_promote.sh`'s
      `provenance_check_ok()` was called with `$PR_URL` (the full PR URL, e.g. `https://github.com/.../pull/656`)
      instead of the bare PR number at its PR-creation call site (line ~966) — the other two call sites (re-arm paths)
      already passed the correct `$PR_NUM`. This flowed into the `provenance_blocked` escalation dispatch's `pr_number`
      client_payload field, which `escalate-to-orchestrator.yml` passes to `jq --argjson pr "..."` (requires a bare JSON
      number, a URL breaks it — confirmed via `gh run view <id> --log-failed` →
      `jq: invalid JSON text passed to --argjson`) and to `gh pr edit "$PR_NUMBER" --add-label` (also needs a bare
      number). Every provenance-block escalation via the PR-creation path was silently failing to reach the
      orchestrator/Slack — found while investigating a burst of 16 "Escalate to Orchestrator" runs (mostly
      cancelled/failed) around `client-reporting-api#656`. Fix: extract `${PR_URL##*/}` before calling
      `provenance_check_ok`. Shipped `unified-trading-pm@d5d2f539f0` (verified ancestor of `origin/live-defi-rollout`).
- [x] ✅ [DEVOPS] P1. **NEW incident found 2026-08-07 ~18:40Z, agent dispatched.** `glue-pool-starvation-monitor` has
      been firing CRITICAL every ~30min (confirmed STILL firing as of the 18:17:30Z run, not a stale/one-off alert) — 9
      `glue`-labelled PM jobs (`check-and-write`, `Doc frontmatter gate (LDR)`, `sweep`, `replay`, `check-and-trigger`,
      `check-stale-lock`, `Dispatch judgment wall to orchestrator`, `reconcile`) queued 6+ hours with ZERO glue jobs in
      progress. Confirmed via `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` → `{"total_count":0}` — PM
      has NO self-hosted runners registered at all right now. Host `i-042a6332509482556` (`ap-northeast-1`) has
      templated `github-glue-runner-<repo>@.service` units for 23 repos but **no `unified-trading-pm` templated unit** —
      unlike 7 sibling repos (agent-orchestrator, strategy-service, e2e-testing, features-service,
      market-tick-data-service, execution-service, ml-service) that do. This is a SEPARATE incident from the
      fleet-promoter livelock above (different label — PM's `glue` self-hosted pool, not the fleet-promoter's
      now-`ubuntu-latest` runner) — flagged directly by the operator, who also asked whether
      `glue-pool-starvation-monitor` announces a Slack RECOVERED message once fixed (not yet confirmed either way).
      Dedicated agent dispatched to root-cause + fix + verify + check/add recovery-announcement logic. **This alone
      means the "zero new issues" clean-window clock has NOT started yet as of this entry.**
- [x] ✅ [DEVOPS] P1. **Blocking the 60-min clean-window bar.** — verified MET, `ci_satellite_ao_dispatch_batch13_2026_08_13.md:163`
      ("CONFIRMED CLEAN 2026-08-14... the 60-min clean-window bar is met — exceeded ~168x over", `unified-trading-pm@e0901407f2`).
      That entry deferred reconciling this checkbox to `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`, but a
      grep of that finalize doc found zero mentions — the deferral was never honored. Flipped here directly by
      plan_reconciler 2026-08-19, independently re-verified both citations before flipping.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-07** (tranche `ci`): KEEP-NA, valid — brand-new (created today), actively-unfolding P1
incident with an explicit operator instruction to keep verifying for a full 60 consecutive minutes before declaring
victory (todo 2). Todo 1 (`[OPERATOR] P1`, deferred/conditional self-debounce) is an explicit operator-gated item. Todos
3-4 (`[DEVOPS] P2` monitor-hardening fixes) read as bounded/deterministic in isolation but are same-day follow-on
hardening from this still-active incident's own investigating session — not defaulted-to-NA-and-never-assessed.

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:4cf4337fae944d2c]: KEEP-NA,
valid — confirms the 2026-08-07 verdict, unchanged since (only context-scout touch). Todo (a) is explicit `[OPERATOR]`,
conditional/deferred; todo (the 60-min clean-window bar) is live-incident observation work, not yet confirmed cleared.
No `assigned_vm` change.

## Fleet-wide zombie-queued-run purge (2026-08-10, /ci-reconcile)

`gh run list --status queued` was polluted fleet-wide by runs that will never start — which matters because that view is
exactly what a human or agent checks when asking "is the runner pool starved?". A stale `queued` row is
indistinguishable at a glance from live work waiting on a runner.

**Purged 12 of 15** (cancel first, `DELETE .../actions/runs/<id>` where cancel 500s):

| Repo                                                               | Run(s)      | Workflow                                      | Age           |
| ------------------------------------------------------------------ | ----------- | --------------------------------------------- | ------------- |
| unified-trading-pm                                                 | 30513367555 | `ldr-to-main-promote-fleet`                   | 2026-07-30    |
| unified-trading-pm                                                 | 4 runs      | `ci-status-update`                            | 2026-05-15    |
| deployment-api / features-service / market-data-processing-service | 1 each      | retired `quality-gates.yml` / `Quality Gates` | 2026-05-15    |
| execution-service / market-tick-data-service / strategy-service    | 1 each      | retired `workspace-qg`                        | 2026-05-24/25 |
| strategy-service                                                   | 25906785079 | retired `quality-gates.yml`                   | 2026-05-15    |

The PM `ldr-to-main-promote-fleet` row is this doc's own failure mode, and `gh run cancel <id>` is the recovery
`scripts/cicd/promote_fleet_startup_failure_monitor.py`'s header already prescribes. The `ci-status-update` rows were
queued under the `manifest-update` concurrency group that WS-A Phase-3 RETIRED when that workflow stopped committing the
manifest and moved to Firestore CAS — with the group gone, nothing could ever release them. The rest are runs of
workflows that no longer exist.

**3 could NOT be removed — GitHub-side, not ours.** `strategy-service` runs 31164709790 (`quality-gates-v2`),
31164709402 (`Semver Agent`), 31164709423 (`main-backmerge-to-ldr`), all queued 2026-08-07T09:09:30Z with `jobs=0`.
`cancel` returns HTTP 500 and `DELETE` returns HTTP 403 ("Could not delete the workflow run" — the delete API refuses a
run that is not `completed`, and cancel cannot move it to `completed`). They are wedged server-side with no API escape.

**They are cosmetic only — verified, not assumed.** strategy-service's live CI is healthy (every run on 2026-08-10
succeeded). Neither standing monitor can be fooled by them: `promote_fleet_startup_failure_monitor.py` scopes to
`WORKFLOW_FILES = ("ldr-to-main-promote-fleet.yml", "ldr-to-main-promote.yml")`, and these three are none of those;
`glue_pool_starvation_monitor.py` keys on `glue`-labelled JOBS, and a run with `jobs=0` exposes no job to match. So no
false page is possible — the only cost is the polluted `--status queued` view.

**If you are checking for runner starvation**: age-filter, or expect those three strategy-service rows. They should age
out with GitHub's run retention; re-attempt the purge after that.

## Todos

- [ ] [OPERATOR] P3. Re-attempt `gh run cancel` / run-delete on strategy-service 31164709790, 31164709402, 31164709423
      once GitHub's retention has aged them out (or via support if they persist). Purely cosmetic — they pollute
      `gh run list --status queued` but provably cannot trip either standing monitor (see above). Done-when:
      `--status queued` is empty fleet-wide.

## Progress Log addendum

- **context-scout 2026-08-17**: re-verified context_scope (5 entries), unchanged.

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- Doc has materially changed since its last dated audit passes (2026-08-07, 08-09): both DEVOPS P2 monitor-hardening todos and the semver-agent-regression/glue-pool-starvation todos those audits scoped are now `[x]` RESOLVED (2026-08-16 plan_reconciler entries), and an entirely new 'Fleet-wide zombie-queued-run purge' section + todo was added 2026-08-10, so those prior verdicts are stale as to current content and were re-derived fresh here. Item 1 (60-min clean-CI-window bar before declaring...

- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid — live-reverified, not inferred. Sole open
todo (`[OPERATOR] P3`, re-attempt `gh run cancel`/delete on the 3 wedged `strategy-service` runs once GitHub's
retention ages them out) re-tested live this pass: `gh run list --repo IggyIkenna/strategy-service --status queued`
still shows all 3 runs (31164709790, 31164709402, 31164709423) queued at **328h6m** age (13.7 days, up from the
original 2026-08-07 filing); re-attempted both `gh api ... /cancel` (HTTP 500, "Failed to cancel workflow run") and
`gh api -X DELETE` (HTTP 403, "Could not delete the workflow run") on all 3 — identical failure signature to the
doc's original evidence, no change. GitHub's retention has not yet aged these out. Genuinely still not resolvable;
todo stays open, correctly OPERATOR-tagged and P3 (doc's own text: "purely cosmetic... provably cannot trip either
standing monitor"). No `assigned_vm` change.
