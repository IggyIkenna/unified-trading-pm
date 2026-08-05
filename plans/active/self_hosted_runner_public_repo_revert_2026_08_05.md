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

- [x] 1. ✅ [INFRA] P0. **Mapped the exact revert mechanism — DONE 2026-08-05, resolved differently than assumed.**
      `rollout-workflow-templates.sh` byte-copies 11 templates (not 6) verbatim from `scripts/workflow-templates/` —
      only `quality-gates-v2.yml.tmpl`/`semver-agent.yml.tmpl` were allowlist-parameterized before this session; the
      other 9 (`main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`, `request-major-bump.yml`,
      `staging-backmerge-to-ldr.yml`, `staging-lock-check.yml`, `update-dependency-version.yml`,
      `version-registry-notify.yml`, `image-build-gate.yml` [no runs-on], `notify-slack.yml` [deliberately
      ubuntu-latest]) were hardcoded `[self-hosted, glue]` for EVERY repo regardless of visibility — no per-repo lever
      existed. **Fixed at the source**: added a `{{RUNS_ON}}` placeholder + `get_runs_on_value()` helper to
      `rollout-workflow-templates.sh` (same `self-hosted-qg-repos.txt` allowlist `get_qg_runner_labels()` already used),
      applied to all 8 runner-bearing templates — `unified-trading-pm@3240ec79e`. A remaining set of per-repo bespoke
      files (not fleet-templated at all: `uac-registry-sync.yml`/`uic-openapi-sync.yml`/`plan-alignment-agent.yml`/
      `publish-package.yml`/`canary-offline.yml`/`pr-watcher.yml`/`schema-health.yml`/`weekly-validation.yml`/
      `full-workspace-sit.yml`/`performance-test.yml`/`sit-plan-sync-agent.yml`/`smoke-test-gate.yml`/`ci.yml`/
      `deploy-uat-on-merge.yml`/`orphan-audit.yml`/`ui-quality-gates.yml`) were found self-hosted too (none are
      fleet-health watchdogs — all normal build/test/sync/deploy jobs) and reverted by direct per-repo edit, since no
      template owns them.
- [x] 2. ✅ [INFRA] P0. **Confirmed `hosted-baseline.sh` is PM-workflow-scoped only** — `MANIFEST.tsv`'s 56 entries are
      all PM's own workflow filenames (`REPO_ROOT` resolves relative to the script's own location, which only exists in
      PM's checkout). It does not cover any of the 17 target repos. Reverts for those instead went through
      `rollout-workflow-templates.sh`'s new parameterization (todo 1) or direct edit for bespoke files.
