# Agent Prompt — Sports Phase 1: Foundation & Contracts

> **NOTE (2026-03-01): Sports services have been consolidated into existing core services.**
> The standalone sports service repos referenced in this plan (sports-reference-data-service,
> sports-odds-processing-service, sports-strategy-service, sports-execution-service) have been
> merged into instruments-service, market-data-processing-service, strategy-service, and
> execution-service respectively. See `workspace-manifest.json` for current statuses.
> The skeleton creation steps below for those services should target the consolidated services instead.

> Paste this entire prompt into a new agent session to execute Sports Phase 1.
> Do NOT start Sports Phase 2 until every done criterion below is checked.
> This phase is UNIT TESTS ONLY — no external API calls, no live auth required.

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

This means:
- No TODO comments in production code — open a GitHub issue instead
- No magic numbers or hardcoded strings — use constants from UCI/AC
- No skipped tests — every skip documented with issue link
- No silent failures — every error logged with `service_name`, `correlation_id`, `timestamp`
- Every secret through Secret Manager — never env vars, never config files
- Every config through `UnifiedCloudConfig` — never `os.getenv()`
- Meaningful error messages — not "an error occurred"
- All public functions/classes have docstrings and full type hints
- If it would fail a Citadel code review, it is not done

---

## Your Mission

Execute **Sports Phase 1 — Foundation & Contracts** for the sports betting vertical integration.

Read the existing sports-betting-services repo at `SPORTS_REPO` before starting any work — it contains fully-implemented feature calculators, data clients, and arbitrage logic that inform the canonical schemas you must create. Do NOT port any implementation in this phase — schemas and stubs only.

Sports Phase 2 cannot start until all DONE criteria below are met.

---

## Context — What Already Exists

### In `SPORTS_REPO` (external, reference only — do NOT modify):
- `footballbets/clients/` — 5 data source clients (API-Football, FootyStats, Understat, Soccer-Football-Info, Open-Meteo)
- `footballbets/arbitrage/odds.py` — The Odds API v4 multi-bookmaker downloader
- `footballbets/features/` — 14 feature calculators
- `footballbets/core/models.py` — 2,300+ line PostgreSQL ORM with 40+ tables across 5 sources (use this to derive canonical Pydantic schemas)
- `footballbets/arbitrage/analyze_bookmaker_vig.py` — vig/margin analysis

### In unified trading system (existing skeletons to upgrade):
- `unified-sports-execution-interface` (T2) — `BaseSportsAdapter` protocol with untyped `dict[str,str]` return types, no adapter implementations
- `features-sports-service` (T4) — Pub/Sub seam adapters only, no feature logic
- `unified-api-contracts` — NO sports schemas yet (needs `sports/` subdir)
- `unified-market-interface` — NO sports odds protocol yet

---

## SSOT — Read These First

| Source | Path | What it governs |
|--------|------|-----------------|
| Workspace manifest | `unified-trading-pm/workspace-manifest.json` | Repo registry — add 5 new service repos here |
| Tier architecture | `unified-trading-codex/04-architecture/TIER-ARCHITECTURE.md` | Tier DAG — sports services are T4 |
| Library matrix | `unified-trading-codex/05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md` | Which libraries services may import |
| New repo setup | `unified-trading-pm/docs/new-repo-setup.md` | Template for creating new repos |
| Batch/live symmetry | `unified-trading-codex/04-architecture/batch-live-symmetry.md` | All services support `--mode batch\|live` |
| AC structure | `unified-api-contracts/` | Existing schema structure to follow when adding `sports/` subdir |

---

## Bottom-Up Rule — Template First, Then Propagate

Sports vertical follows the same tier hierarchy as the rest of the system:

```
T0: unified-api-contracts         ← sports schemas go HERE first
T2: unified-sports-execution-interface  ← adapter protocols + stubs (imports AC)
T4: sports-reference-data-service
    sports-odds-data-service
    sports-odds-processing-service
    sports-strategy-service
    sports-execution-service
```

