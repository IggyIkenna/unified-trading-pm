---
doc_type: issue
title:
  features-service live-defi-rollout QG red (sports squad_value coverage-gate test) blocks the FixDigestPin cloudbuild
  auto-repin ship
summary:
  The FixDigestPin fix for features-service-sports-job (footgun B — digest-pin requires a manual per-rollout re-pin) is
  designed, verified read-only, and coded (features-service/cloudbuild.yaml auto-repin step + deployment-service sports
  tfvars flip to :latest, the fleet convention). It cannot SHIP because features-service's live-defi-rollout tree is red
  on a pre-existing, unrelated sports coverage-gate test
  (tests/sports/unit/test_run_new_calculators_coverage_gate.py::TestOlderCalculatorsCoverageGate::test_squad_value_pre_launch_is_out_of_coverage,
  asserts squad_value status == out_of_coverage but gets partial). Red across 5 of the last 6 features-service
  quality-gates-v2 CI runs (one success at 18:25Z → flaky/data-dependent). Not caused by the cloudbuild.yaml change
  (never imported by pytest). Blocks a green local QG sentinel → quickmerge refuses. Shipping the deployment-service
  tfvars :latest half ALONE reintroduces the original staleness footgun, so both must land together once green.
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [features-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [red-tree, sports, coverage-gate, ci-blocking, digest-pin, incident]
related: [/plans/archive/2026_07/features_sports_service_consolidation_deploy_2026_07_15.md]
created: 2026-07-15
last_updated: 2026-07-21
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
resolved_by: "features-service@1d65390a"
source:
  FixDigestPin (footgun B) task, features_sports_service_consolidation_deploy_2026_07_15.md P2 re-pin todo, slot-3,
  2026-07-15
---

# features-service red tree blocks the FixDigestPin cloudbuild auto-repin ship

> **Filed by**: the FixDigestPin (footgun B) `/autonomous` sub-agent, slot-3, 2026-07-15, per the findings-triage HARD
> RULE (pre-existing outside-plan failure that is BLOCKING a ship + branch-health / CI-blocking → issue doc + operator
> notify). The failure is NOT caused by this task's change.

## The fix that is ready to ship (design + verification)

Footgun B: `features-service-sports-job`'s terraform `docker_image` was `@sha256:` digest-pinned, so every future
features-service image rollout needed a MANUAL tfvars re-pin or the job silently kept the old image (the exact
silent-staleness mode that broke features-sports for 5+ weeks). The established fleet convention to keep a Cloud Run JOB
current on `:latest` is a **post-push `gcloud run jobs update <job> --image=…:latest` step in the service's own
cloudbuild.yaml**, failure-tolerant — three precedents:

- `deployment-service/cloudbuild.yaml` id `redeploy-monitor-jobs` (re-pins the 4 dp-\* monitor jobs to deployment-api
  `:latest`; closed the same "manual re-pin gap" per
  `plans/active/issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md`).
- `deployment-service/cloud-build/deployment-service-jobs-image.cloudbuild.yaml` id `redeploy-jobs`.
- `deployment-service/scripts/cloud-run/deploy-shared.sh` (rollup-job sync after each build).

**Edits made (in the slot-3 working tree, uncommitted — held for a green tree):**

1. `features-service/cloudbuild.yaml` — new post-`push` step `redeploy-features-jobs` (image `cloud-sdk:slim`,
   `waitFor: ["push"]`):
   `gcloud run jobs update features-service-sports-job --image=asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_REGISTRY_REPO}/${_SERVICE_NAME}:latest`,
   failure-tolerant (WARN not fail). Makes every features-service-backed job track each build automatically.
2. `deployment-service/terraform/services/features-service-sports/gcp/terraform.tfvars` — `docker_image` flipped from
   the `@sha256:b7fc3d7f…` pin to `:latest` (matches EVERY other service tfvars in the tree) + comment rewrite.

**Verification (read-only, no rebuild, no live mutation):**

- `features-service:latest` (shared `unified-trading-system` registry) resolves to
  `sha256:b7fc3d7f7b92fe37edfae592b8c62244ecc46d5598dd4e08571508de08fb3117` — the EXACT digest currently pinned in
  tfvars and running on the live job → flipping to `:latest` is **behavior-neutral today**.
- `gcloud run jobs describe features-service-sports-job` → job exists, image `@sha256:b7fc3d7f…`. The update command is
  well-formed and idempotent.
- `cloudbuild.yaml` parses (yaml.safe_load); step order correct; prettier + `tofu fmt` clean.
- **deployment-service QG green** (`✅ ALL QUALITY GATES PASSED`, sentinel written for `0c3fb77`).

**These two edits are a matched pair.** Shipping the tfvars `:latest` flip WITHOUT the cloudbuild auto-repin step
recreates the original footgun (a bare `:latest` in tfvars only re-resolves at `tofu apply` time, not on each build). Do
NOT ship one without the other.

## The blocker (facts)

- `features-service` HEAD == `origin/live-defi-rollout` == `d695c06b`. Only uncommitted diff in the slot =
  `cloudbuild.yaml` (this task's change).
- `bash scripts/quality-gates.sh --no-fix` → `1 failed, 17555 passed`. The one failure:
  `tests/sports/unit/test_run_new_calculators_coverage_gate.py::TestOlderCalculatorsCoverageGate::test_squad_value_pre_launch_is_out_of_coverage`
  — `AssertionError: assert 'partial' == 'out_of_coverage'` (squad_value produced 12 all-NaN columns → schema violation
  → recovery=skip; coverage classified `partial` not `out_of_coverage`).
- Pre-existing + unrelated: `cloudbuild.yaml` is never imported by pytest; the test lives entirely in the
  sports-calculator/exporter domain. Last touched by `features-service@7c4e9b00` (harshkantariya, Jun 16, "fix stale
  sports coverage-start gate tests"); the same test name appears in the archived
  `plans/archive/issues/qg_firefight_fixes_2026_06_16.md`.
- Authoritative CI: `features-service` `quality-gates-v2` on `live-defi-rollout` = FAILURE on 5 of the last 6 runs
  (success once at 2026-07-15T18:25Z) → flaky / data-dependent (squad_value coverage depends on transfermarkt fixture
  presence), and **features-service promotions are branch-blocked** meanwhile.
- Effect on this task: no green local QG sentinel is reachable → `quickmerge` Pass 2 refuses. Not fixing the sports test
  here — out of scope (sports data-correctness), collision risk (another agent's/domain's file), and a naive assertion
  flip could MASK a real coverage-classification regression.

## Recommended resolution

1. Sports/features-service owner fixes or de-flakes `test_squad_value_pre_launch_is_out_of_coverage` (decide whether
   squad_value should be `out_of_coverage` or `partial` given current fixture coverage; the assertion or the fixture is
   stale — a domain call, not an infra one). This also unblocks all features-service promotions.
2. Once features-service is green: `quality-gates.sh` (green) → `quickmerge --agent --files 'cloudbuild.yaml'`
   (features-service) AND `--files 'terraform/services/features-service-sports/gcp/terraform.tfvars'`
   (deployment-service) — **together**. Then flip the P2 re-pin todo in
   `features_sports_service_consolidation_deploy_2026_07_15.md` with the two shas.

## Resolution (2026-07-21)

**Root cause: STALE TEST ASSERTION, not a coverage-classification bug — and it was already fixed before this
investigation started.** `test_squad_value_pre_launch_is_out_of_coverage` derives `pre_launch` from
`get_source_coverage_start(SPORTS_DATA_TYPE_TO_SOURCE["PLAYER_VALUES"], "PLAYER_VALUES")` (the LIVE UAC transfermarkt
floor) rather than a hardcoded date. Commit `features-service@1d65390a` ("fix(sports-tests): update squad_value
coverage-gate test for uac@c280e1ff floor amendment", landed 2026-07-16, the day after this doc was filed) is what made
the derivation live — before it, the test's prior hardcoded pre-launch date went stale every time the UAC transfermarkt
floor moved (the same failure class the docstring in the test now documents in detail). Once derivation replaced the
hardcoded date, the test became self-correcting: `pre_launch` is always defined as 1 day before whatever the current UAC
floor is, so `check_calculator_coverage("squad_value", …)` always returns `OUT_OF_COVERAGE` for it, by construction —
regardless of where the floor happens to sit.

**Verified independently, live, 2026-07-21 (before any code change):**

- **CI**: `features-service` `quality-gates-v2` on `live-defi-rollout` has been GREEN on every run since `35e6bb49` /
  `2026-07-16T06:50:47Z` (the run right after `1d65390a` landed) through the current HEAD `0445eaec`
  (`2026-07-21T13:33:32Z`) — **40+ consecutive successes**, spanning today's separate 2020-06-06 sports-floor revert
  (`uac@8cdf7808`, `/codex/02-data/sports-2020-06-data-floor.md`) with no break. That revert changed the LIVE floor
  value the test derives from (transfermarkt 2018-01-01 → 2020-06-06) and the test kept passing — direct proof the
  derivation fix is robust to floor churn, which was its explicit design intent.
- **Local**: `features-service` HEAD == `origin/live-defi-rollout` == `0445eaec`, clean tree.
  `check_calculator_coverage(calc_name="squad_value", ref_data={"player_values": …}, target_date=date(2020, 6, 5))` →
  `CoverageDecision(verdict=OUT_OF_COVERAGE, reason='all_upstreams_out_of_coverage')` (matches the test's expectation).
  `.venv/bin/python -m pytest tests/sports/unit/test_run_new_calculators_coverage_gate.py -v` → **8 passed** (the whole
  module, not just the one test).

**Effect**: this task's premise (tree currently red, blocking all features-service promotions) was **stale** — factually
true 2026-07-15, not true since 2026-07-16. No code change was needed or made in this session; nothing to ship via
quickmerge for this issue. The paired digest-pin fix (`features-service/cloudbuild.yaml` auto-repin step +
`deployment-service` tfvars `:latest` flip) described above under "The fix that is ready to ship" remains **separately
unshipped** — out of scope for this resolution — but its blocker (this red tree) is now cleared. Its owner should
re-verify the diff before shipping (the 2026-07-15 slot-3 working tree that held it is 6 days old and may no longer
exist); the open P2 re-pin todo lives in `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md` (not
touched by this resolution).
