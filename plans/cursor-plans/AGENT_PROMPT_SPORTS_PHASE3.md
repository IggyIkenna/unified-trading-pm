# Agent Prompt — Sports Phase 3: Service Integration

> **SUPERSEDED (2026-03-01): Sports services have been consolidated into existing core services.**
> - `sports-reference-data-service` -> merged into `instruments-service`
> - `sports-odds-processing-service` -> merged into `market-data-processing-service`
> - `sports-strategy-service` -> merged into `strategy-service`
> - `sports-execution-service` -> merged into `execution-service`
> - `features-sports-service` and `unified-sports-execution-interface` remain standalone.
> - `sports-odds-data-service` remains standalone.
> See `workspace-manifest.json` for updated statuses and dependency lists.

> Paste this entire prompt into a new agent session to execute Sports Phase 3.
> REQUIRES Sports Phase 1 AND Sports Phase 2 fully complete. Verify preconditions before starting.

---

Follow all workspace cursor rules in .cursorrules.
No summary docs (no-summary-docs.mdc). uv not pip. quickmerge not git push.
basedpyright <dir>/ not basedpyright. Delete deprecated code; no parallel code paths.
Search unified libraries before implementing anything new.

WORKSPACE_ROOT=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos
SPORTS_REPO=/Users/ikennaigboaka/Documents/repos/other_repos/sports-betting-services
All Python/pytest/ruff/basedpyright/QG commands: cd WORKSPACE_ROOT && source .venv-workspace/bin/activate first.

---

## Standard of Work — Citadel Audit-Worthy

> **When in doubt, assume a senior quant engineer at a top-tier fund (Citadel, Two Sigma, DE Shaw) is reviewing every PR. Build accordingly.**

This means — no exceptions, no shortcuts:
- **No silent errors** — every `except` block must reraise, raise a typed error, or log at ERROR + reraise. `pass` is a build failure.
- **No empty fallbacks** — `os.getenv(KEY, '')` is forbidden. Use `UnifiedCloudConfig` or fail on missing config.
- **No untyped boundaries** — every GCS write, PubSub message, and service output uses Pydantic models. `dict[str, Any]` at a boundary is a type violation.
- **No service→service Python imports** — services communicate via GCS, PubSub, or HTTP only.
- **Full observability** — every service logs all 11 lifecycle events. Every failure is structured with `correlation_id`, `service_name`, `timestamp`.
- **Every secret** through Secret Manager. Every config through `UnifiedCloudConfig`.
- **Every external call** has retry logic (`@with_retry`) and a timeout.
- **Batch/live symmetry** — every service supports `--mode batch|live`. The engine is mode-agnostic.
- If it would fail a Citadel code review, it is not done.

---

## Preconditions (verify ALL before starting)

```bash
# 1. All 20 adapter implementations complete (no NotImplementedError)
python -c "
from unified_sports_execution_interface.adapters.exchanges.betfair import BetfairAdapter
from unified_sports_execution_interface.adapters.aggregator.odds_api import OddsApiAdapter
from unified_sports_execution_interface.adapters.scrapers.skybet import SkyBetAdapter
print('USEI adapters: OK')
"

# 2. All 14 feature calculators ported
python -c "
from features_sports_service.calculators.pipeline import FeaturePipeline
print('FeaturePipeline: OK')
"

# 3. SportsFeatureVector schema exists
python -c "from unified_api_contracts.sports.canonical.features import SportsFeatureVector"

# 4. All typed exceptions exist
python -c "from unified_api_contracts.sports.errors import BetRejectedError, ScraperError, OddsChangedError"

# 5. UMI sports registry works
python -c "
from unified_market_interface.sports.registry import adapter_for_bookmaker
a = adapter_for_bookmaker('betfair')
print(f'Registry: OK — {type(a).__name__}')
"

# 6. All 5 service skeletons exist
python -c "import sports_reference_data_service, sports_odds_data_service, sports_odds_processing_service, sports_strategy_service, sports_execution_service; print('Services: OK')"

# 7. unified-sports-execution-interface D5 passed
# 8. features-sports-service D5 passed
```

If any check fails: STOP. Complete Sports Phase 1/2 first.

---

## SSOT

| Source | Path |
|--------|------|
| AC sports schemas | `unified-api-contracts/unified_api_contracts/sports/` |
| USEI adapters | `unified-sports-execution-interface/unified_sports_execution_interface/adapters/` |
| UMI sports registry | `unified-market-interface/unified_market_interface/sports/registry.py` |
| Feature pipeline | `features-sports-service/features_sports_service/calculators/pipeline.py` |
| Batch/live symmetry | `unified-trading-codex/04-architecture/batch-live-symmetry.md` |
| Event logging | `unified-trading-codex/03-observability/lifecycle-events.md` |
| Service pair flows | `unified-trading-codex/08-workflows/service-pair-flows.md` |
| Integration layers | `unified-trading-codex/06-coding-standards/integration-testing-layers.md` |

