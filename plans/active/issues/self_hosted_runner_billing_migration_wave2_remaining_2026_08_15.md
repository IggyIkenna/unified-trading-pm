---
doc_type: issue
title: Self-hosted-runner billing migration (wave 2) — remaining ship + doc work
summary: >-
  Operator-directed sweep to flip instruments-service, unified-api-contracts, market-data-processing-service,
  trading-agent-service, deployment-api, deployment-service, unified-trading-library private + self-hosted (billing).
  instruments-service/unified-api-contracts/market-data-processing-service + the PM cursorpyright memory-trim have
  landed. Remaining: 4 more repos to ship (one blocked on a live external edit), one repo's rollout never actually
  applied, two codex docs to update, a live-CI canary check, and one orphaned script found along the way.
status: open
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
  `/plans/active/issues/e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md` for the root cause and
  the still-open operator-gated resolution.
- All 7 target repos (instruments-service, unified-api-contracts, market-data-processing-service, trading-agent-service,
  deployment-api, deployment-service, unified-trading-library) are flipped **private** and have self-hosted runner pools
  **installed + confirmed online** via the GitHub API on `ci-escalation-runner-vm-1` (`i-042a6332509482556`).
  `scripts/workflow-templates/self-hosted-qg-repos.txt` lists all 7.

## Todos

- [ ] [SCRIPT] P1. Ship market-data-processing-service's prepared workflow change
      (`.github/workflows/quality-gates-v2.yml` + `notify-slack.yml`, already rolled out locally, uncommitted) via
      `bash scripts/quickmerge.sh "ci: route quality-gates-v2 to self-hosted glue runner (private-repo billing migration)" --agent --files '.github/workflows/quality-gates-v2.yml .github/workflows/notify-slack.yml'`.
      Was next in the ship queue; blocked by todo 2 below (pre-flight dependency check on unified-api-contracts). Repo:
      market-data-processing-service.
- [ ] [OPERATOR] P1. instruments-service's and market-data-processing-service's quickmerge pre-flight audit BLOCKS on
      unified-api-contracts having uncommitted changes — but those changes
      (`unified_api_contracts/internal/domain/defi/solana.py`, `unified_api_contracts/registry/lst_token_addresses.py`,
      `tests/unit/test_lst_token_addresses.py`) are **another live session's in-progress LST-token-address work**, not
      mine to commit (measured live — mtime 43s at last check, i.e. actively being edited). Do not `git add -A` this —
      it would land incomplete/unintended work under an unrelated commit message. Wait for that session to commit its
      own work, or ask whoever owns it to pause/land it, then retry the blocked ships above. Repo:
      unified-api-contracts.
- [ ] [SCRIPT] P1. `unified-trading-library`'s workflow rollout never actually applied — live-checked
      `self_hosted_runner_labels: ""` (empty) in its `.github/workflows/quality-gates-v2.yml` despite being one of the 4
      repos in the "second batch" this session ran `rollout-workflow-templates.sh --repo unified-trading-library`
      against. Re-run the rollout
      (`cd unified-trading-pm && bash scripts/workflow-templates/rollout-workflow-templates.sh --repo unified-trading-library`),
      verify the label actually lands this time, then ship via quickmerge (same pattern as the others). Repo:
      unified-trading-library.
- [ ] [SCRIPT] P1. Ship deployment-service's prepared workflow change (same pattern as todo 1). Note: repo also has an
      untracked `_.gstmp` file (looks like a stray GCS resumable-upload temp artifact, not mine) — leave it alone, don't
      include it in `--files`. Repo: deployment-service.
- [ ] [SCRIPT] P1. Ship deployment-api's prepared workflow change (same pattern). Depends on deployment-service landing
      first per its own `dep_repos` (`unified-trading-library unified-api-contracts deployment-service`). Repo:
      deployment-api.
- [ ] [SCRIPT] P1. Ship trading-agent-service's prepared workflow change (same pattern). Repo: trading-agent-service.
- [ ] [SCRIPT] P2. Verify a live self-hosted CI run actually passes for each of the 7 repos post-ship — trigger or wait
      for a real `quality-gates-v2` run and confirm it claims a runner on `ci-escalation-runner-vm-1` (not
      `ubuntu-latest`) and goes green, not just that the YAML routes there.
      `gh run list --repo IggyIkenna/<repo> --workflow quality-gates-v2.yml --limit 3` then inspect the run's job
      runner. Repo: all 7.
- [ ] [DOC] P2. Update `/codex/07-security/self-hosted-runner-security-posture.md` — the "Current self-hosted repo set"
      table (line ~60-67, last re-derived 2026-08-09) names only the original 7 always-on repos (`agent-orchestrator` ·
      `strategy-service` · `e2e-testing` · `features-service` · `market-tick-data-service` · `execution-service` ·
      `ml-service`); add the 7 new ones once all are confirmed shipped + green (todo 6). Repo: unified-trading-pm.
- [ ] [DOC] P2. Update `/codex/08-workflows/ci-cd-flow.md` (~line 1240-1287) — the reusable-workflow-host table and
      "Second wave" migration narrative cite `self_hosted_runner_public_repo_revert_2026_08_05.md` as the governing
      history; add a continuation note pointing at this doc + the forward migration once shipped. Repo:
      unified-trading-pm.
