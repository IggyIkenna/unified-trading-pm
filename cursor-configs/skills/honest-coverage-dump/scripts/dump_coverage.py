#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Honest-coverage dump -- Tuesday deliverable 2
(/plans/active/data_pipeline_completion_2026_08_21.md § "Tuesday dumps").

Prints per-shard coverage straight from the already-computed daily
coverage.json (SSOT: /codex/02-data/honest-coverage-model.md). This is a
DUMP of data we already have, not a measurement campaign -- it never reads
GCS objects, never re-derives the expected universe, and never recomputes a
capture_status. It reuses instruments-service's measure_honest_coverage.py
output verbatim (the same payload deployment-api's
/api/data-status/honest-coverage route returns).

Grain is whatever coverage.json currently carries -- see shard_universe.py's
detect_grain(). No flag forces a grain; the payload decides. Re-running this
after the instrument_type axis lands on VenueCapabilityRecord picks up the
finer (venue, instrument_type, data_type) grain automatically.

Reads GCS via `unified_trading_library.cloud_interface` only (never a
subprocess `gcloud`/`gsutil` call -- that is a hard workspace ban, reads
included; see shard_universe.py's module docstring). Run under a venv that
has `unified-trading-library` installed -- instruments-service's `.venv` is
the natural choice (it owns the script that WRITES this coverage.json):

    cd instruments-service && .venv/bin/python3 \\
        ../unified-trading-pm/cursor-configs/skills/honest-coverage-dump/scripts/dump_coverage.py

Usage:
    python dump_coverage.py                              # latest date, all asset_groups
    python dump_coverage.py --date 2026-08-17
    python dump_coverage.py --asset-group cefi --venue OKX-FUTURES
    python dump_coverage.py --json                        # machine-readable
    python dump_coverage.py --project my-other-project
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from shard_universe import (
    CAPTURE_STATE_FIELDS,
    DEFAULT_PROJECT_ID,
    DISPLAY_LABELS,
    NOT_EXPECTED_LABEL,
    CoverageReadError,
    ShardCell,
    detect_grain,
    iter_shard_cells,
    load_coverage,
    missing_tuples,
    not_expected_tuples,
)


def _matches(cell: ShardCell, asset_groups: set[str] | None, venues: set[str] | None) -> bool:
    if asset_groups and cell.asset_group not in asset_groups:
        return False
    if venues and cell.venue not in venues:
        return False
    return True


def _format_shard_key(cell: ShardCell) -> str:
    if cell.instrument_type is not None:
        return f"{cell.asset_group}/{cell.venue}/{cell.instrument_type}/{cell.data_type}"
    return f"{cell.asset_group}/{cell.venue}/{cell.data_type}"


def _reachable_pct(cell: ShardCell) -> float | None:
    denom = cell.reachable_total()
    if denom == 0:
        return None
    return round(100.0 * cell.count("captured") / denom, 2)


def _all_shards_pct(cell: ShardCell) -> float | None:
    denom = cell.all_shards_total()
    if denom == 0:
        return None
    return round(100.0 * cell.count("captured") / denom, 2)


def build_report(
    payload: dict,
    asset_groups: set[str] | None,
    venues: set[str] | None,
) -> dict:
    grain = detect_grain(payload)
    cells = [c for c in iter_shard_cells(payload, grain) if _matches(c, asset_groups, venues)]

    shard_rows = []
    for cell in sorted(cells, key=_format_shard_key):
        state_counts = {DISPLAY_LABELS[f]: cell.count(f) for f in CAPTURE_STATE_FIELDS}
        shard_rows.append(
            {
                "shard": _format_shard_key(cell),
                "asset_group": cell.asset_group,
                "venue": cell.venue,
                "instrument_type": cell.instrument_type,
                "data_type": cell.data_type,
                "capture_states": state_counts,
                "reachable_denominator": cell.reachable_total(),
                "reachable_coverage_pct": _reachable_pct(cell),
                "all_shards_denominator": cell.all_shards_total(),
                "all_shards_coverage_pct": _all_shards_pct(cell),
            }
        )

    ags_present = sorted({c.asset_group for c in cells}) if cells else sorted(asset_groups or [])
    not_expected_section = {ag: not_expected_tuples(payload, ag) for ag in ags_present}
    layer1_holes_section = {ag: missing_tuples(payload, ag) for ag in ags_present}

    totals = dict.fromkeys(CAPTURE_STATE_FIELDS, 0)
    for cell in cells:
        for f in CAPTURE_STATE_FIELDS:
            totals[f] += cell.count(f)
    total_reachable_denom = totals["captured"] + totals["attempted_failed"] + totals["expected_unattempted"]
    total_reachable_pct = (
        round(100.0 * totals["captured"] / total_reachable_denom, 2) if total_reachable_denom else None
    )

    return {
        "grain": grain,
        "generated_at_of_source": payload.get("generated_at"),
        "date_of_source": payload.get("date"),
        "schema_version": payload.get("schema_version"),
        "shard_count": len(shard_rows),
        "totals": {
            **{DISPLAY_LABELS[f]: totals[f] for f in CAPTURE_STATE_FIELDS},
            "reachable_denominator": total_reachable_denom,
            "reachable_coverage_pct": total_reachable_pct,
        },
        f"{NOT_EXPECTED_LABEL}_tuples_by_asset_group": not_expected_section,
        "layer1_hole_tuples_by_asset_group": layer1_holes_section,
        "shards": shard_rows,
    }


def _print_human(report: dict, gcs_path: str, resolved_date: str, verbose: bool) -> None:
    print(f"Honest coverage dump -- source: {gcs_path} (date={resolved_date})")
    print(f"Grain: {report['grain']} ({'venue x instrument_type x data_type' if report['grain'] == 'instrument_type' else 'venue x data_type'})")
    print(f"Shards in scope: {report['shard_count']}")
    print()
    t = report["totals"]
    print("=== Totals across shards in scope ===")
    for field in CAPTURE_STATE_FIELDS:
        label = DISPLAY_LABELS[field]
        print(f"  {label:<22} {t[label]:>10}")
    denom = t["reachable_denominator"]
    pct = t["reachable_coverage_pct"]
    pct_str = f"{pct}%" if pct is not None else "undefined (denominator=0)"
    print(f"  {'reachable coverage':<22} {pct_str}  (denominator = captured + attempted_failed + expected_unattempted = {denom})")
    print()

    for ag, strays in report[f"{NOT_EXPECTED_LABEL}_tuples_by_asset_group"].items():
        holes = report["layer1_hole_tuples_by_asset_group"].get(ag, [])
        print(f"=== {ag}: not-expected (stray) tuples = {len(strays)}, Layer-1 holes (missing_tuples) = {len(holes)} ===")
        if verbose:
            for t2 in strays[:20]:
                print(f"    not-expected: {t2}")
            for h in holes[:20]:
                print(f"    layer1-hole:  {h}")
    print()

    if verbose:
        print("=== Per-shard rows ===")
        for row in report["shards"]:
            pct = row["reachable_coverage_pct"]
            pct_str = f"{pct}%" if pct is not None else "undefined"
            cs = row["capture_states"]
            cs_str = ", ".join(f"{k}={v}" for k, v in cs.items())
            print(f"  {row['shard']:<60} reachable={pct_str:<10} denom={row['reachable_denominator']:<6} [{cs_str}]")
    else:
        print("(pass --verbose for the full per-shard table and stray/hole listings)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=DEFAULT_PROJECT_ID, help="GCP project hosting the honest-coverage bucket")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD; defaults to the latest available coverage.json")
    parser.add_argument("--asset-group", action="append", default=None, help="Filter to one or more asset_groups (repeatable)")
    parser.add_argument("--venue", action="append", default=None, help="Filter to one or more venues (repeatable)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of the human report")
    parser.add_argument("--verbose", action="store_true", help="Print the full per-shard table and stray/hole listings")
    args = parser.parse_args()

    try:
        payload, resolved_date, gcs_path = load_coverage(args.project, args.date)
    except CoverageReadError as exc:
        print(f"COULD NOT READ coverage.json -- {exc}", file=sys.stderr)
        print("This dump reports honestly when it cannot read its source; it does not fabricate a payload.", file=sys.stderr)
        return 1

    asset_groups = set(args.asset_group) if args.asset_group else None
    venues = set(args.venue) if args.venue else None
    report = build_report(payload, asset_groups, venues)

    if args.json:
        report["source_gcs_path"] = gcs_path
        report["resolved_date"] = resolved_date
        json.dump(report, sys.stdout, indent=2, default=lambda o: asdict(o) if hasattr(o, "__dataclass_fields__") else str(o))
        print()
    else:
        _print_human(report, gcs_path, resolved_date, args.verbose)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