---

## Sports Pipeline DAG — Batch Ordering

**Never start Sports Batch N until Sports Batch N-1 is fully D5 green.**

```
Sports Batch A:  sports-reference-data-service
                 (analogous to instruments-service — reference data foundation)

Sports Batch B:  sports-odds-data-service  |  sports-odds-processing-service
                 (parallel, after Batch A D5 — analogous to MTDH + MDPS)

Sports Batch C:  features-sports-service
                 (already partial from Phase 2 — wire to Batch B output, after Batch B D5)

Sports Batch D:  sports-strategy-service
                 (arbitrage + ML — after Batch C D5)

Sports Batch E:  sports-execution-service
                 (bet placement — after Batch D D5)
```

---

## Naming Check — Run at Step A of Every Service

```bash
rg 'BaseSportsAdapter' .  # must be zero (deleted in Phase 1)
rg 'dict\[str, str\]' .   # must be zero in USEI (old untyped protocol)
rg 'from footballbets' .  # must be zero (no imports from external sports repo)
rg 'postgresql\|psycopg2\|sqlalchemy' . --type py  # must be zero (no DB in pipeline services)
```

---

## Bottom-Up Rule — No Exceptions

If any service needs a new schema, error type, lifecycle event, or config field during implementation:
→ Add to the correct T0 library FIRST (AC, UEI, UCI, UCLI)
→ Run D5 on that library
→ Cascade `--dep-branch` to all consumers
→ Only then use in the service

**Never define a schema or contract inline in a service.**

---

## Testing Progression

| Step | Command | ~Time | Catches |
|------|---------|-------|---------|
| Import smoke | `python -c "import <pkg>"` | 2s | Broken `__init__`, circular imports |
| D1 | `--lint-only` | 30s | Syntax, formatting |
| D2 | `--unit-only` | ~2 min | Type errors, unit test failures |
| D3 | `--qg-only` | ~5 min | Integration failures, coverage gaps |
| D4 | `--quick` | ~8 min | Full QG + git ops |
| D5 | (no flags) | ~15 min | Full pipeline — the only gate that counts |

**D5 is the only valid green gate.** `--quick` alone is not sufficient for batch promotion.

---

## Per-Service Step Pattern

Every service (Batches A–E) follows:

**Step A — Naming + connectivity audit:**
- Run naming checks above (zero hits required)
- `python -c 'import <package>'` exits 0
- Zero `os.getenv(API_KEY)`, zero direct `requests` calls, zero PostgreSQL imports
- `cloudbuild.yaml` image tag correct
- All deps present in `pyproject.toml`

**Step B — Tests first (before code):**
- Add `tests/unit/test_schema_robustness.py`: required field missing → `ValidationError`
- Add `tests/unit/test_event_logging.py`: all 11 lifecycle events emitted in correct order
- Add `tests/unit/test_imports.py`: import every public module
- Add `tests/unit/test_batch_live_seams.py`: mode-agnostic engine accepts both batch + live data sources

**Step C — Engine implementation:**
- Mode-agnostic engine receives data via injected adapter (batch: GCS reader / live: PubSub)
- `--mode batch`: date range loop → GCS write → PubSub publish completion event
- `--mode live`: event-driven callback → PubSub publish output
- No mode-specific logic inside the engine class

**D1 → D5:** Quickmerge ladder. Fix each step before the next.

---

## Sports Batch A — `sports-reference-data-service`

**Analogy:** instruments-service. Fetches canonical reference data for all fixtures and writes to GCS.

**Data sources (via existing clients from SPORTS_REPO, ported as thin wrappers):**
- API-Football: fixtures, teams, players, lineups, events, stats, referees, venues
- FootyStats: league/team/player metadata, BTTS/over-under historical stats
- Soccer-Football-Info: match dominance stats, progressive stats

**Engine architecture:**
```python
class ReferenceDataEngine:
    """
    Fetches canonical fixture/team/league/player reference data from multiple sources.
    Merges via canonical mapping (CanonicalFixture.fixture_id = cross-source key).
    Mode-agnostic: batch fetches a date range; live subscribes to API-Football webhook.
    """

    def __init__(
        self,
        api_football_client: APIFootballClient,
        footystats_client: FootyStatsClient,
        sfi_client: SoccerFootballInfoClient,
        writer: BaseCloudWriter,
    ) -> None: ...

    async def process_fixture(self, fixture_id: str) -> CanonicalFixture:
        """Fetch from all sources, merge, return canonical fixture."""
        ...
```

