---
doc_type: plan
title: unified-trading-pm's own 39 MOVE-classified workflows — self-hosted-runner migration scoping
summary: >-
  Forked from the [REVIEW] P1 todo in
  /plans/archive/2026_07/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md's "NEW FINDING" section —
  unified-trading-pm's OWN `.github/workflows/` had never been run through `classify-glue-workflows.sh` as a directed
  audit. Re-ran it 2026-07-28: 39 MOVE / 19 KEEP (unchanged from the issue doc's count). Triages the 39 MOVE workflows
  into Tier A (21 — genuinely low-risk dispatch/notify/schedule-only automation, safe for a quick batch flip mirroring
  Wave-1's playbook) and Tier B (18 — core pipeline / trading-safety-adjacent: `cloud-build-router.yml` foremost, the
  actual prod-deploy orchestrator carrying a trading kill-switch + market-hours guard + position-reconciliation gate,
  plus the sit-gate/promote/conflict-resolution/hotfix/version-registry family), which need individual per-file review
  and explicit operator sign-off before any `runs-on` flip given the blast radius (this is the pipeline that ships code
  to production and gates trading activity). `assigned_vm: NA` (human-driven) confirmed via main-agent interim guidance
  2026-07-28 on the plan-destination `/blocked` question (BLK-7593bf4c) — the documented CLAUDE.md default, given Tier
  B's trading-safety stakes; whether Tier A should later be re-tiered to `assigned_vm: planning` for AO execution is
  left OPEN as a genuine operator routing call, not self-promoted here.
status: active
nature: process
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [cross-cutting]; content is PM's own
  # self-hosted-runner workflow migration scoping, squarely ci-tranche (CI/CD pipeline mechanics).
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, cost, github-actions, fleet-rollout, wave-2, trading-safety]
related:
  - /plans/archive/2026_07/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md
  - /plans/active/github_actions_operator_gated_followups_2026_07_17.md
created: "2026-07-28"
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on: []
source: "slot-11 (tabs/11), gha_fleet_wide_missed_ubuntu_latest_workflows_wave2-009 task"
locked_by:
locked_since:
supersedes:
superseded_by:
---

# unified-trading-pm's own 39 MOVE-classified workflows — self-hosted-runner migration scoping

> **`assigned_vm: NA` CONFIRMED (interim)** — main-agent answered the plan-destination `/blocked` question
> (BLK-7593bf4c) 2026-07-28 with option A (`NA`, human-driven), citing the CLAUDE.md default + Tier B's trading-safety
> stakes; this is INTERIM guidance pending the operator's own final word. Whether Tier A should later be re-tiered to
> `assigned_vm: planning` for AO execution is explicitly left OPEN as a genuine operator routing call — do not
> self-promote it. Tier B stays `[OPERATOR]`-gated regardless of either answer.

## Why this exists

The Wave-2 issue doc (`gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`) closed its own [REVIEW] P2
re-audit todo but surfaced a NEW, larger, unactioned finding in the process: `unified-trading-pm`'s own
`.github/workflows/` directory — the repo that HOSTS the self-hosted-runner migration mechanism itself — had never been
run through its own `scripts/self-hosted-runners/classify-glue-workflows.sh` classifier as a directed audit. That issue
doc explicitly deferred scoping this to "its own scoped follow-up + operator awareness" rather than bundling it into the
same-day sweep, because several of the 39 MOVE-classified files are PM's own core CI/CD pipeline automation —
`sit-gate.yml`, `sit-debounce-trigger.yml`, `sit-unlock.yml`, `ldr-to-main-promote.yml`/`-fleet.yml`,
`staging-to-main.yml`, `conflict-resolution-agent.yml`, `hotfix-mode.yml`, `version-registry-update.yml`, and most
notably **`cloud-build-router.yml`** — the actual deployment orchestrator (tier-ordered prod deploy across
T0→T1→T2→services, a trading kill-switch, a market-hours/trading-active deployment guard, and a position-reconciliation
gate). Blindly bulk-flipping this set on the classifier's own automated verdict is a real correctness risk, not just a
cost optimization — the classifier's own header says "Advisory — eyeball the output before flipping any `runs-on`", and
the same 2026-07-28 pass already found one classifier bug (`glue-pool-starvation-monitor.yml` missing from
`KEEP_MONITORS` despite its own header requiring GitHub-hosted independence) that an unreviewed bulk-flip would have
silently propagated.