**Never** define a canonical type inline in a service or T2 library. If it is a cross-source type (`CanonicalOdds`, `BetOrder`, etc.) it belongs in `unified-api-contracts/sports/`.

---

## New Repos to Create (5)

Create each repo using `unified-trading-pm/docs/new-repo-setup.md` as template.
Every repo must have: `pyproject.toml`, `scripts/quickmerge.sh`, `scripts/quality-gates.sh`, `.github/workflows/version-bump.yml`, `README.md`, `QUALITY_GATE_BYPASS_AUDIT.md`.

| Repo | Package Name | Tier | Sports DAG Batch | Analogous Existing Service |
|------|-------------|------|------------------|---------------------------|
| `sports-reference-data-service` | `sports_reference_data_service` | T4 | Batch A | instruments-service |
| `sports-odds-data-service` | `sports_odds_data_service` | T4 | Batch B | market-tick-data-service |
| `sports-odds-processing-service` | `sports_odds_processing_service` | T4 | Batch B | market-data-processing-service |
| `sports-strategy-service` | `sports_strategy_service` | T4 | Batch D | strategy-service |
| `sports-execution-service` | `sports_execution_service` | T4 | Batch E | execution-service |

Each new repo skeleton must contain:
```
<repo>/
  <package_name>/
    __init__.py           # version = "0.1.0", brief docstring
    engine.py             # STUB: class <Name>Engine — mode-agnostic, no logic yet
    adapters/
      __init__.py
      live_data_source.py # STUB: LiveDataSource(PubSub subscriber)
      broadcast_sink.py   # STUB: BroadcastSink(PubSub publisher)
  tests/
    __init__.py
    unit/
      __init__.py
      test_imports.py     # smoke test: import <package_name> exits 0
  pyproject.toml
  README.md
  scripts/
    quickmerge.sh
    quality-gates.sh
  .github/
    workflows/
      version-bump.yml
  QUALITY_GATE_BYPASS_AUDIT.md
```

**`pyproject.toml` for each new service** must list:
```toml
dependencies = [
    "unified-api-contracts>=1.0.0,<2.0.0",
    "unified-trading-services>=2.2.0,<3.0.0",
    "unified-config-interface>=1.1.0,<2.0.0",
    "unified-events-interface>=1.0.0,<2.0.0",
    "unified-cloud-interface>=1.0.0,<2.0.0",
]
```

Add `sports-execution-service` and `sports-strategy-service` also depend on:
```toml
    "unified-sports-execution-interface>=0.1.0,<1.0.0",
```

---

## Execution Order

Streams A, B, C run in parallel.

### Stream A — New Repo Scaffolding + Manifest Registration (parallel)

5 sub-agents, one per new repo:

1. Create each repo directory at `WORKSPACE_ROOT/<repo-name>/`
2. Write all skeleton files (see structure above)
3. Register in `unified-trading-pm/workspace-manifest.json`:
   ```json
   {
     "name": "<repo-name>",
     "arch_tier": "service",
     "package_name": "<package_name>",
     "github_url": "https://github.com/unified-trading/<repo-name>",
     "artifact_registry_url": "europe-west2-docker.pkg.dev/project/unified-trading/<repo-name>",
     "ci_status": "PENDING",
     "quality_gate_status": "PENDING",
     "coverage_pct": 0,
     "testing_level": "unit"
   }
   ```
4. Add `sports_completion_path` field to manifest noting sports vertical progress
5. Run import smoke test: `python -c "import <package_name>"` — must exit 0

### Stream B — T0 Sports Schemas in `unified-api-contracts` (strictly sequential within stream)

**This is the most critical stream. All canonical types live here. Read `SPORTS_REPO/footballbets/core/models.py` fully before writing a single schema.**

Create `unified-api-contracts/sports/` with the following structure:

