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
- [x] 5. ✅ [INFRA] P1. **`alerting-service` reverted** — `alerting-service@6ecb3534`, full QG green (713s), landed.
- [x] 6. ✅ [INFRA] P1. **`batch-live-reconciliation-service` reverted** — `batch-live-reconciliation-service@449ec027`,
      full QG green (1070s), landed.
- [x] 7. ✅ [INFRA] P1. **`client-reporting-api` reverted** — `client-reporting-api@154ab790`, full QG green (946s),
      landed.
- [ ] 8. [INFRA] P1. **`deployment-api` — STILL BLOCKED, not yet shipped.** Local revert applied + verified
      content-clean. Twice failed pre-flight because its path-dependency `deployment-service` had uncommitted changes
      from ANOTHER concurrent session on this shared host (`scripts/vm/launch-canonical-migration-vm.sh`) — not mine to
      touch or commit. **Re-checked at session end: `deployment-service` is now clean** (the other session committed its
      own file), so this todo is very likely unblocked now — retry
      `bash scripts/quickmerge.sh "fix(ci): revert to     GitHub-hosted runners (public repo, GH Actions unmetered)" --agent --files ".github/workflows/main-backmerge-to-ldr.yml     .github/workflows/major-bump-issue-handler.yml .github/workflows/quality-gates-v2.yml     .github/workflows/request-major-bump.yml .github/workflows/semver-agent.yml     .github/workflows/staging-backmerge-to-ldr.yml .github/workflows/staging-lock-check.yml     .github/workflows/update-dependency-version.yml .github/workflows/version-registry-notify.yml"`
      from `deployment-api/` as the very next action — not attempted this session due to context-limit cutoff, not a
      real blocker.
- [x] 9. ✅ [INFRA] P1. **`deployment-service` reverted** — `deployment-service@cb814e26`, full QG green (512s after one
      300s-wall-clock-SLA retry caused by governor queue-wait, not a real failure), landed.
- [x] 10. ✅ [INFRA] P1. **`deployment-ui` reverted** — `deployment-ui@8cc6f863`, every self-hosted workflow reverted
      EXCEPT `ui-quality-gates-v2.yml` (already correctly `ubuntu-latest`, left untouched); full QG green (89s), landed.
- [x] 11. ✅ [INFRA] P1. **`fund-administration-service` reverted** — `fund-administration-service@5701520a`, full QG
      green (470s), landed.
- [x] 12. ✅ [INFRA] P1. **`greeks-service` reverted** — `greeks-service@f35dc273`, full QG green (882s), landed.
- [x] 13. ✅ [INFRA] P1. **`ibkr-gateway-infra` reverted** — `ibkr-gateway-infra@64ebd8d0`, full QG green (123s),
      landed.
