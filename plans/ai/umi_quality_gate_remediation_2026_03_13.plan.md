# UMI Quality Gate Remediation Plan — No Exclusions, Proper Fixes

**Status:** AI-generated draft — awaiting user review and promotion to `plans/active/` **Date:** 2026-03-13 **Scope:**
unified-market-interface (UMI) **Context:** User requested removal of quality-gate exclusions and proper fixes for all
violations. No shortcuts or fallbacks.

---

## Executive Summary

UMI has 5 codex compliance violations that were previously bypassed via exclusion arrays in `scripts/quality-gates.sh`.
This plan documents each violation category in detail, with concrete examples, proper fix patterns, and a phased
remediation approach.

**Violation categories:**

1. Raw `response.json()` — parse through Pydantic `model_validate()`
2. Empty string fallback — fail fast
3. Empty dict/list fallback — fail fast
4. Deep unified lib imports — use top-level
5. Function/class/method size exceeded

---

## 1. Raw `response.json()` — Parse Through Pydantic `model_validate()`

### Rule and Rationale

**Rule:** Every `response.json()` or `await response.json()` must be validated through a Pydantic model via
`Model.model_validate(...)` before use.

**Why:** Raw JSON returns `dict[str, Any]` (or `Any`). Accessing fields like `data["symbols"]` assumes the API contract.
If the API changes (field renamed, type changed, nested structure altered), the code fails at runtime with `KeyError`,
`TypeError`, or silent wrong behavior. Pydantic validation:

- Fails fast at the boundary with a clear `ValidationError`
- Documents the expected schema in code
- Enables type-safe access (`obj.symbols` instead of `data.get("symbols", [])`)

### Current Violations (Examples)

**Example 1 — Tardis adapter (REST, structured response):**

```python
# unified_market_interface/adapters/tradfi/tardis_adapter.py:205
response = self.base_client.sync_get(url, timeout=60)
response.raise_for_status()
exchange_info = response.json()  # ❌ Raw JSON
available_symbols = exchange_info.get("availableSymbols", [])  # Dict access, no validation
```

**Example 2 — Aster adapter (Binance-style exchangeInfo):**

```python
# unified_market_interface/adapters/onchain_perps/aster_adapter.py:168
response = self.client.sync_session.get(url, timeout=30)
response.raise_for_status()
exchange_info = response.json()  # ❌ Raw JSON
symbols = exchange_info.get("symbols", [])  # Dict access
```

**Example 3 — Uniswap V3 / The Graph (GraphQL, dynamic schema):**

```python
# unified_market_interface/adapters/defi/uniswap_v3_adapter.py:197
data = await response.json()  # ❌ Raw JSON — GraphQL response shape varies by query
if "errors" in data:
    logger.warning("The Graph query errors: %s", data["errors"])
return data
```

### Proper Fix Pattern

**Pattern A — REST with known schema (Tardis, Aster, Hyperliquid):**

UAC already has `TardisExchangeDetail` for the Tardis exchange endpoint. Use it:

```python
# Before
exchange_info = response.json()
available_symbols = exchange_info.get("availableSymbols", [])

# After
from unified_api_contracts import TardisExchangeDetail
parsed = TardisExchangeDetail.model_validate(response.json())
available_symbols = parsed.instruments if parsed.instruments else []
# Or: raise if required — if instruments is required, don't default to []
```

**Pattern B — Reference implementation (Hyperliquid, already fixed):**

```python
# unified_market_interface/adapters/onchain_perps/hyperliquid_adapter.py:179
metadata = HyperliquidMeta.model_validate(response.json())
if metadata.universe is None:
    raise ValueError("Hyperliquid meta response missing 'universe'")
universe = metadata.universe
for asset in universe:
    # asset is HyperliquidAssetInfo — typed, no .get() needed
    if not asset.name:
        continue
```

**Pattern C — GraphQL (dynamic schema):**

GraphQL responses vary by query. Options:

1. **Per-query models:** Define a Pydantic model for each query’s expected shape (e.g. `UniswapV3PoolsResponse` with
   `data.pools[].token0.symbol`).
