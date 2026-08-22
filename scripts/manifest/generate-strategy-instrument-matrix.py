#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate a strategy-instrument validation matrix from strategy-manifest.json.

Cross-references strategies with their declared instrument requirements:
1. Validates each strategy's `instruments` list against `venues` and `asset_groupes`
2. Checks instrument ID format consistency (VENUE:TYPE:PAYLOAD[@CHAIN])
3. Reports strategy-instrument coverage (which strategies cover which instruments)
4. Detects instrument conflicts (same instrument claimed by incompatible strategies)
5. Generates a machine-readable JSON matrix for downstream tooling

Can be wired into quality-gates.sh or run standalone.

Exit codes:
  0 -- all validations pass
  1 -- one or more validation errors

Usage:
    python3 scripts/manifest/generate-strategy-instrument-matrix.py
    python3 scripts/manifest/generate-strategy-instrument-matrix.py --json
    python3 scripts/manifest/generate-strategy-instrument-matrix.py --asset-group CEFI
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
PM_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PM_ROOT / "strategy-manifest.json"

# Canonical instrument ID pattern: VENUE:TYPE:PAYLOAD (with optional @CHAIN suffix)
_INSTRUMENT_ID_PATTERN = re.compile(r"^[A-Z0-9_-]+:[A-Z0-9_]+:[A-Za-z0-9_@.*-]+$")


