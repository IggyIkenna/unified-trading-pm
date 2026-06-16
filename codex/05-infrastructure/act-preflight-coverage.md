---
scope: [engineer, admin]
title: act-preflight workflow coverage
type: infrastructure
last_reviewed: 2026-05-17
status: living
owner: workspace-platform
cadence: re-review whenever a new workflow lands or an existing one gains a non-runner job
verifier: bash unified-trading-pm/scripts/dev/act-preflight.sh --repo <name>
last_executed: 2026-05-17
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

## Workspace workflows (`unified-trading-pm/.github/workflows/`)

| Workflow                              | Status         | Notes                                                                              |
| ------------------------------------- | -------------- | ---------------------------------------------------------------------------------- |
| `agent-audit.yml`                     | 🔴 REMOTE-ONLY | Uses `gh` against live repos; needs `GITHUB_TOKEN` with org scope                  |
| `auto-merge-minor-fixes.yml`          | 🔴 REMOTE-ONLY | Triggers on PR labels; cannot be simulated locally                                 |
| `build-smoke-all-repos.yml`           | 🟡 PARTIAL     | Matrix expansion runs under act; per-repo build step needs Cloud Build trigger     |
| `cascade-qg-ordering.yml`             | 🔴 REMOTE-ONLY | Cross-repo workflow dispatch                                                       |
| `cassette-drift-check.yml`            | ✅ FULL        | Pure Python contract check; runs cleanly under act                                 |
| `change-freeze-check.yml`             | ✅ FULL        | Reads `unified-trading-pm/freeze-state.json`; no network                           |
| `ci-status-update.yml`                | 🔴 REMOTE-ONLY | Posts to GitHub Checks API                                                         |
| `claude-api-health-monitor.yml`       | 🔴 REMOTE-ONLY | Hits Anthropic API; requires `ANTHROPIC_API_KEY`                                   |
| `cloud-build-router.yml`              | 🔴 REMOTE-ONLY | Triggers GCP Cloud Build                                                           |
| `cold-storage-cleanup.yml`            | 🔴 REMOTE-ONLY | gsutil against `gs://*-cold/`                                                      |
| `conflict-resolution-agent.yml`       | 🔴 REMOTE-ONLY | Spawns Claude API agent run                                                        |
| `conflict-resolution-merged.yml`      | 🔴 REMOTE-ONLY | PR-merge-driven                                                                    |
| `contract-drift-record.yml`           | ✅ FULL        | Computes diff vs `unified_api_contracts` and writes artifact                       |
| `downstream-fix-agent.yml`            | 🔴 REMOTE-ONLY | Cross-repo dispatch + Claude API                                                   |
| `fix-approval-timeout.yml`            | ⚙️ N/A         | Scheduled cron only                                                                |
| `hotfix-mode.yml`                     | 🔴 REMOTE-ONLY | PR label-driven; cross-repo                                                        |
| `infra-quality-gates.yml`             | 🟡 PARTIAL     | Lint phase runs locally; terraform plan step needs cloud creds                     |
| `major-bump-approval.yml`             | 🔴 REMOTE-ONLY | Triggered by issue-comment `/approve`                                              |
| `major-bump-issue-handler.yml`        | 🔴 REMOTE-ONLY | Issue-event driven                                                                 |
| `notify-telegram.yml`                 | 🔴 REMOTE-ONLY | Needs `TELEGRAM_BOT_TOKEN`                                                         |
| `overnight-agent-orchestrator.yml`    | ⚙️ N/A         | Scheduled cron — runs nightly only                                                 |
| `overnight-dead-man-switch.yml`       | ⚙️ N/A         | Scheduled cron                                                                     |
| `persist-cicd-event.yml`              | 🔴 REMOTE-ONLY | Writes to BigQuery                                                                 |
| `plan-health-agent.yml`               | 🔴 REMOTE-ONLY | Claude API + cross-repo                                                            |
| `plan-notification.yml`               | 🔴 REMOTE-ONLY | Slack/Telegram fan-out                                                             |
| `publish-package.yml`                 | 🔴 REMOTE-ONLY | Pushes to Artifact Registry                                                        |
| `python-quality-gates.yml`            | ✅ FULL        | Repo-local pytest + ruff + basedpyright (assuming `.venv` resolvable in container) |
| `quality-gates.yml`                   | ✅ FULL        | Top-level orchestrator; calls only repo-local scripts                              |
| `readiness-verifier.yml`              | 🟡 PARTIAL     | Plan-inventory regen runs locally; GCP-status step is remote                       |
| `request-major-bump.yml`              | 🔴 REMOTE-ONLY | Issue-creation flow                                                                |
| `rollout-action-ref.yml`              | 🔴 REMOTE-ONLY | PR fan-out across repos                                                            |
| `rules-alignment-agent.yml`           | 🔴 REMOTE-ONLY | Claude API spawn                                                                   |
| `schema-changed-handler.yml`          | 🟡 PARTIAL     | Path-filter + symbol grep runs locally; downstream dispatch is remote              |
| `secret-health-check.yml`             | 🔴 REMOTE-ONLY | Needs Secret Manager + AWS Secrets Manager                                         |
| `semver-agent.yml`                    | 🔴 REMOTE-ONLY | Tag + release creation                                                             |
| `sit-debounce-trigger.yml`            | 🔴 REMOTE-ONLY | Cross-repo dispatch                                                                |
| `sit-gate.yml`                        | 🔴 REMOTE-ONLY | Cross-repo + GCS state                                                             |
| `sit-starvation-detector.yml`         | ⚙️ N/A         | Scheduled cron                                                                     |
| `sit-unlock.yml`                      | 🔴 REMOTE-ONLY | Manual dispatch with auth check                                                    |
| `staging-to-main.yml`                 | 🔴 REMOTE-ONLY | PR merge orchestration                                                             |
| `ui-quality-gates.yml`                | ✅ FULL        | pnpm + vitest only; runs cleanly under act on UI repos                             |
| `update-repo-version.yml`             | 🔴 REMOTE-ONLY | Edits + commits across repos                                                       |
| `workspace-quickmerge-validation.yml` | 🟡 PARTIAL     | Schema lint runs; cross-repo merge gate is remote                                  |

