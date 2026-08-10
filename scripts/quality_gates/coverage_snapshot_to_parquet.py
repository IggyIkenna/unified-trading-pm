# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""coverage_snapshot_to_parquet.py — per-repo coverage → GCS daily writer.

Sibling of snapshot_to_parquet.py (Phase 4.A). Reads JSON lines from stdin
(output of coverage_snapshot.sh) and writes one parquet per repo per day:

    gs://{project_id}-deployment-events/
        coverage_snapshot/
            repo={repo}/
                coverage_snapshot_{YYYY_MM_DD}.parquet

Schema:
    repo             str   — repo name
    surface          str   — surface name from coverage_targets.yaml
    target_pct       int64 — declared target
    actual_pct       float — actual aggregate per surface (lines_covered/lines_valid)
    files_matched    int64 — count of files contributing to this aggregate
    lines_covered    int64 — sum of covered lines across matched files
    lines_valid      int64 — sum of total lines across matched files
    snapshot_at      str   — ISO-8601 UTC timestamp

Consumer: deployment-ui's DeploymentReadinessTab reads these per surface +
shows red/green per surface in the Coverage column.

Usage:
    bash coverage_snapshot.sh | \
        python3 coverage_snapshot_to_parquet.py --project-id central-element-323112

Plan: deployment_and_qg_strategy_implementation_2026_05_13.md Phase 8.E.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime


def _build_parquet_bytes(rows_by_repo: dict[str, list[dict[str, object]]]) -> dict[str, bytes]:
    """Build per-repo parquet bytes. Returns {repo: parquet_bytes}."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema(
        [
            pa.field("repo", pa.string()),
            pa.field("surface", pa.string()),
            pa.field("target_pct", pa.int64()),
            pa.field("actual_pct", pa.float64()),
            pa.field("files_matched", pa.int64()),
            pa.field("lines_covered", pa.int64()),
            pa.field("lines_valid", pa.int64()),
            pa.field("snapshot_at", pa.string()),
        ]
    )

    result: dict[str, bytes] = {}
    for repo, rows in rows_by_repo.items():
        if not rows:
            continue
        table = pa.table(
            {
                "repo": [str(r.get("repo") or repo) for r in rows],
                "surface": [str(r.get("surface") or "") for r in rows],
                "target_pct": [int(r.get("target_pct") or 0) for r in rows],
                "actual_pct": [float(r.get("actual_pct") or 0.0) for r in rows],
                "files_matched": [int(r.get("files_matched") or 0) for r in rows],
                "lines_covered": [int(r.get("lines_covered") or 0) for r in rows],
                "lines_valid": [int(r.get("lines_valid") or 0) for r in rows],
                "snapshot_at": [str(r.get("snapshot_at") or "") for r in rows],
            },
            schema=schema,
        )
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        result[repo] = buf.getvalue()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Write per-repo coverage snapshot parquets to GCS")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--date", default=None, help="Snapshot date YYYY_MM_DD (default: today UTC)")
    parser.add_argument("--dry-run", action="store_true", help="Build parquets but skip GCS upload")
    args = parser.parse_args()

    project_id: str = args.project_id
    date_str: str = args.date or datetime.now(UTC).strftime("%Y_%m_%d")

    rows_by_repo: dict[str, list[dict[str, object]]] = defaultdict(list)
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("Coverage snapshot") or line.startswith("WARN"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"WARN: skipping unparseable line: {exc}", file=sys.stderr)
            continue
        repo = str(row.get("repo") or "unknown")
        rows_by_repo[repo].append(row)

    if not rows_by_repo:
        print("WARN: no coverage rows received from stdin — nothing to write", file=sys.stderr)
        return

    parquet_map = _build_parquet_bytes(rows_by_repo)

    if args.dry_run:
        for repo, parquet_bytes in parquet_map.items():
            print(f"DRY  {repo}: {len(parquet_bytes)} bytes (would write to GCS)")
        print(f"\nDone (dry-run): {len(parquet_map)} repos", file=sys.stderr)
        return

    from unified_trading_library import upload_to_storage

    bucket_name = f"{project_id}-deployment-events"
    uploaded = 0
    failed = 0
    for repo, parquet_bytes in parquet_map.items():
        blob_path = f"coverage_snapshot/repo={repo}/coverage_snapshot_{date_str}.parquet"
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