```
unified-api-contracts/
  unified_api_contracts/
    sports/
      __init__.py                    # exports all canonical types
      canonical/
        __init__.py
        fixture.py                   # CanonicalFixture, CanonicalTeam, CanonicalLeague, CanonicalPlayer, CanonicalVenue, CanonicalReferee
        odds.py                      # CanonicalOdds, CanonicalBookmakerMarket, OddsType, OutcomeType, MarketStatus
        betting.py                   # BetOrder, BetExecution, BetStatus, BettingSignal, SignalSource
        arbitrage.py                 # ArbitrageOpportunity, ArbitrageMarket, ExpectedValue, ArbitrageStatus
        bookmaker.py                 # BookmakerInfo, BookmakerCategory, BookmakerRegistry (constant — all 20 bookmakers)
      sources/
        __init__.py
        api_football/
          __init__.py
          schemas.py                 # APIFootballFixture, APIFootballTeam, APIFootballPlayer, APIFootballStats, APIFootballLineup, APIFootballEvent, APIFootballVenue, APIFootballReferee, APIFootballLeague, APIFootballOdds
        footystats/
          __init__.py
          schemas.py                 # FootyStatsMatch, FootyStatsTeam, FootyStatsLeague, FootyStatsPlayer, FootyStatsReferee, FootyStatsBTTS, FootyStatsOverUnder, FootyStatsOdds
        understat/
          __init__.py
          schemas.py                 # UnderstatMatch, UnderstatShot, UnderstatPlayerSeason, UnderstatTeamHistory, UnderstatXGData
        soccer_football_info/
          __init__.py
          schemas.py                 # SFIMatch, SFITeam, SFILeague, SFIMatchDominance, SFIMatchProgressiveStats, SFIMatchProgressiveOdds
        open_meteo/
          __init__.py
          schemas.py                 # OpenMeteoWeather, OpenMeteoForecast, WeatherCondition, WeatherAtKickoff
        betfair/
          __init__.py
          schemas.py                 # BetfairMarket, BetfairRunner, BetfairPrice, BetfairOrder, BetfairMarketStatus, BetfairExchangeOdds
        pinnacle/
          __init__.py
          schemas.py                 # PinnacleOdds, PinnacleLine, PinnacleEvent, PinnacleMatchup
        odds_api/
          __init__.py
          schemas.py                 # OddsApiEvent, OddsApiBookmaker, OddsApiMarket, OddsApiOutcome
```

**Schema requirements (every schema):**
- Pydantic v2 `BaseModel` with `model_config = ConfigDict(frozen=True)`
- All fields fully typed — no `Any`, no `dict[str, Any]`
- Required fields have no defaults; optional fields use `field: X | None = None`
- Docstring on every class and every non-obvious field
- Every schema has at least one `@classmethod` factory method `from_raw(data: dict[str, ...]) -> Self`

**Canonical types detail:**

`CanonicalFixture`:
```python
class CanonicalFixture(BaseModel):
    fixture_id: str          # cross-source canonical key (e.g. "af:12345")
    home_team: CanonicalTeam
    away_team: CanonicalTeam
    league: CanonicalLeague
    kickoff_utc: datetime    # always UTC, always timezone-aware
    venue: CanonicalVenue | None
    referee: CanonicalReferee | None
    season: str              # e.g. "2024-25"
    match_week: int | None
    source: str              # "api_football" | "footystats" | "soccer_football_info"
```

`CanonicalOdds`:
```python
class CanonicalOdds(BaseModel):
    fixture_id: str
    bookmaker: BookmakerInfo
    market: OddsType                 # H2H | OVER_UNDER | ASIAN_HANDICAP | BOTH_TEAMS_SCORE | CORRECT_SCORE | OUTRIGHT
    home_odds: Decimal | None
    draw_odds: Decimal | None
    away_odds: Decimal | None
    over_line: Decimal | None        # for OVER_UNDER
    over_odds: Decimal | None
    under_odds: Decimal | None
    handicap_line: Decimal | None    # for ASIAN_HANDICAP
    handicap_home_odds: Decimal | None
    handicap_away_odds: Decimal | None
    implied_home_prob: Decimal | None
    implied_draw_prob: Decimal | None
    implied_away_prob: Decimal | None
    margin: Decimal | None           # bookmaker overround (vig)
    timestamp_utc: datetime
    source: str
```