**Workspace coverage**: 6 FULL · 6 PARTIAL · 28 REMOTE-ONLY · 5 N/A (45 total)

## Per-service-repo workflows

Every service repo carries copies of:

- `quality-gates.yml` — repo-local QG runner (✅ FULL under act for repos with `.venv` + scripts/quality-gates.sh)
- `python-quality-gates.yml` (when applicable) — ✅ FULL
- `cassette-drift-check.yml` (UAC consumers) — ✅ FULL
- `auto-merge-minor-fixes.yml` — 🔴 REMOTE-ONLY (PR-driven)

For a fresh service repo, the _baseline_ expectation is that `act-preflight.sh --repo <name>` runs `quality-gates.yml`
end-to-end. If it fails because of:

- **missing `.venv`**: bootstrap via `cd <repo> && uv venv && uv pip install -e .` — this is a workspace setup gap, not
  an act limitation
- **missing dep**: same — workspace deps must be present locally for act to mirror remote
- **secrets requested by a step**: that step is REMOTE-ONLY and the workflow should be re-classified PARTIAL in this
  matrix

## Coverage targets

- Workspace workflows: 6/45 FULL is the steady-state ceiling — most workspace workflows are designed to coordinate
  across repos and cannot be exercised against a single local checkout.
- Service repos: 100% of `quality-gates.yml` invocations should be FULL — any new step that reaches for a secret or
  external API must be split into a separate workflow tagged REMOTE-ONLY in this matrix so `act-preflight.sh` keeps
  returning meaningful signal.

## Operational guidance

- **Before pushing a service-repo change**: `bash unified-trading-pm/scripts/dev/act-preflight.sh --repo <name>` to
  rehearse `quality-gates.yml`. Green here = remote will be green for the QG path.
- **Before pushing a workspace workflow change**: act covers syntax (`act --list`); for PARTIAL/REMOTE-ONLY workflows,
  push to `live-defi-rollout` first and watch via `gh run watch --repo IggyIkenna/unified-trading-pm`.
- **New workflow added**: append a row to the appropriate table above + update the coverage total. A workflow without a
  row in this matrix is review-blocking — the reviewer cannot reason about pre-push validation otherwise.

## Composes with

- [`deployment-and-qg-strategy.md`](deployment-and-qg-strategy.md) — overall QG layering
- [`cicd-setup.md`](cicd-setup.md) — remote CI pipeline architecture
- `scripts/dev/act-preflight.sh` — the wrapper this doc certifies
