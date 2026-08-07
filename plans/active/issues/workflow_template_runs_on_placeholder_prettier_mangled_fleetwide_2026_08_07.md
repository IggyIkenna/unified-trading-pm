---
doc_type: issue
title: >-
  Fleet-wide broken `runs-on:` in 7 workflow templates — prettier deterministically mangles the `{{RUNS_ON}}`
  placeholder on every commit; root-caused, template SSOT fixed, alerting-service re-rolled + verified green
summary: >-
  `unified-trading-pm/scripts/workflow-templates/{main-backmerge-to-ldr,major-bump-issue-handler,request-major-bump,
  staging-backmerge-to-ldr,staging-lock-check,update-dependency-version,version-registry-notify}.yml` all carried
  `runs-on: { { RUNS_ON } }` (introduced in 3240ec79e, 2026-08-05) — invalid YAML (a nested flow-mapping used as an
  unhashable key). GitHub silently stops scheduling any workflow with this, and `quality-gates-v2`'s workflow-yaml gate
  correctly reds on every repo that received the broken copy. This escalation (agt-62ba62, wall_type ldr_qg_failure,
  repo alerting-service) chased it down.

  **Real root cause (not a one-time typo)**: `prettier --write` deterministically reformats a bare `{{RUNS_ON}}` (parsed
  as a YAML flow-mapping) into `{ { RUNS_ON } }` — confirmed by direct repro (`npx prettier --write` on an isolated test
  file). This repo's `prettier-autostage` pre-commit hook re-applies that mangling on every commit that touches the
  file, so simply restoring literal `{{RUNS_ON}}` text does NOT survive a commit here (verified the hard way: my first
  attempted fix committed as an EMPTY commit — prettier silently reverted it back to the broken form before the commit
  closed, and `git show --stat` on that commit showed zero files changed). This is very likely the actual mechanism that
  broke 3240ec79e in the first place — someone likely typed `{{RUNS_ON}}`, the pre-commit hook mangled it, and it
  shipped broken without anyone noticing since the corruption is silent (no hook failure, no lint error at commit time —
  only surfaces later as a red `quality-gates-v2` on repos that receive the template).

  **Fix shipped to the template SSOT** (`unified-trading-pm@300fe3aaf`): switched the placeholder to `__RUNS_ON__`
  (double-underscore, matching the existing `__REPO_NAME__`/`__SOURCE_DIR__`/`__VERSION_SOURCE__` convention already
  used elsewhere in this same script) — verified stable under `prettier --write` (unchanged) and substitutes correctly
  for both the scalar (`ubuntu-latest`) and list (`[self-hosted, glue]`) `get_runs_on_value()` outputs. Updated
  `rollout-workflow-templates.sh`'s two sed passes plus all 9 templates that reference RUNS_ON (7 flat copies +
  `quality-gates-v2.yml.tmpl` + `semver-agent.yml.tmpl`, for one consistent token — the latter two were already using
  `.tmpl`-extension files, which the prettier hook's `types_or: [yaml]` filter doesn't match by extension, so they were
  unaffected by the mangling but are now on the same stable token for consistency). Every flat-copy template now also
  parses as valid standalone YAML pre-substitution (a nice side-effect — previously they could never be linted/loaded
  directly even by tooling that knows to skip real substitution).

  **alerting-service (this escalation's target) is fixed + verified**: re-rolled via `rollout-workflow-templates.sh
  --repo alerting-service`, shipped via quickmerge (`alerting-service@4e59479`, verified on origin), and a FRESH
  `quality-gates.sh` re-run confirms `✅ ALL QUALITY GATES PASSED` with `✅ workflow-yaml: 12 workflows parse`.

  **Fleet-wide scope — NOT yet closed for other repos**: the same broken copies were found (via local grep, 2026-08-07)
  in 11 other repo clones checked out under this workspace's `.tabs/6/`: batch-live-reconciliation-service,
  client-reporting-api, deployment-api, deployment-service, execution-service, features-service,
  fund-administration-service, greeks-service, ibkr-gateway-infra, instruments-service, and their
  `.stale-pre-history-rewrite-*` snapshot dirs (not real targets). The full fleet is 26 repos
  (`workspace-manifest.json`); this was a local-clone spot-check, not an exhaustive fleet sweep — some of the remaining
  ~14 repos may also carry the broken copies. **`deployment-service` already has an open repo-blocker** (`RB-45c789ad`,
  opened independently by slot-4/escalation agt-aaf874 hitting the same root cause) — that slot may already be working
  an overlapping fix; coordinate before duplicating.

  **Remaining work** (now mechanical, since the template SSOT is fixed): for each affected repo, run `bash
  scripts/workflow-templates/rollout-workflow-templates.sh --repo <repo>` from `unified-trading-pm`, commit + push the
  regenerated `.github/workflows/*.yml` via quickmerge, and confirm `quality-gates.sh` green. A full-fleet
  `rollout-workflow-templates.sh` (no `--repo` filter) run would also work in one pass since it's idempotent (skips
  repos already current) — but that touches every repo's `.github/workflows/`, so scope/sequence per operator
  preference.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    execution-service,
    features-service,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
  ]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    workflow-template,
    prettier,
    yaml-parse,
    fleet-wide,
    quality-gates-v2,
    ldr_qg_failure,
    rollout-workflow-templates,
  ]
related: [workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
source: cicd-escalation-agt-62ba62
---

# Fleet-wide `runs-on:` placeholder break — root-caused + template SSOT fixed

## Timeline

- **2026-08-05** (`3240ec79e`): `runs-on: {{RUNS_ON}}` introduced across 7 flat-copy workflow templates + 2 `.tmpl`
  templates. The flat-copy templates' `{{RUNS_ON}}` was (very likely, per the repro below) silently mangled to
  `{ { RUNS_ON } }` by the `prettier-autostage` pre-commit hook at commit time — invalid YAML, GitHub silently stops
  scheduling any workflow carrying it.
- **2026-08-07**: two independent CICD escalations (agt-aaf874/slot-4 on `deployment-service`, agt-62ba62/slot-6 on
  `alerting-service`) both hit `quality-gates-v2`'s `workflow-yaml` gate reporting the same 7-file break.
- **2026-08-07** (this doc, agt-62ba62): root-caused to the prettier hook (confirmed via direct `prettier --write` repro
  — see summary), fixed the template SSOT (`unified-trading-pm@300fe3aaf`, `{{RUNS_ON}}` → `__RUNS_ON__`), re-rolled +
  shipped `alerting-service` (`@4e59479`), verified green with a fresh `quality-gates.sh` run.

## Verification evidence

- `unified-trading-pm@300fe3aaf`: 10 files changed (7 templates + `.tmpl`×2 + `rollout-workflow-templates.sh`),
  confirmed via `git show --stat` the commit actually carries the diff (learned the hard way after the first attempt
  silently produced an empty commit).
- `alerting-service@4e59479`: 8 `.github/workflows/*.yml` regenerated via
  `rollout-workflow-templates.sh --repo alerting-service`, all now resolve `runs-on: ubuntu-latest`, all parse via
  `yaml.safe_load`.
- Fresh `bash scripts/quality-gates.sh` on `alerting-service` (not relying on quickmerge's own Pass-1 sentinel):
  `✅ ALL QUALITY GATES PASSED (15s)`, `✅ workflow-yaml: 12 workflows parse`.

## Remaining work

- [x] ✅ [DEVOPS] P1. Re-roll + ship `deployment-service`'s workflow templates — `deployment-service@86af67a` (via
      `rollout-workflow-templates.sh --repo deployment-service`, shipped via quickmerge, verified on origin). Fresh
      `quality-gates.sh` re-run confirmed `✅ ALL QUALITY GATES PASSED (215s)`, `✅ workflow-yaml: 15 workflows parse`.
      `RB-45c789ad` resolved. (agt-aaf874, 2026-08-07)
- [x] ✅ [DEVOPS] P1. Re-roll + ship `greeks-service`'s workflow templates — `greeks-service@f5a63a8` (via
      `rollout-workflow-templates.sh --repo greeks-service`, shipped via quickmerge, verified on origin). Fresh
      `quality-gates.sh` re-run confirmed `✅ ALL QUALITY GATES PASSED (24s)`; all 7 previously-unparseable workflows
      now valid YAML; a direct `workflow_dispatch` of `quality-gates-v2` on `live-defi-rollout` (run 31157269647)
      confirmed green. No open repo-blocker existed for this repo. (agt-5f8afe, cicd escalation, 2026-08-07)
- [x] ✅ [DEVOPS] P1. Re-roll + ship `execution-service`'s workflow templates — `execution-service@e3870664` (via
      `rollout-workflow-templates.sh --repo execution-service`, shipped via quickmerge, verified on origin ancestor).
      Fresh `quality-gates.sh` re-run confirmed `✅ ALL QUALITY GATES PASSED (140s)`,
      `✅ workflow-yaml: 14 workflows     parse`. This also picked up the unrelated `quality-gates-v2.yml.tmpl` drift
      (`ci_trigger_branch` field, `billing_kill` output removal, `d597eb759`) from the same template sync. Unblocked
      LDR→main promotion PR execution-service#557; dispatched `ldr-to-main-promote-fleet` scoped to
      `only_repo=execution-service` to fast-path the re-gate instead of waiting for the next `*/5` scheduled tick — PR
      #557 still showed its stale pre-fix head SHA as of this edit; the scheduled `*/5` tick should supersede it shortly
      if the manual dispatch didn't. (agt-02e6a8, 2026-08-07)
- [x] ✅ [DEVOPS] P1. Re-roll + ship `batch-live-reconciliation-service`'s workflow templates —
      `batch-live-reconciliation-service@afcdd11` (via
      `rollout-workflow-templates.sh --repo batch-live-reconciliation-service`, shipped via quickmerge, verified on
      origin ancestor). Fresh `quality-gates.sh` re-run confirmed `✅ ALL QUALITY GATES PASSED (33s)`; all 8
      previously-broken/drifted workflow files now parse (`yaml.safe_load` clean across all 12
      `.github/workflows/*.yml`). This was blocking promotion PR batch-live-reconciliation-service#315
      (`ci_status=FAILING` on LDR → fleet promoter GATE BLOCK → sit-gate/fleet-green never posted, mis-surfaced upstream
      as a stuck/"merge_conflict" promotion PR — no actual git conflict existed, `mergeable_state=blocked` not `dirty`).
      **Second-order finding**: `main-backmerge-to-ldr.yml` on this repo had ALSO been silently unschedulable since the
      same 2026-08-05 break (its own copy carried the broken placeholder), so every LDR→main promotion since then never
      backmerged into LDR — main and LDR diverged on `Dockerfile`'s `BASE_IMAGE_DIGEST` (LDR kept auto-refreshing via
      `update-dependency-version.yml`, main never got backmerged the older value's supersession), producing a SECOND,
      genuine merge conflict on the very next promote PR (#316) right after the first fix landed. Root-caused +
      resolved: fixing the workflow YAML alone is NOT sufficient per affected repo — `main-backmerge-to-ldr.yml` must
      also be manually re-dispatched (`gh workflow run main-backmerge-to-ldr.yml --ref live-defi-rollout`) to reconcile
      any accumulated main/LDR drift BEFORE the next promote-PR gate re-check, or the fleet promoter will hit the same
      "stuck_promotion_pr" class again on a fresh conflict. (Learned the hard way: my first attempt resolved the
      conflict by pushing a merge commit directly onto the promoter's frozen per-SHA promote branch
      `promote/<repo>/<sha>` — this breaks the frozen-head invariant since the ref's own name encodes the SHA it's
      pinned to, so the promoter's `sit-gate/fleet-green` status post landed on the stale name-SHA instead of the new
      tip and never satisfied the actual PR head's required check. Correct fix: resolve on `live-defi-rollout` itself
      via the backmerge workflow, then let the next promoter tick mint a fresh, correctly-named frozen-head ref.)
      Verified fully resolved: `batch-live-reconciliation-service` main and LDR are now tree-identical
      (`427541269dd8...`), `quality-gates-v2` + `main-backmerge-to-ldr` both green on `main` (push run
      31162503341/31162503702), zero open PRs. (conflict_resolver agt-8289f1, 2026-08-07)
- [ ] [DEVOPS] P1. Re-roll + ship for the other 6 locally-confirmed repos: client-reporting-api, deployment-api,
      features-service, fund-administration-service, ibkr-gateway-infra, instruments-service (same recipe as above, one
      commit+push per repo). **Also check each for accumulated main/LDR drift from the second-order
      `main-backmerge-to-ldr.yml` break above** — after the workflow-template re-roll, manually dispatch
      `gh workflow run main-backmerge-to-ldr.yml --ref live-defi-rollout` for each repo BEFORE relying on the fleet
      promoter's next tick, since any push-to-main backmerge since 2026-08-05 may have silently failed to schedule.
- [ ] [SCRIPT] P2. Sweep the remaining ~14 fleet repos not locally checked out here (full list in
      `workspace-manifest.json`) for the same broken `runs-on: { { RUNS_ON } }` pattern in their
      `.github/workflows/*.yml`, and re-roll any that are affected.
- [ ] [SCRIPT] P3. Consider adding a template-content lint to `check-action-pins.py`'s pre-flight pass (or a new
      lightweight pre-flight check in `rollout-workflow-templates.sh`) that `yaml.safe_load`s each flat-copy template
      after prettier would run on it, so a future prettier-mangled placeholder fails the ROLLOUT script's own pre-flight
      instead of silently propagating to 26 repos again.
- [ ] [DEVOPS] P2. Investigate: after `greeks-service@f5a63a8` landed on LDR (content/TIER-A/SIT/LABEL-CHECK all PASS
      per `scripts/cicd/ldr_to_main_fleet_promote.sh --repo greeks-service` re-runs 31156978197 + 31157072912), the
      stale promotion PR #420 (head=`promote/greeks-service/49b92a1a7ca0`, the pre-fix SHA) was NOT superseded by a
      fresh per-SHA ref/PR at `f5a63a8` — the run's own summary tallied `Promoted (0)`/`Blocked (0)`/`Conflicted (0)`/
      `Auto-merge ARM FAILED (0)` for the single `ONLY_REPO=greeks-service` item despite every gate log-line reading
      PASS, i.e. `process_repo` appears to have exited without ever reaching a `_done` call (same silent-drop SHAPE as
      `ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md`, but that doc's known trigger
      — a bare `return 0` after a failed `gh pr create` with no open PR — is already hardened at
      `ldr_to_main_fleet_promote.sh:1096-1105`, so this looks like a DIFFERENT gap, possibly `ONLY_REPO`-mode-specific
      or a race in the frozen-head ref-creation/PR-create path). Not blocking — the repo's actual gate is fixed +
      verified green directly (`quality-gates-v2` run 31157269647 on `live-defi-rollout`, and the un-scoped fleet cron
      will eventually pick it up too) — but the promote-PR non-supersession itself may be a live bug worth its own
      root-cause pass. (agt-5f8afe, cicd escalation, 2026-08-07)

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` (gate set / quickmerge / workflow templates)
