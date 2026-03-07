# Player Profiles & Lineup Strength Prediction

**Purpose:** Define player profile system for starting XI and bench strength predictions.

**Related Documents:**

- `FEATURE_ENGINEERING.md` - Feature definitions (see §3.5, §6)
- `reference_data_spec.md` - Stage 1 canonical keys + provider ID mappings (join layer)
- `raw_data_spec.md` - Stage 2 raw download spec + provider field appendix
- `LEAGUE_CLASSIFICATION.md` - League types and data requirements

**Version:** 1.0 **Last Updated:** December 2024

---

## Table of Contents

1. [Overview](#1-overview)
2. [Player Attributes](#2-player-attributes)
3. [Starting XI Aggregation](#3-starting-xi-aggregation)
4. [Bench Strength](#4-bench-strength)
5. [Expected vs Confirmed Lineups](#5-expected-vs-confirmed-lineups)
6. [Lineup Availability Handling](#6-lineup-availability-handling)
7. [Player Data Sources](#7-player-data-sources)
8. [Implementation](#8-implementation)

---

## 1. Overview

### 1.1 Key Principle

**We do NOT have a column per player** (variable roster sizes, sparse data). Instead, we **aggregate player stats for
the confirmed XI** into fixed-size feature vectors.

### 1.2 Why Aggregation?

| Approach                 | Problem                                |
| ------------------------ | -------------------------------------- |
| 22 columns (11 per team) | Rosters change, column order arbitrary |
| Column per player ID     | Thousands of columns, very sparse      |
| One-hot encoding         | Extremely high dimensionality          |

**Solution:** Aggregate to fixed-size feature vector (XI strength, goals, assists, value, etc.)

### 1.3 Use Cases

1. **Pre-Game Predictions (T-24h, T-1h):**
   - Expected XI strength (when lineup not confirmed)
   - Confirmed XI strength (when lineup available)
   - Key absentees impact

2. **Bench Strength:**
   - Substitution quality
   - Squad depth
   - Rotation capability

3. **Promoted Teams / New Squads:**
   - Player-level aggregation when squad turnover >40%
   - Team strength from player quality

---

## 2. Player Attributes

### 2.1 Core Player Attributes

**From API-Football:**

| Attribute     | Type   | Description                  | Source       |
| ------------- | ------ | ---------------------------- | ------------ |
| `player_id`   | int    | Unique player identifier     | API-Football |
| `name`        | string | Player name                  | API-Football |
| `position`    | string | Position (GK, DEF, MID, FWD) | API-Football |
| `age`         | int    | Player age                   | API-Football |
| `nationality` | string | Country                      | API-Football |
| `height`      | int    | Height in cm                 | API-Football |
| `weight`      | int    | Weight in kg                 | API-Football |
| `injured`     | bool   | Currently injured            | API-Football |
| `suspended`   | bool   | Currently suspended          | API-Football |

**From API-Football Player Statistics:**

| Attribute               | Type  | Description          | Window         |
| ----------------------- | ----- | -------------------- | -------------- |
| `goals`                 | int   | Goals scored         | Season-to-date |
| `assists`               | int   | Assists              | Season-to-date |
| `minutes`               | int   | Minutes played       | Season-to-date |
| `rating`                | float | Average match rating | Season-to-date |
| `shots_total`           | int   | Total shots          | Season-to-date |
| `shots_on_target`       | int   | Shots on target      | Season-to-date |
| `passes_total`          | int   | Total passes         | Season-to-date |
| `passes_accuracy`       | float | Pass accuracy %      | Season-to-date |
| `tackles_total`         | int   | Total tackles        | Season-to-date |
| `tackles_interceptions` | int   | Interceptions        | Season-to-date |
| `duels_total`           | int   | Total duels          | Season-to-date |
| `duels_won`             | int   | Duels won            | Season-to-date |
| `dribbles_attempts`     | int   | Dribble attempts     | Season-to-date |
| `dribbles_success`      | int   | Successful dribbles  | Season-to-date |
| `fouls_committed`       | int   | Fouls committed      | Season-to-date |
| `cards_yellow`          | int   | Yellow cards         | Season-to-date |
| `cards_red`             | int   | Red cards            | Season-to-date |

**From Transfermarkt:**

| Attribute          | Type  | Description             | Source        |
| ------------------ | ----- | ----------------------- | ------------- |
| `market_value`     | float | Market value (EUR)      | Transfermarkt |
| `contract_expires` | date  | Contract expiry         | Transfermarkt |
| `transfer_fee`     | float | Transfer fee paid (EUR) | Transfermarkt |

**From FootyStats:**

| Attribute          | Type  | Description              | Source     |
| ------------------ | ----- | ------------------------ | ---------- |
| `xg_per90`         | float | Expected goals per 90    | FootyStats |
| `xa_per90`         | float | Expected assists per 90  | FootyStats |
| `defensive_rating` | float | Defensive rating (0-100) | FootyStats |
| `offensive_rating` | float | Offensive rating (0-100) | FootyStats |

**From Understat (if available):**

| Attribute    | Type  | Description                 | Source    |
| ------------ | ----- | --------------------------- | --------- |
| `npxg_per90` | float | Non-penalty xG per 90       | Understat |
| `npxa_per90` | float | Non-penalty xA per 90       | Understat |
| `ppda`       | float | Passes per defensive action | Understat |

### 2.2 Derived Attributes

**Per-90 Statistics:**

```python
def compute_per90_stats(player_stats: dict, minutes: int) -> dict:
    """Compute per-90 statistics."""
    if minutes == 0:
        return {k: 0.0 for k in ["goals_per90", "assists_per90", "shots_per90"]}

    return {
        "goals_per90": (player_stats["goals"] / minutes) * 90,
        "assists_per90": (player_stats["assists"] / minutes) * 90,
        "shots_per90": (player_stats["shots_total"] / minutes) * 90,
        "shots_on_target_per90": (player_stats["shots_on_target"] / minutes) * 90,
        "tackles_per90": (player_stats["tackles_total"] / minutes) * 90,
        "interceptions_per90": (player_stats["tackles_interceptions"] / minutes) * 90,
        "passes_per90": (player_stats["passes_total"] / minutes) * 90,
        "dribbles_per90": (player_stats["dribbles_success"] / minutes) * 90,
    }
```

**Position-Specific Metrics:**

```python
def compute_position_metrics(player: dict) -> dict:
    """Compute position-specific metrics."""
    position = player["position"]
    metrics = {}

    if position == "GK":
        metrics["clean_sheets"] = player.get("clean_sheets", 0)
        metrics["saves_per90"] = player.get("saves_per90", 0)
        metrics["goals_conceded_per90"] = player.get("goals_conceded_per90", 0)

    elif position in ["DEF", "MID"]:
        metrics["tackles_per90"] = player.get("tackles_per90", 0)
        metrics["interceptions_per90"] = player.get("interceptions_per90", 0)
        metrics["clearances_per90"] = player.get("clearances_per90", 0)
        metrics["aerial_duels_won_pct"] = player.get("aerial_duels_won", 0) / max(
            player.get("aerial_duels_total", 1), 1
        )

    elif position == "FWD":
        metrics["xg_per90"] = player.get("xg_per90", 0)
        metrics["shots_on_target_per90"] = player.get("shots_on_target_per90", 0)
        metrics["dribbles_per90"] = player.get("dribbles_per90", 0)

    return metrics
```

---

## 3. Starting XI Aggregation

### 3.1 Aggregation Strategy

**Key Principle:** Aggregate player stats for the confirmed XI into team-level features.

**Aggregation Methods:**

1. **SUM** - Total output (goals, assists, value)
2. **MEAN** - Average quality (rating, xG per 90, age)
3. **WEIGHTED SUM** - Position-weighted contributions
4. **MAX/MIN** - Best/worst in position

### 3.2 XI Strength Features

**Offensive Aggregates:**

```python
def compute_xi_offensive_aggregates(xi_players: list) -> dict:
    """
    Aggregate offensive stats for starting XI.

    Args:
        xi_players: List of player dicts for starting XI

    Returns:
        Dictionary of aggregated features
    """
    features = {}

    # SUM: Total output
    features["xi_goals_season"] = sum(p.get("goals", 0) for p in xi_players)
    features["xi_assists_season"] = sum(p.get("assists", 0) for p in xi_players)
    features["xi_total_value"] = sum(p.get("market_value", 0) for p in xi_players)

    # MEAN: Average quality
    features["xi_avg_rating"] = np.mean([p.get("rating", 0) for p in xi_players])
    features["xi_avg_age"] = np.mean([p.get("age", 25) for p in xi_players])
    features["xi_xg_per90_avg"] = np.mean([p.get("xg_per90", 0) for p in xi_players])
    features["xi_xa_per90_avg"] = np.mean([p.get("xa_per90", 0) for p in xi_players])

    # Position-weighted: Attackers matter more for xG
    attackers = [p for p in xi_players if p.get("position") in ["FWD", "AM"]]
    if attackers:
        features["xi_attack_xg_avg"] = np.mean(
            [p.get("xg_per90", 0) for p in attackers]
        )
        features["xi_attack_value"] = sum(p.get("market_value", 0) for p in attackers)
    else:
        features["xi_attack_xg_avg"] = 0.0
        features["xi_attack_value"] = 0.0

    return features
```

**Defensive Aggregates:**

```python
def compute_xi_defensive_aggregates(xi_players: list) -> dict:
    """
    Aggregate defensive stats for starting XI.
    """
    features = {}

    # MEAN: Average defensive quality
    features["xi_tackles_per90_avg"] = np.mean(
        [p.get("tackles_per90", 0) for p in xi_players]
    )
    features["xi_interceptions_per90_avg"] = np.mean(
        [p.get("interceptions_per90", 0) for p in xi_players]
    )
    features["xi_blocks_per90_avg"] = np.mean(
        [p.get("blocks_per90", 0) for p in xi_players]
    )
    features["xi_clearances_per90_avg"] = np.mean(
        [p.get("clearances_per90", 0) for p in xi_players]
    )

    # Position-weighted: Defenders matter more
    defenders = [p for p in xi_players if p.get("position") in ["DEF", "GK"]]
    if defenders:
        features["xi_def_tackles_avg"] = np.mean(
            [p.get("tackles_per90", 0) for p in defenders]
        )
        features["xi_def_interceptions_avg"] = np.mean(
            [p.get("interceptions_per90", 0) for p in defenders]
        )
        features["xi_def_avg_height"] = np.mean(
            [p.get("height", 175) for p in defenders]
        )
    else:
        features["xi_def_tackles_avg"] = 0.0
        features["xi_def_interceptions_avg"] = 0.0
        features["xi_def_avg_height"] = 175.0

    # Aerial duels (aggregate)
    total_aerial = sum(p.get("aerial_duels_total", 0) for p in xi_players)
    won_aerial = sum(p.get("aerial_duels_won", 0) for p in xi_players)
    features["xi_aerial_won_pct"] = won_aerial / max(total_aerial, 1)

    return features
```

**Position-Level Aggregates:**

```python
def compute_position_level_aggregates(xi_players: list) -> dict:
    """
    Aggregate by position groups (GK, DEF, MID, FWD).
    """
    features = {}

    # Group by position
    by_position = {
        "GK": [p for p in xi_players if p.get("position") == "GK"],
        "DEF": [p for p in xi_players if p.get("position") == "DEF"],
        "MID": [p for p in xi_players if p.get("position") == "MID"],
        "FWD": [p for p in xi_players if p.get("position") == "FWD"],
    }

    for position, players in by_position.items():
        if not players:
            continue

        prefix = f"xi_{position.lower()}"

        # Value
        features[f"{prefix}_value"] = sum(p.get("market_value", 0) for p in players)
        features[f"{prefix}_avg_value"] = np.mean(
            [p.get("market_value", 0) for p in players]
        )

        # Rating
        features[f"{prefix}_avg_rating"] = np.mean(
            [p.get("rating", 0) for p in players]
        )

        # Position-specific stats
        if position == "GK":
            features[f"{prefix}_clean_sheets"] = sum(
                p.get("clean_sheets", 0) for p in players
            )
            features[f"{prefix}_saves_per90"] = np.mean(
                [p.get("saves_per90", 0) for p in players]
            )

        elif position == "FWD":
            features[f"{prefix}_goals"] = sum(p.get("goals", 0) for p in players)
            features[f"{prefix}_xg_per90"] = np.mean(
                [p.get("xg_per90", 0) for p in players]
            )

        elif position in ["DEF", "MID"]:
            features[f"{prefix}_tackles_per90"] = np.mean(
                [p.get("tackles_per90", 0) for p in players]
            )
            features[f"{prefix}_interceptions_per90"] = np.mean(
                [p.get("interceptions_per90", 0) for p in players]
            )

    return features
```

### 3.3 Complete XI Feature Set

**Total Features: ~37**

| Category                    | Count | Features                                                       |
| --------------------------- | ----- | -------------------------------------------------------------- |
| XI Strength (Value, Rating) | 8     | Total value, avg value, avg rating, value ratio, etc.          |
| Offensive Aggregates        | 7     | Goals, assists, xG per 90, attack value, etc.                  |
| Defensive Aggregates        | 12    | Tackles, interceptions, blocks, clearances, aerial duels, etc. |
| Position-Level              | 16    | GK/DEF/MID/FWD aggregates                                      |
| Formation & Stability       | 4     | Formation, XI stability, etc.                                  |

**See `FEATURE_ENGINEERING.md` §3.5 for complete feature list.**

---

## 4. Bench Strength

### 4.1 Bench Players

**Definition:** Players available as substitutes (typically 7-9 players on bench).

**Key Metrics:**

1. **Bench Value:**
   - Total market value of bench players
   - Average player value
   - Value ratio (bench / XI)

2. **Bench Quality:**
   - Average rating of bench players
   - Goals/assists from bench players
   - xG per 90 from bench players

3. **Position Coverage:**
   - Can bench cover all positions?
   - Attacking options on bench
   - Defensive options on bench

### 4.2 Bench Strength Features

```python
def compute_bench_strength(bench_players: list, xi_players: list) -> dict:
    """
    Compute bench strength features.

    Args:
        bench_players: List of player dicts on bench
        xi_players: List of player dicts in starting XI

    Returns:
        Dictionary of bench strength features
    """
    features = {}

    if not bench_players:
        # No bench data - set defaults
        features["bench_total_value"] = 0.0
        features["bench_avg_value"] = 0.0
        features["bench_value_ratio"] = 0.0
        features["bench_avg_rating"] = 0.0
        features["bench_goals_season"] = 0
        features["bench_attack_options"] = 0
        features["bench_defense_options"] = 0
        return features

    # Value metrics
    bench_value = sum(p.get("market_value", 0) for p in bench_players)
    xi_value = sum(p.get("market_value", 0) for p in xi_players)

    features["bench_total_value"] = bench_value
    features["bench_avg_value"] = bench_value / len(bench_players)
    features["bench_value_ratio"] = bench_value / max(xi_value, 1e-6)

    # Quality metrics
    features["bench_avg_rating"] = np.mean([p.get("rating", 0) for p in bench_players])
    features["bench_goals_season"] = sum(p.get("goals", 0) for p in bench_players)
    features["bench_assists_season"] = sum(p.get("assists", 0) for p in bench_players)
    features["bench_xg_per90_avg"] = np.mean(
        [p.get("xg_per90", 0) for p in bench_players]
    )

    # Position coverage
    bench_positions = [p.get("position") for p in bench_players]
    features["bench_attack_options"] = len(
        [p for p in bench_positions if p in ["FWD", "AM"]]
    )
    features["bench_defense_options"] = len(
        [p for p in bench_positions if p in ["DEF", "GK"]]
    )
    features["bench_midfield_options"] = len([p for p in bench_positions if p == "MID"])

    # Can bench cover all positions?
    xi_positions = set(p.get("position") for p in xi_players)
    bench_positions_set = set(bench_positions)
    features["bench_position_coverage"] = len(
        xi_positions.intersection(bench_positions_set)
    ) / max(len(xi_positions), 1)

    return features
```

**Bench Strength Features:**

| Feature                   | Type  | Description                              |
| ------------------------- | ----- | ---------------------------------------- |
| `bench_total_value`       | float | Total market value of bench (EUR)        |
| `bench_avg_value`         | float | Average player value on bench            |
| `bench_value_ratio`       | float | bench_value / xi_value                   |
| `bench_avg_rating`        | float | Average rating of bench players          |
| `bench_goals_season`      | int   | Total goals by bench players             |
| `bench_assists_season`    | int   | Total assists by bench players           |
| `bench_xg_per90_avg`      | float | Average xG per 90 of bench players       |
| `bench_attack_options`    | int   | Number of attackers on bench             |
| `bench_defense_options`   | int   | Number of defenders on bench             |
| `bench_midfield_options`  | int   | Number of midfielders on bench           |
| `bench_position_coverage` | float | % of XI positions covered by bench (0-1) |

---

## 5. Expected vs Confirmed Lineups

### 5.1 Lineup Availability Timeline

| Time          | Lineup Status         | Typical Availability             |
| ------------- | --------------------- | -------------------------------- |
| T-24h         | Not confirmed         | ~5% of matches have predicted XI |
| T-6h          | Not confirmed         | ~10%                             |
| T-2h          | Sometimes             | ~30% (manager press conferences) |
| **T-1h**      | **Usually confirmed** | **~85% of matches**              |
| T-30m         | Confirmed             | ~95%                             |
| T-0 (kickoff) | Confirmed             | 100%                             |

### 5.2 Expected Lineup Prediction

**When lineup is NOT confirmed, predict most likely XI:**

```python
def predict_likely_xi(
    team_id: int, prediction_time: datetime, exclude_injured: bool = True
) -> list:
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
    if exclude_injured:
        injured = get_current_injuries(team_id, prediction_time)
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


def select_balanced_xi(players_with_pos: list) -> list:
    """
    Select balanced XI from players ranked by starts.

    Formation: 1 GK, 4 DEF, 3-4 MID, 2-3 FWD
    """
    # Sort by starts (most frequent first)
    players_sorted = sorted(players_with_pos, key=lambda x: x["starts"], reverse=True)

    xi = []
    position_counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}

    for player in players_sorted:
        position = player["position"]

        # Check if we need this position
        if position == "GK" and position_counts["GK"] < 1:
            xi.append(player["player_id"])
            position_counts["GK"] += 1
        elif position == "DEF" and position_counts["DEF"] < 4:
            xi.append(player["player_id"])
            position_counts["DEF"] += 1
        elif position == "MID" and position_counts["MID"] < 4:
            xi.append(player["player_id"])
            position_counts["MID"] += 1
        elif position == "FWD" and position_counts["FWD"] < 3:
            xi.append(player["player_id"])
            position_counts["FWD"] += 1

        if len(xi) >= 11:
            break

    return xi
```

### 5.3 Lineup Source Flag

**Always include lineup source:**

```python
def compute_lineup_features_with_source(
    fixture_id: int, prediction_time: datetime
) -> dict:
    """
    Compute lineup features with source tracking.
    """
    features = {}

    # Try to get confirmed lineup
    confirmed_lineup = get_lineup(fixture_id, "confirmed", prediction_time)

    if confirmed_lineup and confirmed_lineup["announced_at_utc"] <= prediction_time:
        # Confirmed lineup available
        features["lineup_available"] = 1
        features["lineup_source"] = "confirmed"
        xi_players = get_player_data(confirmed_lineup["startXI"])

    else:
        # Use predicted lineup
        features["lineup_available"] = 0
        features["lineup_source"] = "predicted"

        home_team, away_team = get_teams(fixture_id)
        predicted_home_xi = predict_likely_xi(home_team, prediction_time)
        predicted_away_xi = predict_likely_xi(away_team, prediction_time)

        if predicted_home_xi and predicted_away_xi:
            xi_players = get_player_data(predicted_home_xi + predicted_away_xi)
        else:
            # Fallback: use team averages
            features["lineup_source"] = "team_avg"
            xi_players = get_team_average_players(home_team, away_team, prediction_time)

    # Compute XI features
    features.update(compute_xi_offensive_aggregates(xi_players))
    features.update(compute_xi_defensive_aggregates(xi_players))

    return features
```

---

## 6. Lineup Availability Handling

### 6.1 Fallback Strategy

**When lineup NOT available:**

1. **Option 1:** Use predicted XI (based on last 5 lineups)
2. **Option 2:** Use team-level averages (no player granularity)

```python
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

### 6.2 Key Absentees Detection

**Identify key players missing from lineup:**

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
    if missing:
        missing_data = get_player_data(missing)
        features["value_lost_to_injury"] = missing_data["market_value"].sum()

        # Attack value lost
        attackers_missing = [p for p in missing_data if p["position"] in ["FWD", "AM"]]
        features["attack_value_missing"] = sum(
            p["market_value"] for p in attackers_missing
        )
    else:
        features["value_lost_to_injury"] = 0.0
        features["attack_value_missing"] = 0.0

    return features
```

### 6.3 Lineup Stability

**Compute overlap between current XI and last 5 starting XIs:**

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

---

## 7. Player Data Sources

### 7.1 Data Source Priority

**For each player attribute:**

1. **API-Football** - Primary source for:
   - Basic info (name, age, position, nationality)
   - Match statistics (goals, assists, passes, tackles)
   - Injuries and suspensions
   - Lineup data

2. **Transfermarkt** - For:
   - Market value
   - Transfer fees
   - Contract information

3. **FootyStats** - For:
   - xG per 90
   - Expected assists per 90
   - Attack/defense ratings

4. **Understat** - For (5 leagues only):
   - Non-penalty xG
   - PPDA metrics
   - Shot-level data

### 7.2 Data Collection Strategy

**For Prediction Leagues:**

- Collect player data for all teams
- Update after each match
- Track injuries/suspensions daily

**For Reference Leagues:**

- Collect player participation (who played)
- Basic stats (goals, assists) for fatigue tracking
- NO detailed player profiles needed

**For Features Leagues:**

- Summary-level player data only
- Squad value and key players
- NO match-level player stats

---

## 8. Implementation

### 8.1 Player Profile Schema

```python
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class PlayerProfile:
    """Player profile with all attributes."""

    # Basic Info
    player_id: int
    name: str
    position: str  # GK, DEF, MID, FWD
    age: int
    nationality: str
    height: Optional[int] = None
    weight: Optional[int] = None

    # Status
    injured: bool = False
    suspended: bool = False

    # Market Value
    market_value: Optional[float] = None  # EUR
    contract_expires: Optional[date] = None

    # Season Statistics (season-to-date)
    goals: int = 0
    assists: int = 0
    minutes: int = 0
    rating: Optional[float] = None

    # Per-90 Statistics
    goals_per90: float = 0.0
    assists_per90: float = 0.0
    xg_per90: Optional[float] = None
    xa_per90: Optional[float] = None

    # Defensive Statistics
    tackles_per90: float = 0.0
    interceptions_per90: float = 0.0
    blocks_per90: float = 0.0
    clearances_per90: float = 0.0

    # Passing
    passes_per90: float = 0.0
    pass_accuracy: Optional[float] = None

    # Aerial
    aerial_duels_won_pct: Optional[float] = None

    def is_available(self) -> bool:
        """Check if player is available (not injured/suspended)."""
        return not (self.injured or self.suspended)

    def get_position_weight(self) -> float:
        """Get position weight for aggregation."""
        weights = {
            "GK": 0.8,
            "DEF": 0.9,
            "MID": 1.1,
            "FWD": 1.3,
        }
        return weights.get(self.position, 1.0)
```

### 8.2 XI Aggregation Function

```python
def aggregate_xi_features(xi_profiles: list[PlayerProfile]) -> dict:
    """
    Aggregate player profiles into XI-level features.

    Args:
        xi_profiles: List of PlayerProfile objects for starting XI

    Returns:
        Dictionary of aggregated features
    """
    if not xi_profiles:
        return {}

    features = {}

    # Value aggregates
    features["xi_total_value"] = sum(p.market_value or 0 for p in xi_profiles)
    features["xi_avg_value"] = features["xi_total_value"] / len(xi_profiles)
    features["xi_avg_rating"] = np.mean([p.rating or 0 for p in xi_profiles])
    features["xi_avg_age"] = np.mean([p.age for p in xi_profiles])

    # Offensive aggregates
    features["xi_goals_season"] = sum(p.goals for p in xi_profiles)
    features["xi_assists_season"] = sum(p.assists for p in xi_profiles)
    features["xi_xg_per90_avg"] = np.mean([p.xg_per90 or 0 for p in xi_profiles])

    # Defensive aggregates
    features["xi_tackles_per90_avg"] = np.mean([p.tackles_per90 for p in xi_profiles])
    features["xi_interceptions_per90_avg"] = np.mean(
        [p.interceptions_per90 for p in xi_profiles]
    )

    # Position-weighted aggregates
    attackers = [p for p in xi_profiles if p.position in ["FWD", "AM"]]
    if attackers:
        features["xi_attack_xg_avg"] = np.mean([p.xg_per90 or 0 for p in attackers])
        features["xi_attack_value"] = sum(p.market_value or 0 for p in attackers)

    defenders = [p for p in xi_profiles if p.position in ["DEF", "GK"]]
    if defenders:
        features["xi_def_tackles_avg"] = np.mean([p.tackles_per90 for p in defenders])
        features["xi_def_avg_height"] = np.mean([p.height or 175 for p in defenders])

    return features
```

### 8.3 Complete Pipeline

```python
def compute_lineup_features_pipeline(
    fixture_id: int,
    prediction_time: datetime,
    lineup_type: str = "expected",  # or 'confirmed'
) -> dict:
    """
    Complete lineup feature computation pipeline.

    Args:
        fixture_id: Fixture identifier
        prediction_time: When prediction is made
        lineup_type: 'expected' or 'confirmed'

    Returns:
        Dictionary of all lineup-related features
    """
    home_team, away_team = get_teams(fixture_id)

    features = {}

    # Get lineups
    home_lineup = get_lineup_data(home_team, fixture_id, prediction_time, lineup_type)
    away_lineup = get_lineup_data(away_team, fixture_id, prediction_time, lineup_type)

    # Lineup availability
    features["lineup_available"] = 1 if (home_lineup and away_lineup) else 0
    features["lineup_source"] = (
        "confirmed" if features["lineup_available"] else "predicted"
    )

    if home_lineup and away_lineup:
        # Get player profiles
        home_xi_profiles = get_player_profiles(home_lineup["startXI"], prediction_time)
        away_xi_profiles = get_player_profiles(away_lineup["startXI"], prediction_time)

        # XI aggregates
        features.update(
            {f"home_{k}": v for k, v in aggregate_xi_features(home_xi_profiles).items()}
        )
        features.update(
            {f"away_{k}": v for k, v in aggregate_xi_features(away_xi_profiles).items()}
        )

        # Key absentees
        features.update(
            compute_key_absentees(home_team, home_lineup["startXI"], prediction_time)
        )
        features.update(
            compute_key_absentees(away_team, away_lineup["startXI"], prediction_time)
        )

        # Lineup stability
        features["home_xi_stability"] = compute_lineup_stability(
            home_team, home_lineup["startXI"], prediction_time
        )
        features["away_xi_stability"] = compute_lineup_stability(
            away_team, away_lineup["startXI"], prediction_time
        )

        # Bench strength
        if "bench" in home_lineup:
            home_bench_profiles = get_player_profiles(
                home_lineup["bench"], prediction_time
            )
            features.update(
                {
                    f"home_{k}": v
                    for k, v in compute_bench_strength(
                        home_bench_profiles, home_xi_profiles
                    ).items()
                }
            )

        if "bench" in away_lineup:
            away_bench_profiles = get_player_profiles(
                away_lineup["bench"], prediction_time
            )
            features.update(
                {
                    f"away_{k}": v
                    for k, v in compute_bench_strength(
                        away_bench_profiles, away_xi_profiles
                    ).items()
                }
            )

    else:
        # Fallback: use team averages
        features.update(
            compute_team_level_fallback(home_team, away_team, prediction_time)
        )

    return features
```

---

## Summary

This document defines:

1. **Player Attributes:** Complete list of player data from all sources
2. **XI Aggregation:** How to aggregate player stats into team-level features
3. **Bench Strength:** Metrics for substitution quality
4. **Expected vs Confirmed:** Handling lineup uncertainty
5. **Fallback Strategies:** What to do when lineups unavailable
6. **Data Sources:** Which sources provide which player attributes

**Key Principles:**

- Aggregate, don't create per-player columns
- Use position weights for meaningful aggregation
- Handle missing lineups gracefully
- Track lineup source for model confidence

**Next Steps:**

- Harsh will implement player profile collection
- Feature engineering will use these aggregations
- Models will learn from XI strength features
