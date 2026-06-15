---
title: Engine findings remediation — collateral / margin / netting / catalogue over-claims
created: 2026-06-15
parent_epic: strategy_master
assigned_vm: vm-trading-core
estimate_class: brand-new
estimate_baseline_ai_days: 9.0
estimate_calibrated_ai_days: 9.0
locked_by: live-defi-rollout
locked_since: 2026-06-15
source:
  - plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md
  - plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md
priority: P2
status: active
---

# Engine findings remediation (2026-06-15)

Wrapper plan dispatching the OPEN engine findings the capability-wizard initiative surfaced (F1–F53 + margin audit).
Operator decisions (2026-06-15):

1. **strategy-service LOGIC FREEZE — LIFTED** for the CeFi-margin engine work (+ F27 / F16). Real engine code authorised.
2. **F45 exposure-netting OWNER = strategy-service** (position/risk lives there; now unfrozen).
3. **F28 collateral haircuts — research official venue haircuts, reconcile to the CONSERVATIVE value, operator approves
   the diff before ship.**
4. **HARD RULE for this whole plan (operator 2026-06-15): every dual-source finding converges to ONE canonical SSOT and
   the duplicate is DELETED** — no parallel old+new paths, no reconciled-but-both-kept. (Composes with the workspace
   "Delete deprecated code / no dual SSOTs" rule.)

Ownership map (verified 2026-06-15): F28 = UAC `registry/venue_collateral.py` + execution-service
`services/lst_collateral_resolver.py` (NOT strategy-service) · margin cluster + F45 + F27 + F16 = strategy-service ·
F47/F48 surface = PM `scripts/openapi/generate_capability_verdict_matrix.py`, engine = strategy-service.

---

## Phase A — non-frozen quick wins (PARALLEL; no engine freeze involved)

- [x] ✅ [SPEC] P1. **F28 — single canonical collateral-haircut SSOT + delete the duplicate.** — DONE **UAC@f302c72 +
      execution-service@8a3c6ab** (2026-06-15, operator-approved values). UAC `venue_collateral.py` = CANONICAL; its 7
      clear-cut values were already correct (HL wstETH / OKX stETH / Binance stETH NOT-ACCEPTED; Deribit stETH 0.075;
      Deribit wstETH NOT-ACCEPTED; Bybit/OKX wstETH 0.10). execution-service `_LST_REGISTRY` (106-line duplicate) +
      local lookup **DELETED** → `get_lst_acceptance()` now reads UAC `venue_accepts_collateral`/`get_collateral_haircut`
      with an explicit fraction→percent boundary conversion (the 100× units-bug guard). Orphaned `margin_mode` field
      removed. Bybit-stETH + Drift-mSOL flagged `# PLACEHOLDER` (operator-held). Kamino kept out (lending). QG green both
      repos (UAC 2 tests, exec-svc 22 tests).
- [ ] [DEFI] P2. **F28 live-API probe** to finalize the two operator-HELD collateral haircuts in UAC
      `registry/venue_collateral.py` — Bybit stETH (0.10 placeholder) + Drift mSOL (0.10 placeholder); replace the
      `# PLACEHOLDER — pending live-API probe (F28, operator-held 2026-06-15)` comments with probed values + source
      citation. Provenance: F28 consolidation (UAC@f302c72 / execution-service@8a3c6ab). Target: unified-api-contracts.
