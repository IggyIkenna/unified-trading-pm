#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Snapshot per-bucket GCS storage stats from Cloud Monitoring (instant, no object walk).

Reads the ``storage.googleapis.com/storage/v2/total_bytes`` and ``.../total_count``
metrics (sampled once per day by GCS) instead of walking every object with
``gcloud storage du`` — the latter takes hours on million-object buckets while this
returns in seconds. Each metric is split by the ``type`` label
(live / noncurrent / soft-deleted / multipart), letting us surface soft-delete and
versioning bloat per bucket.

The output CSV mirrors the columns first used in ``gcs_buckets_stats_20260520.csv``:
one row per bucket, sorted by total bytes descending, empty buckets (no metric data)
listed last with blank location/storage-class/as_of.

Usage:
    # Snapshot the default project to a dated file in the CWD:
    python3 scripts/finops/gcs-bucket-stats.py

    # Explicit output path + project:
    python3 scripts/finops/gcs-bucket-stats.py --out /tmp/stats.csv --project central-element-323112

Auth: uses the active gcloud credentials (``gcloud auth print-access-token``). Needs
``roles/monitoring.viewer`` + ``roles/storage.buckets.list`` on the project.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TypedDict, cast

DEFAULT_PROJECT = "central-element-323112"

# GCS storage/v2 metric ``type`` label -> our CSV column stem.
TYPE_MAP: dict[str, str] = {
    "live-object": "live",
    "noncurrent-object": "noncurrent",
    "soft-deleted-object": "soft_deleted",
    "multipart-object": "multipart",
}
TYPES: tuple[str, ...] = ("live", "noncurrent", "soft_deleted", "multipart")


class _LabelValue(TypedDict, total=False):
    stringValue: str


class _PointValue(TypedDict, total=False):
    doubleValue: float
    int64Value: str


class _TimeInterval(TypedDict):
    endTime: str


class _PointData(TypedDict):
    values: list[_PointValue]
    timeInterval: _TimeInterval


class _Series(TypedDict):
    labelValues: list[_LabelValue]
    pointData: list[_PointData]


class _QueryResponse(TypedDict, total=False):
    timeSeriesData: list[_Series]
    nextPageToken: str


@dataclass
class BucketRow:
    bucket: str
    location: str
    storage_classes: str
    as_of: str
    total_objects: int
    total_bytes: int
    total_GiB: float  # noqa: N815 - CSV column name kept identical to the 2026-05-20 baseline
    live_objects: int
    live_bytes: int
    noncurrent_objects: int
    noncurrent_bytes: int
    soft_deleted_objects: int
    soft_deleted_bytes: int
    multipart_objects: int
    multipart_bytes: int
    nonlive_bytes: int
    bloat_pct: float


