---
doc_type: issue
title: Stop all 6 staging-branch workflows fleet-wide — ~6,900 runs/wk against a branch dead since 2026-06-27
summary: >-
  The `staging` branch has been dormant fleet-wide since 2026-06-27 (frozen, 600-967 commits behind LDR, 0 open PRs in
  any of the 24 repos, PM has no staging branch at all), but six workflows still fire ~6,900 runs/week against it. Two
  are GitHub-hosted fleet templates rendered into 24 repos (`staging-backmerge-to-ldr` hourly cron ~3,216 runs/wk,
  `staging-lock-check` repository_dispatch ~3,168 runs/wk) and account for ~$166/mo — ~97% of the billable waste, and
  they CANNOT be moved to the planning VM because all 8 self-hosted runners are registered to unified-trading-pm only
  (fleet repos have 0; no org-level pool — personal account). The other four are PM-side drivers already migrated to
  `[self-hosted, glue]` in STEP 2 (2026-07-17) and cost $0 — but operator ruling 2026-07-23: "free doesn't mean we want
  them to run" (they still consume VM capacity and clutter the signal), so they stop too. Re-entry is MANUAL (a
  git-tracked `workspace-manifest.json` flip), so nothing auto-routes into a disabled path — the shutdown is reversible
  by uncommenting.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
    e2e-testing,
    execution-service,
    features-service,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    strategy-service,
    system-integration-tests,
    trading-agent-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, staging, workflows, fleet-rollout, spend-reduction]
related:
  - github_actions_ci_cost_reduction_2026_07_15.md
  - stale_staging_versions_manifest_2026_07_23.md
  - ../cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
created: 2026-07-23
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
resolved_by:
  "unified-trading-pm@a7b5cc27c (6 workflow triggers disabled + 2 templates) + 24-repo rollout, all verified on origin;
  effect MEASURED 2026-07-23T09:04Z — staging-backmerge-to-ldr fleet-wide 47 runs in the 2h before promote vs 0 in the
  >1h after, zero repos still firing"
depends_on: []
source:
  - "operator ask 2026-07-23: audit what still runs for staging fleet-wide, can we stop it, will it break anything"
  - "operator ruling 2026-07-23: stop the 4 self-hosted ones too — 'running for free doesn't mean we want them to run'"
  - "measured: GH Actions run counts 2026-07-17..23; workspace-manifest.json; repos/*/actions/runners"
---

# Stop the staging-branch workflow machinery (all 6)

## Evidence that staging is dead

| Signal                       | Measured 2026-07-23                                                     |
| ---------------------------- | ----------------------------------------------------------------------- |
| Last commit on `staging`     | **2026-06-27** in every repo checked                                    |
| `staging` vs LDR             | **600–967 commits behind**, `ahead_by=0` (UAC 967, IS 837, MTDS 786, …) |
| Open PRs targeting `staging` | **0** — full 24-repo sweep, not a sample                                |
| PM's own `staging` branch    | **does not exist**                                                      |
| `workspace-manifest.json`    | `staging_dormant_mode: true`, 24/25 repos `promotion_model: ldr_main`   |

## What still fires, and what it costs

| #   | Workflow                             | Scope    | Runs/wk | Trigger                  | runs-on               | Cost/mo                |
| --- | ------------------------------------ | -------- | ------- | ------------------------ | --------------------- | ---------------------- |
| 1   | `staging-backmerge-to-ldr`           | 24 repos | ~3,216  | hourly cron `10 * * * *` | `ubuntu-latest`       | **~$84**               |
| 2   | `staging-lock-check`                 | 24 repos | ~3,168  | `repository_dispatch`    | `ubuntu-latest`       | **~$82**               |
| 3   | `staging-to-main`                    | PM       | 241     | hourly cron + dispatch   | `[self-hosted, glue]` | $0 (+~$6 notify-slack) |
| 4   | `staging-conflict-ldr-main-fallback` | PM       | 142     | hourly cron `47 * * * *` | `[self-hosted, glue]` | $0                     |
| 5   | `reconcile-staging-versions`         | PM       | 137     | hourly cron `35 * * * *` | `[self-hosted, glue]` | $0                     |
| 6   | `ldr-to-staging-promote`             | PM       | 39      | `repository_dispatch`    | `[self-hosted, glue]` | $0                     |

