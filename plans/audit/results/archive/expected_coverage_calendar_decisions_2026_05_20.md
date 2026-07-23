---
doc_type: audit-result
title: A2 — expected_coverage() calendar-decision sidecar
summary:
  A2 operator calendar-decision sidecar for the expected_coverage() availability oracle — records which calendars UAC
  encodes (US holidays/half-days, venue launch, chain genesis) vs 5 gaps it defaults to SHOULD_HAVE_DATA (sports
  off-season, DeFi protocol pauses, per-instrument listed_at, coverage_start, pre-Tardis windows) + the tradfi
  tbbo/trades 2-month cost-scoped BLOCKED-OPERATOR-DECISION.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [audit, honest-coverage, uac, tradfi, sports, defi, golden-window, cost]
related:
  [
    /plans/audit/results/archive/expected_coverage_dump_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md,
  ]
created: 2026-05-20
audited_scope:
  The calendar/trading-judgment inputs to the UAC expected_coverage() oracle — calendars currently encoded, known
  unencoded gaps (per asset_group), and operator-acked scope decisions (tradfi tbbo/trades cost reduction)
date: 2026-05-20
auditor: semver
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

# A2 — expected_coverage() calendar-decision sidecar

> Operator iteration log for the trading-judgment inputs to the deterministic availability oracle
> (`unified_api_contracts.registry.expected_coverage. expected_coverage`). Mega-audit Phase A2 produced this on
> 2026-05-20.
>
> Update annually + on any operator-driven gap-policy change. Cited by every A3 manifest divergence report so the
> consumer knows what calendar gaps the oracle accounts for vs leaves on the table.

## Calendars currently encoded in UAC (oracle composes these automatically)

| Calendar                       | UAC SSOT                                                    | Asset groups it gates | Notes                                                                                                                                        |
| ------------------------------ | ----------------------------------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| US market holidays 2020–2028   | `registry/venue_trading_calendar.US_MARKET_HOLIDAYS`        | tradfi                | NYSE / NASDAQ / CBOE share the same list. Refresh annually.                                                                                  |
| US half-day sessions 2020–2027 | `registry/half_day_sessions.HALF_DAY_SESSIONS`              | tradfi                | Per-venue (NYSE, NASDAQ, CBOE, CME, ICE, EUREX) with separate frozensets for `_US_EQUITY_HALF_DAYS` / `_CME_HALF_DAYS` / `_EUREX_HALF_DAYS`. |
| US weekend                     | weekday() ≥ 5                                               | tradfi                | Hardcoded in oracle (no SSOT needed).                                                                                                        |
| CeFi venue launch dates        | `registry/venue_launch_dates.CEFI_VENUE_LAUNCH_DATES`       | cefi                  | 19 venues. Refresh on each new venue scaffold.                                                                                               |
| DeFi protocol launch dates     | `registry/venue_launch_dates.DEFI_VENUE_LAUNCH_DATES`       | defi                  | Per (protocol, chain) tuple.                                                                                                                 |
| Prediction venue launch dates  | `registry/venue_launch_dates.PREDICTION_VENUE_LAUNCH_DATES` | prediction            | POLYMARKET (2020-09-01) + KALSHI (2021-07-30).                                                                                               |
| Chain genesis dates            | `registry/chain_env.CHAIN_GENESIS_DATES`                    | defi                  | Per-chain (ETHEREUM, ARBITRUM, BASE, etc.).                                                                                                  |

## Known gaps the oracle does NOT yet encode (review-blocking before next A3 refresh)

The list below records every category where Phase A2 fell through to a default of `SHOULD_HAVE_DATA` even though
operator trading-judgment may dictate otherwise. Each gap should be either: (a) encoded in UAC + the oracle extended in
a follow-up patch, OR (b) explicitly marked as out-of-scope for the divergence report. Until then, A3 reports may
overstate `MISSING_EXPECTED` for the relevant cells.

### 1. Sports off-season + no-fixture calendars

**Gap**: sports asset_group has no calendar encoded. For every in-scope sports venue × data_type × date, the oracle
returns `SHOULD_HAVE_DATA` once the venue launch date passes — even on days no fixture exists.

