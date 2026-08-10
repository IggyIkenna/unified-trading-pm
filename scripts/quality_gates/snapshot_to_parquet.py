# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""
QG snapshot → parquet writer (B-018 Phase 4.A).

Reads per-repo JSON lines from stdin (output of snapshot.sh), writes one
parquet per repo per day into GCS under the hive-partitioned path:

    gs://{project_id}-deployment-events/
        quality_gates_snapshot/
            repo={repo}/
                quality_gates_snapshot_{YYYY_MM_DD}.parquet

Schema (matches what deployment-api/routes/repo_readiness.py reads):
    repo             str   — repo name
    qg_status        str   — "green" | "red" | "skipped"
    pull_sha         str   — git HEAD SHA at snapshot time (empty string if null)
    failing_step     str   — last STEP marker from log (empty string if null)
    first_error_line str   — first error line from log (empty string if null, 200 chars max)
    duration_seconds int64 — wall-clock QG runtime in seconds
    snapshot_at      str   — ISO-8601 UTC timestamp

Usage:
    bash snapshot.sh | python3 snapshot_to_parquet.py --project-id central-element-323112

Plan: deployment_and_qg_strategy_implementation_2026_05_13.md Phase 4.A.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import UTC, datetime


def _build_parquet_bytes(rows: list[dict[str, object]]) -> dict[str, bytes]:
    """Build per-repo parquet bytes. Returns {repo: parquet_bytes}."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema(
        [
            pa.field("repo", pa.string()),
            pa.field("qg_status", pa.string()),
            pa.field("pull_sha", pa.string()),
            pa.field("failing_step", pa.string()),
            pa.field("first_error_line", pa.string()),
            pa.field("duration_seconds", pa.int64()),
            pa.field("snapshot_at", pa.string()),
        ]
    )

    result: dict[str, bytes] = {}
    for row in rows:
        repo = str(row.get("repo") or "unknown")
        table = pa.table(
            {
                "repo": [repo],
                "qg_status": [str(row.get("qg_status") or "")],
                "pull_sha": [str(row.get("pull_sha") or "")],
                "failing_step": [str(row.get("failing_step") or "")],
                "first_error_line": [str(row.get("first_error_line") or "")],
                "duration_seconds": [int(row.get("duration_seconds") or 0)],
                "snapshot_at": [str(row.get("snapshot_at") or "")],
            },
            schema=schema,
        )
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        result[repo] = buf.getvalue()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Write QG snapshot parquets to GCS")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--date", default=None, help="Snapshot date YYYY_MM_DD (default: today UTC)")
    args = parser.parse_args()

    project_id: str = args.project_id
    date_str: str = args.date or datetime.now(UTC).strftime("%Y_%m_%d")

    rows: list[dict[str, object]] = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("QG snapshot"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"WARN: skipping unparseable line: {exc}", file=sys.stderr)

    if not rows:
        print("ERROR: no rows received from stdin", file=sys.stderr)
        sys.exit(1)

    from unified_trading_library import upload_to_storage

    parquet_map = _build_parquet_bytes(rows)

    bucket_name = f"{project_id}-deployment-events"
    uploaded = 0
    failed = 0
    for repo, parquet_bytes in parquet_map.items():
        blob_path = f"quality_gates_snapshot/repo={repo}/quality_gates_snapshot_{date_str}.parquet"
        try:
            upload_to_storage(bucket_name, blob_path, parquet_bytes, "application/octet-stream")
            print(f"OK  {repo} → gs://{bucket_name}/{blob_path}")
            uploaded += 1
        except Exception as exc:  # noqa: broad-except — per-repo isolation: one repo's upload
            # failure must not abort the batch upload for the remaining repos
            print(f"ERR {repo} upload failed: {exc}", file=sys.stderr)
            failed += 1

    print(f"\nDone: {uploaded} uploaded, {failed} failed", file=sys.stderr)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
