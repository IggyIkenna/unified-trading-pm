---
doc_type: issue
title:
  "capability_wizard_analysis_findings_2026_06_11.md has ~25 prose 'Status: OPEN' findings but only 1 tracked checkbox
  todo"
summary: >-
  Found during plan_reconciler agt-733350's cross-cutting tranche run (2026-08-09, E2 hunter). Direct violation of the
  workspace HARD RULE "every follow-up is a - [ ] todo, never prose" -- too large to safely convert in that run (not all
  25 need action; several look like real unaddressed engineering). Self-resolved via BLK-af5841d0's [WORKER REC] after
  2h with no operator reply, per the plan-reconcile SKILL's calibration section.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, prose-only-work, hard-rule-violation, task-conversion]
related: [/plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md]
created: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "plan_reconciler agt-733350 (slot 27), cross-cutting tranche run, 2026-08-09 -- E2 hunter finding, routed via
  BLK-af5841d0"
context_scope: [/plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md]
depends_on: []
---

# `capability_wizard_analysis_findings_2026_06_11.md` prose-only remaining work

## What I found

The source doc has 15+ `**Status**: OPEN` entries plus 11 more `OPEN (...)` variants (F2, F3, F4-CONFIRMED, F5, F10,
F11, F13, F14, F16, F17, F28, F39-remainder, F42, F46, etc.) — e.g. F13 "OPEN — minor import-surface gap... not made in
this unit"; F14 "OPEN — workflow-coverage gap... Decision deferred to the UI-phase owner"; F28 "OPEN — conflicting
truths... Recommended decision: pick `venue_collateral.py` as the single SSOT"; F42 "OPEN — logged for registry
alignment follow-up... Deferred to registry alignment phase." The doc's actual `- [ ]`/`- [x]` checkbox count is 13
total (12 done + exactly 1 open, F46).

This is a direct violation of the workspace HARD RULE: "every follow-up is a `- [ ]` todo, never prose." The source doc
is also one of the 8 sources cited by `cross_cutting_strategy_execution_determinism_2026_07_26.md`'s "~121 open todos
across 8 docs" figure — if that figure was derived by checkbox-grep, it undercounts this doc's true remaining work by
roughly an order of magnitude.

Not all 25 findings need action — several (F12/F18/F19/F32 per the hunter's read) are informational/environmental notes,
not real remaining work. Several DO look like real unaddressed engineering: F13 (import-surface gap), F14
(workflow-coverage gap, decision deferred to UI-phase owner), F28 (conflicting SSOT truths, has a stated
recommendation), F42 (registry alignment follow-up), F16 (a latent TypeError bug), F17.

## Todos

- [ ] [REVIEW] P2. Read `capability_wizard_analysis_findings_2026_06_11.md` end to end and classify each of the ~25
      "Status: OPEN" findings as: (a) genuine remaining engineering work → convert to a canonical `- [ ] [TAG] P<n>.`
      todo in that doc (never leave it prose, per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`
      § 2); (b) informational/environmental, no action needed → note explicitly why, do not convert; (c)
      superseded/already resolved elsewhere → cite the resolving doc. Start with F13, F14, F16, F17, F28, F42 (the ones
      this run's hunter flagged as most likely to be real work) but read the full ~25 rather than trusting that
      shortlist.
- [ ] [SCRIPT] P3. Once the conversion lands, re-check whether
      `cross_cutting_strategy_execution_determinism_2026_07_26.md`'s "~121 open todos across 8 docs" figure needs
      updating to reflect the newly-tracked count.

## Progress Log

- **2026-08-09 (plan_reconciler agt-733350)**: filed per BLK-af5841d0, self-resolved after 2h with no operator reply
  (marked [WORKER REC] applied: file as its own dedicated follow-up rather than attempting the conversion inline in a
  reconciliation run).
