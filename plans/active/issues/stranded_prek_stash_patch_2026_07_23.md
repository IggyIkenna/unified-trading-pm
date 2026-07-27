---
doc_type: issue
title: A ~11MB prek pre-commit stash patch is stranded on disk, unapplied, unclaimed
summary: >-
  While committing an unrelated fix during a very active session (many concurrent commits landing on live-defi-rollout
  within minutes of each other), a `git commit` invocation's prek pre-commit hook stashed another session's unstaged
  working-tree changes to a patch file, then failed to re-apply that patch after the branch had moved (upstream drift
  during the hook run). The patch is fully intact on disk but was never reapplied to the working tree, and nothing in
  the plans corpus references it.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [git, concurrency, data-risk, plan-hygiene]
related: []
created: 2026-07-23
parent_epic: agent_operating_framework_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
drift_direction: none
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: [/home/ubuntu/.cache/prek/patches/1784815445082-3204588.patch]
depends_on: []
---

# Stranded prek stash patch (2026-07-23)

## What happened

During an extremely active window on `unified-trading-pm`'s `live-defi-rollout` (multiple concurrent sessions committing
within minutes of each other — observed commits like `plan_line_cap_remediation_2026_07_23.md`, rapid `docs(plans):`
churn across hundreds of `codex/**` files), a routine `git commit` for an unrelated fix (`validate_plan_links.py`)
triggered prek's `fix-commit-identity` hook, which needed to stash unstaged changes to run cleanly. The stash-pop that
followed failed:

```
error: patch failed: /codex/09-strategy/_archived_pre_v2/defi/aave-lending.md:1
error: patch failed: /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md:14
error: patch failed: /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md:12
error: patch failed: plans/archive/2026_06/orchestrator_dirty_state_gate_stomps_live_wip_2026_06_22.md:1
error: patch failed: plans/archive/consolidated_remaining_work.plan.md:10
error: patch failed: plans/archive/defi_instrument_pipeline_and_rewards_2026_04_01.plan.md:6
error: patch failed: plans/archive/issues/tradfi_manifest_row_loss_regression_2026_07_12.md:378
```

The patch file itself is intact (not corrupted, not deleted):

```
/home/ubuntu/.cache/prek/patches/1784815445082-3204588.patch  (11,451,591 bytes, 2026-07-23 14:04)
```

## Why it wasn't fixed in-session

The content is not mine — I never touched any of the files listed above this session. Per the multi-agent safety rule
("never edit unfamiliar/untracked/recently-pushed files you don't own"), reconstructing or reapplying someone else's
stash without understanding its intent risks clobbering real, different, more current work that has very likely already
landed through the same session's subsequent commits (this repo has had enormous commit volume since — the stash is
almost certainly stale by now).

## What to do

1. **Check staleness first** — `git log --since="2026-07-23T14:00:00Z" -- <one of the listed files>` for each affected
   file; if a commit already touched it after the stash timestamp, the stashed content is very likely superseded and
   this can be closed as moot (safe to delete the patch file at that point).
2. If genuinely not superseded, identify whose work it was (unclear from the patch alone) and hand it back to them, or
   apply it manually with full understanding of the diff.
3. Either way, close this issue once triaged — it should not linger.

## Todos

- [ ] 1. [REVIEW] P2. Check whether the 7 files listed in the failed patch have been touched by later commits since
      2026-07-23T14:04 UTC; if yes for all, delete the stash patch file and close this issue as moot.
- [ ] 2. [REVIEW] P2. If any file was NOT superseded, recover the relevant hunk from the patch file and apply it
      properly (or flag to the operator for whose work it was).