**GCS output schema:**
```
gs://sports-reference-data/
  canonical/
    fixtures/
      {season}/{league_id}/{fixture_id}.json   # CanonicalFixture serialized
    teams/
      {team_id}.json                           # CanonicalTeam
    leagues/
      {league_id}/{season}.json                # CanonicalLeague
```

**PubSub output topic:** `sports-reference-data-updated`
**Message schema:** `{"fixture_id": "af:12345", "event": "FIXTURE_UPDATED", "timestamp_utc": "..."}`

**Config fields to add to `unified-config-interface`:**
```python
sports_api_football_key: str          # Secret Manager
sports_footystats_key: str            # Secret Manager
sports_sfi_key: str                   # Secret Manager
sports_reference_data_bucket: str     # GCS bucket
sports_reference_data_pubsub_topic: str
```

**Lifecycle events (11 required, from `unified-events-interface`):**
`STARTED` → `CONFIG_LOADED` → `VALIDATION_STARTED` → `VALIDATION_COMPLETED` →
`DATA_FETCH_STARTED` → `DATA_FETCH_COMPLETED` →
`PERSISTENCE_STARTED` → `PERSISTENCE_COMPLETED` →
`BROADCAST_STARTED` → `BROADCAST_COMPLETED` → `STOPPED`

**Unit tests:**
```
tests/unit/
  test_schema_robustness.py        # CanonicalFixture construction + validation
  test_event_logging.py            # all 11 events emitted via MockEventSink
  test_imports.py
  test_batch_live_seams.py         # engine accepts mock GCS source + mock PubSub source
  test_reference_data_merge.py     # given API-Football + FootyStats data → correct CanonicalFixture
  test_cross_source_mapping.py     # fixture_id canonical key construction is deterministic
```

Run D5: `bash scripts/quickmerge.sh "feat: implement sports-reference-data-service engine" --no-pr`

---

## Sports Batch B — `sports-odds-data-service` (parallel)

**Analogy:** market-tick-data-service. Polls all 20 bookmakers for odds snapshots.

**Live connectivity (how we connect to bookmakers live):** See `unified-trading-codex/04-architecture/sports-live-odds-connectivity.md`. Summary: Odds API = REST poll (40–60s), no login. Exchanges = REST/stream API. Scrapers = browser + login/geo when needed; prefer Odds API where it covers the bookmaker.

**Engine architecture:**
```python
class OddsDataEngine:
    """
    Polls all 20 bookmakers for pre-match and live odds.
    Writes snapshots to GCS; publishes delta events to PubSub.
    Batch mode: historical odds download via OddsApiAdapter for a date range.
    Live mode: polls each bookmaker at configurable intervals (exchange: 5s, scraper: 60s).
    """

    def __init__(
        self,
        adapters: dict[str, OddsAdapter],  # bookmaker_key → adapter instance
        writer: BaseCloudWriter,
        sink: EventSink,
    ) -> None: ...

    async def snapshot_all_bookmakers(self, fixture_ids: list[str]) -> list[CanonicalOdds]:
        """Fetch odds from all active adapters concurrently. Partial failures logged, not raised."""
        ...

    async def run_live_polling(self) -> None:
        """Poll all adapters at their configured intervals. Writes deltas to PubSub."""
        ...
```

**Concurrency model:**
- Exchange adapters (Betfair, Smarkets, Matchbook, Betdaq): poll every 5 seconds — asyncio gather
- Bookmaker API adapters (Pinnacle, OddsApi): poll every 30 seconds
- Web scrapers: poll every 60 seconds, max 4 concurrent scrapers (rate limiting + bot detection)
- RAM guard: `psutil.virtual_memory().percent > 85` → reduce concurrent scrapers to 2

**GCS output schema:**
```
gs://sports-odds-data/
  snapshots/
    {date}/{fixture_id}/{bookmaker_key}/{timestamp_epoch_ms}.json   # CanonicalOdds
  latest/
    {fixture_id}/{bookmaker_key}/latest.json                        # latest snapshot per bookmaker
```

**PubSub output topic:** `sports-odds-updated`
**Message schema:** `{"fixture_id": "af:12345", "bookmaker_key": "betfair", "odds_changed": true, "timestamp_utc": "..."}`

**Config fields:**
```python
sports_odds_api_key: str               # Secret Manager — The Odds API
sports_betfair_api_key: str            # Secret Manager
sports_smarkets_api_key: str           # Secret Manager
sports_matchbook_username: str         # Secret Manager
sports_matchbook_api_key: str          # Secret Manager
sports_betdaq_api_key: str             # Secret Manager
sports_pinnacle_api_key: str           # Secret Manager
sports_onexbet_api_key: str            # Secret Manager
sports_odds_data_bucket: str           # GCS bucket
sports_odds_data_pubsub_topic: str
sports_scraper_poll_interval_s: int = 60
sports_exchange_poll_interval_s: int = 5
sports_max_concurrent_scrapers: int = 4
```

