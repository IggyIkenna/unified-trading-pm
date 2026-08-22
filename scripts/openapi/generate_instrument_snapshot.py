#!/usr/bin/env python3
# Epic: uac_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate a full instrument snapshot from GCS for a given date.

Pulls ALL instruments from all categories (cefi, tradfi, defi, sports,
prediction) and consolidates into a single JSON file for the UI registry.

Usage:
    python generate_instrument_snapshot.py \
        --date 2026-03-27 \
        --output-dir unified-api-contracts/openapi

The snapshot is a permanent registry file (a few MB), NOT cached/git-ignored.
The UI uses it as SSOT for realistic mock data at scale.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from pathlib import Path

from unified_trading_library import get_storage_client, resolve_bucket_name

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

CATEGORIES = ["cefi", "tradfi", "defi", "sports", "prediction"]


def _instrument_bucket_prefix(category: str, date: str) -> str:
    """Resolve the env-tiered instruments-store bucket prefix for a category.

    The hardcoded ``instruments-store-{category}-{project}`` shape (no env tier)
    doesn't exist on GCS — Group-A raw buckets are env-tiered per
    codex/05-infrastructure/bucket-isolation-model.md. ``prediction`` is a flat
    dedicated kind (no per-asset_group entry); the other categories are keyed
    per-asset_group under the ``instruments-store`` kind.
    """
    if category == "prediction":
        bucket = resolve_bucket_name(cloud="gcp", kind="instruments-store-prediction")
    else:
        bucket = resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=category)
    return f"gs://{bucket}/instrument_availability/by_date/day={date}/"


def _list_venues(bucket_prefix: str) -> list[str]:
    """List venue subdirectories under a GCS prefix."""
    bucket, prefix = bucket_prefix.removeprefix("gs://").split("/", 1)
    try:
        native_iter = get_storage_client(provider="gcp").bucket(bucket).list_blobs(prefix=prefix, delimiter="/")
        list(native_iter)  # exhaust — `.prefixes` only populates after iteration
    except (OSError, ValueError, RuntimeError):
        return []
    venues: list[str] = []
    for child_prefix in getattr(native_iter, "prefixes", []):
        line = f"gs://{bucket}/{child_prefix}"
        # Extract venue= from path
        parts = line.rstrip("/").split("/")
        for part in parts:
            if part.startswith("venue="):
                venues.append(part.replace("venue=", ""))
                break
    return venues


def _download_parquet(bucket_prefix: str, venue: str, dest: Path) -> bool:
    """Download a single venue's instruments.parquet from GCS."""
    src = f"{bucket_prefix}venue={venue}/instruments.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    bucket, path = src.removeprefix("gs://").split("/", 1)
    try:
        get_storage_client(provider="gcp").bucket(bucket).blob(path).download_to_filename(str(dest))
    except (OSError, ValueError, RuntimeError):
        return False
    return True


