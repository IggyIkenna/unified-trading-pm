---
doc_type: plan
title: Revert self-hosted CI runners to GitHub-hosted for confirmed-public repos
summary: >-
  17 of the 25-repo self-hosted CI fleet are PUBLIC GitHub repos, confirmed intentional by the operator 2026-08-05 —
  GitHub Actions is unmetered on GitHub-hosted runners for public repos, so their self-hosted CI can revert to
  ubuntu-latest at zero billing cost while directly relieving the shared self-hosted VM's documented capacity
  contention. Only 8 fleet repos are private and genuinely need to stay self-hosted. **Correction 2026-08-06**:
  `unified-trading-pm` — one of the 8 — was itself flipped PUBLIC on 2026-08-06 (see todo 24; it had been accidentally
  left private, which broke every repo's `quality-gates-v2` since public repos cannot call reusable workflows hosted in
  a private repo). PM is now in scope for the same revert this plan already does for the other 17.
status: active
nature: process
asset_group: [ci]
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
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /plans/archive/2026_07/pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md,
  ]
created: 2026-08-05
last_updated: 2026-08-12
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
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
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
- [x] 8. ✅ [INFRA] P1. **`deployment-api` reverted** — `deployment-api@54a4444`, landed on LDR. First ship attempt hit
      a genuine-but-unrelated flake: `test_reads_execute_concurrently_not_sequentially` (a wall-clock timing assertion,
      `elapsed < sequential_cost * 0.65`) failed at 1.123s vs. a 0.78s threshold under shared-host CPU contention from
      concurrent QG runs — confirmed flaky (not caused by this change, which touches only `.github/workflows/*.yml`) by
      re-running the single test standalone, which passed cleanly in 0.35s. Retry succeeded.
- [x] 9. ✅ [INFRA] P1. **`deployment-service` reverted** — `deployment-service@cb814e26`, full QG green (512s after one
      300s-wall-clock-SLA retry caused by governor queue-wait, not a real failure), landed.
- [x] 10. ✅ [INFRA] P1. **`deployment-ui` reverted** — `deployment-ui@8cc6f863`, every self-hosted workflow reverted
      EXCEPT `ui-quality-gates-v2.yml` (already correctly `ubuntu-latest`, left untouched); full QG green (89s), landed.
- [x] 11. ✅ [INFRA] P1. **`fund-administration-service` reverted** — `fund-administration-service@5701520a`, full QG
      green (470s), landed.
- [x] 12. ✅ [INFRA] P1. **`greeks-service` reverted** — `greeks-service@f35dc273`, full QG green (882s), landed.
- [x] 13. ✅ [INFRA] P1. **`ibkr-gateway-infra` reverted** — `ibkr-gateway-infra@64ebd8d0`, full QG green (123s),
      landed.