`#1` and `#2` run **8–13 seconds** and bill a **full minute** each — the 1-minute-minimum tax is ~85–90% of their cost.

**Why #1/#2 cannot move to the planning VM**: all 8 runners are registered to `unified-trading-pm` **only** (measured:
PM `actions/runners` total=8; features-service / unified-api-contracts / market-tick-data-service / deployment-api each
**0**; `orgs/IggyIkenna/actions/runners` → **404**, personal account, no org pool). Flipping a fleet template's
`runs-on` would hang all 24 rendered copies on a runner that does not exist for them — this is exactly the **KEEP-T**
class in `github_actions_ci_cost_reduction_2026_07_15.md`.

## Will stopping it break anything? No

- **Re-entry is MANUAL.** The toggle is a git-tracked JSON field (`workspace-manifest.json` `promotion_model` /
  `staging_dormant_mode`); **nothing writes it programmatically** — every reference in `scripts/**` is a read. A
  breaking/major bump does **not** auto-route through staging: per `codex/08-workflows/ci-cd-flow.md:451` that gate
  moved to `ldr-to-main-promote-fleet.yml` (AST differ + `sit_validated_tree`), and `breaking_pending` is `[]`.
- **No live-path side effects.** `staging-conflict-ldr-main-fallback` skips PM + every `ldr_main` repo (= all 25) so it
  is structurally a no-op and is NOT the LDR→main safety net (that is `ldr-to-main-promote-fleet.yml`);
  `reconcile-staging-versions` cannot produce new values (its source is the frozen staging pyprojects — last write
  `c2d6b1e7b`, 2026-06-27); SIT is untouched (`full-workspace-sit.yml` owns its own `0 3 * * *` cron and the fleet
  promoter reads that run list directly, so the `staging-locked` fan-out is vestigial).
- **The one footgun, mitigated.** `staging-lock-check`'s `check-staging-lock` job posts a **required status check** on
  the `require-staging-lock-check` ruleset, present in **16 of 24** repos (absent in agent-orchestrator, e2e-testing,
  features-service, fund-administration-service, greeks-service, ml-service, unified-trading-api,
  unified-trading-system-ui). Deleting the workflow would hang any future staging PR forever on a check nothing reports.
  **Mitigation: disable ONLY the `repository_dispatch` trigger and keep the `pull_request` job intact** — the required
  check still reports the moment a staging PR is opened, and the job is
  `if: github.event_name == 'pull_request'`-guarded so it never ran on the dispatch path anyway.
- **`ldr-to-staging-promote`'s `tier-ab-green` dispatcher is LIVE** (`ci-status-update.yml:223`, the high-frequency
  status writer). We disable the **listener**, never the live writer — the dispatch simply becomes unsubscribed.

## Method — reversible by construction

Follow the precedent already set in `ldr-to-staging-promote.yml` (its cron was commented out 2026-06-28, not deleted):
**comment out the trigger with a dated note naming what to uncomment**. Never delete a workflow file, never hand-edit a
per-repo copy (edit the template + `rollout-workflow-templates.sh`).

**Default-branch gotcha**: a `schedule:` fires from the **default branch** (`main`), so these changes only take effect
once promoted to `main` — landing on LDR alone does not stop a cron.

## Resolution checklist

- [x] [INFRA] P2. Disable the hourly `schedule:` in `scripts/workflow-templates/staging-backmerge-to-ldr.yml` (keep
      `push:[staging]` + `workflow_dispatch`). — DONE `unified-trading-pm@a7b5cc27c`; YAML + `actionlint` clean,
      surviving triggers verified `['push', 'workflow_dispatch']`.