`ArbitrageOpportunity`:
```python
class ArbitrageOpportunity(BaseModel):
    opportunity_id: str
    fixture_id: str
    market: OddsType
    legs: list[ArbitrageMarket]      # one entry per bookmaker/exchange in the arb
    total_implied_prob: Decimal      # sum of best implied probs — must be < 1.0 for true arb
    expected_return_pct: Decimal     # (1 / total_implied_prob - 1) * 100
    detected_at_utc: datetime
    status: ArbitrageStatus          # DETECTED | STALE | EXECUTED | MISSED
```

`BetOrder`:
```python
class BetOrder(BaseModel):
    order_id: str
    fixture_id: str
    bookmaker: BookmakerInfo
    market: OddsType
    selection: str                   # "HOME" | "DRAW" | "AWAY" | "OVER" | "UNDER"
    requested_odds: Decimal
    stake: Decimal                   # in GBP/USD/EUR — currency in BookmakerInfo
    max_acceptable_odds: Decimal     # min odds we accept (slippage protection)
    strategy_source: SignalSource    # ARBITRAGE | ML_MODEL
    signal_id: str | None            # links to BettingSignal if ML
    opportunity_id: str | None       # links to ArbitrageOpportunity if arb
    created_at_utc: datetime
```

`BookmakerRegistry` — define this as a constant `dict[str, BookmakerInfo]` with all 20 entries:
- **Category A (Exchange, direct API):** betfair, smarkets, matchbook, betdaq
- **Category B (Bookmaker, direct API):** pinnacle, onexbet
- **Category C (Aggregator):** odds_api (meta-entry covering 15+ bookmakers via The Odds API v4)
- **Category D (Scraped):** skybet, coral, paddypower, betfred, betvictor, boylesports, bwin, ladbrokes, williamhill, betway, unibet, bet888sport

Each `BookmakerInfo`:
```python
class BookmakerInfo(BaseModel):
    key: str                 # machine key e.g. "betfair"
    display_name: str        # e.g. "Betfair Exchange"
    category: BookmakerCategory  # EXCHANGE | BOOKMAKER_API | AGGREGATOR | SCRAPER
    currency: str            # "GBP" | "USD" | "EUR"
    supports_live_betting: bool
    supports_cash_out: bool
    min_bet_gbp: Decimal
    max_bet_gbp: Decimal | None
    api_docs_url: str | None
    scrape_url: str | None
```

**After writing all schemas, add to `unified-api-contracts/sports/__init__.py`:**
```python
from unified_api_contracts.sports.canonical.fixture import CanonicalFixture, CanonicalTeam, CanonicalLeague, ...
from unified_api_contracts.sports.canonical.odds import CanonicalOdds, OddsType, ...
from unified_api_contracts.sports.canonical.betting import BetOrder, BetExecution, BettingSignal, ...
from unified_api_contracts.sports.canonical.arbitrage import ArbitrageOpportunity, ...
from unified_api_contracts.sports.canonical.bookmaker import BookmakerInfo, BookmakerRegistry, ...
```

**Update `unified-api-contracts/unified_api_contracts/__init__.py`:**
Add `from unified_api_contracts.sports import *` or explicit re-exports so `from unified_api_contracts import CanonicalFixture` works.

**Tests to write in `unified-api-contracts/tests/unit/sports/`:**
```
test_canonical_schemas.py    — every canonical schema: construct valid, missing required field raises ValidationError, wrong type raises ValidationError
test_source_schemas.py       — every source schema: round-trip serialisation, from_raw() factory
test_bookmaker_registry.py   — all 20 entries present; each has required fields; categories correct
test_sports_exports.py       — `from unified_api_contracts import CanonicalFixture` works; spot check all canonical types importable from top level
```

