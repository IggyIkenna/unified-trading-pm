---
doc_type: plan
title:
  AO consolidated close-out (2026-08 cycle) — active coordinator for agent-orchestrator-internal findings created after
  the 2026-07 tranche was archived
summary: >-
  The `ao` topic tranche's consolidated close-out was archived on 2026-07-30
  (/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md plus its finalize sibling), but `ao`-tagged work did
  not stop: 115 docs under plans/active still carry asset_group [ao] as of 2026-08-12. That left the tranche with no
  ACTIVE coordinator, and the gap is machine-visible — `check_ag_closeout_linkage` resolves an `[ao]` doc by finding a
  mention in an `ao_consolidated_*` plan across plans/active AND plans/archive, so any `ao` finding created after the
  archived doc stopped being edited is an orphan by construction, and cannot be committed. This plan is that active
  coordinator for the 2026-08 cycle. It deliberately does NOT re-triage the 115 inherited docs (that is todo 1, not a
  claim); it opens the tranche, adopts the findings already blocked on it, and records the structural lesson that a
  tranche whose coordinator is archived while its work continues will silently block commits.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao, close-out, consolidation, plan-hygiene, ag-closeout-linkage]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-12
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
# Declared explicitly rather than inherited: todo 1 (re-triage 115 inherited [ao] docs) is a
# judgment-heavy classification pass, not mechanical work, and the role default would under-serve it.
effort: high
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
source: >-
  Opened 2026-08-12 from a measured blockage, not a planning exercise: three peer issue docs had sat UNTRACKED in slot 3
  for up to 10 days because check_ag_closeout_linkage refused them, and diagnosis showed the `ao` tranche's only
  coordinator was archived. Operator decision the same day was to fix the structural gap (open an active tranche doc)
  rather than route around it by retargeting the docs to a tranche they do not belong to.
---

# The `ao` tranche outlived its close-out doc

## What was measured (2026-08-12)

| fact                                                                      | value                                                      |
| ------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `ao` coordinator in `plans/active`                                        | none, before this plan                                     |
| `ao` coordinators in `plans/archive/2026_07`                              | 2 (the 07-25 doc + its 07-30 finalize sibling)             |
| docs under `plans/active` still tagged `asset_group: [ao]`                | 115                                                        |
| dirs `check_ag_closeout_linkage` searches for an `ao_consolidated_*` plan | `plans/active`, `plans/archive`                            |
| consequence                                                               | any post-archive `ao` finding is an orphan → uncommittable |

The linkage check is not wrong to search the archive — an archived tranche legitimately still explains its own
historical findings. The defect is the combination: **archiving a coordinator does not retire the topic**, so the
tranche kept producing findings that nothing active could adopt. The failure surfaces far from its cause, as a
plan-hygiene refusal on an unrelated commit, which is why it sat undiagnosed for 10 days.

## Adopted findings

**CORRECTED 2026-08-12 (/plan-reconcile), same-day as this plan's own creation**: both docs below are already fully
resolved and archived — this section's original framing ("blocked... adopted so they can be committed," "has open todos
and belongs to the active cycle") was wrong. Neither carries any open work; nothing here needs a resolution path.

- `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03` — resolved, archived 2026-08-09
  (`/plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md`), all todos done.
  Naming-trap note kept for value: **the filename prefix is not the asset group** — this `tradfi_`-prefixed doc is
  actually an `[ao]` finding about how a worker sourced a ruling.
- `ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02` — resolved, archived 2026-08-09
  (`/plans/archive/2026_08/issues/ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md`), all 3
  todos done, both false-positive/false-negative blind spots closed with cited commit SHAs.

## Open `[ao]` findings referenced here for closeout-linkage (2026-08-16, `/ag-closeout-audit ao`)

Named here so each has a durable path into this tranche's closeout family that doesn't depend on any one satellite
doc staying active — the first two were orphaned from `check_ag_closeout_linkage.py`'s reachability graph when
[`cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`](/plans/archive/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md)
(the doc that used to carry the only mention of both) archived. All three remain genuinely open, uncovered by any
active AO-dispatch plan — see this run's parked-findings doc for detail, not duplicated here.