2. **TypedDict for partial validation:** Use `TypedDict` for the subset of fields we care about; validate only those.
3. **Wrapper model:**
   `class GraphQLResponse(BaseModel): data: dict[str, object] | None; errors: list[dict[str, object]] | None` — at least
   validates top-level structure.

### Scope

| File / adapter family                                        | Response type                     | Fix approach                                                 |
| ------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------ |
| tardis_adapter.py                                            | REST (Tardis exchange detail)     | Use `TardisExchangeDetail`                                   |
| aster_adapter.py                                             | REST (Binance-style exchangeInfo) | Add `AsterExchangeInfo` to UAC or reuse Binance-style schema |
| thegraph_base_client.py                                      | GraphQL                           | Wrapper model for `data`/`errors`                            |
| aave_lending.py, aave_positions.py                           | GraphQL                           | Per-query models                                             |
| uniswap_v3_adapter.py, curve_adapter.py, balancer_adapter.py | GraphQL                           | Per-query models                                             |
| lst_lido_adapter.py, defi/utils.py                           | REST                              | Add schemas to UAC                                           |
| databento_adapter.py                                         | N/A (uses SDK, not raw JSON)      | —                                                            |

**Estimated:** ~15–20 files, ~25–35 `response.json()` call sites. Some share schemas (e.g. Binance-style
`exchangeInfo`).

---

## 2. Empty String Fallback — Fail Fast

### Rule and Rationale

**Rule:** No `.get("key", "")` — use Pydantic validation or raise when the key is missing.

**Why:** Empty string as fallback hides API contract violations. If `symbol` is required for downstream logic,
`raw.get("symbol", "")` produces `""`, which can cause:

- Wrong instrument keys
- Empty lookups
- Silent data loss

Fail fast: if the field is required, raise. If it’s optional, use `Optional[str] = None` in the model.

### Current Violations (Examples)

**Example 1 — Coinbase (required fields with empty fallback):**

```python
# unified_market_interface/adapters/coinbase.py:35
"time": str(raw.get("time", "")),  # ❌ Empty fallback
# Line 50, 54, 68, 92, 108 — same pattern for time, side, product_id
```

**Example 2 — Binance WebSocket:**

```python
# unified_market_interface/adapters/binance.py:49
"symbol": raw.get("s", ""),  # ❌ — WS message should always have symbol
# Line 100, 120, 165, 166 — symbol, side with empty fallback
```

**Example 3 — OKX (with noqa):**

```python
# unified_market_interface/adapters/okx.py:60
symbol = pt.symbol or raw_trade.get("instId", "")  # noqa: qg-empty-fallback
```

### Proper Fix Pattern

**Pattern A — Validate at boundary (preferred):**

Parse the raw dict into a Pydantic model. Required fields have no default; missing → `ValidationError`.

```python
# Before
symbol = str(raw_trade.get("product_id", ""))

# After — CoinbaseTrade has product_id: str (required)
trade = CoinbaseTrade.model_validate(raw_trade)
symbol = trade.product_id
```

**Pattern B — Explicit raise when required:**

```python
# Before
symbol = raw.get("s", "")

# After
symbol = raw.get("s")
if symbol is None or symbol == "":
    raise ValueError("Binance WS trade missing required field 's' (symbol)")
```

**Pattern C — Optional field (legitimate default):**

If the field is truly optional and empty is acceptable:

```python
# In Pydantic model: short_title: str | None = None
# At call site: use model validation, not .get("key", "")
```

### Scope

| File                    | Pattern                                        | Fix                                          |
| ----------------------- | ---------------------------------------------- | -------------------------------------------- |
| coinbase.py             | `.get("time", "")`, `.get("product_id", "")`   | Validate via CoinbaseTrade/CoinbaseOrderBook |
| binance.py              | `.get("s", "")`, `.get("symbol", "")`          | Validate via BinanceTrade or raise           |
| okx.py                  | `.get("instId", "")`                           | Validate via OKX schemas or raise            |
| bybit.py                | `.get("side", "")`, `.get("symbol", "")`       | Validate or raise                            |
| deribit.py              | `.get("bids", [])`, `.get("asks", [])`         | See §3 (empty list)                          |
| understat_adapter.py    | `.get("title", "")`, `.get("short_title", "")` | Validate or raise                            |
| thegraph_base_client.py | `.get("message", "")`                          | Error model with optional message            |

