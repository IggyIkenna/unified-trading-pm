#!/usr/bin/env python3
# Epic: manifest_master
# Lifecycle: oneoff
# Delete-when: after prod-run + manifest-verify confirms perp_mark_price captured rows
#   match the discovered object count for every registered (day, venue) shard
"""One-shot: register availability-manifest rows for already-migrated historical
``perp_mark_price`` GCS objects in the shared DeFi tick-data bucket.

WHY: ``perp_mark_price`` is a genuine manifest-invisibility gap — no registered
``data_type``/``SchemaContract`` under UAC's ``DATA_TYPES_BY_ASSET_GROUP["defi"]`` (fixed
same session, see ``issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md``,
whose source todo named BOTH ``perp_daily_ctx`` and ``perp_mark_price`` — ``perp_daily_ctx``
was closed earlier this session via ``register_perp_daily_ctx_manifest_backfill_2026_08_04.py``,
this script closes the sibling gap). Real, already-migrated historical rows sit in the shared
bucket TODAY (copied forward by the 2026-07-13 dedicated-bucket-to-shared-bucket migration's
residual-gap closure pass — see ``/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_
2026_07_13.md`` Progress Log 2026-07-13 entry (c): "HL perp_mark_price (316 objs) preserved into
the shared bucket though no current reader consumes it") but the availability manifest has never
heard of them. This script discovers those already-existing GCS objects via a BOUNDED, exact-prefix
listing (never a whole-corpus walk — see "Discovery method" below) and registers one
``ManifestWriter.add()`` row per (day, venue) shard. Purely additive: it never deletes or rewrites
a GCS object, only ADDS manifest rows for objects that already exist.

**DISTINCT from perp_daily_ctx, confirmed via direct GCS content read (not name inference)**:
``perp_mark_price`` rows carry ONLY ``mark_price`` (no ``day_ntl_vlm``/``open_interest``) — a
different, narrower schema than ``perp_daily_ctx``'s. The only writer reference in the codebase,
``market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py``,
targets a bucket (``perp-funding-{project}``) confirmed DELETED (``gcloud storage buckets describe``
-> 404), AND its current code actually writes ``data_type=perp_daily_ctx`` (the module's own
``_DT`` constant was renamed at some point after these historical ``perp_mark_price`` rows were
produced — the docstring's OUTPUT section describing ``data_type=perp_mark_price`` is now stale).
So this data_type has no live writer and cannot be reproduced even by re-running that script.
Confirmed via direct grep of ``strategy-service/strategy_service/engine/core/
canonical_perp_funding_provider.py`` and ``canonical_dex_pool_provider.py`` (the only two
"Canonical*Provider" DeFi readers) that NEITHER references ``perp_mark_price`` — this is DEAD
data with no live reader. Registered anyway per the honest-coverage rule: real historical rows
should not stay structurally invisible to the manifest just because both writer and reader are
now dead.

Discovery method (single-walk discipline): a naive ``day={D}/`` prefix listing returns EVERY
object the shared bucket has for that day across every asset_group/venue/data_type — effectively
a whole-corpus walk if repeated per day. Instead this script lists the FULLY-QUALIFIED
per-(day, venue) prefix directly (``.../pipeline_mode=X/asset_group=Y/venue=Z/chain=.../
instrument_type=perpetual/data_type=perp_mark_price/``), a true O(1) bounded call per day
(confirmed ~1-2s each against prod) — mirrors the exact precedent already established by
``register_perp_daily_ctx_manifest_backfill_2026_08_04.py``.

**NOT contiguous — confirmed via a bounded binary search + spot-checks, then this script's own
full day-by-day scan (2026-08-04)**: unlike ``perp_daily_ctx``'s clean 2023-05-20..2026-06-01
zero-gap range, ``perp_mark_price`` spans 315 contiguous days (2023-05-20..2024-03-29) PLUS one
isolated day (2025-06-01, 199 objects) more than a year later — all objects carry the SAME
``available_at`` timestamp cluster (~2026-06-18T11:0x), i.e. every object was written in a single
historical migration/backfill batch, not by ongoing production. Because the shape is non-uniform
(unlike perp_daily_ctx's confirmed-contiguous window), this script scans the FULL candidate
window day-by-day rather than assuming contiguity — still one bounded exact-prefix call per day,
never a corpus walk.

KNOWN SHARD GRAIN (verified against real GCS content 2026-08-04, same as perp_daily_ctx's
HYPERLIQUID corpus): one file per coin per day (e.g. ``BTC.parquet``), each file carrying exactly
1 row — confirmed via direct content read of the 2023-05-20 and 2025-06-01 shards. No
``_migrated_*`` consolidation-marker files were found for this data_type (unlike perp_daily_ctx,
whose every day carries one) — nothing excluded from discovery here.

Usage::

    # Dry-run (default) — prints per-day-range discovery totals, writes nothing:
    python register_perp_mark_price_manifest_backfill_2026_08_04.py

    # Apply — registers one manifest row per (day, venue) shard, then writes:
    python register_perp_mark_price_manifest_backfill_2026_08_04.py --apply

    # Also run the manifest consolidator once the per-VM shard is written:
    python register_perp_mark_price_manifest_backfill_2026_08_04.py --apply --consolidate

    # Narrow the scan window (default is a bounded superset of the confirmed real range):
    python register_perp_mark_price_manifest_backfill_2026_08_04.py --start 2023-05-20 --end 2026-08-04

Requires ``GCP_PROJECT_ID`` in the environment (``get_storage_client()``'s project-id resolution
— a bare one-off script has no service bootstrap to set it implicitly).

Source: issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md (source todo named both
perp_daily_ctx and perp_mark_price), plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md
(todo -010, perp_daily_ctx half already landed; this closes the perp_mark_price sibling half).
"""