- [`ao_residuals_after_dispatch_hardening_2026_07_17.md`](/plans/active/issues/ao_residuals_after_dispatch_hardening_2026_07_17.md)
- [`data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`](/plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md)
- [`ao_park_wiring_dropped_repeats_premature_gated_dispatch_2026_08_11.md`](/plans/archive/2026_08/issues/ao_park_wiring_dropped_repeats_premature_gated_dispatch_2026_08_11.md) — RESOLVED + archived 2026-08-18 —
  retagged into `[ao]` 2026-08-16 by `/ag-closeout-audit sports` (was `[sports, meta]`, a mistag — 100%
  agent-orchestrator dispatch/`auto_park` internals; see that run's sports-tranche parked-findings doc, Finding 1).
  Its own sole Follow-up item is already `[x]` shipped (`agent-orchestrator@153c0a0f3f`) — only the archival ritual
  remains, out of scope for the AO tranche's own audit which runs separately.

Also linked here for the same reason — resolved and archived this run, but its own former linkage path
(`ao_open_issues_consolidated_close_out_2026_07_17.md`, itself since archived) no longer resolves reliably from a
fresh scan:

- [`regen_positional_task_ids_not_content_stable_2026_07_17.md`](/plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md) — resolved 2026-08-16, see its own `resolved_by:` for evidence.

## Todos

- [ ] [INFRA] P2. **Re-triage the 115 inherited `plans/active` docs tagged `[ao]`.** This plan opens the tranche; it has
      NOT classified them. Some are genuinely open `ao` work, many are `ao_satellite_ao_dispatch_batch*` docs that are
      likely closeable in bulk. Done when: each is either linked into this plan's Sources, retagged to the tranche it
      actually belongs to, or archived. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P2. **MOOT 2026-08-12 (/plan-reconcile)** — both findings above are already resolved + archived
      (2026-08-09), so there is no per-doc disposition left to adopt; the "Adopted findings" section above was corrected
      to state this directly instead of framing them as active/blocked work.
- [x] ✅ [SCRIPT] P2. **Make an archived-coordinator tranche detectable before it blocks a commit.** Today the only
      signal is a refused commit on an unrelated change. Options: have the ag-closeout hygiene sweep WARN when an asset
      group has live docs but no ACTIVE coordinator, or have `check_ag_closeout_linkage`'s failure message say "the only
      `ao_consolidated_*` match is archived — the tranche may need reopening" instead of the generic "no path". The
      second is nearly free and turns a 10-day diagnosis into a one-line read. Done when: one is implemented, or both
      are rejected with the reason recorded. Repo: unified-trading-pm. **SHIPPED — `unified-trading-pm@69ebbb5e57`**
      (violation message now names archived closeout match(es) + flags "tranche may need reopening"). Reconciled
      2026-08-14 per `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` todo 1 (evidence from
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`).
- [x] ✅ [INFRA] P3. **Decide the tranche-reopening convention and write it down.** This plan invented one (open a
      `<ag>_consolidated_closeout_<new-date>.md` for the new cycle, leave the archived one untouched). It is not
      recorded anywhere as the convention, so the next person to hit this will invent a different one — most likely
      editing the archived doc, which is worse. Done when:
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` states what to do when an archived tranche
      produces new findings. Repo: unified-trading-pm. **Extracted 2026-08-18 (na-eligibility-audit, ao tranche) →
      `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 5** — conflict-checked clear (closing the loop on this
      item's 2026-08-17 `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` flag). Track dispatch/completion there, not here.
- [x] ✅ [INFRA] P3. **Check whether the other archived tranches have the same latent gap.** `ao` was found by accident.
      Any tranche whose coordinator is archived while its asset group still has active docs is one commit away from the
      same block. Done when: every asset group is confirmed to have either an active coordinator or genuinely zero
      active docs. Repo: unified-trading-pm. **SHIPPED — `unified-trading-pm@a8d835e74e`** (confirmed no gap fleet-wide
      across all 10 covered AGs; made the condition a standing sweep-time WARN in `check_ag_closeout_linkage.py`), test
      coverage at `unified-trading-pm@cbec983969`. Reconciled 2026-08-14 per
      `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` todo 1 (evidence from
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`).
- [ ] [BACKEND] P2. **Root-cause a recurring `sequential: true` dispatch-ordering violation on satellite finalize
      plans — 2 confirmed instances.** `ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md` (2026-08-10, slot 18:
      todo 4 dispatched before todo 3, which never derived a backlog row at all) and
      `ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md` (2026-08-09: appended todos 5-6 completed while the
      original chain's todos 2-4 stayed open). A same-shape bug
      (`/plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`) was fixed
      2026-08-02, 8 days before the batch14 incident — either a regression of that fix, or a distinct gap the fix
      didn't cover (e.g. specifically appended-after-authoring todos, or a todo that silently never derives a backlog
      row bypassing the sequential check entirely). Done when: the actual mechanism is identified (read
      `regen_backlog_from_plan.py`'s `sequential:`-enforcement path + both incidents' exact backlog/dispatch history),
      and either a regression is confirmed+fixed or the new gap is root-caused and fixed. Repo: agent-orchestrator.
      Source: `plan_reconciler_findings_ao_2026_08_16.md` § Contradictions.

## Provenance note

The blockage this plan resolves was itself mis-recorded before it was understood. It was written down as "no
`ao_consolidated_closeout` plan exists", which was false — two exist, both archived. The corrected statement is that
none was ACTIVE. The distinction mattered: the false version implied the tranche had never been closed out, the true one
shows it was closed out and then kept producing work. Recorded here because the wrong version was believed long enough
to shape a plan.

## Progress Log

- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-15**: populated/refreshed context_scope (4 entries); doc had no prior Progress Log section,
  added a minimal one.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:ba0e198553e8878a]: KEEP-NA, valid — todo 1 (re-triage 115 [ao] docs) is explicitly self-declared judgment-heavy classification, not mechanical; todo 3 (sequential:true dispatch-order root-cause) touches live-dispatch-critical-path machinery. Todo 2 (tranche-reopening convention) flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for a future pass, not split now.
- **na-eligibility-audit 2026-08-18 (ao tranche)**: RECLASSIFY (per-todo split) — closing the loop on the 2026-08-17 marker's MISCLASSIFIED_LIKELY_AO_ELIGIBLE flag on the tranche-reopening-convention todo: the convention text is already fully specified in the todo itself (transcription into a named codex doc, no open judgment call), so it clears the RECLASSIFY bar on its own. Conflict-checked clear (no other active doc claims this) and extracted to `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 5. The re-triage todo (self-declared judgment-heavy) and the dispatch-order root-cause todo (live-dispatch-critical-path) both re-confirmed KEEP-NA. Doc stays `assigned_vm: NA`.