**Unit tests:**
```
tests/unit/
  test_schema_robustness.py
  test_event_logging.py
  test_imports.py
  test_batch_live_seams.py
  test_odds_engine_concurrent_polling.py    # mock all adapters; verify concurrent gather
  test_odds_engine_partial_failure.py       # one adapter raises BookmakerUnavailableError → rest still complete
  test_odds_engine_ram_guard.py             # psutil > 85% → reduces concurrent scrapers to 2
  test_gcs_snapshot_writes.py              # engine writes correct GCS paths
```

Run D5.

---

## Sports Batch B — `sports-odds-processing-service` (parallel with above)

**Analogy:** market-data-processing-service. Consumes raw odds snapshots → normalizes → detects arbitrage.

**Engine architecture:**
```python
class OddsProcessingEngine:
    """
    Consumes CanonicalOdds from GCS/PubSub.
    Computes:
      1. Implied probability normalization (remove bookmaker margin)
      2. Market consensus (weighted average across bookmakers)
      3. Arbitrage detection (sum of best back prices < 1.0 after commission)
    Mode-agnostic: batch processes historical snapshots; live subscribes to PubSub.
    """

    def process_odds_snapshot(
        self,
        odds_list: list[CanonicalOdds],
        fixture_id: str,
    ) -> ProcessedOddsOutput:
        """Process a full odds snapshot for one fixture. Returns normalized odds + arb opportunities."""
        ...

    def detect_arbitrage(
        self,
        odds_list: list[CanonicalOdds],
        min_return_pct: Decimal = Decimal("0.5"),
    ) -> list[ArbitrageOpportunity]:
        """
        Scan for arbitrage opportunities across bookmakers.
        Port logic from SPORTS_REPO/footballbets/arbitrage/analyze_bookmaker_vig.py.

        Algorithm:
        1. For each market (H2H, OVER_UNDER, etc.), find best back price per outcome across all bookmakers
        2. Compute total_implied_prob = sum(1/best_odds_per_outcome)
        3. If total_implied_prob < 1.0 (after exchange commission of 5%), yield ArbitrageOpportunity
        4. Compute expected_return_pct = (1 / total_implied_prob - 1) * 100
        """
        ...

    def compute_implied_probs(self, odds: CanonicalOdds) -> CanonicalOdds:
        """
        Remove bookmaker margin to get true implied probabilities.
        Uses multiplicative normalization: p_true = p_raw / sum(p_raw_all_outcomes).
        """
        ...

    def compute_market_consensus(self, odds_list: list[CanonicalOdds]) -> dict[str, Decimal]:
        """Weighted average of implied probs across bookmakers (weight by liquidity tier)."""
        ...
```

**Add to `unified-api-contracts/sports/canonical/`:**

`processed_odds.py`:
```python
class ProcessedOddsOutput(BaseModel):
    """Output of OddsProcessingEngine for one fixture snapshot."""
    fixture_id: str
    processed_at_utc: datetime
    normalized_odds: list[CanonicalOdds]          # margin-removed implied probs filled
    consensus_home_prob: Decimal | None
    consensus_draw_prob: Decimal | None
    consensus_away_prob: Decimal | None
    market_overround_avg: Decimal | None           # average across all bookmakers
    arbitrage_opportunities: list[ArbitrageOpportunity]
    bookmaker_coverage: int                        # number of distinct bookmakers with data
```

**GCS output:** `gs://sports-processed-odds/{date}/{fixture_id}/processed.json` — `ProcessedOddsOutput`
**PubSub topics:**
- `sports-processed-odds-updated` — all processed outputs
- `sports-arbitrage-detected` — only when `len(arbitrage_opportunities) > 0`

**Unit tests:**
```
tests/unit/
  test_schema_robustness.py
  test_event_logging.py
  test_imports.py
  test_arbitrage_detection.py         # known arb scenario (constructed odds) → correct opportunity
  test_no_arb_detection.py            # normal odds → empty arb list
  test_implied_prob_normalization.py  # sum of normalized probs == 1.0 (within Decimal precision)
  test_market_consensus.py            # weighted average is correct given mock odds list
  test_commission_adjusted_arb.py     # Betfair 5% commission is applied before arb check
```

Run D5.

---

## Sports Batch C — `features-sports-service` (wired end-to-end)

Phase 2 implemented all 14 calculators and the `FeaturePipeline`. This batch wires the service to:
- Subscribe to `sports-reference-data-updated` and `sports-processed-odds-updated` PubSub topics
- Fetch canonical data from GCS (reference data + processed odds)
- Run `FeaturePipeline.compute()` → `SportsFeatureVector`
- Write to `gs://sports-features/{date}/{fixture_id}/features.json`
- Publish to `sports-features-computed` PubSub topic

