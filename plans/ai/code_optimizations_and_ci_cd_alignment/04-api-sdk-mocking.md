# 04: API/SDK Contract Mocking

**Status**: ⬜ Not Started  
**Priority**: P1 (Prevents runtime surprises)  
**Estimated Time**: 3-4 hours  
**Expected Benefit**: 15-30 min/day saved, fewer API integration bugs

---

## 📖 Overview

Create a "mock" or "spec" repository that defines API contracts for external services (Databento, Tardis, Binance, etc.) so LLMs can code against known, stable behaviors without live API calls.

### Current State
- LLMs write code assuming API behavior
- Tests fail at runtime when API returns unexpected data
- Must debug and fix after discovering API differences
- No single source of truth for API contracts

### Target State
- All external APIs have defined contracts (schemas, endpoints, examples)
- LLMs code against contracts (type-safe)
- Tests use mocked responses (fast, deterministic)
- Real API calls only in integration tests

---

## 🔗 Dependencies

**None** - Can be implemented independently.

---

## 🚧 Blockers

- [ ] Need to document actual API responses (requires live API calls)
- [ ] Need to choose mocking approach (Pydantic vs VCR.py vs OpenAPI)
- [ ] Need to integrate with existing test suite

---

## 🔍 Current API Usage

### APIs to Mock

1. **Databento** (market data)
   - Endpoints: historical data, symbology, metadata
   - Used by: market-tick-data-handler, market-data-processing-service

2. **Tardis** (market data)
   - Endpoints: historical trades, order books, funding rates
   - Used by: market-tick-data-handler

3. **Binance** (exchange)
   - Endpoints: markets, tickers, order book, trades
   - Used by: execution-service, strategy-service

4. **CCXT** (unified exchange interface)
   - Methods: fetch_markets, fetch_ticker, fetch_order_book
   - Used by: instruments-service, execution-service

5. **The Graph** (DeFi data)
   - Queries: pools, swaps, positions
   - Used by: instruments-service (DeFi processor)

---

## 🛠️ Implementation

### Approach: Hybrid (Pydantic + VCR.py)

**Pydantic models** for type safety + **VCR.py** for realistic responses.

### Step 1: Create API Contracts Repository

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

# Create new directory (not a separate repo, part of workspace)
mkdir -p api-contracts
cd api-contracts

# Create structure
mkdir -p {databento,tardis,binance,ccxt,thegraph}/{schemas,examples,mocks}

# Create README
cat > README.md << 'EOF'
# API Contracts

Defines contracts for external APIs used across the trading system.

## Purpose

- **Type safety**: Pydantic models for all API responses
- **Testing**: VCR.py cassettes for realistic test data
- **Documentation**: Single source of truth for API behavior

## Structure

```
api-contracts/
├── databento/
│   ├── schemas.py          # Pydantic models
│   ├── examples/           # Sample responses (JSON)
│   └── mocks/              # VCR.py cassettes
├── tardis/
│   ├── schemas.py
│   ├── examples/
│   └── mocks/
├── binance/
│   ├── schemas.py
│   ├── examples/
│   └── mocks/
├── ccxt/
│   ├── schemas.py
│   ├── examples/
│   └── mocks/
└── thegraph/
    ├── schemas.py
    ├── examples/
    └── mocks/
```

## Usage

### In Production Code

```python
from api_contracts.databento.schemas import HistoricalDataResponse

response = databento_client.get_historical_data(...)
validated = HistoricalDataResponse(**response)  # Type-safe!
```

### In Tests

```python
import vcr

@vcr.use_cassette('api-contracts/databento/mocks/historical_data.yaml')
def test_process_databento_data():
    response = databento_client.get_historical_data(...)
    # Uses recorded response, no live API call
```
EOF
```

### Step 2: Define Databento Schemas

```python
# api-contracts/databento/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime

class DatabentoSymbol(BaseModel):
    """Databento symbol metadata."""
    symbol: str
    stype_in: str
    stype_out: str
    start_date: str
    end_date: str | None = None

class DatabentoTrade(BaseModel):
    """Databento trade record."""
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    ts_recv: int = Field(description="Receive timestamp (nanoseconds)")
    price: float
    size: float
    side: str  # 'B' or 'A'
    flags: int = 0
    
    @property
    def timestamp(self) -> datetime:
        """Convert nanosecond timestamp to datetime."""
        return datetime.fromtimestamp(self.ts_event / 1e9)

class DatabentoHistoricalResponse(BaseModel):
    """Response from Databento historical API."""
    dataset: str
    schema: str
    start: str
    end: str
    symbols: list[str]
    stype_in: str
    stype_out: str
    records: list[DatabentoTrade]
    
    @property
    def record_count(self) -> int:
        return len(self.records)
```

### Step 3: Capture Real API Responses

```python
# scripts/capture-api-responses.py
"""
Capture real API responses for mocking.

Usage:
    python scripts/capture-api-responses.py --api databento --endpoint historical
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import databento as db

def capture_databento_historical():
    """Capture Databento historical data response."""
    client = db.Historical(key=os.getenv("DATABENTO_API_KEY"))
    
    # Request small sample
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["ES.FUT"],
        schema="trades",
        start=datetime.now() - timedelta(days=1),
        end=datetime.now() - timedelta(days=1, hours=23),
        limit=100  # Small sample
    )
    
    # Save as JSON
    output_path = Path("api-contracts/databento/examples/historical_trades.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump([record.to_dict() for record in data], f, indent=2)
    
    print(f"✅ Saved {len(data)} records to {output_path}")

def capture_tardis_trades():
    """Capture Tardis trades response."""
    # Similar pattern for Tardis
    pass

def capture_binance_markets():
    """Capture Binance markets response."""
    import ccxt
    
    exchange = ccxt.binance()
    markets = exchange.fetch_markets()
    
    # Save sample (first 10 markets)
    output_path = Path("api-contracts/binance/examples/markets.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(markets[:10], f, indent=2)
    
    print(f"✅ Saved {len(markets[:10])} markets to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", choices=["databento", "tardis", "binance"], required=True)
    parser.add_argument("--endpoint", required=True)
    args = parser.parse_args()
    
    if args.api == "databento" and args.endpoint == "historical":
        capture_databento_historical()
    elif args.api == "binance" and args.endpoint == "markets":
        capture_binance_markets()
    # Add more as needed
```

### Step 4: Set Up VCR.py for Tests

```bash
# Install VCR.py
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/market-tick-data-handler
uv pip install vcrpy
```

```python
# tests/conftest.py
import vcr
import pytest
from pathlib import Path

# VCR configuration
vcr_config = vcr.VCR(
    cassette_library_dir=str(Path(__file__).parent.parent.parent / "api-contracts" / "databento" / "mocks"),
    record_mode='once',  # Record once, then replay
    match_on=['uri', 'method'],
    filter_headers=['authorization', 'x-api-key'],  # Don't record API keys
)

@pytest.fixture
def vcr_cassette():
    """Fixture to use VCR cassettes in tests."""
    return vcr_config

# Example usage in test:
# @pytest.mark.vcr()
# def test_databento_api(vcr_cassette):
#     with vcr_cassette.use_cassette('historical_trades.yaml'):
#         response = databento_client.get_historical_data(...)
#         # Uses recorded response, no live API call
```

### Step 5: Update Existing Code to Use Schemas

```python
# market-tick-data-handler/market_tick_data_handler/adapters/databento_adapter.py

# Before (no type safety):
def fetch_trades(self, symbol: str, start: str, end: str) -> list[dict]:
    response = self.client.get_historical_data(...)
    return response  # Any type, no validation

# After (type-safe):
from api_contracts.databento.schemas import DatabentoHistoricalResponse, DatabentoTrade

def fetch_trades(self, symbol: str, start: str, end: str) -> list[DatabentoTrade]:
    response = self.client.get_historical_data(...)
    validated = DatabentoHistoricalResponse(**response)
    return validated.records  # Fully typed!
```

### Step 6: Update Tests to Use Mocks

```python
# tests/integration/test_databento_adapter.py

import pytest
import vcr

@pytest.mark.vcr()
def test_fetch_trades_databento():
    """Test Databento adapter with recorded response."""
    from api_contracts.databento.schemas import DatabentoTrade
    from market_tick_data_handler.adapters.databento_adapter import DatabentoAdapter
    
    adapter = DatabentoAdapter(api_key="fake-key")  # Won't be used (VCR replay)
    
    # Use recorded cassette
    with vcr.use_cassette('api-contracts/databento/mocks/historical_trades.yaml'):
        trades = adapter.fetch_trades(
            symbol="ES.FUT",
            start="2024-01-01",
            end="2024-01-02"
        )
    
    # Validate response
    assert len(trades) > 0
    assert all(isinstance(t, DatabentoTrade) for t in trades)
    assert all(t.price > 0 for t in trades)
    assert all(t.side in ['B', 'A'] for t in trades)
```

---

## ✅ Verification

### Test 1: Schema Validation

```python
# Test that schemas match real API responses
from api_contracts.databento.schemas import DatabentoHistoricalResponse
import json

# Load captured response
with open('api-contracts/databento/examples/historical_trades.json') as f:
    data = json.load(f)

# Should validate without errors
response = DatabentoHistoricalResponse(**data)
print(f"✅ Validated {response.record_count} records")
```

### Test 2: VCR Replay

```python
# Test that VCR cassettes work
import vcr

@vcr.use_cassette('api-contracts/databento/mocks/historical_trades.yaml')
def test_vcr():
    # Make API call (will use recorded response)
    response = databento_client.get_historical_data(...)
    assert response is not None
    print("✅ VCR replay works")
```

### Test 3: Type Safety in IDE

Open a file using the schemas in Cursor:

```python
from api_contracts.databento.schemas import DatabentoTrade

trade = DatabentoTrade(...)
trade.  # Should show autocomplete: price, size, side, timestamp, etc.
```

**Expected**: Full autocomplete and type checking.

---

## 📊 Success Metrics

- [ ] All 5 APIs have Pydantic schemas defined
- [ ] All APIs have example responses captured
- [ ] All APIs have VCR cassettes for common endpoints
- [ ] Existing code updated to use schemas (type-safe)
- [ ] Tests use VCR cassettes (no live API calls in unit tests)
- [ ] LLMs can read schemas and generate correct code
- [ ] Zero "unexpected API response" errors in development

---

## 🔄 Rollback Plan

If schemas cause issues:

1. Keep schemas as documentation only
2. Don't enforce validation in production code
3. Continue using VCR for tests
4. Gradually adopt schemas as confidence grows

---

## 📚 Related Documentation

- ChatGPT conversation: Lines 73-96 (API mocking discussion)
- Pydantic docs: https://docs.pydantic.dev
- VCR.py docs: https://vcrpy.readthedocs.io
- Type checking rules: `.cursor/rules/strict-type-checking.mdc`

---

## 💡 Tips

1. **Start with most-used APIs**: Databento and Binance first
2. **Capture small samples**: 10-100 records, not full datasets
3. **Update cassettes periodically**: APIs change, re-record yearly
4. **Use in tests first**: Gain confidence before using in production
5. **Share across services**: api-contracts/ is workspace-wide

---

## ✏️ Notes

- Pydantic provides type safety and validation
- VCR.py provides realistic test data
- Combination gives best of both worlds
- Expected to save 15-30 min/day debugging API issues
- Prevents "works in dev, fails in prod" API surprises
