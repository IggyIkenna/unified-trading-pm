---
doc_type: issue
title:
  A failed main-backmerge-to-ldr run strands LDR indefinitely on every non-PM repo — the drift-tick safety-net is
  github.repository-scoped (PM only), so the push trigger is the only path and it never retries
summary: |
  Escalation agt-cebebf (trading-agent-service PR #459, wall_type=merge_conflict) was caused not by a code conflict but
  by a TRANSIENT GitHub Actions infrastructure failure that nothing ever re-drove. main-backmerge-to-ldr run
  32035206185 (for main@a142d0d, 2026-08-17T13:27Z) failed downloading actions/create-github-app-token@v3 with HTTP
  429 (Too Many Requests) after 3 built-in retries — no job logic ran at all. Because that workflow's only automatic
  trigger on a non-PM repo is `push: [main]`, and that push had already fired, LDR was never reconciled with main.
  LDR then kept advancing (hourly base-image digest-pin refreshes), so the NEXT promote PR conflicted on the single
  `ARG BASE_IMAGE_DIGEST` line and escalated to a conflict_resolver. Measured drift: 11h13m (2026-08-17 13:27Z →
  2026-08-18 01:38Z). The workflow's own comment claims the removed drift-tick schedule "is now handled by PM's
  branch-health.yml (every 30 min) which dispatches this workflow" — but branch-health.yml's drift-tick job dispatches
  `main-backmerge-to-ldr.yml --repo "${{ github.repository }}"`, i.e. unified-trading-pm ONLY, and its cron is hourly
  (`0 * * * *`), not every 30 min. Every non-PM `promotion_model: ldr_main` repo therefore has NO retry and NO
  safety-net for this workflow. This is a fleet-wide class, not a trading-agent-service quirk.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-ci, trading-agent-service]
scope: [engineer, admin]
tags: [ci-cd, backmerge, promotion, ldr, transient-failure, safety-net, escalation]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
    /plans/archive/2026_08/client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md,
  ]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/.github/workflows/branch-health.yml,
    unified-trading-ci/.github/workflows/main-backmerge-to-ldr.yml,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: ci
effort: medium
drift_direction: advance-code
resolved_by:
supersedes:
superseded_by:
depends_on:
locked_by:
locked_since:
source: conflict_resolver escalation agt-cebebf (trading-agent-service PR #459), 2026-08-18
---

# A failed `main-backmerge-to-ldr` strands LDR on every non-PM repo

## What happened (measured, not inferred)

| Fact                                                                 | Evidence                                                                         |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Backmerge run for `main@a142d0d` FAILED                              | `gh run view 32035206185 --repo IggyIkenna/trading-agent-service --log-failed`   |
| Failure was transient GHA infra, not repo logic                      | `429 (Too Many Requests)` downloading `actions/create-github-app-token@v3`; `Failed to download archive ... after 3 attempts` — no job step ever ran |
| Nothing re-drove it                                                  | `main-backmerge-to-ldr.yml` triggers = `push: [main]` + `workflow_dispatch` only |
| The claimed safety-net does not cover this repo                      | `branch-health.yml` drift-tick runs `gh workflow run main-backmerge-to-ldr.yml --repo "${{ github.repository }}"` — resolves to `unified-trading-pm`, never a fleet repo |
| The claimed cadence is also wrong                                    | `branch-health.yml` cron is `0 * * * *` (hourly), not "every 30 min" as the caller-stub comment states |
| Resulting drift                                                      | 11h13m — main@`a142d0d` (2026-08-17 13:27Z) unreconciled until this escalation resolved it (2026-08-18 01:38Z) |
| Downstream symptom                                                   | PR #459 `mergeable: CONFLICTING` / `mergeStateStatus: DIRTY` on one line (`ARG BASE_IMAGE_DIGEST`) |

## Why the conflict looked like a code conflict but was not

`main` carried exactly one file's difference from LDR: `Dockerfile`'s auto-refreshed `ARG BASE_IMAGE_DIGEST`. `main`'s
value (`2c86cca5…`) is byte-identical to LDR@`0d447a8` — the very commit `main`'s squash names in its
`Promoted-From-LDR:` trailer, and an ancestor of LDR's tip. LDR had since advanced that same line three times
(`faae1ea`, `8723665`, `b19c626` → `75510abb…`). So `main` held ZERO work LDR lacked; it held a stale snapshot of a
monotonically-refreshed pin. Any repo whose LDR carries a bot-refreshed single-valued line will manufacture this exact
conflict shape whenever a backmerge is skipped — the churn rate (hourly here) sets how fast it appears.

## Resolution applied for this instance (escalation agt-cebebf)

Back-merged `origin/main` into `live-defi-rollout` keeping LDR's newer pin (the older value would REGRESS the
base-image pin), QG exit 0, pushed `0bf06fb`, fast-forwarded PR #459's head, armed v2-gated auto-merge. That fixes the
symptom for one repo/one tick — it does not close any todo below.

