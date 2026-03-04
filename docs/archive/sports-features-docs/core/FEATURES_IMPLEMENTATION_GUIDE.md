## Feature Implementation Guide (Math + Nuances)

### Purpose

This document defines the **implementation-level rules** that apply to feature computation, independent of any particular codebase. It is designed to remove ambiguity by standardizing:

- time cutoffs (anti-leakage)
- windowing and padding
- priors and shrinkage
- provider-specific nuances (odds snapshots, lineup availability)

**Authoritative catalogs:**

- Feature list + per-feature formulas live in `sports-betting-service/docs/FEATURES_CATALOG.md`.
- Stage 1 keys live in `sports-betting-service/docs/reference_data_spec.md`.
- Stage 2 raw tables live in `sports-betting-service/docs/raw_data_spec.md`.

### Global invariants (anti-leakage)

Define:

- `kickoff_utc`: canonical fixture kickoff time (UTC)
- `as_of_utc`: the timestamp at which we are computing features (UTC)

**Invariant A (no-lookahead):** every input event used to compute any feature for a fixture must satisfy:
\[
\max(\text{timestamp of inputs}) \le as_of_utc < kickoff_utc
\]

**Invariant B (partition vs event time):**

- Stage 2 `dt` partitions are **storage partitions**.
- Feature correctness is governed by **event timestamps** (`fetched_at_utc`, `timestamp_utc`, `announced_at_utc`, `kickoff_utc`).

### Feature horizons (time buckets)

We standardize discrete horizons, aligned to Odds API sampling:

- Pregame: `T-24h`, `T-12h`, `T-6h`, `T-90m`, `T-80m`, `T-70m`, `T-60m`, `T-50m`, `T-40m`, `T-30m`, `T-20m`, `T-10m`, `T-0`
- Halftime: `HT-2min`

`as_of_utc` for a horizon is defined by the **data timestamp** actually available at that horizon (not by an assumed schedule).

### Rolling windows (team-level)

#### Window definitions

Typical windows used throughout the spec:

- `last1`, `last3`, `last5`, `last10`
- `season` (season-to-date, but still `kickoff_utc < as_of_utc`)
- EWMAs by time half-life: `ewma_30d`, `ewma_90d`

#### Home/away splits (critical)

For a given fixture with home team `H` and away team `A`:

- `home_*` rolling stats are computed from matches where **team == H and venue_side == home**
- `away_*` rolling stats are computed from matches where **team == A and venue_side == away**

This applies to xG, goals, shots, possession, etc.

#### Cross-competition vs league-only

Rule of thumb:

- **Rolling last-N windows**: include all competitions (league + cups + continental), unless a feature explicitly says league-only.
- **Season-to-date baselines**: league-only when you need comparability to standings and league rates.

#### Padding rule (no fake data)

If fewer than `N` matches exist for a `lastN` feature:

- compute using only the available historical matches (do **not** pad with zeros or global means)
- expose uncertainty via `history_depth_*` and `insufficient_data_*` features

### EWMA (with previous-season prior)

EWMAs must not cold-start from the first match of the season.

Let \(x_t\) be the match-level metric (e.g., xG-for) in chronological order.
Let \(m_0\) be the previous season mean (or league mean if unavailable).

EWMA update:
\[
m*t = \alpha x_t + (1-\alpha) m*{t-1}
\]

Where \(\alpha\) is derived from a time-based half-life (e.g., 30 days) and the time delta between matches.

### Promoted teams / fresh-season handling

Promoted/new-to-league teams require priors and blending.

#### League-strength normalization

When translating previous-league metrics into current-league scale, apply a league-strength factor:
\[
attack_factor = \\frac{strength(source_league)}{strength(target_league)}
\]
\[
defense_factor = \\frac{strength(source_league)}{strength(target_league)}
\]

#### Decay-weighted blending

Blend priors with observed current-season values using:
\[
F = \\alpha \\cdot F*{prior} + (1-\\alpha) \\cdot F*{current}
\]
\[
\\alpha = e^{-games\\\_played/\\tau}
\]

Where typical \(\tau\) is 3–5 (tunable).

### Lineups: confirmed vs predicted vs priors

Lineups must be “as-of safe”:

- a confirmed lineup row is usable only if `announced_at_utc <= as_of_utc`
- otherwise the system must fall back to predicted XI or priors

**Backtesting rule:** if simulating a `T-24h` horizon historically, you must reconstruct what an expected XI would have been using only data before `as_of_utc` (e.g., last-N lineup frequency, injuries known at the time).

### Odds features: fair odds, vig, drift

Given decimal odds \(o_1, o_X, o_2\):
\[
p_i = 1/o_i
\]
\[
vig = (p_1 + p_X + p_2) - 1
\]
Vig-free probabilities:
\[
p_i^{fair} = p_i / (p_1 + p_X + p_2)
\]

### Odds microstructure (path-based features)

