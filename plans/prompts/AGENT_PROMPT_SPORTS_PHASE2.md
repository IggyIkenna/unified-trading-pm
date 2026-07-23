# Agent Prompt — Sports Phase 2: Adapter & Library Implementation

> Paste this entire prompt into a new agent session to execute Sports Phase 2. REQUIRES Sports Phase 1 fully complete.
> Verify preconditions before starting. This phase is UNIT TESTS ONLY — VCR cassettes for HTTP, no live API calls, no
> real auth.

---

Follow all workspace cursor rules in .cursorrules. No summary docs (no-summary-docs.mdc). uv not pip. quickmerge not git
push. basedpyright <dir>/ not basedpyright. Delete deprecated code; no parallel code paths. Search unified libraries
before implementing anything new.

WORKSPACE_ROOT=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos
SPORTS_REPO=/Users/ikennaigboaka/Documents/repos/other_repos/sports-betting-services All
Python/pytest/ruff/basedpyright/QG commands: cd WORKSPACE_ROOT && source .venv-workspace/bin/activate first.

---

## Standard of Work — Citadel Audit-Worthy

> **When in doubt, assume a senior quant engineer at a top-tier fund (Citadel, Two Sigma, DE Shaw) is reviewing every
> PR. Build accordingly.**

This means — no exceptions, no shortcuts:

- **No silent errors** — every `except` block must reraise, raise a typed error, or log at ERROR + reraise. `pass` is a
  build failure.
- **No empty fallbacks** — `os.getenv(KEY, '')` silently fails in production; forbidden. Use `UnifiedCloudConfig` or
  `os.environ[KEY]` (raises on missing).
- **No untyped code** — every function parameter, return type, and class field has a type annotation. `Any` is forbidden
  unless documented in `QUALITY_GATE_BYPASS_AUDIT.md`.
- **No TODO comments** in production code — open a GitHub issue with a link instead.
- **No magic numbers/strings** — use constants from UCI or AC (`BookmakerRegistry`, `OddsType`).
- **No skipped tests** — every skip must have a linked issue and `xfail` marker.
- **Every public function/class** has a docstring.
- **Every secret** through Secret Manager. Every config through `UnifiedCloudConfig`.
- If it would fail a Citadel code review, it is not done.

---

## Preconditions (verify ALL before starting)

```bash
# 1. Phase 1 complete — all AC sports schemas importable
python -c "from unified_api_contracts.sports import CanonicalFixture, CanonicalOdds, BetOrder, ArbitrageOpportunity, BookmakerRegistry"

# 2. BookmakerRegistry has 20 entries
python -c "from unified_api_contracts.sports.canonical.bookmaker import BookmakerRegistry; assert len(BookmakerRegistry) == 20, f'Got {len(BookmakerRegistry)}'"

# 3. USEI upgraded — no old BaseSportsAdapter with dict[str,str]
rg 'dict\[str, str\]' unified-sports-execution-interface/unified_sports_execution_interface/  # must be zero

# 4. All 20 adapter stubs exist
ls unified-sports-execution-interface/unified_sports_execution_interface/adapters/exchanges/
ls unified-sports-execution-interface/unified_sports_execution_interface/adapters/scrapers/

# 5. unified-api-contracts D5 passed (check latest CI status)
python -c "import unified_api_contracts"

# 6. All 5 new service repos scaffold exists
python -c "import sports_reference_data_service"
python -c "import sports_odds_data_service"
python -c "import sports_odds_processing_service"
python -c "import sports_strategy_service"
python -c "import sports_execution_service"
```

If any check fails: STOP. Complete Sports Phase 1 first.

---

## SSOT

| Source                   | Path                                                                            |
| ------------------------ | ------------------------------------------------------------------------------- |
| Sports AC schemas        | `unified-api-contracts/unified_api_contracts/sports/`                           |
| BookmakerRegistry        | `unified-api-contracts/unified_api_contracts/sports/canonical/bookmaker.py`     |
| USEI base protocols      | `unified-sports-execution-interface/unified_sports_execution_interface/base.py` |
| Existing feature logic   | `SPORTS_REPO/footballbets/features/` — 14 calculators to port                   |
| Existing odds downloader | `SPORTS_REPO/footballbets/arbitrage/odds.py` — OddsApiAdapter source of truth   |
| Existing client impls    | `SPORTS_REPO/footballbets/clients/` — adapter implementations to port           |
| Tier architecture        | `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md`                   |
| Batch/live symmetry      | `unified-trading-/codex/04-architecture/batch-live-symmetry.md`                 |

