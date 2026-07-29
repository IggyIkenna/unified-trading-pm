---
doc_type: plan
title: PM's own 39 MOVE-classified workflows — bucket (a)/(b) triage + core-pipeline operator sign-off
summary: >-
  Follow-up to the Wave-2 self-hosted-runner migration's "NEW FINDING" — unified-trading-pm's OWN `.github/workflows/`
  had never been run through `scripts/self-hosted-runners/classify-glue-workflows.sh` as a directed audit. Re-running it
  confirmed the 39 MOVE / 19 KEEP split, but a file-by-file re-verification of each MOVE-classified file's ACTUAL
  current `runs-on:` state (the classifier is purely trigger-derived and never checks this) found 38 of the 39 are
  ALREADY fully self-hosted — only `cloud-build-router.yml`'s `record-cloud-build-result` job remains on
  `ubuntu-latest`. Fixed the classifier itself (bucket a, shipped) to report this STATE going forward. The one real
  remaining gap sits inside the operator-named highest-stakes file and is left `[OPERATOR]`-gated per explicit
  instruction, NOT auto-flipped.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, cost, github-actions, wave-2, audit, operator-gated]
related:
  [
    /plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
  ]
created: "2026-07-28"
last_updated: 2026-07-28
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - "slot-1 (tabs/1), /autonomous dispatch fulfilling the P1 REVIEW todo in
    /plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md's 'Fleet-wide re-audit
    results' section (2026-07-28 NEW FINDING) — operator explicitly chose 'human plan' when asked
    agent-orchestrator-vs-human per the plan-destination hard rule, specifically because several of the 39
    MOVE-classified files are core CI/CD pipeline automation with real blast radius (cloud-build-router.yml above all —
    the trading kill-switch / market-hours deploy guard / position-reconciliation-gated deployment orchestrator)."
---

# PM's own 39 MOVE-classified workflows — bucket (a)/(b) triage + core-pipeline operator sign-off

> **Origin.** `/plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`'s 2026-07-28
> "Fleet-wide re-audit results" section found that unified-trading-pm's OWN `.github/workflows/` directory had never
> been run through its own `bash scripts/self-hosted-runners/classify-glue-workflows.sh` classifier as a directed audit
> (that plan's earlier work covered the 24 OTHER repos only). Doing so found **39 workflows classified MOVE** vs **19
> KEEP**. The issue doc explicitly deferred scoping this into its own follow-up plan given the blast radius of several
> MOVE-classified files (`cloud-build-router.yml` most notably), and asked the operator agent-orchestrator-vs-human per
> the plan-destination hard rule. **Operator answer: human plan** — this doc.

## The load-bearing finding (read this before the todos below)

`classify-glue-workflows.sh`'s MOVE/KEEP verdict is **purely trigger-derived** (`on:` shape, heaviness, template
membership, monitor/reusable/hosted-dep exemption lists) — it **never inspects a file's actual current `runs-on:`
value**. That means a workflow already fully migrated to `[self-hosted, glue]` keeps printing `MOVE` on every future
rerun, identical to a file that's still on `ubuntu-latest` and genuinely needs the flip. The issue doc's "39 MOVE...
never actioned" framing took the raw count at face value without this cross-check.

**Re-verification performed today** (`grep -nE '^\s*runs-on:\s*ubuntu-latest\b'` against each of the 39 MOVE-classified
files, excluding comment-only mentions like `# restoring runs-on: ubuntu-latest requires...`):

- **38 of the 39 files are ALREADY fully self-hosted** — no real `ubuntu-latest` line remains in them. (Most carry an
  explicit `# Self-hosted-ONLY: restoring runs-on: ubuntu-latest requires restoring <step>` comment, confirming this was
  a deliberate prior migration, not an accident of never having had a runner label.)
- **Exactly ONE real gap exists in the entire 39-file MOVE set**: `cloud-build-router.yml:1259` — the
  `record-cloud-build-result` job (a `continue-on-error`/best-effort Firestore read+write that tracks whether the
  `unified-trading-library-prod` Cloud Build trigger's last conclusion recovered from a prior `not-configured` failure,
  purely for a recovery-notification bookend; it does not itself trigger a build, deploy, or touch the
  kill-switch/market-hours-guard/position-reconciliation logic elsewhere in that file).
