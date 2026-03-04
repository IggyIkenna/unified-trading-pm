# Feature Engineering - Sports Betting Service

**Purpose:** Complete feature inventory (~738 features) for ML models.

**Related Documents:**

- `ML_MODELS.md` - Which models use these features
- `reference_data_spec.md` - Stage 1 canonical keys + provider ID mappings (join layer)
- `raw_data_spec.md` - Stage 2 raw download tables + provider field appendix
- `HARSH_IMPLEMENTATION_GUIDE.md` - How to build features
- `LEAGUE_CLASSIFICATION.md` - League types and data requirements (see §2.7 for promoted teams)
- `PLAYER_PROFILES.md` - Player attributes and lineup aggregation (see §3.5, §6 for details)
- `models.py` - Database schemas

**Version:** 2.1
**Last Updated:** December 2024

---

## Table of Contents

1. [Feature Summary](#1-feature-summary)
2. [Rolling Window Strategy](#2-rolling-window-strategy)
   - [2.7 Promoted Teams & Fresh Season Handling (CRITICAL)](#27-promoted-teams--fresh-season-handling-critical)
3. [Pre-Game Features (~160)](#3-pre-game-features-160)
4. [HT-Specific Features (~55)](#4-ht-specific-features-55)
5. [Derived Features (~35)](#5-derived-features-35)
6. [Player-Level Feature Attribution](#6-player-level-feature-attribution)
7. [Feature Encoding](#7-feature-encoding)
8. [Feature Computation](#8-feature-computation)
9. [Timestamp Discipline](#9-timestamp-discipline)

---

## 1. Feature Summary

| Category                                 | Pre-Game | HT-Only | Total    |
| ---------------------------------------- | -------- | ------- | -------- |
| Market Features                          | 55       | 10      | 65       |
| Team Performance (Rolling)               | 60       | 25      | 85       |
| H2H Historical                           | 20       | 0       | 20       |
| Lineup/Player Features (incl. defensive) | 37       | 0       | 37       |
| Season State Features                    | 8        | 0       | 8        |
| **Promoted Teams & Fresh Season**        | **57**   | **0**   | **57**   |
| Context Features                         | 25       | 5       | 30       |
| Poisson/Statistical                      | 15       | 15      | 30       |
| **Total**                                | **~282** | **~55** | **~337** |

---

## 2. Rolling Window Strategy

### 2.1 Window Definitions

We compute team stats over MULTIPLE rolling windows to capture different signals:

| Window       | Games     | Description        | Signal            |
| ------------ | --------- | ------------------ | ----------------- |
| **Last 1**   | 1         | Previous game only | Immediate recency |
| **Last 3**   | 3         | Short-term form    | Hot/cold streak   |
| **Last 5**   | 5         | Medium-term form   | Consistent trend  |
| **Last 10**  | 10        | Long-term form     | Baseline quality  |
| **Season**   | All       | Season-to-date     | True team level   |
| **EWMA 30d** | ~6 games  | Half-life 30 days  | Weighted recency  |
| **EWMA 90d** | ~18 games | Half-life 90 days  | Stable baseline   |

### 2.2 Home/Away Splits

**Critical:** For the HOME team, compute form using **HOME GAMES ONLY**.
For the AWAY team, compute form using **AWAY GAMES ONLY**.

```python
# Example: Computing home team xG
home_xg_season_home_only = (
    home_team_matches.filter((team == home_team) & (venue == "home"))
    .filter(kickoff < prediction_time)
    .mean("xg")
)

# Example: Computing away team xG
away_xg_season_away_only = (
    away_team_matches.filter((team == away_team) & (venue == "away"))
    .filter(kickoff < prediction_time)
    .mean("xg")
)
```

### 2.3 Stats to Roll (Beyond Just Results)

For EACH rolling window, compute these stats:

| Stat              | Description            | Source                   |
| ----------------- | ---------------------- | ------------------------ |
| Goals scored      | Actual goals           | API-Football             |
| Goals conceded    | Goals against          | API-Football             |
| xG                | Expected goals         | Soccerfootball/Understat |
| xGA               | Expected goals against | Soccerfootball/Understat |
| Shots             | Total shots            | API-Football             |
| Shots on target   | SOT                    | API-Football             |
| Possession        | Ball possession %      | Soccerfootball           |
| Corners           | Corners won            | API-Football             |
| Fouls committed   | Team fouls             | API-Football             |
| Yellow cards      | Team yellows           | API-Football             |
| Dangerous attacks | Dangerous attacks      | FootyStats               |
| PPDA              | Pressing intensity     | Understat/FootyStats     |
| PPG               | Points per game        | Derived                  |

### 2.4 Cross-Competition Data (League + Cup + International)

**Critical Decision:** Rolling features should include ALL competitions, not just league games.

**Why?**

- Cup games affect fatigue, form, and momentum
- A team winning in Champions League carries confidence
- Squad rotation for cup games affects league lineup
- Missing cup data = incomplete picture of team state

**Implementation:**

```python
def get_team_matches_all_competitions(team_id: int, before: datetime) -> pd.DataFrame:
    """
    Get ALL team matches across competitions.

    Includes: League, domestic cups, international club (CL/EL/ECL), super cups
    """
    return fixtures_df[
        (
            (fixtures_df["home_team_id"] == team_id)
            | (fixtures_df["away_team_id"] == team_id)
        )
        & (fixtures_df["kickoff_utc"] < before)
    ].sort_values("kickoff_utc", ascending=False)


def get_team_matches_league_only(
    team_id: int, before: datetime, league_id: int
) -> pd.DataFrame:
    """
    Get team matches in specific league only.

    Use for: Season-to-date stats, league position context
    """
    return fixtures_df[
        (
            (fixtures_df["home_team_id"] == team_id)
            | (fixtures_df["away_team_id"] == team_id)
        )
        & (fixtures_df["league_id"] == league_id)
        & (fixtures_df["kickoff_utc"] < before)
    ].sort_values("kickoff_utc", ascending=False)
```

**Feature Variants:**

| Feature            | All Competitions | League Only    |
| ------------------ | ---------------- | -------------- |
| `home_xg_last5`    | ✅ Use all       | -              |
| `home_xg_season`   | -                | ✅ League only |
| `home_ppg_last5`   | ✅ Use all       | -              |
| `home_ppg_season`  | -                | ✅ League only |
| `home_goals_last3` | ✅ Use all       | -              |

**Rule of Thumb:**

- **Last N (rolling):** Include all competitions (captures current form)
- **Season stats:** League only (comparable baseline)
- **EWMA:** Include all competitions (form decay)

---

### 2.5 Season Crossover & Early Season Features

**Problem:** At the start of a new season:

- "Season" aggregates have only 1-2 games (high variance)
- Teams may have new managers, new players
- Last season's data is stale but still informative

**Solution:** Add explicit season state features + use previous season as EWMA prior.

#### Season State Features (NEW - 8 features)

| Feature                    | Type  | Description                          |
| -------------------------- | ----- | ------------------------------------ |
| `games_played_season`      | int   | Games played this season (home team) |
| `games_played_season_away` | int   | Games played this season (away team) |
| `days_since_season_start`  | int   | Days since first league game         |
| `is_early_season`          | int   | 1 if < 5 league games played         |
| `is_first_3_games`         | int   | 1 if < 3 league games                |
| `season_progress_pct`      | float | % of season completed (0-1)          |
| `new_manager_flag_home`    | int   | 1 if manager changed in last 90 days |
| `new_manager_flag_away`    | int   | 1 if manager changed in last 90 days |

```python
def compute_season_state_features(fixture_id: int, prediction_time: datetime) -> dict:
    """Compute season state / crossover features."""
    home_team, away_team = get_teams(fixture_id)
    league_id = get_league(fixture_id)

    # Get season boundaries
    season_start = get_season_start_date(league_id)
    season_end = get_season_end_date(league_id)
    total_season_days = (season_end - season_start).days

    # Games played this season
    home_season_matches = get_team_matches_league_only(
        home_team, prediction_time, league_id
    )
    away_season_matches = get_team_matches_league_only(
        away_team, prediction_time, league_id
    )

    features = {}
    features["games_played_season_home"] = len(home_season_matches)
    features["games_played_season_away"] = len(away_season_matches)
    features["days_since_season_start"] = (prediction_time - season_start).days
    features["is_early_season"] = 1 if len(home_season_matches) < 5 else 0
    features["is_first_3_games"] = 1 if len(home_season_matches) < 3 else 0
    features["season_progress_pct"] = min(
        1.0, (prediction_time - season_start).days / total_season_days
    )

    # Manager changes
    features["new_manager_flag_home"] = check_manager_change(
        home_team, prediction_time, days=90
    )
    features["new_manager_flag_away"] = check_manager_change(
        away_team, prediction_time, days=90
    )

    return features
```

---

### 2.6 EWMA Rolling with Previous Season Prior

**Problem you identified:** If EWMA starts from scratch, the first value dominates.

**Solution:** Use PREVIOUS SEASON AVERAGE as the starting point (prior), then roll EWMA forward.

```python
def compute_ewma_with_prior(
    team_id: int, stat: str, prediction_time: datetime, halflife_days: int = 30
) -> float:
    """
    Compute EWMA with previous season as prior.

    This prevents the first match of the season from having outsized influence.
    """
    # Get current season matches
    current_season = get_current_season(prediction_time)
    current_matches = get_team_matches_all_competitions(team_id, prediction_time)
    current_matches = current_matches[current_matches["season"] == current_season]

    # Get previous season average as PRIOR
    prev_season = current_season - 1
    prev_matches = get_team_matches_all_competitions(
        team_id, get_season_end(prev_season)
    )
    prev_matches = prev_matches[prev_matches["season"] == prev_season]

    if len(prev_matches) > 0:
        prior_value = prev_matches[stat].mean()
    else:
        # Fall back to league average if no prev season data
        prior_value = get_league_average(stat, current_season)

    if len(current_matches) == 0:
        # Season hasn't started - return prior
        return prior_value

    # EWMA calculation with prior as starting point
    alpha = 1 - np.exp(-np.log(2) / halflife_days)

    # Sort matches oldest to newest
    current_matches = current_matches.sort_values("kickoff_utc", ascending=True)

    # Start with prior
    ewma_value = prior_value

    # Roll forward through matches
    for _, match in current_matches.iterrows():
        days_since_prev = (
            (match["kickoff_utc"] - prev_date).days if prev_date else halflife_days
        )
        decay = np.exp(-alpha * days_since_prev)
        ewma_value = decay * ewma_value + (1 - decay) * match[stat]
        prev_date = match["kickoff_utc"]

    return ewma_value
```

**Why This Works:**

- Early season: EWMA is close to prev season average (stable)
- Mid season: New results dominate, prev season fades
- Cross-season: Smooth transition, no discontinuity

---

### 2.7 Promoted Teams & Fresh Season Handling (CRITICAL) 🔥

**Problem:** This is one of the hardest parts of football modeling. Promoted teams, newly constructed squads, and fresh-season teams have:

- **Zero history** in the current league
- **No reliable rolling statistics** for first 6-8 weeks
- **Player turnover** >40% in some cases
- **Lineup uncertainty** before lineups are announced

**If not handled correctly:** Features leak, models miscalibrate, EV collapses for first 6-8 weeks.

**Solution:** Three-layer approach used by professional syndicates (SmartOdds, Starlizard, DeckPrism):

---

#### 2.7.1 Layer 1: Team Prior Embeddings (Team Identity Projection)

**Key Principle:** NEVER start teams at "random." Propagate statistical identity from:

- Previous league performance (if promoted)
- Player quality aggregates
- Manager style embeddings
- Underlying xG in previous division
- Squad retention rate
- Transfer market valuation
- Preseason games (if available)
- Club-level long-term performance baseline

**Team Prior Embedding Formula:**

```python
def compute_team_prior_embedding(
    team_id: int, current_league_id: int, prediction_time: datetime
) -> dict:
    """
    Build team prior vector for promoted/new teams.

    Returns prior features that can be blended with actual data.
    """
    features = {}

    # Check if team is promoted/new to league
    is_promoted = check_if_promoted(team_id, current_league_id, prediction_time)
    previous_league_id = get_previous_league(team_id, current_league_id)

    if is_promoted and previous_league_id:
        # Get previous league stats
        prev_league_stats = get_team_stats_league(
            team_id, previous_league_id, get_season_end(prediction_time.year - 1)
        )

        # League strength normalization (see 2.7.2)
        league_factor_attack = get_league_strength_factor(
            previous_league_id, current_league_id, "attack"
        )
        league_factor_defense = get_league_strength_factor(
            previous_league_id, current_league_id, "defense"
        )

        # Normalized prior features
        features["prior_xg_attack"] = (
            prev_league_stats["xg_for"].mean() * league_factor_attack
        )
        features["prior_xg_defense"] = (
            prev_league_stats["xg_against"].mean() * league_factor_defense
        )
        features["prior_goals_for"] = (
            prev_league_stats["goals_for"].mean() * league_factor_attack
        )
        features["prior_goals_against"] = (
            prev_league_stats["goals_against"].mean() * league_factor_defense
        )
        features["prior_possession"] = prev_league_stats[
            "possession"
        ].mean()  # Less league-dependent
        features["prior_shots_for"] = (
            prev_league_stats["shots_for"].mean() * league_factor_attack
        )
        features["prior_shots_against"] = (
            prev_league_stats["shots_against"].mean() * league_factor_defense
        )

    else:
        # New team or no previous league data
        # Use league average as prior
        league_avg = get_league_average_stats(current_league_id, prediction_time.year)
        features["prior_xg_attack"] = league_avg["xg_for"]
        features["prior_xg_defense"] = league_avg["xg_against"]
        features["prior_goals_for"] = league_avg["goals_for"]
        features["prior_goals_against"] = league_avg["goals_against"]
        features["prior_possession"] = league_avg["possession"]
        features["prior_shots_for"] = league_avg["shots_for"]
        features["prior_shots_against"] = league_avg["shots_against"]

    # Add player-quality-based prior
    squad_value = get_squad_market_value(team_id, prediction_time)
    league_avg_value = get_league_avg_squad_value(current_league_id)
    value_ratio = squad_value / max(league_avg_value, 1e-6)

    features["prior_squad_value_ratio"] = value_ratio
    features["prior_attack_adjustment"] = (
        value_ratio * 0.3
    )  # Value correlates with attack
    features["prior_defense_adjustment"] = value_ratio * 0.2  # Less correlation

    # Manager style embedding (if available)
    manager_id = get_current_manager(team_id, prediction_time)
    if manager_id:
        manager_style = get_manager_style_embedding(manager_id, prediction_time)
        features["prior_manager_attack_style"] = manager_style["attack_tendency"]
        features["prior_manager_defense_style"] = manager_style["defense_tendency"]
        features["prior_manager_possession"] = manager_style["possession_preference"]

    # Preseason form (if available)
    preseason_matches = get_preseason_matches(team_id, prediction_time)
    if len(preseaon_matches) >= 3:
        features["prior_preseaon_xg_for"] = preseason_matches["xg_for"].mean()
        features["prior_preseaon_xg_against"] = preseason_matches["xg_against"].mean()
        features["prior_preseaon_form"] = compute_preseason_form_score(preseaon_matches)

    # Squad stability (retention rate)
    retention_rate = compute_squad_retention_rate(team_id, prediction_time)
    features["prior_squad_stability"] = retention_rate
    # Higher stability = more trust in prior
    features["prior_reliability"] = retention_rate * 0.5 + 0.5  # 0.5 to 1.0

    return features
```

**Team Prior Features (NEW - 15 features):**

| Feature                       | Type  | Description                                               |
| ----------------------------- | ----- | --------------------------------------------------------- |
| `prior_xg_attack`             | float | League-normalized xG for (from prev league or league avg) |
| `prior_xg_defense`            | float | League-normalized xG against                              |
| `prior_goals_for`             | float | League-normalized goals for                               |
| `prior_goals_against`         | float | League-normalized goals against                           |
| `prior_possession`            | float | Possession prior                                          |
| `prior_shots_for`             | float | Shots for prior                                           |
| `prior_shots_against`         | float | Shots against prior                                       |
| `prior_squad_value_ratio`     | float | Squad value / league avg value                            |
| `prior_attack_adjustment`     | float | Value-based attack adjustment                             |
| `prior_defense_adjustment`    | float | Value-based defense adjustment                            |
| `prior_manager_attack_style`  | float | Manager attack tendency embedding                         |
| `prior_manager_defense_style` | float | Manager defense tendency embedding                        |
| `prior_manager_possession`    | float | Manager possession preference                             |
| `prior_preseaon_xg_for`       | float | Preseason xG for (if available)                           |
| `prior_squad_stability`       | float | Squad retention rate (0-1)                                |

---

#### 2.7.2 Layer 2: League Strength Normalization (Cross-Division Scaling)

**Key Insight:** Championship-to-Premier-League strength ratios are known. Lower division metrics must be normalized before use as priors.

**League Strength Factors:**

| Division          | Attack Factor | Defense Factor | Notes                                   |
| ----------------- | ------------- | -------------- | --------------------------------------- |
| **EPL**           | 1.00          | 1.00           | Baseline                                |
| **Championship**  | 0.65-0.75     | 0.55-0.70      | ~30% weaker attack, ~40% weaker defense |
| **La Liga**       | 1.00          | 1.00           | Baseline                                |
| **La Liga 2**     | 0.70          | 0.65           | ~30% weaker                             |
| **Bundesliga**    | 1.00          | 1.00           | Baseline                                |
| **2. Bundesliga** | 0.68          | 0.60           | ~32% weaker attack, ~40% weaker defense |
| **Serie A**       | 1.00          | 1.00           | Baseline                                |
| **Serie B**       | 0.72          | 0.68           | ~28% weaker                             |
| **Ligue 1**       | 1.00          | 1.00           | Baseline                                |
| **Ligue 2**       | 0.70          | 0.65           | ~30% weaker                             |

**Implementation:**

```python
LEAGUE_STRENGTH_FACTORS = {
    # EPL hierarchy
    39: {"attack": 1.00, "defense": 1.00},  # EPL
    40: {"attack": 0.70, "defense": 0.62},  # Championship
    41: {"attack": 0.60, "defense": 0.55},  # League One
    42: {"attack": 0.55, "defense": 0.50},  # League Two
    # La Liga hierarchy
    140: {"attack": 1.00, "defense": 1.00},  # La Liga
    141: {"attack": 0.70, "defense": 0.65},  # La Liga 2
    # Bundesliga hierarchy
    78: {"attack": 1.00, "defense": 1.00},  # Bundesliga
    79: {"attack": 0.68, "defense": 0.60},  # 2. Bundesliga
    80: {"attack": 0.60, "defense": 0.55},  # 3. Liga
    # Serie A hierarchy
    135: {"attack": 1.00, "defense": 1.00},  # Serie A
    136: {"attack": 0.72, "defense": 0.68},  # Serie B
    # Ligue 1 hierarchy
    61: {"attack": 1.00, "defense": 1.00},  # Ligue 1
    62: {"attack": 0.70, "defense": 0.65},  # Ligue 2
    # Add more leagues as needed...
}


def get_league_strength_factor(
    source_league_id: int,
    target_league_id: int,
    metric_type: str,  # 'attack' or 'defense'
) -> float:
    """
    Get normalization factor when moving from source league to target league.

    Example: Championship (40) → EPL (39)
    Returns: 0.70 (attack) or 0.62 (defense)
    """
    source_factors = LEAGUE_STRENGTH_FACTORS.get(
        source_league_id, {"attack": 0.70, "defense": 0.65}
    )
    target_factors = LEAGUE_STRENGTH_FACTORS.get(
        target_league_id, {"attack": 1.00, "defense": 1.00}
    )

    # Factor = source_strength / target_strength
    factor = source_factors[metric_type] / target_factors[metric_type]

    return factor


def normalize_league_stats(
    raw_stats: dict, source_league_id: int, target_league_id: int
) -> dict:
    """
    Normalize stats from source league to target league level.
    """
    attack_factor = get_league_strength_factor(
        source_league_id, target_league_id, "attack"
    )
    defense_factor = get_league_strength_factor(
        source_league_id, target_league_id, "defense"
    )

    normalized = {}
    normalized["xg_for"] = raw_stats.get("xg_for", 0) * attack_factor
    normalized["xg_against"] = raw_stats.get("xg_against", 0) * defense_factor
    normalized["goals_for"] = raw_stats.get("goals_for", 0) * attack_factor
    normalized["goals_against"] = raw_stats.get("goals_against", 0) * defense_factor
    normalized["shots_for"] = raw_stats.get("shots_for", 0) * attack_factor
    normalized["shots_against"] = raw_stats.get("shots_against", 0) * defense_factor

    # Possession less league-dependent
    normalized["possession"] = raw_stats.get("possession", 50.0)

    return normalized
```

**League Normalization Features (NEW - 6 features):**

| Feature                                   | Type  | Description                                   |
| ----------------------------------------- | ----- | --------------------------------------------- |
| `is_promoted_team_home`                   | int   | 1 if home team promoted this season           |
| `is_promoted_team_away`                   | int   | 1 if away team promoted this season           |
| `league_normalized_attack_strength_home`  | float | Attack strength normalized to current league  |
| `league_normalized_defense_strength_home` | float | Defense strength normalized to current league |
| `league_normalized_attack_strength_away`  | float | Attack strength normalized to current league  |
| `league_normalized_defense_strength_away` | float | Defense strength normalized to current league |

---

#### 2.7.3 Layer 3: Decay-Weighted Priors for Early Season

**Key Formula:** Blend prior with actual data using exponential decay. As more games are played, trust actual data more.

```python
def compute_decay_weighted_feature(
    prior_value: float,
    actual_rolling_value: float,
    games_played: int,
    tau: float = 4.0,  # Decay rate (typical: 3-5)
) -> float:
    """
    Blend prior with actual data using exponential decay.

    Formula: effective_feature = alpha * prior + (1-alpha) * actual
    where alpha = exp(-games_played / tau)

    tau = 3-5 is typical (higher = slower decay, more trust in prior)
    """
    if games_played == 0:
        return prior_value

    alpha = np.exp(-games_played / tau)
    effective_value = alpha * prior_value + (1 - alpha) * actual_rolling_value

    return effective_value


def compute_all_decay_weighted_features(
    team_id: int, prediction_time: datetime, prior_features: dict
) -> dict:
    """
    Compute decay-weighted features for all team stats.
    """
    games_played = get_games_played_season(team_id, prediction_time)

    # Get actual rolling stats (if available)
    if games_played > 0:
        actual_stats = compute_rolling_stats(team_id, prediction_time, window="season")
    else:
        actual_stats = {}

    features = {}

    # Decay-weighted xG
    features["decay_weighted_xg_for"] = compute_decay_weighted_feature(
        prior_features["prior_xg_attack"],
        actual_stats.get("xg_for", prior_features["prior_xg_attack"]),
        games_played,
        tau=4.0,
    )

    features["decay_weighted_xg_against"] = compute_decay_weighted_feature(
        prior_features["prior_xg_defense"],
        actual_stats.get("xg_against", prior_features["prior_xg_defense"]),
        games_played,
        tau=4.0,
    )

    # Decay-weighted goals
    features["decay_weighted_goals_for"] = compute_decay_weighted_feature(
        prior_features["prior_goals_for"],
        actual_stats.get("goals_for", prior_features["prior_goals_for"]),
        games_played,
        tau=4.0,
    )

    features["decay_weighted_goals_against"] = compute_decay_weighted_feature(
        prior_features["prior_goals_against"],
        actual_stats.get("goals_against", prior_features["prior_goals_against"]),
        games_played,
        tau=4.0,
    )

    # Decay factor itself (how much we trust prior)
    features["prior_decay_factor"] = np.exp(-games_played / 4.0)

    return features
```

**Decay-Weighted Features (NEW - 5 features):**

| Feature                        | Type  | Description                                         |
| ------------------------------ | ----- | --------------------------------------------------- |
| `decay_weighted_xg_for`        | float | Blended xG for (prior + actual)                     |
| `decay_weighted_xg_against`    | float | Blended xG against                                  |
| `decay_weighted_goals_for`     | float | Blended goals for                                   |
| `decay_weighted_goals_against` | float | Blended goals against                               |
| `prior_decay_factor`           | float | Weight on prior (1.0 = all prior, 0.0 = all actual) |

**Decay Schedule Example:**

| Games Played | Alpha (Prior Weight) | Actual Weight | Interpretation        |
| ------------ | -------------------- | ------------- | --------------------- |
| 0            | 1.00                 | 0.00          | 100% prior            |
| 1            | 0.78                 | 0.22          | 78% prior, 22% actual |
| 3            | 0.47                 | 0.53          | 47% prior, 53% actual |
| 5            | 0.29                 | 0.71          | 29% prior, 71% actual |
| 10           | 0.08                 | 0.92          | 8% prior, 92% actual  |
| 15+          | <0.03                | >0.97         | Almost all actual     |

---

#### 2.7.4 History Depth Features (Uncertainty Quantification)

**Key Principle:** Models need to know HOW MUCH data is available. This helps them understand uncertainty.

```python
def compute_history_depth_features(
    team_id: int,
    prediction_time: datetime,
    windows: list = ["last1", "last3", "last5", "last10", "season"],
) -> dict:
    """
    Compute how many games are available in each rolling window.

    This quantifies uncertainty - fewer games = less reliable features.
    """
    features = {}

    for window in windows:
        matches = get_team_matches_all_competitions(team_id, prediction_time)

        if window == "last1":
            window_matches = matches.head(1)
        elif window == "last3":
            window_matches = matches.head(3)
        elif window == "last5":
            window_matches = matches.head(5)
        elif window == "last10":
            window_matches = matches.head(10)
        elif window == "season":
            current_season = get_current_season(prediction_time)
            window_matches = matches[matches["season"] == current_season]

        count = len(window_matches)
        features[f"history_depth_{window}"] = count

        # Flag if insufficient data
        min_required = {
            "last1": 1,
            "last3": 2,
            "last5": 3,
            "last10": 5,
            "season": 3,
        }.get(window, 1)
        features[f"insufficient_data_{window}"] = 1 if count < min_required else 0

    return features
```

**History Depth Features (NEW - 10 features):**

| Feature                    | Type | Description                              |
| -------------------------- | ---- | ---------------------------------------- |
| `history_depth_last1`      | int  | Games available in last1 window          |
| `history_depth_last3`      | int  | Games available in last3 window          |
| `history_depth_last5`      | int  | Games available in last5 window          |
| `history_depth_last10`     | int  | Games available in last10 window         |
| `history_depth_season`     | int  | Games played this season                 |
| `insufficient_data_last3`  | int  | 1 if <2 games in last3 window            |
| `insufficient_data_last5`  | int  | 1 if <3 games in last5 window            |
| `insufficient_data_last10` | int  | 1 if <5 games in last10 window           |
| `insufficient_data_season` | int  | 1 if <3 games this season                |
| `total_history_depth`      | int  | Total games available (all competitions) |

---

#### 2.7.5 Rolling Windows with Padding Rules

**CRITICAL RULE:** If history < required window size, use ONLY available games. DO NOT fill missing with zeros or means.

```python
def compute_rolling_with_padding(
    team_id: int, stat: str, window_size: int, prediction_time: datetime
) -> float:
    """
    Compute rolling stat using ONLY available games.

    If < window_size games available, use what we have.
    """
    matches = get_team_matches_all_competitions(team_id, prediction_time)

    if len(matches) == 0:
        # No history - return prior or league average
        return get_team_prior(team_id, stat, prediction_time)

    # Use only available games (up to window_size)
    available_matches = matches.head(min(window_size, len(matches)))

    # Compute stat on available matches
    if stat in available_matches.columns:
        return available_matches[stat].mean()
    else:
        # Stat not available - compute from raw data
        return compute_stat_from_matches(available_matches, stat)


# Example usage:
# For "last5" window with only 3 games available:
# → Use those 3 games, don't pad with zeros or means
rolling_xg_last5 = compute_rolling_with_padding(team_id, "xg_for", 5, prediction_time)
# If only 3 games: returns mean of those 3 games
# Model sees history_depth_last5 = 3, knows uncertainty
```

**Why This Matters:**

- Padding with zeros → artificially deflates stats
- Padding with means → leaks league information
- Using only available → honest uncertainty, model can learn to handle it

---

#### 2.7.6 Player-Level Aggregation for New Squads

**Problem:** When squad turnover >40%, team-level stats are unreliable. Use player-level aggregation instead.

**See `PLAYER_PROFILES.md` for complete player aggregation system.**

```python
def compute_player_aggregated_team_strength(
    team_id: int,
    prediction_time: datetime,
    lineup_type: str = "expected",  # or 'confirmed'
) -> dict:
    """
    Build team strength embedding from player-level data.

    Used when squad turnover is high or team is new.
    """
    # Get expected/confirmed lineup
    lineup = get_lineup(team_id, prediction_time, lineup_type)

    if not lineup or len(lineup) < 8:  # Need at least 8 players
        # Fallback to squad-level prior
        return compute_team_prior_embedding(
            team_id, get_league(team_id), prediction_time
        )

    player_ids = lineup["startXI"]

    # Get player stats (from previous season or current season)
    player_stats = get_player_stats(player_ids, prediction_time)

    # Position weights (attackers matter more for xG)
    position_weights = {
        "GK": 0.8,  # Goalkeeper
        "DEF": 0.9,  # Defender
        "MID": 1.1,  # Midfielder
        "FWD": 1.3,  # Forward
    }

    features = {}

    # Weighted sum of player xG contributions
    total_xg_contribution = 0
    for _, player in player_stats.iterrows():
        weight = position_weights.get(player["position"], 1.0)
        xg_per90 = player.get("xg_per90", 0)
        total_xg_contribution += xg_per90 * weight

    features["player_aggregated_xg_for"] = (
        total_xg_contribution / 11
    )  # Per team average

    # Weighted sum of defensive contributions
    total_defensive_value = 0
    for _, player in player_stats.iterrows():
        weight = position_weights.get(player["position"], 1.0)
        defensive_rating = player.get("defensive_rating", 0)
        total_defensive_value += defensive_rating * weight

    features["player_aggregated_defense"] = total_defensive_value / 11

    # Transfermarkt value aggregation
    total_value = player_stats["market_value"].sum()
    league_avg_value = get_league_avg_squad_value(get_league(team_id))
    features["player_aggregated_value_ratio"] = total_value / max(
        league_avg_value, 1e-6
    )

    # Squad turnover indicator
    squad_turnover = compute_squad_turnover_rate(team_id, prediction_time)
    features["squad_turnover_rate"] = squad_turnover
    features["use_player_aggregation"] = 1 if squad_turnover > 0.40 else 0

    return features
```

**Player Aggregation Features (NEW - 5 features):**

| Feature                         | Type  | Description                                 |
| ------------------------------- | ----- | ------------------------------------------- |
| `player_aggregated_xg_for`      | float | Team xG from player-level aggregation       |
| `player_aggregated_defense`     | float | Team defense from player-level aggregation  |
| `player_aggregated_value_ratio` | float | Squad value ratio (player sum / league avg) |
| `squad_turnover_rate`           | float | % of squad that changed (0-1)               |
| `use_player_aggregation`        | int   | 1 if turnover >40%, use player aggregation  |

---

#### 2.7.7 Preseason Embeddings (If Available)

```python
def compute_preseason_embedding(team_id: int, prediction_time: datetime) -> dict:
    """
    Extract team direction from preseason games.

    Even 3-4 preseason games help calibrate team direction.
    """
    preseason_matches = get_preseaon_matches(team_id, prediction_time)

    features = {}

    if len(preseaon_matches) >= 2:
        features["preseaon_xg_for"] = preseason_matches["xg_for"].mean()
        features["preseaon_xg_against"] = preseason_matches["xg_against"].mean()
        features["preseaon_goals_for"] = preseason_matches["goals_for"].mean()
        features["preseaon_goals_against"] = preseason_matches["goals_against"].mean()
        features["preseaon_wins"] = (preseaon_matches["result"] == "W").sum()
        features["preseaon_form_score"] = compute_form_score(preseaon_matches)
        features["preseaon_available"] = 1
    else:
        # No preseason data
        features["preseaon_xg_for"] = np.nan
        features["preseaon_xg_against"] = np.nan
        features["preseaon_goals_for"] = np.nan
        features["preseaon_goals_against"] = np.nan
        features["preseaon_wins"] = 0
        features["preseaon_form_score"] = 0.5  # Neutral
        features["preseaon_available"] = 0

    return features
```

**Preseason Features (NEW - 7 features):**

| Feature                  | Type  | Description                        |
| ------------------------ | ----- | ---------------------------------- |
| `preseaon_xg_for`        | float | Average xG for in preseason        |
| `preseaon_xg_against`    | float | Average xG against in preseason    |
| `preseaon_goals_for`     | float | Average goals for in preseason     |
| `preseaon_goals_against` | float | Average goals against in preseason |
| `preseaon_wins`          | int   | Number of preseason wins           |
| `preseaon_form_score`    | float | Preseason form score (0-1)         |
| `preseaon_available`     | int   | 1 if preseason data available      |

---

#### 2.7.8 Team-Style PCA Embeddings from Prior Season

**Key Insight:** Team-style principal components shrink the "team identity gap" dramatically.

```python
def compute_team_style_pca_embedding(
    team_id: int, current_league_id: int, prediction_time: datetime
) -> dict:
    """
    Extract team style PCs from previous season.

    These capture playing style (possession, pressing, pace) which
    transfers better across leagues than raw stats.
    """
    # Get previous season matches (or previous league if promoted)
    prev_matches = get_previous_season_matches(team_id, prediction_time)

    if len(prev_matches) < 10:
        # Not enough data - return neutral embedding
        return {
            "style_pc1": 0.0,
            "style_pc2": 0.0,
            "style_pc3": 0.0,
            "style_embedding_available": 0,
        }

    # Compute style features from matches
    style_features = compute_match_style_features(prev_matches)

    # Apply PCA (trained on all teams, all seasons)
    pca_model = load_team_style_pca_model()
    style_pcs = pca_model.transform(style_features)

    features = {}
    features["style_pc1"] = style_pcs[0]  # Main style component
    features["style_pc2"] = style_pcs[1]  # Secondary component
    features["style_pc3"] = style_pcs[2]  # Tertiary component
    features["style_embedding_available"] = 1

    return features
```

**Style PCA Features (NEW - 4 features):**

| Feature                     | Type  | Description                            |
| --------------------------- | ----- | -------------------------------------- |
| `style_pc1`                 | float | First principal component (main style) |
| `style_pc2`                 | float | Second principal component             |
| `style_pc3`                 | float | Third principal component              |
| `style_embedding_available` | int   | 1 if style embedding computed          |

---

#### 2.7.9 Feature: `games_since_season_start`

**Already exists** (see section 2.5), but critical for promoted teams:

```python
# This feature helps models learn:
# - Early-season metrics are unreliable
# - Priors matter more in first 6-10 matches
# - Volatility is higher early season

features["games_since_season_start"] = get_games_played_season(team_id, prediction_time)
```

Models automatically learn that:

- `games_since_season_start < 5` → High uncertainty, trust priors
- `games_since_season_start > 10` → Lower uncertainty, trust actuals

---

#### 2.7.10 Summary: Promoted Team Feature Block

**Total New Features: 57**

| Category              | Count | Features                                                          |
| --------------------- | ----- | ----------------------------------------------------------------- |
| Team Prior Embeddings | 15    | prior_xg_attack, prior_xg_defense, prior_goals_for, etc.          |
| League Normalization  | 6     | is_promoted_team, league_normalized_attack_strength, etc.         |
| Decay-Weighted        | 5     | decay_weighted_xg_for, decay_weighted_xg_against, etc.            |
| History Depth         | 10    | history_depth_last1, history_depth_last3, insufficient_data flags |
| Player Aggregation    | 5     | player_aggregated_xg_for, squad_turnover_rate, etc.               |
| Preseason             | 7     | preseaon_xg_for, preseaon_form_score, etc.                        |
| Style PCA             | 4     | style_pc1, style_pc2, style_pc3                                   |
| Games Since Start     | 1     | games_since_season_start (already exists)                         |

**Implementation Priority:**

1. **P0 (Critical):** History depth features, rolling windows with padding, games_since_season_start
2. **P1 (High):** Team prior embeddings, league normalization, decay-weighted features
3. **P2 (Medium):** Player aggregation, preseason embeddings, style PCA

**Usage in Feature Pipeline:**

```python
def compute_pregame_features_with_promoted_handling(
    fixture_id: int, prediction_time: datetime
) -> dict:
    """Compute features with robust promoted team handling."""
    home_team, away_team = get_teams(fixture_id)

    features = {}

    # Standard features (with padding rules)
    features.update(compute_standard_features(home_team, "home", prediction_time))
    features.update(compute_standard_features(away_team, "away", prediction_time))

    # History depth (uncertainty quantification)
    features.update(compute_history_depth_features(home_team, prediction_time))
    features.update(compute_history_depth_features(away_team, prediction_time))

    # Check if teams are promoted/new
    home_is_promoted = check_if_promoted(
        home_team, get_league(fixture_id), prediction_time
    )
    away_is_promoted = check_if_promoted(
        away_team, get_league(fixture_id), prediction_time
    )

    if home_is_promoted or features["history_depth_season_home"] < 5:
        # Use prior + decay-weighted features
        home_prior = compute_team_prior_embedding(
            home_team, get_league(fixture_id), prediction_time
        )
        features.update({f"home_{k}": v for k, v in home_prior.items()})

        decay_weighted = compute_all_decay_weighted_features(
            home_team, prediction_time, home_prior
        )
        features.update({f"home_{k}": v for k, v in decay_weighted.items()})

    if away_is_promoted or features["history_depth_season_away"] < 5:
        # Same for away team
        away_prior = compute_team_prior_embedding(
            away_team, get_league(fixture_id), prediction_time
        )
        features.update({f"away_{k}": v for k, v in away_prior.items()})

        decay_weighted = compute_all_decay_weighted_features(
            away_team, prediction_time, away_prior
        )
        features.update({f"away_{k}": v for k, v in decay_weighted.items()})

    # High squad turnover → use player aggregation
    if features.get("squad_turnover_rate_home", 0) > 0.40:
        player_features = compute_player_aggregated_team_strength(
            home_team, prediction_time
        )
        features.update({f"home_{k}": v for k, v in player_features.items()})

    if features.get("squad_turnover_rate_away", 0) > 0.40:
        player_features = compute_player_aggregated_team_strength(
            away_team, prediction_time
        )
        features.update({f"away_{k}": v for k, v in player_features.items()})

    return features
```

**This is EXACTLY how professional syndicates handle fresh-season teams.**

---

## 3. Pre-Game Features (~160)

### 3.1 Market Features (123)

#### 3.1.1 H2H (Head-to-Head) 3-Way Market (12 features)

**Source:** Odds API

| Feature                  | Type  | Description                      |
| ------------------------ | ----- | -------------------------------- |
| `odds_h2h_home`          | float | Home win decimal odds (best)     |
| `odds_h2h_draw`          | float | Draw decimal odds (best)         |
| `odds_h2h_away`          | float | Away win decimal odds (best)     |
| `odds_h2h_home_prob`     | float | Implied prob home (vig-adjusted) |
| `odds_h2h_draw_prob`     | float | Implied prob draw (vig-adjusted) |
| `odds_h2h_away_prob`     | float | Implied prob away (vig-adjusted) |
| `odds_h2h_home_pinnacle` | float | Pinnacle home odds               |
| `odds_h2h_draw_pinnacle` | float | Pinnacle draw odds               |
| `odds_h2h_away_pinnacle` | float | Pinnacle away odds               |
| `odds_h2h_vig`           | float | Total bookmaker margin           |
| `odds_h2h_max_vig`       | float | Max vig across bookmakers        |
| `odds_h2h_min_vig`       | float | Min vig (sharp indicator)        |

#### 3.1.2 Asian Handicap Market (18 features)

| Feature                    | Description                              |
| -------------------------- | ---------------------------------------- |
| `odds_ah_{line}_home/away` | AH odds for lines: 0, ±0.5, ±1, ±1.5, ±2 |
| `ah_primary_line`          | Most liquid AH line                      |
| `ah_vig`                   | AH market margin                         |

#### 3.1.3 Totals (Over/Under) Market (14 features)

| Feature                        | Description                                      |
| ------------------------------ | ------------------------------------------------ |
| `odds_total_{line}_over/under` | O/U odds for lines: 0.5, 1.5, 2.5, 3.5, 4.5, 5.5 |
| `total_primary_line`           | Most liquid total line                           |
| `total_vig`                    | Totals margin                                    |

#### 3.1.4 Price Dynamics & Microstructure (45 features) 🔥

**Why This Matters:**

- Closing line prediction is market microstructure modelling
- Basic approach: features → closing line
- **Syndicate approach: features + price PATH → closing line**
- The path of odds movement contains information the levels don't

---

##### 3.1.4.1 Odds Velocity (18 features)

**Not just drift (Δ odds), but rate of change per unit time:**

**Snapshot Schedule:** `T-24h, T-12h, T-6h, T-90m, T-80m, T-70m, T-60m, T-50m, T-40m, T-30m, T-20m, T-10m, T-0, HT-2min`

| Feature                    | Type  | Description                                     |
| -------------------------- | ----- | ----------------------------------------------- |
| `velocity_home_24h_to_12h` | float | (prob_12h - prob_24h) / 12 hours (early market) |
| `velocity_home_24h_to_6h`  | float | (prob_6h - prob_24h) / 18 hours                 |
| `velocity_home_6h_to_90m`  | float | (prob_90m - prob_6h) / 4.5 hours                |
| `velocity_home_90m_to_30m` | float | (prob_30m - prob_90m) / 60 mins                 |
| `velocity_home_30m_to_10m` | float | (prob_10m - prob_30m) / 20 mins                 |
| `velocity_home_10m_to_0`   | float | (prob_0 - prob_10m) / 10 mins                   |
| `velocity_draw_*`          | float | Same for draw (6 features)                      |
| `velocity_away_*`          | float | Same for away (6 features)                      |

**HT-Specific Velocity:**
| Feature | Type | Description |
|---------|------|-------------|
| `velocity_ht_home` | float | (prob_HT-2min - prob_0) / halftime duration |

**Interpretation:**

- High velocity T-24h→T-12h = early sharp action (informed bettors)
- High velocity T-30m→T-0 = late sharp action (final market)
- Acceleration (velocity increasing) = money piling in
- Deceleration = market stabilizing

```python
def compute_odds_velocity(odds_history: list, market: str = "home") -> dict:
    """
    Compute velocity (Δprob / Δtime) between each snapshot.

    odds_history: list of {timestamp, odds_home, odds_draw, odds_away}
    """
    features = {}

    # Sort by timestamp
    sorted_odds = sorted(odds_history, key=lambda x: x["timestamp"])

    for i in range(1, len(sorted_odds)):
        prev = sorted_odds[i - 1]
        curr = sorted_odds[i]

        # Time delta in hours
        dt_hours = (curr["timestamp"] - prev["timestamp"]).total_seconds() / 3600

        if dt_hours > 0:
            # Convert odds to implied probability
            prev_prob = 1 / prev[f"odds_{market}"]
            curr_prob = 1 / curr[f"odds_{market}"]

            # Velocity = Δprob / Δtime
            velocity = (curr_prob - prev_prob) / dt_hours

            # Name based on time window
            window_name = get_window_name(prev["timestamp"], curr["timestamp"])
            features[f"velocity_{market}_{window_name}"] = velocity

    return features
```

---

##### 3.1.4.2 Odds Acceleration (6 features)

**Second derivative: Is velocity increasing or decreasing?**

| Feature               | Type  | Description                  |
| --------------------- | ----- | ---------------------------- |
| `accel_home_6h_to_1h` | float | velocity_1h - velocity_24h   |
| `accel_home_1h_to_0`  | float | velocity_final - velocity_1h |
| `accel_draw_*`        | float | Same for draw                |
| `accel_away_*`        | float | Same for away                |

**Interpretation:**

- Positive acceleration = money accelerating into position
- Negative acceleration = movement slowing down
- Sharp spikes in acceleration = steam moves

```python
def compute_acceleration(velocities: dict, market: str) -> dict:
    """
    Acceleration = change in velocity between periods.
    """
    features = {}

    v1 = velocities.get(f"velocity_{market}_24h_to_6h", 0)
    v2 = velocities.get(f"velocity_{market}_6h_to_1h", 0)
    v3 = velocities.get(f"velocity_{market}_1h_to_0", 0)

    features[f"accel_{market}_early"] = v2 - v1  # Did movement speed up mid-day?
    features[f"accel_{market}_late"] = v3 - v2  # Did movement speed up late?

    return features
```

---

##### 3.1.4.3 Volatility & Noise (8 features)

**Is the path smooth or noisy?**

| Feature                      | Type  | Description             |
| ---------------------------- | ----- | ----------------------- |
| `volatility_home_24h`        | float | Std dev of prob changes |
| `volatility_draw_24h`        | float | Std dev of prob changes |
| `volatility_away_24h`        | float | Std dev of prob changes |
| `volatility_ratio_home_away` | float | vol_home / vol_away     |
| `path_smoothness_home`       | float | 1 = smooth, 0 = jumpy   |
| `path_smoothness_away`       | float | 1 = smooth, 0 = jumpy   |
| `max_single_move_home`       | float | Largest single Δprob    |
| `max_single_move_away`       | float | Largest single Δprob    |

**Interpretation:**

- High volatility = uncertain market, information arriving
- Low volatility = consensus view
- Single large move = sharp money / steam
- Smooth path = recreational money gradually arriving

```python
def compute_path_features(odds_history: list, market: str) -> dict:
    """
    Compute path characteristics: volatility, smoothness, jumps.
    """
    probs = [
        1 / o[f"odds_{market}"]
        for o in sorted(odds_history, key=lambda x: x["timestamp"])
    ]
    changes = np.diff(probs)

    features = {}

    # Volatility = std of changes
    features[f"volatility_{market}_24h"] = np.std(changes) if len(changes) > 0 else 0

    # Max single move (absolute)
    features[f"max_single_move_{market}"] = (
        np.max(np.abs(changes)) if len(changes) > 0 else 0
    )

    # Smoothness: inverse of (max_move / total_move)
    total_move = abs(probs[-1] - probs[0]) if len(probs) > 1 else 0.001
    max_move = features[f"max_single_move_{market}"]
    features[f"path_smoothness_{market}"] = 1 - (max_move / max(total_move, 0.001))

    return features
```

---

##### 3.1.4.4 Steam Move Detection (6 features)

**Steam move = sharp syndicate money moving the line quickly**

| Feature                | Type  | Description                |
| ---------------------- | ----- | -------------------------- |
| `steam_detected_home`  | int   | 1 if steam move on home    |
| `steam_detected_away`  | int   | 1 if steam move on away    |
| `steam_magnitude_home` | float | Size of steam move (Δprob) |
| `steam_magnitude_away` | float | Size of steam move         |
| `steam_timing_home`    | float | Hours before kickoff       |
| `steam_timing_away`    | float | Hours before kickoff       |

**Steam Detection Logic:**

```python
def detect_steam_moves(odds_history: list, market: str) -> dict:
    """
    Detect sharp/steam moves in odds path.

    Steam move criteria:
    1. Prob change > 2% in < 30 minutes
    2. Multiple books move in same direction
    3. Move persists (doesn't reverse)
    """
    features = {
        f"steam_detected_{market}": 0,
        f"steam_magnitude_{market}": 0,
        f"steam_timing_{market}": 0,
    }

    sorted_odds = sorted(odds_history, key=lambda x: x["timestamp"])
    kickoff = sorted_odds[-1]["timestamp"]

    for i in range(1, len(sorted_odds)):
        prev = sorted_odds[i - 1]
        curr = sorted_odds[i]

        dt_minutes = (curr["timestamp"] - prev["timestamp"]).total_seconds() / 60

        if dt_minutes > 0 and dt_minutes <= 30:
            prev_prob = 1 / prev[f"odds_{market}"]
            curr_prob = 1 / curr[f"odds_{market}"]
            delta_prob = abs(curr_prob - prev_prob)

            # Steam threshold: > 2% move in <= 30 min
            if delta_prob > 0.02:
                features[f"steam_detected_{market}"] = 1
                features[f"steam_magnitude_{market}"] = max(
                    features[f"steam_magnitude_{market}"], delta_prob
                )
                hours_before = (kickoff - curr["timestamp"]).total_seconds() / 3600
                features[f"steam_timing_{market}"] = hours_before

    return features
```

---

##### 3.1.4.5 Bookmaker Microstructure (13 features)

**Which book moves first? Who leads and who follows?**

| Feature                   | Type  | Description                         |
| ------------------------- | ----- | ----------------------------------- |
| `pinnacle_lead_time_home` | float | How early Pinnacle moved (mins)     |
| `pinnacle_lead_time_away` | float | How early Pinnacle moved            |
| `bet365_lag_home`         | float | Bet365 reaction time to Pinnacle    |
| `bet365_lag_away`         | float | Bet365 reaction time                |
| `asian_leads_european`    | int   | 1 if Asian books moved first        |
| `sbo_pinnacle_delta_home` | float | SBO prob - Pinnacle prob            |
| `sbo_pinnacle_delta_away` | float | Proxy for sharp disagreement        |
| `book_fragmentation_home` | float | Std dev across books at T-1h        |
| `book_fragmentation_away` | float | High = books disagree               |
| `books_in_sync`           | int   | 1 if all books moved same direction |
| `pinnacle_vs_market_home` | float | Pinnacle prob vs avg                |
| `pinnacle_vs_market_away` | float | Pinnacle prob vs avg                |
| `sharp_soft_spread`       | float | Pinnacle margin vs avg soft book    |

**Why Pinnacle Matters:**

- Pinnacle = sharp book (low margin, accepts big bets, doesn't limit)
- Pinnacle price = closest to "true" probability
- Other books follow Pinnacle with lag
- When Pinnacle moves and others don't → opportunity

```python
def compute_bookmaker_microstructure(
    odds_by_book: dict,  # {bookmaker: [{timestamp, odds_home, odds_draw, odds_away}]}
    prediction_time: datetime,
) -> dict:
    """
    Analyze bookmaker-level dynamics.

    Key books to track:
    - Pinnacle (sharp, reference)
    - SBO/SBOBET (Asian sharp)
    - Bet365 (European soft, high volume)
    - 1xBet (soft)
    """
    features = {}

    SHARP_BOOKS = ["pinnacle", "sbobet", "betfair_exchange"]
    SOFT_BOOKS = ["bet365", "1xbet", "unibet", "betway"]

    # 1. Who moved first?
    for market in ["home", "away"]:
        first_mover = find_first_mover(odds_by_book, market, threshold=0.01)
        features[f"first_mover_{market}"] = first_mover["bookmaker"]
        features[f"first_mover_time_{market}"] = first_mover["hours_before_kickoff"]

    # 2. Pinnacle lead time
    pinnacle_moves = get_significant_moves(odds_by_book.get("pinnacle", []))
    features["pinnacle_lead_time_home"] = pinnacle_moves.get("first_move_time_home", 0)

    # 3. Bet365 lag (how long after Pinnacle)
    bet365_moves = get_significant_moves(odds_by_book.get("bet365", []))
    pinn_time = pinnacle_moves.get("first_move_timestamp_home")
    b365_time = bet365_moves.get("first_move_timestamp_home")
    if pinn_time and b365_time:
        features["bet365_lag_home"] = (b365_time - pinn_time).total_seconds() / 60

    # 4. Asian vs European timing
    asian_first = any(
        find_first_mover(odds_by_book, "home")["bookmaker"]
        in ["sbobet", "maxbet", "singbet"]
        for _ in [1]
    )
    features["asian_leads_european"] = 1 if asian_first else 0

    # 5. Book fragmentation (disagreement)
    probs_at_t1h = {}
    for book, history in odds_by_book.items():
        t1h_odds = get_odds_at_time(history, prediction_time)
        if t1h_odds:
            probs_at_t1h[book] = 1 / t1h_odds["odds_home"]

    if len(probs_at_t1h) > 1:
        features["book_fragmentation_home"] = np.std(list(probs_at_t1h.values()))
    else:
        features["book_fragmentation_home"] = 0

    # 6. Pinnacle vs market average
    pinnacle_prob = probs_at_t1h.get("pinnacle", 0)
    avg_prob = np.mean(list(probs_at_t1h.values())) if probs_at_t1h else 0
    features["pinnacle_vs_market_home"] = pinnacle_prob - avg_prob

    # 7. Sharp vs soft spread
    sharp_probs = [probs_at_t1h.get(b, 0) for b in SHARP_BOOKS if b in probs_at_t1h]
    soft_probs = [probs_at_t1h.get(b, 0) for b in SOFT_BOOKS if b in probs_at_t1h]
    if sharp_probs and soft_probs:
        features["sharp_soft_spread"] = np.mean(sharp_probs) - np.mean(soft_probs)

    return features


def find_first_mover(odds_by_book: dict, market: str, threshold: float = 0.01) -> dict:
    """
    Find which bookmaker first moved the line significantly.
    """
    first_move = {"bookmaker": None, "hours_before_kickoff": 999}

    for bookmaker, history in odds_by_book.items():
        sorted_h = sorted(history, key=lambda x: x["timestamp"])

        if len(sorted_h) < 2:
            continue

        baseline_prob = 1 / sorted_h[0][f"odds_{market}"]
        kickoff = sorted_h[-1]["timestamp"]

        for i in range(1, len(sorted_h)):
            curr_prob = 1 / sorted_h[i][f"odds_{market}"]
            if abs(curr_prob - baseline_prob) > threshold:
                hours_before = (
                    kickoff - sorted_h[i]["timestamp"]
                ).total_seconds() / 3600
                if hours_before < first_move["hours_before_kickoff"]:
                    first_move = {
                        "bookmaker": bookmaker,
                        "hours_before_kickoff": hours_before,
                        "move_size": curr_prob - baseline_prob,
                    }
                break

    return first_move
```

---

##### 3.1.4.6 Reverse Line Movement (RLM) Detection

**RLM = line moves OPPOSITE to public betting %**

| Feature              | Type  | Description          |
| -------------------- | ----- | -------------------- |
| `rlm_detected_home`  | int   | 1 if RLM on home     |
| `rlm_magnitude_home` | float | Size of reverse move |

**Why RLM matters:**

- Public bets home → line SHOULD shorten on home
- If line lengthens → sharps betting opposite side
- RLM is one of the strongest sharp signals

```python
def detect_reverse_line_movement(
    odds_history: list,
    public_betting_pct: dict,  # {'home': 0.65, 'draw': 0.15, 'away': 0.20}
) -> dict:
    """
    Detect reverse line movement.

    RLM occurs when:
    - Public heavily on one side (> 60%)
    - Line moves AGAINST public side
    """
    features = {"rlm_detected_home": 0, "rlm_detected_away": 0}

    if not odds_history or not public_betting_pct:
        return features

    sorted_odds = sorted(odds_history, key=lambda x: x["timestamp"])

    open_prob_home = 1 / sorted_odds[0]["odds_home"]
    close_prob_home = 1 / sorted_odds[-1]["odds_home"]
    prob_drift_home = close_prob_home - open_prob_home

    public_home = public_betting_pct.get("home", 0.33)

    # RLM: Public on home (> 60%) but line drifts AWAY from home (prob decreases)
    if public_home > 0.60 and prob_drift_home < -0.02:
        features["rlm_detected_home"] = 1
        features["rlm_magnitude_home"] = abs(prob_drift_home)

    # Same for away
    public_away = public_betting_pct.get("away", 0.33)
    open_prob_away = 1 / sorted_odds[0]["odds_away"]
    close_prob_away = 1 / sorted_odds[-1]["odds_away"]
    prob_drift_away = close_prob_away - open_prob_away

    if public_away > 0.60 and prob_drift_away < -0.02:
        features["rlm_detected_away"] = 1
        features["rlm_magnitude_away"] = abs(prob_drift_away)

    return features
```

---

##### Summary: Price Dynamics Features

| Category                     | Count | Key Insight                    |
| ---------------------------- | ----- | ------------------------------ |
| **Velocity**                 | 12    | Rate of change per time period |
| **Acceleration**             | 6     | Is movement speeding up?       |
| **Volatility/Path**          | 8     | Smooth vs jumpy path           |
| **Steam Detection**          | 6     | Sharp money spikes             |
| **Bookmaker Microstructure** | 13    | Who moves first, fragmentation |

**Total: 45 price dynamics features**

**Why This Is Elite-Level:**

```
Basic Model:    features → closing_line
Syndicate Model: features + price_PATH → closing_line
                          ^^^^^^^^^^^^
                          You were missing this
```

The PATH of odds contains:

- Information about WHO is betting (sharp vs public)
- HOW FAST information is being incorporated
- WHETHER the market is uncertain or confident
- Timing of sharp action (late = more confident)

---

#### 3.1.5 Market Structure & Efficiency Features (28 features) 🔥

**Why This Matters:**

- Market efficiency varies MASSIVELY by league
- EPL = highly efficient (sharps everywhere, low edge)
- Moldovan Liga = inefficient (sharps ignore it, more edge)
- Model must learn different priors per league-bookmaker combo

---

##### 3.1.5.1 Bookmaker Type Classification

**CRITICAL: Not all bookmakers are equal.**

| Type             | Examples                                    | Characteristics                                   | Use                  |
| ---------------- | ------------------------------------------- | ------------------------------------------------- | -------------------- |
| **Sharp**        | Pinnacle, SBOBET, Betfair Exchange          | Low margins, accept big bets, don't limit winners | Reference price      |
| **Market Maker** | Betfair, Matchbook                          | True exchange prices, liquidity-driven            | Purest odds          |
| **Semi-Sharp**   | Bet365, Unibet                              | High volume, some limits, follow sharps           | Volume indicator     |
| **Recreational** | William Hill, SkyBet, PaddyPower, Ladbrokes | High margins, limit winners, recreational focus   | Soft money indicator |

```python
# ACTUAL BOOKMAKERS FROM ODDS API (our data sources)
BOOKMAKER_CLASSIFICATION = {
    # Sharp books (reference prices - won't limit you)
    "sharp": ["pinnacle"],
    # Exchanges (true market prices - won't limit you)
    "exchange": ["betfair_uk", "matchbook"],
    # Semi-sharp (low margin, accept some sharp action)
    "semi_sharp": ["lowvig"],
    # Soft books (will limit winners)
    "soft": ["bovada", "betonlineag", "mybookieag", "betus", "gtbets"],
}
```

---

##### 3.1.5.2 Sharp vs Soft Separation Features (10 features)

| Feature                   | Type  | Description                         |
| ------------------------- | ----- | ----------------------------------- |
| `sharp_consensus_home`    | float | Avg implied prob across sharp books |
| `sharp_consensus_away`    | float | Avg implied prob across sharp books |
| `soft_consensus_home`     | float | Avg implied prob across soft books  |
| `soft_consensus_away`     | float | Avg implied prob across soft books  |
| `sharp_soft_delta_home`   | float | sharp_prob - soft_prob (KEY!)       |
| `sharp_soft_delta_away`   | float | sharp_prob - soft_prob              |
| `sharp_book_count`        | int   | # of sharp books with prices        |
| `soft_book_count`         | int   | # of soft books with prices         |
| `exchange_price_home`     | float | Betfair/Matchbook price (purest)    |
| `exchange_vs_sharp_delta` | float | Exchange - Sharp consensus          |

**Why `sharp_soft_delta` is GOLD:**

- If sharps say 55% but softs say 50% → sharps see value on home
- Softs follow sharps with LAG → this delta predicts closing line movement
- Large delta = market inefficiency = potential edge

```python
def compute_sharp_soft_features(odds_by_book: dict, prediction_time: datetime) -> dict:
    """
    Compute separation between sharp and soft bookmakers.
    """
    features = {}

    sharp_probs_home = []
    soft_probs_home = []

    for bookmaker, history in odds_by_book.items():
        odds_at_time = get_odds_at_time(history, prediction_time)
        if not odds_at_time:
            continue

        prob_home = 1 / odds_at_time["odds_home"]

        if bookmaker in BOOKMAKER_CLASSIFICATION["sharp"]:
            sharp_probs_home.append(prob_home)
        elif bookmaker in BOOKMAKER_CLASSIFICATION["recreational"]:
            soft_probs_home.append(prob_home)

    # Sharp consensus
    if sharp_probs_home:
        features["sharp_consensus_home"] = np.mean(sharp_probs_home)
    else:
        features["sharp_consensus_home"] = 0.33

    # Soft consensus
    if soft_probs_home:
        features["soft_consensus_home"] = np.mean(soft_probs_home)
    else:
        features["soft_consensus_home"] = 0.33

    # THE KEY FEATURE: Sharp-Soft Delta
    features["sharp_soft_delta_home"] = (
        features["sharp_consensus_home"] - features["soft_consensus_home"]
    )

    return features
```

---

##### 3.1.5.3 Market Efficiency by League (12 features)

**Different leagues have VERY different market quality.**

| League Tier                  | Examples                                   | Market Efficiency | Typical Edge |
| ---------------------------- | ------------------------------------------ | ----------------- | ------------ |
| **Tier 1** (hyper-efficient) | EPL, La Liga, Bundesliga, Serie A, Ligue 1 | 95-98%            | 1-2%         |
| **Tier 2** (efficient)       | Eredivisie, Primeira Liga, Süper Lig       | 90-95%            | 2-4%         |
| **Tier 3** (moderate)        | MLS, Championship, Belgian First           | 85-90%            | 4-6%         |
| **Tier 4** (inefficient)     | Swiss, Czech, Polish                       | 80-85%            | 6-10%        |
| **Tier 5** (weak)            | Moldovan, Cypriot, lower Asian             | 70-80%            | 10%+         |

| Feature                        | Type  | Description                              |
| ------------------------------ | ----- | ---------------------------------------- |
| `league_efficiency_score`      | float | Pre-computed efficiency (0-1)            |
| `league_sharp_book_coverage`   | int   | # of sharp books covering this league    |
| `league_avg_margin`            | float | Avg bookmaker margin in this league      |
| `league_odds_variance_home`    | float | Historical variance of odds across books |
| `league_odds_variance_away`    | float | Historical variance                      |
| `league_closing_line_accuracy` | float | How often CL beats opening               |
| `league_steam_frequency`       | float | How often steam moves occur              |
| `league_pinnacle_available`    | int   | 1 if Pinnacle covers this league         |
| `league_betfair_liquidity`     | float | Avg Betfair volume (0=none)              |
| `league_bookmaker_count`       | int   | # of books offering odds                 |
| `league_tier`                  | int   | 1-5 efficiency tier                      |
| `market_maturity_score`        | float | Combined efficiency metric               |

```python
# Pre-computed league efficiency scores
LEAGUE_EFFICIENCY = {
    # Tier 1: Hyper-efficient
    39: 0.97,  # EPL
    140: 0.96,  # La Liga
    78: 0.95,  # Bundesliga
    135: 0.95,  # Serie A
    61: 0.94,  # Ligue 1
    # Tier 2: Efficient
    88: 0.91,  # Eredivisie
    94: 0.90,  # Primeira Liga
    203: 0.89,  # Süper Lig
    # Tier 3: Moderate
    253: 0.85,  # MLS
    40: 0.84,  # Championship
    144: 0.83,  # Belgian First
    # Tier 4: Inefficient
    207: 0.78,  # Swiss Super League
    345: 0.76,  # Czech First
    106: 0.75,  # Polish Ekstraklasa
    # Tier 5: Weak markets
    235: 0.65,  # Moldova
    318: 0.63,  # Cyprus
    # etc.
}


def compute_league_efficiency_features(league_id: int, fixture_id: int) -> dict:
    """
    Compute market efficiency features for this league.
    """
    features = {}

    # Static efficiency score
    features["league_efficiency_score"] = LEAGUE_EFFICIENCY.get(league_id, 0.80)
    features["league_tier"] = get_league_tier(league_id)

    # Dynamic: How many sharp books cover this fixture?
    odds = get_fixture_odds(fixture_id)
    sharp_coverage = sum(
        1 for b in odds.keys() if b in BOOKMAKER_CLASSIFICATION["sharp"]
    )
    features["league_sharp_book_coverage"] = sharp_coverage

    # Is Pinnacle available?
    features["league_pinnacle_available"] = 1 if "pinnacle" in odds else 0

    # Bookmaker count
    features["league_bookmaker_count"] = len(odds)

    # Historical variance across books (pre-computed per league)
    features["league_odds_variance_home"] = get_league_odds_variance(league_id, "home")
    features["league_odds_variance_away"] = get_league_odds_variance(league_id, "away")

    # Combined maturity score
    features["market_maturity_score"] = (
        features["league_efficiency_score"] * 0.4
        + min(sharp_coverage / 3, 1) * 0.3
        + min(features["league_bookmaker_count"] / 10, 1) * 0.3
    )

    return features
```

---

##### 3.1.5.4 Bookmaker Weighting Features (6 features)

**Model should weight bookmaker opinions differently.**

| Feature                   | Type  | Description                                     |
| ------------------------- | ----- | ----------------------------------------------- |
| `pinnacle_weight`         | float | Pinnacle prob / avg prob (>1 = Pinnacle higher) |
| `betfair_weight`          | float | Betfair prob / avg prob                         |
| `sharp_vs_all_weight`     | float | Sharp avg / all avg                             |
| `weighted_consensus_home` | float | Bookmaker-weighted prob (sharps count more)     |
| `weighted_consensus_away` | float | Bookmaker-weighted prob                         |
| `max_min_spread`          | float | Max prob - Min prob across all books            |

```python
# Bookmaker weights (how much to trust each) - ACTUAL ODDS API BOOKMAKERS
BOOKMAKER_WEIGHTS = {
    # Sharp (high weight - reference prices)
    "pinnacle": 1.0,  # Gold standard sharp
    # Exchanges (high weight - true market)
    "betfair_uk": 0.98,  # Betfair Exchange
    "matchbook": 0.90,  # Exchange
    # Semi-sharp (medium weight)
    "lowvig": 0.80,  # Low margin book
    # Soft markets (lower weight - follow sharps)
    "bovada": 0.55,  # US market, high volume
    "betonlineag": 0.50,  # US market
    "mybookieag": 0.50,  # US market
    "betus": 0.45,  # US market
    "gtbets": 0.45,  # US market
}


def compute_weighted_consensus(odds_by_book: dict) -> dict:
    """
    Compute bookmaker-weighted consensus probabilities.

    Sharp books count MORE than recreational books.
    """
    features = {}

    weighted_sum_home = 0
    weight_sum = 0
    all_probs_home = []

    for bookmaker, odds in odds_by_book.items():
        prob_home = 1 / odds["odds_home"]
        all_probs_home.append(prob_home)

        weight = BOOKMAKER_WEIGHTS.get(bookmaker, 0.50)
        weighted_sum_home += prob_home * weight
        weight_sum += weight

    # Weighted consensus (sharps count more)
    features["weighted_consensus_home"] = (
        weighted_sum_home / weight_sum if weight_sum > 0 else 0.33
    )

    # Simple average
    avg_prob = np.mean(all_probs_home) if all_probs_home else 0.33

    # Pinnacle vs average
    pinn_prob = 1 / odds_by_book.get("pinnacle", {}).get("odds_home", 3.0)
    features["pinnacle_weight"] = pinn_prob / avg_prob if avg_prob > 0 else 1.0

    # Max-min spread (market disagreement)
    if all_probs_home:
        features["max_min_spread"] = max(all_probs_home) - min(all_probs_home)
    else:
        features["max_min_spread"] = 0

    return features
```

---

##### Summary: Market Structure Features

| Category                     | Count | Key Insight                        |
| ---------------------------- | ----- | ---------------------------------- |
| **Sharp vs Soft Separation** | 10    | Different bookmaker types disagree |
| **League Efficiency**        | 12    | Market quality varies by league    |
| **Bookmaker Weighting**      | 6     | Weight sharp opinions higher       |

**Total: 28 market structure features**

**Why This Is Critical:**

```
Your Current Approach:
    All bookmakers treated equally
    All leagues treated equally

Syndicate Approach:
    Sharp books = reference price (weight 1.0)
    Soft books = follow sharps with lag (weight 0.5)
    EPL = efficient (small edge, high confidence)
    Moldova = inefficient (large edge, lower confidence)
```

**The Key Insight:**

- In Tier 1 leagues (EPL), beat the closing line by 1-2% = good
- In Tier 5 leagues (Moldova), beat by 5%+ = achievable but noisier
- Model must learn these different priors

---

#### 3.1.6 FootyStats Potentials (6 features)

| Feature                            | Type | Description                |
| ---------------------------------- | ---- | -------------------------- |
| `o05_potential` to `o45_potential` | int  | Over X.5 potential (0-100) |
| `btts_potential`                   | int  | BTTS potential (0-100)     |

---

### 3.2 Team Performance - Rolling Features (60)

**This is the core of historical features. Each stat is computed for multiple windows.**

#### 3.2.1 xG Features - By Window (16 features)

| Feature           | Window | Description                         |
| ----------------- | ------ | ----------------------------------- |
| `home_xg_last1`   | Last 1 | Home team xG last game (home only)  |
| `home_xg_last3`   | Last 3 | Home team avg xG last 3 (home only) |
| `home_xg_last5`   | Last 5 | Home team avg xG last 5 (home only) |
| `home_xg_season`  | Season | Home team season avg xG (home only) |
| `away_xg_last1`   | Last 1 | Away team xG last game (away only)  |
| `away_xg_last3`   | Last 3 | Away team avg xG last 3 (away only) |
| `away_xg_last5`   | Last 5 | Away team avg xG last 5 (away only) |
| `away_xg_season`  | Season | Away team season avg xG (away only) |
| `home_xga_last1`  | Last 1 | Home team xGA last game             |
| `home_xga_last3`  | Last 3 | Home team avg xGA last 3            |
| `home_xga_last5`  | Last 5 | Home team avg xGA last 5            |
| `home_xga_season` | Season | Home team season avg xGA            |
| `away_xga_last1`  | Last 1 | Away team xGA last game             |
| `away_xga_last3`  | Last 3 | Away team avg xGA last 3            |
| `away_xga_last5`  | Last 5 | Away team avg xGA last 5            |
| `away_xga_season` | Season | Away team season avg xGA            |

#### 3.2.2 Goals Features - By Window (16 features)

| Feature                      | Window | Description                |
| ---------------------------- | ------ | -------------------------- |
| `home_goals_last1`           | Last 1 | Home team goals last game  |
| `home_goals_last3`           | Last 3 | Home team avg goals last 3 |
| `home_goals_last5`           | Last 5 | Home team avg goals last 5 |
| `home_goals_season`          | Season | Home team season avg goals |
| `away_goals_last1`           | Last 1 | Away team goals last game  |
| `away_goals_last3`           | Last 3 | Away team avg goals last 3 |
| `away_goals_last5`           | Last 5 | Away team avg goals last 5 |
| `away_goals_season`          | Season | Away team season avg goals |
| `home_goals_conceded_last1`  | Last 1 | Conceded last game         |
| `home_goals_conceded_last3`  | Last 3 | Avg conceded last 3        |
| `home_goals_conceded_last5`  | Last 5 | Avg conceded last 5        |
| `home_goals_conceded_season` | Season | Season avg conceded        |
| `away_goals_conceded_last1`  | Last 1 | Conceded last game         |
| `away_goals_conceded_last3`  | Last 3 | Avg conceded last 3        |
| `away_goals_conceded_last5`  | Last 5 | Avg conceded last 5        |
| `away_goals_conceded_season` | Season | Season avg conceded        |

#### 3.2.3 Possession Features - By Window (8 features)

**Source:** Soccerfootball.info, API-Football

| Feature                  | Window | Description                    |
| ------------------------ | ------ | ------------------------------ |
| `home_possession_last1`  | Last 1 | Home team possession last game |
| `home_possession_last3`  | Last 3 | Avg possession last 3 games    |
| `home_possession_last5`  | Last 5 | Avg possession last 5 games    |
| `home_possession_season` | Season | Season avg possession          |
| `away_possession_last1`  | Last 1 | Away team possession last game |
| `away_possession_last3`  | Last 3 | Avg possession last 3 games    |
| `away_possession_last5`  | Last 5 | Avg possession last 5 games    |
| `away_possession_season` | Season | Season avg possession          |

#### 3.2.4 Shots & Accuracy - By Window (16 features)

| Feature                      | Window | Description            |
| ---------------------------- | ------ | ---------------------- |
| `home_shots_last1`           | Last 1 | Shots last game        |
| `home_shots_last3`           | Last 3 | Avg shots last 3       |
| `home_shots_last5`           | Last 5 | Avg shots last 5       |
| `home_shots_season`          | Season | Season avg shots       |
| `away_shots_last1`           | Last 1 | Shots last game        |
| `away_shots_last3`           | Last 3 | Avg shots last 3       |
| `away_shots_last5`           | Last 5 | Avg shots last 5       |
| `away_shots_season`          | Season | Season avg shots       |
| `home_sot_pct_last5`         | Last 5 | Shot accuracy % last 5 |
| `home_sot_pct_season`        | Season | Season shot accuracy   |
| `away_sot_pct_last5`         | Last 5 | Shot accuracy % last 5 |
| `away_sot_pct_season`        | Season | Season shot accuracy   |
| `home_shots_conceded_last5`  | Last 5 | Shots against last 5   |
| `home_shots_conceded_season` | Season | Shots against season   |
| `away_shots_conceded_last5`  | Last 5 | Shots against last 5   |
| `away_shots_conceded_season` | Season | Shots against season   |

#### 3.2.5 Form (Results) Features (8 features)

| Feature            | Type  | Description            |
| ------------------ | ----- | ---------------------- |
| `home_ppg_last3`   | float | Points per game last 3 |
| `home_ppg_last5`   | float | Points per game last 5 |
| `home_ppg_season`  | float | Season PPG             |
| `away_ppg_last3`   | float | Points per game last 3 |
| `away_ppg_last5`   | float | Points per game last 5 |
| `away_ppg_season`  | float | Season PPG             |
| `home_form_string` | str   | Last 5 results "WWDLW" |
| `away_form_string` | str   | Last 5 results "LDWWD" |

---

### 3.3 Head-to-Head (H2H) Historical Features (20)

**Source:** API-Football, derived from fixture history

These features capture the historical matchup between the two specific teams.

| Feature                   | Type  | Description                   |
| ------------------------- | ----- | ----------------------------- |
| `h2h_matches_total`       | int   | Total H2H matches in history  |
| `h2h_matches_last5y`      | int   | H2H matches last 5 years      |
| `h2h_home_wins`           | int   | Home team H2H wins (all time) |
| `h2h_away_wins`           | int   | Away team H2H wins (all time) |
| `h2h_draws`               | int   | H2H draws (all time)          |
| `h2h_home_win_pct`        | float | Home team H2H win %           |
| `h2h_goals_home_avg`      | float | Avg goals by home team in H2H |
| `h2h_goals_away_avg`      | float | Avg goals by away team in H2H |
| `h2h_total_goals_avg`     | float | Avg total goals in H2H        |
| `h2h_btts_pct`            | float | BTTS % in H2H                 |
| `h2h_over25_pct`          | float | Over 2.5 % in H2H             |
| `h2h_xg_home_avg`         | float | Avg xG by home team in H2H    |
| `h2h_xg_away_avg`         | float | Avg xG by away team in H2H    |
| `h2h_last_result`         | str   | Last H2H result (H/D/A)       |
| `h2h_last_score_home`     | int   | Home team goals in last H2H   |
| `h2h_last_score_away`     | int   | Away team goals in last H2H   |
| `h2h_home_at_venue_wins`  | int   | Home team wins at THIS venue  |
| `h2h_days_since_last`     | int   | Days since last H2H meeting   |
| `h2h_possession_home_avg` | float | Avg possession home in H2H    |
| `h2h_possession_away_avg` | float | Avg possession away in H2H    |

```python
def compute_h2h_features(
    home_team_id: int, away_team_id: int, prediction_time: datetime
) -> dict:
    """
    Compute head-to-head features between two teams.

    Only uses matches with kickoff < prediction_time (anti-leakage).
    """
    # Get all H2H matches
    h2h_matches = fixtures_df[
        (
            (fixtures_df["home_team_id"] == home_team_id)
            & (fixtures_df["away_team_id"] == away_team_id)
        )
        | (
            (fixtures_df["home_team_id"] == away_team_id)
            & (fixtures_df["away_team_id"] == home_team_id)
        )
    ]

    # Filter to matches before prediction time
    h2h_matches = h2h_matches[h2h_matches["kickoff_utc"] < prediction_time]

    # Filter to matches where home_team_id is actually at home
    h2h_home_matches = h2h_matches[h2h_matches["home_team_id"] == home_team_id]

    features = {}
    features["h2h_matches_total"] = len(h2h_matches)
    features["h2h_matches_last5y"] = len(
        h2h_matches[
            h2h_matches["kickoff_utc"] > prediction_time - timedelta(days=5 * 365)
        ]
    )

    if len(h2h_home_matches) > 0:
        features["h2h_home_wins"] = len(
            h2h_home_matches[h2h_home_matches["winner_team_id"] == home_team_id]
        )
        features["h2h_away_wins"] = len(
            h2h_home_matches[h2h_home_matches["winner_team_id"] == away_team_id]
        )
        features["h2h_draws"] = len(
            h2h_home_matches[h2h_home_matches["winner_team_id"].isna()]
        )
        features["h2h_home_win_pct"] = features["h2h_home_wins"] / len(h2h_home_matches)
        features["h2h_goals_home_avg"] = h2h_home_matches["home_score"].mean()
        features["h2h_goals_away_avg"] = h2h_home_matches["away_score"].mean()
        features["h2h_total_goals_avg"] = (
            h2h_home_matches["home_score"] + h2h_home_matches["away_score"]
        ).mean()
        # ... etc
    else:
        # Fill with league averages if no H2H history
        features["h2h_home_win_pct"] = 0.45  # League avg
        # ... etc

    return features
```

---

### 3.4 Previous Game Features (12)

**Purpose:** Capture the immediate last game's detailed stats (not just rolling averages).

| Feature                       | Type  | Description              |
| ----------------------------- | ----- | ------------------------ |
| `home_prev_opponent_strength` | float | Elo of last opponent     |
| `home_prev_was_home`          | int   | 1 if last game was home  |
| `home_prev_result`            | str   | W/D/L of last game       |
| `home_prev_goals_scored`      | int   | Goals scored last game   |
| `home_prev_goals_conceded`    | int   | Goals conceded last game |
| `home_prev_xg`                | float | xG last game             |
| `away_prev_opponent_strength` | float | Elo of last opponent     |
| `away_prev_was_home`          | int   | 1 if last game was home  |
| `away_prev_result`            | str   | W/D/L of last game       |
| `away_prev_goals_scored`      | int   | Goals scored last game   |
| `away_prev_goals_conceded`    | int   | Goals conceded last game |
| `away_prev_xg`                | float | xG last game             |

---

### 3.5 Lineup/Player Features (69)

#### 3.5.0 Lineup Availability Strategy

**Data Source:** API-Football is our primary source for lineup data.

**When Lineups Are Available:**

| Time          | Lineup Status         | Typical Availability             |
| ------------- | --------------------- | -------------------------------- |
| T-24h         | Not confirmed         | ~5% of matches have predicted XI |
| T-6h          | Not confirmed         | ~10%                             |
| T-2h          | Sometimes             | ~30% (manager press conferences) |
| **T-1h**      | **Usually confirmed** | **~85% of matches**              |
| T-30m         | Confirmed             | ~95%                             |
| T-0 (kickoff) | Confirmed             | 100%                             |

**Schema for Tracking:**

```python
# In FixtureLineup table
lineup_type = Column(String)  # 'expected' or 'confirmed'
announced_at_utc = Column(DateTime)  # When lineup was published
source = Column(String)  # 'api_football', 'news_scrape', 'predicted'
```

**Feature Availability by Prediction Time:**

| Prediction Time | Lineup Features Available? | Strategy              |
| --------------- | -------------------------- | --------------------- |
| **T-24h**       | NO (usually)               | Use FALLBACK features |
| **T-1h**        | YES (usually)              | Use confirmed XI      |

#### Fallback Strategy When Lineup NOT Available

```python
def compute_lineup_features_with_fallback(
    fixture_id: int,
    prediction_time: datetime,
    lineup_type: str,  # 'expected' or 'confirmed'
) -> dict:
    """
    Compute lineup features with fallback when lineup unavailable.
    """
    features = {}

    # Try to get lineup
    lineup = get_lineup(fixture_id, lineup_type)
    lineup_available = (
        lineup is not None and lineup["announced_at_utc"] <= prediction_time
    )

    # FLAG: Did we have lineup data?
    features["lineup_available"] = 1 if lineup_available else 0

    if lineup_available:
        # ========== CONFIRMED LINEUP PATH ==========
        home_xi = lineup["home"]["startXI"]
        away_xi = lineup["away"]["startXI"]

        # Compute actual XI features
        features.update(compute_xi_strength(home_xi, away_xi))
        features.update(compute_defensive_aggregates(home_xi, away_xi))

    else:
        # ========== FALLBACK PATH ==========
        # Use PREDICTED XI or TEAM AVERAGES

        home_team, away_team = get_teams(fixture_id)

        # Option 1: Use most likely XI (based on last 5 lineups)
        predicted_home_xi = predict_likely_xi(home_team, prediction_time)
        predicted_away_xi = predict_likely_xi(away_team, prediction_time)

        if predicted_home_xi:
            features.update(compute_xi_strength(predicted_home_xi, predicted_away_xi))
            features["lineup_source"] = "predicted"
        else:
            # Option 2: Use team-level averages (no player granularity)
            features.update(
                compute_team_level_fallback(home_team, away_team, prediction_time)
            )
            features["lineup_source"] = "team_avg"

    return features


def predict_likely_xi(team_id: int, prediction_time: datetime) -> list:
    """
    Predict most likely starting XI based on recent patterns.

    Logic:
    1. Get last 5 starting XIs
    2. Exclude known injured players
    3. Rank by frequency of starts
    4. Pick top 11 by position
    """
    # Get recent lineups
    recent_lineups = get_recent_lineups(team_id, n=5, before=prediction_time)

    if len(recent_lineups) == 0:
        return None

    # Count starts per player
    player_starts = Counter()
    for lineup in recent_lineups:
        for player_id in lineup["startXI"]:
            player_starts[player_id] += 1

    # Get current injuries
    injured = get_current_injuries(team_id, prediction_time)

    # Remove injured players
    for player_id in injured:
        player_starts.pop(player_id, None)

    # Get player positions
    players_with_pos = []
    for player_id, starts in player_starts.items():
        position = get_player_position(player_id)
        players_with_pos.append(
            {"player_id": player_id, "position": position, "starts": starts}
        )

    # Select XI by position (1 GK, 4 DEF, 3-4 MID, 2-3 FWD)
    predicted_xi = select_balanced_xi(players_with_pos)

    return predicted_xi


def compute_team_level_fallback(
    home_team: int, away_team: int, prediction_time: datetime
) -> dict:
    """
    Fallback features when no lineup available at all.
    Uses team-level aggregates instead of player-level.
    """
    features = {}

    # Use team's average squad value (not XI-specific)
    home_squad = get_squad_data(home_team, prediction_time)
    away_squad = get_squad_data(away_team, prediction_time)

    features["home_squad_avg_value"] = home_squad["avg_player_value"]
    features["away_squad_avg_value"] = away_squad["avg_player_value"]
    features["home_squad_total_value"] = home_squad["total_value"]
    features["away_squad_total_value"] = away_squad["total_value"]

    # Use team xG/xGA as proxy for quality (already have this)
    # XI-specific features set to NaN or team average
    features["home_xi_total_value"] = home_squad["typical_xi_value"]  # Avg of last 5 XI
    features["away_xi_total_value"] = away_squad["typical_xi_value"]

    return features
```

#### Historical Predicted Lineups (Backtesting)

**Q: Can we get historical predicted lineups?**
**A: No reliable external source exists.** Services like WhoScored/FotMob show "expected XI" but:

- Not consistently archived
- Often inaccurate
- Would require scraping (legal/reliability issues)

**Our approach: Reconstruct predicted XI from our own data:**

```python
def get_lineup_for_backtesting(
    fixture_id: int,
    prediction_time: datetime,  # T-24h or T-1h
    actual_kickoff: datetime,
) -> dict:
    """
    For BACKTESTING: Simulate what lineup data would have been available.

    Key insight: We HAVE historical lineups (the actual ones that played).
    We use these to RECONSTRUCT what a predicted XI would have been.
    """
    hours_before = (actual_kickoff - prediction_time).total_seconds() / 3600

    if hours_before > 2:  # T-24h, T-6h, etc.
        # Lineup was NOT available → use predicted XI
        team_ids = get_fixture_teams(fixture_id)

        # Predict XI using data available at prediction_time
        home_predicted = predict_likely_xi(
            team_ids["home"], prediction_time  # Only use lineups from BEFORE this time
        )
        away_predicted = predict_likely_xi(team_ids["away"], prediction_time)

        return {
            "home_xi": home_predicted,
            "away_xi": away_predicted,
            "lineup_available": 0,
            "lineup_source": "predicted",
        }

    else:  # T-1h or closer
        # Lineup WAS available → use actual lineup
        actual_lineup = get_actual_lineup(fixture_id)

        return {
            "home_xi": actual_lineup["home"]["startXI"],
            "away_xi": actual_lineup["away"]["startXI"],
            "lineup_available": 1,
            "lineup_source": "confirmed",
        }
```

**For backtesting at T-24h:**

1. Use `predict_likely_xi()` based on last 5 lineups (before prediction_time)
2. Exclude players injured at prediction_time
3. This simulates what we would have predicted in real-time

**For backtesting at T-1h:**

1. Use actual lineup (we have this historically)
2. Assume it was available ~1h before kickoff (realistic assumption)

---

#### Key Feature: `lineup_available`

**Always include this binary flag:**

| Feature            | Type | Description                                      |
| ------------------ | ---- | ------------------------------------------------ |
| `lineup_available` | int  | 1 if confirmed XI available, 0 if using fallback |
| `lineup_source`    | str  | 'confirmed', 'predicted', 'team_avg'             |

**Why this matters:**

- Model can learn to weight lineup features differently based on confidence
- At T-24h: Most lineup features are predicted → lower weight
- At T-1h: Most lineup features are confirmed → higher weight

---

#### 3.5.1 XI Strength (8 features)

| Feature               | Type  | Description                     |
| --------------------- | ----- | ------------------------------- |
| `home_xi_total_value` | float | Total market value of XI (EUR)  |
| `away_xi_total_value` | float | Total market value of XI        |
| `home_xi_avg_value`   | float | Avg player value in XI          |
| `away_xi_avg_value`   | float | Avg player value in XI          |
| `home_xi_avg_rating`  | float | Avg season rating of XI         |
| `away_xi_avg_rating`  | float | Avg season rating of XI         |
| `xi_value_ratio`      | float | home_xi_value / away_xi_value   |
| `xi_rating_diff`      | float | home_xi_rating - away_xi_rating |

#### 3.5.2 Key Absentees (6 features)

| Feature                     | Type  | Description                       |
| --------------------------- | ----- | --------------------------------- |
| `home_key_absentees_count`  | int   | # of top-5 minute players missing |
| `away_key_absentees_count`  | int   | # of top-5 minute players missing |
| `home_value_lost_to_injury` | float | EUR value of injured              |
| `away_value_lost_to_injury` | float | EUR value of injured              |
| `home_attack_value_missing` | float | Value of missing attackers        |
| `away_attack_value_missing` | float | Value of missing attackers        |

#### 3.5.3 Formation & Stability (4 features)

| Feature             | Type  | Description                   |
| ------------------- | ----- | ----------------------------- |
| `home_formation`    | str   | Formation (e.g., "4-3-3")     |
| `away_formation`    | str   | Formation                     |
| `home_xi_stability` | float | Overlap with last 5 XIs (0-1) |
| `away_xi_stability` | float | Overlap with last 5 XIs       |

#### 3.5.4 Player Offensive Aggregates (7 features)

| Feature                  | Type  | Description                           |
| ------------------------ | ----- | ------------------------------------- |
| `home_xi_goals_season`   | int   | Total goals by XI players this season |
| `home_xi_assists_season` | int   | Total assists by XI players           |
| `away_xi_goals_season`   | int   | Total goals by XI players             |
| `away_xi_assists_season` | int   | Total goals by XI players             |
| `home_xi_xg_per90_avg`   | float | Avg xG per 90 of XI players           |
| `away_xi_xg_per90_avg`   | float | Avg xG per 90 of XI players           |
| `home_xi_avg_age`        | float | Avg age of starting XI                |

#### 3.5.5 Player DEFENSIVE Aggregates (12 features)

**Source:** API-Football player stats, Transfermarkt

| Feature                           | Type  | Description                   |
| --------------------------------- | ----- | ----------------------------- |
| `home_xi_tackles_per90_avg`       | float | Avg tackles per 90 of XI      |
| `away_xi_tackles_per90_avg`       | float | Avg tackles per 90 of XI      |
| `home_xi_interceptions_per90_avg` | float | Avg interceptions per 90      |
| `away_xi_interceptions_per90_avg` | float | Avg interceptions per 90      |
| `home_xi_blocks_per90_avg`        | float | Avg blocks per 90             |
| `away_xi_blocks_per90_avg`        | float | Avg blocks per 90             |
| `home_xi_clearances_per90_avg`    | float | Avg clearances per 90         |
| `away_xi_clearances_per90_avg`    | float | Avg clearances per 90         |
| `home_xi_aerial_won_pct`          | float | Aerial duels won %            |
| `away_xi_aerial_won_pct`          | float | Aerial duels won %            |
| `home_def_avg_height_cm`          | float | Avg height of defenders in XI |
| `away_def_avg_height_cm`          | float | Avg height of defenders in XI |

**Implementation:**

```python
def compute_defensive_player_aggregates(
    player_ids: list, prediction_time: datetime
) -> dict:
    """
    Aggregate defensive stats for starting XI.

    Uses per-90 stats to normalize for playing time.
    """
    player_stats = get_player_season_stats(player_ids, prediction_time)

    features = {}

    # Defensive actions (per 90 to normalize)
    features["xi_tackles_per90_avg"] = player_stats["tackles_per90"].mean()
    features["xi_interceptions_per90_avg"] = player_stats["interceptions_per90"].mean()
    features["xi_blocks_per90_avg"] = player_stats["blocks_per90"].mean()
    features["xi_clearances_per90_avg"] = player_stats["clearances_per90"].mean()

    # Aerial duels
    total_aerial = player_stats["aerial_total"].sum()
    won_aerial = player_stats["aerial_won"].sum()
    features["xi_aerial_won_pct"] = won_aerial / max(total_aerial, 1)

    # Defender height (for set piece defense)
    defenders = player_stats[
        player_stats["position"].isin(["CB", "LB", "RB", "LWB", "RWB"])
    ]
    if len(defenders) > 0:
        features["def_avg_height_cm"] = defenders["height_cm"].mean()
    else:
        features["def_avg_height_cm"] = 180  # League avg default

    return features
```

**Why Defensive Stats Matter:**

- Teams with strong tacklers can disrupt opposition xG
- Aerial dominance affects set-piece outcomes
- Tall defenders reduce corner/free-kick goals
- Interceptions correlate with pressing style

---

#### 3.5.6 Position-Level Features (16 features)

**Q: When a starter is injured, how do we know who replaces them?**

**Problem with pure aggregation:** If Haaland is out, "total XI value dropped" doesn't tell you:

- Is the backup striker any good?
- Will they change formation instead?
- How much attacking quality is specifically lost?

**Solution: Track quality BY POSITION LINE**

| Feature                | Type  | Description             |
| ---------------------- | ----- | ----------------------- |
| `home_gk_rating`       | float | GK rating/value         |
| `away_gk_rating`       | float | GK rating/value         |
| `home_def_line_rating` | float | Avg rating of DEF in XI |
| `away_def_line_rating` | float | Avg rating of DEF in XI |
| `home_mid_line_rating` | float | Avg rating of MID in XI |
| `away_mid_line_rating` | float | Avg rating of MID in XI |
| `home_fwd_line_rating` | float | Avg rating of FWD in XI |
| `away_fwd_line_rating` | float | Avg rating of FWD in XI |
| `home_def_line_value`  | float | Total value of DEF line |
| `away_def_line_value`  | float | Total value of DEF line |
| `home_mid_line_value`  | float | Total value of MID line |
| `away_mid_line_value`  | float | Total value of MID line |
| `home_fwd_line_value`  | float | Total value of FWD line |
| `away_fwd_line_value`  | float | Total value of FWD line |
| `home_fwd_xg_per90`    | float | FWD line avg xG/90      |
| `away_fwd_xg_per90`    | float | FWD line avg xG/90      |

**Position Mapping (from API-Football `pos` field):**

```python
POSITION_GROUPS = {
    "GK": ["G"],
    "DEF": ["D"],  # Includes CB, LB, RB, LWB, RWB
    "MID": ["M"],  # Includes CDM, CM, CAM, LM, RM
    "FWD": ["F"],  # Includes ST, CF, LW, RW
}

# For more granular analysis (from player.grid or detailed pos)
DETAILED_POSITIONS = {
    "GK": ["GK"],
    "CB": ["CB"],
    "FB": ["LB", "RB", "LWB", "RWB"],  # Full-backs
    "DM": ["CDM", "DM"],
    "CM": ["CM", "LM", "RM"],
    "AM": ["CAM", "AM"],
    "WG": ["LW", "RW"],
    "ST": ["ST", "CF"],
}
```

**Implementation:**

```python
def compute_position_line_features(xi_players: list, prediction_time: datetime) -> dict:
    """
    Compute quality metrics by position line (DEF, MID, FWD).
    """
    features = {}
    player_stats = get_player_season_stats(
        [p["id"] for p in xi_players], prediction_time
    )

    # Group by position
    gk = player_stats[player_stats["position"] == "G"]
    defenders = player_stats[player_stats["position"] == "D"]
    midfielders = player_stats[player_stats["position"] == "M"]
    forwards = player_stats[player_stats["position"] == "F"]

    # GK (single player)
    features["gk_rating"] = gk["rating"].mean() if len(gk) > 0 else 6.5
    features["gk_saves_pct"] = gk["saves_pct"].mean() if len(gk) > 0 else 0.7

    # DEF line
    features["def_line_rating"] = (
        defenders["rating"].mean() if len(defenders) > 0 else 6.5
    )
    features["def_line_value"] = (
        defenders["market_value"].sum() if len(defenders) > 0 else 0
    )
    features["def_line_count"] = len(defenders)

    # MID line
    features["mid_line_rating"] = (
        midfielders["rating"].mean() if len(midfielders) > 0 else 6.5
    )
    features["mid_line_value"] = (
        midfielders["market_value"].sum() if len(midfielders) > 0 else 0
    )
    features["mid_line_xg_per90"] = (
        midfielders["xg_per90"].mean() if len(midfielders) > 0 else 0.1
    )

    # FWD line (most important for xG prediction)
    features["fwd_line_rating"] = (
        forwards["rating"].mean() if len(forwards) > 0 else 6.5
    )
    features["fwd_line_value"] = (
        forwards["market_value"].sum() if len(forwards) > 0 else 0
    )
    features["fwd_line_xg_per90"] = (
        forwards["xg_per90"].mean() if len(forwards) > 0 else 0.3
    )
    features["fwd_line_goals_season"] = (
        forwards["goals_season"].sum() if len(forwards) > 0 else 0
    )

    return features
```

---

#### 3.5.7 Depth Chart & Key Player Features (12 features)

**What Pros Do:**

1. Track who's the #1, #2, #3 at each position
2. Model quality drop when #1 is out
3. Identify "irreplaceable" players (no good backup)

| Feature                    | Type  | Description                             |
| -------------------------- | ----- | --------------------------------------- |
| `home_top_scorer_in_xi`    | int   | 1 if team's top scorer is starting      |
| `away_top_scorer_in_xi`    | int   | 1 if team's top scorer is starting      |
| `home_top_assister_in_xi`  | int   | 1 if team's top assister is starting    |
| `away_top_assister_in_xi`  | int   | 1 if team's top assister is starting    |
| `home_top_xg_player_in_xi` | int   | 1 if highest xG player is starting      |
| `away_top_xg_player_in_xi` | int   | 1 if highest xG player is starting      |
| `home_fwd_quality_drop`    | float | Rating drop from typical FWD line       |
| `away_fwd_quality_drop`    | float | Rating drop from typical FWD line       |
| `home_def_quality_drop`    | float | Rating drop from typical DEF line       |
| `away_def_quality_drop`    | float | Rating drop from typical DEF line       |
| `home_key_players_missing` | int   | Count of top-5 minute players not in XI |
| `away_key_players_missing` | int   | Count of top-5 minute players not in XI |

**Building a Depth Chart:**

```python
def build_depth_chart(team_id: int, prediction_time: datetime) -> dict:
    """
    Build depth chart by position based on historical lineups.

    Returns dict of position -> [player_id ranked by starts].
    """
    # Get all lineups from this season
    season_lineups = get_season_lineups(team_id, before=prediction_time)

    # Count starts by player and position
    position_starts = defaultdict(lambda: Counter())

    for lineup in season_lineups:
        for player in lineup["startXI"]:
            pos = player["pos"]  # G, D, M, F
            position_starts[pos][player["id"]] += 1

    # Rank players by starts at each position
    depth_chart = {}
    for pos, player_counts in position_starts.items():
        # Sort by starts (descending)
        ranked = sorted(player_counts.items(), key=lambda x: x[1], reverse=True)
        depth_chart[pos] = [player_id for player_id, _ in ranked]

    return depth_chart


def compute_quality_drop(
    current_xi: list,
    depth_chart: dict,
    player_ratings: dict,
    position: str,  # 'F' for forwards
) -> float:
    """
    Compute quality drop at a position vs typical starters.

    If backup striker is playing instead of #1, how much rating is lost?
    """
    typical_starters = depth_chart.get(position, [])[:3]  # Top 3 at position
    current_at_pos = [p for p in current_xi if p["pos"] == position]

    if not typical_starters or not current_at_pos:
        return 0.0

    # Typical rating (avg of usual starters)
    typical_rating = np.mean([player_ratings.get(p, 6.5) for p in typical_starters])

    # Current rating
    current_rating = np.mean([player_ratings.get(p["id"], 6.5) for p in current_at_pos])

    # Quality drop (positive = weaker than usual)
    return typical_rating - current_rating


def predict_replacement(
    injured_player_id: int, team_id: int, prediction_time: datetime, depth_chart: dict
) -> dict:
    """
    Predict who replaces an injured player.

    Returns:
        - Likely replacement player
        - Quality drop estimate
        - Formation change probability
    """
    injured_pos = get_player_position(injured_player_id)
    injured_rating = get_player_rating(injured_player_id)

    # Get depth chart for that position
    pos_depth = depth_chart.get(injured_pos, [])

    # Find injured player's rank and get next in line
    if injured_player_id in pos_depth:
        rank = pos_depth.index(injured_player_id)
        if rank + 1 < len(pos_depth):
            replacement_id = pos_depth[rank + 1]
            replacement_rating = get_player_rating(replacement_id)

            return {
                "replacement_id": replacement_id,
                "quality_drop": injured_rating - replacement_rating,
                "formation_change_prob": 0.1,  # Low if direct replacement available
            }

    # No clear replacement → formation change likely
    return {
        "replacement_id": None,
        "quality_drop": injured_rating - 6.0,  # Assume avg replacement
        "formation_change_prob": 0.6,  # Higher if no backup at position
    }
```

---

#### 3.5.8 Formation Intelligence (4 features)

**When star striker is out, manager might:**

1. Play backup striker (direct replacement)
2. Change formation (4-3-3 → 4-5-1)
3. Use a midfielder as "false 9"

| Feature                        | Type  | Description                      |
| ------------------------------ | ----- | -------------------------------- |
| `formation_home`               | str   | Formation string (e.g., "4-3-3") |
| `formation_away`               | str   | Formation string                 |
| `formation_attacking_ratio`    | float | FWD count / DEF count            |
| `formation_differs_from_usual` | int   | 1 if not the typical formation   |

**Tracking Formation Tendencies:**

```python
def get_formation_tendency(team_id: int, prediction_time: datetime) -> dict:
    """
    Get team's typical formation and variation.
    """
    recent_lineups = get_recent_lineups(team_id, n=10, before=prediction_time)

    formation_counts = Counter(l["formation"] for l in recent_lineups)
    most_common = (
        formation_counts.most_common(1)[0] if formation_counts else ("4-4-2", 5)
    )

    return {
        "typical_formation": most_common[0],
        "formation_consistency": most_common[1]
        / len(recent_lineups),  # How often they use it
        "formations_used": list(formation_counts.keys()),
    }


def formation_attacking_ratio(formation: str) -> float:
    """
    Compute attacking vs defensive ratio from formation string.

    "4-3-3" → 3 FWD / 4 DEF = 0.75
    "5-4-1" → 1 FWD / 5 DEF = 0.20
    """
    parts = formation.split("-")
    if len(parts) >= 2:
        defenders = int(parts[0])
        forwards = int(parts[-1])
        return forwards / max(defenders, 1)
    return 0.5
```

---

#### Summary: Position-Level Approach

**What we now track:**

| Level             | Features                 | Purpose                        |
| ----------------- | ------------------------ | ------------------------------ |
| **XI Total**      | Total value, avg rating  | Overall squad strength         |
| **Position Line** | DEF/MID/FWD ratings      | Where is quality concentrated? |
| **Key Players**   | Top scorer in XI?        | Irreplaceable player impact    |
| **Depth Chart**   | Quality drop at position | Backup quality assessment      |
| **Formation**     | 4-3-3 vs 5-4-1           | Tactical intent                |

**Backtesting Predicted XI with Position Awareness:**

```python
def predict_likely_xi_position_aware(team_id: int, prediction_time: datetime) -> list:
    """
    Predict XI using depth chart + injuries.

    For each position:
    1. Get depth chart (ranked by starts)
    2. Remove injured players
    3. Pick available #1 at each position
    4. Adjust for formation tendency
    """
    depth_chart = build_depth_chart(team_id, prediction_time)
    injured = get_current_injuries(team_id, prediction_time)
    formation_info = get_formation_tendency(team_id, prediction_time)

    predicted_xi = []

    # Parse typical formation for position counts
    formation = formation_info["typical_formation"]
    pos_counts = parse_formation(formation)  # {'G': 1, 'D': 4, 'M': 3, 'F': 3}

    for position, needed in pos_counts.items():
        available = [p for p in depth_chart.get(position, []) if p not in injured]

        # Take top N available at this position
        selected = available[:needed]
        predicted_xi.extend([{"id": p, "pos": position} for p in selected])

    return predicted_xi
```

---

### 3.6 Context Features (81)

#### 3.6.1 Referee Features - Basic (6)

| Feature                  | Description             |
| ------------------------ | ----------------------- |
| `referee_id`             | Referee identifier      |
| `referee_avg_cards`      | Avg cards per match     |
| `referee_avg_fouls`      | Avg fouls per match     |
| `referee_avg_penalties`  | Avg penalties per match |
| `referee_home_bias`      | Home win rate deviation |
| `referee_card_rate_band` | low/medium/high         |

#### 3.6.2 Referee-Team Interactions (22 features) 🔥

**Why This Is A Goldmine:**

- Some teams get more cards from specific referees
- Some refs have historical bias toward/against certain teams
- Team attacking style × referee penalty propensity = predictive

---

##### 3.6.2.1 Team-Specific Card Patterns Under Referee (8 features)

| Feature                        | Type  | Description                            |
| ------------------------------ | ----- | -------------------------------------- |
| `home_cards_under_referee`     | float | Avg cards home team gets from this ref |
| `away_cards_under_referee`     | float | Avg cards away team gets from this ref |
| `home_cards_vs_ref_avg`        | float | Team cards - ref's avg cards           |
| `away_cards_vs_ref_avg`        | float | Team cards - ref's avg cards           |
| `home_red_risk_with_ref`       | float | Red card rate with this ref            |
| `away_red_risk_with_ref`       | float | Red card rate with this ref            |
| `ref_team_card_chemistry_home` | float | Composite card interaction score       |
| `ref_team_card_chemistry_away` | float | Composite card interaction score       |

```python
def compute_team_ref_card_history(
    team_id: int, referee_id: int, prediction_time: datetime
) -> dict:
    """
    Compute historical card patterns between team and referee.
    """
    features = {}

    # Get matches where this team played with this referee
    matches = get_team_matches_with_referee(team_id, referee_id, before=prediction_time)

    if len(matches) < 3:
        # Not enough history - use team average cards
        return default_team_ref_cards(team_id)

    # Avg cards this team gets from this referee
    team_cards = np.mean([m["team_cards"] for m in matches])
    features["cards_under_referee"] = team_cards

    # Compare to referee's overall average
    ref_avg = get_referee_avg_cards(referee_id)
    features["cards_vs_ref_avg"] = team_cards - ref_avg

    # Red card risk
    red_cards = sum(m["team_red_cards"] for m in matches)
    features["red_risk_with_ref"] = red_cards / len(matches)

    # Card chemistry score (positive = more cards than expected)
    team_avg_cards = get_team_avg_cards(team_id)
    expected = (team_avg_cards + ref_avg) / 2
    features["ref_team_card_chemistry"] = team_cards - expected

    return features
```

---

##### 3.6.2.2 Referee Historical Bias Toward Teams (6 features)

| Feature                          | Type  | Description                           |
| -------------------------------- | ----- | ------------------------------------- |
| `ref_home_result_with_home_team` | float | Home team's win rate with this ref    |
| `ref_away_result_with_away_team` | float | Away team's win rate with this ref    |
| `ref_bias_toward_home`           | float | Ref's home win rate - league avg      |
| `ref_historical_favor_home`      | int   | 1 if home team historically favored   |
| `ref_historical_favor_away`      | int   | 1 if away team historically favored   |
| `ref_bias_differential`          | float | Favor toward home - favor toward away |

```python
def compute_referee_team_bias(
    home_id: int, away_id: int, referee_id: int, prediction_time: datetime
) -> dict:
    """
    Compute referee's historical bias toward specific teams.
    """
    features = {}

    # Home team's results with this referee
    home_matches = get_team_matches_with_referee(
        home_id, referee_id, before=prediction_time
    )
    if len(home_matches) >= 3:
        home_wins = sum(1 for m in home_matches if m["result"] == "W")
        home_ppg = sum(m["points"] for m in home_matches) / len(home_matches)
        features["ref_home_result_with_home_team"] = home_ppg

        # Compare to team's average PPG
        team_avg_ppg = get_team_avg_ppg(home_id, prediction_time)
        features["ref_historical_favor_home"] = (
            1 if home_ppg > team_avg_ppg + 0.2 else 0
        )

    # Away team's results with this referee
    away_matches = get_team_matches_with_referee(
        away_id, referee_id, before=prediction_time
    )
    if len(away_matches) >= 3:
        away_ppg = sum(m["points"] for m in away_matches) / len(away_matches)
        features["ref_away_result_with_away_team"] = away_ppg

        team_avg_ppg = get_team_avg_ppg(away_id, prediction_time)
        features["ref_historical_favor_away"] = (
            1 if away_ppg > team_avg_ppg + 0.2 else 0
        )

    # Referee's general home bias
    all_ref_matches = get_referee_matches(referee_id, before=prediction_time)
    home_win_rate = sum(1 for m in all_ref_matches if m["home_win"]) / len(
        all_ref_matches
    )
    league_avg_home = 0.46  # Typical home win rate
    features["ref_bias_toward_home"] = home_win_rate - league_avg_home

    return features
```

---

##### 3.6.2.3 Penalty Propensity × Team Style Interactions (8 features)

| Feature                     | Type  | Description                    |
| --------------------------- | ----- | ------------------------------ |
| `ref_pen_propensity`        | float | Referee penalties per match    |
| `home_pen_box_entries`      | float | Home team entries into pen box |
| `away_pen_box_entries`      | float | Away team entries into pen box |
| `pen_opportunity_home`      | float | ref_pen × home_box_entries     |
| `pen_opportunity_away`      | float | ref_pen × away_box_entries     |
| `home_pen_won_rate`         | float | Home team's pens won per match |
| `away_pen_won_rate`         | float | Away team's pens won per match |
| `pen_differential_expected` | float | Expected pen advantage         |

```python
def compute_penalty_interaction_features(
    home_id: int, away_id: int, referee_id: int, prediction_time: datetime
) -> dict:
    """
    Compute penalty probability based on referee × team style interaction.
    """
    features = {}

    # Referee's penalty propensity
    ref_stats = get_referee_stats(referee_id)
    features["ref_pen_propensity"] = ref_stats["penalties_per_match"]

    # Home team's penalty box entries (from FootyStats/Soccerfootball)
    home_stats = get_team_attacking_stats(home_id, prediction_time, n=10)
    features["home_pen_box_entries"] = home_stats.get("box_entries_per_match", 15)
    features["home_pen_won_rate"] = home_stats.get("penalties_won_per_match", 0.15)

    # Away team's penalty box entries
    away_stats = get_team_attacking_stats(away_id, prediction_time, n=10)
    features["away_pen_box_entries"] = away_stats.get("box_entries_per_match", 15)
    features["away_pen_won_rate"] = away_stats.get("penalties_won_per_match", 0.15)

    # INTERACTION: Pen opportunity = ref propensity × team box entries
    # High press team + penalty-happy ref = more penalties!
    features["pen_opportunity_home"] = (
        features["ref_pen_propensity"]
        * features["home_pen_box_entries"]
        / 15  # Normalized
    )
    features["pen_opportunity_away"] = (
        features["ref_pen_propensity"] * features["away_pen_box_entries"] / 15
    )

    # Expected penalty differential
    features["pen_differential_expected"] = (
        features["pen_opportunity_home"] - features["pen_opportunity_away"]
    )

    return features
```

---

##### 3.6.2.4 Referee Style × Match Intensity Interaction

| Feature                      | Type  | Description                |
| ---------------------------- | ----- | -------------------------- |
| `ref_tolerance_x_team_fouls` | float | ref_card_rate × team_fouls |
| `match_card_risk_score`      | float | Combined card risk         |

```python
def compute_card_risk_score(
    home_id: int, away_id: int, referee_id: int, prediction_time: datetime
) -> dict:
    """
    Compute expected cards based on referee strictness × team fouling tendencies.
    """
    features = {}

    # Referee strictness
    ref_cards_per_foul = get_referee_cards_per_foul(referee_id)  # How quickly they card

    # Team fouling tendencies
    home_fouls = get_team_avg_fouls(home_id, prediction_time)
    away_fouls = get_team_avg_fouls(away_id, prediction_time)

    # Interaction: Strict ref × high-fouling teams = cards galore
    features["ref_tolerance_x_home_fouls"] = ref_cards_per_foul * home_fouls
    features["ref_tolerance_x_away_fouls"] = ref_cards_per_foul * away_fouls

    # Combined match card risk
    features["match_card_risk_score"] = (
        ref_cards_per_foul * (home_fouls + away_fouls) / 2
    )

    return features
```

---

##### Summary: Referee-Team Interaction Features

| Category                 | Count | Key Insight                                  |
| ------------------------ | ----- | -------------------------------------------- |
| **Card Patterns**        | 8     | Teams get more/less cards from specific refs |
| **Historical Bias**      | 6     | Some refs historically favor certain teams   |
| **Penalty Interactions** | 8     | Pen-happy ref × attacking team = more pens   |

**Total: 22 referee-team interaction features**

**Why This Is A Goldmine:**

```
Without Interactions:
    Ref avg cards: 4.2
    Home team avg cards: 2.0
    → Expected home cards: ~2.0

With Interactions:
    This ref has given this team 2.8 cards avg (above team avg!)
    ref_team_card_chemistry = +0.8
    → Expected home cards: ~2.8

    This is predictive edge in cards markets!
```

**Example: Penalty Markets**

```
Referee: Known for penalties (0.4 per match, league avg 0.25)
Home team: Liverpool (high pressing, many box entries)
Away team: Burnley (defensive, few box entries)

pen_opportunity_home = 0.4 × (25/15) = 0.67
pen_opportunity_away = 0.4 × (10/15) = 0.27

→ Liverpool significantly more likely to win a penalty
→ Edge in penalty-related markets
```

---

#### 3.6.3 Weather Features (10)

| Feature              | Description                  |
| -------------------- | ---------------------------- |
| `temperature_c`      | Forecast temp                |
| `wind_speed_kmh`     | Wind speed                   |
| `precipitation_mm`   | Expected rain                |
| `precipitation_prob` | Rain probability             |
| `humidity_pct`       | Humidity                     |
| `cloud_cover_pct`    | Cloud coverage               |
| `temp_band`          | cold/cool/mild/warm          |
| `wind_band`          | calm/medium/windy            |
| `rain_flag`          | 1 if precipitation > 0       |
| `bad_weather_flag`   | 1 if rain>40% OR wind>20km/h |

#### 3.6.4 Schedule, Travel & Fatigue Features (28 features) 🔥

**Why This Matters:**

- 3 games in 8 days → historically ~0.3 xG penalty
- Long-haul travel → significant impact
- Squad depth matters less in minor leagues → fatigue hits harder
- Rest advantage is one of the most underpriced edges

**Data Source:** API-Football fixtures (dates, venues, cities), computed distances

---

##### 3.6.4.1 Basic Rest Features (6)

| Feature           | Type | Description                      |
| ----------------- | ---- | -------------------------------- |
| `home_days_rest`  | int  | Days since home team's last game |
| `away_days_rest`  | int  | Days since away team's last game |
| `rest_diff`       | int  | home_days_rest - away_days_rest  |
| `home_short_rest` | int  | 1 if days_rest <= 3              |
| `away_short_rest` | int  | 1 if days_rest <= 3              |
| `both_short_rest` | int  | 1 if both teams on short rest    |

---

##### 3.6.4.2 Congestion Features (8)

| Feature                 | Type  | Description                             |
| ----------------------- | ----- | --------------------------------------- |
| `home_games_last_14d`   | int   | Games played in last 14 days            |
| `away_games_last_14d`   | int   | Games played in last 14 days            |
| `home_games_last_21d`   | int   | Games played in last 21 days            |
| `away_games_last_21d`   | int   | Games played in last 21 days            |
| `home_congestion_score` | float | Weighted congestion metric              |
| `away_congestion_score` | float | Weighted congestion metric              |
| `congestion_diff`       | float | home_congestion - away_congestion       |
| `fixture_pile_up`       | int   | 1 if either team has 3+ games in 8 days |

**Research-Backed Congestion Impact:**

```
Games in 8 days | xG Penalty | PPG Drop
---------------|------------|----------
1-2            | 0.00       | 0.00
3              | -0.15      | -0.20
4              | -0.30      | -0.40
5+             | -0.45      | -0.55
```

```python
def compute_congestion_features(team_id: int, match_date: datetime) -> dict:
    """
    Compute schedule congestion features.
    """
    features = {}

    # Get recent fixtures
    fixtures = get_team_fixtures(team_id, before=match_date, days=21)

    # Games in different windows
    features["games_last_14d"] = len([f for f in fixtures if f["days_ago"] <= 14])
    features["games_last_21d"] = len(fixtures)

    # Congestion score (weighted by recency)
    # Recent games count more heavily
    congestion = 0
    for f in fixtures:
        days_ago = f["days_ago"]
        if days_ago <= 3:
            congestion += 3.0  # Very recent = high fatigue
        elif days_ago <= 7:
            congestion += 2.0
        elif days_ago <= 14:
            congestion += 1.0
        else:
            congestion += 0.5

    features["congestion_score"] = congestion

    # Fixture pile-up (3+ games in 8 days)
    games_in_8d = len([f for f in fixtures if f["days_ago"] <= 8])
    features["fixture_pile_up"] = 1 if games_in_8d >= 3 else 0

    return features
```

---

##### 3.6.4.3 Travel Distance Features (8)

| Feature                 | Type  | Description                             |
| ----------------------- | ----- | --------------------------------------- |
| `away_travel_km`        | float | Distance from away team's city to venue |
| `away_travel_band`      | str   | local/regional/national/international   |
| `home_last_travel_km`   | float | Home team's travel in last match        |
| `away_last_travel_km`   | float | Away team's travel in last match        |
| `home_total_travel_14d` | float | Total km traveled in last 14 days       |
| `away_total_travel_14d` | float | Total km traveled in last 14 days       |
| `travel_fatigue_home`   | float | Weighted travel fatigue score           |
| `travel_fatigue_away`   | float | Weighted travel fatigue score           |

**Travel Bands:**

```python
TRAVEL_BANDS = {
    "local": (0, 100),  # Same city / nearby
    "regional": (100, 300),  # ~2-3 hour drive
    "national": (300, 800),  # Domestic flight
    "international": (800, float("inf")),  # Cross-border
}
```

```python
def compute_travel_features(
    home_team_id: int, away_team_id: int, venue: dict, prediction_time: datetime
) -> dict:
    """
    Compute travel distance and fatigue features.
    """
    features = {}

    # Away team travel to this venue
    away_city = get_team_home_city(away_team_id)
    venue_coords = (venue["lat"], venue["lon"])
    away_coords = (away_city["lat"], away_city["lon"])

    features["away_travel_km"] = haversine_distance(away_coords, venue_coords)
    features["away_travel_band"] = get_travel_band(features["away_travel_km"])

    # Total travel in last 14 days (both teams)
    for team_id, prefix in [(home_team_id, "home"), (away_team_id, "away")]:
        recent_fixtures = get_team_fixtures(team_id, before=prediction_time, days=14)

        total_travel = 0
        team_city = get_team_home_city(team_id)

        for fixture in recent_fixtures:
            fixture_venue = fixture["venue"]
            if fixture["is_away"]:
                # Travel to away venue and back
                dist = (
                    haversine_distance(
                        (team_city["lat"], team_city["lon"]),
                        (fixture_venue["lat"], fixture_venue["lon"]),
                    )
                    * 2
                )  # Round trip
                total_travel += dist

        features[f"{prefix}_total_travel_14d"] = total_travel

        # Travel fatigue score (weighted by distance and recency)
        fatigue = 0
        for fixture in recent_fixtures:
            if fixture["is_away"]:
                dist = fixture["travel_km"]
                days_ago = fixture["days_ago"]
                # Recent long travel = high fatigue
                fatigue += (dist / 500) * (7 / max(days_ago, 1))

        features[f"{prefix}_travel_fatigue"] = fatigue

    return features


def haversine_distance(coord1: tuple, coord2: tuple) -> float:
    """
    Calculate distance between two lat/lon points in km.
    """
    from math import radians, sin, cos, sqrt, atan2

    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return 6371 * c  # Earth radius in km
```

---

##### 3.6.4.4 Competition Type & Continental Fatigue (6)

| Feature                             | Type  | Description                       |
| ----------------------------------- | ----- | --------------------------------- |
| `home_played_continental_last_week` | int   | 1 if CL/EL in last 7 days         |
| `away_played_continental_last_week` | int   | 1 if CL/EL in last 7 days         |
| `home_midweek_european`             | int   | 1 if midweek European away        |
| `away_midweek_european`             | int   | 1 if midweek European away        |
| `continental_hangover_home`         | float | Fatigue from European competition |
| `continental_hangover_away`         | float | Fatigue from European competition |

```python
def compute_continental_fatigue(team_id: int, match_date: datetime) -> dict:
    """
    Compute fatigue from European/continental competition.
    """
    features = {}

    # Get fixtures in last 10 days
    recent = get_team_fixtures(team_id, before=match_date, days=10)

    # Check for continental matches
    continental_comps = [
        "UEFA Champions League",
        "UEFA Europa League",
        "UEFA Europa Conference League",
        "Copa Libertadores",
    ]

    continental_matches = [f for f in recent if f["competition"] in continental_comps]

    features["played_continental_last_week"] = 1 if len(continental_matches) > 0 else 0

    # Midweek European away (the killer)
    midweek_euro_away = [
        f for f in continental_matches if f["is_away"] and f["day_of_week"] in [1, 2, 3]
    ]  # Tue, Wed, Thu
    features["midweek_european"] = 1 if len(midweek_euro_away) > 0 else 0

    # Continental hangover score
    hangover = 0
    for f in continental_matches:
        days_ago = f["days_ago"]
        travel_km = f.get("travel_km", 0)

        # Midweek away in Europe = maximum fatigue
        if f["is_away"]:
            hangover += (1 / max(days_ago, 1)) * (1 + travel_km / 1000)
        else:
            hangover += (1 / max(days_ago, 1)) * 0.5

    features["continental_hangover"] = hangover

    return features
```

**Why Continental Fatigue Matters:**

```
Example: Liverpool
Thursday: Europa League away in Istanbul (3000km flight)
Sunday: Premier League vs Newcastle (home)

Without: Model uses Liverpool's normal xG
With: continental_hangover = HIGH, midweek_european = 1
     → Expect -0.3 to -0.5 xG penalty

This is consistently underpriced by bookmakers!
```

---

##### Summary: Schedule & Fatigue Features

| Category            | Count | Key Insight                   |
| ------------------- | ----- | ----------------------------- |
| **Basic Rest**      | 6     | Days since last game          |
| **Congestion**      | 8     | Games in 8/14/21 days         |
| **Travel Distance** | 8     | Km traveled, fatigue score    |
| **Continental**     | 6     | European competition hangover |

**Total: 28 schedule & fatigue features**

**Why This Is Massive Edge:**

```
Without Fatigue Features:
    Man City xG: 2.1
    vs Burnley xG: 0.8
    Expected: City dominant

With Fatigue Features:
    Man City: 3 games in 8 days
    Man City: Wednesday CL away (Milan, 1200km)
    congestion_score = HIGH
    continental_hangover = HIGH

    Adjusted Man City xG: 1.7 (-0.4)
    → Much closer match than expected
    → Value on Burnley +2.0 Asian Handicap
```

**Minor League Impact:**

```
In lower leagues (Championship, Bundesliga 2, etc.):
- Smaller squads = less rotation
- Same players every 3 days = cumulative fatigue
- congestion_score impact is 1.5x higher
- This is where the edge is biggest!
```

---

#### 3.6.5 Venue Features (4)

| Feature                      | Description                                  |
| ---------------------------- | -------------------------------------------- |
| `venue_altitude_m`           | Altitude in meters (La Paz = massive impact) |
| `venue_surface`              | grass/artificial (artificial = different xG) |
| `venue_capacity`             | Stadium size (atmosphere proxy)              |
| `venue_home_advantage_score` | Historical home win rate at venue            |

---

#### 3.6.6 Match Context (3)

| Feature                | Description        |
| ---------------------- | ------------------ |
| `is_derby`             | Local rivalry flag |
| `is_relegation_battle` | Either in bottom 5 |
| `competition_stage`    | Gameweek number    |

#### 3.6.5 Categorical Features for Trees (12)

**Q: Do unordered categoricals like league, manager, referee help tree models?**
**A: YES! Trees don't need ordering.** They find splits that reduce variance.

**Why categoricals work for trees:**

- Tree split: "Is `league_id` ∈ {39, 135, 140}?" (EPL, Serie A, La Liga)
- Groups leagues with similar goal patterns together
- CatBoost is BEST for this (native categorical support)
- XGBoost/LightGBM work with proper encoding

| Feature            | Type | Cardinality | Why It Helps                                                   |
| ------------------ | ---- | ----------- | -------------------------------------------------------------- |
| `league_id`        | cat  | ~36         | Different leagues have different goal/style patterns           |
| `division_tier`    | cat  | 3           | 1st div vs 2nd div vs 3rd div behavior                         |
| `region`           | cat  | 5           | europe, south_america, asia, north_america, oceania            |
| `manager_home_id`  | cat  | ~500        | Tactical styles (defensive vs attacking)                       |
| `manager_away_id`  | cat  | ~500        | Manager matchup dynamics                                       |
| `referee_id`       | cat  | ~200        | Card rates, penalty tendencies                                 |
| `venue_id`         | cat  | ~400        | Fortress effect, pitch size                                    |
| `competition_type` | cat  | 4           | league, domestic_cup, continental_cup, playoff                 |
| `country_id`       | cat  | ~20         | National football culture                                      |
| `home_team_id`     | cat  | ~800        | Team-specific patterns                                         |
| `away_team_id`     | cat  | ~800        | Team-specific patterns                                         |
| `kickoff_hour`     | cat  | 8           | Early (12-14), afternoon (15-17), evening (18-21), night (21+) |

**Encoding Strategy by Model:**

```python
# CatBoost: Native categorical support (BEST)
cat_features = ["league_id", "manager_home_id", "referee_id", "region", ...]
model = CatBoostRegressor(cat_features=cat_features)


# XGBoost/LightGBM: Target encoding for high cardinality
def target_encode(df, col, target, smoothing=10):
    """
    Encode category by smoothed mean of target.
    Handles rare categories gracefully.
    """
    global_mean = df[target].mean()
    agg = df.groupby(col)[target].agg(["mean", "count"])
    smooth = (agg["mean"] * agg["count"] + global_mean * smoothing) / (
        agg["count"] + smoothing
    )
    return df[col].map(smooth)


# For low cardinality (< 10 categories): One-hot encoding OK
df = pd.get_dummies(df, columns=["region", "division_tier", "competition_type"])
```

**Example: Why `league_id` helps**

- Bundesliga: Avg 3.1 goals/game (more open)
- Serie A: Avg 2.5 goals/game (more defensive)
- Tree learns: "If league_id = Bundesliga → increase goal expectation"

**Example: Why `manager_id` helps**

- Mourinho teams: Strong defense, low xG against
- Guardiola teams: High possession, high xG for
- Tree learns manager fingerprints without explicit features

**Example: Why `referee_id` helps**

- Some referees avg 4.5 cards/game, others 2.8
- Some are penalty-shy, others more trigger-happy
- Directly impacts cards/penalties market edges

**Example: Why `region` helps**

- European leagues: More tactical, lower variance
- South American: More chaotic, higher variance
- Asian leagues: Different patterns, bookmaker attention differs

**IMPORTANT:** For team_id features, use sparingly:

- Risk of overfitting to specific teams
- Better to use team_id for lookup of derived features
- But including team_id can capture "intangibles" (fan pressure, history)

---

### 3.7 Bayesian Poisson & Statistical Features (42 features) 🔥

**Why Basic Poisson Isn't Enough:**

- Point estimates don't capture uncertainty
- Early season: 3 games ≠ reliable λ estimate
- League averages matter (shrinkage toward prior)
- Market-implied priors often better than raw xG priors

**Syndicate Approach:** Bayesian updating with proper uncertainty quantification

---

#### 3.7.1 Basic Poisson Features (10)

| Feature                          | Type  | Description                   |
| -------------------------------- | ----- | ----------------------------- |
| `lambda_home_poisson`            | float | Expected home goals (Poisson) |
| `lambda_away_poisson`            | float | Expected away goals (Poisson) |
| `lambda_total_poisson`           | float | Total expected goals          |
| `lambda_diff_poisson`            | float | Home - Away expected          |
| `P_poisson_home`                 | float | Poisson P(home win)           |
| `P_poisson_draw`                 | float | Poisson P(draw)               |
| `P_poisson_away`                 | float | Poisson P(away win)           |
| `delta_p_home_poisson_vs_market` | float | Poisson - market prob         |
| `delta_p_draw_poisson_vs_market` | float | Poisson - market prob         |
| `delta_p_away_poisson_vs_market` | float | Poisson - market prob         |

---

#### 3.7.2 Bayesian Poisson Updating (12 features)

**Key Insight:** Use Gamma-Poisson conjugate prior for proper uncertainty.

| Feature                   | Type  | Description                            |
| ------------------------- | ----- | -------------------------------------- |
| `lambda_home_bayesian`    | float | Posterior mean λ (shrunk toward prior) |
| `lambda_away_bayesian`    | float | Posterior mean λ (shrunk toward prior) |
| `lambda_home_lower_95`    | float | 95% credible interval lower bound      |
| `lambda_home_upper_95`    | float | 95% credible interval upper bound      |
| `lambda_away_lower_95`    | float | 95% credible interval lower bound      |
| `lambda_away_upper_95`    | float | 95% credible interval upper bound      |
| `lambda_uncertainty_home` | float | Width of credible interval             |
| `lambda_uncertainty_away` | float | Width of credible interval             |
| `shrinkage_factor_home`   | float | How much we shrink toward prior (0-1)  |
| `shrinkage_factor_away`   | float | How much we shrink toward prior        |
| `prior_weight_home`       | float | Weight given to prior vs data          |
| `prior_weight_away`       | float | Weight given to prior vs data          |

```python
import numpy as np
from scipy import stats


class BayesianPoissonModel:
    """
    Bayesian Poisson model with Gamma conjugate prior.

    Prior: λ ~ Gamma(α₀, β₀)
    Likelihood: Goals ~ Poisson(λ)
    Posterior: λ | data ~ Gamma(α₀ + Σgoals, β₀ + n_games)
    """

    def __init__(self, league_avg_goals: float = 1.4, prior_strength: int = 5):
        """
        Initialize with league-specific prior.

        Args:
            league_avg_goals: League average goals per team per game
            prior_strength: Effective number of "prior games" (higher = stronger shrinkage)
        """
        # Gamma prior parameters (α, β) where E[λ] = α/β
        self.alpha_0 = league_avg_goals * prior_strength
        self.beta_0 = prior_strength

    def update(self, goals_scored: list) -> dict:
        """
        Update posterior given observed goals.

        Args:
            goals_scored: List of goals in recent games

        Returns:
            Posterior statistics
        """
        n_games = len(goals_scored)
        total_goals = sum(goals_scored)

        # Posterior parameters
        alpha_n = self.alpha_0 + total_goals
        beta_n = self.beta_0 + n_games

        # Posterior mean (shrunk estimate)
        posterior_mean = alpha_n / beta_n

        # Credible interval
        lower_95 = stats.gamma.ppf(0.025, alpha_n, scale=1 / beta_n)
        upper_95 = stats.gamma.ppf(0.975, alpha_n, scale=1 / beta_n)

        # Shrinkage factor (how much we trust the data vs prior)
        # 0 = all prior, 1 = all data
        shrinkage = n_games / (n_games + self.beta_0)

        # Raw MLE estimate (no shrinkage)
        mle_estimate = (
            total_goals / n_games if n_games > 0 else self.alpha_0 / self.beta_0
        )

        return {
            "lambda_bayesian": posterior_mean,
            "lambda_lower_95": lower_95,
            "lambda_upper_95": upper_95,
            "lambda_uncertainty": upper_95 - lower_95,
            "shrinkage_factor": shrinkage,
            "prior_weight": 1 - shrinkage,
            "lambda_mle": mle_estimate,
        }


def compute_bayesian_lambda_features(
    team_id: int, prediction_time: datetime, league_id: int
) -> dict:
    """
    Compute Bayesian Poisson features with league-specific shrinkage.
    """
    features = {}

    # Get league average (the prior)
    league_stats = get_league_stats(league_id, prediction_time)
    league_avg_home = league_stats["avg_home_goals"]  # ~1.5
    league_avg_away = league_stats["avg_away_goals"]  # ~1.2

    # Get team's recent goals
    home_matches = get_team_home_matches(team_id, prediction_time, n=10)
    away_matches = get_team_away_matches(team_id, prediction_time, n=10)

    home_goals = [m["goals_for"] for m in home_matches]
    away_goals = [m["goals_for"] for m in away_matches]

    # Prior strength depends on sample size (more data = weaker prior)
    home_prior_strength = max(5, 10 - len(home_goals))
    away_prior_strength = max(5, 10 - len(away_goals))

    # Bayesian update for home attacking
    home_model = BayesianPoissonModel(league_avg_home, home_prior_strength)
    home_posterior = home_model.update(home_goals)

    for key, val in home_posterior.items():
        features[f"{key}_home"] = val

    # Bayesian update for away attacking
    away_model = BayesianPoissonModel(league_avg_away, away_prior_strength)
    away_posterior = away_model.update(away_goals)

    for key, val in away_posterior.items():
        features[f"{key}_away"] = val

    return features
```

**Why Bayesian Matters:**

```
Early Season (3 games played):
    Team scored: 5, 2, 1 goals (avg = 2.67)
    MLE λ = 2.67 (overconfident!)

    Bayesian with prior (league avg = 1.4):
    Posterior λ = 1.85 (shrunk toward prior)
    95% CI = [1.1, 2.8] (high uncertainty)
    shrinkage_factor = 0.38 (62% prior, 38% data)

Late Season (25 games played):
    Team scored avg 2.2 goals

    Bayesian:
    Posterior λ = 2.15 (closer to data)
    95% CI = [1.9, 2.4] (low uncertainty)
    shrinkage_factor = 0.83 (17% prior, 83% data)
```

---

#### 3.7.3 Home/Away Variance Features (6)

| Feature                 | Type  | Description                     |
| ----------------------- | ----- | ------------------------------- |
| `home_attack_variance`  | float | Variance in home goals scored   |
| `away_attack_variance`  | float | Variance in away goals scored   |
| `home_defense_variance` | float | Variance in home goals conceded |
| `away_defense_variance` | float | Variance in away goals conceded |
| `home_predictability`   | float | 1 / (1 + variance)              |
| `away_predictability`   | float | 1 / (1 + variance)              |

**Why Variance Matters:**

- Low variance team = predictable, model confident
- High variance team = volatile, model uncertain
- Variance affects bet sizing, not just prediction

---

#### 3.7.4 Market-Implied Priors (8 features)

**Key Insight:** Markets are often better priors than raw xG, especially for team strength.

| Feature                       | Type  | Description                                    |
| ----------------------------- | ----- | ---------------------------------------------- |
| `lambda_home_market_implied`  | float | λ extracted from market odds                   |
| `lambda_away_market_implied`  | float | λ extracted from market odds                   |
| `lambda_blend_home`           | float | Weighted blend of xG and market λ              |
| `lambda_blend_away`           | float | Weighted blend of xG and market λ              |
| `market_xg_disagreement_home` | float | market*λ - xg*λ                                |
| `market_xg_disagreement_away` | float | market*λ - xg*λ                                |
| `market_confidence_score`     | float | How tight is the market? (low vig = confident) |
| `use_market_prior_flag`       | int   | 1 if market more reliable than xG              |

```python
def extract_market_implied_lambda(
    odds_home: float, odds_draw: float, odds_away: float
) -> dict:
    """
    Extract implied λ from market odds using Poisson inversion.

    Market odds encode sharp money's view of goal expectancy.
    """
    # Convert to probabilities (remove vig first)
    probs = remove_vig([1 / odds_home, 1 / odds_draw, 1 / odds_away])
    p_home, p_draw, p_away = probs

    # Grid search for λ that best fits these probabilities
    best_lambda_home, best_lambda_away = None, None
    best_error = float("inf")

    for lh in np.arange(0.5, 4.0, 0.05):
        for la in np.arange(0.5, 4.0, 0.05):
            # Compute Poisson probabilities
            p_h_pred, p_d_pred, p_a_pred = poisson_match_probs(lh, la)

            error = (
                (p_home - p_h_pred) ** 2
                + (p_draw - p_d_pred) ** 2
                + (p_away - p_a_pred) ** 2
            )

            if error < best_error:
                best_error = error
                best_lambda_home = lh
                best_lambda_away = la

    return {
        "lambda_home_market_implied": best_lambda_home,
        "lambda_away_market_implied": best_lambda_away,
    }


def compute_blended_lambda(
    lambda_xg_home: float,
    lambda_xg_away: float,
    lambda_market_home: float,
    lambda_market_away: float,
    market_confidence: float,  # Based on vig, sharp consensus
    sample_size: int,  # Number of games for xG estimate
) -> dict:
    """
    Blend xG-based λ with market-implied λ.

    Early season: Weight market more (better prior)
    Late season: Weight xG more (more data)
    Sharp market: Weight market more
    """
    # Market weight increases with confidence and decreases with sample size
    market_weight = market_confidence * (1 / (1 + sample_size / 20))
    xg_weight = 1 - market_weight

    features = {
        "lambda_blend_home": xg_weight * lambda_xg_home
        + market_weight * lambda_market_home,
        "lambda_blend_away": xg_weight * lambda_xg_away
        + market_weight * lambda_market_away,
        "market_xg_disagreement_home": lambda_market_home - lambda_xg_home,
        "market_xg_disagreement_away": lambda_market_away - lambda_xg_away,
        "market_weight_used": market_weight,
    }

    return features
```

---

#### 3.7.5 League-Specific Shrinkage (6)

| Feature                     | Type  | Description                                     |
| --------------------------- | ----- | ----------------------------------------------- |
| `league_avg_home_goals`     | float | League average home goals                       |
| `league_avg_away_goals`     | float | League average away goals                       |
| `league_goal_variance`      | float | Goal variance in this league                    |
| `shrinkage_strength_league` | float | How much to shrink (higher in volatile leagues) |
| `home_goals_vs_league`      | float | Team home goals / league avg                    |
| `away_goals_vs_league`      | float | Team away goals / league avg                    |

```python
# League-specific prior strengths
LEAGUE_PRIOR_STRENGTH = {
    # Tier 1: Lots of data, weak prior needed
    39: 3,  # EPL
    140: 3,  # La Liga
    78: 3,  # Bundesliga
    # Tier 2-3: Moderate prior
    88: 5,  # Eredivisie
    253: 5,  # MLS
    # Tier 4-5: Sparse data, strong prior needed
    106: 8,  # Polish Ekstraklasa
    207: 8,  # Swiss Super League
    # Very sparse leagues
    "default": 10,
}


def get_league_shrinkage_strength(league_id: int, games_played: int) -> float:
    """
    Get shrinkage strength based on league and sample size.

    More shrinkage for:
    - Minor leagues (less reliable data)
    - Early season (fewer games)
    """
    base_strength = LEAGUE_PRIOR_STRENGTH.get(league_id, 10)

    # Reduce shrinkage as more games are played
    adjusted = base_strength * (1 / (1 + games_played / 10))

    return adjusted
```

---

#### Summary: Bayesian Poisson Features

| Category              | Count | Key Insight             |
| --------------------- | ----- | ----------------------- |
| **Basic Poisson**     | 10    | Point estimates         |
| **Bayesian Updating** | 12    | Uncertainty + shrinkage |
| **Variance Features** | 6     | Predictability          |
| **Market-Implied**    | 8     | Blend xG with market    |
| **League Shrinkage**  | 6     | League-specific priors  |

**Total: 42 Bayesian Poisson features**

**Why This Is How Syndicates Handle Uncertainty:**

```
Basic Approach:
    λ_home = team_xg_avg = 1.8
    → Single point estimate, no uncertainty

Syndicate Approach:
    λ_home_bayesian = 1.65 (shrunk toward league avg 1.4)
    λ_home_95_CI = [1.3, 2.0] (uncertainty quantified)
    λ_home_market = 1.55 (what sharps think)
    λ_home_blend = 1.60 (weighted combination)
    shrinkage_factor = 0.6 (40% prior, 60% data)

    → Model knows its confidence level
    → Can size bets appropriately
    → Handles early season properly
```

**Early Season Example:**

```
Game 3 of season. Team scored 5, 2, 4 goals (avg 3.67).

Basic: λ = 3.67 (way overconfident!)

Bayesian:
    Prior: league_avg = 1.4, strength = 8
    Posterior λ = (8*1.4 + 11) / (8 + 3) = 2.02
    95% CI = [1.2, 3.1]
    shrinkage_factor = 0.27

→ Properly skeptical of small sample
→ Won't over-bet based on 3 games
```

---

### 3.8 Multi-Source xG Features (36 features) 🔥

**We have 3 labeled xG sources - each captures different aspects!**

| Source                  | Coverage         | Methodology                | Granularity | Best For                   |
| ----------------------- | ---------------- | -------------------------- | ----------- | -------------------------- |
| **Understat**           | 5 leagues        | Shot coordinates + context | Shot-level  | Ground truth, shot quality |
| **Soccerfootball.info** | 35 leagues       | Their proprietary model    | Match + HT  | HT features, all leagues   |
| **FootyStats**          | 33 of 35 leagues | Their proprietary model    | Team-level  | Rolling features           |

**Why Use All Sources:**

1. **Different methodologies** - Each model values shot types differently
2. **xG disagreement = signal** - When sources disagree, something interesting is happening
3. **Redundancy** - If one source is missing, others provide backup
4. **Ensemble value** - Average of multiple xG sources often beats any single source

**Note:** API-Football provides basic match statistics but is NOT used as a labeled xG source. We use the 3 labeled sources above plus synthetic xG as fallback for non-Understat leagues.

---

#### 3.8.1 Per-Source xG Features (12 features)

| Feature                      | Source              | Coverage         | Description               |
| ---------------------------- | ------------------- | ---------------- | ------------------------- |
| `xg_understat_home`          | Understat           | 5 leagues        | Most accurate, shot-level |
| `xg_understat_away`          | Understat           | 5 leagues        | Most accurate, shot-level |
| `xg_soccerfootball_home`     | Soccerfootball.info | 35 leagues       | Match-level               |
| `xg_soccerfootball_away`     | Soccerfootball.info | 35 leagues       | Match-level               |
| `xg_footystats_home`         | FootyStats          | 33 of 35 leagues | Season rolling xG         |
| `xg_footystats_away`         | FootyStats          | 33 of 35 leagues | Season rolling xG         |
| `ht_xg_soccerfootball_home`  | Soccerfootball.info | 35 leagues       | Half-time xG              |
| `ht_xg_soccerfootball_away`  | Soccerfootball.info | 35 leagues       | Half-time xG              |
| `ht_xg_understat_home`       | Understat           | 5 leagues        | HT shot-level             |
| `ht_xg_understat_away`       | Understat           | 5 leagues        | HT shot-level             |
| `npxg_understat_home`        | Understat           | 5 leagues        | Non-penalty xG            |
| `npxg_understat_away`        | Understat           | 5 leagues        | Non-penalty xG            |
| `xg_per_shot_understat_home` | Understat           | 5 leagues        | Shot quality              |
| `xg_per_shot_understat_away` | Understat           | 5 leagues        | Shot quality              |

**Total: 14 features** (removed API-Football xG features)

---

#### 3.8.2 xG Disagreement Features (16 features) 🔥

**Key Insight:** When xG sources disagree significantly, it signals model uncertainty or unusual match characteristics.

| Feature                                | Formula                     | Description                                                               |
| -------------------------------------- | --------------------------- | ------------------------------------------------------------------------- |
| `xg_disagreement_home`                 | std(all_xg_sources)         | Higher = sources disagree                                                 |
| `xg_disagreement_away`                 | std(all_xg_sources)         | Higher = sources disagree                                                 |
| `xg_understat_vs_soccerfootball_home`  | understat - soccerfootball  | Positive = Understat sees more                                            |
| `xg_understat_vs_soccerfootball_away`  | understat - soccerfootball  | Positive = Understat sees more                                            |
| `xg_understat_vs_footystats_home`      | understat - footystats      | Compare to team-level                                                     |
| `xg_understat_vs_footystats_away`      | understat - footystats      | Compare to team-level                                                     |
| `xg_soccerfootball_vs_footystats_home` | soccerfootball - footystats | Both available in most leagues (excludes Argentina, Chile for FootyStats) |
| `xg_soccerfootball_vs_footystats_away` | soccerfootball - footystats | Both available in most leagues (excludes Argentina, Chile for FootyStats) |
| `xg_max_source_home`                   | max(all_sources)            | Which model is most optimistic                                            |
| `xg_max_source_away`                   | max(all_sources)            | Which model is most optimistic                                            |
| `xg_min_source_home`                   | min(all_sources)            | Which model is most pessimistic                                           |
| `xg_min_source_away`                   | min(all_sources)            | Which model is most pessimistic                                           |
| `xg_range_home`                        | max - min                   | Spread of xG estimates                                                    |
| `xg_range_away`                        | max - min                   | Spread of xG estimates                                                    |
| `xg_consensus_home`                    | mean(all_sources)           | Ensemble average                                                          |
| `xg_consensus_away`                    | mean(all_sources)           | Ensemble average                                                          |

```python
def compute_xg_disagreement_features(
    xg_understat: float,
    xg_soccerfootball: float,
    xg_footystats: float,
    team: str = "home",
) -> dict:
    """
    Compute xG disagreement features from 3 labeled xG sources.

    High disagreement = model uncertainty = lower confidence in predictions.
    """
    features = {}

    # Collect available sources (some may be None)
    sources = [xg_understat, xg_soccerfootball, xg_footystats]
    available = [x for x in sources if x is not None]

    if len(available) >= 2:
        features[f"xg_disagreement_{team}"] = np.std(available)
        features[f"xg_max_source_{team}"] = max(available)
        features[f"xg_min_source_{team}"] = min(available)
        features[f"xg_range_{team}"] = max(available) - min(available)
        features[f"xg_consensus_{team}"] = np.mean(available)
    else:
        # Only one source available
        features[f"xg_disagreement_{team}"] = 0
        features[f"xg_consensus_{team}"] = available[0] if available else None

    # Source comparisons (when both available)
    if xg_understat and xg_soccerfootball:
        features[f"xg_understat_vs_soccerfootball_{team}"] = (
            xg_understat - xg_soccerfootball
        )

    if xg_understat and xg_footystats:
        features[f"xg_understat_vs_footystats_{team}"] = xg_understat - xg_footystats

    if xg_soccerfootball and xg_footystats:
        features[f"xg_soccerfootball_vs_footystats_{team}"] = (
            xg_soccerfootball - xg_footystats
        )

    return features
```

---

#### 3.8.3 xG Source Priority & Fallback Logic (6 features)

**Total Multi-Source xG Features:**

- Per-source xG: 14 features (Understat, Soccerfootball, FootyStats)
- Disagreement features: 16 features
- Source priority & fallback: 6 features
- **Total: 36 features** (was 32, increased due to additional source comparisons)

| Feature                  | Type  | Description                                                                    |
| ------------------------ | ----- | ------------------------------------------------------------------------------ |
| `xg_source_primary`      | str   | Which source used (understat > soccerfootball > footystats > synthetic)        |
| `xg_source_count`        | int   | How many xG sources available (1-3)                                            |
| `xg_confidence`          | float | 1.0 if Understat, 0.9 if Soccerfootball, 0.85 if FootyStats, 0.75 if Synthetic |
| `xg_is_understat_league` | bool  | True for 5 Understat leagues                                                   |
| `xg_used_home`           | float | Final xG value used (best available)                                           |
| `xg_used_away`           | float | Final xG value used (best available)                                           |

```python
XG_SOURCE_PRIORITY = [
    "understat",  # Best: shot-level with coordinates
    "soccerfootball",  # Good: match-level, 35 leagues
    "footystats",  # Good: team-level rolling
    "synthetic",  # Fallback: our trained model (for non-Understat leagues)
]

XG_CONFIDENCE = {
    "understat": 1.0,
    "soccerfootball": 0.9,
    "footystats": 0.85,
    "synthetic": 0.75,
}


def get_best_xg(
    xg_understat: float,
    xg_soccerfootball: float,
    xg_footystats: float,
    xg_synthetic: float,
    league_id: int,
) -> dict:
    """
    Get best available xG with source tracking.

    Uses 3 labeled xG sources: Understat, Soccerfootball.info, FootyStats
    Falls back to synthetic xG for non-Understat leagues if needed.
    """
    UNDERSTAT_LEAGUES = [
        39,
        140,
        135,
        78,
        61,
    ]  # EPL, La Liga, Serie A, Bundesliga, Ligue 1

    sources = {
        "understat": xg_understat,
        "soccerfootball": xg_soccerfootball,
        "footystats": xg_footystats,
        "synthetic": xg_synthetic,
    }

    # Count available sources
    available_count = sum(1 for v in sources.values() if v is not None)

    # Select best available
    for source in XG_SOURCE_PRIORITY:
        if sources[source] is not None:
            return {
                "xg_used": sources[source],
                "xg_source_primary": source,
                "xg_confidence": XG_CONFIDENCE[source],
                "xg_source_count": available_count,
                "xg_is_understat_league": league_id in UNDERSTAT_LEAGUES,
            }

    return {
        "xg_used": None,
        "xg_source_primary": "none",
        "xg_confidence": 0,
        "xg_source_count": 0,
        "xg_is_understat_league": league_id in UNDERSTAT_LEAGUES,
    }
```

---

### 3.9 Synthetic xG Model (For Non-Understat Leagues) (18 features) 🔥

**The Problem:**

- Understat provides shot-level xG for **only 5 leagues** (EPL, La Liga, Serie A, Bundesliga, Ligue 1)
- Some leagues may have gaps in Soccerfootball.info/FootyStats coverage
- xG-driven features should be consistent across ALL leagues

**The Solution:**
Train a synthetic xG model using features available EVERYWHERE, then apply as final fallback.

---

#### 3.8.1 Features Available in ALL 35 Leagues

| Feature               | Source         | Available       | Correlation with xG |
| --------------------- | -------------- | --------------- | ------------------- |
| `shots`               | API-Football   | ✅ All          | 0.75                |
| `shots_on_target`     | API-Football   | ✅ All          | 0.82                |
| `shots_off_target`    | API-Football   | ✅ All          | 0.65                |
| `shots_blocked`       | API-Football   | ✅ All          | 0.55                |
| `dangerous_attacks`   | FootyStats     | ✅ Most (33/35) | 0.70                |
| `attacks`             | FootyStats     | ✅ Most (33/35) | 0.60                |
| `possession`          | API-Football   | ✅ All          | 0.45                |
| `corners`             | API-Football   | ✅ All          | 0.50                |
| `key_passes`          | API-Football   | ✅ Most         | 0.72                |
| `big_chances_created` | Soccerfootball | ✅ All          | 0.85                |
| `passes_final_third`  | API-Football   | ✅ Some         | 0.65                |
| `crosses`             | API-Football   | ✅ Most         | 0.45                |
| `ppda`                | Understat only | ❌ 5            | -                   |
| `shot_coordinates`    | Understat only | ❌ 5            | -                   |

---

#### 3.8.2 Synthetic xG Model Architecture

**Step 1: Train on Understat Leagues**

```python
class SyntheticXGModel:
    """
    Learn to predict xG from non-coordinate features.

    Train on 5 Understat leagues where we have ground truth xG.
    Apply to 31 non-Understat leagues to generate synthetic xG.
    """

    def __init__(self):
        # Model to predict match-level xG from available features
        self.model = GradientBoostingRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.1
        )

        # Features available in ALL leagues
        self.feature_cols = [
            "shots",
            "shots_on_target",
            "shots_off_target",
            "shots_blocked",
            "dangerous_attacks",
            "attacks",
            "possession",
            "corners",
            "big_chances_created",
            "key_passes",
            "crosses",
            "shots_inside_box",
            "shots_outside_box",  # If available
            "shot_accuracy",  # SOT / shots
            "attack_efficiency",  # shots / attacks
        ]

    def prepare_training_data(self) -> tuple:
        """
        Prepare training data from Understat leagues.

        Features: Non-coordinate stats
        Target: Actual xG from Understat
        """
        # Get all matches from Understat leagues with both xG and basic stats
        matches = get_matches_with_xg(
            leagues=[
                39,
                140,
                135,
                78,
                61,
            ],  # EPL, La Liga, Serie A, Bundesliga, Ligue 1
            seasons=["2021", "2022", "2023", "2024"],
        )

        X = []
        y = []

        for match in matches:
            # Features (available everywhere)
            features = self.extract_features(match)
            X.append(features)

            # Target (Understat xG)
            y.append(match["xg_home"])  # Or xg_away for away team

        return np.array(X), np.array(y)

    def extract_features(self, match: dict) -> list:
        """Extract prediction features from match data."""
        return [
            match.get("shots", 0),
            match.get("shots_on_target", 0),
            match.get("shots", 0) - match.get("shots_on_target", 0),  # Off target
            match.get("shots_blocked", 0),
            match.get("dangerous_attacks", 0),
            match.get("attacks", 0),
            match.get("possession", 50),
            match.get("corners", 0),
            match.get("big_chances", 0),
            match.get("key_passes", 0),
            match.get("crosses", 0),
            match.get("shots_inside_box", match.get("shots", 0) * 0.6),  # Estimate
            match.get("shots_outside_box", match.get("shots", 0) * 0.4),  # Estimate
            match.get("shots_on_target", 0) / max(match.get("shots", 1), 1),  # Accuracy
            match.get("shots", 0) / max(match.get("attacks", 1), 1),  # Efficiency
        ]

    def train(self):
        """Train the synthetic xG model."""
        X, y = self.prepare_training_data()

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"Synthetic xG Model - MAE: {mae:.3f}, R²: {r2:.3f}")
        # Typical: MAE ~0.25-0.35, R² ~0.70-0.80

        return self

    def predict_xg(self, match: dict) -> float:
        """Predict xG for a match (any league)."""
        features = self.extract_features(match)
        return self.model.predict([features])[0]
```

**Expected Performance:**

```
Synthetic xG Model trained on 5 leagues:
    MAE: ~0.28 xG (pretty good!)
    R²: ~0.75

For comparison:
    Actual Understat xG MAE vs goals: ~0.35

→ Synthetic xG is ~80% as accurate as true xG
→ MUCH better than using shots alone
```

---

#### 3.8.3 Synthetic xG Features (18 features)

| Feature                      | Type  | Description                                      |
| ---------------------------- | ----- | ------------------------------------------------ |
| `xg_synthetic_home`          | float | Synthetic xG for home team                       |
| `xg_synthetic_away`          | float | Synthetic xG for away team                       |
| `xg_synthetic_total`         | float | Total synthetic xG                               |
| `xg_synthetic_diff`          | float | Home - Away synthetic xG                         |
| `xg_source`                  | str   | 'understat' or 'synthetic'                       |
| `xg_confidence`              | float | Confidence in xG estimate (higher for Understat) |
| `xg_synthetic_last5_home`    | float | Rolling synthetic xG (last 5)                    |
| `xg_synthetic_last5_away`    | float | Rolling synthetic xG (last 5)                    |
| `xg_synthetic_season_home`   | float | Season avg synthetic xG                          |
| `xg_synthetic_season_away`   | float | Season avg synthetic xG                          |
| `xg_synthetic_vs_goals_home` | float | Synthetic xG - actual goals                      |
| `xg_synthetic_vs_goals_away` | float | Over/underperformance                            |
| `xg_per_shot_synthetic_home` | float | Shot quality proxy                               |
| `xg_per_shot_synthetic_away` | float | Shot quality proxy                               |
| `big_chance_conversion_home` | float | Goals / big chances                              |
| `big_chance_conversion_away` | float | Finishing quality                                |
| `xg_model_residual_home`     | float | Prediction error if Understat available          |
| `xg_model_residual_away`     | float | Useful for calibration                           |

```python
def compute_synthetic_xg_features(
    fixture_id: int, team_id: int, prediction_time: datetime, xg_model: SyntheticXGModel
) -> dict:
    """
    Compute xG features - using Understat if available, synthetic otherwise.
    """
    features = {}

    # Check if this is an Understat league
    league_id = get_fixture_league(fixture_id)
    is_understat_league = league_id in [39, 140, 135, 78, 61]

    # Get recent matches
    recent_matches = get_team_matches(team_id, before=prediction_time, n=10)

    xg_values = []
    for match in recent_matches:
        if is_understat_league and "xg" in match:
            # Use actual Understat xG
            xg = match["xg"]
            features["xg_source"] = "understat"
        else:
            # Compute synthetic xG
            xg = xg_model.predict_xg(match)
            features["xg_source"] = "synthetic"

        xg_values.append(xg)

    # Rolling features
    features["xg_synthetic_last5"] = (
        np.mean(xg_values[:5]) if len(xg_values) >= 5 else np.mean(xg_values)
    )
    features["xg_synthetic_season"] = np.mean(xg_values)

    # xG confidence (Understat = 1.0, Synthetic = 0.8)
    features["xg_confidence"] = 1.0 if is_understat_league else 0.8

    # xG per shot (quality proxy)
    total_shots = sum(m.get("shots", 1) for m in recent_matches)
    total_xg = sum(xg_values)
    features["xg_per_shot_synthetic"] = total_xg / max(total_shots, 1)

    # Over/underperformance
    total_goals = sum(m.get("goals_for", 0) for m in recent_matches)
    features["xg_synthetic_vs_goals"] = total_xg - total_goals

    return features
```

---

#### 3.8.4 Per-Shot xG Estimation (Advanced)

For even better synthetic xG, estimate per-shot xG:

```python
class PerShotSyntheticXG:
    """
    Estimate xG per shot category without coordinates.

    Uses historical averages by shot type.
    """

    # League-average xG by shot type (from Understat analysis)
    XG_BY_SHOT_TYPE = {
        "shot_on_target_inside_box": 0.35,
        "shot_on_target_outside_box": 0.08,
        "shot_off_target_inside_box": 0.10,
        "shot_off_target_outside_box": 0.03,
        "big_chance": 0.45,
        "penalty": 0.76,
        "header": 0.12,
        "free_kick": 0.06,
    }

    def estimate_match_xg(self, match_stats: dict) -> float:
        """
        Estimate match xG from shot breakdown.
        """
        xg = 0

        # Big chances (highest xG)
        xg += match_stats.get("big_chances", 0) * self.XG_BY_SHOT_TYPE["big_chance"]

        # Shots on target (assume 70% inside box)
        sot = match_stats.get("shots_on_target", 0) - match_stats.get("big_chances", 0)
        xg += sot * 0.7 * self.XG_BY_SHOT_TYPE["shot_on_target_inside_box"]
        xg += sot * 0.3 * self.XG_BY_SHOT_TYPE["shot_on_target_outside_box"]

        # Shots off target
        shots_off = match_stats.get("shots", 0) - match_stats.get("shots_on_target", 0)
        xg += shots_off * 0.6 * self.XG_BY_SHOT_TYPE["shot_off_target_inside_box"]
        xg += shots_off * 0.4 * self.XG_BY_SHOT_TYPE["shot_off_target_outside_box"]

        # Penalties
        xg += match_stats.get("penalties", 0) * self.XG_BY_SHOT_TYPE["penalty"]

        return xg
```

---

#### 3.8.5 Model Calibration (Understat vs Synthetic)

| Metric       | Understat xG | Synthetic xG | Ratio |
| ------------ | ------------ | ------------ | ----- |
| MAE vs Goals | 0.35         | 0.45         | 1.29x |
| R² vs Goals  | 0.82         | 0.70         | 0.85x |
| Correlation  | 0.91         | 0.84         | 0.92x |

**Interpretation:**

- Synthetic xG is ~85-90% as predictive as true xG
- MUCH better than using shots or goals alone
- Enables consistent xG features across all 35 leagues

---

#### Summary: Synthetic xG Features

| Category            | Count | Key Insight                   |
| ------------------- | ----- | ----------------------------- |
| **Match-level xG**  | 6     | Synthetic xG for any league   |
| **Rolling xG**      | 4     | Historical synthetic xG       |
| **Quality metrics** | 4     | xG per shot, conversion rates |
| **Calibration**     | 4     | Confidence, residuals         |

**Total: 18 synthetic xG features**

**Why This Unifies Your xG Stack:**

```
Before:
    EPL: Real xG features ✅
    La Liga: Real xG features ✅
    MLS: NO xG features ❌ (model degrades)
    Polish Ekstraklasa: NO xG features ❌

After:
    EPL: Real xG features ✅
    La Liga: Real xG features ✅
    MLS: Synthetic xG features ✅ (~85% accuracy)
    Polish Ekstraklasa: Synthetic xG features ✅

→ Consistent model performance across ALL 35 leagues!
```

---

### 3.9 Team Style Embeddings & Latent Profiles (48 features) 🔥

**Why This Matters:**

- Rolling windows capture WHAT teams produce (goals, xG, shots)
- But NOT HOW they play (tempo, width, verticality, pressing)
- Team style affects matchup dynamics: counter-attacking vs possession, high-press vs low-block
- These embeddings improve model generalization across leagues

**Data Limitation:** We don't have GPS/tracking data.
**Solution:** Derive style PROXIES from existing data.

---

#### 3.8.1 Attacking Style Profile (16 features)

| Feature                     | Type  | Description                | Derived From                               |
| --------------------------- | ----- | -------------------------- | ------------------------------------------ |
| `home_xg_per_shot`          | float | xG quality per shot        | xG / shots                                 |
| `away_xg_per_shot`          | float | Shot quality               | xG / shots                                 |
| `home_shot_volume_style`    | float | High vs low volume         | shots / match                              |
| `away_shot_volume_style`    | float | High vs low volume         | shots / match                              |
| `home_big_chance_pct`       | float | % shots from big chances   | big_chances / shots                        |
| `away_big_chance_pct`       | float | % shots from big chances   | big_chances / shots                        |
| `home_counter_attack_ratio` | float | % goals from counters      | counter_goals / total_goals                |
| `away_counter_attack_ratio` | float | Counter reliance           | counter_goals / total_goals                |
| `home_set_piece_reliance`   | float | % xG from set pieces       | set_piece_xg / total_xg                    |
| `away_set_piece_reliance`   | float | Set piece dependence       | set_piece_xg / total_xg                    |
| `home_attack_width`         | float | Shots from wide vs central | (shots_left + shots_right) / shots_central |
| `away_attack_width`         | float | Wide vs central attacks    | (shots_left + shots_right) / shots_central |
| `home_attack_directness`    | float | Direct vs build-up         | passes_forward / passes_total              |
| `away_attack_directness`    | float | Vertical vs horizontal     | passes_forward / passes_total              |
| `home_cross_reliance`       | float | Crosses per attack         | crosses / dangerous_attacks                |
| `away_cross_reliance`       | float | Crossing style             | crosses / dangerous_attacks                |

```python
def compute_attacking_style_features(team_id: int, prediction_time: datetime) -> dict:
    """
    Derive attacking style profile from match data.
    """
    features = {}

    # Get last 10 matches
    matches = get_team_matches(team_id, n=10, before=prediction_time)

    # xG per shot (quality over quantity)
    total_xg = sum(m["xg"] for m in matches)
    total_shots = sum(m["shots"] for m in matches)
    features["xg_per_shot"] = total_xg / max(total_shots, 1)

    # Shot volume style (shots per match)
    features["shot_volume_style"] = total_shots / len(matches) if matches else 0

    # Big chance percentage (clinical finishing)
    big_chances = sum(m.get("big_chances", 0) for m in matches)
    features["big_chance_pct"] = big_chances / max(total_shots, 1)

    # Set piece reliance (from FootyStats)
    set_piece_xg = sum(m.get("set_piece_xg", 0) for m in matches)
    features["set_piece_reliance"] = set_piece_xg / max(total_xg, 0.01)

    # Attack directness (if pass data available)
    if "passes_forward" in matches[0]:
        passes_fwd = sum(m["passes_forward"] for m in matches)
        passes_total = sum(m["passes_total"] for m in matches)
        features["attack_directness"] = passes_fwd / max(passes_total, 1)

    return features
```

---

#### 3.8.2 Defensive Style Profile (14 features)

| Feature                       | Type  | Description                | Derived From                 |
| ----------------------------- | ----- | -------------------------- | ---------------------------- |
| `home_defensive_block_height` | float | High vs low block          | PPDA + opp_pass_completion   |
| `away_defensive_block_height` | float | Pressing height            | PPDA + opp_pass_completion   |
| `home_ppda_style`             | float | Pressing intensity         | PPDA (passes per def action) |
| `away_ppda_style`             | float | Pressing intensity         | PPDA                         |
| `home_tackle_aggression`      | float | Tackles per match          | tackles / match              |
| `away_tackle_aggression`      | float | Tackling style             | tackles / match              |
| `home_interception_rate`      | float | Interceptions per opp pass | interceptions / opp_passes   |
| `away_interception_rate`      | float | Reading game               | interceptions / opp_passes   |
| `home_shots_blocked_pct`      | float | Shot blocking              | shots_blocked / opp_shots    |
| `away_shots_blocked_pct`      | float | Blocking effort            | shots_blocked / opp_shots    |
| `home_aerial_dominance`       | float | Aerial win %               | aerial_won / aerial_total    |
| `away_aerial_dominance`       | float | Physical style             | aerial_won / aerial_total    |
| `home_foul_propensity`        | float | Fouls per match            | fouls / match                |
| `away_foul_propensity`        | float | Cynical style              | fouls / match                |

```python
def compute_defensive_style_features(team_id: int, prediction_time: datetime) -> dict:
    """
    Derive defensive style profile.
    """
    features = {}
    matches = get_team_matches(team_id, n=10, before=prediction_time)

    # PPDA (lower = more pressing)
    # Understat provides this directly for top 5 leagues
    if "ppda" in matches[0]:
        features["ppda_style"] = np.mean([m["ppda"] for m in matches])
    else:
        # Proxy: use tackles + interceptions per opp possession
        features["ppda_style"] = estimate_ppda(matches)

    # Defensive block height proxy
    # Low PPDA + low opp pass completion = high block
    # High PPDA + high opp pass completion = low block
    ppda = features.get("ppda_style", 10)
    opp_pass_comp = np.mean([m.get("opp_pass_accuracy", 80) for m in matches])
    features["defensive_block_height"] = (1 / ppda) * (100 - opp_pass_comp)

    # Shot blocking rate
    shots_blocked = sum(m.get("shots_blocked", 0) for m in matches)
    opp_shots = sum(m.get("opp_shots", 10) for m in matches)
    features["shots_blocked_pct"] = shots_blocked / max(opp_shots, 1)

    # Tackle aggression
    tackles = sum(m.get("tackles", 0) for m in matches)
    features["tackle_aggression"] = tackles / len(matches) if matches else 0

    # Aerial dominance
    aerial_won = sum(m.get("aerial_won", 0) for m in matches)
    aerial_total = sum(m.get("aerial_total", 1) for m in matches)
    features["aerial_dominance"] = aerial_won / max(aerial_total, 1)

    return features
```

---

#### 3.8.3 Tempo & Rhythm Profile (10 features)

| Feature                 | Type  | Description           | Derived From                      |
| ----------------------- | ----- | --------------------- | --------------------------------- |
| `home_match_tempo`      | float | Events per minute     | total_events / 90                 |
| `away_match_tempo`      | float | Game speed            | total_events / 90                 |
| `home_possession_style` | float | Possession % tendency | avg possession                    |
| `away_possession_style` | float | Possession tendency   | avg possession                    |
| `home_pass_tempo`       | float | Passes per minute     | passes / 90                       |
| `away_pass_tempo`       | float | Passing rate          | passes / 90                       |
| `home_transition_speed` | float | Quick vs slow breaks  | counter_attacks / possession_lost |
| `away_transition_speed` | float | Transition style      | counter_attacks / possession_lost |
| `home_game_control`     | float | Match dominance       | (possession + pass_accuracy) / 2  |
| `away_game_control`     | float | Match dominance       | (possession + pass_accuracy) / 2  |

```python
def compute_tempo_features(team_id: int, prediction_time: datetime) -> dict:
    """
    Derive tempo and rhythm profile.
    """
    features = {}
    matches = get_team_matches(team_id, n=10, before=prediction_time)

    # Match tempo (events per minute)
    total_events = sum(m.get("total_events", 0) for m in matches)
    minutes_played = len(matches) * 90
    features["match_tempo"] = total_events / minutes_played if minutes_played else 0

    # Possession style (consistent possession preference)
    possessions = [m["possession"] for m in matches]
    features["possession_style"] = np.mean(possessions)
    features["possession_consistency"] = (
        1 - np.std(possessions) / 50
    )  # Lower std = more consistent

    # Pass tempo
    passes = sum(m.get("passes", 0) for m in matches)
    features["pass_tempo"] = passes / minutes_played if minutes_played else 0

    # Game control composite
    pass_accuracy = np.mean([m.get("pass_accuracy", 75) for m in matches])
    features["game_control"] = (features["possession_style"] + pass_accuracy) / 2

    return features
```

---

#### 3.8.4 Style Matchup Features (8 features)

**How do the two team styles interact?**

| Feature                      | Type  | Description                      |
| ---------------------------- | ----- | -------------------------------- |
| `tempo_differential`         | float | home_tempo - away_tempo          |
| `possession_battle`          | float | Who controls the ball more       |
| `press_vs_build`             | float | high_press vs possession team    |
| `direct_vs_patient`          | float | Style contrast                   |
| `physical_mismatch`          | float | Aerial + tackle dominance diff   |
| `counter_attack_opportunity` | float | High press vs counter team       |
| `style_similarity`           | float | How similar are the styles (0-1) |
| `style_clash_score`          | float | How much styles conflict         |

```python
def compute_style_matchup_features(home_style: dict, away_style: dict) -> dict:
    """
    Compute style interaction features.
    """
    features = {}

    # Tempo differential
    features["tempo_differential"] = (
        home_style["match_tempo"] - away_style["match_tempo"]
    )

    # Possession battle
    features["possession_battle"] = (
        home_style["possession_style"] - away_style["possession_style"]
    )

    # Press vs build-up mismatch
    # High press team (low PPDA) vs possession team = interesting dynamic
    features["press_vs_build"] = (1 / home_style["ppda_style"]) * away_style[
        "possession_style"
    ]

    # Direct vs patient contrast
    features["direct_vs_patient"] = abs(
        home_style["attack_directness"] - away_style["attack_directness"]
    )

    # Physical mismatch
    features["physical_mismatch"] = (
        home_style["aerial_dominance"]
        + home_style["tackle_aggression"]
        - away_style["aerial_dominance"]
        - away_style["tackle_aggression"]
    )

    # Counter-attack opportunity
    # If away team presses high and home is counter-attacking
    features["counter_attack_opportunity"] = home_style["counter_attack_ratio"] * (
        1 / away_style["ppda_style"]
    )

    # Style similarity (cosine similarity of style vectors)
    home_vec = [home_style.get(k, 0) for k in STYLE_VECTOR_KEYS]
    away_vec = [away_style.get(k, 0) for k in STYLE_VECTOR_KEYS]
    features["style_similarity"] = cosine_similarity(home_vec, away_vec)

    # Style clash (opposite styles = higher variance match)
    features["style_clash_score"] = 1 - features["style_similarity"]

    return features


STYLE_VECTOR_KEYS = [
    "xg_per_shot",
    "possession_style",
    "ppda_style",
    "attack_directness",
    "set_piece_reliance",
    "aerial_dominance",
]
```

---

#### 3.8.5 Optional: Learned Style Embeddings

**For advanced implementation: Train autoencoder on team stats to learn latent style factors.**

```python
class TeamStyleAutoencoder(nn.Module):
    """
    Learn latent team style embeddings from observable stats.

    Input: 30 observable team stats
    Latent: 8-dimensional style embedding
    Output: Reconstruct observable stats
    """

    def __init__(self, input_dim=30, latent_dim=8):
        super().__init__()

        # Encoder: Observable stats → Latent style
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(), nn.Linear(16, latent_dim)
        )

        # Decoder: Latent style → Observable stats
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16), nn.ReLU(), nn.Linear(16, input_dim)
        )

    def encode(self, x):
        """Get style embedding for a team."""
        return self.encoder(x)

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent


def create_style_embeddings(teams_data: pd.DataFrame) -> dict:
    """
    Train autoencoder and extract style embeddings for all teams.

    Observable stats used:
    - xG/shot, shots/match, possession, PPDA, pass accuracy
    - Aerial %, tackles/match, fouls/match, crosses/match
    - Set piece xG %, counter goals %, etc.
    """
    # Prepare input features
    observable_stats = teams_data[OBSERVABLE_COLUMNS].values

    # Normalize
    scaler = StandardScaler()
    normalized = scaler.fit_transform(observable_stats)

    # Train autoencoder
    model = TeamStyleAutoencoder(input_dim=len(OBSERVABLE_COLUMNS), latent_dim=8)
    train_autoencoder(model, normalized, epochs=100)

    # Extract embeddings
    embeddings = {}
    with torch.no_grad():
        for team_id, stats in zip(teams_data["team_id"], normalized):
            latent = model.encode(torch.tensor(stats, dtype=torch.float32))
            embeddings[team_id] = latent.numpy()

    return embeddings
```

**Embedding Interpretation:**
After training, each latent dimension roughly corresponds to:

- `style_dim_0`: Possession vs Counter-attacking
- `style_dim_1`: High press vs Low block
- `style_dim_2`: Direct vs Patient build-up
- `style_dim_3`: Physical vs Technical
- `style_dim_4`: Set-piece reliance
- `style_dim_5-7`: Other latent factors

---

#### Summary: Team Style Features

| Category            | Count | Key Insight              |
| ------------------- | ----- | ------------------------ |
| **Attacking Style** | 16    | HOW teams create chances |
| **Defensive Style** | 14    | HOW teams defend         |
| **Tempo & Rhythm**  | 10    | Speed and control        |
| **Style Matchup**   | 8     | Interaction effects      |

**Total: 48 team style features**

**Why This Improves Generalization:**

```
Without Style Features:
    Team A (unknown league) has xG=1.5, possession=60%
    → Model only sees outcomes, not process

With Style Features:
    Team A: high_press=True, counter_attack_ratio=0.4, direct_style=0.7
    → Model understands this is a pressing, counter-attacking team
    → Can generalize from similar teams in other leagues
```

**Key Insight:**
Two teams with identical xG can have completely different styles:

- Team A: 1.5 xG from 15 low-quality chances (volume style)
- Team B: 1.5 xG from 5 high-quality chances (clinical style)

Style features capture this distinction.

---

### 3.9 Manager Impact & Embeddings (32 features) 🔥

**Why This Matters:**

- Manager changes dramatically alter team performance
- "New manager bounce" is well-documented (avg +0.5 PPG for 5 games)
- Different managers have distinct tactical fingerprints
- Manager-specific form ≠ team form (same team, different manager = different results)

**Data Source:** Transfermarkt (manager history), API-Football (fixtures by manager)

---

#### 3.9.1 Manager Change Detection (8 features)

| Feature                          | Type | Description                          |
| -------------------------------- | ---- | ------------------------------------ |
| `home_new_manager_flag`          | int  | 1 if manager changed in last 90 days |
| `away_new_manager_flag`          | int  | 1 if manager changed in last 90 days |
| `home_games_under_manager`       | int  | Games played under current manager   |
| `away_games_under_manager`       | int  | Games played under current manager   |
| `home_manager_honeymoon`         | int  | 1 if games_under_manager <= 5        |
| `away_manager_honeymoon`         | int  | 1 if in "new manager bounce" period  |
| `home_days_since_manager_change` | int  | Days since appointment               |
| `away_days_since_manager_change` | int  | Days since appointment               |

**The "New Manager Bounce":**

```python
# Research shows:
# Games 1-5 under new manager: +0.5 PPG vs expected
# Games 6-15: +0.2 PPG
# Games 16+: Revert to baseline (manager's true impact)


def compute_manager_change_features(team_id: int, prediction_time: datetime) -> dict:
    """
    Detect manager changes and compute impact features.
    """
    features = {}

    # Get current manager
    current_manager = get_current_manager(team_id, prediction_time)

    # When did they start?
    appointment_date = current_manager["start_date"]
    days_since = (prediction_time - appointment_date).days

    features["new_manager_flag"] = 1 if days_since <= 90 else 0
    features["days_since_manager_change"] = days_since

    # Games under this manager
    matches_under = get_matches_under_manager(
        team_id, current_manager["id"], before=prediction_time
    )
    features["games_under_manager"] = len(matches_under)

    # Honeymoon period (first 5 games)
    features["manager_honeymoon"] = 1 if len(matches_under) <= 5 else 0

    return features
```

---

#### 3.9.2 Manager Form (Rolling Under Current Manager) (10 features)

**Key insight:** Team form under THIS manager, not overall team form.

| Feature                         | Type  | Description                      |
| ------------------------------- | ----- | -------------------------------- |
| `home_manager_ppg_last5`        | float | PPG in last 5 under THIS manager |
| `away_manager_ppg_last5`        | float | PPG in last 5 under THIS manager |
| `home_manager_xg_diff_last5`    | float | xGF - xGA last 5 under manager   |
| `away_manager_xg_diff_last5`    | float | xGF - xGA last 5 under manager   |
| `home_manager_win_rate`         | float | Win % under this manager         |
| `away_manager_win_rate`         | float | Win % under this manager         |
| `home_manager_goals_per_game`   | float | Goals scored per game            |
| `away_manager_goals_per_game`   | float | Goals scored per game            |
| `home_manager_clean_sheet_rate` | float | Clean sheet % under manager      |
| `away_manager_clean_sheet_rate` | float | Clean sheet % under manager      |

```python
def compute_manager_form_features(
    team_id: int, manager_id: int, prediction_time: datetime
) -> dict:
    """
    Compute form metrics specifically under current manager.
    """
    features = {}

    # Get matches under this manager
    matches = get_matches_under_manager(team_id, manager_id, before=prediction_time)

    if len(matches) == 0:
        return default_manager_form()

    # Last 5 games under manager (or all if < 5)
    recent = matches[-5:] if len(matches) >= 5 else matches

    # PPG under manager
    points = sum(
        3 if m["result"] == "W" else 1 if m["result"] == "D" else 0 for m in recent
    )
    features["manager_ppg_last5"] = points / len(recent)

    # xG diff under manager
    xg_diff = sum(m["xgf"] - m["xga"] for m in recent) / len(recent)
    features["manager_xg_diff_last5"] = xg_diff

    # Win rate under manager (all games)
    wins = sum(1 for m in matches if m["result"] == "W")
    features["manager_win_rate"] = wins / len(matches)

    # Goals per game
    goals = sum(m["goals_for"] for m in matches)
    features["manager_goals_per_game"] = goals / len(matches)

    # Clean sheet rate
    clean_sheets = sum(1 for m in matches if m["goals_against"] == 0)
    features["manager_clean_sheet_rate"] = clean_sheets / len(matches)

    return features
```

---

#### 3.9.3 Manager Tactical Fingerprint (10 features)

**Learn manager style from their historical patterns across ALL teams they've managed.**

| Feature                        | Type  | Description                       |
| ------------------------------ | ----- | --------------------------------- |
| `home_manager_avg_possession`  | float | Career avg possession             |
| `away_manager_avg_possession`  | float | Career avg possession             |
| `home_manager_avg_ppda`        | float | Career pressing intensity         |
| `away_manager_avg_ppda`        | float | Career pressing intensity         |
| `home_manager_attack_style`    | float | xG per shot (quality vs quantity) |
| `away_manager_attack_style`    | float | xG per shot                       |
| `home_manager_defensive_style` | float | xGA per match                     |
| `away_manager_defensive_style` | float | xGA per match                     |
| `home_manager_set_piece_focus` | float | Set piece xG %                    |
| `away_manager_set_piece_focus` | float | Set piece xG %                    |

```python
def compute_manager_tactical_fingerprint(
    manager_id: int, prediction_time: datetime
) -> dict:
    """
    Compute manager's tactical fingerprint from career history.

    This looks at ALL teams the manager has coached to learn their style.
    """
    features = {}

    # Get all matches this manager has coached (across all teams)
    career_matches = get_manager_career_matches(manager_id, before=prediction_time)

    if len(career_matches) < 10:
        return default_manager_fingerprint()

    # Career averages (style fingerprint)
    features["manager_avg_possession"] = np.mean(
        [m["possession"] for m in career_matches]
    )

    # PPDA if available
    if "ppda" in career_matches[0]:
        features["manager_avg_ppda"] = np.mean([m["ppda"] for m in career_matches])

    # Attack style (xG per shot)
    total_xg = sum(m["xgf"] for m in career_matches)
    total_shots = sum(m["shots"] for m in career_matches)
    features["manager_attack_style"] = total_xg / max(total_shots, 1)

    # Defensive style (xGA per match)
    total_xga = sum(m["xga"] for m in career_matches)
    features["manager_defensive_style"] = total_xga / len(career_matches)

    # Set piece focus
    set_piece_xg = sum(m.get("set_piece_xg", 0) for m in career_matches)
    features["manager_set_piece_focus"] = set_piece_xg / max(total_xg, 0.01)

    return features
```

---

#### 3.9.4 Manager vs Manager Matchup (4 features)

| Feature                   | Type | Description                           |
| ------------------------- | ---- | ------------------------------------- |
| `manager_h2h_matches`     | int  | Times these managers faced each other |
| `manager_h2h_home_wins`   | int  | Home manager wins in H2H              |
| `manager_experience_diff` | int  | Career games difference               |
| `manager_trophy_diff`     | int  | Major trophies difference             |

```python
def compute_manager_matchup_features(
    home_manager_id: int, away_manager_id: int
) -> dict:
    """
    Compute manager vs manager matchup history.
    """
    features = {}

    # H2H between these managers
    h2h_matches = get_manager_h2h(home_manager_id, away_manager_id)
    features["manager_h2h_matches"] = len(h2h_matches)

    if h2h_matches:
        features["manager_h2h_home_wins"] = sum(
            1
            for m in h2h_matches
            if m["home_manager"] == home_manager_id and m["result"] == "H"
        )

    # Experience differential
    home_career = get_manager_career_games(home_manager_id)
    away_career = get_manager_career_games(away_manager_id)
    features["manager_experience_diff"] = home_career - away_career

    # Trophy differential (proxy for quality)
    home_trophies = get_manager_trophies(home_manager_id)
    away_trophies = get_manager_trophies(away_manager_id)
    features["manager_trophy_diff"] = home_trophies - away_trophies

    return features
```

---

#### 3.9.5 Manager Quality Tier (categorical)

| Feature             | Type | Description                          |
| ------------------- | ---- | ------------------------------------ |
| `home_manager_tier` | int  | 1=Elite, 2=Strong, 3=Average, 4=Weak |
| `away_manager_tier` | int  | Manager quality tier                 |

```python
# Pre-computed manager tiers based on career PPG, win rate, trophies
MANAGER_TIERS = {
    # Tier 1: Elite (Guardiola, Klopp, Ancelotti, etc.)
    "elite": ["guardiola", "klopp", "ancelotti", "mourinho", "conte"],
    # Tier 2: Strong (proven at top level)
    "strong": ["arteta", "ten_hag", "inzaghi", "xavi", "nagelsmann"],
    # Tier 3: Average
    "average": [...],
    # Tier 4: Weak/Unproven
    "weak": [...],
}


def get_manager_tier(manager_id: int) -> int:
    """
    Return manager quality tier (1-4).
    Computed from career PPG, win rate, and trophies.
    """
    stats = get_manager_career_stats(manager_id)

    # Scoring formula
    score = (
        stats["career_ppg"] * 40
        + stats["win_rate"] * 30
        + min(stats["trophies"], 10) * 3
    )

    if score >= 90:
        return 1  # Elite
    elif score >= 70:
        return 2  # Strong
    elif score >= 50:
        return 3  # Average
    else:
        return 4  # Weak
```

---

#### Summary: Manager Impact Features

| Category                     | Count | Key Insight                             |
| ---------------------------- | ----- | --------------------------------------- |
| **Manager Change Detection** | 8     | New manager bounce, honeymoon period    |
| **Manager Form**             | 10    | Results under THIS manager specifically |
| **Tactical Fingerprint**     | 10    | Career style patterns                   |
| **Manager Matchup**          | 4     | H2H history between managers            |

**Total: 32 manager impact features**

**Why This Is Massive:**

```
Without Manager Features:
    Team has PPG=1.8 this season
    → Model uses team form only

With Manager Features:
    Team has PPG=1.8, but new manager 3 games ago
    Manager honeymoon = 1 (expect +0.5 PPG boost)
    Manager career PPG = 2.1 (proven winner)
    Manager style = high press, possession
    → Much more predictive

Example: Chelsea fires manager, appoints elite replacement
    - Without: Model sees bad recent form, predicts low
    - With: Model sees elite new manager + honeymoon = predicts bounce
```

**Key Insight:**
Same team, same players, different manager = COMPLETELY different expected performance.

---

## 4. HT-Specific Features (~100)

### 4.1 Pre-Game Predictions as Inputs (9)

| Feature                           | Description                |
| --------------------------------- | -------------------------- |
| `pregame_pred_clv_home/draw/away` | Pre-game CLV predictions   |
| `pregame_pred_xg_home/away`       | Pre-game xG predictions    |
| `pregame_pred_h2h_home/draw/away` | Pre-game H2H probabilities |

### 4.2 First-Half State (22)

| Feature                         | Description     |
| ------------------------------- | --------------- |
| `ht_score_home/away/diff/total` | HT goals        |
| `ht_xg_home/away/diff/total`    | HT xG           |
| `ht_shots_home/away`            | HT shots        |
| `ht_shots_on_target_home/away`  | HT SOT          |
| `ht_possession_home/away`       | HT possession % |
| `ht_corners_home/away`          | HT corners      |
| `ht_fouls_home/away`            | HT fouls        |
| `ht_offsides_home/away`         | HT offsides     |
| `ht_saves_home/away`            | HT GK saves     |

### 4.3 Discipline (6)

| Feature                     | Description           |
| --------------------------- | --------------------- |
| `ht_yellow_cards_home/away` | HT yellows            |
| `ht_red_cards_home/away`    | HT reds               |
| `red_card_diff`             | Red card differential |
| `player_advantage`          | +1/-1/0 player count  |

### 4.4 HT Market (8)

| Feature                                 | Description     |
| --------------------------------------- | --------------- |
| `ht_odds_home/draw/away`                | HT odds         |
| `odds_movement_t0_to_ht_home/draw/away` | Odds change     |
| `ht_implied_prob_home/away`             | HT implied prob |

### 4.5 Performance vs Expected (10)

| Feature                          | Description                |
| -------------------------------- | -------------------------- |
| `ht_xg_vs_expected_home/away`    | HT xG vs pre-game expected |
| `ht_goals_vs_xg_home/away`       | HT over/under-performance  |
| `xg_rate_first_half_home/away`   | xG per minute              |
| `shot_rate_first_half_home/away` | Shots per minute           |
| `ht_performance_score_home/away` | Composite performance      |

---

### 4.6 First-Half SEQUENCING Features (45 features) 🔥

**Why This Is Critical:**

- HT aggregate stats don't capture TRAJECTORY within the half
- A team with 1.2 xG in first 45 could have:
  - Dominated early, faded late (momentum lost)
  - Started slow, finished strong (momentum gained)
- These are COMPLETELY different HT states with same aggregate xG

**Data Source:** API-Football events (minute-by-minute) + Soccerfootball.info progressive stats

---

#### 4.6.1 xG Temporal Dynamics (10 features)

| Feature                | Type  | Description                     |
| ---------------------- | ----- | ------------------------------- |
| `xg_first_15min_home`  | float | xG in minutes 0-15              |
| `xg_first_15min_away`  | float | xG in minutes 0-15              |
| `xg_last_15min_home`   | float | xG in minutes 30-45             |
| `xg_last_15min_away`   | float | xG in minutes 30-45             |
| `xg_acceleration_home` | float | xG_last_15 - xG_first_15 (KEY!) |
| `xg_acceleration_away` | float | xG_last_15 - xG_first_15        |
| `xg_middle_15min_home` | float | xG in minutes 15-30             |
| `xg_middle_15min_away` | float | xG in minutes 15-30             |
| `xg_trend_home`        | float | Linear trend coefficient        |
| `xg_trend_away`        | float | Linear trend coefficient        |

**Why xG Acceleration is GOLD:**

```python
# Scenario 1: Team A has 1.2 xG at HT
# xG_first_15 = 0.8, xG_last_15 = 0.2
# xg_acceleration = -0.6 (FADING, bad sign for 2H)

# Scenario 2: Team B has 1.2 xG at HT
# xG_first_15 = 0.2, xG_last_15 = 0.8
# xg_acceleration = +0.6 (BUILDING, great sign for 2H)

# Same HT xG, completely different 2H outlook!
```

```python
def compute_xg_temporal_features(fixture_id: int, events: list) -> dict:
    """
    Compute xG by time period within first half.

    events: list of {minute, type, xG, team} from API-Football + Understat
    """
    features = {}

    # Filter to first half shots with xG
    first_half_shots = [e for e in events if e["minute"] <= 45 and e["type"] == "shot"]

    home_shots = [s for s in first_half_shots if s["team"] == "home"]
    away_shots = [s for s in first_half_shots if s["team"] == "away"]

    # Time periods
    for team, shots in [("home", home_shots), ("away", away_shots)]:
        first_15 = sum(s["xG"] for s in shots if s["minute"] <= 15)
        mid_15 = sum(s["xG"] for s in shots if 15 < s["minute"] <= 30)
        last_15 = sum(s["xG"] for s in shots if 30 < s["minute"] <= 45)

        features[f"xg_first_15min_{team}"] = first_15
        features[f"xg_middle_15min_{team}"] = mid_15
        features[f"xg_last_15min_{team}"] = last_15

        # THE KEY FEATURE: xG acceleration
        features[f"xg_acceleration_{team}"] = last_15 - first_15

        # Linear trend (requires at least 3 shots)
        if len(shots) >= 3:
            minutes = [s["minute"] for s in shots]
            xgs = [s["xG"] for s in shots]
            features[f"xg_trend_{team}"] = np.polyfit(minutes, xgs, 1)[0]  # slope
        else:
            features[f"xg_trend_{team}"] = 0

    return features
```

---

#### 4.6.2 Shot Pressure Sequences (8 features)

| Feature                    | Type  | Description                         |
| -------------------------- | ----- | ----------------------------------- |
| `shots_last_10min_home`    | int   | Shots in min 35-45                  |
| `shots_last_10min_away`    | int   | Shots in min 35-45                  |
| `shots_last_5min_home`     | int   | Shots in min 40-45                  |
| `shots_last_5min_away`     | int   | Shots in min 40-45                  |
| `shot_pressure_ratio_home` | float | shots_last_10 / total_shots         |
| `shot_pressure_ratio_away` | float | shots_last_10 / total_shots         |
| `late_surge_home`          | int   | 1 if shots_last_10 > shots_first_10 |
| `late_surge_away`          | int   | 1 if shots_last_10 > shots_first_10 |

**Why Late Shot Pressure Matters:**

- Teams with high shot pressure going into HT maintain momentum
- "Finishing strong" = psychological edge + tactical working
- Late surge predicts 2H performance

```python
def compute_shot_pressure_features(events: list) -> dict:
    """
    Compute shot pressure by time windows.
    """
    features = {}

    for team in ["home", "away"]:
        team_shots = [
            e
            for e in events
            if e["team"] == team and e["type"] == "shot" and e["minute"] <= 45
        ]

        total_shots = len(team_shots)
        first_10 = len([s for s in team_shots if s["minute"] <= 10])
        last_10 = len([s for s in team_shots if s["minute"] > 35])
        last_5 = len([s for s in team_shots if s["minute"] > 40])

        features[f"shots_last_10min_{team}"] = last_10
        features[f"shots_last_5min_{team}"] = last_5
        features[f"shot_pressure_ratio_{team}"] = last_10 / max(total_shots, 1)
        features[f"late_surge_{team}"] = 1 if last_10 > first_10 else 0

    return features
```

---

#### 4.6.3 Momentum Score (Rolling 5-min windows) (8 features)

| Feature                  | Type  | Description                       |
| ------------------------ | ----- | --------------------------------- |
| `momentum_score_ht_home` | float | Weighted recent events score      |
| `momentum_score_ht_away` | float | Weighted recent events score      |
| `max_momentum_home`      | float | Peak momentum in 1H               |
| `max_momentum_away`      | float | Peak momentum in 1H               |
| `momentum_at_35_home`    | float | Momentum at min 35                |
| `momentum_at_35_away`    | float | Momentum at min 35                |
| `momentum_trend_home`    | float | Is momentum increasing/decreasing |
| `momentum_trend_away`    | float | Is momentum increasing/decreasing |

**Momentum Calculation:**

```python
def compute_momentum_score(events: list, current_minute: int = 45) -> dict:
    """
    Compute rolling momentum score based on event sequence.

    Event weights:
    - Goal: +20 (attacking team), -10 (defending team)
    - Shot on target: +3
    - Shot off target: +1
    - Corner: +2
    - Dangerous attack: +1
    - Card received: -2

    Time decay: events closer to current_minute weighted more heavily
    """
    features = {}

    WEIGHTS = {
        "goal": 20,
        "shot_on_target": 3,
        "shot": 1,
        "corner": 2,
        "dangerous_attack": 1,
        "yellow_card": -2,
        "red_card": -10,
    }

    for team in ["home", "away"]:
        # Filter events for this team
        team_events = [e for e in events if e["team"] == team and e["minute"] <= 45]

        # Compute weighted momentum (time-decayed)
        momentum = 0
        momentum_over_time = []  # For trend calculation

        for event in team_events:
            weight = WEIGHTS.get(event["type"], 0)
            time_decay = 1 / (1 + (current_minute - event["minute"]) / 10)
            momentum += weight * time_decay

            # Track momentum at each 5-min mark
            if event["minute"] % 5 == 0:
                momentum_over_time.append((event["minute"], momentum))

        features[f"momentum_score_ht_{team}"] = momentum

        # Max momentum (did they have a dominant period?)
        features[f"max_momentum_{team}"] = (
            max([m[1] for m in momentum_over_time]) if momentum_over_time else 0
        )

        # Momentum at min 35 (10 mins before HT)
        at_35 = [m for m in momentum_over_time if m[0] <= 35]
        features[f"momentum_at_35_{team}"] = at_35[-1][1] if at_35 else 0

        # Momentum trend (is it increasing?)
        if len(momentum_over_time) >= 3:
            recent = [m[1] for m in momentum_over_time[-3:]]
            features[f"momentum_trend_{team}"] = recent[-1] - recent[0]
        else:
            features[f"momentum_trend_{team}"] = 0

    return features
```

---

#### 4.6.4 Game-State Response Features (10 features)

**How teams respond when winning/losing/drawing at different points in the half**

| Feature                     | Type  | Description                                  |
| --------------------------- | ----- | -------------------------------------------- |
| `game_state_at_ht`          | int   | +1 (winning), 0 (draw), -1 (losing) for home |
| `home_response_when_behind` | float | xG after going behind / time behind          |
| `away_response_when_behind` | float | xG after going behind / time behind          |
| `home_response_when_ahead`  | float | xG after going ahead / time ahead            |
| `away_response_when_ahead`  | float | xG after going ahead / time ahead            |
| `time_in_lead_home`         | int   | Minutes home team was leading                |
| `time_in_lead_away`         | int   | Minutes away team was leading                |
| `lead_changes`              | int   | Number of lead changes in 1H                 |
| `comeback_attempted_home`   | int   | 1 if home went behind then equalized         |
| `comeback_attempted_away`   | int   | 1 if away went behind then equalized         |

**Why Game-State Response Matters:**

- Team that went behind early but created 0.8 xG while losing = fighting
- Team that went behind and created 0.2 xG while losing = capitulating
- Completely different 2H outlook even if HT aggregate similar

```python
def compute_game_state_features(events: list) -> dict:
    """
    Compute features based on game state changes and responses.
    """
    features = {}

    # Track score throughout first half
    goals = sorted(
        [e for e in events if e["type"] == "goal" and e["minute"] <= 45],
        key=lambda x: x["minute"],
    )

    score_home, score_away = 0, 0
    state_periods = []  # (start_min, end_min, state_for_home)

    last_min = 0
    for goal in goals:
        # Record period before this goal
        state = 1 if score_home > score_away else (-1 if score_home < score_away else 0)
        state_periods.append((last_min, goal["minute"], state))

        # Update score
        if goal["team"] == "home":
            score_home += 1
        else:
            score_away += 1
        last_min = goal["minute"]

    # Final period to min 45
    state = 1 if score_home > score_away else (-1 if score_home < score_away else 0)
    state_periods.append((last_min, 45, state))

    # Game state at HT
    features["game_state_at_ht"] = state

    # Time in each state
    features["time_in_lead_home"] = sum(p[1] - p[0] for p in state_periods if p[2] == 1)
    features["time_in_lead_away"] = sum(
        p[1] - p[0] for p in state_periods if p[2] == -1
    )

    # Lead changes
    features["lead_changes"] = sum(
        1
        for i in range(1, len(state_periods))
        if state_periods[i][2] != state_periods[i - 1][2]
    )

    # Response when behind (xG created while losing)
    shots = [e for e in events if e["type"] == "shot" and e["minute"] <= 45]

    for team in ["home", "away"]:
        behind_state = -1 if team == "home" else 1
        xg_when_behind = 0
        time_behind = 0

        for start, end, state in state_periods:
            if state == behind_state:
                time_behind += end - start
                # xG in this period
                period_shots = [
                    s for s in shots if s["team"] == team and start <= s["minute"] < end
                ]
                xg_when_behind += sum(s.get("xG", 0.1) for s in period_shots)

        features[f"{team}_response_when_behind"] = (
            xg_when_behind / max(time_behind, 1) * 45
        )

    # Comeback attempt
    features["comeback_attempted_home"] = (
        1
        if any(
            state_periods[i][2] == -1 and state_periods[i + 1][2] >= 0
            for i in range(len(state_periods) - 1)
        )
        else 0
    )

    return features
```

---

#### 4.6.5 Fatigue Proxy Features (5 features)

**Without GPS/tracking data, we proxy fatigue from:**

- Event frequency decline
- Substitution patterns (though rare in 1H)
- Historical team fitness data

| Feature                   | Type  | Description                    |
| ------------------------- | ----- | ------------------------------ |
| `event_rate_decline_home` | float | events_35-45 / events_0-10     |
| `event_rate_decline_away` | float | events_35-45 / events_0-10     |
| `intensity_score_home`    | float | Total events / 45 min          |
| `intensity_score_away`    | float | Total events / 45 min          |
| `high_intensity_match`    | int   | 1 if total events > league avg |

```python
def compute_fatigue_proxy_features(events: list, league_avg_events: float) -> dict:
    """
    Proxy fatigue from event frequency patterns.
    """
    features = {}

    for team in ["home", "away"]:
        team_events = [e for e in events if e["team"] == team and e["minute"] <= 45]

        # Event rate by period
        first_10_events = len([e for e in team_events if e["minute"] <= 10])
        last_10_events = len([e for e in team_events if e["minute"] > 35])

        # Decline ratio (< 1 = fading)
        features[f"event_rate_decline_{team}"] = last_10_events / max(
            first_10_events, 1
        )

        # Overall intensity
        features[f"intensity_score_{team}"] = len(team_events) / 45

    # High intensity match flag
    total_events = len([e for e in events if e["minute"] <= 45])
    features["high_intensity_match"] = 1 if total_events > league_avg_events else 0

    return features
```

---

#### 4.6.6 Danger Zone Sequences (4 features)

**Based on Soccerfootball.info progressive stats + FootyStats dangerous attacks**

| Feature                          | Type  | Description                      |
| -------------------------------- | ----- | -------------------------------- |
| `dangerous_attacks_last_10_home` | int   | Dangerous attacks min 35-45      |
| `dangerous_attacks_last_10_away` | int   | Dangerous attacks min 35-45      |
| `attack_dominance_late_home`     | float | DA_last_10 / opponent_DA_last_10 |
| `attack_dominance_late_away`     | float | DA_last_10 / opponent_DA_last_10 |

---

#### Summary: First-Half Sequencing Features

| Category                    | Count | Key Insight                         |
| --------------------------- | ----- | ----------------------------------- |
| **xG Temporal Dynamics**    | 10    | xG acceleration = finishing strong? |
| **Shot Pressure Sequences** | 8     | Late shot surge predicts 2H         |
| **Momentum Score**          | 8     | Rolling weighted event score        |
| **Game-State Response**     | 10    | How teams respond when behind/ahead |
| **Fatigue Proxies**         | 5     | Event rate decline                  |
| **Danger Zone Sequences**   | 4     | Late dangerous attacks              |

**Total: 45 first-half sequencing features**

**Why This Is Massive:**

```
Basic HT Model:
    HT_xG = 1.2 → predict 2H

Syndicate HT Model:
    HT_xG = 1.2
    xG_acceleration = +0.6 (finishing STRONG)
    momentum_score = 15 (dominating)
    shot_pressure_last_10 = 5 (sustained attack)
    game_state = -1 (losing but FIGHTING)
    → MUCH more predictive of 2H
```

**Key Insight:**
Two teams with identical HT aggregate stats can have COMPLETELY different 2H outlooks based on how the 1H unfolded.

---

## 5. Market Efficiency & Learnability Features (24 features) 🔥

**Why This Matters:**

- Not all fixtures are equally "learnable"
- Some markets are noisy, illiquid, have no price discovery
- Syndicates FILTER these out rather than bet blindly
- This is meta-modeling: knowing WHEN your model is reliable

**Use Cases:**

1. Weight predictions by confidence
2. Size bets by market quality
3. Skip matches entirely below threshold
4. Focus on highest-edge opportunities

---

### 5.1 Liquidity Score (6 features)

| Feature                   | Type  | Description                     |
| ------------------------- | ----- | ------------------------------- |
| `liquidity_score`         | float | 0-1 composite liquidity metric  |
| `bookmaker_count`         | int   | # of bookmakers offering odds   |
| `sharp_book_available`    | int   | 1 if Pinnacle/Betfair available |
| `betfair_volume_estimate` | float | Exchange volume (if available)  |
| `league_liquidity_tier`   | int   | 1=high, 2=medium, 3=low         |
| `max_stake_estimate`      | float | Estimated max bet size          |

```python
LEAGUE_LIQUIDITY_TIERS = {
    # Tier 1: High liquidity (>£100k Betfair volume typical)
    1: [
        39,
        140,
        78,
        135,
        61,
        2,
        3,
    ],  # EPL, La Liga, Bundesliga, Serie A, Ligue 1, CL, EL
    # Tier 2: Medium liquidity (£10k-100k)
    2: [
        88,
        94,
        40,
        79,
        203,
    ],  # Eredivisie, Primeira Liga, Championship, Bundesliga 2, Super Lig
    # Tier 3: Low liquidity (<£10k)
    3: [253, 106, 207, 98, 262],  # MLS, Polish, Swiss, J-League, Liga MX
}


def compute_liquidity_score(fixture_id: int, league_id: int, odds_data: dict) -> dict:
    """
    Compute market liquidity score.
    """
    features = {}

    # Number of bookmakers
    bookmaker_count = len(odds_data.get("bookmakers", []))
    features["bookmaker_count"] = bookmaker_count

    # Sharp books available?
    sharp_available = any(
        b in ["pinnacle", "betfair_ex_uk", "sbobet"]
        for b in odds_data.get("bookmakers", [])
    )
    features["sharp_book_available"] = 1 if sharp_available else 0

    # League liquidity tier
    for tier, leagues in LEAGUE_LIQUIDITY_TIERS.items():
        if league_id in leagues:
            features["league_liquidity_tier"] = tier
            break
    else:
        features["league_liquidity_tier"] = 3

    # Composite liquidity score (0-1)
    liquidity = (
        min(bookmaker_count / 10, 1) * 0.3  # More books = better
        + features["sharp_book_available"] * 0.4  # Sharp = much better
        + (4 - features["league_liquidity_tier"]) / 3 * 0.3  # Higher tier = better
    )
    features["liquidity_score"] = liquidity

    # Estimate max stake
    if features["league_liquidity_tier"] == 1:
        features["max_stake_estimate"] = 10000
    elif features["league_liquidity_tier"] == 2:
        features["max_stake_estimate"] = 2000
    else:
        features["max_stake_estimate"] = 500

    return features
```

---

### 5.2 Market Uncertainty / Entropy (18 features)

| Feature                        | Type  | Description                                |
| ------------------------------ | ----- | ------------------------------------------ |
| `market_entropy`               | float | How spread out are the probabilities       |
| `odds_stability_score`         | float | 1 - (max_move / avg_odds)                  |
| `price_discovery_score`        | float | Consensus strength                         |
| `bookmaker_agreement`          | float | 1 - std(implied_probs)                     |
| `market_confidence`            | float | Inverse of vig \* stability                |
| `closing_line_predictability`  | float | Historical CL accuracy for this league     |
| `data_completeness_score`      | float | % of features available                    |
| `corrupted_data_flag`          | int   | 1 if data issues detected                  |
| **`max_odds_home`**            | float | Best available odds for home win           |
| **`max_odds_draw`**            | float | Best available odds for draw               |
| **`max_odds_away`**            | float | Best available odds for away win           |
| **`max_odds_book_home`**       | str   | Which bookmaker offers max home odds       |
| **`pinnacle_home`**            | float | Pinnacle odds for home (sharp benchmark)   |
| **`gap_max_vs_pinnacle_home`** | float | max_odds_home - pinnacle_home              |
| **`gap_max_vs_pinnacle_draw`** | float | max_odds_draw - pinnacle_draw              |
| **`gap_max_vs_pinnacle_away`** | float | max_odds_away - pinnacle_away              |
| **`odds_range_home`**          | float | max_odds_home - min_odds_home              |
| **`soft_book_value_home`**     | float | (max_prob - pinnacle_prob) / pinnacle_prob |

```python
import numpy as np
from scipy.stats import entropy


def compute_market_uncertainty_features(
    odds_by_book: dict, odds_history: list, fixture_id: int
) -> dict:
    """
    Compute market uncertainty and stability features.

    Args:
        odds_by_book: Dict of {bookmaker: {'home': x, 'draw': y, 'away': z}}
        odds_history: List of historical odds snapshots
        fixture_id: Fixture ID
    """
    features = {}

    # ============================================================
    # MAX ODDS & PINNACLE GAP FEATURES (NEW)
    # ============================================================

    # Find max odds across all bookmakers
    home_odds = [(b, odds["home"]) for b, odds in odds_by_book.items()]
    draw_odds = [(b, odds["draw"]) for b, odds in odds_by_book.items()]
    away_odds = [(b, odds["away"]) for b, odds in odds_by_book.items()]

    if home_odds:
        max_home = max(home_odds, key=lambda x: x[1])
        min_home = min(home_odds, key=lambda x: x[1])
        features["max_odds_home"] = max_home[1]
        features["max_odds_book_home"] = max_home[0]  # Which book offers best price
        features["min_odds_home"] = min_home[1]
        features["odds_range_home"] = (
            max_home[1] - min_home[1]
        )  # Wide range = disagreement

        max_draw = max(draw_odds, key=lambda x: x[1])
        features["max_odds_draw"] = max_draw[1]
        features["odds_range_draw"] = (
            max_draw[1] - min(draw_odds, key=lambda x: x[1])[1]
        )

        max_away = max(away_odds, key=lambda x: x[1])
        features["max_odds_away"] = max_away[1]
        features["odds_range_away"] = (
            max_away[1] - min(away_odds, key=lambda x: x[1])[1]
        )

    # Pinnacle as sharp benchmark
    pinnacle_odds = odds_by_book.get(
        "pinnacle", odds_by_book.get("pinnacle_sports", {})
    )
    if pinnacle_odds:
        features["pinnacle_home"] = pinnacle_odds.get("home")
        features["pinnacle_draw"] = pinnacle_odds.get("draw")
        features["pinnacle_away"] = pinnacle_odds.get("away")

        # Gap between max odds and Pinnacle (sharp benchmark)
        # Positive gap = soft book offering better than sharp = potential value
        features["gap_max_vs_pinnacle_home"] = (
            features.get("max_odds_home", 0) - features["pinnacle_home"]
        )
        features["gap_max_vs_pinnacle_draw"] = (
            features.get("max_odds_draw", 0) - features["pinnacle_draw"]
        )
        features["gap_max_vs_pinnacle_away"] = (
            features.get("max_odds_away", 0) - features["pinnacle_away"]
        )

        # Soft book value as percentage of Pinnacle
        # If max_implied_prob > pinnacle_prob, there's "soft book value"
        pinnacle_prob_home = 1 / features["pinnacle_home"]
        max_prob_home = 1 / features.get("max_odds_home", features["pinnacle_home"])
        features["soft_book_value_home"] = (
            pinnacle_prob_home - max_prob_home
        ) / pinnacle_prob_home
        # Positive value = max odds is higher than Pinnacle (soft book giving value)
    else:
        # No Pinnacle available - use market average as proxy
        features["pinnacle_home"] = None
        features["gap_max_vs_pinnacle_home"] = None
        features["soft_book_value_home"] = None

    # ============================================================
    # ENTROPY & STABILITY FEATURES
    # ============================================================

    # Market entropy (how uncertain is the market?)
    all_probs = []
    for book, odds in odds_by_book.items():
        probs = [1 / odds["home"], 1 / odds["draw"], 1 / odds["away"]]
        probs = [p / sum(probs) for p in probs]  # Normalize
        all_probs.extend(probs)

    if all_probs:
        avg_probs = [
            np.mean(all_probs[::3]),
            np.mean(all_probs[1::3]),
            np.mean(all_probs[2::3]),
        ]
        features["market_entropy"] = entropy(avg_probs, base=2)

    # Odds stability (how much have odds moved?)
    if len(odds_history) >= 2:
        max_move = max(
            abs(h["prob_home"] - odds_history[0]["prob_home"]) for h in odds_history
        )
        avg_odds = np.mean([h["prob_home"] for h in odds_history])
        features["odds_stability_score"] = 1 - min(max_move / avg_odds, 1)
    else:
        features["odds_stability_score"] = 0.5

    # Bookmaker agreement (low std = consensus)
    home_probs = [1 / odds_by_book[b]["home"] for b in odds_by_book]
    if len(home_probs) >= 2:
        features["bookmaker_agreement"] = 1 - min(np.std(home_probs) * 10, 1)
    else:
        features["bookmaker_agreement"] = 0.5

    # Price discovery score (composite)
    features["price_discovery_score"] = (
        features["odds_stability_score"] * 0.4
        + features["bookmaker_agreement"] * 0.4
        + (1 - features["market_entropy"] / 1.58) * 0.2
    )

    # Data completeness
    expected_features = ["shots", "xg", "possession", "corners", "odds"]
    match_data = get_fixture_data(fixture_id)
    available = sum(
        1 for f in expected_features if f in match_data and match_data[f] is not None
    )
    features["data_completeness_score"] = available / len(expected_features)

    # Corrupted data detection
    features["corrupted_data_flag"] = detect_data_corruption(fixture_id)

    return features


def detect_data_corruption(fixture_id: int) -> int:
    """
    Detect potential data quality issues.
    """
    issues = 0
    data = get_fixture_data(fixture_id)

    # Impossible values
    if data.get("possession_home", 50) + data.get("possession_away", 50) != 100:
        issues += 1

    # Missing critical data
    if data.get("shots") is None and data.get("xg") is None:
        issues += 1

    # Odds outside reasonable range
    odds = data.get("odds", {})
    if any(o < 1.01 or o > 100 for o in odds.values() if o):
        issues += 1

    return 1 if issues > 0 else 0
```

---

### 5.3 Learnability Score (6 features)

| Feature                     | Type  | Description                                      |
| --------------------------- | ----- | ------------------------------------------------ |
| `learnability_score`        | float | 0-1 overall fixture learnability                 |
| `historical_clv_accuracy`   | float | Model's past CLV performance on similar fixtures |
| `league_model_r2`           | float | Model R² for this league historically            |
| `feature_reliability_score` | float | How reliable are the input features              |
| `skip_fixture_flag`         | int   | 1 if fixture should be skipped                   |
| `bet_size_multiplier`       | float | Suggested bet size scaling (0-1)                 |

```python
def compute_learnability_score(
    fixture_id: int,
    league_id: int,
    liquidity_features: dict,
    uncertainty_features: dict,
    historical_performance: dict,
) -> dict:
    """
    Compute overall fixture learnability score.

    This tells us how much to trust our prediction.
    """
    features = {}

    # Historical model performance for this league
    league_perf = historical_performance.get(league_id, {})
    features["historical_clv_accuracy"] = league_perf.get("clv_accuracy", 0.5)
    features["league_model_r2"] = league_perf.get("r2_score", 0.3)

    # Feature reliability (data quality + completeness)
    features["feature_reliability_score"] = (
        uncertainty_features["data_completeness_score"] * 0.5
        + (1 - uncertainty_features["corrupted_data_flag"]) * 0.3
        + liquidity_features["sharp_book_available"] * 0.2
    )

    # COMPOSITE LEARNABILITY SCORE
    features["learnability_score"] = (
        liquidity_features["liquidity_score"] * 0.25
        + uncertainty_features["price_discovery_score"] * 0.25
        + features["feature_reliability_score"] * 0.25
        + features["historical_clv_accuracy"] * 0.25
    )

    # Skip fixture flag (too noisy to bet)
    skip_conditions = [
        liquidity_features["liquidity_score"] < 0.3,
        uncertainty_features["bookmaker_agreement"] < 0.4,
        uncertainty_features["corrupted_data_flag"] == 1,
        features["feature_reliability_score"] < 0.5,
        liquidity_features["sharp_book_available"] == 0
        and liquidity_features["league_liquidity_tier"] == 3,
    ]
    features["skip_fixture_flag"] = 1 if any(skip_conditions) else 0

    # Bet size multiplier (scale down bets for uncertain fixtures)
    if features["skip_fixture_flag"]:
        features["bet_size_multiplier"] = 0.0
    else:
        features["bet_size_multiplier"] = (
            features["learnability_score"] ** 0.5
        )  # Square root scaling

    return features
```

---

### 5.4 Volatility-Adjusted Expected Value (4 features)

| Feature                    | Type  | Description                    |
| -------------------------- | ----- | ------------------------------ |
| `raw_edge`                 | float | Predicted prob - market prob   |
| `volatility_adjusted_edge` | float | Edge adjusted for market noise |
| `expected_clv`             | float | Expected closing line value    |
| `risk_adjusted_ev`         | float | EV / volatility (Sharpe-like)  |

```python
def compute_volatility_adjusted_ev(
    predicted_prob: float,
    market_prob: float,
    learnability_score: float,
    market_volatility: float,
) -> dict:
    """
    Compute volatility-adjusted expected value.

    Raw edge is naive. Adjusted edge accounts for market noise.
    """
    features = {}

    # Raw edge
    raw_edge = predicted_prob - market_prob
    features["raw_edge"] = raw_edge

    # Volatility adjustment
    # In noisy markets, our edge estimate is less reliable
    # Shrink edge toward zero based on learnability
    features["volatility_adjusted_edge"] = raw_edge * learnability_score

    # Expected CLV (how much we expect to beat closing line)
    # CLV = (predicted_prob - closing_prob) / closing_prob
    # We estimate based on historical model performance
    features["expected_clv"] = (
        features["volatility_adjusted_edge"] * 0.7
    )  # ~70% of edge realized

    # Risk-adjusted EV (Sharpe-like metric)
    # EV / volatility = edge per unit risk
    if market_volatility > 0:
        features["risk_adjusted_ev"] = (
            features["volatility_adjusted_edge"] / market_volatility
        )
    else:
        features["risk_adjusted_ev"] = features["volatility_adjusted_edge"]

    return features
```

---

### Summary: Market Efficiency Features

| Category                   | Count | Key Insight                                                  |
| -------------------------- | ----- | ------------------------------------------------------------ |
| **Liquidity Score**        | 6     | Can we actually bet this?                                    |
| **Market Uncertainty**     | 18    | Is the market stable/confident? **+ max odds, Pinnacle gap** |
| **Learnability Score**     | 6     | How reliable is our prediction?                              |
| **Volatility-Adjusted EV** | 4     | What's our TRUE edge after noise?                            |

**Total: 34 market efficiency features**

**Why This Is How Syndicates Filter:**

```
Without Efficiency Filtering:
    Bet on all fixtures equally
    → Noisy fixtures dilute edge
    → Variance is high
    → Bankroll swings wildly

With Efficiency Filtering:
    learnability_score < 0.4 → SKIP
    liquidity_score < 0.3 → SKIP
    corrupted_data_flag = 1 → SKIP

    Good fixtures:
        bet_size = base_stake * bet_size_multiplier
        → Focus capital on highest-quality opportunities
        → Lower variance
        → Better risk-adjusted returns
```

**Example:**

```
Fixture A: EPL match
    liquidity_score = 0.9
    learnability_score = 0.85
    raw_edge = 3%
    volatility_adjusted_edge = 2.55%
    bet_size_multiplier = 0.92
    → FULL BET

Fixture B: Polish Ekstraklasa
    liquidity_score = 0.4
    learnability_score = 0.45
    raw_edge = 5%
    volatility_adjusted_edge = 2.25%
    bet_size_multiplier = 0.67
    → REDUCED BET (⅔ stake)

Fixture C: Moldovan Liga
    liquidity_score = 0.2
    learnability_score = 0.3
    raw_edge = 8%
    skip_fixture_flag = 1
    → NO BET (too noisy despite apparent edge)
```

---

## 6. Derived Features (~35)

### 6.1 Momentum Features (8)

| Feature                 | Description                |
| ----------------------- | -------------------------- |
| `home_xg_momentum`      | last5_xg - season_xg       |
| `away_xg_momentum`      | last5_xg - season_xg       |
| `home_goals_momentum`   | last5_goals - season_goals |
| `away_goals_momentum`   | last5_goals - season_goals |
| `home_form_trend`       | PPG change last5 vs prev5  |
| `away_form_trend`       | PPG change last5 vs prev5  |
| `home_possession_trend` | Possession change          |
| `away_possession_trend` | Possession change          |

### 5.2 Relative Features (10)

| Feature                         | Description             |
| ------------------------------- | ----------------------- |
| `xg_vs_league_avg_home`         | home_xg / league_avg    |
| `xg_vs_league_avg_away`         | away_xg / league_avg    |
| `goals_vs_league_avg_home`      | goals / league_avg      |
| `goals_vs_league_avg_away`      | goals / league_avg      |
| `possession_vs_league_avg_home` | possession / league_avg |
| `possession_vs_league_avg_away` | possession / league_avg |
| `shots_vs_league_avg_home`      | shots / league_avg      |
| `shots_vs_league_avg_away`      | shots / league_avg      |
| `xi_value_vs_league_avg`        | xi_value / league_avg   |
| `elo_vs_league_avg`             | elo / league_avg        |

### 5.3 Rolling EWMA Features (10)

| Feature                    | Description                |
| -------------------------- | -------------------------- |
| `home_xg_ewma_30d`         | EWMA xG (30 day half-life) |
| `away_xg_ewma_30d`         | EWMA xG (30 day half-life) |
| `home_xg_ewma_90d`         | EWMA xG (90 day half-life) |
| `away_xg_ewma_90d`         | EWMA xG (90 day half-life) |
| `home_goals_ewma_30d`      | EWMA goals (30 day)        |
| `away_goals_ewma_30d`      | EWMA goals (30 day)        |
| `home_possession_ewma_30d` | EWMA possession            |
| `away_possession_ewma_30d` | EWMA possession            |
| `home_goals_std_last10`    | Volatility (std dev)       |
| `away_goals_std_last10`    | Volatility (std dev)       |

### 5.4 Interaction Features (7)

| Feature                   | Description                  |
| ------------------------- | ---------------------------- |
| `xg_x_elo_home`           | xg \* elo / 1000             |
| `xg_x_elo_away`           | xg \* elo / 1000             |
| `weather_x_style`         | bad_weather \* set_piece_pct |
| `referee_x_discipline`    | referee_cards \* team_fouls  |
| `form_x_xi_strength_home` | ppg \* xi_value              |
| `form_x_xi_strength_away` | ppg \* xi_value              |
| `possession_x_xg_home`    | possession \* xg             |

---

## 6. Player-Level Feature Attribution

**See `PLAYER_PROFILES.md` for complete documentation on player attributes, aggregation strategies, and lineup handling.**

### 6.1 The Problem

We have player-level stats (goals, assists, xG/90, ratings), but models need team-level features. How do we attribute players to a game?

### 6.2 Strategy: Aggregate by Confirmed Lineup

**Key Principle:** We do NOT have a column per player (variable roster sizes, sparse data). Instead, we **aggregate player stats for the confirmed XI**.

**For detailed player profile system, see `PLAYER_PROFILES.md` §2-3.**

```python
def compute_lineup_features(fixture_id: int, lineup_type: str = "confirmed") -> dict:
    """
    Aggregate player features for the starting XI.

    Args:
        fixture_id: Fixture to compute features for
        lineup_type: 'expected' (T-24h) or 'confirmed' (T-1h)

    Returns:
        Aggregated features dict
    """
    # Get starting XI player IDs
    lineup = get_lineup(fixture_id, lineup_type)
    home_xi_ids = lineup["home"]["startXI"]  # List of 11 player_ids
    away_xi_ids = lineup["away"]["startXI"]

    # Get player stats (season-to-date, before this match)
    home_players = get_player_stats(home_xi_ids, prediction_time)
    away_players = get_player_stats(away_xi_ids, prediction_time)

    features = {}

    # Aggregate by SUM (total output)
    features["home_xi_goals_season"] = home_players["goals"].sum()
    features["home_xi_assists_season"] = home_players["assists"].sum()
    features["away_xi_goals_season"] = away_players["goals"].sum()
    features["away_xi_assists_season"] = away_players["assists"].sum()

    # Aggregate by MEAN (average quality)
    features["home_xi_avg_rating"] = home_players["rating"].mean()
    features["away_xi_avg_rating"] = away_players["rating"].mean()
    features["home_xi_xg_per90_avg"] = home_players["xg_per90"].mean()
    features["away_xi_xg_per90_avg"] = away_players["xg_per90"].mean()
    features["home_xi_avg_age"] = home_players["age"].mean()

    # DEFENSIVE AGGREGATES
    features["home_xi_tackles_per90_avg"] = home_players["tackles_per90"].mean()
    features["away_xi_tackles_per90_avg"] = away_players["tackles_per90"].mean()
    features["home_xi_interceptions_per90_avg"] = home_players[
        "interceptions_per90"
    ].mean()
    features["away_xi_interceptions_per90_avg"] = away_players[
        "interceptions_per90"
    ].mean()
    features["home_xi_aerial_won_pct"] = home_players["aerial_won"].sum() / max(
        home_players["aerial_total"].sum(), 1
    )
    features["away_xi_aerial_won_pct"] = away_players["aerial_won"].sum() / max(
        away_players["aerial_total"].sum(), 1
    )

    # Aggregate by SUM (total value)
    features["home_xi_total_value"] = home_players["market_value"].sum()
    features["away_xi_total_value"] = away_players["market_value"].sum()

    # Weighted by position (attackers matter more for xG)
    attackers_home = home_players[home_players["position"].isin(["FW", "AM"])]
    features["home_xi_attack_xg_avg"] = (
        attackers_home["xg_per90"].mean() if len(attackers_home) > 0 else 0
    )

    return features
```

### 6.3 Key Absentees Detection

```python
def compute_key_absentees(
    team_id: int, lineup: list, prediction_time: datetime
) -> dict:
    """
    Identify key players missing from lineup.

    Key player = Top 5 by minutes played this season.
    """
    # Get team's regular players (by minutes)
    season_players = get_season_minutes(team_id, prediction_time)
    key_players = season_players.nlargest(5, "minutes")["player_id"].tolist()

    # Check who's missing
    missing = [p for p in key_players if p not in lineup]

    features = {}
    features["key_absentees_count"] = len(missing)

    # Get value of missing players
    missing_data = get_player_data(missing)
    features["value_lost_to_injury"] = missing_data["market_value"].sum()

    return features
```

### 6.4 Lineup Stability

```python
def compute_lineup_stability(
    team_id: int, current_xi: list, prediction_time: datetime
) -> float:
    """
    Compute overlap between current XI and last 5 starting XIs.

    Returns: float 0-1 (1 = same XI every game)
    """
    # Get last 5 lineups
    last_5_lineups = get_recent_lineups(team_id, n=5, before=prediction_time)

    if len(last_5_lineups) == 0:
        return 0.5  # Default if no history

    # Count players appearing in each lineup
    stability_scores = []
    for past_xi in last_5_lineups:
        overlap = len(set(current_xi) & set(past_xi))
        stability_scores.append(overlap / 11)

    return np.mean(stability_scores)
```

### 6.5 Why NOT Per-Player Columns?

| Approach                 | Problem                                |
| ------------------------ | -------------------------------------- |
| 22 columns (11 per team) | Rosters change, column order arbitrary |
| Column per player ID     | Thousands of columns, very sparse      |
| One-hot encoding         | Extremely high dimensionality          |

**Solution:** Aggregate to fixed-size feature vector (XI strength, goals, assists, value, etc.)

---

## 7. Feature Encoding

### 7.1 Model-Specific Requirements

| Model       | Scaling        | Categorical  |
| ----------- | -------------- | ------------ |
| CatBoost    | Not needed     | Native       |
| XGBoost     | Not needed     | Label encode |
| LightGBM    | Not needed     | Native       |
| Huber       | StandardScaler | One-hot      |
| Poisson GLM | StandardScaler | One-hot      |
| Ridge       | StandardScaler | One-hot      |

### 7.2 Categorical Features

```python
CATEGORICAL_FEATURES = [
    "home_formation",
    "away_formation",
    "home_form_string",
    "away_form_string",
    "h2h_last_result",
    "home_prev_result",
    "away_prev_result",
    "temp_band",
    "wind_band",
    "referee_card_rate_band",
    "venue_surface",
]
```

---

## 8. Feature Computation

### 8.1 Pre-Game Features

```python
def compute_pregame_features(fixture_id: str, prediction_time: datetime) -> pd.Series:
    """Compute all pre-game features."""
    home_team, away_team = get_teams(fixture_id)

    features = {}

    # Market features
    features.update(compute_market_features(fixture_id, prediction_time))

    # Rolling team performance (MULTIPLE WINDOWS, ALL COMPETITIONS)
    for window in ["last1", "last3", "last5", "last10", "season"]:
        features.update(
            compute_team_rolling_features(home_team, "home", window, prediction_time)
        )
        features.update(
            compute_team_rolling_features(away_team, "away", window, prediction_time)
        )

    # EWMA with previous season prior
    features.update(compute_ewma_features(home_team, "home", prediction_time))
    features.update(compute_ewma_features(away_team, "away", prediction_time))

    # H2H historical
    features.update(compute_h2h_features(home_team, away_team, prediction_time))

    # Previous game details
    features.update(compute_prev_game_features(home_team, "home", prediction_time))
    features.update(compute_prev_game_features(away_team, "away", prediction_time))

    # Lineup features (aggregate player stats INCLUDING DEFENSIVE)
    lineup_type = "confirmed" if is_t1h(prediction_time) else "expected"
    features.update(compute_lineup_features(fixture_id, lineup_type))
    features.update(compute_defensive_player_aggregates(fixture_id, lineup_type))

    # Season state features (crossover handling)
    features.update(compute_season_state_features(fixture_id, prediction_time))

    # Context
    features.update(compute_context_features(fixture_id, prediction_time))

    # Poisson priors
    features.update(compute_poisson_features(home_team, away_team, prediction_time))

    # Derived
    features.update(compute_derived_features(features))

    return pd.Series(features)
```

### 8.2 Rolling Feature Computation

```python
def compute_team_rolling_features(
    team_id: int, venue_side: str, window: str, prediction_time: datetime
) -> dict:
    """
    Compute rolling features for a team.

    Args:
        team_id: Team to compute for
        venue_side: 'home' or 'away' - filter matches accordingly
        window: 'last1', 'last3', 'last5', 'last10', 'season'
        prediction_time: Cutoff time (anti-leakage)
    """
    # Get team's matches where they played at the specified venue
    if venue_side == "home":
        matches = get_team_home_matches(team_id, before=prediction_time)
    else:
        matches = get_team_away_matches(team_id, before=prediction_time)

    # Sort by date descending
    matches = matches.sort_values("kickoff_utc", ascending=False)

    # Apply window
    if window == "last1":
        matches = matches.head(1)
    elif window == "last3":
        matches = matches.head(3)
    elif window == "last5":
        matches = matches.head(5)
    elif window == "last10":
        matches = matches.head(10)
    # 'season' = all matches in current season (already filtered)

    prefix = f"{venue_side}_{window}" if window != "season" else f"{venue_side}_season"

    features = {}

    if len(matches) > 0:
        # Goals
        features[f"{prefix}_goals"] = matches["goals_scored"].mean()
        features[f"{prefix}_goals_conceded"] = matches["goals_conceded"].mean()

        # xG
        features[f"{prefix}_xg"] = matches["xg"].mean()
        features[f"{prefix}_xga"] = matches["xga"].mean()

        # Possession
        features[f"{prefix}_possession"] = matches["possession"].mean()

        # Shots
        features[f"{prefix}_shots"] = matches["shots"].mean()
        features[f"{prefix}_sot_pct"] = (
            matches["shots_on_target"] / matches["shots"].replace(0, 1)
        ).mean()

        # PPG
        features[f"{prefix}_ppg"] = matches["points"].mean()
    else:
        # Fill with league averages if no data
        features[f"{prefix}_goals"] = 1.3
        features[f"{prefix}_xg"] = 1.2
        # ... etc

    return features
```

---

## 9. Timestamp Discipline

### 9.1 Golden Rules

1. **Rolling features:** `match_kickoff < prediction_time`
2. **Lineups:** Expected at T-24h, Confirmed at T-1h
3. **Odds:** T-72h/T-24h snapshots for early features, T-90m through T-10m for pre-match granularity, T-0 for closing odds, HT-2min for HT model
4. **H2H:** Only matches with `kickoff < prediction_time`
5. **Player stats:** Season-to-date before the match
6. **Weather:** Forecast, not actual

### 9.2 Validation

```python
def validate_features(features_df, fixtures_df):
    """Validate no lookahead bias."""

    for idx, row in features_df.iterrows():
        fixture = fixtures_df[fixtures_df["fixture_id"] == row["fixture_id"]].iloc[0]
        prediction_time = row["prediction_time"]
        kickoff = fixture["kickoff_utc"]

        # Check rolling features used correct cutoff
        assert prediction_time <= kickoff, "Features computed after kickoff"

        # Check H2H matches are historical
        # (would need to trace back to source data)

        # Check lineup type matches prediction horizon
        if row["feature_horizon"] == "T-24h":
            assert row["lineup_type"] == "expected"
        elif row["feature_horizon"] == "T-1h":
            assert row["lineup_type"] == "confirmed"

    return True
```

---

## Summary

This document defines **~738 features** across:

- **Market (123):** Odds, spreads, totals, **price dynamics (45)**, **market structure/efficiency (28)**, potentials
- **Team Performance Rolling (60):** Goals, xG, possession, shots across multiple windows
- **H2H Historical (20):** Full matchup history between teams
- **Previous Game (12):** Last game details
- **Lineup/Player (69):** XI aggregates, absentees, **position-level quality, depth charts, formation**
- **Season State (8):** Early season flags, games played, manager changes
- **Promoted Teams & Fresh Season (57):** Team prior embeddings, league normalization, decay-weighted priors, history depth
- **Context (81):** Referee-team interactions (22), weather, **schedule/travel/fatigue (28)**, venue
- **Bayesian Poisson (42):** Shrinkage, uncertainty intervals, **market-implied λ blend**
- **Multi-Source xG (36):** Understat + Soccerfootball + FootyStats (3 labeled sources), **xG disagreement features**
- **Synthetic xG (18):** xG estimates for non-Understat leagues, **unified xG fallback**
- **Team Style (48):** Attacking/defensive style, tempo, **style matchup interactions**
- **Manager Impact (32):** Change detection, form, **tactical fingerprint, honeymoon effect**
- **Market Efficiency (34):** Liquidity, learnability, **max odds, Pinnacle gap, soft book value, volatility-adjusted EV, skip flags**
- **HT-Specific (100):** First-half state, market, performance, **SEQUENCING (45)**
- **Derived (35):** Momentum, relative, EWMA, interactions

**Key Features Addressed:**

1. ✅ Multiple rolling windows (last1, last3, last5, last10, season)
2. ✅ Home/away splits for all rolling features
3. ✅ Comprehensive possession features
4. ✅ Extensive H2H historical features (20 features)
5. ✅ Previous game detailed stats
6. ✅ Player attribution strategy (aggregate XI, not per-player columns)
7. ✅ EWMA with **previous season as prior** (no cold-start problem)
8. ✅ **Cross-competition data** (league + cup + international in rolling features)
9. ✅ **Season crossover features** (early season flags, games played, manager changes)
10. ✅ **Defensive player stats** (tackles, interceptions, aerial duels, height)
11. ✅ **Lineup availability tracking** (T-24h fallback vs T-1h confirmed XI)
12. ✅ **Backtesting lineup strategy** (reconstruct predicted XI from historical data)
13. ✅ **Categorical features for trees** (league, manager, referee, region for variance reduction)
14. ✅ **Position-level quality** (DEF/MID/FWD line ratings, not just total XI)
15. ✅ **Depth chart modeling** (who replaces injured #1? quality drop estimation)
16. ✅ **Key player impact** (top scorer/assister in XI flags)
17. ✅ **Formation intelligence** (attacking ratio, differs from usual)
18. ✅ **Price dynamics (45 features)** - odds velocity, acceleration, path volatility
19. ✅ **Bookmaker microstructure** - who moves first, Pinnacle lead, Asian vs European
20. ✅ **Steam/sharp detection** - sudden moves, reverse line movement
21. ✅ **Book fragmentation** - disagreement between bookmakers as signal
22. ✅ **Sharp vs Soft separation** - sharp_soft_delta as leading indicator
23. ✅ **League efficiency scores** - tier 1-5 market quality by league
24. ✅ **Bookmaker weighting** - weight sharp opinions higher than recreational
25. ✅ **First-half SEQUENCING (45)** - xG acceleration, momentum, game-state response
26. ✅ **Shot pressure sequences** - late surge detection, attack dominance
27. ✅ **Fatigue proxies** - event rate decline as stamina indicator
28. ✅ **Team style embeddings (48)** - attacking/defensive style, tempo, rhythm
29. ✅ **Style matchup features** - press vs build-up, counter opportunity
30. ✅ **Optional autoencoder** - learned latent style factors for generalization
31. ✅ **Manager change detection** - honeymoon effect (+0.5 PPG for 5 games)
32. ✅ **Manager form** - rolling PPG/xG under THIS manager specifically
33. ✅ **Manager tactical fingerprint** - career style patterns from all teams managed
34. ✅ **Referee-team card patterns** - team-specific cards under specific refs
35. ✅ **Referee historical bias** - some refs favor certain teams
36. ✅ **Penalty × attacking style** - pen-happy ref × high-press team = more pens
37. ✅ **Schedule congestion** - 3 games in 8 days = ~0.3 xG penalty
38. ✅ **Travel fatigue** - total km traveled in 14 days, flight distance
39. ✅ **Continental hangover** - midweek European away = massive impact
40. ✅ **Bayesian Poisson updating** - Gamma-Poisson conjugate with uncertainty
41. ✅ **League-specific shrinkage** - minor leagues need stronger priors
42. ✅ **Market-implied λ blend** - weight xG vs market based on confidence
43. ✅ **Synthetic xG model** - trained on Understat, applied to all 35 leagues
44. ✅ **Unified xG features** - consistent xG across all leagues (not just top 5)
45. ✅ **Liquidity scoring** - filter out illiquid markets
46. ✅ **Learnability score** - know when model is reliable vs noisy
47. ✅ **Volatility-adjusted EV** - shrink edge toward zero in uncertain markets
48. ✅ **Skip fixture flags** - don't bet on unlearnable matches
49. ✅ **Max odds across books** - find best available price
50. ✅ **Pinnacle gap** - gap between max odds and sharp benchmark
51. ✅ **Soft book value** - identify where soft books give edge vs sharp
52. ✅ **T-24h early market** - captures opening line and early sharp action
53. ✅ **T-20m granularity** - better resolution in final pre-match window
54. ✅ **HT-2min snapshot** - odds 2 minutes before second half (HT model target)
55. ✅ **Bet selection engine** - league-specific thresholds, dynamic edge filtering
56. ✅ **Fractional Kelly** - optimal sizing with risk modifiers
57. ✅ **Drift detection** - KS test, calibration monitoring, CLV-profit correlation
58. ✅ **Multi-model arbitration** - context-aware ensemble weighting
59. ✅ **Market simulation** - synthetic odds path simulation for timing
60. ✅ **Arb bucket classification** - Soft→Sharp (0.2-0.6%), Soft→Soft (0.4-1.2%), Soft→Exchange (0.5-1.5%)
61. ✅ **Multi-source xG** - Understat, Soccerfootball, FootyStats (3 labeled sources)
62. ✅ **xG disagreement features** - When sources disagree = signal of uncertainty
63. ✅ **xG source priority** - Understat > Soccerfootball > FootyStats > Synthetic