---

## Testing Standard — VCR Cassettes for All HTTP

Every HTTP call in every adapter test uses VCR cassettes (pytest-recording or vcrpy):

```python
@pytest.mark.unit
@pytest.mark.vcr  # records/replays HTTP at tests/cassettes/<test_name>.yaml
async def test_betfair_get_odds_returns_canonical_odds(betfair_adapter):
    odds = await betfair_adapter.get_odds("af:12345", [OddsType.H2H])
    assert len(odds) > 0
    assert all(isinstance(o, CanonicalOdds) for o in odds)
    assert all(o.bookmaker.key == "betfair" for o in odds)
```

Cassette files live in `tests/cassettes/`. Record once from real API (or hand-craft realistic JSON/HTML). After
recording, tests NEVER make live calls — CI always uses cassettes.

For Playwright scrapers, use `responses` library or hand-crafted HTML fixtures in `tests/fixtures/html/`:

```python
@pytest.mark.unit
async def test_skybet_parses_html_odds(skybet_adapter, skybet_html_fixture):
    """skybet_html_fixture loads a real HTML snapshot from tests/fixtures/html/skybet_match_page.html"""
    odds = skybet_adapter._parse_odds_from_html(skybet_html_fixture, "af:12345")
    assert isinstance(odds[0], CanonicalOdds)
    assert odds[0].bookmaker.key == "skybet"
```

---

## Bottom-Up Development Rule

If any adapter needs new error types (e.g., `BookmakerUnavailableError`, `BetRejectedError`, `OddsChangedError`): → Add
to `unified-api-contracts/sports/errors.py` FIRST → Run D5 on `unified-api-contracts` before using in USEI

If any new config field is needed (e.g., `sports_betfair_api_key`, `sports_playwright_headless`): → Add to
`unified-config-interface` FIRST → Run D5 on `unified-config-interface` before using in adapters

---

## Testing Progression

| Step         | Command                    | Catches                                   |
| ------------ | -------------------------- | ----------------------------------------- |
| Import smoke | `python -c "import <pkg>"` | Broken `__init__`, circular imports       |
| D1           | `--lint-only`              | Syntax, formatting, import order          |
| D2           | `--unit-only`              | Type errors, unit test failures           |
| D3           | `--qg-only`                | Coverage gaps — no git, safe to retry     |
| D4           | `--quick`                  | Full QG + git ops, no act                 |
| D5           | (no flags)                 | Full pipeline — the only gate that counts |

---

## Execution Order

Steps 1, 2, 3, 4 run in parallel. Step 5 (features-sports-service) requires Steps 1-4 complete.

---

### Step 1 — Add Sports Error Types to T0 (before any adapter implementation)

Add `unified-api-contracts/unified_api_contracts/sports/errors.py`:

