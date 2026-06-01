"""A3 — Manifest divergence report.

Mega-audit Phase A3 deliverable. Reads the canonical
``_index/availability_index.parquet`` from every per-asset-group MTDS bucket
(single-walk discipline — one parquet per bucket, not a per-shard walk),
joins with the A2 dump, and classifies every (asset_group, venue, data_type,
date) cell into:

- ``OK_CAPTURED`` — manifest captured, A2 said SHOULD_HAVE_DATA. ✅
- ``OK_HONEST_EMPTY`` — manifest empty_confirmed, A2 said EXPECTED_EMPTY. ✅
- ``DIVERGENT_EMPTY`` — manifest empty_confirmed, A2 said SHOULD_HAVE_DATA. ❌
  (the Drift S3 silent-absence bug class — adapter returned 0 rows when it
   shouldn't have)
- ``MISSING_EXPECTED`` — no manifest row, A2 said SHOULD_HAVE_DATA. ❌
  (silent gap — adapter never ran or never emitted)
- ``OK_NOT_YET_LIVE`` — no manifest row (or empty_confirmed), A2 said
  NOT_YET_LIVE. ✅
- ``OK_OUT_OF_SCOPE`` — manifest row exists but A2 said NOT_IN_SCOPE; rendered
  as ``out_of_scope`` in the data-status view.
- ``ATTEMPTED_FAILED`` — manifest attempted_failed (any reason). Review per-row.

Outputs:
    plans/audit/results/manifest_divergence_2026_05_20.parquet
    plans/audit/results/manifest_divergence_2026_05_20_summary.md
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

import gcsfs
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
PROJECT_ID = "central-element-323112"
ENV_SHORT = "prd"

# Per-asset-group MTDS bucket → manifest index. Bucket-naming convention from
# deployment-service/configs/cloud-providers.yaml (`market-data` kind).
MANIFEST_BUCKETS: dict[str, str] = {
    "cefi": f"market-data-tick-cefi-{ENV_SHORT}-{PROJECT_ID}",
    "defi": f"market-data-tick-defi-{ENV_SHORT}-{PROJECT_ID}",
    "tradfi": f"market-data-tick-tradfi-{ENV_SHORT}-{PROJECT_ID}",
    "sports": f"market-data-tick-sports-{ENV_SHORT}-{PROJECT_ID}",
    "prediction": f"market-data-tick-pred-{ENV_SHORT}-{PROJECT_ID}",
}

MIN_DATE = date(2020, 1, 1)
MAX_DATE = date(2026, 5, 20)


def load_expected_dump() -> pd.DataFrame:
    """Read the A2 dump as a pandas DataFrame."""
    dump_path = (
        WORKSPACE_ROOT
        / "unified-trading-pm"
        / "plans"
        / "audit"
        / "results"
        / "expected_coverage_dump_2026_05_20.parquet"
    )
    if not dump_path.exists():
        msg = f"A2 dump not found at {dump_path}; run a2_materialize_expected_coverage_dump.py first."
        raise FileNotFoundError(msg)
    df = pd.read_parquet(dump_path)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def load_manifest_for_bucket(asset_group: str, fs: gcsfs.GCSFileSystem) -> pd.DataFrame:
    """Read the canonical availability_index for one MTDS bucket.

    Returns a long DataFrame with one row per (venue, data_type, date) +
    capture_status. Filters to the audit window (2020-01-01 → 2026-05-20).
    """
    bucket = MANIFEST_BUCKETS[asset_group]
    path = f"{bucket}/_index/availability_index.parquet"
    print(f"  reading gs://{path} ...", flush=True)  # noqa: gs-uri — audit script diagnostic print; path is resolved from MANIFEST_BUCKETS SSOT
    with fs.open(path, "rb") as fh:
        # Project only the columns we need to keep memory in check.
        df = pq.read_table(
            fh,
            columns=["date", "venue", "data_type", "capture_status", "error_reason"],
        ).to_pandas()
    # Normalise date string → date object.
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])  # drop rows with malformed dates
    df = df[(df["date"] >= MIN_DATE) & (df["date"] <= MAX_DATE)]
    df["asset_group"] = asset_group
    # Normalise capture_status to lowercase canonical strings.
    df["capture_status"] = df["capture_status"].astype(str).str.lower()
    print(f"    rows: {len(df):,}", flush=True)
    return df


def aggregate_manifest(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate manifest to per (asset_group, venue, data_type, date) summary.

    Reduces from per-symbol-shard rows (which can have many per cell) to per-cell
    flags ``any_captured``, ``any_empty``, ``any_failed`` and dominant reason.
    """
    grouped = df.groupby(["asset_group", "venue", "data_type", "date"], as_index=False)
    summary = grouped.agg(
        any_captured=("capture_status", lambda x: bool((x == "captured").any())),
        any_empty=("capture_status", lambda x: bool((x == "empty_confirmed").any())),
        any_failed=("capture_status", lambda x: bool((x == "attempted_failed").any())),
        row_count=("capture_status", "count"),
    )
    return summary