- **Bucket (a) fixed the tool, not a phantom backlog**: `scripts/self-hosted-runners/classify-glue-workflows.sh` now
  prints a `STATE` column (`pending` vs `done`) so this exact false reading cannot recur on a future rerun — see bucket
  (a) todo below, already shipped.
- **Bucket (a) has ZERO `runs-on:` line-flip todos** as a direct consequence — there is no low-risk batch of
  still-hosted files waiting to be flipped; that work was already done in an earlier pass. Manufacturing a no-op edit on
  an already-self-hosted file would not be real work.
- **Bucket (b) has exactly ONE todo**: the `cloud-build-router.yml:1259` gap. Even though the specific job reads as
  low-risk in isolation (no build/deploy/trading logic — see above), it lives inside the file the operator explicitly
  named as the fleet's highest-stakes deployment orchestrator and asked to be reviewed individually, not
  bulk/auto-flipped. This plan respects that boundary at the FILE level, not the job level — no line inside
  `cloud-build-router.yml` is touched by this plan without explicit operator sign-off.

## Full per-file state (39 MOVE-classified files, verified 2026-07-28)

| #   | File                                           | Current state                                                            | Bucket               |
| --- | ---------------------------------------------- | ------------------------------------------------------------------------ | -------------------- |
| 1   | `agent-runner.yml`                             | already self-hosted                                                      | n/a (done)           |
| 2   | `cascade-qg-ordering.yml`                      | already self-hosted                                                      | n/a (done)           |
| 3   | `cassette-drift-check.yml`                     | already self-hosted                                                      | n/a (done)           |
| 4   | `change-freeze-check.yml`                      | already self-hosted                                                      | n/a (done)           |
| 5   | `ci-status-consolidator.yml`                   | already self-hosted                                                      | n/a (done)           |
| 6   | `ci-status-update.yml`                         | already self-hosted                                                      | n/a (done)           |
| 7   | `cloud-build-router-aws.yml`                   | already self-hosted                                                      | n/a (done)           |
| 8   | `cloud-build-router.yml`                       | **1 job still `ubuntu-latest`** (`record-cloud-build-result`, line 1259) | **(b) `[OPERATOR]`** |
| 9   | `cold-storage-cleanup.yml`                     | already self-hosted                                                      | n/a (done)           |
| 10  | `conflict-resolution-agent.yml`                | already self-hosted                                                      | n/a (done)           |
| 11  | `deterministic-promotion-conflict-resolve.yml` | already self-hosted                                                      | n/a (done)           |
| 12  | `digest-drift-sweep.yml`                       | already self-hosted                                                      | n/a (done)           |
| 13  | `escalate-to-orchestrator.yml`                 | already self-hosted                                                      | n/a (done)           |
| 14  | `fix-approval-timeout.yml`                     | already self-hosted                                                      | n/a (done)           |
| 15  | `freeze-deferred-build-replay.yml`             | already self-hosted                                                      | n/a (done)           |
| 16  | `hotfix-mode.yml`                              | already self-hosted                                                      | n/a (done)           |
| 17  | `ldr-docs-gate.yml`                            | already self-hosted                                                      | n/a (done)           |
| 18  | `ldr-to-main-promote-fleet.yml`                | already self-hosted                                                      | n/a (done)           |
| 19  | `ldr-to-main-promote.yml`                      | already self-hosted                                                      | n/a (done)           |
| 20  | `ldr-to-staging-promote.yml`                   | already self-hosted                                                      | n/a (done)           |
| 21  | `overnight-agent-orchestrator.yml`             | already self-hosted                                                      | n/a (done)           |
| 22  | `plan-notification.yml`                        | already self-hosted                                                      | n/a (done)           |
| 23  | `readiness-verifier.yml`                       | already self-hosted                                                      | n/a (done)           |
| 24  | `reconcile-release-tags.yml`                   | already self-hosted                                                      | n/a (done)           |
| 25  | `reconcile-staging-versions.yml`               | already self-hosted                                                      | n/a (done)           |
| 26  | `removed-symbols-workspace-sweep.yml`          | already self-hosted                                                      | n/a (done)           |
| 27  | `rules-alignment-agent.yml`                    | already self-hosted                                                      | n/a (done)           |
| 28  | `ruleset-drift-alert.yml`                      | already self-hosted                                                      | n/a (done)           |
| 29  | `secret-health-check.yml`                      | already self-hosted                                                      | n/a (done)           |
| 30  | `sit-debounce-trigger.yml`                     | already self-hosted                                                      | n/a (done)           |
| 31  | `sit-gate.yml`                                 | already self-hosted                                                      | n/a (done)           |
| 32  | `sit-unlock.yml`                               | already self-hosted                                                      | n/a (done)           |
| 33  | `staging-conflict-ldr-main-fallback.yml`       | already self-hosted                                                      | n/a (done)           |
| 34  | `staging-to-main.yml`                          | already self-hosted                                                      | n/a (done)           |
| 35  | `supersede-stale-dep-update-prs.yml`           | already self-hosted                                                      | n/a (done)           |
| 36  | `update-repo-version.yml`                      | already self-hosted                                                      | n/a (done)           |
| 37  | `version-coherence-check.yml`                  | already self-hosted                                                      | n/a (done)           |
| 38  | `version-registry-update.yml`                  | already self-hosted                                                      | n/a (done)           |
| 39  | `workspace-quickmerge-validation.yml`          | already self-hosted                                                      | n/a (done)           |

