---
type: audit
scope: [engineer, admin]
created: 2026-04-24
status: in-progress
---

# Audit: Strategy Config Model, Trade/Position Tagging, and Strategy Versioning

## Purpose

Three core questions driving this audit — all necessary before the UI can
correctly represent the system to operators and clients:

**Q1 — Strategy Config Model**
When a client wants to run a strategy on SPY vs Nasdaq-100 basket vs
"10 stocks with optimized per-instrument params" — how is this handled?
Does each instrument get its own tuned config, or is one config shared?
Where in the system is this decided?

**Q2 — Trade / Position Tagging**
How are orders, fills, and positions differentiated across clients,
accounts, strategies, and strategy versions? Which identifiers flow
through the pipeline? What fields exist at each layer?

**Q3 — Strategy Versioning**
A strategy can have multiple versions (model swap, feature group change,
slot version bump). How does the system track and surface this? How does
the UI show version history? How do different clients get different
versions?

## Scope

Backend: unified-api-contracts (UAC), unified-internal-contracts (UIC),
strategy-service, execution-service, unified-trading-api (the HTTP layer).
Frontend: the UI context folder (canonical schemas snapshot + codex
context copy).
Gap analysis: what the architecture says vs what schemas/routes implement.

---

## Phase 1 — Strategy Config Model

### 1.1 What the architecture says

The v2 architecture has a **5-layer identity model**:

```
1. FAMILY           — 8 orthogonal alpha styles (enum, immutable)
2. ARCHETYPE        — 18 code paths within a family (enum, build-versioned)
3. STRATEGY INSTANCE — slot: archetype + client_id + capital + risk_budget
                       + share_class + slot_label
4. CONFIG           — hash-identified content: venues, instruments, feature/
                       model/policy refs, thresholds, lookbacks, Kelly, risk
                       limits, rebalance cadence, staking method
5. DERIVED CATEGORIES — execution_categories + data_categories (multi-valued
                         lists for UI/reporting, never used for routing)
```

**Key design principle**: Strategy instances are scoped to ONE primary
instrument (or one instrument universe). When a client wants multiple
instruments with optimized configs, they get multiple instances — not one
instance with per-instrument config overrides.

### 1.2 Single-instrument strategies (ML_DIRECTIONAL_CONTINUOUS and most archetypes)

Each instance runs on exactly ONE instrument. Config example:

```yaml
# ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod
model_id: CRYPTO_BTC_CATBOOST_V4
calibration_fn_ref: platt_v2
feature_group_refs:
  - cefi-crypto-candles-5m@v3
  - cefi-crypto-orderbook-depth@v2
timeframe: 5m
confidence_threshold: 0.58
min_edge_threshold: 0.01
kelly_fraction: 0.25
max_position_pct_of_equity: 0.30
venues: [HYPERLIQUID]
```

For a client who wants this strategy on both BTC and ETH:
- `ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod` (BTC, CatBoost BTC model, BTC thresholds)
- `ML_DIRECTIONAL_CONTINUOUS@hyperliquid-eth-5m-usdt-prod` (ETH, separate ETH model, different thresholds)

The Portfolio Allocator then manages capital distribution across these
two instances. This is the correct architecture — each instrument gets
its own backtest-derived config.

**Confirmed in code**: `strategy_service/types.py StrategyConfigDict`
has `instrument_id: str` (singular), confirming one instrument per config.

### 1.3 Multi-instrument basket strategies (STAT_ARB_CROSS_SECTIONAL)

Cross-sectional strategies operate on a UNIVERSE. Config example:

```yaml
# STAT_ARB_CROSS_SECTIONAL@ibkr-russell1000-daily-usd-prod
universe_ref: RUSSELL_1000       # versioned universe artifact
ranking_model_ref: EQUITY_CS_CATBOOST_V3
basket_size_long_pct: 0.10
basket_size_short_pct: 0.10
weighting_scheme: RANK_WEIGHTED
rebalance_cadence: DAILY
max_single_name_pct: 0.02
```

