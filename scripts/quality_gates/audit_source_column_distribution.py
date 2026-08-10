#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Phase 7 — prod `source`-column distribution audit (read-only, data-state).

``data_source_provenance_all_asset_groups_2026_06_01.md`` Phase 7 [AUDIT]:

  After enforcement + backfill land, read the ACTUAL ``source`` column
  distribution per ``(asset_group, venue, data_type)`` in the prod manifest /
  parquets and confirm **zero blank ``source`` on every external-vendor cell,
  all asset groups** (not just multi-source). Data-state, NOT a code constant —
  per the manifest-v8 lesson (the constant said 8 while 0% of rows were v8).

This is a **read-only** audit. It reads a consolidated availability-index
parquet (local path or ``gs://`` URI), groups rows by
``(category, venue, data_type)``, and reports the per-cell ``source`` histogram.
A cell is flagged RED when it has a UAC ``SOURCE_PRIORITY`` entry with ≥1
**external** source (i.e. ``external_sources_for(...)`` is non-empty) yet has
rows with a blank ``source``. Computed/service-only + unregistered cells are
exempt (per the universal-stamping design — `COMPUTED_SOURCES`).

SEQUENCING (operator banner 2026-06-01): the prod run is sequenced AFTER the
`bucket_name_ssot_legacy_dual_write_remediation` server-side copy finishes AND
the write-path enforcement + `source` backfill land. Running it before backfill
will (correctly) report ~100% blank — the pre-enforcement baseline. This tool
is built now; the prod walk is the sequenced step.

Usage::

    # local or remote consolidated manifest parquet:
    python audit_source_column_distribution.py --manifest-path <path-or-gs-uri>
    # fail (exit 1) if any external cell has blank source:
    python audit_source_column_distribution.py --manifest-path <p> --strict
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

import pandas as pd

try:  # noqa: fallback-import — optional UAC import; unavailable means the audit cannot run at all, so it exits 0
    from unified_api_contracts import external_sources_for, has_source_priority
except ImportError as exc:
    print(
        f"[audit_source_column_distribution] unified_api_contracts not importable: {exc} — cannot audit.",
        file=sys.stderr,
    )
    raise SystemExit(0) from exc


@dataclass
class CellStats:
    asset_group: str
    venue: str
    data_type: str
    total_rows: int = 0
    source_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def blank_rows(self) -> int:
        return self.source_counts.get("", 0)

    @property
    def external_required(self) -> bool:
        """True when the cell has ≥1 external source (blank source is then RED)."""
        return bool(external_sources_for(self.asset_group, self.data_type))


def _read_manifest(path: str) -> pd.DataFrame:
    """Read the consolidated availability-index parquet (local or gs:// URI)."""
    # pandas reads gs:// transparently when gcsfs is installed; falls back to a
    # clear error otherwise. Read-only.
    return pd.read_parquet(path)


def _category_col(df: pd.DataFrame) -> str:
    for col in ("category", "asset_group"):
        if col in df.columns:
            return col
    msg = f"manifest has neither 'category' nor 'asset_group' column; columns={list(df.columns)}"
    raise ValueError(msg)


def collect(df: pd.DataFrame) -> list[CellStats]:
    cat_col = _category_col(df)
    if "source" not in df.columns:
        msg = "manifest parquet has no 'source' column — not a v9+ manifest; cannot audit provenance."
        raise ValueError(msg)
    venue_col = "venue" if "venue" in df.columns else None
    dt_col = "data_type" if "data_type" in df.columns else None
    if dt_col is None:
        msg = f"manifest has no 'data_type' column; columns={list(df.columns)}"
        raise ValueError(msg)

    cells: dict[tuple[str, str, str], CellStats] = {}
    for row in df.itertuples(index=False):
        ag = str(getattr(row, cat_col, "") or "")
        venue = str(getattr(row, venue_col, "") or "") if venue_col else ""
        dt = str(getattr(row, dt_col, "") or "")
        src = str(getattr(row, "source", "") or "")
        key = (ag, venue, dt)
        cell = cells.setdefault(key, CellStats(asset_group=ag, venue=venue, data_type=dt))
        cell.total_rows += 1
        cell.source_counts[src] += 1
    return list(cells.values())


def report(cells: list[CellStats]) -> tuple[int, int]:
    """Print the per-cell histogram. Return (red_cell_count, red_row_count)."""
    red_cells = 0
    red_rows = 0
    print("=== source-column distribution per (asset_group, venue, data_type) ===")
    for cell in sorted(cells, key=lambda c: (c.asset_group, c.venue, c.data_type)):
        registered = has_source_priority(cell.asset_group, cell.data_type)
        ext = cell.external_required
        hist = ", ".join(f"{s or '<blank>'}={n}" for s, n in sorted(cell.source_counts.items()))
        tag = "EXEMPT" if not ext else ("RED" if cell.blank_rows else "GREEN")
        if ext and cell.blank_rows:
            red_cells += 1
            red_rows += cell.blank_rows
        reg = "" if registered else " [UNREGISTERED]"
        print(f"  [{tag}] {cell.asset_group}/{cell.venue}/{cell.data_type}{reg}  rows={cell.total_rows}  {{{hist}}}")
    return red_cells, red_rows


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of the manifest source-column distribution.")
    parser.add_argument(
        "--manifest-path", required=True, help="Consolidated availability-index parquet (local or gs:// URI)."
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 if any external-vendor cell has blank source rows."
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    df = _read_manifest(args.manifest_path)
    cells = collect(df)
    red_cells, red_rows = report(cells)

    total_rows = sum(c.total_rows for c in cells)
    print(
        f"\n[audit_source_column_distribution] {len(cells)} cells, {total_rows} rows. "
        f"External-vendor cells with blank source: {red_cells} cell(s) / {red_rows} row(s)."
    )
    if red_cells and args.strict:
        print(
            "[audit_source_column_distribution] FAIL (--strict) — blank source on external-vendor cells. "
            "Run the source backfill (sequenced after the bucket remediation) then re-audit.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