**Engine wiring (add to existing Phase 2 service):**
```python
class SportsFeaturesEngine:
    """
    Orchestrates the full feature computation pipeline.

    Live mode: subscribes to PubSub, computes features on each update event.
    Batch mode: iterates fixture list from GCS, computes features for all fixtures in date range.
    """

    def __init__(
        self,
        data_source: LiveDataSource | BatchDataSource,
        pipeline: FeaturePipeline,
        writer: BaseCloudWriter,
        sink: EventSink,
    ) -> None: ...

    async def process_fixture(self, fixture_id: str) -> SportsFeatureVector:
        """Fetch all required data, run pipeline, return feature vector."""
        reference_data = await self._data_source.get_canonical_fixture(fixture_id)
        processed_odds = await self._data_source.get_processed_odds(fixture_id)
        context = FeatureContext(
            fixture=reference_data,
            odds=processed_odds,
            # ... additional context
        )
        return self._pipeline.compute(reference_data.fixture, context)
```

**New config fields:**
```python
sports_features_bucket: str
sports_features_pubsub_topic: str
sports_reference_data_subscription: str      # PubSub subscription to read from
sports_processed_odds_subscription: str
```

**Unit tests to add:**
```
tests/unit/
  test_engine_wiring.py              # mock data source → engine → mock writer → verify GCS path
  test_engine_live_seam.py           # PubSub message → fixture_id extracted → process_fixture called
  test_engine_batch_seam.py          # date range → fixture list from GCS → process each
  test_feature_vector_completeness.py  # all 14 feature groups populated in output
```

Run D5.

---

## Sports Batch D — `sports-strategy-service`

**Two strategy modes in the same service, selected by config:**
- `--strategy arbitrage` — scans arb opportunities, sizes bets, emits BetOrder
- `--strategy ml` — loads ML model (from `ml-inference-service` via PubSub), applies features, emits BetOrder

```python
class SportsStrategyEngine:
    """
    Mode-agnostic sports strategy engine.
    Strategy type selected by config (ARBITRAGE | ML_MODEL).
    Receives features + opportunities via PubSub, emits BetOrder to PubSub.
    """

    def __init__(
        self,
        strategy: ArbitrageStrategy | MLStrategy,
        data_source: LiveDataSource | BatchDataSource,
        sink: EventSink,
    ) -> None: ...

    async def process_signal(
        self,
        fixture_id: str,
        processed_odds: ProcessedOddsOutput,
        feature_vector: SportsFeatureVector,
    ) -> list[BetOrder]:
        """Generate bet orders from current odds + features. Returns empty list if no signal."""
        ...
```

**ArbitrageStrategy:**
```python
class ArbitrageStrategy:
    """
    Generates BetOrder from ArbitrageOpportunity.

    Risk rules (configurable via UnifiedCloudConfig):
    - min_return_pct: minimum expected return to act on (default 0.5%)
    - max_stake_per_bet_gbp: maximum stake per individual leg
    - max_exposure_per_fixture_gbp: total max across all legs of one arb
    - kelly_fraction: Kelly criterion fraction for stake sizing (default 0.25 = quarter-Kelly)
    """

    def generate_orders(
        self,
        opportunity: ArbitrageOpportunity,
        available_balance: dict[str, Decimal],  # bookmaker_key → available balance
    ) -> list[BetOrder]:
        """
        Generate BetOrder list for all legs of the arbitrage.
        One BetOrder per leg (each on a different bookmaker/exchange).
        Applies Kelly stake sizing, balance checks, and risk limits before emitting.
        """
        ...
```

**MLStrategy:**
```python
class MLStrategy:
    """
    Generates BetOrder from ML model predictions (BettingSignal from ml-inference-service).

    Consumes from `sports-ml-signals` PubSub topic (published by ml-inference-service).
    Converts signal strength + market odds → BetOrder with Kelly-sized stake.
    """

    def generate_orders(
        self,
        signal: BettingSignal,
        market_odds: list[CanonicalOdds],
        available_balance: dict[str, Decimal],
    ) -> list[BetOrder]:
        """Generate order if signal has sufficient edge vs market implied probability."""
        ...
```

**BettingSignal** (add to `unified-api-contracts/sports/canonical/betting.py`):
```python
class BettingSignal(BaseModel):
    """ML model prediction for a fixture outcome."""
    signal_id: str
    fixture_id: str
    model_id: str
    model_version: str
    predicted_outcome: str            # "HOME_WIN" | "DRAW" | "AWAY_WIN" | "OVER" | "UNDER"
    confidence: Decimal               # 0.0–1.0
    predicted_home_win_prob: Decimal
    predicted_draw_prob: Decimal
    predicted_away_win_prob: Decimal
    edge_vs_market: Decimal | None    # predicted_prob - market_implied_prob
    source: SignalSource              # ML_MODEL
    generated_at_utc: datetime
```

