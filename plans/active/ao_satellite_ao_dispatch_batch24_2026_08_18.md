---
doc_type: plan
title: AO satellite AO batch 24 — conflict-clear bounded extraction from the 2026-08-18 na-eligibility-audit ao run
summary: >-
  TWENTY-FOURTH AO-dispatch batch for the `ao` topic tranche — output of a `/na-eligibility-audit ao` Phase 0-3 run
  (2026-08-18). Phase 1 classified 10 in-scope `assigned_vm: NA` docs (60 of the 70-doc candidate set were
  incremental-skip, unchanged since their last dated verdict marker) via a 10-agent Workflow fan-out; 5 items across 2
  source docs survive the Phase 2 conflict-check (verbatim/near-verbatim duplicate check against every active
  `assigned_vm: planning` plan in the same parent_epic, the tranche's own consolidated closeout, and every other
  satellite batch created this run or earlier) as genuinely bounded, already-decided, conflict-clear work. TWO further
  candidates were found CONFLICTED and deliberately EXCLUDED — see below.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-24, satellite-docs, satellite-extraction, na-eligibility-audit]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch24_finalize_2026_08_18.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/issues/ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md,
    /plans/active/ao_human_fleet_integration_2026_08_15.md,
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.3
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  `/na-eligibility-audit ao` (2026-08-18, dispatch agt-0f2c85, slot 9). Phase 1 classified 10 in-scope docs (of 70
  total ao-tranche candidates, 60 skipped via an unchanged incremental-diff marker) via a 10-agent Workflow fan-out —
  one hunter per doc, full end-to-end read, mandatory grep-count completeness check against Phase 0's own open_todos
  figure. Phase 2 conflict-check: grepped every status:draft/active `ao_satellite_ao_dispatch_batch*` (3/8/14/21/22/23)
  + finalizes, `ao_consolidated_closeout_2026_08_12.md`, and every other `assigned_vm: planning` doc under
  `parent_epic: orchestrator_master`/`agent_operating_framework_master`/`infrastructure_master` for each RECLASSIFY
  candidate's subject matter (distinctive function/mechanism names, not just titles) — zero hits for the 5 items
  extracted here; 2 candidates held back on a confirmed conflict (see "Explicitly excluded" below).
---

# AO satellite AO batch 24

> **`status: active`** per this skill's own Phase-3 rule (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
> § 1(b) + the na-eligibility-audit SKILL.md's 2026-08-10 fix) — this audit's own verdict IS the authorizing decision,
> unlike `/ag-closeout-audit`'s read-only `status: draft` convention. **Note**: the immediately-prior ao-tranche batch
> (`ao_satellite_ao_dispatch_batch23_2026_08_17.md`) shipped `status: draft` instead — confirmed (via its Progress Log
> author tag, `na_eligibility_auditor`) to be a copy-paste of the `/ag-closeout-audit` template rather than a
> deliberate newer convention (batches 3/8/14/21, the other na-eligibility-audit-authored batches through 2026-08-16,
> all correctly used `status: active`). Flagging for the operator/main agent to decide whether batch23 should be
> retroactively flipped to `active` — not done here (a status flip on someone else's undispatched batch, from a
> different run, a day later, is exactly the kind of unilateral action this run should surface rather than take).

## Why this plan exists

`/na-eligibility-audit ao`'s 2026-08-18 run classified the 10 in-scope docs in the `assigned_vm: NA` "ao" tranche
population (60 of 70 candidates were unchanged since a prior dated verdict and skipped per Phase 0's incremental-diff
rule). Of the 10, the majority are genuine KEEP-NA (operator-gated, live-infra judgment, unresolved design forks, or
already tracked elsewhere) — see this run's chat report for the full breakdown. This batch extracts the handful that
are bounded, already-decided, and conflict-clear:

