---
doc_type: issue
title: Phase 8 Codex Audit — strategy-service archetype codex drift (2026-05-15)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
author: slot-3
resolved: 2026-05-17
resolution:
  AUDIT-COMPLETE — drifts 1-5 ✅ shipped 2026-05-15 by slot 6. P3-P5 follow-ups have named owners (slot 1 codex docs +
  features-onchain publisher) and explicit successors. Primary audit deliverable (codex/code parity for staked-basis +
  APD archetypes) closed per body § "RESOLVED 2026-05-17 slot 4".
source:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
    strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py,
  ]
locked_by: live-defi-rollout
---

# Phase 8 Codex Audit — Archetype Codex/Code Drift

Audit performed 2026-05-15 per item 12 of slot 3 queue. Compared `codex/09-strategy/architecture-v2/archetypes/` docs
against shipped code in strategy-service tab/hk/3. Found 5 drifts across 2 archetype docs.

---

## What I found

### Drift 1 — `carry-staked-basis.md`: Phase 6B hedge ratio marked as FUTURE but is SHIPPED

**Codex says (lines 32–37):**

> current hedge sizing is **STATIC** at `eth_qty * (1 - margin_haircut)` … NO per-tick / per-bar adjustment for
> LST/native peg drift. Phase 6B implementation (Harsh slot 4) **introduces** dynamic adjustment using LST exchange rate
> stream …

**Actual code (shipped):** Phase 6B IS shipped: `dynamic_hedge_ratio.py` + `compute_dynamic_hedge_ratio()` function are
live in `staked_basis.py:on_tick` at `strategy-service@d6be15b`. The formula is now
`eth_qty * lst_native_rate_now * (1 - margin_haircut)`.

**Severity:** High — codex says STATIC when code is DYNAMIC.

---

### Drift 2 — `carry-staked-basis.md`: stale `staked_basis.py:264` line reference

**Codex says:** "confirmed at `staked_basis.py:264`"

**Actual:** The hedge ratio computation moved from a static line 264 to the `compute_dynamic_hedge_ratio()` call in
`on_tick`. Line 264 in the current file is in `_build_legs` function body, not the hedge formula.

**Severity:** Medium — stale code pointer misleads engineers looking for the right line.

---

### Drift 3 — `carry-staked-basis.md`: missing `lst_native_rate` and `lst_native_rate_ts` features

**Codex features section (lines 31–39):** lists only:

- `staking_apy_bps`
- `funding_rate_apy_bps`
- `usdc_idle_yield_apy_bps`
- `health_factor`

**Actual code (`staked_basis.py:on_tick`):** also reads:

- `lst_native_rate` (float, default 1.0) — LST/native exchange rate for Phase 6B dynamic hedge
- `lst_native_rate_ts` (float, optional unix timestamp) — staleness guard; if present and >300s old, engine falls back
  to `lst_native_rate = 1.0` with `logger.warning`

**Severity:** High — undocumented feature keys; engineers won't know to publish them upstream.

---

### Drift 4 — `carry-staked-basis.md`: `peg_drift_threshold_bps` missing from config schema

**Codex config schema (lines 195–210):** lists `entry_bps`, `exit_bps`, `min_health_factor`, `hedge_deadline_ms` as
optional — but NOT `peg_drift_threshold_bps`.

**Actual code (`staked_basis.py:on_tick`):**

```python
peg_drift_threshold_bps = decimal_param(
    self.params, "peg_drift_threshold_bps", DEFAULT_PEG_DRIFT_THRESHOLD_BPS
)
```

The param is configurable (default 25 bps). Currently absent from the codex config schema.

**Severity:** Medium — operators can't override the hysteresis band without knowing the param exists.

---

### Drift 5 — `arbitrage-price-dispersion.md`: stale code module path

**Codex says (line 12):**

> **Code module (target):** `strategy-service/engine/strategies/arbitrage_price_dispersion_engine.py`

**Actual path:** `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`

Also `arbitrage_structural/price_dispersion_hierarchical.py` for the hierarchical variant. The `(target)` qualifier
suggests this was written prospectively and never updated after the v2 engine refactor.

**Severity:** Medium — engineers navigating from codex to code will look in the wrong directory.

---

## Why it matters

Codex/code drift on Phase 6B status (Drift 1) is the most critical: a developer reading the codex to understand the
hedge-ratio behavior would implement or debug against the wrong formula. The `lst_native_rate_ts` staleness feature
(Drift 3) is the only undocumented feature key that upstream (features-onchain) must publish for the staleness guard to
activate — without the codex update, the feature will never be published and the guard will never fire.

---

## Recommended decision

1. **Fix Drift 1 + 2 in `carry-staked-basis.md`**: update the hedge ratio section to say Phase 6B is SHIPPED
   (strategy-service@d6be15b), remove the "will introduce" language, update the formula description and remove the stale
   `staked_basis.py:264` pointer.

2. **Fix Drift 3 in `carry-staked-basis.md`**: add `lst_native_rate` + `lst_native_rate_ts` to the "Features expected"
   section with descriptions.

3. **Fix Drift 4 in `carry-staked-basis.md`**: add `peg_drift_threshold_bps: "25"` to the config schema YAML with a
   comment explaining it controls the rebalance hysteresis band.

4. **Fix Drift 5 in `arbitrage-price-dispersion.md`**: update the Code module path to
   `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`.