**Why several of these would have been bucket (b) candidates anyway** (had they still needed the flip): the
`cloud-build-router*.yml` pair (deployment orchestrator), `sit-gate.yml`/`sit-debounce-trigger.yml`/`sit-unlock.yml`
(SIT gating), `ldr-to-main-promote*.yml`/`ldr-to-staging-promote.yml`/`staging-to-main.yml`/
`staging-conflict-ldr-main-fallback.yml` (promotion machinery — the last one auto-merges/closes cross-repo PRs via
`gh pr merge --auto`/`gh pr close`), `conflict-resolution-agent.yml`/`deterministic-promotion-conflict-resolve.yml`
(shared-branch conflict resolution), `hotfix-mode.yml` (hotfix mode), `version-registry-update.yml`/
`update-repo-version.yml`/`reconcile-staging-versions.yml` (release/version machinery feeding the promotion set),
`cascade-qg-ordering.yml` (fleet-wide breaking-change QG cascade), `change-freeze-check.yml`/
`freeze-deferred-build-replay.yml` (change-freeze gate + deferred prod-build replay, both on `cloud-build-router`'s
critical path) — all of these are ALREADY self-hosted, so no action is needed, but the record above exists so a future
re-audit doesn't have to re-derive this risk read from scratch.

## Bucket (a) — low-risk, executed today