from __future__ import annotations

import argparse
import io
import logging
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

import pandas as pd
from unified_api_contracts import PipelineMode
from unified_trading_library import ManifestWriter, StorageClient, get_storage_client, resolve_bucket_name

logger = logging.getLogger("register_perp_mark_price_manifest_backfill")

_DATA_TYPE = "perp_mark_price"

# Bounded scan window: a superset of the confirmed real range (315 contiguous days
# 2023-05-20..2024-03-29 + one isolated day 2025-06-01), extended to "today" in case
# more isolated days exist that a spot-check sample missed. Still one bounded
# exact-prefix call per day (never a whole-corpus walk) — 2023-05-20 is the HL S3
# asset_ctxs source-coverage start (same origin as perp_daily_ctx's HL corpus).
_DEFAULT_START = date(2023, 5, 20)
_DEFAULT_END = date(2026, 8, 4)


@dataclass
class ShardTarget:
    """One (asset_group, pipeline_mode, venue, chain, instrument_type) prefix scope to
    scan across its own day range — the fully-qualified prefix that makes each day's
    GCS listing O(1) instead of a whole-day-across-the-bucket walk."""

    asset_group: str
    pipeline_mode: str
    venue: str
    chain: str
    instrument_type: str
    start: date
    end: date
    source: str = ""
    rows_per_file: int | None = None


@dataclass
class DayShardResult:
    target: ShardTarget
    day: date
    blob_names: list[str] = field(default_factory=list)


def _iter_days(start: date, end: date) -> list[date]:
    out: list[date] = []
    d = start
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def _prefix_for(target: ShardTarget, day: date) -> str:
    return (
        f"raw_tick_data/by_date/day={day:%Y-%m-%d}/"
        f"pipeline_mode={target.pipeline_mode}/asset_group={target.asset_group}/"
        f"venue={target.venue}/"
        + (f"chain={target.chain}/" if target.chain else "")
        + f"instrument_type={target.instrument_type}/data_type={_DATA_TYPE}/"
    )


def discover(bucket: str, targets: list[ShardTarget], *, max_workers: int = 16) -> list[DayShardResult]:
    """Bounded, exact-prefix discovery — one GCS list call per (target, day), never a
    whole-day or whole-corpus listing. Returns only shards with >=1 matching object."""
    storage = get_storage_client()
    jobs: list[tuple[ShardTarget, date]] = [(t, d) for t in targets for d in _iter_days(t.start, t.end)]

    def _list_one(target: ShardTarget, day: date) -> DayShardResult:
        prefix = _prefix_for(target, day)
        try:
            blobs = list(storage.list_blobs(bucket, prefix=prefix, resolve_size=False))
        except (OSError, ValueError, RuntimeError) as exc:
            logger.warning("list failed venue=%s day=%s (%s)", target.venue, day, exc)
            return DayShardResult(target=target, day=day, blob_names=[])
        names = [b.name for b in blobs if b.name.endswith(".parquet")]
        return DayShardResult(target=target, day=day, blob_names=names)

    results: list[DayShardResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_list_one, t, d) for t, d in jobs]
        for done, fut in enumerate(as_completed(futures), start=1):
            if done % 200 == 0:
                logger.info("scanned %d/%d (target, day) prefixes...", done, len(jobs))
            res = fut.result()
            if res.blob_names:
                results.append(res)
    return results


def _row_count(storage: StorageClient, bucket: str, blob_names: list[str]) -> int:
    """Sum real per-file row counts (each file is small — a per-coin daily snapshot,
    never a bulk shard) so the registered row_count is honest."""
    total = 0
    for name in blob_names:
        try:
            raw = storage.download_bytes(bucket, name)
            total += len(pd.read_parquet(io.BytesIO(raw)))
        except (OSError, ValueError, RuntimeError) as exc:
            logger.warning("row-count read failed %s (%s)", name, exc)
    return total