def _read_parquet(path: Path) -> list[dict[str, object]]:
    """Read a parquet file and return rows as dicts."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        LOG.error("pyarrow not installed — run: uv pip install pyarrow")
        sys.exit(1)

    table = pq.read_table(path)
    rows: list[dict[str, object]] = []
    # Convert to Python dicts, handling pyarrow types
    for batch in table.to_batches():
        for row_idx in range(batch.num_rows):
            row: dict[str, object] = {}
            for col_name in batch.schema.names:
                val = batch.column(col_name)[row_idx].as_py()
                # Convert datetimes to ISO strings for JSON
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                row[col_name] = val
            rows.append(row)
    return rows


def _load_sports_fixtures(workspace_root: Path) -> list[dict[str, object]]:
    """Load sports fixtures from e2e-testing live arb data."""
    odds_state_path = workspace_root / "e2e-testing" / "data" / "live_arb" / "odds_state.json"
    if not odds_state_path.exists():
        LOG.warning("No sports odds_state.json found at %s", odds_state_path)
        return []

    LOG.info("Loading sports fixtures from %s", odds_state_path)
    with open(odds_state_path) as f:
        data = json.load(f)

    odds_store = data.get("odds_store", {})  # noqa: qg-empty-fallback
    fixtures: list[dict[str, object]] = []

    for fixture_key, markets in odds_store.items():
        # fixture_key format: "league|team1|team2"
        parts = fixture_key.split("|")
        if len(parts) < 3:
            continue

        league = parts[0].strip()
        home_team = parts[1].strip()
        away_team = parts[2].strip()

        # Collect bookmakers that have odds for this fixture
        bookmakers: list[str] = []
        for _market_type, market_data in markets.items():
            if isinstance(market_data, dict):
                for bm in market_data.get("bookmakers", market_data.keys()):
                    if isinstance(bm, str) and bm not in bookmakers:
                        bookmakers.append(bm)

        fixture = {
            "instrument_key": f"SPORTS:FIXTURE:{league}:{home_team}-{away_team}".upper().replace(" ", "_"),
            "venue": "MULTI_VENUE",
            "instrument_type": "sports_fixture",
            "raw_symbol": fixture_key,
            "base_asset": home_team,
            "quote_asset": away_team,
            "status": "active",
            "asset_group": "sports",
            "league": league,
            "home_team": home_team,
            "away_team": away_team,
            "bookmakers": bookmakers,
        }
        fixtures.append(fixture)

    LOG.info("  Loaded %d sports fixtures", len(fixtures))
    return fixtures


def _load_sports_reference(workspace_root: Path) -> dict[str, object]:
    """Load sports reference data (team mappings, leagues) from UAC."""
    import csv

    ref: dict[str, object] = {}

    # Team mappings
    team_csv = (
        workspace_root
        / "unified-api-contracts"
        / "unified_api_contracts"
        / "canonical"
        / "domain"
        / "sports"
        / "data"
        / "team_mapping.csv"
    )
    if team_csv.exists():
        with open(team_csv) as f:
            reader = csv.DictReader(f)
            teams = list(reader)
        ref["team_count"] = len(teams)
        LOG.info("  Loaded %d team mappings", len(teams))
    else:
        ref["team_count"] = 0

    return ref


def generate_snapshot(
    date: str,
    workspace_root: Path,
    output_dir: Path,
) -> Path:
    """Pull all instruments from GCS and produce a JSON snapshot."""
    LOG.info("Generating instrument snapshot for date=%s", date)

    all_instruments: list[dict[str, object]] = []
    venue_summary: dict[str, dict[str, int]] = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        for category in CATEGORIES:
            bucket_prefix = _instrument_bucket_prefix(category, date)

            LOG.info("\n%s. Listing venues in %s...", category.upper(), bucket_prefix[:60])
            venues = _list_venues(bucket_prefix)

            if not venues:
                LOG.info("  No venues found for %s", category)
                continue

            LOG.info("  Found %d venues", len(venues))
            category_total = 0

            for venue in venues:
                dest = tmppath / category / venue / "instruments.parquet"
                if _download_parquet(bucket_prefix, venue, dest):
                    rows = _read_parquet(dest)
                    # Tag each row with category
                    for row in rows:
                        row["category"] = category
                    all_instruments.extend(rows)
                    category_total += len(rows)
                    venue_summary.setdefault(category, {})[venue] = len(rows)
                    LOG.info("  %s: %d instruments", venue, len(rows))
                else:
                    LOG.warning("  FAILED to download %s/%s", category, venue)

            LOG.info("  --- %s total: %d", category, category_total)

    # Add sports fixtures from e2e-testing if no GCS sports data
    if "sports" not in venue_summary or not venue_summary.get("sports"):
        fixtures = _load_sports_fixtures(workspace_root)
        if fixtures:
            all_instruments.extend(fixtures)
            venue_summary["sports"] = {"FIXTURES_FROM_LIVE_ARB": len(fixtures)}

    # Load sports reference metadata
    sports_ref = _load_sports_reference(workspace_root)

    # Build the snapshot
    snapshot = {
        "_meta": {
            "date": date,
            "generated_by": "generate_instrument_snapshot.py",
            "total_instruments": len(all_instruments),
            "categories": {cat: sum(v.values()) for cat, v in venue_summary.items()},
            "venues": venue_summary,
            "sports_reference": sports_ref,
        },
        "instruments": all_instruments,
    }

    # Strip null/empty values to reduce file size (~40% reduction)
    # Add hasMarketData: true to every instrument — the UI assumes market data
    # exists for all snapshot instruments (mock handler generates synthetic data).
    stripped_instruments: list[dict[str, object]] = []
    for inst in all_instruments:
        stripped = {k: v for k, v in inst.items() if v is not None and v != ""}
        stripped["hasMarketData"] = True
        stripped_instruments.append(stripped)
    snapshot["instruments"] = stripped_instruments

    # Write output (compact JSON, no indent)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "instruments-snapshot.json"
    with open(output_path, "w") as f:
        json.dump(snapshot, f, separators=(",", ":"), default=str)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    LOG.info("\nSnapshot written: %s (%.1f MB)", output_path, size_mb)
    LOG.info("Total instruments: %d", len(all_instruments))
    LOG.info("Categories: %s", {k: sum(v.values()) for k, v in venue_summary.items()})

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate instrument snapshot from GCS")
    parser.add_argument(
        "--date",
        default="2026-03-27",
        help="Date to pull instruments for (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output-dir",
        default="unified-api-contracts/openapi",
        help="Output directory for the snapshot JSON",
    )
    parser.add_argument(
        "--workspace-root",
        default=None,
        help="Workspace root (auto-detected if not set)",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root) if args.workspace_root else Path(__file__).resolve().parents[3]
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = workspace_root / output_dir

    generate_snapshot(args.date, workspace_root, output_dir)


if __name__ == "__main__":
    main()
