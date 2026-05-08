"""Validate the G1.13 upsell-overlay hierarchy YAML.

Asserts:

* Top-level ``rule_id == 13`` + ``rule_name``.
* Exactly the 4 allowed axes: ``categories``, ``instrument_types``,
  ``venue_scope``, ``strategy_style``. ``service_family`` + ``fund_structure``
  must NOT appear (they are commercial-axis picks, not tempt surfaces).
* Each axis has ``hierarchy`` (non-empty ordered list of strings) and
  ``vague_triggers`` (non-empty list of known trigger names).
* Every trigger is in the closed enum
  ``{empty_array, all_selected, all_keyword, empty}``.

Exit 0 on success; non-zero on any violation.

Usage::

    python codex/14-customer-journeys/demo-ops/_tools/validate_upsell_hierarchy.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

import yaml

_YAML_PATH: Final = Path(__file__).resolve().parent.parent / "upsell-overlay-hierarchy.yaml"

_ALLOWED_AXES: Final[frozenset[str]] = frozenset({"categories", "instrument_types", "venue_scope", "strategy_style"})
_DISALLOWED_AXES: Final[frozenset[str]] = frozenset({"service_family", "fund_structure"})
_ALLOWED_TRIGGERS: Final[frozenset[str]] = frozenset({"empty_array", "all_selected", "all_keyword", "empty"})


def _validate(raw: dict[str, object]) -> list[str]:
    errors: list[str] = []

    if raw.get("rule_id") != 13:
        errors.append(f"rule_id must be 13 (got {raw.get('rule_id')!r})")
    if not raw.get("rule_name"):
        errors.append("rule_name must be non-empty")

    axes = raw.get("axes", {})
    if not isinstance(axes, dict):
        return errors + ["'axes' must be a mapping"]

    actual = set(axes.keys())
    unknown = actual - _ALLOWED_AXES
    if unknown:
        errors.append(f"unknown tempt-logic axes: {sorted(unknown)} (allowed: {sorted(_ALLOWED_AXES)})")
    missing = _ALLOWED_AXES - actual
    if missing:
        errors.append(f"missing required axes: {sorted(missing)}")
    leaked = actual & _DISALLOWED_AXES
    if leaked:
        errors.append(f"axes {sorted(leaked)} MUST NOT appear — commercial-axis picks never widen")

    for name, body in axes.items():
        if not isinstance(body, dict):
            errors.append(f"axes['{name}'] must be a mapping")
            continue

        hierarchy = body.get("hierarchy", [])
        if not isinstance(hierarchy, list) or not hierarchy:
            errors.append(f"{name}.hierarchy must be a non-empty list")
        else:
            for idx, step in enumerate(hierarchy):
                if not isinstance(step, str):
                    errors.append(f"{name}.hierarchy[{idx}] must be a string")

        triggers = body.get("vague_triggers", [])
        if not isinstance(triggers, list) or not triggers:
            errors.append(f"{name}.vague_triggers must be a non-empty list")
        else:
            for idx, trigger in enumerate(triggers):
                if not isinstance(trigger, str):
                    errors.append(f"{name}.vague_triggers[{idx}] must be a string")
                    continue
                if trigger not in _ALLOWED_TRIGGERS:
                    errors.append(f"{name}.vague_triggers[{idx}] = {trigger!r} not in enum {sorted(_ALLOWED_TRIGGERS)}")

    return errors


def main() -> int:
    if not _YAML_PATH.is_file():
        print(f"ERROR: hierarchy YAML not found at {_YAML_PATH}", file=sys.stderr)
        return 2

    with _YAML_PATH.open("r", encoding="utf-8") as handle:
        try:
            raw = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            print(f"FAIL: YAML parse error — {exc}", file=sys.stderr)
            return 1

    if not isinstance(raw, dict):
        print("FAIL: top-level must be a mapping", file=sys.stderr)
        return 1

    errors = _validate(raw)
    if errors:
        print(f"FAIL: {len(errors)} validation error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    axes_count = len(raw["axes"])
    print(f"OK: upsell-overlay hierarchy valid ({axes_count} axes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