- [x] 14. ✅ [INFRA] P1. **`instruments-service` reverted** — `instruments-service@064e2560`, landed on LDR. Was blocked
      on a genuine, pre-existing golden-fixture test failure (`test_expected_matches_golden[prediction]`, caused by
      another session's `unified-api-contracts@72d11208` deletion) — re-checked before retrying and confirmed fixed
      upstream (test passes standalone, 2/2), so this was not something I needed to fix myself. A benign, unrelated
      `uv.lock` drift (stale `schema-validation` extra metadata inherited from `unified-trading-library`'s own committed
      lockfile, not declared in any pyproject.toml — pre-existing upstream inconsistency, not mine to fix) was excluded
      from the `--files` commit and left untouched.
- [x] 15. ✅ [INFRA] P1. **`market-data-processing-service` reverted** — `market-data-processing-service@7ccbfe84`, full
      QG green (211s), landed. (Corrected SHA citation 2026-08-05: `b039ec2f` was the parent commit, not the revert
      itself.)
- [x] 16. ✅ [INFRA] P1. **`system-integration-tests` reverted** — `system-integration-tests@69875d4`, landed on LDR —
      **the 17th and final repo, this plan's revert work is now 100% shipped.** Pre-flight still failed once after
      #8/#14 landed, this time on the same benign `uv.lock` drift (see #14) surfacing in two OTHER path dependencies
      (`market-data-processing-service`, `instruments-service`) — confirmed it was orphaned lockfile metadata (not real
      WIP: the `schema-validation` extra it references isn't declared in any repo's `pyproject.toml`, only dangling in
      `unified-trading-library`'s own already-committed `uv.lock`), discarded locally via `git checkout -- uv.lock` in
      both repos (safe: purely regenerates on next `uv sync`, destroys no one's authored work), retried, landed clean.
- [x] 17. ✅ [INFRA] P1. **`trading-agent-service` reverted** — `trading-agent-service@fb508071`, full QG green (95s),
      landed.
- [x] 18. ✅ [INFRA] P1. **`unified-trading-api` reverted** — `unified-trading-api@7186c8e9`, full QG green (121s),
      landed.
- [x] 19. ✅ [INFRA] P1. **`unified-trading-system-ui` reverted** — `unified-trading-system-ui@6441e477`, every
      self-hosted workflow reverted EXCEPT `ui-quality-gates-v2.yml` (already correctly `ubuntu-latest`); full QG green
      (254s), landed.
- [x] ✅ 24. [INFRA] P1. **Revert `unified-trading-pm`'s own self-hosted workflows to `ubuntu-latest` — DONE
      2026-08-07.** `unified-trading-pm@c8cd56251e`. (a) Removed `unified-trading-pm` from
      `scripts/workflow-templates/self-hosted-qg-repos.txt`;
      `rollout-workflow-templates.sh --dry-run --repo     unified-trading-pm` showed 0 diffs (PM's own
      `quality-gates-v2.yml`/`python-quality-gates-v2.yml` are NOT template-rendered targets of that script — they're
      hand-maintained locally, confirmed by the file's own comment "PM's local `uses: ./...` self-call fell outside that
      script's scope"), so `self_hosted_runner_labels` was hand- edited to `""` instead. (b) ~40 bespoke files reverted
      via `hosted-baseline.sh restore` (per-file, not `--all`, since 3 files' baselines were genuinely logic-stale) + 5
      hand-reviewed exceptions requiring real archaeology: `ldr-docs-gate.yml` and `version-coherence-check.yml` (BORN
      self-hosted, no hosted ancestor — the former needed a new `actions/setup-python` + `pip install pyyaml` step added
      since it has no ambient venv to fall back on; the latter was already safe as-is, has its own auth +
      self-installing Firestore SDK); `reconcile-staging-versions.yml` / `staging-to-main.yml` (mechanical flip, no
      missing steps); `ldr-to-main-promote.yml` (already `ubuntu-latest` from an unrelated 2026-08-06 emergency revert —
      just updated the stale "temporary, flip back" comment to record this is now permanent). (c) The 7ish
      fleet-health-watchdog files were never touched — confirmed still `ubuntu-latest`. **Real gap found in
      `hosted-baseline.sh`'s own `restore --all`**: its mechanical-flip classifier only inspects the FIRST commit that
      ever introduced a self-hosted `runs-on` line — 3 files (`readiness-verifier.yml`, `ruleset-drift-alert.yml`,
      `reconcile-release-tags.yml`) had their `actions/setup-     python` / Firestore-install steps deleted in a LATER
      commit, so the tool's own `restore --all` silently produced a broken (Python/deps-less) `ubuntu-latest` workflow
      for all 3 — caught via a fleet-wide grep for python/uv/ gcloud usage lacking any matching setup step, fixed by
      hand from each file's true first-flip-commit parent (`git log --reverse -G'runs-on:\[self-hosted'`). Evidence:
      `grep -rn 'runs-on:.*self-hosted'     unified-trading-pm/.github/workflows/` shows zero real routing lines left
      (only historical comments); `QG slice     (tests)` green on `ubuntu-latest` for the post-revert commit
      (`workflow_dispatch` run 31174345746 — the only failing leg, `QG slice (checks)`, is the pre-existing unrelated
      plan-hygiene ratchet failure). PM's 8 self-hosted runners deregistered from GitHub + systemd units
      stopped/disabled on the CI VM, confirmed `inactive` with no re-registration; other 7 private repos' pools
      confirmed untouched. Full detail + 24h CI-VM usage tracking:
      `/plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`.
- [ ] 20. [INFRA] P2. **Re-measure GitHub Actions billing for the 17 reverted repos** (should read $0/unmetered,
      confirming the public-repo-unmetered premise held in practice) and the self-hosted VM's steady-state load average
      before vs. after (not a spot-check — matches `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s own
      still-open "longer-window measurement" gap). Update that plan's issue doc
      (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`) with the dated result rather than duplicating
      it here.
- [x] 21. ✅ [INFRA] P1. **Deregistered the old self-hosted runners for all 17 landed repos — DONE.** Used the
      documented safe path exactly (`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s own incident-derived
      method — never `setup-glue-runners.sh teardown --POOL_TAG`, which has a live, unresolved, reproducible bug that
      silently drops `POOL_TAG` and can take down an unrelated repo's entire pool). Confirmed live via SSM
      (`SSM_INSTANCE=i-042a6332509482556`, the dedicated `ci-escalation-runner-vm-1` — NOT `ssm-run.sh`'s stale default,
      which still points at the old AO box) that each of the 17 repos maps to EXACTLY one
      `github-glue-runner-<repo>@glue-1.service` + 2 timers (`slot-refresh`, `token-refresh`), with the unit DESCRIPTION
      itself naming the exact repo — zero ambiguity. Stopped+disabled all 51 units (17×3) by exact literal name in one
      pass (no `POOL_TAG`/script invocation anywhere), then `gh api -X DELETE` the specific runner ID for each of the 17
      repos (fetched per-repo first, not guessed). **Verified clean both sides**: all 17 repos now show `total_count: 0`
      registered runners; a fresh `systemctl list-units 'github-glue-runner*'` sweep afterward shows ONLY the 8 private
      repos' pools still active (`ao` ×4, `unified-trading-pm` ×8, `strategy-service`, `e2e-testing`,
      `execution-service`, `features-service`, `market-tick-data-service`, `ml-service` — all online, zero collateral
      damage). **One false alarm chased down and cleared**: `market-tick-data-service`'s journal showed a
      `Stopping`/job-`Canceled`/`Started` cycle that looked concerning at first glance — traced it to 13:38-13:39 UTC,
      ~7.5 hours before this deregistration ran (~21:1x UTC) and confirmed as a routine JIT-ephemeral runner restart
      (its own systemd `restart counter` was already at 13 from routine per-job cycling since 2026-08-04) — unrelated to
      anything done here; the unit's own timers were still correctly active/scheduled throughout, confirming it was
      never touched.
- [x] 22. ✅ [INFRA] P2. **`unified-trading-library`'s promotion-PR backlog — RESOLVED, not a bug.** Follow-up check:
      PRs #746–#750 were each individually **closed (not merged)** at staggered times through 2026-08-05, and a fresh PR
      #751 was open with all checks green (`semver-agent/label-check`, `sit-gate/fleet-green`,
      `unified-trading-library-live-defi-rollout` Cloud Build all `SUCCESS`) and `MERGEABLE`. This matches
      `ldr-to-main-promote-fleet.yml`'s close-and-recreate-on-new-diff behavior firing repeatedly under this session's
      (and the wider shared host's) unusually high same-day commit volume on `unified-trading-library`'s dependents —
      not a stuck pipeline. No fix needed.
- [x] 23. ✅ [INFRA] P2. **Inverse-direction audit: any of the 8 PRIVATE repos' workflows still on billed GitHub-hosted
      minutes that COULD move to self-hosted? Checked all 7 not already covered by the earlier `unified-trading-pm`
      sweep (todo/finding above) — zero actionable items, same shape of answer.** Every `runs-on: ubuntu-latest` /
      GH-hosted item across `agent-orchestrator`, `strategy-service`, `e2e-testing`, `features-service`,
      `market-tick-data-service`, `execution-service`, `ml-service` resolves to one of three legitimate categories: -
      **`notify-slack.yml`** (5 of 7 repos) — confirmed `on: workflow_call` only (a reusable carrier other jobs invoke
      on-demand when something fails), same resilience reasoning as PM's own fleet-health watchdogs: it must stay
      GH-hosted so it can still fire if the self-hosted infra itself is what's unhealthy. Correct as-is. -
      **`image-build-gate.yml`** (all 7) — has no local `runs-on:` at all; it's a pure `uses:` delegation to
      `unified-trading-pm/.github/workflows/image-build-validate.yml`, which is ALREADY self-hosted
      (`[self-hosted, glue]` on all 3 of its own jobs). Zero local cost, nothing to fix. - **`agent-audit.yml`**
      (`strategy-service` inline; `execution-service`/`features-service`/ `market-tick-data-service` delegate to PM's
      `python-quality-gates-v2.yml`) — `workflow_dispatch`-only. Header comments in 3 of these claim "Triggered by
      `overnight-agent-orchestrator.yml` for nightly quality-gate validation," which is **stale**: read that
      orchestrator directly — its T1/T2/T3 tiers were removed when their member repos folded into
      `unified-api-contracts`/`unified-trading-library`; only T0 (those 2, both already public/GH-hosted) remains wired.
      No live recurring trigger exists for any of these 4 `agent-audit.yml` files today, so their runner choice costs
      nothing regardless of value. - **Useful side-finding, not a gap**: this traced through to confirming the MAIN
      `quality-gates-v2.yml` gate's real heavy execution (`qg-slices` job in `python-quality-gates-v2.yml`) is
      controlled by a `with:       self_hosted_runner_labels` input — NOT the caller file's own local `runs-on:` lines
      (those govern only that file's auxiliary jobs, e.g. the escalation/notify ones this plan's todo 1-4 work fixed).
      That input is templated by the SAME pre-existing `get_qg_runner_labels()` off the SAME `self-hosted-qg-repos.txt`
      this plan edited, via the SAME `rollout-workflow-templates.sh` rollout already run — spot-checked and confirmed
      correct both directions: `strategy-service`/`execution-service` (private) render `'["self-hosted","glue"]'`;
      `unified-api-contracts`/`deployment-api` (public, reverted) render `""` (→ `ubuntu-latest`). Confirms the
      session's core revert was complete and correct for the main gate all along, not just the auxiliary jobs.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  reconsidered but NOT flipped. Todo 20 (billing/load re-measurement) was originally time-gated as "needs a few days of
  real elapsed usage to be meaningful" (2026-08-07 note); as of today, 4 days have elapsed since the bulk of the 17
  repos' reverts landed (2026-08-05) and 2 days since PM's own revert (todo 24, 2026-08-07) — genuinely closer to
  boundary than at the last check, and the underlying pull mechanism itself is fully bounded/procedural (the same
  `github-billing-token` GSM secret + `aws ce get-cost-and-usage` procedure already used successfully by the sibling
  `ci_pipeline_speed_and_cost_redesign_2026_08_05.md` P0 todo, which explicitly treated a partial-month pull as a
  legitimate interim data point). Did NOT flip this round for two reasons: (1) "a few days" has no stated numeric
  threshold in this doc's own text, so treating 2-4 days as sufficient is itself a judgment call this sweep should not
  make unilaterally when the doc's own author (an interactive, operator-directed session, not AO-dispatch) explicitly
  chose the LOCAL/human track "since each revert needs live-judgment verification"; (2) the todo's own text says "update
  that plan's issue doc" (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`) rather than this plan
  directly, and that issue doc is itself an active hub for at least 2 adjacent billing-measurement efforts
  (`github_actions_operator_gated_followups_2026_07_17.md`'s own separate "two-week billing-ledger comparison," earliest
  ~2026-07-31) — coordinating which measurement lands where has a real risk of duplicate/conflicting dispatch that a
  fresh conflict-check alone does not fully resolve. Flagging this as the closest-to-boundary item found in this round's
  11-doc sweep, worth a direct re-check in a few more days rather than dispatching now. Checked against this round's
  accumulated-precedent list (IAM self-service, D16 all-repos, S5.1 tiering, plan-destination-AO-default,
  escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks) — none directly
  resolve the "is enough time elapsed" question; noted this is a pure timing/ coordination call, not a precedent-driven
  one.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since 2026-08-06. Re-read end-to-end;
  `grep -cE '^- \[ \]'` = 1, matching (todo 24, PM's own revert, was closed same day 2026-08-07, before this pass). The
  sole remaining item (todo 20, billing/load re-measurement) is explicitly timing-gated — needs a few days of real
  elapsed usage to be meaningful, not worker-determinable today.
- **2026-08-07 (ci-reconcile sweep, follow-on finding)** — This plan's runner deregistration (todo 21, DONE) left
  `glue-runner-health-monitor.yml` (created 2026-08-06, after most of this plan's early phases) watching a pool that
  will never come back — it paged CRITICAL every hour on a permanent, will-never-clear "0 online" condition. Also found
  its `GET .../actions/runners` call had been 403ing 100% of the time on `secrets.GITHUB_TOKEN` (structural: the
  `administration` scope it needs isn't grantable to the automatic token at all), which is WHY it took this long to
  notice the pool was empty — the query itself was broken, not just alarmingly honest. Fixed the token
  (`unified-trading-pm@f05e93d10a`, switched to the existing `GH_PAT` already used to register the pool) so the monitor
  could see reality, confirmed reality is genuinely 0 registered runners (not a query-scope bug — verified
  independently), then disabled its `schedule:` trigger (`unified-trading-pm@95cce3aa4`) since this plan already
  established that state is permanent by design. `glue-pool-starvation-monitor.yml` (sibling, same now-retired pool) was
  NOT touched — it isn't currently paging (nothing queues onto a pool nobody targets), lower priority, flagged here for
  whoever next touches this plan to consider retiring for the same reason.

- **2026-08-07 (interactive session)** — Closed todo 24 (see the todo's own entry for full detail): PM's ~40
  self-hosted-routed workflows reverted to `ubuntu-latest` (`unified-trading-pm@c8cd56251e`), live-verified green,
  runners deregistered. Only todo 20 (billing re-measure, P2, timing-gated) remains open in this plan.

- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — operator-directed local plan (Progress Log
  2026-08-05); todo 24 (PM's own revert) requires the same per-file mechanism-landscape care on live CI + todo 20 is
  timing-gated re-measurement; neither stale nor duplicated.

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

- **2026-08-05 (resumed after `/compact`, session close-out): all 17/17 repos now landed — the revert is 100% shipped.**
  Picked up exactly where the checkpoint left off:
  - **`deployment-api`** (`@54a4444`): first attempt hit `test_reads_execute_concurrently_not_sequentially`, a
    wall-clock timing assertion (`elapsed < sequential_cost*0.65`) that failed at 93% of the threshold under shared-host
    CPU contention — confirmed flaky, unrelated to a workflow-file-only change, by re-running the single test standalone
    (passed cleanly, 0.35s vs. 1.123s under load). Bare retry succeeded.
  - **`instruments-service`** (`@064e2560`): re-checked the golden-fixture test before retrying — now passes (2/2),
    fixed upstream by whoever owned that judgment call, exactly as todo 14 anticipated. Shipped clean.
  - **`system-integration-tests`** (`@69875d4`) — the 17th and final repo. Pre-flight failed once more, this time on a
    **different, previously-undiagnosed blocker**: `market-data-processing-service` and `instruments-service` both
    showed a dirty `uv.lock` (unrelated to any of the workflow reverts). Traced it: both diffs added identical
    `marker = "extra == 'schema-validation'"` entries for the SAME six packages, sourced from
    `unified-trading-library`'s own `[[package]]` entry in the downstream lockfiles. Checked `unified-trading-library`
    itself — its **committed** `uv.lock` already carries `provides-extras = ["schema-validation"]`, but `grep` found
    that string **nowhere in its `pyproject.toml`** — i.e. the extra is dangling/orphaned lockfile metadata, not a real
    declared dependency, and downstream `uv sync` regenerates this same diff on every run regardless of what anyone does
    locally. Confirmed safe to discard (`git checkout -- uv.lock` in both repos) rather than treat as foreign WIP: it's
    a derived artifact from an already-committed upstream inconsistency, not hand-authored work — discarding it destroys
    nothing and it would regenerate identically if truly needed. Retried, landed clean.
  - **Final verification**: `grep -rl 'runs-on:.*self-hosted'` across all 17 repos' `.github/workflows/` → **zero hits,
    all 17**; all 17 working trees clean (`git status --short .github/workflows/` empty); all 8 private repos
    (`agent-orchestrator`, `unified-trading-pm`, `strategy-service`, `e2e-testing`, `features-service`,
    `market-tick-data-service`, `execution-service`, `ml-service`) independently confirmed to still carry their
    self-hosted refs (9-41 hits each) — the split is exactly as intended, answering the operator's direct question: no
    public-repo self-hosted CI ever ran pointlessly past this session's fixes.
  - Also closed out todo 22 in the same pass: the `unified-trading-library` promotion-PR "backlog" (#746-750) was just
    `ldr-to-main-promote-fleet.yml` closing and recreating the PR each time LDR advanced past its diff — expected under
    this session's own high commit volume, not a stuck pipeline. PR #751 is open, green, mergeable.
  - **Genuinely still open, in priority order**: todo 21 (deregister the now-idle old self-hosted runner registrations
    for all 17 repos — confirmed via `gh api repos/IggyIkenna/alerting-service/actions/runners` that stale registrations
    do still exist and sit idle; deferred this session rather than attempted, since it requires SSM access to the shared
    CI runner VM to stop/disable the actual systemd units (GH-API-delete alone would leave the process running) and
    touches shared infra other concurrent sessions may be relying on — this is cleanup, not correctness: the
    billing-waste problem itself is already fully fixed by the `runs-on:` changes, since idle registrations cost nothing
    and simply won't be assigned work); todo 20 (billing/load re-measurement — genuinely cannot be done yet, needs a few
    days of elapsed real usage to be meaningful). **Plan stays `status: active`** — not archiving until 20 and 21 close.

- **2026-08-05 (operator: "do it, any other flows that can be self hosted on private repos anything at all currently
  using gh ci mins?") — todo 21 (runner deregistration) and todo 23 (inverse-direction audit) both closed.**
  - **Todo 21**: full details in that todo's own entry above. Headline: 17/17 repos' old self-hosted runners cleanly
    deregistered (systemd + GitHub API both sides), zero collateral damage to the 8 private repos, one false-alarm
    journal entry chased down and confirmed unrelated (predates this work by ~7.5h).
  - **Todo 23**: the operator's question was the exact inverse of this plan's original direction — private repos still
    paying real GH Actions minutes that could move to self-hosted. Checked all 7 private repos not already covered by
    the earlier PM sweep; found zero actionable items, each `ubuntu-latest` use falls into a legitimate, already-correct
    category (see todo 23 for the three-way breakdown). **The most valuable output of this pass wasn't a new fix — it
    was closing a verification gap this plan had never actually closed**: tracing exactly how
    `self_hosted_runner_labels` flows from `self-hosted-qg-repos.txt` through `rollout-workflow-templates.sh` into the
    reusable `python-quality-gates-v2.yml`'s heavy `qg-slices` job confirmed the MAIN quality-gates-v2.yml gate (not
    just the 9 auxiliary templates todos 1-4 fixed) was correctly reverted for all 17 public repos all along — this had
    been _assumed_ correct (the allowlist + existing `get_qg_runner_labels()` predates this plan) but never directly
    spot-checked against the actual rendered `with:` value in a committed file until now.
  - **Lesson for whoever continues this**: when a repo's workflow calls a reusable workflow via `uses:`, that reusable
    workflow's OWN `runs-on:` (or, if parameterized, whatever input drives it) is what actually governs execution — a
    caller-local `runs-on:` line in the SAME job key is not even read by GitHub Actions. Don't assume a grep for
    `runs-on:` in the caller file tells the whole story; find the `uses:` target and check IT.
  - **Genuinely remaining**: only todo 20 (billing/load re-measurement, needs a few days of real elapsed usage). Nothing
    else is open. Plan stays `status: active` until that closes, then archive per the standard ritual.

- **2026-08-06 (interactive session, main_ci_red incident)**: `unified-trading-pm` was found accidentally PRIVATE,
  breaking `quality-gates-v2` fleet-wide (public repos cannot call a reusable workflow hosted in a private repo — a
  GitHub platform rule, not a settings toggle; confirmed via `unified-api-contracts` PR #860 stuck with the required
  check never reporting). Flipped PM back to PUBLIC (`gh repo edit --visibility public`), verified fixed (a fresh
  `workflow_dispatch` run on `unified-api-contracts`'s `quality-gates-v2.yml` resolved real jobs instead of 0-jobs/
  "workflow not found"). This makes PM the 18th repo in this plan's scope for the SAME reason as the other 17 — added as
  todo 24. Also marked `pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md` **superseded**: it was
  scoping moving MORE of PM's workflows TO self-hosted (billing-motivated, written while PM was private); that premise
  is now moot in the opposite direction. Separately started
  `/plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md` (LOCAL plan) to extract the reusable
  workflow YAML itself into a small dedicated public repo (`unified-trading-ci`), so PM can go private again in the
  future (e.g. if today's accidental flip reflects a real sensitivity concern) without breaking CI fleet-wide — that
  plan is the durable architecture fix; this plan's todo 24 is the same billing-driven revert already applied to the
  other 17.
- **context-scout 2026-08-06**: populated context_scope (6 entries).
