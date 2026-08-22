#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Strategy manifest validation for quality gates.

Validates strategy-manifest.json:
1. Valid JSON, well-formed structure
2. No duplicate strategy_ids
3. Required fields present on each entry
4. class_path file exists in strategy-service (when class_exists=true)
5. Cross-reference with strategy-service Python files (orphan detection)
6. Strategy-instrument validation matrix output
7. Maturity field consistency

Exit codes:
  0 -- all checks pass
  1 -- one or more validation errors
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
# When called from QG: validate-strategy-manifest.py lives in scripts/validation/
PM_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PM_ROOT / "strategy-manifest.json"
WORKSPACE_ROOT = PM_ROOT.parent
STRATEGY_SERVICE_ROOT = WORKSPACE_ROOT / "strategy-service"

# ── Required fields per strategy entry ────────────────────────────────────────
REQUIRED_FIELDS = {
    "strategy_id",
    "display_name",
    "asset_group",
    "domain",
    "asset_groupes",
    "venues",
    "class_path",
    "maturity",
}

VALID_STRATEGY_ASSET_GROUPS = {"CEFI", "TRADFI", "DEFI", "SPORTS", "QUANT", "OPTIONS"}
VALID_DOMAINS = {"cefi", "tradfi", "defi", "sports", "quant", "options", "prediction"}

# Maturity sub-objects and their required boolean/string fields
MATURITY_CODE_FIELDS = {"status", "class_exists", "unit_tests", "qg_pass", "merged"}
MATURITY_DEPLOYMENT_FIELDS = {"status", "batch_analytics", "mock_smoke", "batch_live_recon"}
MATURITY_BUSINESS_FIELDS = {"status", "backtest_profitable", "live_1d_match", "live_1w_match", "strategy_deck"}


def _class_path_to_module_file(class_path: str) -> Path:
    """Convert a dotted class_path to the .py module file in strategy-service.

    Example:
        strategy_service.engine.strategies.cefi_momentum.CeFiMomentumStrategy
        -> strategy-service/strategy_service/engine/strategies/cefi_momentum.py
    """
    parts = class_path.rsplit(".", 1)  # split off class name
    module_dotted = parts[0]
    segments = module_dotted.split(".")
    file_path = STRATEGY_SERVICE_ROOT / "/".join(segments[:-1]) / f"{segments[-1]}.py"
    return file_path


def _class_path_to_init_file(class_path: str) -> Path:
    """Check __init__.py in the module's package directory."""
    parts = class_path.rsplit(".", 1)
    module_dotted = parts[0]
    segments = module_dotted.split(".")
    return STRATEGY_SERVICE_ROOT / "/".join(segments) / "__init__.py"


def validate_json_structure(manifest_path: Path) -> tuple[dict[str, object] | None, list[str]]:
    """Validate that the file is valid JSON with expected top-level structure."""
    errors: list[str] = []

    if not manifest_path.exists():
        errors.append(f"strategy-manifest.json not found at {manifest_path}")
        return None, errors

    try:
        raw = manifest_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON: {exc}")
        return None, errors

    if not isinstance(data, dict):
        errors.append("Top-level value must be a JSON object")
        return None, errors

    if "strategies" not in data:
        errors.append("Missing required top-level key: 'strategies'")
        return None, errors

    if not isinstance(data["strategies"], list):
        errors.append("'strategies' must be a JSON array")
        return None, errors

    return data, errors


def validate_no_duplicate_ids(strategies: list[dict[str, object]]) -> list[str]:
    """Check for duplicate strategy_id values."""
    errors: list[str] = []
    seen_ids: dict[str, int] = {}
    for idx, strat in enumerate(strategies):
        sid = strat.get("strategy_id", f"<missing-at-index-{idx}>")
        sid_str = str(sid)
        if sid_str in seen_ids:
            errors.append(f"Duplicate strategy_id '{sid_str}' at index {idx} (first seen at index {seen_ids[sid_str]})")
        else:
            seen_ids[sid_str] = idx
    return errors


