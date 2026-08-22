# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG snapshot staleness checker (B-018 Phase 4.A monitoring, 2026-05-15).

Checks whether a QG snapshot parquet has been written to GCS for each of the
last N days (default: 2). If all checked dates are missing, emits a
QG_SNAPSHOT_STALE log event and exits with code 1.

Usage (from the qg-snapshot cron VM, after snapshot_to_parquet.py):
    python3 check_snapshot_staleness.py --project-id <YOUR_PROJECT_ID>
    python3 check_snapshot_staleness.py --project-id <YOUR_PROJECT_ID> --lookback-days 3
    python3 check_snapshot_staleness.py --project-id <YOUR_PROJECT_ID> --dry-run
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from typing import cast


def _list_snapshot_dates(bucket_name: str) -> set[str]:
    from unified_trading_library import get_storage_client  # type: ignore[import-not-found]

    client = get_storage_client()
    raw = list(client.list_blobs(bucket_name, prefix="quality_gates_snapshot/"))
    found: set[str] = set()
    for blob in raw:
        blob_name: str = blob.name
        filename = blob_name.rstrip("/").split("/")[-1]
        if filename.startswith("quality_gates_snapshot_") and filename.endswith(".parquet"):
            date_part = filename[len("quality_gates_snapshot_") : -len(".parquet")]
            if len(date_part) == 10 and date_part[4] == "_" and date_part[7] == "_":
                found.add(date_part)
    return found


def check_staleness(
    project_id: str,
    lookback_days: int = 2,
    *,
    today: datetime | None = None,
) -> tuple[int, list[str], str | None]:
    """Return (stale_days, checked_dates, last_snapshot_date)."""
    ref_date = (today or datetime.now(UTC)).replace(hour=0, minute=0, second=0, microsecond=0)
    checked_dates = [(ref_date - timedelta(days=i)).strftime("%Y_%m_%d") for i in range(lookback_days)]
    bucket_name = f"{project_id}-deployment-events"
    found_dates = _list_snapshot_dates(bucket_name)
    missing = [d for d in checked_dates if d not in found_dates]
    present = [d for d in checked_dates if d in found_dates]
    last_snapshot_date: str | None = present[0] if present else None
    return len(missing), checked_dates, last_snapshot_date


def emit_stale_alert(
    project_id: str,
    stale_days: int,
    checked_dates: list[str],
    last_snapshot_date: str | None,
) -> None:
    from unified_trading_library import log_event  # type: ignore[import-not-found]

    bucket_path = f"gs://{project_id}-deployment-events/quality_gates_snapshot/"
    log_event(
        "QG_SNAPSHOT_STALE",
        details={
            "stale_days": stale_days,
            "last_snapshot_date": last_snapshot_date,
            "bucket_path": bucket_path,
            "checked_dates": checked_dates,
            "message": (f"QG snapshot missing for {stale_days} of the last {len(checked_dates)} days."),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check QG snapshot staleness and emit QG_SNAPSHOT_STALE alert if needed.",
    )
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=2,
        help="Number of consecutive days to check (default: 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check staleness but do not emit the alert event",
    )
    args = parser.parse_args()
    project_id: str = cast(str, args.project_id)
    lookback_days: int = cast(int, args.lookback_days)
    dry_run: bool = cast(bool, args.dry_run)

    stale_days, checked_dates, last_snapshot_date = check_staleness(project_id, lookback_days)

    if stale_days >= lookback_days:
        print(
            f"STALE: {stale_days}/{lookback_days} days missing (last seen: {last_snapshot_date or 'never'})",
            flush=True,
        )
        if not dry_run:
            emit_stale_alert(project_id, stale_days, checked_dates, last_snapshot_date)
        sys.exit(1)
    else:
        print(
            f"OK: snapshot present for {lookback_days - stale_days}/{lookback_days} checked days"
            f" (last: {last_snapshot_date})",
            flush=True,
        )


if __name__ == "__main__":
    main()
