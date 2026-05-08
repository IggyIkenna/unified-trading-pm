---
title:
  "Instruments lifecycle (futures expiry / options expiry hard-required) + fixtures end_time cascade + half-time /
  extra-time / penalty timing as captured fields and ML features"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/canonical/domain/market/tradfi.py (no CanonicalFuturesContract)
  - unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/__init__.py:77-96
    (CanonicalOptionsChainEntry — expiration nullable)
  - unified-api-contracts/unified_api_contracts/canonical/domain/predictions/lifecycle.py:43-79 (MarketLifecycle — fully
    required, the gold standard)
  - unified-api-contracts/unified_api_contracts/canonical/domain/sports/__init__.py:466-515 (CanonicalFixture — halftime
    scores only, no timestamps)
  - unified-trading-library/unified_trading_library/availability_stamping.py:161-206 (stamp_available_at_post_match —
    hardcoded kickoff+120min fallback, NO source cascade)
  - CLAUDE.md "fixture_stats / fixture_player_stats → match_end_time (detected via cascade:
      api_football native → SFI progressive freeze → footystats / understat → low-confidence kickoff + 120min fallback)"
  - CLAUDE.md "Prediction market lifecycle timing"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Instruments lifecycle + fixtures end_time cascade + half-time / penalty timing

> **Severity**: P0 for Q1+Q2 (futures/options without expiry break roll detection + odds settlement); P1 for Q4-Q6
> (sports end_time cascade + half-time / penalty timing — affects 5% of cup matches' settlement correctness + blocks
> half-time prediction ML). **Blast radius**: UAC (tradfi + derivatives + sports schemas) + instruments-service write
> path (hard schema enforcement) + MTDS (roll detection + lifecycle gating) + UTL (`stamp_available_at_post_match`
> cascade) + features-sports-service (half-time / extra-time / penalty features). **Suggested owner**: split — Q1+Q2 →
> `tradfi_master_2026_05_07.md` Phase X; Q4-Q6 → `sports_master_2026_05_07.md` Phase 3 sub-plan.

## What I found