**Config fields:**
```python
sports_strategy_mode: str = "arbitrage"           # "arbitrage" | "ml"
sports_arb_min_return_pct: Decimal = Decimal("0.5")
sports_arb_max_stake_gbp: Decimal = Decimal("100")
sports_arb_max_exposure_gbp: Decimal = Decimal("500")
sports_kelly_fraction: Decimal = Decimal("0.25")
sports_ml_min_edge: Decimal = Decimal("0.03")     # minimum edge vs market to act
sports_ml_signals_subscription: str               # PubSub sub for ml-inference-service output
sports_strategy_orders_topic: str                 # PubSub topic for BetOrder output
sports_features_subscription: str
sports_processed_odds_subscription: str
```

**PubSub input:** `sports-features-computed` + `sports-arbitrage-detected`
**PubSub output:** `sports-bet-orders`
**GCS output:** `gs://sports-strategy/{date}/{fixture_id}/orders.json` — list of `BetOrder`

**Unit tests:**
```
tests/unit/
  test_schema_robustness.py
  test_event_logging.py
  test_imports.py
  test_arbitrage_strategy_order_generation.py     # known arb → correct BetOrder list + stakes
  test_arbitrage_strategy_no_signal.py            # return_pct < min → empty list
  test_arbitrage_strategy_balance_check.py        # insufficient balance → stake reduced / order dropped
  test_arbitrage_kelly_sizing.py                  # Kelly fraction applied correctly
  test_ml_strategy_above_edge_threshold.py        # edge > min_edge → BetOrder generated
  test_ml_strategy_below_edge_threshold.py        # edge < min_edge → empty list
  test_ml_strategy_kelly_sizing.py
  test_strategy_engine_selects_correct_strategy.py  # config "arbitrage" → ArbitrageStrategy; "ml" → MLStrategy
```

Run D5.

---

## Sports Batch E — `sports-execution-service`

**Analogy:** execution-service. Receives BetOrder from PubSub, places on exchanges/bookmakers.

```python
class SportsExecutionEngine:
    """
    Receives BetOrder from PubSub. Routes to correct USEI adapter. Returns BetExecution.

    Lifecycle:
      PLACED → MATCHED (full/partial) → SETTLED
      PLACED → UNMATCHED → EXPIRED (if not matched before event kickoff)

    Slippage protection: if available odds < BetOrder.max_acceptable_odds, cancel and log.
    Circuit breaker: if >3 BetRejectedError in 60s for same bookmaker → disable that bookmaker for 5 min.
    """

    def __init__(
        self,
        adapters: dict[str, BettingAdapter],  # bookmaker_key → adapter (exchanges only)
        odds_adapters: dict[str, OddsAdapter],  # bookmaker_key → for pre-flight price check
        writer: BaseCloudWriter,
        sink: EventSink,
    ) -> None: ...

    async def execute_order(self, order: BetOrder) -> BetExecution:
        """
        Execute a single bet order.

        Steps:
        1. Pre-flight price check: fetch current odds — if worse than max_acceptable_odds, reject with OddsChangedError
        2. Place bet via BettingAdapter.place_bet(order)
        3. Write BetExecution to GCS
        4. Publish BetExecution to PubSub
        5. Log BROADCAST_COMPLETED lifecycle event
        """
        ...

    async def monitor_open_bets(self) -> None:
        """Periodic check of PLACED bets. Update status to MATCHED/SETTLED/EXPIRED."""
        ...
```

**BetExecution** (already in AC from Phase 1):
```python
class BetExecution(BaseModel):
    execution_id: str
    order_id: str
    fixture_id: str
    bookmaker: BookmakerInfo
    status: BetStatus                  # PLACED | MATCHED | PARTIALLY_MATCHED | SETTLED | CANCELLED | REJECTED | EXPIRED
    placed_at_utc: datetime
    matched_at_utc: datetime | None
    settled_at_utc: datetime | None
    requested_odds: Decimal
    matched_odds: Decimal | None
    stake: Decimal
    matched_stake: Decimal | None
    pnl: Decimal | None                # set on SETTLED
    rejection_reason: str | None
```

**Circuit breaker implementation:**
```python
class BookmakerCircuitBreaker:
    """
    Per-bookmaker circuit breaker.
    Opens after 3 BetRejectedError in 60s.
    Half-opens after 5 min cool-down.
    Logs CIRCUIT_BREAKER_OPEN / CIRCUIT_BREAKER_CLOSED lifecycle events.
    """
    ...
```

