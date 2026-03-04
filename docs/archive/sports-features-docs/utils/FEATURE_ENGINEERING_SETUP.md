# Feature Engineering Setup - Summary

## What We Created

We've set up a complete feature engineering pipeline with clean separation between data models and feature computation.

### File Structure

```
new-sports/
├── models.py                           # Existing: Data source tables (DO NOT MODIFY)
├── feature_models.py                   # NEW: Feature table schemas
├── create_feature_tables.py            # NEW: Script to create feature tables
├── example_compute_features.py         # NEW: Example usage
├── features/                           # NEW: Feature engineering package
│   ├── __init__.py                    # Package initialization
│   ├── base.py                        # Base FeatureBuilder class
│   ├── team.py                        # Team feature builder (IMPLEMENTED)
│   └── README.md                      # Documentation
```

## Key Design Decisions

### 1. **Shared Base Class**

- `feature_models.py` imports `Base` from `models.py`
- This ensures all tables use the same SQLAlchemy metadata
- **CRITICAL**: Prevents accidental modification of existing tables

### 2. **Separate Feature Tables**

- Feature tables are stored separately from data tables
- Each feature category has its own table:
  - `feature_vector_team` - Team-level features
  - `feature_vector_league` - League-level features
  - `feature_vector_h2h` - Head-to-head features
  - `feature_vector_context` - Contextual features
  - `feature_team_ratings` - Team ratings helper table
  - `feature_h2h_records` - H2H records helper table

### 3. **Temporal Discipline**

- Every feature table has:
  - `fixture_id` - The match being predicted
  - `feature_horizon` - When computed (T-24h, T-1h, HT-2min)
  - `timestamp_utc` - Exact computation timestamp
- Unique constraint on `(fixture_id, feature_horizon, timestamp_utc)`
- Anti-leakage validation built into base class

### 4. **Data Sources**

Currently using:

- `models.Fixture` - API-Football match data ✅
- `models.FixtureStats` - API-Football statistics ✅
- `models.FTMatch` - FootyStats match data ✅
- `models.Team` - Team information ✅
- `models.League` - League information ✅

## Getting Started

### Step 1: Create Feature Tables

```bash
python create_feature_tables.py
```

This creates 6 new tables **without modifying existing tables**.

### Step 2: Test Feature Computation

```bash
python example_compute_features.py
```

This will:

1. Find 5 finished fixtures from Premier League 2023
2. Compute team features at T-24h horizon
3. Save features to `feature_vector_team` table
4. Print summary

### Step 3: Verify in Database

```sql
-- Check if tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_name LIKE 'feature_%';

-- Check computed features
SELECT
    fixture_id,
    feature_horizon,
    home_ppg_last5,
    away_ppg_last5,
    home_xg_season,
    away_xg_season
FROM feature_vector_team
LIMIT 5;
```

## Team Features Implemented

### Current Status: ~100 Features

**Form Features (6 per team = 12 total)**

- PPG (last 3, last 5, season)
- Form points, form trend
- Win rate

**Goal Features (9 per team = 18 total)**

- Goals scored (last 1, 3, 5, season)
- Goals conceded (last 1, 3, 5, season)
- Goal difference

**xG Features (9 per team = 18 total)**

- xG for (last 1, 3, 5, season)
- xG against (last 1, 3, 5, season)
- xG difference

**Shot Features (7 per team = 14 total)**

- Total shots (last 3, 5, season)
- Shots on target (last 3, 5, season)
- Shot accuracy

**Possession Features (3 per team = 6 total)**

- Possession (last 3, 5, season)

**Dangerous Attacks (3 per team = 6 total)**

- From FootyStats (last 3, 5, season)

**Card Features (3 per team = 6 total)**

- Yellow cards, red cards, total cards

**Corner Features (3 per team = 6 total)**

- Corners (last 3, 5, season)

**Rest & Congestion (2 per team = 4 total)**

- Days rest, games in last 14 days

**Derived Features (5 total)**

- PPG difference, xG difference
- Form momentum (home & away)
- Rest advantage

## Next Steps

### Immediate (Can start now with existing data)

1. **Test on Real Data**

   ```bash
   # Modify example_compute_features.py with your league/season
   python example_compute_features.py
   ```

2. **Implement League Features**
   - League averages (goals, xG, possession)
   - League patterns (home win %, BTTS %)
   - Season progress indicators

3. **Implement H2H Features**
   - Historical head-to-head records
   - Recent H2H form
   - H2H goal patterns

4. **Implement Context Features**
   - Venue information
   - Match timing (weekend, midweek)
   - Basic referee stats

### Medium Term (Requires more data)

5. **Add Market Features** (requires odds data)
   - Odds-implied probabilities
   - Sharp vs soft consensus
   - Velocity, steam detection

