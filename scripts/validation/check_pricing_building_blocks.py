# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate codex/14-playbooks/commercial-model/pricing-building-blocks.md structure.

Stage 3E G3.2 Phase A. Asserts:

1. The main 13-row pricing table exists and has 13 data rows x 4 columns of prices
   (internal / Tier A / Tier B monthly / Tier B upfront) plus the leading "#" and
   "Block" columns.
2. No ``codex-private (TBD)`` sentinel is present in any pricing cell after
   population (Stage 3E §3.2 Phase C requires the internal column to be populated).
3. The Block 5 depth sub-table (3 rows) exists with populated internal values.
4. Block 12 exclusivity uplift table (4 IP-power tiers) exists.

Exits non-zero with a clear reproduce command on any violation. Wire into
``scripts/quality-gates.sh`` to block regressions.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOC_REL = "codex/14-playbooks/commercial-model/pricing-building-blocks.md"
EXPECTED_BLOCKS = 13
TBD_SENTINEL = "codex-private (TBD)"


def _repo_root() -> Path:
    """Walk upwards from this file to find the unified-trading-pm repo root."""

    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / DOC_REL
        if candidate.exists():
            return parent
    raise SystemExit(f"ERROR: could not find {DOC_REL} in any ancestor of {here}")


def _find_main_pricing_table(lines: list[str]) -> tuple[int, int]:
    """Return (start_row, end_row) of the 13-row pricing table."""

    # Look for the header row with "| # | Block | Internal monthly cost | ..."
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if (
            stripped.startswith("|")
            and "Internal monthly cost" in stripped
            and "Tier A" in stripped
            and "Tier B fixed monthly" in stripped
        ):
            # Data starts two rows later (header + separator).
            data_start = idx + 2
            # Walk forward to find the end of the table — blank line or new heading.
            data_end = data_start
            while data_end < len(lines) and lines[data_end].strip().startswith("|"):
                data_end += 1
            return data_start, data_end
    raise SystemExit(f"ERROR: main pricing table header not found in {DOC_REL}")


def _check_main_table(lines: list[str]) -> list[str]:
    errors: list[str] = []
    start, end = _find_main_pricing_table(lines)
    rows = lines[start:end]
    if len(rows) != EXPECTED_BLOCKS:
        errors.append(f"main pricing table has {len(rows)} data rows (expected {EXPECTED_BLOCKS})")

    # Check for TBD sentinels in the internal-cost column (3rd column after leading pipe).
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 3:
            errors.append(f"row has < 3 columns: {row.strip()!r}")
            continue
        internal_cell = cells[2]
        if TBD_SENTINEL in internal_cell:
            errors.append(f"row #{cells[0]} ({cells[1]}) internal cost still unpopulated: {internal_cell!r}")
    return errors


def _check_block_5_depth_table(lines: list[str]) -> list[str]:
    errors: list[str] = []
    # The block 5 depth table has "| Block 5 depth |" in its header.
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and "Block 5 depth" in line:
            # Three depth rows: Minimal / Standard / Rich.
            rows = lines[idx + 2 : idx + 5]
            for row in rows:
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                if len(cells) >= 2 and TBD_SENTINEL in cells[1]:
                    errors.append(f"block 5 depth row {cells[0]!r} internal still unpopulated")
            return errors
    errors.append("block 5 depth table not found")
    return errors


def _check_block_12_exclusivity_table(lines: list[str]) -> list[str]:
    errors: list[str] = []
    for idx, line in enumerate(lines):
        # Header-only match: line must start with "| IP-power tier" exactly
        # so we don't falsely match the main pricing table's row 12 text.
        if line.lstrip().startswith("| IP-power tier"):
            rows = lines[idx + 2 : idx + 6]
            if sum(1 for r in rows if r.strip().startswith("|")) != 4:
                errors.append("block 12 exclusivity table does not have 4 IP-power rows")
            return errors
    errors.append("block 12 exclusivity table not found")
    return errors


def main() -> int:
    root = _repo_root()
    doc_path = root / DOC_REL
    lines = doc_path.read_text(encoding="utf-8").splitlines()

    errors: list[str] = []
    errors += _check_main_table(lines)
    errors += _check_block_5_depth_table(lines)
    errors += _check_block_12_exclusivity_table(lines)

    # Top-of-file TBD sentinel anywhere in the main pricing table range is a hard-fail.
    # (Historical versions used codex-private (TBD); those should be replaced when
    # finance populates numbers.)
    start, end = _find_main_pricing_table(lines)
    table_body = "\n".join(lines[start:end])
    if TBD_SENTINEL in table_body:
        # Already caught above but list the raw count for clarity.
        tbd_count = len(re.findall(re.escape(TBD_SENTINEL), table_body))
        errors.append(f"found {tbd_count} '{TBD_SENTINEL}' sentinels in main table")

    if errors:
        print(f"❌ {doc_path.relative_to(root)} — {len(errors)} problem(s):")
        for err in errors:
            print(f"  - {err}")
        print("\nReproduce: python unified-trading-pm/scripts/validation/check_pricing_building_blocks.py")
        return 1

    print(f"✅ {doc_path.relative_to(root)} — structure + population OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
