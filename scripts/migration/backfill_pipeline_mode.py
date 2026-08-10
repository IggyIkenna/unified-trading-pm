#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""One-shot backfill: fill pipeline_mode column on existing manifest rows.

~38M manifest rows written before Phase 4.MTDS (2026-05) lack pipeline_mode.
This script reads each availability_index.parquet, derives pipeline_mode from
(venue, asset_group, data_type) using the UTL SSOT helper, and writes the
updated parquet back.

Idempotent: rows that already have a valid pipeline_mode value are skipped
unless --force is given.

Usage::

    # Dry-run (default) — shows what would change, writes nothing:
    python backfill_pipeline_mode.py --bucket instruments-store-cefi-<PROJECT_ID> --asset-group cefi

    # Apply to a single bucket:
    python backfill_pipeline_mode.py --apply --bucket instruments-store-cefi-<PROJECT_ID> --asset-group cefi

    # Apply to all asset-group buckets (requires --project-id):
    python backfill_pipeline_mode.py --apply --all --project-id <PROJECT_ID>

    # Verify only (count NULL rows, no changes):
    python backfill_pipeline_mode.py --verify --bucket instruments-store-cefi-<PROJECT_ID> --asset-group cefi

    # Force-overwrite rows that have a pipeline_mode value (operator-blessed):
    python backfill_pipeline_mode.py --apply --force --bucket my-bucket --asset-group cefi

    # Also backfill per-VM shards under _index/per_vm/:
    python backfill_pipeline_mode.py --apply --per-vm --bucket my-bucket --asset-group cefi

Plan: pipeline_mode_implementation_2026_05_28.md Phase 3.1.
SSOT: derive_pipeline_mode_for_row() in unified_trading_library.pipeline_mode_resolver.
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger("backfill_pipeline_mode")

# ── Workspace-resolved imports ─────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # unified-trading-pm/
WORKSPACE_ROOT = REPO_ROOT.parent
UAC_PATH = WORKSPACE_ROOT / "unified-api-contracts"
UTL_PATH = WORKSPACE_ROOT / "unified-trading-library"
for _p in (UAC_PATH, UTL_PATH):
    _p_str = str(_p)
    if _p.exists() and _p_str not in sys.path:
        sys.path.insert(0, _p_str)

# ruff: noqa: I001
import pandas as pd
from unified_api_contracts import PipelineMode  # type: ignore[import-not-found]
from unified_trading_library import get_storage_client  # type: ignore[import-not-found]
from unified_trading_library import derive_pipeline_mode_for_row  # type: ignore[import-not-found]

# ── Constants ──────────────────────────────────────────────────────────────
_INDEX_BLOB = "_index/availability_index.parquet"
_PER_VM_PREFIX = "_index/per_vm/"

_BUCKET_TEMPLATES: list[tuple[str, str]] = [
    # (bucket_prefix, asset_group) — suffix with -{project_id} at runtime.
    # Production env-tiered buckets (with -prd- infix).
    ("market-data-tick-cefi-prd", "cefi"),
    ("market-data-tick-defi-prd", "defi"),
    ("market-data-tick-tradfi-prd", "tradfi"),
    ("market-data-tick-sports-prd", "sports"),
    ("market-data-tick-pred-prd", "prediction"),
    ("instruments-store-cefi-prd", "cefi"),
    ("instruments-store-defi-prd", "defi"),
    ("instruments-store-tradfi-prd", "tradfi"),
    ("instruments-store-sports-prd", "sports"),
    ("instruments-store-pred-prd", "prediction"),
    # Legacy (no env suffix) — also need backfill for any residual nulls.
    ("market-data-tick-cefi", "cefi"),
    ("market-data-tick-defi", "defi"),
    ("market-data-tick-tradfi", "tradfi"),
    ("market-data-tick-sports", "sports"),
    ("market-data-tick-prediction", "prediction"),
    ("instruments-store-cefi", "cefi"),
    ("instruments-store-defi", "defi"),
    ("instruments-store-tradfi", "tradfi"),
    ("instruments-store-sports", "sports"),
    ("instruments-store-prediction", "prediction"),
    # features — NO_INDEX as of 2026-05-28; will skip gracefully.
    ("features-delta-one-cefi-prd", "cefi"),
    ("features-delta-one-defi-prd", "defi"),
    ("features-delta-one-tradfi-prd", "tradfi"),
    ("features-delta-one-sports-prd", "sports"),
    ("features-delta-one-prediction", "prediction"),
]


def _build_bucket_map(project_id: str) -> list[tuple[str, str]]:
    return [(f"{prefix}-{project_id}", ag) for prefix, ag in _BUCKET_TEMPLATES]


def _is_pipeline_mode_null(val: object) -> bool:
    """Return True if the pipeline_mode value is NULL/empty and needs backfill."""
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s == "nan" or s == "None"


def _is_valid_pipeline_mode(val: object) -> bool:
    """Return True if val is a valid PipelineMode enum member string."""
    try:
        PipelineMode(str(val))
        return True
    except ValueError:
        return False