**Config fields:**
```python
sports_execution_bet_orders_subscription: str
sports_execution_executions_topic: str
sports_execution_executions_bucket: str
sports_execution_circuit_breaker_threshold: int = 3
sports_execution_circuit_breaker_window_s: int = 60
sports_execution_circuit_breaker_cooldown_s: int = 300
sports_execution_active_bookmakers: list[str]   # which bookmakers to route orders to
sports_execution_max_concurrent_orders: int = 10
```

**PubSub input:** `sports-bet-orders`
**PubSub output:** `sports-bet-executions`
**GCS output:** `gs://sports-executions/{date}/{execution_id}.json` — `BetExecution`

**Unit tests:**
```
tests/unit/
  test_schema_robustness.py
  test_event_logging.py
  test_imports.py
  test_execution_engine_successful_bet.py          # mock BettingAdapter.place_bet → BetExecution(PLACED)
  test_execution_engine_slippage_rejection.py      # odds worse than max_acceptable → OddsChangedError
  test_execution_engine_bet_rejected.py            # adapter raises BetRejectedError → BetExecution(REJECTED)
  test_execution_engine_circuit_breaker_opens.py   # 3 rejections in 60s → bookmaker disabled
  test_execution_engine_circuit_breaker_resets.py  # after cooldown → orders resume
  test_execution_engine_concurrent_orders.py       # max 10 concurrent → 11th queues
  test_monitor_open_bets_matched.py                # PLACED → MATCHED on price match
  test_monitor_open_bets_expired.py                # PLACED + kickoff passed → EXPIRED
```

Run D5.

---

## Integration Layer Verification

### L0 — Contract Alignment (verify in unified-api-contracts tests)
```bash
cd unified-api-contracts
pytest tests/unit/sports/ -v -m unit
# Must pass: all canonical schemas, BookmakerRegistry, SportsFeatureVector, errors
```

### L1 — Schema Robustness (per-service, already added in Batch A–E Step B)
```bash
for svc in sports-reference-data-service sports-odds-data-service sports-odds-processing-service sports-strategy-service sports-execution-service; do
  cd $WORKSPACE_ROOT/$svc
  pytest tests/unit/test_schema_robustness.py -v -m unit
done
```

### L2 — Infra Verification (after sandbox deploy)
```bash
# Add sports infra checks to deployment-engine/scripts/verify_infra.py:
# - GCS buckets: sports-reference-data, sports-odds-data, sports-processed-odds, sports-features, sports-strategy, sports-executions
# - PubSub topics: sports-reference-data-updated, sports-odds-updated, sports-arbitrage-detected, sports-features-computed, sports-bet-orders, sports-bet-executions
# - Secret Manager: all 8 sports API keys present
curl http://localhost:8001/infra/health | jq '.sports'
# All checks: "pass"
```

### L3a — Pipeline Smoke Tests (add to `system-integration-tests`)
```bash
cd system-integration-tests
pytest -m smoke -k "sports" -v
```

Add `tests/smoke/test_sports_pipeline_smoke.py`:
```python
@pytest.mark.smoke
async def test_sports_reference_data_writes_to_gcs(mock_gcs, mock_api_football):
    """Fixture data fetched → CanonicalFixture written to GCS."""
    ...

@pytest.mark.smoke
async def test_sports_odds_snapshot_triggers_processing(mock_gcs, mock_pubsub):
    """OddsDataEngine publishes PubSub → ProcessingEngine subscribes → ProcessedOddsOutput written."""
    ...

@pytest.mark.smoke
async def test_sports_arbitrage_opportunity_triggers_order(mock_gcs, mock_pubsub):
    """ArbitrageOpportunity published → StrategyEngine generates BetOrder → BetOrder published."""
    ...

@pytest.mark.smoke
async def test_sports_bet_order_reaches_execution(mock_pubsub, mock_betting_adapter):
    """BetOrder published → ExecutionEngine routes to correct adapter → BetExecution written."""
    ...
```

### L3b — Full E2E (after L3a green)
```bash
pytest -m full_e2e -k "sports" -v
```

Add `tests/e2e/test_sports_full_pipeline.py`:
```python
@pytest.mark.full_e2e
async def test_sports_arbitrage_pipeline_end_to_end(
    real_gcs_client,
    mock_bookmaker_adapters,
    mock_pubsub,
):
    """
    Full pipeline from fixture ingestion to bet execution:
    1. ReferenceDataEngine fetches fixture → GCS + PubSub
    2. OddsDataEngine fetches odds from mock adapters → GCS + PubSub
    3. OddsProcessingEngine normalizes + detects arb → GCS + PubSub
    4. SportsFeaturesEngine computes features → GCS + PubSub
    5. SportsStrategyEngine generates BetOrder → PubSub
    6. SportsExecutionEngine routes order → mock BettingAdapter.place_bet called
    Assert: BetExecution with status=PLACED written to GCS
    """
    ...
```

---