**Impact on A3**: sports MISSING_EXPECTED counts are inflated; many of those are honest off-season days.

**Operator decision needed**: per-league calendar export (NFL off-season = roughly Feb–Aug; NBA = Jul–Oct; MLB =
Nov–Mar; tennis ATP/WTA = mostly continuous; soccer EPL = May–Aug off-season). Either:

- (a) encode `LEAGUE_OFFSEASON_RANGES` in a new UAC registry + extend oracle, or
- (b) defer sports divergence detection until per-fixture instruments-service rows land (instruments-service knows
  fixtures; can do this exactly).

**Recommendation**: option (b) — pair the divergence report with IS fixture data rather than build a parallel
league-calendar registry. Tracked in follow-up todo.

### 2. DeFi protocol pause windows + known gaps

**Gap**: DeFi protocol pauses (e.g. Aave V2 → V3 migration windows, Compound governance pauses, chain-specific outages)
are not encoded. For every in-scope DeFi cell, the oracle returns `SHOULD_HAVE_DATA` once chain genesis + venue launch
pass.

**Impact on A3**: DeFi MISSING_EXPECTED counts may include honest protocol-pause windows. The 184k DeFi MISSING_EXPECTED
cells in the 2026-05-20 report likely include some of these.

**Operator decision needed**: enumerate known pause windows per protocol-chain. Known candidates (from workspace
history):

- Aave V2 deprecation 2024–2025 (Ethereum mainnet rebalance).
- Compound V2 wind-down 2024 (most chains).
- Chain reorganisation windows (e.g. Polygon Bor halts).

**Recommendation**: build `PROTOCOL_PAUSE_WINDOWS: dict[str, list[(date, date)]]` in `registry/chain_env.py` or a new
module + extend oracle to check it. Tracked as a follow-up todo against the mega-audit tracker.

### 3. Per-instrument `listed_at` / `delisted_at`

**Gap**: oracle has no symbol axis in v1. Every cell at (asset_group, source, data_type, date) is symbol-agnostic.
Per-symbol listing windows (e.g. BINANCE listed BTC-USDT on 2017-08-17 but ETH-USDT only on 2018-01-23) are not
incorporated.

**Impact on A3**: divergence comparison is at (venue, data_type, date) level, which already aggregates over symbols — so
MISSING_EXPECTED at this level means "no symbol on this venue had captured data on this day", not "specific symbol X
missing". Per-symbol bugs are visible in the parquet but not in the per-cell classification.

**Recommendation**: extend A3 to do a second per-symbol join against the IS catalogue's `listed_at` field once that's
queryable from the manifest. Tracked as a follow-up.

### 4. `SourceCapability.coverage_start` not yet consumed

**Gap**: slot-3's `uac_source_capability_metadata_promotion_2026_05_20.md` landed
`SourceCapability.coverage_start: dict[str, date]` on 2026-05-20 but no aggregated lookup index exists yet. The oracle
falls through to `venue_launch_dates.py` (which is per-venue, not per-data_type) — overshoots coverage windows for
venues with data_type-specific archives starting later than the venue launch.

**Impact on A3**: some `SHOULD_HAVE_DATA` cells may actually be `EXPECTED_PRE_SOURCE_COVERAGE_START` once
`coverage_start` is consumed. This slightly inflates MISSING_EXPECTED.

**Recommendation**: build the source index in slot-3 Phase 4 + re-run A2 dump

- A3 divergence. Already a tracked todo.

### 5. CeFi pre-Tardis-archive windows

**Gap**: even when a CeFi venue launched before 2018-01-01, the Tardis archive window may begin later (Tardis backfill
is per-venue + per-data_type). Some cells before 2019 likely register as `MISSING_EXPECTED` when they're actually
pre-Tardis-archive (honest empty).

**Operator decision needed**: confirm the Tardis archive start per (venue, data_type) and either:

- (a) populate `SourceCapability.coverage_start[data_type]` from Tardis docs, or
- (b) accept the pre-2019 overstatement until the slot-3 integration lands.

**Recommendation**: option (a), bundled with the slot-3 Phase 4 work.

