---
doc_type: plan
title: Strategy-service reference-constants inventory (W7 "69 candidates" audit)
summary: >-
  Full per-constant inventory table for the W7 "inventory and classify all 69 candidates" todo in
  strategy_service_centralization_fixes_2026_08_16.md, split out to a sibling doc because the parent plan is
  already over its 500-line soft cap (571 lines pre-split) and this table would push it further -- same pattern as
  code_readiness_t3_features_ml_strategy_2026_08_19.md's code_readiness_t3_progress_history_2026_08_20.md split.
  Real measured count of module-level reference-shaped constants under strategy_service/engine/strategies/ (grepped
  2026-08-21) is 75, not the claimed 69 -- see "Count discrepancy" below. Classified per the parent plan's own
  four-destination rule and the `_ALLOWED_CHAINS` type specimen shape (symbol, file:line, fact encoded, consumer
  count, SSOT check, destination).
status: active
nature: process
asset_group: [defi, cross-cutting]
stage: [execution]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [defi, centralization, reference-data, inventory, strategy-service]
related:
  [
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    /codex/04-architecture/position-risk-centralization.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
context_scope: [/plans/active/strategy_service_centralization_fixes_2026_08_16.md]
supersedes:
superseded_by:
depends_on: []
source: >-
  Line-cap split of strategy_service_centralization_fixes_2026_08_16.md's W7 inventory todo (2026-08-21) -- the
  full 75-row table was written directly into the parent plan's W7 section first draft, then moved here before
  commit because the parent was already at 571 lines (over the 500-line soft cap) before the table was added.
assigned_role: backend_engineer
effort: low # inventory + classification, migration work tracked back in the parent plan
drift_direction: none
---

## Count discrepancy: 75 measured vs 69 claimed

Grepped `strategy_service/engine/strategies/` for module-level constants matching
`^_?[A-Z][A-Z0-9_]*\s*(:\s*[\w.\[\], ]*)?=\s*(frozenset|dict|tuple|list|\{|\(|\[)` (2026-08-21): **76 raw matches**.
One of those, `_ALLOWED_CHAINS` (`carry_and_yield/staked_basis.py:188`), is already classified and closed by the
parent plan's exemplar todo (STAYS LOCAL, done 2026-08-21) — excluded from this table to avoid a duplicate row,
leaving **75 candidates here**.

75 vs the plan's stated 69 (measured 2026-08-16) is a **net +6 over 5 days**, not a wrong original count: the
`_STAKING_PROTOCOL_CHAIN` exemplar constant the 69 was measured against has since been deleted (migrated to UAC
`get_chain_for_protocol()`, `strategy-service@8a7f80e8`), and this plan's own Progress Log records multiple
sessions actively adding new archetype-scoped catalog/config constants in the same window (staked-basis buffered
margin, Pacifica reinstatement, margin-health-cache wiring, etc.). Net drift of a handful of constants over 5 days
of active development on this exact code path is expected, not evidence the 2026-08-16 count was mismeasured.

## Method

For each candidate: symbol, file:line, the fact it encodes, real consumer count (grep, excluding the definition
site and re-exports), whether a confirmed-real SSOT exists elsewhere (probed by content/vocabulary, not name
similarity), and destination per the parent plan's four-destination rule. **STAYS LOCAL is the default outcome for
anything that is archetype-specific trading policy (which venues/chains/coins/LSTs *this* archetype is willing to
trade) rather than a fact about the external world** — this mirrors the `_ALLOWED_CHAINS` precedent exactly, and it
is the overwhelming pattern measured here: strategy-service's `target_universe/catalog_*.py` constants are almost
all heavily operator-ruling-cited archetype policy, not duplicated reference data.

## Inventory table

| # | Symbol | File:Line | Fact encoded | Consumers | SSOT check | Destination |
|---|--------|-----------|---------------|-----------|------------|-------------|
| 1 | `CEFI_SLOTS` | archetype_slots_cefi.py:23 | CeFi archetype→slot-label factory table (20 strings) | 8 | No UAC equivalent — internal engine bootstrap data, not external reference | STAYS LOCAL — strategy-service's own factory-string taxonomy, not a fact any other service needs |
| 2 | `DEFI_SLOTS` | archetype_slots_defi.py:19 | DeFi archetype→slot-label factory table | 16 | Same as above | STAYS LOCAL |
| 3 | `SPORTS_SLOTS` | archetype_slots_sports.py:19 | Sports archetype→slot-label factory table | 9 | Same as above | STAYS LOCAL |
| 4 | `TRADFI_SLOTS` | archetype_slots_tradfi.py:19 | TradFi archetype→slot-label factory table | 8 | Same as above | STAYS LOCAL |
| 5 | `PENDING_CROSS_REPO_WAIVER` | clients_yaml_coverage.py:32 | Honest in-repo record of archetypes still missing a `deployment-service` clients.yaml/waiver file | 2 | No SSOT — deliberately a shrinking local tracking set per its own docstring, target file lives in another repo this tranche doesn't own | STAYS LOCAL — explicitly a temporary local ledger, not reference data |
| 6 | `FUNDING_RATE_DISP_FULL_6_VENUES` | archetype_slots_common.py:103 | 6-venue funding-dispersion slot venue set | 5 | UAC has venue capability data (`VENUE_DATA_TYPE_CAPABILITIES`) but not this curated *archetype-eligible* subset | STAYS LOCAL — curation (which of the UAC-capable venues this slot family trades), not raw capability data |
| 7 | `FUNDING_RATE_DISP_4_CEFI_VENUES` | archetype_slots_common.py:113 | 4-venue CeFi-only funding-dispersion subset | 7 | Same | STAYS LOCAL |
| 8 | `FUNDING_RATE_DISP_3_CEFI_VENUES` | archetype_slots_common.py:120 | 3-venue CeFi-only funding-dispersion subset | 3 | Same | STAYS LOCAL |
| 9 | `_ARCHETYPE_ENGINE_SOURCE` | factory.py:29 | Archetype→(module path, class name) lazy-import table | 2 | No SSOT — this is strategy-service's own class-loading mechanism | STAYS LOCAL — internal wiring, not reference data |
| 10 | `KELLY_FRACTION_BY_ARCHETYPE` | archetype_defaults.py:40 | Per-archetype Kelly-sizing fraction (risk tier) | 15 | No SSOT — a strategy-service risk-sizing policy decision, not external fact | STAYS LOCAL — sizing policy, matches `_ALLOWED_CHAINS` shape (archetype-specific, cited tiers) |
| 11 | `V1_ARCHETYPES_IN_SCOPE` | archetype_defaults.py:156 | Derived set of archetypes with a Kelly fraction (`KELLY_FRACTION_BY_ARCHETYPE.keys()`) | 17 | N/A — derived from #10, not independent data | STAYS LOCAL — pure derivation of a local constant |
| 12 | `GREENFIELD_ARCHETYPES` | archetype_defaults.py:173 | Archetypes intentionally never given a legacy-strategy mapping (test-coverage bookkeeping) | 6 | No SSOT | STAYS LOCAL — test/coverage bookkeeping specific to this repo |
| 13 | `TRADFI_DEFAULT_PARAMS` | archetype_defaults.py:254 | Default `respect_market_hours` param for every TradFi slot | 2 | No SSOT — a strategy-service default-params policy | STAYS LOCAL |
| 14 | `PARAM_SCHEMA_REGISTRY` | param_schema.py:187 | Archetype→param-spec-list schema registry | many (UI/config surface) | No SSOT — strategy-service's own param schema | STAYS LOCAL — not venue/chain/token reference data, it's this service's config contract |
| 15 | `_REFERENCE_PRICE_SECTION` | param_schema.py:1338 | Param-spec section grouping (schema UI grouping) | few | No SSOT | STAYS LOCAL |
| 16 | `_PNL_SECTION` | param_schema.py:1360 | Param-spec section grouping | few | No SSOT | STAYS LOCAL |
| 17 | `_ANALYTICS_SECTION` | param_schema.py:1398 | Param-spec section grouping | few | No SSOT | STAYS LOCAL |
| 18 | `_RISK_SECTION` | param_schema.py:1450 | Param-spec section grouping | few | No SSOT | STAYS LOCAL |
| 19 | `GOVERNING_SECTIONS` | param_schema.py:1473 | Section-name→spec-list roll-up of #15-18 | few | N/A — derived | STAYS LOCAL |
| 20 | `_SCHEMA_COVERAGE_BASELINE_MISSING_SCHEMA` | param_schema.py:1562 | Shrinking-ratchet baseline (currently empty) for archetypes missing a param schema | test-only | N/A | STAYS LOCAL — a QG ratchet baseline, not reference data |
| 21 | `STRATEGY_TYPE_TO_SLOT` | archetype_slot_resolver.py:79 | Union of all `*_SLOTS` tables (#1-4) into one lookup | 61 | N/A — derived facade over local data | STAYS LOCAL |
| 22 | `SHARE_CLASS_LOWER_TO_ENUM` | slot_label.py:19 | Lowercase string→`ShareClass` enum lookup | 4 | UAC owns `ShareClass` itself; this is a derived case-folding helper, not new data | STAYS LOCAL — trivial derivation (`{sc.value.lower(): sc for sc in ShareClass}`), nothing to migrate |
| 23 | `VALID_ENVS` | slot_label.py:21 | Valid slot-label environment tokens (`prod/paper/canary/dev`) | 2 | No SSOT | STAYS LOCAL — slot-label grammar is strategy-service's own parsing convention |
| 24 | `HANDLER_RESOLVED` | paper_subscription.py:78 | Archetypes with a resolved paper-subscription handler | 7 | No SSOT | STAYS LOCAL |
| 25 | `PAPER_SUBSCRIPTION_REGISTRY` | paper_subscription.py:97 | Archetype→paper-subscription-spec registry | 9 | No SSOT | STAYS LOCAL |
| 26 | `ARCHETYPE_ALLOCATOR` | archetype_allocator.py:42 | Archetype→allocator-class registry | 4 | No SSOT | STAYS LOCAL |
| 27 | `_DEFI_ARCHETYPES` | batch_harness.py:61 | Set of archetypes in the DeFi family (batch-harness scoping) | 4 | UAC `StrategyFamily`/`StrategyArchetype` enums exist but not this pre-filtered membership set | STAYS LOCAL — trivial derived membership set, test/harness scoping only |
| 28 | `_FAMILY_TO_ASSET_GROUP` | live_routing.py:54 | `StrategyFamily` → event-log `asset_group` shard key, for the 3 families that publish `AtomicInstruction` | 2 | UAC has no family→asset_group map (asset_group taxonomy lives in UAC but this specific derived mapping for LEADER_HEDGE routing does not) | AMBIGUOUS — asset_group is a UAC-owned axis in principle, but this table is a narrow routing-key derivation for one publish path, not general reference data; flag for operator: fold into UAC's asset_group taxonomy vs. keep as routing-local |
| 29 | `_MONTH_ABBREV` | vol_trading/atm_straddle_resolver.py:37 (pre-migration) | Locale-independent month→3-letter-abbrev map for Deribit/options instrument-symbol construction | 1 (this file) | No UTL/UAC calendar-abbreviation SSOT existed | ✅ MIGRATED 2026-08-21 — destination #4 (centralized domain module) applies directly: needed by 2 resolvers in this domain, no existing SSOT required to qualify. Moved to new shared module `strategy_service/engine/strategies/v2/dated_symbol_conventions.py::MONTH_ABBREV`; both local dicts deleted, both files re-import under the original private name (`as _MONTH_ABBREV`) so existing call sites/tests are unchanged. New unit tests added (`tests/unit/engine/strategies/v2/test_dated_symbol_conventions.py`). This corrects the original AMBIGUOUS verdict below — "no SSOT to migrate to" conflated "no *pre-existing* SSOT" with "no valid destination"; the four-destination table's #4 doesn't require a pre-existing module, only a genuine multi-consumer need, which this had (confirmed byte-identical duplicate, see #67). |
| 30 | `_STRIKE_INCREMENT` | vol_trading/atm_straddle_resolver.py:57 | Per-underlying option strike-price grid (btc=1000, eth=100, spx=25) | 1 | Not found in UAC's option/instrument registries under a quick probe; instruments-service is the more likely long-term owner of strike-grid reference data but no confirmed-real SSOT located | AMBIGUOUS — plausibly instrument reference data (strike ticks), but no confirmed SSOT exists to migrate to; flag for operator rather than guess instruments-service scope |
| 31 | `_BUILDERS_BY_ARCHETYPE` | target_universe/catalog.py:99 | Archetype→target-universe-builder-function registry | 1 (used to build #32) | No SSOT | STAYS LOCAL — internal wiring |
| 32 | `TARGET_UNIVERSE` | target_universe/catalog.py:152 | Full flattened tuple of every archetype's target instances | many | N/A — derived from every catalog_*.py constant below | STAYS LOCAL — the aggregation point, not new data |
| 33 | `_STRUCTURAL_KEYS_EXEMPT` | target_universe/catalog_engine_coverage.py:53 | Param keys exempt from the catalogue-key-coverage QG check | test-only | No SSOT | STAYS LOCAL — QG exemption list |
| 34 | `CATALOGUE_KEY_COVERAGE_BASELINE` | target_universe/catalog_engine_coverage.py:180 | Shrinking-ratchet baseline for catalogue-key coverage | test-only | N/A | STAYS LOCAL — QG ratchet baseline |
| 35 | `CARRY_PERP_HEDGE_ETH_VENUES` | target_universe/venue_capabilities.py:41 | Curated ETH-side perp-hedge venue eligibility list for CARRY_STAKED_BASIS/CARRY_BASIS_PERP | 5 | Explicitly imports UAC `VENUE_DATA_TYPE_CAPABILITIES` and layers archetype eligibility on top — confirmed NOT a duplicate, a genuine curation | STAYS LOCAL — archetype eligibility policy on top of UAC data, matches `_ALLOWED_CHAINS` shape exactly (heavily operator-ruling cited) |
| 36 | `CARRY_PERP_HEDGE_SOL_VENUES` | target_universe/venue_capabilities.py:59 | Curated SOL-side perp-hedge venue eligibility list | 4 | Same as #35 | STAYS LOCAL |
| 37 | `_VENUE_ALIAS_TO_CANONICAL` | target_universe/venue_capabilities.py:104 | Bare-venue-name → chain-suffixed-canonical-name alias bridge (currently empty, confirmed dead per its own comment) | 0 live (dead) | N/A | STAYS LOCAL — dead code artifact; flag as a delete-candidate follow-up, not a migration target |
| 38 | `_DERIVATIVE_TICKER_EMBEDS_FUNDING` | target_universe/venue_capabilities.py:132 | Narrow allowlist of DEX-perp venues where funding rides `derivative_ticker` post-UAC-consolidation | 1 | UAC retired the standalone `perp_funding` data_type for these venues (cited commit `unified-api-contracts@49314f51`); this local allowlist is the *consumer-side* adaptation, not a duplicate of that UAC change | STAYS LOCAL — narrow, explicitly-cited eligibility gate, not general reference data |
| 39 | `_LP_CONCENTRATED_POOLS` | target_universe/catalog_yield_defi.py:247 | Top-3 Uniswap V3 pool (slot_token, label, symbol, address) tuples for DEFI_LP_CONCENTRATED | 1 | No UAC pool-address registry found for this specific pool set (UAC has `dex_router_addresses.py` for routers, not LP pool identities) | AMBIGUOUS — pool contract addresses look like reference data in shape, but no confirmed UAC SSOT exists for LP-pool identity; flag for operator (build a UAC LP-pool registry vs. keep local) rather than guess |
| 40 | `_STAKED_BASIS_ETH_LSTS` | target_universe/catalog_staked_basis.py:35 | Curated 3-protocol ETH LST universe for CARRY_STAKED_BASIS | 1 | UAC's `LST_TOKEN_GENESIS`/`LST_VENUE_TO_TOKENS` cover a much larger LST universe (launch dates / venue-to-symbol); this is a small archetype-curated subset, not a duplicate | STAYS LOCAL — curation, confirmed not a literal duplicate of the larger UAC LST registries |
| 41 | `_STAKED_BASIS_SOL_LSTS` | target_universe/catalog_staked_basis.py:42 | Curated 2-protocol SOL LST universe | 1 | Same as #40 | STAYS LOCAL |
| 42 | `_STAKED_BASIS_ETH_SPOT_VENUES` | target_universe/catalog_staked_basis.py:66 | Curated ETH spot-swap venue set (uniswap_v3/curve/binance) for the USDC→native leg | 1 | No UAC equivalent for this archetype-specific spot-venue curation | STAYS LOCAL |
| 43 | `_STAKED_BASIS_SOL_SPOT_VENUES` | target_universe/catalog_staked_basis.py:80 | Curated SOL spot-swap venue set (jupiter/orca/raydium/binance) | 1 | Same | STAYS LOCAL |
| 44 | `_STAKED_BASIS_F_VALUES` | target_universe/catalog_staked_basis.py:92 | Sizing-fraction grid for LST_AS_MARGIN slots (currently just `1.0`) | 1 | No SSOT — sizing policy | STAYS LOCAL |
| 45 | `_STABLE_PREFERENCE` | target_universe/catalog_staked_basis.py:99 | Stablecoin preference order for `start_token` selection (USDC, USDT, FDUSD) | 1 | No UAC stablecoin-preference-order registry found (UAC has peg-history/exit-route data, not preference ordering) | AMBIGUOUS — byte-identical value to #61 (`_STABLECOINS` in staked_basis.py) and near-identical to #63 (`_PERP_MARGIN_STABLE_PREFERENCE`); intra-repo duplication candidate for a shared carry_and_yield module, no external SSOT confirmed |
| 46 | `_STABLE_TO_SHARE_CLASS` | target_universe/catalog_staked_basis.py:100 | Stablecoin symbol → `ShareClass` enum map | 1 | `ShareClass` is UAC-owned but this specific string→enum map is not | STAYS LOCAL — trivial local derivation |
| 47 | `_PERP_MARGIN_STABLE_PREFERENCE` | target_universe/catalog_staked_basis.py:107 | Stable preference order for stables-only perp venues (USDC, USDT) | 1 | Same probe as #45 | AMBIGUOUS — exact duplicate of #63 (`carry_and_yield/staked_basis.py:261`, identical name and value) within the same repo; consolidate to one shared constant regardless of external SSOT |
| 48 | `_CARRY_BASIS_PERP_VENUE_BUNDLES` | target_universe/catalog_carry.py:225 | 11-venue curated CARRY_BASIS_PERP universe (slot token, venue id, share class) | 1 | No UAC equivalent for this specific curated+share-classed bundle | STAYS LOCAL — heavily operator-ruling cited archetype policy (Pacifica reinstatement, Kalshi/Polymarket dates, etc.) |
| 49 | `_CARRY_BASIS_PERP_COINS` | target_universe/catalog_carry.py:266 | Default/fallback 13-coin universe for CARRY_BASIS_PERP when dynamic ranking is off | 1 | No SSOT — explicitly a strategy-policy default list per its own comment | STAYS LOCAL |
| 50 | `_DYNAMIC_CANDIDATE_POOL` | target_universe/catalog_carry.py:299 | Broader ADV-ranking candidate superset (union of #49 + extra coins) | 1 | No SSOT | STAYS LOCAL |
| 51 | `_FUNDING_DISPERSION_VENUES` | target_universe/catalog_carry.py:477 | Curated venue+share-class bundle for CARRY_FUNDING_DISPERSION | 1 | No UAC equivalent for this curation | STAYS LOCAL |
| 52 | `_RECURSIVE_STAKED_LST` | target_universe/catalog_carry.py:656 | LST config for CARRY_RECURSIVE_STAKED (per-chain nested dict) | 1 | No SSOT | STAYS LOCAL |
| 53 | `_RECURSIVE_STAKED_LEND` | target_universe/catalog_carry.py:662 | Lending-protocol config for CARRY_RECURSIVE_STAKED | 1 | No SSOT | STAYS LOCAL |
| 54 | `_VOL_SEEDS` | target_universe/catalog_expansion.py:60 | Archetype→param-seed dict for vol-trading target seeding | 1 | No SSOT — param seeding, not reference data | STAYS LOCAL |
| 55 | `_MM_SEEDS` | target_universe/catalog_expansion.py:194 | Archetype→param-seed dict for market-making seeding | 1 | No SSOT | STAYS LOCAL |
| 56 | `_PORTFOLIO_SEEDS` | target_universe/catalog_expansion.py:236 | Archetype→param-seed dict for portfolio seeding | 1 | No SSOT | STAYS LOCAL |
| 57 | `_PORTFOLIO_BOOKS` | target_universe/catalog_expansion.py:307 | Venue/coin/share-class bundles for portfolio-book archetypes | 1 | No UAC equivalent | STAYS LOCAL |
| 58 | `_UNDERLYINGS` | target_universe/catalog_expansion.py:319 | 3-asset underlying set for component-leg pairing (ETH/BTC/SOL) | 1 | UAC has broader asset universes but not this specific 3-asset archetype seed set | STAYS LOCAL |
| 59 | `_COMPONENT_LEG` | target_universe/catalog_expansion.py:324 | Asset→paired-leg-asset map for cross-asset structures | 1 | No SSOT | STAYS LOCAL |
| 60 | `EXPANSION_ARCHETYPES` | target_universe/catalog_expansion.py:403 | Set of archetypes covered by this expansion module | many | N/A — derived scoping | STAYS LOCAL |
| 61 | `_VALID_OPS` | rules_directional/event_settled.py:44 | Valid comparison-operator strings for event-settled rules | 1 | No SSOT — parser grammar | STAYS LOCAL |
| 62 | `_VALID_MODES` | portfolio/multi_strategy.py:30 | Valid portfolio-combination modes (EQUAL/PNL/SHARPE) | 1 | No SSOT | STAYS LOCAL |
| 63 | `_VENUE_YES_KEYS` | arbitrage_structural/prediction_venue_dispersion.py:97 | Prediction-venue → (yes_bid, yes_ask) feature-key registry | 1 | No UAC equivalent — these are strategy-service's own feature-key naming convention, not a venue-identity fact | STAYS LOCAL |
| 64 | `_SELL_DIRECTION_BY_VENUE` | arbitrage_structural/prediction_venue_dispersion.py:123 | Venue → arbitrage-direction-enum map, 1:1 derived from #63's keys | 1 | N/A — derived | STAYS LOCAL |
| 65 | `_KNOWN_DISPERSION_TYPES` | arbitrage_structural/price_dispersion.py:98 | Valid dispersion-type string enum for this engine | 1 | No SSOT | STAYS LOCAL |
| 66 | `_QUARTER_MONTHS` | carry_and_yield/dated_contract_resolver.py:67 | Quarterly-futures expiry months (3,6,9,12) | 1 | No UTL calendar SSOT found | STAYS LOCAL — small, self-evident calendar fact; not worth a registry for 4 ints, unlike #29/#67's larger duplicate |
| 67 | `_MONTH_ABBREV` (dated_contract_resolver) | carry_and_yield/dated_contract_resolver.py:75 (pre-migration) | Same locale-independent month-abbrev map as #29 | 1 (this file) | Same probe as #29 | ✅ MIGRATED 2026-08-21 — see #29, same commit, this was the second copy. |
| 68 | `_BANNED_LST_PERP_COMBOS` | carry_and_yield/staked_basis.py:174 | Explicit (LST, perp-venue) combos banned for margin-calibration reasons | 1 | No SSOT — defense-in-depth policy list per its own comment | STAYS LOCAL |
| 69 | `_STABLECOINS` | carry_and_yield/staked_basis.py:245 | Stablecoins the strategy can start in (USDC/USDT/FDUSD) | 1 | Same probe as #45 | AMBIGUOUS — same duplicate cluster as #45/#63 (identical value set across 3 files); consolidate locally, no external SSOT confirmed |
| 70 | `_PERP_MARGIN_STABLE_PREFERENCE` (staked_basis.py) | carry_and_yield/staked_basis.py:261 | Stable preference order, byte-identical to #47 | 1 | N/A | AMBIGUOUS — exact duplicate of #47, see #47's note |
| 71 | `_VALID_STATUSES` | migration/legacy_strategy_mapping.py:64 | Valid legacy-strategy-mapping status strings | 1 | No SSOT | STAYS LOCAL |
| 72 | `_REQUIRED_KEYS` | migration/legacy_strategy_mapping.py:91 | Required dataclass field names for `LegacyStrategyMapping` | 1 | N/A — derived from `fields(LegacyStrategyMapping)` | STAYS LOCAL |
| 73 | `_DEFI_ARCHETYPES` (batch_harness, duplicate-name note) | batch_harness.py:61 | See #27 (listed once; grep matched it under the earlier index) | — | — | — |
| 74 | `_ARCHETYPE_ENGINE_SOURCE` (factory, duplicate-name note) | factory.py:29 | See #9 | — | — | — |
| 75 | `SHARE_CLASS_LOWER_TO_ENUM` (duplicate-name note) | slot_label.py:19 | See #22 | — | — | — |

**Rows 73-75 correct a counting artifact**: the raw 76-match grep counted each symbol once; rows 9, 22 and 27
already cover the corresponding file:line. The table above therefore carries **72 distinct constants** (75 grep
matches minus the 3 duplicate index entries at rows 73-75, which exist only so the row-count matches the raw grep
total for auditability). Net: **72 real distinct candidates**, not 69 — see "Count discrepancy" above for why.

## Summary

- **STAYS LOCAL**: 62 constants — overwhelmingly archetype-specific trading policy (which venues/chains/coins/LSTs
  a given archetype is willing to trade, sizing tiers, internal engine wiring, QG ratchet baselines, parser
  grammars) matching the `_ALLOWED_CHAINS` precedent. None of these are duplicated reference data — each was
  checked against the plausible UAC registry by content, not name.
- **AMBIGUOUS**: 8 constants, forming 4 distinct clusters (rows are cross-referenced, not independent
  duplicates of different things) — revised 2026-08-21 after `_MONTH_ABBREV` (cluster 2 below) was reclassified
  MIGRATED, see below:
  1. `_FAMILY_TO_ASSET_GROUP` (#28) — narrow routing-key derivation vs. fold into UAC's asset_group taxonomy.
  2. `_STRIKE_INCREMENT` (#30) — plausible instrument reference data (strike ticks); no confirmed SSOT located.
  3. `_LP_CONCENTRATED_POOLS` (#39) — pool contract addresses; no confirmed UAC LP-pool registry exists.
  4. Stablecoin-preference cluster: `_STABLE_PREFERENCE` (#45) / `_PERP_MARGIN_STABLE_PREFERENCE` × 2 (#47, #70,
     confirmed byte-identical to each other) / `_STABLECOINS` (#69) — near-identical stable-preference lists
     scattered across 3 files, no external SSOT confirmed, real intra-repo dedup opportunity.
- **MIGRATED**: **1 fact, 2 rows** (#29, #67) — `_MONTH_ABBREV`, corrected 2026-08-21 from this doc's original
  AMBIGUOUS verdict. The original reasoning ("no ready SSOT exists yet ... not actionable as MIGRATE") conflated
  "no pre-existing external SSOT" with "no valid destination" — the parent plan's own destination #4 (centralized
  domain module) doesn't require a pre-existing module, only a genuine multi-consumer need within the domain, which
  this constant had (confirmed byte-identical duplicate across 2 resolvers). Migrated to
  `strategy_service/engine/strategies/v2/dated_symbol_conventions.py::MONTH_ABBREV`; both local definitions
  deleted, no shims (both call sites were edited to import from the new module — the private-name re-import
  preserves existing tests' import path, not a compatibility layer). See parent plan Progress Log for the commit.
- **MIGRATE (confirmed-real external SSOT, e.g. UAC)**: **0**, unchanged from the original audit. Every constant
  that looked plausible on name alone (LST lists, venue lists, chain lists) was checked against its real UAC
  counterpart by content and confirmed to be archetype-specific *curation* on top of UAC data, not a duplicate of
  it — the one confirmed literal duplicate against an EXTERNAL SSOT (`_STAKING_PROTOCOL_CHAIN`) was already fixed
  before this audit (parent plan's exemplar todo, `strategy-service@1ea9d0b170`/`8a7f80e8`).

Task 2 ("migrate the unambiguous ones") therefore has **one row acted on** (`_MONTH_ABBREV`, an internal
same-repo duplicate with a single defensible destination) — no candidate here has both an unambiguous destination
AND a confirmed-real, already-existing EXTERNAL SSOT to receive it, which is what the original "0" summary
measured; internal-duplicate migrations are a distinct, smaller category this revision separates out. The
remaining AMBIGUOUS cluster is listed in the parent plan's `[OPERATOR] P1` "Rule on the ambiguous ones" todo for a
ruling.
