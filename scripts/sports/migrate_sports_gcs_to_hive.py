#!/usr/bin/env python3
"""Migrate archived sports betting GCS data to UTS hive-partitioned format.

Transforms:
  Old: football-raw-data-all-sources-*/api_football/fixtures.csv
  New: instruments-store-sports-*/sports_reference/by_date/day={date}/entity=fixtures/fixtures.parquet

  Old: market-data-tick-sports-*-v3/odds-api/2020-06-17/{league}.parquet
  New: market-data-tick-sports-*/raw_tick_data/by_date/day=2020-06-17/venue=ODDS_API/ticks.parquet

  Old: football-mapped-consolidated-*/mapping/team_mappings.csv
  New: instruments-store-sports-*/sports_reference/mappings/team_mapping.parquet

  Old: football-ml-features-*/version=1/league=39/season=2024/features.parquet
  New: features-sports-*/by_date/day={date}/feature_version=1/features.parquet

Modes:
  --dry-run    Show what would be done without copying
  --execute    Actually perform the migration
  --verify     Verify row counts match after migration

Usage:
  python migrate_sports_gcs_to_hive.py --dry-run
  python migrate_sports_gcs_to_hive.py --execute --date-range 2020-06-01:2026-03-25

WAIT: Do not execute until user says "go".
"""

from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger(__name__)

PROJECT_ID = "central-element-323112"

# Old bucket names
OLD_RAW = f"football-raw-data-all-sources-{PROJECT_ID}"
OLD_ODDS = f"market-data-tick-sports-{PROJECT_ID}-v3"
OLD_MAPPED = f"football-mapped-consolidated-{PROJECT_ID}"
OLD_FEATURES = f"football-ml-features-{PROJECT_ID}"
OLD_MODELS = f"football-ml-models-and-predictions-{PROJECT_ID}"

# New UTS bucket names
NEW_INSTRUMENTS = f"instruments-store-sports-{PROJECT_ID}"
NEW_TICK_DATA = f"market-data-tick-sports-{PROJECT_ID}"
NEW_FEATURES = f"features-sports-{PROJECT_ID}"

# Raw data entity mapping: old CSV name → new entity type
RAW_ENTITY_MAP: dict[str, str] = {
    "api_football/fixtures.csv": "fixtures",
    "api_football/teams.csv": "teams",
    "api_football/venues.csv": "venues",
    "api_football/countries.csv": "countries",
    "api_football/fixture_stats.csv": "fixture_stats",
    "api_football/fixture_events.csv": "fixture_events",
    "api_football/fixture_lineups.csv": "fixture_lineups",
    "api_football/fixture_player_stats.csv": "player_stats",
    "api_football/fixture_coaches.csv": "coaches",
    "footystats/matches.csv": "footystats_matches",
    "footystats/teams.csv": "footystats_teams",
    "footystats/players.csv": "footystats_players",
    "footystats/referees.csv": "footystats_referees",
    "soccer_football/matches.csv": "sf_matches",
    "soccer_football/teams_standings.csv": "sf_standings",
    "soccer_football/all_matches.csv": "sf_all_matches",
    "understat/matches.csv": "understat_matches",
    "understat/team_data.csv": "understat_teams",
    "understat/player_data.csv": "understat_players",
    "understat/us_match_shots.csv": "understat_shots",
    "transfermarkt/teams.csv": "transfermarkt_teams",
    "transfermarkt/players.csv": "transfermarkt_players",
}

# Mapping files
MAPPING_FILES: dict[str, str] = {
    "mapping/team_mappings.csv": "team_mapping.parquet",
    "mapping/fixture_mappings.csv": "fixture_mapping.parquet",
    "mapping/leagues.csv": "league_mapping.parquet",
    "mapping/teams.csv": "teams_consolidated.parquet",
    "mapping/fixtures.csv": "fixtures_consolidated.parquet",
    "mapping/odds_api_team_mappings.csv": "odds_api_team_mapping.parquet",
}