- [x] ✅ [SCRIPT] P2. **F47/F48 — surface-correct the verdict-matrix over-claims.** — DONE **PM@d0f66d732 (PR #339) +
      UAC@a1f8b38** (2026-06-15). F47: leg-eligible venues whose folded slot-token ∉ `KNOWN_VENUE_TOKENS` → `blocked`
      with `unbuildable_slot_venue` (186 cells / 11 venues, DERIVED not enumerated). F48: archetypes whose value ∉ the
      v2 engine-backed set → `not_registered(no_v2_engine)` (22 VOL_*/MARKET_MAKING_*, retained the 3 engined ones).
      AVAILABLE 16913→12977 (−3936); total 24752→21600; deterministic. UI re-bundle dispatched (uts-ui + dep-ui →
      21600/12977). Engine builds = Phase C.
- [ ] [SCRIPT] P3. **F48 follow-up — replace the engine-registry TRANSCRIPTION with a venv probe (single-canonical).**
      The F47/F48 fix transcribed strategy-service's `ARCHETYPE_ENGINE_REGISTRY` keys (engine/strategies/v2/factory.py)
      into PM `generate_capability_verdict_matrix.py` as `_ENGINE_BACKED_ARCHETYPE_VALUES` (cited, because UAC/PM cannot
      import strategy-service — service-dep ban). That's a duplicate SSOT. Make the generator PROBE strategy-service via
      the per-service `.venv` subprocess (the same pattern the capability-MANIFEST exporter uses for exec-algos/
      feature-groups/ml-models) so the engine-backed set is read live, not copied. Target: unified-trading-pm.

## Phase B — strategy-service engine (freeze LIFTED) — CeFi margin traceability + netting + F27/F16

- [ ] [SPEC] P0. **Margin cluster — make CeFi margin TRACEABLE end-to-end** (operator's original "can we trace where our
      margin sits?"). Three coupled fixes in strategy-service `position/`:
      (a) `core/margin_event_emitter.py` — drop the hardcoded `venue_type="defi"`; emit `MarginEvent` for CeFi perp
      venues (HL/Bybit/OKX/Binance) off live per-venue balances, classified by real venue_type.
      (b) `core/venue_balance_tracker.py` — add a CeFi per-venue balance tracker (currently sports/per-bookmaker only) so
      the emitter has live balances to feed.
      (c) `api/margin_health.py` — replace the Phase-1 stub (`return []`) with a real `MarginHealthSnapshot` per
      client/venue, reading the haircut-adjusted posted-collateral from the F28-canonical collateral SSOT
      (`collateral_usd`), resolving the F28 dual-SSOT risk on the consumer side too.
      Emit against the existing UAC surface (`transfer_purpose` + `COLLATERAL_POSTED`/`MARGIN_RELEASED`, already shipped).
- [ ] [SPEC] P1. **F45 — exposure-normalization / net-delta pipeline, OWNED by strategy-service.** Consolidate the
      scattered primitives (UAC `risk.py`, UTL `risk/`, execution-service leg controllers / `perp_hedge_sizer`) into ONE
      canonical netting pipeline in strategy-service that nets LST→underlying delta + multi-leg inter-leg delta into a
      single position-level exposure. **DELETE the scattered duplicate netting logic** once consumers point at the
      canonical one (single-SSOT rule). Target: strategy-service (+ UTL/UAC for the shared contract types only).
- [x] ✅ [LOGIC] P1. **F27 — carry-staked-basis venue-id CASE MISMATCH** (`deribit` vs `DERIBIT`) that no-emits. Normalise
      venue-id casing at the engine boundary (one canonical case; cite the SSOT). Target: strategy-service. — DONE
      **UAC@c0b2d0e** (2026-06-15): fixed at the SOURCE — `venue_collateral.py` accessors (`accepted_perp_collateral`/
      `venue_accepts_collateral`/`get_collateral_haircut`/`get_accepted_collateral`) now normalise both sides to
      `.upper()`, so lowercase slot-config venue ids resolve against the UPPERCASE matrix. `accepted_perp_collateral('deribit')`
      now returns `['BTC','ETH','USDC','stETH']` (was `[]`). Protects ALL callers, not just staked_basis. +regression test.
- [x] ✅ [BUG] P2. **F16 — latent `log_event(service_name=)` TypeError on the GCS-config path.** Fix the call signature.
      Target: strategy-service. — DONE **strategy-service@bce2f46d** (2026-06-15): moved the invalid
      `service_name=`/`operation=`/`error_code=` kwargs into `details={}` (log_event takes only event_name/severity/
      details/client_id/correlation_id); the GCS-config search error path no longer raises TypeError.

## Phase C — engine builds for the catalogue over-claims (follow-on; larger)

- [ ] [LOGIC] P2. **F47/F48 engine — build the missing v2 engines** for the venues/archetypes the matrix had been
      over-claiming (the v2 slot-label venue tokens + the 22 VOL_*/MARKET_MAKING_* archetypes), OR ratify (with operator)
      that they stay honestly `not_available`. Target: strategy-service. **Scoped separately — bigger than Phase B.**

## Codex SSOT updates

- `codex/04-architecture/client-funds-isolation.md` / margin-traceability section (margin cluster end-to-end).
- `codex/09-strategy/operational/pnl-attribution.md` (net-delta / exposure-normalization owner).
- Collateral haircut SSOT note (which of venue_collateral.py / lst_collateral_resolver.py is canonical post-F28).

## Success criteria

- CeFi margin is traceable: a USDC margin transfer to HL produces a `MarginEvent` with the right `venue_type` +
  `transfer_purpose`, and `margin_health` returns a real snapshot with haircut-adjusted `collateral_usd`.
- Exactly ONE collateral-haircut SSOT remains (the other deleted); ONE netting pipeline (scattered ones deleted).
- Verdict-matrix no longer claims `available` for unbuildable venues/archetypes.
- QG green per repo; F27 carry-staked-basis emits; F16 path no longer raises.

## Progress Log (append-only)

- 2026-06-15 — Plan authored from the operator's remediation go-ahead (freeze lifted / netting→strategy-service / F28
  conservative-research-with-approval / single-canonical-delete-duplicate). Phase A dispatched (F28 research + F47/F48
  surface, parallel); Phase B (strategy-service margin core) pre-audit started.
