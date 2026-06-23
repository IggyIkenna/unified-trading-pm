# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Render or verify ``unified-trading-system-ui/lib/architecture-v2/coverage.ts``
from the UAC archetype-capability manifest.

This is the downstream arm of G1.8: UAC owns the Python SSOT, UI renders
the TS mirror, and this script enforces parity. Invoked from:

  * ``unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh``
  * ``unified-trading-system-ui/scripts/quality-gates.sh`` (``--check`` mode).

Usage (via the shell wrapper, which injects ``--workspace-root``)::

    bash sync-archetype-capability-to-ui.sh            # --check
    bash sync-archetype-capability-to-ui.sh --write    # rewrite coverage.ts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MANIFEST_REL = Path(
    "unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json"
)
COVERAGE_TS_REL = Path("unified-trading-system-ui/lib/architecture-v2/coverage.ts")

_HEADER = """\
// AUTO-GENERATED from UAC archetype_capability_manifest.json.
// Do not edit by hand. Re-run:
//   bash unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh --write
// SSOT: unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json
// Codex narrative: unified-trading-pm/codex/09-strategy/architecture-v2/category-instrument-coverage.md

import type { StrategyArchetype, VenueCategoryV2 } from "./enums";

export type InstrumentTypeV2 =
  | "spot"
  | "perp"
  | "dated_future"
  | "option"
  | "lending"
  | "staking"
  | "lp"
  | "event_settled";

export const INSTRUMENT_TYPES_V2: readonly InstrumentTypeV2[] = [
  "spot",
  "perp",
  "dated_future",
  "option",
  "lending",
  "staking",
  "lp",
  "event_settled",
] as const;

export type CoverageStatus = "SUPPORTED" | "PARTIAL" | "BLOCKED" | "NOT_APPLICABLE";

export type SignalVariant =
  | "price"
  | "funding_rate"
  | "basis"
  | "iv_dispersion"
  | "vol_metric"
  | "rate_spread"
  | "liquidation_bonus"
  | "odds"
  | "event_surprise"
  | "delta_as_expression"
  | "staking_yield"
  | "zscore_reversion"
  | "momentum_ranking"
  | "spread_capture";

export type RollMode = "rolling" | "fixed" | "both" | "n/a";

export interface CoverageCell {
  archetype: StrategyArchetype;
  assetGroup: VenueCategoryV2;
  instrumentType: InstrumentTypeV2;
  status: CoverageStatus;
  representativeVenueIds: readonly string[];
  signalVariants: readonly SignalVariant[];
  rollMode: RollMode;
  notes: string;
  blockListRefs: readonly string[];
  representativeSlotLabels: readonly string[];
}

export interface ArchetypeCoverage {
  archetype: StrategyArchetype;
  usesRollingFutures: boolean;
  cells: readonly CoverageCell[];
}

"""


def _ts_string_literal(value: str) -> str:
    """Return a double-quoted TS string literal with common escapes."""

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _ts_string_array(values: list[str]) -> str:
    if not values:
        return "[]"
    items = ", ".join(_ts_string_literal(v) for v in values)
    return f"[{items}]"


def _render_cell(archetype_id: str, cell: dict[str, object]) -> str:
    raw_group = cell.get("asset_group") or cell.get("category")
    if raw_group is None:
        raise KeyError("cell missing asset_group (and legacy category)")
    fields = [
        f"      archetype: {_ts_string_literal(archetype_id)}",
        f"      assetGroup: {_ts_string_literal(str(raw_group))}",
        f"      instrumentType: {_ts_string_literal(str(cell['instrument_type']))}",
        f"      status: {_ts_string_literal(str(cell['status']))}",
        f"      representativeVenueIds: {_ts_string_array(list(cell['venue_ids']))}",  # type: ignore[arg-type]
        f"      signalVariants: {_ts_string_array(list(cell['signal_variants']))}",  # type: ignore[arg-type]
        f"      rollMode: {_ts_string_literal(str(cell['roll_mode']))}",
        f"      notes: {_ts_string_literal(str(cell['notes']))}",
        f"      blockListRefs: {_ts_string_array(list(cell['block_list_refs']))}",  # type: ignore[arg-type]
        f"      representativeSlotLabels: {_ts_string_array(list(cell['representative_slot_labels']))}",  # type: ignore[arg-type]
    ]
    body = ",\n".join(fields)
    return "    {\n" + body + ",\n    }"


def _const_name(archetype_id: str) -> str:
    return archetype_id.lower()