Run quickmerge ladder on `unified-api-contracts`:
```bash
cd unified-api-contracts
bash scripts/quickmerge.sh "feat(sports): add sports betting schemas — canonical types, source schemas, BookmakerRegistry" --no-pr
```
D5 must pass before starting Stream C USEI upgrades.

### Stream C — T2 USEI Upgrade (after Stream B `unified-api-contracts` D5 passes)

**Goal:** Upgrade `unified-sports-execution-interface` from untyped stubs to fully-typed protocols backed by the AC schemas. Do NOT implement any adapter logic — stubs + protocols only.

#### Step 1 — Replace untyped base protocol

Replace `unified_sports_execution_interface/base.py` entirely:

```python
"""Sports execution interface — typed adapter protocols."""

from decimal import Decimal
from typing import Protocol

from unified_api_contracts.sports import (
    BetExecution,
    BetOrder,
    CanonicalOdds,
    OddsType,
)


class OddsAdapter(Protocol):
    """Protocol for bookmakers and exchanges that provide odds data."""

    async def get_odds(
        self,
        fixture_id: str,
        markets: list[OddsType],
    ) -> list[CanonicalOdds]:
        """Fetch current odds for a fixture across requested markets."""
        ...

    async def get_fixtures_with_odds(
        self,
        sport: str,
        competition_id: str | None = None,
    ) -> list[str]:
        """Return fixture IDs that currently have active markets."""
        ...


class BettingAdapter(Protocol):
    """Protocol for exchanges/bookmakers that support bet placement."""

    async def place_bet(self, order: BetOrder) -> BetExecution:
        """Submit a bet order. Raises BetRejectedError on refusal."""
        ...

    async def cancel_bet(self, bet_id: str) -> bool:
        """Cancel an open bet. Returns True if cancelled, False if already settled."""
        ...

    async def get_bet_status(self, bet_id: str) -> BetExecution:
        """Retrieve current status of a bet."""
        ...

    async def get_balance(self) -> Decimal:
        """Return available balance in the adapter's base currency."""
        ...
```

Delete old `BaseSportsAdapter` — no backward compat, no re-export.

#### Step 2 — Create 20 adapter stub files

Create one file per bookmaker under `unified_sports_execution_interface/adapters/`:

```
adapters/
  exchanges/
    __init__.py
    betfair.py          # BetfairAdapter(OddsAdapter, BettingAdapter) — stub
    smarkets.py         # SmarketsAdapter(OddsAdapter, BettingAdapter) — stub
    matchbook.py        # MatchbookAdapter(OddsAdapter, BettingAdapter) — stub
    betdaq.py           # BetdaqAdapter(OddsAdapter, BettingAdapter) — stub
  bookmaker_api/
    __init__.py
    pinnacle.py         # PinnacleAdapter(OddsAdapter) — stub (no bet placement)
    onexbet.py          # OnexBetAdapter(OddsAdapter) — stub
  aggregator/
    __init__.py
    odds_api.py         # OddsApiAdapter(OddsAdapter) — covers 15+ bookmakers via The Odds API v4
  scrapers/
    __init__.py
    skybet.py           # SkyBetAdapter(OddsAdapter) — stub
    coral.py            # CoralAdapter(OddsAdapter) — stub
    paddy_power.py      # PaddyPowerAdapter(OddsAdapter) — stub
    betfred.py          # BetfredAdapter(OddsAdapter) — stub
    betvictor.py        # BetVictorAdapter(OddsAdapter) — stub
    boylesports.py      # BoyleSportsAdapter(OddsAdapter) — stub
    bwin.py             # BwinAdapter(OddsAdapter) — stub
    ladbrokes.py        # LadbrokesAdapter(OddsAdapter) — stub
    william_hill.py     # WilliamHillAdapter(OddsAdapter) — stub
    betway.py           # BetwayAdapter(OddsAdapter) — stub
    unibet.py           # UnibetAdapter(OddsAdapter) — stub
    bet888sport.py      # Bet888SportAdapter(OddsAdapter) — stub
  __init__.py           # exports all adapter classes
```