**Estimated:** ~12–15 files, ~25–40 call sites. Many can be fixed by adopting Pydantic validation from §1.

---

## 3. Empty Dict/List Fallback — Fail Fast

### Rule and Rationale

**Rule:** No `.get("key", {})` or `.get("key", [])` — validate structure or raise when the key is missing.

**Why:** Empty dict/list fallbacks hide structural changes. `data.get("pools", [])` can mask:

- API returning `{"pools": null}` instead of `[]`
- Renamed field (`"data"` → `"items"`)
- Pagination where empty means “no more pages” vs “error”

### Current Violations (Examples)

**Example 1 — Tardis (list fallback):**

```python
# unified_market_interface/adapters/tradfi/tardis_adapter.py:206
available_symbols = exchange_info.get("availableSymbols", [])
```

**Example 2 — Aster (list fallback):**

```python
# unified_market_interface/adapters/onchain_perps/aster_adapter.py:172
symbols = exchange_info.get("symbols", [])
```

**Example 3 — Binance order book (bids/asks):**

```python
# unified_market_interface/adapters/binance.py:87-88
"bids": raw_any.get("bids", []),
"asks": raw_any.get("asks", []),
```

**Example 4 — Bybit (order book with alternate keys):**

```python
# unified_market_interface/adapters/bybit.py:30-31
bids = raw.get("b", raw.get("bids", []))
asks = raw.get("a", raw.get("asks", []))
```

**Example 5 — Hyblock / Coinglass (nested fallbacks):**

```python
# unified_market_interface/adapters/cefi/hyblock.py:145
for lvl in payload.get("levels", payload.get("list", []))
```

### Proper Fix Pattern

**Pattern A — Pydantic model with default_factory:**

```python
# In schema
class ExchangeInfo(BaseModel):
    symbols: list[SymbolInfo] = Field(default_factory=list)
# Parsing: parsed = ExchangeInfo.model_validate(response.json())
# If symbols is required: symbols: list[SymbolInfo]  # no default → ValidationError if missing
```

**Pattern B — Explicit check and raise:**

```python
# Before
symbols = exchange_info.get("symbols", [])

# After
symbols = exchange_info.get("symbols")
if symbols is None:
    raise ValueError("Exchange info missing 'symbols'")
```

**Pattern C — Protocol-specific (Bybit b/bids):**

Bybit uses `b`/`a` or `bids`/`asks`. Model both:

```python
class BybitOrderBook(BaseModel):
    b: list[list[str]] = Field(default_factory=list, alias="bids")  # or separate fields
    a: list[list[str]] = Field(default_factory=list, alias="asks")
    # Use model_validate with the raw dict
```

### Scope

| File                                          | Pattern                                  | Fix                              |
| --------------------------------------------- | ---------------------------------------- | -------------------------------- |
| tardis_adapter.py                             | `.get("availableSymbols", [])`           | TardisExchangeDetail.instruments |
| aster_adapter.py                              | `.get("symbols", [])`                    | AsterExchangeInfo model          |
| binance.py, bybit.py, coinbase.py, deribit.py | `.get("bids", [])`, `.get("asks", [])`   | Order book models                |
| hyblock.py, coinglass.py                      | `.get("levels", [])`, `.get("list", [])` | Response models                  |
| databento_adapter.py                          | `.get("detail", {})`                     | Error detail model               |

**Estimated:** ~10–12 files, ~20–30 call sites. Overlaps with §1 and §2.

---

## 4. Deep Unified Lib Imports — Use Top-Level

### Rule and Rationale

**Rule:** No `from unified_api_contracts.unified_api_contracts_external.<venue>.schemas import X` — use
`from unified_api_contracts import X`.

**Why:** Deep imports couple consumers to UAC’s internal layout. Moving or renaming subpackages breaks all adapters.
Top-level imports:

- Treat UAC as a stable public API
- Centralize exports in one place
- Simplify refactoring inside UAC

### Current Violations (Examples)