Within one STAT_ARB_CROSS_SECTIONAL instance there is NO per-name
config tuning — the cross-sectional model applies the same ranking
logic to all 1000 members. Position sizing is rank-weighted or
equal-weight, not per-instrument-optimized.

If a client wants Nasdaq-100, create an instance with `universe_ref:
NASDAQ_100`. The cross-sectional model is trained on all 100 names
together and treats them equally.

### 1.4 Per-client overrides (ClientStrategyOverride)

`unified_api_contracts.internal.domain.strategy_service.client_config`
has `ClientStrategyOverride`:

```python
class ClientStrategyOverride(BaseModel):
    client_id: str
    strategy_id: str
    allowed_perp_venues: list[str] | None    # venue restrictions
    allowed_spot_venues: list[str] | None
    multi_coin_rotation: bool = True         # lock to one coin
    dynamic_venue_weighting: bool = True     # use equal weights
    fixed_basis_coin: str | None             # e.g. "ETH" locks coin
    fixed_venue_weights: dict[str, float] | None
    max_leverage: Decimal | None
    max_position_usd: Decimal | None
```

This is **per-client-per-strategy** restriction/tuning — not per-instrument.
It answers "which venues and coins can this client use for this strategy"
but not "what Kelly fraction or threshold applies to this specific instrument".

### 1.5 The "general vs per-instrument config" decision flow

| Client want | System mechanism | How UI shows it |
|-------------|-----------------|-----------------|
| One strategy, one instrument (SPY) | One strategy instance, config tuned to SPY | Single instance card |
| One strategy, N instruments (Nasdaq-100 basket via cross-sectional) | One STAT_ARB_CROSS_SECTIONAL instance with universe_ref | One instance, N=100 implicit in universe |
| One strategy, N single-instrument instances (each with own model/params) | N separate strategy instances, each with own config hash | Portfolio view groups them by archetype + client |
| Restrict to certain venues/coins | ClientStrategyOverride on the strategy_id | Config settings tab per instance |

The system does NOT have a "general config vs per-instrument config" toggle
within a single strategy instance for single-instrument archetypes.
The per-instrument optimization happens at backtest time (Group B), which
outputs different configs per instrument, and each config becomes its own
strategy instance.

### 1.6 Additional per-instance structural dimensions (from strategy-summary.md)

Three axes are **per-instance structural fields**, not config knobs — meaning
a different value for any of them creates a different strategy instance:

#### Share Class (Axis 7)
`share_class` is the accounting currency (USDT, USD, ETH, BTC, GBP, EUR, SOL).
**Fixed at instance creation.** Different share class = different instance.
A client who wants BTC-denominated and USD-denominated versions of the same
strategy gets two separate instances.

Cross-currency policy per instance: `HEDGE_ON_ENTRY` / `HEDGE_ON_EXIT` /
`ACCEPT` / `REBALANCE_PERIODICALLY` — e.g., a USD-share-class strategy on
USDT-margined Binance carries USD↔USDT basis risk managed per this policy.

**Tagging implication**: `share_class` must be on every fill, order, and
position record to correctly attribute P&L. Currently **missing** from all
canonical schemas (gap already noted in Phase 2 table, now confirmed critical).

#### Expression (Axis 5)
How the view is expressed in actual traded instruments:
- Cash-directional: `SPOT`, `PERP`, `DATED_FUTURE`, `MARGIN`
- Options: `ATM_CALL`, `STRADDLE`, `RISK_REVERSAL`, `BUTTERFLY`, `IRON_CONDOR`, etc.
- DeFi: `LP_ACTIVE`, `LEND`, `STAKE_LIQUID`, `LEVERAGED_LENDING_LOOP`, etc.
- Sports: `BET_BACK`, `BET_LAY`, `BET_CLOB_YES/NO`
- Synthetic: `SYNTHETIC_PERP_FROM_OPTIONS`, `BASKET`, `DELTA_HEDGED_OPTION`

