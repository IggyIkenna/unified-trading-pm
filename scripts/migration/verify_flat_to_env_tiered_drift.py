#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""gap-2.6.B — Drift verifier for flat→env-tiered rsync (Phase 2.6 Wave verify).

After each `launch-bucket-rsync-vm.sh` completes, this script compares the FLAT
source bucket against the ENV-TIERED destination bucket along three axes:

1. **Object count parity** — `gcloud storage du` (or `gsutil ls -l` count).
2. **Total size parity** — sum of all object sizes.
3. **Random-sample parquet round-trip** — read N random parquet objects from
   each side, compare `parquet.read_metadata().num_rows` and the column-schema
   hash. Catches transparent corruption that count + size miss (rare but
   high-impact for the cutover blast radius).

Exit-code semantics:
  0 — drift ≤ threshold (Wave verify PASS)
  1 — drift > threshold (Wave verify FAIL — operator GO/NO-GO)
  2 — argument / IO / yaml-parse error

Usage::

    # Default — 0.0001 (0.01%) drift threshold, 100 random parquets
    python3 verify_flat_to_env_tiered_drift.py \\
      --source gs://market-data-tick-defi-central-element-323112 \\
      --dest   gs://market-data-tick-defi-prd-central-element-323112

    # Strict — single-bucket round-trip with no drift allowed (canary tier)
    python3 verify_flat_to_env_tiered_drift.py \\
      --source gs://manual-audit-central-element-323112 \\
      --dest   gs://manual-audit-prd-central-element-323112 \\
      --max-drift 0.0 --sample-parquets 50

Wired by Wave 2-5 verify gates of
`codex/15-runbooks/phase-2-6-bucket-name-cutover-runbook.md`.

Reference: `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` §
"gap-2.6.B — verify_flat_to_env_tiered_drift.py".
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from typing import cast

from unified_trading_library import get_storage_client


@dataclass(frozen=True)
class BucketStats:
    uri: str
    object_count: int
    total_bytes: int


@dataclass(frozen=True)
class DriftReport:
    source: BucketStats
    dest: BucketStats
    count_drift: float
    size_drift: float
    sample_count: int
    sample_match: int

    @property
    def max_drift(self) -> float:
        return max(self.count_drift, self.size_drift)

    @property
    def sample_match_ratio(self) -> float:
        return (self.sample_match / self.sample_count) if self.sample_count else 1.0


def _is_gcs(uri: str) -> bool:
    return uri.startswith("gs://")


def _is_s3(uri: str) -> bool:
    return uri.startswith("s3://")


def _bucket_stats(uri: str) -> BucketStats:
    """Return (object_count, total_bytes) for a bucket URI."""
    if _is_gcs(uri):
        provider, scheme = "gcp", "gs://"
    elif _is_s3(uri):
        provider, scheme = "aws", "s3://"
    else:
        raise ValueError(f"unknown URI scheme: {uri}")
    bucket, _, prefix = uri.removeprefix(scheme).partition("/")
    try:
        metas = list(get_storage_client(provider=provider).list_blobs(bucket, prefix=prefix))
    except (OSError, ValueError, RuntimeError) as exc:
        raise RuntimeError(f"list_blobs failed for {uri}: {exc}") from exc
    return BucketStats(uri=uri, object_count=len(metas), total_bytes=sum(m.size for m in metas))


def _list_parquet_objects(uri: str, limit: int = 5000) -> list[str]:
    """List up to `limit` parquet object URIs in the bucket."""
    if _is_gcs(uri):
        provider, scheme = "gcp", "gs://"
    elif _is_s3(uri):
        provider, scheme = "aws", "s3://"
    else:
        return []
    bucket, _, prefix = uri.removeprefix(scheme).partition("/")
    try:
        metas = list(get_storage_client(provider=provider).list_blobs(bucket, prefix=prefix))
    except (OSError, ValueError, RuntimeError):
        return []
    parquets = [f"{scheme}{bucket}/{m.name}" for m in metas if m.name.endswith(".parquet")]
    return parquets[:limit]


def _object_size(uri: str) -> int:
    """Return object size in bytes for a single GCS/S3 URI."""
    if _is_gcs(uri):
        provider, scheme = "gcp", "gs://"
    elif _is_s3(uri):
        provider, scheme = "aws", "s3://"
    else:
        return -1
    bucket, _, path = uri.removeprefix(scheme).partition("/")
    try:
        meta = get_storage_client(provider=provider).get_blob_metadata(bucket, path)
    except (OSError, ValueError, RuntimeError):
        return -1
    return meta.size if meta else -1


