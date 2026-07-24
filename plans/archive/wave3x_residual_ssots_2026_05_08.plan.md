---
doc_type: plan
title: Wave 3.X residual SSOTs + classifier extensions + reconcilers — 2026-05-08
summary:
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos:
  [
    deployment-api,
    features-service,
    instruments-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (design, multiplier 0.6×).

  Owner agent: fill baseline + multiply × 0.6 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
parent_epic: sports_master
priority: P2
---

## Deferred work — migrated to:

| Item                                                                                                     | Successor plan                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track D — case-D zero-activity-bar implementation (MTDS/MDPS/features wire-in + per-adapter smoke tests) | [`wave3x_track_d_implementation_2026_05_19.md`](../active/wave3x_track_d_implementation_2026_05_19.md) — post-2026-05-23 cutover                      |
| Track E — features-sports stamp-helper calculator wire-in at emission boundaries                         | [`available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md) Phase B — post-consolidation |

> **🟡 STAMPING SCOPE FOLDED INTO UMBRELLA — `available_at_lookahead_bias_completion_2026_05_08`** (codified 2026-05-08)
>
> **Track E ONLY** (4 sports stamping helpers `stamp_available_at_lineups` / `stamp_available_at_injuries` /
> `stamp_available_at_post_match_cascade` / `stamp_available_at_odds_snapshot`) is folded into the available_at
> umbrella. **Tracks A + D** are folded into the `manifest_evolution_master` umbrella (above). Track E executes as part
> of the available_at umbrella's per-asset_group cascade — NOT in isolation.
>
> Stamping owner:
> [`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md)

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_SUPERSEDED_2026_05_21`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of:
> [`plans/epics/manifest_evolution_SUPERSEDED_2026_05_21.md`](../epics/manifest_evolution_SUPERSEDED_2026_05_21.md)
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
- [x] [UTL] P0. **SHIPPED 2026-05-11 UTL@`3fbc6b3`** (slot 3, harsh-wave3x-tab). `_classify_tradfi` extended: after the
      whole-day `non_trading_day_reason` check — `is_half_day_session(venue, day)` (UAC `registry.half_day_sessions`
      @bdc84ed) → `EXPECTED_PARTIAL_HALF_DAY`; an intra-day `timestamp` cell outside
      `is_within_venue_session_hours(venue, ts)` (UAC `registry.venue_session_hours`) →
      `EXPECTED_OUTSIDE_TRADING_HOURS`. Added `_parse_iso_date` / `_parse_iso_datetime` defensive parsers (None → fall
      through to `SOURCE_RETURNED_ZERO`). Closed-set drift guard extended (the existing
      `test_every_classifier_returns_value_inside_empty_confirmed_reasons` test gets the new sample rows).
- [x] [TEST] P0. **SHIPPED 2026-05-11 UTL@`3fbc6b3`** (slot 3): `tests/unit/test_legacy_reason_classifier.py` extended
      (NOT a parallel file — same file per the "expand existing test files" rule). +13 tests (half-day / pre-market-ts /
      in-session-ts / 24-7-venue + the sports ones below) + 5 new entries in the closed-set drift guard. 33 tests pass;
      ruff clean; basedpyright clean modulo a PRE-EXISTING `reportPrivateImportUsage` on the unchanged
      `from unified_api_contracts import non_trading_day_reason` line.

### Track B — Sports per-source coverage SSOTs (UAC, ~2 days)

**Why**: sports adapters write `empty_confirmed` shards for legitimate per-source-doesn't-cover-this-league cases
(Understat covers EPL/LaLiga/SerieA/Bundesliga/Ligue1 only; transfermarkt has per-country transfer windows; footystats
has per-league season boundaries). Without per-source SSOTs, the classifier emits `SOURCE_RETURNED_ZERO` and the
data-status UI flags every Understat shard for La Liga as a possible coverage hole — false-positive noise.

**Files to create**:

- [x] [UAC] P0. **SHIPPED 2026-05-11 UAC@`7c8b5ad`** (slot 3, harsh-wave3x-tab). **DEVIATION (DRY, per "No double
      SSOT")**: NOT a new `understat_coverage.py` file — the data already lives in `provider_league_ids.py`'s
      `UNDERSTAT_NAMES` + the private `_UNDERSTAT_LEAGUE_COVERAGE`. Added a public alias `UNDERSTAT_COVERED_LEAGUES` (=
      `frozenset(UNDERSTAT_NAMES.keys())` — single SSOT) + `does_understat_cover(league_id)` to
      `provider_league_ids.py`, re-exported from the `sports` facade. 5 leagues (BUNDESLIGA / EPL / LA_LIGA / LIGUE_1 /
      SERIE_A).
- [x] [UAC] P0. **SHIPPED 2026-05-11 UAC@`7c8b5ad`** (slot 3). EXTEND `transfer_windows.py` — **DEVIATION (DRY)**: NOT a
      new `TRANSFER_WINDOWS: dict[country_code, list[(date,date)]]` dict — that would duplicate the existing
      `_COUNTRY_DEFAULTS` + `_YEAR_OVERRIDES` (which already cover 25+ countries incl. COVID-2020 overrides). Added
      `is_within_transfer_window(country_code: str, day: date) -> bool` — country-code-keyed sibling of the existing
      league-id-keyed `is_transfer_window_open`; reads the same SSOT via `_get_candidate_windows` / `_resolve_specs` (no
      duplicate calendar dict). Re-exported from the `sports` facade. The classifier wires to `is_transfer_window_open`
      (which already takes a league_id) — see Track B UTL below.
- [x] [UAC] P0. **SHIPPED 2026-05-11 UAC@`7c8b5ad`** (slot 3). EXTEND season bounds — **DEVIATION (DRY)**: NOT
      `season_start`/`season_end` fields on `FOOTYSTATS_SEASON_IDS` (those are `int` season IDs; adding fields would
      break `get_provider_league_id`) — the season _boundary dates_ already exist via `season_dates.get_season_boundary`
      (derived from `LeagueDefinition.season_months`). Added
      `get_footystats_season_bounds(league_id, season_year) ->     tuple[date, date]` +
      `is_within_footystats_season(league_id, season_year, day) -> bool` +
      `footystats_season_status_for_day(league_id, day) -> Literal["EXPECTED_PRE_SEASON","EXPECTED_POST_SEASON"] | None`
      to `season_dates.py`, re-exported from the `sports` facade. (Composes with the existing `SOURCE_COVERAGE_START`
      clip — that handles before-FootyStats-coverage-started; this handles before/after the league's season window.)
- [x] [UTL] P0. **SHIPPED 2026-05-11 UTL@`3fbc6b3`** (slot 3, harsh-wave3x-tab; bundled with the Track A UTL extension —
      both touch `legacy_reason_classifier.py`). `_classify_sports` extended: after the coarse known-gap +
      pre-source-coverage-start checks, when the shard has a `league_id` — understat +
      `not does_understat_cover(league_id)` → `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`; transfermarkt + a
      transfer-records `data_type` (the `"transfer" in     data_type` guard keeps the rule off year-round
      PLAYER_VALUES) + day outside `is_transfer_data_expected(league_id, day)` (window + post-close grace) →
      `EXPECTED_OUTSIDE_TRANSFER_WINDOW`; footystats + `footystats_season_status_for_day(league_id, day)` non-None →
      `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`. Consumes the UAC@7c8b5ad SSOTs (Track B above). 9 sports tests
      added (covered/uncovered/no-league understat; off-window/in-window/player-values transfermarkt; pre/post/in-season
      footystats) — see the `[TEST]` item under Track A above.
- [x] [TEST] P0. UAC tests — **SHIPPED 2026-05-11 UAC@`7c8b5ad`** (slot 3):
      `tests/unit/sports/test_per_source_coverage_ssots.py`, 22 tests covering each new SSOT's entries + helper
      correctness + cross-year-vs-calendar-year footystats season status + typed-reason-string check + facade re-export;
      all pass; ruff + basedpyright clean. **UTL classifier tests pending — bundled with the Track B UTL
      `_classify_sports` extension above.**

### Track C — Reconciler script (instruments-service, ~1 day)

**Why**: shards classified pre-2026-05-07 as `empty_confirmed` with blank `error_reason` (the silent-fallback bug
cleaned up by Wave 2 of writegate Phase 3.D.5) included MANY shards that should now be classified with one of the new
typed reasons (`EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_OUTSIDE_TRADING_HOURS` / `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`
/ `EXPECTED_OUTSIDE_TRANSFER_WINDOW` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`). The 2026-05-07
reconcile_blank_error_reason_rows.py migration only flipped them to a default reason; with Track A + B SSOTs landed this
reconciler can re-classify them with the now-available typed reasons.

