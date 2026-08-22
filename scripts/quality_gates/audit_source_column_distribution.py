#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
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


_WANTED_COLUMNS = ("category", "asset_group", "venue", "data_type", "source")
_BATCH_SIZE = 500_000


def _resolve_columns(path: str) -> tuple[list[str], str]:
    """Schema-peek the parquet and resolve the narrow column set + category column name.

    This audit only needs 5 of the manifest's ~50 columns, and some prod indices
    (e.g. DeFi's, ~6.7GB/33M rows) are large enough that even a column-projected
    *single-shot* read risks stalling/OOMing the shared host (see
    ``plans/archive/2026_08/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md``).
    Streaming per-row-group (``_iter_manifest_batches`` below) is the actual memory
    bound; this just resolves which columns exist up front.
    """
    import pyarrow.parquet as pq

    schema_names = set(pq.read_schema(path).names)
    cat_col = next((c for c in ("category", "asset_group") if c in schema_names), None)
    if cat_col is None:
        msg = f"manifest has neither 'category' nor 'asset_group' column; columns={sorted(schema_names)}"
        raise ValueError(msg)
    if "source" not in schema_names:
        msg = "manifest parquet has no 'source' column — not a v9+ manifest; cannot audit provenance."
        raise ValueError(msg)
    if "data_type" not in schema_names:
        msg = f"manifest has no 'data_type' column; columns={sorted(schema_names)}"
        raise ValueError(msg)
    columns = [c for c in _WANTED_COLUMNS if c in schema_names]
    return columns, cat_col


def _iter_manifest_batches(path: str, columns: list[str]) -> Iterable[pd.DataFrame]:
    """Stream the consolidated availability-index parquet (local or gs:// URI) in bounded batches.

    Reads only ``columns`` (5 of ~50) AND row-group-streams via
    ``ParquetFile.iter_batches`` instead of materializing the whole table —
    peak memory stays proportional to ``_BATCH_SIZE`` rows regardless of total
    manifest size, which single-shot ``pd.read_parquet`` (even column-projected)
    does not guarantee on the largest prod indices.
    """
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(columns=columns, batch_size=_BATCH_SIZE):
        yield batch.to_pandas()


def collect(batches: Iterable[pd.DataFrame], cat_col: str) -> list[CellStats]:
    cells: dict[tuple[str, str, str], CellStats] = {}
    rows_seen = 0
    for df in batches:
        venue_col = "venue" if "venue" in df.columns else None
        for row in df.itertuples(index=False):
            ag = str(getattr(row, cat_col, "") or "")
            venue = str(getattr(row, venue_col, "") or "") if venue_col else ""
            dt = str(getattr(row, "data_type", "") or "")
            src = str(getattr(row, "source", "") or "")
            key = (ag, venue, dt)
            cell = cells.setdefault(key, CellStats(asset_group=ag, venue=venue, data_type=dt))
            cell.total_rows += 1
            cell.source_counts[src] += 1
        rows_seen += len(df)
        print(f"[audit_source_column_distribution] ...{rows_seen} rows streamed", file=sys.stderr)
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

    columns, cat_col = _resolve_columns(args.manifest_path)
    batches = _iter_manifest_batches(args.manifest_path, columns)
    cells = collect(batches, cat_col)
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
