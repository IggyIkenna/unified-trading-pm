---
doc_type: plan
title: CeFi satellite AO batch 7 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch7_2026_08_03.md — machine-held via depends_on + gate_on_depends:
  true until all 3 of that plan's todos are done. Mirrors the batch1 through batch6 finalize pattern: reconcile each
  source doc's checkboxes once its batch-7 todo lands, re-check the two still-blocked items carried forward from batch6
  (Schema v10 transitive gate, estate_orphan_assessment todo 6 cross-tranche conflict) for any whose gate has since
  cleared, then archive batch7 via the standard 6-step ritual.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-7, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch7_2026_08_03.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch6_2026_08_02_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch7_2026_08_03]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-08-03 (scheduled autonomous dispatch, agent-orchestrator slot 7), per
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the cefi batch1 through batch6 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch7_2026_08_03.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# CeFi satellite AO batch 7 — finalize

> **Status: active from the start (2026-07-30 ruling — no double gate).** `gate_on_depends: true` already machine-holds
> every todo below until batch7's own 3 tasks are `done`, regardless of batch7's own `status` (draft or active) — see
> `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md`'s header for the ruling record. Only the batch itself needs
> `status: draft` + explicit operator approval; this finalize plan carries no independent judgment call.

> **Machine-gated on `cefi_satellite_ao_dispatch_batch7_2026_08_03.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because todo 2
> depends on todo 1's reconciliation, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 3 distinct source docs' checkboxes.** Batch 7's 3 todos draw from 3 source docs:
      `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` (Phase 1, all 3 todos only — Phases 2-5 stay
      open, `[OPERATOR]`-gated per that doc's own hard-ordering),
      `issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (this doc is DELETED by batch7's todo 2,
      not checkbox-flipped — confirm the `git rm` landed and the file is genuinely gone from `plans/active/issues/`, no
      reconciliation needed on a deleted file),
      `issues/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md` (the `[DIAG] P2` todo only — its
      `[DECISION] P2` `[OPERATOR]` todo stays open, unaffected). For each landed batch-7 todo, flip the corresponding
      checkbox/section in its named source doc citing the shipping commit — **verify the commit exists and is reachable
      on `origin/live-defi-rollout` before citing it**. If todo 3's DIAG finding was positive, also confirm
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s P1.2 was updated with the correct
      ledger-root pointer (per batch7 todo 3's own done-when). **Done when**: every landed todo's source checkbox is
      flipped with a verified commit (or, for the deleted doc, its removal is confirmed), and each source doc's
      remaining-open count is explicitly re-stated rather than assumed.

- [ ] [REVIEW] P1. **Re-check the two items carried forward from batch6's Deferred section for cleared gates.** (a) Has
      `issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1` "close the three §5 gaps" todo
      closed, and has Stage 1 (write-enforce) shipped? If so, the Schema v10 `instrument_id_form` backfill becomes a
      normal batch8 candidate — record it, do NOT draft the todo here (this finalize plan's scope is reconciliation, not
      fresh drafting). (b) Has the operator ruled on `issues/estate_orphan_assessment_2026_07_21.md` todo 6's
      cross-tranche boundedness disagreement (cefi/sports KEEP-NA vs. defi RECLASSIFY)? If so, record the ruling and its
      consequence (a batch8 candidate if ruled AO-eligible; a closed non-issue otherwise). **Done when**: both items
      carry either a "gate cleared → batch8 candidate" note or a dated re-verification that they are still blocked,
      exactly as batch7's own body already re-confirmed for this run.

- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch7_2026_08_03.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm the "Cross-tranche notes" and "Archival-hygiene housekeeping" sections
      (informational, not gated AO items) need no separate migration since they were never batch todos → add the archive
      banner → run the codex-alignment check (batch7 creates no new durable contract; confirm still true) → grep the
      corpus for every referrer of `cefi_satellite_ao_dispatch_batch7_2026_08_03` and repoint each to the archived path
      → clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_08/`, every
      corpus referrer resolves to the new path, `run_hygiene_sweep.sh` stays green, and this finalize doc is archived
      alongside it in the same commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this plan's todo 3
  executes.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
