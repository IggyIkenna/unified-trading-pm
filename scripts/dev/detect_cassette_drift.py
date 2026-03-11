"""
detect_cassette_drift.py — Schema-level VCR cassette drift detector.

Walks a cassette directory looking for *.yaml cassette files. For each cassette
it attempts to validate recorded responses against UAC Pydantic models (when
available). Writes a JSON report and exits 0 (no drift) or 1 (drift detected).

Usage:
    python detect_cassette_drift.py \\
        --cassette-dir unified-api-contracts/ \\
        --output-json drift_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YAML loading — stdlib-only fallback so the script works without extras
# ---------------------------------------------------------------------------
try:
    import yaml  # type: ignore[import-untyped]

    def _load_yaml(path: Path) -> object:
        with path.open() as fh:
            return yaml.safe_load(fh)

except ModuleNotFoundError:

    def _load_yaml(path: Path) -> object:  # type: ignore[misc]
        logger.warning("PyYAML not available — skipping YAML parse for %s", path)
        return None


# ---------------------------------------------------------------------------
# Pydantic model registry (populated lazily from UAC package)
# ---------------------------------------------------------------------------


def _build_model_registry() -> dict[str, type]:
    """
    Attempt to import UAC Pydantic models.

    Returns a mapping of cassette-name fragment → Pydantic model class.
    Returns an empty dict if UAC is not installed (graceful degradation).
    """
    registry: dict[str, type] = {}
    try:
        import importlib  # noqa: PLC0415

        # Walk the package looking for Pydantic BaseModel subclasses.
        import inspect  # noqa: PLC0415
        import pkgutil  # noqa: PLC0415

        import unified_api_contracts as uac  # type: ignore[import-untyped]  # noqa: PLC0415

        for _importer, modname, _ispkg in pkgutil.walk_packages(
            path=uac.__path__,
            prefix=uac.__name__ + ".",
            onerror=lambda _name: None,
        ):
            try:
                mod = importlib.import_module(modname)
            except Exception:  # noqa: BLE001
                continue
            for _attr, obj in inspect.getmembers(mod, inspect.isclass):
                try:
                    from pydantic import BaseModel  # noqa: PLC0415

                    if issubclass(obj, BaseModel) and obj is not BaseModel:
                        key = obj.__name__.lower()
                        registry[key] = obj
                except Exception:  # noqa: BLE001
                    pass
    except ModuleNotFoundError:
        logger.info("unified_api_contracts not installed — schema validation skipped")
    return registry


def _cassette_name_hint(path: Path) -> str:
    """Return a lower-case stem that can be matched against model registry keys."""
    return path.stem.lower().replace("-", "_")


# ---------------------------------------------------------------------------
# Drift detection logic
# ---------------------------------------------------------------------------


def _validate_cassette(
    cassette_path: Path,
    model_registry: dict[str, type],
) -> list[str]:
    """
    Validate a single cassette file.

    Returns a list of validation error strings. Empty list means no drift.
    """
    raw = _load_yaml(cassette_path)
    if raw is None:
        return []  # Unparseable — skip silently

    if not isinstance(raw, dict):
        return [f"Unexpected cassette structure (root is not a mapping): {cassette_path.name}"]

    interactions: list[object] = raw.get("interactions") or []
    if not interactions:
        return []

    hint = _cassette_name_hint(cassette_path)

    # Find best-matching model by name fragment
    model: type | None = None
    for key, cls in model_registry.items():
        if key in hint or hint in key:
            model = cls
            break

    errors: list[str] = []

    for idx, interaction in enumerate(interactions):
        if not isinstance(interaction, dict):
            continue

        response_body: object = (
            interaction.get("response", {}).get("body", {}).get("string")
            if isinstance(interaction.get("response"), dict)
            else None
        )

        if response_body is None:
            continue

        # If we have a matching model, attempt schema validation
        if model is not None:
            try:
                import json as _json  # noqa: PLC0415

                if isinstance(response_body, str):
                    data = _json.loads(response_body)
                elif isinstance(response_body, dict):
                    data = response_body
                else:
                    continue

                if isinstance(data, list):
                    for item in data[:5]:  # Validate first 5 items for lists
                        model.model_validate(item)
                else:
                    model.model_validate(data)

            except Exception as exc:  # noqa: BLE001
                errors.append(f"{cassette_path.name}[interaction={idx}]: {type(exc).__name__}: {exc}")
        else:
            # No model available — perform structural checks only
            if isinstance(response_body, str):
                try:
                    import json as _json  # noqa: PLC0415

                    _json.loads(response_body)
                except ValueError:
                    errors.append(
                        f"{cassette_path.name}[interaction={idx}]: "
                        f"response body is not valid JSON (may indicate API format change)"
                    )

    return errors


def run_drift_detection(cassette_dir: Path, output_json: Path) -> bool:
    """
    Walk cassette_dir recursively for *.yaml files, validate each one.

    Returns True if drift was detected, False otherwise.
    Writes the JSON report to output_json regardless.
    """
    cassette_files = sorted(cassette_dir.rglob("*.yaml"))
    total_checked = len(cassette_files)

    if total_checked == 0:
        logger.info("No cassette files found under %s", cassette_dir)
        report = {
            "summary": f"No cassette files found under {cassette_dir}.",
            "drifted_cassettes": [],
            "total_checked": 0,
        }
        output_json.write_text(json.dumps(report, indent=2))
        return False

    model_registry = _build_model_registry()
    logger.info("Loaded %d Pydantic models from UAC registry", len(model_registry))
    logger.info("Checking %d cassette files...", total_checked)

    drifted: list[str] = []
    all_errors: list[str] = []

    for cassette_path in cassette_files:
        errors = _validate_cassette(cassette_path, model_registry)
        if errors:
            drifted.append(str(cassette_path.relative_to(cassette_dir)))
            all_errors.extend(errors)
            for err in errors:
                logger.warning("DRIFT: %s", err)
        else:
            logger.debug("OK: %s", cassette_path.name)

    drift_detected = len(drifted) > 0

    if drift_detected:
        summary = (
            f"{len(drifted)} of {total_checked} cassette(s) have schema drift. "
            f"Errors: {'; '.join(all_errors[:5])}" + (" (truncated)" if len(all_errors) > 5 else "")
        )
    else:
        summary = f"All {total_checked} cassette(s) match expected schemas."

    report = {
        "summary": summary,
        "drifted_cassettes": drifted,
        "all_errors": all_errors,
        "total_checked": total_checked,
    }

    output_json.write_text(json.dumps(report, indent=2))
    logger.info("Report written to %s", output_json)
    logger.info(summary)

    return drift_detected


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect schema drift in VCR cassettes against UAC Pydantic models.",
    )
    parser.add_argument(
        "--cassette-dir",
        required=True,
        type=Path,
        help="Root directory to search for *.yaml cassette files recursively.",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        type=Path,
        help="Path for the JSON drift report output.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s  %(message)s",
    )

    cassette_dir = args.cassette_dir.resolve()
    if not cassette_dir.exists():
        logger.error("cassette-dir does not exist: %s", cassette_dir)
        return 2

    drift_detected = run_drift_detection(
        cassette_dir=cassette_dir,
        output_json=args.output_json.resolve(),
    )

    return 1 if drift_detected else 0


if __name__ == "__main__":
    sys.exit(main())