## Todos

- [x] ✅ [CI] P1. Landed as `unified-trading-pm@96c163347f` (verified on `origin/live-defi-rollout`; live non-PM dispatch test: `trading-agent-service` run `32303502126`). Completed in the batch17 work split (item 1) (na-eligibility-audit 2026-08-18). Make the `branch-health.yml` drift-tick safety-net FLEET-WIDE instead of `github.repository`-scoped:
      dispatch `main-backmerge-to-ldr.yml` for every `promotion_model: ldr_main` repo in `workspace-manifest.json`
      (the same repo-list read the AR-lag job in that file already does), not just `unified-trading-pm`. Without this,
      a single transient GHA failure strands any fleet repo's LDR until a human or a conflict_resolver notices.
      Provenance: escalation agt-cebebf, 2026-08-18.
- [x] ✅ [CI] P2. Landed in 25 caller stubs on `origin/live-defi-rollout` (verified old-comment count 0): `agent-orchestrator@e674c4d0`, `alerting-service@89f81d1`, `batch-live-reconciliation-service@91492a0`, `client-reporting-api@f320528`, `deployment-api@c38b675`, `deployment-service@d2fe2045`, `deployment-ui@cf3072a`, `e2e-testing@eac861e`, `execution-service@196b52dd`, `features-service@25af96cb`, `fund-administration-service@5b9d40a`, `greeks-service@c240e8e`, `ibkr-gateway-infra@657d541`, `instruments-service@6558be48`, `market-data-processing-service@63c9cd15`, `market-tick-data-service@98e3e7e1`, `ml-service@0aec46f`, `strategy-service@f7391889`, `system-integration-tests@44d0a05`, `trading-agent-service@a31f3f5`, `unified-api-contracts@70b0b200`, `unified-trading-api@7dffc4d`, `unified-trading-library@5ceddb2a`, `unified-trading-pm@0369723950`, `unified-trading-system-ui@b3f6b9f3`. Completed in the batch17 work split (item 2) (na-eligibility-audit 2026-08-18, fix-location pointer corrected during extraction — see that item). Fix the misleading comment in the `main-backmerge-to-ldr.yml` caller stub — it states the drift-tick is
      "now handled by PM's branch-health.yml (every 30 min) which dispatches this workflow" and that "for non-PM repos
      the push trigger covers the common case". Both halves mislead: the cadence is hourly, and the dispatch never
      reaches non-PM repos at all, so the push trigger is not a "common case" fallback but the ONLY path. The misleading text lives in each repo's thin caller stub at `.github/workflows/main-backmerge-to-ldr.yml`; update those
      per-repo stubs (the reusable workflow in `unified-trading-ci` carries no such comment). Provenance: this comment directly misled the agt-cebebf investigation.
      Depends on the P1 todo landing first (the corrected wording depends on what the net actually becomes).
- [x] ✅ [CI] P2. Landed as `unified-trading-pm@2ead733819` (verified on `origin/live-defi-rollout`; YAML parse, embedded-shell `bash -n`, commit-hook/provenance, and ancestry checks passed; plan-flip commit `6cabee1015`). Completed in the batch17 work split (item 3) (na-eligibility-audit 2026-08-18). Add a detection surface for a FAILED backmerge specifically, so this class is caught by monitoring
      rather than by a downstream promote PR conflicting: `branch-health.yml`'s lag-monitor already computes LDR↔main
      lag — assert additionally that the most recent `main-backmerge-to-ldr` run per repo did not end `failure`, and
      route it through the existing `notify-slack.yml` carrier with a state-transition `dedup_key`. Provenance:
      escalation agt-cebebf, 2026-08-18.
- [ ] [CI] P3. Evaluate whether `actions/create-github-app-token` (and the other third-party actions these reusable
      workflows pull per run) should be resolved from a warm local cache on the self-hosted `glue` runners, so a
      codeload 429 cannot fail a run before any job logic executes. Scope this as an investigation — the answer may be
      "accept the transient and rely on the P1 retry net". Provenance: escalation agt-cebebf, 2026-08-18.

## Progress Log

### 2026-08-18 — filed from conflict_resolver escalation agt-cebebf (slot 7)

Resolved trading-agent-service PR #459 (see "Resolution applied" above), then traced WHY the conflict existed rather
than stopping at the merge. The backmerge automation had failed 11h earlier on a transient 429 and nothing in the
system re-drove it. Verified the safety-net claim against `branch-health.yml` directly rather than trusting the caller
stub's comment — the dispatch is `github.repository`-scoped, confirming non-PM repos are uncovered. Both arm-gates
(strict-quickmerge provenance over `0d447a8..origin/live-defi-rollout`, and Tier-A `ci_status` = `MAIN_GREEN`) were
checked clean before auto-merge was armed, per `ldr_to_main_fleet_promote.sh`'s `provenance_check_ok()` /
`tier_a_merge_gate_ok()`.