**Each stub file pattern (example for BetfairAdapter):**
```python
"""Betfair Exchange adapter — odds and bet placement via Betfair Exchange API."""

from decimal import Decimal

from unified_api_contracts.sports import BetExecution, BetOrder, CanonicalOdds, OddsType

from unified_sports_execution_interface.base import BettingAdapter, OddsAdapter


class BetfairAdapter:
    """
    Betfair Exchange adapter.

    Implements both OddsAdapter (price feed) and BettingAdapter (execution).
    Uses the Betfair Exchange API via betfairlightweight.
    Implementation deferred to Phase 2.
    """

    async def get_odds(
        self,
        fixture_id: str,
        markets: list[OddsType],
    ) -> list[CanonicalOdds]:
        """Fetch Betfair Exchange best available prices."""
        raise NotImplementedError("Betfair odds fetch — implement in Phase 2")

    async def get_fixtures_with_odds(
        self,
        sport: str,
        competition_id: str | None = None,
    ) -> list[str]:
        """Fetch active Betfair markets."""
        raise NotImplementedError("Betfair fixture listing — implement in Phase 2")

    async def place_bet(self, order: BetOrder) -> BetExecution:
        """Place a bet on Betfair Exchange."""
        raise NotImplementedError("Betfair bet placement — implement in Phase 2")

    async def cancel_bet(self, bet_id: str) -> bool:
        raise NotImplementedError("Betfair cancel — implement in Phase 2")

    async def get_bet_status(self, bet_id: str) -> BetExecution:
        raise NotImplementedError("Betfair bet status — implement in Phase 2")

    async def get_balance(self) -> Decimal:
        raise NotImplementedError("Betfair balance — implement in Phase 2")


_: OddsAdapter = BetfairAdapter()   # type: ignore[assignment]  # structural Protocol check
_b: BettingAdapter = BetfairAdapter()  # type: ignore[assignment]
```

Note: The `_: OddsAdapter = BetfairAdapter()` lines are static structural type assertions — they verify the adapter satisfies the protocol at type-check time without runtime overhead. Document in `QUALITY_GATE_BYPASS_AUDIT.md`.

Scrapers (`OddsAdapter` only, no `BettingAdapter`):
```python
class SkyBetAdapter:
    """SkyBet scraper adapter — reads odds via Playwright. Implementation in Phase 2."""

    async def get_odds(self, fixture_id: str, markets: list[OddsType]) -> list[CanonicalOdds]:
        raise NotImplementedError("SkyBet scraper — implement in Phase 2")

    async def get_fixtures_with_odds(self, sport: str, competition_id: str | None = None) -> list[str]:
        raise NotImplementedError("SkyBet fixture listing — implement in Phase 2")
```

#### Step 3 — Tests

Write `tests/unit/test_adapter_stubs.py`:
```python
"""Verify all adapter stubs are importable, structurally correct, and raise NotImplementedError."""
import pytest
from unified_sports_execution_interface.adapters.exchanges.betfair import BetfairAdapter
# ... import all 20 adapters

@pytest.mark.unit
@pytest.mark.parametrize("adapter_class", [BetfairAdapter, SmarketsAdapter, ...])
def test_adapter_importable(adapter_class):
    adapter = adapter_class()
    assert adapter is not None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_betfair_raises_not_implemented():
    adapter = BetfairAdapter()
    with pytest.raises(NotImplementedError):
        await adapter.get_odds("af:12345", [OddsType.H2H])
```

