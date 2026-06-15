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
      **Left as tracked todo (engine-remediation pass 2026-06-15): OPERATOR-GATED BY DESIGN** — operator decision #3 for
      this plan requires "operator approves the diff before ship", and the two values are explicitly `operator-HELD`
      placeholders. The conservative-value pick + ship is a `BLOCKED-OPERATOR-DECISION` the operator themselves set; not
      an autonomous-resolvable item. The margin cluster already reads these via the F28 accessors, so a later value
      update flows through with no consumer change.
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
      **DIAGNOSIS (2026-06-15, engine-remediation pass — left as tracked todo, NOT done):** the probe itself WORKS —
      `from strategy_service.engine.strategies.v2.factory import ARCHETYPE_ENGINE_REGISTRY` via `strategy-service/.venv`
      returns the exact 29 keys currently in `_ENGINE_BACKED_ARCHETYPE_VALUES` (transcription verified accurate). The
      blocker to a clean swap: `build_matrix()` is exercised by the DETERMINISTIC PM unit test
      `tests/unit/test_capability_verdict_matrix.py` (6 call sites, runs in PM QG) and is deliberately self-contained —
      the transcription is a CITED + parity-guarded choice so the generator + its byte-stable test carry no runtime
      cross-service dependency (the manifest exporter probes at heavy on-demand build time, not in a deterministic unit
      test). Doing F48 right = give `build_matrix()` an injected `engine_backed_archetypes` param (default→probe in
      `main()`; the unit test passes a fixture set), so the live probe runs at generation time while the test stays
      hermetic. Mechanical but touches the test contract — deferred from this engine-pass per the dispatch's
      "follow-ups: do if time, else leave as the tracked todos". Reuse `_run_service_probe` from `_capability_gaps.py`.

## Phase B — strategy-service engine (freeze LIFTED) — CeFi margin traceability + netting + F27/F16

