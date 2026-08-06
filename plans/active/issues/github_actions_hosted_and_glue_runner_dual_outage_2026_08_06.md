---
doc_type: issue
title:
  "PM main quality-gates-v2 red RCA (agt-80c470): 748-commit LDR->main promotion stall — TWO independent causes,
  one fixed (glue runner revert), one operator-only (GH Actions hosted-runner-acquisition wall, recurrence)"
summary: >-
  Dispatched as cicd escalation agt-80c470 (wall_type=main_ci_red) for unified-trading-pm's `main` quality-gates-v2
  being RED. Root cause was NOT a code regression — the three failing checks on `main` (agent-rules-size-cap,
  codex-doc-freshness, finalize-plan-coverage) were already fixed on `live-defi-rollout` HEAD (verified locally: all
  three pass against LDR@10de6354d). `main` was simply 748 commits behind LDR because `ldr-to-main-promote.yml`
  (the workflow that drains LDR->main for PM's `promotion_model: ldr_main`) could not run. Found TWO independent,
  stacked failures:

  **(1) FIXED — self-hosted `glue` JIT-ephemeral runner pool is structurally broken on the runner host
  (ip-172-31-5-118)**: `github-glue-token-refresh*.service` fails `203/EXEC` (`/opt/github-glue-runners` and
  `/opt/github-glue-runners-<repo>` do not exist on disk), and `systemctl list-unit-files 'github-glue-runner@*'`
  returns ZERO template units registered — there is no JIT-runner launcher installed at all, only the token-refresh
  timers/services and cgroup slices survive. This is NOT the account-level billing wall (see #2) — it reproduces the
  distinct symptom `"The job was not acquired by Runner of type self-hosted even after multiple attempts"` with a
  real queued job entry (not `startup_failure`/`jobs:[]`). Confirmed via direct host inspection (`systemctl status
  github-glue-token-refresh.service`, `ls /opt/github-glue-runners*` -> not found). I do not have sudo in my slot
  session (`sudo: "no new privileges" flag is set`) so I cannot redeploy the pool per
  `scripts/self-hosted-runners/README.md`. **Mitigated**: reverted `ldr-to-main-promote.yml`'s `runs-on` from
  `[self-hosted, glue]` to `ubuntu-latest` (unified-trading-pm@ce7073ba3, pushed direct to LDR per the
  `scripts/**`/`.github/**`-unblock-the-pipeline carve-out) so PM's own promotion no longer depends on the broken
  pool. This is a point fix for ONE workflow — `ldr-to-main-promote-fleet.yml` (drains ~30 other `ldr_main` repos)
  and every other workflow the 2026-07-17 "batch 3: 26 movers to self-hosted glue pool" migration touched are
  STILL on `[self-hosted, glue]` and will hit the same wall the moment the current billing wall (#2) clears.

  **(2) OPERATOR-ONLY, STILL ACTIVE — GitHub Actions hosted-runner acquisition is ALSO currently failing**, a
  recurrence of the documented pattern in `plans/archive/issues/github_actions_billing_wall_recurrence_2026_07_29.md`
  and `plans/archive/issues/github_actions_billing_wall_2026_06_11.md`. Evidence: my own re-dispatched
  `ldr-to-main-promote.yml` run (31119076413, now correctly requesting `ubuntu-latest` per fix #1 above) sat
  `queued`/`pending` for 5+ min with `runner_id: 0`; independently, `promote-fleet-startup-failure-monitor` run
  31117734179 failed with annotation `"The job was not acquired by Runner of type hosted even after multiple
  attempts"` — i.e. even plain GitHub-hosted runners are not being acquired right now. Every `schedule:`/
  `workflow_dispatch`-triggered run on this repo since ~15:49:49Z is stuck `queued`/`pending`
  (`sit-gate-stuck-detector`, `version-coherence-check`, `ldr-to-main-promote-fleet`, `reconcile-release-tags`,
  `ci-status-consolidator` all confirmed queued at time of filing) while push/PR-triggered runs still work — the
  exact schedule/dispatch-only signature the archived precedent docs record. Both prior recurrences self-resolved
  within hours with NO code change, purely an account-level payment/spending-limit condition only the account owner
  can see/clear (`github.com/settings/billing`). No code fix exists for this from a repo-scoped worker/session.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, ldr-to-main, promote, github-actions, self-hosted-runner, billing-wall, startup-failure, P0]
related:
  [
    /plans/active/issues/main_ci_red_promotion_blocked_by_plan_hygiene_backlog_2026_08_06.md,
    /plans/archive/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md,
    /plans/archive/issues/github_actions_billing_wall_recurrence_2026_07_29.md,
    /plans/archive/issues/github_actions_billing_wall_2026_06_11.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/devops-ci-walls.md,
    scripts/self-hosted-runners/README.md,
  ]
created: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: cicd
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    .github/workflows/ldr-to-main-promote.yml,
    .github/workflows/ldr-to-main-promote-fleet.yml,
    scripts/self-hosted-runners/README.md,
    /plans/archive/issues/github_actions_billing_wall_recurrence_2026_07_29.md,
  ]
source: "cicd agent, slot-5, escalation agt-80c470 (wall_type=main_ci_red), 2026-08-06"
resolved_by:
---

# unified-trading-pm main quality-gates-v2 red — 748-commit promotion stall, dual runner outage

## What I found

> **Note (added after cross-checking): this is NOT the sole blocker.** A prior worker on this same escalation
> (slot 2) already found the PRIMARY blocker — the LDR→main promote PR is separately failing its own
> `quality-gates-v2` on a plan-hygiene backlog (112 archive candidates / 77 AG-closeout orphans / NA corpus over
> baseline) on LDR content, tracked in
> `/plans/active/issues/main_ci_red_promotion_blocked_by_plan_hygiene_backlog_2026_08_06.md` with an operator
> decision pending (`/blocked BLK-46fa5703`, unanswered as of this filing). This doc's findings are a SEPARATE,
> compounding cause discovered while re-verifying that escalation — fixing this doc's issues alone will NOT unblock
> promotion; the plan-hygiene backlog still has to clear.

`main`'s `quality-gates-v2` was red because `main` is (was, at filing) 748 commits behind `live-defi-rollout` — not a
code regression. The 3 checks failing on `main`'s latest run (agent-rules-size-cap: `cursor-configs/CLAUDE.md` was
41,008 B vs the 40,960 B cap; codex-doc-freshness; finalize-plan-coverage) all pass cleanly when run against LDR HEAD
(verified locally with `check_agent_rules_size_cap.py` / `check_finalize_plan_coverage.py` /
`check_codex_doc_freshness.py`). The blocker is purely that `ldr-to-main-promote.yml` — the only path LDR content
reaches `main` for PM's `promotion_model: ldr_main` — has not been able to start a job.

Two independent, stacked causes, detailed in the summary above:

1. **Self-hosted `glue` pool structurally absent** on the runner host (`ip-172-31-5-118`): token-refresh services
   `203/EXEC` because `/opt/github-glue-runners*` doesn't exist; zero `github-glue-runner@` template units
   registered. This is a genuine deploy-state regression vs `scripts/self-hosted-runners/README.md`'s documented
   install, not a transient blip.
2. **GitHub Actions hosted-runner acquisition also currently failing**, account-wide signature matching two prior
   documented recurrences (2026-06-11, 2026-07-29) — self-resolves within hours, operator-only fix
   (`github.com/settings/billing`).

## Why it matters

- PM's own LDR->main promotion was silently stuck for 748 commits before this filing — any `assigned_vm: planning`
  content or `docs(plans):` carve-out push landing on LDR has had no path to `main` for an extended period.
- Cause #1 is NOT PM-specific — `ldr-to-main-promote-fleet.yml` drains ~30 other `promotion_model: ldr_main` repos
  and is still pinned to `[self-hosted, glue]`; every one of those repos' `main` branches is equally exposed the
  moment cause #2 clears (hosted runners come back, but the glue-only workflows will still queue forever).
- Cause #2 blocks not just promotion but several other scheduled workflows on this repo (`ci-status-consolidator`,
  `reconcile-release-tags`, `sit-gate-stuck-detector`, `version-coherence-check` all observed stuck `queued` at
  filing time) — broader than just the promote pipeline.

