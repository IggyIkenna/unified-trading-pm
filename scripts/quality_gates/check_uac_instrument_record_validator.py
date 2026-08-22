# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""STEP 5.83 — UAC InstrumentRecord hard-schema enforcement validator.

Verifies that unified_api_contracts/internal/reference/instrument.py:
  (a) Defines CEFI_PAIR_INSTRUMENT_TYPES and DEFI_ONCHAIN_INSTRUMENT_TYPES frozensets.
  (b) InstrumentRecord has a model_validator named _enforce_per_asset_group_required_fields.
  (c) The validator body references CeFi, DeFi, and EVENT_CONTRACT enforcement rules.

This check guards against regression in hard_schema_enforcement_2026_05_08 Phase 1
(the model_validator that enforces non-empty required fields per asset_group).

Exit 0 = pass. Exit 1 = fail (with diagnostic output).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_INSTRUMENT_PY_RELPATH = "unified_api_contracts/internal/reference/instrument.py"

_REQUIRED_FROZENSETS = {
    "CEFI_PAIR_INSTRUMENT_TYPES",
    "DEFI_ONCHAIN_INSTRUMENT_TYPES",
}

_REQUIRED_VALIDATOR_NAME = "_enforce_per_asset_group_required_fields"

_REQUIRED_RULE_MARKERS = (
    "CEFI_PAIR_INSTRUMENT_TYPES",
    "DEFI_ONCHAIN_INSTRUMENT_TYPES",
    "EVENT_CONTRACT",
)


def _find_uac_root(start: Path) -> Path:
    """Walk up from start to find directory containing unified_api_contracts/."""
    for candidate in [start, *start.parents]:
        if (candidate / "unified_api_contracts").is_dir():
            return candidate
    msg = (
        f"Cannot locate unified_api_contracts/ package under {start}. "
        "Run from within the unified-api-contracts repo worktree."
    )
    raise FileNotFoundError(msg)


def _check(instrument_path: Path) -> list[str]:
    errors: list[str] = []
    src = instrument_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(instrument_path))

    # (a) Frozenset constants at module level (plain or annotated assignment)
    found_frozensets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in _REQUIRED_FROZENSETS:
                    found_frozensets.add(target.id)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in _REQUIRED_FROZENSETS
        ):
            found_frozensets.add(node.target.id)

    missing_frozensets = _REQUIRED_FROZENSETS - found_frozensets
    for name in sorted(missing_frozensets):
        errors.append(
            f"[FAIL] {name} frozenset not found in {instrument_path}. "
            "hard_schema_enforcement Phase 1 requires this constant to exist."
        )

    # (b) InstrumentRecord has the model_validator method
    found_validator = False
    validator_src_lines: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "InstrumentRecord":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == _REQUIRED_VALIDATOR_NAME:
                found_validator = True
                validator_src_lines = src.splitlines()[item.lineno - 1 : (item.end_lineno or item.lineno)]
                break

    if not found_validator:
        errors.append(
            f"[FAIL] InstrumentRecord.{_REQUIRED_VALIDATOR_NAME}() not found in "
            f"{instrument_path}. This model_validator enforces hard-required fields "
            "per asset_group (hard_schema_enforcement Phase 1). Do not remove it."
        )
    else:
        # (c) Validator body must reference all 3 rule markers
        validator_body = "\n".join(validator_src_lines)
        for marker in _REQUIRED_RULE_MARKERS:
            if marker not in validator_body:
                errors.append(
                    f"[FAIL] {_REQUIRED_VALIDATOR_NAME}() in InstrumentRecord does not "
                    f"reference '{marker}'. The validator must enforce CeFi, DeFi, and "
                    "EVENT_CONTRACT rules (hard_schema_enforcement Phase 1)."
                )

    return errors


def main() -> int:
    try:
        uac_root = _find_uac_root(Path.cwd())
    except FileNotFoundError as exc:
        print(f"[SKIP] {exc}", file=sys.stderr)
        return 0

    instrument_path = uac_root / _INSTRUMENT_PY_RELPATH
    if not instrument_path.exists():
        print(
            f"[SKIP] {instrument_path} not found — check not applicable outside UAC.",
            file=sys.stderr,
        )
        return 0

    errors = _check(instrument_path)
    if errors:
        for err in errors:
            print(err)
        print(
            "\nREMEDIATION: restore _enforce_per_asset_group_required_fields() in "
            "InstrumentRecord per hard_schema_enforcement_2026_05_08 Phase 1.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[OK] InstrumentRecord hard-schema enforcement present: "
        f"{_REQUIRED_VALIDATOR_NAME}() + {sorted(_REQUIRED_FROZENSETS)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
