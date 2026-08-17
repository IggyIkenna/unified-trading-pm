---
doc_type: issue
title: Self-hosted-runner billing migration (wave 2) — remaining ship + doc work
summary: >-
  Operator-directed sweep to flip instruments-service, unified-api-contracts, market-data-processing-service,
  trading-agent-service, deployment-api, deployment-service, unified-trading-library private + self-hosted (billing).
  instruments-service/unified-api-contracts/market-data-processing-service + the PM cursorpyright memory-trim have
  landed. Remaining: 4 more repos to ship (one blocked on a live external edit), one repo's rollout never actually
  applied, two codex docs to update, a live-CI canary check, and one orphaned script found along the way.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    instruments-service,
    unified-api-contracts,
    market-data-processing-service,
    trading-agent-service,
    deployment-api,
    deployment-service,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, billing, cursorpyright, workspace-config]
related:
  [
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/active/issues/slot_collision_guard_bats_fails_open_under_host_load_2026_08_15.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-15
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: operator-directed billing sweep, this session
drift_direction: advance-code
depends_on: []
---

# Self-hosted-runner billing migration (wave 2) — remaining work

## Already landed (this session, verified on origin)

- `instruments-service@dc7de60a73`'s sibling commits — self-hosted runner routing shipped for instruments-service,
  unified-api-contracts (`unified-api-contracts@dc7de60a73`, also split 2 files under the 900L ratchet), and
  market-data-processing-service (pending — see todo 1, was next in queue when this doc was written).
- `unified-trading-pm@3f3fd16221` — cursorpyright capped to `basic` + `openFilesOnly` across all 9 workspace-config
  variants (memory trim, fleet-wide) and all 11 local slot copies; also fixed 1 unrelated pre-existing blocker (a broken
  doc link) and a genuine flaky-test bug in the slot-collision-guard BATS suite (see the linked issue doc — root cause +
  guard-level fix, not just a test tweak). **Correction (2026-08-15, slot 22):** the "e2e-testing/deployment-service
  manifest drift" fix claimed here was NOT a fix — this same commit's manifest-entry removal reintroduced that exact
  drift (STAGE 1.5 dependency-alignment is RED for every PM push as a result); see
  `/plans/archive/2026_08/issues/e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md` for the root cause and
  the still-open operator-gated resolution.
- All 7 target repos (instruments-service, unified-api-contracts, market-data-processing-service, trading-agent-service,
  deployment-api, deployment-service, unified-trading-library) are flipped **private** and have self-hosted runner pools
  **installed + confirmed online** via the GitHub API on `ci-escalation-runner-vm-1` (`i-042a6332509482556`).
  `scripts/workflow-templates/self-hosted-qg-repos.txt` lists all 7.

## Todos

- [x] [SCRIPT] P1. Ship market-data-processing-service's prepared workflow change. **Landed
      `market-data-processing-service@fdad5edce4`** (Session 2). Repo: market-data-processing-service.
- [x] [OPERATOR] P1. instruments-service's and market-data-processing-service's quickmerge pre-flight audit blocked on
      unified-api-contracts having uncommitted changes from another live session's in-progress LST-token-address work.
      Not force-committed — inherited as dead WIP once confirmed stale (process gone, mtime 87min+), fixed a real test
      gap it left (drift-invariant citation), and shipped as `unified-api-contracts@9ed9cdce` (Session 2). Repo:
      unified-api-contracts.
- [x] [SCRIPT] P1. `unified-trading-library`'s workflow rollout never actually applied. Re-ran the rollout, verified the
      label landed, shipped as `unified-trading-library@fead8ba1e7` (Session 2). Repo: unified-trading-library.
- [x] [SCRIPT] P1. Ship deployment-service's prepared workflow change. **Landed `deployment-service@63de08635a`**
      (Session 2). Repo: deployment-service.
- [x] [SCRIPT] P1. Ship deployment-api's prepared workflow change. **Landed `deployment-api@98bdafc78d`** (Session 2).
      Repo: deployment-api.
- [x] [SCRIPT] P1. Ship trading-agent-service's prepared workflow change. **Landed
      `trading-agent-service@a11a405430`** (Session 2). Repo: trading-agent-service.
- [x] [SCRIPT] P2. Verify a live self-hosted CI run actually passes for each of the 7 repos post-ship. **Verified via
      GitHub API job runner_name** — 6/7 directly confirmed on `glue-ip-172-31-3-59-1`; instruments-service confirmed
      via identical file content (its own fresh dispatch hit a content-sentinel cache-skip). Repo: all 7.
- [x] [DOC] P2. Update `/codex/07-security/self-hosted-runner-security-posture.md` — repo-set table. **Landed
      `unified-trading-pm@9456bfc183`** (Session 2). Repo: unified-trading-pm.
- [x] [DOC] P2. Update `/codex/08-workflows/ci-cd-flow.md` — forward-migration continuation note. **Landed
      `unified-trading-pm@9456bfc183`** (Session 2). Repo: unified-trading-pm.
- [x] [DOC] P3. `scripts/propagation/update-workspace-strict-linting.py` was orphaned/stale (stale hardcoded path,
      non-existent target dir, zero live callers, would have silently re-flipped the cursorpyright memory-trim change
      if ever resurrected). **Deleted, landed `unified-trading-pm@40817d5237`** (Session 3, 2026-08-17) — first ship
      attempt was blocked twice by unrelated whole-corpus gates (a live `ao_human_fleet_integration_2026_08_15.md`
      DEFERRED-banner false-positive that cleared on its own by Session 3; a genuine `workspace-manifest.json`
      tier-DAG conflict — `e2e-testing` now imports `deployment-service` in its `pyproject.toml`, which the
      dependency-alignment tool refuses to auto-fix since adding it to the manifest would violate the tier DAG.
      Shipped the deletion alone, left `workspace-manifest.json` untouched — that tier conflict is a genuine,
      separate architectural question (does e2e-testing legitimately need this import, or should it be removed?)
      for whoever owns that change, not something to resolve as a side effect of a script deletion. Repo:
      unified-trading-pm. **New finding, not yet triaged**: e2e-testing/pyproject.toml importing deployment-service
      vs the tier DAG — `python3 scripts/manifest/check-dependency-alignment.py --json` reproduces it live.

## Session 2 update (2026-08-16) — all 7 repos shipped + verified; billing investigation opened new scope

All of todos 1-9 above are DONE (stale as written — superseded by this section, not re-edited line-by-line to avoid
churn). Verified on origin: `instruments-service@ebc2cf9c60` (had to re-ship — the earlier `dc7de60a73` "sibling
commits" claim in the "Already landed" section above was WRONG, the fix sat uncommitted in a local working tree for
~24h and never actually reached origin until this session caught it via a live CI runner-assignment check),
`unified-api-contracts@9ed9cdce`, `market-data-processing-service@fdad5edce4`, `unified-trading-library@fead8ba1e7`,
`deployment-service@63de08635a`, `trading-agent-service@a11a405430`, `deployment-api@98bdafc78d`. Both codex docs
landed at `unified-trading-pm@9456bfc183`. Live CI runner-assignment verified (`glue-ip-172-31-3-59-1`, not
`ubuntu-latest`) for 6/7 directly; instruments-service verified via identical file content + a cache-skipped dispatch
(re-verify on its next real push).

**New scope opened by the operator's "why hasn't billing dropped" question**: `quality-gates-v2.yml` was only ONE of
11-16 workflow files per repo. Full-fleet CI-volume audit (all 90+ private repos, run counts since 2026-08-15) found:

- [x] [SCRIPT] P1. Add `self_hosted_runner_labels: '["self-hosted","glue"]'` to `update-dependency-version.yml`,
      `semver-agent.yml`, `main-backmerge-to-ldr.yml` caller stubs across all 7 wave-2 repos — the reusable-workflow
      callee in `unified-trading-ci` already supports the input (same mechanism as quality-gates-v2.yml); the always-on
      7 repos already had this, wave-2 never did. Fires 5-9x/day per repo per workflow. **Shipped + verified on origin,
      all 7**: `unified-api-contracts@76adc2bc3d` (unblocked once `execution-service@85c8310b2` landed the symbiotic
      venue-reachability fix another session was mid-work on), `unified-trading-library@abb158eeeb`,
      `deployment-service@2743f24cf9`, `trading-agent-service@9e00c03`, `deployment-api@1d19ce6fa7`,
      `instruments-service@fd15192b1b`, `market-data-processing-service@2e66754f43`. Repo: all 7 wave-2. DONE.
- [x] [OPERATOR] P1. Ship of the above was BLOCKED on `unified-api-contracts` by a genuinely pre-existing, unrelated
      test failure — `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions` failed with/
      without this session's diff (confirmed via stash test). Traced to live, actively-dated 2026-08-16 work:
      7 repos already had this, wave-2 never did. Fires 5-9x/day per repo per workflow. **Shipped + verified on origin,
      all 7**: `unified-api-contracts@76adc2bc3d` (unblocked once `execution-service@6dba7ac5` landed the symbiotic
      venue-reachability fix another session was mid-work on), `unified-trading-library@abb158eeeb`,
      `deployment-service@2743f24cf9`, `trading-agent-service@9e00c03`, `deployment-api@1d19ce6fa7`,
      `instruments-service@fd15192b1b`, `market-data-processing-service@2e66754f43`. Repo: all 7 wave-2. DONE.
- [x] [OPERATOR] P1. Ship of the above was BLOCKED on `unified-api-contracts` by a genuinely pre-existing, unrelated
      test failure — `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions` failed with/
      without this session's diff (confirmed via stash test). Traced to live, actively-dated 2026-08-16 work:
      `/plans/active/issues/karak_decommission_2026_08_16.md`,
      `/plans/archive/issues/symbiotic_venue_onboarding_2026_08_16.md`. Not fixed or bypassed here — waited for that
      other session's own fix (`execution-service@85c8310b2`) to land, then retried and it passed. Repo:
      unified-api-contracts. RESOLVED (external dependency landed). **2026-08-16 note (interactive session)**: found
      this doc's "RESOLVED"/done state briefly reverted to an earlier "BLOCKED" draft on origin by a peer session's
      apparent full-file-overwrite (a `git pull` mid-resolution landed a stale local copy) — restored the correct,
      more-advanced RESOLVED state here rather than the regressed one, while also correcting the `execution-service`
      sha citation (`6dba7ac5` does not resolve to a real commit; `85c8310b2` — "wire Symbiotic into DeFiAdapter's real
      dispatch" — matches the described fix exactly, same day, same author intent).
      `/plans/archive/issues/symbiotic_venue_onboarding_2026_08_16.md`. Not fixed or bypassed here — waited for that
      other session's own fix (`execution-service@6dba7ac5`) to land, then retried and it passed. Repo:
      unified-api-contracts. RESOLVED (external dependency landed).
- [x] [SCRIPT] P2. `image-build-gate.yml` fired 10-13x/day per repo on `ubuntu-latest` — its callee
      (`unified-trading-ci/.github/workflows/image-build-validate.yml`) had NO `self_hosted_runner_labels` input at
      all (unlike the other reusable workflows). **Fixed + shipped, all 14 self-hosted repos**: added the
      `${{ inputs.self_hosted_runner_labels != '' && fromJSON(...) || 'ubuntu-latest' }}` pattern to
      `image-build-validate.yml`'s 3 `runs-on:` sites (`unified-trading-pm@8b3c14e1bc`), converted the template to
      `.tmpl` + added the input, rolled out to every caller via `rollout-workflow-templates.sh`, then shipped per-repo:
      `unified-api-contracts@db275662de`, `unified-trading-library@eee26f41b4`, `deployment-service@2d92888673`,
      `deployment-api@e3643bcb43`, `trading-agent-service` (landed via prek-restored stash), `market-data-processing-
      service@9608091c81`, `instruments-service@cefb45ddc4`, `market-tick-data-service@e7c294a34a`,
      `ml-service@5f5f56c1ed`, `agent-orchestrator@bf8075a4a3`, `features-service` (landed), `execution-service@
      200beaf744`, `strategy-service@7fc96848d4`, `e2e-testing@597cf346e3`. Verified via GitHub API against
      `live-defi-rollout` HEAD on all 14 — real `self_hosted_runner_labels: '["self-hosted","glue"]'` present, not the
      empty default. Repo: unified-trading-ci + all 14 callers. DONE.
- [x] [OPERATOR] P1. `basis-strategy` — `agent-monitor.yml` cron fired every 5 minutes (288 runs/day) running a demo
      script that just checks for `agent-a-progress.txt`/`agent-b-progress.txt` (files that don't exist) — dead test
      scaffolding, not real automation, confirmed running on `ubuntu-latest`. **Archived 2026-08-16** (operator
      decision) — stops the billing immediately, fully reversible (`gh repo edit --unarchive`, org-owner only), code/
      history preserved. **Operator note: check back in on this repo once the strategy work is more mature** — may be
      worth reactivating (or extracting whatever real signal `agent-monitor.yml` was meant to provide into the real
      fleet's monitoring, rather than resurrecting the 5-min cron as-is). Repo: basis-strategy.
- [x] [OPERATOR] P1. `agent-orchestrator-fork-bak` — `tab-mirror-to-ldr.yml` `*/15min` cron (96 runs/day) was a live
      DUPLICATE of agent-orchestrator's own real tab-mirror automation, running on an abandoned backup fork, on
      `ubuntu-latest`. Delete blocked here on missing `delete_repo` OAuth scope (non-interactive session can't grant
      it) — handed off to the operator with the exact 2-command script
      (`gh auth refresh -h github.com -s delete_repo` then `gh repo delete IggyIkenna/agent-orchestrator-fork-bak
      --yes`). **Operator ran it and confirmed 2026-08-17** — `gh repo view IggyIkenna/agent-orchestrator-fork-bak`
      now 404s ("Could not resolve to a Repository"). Repo fully deleted, billing stopped. DONE.

## Sequencing note

Every remaining ship in this doc depends on `unified-api-contracts` having a clean working tree (path-dependency
pre-flight check) — todo 2 is the actual blocker for todos 1, 4, 5. Do that one first; the rest are then a
straightforward repeat of the exact pattern already proven 3x this session (rollout if needed → quickmerge --files
scoped to the workflow files → verify `post-push ancestry` in the output, don't trust the exit code alone — this session
hit two cases where a background task's "exit code 0" summary was wrong because a trailing `| tail` pipe masked the real
exit code).