6. **Add Lineup Features** (requires lineup tracking)
   - Expected XI aggregation
   - Missing key players
   - Formation analysis

7. **Add Weather Features** (requires weather API)
   - Temperature, wind, rain
   - Weather impact scores

### Long Term

8. **Half-Time Features**
   - Build `HTState` snapshot system
   - Implement delta models
   - HT momentum features

9. **Feature Aggregator**
   - Combine all feature categories
   - Single entry point for ML pipeline

10. **Validation & Testing**
    - Feature importance tracking
    - Anti-leakage tests
    - Data quality checks

## Usage Examples

### Basic Usage

```python
from datetime import datetime, timezone, timedelta
from features.team import TeamFeatureBuilder

# Compute features for a fixture
builder = TeamFeatureBuilder(
    fixture_id=12345,
    feature_horizon="T-24h",
    as_of_utc=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
)

# Run full pipeline (validate, compute, save)
features = builder.run()

# Access specific features
print(f"Home PPG: {features['home_ppg_last5']}")
print(f"Away xG: {features['away_xg_season']}")
```

### Batch Processing

```python
from database import SessionLocal
from models import Fixture
from features.team import TeamFeatureBuilder

session = SessionLocal()

# Get all fixtures for a league-season
fixtures = (
    session.query(Fixture)
    .filter(
        Fixture.af_league_id == 39,  # Premier League
        Fixture.season == 2023,
        Fixture.status_long == "Match Finished",
    )
    .all()
)

# Compute features for each
for fixture in fixtures:
    as_of_utc = fixture.date - timedelta(hours=24)

    with TeamFeatureBuilder(
        fixture_id=fixture.af_fixture_id,
        feature_horizon="T-24h",
        as_of_utc=as_of_utc,
        session=session,
    ) as builder:
        try:
            builder.run()
            print(f"✓ Fixture {fixture.af_fixture_id}")
        except Exception as e:
            print(f"✗ Fixture {fixture.af_fixture_id}: {e}")

session.close()
```

### Custom Feature Horizon

```python
# Compute at different horizons
horizons = ["T-72h", "T-24h", "T-6h", "T-1h"]

for horizon in horizons:
    if horizon == "T-72h":
        hours = 72
    elif horizon == "T-24h":
        hours = 24
    elif horizon == "T-6h":
        hours = 6
    else:
        hours = 1

    as_of_utc = fixture.date - timedelta(hours=hours)

    builder = TeamFeatureBuilder(
        fixture_id=fixture.af_fixture_id, feature_horizon=horizon, as_of_utc=as_of_utc
    )
    builder.run()
```

## Important Notes

### ⚠️ DO NOT MODIFY

- **`models.py`** - Contains existing tables with data
- **Existing database tables** - Feature computation only reads, never writes to data tables

### ✅ SAFE TO MODIFY

- **`feature_models.py`** - Add new feature tables here
- **`features/*.py`** - Add new feature builders here
- **Feature tables** - Can be dropped and recreated anytime

### Anti-Leakage Validation

The base class automatically validates:

```python
def validate_no_leakage(self) -> bool:
    """Ensure as_of_utc is before fixture kickoff"""
    if self.as_of_utc >= self.fixture.date:
        raise ValueError("LEAKAGE DETECTED")
    return True
```

This runs automatically in `builder.run()`.

## Troubleshooting

### "Fixture not found"

- Check that `af_fixture_id` exists in `fixtures` table
- Verify fixture has `status_long = "Match Finished"`

### "No previous fixtures"

- Team might be in first few games of season
- Features will return `None` for insufficient data

### "LEAKAGE DETECTED"

- `as_of_utc` is after fixture kickoff
- Adjust `as_of_utc` to be before `fixture.date`

### "No xG data"

- `FixtureStats` might not have `expected_goals`
- Feature will return `None`

### "Table already exists"

- Safe to ignore if running `create_feature_tables()` multiple times
- Uses `checkfirst=True` to avoid errors

## Performance Tips

1. **Use batch processing** - Process multiple fixtures in one session
2. **Start small** - Test with 5-10 fixtures first
3. **Use indexes** - Feature tables have indexes on `fixture_id` and `feature_horizon`
4. **Cache session** - Reuse session for multiple builders
5. **Parallel processing** - Can process different leagues in parallel

## Summary

✅ **Created:**

- 6 new feature tables
- Base feature builder class with anti-leakage validation
- Team feature builder with ~100 features
- Example scripts and documentation

✅ **Safe:**

- No modifications to existing tables
- Separate metadata for features
- Can drop and recreate feature tables anytime

✅ **Ready:**

- Compute team features for any finished fixture
- Extend with new feature categories
- Build ML pipeline on top of features

🎯 **Next:** Test on your data and start implementing additional feature categories!