def validate_required_fields(strategies: list[dict[str, object]]) -> list[str]:
    """Validate each strategy has all required fields."""
    errors: list[str] = []
    for idx, strat in enumerate(strategies):
        sid = str(strat.get("strategy_id", f"<index-{idx}>"))
        missing = REQUIRED_FIELDS - set(strat.keys())
        if missing:
            errors.append(f"{sid}: missing required fields: {sorted(missing)}")

        # Validate venue asset group (strategy axis) is known
        asset_group = strat.get("asset_group")
        if asset_group is not None and str(asset_group) not in VALID_STRATEGY_ASSET_GROUPS:
            errors.append(f"{sid}: unknown asset_group '{asset_group}' (valid: {sorted(VALID_STRATEGY_ASSET_GROUPS)})")

        # Validate domain is known
        domain = strat.get("domain")
        if domain is not None and str(domain) not in VALID_DOMAINS:
            errors.append(f"{sid}: unknown domain '{domain}' (valid: {sorted(VALID_DOMAINS)})")

        # Validate asset_groupes is a list
        ac = strat.get("asset_groupes")
        if ac is not None and not isinstance(ac, list):
            errors.append(f"{sid}: 'asset_groupes' must be a list, got {type(ac).__name__}")

        # Validate venues is a list
        venues = strat.get("venues")
        if venues is not None and not isinstance(venues, list):
            errors.append(f"{sid}: 'venues' must be a list, got {type(venues).__name__}")

        # Validate maturity sub-structure
        maturity = strat.get("maturity")
        if isinstance(maturity, dict):
            for sub_key, required_sub_fields in [
                ("code", MATURITY_CODE_FIELDS),
                ("deployment", MATURITY_DEPLOYMENT_FIELDS),
                ("business", MATURITY_BUSINESS_FIELDS),
            ]:
                sub = maturity.get(sub_key)
                if sub is None:
                    errors.append(f"{sid}: maturity missing sub-key '{sub_key}'")
                elif isinstance(sub, dict):
                    sub_missing = required_sub_fields - set(sub.keys())
                    if sub_missing:
                        errors.append(f"{sid}: maturity.{sub_key} missing fields: {sorted(sub_missing)}")
                else:
                    errors.append(f"{sid}: maturity.{sub_key} must be an object")
        elif maturity is not None:
            errors.append(f"{sid}: 'maturity' must be an object with code/deployment/business sub-keys")

    return errors