def load_manifest(manifest_path: Path) -> dict[str, list[dict[str, object]]]:
    """Load and parse strategy-manifest.json.

    Returns:
        Dict with "strategies" key containing list of strategy entries.

    Raises:
        SystemExit: If the file is missing or invalid.
    """
    if not manifest_path.exists():
        print(f"FATAL: strategy-manifest.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path) as f:
        data: dict[str, list[dict[str, object]]] = json.load(f)
    return data


def validate_instrument_format(instrument_id: str) -> bool:
    """Check that an instrument ID follows the canonical VENUE:TYPE:PAYLOAD format."""
    return bool(_INSTRUMENT_ID_PATTERN.match(instrument_id))


def extract_instrument_venue(instrument_id: str) -> str:
    """Extract the venue portion from a canonical instrument ID."""
    parts = instrument_id.split(":", 1)
    return parts[0] if parts else ""


def extract_instrument_type(instrument_id: str) -> str:
    """Extract the instrument type portion from a canonical instrument ID."""
    parts = instrument_id.split(":")
    return parts[1] if len(parts) >= 2 else ""


def validate_instruments_vs_venues(
    strategy: dict[str, object],
) -> list[str]:
    """Check that each instrument's venue is in the strategy's declared venues list."""
    errors: list[str] = []
    sid = str(strategy.get("strategy_id", "UNKNOWN"))
    instruments_raw = strategy.get("instruments")
    venues_raw = strategy.get("venues")

    if not instruments_raw or not isinstance(instruments_raw, list):
        return errors
    if not venues_raw or not isinstance(venues_raw, list):
        return errors

    venues_set: set[str] = {str(v) for v in venues_raw}
    for instrument_id in instruments_raw:
        iid = str(instrument_id)
        venue = extract_instrument_venue(iid)
        if venue and venue not in venues_set:
            errors.append(
                f"{sid}: instrument '{iid}' references venue '{venue}' not in declared venues {sorted(venues_set)}"
            )
    return errors


def validate_instruments_vs_asset_groupes(
    strategy: dict[str, object],
) -> list[str]:
    """Check that each instrument's type is in the strategy's declared asset_groupes list."""
    errors: list[str] = []
    sid = str(strategy.get("strategy_id", "UNKNOWN"))
    instruments_raw = strategy.get("instruments")
    asset_groupes_raw = strategy.get("asset_groupes")

    if not instruments_raw or not isinstance(instruments_raw, list):
        return errors
    if not asset_groupes_raw or not isinstance(asset_groupes_raw, list):
        return errors

    ac_set: set[str] = {str(ac) for ac in asset_groupes_raw}
    for instrument_id in instruments_raw:
        iid = str(instrument_id)
        inst_type = extract_instrument_type(iid)
        if inst_type and inst_type not in ac_set:
            errors.append(
                f"{sid}: instrument '{iid}' has type '{inst_type}' not in declared asset_groupes {sorted(ac_set)}"
            )
    return errors


def validate_instrument_id_formats(
    strategy: dict[str, object],
) -> list[str]:
    """Validate each instrument ID matches the canonical format."""
    errors: list[str] = []
    sid = str(strategy.get("strategy_id", "UNKNOWN"))
    instruments_raw = strategy.get("instruments")

    if not instruments_raw or not isinstance(instruments_raw, list):
        return errors

    for instrument_id in instruments_raw:
        iid = str(instrument_id)
        if not validate_instrument_format(iid):
            errors.append(f"{sid}: instrument '{iid}' does not match canonical format VENUE:TYPE:PAYLOAD[@CHAIN]")
    return errors


def build_instrument_to_strategies_map(
    strategies: list[dict[str, object]],
) -> dict[str, list[str]]:
    """Build a map from instrument_id to list of strategy_ids that use it."""
    instrument_map: dict[str, list[str]] = {}
    for strategy in strategies:
        sid = str(strategy.get("strategy_id", "UNKNOWN"))
        instruments_raw = strategy.get("instruments")
        if not instruments_raw or not isinstance(instruments_raw, list):
            continue
        for instrument_id in instruments_raw:
            iid = str(instrument_id)
            instrument_map.setdefault(iid, []).append(sid)
    return instrument_map


def build_matrix(
    strategies: list[dict[str, object]],
) -> list[dict[str, str | list[str]]]:
    """Build the strategy-instrument matrix as a list of row dicts.

    Each row contains:
        strategy_id, asset_group (venue axis), venues, asset_groupes, instruments, live_capable, batch_capable
    """
    rows: list[dict[str, str | list[str]]] = []
    for strategy in strategies:
        sid = str(strategy.get("strategy_id", "UNKNOWN"))
        venue_axis = str(strategy.get("asset_group", "UNKNOWN"))
        venues_raw = strategy.get("venues")
        asset_groupes_raw = strategy.get("asset_groupes")
        instruments_raw = strategy.get("instruments")
        live_capable = str(strategy.get("live_capable", False))
        batch_capable = str(strategy.get("batch_capable", False))

        venues: list[str] = venues_raw if isinstance(venues_raw, list) else []
        asset_groupes: list[str] = asset_groupes_raw if isinstance(asset_groupes_raw, list) else []
        instruments: list[str] = [str(i) for i in instruments_raw] if isinstance(instruments_raw, list) else []

        rows.append(
            {
                "strategy_id": sid,
                "asset_group": venue_axis,
                "venues": venues,
                "asset_groupes": asset_groupes,
                "instruments": instruments,
                "live_capable": live_capable,
                "batch_capable": batch_capable,
            }
        )
    return rows


def detect_instrument_conflicts(
    instrument_map: dict[str, list[str]],
    strategies_by_id: dict[str, dict[str, object]],
) -> list[str]:
    """Detect instruments claimed by strategies with conflicting directions.

    This is a soft check -- it warns when the same instrument is used by multiple
    strategies that have different venue asset groups (e.g., CEFI and DEFI on the same perp).
    """
    warnings: list[str] = []
    for instrument_id, strategy_ids in instrument_map.items():
        if len(strategy_ids) <= 1:
            continue
        asset_groups: set[str] = set()
        for sid in strategy_ids:
            strat = strategies_by_id.get(sid, {})
            asset_groups.add(str(strat.get("asset_group", "UNKNOWN")))
        if len(asset_groups) > 1:
            warnings.append(
                f"Instrument '{instrument_id}' shared across asset groups "
                f"{sorted(asset_groups)} by strategies: {strategy_ids}"
            )
    return warnings


def print_matrix_table(rows: list[dict[str, str | list[str]]]) -> None:
    """Print the strategy-instrument matrix as a formatted table."""
    print(f"\n{'Strategy':<45} {'AssetGroup':<10} {'Venues':<30} {'Instruments'}")
    print("-" * 130)
    for row in rows:
        venues_str = ", ".join(row["venues"]) if isinstance(row["venues"], list) else str(row["venues"])
        instruments = row["instruments"]
        instruments_list: list[str] = instruments if isinstance(instruments, list) else [str(instruments)]
        instr_str = ", ".join(instruments_list) if instruments_list else "(none)"
        # Truncate long strings
        if len(instr_str) > 50:
            instr_str = instr_str[:47] + "..."
        if len(venues_str) > 28:
            venues_str = venues_str[:25] + "..."
        print(f"{row['strategy_id']:<45} {row['asset_group']:<10} {venues_str:<30} {instr_str}")


def main() -> int:
    """Run strategy-instrument matrix generation and validation."""
    parser = argparse.ArgumentParser(description="Strategy-instrument validation matrix")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output matrix as JSON instead of table",
    )
    parser.add_argument(
        "--asset-group",
        type=str,
        default=None,
        dest="asset_group",
        help="Filter by venue asset group (CEFI, TRADFI, DEFI, SPORTS, QUANT, OPTIONS)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to strategy-manifest.json (default: auto-detect)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest) if args.manifest else MANIFEST_PATH
    data = load_manifest(manifest_path)
    strategies_raw = data.get("strategies")
    strategies: list[dict[str, object]] = strategies_raw if isinstance(strategies_raw, list) else []

    if args.asset_group:
        want = str(args.asset_group).upper()
        strategies = [s for s in strategies if str(s.get("asset_group", "")).upper() == want]

    if not strategies:
        print("No strategies found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []

    # ── Validate instrument formats ──────────────────────────────────────────
    for strategy in strategies:
        all_errors.extend(validate_instrument_id_formats(strategy))

    # ── Validate instruments vs venues ───────────────────────────────────────
    for strategy in strategies:
        all_errors.extend(validate_instruments_vs_venues(strategy))

    # ── Validate instruments vs asset_groupes ────────────────────────────────
    for strategy in strategies:
        all_errors.extend(validate_instruments_vs_asset_groupes(strategy))

    # ── Build instrument map and detect conflicts ────────────────────────────
    instrument_map = build_instrument_to_strategies_map(strategies)
    strategies_by_id = {str(s.get("strategy_id", "UNKNOWN")): s for s in strategies}
    all_warnings.extend(detect_instrument_conflicts(instrument_map, strategies_by_id))

    # ── Build and output matrix ──────────────────────────────────────────────
    matrix_rows = build_matrix(strategies)

    if args.json:
        output = {
            "matrix": matrix_rows,
            "instrument_map": instrument_map,
            "total_strategies": len(strategies),
            "total_instruments": len(instrument_map),
            "errors": all_errors,
            "warnings": all_warnings,
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 80)
        print("STRATEGY-INSTRUMENT VALIDATION MATRIX")
        print("=" * 80)
        print(f"\nTotal strategies: {len(strategies)}")
        print(f"Total unique instruments: {len(instrument_map)}")

        print_matrix_table(matrix_rows)

        # ── Instrument coverage summary ──────────────────────────────────────
        print(f"\n{'=' * 80}")
        print("INSTRUMENT COVERAGE")
        print(f"{'=' * 80}")
        for instrument_id, sids in sorted(instrument_map.items()):
            count_str = f"({len(sids)} strategies)"
            print(f"  {instrument_id:<55} {count_str}")

        # ── Errors and warnings ──────────────────────────────────────────────
        if all_warnings:
            print(f"\nWARNINGS ({len(all_warnings)}):")
            for warn in all_warnings:
                print(f"  WARN: {warn}")

        if all_errors:
            print(f"\nERRORS ({len(all_errors)}):")
            for err in all_errors:
                print(f"  FAIL: {err}")
            print(f"\nFAIL: {len(all_errors)} validation error(s)")
            return 1

        print(f"\nPASS: {len(strategies)} strategies, {len(instrument_map)} instruments validated")

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