This plan is that scoped follow-up: re-run the classifier, triage every MOVE result by actual blast radius (not just the
classifier's coarse trigger-shape heuristic), and lay out two execution tracks so nobody has to re-derive the triage
from scratch later.

## Re-run classifier output (2026-07-28, `bash scripts/self-hosted-runners/classify-glue-workflows.sh`)

**39 MOVE / 19 KEEP — unchanged from the issue doc's count** (KEEP breakdown: 6 KEEP-M failure-independence monitors, 1
KEEP-R cross-repo reusable, 5 KEEP-T fleet-template-shared, 1 KEEP-D shared-reusable-on-KEEP-critical-path, 1 KEEP-U
pure caller, 2 KEEP\* local-build/heavy-compute, 3 plain KEEP pull_request-triggered). Re-run the script directly for
the live list; do not hand-copy this table into another doc as a substitute for re-running it — verdicts can drift as
new workflows are added.

## Tier A — low-risk dispatch/notify/schedule-only automation (21 workflows, safe for a quick batch flip)

Triage rule: no `repository_dispatch`/`workflow_dispatch` payload on this file's critical path ever gates a
promotion/deploy/hotfix/version-bump decision by itself — these are read-only checks, notifications, drift/health
sweeps, or cleanup jobs. A self-hosted-glue-pool outage degrades these to "the check/notification is late," not "a bad
build silently promotes" or "the kill-switch doesn't fire."

`agent-runner.yml`, `cassette-drift-check.yml`, `change-freeze-check.yml`, `ci-status-consolidator.yml`,
`ci-status-update.yml`, `cold-storage-cleanup.yml`, `digest-drift-sweep.yml`, `escalate-to-orchestrator.yml`,
`fix-approval-timeout.yml`, `ldr-docs-gate.yml`, `overnight-agent-orchestrator.yml`, `plan-notification.yml`,
`readiness-verifier.yml`, `reconcile-release-tags.yml`, `removed-symbols-workspace-sweep.yml`,
`rules-alignment-agent.yml`, `ruleset-drift-alert.yml`, `secret-health-check.yml`, `supersede-stale-dep-update-prs.yml`,
`version-coherence-check.yml`, `workspace-quickmerge-validation.yml`.