**Already fixed (7 files):** base_adapter, bybit, okx, binance, sports/protocol, coinglass, hyblock.

**Remaining (20+ files):**

```python
# deribit.py
from unified_api_contracts.unified_api_contracts_external.deribit.schemas import (...)

# glassnode_adapter.py
from unified_api_contracts.unified_api_contracts_external.glassnode.schemas import (...)

# manifold_adapter.py
from unified_api_contracts.unified_api_contracts_external.manifold.schemas import (...)

# coinbase.py
from unified_api_contracts.unified_api_contracts_external.coinbase.schemas import (
    CoinbaseOrderBook, CoinbaseTicker, CoinbaseTrade,
)
# ... and 17+ more adapters
```

### Proper Fix Pattern

1. **Add export in UAC `__init__.py`:**
   ```python
   from .unified_api_contracts_external.coinbase.schemas import (
       CoinbaseOrderBook,
       CoinbaseProductInfo,
       CoinbaseProductsResponse,
       CoinbaseTicker,
       CoinbaseTrade,
   )
   ```
2. **Add to `__all__`**
3. **Update adapter:**
   ```python
   from unified_api_contracts import CoinbaseOrderBook, CoinbaseTicker, CoinbaseTrade
   ```

### Scope

| Adapter / file        | UAC subpackage     | Symbols to export                                |
| --------------------- | ------------------ | ------------------------------------------------ |
| coinbase.py           | coinbase.schemas   | CoinbaseOrderBook, CoinbaseTicker, CoinbaseTrade |
| deribit.py            | deribit.schemas    | (check existing exports)                         |
| glassnode_adapter.py  | glassnode.schemas  | (schema classes used)                            |
| manifold_adapter.py   | manifold.schemas   | (schema classes used)                            |
| mev_adapter.py        | mev.schemas        | (schema classes used)                            |
| polymarket_adapter.py | polymarket.schemas | PolymarketGammaMarket already exported           |
| barchart_adapter.py   | barchart.schemas   | (schema classes used)                            |
| kalshi_adapter.py     | kalshi.schemas     | (schema classes used)                            |
| ofr_adapter.py        | ofr.schemas        | (schema classes used)                            |
| fred_adapter.py       | fred.schemas       | (schema classes used)                            |
| ...                   | ...                | ...                                              |

**Estimated:** ~25 adapter files. Mechanical: add exports to UAC, update imports in UMI. Can be batched by venue.

---

## 5. Function/Class/Method Size Exceeded

### Rule and Rationale

**Rule:** Methods ≤ 50 lines, functions ≤ 200 lines, classes ≤ 900 lines (per `base-library.sh`).

**Why:** Large methods are hard to test, reason about, and reuse. They often mix multiple concerns (validation,
transformation, I/O, error handling).

### Current Violations (Examples)

**Example — DatabentoAdapter.fetch_instrument_definitions (148 lines):**

```python
# unified_market_interface/adapters/tradfi/databento_adapter.py:112
def fetch_instrument_definitions(self, exchange, symbols, date, dataset=None):
    # 1. Map exchange to dataset
    # 2. T+2 availability check
    # 3. Get query date (weekend adjustment)
    # 4. Build date range
    # 5. Group symbols by stype_in
    # 6. For each stype group: rate limit, fetch, handle 422, filter, iterate
    # 7. Return combined dict
    # ... 148 lines
```

**Example — HyperliquidAdapter.fetch_perpetuals (117 lines):**

Already uses `model_validate`; size is from data_sources_metadata JSON and loop logic.

### Proper Fix Pattern

**Extract helpers:**

```python
def fetch_instrument_definitions(self, ...):
    dataset = self._get_dataset_for_exchange(exchange)
    self._validate_t2_availability(target_date)
    query_date = self._get_query_date_for_databento(target_date)
    symbols_by_stype = self._group_symbols_by_stype(symbols)
    return self._fetch_instruments_by_stype(dataset, symbols_by_stype, query_date, exchange)

def _fetch_instruments_by_stype(self, dataset, symbols_by_stype, query_date, exchange):
    all_instruments = {}
    for stype_in, symbol_group in symbols_by_stype.items():
        instruments = self._fetch_one_stype_group(dataset, stype_in, symbol_group, query_date, exchange)
        all_instruments.update(instruments)
    return all_instruments
```

