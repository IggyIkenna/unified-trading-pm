---
doc_type: plan
title: CeFi Track-7 candle-namespace residual — gated delete of the 149 stale bundle-collision objects
summary: >-
  Track 7's terminal, `[OPERATOR]`-tagged step only — deleting the 149 stale legacy per-leg `processed_candles/` objects
  (BYBIT futures_chain + DERIBIT options_chain bundle-collision residual). Forked from
  cefi_consolidated_closeout_2026_07_18.md's Track 7 (2026-07-25 split). The verify (raw-tick presence for the remaining
  6 of 8 affected days) + the targeted MDPS `--force` candle backfill are deliberately NOT re-drafted here — already
  combined into one ordering-safe todo as candidate 7 of cefi_consolidated_native_ao_extract_2026_07_25.md. This plan
  machine-gates the delete on that plan's completion instead, preserving the original verify->backfill->delete ordering
  constraint via a cross-plan gate rather than intra-plan sequencing.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [cefi, close-out, candle, track-7, bundle-collision, operator-gated-delete]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/cefi_track7_candle_namespace_residual_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  Forked from cefi_consolidated_closeout_2026_07_18.md's Track 7 ("Candle namespace bundle-collision residual"),
  2026-07-25 split — path 3 of that parent's 4 reachability paths, the candle-namespace path. Kept as its OWN
  sequential:true child rather than merged into the misc-hygiene plan per an explicit 2026-07-25 operator ruling
  ("correctness over file count" — a real ordering constraint deserves its own machine-enforced gate even at 1 todo),
  and per Track 7's own 2026-07-24 finding that this delete step was tagged [OPERATOR] specifically to stop it racing
  ahead of verify/backfill under AO's concurrent-dispatch default.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi Track-7 candle-namespace residual — gated delete

> **Why this plan has only 1 todo (deliberate, not an oversight).** Track 7's original 3-step shape was verify(6
> remaining days) → backfill(--force) → delete(149 objects). The first two steps are already drafted, combined into ONE
> ordering-safe todo, as candidate 7 of `cefi_consolidated_native_ao_extract_2026_07_25.md` (drafted by a parallel
> sibling triage of this same parent's native todos) — re-drafting them here would duplicate that work. Instead, this
> plan exists SOLELY to hold the `[OPERATOR]`-gated delete step, machine-gated (`depends_on` + `gate_on_depends: true`)
> on `cefi_consolidated_native_ao_extract_2026_07_25.md`'s entire todo set being done — which, by construction, includes
> its candidate-7 verify+backfill work. This is coarser than gating on that one todo alone (AO's dependency model has no
> per-todo cross-plan gate — see `task_template.md` §4), but it is CORRECT: the delete cannot dispatch before
> verify+backfill land. `sequential: true` is declared for pattern consistency and to block any future todo added to
> this plan from skipping the gate. Companion gated finalize:
> `cefi_track7_candle_namespace_residual_finalize_2026_07_25.md`.

## Todos

- [ ] [OPERATOR] P2. **Delete the 149 stale legacy per-leg candle objects** (listed in
      `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv`) — Track 7's terminal step, ONLY after the
      regenerated bundles are verified complete (via `cefi_consolidated_native_ao_extract_2026_07_25.md`'s candidate-7
      todo, which this plan is gated on). Deleting before the bundles are verified complete causes permanent,
      unrecoverable data loss — 93 BYBIT `futures_chain` + 56 DERIBIT `options_chain` objects are real, distinct
      per-contract-leg candle files that lost a bundle-target-collision race, with no other copy anywhere. Tagged
      `[OPERATOR]` per `task_template.md` §3 finding F +
      `/codex/05-infrastructure/gcs-and-manifest-delete-safety-protocol.md` (2026-07-24 AO-flip-safety audit finding —
      this delete previously sat untagged in the parent, which under AO's same-priority concurrent-dispatch default
      could have raced it against the verify/backfill work instead of strictly following it). Repo:
      market-data-processing-service. **Done when**: the regenerated `ticks.parquet` bundles for all 8 affected
      `(day, venue)` cells are independently confirmed to contain every leg's data (row/ symbol count check against the
      pre-delete per-leg object count — re-verify this yourself, do not just trust the upstream plan's own claim), the
      149 listed objects are deleted, and `candle_feature_canonical_path_divergence_2026_07_20.md` todo 19 is updated to
      reference this track's resolution.

## Reconciliation

Once this plan's todo ships, flip Track 7's delete checkbox in `cefi_consolidated_closeout_2026_07_18.md` and close todo
19 in `candle_feature_canonical_path_divergence_2026_07_20.md`, citing the delete operation's evidence. Gated via the
companion `cefi_track7_candle_namespace_residual_finalize_2026_07_25.md`
(`depends_on: [cefi_track7_candle_namespace_residual_2026_07_25]` — `gate_on_depends: true`).

## Codex SSOTs

`/codex/05-infrastructure/gcs-and-manifest-delete-safety-protocol.md`,
`/codex/02-data/availability-manifest-and-data-status.md`. No new durable contract is created by this plan.
