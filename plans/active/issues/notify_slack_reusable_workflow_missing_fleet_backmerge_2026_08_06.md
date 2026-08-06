---
doc_type: issue
title: >-
  notify-slack.yml reusable workflow never rolled out to 4 fleet repos (instruments-service, execution-service,
  market-data-processing-service, e2e-testing) — their main-backmerge-to-ldr workflows are INVALID (0s/0job fails) since
  the 08-04 todo-3 defense-in-depth rollout
summary: >-
  The 08-04 `a9743a79` fleet rollout of the main_backmerge_to_ldr_silent_failure_2026_08_02 todo-3 defense-in-depth
  added a `notify-failure` job to `main-backmerge-to-ldr.yml` that references `./.github/workflows/notify-slack.yml` as
  a reusable workflow (`uses: ./.github/workflows/notify-slack.yml`) — but `notify-slack.yml` was never copied into 4
  repos (instruments-service, execution-service, market-data-processing-service, e2e-testing). A `pull_request`/`push`
  workflow that references a reusable workflow absent from the repo is INVALID at parse time: GitHub reports "This run
  likely failed because of a workflow file issue", runs 0 jobs, and completes in 0s. Those 4 repos' backmerge bridge
  (main → live-defi-rollout) has been dead since the first main push after the rollout. The 08-02 doc's todo-3 "24 repos
  fleet-wide (rollout verified: trap=3, notify-failure=3, outputs=1 in every copy; all ahead=0)" claim verified the
  backmerge file's own additions but NOT the notify-slack.yml dependency it newly introduced — that dependency is
  missing in exactly the repos whose last full template rollout predates notify-slack.yml's addition to the template
  dir. Found 2026-08-06 while resolving ldr_qg_failure escalation agt-9e4351 (instruments-service promote PR #1082
  CONFLICTING because the dead backmerge let main↔LDR drift). instruments-service fixed in-session (@38821603). The
  other 3 remain broken; fix is a fleet rollout of the notify-slack.yml template (it IS present in
  `scripts/workflow-templates/notify-slack.yml`, blob 56354f32, byte-identical to the fleet copy).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [instruments-service, execution-service, market-data-processing-service, e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, backmerge, notify-slack, reusable-workflow, rollout-gap, live-defi-rollout, drift]
related:
  [
    /plans/active/issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md,
    /plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md,
    /plans/active/issues/client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md,
  ]
created: 2026-08-06
author: slot-11
parent_epic: infrastructure_master
priority: P1
source:
  cicd escalation agt-9e4351 (slot 11, 2026-08-06) — root-causing instruments-service ldr_qg_failure (promote PR #1082
  CONFLICTING after the dead backmerge let main↔LDR drift). Found the notify-slack.yml rollout gap while diagnosing the
  main-backmerge-to-ldr 0s/0job parse failures.
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-08-06
locked_by:
resolved_by:
depends_on: []
---

# notify-slack.yml reusable workflow missing in 4 fleet repos → backmerge invalid

## Finding

- Commit `a9743a79` (2026-08-04, "roll out main-backmerge-to-ldr silent-failure defense-in-depth", a follow-up of
  `main_backmerge_to_ldr_silent_failure_2026_08_02` todo 3) added the `notify-failure` job to every repo's
  `main-backmerge-to-ldr.yml`: `uses: ./.github/workflows/notify-slack.yml` (the fleet `notify-slack.yml` reusable
  carrier).
- A reusable-workflow `uses:` reference to a file that does NOT exist in the repo makes the WHOLE workflow invalid at
  parse time — GitHub shows "This run likely failed because of a workflow file issue", **zero jobs**, 0s duration.
- `notify-slack.yml` exists in `scripts/workflow-templates/` (the rollout SSOT) but was only ever copied into repos that
  had a **full** template rollout AFTER it was added to the dir. Repos that last rolled out before then got the
  backmerge file's new notify-failure reference **without** the reusable file.
- Verified missing on `origin/live-defi-rollout` (2026-08-06): **instruments-service** (fixed in-session),
  **execution-service**, **market-data-processing-service**, **e2e-testing**. Present (blob `56354f32`) in
  alerting-service, deployment-service, market-tick-data-service, features-service, unified-trading-library, PM, and
  others.

## Impact (proven on instruments-service)

- `main-backmerge-to-ldr` failed 0s/0jobs on every main push since the first push after the rollout (measured
  08-04T20:42 → 08-06, 100% failure; runs have an empty `jobs` array).
- With the main→LDR bridge dead, main and `live-defi-rollout` drifted → the LDR→main promote PR became CONFLICTING → a
  conflicting PR has no merge-ref → its required `quality-gates-v2` check can never report → promotion permanently
  blocked (this is the shape that produced ldr_qg_failure escalation agt-9e4351 / PR #1082).
- The same class of silent CI death is likely already wedging the other 3 repos' promotions; they just have not been
  escalated yet.

## Fix applied (instruments-service)

- `38821603` — added `.github/workflows/notify-slack.yml` (canonical template blob `56354f32`, byte-identical to the
  fleet copy) via quickmerge.
- `b75a7040` — back-merged `origin/main` into `live-defi-rollout`, resolving the 3 drifted-file conflicts
  (pyproject.toml `unified-api-contracts>=0.95.0`, regenerated `cefi.json` golden, `DEFI` target count 102) to LDR's
  newer side. LDR now contains main → the next promote PR is conflict-free and its v2 fires green.
- Verified: promote PR #1084 (head 497c4f5e) MERGEABLE, `quality-gates-v2` SUCCESS (run 31082043349),
  `sit-gate/fleet-green` SUCCESS, current LDR head QG-GREEN (run 31082699158).

## Remaining

- [ ] [INFRA] P1. **Roll out notify-slack.yml to the 3 missing repos** — execution-service,
      market-data-processing-service, e2e-testing — via
      `bash unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh --template notify-slack.yml` (or
      a full rollout), commit + push each, then verify their `main-backmerge-to-ldr` runs start producing real job
      output (not the 0s/0job parse failure). The same fix as instruments-service `38821603`. Evidence: the blob must be
      `56354f32ea68feb5a47ffc162ed3a0293e0dc632`.

## Progress Log

- **2026-08-06 (slot-11, cicd agt-9e4351)**: Found while root-causing instruments-service ldr_qg_failure. Added
  notify-slack.yml to instruments-service @38821603 + back-merged main @b75a7040. Promotion re-gated green
  (quality-gates-v2 + sit-gate SUCCESS on PR #1084, MERGEABLE). Filed this doc for the 3 remaining repos.

## Related (for the final-merge state)

- The promote PR #1084's final merge is additionally gated on `image-build-gate`'s `validate / GCP Cloud Build` job
  being stuck QUEUED on the `[self-hosted, glue]` runner pool — covered separately by
  `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` (open OPERATOR-gated).
