---
doc_type: plan
title: TradFi satellite AO batch 9 — batch8-finalize deferred-item extraction (1 cleared conflict-gated item)
summary: >-
  Extracted by `tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md`'s todo 2 (re-check batch8's own
  Deferred/Flagged sections). Batch8's conflict-gated item — `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s
  todo 2 (relaunch the TRADFI:volatility benchmark) — is now clean: both sides of the original conflict have resolved
  (todo 1's `_resolve_spot_perp` fix shipped + verified 2026-08-16; `governance_sweep_deferred_followups_2026_08_06.md`'s
  duplicate CME `instrument_id`-format `[DIAG]` todo independently verified 2026-08-14). This is the sole item this pass
  found cleared-AND-safely-scoped for direct extraction; other cleared/readied items found during the same re-check
  (the legacy-twin bucket delete fix, autonomous-session-decision propagation) are tracked separately — see batch8's
  finalize doc Progress Log for the full accounting of all 11 Deferred/Flagged items re-checked this pass.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-9, satellite-docs, conflict-checked]
related:
  [
    /plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md` todo 2, dispatch
  tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize-597096e91311, slot 5 (review), 2026-08-16. Per the
  ag-closeout-audit skill's autonomous-mode contract, a freshly-drafted batch always ships `status: draft` regardless of
  how clean the conflict-check came back — flipping to `active` is an operator decision, never autonomous.
assigned_role: data_engineering
effort: max
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# TradFi satellite AO batch 9 — deferred-item extraction

> **Status: draft — needs operator review before dispatch**, per the ag-closeout-audit skill's autonomous-mode
> contract. This batch's sole todo touches only `features-service`'s launcher config — no file collision with any
> other active tradfi batch (batch8's finalize plan is docs-only; no other active tradfi batch exists at drafting
> time).

## Why this batch exists

`tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md`'s todo 2 re-checked batch8's own Deferred/Flagged
sections now that time has passed. One item — the conflict-gated `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`
todo 1/2 pair — is now genuinely clean:

- **The conflict itself resolved**: `governance_sweep_deferred_followups_2026_08_06.md`'s `[DIAG] P2` todo (verify the
  CME `instrument_id` format) was independently confirmed done 2026-08-14 ("VERIFIED — CME FUTURE `instrument_id`
  format confirmed against BOTH code and the live production catalogue").
- **The blocked fix itself also shipped**: `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1
  (make `_resolve_spot_perp` asset-group-aware for TRADFI) is now `[x]` DONE — verified 2026-08-16 by `plan_reconciler`
  (tranche=tradfi, agt-a74a6a), citing `features-service@a46681c84a` as the landed fix, an ancestor of
  `origin/live-defi-rollout`.
- **What's left is exactly todo 2** in that same source doc — a real relaunch of the TRADFI:volatility benchmark now
  that the fix is live, to capture real throughput. This was explicitly un-drafted before now (blocked on the fix
  landing); it is bounded, deterministic-outcome, AO-eligible work with a crisp done-when.

## Todos

- [ ] [DATA] P2. **Relaunch the TRADFI:volatility features benchmark now that `_resolve_spot_perp` is
      asset-group-aware.** Run `launch-features-vm.sh FAMILY=volatility ASSET_GROUP=TRADFI` (or the current equivalent
      CLI invocation per `features-service`'s launcher conventions at dispatch time) to capture real throughput for the
      TRADFI volatility feature family, now that `_resolve_spot_perp` correctly resolves (venue, symbol) for TRADFI FX
      underlyings (`features-service@a46681c84a`). **Done when**: a completed VM run reports real (non-zero,
      non-error) throughput/group-count numbers for TRADFI:volatility, and
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 2 is flipped citing the run's evidence
      (VM name, log path, measured throughput). If the doc then reaches 0 open items, flip its `status` to `resolved`
      per the normal archival discipline. Repo: features-service (VM launch only — code fix already shipped, no new
      code expected). Source: `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`.

## File-collision matrix

| Todo | Primary file(s) touched                                        |
| ---- | ---------------------------------------------------------------- |
| 1    | VM launch only (`launch-features-vm.sh` invocation) — no source file edits expected |

## Reconciliation

Once this todo ships, flip the corresponding checkbox in `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`,
citing this plan's evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch9_2026_08_16_finalize.md` (`depends_on` on this plan plus `gate_on_depends: true`),
mirroring the batch1-8 finalize pattern.

## Progress Log

- **2026-08-16 (slot 5, review, via `tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md` todo 2)**: created —
  extracted the one item this pass found both cleared AND cleanly scoped for direct extraction. See batch8's finalize
  doc Progress Log for the full 11-item Deferred/Flagged accounting (including 2 other cleared-but-differently-handled
  items: the legacy-twin bucket delete, already independently extracted into its own dedicated plan same-day; and the
  autonomous-session-decision propagation items, noted ready but recommended as their own dedicated follow-up given
  their multi-file blast radius).

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
carries the conflict-check + batch-naming convention this plan follows.