- **na-eligibility-audit 2026-08-18** [body-hash:ef6e0dc9d0973bd1]: RECLASSIFY (per-todo split) -- 3 of 4 open todos are bounded/deterministic with cited existing patterns (workspace-manifest.json repo-list read, notify-slack.yml dedup_key carrier). Conflict-checked against 7 other active-plan hits on main-backmerge-to-ldr/branch-health.yml (different axes: git-ref hygiene, CI cost/billing, stuck-queued-run cleanup, template-hosting location, self-hosted-runner migration cost, an already-shipped different-DECISION escalation-resolution poll) -- none claims this scope/comment/detection-surface work. Completed in the batch17 work split (items 1-3). Remaining 1 item stays assigned_vm: NA: todo 4 (evaluate a warm local action-cache), explicitly self-framed in-doc as an open investigation with an uncertain answer. Corrected a stale fix-location pointer in todo 2 while extracting (unified-trading-pm/scripts/workflow-templates/ no longer hosts main-backmerge-to-ldr.yml; migrated to unified-trading-ci 2026-08-07/08). Cross-cutting tranche audit.
- **context-scout 2026-08-19**: populated/refreshed context_scope (4 entries).
- **2026-08-20 (finalize review, slot 18)**: re-verified the three extracted items against landed commits and current `origin/live-defi-rollout`, then added concrete commit/run evidence to the three checkbox citations above. The source doc intentionally remains active with only the independent warm action-cache investigation open.

## Triage recipe for the next instance of this class

A promote PR reported as `merge_conflict` is NOT necessarily a code conflict. Before resolving anything, spend three
commands separating "two agents genuinely wrote different code" from "a backmerge was skipped and the target is a stale
snapshot of the source". They need opposite responses — the first is a merits merge, the second means the AUTOMATION
failed and resolving the PR alone leaves the cause live to recur next tick.

```bash
# 1. Shape: how much real content actually differs?
gh api repos/IggyIkenna/$REPO/compare/main...$HEAD --jq '{ahead:.ahead_by, behind:.behind_by, files:(.files|length)}'
# files==0            -> drain-noise, close
# files small + behind>0 -> suspect a skipped backmerge, continue to 2

# 2. Provenance: does the target name the source commit it was squashed FROM?
git log -1 --format='%b' origin/main | grep Promoted-From-LDR
git merge-base --is-ancestor <that-sha> origin/live-defi-rollout   # TRUE => target holds zero source-absent work

# 3. Cause: did the backmerge that should have reconciled them actually run?
gh run list --repo IggyIkenna/$REPO --workflow main-backmerge-to-ldr.yml --limit 5
```

If step 2 is TRUE, the differing lines are by definition a stale snapshot, and the resolution is decided by which side
is NEWER — not by reading the diff on its merits. Step 3 is the one that turns a symptom fix into a root-cause fix; it
is also the step that is easy to skip once the PR is green.

## Lessons / measurement traps hit while diagnosing this

- **A workflow's own comment is not evidence of what it does.** `main-backmerge-to-ldr.yml`'s stub asserts a 30-minute
  fleet-wide safety-net; reading `branch-health.yml` showed an hourly, `github.repository`-scoped dispatch. The claim
  was wrong on both cadence and scope. Read the dispatching workflow, not the dispatched one's description of it.
- **`gh pr checks` / the check-runs REST API 403 on the workspace PAT** (`Resource not accessible by personal access
  token`). `gh run list --branch <head-branch>` returns the same information and does work — use it instead of
  concluding the checks are missing.
- **`promote_provenance_range.py --base ...` is ambiguous** (`--base-branch` vs `--base-ref`) and errors out; pass
  `--base-branch main --cwd .` explicitly.
- **`ci_status_store.py get-doc` fails open, not loud, on the system python** — it prints
  `Firestore unavailable (ModuleNotFoundError: No module named 'google')` and emits `{}`. An empty doc is NOT
  `ci_status: clean`; run it from the repo `.venv` or the Tier-A gate check is silently meaningless.
- **`safe-doc-push` printing `✅ Pushed <sha>` is not proof the file landed** — in this run it also quarantined a dirty
  tree into a named stash on the way (the "extreme stash pile" path, see
  `/plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md`, which
  documents that path dropping RENAMED-file content). Verify with
  `git cat-file -e origin/live-defi-rollout:<path>` plus a content spot-check, per the workspace's own
  `ahead=0 + clean tree != landed` rule.