The microstructure features treat the odds path as a time series.

#### Velocity

\[
velocity = \\frac{\\Delta p}{\\Delta t}
\]
Computed between standardized snapshot windows (e.g., `T-24h` to `T-6h`, `T-30m` to `T-10m`).

#### Acceleration

\[
accel = velocity*{late} - velocity*{early}
\]

#### Volatility / smoothness

Use the standard deviation of probability deltas, plus “max single move” and “path smoothness” heuristics.

### HT sequencing features (first-half dynamics)

HT models cannot rely solely on aggregates. Sequencing features require minute-by-minute data:

- API-Football events (goals/cards/substitutions) filtered to minute \(\le 45\)
- Soccerfootball progressive series
- Understat shots (for xG by minute) where available

Core constructs:

- early vs late xG (0–15, 15–30, 30–45)
- momentum scores (time-decayed event weights)
- game-state response (xG created while behind vs minutes behind)

### Schema artifacts (non-feature tables)

This section defines **execution-layer storage** that is not “a feature,” but is required to build features consistently and to backtest without leakage.

All table definitions should map to `sports-betting-service/docs/models.py`.

#### 1) Explicit feature vector tables (columnar)

Because the feature universe is large and strictly enumerated, feature storage is split into explicit, grouped tables:

- `feature_vector_market_explicit`
- `feature_vector_team_explicit`
- `feature_vector_league_explicit`
- `feature_vector_h2h_explicit`
- `feature_vector_player_explicit`
- `feature_vector_lineup_explicit`
- `feature_vector_referee_explicit`
- `feature_vector_weather_explicit`
- `feature_vector_ht_explicit`
- `feature_vector_context_explicit`

**Keys (all feature vector tables):**

- `(fixture_id, feature_horizon, timestamp_utc)` uniquely identify a computed feature row set.

#### 2) Player snapshots (as-of player state)

**Goal:** freeze the state of each player as-of a timestamp so features can be computed deterministically and backtests can reconstruct “what was known.”

Minimum contract (per player, per as-of):

- `player_id`
- `team_id` (club at time)
- `as_of_utc`
- rolling form aggregates (minutes, xg/xa proxies where available)
- availability flags (injury/suspension/return timeline where available)
- market value / value date (Transfermarkt)

#### 3) XI expectation tables (probabilistic lineup)

**Goal:** represent expected lineup as a distribution so feature aggregation is mathematically correct.

For each fixture, team, player, and horizon:

- `fixture_id`, `team_id`, `player_id`
- `feature_horizon`, `as_of_utc`
- `p_start` (probability of starting)
- optional: `p_90` (probability of playing 90), `p_sub_on`
- `source` (confirmed, predicted, fallback)

Backtesting requirement: probabilities must be computed using only information with timestamps `<= as_of_utc`.

#### 4) HT state tables (as-of halftime state)

**Goal:** create a single, canonical halftime state record used by HT feature pipelines and delta models.

Even if raw HT fields exist in multiple sources, HT modeling benefits from a unified record keyed by:

- `fixture_id`
- `timestamp_utc` (HT-2min snapshot time)

State should include:

- HT score
- first-half xG (best available source + fallback)
- cards, shots, dangerous attacks, possession summaries

### Implementation sequencing (feature dependency + compute order)

This section defines which computations must exist before others and what should be cached.

#### Compute layers

- **Layer A (curated inputs)**: stage-2 provider tables mapped onto canonical fixture/team/player keys.
- **Layer B (base transforms)**: implied probabilities, vig removal, per-match normalized stats, lineup availability.
- **Layer C (rolling aggregates)**: lastN/season/EWMA features, priors, promotion blending.
- **Layer D (path features)**: odds velocity/acceleration/steam, disagreement across books, learnability scores.
- **Layer E (HT sequencing)**: first-half trajectories, momentum, game-state response.

#### Minimum dependency order (practical)

1. Canonical fixture keys + kickoff_utc (`reference_data_spec.md`)
2. Odds snapshots + bookmaker classification (`raw_data_spec.md`, `BookmakerMeta`)
3. Convert odds → implied probs → vig-free probs (market base)
4. Team/league baselines (standings snapshots, league rates)
5. Rolling team windows + priors (early season + promoted handling)
6. Player aggregation + XI expectation (confirmed→predicted→priors)
7. Microstructure/path features (velocity/accel/steam/disagreement)
8. HT state + sequencing (only for `HT-2min`)

#### Caching strategy

Cache at the granularity that avoids recomputation while preserving correctness:

- **Cache key**: `(fixture_id, feature_horizon, timestamp_utc, feature_group, source_version)`
- Cache layers B/C/D separately so that changes in odds snapshots don’t force recomputation of long-horizon rolling team stats.
- Treat Stage 2 raw tables as immutable by `dt`; corrected data should be written as a new `dt` cut and reprocessed.
