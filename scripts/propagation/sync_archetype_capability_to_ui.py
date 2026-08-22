# Epic: security_and_cross_cutting_master
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
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Mirrors unified-trading-pm/scripts/hooks/prettier-autostage.sh's version guard —
# prettier <3.9.5 corrupts content under this workspace's config (see
# prettier_emphasis_mangling_corpus_corruption_2026_07_14.md). Pin the same floor here.
_PRETTIER_MIN_VERSION = "3.9.5"


def _prettier_version_ok(version: str) -> bool:
    try:
        parts = tuple(int(p) for p in version.strip().split(".")[:3])
    except ValueError:
        return False
    floor = tuple(int(p) for p in _PRETTIER_MIN_VERSION.split("."))
    return parts >= floor


def _resolve_prettier(ui_repo_root: Path) -> list[str] | None:
    local = ui_repo_root / "node_modules" / ".bin" / "prettier"
    if local.is_file():
        probe = subprocess.run([str(local), "--version"], capture_output=True, text=True, check=False)
        if probe.returncode == 0 and _prettier_version_ok(probe.stdout):
            return [str(local)]
    if shutil.which("npx"):
        return ["npx", "-y", f"prettier@{_PRETTIER_MIN_VERSION}"]
    return None


MANIFEST_REL = Path(
    "unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json"
)
COVERAGE_TS_REL = Path("unified-trading-system-ui/lib/architecture-v2/coverage.ts")
ENUMS_TS_REL = Path("unified-trading-system-ui/lib/architecture-v2/enums.ts")

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
  | "event_settled"
  | "sleeve_mix";

export const INSTRUMENT_TYPES_V2: readonly InstrumentTypeV2[] = [
  "spot",
  "perp",
  "dated_future",
  "option",
  "lending",
  "staking",
  "lp",
  "event_settled",
  "sleeve_mix",
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


def _read_enum_archetype_ids(enums_ts_path: Path) -> list[str]:
    """Parse the hand-maintained ``STRATEGY_ARCHETYPES_V2`` array out of enums.ts.

    Some UAC archetypes are declared in the UI's enums mirror ahead of landing
    in the capability manifest (see sync commit 7cd80d34's "manifest-pending"
    note). Reading the enum list lets the generator emit stub coverage for
    those archetypes itself, so a plain ``--write`` re-run doesn't silently
    drop hand-added stubs the next time only the manifest side changes.
    """

    text = enums_ts_path.read_text(encoding="utf-8")
    # Skip past the `readonly StrategyArchetype[]` type annotation's own brackets to the
    # array literal's opening `[` (the one following `=`).
    match = re.search(r"export const STRATEGY_ARCHETYPES_V2:[^=]*=\s*\[(.*?)\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"could not locate STRATEGY_ARCHETYPES_V2 in {enums_ts_path}")
    return re.findall(r'"([A-Z0-9_]+)"', match.group(1))


_STUB_COMMENT = (
    "// Stub entries — archetypes declared in UAC enums but not yet in the capability manifest.\n"
    "// Re-run sync-archetype-capability-to-ui.sh --write to replace these with real data when the\n"
    "// manifest is populated.\n"
)


def _render_stub_archetype(archetype_id: str) -> str:
    const = _const_name(archetype_id)
    return (
        f"const {const}: ArchetypeCoverage = {{\n"
        f"  archetype: {_ts_string_literal(archetype_id)},\n"
        f"  usesRollingFutures: false,\n"
        f"  cells: [],\n"
        "};\n"
    )


def _render_archetype(entry: dict[str, object]) -> str:
    archetype_id = str(entry["archetype_id"])
    const = _const_name(archetype_id)
    cells = list(entry["cells"])  # type: ignore[arg-type]
    cell_blocks = ",\n".join(_render_cell(archetype_id, cell) for cell in cells)
    uses_rolling = "true" if bool(entry["uses_rolling_futures"]) else "false"
    cells_body = f"\n{cell_blocks},\n  " if cell_blocks else ""
    return (
        f"const {const}: ArchetypeCoverage = {{\n"
        f"  archetype: {_ts_string_literal(archetype_id)},\n"
        f"  usesRollingFutures: {uses_rolling},\n"
        f"  cells: [{cells_body}],\n"
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


def render_coverage_ts(manifest: dict[str, object], enum_archetype_ids: list[str]) -> str:
    archetypes = list(manifest["archetypes"])  # type: ignore[arg-type]
    archetype_blocks = "\n".join(_render_archetype(entry) for entry in archetypes)

    manifest_ids = {str(entry["archetype_id"]) for entry in archetypes}
    pending_ids = [aid for aid in enum_archetype_ids if aid not in manifest_ids]
    stub_blocks = "\n".join(_render_stub_archetype(aid) for aid in pending_ids)
    stub_section = f"\n{_STUB_COMMENT}\n{stub_blocks}\n" if pending_ids else ""

    mapping_lines = [f"  {entry['archetype_id']!s}: {_const_name(str(entry['archetype_id']))}," for entry in archetypes]
    mapping_lines += [f"  {aid}: {_const_name(aid)}," for aid in pending_ids]
    mapping_body = "\n".join(mapping_lines)
    footer = _FOOTER.replace("__MAPPING_BODY__", mapping_body)

    return _HEADER + archetype_blocks + stub_section + "\n" + footer


def _format_ts(text: str, ui_repo_root: Path) -> str:
    """Run the raw generator output through prettier so it matches the committed,
    hook-formatted file byte-for-byte. Without this, ``--check`` compares an
    unformatted render against a prettier-formatted commit and reports drift on
    every run, even when the manifest and coverage.ts are semantically in sync.
    """

    cmd = _resolve_prettier(ui_repo_root)
    if cmd is None:
        sys.stderr.write(
            f"WARN: no prettier >={_PRETTIER_MIN_VERSION} available; comparing/writing unformatted output.\n"
        )
        return text
    result = subprocess.run(
        [*cmd, "--stdin-filepath", str(COVERAGE_TS_REL.name)],
        input=text,
        capture_output=True,
        text=True,
        cwd=ui_repo_root,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(
            f"WARN: prettier formatting failed (exit {result.returncode}); comparing/writing unformatted output.\n"
            f"{result.stderr}\n"
        )
        return text
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True, help="workspace root directory")
    parser.add_argument("--check", action="store_true", help="verify only; exit 1 on drift")
    parser.add_argument("--write", action="store_true", help="rewrite coverage.ts")
    args = parser.parse_args()

    workspace = Path(args.workspace_root).resolve()
    manifest_path = workspace / MANIFEST_REL
    coverage_ts_path = workspace / COVERAGE_TS_REL
    enums_ts_path = workspace / ENUMS_TS_REL

    if not manifest_path.is_file():
        sys.stderr.write(f"ERROR: UAC manifest not found at {manifest_path}\n")
        return 2
    if not enums_ts_path.is_file():
        sys.stderr.write(f"ERROR: UI enums mirror not found at {enums_ts_path}\n")
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    enum_archetype_ids = _read_enum_archetype_ids(enums_ts_path)
    rendered = render_coverage_ts(manifest, enum_archetype_ids)
    ui_repo_root = workspace / COVERAGE_TS_REL.parts[0]
    rendered = _format_ts(rendered, ui_repo_root)

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
