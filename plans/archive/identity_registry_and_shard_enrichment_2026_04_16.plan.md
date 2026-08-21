---
doc_type: plan
title: identity-registry-and-shard-enrichment
summary: Unified client/account identity, UAC strategy registry SSOT, shard-enriched records across all services and UI,
  SCE mode enforcement
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-16"
type: code
epic: epic-code-completion
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C4, deployment: none, business: none }
  - { repo: unified-trading-library, code: C1, deployment: none, business: none }
  - { repo: strategy-service, code: C4, deployment: none, business: none }
  - { repo: execution-service, code: C4, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C1, deployment: none, business: none }
  - { repo: unified-trading-system-ui, code: C1, deployment: none, business: none }
  - { repo: unified-trading-api, code: C1, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C1, deployment: none, business: none }
depends_on: []
todos:
  - { id: uac-strategy-registry, content: "- [x] [AGENT] P0. UAC: Create StrategyRegistry as SSOT for all 65+ strategies
        (PARALLEL)\n\nDefine in
        `unified_api_contracts/internal/domain/strategy_service/registry.py`:\n\n```python\nclass
        StrategyFamily(StrEnum):\n    BASIS_TRADE = \"BASIS_TRADE\"\n    MOMENTUM = \"MOMENTUM\"\n    MEAN_REVERSION =
        \"MEAN_REVERSION\"\n    MARKET_MAKING = \"MARKET_MAKING\"\n    ARBITRAGE = \"ARBITRAGE\"\n    LENDING =
        \"LENDING\"\n    STAKING = \"STAKING\"\n    LP_PROVISION = \"LP_PROVISION\"\n    OPTIONS_VOL =
        \"OPTIONS_VOL\"\n    SPORTS_VALUE = \"SPORTS_VALUE\"\n    SPORTS_ARB = \"SPORTS_ARB\"\n    PREDICTION =
        \"PREDICTION\"\n    # ... full list from UI strategy-registry.ts\n\nclass
        StrategyArchetype(StrEnum):\n    DIRECTIONAL = \"DIRECTIONAL\"\n    DELTA_NEUTRAL = \"DELTA_NEUTRAL\"\n    YIELD
        = \"YIELD\"\n    RELATIVE_VALUE = \"RELATIVE_VALUE\"\n    QUOTING = \"QUOTING\"\n\n@dataclass\nclass
        StrategyDefinition:\n    strategy_id: str              # CEFI_BTC_momentum-macd_HUF_5M_V1\n\
        \    name: str                     # \"BTC Momentum MACD\"\n    family: StrategyFamily\n    category:
        str                 # CEFI, DEFI, TRADFI, SPORTS, PREDICTION\n    archetype:
        StrategyArchetype\n    allowed_modes: list[str]      # [HUF] for DeFi, [SCE, HUF] for specific
        CeFi\n    asset_group: str\n    default_timeframe: str\n    version: int = 1\n    description: str =
        \"\"\n\nclass StrategyRegistry:\n    \"\"\"SSOT for all strategy definitions. Consumed by backend
        services\n    directly (Python import) and by UI via OpenAPI generation pipeline.\"\"\"\n    _strategies:
        dict[str, StrategyDefinition]\n\n    def get(self, strategy_id: str) -> StrategyDefinition | None\n    def
        get_by_family(self, family: StrategyFamily) -> list[StrategyDefinition]\n    def get_by_category(self, category:
        str) -> list[StrategyDefinition]\n    def resolve_name(self, strategy_id: str) -> str  # for enrichment\n    def
        validate_mode(self, strategy_id: str, mode: str) -> bool\n```\n\nPopulate with all 65+\
        \ strategies from `unified-trading-system-ui/lib/strategy-registry.ts`.\n\n**SCE mode enforcement rules:**\n-
        DEFI category → `allowed_modes = [HUF]` always, no exceptions\n- CEFI/TRADFI → HUF by default; SCE only for
        ML-driven TP/SL strategies\n- SPORTS → HUF always\n- PREDICTION → HUF always\n- Market making (all categories) →
        HUF (reference price model, execution quotes around it)\n\nRe-export from `unified_api_contracts.strategy`
        facade.\n", status: done }
  - { id: uac-account-model, content: "- [x] [AGENT] P0. UAC: Create unified TradingAccount model (PARALLEL)\n\nDefine
        in `unified_api_contracts/internal/domain/account.py`:\n\n```python\n@dataclass\nclass
        TradingAccount:\n    client_id: str          # \"patrick-elysium\"\n    venue: str              # \"BINANCE\",
        \"AAVE_V3-ETHEREUM\"\n    account_label: str      # \"main\", \"sub-1\", \"hedge\", wallet address for
        DeFi\n    account_type: str       # \"CEFI_EXCHANGE\", \"DEFI_WALLET\", \"TRADFI_BROKER\"\n    chain: str |
        None       # \"ETHEREUM\", \"ARBITRUM\" — DeFi only\n    share_class: str | None # \"USDC\", \"ETH\" — links to
        treasury\n    is_active: bool = True\n\n    @property\n    def account_id(self) -> str:\n        \"\"\"Composite
        key: {client_id}:{venue}:{account_label}\"\"\"\n        return
        f\"{self.client_id}:{self.venue}:{self.account_label}\"\n```\n\nAlso define `AccountRegistry` for credential
        routing:\n```python\nclass AccountRegistry:\n    \"\"\"Maps (client_id, venue) →\
        \ list[TradingAccount].\n    Credential resolution uses account_label to select API key set.\"\"\"\n\n    def
        get_accounts(self, client_id: str, venue: str) -> list[TradingAccount]\n    def get_default_account(self,
        client_id: str, venue: str) -> TradingAccount\n    def get_by_id(self, account_id: str) -> TradingAccount |
        None\n```\n\nRe-export from `unified_api_contracts.account` facade.\n", status: done }
  - { id: uac-enrich-schemas, content: "- [x] [AGENT] P0. UAC: Add shard dimensions to CanonicalOrder, CanonicalFill,
        all Position models (PARALLEL)


        **CanonicalOrder** — add to `canonical/domain/execution/base.py`:

        - `strategy_name: str | None` (resolved from StrategyRegistry at write time)

        - `client_name: str | None` (resolved from ClientConfigRegistry)

        - `category: str | None` (CEFI/DEFI/TRADFI — parseable from strategy_id prefix)

        - `strategy_family: str | None` (from StrategyRegistry)

        - `chain: str | None` (for DeFi orders)

        - `account_id: str | None` (composite key from TradingAccount)

        - `share_class: str | None`


        **CanonicalFill** — same additions as CanonicalOrder.


        **CeFi Position** (`internal/positions/cefi.py`):

        - Ensure `account_id` is NOT None-defaulted — make it required where applicable

        - Add `strategy_name`, `client_name`, `category`, `strategy_family`


        **DeFi Positions** (lending, lp, staking):

        - Add `account_id` (wallet address), `client_name`, `strategy_name`, `strategy_family`


        **AggregatedPosition** (`canonical/domain/position/__init__.py`):

        - Add `strategy_name`, `client_name`, `strategy_family`, `category`

        - Already has `strategy_id` and `client_id`


        **PnLAttribution** (`internal/domain/strategy_service/pnl.py`):

        - Add `client_id: str` (make required, not missing)

        - Add `client_name: str | None`

        - Add `account_id: str | None`

        - Add `strategy_name: str | None`


        **RiskMetrics** (`internal/risk.py`):

        - Add `account_id: str | None` for account-level risk

        - Implement ACCOUNT level in aggregation (currently schema-only)


        **AccountState** (`internal/risk.py`):

        - Add `client_id: str` (currently missing — only has venue + account_id)


        **StrategyInstruction** (`internal/domain/strategy_service/instruction.py`):

        - Make `client_id` REQUIRED (not `str | None`)

        - Add `account_id: str | None` for execution routing

        ", status: done }
  - {
      id: uac-client-registry,
      content:
        "- [x] [AGENT] P0. UAC: Create ClientRegistry for name resolution (PARALLEL)\n\nExtend
        `internal/domain/strategy_service/client_config.py`:\n\n```python\n@dataclass\nclass
        ClientDefinition:\n    client_id: str        # \"patrick-elysium\"\n    name: str             #
        \"Patrick\"\n    entity: str           # \"Elysium Capital\"\n    share_classes: list[str]  # [\"USDC\",
        \"ETH\"]\n    is_active: bool = True\n\nclass ClientRegistry:\n    _clients: dict[str,
        ClientDefinition]\n\n    def resolve_name(self, client_id: str) -> str\n    def get_all_active(self) ->
        list[ClientDefinition]\n```\n\nThis is the lookup used when enriching records with `client_name`.\n",
      status: done,
    }
  - {
      id: utl-mode-validation,
      content:
        "- [x] [AGENT] P0. UTL: Cross-validate category × mode in id_conventions.py (SEQUENTIAL after Phase 0)\n\nIn
        `unified_trading_library/utils/id_conventions.py`:\n1. Import `StrategyRegistry` from UAC\n2. In
        `generate_strategy_id()` and `validate_strategy_id()`, add cross-validation:\n   - If category=DEFI and mode=SCE
        → raise ValueError(\"DeFi strategies must use HUF mode\")\n   - If category=SPORTS and mode=SCE → raise
        ValueError\n   - If category=PREDICTION and mode=SCE → raise ValueError\n3. For CeFi/TradFi SCE: check against
        StrategyRegistry.allowed_modes\n\nAlso add `resolve_category(strategy_id: str) -> str` utility that extracts
        category\nfrom the strategy_id prefix (already parseable, just not exposed as a function).\n",
      status: done,
    }
  - { id: utl-record-enricher, content: "- [x] [AGENT] P0. UTL: Create RecordEnricher utility for shard dimension
        resolution (PARALLEL with above)\n\nIn `unified_trading_library/utils/record_enricher.py`:\n\n```python\nclass
        RecordEnricher:\n    \"\"\"Resolves human-readable names and shard dimensions from IDs.\n    Used at write-time
        by execution-service, PBMS, strategy-service.\"\"\"\n\n    def __init__(self, strategy_registry:
        StrategyRegistry, client_registry: ClientRegistry):\n        ...\n\n    def enrich_order(self, order:
        CanonicalOrder) -> CanonicalOrder:\n        \"\"\"Fill strategy_name, client_name, category, strategy_family
        from IDs.\"\"\"\n\n    def enrich_fill(self, fill: CanonicalFill) -> CanonicalFill:\n        \"\"\"Same
        enrichment for fills.\"\"\"\n\n    def enrich_position(self, position: AggregatedPosition) ->
        AggregatedPosition:\n        \"\"\"Same enrichment for positions.\"\"\"\n```\n\nEnrichment happens at WRITE
        TIME, not display time. This ensures GCS/BigQuery\nrecords\
        \ are self-describing and filterable without joins.\n", status: done }
  - { id: strategy-svc-client-keyed, content: "- [x] [AGENT] P1. Strategy-service: Key instructions by (client_id,
        strategy_id) (PARALLEL)\n\n1. **GCS storage path** — change
        from:\n   `strategy_instructions/strategy_id={id}/day={date}/`\n   to:\n   `strategy_instructions/client_id={cid}/strategy_id={id}/day={date}/`\n\n2.
        **Instruction generation** — `client_id` becomes REQUIRED on all StrategyInstruction\n   emissions. Strategy
        engine must know which client it's generating for.\n\n3. **Position queries** — strategy already queries PBMS by
        (client_id, strategy_id) via\n   StrategyPositionClient. This is correct — just needs client_id to be
        non-optional.\n\n4. **Config loading** — strategy loads ClientStrategyOverride for each client,
        generates\n   separate instruction sets per client (different venues, leverage, position limits).\n\n5. **Batch
        handler** — iterate over active clients per strategy, not just strategy alone.\n\n6. **Market making
        strategies** — reference price model:\n   - Strategy\
        \ emits reference_price in instruction\n   - Execution market-makes around it\n   - When strategy updates
        reference_price, execution updates quotes\n   - For options: emit delta_premium per instrument, execution
        computes quotes from underlying delta\n\n7. **Account routing** — instruction carries `account_id` from
        AccountRegistry\n   so execution knows which credential set to use.\n", status: done }
  - { id: exec-svc-account-routing, content: "- [x] [AGENT] P1. Execution-service: Account-aware credential routing
        (PARALLEL)\n\n1. **Credential mapping** — `VenueInitializer` loads credentials keyed by\n   `(client_id, venue,
        account_label)` from Secret Manager, not just venue.\n   Secret naming:
        `{venue}_{client_id}_{account_label}_api_key`\n\n2. **Adapter factory** — `get_order_adapter()` accepts
        `account_id: str` parameter.\n   Cache key includes account_id. Different accounts = different adapter
        instances.\n\n3. **place_order()** — add `account_id: str | None` parameter to BaseOrderAdapter.\n   For venues
        with sub-accounts (Binance, OKX), pass to venue API.\n   For DeFi, account_id = wallet address — already handled
        via config injection.\n\n4. **Record enrichment** — use RecordEnricher at fill-write time to
        stamp\n   strategy_name, client_name, category, strategy_family, chain on CanonicalFill.\n\n5. **Audit log** —
        already captures client_id. Add account_id, strategy_name.\n\n6. **Reference\
        \ pricing for MM** — extend UnderlyingTracker to serve as the\n   strategy→execution reference price channel.
        When strategy instruction carries\n   `reference_price`, execution uses it for quote generation instead of
        market mid.\n\n7. **Options MM pass-through** — for Deribit options, strategy passes delta_premium\n   from
        features-volatility-service (initially Deribit's own greeks). Execution\n   computes option quotes from
        underlying move × delta. Strategy does NOT compute\n   greeks — pricing engine responsibility.\n", status: done }
  - { id: pbms-account-aware, content: "- [x] [AGENT] P1. PBMS: Add account_id to position storage key (PARALLEL)\n\n1.
        **Position key** — change from 4-tuple `(client_id, strategy_id, venue, instrument)`\n   to 5-tuple `(client_id,
        strategy_id, venue, account_id, instrument)`.\n   account_id defaults to \"default\" for backward compat during
        migration.\n\n2. **Position store upsert** — add account_id to filter clause in position_store.py.\n\n3.
        **Position tracker** — carry account_id through fill processing pipeline.\n\n4. **Record enrichment** — use
        RecordEnricher to stamp strategy_name, client_name,\n   category, strategy_family on AggregatedPosition at write
        time.\n\n5. **PnL attribution** — add client_id (required), account_id, strategy_name to\n   PnLAttribution
        records.\n\n6. **Risk aggregation** — implement ACCOUNT level in risk_group_aggregator.\n   RiskMetrics gains
        account_id field. Per-account leverage, margin, drawdown.\n\n7. **Cross-venue aggregator** — ensure account_id
        flows\
        \ through to AggregatedPosition.\n", status: done }
  - {
      id: api-gateway-enriched,
      content:
        "- [x] [AGENT] P1. API gateway: Expose enriched fields and new filter params (SEQUENTIAL after Phase
        1)\n\n**unified-trading-api routes:**\n\n1. `/positions/active` — add query params: `client_id`, `category`,
        `strategy_family`,\n   `account_id`, `chain`. Response includes all enriched fields.\n\n2. `/execution/orders` —
        add query params: `client_id`, `category`, `strategy_family`,\n   `account_id`. Response includes strategy_name,
        client_name, category, chain.\n\n3. `/execution/fills` — same enrichment as orders.\n\n4.
        `/api/analytics/strategies/catalog` — serve from UAC StrategyRegistry\n   (currently unclear source). Return
        families, archetypes, allowed_modes.\n\n5. New: `/accounts` — list accounts per client from
        AccountRegistry.\n   `/accounts/{account_id}/positions` — positions for specific account.\n\n6. `/risk/metrics`
        — add account_id filter. Return per-account risk if requested.\n",
      status: done,
    }
  - { id: ui-strategy-registry-generated, content: "- [x] [AGENT] P1. UI: Replace hand-written strategy-registry.ts with
        generated from UAC (PARALLEL)\n\n1. Add StrategyRegistry export to `generate_ui_reference_data.py` in
        PM.\n   Output goes into `ui-reference-data.json` under `strategy_registry` key.\n\n2. In UI
        `lib/registry/generated.ts`, re-export strategy registry data.\n\n3. Replace `lib/strategy-registry.ts` with
        thin wrapper that imports from generated:\n   ```typescript\n   import { strategyRegistry } from
        \"@/lib/registry/generated\";\n   export const STRATEGIES = strategyRegistry.strategies;\n   export const
        FAMILIES = strategyRegistry.families;\n   export function resolveStrategyName(id: string): string { ...
        }\n   ```\n\n4. Update `hooks/api/use-strategies.ts` — `useStrategyCatalog()` reads from\n   generated registry
        instead of API call (or API serves from same UAC source).\n\n5. Update `lib/types/strategy-platform.ts` to use
        generated strategy types.\n\n6. Verify strategy-family-browser-widget.tsx\
        \ works with new data source.\n", status: done }
  - { id: ui-enriched-tables, content: "- [x] [AGENT] P1. UI: Add shard dimension columns to position/order/fill tables
        (PARALLEL)


        **Positions table** (`components/widgets/positions/positions-table-widget.tsx`):

        - Add columns: Client, Category, Strategy Family, Chain, Account

        - Add filter dropdowns for: client, category, family, chain

        - Ensure PositionRecord type includes all new fields


        **Orders table** (`components/widgets/orders/orders-table-widget.tsx`):

        - Add columns: Client, Category, Strategy Family, Chain, Account

        - Add filter dropdowns matching positions table


        **Trades dashboard** (`components/reports/trades-dashboard.tsx`):

        - Add strategy_id, client, category columns

        - Add export with all shard dimensions


        **Strategy pages** — ensure strategy_family renders from generated registry,

        not from hand-written config.


        **Data contexts** — update PositionRecord, OrderRecord, TradeRecord types

        to include all enriched fields from API responses.

        ", status: done }
  - {
      id: pm-openapi-sync,
      content:
        "- [x] [AGENT] P1. PM: Update OpenAPI generation to include StrategyRegistry + AccountRegistry\n\n1. In
        `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`:\n   - Import StrategyRegistry from UAC\n   -
        Serialize all strategy definitions to JSON under `strategy_registry` key\n   - Include families, archetypes,
        allowed_modes\n   - Import ClientRegistry, serialize active clients (names only, no PII)\n\n2. In
        `unified-trading-pm/scripts/openapi/generate_unified_spec.py`:\n   - Ensure new API endpoints (/accounts,
        enriched /positions, /orders) appear in spec\n\n3. Update `uac-registry-sync.yml` workflow template — trigger
        regeneration\n   when UAC strategy registry changes.\n\n4. Run `generate-unified-openapi.sh` to verify
        end-to-end pipeline.\n",
      status: done,
    }
  - { id: codex-docs, content: "- [x] [AGENT] P2. Codex: Document identity model, strategy registry, SCE rules, MM
        reference price model\n\n1. `/codex/04-architecture/identity-model.md` — client_id, account_id,
        strategy_id\n   relationships. TradingAccount composite key. Credential routing.\n\n2.
        `/codex/09-strategy/_archived_pre_v2/strategy-registry.md` — StrategyRegistry SSOT in UAC,\n   families, archetypes, OpenAPI sync
        pipeline.\n\n3. `/codex/09-strategy/_archived_pre_v2/execution-modes.md` — SCE vs HUF rules:\n   - DeFi/Sports/Prediction → HUF
        always\n   - CeFi/TradFi → HUF default, SCE only for ML TP/SL\n   - Market making → HUF (reference price
        model)\n\n4. `/codex/09-strategy/market-making-reference-price.md` — reference price model:\n   - Strategy emits
        reference_price\n   - Execution quotes around it\n   - Options: delta-premium from pricing engine → strategy →
        execution\n   - Deribit pass-through initially, own pricing engine eventually\n\n5. Update
        `codex/06-coding-standards/` — enrichment-at-write-time rule:\n   \"\
        All records (orders, fills, positions) must carry strategy_name, client_name,\n   category, strategy_family at
        write time. Never resolve at display time.\"\n", status: done }
  - { id: qg-all-repos, content: "- [x] [AGENT] P0. Run quality-gates.sh on all affected repos


        Sequential QG runs:

        1. `cd unified-api-contracts && bash scripts/quality-gates.sh`

        2. `cd unified-trading-library && bash scripts/quality-gates.sh`

        3. `cd strategy-service && bash scripts/quality-gates.sh`

        4. `cd execution-service && bash scripts/quality-gates.sh`

        5. `cd position-balance-monitor-service && bash scripts/quality-gates.sh`

        6. `cd unified-trading-api && bash scripts/quality-gates.sh`

        7. `cd unified-trading-system-ui && CI=true npm test -- --run`

        8. `cd unified-trading-pm && bash scripts/quality-gates.sh`

        ", status: done }
isProject: false
---

# Context

## Problem Statement

The unified trading system has fragmented identity management. Client identity is an optional annotation rather than a
first-class routing dimension. Strategy definitions exist only in the UI (TypeScript). Account identity has no unified
model. Records (orders, fills, positions) lack shard dimensions needed for filtering and attribution.

## Pre-Audit Manifest

### Strategy Registry (UI → UAC migration)

| Source File                                                                                  | What                                  | Action                                 |
| -------------------------------------------------------------------------------------------- | ------------------------------------- | -------------------------------------- |
| `unified-trading-system-ui/lib/strategy-registry.ts`                                         | 65+ hand-written strategy definitions | Source data → migrate to UAC           |
| `unified-trading-system-ui/lib/config/services/strategies.config.ts`                         | ARCHETYPES, asset_group_COLORS        | Keep in UI (display-only config)       |
| `unified-trading-system-ui/hooks/api/use-strategies.ts`                                      | `useStrategyCatalog()` hook           | Update to read from generated registry |
| `unified-trading-system-ui/components/widgets/strategies/strategy-family-browser-widget.tsx` | Family browser                        | Update data source                     |
| `unified-trading-system-ui/lib/types/strategy-platform.ts`                                   | Strategy platform types               | Align with generated types             |

### Account Identity (new, touches these files)

| File                                                             | Current                                               | Action                                   |
| ---------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------- |
| `unified-api-contracts/.../risk.py:184-193`                      | AccountState has (venue, account_id) but no client_id | Add client_id                            |
| `unified-api-contracts/.../cefi.py:29-31`                        | CeFi position has optional account_id                 | Make consistent with new model           |
| `position-balance-monitor-service/.../position_store.py:92-101`  | 4-tuple key, no account_id                            | Add account_id to key                    |
| `position-balance-monitor-service/.../position_tracker.py:46-53` | 4-tuple processing                                    | Add account_id                           |
| `execution-service/.../base_adapter.py:163-199`                  | account_id on queries but not on place_order()        | Add to place_order()                     |
| `execution-service/.../factory.py:282-365`                       | Cache key has api_key but no account_id               | Add account_id to cache key              |
| `execution-service/.../initializer.py:39-85`                     | Credential loading by venue only                      | Key by (client_id, venue, account_label) |

### Schema Enrichment (add fields to these models)

| Model               | File                                                      | Fields to Add                                                                         |
| ------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| CanonicalOrder      | `canonical/domain/execution/base.py:129-152`              | strategy_name, client_name, category, strategy_family, chain, account_id, share_class |
| CanonicalFill       | `canonical/domain/execution/base.py:154-174`              | strategy_name, client_name, category, strategy_family, chain, account_id, share_class |
| AggregatedPosition  | `canonical/domain/position/__init__.py:83-125`            | strategy_name, client_name, strategy_family, category                                 |
| PnLAttribution      | `internal/domain/strategy_service/pnl.py:120-256`         | client_id (required), client_name, account_id, strategy_name                          |
| RiskMetrics         | `internal/risk.py:50-76`                                  | account_id                                                                            |
| AccountState        | `internal/risk.py:184-193`                                | client_id                                                                             |
| StrategyInstruction | `internal/domain/strategy_service/instruction.py:303-306` | client_id required (not optional), account_id                                         |

### SCE Mode Enforcement

| File                                                    | Current                          | Action                             |
| ------------------------------------------------------- | -------------------------------- | ---------------------------------- |
| `unified-trading-library/utils/id_conventions.py:13-14` | CATEGORIES and MODES independent | Add cross-validation               |
| `unified-trading-library/docs/ID_NAMING_CONVENTIONS.md` | Lists DeFi SCE examples          | Remove, document HUF-only for DeFi |

### OpenAPI Sync Pipeline

| File                                                                  | Action                                       |
| --------------------------------------------------------------------- | -------------------------------------------- |
| `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`    | Add StrategyRegistry + ClientRegistry export |
| `unified-trading-pm/scripts/openapi/generate_unified_spec.py`         | Include new API endpoints                    |
| `unified-trading-pm/scripts/workflow-templates/uac-registry-sync.yml` | Trigger on strategy registry changes         |
| `unified-trading-system-ui/lib/registry/generated.ts`                 | Add strategy registry re-exports             |

## Execution DAG

```
Phase 0 (PARALLEL — UAC foundation)
├── uac-strategy-registry
├── uac-account-model
├── uac-enrich-schemas
└── uac-client-registry
    │
    ▼ QG: unified-api-contracts
    │
Phase 0.5 (UTL — depends on UAC)
├── utl-mode-validation
└── utl-record-enricher
    │
    ▼ QG: unified-trading-library
    │
Phase 1 (PARALLEL — service integration)
├── strategy-svc-client-keyed
├── exec-svc-account-routing
└── pbms-account-aware
    │
    ▼ QG: strategy-service, execution-service, PBMS
    │
Phase 1.5 (SEQUENTIAL — API gateway)
└── api-gateway-enriched
    │
    ▼ QG: unified-trading-api
    │
Phase 2 (PARALLEL — UI alignment)
├── ui-strategy-registry-generated
└── ui-enriched-tables
    │
    ▼ QG: unified-trading-system-ui
    │
Phase 3 (PM OpenAPI sync)
└── pm-openapi-sync
    │
Phase 4 (PARALLEL — documentation)
└── codex-docs
    │
Phase 5 (SEQUENTIAL — final QG)
└── qg-all-repos
```

## Market Making Reference Price Architecture

Strategy-to-execution communication for market making:

```
┌─────────────────────────┐     StrategyInstruction      ┌────────────────────────┐
│    Strategy Service      │ ──── reference_price ───────▶│   Execution Service    │
│                          │     delta_premium (options)   │                        │
│  Receives:               │                               │  Quotes around         │
│  - Vol features          │◀── PortfolioView (feedback) ──│  reference price       │
│  - Greeks (pass-through) │                               │  Adjusts on underlying │
│  - Market data           │                               │  delta vs reference    │
└─────────────────────────┘                               └────────────────────────┘
        ▲                                                          ▲
        │                                                          │
  features-volatility-svc                                    Market data feed
  (Deribit greeks initially,                                 (real-time prices)
   own pricing engine later)
```

For options: strategy emits `delta_premium` per instrument. Execution computes option quotes from
`underlying_move × delta`. Strategy does NOT compute greeks — it's a pricing engine responsibility
(features-volatility-service).
