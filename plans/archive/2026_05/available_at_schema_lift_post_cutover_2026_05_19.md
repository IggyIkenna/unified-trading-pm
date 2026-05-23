---
title: available_at schema-level invariant lift + QG hardening (post-cutover architectural slice)
parent_epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
locked_by: live-defi-rollout
locked_since: 2026-05-19
related_plans:
  - available_at_lookahead_bias_completion_2026_05_08.md
---

# available_at Schema-Level Invariant Lift (Post-Cutover)

> **TIMING**: post-May-23 cutover. Ride with Block B1 ADT lift + monorepo migration as one architectural slice.

Post-cutover architectural slice migrated from `available_at_lookahead_bias_completion_2026_05_08.md`. Lifts
`available_at` from opt-in runtime gate to type-level invariant (UAC `AvailabilityRule` Protocol + row base class
pydantic validator). Eliminates the silent-wrong-rule class of lookahead bias bugs. Also holds QG STEP 5.67/5.68 static
enforcement items deferred from the completion plan Phase 8 (P2, gated on features_repo_consolidation Phase 5.c + Tab 12
wiring).

Codex SSOTs: `codex/02-data/availability-manifest-and-data-status.md` · `codex/06-coding-standards/quality-gates.md`

---

## Phase A — UAC `AvailabilityRule` Protocol (post-cutover)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. NEW UAC `availability_rule.py` — `AvailabilityRule` Protocol +
      per-source implementations lifted from `availability_stamping.py` (odds_api / tick_timestamp / bar_close / etc.).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. Row base class in UAC requires `available_at: datetime` field; pydantic
      validator invokes row's source's `AvailabilityRule.stamp(row)` automatically. Silent-wrong-rule becomes type-level
      unrepresentable.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. MIGRATE per-source row classes to inherit from base;
      `stamp_available_at_*` opt-in helpers become unnecessary.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. DELETE — `availability_stamping.py` collapses from 330 lines to ~50
      lines (per-source rule implementations only).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. REDUCE — update workspace SSOT pointers in CLAUDE.md + codex for
      `available_at` rules to point to UAC `AvailabilityRule` as canonical.

## Phase B — QG Static Enforcement (post Phase 6 + features consolidation)

Gate: `features_repo_consolidation_2026_05_08` Phase 5.c ships + Tab 12 wiring cleared.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P2. `quality-gates.sh` STEP 5.67 — `record_captured` must be preceded by
      stamping. AST-walk every `record_captured(` callsite; assert stamping helper precedes on same code path. Mirror
      STEP 5.64. Once Phase A ships (auto-stamping via validator), this check becomes vacuous — remove.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P2. `quality-gates.sh` STEP 5.68 — feature-compute callsites must call
      `assert_no_lookahead_for_feature_group`. AST-walk `record_captured(` in consolidated features-service. Gate:
      features_repo_consolidation Phase 5.c.

## Codex SSOT updates (at completion)

- Update `codex/02-data/availability-manifest-and-data-status.md` — `available_at` rule section.
- Update CLAUDE.md `available_at` stamping rules to point to UAC `AvailabilityRule`.
- Archive `unified_trading_library/availability_stamping.py` docstring SSOT reference.

## Temporary states + canonical follow-up plans

- Phase A gated on monorepo migration: ride with Block B1 ADT lift post-May-23.
- Phase B gated on features consolidation: `features_repo_consolidation_2026_05_08` Phase 5.c.