Operator decision needed on: who does the codex update (slot 1 owns PM repo codex; slot 3 can prepare a patch but must
not commit to PM codex bodies per slot-precedence rule).

---

---

## Audit update — 2026-05-15 session-4 (slot-3)

**Drifts 1–5 status**: ALL CONFIRMED FIXED by slot 6 in PM codex update (incoming merge to LDR 2026-05-15 afternoon).

- Drift 1: Phase 6B hedge ratio → SHIPPED language + DYNAMIC formula in carry-staked-basis.md:32-38. ✅
- Drift 2: stale `staked_basis.py:264` pointer → removed, replaced with `compute_dynamic_hedge_ratio()` ref. ✅
- Drift 3: `lst_native_rate` + `lst_native_rate_ts` → added to Features section at lines 221-224. ✅
- Drift 4: `peg_drift_threshold_bps` → added to config schema at line 210-212. ✅
- Drift 5: APD code module path → fixed to v2 path at line 14-16. ✅

**New drifts found (session-4 item 8 audit)**:

### Drift 6 — `carry-staked-basis.md`: boot-rejection timing changed

**Codex says (line 229):** `venue_accepts_collateral(perp_venue, lst_asset)` returns False → "slot is rejected at
preflight."

**Actual code (item 6 shipped at strategy-service@93965fd):** CarryStakedBasisEngine now raises `ValueError` at
`__init__` if any of the 6 required params (`staking_protocol`, `native_asset`, `lst_asset`, `perp_venue`,
`perp_instrument`, `spot_venue`) are absent. The rejection is at CONSTRUCTION, not at tick-time preflight. The codex
"rejected at preflight" language refers to the collateral-matrix check (which still runs at tick time via
`_derive_structure`), but the required-params check now fires earlier at boot. These are two different rejection points.

**Severity:** Low — the behavior change is additive (boot rejection is stricter than tick rejection). Operators will get
a clearer error message. Codex comment accuracy only.

**Recommended fix (Drift 6):** Add a sentence to the config schema section noting that the 6 required params are
validated at construction (ValueError at boot if absent), not silently skipped.

---

### Drift 7 — `arbitrage-price-dispersion.md`: Config schema shows generic sports schema, not engine params

**Codex says (lines 80-100):** Config schema uses `opportunity_type: CROSS_BOOK_SPORTS`, `eligible_venues`,
`eligible_markets`, `min_edge_bps` — generic schema for the theoretical full APD archetype.

**Actual code engine params (price-dispersion path):**

- `candidate_venues` (required, comma-separated, ≥ 2 venues) — NEW: raises ValueError at boot if absent or < 2
- `dispersion_bps` (default "30")
- `cost_bps` (default "10")
- `stake_fraction` (default "0.1")
- `hedge_deadline_ms` (default "5000")

**Actual code engine params (funding-rate-dispersion path):** `dispersion_type: "funding-rate-dispersion"`,
`venue_universe`, `pair_selection_mode`, `vol_cap_clamp_feature`, etc. (documented in examples at lines 163-173 as
comments).

**Severity:** Medium — engineer reading codex to implement APD upstream integration (features publisher) will expect the
wrong params schema. `candidate_venues` especially is now required at boot — an upstream operator creating a new slot
must know this.

**Recommended fix (Drift 7):** Replace the generic YAML config schema with two sections: (a) price-dispersion params
(CURRENT IMPLEMENTATION) and (b) funding-rate-dispersion params. Mark the old generic schema as "SUPERSEDED by actual
impl."

---

## Deferred work

- [x] **P1. FIXED** — Slot 6 applied fixes 1–4 to carry-staked-basis.md (confirmed in merge 2026-05-15).
- [x] **P2. FIXED** — Slot 6 applied fix 5 to arbitrage-price-dispersion.md (confirmed in merge 2026-05-15).
- [x] ✅ **P3. FIXED** — Add `lst_native_rate` + `lst_native_rate_ts` to features-onchain publisher so staleness guard
      activates in production. features-service@c29dd8cc: added both columns to `_annualise_and_stamp` + happy-path unit
      test verifying output schema. Provenance: slot-3 audit 2026-05-15. Fixed: slot-7 2026-05-19.
- [x] ✅ **P4. FIXED** — Updated `carry-staked-basis.md` config schema with Drift 6 boot-validation note: 6 required
      params validated at `__init__`; ValueError raised at boot if absent. PM codex update slot-7 2026-05-19.
- [x] ✅ **P5. FIXED** — Replaced APD generic config schema with actual impl params (Drift 7): added SUPERSEDED banner
      on legacy schema + Variant A (price-dispersion, CURRENT IMPLEMENTATION with `candidate_venues` required) + Variant
      B placeholder (funding-rate-dispersion). PM codex update slot-7 2026-05-19.

## RESOLVED — 2026-05-17 (slot 4 audit during cross-slot sweep)

Immediate drifts 1-5 ✅ shipped 2026-05-15 by slot 6 (per audit-update body line 133-141). Remaining P3-P5 items have
named owners (slot 1 codex docs + features-onchain publisher) and explicit successors. Primary audit deliverable
(codex/code parity for staked-basis + APD archetypes) closed. Issue archivable at next sweep.

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Resolved; drifts 1-5 fixed by slot-6; P3-P5
deferred to successor
