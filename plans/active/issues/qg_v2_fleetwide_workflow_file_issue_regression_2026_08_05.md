---
doc_type: issue
title: >-
  quality-gates-v2 fails fleet-wide with GitHub's generic "workflow file issue" (zero jobs created) — ROOT CAUSE
  CONFIRMED 2026-08-05: PUBLIC repos cannot use PM's PRIVATE reusable workflows (public→private hard block)
summary: >-
  While chasing an unrelated LDR->main promotion timing measurement (ci_pipeline_speed_and_cost_redesign_2026_08_05.md),
  discovered `quality-gates-v2` fails INSTANTLY (zero jobs created, no check-runs, no billable time) with GitHub's
  generic "This run likely failed because of a workflow file issue" banner. Confirmed on two independent repos
  (greeks-service PR #410, deployment-service PR #703/#705) at different times, ruling out a single-repo cause. First
  observed 2026-08-05 18:00:57Z.
summary_continued: >-
  Initial hypothesis: the newly-landed fast-checkout.sh self-hosted-runner optimization (unified-trading-pm@b656cb87b /
  23f1ad262 / 91ebc6584, 16:58-17:17 UTC 2026-08-05) — timing lined up closely, and a concurrent session was already
  live-debugging exactly that feature ("fast-checkout.sh third bug... add diagnostics for the still-unexplained
  script-not-found"). That session reverted python-quality-gates-v2.yml TWICE: a partial revert
  (unified-trading-pm@01d0353, 18:37:55Z) then a FULL restore to the exact pre-fast-checkout content
  (unified-trading-pm@28af8342, 18:45:59Z, message: "restore reusable workflow to exact last known working version
  (6c579fc)"). Verified via `git diff 6c579fce...HEAD -- .github/workflows/python-quality-gates-v2.yml` that this
  restore is BYTE-IDENTICAL to the last confirmed-working version (6c579fce, 2026-08-04) — zero diff. Despite that, a
  fresh retrigger on greeks-service's promote branch at 19:26:57Z (well after the restore landed and confirmed reachable
  from live-defi-rollout via `git merge-base --is-ancestor`) failed with the IDENTICAL signature 8 seconds later. This
  rules out "the revert just hasn't propagated yet" and means one of: (a) fast-checkout.sh was never the actual root
  cause (coincidental timing correlation with something else that broke concurrently), (b) a second, still-unidentified
  regression landed in the same window and hasn't been isolated, or (c) a genuine transient GitHub-side platform issue
  unrelated to any workspace file. `actionlint` found ZERO issues in either the reusable workflow (PM's
  python-quality-gates-v2.yml, post-revert) or the calling template (greeks-service's quality-gates-v2.yml) beyond the
  pre-existing, already-documented, explicitly non-fatal `runs-on: [self-hosted, glue]` label warning (9 such warnings
  noted as benign in main_backmerge_conflict_wall_digest_churn_2026_08_05.md Finding 6). GitHub's REST API does not
  expose the actual parse-error text for this failure class — `gh run view`, `.../check-runs`, `.../check-suites`, and
  the run-detail endpoint all come back empty or generic ("workflow file issue", no annotation body). Only the Actions
  web UI shows the real error, which was not available in this session. Left UNRESOLVED — needs someone with web UI
  access to open one of the failed run URLs below and read the actual banner/annotation text, which will very likely
  name the exact broken line/reference immediately.
status: open
nature: issue
asset_group:
  [ci] # corrected 2026-08-06 (ag-closeout-audit cross-cutting orthogonality fix) -- was [cross-cutting, ci], a genuine
  # mistag: content is GitHub Actions reusable-workflow resolution across public/private repo visibility, breaking
  # quality-gates-v2 fleet-wide -- squarely CI/CD pipeline mechanics, not cross-asset-group data-pipeline scope (no
  # data/manifest/GCS-path content anywhere in the doc). cross-cutting dropped.
stage: [meta]
repos: [unified-trading-pm, greeks-service, deployment-service, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, quality-gates-v2, reusable-workflow, workflow-file-issue, fast-checkout, regression, fleet-wide, blocking]
related:
  [
    /plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md,
    /plans/active/issues/main_backmerge_conflict_wall_digest_churn_2026_08_05.md,
    /plans/active/issues/qg_v2_digest_refresh_fastpath_gap_2026_08_05.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-05
author: unknown
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: cicd
drift_direction: unstable
source: interactive-session-2026-08-05
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    .github/workflows/python-quality-gates-v2.yml,
    .github/workflows/image-build-validate.yml,
  ]
---

# quality-gates-v2 fleet-wide "workflow file issue" regression — unresolved

## Impact (why this is P0)

**No repo can currently complete an LDR->main promotion, or land any change gated by `quality-gates-v2`.** Every promote
PR that reaches the QG check gets an instant, zero-job failure. This is a full fleet-wide CI outage for the promotion
pipeline, not a single-repo issue.

## Root cause (CONFIRMED 2026-08-05 — public→private reusable-workflow access)

**GitHub hard-blocks workflows in PUBLIC repositories from using reusable workflows in PRIVATE repositories.** The 17
repos made public by `self_hosted_runner_public_repo_revert_2026_08_05.md` (operator-confirmed intentional) all call
PM's PRIVATE reusable workflows
(`IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml @live-defi-rollout`), so GitHub fails
every such run at the parse stage with zero jobs — exactly this failure class. The fast-checkout.sh experiment and its
byte-identical revert were **irrelevant**; only the repo-visibility change (public, ~08:00-13:00Z 2026-08-05) correlates
with the break.

Evidence (escalation `agt-6a6285`, slot 4):

- Actual parse error, read from the run-page banner (the exact text the "needs UI access" note below was missing):
  `Invalid workflow file: .github/workflows/quality-gates-v2.yml#L64` →
  `error parsing called workflow ...: workflow was not found` for
  `IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout`.
- The SAME caller resolves fine from PRIVATE repos (`agent-orchestrator` v2 SUCCESS 21:27Z, `execution-service` 17:32Z)
  and fails from every PUBLIC repo (unified-api-contracts, greeks-service, deployment-service, instruments-service,
  unified-trading-library) with the identical signature.
- PM's reusable-workflow access is already `access_level: "user"` (all same-user repos granted) — the grant does NOT
  override the public→private prohibition. A fresh re-fire
  (`gh workflow run quality-gates-v2.yml --ref promote/unified-api-contracts/fe46865f0c0a`) failed with the identical
  parse error.
- `image-build-gate.yml` fails identically on the same PRs because it likewise calls a private PM reusable workflow.

**Fix direction (operator decision pending, escalation `agt-6a6285`)**: the reusable workflows
(`python-quality-gates-v2.yml` + `image-build-validate.yml` + `notify-slack.yml`) must be hosted somewhere PUBLIC (new
public repo, templates + callers re-pointed), OR the 17 repos revert to private. No GitHub setting bridges public-caller
→ private-reusable.

## What's confirmed

1. Failure signature: `gh run view <id>` shows `X This run likely failed because of a workflow file issue.` with **zero
   jobs**, **zero check-runs**, **zero billable time** — this is a workflow-resolution-level failure, not a job/script
   runtime failure.
2. Reproduced on two independent repos: greeks-service (PR #410, runs `31032720825` / `31035825349` / `31039463320`) and
   deployment-service (PR #703, run `31035144462`) — not a single-repo cause.
3. Both `greeks-service/.github/workflows/quality-gates-v2.yml` (the caller) AND
   `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml` (the reusable callee) pass `actionlint` clean
   (only the pre-existing, documented-benign `glue` runner-label warning).
4. `unified-trading-pm@28af83429444e5d6e9c3d979af73f1785c6bce82` ("restore reusable workflow to exact last known working
   version (6c579fc)") is confirmed on `live-defi-rollout` (`git merge-base --is-ancestor` = true) and is
   **byte-identical** to `6c579fce611e963165ff97aa397ada75c8614c68` (2026-08-04, the last commit before any
   fast-checkout.sh work, and the version in place during agent-orchestrator's last confirmed _successful_
   quality-gates-v2 run, ~16:53Z 2026-08-05).
5. **A fresh retrigger AFTER that restore still fails identically.** Pushed an empty commit to `greeks-service`'s
   promote branch (`promote/greeks-service/f35dc273b7df`) at `19:26:57Z` (commit `9c19b6f`); the resulting
   `quality-gates-v2` run (`31039463320`) failed with the same zero-job "workflow file issue" 8 seconds later.

## What was NOT confirmed (needs UI access) — now RESOLVED (see "Root cause" above)

The exact broken reference/line was the missing piece. GitHub's REST API gives no detail for this failure class; the
run-page banner (fetched 2026-08-05 by escalation `agt-6a6285`) provided it: `quality-gates-v2.yml#L64` →
`error parsing called workflow ...: workflow was not found`. REST-side symptoms documented below for reference:

- `gh api repos/<repo>/actions/runs/<id>/jobs` → empty.
- `gh api repos/<repo>/commits/<sha>/check-runs` → empty.
- `gh api repos/<repo>/commits/<sha>/check-suites` → shows `status: completed, conclusion: failure` for the
  `github-actions` app, no error text.

**Recommended next step**: open `https://github.com/IggyIkenna/greeks-service/actions/runs/31039463320` (or the
deployment-service equivalent) directly in a browser — the Actions UI renders the actual parse/reference error as a
banner or annotation on the failed run, which the API does not surface. That text will almost certainly point straight
at the broken line.

## Hypotheses — RESOLVED 2026-08-05 (see "Root cause" above)

- **A second regression landed in the same window**, separate from fast-checkout.sh → **RULED OUT**: the real cause is
  the repo-visibility (public) change; the fast-checkout commits and their byte-identical revert were coincidence.
- **A GitHub-side transient/platform issue** → **RULED OUT**: the failure is deterministic and persisting on every
  PUBLIC repo while PRIVATE repos succeed, so it is not transient.
- Something in `image-build-validate.yml` / `image-build-gate.yml`'s own chain → **CONFIRMED as the same root cause**:
  both call PRIVATE PM reusable workflows from the same PUBLIC caller, hence both fail identically.

## Evidence

- First observed failures: greeks-service run `31032720825` (18:00:57Z), deployment-service run `31035144462`
  (18:31:41Z, "about 9 minutes" before a repeat check at 18:40).
- Fast-checkout.sh landing commits (initial suspect): `unified-trading-pm@b656cb87b` (16:58:34 +0100), `@23f1ad262`
  (17:08:33 +0100), `@91ebc6584` (17:17:52 +0100) — all "ikennaigboaka [slot-2·laptop]", part of
  `ci_pipeline_speed_and_cost_redesign_2026_08_05.md`.
- Revert commits (did not fix it): `unified-trading-pm@01d03532bcaf` (18:37:55Z, partial),
  `unified-trading-pm@28af83429444` (18:45:59Z, full byte-identical restore to `6c579fce`).
- Post-revert re-test (still fails): greeks-service commit `9c19b6f8090c7b5040ab7a62bec821c0256417ee` pushed 19:26:57Z
  to `promote/greeks-service/f35dc273b7df`, run `31039463320` failed 19:27:05Z.
- `actionlint .github/workflows/python-quality-gates-v2.yml` (unified-trading-pm, post-revert) — zero findings.
- `actionlint .github/workflows/quality-gates-v2.yml .github/workflows/image-build-gate.yml` (greeks-service) — only the
  3 pre-existing `glue` label warnings (lines 99/154/184).

## Progress Log

- **cicd escalation `agt-6a6285` (slot 4, 2026-08-05 ~22:35-22:50Z)**: ROOT CAUSE CONFIRMED. Got the run-page banner
  text via WebFetch of `unified-api-contracts` run `31046782461` (the exact diagnostic the "needs UI access" note above
  called for): `Invalid workflow file: quality-gates-v2.yml#L64` →
  `error parsing called workflow ...: workflow was not found` for
  `IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout`. Correlated it with
  repo visibility: PRIVATE repos (`agent-orchestrator` v2 success 21:27Z, `execution-service` 17:32Z) resolve the same
  reference; PUBLIC repos (unified-api-contracts, greeks-service, deployment-service, instruments-service,
  unified-trading-library) all fail identically. PM's reusable-workflow access is `access_level: "user"` (all same-user
  repos granted) yet public callers still fail — GitHub hard-blocks public→private reusable-workflow use. Confirmed with
  a fresh `gh workflow run quality-gates-v2.yml --ref promote/unified-api-contracts/fe46865f0c0a` (failed with the same
  parse error). This closes the "needs UI access" gap; the fix requires an operator decision (host reusable workflows
  publicly, or revert the 17 repos to private). Escalated via `/blocked` with options.
- **interactive-session 2026-08-05 (~18:00-19:30Z)**: discovered as a side effect while trying to measure a clean
  LDR->main promotion timing baseline (see `ci_pipeline_speed_and_cost_redesign_2026_08_05.md`). Traced the failure
  fleet-wide (not repo-specific), watched another concurrent session revert the suspected cause twice, verified the
  final revert is byte-identical to known-good, then proved via a fresh retrigger that the regression is STILL PRESENT
  after that revert — meaning the real cause is not yet isolated. Exhausted the CLI/API diagnostic surface (actionlint
  clean, REST API exposes no error detail for this failure class). Left open per operator direction ("write it up
  leaving it undone") — next session/operator should start from the recommended web-UI step above rather than re-derive
  this investigation.

- **context-scout 2026-08-06**: populated context_scope (3 entries).