- [x] [INFRA] P2. ✅ **DONE 2026-07-29 — fixed `classify-glue-workflows.sh`'s state-blindness.** Added a `STATE` column
      (`pending`/`done`) to its output by grep-checking each MOVE/MOVE-C file's actual current
      `runs-on:\s*ubuntu-latest` line (non-comment), and a `[N pending / M already self-hosted]` breakdown in the
      summary line, so a future rerun can never again read a stale trigger-derived MOVE verdict as "still needs
      migrating" without a manual per-file re-grep. Zero CI/CD blast radius — local advisory dev-tool script, not a
      pipeline workflow. **Verified**: `bash scripts/self-hosted-runners/classify-glue-workflows.sh` prints
      `MOVE (→ PM-local direct flip): 39 [1 pending / 38 already self-hosted]   KEEP (→ GitHub-hosted): 20` and
      `cloud-build-router.yml` is the only row showing `pending`. Shipped `unified-trading-pm@<this-commit>`. **A second
      exemption found in the same pass**: `stale-build-watcher.yml` (new file, landed on the shared branch after this
      plan's original table above) is the same failure-independence-monitor shape as `cloud-build-failure-watcher.yml` —
      it measures whether a Cloud Build actually happened, independent of the build pipeline; a self-hosted copy would
      go dark exactly when the glue pool it depends on is the thing failing. Added to `KEEP_MONITORS` (identical
      reasoning already applied to `glue-pool-starvation-monitor.yml` the day before) — this is why the total moved
      40→39 MOVE / 19→20 KEEP between this plan's authoring and its ship, not a miscount.

## Bucket (b) — core-pipeline, `[OPERATOR]`-gated, NOT executed by any agent without explicit sign-off

- [x] ✅ [OPERATOR] P2. **Operator-approved 2026-07-29 (interactive decision session).** `cloud-build-router.yml:1259` —
      flipped the `record-cloud-build-result` job's `runs-on: ubuntu-latest` → `runs-on: [self-hosted, glue]` (see
      Progress Log for shipping evidence). Reason gated: this file is the fleet's actual production deployment
      orchestrator (tier-ordered T0→T1→T2→services prod deploy, a trading kill-switch, a market-hours/trading-active
      deployment guard, a position-reconciliation gate) — the operator explicitly asked that no MOVE-classified file
      inside this set be bulk/auto-flipped without individual review, given the blast radius of a self-hosted-runner
      outage or misbehavior silently breaking the fleet's ability to ship code (or worse, a subtly-wrong trading-safety
      gate). The specific job itself is low-risk on its own merits (a 3-minute, `continue-on-error`, fail-open Firestore
      read+write with no build/deploy/trading logic — see "The load-bearing finding" above) — this gate is about the
      FILE's blast radius and the operator's explicit ask, not a judgment that this one job is actually risky in
      isolation. **Approve-executes**: once the operator confirms, any worker/session can make this exact one-line
      change, run `bash scripts/quality-gates.sh --no-fix`, and ship via
      `quickmerge --agent --files 'unified-trading-pm/.github/workflows/cloud-build-router.yml'` — no further
      investigation needed, the analysis above already stands.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / self-hosted-runner rollout mechanism this plan extends.
- `/plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md` — origin issue doc (Wave-2
  re-audit); its P1 REVIEW todo is fulfilled by this plan.
- `/plans/active/github_actions_operator_gated_followups_2026_07_17.md` — sibling PM self-hosted-runner cost-followup
  plan (same epic, same `nature`/`asset_group` convention mirrored here).

## Progress Log

- **2026-07-28**: Plan authored (human/`assigned_vm: NA` per operator's explicit choice when asked
  agent-orchestrator-vs-human). Re-ran `classify-glue-workflows.sh` (confirmed 39 MOVE / 19 KEEP, unchanged from the
  issue doc's number). Discovered the state-blindness of the classifier via file-by-file re-verification — 38/39
  MOVE-classified files were ALREADY self-hosted; the ONLY real gap is `cloud-build-router.yml:1259`. Fixed the
  classifier to report STATE going forward (bucket a, todo 1). Bucket (b)'s single todo left `[OPERATOR]`-gated per the
  operator's explicit instruction not to touch `cloud-build-router.yml` (or the other named core-pipeline files) without
  individual sign-off.
- **2026-07-29**: Closing pass before shipping — the classifier's live output had drifted from this plan's authored
  numbers (40 MOVE / 19 KEEP / 2 pending, not 39/19/1) because a NEW workflow, `stale-build-watcher.yml`, landed on the
  shared branch mid-session from an unrelated concurrent fix
  (`cloud_build_router_concurrency_drops_dispatch_2026_07_27.md`). Read it: it's the same failure-independence-monitor
  shape as the other 7 `KEEP_MONITORS` entries (measures whether a Cloud Build actually happened, independent of the
  pipeline that would run it) — added it to `KEEP_MONITORS` rather than batch-flipping it, for the identical reason
  `glue-pool-starvation-monitor.yml` was added the day before. Classifier now prints the exact done-when string. Bucket
  (a) todo 1 flipped to done; shipping both files now.
- **2026-07-29 (interactive decision session)**: Operator approved bucket (b)'s single gated flip. Shipped
  `.github/workflows/cloud-build-router.yml:1259` `runs-on: ubuntu-latest` → `[self-hosted, glue]` directly (the
  `.github/**` carve-out — quickmerge's re-gate hit the pre-existing, already-tracked
  `test_capability_param_schema.py`/`test_capability_verdict_matrix.py` failures documented in
  `fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md`, confirmed stable across 2 identical runs, unrelated
  to this 1-line YAML change). All 39 MOVE-classified files are now self-hosted.
