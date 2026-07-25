---
doc_type: plan
title: AG closeout-audit rollout — cefi/defi/tradfi/prediction (sports treatment, generalized)
summary: >-
  Autonomous session (/autonomous, operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset
  groups that haven't had it yet — cefi, defi, tradfi, prediction — each of which already carries its own
  <ag>_consolidated_closeout_2026_07_18.md sitting in the same pre-treatment state sports was in before this session's
  earlier work (satellite triage -> sports_satellite_ao_dispatch_batch2 -> gated batch2_finalize -> orphan-projection
  audit). For each AG: discover its covering-plan set, run a per-doc Workflow classification audit (archivable now /
  archivable once currently-dispatched work lands / orphaned with no coverage / cross-cutting exclude), then — with a
  hard conflict-check against the consolidated plan's own todos first — draft (status: draft, never auto-shipped to
  active) the next AO-dispatch-batch + gated finalize plan pair for genuinely AO-eligible orphaned work. This is the
  plan-of-record / Progress Log for the whole rollout per cursor-configs/AUTONOMOUS_AGENT_RULES.md rule 6 — a compressed
  future-session must be able to resume losslessly from this doc alone.
status: active
nature: process
asset_group: [cefi, defi, tradfi, prediction, sports, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, autonomous, plan-hygiene, ao-dispatch, orphan-audit]
related:
  - /cursor-configs/skills/ag-closeout-audit/SKILL.md
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
  - /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md
  - /plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md
  - /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator instruction 2026-07-25: "keep going for the next 8 hours or until you are done with everything /autonomous
  ... anything remaining you need to queue because you have to ask me operator questions for decisions make clear for me
  so that i can answer when im back" — issued immediately after confirming the /ag-closeout-audit skill's scope (audit +
  report + draft next batch) via AskUserQuestion. Genuine operator-decision-caliber questions are QUEUED in the linked
  issue doc per that instruction, NOT silently auto-decided (this overrides AUTONOMOUS_AGENT_RULES.md rule 2's default
  "decide yourself, don't ask" for THIS session only — the operator explicitly asked for queued questions instead).
---

# AG closeout-audit rollout — cefi/defi/tradfi/prediction

## Todos

- [ ] [DOC] P1. **Sports**: get the 53-doc orphan-audit workflow's results (in flight at session start,
      `wf_8cdc5fb5-b1f`), synthesize counts by verdict, journal to this Progress Log, report to operator (already
      requested). **Done when**: counts reported + logged with the full orphaned-doc list.
- [ ] [DOC] P1. **Sports**: conflict-check + draft the next `sports_satellite_ao_dispatch_batch3_<date>.md` +
      `..._batch3_finalize_<date>.md` pair (status: draft) for any AO-eligible orphaned work the audit finds, per
      ag-closeout-audit skill Phase 3. Skip if the audit finds nothing AO-eligible remaining. **Done when**: drafted +
      shipped (as draft docs) or explicitly logged as "nothing to draft."
- [ ] [DOC] P1. **cefi**: run /ag-closeout-audit Phases 0-3 in full (discover covering plans, per-doc classify Workflow,
      synthesize+report, conflict-check + draft next batch). **Done when**: audit results logged, any draft
      batch/finalize pair shipped.
- [ ] [DOC] P1. **defi**: same, for defi.
- [ ] [DOC] P1. **tradfi**: same, for tradfi.
- [ ] [DOC] P1. **prediction**: same, for prediction.
- [ ] [DOC] P2. **Final report** (AUTONOMOUS_AGENT_RULES.md rule 9): once all 5 AGs are audited and any warranted
      batches drafted, write a closing summary in this Progress Log — every AG's orphan count, every drafted
      batch/finalize pair, every question parked in the operator-decisions queue, and the verified end-state. Kill the
      loop.

## Progress Log

- **2026-07-25 (session start)**: Plan created. Prior work this session (before /autonomous): shipped the
  finalize-plan-coverage QG rule (task_template.md + check_finalize_plan_coverage.py + baseline), landed the
  verify-slot-host-symmetry.sh RECOVERED-bookend fix, built + shipped the /ag-closeout-audit skill (2 branch-drift
  retries), filed `issues/test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25.md` (found while
  shipping the skill — real flakiness in a pre-existing test, not caused by this session's changes). Launched a 53-agent
  Workflow classifying every sports-primary doc (`wf_8cdc5fb5-b1f`) — in flight when /autonomous was invoked.