**File**:

- [x] [instruments-service] P0. **SHIPPED 2026-05-11 instruments-service@`485c57b`** (slot 3, harsh-wave3x-tab).
      `scripts/reconcile_legacy_blank_to_typed_reason.py` — walks `empty_confirmed` rows whose `error_reason` is a
      2026-05-07-sweep default (`SOURCE_RETURNED_ZERO` / `EXPECTED_INSTRUMENT_NOT_LISTED`), re-runs each through
      `classify_blank_reason_row` (deep import — it's not on the UTL facade) now that the Track A SSOTs (UAC@bdc84ed) +
      Track B SSOTs (UAC@7c8b5ad) are available, and upgrades rows where the classifier returns a more-specific
      `EXPECTED_*` (≠ `SOURCE_RETURNED_ZERO`, ≠ current reason; **never downgrades; never flips `capture_status`** — the
      `empty_confirmed→attempted_failed` discrimination for cefi/defi/tradfi-at-instrument-grain is the writeguard's /
      `reconcile_blank_error_reason_rows.py`'s job). Same shape as `reconcile_expected_absence_reasons.py`:
      `--asset-group`, `--apply-flips` (default scan-only) + CSV audit, `MANIFEST_PER_VM_SHARDS=true`+`VM_NAME=` guard,
      `RECONCILER_*` events, `--max-flips-per-run`, per-VM-shard write (consolidator merges last-writer-wins). **FINDING
      (adjacent, → writegate Phase 3.D.5 / a follow-up)**: the dry-run found ~604,951 defi + ~1,868,285 sports
      `empty_confirmed/SOURCE_RETURNED_ZERO` rows. Per the operator directive (defi can't legit-empty at instrument-day
      grain) many of the defi ones arguably should be `attempted_failed` — but the pass-1 sweep only handled BLANK
      reasons (these already have `SOURCE_RETURNED_ZERO`), so they were never flipped. This reconciler deliberately
      doesn't do that status-flip (it's a reason-UPGRADE, not a status-flip); the gap is for the writeguard / a
      follow-up.
- [x] [TEST] P0. **SHIPPED 2026-05-11 instruments-service@`485c57b`** (slot 3):
      `tests/unit/test_reconcile_legacy_blank_to_typed_reason.py` (importlib-loaded script-module pattern, matching
      `test_purge_legacy_unsharded_manifest_rows.py`). 6 tests: SWEEP_DEFAULT_REASONS constant; candidate-mask picks
      sweep-defaults only / missing-columns→all-false; `main()` scan-only proposes the
      `SOURCE_RETURNED_ZERO → EXPECTED_WEEKEND` upgrade for a planted Saturday CME row (CSV assertion); `main()`
      `--apply-flips` rewrites `error_reason` in the uploaded per-VM shard; `--apply-flips` aborts `rc=4` without
      `MANIFEST_PER_VM_SHARDS`. All pass; ruff clean; basedpyright `scripts/*` baseline matches the sibling reconciler
      (~60 `reportAny`/`reportUnknownMemberType` from `google.cloud` no-stubs + pandas `.loc` — `scripts/` is not
      strict-typed in instruments-service QG). **Full-execution evidence — dry-run on the 5 production manifests
      (2026-05-11)**: tradfi 141,401 rows / 0 candidates; sports 2,675,696 rows / 1,868,285 candidates / 0 upgrades;
      cefi 2,632,931 rows / 0 candidates; defi 1,606,190 rows / 604,951 candidates / 0 upgrades; prediction 16,812 rows
      / 41 candidates / 0 upgrades. Reconciler RAN clean on all 5 (no errors, no incorrect reclassifications). 0
      upgrades surfaced because the existing 2026-05-07 sweep + orchestrator calendar-pre-skip already classified most
      rows, AND the new Track A+B branches need finer per-row columns (`league_id` for sports / intraday `timestamp` for
      tradfi / `chain` for defi) that current manifest rows mostly lack — the reconciler is ready for whenever those
      columns are written / a new reason is added. (Operator decides if/when to run `--apply-flips` after CSV review —
      currently a no-op given 0 upgrades.)
- [x] [DOCS] P0. **SHIPPED 2026-05-11 PM** (slot 3): codex update to
      `/codex/02-data/honest-absence-downstream-handling.md` — added a
      `### Reconciler chain for legacy error_reason (the three passes)` subsection (under "Reader-side fallback for
      legacy rows") naming all 3 reconcilers in order + noting `reconcile_legacy_blank_to_typed_reason.py` is the
      **canonical mechanism for legacy-reason upgrades whenever a new `EXPECTED_*` reason is added to UAC
      `EmptyConfirmedReason` or a new fine-grained SSOT lands** + the 2026-05-11 dry-run result. (The plan said
      `availability-manifest-and-data-status.md` § "Reason taxonomy" but that doc has no such section — the
      reason-taxonomy content lives in `honest-absence-downstream-handling.md`, so the update landed there.)

### Track D — Wave 3.M zero-activity-bar adapter audit (every per-shard adapter; ~2 days)

**Why**: operator directive 2026-05-07 (msg 8) added the 4-category empty-output decision matrix to CLAUDE.md, with case
D being "source returned zero BUT instruments-service catalog says alive AND day within venue market hours → write
zero-activity bars + record_captured". Wave 2 of writegate Phase 3.D.5 shipped the catalog-aware classifier at the
manifest level; Wave 3.M extends the same logic to the WRITE side so adapters emit shape-correct zero-activity-bars
instead of writing nothing.

> **🟢 AUDIT COMPLETE 2026-05-11 (slot 3, harsh-wave3x-tab — 6 read-only sub-agents)** — findings doc:
> [`plans/archive/issues/wave3x_track_d_findings_2026_05_11.md`](../archive/issues/wave3x_track_d_findings_2026_05_11.md)
> (per-adapter A/B/C/D classification per CLAUDE.md "Four-category empty-output decision"). **Anti-sequencing
> conclusion**: Track D forces **no new manifest schema column / shard-atom dimension** (the `zero_activity` marker is a
> per-row parquet-schema value, not a manifest column) → the case-D _implementation_ can safely defer post-cutover.
> **ONE candidate new `EmptyConfirmedReason`** surfaced (`EXPECTED_KNOWN_SOURCE_GAP` for mid-history accepted gaps — VIX
> 15m gap + sports `KNOWN_COVERAGE_GAPS`) — Ikenna slot 5 + slot 1 decision pending (Phase-1-now-vs-defer; tiny additive
> enum). The audit ALSO surfaced current correctness bugs NOT in scope for Track D (escalated in the findings doc):
> **P0-1** MTDS orchestrator `record_empty(row_key=...)` without `reason=` at `engine/orchestrator.py:2671/:2808/:2849`
> → `LegacyBlankErrorReasonError` → honest-coverage sentinel pass silently aborts for CeFi/sports; **P0-2** MDPS
> canonical-writer/`record_captured`/4-pillar-write-gate path is DEAD on the live path (MRO-overridden by the legacy
> `upload_bytes`-no-manifest `_write_candles`) + `tradfi/ohlcv_passthrough.py:266 _create_full_day_empty_output` still
> emits the 1440-NaN-bar incident shape + `output_schemas.py` nullable=True for trades/ohlcv + triple-SSOT candle
> pipeline; **commodity** `cli/handlers/batch_handler.py:251-290` phantom manifest-row bug; **cross_instrument** 4
> calculators `np.zeros(n)` for continuous features; **sports** calculators `fillna(magic)` masking-absence +
> half-shipped quality-gate. → owners: writegate Phase 2.A/2.E + Harsh slot 5 (live-pipeline) + Harsh slot 6 (QG sweep).

**Audit scope** (every per-shard adapter):

- [x] ✅ [MTDS] P0. Audit MTDS adapters + (when source returns zero AND catalog-aware guard reports the instrument
      alive) replace the `record_empty()` call with a per-data\*type zero-activity-bar emission per the CLAUDE.md table:
      `ohlcv**`→ O=H=L=C=prior_LTP, volume=0, trade_count=0, available_at=window_close;`trades`→ empty parquet (0 rows
      ok; manifest`record_captured`row_count=0 + zero-activity flag column);`book_snapshot_5`→ carry-forward last
      bid/ask 5 levels;`derivative_ticker`→ carry-forward last open_interest/mark_price/index_price. **AUDIT DONE
      2026-05-11** (slot 3 — D1+D2+D3 sub-agents; findings:`../archive/issues/wave3x_track_d_findings_2026_05_11.md`).
      **DEFERRED — case-D implementation post-cutover** per successor plan:
      `wave3x_track_d_implementation_2026_05_19.md`. Sports historical in instruments-service NOT MTDS (D3 finding).
- [x] ✅ [MDPS] P0. Audit MDPS calculators for the same case-D handling at the candle-aggregation boundary. **AUDIT DONE
      2026-05-11** (slot 3 — D4 sub-agent). **DEFERRED — case-D impl post-cutover** per successor plan:
      `wave3x_track_d_implementation_2026_05_19.md`. D4 findings (dead canonical-writer path + 1440-NaN TradFi
      passthrough + banned `_handle_empty_tick_data` / `_create_closed_market_candle`×2 /
      `_maybe_write_vix_gap_placeholder`) escalated to writegate Phase 2.A owner + Harsh slot 5 per findings doc.
- [x] ✅ [features-* (8 services)] P1. Audit each features service's calculators per same shape — especially the
      sports/prediction case-D-with-bookmaker-odds-carry-forward. **AUDIT DONE 2026-05-11** (slot 3 — D5+D6 sub-agents,
      against the consolidated `features-service`@52898f5a, 8 family subdirs). **DEFERRED — case-D impl post-cutover**
      per successor plan: `wave3x_track_d_implementation_2026_05_19.md`. D5/D6 findings escalated in findings doc.
- [x] ✅ [TEST] P0. Per-adapter smoke tests: synthetic instrument-alive-but-source-zero day → zero-activity-bar with
      correct shape; instrument-not-yet-listed day → `record_empty(EXPECTED_INSTRUMENT_NOT_LISTED)`; pre-genesis-chain
      day for DeFi → `record_empty(EXPECTED_PRE_GENESIS_CHAIN)`. **DEFERRED — part of case-D implementation** per
      successor plan: `wave3x_track_d_implementation_2026_05_19.md`. Tests pair with adapter wiring above.
- [x] [DOCS] P0. Codex update to `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md` §
      "Zero-activity-bar shape" — table of bar-shape per data_type, with explicit pre-LTP-carry-forward semantics + the
      volatility-smile use case (operator-flagged: every strike must be visible even on zero-volume days for
      cross-instrument analysis). **SHIPPED 2026-05-13 (slot 6 wave 2, PM@84e29700)**: added
      `## Zero-activity-bar shape (case-D design —     implementation deferred post-cutover)` section to
      `/codex/02-data/honest-absence-downstream-handling.md` — per-data_type carry-forward table
      (ohlcv/trades/book_snapshot/derivative_ticker/options_chain/DeFi-continuous/prediction CLOB), vol-smile
      constraint, Wave 3.M implementation requirements, and successor-plan pointer.
- [x] ✅ [PLAN] P2. **DEFERRED-AFTER-CUTOVER** File `plans/active/wave3x_track_d_implementation_<date>.md` — the Wave
      3.M case-D implementation plan. (evidence: `plans/active/wave3x_track_d_implementation_2026_05_19.md` created
      PM@5c54ed57 — scope: UTL `zero_activity_bars` primitive + catalog threading + MTDS/MDPS/features wire-in +
      per-adapter smoke tests. Post-2026-05-23 cutover. Owner: slot 1 or writegate Phase 3.D.5 Wave 2/3 owner.)

### Track E — Wave 3.S sports per-source rules (sports services, ~3 days)

**Why**: sports adapters need per-source rules for things that don't fit the per-day capture/empty model — match-end
detection cascade for `available_at` stamping, lineup pre-match carry-forward semantics, odds-snapshot freshness
windows. These overlap with Track A+B SSOTs (which provide the structural denominator) but are about the write-time
stamping logic.

**Files / changes**:

- [x] [UTL] P0. **SHIPPED 2026-05-11 UTL@`2ab3685`** (slot 3, harsh-wave3x-tab). Added to `availability_stamping.py`:
      `stamp_available_at_injuries(df, report_time_col="report_time")` (named alias over
      `stamp_available_at_event_time`); `stamp_available_at_odds_snapshot(df, snapshot_time_col="bm_time")` (named
      alias); `stamp_available_at_post_match_cascade(df, match_end_candidate_cols, kickoff_col, default_match_duration)`
      — generalises the existing `stamp_available_at_post_match`: per-row uses the first present-and-non-null candidate
      match-end column in source-priority order (api_football native → SFI progressive freeze → footystats/understat),
      falls back to `kickoff + 120min`; raises `AvailableAtStampingError` on empty-list / no-columns / all-NaT. Plus
      `INJURIES_REPORT_TIME_COL` / `ODDS_SNAPSHOT_TIME_COL` constants + 3 facade re-exports. **DEVIATION**: kept the
      module's DataFrame-shaped helper API (the plan body sketched scalar signatures `(kickoff: datetime) -> datetime`);
      `stamp_available_at_lineups` (kickoff−60min) already existed.
- [x] ✅ [features-sports] P0. Wire the new stamp helpers at the sports calculator emission boundaries. **DEFERRED →
      `available_at_schema_lift_post_cutover_2026_05_19.md` Phase B** (slot-8 2026-05-20). MTDS sports odds stamping
      (Harsh slot 4 scope) was absorbed by Ikenna slot 3 and shipped at MTDS@a512edf + UTL@f7b704fd (2026-05-11).
      Features-sports calculator/writer-boundary enforcement (Tab 12) is officially deferred per PM@cf9b9ba1 until
      `features_repo_consolidation_2026_05_08` Phase 5.c + chain links 0+1 ship; named successor is
      `available_at_schema_lift_post_cutover_2026_05_19.md` Phase B. UTL stamp helpers ready to consume.
- [x] [TEST] P0. **SHIPPED 2026-05-11 UTL@`2ab3685`** (slot 3): `tests/unit/test_availability_stamping.py` extended (NOT
      a parallel file — same file). +18 tests (injuries default/custom/missing-col; odds_snapshot default/custom;
      cascade priority-per-row / first-wins / single-candidate-matches-post_match / fallback-only / empty-list-raises /
      no-cols-raises / empty-df / all-NaT-raises / no-mutation; + UTL-facade re-export). 37 tests pass; ruff clean;
      basedpyright clean on `availability_stamping.py`.
- [x] [DOCS] P0. **SHIPPED 2026-05-11 PM** (slot 3): codex update to
      `/codex/02-data/honest-absence-downstream-handling.md` — added a
      `## Per-source available_at stamping helpers (UTL)` section with the per-helper rule table (lineups / injuries /
      odds_snapshot / post_match(+cascade) / event_time-for-weather / cefi_tick / offset+explicit) + the
      `record_captured` → `assert_available_at_present` → `LookaheadBiasError` enforcement note + the
      per-service-wire-in ownership pointer. (The plan said "existing temporal-availability table" but that table lives
      in `availability-manifest-and-data-status.md` / CLAUDE.md, not this doc — added a fresh section here instead,
      which also gives the doc's existing line-112 cross-ref a local target.)

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

## Deferred work after 2026-05-11 slot-3 session

The 2026-05-11 slot-3 (`harsh-wave3x-tab`) session shipped Tracks A-UTL + B + C + D (audit) + E. Items still open
(deferred to named owners) are tracked here so the next agent picks up cleanly:

| Track / item                                                                                                                                                                                                                                                                                                           | Status as of 2026-05-11                                                                                                                                                           | Successor / owner                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track A `[UTL]` classifier + `[TEST]`                                                                                                                                                                                                                                                                                  | `done` (UTL@3fbc6b3)                                                                                                                                                              | —                                                                                                                                                                                                                                                                                         |
| Track B `[UAC]` ×3 + `[TEST]`-UAC                                                                                                                                                                                                                                                                                      | `done` (UAC@7c8b5ad)                                                                                                                                                              | —                                                                                                                                                                                                                                                                                         |
| Track B `[UTL]` `_classify_sports` + tests                                                                                                                                                                                                                                                                             | `done` (UTL@3fbc6b3)                                                                                                                                                              | —                                                                                                                                                                                                                                                                                         |
| Track C `[instruments-service]` + `[TEST]` + `[DOCS]`                                                                                                                                                                                                                                                                  | `done` (instruments-service@485c57b; dry-runs on 5 prod manifests; codex@bce1822e-area)                                                                                           | — (operator decides if/when to `--apply-flips` after CSV review — currently a no-op given 0 upgrades on current manifest data)                                                                                                                                                            |
| Track D — `[MTDS]` / `[MDPS]` / `[features-*]` AUDIT                                                                                                                                                                                                                                                                   | `done` 2026-05-11 — findings: `../archive/issues/wave3x_track_d_findings_2026_05_11.md`                                                                                           | — (audit complete; per-adapter A/B/C/D classification filed)                                                                                                                                                                                                                              |
| Track D — case-D _implementation_ (zero-activity-bar adapter wiring)                                                                                                                                                                                                                                                   | `deferred-post-cutover` — no schema change forced (anti-seq verdict: no new manifest dim)                                                                                         | DEFERRED post-cutover; needs a NEW UTL `zero_activity_bars` primitive + `instrument_catalog` threaded into adapter construction (Wave 2/3 of writegate Phase 3.D.5, "pending"); sports half re-scopes to instruments-service. Slot 1 / a Wave 3.M follow-up owns the impl plan.           |
| Track D — `[TEST]` per-adapter smoke tests                                                                                                                                                                                                                                                                             | `deferred-post-cutover`                                                                                                                                                           | Pairs with the case-D adapter wiring above.                                                                                                                                                                                                                                               |
| Track D — `[DOCS]` codex zero-activity-bar shape stub                                                                                                                                                                                                                                                                  | `done` (PM@84e29700 + PM@e1185105, 2026-05-13 slot 6 wave 2)                                                                                                                      | — (codex stub written; see `honest-absence-downstream-handling.md` § "Zero-activity-bar shape"; Wave 3.M follow-up todo added to plan body)                                                                                                                                               |
| Track D — `[PLAN]` Wave 3.M case-D implementation plan                                                                                                                                                                                                                                                                 | `deferred-after-cutover`                                                                                                                                                          | File `wave3x_track_d_implementation_<date>.md` post-2026-05-23. Owner: slot 1 or writegate Phase 3.D.5 Wave 2/3 owner.                                                                                                                                                                    |
| Track D — `EXPECTED_KNOWN_SOURCE_GAP` candidate new `EmptyConfirmedReason`                                                                                                                                                                                                                                             | `done` (UAC@174f401 2026-05-11)                                                                                                                                                   | — (enum added by Ikenna slot 6 in Phase 1 schema window; see findings doc § "Recommended decision" operator A1)                                                                                                                                                                           |
| Track D — P0 bugs surfaced (MTDS blank-reason sentinel-abort; MDPS dead canonical-writer path + 1440-NaN TradFi passthrough; commodity phantom-row; cross_instrument np.zeros; sports fillna-magic)                                                                                                                    | `mostly-done` — P0-1 SHIPPED (MTDS@3da026d); P0-2 steps 1-4+6 SHIPPED (Ikenna slot 8); P0-2 Step 5 (output_schemas nullability) deferred; QG AST gate (Step 6) done (PM@a4512ed3) | Residual: P0-2 Step 5 deferred-after `hard_schema_enforcement_2026_05_08`; commodity phantom-row + sports fillna + cross_instrument np.zeros → features-service owners (unscheduled).                                                                                                     |
| Track E `[UTL]` 3 stamping helpers + `[TEST]` + `[DOCS]`                                                                                                                                                                                                                                                               | `done` (UTL@2ab3685; codex@bce1822e)                                                                                                                                              | —                                                                                                                                                                                                                                                                                         |
| Track E `[features-sports]` calculator wire-in of the stamp helpers                                                                                                                                                                                                                                                    | `deferred` — per-service half                                                                                                                                                     | DEFERRED to Harsh slot 4 (MTDS sports adapter stamping wiring) + Ikenna slot 3 (available_at Phase 1 per-asset_group cascade) per the 2026-05-11 work-split. UTL helpers are ready to consume; see `plans/active/issues/` for slot 4's MTDS-slice sports `available_at` wiring issue doc. |
| Track A `[UTL]` adjacent: pre-existing `reportPrivateImportUsage` on `from unified_api_contracts import non_trading_day_reason` (legacy_reason_classifier.py:162)                                                                                                                                                      | `noted` — pre-existing, not introduced this session                                                                                                                               | Picked up by the workspace QG sweep (Ikenna) or the writegate owner; fix = deep import `from unified_api_contracts.registry.venue_trading_calendar import non_trading_day_reason` with a `# noqa: ... qg-deep-import` comment.                                                            |
| Adjacent finding: `instruments-service/scripts/reconcile_blank_error_reason_rows.py:76` does `from unified_trading_library import classify_blank_reason_row` — that symbol is NOT on the UTL facade → `ImportError` at runtime                                                                                         | `noted` — pre-existing bug on the writegate Wave 2.M sweep script                                                                                                                 | → writegate Phase 3.D.5 owner / QG sweep. 1-line fix: change to `from unified_trading_library.legacy_reason_classifier import classify_blank_reason_row` (the deep path the docstring already references). My new reconciler uses the correct deep import.                                |
| Adjacent finding (Track C dry-run): ~604,951 defi + ~1,868,285 sports `empty_confirmed/SOURCE_RETURNED_ZERO` rows that arguably should be `attempted_failed` per the cefi/defi/tradfi-can't-legit-empty-at-instrument-grain operator directive — the 2026-05-07 sweep only handled BLANK reasons so never flipped them | `noted` — gap                                                                                                                                                                     | → writegate Phase 3.D.5 / a follow-up. My reconciler deliberately doesn't do that status-flip (it's a reason-UPGRADE only).                                                                                                                                                               |

## DONE-2026-05-11 (slot 3 — wave3x Tracks A-UTL / B / C / D (audit) / E)

Slot 3 (`harsh-wave3x-tab`) ran Tracks A-UTL + B + C + D (read-only audit) + E end-to-end on real infrastructure
(per-tab worktree `tab/hk/3`, pushed directly to `live-defi-rollout`).

**Code commits:**

- `unified-api-contracts@7c8b5ad` — Track B sports per-source SSOTs: `UNDERSTAT_COVERED_LEAGUES` +
  `does_understat_cover` (provider_league_ids.py) + `is_within_transfer_window(country_code, day)`
  (transfer_windows.py) + `get_footystats_season_bounds` / `is_within_footystats_season` /
  `footystats_season_status_for_day` (season_dates.py) + sports-facade re-exports + 22 unit tests
  (`tests/unit/sports/test_per_source_coverage_ssots.py`). DRY deviation: re-used existing SSOTs (`UNDERSTAT_NAMES` /
  `_COUNTRY_DEFAULTS` / `get_season_boundary`) rather than creating duplicate dicts (per "No double SSOT").
- `unified-trading-library@3fbc6b3` — Tracks A+B UTL classifier extensions: `_classify_tradfi` (half-day →
  `EXPECTED_PARTIAL_HALF_DAY`, intraday-ts-outside-session → `EXPECTED_OUTSIDE_TRADING_HOURS`; consumes
  `registry.half_day_sessions` + `registry.venue_session_hours`) + `_classify_sports` (understat /
  transfermarkt-off-window / footystats-pre/post-season → matching `EXPECTED_*`; consumes UAC@7c8b5ad) +
  `_parse_iso_date`/`_parse_iso_datetime` helpers + 13 new tests + 5 drift-guard entries (33 pass).
- `unified-trading-library@2ab3685` — Track E availability_stamping sports helpers: `stamp_available_at_injuries` +
  `stamp_available_at_odds_snapshot` (named aliases over `_event_time`) + `stamp_available_at_post_match_cascade`
  (source-priority candidate cascade + `kickoff+120min` fallback) + 2 col-name constants + 3 facade re-exports + 18 new
  tests (37 pass).
- `instruments-service@485c57b` — Track C `scripts/reconcile_legacy_blank_to_typed_reason.py` (second-pass reason
  upgrader: `empty_confirmed` rows with a 2026-05-07-sweep default reason → re-classify via `classify_blank_reason_row`
  with Track A+B SSOTs → upgrade to more-specific `EXPECTED_*`; never downgrades / never flips capture_status; same
  shape as `reconcile_expected_absence_reasons.py`) + 6 unit/smoke tests.

**Plan-flip + codex + findings commits (PM):**

- `unified-trading-pm@56dec3f1` — Track D findings doc `plans/archive/issues/wave3x_track_d_findings_2026_05_11.md` (6
  read-only audit sub-agents, per-adapter A/B/C/D classification) + Track D plan annotations + escalation ping.
- `unified-trading-pm@e5d82a15` — Track B UAC plan flips (3 `[UAC]` + `[TEST]`-UAC checkboxes).
- `unified-trading-pm@c6607382` — Track A+B UTL plan flips (3 `[UTL]`/`[TEST]` checkboxes).
- `unified-trading-pm@bce1822e` — Track E plan flips (3 of 4 checkboxes) + codex `honest-absence-downstream-handling.md`
  `## Per-source available_at stamping helpers (UTL)` section.
- `unified-trading-pm@<this commit>` — Track C plan flips (3 checkboxes) + codex `honest-absence-downstream-handling.md`
  `### Reconciler chain for legacy error_reason (the three passes)` subsection + this DONE block + the deferred-work
  scoreboard above.

**Full-execution evidence:**

- UAC@7c8b5ad:
  `cd unified-api-contracts && .venv-workspace/bin/python -m pytest tests/unit/sports/test_per_source_coverage_ssots.py`
  → 22 passed; ruff + basedpyright clean.
- UTL@3fbc6b3: `pytest tests/unit/test_legacy_reason_classifier.py` → 33 passed; ruff clean; basedpyright clean modulo
  the pre-existing `non_trading_day_reason` `reportPrivateImportUsage`.
- UTL@2ab3685: `pytest tests/unit/test_availability_stamping.py` → 37 passed; ruff clean; basedpyright clean on
  `availability_stamping.py`.
- instruments-service@485c57b: `pytest tests/unit/test_reconcile_legacy_blank_to_typed_reason.py` → 6 passed; ruff
  clean; **dry-run on the 5 production canonical manifests** (tradfi 141,401 rows / 0 candidates; sports 2,675,696 /
  1,868,285 candidates / 0 upgrades; cefi 2,632,931 / 0 candidates; defi 1,606,190 / 604,951 candidates / 0 upgrades;
  prediction 16,812 / 41 candidates / 0 upgrades — reconciler RAN clean on all 5, no errors, no incorrect
  reclassifications; 0 upgrades because the existing sweep + orchestrator pre-skip already classified most rows and the
  new branches need finer per-row columns current rows mostly lack).
- All pushes verified `git rev-list --left-right --count HEAD...origin/live-defi-rollout` → `0 0`.

**Deferred (see the scoreboard above for the full table)**: Track D case-D _implementation_ + per-adapter smoke tests +
codex stub → post-cutover (no schema change forced); Track D `EXPECTED_KNOWN_SOURCE_GAP` candidate reason → Ikenna slot
5 decision; Track D P0 bugs → writegate Phase 2.A/2.E + Harsh slots 5+6; Track E features-sports calculator wire-in →
Harsh slot 4 + Ikenna slot 3.

## DONE-2026-05-10 (Tab H — wave3x Track A UAC half)

Track A's UAC half shipped end-to-end on real infrastructure (sibling-clone UAC@bdc84ed pushed to live-defi-rollout).
Code, tests, ruff, basedpyright all green; full-execution criterion met locally + visible on origin.

**Code commits:**

- `unified-api-contracts@bdc84ed` — `feat(uac): half_day_sessions + venue_session_hours SSOTs (wave3x Track A)` — 4
  files, 608 insertions. Modules + 33 unit tests. Foreign-dirty UAC files
  (`tests/internal/unit/test_instruments_live_event_taxonomy.py` /
  `tests/unit/test_archetype_capability_may_23_coverage.py` / `unified_api_contracts/__init__.py`) untouched per
  workspace foreign-WIP rule.

**Plan-flip commit:**

- `unified-trading-pm@72bf558e` —
  `docs(plans): wave3x Track A — UAC half_day_sessions + venue_session_hours SSOTs shipped` — Track A's 3 P0 UAC todos
  flipped to `[x]`. Pathspec-scoped (`git commit --only -- <path>`) to leave the ~50 foreign-dirty PM codex docs
  untouched.

**Full-execution verification (per "Plans Run To Actual Completion" HARD RULE):**

- `cd unified-api-contracts && .venv/bin/python -m pytest tests/unit/test_half_day_sessions.py tests/unit/test_venue_session_hours.py -v`
  → **33 passed in 3.75s**.
- `.venv/bin/python -m ruff check <new-files>` → **All checks passed!**
- `.venv/bin/python -m basedpyright <new-files>` → **0 errors, 0 warnings, 0 notes**.
- `.venv/bin/python -m ruff format <new-files>` → no reformats needed.
- `git rev-list --left-right --count HEAD...origin/live-defi-rollout` → **0 0** (UAC + PM both at parity with origin
  post-push).

**Deferred items still open in this plan (not Tab H scope):**

- Track A `[UTL]` classifier extension (`unified_trading_library/legacy_reason_classifier.py` to consume both new UAC
  SSOTs + emit `EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_OUTSIDE_TRADING_HOURS`) — `- [ ]` in plan body. Status:
  `helper-shipped` for UAC dependencies; UTL wire-in is the natural next step. Successor: any Tab/agent picking up Track
  A's UTL half. Not blocked — UAC SSOTs are now consumable.
- Track A `[TEST]` UTL classifier tests — paired with the UTL extension above.
- Tracks B / C / D / E — independent of Track A; not picked up this session.

**Out-of-scope this session:**

- Track B (sports per-source SSOTs) — explicitly skipped per spawn prompt to avoid asset-group authority collision.
- Phase 4.A items 1/2/3 of `writegate_honest_coverage_endtoend_2026_05_06.md` — already shipped (deployment-api@453836d
  / @7d57056 / @3b0477a, verified). Phase 4.A item 4 (live-vs-historical envelope alert) is `- [ ]` and explicitly
  multi-repo deferred (UAC + UTL + 3 services) — out of clean context for a single tab.

## DONE-2026-05-13 (slot 6 wave 2 — Track D DOCS codex stub)

Slot 6 wave 2 (`slot-6-w2`, `tab/hk/6`) shipped the only actionable remaining item: Track D `[DOCS]` codex stub. All
other 5 remaining `- [ ]` items confirmed deferred with named owners.

**Plan-flip + codex commits:**

- `unified-trading-pm@84e29700` — Track D `[DOCS]` checkbox flipped `- [ ]` → `- [x]`; codex
  `honest-absence-downstream-handling.md` § "Zero-activity-bar shape (case-D design — implementation deferred
  post-cutover)" added (per-data_type carry-forward table, vol-smile constraint, Wave 3.M implementation requirements,
  successor-plan pointer); Wave 3.M follow-up `[PLAN]` P2 todo added to Track D; boot ack in `pings/slot_6.md`.
- `unified-trading-pm@e1185105` — SHA placeholder corrected to `PM@84e29700`; deferred-work scoreboard updated (Track D
  DOCS row → done; EXPECTED_KNOWN_SOURCE_GAP row → done per UAC@174f401; P0 bugs row → mostly-done summary).

**Full-execution evidence:**

- Codex doc update is pure markdown; no code tests required. Push verified:
  `git rev-list --left-right --count HEAD...origin/live-defi-rollout` → `0 0` after both pushes.

**Deferred after 2026-05-13 wave 2 session:**

| Track / item                                                         | Status                        | Successor / owner                                                                  |
| -------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------- |
| Track D `[MTDS]` / `[MDPS]` / `[features-*]` case-D _implementation_ | `deferred-post-cutover`       | Wave 3.M plan `wave3x_track_d_implementation_<date>.md` (to file post-2026-05-23)  |
| Track D `[TEST]` per-adapter smoke tests                             | `deferred-post-cutover`       | Pairs with case-D adapter wiring                                                   |
| Track D `[PLAN]` Wave 3.M filing                                     | `deferred-after-cutover`      | Slot 1 or writegate Phase 3.D.5 Wave 2/3 owner                                     |
| Track E `[features-sports]` stamp-helper wire-in                     | `deferred` — per-service half | Harsh slot 4 (MTDS sports stamping) + Ikenna slot 3 (available_at Phase 1 cascade) |

Plan checkpoint count: 17/23 done (the new `[PLAN]` todo adds 1 to total; 1 more `[x]` flipped this session → 17 done of
23 total).
