---
doc_type: issue
title:
  evidence-backed-completion sub-rule B ratchet regressed to 24 (baseline 23) — one genuinely new unevidenced claim,
  blocks unified-trading-pm QG fleet-wide
summary: >-
  `scripts/quality_gates/check_evidence_backed_completion.py` sub-rule B fails (24 claims-without-evidence > baseline
  23), blocking `quality-gates.sh`'s post-gate suite for `unified-trading-pm` and therefore the `quickmerge --agent`
  sentinel path for every agent shipping any change in this repo. Diffed the live violation set against the baseline
  yaml's recorded (path, line) pairs: 13 of the 14 "new" entries are just line-number drift from unrelated edits
  shifting content within already-baselined files (same doc, nearby line) — not real regressions. Exactly ONE is
  genuinely new, with no baseline counterpart at all:
  `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:181`, a todo in a plan doc created today.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, quality-gates, ratchet, evidence-backed-completion, regression]
related: [/plans/PLAN_FORMAT.md]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: cicd
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found blocking `unified-trading-pm`'s `quality-gates.sh` Pass-1 while shipping an unrelated `scripts/dev/` addition
  (2026-08-09 interactive session, slot 5), immediately after the separate
  `cloudbuild_api_template_client_reporting_drift_regression_2026_08_09.md` blocker resolved. 6 consecutive re-pulls
  over ~1 minute all reproduced the same 24-vs-23 count — not self-resolving transient noise the way the cloudbuild
  drift was.
depends_on: []
---

# evidence-backed-completion ratchet regressed to 24 (baseline 23)

## What I found

`check_evidence_backed_completion.py` sub-rule B (runtime-green claims without `Evidence: cloudbuild=<id>`) fails
deterministically: 24 live violations vs a baseline of 23. Reproduced across 6 consecutive
`git pull --rebase --autostash` + re-check cycles over about a minute — this is a standing condition, not the
branch-churn-timing noise the sibling cloudbuild drift blocker turned out to be.

Wrote a one-off diff (baseline yaml's `baseline_files: [{path, line}]` vs the live violation set's `(path, line)` pairs)
to separate real regressions from line-number drift:

- 13 of 14 "new" entries pair up with a "removed" entry in the SAME file at a nearby line number — ordinary drift from
  unrelated concurrent edits shifting line numbers in already-baselined docs
  (`monitoring_control_plane_master_2026_06_10.md`, `ci_satellite_ao_dispatch_batch1_2026_07_26.md`, etc.) — not real
  content regressions.
- Exactly ONE has no baseline counterpart at all:
  `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:181` — a `- [x] ✅ [INFRA] P0.` claim ("Rebuild
  the IS daily-definition producer for TradFi/sports/prediction ... `uts-prod-instruments-service-prediction-t1-recon`
  ... succeeded 5/5 consecutive days 2026-08-05→09") in a plan doc created today. It cites
  `instruments-service@cad1d322` (a commit SHA) and named scheduler run history, not a `cloudbuild=<id>`.

## Why it matters

Same blast radius as the sibling cloudbuild-drift blocker: this is a whole-repo post-gate check, so it blocks the
sanctioned `quickmerge --agent` ship path for EVERY agent touching `unified-trading-pm`, not just whoever authored the
new claim.

## Recommended next step

This needs a judgment call by whoever owns `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (not this session
— different plan, different content, out of this task's scope), choosing one of:

- (a) The claim is genuinely deploy/runtime-green-shaped and needs a real `Evidence: cloudbuild=<id>` citation added, OR
- (b) The claim is about a scheduled-job run history, not a Cloud Build deploy — the sub-rule B heuristic is over-firing
  on "succeeded"/"prod-verified" language that isn't actually a build claim, and the fix is scoping the heuristic
  tighter (or, if this specific instance is judged a one-off acceptable exception, re-baselining with
  `python3 scripts/quality_gates/check_evidence_backed_completion.py --baseline-write` after confirming no OTHER real
  regression is hiding in the ratchet bump).

## Todos

- [ ] [CICD] P1. **Resolve the `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:181` evidence-backed-completion
      violation** (repo: unified-trading-pm) — pick (a) or (b) above, confirm
      `check_evidence_backed_completion.py --workspace-root $WORKSPACE_ROOT` reports sub-rule B count back at or below
      23, and that `unified-trading-pm`'s `quality-gates.sh` evidence-backed-completion post-gate is green again.

## Codex SSOTs

- `plans/PLAN_FORMAT.md` § 8b — evidence-backed-completion rule this ratchet enforces

## Progress Log

- **2026-08-09 (backend_engineer, slot 5)**: Filed while still blocked shipping an unrelated `unified-trading-pm`
  change, immediately after the sibling cloudbuild-drift blocker resolved. Isolated the exact new violation via a
  baseline-vs-live (path, line) diff rather than treating the whole 24-vs-23 delta as unknown. Declaring/joining the
  `qg_red` repo-blocker for `unified-trading-pm` and waiting rather than editing someone else's in-flight plan content.
