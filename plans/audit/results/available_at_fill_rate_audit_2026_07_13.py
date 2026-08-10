"""available_at fill-rate audit for capture_status=captured manifest rows, per asset_group.

Blast-radius audit for
`plans/active/issues/manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`
todo 1 — that issue found `ManifestWriter.record_captured()` /
`record_captured_from_counts()` validated `available_at` but never persisted it onto the
`AvailabilityRecord` (fixed at unified-trading-library@9c9cdc50); the CF-8 sports audit
(2026-06-01) had only ever measured sports, so it was unknown whether other asset_groups
were similarly degraded. This script reads the CONSOLIDATED manifest index per bucket via
UTL `read_availability_index()` (no whole-corpus GCS walk — single-walk discipline) and
reports the fraction of `capture_status=captured` rows with a non-empty `available_at`
string, broken down by asset_group / bucket kind / service_name.

`available_at: str = ""` is the writer's own legacy default (never `None`/`NaN` — the
reader backfills missing columns to `""` too, per
`unified_trading_library/manifest_writer/_read_index.py`), so "filled" here means
`available_at != ""`, not `.notna()`.

Run (from unified-trading-library, so the UTL package + its .venv are on path):
  cd unified-trading-library && GCP_PROJECT_ID=central-element-323112 \
    .venv/bin/python ../unified-trading-pm/plans/audit/results/available_at_fill_rate_audit_2026_07_13.py

Results + verdict: see the issue doc's "## Audit Results (2026-07-13)" section.
"""

from __future__ import annotations

import sys

import pandas as pd
from unified_trading_library import BucketNamingError, read_availability_index, resolve_bucket_name

# (kind, asset_group-or-None) pairs to check. asset_group=None -> single bucket (no AG split).
TARGETS: list[tuple[str, str | None]] = (
    [("market-data", ag) for ag in ["cefi", "defi", "tradfi", "sports"]]
    + [("market-data-tick-prediction", None)]
    + [("instruments-store", ag) for ag in ["cefi", "defi", "tradfi", "sports"]]
    + [("instruments-store-prediction", None)]
    + [("strategy-store", None)]
)


def audit_bucket(kind: str, asset_group: str | None) -> dict | None:
    try:
        bucket = resolve_bucket_name(cloud="gcp", kind=kind, asset_group=asset_group)
    except BucketNamingError as exc:
        print(f"SKIP {kind}/{asset_group}: bucket resolve failed: {exc}", file=sys.stderr)
        return None

    try:
        df = read_availability_index(bucket, columns=["capture_status", "available_at", "service_name"])
    except Exception as exc:  # noqa: broad-except — read_availability_index's own contract explicitly
        # re-raises arbitrary unclassified exceptions (auth/permission errors, pyarrow errors) beyond
        # the (FileNotFoundError, OSError, ValueError, ParserError, NotFound/Forbidden-by-name) it
        # already swallows internally; this is a per-bucket audit-sweep isolation catch — one bad
        # bucket must SKIP, not crash the whole multi-target audit.
        print(f"SKIP {kind}/{asset_group} bucket={bucket}: read failed: {exc}", file=sys.stderr)
        return None

    if df.empty:
        print(f"EMPTY {kind}/{asset_group} bucket={bucket}: 0 rows")
        return None

    captured = df[df["capture_status"] == "captured"]
    n_captured = len(captured)
    if n_captured == 0:
        print(f"{kind}/{asset_group} bucket={bucket}: 0 captured rows (total={len(df)})")
        return None

    filled = int((captured["available_at"].astype(str) != "").sum())
    fill_rate = filled / n_captured

    by_service = (
        captured.assign(_filled=captured["available_at"].astype(str) != "")
        .groupby("service_name")
        .agg(n_captured=("_filled", "size"), n_filled=("_filled", "sum"))
    )
    by_service["fill_rate"] = by_service["n_filled"] / by_service["n_captured"]

    result = {
        "kind": kind,
        "asset_group": asset_group or "-",
        "bucket": bucket,
        "n_captured": n_captured,
        "n_filled": filled,
        "fill_rate": fill_rate,
        "by_service": by_service,
    }
    print(
        f"{kind}/{asset_group or '-'} bucket={bucket}: captured={n_captured:,} "
        f"filled={filled:,} fill_rate={fill_rate:.1%}"
    )
    print(by_service.to_string())
    print()
    return result


def main() -> None:
    results = []
    for kind, ag in TARGETS:
        r = audit_bucket(kind, ag)
        if r is not None:
            results.append(r)

    print("\n=== SUMMARY ===")
    summary_rows = [
        {
            "kind": r["kind"],
            "asset_group": r["asset_group"],
            "bucket": r["bucket"],
            "n_captured": r["n_captured"],
            "n_filled": r["n_filled"],
            "fill_rate_pct": round(r["fill_rate"] * 100, 1),
        }
        for r in results
    ]
    summary_df = pd.DataFrame(summary_rows)
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