def _backfill_df_vectorized(
    df: pd.DataFrame,
    asset_group: str,
    *,
    force: bool = False,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Derive and fill pipeline_mode using vectorized group-by derivation.

    Returns (updated_df, counts) where counts has: skipped, filled, failed,
    not_derivable. total is len(df).

    Vectorization: calls derive_pipeline_mode_for_row once per unique
    (venue, data_type) combo instead of once per row — critical for manifests
    with tens of millions of rows.
    """
    counts: dict[str, int] = {"skipped": 0, "filled": 0, "failed": 0, "not_derivable": 0}

    if "pipeline_mode" not in df.columns:
        df = df.copy()
        df["pipeline_mode"] = None

    # Identify rows needing backfill.
    null_mask = df["pipeline_mode"].apply(_is_pipeline_mode_null)
    fill_mask = pd.Series([True] * len(df), index=df.index) if force else null_mask
    counts["skipped"] = int((~fill_mask).sum())

    rows_to_fill = df[fill_mask]
    if rows_to_fill.empty:
        return df, counts

    # Build lookup key per unique (venue, data_type) combo.
    venue_col = (
        rows_to_fill["venue"].fillna("").astype(str)
        if "venue" in rows_to_fill.columns
        else pd.Series([""] * len(rows_to_fill), index=rows_to_fill.index)
    )
    data_type_col = (
        rows_to_fill["data_type"].fillna("").astype(str)
        if "data_type" in rows_to_fill.columns
        else pd.Series([""] * len(rows_to_fill), index=rows_to_fill.index)
    )
    _SEP = "|||SPLIT|||"  # noqa: N806
    key_series = venue_col + _SEP + data_type_col

    unique_keys = key_series.unique()
    logger.info(
        "Deriving pipeline_mode for %d unique (venue, data_type) combos (out of %d rows)",
        len(unique_keys),
        len(rows_to_fill),
    )

    key_to_pm: dict[str, str | None] = {}
    for k in unique_keys:
        venue, data_type = str(k).split(_SEP, 1)
        try:
            derived = derive_pipeline_mode_for_row(venue, asset_group, data_type)
            key_to_pm[k] = derived.value if derived is not None else None
        except Exception as exc:  # noqa: broad-except — shard-level (per-key) isolation: one
            # unexpected (venue, data_type) combo must not abort the whole vectorized backfill
            logger.warning("Derivation error for venue=%r data_type=%r: %s", venue, data_type, exc)
            key_to_pm[k] = None

    # Map derived values back to rows.
    derived_values = key_series.map(key_to_pm)

    # Count outcomes before assignment.
    filled_mask = fill_mask & derived_values.notna()
    not_derivable_mask = fill_mask & derived_values.isna()
    counts["filled"] = int(filled_mask.sum())
    counts["not_derivable"] = int(not_derivable_mask.sum())
    # failed: keys that errored → mapped to None → counted in not_derivable above

    if counts["filled"] > 0:
        df = df.copy()
        df.loc[filled_mask, "pipeline_mode"] = derived_values[filled_mask]

    if counts["not_derivable"] > 0:
        logger.debug("%d rows cannot derive pipeline_mode — leaving NULL", counts["not_derivable"])

    return df, counts


def _list_per_vm_blobs(storage: object, bucket: str) -> list[str]:
    """Return blob paths for all per-VM shard parquets under _index/per_vm/."""
    try:
        blobs = storage.list_blobs(bucket, prefix=_PER_VM_PREFIX)  # type: ignore[attr-defined]
        return [b.name for b in blobs if b.name.endswith(".parquet")]
    except Exception as exc:  # noqa: broad-except — bucket-level isolation: one bucket's list
        # failure must not abort processing of other buckets in the same --all run
        logger.warning("Could not list per-VM shards in %s: %s", bucket, exc)
        return []


def backfill_blob(
    storage: object,
    bucket: str,
    blob_path: str,
    asset_group: str,
    *,
    dry_run: bool = True,
    force: bool = False,
    verify_only: bool = False,
) -> dict[str, int]:
    """Backfill pipeline_mode on a single parquet blob.

    Returns a dict with counts: total, skipped, filled, failed, not_derivable.
    """
    if not storage.blob_exists(bucket, blob_path):  # type: ignore[attr-defined]
        logger.warning("Blob not found: %s/%s — skipping", bucket, blob_path)
        return {"total": 0, "skipped": 0, "filled": 0, "failed": 0, "not_derivable": 0}

    raw = storage.download_bytes(bucket, blob_path)  # type: ignore[attr-defined]
    df = pd.read_parquet(io.BytesIO(raw))

    if "pipeline_mode" not in df.columns:
        df["pipeline_mode"] = None

    total = len(df)
    counts = {"total": total, "skipped": 0, "filled": 0, "failed": 0, "not_derivable": 0}

    if verify_only:
        null_count = df["pipeline_mode"].apply(_is_pipeline_mode_null).sum()
        counts["not_derivable"] = int(null_count)
        logger.info("VERIFY %s/%s: %d/%d rows have NULL pipeline_mode", bucket, blob_path, null_count, total)
        return counts

    df, fill_counts = _backfill_df_vectorized(df, asset_group, force=force)
    counts.update(fill_counts)

    logger.info(
        "Blob %s/%s: total=%d skipped=%d filled=%d failed=%d not_derivable=%d",
        bucket,
        blob_path,
        total,
        counts["skipped"],
        counts["filled"],
        counts["failed"],
        counts["not_derivable"],
    )

    if counts["filled"] == 0:
        logger.info("No rows modified — skipping write for %s/%s", bucket, blob_path)
        return counts

    if dry_run:
        logger.info("DRY RUN — not writing %d modified rows to %s/%s", counts["filled"], bucket, blob_path)
        return counts

    # Write back.
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f"backfill_pm_{bucket.replace('-', '_')}_",
        suffix=".parquet",
        delete=False,
    ) as tf:
        tmp_path = Path(tf.name)
    try:
        df.to_parquet(tmp_path, index=False)
        storage.upload_file(bucket, blob_path, str(tmp_path))  # type: ignore[attr-defined]
        logger.info("Wrote %d rows to %s/%s", len(df), bucket, blob_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return counts


def backfill_bucket(
    bucket: str,
    asset_group: str,
    *,
    dry_run: bool = True,
    force: bool = False,
    verify_only: bool = False,
    per_vm: bool = False,
) -> dict[str, int]:
    """Backfill pipeline_mode on all manifest parquets in a bucket.

    Processes the main availability_index.parquet and, if per_vm=True,
    all shards under _index/per_vm/.

    Returns a dict with counts: total, skipped, filled, failed, not_derivable.
    """
    logger.info("Processing bucket=%s asset_group=%s per_vm=%s", bucket, asset_group, per_vm)
    storage = get_storage_client()

    blobs_to_process = [_INDEX_BLOB]
    if per_vm:
        pv_blobs = _list_per_vm_blobs(storage, bucket)
        logger.info("Found %d per-VM shard(s) in %s", len(pv_blobs), bucket)
        blobs_to_process.extend(pv_blobs)

    grand: dict[str, int] = {"total": 0, "skipped": 0, "filled": 0, "failed": 0, "not_derivable": 0}
    for blob_path in blobs_to_process:
        result = backfill_blob(
            storage,
            bucket,
            blob_path,
            asset_group,
            dry_run=dry_run,
            force=force,
            verify_only=verify_only,
        )
        for k in grand:
            grand[k] += result.get(k, 0)

    return grand


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Backfill pipeline_mode column in availability manifests.")
    parser.add_argument("--bucket", help="Target GCS bucket name (without gs:// prefix)")
    parser.add_argument("--asset-group", help="Asset group for the bucket (cefi/defi/tradfi/sports/prediction)")
    parser.add_argument("--all", dest="all_buckets", action="store_true", help="Process all default buckets")
    parser.add_argument("--project-id", help="GCP project ID (required with --all)")
    parser.add_argument("--apply", action="store_true", default=False, help="Apply changes (default: dry-run)")
    parser.add_argument("--force", action="store_true", default=False, help="Overwrite rows with existing values")
    parser.add_argument("--verify", action="store_true", default=False, help="Count NULL rows only, no changes")
    parser.add_argument(
        "--per-vm", action="store_true", default=False, help="Also process per-VM shards under _index/per_vm/"
    )
    args = parser.parse_args()

    if args.all_buckets and not args.project_id:
        parser.error("--all requires --project-id")
    if not args.all_buckets and not (args.bucket and args.asset_group):
        parser.error("Provide --bucket + --asset-group, or --all --project-id <project>")

    dry_run = not args.apply and not args.verify
    if dry_run:
        logger.info("DRY RUN mode — pass --apply to write changes")

    targets: list[tuple[str, str]] = (
        _build_bucket_map(args.project_id) if args.all_buckets else [(args.bucket, args.asset_group)]
    )

    grand_total: dict[str, int] = {"total": 0, "skipped": 0, "filled": 0, "failed": 0, "not_derivable": 0}
    exit_code = 0

    for bucket, asset_group in targets:
        try:
            result = backfill_bucket(
                bucket,
                asset_group,
                dry_run=dry_run,
                force=args.force,
                verify_only=args.verify,
                per_vm=args.per_vm,
            )
            for k in grand_total:
                grand_total[k] += result.get(k, 0)
        except Exception as exc:  # noqa: broad-except — bucket-level isolation: one bucket's
            # failure must not abort processing of the remaining --all targets
            logger.exception("Bucket %s failed: %s", bucket, exc)
            exit_code = 1

    logger.info(
        "SUMMARY: total=%d skipped=%d filled=%d failed=%d not_derivable=%d",
        grand_total["total"],
        grand_total["skipped"],
        grand_total["filled"],
        grand_total["failed"],
        grand_total["not_derivable"],
    )

    if grand_total.get("not_derivable", 0) > 0 and args.verify:
        logger.warning("%d rows cannot be auto-derived — manual review needed", grand_total["not_derivable"])
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