```python
"""Sports-specific typed exceptions for the betting vertical."""


class SportsError(Exception):
    """Base error for all sports betting errors."""


class BookmakerUnavailableError(SportsError):
    """Bookmaker API or scrape target is unreachable or returned an error response."""
    def __init__(self, bookmaker_key: str, reason: str) -> None:
        super().__init__(f"Bookmaker {bookmaker_key!r} unavailable: {reason}")
        self.bookmaker_key = bookmaker_key
        self.reason = reason


class BetRejectedError(SportsError):
    """Bookmaker rejected the bet order (price moved, account restricted, etc.)."""
    def __init__(self, order_id: str, reason: str, bookmaker_key: str) -> None:
        super().__init__(f"Bet {order_id!r} rejected by {bookmaker_key!r}: {reason}")
        self.order_id = order_id
        self.reason = reason
        self.bookmaker_key = bookmaker_key


class OddsChangedError(SportsError):
    """Odds changed beyond acceptable slippage before order was placed."""
    def __init__(self, requested: float, available: float) -> None:
        super().__init__(f"Odds changed: requested {requested}, available {available}")
        self.requested = requested
        self.available = available


class MarketClosedError(SportsError):
    """Market has closed or been suspended before order placement."""


class ScraperError(SportsError):
    """Web scraper failed to extract odds (page structure changed, bot detection, etc.)."""
    def __init__(self, bookmaker_key: str, url: str, reason: str) -> None:
        super().__init__(f"Scraper failed for {bookmaker_key!r} at {url!r}: {reason}")
        self.bookmaker_key = bookmaker_key
        self.url = url
        self.reason = reason


class FixtureNotFoundError(SportsError):
    """Fixture ID not found on this bookmaker or data source."""
    def __init__(self, fixture_id: str, bookmaker_key: str) -> None:
        super().__init__(f"Fixture {fixture_id!r} not found at {bookmaker_key!r}")
        self.fixture_id = fixture_id
        self.bookmaker_key = bookmaker_key
```

Export from `unified_api_contracts/sports/__init__.py`. Write unit tests. Run `unified-api-contracts` D5.

---

### Step 2 — Implement Exchange Adapters (4 parallel sub-agents)

**2A — BetfairAdapter** (`adapters/exchanges/betfair.py`)

Dependencies to add to `unified-sports-execution-interface/pyproject.toml`:

```toml
"betfairlightweight>=3.14,<4.0"
```

Implementation requirements:

- `get_odds()`: calls `betfairlightweight` client → `list_runner_book()` → parses available back/lay prices → returns
  `list[CanonicalOdds]`
- Map Betfair market types to `OddsType`: `MATCH_ODDS` → `H2H`, `OVER_UNDER_25` → `OVER_UNDER`, etc.
- `place_bet()`: constructs `PlaceInstruction` → `place_orders()` → returns `BetExecution`
- `cancel_bet()`: calls `cancel_orders()`
- `get_balance()`: calls `get_account_funds()`
- Auth: `api_key` via `UnifiedCloudConfig.sports_betfair_api_key` (Secret Manager) — NEVER hardcoded
- All methods wrapped with `@with_retry(max_attempts=3, backoff=2.0)` from unified-trading-services
- Every HTTP error → `BookmakerUnavailableError`; every bet rejection → `BetRejectedError`

VCR cassettes at `tests/cassettes/betfair_*.yaml`. Tests:

```
test_betfair_get_odds_h2h.py
test_betfair_place_bet_success.py
test_betfair_place_bet_rejection.py
test_betfair_cancel_bet.py
test_betfair_get_balance.py
test_betfair_maps_market_types.py
```

**2B — SmarketsAdapter** (`adapters/exchanges/smarkets.py`)

Smarkets REST API at `https://api.smarkets.com/v3/`. Requires `aiohttp`.

- `get_odds()`: `GET /events/?sport=football` → filter by fixture → `GET /markets/{id}/quotes/` → `list[CanonicalOdds]`
- `place_bet()`: `POST /orders/` with `{"market": ..., "quantity": ..., "price": ..., "side": "buy"|"sell"}`
- Auth: Bearer token via `UnifiedCloudConfig.sports_smarkets_api_key`
- Rate limit: 10 req/s — implement token-bucket rate limiter in adapter

**2C — MatchbookAdapter** (`adapters/exchanges/matchbook.py`)

Matchbook REST API at `https://api.matchbook.com/edge/rest/`.

- `get_odds()`: `GET /events?sport=soccer` → `GET /events/{id}/markets` → parse runners → `list[CanonicalOdds]`
- `place_bet()`: `POST /offers`
- Auth: `UnifiedCloudConfig.sports_matchbook_username` + `sports_matchbook_api_key` (Basic Auth)

**2D — BetdaqAdapter** (`adapters/exchanges/betdaq.py`)

Betdaq REST API at `https://api.betdaq.com/v2.0/`.

