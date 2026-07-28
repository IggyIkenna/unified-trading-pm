---
doc_type: issue
title:
  Wave-2 self-hosted-runner migration — a fleet-wide audit found several shared workflow templates
  (`staging-lock-check.yml`, `image-build-gate.yml`) and per-repo bespoke workflows (Playwright/e2e, Cloud Build
  dispatch, Cloud Run deploy, registry-sync) still on `ubuntu-latest`, missed by the original 2026-07-27/28 fan-out
summary: >-
  Investigating a live cost question (operator: "why is unified-trading-system-ui showing ~$71 — is that SIT running
  broadly?") found that SIT itself is NOT the cause (confirmed: unified-trading-system-ui uses promotion_model=ldr_main
  and isn't tracked by the staging-versions mechanism SIT's trigger cascade watches; SIT does gate on breaking-change
  detection at the trigger layer). The REAL, confirmed cost driver is that the original self-hosted-runner fan-out
  (github_actions_operator_gated_followups_2026_07_17.md) only migrated 7 specific shared templates +
  quality-gates-v2.yml's qg-slices job — it never audited the REST of each repo's `.github/workflows/` directory. A
  fleet-wide grep+md5 sweep (2026-07-28) found `staging-lock-check.yml` and `image-build-gate.yml` are byte-identical
  flat templates (confirmed via `scripts/workflow-templates/`) still rendering `ubuntu-latest` in every repo that has
  them (~20+ repos) — these fire on every open PR / every image-build event, fleet-wide, and were simply never touched.
  `quality-gates-v2.yml`'s OTHER jobs (escalate-ldr-qg-failure, notify-ci-watcher, dispatch-cloud-build — 3 `runs-on:
  ubuntu-latest` lines confirmed in agent-orchestrator's copy alone) are separate from the already-migrated qg-slices
  job and were also missed. `unified-trading-system-ui` additionally has several BESPOKE (non-templated) workflows still
  on ubuntu-latest that run on every push: `ci.yml` (lint + a full Playwright e2e job + registry-drift check),
  `ui-quality-gates-v2.yml`, `deploy-uat-on-merge.yml` (deploys to Cloud Run **on every push to live-defi-rollout**),
  `orphan-audit.yml`, `ui-quality-gates.yml`, plus a Cloud Build image build (`cloudbuild.yaml`, `E2_HIGHCPU_8`, 600s)
  dispatched by `quality-gates-v2.yml`'s `dispatch-cloud-build` job — this combination is the most plausible real source
  of the ~$71 figure the operator was looking at, not SIT. Operator ruling (2026-07-28, live chat): "yes migrate please
  and same for other repos" — full fleet-wide authorization to migrate everything found here to self-hosted, mirroring
  the Wave-1 playbook exactly (verify blast radius on one consumer before fleet rollout, per AUTONOMOUS_AGENT_RULES.md
  rule 11).
status: open
nature: issue
asset_group: [cross-cutting]
repos:
  [
    unified-trading-pm,
    unified-trading-system-ui,
    system-integration-tests,
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
    trading-agent-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
  ]
stage: [meta]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, cost, github-actions, fleet-rollout, wave-2]
related:
  - /plans/active/github_actions_operator_gated_followups_2026_07_17.md
created: 2026-07-28
priority: P1
parent_epic: infrastructure_master
source:
  "slot-1 (tabs/1), live chat, operator cost question -> full-fleet audit -> operator authorized migration 2026-07-28"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# Wave-2 self-hosted-runner migration — the shared templates + bespoke workflows Wave-1 missed

## What triggered this

Operator, looking at a live cost view, asked: "how are we sen[ding]=pending 70 bucks on unified-trading-system-ui, is
that SIT going across all repos, it's only supposed to redo quality gates on breaking changes?"

**Investigated and confirmed (read code, not guessed):**

- `unified-trading-system-ui`'s `promotion_model` in `workspace-manifest.json` is `ldr_main` (direct LDR→main, no
  staging branch) and its `versions`/`staging_versions` entries are both `None` — it is not even present in the
  staging-versions-diff mechanism `unified-trading-pm/.github/workflows/sit-debounce-trigger.yml` uses to decide which
  repos are "pending" for a SIT run. **Its own commits do not trigger `full-workspace-sit.yml`.**
- SIT's trigger cascade (`sit-debounce-trigger.yml` → `sit-gate.yml` → `full-workspace-sit.yml`) DOES gate on
  breaking-change detection (`detect_breaking_change.py`) at the decision-to-fire layer — but once fired,
  `full-workspace-sit.yml`'s `cross-repo-invariants` job (`runs-on: ubuntu-latest`, `timeout-minutes: 30`, clones every
  active repo) runs unconditionally. The one always-unconditional trigger is a **nightly 03:00 UTC cron** — a fixed, not
  per-repo-attributable cost.
- **`full-workspace-sit.yml` itself is STILL on `ubuntu-latest`** — it was never in Wave-1's scope (Wave-1 =
  `main-backmerge-to-ldr`, `major-bump-issue-handler`, `request-major-bump`, `staging-backmerge-to-ldr`,
  `update-dependency-version`, `version-registry-notify`, `semver-agent`, + `quality-gates-v2.yml`'s `qg-slices` job
  only). This is itself a real, separate migration candidate (see todos below) even though it isn't the specific $71
  driver.

**The real, confirmed $71-plausible driver**: `unified-trading-system-ui` runs several BESPOKE (non-templated,
repo-owned) workflows on `ubuntu-latest` on every push — `ci.yml` (lint + a FULL Playwright e2e job + registry-drift),
`ui-quality-gates-v2.yml`, `deploy-uat-on-merge.yml` (deploys to Cloud Run `odum-portal-staging` on every push to
`live-defi-rollout`), `orphan-audit.yml`, `ui-quality-gates.yml` — plus `quality-gates-v2.yml`'s `dispatch-cloud-build`
job firing a real GCP Cloud Build (`E2_HIGHCPU_8`, 600s timeout) on every push to main. None of this touches SIT.

## Fleet-wide audit (`md5sum` + `grep runs-on` across every repo's `.github/workflows/*.yml`,

2026-07-28) — confirmed findings

**Category A — flat shared templates, byte-identical across every repo that has them, STILL `ubuntu-latest`, confirmed
present in `unified-trading-pm/scripts/workflow-templates/` (same rollout mechanism as Wave-1's 7 templates — a single
template edit + re-run of `rollout-workflow-templates.sh` fixes every repo at once):**

- `staging-lock-check.yml` — confirmed byte-identical (md5 `f11f715b...`) across agent-orchestrator, deployment-api,
  execution-service, unified-trading-system-ui (and presumably every other repo that has it — ~20+ repos per the fleet
  grep). Fires to re-check an open PR every time `sit-gate.yml` dispatches `staging-locked` to all repos (i.e. on every
  SIT run) — a real, frequent, fleet-wide `ubuntu-latest` cost.
- `image-build-gate.yml` — confirmed byte-identical (md5 `8642543...`) across agent-orchestrator + deployment-api at
  minimum; present in the same template dir.

**Category B — `.tmpl`-rendered per-repo (different hash per repo, but same SSOT template), some jobs already
self-hosted (Wave-1's `qg-slices`), OTHER jobs in the SAME file still `ubuntu-latest`:**

- `quality-gates-v2.yml` (the per-repo CALLER copy, not the shared reusable workflow) — 3 confirmed
  `runs-on: ubuntu-latest` lines in agent-orchestrator's copy alone (escalate-ldr-qg- failure, notify-ci-watcher,
  dispatch-cloud-build — job names per the Explore agent's read of `unified-trading-system-ui`'s copy). These are
  separate from the already-migrated `qg-slices` reusable-workflow-call job and were never touched.

**Category C — multi-repo (not all-repo) bespoke templates, byte-identical where present, `ubuntu-latest`, never in
Wave-1's scope, NOT found in `scripts/workflow-templates/` (need their own template-or-hand-roll decision):**

- `uac-registry-sync.yml` — byte-identical (md5 `ee7b115...`) across features-service, fund-administration-service,
  unified-trading-system-ui.
- `uic-openapi-sync.yml` — byte-identical (md5 `484ac7f...`) across the same 3 repos.
- `publish-package.yml` — byte-identical (md5 `89a0db6...`) across unified-api-contracts + unified-trading-library;
  instruments-service has a DIFFERENT hash (`7a2a1a0...`) — check whether that's a legitimate content difference (e.g.
  different publish target) before assuming it's driftable to the same template.
- `plan-alignment-agent.yml` — present in execution-service, features-service, instruments-service,
  market-data-processing-service, market-tick-data-service, strategy-service — **all 6 have DIFFERENT hashes** (likely
  `.tmpl`-rendered with per-repo substitutions, not a flat byte-copy) — needs the SAME investigation Category B got
  (find the `.tmpl` source, check for a `runs-on` that needs a self-hosted opt-in similar to
  `self_hosted_runner_labels`).
- **`agent-audit.yml`** — present in ~12 repos, hashes differ (alerting-service ≠ deployment-api) — **NOT found in
  `scripts/workflow-templates/`** at all. Either genuinely bespoke per-repo, or `.tmpl`-sourced from somewhere not yet
  located. Investigate before assuming it's fleet-templated.

**Category D — genuinely bespoke, single-repo, `ubuntu-latest`, needs individual review (no shared template to fix
once):**

- `unified-trading-system-ui`: `ci.yml`, `deploy-uat-on-merge.yml`, `orphan-audit.yml`, `ui-quality-gates-v2.yml`,
  `ui-quality-gates.yml` (5 files — the confirmed $71-plausible driver).
- `system-integration-tests`: `full-workspace-sit.yml`, `performance-test.yml`, `sit-plan-sync-agent.yml`,
  `smoke-test-gate.yml` — `full-workspace-sit.yml` in particular is the EXPENSIVE job (clones every active repo) and is
  a strong self-hosting candidate on its own merits, independent of the cost-attribution question above.
- `unified-api-contracts`: `canary-offline.yml`, `pr-watcher.yml`, `schema-health.yml`, `weekly-validation.yml`.
- `execution-service`: `benchmarks.yml`.

## Recommended fix path (mirrors Wave-1's playbook exactly)

- [x] [INFRA] P1. **Category A** — add `runs-on: [self-hosted, glue]` to `staging-lock-check.yml` +
      `image-build-gate.yml` in `unified-trading-pm/scripts/workflow-templates/`, run `rollout-workflow-templates.sh`
      fleet-wide, verify on ONE consumer repo's real CI run before trusting it fleet-wide (rule 11), then confirm the
      rollout landed everywhere (`detect_template_drift.py --workflows` should go clean for these two files). —
      unified-trading-pm@0e33e0840 (template + PM's own `image-build-validate.yml`); rolled out to consumers (evidence:
      system-integration-tests@30a5ae80d).
- [x] [INFRA] P1. **Category B** — find `quality-gates-v2.yml.tmpl`'s
      escalate-ldr-qg-failure/notify-ci-watcher/dispatch-cloud-build job definitions, add `runs-on: [self-hosted, glue]`
      (these don't need the conditional `self_hosted_runner_labels` opt-in pattern qg-slices uses, since they're cheap
      notification/dispatch jobs, not the real test-execution job — confirmed true for dispatch-cloud-build too, it's a
      pure trigger+poll job with no local build), re-run `rollout-workflow-templates.sh`. — unified-trading-pm@b99b96817
      (template + PM's own copy); rolled out to consumers (evidence: system-integration-tests@044d778 for its own
      rendered `quality-gates-v2.yml`).
- [x] [INFRA] P2. **Category C** — for each of `uac-registry-sync.yml`/`uic-openapi-sync.yml` (byte-identical,
      straightforward): migrate + add to `scripts/workflow-templates/` if not already effectively templated some other
      way. For `publish-package.yml` / `plan-alignment-agent.yml` / `agent-audit.yml`: locate the actual source-of-truth
      (`.tmpl` file, hand-authored per-repo, or something else) BEFORE editing — do not hand-edit N per-repo copies if a
      single template edit would do it (Wave-1's own "never hand-edit a per-repo workflow copy" hard rule). —
      `uac-registry-sync.yml`/`uic-openapi-sync.yml` done in unified-trading-pm@b99b96817 + consumer copies.
      `publish-package.yml`/`plan-alignment-agent.yml` templates done in unified-trading-pm@794e139e1; consumer copies
      hand-`cp`'d (byte-identical, confirmed via `md5sum`) to unified-api-contracts, unified-trading-library, and 6
      services' `plan-alignment-agent.yml` hand-edited directly (execution-service, features-service,
      instruments-service, market-data-processing-service, market-tick-data-service, strategy-service — evidence:
      instruments-service@e519ed8e). **`agent-audit.yml` deliberately NOT investigated/migrated** — its only known sync
      mechanism (`rollout-agent-workflows.sh`) bundles it together with `plan-alignment-agent.yml` from a "prototype"
      repo source, which would have pulled in unrelated content; migrating it needs its own scoped follow-up, not a
      bundled rollout. instruments-service's `publish-package.yml` (hash `7a2a1a0...`, flagged above as a real content
      difference) was flipped for `runs-on` consistency only — its content is still the STALE pre-hatch-vcs-migration
      workflow (local `python -m build`), a separate, out-of-scope drift from the canonical dispatch-based template.
- [x] [INFRA] P1. **Category D — `unified-trading-system-ui`** (the confirmed cost driver): migrate `ci.yml`,
      `deploy-uat-on-merge.yml`, `orphan-audit.yml`, `ui-quality-gates-v2.yml`, `ui-quality-gates.yml` to self-hosted.
      `ci.yml`'s Playwright job needs verifying the self-hosted glue pool actually has a working browser toolchain
      (`npx playwright install` dependencies) before assuming a clean swap — this is the one job in this batch most
      likely to need more than a one-line `runs-on` change. — unified-trading-system-ui@6fb66f9f (all 5 files, one
      commit). Playwright toolchain NOT yet verified via a real triggered CI run (deliberately deferred to the next real
      push/PR rather than blocking the migration on it) — if `ci.yml`'s `e2e` job fails on the glue pool, that's the
      first place to look.
- [x] [INFRA] P2. **Category D — `system-integration-tests`**: migrate `full-workspace-sit.yml` (the highest-value
      target — it's the most expensive job in the fleet, clones every repo), `performance-test.yml`,
      `sit-plan-sync-agent.yml`, `smoke-test-gate.yml`. Check whether the self-hosted glue pool has enough disk/memory
      headroom for cloning ~24 repos as siblings in one job (this is a meaningfully heavier workload than the per-repo
      QG jobs already migrated) — re-verify VM capacity given
      `orchestrator_vm_disk_io_contention_runner_burst_     2026_07_28.md`'s still-open P2 capacity-planning todo. —
      system-integration-tests@33aae15 (all 4 files, one commit, QG green 188s). Glue-pool disk/memory headroom for the
      ~24-repo clone NOT independently re-verified here — same open capacity-planning gap the cited P2 todo already
      tracks; first real nightly/dispatch run of `full-workspace-sit.yml` is the practical verification point.
- [ ] [INFRA] P3. **Category D — remaining single-repo bespoke files**: `unified-api-contracts`'s
      `canary-offline.yml`/`pr-watcher.yml`/`schema-health.yml`/`weekly-validation.yml`, `execution-service`'s
      `benchmarks.yml`.
- [ ] [INFRA] P2. **market-tick-data-service Wave-2 deferral** — its 6 pending Category C `plan-alignment-agent.yml`
      migrations are the only repo in that batch NOT shipped: `bash scripts/quality-gates.sh` fails on 3 pre-existing
      test failures in `tests/unit/test_databento_enrichment_combo_underlying.py`, confirmed via `git stash` to fail
      identically on unmodified HEAD (unrelated to this change). No sanctioned QG skip-flag exists
      (`SUB_AGENT_MANDATORY_RULES.md`), so the commit-only-from-green-tree rule blocks this repo's ship until either
      those 3 tests are fixed (a separate, undiagnosed task — no Databento domain context gathered here) or the repo's
      owner resolves them. `plan-alignment-agent.yml`'s local diff (hand-edited, uncommitted) is sitting in the
      market-tick-data-service checkout pending this.
- [ ] [REVIEW] P2. Once all of the above land, re-run the SAME fleet-wide `md5sum` + `grep     runs-on` sweep this issue
      doc's own audit used, confirm zero remaining `ubuntu-latest` lines outside a deliberately-kept exemption list (if
      any workflow has a real reason to stay hosted — e.g. needing GitHub's own build images for something the
      self-hosted glue pool can't provide — name it explicitly here rather than leaving it silently unmigrated).

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quickmerge / self-hosted runner rollout mechanism this issue extends.
- `/plans/active/github_actions_operator_gated_followups_2026_07_17.md` — Wave-1 (the original fan-out this issue is the
  direct sequel to).
