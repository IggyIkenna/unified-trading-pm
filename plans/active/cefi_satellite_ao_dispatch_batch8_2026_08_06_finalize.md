---
doc_type: plan
title: CeFi satellite AO batch 8 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch8_2026_08_06.md — machine-held via depends_on + gate_on_depends:
  true until all 3 of that plan's todos are done. Mirrors the batch1 through batch7 finalize pattern: reconcile each
  source doc's checkboxes once its batch-8 todo lands, re-check the two long-carried-forward deferred items (Schema v10
  transitive gate, estate_orphan_assessment todo 6 cross-tranche conflict — both re-confirmed still blocked as of
  2026-08-06, unchanged since batch7's own 2026-08-03 re-check) for any whose gate has since cleared, then archive
  batch8 via the standard 6-step ritual.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch8_2026_08_06.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch7_2026_08_03_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
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
depends_on: [cefi_satellite_ao_dispatch_batch8_2026_08_06]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-08-06 (scheduled autonomous dispatch, agent-orchestrator slot 3, dispatch
  agt-02411c), per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated
  finalize plan, mirroring the cefi batch1 through batch7 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch8_2026_08_06.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch7_2026_08_03_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# CeFi satellite AO batch 8 — finalize

> **Status: active from the start (2026-07-30 ruling — no double gate).** `gate_on_depends: true` already machine-holds
> every todo below until batch8's own 3 tasks are `done`, regardless of batch8's own `status` (draft or active) — see
> `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md`'s header for the ruling record. Only the batch itself needs
> `status: draft` + explicit operator approval; this finalize plan carries no independent judgment call.

> **Machine-gated on `cefi_satellite_ao_dispatch_batch8_2026_08_06.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because todo 2
> depends on todo 1's reconciliation, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 3 distinct source docs' checkboxes.** Batch 8's 3 todos draw from 3 source docs:
      `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` (the G1.2/GATE-G4/MANIFEST_ALLOW_STALE_FALLBACK items only —
      the doc's other 2 open items, EXTENDED-STARKNET CF-11 and formal GATE G1 sign-off, stay open, untouched),
      `issues/mdps_derivative_ticker_single_instrument_high_rss_2026_08_03.md` (promote the "Implement the fix" prose
      item to a real `[x]` checkbox citing the shipping commit — it was never its own checkbox in the source doc, batch
      8 todo 2 IS that promotion), `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` (the
      `[SCRIPT]     P1` item's docstring-only sub-part (a) — leave the item's checkbox open overall, since sub-part
      (b)'s contingent Option-B-revert stays blocked on the still-open `[OPERATOR] P1` ratification). For each landed
      batch-8 todo, flip the corresponding checkbox/section in its named source doc citing the shipping commit —
      **verify the commit exists and is reachable on `origin/live-defi-rollout` before citing it**. **Done when**: every
      landed todo's source checkbox is flipped (or, for the prose-only item, promoted+flipped) with a verified commit,
      and each source doc's remaining-open count is explicitly re-stated rather than assumed. — **DONE 2026-08-07**: (1)
      instruments doc: G1.2/GATE-G4/MANIFEST_ALLOW_STALE_FALLBACK flipped at unified-trading-pm@82a9ec25 (slot-16,
      2026-08-07); 2 open items remain (EXTENDED CF-11, GATE G1 sign-off). (2) mdps doc (archived): "Implement the fix"
      promoted to `[x] ✅ [BACKEND] P1` checkbox citing `market-data-processing-service@4f2b99e` (verified reachable on
      origin/live-defi-rollout); 0 open items remain. (3) okx doc: `[SCRIPT] P1` sub-part (a) marked DONE-ELSEWHERE
      citing `market-tick-data-service@8a6bbc97` (verified reachable); sub-part (b) marked MOOT (operator ratified
      Option A 2026-08-06); checkbox left open per plan; 3 items nominally open (`[SCRIPT] P1` shell, `[SCRIPT] P2`,
      `[RESEARCH] P2`).

- [ ] [REVIEW] P1. **Re-check the two items carried forward from batch4→batch6→batch7's Deferred/re-check sections for
      cleared gates — still unresolved as of 2026-08-06, third consecutive re-check to find them unchanged.** (a) Has
      `issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1` "close the three §5 gaps" todo (line
      ~156) closed? If so, the Schema v10 `instrument_id_form` backfill becomes a normal batch9 candidate — record it,
      do NOT draft the todo here (this finalize plan's scope is reconciliation, not fresh drafting). (b) Has the
      operator ruled on `issues/estate_orphan_assessment_2026_07_21.md` todo 6's cross-tranche boundedness disagreement
      (cefi/sports KEEP-NA vs. defi RECLASSIFY, line ~549's "Operator/next-toucher: rule on todo 6's boundedness" note)?
      If so, record the ruling and its consequence (a batch9 candidate if ruled AO-eligible; a closed non-issue
      otherwise). If BOTH are still unresolved a fourth time when batch9 is next drafted, flag explicitly for the
      operator as a standing item rather than silently re-deferring a fourth time — three consecutive no-change
      re-checks (batch6→7→8) is a real signal this needs direct attention, not more automated re-triage. **Done when**:
      both items carry either a "gate cleared → batch9 candidate" note or a dated re-verification that they are still
      blocked, exactly as batch7 and batch8's own bodies already re-confirmed for this run.

- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch8_2026_08_06.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm the "Cross-tranche notes", "Archival-hygiene housekeeping" and
      "Self-dispatched, linkage-fix-only" sections (informational, not gated AO items) need no separate migration since
      they were never batch todos → add the archive banner → run the codex-alignment check (batch8 creates no new
      durable contract; confirm still true) → grep the corpus for every referrer of
      `cefi_satellite_ao_dispatch_batch8_2026_08_06` and repoint each to the archived path → clear `locked_by` (already
      empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_08/`, every corpus referrer resolves to
      the new path, `run_hygiene_sweep.sh` stays green, and this finalize doc is archived alongside it in the same
      commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this plan's todo 3
  executes.

## Progress Log

- **context-scout 2026-08-06**: populated/refreshed context_scope (4 entries) — added the batch7 finalize sibling
  (immediate precedent in the finalize-pattern chain); `_finalize` gate doc, no source-code paths per the skip-source
  carve-out.