- `get_odds()`: `GET /Sport/GetTopLevelEvents` → `GET /Market/GetPricesForMarkets` → parse
- `place_bet()`: `POST /Betting/PlaceOrdersWithReceipt`
- Auth: `UnifiedCloudConfig.sports_betdaq_api_key` + `sports_betdaq_username`

---

### Step 3 — Implement Bookmaker API Adapters (2 parallel sub-agents)

**3A — PinnacleAdapter** (`adapters/bookmaker_api/pinnacle.py`)

Pinnacle Sports API at `https://api.pinnacle.com/v1/`.

- `get_odds()`: `GET /odds?sportId=29&leagueIds=...` (soccer sportId=29) → parse lines → `list[CanonicalOdds]`
- `get_fixtures_with_odds()`: `GET /fixtures?sportId=29&leagueIds=...`
- Read-only (odds provider only, no bet placement via API)
- Map Pinnacle `moneyline` → `H2H`, `totals` → `OVER_UNDER`, `spreads` → `ASIAN_HANDICAP`
- Auth: `UnifiedCloudConfig.sports_pinnacle_api_key` (HTTP Basic)
- Rate limit: 1 req/s on free tier — implement rate limiter

**3B — OddsApiAdapter** (`adapters/aggregator/odds_api.py`)

Port from `SPORTS_REPO/footballbets/arbitrage/odds.py`. This adapter wraps The Odds API v4.

Key differences from the existing implementation:

- Remove PostgreSQL storage — return `list[CanonicalOdds]` directly
- Remove `ThreadPoolExecutor` — use `asyncio` + `aiohttp`
- Remove hardcoded API key — use `UnifiedCloudConfig.sports_odds_api_key`
- Keep rate limiting logic (1 req/s free tier, 10 req/s paid)

```python
class OddsApiAdapter:
    """
    The Odds API v4 adapter.

    Covers 15+ bookmakers in a single request: Bet365, William Hill, Ladbrokes,
    Betway, 888Sport, Unibet, DraftKings, FanDuel, BetMGM, Paddy Power, Coral,
    Sky Bet, Betfred, BetVictor, BoyleSports.

    Base URL: https://api.the-odds-api.com/v4/
    """

    BASE_URL = "https://api.the-odds-api.com/v4"
    SPORT_KEY = "soccer"

    async def get_odds(
        self,
        fixture_id: str,
        markets: list[OddsType],
    ) -> list[CanonicalOdds]:
        """
        Fetch odds from The Odds API, expanding each bookmaker into a separate CanonicalOdds.
        One CanonicalOdds per bookmaker per market.
        """
        ...

    def _map_odds_api_bookmaker(self, key: str) -> BookmakerInfo | None:
        """Map The Odds API bookmaker key to BookmakerRegistry entry."""
        ODDS_API_KEY_MAP: dict[str, str] = {
            "betfair": "betfair",
            "williamhill": "williamhill",
            "ladbrokes": "ladbrokes",
            "paddypower": "paddypower",
            "skybet": "skybet",
            "coral": "coral",
            "betway": "betway",
            "unibet": "unibet",
            "bet365": "bet365",
            "888sport": "bet888sport",
            "betfred": "betfred",
            "betvictor": "betvictor",
            "boylesports": "boylesports",
            "draftkings": "draftkings",
            "fanduel": "fanduel",
            "betmgm": "betmgm",
        }
        canonical_key = ODDS_API_KEY_MAP.get(key)
        return BookmakerRegistry.get(canonical_key)
```

---

### Step 4 — Implement Scraper Adapters (4 parallel sub-agents, 3-4 scrapers each)

**Dependencies to add to `unified-sports-execution-interface/pyproject.toml`:**

```toml
"playwright>=1.40,<2.0",
"httpx>=0.27,<1.0",
"beautifulsoup4>=4.12,<5.0",
"lxml>=5.0,<6.0",
```

**Scraper architecture pattern (all 13 scrapers follow this):**

