---
doc_type: plan
title: CeFi satellite AO batch 6 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch6_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until all 6 of that plan's todos are done. Mirrors the batch1 through batch5 finalize pattern: reconcile each
  source doc's checkboxes once its batch-6 todo lands, re-check batch6's own Deferred items (the transitively-gated
  Schema v10 item and the carried-forward estate_orphan_assessment cross-tranche conflict) for any whose gate has since
  cleared, then archive batch6 via the standard 6-step ritual.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.35
estimate_calibrated_ai_days: 0.28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch6_2026_08_02]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-08-02 (scheduled autonomous dispatch, agent-orchestrator slot 8), per
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the cefi batch1 through batch5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch6_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# CeFi satellite AO batch 6 — finalize

> **Status: active from the start (2026-07-30 ruling — no double gate).** `gate_on_depends: true` already machine-holds
> every todo below until batch6's own 6 tasks are `done`, regardless of batch6's own `status` (draft or active) — see
> `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md`'s header for the ruling record. Only the batch itself needs
> `status: draft` + explicit operator approval; this finalize plan carries no independent judgment call.

> **Machine-gated on `cefi_satellite_ao_dispatch_batch6_2026_08_02.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 6 tasks in that plan are `done`. `sequential: true` because todo 2
> depends on todo 1's reconciliation, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 5 distinct source docs' checkboxes.** Batch 6's 6 todos draw from 5 source docs:
      `cefi_ml_directional_continuous_live_2026_06_20.md` (1 sub-requirement of the `[VERIFY] P0` todo only — do NOT
      flip that todo's own checkbox, the VM-run half is still open),
      `issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27.md` (item 2 of 4 only),
      `issues/fail_hard_canonical_enforcement_design_2026_07_20.md` (the Stage-0 `[DATA] P2` todo only — Stage 2 stays
      open, see batch6's Deferred), `issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md` (both todos),
      `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` (the `[SCRIPT] P2` and `[RESEARCH] P2` todos
      only — the `[OPERATOR]`/`[SCRIPT]` P1 items stay open, unaffected by this batch). For each landed batch-6 todo,
      flip the corresponding checkbox/section in its named source doc citing the shipping commit — **verify the commit
      exists and is reachable on `origin/live-defi-rollout` before citing it**. Then, per source doc, re-check whether
      it now has 0 open items remaining in **both** checkbox AND prose form, and only flip `status: resolved` on a
      genuine zero (note in advance: none of the 5 source docs will reach zero by design — each retains at least one
      deliberately-excluded residual item: the VM-run half, items 1/3/4, Stage 1/2, [none for mtds_docker if both jobs
      resolve — check freshly], and the P1 convention-decision items respectively). **Done when**: every landed todo's
      source checkbox is flipped with a verified commit, and each source doc's remaining-open count is explicitly
      re-stated rather than assumed.

- [ ] [REVIEW] P1. **Re-check batch6's own Deferred items for cleared gates.** Walk each Deferred entry in
      `cefi_satellite_ao_dispatch_batch6_2026_08_02.md` and re-verify its specific blocking condition: (a) the
      transitively-gated Schema v10 item — has `issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s
      `[DESIGN] P1` §5-gaps item closed and has Stage 1 (write-enforce) shipped? If so, record it as a `batch7`
      candidate — do NOT draft the todo here, this finalize plan's scope is reconciliation, not fresh drafting. (b) the
      carried-forward `estate_orphan_assessment_2026_07_21.md` todo-6 cross-tranche conflict — has the operator ruled
      which tranche's verdict wins? **Done when**: each Deferred entry carries either a "gate cleared → batch7
      candidate" note or a dated re-verification that it is still blocked.

- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch6_2026_08_02.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate every remaining Deferred item to a tracked todo elsewhere (todo 2 above
      should have resolved or re-confirmed each — verify none silently vanish) → add the archive banner → run the
      codex-alignment check (batch6 creates no new durable contract; confirm still true) → grep the corpus for every
      referrer of `cefi_satellite_ao_dispatch_batch6_2026_08_02` and repoint each to the archived path → clear
      `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_08/`, every corpus
      referrer resolves to the new path, `run_hygiene_sweep.sh` stays green, and this finalize doc is archived alongside
      it in the same commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this plan's todo 3
  executes.
