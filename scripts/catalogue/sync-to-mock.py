# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Copy date-partitioned GCS data into a mock-tier scenario bucket.

Derives source/target buckets from the UCI three-tier model (get_bucket_name),
copies date-partitioned files for the specified date range, and writes a
manifest entry to the data catalogue.

Usage:
    python3 unified-trading-pm/scripts/catalogue/sync-to-mock.py \
        --name stress \
        --service market-tick-data-service \
        --asset-group CEFI \
        --from-env prod \
        --start-date 2026-01-01 \
        --end-date 2026-01-31

    python3 unified-trading-pm/scripts/catalogue/sync-to-mock.py \
        --name eth-backtest \
        --services instruments-service,market-tick-data-service \
        --asset-group DEFI \
        --from-env prod \
        --start-date 2025-06-01 \
        --end-date 2025-06-30 \
        --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, date, datetime, timedelta

from google.cloud import storage
from google.cloud.storage.retry import DEFAULT_RETRY

logger = logging.getLogger(__name__)

_GROUP_A_DOMAINS = frozenset({"instruments", "market_data", "features_calendar", "data_catalogue"})

BUCKET_PREFIXES = {
    "instruments": "instruments-store",
    "market_data": "market-data-tick",
    "features_calendar": "features-calendar",
    "features_delta_one": "features-delta-one",
    "features_onchain": "features-onchain",
    "features_volatility": "features-volatility",
    "execution": "execution-store",
    "strategy": "strategy-store",
    "ml_models": "ml-models-store",
    "ml_predictions": "ml-predictions-store",
    "ml_configs": "ml-configs-store",
    "data_catalogue": "data-catalogue",
    "pnl": "pnl-store",
}

SERVICE_TO_DOMAIN = {
    "instruments-service": "instruments",
    "market-tick-data-service": "market_data",
    "features-calendar-service": "features_calendar",
    "features-delta-one-service": "features_delta_one",
    "features-onchain-service": "features_onchain",
    "features-volatility-service": "features_volatility",
    "execution-service": "execution",
    "strategy-service": "strategy",
    "ml-training-service": "ml_models",
    "ml-inference-service": "ml_predictions",
    "pnl-attribution-service": "pnl",
}


def _get_bucket_name(domain: str, category: str, env: str | None, project_id: str) -> str:
    prefix = BUCKET_PREFIXES.get(domain, domain)
    is_group_a = domain in _GROUP_A_DOMAINS
    cat = category.lower()

    if is_group_a:
        return f"{prefix}-{cat}-{project_id}"
    if env:
        return f"{prefix}-{cat}-{env}-{project_id}"
    return f"{prefix}-{cat}-{project_id}"


def _generate_dates(start: date, end: date) -> list[date]:
    dates: list[date] = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def _copy_day(
    client: storage.Client,
    src_bucket_name: str,
    tgt_bucket_name: str,
    category: str,
    day: date,
    scenario_name: str,
    *,
    dry_run: bool,
) -> int:
    src_bucket = client.bucket(src_bucket_name)
    tgt_bucket = client.bucket(tgt_bucket_name)

    src_prefix = f"category={category}/day={day.isoformat()}/"
    blobs = list(client.list_blobs(src_bucket, prefix=src_prefix))

    if not blobs:
        logger.debug("No blobs at gs://%s/%s", src_bucket_name, src_prefix)
        return 0

    copied = 0
    for blob in blobs:
        relative = blob.name[len(src_prefix) :]
        tgt_name = f"scenario={scenario_name}/day={day.isoformat()}/{relative}"

        if dry_run:
            logger.info("[DRY-RUN] gs://%s/%s -> gs://%s/%s", src_bucket_name, blob.name, tgt_bucket_name, tgt_name)
        else:
            # No generation precondition -> google-cloud-storage's default ConditionalRetryPolicy
            # won't auto-retry a transient 429/503 on a bare copy; DEFAULT_RETRY (same policy
            # backing reload()/exists()/delete()) is safe here since re-copying is idempotent.
            src_bucket.copy_blob(blob, tgt_bucket, new_name=tgt_name, retry=DEFAULT_RETRY)
        copied += 1

    return copied


