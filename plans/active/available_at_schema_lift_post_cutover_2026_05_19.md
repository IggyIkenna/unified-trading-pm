---
plan_type: code+refactor
asset_group: cross-cutting
owner: ikenna
created: 2026-05-19
last_updated: 2026-05-19
locked_by: live-defi-rollout
locked_since: 2026-05-19
name: available-at-schema-lift-post-cutover-2026-05-19
title: "available_at schema-level invariant lift + QG hardening (post-cutover architectural slice)"
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
overview: >-
  Post-May-23-cutover architectural slice. Lifts `available_at` from an opt-in runtime gate to a type-level invariant
  (UAC `AvailabilityRule` Protocol + row base class pydantic validator). Eliminates the silent-wrong-rule class of
  lookahead bias bugs. Composes with Block B1 ADT lift + monorepo migration. Also holds QG STEP 5.67/5.68 static
  enforcement items deferred from available_at_lookahead_bias_completion_2026_05_08 Phase 8 (P2, gated on
  features_repo_consolidation Phase 5.c + Tab 12 wiring).

type: refactor
epic: epic-code-completion
status: todo
---

# available_at Schema-Level Invariant Lift (Post-Cutover)

> **TIMING**: post-May-23 cutover. Ride with Block B1 ADT lift + monorepo migration as one architectural slice. Do NOT
> start before May-23 cutover ships.

**MIGRATED FROM**: `available_at_lookahead_bias_completion_2026_05_08.md` § "Audit-2026-05-10 finding" (UAC Protocol
items, Phase 8 QG items — 2026-05-19)

---

## Background

Today's enforcement is two-layer:

1. opt-in stamping helpers in `unified_trading_library/availability_stamping.py` (330 lines)
2. runtime gate `manifest_writer.assert_available_at_present` that raises `LookaheadBiasError` for missing/null

**Gap**: the gate catches missing-stamp at write time, not at row-construction time. An adapter that stamps with the
WRONG rule (e.g. `event_time` for a post-match stat that should use `match_end_time`) never fails — silent lookahead
bias. Highest-priority Block-B item per 2026-05-10 audit.

---

## Phase A — UAC `AvailabilityRule` Protocol (post-cutover)

**MIGRATED FROM**: `available_at_lookahead_bias_completion_2026_05_08.md` lines 851-859

todos:

- [ ] [SCRIPT] P1. **NEW** UAC `availability_rule.py` — `AvailabilityRule` Protocol + per-source implementations lifted
      from `availability_stamping.py`. Each source (odds_api / tick_timestamp / bar_close / etc.) gets a typed rule
      object.

- [ ] [SCRIPT] P1. **NEW** row base class in UAC requires `available_at: datetime` field; pydantic validator on every
      row class invokes the row's source's `AvailabilityRule.stamp(row)` automatically. Silent-wrong-rule class becomes
      type-level unrepresentable.

- [ ] [SCRIPT] P1. **MIGRATE** per-source row classes inherit from the base; `stamp_available_at_*` opt-in helpers
      become unnecessary (auto-applied via validator). Update all callsites.

- [ ] [SCRIPT] P1. **DELETE** 330 lines of `availability_stamping.py` collapse to ~50 lines (per-source rule
      implementations only). Remove opt-in stamping call requirements from all adapters.

- [ ] [SCRIPT] P1. **REDUCE** cross-referenced CLAUDE.md + codex doc surface for `available_at` rules collapses to one
      canonical UAC reference. Update workspace SSOT pointers.

---

## Phase B — QG Static Enforcement (post Phase 6 + features consolidation)

**MIGRATED FROM**: `available_at_lookahead_bias_completion_2026_05_08.md` Phase 8 (lines 491-499)

Gate: `features_repo_consolidation_2026_05_08` Phase 5.c ships + Tab 12 wiring cleared.

todos:

- [ ] [SCRIPT] P2. **`quality-gates.sh` STEP 5.67 — `record_captured` must be preceded by stamping**. AST-walk every
      `record_captured(` callsite across the workspace. Assert: on the same code path, a stamping helper call
      (`stamp_available_at_*` OR `compute_bar_close_boundary` for bars) precedes it. Mirror writegate STEP 5.64 (cluster
      validation static check). Fail-loud at CI; no warnings. Once Phase A ships (auto-stamping via validator), this
      check becomes vacuous — remove.

- [ ] [SCRIPT] P2. **`quality-gates.sh` STEP 5.68 — feature-compute callsites must call
      `assert_no_lookahead_for_feature_group`**. AST-walk every `record_captured(` in features-\* services
      (post-consolidation: consolidated `features-service`). Assert: writer-boundary call precedes the record. Gate:
      features_repo_consolidation Phase 5.c ships. Pairs with Phase 6 Tab 12 wiring.

---

## Codex SSOT updates (at completion)

- Update `codex/02-data/availability-manifest-and-data-status.md` — `available_at` rule section
- Update CLAUDE.md `available_at` stamping rules to point to UAC AvailabilityRule as canonical
- Archive `unified_trading_library/availability_stamping.py` docstring SSOT reference

---

## Success criteria

- Every row class in UAC inherits base with `available_at` validator; wrong-rule bias = type error
- `availability_stamping.py` reduced to ≤50 lines
- QG STEP 5.67/5.68 wired and green on full workspace scan
- No regression on existing `LookaheadBiasError` unit tests

---

## Temporary states + their canonical follow-up plans

- **Phase A gated on monorepo migration**: ride with Block B1 ADT lift. Named gate: post-May-23 cutover window.
- **Phase B gated on features consolidation**: `features_repo_consolidation_2026_05_08` Phase 5.c.
