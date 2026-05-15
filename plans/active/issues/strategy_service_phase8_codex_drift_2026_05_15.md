---
title: "Phase 8 Codex Audit — strategy-service archetype codex drift (2026-05-15)"
created: 2026-05-15
author: slot-3
source:
  - "codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md"
  - "codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md"
  - "strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py"
  - "strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py"
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

## Deferred work

- [ ] **P1. DEFERRED** — Slot 1 (PM owner) to apply fixes 1–4 above to carry-staked-basis.md. Provenance: slot-3 audit
      2026-05-15.
- [ ] **P2. DEFERRED** — Slot 1 (PM owner) to apply fix 5 to arbitrage-price-dispersion.md. Provenance: slot-3 audit
      2026-05-15.
- [ ] **P3. DEFERRED** — Add `lst_native_rate_ts` to features-onchain publisher so the staleness guard actually
      activates in production. Provenance: slot-3 audit 2026-05-15.