**UI implication**: The expression type determines how to render a position
(a `BET_BACK` looks different from a `PERP` looks different from `LP_ACTIVE`).
Currently `CeFiPosition` has `instrument_type` (SPOT/PERP/FUTURE/OPTION) but
**expression** as an axis label is not on any position record.

#### Hold Policy (Axis 6)
| Policy | Meaning | Exit trigger |
|--------|---------|-------------|
| `SAME_CANDLE_EXIT` | In and out within same bar | End of candle |
| `HOLD_UNTIL_FLIP` | Held until signal reverses | Signal flip |
| `CONTINUOUS` | Always-on (MM, LP) | No exit |
| `ONE_SHOT` | Fixed rule unwind | Event/arb settled |
| `EXPIRY_DRIVEN` | Lives until expiry | Options/dated futures |
| `CONVERGENCE_DRIVEN` | Closes when spread converges | Stat Arb, basis arb |
| `REBALANCE_DRIVEN` | Moving target, exits on weight→0 | Cross-sectional, allocator |

**UI implication**: The UI must render position lifecycle differently by
hold policy. A `REBALANCE_DRIVEN` position doesn't have an explicit close
date; an `EXPIRY_DRIVEN` one does. Currently the UI renders all positions
uniformly — no hold_policy field on position records.

#### Topology requirements (from archetype frontmatter)
| Archetype tier | Latency budget | Isolation required |
|----------------|---------------|--------------------|
| Market Making (MM_CONTINUOUS, MM_EVENT_SETTLED) | 40 ms | strategy-service isolated + co-located with execution; premium SLA |
| Most others | 150 ms | standard SLA |
| Rules/Yield | 500 ms | basic SLA |

**UI implication**: Operators deploying an MM strategy need to know it
requires premium infrastructure. The instance creation flow should surface
this.

### 1.7 Gaps and issues in Phase 1

| Gap | Evidence | Impact |
|-----|----------|--------|
| **No per-instrument param overrides schema within a single instance** | No `InstrumentParamsOverride` type exists anywhere in UAC or UIC | For future archetypes that genuinely need it (e.g., vol surface fit per name) |
| **DeFi multi-instrument exception** | `DeFiPositionConfigDict.instruments: list[str]` — DeFi uses list, not single | Inconsistency with single-instrument principle; needs explicit doc |
| **UI has no Portfolio Grouping view** | UI shows individual instances, no "all BTC strategies for client X" group | Hard to see which instruments a client is covered on |
| **No UI for comparing instance configs across instruments** | e.g., "how do BTC threshold differ from ETH threshold for same client?" | Must use raw config viewer |
| **ClientStrategyOverride not surfaced in UI** | No "Client Config Overrides" tab per client per strategy | Operators can't see restrictions per client |
| **Universe artifacts not visible in UI** | `universe_ref: RUSSELL_1000` is just a string; no UI shows universe members | Operators can't see what's in the basket |
| **Config injection system StrategyDomainConfig.strategy_params is flat** | `strategy_params: dict[str, dict]` — one param set per strategy_id | Cannot encode per-instrument params even if needed; would require schema extension |

### 1.7 Recommendations for Phase 1

1. **UI: Portfolio Grouping by (client, archetype)** — show "10 instances of
   ML_DIRECTIONAL_CONTINUOUS for client X" as a group, with instruments as
   children.
2. **UI: ClientStrategyOverride viewer** — per-client settings panel per
   strategy showing venue restrictions, coin locks, leverage caps.
3. **UI: Config diff view** — show "BTC config vs ETH config" for same
   archetype/client.
4. **Backend: Universe registry** — `universe_ref` should be resolvable via
   API (GET /instruments/universe/RUSSELL_1000 → 1000 members). Currently
   the UI context shows no such endpoint.

---

## Phase 2 — Trade / Position Tagging

### 2.1 What the architecture says

Every fill, instruction, and PnL row should carry the full event tag:

