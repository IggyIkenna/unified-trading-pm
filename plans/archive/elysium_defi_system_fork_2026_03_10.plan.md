---
doc_type: plan
title: elysium-defi-system-fork-2026-03-10
summary: Create a standalone elysium-defi-system repo forked from DeFi strategy/execution components, delivered as a private
  GitHub repo + Docker image for Elysium Capital
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: code
epic: epic-code-completion
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: elysium-defi-system, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-market-interface, code: C2, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: [elysium_defi_presentation_2026_03_10, api_keys_and_auth]
todos:
- {id: phase-1-repo-setup, content: 'Create elysium-defi-system repo structure, copy and strip source modules from strategy-service, execution-service, and unified-market-interface', status: todo, note: ''}
- {id: phase-2-runner, content: 'Implement config model, main runner, and paper trader', status: todo, note: ''}
- {id: phase-3-web-ui, content: Build FastAPI endpoints and dashboard HTML, status: todo, note: ''}
- {id: phase-4-testing, content: Record VCR cassettes for all 14 protocols and write integration tests, status: todo, note: ''}
- {id: phase-5-docs, content: 'Write README, setup.md, and strategy-guide.md', status: todo, note: ''}
isProject: false
---

# Plan: Elysium DeFi Lite Fork

## Context

Elysium Capital (DeFi client) wants to own and run an end-to-end DeFi strategy system themselves. They need: DeFi market
data adapters (14 protocols), DeFi strategy execution (basis, lending, staked-basis, recursive-basis), and DeFi
execution handlers (swap, lend, stake, borrow, flash-loan) — without our deployment infrastructure orchestration. They
run it via `docker-compose up`. The fork strips out TradFi, CeFi, Sports, ML training, deployment-service, and
multi-repo orchestration. Client delivery: private GitHub repo + Docker image + setup guide.

---

## Scope: included vs excluded

**Included:**

- DeFi strategies: `defi_basis.py`, `defi_lending.py`, `defi_staked_basis.py`, `defi_recursive_basis.py`, `defi_base.py`
- DeFi execution handlers: `swap_handler.py`, `borrow_handler.py`, `lend_handler.py`, `stake_handler.py`,
  `flash_loan_handler.py`
- UMI DeFi adapters: aave_v3, balancer, curve, ethena, euler, fluid, etherfi, lido, morpho, uniswap_v2/v3/v4, instadapp,
  defillama
- Thin runner: CLI that wires strategies → market data → execution
- Basic web UI (read-only): positions, strategy state, recent trades
- VCR cassettes for all 14 DeFi protocols (client can test without prod creds)
- Paper trading mode (default on)
- Live trading mode (activated by config + real wallet)

**Excluded:**

- TradFi, CeFi, Sports adapters
- ML training/inference pipeline
- Feature pipeline services (all 8)
- deployment-service orchestration
- Multi-repo workspace structure
- Non-DeFi circuit breakers
- UEI (replaced with simple Python logging)
- UCI (replaced with direct env var reads — client context only)

---

## Phase 1: Repository setup

### P1.1 — Repository structure

```
elysium-defi-system/
├── pyproject.toml          (single package: elysium_defi_system)
├── docker-compose.yml      (production: live trading)
├── docker-compose.dev.yml  (VCR cassette mode, paper trading)
├── .env.example
├── README.md
├── docs/
│   ├── setup.md
│   ├── config.md
│   └── strategy-guide.md
└── src/
    ├── market_data/
    │   ├── adapters/       (14 DeFi adapters from UMI)
    │   └── factory.py      (creates adapter instances from config)
    ├── strategies/
    │   ├── base.py         (stripped defi_base.py)
    │   ├── basis.py        (defi_basis.py)
    │   ├── lending.py      (defi_lending.py)
    │   ├── staked_basis.py
    │   └── recursive_basis.py
    ├── execution/
    │   ├── handlers/       (swap, lend, stake, borrow, flash_loan)
    │   ├── circuit_breaker.py  (DeFi-specific, config-driven)
    │   └── paper_trader.py
    ├── runner/
    │   ├── main.py         (entry point)
    │   ├── config.py       (Pydantic config model)
    │   └── scheduler.py    (signal generation loop)
    ├── web_ui/
    │   ├── main.py         (FastAPI)
    │   └── templates/      (HTML + Chart.js)
    └── tests/
        ├── unit/
        ├── integration/
        └── vcr_cassettes/  (committed, no secrets)
```