- [ ] [DOC] P3. `scripts/propagation/update-workspace-strict-linting.py` is orphaned/stale — found while investigating
      the cursorpyright memory-trim change. Its hardcoded path
      (`/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/...`) doesn't match this machine's actual
      layout (`/Users/ikennaigboaka/Code/unified-trading-system-repos/...`), and its target directory
      (`.cursor/workspace-configs/`) doesn't exist — the real canonical workspace-config files live at
      `unified-trading-pm/cursor-configs/*.code-workspace` (confirmed via `check_workspace_code_workspace_drift.py`'s
      own docstring: "Canonical SSOT ... the file the repos-root symlink chain actually loads"). Last real content edit
      `2dc131639f` (2026-06-23, a mechanical lifecycle-marker stamp only — no functional change since 2026-03-07). Not
      referenced anywhere else in the codebase (`grep -rl update-workspace-strict-linting` finds nothing but itself).
      Also worth noting: it still hardcodes `cursorpyright.analysis.typeCheckingMode: strict` — if ever resurrected
      without updating that, it would silently re-flip this session's memory-trim change. Either delete it (fully
      superseded, zero live callers) or fix the path + target dir if someone believes it's still needed — operator call,
      not mine to make unilaterally. Repo: unified-trading-pm.

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
      7 repos already had this, wave-2 never did. Fires 5-9x/day per repo per workflow. Edits applied to all 7 repos;
      shipped: unified-api-contracts BLOCKED (see below). Repo: all 7 wave-2.
- [ ] [OPERATOR] P1. Ship BLOCKED on `unified-api-contracts` by a genuinely pre-existing, unrelated test failure —
      `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions` fails with/without this session's
      diff (confirmed via stash test). Traces to live, actively-dated 2026-08-16 work:
      `/plans/active/issues/karak_decommission_2026_08_16.md`,
      `/plans/active/issues/symbiotic_venue_onboarding_2026_08_16.md`. Two identical consecutive quickmerge failures —
      not mine to fix (domain wiring decision) or bypass. Retry once that work lands. Once unified-api-contracts clears,
      unified-trading-library + deployment-service + trading-agent-service + deployment-api need the same 3-workflow
      ship (edits already applied locally to all 4, just uncommitted). Repo: unified-api-contracts (blocker),
      unified-trading-library, deployment-service, trading-agent-service, deployment-api (downstream).
- [ ] [SCRIPT] P2. `image-build-gate.yml` fires 10-13x/day per repo on `ubuntu-latest` — its callee
      (`unified-trading-ci/.github/workflows/image-build-validate.yml`) has NO `self_hosted_runner_labels` input at
      all (unlike the other reusable workflows), so this needs real work: add the
      `${{ inputs.self_hosted_runner_labels != '' && fromJSON(...) || 'ubuntu-latest' }}` pattern (already used
      elsewhere in that same repo) to its 3 `runs-on:` sites, then add the input to every caller's
      `image-build-gate.yml` stub (managed via `scripts/workflow-templates/image-build-gate.yml` +
      `rollout-workflow-templates.sh`, so a template-level fix propagates fleet-wide). Higher blast radius than the
      other fixes: `unified-trading-ci` is public and fleet-critical — verify on a representative consumer + across
      branches before considering done (rule 11 territory). Confirmed still charges the CALLING repo's billing despite
      living in a public repo — GH Actions bills the caller, not the workflow-definition host. Repo: unified-trading-ci
      + template rollout to all callers.
- [x] [OPERATOR] P1. `basis-strategy` — `agent-monitor.yml` cron fired every 5 minutes (288 runs/day) running a demo
      script that just checks for `agent-a-progress.txt`/`agent-b-progress.txt` (files that don't exist) — dead test
      scaffolding, not real automation, confirmed running on `ubuntu-latest`. **Archived 2026-08-16** (operator
      decision) — stops the billing immediately, fully reversible (`gh repo edit --unarchive`, org-owner only), code/
      history preserved. **Operator note: check back in on this repo once the strategy work is more mature** — may be
      worth reactivating (or extracting whatever real signal `agent-monitor.yml` was meant to provide into the real
      fleet's monitoring, rather than resurrecting the 5-min cron as-is). Repo: basis-strategy.
- [ ] [OPERATOR] P1. `agent-orchestrator-fork-bak` — `tab-mirror-to-ldr.yml` `*/15min` cron (96 runs/day) is a live
      DUPLICATE of agent-orchestrator's own real tab-mirror automation, running on what looks like an abandoned backup
      fork, on `ubuntu-latest`. **Operator wants this repo permanently DELETED** (not archived) — attempted via
      `gh repo delete IggyIkenna/agent-orchestrator-fork-bak --yes`, blocked: current token lacks the `delete_repo`
      OAuth scope, which needs an interactive `gh auth refresh -h github.com -s delete_repo` (cannot be completed in a
      non-interactive session). Operator needs to either run that refresh + hand off, or delete directly via GitHub UI
      (Settings → Danger Zone). Until then this repo is STILL LIVE and billing. Repo: agent-orchestrator-fork-bak.

## Sequencing note

Every remaining ship in this doc depends on `unified-api-contracts` having a clean working tree (path-dependency
pre-flight check) — todo 2 is the actual blocker for todos 1, 4, 5. Do that one first; the rest are then a
straightforward repeat of the exact pattern already proven 3x this session (rollout if needed → quickmerge --files
scoped to the workflow files → verify `post-push ancestry` in the output, don't trust the exit code alone — this session
hit two cases where a background task's "exit code 0" summary was wrong because a trailing `| tail` pipe masked the real
exit code).
