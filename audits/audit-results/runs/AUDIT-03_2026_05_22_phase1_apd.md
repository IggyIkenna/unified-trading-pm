---
title: "AUDIT-03 — Phase 1 READ results: §2.2 arbitrage_price_dispersion"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift (codex+plans ↔ code), READ checkpoints"
section: "§2.2 arbitrage_price_dispersion (APD-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - strategy-service@b303a358 — engine/strategies/v2/arbitrage_structural/{price_dispersion.py,
    funding_rate_dispersion.py}, target_universe/catalog.py, archetype_slot_resolver.py
oracle: codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md
---

# AUDIT-03 — Phase 1 READ — §2.2 arbitrage_price_dispersion

Sub-agent first pass, Opus-reviewed. **3 findings (F-13…F-15).** Core dispatch + entry/leg structure PASS.

## Per-checkpoint verdicts

| ID                 | Verdict           | Evidence                                                                                                                                                                                                                                                                                                                  |
| ------------------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| APD-01             | PASS              | `price_dispersion.py:98` `REQUIRED_PARAMS=frozenset({"candidate_venues"})`; `__init__` L108-116 raises `ValueError` if absent or `len(venues)<2`; guard scoped to `dispersion_type=="price-dispersion"` (Variant A) ✓                                                                                                     |
| APD-02             | PASS              | `price_dispersion.py:201-207` defaults `dispersion_bps=30, cost_bps=10, stake_fraction=0.1, hedge_deadline_ms=5000` ✓                                                                                                                                                                                                     |
| APD-03             | **DRIFT**         | codex says `pair_selection_mode=dynamic-best-long-short`; code slots set `pair_selection_mode="single-best"` + a separate `venue_selection_mode="dynamic-best-long-short"` (`archetype_slot_resolver.py:100-102`). `PairSelectionMode` enum has no `DYNAMIC_BEST_LONG_SHORT` (`funding_rate_dispersion.py:44-54`). → F-13 |
| APD-05             | PASS              | `price_dispersion.py:138-152` dispatch: funding→`_on_tick_funding_rate_dispersion`, else→`_on_tick_price_dispersion` ✓                                                                                                                                                                                                    |
| APD-06             | PASS              | price path emits `execution_mode=LEADER_HEDGE` (L230-248); funding path L595 same. LegController inline (KD-01 deferral, consistent)                                                                                                                                                                                      |
| APD-09             | **DRIFT**         | codex `max_underlying_move_pct=3.0` NOT read/enforced; vol-cap uses `vol_cap_clamp_threshold_pct` (default 80.0) + zscore (`price_dispersion.py:527-535`). Different mechanism than the absolute pct-move cutoff codex names. → F-14                                                                                      |
| APD-11             | PASS              | funding-rate-dispersion slots in `_CEFI` → `STRATEGY_TYPE_TO_SLOT` (`archetype_slot_resolver.py:1177-1182`), not catalog ✓                                                                                                                                                                                                |
| APD-12             | **DRIFT (minor)** | base `react_to_equity_change` sets equity + returns `[]` (`base.py:308-319`); APD does not override. Codex pseudocode references `max_capital_per_opp` recompute — no such field exists; per-opp sizing auto-scales via `target_equity*stake_fraction` inline → functionally OK, codex field phantom. → F-15              |
| APD-14             | PASS              | `catalog.py:1212-1340` `_build_arbitrage_price_dispersion` slots use `opportunity_type`-style keys, NOT the legacy generic `eligible_venues` schema; no Variant A/B key collision ✓                                                                                                                                       |
| APD-04/07/08/10/13 | PHASE2            | net-edge gate present (L200-203); `CLOSE_LEADER_IF_HEDGE_FAILS` + hedge_deadline present (L237-239); `if self.killed: return []` (L127). Opportunity-validation (liquidity/connectivity/prefund) NOT in engine — likely execution-service (verify Phase 2). Behaviour deferred.                                           |

## Findings

| ID   | Checkpoint | Class       | Finding                                                                                                                                                                                                                                                                                                       | Sev |
| ---- | ---------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| F-13 | APD-03     | CODEX-DRIFT | codex names `pair_selection_mode=dynamic-best-long-short` but no such `PairSelectionMode` enum value exists; code uses `pair_selection_mode=single-best` + separate `venue_selection_mode=dynamic-best-long-short`. Codex term stale OR config field renamed without doc update — clarify intended semantics. | P1  |
| F-14 | APD-09     | CODE-DRIFT  | `max_underlying_move_pct` (codex 3.0, universal StrategyInstanceDefinition field) not read/enforced in APD engine; only the `vol_cap_clamp_threshold_pct`(80)+zscore mechanism exists. (Cross-check carry CSB — likely same gap → XAS candidate: universal vol-cap field unenforced across archetypes.)       | P2  |
| F-15 | APD-12     | CODEX-DRIFT | codex `react_to_equity_change` pseudocode references `max_capital_per_opp`/`max_capital_per_opp_pct` — phantom fields not on the engine. Engine auto-scales per-opp via `target_equity*stake_fraction`; functionally correct but codex doc references non-existent fields.                                    | P2  |