def _sh(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def _mql(project: str, token: str, query: str) -> list[_Series]:
    """Run a Monitoring Query Language query via curl, following pagination."""
    url = f"https://monitoring.googleapis.com/v3/projects/{project}/timeSeries:query"
    out: list[_Series] = []
    page_token: str | None = None
    while True:
        body: dict[str, str] = {"query": query}
        if page_token:
            body["pageToken"] = page_token
        raw = subprocess.run(
            [
                "curl",
                "-sS",
                "-X",
                "POST",
                url,
                "-H",
                f"Authorization: Bearer {token}",
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                "@-",
            ],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        payload = cast(_QueryResponse, json.loads(raw))
        out.extend(payload.get("timeSeriesData", []))
        token_value = payload.get("nextPageToken")
        page_token = token_value if token_value else None
        if not page_token:
            break
    return out


def _latest_point(series: _Series) -> tuple[float, str]:
    """Most recent (value, endTime) across a series' daily points."""
    best_value, best_time = 0.0, ""
    for point in series["pointData"]:
        end_time = point["timeInterval"]["endTime"]
        raw = point["values"][0]
        value = raw.get("doubleValue")
        if value is None:
            value = float(raw.get("int64Value", "0"))
        if best_time == "" or end_time > best_time:
            best_time, best_value = end_time, value
    return best_value, best_time


def _collect(
    project: str,
    token: str,
    metric: str,
) -> tuple[dict[tuple[str, str], float], dict[str, str], dict[str, set[str]], str]:
    """Return per-(bucket, type) latest value, bucket->location, bucket->storage-classes, max as_of."""
    query = (
        f"fetch gcs_bucket | metric '{metric}' | within 3d | "
        "group_by [resource.bucket_name, resource.location, metric.storage_class, metric.type], "
        "[v: max(value)] | every 1d | within 3d"
    )
    values: dict[tuple[str, str], float] = defaultdict(float)
    locations: dict[str, str] = {}
    storage_classes: dict[str, set[str]] = defaultdict(set)
    as_of = ""
    for series in _mql(project, token, query):
        labels = [v.get("stringValue", "") for v in series["labelValues"]]
        bucket, location, storage_class, raw_type = labels[0], labels[1], labels[2], labels[3]
        value, end_time = _latest_point(series)
        type_col = TYPE_MAP.get(raw_type, raw_type)
        values[(bucket, type_col)] += value
        locations[bucket] = location
        if value > 0:
            storage_classes[bucket].add(storage_class)
        if end_time > as_of:
            as_of = end_time
    return values, locations, storage_classes, as_of


def build_rows(project: str, token: str) -> tuple[list[BucketRow], str]:
    buckets = [
        b
        for b in _sh(
            ["gcloud", "storage", "buckets", "list", f"--project={project}", "--format=value(name)"],
        ).splitlines()
        if b
    ]

    byte_values, byte_loc, byte_sc, byte_as_of = _collect(
        project, token, "storage.googleapis.com/storage/v2/total_bytes"
    )
    count_values, count_loc, count_sc, count_as_of = _collect(
        project, token, "storage.googleapis.com/storage/v2/total_count"
    )
    as_of = max(byte_as_of, count_as_of)

    locations = {**count_loc, **byte_loc}
    storage_classes: dict[str, set[str]] = defaultdict(set)
    for source in (byte_sc, count_sc):
        for bucket, classes in source.items():
            storage_classes[bucket] |= classes

    rows: list[BucketRow] = []
    for bucket in buckets:
        objs = {t: int(count_values.get((bucket, t), 0)) for t in TYPES}
        size = {t: int(byte_values.get((bucket, t), 0)) for t in TYPES}
        total_objects = sum(objs.values())
        total_bytes = sum(size.values())
        nonlive_bytes = size["noncurrent"] + size["soft_deleted"] + size["multipart"]
        has_data = total_bytes > 0 or total_objects > 0
        rows.append(
            BucketRow(
                bucket=bucket,
                location=locations.get(bucket, "") if has_data else "",
                storage_classes="|".join(sorted(storage_classes.get(bucket, set()))),
                as_of=as_of if has_data else "",
                total_objects=total_objects,
                total_bytes=total_bytes,
                total_GiB=round(total_bytes / (1024**3), 3),
                live_objects=objs["live"],
                live_bytes=size["live"],
                noncurrent_objects=objs["noncurrent"],
                noncurrent_bytes=size["noncurrent"],
                soft_deleted_objects=objs["soft_deleted"],
                soft_deleted_bytes=size["soft_deleted"],
                multipart_objects=objs["multipart"],
                multipart_bytes=size["multipart"],
                nonlive_bytes=nonlive_bytes,
                bloat_pct=round(nonlive_bytes / total_bytes * 100, 1) if total_bytes else 0.0,
            )
        )

    rows.sort(key=lambda r: (-r.total_bytes, r.bucket))
    return rows, as_of


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP project id")
    parser.add_argument("--out", default=None, help="Output CSV path (default: ./gcs_buckets_stats_<YYYYMMDD>.csv)")
    args = parser.parse_args()
    project = cast(str, args.project)
    out_arg = cast("str | None", args.out)

    token = _sh(["gcloud", "auth", "print-access-token"]).strip()
    rows, as_of = build_rows(project, token)

    stamp = datetime.now(UTC).strftime("%Y%m%d")
    out_path = out_arg or f"gcs_buckets_stats_{stamp}.csv"
    columns = list(BucketRow.__dataclass_fields__.keys())
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    nonzero = sum(1 for r in rows if r.total_bytes > 0)
    total_tib = sum(r.total_bytes for r in rows) / (1024**4)
    print(f"wrote {len(rows)} buckets ({nonzero} non-empty, {total_tib:.2f} TiB) to {out_path}; as_of={as_of}")


if __name__ == "__main__":
    main()