def classify_row(row: pd.Series) -> str:  # type: ignore[type-arg]
    expected_state = row["expected_state"]
    if pd.isna(expected_state):
        # No A2 expectation row (in_scope but oracle didn't emit) — shouldn't happen given the
        # dump covers every in-scope cell + the manifest contributes the rest.
        return "NO_EXPECTATION"

    any_captured = bool(row.get("any_captured", False))
    any_empty = bool(row.get("any_empty", False))
    any_failed = bool(row.get("any_failed", False))
    has_manifest_row = any_captured or any_empty or any_failed

    if expected_state == "SHOULD_HAVE_DATA":
        if any_captured:
            return "OK_CAPTURED"
        if any_empty and not any_captured:
            return "DIVERGENT_EMPTY"
        if any_failed and not (any_captured or any_empty):
            return "ATTEMPTED_FAILED"
        if not has_manifest_row:
            return "MISSING_EXPECTED"
        return "OK_CAPTURED"  # mixed captured+empty → still captured.

    if expected_state == "EXPECTED_EMPTY":
        if any_captured:
            # Unexpected — data exists when we said it shouldn't (e.g. weekend trading day?).
            return "UNEXPECTED_CAPTURED"
        if any_empty:
            return "OK_HONEST_EMPTY"
        return "OK_HONEST_EMPTY"  # no row = silent empty, treat as honest given oracle expected empty.

    if expected_state == "NOT_YET_LIVE":
        if any_captured:
            return "UNEXPECTED_PRE_LAUNCH_CAPTURED"
        return "OK_NOT_YET_LIVE"

    if expected_state == "NOT_IN_SCOPE":
        return "OK_OUT_OF_SCOPE"

    return f"UNKNOWN:{expected_state}"


