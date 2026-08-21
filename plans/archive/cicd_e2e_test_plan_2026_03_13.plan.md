---
doc_type: plan
title: cicd-e2e-test-plan
summary: End-to-end test plan for the full CI/CD pipeline stack. Validates all autonomous components, SIT lock lifecycle,
  hotfix path, Cloud Build routing, YAML validation, conflict resolution agent, Telegram inventory, and semver agent — with
  a test for each major decision point in cicd-pipeline-definition.yaml. Created after CI-CD-FLOW.md was expanded (2026-03-13)
  to identify untested gaps and drive systematic production validation.
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
type: infra
epic: epic-infra
superseded_by: cicd_e2e_testing_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: test plan — no cloud deployment artifact. BR N/A: internal tooling.'}
- {repo: system-integration-tests, code: C3, deployment: none, business: none, readiness_note: Audit agent tests live here.}
depends_on: [full_autonomous_agent_ci, conflict_resolution_agent_2026_03_13]
todos:
- {id: test-overnight-orchestrator, content: 'Trigger overnight-agent-orchestrator.yml via workflow_dispatch. Verify in GHA logs: (1) T0 jobs fire first (no T1 jobs run while T0 is pending); (2) T1 jobs start only after all T0 jobs show result=success; (3) T2 waits on T1, T3 waits on T2; (4) notify job fires with if: always() regardless of tier results; (5) Telegram morning summary message received with pass/fail counts. If ANTHROPIC_API_KEY is not set, agent steps should fail gracefully (not corrupt workflow state). Acceptance: tier ordering structurally enforced, Telegram fires, no cross-tier contamination.

    ', status: pending}
- {id: test-conflict-resolution-agent, content: "Blocked on: create-conflict-resolution-agent-workflow (conflict_resolution_agent plan). Once conflict-resolution-agent.yml exists: (1) Create a test repo branch with a deliberate merge conflict (edit same line differently on feat/* vs staging). (2) Open a PR feat/* → staging. Verify: feature-branch-to-staging.yml template detects CONFLICTING\n    and dispatches merge-conflict-detected to PM.\n(3) Verify conflict-resolution-agent.yml fires: Telegram \"working\" received. (4) Verify agent opens a resolution PR with QG advisory result in PR body. (5) Verify Telegram \"done\" message with PR URL received. (6) Verify agent does NOT self-merge the PR. Acceptance: full dispatch chain works, human review gate holds, both Telegram messages fire.\n", status: pending, blocks: create-conflict-resolution-agent-workflow (conflict_resolution_agent plan)}
- {id: test-sit-lock-cycle, content: 'Validate the full SIT lock/unlock cycle for a breaking change: (1) Push a feat!: change to a T2 interface repo via quickmerge --to-staging. (2) Verify staging_status.locked=false before SIT starts (check manifest via gh api). (3) Wait for SIT to start; verify staging_status.locked=true (sit-gate.yml fired). (4) Verify staging_commits[repo] contains the correct SHA. (5) Verify Telegram "SIT locked" message received. (6) If SIT passes: verify staging_status.locked=false after staging-to-main, versions[repo] promoted. (7) If SIT fails: verify staging_status.locked=false via sit-unlock.yml, Telegram "SIT failed" received. Acceptance: lock state transitions correctly, SHA pinning works, Telegrams fire on both paths.

    ', status: pending}
- {id: test-hotfix-fast-path, content: 'Validate the abbreviated SIT hotfix path: (1) Run quickmerge --hotfix "fix: test hotfix path" in a T3 service repo. (2) Verify manifest staging_status.hotfix_mode=true immediately after push. (3) Verify smoke-test-gate.yml reads hotfix_mode and routes to tests/abbreviated/ only. (4) Verify SIT completes in under 2 minutes (abbreviated = schema checks only). (5) Verify hotfix_mode is cleared after SIT pass. (6) Verify NO code-tests or deployment-tests job ran (check GHA job list). Acceptance: full path < 5 min end-to-end, hotfix_mode flag lifecycle correct.

    ', status: pending}
- {id: test-cascade-selectivity, content: "Validate that the dep-update cascade is selective (only direct dependents dispatched): (1) Push a fix: change to a T1 library (e.g. unified-events-interface) via quickmerge. (2) After version-bump.yml fires, inspect PM's update-repo-version.yml run:\n    (a) Check which repos received dependency-update dispatch in the run logs.\n    (b) Verify ONLY repos with unified-events-interface in their manifest.repositories[].dependencies received\ndispatch.\n    (c) Verify repos that don't depend on UEI (e.g. strategy-ui) did NOT receive dispatch.\n(3) Check that each dispatched repo created a [skip ci] constraint update commit on staging. Acceptance: cascade topology matches manifest DAG exactly, no spurious dispatches.\n", status: pending}
- {id: test-cloud-build-routing, content: "Validate Cloud Build routing per branch: (1) Push to feat/* in any service repo → verify cloud-build-router.yml routes to uts-dev-ikenna project.\n    Image tag must contain branch slug (e.g. 0.1.5-feat-my-feature).\n(2) Push to staging → verify uts-staging-ikenna project receives build, tag ends in -staging. (3) After staging-to-main.yml fires → verify uts-prod-ikenna project receives build, tag is clean semver. (4) Library repo: verify NO Docker build (wheel build only, no Dockerfile step). (5) Verify GCP_SA_KEY_DEV / _STAGING / _PROD auth each used for the correct project. Acceptance: routing table matches cloud-build-router.yml spec, image tags immutable and correctly formatted.\n", status: pending}
- {id: test-yaml-validation-rejection, content: "Validate that YAML syntax errors are caught pre-merge: (1) Introduce a deliberate actionlint error in a .github/workflows/ file\n    (e.g. invalid expression ${{ ... }}). Verify quality-gates.sh exits non-zero.\n(2) Introduce a yamllint error (bad indentation in a service YAML). Verify blocked. (3) Introduce an invalid Cloud Build substitution in cloudbuild.yaml.\n    Verify validate-cloudbuild.py exits non-zero and blocks quality-gates.sh.\n(4) Introduce an invalid phase name in buildspec.aws.yaml.\n    Verify validate-buildspec.py exits non-zero.\n(5) Fix each error and verify all four checks pass. Acceptance: all 4 validators catch their respective error classes, zero false positives on valid YAML.\n", status: pending}
- {id: test-semver-agent-staging-trigger, content: 'Blocked on: fix-semver-agent-template-staging-trigger (full_autonomous_agent_ci plan). After semver-agent.yml template is fixed to trigger on staging (not main): (1) Push a feat: commit to a T2 repo via quickmerge --to-staging. (2) Verify semver-agent.yml fires on staging push (not on feat/* push, not on main push). (3) Verify minor version bump applied to pyproject.toml (feat: → minor). (4) Verify CHANGELOG.md entry prepended with correct version and date. (5) Verify [skip ci] commit pushed to staging (no re-run of semver-agent on that commit). (6) Verify version-bump.yml is disabled (if: false) — no double-bump. Acceptance: exactly one version bump per staging merge, correct magnitude, no double-bump.

    ', status: pending, blocks: fix-semver-agent-template-staging-trigger (full_autonomous_agent_ci plan)}
- {id: test-composite-action-inheritance, content: 'Blocked on: create setup-python-tools action (composite_action_qg_inheritance_2026_03_12 plan P0). After setup-python-tools/action.yml and run-quality-gates/action.yml are created: (1) Push to PM main. Verify action is reachable at IggyIkenna/unified-trading-pm/.github/actions/setup-python-tools@main. (2) Open a PR in alerting-service. Verify CI uses the composite action (check job logs for "Setup Python CI tools"). (3) Verify Python version = 3.13.9 in the CI runner. (4) Verify basedpyright version = 1.38.2 (from action, not from fallback PATH install). (5) Verify tool versions in setup-python-tools match workspace pinned versions. (6) Push a bad Python version to PM action → verify ALL service repos fail CI (proves inheritance). (7) Revert and verify all service repos recover. Acceptance: composite action inheritance works, versions propagate from PM, breakage is visible.

    ', status: pending, blocks: P0 in composite_action_qg_inheritance_2026_03_12.md}
- {id: test-staging-version-gate, content: 'Validate the per-repo staging version gate (block PRs below 1.0.0): (1) Take a repo currently at 0.x.x. Attempt quickmerge --to-staging. (2) Verify staging-version-gate required status check FAILS with message "version < 1.0.0". (3) Verify the PR is created but auto-merge CANNOT fire (gate is blocking). (4) Manually bump repo to 1.0.0 (simulate approval gate). Re-run quickmerge --to-staging. (5) Verify staging-version-gate now passes, auto-merge proceeds. Acceptance: 0.x.x repos cannot merge to staging, 1.0.0 gate enforces production readiness.

    ', status: pending}
- {id: test-telegram-inventory, content: 'Verify all Telegram alert types from the inventory in CI-CD-FLOW.md fire correctly: (a) Overnight summary — trigger workflow_dispatch on overnight-agent-orchestrator.yml. (b) Conflict detected + working + done — requires conflict-resolution-agent.yml (blocked on todo above). (c) Codex sync — push a manifest change to PM main, wait for manifest-sync.yml + codex-sync-agent.yml. (d) Rules alignment — push a new plan todo to PM, wait for rules-alignment-agent.yml. (e) MAJOR bump pending — trigger request-major-bump.yml manually for a test repo. (f) SIT locked + pass/fail — covered by test-sit-lock-cycle above. (g) Cassette drift — trigger cassette-drift-check.yml via workflow_dispatch with a deliberate schema mismatch. For each: verify message content matches inventory table, correct emoji/format, received on correct chat. Acceptance: all 11 alert types fire with correct content. Zero alerts fire spuriously on normal operations.

    ', status: pending}
- {id: register-in-ssot-index, content: 'Add this plan to unified-trading-codex/00-SSOT-INDEX.md in the Plans section (after the conflict_resolution_agent row). Entry format: | cicd_e2e_test_plan_2026_03_13.md | E2E test plan for full CI/CD stack | unified-trading-pm/plans/active/ |

    ', status: pending}
isProject: false
---

# CI/CD E2E Test Plan

**Purpose:** Systematically validate every major component and decision point in the CI/CD pipeline after the
`CI-CD-FLOW.md` expansion (2026-03-13). This plan drives production confidence by testing the parts of the system that
were previously documented but not end-to-end validated.

## Coverage Map

Each todo maps to a decision diamond or key node in `cicd-pipeline-definition.yaml`:

| Todo                              | Pipeline Node(s)                                        | Status            |
| --------------------------------- | ------------------------------------------------------- | ----------------- |
| test-overnight-orchestrator       | `overnight_orchestrator`                                | pending           |
| test-conflict-resolution-agent    | `conflict_detected`, `conflict_agent`, Telegram nodes   | pending (blocked) |
| test-sit-lock-cycle               | `sit_gate_lock`, `staging_to_main`, `sit_unlock_fail`   | pending           |
| test-hotfix-fast-path             | `hotfix_mode_decision`, `abbreviated_sit`               | pending           |
| test-cascade-selectivity          | `dep_cascade`, `update_repo_version`                    | pending           |
| test-cloud-build-routing          | `cloud_build_router`, `build_dev/staging/prod`          | pending           |
| test-yaml-validation-rejection    | `qg_yml` (actionlint, yamllint, validate-cloudbuild.py) | pending           |
| test-semver-agent-staging-trigger | `semver_agent`                                          | pending (blocked) |
| test-composite-action-inheritance | `qg_yml` (composite action)                             | pending (blocked) |
| test-staging-version-gate         | `version_gate_decision`                                 | pending           |
| test-telegram-inventory           | All `tg_*` nodes                                        | pending           |

## Untested Gaps (Known Risks)

From the 2026-03-11 full audit:

- Float price fields in `features.py` execution path — not covered by any test in this plan (tracked in
  `full_autonomous_agent_ci` §5 audit section)
- `DISABLE_AUTH` misconfiguration not caught by QG — tracked in audit §3
- `MIN_COVERAGE` vs `pyproject.toml fail_under` mismatch — tracked in §11

## Prerequisites

| Prerequisite                                  | Plan                                              |
| --------------------------------------------- | ------------------------------------------------- |
| `ANTHROPIC_API_KEY` set in all repo secrets   | `api_keys_and_auth` plan                          |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` set | `api_keys_and_auth` plan                          |
| `conflict-resolution-agent.yml` created       | `conflict_resolution_agent_2026_03_13` plan       |
| `semver-agent.yml` staging trigger fixed      | `full_autonomous_agent_ci` plan                   |
| `setup-python-tools/action.yml` created       | `composite_action_qg_inheritance_2026_03_12` plan |

## Running Individual Tests

```bash
# test-overnight-orchestrator
gh workflow run overnight-agent-orchestrator.yml --repo IggyIkenna/unified-trading-pm

# test-hotfix-fast-path (in any T3 service repo)
cd <service-repo>
bash scripts/quickmerge.sh "fix: test hotfix path" --hotfix --agent

# test-yaml-validation-rejection
echo "invalid: [" >> .github/workflows/quality-gates.yml
bash scripts/quality-gates.sh  # should exit non-zero with actionlint error
git restore .github/workflows/quality-gates.yml

# test-staging-version-gate (requires 0.x.x repo)
bash scripts/quickmerge.sh "feat: test version gate" --to-staging --agent
# Expect: PR created, staging-version-gate FAILS
```

## References

- `docs/repo-management/CI-CD-FLOW.md` — SSOT for full pipeline (Conflict Resolution Agent, YAML Validation, Telegram
  Inventory, Agent Cursor Rules sections)
- `docs/repo-management/cicd-pipeline-definition.yaml` — YAML data source for visual diagram
- `docs/repo-management/CI-CD-PIPELINE.html` — Interactive diagram (hover for node details)
- `plans/active/conflict_resolution_agent_2026_03_13.md` — Conflict agent implementation
- `plans/active/full_autonomous_agent_ci.md` — Audit agent + semver agent todos
- `plans/active/work/cicd/composite_action_qg_inheritance_2026_03_12.md` — Composite action plan