- [x] [INFRA] P2. Disable the `repository_dispatch:` trigger in `scripts/workflow-templates/staging-lock-check.yml`,
      keeping the `pull_request` job that posts the required check. — DONE `unified-trading-pm@a7b5cc27c`; surviving
      triggers verified `['pull_request']`, and `^  pull_request:` re-confirmed present in **all 24** rendered copies on
      `origin/live-defi-rollout` — the required-check footgun is closed by measurement, not merely by intent.
- [x] [INFRA] P2. Disable the `schedule:` in PM's `staging-to-main.yml`, `staging-conflict-ldr-main-fallback.yml`,
      `reconcile-staging-versions.yml`; disable the `repository_dispatch:` listener in `ldr-to-staging-promote.yml`. —
      DONE `unified-trading-pm@a7b5cc27c`. Each retains ≥1 live trigger (`workflow_dispatch`, plus
      `repository_dispatch: [staging-validated]` on staging-to-main) so a real staging promotion still drains.
- [x] [INFRA] P2. Roll the 2 templates out to all 24 repos (`rollout-workflow-templates.sh`) and ship each repo via its
      own `quickmerge.sh --agent --files`. — DONE, **24/24 verified by reading CONTENT from
      `origin/live-defi-rollout`**, not local state and not agent self-reports. SHAs: unified-api-contracts@9079f652 ·
      deployment-ui@9b6f8f09 · unified-trading-system-ui@d0a9ed91 · unified-trading-library@7ce9c068 ·
      agent-orchestrator@583800f8 · alerting-service@f1e8894d · batch-live-reconciliation-service@fcf7e5f9 ·
      client-reporting-api@a3e92279 · deployment-service@c1b8a3d5 · execution-service@b7516ba8 ·
      features-service@b88d0955 · fund-administration-service@01631495 · greeks-service@bf73930c ·
      ibkr-gateway-infra@9fdebfc1 · instruments-service@ea60a28e · market-data-processing-service@4b583382 ·
      market-tick-data-service@74938624 · ml-service@eed9fc9b · strategy-service@6c7a5673 ·
      trading-agent-service@e500abac · unified-trading-api@1f41dba4 · deployment-api@bcc125e9 (landed by a PEER slot
      concurrently — verified, not re-shipped) · e2e-testing@e4dae527 · system-integration-tests@1f86d524.
- [x] [VERIFY] P2. Confirm run volume drops to ~0 once the changes reach `main` (default-branch gotcha — a `schedule:`
      fires from the DEFAULT branch, so landing on LDR alone does NOT stop a cron). — **VERIFIED BY MEASUREMENT
      2026-07-23T09:04Z, not by the shipped diff.** Promote tracked to completion (1→8→15→19→22→**24/24 on `main`** at
      09:04Z; the run was deliberately watched on a climbing progress metric, not a fixed sleep). Then the actual
      question — did the crons stop? — measured fleet-wide on `staging-backmerge-to-ldr` across ALL 24 repos:

      | window                          | scheduled runs |
              | ------------------------------- | -------------- |
              | 06:00–08:00Z (2h, pre-promote)  | **47**         |
              | after 08:00Z (>1h, post-promote)| **0**          |

              Repos still firing: **NONE**. PM's own three crons likewise 0 after 08:00Z (`reconcile-staging-versions`,
              `staging-to-main`, `staging-conflict-ldr-main-fallback` — each had 1–2 runs in the prior window). Note this was
              only tickable AFTER the promote: the same check at 07:50Z correctly showed the crons still firing, which is why
              the box was held open through two earlier status reports rather than closed on the diff.

- [x] [DOC] P2. Add "re-enable the staging workflows" to the staging re-entry path so the reversibility guarantee is not
      half-true. — DONE: every disabled trigger carries an inline dated note naming exactly what to uncomment and the
      `workspace-manifest.json` flip that constitutes re-entry; § "Method — reversible by construction" is the index.
      Mirrored in `github_actions_ci_cost_reduction_2026_07_15.md` § Phase 6.