def main() -> int:
    print("Loading A2 dump ...", flush=True)
    expected = load_expected_dump()
    print(f"A2 dump rows: {len(expected):,}", flush=True)

    fs = gcsfs.GCSFileSystem(token="google_default")

    print("\nReading manifest indexes from prod GCS ...", flush=True)
    manifest_frames: list[pd.DataFrame] = []
    for ag in MANIFEST_BUCKETS:
        try:
            df_bucket = load_manifest_for_bucket(ag, fs)
            manifest_frames.append(df_bucket)
        except (FileNotFoundError, OSError) as err:
            print(f"  SKIP {ag}: {err}", flush=True)

    manifest_long = pd.concat(manifest_frames, ignore_index=True) if manifest_frames else pd.DataFrame()
    print(f"\nTotal manifest rows ingested: {len(manifest_long):,}", flush=True)

    print("\nAggregating manifest to per-cell summary ...", flush=True)
    manifest_summary = aggregate_manifest(manifest_long)
    print(f"Per-cell manifest summary rows: {len(manifest_summary):,}", flush=True)

    print("\nJoining A2 expected vs manifest actual ...", flush=True)
    expected_renamed = expected.rename(columns={"source": "venue"})[
        ["asset_group", "venue", "data_type", "date", "expected_state", "reason"]
    ]
    joined = expected_renamed.merge(
        manifest_summary,
        on=["asset_group", "venue", "data_type", "date"],
        how="outer",
    )

    # Cells that exist in manifest but not in A2 expected (because the venue
    # is out of EXPECTED_COVERAGE_BY_ASSET_GROUP scope).
    joined["expected_state"] = joined["expected_state"].fillna("NOT_IN_SCOPE")
    joined["reason"] = joined["reason"].where(joined["reason"].notna(), None)
    joined["any_captured"] = joined["any_captured"].fillna(False).astype(bool)
    joined["any_empty"] = joined["any_empty"].fillna(False).astype(bool)
    joined["any_failed"] = joined["any_failed"].fillna(False).astype(bool)
    joined["row_count"] = joined["row_count"].fillna(0).astype(int)

    print("Classifying cells ...", flush=True)
    joined["classification"] = joined.apply(classify_row, axis=1)

    # Counts per classification.
    classification_counts: dict[str, int] = defaultdict(int)
    for k, v in joined["classification"].value_counts().to_dict().items():
        classification_counts[k] = int(v)

    # Per-asset-group breakdown.
    ag_breakdown: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for _, r in joined.iterrows():
        ag_breakdown[r["asset_group"]][r["classification"]] += 1

    # Write parquet.
    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"
    parquet_path = out_dir / "manifest_divergence_2026_05_20.parquet"
    table = pa.Table.from_pandas(joined, preserve_index=False)
    pq.write_table(table, parquet_path, compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1024 / 1024:.2f} MiB)", flush=True)

    # Top divergent rows.
    divergent = joined[joined["classification"].isin(["DIVERGENT_EMPTY", "MISSING_EXPECTED", "ATTEMPTED_FAILED"])]
    top_per_ag: dict[str, pd.DataFrame] = {}
    for ag in joined["asset_group"].dropna().unique():
        sub = divergent[divergent["asset_group"] == ag]
        # Group by (venue, data_type) and count cells.
        venue_counts = sub.groupby(["venue", "data_type", "classification"]).size().reset_index(name="cells")
        venue_counts = venue_counts.sort_values("cells", ascending=False)
        top_per_ag[ag] = venue_counts.head(20)

    summary_path = out_dir / "manifest_divergence_2026_05_20_summary.md"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A3 — Manifest divergence summary\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"Window: {MIN_DATE.isoformat()} → {MAX_DATE.isoformat()}\n\n")
        fh.write(f"Total joined cells: {len(joined):,}\n\n")
        fh.write("Output parquet: `plans/audit/results/manifest_divergence_2026_05_20.parquet` ")
        fh.write(f"({parquet_path.stat().st_size / 1024 / 1024:.2f} MiB)\n\n")

        fh.write("## Classification breakdown (workspace-wide)\n\n")
        fh.write("| Classification | Cells | % | Status |\n|---|---:|---:|---|\n")
        status_map = {
            "OK_CAPTURED": "✅ honest",
            "OK_HONEST_EMPTY": "✅ honest",
            "OK_NOT_YET_LIVE": "✅ honest",
            "OK_OUT_OF_SCOPE": "✅ honest",
            "DIVERGENT_EMPTY": "❌ review-blocking (Drift-bug class)",
            "MISSING_EXPECTED": "❌ review-blocking (silent gap)",
            "ATTEMPTED_FAILED": "⚠️ review per-row",
            "UNEXPECTED_CAPTURED": "⚠️ data on a date the oracle said empty",
            "UNEXPECTED_PRE_LAUNCH_CAPTURED": "⚠️ data before declared launch",
            "NO_EXPECTATION": "⚠️ oracle gap",
        }
        for cls, count in sorted(classification_counts.items(), key=lambda kv: -kv[1]):
            pct = 100.0 * count / len(joined) if len(joined) else 0.0
            fh.write(f"| `{cls}` | {count:,} | {pct:.2f}% | {status_map.get(cls, '?')} |\n")

        fh.write("\n## Per-asset-group breakdown\n\n")
        for ag, classes in ag_breakdown.items():
            fh.write(f"\n### {ag}\n\n")
            fh.write("| Classification | Cells |\n|---|---:|\n")
            for cls, count in sorted(classes.items(), key=lambda kv: -kv[1]):
                fh.write(f"| `{cls}` | {count:,} |\n")

        fh.write("\n## Top divergent (venue, data_type) per asset_group (review-blocking list)\n\n")
        for ag, top in top_per_ag.items():
            fh.write(f"\n### {ag}\n\n")
            if top.empty:
                fh.write("_No divergent cells._\n")
                continue
            fh.write("| Venue | Data type | Classification | Cells |\n|---|---|---|---:|\n")
            for _, r in top.iterrows():
                fh.write(f"| {r['venue']} | {r['data_type']} | `{r['classification']}` | {r['cells']:,} |\n")

        fh.write("\n## Notes\n\n")
        fh.write(
            "- A2 oracle has known gaps (sports off-seasons + DeFi protocol pauses not yet encoded)."
            " Cells classified as `SHOULD_HAVE_DATA` in those domains may actually be honest empties.\n"
        )
        fh.write(
            "- `DIVERGENT_EMPTY` is the highest-priority class — these are likely silent adapter bugs"
            " (the Drift S3 class). Each (venue, data_type) row above should be inspected"
            " for the source of the empty.\n"
        )
        fh.write(
            "- `MISSING_EXPECTED` indicates a silent gap (the adapter never emitted a manifest row at all)."
            " Either the venue's date enumerator skipped these cells,"
            " or the orchestrator scope doesn't enumerate them.\n"
        )
        fh.write(
            "- `ATTEMPTED_FAILED` is per-row noise unless concentrated on specific (venue, data_type) pairs"
            " — check the `error_reason` column in the parquet for the failure taxonomy.\n"
        )
        fh.write(
            "- Buckets read:"
            " `market-data-tick-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112`"
            " (one `_index/availability_index.parquet` each — single-walk discipline).\n"
        )

    print(f"\nWrote {summary_path}", flush=True)
    print(f"\nDIVERGENT_EMPTY:  {classification_counts.get('DIVERGENT_EMPTY', 0):,}")
    print(f"MISSING_EXPECTED: {classification_counts.get('MISSING_EXPECTED', 0):,}")
    print(f"OK_CAPTURED:      {classification_counts.get('OK_CAPTURED', 0):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
