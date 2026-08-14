---
doc_type: issue
title: ag-closeout-audit tradfi parked findings 2026-08-10
summary: >-
  Phase 0-2 audit of 27 tradfi-primary candidates (from 81 tradfi-tagged docs, 29 covering-plan + 25 multi-AG excluded).
  No batch13 draft warranted — genuinely orphaned docs are all operator-gated or conflicted. Phase 3 skipped.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, tradfi, parked, orphan-audit]
related:
  - /plans/active/tradfi_consolidated_closeout_2026_07_18.md
  - /plans/active/tradfi_satellite_ao_dispatch_batch11_2026_08_10.md
  - /plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md
created: "2026-08-10"
author: slot-24 (ag_closeout_auditor)
priority: P3
parent_epic: tradfi_master
source: ag-closeout-audit tradfi Phase 0-2 2026-08-10 (dispatch agt-ab2792, slot-24)
resolved_by:
locked_by:
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch11_2026_08_10.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# ag-closeout-audit tradfi — parked findings 2026-08-10

## Resolved this run (mechanical fixes, shipped in-run)

1. **Orthogonality fix**:
   `plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` — dropped
   `cross-cutting` from `asset_group: [tradfi, cross-cutting]` → `[tradfi]`. Doc is purely tradfi-specific
   (tradfi_master parent_epic, no other AGs in body, only references tradfi_consolidated_closeout).

## Informational findings (no action needed, no todos)

### Finding 1 — 3 genuinely orphaned docs, all operator-gated or conflicted (not batchable)

The 3 docs below have NO coverage in any active dispatched covering plan's `## Todos` section. None are AO-eligible:
each is operator-gated or carries a live conflict that must resolve before any batch extraction.

1. **`databento_ice_opra_subscription_ask_2026_08_09.md`** (open=2, NA) — BLOCKED-CREDENTIALS: ICE/OPRA subscription is
   a billing decision only the operator can make. Correctly NA. Cited in
   `tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`'s body but not in its Todos section. Per the skill's
   coverage bar, body citations do not count.

2. **`tradfi_autonomous_session_operator_decisions_2026_07_25.md`** (open=1, NA) — Sole open todo bundles propagation of
   3 already-ruled items (5/7/8 from 2026-08-07) spanning different target files/repos. Needs decomposition into
   discrete per-action todos before any single piece is independently dispatchable. Tagged
   MISCLASSIFIED_LIKELY_AO_ELIGIBLE by na-eligibility-audit but not promoted pending split.

3. **`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`** (open=2, NA) — Live CONFLICT with
   `governance_sweep_deferred_followups_2026_08_06.md`'s `[DIAG] P2` todo (both docs claim the CME instrument_id format
   verification step). Operator already ruled Option A (2026-08-06), and the code fix is clear-scope — blocked only on
   the conflict resolving. Conflict-gated (re-triageable in a future batch).

**No batch13 draft warranted from these 3.** All 3 fail the bounded-outcome bar: a billing decision, a bundled
propagation todo needing decomposition, and a conflict-gated code fix.

### Finding 2 — 4 docs are draft-covered (batch11/12, both status: draft + assigned_vm: NA)

These will become fully covered once batch11/12 are flipped to `status: active` + `assigned_vm: planning`:

- `cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md` (open=2) → batch12 Todos
- `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` (open=3) → batch11 Todos
- `tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` (open=2) → batch11 Todos
- `tradfi_live_shard_atom_unknown_writer_2026_08_09.md` (open=1) → batch11 Todos

**Operator action needed**: flip batch11 and batch12 from draft→active (the BATCH plans only; their finalize siblings
are already `status: active` per the skill's Phase 3 rule). This unblocks 4 docs + 8 open todos.

> **RESOLVED 2026-08-12 (/plan-reconcile, operator interactive ruling)**: batch11 + batch12 flipped
> `status: draft`→`active` and `assigned_vm: NA`→`planning`. Reason for flipping NOW rather than waiting: a live check
> this same run found the tradfi host-cron dispatch mechanism was never actually paused and is currently launching an
> out-of-scope `nq-2022` shard (see `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`) —
> batch11's shipped `_cme_root_universe()` MVP_SCOPE-consulting fix needs to actually dispatch to close that gap, not
> sit in draft. This unblocks the 4 docs + 8 open todos named in Finding 2 above.

### Finding 3 — 6 archivable candidates (0 open todos, no hidden prose work)

- ~~`plan_reconciler_findings_2026_08_06.md` — locked_by: plan_reconciler (run in progress).~~ **RESOLVED 2026-08-10**:
  `[unlock-plan]` granted by direct operator ruling; lock was stale (the run that set it had ended, 0 open todos).
  Archived, and the stale duplicate left at `plans/active/issues/` deleted. See
  `/plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md` § "Full sweep".
- ~~`plan_reconciler_findings_tradfi_2026_08_09.md` — locked_by: plan_reconciler (agt-642862).~~ **RESOLVED
  2026-08-10**: same ruling, same disposition.
- `tradfi_backfill_oom_remediation_2026_06_24.md` — 0 open, 12 done. locked_by: live-defi-rollout.
- `tradfi_canonical_path_migration_design_2026_07_19.md` — 0 open, 1 done. locked_by: live-defi-rollout.
- `tradfi_recovery_quarantine_registration_gap_2026_07_27.md` — 0 open, 4 done. locked_by: live-defi-rollout.
- `tradfi_es_opt_manifest_chain_field_empty_blocking_coverage_2026_08_10.md` — 0 open, 0 done (pure findings doc;
  documents a live bug whose fix belongs in code repos, not in this doc). Not locked.

All 6 are `archivable_now` by content but 5 are locked. The unlocked one (`tradfi_es_opt_manifest_chain_field`)
documents an active ES_OPT bug (chain='' rejected by manifest writer) — the fix should ship in MTDS/UTL code, and this
doc archives once batch6 todo#2 (ES_OPT coverage) resolves.

## Progress Log

- **2026-08-10, slot-24 (ag_closeout_auditor)**: Phase 0-2 audit complete. 27 tradfi-primary candidates classified. 3
  genuinely orphaned (operator-gated/conflicted), 4 draft-covered, 14 covered-by-active-plans-or-self-dispatched, 6
  archivable (0 open). No batch13 draft — no AO-eligible bounded orphaned work to extract.
- **context-scout 2026-08-14**: populated context_scope (4 entries)
