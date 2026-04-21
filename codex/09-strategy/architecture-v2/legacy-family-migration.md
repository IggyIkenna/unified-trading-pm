# Legacy Family String Migration Report

**Audit driver:** `plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md` § `p8-audit-legacy-family-strings`.

**Scope:** Find every lowercase / v1-era family string (`basis-trade`, `mean-reversion`, `sports-arb`, `prediction-ml`,
etc.) used as a route slug, filter value, or user-visible display label in `unified-trading-system-ui`. Migrate to v2
canonical names or flag for the Phase 11 strategy fixture regeneration (see `legacy-mapping.ts`).

**Owning code:**

- v2 canonical family enum: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py` (Python
  SSOT) + `unified-trading-system-ui/lib/architecture-v2/enums.ts` (TypeScript mirror).
- v1→v2 bridge: `unified-trading-system-ui/lib/architecture-v2/legacy-mapping.ts` (`LEGACY_FAMILY_TO_V2` map).

---

## 1. Categories of findings

### 1.1 Legitimate migration targets — DONE

These user-visible URL slugs / route labels were migrated in earlier waves:

| Old slug                 | New slug                 | Commit       |
| ------------------------ | ------------------------ | ------------ |
| `/.../basis-trade`       | `/.../carry-basis`       | UI `d417223` |
| "Basis Trade" page title | "Carry-Basis" page title | UI `d417223` |

These are closed. Confirmed no remaining `/basis-trade` URLs in `app/` or `components/` via
`rg "/basis-trade" unified-trading-system-ui/{app,components}`.

### 1.2 Out-of-scope until Phase 11 (strategy fixture migration) — DEFERRED

Canonical statement from `lib/architecture-v2/legacy-mapping.ts`:

> The existing `strategy-catalog-data.ts` fixture (53 strategies) was written before the v2 taxonomy landed. Rather than
> regenerate the fixture in this phase 9 session — which would cascade into the 6 detail tabs — we map at read time so
> the family dashboards aggregate correctly.
>
> Follow-up: regenerate the catalog fixture from UAC `StrategyInstanceDefinition` rows once phase 11 (strategy
> migration) lands and delete this mapping.

Concrete files that still use v1 family strings AS LEGITIMATE FIXTURE DATA (read through `legacyFamilyToV2()` at display
time):

- `unified-trading-system-ui/lib/strategy-registry.ts` — 53-strategy v1 fixture with `strategyType: "Basis Trade"` /
  `"Mean Reversion"` / `"Prediction ML Directional"` etc.
- `unified-trading-system-ui/lib/mocks/fixtures/strategy-catalog-data.ts` — dashboards feed.
- `unified-trading-system-ui/lib/mocks/fixtures/{promote-candidates,trading-data,build-data,ml-data,strategy-platform,defi-basis-trade,kill-switch-entities}.ts`
  — widget mock data.
- `unified-trading-system-ui/lib/reference-data.ts` — reference labels for filter UIs.
- `unified-trading-system-ui/lib/taxonomy.ts` — v1 taxonomy, feeds lifecycle nav.
- `unified-trading-system-ui/lib/config/services/strategies.config.ts` — `ARCHETYPES` filter list with
  `{ id: "BASIS_TRADE", label: "Basis Trade" }` entries (matches v1 `strategy-registry.ts` archetype ids).
- `unified-trading-system-ui/lib/config/strategy-config-schemas/{cefi,defi,tradfi,sports,prediction}.ts` — per-category
  config schemas with v1 strategy ids.
- `unified-trading-system-ui/components/widgets/sports/register.ts` — sports-arb widget registrations.
- `unified-trading-system-ui/components/dashboards/trader-dashboard.tsx` — `id: "sports-arb"` dashboard card.
- `unified-trading-system-ui/lib/help/help-tree.ts` + `unified-trading-system-ui/lib/glossary.ts` — help / glossary
  entries.

**Why deferred:** these are all consumed in lockstep by the v1 strategy-registry + v1-style UI views. Unilaterally
renaming `"Basis Trade"` → `"Carry & Yield · Carry Basis Perp"` without simultaneously regenerating the fixture +
updating the display components would break ~400 tests and break the v1 trading page. Per plan header convention
"clean-break when all 60+ repos are available; temporary co-existence when not", and per the explicit comment in
`legacy-mapping.ts`, this is a Phase 11 deliverable.

**Tracking:** add a follow-up plan `plans/active/strategy_fixture_v2_regeneration_<date>.plan.md` when Phase 11 work
begins.

### 1.3 Intentional v1 identifiers — NOT TARGETS

These are NOT migration targets. They are internal keys that happen to use the lowercase-hyphen style but are
identifiers (not display labels / route slugs / family strings):

- `defi-swap-widget.tsx` `config.mode === "basis-trade"` — widget config discriminator; changing it would break the
  widget's internal mode routing and has nothing to do with the v2 family enum.
- `glossary.ts` `"mean-reversion"` entry — dictionary key for `<Term id="mean-reversion">` tooltip lookups. Legitimate
  jargon entry.
- `components/trading/sports/arb-tab.tsx` — `"arb"` suffix is domain terminology ("arbitrage"), not a family string.
- `help-tree.ts` `id: "sports-arb"` — internal help-tree node id.
- `config-page-schema.ts` `id: "sports-arb"` — internal config schema id.

---

## 2. Exit criteria

Per plan p8-audit-legacy-family-strings:

- [x] Grep performed across UI + services.
- [x] Route slug `basis-trade` → `carry-basis` — done Wave 1 (UI `d417223`).
- [x] Display label "Basis Trade" on dedicated page → "Carry Basis" — done Wave 1.
- [x] Migration report produced (this document).
- [ ] 53-strategy fixture regeneration — Phase 11 follow-up.
- [x] v1→v2 equivalency audit — **see § 2.1 below (2026-04-21)**.

The plan checkbox can flip to `[x]` on the basis of the audit being complete + migrations being either applied or
tracked. No further route-slug / display-label migrations are viable until Phase 11.

### 2.1 v1 strategy-registry.ts equivalency audit (2026-04-21)

**Audit driver:** `plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md` § follow-up Task C — user directive
2026-04-21 "we don't need v1 strategies anymore as long as we are sure they are at least as maturely integrated in v2".

**Scope:** all 56 entries in `unified-trading-system-ui/lib/strategy-registry.ts` `STRATEGIES: Strategy[]`, mapped to
the nearest v2 `(family, archetype, category)` triple and against UAC's post-Wave-3-A `STRATEGY_REGISTRY` (96 slot
entries derived from `ARCHETYPE_CAPABILITY_REGISTRY`) + UI `lib/architecture-v2/coverage.ts`.

**Verdict:** **6 GAP / 50 EQUIVALENT → retain v1, do NOT delete.**

Summary of gaps (detail per row below):

| Cluster                    | Rows | Verdict         | Reason                                                                                                                                                                                                                                                                                                                                                    |
| -------------------------- | ---- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Elysium provider entries   | 3    | GAP (retired)   | Provider deleted from UAC per workspace CLAUDE.md (Elysium, Arkham, Bloxroute, Pyth, Infura). v1 rows reference a retired venue. Strategy concepts (CARRY_BASIS_PERP / YIELD_ROTATION_LENDING / CARRY_RECURSIVE_STAKED) exist in v2, but mapped to other venues. Technically RETIRED, not SUPERSET — calling them EQUIVALENT would misrepresent coverage. |
| Sports value-betting       | 2    | GAP (semantics) | v2 lacks a dedicated `VALUE_BETTING` archetype. `ARBITRAGE_PRICE_DISPERSION` is a riskless cross-bookmaker arb; value-betting is a single-side positive-EV wager with real drawdown risk. Distinct strategy semantics — SUPERSET mapping would lose risk-profile fidelity.                                                                                |
| TradFi bond mean-reversion | 1    | GAP (cell)      | v2 has `STAT_ARB_PAIRS_FIXED` as an archetype, but `coverage.ts` does not declare a TradFi·bond cell for it. Archetype exists but the coverage cell is absent — SUPPORTED not PARTIAL, so v1 row is orphaned.                                                                                                                                             |

**Gated decision (per Task C gate "if ANY v1 entry maps to v2 GAP → STOP"):** v1 retained in place. Do NOT delete
`lib/strategy-registry.ts`. Do NOT delete `legacyFamilyToV2()` — still in active use (18 files). Phase 11 fixture
regeneration remains the canonical closure for this debt.

**Closure prerequisites for a future Phase-11-adjacent delete wave:**

1. Add `VALUE_BETTING` archetype to v2 (or justify folding into an existing archetype with a written semantic guard).
2. Add TradFi·bond SUPPORTED cell under `STAT_ARB_PAIRS_FIXED` in `lib/architecture-v2/coverage.ts` + UAC
   `ARCHETYPE_CAPABILITY_REGISTRY`.
3. Mark the 3 Elysium rows explicitly RETIRED in the migration doc + in the v2 availability store (not EQUIVALENT).
4. Regenerate `lib/mocks/fixtures/strategy-catalog-data.ts` from UAC `STRATEGY_REGISTRY` so consumer pages that need
   rich mock data (instruments, performance, PnL breakdown, kelly sizing) have a v2-native source.
5. Migrate 18 consumer files (per `rg "from.*lib/strategy-registry"`) from `STRATEGIES` / `getStrategyById` /
   `generatePositionsForStrategy` to v2-equivalents sourced from `coverage.ts` + the new mock fixture.

Once all 5 prerequisites ship, v1 `lib/strategy-registry.ts` can be deleted in a clean break wave.

### 2.2 Full row-by-row audit table

Mapping is `v1_archetype` + asset-class inference → `v2_family.v2_archetype` + `VenueCategoryV2`.

| #   | v1 strategy_id                      | v1 asset   | v1 type          | v1 archetype           | v2 family            | v2 archetype                 | v2 category | Verdict                          |
| --- | ----------------------------------- | ---------- | ---------------- | ---------------------- | -------------------- | ---------------------------- | ----------- | -------------------------------- |
| 1   | DEFI_ETH_BASIS_HUF_1H               | DeFi       | Basis Trade      | BASIS_TRADE            | CARRY_AND_YIELD      | CARRY_BASIS_PERP             | DEFI        | EQUIVALENT                       |
| 2   | DEFI_ETH_REC_STAKE_HUF_1H           | DeFi       | Leveraged Basis  | BASIS_TRADE            | CARRY_AND_YIELD      | CARRY_RECURSIVE_STAKED       | DEFI        | EQUIVALENT                       |
| 3   | DEFI_UNI_LP_HUF_1H                  | DeFi       | LP Provision     | MARKET_MAKING          | MARKET_MAKING        | MARKET_MAKING_CONTINUOUS     | DEFI        | EQUIVALENT                       |
| 4   | CEFI_BTC_MM_EVT_TICK                | CeFi       | Market Making    | MARKET_MAKING          | MARKET_MAKING        | MARKET_MAKING_CONTINUOUS     | CEFI        | EQUIVALENT                       |
| 5   | CEFI_ETH_OPT_MM_EVT_TICK            | CeFi       | Options MM       | OPTIONS                | VOL_TRADING          | VOL_TRADING_OPTIONS          | CEFI        | EQUIVALENT                       |
| 6   | TRADFI_SPY_MOM_HUF_1D               | TradFi     | ML Directional   | DIRECTIONAL            | ML_DIRECTIONAL       | ML_DIRECTIONAL_CONTINUOUS    | TRADFI      | EQUIVALENT                       |
| 7   | SPORTS_NFL_ARB_SCE_GAME             | Sports     | Arbitrage        | ARBITRAGE              | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | SPORTS      | EQUIVALENT                       |
| 8   | CEFI_BTC_BASIS_SCE_1H               | CeFi       | Basis Trade      | BASIS_TRADE            | CARRY_AND_YIELD      | CARRY_BASIS_PERP             | CEFI        | EQUIVALENT                       |
| 9   | PRED_POLY_ARB_SCE_1M                | Prediction | Arbitrage        | ARBITRAGE              | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | PREDICTION  | EQUIVALENT                       |
| 10  | PRED_BTC_CEFI_ARB_SCE_5M            | Prediction | Arbitrage        | PREDICTION_ARB         | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | PREDICTION  | EQUIVALENT                       |
| 11  | DEFI_AAVE_LEND_HUF_1D               | DeFi       | Lending          | YIELD                  | CARRY_AND_YIELD      | YIELD_ROTATION_LENDING       | DEFI        | EQUIVALENT                       |
| 12  | CEFI_BTC_ML_DIR_HUF_4H              | CeFi       | ML Directional   | DIRECTIONAL            | ML_DIRECTIONAL       | ML_DIRECTIONAL_CONTINUOUS    | CEFI        | EQUIVALENT                       |
| 13  | SPORTS_NBA_ML_HUF_GAME              | Sports     | Sports ML        | DIRECTIONAL            | ML_DIRECTIONAL       | ML_DIRECTIONAL_EVENT_SETTLED | SPORTS      | EQUIVALENT                       |
| 14  | DEFI_MORPHO_LEND_HUF_1D             | DeFi       | Lending          | YIELD                  | CARRY_AND_YIELD      | YIELD_ROTATION_LENDING       | DEFI        | EQUIVALENT                       |
| 15  | TRADFI_BOND_MEAN_REV_HUF_1D         | TradFi     | Mean Reversion   | MEAN_REVERSION         | STAT_ARB_PAIRS       | STAT_ARB_PAIRS_FIXED         | TRADFI      | **GAP**                          |
| 16  | CEFI_ETH_MOM_HUF_4H                 | CeFi       | Momentum         | MOMENTUM               | RULES_DIRECTIONAL    | RULES_DIRECTIONAL_CONTINUOUS | CEFI        | EQUIVALENT                       |
| 17  | CEFI_SOL_MOM_HUF_4H                 | CeFi       | Momentum         | MOMENTUM               | RULES_DIRECTIONAL    | RULES_DIRECTIONAL_CONTINUOUS | CEFI        | EQUIVALENT                       |
| 18  | CEFI_MULTI_ARB_SCE_TICK             | CeFi       | Arbitrage        | ARBITRAGE              | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | CEFI        | EQUIVALENT                       |
| 19  | CEFI_AVAX_MOMENTUM_HUF_1H           | CeFi       | Momentum         | MOMENTUM               | RULES_DIRECTIONAL    | RULES_DIRECTIONAL_CONTINUOUS | CEFI        | EQUIVALENT                       |
| 20  | CEFI_ETH_MEAN_REV_SCE_4H            | CeFi       | Mean Reversion   | MEAN_REVERSION         | STAT_ARB_PAIRS       | STAT_ARB_PAIRS_FIXED         | CEFI        | EQUIVALENT (IM-live PUBLIC cell) |
| 21  | CEFI_DOGE_MM_HUF_30S                | CeFi       | Market Making    | MARKET_MAKING          | MARKET_MAKING        | MARKET_MAKING_CONTINUOUS     | CEFI        | EQUIVALENT                       |
| 22  | CEFI_LINK_MOMENTUM_SCE_2H           | CeFi       | Momentum         | MOMENTUM               | RULES_DIRECTIONAL    | RULES_DIRECTIONAL_CONTINUOUS | CEFI        | EQUIVALENT                       |
| 23  | CEFI_ARB_MEAN_REV_HUF_15M           | CeFi       | Mean Reversion   | MEAN_REVERSION         | STAT_ARB_PAIRS       | STAT_ARB_PAIRS_FIXED         | CEFI        | EQUIVALENT                       |
| 24  | CEFI_XRP_MM_HUF_1M                  | CeFi       | Market Making    | MARKET_MAKING          | MARKET_MAKING        | MARKET_MAKING_CONTINUOUS     | CEFI        | EQUIVALENT                       |
| 25  | TRADFI_ES_ML_DIR_SCE_30M            | TradFi     | ML Directional   | ML_DIRECTIONAL         | ML_DIRECTIONAL       | ML_DIRECTIONAL_CONTINUOUS    | TRADFI      | EQUIVALENT                       |
| 26  | TRADFI_SPY_OPTIONS_ML_EVT_1D        | TradFi     | Options ML       | OPTIONS                | VOL_TRADING          | VOL_TRADING_OPTIONS          | TRADFI      | EQUIVALENT                       |
| 27  | TRADFI_CL_ML_DIR_SCE_1H             | TradFi     | ML Directional   | ML_DIRECTIONAL         | ML_DIRECTIONAL       | ML_DIRECTIONAL_CONTINUOUS    | TRADFI      | EQUIVALENT                       |
| 28  | TRADFI_GC_MM_OPTIONS_EVT_TICK       | TradFi     | Options MM       | OPTIONS                | VOL_TRADING          | VOL_TRADING_OPTIONS          | TRADFI      | EQUIVALENT                       |
| 29  | TRADFI_ZN_OPTIONS_ML_SCE_4H         | TradFi     | Options ML       | OPTIONS                | VOL_TRADING          | VOL_TRADING_OPTIONS          | TRADFI      | EQUIVALENT                       |
| 30  | TRADFI_SI_ML_DIR_SCE_2H             | TradFi     | ML Directional   | ML_DIRECTIONAL         | ML_DIRECTIONAL       | ML_DIRECTIONAL_CONTINUOUS    | TRADFI      | EQUIVALENT                       |
| 31  | TRADFI_QQQ_MM_OPTIONS_EVT_5M        | TradFi     | Options MM       | OPTIONS                | VOL_TRADING          | VOL_TRADING_OPTIONS          | TRADFI      | EQUIVALENT                       |
| 32  | TRADFI_EURUSD_ML_DIR_SCE_1H         | TradFi     | ML Directional   | ML_DIRECTIONAL         | ML_DIRECTIONAL       | ML_DIRECTIONAL_CONTINUOUS    | TRADFI      | EQUIVALENT                       |
| 33  | TRADFI_HG_OPTIONS_ML_SCE_1D         | TradFi     | Options ML       | OPTIONS                | VOL_TRADING          | VOL_TRADING_OPTIONS          | TRADFI      | EQUIVALENT                       |
| 34  | DEFI_WBTC_BASIS_HUF_4H              | DeFi       | Basis Trade      | BASIS_TRADE            | CARRY_AND_YIELD      | CARRY_BASIS_PERP             | DEFI        | EQUIVALENT                       |
| 35  | DEFI_STETH_STAKED_BASIS_HUF_1D      | DeFi       | Staked Basis     | BASIS_TRADE            | CARRY_AND_YIELD      | CARRY_STAKED_BASIS           | DEFI        | EQUIVALENT                       |
| 36  | DEFI_ETH_RECURSIVE_STAKED_HUF_BLOCK | DeFi       | Recursive Staked | RECURSIVE_STAKED_BASIS | CARRY_AND_YIELD      | CARRY_RECURSIVE_STAKED       | DEFI        | EQUIVALENT                       |
| 37  | DEFI_USDC_AAVE_LEND_HUF_1H          | DeFi       | Lending          | YIELD                  | CARRY_AND_YIELD      | YIELD_ROTATION_LENDING       | DEFI        | EQUIVALENT                       |
| 38  | DEFI_ARB_AMM_LP_HUF_4H              | DeFi       | AMM LP           | AMM_LP                 | MARKET_MAKING        | MARKET_MAKING_CONTINUOUS     | DEFI        | EQUIVALENT                       |
| 39  | DEFI_MATIC_AMM_LP_HUF_2H            | DeFi       | AMM LP           | AMM_LP                 | MARKET_MAKING        | MARKET_MAKING_CONTINUOUS     | DEFI        | EQUIVALENT                       |
| 40  | DEFI_DAI_AAVE_LEND_HUF_8H           | DeFi       | Lending          | YIELD                  | CARRY_AND_YIELD      | YIELD_ROTATION_LENDING       | DEFI        | EQUIVALENT                       |
| 41  | SPORTS_EPL_ARB_EVT_MATCH            | Sports     | Arbitrage        | SPORTS_ARB             | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | SPORTS      | EQUIVALENT                       |
| 42  | SPORTS_NFL_VALUE_BET_EVT_GAME       | Sports     | Value Betting    | SPORTS_ARB             | —                    | —                            | SPORTS      | **GAP**                          |
| 43  | SPORTS_LALIGA_ML_EVT_MATCH          | Sports     | Sports ML        | SPORTS_ARB             | ML_DIRECTIONAL       | ML_DIRECTIONAL_EVENT_SETTLED | SPORTS      | EQUIVALENT                       |
| 44  | SPORTS_NBA_MM_EVT_QUARTER           | Sports     | Sports MM        | MARKET_MAKING          | MARKET_MAKING        | MARKET_MAKING_EVENT_SETTLED  | SPORTS      | EQUIVALENT                       |
| 45  | SPORTS_MLB_VALUE_BET_EVT_GAME       | Sports     | Value Betting    | SPORTS_ARB             | —                    | —                            | SPORTS      | **GAP**                          |
| 46  | SPORTS_SERIE_A_ARB_EVT_MATCH        | Sports     | Arbitrage        | SPORTS_ARB             | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | SPORTS      | EQUIVALENT                       |
| 47  | PREDICTION_POLY_ML_DIR_EVT_4H       | Prediction | ML Directional   | PREDICTION_ARB         | ML_DIRECTIONAL       | ML_DIRECTIONAL_EVENT_SETTLED | PREDICTION  | EQUIVALENT                       |
| 48  | PREDICTION_POLY_ARB_EVT_1H          | Prediction | Arbitrage        | PREDICTION_ARB         | ARBITRAGE_STRUCTURAL | ARBITRAGE_PRICE_DISPERSION   | PREDICTION  | EQUIVALENT                       |
| 49  | CEFI_MATIC_MOMENTUM_SCE_2H          | CeFi       | Momentum         | MOMENTUM               | RULES_DIRECTIONAL    | RULES_DIRECTIONAL_CONTINUOUS | CEFI        | EQUIVALENT                       |
| 50  | CEFI_SUI_MOMENTUM_HUF_1H            | CeFi       | Momentum         | MOMENTUM               | RULES_DIRECTIONAL    | RULES_DIRECTIONAL_CONTINUOUS | CEFI        | EQUIVALENT                       |
| 51  | SPORTS_BETFAIR_MM_EVT_TICK          | Sports     | Sports MM        | MARKET_MAKING          | MARKET_MAKING        | MARKET_MAKING_EVENT_SETTLED  | SPORTS      | EQUIVALENT                       |
| 52  | DEFI_ETH_STAKED_BASIS_HUF_1H        | DeFi       | Staked Basis     | BASIS_TRADE            | CARRY_AND_YIELD      | CARRY_STAKED_BASIS           | DEFI        | EQUIVALENT                       |
| 53  | DEFI_AAVE_SUPPLY_USDC_HUF_1H        | DeFi       | Lending          | YIELD                  | CARRY_AND_YIELD      | YIELD_ROTATION_LENDING       | DEFI        | EQUIVALENT                       |
| 54  | ELYSIUM_AAVE_LENDING                | DeFi       | Yield Lending    | YIELD                  | —                    | —                            | —           | **GAP (retired)**                |
| 55  | ELYSIUM_BASIS_TRADE                 | DeFi       | Basis Trade      | BASIS_TRADE            | —                    | —                            | —           | **GAP (retired)**                |
| 56  | ELYSIUM_RECURSIVE_STAKED_BASIS      | DeFi       | Recursive Yield  | RECURSIVE_STAKED_BASIS | —                    | —                            | —           | **GAP (retired)**                |

### 2.3 Open v1→v2 gaps (track for follow-up plan)

Proposed follow-up plan title: `strategy_fixture_v2_regeneration_<date>.plan.md`. Five prerequisites enumerated in § 2.1
above. Until that plan lands, `lib/strategy-registry.ts` + `legacyFamilyToV2()` remain in place.

---

## 3. References

- `codex/09-strategy/architecture-v2/strategy-registry-v2.md` — canonical v2 registry overview.
- `codex/09-strategy/architecture-v2/naming-convention.md` — `parse_strategy_id` / `format_strategy_id` canonical form.
- `lib/architecture-v2/legacy-mapping.ts` — v1→v2 bridge with the explicit "Phase 11 regen + delete" follow-up comment.
