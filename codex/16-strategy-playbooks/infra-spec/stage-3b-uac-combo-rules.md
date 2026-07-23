---
doc_type: codex-ssot
title: Stage 3B — UAC Combo Rules (Dimensions + Blocker Predicates)
summary:
  Declarative spec for the UAC combo registry — 15 orthogonal dimensions (strategy-identity / market-surface /
  phase-maturity / commercial-visibility) plus 22 blocker predicates (BL-1..BL-22, code-cited) and the valid_strategies
  resolution formula (~21,600 candidates → ~130 slots); the schema the Stage 3C derivation engine reads.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [uac, strategy, execution, registry, docspec, defi]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
    /codex/09-strategy/architecture-v2/uac-registry-gaps.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md,
  ]
created: 2026-04-20
authoritative_for:
  [Stage 3B combo-registry dimension model + BL-1..BL-22 blocker predicates + valid-combo resolution formula]
referenced_by:
  [
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
    /codex/14-customer-journeys/shared-core/instruction-schema-fit-and-package-boundaries.md,
    /codex/14-customer-journeys/shared-core/venue-chain-instrument-scope.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Stage 3B — UAC Combo Rules (Dimensions + Blocker Predicates)

> **Purpose.** Declarative rule doc for the UAC combo registry that Stage 3C's derivation engine reads from. Lists every
> building-block dimension the registry carries, every blocker predicate (≥20 rules) with code-level evidence, and the
> valid-combo resolution formula. The eventual UAC PR implements the schema sketched in
> [`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml); this doc is the prose specification that PR
> must satisfy.
>
> **Sources (authoritative):**
>
> - [`_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md) —
>   `lifecycle_phase` is a named dimension orthogonal to `maturity`.
> - [`_ssot-rules/04-dart-commercial-axes.md`](../../14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md) —
>   commercial-path axes.
> - [`_ssot-rules/05-building-block-dimensions.md`](../../14-customer-journeys/_ssot-rules/05-building-block-dimensions.md)
>   — 13 building blocks are the entitlement dimension.
> - [`_ssot-rules/07-data-licensing-boundaries.md`](../../14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md)
>   — data-sensitive blocks carry a licensing-constraint flag.
> - [`_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
>   — `instruction_schema_fit` dimension (signals-only / client-strategy+downstream / full-pipeline).
> - [`_ssot-rules/_source-v1-feedback.md`](../../14-customer-journeys/_ssot-rules/_source-v1-feedback.md) §"On
>   building-block dimensions (rule 05)" + §"On DART commercial model (rule 04)".
> - [`../../09-strategy/architecture-v2/category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md)
>   — 18 archetypes × 4 categories × 8 instrument types matrix with representative slot labels + 10 block-list groups
>   (BL-1..BL-10).
> - [`../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
>   — `lock_state` (4 values) + `maturity` (8 values) semantics.
> - [`../../09-strategy/architecture-v2/uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md) —
>   11 queued UAC additions (the schema here anticipates them).
> - [`../../02-venues/venue-registry-reference.md`](../../02-venues/venue-registry-reference.md) — venue + chain
>   universe.
> - `strategy-service/strategy_service/engine/strategies/v2/**/*.py` — engine code asserts archetype identity
>   ([`base.py:88-96`](#file-citations)) and encodes category/instrument/venue support per archetype (cited inline per
>   blocker predicate below).

---

## 1. Dimension model

The registry is a relational model over **15 orthogonal dimensions**. Each slot in the strategy catalogue corresponds to
exactly one tuple over these dimensions; the derivation engine (Stage 3C) resolves `(path, blocks, tier)` against this
tuple space to produce pricing quotes, demo-restriction profiles, production entitlements, and codex scopes.

The dimensions divide into five groups:

- **Strategy identity** — `strategy_archetype`, `feature_group`, `model_family`, `exec_algo`.
- **Market surface** — `category`, `venue`, `chain`, `instrument_type`.
- **Phase / maturity** — `lifecycle_phase` (rule 03), `maturity`.
- **Commercial / visibility** — `entitlement` (the 13 building blocks from rule 05), `lock_state`, `org_scope`,
  `fund_structure`, `data_license_tier`, `instruction_schema_fit`.

A single dimension may also carry **sub-dimensions** (e.g. a venue pack has sub-scope per venue group; `entitlement` has
sub-scope per block). Sub-scopes are declared alongside the primary dimension in the YAML schema; they are not top-level
axes.

### 1.1 `category`

| Value        | Meaning                                                                | Sub-dimensions             |
| ------------ | ---------------------------------------------------------------------- | -------------------------- |
| `CEFI`       | Centralised crypto: Binance, OKX, Bybit, Hyperliquid (hybrid), Deribit | —                          |
| `TRADFI`     | IBKR meta-broker + CME + ICE                                           | `cross_venue_route: bool`  |
| `DEFI`       | On-chain DEX / lending / staking across 7 chains                       | `chain_scope: list[chain]` |
| `SPORTS`     | Unity (10 child books), Betfair/Smarkets/Matchbook direct              | `lay_side_capable: bool`   |
| `PREDICTION` | Polymarket, Kalshi                                                     | `binary_outcome: bool`     |

**Note on CeFi/DeFi overlap.** Category is derived from the **execution venue**, not from the strategy code. The same
engine (e.g. `ArbitragePriceDispersionEngine` at [`arbitrage_structural/price_dispersion.py:46-48`](#file-citations))
runs against CeFi, DeFi, or Sports venues — only the venue tuple differs. Category is an emergent property of the
`(archetype, venue)` pair, not a strategy attribute.

**v1 source.** The CeFi / TradFi / DeFi / Sports & Prediction split is the conventional 4-category model from v1 agent
feedback; `PREDICTION` is broken out as a first-class category here to mirror the UAC split (`canonical/domain/sports/`
vs `canonical/domain/prediction/` — deferred to Agent A's rule 05 reconciliation).

### 1.2 `venue`

Declared per-venue from [`02-venues/venue-registry-reference.md`](../../02-venues/venue-registry-reference.md):

| Category   | Venues                                                                                                                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI       | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `coinbase` (data-only), `cboe` (ref-data)                                                                                                |
| TRADFI     | `ibkr` (META_BROKER), `cme`, `ice`                                                                                                                                                            |
| DEFI       | see §1.3 (chain × protocol matrix)                                                                                                                                                            |
| SPORTS     | `unity` (META_BROKER: vx, sharpbet, 3et, betdex, matchbook_via_unity, ibcbet, betfair_via_unity, broker5, cf1, cf2), `betfair_direct`, `smarkets_direct`, `matchbook_direct`, `betdaq_direct` |
| PREDICTION | `polymarket`, `kalshi`                                                                                                                                                                        |

Venue carries `venue_type ∈ {SINGLE_VENUE, META_BROKER, DATA_AGGREGATOR}`,
`supported_operations ⊆ {TRADE, SWAP, LEND, BORROW, STAKE, UNSTAKE, QUOTE, TRANSFER, BRIDGE, ATOMIC, CANCEL, TICKS, OHLC, ORDERBOOK, TRADES, FUNDING, LIQUIDATIONS, REFERENCE_DATA}`,
and `supported_instruments ⊆ instrument_type`.

### 1.3 `chain`

DeFi-only. SSOT is UAC `CHAIN_RPC_TEMPLATES` in `registry/capability_declarations/_defi.py`.

| Chain       | Primary DEXes                                | Lending                                    | Staking                     |
| ----------- | -------------------------------------------- | ------------------------------------------ | --------------------------- |
| `ethereum`  | Uniswap V2/V3/V4, Curve, Balancer, SushiSwap | Aave V3, Compound V3, Morpho, Euler, Spark | Lido, Rocket Pool, Ether.fi |
| `arbitrum`  | Uniswap V3, Balancer                         | Aave V3                                    | bridged LSTs                |
| `optimism`  | Uniswap V3, Velodrome                        | Aave V3                                    | —                           |
| `base`      | Uniswap V3, Aerodrome                        | Aave V3, Morpho                            | —                           |
| `polygon`   | Uniswap V3, Curve, Balancer                  | Aave V3                                    | —                           |
| `avalanche` | Joe V2, Uniswap V3                           | Aave V3                                    | —                           |
| `solana`    | Orca CLMM, Raydium                           | Kamino, MarginFi                           | Jito, Marinade              |

### 1.4 `instrument_type`

Eight values, per [`category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md)
§Conventions:

| Value           | Covers                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------- |
| `spot`          | Cash market — crypto spot, equity, FX spot, physical commodity                                             |
| `perp`          | Perpetual future (CEX + DEX perps)                                                                         |
| `dated_future`  | Expiring future — rolling continuous by default (`-dated-` slot) or explicit expiry (`-fixed-{contract}-`) |
| `option`        | Call/put, vanilla or complex (single-venue multi-leg)                                                      |
| `lending`       | Supplied balance on a lending protocol (a-token, c-token, debt token)                                      |
| `staking`       | Staked native asset (LST)                                                                                  |
| `lp`            | AMM liquidity pool position                                                                                |
| `event_settled` | Binary outcome — sports fixture or prediction market                                                       |

Prediction markets are `event_settled` at the instrument axis; the distinction from sports is at the `category` axis.

### 1.5 `strategy_archetype`

Eighteen values from `StrategyArchetype` enum, per
[`strategy-service/strategy_service/engine/strategies/v2/factory.py:45-65`](#file-citations):

```
ML_DIRECTIONAL_CONTINUOUS         ML_DIRECTIONAL_EVENT_SETTLED
RULES_DIRECTIONAL_CONTINUOUS      RULES_DIRECTIONAL_EVENT_SETTLED
CARRY_BASIS_DATED                 CARRY_BASIS_PERP
CARRY_STAKED_BASIS                CARRY_RECURSIVE_STAKED
YIELD_ROTATION_LENDING            YIELD_STAKING_SIMPLE
ARBITRAGE_PRICE_DISPERSION        LIQUIDATION_CAPTURE
STAT_ARB_PAIRS_FIXED              STAT_ARB_CROSS_SECTIONAL
MARKET_MAKING_CONTINUOUS          MARKET_MAKING_EVENT_SETTLED
VOL_TRADING_OPTIONS               EVENT_DRIVEN
```

Each archetype carries `valid_pairs: set[(category, instrument_type)]` and `supported_venues: set[venue]`, derived from
the engine source per archetype (see `category-instrument-coverage.md` §archetype-by-archetype tables).

### 1.6 `feature_group`

Opaque string identifier; a stable contract declared in the UAC `FeatureGroupRegistry`. Rule 10's fit-check must
validate that a signals-only client's instruction surface does **not** reference upstream feature groups (the client
keeps their feature engineering upstream; see [§1.15](#115-instruction_schema_fit)).

Examples: `delta_one`, `cross_sectional_momentum`, `funding_regime`, `onchain_tvl`, `unity_sharpbook`, `iv_surface`.

### 1.7 `model_family`

Opaque string; identifies the ML model family backing an `ML_DIRECTIONAL_*` archetype instance. Examples: `xgboost_1h`,
`lstm_5m`, `poisson_xg`, `logit_eloprobs`. A `model_family` swap on the same slot is a `v{N}` increment per
[`06-coding-standards/strategy-identity-versioning.md`](../../06-coding-standards/strategy-identity-versioning.md).

### 1.8 `exec_algo`

Opaque string; identifies the execution algorithm from execution-service `algo_library/`. Examples: `market`,
`limit_passive`, `leader_hedge`, `twap`, `pov`, `atomic_onchain`, `flash_loan_bundle`, `calendar_spread_combo`.

### 1.9 `entitlement`

The 13 building blocks from
[`_ssot-rules/05-building-block-dimensions.md`](../../14-customer-journeys/_ssot-rules/05-building-block-dimensions.md):

```
1.  reporting_core
2.  regulatory_umbrella_reporting
3.  im_allocator_reporting
4.  strategy_service_entry
5.  instructions_integration           (sub-dim: schema_depth ∈ {minimal, standard, rich})
6.  research_promote_pipeline
7.  execution_layer                    (sub-dim: venue_scope, instrument_scope)
8.  venue_packs                        (sub-dim: venue)
9.  chain_packs                        (sub-dim: chain)
10. instrument_type_packs              (sub-dim: instrument_type)
11. analytics_packs                    (sub-dim: analytic_family)
12. exclusivity_premium                (Tier B only — rule 08)
13. custom_solution_premium            (Tier B only — rule 08)
```

### 1.10 `lock_state`

Four values, per
[`cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md):

| Value                            | Meaning                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `PUBLIC`                         | Visible to any DART trading-platform subscriber (subject to their entitlements) |
| `INVESTMENT_MANAGEMENT_RESERVED` | Odum-internal IM desk only                                                      |
| `CLIENT_EXCLUSIVE`               | Single client's bespoke exclusive (carries `exclusive_client_id`)               |
| `RETIRED`                        | Historical — no new allocations, existing positions wind down                   |

### 1.11 `maturity`

Eight values; forward-moving under the promote-pipeline watchdog, only ops can demote:

```
CODE_NOT_WRITTEN → CODE_WRITTEN → CODE_AUDITED → BACKTESTED →
PAPER_TRADING → PAPER_TRADING_VALIDATED → LIVE_TINY → LIVE_ALLOCATED
```

External-visibility threshold is `maturity ≥ BACKTESTED` for SaaS surfaces; internal sees all maturities including
`CODE_NOT_WRITTEN` placeholders.

### 1.12 `lifecycle_phase`

Three values, **orthogonal to `maturity`** per rule 03 sub-claim (d):

| Value      | Meaning                                                              |
| ---------- | -------------------------------------------------------------------- |
| `research` | User is viewing the slot re-run over historical data                 |
| `paper`    | User is viewing the slot in simulated-fill mode on current live data |
| `live`     | User is viewing the slot on live fills                               |

A `LIVE_ALLOCATED` slot can still be viewed in `research` phase; a `BACKTESTED` slot can be viewed in `paper` phase.
Phase binds the data source of UI components; it does not fork the component tree (rule 03 enforcement).

### 1.13 `org_scope`

Organisation-level scope carried by JWT claims (Stage 3E integration target). Examples: `odum_internal`,
`client:<org_id>`, `prospect:<session_id>`. Used for visibility-slicing and `CLIENT_EXCLUSIVE` enforcement.

### 1.14 `fund_structure`

Two values for IM + Reg Umbrella engagements:

| Value    | Meaning                                   |
| -------- | ----------------------------------------- |
| `POOLED` | Commingled fund (one NAV, many investors) |
| `SMA`    | Separately Managed Account (per-investor) |

Fund structure determines reporting-core sub-surfaces (client-reporting tool surfaces NAV / share-class differently per
structure). Per the memory note dated 2026-04-19, SMA vs Pooled applies to BOTH IM and Reg Umbrella.

### 1.15 `data_license_tier`

Three values. Stage 3B derivation of rule 07 §Enforcement rule #4 ("Data-sensitive blocks get an internal licensing
flag. The block registry (rule 05 + Stage 3B) carries a licensing-constraint flag per block..."). Rule 07 describes the
concept; the specific enum below is this document's projection for the registry.

| Value                | Meaning                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| `retail_ok`          | Data source licence permits unrestricted redistribution (sports public odds, many on-chain)      |
| `institutional_only` | Licence restricts to institutional clients (most CeFi exchange data, IBKR market data)           |
| `odum_proprietary`   | Odum-enriched output (factor exposures, regime tags, synthetic pricing) — always redistributable |

Rule 07's enriched-service framing means `odum_proprietary` is what clients actually pay for; the other two tiers gate
which raw-adjacent surfaces can be shown at all. Tier naming is not prescribed by rule 07 itself and may be adjusted
when Agent A's final rule 07 merges if the rule introduces its own nomenclature — see §6 reconciliation.

### 1.16 `instruction_schema_fit`

Three values per rule 10:

| Value                            | Meaning                                                                                               |
| -------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `signals_only`                   | Client sends instructions matching the rule-10 required-fields schema; Odum operates downstream stack |
| `client_strategy_and_downstream` | Client runs strategy on Odum infra but keeps research upstream; executes via Odum                     |
| `full_pipeline`                  | Full-DART: client uses Odum research/promote + strategy + execution + reporting                       |

Schema depth (`minimal` / `standard` / `rich`) is a sub-dimension of `signals_only` — see rule 10 §"Schema depth as a
pricing dimension".

---

## 2. Valid-combo formula

```
valid_strategies(venue, instrument_type, category) =
  { archetype ∈ StrategyArchetype
      : (category, instrument_type) ∈ archetype.valid_pairs
      ∧ venue ∈ archetype.supported_venues
      ∧ venue.category == category
      ∧ instrument_type ∈ venue.supported_instruments
      ∧ ¬ blocked(archetype, venue, instrument_type, category)
      ∧ data_license_tier_compatible(venue, client.entitlement_scope)
      ∧ (if signals_only: archetype.instruction_schema_fit ⊆ {minimal, standard, rich})
  }
```

Where `blocked(...)` is the disjunction of the BL-1..BL-20 blocker predicates in §3.

**Resolution order (derivation engine):**

1. Expand the Cartesian product `archetype × category × instrument_type × venue` (≈ 18 × 5 × 8 × 30 ≈ 21,600
   candidates).
2. Drop cells where `(category, instrument_type) ∉ archetype.valid_pairs` → ~1,000 surviving.
3. Drop cells where `venue.category ≠ category` OR `instrument_type ∉ venue.supported_instruments` → ~400 surviving.
4. Apply each blocker predicate in §3 → final set ≈ 130 representative slots (per
   [`category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md) changelog).
5. Apply visibility filters: `lock_state × org_scope`, `maturity ≥ BACKTESTED` for SaaS surfaces, etc.

---

## 3. Blocker predicates (≥20)

Each blocker has: name, predicate (pseudo-code), reason category ∈ {licensing, venue-unsupported, regulatory, technical,
commercial}, and file:line evidence. BL-1..BL-10 mirror the block-list groups in
[`category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md) §"Block list
(BL-1..BL-10)"; BL-11..BL-20 are new Stage 3B additions covering commercial, visibility, and instruction-schema-fit
conditions that the derivation engine enforces.

### BL-1: No supported DeFi options venue

- **Predicate:** `category == DEFI ∧ instrument_type == option`
- **Reason:** venue-unsupported
- **Archetypes affected:** `ML_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_CONTINUOUS`, `ARBITRAGE_PRICE_DISPERSION`,
  `MARKET_MAKING_CONTINUOUS`, `VOL_TRADING_OPTIONS`.
- **Evidence:**
  [`category-instrument-coverage.md:1192-1205`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "Lyra and Dopex were archived 2026-03. No replacement DeFi options venue is currently declared." Engine file
  [`vol_trading/options.py:41-43`](#file-citations) declares `ARCHETYPE = VOL_TRADING_OPTIONS` with no DeFi venue
  registration in `factory.py`.

### BL-2: No DeFi dated-future venue

- **Predicate:** `category == DEFI ∧ instrument_type == dated_future`
- **Reason:** venue-unsupported
- **Archetypes affected:** `ML_DIRECTIONAL_CONTINUOUS`, `CARRY_BASIS_DATED`.
- **Evidence:**
  [`category-instrument-coverage.md:1206-1213`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "Deribit is CeFi. No on-chain dated-future venue currently supported."
  [`carry_and_yield/basis_dated.py:47-49`](#file-citations) declares `CARRY_BASIS_DATED` — the archetype is
  DEX-venue-agnostic but no DEX venue exposes dated futures.

### BL-3: CeFi lending out-of-scope

- **Predicate:** `archetype == YIELD_ROTATION_LENDING ∧ category == CEFI`
- **Reason:** commercial (deliberate product-scope exclusion)
- **Evidence:**
  [`category-instrument-coverage.md:1215-1221`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "CeFi lending products (Binance Earn, Bybit) have withdrawal lockups + counterparty risk; deliberately out-of-scope."
  Also [`carry_and_yield/rotation_lending.py:52-54`](#file-citations) declares the archetype;
  [`rotation_lending.py:114-153`](#file-citations) assumes `needs_bridge` / `bridge_hint` semantics — both are DeFi-only
  cross-chain concepts.

### BL-4: CeFi / TradFi directional options via rules (non-standard)

- **Predicate:** `archetype == RULES_DIRECTIONAL_CONTINUOUS ∧ instrument_type == option`
- **Reason:** technical (degenerate signal — use `VOL_TRADING_OPTIONS` or `ML_DIRECTIONAL_CONTINUOUS` with
  expression=`atm_call` instead)
- **Evidence:**
  [`category-instrument-coverage.md:1223-1231`](../../09-strategy/architecture-v2/category-instrument-coverage.md).
  [`rules_directional/continuous.py:36-38`](#file-citations) — engine code does not accept `option` in `valid_pairs`.

### BL-5: Kalshi execution adapter pending

- **Predicate:** `venue == kalshi ∧ supported_operation(TRADE) == false`
- **Reason:** technical (adapter work in progress)
- **Archetypes affected:** `ML_DIRECTIONAL_EVENT_SETTLED`, `RULES_DIRECTIONAL_EVENT_SETTLED`,
  `MARKET_MAKING_EVENT_SETTLED`.
- **Evidence:**
  [`category-instrument-coverage.md:1233-1241`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "Data + pricing live; execution adapter not built." Venue registry at
  [`02-venues/venue-registry-reference.md`](../../02-venues/venue-registry-reference.md) does not list Kalshi under
  execution venues.

### BL-6: Unity cannot quote (Feed Connector is place-only)

- **Predicate:** `venue == unity ∧ archetype == MARKET_MAKING_EVENT_SETTLED`
- **Reason:** venue-unsupported (venue exposes PLACE/CANCEL only; no quoting API)
- **Evidence:**
  [`category-instrument-coverage.md:1243-1250`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "Unity's Java Feed Connector accepts PLACE_BET / CANCEL but does not expose a quoting API. Unity child books quote
  internally; we cannot add our own bids/offers through Unity." Market-making event-settled engine at
  [`market_making/event_settled.py:55-139`](#file-citations) emits `QuoteInstruction`s with BET_BACK and BET_LAY sides;
  Unity adapter rejects `QuoteInstruction`.

### BL-7: DeFi perp MM not exposed as third-party role

- **Predicate:** `archetype == MARKET_MAKING_CONTINUOUS ∧ category == DEFI ∧ instrument_type == perp`
- **Reason:** venue-unsupported (protocol-level MM incentives only; no CLOB MM role)
- **Evidence:**
  [`category-instrument-coverage.md:1252-1258`](../../09-strategy/architecture-v2/category-instrument-coverage.md).
  [`market_making/continuous.py:38-40`](#file-citations) declares `MARKET_MAKING_CONTINUOUS` — no DeFi perp venue
  registered in supported_venues for this archetype.

### BL-8: DeFi cross-sectional basket (multi-leg gas efficiency)

- **Predicate:** `archetype == STAT_ARB_CROSS_SECTIONAL ∧ category == DEFI ∧ instrument_type == spot`
- **Reason:** technical (atomic multi-token basket on EVM is gas-prohibitive; no specialised router declared)
- **Evidence:**
  [`category-instrument-coverage.md:1260-1267`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "Atomic multi-token basket trade on DeFi is gas-prohibitive on EVM; requires specialised router (1inch Pathfinder
  style) not currently declared." [`stat_arb_pairs/cross_sectional.py:48-50`](#file-citations) declares
  `STAT_ARB_CROSS_SECTIONAL`.

### BL-9: TradFi cross-sectional on futures basket

- **Predicate:** `archetype == STAT_ARB_CROSS_SECTIONAL ∧ category == TRADFI ∧ instrument_type == dated_future`
- **Reason:** technical (multi-leg batch-order capability not declared for CME adapter)
- **Evidence:**
  [`category-instrument-coverage.md:1269-1275`](../../09-strategy/architecture-v2/category-instrument-coverage.md). UAC
  gap #7 (`MultiLegOrderCapability.max_legs`) covers this.

### BL-10: Dated-future auto-roll + combo creation not yet live

- **Predicate:**
  `instrument_type == dated_future ∧ slot_label matches -dated- ∧ representative_future_service == not_deployed`
- **Reason:** technical (representative-future-service + FUTURES_ROLL ATOMIC mode not yet built)
- **Archetypes affected:** all archetypes with `-dated-` slots per
  [`category-instrument-coverage.md:1277-1298`](../../09-strategy/architecture-v2/category-instrument-coverage.md).
- **Mitigation:** `-fixed-{contract}-` slot labels are launchable; ops rotate manually until the roll service ships.
- **UAC gap:** #11 (`RepresentativeFutureRegistry` + `REPRESENTATIVE_FUTURE_CHANGED` event).

### BL-11: Signals-only clients cannot access research/promote pipeline

- **Predicate:** `instruction_schema_fit == signals_only ∧ entitlement.includes(research_promote_pipeline)`
- **Reason:** commercial (rule 10 enforcement: block 6 excluded by default from signals-only package)
- **Evidence:**
  [`_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
  §"Package boundaries" — "Research / promote pipeline (block 6). Signals-only clients do not automatically get
  research, backtest, paper, or promotion capabilities." Derivation-engine rejection surfaces "upgrade to full-DART
  pricing" prompt per rule 10 §"Commercial quote enforcement".

### BL-12: Rule-07 licensed raw data cannot be surfaced to external clients

- **Predicate:** `data_license_tier == institutional_only ∧ view_surface == public_marketing`
- **Reason:** licensing (rule 07 boundary)
- **Evidence:**
  [`_ssot-rules/07-data-licensing-boundaries.md`](../../14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md)
  §"Enforcement rules" #1–#5 — "Line items never reference raw data", "No 'Tier A raw data' combinations".
  Derivation-engine logs rule-07 breach to compliance per rule 07 §#6.

### BL-13: Demo mode locks research/promote for `(Client, downstream)` prospects

- **Predicate:** `demo_mode == true ∧ commercial_path == client_downstream ∧ block ∈ {research_promote_pipeline}`
- **Reason:** visibility (demo-ops LOCKED-VISIBLE profile per rule 06 × rule 10)
- **Evidence:**
  [`_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
  §"Interaction with the same-system principle" — "The client does **not** see the research / promote /
  strategy-authoring surfaces (rule 06 LOCKED-VISIBLE)". Enforced via demo-restriction-profile in Stage 2
  `demo-ops/demo-restriction-profiles.md`.

### BL-14: `CLIENT_EXCLUSIVE` slots invisible outside `exclusive_client_id`

- **Predicate:**
  `slot.lock_state == CLIENT_EXCLUSIVE ∧ viewer.org_scope ≠ slot.exclusive_client_id ∧ viewer.org_scope ≠ odum_internal`
- **Reason:** visibility (exclusivity premium enforcement — block 12)
- **Evidence:** `StrategyAvailabilityEntry.lock_state == CLIENT_EXCLUSIVE` semantics in
  [`cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md).
  `strategy-service/strategy_service/availability/` store enforces `exclusive_client_id` validator per Phase 10.5
  backend commit (strategy-service `7e0b6a4`).

### BL-15: `RETIRED` slots take no new allocations

- **Predicate:** `slot.lock_state == RETIRED ∧ action == new_allocation`
- **Reason:** commercial (strategy retired; no capital should flow in)
- **Evidence:** `LockState.RETIRED` semantics — "Historical — no new allocations, existing positions wind down."
  Allocator gate `ClientAllocatorInstance.run()` raises per-slot rejection when `lock_state == RETIRED`
  (strategy-service Phase 10.5 commit `7e0b6a4`).

### BL-16: External visibility requires `maturity ≥ BACKTESTED`

- **Predicate:**
  `view_surface ∈ {saas_subscriber, im_client, reg_umbrella_client} ∧ slot.maturity ∈ {CODE_NOT_WRITTEN, CODE_WRITTEN, CODE_AUDITED}`
- **Reason:** visibility (placeholder slots not yet audited externally)
- **Evidence:** `strategy-service` Phase 10.5 plan commit (PM `7aa56b8d`, memory note "Strategy Architecture v2 —
  finalization through Phase 8 ALL GREEN"). External-visibility threshold captured as `maturity ≥ BACKTESTED`. Internal
  surfaces (`odum_internal` org scope) see all maturities.

### BL-17: `LIVE_TINY` maturity caps allocation size

- **Predicate:** `slot.maturity == LIVE_TINY ∧ allocation.target_notional > LIVE_TINY_CAP`
- **Reason:** risk (shadow deployment validator per
  [`shadow-deployment-pattern.md`](../../04-architecture/shadow-deployment-pattern.md))
- **Evidence:** `ShadowDeploymentPolicy.evaluate_shadow_deployment` in
  [`strategy_service/engine/strategies/v2/shadow_deployment.py:213-285`](#file-citations) — "LIVE_TINY → LIVE_ALLOCATED
  promotion on first non-zero AllocationDirective."

### BL-18: Rule-10 minimal-schema required fields must be present

- **Predicate:** `instruction_schema_fit == signals_only ∧ ¬ all_required_fields_present(client.schema)`
- **Reason:** technical (instruction schema contract — rule 10 §"What Odum execution needs")
- **Evidence:**
  [`_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
  §"What Odum execution needs" — eight required fields (instrument+venue, action, size/exposure, timeframe/urgency,
  order constraints, strategy id, lifecycle behavior, essential risk+allocation constraints). Absence ⇒ engagement is
  either full-DART or bespoke, not signals-only.

### BL-19: Tier-A raw-data framing forbidden (any upstream tier)

- **Predicate:** `entitlement.tier == TIER_A ∧ framing == raw_data_feed`
- **Reason:** licensing (rule 07 × rule 08 joint violation)
- **Evidence:**
  [`_ssot-rules/07-data-licensing-boundaries.md`](../../14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md)
  §"Enforcement rules" #5 — "No 'Tier A raw data' combinations. If a Tier A quote line reads as a raw-data pass-through,
  it's a joint rule-07 and rule-08 violation. Rewrite." Note: rule 07 §#5 does NOT condition on the upstream
  `data_license_tier`; raw-data framing on a Tier A line is forbidden regardless of whether the underlying licence
  permits redistribution. The `odum_proprietary` enriched surface is still sellable on Tier A — the predicate only fires
  when the FRAMING reads as raw-data pass-through.

### BL-20: Cross-chain bridge hedge breaks LEADER_HEDGE deadline

- **Predicate:**
  `archetype == CARRY_BASIS_PERP ∧ category == DEFI ∧ leg_1.chain ≠ leg_2.chain ∧ max_hedge_delay_ms < BRIDGE_LATENCY_P99`
- **Reason:** technical (bridge latency exceeds hedge deadline; PARTIAL status per matrix)
- **Evidence:**
  [`category-instrument-coverage.md:538-539`](../../09-strategy/architecture-v2/category-instrument-coverage.md) —
  "Bridge latency breaks LEADER_HEDGE deadline — needs longer `max_hedge_delay_ms` config + bridge state machine
  integration."

### BL-21: Fund-structure mismatch between slot and allocator

- **Predicate:** `slot.fund_structure ≠ allocator.fund_structure ∧ allocator.fund_structure ∈ {POOLED, SMA}`
- **Reason:** commercial / reporting (SMA vs Pooled share-class wiring differs; slots cannot be migrated mid-lifecycle)
- **Evidence:** [`_source-v1-feedback.md`](../../14-customer-journeys/_ssot-rules/_source-v1-feedback.md) + memory note
  2026-04-19 "Playbook SSOT shipped" — "SMA vs Pooled structural decision applies to both IM + Reg Umbrella."

### BL-22: Org-scope mismatch on `CLIENT_EXCLUSIVE` allocation

- **Predicate:** `slot.lock_state == CLIENT_EXCLUSIVE ∧ allocator.org_scope ≠ slot.exclusive_client_id`
- **Reason:** visibility + commercial (allocator cannot flow capital to an exclusive not theirs)
- **Evidence:** `validate_allocation_authorised(saas|im_desk|admin)` in UAC `strategy_availability/` + allocator gate in
  strategy-service Phase 10.5.

---

## 4. Dimension × blocker matrix

| Blocker | Primary dimension tripped                  | Resolvable by UAC addition?                           |
| ------- | ------------------------------------------ | ----------------------------------------------------- |
| BL-1    | `category`, `instrument_type`, `venue`     | No (no DeFi options venue exists)                     |
| BL-2    | `category`, `instrument_type`              | No (no on-chain dated-future venue exists)            |
| BL-3    | `archetype`, `category`                    | No (product-scope decision)                           |
| BL-4    | `archetype`, `instrument_type`             | No (modelling decision)                               |
| BL-5    | `venue`                                    | Yes (Kalshi adapter PR)                               |
| BL-6    | `venue`, `archetype`                       | No (Unity API limitation)                             |
| BL-7    | `archetype`, `category`, `instrument_type` | No (venue architecture)                               |
| BL-8    | `archetype`, `category`, `exec_algo`       | Yes (1inch Pathfinder adapter)                        |
| BL-9    | `archetype`, `category`, `exec_algo`       | Yes (UAC gap #7 — `MultiLegOrderCapability.max_legs`) |
| BL-10   | `instrument_type`, `exec_algo`             | Yes (UAC gap #11 — `RepresentativeFutureRegistry`)    |
| BL-11   | `instruction_schema_fit`, `entitlement`    | No (rule 10 enforcement)                              |
| BL-12   | `data_license_tier`                        | No (rule 07 enforcement)                              |
| BL-13   | `lifecycle_phase`, `entitlement`           | No (rule 06 × 10)                                     |
| BL-14   | `lock_state`, `org_scope`                  | No (exclusivity enforcement)                          |
| BL-15   | `lock_state`                               | No (retired slot)                                     |
| BL-16   | `maturity`, `org_scope`                    | No (external readiness threshold)                     |
| BL-17   | `maturity`                                 | No (risk cap)                                         |
| BL-18   | `instruction_schema_fit`                   | No (rule 10 required fields)                          |
| BL-19   | `entitlement.tier`, `framing`              | No (rule 07 × 08)                                     |
| BL-20   | `chain`, `exec_algo`                       | Yes (bridge state machine)                            |
| BL-21   | `fund_structure`                           | No (structural mismatch)                              |
| BL-22   | `lock_state`, `org_scope`                  | No (entitlement mismatch)                             |

---

## 5. How Stage 3C consumes this registry

Stage 3C's derivation engine (one-registry-four-derivations) reads this schema and produces:

1. **`pricing_quote(commercial_path, blocks, tier)`** — line items per building block per tier (rule 08 shape). Any
   BL-11, BL-19 hit rewrites the quote or rejects it.
2. **`demo_universe(prospect_profile)`** — visibility-sliced catalogue for a demo session. BL-13 + BL-14 + BL-16 govern
   which slots show.
3. **`prod_restrictions(client_contract)`** — production entitlements. BL-14 + BL-15 + BL-17 + BL-22 enforce runtime
   allocation decisions.
4. **`codex_scope(audience)`** — codex-documentation surface per audience (internal vs public). Rule 07 + BL-12 enforce
   the enriched-service framing externally.

Each derivation is a pure function of `(registry_read, input_context)`; no side-state. This is what makes the registry a
true SSOT — the four artefacts (quote, demo, prod, codex) derive from one read with no drift.

---

## 6. Reconciliation pass (vs Agent A's merged rules 05 / 07 / 10)

Reconciliation pass completed 2026-04-20 against the merged `_ssot-rules/05-building-block-dimensions.md`,
`_ssot-rules/07-data-licensing-boundaries.md`, and `_ssot-rules/10-strategy-instruction-schema-principles.md`.

### Verified (no change needed)

- **Rule 05** — 13 building blocks (§1.9 of this doc) match rule 05 §"The thirteen blocks" verbatim. Sub-scoping per
  rule 05 §"Sub-scoping within a block" — venue / chain / instrument-type / analytic-family — matches YAML
  `entitlement.sub_scope`. §"Composition rules" → `(Client, downstream) → signals-only DART` typical-blocks list
  confirms BL-11's exclusion of block 6 from signals-only.
- **Rule 07** — §"Cross-client aggregates" cited in downstream-analytics matrix #12 ✓. §"Enforcement rules" #1–#6
  underpin BL-12 / BL-19 reasoning. §Enforcement rule #4 ("licensing-constraint flag per block") is the authoritative
  source for §1.15.
- **Rule 10** — 8 required fields (§2 of
  [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md)) match rule 10 §"What Odum
  execution needs" 1:1. §"What Odum does NOT need" 4-item list matches instruction-schema-contract §1. §"Package
  boundaries" included/excluded block lists match §7 of that doc. §"Schema depth as a pricing dimension" (minimal /
  standard / rich) matches YAML `schema_depth` sub-dim. §"Pre-demo fit-check discipline" cited accurately in §7.1 of
  instruction-schema-contract. §"Interaction with the same-system principle" supports BL-13.

### Resolved in this reconciliation pass

- **BL-19 predicate narrowed fix.** Initial predicate
  `entitlement.tier == TIER_A ∧ block.data_license_tier == institutional_only ∧ framing == raw_data_feed` was
  over-narrow — rule 07 §#5 forbids Tier A raw-data framing _regardless_ of upstream tier. Predicate corrected to
  `entitlement.tier == TIER_A ∧ framing == raw_data_feed` in both §3 of this doc and
  [`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml) BL-19 block. Dimension × blocker matrix row for
  BL-19 (§4) updated accordingly.
- **§1.15 `data_license_tier` labelling clarified.** Rule 07 mandates a "licensing-constraint flag per block"
  (§Enforcement rule #4) but does not prescribe a specific enum. Reworded §1.15 to mark the three-tier enum (`retail_ok`
  / `institutional_only` / `odum_proprietary`) as a Stage 3B derivation of that flag, not a rule-07 verbatim.

### Watch-for (future rule-text changes)

- **Rule 10 required-fields list.** If Agent A later expands or renames the 8 fields in rule 10 §"What Odum execution
  needs", update: (a) BL-18 predicate in both §3 of this doc and YAML, (b)
  [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md) §2 YAML field blocks + §4
  unsupported-shapes error codes.
- **Rule 07 licensing-flag nomenclature.** If rule 07 later introduces its own tier vocabulary (different names or a
  2-tier vs 3-tier split), align §1.15 of this doc, YAML `dimensions.data_license_tier.values`, and all BL-12 / BL-19
  citations.
- **Rule 05 block renumbering.** Unlikely — rule 05 §"Enforcement rules" #5 ("No silent block splits") explicitly guards
  against this — but if it happens the YAML `entitlement.block_id` enum values need re-keying across the whole registry.

---

## 7. File citations

Paths relative to workspace root `/Users/ikennaigboaka/Code/unified-trading-system-repos/`.

| Citation                                            | Path                                                                                                 | Lines                                   |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `base.py:88-96`                                     | `strategy-service/strategy_service/engine/strategies/v2/base.py`                                     | 88–96 (archetype/family identity guard) |
| `factory.py:45-65`                                  | `strategy-service/strategy_service/engine/strategies/v2/factory.py`                                  | 45–65 (`ARCHETYPE_ENGINE_REGISTRY`)     |
| `arbitrage_structural/price_dispersion.py:46-48`    | `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`    | 46–48                                   |
| `carry_and_yield/basis_dated.py:47-49`              | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/basis_dated.py`              | 47–49                                   |
| `carry_and_yield/basis_perp.py:41-43`               | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/basis_perp.py`               | 41–43                                   |
| `carry_and_yield/rotation_lending.py:52-54`         | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/rotation_lending.py`         | 52–54                                   |
| `carry_and_yield/rotation_lending.py:114-153`       | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/rotation_lending.py`         | 114–153 (bridge-hint semantics)         |
| `market_making/continuous.py:38-40`                 | `strategy-service/strategy_service/engine/strategies/v2/market_making/continuous.py`                 | 38–40                                   |
| `market_making/event_settled.py:55-139`             | `strategy-service/strategy_service/engine/strategies/v2/market_making/event_settled.py`              | 55–139                                  |
| `stat_arb_pairs/cross_sectional.py:48-50`           | `strategy-service/strategy_service/engine/strategies/v2/stat_arb_pairs/cross_sectional.py`           | 48–50                                   |
| `stat_arb_pairs/pairs_fixed.py:53-55`               | `strategy-service/strategy_service/engine/strategies/v2/stat_arb_pairs/pairs_fixed.py`               | 53–55                                   |
| `rules_directional/continuous.py:36-38`             | `strategy-service/strategy_service/engine/strategies/v2/rules_directional/continuous.py`             | 36–38                                   |
| `rules_directional/event_settled.py:47-49`          | `strategy-service/strategy_service/engine/strategies/v2/rules_directional/event_settled.py`          | 47–49                                   |
| `ml_directional/continuous.py:50-61`                | `strategy-service/strategy_service/engine/strategies/v2/ml_directional/continuous.py`                | 50–61                                   |
| `ml_directional/event_settled.py:48-50`             | `strategy-service/strategy_service/engine/strategies/v2/ml_directional/event_settled.py`             | 48–50                                   |
| `vol_trading/options.py:41-43`                      | `strategy-service/strategy_service/engine/strategies/v2/vol_trading/options.py`                      | 41–43                                   |
| `event_driven/event_driven.py:43-45`                | `strategy-service/strategy_service/engine/strategies/v2/event_driven/event_driven.py`                | 43–45                                   |
| `arbitrage_structural/liquidation_capture.py:64-66` | `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/liquidation_capture.py` | 64–66                                   |
| `carry_and_yield/recursive_staked.py:125-127`       | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py`         | 125–127                                 |
| `carry_and_yield/staked_basis.py:174-176`           | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`             | 174–176                                 |
| `carry_and_yield/staking_simple.py:45-47`           | `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staking_simple.py`           | 45–47                                   |
| `shadow_deployment.py:213-285`                      | `strategy-service/strategy_service/engine/strategies/v2/shadow_deployment.py`                        | 213–285                                 |
