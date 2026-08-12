---
doc_type: issue
title: deployment-api cloudbuild drift exceeds its baseline and blocks EVERY unified-trading-pm quickmerge
summary: >-
  deployment-api@4c31b72 added post-deploy auth-contract steps to its cloudbuild.yaml without forward-porting them into
  cloudbuild-api-template.yaml, raising check_cloudbuild_template_drift to 19 markers against a committed baseline of
  16. The check is a shrinking ratchet ('NEVER raise a count'), so it now fails for everyone: any unified-trading-pm
  quickmerge re-gates the whole tree and is refused on this unrelated repo's drift. Confirmed it is committed content on
  a clean tree, not anyone's WIP. Worked around once on 2026-08-12 via the documented GATE-INFRA carve-out
  (unified-trading-pm@f9dbc8a31f); the carve-out only covers scripts/quality_gates and scripts/quality-gates-base, so
  ordinary PM changes remain blocked until this is drained.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [cloudbuild, quality-gates, ratchet-baseline, template-drift, ship-blocker]
related:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md,
  ]
created: 2026-08-12
last_updated: 2026-08-11
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on:
source: found 2026-08-11 while shipping the DeepSeek wallet sampler — the repo's own test suite could not run
---

## What is broken

`check_cloudbuild_template_drift` compares each consumer repo's `cloudbuild.yaml` against its mapped template and fails
when a consumer carries content the template does not. `deployment-api` now carries 19 such markers against a committed
baseline of 16 — the over-baseline content is the `vendor-deps` and `verify-auth-contract` step args added by
`deployment-api@4c31b72` ("post-deploy auth-contract verification, 401 no-cred / 200 keyed").

The consequence is fleet-wide, not local: `quickmerge.sh` re-gates the **current tree**, so a `unified-trading-pm` ship
is refused because a DIFFERENT repo drifted. It is not flaky and not anyone's WIP — `deployment-api` has a clean working
tree and the drift is committed.

## Why it was not fixed in passing

The remedy the checker prints is `--update-baseline`, but this baseline is a shrinking ratchet and CLAUDE.md is explicit
that such counts only go DOWN. Raising 16 -> 19 to unblock a ship would convert a real "template is behind its
consumers" signal into permanent accepted debt, which is exactly the failure the ratchet exists to prevent. The correct
drain is to forward-port the auth-contract steps into `cloudbuild-api-template.yaml` — that is
`deployment-api`/deploy-infra work, not gate work, and it needs an owner who can say whether the steps are meant to be
template-wide or a deliberate per-repo customisation.

## Measurement trap worth keeping

A first pass called this transient after running the checker standalone and seeing only `[OK]` lines. That read was
`tail -12`, and `deployment-api` sorts alphabetically ABOVE every `[OK]` line shown — the failure was in the part that
got cut. `head`/`tail` on a checker's output is not evidence of absence; grep for the failing token instead.

## Todos

- [ ] [OPERATOR] P1. **Decide whether the auth-contract steps belong in `cloudbuild-api-template.yaml`.** If yes,
      forward-port them and the drift drains to baseline on its own. If they are deliberate per-repo customisation, the
      baseline needs an explicit, reviewed re-ratchet with that rationale recorded — not a silent `--update-baseline` to
      unblock a ship. **Done when**: `check_cloudbuild_template_drift` passes on a clean tree with no raised count, or
      the raise is recorded with its justification. (repo: deployment-api)
- [ ] [INFRA] P2. **Make the failure name its blast radius.** The check fails a PM ship while naming only a consumer
      repo, so the reader's first hypothesis is "my change broke this". One line stating that a consumer's drift blocks
      every unified-trading-pm quickmerge would have saved the whole diagnosis above. (repo: unified-trading-pm)
