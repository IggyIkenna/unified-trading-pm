#!/usr/bin/env python3
# Epic: sports_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""Migrate player mappings from football-mapped-consolidated to sports-data bucket.

Reads players.csv from old NSBS bucket, deduplicates by api_football_player_id,
constructs canonical PlayerMapping objects, and writes to canonical parquet.

Usage:
    python scripts/sports/migrate_player_mappings_to_canonical.py \
        --project central-element-323112 --dry-run
    python scripts/sports/migrate_player_mappings_to_canonical.py \
        --project central-element-323112 --apply
"""

from __future__ import annotations

import argparse
import io
import logging

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from unified_api_contracts import PlayerMapping
from unified_api_contracts.external.api_football import (  # noqa: qg-deep-import, qg-deep-import
    get_canonical_player_name_from_api_football,
)
from unified_trading_library import download_from_storage, upload_to_storage

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_BUCKET_PATTERN = "football-mapped-consolidated-{project}"
DEFAULT_DEST_BUCKET_PATTERN = "sports-data-{project}"
SOURCE_PATH = "mapping/players.csv"
DEST_PATH = "sports/player_mappings.parquet"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate player mappings to canonical format")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument(
        "--source-bucket",
        default=None,
        help=f"Source bucket (default: {DEFAULT_SOURCE_BUCKET_PATTERN})",
    )
    parser.add_argument(
        "--dest-bucket",
        default=None,
        help=f"Destination bucket (default: {DEFAULT_DEST_BUCKET_PATTERN})",
    )
    parser.add_argument("--dry-run", action="store_true", default=True, help="Print stats only (default)")
    parser.add_argument("--apply", action="store_true", help="Write to GCS")
    return parser.parse_args()


def _build_mappings(df: pd.DataFrame) -> list[dict[str, object]]:
    """Convert deduplicated DataFrame rows to PlayerMapping dicts."""
    mappings: list[dict[str, object]] = []
    for _, row in df.iterrows():
        af_id = int(row["api_football_player_id"])
        af_name = str(row.get("api_football_player_name", ""))
        canonical_id = get_canonical_player_name_from_api_football(af_name, af_id)

        us_id_raw = row.get("understat_id")
        us_id = int(us_id_raw) if pd.notna(us_id_raw) else None

        mapping = PlayerMapping(
            canonical_player_id=canonical_id,
            display_name=af_name,
            api_football_player_id=af_id,
            understat_player_id=us_id,
            footystats_player_id=None,
            soccer_football_player_id=None,
        )
        mappings.append(mapping.model_dump())
    return mappings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = _parse_args()

    source_bucket = args.source_bucket or DEFAULT_SOURCE_BUCKET_PATTERN.format(project=args.project)
    dest_bucket = args.dest_bucket or DEFAULT_DEST_BUCKET_PATTERN.format(project=args.project)

    logger.info("Source: gs://%s/%s", source_bucket, SOURCE_PATH)
    logger.info("Dest:   gs://%s/%s", dest_bucket, DEST_PATH)

    # Download CSV
    raw_bytes = download_from_storage(source_bucket, SOURCE_PATH)
    df = pd.read_csv(io.BytesIO(raw_bytes))
    logger.info("Raw rows: %d", len(df))

    # Deduplicate by api_football_player_id (keep highest match_score)
    if "match_score" in df.columns:
        df = df.sort_values("match_score", ascending=False)
    df = df.drop_duplicates(subset=["api_football_player_id"], keep="first")
    logger.info("Deduplicated players: %d", len(df))

    # Build canonical mappings
    mappings = _build_mappings(df)
    logger.info("PlayerMapping objects: %d", len(mappings))

    if args.apply and not args.dry_run:
        # Write parquet
        out_df = pd.DataFrame(mappings)
        table = pa.Table.from_pandas(out_df)
        buf = io.BytesIO()
        pq.write_table(table, buf)
        upload_to_storage(dest_bucket, DEST_PATH, buf.getvalue())
        logger.info("Uploaded to gs://%s/%s", dest_bucket, DEST_PATH)
    else:
        logger.info("[DRY RUN] Would write %d mappings to gs://%s/%s", len(mappings), dest_bucket, DEST_PATH)
        # Show sample
        if mappings:
            sample = mappings[0]
            logger.info("Sample: %s", sample)


if __name__ == "__main__":
    main()
