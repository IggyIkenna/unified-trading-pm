---
doc_type: issue
title:
  "sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md — Progress Log history (2026-08-02 slot-9 fleet-CI
  runner-capacity re-check)"
summary: >-
  Line-cap remediation extraction from plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md
  (1017L, over the 1000L hard cap) — a single self-contained, fully-closed narrative entry documenting a 2026-08-02
  re-check that found the same-day promote-drain blocker was the fleet-wide self-hosted-runner capacity crisis, already
  tracked (and owned by a different craft) in fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md and its
  continuation. Moved verbatim (no content change) so the live doc stays under cap; the live doc's own text already
  states this finding is not duplicated there, only referenced.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [data-correctness, oom, sports, history, line-cap-remediation]
related:
  [
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Extracted 2026-08-09 by plan_reconciler (agt-196785) per operator direction on BLK-43da7ab8 ("splitting an over-cap
  doc" — one of 3 authorized mechanical fixes).
depends_on: []
---

# sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md — Progress Log history

## 2026-08-02 (slot 9) — precondition re-checked, root cause of the block identified (still not met)

Re-checked the same precondition slot 4 checked earlier today. Unchanged on the surface (`4e0e03d` still only on
`origin/live-defi-rollout`, still NOT on `origin/main`; `origin/main` still ~875 commits behind LDR) but this pass
traced **why** the promote isn't draining, rather than just re-observing the gap:

- The fleet's `ldr-to-main-promote-fleet` workflow (in `unified-trading-pm`) IS running on schedule (`*/15`, confirmed
  green ticks every ~15min all day 2026-08-02) and DOES reach `deployment-service` in its per-repo loop, but explicitly
  gates it:
  `GATE BLOCK deployment-service: ci_status=FAILING (cached='MAIN_GREEN', live='FAILING') — LDR CI is red; fix before LDR→main`
  (dep-order on `unified-api-contracts` is separately flagged but explicitly advisory/not-enforced — the real blocker is
  `deployment-service`'s own LDR `quality-gates-v2` check).
- Checked that check directly: `quality-gates-v2` run `30754282372` (workflow_dispatch on `live-defi-rollout`, triggered
  2026-08-02T15:24:38Z) has both its `QG slice (tests)` and `QG slice (checks)` jobs sitting in GitHub's `queued` state
  35+ minutes later -- never picked up by a runner. `runs-on: [self-hosted, glue]`; the fleet's `glue-*` runner pool (5
  registered, e.g. `glue-ip-172-31-5-118-{1..5}`) shows 2/5 busy at check time, and `gh run list --status queued` across
  several repos surfaced queued workflow runs dating back to 2026-05-15/05-26 (2+ months old, never cleared) -- this is
  a severe, sustained runner-starvation backlog, not a one-off slow run.
- This is NOT a new finding -- it's the **exact same root cause** already tracked in
  `plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (open since 2026-07-27) and its
  continuation `.../fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (`status: open`,
  `last_updated: 2026-08-01`, `assigned_role: cicd`, `assigned_vm: NA` -- explicitly operator/local-only, not
  AO-craft-dispatchable). Not duplicating that doc or attempting a fix here: it's a different craft (`cicd`/infra, not
  `data_engineering`), already owned, and NOT something a single worker turn should try to force (e.g. re-triggering QG
  again would just compete for the same starved runner pool).

**Net**: this todo's precondition genuinely still isn't met, and won't be until either the runner-capacity crisis clears
enough for `deployment-service`'s LDR CI to go green (unblocking the fleet promote) AND the Cloud Run Job is manually
redeployed (per slot 4's finding, no CD-on-main-push exists for this job). Self-skipping again (`reason_code: GATED`)
rather than re-checking on a tight loop -- the blocking condition is fleet-wide and external to this todo, not something
that resolves on a per-dispatch retry cadence.
