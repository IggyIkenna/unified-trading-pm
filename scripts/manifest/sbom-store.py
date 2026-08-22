#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
sbom-store.py — Store pip-audit JSON output (SBOM) in GCS as an audit trail.

Called non-blocking from quality-gates.sh:
    python ... --project-id <project_id> --service-name "$SERVICE_NAME" \
        /tmp/pip-audit-output.json || true
Stores to: gs://{bucket}/sboms/{service_name}/{date}/{timestamp}.json

Args:
    --project-id    — project ID (required; pass via --project-id or canonical env var)
    --bucket        — GCS bucket name (default: uts-sbom-audit)
    --service-name  — Name of the service running quality gates (default: unknown)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import cast


def _load_storage_client():
    try:
        uts = __import__("unified_trading_services", fromlist=["get_storage_client"])
        return uts.get_storage_client
    except ImportError:
        return None  # acceptable: optional GCS upload in PM tooling script; caller checks for None


get_storage_client = _load_storage_client()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Store pip-audit JSON output (SBOM) in GCS as an audit trail.",
    )
    parser.add_argument(
        "audit_file",
        type=Path,
        help="Path to pip-audit JSON output file",
    )
    parser.add_argument(
        "--project-id",
        required=False,
        default="",
        help="project ID (required for upload; pass via --project-id)",
    )
    parser.add_argument(
        "--bucket",
        default="uts-sbom-audit",
        help="GCS bucket name (default: uts-sbom-audit)",
    )
    parser.add_argument(
        "--service-name",
        default="unknown",
        help="Name of the service running quality gates (default: unknown)",
    )
    args = parser.parse_args()

    if not args.audit_file.exists():
        logger.warning("SBOM file not found: %s — skipping GCS upload", args.audit_file)
        sys.exit(0)

    project_id = (args.project_id or "").strip()
    if not project_id:
        logger.warning("--project-id not set — skipping SBOM GCS upload")
        sys.exit(0)

    with open(args.audit_file) as f:
        audit_data = cast(dict[str, object], json.load(f))

    now = datetime.now(UTC)
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y%m%dT%H%M%SZ")
    blob_path = f"sboms/{args.service_name}/{date_str}/{timestamp_str}.json"

    payload: dict[str, str | dict[str, object]] = {
        "service_name": args.service_name,
        "generated_at": now.isoformat(),
        "pip_audit_output": audit_data,
    }

    if get_storage_client is None:
        logger.warning("unified_trading_services not installed — skipping SBOM GCS upload")
        sys.exit(0)

    try:
        client = get_storage_client(project_id=project_id)
        bucket = client.bucket(args.bucket)
        blob = bucket.blob(blob_path)
        upload_fn = cast(Callable[..., None], blob.upload_from_string)
        upload_fn(
            json.dumps(payload, indent=2),
            content_type="application/json",
        )
        logger.info("SBOM stored: gs://%s/%s", args.bucket, blob_path)
    except (OSError, ValueError) as exc:
        logger.warning("SBOM upload failed (non-blocking): %s", exc)
        sys.exit(0)


if __name__ == "__main__":
    main()