def validate_class_paths(strategies: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    """Validate class_path files exist in strategy-service.

    Only checks strategies where maturity.code.class_exists is true.
    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not STRATEGY_SERVICE_ROOT.exists():
        warnings.append(
            f"strategy-service not found at {STRATEGY_SERVICE_ROOT} -- skipping class_path file existence checks"
        )
        return errors, warnings

    for strat in strategies:
        sid = str(strat.get("strategy_id", "UNKNOWN"))
        class_path = strat.get("class_path")
        if not class_path or not isinstance(class_path, str):
            continue

        maturity = strat.get("maturity")
        class_exists_declared = False
        if isinstance(maturity, dict):
            code = maturity.get("code")
            if isinstance(code, dict):
                class_exists_declared = bool(code.get("class_exists", False))

        if not class_exists_declared:
            continue  # Skip -- class not expected to exist yet

        module_file = _class_path_to_module_file(class_path)
        init_file = _class_path_to_init_file(class_path)

        if not module_file.exists() and not init_file.exists():
            errors.append(
                f"{sid}: class_exists=true but module file not found: {module_file.relative_to(WORKSPACE_ROOT)}"
            )

    return errors, warnings


def generate_instrument_matrix(
    strategies: list[dict[str, object]],
) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Generate strategy-instrument validation matrix.

    Returns (matrix_rows, warnings) where each row is (strategy_id, venue, asset_group).
    """
    matrix_rows: list[tuple[str, str, str]] = []
    warnings: list[str] = []

    for strat in strategies:
        sid = str(strat.get("strategy_id", "UNKNOWN"))
        venues_raw = strat.get("venues", [])  # noqa: qg-empty-fallback
        asset_groupes_raw = strat.get("asset_groupes", [])  # noqa: qg-empty-fallback

        venues: list[str] = venues_raw if isinstance(venues_raw, list) else []
        asset_groupes: list[str] = asset_groupes_raw if isinstance(asset_groupes_raw, list) else []

        if not venues:
            warnings.append(f"{sid}: no venues defined")
        if not asset_groupes:
            warnings.append(f"{sid}: no asset_groupes defined")

        for venue in venues:
            for ac in asset_groupes:
                matrix_rows.append((sid, str(venue), str(ac)))

        # Handle edge case: venues but no asset_groupes
        if venues and not asset_groupes:
            for venue in venues:
                matrix_rows.append((sid, str(venue), "(none)"))

    return matrix_rows, warnings


def validate_maturity_consistency(strategies: list[dict[str, object]]) -> list[str]:
    """Check maturity status codes are consistent with boolean flags.

    Code status progression: C0 -> C1 -> C2 -> C3 -> C4
      C0: nothing, C1: class_exists, C2: +unit_tests, C3: +qg_pass, C4: +merged
    Deployment: D0 -> D1 -> D2 -> D3
    Business: B0 -> B1 -> B2 -> B3 -> B4 -> B5 -> B6
    """
    warnings: list[str] = []

    code_level_map = {
        "C0": set(),
        "C1": {"class_exists"},
        "C2": {"class_exists", "unit_tests"},
        "C3": {"class_exists", "unit_tests", "qg_pass"},
        "C4": {"class_exists", "unit_tests", "qg_pass", "merged"},
    }

    for strat in strategies:
        sid = str(strat.get("strategy_id", "UNKNOWN"))
        maturity = strat.get("maturity")
        if not isinstance(maturity, dict):
            continue

        code = maturity.get("code")
        if isinstance(code, dict):
            status = str(code.get("status", ""))  # noqa: qg-empty-fallback — status is optional; "" safely falls
            # through the `status in code_level_map` check below (only "C0".."C4" are members), so an absent status
            # is correctly treated as "nothing to validate", not silently misread as a real maturity level.
            if status in code_level_map:
                expected_true = code_level_map[status]
                for field in ("class_exists", "unit_tests", "qg_pass", "merged"):
                    actual = bool(code.get(field, False))
                    expected = field in expected_true
                    if actual != expected:
                        warnings.append(
                            f"{sid}: maturity.code.{field}={actual} "
                            f"inconsistent with status={status} "
                            f"(expected {expected})"
                        )

    return warnings


def find_orphan_strategies(strategies: list[dict[str, object]]) -> list[str]:
    """Find strategy Python files in strategy-service that are not in the manifest.

    Returns warnings for potential orphans.
    """
    warnings: list[str] = []

    strategies_dir = STRATEGY_SERVICE_ROOT / "strategy_service" / "engine" / "strategies"
    if not strategies_dir.exists():
        return warnings

    # Collect all class_path module stems from manifest
    manifest_modules: set[str] = set()
    for strat in strategies:
        cp = strat.get("class_path")
        if cp and isinstance(cp, str):
            parts = cp.rsplit(".", 1)
            module_dotted = parts[0]
            # Get the last segment (file stem)
            manifest_modules.add(module_dotted.rsplit(".", 1)[-1])

    # Scan strategy files
    skip_files = {"__init__", "base_strategy", "sports_base", "defi_base", "_defi_recursive_basis_mixins"}
    for py_file in strategies_dir.rglob("*.py"):
        stem = py_file.stem
        if stem.startswith("_") and stem not in skip_files:
            continue
        if stem in skip_files:
            continue
        if stem not in manifest_modules:
            rel = py_file.relative_to(STRATEGY_SERVICE_ROOT)
            warnings.append(f"Potential orphan strategy file not in manifest: {rel}")

    return warnings


def main() -> int:
    """Run all strategy manifest validations."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    # ── 1. JSON structure ─────────────────────────────────────────────────────
    print("=" * 80)
    print("STRATEGY MANIFEST VALIDATION")
    print("=" * 80)

    data, json_errors = validate_json_structure(MANIFEST_PATH)
    if json_errors:
        all_errors.extend(json_errors)
        for err in json_errors:
            print(f"  FAIL: {err}")
        print(f"\nFAIL: {len(all_errors)} error(s) -- cannot continue")
        return 1

    assert data is not None  # guaranteed by validate_json_structure
    strategies: list[dict[str, object]] = data["strategies"]  # type: ignore[assignment]
    print(f"\n  Loaded {len(strategies)} strategies from {MANIFEST_PATH.name}")

    # ── 2. No duplicate IDs ───────────────────────────────────────────────────
    print("\n[1/6] Duplicate strategy_id check...")
    dup_errors = validate_no_duplicate_ids(strategies)
    all_errors.extend(dup_errors)
    if dup_errors:
        for err in dup_errors:
            print(f"  FAIL: {err}")
    else:
        print(f"  PASS: {len(strategies)} unique strategy_ids")

    # ── 3. Required fields ────────────────────────────────────────────────────
    print("\n[2/6] Required fields check...")
    field_errors = validate_required_fields(strategies)
    all_errors.extend(field_errors)
    if field_errors:
        for err in field_errors:
            print(f"  FAIL: {err}")
    else:
        print(f"  PASS: All {len(strategies)} entries have required fields")

    # ── 4. Class path existence ───────────────────────────────────────────────
    print("\n[3/6] Class path existence check...")
    cp_errors, cp_warnings = validate_class_paths(strategies)
    all_errors.extend(cp_errors)
    all_warnings.extend(cp_warnings)
    if cp_errors:
        for err in cp_errors:
            print(f"  FAIL: {err}")
    if cp_warnings:
        for warn in cp_warnings:
            print(f"  WARN: {warn}")
    if not cp_errors and not cp_warnings:
        class_exists_count = sum(
            1
            for s in strategies
            if isinstance(s.get("maturity"), dict)
            and isinstance(s["maturity"].get("code"), dict)  # type: ignore[union-attr]
            and s["maturity"]["code"].get("class_exists")  # type: ignore[union-attr]
        )
        print(f"  PASS: {class_exists_count} class_exists=true strategies verified")

    # ── 5. Maturity consistency ───────────────────────────────────────────────
    print("\n[4/6] Maturity consistency check...")
    maturity_warnings = validate_maturity_consistency(strategies)
    all_warnings.extend(maturity_warnings)
    if maturity_warnings:
        for warn in maturity_warnings:
            print(f"  WARN: {warn}")
    else:
        print("  PASS: All maturity statuses consistent with flags")

    # ── 6. Orphan detection ───────────────────────────────────────────────────
    print("\n[5/6] Orphan strategy detection...")
    orphan_warnings = find_orphan_strategies(strategies)
    all_warnings.extend(orphan_warnings)
    if orphan_warnings:
        for warn in orphan_warnings:
            print(f"  WARN: {warn}")
    else:
        print("  PASS: No orphan strategy files detected")

    # ── 7. Strategy-instrument matrix ─────────────────────────────────────────
    print("\n[6/6] Strategy-instrument matrix...")
    matrix_rows, matrix_warnings = generate_instrument_matrix(strategies)
    all_warnings.extend(matrix_warnings)

    # Print compact matrix
    asset_group_counts: dict[str, int] = {}
    for strat in strategies:
        ag = str(strat.get("asset_group", "UNKNOWN"))
        asset_group_counts[ag] = asset_group_counts.get(ag, 0) + 1

    print(f"  Total matrix entries: {len(matrix_rows)}")
    print("  By asset group:")
    for ag, count in sorted(asset_group_counts.items()):
        print(f"    {ag}: {count}")

    if matrix_warnings:
        for warn in matrix_warnings:
            print(f"  WARN: {warn}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    if all_warnings:
        print(f"WARNINGS: {len(all_warnings)}")

    if all_errors:
        print(f"ERRORS: {len(all_errors)}")
        print(f"FAIL: Strategy manifest validation failed with {len(all_errors)} error(s)")
        return 1

    print(f"PASS: Strategy manifest validated ({len(strategies)} strategies, {len(matrix_rows)} matrix entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