def _write_manifest(
    client: storage.Client,
    catalogue_bucket: str,
    service: str,
    category: str,
    scenario_name: str,
    start: date,
    end: date,
    total_files: int,
    *,
    dry_run: bool,
) -> None:
    import json

    manifest = {
        "service": service,
        "category": category,
        "scenario": scenario_name,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_files_copied": total_files,
        "synced_at": datetime.now(UTC).isoformat(),
    }

    path = f"sync-manifests/{service}/{category}/{scenario_name}.json"
    if dry_run:
        logger.info("[DRY-RUN] Would write manifest to gs://%s/%s", catalogue_bucket, path)
        logger.info("%s", json.dumps(manifest, indent=2))
        return

    bucket = client.bucket(catalogue_bucket)
    blob = bucket.blob(path)
    blob.upload_from_string(json.dumps(manifest, indent=2), content_type="application/json")
    logger.info("Wrote manifest to gs://%s/%s", catalogue_bucket, path)


def sync_to_mock(
    scenario_name: str,
    services: list[str],
    category: str,
    from_env: str,
    start_date: date,
    end_date: date,
    project_id: str,
    *,
    dry_run: bool = False,
) -> None:
    client = storage.Client(project=project_id)
    dates = _generate_dates(start_date, end_date)
    catalogue_bucket = f"data-catalogue-{project_id}"

    logger.info(
        "Syncing %d service(s), %d day(s), category=%s, from=%s, scenario=%s",
        len(services),
        len(dates),
        category,
        from_env,
        scenario_name,
    )

    for service in services:
        domain = SERVICE_TO_DOMAIN.get(service)
        if not domain:
            logger.error("Unknown service %r — add to SERVICE_TO_DOMAIN mapping", service)
            sys.exit(1)

        is_group_a = domain in _GROUP_A_DOMAINS
        src_bucket = _get_bucket_name(domain, category, from_env if not is_group_a else None, project_id)
        tgt_bucket = _get_bucket_name(domain, category, "mock" if not is_group_a else None, project_id)

        logger.info("Service: %s (domain=%s)", service, domain)
        logger.info("  Source: gs://%s/", src_bucket)
        logger.info("  Target: gs://%s/scenario=%s/", tgt_bucket, scenario_name)

        total_files = 0
        for day in dates:
            copied = _copy_day(
                client,
                src_bucket,
                tgt_bucket,
                category,
                day,
                scenario_name,
                dry_run=dry_run,
            )
            total_files += copied
            if copied:
                logger.info("  %s: %d file(s)", day.isoformat(), copied)

        _write_manifest(
            client,
            catalogue_bucket,
            service,
            category,
            scenario_name,
            start_date,
            end_date,
            total_files,
            dry_run=dry_run,
        )

        logger.info("  Total: %d file(s) copied%s", total_files, " [DRY-RUN]" if dry_run else "")

    logger.info("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy date-partitioned GCS data into a mock-tier scenario bucket")
    parser.add_argument("--name", required=True, help="Scenario name (e.g. stress, eth-backtest)")
    svc_group = parser.add_mutually_exclusive_group(required=True)
    svc_group.add_argument("--service", help="Single service name")
    svc_group.add_argument("--services", help="Comma-separated service names")
    parser.add_argument("--asset-group", required=True, help="Category (CEFI, TRADFI, DEFI)")
    parser.add_argument("--from-env", required=True, help="Source environment (prod, dev)")
    parser.add_argument("--start-date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--project-id", help="GCP project ID (falls back to GCP_PROJECT_ID)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    project_id = args.project_id or os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        logger.error("--project-id required or set GCP_PROJECT_ID env var")
        sys.exit(1)

    services_list = [args.service] if args.service else [s.strip() for s in args.services.split(",")]
    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date)

    if start > end:
        logger.error("--start-date must be <= --end-date")
        sys.exit(1)

    sync_to_mock(
        scenario_name=args.name,
        services=services_list,
        category=args.category,
        from_env=args.from_env,
        start_date=start,
        end_date=end,
        project_id=project_id,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