## What I fixed (this session, agt-80c470)

- [x] ✅ **DONE 2026-08-06** — [CI] P0. Reverted `ldr-to-main-promote.yml`'s `runs-on: [self-hosted, glue]` to
      `runs-on: ubuntu-latest` so PM's own promotion no longer depends on the broken glue pool. Pushed direct to
      `live-defi-rollout` — unified-trading-pm@ce7073ba3. Verified the change took effect (re-dispatched run
      31119076413's job correctly requests `labels: ["ubuntu-latest"]` per the GH API). Could not verify an
      end-to-end successful promote run at filing time because cause #2 (hosted-runner acquisition wall) was ALSO
      active during this session — the re-dispatched run is queued, not yet completed.

## Recommended next steps (needs operator — [OPERATOR])

- [ ] [OPERATOR] P0. Check `github.com/settings/billing` for a failed payment method or exhausted Actions spending
      limit (cause #2) — same recipe as the two prior recurrences. Expect self-clear within hours once resolved; no
      code action needed for this half.
- [ ] [OPERATOR] P1. Once on the runner host (`ip-172-31-5-118`) with sudo: either redeploy the `glue` pool per
      `scripts/self-hosted-runners/README.md` (`setup-glue-runners.sh install` after fixing whatever removed
      `/opt/github-glue-runners*` and the token-refresh script — first find out WHY the payload is missing while the
      systemd units/timers survive, this looks like a partial teardown not a fresh-never-installed state given the
      2026-07-17 migration commit and the many per-repo slices/timers still registered), or make a deliberate
      decision to walk the CI-cost-reduction migration back to GitHub-hosted runners fleet-wide if the self-hosted
      pool is not worth maintaining.
- [ ] [CI] P1. Once #OPERATOR above lands either way, flip `ldr-to-main-promote.yml`'s `runs-on` back to
      `[self-hosted, glue]` (if the pool is repaired) or apply the same `ubuntu-latest` revert to
      `ldr-to-main-promote-fleet.yml` and every other still-`[self-hosted, glue]` workflow from the 2026-07-17
      "batch 3" migration (if the pool is being retired) — do not leave the fleet in the current mixed, broken state.
- [ ] [CI] P2. Confirm PM's `main` actually catches up to `live-defi-rollout` (compare
      `gh api repos/IggyIkenna/unified-trading-pm/compare/main...live-defi-rollout` — expect `ahead_by: 0`) once both
      causes clear, and that `quality-gates-v2` on `main` goes green.