```
(
  family,
  archetype_id,
  archetype_build_version,
  strategy_instance_id,     # = slot label
  slot_version,
  config_hash,
  config_version,
  client_id,
  share_class,
  # plus nested per-config refs:
  model_version,
  feature_group_versions[],
  execution_policy_version,
  risk_policy_version
)
```

And venue-account isolation: every venue account is a
`(client_id, venue, account_id)` tuple. PBMS maintains:
- Strategy-instance view: logical positions per strategy_instance_id
- Venue-account view: actual positions at venue, summed across strategies

### 2.2 What is currently implemented at each layer

#### Layer 1: StrategyInstruction (strategy → execution)

`ClientInstruction` in UAC (`unified_api_contracts/instruction.py`):

```python
class ClientInstruction:
    instrument_venue_context: InstrumentVenueContext  # venue, category, instrument_type
    intended_action: InstructionAction
    size_or_target_exposure: SizeOrTargetExposure
    timeframe_urgency: TimeframeUrgency
    order_constraints: OrderConstraints
    strategy_instruction_id: StrategyInstructionId    # client_strategy_id + instruction_id
    lifecycle_replace_cancel: LifecycleReplaceCancel
    risk_and_allocation_constraints: RiskAndAllocationConstraints
    client_id: str | None = None
```

**Present**: `client_strategy_id` (encodes the slot label), `client_id`
**Missing from full event tag**: `family`, `archetype_id`,
`archetype_build_version`, `slot_version`, `config_hash`, `config_version`,
`share_class` — these are referenced in the codex but not in the implemented
`ClientInstruction` schema.

