#!/usr/bin/env python3.13
"""
Delete instruments and market-tick data from GCS for specific dates only.

Uses unified-trading-services (get_storage_client) for all GCS operations.
No gsutil dependency.

SAFETY:
- Default: --dry-run lists files to delete, NO deletion
- --execute: actually deletes, but requires typing "DELETE" to confirm
- Only deletes the EXACT dates specified (2025-11-01 to 2025-11-10)
- Validates paths before any operation

Usage:
  python scripts/delete_gcs_data_for_dates.py [--dry-run]           # List only (default)
  python scripts/delete_gcs_data_for_dates.py --execute              # Delete (prompts for confirmation)
  python scripts/delete_gcs_data_for_dates.py --dates 2025-11-01,2025-11-02  # Custom dates
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Ensure unified-trading-services is on path (sibling in workspace)
REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
UCS_PATH = WORKSPACE_ROOT / "unified-trading-services"
if UCS_PATH.exists() and str(UCS_PATH) not in sys.path:
    sys.path.insert(0, str(UCS_PATH))  # unified-trading-services/ contains unified_trading_services/

# ruff: noqa: E402
from unified_trading_services import (
    get_bucket_name,
    get_project_id,
    get_storage_client,
)


def _resolve_credentials_path() -> str | None:
    """
    Resolve GCP credentials path for get_storage_client.
    If GOOGLE_APPLICATION_CREDENTIALS is set to a relative path that doesn't exist,
    search for the credentials file in common workspace locations.
    Returns None to use default application credentials (ADC) when appropriate.
    """
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds:
        return None
    p = Path(creds)
    if p.is_absolute() and p.exists():
        return creds
    if p.exists():
        return str(p.resolve())
    # Search common locations for the credentials filename
    name = p.name
    for base in (UCS_PATH, WORKSPACE_ROOT / "deployment-service", REPO_ROOT):
        candidate = base / name
        if candidate.exists():
            return str(candidate.resolve())
    return None


# Date format we allow (strict validation)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

INSTRUMENTS_PREFIX = "instrument_availability/by_date"
# Market-tick bucket prefixes (all 3 for each date in CEFI, TRADFI, DEFI)
MARKET_DATA_PREFIXES = (
    "raw_tick_data/by_date",
    "processed_candles/by_date",
    "market-tick-data/by_date",
)

# Default dates: 2025-11-01 to 2025-11-10
DEFAULT_DATES = [
    "2025-11-01",
    "2025-11-02",
    "2025-11-03",
    "2025-11-04",
    "2025-11-05",
    "2025-11-06",
    "2025-11-07",
    "2025-11-08",
    "2025-11-09",
    "2025-11-10",
]

CATEGORIES = ("CEFI", "TRADFI", "DEFI")


def validate_date(d: str) -> bool:
    """Ensure date matches YYYY-MM-DD exactly."""
    return bool(DATE_PATTERN.match(d))


def build_delete_paths(
    dates: list[str],
    category_only: str | None = None,
    domain_only: str | None = None,
) -> list[tuple[str, str]]:
    """
    Build list of (bucket, prefix) to delete.
    Uses unified-trading-services get_bucket_name for bucket resolution.
    """
    paths: list[tuple[str, str]] = []
    project_id = get_project_id()
    categories = (category_only,) if category_only else CATEGORIES
    do_instruments = domain_only is None or domain_only == "instruments"
    do_market_data = domain_only is None or domain_only == "market_data"

    for date in dates:
        if not validate_date(date):
            raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD")
        day_prefix = f"day-{date}"
        if do_instruments:
            for cat in categories:
                bucket = get_bucket_name("instruments", cat, project_id)
                prefix = f"{INSTRUMENTS_PREFIX}/{day_prefix}"
                paths.append((bucket, prefix))
        if do_market_data:
            for cat in categories:
                bucket = get_bucket_name("market_data", cat, project_id)
                for mkt_prefix in MARKET_DATA_PREFIXES:
                    prefix = f"{mkt_prefix}/{day_prefix}"
                    paths.append((bucket, prefix))
    return paths


def list_objects(storage_client, bucket: str, prefix: str) -> list[str]:
    """List blob paths under bucket/prefix using unified-trading-services StorageClient."""
    blob_paths: list[str] = []
    try:
        for meta in storage_client.list_blobs(bucket, prefix=prefix):
            blob_paths.append(meta.name)
    except (ConnectionError, TimeoutError, OSError, ValueError) as e:
        print(f"Warning: Failed to list gs://{bucket}/{prefix}: {e}", file=sys.stderr)
    return blob_paths


def delete_objects(storage, bucket: str, blob_paths: list[str]) -> int:
    """Delete blobs using unified-trading-services StorageClient. Returns count deleted."""
    if not blob_paths:
        return 0
    return storage.delete_blobs(bucket, blob_paths)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete instruments and market-tick GCS data for specific dates (with dry-run)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="List files to delete, do NOT delete (default)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete. Requires typing DELETE to confirm.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (use with --execute for non-interactive).",
    )
    parser.add_argument(
        "--category-only",
        type=str,
        choices=("CEFI", "TRADFI", "DEFI"),
        help="Only delete from this category (e.g. CEFI for market-data-tick-cefi).",
    )
    parser.add_argument(
        "--domain-only",
        type=str,
        choices=("instruments", "market_data"),
        help="Only delete from this domain (market_data = raw_tick_data, processed_candles, market-tick-data).",
    )
    parser.add_argument(
        "--dates",
        type=str,
        default=",".join(DEFAULT_DATES),
        help="Comma-separated dates (YYYY-MM-DD). Default: 2025-11-01 to 2025-11-10",
    )
    args = parser.parse_args()

    dry_run = not args.execute
    dates = [d.strip() for d in args.dates.split(",") if d.strip()]

    if not dates:
        print("Error: No dates specified.", file=sys.stderr)
        sys.exit(1)

    for d in dates:
        if not validate_date(d):
            print(f"Error: Invalid date '{d}'. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    paths = build_delete_paths(
        dates,
        category_only=getattr(args, "category_only", None),
        domain_only=getattr(args, "domain_only", None),
    )

    scope = []
    if getattr(args, "category_only", None):
        scope.append(f"category={args.category_only}")
    if getattr(args, "domain_only", None):
        scope.append(f"domain={args.domain_only}")
    scope_str = f" [{', '.join(scope)}]" if scope else ""

    print("=" * 70)
    print("GCS DATA DELETION - INSTRUMENTS + MARKET-TICK" + scope_str)
    print("=" * 70)
    print(f"Dates: {', '.join(dates)}")
    print(f"Mode: {'DRY-RUN (list only, no deletion)' if dry_run else 'EXECUTE (will delete)'}")
    print("Storage: unified-trading-services get_storage_client()")
    print("=" * 70)

    # Get storage client from unified-trading-services
    creds_path = _resolve_credentials_path()
    storage = get_storage_client(credentials_path=creds_path)

    # Collect all objects to delete (and which prefixes have data)
    all_objects: list[str] = []
    by_bucket: dict[str, list[str]] = {}
    paths_with_data: list[tuple[str, str]] = []

    for bucket, prefix in paths:
        objects = list_objects(storage, bucket, prefix)
        if objects:
            by_bucket.setdefault(bucket, []).extend(objects)
            all_objects.extend(objects)
            paths_with_data.append((bucket, prefix))

    # Report
    print("\n--- PREFIXES TO DELETE (only these exact paths) ---\n")
    for bucket, prefix in paths_with_data:
        print(f"  gs://{bucket}/{prefix}/")
    print()

    print("\n--- FILES TO DELETE ---\n")
    for bucket in sorted(by_bucket.keys()):
        objs = by_bucket[bucket]
        print(f"  {bucket}: {len(objs)} objects")
        for o in objs[:10]:  # Show first 10 per bucket
            print(f"    {o}")
        if len(objs) > 10:
            print(f"    ... and {len(objs) - 10} more")
        print()

    total = len(all_objects)
    print(f"TOTAL: {total} objects across {len(by_bucket)} buckets")
    print()

    if total == 0:
        print("No objects found for these dates. Nothing to delete.")
        return

    if dry_run:
        print("DRY-RUN: No files were deleted.")
        print("To actually delete, run: python scripts/delete_gcs_data_for_dates.py --execute")
        return

    # Execute: require confirmation (unless --yes)
    if not getattr(args, "yes", False):
        print("=" * 70)
        print("⚠️  WARNING: You are about to PERMANENTLY DELETE the above data.")
        print("⚠️  This cannot be undone.")
        print("=" * 70)
        print('Type "DELETE" (exactly) to confirm: ', end="")
        try:
            confirm = input().strip()
        except EOFError:
            confirm = ""
        if confirm != "DELETE":
            print("Aborted. No data was deleted.")
            sys.exit(0)

    print("\nDeleting (parallel by bucket, batch API per bucket)...")
    deleted_total = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(delete_objects, storage, bucket, blob_paths): bucket for bucket, blob_paths in by_bucket.items()
        }
        for fut in as_completed(futures):
            bucket = futures[fut]
            try:
                deleted = fut.result()
                deleted_total += deleted
                print(f"  {bucket}: deleted {deleted} objects")
            except (ConnectionError, TimeoutError, OSError, ValueError) as e:
                print(f"  {bucket}: ERROR {e}", file=sys.stderr)

    if deleted_total == total:
        print(f"\n✓ Deleted {deleted_total} objects (from {len(paths_with_data)} prefixes).")
    else:
        print(
            f"\n⚠ Deleted {deleted_total}/{total} objects. Some may have been missing.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