Eight-question audit; the prediction-markets pattern (Q3 — fully required `market_created_at` + `resolution_time` +
`settlement_time` per
[lifecycle.py:43-79](../../../unified-api-contracts/unified_api_contracts/canonical/domain/predictions/lifecycle.py#L43-L79))
is the gold standard, and every other lifecycle is missing one or more of its components.

### Q1 — Futures expiry/settlement/delivery: COMPLETE GAP

[unified-api-contracts/unified_api_contracts/canonical/domain/market/tradfi.py](../../../unified-api-contracts/unified_api_contracts/canonical/domain/market/tradfi.py)
— only has `CanonicalYieldCurvePoint`, `CanonicalBondData`, `CanonicalCdsSpread`. **No `CanonicalFuturesContract` schema
exists.** Hard-required fields are missing entirely:

- `expiry_date`
- `last_trading_date`
- `first_notice_date`
- `delivery_date`
- `settlement_date`

This blocks roll detection (continuous front-month) at MTDS, expiry-aware position-balance-monitor checks, and
lifecycle-bounded backfill (no MTDS ticks fetched after `last_trading_date` for the rolled-off contract).

### Q2 — Options expiry: PARTIAL — nullable when it should be required

[derivatives/**init**.py:77-96](../../../unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/__init__.py#L77-L96)
`CanonicalOptionsChainEntry`:

```python
strike: Decimal              # required
option_type: str             # required ("call" or "put")
expiration: AwareDatetime | None = None   # NULLABLE — should be hard-required
```

Hard rule per CLAUDE.md "options/futures bundled by root" + cluster validation: every options contract MUST have an
expiry. Nullable creates: ambiguity between weekly/monthly options at schema level, undetectable
expired-but-still-quoted contracts, and breaks the per-`(root, expiry, strike, right)` bundling key for cluster
validation.

### Q3 — Prediction-market lifecycle: PRESENT (gold standard)

[predictions/lifecycle.py:43-79](../../../unified-api-contracts/unified_api_contracts/canonical/domain/predictions/lifecycle.py#L43-L79)
`MarketLifecycle`:

```python
@dataclass(frozen=True)
class MarketLifecycle:
    market_created_at: datetime    # required
    resolution_time: datetime       # required
    settlement_time: datetime       # required
```

CLAUDE.md "Prediction market lifecycle timing" mandates all three; instruments-service + MTDS enforce bounds (no ticks
before `market_created_at`, none after `settlement_time`). **This is the model the other asset_groups should follow.**

### Q4 — Sports match_end_time cascade: PARTIAL — fallback exists, cascade NOT wired

[availability_stamping.py:161-206](../../../unified-trading-library/unified_trading_library/availability_stamping.py#L161-L206)
`stamp_available_at_post_match`:

```python
def stamp_available_at_post_match(df, match_end_col="match_end_time", kickoff_col="kickoff_utc",
                                   default_match_duration=DEFAULT_MATCH_DURATION):
    # If match_end_col present + non-null per row: use it
    # Else: fall back to kickoff + 120min
```

Hardcoded `kickoff + 120min` fallback. **No multi-source cascade per CLAUDE.md spec** (api_football native → SFI
progressive freeze → footystats / understat). When SFI progressive detects actual 95-min match (no extra time, minimal
stoppage), the feature `available_at` is 25min late — features computed at `kickoff + 100min` exclude valid match data.

Conversely, when a match goes to extra time + penalties (~140min total), the 120min fallback creates lookahead —
features stamped as available at `kickoff + 120min` actually contain data from minutes 121-140.

### Q5 — Half-time + extra-time + penalty-shootout timestamps: COMPLETE GAP

[sports/**init**.py:466-515](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/__init__.py#L466-L515)
`CanonicalFixture` has score-side halftime: `home_goals_halftime` / `away_goals_halftime` (nullable). **Zero captured
timestamps for**:

- `halftime_start_time` / `halftime_end_time`
- `extra_time_first_half_start_time` / `extra_time_first_half_end_time` / `extra_time_second_half_start_time` /
  `extra_time_second_half_end_time`
- `penalty_shootout_start_time` / `penalty_shootout_end_time`
- `whistle_full_time_at` (referee's full-time whistle, distinct from match administrative end-time)

These are inputs to:

- **Half-time prediction ML**: predict 2nd-half goals from 1st-half stats. Need precise HT-end timestamp for feature
  `available_at` clip.
- **Live trading**: liquidity at half-time is fundamentally different (no live ball-in-play action). `available_at` of
  HT-period odds depends on knowing when HT actually ended.
- **Odds settlement**: half-time markets settle at HT, full-time markets at FT (90min), AET markets at end of extra
  time, penalty markets at end of shootout. Without timestamps, settlement attribution is wrong for any market other
  than full-time.

### Q6 — Penalty shootout outcome: COMPLETE GAP — score collapse

`CanonicalFixture.home_goals` / `away_goals` is single-valued. **No distinction between**:

- `home_score_regulation` (final score at 90min + stoppage)
- `home_score_after_extra_time` (final score at 120min + stoppage if went to ET)
- `home_score_after_penalty_shootout` (final after pens)
- `home_penalty_shootout_score` / `away_penalty_shootout_score` (the shootout itself, e.g. 5-4)
- `home_winner` / `away_winner` (boolean — won including pens; penalties resolve a tied 120-min score)

Different betting markets settle on different scores. Match-result-90min vs match-result-after-pens vs
match-winner-after-extra-time vs first-to-score-in-pens are distinct markets. Single-`home_goals` collapse breaks
settlement for any market other than result-after-pens.

Per [shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md] and audit, ~5% of cup matches go to extra time + ~3% go
to pens (varies by competition). Feature compute on those matches is silently wrong.

### Q7 — End_time first-known-point in pipeline: GAP — circular dependency risk

`match_end_time` is only available POST-match (correct per CLAUDE.md "NEVER available pre-kickoff"). But the detection
itself can require features-side processing (SFI progressive freeze detection, understat xG terminal-row detection). If
features-sports-service is the FIRST place we know `match_end_time`:

- Anything downstream of features that requires `match_end_time` for its own `available_at` stamp depends on
  features-sports-service running first.
- features-sports-service's own outputs (`xg_at_full_time`, `goals_at_match_end`, etc.) need `match_end_time` to stamp
  their `available_at`.
- Circular dependency unless we bake the detection cascade INTO `stamp_available_at_post_match` upstream (UTL, before
  features-sports-service).

The right shape: detection cascade lives in UTL `stamp_available_at_post_match` and is called at instruments-service +
MTDS write boundary, OR a dedicated pre-features stage `match_lifecycle_extractor` runs first and writes a canonical
`match_lifecycle.parquet` per fixture with all timestamps + outcome fields, then everything downstream reads from there.

### Q8 — Plan coverage: MINIMAL

- `sports_data_completeness_2026_04_14.md` — halftime calculator wired (scores only); does NOT cover match_end_time
  cascade, penalty shootout, regulation-score-vs-AET distinction.
- `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` — names the cascade in plain English, does NOT implement.
- `predictions_canonical_question_group_polymarket_migration_2026_05_06.md` — lifecycle wired (Q3),
  prediction-only.
- **No active plan** owns: futures schema addition (Q1), options expiry hard-required (Q2), sports half-time /
  extra-time / penalty timestamps (Q5), regulation-vs-AET-vs-pens score distinction (Q6), end_time cascade
  implementation (Q4 + Q7).

## Why it matters

- **Roll detection broken (Q1)**: continuous front-month futures (ES, NQ, etc.) need expiry-aware roll. Without
  `last_trading_date` in schema, MTDS can fetch ticks for an expired contract; features compute on stale post-expiry
  prints.
- **Options-chain partial-bundle invisible (Q2)**: cluster validation per CLAUDE.md "Cluster validation MANDATORY" rule
  needs `(root, expiry, strike, right)` as the cluster key. Nullable expiry breaks the key.
- **Sports settlement wrong for cup matches (Q5+Q6)**: cup matches go to ET (~5%) and pens (~3%); settlement of "match
  result" markets is wrong for both groups without regulation/AET/pens distinction.
- **Half-time prediction ML blocked (Q5)**: can't compute 2nd-half features with correct `available_at` clip without
  `halftime_end_time`.
- **`Live = batch` violation throughout (Q4)**: live mode would naturally know `match_end_time` from real-time
  fixture-status feed; batch's hardcoded 120min fallback diverges.
- **Lookahead bias compounding with FIXTURES issue**: combined with
  `fixtures_lookahead_bias_post_match_scores_2026_05_08.md` finding, sports features get hit twice — wrong
  `available_at` AND wrong end-time stamping.

## Recommended decision

Five workstreams, prioritised:

### Phase 1 (P0) — Futures + options hard schema enforcement [Q1 + Q2]

- New UAC schema: `CanonicalFuturesContract` with REQUIRED `expiry_date`, `last_trading_date`, `first_notice_date`,
  `delivery_date`, `settlement_date`, `contract_size`, `tick_size`, `currency`, `underlying_id`.
- Update `CanonicalOptionsChainEntry`: change `expiration: AwareDatetime | None` → `expiration: AwareDatetime`
  (required). Schema validation rejects rows without expiry.
- instruments-service write path adds schema validation gate at `record_captured` — row failing schema-required check →
  `record_failed(reason=SCHEMA_VALIDATION_FAILED, missing_fields=...)`.
- One-time migration: read existing futures/options parquets, attempt to extract expiry from venue-specific tags
  (Databento `expiration_date`, etc.); rows without recoverable expiry get marked as `attempted_failed` for re-fetch.

### Phase 2 (P0) — Sports lifecycle schema expansion [Q5 + Q6]

- Extend `CanonicalFixture` (or new `CanonicalFixtureLifecycle`) with:
  - `halftime_start_time, halftime_end_time` (nullable — only known post-match)
  - `extra_time_first_half_start_time, extra_time_first_half_end_time, extra_time_second_half_start_time, extra_time_second_half_end_time`
    (nullable)
  - `penalty_shootout_start_time, penalty_shootout_end_time` (nullable)
  - `whistle_full_time_at` (nullable; ref's whistle, distinct from match admin end)
- Score-distinction columns:
  - `home_score_regulation` (90min + stoppage)
  - `home_score_after_extra_time` (120min + stoppage)
  - `home_score_after_penalty_shootout`
  - `home_penalty_shootout_score`, `away_penalty_shootout_score` (e.g. 5-4)
  - Boolean `went_to_extra_time`, `went_to_penalties`
- Migration: re-fetch + re-flatten api_football + footystats / SFI to populate where source-side data exists.
- Bonus: `MatchLifecyclePhase` enum aligned to `MarketSession` precedent — `FIRST_HALF`, `HALFTIME`, `SECOND_HALF`,
  `EXTRA_TIME_FIRST_HALF`, `EXTRA_TIME_HALFTIME`, `EXTRA_TIME_SECOND_HALF`, `PENALTY_SHOOTOUT`, `FULL_TIME`. Use as
  session-axis equivalent for live sports trading.

### Phase 3 (P1) — match_end_time detection cascade in UTL [Q4 + Q7]

- Implement the cascade in `stamp_available_at_post_match`:
  - Layer 1: api_football `status_long="Match Finished"` + last fixture-event timestamp.
  - Layer 2: SFI progressive stats freeze detection (last non-zero delta).
  - Layer 3: footystats / understat xG terminal-row.
  - Layer 4: hardcoded `kickoff + 120min` fallback (low-confidence; flag in event metadata).
- Each layer's confidence + provenance written to a `match_end_time_source` column on the lifecycle parquet.
- Cascade is called UPSTREAM of features-sports-service (in instruments-service or a new pre-features
  `match_lifecycle_extractor` stage), so features can consume canonical `match_end_time` without the circular dependency
  Q7 describes.

### Phase 4 (P1) — Pre-features `match_lifecycle_extractor` stage

New stage in the DAG: instruments-service → MTDS → MDPS → **match_lifecycle_extractor** → features-sports-service →
strategy-service. Reads raw fixture events / SFI progressive / xG, applies the Phase 3 cascade, writes canonical
`match_lifecycle.parquet` per fixture. Features-sports-service then reads this as the SSOT for any timing-derived
feature.

### Phase 5 (P1) — Half-time + extra-time + penalty timing as features

Once Phase 2 + 3 + 4 land:

- features-sports-service exposes `time_in_extra_time`, `went_to_penalties`, `halftime_duration_observed`,
  `stoppage_time_first_half`, etc. as ML features.
- Half-time prediction ML models clip features at `halftime_end_time` (Phase 5 unblocks).
- Odds-settlement features distinguish settlement at FT vs AET vs pens correctly.

## Acceptance criteria

- [ ] `CanonicalFuturesContract` shipped with required expiry/settlement/delivery dates.
- [ ] `CanonicalOptionsChainEntry.expiration` migrated to required (non-nullable).
- [ ] Sports lifecycle schema extended with HT/ET/pens timestamps + regulation/AET/pens score columns.
- [ ] UTL `stamp_available_at_post_match` implements 4-layer cascade with `match_end_time_source` provenance.
- [ ] Pre-features `match_lifecycle_extractor` stage shipped; features-sports-service reads from canonical
      lifecycle.parquet.
- [ ] Smoke test: cup match that went to penalties (e.g. 2022 World Cup Final) — verify schema captures regulation 3-3,
      AET 3-3, pens 4-2, winner=ARG.
- [ ] Hard schema validation gate at instruments-service `record_captured` — futures/options without required lifecycle
      fields → `record_failed(SCHEMA_VALIDATION_FAILED)`.
- [ ] Half-time prediction ML feature wired with correct `available_at = halftime_end_time`.
- [ ] LookaheadBiasError fires correctly when feature compute attempts to consume penalty-shootout-score row at T <
      penalty_shootout_end_time.

## Open questions

- For futures: which Databento metadata field carries `last_trading_date` vs `first_notice_date` vs `delivery_date`? May
  need vendor-side mapping in UAC `external/databento/normalize.py`.
- For options-chain hard-required expiry: backfill scope — how many existing rows are missing expiry? Migration cost vs
  `record_failed` + re-fetch cost.
- Sports HT/ET/pens timestamp source: does api_football's `/fixtures/events` reliably emit period-transition events?
  Need empirical audit on 50+ recent extra-time matches.
- Cascade Layer-2 (SFI progressive freeze): what's the empirical false-positive rate (e.g. natural lull mid-match looks
  like freeze)? Need detection threshold tuning.
- Pre-features stage: implement as a separate service or as a UTL helper that runs at MDPS / features boundary? Operator
  architectural decision; default = separate service for DAG clarity.
- Coordination with `databento_tradfi_session_type_awareness_2026_05_08.md`: the `MatchLifecyclePhase` enum is to sports
  what `MarketSession` is to TradFi — both are session-axis labels for inputs. Same architectural shape, separate
  domains.
- Coordination with `fixtures_lookahead_bias_post_match_scores_2026_05_08.md`: that issue's FIXTURES_OUTCOMES split MUST
  adopt the regulation/AET/pens distinction from this issue's Phase 2 — fold into Phase 1 of that issue's planning.