**Extract constants / config:**

```python
# Move data_sources_metadata dict to a method or module-level constant
def _get_data_sources_metadata(self) -> dict[str, object]:
    return {...}
```

### Scope

| Category         | Count | Approach                         |
| ---------------- | ----- | -------------------------------- |
| Methods > 50L    | ~80   | Extract helpers, split loops     |
| Functions > 200L | Few   | Split into smaller functions     |
| Classes > 900L   | ~4    | Extract mixins or sub-components |

**Estimated:** ~80 methods across DeFi, TradFi, CeFi, onchain-perps adapters. Refactors are incremental; each method can
be split in isolation.

---

## Phased Remediation Plan

### Phase 1 — Deep Imports (Low Risk, High Impact)

**Goal:** Eliminate deep import violations.

**Steps:**

1. For each adapter with deep imports, identify required symbols.
2. Add exports to `unified_api_contracts/__init__.py` and `__all__`.
3. Update adapter imports to top-level.
4. Run quality gates.

**Repos:** unified-api-contracts, unified-market-interface  
**Effort:** ~2–4 hours (mechanical)  
**Risk:** Low (no behavior change)

---

### Phase 2 — Raw JSON + Empty Fallbacks (Schema Work)

**Goal:** Add Pydantic models for REST responses and validate at boundary.

**Steps:**

1. **Tier 1 — Simple REST (Tardis, Aster):**
   - Add or reuse schemas in UAC (e.g. `TardisExchangeDetail`, `AsterExchangeInfo`).
   - Replace `response.json()` with `Model.model_validate(response.json())`.
   - Replace `.get("key", [])` with `parsed.field` (or raise if missing).
2. **Tier 2 — CeFi WebSocket (Binance, Bybit, OKX, Coinbase, Deribit):**
   - Ensure UAC has models for WS message shapes.
   - Validate raw dicts at parse/normalize boundary.
   - Remove empty fallbacks in favor of model fields or explicit raises.
3. **Tier 3 — GraphQL (The Graph, Aave, Uniswap):**
   - Add per-query response models where feasible.
   - For highly dynamic responses, use wrapper models for `data`/`errors`.

**Repos:** unified-api-contracts, unified-market-interface  
**Effort:** ~2–3 days (schema design + adapter updates)  
**Risk:** Medium (schema mismatches can surface new failures; test coverage important)

---

### Phase 3 — Function Size (Refactor)

**Goal:** Reduce method size to ≤ 50 lines.

**Steps:**

1. Target adapters with most violations (databento_adapter, uniswap_v3_adapter, aster_adapter, etc.).
2. For each oversized method: extract helpers, split loops, move constants.
3. Preserve behavior; add/run tests as needed.

**Repos:** unified-market-interface  
**Effort:** ~3–5 days (incremental refactors)  
**Risk:** Low if done incrementally with tests

---

## Dependencies and Ordering

- **Phase 1** can run independently.
- **Phase 2** benefits from Phase 1 (fewer deep imports to fix later).
- **Phase 3** can run in parallel with Phase 2 for different files.

---

## Success Criteria

- [ ] `bash scripts/quality-gates.sh` in unified-market-interface passes with 0 codex violations.
- [ ] No exclusion arrays (`RAW_JSON_EXTRA_EXCLUDES`, `EMPTY_FALLBACK_EXTRA_EXCLUDES`, etc.) in `quality-gates.sh`.
- [ ] QUALITY_GATE_BYPASS_AUDIT.md updated to remove or supersede §§2.8, 2.9, 2.10, 2.11 for UMI.

---

## References

- `unified-trading-pm/scripts/quality-gates-base/base-library.sh` — codex compliance checks
- `unified-market-interface/QUALITY_GATE_BYPASS_AUDIT.md` — current bypass justifications
- `unified-api-contracts/unified_api_contracts/__init__.py` — existing exports
- `unified-market-interface/adapters/onchain_perps/hyperliquid_adapter.py` — reference implementation for raw JSON +
  typed models