Also: `account_id` is NOT on the instruction — it's resolved by
execution-service via `venue_account_registry.get(client_id, venue)`.
This is architecturally correct (strategy doesn't know accounts), but
means account tagging is added downstream.

#### Layer 2: CanonicalOrder / CanonicalFill (execution canonical)

`CanonicalOrder` in UAC canonical schemas:

```python
class CanonicalOrder:
    order_id: str
    client_order_id: str | None
    timestamp: AwareDatetime
    venue: str
    instrument_id: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    status: OrderStatus
    strategy_id: str | None          # ✅ present
    client_id: str | None            # ✅ present (PII-tagged)
    # account_id: str | None         # ❌ missing
```

`CanonicalFill` same pattern: `strategy_id` ✅, `client_id` ✅, `account_id` ❌.

The full event tag fields (archetype, family, config_hash, etc.) are NOT
present on canonical orders/fills. These schemas carry only `strategy_id`
and `client_id` — a subset of the intended tag.

#### Layer 3: Positions (CeFiPosition)

```python
class CeFiPosition:
    instrument_key: str
    venue: str
    strategy_id: str              # ✅ required
    client_id: str                # ✅ required (PII-tagged)
    account_id: str | None        # ⚠️ optional
    # no family, archetype, config_hash, etc.
```

CeFi positions have the best coverage. DeFi position schemas (defi_lending,
defi_lp, defi_staking) also have `client_id`. Sports schemas have
`account_id` in some cases.

#### Layer 4: Pub/Sub fill events

`FillEventMessage` in UIC (`unified_internal_contracts/pubsub.py`):

```python
class FillEventMessage:
    fill_id: str
    order_id: str
    venue: str
    instrument_id: str
    strategy_id: str | None      # ✅ optional
    client_id: str | None        # ✅ optional (PII)
    # account_id: str | None     # ❌ missing
```

`OrderRequestMessage`: `strategy_id` ✅, `client_id` ✅ required.

#### Layer 5: ManualInstruction (operator manual trades)

In the actual `unified-internal-contracts` repo:

```python
class ManualInstruction:
    instruction_id: str
    submitted_by: str              # OAuth sub claim
    venue: str
    account_id: str                # ✅ required
    instrument_key: str
    side: str
    order_type: str
    quantity: Decimal
    execution_mode: ManualExecutionMode  # EXECUTE | RECORD_ONLY
    client_id: str = ""            # ✅ present (default "")
    strategy_id: str = ""          # ✅ present (default "")
    portfolio_id: str = ""         # ✅ present (default "")
    category: str = ""
    counterparty: str = ""
    source_reference: str = ""
```

**Important**: The UI context snapshot (`context/internal-contracts/...`) is
STALE. It shows an older version of `ManualInstruction` that was MISSING
`client_id`, `strategy_id`, `portfolio_id`, and `execution_mode`. The
actual UIC repo has all these fields. The context folder needs regeneration.

#### Layer 6: Strategy domain events (strategy-service internal)

`PositionSnapshot`, `OrderEvent`, etc. envelopes have `client_name` (a
string, not typed `client_id`), but do NOT have `account_id`. The inner
data objects (`PositionData`, `OrderData`) have `strategy_id` but no
`client_id` or `account_id` at the field level.

#### Layer 7: HTTP API routes (unified-trading-api)

**Filters available**:

| Endpoint | client_id | account_id | strategy_id | family |
|----------|-----------|------------|-------------|--------|
| GET /positions/active | ✅ | ✅ | ✅ | ✅ |
| GET /execution/orders | ✅ | ✅ | ❌ missing | ✅ (strategy_family) |
| GET /execution/fills  | ✅ | ✅ | ❌ missing | ✅ (strategy_family) |
| GET /positions/balances | ✅ | ✅ | — | — |

**Manual order creation** (`POST /execution/orders`):
Body accepts `strategy_id` ✅ but does NOT write `account_id` or `client_id`
to the created order/fill/position records. The mock data generator
creates position records without `account_id` or `client_id`.

### 2.3 Tagging field coverage matrix

| Field | ClientInstruction | CanonicalOrder | CanonicalFill | CeFiPosition | FillEventMessage | ManualInstruction |
|-------|:-:|:-:|:-:|:-:|:-:|:-:|
| client_id | ✅ | ✅ opt | ✅ opt | ✅ req | ✅ opt | ✅ opt |
| account_id | ❌ | ❌ | ❌ | ⚠️ opt | ❌ | ✅ req |
| strategy_id / client_strategy_id | ✅ | ✅ opt | ✅ opt | ✅ req | ✅ opt | ✅ opt |
| family | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| archetype_id | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| archetype_build_version | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| config_hash | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| config_version | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| share_class | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ← per-instance structural field; P&L denominator |
| expression (SPOT/PERP/LP/BET_BACK/…) | ❌ | ❌ | ❌ | ⚠️ instrument_type only | ❌ | ❌ | ← needed for UI rendering |
| hold_policy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ← needed for position lifecycle display |

Legend: ✅ = present, ❌ = missing, ⚠️ = present but optional

### 2.4 Gaps and issues in Phase 2

| Gap | Schema/Layer | Severity | Notes |
|-----|-------------|----------|-------|
| `account_id` missing from `CanonicalOrder` | UAC execution/base.py | High | Needed to attribute fills per venue account |
| `account_id` missing from `CanonicalFill` | UAC execution/base.py | High | Same |
| `account_id` missing from `FillEventMessage` (pub/sub) | UIC pubsub.py | High | pub/sub fill events can't be attributed to account |
| Full event tag (family, archetype, config_hash) missing from canonical schemas | UAC | Medium | Currently only carried in strategy-internal domain events, not in execution layer |
| `GET /execution/orders` missing `strategy_id` filter | API routes | Medium | Can't filter orders by strategy_id |
| `GET /execution/fills` missing `strategy_id` filter | API routes | Medium | Same |
| `POST /execution/orders` doesn't persist `account_id` / `client_id` | API routes + mock | Medium | Manual trades created without full tagging |
| `domain_events.py` envelope uses `client_name: str` not `client_id: str` | UIC strategy_service | Low | Inconsistent typing; `client_name` ≠ `client_id` |
| `OrderData` (strategy monitoring) missing `client_id`, `account_id` | UIC strategy_service | Low | Strategy internal, but used for audit |
| **UI context folder is stale** | UI `context/internal-contracts/` | High | `ManualInstruction` snapshot missing `client_id`, `strategy_id`, `portfolio_id`, `execution_mode` — the actual UIC repo has these. Context needs regeneration. |

### 2.5 How the UI should work for tagging

When an operator places a manual trade:
1. Select `client_id` from dropdown (or auto-filled from auth session)
2. Select `account_id` from that client's registered venue accounts
3. Select `strategy_id` from active strategies on that account (or "MANUAL")
4. Fill `instrument_key`, `side`, `order_type`, `quantity`, `price`
5. Submit → `POST /execution/manual-instruction` with all fields
6. Execution service records `ManualInstruction` → routes to execution or records only

The `ManualInstruction` schema in UIC already supports all these fields.
The gap is in the UI form + the `unified-trading-api` route that handles it.

### 2.6 Recommendations for Phase 2

1. **Add `account_id` to `CanonicalOrder` and `CanonicalFill`** in UAC — this
   is the biggest schema gap. Every fill needs the account it was executed on.
2. **Add `account_id` to `FillEventMessage`** in UIC pubsub.py.
3. **Add `strategy_id` filter to `GET /execution/orders` and `GET /execution/fills`**
   in `unified-trading-api/routes/execution.py`.
4. **Fix `POST /execution/orders`** to write `account_id` and `client_id`
   from the request body into created order, fill, and position records.
5. **Regenerate UI context snapshot** — `unified-trading-system-ui/context/internal-contracts/`
   is stale. The backend team should have a script to regenerate it.
6. **Manual trade UI form** — Add client_id, account_id, strategy_id
   selectors. The backend schema supports them; the form just needs building.
7. **Decide on full event tag in execution layer** — carrying family/archetype/
   config_hash on every fill is expensive but makes audit complete. Minimal
   fix: add them as optional fields to CanonicalOrder/CanonicalFill.

---

## Phase 3 — Strategy Versioning

### 3.1 What the architecture says

Three independent version axes per artifact:

| Axis | Tracks | Versioned by |
|------|--------|-------------|
| Code / Build | Service source + algo code | Git SHA + semver |
| Artifact | Runtime configs, models, rule tables | Content hash + monotonic version |
| Schema | Data format / wire contract | UAC semver |

Strategy configs are artifacts versioned by content hash + monotonic
version per `(slot_label)`.

**Slot version** (`-v2`, `-v3`) is for material dependency changes that
warrant a human-visible distinction:
- Model family swap (CatBoost → XGBoost)
- Feature group major-version bump
- Venue swap

Example:
```
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod     # v1, CatBoost
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod  # XGBoost model
```

Both run in parallel (shadow), compared, and eventually one retires.

**Full archetype event tag** on every fill/instruction:
```
(family, archetype_id, archetype_build_version, strategy_instance_id,
 slot_version, config_hash, config_version, client_id, share_class)
```

### 3.2 What is currently implemented

#### UAC enums (confirmed implemented)

- `StrategyFamily` enum — 8 values ✅ (in `architecture_v2/enums.py`)
- `StrategyArchetype` enum — 18 values ✅
- `ARCHETYPE_TO_FAMILY` mapping ✅
- `AllocatorArchetype` enum (in the same file, not read here but referenced in docs) ✅

v1 `StrategyFamily` (17 values) and v1 `StrategyArchetype` (13 values) were
deleted 2026-04-21. Only v2 enums remain.

#### Strategy Registry (confirmed implemented)

- 96 slot-labelled strategy instances in the registry as of 2026-04-21
- Backed by `archetype_capability_manifest.json`
- `STRATEGY_REGISTRY.resolve_name()`, `.resolve_family()`, `.resolve_category()` ✅
- Slot label grammar enforced: `{archetype_id}@{venue_scope}-{instrument_scope}-{share_class}-{env}` ✅

#### ClientInstruction versioning fields

`StrategyInstructionId.client_strategy_id` encodes the full slot label
(which includes archetype_id + version if applicable). But:
- `archetype_build_version` — NOT on ClientInstruction ❌
- `config_hash` — NOT on ClientInstruction ❌
- `slot_version` — embedded in the slot label string but NOT as a separate typed field ❌

#### Strategy service config

`StrategyConfigDict.strategy_id: str` — carries the slot label.
Config hash is computed per the codex spec but is NOT a first-class field
on `StrategyConfigDict` (it would need to be added).

### 3.3 How different clients get different versions

Mechanism: each client-strategy combination is a SEPARATE strategy instance
with its own slot label and config. Client A and Client B do not share an
instance.

```
Client A (conservative):
  ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod    (v1, CatBoost, kelly=0.25)

Client B (aggressive):
  ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod (XGBoost, kelly=0.5)
```

But: there is no mechanism to say "give client C the v1 config AND
client D the v2 config of the SAME underlying strategy". Currently:
- Different slot labels (v1 vs v2) create different strategy instances
- Clients are assigned to strategy instances at onboarding
- No "version subscription" concept where a client can opt-in to a
  specific config version independently

### 3.4 Gaps and issues in Phase 3

| Gap | Location | Severity | Notes |
|-----|----------|----------|-------|
| Full event tag not carried on ClientInstruction | UAC instruction.py | High | `archetype_build_version`, `config_hash`, `config_version`, `slot_version` missing |
| `config_hash` and `config_version` not in `StrategyConfigDict` | strategy_service/types.py | High | Can't verify config integrity at runtime from the dict alone |
| No UI "strategy version history" view | UI | Medium | Operators can't see "what config version is running, and what changed since v1" |
| No UI "parallel versions comparison" view | UI | Medium | Can't compare v1 vs v2 performance before promoting v2 |
| No "version subscription" API | UAC/UIC | Low | Clients can't opt-in to specific config versions; must be assigned by operators |
| Strategy Registry v2 not fully synced to UI context | UI context | High | Slot labels in UI may reference stale v1 strategy_ids; context regeneration needed |
| No API endpoint for "what changed between config v3 and v4 for this slot" | unified-trading-api | Medium | Config diff is available in deployment-api for domain configs but not strategy-specific configs |

### 3.5 Recommendations for Phase 3

1. **Add `config_hash`, `config_version`, `archetype_build_version` to
   `ClientInstruction`** in UAC — as optional fields initially. This makes
   every instruction self-describing for audit.
2. **Add `config_hash` to `StrategyConfigDict`** in strategy_service — computed
   at config load time, logged, used for audit correlation.
3. **UI: Strategy Instance detail view** — show:
   - slot_label (= strategy_instance_id)
   - family + archetype
   - config_version + config_hash
   - archetype_build_version (strategy-service version that's running this)
   - model artifact refs (model name + version)
   - feature group refs
   - creation date, who created it
4. **UI: Version comparison tab** — for slots with v1/v2 running in parallel,
   show side-by-side config diff and performance metrics.
5. **UI: Config changelog** — show "config version 4 → 5 changed kelly_fraction
   from 0.25 to 0.30, changed confidence_threshold from 0.58 to 0.60".

---

## Summary: Prioritized Gap List

### Critical (blocks correct attribution)

| # | Gap | Location | Fix |
|---|-----|----------|-----|
| 1 | `account_id` missing from `CanonicalOrder` and `CanonicalFill` | UAC execution/base.py | Add optional field |
| 2 | `account_id` missing from `FillEventMessage` (pub/sub) | UIC pubsub.py | Add optional field |
| 3 | UI context snapshot of `ManualInstruction` is stale (missing `client_id`, `strategy_id`, `portfolio_id`) | UI context/ | Regenerate context folder from actual UIC/UAC |
| 4 | `POST /execution/orders` doesn't write `account_id`/`client_id` to created records | unified-trading-api | Fix mock data creation + route body handling |

### High (degrades observability + filtering)

| # | Gap | Location | Fix |
|---|-----|----------|-----|
| 5 | `share_class` missing from `CanonicalOrder`, `CanonicalFill`, `CeFiPosition` | UAC + UIC | Add field; it's a per-instance structural field — critical for P&L denomination |
| 6 | `expression` type missing from position records | UAC/UIC | Add `expression` field so UI knows how to render each position |
| 7 | `hold_policy` missing from position records | UAC/UIC | Add field so UI can show position lifecycle correctly |
| 8 | `GET /execution/orders` and `GET /execution/fills` missing `strategy_id` filter | unified-trading-api | Add query param |
| 6 | Full event tag (archetype, config_hash, slot_version) missing from ClientInstruction | UAC | Add optional fields |
| 7 | Strategy Registry v2 (96 slot labels) may not be reflected in UI strategy dropdowns | UI | Update from new openapi/ui-reference-data.json |

### Medium (UI completeness)

| # | Gap | Location | Fix |
|---|-----|----------|-----|
| 8 | No UI Portfolio Grouping view (N instances of same archetype per client) | UI | New view |
| 9 | No UI ClientStrategyOverride viewer | UI | New config panel |
| 10 | No UI strategy version history / comparison | UI | New tab |
| 11 | Manual trade UI form missing client_id, account_id, strategy_id fields | UI | Form fields |

### Low (technical debt)

| # | Gap | Location | Fix |
|---|-----|----------|-----|
| 12 | `domain_events.py` envelope uses `client_name: str` not typed `client_id` | UIC | Rename + type |
| 13 | `OrderData` missing `client_id`, `account_id` | UIC | Add fields |
| 14 | No per-instrument param override schema (for future needs) | UAC | Design when needed |

---

## Files Read During This Audit

- PM codex: `09-strategy/architecture-v2/README.md` (full 5-layer model)
- PM codex: `06-coding-standards/strategy-identity-versioning.md`
- PM codex: `04-architecture/artifact-versioning.md`
- PM codex: `04-architecture/strategy-execution-protocol.md` (partial)
- PM codex: `09-strategy/architecture-v2/archetypes/ml-directional-continuous.md`
- PM codex: `09-strategy/architecture-v2/archetypes/stat-arb-cross-sectional.md`
- PM codex: `09-strategy/architecture-v2/axes/signal-sources.md`
- PM codex: `09-strategy/architecture-v2/axes/staking-methods.md`
- PM codex: `09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md`
- PM codex: `09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md`
- PM codex: `09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md`
- PM codex: `09-strategy/cross-cutting/client-strategy-config.md`
- PM codex: `09-strategy/strategy-registry-v2.md`
- PM codex: `08-workflows/config-injection.md` (UI context copy)
- UAC: `unified_api_contracts/instruction.py` → `internal/validation/instruction.py`
- UAC: `internal/architecture_v2/enums.py` (StrategyFamily, StrategyArchetype)
- UAC: `canonical/domain/execution/base.py` (CanonicalOrder, CanonicalFill)
- UAC: `canonical/domain/execution/trade.py` (CanonicalAccountState, MarginState)
- UIC actual repo: `unified_internal_contracts/execution.py` (ManualInstruction — richer than snapshot)
- UIC actual repo: `unified_internal_contracts/pubsub.py` (FillEventMessage, OrderRequestMessage)
- UIC actual repo: `unified_internal_contracts/events.py` (LifecycleEventType)
- UIC actual repo: `domain/strategy_service/monitoring.py` (PositionData, OrderData)
- UIC actual repo: `domain/strategy_service/domain_events.py` (event envelopes)
- strategy-service: `types.py` (StrategyConfigDict — single instrument_id)
- strategy-service: `config.py` (service config structure)
- execution-service: `configs/expected_start_dates.yaml` (instrument_overrides)
- API: `unified_trading_api/routes/execution.py` (orders, fills, POST /orders)
- API: `unified_trading_api/routes/positions.py` (active positions)
- UI context: `context/internal-contracts/schemas/positions/cefi.py`
- UI context: `context/internal-contracts/schemas/domain/execution_service/manual_instruction.py` (STALE)
