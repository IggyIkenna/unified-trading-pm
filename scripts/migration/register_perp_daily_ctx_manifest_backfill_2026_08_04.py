#!/usr/bin/env python3
# Epic: manifest_master
# Lifecycle: oneoff
# Delete-when: after prod-run + manifest-verify confirms perp_daily_ctx captured rows
#   match the discovered object count for every registered (day, venue) shard
"""One-shot: register availability-manifest rows for already-migrated historical
``perp_daily_ctx`` GCS objects in the shared DeFi tick-data bucket.

WHY: ``perp_daily_ctx`` was, until 2026-08-04, a genuine manifest-invisibility gap —
no registered ``data_type``/``SchemaContract`` under UAC's
``DATA_TYPES_BY_ASSET_GROUP["defi"]`` (fixed same session, see
``issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md``). Real,
already-migrated historical rows sit in the shared bucket TODAY
(``CanonicalPerpFundingProvider`` reads them for the funding-driven strategy
archetypes' mark price) but the availability manifest has never heard of them. This
script discovers those already-existing GCS objects via a BOUNDED, exact-prefix
listing (never a whole-corpus walk — see "Discovery method" below) and registers one
``ManifestWriter.add()`` row per (day, venue) shard. Purely additive: it never deletes
or rewrites a GCS object, only ADDS manifest rows for objects that already exist.

Discovery method (single-walk discipline): a naive ``day={D}/`` prefix listing returns
EVERY object the shared bucket has for that day across every asset_group/venue/
data_type (confirmed empirically: 5,000-26,000 objects/day) — effectively a
whole-corpus walk if repeated per day. Instead this script lists the FULLY-QUALIFIED
per-(day, venue) prefix directly (``.../pipeline_mode=X/asset_group=Y/venue=Z/
chain=.../instrument_type=perpetual/data_type=perp_daily_ctx/``), which is a true O(1)
bounded call per day (confirmed ~1-2s each against prod).

KNOWN SHARD GRAIN (verified against real GCS content 2026-08-04): the historical
HYPERLIQUID corpus is written ONE FILE PER COIN PER DAY (e.g. ``WLD.parquet``), not one
combined file/day — each file carries exactly 1 row. The CeFi Tardis corpus (7 venues,
narrow 2026-05-16..22 window) is one combined file per (venue, day)
(``cefi_{VENUE}_{DAY}.parquet``). ``row_count`` below is the number of matching blobs
per (day, venue) — verified-correct under this per-file-is-1-row shape for HL; for the
CeFi cluster each file is also read to confirm its real row count (small volume, ~49
files) since that writer's shape was never spot-checked.

**RECONCILED against the source issue doc's "1,109 objects" sanity-check number**: a
real bounded GCS scan (this script's own dry-run, 2026-08-04) found the HYPERLIQUID
``perp_daily_ctx`` corpus spans EXACTLY 2023-05-20..2026-06-01 with zero gap days — and
``(date(2026,6,1) - date(2023,5,20)).days + 1 == 1109``, an exact byte-for-byte match
with the issue doc's "1,109 objects" figure. That figure was counting SHARD-DAYS (one
per calendar day, fully daily coverage, no gaps), not individual per-coin files — the
real per-coin-file population within those 1,109 days is ~169,400 files (confirmed:
coin-count per day grows from 22 in 2023-05 to ~230 by 2026-05, one file per coin per
day, verified 1 row/file), which this script correctly collapses back to ONE manifest
row per (day, venue) — 1,109 HL rows, matching the reconciled day-count, each carrying
the real summed per-day row_count. Every HL day ALSO carries exactly one
``_migrated_hyperliquid_*.parquet`` consolidation-marker file (a redundant bulk copy of
that same day's rows, left over from a 2026-06-18 consolidation pass) — excluded from
discovery (see ``discover()``) so it is never double-counted. The corpus stops abruptly
after 2026-06-01 (no objects on/after 2026-06-02) — no live writer has produced
``perp_daily_ctx`` for HL since; a separate, real, NOT-yet-filed forward gap, out of
this script's scope (this script only registers manifest rows for objects that already
exist — it does not backfill or resume live production).

Usage::

    # Dry-run (default) — prints per-day-range discovery totals, writes nothing:
    python register_perp_daily_ctx_manifest_backfill_2026_08_04.py

    # Apply — registers one manifest row per (day, venue) shard, then writes:
    python register_perp_daily_ctx_manifest_backfill_2026_08_04.py --apply

    # Also run the manifest consolidator once the per-VM shard is written:
    python register_perp_daily_ctx_manifest_backfill_2026_08_04.py --apply --consolidate

    # Narrow the HL window (default is the empirically-confirmed full corpus range):
    python register_perp_daily_ctx_manifest_backfill_2026_08_04.py --hl-start 2023-05-20 --hl-end 2026-07-12

Requires ``GCP_PROJECT_ID`` in the environment (``get_storage_client()``'s project-id
resolution — a bare one-off script has no service bootstrap to set it implicitly).

Source: issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md (todo -010).
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

logger = logging.getLogger("register_perp_daily_ctx_manifest_backfill")

_DATA_TYPE = "perp_daily_ctx"

# HYPERLIQUID's confirmed real corpus window (verified via live GCS listing 2026-08-04
# — see module docstring). 2023-05-20 is also the HL S3 asset_ctxs source-coverage
# start referenced by market-tick-data-service/scripts/
# backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py.
_HL_DEFAULT_START = date(2023, 5, 20)
_HL_DEFAULT_END = date(2026, 7, 12)

# 7 CeFi Tardis venues' narrow capture window (issue doc fact #3 / archived
# defi_dedicated_bucket_shared_migration_2026_07_13.md residual-gap Progress Log:
# "7 CeFi Tardis venues' 2026-05-16..22 perp capture (98 objs)" — 7 venues x 7 days x
# 2 data_types (perp_funding + perp_daily_ctx) = 98, an exact match confirmed live).
_CEFI_TARDIS_VENUES: tuple[str, ...] = (
    "BINANCE-FUTURES",
    "BYBIT-FUTURES",
    "OKX-FUTURES",
    "DERIBIT",
    "KRAKEN-FUTURES",
    "BITGET-FUTURES",
    "BITFINEX-FUTURES",
)
_CEFI_DEFAULT_START = date(2026, 5, 16)
_CEFI_DEFAULT_END = date(2026, 5, 22)


@dataclass
class ShardTarget:
    """One (asset_group, pipeline_mode, venue, chain, instrument_type) prefix scope to
    scan across its own day range — the fully-qualified prefix that makes each day's
    GCS listing O(1) instead of a whole-day-across-the-bucket walk.

    ``rows_per_file``: when the per-file row shape is KNOWN and constant (verified
    2026-08-04 for HYPERLIQUID — every real per-coin file carries exactly 1 row), set
    this to skip a real per-file download/read for row_count (170K+ files would
    otherwise mean 170K+ GCS downloads for a count already knowable from the listing
    alone). Leave ``None`` when the shape is unverified/variable (the CeFi Tardis
    cluster's combined per-venue-per-day files carry a VARIABLE row count — confirmed
    9 rows for one sampled BINANCE-FUTURES file, not 1 — so those are always read for
    real; the cluster is small, ~49 files, so this is cheap)."""

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
        # Exclude "_migrated_*" consolidation-marker files (verified 2026-08-04:
        # EVERY HYPERLIQUID day carries exactly one such file, a redundant bulk copy
        # of that SAME day's whole per-coin population under one name, left over from
        # a 2026-06-18 consolidation pass — e.g. a 231-file day is 230 real per-coin
        # files + 1 marker duplicating those same 230 rows again). Counting it would
        # double-count real observations.
        names = [
            b.name
            for b in blobs
            if b.name.endswith(".parquet") and not b.name.rsplit("/", 1)[-1].startswith("_migrated")
        ]
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
    """Sum real per-file row counts (each file is small — a per-coin or per-venue
    daily snapshot, never a bulk shard) so the registered row_count is honest."""
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
    logger.info("Registered %d (day, venue) manifest rows for perp_daily_ctx (%d failed)", registered, failed)
    return registered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Write manifest rows (default: dry-run, discovery only)")
    parser.add_argument("--consolidate", action="store_true", help="Run the manifest consolidator after --apply")
    parser.add_argument("--hl-start", default=_HL_DEFAULT_START.isoformat())
    parser.add_argument("--hl-end", default=_HL_DEFAULT_END.isoformat())
    parser.add_argument("--cefi-start", default=_CEFI_DEFAULT_START.isoformat())
    parser.add_argument("--cefi-end", default=_CEFI_DEFAULT_END.isoformat())
    parser.add_argument("--skip-cefi", action="store_true", help="Skip the 7-venue CeFi Tardis cluster")
    parser.add_argument("--skip-hl", action="store_true", help="Skip HYPERLIQUID")
    parser.add_argument("--max-workers", type=int, default=16)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    bucket = resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")
    logger.info("Bucket: gs://%s", bucket)

    targets: list[ShardTarget] = []
    if not args.skip_hl:
        targets.append(
            ShardTarget(
                asset_group="defi",
                pipeline_mode=PipelineMode.BATCH_HYPERLIQUID.value,
                venue="HYPERLIQUID",
                chain="HYPERLIQUID",
                instrument_type="perpetual",
                start=date.fromisoformat(args.hl_start),
                end=date.fromisoformat(args.hl_end),
                source="",
                rows_per_file=1,  # verified 2026-08-04 — every real per-coin file is 1 row
            )
        )
    if not args.skip_cefi:
        for venue in _CEFI_TARDIS_VENUES:
            targets.append(
                ShardTarget(
                    asset_group="cefi",
                    pipeline_mode=PipelineMode.BATCH_TARDIS.value,
                    venue=venue,
                    chain="",
                    instrument_type="perpetual",
                    start=date.fromisoformat(args.cefi_start),
                    end=date.fromisoformat(args.cefi_end),
                    source="tardis",
                )
            )

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
        # precedent (defi_fold_manifest_registration_pending_2026_07_21.md's recipe)
        # and avoids a deep-import violation (no top-level `consolidate` export).
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