- **Unplanned but required fix, found via PM's own quality gates**: the `{{RUNS_ON}}` placeholder broke
  `detect_template_drift.py --workflows`'s byte-compare (it globs `*.yml` only, assuming flat templates are always
  byte-identical across the fleet — a template containing a placeholder can never match a rendered repo copy). Renaming
  the 8 templates to `.yml.tmpl` would have silently dropped `main-backmerge-to-ldr.yml`/ `staging-backmerge-to-ldr.yml`
  from `CRITICAL_PROMOTE_TEMPLATES`' missing-copy escalation (a real regression on the documented Tier-C runaway-promote
  guard, Gap 6) — fixed instead by detecting substitution by CONTENT (`b"{{RUNS_ON}}" in template_bytes`) rather than
  extension, preserving every other check. `unified-trading-pm@3240ec79e` (bundled with todo 1's fix); baseline
  re-written, ratcheted down 140 now-stale entries.
- [x] 3. ✅ [INFRA] P1. **`unified-api-contracts` reverted** — `unified-api-contracts@36de8ef7`, full QG green (464s),
      landed on LDR trunk.
- [x] 4. ✅ [INFRA] P1. **`unified-trading-library` reverted** — `unified-trading-library@2b83764f`, full QG green
      (209s), landed on LDR trunk. (Shipped 2nd — both `alerting-service`/others declare it + `unified-api-contracts` as
      path deps; quickmerge's pre-flight refuses a downstream ship while an upstream dep has uncommitted changes, so
      dependency order matters here, not just per-repo independence.)
- [ ] 5. [INFRA] P1. **Revert `alerting-service`** — all self-hosted workflows back to `ubuntu-latest`; local edit
      applied and verified content-clean, quickmerge IN FLIGHT (queued behind shared-host QG-token contention from other
      concurrent sessions on this host, not a failure). Verify a real green CI run post-land (cite run URL). Deregister
      its self-hosted runner (`gh api .../actions/runners` DELETE + `systemctl stop`+`disable` the exact unit — never
      the buggy `teardown --POOL_TAG` path, per the documented incident in
      `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`).
- [ ] 6. [INFRA] P1. **Revert `batch-live-reconciliation-service`** — local edit applied, quickmerge IN FLIGHT (same
      queue). Verify + deregister, cite evidence.
- [ ] 7. [INFRA] P1. **Revert `client-reporting-api`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 8. [INFRA] P1. **Revert `deployment-api`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 9. [INFRA] P1. **Revert `deployment-service`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 10. [INFRA] P1. **Revert `deployment-ui`** — every self-hosted workflow reverted locally EXCEPT
      `ui-quality-gates-v2.yml` (already correctly `ubuntu-latest`, left untouched); not yet shipped. Verify +
      deregister, cite evidence.
- [ ] 11. [INFRA] P1. **Revert `fund-administration-service`** — local edit applied, not yet shipped. Verify +
      deregister, cite evidence.
- [ ] 12. [INFRA] P1. **Revert `greeks-service`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 13. [INFRA] P1. **Revert `ibkr-gateway-infra`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 14. [INFRA] P1. **Revert `instruments-service`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 15. [INFRA] P1. **Revert `market-data-processing-service`** — local edit applied, not yet shipped. Verify +
      deregister, cite evidence.
- [ ] 16. [INFRA] P1. **Revert `system-integration-tests`** — local edit applied, not yet shipped. Verify + deregister,
      cite evidence.
- [ ] 17. [INFRA] P1. **Revert `trading-agent-service`** — local edit applied, not yet shipped. Verify + deregister,
      cite evidence.
- [ ] 18. [INFRA] P1. **Revert `unified-trading-api`** — local edit applied, not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 19. [INFRA] P1. **Revert `unified-trading-system-ui`** — every self-hosted workflow reverted locally EXCEPT
      `ui-quality-gates-v2.yml` (already correctly `ubuntu-latest`); not yet shipped. Verify + deregister, cite
      evidence.
- [ ] 20. [INFRA] P2. **Re-measure GitHub Actions billing for the 17 reverted repos** (should read $0/unmetered,
      confirming the public-repo-unmetered premise held in practice) and the self-hosted VM's steady-state load average
      before vs. after (not a spot-check — matches `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s own
      still-open "longer-window measurement" gap). Update that plan's issue doc
      (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`) with the dated result rather than duplicating
      it here.

## Progress Log

- **2026-08-05**: Plan authored following an interactive investigation (live `gh repo list` visibility check
  cross-referenced against `self-hosted-qg-repos.txt`, plus a full-fleet `runs-on:` sweep). Operator confirmed all 17
  identified repos are intentionally public and asked for this to be tracked as a human/local plan (not AO-dispatched —
  each revert needs live-judgment verification against an unconfirmed mechanism landscape, same class of reasoning the
  original migration plan used).
- **2026-08-05 (execution)**: Operator said "please do execute." Todos 1-2 resolved the mechanism landscape — found the
  9 non-quality-gates/semver templates were unconditionally hardcoded self-hosted with NO per-repo lever at all (bigger
  gap than assumed). Fixed at the template-mechanism level (not per-repo hacks) so the allowlist becomes the single
  source of truth for runner placement fleet-wide, matching the existing quality-gates-v2/semver-agent pattern —
  `unified-trading-pm@3240ec79e`. Caught and fixed a real regression risk along the way: the fix's own placeholder broke
  `detect_template_drift.py`'s byte-compare gate; content-based (not extension-based) substitution detection fixes it
  without disabling the Tier-C runaway-promote missing-copy guard. Applied the runs-on revert locally across all 17
  target repos (verified zero remaining `self-hosted` references fleet-wide via direct grep sweep before shipping
  anything) plus a broader-than-expected set of bespoke non-templated self-hosted files discovered along the way.
  Shipped `unified-api-contracts` and `unified-trading-library` first (dependency order — quickmerge's pre-flight
  refuses a downstream repo ship while an upstream path-dependency has uncommitted changes; several of the 17 declare
  these two as deps). `alerting-service`/`batch-live-reconciliation-service` are queued mid-ship behind other concurrent
  sessions' QG token usage on this shared host (`qg-governor` 2-token cap) — not a failure, just contention outside this
  session's control. Remaining 13 repos have their local revert applied and verified but are not yet shipped. **Next**:
  land the 2 in-flight ships, then continue shipping the remaining 13 in dependency-safe pairs, verify a real green CI
  run per repo, then deregister each repo's old self-hosted runner.
