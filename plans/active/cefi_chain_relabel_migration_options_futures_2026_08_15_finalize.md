---
doc_type: plan
title: CeFi options_chain/futures_chain path-position entity-rename migration — finalize
summary: >-
  Gated finalize plan for cefi_chain_relabel_migration_options_futures_2026_08_15.md (operator ruling
  2026-07-24, task_template.md § 4: every AO-dispatched plan needs a companion finalize plan). Waits on every
  todo of the parent plan via depends_on + gate_on_depends, then reconciles evidence back into the source docs
  this migration was extracted from, re-checks deferred items, and runs the standard archival ritual.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, entity-rename, chain-relabel, finalize, archival]
related:
  [
    /plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
# was: cefi_master (epic-assignment audit 2026-08-19) -- mirrors the parent plan's retag (mtds_mdps_master, shared UAC/MTDS/MDPS partition-path bug proven to hit CeFi+TradFi identically); this finalize doc gates on and reconciles that same parent
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
context_scope:
  [
    /plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [cefi_chain_relabel_migration_options_futures_2026_08_15]
gate_on_depends: true
sequential: true
source: >-
  Authored 2026-08-17 (slot 1, data_engineering) alongside flipping
  cefi_chain_relabel_migration_options_futures_2026_08_15.md to `assigned_vm: planning` — required by
  task_template.md § 4's "every AO-dispatched plan needs a gated finalize plan" hard rule (operator ruling
  2026-07-24). Held via depends_on + gate_on_depends until every parent-plan todo is done.
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
---

# CeFi options_chain/futures_chain path-position entity-rename migration — finalize

> Gated on `cefi_chain_relabel_migration_options_futures_2026_08_15.md` completing ALL 5 phases (`depends_on` +
> `gate_on_depends: true` — every task of this plan waits on every task of the parent). Do not hand-run these todos
> before the parent shows done; the dispatcher already enforces the wait.

## Todos

- [ ] [REVIEW] P1. Reconcile the parent plan's final evidence back into its TRUE source docs — do not trust a source
      doc's own copy of the evidence line, re-verify the cited commit SHA actually exists (`git cat-file -t <sha>`)
      before writing it down:
      1. `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` todo #9 ("Chain relabel migration — part 2 of
         2", currently annotated "RECONCILED 2026-08-16 ... still open, redirected not done") — flip to done, citing
         the parent plan's final evidence.
      2. `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s mirrored/redirected todo (if that doc is still active) —
         same flip.
      3. `data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md`'s "Re-verify the chain relabel migration part 2
         execution plan..." todo (flipped 2026-08-17 citing dispatch-readiness only) — append a closing note citing
         the parent plan's actual completion evidence now that execution finished.
- [ ] [REVIEW] P2. Re-check Phase 0's move-vs-copy resolution and every deferred/excluded item recorded in the parent
      plan's own Progress Log for whether its gate has since cleared; spin any newly-unblocked item into a tracked
      todo/plan if so, rather than leaving it a dangling prose note.
- [ ] [DOC] P2. Run the standard 6-step archival ritual on
      `plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md` (git mv to the dated archive folder +
      SUPERSEDED/exact-successor banner + corpus-wide referrer-path fixup), per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Different tag+priority than todo 1 above
      by design (task_template.md § 4's finalize-plan tag-collision gotcha — the AO done-gate's checked-line
      disambiguator fails closed on two same-tag-priority checked lines in one commit).
- [ ] [DOC] P3. Batch-extraction check: if reconciling todo 1's checkboxes left
      `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` and/or (if still active)
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` with zero open todos of their own, those source docs are ALSO
      archival candidates — run the same 6-step ritual on them, not just their checkbox flip.

## Progress Log

- **2026-08-17 (slot 1, data_engineering)**: drafted this finalize plan alongside dispatching the parent plan, per
  the mandatory finalize-plan hard rule (`task_template.md` § 4). No parent-plan phases have landed yet — this plan
  is gated and will not dispatch until they do.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