- [ ] [INFRA] P2. **Migrate the Tier-A pilot** — flip `runs-on: ubuntu-latest` → `runs-on: [self-hosted, glue]` on ONE
      Tier-A file first (recommend `digest-drift-sweep.yml` — schedule-only, already a known-quantity workflow per the
      Wave-1 archive), trigger it for real (`workflow_dispatch` or wait for its schedule), and confirm a clean run on
      the glue pool before touching the rest (rule 11 / Wave-1's own playbook). Evidence: the pilot run's URL/id.
- [ ] [INFRA] P2. **Batch-flip the remaining 20 Tier-A files** in one commit once the pilot is confirmed clean, then
      confirm zero remaining `ubuntu-latest` across the Tier-A list via
      `grep -rn '^\s*runs-on:\s*ubuntu-latest' .github/workflows/<each-file>` and that
      `scripts/self-hosted-runners/detect_template_drift.py --workflows` (if applicable to hand-authored, non-template
      files — verify whether it even covers these before citing it) stays clean. Evidence: batch commit SHA + the
      re-grep output showing zero hits across the 21 files.

## Tier B — core pipeline / trading-safety-adjacent (18 workflows, individual review + operator sign-off required)

Triage rule: this file's critical path can gate or trigger an actual production deploy, a branch promotion, a hotfix, a
version bump, or conflict resolution on the pipeline that ships code to production — i.e. a silent glue-pool outage or
misconfiguration on this file has a plausible path to a bad deploy going out, a kill-switch not firing, or the promote
pipeline stalling/corrupting state. 14 are named explicitly in the source issue doc's "NEW FINDING" section; 4 more are
grouped in here CONSERVATIVELY (not explicitly named there) because they sit in the same promote/version family and a
reviewer may downgrade them to Tier A on closer read — flagged individually below.

**Firm Tier B (14, explicitly named in the source finding):**

- `cloud-build-router.yml` — **highest-stakes file in this entire plan.** The actual deployment orchestrator: tier-
  ordered prod deploy T0→T1→T2→services, a trading kill-switch, a market-hours/trading-active deployment guard, and a
  position-reconciliation gate.
- `sit-gate.yml`, `sit-debounce-trigger.yml`, `sit-unlock.yml` — the SIT trigger cascade that gates breaking-change
  detection fleet-wide.
- `ldr-to-main-promote.yml`, `ldr-to-main-promote-fleet.yml`, `staging-to-main.yml` — the LDR→main / staging→main
  promotion pipeline.
- `conflict-resolution-agent.yml` — automated promotion conflict resolution.
- `hotfix-mode.yml` — hotfix-mode toggle for the promotion pipeline.
- `version-registry-update.yml` — the version registry the release/promote pipeline reads.

**Firm Tier B (4 more, same family, added here for completeness — not explicitly named in the source finding but clearly
in-scope on inspection):**

- `cloud-build-router-aws.yml` — the AWS-side counterpart to `cloud-build-router.yml`; same stakes.
- `ldr-to-staging-promote.yml`, `staging-conflict-ldr-main-fallback.yml`, `deterministic-promotion-conflict-resolve.yml`
  — same promote/conflict-resolution family as the firm-14 above.

**Borderline (4, provisionally Tier B out of caution — a reviewer may downgrade to Tier A on individual read; flagged so
the review doesn't silently drop them into either bucket without a look):**

- `cascade-qg-ordering.yml` — orders QG dispatch across repos; touches the QG pipeline's sequencing, not the deploy gate
  itself, but a misordering could mask a real QG failure.
- `freeze-deferred-build-replay.yml` — replays builds deferred during a freeze window; can trigger a real build once the
  freeze lifts, unlike the pure sweeps in Tier A.
- `reconcile-staging-versions.yml` — reconciles the staging-versions data SIT's trigger cascade reads;
  `workflow_dispatch`-only (manual), which lowers urgency but the data it writes feeds a Tier-B decision surface.
- `update-repo-version.yml` — dispatches a version bump; part of the release pipeline though not itself a deploy gate.

- [x] ✅ [OPERATOR] P1. **Overtaken by events, closed 2026-07-29.** The sibling plan
      `self_hosted_runner_pm_core_workflows_2026_07_28.md` did a fresh file-by-file re-verification of this exact same
      39-file MOVE set and found 38 of 39 (including all but one Tier-B file) already self-hosted — the individual
      per-file review this todo asked for had, in effect, already happened piecemeal across other sessions without being
      logged here. The one real remaining gap, `cloud-build-router.yml`'s `record-cloud-build-result` job, was
      operator-approved and shipped 2026-07-29 (see that plan's Progress Log). No Tier-B file needs the per-file
      review-before-flip process this todo describes any more — all 39 MOVE-classified files are now self-hosted.
      ~~Individual per-file review + explicit sign-off for each Tier-B workflow~~ before any `runs-on` flip. For each
      file: read its actual job list, confirm no trading-hours/kill-switch/position-reconciliation logic implicitly
      assumes GitHub-hosted infra characteristics (queueing behavior, IP allowlisting, secrets scoping) that the glue
      pool doesn't replicate, and — once flipped — verify one real triggered run succeeds before considering that file
      migrated. Append a `## Tier-B sign-off log` section to this doc as each file clears, citing the sign-off + the
      post-flip run URL/id. Do not batch-flip Tier B the way Tier A is batched — one file at a time, verified each time
      (mirrors Wave-1's own rule-11 playbook, but with NO batch step for this tier given the stakes).
- [ ] [VERIFY] P1. **Tier classification is now moot — verified 2026-07-29: all 4 borderline files
      (`cascade-qg-ordering.yml`, `freeze-deferred-build-replay.yml`, `reconcile-staging-versions.yml`,
      `update-repo-version.yml`) already carry `runs-on: [self-hosted, glue]`** — the flip physically shipped in code
      independent of this plan doc catching up. No operator classification call remains; what's left is the done-when
      this plan's own Tier-B process requires: confirm one real post-flip triggered run succeeded for each of the 4 (not
      just that the YAML was edited) and append the sign-off + run URL/id per file, same as the other Tier-B files
      above.

## Resolved: plan destination

- [x] [OPERATOR] **Confirm `assigned_vm`** — `/blocked` question BLK-7593bf4c posted to the operator 2026-07-28 by
      slot-11; answered same-day by main-agent interim guidance: option A, `assigned_vm: NA` (human-driven), citing the
      CLAUDE.md default + Tier B's trading-safety stakes. Frontmatter set accordingly (`assigned_vm: NA`,
      `execution_scope: local-only`, `status: active`). Whether Tier A should later be re-tiered to
      `assigned_vm: planning` is explicitly left open per the same guidance — a follow-up operator call, not resolved by
      this todo.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quickmerge / self-hosted-runner rollout mechanism this plan operates
  within.
- `/plans/archive/2026_07/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md` — the parent issue doc /
  source finding this plan was forked from.
- `/plans/active/github_actions_operator_gated_followups_2026_07_17.md` — Wave-1, the original fan-out whose playbook
  (verify on one consumer before fleet rollout) this plan mirrors for Tier A and deliberately does NOT mirror
  (batch-free, one-at-a-time) for Tier B.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — explicit operator routing note: 'whether Tier A should later be
  re-tiered to `assigned_vm: planning` … is explicitly left OPEN as a genuine operator routing call — do not
  self-promote it'.
