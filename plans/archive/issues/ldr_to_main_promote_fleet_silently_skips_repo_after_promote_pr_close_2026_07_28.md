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
status: resolved
nature: issue
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [meta]; content is ldr-to-main-promote-fleet.yml
  # automation bug, squarely ci-tranche (CI/CD pipeline mechanics), not generic cross-workspace content.
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, ldr-to-main, promote-fleet, automation-gap, self-hosted-runners, deployment-service]
related:
  - /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md
  - /plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
  - /codex/08-workflows/ci-cd-flow.md
created: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: cicd
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: "cicd agent, slot-11, escalation agt-7ea8ad (deployment-service ldr_qg_failure, PR #576), 2026-07-28"
resolved_by: "cicd agent, slot-3, 2026-07-31"
---

> **🟢 RESOLVED 2026-07-31** — both open todos closed. Todo 1 self-resolved (confirmed via merged-PR history,
> 2026-07-30). Todo 2 shipped as discretionary hardening (`unified-trading-pm@9ff98b12a`) — the exact silent-drop
> mechanism this doc's narrative describes (`process_repo`'s PR-arm fallthrough dropping a repo from every tally with no
> `_done` call) is fixed. Zero open follow-up todos — this doc is a closed-out record, not a dispatch. The SEPARATE,
> still-ACTIVE fleet-wide `startup_failure` outage discovered while confirming this is tracked in its own doc, not here:
> `/plans/active/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`.

## What I fixed (the actual escalation)

- Root cause: fleet-wide self-hosted-runner capacity crisis (see linked doc), NOT a code regression.
- Fix: reverted `self_hosted_runner_labels` to empty in `deployment-service/.github/workflows/quality-gates-v2.yml`,
  shipped via `quickmerge --agent --files '.github/workflows/quality-gates-v2.yml'` —
  `deployment-service@ed2691fa93e2a146b3219762c16b5263576ee0cd`.
- Verified: a fresh `quality-gates-v2` run against that commit (cherry-picked onto the then-open PR #576's head to force
  a re-gate, since the frozen promote ref doesn't auto-rebase) completed **green** on GH-hosted `ubuntu-latest` runners
  (run `30331770894`, all jobs `runner_name: "GitHub Actions ..."`, not `glue-ip-...`).

## What's still open (this doc's scope)

- [x] ✅ [CI] P2. **Self-resolved — confirmed via merged-PR history, 2026-07-30 (slot-11).** NOT a persisting per-repo
      bug in `process_repo`: `gh pr list --repo IggyIkenna/deployment-service --search promote --state all` shows
      deployment-service promote PRs `#586`–`#603` all `MERGED` cleanly on the standing cadence, spanning
      `2026-07-28T12:31:43Z`–`2026-07-29T16:20:03Z` (10 consecutive successful promotes after the 2 no-op ticks this doc
      originally observed, incl. `#594`/`#595` shortly after the stale-PR-close). The 2-tick no-op was a
      timing/eventual-consistency artifact, not a code defect — no fix needed in `process_repo`.
- [x] ✅ [SCRIPT] P3. **Shipped as discretionary hardening, 2026-07-31 (slot-3).** Its trigger condition ("if confirmed
      a real bug") was never met (see todo 1), but the exact silent-drop mechanism this doc reproduced twice against
      deployment-service was still live in `process_repo`'s PR-arm section: the `gh pr create` fallthrough at the bottom
      of the PR-open block returned `0` WITHOUT ever calling `_done`, so `$RESULT_DIR/$REPO` was never written and the
      repo dropped out of every Promoted/Blocked/Conflicted tally with zero trace — plus the `gh pr create` stderr that
      would explain WHY it failed was discarded via `2>/dev/null`. Fixed both: captured the previously-swallowed stderr
      and now log it on failure, and the fallthrough calls `_done BLOCKED` instead of a bare `return 0`, so the repo
      surfaces in the tally (and next tick's retry) instead of vanishing silently. `unified-trading-pm@9ff98b12a`
      (`scripts/cicd/ldr_to_main_fleet_promote.sh`).
- Resolved: `deployment-service` LDR→main promotion proceeded normally on the standing cadence with no further manual
  intervention, through 2026-07-29T16:20:03Z.
- **Separate, currently-ACTIVE incident found while confirming the above** (NOT the same bug — a distinct, much larger
  outage discovered 2026-07-30): both fleet promote workflows have been returning `startup_failure` on every tick since
  2026-07-29T18:30:03Z, blocking the entire `ldr_main` fleet. Tracked separately, do not conflate:
  `/plans/active/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`.

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

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **2026-07-30 (slot-11)**: confirmed todo 1 self-resolved via merged-PR history (`#586`-`#603`); flipped. Todo 2's
  trigger condition was never met, downgraded to discretionary. Filed a SEPARATE issue doc for a much bigger, currently
  active fleet-wide `startup_failure` outage discovered while confirming this — see the note above the Evidence section.
  Escalated to main via chat.
- **2026-07-31 (slot-3)**: shipped todo 2 as discretionary hardening. Re-read `process_repo` in
  `scripts/cicd/ldr_to_main_fleet_promote.sh` and located the exact silent-drop mechanism this doc's own narrative
  describes: the `gh pr create` fallthrough (PR creation failed AND no existing open PR found) returned `0` without
  calling `_done`, so the repo never gets a `$RESULT_DIR/$REPO` entry and is silently absent from every tick's
  Promoted/Blocked/Conflicted tally — reproducing the exact deployment-service symptom this doc reported. Hardened two
  swallows: captured `gh pr create`'s previously-`2>/dev/null`-discarded stderr and log it on failure, and the
  fallthrough now calls `_done BLOCKED` instead of a bare `return 0`. `bash -n` + `shellcheck` clean (no new findings vs
  pre-existing warnings), full `quality-gates.sh --no-fix` green. Shipped `unified-trading-pm@9ff98b12a`.