Write `tests/unit/test_protocols.py`:
```python
"""Verify protocol structural compliance via runtime isinstance checks."""
import pytest
from unittest.mock import AsyncMock
from unified_sports_execution_interface.base import OddsAdapter, BettingAdapter

@pytest.mark.unit
def test_odds_adapter_protocol_has_required_methods():
    required = {"get_odds", "get_fixtures_with_odds"}
    assert required.issubset(set(OddsAdapter.__protocol_attrs__))
```

Run quickmerge ladder:
```bash
cd unified-sports-execution-interface
bash scripts/quickmerge.sh "feat: upgrade to typed protocols from AC; add 20 bookmaker stubs" --no-pr
```
D5 must pass before Phase 2 may begin.

---

## Import Smoke Tests (run after each stream completes)

```bash
# After Stream A:
python -c "import sports_reference_data_service"
python -c "import sports_odds_data_service"
python -c "import sports_odds_processing_service"
python -c "import sports_strategy_service"
python -c "import sports_execution_service"

# After Stream B:
python -c "from unified_api_contracts.sports import CanonicalFixture, CanonicalOdds, BetOrder, ArbitrageOpportunity, BookmakerRegistry"
python -c "from unified_api_contracts.sports.canonical.bookmaker import BookmakerRegistry; assert len(BookmakerRegistry) == 20"

# After Stream C:
python -c "from unified_sports_execution_interface.adapters.exchanges.betfair import BetfairAdapter"
python -c "from unified_sports_execution_interface.adapters.scrapers.skybet import SkyBetAdapter"
python -c "from unified_sports_execution_interface.base import OddsAdapter, BettingAdapter"
```

---

## Done Criteria

- [ ] 5 new service repos created with full skeleton, CI/CD, import smoke tests pass
- [ ] All 5 new repos registered in `workspace-manifest.json` with `testing_level: "unit"`, `ci_status: "PENDING"`
- [ ] `unified-api-contracts/sports/` created with all 7 source schema modules
- [ ] All canonical types present: `CanonicalFixture`, `CanonicalTeam`, `CanonicalLeague`, `CanonicalPlayer`, `CanonicalVenue`, `CanonicalReferee`, `CanonicalOdds`, `BetOrder`, `BetExecution`, `BettingSignal`, `ArbitrageOpportunity`, `BookmakerRegistry`
- [ ] `BookmakerRegistry` contains exactly 20 entries (4 exchanges + 2 API + 1 aggregator + 13 scrapers)
- [ ] All canonical schemas have frozen Pydantic v2 config, full type hints, docstrings, `from_raw()` factory
- [ ] `unified-api-contracts` D5 passes (quickmerge full, not just `--quick`)
- [ ] `unified-sports-execution-interface` upgraded: old `BaseSportsAdapter` with `dict[str,str]` deleted; `OddsAdapter` + `BettingAdapter` protocols in place
- [ ] All 20 adapter stub files created under correct category subdirectory
- [ ] Every adapter stub raises `NotImplementedError` on every method
- [ ] `unified-sports-execution-interface` D5 passes
- [ ] All tests are `@pytest.mark.unit` — zero external API calls, zero live auth

---

## Key Files

- `unified-trading-pm/workspace-manifest.json` — add 5 new service repos
- `unified-api-contracts/unified_api_contracts/sports/` — create this subtree
- `unified-sports-execution-interface/unified_sports_execution_interface/base.py` — replace with typed protocols
- `unified-sports-execution-interface/unified_sports_execution_interface/adapters/` — create 20 stub files
- `SPORTS_REPO/footballbets/core/models.py` — read to derive canonical schemas (do NOT copy)
- `SPORTS_REPO/footballbets/arbitrage/odds.py` — read to understand The Odds API structure (do NOT copy)
- `unified-trading-pm/docs/new-repo-setup.md` — template for creating new repos
- `unified-trading-codex/04-architecture/TIER-ARCHITECTURE.md` — tier rules
