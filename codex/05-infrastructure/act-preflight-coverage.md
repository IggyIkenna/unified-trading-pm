---
doc_type: codex-ssot
title: act-preflight workflow coverage
summary:
  Coverage matrix for which .github/workflows entries are fully exercisable under act-preflight.sh (a nektos/act
  wrapper) vs REMOTE-ONLY — 0 FULL / 8 PARTIAL / 51 REMOTE-ONLY of 59 workspace workflows; every PM workflow reaches
  GitHub API, GCP or Slack, so act yields syntax + early-step signal only, and a workflow with no row here is
  review-blocking.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ci, quality-gates, workflows, act, verification, runbook, infrastructure]
related:
  [
    /codex/05-infrastructure/deployment-and-qg-strategy.md,
    /codex/05-infrastructure/cicd-setup.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-05-17
authoritative_for: [act-preflight workflow local-coverage matrix]
referenced_by:
owner: workspace-platform
last_reviewed: 2026-09-14
code_refs:
type: infrastructure
cadence: re-review whenever a new workflow lands or an existing one gains a non-runner job
verifier: bash unified-trading-pm/scripts/dev/act-preflight.sh --repo <name> --workflow quality-gates-v2.yml
last_executed: 2026-07-31
---

# act-preflight coverage matrix

**Scope:** which `.github/workflows/*.yml` entries are _fully_ exercisable under
[`act-preflight.sh`](../../scripts/dev/act-preflight.sh) — and which require remote-only services (GitHub API, Secret
Manager, Cloud Build, etc.) so they cannot be rehearsed locally.

`act-preflight.sh` (Phase 2 P0 of `deployment_and_qg_strategy_implementation_2026_05_13`) wraps `nektos/act` so a
developer can run a workflow against a local docker runtime before pushing. This doc is the SSOT for _what_ a green
local run actually proves.

## Status taxonomy

| Status             | Meaning                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------ |
| ✅ **FULL**        | Workflow runs end-to-end under act with no external mocks. Local PASS ≡ remote PASS for steady-state         |
| 🟡 **PARTIAL**     | act runs the syntax + early steps; later step needs network/secret. Use act for the first failure-class only |
| 🔴 **REMOTE-ONLY** | Requires GitHub API, secrets, Cloud Build trigger, or cross-repo dispatch — do NOT bother with act           |
| ⚙️ **N/A**         | Manual / scheduled-only / dispatched-only — there is no pre-push signal to validate                          |

## How this matrix is derived

Rows below are derived **statically** (2026-07-31 audit) from each workflow's declared `on:` triggers plus a scan for
external-dependency signals (`GITHUB_TOKEN`/`gh`/`github-script`, `ANTHROPIC_API_KEY`, `gcloud`/`google-github-actions`/
`gs://`, `aws-actions`, `SLACK_*`). It is **not** a record of 59 individual `act` runs — treat a row as the expected
class, and correct it in place the first time a real `act` run disagrees.

## Workspace workflows (`unified-trading-pm/.github/workflows/`)

59 workflows as of 2026-07-31. **No PM workflow is FULL** — every one reaches GitHub API, GCP, Slack or a cross-repo
dispatch, so act yields syntax (`act --list`) plus early-step signal only. The eight PARTIAL rows are the ones where a
genuinely local computation runs before the remote step.

| Workflow                                      | Status         | Notes                                                                  |
| --------------------------------------------- | -------------- | ---------------------------------------------------------------------- |
| `agent-audit.yml`                             | 🔴 REMOTE-ONLY | `workflow_dispatch`; spawns Claude API agent run                       |
| `agent-runner.yml`                            | 🔴 REMOTE-ONLY | `workflow_call` reusable; `gh` against live repos                      |
| `branch-health.yml`                           | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP + Slack                                    |
| `build-smoke-all-repos.yml`                   | 🔴 REMOTE-ONLY | Scheduled; per-repo build needs Cloud Build trigger                    |
| `cascade-qg-ordering.yml`                     | 🔴 REMOTE-ONLY | Cross-repo `repository_dispatch`                                       |
| `cassette-drift-check.yml`                    | 🟡 PARTIAL     | Checkout + isolated-venv + drift detection run locally; issue-create,   |
|                                               |                | persist-event and `notify-slack.yml` fan-out are remote                |
| `change-freeze-check.yml`                     | 🟡 PARTIAL     | `workflow_call` only (no direct act entry); the window check itself is  |
|                                               |                | a local read of `plans/ops/change-freeze-calendar.csv`                  |
| `ci-health.yml`                               | 🔴 REMOTE-ONLY | Scheduled + dispatch; GitHub API + GCP                                 |
| `ci-status-consolidator.yml`                  | 🔴 REMOTE-ONLY | Hourly; projects Firestore `ci_status` → manifest cache                |
| `ci-status-update.yml`                        | 🔴 REMOTE-ONLY | `repository_dispatch`; writes Firestore (per-repo-doc CAS)             |
| `cloud-build-failure-watcher.yml`             | 🔴 REMOTE-ONLY | Scheduled; queries GCP Cloud Build                                     |
| `cloud-build-router-aws.yml`                  | 🔴 REMOTE-ONLY | `repository_dispatch`; GCP + AWS                                       |
| `cloud-build-router.yml`                      | 🔴 REMOTE-ONLY | `repository_dispatch`; triggers GCP Cloud Build                        |
| `cold-storage-cleanup.yml`                    | 🔴 REMOTE-ONLY | Scheduled; GCS cold-tier cleanup                                       |
| `conflict-resolution-agent.yml`               | 🔴 REMOTE-ONLY | Spawns Claude API agent run                                            |
| `conflict-resolution-merged.yml`              | 🔴 REMOTE-ONLY | `pull_request`-merge driven                                            |
| `deterministic-promotion-conflict-resolve.yml`| 🔴 REMOTE-ONLY | Dispatch-driven; GitHub API + Slack                                    |
| `digest-drift-sweep.yml`                      | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP                                            |
| `escalate-to-orchestrator.yml`                | 🔴 REMOTE-ONLY | Reusable + dispatch; Claude API + Slack                                |
| `fix-approval-timeout.yml`                    | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP + Slack                                    |
| `freeze-deferred-build-replay.yml`            | 🔴 REMOTE-ONLY | Scheduled; replays deferred builds via GitHub API                      |
| `glue-pool-starvation-monitor.yml`            | 🔴 REMOTE-ONLY | Scheduled; GitHub API + Slack                                          |
| `hotfix-mode.yml`                             | 🔴 REMOTE-ONLY | `repository_dispatch`; cross-repo                                      |
| `image-build-validate.yml`                    | 🔴 REMOTE-ONLY | `workflow_call`; GCP + AWS registries                                  |
| `ldr-ci-monitor.yml`                          | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP + Slack                                    |
| `ldr-docs-gate.yml`                           | 🟡 PARTIAL     | Doc-gate scripts run locally; Slack notify is remote                   |
| `ldr-to-main-promote-fleet.yml`               | 🔴 REMOTE-ONLY | `*/15` fleet promote; opens + auto-merges PRs                          |
| `ldr-to-main-promote.yml`                     | 🔴 REMOTE-ONLY | `*/15` PM promote; opens + auto-merges PRs                             |
| `ldr-to-staging-promote.yml`                  | 🔴 REMOTE-ONLY | Dispatch; staging path (DORMANT by default)                            |
| `main-backmerge-to-ldr.yml`                   | 🔴 REMOTE-ONLY | `push:[main]`; pushes the reconciled projection back to LDR            |
| `major-bump-issue-handler.yml`                | 🔴 REMOTE-ONLY | `issues` / `issue_comment` driven                                      |
| `notify-slack.yml`                            | 🔴 REMOTE-ONLY | `workflow_call` carrier; needs `SLACK_*` + read-back dedup state       |
| `overnight-agent-orchestrator.yml`            | 🔴 REMOTE-ONLY | Scheduled; Claude API + GCP                                            |
| `overnight-dead-man-switch.yml`               | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP                                            |
| `plan-health-agent.yml`                       | 🟡 PARTIAL     | Plan-hygiene scripts run locally; PR annotation is remote              |
| `plan-notification.yml`                       | 🔴 REMOTE-ONLY | Slack fan-out on push/issues                                           |
| `publish-package.yml`                         | 🔴 REMOTE-ONLY | Pushes wheel to Artifact Registry                                      |
| `python-quality-gates-v2.yml`                 | 🟡 PARTIAL     | `workflow_call`; ruff/basedpyright/pytest run locally, status          |
|                                               |                | reporting + Slack are remote                                           |
| `quality-gates-v2.yml`                        | 🟡 PARTIAL     | **The required check.** QG scripts run locally under act; PR check      |
|                                               |                | reporting needs GitHub API                                             |
| `readiness-verifier.yml`                      | 🟡 PARTIAL     | Plan-inventory regen runs locally; GCP-status step is remote           |
| `reconcile-release-tags.yml`                  | 🔴 REMOTE-ONLY | Scheduled stall detector; GitHub API + GCP                             |
| `reconcile-staging-versions.yml`              | 🔴 REMOTE-ONLY | Dispatch; GitHub API                                                   |
| `removed-symbols-workspace-sweep.yml`         | 🔴 REMOTE-ONLY | Scheduled cross-repo sweep                                             |
| `request-major-bump.yml`                      | 🔴 REMOTE-ONLY | Issue-creation flow (1.0.0 graduation path)                            |
| `rules-alignment-agent.yml`                   | 🔴 REMOTE-ONLY | Claude API spawn on push                                               |
| `ruleset-drift-alert.yml`                     | 🔴 REMOTE-ONLY | Scheduled; reads branch-protection via GitHub API                      |
| `secret-health-check.yml`                     | 🔴 REMOTE-ONLY | Needs Secret Manager + AWS Secrets Manager                             |
| `semver-agent.yml`                            | 🔴 REMOTE-ONLY | `push:[main]`; mints git tags + releases                               |
| `sit-debounce-trigger.yml`                    | 🔴 REMOTE-ONLY | Cross-repo dispatch                                                    |
| `sit-gate.yml`                                | 🔴 REMOTE-ONLY | Cross-repo + GCS state; emits `sit-gate/fleet-green`                   |
| `sit-unlock.yml`                              | 🔴 REMOTE-ONLY | Dispatch with auth check                                               |
| `staging-conflict-ldr-main-fallback.yml`      | 🔴 REMOTE-ONLY | Dispatch; GitHub API                                                   |
| `staging-to-main.yml`                         | 🔴 REMOTE-ONLY | PR merge orchestration                                                 |
| `stale-build-watcher.yml`                     | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP                                            |
| `supersede-stale-dep-update-prs.yml`          | 🔴 REMOTE-ONLY | Scheduled; closes superseded PRs                                       |
| `update-repo-version.yml`                     | 🔴 REMOTE-ONLY | `repository_dispatch`; edits + commits across repos                    |
| `version-coherence-check.yml`                 | 🔴 REMOTE-ONLY | Scheduled; GitHub API + GCP                                            |
| `version-registry-update.yml`                 | 🔴 REMOTE-ONLY | Dispatch; GitHub API + GCP                                             |
| `workspace-quickmerge-validation.yml`         | 🟡 PARTIAL     | Schema lint runs locally; cross-repo merge gate is remote              |

**Workspace coverage**: 0 FULL · 8 PARTIAL · 51 REMOTE-ONLY (59 total)

## Per-service-repo workflows

The per-repo set is rolled out from templates (never hand-edit a copy — see `/codex/08-workflows/ci-cd-flow.md`). As of
2026-07-31 the actual distribution is:

- `quality-gates-v2.yml` — **26 repos**; the required check. 🟡 PARTIAL under act (QG scripts local, check reporting
  remote). This is the workflow `act-preflight.sh` should target.
- `python-quality-gates-v2.yml` — PM only (1). 🟡 PARTIAL.
- `ui-quality-gates.yml` + `ui-quality-gates-v2.yml` — `unified-trading-system-ui`; `ui-quality-gates-v2.yml` also in
  `deployment-ui`. 🟡 PARTIAL (pnpm + vitest local; publish/report remote).
- `cassette-drift-check.yml` — PM only (1), **not** every UAC consumer.
- Common per-repo companions: `agent-audit.yml`, `image-build-gate.yml`, `main-backmerge-to-ldr.yml`,
  `major-bump-issue-handler.yml`, `request-major-bump.yml`, `semver-agent.yml`, `staging-backmerge-to-ldr.yml`,
  `staging-lock-check.yml`, `update-dependency-version.yml`, `version-registry-notify.yml` — all 🔴 REMOTE-ONLY.

> **Retired names — do not re-add rows for these.** `quality-gates.yml`, `python-quality-gates.yml`,
> `auto-merge-minor-fixes.yml`, `claude-api-health-monitor.yml`, `contract-drift-record.yml`, `downstream-fix-agent.yml`,
> `infra-quality-gates.yml`, `major-bump-approval.yml`, `notify-telegram.yml` (superseded by `notify-slack.yml`),
> `persist-cicd-event.yml` (now the `persist-event` composite action), `plan_health-agent.yml` (correct name is
> `plan-health-agent.yml`), `schema-changed-handler.yml`, `sit-starvation-detector.yml` (the live scheduled monitor is
> `glue-pool-starvation-monitor.yml`). All were listed here until the 2026-07-31 re-review; none exist in any repo.

For a fresh service repo, the _baseline_ expectation is that
`act-preflight.sh --repo <name> --workflow quality-gates-v2.yml` reaches the repo-local QG steps. If it fails because
of:

- **missing `.venv`**: bootstrap via `cd <repo> && uv venv && uv pip install -e .` — this is a workspace setup gap, not
  an act limitation
- **missing dep**: same — workspace deps must be present locally for act to mirror remote
- **secrets requested by a step**: that step is REMOTE-ONLY and the workflow should be re-classified PARTIAL in this
  matrix

## Coverage targets

- Workspace workflows: **0 FULL is the honest steady state**, not a gap to close. Every PM workflow exists to coordinate
  across repos, GCP or Slack; none is exercisable end-to-end against a single local checkout. The useful target is that
  each one is at least PARTIAL-classified so a developer knows which first failure-class act can still catch.
- Service repos: the local-signal target is the repo-local phase of `quality-gates-v2.yml` (ruff, basedpyright, pytest).
  Any new step reaching for a secret or external API must be split into a separate workflow tagged REMOTE-ONLY in this
  matrix so `act-preflight.sh` keeps returning meaningful signal.

## Operational guidance

- **Before pushing a service-repo change**:
  `bash unified-trading-pm/scripts/dev/act-preflight.sh --repo <name> --workflow quality-gates-v2.yml` to rehearse the
  repo-local QG phase. Green here = the QG path will be green remotely; the check-reporting step still only runs
  remotely.
  - ⚠️ `act-preflight.sh` still **defaults** `--workflow` to the retired `quality-gates.yml`, so an invocation without
    the explicit `--workflow` flag exits 2 ("workflow not found") on every repo. Tracked in
    `/plans/active/issues/act_preflight_default_workflow_retired_2026_07_31.md`.
- **Before pushing a workspace workflow change**: act covers syntax (`act --list`); for PARTIAL/REMOTE-ONLY workflows,
  push to `live-defi-rollout` first and watch via `gh run watch --repo IggyIkenna/unified-trading-pm`.
- **New workflow added**: append a row to the appropriate table above + update the coverage total. A workflow without a
  row in this matrix is review-blocking — the reviewer cannot reason about pre-push validation otherwise.

## Composes with

- [`deployment-and-qg-strategy.md`](deployment-and-qg-strategy.md) — overall QG layering
- [`cicd-setup.md`](cicd-setup.md) — remote CI pipeline architecture
- `scripts/dev/act-preflight.sh` — the wrapper this doc certifies