```python
"""Sky Bet scraper adapter — extracts live odds via Playwright."""

import asyncio
from decimal import Decimal

from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, async_playwright

from unified_api_contracts.sports import CanonicalOdds, OddsType
from unified_api_contracts.sports.canonical.bookmaker import BookmakerRegistry
from unified_api_contracts.sports.errors import ScraperError


class SkyBetAdapter:
    """
    SkyBet odds scraper.

    Uses Playwright (headless Chromium) to extract pre-match odds.
    Bot-detection mitigations: random delays, realistic user-agent, stealth mode.
    Only supports OddsAdapter (read-only) — SkyBet does not support API bet placement.
    """

    BASE_URL = "https://www.skybet.com/football"
    BOOKMAKER = BookmakerRegistry["skybet"]

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless

    async def get_odds(
        self,
        fixture_id: str,
        markets: list[OddsType],
    ) -> list[CanonicalOdds]:
        """Scrape SkyBet odds for a fixture. Raises ScraperError on failure."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self._headless)
            try:
                page = await browser.new_page()
                await page.set_extra_http_headers({"User-Agent": self._user_agent()})
                url = self._build_url(fixture_id)
                await page.goto(url, wait_until="networkidle", timeout=30_000)
                html = await page.content()
                return self._parse_odds_from_html(html, fixture_id, markets)
            except Exception as exc:
                raise ScraperError(
                    bookmaker_key="skybet",
                    url=self.BASE_URL,
                    reason=str(exc),
                ) from exc
            finally:
                await browser.close()

    def _parse_odds_from_html(
        self,
        html: str,
        fixture_id: str,
        markets: list[OddsType],
    ) -> list[CanonicalOdds]:
        """
        Parse HTML from SkyBet match page.

        The HTML structure (as of Feb 2026) uses:
        - `.market-container` divs for each market type
        - `.outcome-button` with `data-odds` attribute (decimal format)
        Subclass or override if Sky Bet changes their markup.
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[CanonicalOdds] = []
        # ... parsing logic ...
        return results

    def _build_url(self, fixture_id: str) -> str:
        """Build SkyBet URL from canonical fixture_id. Override in tests with mock URL."""
        raise NotImplementedError("Implement URL construction in Phase 2")

    @staticmethod
    def _user_agent() -> str:
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

**Scraper test pattern (HTML fixture files):**

```
tests/
  fixtures/
    html/
      skybet_match_page.html       # saved real HTML from a SkyBet match page
      coral_match_page.html
      paddy_power_match_page.html
      # ... one per scraper
  unit/
    scrapers/
      test_skybet_adapter.py
      test_coral_adapter.py
      # ... one per scraper
```

Each scraper test:

```python
@pytest.fixture
def skybet_html(tmp_path) -> str:
    return (Path("tests/fixtures/html/skybet_match_page.html")).read_text()

@pytest.mark.unit
def test_skybet_parses_h2h_odds(skybet_html):
    adapter = SkyBetAdapter(headless=True)
    odds = adapter._parse_odds_from_html(skybet_html, "af:12345", [OddsType.H2H])
    assert len(odds) >= 1
    assert odds[0].bookmaker.key == "skybet"
    assert odds[0].market == OddsType.H2H
    assert odds[0].home_odds is not None
    assert odds[0].away_odds is not None
    assert isinstance(odds[0].home_odds, Decimal)

@pytest.mark.unit
async def test_skybet_raises_scraper_error_on_bad_html():
    adapter = SkyBetAdapter(headless=True)
    with pytest.raises(ScraperError):
        adapter._parse_odds_from_html("<html></html>", "af:12345", [OddsType.H2H])
```

**Sub-agent 4A (Sky Bet, Coral, Paddy Power):** Implement 3 scrapers. **Sub-agent 4B (Betfred, BetVictor,
BoyleSports):** Implement 3 scrapers. **Sub-agent 4C (Bwin, Ladbrokes, William Hill):** Implement 3 scrapers.
**Sub-agent 4D (Betway, Unibet, 888Sport):** Implement 3 scrapers.

Note: The OddsApiAdapter already aggregates many of these bookmakers. The direct scrapers provide real-time odds
independent of The Odds API latency (~2–5 min delay). Both coexist — the `sports-odds-data-service` decides which
adapter to use per bookmaker per latency requirement.

---

### Step 5 — Add Sports Odds Protocol to `unified-market-interface` (T2)

After all USEI adapters are implemented and D5 passes, add sports to `unified-market-interface`.

Create `unified-market-interface/unified_market_interface/sports/`:

```
sports/
  __init__.py
  protocol.py       # SportsMarketAdapter protocol (wraps OddsAdapter + BettingAdapter)
  registry.py       # adapter_for_bookmaker(key: str) -> OddsAdapter factory function