### P1.2 — Copy and strip source modules

**From strategy-service:**

- Copy `engine/strategies/defi_*.py` → `src/strategies/`
- Strip imports: remove UEI, UCI, UIC, UAC, feature-service, ML-interface imports
- Replace: `log_event(...)` → `logger.info(...)`
- Replace: `UnifiedCloudConfig()` → direct env var access (acceptable in client fork)
- Keep: all strategy logic, signal generation, position tracking

**From execution-service:**

- Copy `engine/handlers/swap_handler.py`, `borrow_handler.py`, `lend_handler.py`, `stake_handler.py`,
  `flash_loan_handler.py` → `src/execution/handlers/`
- Copy `engine/circuit_breaker.py` → `src/execution/circuit_breaker.py`
- Strip: TradFi/CeFi handlers, TWAP/VWAP/SOR (keep only DeFi-relevant algos)
- Keep: gas cost estimation, slippage calculation, position tracking

**From unified-market-interface:**

- Copy `adapters/defi/` directory → `src/market_data/adapters/`
- Keep: all 14 DeFi adapter implementations
- Strip: tradfi/, cefi/, sports/ adapter directories + their imports

### P1.3 — Lightweight Pydantic schemas (replace UAC)

File: `src/schemas.py`

Copy only the DeFi schemas from UAC that are actually used:

```python
# DeFi position, trade, signal schemas
class DeFiPosition(BaseModel):
    protocol: str; asset: str; amount: Decimal; usd_value: float; entry_ts: datetime

class DeFiTrade(BaseModel):
    strategy: str; action: str; protocol: str; asset: str; amount: Decimal; pnl: float

class SignalOutput(BaseModel):
    strategy: str; direction: str; strength: float; reason: str; timestamp: datetime
```

---

## Phase 2: Runner / orchestration

### P2.1 — Config model

File: `src/runner/config.py`

```python
class DeFiSystemConfig(BaseModel):
    # Blockchain connectivity
    rpc_url_ethereum: str   # Alchemy/Infura RPC URL
    rpc_url_arbitrum: str | None = None
    rpc_url_base: str | None = None

    # Wallet
    wallet_address: str     # 0x...
    private_key: str | None = None  # only for live trading

    # Mode
    paper_trading: bool = True  # default safe — must explicitly set False for live

    # Strategy selection
    enabled_strategies: list[str] = ["basis", "lending"]

    # Execution constraints
    max_gas_gwei: float = 100.0
    slippage_tolerance_pct: float = 0.5
    max_position_usd: float = 10000.0  # safety cap per protocol

    # Polling
    poll_interval_seconds: int = 60
```

### P2.2 — Main runner

File: `src/runner/main.py`

```python
async def main() -> None:
    config = DeFiSystemConfig.model_validate(load_env())
    adapters = build_adapters(config)
    strategies = build_strategies(config, adapters)
    executor = DeFiExecutor(adapters, config) if not config.paper_trading \
               else PaperTrader(adapters, config)

    logger.info(f"Starting DeFi system (paper_trading={config.paper_trading})")
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_strategy_loop(strategies, executor, config))
        tg.create_task(run_web_ui())
```

### P2.3 — Paper trader

File: `src/execution/paper_trader.py`

```python
class PaperTrader:
    """Records hypothetical trades. State persisted to SQLite (portable, no cloud needed)."""
    _db: sqlite3.Connection  # local trades.db

    async def execute(self, signal: SignalOutput) -> DeFiTrade:
        price = await self._get_current_price(signal)
        trade = DeFiTrade(strategy=signal.strategy, action=signal.direction,
                          protocol=..., asset=..., amount=..., entry_price=price)
        self._db.execute("INSERT INTO trades VALUES (?)", [trade.model_dump_json()])
        return trade
```

