---
title: Wave 3.X residual SSOTs + classifier extensions + reconcilers — 2026-05-08
type: sub-plan
status: active
created: 2026-05-08
deadline: 2026-05-23
parent_plan: writegate_honest_coverage_endtoend_2026_05_06.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

> **🟡 STAMPING SCOPE FOLDED INTO UMBRELLA — `available_at_lookahead_bias_completion_2026_05_08`** (codified 2026-05-08)
>
> **Track E ONLY** (4 sports stamping helpers `stamp_available_at_lineups` / `stamp_available_at_injuries` /
> `stamp_available_at_post_match_cascade` / `stamp_available_at_odds_snapshot`) is folded into the available_at
> umbrella. **Tracks A + D** are folded into the `manifest_evolution_master` umbrella (above). Track E executes as part
> of the available_at umbrella's per-asset_group cascade — NOT in isolation.
>
> Stamping owner:
> [`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md)

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_master_2026_05_08`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of: [`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md)
>
> This plan's phases land in gate(s): **G1** (Track A — UAC HALF_DAY_SESSIONS + EXPECTED_PARTIAL_HALF_DAY) + **G2**
> (Track D — zero-activity-bar audit)

# Wave 3.X residual SSOTs + classifier extensions + reconcilers

## Why this plan exists

The 25-dimension audit captured during the writegate Phase 3.D.5 Wave 3.X work (operator msgs 6-10) surfaced a set of
**residual SSOTs and classifier extensions** that don't fit cleanly inside the writegate plan body — they're greenfield
UAC additions, UTL extensions, and one-time reconciler scripts that compose with but don't depend on the Wave 4
emission-policy work.

Operator greenlight 2026-05-08: ship these in parallel with Wave 4 slice (b/c). None block each other; none block
Wave 4. The work splits into 5 tracks, each with its own owner-and-blast-radius shape.

## Tracks (parallel; no inter-track dependencies)

### Track A — Calendar SSOTs (UAC, ~1.5 days)

**Why**: `EXPECTED_PARTIAL_HALF_DAY` + `EXPECTED_OUTSIDE_TRADING_HOURS` are members of the `EmptyConfirmedReason`
taxonomy (UAC@145457e), but the SSOTs the classifier needs to fire those reasons don't exist yet. Without them, the
classifier silently falls through to `SOURCE_RETURNED_ZERO` for legitimate half-day / outside-hours shards — producing
incorrect operator dashboards and ML training NaN-fill mistakes.

**Files to create**:

- [x] [UAC] P0. NEW `unified_api_contracts/registry/half_day_sessions.py` —
      `HALF_DAY_SESSIONS: dict[str, frozenset[date]]` mapping venue → frozenset of dates that are half-day sessions per
      published exchange calendars. Seeded NYSE / NASDAQ / CBOE / NYSE_ARCA / AMEX / CME / ICE / FX with US-equity
      half-day calendar (Black Friday + eligible Christmas Eve + eligible July 3) for 2020-2028; EUREX / DTB with
      Christmas Eve + New Year's Eve. Helpers `is_half_day_session(venue, day)` + `get_half_day_dates(venue)`. Cites
      source-of-truth URLs in module docstring (CME / NYSE / CBOE / Eurex official calendars). **SHIPPED 2026-05-10
      UAC@bdc84ed**.
- [x] [UAC] P0. NEW `unified_api_contracts/registry/venue_session_hours.py` —
      `VENUE_SESSION_HOURS: dict[tuple[str, int], tuple[time, time]]` keyed by `(venue, weekday_0_to_6)` →
      `(open_utc, close_utc)` tuple (matching `datetime.weekday()` convention). Seeded NYSE / NASDAQ / NYSE_ARCA / AMEX
      (Mon-Fri 13:30-20:00 UTC EDT), CBOE (Mon-Fri 13:30-20:15 UTC for VIX), CME GLBX (Mon-Fri post-midnight 00:00-21:00
      UTC + Sun pre-midnight 22:00-23:59:59 UTC, with classifier-side compose for the wrap), ICE / FX aliases, EUREX /
      DTB (Mon-Fri 07:00-20:00 UTC CEST). 24/7 venues (binance / bybit / okx / kraken / etc.) intentionally absent — the
      `is_within_venue_session_hours` helper falls through to `True` for any venue not in the registry, matching
      existing `session_times.is_trading_hours` 24/7 default. Helpers `is_within_venue_session_hours(venue, ts)` +
      `get_session_window(venue, weekday)` + `is_venue_registered(venue)`. Coexists with `session_times.SessionWindow`
      (different read pattern — flat-keyed for classifier hot path vs dataclass for orchestrator open/close datetime
      derivation; not double-SSOT). Half-day shortening composition documented in module docstring (caller narrows close
      time per published early-close calendar; varies by event so not seeded here). **SHIPPED 2026-05-10 UAC@bdc84ed**.
- [x] [TEST] P0. UAC unit tests for both registries: half-day boolean per venue × date matrix; session-hour bounds
      checks per venue × weekday × representative timestamp; closed-set drift guard against `EmptyConfirmedReason`
      members `EXPECTED_PARTIAL_HALF_DAY` + `EXPECTED_OUTSIDE_TRADING_HOURS`. **SHIPPED 2026-05-10 UAC@bdc84ed**: 33
      tests across `tests/unit/test_half_day_sessions.py` (14) + `tests/unit/test_venue_session_hours.py` (19); all
      pass. Coverage: known-half-day-true / regular-day-false / full-holiday-not-half-day / 24/7-venue-false /
      case-insensitive; in-session / pre-market / post-close / weekend / 24/7-default-True / naive-tz / boundary
      open-inclusive / close-exclusive / CBOE 20:15 close / registry membership; both enum drift guards. Ruff +
      basedpyright clean.
- [ ] [UTL] P0. Extend `unified_trading_library/legacy_reason_classifier.py` to consume both registries: when input
      shard's day is a half-day → emit `EXPECTED_PARTIAL_HALF_DAY`; when intra-day shard timestamp falls outside the
      venue session hours → emit `EXPECTED_OUTSIDE_TRADING_HOURS`. Closed-set drift guard.
- [ ] [TEST] P0. UTL classifier tests: half-day day for ES.OPT venue → reason matches; weekend for venue NYSE →
      EXPECTED_WEEKEND (existing rule); pre-market timestamp for NYSE shard → EXPECTED_OUTSIDE_TRADING_HOURS.

### Track B — Sports per-source coverage SSOTs (UAC, ~2 days)

**Why**: sports adapters write `empty_confirmed` shards for legitimate per-source-doesn't-cover-this-league cases
(Understat covers EPL/LaLiga/SerieA/Bundesliga/Ligue1 only; transfermarkt has per-country transfer windows; footystats
has per-league season boundaries). Without per-source SSOTs, the classifier emits `SOURCE_RETURNED_ZERO` and the
data-status UI flags every Understat shard for La Liga as a possible coverage hole — false-positive noise.

**Files to create**:

- [ ] [UAC] P0. NEW `unified_api_contracts/canonical/domain/sports/understat_coverage.py` —
      `UNDERSTAT_COVERED_LEAGUES: frozenset[str]` containing the 5 league_ids Understat actually covers (per published
      Understat coverage). Helper: `does_understat_cover(league_id: str) -> bool`. Cite source: scrape of Understat's
      per-league index page as of 2026-05-08.
- [ ] [UAC] P0. EXTEND `unified_api_contracts/canonical/domain/sports/transfer_windows.py` — **CORRECTION 2026-05-08
      audit**: file already EXISTS with a different API (`is_transfer_window_open` / `get_transfer_windows_for_year` /
      `most_recent_window_close`). Re-scoped: ADD `TRANSFER_WINDOWS: dict[str, list[tuple[date, date]]]` keyed by
      country_code → list of (window_open, window_close) ranges per the country's published transfer registration
      windows (FIFA + national-FA rules) + `is_within_transfer_window(country_code: str, day: date) -> bool` helper.
      Seed with EU countries (England, Spain, Italy, Germany, France) + USA (MLS-specific summer/winter windows) + Japan
      (J.League windows). Wire `legacy_reason_classifier` to the new dict (existing API remains for callers that need
      year-scoped queries).
- [ ] [UAC] P0. EXTEND `unified_api_contracts/sports/provider_league_ids.py` — add `season_start: date` +
      `season_end: date` fields to the existing `FOOTYSTATS_SEASON_IDS` dict entries. Source: footystats per-league
      season pages. Helpers: `get_footystats_season_bounds(league_id: str, season: str) -> tuple[date, date]` +
      `is_within_footystats_season(league_id: str, season: str, day: date) -> bool`. Composes with the existing
      `SOURCE_COVERAGE_START` clip — pre-season days within the source's coverage window get the new
      `EXPECTED_PRE_SEASON` reason; post-season days get `EXPECTED_POST_SEASON`.
- [ ] [UTL] P0. Extend `legacy_reason_classifier.py::_classify_sports` to consume the three new SSOTs: source ==
      Understat AND league not in covered set → `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`; source == transfermarkt AND day
      outside transfer window → `EXPECTED_OUTSIDE_TRANSFER_WINDOW`; source == footystats AND day outside season bounds →
      `EXPECTED_PRE_SEASON` or `EXPECTED_POST_SEASON` per which side of the window.
- [ ] [TEST] P0. UAC tests cover each new SSOT's seeded entries + helper boolean correctness; UTL classifier tests cover
      each new EXPECTED\_\* reason firing for the right (source, league_id, day) shape; closed-set drift guard.

### Track C — Reconciler script (instruments-service, ~1 day)

**Why**: shards classified pre-2026-05-07 as `empty_confirmed` with blank `error_reason` (the silent-fallback bug
cleaned up by Wave 2 of writegate Phase 3.D.5) included MANY shards that should now be classified with one of the new
typed reasons (`EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_OUTSIDE_TRADING_HOURS` / `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`
/ `EXPECTED_OUTSIDE_TRANSFER_WINDOW` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`). The 2026-05-07
reconcile_blank_error_reason_rows.py migration only flipped them to a default reason; with Track A + B SSOTs landed this
reconciler can re-classify them with the now-available typed reasons.

**File**:

- [ ] [instruments-service] P0. NEW `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` — walks the
      canonical manifest, finds
      `(capture_status=empty_confirmed AND error_reason ∈ {SOURCE_RETURNED_ZERO,     EXPECTED_INSTRUMENT_NOT_LISTED})`
      rows that were stamped during the 2026-05-07 sweep, re-runs them through the now-extended
      `classify_blank_reason_row()` with Track A + B SSOTs available, and where the extended classifier returns a
      more-specific typed reason (e.g. `EXPECTED_PARTIAL_HALF_DAY` instead of `SOURCE_RETURNED_ZERO`), stamps the new
      reason on the row. Same shape as the existing reconciler scripts: `--asset-group` flag, `--apply-flips` gate
      (default scan-only), `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=` per-VM-shard isolation protocol, RECONCILER\_\*
      events, CSV audit, `--max-flips-per-run` halt safety.
- [ ] [TEST] P0. Smoke-test on a synthetic manifest with planted `SOURCE_RETURNED_ZERO` rows for half-day-CME-shards →
      reconciler finds them, scan-only mode reports the proposed new reasons, `--apply-flips` mode flips them.
- [ ] [DOCS] P0. Codex audit-ledger update under
      `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md` § "Reason taxonomy" — note the
      reconciler is the canonical mechanism for legacy reason upgrades whenever a new EXPECTED\_\* reason is added to
      UAC `EmptyConfirmedReason`.

### Track D — Wave 3.M zero-activity-bar adapter audit (every per-shard adapter; ~2 days)

**Why**: operator directive 2026-05-07 (msg 8) added the 4-category empty-output decision matrix to CLAUDE.md, with case
D being "source returned zero BUT instruments-service catalog says alive AND day within venue market hours → write
zero-activity bars + record_captured". Wave 2 of writegate Phase 3.D.5 shipped the catalog-aware classifier at the
manifest level; Wave 3.M extends the same logic to the WRITE side so adapters emit shape-correct zero-activity-bars
instead of writing nothing.

**Audit scope** (every per-shard adapter):

- [ ] [MTDS] P0. Audit MTDS adapters (`market_tick_data_service/adapters/*.py`) for the case-A vs case-D split. For each
      adapter, when source returns zero AND the catalog-aware guard reports the instrument alive: replace the current
      `record_empty()` call with a per-data*type zero-activity-bar emission per the table in CLAUDE.md "Four-category
      empty-output decision" rule. Per-data_type bar shape: -
      `ohlcv*\*`→ O=H=L=C=prior_LTP, volume=0, trade_count=0, available_at=window_close.     -`trades`→ empty parquet (0 rows is correct; manifest carries`record_captured`with row_count=0 + a       zero-activity flag column).     -`book_snapshot_5`→ carry-forward last bid/ask at all 5 levels, mid=last_mid, spread=last_spread.     -`derivative_ticker`
      → carry-forward last open_interest / mark_price / index_price.
- [ ] [MDPS] P0. Audit MDPS calculators for the same case-D handling at the candle-aggregation boundary.
- [ ] [features-* (8 services)] P1. Audit each features service's calculators per same shape — especially the
      sports/prediction case-D-with-bookmaker-odds-carry-forward.
- [ ] [TEST] P0. Per-adapter smoke tests: synthetic instrument-alive-but-source-zero day → zero-activity-bar with
      correct shape; instrument-not-yet-listed day → record_empty with EXPECTED_INSTRUMENT_NOT_LISTED (existing rule);
      pre-genesis-chain day for DeFi → record_empty with EXPECTED_PRE_GENESIS_CHAIN.
- [ ] [DOCS] P0. Codex update to `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md` §
      "Zero-activity-bar shape" — table of bar-shape per data_type, with explicit pre-LTP-carry-forward semantics + the
      volatility-smile use case (operator-flagged: every strike must be visible even on zero-volume days for
      cross-instrument analysis).

### Track E — Wave 3.S sports per-source rules (sports services, ~3 days)

**Why**: sports adapters need per-source rules for things that don't fit the per-day capture/empty model — match-end
detection cascade for `available_at` stamping, lineup pre-match carry-forward semantics, odds-snapshot freshness
windows. These overlap with Track A+B SSOTs (which provide the structural denominator) but are about the write-time
stamping logic.

**Files / changes**:

- [ ] [UTL] P0. Extend `availability_stamping.stamp_available_at_*` family with the four sports stamp helpers per the
      CLAUDE.md "available_at is per-row, write-time" rule: -
      `stamp_available_at_lineups(kickoff: datetime) -> datetime` returns `kickoff - 60min` (conservative — clip earlier
      leaks per operator directive). - `stamp_available_at_injuries(report_time: datetime) -> datetime` per-row event
      time. -
      `stamp_available_at_post_match(match_end_time: datetime | None, kickoff: datetime,       source_cascade: list[str]) -> datetime`
      — cascade detection per CLAUDE.md (api_football native → SFI progressive freeze → footystats / understat →
      low-confidence `kickoff + 120min` fallback). Returns the first non-None match_end_time it finds; the cascade order
      is the source-priority order from UAC. - `stamp_available_at_odds_snapshot(snapshot_time: datetime) -> datetime`
      returns publication time per snapshot.
- [ ] [features-sports] P0. Wire the new stamp helpers at the sports calculator emission boundaries that currently emit
      blank or read-time-derived `available_at` columns.
- [ ] [TEST] P0. Unit tests cover each stamp helper's edge cases + a regression test on a synthetic post-match shard
      that verifies the cascade falls through to `kickoff + 120min` only when all upstream cascades are empty.
- [ ] [DOCS] P0. Codex update to `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md` adding the 4
      sports stamping rules to the existing temporal-availability table.

## Success criteria

- Tracks A + B + C land in lockstep — Track C reconciler depends on A+B SSOTs being available. Sequence: A & B in
  parallel (~2 days each), then C (~1 day).
- Tracks D + E land in parallel with A/B/C — independent.
- All 5 tracks shipped + green QG by ~2026-05-15 (1 week from this plan creation; gives 1-week buffer to the 2026-05-23
  live-DeFi cutover).
- Workspace-wide QG passes after each track.
- Memory entry per shipped track per the workspace memory model.

## Coordination with other plans

- **Wave 4 slice (b/c)** in
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) — runs in
  parallel; no dependencies between this plan and Wave 4. The classifier extensions in tracks A+B make more shards
  classify as `empty_confirmed` (vs `attempted_failed`) which improves the completeness_fraction denominator the Wave 4
  helper computes — but that's strictly improvement, not a hard dependency.