```

`protocol.py`:

```python
"""Sports market adapter protocol — unified interface for sports odds and execution."""

from typing import Protocol

from unified_api_contracts.sports import CanonicalOdds, BetOrder, BetExecution, OddsType


class SportsMarketAdapter(Protocol):
    """
    Unified sports market adapter.

    Implemented by adapters in unified-sports-execution-interface.
    Registered in unified-market-interface.sports.registry.
    """

    async def get_odds(self, fixture_id: str, markets: list[OddsType]) -> list[CanonicalOdds]:
        """Fetch current odds for a fixture. Raises BookmakerUnavailableError on failure."""
        ...

    async def get_fixtures_with_odds(self, sport: str, competition_id: str | None = None) -> list[str]:
        """Return active fixture IDs for this bookmaker."""
        ...
```

`registry.py`:

```python
"""Factory for creating sports market adapters by bookmaker key."""

from unified_sports_execution_interface.adapters.aggregator.odds_api import OddsApiAdapter
from unified_sports_execution_interface.adapters.exchanges.betfair import BetfairAdapter
# ... imports for all 20 adapters

_ADAPTER_MAP: dict[str, type] = {
    "betfair": BetfairAdapter,
    "smarkets": SmarketsAdapter,
    "odds_api": OddsApiAdapter,
    # ... all 20
}

def adapter_for_bookmaker(key: str) -> SportsMarketAdapter:
    """Return a fresh adapter instance for the given bookmaker key."""
    cls = _ADAPTER_MAP.get(key)
    if cls is None:
        from unified_api_contracts.sports.errors import BookmakerUnavailableError
        raise BookmakerUnavailableError(bookmaker_key=key, reason=f"No adapter registered for {key!r}")
    return cls()