1-4. **Four per-task telemetry-capture fields on `TaskUsageRow`** — join per-task compaction occurrence, capture the
peak/high-watermark `context_used_pct`, capture which repo(s) a task actually touched, and persist the task's
`context_scope` size onto the completed-task record. All four are pure bounded backend/DB engineering (an existing
event/value joined or persisted onto an existing per-task table via an already-identified key), added the same day
(2026-08-17) to `multi_provider_context_billing_reconciliation_2026_08_16.md` — a doc otherwise correctly held
`assigned_vm: NA` on an explicit dated operator ruling ("human plan, not AO-dispatched... the design calls and
live-testing judgment here don't fit the AO-eligible bar"), but that ruling's own text scopes itself to "design calls
and live-testing judgment" specifically, and these 4 items have neither — they fall outside the cited ruling's own
stated scope. Source: `multi_provider_context_billing_reconciliation_2026_08_16.md`.
5. **Write down the tranche-reopening convention** `ao_consolidated_closeout_2026_08_12.md` already invented and used
   ad hoc ("open a `<ag>_consolidated_closeout_<new-date>.md` for the new cycle, leave the archived one untouched") into
   `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, so the next tranche-reopening doesn't have to
   reinvent it. This item was flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` by the 2026-08-17 na-eligibility-audit run
   ("for a future pass, not split now") — per the skill's close-the-loop rule, this run is that future pass. The
   convention text is already fully specified in the source todo; nothing left is a judgment call, only transcription
   into the named codex doc. Source: `ao_consolidated_closeout_2026_08_12.md`.

**Explicitly excluded** (named here so nobody re-derives them as candidates without reading why):

1. **`ao_open_work_consolidated_tracker_2026_08_14.md`'s Track-5 dashboard test-fixture bug**
   (`task-usage-account-filter.spec.ts`, 2 pre-existing failures, `window_task_usage_totals` double-counting ~5000
   from "unregistered account" oneoff rows). Individually reads as a bounded, deterministic debugging task. BUT
   `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md` — the plan that originally built both this
   exact test file and the `window_task_usage_totals` function, and is still active with 29 open todos — carries its
   own still-open todo directly adjacent in the same subsystem: `[REVIEW] P0. Quantify the double-count blast radius on
   the live DB before repricing anything`, sequenced immediately after an already-fixed *different* double-counting
   defect ("a typed one-off with `assigned_at=None` bills the WHOLE session"). Whether the test-fixture failure is the
   SAME residual double-count family that quantify-blast-radius todo is about to investigate, or a genuinely distinct
   defect, is not resolvable by re-reading either doc harder — it needs whoever picks up that still-open investigation
   to check. Extracting this as a standalone fix risks either duplicating that investigation's own eventual fix or
   patching a symptom the investigation is about to explain more completely. Flagged in this run's report for
   reconciliation, not dispatched here.
2. **`ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md`'s Todos 5-6** (a `UserPromptSubmit`-driven IDE-compatible
   human-fleet heartbeat, operator-approved via `AskUserQuestion` mid-session). Individually reads as bounded (reuses
   `scripts/human_fleet/ao_client.sh`'s existing transport). BUT `ao_human_fleet_integration_2026_08_15.md` — the
   active, extensively-shipped (19+ todos landed) plan that owns this exact heartbeat mechanism — has its own
   documented "Design decisions (resolved... do not re-open without a new operator ruling)" section explicitly
   evaluating and REJECTING `UserPromptSubmit` as a heartbeat carrier: "no Claude Code hook payload
   (PreToolUse/PostToolUse/Stop/SessionStart/PreCompact/**UserPromptSubmit**) carries context-window usage, model
   name, or account identifier — confirmed absent from every schema... statusline is the answer." Todo 5's own framing
   ("IDE-compatible... equivalent heartbeat sender") suggests it may be solving a narrower, genuinely-uncovered gap
   (statusline doesn't render in Cursor/VS Code IDE-embedded mode) rather than re-litigating the rejected general
   mechanism — but that distinction is exactly the kind of judgment call the conflict-check protocol reserves for an
   operator ruling, not a worker's own read. Flagged in this run's report for reconciliation, not dispatched here.

## Rules for every worker on this plan

- All 5 todos below are file-disjoint (todos 1-4 touch `agent-orchestrator/server/orm.py` + `context_lifecycle.py` +
  `dispatch.py` in different, non-overlapping ways per todo; todo 5 touches a `unified-trading-pm` codex doc entirely)
  — safe to run concurrently, no `sequential: true`.
- Todos 1-4 all read from `TaskUsageRow` (`agent-orchestrator/server/orm.py:292`) but each ADDS a different column/field
  — coordinate schema-migration ordering informally (check for an in-flight migration from a sibling todo before
  adding your own) rather than assuming exclusive ownership of the table.

## Todos

- [ ] [DATA] P1. **Join per-task compaction occurrence onto a queryable per-task record.** Whether a given `task_id`
      triggered `forced_precompact`/`forced_compact`/`forced_compact_ineffective` during its own run —
      `ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md` already logs these events with a
      timestamp + `slot_id` (`server/fleet_kpis.py`/`server/context_lifecycle.py`, its own `craft_type`-tagging todo 3
      shipped `agent-orchestrator@c46102b9b5`), and `TaskUsageRow` (`server/orm.py:292`) already carries
      `assigned_at`/`completed_at` per task — the join key (an event's timestamp falling inside a task's own
      `[assigned_at, completed_at]` window for that `slot_id`) exists in principle but is never materialized as a
      field or query today. **Done when**: a real query (or a new persisted field, e.g. `TaskUsageRow.compact_count`)
      answers "did task X trigger compaction" for a real historical task without hand-correlating timestamps. Source:
      `/plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md` todo "[DATA] P1. New (2026-08-17):
      join per-task compaction occurrence...". Repo: agent-orchestrator.
- [ ] [INFRA] P1. **Capture the PEAK/high-watermark `context_used_pct` reached during a task.** Not just the
      end-state token sums `TaskUsageRow` already stores — `context_lifecycle.py`'s per-tick reader already sees
      `context_used_pct` live for every active target; nothing records the max value seen during a task's own window
      onto its durable per-task record. **Done when**: a real completed task's record shows a real peak-context value,
      cross-checked against a live session known to have approached a specific pct. Source: same doc, "[INFRA] P1. New
      (2026-08-17): capture the PEAK/high-watermark `context_used_pct`...". Repo: agent-orchestrator.
- [ ] [DATA] P2. **Capture which repo(s) a task actually touched, from real commit/push evidence.** Not the plan's
      declared `repos:` frontmatter (a stated intent, not a measurement) — confirmed no such field exists today
      (`repos_touched`/`repo_count` in `server/` only match unrelated dirty-worktree-state concepts,
      `server/routes/git_health.py:277`, `server/worktree_clean_check/_report.py:51`). **Done when**: a real completed
      task's record shows the real repo(s) it committed to, sourced from actual commit/push evidence. Source: same
      doc, "[DATA] P2. New (2026-08-17): capture which repo(s) a task actually touched...". Repo: agent-orchestrator.
- [ ] [DATA] P2. **Persist the task's `context_scope` size onto the completed-task record.** The reading-list already
      passed to the worker at dispatch (`server/dispatch.py:564`) is dispatch-time-only today and never carried
      through to `TaskUsageRow` or any other durable per-task table. **Done when**: a real completed task's record
      shows both its `context_scope` size and its real outcome metrics (turns/tokens/compacted) joinable in one
      query. Source: same doc, "[DATA] P2. New (2026-08-17): persist the task's `context_scope`...". Repo:
      agent-orchestrator.
- [ ] [DOC] P3. **Write the tranche-reopening convention into `plan-completion-and-archival-discipline.md`.** The
      convention `ao_consolidated_closeout_2026_08_12.md` already invented and used ("open a
      `<ag>_consolidated_closeout_<new-date>.md` for the new cycle, leave the archived one untouched") is not recorded
      anywhere as THE convention, so the next tranche-reopening will likely invent a different one — most likely
      editing the archived doc directly, which is worse. **Done when**:
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` states what to do when an archived
      tranche produces new findings, citing `ao_consolidated_closeout_2026_08_12.md` as the worked precedent. Source:
      `/plans/active/ao_consolidated_closeout_2026_08_12.md` todo "[INFRA] P3. Decide the tranche-reopening convention
      and write it down.". Repo: unified-trading-pm.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`, `/codex/12-agent-workflow/measurement-claims-discipline.md`.

## Progress Log

- **2026-08-18 (na_eligibility_auditor, dispatch agt-0f2c85, autonomous)**: Drafted per `/na-eligibility-audit ao`'s
  Phase 3 — 5 conflict-clear, file-disjoint, bounded todos extracted from 2 source docs after Phase 2's conflict-check
  excluded 2 further candidates (both detailed above under "Explicitly excluded"). `status: active` per the skill's
  documented Phase-3 rule.
