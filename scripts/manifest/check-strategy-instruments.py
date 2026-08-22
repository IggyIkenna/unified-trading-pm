#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Validate strategy-manifest.json instrument references.

For each strategy, verifies:
1. All venues[] are valid (present in UAC VENUE_CATEGORY_MAP)
2. All asset_groupes[] are valid InstrumentType enum values (from UAC)
3. Generates a matrix output: strategy x venue x asset_group

Exit 0 if all valid, exit 1 with details on invalid entries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from unified_api_contracts import VENUE_CATEGORY_MAP, InstrumentType


def _load_strategy_manifest() -> list[dict[str, object]]:
    """Load strategy-manifest.json from the PM repo root."""
    manifest_path = Path(__file__).resolve().parent.parent.parent / "strategy-manifest.json"
    if not manifest_path.exists():
        print(f"FATAL: strategy-manifest.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path) as f:
        data = json.load(f)
    strategies: list[dict[str, object]] = data.get("strategies", [])  # noqa: qg-empty-fallback
    return strategies


def _get_valid_instrument_types() -> set[str]:
    """Return all valid InstrumentType values as strings."""
    return {member.value for member in InstrumentType}


def _get_valid_venues() -> set[str]:
    """Return all valid venue keys from VENUE_CATEGORY_MAP."""
    return set(VENUE_CATEGORY_MAP.keys())


def main() -> int:
    strategies = _load_strategy_manifest()
    valid_venues = _get_valid_venues()
    valid_instrument_types = _get_valid_instrument_types()

    errors: list[str] = []
    matrix_rows: list[tuple[str, str, str, str]] = []

    for strategy in strategies:
        sid = str(strategy.get("strategy_id", "UNKNOWN"))
        venues_raw = strategy.get("venues", [])  # noqa: qg-empty-fallback
        asset_groupes_raw = strategy.get("asset_groupes", [])  # noqa: qg-empty-fallback

        venues: list[str] = venues_raw if isinstance(venues_raw, list) else []
        asset_groupes: list[str] = asset_groupes_raw if isinstance(asset_groupes_raw, list) else []

        # Validate venues
        for venue in venues:
            venue_str = str(venue)
            status = "OK" if venue_str in valid_venues else "INVALID_VENUE"
            if status != "OK":
                errors.append(f"  {sid}: venue '{venue_str}' not in VENUE_CATEGORY_MAP")
            # Add to matrix for each asset_group
            for ac in asset_groupes:
                ac_str = str(ac)
                ac_status = "OK" if ac_str in valid_instrument_types else "INVALID_TYPE"
                combined = (
                    "OK"
                    if status == "OK" and ac_status == "OK"
                    else f"{status},{ac_status}".replace("OK,", "").replace(",OK", "")
                )
                matrix_rows.append((sid, venue_str, ac_str, combined))

        # Validate asset_groupes independently (in case venues is empty)
        for ac in asset_groupes:
            ac_str = str(ac)
            if ac_str not in valid_instrument_types:
                errors.append(f"  {sid}: asset_group '{ac_str}' not a valid InstrumentType")

        # Handle case with venues but no asset_groupes
        if venues and not asset_groupes:
            for venue in venues:
                venue_str = str(venue)
                status = "OK" if venue_str in valid_venues else "INVALID_VENUE"
                matrix_rows.append((sid, venue_str, "(none)", status))

    # Print matrix
    print("\n=== Strategy-Instrument Validation Matrix ===\n")
    print(f"{'Strategy':<40} {'Venue':<25} {'AssetClass':<20} {'Status'}")
    print("-" * 110)
    for sid, venue, ac, status in matrix_rows:
        marker = "OK" if status == "OK" else f"FAIL ({status})"
        print(f"{sid:<40} {venue:<25} {ac:<20} {marker}")

    print(f"\nTotal strategies: {len(strategies)}")
    print(f"Total matrix entries: {len(matrix_rows)}")

    if errors:
        print(f"\n=== {len(errors)} VALIDATION ERROR(S) ===\n", file=sys.stderr)
        seen: set[str] = set()
        for err in errors:
            if err not in seen:
                seen.add(err)
                print(err, file=sys.stderr)
        return 1

    print("\nAll strategies pass venue and asset_group validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