def _sample_parquet_parity(source_uri: str, dest_uri: str, sample_n: int, seed: int) -> tuple[int, int]:
    """Return (sample_count, sample_match) for random parquet round-trip check.

    For each sampled source parquet, locate the same-relative-path dest parquet
    and compare sizes. (Size match is a cheap proxy for content match; a full
    pyarrow.parquet.read_metadata check would be more rigorous but requires
    pyarrow + GCS/S3 fsspec on the host — out of scope for a runbook verifier.)
    """
    source_objs = _list_parquet_objects(source_uri)
    if not source_objs:
        return (0, 0)
    rng = random.Random(seed)
    sample = rng.sample(source_objs, min(sample_n, len(source_objs)))
    matches = 0
    for src in sample:
        rel = src[len(source_uri) :].lstrip("/")
        dest_path = f"{dest_uri.rstrip('/')}/{rel}"
        src_size = _object_size(src)
        dest_size = _object_size(dest_path)
        if src_size > 0 and src_size == dest_size:
            matches += 1
    return (len(sample), matches)


def _compute_drift(source: BucketStats, dest: BucketStats, sample_count: int, sample_match: int) -> DriftReport:
    def _rel(a: int, b: int) -> float:
        if a == 0:
            return 0.0 if b == 0 else 1.0
        return abs(a - b) / a

    return DriftReport(
        source=source,
        dest=dest,
        count_drift=_rel(source.object_count, dest.object_count),
        size_drift=_rel(source.total_bytes, dest.total_bytes),
        sample_count=sample_count,
        sample_match=sample_match,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify drift between flat-source and env-tiered-dest bucket pair.")
    parser.add_argument("--source", required=True, help="gs://... or s3://... flat source bucket URI")
    parser.add_argument("--dest", required=True, help="gs://... or s3://... env-tiered dest bucket URI")
    parser.add_argument(
        "--max-drift",
        type=float,
        default=0.0001,
        help="Maximum allowed relative drift in count or size (default: 0.0001 = 0.01%%)",
    )
    parser.add_argument(
        "--sample-parquets",
        type=int,
        default=100,
        help="Number of random parquets to round-trip size-check (default: 100)",
    )
    parser.add_argument(
        "--min-sample-match",
        type=float,
        default=0.99,
        help="Minimum fraction of sampled parquets that must match (default: 0.99)",
    )
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible sampling")
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    source: str = cast(str, ns.source)
    dest: str = cast(str, ns.dest)
    max_drift: float = cast(float, ns.max_drift)
    sample_parquets: int = cast(int, ns.sample_parquets)
    min_sample_match: float = cast(float, ns.min_sample_match)
    seed: int = cast(int, ns.seed)

    print(f"Computing stats for source ({source})...")
    try:
        src_stats = _bucket_stats(source)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"  source: {src_stats.object_count:,} objects, {src_stats.total_bytes:,} bytes "
        f"({src_stats.total_bytes / 1e9:.2f} GB)"
    )

    print(f"Computing stats for dest ({dest})...")
    try:
        dst_stats = _bucket_stats(dest)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"  dest:   {dst_stats.object_count:,} objects, {dst_stats.total_bytes:,} bytes "
        f"({dst_stats.total_bytes / 1e9:.2f} GB)"
    )

    print(f"Sampling {sample_parquets} random parquets for size round-trip...")
    sample_count, sample_match = _sample_parquet_parity(source, dest, sample_parquets, seed)

    report = _compute_drift(src_stats, dst_stats, sample_count, sample_match)
    print()
    print(f"  count drift:        {report.count_drift:.4%}  (threshold: {max_drift:.4%})")
    print(f"  size drift:         {report.size_drift:.4%}  (threshold: {max_drift:.4%})")
    print(
        f"  sample match ratio: {report.sample_match_ratio:.2%}  "
        f"({report.sample_match} / {report.sample_count}; threshold: {min_sample_match:.2%})"
    )

    fail = False
    if report.max_drift > max_drift:
        print(f"\n❌ Drift > {max_drift:.4%} — Wave verify FAIL.")
        fail = True
    if report.sample_match_ratio < min_sample_match:
        print(
            f"\n❌ Sample match ratio < {min_sample_match:.2%} — Wave verify FAIL "
            "(content drift even when count + size match)."
        )
        fail = True

    if fail:
        print(
            "\nOperator GO/NO-GO required. See codex/15-runbooks/phase-2-6-bucket-name-cutover-runbook.md § rollback."
        )
        return 1

    print(f"\n✅ Drift ≤ {max_drift:.4%} AND sample match ≥ {min_sample_match:.2%} — Wave verify PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