---

## Phase 3: Web UI

### P3.1 — FastAPI endpoints

File: `src/web_ui/main.py`

```python
@app.get("/positions")
async def get_positions() -> list[DeFiPosition]: ...  # from SQLite

@app.get("/trades")
async def get_trades(limit: int = 50) -> list[DeFiTrade]: ...

@app.get("/signals")
async def get_signals() -> dict[str, SignalOutput]: ...  # current signal per strategy

@app.get("/yields")
async def get_yields() -> dict[str, float]: ...  # current APY per protocol

@app.get("/health")
async def health() -> dict: ...
```

### P3.2 — Dashboard HTML

File: `src/web_ui/templates/dashboard.html`

Single-page HTML (no React — minimal dependencies for client):

- Strategy status cards: enabled/disabled, last signal, current position
- Positions table: protocol, asset, amount, USD value, unrealized PnL
- PnL chart: Chart.js line chart (last 30 days)
- Yield comparison bar chart: current APY per protocol
- Recent trades table: last 20 trades with direction, PnL
- System status: last update, paper/live mode indicator

---

## Phase 4: Testing

### P4.1 — VCR cassettes for all 14 protocols

Record HTTP responses for each DeFi adapter during development:

- `VCR_MODE=record pytest tests/integration/` → cassettes recorded
- Cassettes committed to `tests/vcr_cassettes/{protocol}/`
- No secrets in cassettes (auth headers stripped, wallet addresses anonymized)

### P4.2 — Integration tests with cassettes

File: `tests/integration/test_defi_strategies.py`

```python
@pytest.mark.parametrize("strategy", ["basis", "lending", "staked_basis"])
async def test_strategy_generates_valid_signals(strategy: str, vcr_cassette) -> None:
    runner = build_test_runner(strategy, vcr_cassette)
    signals = await runner.run_one_cycle()
    assert len(signals) > 0
    for signal in signals:
        assert signal.strategy == strategy
        assert signal.direction in ("long", "short", "flat")
        assert -1.0 <= signal.strength <= 1.0
```

### P4.3 — Paper trading smoke test

```bash
docker-compose -f docker-compose.dev.yml run --rm test
# Should: start, run 1 cycle with VCR cassettes, generate signals, record to SQLite, exit 0
```

---

## Phase 5: Documentation

### P5.1 — README.md

```markdown
# Elysium DeFi System

End-to-end DeFi strategy execution system.

## Quick start (paper trading, no live funds)

cp .env.example .env

# Edit .env: add your Alchemy RPC URL

docker-compose -f docker-compose.dev.yml up

# Open http://localhost:8080 to view positions and signals
```

### P5.2 — docs/setup.md

- Prerequisites: Docker, Alchemy/Infura RPC URL
- .env configuration reference
- Paper trading mode vs live trading (how to switch, risks)
- Monitoring: what the dashboard shows

### P5.3 — docs/strategy-guide.md

Per strategy: how it works, what it trades, key parameters, historical performance.

---

## Delivery

- Private GitHub repo invite to Elysium GitHub account
- Docker image: `ghcr.io/unified-trading/elysium-defi-system:latest`
- Demo session: show paper trading running in Docker (30 min walk-through)
- Handoff: Elysium configures their Alchemy RPC URL + wallet address in `.env`

## Verification Gates

- [ ] `docker-compose -f docker-compose.dev.yml up` → starts, runs 1 cycle, no errors
- [ ] Paper trading: 24h run with no crashes, SQLite `trades.db` has entries
- [ ] `pytest tests/ --vcr` → all tests green with cassettes
- [ ] Web UI: http://localhost:8080 shows positions, signals, yields
- [ ] Live trading: `paper_trading=false` with paper wallet → single test trade executes on testnet

## Files Created

- `elysium-defi-system/` (new repo, all files described above)

## Dependencies

- `stub_completion_interfaces_and_infra.md` (UPI/UMI DeFi adapters must be complete)
- `api_keys_and_auth.md` Phase 2 (DeFi VCR cassettes needed for tests)
- `elysium_defi_presentation_2026_03_10.md` (presentation references this fork)
