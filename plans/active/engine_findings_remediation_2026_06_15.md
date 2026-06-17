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

1. **strategy-service LOGIC FREEZE — LIFTED** for the CeFi-margin engine work (+ F27 / F16). Real engine code
   authorised.
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
      local lookup **DELETED** → `get_lst_acceptance()` now reads UAC
      `venue_accepts_collateral`/`get_collateral_haircut` with an explicit fraction→percent boundary conversion (the
      100× units-bug guard). Orphaned `margin_mode` field removed. Bybit-stETH + Drift-mSOL flagged `# PLACEHOLDER`
      (operator-held). Kamino kept out (lending). QG green both repos (UAC 2 tests, exec-svc 22 tests).
- [ ] [DEFI] P2. **F28 live-API probe** to finalize the two operator-HELD collateral haircuts in UAC
      `registry/venue_collateral.py` — Bybit stETH (0.10 placeholder) + Drift mSOL (0.10 placeholder); replace the
      `# PLACEHOLDER — pending live-API probe (F28, operator-held 2026-06-15)` comments with probed values + source
      citation. Provenance: F28 consolidation (UAC@f302c72 / execution-service@8a3c6ab). Target: unified-api-contracts.
      **Left as tracked todo (engine-remediation pass 2026-06-15): OPERATOR-GATED BY DESIGN** — operator decision #3 for
      this plan requires "operator approves the diff before ship", and the two values are explicitly `operator-HELD`
      placeholders. The conservative-value pick + ship is a `BLOCKED-OPERATOR-DECISION` the operator themselves set; not
      an autonomous-resolvable item. The margin cluster already reads these via the F28 accessors, so a later value
      update flows through with no consumer change.
      **GO-LIVE MARKERS NOW LOUD — UAC@5fccaa7 (2026-06-17, operator-requested):** the two placeholders are flagged
      unmissably in code so they can't ship to live un-updated: (1) a `⚠️ PRE-GO-LIVE TODO` banner at the top of
      `registry/venue_collateral.py`; (2) `⚠️ PLACEHOLDER HAIRCUT — UPDATE … BEFORE GO-LIVE` inline comments + a
      `PLACEHOLDER 0.10 — update before go-live` string in each entry's `notes` field; (3) a machine-checkable
      `PLACEHOLDER_HAIRCUTS_PENDING_GO_LIVE = {("BYBIT","stETH"), ("DRIFT","mSOL")}` constant (exported from
      `unified_api_contracts.registry`) so a go-live preflight can ASSERT the set was emptied/re-probed. Conservative
      0.10 under-counts collateral (fails safe to RUN; not accurate for sizing). **This item stays OPEN** — it closes
      only when the operator approves the real probed haircut diff (decision #3).
- [x] ✅ [SCRIPT] P2. **F47/F48 — surface-correct the verdict-matrix over-claims.** — DONE **PM@d0f66d732 (PR #339) +
      UAC@a1f8b38** (2026-06-15). F47: leg-eligible venues whose folded slot-token ∉ `KNOWN_VENUE_TOKENS` → `blocked`
      with `unbuildable_slot_venue` (186 cells / 11 venues, DERIVED not enumerated). F48: archetypes whose value ∉ the
      v2 engine-backed set → `not_registered(no_v2_engine)` (22 VOL*\*/MARKET_MAKING*\*, retained the 3 engined ones).
      AVAILABLE 16913→12977 (−3936); total 24752→21600; deterministic. UI re-bundle dispatched (uts-ui + dep-ui →
      21600/12977). Engine builds = Phase C.
- [x] ✅ [SCRIPT] P3. **F48 follow-up — replace the engine-registry TRANSCRIPTION with a venv probe (single-canonical).** — DONE **PM@362f90404** (2026-06-17). `_ENGINE_BACKED_ARCHETYPE_VALUES` transcription DELETED from the generator; `_probe_engine_backed_archetypes(workspace_root)` reads `ARCHETYPE_ENGINE_REGISTRY` LIVE via strategy-service's `.venv` subprocess (reusing `_capability_gaps._run_service_probe`, the manifest-exporter idiom), fail-loud on probe failure. `build_matrix(engine_backed_archetypes)` now takes the set as an INJECTED param so `main()` supplies the live-probed set while the deterministic unit test stays hermetic (passes `_FIXTURE_ENGINE_BACKED`); a new `test_fixture_matches_live_engine_registry` guards the fixture against drift (skips when `.venv` absent, runs in the workspace). 8 tests green; ruff + basedpyright clean; PM QG green (required a back-merge of main→LDR for the routine 1.2.146→1.2.147 PM version-alignment churn). Target: unified-trading-pm.
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

- [x] ✅ [SPEC] P0. **Margin cluster — make CeFi margin TRACEABLE end-to-end** (operator's original "can we trace where
      our margin sits?"). Three coupled fixes in strategy-service `position/`: (a) `core/margin_event_emitter.py` — drop
      the hardcoded `venue_type="defi"`; emit `MarginEvent` for CeFi perp venues (HL/Bybit/OKX/Binance) off live
      per-venue balances, classified by real venue_type. (b) `core/venue_balance_tracker.py` — add a CeFi per-venue
      balance tracker (currently sports/per-bookmaker only) so the emitter has live balances to feed. (c)
      `api/margin_health.py` — replace the Phase-1 stub (`return []`) with a real `MarginHealthSnapshot` per
      client/venue, reading the haircut-adjusted posted-collateral from the F28-canonical collateral SSOT
      (`collateral_usd`), resolving the F28 dual-SSOT risk on the consumer side too. Emit against the existing UAC
      surface (`transfer_purpose` + `COLLATERAL_POSTED`/`MARGIN_RELEASED`, already shipped). — DONE **UTL@1b215ea9 +
      strategy-service@b9b26433** (2026-06-15). (a)
      `emit_margin_event_for_cefi(*, client_id,     strategy_id, venue, margin_model, portfolio, position_type="PERP")`
      computes via the UTL CeFi model, maps `severity_breach`→`MarginEventSeverity` (none→INFO skip / warning→WARNING /
      critical→CRITICAL / severe+liquidation→LIQUIDATION), emits a `venue_type="cefi"` snapshot — usage% lands in the
      schema's `margin_usage_pct` field (NOT `health_factor`, a DeFi-only concept), shared `_publish_margin_event` for
      both paths. (b) `CefiVenueBalanceReader` builds `PortfolioInputs` from the LIVE in-service `AccountQueryClient`
      (UPI-backed — no execution-service import; service-dep ban holds): open positions → collateral_positions (mark =
      entry + upnl/qty), used margin → USD debt leg; + `CEFI_PERP_VENUES` / `cefi_margin_model_for_venue`. (c)
      `margin_health` returns real per-venue `MarginHealthSnapshot[]` (model usage% + F28 `get_collateral_haircut`
      haircut-adjusted wallet collateral_usd), summary aggregates avg_margin_usage_pct/max_ltv; GCS time-series is the
      documented Phase-2 next step. UTL prereq: `get_margin_model`/`PortfolioInputs`/`compute_health` re-exported at UTL
      top level (import gate wants top-level UTL imports). Tests: 31 (severity map, cefi snapshot, publish-swallow,
      reader live path, margin_health real return, no-position skip). QG green both repos (UTL 120s, strategy-service
      135s).
- [x] ✅ [SPEC] P1. **F45 — exposure-normalization / net-delta pipeline, single-canonical.** Consolidate the scattered
      primitives (UAC `risk.py`, UTL `risk/`, execution-service leg controllers / `perp_hedge_sizer`) into ONE canonical
      netting entry that nets LST→underlying delta + multi-leg inter-leg delta into a single position-level exposure.
      **DELETE the scattered duplicate netting logic** once consumers point at the canonical one (single-SSOT rule).
      Target: strategy-service (+ UTL/UAC for the shared contract types only). — DONE **UTL@b819cd1c +
      execution-service@b7c63335 + strategy-service@bdac6595** (2026-06-15). **Canonical home = UTL
      `unified_trading_library/risk/net_delta.py`** (top-level re-exported), NOT strategy-service — **operator-absent
      architectural decision, documented per autonomous rule 1**: the literal "pipeline in strategy-service that every
      consumer points at" is unbuildable because the workspace **no-service↔service-import** HARD RULE forbids
      execution-service (`perp_hedge_sizer`/`leveraged_leg_controller`) importing a strategy-service module. UTL is the
      only shared T0 lib BOTH services already depend on, so the single SSOT lives there; strategy-service still OWNS
      the position/risk orchestration that calls it. Five pure-Decimal primitives (behavior-identical extractions, no
      math changed): `net_underlying_delta` (collateral·er − debt, LST→underlying), `residual_hedge_size` (max(0, e −
      target), the perp-hedge sizing), `net_signed_delta` / `net_signed_exposure` / `gross_exposure` (signed rollups).
      Consumers repointed + inline DELETED: execution-service `PerpHedgeSizer.read_e_from_aave_data` +
      `compute_rebalance` + `leveraged_leg_controller.verify_net_delta`; strategy-service `risk_group_aggregator` +
      `exposure_aggregator`. **Diagnosis (read-both-sides, distinct-concern → left alone, NOT dupes):**
      `margin_sim._netting_factor` = margin-requirement netting (not position delta);
      `output_builders._aggregate_exposure_totals` = **float**-domain output-schema rollup (routing through the Decimal
      primitives would alter live `risk_metrics` parquet precision — deliberately kept local); options-greeks delta
      aggregation; pre-trade limit checks. Tests: UTL 16 net_delta + exec-svc 16 perp_hedge_sizer + 25
      leveraged_leg_controller + strategy 18 risk/exposure aggregator (all green, behavior preserved). QG green all 3
      repos.
- [x] ✅ [LOGIC] P1. **F27 — carry-staked-basis venue-id CASE MISMATCH** (`deribit` vs `DERIBIT`) that no-emits.
      Normalise venue-id casing at the engine boundary (one canonical case; cite the SSOT). Target: strategy-service. —
      DONE **UAC@c0b2d0e** (2026-06-15): fixed at the SOURCE — `venue_collateral.py` accessors
      (`accepted_perp_collateral`/ `venue_accepts_collateral`/`get_collateral_haircut`/`get_accepted_collateral`) now
      normalise both sides to `.upper()`, so lowercase slot-config venue ids resolve against the UPPERCASE matrix.
      `accepted_perp_collateral('deribit')` now returns `['BTC','ETH','USDC','stETH']` (was `[]`). Protects ALL callers,
      not just staked_basis. +regression test.
- [x] ✅ [BUG] P2. **F16 — latent `log_event(service_name=)` TypeError on the GCS-config path.** Fix the call signature.
      Target: strategy-service. — DONE **strategy-service@bce2f46d** (2026-06-15): moved the invalid
      `service_name=`/`operation=`/`error_code=` kwargs into `details={}` (log_event takes only event_name/severity/
      details/client_id/correlation_id); the GCS-config search error path no longer raises TypeError.

## Phase C — engine builds OR ratify for the catalogue over-claims (build-or-ratify, per-archetype + per-venue)

> **Phase C is catalogue-honesty + selective post-MVP build-out, NOT a May-23 critical-path item.** The two LIVE DeFi
> MVP archetypes (`carry_staked_basis` + `arbitrage_price_dispersion`) are ALREADY engine-backed and use only supported
> venues — Phase B's F47/F48 SURFACE fix (PM@d0f66d732 + UAC@a1f8b38) already made the verdict matrix HONEST: it reports
> `not_registered(no_v2_engine)` / `not_registered(missing_registry)` for engineless archetypes and
> `blocked(unbuildable_slot_venue)` for venues whose folded slot-token ∉ the canonical `architecture_v2.venue_tokens`
> (`KNOWN_VENUE_TOKENS`) registry. **That honesty is CORRECT, not a bug.** Phase C is the per-archetype / per-venue
> decision: BUILD the engine (real design+implement+backtest) / ADD the venue token (only for a genuinely
> end-to-end-supported venue), **or RATIFY it stays honestly `not_available`.**

### Operator decision (recorded 2026-06-15 — autonomous dispatch, decision blanks left empty)

The dispatch's three operator-decision sets (BUILD-SUBSET / VENUE-TOKEN-ADD / RATIFY-ack) were **left empty** by the
operator. The dispatch's own decision rule governs the empty case verbatim: _"If the operator leaves the BUILD-SUBSET
empty: Phase C = RATIFY-ONLY … Do NOT build engines the operator did not name (building 28 unwanted strategies is the
wrong outcome)."_ The recommended default was explicitly **EMPTY** ("none are on the live path; the honest matrix
already reflects reality"). Per AUTONOMOUS_AGENT_RULES rule 2 (decide from the documented record of intent, don't ask):

- **BUILD-SUBSET = { } (empty)** — no v2 engine is built in this pass. None of the 28 engineless archetypes is on the
  live DeFi path; each is a genuine options-vol / MM-microstructure / portfolio-optimisation design+implement+backtest
  effort, and a registered-but-empty engine is WORSE than honest `not_available` (it re-creates the over-claim).
- **VENUE-TOKEN-ADD = { } (empty)** — no venue token added. None of the 11 blocked venues is wired end-to-end (adapter +
  collateral + capability); adding a token for an unsupported venue re-introduces the exact F47 over-claim Phase B
  fixed.
- **RATIFY-the-rest = ALL 28 engineless archetypes + ALL 11 unbuildable venues** stay honestly `not_available`. This is
  the intended DONE state, not a gap. NO code change → the matrix is unchanged-and-honest.

### Ground truth (re-verified 2026-06-15 via the live registries — registries drift, do not trust a paste)

- **57** `StrategyArchetype` enum values; **29 engine-backed** (`ARCHETYPE_ENGINE_REGISTRY`, probed live via
  `strategy-service/.venv`); **28 MISSING** an engine. (The Phase-A "22" was the `no_v2_engine` _subset_, not the total:
  28 = **22** archetypes with leg structure but no engine [`no_v2_engine`] + **6** with no leg structure at all
  [`missing_registry`].)
- **11** venues / **186** cells `blocked(unbuildable_slot_venue)`: folded slot-token ∉ `KNOWN_VENUE_TOKENS` (74 tokens).
- Verdict-matrix counts (committed `unified-api-contracts/openapi/capability-verdict-matrix.json`, deterministic):
  **total 21600 / available 12977 / blocked 8175 / not_registered 448** (= 96 `missing_registry` [6 archetypes] + 352
  `no_v2_engine` [22 archetypes]). Identical to the Phase-B post-fix counts → RATIFY introduces a **zero delta**.

- [x] ✅ [LOGIC] P2. **F47/F48 engine — RATIFIED honestly `not_available` (build-subset + venue-add both empty).** —
      DONE **PM (this plan + codex) 2026-06-15**. Operator left BUILD-SUBSET / VENUE-TOKEN-ADD empty → per the
      dispatch's empty-case rule, RATIFY-ONLY: all 28 engineless archetypes + 11 unbuildable venues stay honestly
      `not_available`, NO engine built, NO venue token added (either would re-introduce the over-claim). Matrix
      re-verified unchanged (21600/12977/8175/448); deterministic unit test
      `tests/unit/test_capability_verdict_matrix.py` green (7 tests); codex `archetype-paper-readiness.md` reconciled
      (29 registered / 28 not) + ratification section added. Target: strategy-service (no change) / PM (doc) / codex.

#### Ratified `not_available` — archetypes (28, post-MVP, no engine planned)

`not_registered(no_v2_engine)` — has leg structure (`ARCHETYPE_LEG_STRUCTURES`) but no registered v2 engine (22):

| Family               | Archetypes (ratified `not_available`)                                                                                                                                                                                                                                                                                                                                    | Reason (post-MVP, no engine planned)                                                                                                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| VOL\_\* (17)         | `VOL_STRADDLE` `VOL_DISPERSION` `VOL_VARIANCE_SWAP` `VOL_TERM_STRUCTURE_ARB` `VOL_TERM_STRUCTURE_SLOPE` `VOL_RATIO_SPREAD` `VOL_SPREAD_STRUCTURES` `VOL_SYNTHETIC_DELTA` `VOL_CARRY` `VOL_CROSS_ASSET_SPREAD` `VOL_LEAPS_CONVEXITY` `VOL_OVERLAY_COVERED_CALLS` `VOL_OVERLAY_PROTECTIVE_PUT` `VOL_0DTE_GAMMA_SCALPING` `VOL_ARB_RV_IV` `VOL_MARKET_MAKING` `VOL_ML_LEAN` | Options-vol pricing book (Phase-9 catalogue expansion). Not on the live DeFi path; no options book trading at MVP. `VOL_TRADING_OPTIONS` (the legacy umbrella engine) IS backed and covers the family for back-compat. |
| MARKET*MAKING*\* (5) | `MARKET_MAKING_INVENTORY_SKEW` `MARKET_MAKING_ML_LEAN` `MARKET_MAKING_PASSIVE_SPREAD` `MARKET_MAKING_PREDICTION` `MARKET_MAKING_QUEUE_MICROSTRUCTURE`                                                                                                                                                                                                                    | MM micro-variants. `MARKET_MAKING_CONTINUOUS` + `MARKET_MAKING_EVENT_SETTLED` ARE backed; the granular variants are post-MVP.                                                                                          |

`not_registered(missing_registry)` — no leg structure at all (`ARCHETYPE_LEG_STRUCTURES.not_registered`) (6):

| Family            | Archetypes (ratified `not_available`)                                                                         | Reason (post-MVP, no engine planned)                                                                                                                                                                                |
| ----------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PORTFOLIO\_\* (4) | `PORTFOLIO_FACTOR_ALLOCATION` `PORTFOLIO_MULTI_STRATEGY` `PORTFOLIO_RISK_PARITY` `PORTFOLIO_TACTICAL_OVERLAY` | Cross-category allocators (the 8 `PortfolioAllocator` engines are a distinct concept — not v2 archetype engines). Portfolio-level allocation is a post-MVP layer above the per-strategy engines.                    |
| VOL\_\* (1)       | `VOL_0DTE_PIN_RISK`                                                                                           | 0DTE pin-risk; no leg structure declared. Post-MVP with the rest of the 0DTE/options book.                                                                                                                          |
| ARBITRAGE_MEV (1) | `ARBITRAGE_MEV_SANDWICH`                                                                                      | Theoretical only (`mev/sandwich_theoretical.py`, not registered). Adversarial MEV — deliberately not productionised. The 3 productionised MEV archetypes (BACKRUN / JIT_LIQUIDITY / LIQUIDATION_BUNDLE) ARE backed. |

#### Ratified `not_available` — venues (11, `unbuildable_slot_venue`; 186 cells)

| Venue (eligible-but-unbuildable) | Folded token (∉ `KNOWN_VENUE_TOKENS`) | Cells | Reason (no end-to-end wiring → token NOT added)                                                              |
| -------------------------------- | ------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------ |
| `gmx_v2`                         | `gmxv2`                               | 66    | Alt perp DEX. No adapter+collateral+capability wiring; not on the live path (supported DEXes are tokenised). |
| `betfair_direct`                 | `betfairdirect`                       | 48    | Sports betting exchange. Sports track is non-DeFi-MVP; direct-API venue not wired end-to-end.                |
| `smarkets_direct`                | `smarketsdirect`                      | 36    | Sports betting exchange. As above.                                                                           |
| `pancakeswap_v3`                 | `pancakeswapv3`                       | 10    | Alt DEX. Not wired end-to-end.                                                                               |
| `sushiswap_v3`                   | `sushiswapv3`                         | 10    | Alt DEX. Not wired end-to-end.                                                                               |
| `jupiter`                        | `jupiter`                             | 6     | Solana DEX aggregator. Not wired end-to-end (supported Solana DEXes are tokenised).                          |
| `balancer_v2`                    | `balancerv2`                          | 2     | Alt DEX. Not wired end-to-end.                                                                               |
| `balancer_v3`                    | `balancerv3`                          | 2     | Alt DEX. Not wired end-to-end.                                                                               |
| `matchbook_direct`               | `matchbookdirect`                     | 2     | Sports betting exchange. Not wired end-to-end.                                                               |
| `sommelier`                      | `sommelier`                           | 2     | Yield-vault protocol. Not wired end-to-end.                                                                  |
| `trader_joe`                     | `traderjoe`                           | 2     | Alt DEX. Not wired end-to-end.                                                                               |

Each is honestly `blocked(unbuildable_slot_venue)` today. Adding a token without the adapter/collateral/capability
wiring would re-introduce the F47 over-claim — so the token is added ONLY when a venue is genuinely supported end-to-end
(none qualify now). A later support effort is a new plan item, not a Phase-C gap.

## Discovered debt (2026-06-15)

- [x] ✅ [SCRIPT] P3. **e2e-testing/scripts/defi/test_collateral_validation.py ruff errors** surfaced as warn-only in strategy-service's peripheral-dir QG. — DONE **e2e-testing@8696934** (2026-06-17). Residual set at fix time was 7 (count had drifted from the originally-noted 22): 5 RUF100 unused-`noqa` (auto-fixed) + 2 N806 (`lev_weETH`→`lev_weeth`, `lev_WETH`→`lev_weth`). `ruff check` clean; QG green (27s). Repo: e2e-testing.

## Audit findings (2026-06-15 — adversarial verification of the Phase-B/C completion)

- [x] [BUG] P1. ✅ **AccountQueryClient silently falls back to MOCK data on a live-fetch failure** — FIXED strategy-service@bdf7b3e4: live-mode fetch failures now reraise (fail-loud) instead of returning mock; mock-mode short-circuits at top, unchanged; 6 tests (3 live-fail-loud + 3 mock-still-mocks). QG green. (audit discovery
      2026-06-15). `strategy-service/strategy_service/.../account_query_client.py:133-134/165-166/194` swallows live
      UPI-adapter exceptions and returns FABRICATED balances/positions instead of failing loud. Pre-existing (file
      dated 2026-06-05) but now LOAD-BEARING: the new CeFi `margin_health` / `emit_margin_event_for_cefi` read balances
      through it, so a credentialed live failure produces a margin snapshot with FAKE numbers that looks healthy. Make
      the live path fail-loud (raise / `CLIENT_QUARANTINED` / loud alert) — mock-fallback is dev/CI-only. Target:
      strategy-service.

## Codex SSOT updates

- `codex/04-architecture/client-funds-isolation.md` / margin-traceability section (margin cluster end-to-end).
- `codex/09-strategy/operational/pnl-attribution.md` (net-delta / exposure-normalization owner).
- Collateral haircut SSOT note (which of venue_collateral.py / lst_collateral_resolver.py is canonical post-F28).
- **Phase C (2026-06-15):** `codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md` — reconciled
  the stale registered/stub counts (26→**29** registered / 31→**28** not-engine-backed; the 3 stub→registered since the
  2026-05-22 audit = `CARRY_STAKED_BASIS_DATED` / `CARRY_BASIS_DATED_INV` / `ARBITRAGE_CROSS_DOMAIN_EVENT`) + added the
  **Phase C ratification** section (28 archetypes + 11 venues operator-ratified honestly `not_available`).

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
  shape (positions = collateral_positions notional book carrying MMR; used-margin = USD debt leg) — model is
  owned/complete, this is wiring; (3) venues with no open positions are skipped (the model's `equity<=0` branch would
  falsely grade an empty book 100%). Next: F45 netting consolidation (P1) — pre-audit confirms net-delta logic is
  genuinely multi-site (`risk_group_aggregator`, `aggregated` route, `output_builders` delta_btc/eth, `math_utilities`
  LST→underlying, `risk/engine/orchestrator`), distinct from margin-requirement netting (`margin_sim._netting_factor` —
  left alone).
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
  `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` (net-delta/exposure-netting SSOT section). SHAs: margin
  = UTL@1b215ea9 + strategy-service@b9b26433; F45 = UTL@b819cd1c + execution-service@b7c63335 +
  strategy-service@bdac6595. Phase C (build missing v2 engines) remains separately-scoped (bigger than this pass).
- 2026-06-15 — **Phase C CLOSED — RATIFY-ONLY (build-subset + venue-add both empty).** The dispatch's operator-decision
  blanks (BUILD-SUBSET / VENUE-TOKEN-ADD / RATIFY-ack) were left empty; the dispatch's own empty-case rule + the
  recommended-EMPTY default + AUTONOMOUS_AGENT_RULES rule 2 (decide from documented intent, don't ask) →
  **RATIFY-ONLY**. Re-verified ground truth live (registries drift): 57 enum / **29 engine-backed** (probed via
  `strategy-service/.venv`) / **28 missing** (= 22 `no_v2_engine` + 6 `missing_registry`); **11** unbuildable venues /
  **186** `unbuildable_slot_venue` cells (folded token ∉ `KNOWN_VENUE_TOKENS`, 74 tokens). **Decision (autonomous,
  documented per rule 1):** NO engine built (none on the live path; a registered-but-empty engine re-creates the
  over-claim — worse than honest `not_available`), NO venue token added (no venue wired end-to-end; an unbacked token
  re-introduces the F47 over-claim Phase B fixed). All 28 archetypes + 11 venues RATIFIED honestly `not_available`
  (per-archetype + per-venue tables in the Phase C section above, grouped + reasoned). **Matrix unchanged-and-honest**
  (RATIFY = doc-only, zero code): re-built deterministically → **21600 / available 12977 / blocked 8175 / not_registered
  448** (96 `missing_registry` + 352 `no_v2_engine`) — **identical to the Phase-B counts, delta 0** (as expected: Phase
  B already made it honest; Phase C ratifies that honesty). Committed `capability-verdict-matrix.json` already carries
  these counts. Deterministic PM unit test `tests/unit/test_capability_verdict_matrix.py` **green (7 passed)** —
  unchanged. **Codex** `archetype-paper-readiness.md` reconciled (the doc's 2026-05-22 26-registered/31-stub counts were
  stale by the 3 since-registered archetypes → corrected to 29/28) + a Phase C ratification subsection added. **Entire
  engine findings remediation plan (Phases A/B/C) is now resolved** — A: F28 consolidated (one operator-held follow-up,
  operator-gated by design) + F47/F48 surface; B: margin cluster / F45 / F27 / F16 all shipped; C: ratified. The only
  remaining open `- [ ]` items are the two explicitly operator-/contract-gated follow-ups (F28 live-API probe; F48
  venv-probe), both with documented diagnoses, neither a Phase-C gap.
- 2026-06-17 — **F48 venv-probe SHIPPED + F28 go-live markers made loud (operator-requested).** **F48** (PM@362f90404):
  deleted the `_ENGINE_BACKED_ARCHETYPE_VALUES` transcription; the verdict-matrix generator now probes
  `ARCHETYPE_ENGINE_REGISTRY` LIVE via strategy-service's `.venv` (`_probe_engine_backed_archetypes`, fail-loud),
  `build_matrix` takes the engine-backed set as an injected param (hermetic unit test passes a fixture + a new
  live-parity drift guard). The deterministic-test self-containment tension is resolved, not bypassed. **F28**
  (UAC@5fccaa7): the two operator-held placeholder haircuts (Bybit stETH / Drift mSOL, conservative 0.10) are now
  unmissable before go-live — a `⚠️ PRE-GO-LIVE TODO` module banner, inline `UPDATE … BEFORE GO-LIVE` comments + `notes`,
  and a machine-checkable `PLACEHOLDER_HAIRCUTS_PENDING_GO_LIVE` constant (exported) a go-live preflight can assert. F28
  STAYS OPEN by design (operator approves the real probed diff — decision #3). Routine PM version-alignment churn
  (LDR 1.2.146 behind main 1.2.147) was reconciled via a sanctioned main→LDR back-merge to land F48. **Net: every open
  autonomously-closeable item in this plan is now done; the sole remaining `- [ ]` is the operator-gated F28 probe.**
