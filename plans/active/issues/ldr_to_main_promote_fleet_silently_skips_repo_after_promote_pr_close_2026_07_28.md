---
doc_type: issue
title:
  "ldr-to-main-promote-fleet.yml silently no-ops for a repo (no PR create, no Promoted/Blocked/Conflicted tally entry)
  after its stale promote PR is closed out-of-band — deployment-service's promote PR stayed absent across 2 full ticks"
summary: >-
  Responding to an `ldr_qg_failure` escalation (agt-7ea8ad) for deployment-service PR #576 (LDR→main promote,
  `quality-gates-v2` red), root-caused the ACTUAL wall to the fleet-wide self-hosted-runner capacity crisis already
  tracked in `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (8th corroboration: 2 pure file-I/O tests
  — `test_every_spot_launcher_can_emit_the_preemption_signal`, `test_real_execution_order` — timed out >60s on the
  shared oversubscribed `glue-ip-172-31-5-118-1` runner; deployment-service's own Phase-7 rollout commit `b645aaa4` had
  never been reverted). Applied the same precedented fix (revert `self_hosted_runner_labels` to empty) and shipped to
  `live-defi-rollout` via quickmerge (`deployment-service@ed2691fa93e2`). That part is DONE and verified —
  `quality-gates-v2` is confirmed green on GH-hosted `ubuntu-latest` runners going forward.

  Surfaced a SEPARATE, narrower automation gap while trying to get PR #576 itself to re-gate: `PROMOTE_HEAD` in
  `ldr-to-main-promote-fleet.yml` is computed each tick as `promote/$REPO/${LDR_SHA:0:12}` from the CURRENT
  `live-defi-rollout` tip. Once my fix landed, the correct head for deployment-service became
  `promote/deployment-service/ed2691fa93e2`, but PR #576 was still pinned to the OLD frozen ref
  `promote/deployment-service/679f826c23dc` (pre-dating the fix). The `_INFLIGHT_HEAD != PROMOTE_HEAD` branch is
  supposed to either wait (if v2 still running on the inflight head) or supersede (close the stale PR, open a fresh one
  at the new frozen ref) — but for deployment-service specifically, `process_repo` produced NO output at all across 2
  consecutive ticks (run `30330698700` deployment-service missing from `Promoted (0)/Blocked (1:
  market-tick-data-service only)/Conflicted (0)` tallies; same absence in the following tick). To unblock the actual
  escalation without a force-push (blocked by the `block_destructive_commands.py` orchestrator guardrail, correctly — a
  shared bot-owned ref is not mine to force-push), I closed PR #576 by hand (`gh pr close 576 --comment "..."`,
  referencing this doc) so a subsequent tick's `gh pr create` (which only fires when no existing open PR is found) would
  have a clear path. Two more ticks after the close (`30332303809` at 05:40:30Z, and one prior) STILL show
  deployment-service absent from the Promoted/Blocked/Conflicted tally — no new `promote/deployment-service/ed2691f*`
  branch exists (`gh api repos/IggyIkenna/deployment-service/branches` confirms; only stale historical
  `promote/deployment-service/<sha>` branches from 2026-07-27/28 churn are present, none matching the current LDR tip).
  `sit-gate/fleet-green` + `semver-agent/label-check` statuses ARE posted correctly against
  `ed2691fa93e2a146b3219762c16b5263576ee0cd` each tick (confirmed in both ticks' logs) — so the Tier-A/SIT stage runs
  fine; it is specifically the `process_repo` PR-create/arm stage that appears to silently drop deployment-service.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, ldr-to-main, promote-fleet, automation-gap, self-hosted-runners, deployment-service]
related:
  - /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md
  - /plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
  - /codex/08-workflows/ci-cd-flow.md
created: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: devops-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: "cicd agent, slot-11, escalation agt-7ea8ad (deployment-service ldr_qg_failure, PR #576), 2026-07-28"
resolved_by:
---

## What I fixed (the actual escalation)

- Root cause: fleet-wide self-hosted-runner capacity crisis (see linked doc), NOT a code regression.
- Fix: reverted `self_hosted_runner_labels` to empty in `deployment-service/.github/workflows/quality-gates-v2.yml`,
  shipped via `quickmerge --agent --files '.github/workflows/quality-gates-v2.yml'` —
  `deployment-service@ed2691fa93e2a146b3219762c16b5263576ee0cd`.
- Verified: a fresh `quality-gates-v2` run against that commit (cherry-picked onto the then-open PR #576's head to force
  a re-gate, since the frozen promote ref doesn't auto-rebase) completed **green** on GH-hosted `ubuntu-latest` runners
  (run `30331770894`, all jobs `runner_name: "GitHub Actions ..."`, not `glue-ip-...`).

## What's still open (this doc's scope)

- [ ] [CI] P2. **Retagged from [OPERATOR] 2026-07-28** — this is plain CI-diagnosis monitoring, any AO worker can do it
      the same way any other `gh run list`/`gh pr list` observation todo works, no operator judgment call needed.
      Confirm whether `ldr-to-main-promote-fleet.yml`'s `process_repo` step genuinely no-ops for deployment-service (vs.
      a timing/eventual-consistency artifact that resolves on a later tick with no code change needed) — watch the next
      few scheduled (`*/15`) ticks and confirm a `promote/deployment-service/ed2691f*` PR appears and auto-merge arms.
      If it does NOT self-resolve within a few ticks, the bug is real and needs a fix in
      `unified-trading-pm/.github/workflows/ldr-to-main-promote-fleet.yml`'s `process_repo` function (likely something
      swallowing an error via a `2>/dev/null || true` in the PR-create/list path for this specific repo — worth adding
      non-silenced diagnostic output to the bounded-parallel per-repo log capture, since `2>&1 &` backgrounding + a
      `gh run view --log` fetch may also just be truncating/dropping some per-repo output rather than the step never
      running at all; both are worth ruling in/out before assuming a code bug).
- [ ] [SCRIPT] P3. If confirmed a real bug: harden `process_repo`'s error paths (the multiple `2>/dev/null || true`
      swallows around `gh pr create`/`gh pr list` in the PR-arm section) to at least emit a non-silenced diagnostic line
      per repo so a silent no-op is visible in the run log without needing to diff branch listings by hand, as was
      necessary here.
- Once resolved, `deployment-service` LDR→main promotion should proceed normally on the standing 15-min cadence with no
  further manual intervention.

## Evidence

- Escalation: `agt-7ea8ad` (dashboard).
- Failing run (original wall): https://github.com/IggyIkenna/deployment-service/actions/runs/30330092404
- Fix commit: `deployment-service@ed2691fa93e2a146b3219762c16b5263576ee0cd`
- Green re-verify run (cherry-picked fix on then-PR-#576 head):
  https://github.com/IggyIkenna/deployment-service/actions/runs/30331770894
- Fleet ticks observed post-close with no new PR: `30332185475` (05:34:19Z tally), `30332303809` (05:40:30Z tally) —
  both show deployment-service absent from Promoted/Blocked/Conflicted.
- Closed stale PR: https://github.com/IggyIkenna/deployment-service/pull/576 (closed by this worker, comment references
  this doc).