```

Update `unified-market-interface/pyproject.toml` to add USEI dependency:

```toml
"unified-sports-execution-interface>=0.2.0,<1.0.0",
```

Tests: `tests/unit/sports/test_sports_registry.py` — verify all 20 keys return a non-None adapter instance. Run
`unified-market-interface` D5.

---

### Step 6 — Port Feature Calculators to `features-sports-service` (after Steps 1-5 complete)

Read `SPORTS_REPO/footballbets/features/` fully before starting. Port all 14 calculators.

**Architecture:** Feature calculators no longer use PostgreSQL ORM. They receive canonical Pydantic models from
GCS/PubSub (as `CanonicalFixture`, `CanonicalOdds`, etc.) and return typed feature dicts.

**Feature output schema** — add to `unified-api-contracts/sports/canonical/features.py`:

```python
class SportsFeatureVector(BaseModel):
    """Complete ML feature vector for a single fixture."""

    fixture_id: str
    computed_at_utc: datetime

    # Team features (from TeamFeatureCalculator)
    home_form_5: float | None       # points per game last 5 matches
    away_form_5: float | None
    home_win_rate_season: float | None
    away_win_rate_season: float | None
    home_goals_scored_avg: float | None
    away_goals_scored_avg: float | None
    home_goals_conceded_avg: float | None
    away_goals_conceded_avg: float | None
    home_home_advantage_factor: float | None   # home team's home win rate vs away win rate

    # H2H features (from H2HFeatureCalculator)
    h2h_home_wins: int | None
    h2h_draws: int | None
    h2h_away_wins: int | None
    h2h_avg_goals: float | None
    h2h_matches_played: int | None

    # League features (from LeagueFeatureCalculator)
    league_avg_goals_per_game: float | None
    league_home_win_rate: float | None
    league_btts_rate: float | None
    league_over_25_rate: float | None

    # Halftime features (from HalfTimeFeatureCalculator)
    home_ht_goal_rate: float | None
    away_ht_goal_rate: float | None

    # Goal timing features (from GoalTimingFeatureCalculator)
    home_early_goal_rate: float | None     # goals 0-15 min
    home_late_goal_rate: float | None      # goals 75-90 min
    away_late_concede_rate: float | None

    # Season context (from SeasonContextFeatureCalculator)
    match_week: int | None
    season_stage: str | None               # "EARLY" | "MID" | "RUN_IN" | "FINAL"
    home_relegation_pressure: float | None
    away_relegation_pressure: float | None
    home_title_pressure: float | None

    # Venue context (from VenueContextFeatureCalculator)
    venue_capacity: int | None
    venue_altitude_m: float | None
    venue_surface: str | None              # "GRASS" | "ARTIFICIAL" | "HYBRID"
    attendance_rate: float | None

    # Referee features (from RefereeFeatureCalculator)
    ref_cards_per_game: float | None
    ref_penalty_rate: float | None
    ref_home_bias_score: float | None

    # Player lineup features (from PlayerLineupFeatureCalculator)
    home_key_player_absent: bool | None
    away_key_player_absent: bool | None
    home_lineup_strength: float | None     # 0-1, relative to season average
    away_lineup_strength: float | None

    # Odds features (from OddsFeatureCalculator)
    market_home_implied_prob: float | None
    market_draw_implied_prob: float | None
    market_away_implied_prob: float | None
    market_overround: float | None
    market_consensus_home_prob: float | None   # weighted average across bookmakers

    # xG features (from MultiSourceXGFeatureCalculator + PoissonXGFeatureCalculator)
    understat_home_xg: float | None
    understat_away_xg: float | None
    footystats_home_xg: float | None
    footystats_away_xg: float | None
    poisson_home_win_prob: float | None
    poisson_draw_prob: float | None
    poisson_away_win_prob: float | None
    poisson_over_25_prob: float | None

    # Advanced stats (from AdvancedStatsFeatureCalculator)
    home_shots_on_target_avg: float | None
    away_shots_on_target_avg: float | None
    home_corners_avg: float | None
    away_corners_avg: float | None
    home_possession_avg: float | None

    # Weather features (from WeatherFeatureCalculator)
    weather_temp_c: float | None
    weather_wind_speed_ms: float | None
    weather_precipitation_mm: float | None
    weather_condition: str | None          # "CLEAR" | "RAIN" | "HEAVY_RAIN" | "SNOW" | "WIND"
```

Add `SportsFeatureVector` to `unified-api-contracts/sports/__init__.py`. Run `unified-api-contracts` D5.

**Calculator porting pattern** (same for all 14):

```python
# features_sports_service/calculators/team.py
"""Team form and performance feature calculator."""

from unified_api_contracts.sports import CanonicalFixture
from unified_api_contracts.sports.canonical.features import SportsFeatureVector


class TeamFeatureCalculator:
    """
    Computes team form, win rates, goals scored/conceded, and home/away splits.

    Ported from SPORTS_REPO/footballbets/features/team.py.
    Inputs are canonical Pydantic models (not PostgreSQL ORM rows).
    """

    def calculate(
        self,
        fixture: CanonicalFixture,
        home_recent_fixtures: list[CanonicalFixture],
        away_recent_fixtures: list[CanonicalFixture],
    ) -> dict[str, float | None]:
        """
        Return team feature dict. Keys match SportsFeatureVector field names.
        Returns None for any feature that cannot be computed from available data.
        """
        ...
```

Create `features_sports_service/calculators/`:

```
calculators/
  __init__.py
  team.py
  h2h.py
  league.py
  halftime.py
  goal_timing.py
  season_context.py
  venue_context.py
  referee.py
  player_lineup.py
  odds.py
  multisource_xg.py
  poisson_xg.py
  advanced_stats.py
  weather.py
  pipeline.py        # FeaturePipeline: orchestrates all 14, assembles SportsFeatureVector
