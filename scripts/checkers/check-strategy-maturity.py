#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Strategy maturity checker.

Loads strategy-manifest.json and validates:
1. The class_path file exists in strategy-service
2. A unit test file exists containing the strategy class name
3. The declared maturity level matches the evidence

Exit codes:
  0 — all checks pass
  1 — a production-declared strategy lacks tests, or class_path file missing
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "strategy-manifest.json"
STRATEGY_SERVICE_ROOT = WORKSPACE_ROOT.parent / "strategy-service"
TESTS_DIR = STRATEGY_SERVICE_ROOT / "tests"


def _class_path_to_file(class_path: str) -> Path:
    """Convert dotted class_path to a filesystem path relative to strategy-service."""
    # e.g. strategy_service.engine.core.strategies.btc_basis_strategy.BTCBasisStrategyManager
    parts = class_path.rsplit(".", 1)  # split off class name
    module_path = parts[0]
    return STRATEGY_SERVICE_ROOT / module_path.replace(".", "/") / "__init__.py"


def _module_file(class_path: str) -> Path:
    """Convert dotted class_path to the .py module file."""
    parts = class_path.rsplit(".", 1)  # split off class name
    module_dotted = parts[0]
    # module_dotted = strategy_service.engine.core.strategies.btc_basis_strategy
    # The last segment is the module file name
    segments = module_dotted.split(".")
    file_path = STRATEGY_SERVICE_ROOT / "/".join(segments[:-1]) / f"{segments[-1]}.py"
    return file_path


def _find_test_file(class_name: str, class_path: str) -> Path | None:
    """Search tests/ recursively for a file referencing the strategy.

    Searches for:
    1. The class name itself (e.g. BTCBasisStrategyManager)
    2. The module import path (e.g. strategy_service.engine.strategies.sports.kelly)
    3. A factory function pattern (e.g. create_kelly_criterion_strategy)
    """
    if not TESTS_DIR.exists():
        return None

    # Build search terms: class name + module path
    module_dotted = class_path.rsplit(".", 1)[0]  # drop class name
    module_name = module_dotted.rsplit(".", 1)[-1]  # last segment = module file stem
    search_terms = [class_name, module_dotted, f"from {module_dotted}"]

    # Also check for factory import: "from <parent.module> import"
    if "." in module_dotted:
        parent = module_dotted.rsplit(".", 1)[0]
        search_terms.append(f"from {parent}.{module_name} import")

    for test_file in TESTS_DIR.rglob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8")
            for term in search_terms:
                if term in content:
                    return test_file
        except OSError:
            continue
    return None


def _expected_maturity(has_tests: bool, has_config: bool) -> str:
    """Determine expected maturity from evidence."""
    if has_tests and has_config:
        return "beta"  # would be production if deployed
    if has_tests:
        return "beta"
    return "experimental"


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}")
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    strategies = manifest.get("strategies", [])  # noqa: qg-empty-fallback

    if not strategies:
        print("WARNING: No strategies found in manifest")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    print(f"Checking {len(strategies)} strategies from {MANIFEST_PATH.name}")
    print("=" * 80)

    for strat in strategies:
        name = strat["name"]
        class_name = strat["class_name"]
        class_path = strat["class_path"]
        declared_maturity = strat["maturity"]
        declared_has_tests = strat["has_unit_tests"]
        declared_has_config = strat["has_config_yaml"]

        # 1. Verify class_path file exists
        module_file = _module_file(class_path)
        file_exists = module_file.exists()
        if not file_exists:
            errors.append(f"  {name}: class_path file not found: {module_file}")

        # 2. Check if unit test exists
        test_file = _find_test_file(class_name, class_path)
        actual_has_tests = test_file is not None

        # 3. Validate maturity matches evidence
        expected = _expected_maturity(actual_has_tests, declared_has_config)

        # Report
        status_icon = "PASS" if file_exists else "FAIL"
        test_icon = "yes" if actual_has_tests else "no"
        config_icon = "yes" if declared_has_config else "no"

        print(
            f"  [{status_icon}] {name:<25s} "
            f"maturity={declared_maturity:<14s} "
            f"tests={test_icon:<4s} "
            f"config={config_icon:<4s} "
            f"class={class_name}"
        )

        if actual_has_tests and test_file is not None:
            rel_test = test_file.relative_to(STRATEGY_SERVICE_ROOT)
            print(f"         test file: {rel_test}")

        # Mismatch checks
        if declared_has_tests != actual_has_tests:
            msg = f"  {name}: has_unit_tests declared={declared_has_tests}, actual={actual_has_tests}"
            warnings.append(msg)

        if declared_maturity == "production" and not actual_has_tests:
            errors.append(f"  {name}: declared production but no test file found for {class_name}")

        if declared_maturity == "experimental" and actual_has_tests:
            warnings.append(f"  {name}: declared experimental but tests exist — consider upgrading to beta")

        if declared_maturity != expected and declared_maturity != "production":
            warnings.append(f"  {name}: declared {declared_maturity} but evidence suggests {expected}")

    print("=" * 80)

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(w)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(e)
        print(f"\nFAIL: {len(errors)} error(s) found")
        return 1

    print(f"\nPASS: All {len(strategies)} strategies validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