- **`master_to_live_defi_2026_05_23.md`** — this plan is a Group D (Coverage & shard) feeder; tracks A+B clear
  false-positive coverage holes in the operator-facing dashboards before the May-23 cutover.
- **`master_readiness_data_status.md` / `data_status_drilldown_shard_atom_alignment_2026_05_07.md`** — tracks A+B
  populate denominators that the data-status UI consumes; track C reconciler back-fills history so existing drilldown
  views light up the new typed reasons retroactively.

## Why this isn't folded into the writegate plan

The writegate plan is already 3221 lines covering the cross-cutting Phase 3.D.5 architecture work. These residuals are
independent SSOT additions + classifier extensions + a one-time reconciler — they don't fit the writegate plan's
"phase-by-phase honest-coverage rollout" narrative. Spinning them into a sub-plan keeps the writegate plan focused on
its through-line + makes track ownership cleaner per the daily work-split process.

## Open questions

(none currently — operator greenlight 2026-05-08 covered the full track set)

## DONE-2026-05-10 (Tab H — wave3x Track A UAC half)

Track A's UAC half shipped end-to-end on real infrastructure (sibling-clone UAC@bdc84ed pushed to live-defi-rollout).
Code, tests, ruff, basedpyright all green; full-execution criterion met locally + visible on origin.