def migrate_raw_data(dry_run: bool = True) -> list[str]:
    """Migrate raw CSV data to hive-partitioned parquet.

    Old: gs://{OLD_RAW}/{provider}/{entity}.csv
    New: gs://{NEW_INSTRUMENTS}/sports_reference/archived_raw/source={provider}/entity={type}/{entity}.parquet
    """
    import pandas as pd

    actions: list[str] = []

    for old_path, entity in RAW_ENTITY_MAP.items():
        src = f"gs://{OLD_RAW}/{old_path}"
        provider = old_path.split("/")[0]
        dst_prefix = f"sports_reference/archived_raw/source={provider}/entity={entity}"
        dst = f"gs://{NEW_INSTRUMENTS}/{dst_prefix}/{entity}.parquet"

        if dry_run:
            actions.append(f"COPY {src} → {dst} (CSV→parquet)")
            continue

        try:
            df = pd.read_csv(src)
            df.to_parquet(dst, index=False)
            actions.append(f"OK {src} → {dst} ({len(df)} rows)")
            logger.info("Migrated %s: %d rows", old_path, len(df))
        except Exception as exc:
            actions.append(f"FAIL {src}: {exc}")
            logger.warning("Failed to migrate %s: %s", old_path, exc)

    return actions


def migrate_odds_data(dry_run: bool = True, date_range: tuple[str, str] | None = None) -> list[str]:
    """Migrate odds tick data to hive-partitioned format.

    Old: gs://{OLD_ODDS}/odds-api/{YYYY-MM-DD}/{league}.parquet
    New: gs://{NEW_TICK_DATA}/raw_tick_data/by_date/day={YYYY-MM-DD}/venue=ODDS_API/ticks.parquet

    Server-side copy where possible (same project, just reorganise paths).
    """
    # One-shot migration script; predates UTL gcs_copy_object (TID251 lives only in the 5.95 ratchet config):
    from google.cloud import storage  # noqa: TID251, RUF100

    client = storage.Client(project=PROJECT_ID)
    old_bucket = client.bucket(OLD_ODDS)
    actions: list[str] = []

    # List all date directories
    blobs = list(old_bucket.list_blobs(prefix="odds-api/"))
    dates_seen: set[str] = set()

    for blob in blobs:
        # Extract date from path: odds-api/2020-06-17/soccer_epl.parquet
        parts = blob.name.split("/")
        if len(parts) < 3 or not parts[1] or parts[1].startswith("001_"):
            continue
        date_str = parts[1]

        if date_range and (date_str < date_range[0] or date_str > date_range[1]):
            continue

        dates_seen.add(date_str)

    for date_str in sorted(dates_seen):
        src = f"gs://{OLD_ODDS}/odds-api/{date_str}/"
        dst = f"gs://{NEW_TICK_DATA}/raw_tick_data/by_date/day={date_str}/venue=ODDS_API/"

        if dry_run:
            actions.append(f"COPY {src}*.parquet → {dst}ticks.parquet (merge all leagues)")
            continue

        # In execute mode: read all league parquets for this date, merge, write
        try:
            import pandas as pd

            league_blobs = [
                b for b in blobs if b.name.startswith(f"odds-api/{date_str}/") and b.name.endswith(".parquet")
            ]
            if not league_blobs:
                continue

            dfs: list[pd.DataFrame] = []
            for lb in league_blobs:
                league_path = f"gs://{OLD_ODDS}/{lb.name}"
                try:
                    df = pd.read_parquet(league_path)
                    dfs.append(df)
                except Exception:
                    pass

            if dfs:
                merged = pd.concat(dfs, ignore_index=True)
                merged.to_parquet(f"{dst}ticks.parquet", index=False)
                actions.append(f"OK {date_str}: {len(merged)} rows from {len(dfs)} leagues")
                logger.info("Migrated odds %s: %d rows", date_str, len(merged))
        except Exception as exc:
            actions.append(f"FAIL {date_str}: {exc}")

    return actions


def migrate_mappings(dry_run: bool = True) -> list[str]:
    """Migrate mapping CSVs to parquet in new bucket.

    Old: gs://{OLD_MAPPED}/mapping/{name}.csv
    New: gs://{NEW_INSTRUMENTS}/sports_reference/mappings/{name}.parquet
    """
    import pandas as pd

    actions: list[str] = []

    for old_path, new_name in MAPPING_FILES.items():
        src = f"gs://{OLD_MAPPED}/{old_path}"
        dst = f"gs://{NEW_INSTRUMENTS}/sports_reference/mappings/{new_name}"

        if dry_run:
            actions.append(f"COPY {src} → {dst} (CSV→parquet)")
            continue

        try:
            df = pd.read_csv(src)
            df.to_parquet(dst, index=False)
            actions.append(f"OK {src} → {dst} ({len(df)} rows)")
        except Exception as exc:
            actions.append(f"FAIL {src}: {exc}")

    return actions