def _print_summary(results: list[DayShardResult]) -> int:
    by_venue_objs: dict[str, int] = defaultdict(int)
    by_venue_days: dict[str, set[date]] = defaultdict(set)
    total_objects = 0
    for res in results:
        by_venue_objs[res.target.venue] += len(res.blob_names)
        by_venue_days[res.target.venue].add(res.day)
        total_objects += len(res.blob_names)

    logger.info("=== Discovery summary ===")
    for venue in sorted(by_venue_objs):
        days = by_venue_days[venue]
        logger.info(
            "  venue=%-16s days_with_data=%-5d objects=%-6d date_range=%s..%s",
            venue,
            len(days),
            by_venue_objs[venue],
            min(days),
            max(days),
        )
        # Flag non-contiguity explicitly (this data_type is known non-contiguous —
        # confirmed real, not a discovery bug).
        gap_days = (max(days) - min(days)).days + 1 - len(days)
        if gap_days:
            logger.info("    (%d gap day(s) within that range — confirmed non-contiguous corpus)", gap_days)
    logger.info("  TOTAL objects discovered: %d across %d (day, venue) shards", total_objects, len(results))
    return total_objects


def register(bucket: str, results: list[DayShardResult]) -> int:
    """Register one ManifestWriter.add() row per (day, venue) shard. Best-effort per
    row (mirrors every other ManifestWriter one-off callsite) — a single row's failure
    never aborts the whole registration pass; failures are logged + counted."""
    storage = get_storage_client()
    writer = ManifestWriter(service_name="unified-trading-pm", catalogue_bucket=bucket)
    registered = 0
    failed = 0
    for res in sorted(results, key=lambda r: (r.day, r.target.venue)):
        if res.target.rows_per_file is not None:
            row_count = res.target.rows_per_file * len(res.blob_names)
        else:
            row_count = _row_count(storage, bucket, res.blob_names)
        if row_count <= 0:
            continue
        try:
            writer.add(
                processing_date=res.day,
                asset_group=res.target.asset_group,
                venue=res.target.venue,
                chain=res.target.chain,
                instrument_type=res.target.instrument_type,
                data_type=_DATA_TYPE,
                row_count=row_count,
                pipeline_mode=res.target.pipeline_mode,
                source=res.target.source,
            )
            registered += 1
        except (OSError, ValueError, RuntimeError) as exc:
            failed += 1
            logger.warning(
                "manifest add() failed venue=%s day=%s (%s)",
                res.target.venue,
                res.day,
                exc,
            )
    writer.write()
    logger.info("Registered %d (day, venue) manifest rows for perp_mark_price (%d failed)", registered, failed)
    return registered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Write manifest rows (default: dry-run, discovery only)")
    parser.add_argument("--consolidate", action="store_true", help="Run the manifest consolidator after --apply")
    parser.add_argument("--start", default=_DEFAULT_START.isoformat())
    parser.add_argument("--end", default=_DEFAULT_END.isoformat())
    parser.add_argument("--max-workers", type=int, default=16)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    bucket = resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")
    logger.info("Bucket: gs://%s", bucket)

    targets: list[ShardTarget] = [
        ShardTarget(
            asset_group="defi",
            pipeline_mode=PipelineMode.BATCH_HYPERLIQUID.value,
            venue="HYPERLIQUID",
            chain="HYPERLIQUID",
            instrument_type="perpetual",
            start=date.fromisoformat(args.start),
            end=date.fromisoformat(args.end),
            source="",
            rows_per_file=1,  # verified 2026-08-04 — every real per-coin file is 1 row
        )
    ]

    total_days = sum(len(_iter_days(t.start, t.end)) for t in targets)
    logger.info("Scanning %d (target, day) prefixes across %d shard targets...", total_days, len(targets))

    results = discover(bucket, targets, max_workers=args.max_workers)
    total_objects = _print_summary(results)

    if not args.apply:
        logger.info("DRY RUN — no manifest rows written. Re-run with --apply to register.")
        return 0

    registered = register(bucket, results)
    logger.info("Apply complete: %d manifest rows registered (%d objects covered)", registered, total_objects)

    if args.consolidate:
        # Subprocess CLI invocation (not a direct `unified_trading_library.
        # manifest_consolidator` import) — mirrors the established one-off-script
        # precedent (register_perp_daily_ctx_manifest_backfill_2026_08_04.py /
        # defi_fold_manifest_registration_pending_2026_07_21.md's recipe) and avoids a
        # deep-import violation (no top-level `consolidate` export).
        logger.info("Running manifest consolidator for gs://%s ...", bucket)
        subprocess.run(
            [sys.executable, "-m", "unified_trading_library.manifest_consolidator", "--bucket", bucket],
            check=True,
        )
        logger.info("Consolidator run complete.")

    logger.info("Done: %s", datetime.now(UTC).isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
