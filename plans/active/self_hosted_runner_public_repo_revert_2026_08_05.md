---
doc_type: plan
title: Revert self-hosted CI runners to GitHub-hosted for confirmed-public repos
summary: >-
  17 of the 25-repo self-hosted CI fleet are PUBLIC GitHub repos, confirmed intentional by the operator 2026-08-05 —
  GitHub Actions is unmetered on GitHub-hosted runners for public repos, so their self-hosted CI can revert to
  ubuntu-latest at zero billing cost while directly relieving the shared self-hosted VM's documented capacity
  contention. Only 8 fleet repos are private and genuinely need to stay self-hosted.
status: active
nature: process
asset_group: [ci, infrastructure]
stage: [meta]
repos:
  [
    unified-trading-pm,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
    market-data-processing-service,
    system-integration-tests,
    trading-agent-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [ci-cd, cost, self-hosted-runners, github-actions, capacity, public-repos]
related:
  [
    /plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md,
    /plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-05
last_updated: 2026-08-05
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md,
    /plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    scripts/workflow-templates/self-hosted-qg-repos.txt,
    scripts/self-hosted-runners/hosted-baseline.sh,
    scripts/workflow-templates/rollout-workflow-templates.sh,
    scripts/propagation/rollout-agent-workflows.sh,
  ]
source:
  [
    "operator, interactive session, 2026-08-05 — asked what self-hosted workflows are on public repos and could move
    back to GitHub-hosted since CI is free for public repos; confirmed all 17 identified repos are intentionally public
    and asked for this to be tracked",
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Revert self-hosted CI runners to GitHub-hosted for confirmed-public repos

## Why this plan exists

Investigating "what's left to self-host" turned up the opposite, higher-value question: **none of the self-hosted-runner
planning docs (the ADR, `pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md`,
`github_actions_operator_gated_followups_2026_07_17.md`, `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`,
`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`) ever checked repo VISIBILITY.** The entire self-hosted migration
was billing-motivated (operator: "we spend 1k monthly on gh plus... 5k gh ci spend alone"), but GitHub Actions on
GitHub-hosted runners is unmetered for PUBLIC repos regardless of minutes used — only PRIVATE repos consume billed
minutes. Cross-referencing live repo visibility (`gh repo list IggyIkenna`) against
`scripts/workflow-templates/self-hosted-qg-repos.txt` (2026-08-05):

**17 self-hosted repos are PUBLIC** (in scope for this plan): alerting-service, batch-live-reconciliation-service,
client-reporting-api, deployment-api, deployment-service, deployment-ui, fund-administration-service, greeks-service,
ibkr-gateway-infra, instruments-service, market-data-processing-service, system-integration-tests,
trading-agent-service, unified-api-contracts, unified-trading-api, unified-trading-library, unified-trading-system-ui.
**Operator-confirmed 2026-08-05: all 17 are intentionally public**, not an oversight.

**Only 8 self-hosted repos are PRIVATE** (out of scope — genuinely need self-hosting for billing reasons):
agent-orchestrator, unified-trading-pm, strategy-service, e2e-testing, features-service, market-tick-data-service,
execution-service, ml-service.

Reverting the 17 public repos' CI to `ubuntu-latest`:

- Costs **$0** in GitHub Actions billing (public-repo GH-hosted minutes are unmetered).
- Directly relieves load on the shared self-hosted CI VM — the exact, still-open contention problem
  `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` has been fighting (load average 25-65 on a 16-vCPU box,
  hours-long promotion-gate stalls). Removing 17 of 25 repos' worth of runner load is a bigger lever than anything in
  that plan's own scope, and is complementary to it (not gated on it — no `depends_on`).
- Is strictly SAFER: self-hosted runners on a public repo are a known GitHub anti-pattern if the repo ever takes outside
  pull requests (a PR author can run code on your infrastructure) — reverting to GitHub-hosted removes that exposure
  regardless of whether it's currently exploitable here.

## Findings from the adjacent "remaining self-hosting gaps" investigation (2026-08-05, folded in, no separate plan)

The operator also asked to "fix" a table of workflows still on `ubuntu-latest` that looked like self-hosting gaps.
Investigated each one; **none needed a self-hosting fix**:

- **`deployment-ui` / `unified-trading-system-ui`'s `ui-quality-gates-v2.yml`** — NOT a gap. Both repos are in the
  17-public-repo list above; this file is already correctly on `ubuntu-latest` (free), and this plan's own scope will
  revert the REST of these two repos' workflows (backmerge, semver, version-bump, `quality-gates-v2.yml`) to match it,
  not the other way around.
- **`unified-trading-pm`'s ~15 "unassessed" `ubuntu-latest` workflows** — re-checked individually (PM is private, so
  this direction is a real question). Resolved to zero actionable items:
  - **3 were grep false positives** (`cassette-drift-check.yml`, `readiness-verifier.yml`,
    `removed-symbols-workspace-sweep.yml`) — already self-hosted; the earlier substring scan matched the literal string
    "ubuntu-latest" inside a revert-instructions COMMENT, not a real `runs-on:` line.
  - **7 are fleet-health watchdogs that must stay GitHub-hosted**, same resilience reasoning as `ci-health.yml` (need to
    detect an outage of the thing they'd be running on if self-hosted): `cloud-build-failure-watcher.yml`,
    `glue-pool-starvation-monitor.yml`, `ldr-ci-monitor.yml`, `overnight-dead-man-switch.yml`,
    `promote-fleet-startup-failure-monitor.yml`, `sit-gate-stuck-detector.yml`, `stale-build-watcher.yml`.
  - **5 are genuinely negligible run-count** (verified via each file's actual trigger, not assumed):
    `major-bump-issue-handler.yml` (issue-comment-triggered, human-in-the-loop, rare), `publish-package.yml`
    (repository_dispatch on an actual package release, rare), `request-major-bump.yml` (workflow_dispatch only, manual),
    `build-smoke-all-repos.yml` (weekly cron + manual), `semver-agent.yml` (PM is Option-B/no staging branch, so this
    workflow's trigger is explicitly documented as vestigial for PM — near-zero real runs).
  - This confirms rather than contradicts `ci_pipeline_speed_and_cost_redesign_2026_08_05.md`'s own conclusion that PM's
    cost was ~96%+ explained by the now-fixed `qg-slices` misconfiguration, with the remainder being "diminishing safety
    margin" territory.
- **`strategy-service`'s `agent-audit.yml`** — private repo, but `workflow_dispatch`-only (manual), negligible. Not
  worth touching.
- **`deployment-service`'s `sync-vm-scripts-to-gcs.yml`** — moot: `deployment-service` is itself in the 17-repo public
  list above, so this is free either way regardless of runner choice.

**Net effect: there is nothing to fix from that table beyond what this plan already covers.**

## Mechanism landscape (confirm before touching any file — do not assume)

Reverting is NOT just flipping `runs-on:` — `hosted-baseline.sh`'s own design (three cases: never-flipped /
mechanically-flipped / flipped-with-logic) exists because some flips also changed real steps (e.g.
`cassette-drift-check.yml` deleted its `Set up Python` step because the glue image ships Python pre-installed;
`ubuntu-latest` still needs it). This workspace has a documented history of "2 separate live incidents from touching
this exact runner infrastructure" — treat every revert as needing the same care as the original migration, not a blanket
find-replace. Known landscape so far, NOT yet fully confirmed:

- `scripts/self-hosted-runners/hosted-baseline.sh` (`snapshot`/`verify`/`diff`/`restore`) is PM's own tool and operates
  on PM's OWN `.github/workflows/` (its `REPO_ROOT` resolves relative to the script's own location, which only exists in
  PM's checkout — confirmed absent from all 17 target repos). **Unconfirmed**: whether its snapshot directory
  (`scripts/self-hosted-runners/hosted-baseline/`, which already lists files like `agent-audit.yml`,
  `branch-health.yml`, `cascade-qg-ordering.yml` etc. — i.e. more than just PM's own workflow set) actually covers any
  of the 17 target repos' rendered copies, or is PM-workflow-scoped only.
- `scripts/workflow-templates/rollout-workflow-templates.sh` + `scripts/workflow-templates/self-hosted-qg-repos.txt` is
  the confirmed mechanism for exactly 6 templated files per repo: `request-major-bump.yml`,
  `major-bump-issue-handler.yml`, `staging-lock-check.yml`, `update-dependency-version.yml`, `quality-gates-v2.yml`
  (from `.tmpl`), `semver-agent.yml` (from `.tmpl`) — removing a repo from the allowlist and re-running the rollout
  should regenerate these on `ubuntu-latest`.
- `scripts/propagation/rollout-agent-workflows.sh` covers only `agent-audit.yml` + `plan-alignment-agent.yml` — NOT the
  backmerge/staging/version-registry files.
- Several self-hosted files per repo are NOT covered by either script above (`main-backmerge-to-ldr.yml`,
  `staging-backmerge-to-ldr.yml`, `version-registry-notify.yml`, `image-build-gate.yml`, and UI-specific files like
  `ci.yml`/`deploy-uat-on-merge.yml`/`orphan-audit.yml`/`uac-registry-sync.yml`/`uic-openapi-sync.yml`) — the rollout
  mechanism for these (a third script? hand-maintained per-repo?) is UNCONFIRMED. Todo 1 below resolves this before any
  file is touched.
- **KEEP-T example already found**: `staging-backmerge-to-ldr.yml` carries a comment warning that naively flipping
  `runs-on:` risks "hang[ing] all 24 rendered copies" (a stale pre-runner-pool-rollout assumption, but the file is
  `hosted-baseline.sh`'s "flipped, with logic" class regardless) — its schedule trigger is already commented out
  (staging frozen since 2026-06-27, near-zero real runs), so it is low-risk either way, but revert it using the same
  "verify hosted logic, not just runs-on" discipline as everything else, not a blind edit.

## Todos

- [ ] [INFRA] P0. **Map the exact revert mechanism per workflow file** across the 17 public repos — for each distinct
      self-hosted workflow filename found, state whether it's covered by `rollout-workflow-templates.sh` (→ remove from
      `self-hosted-qg-repos.txt` + re-run), a different rollout script (name it), or hand-maintained per-repo (→ needs a
      `hosted-baseline.sh`-style per-file hosted-form derivation). Done-when: a table exists (in this doc's Progress
      Log) covering every self-hosted filename seen across the 17 repos with its confirmed mechanism — no revert todo
      below should proceed against an unconfirmed mechanism.
- [ ] [INFRA] P0. **Confirm `hosted-baseline.sh`'s snapshot scope** — read `MANIFEST.tsv` and check whether any entries
      correspond to a target repo other than `unified-trading-pm`, or whether the tool is genuinely PM-workflow-scoped
      only. Done-when: stated definitively, feeding directly into todo 1's mechanism map.
- [ ] [INFRA] P1. **Revert `alerting-service`** — all self-hosted workflows back to `ubuntu-latest` per the confirmed
      mechanism (todo 1); remove from `self-hosted-qg-repos.txt` if templated. Verify a real green CI run post-revert
      (cite run URL). Deregister its self-hosted runner (`gh api .../actions/runners` DELETE +
      `systemctl stop`+`disable` the exact unit — never the buggy `teardown --POOL_TAG` path, per the documented
      incident in `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`).
- [ ] [INFRA] P1. **Revert `batch-live-reconciliation-service`** — same procedure as above. Verify + deregister, cite
      evidence.
- [ ] [INFRA] P1. **Revert `client-reporting-api`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `deployment-api`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `deployment-service`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `deployment-ui`** — every self-hosted workflow EXCEPT `ui-quality-gates-v2.yml` (already
      correctly `ubuntu-latest`, leave untouched). Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `fund-administration-service`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `greeks-service`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `ibkr-gateway-infra`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `instruments-service`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `market-data-processing-service`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `system-integration-tests`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `trading-agent-service`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `unified-api-contracts`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `unified-trading-api`** — same procedure. Verify + deregister, cite evidence.
- [ ] [INFRA] P1. **Revert `unified-trading-library`** — same procedure; note this repo cycled through the self-hosted
      starvation revert/re-add loop twice already for unrelated (contention, not billing) reasons per
      `self-hosted-qg-repos.txt`'s own header — a revert here is now for a different, permanent reason (public billing)
      and should not be treated as a 3rd cycle of the same flaky-recurrence pattern.
- [ ] [INFRA] P1. **Revert `unified-trading-system-ui`** — every self-hosted workflow EXCEPT `ui-quality-gates-v2.yml`
      (already correctly `ubuntu-latest`, leave untouched). Verify + deregister, cite evidence.
- [ ] [INFRA] P2. **Re-measure GitHub Actions billing for the 17 reverted repos** (should read $0/unmetered, confirming
      the public-repo-unmetered premise held in practice) and the self-hosted VM's steady-state load average before vs.
      after (not a spot-check — matches `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s own still-open
      "longer-window measurement" gap). Update that plan's issue doc
      (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`) with the dated result rather than duplicating
      it here.

## Progress Log

- **2026-08-05**: Plan authored following an interactive investigation (live `gh repo list` visibility check
  cross-referenced against `self-hosted-qg-repos.txt`, plus a full-fleet `runs-on:` sweep). Operator confirmed all 17
  identified repos are intentionally public and asked for this to be tracked as a human/local plan (not AO-dispatched —
  each revert needs live-judgment verification against an unconfirmed mechanism landscape, same class of reasoning the
  original migration plan used). No files touched yet — todos 1-2 (mechanism confirmation) must land before any repo's
  revert proceeds.