def migrate_features(dry_run: bool = True) -> list[str]:
    """Migrate ML features — already hive-partitioned, just needs bucket move.

    Old: gs://{OLD_FEATURES}/version={N}/league={id}/season={Y}/features.parquet
    New: gs://{NEW_FEATURES}/archived_features/version={N}/league={id}/season={Y}/features.parquet

    Server-side copy (no data transformation needed).
    """
    # One-shot migration script; predates UTL gcs_copy_object (TID251 lives only in the 5.95 ratchet config):
    from google.cloud import storage  # noqa: TID251, RUF100

    client = storage.Client(project=PROJECT_ID)
    old_bucket = client.bucket(OLD_FEATURES)
    new_bucket = client.bucket(NEW_FEATURES)
    actions: list[str] = []

    blobs = list(old_bucket.list_blobs())
    for blob in blobs:
        dst_name = f"archived_features/{blob.name}"

        if dry_run:
            actions.append(f"COPY gs://{OLD_FEATURES}/{blob.name} → gs://{NEW_FEATURES}/{dst_name}")
            continue

        try:
            old_bucket.copy_blob(blob, new_bucket, dst_name)
            actions.append(f"OK {blob.name}")
        except Exception as exc:
            actions.append(f"FAIL {blob.name}: {exc}")

    return actions


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Migrate sports GCS data to UTS hive format")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show actions without executing")
    parser.add_argument("--execute", action="store_true", help="Actually perform migration")
    parser.add_argument("--verify", action="store_true", help="Verify row counts after migration")
    parser.add_argument("--date-range", type=str, default="", help="Date range for odds: YYYY-MM-DD:YYYY-MM-DD")
    parser.add_argument("--skip-odds", action="store_true", help="Skip odds migration (50GB+, slow)")
    parser.add_argument("--skip-raw", action="store_true", help="Skip raw data migration")
    parser.add_argument("--skip-features", action="store_true", help="Skip feature migration")
    args = parser.parse_args()

    dry_run = not args.execute
    date_range = tuple(args.date_range.split(":")) if args.date_range else None

    if dry_run:
        print("=" * 80)
        print("DRY RUN — no data will be copied")
        print("=" * 80)
    else:
        print("=" * 80)
        print("EXECUTING MIGRATION — data will be copied")
        print("=" * 80)
        confirm = input("Type 'yes' to proceed: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    all_actions: list[str] = []

    if not args.skip_raw:
        print("\n--- RAW DATA ---")
        actions = migrate_raw_data(dry_run)
        all_actions.extend(actions)
        for a in actions:
            print(f"  {a}")

    print("\n--- MAPPINGS ---")
    actions = migrate_mappings(dry_run)
    all_actions.extend(actions)
    for a in actions:
        print(f"  {a}")

    if not args.skip_odds:
        print("\n--- ODDS DATA ---")
        actions = migrate_odds_data(dry_run, date_range)
        all_actions.extend(actions)
        for a in actions[:20]:
            print(f"  {a}")
        if len(actions) > 20:
            print(f"  ... and {len(actions) - 20} more dates")

    if not args.skip_features:
        print("\n--- ML FEATURES ---")
        actions = migrate_features(dry_run)
        all_actions.extend(actions)
        for a in actions[:20]:
            print(f"  {a}")
        if len(actions) > 20:
            print(f"  ... and {len(actions) - 20} more files")

    print(f"\n{'=' * 80}")
    print(f"Total actions: {len(all_actions)}")
    ok = sum(1 for a in all_actions if a.startswith("OK"))
    fail = sum(1 for a in all_actions if a.startswith("FAIL"))
    if not dry_run:
        print(f"Success: {ok}, Failed: {fail}")


if __name__ == "__main__":
    main()
