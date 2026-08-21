---
doc_type: issue
title: Re-check whether the prosewrap-padding baseline is still climbing before hand-raising it
summary: >-
  An earlier AO finding (agt-4d722f) reported check_prosewrap_padding.sh's baseline climbing
  despite 3 landed content-fix rounds (2047->2217->2324, ~1900+ real lines fixed), attributed to
  concurrent agents' plan-doc edits re-triggering a known non-idempotent prettier reflow bug
  faster than fixes land, and recommended hand-raising the baseline as the only escape given
  --diff-base mode is disabled for the exact promote-PR/whole-branch context that's blocked.
  Operator ruled 2026-08-16: re-verify this is still the current state before acting on that
  recommendation — do not assume the finding is still fresh.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, prosewrap, baseline, ratchet]
related: []
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: agent_operating_framework_master
priority: P2
source: "agt-4d722f AO backlog finding, re-scoped by operator ruling 2026-08-16"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
effort: max
assigned_role: infra
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    scripts/plan-hygiene/check_prosewrap_padding.sh,
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
  ]
---

# Re-check whether the prosewrap-padding baseline is still climbing

## Todos

- [ ] [DATA] P2. Re-run `check_prosewrap_padding.sh` fresh right now and compare the current violating-line count
      against the last measured checkpoint (2324, per agt-4d722f). If the count has stabilized or dropped since that
      finding (e.g. concurrent agent activity has quieted, or the non-idempotent prettier reflow bug has since been
      fixed elsewhere), the climbing-baseline problem may no longer be current — say so and stop here, do not
      hand-raise the baseline on stale evidence.
- [ ] [DATA] P2. If the count is still climbing, investigate the root cause fresh: confirm it's still the
      documented non-idempotent prettier reflow bug. Measure 2-3 checkpoints ~10-15 min apart to confirm climbing,
      same method the original finding used (`prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`) and not something new,
      then decide between the worker's original recommendation (hand-raise the baseline with a dated justification,
      given `--diff-base` mode is confirmed still disabled for promote-PR/whole-branch contexts) or a different fix,
      based on what the fresh investigation finds. Report back before hand-raising anything — this todo authorizes
      investigation, not the baseline change itself.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up, operator ruling)**: operator explicitly did not accept the worker's
  hand-raise recommendation on the original finding's evidence alone — wants it re-verified fresh first, given how
  much concurrent activity this branch has seen.

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).