**Code commits:**

- `unified-api-contracts@bdc84ed` — `feat(uac): half_day_sessions + venue_session_hours SSOTs (wave3x Track A)` —
  4 files, 608 insertions. Modules + 33 unit tests. Foreign-dirty UAC files (`tests/internal/unit/test_instruments_live_event_taxonomy.py` /
  `tests/unit/test_archetype_capability_may_23_coverage.py` / `unified_api_contracts/__init__.py`) untouched per
  workspace foreign-WIP rule.

**Plan-flip commit:**

- `unified-trading-pm@72bf558e` — `docs(plans): wave3x Track A — UAC half_day_sessions + venue_session_hours SSOTs
  shipped` — Track A's 3 P0 UAC todos flipped to `[x]`. Pathspec-scoped (`git commit --only -- <path>`) to leave the
  ~50 foreign-dirty PM codex docs untouched.

**Full-execution verification (per "Plans Run To Actual Completion" HARD RULE):**

- `cd unified-api-contracts && .venv/bin/python -m pytest tests/unit/test_half_day_sessions.py
  tests/unit/test_venue_session_hours.py -v` → **33 passed in 3.75s**.
- `.venv/bin/python -m ruff check <new-files>` → **All checks passed!**
- `.venv/bin/python -m basedpyright <new-files>` → **0 errors, 0 warnings, 0 notes**.
- `.venv/bin/python -m ruff format <new-files>` → no reformats needed.
- `git rev-list --left-right --count HEAD...origin/live-defi-rollout` → **0 0** (UAC + PM both at parity with origin
  post-push).

**Deferred items still open in this plan (not Tab H scope):**

- Track A `[UTL]` classifier extension (`unified_trading_library/legacy_reason_classifier.py` to consume both new
  UAC SSOTs + emit `EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_OUTSIDE_TRADING_HOURS`) — `- [ ]` in plan body. Status:
  `helper-shipped` for UAC dependencies; UTL wire-in is the natural next step. Successor: any Tab/agent picking up
  Track A's UTL half. Not blocked — UAC SSOTs are now consumable.
- Track A `[TEST]` UTL classifier tests — paired with the UTL extension above.
- Tracks B / C / D / E — independent of Track A; not picked up this session.

**Out-of-scope this session:**

- Track B (sports per-source SSOTs) — explicitly skipped per spawn prompt to avoid asset-group authority collision.
- Phase 4.A items 1/2/3 of `writegate_honest_coverage_endtoend_2026_05_06.md` — already shipped (deployment-api@453836d
  / @7d57056 / @3b0477a, verified). Phase 4.A item 4 (live-vs-historical envelope alert) is `- [ ]` and explicitly
  multi-repo deferred (UAC + UTL + 3 services) — out of clean context for a single tab.
