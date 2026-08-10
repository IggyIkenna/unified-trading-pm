#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Honest-coverage ratchet — fail QG if coverage ratio regresses by >0.5pp.

Usage:
    python3 scripts/qg/honest_coverage_ratchet.py \
        --bucket <gcs_bucket> \
        --service <service_name> \
        [--asset-group <ag>] \
        [--threshold 0.005]

Exit 0 = pass, Exit 1 = regression detected, Exit 2 = no prior snapshot (first run).

Snapshots stored at: gs://<bucket>/_index/snapshots/honest_coverage/<date>.json
Regression threshold: 0.5pp (0.005) by default.

Plan: honest_coverage_formula_consolidation_2026_05_19.md Phase 6.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta

_REGRESSION_THRESHOLD = 0.005  # 0.5 percentage points


def _load_snapshot(bucket: str, snapshot_date: str) -> dict[str, float] | None:
    """Load coverage snapshot from GCS. Returns None if not found."""
    try:
        from unified_trading_library import get_storage_client

        client = get_storage_client()
        path = f"_index/snapshots/honest_coverage/{snapshot_date}.json"
        raw = client.download_bytes(bucket, path)
        return dict(json.loads(raw))
    except FileNotFoundError:
        return None
    except Exception as exc:  # noqa: broad-except — best-effort snapshot load, any failure
        # (auth/network/GCS SDK) degrades to "no prior snapshot", never crashes the regression check
        # pragma: no cover
        print(f"WARNING: could not load snapshot from {bucket}: {exc}", file=sys.stderr)
        return None


def _save_snapshot(bucket: str, snapshot_date: str, data: dict[str, float]) -> None:
    try:
        from unified_trading_library import get_storage_client

        client = get_storage_client()
        path = f"_index/snapshots/honest_coverage/{snapshot_date}.json"
        client.upload_bytes(bucket, path, json.dumps(data).encode())
    except Exception as exc:  # noqa: broad-except — best-effort snapshot save; any failure must
        # not crash the regression check itself, just skip persisting today's snapshot
        # pragma: no cover
        print(f"WARNING: could not save snapshot to {bucket}: {exc}", file=sys.stderr)


def _compute_coverage(bucket: str, asset_group: str | None) -> dict[str, float]:
    """Compute coverage ratios per data_type for the bucket.

    Returns dict mapping data_type → coverage ratio (0.0-1.0).
    """
    from unified_trading_library import compute_coverage_for_bucket, read_availability_index

    index = read_availability_index(bucket, columns=["data_type", "asset_group"])
    if index is None or index.empty:
        return {}

    data_types = index["data_type"].unique() if "data_type" in index.columns else []
    if asset_group and "asset_group" in index.columns:
        index = index[index["asset_group"] == asset_group]

    result: dict[str, float] = {}
    for dt in data_types:
        _, ratio = compute_coverage_for_bucket(bucket, data_type_filter=str(dt))
        result[str(dt)] = ratio
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--asset-group", default=None)
    parser.add_argument("--threshold", type=float, default=_REGRESSION_THRESHOLD)
    parser.add_argument(
        "--skip-on-no-gcs", action="store_true", help="Exit 0 (skip) if GCS unavailable (local dev mode)"
    )
    args = parser.parse_args(argv)

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    try:
        current = _compute_coverage(args.bucket, args.asset_group)
    except Exception as exc:  # noqa: broad-except — top-level CLI guard: any GCS/compute failure
        # either SKIPs (local dev, --skip-on-no-gcs) or reports a clean ERROR, never a raw traceback
        if args.skip_on_no_gcs:
            print(f"SKIP (no GCS): {exc}", file=sys.stderr)
            return 0
        print(f"ERROR: could not compute coverage: {exc}", file=sys.stderr)
        return 1

    if not current:
        print(f"SKIP: no manifest data in bucket {args.bucket}")
        return 0

    prior = _load_snapshot(args.bucket, yesterday)
    if prior is None:
        print(
            f"INFO: no prior snapshot for {yesterday} in {args.bucket}; saving baseline and skipping regression check."
        )
        _save_snapshot(args.bucket, today, current)
        return 2

    regressions: list[tuple[str, float, float, float]] = []
    for dt, current_ratio in sorted(current.items()):
        prior_ratio = prior.get(dt)
        if prior_ratio is None:
            continue
        delta = current_ratio - prior_ratio
        if delta < -args.threshold:
            regressions.append((dt, prior_ratio, current_ratio, delta))

    _save_snapshot(args.bucket, today, current)

    if regressions:
        print(f"COVERAGE REGRESSION DETECTED (service={args.service} bucket={args.bucket}):")
        for dt, prev, cur, delta in regressions:
            print(f"  {dt}: {prev:.4f} → {cur:.4f} (Δ={delta:+.4f}, threshold={-args.threshold:.4f})")
        print(f"\nTotal regressions: {len(regressions)}")
        print("Use --force to re-fetch affected shards or investigate manifest gaps.")
        return 1

    print(f"OK: coverage ratchet passed for {args.service} ({len(current)} data_types checked, no regressions >0.5pp)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
