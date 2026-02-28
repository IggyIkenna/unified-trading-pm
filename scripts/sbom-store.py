#!/usr/bin/env python3
"""
sbom-store.py — Store pip-audit JSON output (SBOM) in GCS as an audit trail.

Called non-blocking from quality-gates.sh:
    python unified-trading-pm/scripts/sbom-store.py /tmp/pip-audit-output.json || true

Uses get_storage_client() from unified_trading_services (never direct google.cloud.storage).
Stores to: gs://{bucket}/sboms/{service_name}/{date}/{timestamp}.json

Required env vars:
    GCP_PROJECT_ID    — GCP project ID (no GOOGLE_CLOUD_PROJECT per workspace rules)
    SBOM_BUCKET       — GCS bucket name (default: uts-sbom-audit)
    SERVICE_NAME      — Name of the service running quality gates (default: unknown)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: sbom-store.py <pip-audit-json-output-file>", file=sys.stderr)
        sys.exit(1)

    audit_file = sys.argv[1]

    if not os.path.exists(audit_file):
        print(f"⚠️  SBOM file not found: {audit_file} — skipping GCS upload", file=sys.stderr)
        sys.exit(0)

    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        print("⚠️  GCP_PROJECT_ID not set — skipping SBOM GCS upload", file=sys.stderr)
        sys.exit(0)

    bucket_name = os.environ.get("SBOM_BUCKET", "uts-sbom-audit")
    service_name = os.environ.get("SERVICE_NAME", "unknown")

    try:
        from unified_trading_services import get_storage_client
    except ImportError:
        print(
            "⚠️  unified_trading_services not installed — skipping SBOM GCS upload",
            file=sys.stderr,
        )
        sys.exit(0)

    with open(audit_file) as f:
        audit_data = json.load(f)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y%m%dT%H%M%SZ")
    blob_path = f"sboms/{service_name}/{date_str}/{timestamp_str}.json"

    payload = {
        "service_name": service_name,
        "generated_at": now.isoformat(),
        "pip_audit_output": audit_data,
    }

    try:
        client = get_storage_client(project_id=project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(
            json.dumps(payload, indent=2),
            content_type="application/json",
        )
        print(f"✅ SBOM stored: gs://{bucket_name}/{blob_path}")
    except Exception as exc:
        print(f"⚠️  SBOM upload failed (non-blocking): {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
