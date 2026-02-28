# Version Alignment Report: UTEI, URDI, UDEI, UPI with api-contracts

**Date:** 2026-02-27
**Scope:** unified-trade-execution-interface, unified-reference-data-interface, unified-defi-execution-interface, unified-position-interface

---

## (a) Per-Interface Dependencies and Versions

| Interface | api-contracts | SDK/API Dependencies | Notes |
|-----------|---------------|----------------------|-------|
| **UTEI** | `>=1.0.0,<2.0.0` | `ccxt>=4.0`, `ib_insync>=0.9.86`, `aiohttp>=3.9`, `httpx>=0.27` | CeFi + TradFi; path dep on api-contracts |
| **URDI** | `>=0.1.0` | `ccxt>=4.0.0`, `aiohttp>=3.9.0,<4.0.0`, `unified-trading-services>=2.0.0` | REST reference data; path dep on api-contracts |
| **UDEI** | — | None (self-contained) | No SDK deps; consumers add unified-* as needed |
| **UPI** | `>=1.0.0,<2.0.0` | None | Schema-only; uses api-contracts for position/balance types |

### api-contracts Current State

- **Version:** 1.1.0
- **Schema coverage:** ccxt (CcxtOrder, CcxtTrade, CcxtBalance, CcxtPosition, etc.), ibkr (IBKROrder, IBKRPosition, etc.), per-venue (Binance, OKX, Bybit, Deribit, etc.)
- **SCHEMA_VERSIONS.md:** Documents per-venue schema coverage; no pinned SDK versions yet
- **No [schema-validation] optional deps** with ccxt/ib_insync pins in api-contracts pyproject.toml

---

## (b) Proposed Alignment Checks

### 1. api-contracts: Add schema-validation Pins

Add optional dependency group and version mapping:

```toml
[project.optional-dependencies]
schema-validation = [
    "requests>=2.31.0",
    "ccxt>=4.0,<5.0",   # Align with UTEI, URDI
]
```

Extend `SCHEMA_VERSIONS.md`:

| Venue/Provider | Schema Module | Package / API | Pinned Version | Last Validated |
|----------------|---------------|---------------|----------------|----------------|
| CCXT | api_contracts.ccxt | ccxt | >=4.0,<5.0 | 2026-02 |
| IBKR | api_contracts.ibkr | ib_insync | >=0.9.86 | 2026-02 |

### 2. Version Alignment Check Script (Same Pattern as check-dependency-alignment.sh)

**Location:** `api-contracts/scripts/check_sdk_version_alignment.py` or quality-gates step

**Logic:**
1. Parse `SCHEMA_VERSIONS.md` (or pyproject.toml `[schema-validation]`) for pinned SDK versions.
2. For each interface that depends on an SDK (UTEI, URDI):
   - Read interface pyproject.toml SDK version (e.g. `ccxt>=4.0`).
   - Check api-contracts has schemas for that version (ccxt 4.x → api_contracts.ccxt.schemas).
   - **FAIL** if interface uses SDK version X and api-contracts has no schemas for X (or schema version mismatch).

**Example failure:**
- UTEI has `ccxt>=4.0` but api-contracts SCHEMA_VERSIONS says "ccxt 3.x" → FAIL
- UTEI has `ib_insync>=0.9.86` but api-contracts has no ibkr schemas → FAIL

### 3. Integration into Quality Gates

- **api-contracts:** Add step: `uv pip install -e ".[schema-validation]"` → run `validate_schemas.py`; fail if schema-validation deps conflict with declared versions.
- **UTEI, URDI:** Add pre-test or quality-gates step: run `check_sdk_version_alignment.py` (or equivalent) that:
  - Reads interface SDK deps
  - Compares against api-contracts SCHEMA_VERSIONS / schema modules
  - Exits 1 if misaligned

### 4. UDEI and UPI

- **UDEI:** No SDK deps → no alignment check needed. When UDEI adds web3/Alchemy/The Graph, add pins and alignment check.
- **UPI:** Depends only on api-contracts → alignment is api-contracts version constraint only (already `>=1.0.0,<2.0.0`).

---

## (c) Integration Test Locations and Pattern

### Where Integration Tests Live

| Interface | Location | Current State |
|-----------|----------|---------------|
| **UTEI** | `tests/integration/test_account_queries.py`, `test_l1_orderbook_integration.py` | Calls real Binance Futures Testnet; **does NOT validate against api-contracts schema** |
| **URDI** | `tests/integration/test_import_sanity.py` | Minimal; no real API call |
| **UDEI** | `tests/` (unit only) | No integration tests |
| **UPI** | `tests/` | No integration tests (repo exists, structure TBD) |

### Recommended Integration Test Pattern (per API_CONTRACTS_AUDIT_ADDENDUM §4f)

**Pattern:** Call real API with credentials → validate response against api-contracts schema.

```python
# Example: UTEI tests/integration/test_api_contracts_integration.py
@pytest.mark.integration
@pytest.mark.skipif(not _has_testnet_credentials(), reason="Credentials required")
@pytest.mark.asyncio
async def test_binance_order_response_validates_against_api_contracts():
    """Call real API; validate response with api-contracts CcxtOrder schema."""
    adapter = get_order_adapter("binance", ...)
    # Fetch real order (or use fetch_open_orders and pick first)
    raw = await adapter._fetch_raw_order("...")  # or equivalent
    from api_contracts.ccxt.schemas import CcxtOrder
    order = CcxtOrder.model_validate(raw)
    assert order.id
```

**Credentials:** `get_secret_client()` or env vars (e.g. `BINANCE_FUTURES_TESTNET_API_KEY`). Skip gracefully when absent.

**Locations to add:**

| Interface | File | Validates |
|-----------|------|-----------|
| UTEI | `tests/integration/test_api_contracts_integration.py` | CCXT order/trade/position responses → CcxtOrder, CcxtTrade, CcxtPosition |
| UTEI | (same or separate) | IBKR callbacks → IBKROrder, IBKRPosition (when ib_insync integration exists) |
| URDI | `tests/integration/test_api_contracts_integration.py` | CCXT fetch_markets, fetch_ticker → CcxtMarket, CcxtTicker |
| UDEI | `tests/integration/` (when DeFi adapters added) | Alchemy/The Graph responses → api-contracts DeFi schemas |
| UPI | `tests/integration/` (when adapters added) | Position/balance responses → api-contracts position schemas |

---

## Summary

| Item | Status |
|------|--------|
| **(a) Deps documented** | ✅ Above |
| **(b) Alignment checks** | Proposed: SCHEMA_VERSIONS.md + [schema-validation] pins; `check_sdk_version_alignment.py`; quality-gates integration |
| **(c) Integration tests** | UTEI has integration tests but no api-contracts validation; URDI/UDEI/UPI need integration tests per pattern |

**Next steps:**
1. Add `[schema-validation]` and SCHEMA_VERSIONS.md pins in api-contracts.
2. Implement `check_sdk_version_alignment.py` (api-contracts or shared script).
3. Add integration tests in UTEI/URDI that validate real API responses against api-contracts schemas.
4. Wire alignment check into quality-gates for api-contracts, UTEI, URDI.