def _render_archetype(entry: dict[str, object]) -> str:
    archetype_id = str(entry["archetype_id"])
    const = _const_name(archetype_id)
    cells = list(entry["cells"])  # type: ignore[arg-type]
    cell_blocks = ",\n".join(_render_cell(archetype_id, cell) for cell in cells)
    uses_rolling = "true" if bool(entry["uses_rolling_futures"]) else "false"
    return (
        f"const {const}: ArchetypeCoverage = {{\n"
        f"  archetype: {_ts_string_literal(archetype_id)},\n"
        f"  usesRollingFutures: {uses_rolling},\n"
        f"  cells: [\n{cell_blocks},\n  ],\n"
        "};\n"
    )


_FOOTER = """\
export const ARCHETYPE_COVERAGE: Readonly<Record<StrategyArchetype, ArchetypeCoverage>> = {
__MAPPING_BODY__
};

export function allCoverageCells(): readonly CoverageCell[] {
  const out: CoverageCell[] = [];
  for (const archetype of Object.keys(ARCHETYPE_COVERAGE) as StrategyArchetype[]) {
    out.push(...ARCHETYPE_COVERAGE[archetype].cells);
  }
  return out;
}

export function coverageForArchetype(archetype: StrategyArchetype): ArchetypeCoverage {
  return ARCHETYPE_COVERAGE[archetype];
}

export function cellsMatching(predicate: (cell: CoverageCell) => boolean): readonly CoverageCell[] {
  return allCoverageCells().filter(predicate);
}

export function cellsForInstrumentPair(
  legAType: InstrumentTypeV2,
  legBType: InstrumentTypeV2,
): readonly CoverageCell[] {
  return cellsMatching(
    (c) =>
      c.status !== "NOT_APPLICABLE" &&
      (c.instrumentType === legAType || c.instrumentType === legBType) &&
      (c.archetype === "ARBITRAGE_PRICE_DISPERSION" ||
        c.archetype === "CARRY_BASIS_PERP" ||
        c.archetype === "CARRY_BASIS_DATED" ||
        c.archetype === "STAT_ARB_PAIRS_FIXED" ||
        c.archetype === "STAT_ARB_CROSS_SECTIONAL" ||
        c.archetype === "CARRY_STAKED_BASIS"),
  );
}

export function blockedCells(): readonly CoverageCell[] {
  return cellsMatching((c) => c.status === "BLOCKED");
}

export function supportedCells(): readonly CoverageCell[] {
  return cellsMatching((c) => c.status === "SUPPORTED");
}

export function rollingFutureCells(): readonly CoverageCell[] {
  return cellsMatching((c) => c.rollMode === "rolling" || c.rollMode === "both");
}
"""


def render_coverage_ts(manifest: dict[str, object]) -> str:
    archetypes = list(manifest["archetypes"])  # type: ignore[arg-type]
    archetype_blocks = "\n".join(_render_archetype(entry) for entry in archetypes)

    mapping_lines = [f"  {entry['archetype_id']!s}: {_const_name(str(entry['archetype_id']))}," for entry in archetypes]
    mapping_body = "\n".join(mapping_lines)
    footer = _FOOTER.replace("__MAPPING_BODY__", mapping_body)

    return _HEADER + archetype_blocks + "\n" + footer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True, help="workspace root directory")
    parser.add_argument("--check", action="store_true", help="verify only; exit 1 on drift")
    parser.add_argument("--write", action="store_true", help="rewrite coverage.ts")
    args = parser.parse_args()

    workspace = Path(args.workspace_root).resolve()
    manifest_path = workspace / MANIFEST_REL
    coverage_ts_path = workspace / COVERAGE_TS_REL

    if not manifest_path.is_file():
        sys.stderr.write(f"ERROR: UAC manifest not found at {manifest_path}\n")
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rendered = render_coverage_ts(manifest)

    if args.write:
        coverage_ts_path.write_text(rendered, encoding="utf-8")
        print(f"wrote {coverage_ts_path}")
        return 0

    # Default is --check even if flag omitted.
    committed = coverage_ts_path.read_text(encoding="utf-8") if coverage_ts_path.is_file() else ""
    if committed == rendered:
        print("lib/architecture-v2/coverage.ts is up-to-date")
        return 0

    sys.stderr.write(
        "lib/architecture-v2/coverage.ts drifted from UAC archetype_capability_manifest.json.\n"
        "Re-run: bash unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh --write\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