- [x] ✅ [SPEC] P0. **Margin cluster — make CeFi margin TRACEABLE end-to-end** (operator's original "can we trace where our
      margin sits?"). Three coupled fixes in strategy-service `position/`:
      (a) `core/margin_event_emitter.py` — drop the hardcoded `venue_type="defi"`; emit `MarginEvent` for CeFi perp
      venues (HL/Bybit/OKX/Binance) off live per-venue balances, classified by real venue_type.
      (b) `core/venue_balance_tracker.py` — add a CeFi per-venue balance tracker (currently sports/per-bookmaker only) so
      the emitter has live balances to feed.
      (c) `api/margin_health.py` — replace the Phase-1 stub (`return []`) with a real `MarginHealthSnapshot` per
      client/venue, reading the haircut-adjusted posted-collateral from the F28-canonical collateral SSOT
      (`collateral_usd`), resolving the F28 dual-SSOT risk on the consumer side too.
      Emit against the existing UAC surface (`transfer_purpose` + `COLLATERAL_POSTED`/`MARGIN_RELEASED`, already shipped).
      — DONE **UTL@1b215ea9 + strategy-service@b9b26433** (2026-06-15). (a) `emit_margin_event_for_cefi(*, client_id,
      strategy_id, venue, margin_model, portfolio, position_type="PERP")` computes via the UTL CeFi model, maps
      `severity_breach`→`MarginEventSeverity` (none→INFO skip / warning→WARNING / critical→CRITICAL /
      severe+liquidation→LIQUIDATION), emits a `venue_type="cefi"` snapshot — usage% lands in the schema's
      `margin_usage_pct` field (NOT `health_factor`, a DeFi-only concept), shared `_publish_margin_event` for both paths.
      (b) `CefiVenueBalanceReader` builds `PortfolioInputs` from the LIVE in-service `AccountQueryClient` (UPI-backed — no
      execution-service import; service-dep ban holds): open positions → collateral_positions (mark = entry +
      upnl/qty), used margin → USD debt leg; + `CEFI_PERP_VENUES` / `cefi_margin_model_for_venue`. (c) `margin_health`
      returns real per-venue `MarginHealthSnapshot[]` (model usage% + F28 `get_collateral_haircut` haircut-adjusted
      wallet collateral_usd), summary aggregates avg_margin_usage_pct/max_ltv; GCS time-series is the documented Phase-2
      next step. UTL prereq: `get_margin_model`/`PortfolioInputs`/`compute_health` re-exported at UTL top level (import
      gate wants top-level UTL imports). Tests: 31 (severity map, cefi snapshot, publish-swallow, reader live path,
      margin_health real return, no-position skip). QG green both repos (UTL 120s, strategy-service 135s).
- [x] ✅ [SPEC] P1. **F45 — exposure-normalization / net-delta pipeline, single-canonical.** Consolidate the
      scattered primitives (UAC `risk.py`, UTL `risk/`, execution-service leg controllers / `perp_hedge_sizer`) into ONE
      canonical netting entry that nets LST→underlying delta + multi-leg inter-leg delta into a
      single position-level exposure. **DELETE the scattered duplicate netting logic** once consumers point at the
      canonical one (single-SSOT rule). Target: strategy-service (+ UTL/UAC for the shared contract types only).
      — DONE **UTL@b819cd1c + execution-service@b7c63335 + strategy-service@bdac6595** (2026-06-15).
      **Canonical home = UTL `unified_trading_library/risk/net_delta.py`** (top-level re-exported), NOT strategy-service —
      **operator-absent architectural decision, documented per autonomous rule 1**: the literal "pipeline in
      strategy-service that every consumer points at" is unbuildable because the workspace **no-service↔service-import**
      HARD RULE forbids execution-service (`perp_hedge_sizer`/`leveraged_leg_controller`) importing a strategy-service
      module. UTL is the only shared T0 lib BOTH services already depend on, so the single SSOT lives there; strategy-service
      still OWNS the position/risk orchestration that calls it. Five pure-Decimal primitives (behavior-identical
      extractions, no math changed): `net_underlying_delta` (collateral·er − debt, LST→underlying), `residual_hedge_size`
      (max(0, e − target), the perp-hedge sizing), `net_signed_delta` / `net_signed_exposure` / `gross_exposure` (signed
      rollups). Consumers repointed + inline DELETED: execution-service `PerpHedgeSizer.read_e_from_aave_data` +
      `compute_rebalance` + `leveraged_leg_controller.verify_net_delta`; strategy-service `risk_group_aggregator` +
      `exposure_aggregator`. **Diagnosis (read-both-sides, distinct-concern → left alone, NOT dupes):** `margin_sim._netting_factor`
      = margin-requirement netting (not position delta); `output_builders._aggregate_exposure_totals` = **float**-domain
      output-schema rollup (routing through the Decimal primitives would alter live `risk_metrics` parquet precision —
      deliberately kept local); options-greeks delta aggregation; pre-trade limit checks. Tests: UTL 16 net_delta +
      exec-svc 16 perp_hedge_sizer + 25 leveraged_leg_controller + strategy 18 risk/exposure aggregator (all green,
      behavior preserved). QG green all 3 repos.
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
- 2026-06-15 — **Phase B margin cluster (P0) SHIPPED end-to-end.** UTL@1b215ea9 (top-level re-export of
  `get_margin_model`/`PortfolioInputs`/`compute_health` — the import-gate prereq; UTL shipped first per dep order) →
  strategy-service@b9b26433. CeFi perp margin is now traceable: a per-venue compute via the existing UTL CeFi models
  (`_CefiMarginModelBase`, margin-usage %) off the LIVE in-service `AccountQueryClient` (UPI, NOT an execution-service
  import) produces a `MarginEvent` with `venue_type="cefi"` + a `MarginHealthSnapshot` whose usage lands in
  `margin_usage_pct` (corrected from the draft's `health_factor`, a DeFi-only field) and whose `collateral_usd` is F28
  haircut-adjusted. `margin_health` API is no longer a `return []` stub — real per-client×venue snapshots live; GCS
  historical time-series is the only documented Phase-2 remainder. 31 tests, QG green both repos. **Decisions
  (autonomous, documented):** (1) CeFi usage → `margin_usage_pct` not `health_factor` (schema SSOT distinguishes them;
  the draft's `health_factor=usage` would mislead consumers); (2) `PortfolioInputs` fed in the canonical test-fixture
  shape (positions = collateral_positions notional book carrying MMR; used-margin = USD debt leg) — model is owned/complete,
  this is wiring; (3) venues with no open positions are skipped (the model's `equity<=0` branch would falsely grade an
  empty book 100%). Next: F45 netting consolidation (P1) — pre-audit confirms net-delta logic is genuinely multi-site
  (`risk_group_aggregator`, `aggregated` route, `output_builders` delta_btc/eth, `math_utilities` LST→underlying,
  `risk/engine/orchestrator`), distinct from margin-requirement netting (`margin_sim._netting_factor` — left alone).
- 2026-06-15 — **F45 net-delta/exposure consolidation (P1) SHIPPED single-canonical across 3 repos.** UTL@b819cd1c
  (canonical `risk/net_delta.py` — 5 pure-Decimal primitives) → execution-service@b7c63335 (`perp_hedge_sizer` +
  `leveraged_leg_controller` repointed, inline deleted) → strategy-service@bdac6595 (`risk_group_aggregator` +
  `exposure_aggregator` repointed, inline deleted). **Key decision (documented in the todo above):** canonical home is
  UTL, NOT strategy-service — the service-dep ban makes a strategy-service "pipeline every consumer points at"
  unbuildable for execution-service, and UTL is the only shared lib both import; strategy-service still owns the risk/
  position orchestration. All extractions are behavior-identical (verified by each consumer's pre-existing tests: 16+25
  exec-svc + 18 strategy + 16 new UTL). **Diagnosed-distinct, deliberately NOT merged (would be wrong / a behavior
  change):** `margin_sim._netting_factor` (margin-requirement, not delta), `output_builders._aggregate_exposure_totals`
  (float domain — Decimal routing would shift live parquet precision), options-greeks delta, pre-trade limit checks.
  This honors "diagnose before fixing / read both sides" — the F45 "scatter" was partly distinct concerns, not all
  duplication; only the genuine net-delta/LST/exposure dupes were consolidated + deleted. Remaining plan items: F28
  live-API probe (operator-held haircuts), F48 venv-probe follow-up — both smaller, attempting next.
- 2026-06-15 — **Engine-remediation pass CLOSED.** Phase B fully shipped (margin cluster P0, F45 P1, F27, F16 all
  `[x]`). Both follow-ups assessed + left as tracked todos with diagnosis (NOT silent defers): **F28** is OPERATOR-GATED
  by design (operator decision #3 = operator approves the haircut diff before ship; values are `operator-HELD`); **F48**
  probe VERIFIED working (returns the exact 29 engine keys) but a clean swap requires reworking `build_matrix()`'s
  signature + its deterministic, hermetic PM unit test (`test_capability_verdict_matrix.py`, 6 call sites) — the
  transcription is a CITED + parity-guarded self-containment choice, not careless dup; the right fix (inject
  `engine_backed_archetypes` param, default→probe, test passes a fixture) is annotated on the todo. **Codex SSOTs
  updated** (Post-Plan-Phase audit): `04-architecture/client-funds-isolation.md` (CeFi margin-traceability section) +
  `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` (net-delta/exposure-netting SSOT section). SHAs:
  margin = UTL@1b215ea9 + strategy-service@b9b26433; F45 = UTL@b819cd1c + execution-service@b7c63335 +
  strategy-service@bdac6595. Phase C (build missing v2 engines) remains separately-scoped (bigger than this pass).
