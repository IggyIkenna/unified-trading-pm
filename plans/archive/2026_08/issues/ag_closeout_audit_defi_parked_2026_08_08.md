---
doc_type: issue
title: ag-closeout-audit defi parked findings — 2026-08-08
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-08, tranche=defi, slot 13). Phase 0: 80 corpus
  members, 17 covering docs, 12 never-cited candidates deep-classified via Phase 1 Workflow. 9/12 confirmed
  exclude_cross_cutting (legitimate multi-AG span, no new mistags — orthogonality check clean). 3/12
  orphaned_never_touched, yielding 3 AO-eligible items total (2 ready now, 1 time-gated). Pool too thin to justify a new
  batch11 doc this round (precedent: 08-07's Option A for an equally thin pool) — all 3 flagged here as batch11
  candidates. 2 informational carry-forwards (unexecuted retag recommendation, linkage-gate tool blind spot). 6 findings
  total.
status: resolved
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, defi, orphan]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_06.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_07.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
  ]
created: 2026-08-08
parent_epic: defi_master
assigned_vm: NA
priority: P3
last_updated: "2026-08-10"
source: >-
  ag_closeout_auditor scheduled run 2026-08-08 (tranche=defi, slot 13, DISPATCH_ID=agt-615b60)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_07.md,
    /plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md,
    /plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