- [ ] 14. [INFRA] P1. **`instruments-service` — BLOCKED, not mine to fix, not yet shipped.** Local revert applied +
      verified content-clean. Quickmerge's re-gate hit a genuine, PRE-EXISTING test failure unrelated to this CI-only
      change:
      `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[prediction]`
      — golden fixture expects 8 KALSHI/POLYMARKET `prediction_market` entries, actual has 0. Root cause: a DIFFERENT
      concurrent session's `unified-api-contracts@72d11208` commit ("refactor(uac): delete dead code —
      MVP_VENUE_DATA_TYPES, DEFI_VENUE_AXIS_OVERRIDES, Prediction inert matrix row") deleted the matrix row that
      populated those entries — landed on this branch before my ship attempt. This is a real product/domain question
      (was that deletion correct, does the golden fixture need regenerating) needing the owning agent's or operator's
      judgment — **not** something to fix as part of a CI-runner-placement revert. Retry once that's resolved elsewhere;
      until then this todo (and #16, which depends on it) stay blocked.
- [x] 15. ✅ [INFRA] P1. **`market-data-processing-service` reverted** — `market-data-processing-service@b039ec2f`, full
      QG green (211s), landed.
- [ ] 16. [INFRA] P1. **`system-integration-tests` — BLOCKED transitively, not yet shipped.** Local revert applied +
      verified content-clean. Pre-flight failure: depends on both `deployment-api` (#8) and `instruments-service` (#14)
      as path dependencies — blocked on both clearing first, not a defect of its own. Retry after #8 and #14 land.
- [x] 17. ✅ [INFRA] P1. **`trading-agent-service` reverted** — `trading-agent-service@fb508071`, full QG green (95s),
      landed.
- [x] 18. ✅ [INFRA] P1. **`unified-trading-api` reverted** — `unified-trading-api@7186c8e9`, full QG green (121s),
      landed.
- [x] 19. ✅ [INFRA] P1. **`unified-trading-system-ui` reverted** — `unified-trading-system-ui@6441e477`, every
      self-hosted workflow reverted EXCEPT `ui-quality-gates-v2.yml` (already correctly `ubuntu-latest`); full QG green
      (254s), landed.
- [ ] 20. [INFRA] P2. **Re-measure GitHub Actions billing for the 17 reverted repos** (should read $0/unmetered,
      confirming the public-repo-unmetered premise held in practice) and the self-hosted VM's steady-state load average
      before vs. after (not a spot-check — matches `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s own
      still-open "longer-window measurement" gap). Update that plan's issue doc
      (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`) with the dated result rather than duplicating
      it here.
- [ ] 21. [INFRA] P1. **Deregister the old self-hosted runners for the 14 landed repos** (not started this session —
      needs SSM access to the CI runner VM per `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s documented
      method: `gh api repos/IggyIkenna/<repo>/actions/runners` DELETE + `systemctl stop`+`disable` the exact unit —
      never the buggy `teardown --POOL_TAG` path, per that plan's own documented incident). Do the 3 remaining repos
      (#8, #14, #16) in the SAME pass once they land, rather than two separate deregistration sweeps.
- [ ] 22. [INFRA] P2. **Investigate `unified-trading-library`'s promotion-PR backlog** — found while spot-checking live
      CI: 5 unmerged `promote/unified-trading-library/*` PRs stacked up (#746–#750) against `main`, and the newest
      (#750, this session's `@2b83764f` revert commit) shows its `quality-gates-v2` promotion-PR run failing with
      GitHub's generic "likely failed because of a workflow file issue" and zero scheduled jobs. **Ruled out as caused
      by this session's change**: fetched the exact file content at that SHA directly from GitHub and validated it with
      a real YAML parser (`python3 -c "import yaml; yaml.safe_load(...)"`) — parses cleanly, and the
      `self_hosted_runner_labels: ""` pattern is the SAME one already proven working this session on `deployment-ui`/
      `unified-trading-system-ui`'s promotion PRs (both real `success`). The 5-PR backlog predates this session's first
      commit to the repo, so this looks like a pre-existing promotion-pipeline issue specific to
      `unified-trading-library` — needs its own investigation, separate from this plan's scope.

## Progress Log

- **2026-08-05**: Plan authored following an interactive investigation (live `gh repo list` visibility check
  cross-referenced against `self-hosted-qg-repos.txt`, plus a full-fleet `runs-on:` sweep). Operator confirmed all 17
  identified repos are intentionally public and asked for this to be tracked as a human/local plan (not AO-dispatched —
  each revert needs live-judgment verification against an unconfirmed mechanism landscape, same class of reasoning the
  original migration plan used).
- **2026-08-05 (execution, session end — context-limit checkpoint)**: Operator said "please do execute," then "keep
  going" through a long shipping run. **Final state: 14 of 17 repos landed** (`unified-api-contracts`,
  `unified-trading-library`, `alerting-service`, `batch-live-reconciliation-service`, `client-reporting-api`,
  `fund-administration-service`, `deployment-service`, `greeks-service`, `ibkr-gateway-infra`,
  `market-data-processing-service`, `trading-agent-service`, `unified-trading-api`, `deployment-ui`,
  `unified-trading-system-ui` — commit SHAs in todos 3-4, 5-7, 9-13, 15, 17-19 above), each verified via a real green
  local `quality-gates.sh` run before shipping (identical to what CI runs). **3 remain blocked, all for reasons outside
  this session's scope** (todos 8, 14, 16) — none are a defect in the revert itself.

  **Root-cause fix, not a per-repo hack**: found the 9 non-quality-gates/semver fleet templates
  (`main-backmerge-to-ldr.yml` etc.) were unconditionally hardcoded self-hosted with NO per-repo lever at all — bigger
  gap than the plan assumed at authoring time. Fixed at the `rollout-workflow-templates.sh` template-mechanism level
  (new `{{RUNS_ON}}` placeholder + `get_runs_on_value()`, reusing the SAME `self-hosted-qg-repos.txt` allowlist
  `get_qg_runner_labels()` already governs) so the allowlist is the single source of truth fleet-wide going forward —
  `unified-trading-pm@3240ec79e`. This ALSO fixes future rollouts for the 8 still-private repos with zero behavior
  change for them (verified: their rendered output is byte-identical before/after, since they stay on the allowlist).

  **Real regression caught and fixed before it shipped**: the `{{RUNS_ON}}` placeholder broke
  `detect_template_drift.py --workflows`'s byte-compare gate (a template containing a placeholder can never byte-match a
  rendered copy). The naive fix — renaming the 8 templates to `.yml.tmpl` — would have silently dropped
  `main-backmerge-to-ldr.yml`/`staging-backmerge-to-ldr.yml` from `CRITICAL_PROMOTE_TEMPLATES`'s missing-copy
  escalation, a real regression on the documented Tier-C runaway-promote guard (Gap 6). Fixed instead by detecting
  substitution by CONTENT (`b"{{RUNS_ON}}" in template_bytes`) rather than extension, preserving every other check —
  bundled into the same `unified-trading-pm@3240ec79e` commit; baseline re-written, ratcheting down 140 now-stale
  entries as a side benefit.

  **Lessons for whoever continues this**:
  1. **Dependency order matters for shipping, not just for content correctness.** `unified-api-contracts` and
     `unified-trading-library` had to ship FIRST — quickmerge's pre-flight refuses a downstream repo's ship while ANY
     upstream path-dependency has uncommitted changes, and most of the 17 repos declare one or both as deps. Ship
     roots-of-the-DAG first, always.
  2. **A blocked pre-flight from an unrelated dirty file in a shared dependency is not your bug to fix.** Hit this twice
     (`deployment-service`'s `scripts/vm/launch-canonical-migration-vm.sh` blocked `deployment-api` twice) — the right
     move is to leave it, not touch/commit someone else's WIP, and retry later. It cleared on its own by session end.
  3. **A downstream repo's pre-existing, unrelated test failure blocks a CI-only revert just as hard as a real
     conflict.** `instruments-service`'s golden-fixture failure has nothing to do with runner placement, but
     quickmerge's re-gate still blocks on it. Don't try to fix unrelated failures to unblock your own change — flag and
     defer.
  4. **This shared host's `qg-governor` token pool (cap 2) is shared across ALL concurrent sessions on the machine, not
     just this session's own background tasks.** Queue waits of 300-950s were routine, and one repo
     (`deployment-service`, first attempt) hit a hard `300s wall-clock SLA` failure purely from governor queue-wait, not
     from the change itself — a bare retry succeeded once a slot freed up. Don't mistake governor contention for a real
     failure; check the actual QG output before concluding the change is broken.
  5. **Verify with the ACTUAL rendered file content when a live CI run looks wrong, not just re-reading your own diff.**
     The `unified-trading-library` promotion-PR anomaly (todo 22) looked alarming (zero jobs scheduled) until fetching
     the exact file at that exact SHA from GitHub and validating it with a real YAML parser showed it was fine — the
     real cause is a separate, pre-existing 5-PR promotion backlog for that repo.
  6. **Mid-checkpoint, a quickmerge retry's failed `git pull` step can still silently fast-forward HEAD even though the
     overall command exits non-zero** — hit this directly: a `PRECOMMIT_WORKING_TREE_CONFLICT` failure left HEAD
     advanced by the incoming commit while the working tree (and this file's own edits) reverted to match it, wiping an
     just-written edit that had never been committed. Recovered by re-applying the same edit from the conversation's own
     record rather than git archaeology. **Takeaway**: after ANY quickmerge failure, re-check `git log -1 HEAD` and the
     actual file content before assuming "failed" means "nothing changed."

  **Next session should**: (1) retry `deployment-api` first (todo 8 — very likely unblocked now, its blocker cleared),
  (2) check whether `instruments-service`'s golden-fixture issue has been resolved elsewhere and retry (todo 14), (3)
  retry `system-integration-tests` once both clear (todo 16), (4) deregister old self-hosted runners for all 17 in one
  pass (todo 21), (5) investigate the `unified-trading-library` promotion backlog separately (todo 22, not blocking this
  plan), (6) todo 20's billing/load re-measurement once a few days have passed.