```

`pipeline.py`:

```python
class FeaturePipeline:
    """
    Orchestrates all 14 feature calculators.
    Receives canonical data, returns a complete SportsFeatureVector.
    """

    def __init__(self) -> None:
        self._calculators = [
            TeamFeatureCalculator(),
            H2HFeatureCalculator(),
            LeagueFeatureCalculator(),
            HalfTimeFeatureCalculator(),
            GoalTimingFeatureCalculator(),
            SeasonContextFeatureCalculator(),
            VenueContextFeatureCalculator(),
            RefereeFeatureCalculator(),
            PlayerLineupFeatureCalculator(),
            OddsFeatureCalculator(),
            MultiSourceXGFeatureCalculator(),
            PoissonXGFeatureCalculator(),
            AdvancedStatsFeatureCalculator(),
            WeatherFeatureCalculator(),
        ]

    def compute(self, fixture: CanonicalFixture, context: FeatureContext) -> SportsFeatureVector:
        """Compute all features. Partial failures log a warning and return None for that feature group."""
        ...
```

**Tests for feature calculators:**

```
tests/unit/calculators/
  test_team_calculator.py         # fixture with known results → assert expected feature values
  test_h2h_calculator.py
  test_poisson_xg_calculator.py   # mathematical model — verify probabilities sum to ~1
  test_feature_pipeline.py        # full pipeline with mock fixture data → SportsFeatureVector
  conftest.py                     # shared fixture factories: make_canonical_fixture(), make_canonical_odds(), etc.
```

Run `features-sports-service` D5.

---

## Done Criteria

- [ ] `unified-api-contracts/sports/errors.py` created with 6 typed exception classes; D5 passes
- [ ] `SportsFeatureVector` schema added to `unified-api-contracts`; all fields typed; D5 passes
- [ ] BetfairAdapter fully implemented; all 6 unit tests pass with VCR cassettes
- [ ] SmarketsAdapter fully implemented; unit tests with VCR cassettes pass
- [ ] MatchbookAdapter fully implemented; unit tests with VCR cassettes pass
- [ ] BetdaqAdapter fully implemented; unit tests with VCR cassettes pass
- [ ] PinnacleAdapter fully implemented; unit tests with VCR cassettes pass
- [ ] OddsApiAdapter ported from SPORTS_REPO; PostgreSQL removed; asyncio; unit tests pass
- [ ] All 13 scraper adapters implemented with `_parse_odds_from_html()` logic; HTML fixtures saved; unit tests pass
- [ ] `unified-sports-execution-interface` D5 passes; zero `NotImplementedError` remaining (Phase 1 stubs all replaced)
- [ ] `unified-market-interface` sports registry added; `adapter_for_bookmaker()` works for all 20 keys; D5 passes
- [ ] All 14 feature calculators ported to `features-sports-service/calculators/`; no PostgreSQL ORM imports
- [ ] `FeaturePipeline` implemented; `test_feature_pipeline.py` passes with mock data
- [ ] `features-sports-service` D5 passes
- [ ] Zero `Any` types in any new code (or each documented in `QUALITY_GATE_BYPASS_AUDIT.md`)
- [ ] All tests are `@pytest.mark.unit` — zero live HTTP calls, zero real auth

---

## Key Files

- `unified-api-contracts/unified_api_contracts/sports/canonical/features.py` — SportsFeatureVector schema (create)
- `unified-api-contracts/unified_api_contracts/sports/errors.py` — typed exceptions (create)
- `unified-sports-execution-interface/unified_sports_execution_interface/adapters/` — all 20 adapters (implement)
- `unified-market-interface/unified_market_interface/sports/` — sports registry (create)
- `features-sports-service/features_sports_service/calculators/` — 14 calculators + pipeline (create)
- `SPORTS_REPO/footballbets/features/` — source implementations to port (read-only reference)
- `SPORTS_REPO/footballbets/clients/` — client implementations to reference for adapter logic
- `SPORTS_REPO/footballbets/arbitrage/odds.py` — OddsApiAdapter source to port
- `unified-trading-/codex/04-architecture/batch-live-symmetry.md` — batch/live seam pattern
- `.cursor/rules/delete-deprecated.mdc` — no backward compat