## Decisions deliberately NOT made by the oracle

The oracle does not make any of the following calls — these are operator-judgment calls that live elsewhere or are
explicitly out of scope:

- Whether a venue is currently being operated against (operator UI filter chips).
- Whether a particular `attempted_failed` reason indicates a real bug or a known venue outage (use the manifest
  `error_reason` column directly).
- Whether to enumerate a date in the orchestrator's scope (the orchestrator enumerator + IS catalogue answer this, not
  the oracle).

## Operator-acked scope decisions 2026-05-20 (round 2)

These are `BLOCKED-OPERATOR-DECISION` scope removals — operator explicitly articulated the reason; agent never makes
this call autonomously.

### TradFi `tbbo` + `trades` cost-driven scope reduction

**Operator directive 2026-05-20**: "we said for tradfi to focus on `ohlcv_1m` for now because of cost. VIX is different
as not databento and same for yahoo finance data source. tbbo and trades are expensive we said to get 2 months one in
2023 one in 2024 as a max if at all for now"

**Concrete scope** (effective until operator unblocks):

| Venue         | Data type             | Status                                    | Window in scope                                                                                            |
| ------------- | --------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| CME           | ohlcv_1m              | IN SCOPE (full)                           | 2018-01-01 → today                                                                                         |
| CME           | tbbo                  | `BLOCKED-OPERATOR-DECISION` — sample only | one month in 2023 + one month in 2024 (operator picks the months)                                          |
| CME           | trades                | `BLOCKED-OPERATOR-DECISION` — sample only | same — one month in 2023 + one month in 2024                                                               |
| ICE           | ohlcv_1m              | IN SCOPE (full)                           | 2018-01-01 → today                                                                                         |
| ICE           | tbbo                  | `BLOCKED-OPERATOR-DECISION` — sample only | one month in 2023 + one month in 2024                                                                      |
| ICE           | trades                | `BLOCKED-OPERATOR-DECISION` — sample only | one month in 2023 + one month in 2024                                                                      |
| CBOE          | ohlcv_15m (VIX)       | IN SCOPE (full)                           | NOT Databento — Barchart preload + Yahoo rolling 60d + honest gap per `registry/data_source_continuity.py` |
| NYSE          | ohlcv_1m              | IN SCOPE (full)                           | per `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`                                                         |
| NASDAQ        | ohlcv_1m              | IN SCOPE (full)                           | per same plan                                                                                              |
| YAHOO_FINANCE | ohlcv_15m + ohlcv_24h | IN SCOPE (full)                           | NOT Databento — separate source per data_source_continuity                                                 |
| FX            | ohlcv_24h             | IN SCOPE (full)                           | not Databento                                                                                              |

**Named successor** (when the BLOCKED-OPERATOR-DECISION resolves): operator revisits cost vs research-value tradeoff; if
approved, expand tbbo + trades to full window via Databento (or alternative tick provider).

**Action required for A2 oracle**: the per-(venue, data_type) scope policy in `EXPECTED_COVERAGE_BY_ASSET_GROUP` should
be narrowed for tradfi tbbo + trades OR the oracle should return `EXPECTED_EMPTY[EXPECTED_OUTSIDE_PROCESSING_SCOPE]` for
cells outside the 2-month sample windows. Recommend the latter — keeps scope policy in-line with capability while
reflecting operator scope.

**Action required for A3 re-run**: cells outside the 2-month sample windows for tradfi tbbo + trades should NOT count as
`MISSING_EXPECTED` — they should classify as `OK_OPERATOR_SCOPED_OUT`. New A3 classification status to add.

## Refresh cadence

- **Annual**: refresh `US_MARKET_HOLIDAYS` + `HALF_DAY_SESSIONS` for the new year (last year + new year both must be
  present).
- **On every new venue scaffold**: append to the relevant `*_VENUE_LAUNCH_DATES` dict + (when `SourceCapability` index
  integration lands) populate `coverage_start`.
- **On any operator-driven gap-policy change**: append to this sidecar + extend oracle accordingly.
- **Before every Phase D plan ship**: re-run A2 dump + A3 divergence to catch any new gap that landed.