## Post-Refactor Sequence — Sports Vertical

```
ALL SPORTS BATCHES A-E GREEN (D5 each) + Final QG sweep
  ↓ Step 1: Sandbox deploy — all 5 sports services via deployment-engine CLI
            --service sports-reference-data-service --mode batch --date 2026-01-01
  ↓ Step 2: GET /infra/health → sports checks all pass
  ↓ Step 3: pytest -m smoke -k "sports" — happy path, <5 min
  ↓ Step 4: pytest -m full_e2e -k "sports" — corner cases, 15–30 min
  ↓ Step 5: Declare sports vertical healthy → merge staging → main
```

---

## Final QG Sweep (after all batches D5 green)

5 parallel agents:
- Upgrade `reportAny` from `'warning'` to `'error'` in all 5 sports services + USEI + UMI sports; fix every violation
- Final `rg` sweep: zero `from footballbets`, zero `os.getenv(KEY, '')`, zero silent excepts, zero `dict[str, Any]` at service boundaries
- Verify all 11 lifecycle events in every service's `test_event_logging.py`
- Verify `sports_execution_active_bookmakers` config starts with `["betfair", "smarkets"]` only (exchange-only for initial rollout — reduce regulatory risk)
- Run QG on all sports repos; record final coverage % in `workspace-manifest.json`

---

## Done Criteria

- [ ] `sports-reference-data-service` D5 passes — fixtures/teams/leagues written to GCS
- [ ] `sports-odds-data-service` D5 passes — all 20 bookmaker adapters wired; concurrency + RAM guard working
- [ ] `sports-odds-processing-service` D5 passes — arbitrage detection verified against known scenarios
- [ ] `features-sports-service` D5 passes — all 14 calculators computing from canonical data; `SportsFeatureVector` fully populated
- [ ] `sports-strategy-service` D5 passes — both arbitrage and ML strategy modes verified with unit tests
- [ ] `sports-execution-service` D5 passes — circuit breaker, slippage protection, lifecycle tracking all verified
- [ ] All 11 lifecycle events in `test_event_logging.py` for every service
- [ ] Zero `from footballbets` imports anywhere in the unified trading system (complete separation)
- [ ] Zero `postgresql|psycopg2|sqlalchemy` imports in any pipeline service
- [ ] Zero `Any` types at service boundaries (documented exceptions in `QUALITY_GATE_BYPASS_AUDIT.md`)
- [ ] L0 contract alignment tests pass in `unified-api-contracts`
- [ ] L1 schema robustness tests pass in all 5 services
- [ ] Sports infra checks added to `deployment-engine/scripts/verify_infra.py`
- [ ] L3a smoke tests pass (`pytest -m smoke -k "sports"`)
- [ ] L3b full E2E tests pass (`pytest -m full_e2e -k "sports"`)
- [ ] Sandbox deploy stable for all 5 sports services
- [ ] `sports-execution-service` initial rollout restricted to exchange adapters only (Betfair, Smarkets)
- [ ] Declared healthy; sports vertical v1.0.0

---

## Key Files

- `unified-api-contracts/unified_api_contracts/sports/canonical/processed_odds.py` — ProcessedOddsOutput (create)
- `unified-api-contracts/unified_api_contracts/sports/canonical/betting.py` — BettingSignal (add)
- `sports-reference-data-service/sports_reference_data_service/engine.py` — ReferenceDataEngine (implement)
- `sports-odds-data-service/sports_odds_data_service/engine.py` — OddsDataEngine (implement)
- `sports-odds-processing-service/sports_odds_processing_service/engine.py` — OddsProcessingEngine (implement)
- `features-sports-service/features_sports_service/engine.py` — SportsFeaturesEngine (implement)
- `sports-strategy-service/sports_strategy_service/engine.py` — SportsStrategyEngine + ArbitrageStrategy + MLStrategy (implement)
- `sports-strategy-service/sports_strategy_service/arbitrage.py` — ArbitrageStrategy (implement)
- `sports-strategy-service/sports_strategy_service/ml_strategy.py` — MLStrategy (implement)
- `sports-execution-service/sports_execution_service/engine.py` — SportsExecutionEngine + BookmakerCircuitBreaker (implement)
- `system-integration-tests/tests/smoke/test_sports_pipeline_smoke.py` — L3a tests (create)
- `system-integration-tests/tests/e2e/test_sports_full_pipeline.py` — L3b tests (create)
- `deployment-engine/scripts/verify_infra.py` — add sports GCS/PubSub/Secret checks
- `unified-trading-codex/04-architecture/batch-live-symmetry.md` — batch/live seam pattern
- `unified-trading-codex/03-observability/lifecycle-events.md` — 11 required events
- `.cursor/rules/delete-deprecated.mdc` — no backward compat, no parallel code paths