> **📦 ARCHIVED 2026-08-10 — this audit report is complete.** Every finding it raised has been dispositioned: the
> bounded, worker-determinable items were extracted into
> `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`, cross-day duplicates were collapsed into
> their origin doc, and informational findings were converted to prose (all per
> `cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Three things that must NOT reach a parked doc",
> `unified-trading-pm@bd812c57ad`). Zero open todos remained at archival. Archived as COMPLETE, not superseded —
> `superseded_by` below points to the next dated report in this tranche's chain for navigation only; it does not mean
> this report's content was replaced.

# ag-closeout-audit defi parked findings — 2026-08-08

## Phase 0 summary

`generate_ag_closeout_audit_candidates.py --tranche defi`: 80 corpus members, 17 covering docs (consolidated closeout +
every active AO-dispatch batch/finalize pair + forked-out children — full list in this run's Workflow script), 12
never-cited, 68 cited-somewhere. `check_ag_closeout_linkage.py`: 64 orphans (baseline 69, PASS) — see Finding 4, a known
tool-disagreement, not a fresh gap. Orthogonality check: no new single-AG-plus-one mistags found in the corpus scan.

**Iterative-drain step 1** (re-check prior day's — 2026-08-07 — parked findings before fresh triage) resolved all 5 of
that report's flagged batch11 candidates WITHOUT needing fresh triage agents: 2 archived (Findings 1, 5), 1 flipped to
self-dispatched and its P2 item done (Finding 3 item 1, via slot-6 2026-08-07), 1 covered by batch9's own open todo
(Finding 4 item 1), 1 already flagged `archivable_now` by batch10's prior Phase 1 (Finding 6). See Finding 1 below for
the residual (non-resolved) items from that same report.

## Phase 1 — 12 never-cited candidates classified (Workflow `wf_085c5035-f5f`, 12 agents, 0 errors)

| #   | Doc                                                                                                   | Verdict                                                                                         |
| --- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 1   | `ag_closeout_audit_rollout_2026_07_25.md`                                                             | exclude_cross_cutting (spans 5 AGs + cross-cutting; this skill's own rollout tracker)           |
| 2   | `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`                       | exclude_cross_cutting (spans all 5 AGs)                                                         |
| 3   | `ag_closeout_audit_defi_parked_2026_08_06.md`                                                         | orphaned_never_touched, 0 AO-eligible (both items belong to other tranches — see Finding 2)     |
| 4   | `ag_closeout_audit_defi_parked_2026_08_07.md`                                                         | orphaned_never_touched, 2 AO-eligible (see Finding 1)                                           |
| 5   | `backfill_smoke_write_path_canonical_audit_2026_07_20.md`                                             | exclude_cross_cutting (spans all 5 AGs; defi explicitly out of that audit's own examined scope) |
| 6   | `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`                                       | orphaned_never_touched, 1 AO-eligible but time-gated (see Finding 3)                            |
| 7   | `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`                               | exclude_cross_cutting (4 AGs + sports content; instruments_master epic)                         |
| 8   | `instruments_remaining_work_audit_2026_07_10.md`                                                      | exclude_cross_cutting (spans 5 AGs + cross-cutting; discoverability index, not a work tracker)  |
| 9   | `mdps_features_deadcode_consolidation_2026_07_20.md`                                                  | exclude_cross_cutting (spans all 5 AGs; shared VM-launcher infra)                               |
| 10  | `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`                | exclude_cross_cutting (spans all 5 AGs; deployment-service infra)                               |
| 11  | `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` | exclude_cross_cutting (spans all 5 AGs; shared-host process-lifetime issue)                     |
| 12  | `phantom_audit_estate_coverage_gap_2026_07_10.md`                                                     | exclude_cross_cutting (4 AGs; cefi is the flagship example, not defi)                           |

**Net**: 9/12 exclude_cross_cutting (all confirmed legitimate multi-AG spans — orthogonality check raised zero new
mistags; 2 carry an explicit `tag_concern` note that only reconfirms legitimacy, not a defect). 3/12
`orphaned_never_touched`, detailed as Findings 1-3 below.

## Finding 1 — orphaned_never_touched, 2 AO-eligible: `ag_closeout_audit_defi_parked_2026_08_07.md`

Re-verified against current live state (not just re-reading yesterday's text):

- **Findings 1 and 5 of the 08-07 report are now fully RESOLVED** — both archived to `plans/archive/2026_08/issues/`,
  all todos `[x]` with cited evidence. Both closed via direct AO dispatch of the child doc itself (na-eligibility-audit
  NA→planning reclassification), not via any covering batch plan.
- **Finding 3 item 1 (relaunch mdps-defi-2025/2026 SPOT VMs) is now `[x]` done** (slot-6, 2026-08-07, VMs verified
  RUNNING) — see `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`.
- **Finding 2 (retag recommendation) still NOT executed** — carried forward as Finding 5 below.
- **Finding 4 item 2 (stranded `market-tick-data-service@531a07d8`)** still blocked on pre-existing QG failures,
  unresolved as of 2026-08-07 context-scout re-check.
- **Finding 6 (Kamino verification gap)** still correctly `assigned_vm: NA` — independently re-ran
  `git merge-base --is-ancestor bd153821 origin/main` in market-tick-data-service this run: confirmed the fix is STILL
  not on `main`, so NA-gating remains correct, not a new gap.

**2 genuinely fresh, AO-eligible items remain** (batch11 candidates):

1. **`defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`** — `[DIAG] P3`: investigate raising the per-date
   subprocess timeout from 1800s for DeFi years with 10K+ instruments. Bounded, target file
   (`market-data-processing-service/.../process_handler.py`) named. **RESOLVED (2026-08-10 formalization sweep,
   corroborated by `ag_closeout_audit_defi_parked_2026_08_10.md`'s own iterative-drain step 1) — now cited/picked up in
   `defi_satellite_ao_dispatch_batch11_2026_08_09.md:438`.** No longer a live candidate; not re-added as a todo here to
   avoid duplication.
2. **`defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`** (ARCHIVED 2026-08-09, all 12 todos closed —
   `/plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`) — item 3:
   retry-fixable historical `attempted_failed` residue backfill for now-healthy dex-swap pairs. Bounded SPOT backfill
   re-run, checkable via manifest. Re-verify this parked item is still open before dispatching — the source doc's own
   item 3 todo may already be closed. **RESOLVED (2026-08-10 formalization sweep) — confirmed via the archived doc
   itself: all 12 todos, including item 3, are `[x]` closed.** No longer a live candidate.

## Finding 2 — orphaned_never_touched, 0 AO-eligible for defi: `ag_closeout_audit_defi_parked_2026_08_06.md`

Both of this doc's 2 recorded findings remain genuinely open, re-verified today, but **neither belongs to defi** under
the primary-owner rule:

1. `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` — still
   `status: open`; needs VM-level/root access this sandboxed session lacks; owner is cross-cutting
   (`asset_group: [cefi, defi, tradfi, sports, prediction]`, `parent_epic: infrastructure_master`), not defi.
2. Stale "0 open todos" claims for `phantom_audit_estate_coverage_gap_2026_07_10.md` in
   `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` (line 316) and
   `tradfi_consolidated_closeout_2026_07_18.md` (line 860) — re-verified today, still factually inaccurate (the doc
   carries 1 open `[DATA] P2` checkbox, line 176). Fix belongs to cefi/tradfi workers (editing their own closeout docs),
   not defi.

No new defi action from this finding — reporting only, per this doc's own stated ownership note (defi classifies and
reports; the actual fixes belong to other tranches' workers).

## Finding 3 — orphaned_never_touched, 1 time-gated AO-eligible: `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`

New doc (created 2026-08-07, after last week's audit window) documenting the manifest-consolidator Cloud Scheduler cron
for `market-data-tick-defi-prd` paused as a likely-intentional precondition for SPOT VM
`canonical-migration-defi-rebuild-20260806-223130` (multi-day rebuild, ~47% through at filing). 3 open items, none
covered by any of the 17 covering docs:

1. `[OPERATOR] P3` — confirm with the VM's launcher that the pause was intentional; get a resume-ETA. Operator-gated.
   **RESOLVED (2026-08-10 formalization sweep)** — the source doc's own todo 1 is now `[x]` closed ("stale-check-defi
   -tranche" independent confirmation, 2026-08-09).
2. `[SCRIPT] P3` — once the rebuild VM completes, verify the scheduler resumed and `CONSOLIDATOR_DOWN` clears.
   **AO-eligible but explicitly premature** — gated on the rebuild VM's multi-day completion (ETA 4-5+ days from
   2026-08-07, likely still running as of today). Valid future-batch candidate once that dependency is actually reached,
   not an immediate dispatch. **RESOLVED (2026-08-10 formalization sweep)** — the source doc's own todo 2 is now `[x]`
   closed (alert-clearing half, `ag_closeout_auditor` 2026-08-10 live investigation; see
   `ag_closeout_audit_defi_parked_2026_08_10.md` Finding 5 for the full evidence trail).
3. `[SCRIPT] P3` — undecided design question (should `CONSOLIDATOR_DOWN` alert-routing gain a Slack channel). Explicitly
   "not something to change unilaterally" per the doc's own text — operator/design-gated. **Still open** as of
   2026-08-10 (source doc's own todo 3, `[ ]`) — genuinely design-gated, not re-formalized here since it already has a
   real checkbox at source.

## Finding 4 (informational) — linkage-gate vs candidate-script discrepancy (carried, not re-litigated)

`check_ag_closeout_linkage.py` flags ~10 defi-tagged docs as orphans that `generate_ag_closeout_audit_candidates.py`
(the skill's sanctioned per-tranche coverage definition) shows as `cited_in_covering_doc: True`. Cross-checked every
flagged basename against the candidate script's JSON output this run — all show covered. This is a known, documented
tool blind spot (the linkage gate's narrower "closeout family" graph doesn't deep-scan every batch doc's prose body the
way the candidate script's `CITE_RE` regex does), not a fresh coverage gap. Trust the candidate script + direct doc
reads over the linkage gate for per-tranche coverage questions.

## Finding 5 (informational, carried forward) — retag recommendation still unexecuted after 2 days

From the 08-07 report's Finding 2, still unresolved as of today:

- `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` — carries `asset_group: [defi]`, content
  is cross-cutting strategy-archetype DRIFT venue cleanup. Should be `[ui]` or `[cross-cutting]`.
- `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — carries `asset_group: [defi]`, content
  is stale deployment-ui bundled capability data. Should be `[ui]`.

Both remain well-covered by the defi covering set (not orphaned), just mistagged into the wrong tranche. This is a
`ui`-tranche pickup, not a defi-owned fix — noted here only because it's been open since 2026-08-07 without action; the
defi tranche has no write remit over these docs' tags under the primary-owner rule.

## Finding 6 (informational) — orthogonality check clean

Phase 1's 9 `exclude_cross_cutting` verdicts (of 12 classified) all carry genuine multi-AG (2-6 tag) spans backed by
actual multi-AG content — none is the flagged "defi + exactly one other specific AG" mistag pattern. No new mistags to
report this run.

---

## Batch11 decision

**No `defi_satellite_ao_dispatch_batch11` drafted this round.** Total AO-eligible pool: 3 items (2 ready now from
Finding 1, 1 time-gated from Finding 3). This is well below the established batch size range (batch9=17 todos, batch10=9
todos) and mirrors the 08-07 report's own Option-A precedent, which declined to draft a batch for an even thinner
(1-item) pool and instead let the item carry forward to the next scheduled audit. All 3 items are clearly flagged above
as batch11 candidates — a future audit (or an operator electing to batch now) can pick them up directly without
re-deriving this analysis.

**Parked count reconciliation**: 6 findings (1 orphaned w/ 2 AO-eligible + 1 orphaned w/ 0 AO-eligible + 1 orphaned w/ 1
time-gated AO-eligible + 2 informational carry-forwards + 1 informational orthogonality note) = 6 entries written to
this doc. ✓

## Progress Log

- **ag_closeout_auditor 2026-08-08** (tranche=defi, slot 13, DISPATCH_ID=agt-615b60): scheduled run. Phase 0 (candidate
  script + linkage gate cross-check) + Phase 1 (12-agent Workflow classification of all never-cited candidates) + Phase
  2 (this synthesis) complete. Phase 3: no batch11 drafted (thin pool, see decision above). 6 findings parked, ledger
  reconciled.
- **na-eligibility-audit 2026-08-08** (tranche=defi): KEEP-NA valid — 0 checkboxes (audit-report doc), same pattern as
  the 08-06/08-07 sibling docs. Content re-read end to end; all 6 findings are either informational or already carry
  their own gating (2 AO-eligible batch11 candidates not yet dispatched, 1 time-gated, 2 informational carry-forwards
  belonging to other tranches' write remit, 1 clean orthogonality note). No action for na-eligibility-audit here — this
  doc's own domain is `/ag-closeout-audit`'s orphan-detection tracking, not a todo list this skill dispatches from.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 0 checkboxes -- the most current defi
  ag-closeout-audit parked-findings doc (created 2026-08-08, self-edited 2026-08-09). Confirmed via repo-wide search
  that no 2026-08-09 successor doc exists yet. Still carries live, unclaimed batch11-candidate pointers. Findings
  ledger, not a task doc. Doc stays `assigned_vm: NA`.
- **2026-08-10 (prose-findings formalization sweep)**: converted 0 prose findings into 0 formal todos (4 already
  resolved, cited inline). Full re-read found every genuinely-actionable item in this doc had since been picked up
  elsewhere: Finding 1's 2 batch11 candidates are now resolved (item 1 cited in
  `defi_satellite_ao_dispatch_batch11_2026_08_09.md:438`; item 2's source doc archived 2026-08-09 with all 12 todos
  closed), and Finding 3's items 1-2 are now `[x]` closed at their source doc
  (`defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`). Finding 3 item 3 and Finding 5's retag
  recommendation remain genuinely open but already carry real `- [ ]` checkboxes at their own source docs
  (`defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` todo 3; `ui_consolidated_closeout_2026_07_30.md`'s P2
  todo #5) — not duplicated here. This doc is a findings ledger by design (per its own repeated na-eligibility-audit
  verdicts); no new `## Todos` section added.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up, group 1 of 2)**: KEEP-NA, valid — not an ARCHIVE
  candidate despite 0 open todos. Unlike the ci/prediction tranches (where a same-tranche successor doc that re-derives
  IDENTICAL Phase-0-3 content over an unchanged candidate set gets `status: resolved` + `superseded_by:` — confirmed
  precedent: `ag_closeout_audit_ci_parked_2026_08_07.md`), this doc's defi-tranche siblings (08-06/08-07/08-10, all
  still `status: open`, none archived) form a genuinely growing, incremental corpus (80 members here -> 91 by 08-10)
  where each day surfaces distinct new candidates rather than re-deriving the same ones — the observed, consistent
  tranche convention keeps every daily parked doc active as its own audit-run provenance record. Not locked. Doc stays
  `assigned_vm: NA`.
