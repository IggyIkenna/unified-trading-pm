---
doc_type: issue
title: >-
  quality-gates-v2 fails fleet-wide with GitHub's generic "workflow file issue" (zero jobs created) — persists even
  after a byte-identical revert of python-quality-gates-v2.yml to its last known-working version; root cause NOT
  isolated, left open
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
asset_group: [cross-cutting, ci]
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

## What's NOT confirmed (needs UI access)

The exact broken reference/line. GitHub's REST API gives no detail for this failure class:

- `gh api repos/<repo>/actions/runs/<id>/jobs` → empty.
- `gh api repos/<repo>/commits/<sha>/check-runs` → empty.
- `gh api repos/<repo>/commits/<sha>/check-suites` → shows `status: completed, conclusion: failure` for the
  `github-actions` app, no error text.

**Recommended next step**: open `https://github.com/IggyIkenna/greeks-service/actions/runs/31039463320` (or the
deployment-service equivalent) directly in a browser — the Actions UI renders the actual parse/reference error as a
banner or annotation on the failed run, which the API does not surface. That text will almost certainly point straight
at the broken line.

## Hypotheses NOT yet ruled out

- **A second regression landed in the same window**, separate from fast-checkout.sh, that hasn't been isolated (most
  likely given the byte-identical revert didn't fix it).
- **A GitHub-side transient/platform issue** — possible but hard to distinguish from (above) without the UI's error
  text; if this is the cause, a later retry may simply start working with no code change needed (worth a fresh
  empty-commit retrigger before assuming more code investigation is needed).
- Something in `image-build-validate.yml` / `image-build-gate.yml`'s own chain (BOTH `quality-gates-v2.yml` and
  `image-build-gate.yml` failed with the identical signature on the same PRs — they call _different_ PM reusable
  workflows, which weakly suggests a cause common to both callers rather than callee-specific, but this wasn't
  conclusively isolated).

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

- **interactive-session 2026-08-05 (~18:00-19:30Z)**: discovered as a side effect while trying to measure a clean
  LDR->main promotion timing baseline (see `ci_pipeline_speed_and_cost_redesign_2026_08_05.md`). Traced the failure
  fleet-wide (not repo-specific), watched another concurrent session revert the suspected cause twice, verified the
  final revert is byte-identical to known-good, then proved via a fresh retrigger that the regression is STILL PRESENT
  after that revert — meaning the real cause is not yet isolated. Exhausted the CLI/API diagnostic surface (actionlint
  clean, REST API exposes no error detail for this failure class). Left open per operator direction ("write it up
  leaving it undone") — next session/operator should start from the recommended web-UI step above rather than re-derive
  this investigation.
