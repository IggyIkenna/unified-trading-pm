# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Sync data-catalogue YAML files from Parquet manifests in GCS.

Reads all Parquet manifests from data-catalogue-{project_id}/ via DuckDB,
aggregates per-service/category (latest date, total row count, date range),
and updates the PM configs/data-catalogue.*.yaml files.

Usage:
    python3 unified-trading-pm/scripts/catalogue/sync-catalogue-yaml.py \
        --project-id my-proj

    python3 unified-trading-pm/scripts/catalogue/sync-catalogue-yaml.py \
        --project-id my-proj --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import yaml

logger = logging.getLogger(__name__)

PM_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = PM_ROOT / "configs"

CATALOGUE_BUCKET_PREFIX = "data-catalogue"


def _build_catalogue_query(bucket: str) -> str:
    return f"""
        SELECT
            service_name,
            category,
            MIN(date) AS min_date,
            MAX(date) AS max_date,
            COUNT(*) AS total_rows,
            MAX(date) AS latest_date
        FROM read_parquet('gs://{bucket}/**/manifest.parquet', hive_partitioning=true)
        GROUP BY service_name, category
        ORDER BY service_name, category
    """


def _load_existing_yaml(service_name: str) -> dict[str, object]:
    path = CONFIGS_DIR / f"data-catalogue.{service_name}.yaml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _write_yaml(service_name: str, data: dict[str, object], dry_run: bool) -> None:
    path = CONFIGS_DIR / f"data-catalogue.{service_name}.yaml"
    if dry_run:
        logger.info("[DRY-RUN] Would write %s", path)
        logger.info("%s", yaml.dump(data, default_flow_style=False, sort_keys=False))
        return
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    logger.info("Wrote %s", path)


def sync_catalogue(project_id: str, *, dry_run: bool = False) -> None:
    bucket = f"{CATALOGUE_BUCKET_PREFIX}-{project_id}"
    query = _build_catalogue_query(bucket)

    logger.info("Querying catalogue bucket: gs://%s/", bucket)

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET s3_region='auto';")

    rows = con.execute(query).fetchall()
    columns = ["service_name", "category", "min_date", "max_date", "total_rows", "latest_date"]
    con.close()

    if not rows:
        logger.warning("No manifest data found in gs://%s/", bucket)
        return

    services: dict[str, dict[str, object]] = {}
    for row in rows:
        record = dict(zip(columns, row, strict=False))
        svc = str(record["service_name"])
        cat = str(record["category"])

        if svc not in services:
            existing = _load_existing_yaml(svc)
            services[svc] = {
                "service_name": svc,
                "last_updated": datetime.now(UTC).strftime("%Y-%m-%d"),
                "auto_refreshed": datetime.now(UTC).isoformat(),
                "status": existing.get("status", "UNKNOWN"),
                "known_exceptions": existing.get("known_exceptions", []),  # noqa: qg-empty-fallback
                "catalogue_dimensions": existing.get("catalogue_dimensions", ["category", "venue", "date"]),
                "shard_status": existing.get("shard_status", {}),  # noqa: qg-empty-fallback
            }

        shard = services[svc].setdefault("shard_status", {})
        if not isinstance(shard, dict):
            shard = {}
            services[svc]["shard_status"] = shard

        cat_data = shard.get(cat, {})
        if not isinstance(cat_data, dict):
            cat_data = {}

        cat_data["_catalogue_sync"] = {
            "min_date": str(record["min_date"]),
            "max_date": str(record["max_date"]),
            "total_rows": int(record["total_rows"]),
            "latest_date": str(record["latest_date"]),
            "synced_at": datetime.now(UTC).isoformat(),
        }
        shard[cat] = cat_data

    for svc, data in services.items():
        _write_yaml(svc, data, dry_run)

    logger.info(
        "Synced %d service(s), %d category record(s)%s",
        len(services),
        len(rows),
        " [DRY-RUN]" if dry_run else "",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync data-catalogue YAML from Parquet manifests in GCS")
    parser.add_argument(
        "--project-id",
        required=False,
        help="GCP project ID (falls back to GCP_PROJECT_ID env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes without writing files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    import os

    project_id = args.project_id or os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        logger.error("--project-id required or set GCP_PROJECT_ID env var")
        sys.exit(1)

    sync_catalogue(project_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
