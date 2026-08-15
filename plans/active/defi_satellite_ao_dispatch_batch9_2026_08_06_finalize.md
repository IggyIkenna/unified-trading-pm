---
doc_type: plan
title: DeFi satellite AO batch 9 — finalize (reconcile 17 source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch9_2026_08_06.md — machine-held via depends_on + gate_on_depends:
  true until every one of that plan's 17 todos is done. Mirrors batch1-8-finalize: reconcile each of the 17 source docs
  (flip/cite the item each batch9 todo closed), re-check the 2 conflict-parked Deferred items + the 33 non-batchable
  Deferred items for whether any blocking condition has since cleared, then archive batch9 via the standard 6-step
  ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch9_2026_08_06]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-08-06 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 9 — finalize

**status: active — gated on batch9's 17 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not
release these until batch9 is fully done.** (Batch9 itself stays `status: draft` until the operator approves dispatch —
this finalize plan needs no separate flip, `gate_on_depends` holds it correctly either way per the "no double gate"
finding in `cursor-configs/skills/ag-closeout-audit/SKILL.md`.)

## Todos

- [ ] [DOC] P1. **Source-doc reconciliation**: for each of batch9's 17 todos, confirm the cited source doc's own open
      item was actually flipped/closed-by-citation as that todo's Done-when specified (todos 1-17, one check each — most
      todos already instruct flipping the source doc's own checkbox/status directly as part of their own Done-when, so
      this is a verification pass, not new investigation). Repo: unified-trading-pm. Done when: every one of the 17
      source docs listed in batch9's todos either shows the item closed in its own text, or a citation note pointing
      back at the batch9 todo that closed it, with no orphaned "still looks open" gap.
- [ ] [DOC] P2. **Re-check the Deferred items**: (a) the 2 conflict-parked operator-decision-gated items
      (`defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`'s stall diagnosis,
      `lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`'s split-vs-alternative — gated on
      `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`'s own `[OPERATOR]` ruling) — has either operator
      question been ruled on since batch9 was drafted? (b) the 33 non-batchable items (20 operator_gated, 8
      genuinely_human_only, 3 too_large_or_risky, 2 time_gated) — has any blocking condition cleared (an operator ruling
      landed, elapsed time passed, a competing claim shipped/superseded)? Per the skill's iterative-drain methodology,
      any item that clears becomes a batch10 candidate directly, without a fresh Phase-1 triage agent. Repo:
      unified-trading-pm. Done when: each of the 2 parked items and the 33 Deferred items has an explicit still-held /
      cleared verdict recorded here, with citations for any newly-cleared item.
- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch9_2026_08_06.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) confirm every Deferred item from todo
      2 above is migrated with an explicit verdict, no orphaned prose; (2) add the archived-banner cross-reference; (3)
      run the post-phase codex audit — cite any codex doc this batch's shipped work should update; (4) confirm no new
      CLAUDE.md contract needs codifying; (5) update every corpus referrer (`plans/active/INDEX.md` +
      `defi_consolidated_closeout_2026_07_18.md`'s covering-plan discovery, if it lists batch9 by name) to the archived
      path; (6) `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch9 is at its archived
      path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-06 (scheduled `ag_closeout_auditor`, tranche=defi, autonomous, slot 3): Drafted alongside batch9,
  `status: active`, gated on batch9's 17 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on
  batch9's operator-approval flip to `active` and subsequent dispatch.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-15**: re-verified context_scope (5 entries) -- all 5 still resolve; unchanged.
